"""Resolution: one-sided changes become actions; conflicts are surfaced.

The load-bearing guarantee here is that a `CHANGED_BOTH` classification is
NEVER turned into a push or a pull — it is emitted as a `Conflict` for a
human, with a recommendation but no applied change.
"""

from __future__ import annotations

from task_sync.models import Task
from task_sync.providers.base import Issue, parse_aware_datetime
from task_sync.reconcile.classify import Classification, ClassKind
from task_sync.reconcile.resolve import resolve

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


# -- one-sided changes -> directional actions ------------------------------


def test_new_local_becomes_a_create() -> None:
    c = Classification(ClassKind.NEW_LOCAL, _task(issue_number=None), None)
    r = resolve([c])
    assert len(r.creates) == 1 and not r.pushes and not r.pulls and not r.conflicts
    assert r.creates[0].task_id == "t-1"
    assert r.creates[0].fields["state"] == "open"


def test_changed_local_becomes_a_push() -> None:
    c = Classification(
        ClassKind.CHANGED_LOCAL, _task(issue_number=7), _issue(7), local_changed=True
    )
    r = resolve([c])
    assert len(r.pushes) == 1 and not r.creates and not r.pulls
    assert r.pushes[0].issue_number == 7


def test_orphan_changed_local_becomes_a_create_not_a_push() -> None:
    # issue_number is None (the issue vanished) but the local task changed:
    # there is nothing to push to, so re-create it.
    c = Classification(ClassKind.CHANGED_LOCAL, _task(issue_number=None), None, local_changed=True)
    r = resolve([c])
    assert len(r.creates) == 1 and not r.pushes


def test_new_remote_becomes_an_adopt_pull() -> None:
    c = Classification(ClassKind.NEW_REMOTE, None, _issue(3), remote_changed=True)
    r = resolve([c])
    assert len(r.pulls) == 1
    assert r.pulls[0].task_id is None  # adopt
    assert r.pulls[0].issue_number == 3
    assert r.pulls[0].issue_updated_at == parse_aware_datetime(LATER).isoformat()


def test_changed_remote_becomes_an_update_pull() -> None:
    c = Classification(
        ClassKind.CHANGED_REMOTE, _task(issue_number=4), _issue(4), remote_changed=True
    )
    r = resolve([c])
    assert len(r.pulls) == 1
    assert r.pulls[0].task_id == "t-1"


def test_unchanged_produces_no_action() -> None:
    c = Classification(ClassKind.UNCHANGED, _task(), _issue())
    r = resolve([c])
    assert not (r.creates or r.pushes or r.pulls or r.conflicts)


# -- closed-remote -> done on pull -----------------------------------------


def test_closed_remote_issue_pulls_task_to_done() -> None:
    issue = _issue(5, state="closed", closed_at=parse_aware_datetime(LATER))
    c = Classification(ClassKind.CHANGED_REMOTE, _task(issue_number=5), issue, remote_changed=True)
    r = resolve([c])
    assert r.pulls[0].fields["status"] == "done"
    assert r.pulls[0].issue_closed_at == parse_aware_datetime(LATER).isoformat()


# -- CHANGED_BOTH -> conflict, never clobbered -----------------------------


def test_changed_both_emits_conflict_and_no_write_action() -> None:
    task = _task(issue_number=8, title="local title")
    issue = _issue(8, title="remote title")
    c = Classification(ClassKind.CHANGED_BOTH, task, issue, local_changed=True, remote_changed=True)
    r = resolve([c])
    assert not r.pushes and not r.pulls and not r.creates  # nothing applied
    assert len(r.conflicts) == 1
    conflict = r.conflicts[0]
    assert conflict.task_id == "t-1" and conflict.issue_number == 8
    assert conflict.local["title"] == "local title"
    assert conflict.remote["title"] == "remote title"


def test_conflict_recommends_local_when_local_is_newer() -> None:
    task = _task(issue_number=1, updated_at=LATER)  # local newer than remote base
    issue = _issue(1, updated_at=parse_aware_datetime(BASE_AT))
    c = Classification(ClassKind.CHANGED_BOTH, task, issue, local_changed=True, remote_changed=True)
    assert resolve([c]).conflicts[0].recommendation == "local"


def test_conflict_recommends_remote_when_remote_is_newer() -> None:
    task = _task(issue_number=1, updated_at=BASE_AT)
    issue = _issue(1, updated_at=parse_aware_datetime(LATER))
    c = Classification(ClassKind.CHANGED_BOTH, task, issue, local_changed=True, remote_changed=True)
    assert resolve([c]).conflicts[0].recommendation == "remote"


def test_conflict_recommends_remote_on_tie() -> None:
    task = _task(issue_number=1, updated_at=BASE_AT)
    issue = _issue(1, updated_at=parse_aware_datetime(BASE_AT))
    c = Classification(ClassKind.CHANGED_BOTH, task, issue, local_changed=True, remote_changed=True)
    assert resolve([c]).conflicts[0].recommendation == "remote"


def test_conflict_recommends_remote_when_local_timestamp_missing() -> None:
    task = _task(issue_number=1, updated_at=None)
    issue = _issue(1, updated_at=parse_aware_datetime(LATER))
    c = Classification(ClassKind.CHANGED_BOTH, task, issue, local_changed=True, remote_changed=True)
    conflict = resolve([c]).conflicts[0]
    assert conflict.recommendation == "remote"
    assert conflict.local_updated_at is None


# -- mixed batch -----------------------------------------------------------


def test_mixed_batch_splits_into_all_buckets() -> None:
    classifications = [
        Classification(ClassKind.NEW_LOCAL, _task("a", issue_number=None), None),
        Classification(
            ClassKind.CHANGED_LOCAL, _task("b", issue_number=2), _issue(2), local_changed=True
        ),
        Classification(ClassKind.NEW_REMOTE, None, _issue(3), remote_changed=True),
        Classification(
            ClassKind.CHANGED_BOTH,
            _task("d", issue_number=4),
            _issue(4),
            local_changed=True,
            remote_changed=True,
        ),
        Classification(ClassKind.UNCHANGED, _task("e", issue_number=5), _issue(5)),
    ]
    r = resolve(classifications)
    assert len(r.creates) == 1
    assert len(r.pushes) == 1
    assert len(r.pulls) == 1
    assert len(r.conflicts) == 1
