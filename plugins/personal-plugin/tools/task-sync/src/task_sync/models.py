"""Task and TaskList data model for task-sync.

Dependency choice (Phase 1, recorded per plan Notes): plain stdlib
`dataclasses` with explicit validation, not pydantic. The schema is small,
validation needs are simple (enum membership + a handful of type checks),
and keeping the package dependency-free means the CI/test/venv story stays
trivial through Phase 1-4. Revisit only if a later phase needs nested-model
coercion pydantic would make substantially simpler.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

# Canonical status values. Order matters for anything that sorts/renders by
# workflow stage (see render.py); treat this tuple as the source of truth.
VALID_STATUSES: tuple[str, ...] = ("backlog", "todo", "in-progress", "blocked", "done")

# Priority is optional; when present it must be one of these.
VALID_PRIORITIES: tuple[str, ...] = ("P1", "P2", "P3", "P4")


def new_id() -> str:
    """Generate a short, stable task id: `t-` followed by 6 hex characters."""
    return f"t-{secrets.token_hex(3)}"


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name!r} must be a string, got {type(value).__name__}")
    return value


def _require_optional_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_str(value, field_name)


@dataclass
class Task:
    """A single task, whether or not it is synced to a remote issue tracker."""

    id: str
    title: str
    body: str = ""
    status: str = "backlog"
    priority: str | None = None
    labels: list[str] = field(default_factory=list)
    milestone: str | None = None
    issue_number: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None
    last_synced: dict[str, Any] = field(default_factory=dict)
    confidentiality: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.id = _require_str(self.id, "id")
        self.title = _require_str(self.title, "title")
        self.body = _require_str(self.body, "body")

        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"invalid status {self.status!r} for task {self.id!r}; "
                f"must be one of {VALID_STATUSES}"
            )

        if self.priority is not None and self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"invalid priority {self.priority!r} for task {self.id!r}; "
                f"must be one of {VALID_PRIORITIES} or None"
            )

        if not isinstance(self.labels, list) or not all(
            isinstance(label, str) for label in self.labels
        ):
            raise ValueError(f"'labels' must be a list of strings for task {self.id!r}")

        self.milestone = _require_optional_str(self.milestone, "milestone")

        if self.issue_number is not None and not isinstance(self.issue_number, int):
            raise ValueError(f"'issue_number' must be an int or None for task {self.id!r}")

        self.created_at = _require_optional_str(self.created_at, "created_at")
        self.updated_at = _require_optional_str(self.updated_at, "updated_at")
        self.closed_at = _require_optional_str(self.closed_at, "closed_at")

        if not isinstance(self.last_synced, dict):
            raise ValueError(f"'last_synced' must be a dict for task {self.id!r}")

        if self.confidentiality is not None and not isinstance(self.confidentiality, dict):
            raise ValueError(f"'confidentiality' must be a dict or None for task {self.id!r}")

    def to_dict(self) -> dict[str, Any]:
        """Canonical dict representation with a stable key order."""
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "status": self.status,
            "priority": self.priority,
            "labels": list(self.labels),
            "milestone": self.milestone,
            "issue_number": self.issue_number,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "last_synced": dict(self.last_synced),
            "confidentiality": self.confidentiality,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        try:
            return cls(
                id=data["id"],
                title=data["title"],
                body=data.get("body", ""),
                status=data.get("status", "backlog"),
                priority=data.get("priority"),
                labels=list(data.get("labels", [])),
                milestone=data.get("milestone"),
                issue_number=data.get("issue_number"),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                closed_at=data.get("closed_at"),
                last_synced=dict(data.get("last_synced", {})),
                confidentiality=data.get("confidentiality"),
            )
        except KeyError as exc:
            raise ValueError(f"task is missing required field: {exc}") from exc


@dataclass
class TaskList:
    """The full canonical store: header metadata plus the task collection."""

    provider: str = "none"
    repo: str | None = None
    last_sync_at: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.provider = _require_str(self.provider, "provider")
        self.repo = _require_optional_str(self.repo, "repo")
        self.last_sync_at = _require_optional_str(self.last_sync_at, "last_sync_at")
        if not isinstance(self.config, dict):
            raise ValueError("'config' must be a dict")
        if not isinstance(self.tasks, list) or not all(
            isinstance(task, Task) for task in self.tasks
        ):
            raise ValueError("'tasks' must be a list of Task instances")

    def to_dict(self) -> dict[str, Any]:
        """Canonical dict representation. `store.save` sorts tasks by id on top of this."""
        return {
            "provider": self.provider,
            "repo": self.repo,
            "last_sync_at": self.last_sync_at,
            "config": dict(self.config),
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskList":
        tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
        return cls(
            provider=data.get("provider", "none"),
            repo=data.get("repo"),
            last_sync_at=data.get("last_sync_at"),
            config=dict(data.get("config", {})),
            tasks=tasks,
        )
