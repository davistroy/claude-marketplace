"""Three-way classifier: task vs. issue vs. the committed ``last_synced`` base.

This is the correctness core of the sync. For every task and every issue we
decide, relative to the *base* recorded at the previous sync, whether the
local side changed, the remote side changed, both, or neither — and whether
a task/issue is brand new on one side. Every downstream decision (push,
pull, conflict, prune) is derived from these classifications, so the rules
here are deliberately conservative: when the base is missing or ambiguous we
treat a side as *changed* rather than assume it is safe to clobber.

The ``last_synced`` base is a small dict on each linked task::

    {"hash": "<content hash of the task at last sync>",
     "at":   "<issue.updated_at ISO-8601 at last sync>"}

"Changed since base" is decidable on each side independently:

* local  — ``content_hash(task) != last_synced["hash"]``
* remote — ``issue.updated_at > parse(last_synced["at"])``

Tasks are matched to issues on ``issue_number``. A task with no
``issue_number`` has never been pushed (``NEW_LOCAL``); an issue whose number
is referenced by no task has never been adopted (``NEW_REMOTE``).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from task_sync.models import Task, TaskList
from task_sync.providers.base import Issue, parse_aware_datetime


class ClassKind(str, Enum):
    """The seven mutually exclusive outcomes of a three-way comparison."""

    NEW_LOCAL = "new_local"
    NEW_REMOTE = "new_remote"
    CHANGED_LOCAL = "changed_local"
    CHANGED_REMOTE = "changed_remote"
    CHANGED_BOTH = "changed_both"
    UNCHANGED = "unchanged"
    ORPHAN_LOCAL = "orphan_local"


# Fields that participate in the content hash. These are exactly the fields
# that round-trip through the tracker (see mapping.py) — identifiers,
# timestamps, and the sync bookkeeping itself are excluded so that recording
# a new base never, by itself, looks like a content change on the next run.
_HASHED_FIELDS = ("title", "body", "status", "priority", "labels", "milestone")


def content_hash(task: Task) -> str:
    """Return a stable SHA-256 over the task's *syncable* content.

    Labels are sorted so that a pure reordering is not treated as a change.
    The digest is deterministic across processes and Python versions, which
    is what makes ``last_synced["hash"]`` a durable, git-committable base.
    """
    payload: dict[str, Any] = {
        "title": task.title,
        "body": task.body,
        "status": task.status,
        "priority": task.priority,
        "labels": sorted(task.labels),
        "milestone": task.milestone,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass
class Classification:
    """One task/issue pairing and its three-way verdict.

    * ``NEW_LOCAL`` — ``task`` set, ``issue`` None.
    * ``NEW_REMOTE`` — ``task`` None, ``issue`` set.
    * ``ORPHAN_LOCAL`` — a task whose issue has vanished from the fetched
      tracker list: ``task`` set, ``issue`` None. Its own kind, never
      ``CHANGED_LOCAL``/``UNCHANGED`` — see :func:`classify`.
    * everything else — both ``task`` and ``issue`` set.

    ``local_changed`` / ``remote_changed`` are the raw per-side signals the
    verdict was derived from; resolution uses them, and they make the reason
    for a ``CHANGED_BOTH`` conflict inspectable.
    """

    kind: ClassKind
    task: Task | None
    issue: Issue | None
    local_changed: bool = False
    remote_changed: bool = False


def _local_changed(task: Task) -> bool:
    """True if the task's content differs from its recorded base hash.

    A missing/empty base hash means we have no trustworthy record of what was
    last synced, so we conservatively report *changed* — the reconcile will
    then re-push or surface a conflict rather than silently assume "clean".
    """
    base_hash = task.last_synced.get("hash") if isinstance(task.last_synced, dict) else None
    if not base_hash:
        return True
    return content_hash(task) != str(base_hash)


def _remote_changed(task: Task, issue: Issue) -> bool:
    """True if the issue was updated after the recorded base timestamp.

    A missing/unparseable base timestamp is treated as *changed* for the same
    conservative reason as ``_local_changed``.
    """
    base_at_raw = task.last_synced.get("at") if isinstance(task.last_synced, dict) else None
    base_at = parse_aware_datetime(base_at_raw if isinstance(base_at_raw, str) else None)
    if base_at is None:
        return True
    return issue.updated_at > base_at


def classify(tasklist: TaskList, issues: list[Issue]) -> list[Classification]:
    """Classify every task and every unmatched issue against the base.

    Returns one ``Classification`` per task (in task order) followed by one
    per issue that no task references (``NEW_REMOTE``, in issue order). The
    result is exhaustive and non-overlapping: each task and each issue
    appears exactly once.
    """
    issues_by_number: dict[int, Issue] = {issue.number: issue for issue in issues}
    matched_numbers: set[int] = set()
    results: list[Classification] = []

    for task in tasklist.tasks:
        if task.issue_number is None:
            # Never pushed — a purely local task awaiting creation.
            results.append(Classification(ClassKind.NEW_LOCAL, task, None))
            continue

        issue = issues_by_number.get(task.issue_number)
        if issue is None:
            # The task points at an issue the tracker no longer returns.
            # This is NOT proof the issue was deleted -- the fetched list can
            # be incomplete (pagination/saturation, #182) -- so it must never
            # be classified as CHANGED_LOCAL or UNCHANGED: `resolve` maps
            # CHANGED_LOCAL to a PushAction (a silent clobber of a merely-
            # unfetched issue, which can even reopen one that is actually
            # closed) and UNCHANGED to nothing at all (silently dropped, and
            # unfiled in every plan section). ORPHAN_LOCAL is its own kind
            # precisely so neither can happen; `local_changed` still records
            # which sub-case this is, for surfacing only. classify() does not
            # mutate `task` -- `task.issue_number` is left as-is.
            local = _local_changed(task)
            results.append(Classification(ClassKind.ORPHAN_LOCAL, task, None, local_changed=local))
            continue

        matched_numbers.add(issue.number)
        local = _local_changed(task)
        remote = _remote_changed(task, issue)

        if local and remote:
            kind = ClassKind.CHANGED_BOTH
        elif local:
            kind = ClassKind.CHANGED_LOCAL
        elif remote:
            kind = ClassKind.CHANGED_REMOTE
        else:
            kind = ClassKind.UNCHANGED

        results.append(
            Classification(kind, task, issue, local_changed=local, remote_changed=remote)
        )

    for issue in issues:
        if issue.number not in matched_numbers:
            # An issue no local task has adopted yet.
            results.append(Classification(ClassKind.NEW_REMOTE, None, issue, remote_changed=True))

    return results
