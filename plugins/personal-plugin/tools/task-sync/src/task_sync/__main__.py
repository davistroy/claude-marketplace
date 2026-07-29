#!/usr/bin/env python3
"""CLI entry point for task-sync.

Local-first task tracker that reconciles a canonical `tasks.json` store
against GitHub/Gitea issues. Every subcommand is live as of Phase 5:

    init                        # create tasks.json (+ TASKS.md) if absent
    list [ls]                   # print the open-tasks table
    add "title"                 # add a new task
    edit <id|#>                 # update fields on a task
    done <id|#> [close]         # mark a task done
    remove <id|#> [rm]          # delete a task
    status                      # counts + last-sync + health hint
    sync --dry-run              # default: print the plan, write nothing
    sync --plan --json          # emit the machine-readable plan, write nothing
    sync --apply --decisions f  # execute the plan (resolving conflicts via f)
    sync --adopt-all            # full mirror: adopt every issue, ignore adopt window
    scan-apply --decisions f    # apply confidentiality dispositions (keep/redact/remove/anonymize)

Usage:
    python -m task_sync <subcommand> [options]
    python -m task_sync --help
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from task_sync import commands, store
from task_sync.commands import TaskNotFoundError
from task_sync.confidential.apply import needs_review
from task_sync.confidential.scan import scan_task
from task_sync.detect import detect_provider
from task_sync.models import Task, TaskList
from task_sync.providers.base import Provider
from task_sync.reconcile.apply import apply
from task_sync.reconcile.classify import classify
from task_sync.reconcile.plan import SyncPlan, build_plan, summarize_plan

# Every registered subcommand's canonical name. `sync` first so it heads the
# help; aliases (`ls`, `close`, `rm`) are registered on top of these but are
# not repeated here.
SUBCOMMANDS = ("sync", "init", "list", "add", "edit", "done", "remove", "status", "scan-apply")


def _build_provider(name: str, repo: str | None, config: dict[str, Any]) -> Provider:
    """Construct a concrete Provider for a detected tracker.

    Kept as a separate seam so tests can inject a mock instead of touching a
    live `gh`/Gitea backend.
    """
    if repo is None:
        raise ValueError("cannot build a provider without a repo slug")
    if name == "github":
        from task_sync.providers.github import GithubProvider

        return GithubProvider(repo)
    if name == "gitea":
        import os

        from task_sync.providers.gitea import GiteaProvider, load_gitea_credentials

        env_base_url = os.environ.get("GITEA_URL", "")
        env_token = os.environ.get("GITEA_TOKEN", "")
        config_base_url = str(config.get("gitea_url") or "")

        # Resolution order — env overrides everything, then the value `init`
        # persisted into tasks.json, then whatever `tea login` configured:
        #   base_url: $GITEA_URL -> config['gitea_url'] -> tea config
        #   token:    $GITEA_TOKEN -> tea config
        # Only consult the tea config when something is still missing, and
        # read it at most once — `load_gitea_credentials` does its own file
        # I/O, and a missing/unreadable config is not fatal here, it just
        # means "no credentials from that source".
        tea_base_url = tea_token = ""
        if not env_token or (not env_base_url and not config_base_url):
            try:
                tea_base_url, tea_token = load_gitea_credentials()
            except RuntimeError:
                pass

        base_url = env_base_url or config_base_url or tea_base_url
        token = env_token or tea_token

        if not base_url or not token:
            raise ValueError(
                "gitea provider needs credentials — run `tea login add`, or "
                "export $GITEA_TOKEN (and $GITEA_URL, unless config['gitea_url'] is set)"
            )
        return GiteaProvider(repo, base_url, token)
    raise ValueError(f"unknown provider {name!r}")


#: Top-level section keys that mark a decisions file as *wrapped* rather than flat.
_DECISION_SECTIONS = ("decisions", "orphan_decisions")


def _split_flat_decisions(
    flat: dict[str, str], plan: SyncPlan
) -> tuple[dict[str, str], dict[str, str]]:
    """Partition a *flat* decisions mapping into (conflict, orphan) maps by plan membership.

    The flat shape lets conflict and orphan decisions coexist in one object
    (`sync-semantics.md`), so neither consumer may receive the other's ids:
    `_validate_orphan_decisions` is deliberately fail-loud (D36) and aborts on
    an id it does not recognize.

    An id in *neither* set is a typo, and is routed to the orphan map precisely
    so that fail-loud check still reports it. Silently dropping it would turn a
    mistyped id into a decision the user believes they made.
    """
    conflict_ids = {c.task_id for c in plan.conflicts}
    orphan_ids = {o.task_id for o in plan.orphans}
    conflicts = {k: v for k, v in flat.items() if k not in orphan_ids}
    orphans = {k: v for k, v in flat.items() if k not in conflict_ids}
    return conflicts, orphans


def _load_decisions(path: str | None, *, key: str = "decisions") -> dict[str, str]:
    """Load a decisions file: `{task_id: "local"|"remote"}` for conflicts or
    `{task_id: "keep"|"drop"}` for orphans.

    Accepts either a flat mapping or one wrapped under a `key` (default
    `"decisions"` for backward compat; `key="orphan_decisions"` for orphans).

    A file is *wrapped* if it carries **any** section key at top level. In that
    case a missing requested section means "no decisions of this kind" and
    yields `{}` — it must NOT fall through to returning the outer dict. That
    fallthrough made a wrapped conflicts-only file (the documented backward-compat
    shape) hand `{"decisions": "..."}` to orphan validation, which aborted every
    `sync --apply` before any mutation. Flat files are returned whole and are
    partitioned by plan membership at the call site.
    A `None`/empty `path` yields an empty mapping (every decision left
    unresolved) — that is "no decisions file was requested", not "the
    requested file was missing".

    **Every** failure mode raises `ValueError` naming the offending path.
    This is the contract both CLI call sites rely on: a stale or mistyped
    `--decisions` path is the likeliest user error (it is `required=True`
    for `scan-apply`), and an unhandled `FileNotFoundError` — an `OSError`,
    not a `ValueError` — used to escape their handlers as a raw traceback.
    Converting here rather than widening each `except` keeps the path, which
    only this function has, inside the message.
    """
    if not path:
        return {}
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        raise ValueError(f"cannot read decisions file {path}: {exc.strerror or exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON in decisions file {path}: {exc}") from exc
    if isinstance(data, dict) and any(k in data for k in _DECISION_SECTIONS):
        data = data.get(key, {})
    if not isinstance(data, dict):
        raise ValueError(f"decisions file {path} must be a JSON object of task_id -> decision")
    return {str(k): str(v) for k, v in data.items()}


def _outbound_task_ids(plan: SyncPlan) -> list[str]:
    """Task ids for every create/push in ``plan`` — content about to leave the machine."""
    return [c.task_id for c in plan.creates] + [p.task_id for p in plan.pushes]


def _scan_confidentiality(plan: SyncPlan, tasklist: TaskList) -> list[dict[str, Any]]:
    """Scan outbound (create/push) task content for confidentiality findings.

    Read-only: runs :func:`scan_task` over each ``creates``/``pushes`` task's
    *current* ``title``/``body`` using the per-repo
    ``tasklist.config['sensitive_terms']`` list (default ``[]``). A task whose
    prior confidentiality review still covers its content
    (:func:`needs_review` is ``False``) is skipped so an already-dispositioned
    task is not re-flagged. Never mutates ``tasklist`` or any task, and
    performs no I/O — safe to call from both ``--plan`` and ``--dry-run``.

    Returns one entry per task with at least one finding, in creates-then-
    pushes order, shaped for direct JSON serialization onto
    ``plan.confidentiality_findings``.
    """
    sensitive_terms = list(tasklist.config.get("sensitive_terms") or [])
    by_id = {task.id: task for task in tasklist.tasks}

    results: list[dict[str, Any]] = []
    for task_id in _outbound_task_ids(plan):
        task = by_id.get(task_id)
        if task is None or not needs_review(task):
            continue
        findings = scan_task(task, sensitive_terms)
        if not findings:
            continue
        results.append(
            {
                "task_id": task_id,
                "title": task.title,
                "findings": [
                    {
                        "field": f.field,
                        "category": f.category,
                        "severity": f.severity,
                        "preview": f.match_preview,
                        "suggestion": f.suggestion,
                    }
                    for f in findings
                ],
            }
        )
    return results


def _apply_summary(plan: SyncPlan) -> str:
    """One-line-per-section summary printed after a successful `--apply`.

    Skipped adoptions get their own trailing sentence, and only when there
    are any — an `--apply` that mirrored nothing *because* N issues fell
    outside the adopt window would otherwise report a bare "0 pull(s)",
    which is the same silence `summarize_plan` was fixed for.
    """
    summary = (
        "task-sync sync: applied "
        f"{len(plan.creates)} create(s), {len(plan.pushes)} push(es), "
        f"{len(plan.pulls)} pull(s); "
        f"{len(plan.conflicts)} conflict(s) surfaced."
    )
    if plan.skipped_adopts:
        summary += (
            f" {len(plan.skipped_adopts)} issue(s) closed outside the adopt "
            "window were not adopted — use --adopt-all to mirror them."
        )
    return summary


def run_sync(args: argparse.Namespace, provider: Provider | None = None) -> int:
    """Handle `task-sync sync`. Read-only unless `--apply` is given.

    `provider` is injectable for tests; in normal use it is built from the
    detected remote. Returns a process exit code.
    """
    tasks_path = Path(args.tasks)
    if not tasks_path.exists():
        print(f"task-sync sync: no tasks file at {tasks_path}", file=sys.stderr)
        return 1

    tasklist = store.load(tasks_path)

    name, repo = detect_provider(args.repo_root)
    if name == "none":
        print("task-sync sync: local-only mode (no tracker remote) — nothing to sync")
        return 0

    if provider is None:
        provider = _build_provider(name, repo, tasklist.config)

    issues = provider.list_issues("all")
    # --adopt-all is a full-mirror escape hatch (no window: adopt everything);
    # otherwise NEW_REMOTE adoption is gated by its own `adopt_closed_within_days`
    # config key (default 0 == adopt open issues only) — a separate question
    # from `prune_closed_after_days`, which governs how long a *tracked* done
    # task is kept locally, not whether a not-yet-tracked issue is worth
    # adopting.
    adopt_window = None if args.adopt_all else commands.adopt_window(tasklist)
    plan = build_plan(classify(tasklist, issues), adopt_closed_within_days=adopt_window)
    # Read-only: scans current content, never mutates tasklist/tasks/files.
    plan.confidentiality_findings = _scan_confidentiality(plan, tasklist)

    if args.apply:
        try:
            decisions = _load_decisions(args.decisions)
        except ValueError as exc:
            # `_load_decisions` normalizes every read/parse failure (including
            # a missing file) into a ValueError carrying the path.
            print(f"task-sync sync: {exc}", file=sys.stderr)
            return 1
        try:
            orphan_decisions = _load_decisions(args.decisions, key="orphan_decisions")
        except ValueError as exc:
            print(f"task-sync sync: {exc}", file=sys.stderr)
            return 1
        if decisions and decisions == orphan_decisions:
            # Both loads returned the same mapping, so the file was flat: one
            # object carrying conflict and orphan decisions together. Route each
            # id to the consumer that owns it.
            decisions, orphan_decisions = _split_flat_decisions(decisions, plan)
        updated = apply(plan, decisions, tasklist, provider, orphan_decisions=orphan_decisions)
        store.save(updated, tasks_path)
        commands.regenerate_tasks_md(updated, tasks_path)
        print(_apply_summary(plan))
        return 0

    # --plan / --dry-run: strictly read-only. Emit and write nothing.
    if args.json:
        print(plan.to_json())
    else:
        print(summarize_plan(plan))
    return 0


def _require_tasklist(tasks_path: Path) -> TaskList | None:
    """Load `tasks_path`, printing a `run task-sync init` hint if it's missing."""
    if not tasks_path.exists():
        print(
            f"task-sync: no tasks file at {tasks_path} (run `task-sync init` first)",
            file=sys.stderr,
        )
        return None
    return store.load(tasks_path)


def _format_task(task: Task) -> str:
    """One-line human summary of a task, for add/edit/done/remove output."""
    priority = f" [{task.priority}]" if task.priority else ""
    issue = f" (#{task.issue_number})" if task.issue_number is not None else ""
    labels = f" {{{', '.join(task.labels)}}}" if task.labels else ""
    milestone = f" <{task.milestone}>" if task.milestone else ""
    return f"{task.id}{issue}: {task.title}{priority} [{task.status}]{labels}{milestone}"


def _print_task(prefix: str, task: Task) -> None:
    print(f"{prefix} {_format_task(task)}")


def run_init(args: argparse.Namespace) -> int:
    """Handle `task-sync init`."""
    message = commands.cmd_init(args.tasks, args.repo_root)
    print(message)
    return 0


def run_list(args: argparse.Namespace) -> int:
    """Handle `task-sync list` / `ls`."""
    tasklist = _require_tasklist(Path(args.tasks))
    if tasklist is None:
        return 1
    print(
        commands.cmd_list(
            tasklist,
            status=args.status,
            priority=args.priority,
            milestone=args.milestone,
            sort=args.sort,
            show_all=args.all,
        )
    )
    return 0


def run_add(args: argparse.Namespace) -> int:
    """Handle `task-sync add "title"`."""
    tasks_path = Path(args.tasks)
    tasklist = _require_tasklist(tasks_path)
    if tasklist is None:
        return 1
    try:
        task = commands.cmd_add(
            tasklist,
            tasks_path,
            args.title,
            body=args.body or "",
            priority=args.priority,
            labels=commands.parse_labels(args.labels),
            milestone=args.milestone,
        )
    except ValueError as exc:
        print(f"task-sync add: {exc}", file=sys.stderr)
        return 1
    _print_task("Added", task)
    return 0


def run_edit(args: argparse.Namespace) -> int:
    """Handle `task-sync edit <id|#>`."""
    tasks_path = Path(args.tasks)
    tasklist = _require_tasklist(tasks_path)
    if tasklist is None:
        return 1
    try:
        task = commands.cmd_edit(
            tasklist,
            tasks_path,
            args.ref,
            title=args.title,
            body=args.body,
            status=args.status,
            priority=args.priority,
            labels=commands.parse_labels(args.labels),
            milestone=args.milestone,
        )
    except (TaskNotFoundError, ValueError) as exc:
        print(f"task-sync edit: {exc}", file=sys.stderr)
        return 1
    _print_task("Updated", task)
    return 0


def run_done(args: argparse.Namespace) -> int:
    """Handle `task-sync done <id|#>` / `close`."""
    tasks_path = Path(args.tasks)
    tasklist = _require_tasklist(tasks_path)
    if tasklist is None:
        return 1
    try:
        task = commands.cmd_done(tasklist, tasks_path, args.ref)
    except TaskNotFoundError as exc:
        print(f"task-sync done: {exc}", file=sys.stderr)
        return 1
    _print_task("Closed", task)
    return 0


def run_remove(args: argparse.Namespace) -> int:
    """Handle `task-sync remove <id|#>` / `rm`."""
    tasks_path = Path(args.tasks)
    tasklist = _require_tasklist(tasks_path)
    if tasklist is None:
        return 1
    try:
        task = commands.cmd_remove(tasklist, tasks_path, args.ref)
    except TaskNotFoundError as exc:
        print(f"task-sync remove: {exc}", file=sys.stderr)
        return 1
    _print_task("Removed", task)
    return 0


def run_status(args: argparse.Namespace) -> int:
    """Handle `task-sync status`."""
    tasklist = _require_tasklist(Path(args.tasks))
    if tasklist is None:
        return 1
    print(commands.cmd_status(tasklist))
    return 0


def run_scan_apply(args: argparse.Namespace) -> int:
    """Handle `task-sync scan-apply --decisions f`.

    Applies a confidentiality disposition (keep/redact/remove/anonymize)
    per task, re-scanning each to recover finding spans. Replaces the
    inline `python3` heredoc previously documented for this step.

    The single `except ValueError` covers both stages because
    `_load_decisions` normalizes its read/parse failures (a missing or
    unreadable `--decisions` path included) into `ValueError`.
    """
    tasks_path = Path(args.tasks)
    tasklist = _require_tasklist(tasks_path)
    if tasklist is None:
        return 1
    try:
        dispositions = _load_decisions(args.decisions)
        message = commands.cmd_scan_apply(tasklist, dispositions, tasks_path)
    except ValueError as exc:
        print(f"task-sync scan-apply: {exc}", file=sys.stderr)
        return 1
    print(message)
    return 0


def _add_tasks_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tasks", default="tasks.json", help="path to tasks.json")


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level parser and every live subcommand."""
    parser = argparse.ArgumentParser(
        prog="task-sync",
        description="Local-first task tracker with reconciling sync to GitHub/Gitea issues.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    sync = subparsers.add_parser("sync", help="reconcile tasks.json with the tracker")
    _add_tasks_argument(sync)
    sync.add_argument("--repo-root", dest="repo_root", default=".", help="git repo root")
    sync.add_argument("--json", action="store_true", help="emit the plan as JSON")
    sync.add_argument("--decisions", help="conflict-decisions JSON file (with --apply)")
    sync.add_argument(
        "--adopt-all",
        dest="adopt_all",
        action="store_true",
        help=(
            "full-mirror mode: adopt every issue regardless of how long ago "
            "it closed (default: only adopt issues within the "
            "adopt_closed_within_days window, 0 days = open issues only)"
        ),
    )
    mode = sync.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="print the plan, write nothing")
    mode.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="print a human summary, write nothing (default)",
    )
    mode.add_argument("--apply", action="store_true", help="execute the plan")
    sync.set_defaults(func=run_sync)

    init = subparsers.add_parser("init", help="create tasks.json (+ TASKS.md) if absent")
    _add_tasks_argument(init)
    init.add_argument("--repo-root", dest="repo_root", default=".", help="git repo root")
    init.set_defaults(func=run_init)

    listing = subparsers.add_parser(
        "list", aliases=["ls"], help="list open tasks (ls; --all includes done)"
    )
    _add_tasks_argument(listing)
    listing.add_argument("--status", help="filter to a single status")
    listing.add_argument("--priority", help="filter to a single priority")
    listing.add_argument("--milestone", help="filter to a single milestone")
    listing.add_argument("--sort", help="task field to sort by (default: status/priority/id)")
    listing.add_argument("--all", action="store_true", help="include done tasks")
    listing.set_defaults(func=run_list)

    add = subparsers.add_parser("add", help="add a new task")
    _add_tasks_argument(add)
    add.add_argument("title", help="task title")
    add.add_argument("--body", default="", help="task body/description")
    add.add_argument("--priority", help="P1-P4")
    add.add_argument("--labels", help="comma-separated labels")
    add.add_argument("--milestone", help="milestone name")
    add.set_defaults(func=run_add)

    edit = subparsers.add_parser("edit", help="update fields on a task")
    _add_tasks_argument(edit)
    edit.add_argument("ref", help="task id or issue number (optionally #-prefixed)")
    edit.add_argument("--title", help="new title")
    edit.add_argument("--body", help="new body")
    edit.add_argument("--status", help="new status")
    edit.add_argument("--priority", help="new priority (P1-P4)")
    edit.add_argument("--labels", help="comma-separated labels (replaces the full set)")
    edit.add_argument("--milestone", help="new milestone")
    edit.set_defaults(func=run_edit)

    done = subparsers.add_parser("done", aliases=["close"], help="mark a task done (close)")
    _add_tasks_argument(done)
    done.add_argument("ref", help="task id or issue number (optionally #-prefixed)")
    done.set_defaults(func=run_done)

    remove = subparsers.add_parser("remove", aliases=["rm"], help="delete a task (rm)")
    _add_tasks_argument(remove)
    remove.add_argument("ref", help="task id or issue number (optionally #-prefixed)")
    remove.set_defaults(func=run_remove)

    status = subparsers.add_parser("status", help="status counts + last sync + health hint")
    _add_tasks_argument(status)
    status.set_defaults(func=run_status)

    scan_apply = subparsers.add_parser(
        "scan-apply",
        help="apply confidentiality dispositions (keep/redact/remove/anonymize)",
    )
    _add_tasks_argument(scan_apply)
    scan_apply.add_argument(
        "--decisions",
        required=True,
        help="confidentiality-dispositions JSON file (task_id -> disposition)",
    )
    scan_apply.set_defaults(func=run_scan_apply)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and dispatch to the selected subcommand.

    Returns the process exit code. `--help` (top-level or per-subcommand) is
    handled by argparse itself, which prints usage and raises `SystemExit(0)`
    before this function would otherwise return.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:  # pragma: no cover - unreachable while required=True
        parser.print_help()
        return 1
    result: int = func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
