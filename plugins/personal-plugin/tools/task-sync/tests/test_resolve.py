"""Resolution: one-sided changes become actions; conflicts are surfaced.

The load-bearing guarantee here is that a `CHANGED_BOTH` classification is
NEVER turned into a push or a pull — it is emitted as a `Conflict` for a
human, with a recommendation but no applied change.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from task_sync.models import Task
from task_sync.providers.base import Issue, parse_aware_datetime
from task_sync.reconcile.classify import Classification, ClassKind
from task_sync.reconcile.resolve import Orphan, resolve

BASE_AT = "2026-07-10T00:00:00Z"
LATER = "2026-07-15T00:00:00Z"
ADOPT_NOW = datetime(2026, 7, 20, tzinfo=timezone.utc)
ADOPT_WINDOW_DAYS = 30


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


# -- ORPHAN_LOCAL -> an Orphan record, never a push/create (#181) ----------


def test_orphan_local_changed_is_surfaced_as_orphan_not_a_push_or_create() -> None:
    task = _task(issue_number=42)
    c = Classification(ClassKind.ORPHAN_LOCAL, task, None, local_changed=True)
    r = resolve([c])
    assert not r.pushes and not r.creates and not r.pulls and not r.conflicts
    assert len(r.orphans) == 1
    assert isinstance(r.orphans[0], Orphan)
    assert r.orphans[0].task_id == "t-1"
    assert r.orphans[0].issue_number == 42
    assert r.orphans[0].local_changed is True


def test_orphan_local_unchanged_is_still_surfaced_not_dropped() -> None:
    """WHEN an orphaned task has no local edit THEN it SHALL still be
    surfaced, not silently omitted (4.1 acceptance criterion)."""
    task = _task(issue_number=42)
    c = Classification(ClassKind.ORPHAN_LOCAL, task, None, local_changed=False)
    r = resolve([c])
    assert len(r.orphans) == 1
    assert r.orphans[0].local_changed is False


def test_orphan_local_never_produces_a_push_even_though_issue_number_is_set() -> None:
    """The #181 regression this whole item exists to close: `task.issue_number`
    is still populated (it's the vanished number, classify never nulls it),
    so `resolve` must route on `kind`, never re-derive "is this an orphan"
    from `issue_number is None` -- that reasoning is exactly what let a
    CHANGED_BOTH-shaped clobber (including reopening a closed issue) slip
    through as a one-sided push before ORPHAN_LOCAL existed."""
    task = _task(issue_number=42)
    assert task.issue_number == 42  # sanity: NOT nulled anywhere upstream
    c = Classification(ClassKind.ORPHAN_LOCAL, task, None, local_changed=True)
    r = resolve([c])
    assert r.pushes == []
    assert r.creates == []
    assert r.orphans[0].issue_number == 42


def _classification_for(kind: ClassKind) -> Classification:
    """Build a realistically-shaped Classification for every current
    ClassKind member, keyed on the enum itself (never a hand-copied list of
    member names) so a future member is forced through this fixture -- and
    therefore through the parametrized exhaustiveness test below -- instead
    of silently falling through resolve()'s if/elif chain with no action."""
    if kind is ClassKind.NEW_LOCAL:
        return Classification(kind, _task("nl", issue_number=None), None)
    if kind is ClassKind.CHANGED_LOCAL:
        return Classification(kind, _task("cl", issue_number=7), _issue(7), local_changed=True)
    if kind is ClassKind.NEW_REMOTE:
        return Classification(kind, None, _issue(3), remote_changed=True)
    if kind is ClassKind.CHANGED_REMOTE:
        return Classification(kind, _task("cr", issue_number=4), _issue(4), remote_changed=True)
    if kind is ClassKind.CHANGED_BOTH:
        return Classification(
            kind, _task("cb", issue_number=8), _issue(8), local_changed=True, remote_changed=True
        )
    if kind is ClassKind.UNCHANGED:
        return Classification(kind, _task("un", issue_number=5), _issue(5))
    if kind is ClassKind.ORPHAN_LOCAL:
        return Classification(kind, _task("or", issue_number=42), None, local_changed=True)
    raise AssertionError(f"unhandled ClassKind member in test fixture: {kind!r}")


@pytest.mark.parametrize("kind", list(ClassKind))
def test_only_orphan_local_ever_produces_an_orphan_record(kind: ClassKind) -> None:
    """Parametrized directly over `list(ClassKind)` -- the real enum, not a
    copy -- so this is the guard the #181 fix depends on: no matter what
    members ClassKind grows in the future, exactly one of them (ORPHAN_LOCAL)
    may ever populate `ResolveResult.orphans`, and it never also produces a
    push or a create."""
    c = _classification_for(kind)
    r = resolve([c])
    if kind is ClassKind.ORPHAN_LOCAL:
        assert len(r.orphans) == 1
        assert not r.pushes and not r.creates
    else:
        assert r.orphans == []


def test_new_remote_becomes_an_adopt_pull() -> None:
    c = Classification(ClassKind.NEW_REMOTE, None, _issue(3), remote_changed=True)
    r = resolve([c])
    assert len(r.pulls) == 1
    assert r.pulls[0].task_id is None  # adopt
    assert r.pulls[0].issue_number == 3
    assert r.pulls[0].issue_updated_at == parse_aware_datetime(LATER).isoformat()


# -- adopt window gates NEW_REMOTE adoption only ---------------------------


def _closed_issue(number: int = 9, **kw: object) -> Issue:
    """A CLOSED issue fixture: `state` and `closed_at` are set together.

    The adopt window keys off `state` (non-null by construction), not the
    nullable `closed_at`, so a fixture that sets only `closed_at` describes
    an issue no tracker would ever return and would silently stop exercising
    the real gate.
    """
    return _issue(number, state="closed", **kw)


def test_new_remote_closed_beyond_window_is_not_adopted() -> None:
    issue = _closed_issue(closed_at=ADOPT_NOW - timedelta(days=40))
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=ADOPT_WINDOW_DAYS, now=ADOPT_NOW)
    assert r.pulls == []
    assert r.skipped_adopts == [9]


def test_new_remote_closed_exactly_at_window_boundary_is_adopted() -> None:
    # Mirrors test_prune.py::test_exactly_threshold_days_is_kept: the rule is
    # strictly greater-than, so exactly N days ago is still adopted.
    issue = _closed_issue(closed_at=ADOPT_NOW - timedelta(days=ADOPT_WINDOW_DAYS))
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=ADOPT_WINDOW_DAYS, now=ADOPT_NOW)
    assert len(r.pulls) == 1
    assert r.pulls[0].task_id is None
    assert r.skipped_adopts == []


def test_new_remote_closed_within_window_is_adopted() -> None:
    issue = _closed_issue(closed_at=ADOPT_NOW - timedelta(days=5))
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=ADOPT_WINDOW_DAYS, now=ADOPT_NOW)
    assert len(r.pulls) == 1


def test_new_remote_open_issue_is_always_adopted_even_with_window() -> None:
    issue = _issue(9, state="open", closed_at=None)
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=ADOPT_WINDOW_DAYS, now=ADOPT_NOW)
    assert len(r.pulls) == 1


def test_adopt_closed_within_days_zero_skips_an_issue_closed_seconds_ago() -> None:
    # The new default (0): adopt open issues only. Even a closure moments
    # ago must be skipped -- there is no "grace period" at window=0.
    issue = _closed_issue(closed_at=ADOPT_NOW - timedelta(seconds=5))
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=0, now=ADOPT_NOW)
    assert r.pulls == []
    assert r.skipped_adopts == [9]


def test_closed_issue_with_no_closed_at_is_not_adopted_at_window_zero() -> None:
    """Fail-closed on the #167 hole: `state` decides, not the nullable `closed_at`.

    Both adapters read `closed_at` via `.get()` (`github.py`/`gitea.py`), so a
    tracker that reports an issue closed but omits the timestamp yields
    `state="closed", closed_at=None`. Keying the gate off `closed_at` adopted
    exactly this issue; its age is unknowable, so it cannot be proven recent.
    """
    issue = _closed_issue(closed_at=None)
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=0, now=ADOPT_NOW)
    assert r.pulls == []
    assert r.skipped_adopts == [9]


def test_closed_issue_with_no_closed_at_is_not_adopted_with_a_real_window() -> None:
    issue = _closed_issue(closed_at=None)
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=ADOPT_WINDOW_DAYS, now=ADOPT_NOW)
    assert r.pulls == []
    assert r.skipped_adopts == [9]


def test_closed_issue_with_future_closed_at_is_not_adopted() -> None:
    """Clock skew must not become an adoption. A `closed_at` ahead of `now`
    makes the age negative, which trivially satisfies any `age > window`
    test — so a naive comparison adopts it. Not provably recent -> skip."""
    issue = _closed_issue(closed_at=ADOPT_NOW + timedelta(days=1))
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=0, now=ADOPT_NOW)
    assert r.pulls == []
    assert r.skipped_adopts == [9]


def test_closed_issue_with_future_closed_at_is_not_adopted_with_a_real_window() -> None:
    issue = _closed_issue(closed_at=ADOPT_NOW + timedelta(days=1))
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=ADOPT_WINDOW_DAYS, now=ADOPT_NOW)
    assert r.pulls == []
    assert r.skipped_adopts == [9]


def test_adopt_closed_within_days_zero_still_adopts_open_issues() -> None:
    issue = _issue(9, state="open", closed_at=None)
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=0, now=ADOPT_NOW)
    assert len(r.pulls) == 1
    assert r.pulls[0].task_id is None
    assert r.skipped_adopts == []


def test_adopt_closed_within_days_none_adopts_everything() -> None:
    # Back-compat default: no window means even a long-closed issue is
    # adopted, and `now` need not be supplied at all.
    issue = _closed_issue(closed_at=ADOPT_NOW - timedelta(days=400))
    c = Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True)
    r = resolve([c])
    assert len(r.pulls) == 1
    assert r.skipped_adopts == []


def test_skipped_adopts_records_every_rejected_issue_number() -> None:
    """Skipped adoptions are recorded, never dropped — the count AND the
    identities survive so a plan can name what it left behind."""
    classifications = [
        Classification(
            ClassKind.NEW_REMOTE,
            None,
            _closed_issue(n, closed_at=ADOPT_NOW - timedelta(days=100)),
            remote_changed=True,
        )
        for n in (11, 12, 13)
    ]
    classifications.append(
        Classification(ClassKind.NEW_REMOTE, None, _issue(14), remote_changed=True)
    )
    r = resolve(classifications, adopt_closed_within_days=0, now=ADOPT_NOW)
    assert [p.issue_number for p in r.pulls] == [14]
    assert r.skipped_adopts == [11, 12, 13]


def test_changed_remote_pull_ignores_adopt_window() -> None:
    # Critical regression guard: an ALREADY-ADOPTED task (task_id set, issue
    # matched) whose issue is long-closed AND changed remotely must still
    # produce a pull — the adopt window must never touch CHANGED_REMOTE.
    issue = _closed_issue(closed_at=ADOPT_NOW - timedelta(days=400))
    task = _task(id="t-9", issue_number=9)
    c = Classification(ClassKind.CHANGED_REMOTE, task, issue, remote_changed=True)
    r = resolve([c], adopt_closed_within_days=ADOPT_WINDOW_DAYS, now=ADOPT_NOW)
    assert len(r.pulls) == 1
    assert r.pulls[0].task_id == "t-9"
    assert r.skipped_adopts == []


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
        Classification(
            ClassKind.ORPHAN_LOCAL, _task("f", issue_number=42), None, local_changed=True
        ),
    ]
    r = resolve(classifications)
    assert len(r.creates) == 1
    assert len(r.pushes) == 1
    assert len(r.pulls) == 1
    assert len(r.conflicts) == 1
    assert len(r.orphans) == 1
    assert r.orphans[0].task_id == "f"
