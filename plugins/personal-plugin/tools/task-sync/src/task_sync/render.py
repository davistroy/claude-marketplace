"""Read-only TASKS.md renderer: an aligned open-tasks table plus a status summary.

Both functions are pure: given a `TaskList` (and optional filters) they
return a string, with no I/O. Callers decide where the string goes (stdout,
a gitignored TASKS.md, etc.) — see Phase 5/6 for wiring TASKS.md into the
skill and gitignoring it.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from task_sync.models import VALID_STATUSES, Task, TaskList

_COLUMNS = ("#", "Pri", "Status", "Title", "Labels")

# Status values shown in render_open by default; "done" is hidden unless a
# filter explicitly asks for it (filters={"status": "done"}).
_DEFAULT_HIDDEN_STATUSES = ("done",)


def _issue_column(task: Task) -> str:
    return str(task.issue_number) if task.issue_number is not None else "—"


def _priority_column(task: Task) -> str:
    return task.priority if task.priority is not None else ""


def _labels_column(task: Task) -> str:
    return ", ".join(task.labels) if task.labels else ""


def _title_column(task: Task) -> str:
    title = task.title
    if task.status == "blocked":
        waiting_on = ""
        if isinstance(task.last_synced, dict):
            waiting_on = str(task.last_synced.get("blocked_on", "")) if task.last_synced else ""
        if waiting_on:
            return f"{title} (blocked on {waiting_on})"
        return f"{title} (blocked)"
    return title


def _matches_filters(task: Task, filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        actual = getattr(task, key, None)
        if actual != expected:
            return False
    return True


def _sort_key(task: Task) -> tuple[int, str, str]:
    status_rank = (
        VALID_STATUSES.index(task.status) if task.status in VALID_STATUSES else len(VALID_STATUSES)
    )
    priority = task.priority or "P9"
    return (status_rank, priority, task.id)


def _sort_field_value(task: Task, sort: str) -> str:
    value = getattr(task, sort, None)
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)


def render_open(
    tasklist: TaskList,
    filters: dict[str, Any] | None = None,
    *,
    include_done: bool = False,
    sort: str | None = None,
) -> str:
    """Render the open-tasks table.

    `done` tasks are hidden by default; pass `filters={"status": "done"}`
    (or another explicit status) to see only that status, including "done",
    or `include_done=True` to show every status without narrowing to one.
    Any other filter key/value pair is matched by exact equality against the
    corresponding `Task` attribute. `sort`, when given, is a `Task`
    attribute name to sort by (ties broken by `id`); otherwise the default
    status/priority/id ordering is used.
    """
    candidates = [task for task in tasklist.tasks if _matches_filters(task, filters)]

    hide_done = not include_done and (not filters or "status" not in filters)
    if hide_done:
        candidates = [task for task in candidates if task.status not in _DEFAULT_HIDDEN_STATUSES]

    if sort:
        candidates.sort(key=lambda task: (_sort_field_value(task, sort), task.id))
    else:
        candidates.sort(key=_sort_key)

    rows: list[tuple[str, str, str, str, str]] = [
        (
            _issue_column(task),
            _priority_column(task),
            task.status,
            _title_column(task),
            _labels_column(task),
        )
        for task in candidates
    ]

    widths = [len(col) for col in _COLUMNS]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _fmt_row(cells: tuple[str, ...]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    lines = [
        _fmt_row(_COLUMNS),
        "| " + " | ".join("-" * widths[i] for i in range(len(_COLUMNS))) + " |",
    ]
    lines.extend(_fmt_row(row) for row in rows)

    if not rows:
        lines.append("(no matching tasks)")

    lines.append("")
    lines.append(f"{len(rows)} open task{'s' if len(rows) != 1 else ''}")

    return "\n".join(lines)


def render_summary(tasklist: TaskList) -> str:
    """Render a one-section status summary: counts by status, total, and open count."""
    counts = Counter(task.status for task in tasklist.tasks)
    total = len(tasklist.tasks)
    open_count = sum(count for status, count in counts.items() if status != "done")

    lines = ["Status summary:"]
    for status in VALID_STATUSES:
        lines.append(f"  {status}: {counts.get(status, 0)}")

    unknown_statuses = sorted(set(counts) - set(VALID_STATUSES))
    for status in unknown_statuses:
        lines.append(f"  {status}: {counts[status]}")

    lines.append(f"  total: {total}")
    lines.append(f"  open: {open_count}")

    return "\n".join(lines)
