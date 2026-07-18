"""Tests for dispositions and content-hash review memory."""

from __future__ import annotations

import pytest

from task_sync.confidential.apply import (
    REDACTION_MARK,
    apply_review,
    needs_review,
    stable_token,
)
from task_sync.confidential.scan import scan_task
from task_sync.models import Task

_TERM = "Zephyrix"
_GH_BODY = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
_AT = "2026-07-18T00:00:00+00:00"


def _task(title: str = "task", body: str = "") -> Task:
    return Task(id="t-000001", title=title, body=body)


def test_redact_masks_span_and_records_decision() -> None:
    task = _task(body=f"deploy with ghp_{_GH_BODY} now")
    findings = scan_task(task, [])
    apply_review(task, findings, "redact", at=_AT)

    assert _GH_BODY not in task.body
    assert REDACTION_MARK in task.body
    assert task.confidentiality is not None
    assert task.confidentiality["decision"] == "redact"
    assert task.confidentiality["reviewed_hash"]
    assert task.confidentiality["at"] == _AT


def test_remove_drops_span() -> None:
    task = _task(body=f"secret ghp_{_GH_BODY} tail")
    apply_review(task, scan_task(task, []), "remove", at=_AT)
    assert "ghp_" not in task.body
    assert task.body == "secret  tail"


def test_remove_empties_wholly_sensitive_field() -> None:
    task = _task(title=_TERM, body="ok")
    apply_review(task, scan_task(task, [_TERM]), "remove", at=_AT)
    assert task.title == ""


def test_anonymize_is_stable_same_term_same_token() -> None:
    """STABLE-TOKEN guarantee: the same term always maps to the same token."""
    # Pure-function stability, across case and surrounding whitespace.
    assert stable_token(_TERM) == stable_token(_TERM.lower())
    assert stable_token(_TERM) == stable_token(f"  {_TERM}  ")

    # And two independent tasks anonymize the term to the identical token.
    task_a = _task(body=f"{_TERM} is here")
    task_b = _task(body=f"see {_TERM} again")
    apply_review(task_a, scan_task(task_a, [_TERM]), "anonymize", at=_AT)
    apply_review(task_b, scan_task(task_b, [_TERM]), "anonymize", at=_AT)

    token = stable_token(_TERM)
    assert token in task_a.body
    assert token in task_b.body
    assert _TERM not in task_a.body


def test_anonymize_token_shape() -> None:
    token = stable_token(_TERM)
    assert token.startswith("<<TERM_") and token.endswith(">>")
    assert len(token) == len("<<TERM_") + 6 + len(">>")


def test_keep_is_noop_on_content_but_records_review() -> None:
    task = _task(body=f"deploy with ghp_{_GH_BODY} now")
    before = task.body
    apply_review(task, scan_task(task, []), "keep", at=_AT)
    assert task.body == before
    assert task.confidentiality is not None
    assert task.confidentiality["decision"] == "keep"


def test_invalid_disposition_rejected() -> None:
    task = _task(body="x")
    with pytest.raises(ValueError):
        apply_review(task, [], "obliterate")


def test_replacement_rejects_non_transforming_disposition() -> None:
    from task_sync.confidential.apply import _replacement

    with pytest.raises(ValueError):
        _replacement("keep", "anything")


def test_unchanged_reviewed_task_not_reflagged() -> None:
    """A reviewed, unchanged task is honored silently (hash matches)."""
    task = _task(body=f"deploy with ghp_{_GH_BODY} now")
    assert needs_review(task) is True  # no record yet

    apply_review(task, scan_task(task, []), "redact", at=_AT)
    assert needs_review(task) is False  # reviewed, unchanged


def test_changed_task_resurfaces() -> None:
    task = _task(body="clean body")
    apply_review(task, [], "keep", at=_AT)
    assert needs_review(task) is False

    task.body = "clean body with a new secret pasted in"
    assert needs_review(task) is True


def test_needs_review_true_without_record() -> None:
    assert needs_review(_task(body="anything")) is True


def test_needs_review_true_with_empty_hash() -> None:
    task = _task(body="x")
    task.confidentiality = {"decision": "keep", "reviewed_hash": "", "at": _AT}
    assert needs_review(task) is True


def test_overlapping_finding_spans_transformed_once() -> None:
    """A span overlapping one already handled to its right is skipped."""
    from task_sync.confidential.finding import SEVERITY_HIGH, Finding

    task = _task(body="abcdefgh")
    findings = [
        Finding(span=(0, 5), category="x", severity=SEVERITY_HIGH, field="body"),
        Finding(span=(2, 4), category="y", severity=SEVERITY_HIGH, field="body"),
    ]
    apply_review(task, findings, "remove", at=_AT)
    # (2,4)->"cd" removed; the overlapping (0,5) is coalesced, not re-applied.
    assert task.body == "abefgh"


def test_apply_review_defaults_at_to_now() -> None:
    task = _task(body="clean")
    apply_review(task, [], "keep")
    assert task.confidentiality is not None
    assert task.confidentiality["at"]  # a real ISO timestamp was stamped


def test_multiple_findings_same_field_all_transformed() -> None:
    task = _task(body=f"a a@b.com b ghp_{_GH_BODY} c")
    apply_review(task, scan_task(task, []), "redact", at=_AT)
    assert "a@b.com" not in task.body
    assert _GH_BODY not in task.body
    assert task.body.count(REDACTION_MARK) == 2
