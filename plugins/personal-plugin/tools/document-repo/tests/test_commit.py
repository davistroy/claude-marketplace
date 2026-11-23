"""``document_repo commit`` and ``backstop``: every failure path, in real throwaway repos.

The cases named S*, F* and B* are the probes from the task-13 re-review that the old hand-filled
shell block failed or mishandled. Each one now has a test here.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import document_repo.commit as commit_mod
from document_repo.cli import main

M = "x = 1\n"
M_COMMENTED = "# Why: x is the answer.\nx = 1\n"
M_CHANGED = "x = 2\n"
N = "y = 1\n"
N_COMMENTED = "# Why: y.\ny = 1\n"


@pytest.fixture(autouse=True)
def _git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """The tool runs plain ``git``: give it an identity and no global or system config."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "test")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "test@example.com")


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, dict[str, Any]]:
    code = main(list(argv))
    cap = capsys.readouterr()
    result = json.loads(cap.out) if cap.out.strip() else {}
    result["_err"] = cap.err
    return code, result


def commit(
    capsys: pytest.CaptureFixture[str],
    repo: Path,
    *files: str,
    ref: str | None = "HEAD",
    msg: str = "docs(m): add comments",
    extra: tuple[str, ...] = (),
) -> tuple[int, dict[str, Any]]:
    mode = ["--verify-against", ref] if ref is not None else ["--no-content-check"]
    return run(capsys, "commit", "--repo", str(repo), *mode, "-m", msg, *extra, "--", *files)


def head(git: Callable[..., str], repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


def hook(repo: Path, name: str, body: str) -> None:
    path = repo / ".git" / "hooks" / name
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def staged(git: Callable[..., str], repo: Path) -> str:
    return git(repo, "diff", "--cached", "--name-only")


# --- success -------------------------------------------------------------------------------------


def test_comment_commit_ok(make_repo, git, capsys) -> None:
    repo = make_repo({"a/m.py": M, "a/n.py": N})
    pre = head(git, repo)
    (repo / "a/m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "a/m.py", "a/n.py", msg="subject", extra=("-m", "body"))
    assert code == 0 and out["status"] == "ok", out
    assert out["paths"] == ["a/m.py"] and out["sha"] == head(git, repo)
    assert git(repo, "rev-parse", "HEAD~1").strip() == pre
    assert git(repo, "log", "-1", "--format=%B").strip() == "subject\n\nbody"
    assert git(repo, "status", "--porcelain") == ""


def test_path_with_spaces_s1b(make_repo, git, capsys) -> None:
    repo = make_repo({"a/my file.py": M, "a/m.py": N})
    (repo / "a/my file.py").write_text(M_COMMENTED)
    (repo / "a/m.py").write_text(N_COMMENTED)
    code, out = commit(capsys, repo, "a/my file.py", "a/m.py")
    assert code == 0, out
    assert out["paths"] == ["a/m.py", "a/my file.py"]


def test_glob_characters_are_literal(make_repo, capsys) -> None:
    repo = make_repo({"a/[x].py": M, "a/x.py": N})
    (repo / "a/[x].py").write_text(M_COMMENTED)
    (repo / "a/x.py").write_text(N_COMMENTED)
    code, out = commit(capsys, repo, "a/[x].py")
    assert code == 0 and out["paths"] == ["a/[x].py"], out


def test_absolute_path_inside_repo(make_repo, capsys) -> None:
    repo = make_repo({"m.py": M})
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, str(repo / "m.py"))
    assert code == 0 and out["paths"] == ["m.py"], out


def test_deletion_without_content_check(make_repo, git, capsys) -> None:
    repo = make_repo({"docs/old.md": "x\n", "keep.md": "k\n"})
    (repo / "docs/old.md").unlink()
    code, out = commit(capsys, repo, "docs/old.md", ref=None)
    assert code == 0 and out["paths"] == ["docs/old.md"], out
    assert git(repo, "ls-files", "docs") == ""


def test_deletion_with_content_check_is_a_precheck_failure(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    (repo / "m.py").unlink()
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "precheck", out
    assert head(git, repo) == pre and staged(git, repo) == ""


def test_directory_with_new_files(make_repo, capsys) -> None:
    repo = make_repo({"src.py": M})
    (repo / "explorer/data").mkdir(parents=True)
    (repo / "explorer/index.html").write_text("<p>hi</p>\n")
    (repo / "explorer/data/model.json").write_text("{}\n")
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 0, out
    assert out["paths"] == ["explorer/data/model.json", "explorer/index.html"]


def test_foreign_index_entry_is_left_out(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M, "other.py": N})
    (repo / "m.py").write_text(M_COMMENTED)
    (repo / "other.py").write_text(M_CHANGED)
    git(repo, "add", "other.py")
    code, out = commit(capsys, repo, "m.py")
    assert code == 0 and out["paths"] == ["m.py"], out
    assert (repo / "other.py").read_text() == M_CHANGED
    assert staged(git, repo) == ""


def test_message_is_never_shell_evaluated_f4(make_repo, git, capsys, tmp_path) -> None:
    repo = make_repo({"m.py": M})
    (repo / "m.py").write_text(M_COMMENTED)
    msg = f"broke `touch {tmp_path}/PWNED` $(touch {tmp_path}/PWNED2) $HOME"
    code, _ = commit(capsys, repo, "m.py", msg=msg)
    assert code == 0
    assert git(repo, "log", "-1", "--format=%s").strip() == msg
    assert not (tmp_path / "PWNED").exists() and not (tmp_path / "PWNED2").exists()


def test_skip_when_nothing_differs(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    code, out = commit(capsys, repo, "m.py")
    assert code == 0 and out["status"] == "skip"
    assert head(git, repo) == pre


def test_restore_commit_against_base(make_repo, git, commit_files, capsys) -> None:
    repo = make_repo({"m.py": M})
    base = head(git, repo)
    commit_files(repo, {"m.py": M_COMMENTED}, "comments")
    git(repo, "checkout", base, "--", "m.py")
    git(repo, "reset", "-q")
    code, out = commit(capsys, repo, "m.py", ref=base, msg="revert(m): remove comments")
    assert code == 0, out
    assert git(repo, "diff", base, "HEAD") == ""


def test_untracked_symlink_stray_is_hashed(make_repo, capsys) -> None:
    repo = make_repo({"m.py": M})
    (repo / "m.py").write_text(M_COMMENTED)
    (repo / "link").symlink_to("m.py")
    code, out = commit(capsys, repo, "m.py")
    assert code == 0 and out["strays"] == [], out


# --- bad input: exit 2, nothing touched -----------------------------------------------------------


@pytest.mark.parametrize(
    ("files", "why"),
    [
        ((), "no paths"),
        (("nope.py",), "does not exist"),
        (("<path>",), "does not exist"),
        (("",), "empty path"),
        (("../x.py",), "outside"),
        (("/etc/hosts",), "outside"),
        ((".",), "whole repository"),
        ((".git/config",), "inside .git"),
    ],
)
def test_bad_paths_exit_2(make_repo, git, capsys, files, why) -> None:
    repo = make_repo({"m.py": M})
    (repo / "m.py").write_text(M_COMMENTED)
    git(repo, "add", "m.py")
    code = main(
        ["commit", "--repo", str(repo), "--verify-against", "HEAD", "-m", "s", "--", *files]
    )
    err = capsys.readouterr().err
    assert code == 2 and why in err, err
    assert staged(git, repo) == "m.py\n", "bad input must not touch the index"


def test_ignored_file_exit_2(make_repo, capsys) -> None:
    repo = make_repo({".gitignore": "*.log\n", "m.py": M})
    (repo / "x.log").write_text("log\n")
    code, out = commit(capsys, repo, "x.log", ref=None)
    assert code == 2 and "ignored" in out["_err"]


def test_symlinked_parent_outside_repo_exit_2(make_repo, tmp_path, capsys) -> None:
    repo = make_repo({"m.py": M})
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "f.py").write_text(M)
    (repo / "out").symlink_to(outside)
    code, out = commit(capsys, repo, "out/f.py", ref=None)
    assert code == 2 and "resolves outside" in out["_err"]


def test_subdirectory_repo_exit_2(make_repo, capsys) -> None:
    repo = make_repo({"a/m.py": M})
    code, out = commit(capsys, repo / "a", "m.py")
    assert code == 2 and "top level" in out["_err"]


def test_not_a_repo_exit_2(tmp_path, capsys) -> None:
    code, out = commit(capsys, tmp_path, "m.py")
    assert code == 2 and "not inside a git work tree" in out["_err"]


def test_wrong_repo_f1(make_repo, git, capsys, monkeypatch) -> None:
    """The old block's ``cd ""`` stayed in the cwd and committed there. Now --repo is explicit."""
    target = make_repo({"m.py": M})
    other = make_repo({"m.py": M})
    (target / "m.py").write_text(M_COMMENTED)
    (other / "m.py").write_text(M_COMMENTED)
    other_head = head(git, other)
    monkeypatch.chdir(other)
    code, _ = commit(capsys, target, "m.py")
    assert code == 0
    assert head(git, other) == other_head and (other / "m.py").read_text() == M_COMMENTED
    with pytest.raises(SystemExit) as exc:
        main(["commit", "--repo", "", "--verify-against", "HEAD", "-m", "s", "--", "m.py"])
    assert exc.value.code == 2, "an empty --repo is refused, not read as the cwd"
    assert head(git, other) == other_head


def test_backstop_empty_repo_refused(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["backstop", "--repo", " ", "--base", "HEAD"])
    assert exc.value.code == 2


@pytest.mark.parametrize("ref", ["", "  ", "no-such-ref", "/base.txt"])
def test_bad_verify_ref_exit_2_f2_f3(make_repo, git, capsys, ref) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    (repo / "m.py").write_text(M_CHANGED)
    code, _ = commit(capsys, repo, "m.py", ref=ref)
    assert code == 2
    assert head(git, repo) == pre


def test_mode_is_required(make_repo, capsys) -> None:
    repo = make_repo({"m.py": M})
    with pytest.raises(SystemExit) as exc:
        main(["commit", "--repo", str(repo), "-m", "s", "--", "m.py"])
    assert exc.value.code == 2


def test_modes_are_exclusive(make_repo, capsys) -> None:
    repo = make_repo({"m.py": M})
    with pytest.raises(SystemExit) as exc:
        main(
            ["commit", "--repo", str(repo), "--verify-against", "HEAD", "--no-content-check"]
            + ["-m", "s", "--", "m.py"]
        )
    assert exc.value.code == 2


def test_empty_message_exit_2(make_repo, capsys) -> None:
    repo = make_repo({"m.py": M})
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py", msg=" ")
    assert code == 2 and "message is empty" in out["_err"]


def test_repo_without_commits_exit_2(tmp_path, git, capsys) -> None:
    git(tmp_path, "init", "-q")
    (tmp_path / "m.py").write_text(M)
    code, out = commit(capsys, tmp_path, "m.py", ref=None)
    assert code == 2 and "HEAD" in out["_err"]


def test_git_error_is_exit_2(make_repo, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise commit_mod.GitError("git add failed: disk full")

    monkeypatch.setattr(commit_mod, "commit_paths", boom)
    code, out = commit(capsys, repo, "m.py")
    assert code == 2 and out["status"] == "error"


# --- precheck ------------------------------------------------------------------------------------


def test_precheck_rejects_code_change(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M, "n.py": N})
    pre = head(git, repo)
    (repo / "m.py").write_text(M_CHANGED)
    (repo / "n.py").write_text(N_COMMENTED)
    code, out = commit(capsys, repo, "m.py", "n.py")
    assert code == 1 and out["status"] == "precheck"
    assert [r["path"] for r in out["verify"]] == ["m.py"]
    assert head(git, repo) == pre and staged(git, repo) == ""
    assert (repo / "m.py").read_text() == M_CHANGED, "the caller decides what to restore"


# --- hooks and post-commit checks ----------------------------------------------------------------


def test_hook_rewrites_and_restages_is_undone(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "pre-commit", "printf 'x = 9\\n' > m.py\ngit add m.py\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "undone", out
    assert "not comment-only" in out["detail"]
    assert head(git, repo) == pre and staged(git, repo) == ""
    assert (repo / "m.py").read_text() == M, "restored to the old HEAD"
    assert out["restored"] == ["m.py"]


def test_hook_rewrites_without_staging_is_undone(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "pre-commit", "printf '# hook\\nx = 1\\n' > m.py\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "undone"
    assert "work tree differs" in out["detail"]
    assert head(git, repo) == pre and (repo / "m.py").read_text() == M


def test_hook_adds_a_file_is_undone(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "pre-commit", "echo extra > extra.txt\ngit add extra.txt\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "undone"
    assert "extra.txt" in out["detail"]
    assert head(git, repo) == pre and staged(git, repo) == ""
    assert "extra.txt" in out["strays"]


def test_hook_adds_a_file_docs_commit_keeps_the_work(make_repo, git, capsys) -> None:
    repo = make_repo({"README.md": "old\n"})
    pre = head(git, repo)
    hook(repo, "pre-commit", "echo extra > extra.txt\ngit add extra.txt\n")
    (repo / "README.md").write_text("new docs\n")
    code, out = commit(capsys, repo, "README.md", ref=None)
    assert code == 1 and out["status"] == "undone"
    assert head(git, repo) == pre
    assert (repo / "README.md").read_text() == "new docs\n", "docs work kept"


def test_hook_rewrites_docs_without_staging_restores_staged_bytes(make_repo, git, capsys) -> None:
    repo = make_repo({"README.md": "old\n"})
    hook(repo, "pre-commit", "printf 'hooked\\n' > README.md\necho junk > explorer/x.txt\n")
    (repo / "explorer").mkdir()
    (repo / "explorer/a.html").write_text("a\n")
    (repo / "README.md").write_text("new docs\n")
    code, out = commit(capsys, repo, "README.md", "explorer", ref=None)
    assert code == 1 and out["status"] == "undone", out
    assert (repo / "README.md").read_text() == "new docs\n"
    assert not (repo / "explorer/x.txt").exists(), "a file the hook made under the list is removed"
    assert (repo / "explorer/a.html").read_text() == "a\n"


def test_hook_edits_another_modules_file_s4(make_repo, git, capsys) -> None:
    repo = make_repo({"a/m.py": M, "b/n.py": N})
    hook(repo, "pre-commit", "printf 'y = 5\\n' > b/n.py\n")
    (repo / "a/m.py").write_text(M_COMMENTED)
    (repo / "b/n.py").write_text(N_COMMENTED)
    code, out = commit(capsys, repo, "a/m.py")
    assert code == 0 and out["status"] == "ok"
    assert out["strays"] == ["b/n.py"], "the damage to another module is reported"
    code, out = commit(capsys, repo, "b/n.py", extra=("--skip-hooks",))
    assert code == 1 and out["status"] == "precheck", "and that module's own commit refuses it"


def test_hook_exits_nonzero(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "pre-commit", "echo 'lint failed' >&2\nexit 1\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "commit-failed"
    assert "pre-commit" in out["detail"] and "lint failed" in out["git_output"]
    assert head(git, repo) == pre and staged(git, repo) == ""
    assert (repo / "m.py").read_text() == M_COMMENTED and out["restored"] == []


def test_hook_fixes_then_fails_s3_minor2(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": 'S = "a"\n'})
    hook(repo, "pre-commit", "printf 'S = \"b\"\\n' > m.py\nexit 1\n")
    (repo / "m.py").write_text('# Why.\nS = "a"\n')
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "commit-failed"
    assert out["restored"] == ["m.py"]
    assert (repo / "m.py").read_text() == '# Why.\nS = "a"\n', "the verified bytes are back"


def test_skip_hooks_bypasses_hook(make_repo, capsys) -> None:
    repo = make_repo({"m.py": M})
    hook(repo, "pre-commit", "exit 1\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py", extra=("--skip-hooks",))
    assert code == 0 and out["status"] == "ok"


def test_signing_failure_is_not_called_a_hook_minor3(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    git(repo, "config", "commit.gpgsign", "true")
    git(repo, "config", "gpg.program", "false")
    hook(repo, "pre-commit", "exit 0\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "commit-failed"
    assert "sign" in out["detail"] and "hooks ran" not in out["detail"], out


def test_commit_failure_without_hooks_message(make_repo) -> None:
    repo = make_repo({"m.py": M})
    assert "no commit hook ran" in commit_mod._commit_failure(repo, "fatal: x", skip_hooks=True)


def test_commit_failure_with_absolute_hooks_path(make_repo, git, tmp_path) -> None:
    repo = make_repo({"m.py": M})
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "commit-msg").write_text("#!/bin/sh\nexit 1\n")
    (hooks / "commit-msg").chmod(0o755)
    git(repo, "config", "core.hooksPath", str(hooks))
    assert "commit-msg" in commit_mod._commit_failure(repo, "x", skip_hooks=False)


def test_undo_keeps_other_modules_edits(make_repo, git, capsys) -> None:
    repo = make_repo({"a/m.py": M, "b/n.py": N, "c/new_dir_keep.py": N})
    pre = head(git, repo)
    hook(repo, "pre-commit", "printf 'x = 9\\n' > a/m.py\ngit add a/m.py\n")
    (repo / "a/m.py").write_text(M_COMMENTED)
    (repo / "b/n.py").write_text(N_COMMENTED)
    (repo / "c/untracked.py").write_text("z = 1\n")
    code, out = commit(capsys, repo, "a/m.py")
    assert code == 1 and out["status"] == "undone"
    assert head(git, repo) == pre
    assert (repo / "b/n.py").read_text() == N_COMMENTED
    assert (repo / "c/untracked.py").read_text() == "z = 1\n"
    assert out["strays"] == []


def test_undo_of_restore_commit_for_a_deleted_file_b4_minor5(
    make_repo, git, commit_files, capsys
) -> None:
    repo = make_repo({"m.py": M, "keep.py": N})
    base = head(git, repo)
    git(repo, "rm", "-q", "m.py")
    git(repo, "commit", "-q", "-m", "delete m.py")
    pre = head(git, repo)
    git(repo, "checkout", base, "--", "m.py")
    git(repo, "reset", "-q")
    hook(repo, "pre-commit", "printf 'x = 9\\n' > m.py\ngit add m.py\n")
    code, out = commit(capsys, repo, "m.py", ref=base)
    assert code == 1 and out["status"] == "undone", out
    assert head(git, repo) == pre
    assert not (repo / "m.py").exists(), "restored to the old HEAD, which lacks the file"
    assert git(repo, "status", "--porcelain") == ""


def test_undo_restore_failure_is_stop(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})
    hook(repo, "pre-commit", "printf 'x = 9\\n' > m.py\ngit add m.py\n")
    (repo / "m.py").write_text(M_COMMENTED)

    def fail(*args: Any) -> list[str]:
        raise commit_mod.GitError("could not restore m.py")

    monkeypatch.setattr(commit_mod, "_restore", fail)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop" and "could not restore" in out["detail"]


def test_restore_reports_what_it_cannot_fix(make_repo, git, monkeypatch) -> None:
    repo = make_repo({"m.py": M})
    (repo / "m.py").write_text(M_CHANGED)
    monkeypatch.setattr(commit_mod, "_differs", lambda *a: ["m.py"])
    with pytest.raises(commit_mod.GitError, match="could not restore"):
        commit_mod._restore(repo, head(git, repo), ["m.py"])


GUARD = '[ -n "$INNER" ] && exit 0\nexport INNER=1\n'


def test_hook_makes_its_own_commit_is_stop(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    hook(repo, "post-commit", GUARD + "git commit -q --allow-empty --no-verify -m sneaky\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop"
    assert git(repo, "log", "-1", "--format=%s").strip() == "sneaky", "history was not touched"


def test_failed_commit_that_moved_head_is_stop(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    hook(repo, "pre-commit", GUARD + "git commit -q --allow-empty --no-verify -m sneaky\nexit 1\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop" and "HEAD moved" in out["detail"]


# --- backstop ------------------------------------------------------------------------------------


def test_backstop_ok(make_repo, git, commit_files, capsys) -> None:
    repo = make_repo({"m.py": M})
    base = head(git, repo)
    commit_files(repo, {"m.py": M_COMMENTED, "README.md": "docs\n"}, "docs")
    code, out = run(capsys, "backstop", "--repo", str(repo), "--base", base)
    assert code == 0 and out["ok"] and out["status"] == []
    assert [r["path"] for r in out["verify"]] == ["m.py"]


def test_backstop_catches_code_change(make_repo, git, commit_files, capsys) -> None:
    repo = make_repo({"m.py": M})
    base = head(git, repo)
    commit_files(repo, {"m.py": M_CHANGED}, "oops")
    code, out = run(capsys, "backstop", "--repo", str(repo), "--base", base)
    assert code == 1 and not out["ok"]


def test_backstop_catches_dirty_tree(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    (repo / "stray.md").write_text("x\n")
    code, out = run(capsys, "backstop", "--repo", str(repo), "--base", head(git, repo))
    assert code == 1 and out["status"] == ["?? stray.md"]


@pytest.mark.parametrize(("base", "why"), [("", "empty"), ("nope", "does not name")])
def test_backstop_bad_base_minor6(make_repo, capsys, base, why) -> None:
    repo = make_repo({"m.py": M})
    code, out = run(capsys, "backstop", "--repo", str(repo), "--base", base)
    assert code == 2 and why in out["_err"]


def test_backstop_base_not_ancestor(make_repo, git, commit_files, capsys) -> None:
    repo = make_repo({"m.py": M})
    git(repo, "switch", "-q", "-c", "side")
    side = commit_files(repo, {"s.py": N}, "side")
    git(repo, "switch", "-q", "main")
    code, out = run(capsys, "backstop", "--repo", str(repo), "--base", side)
    assert code == 2 and "ancestor" in out["_err"]


def test_backstop_subdirectory_exit_2(make_repo, git, capsys) -> None:
    repo = make_repo({"a/m.py": M})
    code, _ = run(capsys, "backstop", "--repo", str(repo / "a"), "--base", "HEAD")
    assert code == 2


def test_backstop_runs_as_module(make_repo, git) -> None:
    repo = make_repo({"m.py": M})
    src = Path(__file__).resolve().parents[1] / "src"
    proc = subprocess.run(
        ["python3", "-m", "document_repo", "backstop", "--repo", str(repo), "--base", ""],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(src)},
    )
    assert proc.returncode == 2 and "Traceback" not in proc.stderr


# --- verify --changed with a bad ref (review-2 Minor 6) ------------------------------------------


@pytest.mark.parametrize(("ref", "why"), [("", "empty"), ("nope", "cannot list changes")])
def test_verify_changed_bad_ref_exit_2(make_repo, capsys, ref, why) -> None:
    repo = make_repo({"m.py": M})
    code = main(["verify", "--repo", str(repo), "--before", ref, "--changed"])
    assert code == 2 and why in capsys.readouterr().err


def test_git_failures_raise_git_error(make_repo) -> None:
    repo = make_repo({"m.py": M})
    with pytest.raises(commit_mod.GitError, match="rev-parse"):
        commit_mod._out(repo, "rev-parse", "--verify", "no-such-ref")
    with pytest.raises(commit_mod.GitError, match="read-tree"):
        commit_mod._differs(repo, "no-such-tree", ["m.py"])


def test_hook_deleting_another_file_is_a_stray(make_repo, capsys) -> None:
    repo = make_repo({"m.py": M, "other.py": N})
    hook(repo, "pre-commit", "rm other.py\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 0 and out["strays"] == ["other.py"], out


# --- task-13b review fixes -----------------------------------------------------------------------


def test_no_content_check_refuses_source_edit_i1(make_repo, git, capsys) -> None:
    repo = make_repo({"a/m.py": M, "b/n.py": N})
    pre = head(git, repo)
    (repo / "a/m.py").write_text("x = 999\n")
    (repo / "b/n.py").write_text(N_COMMENTED)
    git(repo, "add", "b/n.py")
    code, out = commit(capsys, repo, "a/m.py", ref=None)
    assert code == 2 and "a/m.py" in out["_err"] and "--no-content-check" in out["_err"], out
    assert head(git, repo) == pre
    assert staged(git, repo) == "b/n.py\n", "refused before the index is touched"


def test_no_content_check_refuses_rename_i1(make_repo, git, capsys) -> None:
    repo = make_repo({"a/m.py": M})
    pre = head(git, repo)
    git(repo, "mv", "a/m.py", "a/k.py")
    code, out = commit(capsys, repo, "a/m.py", "a/k.py", ref=None)
    assert code == 2 and "a/k.py" in out["_err"], out
    assert head(git, repo) == pre


def test_no_content_check_refuses_gitlink_i1(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    sub = repo / "sub"
    sub.mkdir()
    git(sub, "init", "-q", "-b", "main")
    (sub / "s.txt").write_text("1\n")
    git(sub, "add", "s.txt")
    git(sub, "commit", "-q", "-m", "one")
    git(repo, "add", "sub")
    git(repo, "commit", "-q", "-m", "add gitlink")
    pre = head(git, repo)
    (sub / "s.txt").write_text("2\n")
    git(sub, "commit", "-q", "-am", "two")
    code, out = commit(capsys, repo, "sub", ref=None)
    assert code == 2 and "sub" in out["_err"], out
    assert head(git, repo) == pre


def test_no_content_check_ok_detail_says_not_checked_i1(make_repo, capsys) -> None:
    repo = make_repo({"README.md": "old\n"})
    (repo / "README.md").write_text("new\n")
    code, out = commit(capsys, repo, "README.md", ref=None)
    assert code == 0 and out["status"] == "ok"
    assert out["detail"] == "committed (content not checked: docs only)"


def test_no_content_check_hook_adds_source_under_listed_dir_is_undone_i1(
    make_repo, git, capsys
) -> None:
    repo = make_repo({"docs/a.md": "old\n"})
    pre = head(git, repo)
    hook(repo, "pre-commit", "printf 'x = 1\\n' > docs/x.py\ngit add docs/x.py\n")
    (repo / "docs/a.md").write_text("new\n")
    code, out = commit(capsys, repo, "docs", ref=None)
    assert code == 1 and out["status"] == "undone", out
    assert "docs/x.py" in out["detail"]
    assert head(git, repo) == pre
    assert not (repo / "docs/x.py").exists() and (repo / "docs/a.md").read_text() == "new\n"


def test_corrupt_index_after_commit_is_stop_i2(make_repo, git, capsys) -> None:
    """The reviewer's r/gx: HEAD held x = 9 and the result was exit 2, status error."""
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "pre-commit", "printf 'x = 9\\n' > m.py\ngit add m.py\n")
    hook(repo, "post-commit", ": > .git/index\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop", out
    assert out["pre"] == pre and out["sha"] and "after git commit ran" in out["detail"]


def test_exception_after_commit_is_stop_and_undone_i2(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M, "other.py": N})
    pre = head(git, repo)
    (repo / "m.py").write_text(M_COMMENTED)
    (repo / "other.py").write_text(N_COMMENTED)
    real = commit_mod.verify_file
    calls: list[str] = []

    def flaky(*args: Any, **kwargs: Any) -> Any:
        calls.append(args[1])
        if len(calls) > 1:
            raise KeyboardInterrupt("killed by the Bash timeout")
        return real(*args, **kwargs)

    monkeypatch.setattr(commit_mod, "verify_file", flaky)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop", out
    assert "killed by the Bash timeout" in out["detail"] and "undone" in out["detail"]
    assert out["pre"] == pre and out["sha"] != pre
    assert head(git, repo) == pre and staged(git, repo) == ""
    assert (repo / "m.py").read_text() == M, "with a ref the change is dropped"
    assert (repo / "other.py").read_text() == N_COMMENTED


def test_exception_after_failed_commit_is_stop_i2(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "pre-commit", "exit 1\n")
    (repo / "m.py").write_text(M_COMMENTED)

    def boom(*args: Any) -> list[str]:
        raise OSError("disk full")

    monkeypatch.setattr(commit_mod, "_restore", boom)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop" and "disk full" in out["detail"], out
    assert head(git, repo) == pre and out["pre"] == pre


def test_undo_failure_in_emergency_is_reported_i2(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})
    (repo / "m.py").write_text(M_COMMENTED)
    calls: list[str] = []
    real = commit_mod.verify_file

    def flaky(*args: Any, **kwargs: Any) -> Any:
        calls.append(args[1])
        if len(calls) > 1:
            raise RuntimeError("verifier crashed")
        return real(*args, **kwargs)

    def stuck(*args: Any) -> list[str]:
        raise commit_mod.GitError("could not restore m.py")

    monkeypatch.setattr(commit_mod, "verify_file", flaky)
    monkeypatch.setattr(commit_mod, "_restore", stuck)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop", out
    assert "verifier crashed" in out["detail"] and "could not restore" in out["detail"]


def test_error_before_commit_is_exit_2_status_error_i2(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    (repo / "m.py").write_text(M_COMMENTED)

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("verifier crashed")

    monkeypatch.setattr(commit_mod, "verify_file", boom)
    code, out = commit(capsys, repo, "m.py")
    assert code == 2 and out["status"] == "error" and "nothing was committed" in out["detail"]
    assert head(git, repo) == pre


def test_emit_non_utf8_text_minor1(capsysbinary) -> None:
    from document_repo.cli import emit

    emit({"p": os.fsdecode(b"\xff.md")})
    assert b'"\xff.md"' in capsysbinary.readouterr().out


def test_emit_non_utf8_text_to_file_minor1(tmp_path) -> None:
    from document_repo.cli import emit

    emit({"p": os.fsdecode(b"\xff.md")}, tmp_path / "o.json")
    assert b'"\xff.md"' in (tmp_path / "o.json").read_bytes()


def test_non_utf8_path_deletion_reports_json_minor1(make_repo, git, capsysbinary) -> None:
    repo = make_repo({"keep.md": "k\n"})
    blob = git(repo, "hash-object", "-w", "keep.md").strip()
    name = b"\xff.md"
    subprocess.run(
        [b"git", b"-C", os.fsencode(repo), b"update-index", b"--add", b"--cacheinfo"]
        + [b"100644," + blob.encode() + b"," + name],
        check=True,
    )
    git(repo, "commit", "-q", "-m", "odd name")
    pre = head(git, repo)
    code = main(
        ["commit", "--repo", str(repo), "--no-content-check", "-m", "del", "--"]
        + [os.fsdecode(name)]
    )
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8", "surrogateescape"))
    assert code == 0 and out["status"] == "ok" and out["paths"] == [os.fsdecode(name)], out
    assert git(repo, "rev-parse", "HEAD~1").strip() == pre


def test_backstop_git_failure_exit_2_minor2(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})

    def boom(*args: Any) -> list[str]:
        raise subprocess.CalledProcessError(128, ["git", "diff"], stderr=b"fatal: index corrupt")

    monkeypatch.setattr(commit_mod, "changed_files", boom)
    code, out = run(capsys, "backstop", "--repo", str(repo), "--base", head(git, repo))
    assert code == 2 and "index corrupt" in out["_err"], out


def test_backstop_corrupt_index_exit_2_minor2(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    (repo / ".git" / "index").write_bytes(b"")
    code, out = run(capsys, "backstop", "--repo", str(repo), "--base", head(git, repo))
    assert code == 2 and "backstop:" in out["_err"], out


def test_path_through_in_repo_symlink_exit_2_minor3(make_repo, git, capsys) -> None:
    repo = make_repo({"b/n.py": N, "a/m.py": M})
    (repo / "a/bl").symlink_to("../b")
    git(repo, "add", "a/bl")
    git(repo, "commit", "-q", "-m", "link")
    (repo / "b/n.py").write_text(N_COMMENTED)
    code, out = commit(capsys, repo, "a/bl/n.py")
    assert code == 2 and "symlink" in out["_err"], out


def test_path_inside_submodule_exit_2_minor3(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    sub = repo / "sub"
    (sub / "a").mkdir(parents=True)
    git(sub, "init", "-q", "-b", "main")
    (sub / "a/m.py").write_text(M)
    git(sub, "add", "a/m.py")
    git(sub, "commit", "-q", "-m", "one")
    git(repo, "add", "sub")
    git(repo, "commit", "-q", "-m", "add gitlink")
    (sub / "a/m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "sub/a/m.py")
    assert code == 2 and "sub/a/m.py" in out["_err"], out


def test_case_mismatched_path_exit_2_minor3(make_repo, capsys) -> None:
    repo = make_repo({"a/m.py": M})
    (repo / "a/m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "A/M.py")
    assert code == 2, out


def test_directory_git_knows_nothing_under_exit_2_minor3(make_repo, capsys) -> None:
    repo = make_repo({".gitignore": "*.log\n", "m.py": M})
    (repo / "logs").mkdir()
    (repo / "logs/x.log").write_text("log\n")
    code, out = commit(capsys, repo, "logs", ref=None)
    assert code == 2 and "git knows no file" in out["_err"], out


def test_nfd_spelling_of_a_path_commits_minor4(make_repo, git, capsys) -> None:
    import unicodedata

    repo = make_repo({"keep.md": "k\n"})
    nfd = unicodedata.normalize("NFD", "café.md")
    (repo / nfd).write_text("docs\n")
    code, out = commit(capsys, repo, nfd, ref=None)
    assert code == 0 and out["status"] == "ok", out
    assert len(out["paths"]) == 1
    assert unicodedata.normalize("NFC", out["paths"][0]) == "café.md"


def test_verify_against_must_be_an_ancestor_minor5(make_repo, git, commit_files, capsys) -> None:
    repo = make_repo({"m.py": M})
    git(repo, "switch", "-q", "-c", "side")
    side = commit_files(repo, {"m.py": "x = 7\n"}, "side")
    git(repo, "switch", "-q", "main")
    pre = head(git, repo)
    (repo / "m.py").write_text("x = 7\n")
    code, out = commit(capsys, repo, "m.py", ref=side)
    assert code == 2 and "ancestor" in out["_err"], out
    assert head(git, repo) == pre


def test_stop_reports_the_old_head_minor6(make_repo, git, capsys) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "post-commit", GUARD + "git commit -q --allow-empty --no-verify -m sneaky\n")
    (repo / "m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop" and out["pre"] == pre, out


def test_directory_deletion_is_staged_minor10(make_repo, git, capsys) -> None:
    repo = make_repo({"docs/old.md": "x\n", "docs/new.md": "y\n"})
    (repo / "docs/old.md").unlink()
    (repo / "docs/new.md").write_text("z\n")
    code, out = commit(capsys, repo, "docs", ref=None)
    assert code == 0 and out["paths"] == ["docs/new.md", "docs/old.md"], out
    assert git(repo, "ls-files", "docs") == "docs/new.md\n"


def test_exception_with_foreign_commit_on_head_leaves_history_i2(
    make_repo, git, capsys, monkeypatch
) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "post-commit", GUARD + "git commit -q --allow-empty --no-verify -m sneaky\n")
    (repo / "m.py").write_text(M_COMMENTED)

    def boom(*args: Any) -> Any:
        raise RuntimeError("checks crashed")

    monkeypatch.setattr(commit_mod, "_after_commit", boom)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop" and "history was not touched" in out["detail"]
    assert out["pre"] == pre and git(repo, "log", "-1", "--format=%s").strip() == "sneaky"
