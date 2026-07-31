"""The refusal guard — the highest-risk requirement in the plan.

Written and made to fail **before** the accumulator existed. In the shipped
non-streaming leg the terminal reason is a top-level ``stop_reason`` field on
the response body. Under streaming it moves inside a ``message_delta`` event.
A port that reassembles the stream and keeps the old top-level lookup
compiles, reads correctly, passes review, and **never fires** — silently
writing an empty research report on every safety refusal.

`test_top_level_lookup_finds_nothing` pins that: it performs the old lookup
against the refusal fixtures and asserts it yields ``None`` every time.
"""

from __future__ import annotations

import pytest

from conftest import fixture_lines, naive_top_level_stop_reason
from research_sse.accumulator import EXIT_REFUSAL, accumulate

REFUSAL_FIXTURES = [
    "refusal_with_category.sse",
    "refusal_null_category.sse",
    "refusal_absent_stop_details.sse",
    "refusal_alt_placement.sse",
]


@pytest.mark.parametrize("name", REFUSAL_FIXTURES)
def test_top_level_lookup_finds_nothing(name: str) -> None:
    """The ported-defect lookup must come up empty on every refusal fixture.

    If this ever starts returning ``"refusal"``, the fixtures no longer model
    the streaming shape and the guard below is being tested against the wrong
    thing.
    """
    assert naive_top_level_stop_reason(name) is None


@pytest.mark.parametrize("name", REFUSAL_FIXTURES)
def test_refusal_exits_non_zero(name: str) -> None:
    """A refusal must fail loudly rather than write an empty report."""
    result = accumulate(fixture_lines(name))
    assert result.stop_reason == "refusal"
    assert result.status == "refusal"
    assert result.exit_code == EXIT_REFUSAL
    assert result.exit_code != 0


def test_refusal_surfaces_category() -> None:
    """When the API supplies a category, it reaches the operator."""
    result = accumulate(fixture_lines("refusal_with_category.sse"))
    assert result.refusal_category == "cyber"
    assert result.refusal_category_present is True
    assert "cyber" in result.message


def test_refusal_surfaces_category_from_unexpected_placement() -> None:
    """Placement of the category is UNKNOWN by design — find it wherever it sits.

    This fixture puts ``stop_details`` at the *event* top level instead of
    inside ``delta``. The accumulator must not assume either location.
    """
    result = accumulate(fixture_lines("refusal_alt_placement.sse"))
    assert result.exit_code == EXIT_REFUSAL
    assert result.refusal_category == "bio"
    assert result.refusal_category_present is True


@pytest.mark.parametrize("name", ["refusal_null_category.sse", "refusal_absent_stop_details.sse"])
def test_refusal_with_null_or_absent_category_still_fails(name: str) -> None:
    """A null/absent category must not crash and must not downgrade the refusal.

    This is the specific trap: `category` is documented as nullable, so any
    code that keys the failure off a *truthy* category silently turns a
    null-category refusal back into a success.
    """
    result = accumulate(fixture_lines(name))
    assert result.exit_code == EXIT_REFUSAL
    assert result.refusal_category is None
    assert "unknown" in result.message.lower()
