"""Execute a :class:`SyncPlan` against a Provider and return a new TaskList.

Apply is the only mutating half of the plan/apply split. It:

1. works on a *copy* of the incoming ``TaskList`` (the original is never
   touched — that is what lets ``--dry-run`` provably write nothing);
2. runs creates/pushes/pulls through the ``Provider``, ensuring any
   referenced labels/milestones exist first;
3. applies human ``decisions`` to each conflict — ``"local"`` pushes, and
   ``"remote"`` pulls; an undecided conflict is left untouched (never
   clobbered) so it resurfaces next run;
4. applies human ``orphan_decisions`` to each orphan — ``"keep"`` retains
   the task with its link cleared so the next run re-creates via the
   tested creates path, and ``"drop"`` removes the task; an undecided
   orphan is left untouched so it resurfaces next run;
5. refreshes each affected task's ``last_synced`` base to the post-sync
   content hash + the issue's ``updated_at``; and
6. prunes ``done`` tasks whose issue closed more than ``N`` days ago (``N``
   from ``config['prune_closed_after_days']``, default 30), leaving the
   closed issue on the tracker as the archived record.

The returned ``TaskList`` is for the caller to persist; apply itself writes
no files.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from task_sync.models import Task, TaskList, new_id
from task_sync.providers.base import Issue, Provider, parse_aware_datetime
from task_sync.reconcile.classify import content_hash
from task_sync.reconcile.plan import SyncPlan
from task_sync.reconcile.resolve import Conflict

# Orphan dispositions: valid values for human decisions on orphaned tasks.
ORPHAN_DISPOSITION_KEEP = "keep"
ORPHAN_DISPOSITION_DROP = "drop"
ORPHAN_DISPOSITIONS = (ORPHAN_DISPOSITION_KEEP, ORPHAN_DISPOSITION_DROP)

DEFAULT_PRUNE_DAYS = 30


def _copy_tasklist(tasklist: TaskList) -> TaskList:
    """A deep-enough copy: round-trip through dicts so callers' data is safe."""
    return TaskList.from_dict(tasklist.to_dict())


def _ensure_remote_metadata(provider: Provider, fields: dict[str, Any]) -> None:
    """Create any labels/milestone the push/create references, before it runs."""
    labels = list(fields.get("labels") or [])
    if labels:
        provider.ensure_labels(labels)
    milestone = fields.get("milestone")
    if milestone:
        provider.ensure_milestone(milestone)


def _set_task_content(task: Task, fields: dict[str, Any]) -> None:
    """Overwrite a task's syncable content from an ``issue_to_task_fields`` dict."""
    task.title = fields["title"]
    task.body = fields["body"]
    task.status = fields["status"]
    task.priority = fields["priority"]
    task.labels = list(fields["labels"])
    task.milestone = fields["milestone"]


def _refresh_base(task: Task, updated_at_iso: str) -> None:
    """Rebase ``last_synced`` to the current content + the issue's timestamp.

    Other keys already in ``last_synced`` (e.g. ``blocked_on``) are preserved.
    """
    base = dict(task.last_synced)
    base["hash"] = content_hash(task)
    base["at"] = updated_at_iso
    task.last_synced = base


def _apply_from_issue(task: Task, issue: Issue) -> None:
    """After a create/push, sync the task's remote-derived fields from the return."""
    task.issue_number = issue.number
    task.closed_at = issue.closed_at.isoformat() if issue.closed_at else None
    _refresh_base(task, issue.updated_at.isoformat())


def _do_push(provider: Provider, task: Task, number: int, fields: dict[str, Any]) -> None:
    """Update an existing issue from a task and rebase the task."""
    _ensure_remote_metadata(provider, fields)
    issue = provider.update_issue(
        number,
        title=fields["title"],
        body=fields["body"],
        labels=fields["labels"],
        milestone=fields["milestone"],
        state=fields["state"],
    )
    _apply_from_issue(task, issue)


def _do_pull(
    task: Task,
    fields: dict[str, Any],
    issue_number: int,
    issue_updated_at: str,
    issue_closed_at: str | None,
) -> None:
    """Update an existing task from remote data already in the plan."""
    _set_task_content(task, fields)
    task.issue_number = issue_number
    task.updated_at = issue_updated_at
    task.closed_at = issue_closed_at
    _refresh_base(task, issue_updated_at)


def _adopt(
    fields: dict[str, Any],
    issue_number: int,
    issue_updated_at: str,
    issue_closed_at: str | None,
) -> Task:
    """Create a brand-new local task from a remote issue (NEW_REMOTE)."""
    task = Task(
        id=new_id(),
        title=fields["title"],
        body=fields["body"],
        status=fields["status"],
        priority=fields["priority"],
        labels=list(fields["labels"]),
        milestone=fields["milestone"],
        issue_number=issue_number,
        created_at=issue_updated_at,
        updated_at=issue_updated_at,
        closed_at=issue_closed_at,
    )
    _refresh_base(task, issue_updated_at)
    return task


def _prune_days(tasklist: TaskList) -> int:
    """Read the prune threshold (days) from config, defaulting to 30."""
    raw = tasklist.config.get("prune_closed_after_days", DEFAULT_PRUNE_DAYS)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return DEFAULT_PRUNE_DAYS


def _should_prune(task: Task, now: datetime, threshold_days: int) -> bool:
    """True for a ``done`` task whose issue closed more than N days ago."""
    if task.status != "done":
        return False
    closed = parse_aware_datetime(task.closed_at)
    if closed is None:
        return False
    return now - closed > timedelta(days=threshold_days)


def _validate_orphan_decisions(
    plan: SyncPlan, orphan_decisions: dict[str, str]
) -> None:
    """Validate all orphan decision ids and dispositions upfront (D36).

    Raises ``ValueError`` naming the offending id or disposition if any
    decision is for an unknown orphan or carries an invalid disposition.
    No mutations occur if validation fails.
    """
    orphan_ids = {o.task_id for o in plan.orphans}
    for task_id, disposition in orphan_decisions.items():
        if task_id not in orphan_ids:
            raise ValueError(
                f"orphan decision for unknown task {task_id!r} "
                f"(known: {', '.join(sorted(orphan_ids)) or 'none'})"
            )
        if disposition not in ORPHAN_DISPOSITIONS:
            raise ValueError(
                f"invalid orphan disposition {disposition!r} for task {task_id} "
                f"(must be one of: {', '.join(ORPHAN_DISPOSITIONS)})"
            )


def _apply_orphan_decision(
    orphan_task: Task, decision: str | None
) -> bool:
    """Apply an orphan decision and return True if the task was removed.

    ``keep`` clears issue_number and last_synced so the next run re-creates
    via the tested creates path. ``drop`` returns True so the caller removes
    the task. Undecided orphans are left untouched and return False.
    """
    if decision == ORPHAN_DISPOSITION_KEEP:
        # Clear the link so next run treats it as NEW_LOCAL and re-creates.
        orphan_task.issue_number = None
        orphan_task.last_synced = {}
        return False
    if decision == ORPHAN_DISPOSITION_DROP:
        # Drop the task entirely — return True to signal removal.
        return True
    # Any other value (None) -> leave the orphan unresolved.
    return False


def apply(
    plan: SyncPlan,
    decisions: dict[str, str],
    tasklist: TaskList,
    provider: Provider,
    *,
    orphan_decisions: dict[str, str] | None = None,
    now: datetime | None = None,
) -> TaskList:
    """Execute ``plan`` against ``provider`` and return the updated TaskList.

    ``decisions`` maps a conflict's ``task_id`` to ``"local"`` or ``"remote"``.
    Any conflict without such a decision is left exactly as it is.

    ``orphan_decisions`` maps an orphan's ``task_id`` to ``"keep"`` or ``"drop"``.
    Any orphan without a decision is left untouched. All ids and dispositions
    are validated upfront (D36) — if validation fails, no mutations occur.

    ``now`` (UTC-aware) is injectable for deterministic prune tests; it
    defaults to the current time.
    """
    now = now or datetime.now(timezone.utc)
    orphan_decisions = orphan_decisions or {}

    # Validate orphan decisions upfront (D36).
    _validate_orphan_decisions(plan, orphan_decisions)

    result = _copy_tasklist(tasklist)
    by_id: dict[str, Task] = {task.id: task for task in result.tasks}

    # 1. Creates: purely-local tasks -> new remote issues.
    for create in plan.creates:
        task = by_id[create.task_id]
        _ensure_remote_metadata(provider, create.fields)
        issue = provider.create_issue(
            title=create.fields["title"],
            body=create.fields["body"],
            labels=create.fields["labels"],
            milestone=create.fields["milestone"],
        )
        _apply_from_issue(task, issue)

    # 2. Pushes: locally-changed tasks -> existing issues.
    for push in plan.pushes:
        _do_push(provider, by_id[push.task_id], push.issue_number, push.fields)

    # 3. Pulls: remote -> local (adopt new tasks or update existing ones).
    adopted: list[Task] = []
    for pull in plan.pulls:
        if pull.task_id is None:
            adopted.append(
                _adopt(pull.fields, pull.issue_number, pull.issue_updated_at, pull.issue_closed_at)
            )
        else:
            _do_pull(
                by_id[pull.task_id],
                pull.fields,
                pull.issue_number,
                pull.issue_updated_at,
                pull.issue_closed_at,
            )

    # 4. Conflicts: apply only where a human decision selected a side.
    for conflict in plan.conflicts:
        _apply_conflict_decision(conflict, decisions.get(conflict.task_id), by_id, provider)

    result.tasks.extend(adopted)

    # 5. Orphans: apply only where a human decision selected a disposition.
    # Must run AFTER creates/pushes so by_id lookups don't assume dropped tasks survive.
    tasks_to_drop = set()
    for orphan in plan.orphans:
        task = by_id[orphan.task_id]
        if _apply_orphan_decision(task, orphan_decisions.get(orphan.task_id)):
            tasks_to_drop.add(orphan.task_id)
    result.tasks = [t for t in result.tasks if t.id not in tasks_to_drop]

    # 6. Prune stale done+closed tasks, leaving their issues closed.
    threshold = _prune_days(result)
    result.tasks = [t for t in result.tasks if not _should_prune(t, now, threshold)]

    result.last_sync_at = now.isoformat()
    return result


def _apply_conflict_decision(
    conflict: Conflict,
    decision: str | None,
    by_id: dict[str, Task],
    provider: Provider,
) -> None:
    """Resolve one conflict per the human decision; undecided ones are skipped."""
    task = by_id[conflict.task_id]
    if decision == "local":
        # Reconstruct the local-wins push from the conflict's stored projection.
        _do_push(provider, task, conflict.issue_number, conflict.local)
    elif decision == "remote":
        _do_pull(
            task,
            conflict.remote,
            conflict.issue_number,
            conflict.remote_updated_at,
            conflict.remote_closed_at,
        )
    # Any other value (or None) -> leave the conflict unresolved. Never clobber.
