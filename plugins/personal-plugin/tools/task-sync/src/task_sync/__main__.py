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
SUBCOMMANDS = ("sync", "init", "list", "add", "edit", "done", "remove", "status")


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


def _load_decisions(path: str | None) -> dict[str, str]:
    """Load a conflict-decisions file: `{task_id: "local"|"remote"}`.

    Accepts either a flat mapping or one wrapped under a `"decisions"` key.
    A missing path yields an empty mapping (every conflict left unresolved).
    """
    if not path:
        return {}
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "decisions" in data:
        data = data["decisions"]
    if not isinstance(data, dict):
        raise ValueError("decisions file must be a JSON object of task_id -> decision")
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
    """One-line-per-section summary printed after a successful `--apply`."""
    return (
        "task-sync sync: applied "
        f"{len(plan.creates)} create(s), {len(plan.pushes)} push(es), "
        f"{len(plan.pulls)} pull(s); "
        f"{len(plan.conflicts)} conflict(s) surfaced."
    )


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
    plan = build_plan(classify(tasklist, issues))
    # Read-only: scans current content, never mutates tasklist/tasks/files.
    plan.confidentiality_findings = _scan_confidentiality(plan, tasklist)

    if args.apply:
        decisions = _load_decisions(args.decisions)
        updated = apply(plan, decisions, tasklist, provider)
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
