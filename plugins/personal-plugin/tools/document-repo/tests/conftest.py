"""Shared fixtures: throwaway git repos built from a dict of files."""

from __future__ import annotations

import itertools
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

GIT = [
    "git",
    "-c",
    "user.name=test",
    "-c",
    "user.email=test@example.com",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "core.excludesFile=",
]
# Ignore the developer's global/system git config so rules like a global `archive/` ignore cannot
# drop files.
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(
        [*GIT, "-C", str(repo), *args], check=True, capture_output=True, text=True, env=GIT_ENV
    ).stdout


def _write(repo: Path, files: dict[str, str | bytes]) -> None:
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")


@pytest.fixture
def make_repo(tmp_path: Path) -> Callable[[dict[str, str | bytes]], Path]:
    counter = itertools.count(1)

    def _make(files: dict[str, str | bytes]) -> Path:
        n = next(counter)
        repo = tmp_path / ("repo" if n == 1 else f"repo{n}")
        repo.mkdir()
        run_git(repo, "init", "-q", "-b", "main")
        _write(repo, files)
        run_git(repo, "add", "-A")
        run_git(repo, "commit", "-q", "-m", "init")
        return repo

    return _make


@pytest.fixture
def git() -> Callable[..., str]:
    return run_git


@pytest.fixture
def commit_files(git: Callable[..., str]) -> Callable[[Path, dict[str, str | bytes], str], str]:
    def _commit(repo: Path, files: dict[str, str | bytes], message: str = "change") -> str:
        _write(repo, files)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message)
        return git(repo, "rev-parse", "HEAD").strip()

    return _commit
