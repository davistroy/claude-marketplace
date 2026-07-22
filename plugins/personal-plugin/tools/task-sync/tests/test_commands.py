"""Tests for the deterministic store operations in `task_sync.commands`."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from task_sync import commands, store
from task_sync.__main__ import main
from task_sync.commands import TaskNotFoundError
from task_sync.confidential.apply import REDACTION_MARK, VALID_DISPOSITIONS
from task_sync.models import Task, TaskList
from task_sync.providers.base import Issue, parse_aware_datetime
from task_sync.reconcile.classify import classify
from task_sync.reconcile.resolve import resolve

# A GitHub-token-shaped secret the confidentiality scanner reliably flags,
# used across scan-apply tests to exercise real content transformation
# (matches the fixture used in tests/test_confidential_apply.py).
_GH_SECRET = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


def _init_git_repo_with_origin(repo_root: Path, remote_url: str) -> None:
    """Create a real (but remote-less-network) git repo with `origin` set.

    Used to exercise `cmd_init`'s real `detect_provider`/`detect_gitea_base_url`
    path end to end, rather than mocking `subprocess` — no network I/O occurs,
    `git init`/`git remote add` never touch anything outside `repo_root`.
    """
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", remote_url],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )


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
    assert tasklist.config["adopt_closed_within_days"] == 0
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


def test_init_sets_gitea_url_for_http_gitea_origin(tmp_path: Path) -> None:
    _init_git_repo_with_origin(tmp_path, "https://git.example.com:3000/owner/repo.git")
    tasks_path = tmp_path / "tasks.json"

    commands.cmd_init(tasks_path, repo_root=str(tmp_path))

    tasklist = store.load(tasks_path)
    assert tasklist.provider == "gitea"
    assert tasklist.config["gitea_url"] == "https://git.example.com:3000"


def test_init_leaves_gitea_url_unset_for_ssh_gitea_origin(tmp_path: Path) -> None:
    _init_git_repo_with_origin(tmp_path, "git@git.example.com:owner/repo.git")
    tasks_path = tmp_path / "tasks.json"

    commands.cmd_init(tasks_path, repo_root=str(tmp_path))

    tasklist = store.load(tasks_path)
    assert tasklist.provider == "gitea"
    # No reliable http(s) scheme/port to derive from an ssh remote — leave it
    # for the `$GITEA_URL` / `tea` config fallback in `_build_provider`.
    assert not tasklist.config.get("gitea_url")


def test_init_does_not_set_gitea_url_for_github_origin(tmp_path: Path) -> None:
    _init_git_repo_with_origin(tmp_path, "https://github.com/owner/repo.git")
    tasks_path = tmp_path / "tasks.json"

    commands.cmd_init(tasks_path, repo_root=str(tmp_path))

    tasklist = store.load(tasks_path)
    assert tasklist.provider == "github"
    assert "gitea_url" not in tasklist.config


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


# -- adopt window ------------------------------------------------------


def test_adopt_window_absent_key_resolves_to_zero() -> None:
    # Migration safety: a pre-existing tasks.json predating this config key
    # (init is a no-op on an existing file) must resolve to "open issues
    # only", NOT inherit the unrelated 30-day prune default.
    tasklist = TaskList(config={})
    assert commands.adopt_window(tasklist) == 0


def test_adopt_window_reads_configured_value() -> None:
    tasklist = TaskList(config={"adopt_closed_within_days": 14})
    assert commands.adopt_window(tasklist) == 14


def test_adopt_window_is_independent_of_prune_days() -> None:
    # Reusing the prune window was the bug (#167): a large prune_closed_after_days
    # must not leak into the adopt window when the adopt key is absent.
    tasklist = TaskList(config={"prune_closed_after_days": 90})
    assert commands.adopt_window(tasklist) == 0


def test_adopt_window_invalid_value_falls_back_to_zero() -> None:
    tasklist = TaskList(config={"adopt_closed_within_days": "abc"})
    assert commands.adopt_window(tasklist) == 0


def test_adopt_window_none_value_falls_back_to_zero() -> None:
    tasklist = TaskList(config={"adopt_closed_within_days": None})
    assert commands.adopt_window(tasklist) == 0


def test_adopt_window_negative_value_clamps_to_zero() -> None:
    tasklist = TaskList(config={"adopt_closed_within_days": -5})
    assert commands.adopt_window(tasklist) == 0


# -- scan-apply --------------------------------------------------------


def _secret_task(task_id: str = "t-1", body: str | None = None) -> Task:
    return Task(id=task_id, title="T", body=body or f"secret ghp_{_GH_SECRET} tail", status="todo")


@pytest.mark.parametrize("disposition", VALID_DISPOSITIONS)
def test_scan_apply_stamps_confidentiality_for_every_disposition(
    tmp_path: Path, disposition: str
) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(_secret_task())
    store.save(tasklist, tasks_path)

    message = commands.cmd_scan_apply(tasklist, {"t-1": disposition}, tasks_path)

    reviewed = store.load(tasks_path).tasks[0]
    assert reviewed.confidentiality is not None
    assert reviewed.confidentiality["decision"] == disposition
    assert reviewed.confidentiality["reviewed_hash"]
    assert "reviewed 1 task(s)" in message
    assert f"{disposition}: 1" in message


def test_scan_apply_keep_is_content_noop(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)
    body_before = task.body

    commands.cmd_scan_apply(tasklist, {"t-1": "keep"}, tasks_path)

    assert task.body == body_before
    assert task.confidentiality is not None
    assert task.confidentiality["decision"] == "keep"


def test_scan_apply_redact_transforms_body(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)

    assert _GH_SECRET not in task.body
    assert REDACTION_MARK in task.body


def test_scan_apply_remove_transforms_body(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "remove"}, tasks_path)

    assert "ghp_" not in task.body
    assert _GH_SECRET not in task.body


def test_scan_apply_anonymize_transforms_body(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "anonymize"}, tasks_path)

    assert _GH_SECRET not in task.body
    assert "<<TERM_" in task.body


def test_scan_apply_unknown_task_id_raises_and_writes_nothing(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="T", status="todo"))
    store.save(tasklist, tasks_path)
    before = tasks_path.read_bytes()

    with pytest.raises(ValueError, match="t-nope"):
        commands.cmd_scan_apply(tasklist, {"t-nope": "keep"}, tasks_path)

    assert tasks_path.read_bytes() == before


def test_scan_apply_invalid_disposition_raises_and_writes_nothing(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="T", status="todo"))
    store.save(tasklist, tasks_path)
    before = tasks_path.read_bytes()

    with pytest.raises(ValueError, match="bogus"):
        commands.cmd_scan_apply(tasklist, {"t-1": "bogus"}, tasks_path)

    assert tasks_path.read_bytes() == before


def test_scan_apply_mixed_batch_rejects_whole_batch_and_writes_nothing(
    tmp_path: Path,
) -> None:
    """The key regression guard: one bad id in a batch must reject the WHOLE
    batch, leaving both the file and every in-memory task untouched — not
    silently apply-then-discard the entries that were fine (the old heredoc's
    bare `KeyError` mid-loop behavior)."""
    tasks_path = tmp_path / "tasks.json"
    good_task = Task(id="t-1", title="T1", status="todo")
    tasklist = _tasklist_with(good_task)
    store.save(tasklist, tasks_path)
    before = tasks_path.read_bytes()

    with pytest.raises(ValueError) as exc_info:
        commands.cmd_scan_apply(tasklist, {"t-1": "keep", "t-nope": "keep"}, tasks_path)

    assert "t-nope" in str(exc_info.value)
    assert tasks_path.read_bytes() == before
    assert good_task.confidentiality is None


def test_scan_apply_invalid_disposition_does_not_mutate_earlier_valid_entries(
    tmp_path: Path,
) -> None:
    """The up-front `invalid` check must be what rejects the batch — not
    `apply_review` raising mid-loop after it has already transformed earlier
    tasks in memory.

    The single-task test above cannot tell those apart: with one entry there
    is no "earlier task" to mutate, and the file is unwritten either way
    because the loop never reaches `save_and_regenerate`. Here the FIRST
    entry is a valid `redact` on a task carrying a real, scannable secret,
    so mid-loop validation would visibly destroy its body before the SECOND
    entry blew up. In-memory state is the assertion; file bytes alone are
    not enough.
    """
    tasks_path = tmp_path / "tasks.json"
    first = _secret_task("t-1")
    second = Task(id="t-2", title="T2", status="todo")
    tasklist = _tasklist_with(first, second)
    store.save(tasklist, tasks_path)
    before = tasks_path.read_bytes()
    body_before, title_before = first.body, first.title

    with pytest.raises(ValueError, match="bogus"):
        commands.cmd_scan_apply(tasklist, {"t-1": "redact", "t-2": "bogus"}, tasks_path)

    # The valid first entry was never applied, in memory or on disk.
    assert first.body == body_before
    assert first.title == title_before
    assert first.confidentiality is None
    assert second.confidentiality is None
    assert tasks_path.read_bytes() == before
    assert not commands.tasks_md_path(tasks_path).exists()


def test_scan_apply_combines_unknown_id_and_invalid_disposition_in_one_error(
    tmp_path: Path,
) -> None:
    """Both problem classes are collected and reported together in a single
    error — the "rejects the whole batch with a single error" contract. A
    `raise ValueError(problems[0])` would report only the first clause."""
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="T", status="todo"))
    store.save(tasklist, tasks_path)
    before = tasks_path.read_bytes()

    with pytest.raises(ValueError) as exc_info:
        commands.cmd_scan_apply(tasklist, {"t-nope": "keep", "t-1": "bogus"}, tasks_path)

    message = str(exc_info.value)
    assert "unknown task id(s): t-nope" in message
    assert "invalid disposition(s): t-1='bogus'" in message
    assert message.count(";") == 1  # one error, both clauses
    assert tasks_path.read_bytes() == before


# -- scan-apply: updated_at stamping (confidentiality vs. last-write-wins) --


def test_scan_apply_stamps_updated_at(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    task.updated_at = "2020-01-01T00:00:00+00:00"
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)

    assert task.updated_at is not None
    assert task.updated_at > "2020-01-01T00:00:00+00:00"


def test_scan_apply_stamps_updated_at_for_keep_too(tmp_path: Path) -> None:
    """`keep` changes no content but still records a decision, and `cmd_edit`
    stamps unconditionally — so does this. An unstamped `keep` would let the
    next sync recommend clobbering the just-reviewed state."""
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    task.updated_at = "2020-01-01T00:00:00+00:00"
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "keep"}, tasks_path)

    assert task.updated_at is not None
    assert task.updated_at > "2020-01-01T00:00:00+00:00"


def test_redacted_task_is_recommended_local_against_an_older_remote(tmp_path: Path) -> None:
    """The point of stamping `updated_at`: a task redacted seconds ago must NOT
    look older than its issue.

    `resolve._recommend` is last-write-wins on `updated_at`. Without the
    stamp the freshly-redacted task keeps its stale timestamp, the conflict
    recommendation comes back "remote", and accepting it pulls the
    un-redacted secret back out of the tracker.
    """
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    task.issue_number = 5
    task.updated_at = "2020-01-01T00:00:00+00:00"
    task.last_synced = {"hash": "stale-base", "at": "2020-01-01T00:00:00+00:00"}
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)

    issue = Issue(
        number=5,
        title="T",
        body="secret ghp_" + _GH_SECRET + " tail",
        state="open",
        labels=[],
        milestone=None,
        updated_at=parse_aware_datetime("2021-06-01T00:00:00Z"),
    )
    result = resolve(classify(tasklist, [issue]))

    assert len(result.conflicts) == 1
    assert result.conflicts[0].recommendation == "local"


# -- scan-apply: idempotence -----------------------------------------------


def test_scan_apply_rerun_with_same_disposition_writes_nothing(tmp_path: Path) -> None:
    """Re-running the same decisions file on unchanged content is a genuine
    no-op — byte-identical `tasks.json`.

    `apply_review` stamps a fresh `confidentiality["at"]` on every call, so
    without a skip the second run rewrites the file (and dirties git) purely
    to record a new timestamp. `updated_at` is likewise not re-stamped,
    because the skip happens before either write.
    """
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)
    after_first = tasks_path.read_bytes()
    md_after_first = commands.tasks_md_path(tasks_path).read_bytes()
    updated_at_after_first = task.updated_at

    message = commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)

    assert tasks_path.read_bytes() == after_first
    assert commands.tasks_md_path(tasks_path).read_bytes() == md_after_first
    assert task.updated_at == updated_at_after_first
    assert "already carry the requested disposition" in message
    assert "1 task(s)" in message


def test_scan_apply_rerun_with_a_different_disposition_still_applies(tmp_path: Path) -> None:
    """Re-deciding is a real change: `keep` then `redact` must transform."""
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "keep"}, tasks_path)
    assert _GH_SECRET in task.body  # keep is a content no-op

    message = commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)

    assert _GH_SECRET not in task.body
    assert REDACTION_MARK in task.body
    assert task.confidentiality["decision"] == "redact"
    assert "reviewed 1 task(s)" in message


def test_scan_apply_reapplies_when_content_changed_since_review(tmp_path: Path) -> None:
    """Same disposition, but the content was edited after the review: the
    recorded hash no longer covers it, so it must be re-scanned."""
    tasks_path = tmp_path / "tasks.json"
    task = _secret_task()
    tasklist = _tasklist_with(task)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)
    task.body = f"a NEW secret ghp_{_GH_SECRET} appeared"

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)

    assert _GH_SECRET not in task.body
    assert REDACTION_MARK in task.body


def test_scan_apply_partial_skip_reports_both_counts(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    already = _secret_task("t-1")
    fresh = _secret_task("t-2")
    tasklist = _tasklist_with(already, fresh)
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)
    message = commands.cmd_scan_apply(tasklist, {"t-1": "redact", "t-2": "redact"}, tasks_path)

    assert "reviewed 1 task(s)" in message
    assert "redact: 1" in message
    assert "(1 already up to date)" in message
    assert REDACTION_MARK in fresh.body


def test_scan_apply_empty_dispositions_writes_nothing(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="T", status="todo"))
    store.save(tasklist, tasks_path)
    before = tasks_path.read_bytes()

    message = commands.cmd_scan_apply(tasklist, {}, tasks_path)

    assert "nothing to apply" in message
    assert tasks_path.read_bytes() == before


def test_scan_apply_regenerates_tasks_md(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(_secret_task(body=f"ghp_{_GH_SECRET}"))
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "redact"}, tasks_path)

    md = commands.tasks_md_path(tasks_path).read_text(encoding="utf-8")
    assert "T" in md  # the (unaffected) title still renders


def test_scan_apply_uses_sensitive_terms_from_config(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    task = Task(id="t-1", title="Project Zephyrix status", status="todo")
    tasklist = _tasklist_with(task, config={"sensitive_terms": ["Zephyrix"]})
    store.save(tasklist, tasks_path)

    commands.cmd_scan_apply(tasklist, {"t-1": "anonymize"}, tasks_path)

    assert "Zephyrix" not in task.title
    assert "<<TERM_" in task.title


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


# -- CLI integration: scan-apply ---------------------------------------


def test_cli_scan_apply_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    store.save(_tasklist_with(_secret_task()), tasks_path)
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({"t-1": "redact"}), encoding="utf-8")

    exit_code = main(["scan-apply", "--tasks", str(tasks_path), "--decisions", str(decisions_path)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "reviewed 1 task(s)" in out
    assert "redact: 1" in out

    reloaded = store.load(tasks_path)
    assert reloaded.tasks[0].confidentiality is not None
    assert reloaded.tasks[0].confidentiality["decision"] == "redact"
    assert _GH_SECRET not in reloaded.tasks[0].body
    assert REDACTION_MARK in reloaded.tasks[0].body


def test_cli_scan_apply_wrapped_decisions_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--decisions` accepts the same flat-or-wrapped shape as `sync --decisions`."""
    tasks_path = tmp_path / "tasks.json"
    store.save(_tasklist_with(Task(id="t-1", title="T", status="todo")), tasks_path)
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({"decisions": {"t-1": "keep"}}), encoding="utf-8")

    exit_code = main(["scan-apply", "--tasks", str(tasks_path), "--decisions", str(decisions_path)])

    assert exit_code == 0
    assert store.load(tasks_path).tasks[0].confidentiality["decision"] == "keep"


def test_cli_scan_apply_bad_id_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasklist = _tasklist_with(Task(id="t-1", title="T", status="todo"))
    store.save(tasklist, tasks_path)
    before = tasks_path.read_bytes()
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({"t-nope": "keep"}), encoding="utf-8")

    exit_code = main(["scan-apply", "--tasks", str(tasks_path), "--decisions", str(decisions_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "task-sync scan-apply" in err
    assert "t-nope" in err
    assert tasks_path.read_bytes() == before


def test_cli_scan_apply_missing_tasks_file_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = str(tmp_path / "nope.json")
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({"t-1": "keep"}), encoding="utf-8")

    exit_code = main(["scan-apply", "--tasks", missing, "--decisions", str(decisions_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "task-sync init" in err


def test_cli_scan_apply_missing_decisions_file_errors_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--decisions` is required, so a stale/mistyped path is the likeliest
    user error. It must exit 1 with a message naming the path, not raise an
    uncaught FileNotFoundError (an OSError, which `except ValueError` misses)."""
    tasks_path = tmp_path / "tasks.json"
    store.save(_tasklist_with(Task(id="t-1", title="T", status="todo")), tasks_path)
    before = tasks_path.read_bytes()
    missing = str(tmp_path / "gone.json")

    exit_code = main(["scan-apply", "--tasks", str(tasks_path), "--decisions", missing])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "task-sync scan-apply" in err
    assert missing in err
    assert tasks_path.read_bytes() == before


def test_cli_scan_apply_malformed_decisions_file_names_the_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tasks_path = tmp_path / "tasks.json"
    store.save(_tasklist_with(Task(id="t-1", title="T", status="todo")), tasks_path)
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text("{not json", encoding="utf-8")

    exit_code = main(["scan-apply", "--tasks", str(tasks_path), "--decisions", str(decisions_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "malformed JSON in decisions file" in err
    assert str(decisions_path) in err


def test_cli_scan_apply_requires_decisions_argument(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    store.save(TaskList(), tasks_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["scan-apply", "--tasks", str(tasks_path)])
    assert exc_info.value.code != 0
