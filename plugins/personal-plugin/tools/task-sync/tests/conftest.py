"""Shared fixtures for task-sync tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from task_sync.providers.base import Issue, parse_aware_datetime


@pytest.fixture
def tasks_json_path(tmp_path: Path) -> Path:
    """Provide a scratch path for a tasks.json store, not yet created."""
    return tmp_path / "tasks.json"


class MockProvider:
    """In-memory Provider double — records every call, touches no network.

    Every apply/CLI test injects one of these so nothing ever shells out to
    `gh` or hits Gitea. It structurally satisfies `providers.base.Provider`
    (verified in the tests), returning normalized `Issue`s from `create`/
    `update` so apply can rebase `last_synced` off real return values.
    """

    def __init__(
        self,
        issues: list[Issue] | None = None,
        now: str = "2026-07-20T00:00:00Z",
    ) -> None:
        self._issues: dict[int, Issue] = {i.number: i for i in (issues or [])}
        self._next = max(self._issues, default=0) + 1
        self.now = now
        self.calls: list[tuple[Any, ...]] = []
        self.ensured_labels: list[str] = []
        self.ensured_milestones: list[str] = []

    def list_issues(self, state: str = "all") -> list[Issue]:
        self.calls.append(("list_issues", state))
        return list(self._issues.values())

    def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        milestone: str | None = None,
    ) -> Issue:
        self.calls.append(("create_issue", title))
        number = self._next
        self._next += 1
        issue = Issue(
            number=number,
            title=title,
            body=body,
            state="open",
            labels=list(labels or []),
            milestone=milestone,
            updated_at=parse_aware_datetime(self.now),  # type: ignore[arg-type]
            closed_at=None,
        )
        self._issues[number] = issue
        return issue

    def update_issue(self, number: int, **fields: Any) -> Issue:
        self.calls.append(("update_issue", number, dict(fields)))
        state = fields.get("state", "open")
        closed_at = parse_aware_datetime(self.now) if state == "closed" else None
        issue = Issue(
            number=number,
            title=fields.get("title", "T"),
            body=fields.get("body", ""),
            state=state,
            labels=list(fields.get("labels") or []),
            milestone=fields.get("milestone"),
            updated_at=parse_aware_datetime(self.now),  # type: ignore[arg-type]
            closed_at=closed_at,
        )
        self._issues[number] = issue
        return issue

    def set_state(self, number: int, state: str) -> None:
        self.calls.append(("set_state", number, state))

    def ensure_labels(self, names: list[str]) -> None:
        self.calls.append(("ensure_labels", list(names)))
        self.ensured_labels.extend(names)

    def ensure_milestone(self, name: str) -> None:
        self.calls.append(("ensure_milestone", name))
        self.ensured_milestones.append(name)

    def visibility(self) -> str:
        return "private"

    # -- test helpers --------------------------------------------------

    def method_calls(self, name: str) -> list[tuple[Any, ...]]:
        """Every recorded call to `name`."""
        return [c for c in self.calls if c[0] == name]
