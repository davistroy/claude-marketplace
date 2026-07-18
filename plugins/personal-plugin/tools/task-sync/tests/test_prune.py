"""Prune-on-close: stale done+closed tasks are dropped, issues left closed.

A `done` task whose issue closed more than N days ago (N from config,
default 30) is removed from tasks.json — the closed issue on the tracker
becomes the archive. Everything else is kept, and pruning never reopens or
otherwise touches the issue.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from conftest import MockProvider
from task_sync.models import Task, TaskList
from task_sync.reconcile.apply import DEFAULT_PRUNE_DAYS, apply
from task_sync.reconcile.classify import content_hash
from task_sync.reconcile.plan import SyncPlan

NOW = datetime(2026, 7, 20, tzinfo=timezone.utc)


def _iso(days_ago: int) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


def _task(
    *,
    id: str = "t-1",
    status: str = "done",
    closed_days_ago: int | None = 40,
    issue_number: int | None = 1,
) -> Task:
    task = Task(
        id=id,
        title="task",
        status=status,
        issue_number=issue_number,
        closed_at=_iso(closed_days_ago) if closed_days_ago is not None else None,
    )
    task.last_synced = {"hash": content_hash(task), "at": _iso(closed_days_ago or 0)}
    return task


def _apply_prune(tasklist: TaskList) -> TaskList:
    """Apply an empty plan (no sync actions) so only pruning runs."""
    provider = MockProvider()
    return apply(SyncPlan(), {}, tasklist, provider, now=NOW)


def _ids(tasklist: TaskList) -> list[str]:
    return [t.id for t in tasklist.tasks]


# -- the core prune rule ---------------------------------------------------


def test_done_and_closed_beyond_threshold_is_pruned() -> None:
    tl = TaskList(config={}, tasks=[_task(closed_days_ago=40)])
    result = _apply_prune(tl)
    assert _ids(result) == []


def test_done_and_closed_within_threshold_is_kept() -> None:
    tl = TaskList(config={}, tasks=[_task(closed_days_ago=10)])
    result = _apply_prune(tl)
    assert _ids(result) == ["t-1"]


def test_prune_never_touches_the_issue() -> None:
    tl = TaskList(config={}, tasks=[_task(closed_days_ago=40)])
    provider = MockProvider()
    apply(SyncPlan(), {}, tl, provider, now=NOW)
    # No set_state / update / create — the closed issue is left as-is.
    assert provider.calls == []


# -- what must NOT be pruned -----------------------------------------------


def test_done_with_no_closed_at_is_kept() -> None:
    tl = TaskList(config={}, tasks=[_task(closed_days_ago=None)])
    assert _ids(_apply_prune(tl)) == ["t-1"]


def test_open_task_even_with_old_closed_at_is_kept() -> None:
    # Not "done" -> never pruned regardless of closed_at age.
    tl = TaskList(config={}, tasks=[_task(status="in-progress", closed_days_ago=99)])
    assert _ids(_apply_prune(tl)) == ["t-1"]


def test_exactly_threshold_days_is_kept() -> None:
    # Rule is strictly greater-than N days; exactly N is retained.
    tl = TaskList(config={}, tasks=[_task(closed_days_ago=DEFAULT_PRUNE_DAYS)])
    assert _ids(_apply_prune(tl)) == ["t-1"]


# -- config-driven threshold -----------------------------------------------


def test_custom_prune_days_from_config() -> None:
    # With N=7, a 10-day-old close is now stale.
    tl = TaskList(config={"prune_closed_after_days": 7}, tasks=[_task(closed_days_ago=10)])
    assert _ids(_apply_prune(tl)) == []


def test_larger_prune_days_keeps_a_default_stale_task() -> None:
    tl = TaskList(config={"prune_closed_after_days": 90}, tasks=[_task(closed_days_ago=40)])
    assert _ids(_apply_prune(tl)) == ["t-1"]


def test_invalid_prune_config_falls_back_to_default() -> None:
    tl = TaskList(
        config={"prune_closed_after_days": "not-a-number"}, tasks=[_task(closed_days_ago=40)]
    )
    # Falls back to 30 -> 40 days is still pruned.
    assert _ids(_apply_prune(tl)) == []


# -- prune runs alongside real sync actions --------------------------------


def test_prune_mixes_with_kept_tasks() -> None:
    tl = TaskList(
        config={},
        tasks=[
            _task(id="stale", closed_days_ago=40),
            _task(id="fresh", closed_days_ago=5),
            _task(id="working", status="todo", closed_days_ago=None, issue_number=2),
        ],
    )
    assert sorted(_ids(_apply_prune(tl))) == ["fresh", "working"]
