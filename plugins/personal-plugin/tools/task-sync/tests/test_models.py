"""Tests for Task/TaskList validation and the new_id() helper."""

from __future__ import annotations

import re

import pytest

from task_sync.models import Task, TaskList, new_id


def test_new_id_format() -> None:
    task_id = new_id()
    assert re.fullmatch(r"t-[0-9a-f]{6}", task_id)


def test_new_id_is_unique_across_many_calls() -> None:
    ids = {new_id() for _ in range(200)}
    assert len(ids) == 200


def test_task_defaults() -> None:
    task = Task(id="t-1", title="A task")
    assert task.status == "backlog"
    assert task.priority is None
    assert task.labels == []
    assert task.last_synced == {}
    assert task.confidentiality is None


def test_task_title_must_be_string() -> None:
    with pytest.raises(ValueError, match="'title' must be a string"):
        Task(id="t-1", title=123)  # type: ignore[arg-type]


def test_task_body_must_be_string() -> None:
    with pytest.raises(ValueError, match="'body' must be a string"):
        Task(id="t-1", title="ok", body=123)  # type: ignore[arg-type]


def test_task_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        Task(id="t-1", title="ok", status="nope")


def test_task_invalid_priority_raises() -> None:
    with pytest.raises(ValueError, match="invalid priority"):
        Task(id="t-1", title="ok", priority="P9")


def test_task_valid_priority_accepted() -> None:
    task = Task(id="t-1", title="ok", priority="P1")
    assert task.priority == "P1"


def test_task_labels_must_be_list_of_strings() -> None:
    with pytest.raises(ValueError, match="'labels' must be a list of strings"):
        Task(id="t-1", title="ok", labels="not-a-list")  # type: ignore[arg-type]


def test_task_labels_rejects_non_string_items() -> None:
    with pytest.raises(ValueError, match="'labels' must be a list of strings"):
        Task(id="t-1", title="ok", labels=[1, 2])  # type: ignore[list-item]


def test_task_milestone_must_be_string_or_none() -> None:
    with pytest.raises(ValueError, match="'milestone' must be a string"):
        Task(id="t-1", title="ok", milestone=123)  # type: ignore[arg-type]


def test_task_issue_number_must_be_int_or_none() -> None:
    with pytest.raises(ValueError, match="'issue_number' must be an int or None"):
        Task(id="t-1", title="ok", issue_number="42")  # type: ignore[arg-type]


def test_task_last_synced_must_be_dict() -> None:
    with pytest.raises(ValueError, match="'last_synced' must be a dict"):
        Task(id="t-1", title="ok", last_synced=["not", "a", "dict"])  # type: ignore[arg-type]


def test_task_confidentiality_must_be_dict_or_none() -> None:
    with pytest.raises(ValueError, match="'confidentiality' must be a dict or None"):
        Task(id="t-1", title="ok", confidentiality="secret")  # type: ignore[arg-type]


def test_task_to_dict_round_trips_via_from_dict() -> None:
    task = Task(
        id="t-1",
        title="ok",
        body="body",
        status="todo",
        priority="P2",
        labels=["a"],
        milestone="v1",
        issue_number=5,
        created_at="2026-01-01",
        updated_at="2026-01-02",
        closed_at=None,
        last_synced={"github": "2026-01-02"},
        confidentiality={"level": "public"},
    )
    restored = Task.from_dict(task.to_dict())
    assert restored == task


def test_task_from_dict_missing_required_field_raises() -> None:
    with pytest.raises(ValueError, match="missing required field"):
        Task.from_dict({"title": "no id"})


def test_tasklist_defaults() -> None:
    tasklist = TaskList()
    assert tasklist.provider == "none"
    assert tasklist.repo is None
    assert tasklist.tasks == []


def test_tasklist_config_must_be_dict() -> None:
    with pytest.raises(ValueError, match="'config' must be a dict"):
        TaskList(config="not-a-dict")  # type: ignore[arg-type]


def test_tasklist_tasks_must_be_list_of_task() -> None:
    with pytest.raises(ValueError, match="'tasks' must be a list of Task"):
        TaskList(tasks=["not-a-task"])  # type: ignore[list-item]


def test_tasklist_provider_must_be_string() -> None:
    with pytest.raises(ValueError, match="'provider' must be a string"):
        TaskList(provider=123)  # type: ignore[arg-type]


def test_tasklist_to_dict_and_from_dict_round_trip() -> None:
    tasklist = TaskList(
        provider="github",
        repo="owner/repo",
        last_sync_at="2026-01-01",
        config={"k": "v"},
        tasks=[Task(id="t-1", title="ok")],
    )
    restored = TaskList.from_dict(tasklist.to_dict())
    assert restored.provider == tasklist.provider
    assert restored.repo == tasklist.repo
    assert restored.config == tasklist.config
    assert [t.id for t in restored.tasks] == [t.id for t in tasklist.tasks]
