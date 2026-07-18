"""Tests for the deterministic store operations in `task_sync.commands`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from task_sync import commands, store
from task_sync.__main__ import main
from task_sync.commands import TaskNotFoundError
from task_sync.models import Task, TaskList


def _tasklist_with(*tasks: Task, **header: object) -> TaskList:
    return TaskList(tasks=list(tasks), **header)  # type: ignore[arg-type]


# -- init --------------------------------------------------------------


def test_init_creates_tasks_json_and_tasks_md(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"

    message = commands.cmd_init(tasks_path, repo_root=str(tmp_path))

    assert tasks_path.exists()
    assert "created" in message
    tasklist = store.load(tasks_path)
    assert tasklist.provider == "none"  # tmp_path is not a git repo
    assert tasklist.config["prune_closed_after_days"] == 30
    assert tasklist.config["sensitive_terms"] == []
    assert tasklist.last_sync_at is None
    assert commands.tasks_md_path(tasks_path).exists()


def test_init_is_noop_when_tasks_json_exists(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = _tasklist_with(Task(id="t-1", title="Existing", status="todo"))
    store.save(original, tasks_path)
    before = tasks_path.read_text(encoding="utf-8")

    message = commands.cmd_init(tasks_path, repo_root=str(tmp_path))

    assert "already exists" in message
    assert tasks_path.read_text(encoding="utf-8") == before
    # TASKS.md is still (re)generated even on the no-op path.
    assert commands.tasks_md_path(tasks_path).exists()
    assert "Existing" in commands.tasks_md_path(tasks_path).read_text(encoding="utf-8")


def test_init_regenerates_stale_tasks_md(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="Fresh title", status="todo"))
    store.save(tasklist, tasks_path)
    commands.tasks_md_path(tasks_path).write_text("stale content", encoding="utf-8")

    commands.cmd_init(tasks_path, repo_root=str(tmp_path))

    md = commands.tasks_md_path(tasks_path).read_text(encoding="utf-8")
    assert "Fresh title" in md
    assert "stale content" not in md


# -- add -----------------------------------------------------------------


def test_add_creates_todo_task_with_defaults(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = TaskList()

    task = commands.cmd_add(tasklist, tasks_path, "Write docs")

    assert task.title == "Write docs"
    assert task.status == "todo"
    assert task.priority is None
    assert task.labels == []
    assert task.created_at is not None
    assert task.updated_at is not None
    assert task in tasklist.tasks

    reloaded = store.load(tasks_path)
    assert [t.id for t in reloaded.tasks] == [task.id]


def test_add_applies_optional_fields(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = TaskList()

    task = commands.cmd_add(
        tasklist,
        tasks_path,
        "Ship feature",
        body="Some detail",
        priority="P1",
        labels=["backend", "urgent"],
        milestone="v1",
    )

    assert task.body == "Some detail"
    assert task.priority == "P1"
    assert task.labels == ["backend", "urgent"]
    assert task.milestone == "v1"


def test_add_rejects_invalid_priority(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = TaskList()

    with pytest.raises(ValueError):
        commands.cmd_add(tasklist, tasks_path, "Bad task", priority="P9")


def test_add_regenerates_tasks_md(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = TaskList()

    commands.cmd_add(tasklist, tasks_path, "Visible task")

    md = commands.tasks_md_path(tasks_path).read_text(encoding="utf-8")
    assert "Visible task" in md


# -- edit ------------------------------------------------------------------


def test_edit_updates_only_supplied_fields(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="Old title", body="Old body", status="todo", priority="P2")
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    updated = commands.cmd_edit(tasklist, tasks_path, "t-1", title="New title")

    assert updated.title == "New title"
    assert updated.body == "Old body"
    assert updated.priority == "P2"
    assert updated.updated_at is not None


def test_edit_replaces_labels_wholesale(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="T", status="todo", labels=["a", "b"])
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    updated = commands.cmd_edit(tasklist, tasks_path, "t-1", labels=["c"])

    assert updated.labels == ["c"]


def test_edit_by_issue_number(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="T", status="todo", issue_number=42)
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    updated = commands.cmd_edit(tasklist, tasks_path, "42", status="in-progress")
    assert updated.status == "in-progress"

    # Also matches the '#'-prefixed form.
    updated_again = commands.cmd_edit(tasklist, tasks_path, "#42", status="blocked")
    assert updated_again.status == "blocked"


def test_edit_rejects_invalid_status(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="T", status="todo")
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    with pytest.raises(ValueError):
        commands.cmd_edit(tasklist, tasks_path, "t-1", status="nope")


def test_edit_missing_task_raises_not_found(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = TaskList()
    store.save(tasklist, tasks_path)

    with pytest.raises(TaskNotFoundError):
        commands.cmd_edit(tasklist, tasks_path, "t-does-not-exist", title="X")


def test_edit_persists_and_regenerates_tasks_md(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="Before", status="todo")
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    commands.cmd_edit(tasklist, tasks_path, "t-1", title="After")

    reloaded = store.load(tasks_path)
    assert reloaded.tasks[0].title == "After"
    md = commands.tasks_md_path(tasks_path).read_text(encoding="utf-8")
    assert "After" in md
    assert "Before" not in md


# -- done ------------------------------------------------------------------


def test_done_sets_status_and_closed_at(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="T", status="in-progress")
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    updated = commands.cmd_done(tasklist, tasks_path, "t-1")

    assert updated.status == "done"
    assert updated.closed_at is not None
    reloaded = store.load(tasks_path)
    assert reloaded.tasks[0].status == "done"


def test_done_missing_task_raises_not_found(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = TaskList()
    store.save(tasklist, tasks_path)

    with pytest.raises(TaskNotFoundError):
        commands.cmd_done(tasklist, tasks_path, "nope")


def test_done_hides_task_from_default_list(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="Finish me", status="todo")
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    commands.cmd_done(tasklist, tasks_path, "t-1")

    output = commands.cmd_list(tasklist)
    assert "Finish me" not in output
    output_all = commands.cmd_list(tasklist, show_all=True)
    assert "Finish me" in output_all


# -- remove ------------------------------------------------------------


def test_remove_deletes_task(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="Gone soon", status="todo")
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    removed = commands.cmd_remove(tasklist, tasks_path, "t-1")

    assert removed.id == "t-1"
    assert tasklist.tasks == []
    reloaded = store.load(tasks_path)
    assert reloaded.tasks == []


def test_remove_missing_task_raises_not_found(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = TaskList()
    store.save(tasklist, tasks_path)

    with pytest.raises(TaskNotFoundError):
        commands.cmd_remove(tasklist, tasks_path, "t-nope")


def test_remove_regenerates_tasks_md(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    original = Task(id="t-1", title="Ephemeral", status="todo")
    tasklist = _tasklist_with(original)
    store.save(tasklist, tasks_path)

    commands.cmd_remove(tasklist, tasks_path, "t-1")

    md = commands.tasks_md_path(tasks_path).read_text(encoding="utf-8")
    assert "Ephemeral" not in md


# -- list / filters -------------------------------------------------------


def _filter_fixture() -> TaskList:
    return _tasklist_with(
        Task(id="t-1", title="Todo P1", status="todo", priority="P1"),
        Task(id="t-2", title="Todo P2", status="todo", priority="P2"),
        Task(id="t-3", title="Blocked task", status="blocked"),
        Task(id="t-4", title="Done task", status="done"),
        Task(id="t-5", title="Milestoned", status="todo", milestone="v2"),
    )


def test_list_filters_by_status() -> None:
    tasklist = _filter_fixture()
    output = commands.cmd_list(tasklist, status="blocked")
    assert "Blocked task" in output
    assert "Todo P1" not in output


def test_list_filters_by_priority() -> None:
    tasklist = _filter_fixture()
    output = commands.cmd_list(tasklist, priority="P1")
    assert "Todo P1" in output
    assert "Todo P2" not in output


def test_list_filters_by_milestone() -> None:
    tasklist = _filter_fixture()
    output = commands.cmd_list(tasklist, milestone="v2")
    assert "Milestoned" in output
    assert "Todo P1" not in output


def test_list_hides_done_by_default() -> None:
    tasklist = _filter_fixture()
    output = commands.cmd_list(tasklist)
    assert "Done task" not in output


def test_list_all_includes_done() -> None:
    tasklist = _filter_fixture()
    output = commands.cmd_list(tasklist, show_all=True)
    assert "Done task" in output


def test_list_sort_by_title() -> None:
    tasklist = _tasklist_with(
        Task(id="t-1", title="Zeta", status="todo"),
        Task(id="t-2", title="Alpha", status="todo"),
    )
    output = commands.cmd_list(tasklist, sort="title")
    lines = [line for line in output.splitlines() if line.startswith("|") and "---" not in line]
    # First data row (after header) should be Alpha.
    assert "Alpha" in lines[1]
    assert "Zeta" in lines[2]


# -- status ----------------------------------------------------------------


def test_status_reports_counts_and_last_sync() -> None:
    tasklist = _filter_fixture()
    tasklist.last_sync_at = "2026-07-01T00:00:00+00:00"

    output = commands.cmd_status(tasklist)

    assert "todo: 3" in output
    assert "blocked: 1" in output
    assert "done: 1" in output
    assert "last_sync_at: 2026-07-01T00:00:00+00:00" in output


def test_status_reports_never_synced() -> None:
    tasklist = TaskList()
    output = commands.cmd_status(tasklist)
    assert "last_sync_at: never" in output


def test_status_flags_prune_eligible_done_tasks() -> None:
    long_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    tasklist = _tasklist_with(
        Task(id="t-1", title="Old and done", status="done", closed_at=long_ago),
        config={"prune_closed_after_days": 30},
    )

    output = commands.cmd_status(tasklist)

    assert "1 done task(s) closed > 30d ago" in output


def test_status_health_ok_when_nothing_prune_eligible() -> None:
    tasklist = TaskList()
    output = commands.cmd_status(tasklist)
    assert "health: ok" in output


# -- find_task / require_task ----------------------------------------------


def test_find_task_matches_by_id() -> None:
    task = Task(id="t-1", title="T", status="todo")
    tasklist = _tasklist_with(task)
    assert commands.find_task(tasklist, "t-1") is task


def test_find_task_matches_by_hash_prefixed_issue_number() -> None:
    task = Task(id="t-1", title="T", status="todo", issue_number=7)
    tasklist = _tasklist_with(task)
    assert commands.find_task(tasklist, "#7") is task
    assert commands.find_task(tasklist, "7") is task


def test_find_task_returns_none_for_no_match() -> None:
    tasklist = TaskList()
    assert commands.find_task(tasklist, "t-nope") is None


def test_require_task_raises_for_no_match() -> None:
    tasklist = TaskList()
    with pytest.raises(TaskNotFoundError):
        commands.require_task(tasklist, "t-nope")


# -- parse_labels ------------------------------------------------------


def test_parse_labels_splits_and_strips() -> None:
    assert commands.parse_labels("a, b ,c") == ["a", "b", "c"]


def test_parse_labels_none_stays_none() -> None:
    assert commands.parse_labels(None) is None


def test_parse_labels_empty_string_yields_empty_list() -> None:
    assert commands.parse_labels("") == []


# -- CLI integration (main()) -----------------------------------------


def test_cli_init_then_add_then_list(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"

    assert main(["init", "--tasks", str(tasks_path), "--repo-root", str(tmp_path)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "add",
                "--tasks",
                str(tasks_path),
                "Ship the CLI",
                "--priority",
                "P2",
                "--labels",
                "cli, urgent",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "Added" in out
    assert "Ship the CLI" in out

    assert main(["list", "--tasks", str(tasks_path)]) == 0
    out = capsys.readouterr().out
    assert "Ship the CLI" in out


def test_cli_ls_alias_matches_list(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="Aliased", status="todo"))
    store.save(tasklist, tasks_path)

    assert main(["ls", "--tasks", str(tasks_path)]) == 0
    out = capsys.readouterr().out
    assert "Aliased" in out


def test_cli_edit_updates_task(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="Before", status="todo"))
    store.save(tasklist, tasks_path)

    exit_code = main(["edit", "t-1", "--tasks", str(tasks_path), "--title", "After"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Updated" in out
    assert "After" in out
    assert store.load(tasks_path).tasks[0].title == "After"


def test_cli_edit_missing_task_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    store.save(TaskList(), tasks_path)

    exit_code = main(["edit", "t-nope", "--tasks", str(tasks_path), "--title", "X"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "no task matching" in err


def test_cli_close_alias_marks_done(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="Finish", status="todo"))
    store.save(tasklist, tasks_path)

    exit_code = main(["close", "t-1", "--tasks", str(tasks_path)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Closed" in out
    assert store.load(tasks_path).tasks[0].status == "done"


def test_cli_rm_alias_removes_task(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="Gone", status="todo"))
    store.save(tasklist, tasks_path)

    exit_code = main(["rm", "t-1", "--tasks", str(tasks_path)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Removed" in out
    assert store.load(tasks_path).tasks == []


def test_cli_remove_missing_task_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    store.save(TaskList(), tasks_path)

    exit_code = main(["remove", "t-nope", "--tasks", str(tasks_path)])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "no task matching" in err


def test_cli_status_reports_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    store.save(_filter_fixture(), tasks_path)

    exit_code = main(["status", "--tasks", str(tasks_path)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Status summary" in out
    assert "last_sync_at" in out


def test_cli_add_invalid_priority_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tasks_path = tmp_path / "tasks.json"
    store.save(TaskList(), tasks_path)

    exit_code = main(["add", "Bad", "--tasks", str(tasks_path), "--priority", "P9"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "task-sync add" in err


def test_cli_missing_tasks_file_for_add_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = str(tmp_path / "nope.json")
    exit_code = main(["add", "Whatever", "--tasks", missing])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "task-sync init" in err


def test_cli_init_is_noop_second_time(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    assert main(["init", "--tasks", str(tasks_path), "--repo-root", str(tmp_path)]) == 0
    capsys.readouterr()
    assert main(["init", "--tasks", str(tasks_path), "--repo-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "already exists" in out
