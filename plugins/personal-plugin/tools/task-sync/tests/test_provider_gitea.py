"""Tests for the Gitea adapter, entirely mocking `urllib.request.urlopen`.

No live HTTP: every test installs a fake router keyed on (method, path
prefix) and returns recorded JSON, mirroring the Gitea REST API's actual
issue/label/milestone response shapes.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

import pytest

from task_sync.providers.gitea import GiteaProvider, load_gitea_credentials

_ISSUE_FIXTURE = {
    "number": 42,
    "title": "Fix the thing",
    "body": "Some body text",
    "state": "open",
    "updated_at": "2026-07-10T12:00:00Z",
    "closed_at": None,
    "labels": [{"id": 1, "name": "bug"}, {"id": 2, "name": "status/todo"}],
    "milestone": {"id": 5, "title": "v1.0"},
}

_CLOSED_ISSUE_FIXTURE = {
    "number": 43,
    "title": "Old bug",
    "body": "",
    "state": "closed",
    "updated_at": "2026-06-01T00:00:00Z",
    "closed_at": "2026-06-15T00:00:00Z",
    "labels": [],
    "milestone": None,
}


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._body = json.dumps(payload).encode("utf-8") if payload is not None else b""

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


class FakeUrlopen:
    """Routes fake `urllib.request.urlopen(request)` calls to canned responses."""

    def __init__(self) -> None:
        self.calls: list[urllib.request.Request] = []
        self.routes: dict[tuple[str, str], Callable[[urllib.request.Request], Any]] = {}

    def route(
        self, method: str, path_prefix: str, handler: Callable[[urllib.request.Request], Any]
    ) -> None:
        self.routes[(method, path_prefix)] = handler

    def __call__(
        self, request: urllib.request.Request, timeout: float | None = None
    ) -> FakeResponse:
        self.calls.append(request)
        full_url = request.full_url
        for (method, prefix), handler in self.routes.items():
            if request.get_method() == method and prefix in full_url:
                return FakeResponse(handler(request))
        raise AssertionError(f"no fake route for {request.get_method()} {full_url}")


@pytest.fixture
def fake_urlopen(monkeypatch: pytest.MonkeyPatch) -> FakeUrlopen:
    fake = FakeUrlopen()
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return fake


def _provider() -> GiteaProvider:
    return GiteaProvider("owner/repo", "https://git.example.com", "tok-123")


# -- list_issues / normalization ------------------------------------------


def test_list_issues_returns_normalized_issues(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/issues", lambda req: [_ISSUE_FIXTURE, _CLOSED_ISSUE_FIXTURE])

    provider = _provider()
    issues = provider.list_issues(state="all")

    assert len(issues) == 2
    assert issues[0].number == 42
    assert issues[0].body == "Some body text"
    assert issues[0].labels == ["bug", "status/todo"]
    assert issues[0].milestone == "v1.0"
    assert issues[0].updated_at.tzinfo is not None
    assert issues[1].state == "closed"
    assert issues[1].closed_at is not None


def test_list_issues_paginates_full_pages(fake_urlopen: FakeUrlopen) -> None:
    page_one = [{**_ISSUE_FIXTURE, "number": n} for n in range(1, 51)]  # exactly one page
    page_two = [{**_CLOSED_ISSUE_FIXTURE, "number": 51}]
    calls = {"n": 0}

    def _handler(req: urllib.request.Request) -> Any:
        calls["n"] += 1
        return page_one if calls["n"] == 1 else page_two

    fake_urlopen.route("GET", "/issues", _handler)

    provider = _provider()
    issues = provider.list_issues()

    assert len(issues) == 51
    assert calls["n"] == 2


def test_list_issues_empty(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/issues", lambda req: [])
    provider = _provider()
    assert provider.list_issues() == []


# -- create / update / set_state -----------------------------------------


def test_create_issue_resolves_label_and_milestone_ids(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/labels", lambda req: [{"id": 1, "name": "bug"}])
    fake_urlopen.route("POST", "/labels", lambda req: {"id": 2, "name": "status/todo"})
    fake_urlopen.route("GET", "/milestones", lambda req: [])
    fake_urlopen.route("POST", "/milestones", lambda req: {"id": 5, "title": "v1.0"})
    fake_urlopen.route("POST", "/issues", lambda req: _ISSUE_FIXTURE)

    provider = _provider()
    issue = provider.create_issue(
        "Fix the thing", "Some body text", labels=["bug", "status/todo"], milestone="v1.0"
    )

    assert issue.number == 42

    issue_post = next(
        c for c in fake_urlopen.calls if c.get_method() == "POST" and "/issues" in c.full_url
    )
    body = json.loads(issue_post.data)
    assert sorted(body["labels"]) == [1, 2]
    assert body["milestone"] == 5


def test_update_issue_sets_state_and_fields(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("PATCH", "/issues/42", lambda req: _ISSUE_FIXTURE)

    provider = _provider()
    issue = provider.update_issue(42, title="New title", state="closed")

    assert issue.number == 42
    patch_call = next(c for c in fake_urlopen.calls if c.get_method() == "PATCH")
    body = json.loads(patch_call.data)
    assert body["title"] == "New title"
    assert body["state"] == "closed"


def test_update_issue_clears_milestone(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("PATCH", "/issues/42", lambda req: _ISSUE_FIXTURE)
    provider = _provider()
    provider.update_issue(42, milestone=None)

    patch_call = next(c for c in fake_urlopen.calls if c.get_method() == "PATCH")
    body = json.loads(patch_call.data)
    assert body["milestone"] == 0


def test_set_state_patches_issue(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("PATCH", "/issues/42", lambda req: _ISSUE_FIXTURE)
    provider = _provider()
    provider.set_state(42, "closed")

    patch_call = next(c for c in fake_urlopen.calls if c.get_method() == "PATCH")
    assert json.loads(patch_call.data) == {"state": "closed"}


def test_set_state_invalid_raises(fake_urlopen: FakeUrlopen) -> None:
    provider = _provider()
    with pytest.raises(ValueError, match="invalid state"):
        provider.set_state(42, "merged")


# -- ensure_labels / ensure_milestone --------------------------------------


def test_ensure_labels_creates_only_missing(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/labels", lambda req: [{"id": 1, "name": "bug"}])
    created = []

    def _create_label(req: urllib.request.Request) -> Any:
        body = json.loads(req.data)
        created.append(body)
        return {"id": 9, **body}

    fake_urlopen.route("POST", "/labels", _create_label)

    provider = _provider()
    provider.ensure_labels(["bug", "priority/P1"])

    assert len(created) == 1
    assert created[0]["name"] == "priority/P1"


def test_ensure_labels_empty_is_noop(fake_urlopen: FakeUrlopen) -> None:
    provider = _provider()
    provider.ensure_labels([])
    assert fake_urlopen.calls == []


def test_ensure_milestone_creates_when_missing(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/milestones", lambda req: [])
    created = []

    def _create_milestone(req: urllib.request.Request) -> Any:
        body = json.loads(req.data)
        created.append(body)
        return {"id": 5, **body}

    fake_urlopen.route("POST", "/milestones", _create_milestone)

    provider = _provider()
    provider.ensure_milestone("v1.0")

    assert created == [{"title": "v1.0"}]


def test_ensure_milestone_noop_when_present(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/milestones", lambda req: [{"id": 5, "title": "v1.0"}])
    provider = _provider()
    provider.ensure_milestone("v1.0")
    assert all(c.get_method() != "POST" for c in fake_urlopen.calls)


# -- visibility -------------------------------------------------------------


def test_visibility_private(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/repos/owner/repo", lambda req: {"private": True})
    provider = _provider()
    assert provider.visibility() == "private"


def test_visibility_public(fake_urlopen: FakeUrlopen) -> None:
    fake_urlopen.route("GET", "/repos/owner/repo", lambda req: {"private": False})
    provider = _provider()
    assert provider.visibility() == "public"


# -- HTTP error handling ----------------------------------------------------


def test_http_error_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(request: urllib.request.Request, timeout: float | None = None) -> Any:
        raise urllib.error.HTTPError(
            request.full_url, 404, "Not Found", hdrs=None, fp=io.BytesIO(b"missing")
        )

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    provider = _provider()
    with pytest.raises(RuntimeError, match="404"):
        provider.list_issues()


def test_url_error_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(request: urllib.request.Request, timeout: float | None = None) -> Any:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    provider = _provider()
    with pytest.raises(RuntimeError, match="connection refused"):
        provider.list_issues()


def test_invalid_repo_slug_raises() -> None:
    with pytest.raises(ValueError, match="owner/repo"):
        GiteaProvider("not-a-slug", "https://git.example.com", "tok")


# -- tea config parsing / credential loading -------------------------------


_TEA_CONFIG = """\
logins:
- name: mygitea
  url: https://git.example.com
  token: abc123
  default: true
- name: other
  url: https://git.other.example.com
  token: def456
  default: false
"""


def test_load_gitea_credentials_reads_default_login(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text(_TEA_CONFIG, encoding="utf-8")

    base_url, token = load_gitea_credentials(config_path)

    assert base_url == "https://git.example.com"
    assert token == "abc123"


def test_load_gitea_credentials_falls_back_to_first_login(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "logins:\n- name: only\n  url: https://git.example.com\n  token: xyz\n",
        encoding="utf-8",
    )

    base_url, token = load_gitea_credentials(config_path)
    assert base_url == "https://git.example.com"
    assert token == "xyz"


def test_load_gitea_credentials_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="tea login add"):
        load_gitea_credentials(tmp_path / "does-not-exist.yml")


def test_load_gitea_credentials_no_logins_raises(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text("logins:\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="tea login add"):
        load_gitea_credentials(config_path)


def test_load_gitea_credentials_missing_token_raises(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "logins:\n- name: mygitea\n  url: https://git.example.com\n  default: true\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="tea login add"):
        load_gitea_credentials(config_path)


def test_from_tea_config_builds_provider(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text(_TEA_CONFIG, encoding="utf-8")

    provider = GiteaProvider.from_tea_config("owner/repo", config_path)

    assert provider._base_url == "https://git.example.com"
    assert provider._token == "abc123"
