#!/usr/bin/env python3
"""CLI entry point for task-sync.

Local-first task tracker that reconciles a canonical `tasks.json` store
against GitHub/Gitea issues. The `sync` subcommand is live as of Phase 3:

    sync --dry-run             # default: print the plan, write nothing
    sync --plan --json         # emit the machine-readable plan, write nothing
    sync --apply --decisions f # execute the plan (resolving conflicts via f)

Every other subcommand is still a Phase 1 stub that prints a notice and
returns success; they land in later phases (5: skill wiring, etc.).

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

from task_sync import store
from task_sync.detect import detect_provider
from task_sync.providers.base import Provider
from task_sync.reconcile.apply import apply
from task_sync.reconcile.classify import classify
from task_sync.reconcile.plan import SyncPlan, build_plan, summarize_plan

# Stub subcommands (everything except `sync`, which is fully wired below).
STUB_SUBCOMMANDS = (
    "list",
    "add",
    "edit",
    "done",
    "remove",
    "status",
    "init",
)

# Every registered subcommand, live + stub. `sync` first so it heads the help.
SUBCOMMANDS = ("sync", *STUB_SUBCOMMANDS)


def _stub(name: str) -> int:
    """Placeholder handler for a not-yet-implemented subcommand."""
    print(f"task-sync {name}: not yet implemented")
    return 0


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

        from task_sync.providers.gitea import GiteaProvider

        base_url = str(config.get("gitea_url") or os.environ.get("GITEA_URL", ""))
        token = os.environ.get("GITEA_TOKEN", "")
        if not base_url:
            raise ValueError("gitea provider needs config['gitea_url'] or $GITEA_URL")
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

    if args.apply:
        decisions = _load_decisions(args.decisions)
        updated = apply(plan, decisions, tasklist, provider)
        store.save(updated, tasks_path)
        print(_apply_summary(plan))
        return 0

    # --plan / --dry-run: strictly read-only. Emit and write nothing.
    if args.json:
        print(plan.to_json())
    else:
        print(summarize_plan(plan))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level parser: the live `sync` command plus stubs."""
    parser = argparse.ArgumentParser(
        prog="task-sync",
        description="Local-first task tracker with reconciling sync to GitHub/Gitea issues.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    sync = subparsers.add_parser("sync", help="reconcile tasks.json with the tracker")
    sync.add_argument("--tasks", default="tasks.json", help="path to tasks.json")
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

    for name in STUB_SUBCOMMANDS:
        sub = subparsers.add_parser(name, help=f"{name} (not yet implemented)")
        sub.set_defaults(func=lambda _args, _name=name: _stub(_name))

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
