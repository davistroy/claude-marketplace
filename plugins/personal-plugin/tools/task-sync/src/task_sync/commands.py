"""Deterministic store operations backing every non-``sync`` subcommand.

Each function here operates on a loaded `TaskList` (plus the path it came
from), performing pure validation/mutation via the existing `models`/`store`
primitives. Every *mutating* command follows the same shape: mutate a copy
or entry in `tasklist.tasks`, then `store.save` canonically and regenerate
`TASKS.md` next to `tasks.json` — so the two are never allowed to drift.

Kept separate from `__main__.py` so the CLI wiring there stays a thin
argparse-to-function shim, and so these operations are directly unit
testable without going through `subprocess`/`sys.argv`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from task_sync import store
from task_sync.detect import detect_gitea_base_url, detect_provider
from task_sync.models import Task, TaskList, new_id
from task_sync.providers.base import parse_aware_datetime
from task_sync.render import render_open, render_summary

TASKS_MD_NAME = "TASKS.md"

DEFAULT_PRUNE_DAYS = 30


class TaskNotFoundError(ValueError):
    """Raised when an `<id|#>` reference does not match any task."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def tasks_md_path(tasks_path: str | Path) -> Path:
    """The `TASKS.md` path that sits beside a given `tasks.json` path."""
    return Path(tasks_path).parent / TASKS_MD_NAME


def regenerate_tasks_md(tasklist: TaskList, tasks_path: str | Path) -> None:
    """(Re)write `TASKS.md` beside `tasks_path` from the current tasklist."""
    content = render_open(tasklist) + "\n"
    tasks_md_path(tasks_path).write_text(content, encoding="utf-8")


def save_and_regenerate(tasklist: TaskList, tasks_path: str | Path) -> None:
    """Canonically save `tasklist` and regenerate `TASKS.md` in lockstep."""
    store.save(tasklist, tasks_path)
    regenerate_tasks_md(tasklist, tasks_path)


def find_task(tasklist: TaskList, ref: str) -> Task | None:
    """Match `ref` against a task's `id`, or (if numeric) its `issue_number`.

    `ref` may be a bare task id (``t-abc123``) or an issue-number reference,
    optionally `#`-prefixed (``42`` or ``#42``). Returns `None` when nothing
    matches; callers that require a hit should raise `TaskNotFoundError`.
    """
    for task in tasklist.tasks:
        if task.id == ref:
            return task

    numeric = ref[1:] if ref.startswith("#") else ref
    if numeric.isdigit():
        number = int(numeric)
        for task in tasklist.tasks:
            if task.issue_number == number:
                return task

    return None


def require_task(tasklist: TaskList, ref: str) -> Task:
    """`find_task`, raising `TaskNotFoundError` on a miss."""
    task = find_task(tasklist, ref)
    if task is None:
        raise TaskNotFoundError(f"no task matching {ref!r}")
    return task


def parse_labels(value: str | None) -> list[str] | None:
    """Split a comma-separated `--labels` value into a clean list.

    Returns `None` for `None` input (meaning "field not supplied", distinct
    from an explicit empty list) so callers can tell "leave labels alone"
    apart from "clear the labels".
    """
    if value is None:
        return None
    return [label.strip() for label in value.split(",") if label.strip()]


# -- init ------------------------------------------------------------------


def cmd_init(tasks_path: str | Path, repo_root: str | Path = ".") -> str:
    """Create `tasks.json` if absent; no-op (but still refresh TASKS.md) if present.

    Returns the message to print. The provider/repo are auto-detected from
    the `origin` git remote at `repo_root`. For a `gitea` provider with an
    http(s) `origin` (not ssh — see `detect_gitea_base_url`), `config.gitea_url`
    is also populated so the very first `sync` has a base URL to call without
    needing `$GITEA_URL` or a `tea login` first. GitHub needs no analogous
    field (the `gh` CLI carries its own auth).
    """
    path = Path(tasks_path)

    if path.exists():
        tasklist = store.load(path)
        regenerate_tasks_md(tasklist, path)
        return f"task-sync init: {path} already exists — no-op"

    provider, repo = detect_provider(repo_root)
    config: dict[str, Any] = {
        "prune_closed_after_days": DEFAULT_PRUNE_DAYS,
        "sensitive_terms": [],
    }
    if provider == "gitea":
        gitea_url = detect_gitea_base_url(repo_root)
        if gitea_url:
            config["gitea_url"] = gitea_url
    tasklist = TaskList(
        provider=provider,
        repo=repo,
        last_sync_at=None,
        config=config,
        tasks=[],
    )
    save_and_regenerate(tasklist, path)
    return f"task-sync init: created {path} (provider={provider}, repo={repo or '—'})"


# -- list --------------------------------------------------------------


def cmd_list(
    tasklist: TaskList,
    *,
    status: str | None = None,
    priority: str | None = None,
    milestone: str | None = None,
    sort: str | None = None,
    show_all: bool = False,
) -> str:
    """Render the open-tasks table with the requested filters/sort applied."""
    filters: dict[str, Any] = {}
    if status is not None:
        filters["status"] = status
    if priority is not None:
        filters["priority"] = priority
    if milestone is not None:
        filters["milestone"] = milestone

    return render_open(
        tasklist,
        filters=filters or None,
        include_done=show_all,
        sort=sort,
    )


# -- add ---------------------------------------------------------------


def cmd_add(
    tasklist: TaskList,
    tasks_path: str | Path,
    title: str,
    *,
    body: str = "",
    priority: str | None = None,
    labels: list[str] | None = None,
    milestone: str | None = None,
) -> Task:
    """Create a new `todo` task, save canonically, and regenerate TASKS.md."""
    now = _now_iso()
    task = Task(
        id=new_id(),
        title=title,
        body=body,
        status="todo",
        priority=priority,
        labels=list(labels or []),
        milestone=milestone,
        created_at=now,
        updated_at=now,
    )
    tasklist.tasks.append(task)
    save_and_regenerate(tasklist, tasks_path)
    return task


# -- edit ----------------------------------------------------------------


def cmd_edit(
    tasklist: TaskList,
    tasks_path: str | Path,
    ref: str,
    *,
    title: str | None = None,
    body: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    labels: list[str] | None = None,
    milestone: str | None = None,
) -> Task:
    """Update the given fields on the matched task (only non-`None` args apply).

    Rebuilt via `Task.from_dict` so the usual status/priority/type validation
    runs on the merged result rather than being duplicated here.
    """
    existing = require_task(tasklist, ref)
    data = existing.to_dict()

    if title is not None:
        data["title"] = title
    if body is not None:
        data["body"] = body
    if status is not None:
        data["status"] = status
    if priority is not None:
        data["priority"] = priority
    if labels is not None:
        data["labels"] = list(labels)
    if milestone is not None:
        data["milestone"] = milestone
    data["updated_at"] = _now_iso()

    updated = Task.from_dict(data)
    tasklist.tasks[tasklist.tasks.index(existing)] = updated
    save_and_regenerate(tasklist, tasks_path)
    return updated


# -- done / close ----------------------------------------------------------


def cmd_done(tasklist: TaskList, tasks_path: str | Path, ref: str) -> Task:
    """Mark the matched task `done`, stamping `closed_at`/`updated_at`."""
    existing = require_task(tasklist, ref)
    now = _now_iso()
    data = existing.to_dict()
    data["status"] = "done"
    data["closed_at"] = now
    data["updated_at"] = now

    updated = Task.from_dict(data)
    tasklist.tasks[tasklist.tasks.index(existing)] = updated
    save_and_regenerate(tasklist, tasks_path)
    return updated


# -- remove / rm -------------------------------------------------------


def cmd_remove(tasklist: TaskList, tasks_path: str | Path, ref: str) -> Task:
    """Delete the matched task from the list."""
    existing = require_task(tasklist, ref)
    tasklist.tasks.remove(existing)
    save_and_regenerate(tasklist, tasks_path)
    return existing


# -- status --------------------------------------------------------------


def _prune_days(tasklist: TaskList) -> int:
    raw = tasklist.config.get("prune_closed_after_days", DEFAULT_PRUNE_DAYS)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return DEFAULT_PRUNE_DAYS


def _is_prune_eligible(task: Task, now: datetime, threshold_days: int) -> bool:
    if task.status != "done":
        return False
    closed = parse_aware_datetime(task.closed_at)
    if closed is None:
        return False
    return now - closed > timedelta(days=threshold_days)


def cmd_status(tasklist: TaskList, *, now: datetime | None = None) -> str:
    """Status counts, last sync time, and a prune/rotation health hint."""
    now = now or datetime.now(timezone.utc)
    threshold = _prune_days(tasklist)
    prune_eligible = sum(1 for task in tasklist.tasks if _is_prune_eligible(task, now, threshold))

    lines = [render_summary(tasklist)]
    lines.append(f"  last_sync_at: {tasklist.last_sync_at or 'never'}")
    repo_suffix = f" ({tasklist.repo})" if tasklist.repo else ""
    lines.append(f"  provider: {tasklist.provider}{repo_suffix}")
    if prune_eligible:
        lines.append(
            f"  health: {prune_eligible} done task(s) closed > {threshold}d ago "
            "— will be pruned on next sync --apply"
        )
    else:
        lines.append(f"  health: ok (prune threshold {threshold}d)")

    return "\n".join(lines)
