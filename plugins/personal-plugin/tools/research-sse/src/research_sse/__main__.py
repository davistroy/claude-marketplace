"""CLI entry point: stdin (SSE) -> stdout (report text), verdict via exit status.

    curl -N --no-buffer ... | python -m research_sse > report-body.md
    STATUS=$?

Exit-status contract (this is what the shell leg branches on):

===== ==================================================================
Code  Meaning
===== ==================================================================
0     Success. Report text is on stdout — keep it. Covers BOTH a normal
      completion and a truncation at the depth ceiling; distinguish them
      with the ``truncated`` marker, never with the exit code.
1     Internal error in this tool.
2     Command-line usage error (argparse).
3     RESERVED, never emitted. Truncation is deliberately exit 0.
4     Safety refusal. Do NOT write a report. Category (possibly
      "unknown") is on stderr and in the metadata.
5     Incomplete: the stream ended without a terminal event. The
      completeness sentinel — fires regardless of transport status.
6     An `error` event arrived on the stream.
7     Not a stream at all: empty body, or a plain JSON error object.
8     Stream completed normally but produced no text. An empty research
      report is never a success.
===== ==================================================================

Metadata is written to **stderr** by default (a single ``research-sse-meta:``
line of compact JSON) so stdout stays a clean report body that can be
redirected straight into a file. ``--json`` instead emits one JSON object on
stdout carrying both the text and the metadata, for callers that want a single
structured stream.

Truncation is signalled by ``"truncated": true`` (and ``"status":
"truncated"``) in that metadata — the caller keeps the findings and appends
its truncation note.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO

from research_sse import __version__
from research_sse.accumulator import EXIT_INTERNAL, Result, accumulate

#: Prefix for the stderr metadata line. Stable — callers may grep for it.
META_PREFIX = "research-sse-meta:"


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="research-sse",
        description=(
            "Accumulate an Anthropic Messages SSE stream into report text. "
            "Reads the stream on stdin, writes the concatenated assistant text "
            "to stdout, and reports the terminal outcome via the exit status."
        ),
        epilog=(
            "Exit codes: 0 ok (incl. truncated-at-ceiling), 4 refusal, "
            "5 incomplete stream, 6 stream error event, 7 not a stream, "
            "8 completed but empty."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="read the stream from a file instead of stdin (for tests/replay)",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="emit one JSON object on stdout with both the text and the metadata",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the human-readable stderr summary (metadata line is kept)",
    )
    parser.add_argument("--version", action="version", version=f"research-sse {__version__}")
    return parser


def _emit(result: Result, *, as_json: bool, quiet: bool, stdout: IO[str], stderr: IO[str]) -> None:
    """Write the report body and the terminal metadata."""
    if as_json:
        payload = dict(result.to_meta())
        payload["text"] = result.text
        stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    else:
        stdout.write(result.text)

    if not quiet:
        stderr.write(f"research-sse: {result.status}: {result.message}\n")
    stderr.write(
        META_PREFIX + " " + json.dumps(result.to_meta(), ensure_ascii=False, sort_keys=True) + "\n"
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: IO[str] | None = None,
    stdout: IO[str] | None = None,
    stderr: IO[str] | None = None,
) -> int:
    """Parse arguments, accumulate the stream, and return the process exit code.

    Streams from `--input` or stdin are read lazily, so a large response is
    never pulled into memory in one piece.
    """
    args = build_parser().parse_args(argv)
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    try:
        if args.input is not None:
            with args.input.open("r", encoding="utf-8") as handle:
                result = accumulate(handle)
        else:
            source = stdin if stdin is not None else sys.stdin
            result = accumulate(source)
    except OSError as exc:
        err.write(f"research-sse: cannot read stream: {exc}\n")
        return EXIT_INTERNAL

    _emit(result, as_json=args.as_json, quiet=args.quiet, stdout=out, stderr=err)
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover - exercised via subprocess
    sys.exit(main())
