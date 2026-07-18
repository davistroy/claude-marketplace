"""Tests for git-remote-based provider detection, mocking `subprocess.run`."""

from __future__ import annotations

import subprocess
from typing import Any

import pytest

from task_sync.detect import detect_provider


class _FakeCompletedProcess:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""


def _mock_remote(monkeypatch: pytest.MonkeyPatch, stdout: str, returncode: int = 0) -> None:
    def _fake_run(args: list[str], **kwargs: Any) -> _FakeCompletedProcess:
        assert args[:4] == ["git", "-C", "/repo", "remote"]
        return _FakeCompletedProcess(stdout=stdout, returncode=returncode)

    monkeypatch.setattr(subprocess, "run", _fake_run)


@pytest.mark.parametrize(
    "url",
    [
        "git@github.com:owner/repo.git",
        "https://github.com/owner/repo.git",
        "https://github.com/owner/repo",
        "ssh://git@github.com/owner/repo.git",
    ],
)
def test_github_ssh_and_https_forms(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    _mock_remote(monkeypatch, url + "\n")
    provider, repo = detect_provider("/repo")
    assert provider == "github"
    assert repo == "owner/repo"


@pytest.mark.parametrize(
    "url",
    [
        "git@git.example.com:owner/repo.git",
        "https://git.example.com/owner/repo.git",
        "https://git.example.com:3000/owner/repo.git",
        "ssh://git@git.example.com:2222/owner/repo.git",
    ],
)
def test_gitea_ssh_and_https_forms(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    _mock_remote(monkeypatch, url + "\n")
    provider, repo = detect_provider("/repo")
    assert provider == "gitea"
    assert repo == "owner/repo"


def test_no_remote_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_remote(monkeypatch, "", returncode=128)
    provider, repo = detect_provider("/repo")
    assert (provider, repo) == ("none", None)


def test_empty_stdout_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_remote(monkeypatch, "")
    provider, repo = detect_provider("/repo")
    assert (provider, repo) == ("none", None)


def test_unparseable_url_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_remote(monkeypatch, "not-a-url\n")
    provider, repo = detect_provider("/repo")
    assert (provider, repo) == ("none", None)


def test_git_not_installed_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args: Any, **kwargs: Any) -> Any:
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "run", _raise)
    provider, repo = detect_provider("/repo")
    assert (provider, repo) == ("none", None)
