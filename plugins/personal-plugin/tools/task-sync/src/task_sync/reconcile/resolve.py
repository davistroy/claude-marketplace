"""Turn classifications into concrete, one-directional actions + conflicts.

The rule is simple and safety-first: a change on exactly one side is applied
to the other side; a change on *both* sides is never auto-clobbered — it
becomes a :class:`Conflict` carrying both sides' values plus a *recommended*
resolution (last-write-wins by timestamp) for a human to accept or override.

Directionality:

* ``NEW_LOCAL``      -> a :class:`CreateAction`   (create the issue)
* ``CHANGED_LOCAL``  -> a :class:`PushAction`     (update the issue)
* ``NEW_REMOTE``     -> a :class:`PullAction`     (adopt: create the task)
* ``CHANGED_REMOTE`` -> a :class:`PullAction`     (update the task)
* ``CHANGED_BOTH``   -> a :class:`Conflict`       (surfaced, never applied)
* ``UNCHANGED``      -> nothing

A remotely-closed issue needs no special case: its pull carries
``status="done"`` straight out of :func:`issue_to_task_fields`, so adopting
or updating from a closed issue lands the task in ``done`` automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from task_sync.providers.base import Issue, parse_aware_datetime
from task_sync.reconcile.classify import Classification, ClassKind
from task_sync.reconcile.mapping import issue_to_task_fields, task_to_issue_fields


@dataclass
class CreateAction:
    """Create a brand-new tracker issue from a purely local task."""

    task_id: str
    fields: dict  # task_to_issue_fields(task)


@dataclass
class PushAction:
    """Update an existing issue to match a locally-changed task."""

    task_id: str
    issue_number: int
    fields: dict  # task_to_issue_fields(task)


@dataclass
class PullAction:
    """Update a local task from an issue, or adopt a new one.

    ``task_id is None`` means *adopt* — create a new task from the issue.
    Otherwise the named existing task is updated in place.

    ``issue_updated_at`` / ``issue_closed_at`` are carried on the action so
    that apply can refresh the ``last_synced`` base and the task's
    ``closed_at`` without a second round-trip to the tracker — a pull needs
    no further provider call, the remote data is already in hand.
    """

    issue_number: int
    task_id: str | None
    fields: dict  # issue_to_task_fields(issue)
    issue_updated_at: str = ""
    issue_closed_at: str | None = None


@dataclass
class Conflict:
    """Both sides changed since the base — a human must choose.

    ``local`` and ``remote`` hold each side's would-be projection so a UI can
    diff them directly. ``recommendation`` is last-write-wins ("local" or
    "remote") but is only advice: nothing is applied until a decision selects
    a side.
    """

    task_id: str
    issue_number: int
    local: dict  # task_to_issue_fields(task)
    remote: dict  # issue_to_task_fields(issue)
    recommendation: str  # "local" | "remote"
    local_updated_at: str | None
    remote_updated_at: str
    remote_closed_at: str | None = None


@dataclass
class ResolveResult:
    """The fully-split set of actions produced from a classification list.

    ``skipped_adopts`` holds the issue *numbers* of every NEW_REMOTE issue
    the adopt window rejected — not just a count. The numbers are what makes
    the outcome actionable ("#12, #14 and 18 more were left unadopted"); a
    bare count is recoverable from them via ``len()``, the reverse is not.
    """

    creates: list[CreateAction] = field(default_factory=list)
    pushes: list[PushAction] = field(default_factory=list)
    pulls: list[PullAction] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    skipped_adopts: list[int] = field(default_factory=list)


def _recommend(local_updated_at: str | None, remote_updated_at: str) -> str:
    """Last-write-wins: recommend the side with the newer ``updated_at``.

    A missing/unparseable local timestamp cannot out-rank a real remote one,
    so it defers to remote. Ties also defer to remote (the tracker is the
    shared source of record), keeping the tie-break deterministic.
    """
    local_dt = parse_aware_datetime(local_updated_at)
    remote_dt = parse_aware_datetime(remote_updated_at)
    if local_dt is not None and remote_dt is not None and local_dt > remote_dt:
        return "local"
    return "remote"


def _should_skip_adopt(issue: Issue, now: datetime, window_days: int) -> bool:
    """True when a NEW_REMOTE issue is past the adopt window and must not be adopted.

    The window answers "is this issue recent enough to be worth adopting at
    all" — a different question from prune's "how long do we keep completed
    work", and driven by its own ``adopt_closed_within_days`` config key,
    never by the prune threshold.

    The gate keys off ``issue.state``, not ``closed_at``. ``state`` is
    validated to ``("open", "closed")`` in :class:`Issue`, so it is non-null
    by construction; ``closed_at`` is populated from an optional provider
    field (``.get("closedAt")`` / ``.get("closed_at")``) and can legitimately
    be ``None`` on an issue the tracker reports as closed. Keying off the
    nullable field let exactly that issue slip through and be adopted — the
    regression this window exists to prevent (#167).

    The rule is therefore fail-closed: a closed issue is adopted only when
    its age is *provably* inside the window. Anything unprovable — a missing
    ``closed_at``, or a ``closed_at`` in the future from clock skew between
    the tracker and this machine — is skipped rather than adopted.

    Boundary convention is unchanged and mirrors prune's: the comparison is
    strictly greater-than, so exactly N days ago is still inside the window,
    and the same comparison composes correctly at ``window_days=0`` (adopt
    open issues only — even a closure moments ago is outside a zero window).
    """
    if issue.state != "closed":
        return False
    if issue.closed_at is None:
        # Closed, but the tracker gave us no closure timestamp: its age is
        # unknowable, so it cannot be proven recent. Skip.
        return True
    age = now - issue.closed_at
    if age < timedelta(0):
        # closed_at is in the future (clock skew). Not provably recent. Skip.
        return True
    return age > timedelta(days=window_days)


def resolve(
    classifications: list[Classification],
    *,
    adopt_closed_within_days: int | None = None,
    now: datetime | None = None,
) -> ResolveResult:
    """Split classifications into creates / pushes / pulls / conflicts.

    ``adopt_closed_within_days`` gates NEW_REMOTE adoption only: an issue
    closed more than that many days ago is left unadopted (no
    :class:`PullAction` is emitted for it). This answers "is this issue
    recent enough to be worth adopting at all", a distinct question from
    how long an already-tracked ``done`` task is kept locally (that is
    prune's ``prune_closed_after_days``, a separate config key read by
    ``reconcile.apply``/``commands``, never by this function). The default
    ``None`` adopts every NEW_REMOTE issue regardless of how long ago it
    closed — today's behavior, so every existing call site stays correct
    unchanged. (The CLI's own default, sourced from its
    ``adopt_closed_within_days`` config key, is ``0`` — adopt open issues
    only — but that policy choice lives in the caller, not here.) An open
    issue (``state == "open"``) is always adopted, window or not; a closed
    one is adopted only when its closure is provably inside the window (see
    :func:`_should_skip_adopt`).

    Issues skipped by the window are recorded on
    :attr:`ResolveResult.skipped_adopts` rather than dropped silently, so a
    plan can say "0 pulls *because* N issues were outside the window"
    instead of reporting itself as already in sync.

    This window applies to NEW_REMOTE only. CHANGED_REMOTE (an
    already-adopted task whose issue changed) is completely unaffected —
    an adopted task always keeps full remote fidelity, including a closed
    state, no matter how long ago that closure happened.

    ``now`` is only consulted — and only defaulted to the current time —
    when ``adopt_closed_within_days`` is not None; with no window in
    effect ``resolve`` remains a pure function of ``classifications`` alone.
    """
    result = ResolveResult()

    effective_now: datetime | None = now
    if adopt_closed_within_days is not None and effective_now is None:
        effective_now = datetime.now(timezone.utc)

    for c in classifications:
        if c.kind is ClassKind.NEW_LOCAL:
            assert c.task is not None
            result.creates.append(
                CreateAction(task_id=c.task.id, fields=task_to_issue_fields(c.task))
            )

        elif c.kind is ClassKind.CHANGED_LOCAL:
            assert c.task is not None
            if c.task.issue_number is None:
                # An orphan (issue vanished) that changed locally: there is
                # no live issue to push to, so re-create it instead.
                result.creates.append(
                    CreateAction(task_id=c.task.id, fields=task_to_issue_fields(c.task))
                )
            else:
                result.pushes.append(
                    PushAction(
                        task_id=c.task.id,
                        issue_number=c.task.issue_number,
                        fields=task_to_issue_fields(c.task),
                    )
                )

        elif c.kind is ClassKind.NEW_REMOTE:
            assert c.issue is not None
            if adopt_closed_within_days is not None:
                assert effective_now is not None
                if _should_skip_adopt(c.issue, effective_now, adopt_closed_within_days):
                    # Record, never drop: a silently-skipped adoption makes an
                    # otherwise-empty plan claim "already in sync" while N
                    # issues sit unmirrored.
                    result.skipped_adopts.append(c.issue.number)
                    continue
            result.pulls.append(
                PullAction(
                    issue_number=c.issue.number,
                    task_id=None,
                    fields=issue_to_task_fields(c.issue),
                    issue_updated_at=c.issue.updated_at.isoformat(),
                    issue_closed_at=(c.issue.closed_at.isoformat() if c.issue.closed_at else None),
                )
            )

        elif c.kind is ClassKind.CHANGED_REMOTE:
            assert c.task is not None and c.issue is not None
            result.pulls.append(
                PullAction(
                    issue_number=c.issue.number,
                    task_id=c.task.id,
                    fields=issue_to_task_fields(c.issue),
                    issue_updated_at=c.issue.updated_at.isoformat(),
                    issue_closed_at=(c.issue.closed_at.isoformat() if c.issue.closed_at else None),
                )
            )

        elif c.kind is ClassKind.CHANGED_BOTH:
            assert c.task is not None and c.issue is not None
            remote_updated = c.issue.updated_at.isoformat()
            result.conflicts.append(
                Conflict(
                    task_id=c.task.id,
                    issue_number=c.issue.number,
                    local=task_to_issue_fields(c.task),
                    remote=issue_to_task_fields(c.issue),
                    recommendation=_recommend(c.task.updated_at, remote_updated),
                    local_updated_at=c.task.updated_at,
                    remote_updated_at=remote_updated,
                    remote_closed_at=(c.issue.closed_at.isoformat() if c.issue.closed_at else None),
                )
            )

        # ClassKind.UNCHANGED -> intentionally nothing.

    return result
