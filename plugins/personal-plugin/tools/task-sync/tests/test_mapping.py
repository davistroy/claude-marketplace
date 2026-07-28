"""Status/priority/milestone mapping round-trips, both directions."""

from __future__ import annotations

import pytest

from task_sync.models import VALID_PRIORITIES, VALID_STATUSES, Task
from task_sync.providers.base import Issue, parse_aware_datetime
from task_sync.reconcile.mapping import (
    is_managed_label,
    issue_to_task_fields,
    managed_labels_for,
    task_to_issue_fields,
    user_labels,
)

_AT = parse_aware_datetime("2026-07-10T00:00:00Z")


def _issue(**kw: object) -> Issue:
    base: dict[str, object] = {
        "number": 1,
        "title": "T",
        "body": "b",
        "state": "open",
        "labels": [],
        "milestone": None,
        "updated_at": _AT,
        "closed_at": None,
    }
    base.update(kw)
    return Issue(**base)  # type: ignore[arg-type]


def _task(**kw: object) -> Task:
    base: dict[str, object] = {"id": "t-1", "title": "T", "body": "b", "status": "todo"}
    base.update(kw)
    return Task(**base)  # type: ignore[arg-type]


# -- status: task -> issue -------------------------------------------------


@pytest.mark.parametrize(
    "status,expected_state,expected_status_label",
    [
        ("backlog", "open", "status/backlog"),
        ("todo", "open", None),
        ("in-progress", "open", "status/in-progress"),
        ("blocked", "open", "status/blocked"),
        ("done", "closed", None),
    ],
)
def test_status_to_issue(
    status: str, expected_state: str, expected_status_label: str | None
) -> None:
    fields = task_to_issue_fields(_task(status=status))
    assert fields["state"] == expected_state
    status_labels = [label for label in fields["labels"] if label.startswith("status/")]
    if expected_status_label is None:
        assert status_labels == []
    else:
        assert status_labels == [expected_status_label]


def test_in_progress_pushes_open_with_exactly_one_status_label() -> None:
    fields = task_to_issue_fields(_task(status="in-progress"))
    assert fields["state"] == "open"
    status_labels = [label for label in fields["labels"] if label.startswith("status/")]
    assert status_labels == ["status/in-progress"]  # and no other status/*


# -- status: issue -> task -------------------------------------------------


@pytest.mark.parametrize(
    "state,labels,expected_status",
    [
        ("open", ["status/backlog"], "backlog"),
        ("open", [], "todo"),
        ("open", ["status/in-progress"], "in-progress"),
        ("open", ["status/blocked"], "blocked"),
        ("closed", [], "done"),
        ("closed", ["status/in-progress"], "done"),  # closed always wins
        ("open", ["status/unknown"], "todo"),  # unrecognized -> default
    ],
)
def test_issue_to_status(state: str, labels: list[str], expected_status: str) -> None:
    fields = issue_to_task_fields(_issue(state=state, labels=labels))
    assert fields["status"] == expected_status


# -- full status round-trips -----------------------------------------------


@pytest.mark.parametrize("status", ["backlog", "todo", "in-progress", "blocked", "done"])
def test_status_round_trip(status: str) -> None:
    """task -> issue fields -> issue -> task fields recovers the status,
    and no stray status/* label survives the round-trip."""
    issue_fields = task_to_issue_fields(_task(status=status))
    issue = _issue(state=issue_fields["state"], labels=issue_fields["labels"])
    back = issue_to_task_fields(issue)
    assert back["status"] == status
    assert [label for label in back["labels"] if label.startswith("status/")] == []


# -- priority --------------------------------------------------------------


# Derived from VALID_PRIORITIES, never hardcoded: a literal list here is what
# let P0's absence go unnoticed (#208) — the test agreed with the bug.
@pytest.mark.parametrize("priority", VALID_PRIORITIES)
def test_priority_round_trip(priority: str) -> None:
    issue_fields = task_to_issue_fields(_task(priority=priority))
    assert f"priority/{priority}" in issue_fields["labels"]
    issue = _issue(labels=issue_fields["labels"])
    back = issue_to_task_fields(issue)
    assert back["priority"] == priority
    assert [label for label in back["labels"] if label.startswith("priority/")] == []


def test_no_priority_emits_no_priority_label_and_reads_back_none() -> None:
    fields = task_to_issue_fields(_task(priority=None))
    assert [label for label in fields["labels"] if label.startswith("priority/")] == []
    assert issue_to_task_fields(_issue(labels=[]))["priority"] is None


def test_unknown_priority_label_is_ignored() -> None:
    assert issue_to_task_fields(_issue(labels=["priority/P9"]))["priority"] is None


# -- milestone -------------------------------------------------------------


def test_milestone_both_ways() -> None:
    assert task_to_issue_fields(_task(milestone="v2.0"))["milestone"] == "v2.0"
    assert issue_to_task_fields(_issue(milestone="v2.0"))["milestone"] == "v2.0"


def test_milestone_none_both_ways() -> None:
    assert task_to_issue_fields(_task(milestone=None))["milestone"] is None
    assert issue_to_task_fields(_issue(milestone=None))["milestone"] is None


# -- user labels vs managed labels -----------------------------------------


def test_user_labels_preserved_managed_stripped_on_pull() -> None:
    issue = _issue(labels=["bug", "status/in-progress", "priority/P1", "area/api"])
    back = issue_to_task_fields(issue)
    assert back["labels"] == ["bug", "area/api"]
    assert back["status"] == "in-progress"
    assert back["priority"] == "P1"


def test_push_strips_existing_managed_labels_before_reapplying() -> None:
    # A task that somehow already carries a stale status/* label must not
    # emit two — the mapping recomputes managed labels from scratch.
    task = _task(status="blocked", priority="P2", labels=["bug", "status/todo", "priority/P4"])
    fields = task_to_issue_fields(task)
    status_labels = [label for label in fields["labels"] if label.startswith("status/")]
    priority_labels = [label for label in fields["labels"] if label.startswith("priority/")]
    assert status_labels == ["status/blocked"]
    assert priority_labels == ["priority/P2"]
    assert "bug" in fields["labels"]


def test_managed_labels_for_helper() -> None:
    assert managed_labels_for(_task(status="in-progress", priority="P1")) == [
        "status/in-progress",
        "priority/P1",
    ]
    assert managed_labels_for(_task(status="todo", priority=None)) == []


def test_is_managed_and_user_labels_helpers() -> None:
    assert is_managed_label("status/blocked")
    assert is_managed_label("priority/P3")
    assert not is_managed_label("bug")
    assert user_labels(["bug", "status/todo", "priority/P1", "docs"]) == ["bug", "docs"]


# --- #208 regression: unrecognized managed-namespace labels must survive ---
#
# The bug: `is_managed_label` claimed EVERY status/* and priority/* label
# regardless of whether the suffix was recognized, so `user_labels()` stripped
# it while the reverse mapping declined to capture it. On the next push the
# label was absent from `desired`, and the provider's `current - desired`
# diff emitted `--remove-label` — deleting a label the tool never understood.


@pytest.mark.parametrize("priority", VALID_PRIORITIES)
def test_every_valid_priority_survives_a_full_round_trip(priority: str) -> None:
    issue = _issue(labels=["bug", f"priority/{priority}"])
    fields = issue_to_task_fields(issue)
    assert fields["priority"] == priority

    task = _task(**fields, issue_number=issue.number)
    assert f"priority/{priority}" in task_to_issue_fields(task)["labels"]


@pytest.mark.parametrize("suffix", ["P9", "P10", "urgent", "critical", ""])
def test_unknown_priority_label_is_preserved_not_deleted(suffix: str) -> None:
    # An unrecognized suffix is NOT ours to manage. It must stay in the user
    # label set so the push diff never proposes removing it.
    label = f"priority/{suffix}"
    issue = _issue(labels=["bug", label])
    fields = issue_to_task_fields(issue)

    assert fields["priority"] is None, "unknown suffix must not become a priority"
    assert label in fields["labels"], "unknown label must be preserved, not swallowed"

    task = _task(**fields, issue_number=issue.number)
    desired = task_to_issue_fields(task)["labels"]
    assert label in desired, "push must not drop the label (provider would --remove-label it)"
    assert not set(issue.labels) - set(desired), (
        "push must never propose removing an existing label"
    )


@pytest.mark.parametrize("suffix", ["wontfix", "archived", "P1"])
def test_unknown_status_label_is_preserved_not_deleted(suffix: str) -> None:
    label = f"status/{suffix}"
    issue = _issue(labels=["bug", label])
    fields = issue_to_task_fields(issue)

    assert fields["status"] == "todo", "unknown status label falls back to the default"
    assert label in fields["labels"]

    task = _task(**fields, issue_number=issue.number)
    assert not set(issue.labels) - set(task_to_issue_fields(task)["labels"])


def test_is_managed_label_claims_only_recognized_suffixes() -> None:
    for status in VALID_STATUSES:
        assert is_managed_label(f"status/{status}")
    for priority in VALID_PRIORITIES:
        assert is_managed_label(f"priority/{priority}")

    for stranger in ("status/wontfix", "priority/P9", "priority/urgent", "status/", "priority/"):
        assert not is_managed_label(stranger), f"{stranger} is not ours to delete"

    assert not is_managed_label("bug")
    assert not is_managed_label("statusish/x")


def test_p0_is_a_valid_priority() -> None:
    # #208: P0 was absent from VALID_PRIORITIES while the repo's own issue
    # titles used a [P0]-[P3] scale, so the highest-severity label was the one
    # value the tool could not represent.
    assert "P0" in VALID_PRIORITIES
    issue = _issue(labels=["bug", "priority/P0"])
    fields = issue_to_task_fields(issue)
    assert fields["priority"] == "P0"
    assert fields["labels"] == ["bug"], "a recognized priority label IS stripped into the field"
    assert "priority/P0" in task_to_issue_fields(_task(**fields))["labels"]
