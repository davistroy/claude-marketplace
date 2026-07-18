"""Tests for the TASKS.md renderer and status summary."""

from __future__ import annotations

from task_sync.models import Task, TaskList
from task_sync.render import render_open, render_summary


def _mixed_tasklist() -> TaskList:
    return TaskList(
        tasks=[
            Task(
                id="t-000001", title="Todo with issue", status="todo", priority="P1", issue_number=7
            ),
            Task(id="t-000002", title="Todo no issue", status="todo"),
            Task(
                id="t-000003",
                title="Blocked task",
                status="blocked",
                last_synced={"blocked_on": "t-000001"},
            ),
            Task(id="t-000004", title="Blocked no reason", status="blocked"),
            Task(id="t-000005", title="Done task", status="done", issue_number=3),
            Task(id="t-000006", title="In progress", status="in-progress", labels=["backend"]),
            Task(id="t-000007", title="Backlog item", status="backlog"),
        ]
    )


def test_render_open_filters_by_status_todo() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist, filters={"status": "todo"})

    assert "Todo with issue" in output
    assert "Todo no issue" in output
    assert "Blocked task" not in output
    assert "Done task" not in output
    assert "In progress" not in output
    assert "Backlog item" not in output
    assert "2 open tasks" in output


def test_render_open_hides_done_by_default() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist)

    assert "Done task" not in output
    assert "Todo with issue" in output
    assert "Blocked task" in output


def test_render_open_shows_done_when_explicitly_filtered() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist, filters={"status": "done"})

    assert "Done task" in output
    assert "1 open task" in output


def test_render_open_missing_issue_number_shows_em_dash() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist, filters={"status": "todo"})

    lines = [line for line in output.splitlines() if "Todo no issue" in line]
    assert len(lines) == 1
    assert "—" in lines[0]


def test_render_open_present_issue_number_shown() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist, filters={"status": "todo"})

    lines = [line for line in output.splitlines() if "Todo with issue" in line]
    assert len(lines) == 1
    assert "7" in lines[0]


def test_render_open_blocked_shows_what_it_waits_on() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist, filters={"status": "blocked"})

    lines = output.splitlines()
    blocked_with_reason = [line for line in lines if "Blocked task" in line][0]
    blocked_no_reason = [line for line in lines if "Blocked no reason" in line][0]

    assert "blocked on t-000001" in blocked_with_reason
    assert "(blocked)" in blocked_no_reason


def test_render_open_empty_tasklist() -> None:
    output = render_open(TaskList())
    assert "no matching tasks" in output
    assert "0 open tasks" in output


def test_render_open_no_matches_for_filter() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist, filters={"status": "todo", "priority": "P4"})
    assert "no matching tasks" in output


def test_render_open_arbitrary_filter_key() -> None:
    tasklist = _mixed_tasklist()
    output = render_open(tasklist, filters={"labels": ["backend"]})
    assert "In progress" in output
    assert "Todo with issue" not in output


def test_render_open_labels_column_joins_with_commas() -> None:
    tasklist = TaskList(
        tasks=[Task(id="t-1", title="Multi label", status="todo", labels=["a", "b"])]
    )
    output = render_open(tasklist)
    line = [line for line in output.splitlines() if "Multi label" in line][0]
    assert "a, b" in line


def test_render_summary_counts_by_status() -> None:
    tasklist = _mixed_tasklist()
    summary = render_summary(tasklist)

    assert "todo: 2" in summary
    assert "blocked: 2" in summary
    assert "done: 1" in summary
    assert "in-progress: 1" in summary
    assert "backlog: 1" in summary
    assert "total: 7" in summary
    assert "open: 6" in summary


def test_render_summary_empty_tasklist() -> None:
    summary = render_summary(TaskList())
    assert "total: 0" in summary
    assert "open: 0" in summary
