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

from task_sync.providers.base import parse_aware_datetime
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
    """The fully-split set of actions produced from a classification list."""

    creates: list[CreateAction] = field(default_factory=list)
    pushes: list[PushAction] = field(default_factory=list)
    pulls: list[PullAction] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)


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


def resolve(classifications: list[Classification]) -> ResolveResult:
    """Split classifications into creates / pushes / pulls / conflicts."""
    result = ResolveResult()

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
