"""Tests for scan_task: secrets + structural + per-repo sensitive terms.

Key guarantee: a per-repo term is flagged ONLY when the caller supplies it;
nothing about client terms is baked into the tool.
"""

from __future__ import annotations

from task_sync.confidential.scan import scan_task
from task_sync.models import Task

# A deliberately fictional term — never a real brand/client.
_TERM = "Zephyrix"
_GH_BODY = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


def _task(title: str = "task", body: str = "") -> Task:
    return Task(id="t-000001", title=title, body=body)


def test_sensitive_term_flagged_only_when_configured() -> None:
    task = _task(body=f"The {_TERM} migration is underway.")

    without = scan_task(task, [])
    assert not any(f.category == "sensitive-term" for f in without)

    with_term = scan_task(task, [_TERM])
    hits = [f for f in with_term if f.category == "sensitive-term"]
    assert len(hits) == 1
    assert hits[0].field == "body"


def test_term_match_is_case_insensitive_whole_word() -> None:
    task = _task(body="deploy zephyrix now; zephyrixation is unrelated")
    hits = [f for f in scan_task(task, [_TERM]) if f.category == "sensitive-term"]
    # matches "zephyrix" but not the substring inside "zephyrixation"
    assert len(hits) == 1


def test_secrets_and_structural_combined() -> None:
    task = _task(body=f"email a@b.com and token ghp_{_GH_BODY}")
    cats = {f.category for f in scan_task(task, [])}
    assert "structural.email" in cats
    assert "secret.github" in cats


def test_findings_tagged_with_field() -> None:
    task = _task(title="ping alice@example.com", body="all clear")
    email = next(f for f in scan_task(task, []) if f.category == "structural.email")
    assert email.field == "title"


def test_none_terms_behaves_like_empty() -> None:
    task = _task(body=f"The {_TERM} rollout.")
    assert scan_task(task, None) == scan_task(task, [])


def test_clean_task_yields_no_findings() -> None:
    assert scan_task(_task(title="refactor", body="tidy the module"), [_TERM]) == []
