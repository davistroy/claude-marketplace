"""Shared fixtures for research-sse tests.

Every test in this suite is fully offline: the corpus under `fixtures/` is a
set of captured/synthesised SSE bodies, so nothing here needs an API key, a
network connection, or the `anthropic` SDK.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def fixture_path(name: str) -> Path:
    """Absolute path to a fixture, asserting it exists (a typo must not pass silently)."""
    path = FIXTURE_DIR / name
    assert path.is_file(), f"missing fixture: {path}"
    return path


def fixture_lines(name: str) -> Iterator[str]:
    """Yield a fixture's lines the way the CLI streams stdin — never slurped whole."""
    with fixture_path(name).open("r", encoding="utf-8") as handle:
        yield from handle


def fixture_text(name: str) -> str:
    """Whole fixture body, for the few tests that need to assert on raw bytes."""
    return fixture_path(name).read_text(encoding="utf-8")


@pytest.fixture
def load() -> object:
    """Expose `fixture_lines` as a pytest fixture for readability at call sites."""
    return fixture_lines


def naive_top_level_stop_reason(name: str) -> str | None:
    """Reproduce the *defect* this tool exists to prevent.

    The shipped non-streaming leg reads a **top-level** ``stop_reason`` off the
    response body. A port that reassembles the stream and keeps that lookup
    compiles, reads correctly, and never fires. This helper performs exactly
    that lookup against a fixture's ``message_start`` payload so tests can
    assert it finds nothing — proving the guard *must* read ``message_delta``.
    """
    for line in fixture_lines(name):
        if not line.startswith("data:"):
            continue
        try:
            payload = json.loads(line[len("data:") :].strip())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("type") == "message_start":
            message = payload.get("message")
            if isinstance(message, dict):
                return message.get("stop_reason")
    return None
