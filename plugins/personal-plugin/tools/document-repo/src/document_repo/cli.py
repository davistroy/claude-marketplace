"""Command-line front end for the document-repo tool.

Each subcommand is a thin wrapper: parse arguments, call one library
function, print JSON. Exit codes: 0 success, 1 a check failed (for example a
file changed in more than its comments), 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __version__


def emit(obj: Any, out: Path | None = None) -> None:
    """Write ``obj`` as pretty JSON to ``out``, or to stdout when ``out`` is None."""
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if out is None:
        # Write UTF-8 bytes directly: a Windows console may use a legacy code page that cannot encode the text.
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            # Flush text already buffered on the text layer so output stays in order.
            sys.stdout.flush()
            buffer.write(text.encode("utf-8"))
            buffer.flush()
        else:
            sys.stdout.write(text)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="document_repo", description="Helpers for the document-repo skill.")
    parser.add_argument("--version", action="version", version=f"document_repo {__version__}")
    sub = parser.add_subparsers(dest="cmd", metavar="<command>")
    # SUBCOMMANDS — each later task adds one `_register_<name>(sub)` call here, in task order.
    _ = sub
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 2
    return int(args.func(args))
