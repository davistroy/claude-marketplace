"""Tests for the canonical, atomic tasks.json store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from task_sync.models import Task, TaskList
from task_sync.store import load, save


def _sample_tasklist() -> TaskList:
    return TaskList(
        provider="github",
        repo="owner/repo",
        last_sync_at="2026-07-17T12:00:00Z",
        config={"default_milestone": None},
        tasks=[
            Task(id="t-000002", title="Second task", status="todo", priority="P2"),
            Task(
                id="t-000001",
                title="First task",
                body="Some body text",
                status="in-progress",
                priority="P1",
                labels=["backend", "urgent"],
                milestone="v1.0",
                issue_number=42,
                created_at="2026-07-01T00:00:00Z",
                updated_at="2026-07-10T00:00:00Z",
                last_synced={"github": "2026-07-10T00:00:00Z"},
            ),
        ],
    )


def test_round_trip(tasks_json_path: Path) -> None:
    original = _sample_tasklist()
    save(original, tasks_json_path)

    loaded = load(tasks_json_path)

    assert loaded.provider == original.provider
    assert loaded.repo == original.repo
    assert loaded.last_sync_at == original.last_sync_at
    assert loaded.config == original.config
    assert {task.id for task in loaded.tasks} == {task.id for task in original.tasks}

    loaded_by_id = {task.id: task for task in loaded.tasks}
    assert loaded_by_id["t-000001"].title == "First task"
    assert loaded_by_id["t-000001"].labels == ["backend", "urgent"]
    assert loaded_by_id["t-000001"].issue_number == 42
    assert loaded_by_id["t-000002"].priority == "P2"


def test_double_save_is_byte_identical(tasks_json_path: Path) -> None:
    tasklist = _sample_tasklist()

    save(tasklist, tasks_json_path)
    first_bytes = tasks_json_path.read_bytes()

    save(tasklist, tasks_json_path)
    second_bytes = tasks_json_path.read_bytes()

    assert first_bytes == second_bytes


def test_save_then_load_then_save_is_byte_identical(tasks_json_path: Path) -> None:
    tasklist = _sample_tasklist()
    save(tasklist, tasks_json_path)
    first_bytes = tasks_json_path.read_bytes()

    reloaded = load(tasks_json_path)
    save(reloaded, tasks_json_path)
    second_bytes = tasks_json_path.read_bytes()

    assert first_bytes == second_bytes


def test_save_sorts_tasks_by_id(tasks_json_path: Path) -> None:
    tasklist = _sample_tasklist()
    save(tasklist, tasks_json_path)

    raw = json.loads(tasks_json_path.read_text(encoding="utf-8"))
    ids = [task["id"] for task in raw["tasks"]]
    assert ids == sorted(ids)


def test_save_output_has_trailing_newline_and_two_space_indent(tasks_json_path: Path) -> None:
    save(_sample_tasklist(), tasks_json_path)
    text = tasks_json_path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert not text.endswith("\n\n")
    # Two-space indent: nested keys are indented by exactly 2 spaces per level.
    assert '\n  "provider"' in text


def test_load_invalid_status_raises(tasks_json_path: Path) -> None:
    tasks_json_path.write_text(
        json.dumps(
            {
                "provider": "none",
                "repo": None,
                "last_sync_at": None,
                "config": {},
                "tasks": [{"id": "t-000001", "title": "Bad", "status": "not-a-status"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid status"):
        load(tasks_json_path)


def test_load_invalid_priority_raises(tasks_json_path: Path) -> None:
    tasks_json_path.write_text(
        json.dumps(
            {
                "provider": "none",
                "repo": None,
                "last_sync_at": None,
                "config": {},
                "tasks": [
                    {
                        "id": "t-000001",
                        "title": "Bad",
                        "status": "todo",
                        "priority": "P9",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid priority"):
        load(tasks_json_path)


def test_load_missing_required_field_raises(tasks_json_path: Path) -> None:
    tasks_json_path.write_text(
        json.dumps(
            {
                "provider": "none",
                "repo": None,
                "last_sync_at": None,
                "config": {},
                "tasks": [{"title": "No id field"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required field"):
        load(tasks_json_path)


def test_load_non_object_root_raises(tasks_json_path: Path) -> None:
    tasks_json_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load(tasks_json_path)


def test_save_creates_parent_directories(tmp_path: Path) -> None:
    nested_path = tmp_path / "nested" / "dir" / "tasks.json"
    save(_sample_tasklist(), nested_path)
    assert nested_path.exists()


def test_empty_tasklist_round_trip(tasks_json_path: Path) -> None:
    save(TaskList(), tasks_json_path)
    loaded = load(tasks_json_path)
    assert loaded.tasks == []
    assert loaded.provider == "none"
