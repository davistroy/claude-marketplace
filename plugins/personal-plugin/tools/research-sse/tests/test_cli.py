"""CLI-level tests — the surface the shell leg in item 6.2 actually touches.

These assert the *contract*: report body on stdout, metadata on stderr,
verdict in the exit status. A change here is a breaking change for the caller.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import fixture_path, fixture_text
from research_sse.__main__ import META_PREFIX, main
from research_sse.accumulator import (
    EXIT_EMPTY_OUTPUT,
    EXIT_INCOMPLETE,
    EXIT_INTERNAL,
    EXIT_NO_STREAM,
    EXIT_OK,
    EXIT_REFUSAL,
    EXIT_STREAM_ERROR,
)

SRC = Path(__file__).resolve().parents[1] / "src"


def run(name: str, *args: str) -> tuple[int, str, str]:
    """Invoke `main` against a fixture, returning (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = main(["--input", str(fixture_path(name)), *args], stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def meta_of(stderr: str) -> dict:
    """Parse the machine-readable metadata line out of stderr."""
    for line in stderr.splitlines():
        if line.startswith(META_PREFIX):
            return json.loads(line[len(META_PREFIX) :])
    raise AssertionError(f"no {META_PREFIX} line in stderr:\n{stderr}")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("happy_path.sse", EXIT_OK),
        ("interleaved_reasoning.sse", EXIT_OK),
        ("truncation_max_tokens.sse", EXIT_OK),
        ("unknown_event_and_block.sse", EXIT_OK),
        ("malformed_data_line.sse", EXIT_OK),
        ("unknown_stop_reason.sse", EXIT_OK),
        ("refusal_with_category.sse", EXIT_REFUSAL),
        ("refusal_null_category.sse", EXIT_REFUSAL),
        ("refusal_absent_stop_details.sse", EXIT_REFUSAL),
        ("refusal_alt_placement.sse", EXIT_REFUSAL),
        ("no_terminal_event.sse", EXIT_INCOMPLETE),
        ("mid_stream_error.sse", EXIT_STREAM_ERROR),
        ("empty_stream.sse", EXIT_NO_STREAM),
        ("non_stream_error_body.sse", EXIT_NO_STREAM),
        ("empty_text_end_turn.sse", EXIT_EMPTY_OUTPUT),
    ],
)
def test_exit_code_contract(name: str, expected: int) -> None:
    """The full corpus, pinned against the documented exit-status contract."""
    code, _, _ = run(name)
    assert code == expected


def test_stdout_is_only_the_report_body() -> None:
    """stdout must be redirectable straight into a report file."""
    code, out, err = run("happy_path.sse")
    assert code == EXIT_OK
    assert out == "## Key Findings\n\nStreaming avoids the output ceiling."
    assert META_PREFIX not in out
    assert "research-sse:" not in out


def test_metadata_goes_to_stderr() -> None:
    _, _, err = run("happy_path.sse")
    meta = meta_of(err)
    assert meta["status"] == "ok"
    assert meta["stop_reason"] == "end_turn"
    assert meta["truncated"] is False
    assert meta["exit_code"] == EXIT_OK


def test_truncation_marker_is_machine_readable() -> None:
    """Truncation exits 0; the caller distinguishes it via this marker."""
    code, out, err = run("truncation_max_tokens.sse")
    assert code == EXIT_OK
    meta = meta_of(err)
    assert meta["truncated"] is True
    assert meta["status"] == "truncated"
    assert out  # findings are kept
    assert "depth ceiling" in err


def test_refusal_category_reaches_stderr_and_metadata() -> None:
    code, out, err = run("refusal_with_category.sse")
    assert code == EXIT_REFUSAL
    assert "category=cyber" in err
    assert meta_of(err)["refusal_category"] == "cyber"


def test_refusal_with_null_category_reports_unknown() -> None:
    code, _, err = run("refusal_null_category.sse")
    assert code == EXIT_REFUSAL
    assert "category=unknown" in err
    meta = meta_of(err)
    assert meta["refusal_category"] is None
    assert meta["refusal_category_present"] is True


def test_json_mode_carries_text_and_metadata_together() -> None:
    code, out, _ = run("truncation_max_tokens.sse", "--json")
    assert code == EXIT_OK
    payload = json.loads(out)
    assert payload["truncated"] is True
    assert payload["text"].startswith("## Key Findings")
    assert payload["status"] == "truncated"


def test_quiet_suppresses_the_human_line_but_keeps_metadata() -> None:
    _, _, err = run("happy_path.sse", "--quiet")
    assert "research-sse: ok:" not in err
    assert meta_of(err)["status"] == "ok"


def test_reads_stdin_when_no_input_flag_is_given() -> None:
    """The default path — this is how the shell leg invokes it."""
    out, err = io.StringIO(), io.StringIO()
    stdin = io.StringIO(fixture_text("happy_path.sse"))
    code = main([], stdin=stdin, stdout=out, stderr=err)
    assert code == EXIT_OK
    assert out.getvalue().startswith("## Key Findings")


def test_missing_input_file_is_reported_not_raised() -> None:
    out, err = io.StringIO(), io.StringIO()
    code = main(["--input", "/nonexistent/nope.sse"], stdout=out, stderr=err)
    assert code == EXIT_INTERNAL
    assert "cannot read stream" in err.getvalue()


def test_module_is_runnable_end_to_end() -> None:
    """`python -m research_sse` over a real pipe — the documented invocation."""
    proc = subprocess.run(
        [sys.executable, "-m", "research_sse"],
        input=fixture_text("refusal_with_category.sse"),
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        check=False,
    )
    assert proc.returncode == EXIT_REFUSAL
    assert "category=cyber" in proc.stderr


def test_help_and_version_exit_cleanly() -> None:
    for flag in ("--help", "--version"):
        with pytest.raises(SystemExit) as excinfo:
            main([flag], stdout=io.StringIO(), stderr=io.StringIO())
        assert excinfo.value.code == 0
