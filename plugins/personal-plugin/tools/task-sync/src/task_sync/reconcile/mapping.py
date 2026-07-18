"""Field mapping between the local ``Task`` model and a tracker ``Issue``.

The tool's five statuses collapse onto an issue's two-state world
(``open``/``closed``) plus a single ``status/*`` label, priority onto a
``priority/*`` label, and milestone straight across. The two functions here
are exact inverses on the managed fields so a value that has not otherwise
changed survives a full round-trip unchanged:

    Status        Issue state   status/* label
    -----------   -----------   -------------------
    backlog       open          status/backlog
    todo          open          (none)
    in-progress   open          status/in-progress
    blocked       open          status/blocked
    done          closed        (none)

``todo`` and ``done`` deliberately carry *no* ``status/*`` label: ``todo`` is
"open with nothing else said", and a closed issue already encodes ``done``.
Exactly one ``status/*`` label is ever emitted, and the reverse mapping
strips every ``status/*`` / ``priority/*`` label back out so the round-trip
does not accumulate duplicates.

Creating the labels/milestones this mapping references on the tracker is
*not* done here — that is deferred to apply-time via ``Provider.ensure_*``.
This module is pure data transformation with no I/O.
"""

from __future__ import annotations

from typing import Any

from task_sync.models import VALID_PRIORITIES, Task
from task_sync.providers.base import Issue

STATUS_LABEL_PREFIX = "status/"
PRIORITY_LABEL_PREFIX = "priority/"

# status -> the status/* label suffix, or None when the status carries no
# label. Kept as the single source of truth for both directions.
_STATUS_TO_LABEL: dict[str, str | None] = {
    "backlog": "backlog",
    "todo": None,
    "in-progress": "in-progress",
    "blocked": "blocked",
    "done": None,
}

# Reverse map for *open* issues: label suffix -> status. ``done`` is never
# reached this way (it comes from the closed state), and ``todo`` is the
# default when an open issue has no recognized status/* label.
_LABEL_TO_STATUS: dict[str, str] = {
    "backlog": "backlog",
    "in-progress": "in-progress",
    "blocked": "blocked",
}


def is_managed_label(label: str) -> bool:
    """True for labels this tool owns (``status/*`` or ``priority/*``)."""
    return label.startswith(STATUS_LABEL_PREFIX) or label.startswith(PRIORITY_LABEL_PREFIX)


def user_labels(labels: list[str]) -> list[str]:
    """Return only the caller-owned labels, dropping every managed one."""
    return [label for label in labels if not is_managed_label(label)]


def managed_labels_for(task: Task) -> list[str]:
    """The ``status/*`` + ``priority/*`` labels this task should carry.

    Useful at apply-time to feed ``Provider.ensure_labels`` before a push.
    """
    result: list[str] = []
    suffix = _STATUS_TO_LABEL[task.status]
    if suffix is not None:
        result.append(f"{STATUS_LABEL_PREFIX}{suffix}")
    if task.priority is not None:
        result.append(f"{PRIORITY_LABEL_PREFIX}{task.priority}")
    return result


def task_to_issue_fields(task: Task) -> dict[str, Any]:
    """Project a task onto the issue fields a create/update needs.

    The label set is the task's *user* labels (managed labels stripped to
    avoid duplication) followed by the freshly computed ``status/*`` then
    ``priority/*`` labels — at most one of each.
    """
    labels = user_labels(task.labels) + managed_labels_for(task)
    return {
        "title": task.title,
        "body": task.body,
        "state": "closed" if task.status == "done" else "open",
        "labels": labels,
        "milestone": task.milestone,
    }


def _status_from_issue(issue: Issue) -> str:
    """Derive the local status from an issue's state + ``status/*`` label."""
    if issue.state == "closed":
        return "done"
    for label in issue.labels:
        if label.startswith(STATUS_LABEL_PREFIX):
            suffix = label[len(STATUS_LABEL_PREFIX) :]
            if suffix in _LABEL_TO_STATUS:
                return _LABEL_TO_STATUS[suffix]
    # Open with no recognized status/* label -> the default working state.
    return "todo"


def _priority_from_issue(issue: Issue) -> str | None:
    """Derive priority from a ``priority/*`` label, or None if absent."""
    for label in issue.labels:
        if label.startswith(PRIORITY_LABEL_PREFIX):
            suffix = label[len(PRIORITY_LABEL_PREFIX) :]
            if suffix in VALID_PRIORITIES:
                return suffix
    return None


def issue_to_task_fields(issue: Issue) -> dict[str, Any]:
    """Project an issue onto the task fields a pull/adopt needs.

    Inverse of :func:`task_to_issue_fields` on the managed fields: state +
    ``status/*`` -> status, ``priority/*`` -> priority, managed labels
    stripped back out of the user label set.
    """
    return {
        "title": issue.title,
        "body": issue.body,
        "status": _status_from_issue(issue),
        "priority": _priority_from_issue(issue),
        "labels": user_labels(issue.labels),
        "milestone": issue.milestone,
    }
