"""Exhaustive three-way classification matrix.

Every branch of `classify` is covered: the four steady-state verdicts
(unchanged / changed-local / changed-remote / changed-both), both "new"
verdicts (new-local / new-remote), the orphan fallback (issue vanished), and
the conservative missing-base behaviour.
"""

from __future__ import annotations

from task_sync.models import Task, TaskList
from task_sync.providers.base import Issue, parse_aware_datetime
from task_sync.reconcile.classify import Classification, ClassKind, classify, content_hash

BASE_AT = "2026-07-10T00:00:00Z"
LATER = "2026-07-15T00:00:00Z"


def _issue(
    number: int = 1,
    *,
    title: str = "Fix the bug",
    body: str = "details",
    state: str = "open",
    labels: list[str] | None = None,
    milestone: str | None = None,
    updated: str = BASE_AT,
    closed: str | None = None,
) -> Issue:
    return Issue(
        number=number,
        title=title,
        body=body,
        state=state,
        labels=labels or [],
        milestone=milestone,
        updated_at=parse_aware_datetime(updated),  # type: ignore[arg-type]
        closed_at=parse_aware_datetime(closed),
    )


def _task(
    *,
    id: str = "t-1",
    title: str = "Fix the bug",
    body: str = "details",
    status: str = "todo",
    priority: str | None = None,
    labels: list[str] | None = None,
    milestone: str | None = None,
    issue_number: int | None = 1,
    updated_at: str = BASE_AT,
    base_at: str | None = BASE_AT,
    set_base: bool = True,
) -> Task:
    """Build a task and, by default, seed an in-sync `last_synced` base.

    The base hash is computed from the task *as built*, so mutating a field
    afterwards makes it look locally changed — exactly how the real store
    drifts between syncs.
    """
    task = Task(
        id=id,
        title=title,
        body=body,
        status=status,
        priority=priority,
        labels=labels or [],
        milestone=milestone,
        issue_number=issue_number,
        updated_at=updated_at,
    )
    if set_base and issue_number is not None:
        base: dict[str, object] = {"hash": content_hash(task)}
        if base_at is not None:
            base["at"] = base_at
        task.last_synced = base
    return task


def _one(tasks: list[Task], issues: list[Issue]) -> list[Classification]:
    return classify(TaskList(tasks=tasks), issues)


# -- content_hash ----------------------------------------------------------


def test_content_hash_ignores_label_order() -> None:
    a = _task(labels=["x", "y"], set_base=False)
    b = _task(labels=["y", "x"], set_base=False)
    assert content_hash(a) == content_hash(b)


def test_content_hash_changes_with_title() -> None:
    a = _task(title="one", set_base=False)
    b = _task(title="two", set_base=False)
    assert content_hash(a) != content_hash(b)


def test_content_hash_ignores_issue_number_and_timestamps() -> None:
    a = _task(issue_number=None, updated_at="2026-01-01T00:00:00Z", set_base=False)
    b = _task(issue_number=999, updated_at="2030-01-01T00:00:00Z", set_base=False)
    assert content_hash(a) == content_hash(b)


# -- the six verdicts ------------------------------------------------------


def test_new_local_when_task_has_no_issue_number() -> None:
    task = _task(issue_number=None)
    result = _one([task], [])
    assert [c.kind for c in result] == [ClassKind.NEW_LOCAL]
    assert result[0].task is task and result[0].issue is None


def test_new_remote_when_issue_has_no_matching_task() -> None:
    issue = _issue(number=5)
    result = _one([], [issue])
    assert [c.kind for c in result] == [ClassKind.NEW_REMOTE]
    assert result[0].issue is issue and result[0].task is None


def test_unchanged_when_neither_side_moved() -> None:
    task = _task()
    issue = _issue(updated=BASE_AT)  # updated == base -> not > base -> unchanged
    (c,) = _one([task], [issue])
    assert c.kind is ClassKind.UNCHANGED
    assert not c.local_changed and not c.remote_changed


def test_changed_local_only() -> None:
    task = _task()
    task.title = "edited locally"  # diverges from base hash
    issue = _issue(updated=BASE_AT)
    (c,) = _one([task], [issue])
    assert c.kind is ClassKind.CHANGED_LOCAL
    assert c.local_changed and not c.remote_changed


def test_changed_remote_only() -> None:
    task = _task()  # content matches base
    issue = _issue(updated=LATER)  # updated after base
    (c,) = _one([task], [issue])
    assert c.kind is ClassKind.CHANGED_REMOTE
    assert c.remote_changed and not c.local_changed


def test_changed_both_is_conflict_candidate() -> None:
    task = _task()
    task.body = "locally edited body"
    issue = _issue(updated=LATER)
    (c,) = _one([task], [issue])
    assert c.kind is ClassKind.CHANGED_BOTH
    assert c.local_changed and c.remote_changed


# -- orphan (task's issue vanished from the tracker) -----------------------


def test_orphan_unchanged_is_unchanged() -> None:
    task = _task(issue_number=42)
    (c,) = _one([task], [])  # no issue #42 present
    assert c.kind is ClassKind.UNCHANGED
    assert c.issue is None


def test_orphan_changed_is_changed_local() -> None:
    task = _task(issue_number=42)
    task.title = "edited"
    (c,) = _one([task], [])
    assert c.kind is ClassKind.CHANGED_LOCAL
    assert c.issue is None and c.local_changed


# -- conservative missing-base behaviour -----------------------------------


def test_missing_base_hash_counts_as_local_change() -> None:
    task = _task(set_base=False)  # last_synced == {}
    task.last_synced = {"at": BASE_AT}  # timestamp present, hash absent
    issue = _issue(updated=BASE_AT)
    (c,) = _one([task], [issue])
    assert c.kind is ClassKind.CHANGED_LOCAL
    assert c.local_changed


def test_missing_base_timestamp_counts_as_remote_change() -> None:
    task = _task()
    task.last_synced = {"hash": task.last_synced["hash"]}  # drop "at"
    issue = _issue(updated=BASE_AT)
    (c,) = _one([task], [issue])
    assert c.kind is ClassKind.CHANGED_REMOTE
    assert c.remote_changed


def test_empty_base_counts_as_changed_both() -> None:
    task = _task(set_base=False)  # no hash, no at
    issue = _issue(updated=BASE_AT)
    (c,) = _one([task], [issue])
    assert c.kind is ClassKind.CHANGED_BOTH


# -- matching + exhaustiveness ---------------------------------------------


def test_matches_on_issue_number_across_a_mixed_set() -> None:
    t_new = _task(id="t-new", issue_number=None)
    t_linked = _task(id="t-linked", issue_number=2)
    t_linked.title = "changed"
    issues = [_issue(number=2, updated=BASE_AT), _issue(number=9)]  # #9 unmatched
    result = _one([t_new, t_linked], issues)

    kinds = {(c.task.id if c.task else None, c.kind) for c in result}
    assert ("t-new", ClassKind.NEW_LOCAL) in kinds
    assert ("t-linked", ClassKind.CHANGED_LOCAL) in kinds
    assert any(c.kind is ClassKind.NEW_REMOTE and c.issue.number == 9 for c in result)


def test_every_task_and_issue_appears_exactly_once() -> None:
    tasks = [_task(id="t-1", issue_number=1), _task(id="t-2", issue_number=None)]
    issues = [_issue(number=1), _issue(number=3)]
    result = _one(tasks, issues)
    # 2 tasks + 1 unmatched issue = 3 classifications
    assert len(result) == 3
    task_ids = [c.task.id for c in result if c.task]
    issue_nums = [c.issue.number for c in result if c.issue and c.task is None]
    assert sorted(task_ids) == ["t-1", "t-2"]
    assert issue_nums == [3]
