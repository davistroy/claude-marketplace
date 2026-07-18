#!/usr/bin/env python3
"""CLI entry point for task-sync.

Local-first task tracker that reconciles a canonical `tasks.json` store
against GitHub/Gitea issues. Phase 1 wires up the subcommand skeleton only —
every subcommand below is a stub that prints a "not yet implemented" notice
and returns success; the real behavior lands in later phases (2: provider
adapters, 3: reconcile engine, 4: confidentiality scanner, 5: skill wiring).

Usage:
    python -m task_sync <subcommand> [options]
    python -m task_sync --help
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

# Subcommands the finished tool will support. Kept as a single source of
# truth so the parser and the stub dispatcher can't drift apart.
SUBCOMMANDS = (
    "sync",
    "list",
    "add",
    "edit",
    "done",
    "remove",
    "status",
    "init",
)


def _stub(name: str) -> int:
    """Placeholder handler for a not-yet-implemented subcommand."""
    print(f"task-sync {name}: not yet implemented")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argparse parser with all subcommand stubs registered."""
    parser = argparse.ArgumentParser(
        prog="task-sync",
        description="Local-first task tracker with reconciling sync to GitHub/Gitea issues.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    for name in SUBCOMMANDS:
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
