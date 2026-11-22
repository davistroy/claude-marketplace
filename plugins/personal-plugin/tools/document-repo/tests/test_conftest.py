from collections.abc import Callable
from pathlib import Path


def test_make_repo_tracks_archive_dir(make_repo: Callable[[dict[str, str | bytes]], Path], git: Callable[..., str]) -> None:
    repo = make_repo({"archive/x.py": "print('x')\n"})
    assert repo.name == "repo"
    assert "archive/x.py" in git(repo, "ls-files").splitlines()


def test_make_repo_gives_unique_dirs(make_repo: Callable[[dict[str, str | bytes]], Path]) -> None:
    first = make_repo({"a.txt": "a"})
    second = make_repo({"b.txt": "b"})
    assert first != second
    assert second.name == "repo2"
