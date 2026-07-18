"""Tests for the normalized `Issue` model and the `Provider` protocol."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from task_sync.providers.base import Issue, Provider, parse_aware_datetime
from task_sync.providers.gitea import GiteaProvider
from task_sync.providers.github import GithubProvider


def _aware(year: int = 2026, month: int = 7, day: int = 1) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


# -- Issue validation ---------------------------------------------------


def test_issue_accepts_valid_fields() -> None:
    issue = Issue(
        number=1,
        title="Fix bug",
        body="details",
        state="open",
        labels=["bug", "priority/P1"],
        milestone="v1.0",
        updated_at=_aware(),
        closed_at=None,
    )
    assert issue.number == 1
    assert issue.state == "open"
    assert issue.closed_at is None


def test_issue_rejects_invalid_state() -> None:
    with pytest.raises(ValueError, match="invalid state"):
        Issue(
            number=1,
            title="t",
            body="",
            state="merged",
            labels=[],
            milestone=None,
            updated_at=_aware(),
        )


def test_issue_rejects_non_int_number() -> None:
    with pytest.raises(ValueError, match="must be an int"):
        Issue(
            number="1",  # type: ignore[arg-type]
            title="t",
            body="",
            state="open",
            labels=[],
            milestone=None,
            updated_at=_aware(),
        )


def test_issue_rejects_non_string_labels() -> None:
    with pytest.raises(ValueError, match="labels"):
        Issue(
            number=1,
            title="t",
            body="",
            state="open",
            labels=[1, 2],  # type: ignore[list-item]
            milestone=None,
            updated_at=_aware(),
        )


def test_issue_rejects_naive_updated_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Issue(
            number=1,
            title="t",
            body="",
            state="open",
            labels=[],
            milestone=None,
            updated_at=datetime(2026, 7, 1),
        )


def test_issue_rejects_naive_closed_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Issue(
            number=1,
            title="t",
            body="",
            state="closed",
            labels=[],
            milestone=None,
            updated_at=_aware(),
            closed_at=datetime(2026, 7, 2),
        )


# -- parse_aware_datetime -------------------------------------------------


def test_parse_aware_datetime_handles_zulu_suffix() -> None:
    parsed = parse_aware_datetime("2026-07-01T10:00:00Z")
    assert parsed == datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert parsed.tzinfo is not None


def test_parse_aware_datetime_handles_explicit_offset() -> None:
    parsed = parse_aware_datetime("2026-07-01T10:00:00+02:00")
    assert parsed is not None
    assert parsed.utcoffset() is not None


def test_parse_aware_datetime_none_for_empty() -> None:
    assert parse_aware_datetime(None) is None
    assert parse_aware_datetime("") is None


# -- Protocol conformance -------------------------------------------------


def test_github_provider_satisfies_protocol() -> None:
    assert isinstance(GithubProvider("owner/repo"), Provider)


def test_gitea_provider_satisfies_protocol() -> None:
    assert isinstance(GiteaProvider("owner/repo", "https://git.example.com", "tok"), Provider)


# -- Cross-adapter normalization shape -------------------------------------


def test_github_and_gitea_normalize_to_the_same_issue_shape() -> None:
    """Both adapters must produce structurally and value-identical Issues
    for equivalent tracker input — reconcile code (Phase 3) depends on
    this to stay provider-agnostic."""
    gh_data = {
        "number": 7,
        "title": "Fix bug",
        "body": "details",
        "state": "OPEN",
        "updatedAt": "2026-07-01T10:00:00Z",
        "closedAt": None,
        "labels": [{"name": "bug"}, {"name": "priority/P1"}],
        "milestone": {"title": "v1.0"},
    }
    gitea_data = {
        "number": 7,
        "title": "Fix bug",
        "body": "details",
        "state": "open",
        "updated_at": "2026-07-01T10:00:00Z",
        "closed_at": None,
        "labels": [{"name": "bug"}, {"name": "priority/P1"}],
        "milestone": {"title": "v1.0"},
    }

    gh_issue = GithubProvider._normalize(gh_data)
    gitea_issue = GiteaProvider._normalize(gitea_data)

    assert gh_issue == gitea_issue
    assert isinstance(gh_issue, Issue)
    assert isinstance(gitea_issue, Issue)
