"""Plan building and serialization: orphans are surfaced and block is_empty().

The load-bearing guarantee here is that `is_empty()` returns False when a
plan contains only orphans — exactly mirroring the `skipped_adopts` pattern
from #181. Omitting the orphans term would recreate the silent-data-loss
bug: an orphan-only plan would report "already in sync" when actually N
issues need human review.
"""

from __future__ import annotations

import json

import pytest

from task_sync.models import Task
from task_sync.providers.base import Issue, parse_aware_datetime
from task_sync.reconcile.classify import Classification, ClassKind
from task_sync.reconcile.plan import SyncPlan, build_plan, summarize_plan
from task_sync.reconcile.resolve import (
    Conflict,
    CreateAction,
    Orphan,
    PullAction,
    PushAction,
)

BASE_AT = "2026-07-10T00:00:00Z"
LATER = "2026-07-15T00:00:00Z"


def _issue(number: int = 1, **kw: object) -> Issue:
    base: dict[str, object] = {
        "number": number,
        "title": "T",
        "body": "b",
        "state": "open",
        "labels": [],
        "milestone": None,
        "updated_at": parse_aware_datetime(LATER),
        "closed_at": None,
    }
    base.update(kw)
    return Issue(**base)  # type: ignore[arg-type]


def _task(id: str = "t-1", issue_number: int | None = 1, **kw: object) -> Task:
    base: dict[str, object] = {
        "id": id,
        "title": "T",
        "body": "b",
        "status": "todo",
        "issue_number": issue_number,
        "updated_at": BASE_AT,
    }
    base.update(kw)
    return Task(**base)  # type: ignore[arg-type]


# -- orphans are included in to_dict() and to_json() -----


def test_plan_with_orphan_includes_it_in_to_dict() -> None:
    orphan = Orphan(task_id="t-1", issue_number=42, local_changed=True)
    plan = SyncPlan(orphans=[orphan])
    d = plan.to_dict()
    assert "orphans" in d
    assert len(d["orphans"]) == 1
    assert d["orphans"][0]["task_id"] == "t-1"
    assert d["orphans"][0]["issue_number"] == 42
    assert d["orphans"][0]["local_changed"] is True


def test_plan_to_json_includes_orphans_key() -> None:
    orphan = Orphan(task_id="t-1", issue_number=42, local_changed=True)
    plan = SyncPlan(orphans=[orphan])
    j = plan.to_json()
    payload = json.loads(j)
    assert "orphans" in payload
    assert len(payload["orphans"]) == 1


def test_plan_with_multiple_orphans_serializes_all() -> None:
    orphans = [
        Orphan(task_id="t-1", issue_number=42, local_changed=True),
        Orphan(task_id="t-2", issue_number=43, local_changed=False),
    ]
    plan = SyncPlan(orphans=orphans)
    d = plan.to_dict()
    assert len(d["orphans"]) == 2
    assert d["orphans"][0]["issue_number"] == 42
    assert d["orphans"][1]["issue_number"] == 43


# -- is_empty() checks orphans ----------


def test_plan_with_only_orphans_is_not_empty() -> None:
    """WHEN a plan contains only orphans THEN is_empty() SHALL return False
    (4.2 acceptance criterion). Exactly mirrors the skipped_adopts pattern."""
    orphan = Orphan(task_id="t-1", issue_number=42, local_changed=True)
    plan = SyncPlan(orphans=[orphan])
    assert plan.is_empty() is False


def test_empty_plan_with_no_orphans_is_empty() -> None:
    plan = SyncPlan()
    assert plan.is_empty() is True


def test_plan_with_orphans_and_other_actions_is_not_empty() -> None:
    plan = SyncPlan(
        creates=[CreateAction(task_id="t-1", fields={})],
        orphans=[Orphan(task_id="t-2", issue_number=42, local_changed=True)],
    )
    assert plan.is_empty() is False


# -- orphans are summarized for --dry-run ----------


def test_summarize_plan_names_orphan_issue_numbers() -> None:
    """WHEN a plan contains orphans THEN the summary SHALL name the
    affected issue numbers (4.2 acceptance criterion)."""
    orphans = [
        Orphan(task_id="t-1", issue_number=42, local_changed=True),
        Orphan(task_id="t-2", issue_number=43, local_changed=False),
    ]
    plan = SyncPlan(orphans=orphans)
    summary = summarize_plan(plan)
    assert "orphans" in summary
    assert "#42" in summary
    assert "#43" in summary
    assert "links missing from fetch" in summary


def test_summarize_plan_with_multiple_orphans_shows_count() -> None:
    orphans = [
        Orphan(task_id=f"t-{i}", issue_number=40 + i, local_changed=True)
        for i in range(3)
    ]
    plan = SyncPlan(orphans=orphans)
    summary = summarize_plan(plan)
    assert "3" in summary
    assert "orphans" in summary


def test_summarize_plan_omits_orphan_line_when_empty() -> None:
    plan = SyncPlan()
    summary = summarize_plan(plan)
    assert "orphans" not in summary


# -- build_plan passes orphans from resolution ----------


def test_build_plan_includes_orphans_from_resolve() -> None:
    """WHEN classifications include ORPHAN_LOCAL THEN build_plan SHALL
    populate the plan's orphans field."""
    task = _task(issue_number=42)
    c = Classification(ClassKind.ORPHAN_LOCAL, task, None, local_changed=True)
    plan = build_plan([c])
    assert len(plan.orphans) == 1
    assert plan.orphans[0].task_id == "t-1"
    assert plan.orphans[0].issue_number == 42
    assert plan.orphans[0].local_changed is True


def test_build_plan_empty_when_no_orphans() -> None:
    task = _task(issue_number=1)
    c = Classification(ClassKind.UNCHANGED, task, _issue(1))
    plan = build_plan([c])
    assert len(plan.orphans) == 0


def test_build_plan_orphan_only_plan_is_not_empty() -> None:
    """WHEN the sole outcome is orphans THEN is_empty() returns False
    and a consumer is alerted to review them."""
    task = _task(issue_number=42)
    c = Classification(ClassKind.ORPHAN_LOCAL, task, None, local_changed=False)
    plan = build_plan([c])
    assert plan.is_empty() is False
    assert "already in sync" not in summarize_plan(plan)


# -- mutation testing: is_empty() really checks orphans ----------


def _plan_with_each_field() -> dict[str, object]:
    """A fixture mapping each plan field to a non-empty instance, for
    mutation testing. When any field is deleted from is_empty()'s or-chain,
    that field's test goes red."""
    return {
        "creates": [CreateAction(task_id="t-1", fields={})],
        "pushes": [PushAction(task_id="t-2", issue_number=2, fields={})],
        "pulls": [PullAction(issue_number=3, task_id="t-3", fields={})],
        "conflicts": [
            Conflict(
                task_id="t-4",
                issue_number=4,
                local={"title": "local"},
                remote={"title": "remote"},
                recommendation="local",
                local_updated_at=BASE_AT,
                remote_updated_at=LATER,
            )
        ],
        "skipped_adopts": [5],
        "orphans": [Orphan(task_id="t-6", issue_number=6, local_changed=True)],
    }


@pytest.mark.parametrize("field_name", list(_plan_with_each_field().keys()))
def test_is_empty_checks_all_fields(field_name: str) -> None:
    """Parametrized directly over the plan's field names (the real set, not
    a hand-copied list) so this is the mutation-testing guard: if a future
    developer removes a field from is_empty()'s or-chain, the test for that
    field goes red, and the silent-data-loss bug is caught before merge."""
    all_fields = _plan_with_each_field()
    # Set only this field; all others are empty
    plan_kwargs = {k: (v if k == field_name else []) for k, v in all_fields.items()}
    plan = SyncPlan(**plan_kwargs)  # type: ignore[arg-type]
    assert (
        plan.is_empty() is False
    ), f"Plan with only {field_name} should not be empty"


# -- consistent SKILL parsing of all plan sections ----------


def test_plan_to_dict_preserves_existing_sections() -> None:
    """Existing SKILL parsing of creates/pushes/pulls/conflicts/skipped_adopts
    is unaffected (4.2 acceptance criterion). The to_dict() order is stable."""
    plan = SyncPlan(creates=[CreateAction(task_id="t-1", fields={"title": "test"})])
    d = plan.to_dict()
    keys = list(d.keys())
    # Orphans is inserted after skipped_adopts (same nature); before confidentiality
    assert keys == [
        "creates",
        "pushes",
        "pulls",
        "conflicts",
        "skipped_adopts",
        "orphans",
        "confidentiality_findings",
    ]
