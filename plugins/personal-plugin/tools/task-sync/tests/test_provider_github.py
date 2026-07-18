"""Tests for the GitHub adapter, entirely mocking `subprocess.run`.

No live `gh` calls: every test installs a fake router keyed on the argv gh
would receive and returns recorded JSON, mirroring real `gh issue list
--json ...` output shapes.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Callable

import pytest

from task_sync.providers.github import GithubProvider

_ISSUE_FIXTURE = {
    "number": 42,
    "title": "Fix the thing",
    "body": "Some body text",
    "state": "OPEN",
    "updatedAt": "2026-07-10T12:00:00Z",
    "closedAt": None,
    "labels": [{"name": "bug"}, {"name": "status/todo"}],
    "milestone": {"title": "v1.0"},
}

_CLOSED_ISSUE_FIXTURE = {
    "number": 43,
    "title": "Old bug",
    "body": "",
    "state": "CLOSED",
    "updatedAt": "2026-06-01T00:00:00Z",
    "closedAt": "2026-06-15T00:00:00Z",
    "labels": [],
    "milestone": None,
}


class FakeCompletedProcess:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class FakeGh:
    """Routes fake `subprocess.run(["gh", *args], ...)` calls to canned responses."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.routes: dict[tuple[str, ...], Callable[[list[str]], FakeCompletedProcess]] = {}

    def route(
        self,
        prefix: tuple[str, ...],
        handler: Callable[[list[str]], FakeCompletedProcess],
    ) -> None:
        self.routes[prefix] = handler

    def __call__(self, argv: list[str], **kwargs: Any) -> FakeCompletedProcess:
        args = argv[1:]  # drop "gh"
        self.calls.append(args)
        for prefix, handler in self.routes.items():
            if tuple(args[: len(prefix)]) == prefix:
                return handler(args)
        raise AssertionError(f"no fake route for gh {' '.join(args)}")


@pytest.fixture
def fake_gh(monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    fake = FakeGh()
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def _json_ok(data: Any) -> FakeCompletedProcess:
    return FakeCompletedProcess(stdout=json.dumps(data))


def test_list_issues_returns_normalized_issues(fake_gh: FakeGh) -> None:
    fake_gh.route(
        ("issue", "list"),
        lambda args: _json_ok([_ISSUE_FIXTURE, _CLOSED_ISSUE_FIXTURE]),
    )

    provider = GithubProvider("owner/repo")
    issues = provider.list_issues(state="all")

    assert len(issues) == 2
    assert issues[0].number == 42
    assert issues[0].state == "open"
    assert issues[0].labels == ["bug", "status/todo"]
    assert issues[0].milestone == "v1.0"
    assert issues[0].updated_at.tzinfo is not None
    assert issues[1].state == "closed"
    assert issues[1].closed_at is not None
    assert issues[1].milestone is None

    list_call = next(c for c in fake_gh.calls if c[:2] == ["issue", "list"])
    assert "--repo" in list_call and "owner/repo" in list_call
    assert "--state" in list_call and "all" in list_call


def test_visibility_public(fake_gh: FakeGh) -> None:
    fake_gh.route(("repo", "view"), lambda args: _json_ok({"visibility": "PUBLIC"}))
    provider = GithubProvider("owner/repo")
    assert provider.visibility() == "public"


def test_visibility_private(fake_gh: FakeGh) -> None:
    fake_gh.route(("repo", "view"), lambda args: _json_ok({"visibility": "PRIVATE"}))
    provider = GithubProvider("owner/repo")
    assert provider.visibility() == "private"


def test_create_issue_creates_labels_and_returns_normalized_issue(fake_gh: FakeGh) -> None:
    def _milestones_route(args: list[str]) -> FakeCompletedProcess:
        if "-f" not in args:
            return _json_ok([])
        return FakeCompletedProcess(stdout="")

    fake_gh.route(("label", "list"), lambda args: _json_ok([{"name": "bug"}]))
    fake_gh.route(("label", "create"), lambda args: FakeCompletedProcess(stdout=""))
    fake_gh.route(("api", "repos/owner/repo/milestones"), _milestones_route)
    fake_gh.route(
        ("issue", "create"),
        lambda args: FakeCompletedProcess(stdout="https://github.com/owner/repo/issues/42\n"),
    )
    fake_gh.route(("issue", "view"), lambda args: _json_ok(_ISSUE_FIXTURE))

    provider = GithubProvider("owner/repo")
    issue = provider.create_issue(
        "Fix the thing", "Some body text", labels=["bug", "status/todo"], milestone="v1.0"
    )

    assert issue.number == 42
    assert issue.title == "Fix the thing"

    create_call = next(c for c in fake_gh.calls if c[:2] == ["issue", "create"])
    assert create_call.count("--label") == 2
    assert "--milestone" in create_call and "v1.0" in create_call

    # New label ("status/todo") was created since it wasn't in the existing list.
    label_create_calls = [c for c in fake_gh.calls if c[:2] == ["label", "create"]]
    assert any(c[2] == "status/todo" for c in label_create_calls)


def test_create_issue_raises_on_unparseable_output(fake_gh: FakeGh) -> None:
    fake_gh.route(("issue", "create"), lambda args: FakeCompletedProcess(stdout="not a url"))

    provider = GithubProvider("owner/repo")
    with pytest.raises(RuntimeError, match="could not parse issue number"):
        provider.create_issue("t", "b")


def test_update_issue_diffs_labels_and_edits(fake_gh: FakeGh) -> None:
    fake_gh.route(("label", "list"), lambda args: _json_ok([{"name": "bug"}, {"name": "wontfix"}]))
    fake_gh.route(
        ("issue", "view"),
        lambda args: _json_ok({**_ISSUE_FIXTURE, "labels": [{"name": "bug"}, {"name": "wontfix"}]}),
    )
    fake_gh.route(("issue", "edit"), lambda args: FakeCompletedProcess(stdout=""))

    provider = GithubProvider("owner/repo")
    issue = provider.update_issue(42, title="New title", labels=["bug"])

    assert issue.number == 42

    edit_call = next(c for c in fake_gh.calls if c[:2] == ["issue", "edit"])
    assert "--title" in edit_call and "New title" in edit_call
    assert "--remove-label" in edit_call and "wontfix" in edit_call
    # "bug" is already present, so it should not be re-added.
    add_label_indices = [i for i, v in enumerate(edit_call) if v == "--add-label"]
    assert not add_label_indices


def test_update_issue_clears_milestone(fake_gh: FakeGh) -> None:
    fake_gh.route(("issue", "view"), lambda args: _json_ok(_ISSUE_FIXTURE))
    fake_gh.route(("issue", "edit"), lambda args: FakeCompletedProcess(stdout=""))

    provider = GithubProvider("owner/repo")
    provider.update_issue(42, milestone=None)

    edit_call = next(c for c in fake_gh.calls if c[:2] == ["issue", "edit"])
    assert "--remove-milestone" in edit_call


def test_update_issue_no_fields_still_returns_current_issue(fake_gh: FakeGh) -> None:
    fake_gh.route(("issue", "view"), lambda args: _json_ok(_ISSUE_FIXTURE))

    provider = GithubProvider("owner/repo")
    issue = provider.update_issue(42)

    assert issue.number == 42
    assert all(c[:2] != ["issue", "edit"] for c in fake_gh.calls)


def test_update_issue_state_calls_set_state(fake_gh: FakeGh) -> None:
    fake_gh.route(("issue", "close"), lambda args: FakeCompletedProcess(stdout=""))
    fake_gh.route(("issue", "view"), lambda args: _json_ok(_CLOSED_ISSUE_FIXTURE))

    provider = GithubProvider("owner/repo")
    issue = provider.update_issue(43, state="closed")

    assert issue.state == "closed"
    assert any(c[:2] == ["issue", "close"] for c in fake_gh.calls)


def test_set_state_open_reopens(fake_gh: FakeGh) -> None:
    fake_gh.route(("issue", "reopen"), lambda args: FakeCompletedProcess(stdout=""))
    provider = GithubProvider("owner/repo")
    provider.set_state(42, "open")
    assert any(c[:2] == ["issue", "reopen"] for c in fake_gh.calls)


def test_set_state_closed_closes(fake_gh: FakeGh) -> None:
    fake_gh.route(("issue", "close"), lambda args: FakeCompletedProcess(stdout=""))
    provider = GithubProvider("owner/repo")
    provider.set_state(42, "closed")
    assert any(c[:2] == ["issue", "close"] for c in fake_gh.calls)


def test_set_state_invalid_raises(fake_gh: FakeGh) -> None:
    provider = GithubProvider("owner/repo")
    with pytest.raises(ValueError, match="invalid state"):
        provider.set_state(42, "merged")


def test_ensure_labels_creates_only_missing(fake_gh: FakeGh) -> None:
    fake_gh.route(("label", "list"), lambda args: _json_ok([{"name": "bug"}]))
    fake_gh.route(("label", "create"), lambda args: FakeCompletedProcess(stdout=""))

    provider = GithubProvider("owner/repo")
    provider.ensure_labels(["bug", "priority/P1"])

    create_calls = [c for c in fake_gh.calls if c[:2] == ["label", "create"]]
    assert len(create_calls) == 1
    assert create_calls[0][2] == "priority/P1"


def test_ensure_labels_empty_is_noop(fake_gh: FakeGh) -> None:
    provider = GithubProvider("owner/repo")
    provider.ensure_labels([])
    assert fake_gh.calls == []


def test_ensure_milestone_creates_when_missing(fake_gh: FakeGh) -> None:
    fake_gh.route(
        ("api", "repos/owner/repo/milestones"),
        lambda args: _json_ok([]) if "-f" not in args else FakeCompletedProcess(stdout="{}"),
    )
    provider = GithubProvider("owner/repo")
    provider.ensure_milestone("v1.0")

    create_calls = [c for c in fake_gh.calls if "-f" in c]
    assert len(create_calls) == 1
    assert "title=v1.0" in create_calls[0]


def test_ensure_milestone_noop_when_present(fake_gh: FakeGh) -> None:
    fake_gh.route(
        ("api", "repos/owner/repo/milestones"),
        lambda args: _json_ok([{"title": "v1.0"}]),
    )
    provider = GithubProvider("owner/repo")
    provider.ensure_milestone("v1.0")

    create_calls = [c for c in fake_gh.calls if "-f" in c]
    assert create_calls == []


def test_run_raises_on_nonzero_exit(fake_gh: FakeGh) -> None:
    fake_gh.route(("issue", "list"), lambda args: FakeCompletedProcess(stderr="boom", returncode=1))
    provider = GithubProvider("owner/repo")
    with pytest.raises(RuntimeError, match="boom"):
        provider.list_issues()


def test_run_raises_clear_error_when_gh_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_not_found(*args: Any, **kwargs: Any) -> Any:
        raise FileNotFoundError("gh not found")

    monkeypatch.setattr(subprocess, "run", _raise_not_found)
    provider = GithubProvider("owner/repo")
    with pytest.raises(RuntimeError, match="'gh' CLI was not found"):
        provider.list_issues()
