"""``document_repo commit`` and ``backstop``: every failure path, in real throwaway repos.

The cases named S*, F* and B* are the probes from the task-13 re-review that the old hand-filled
shell block failed or mishandled. Each one now has a test here.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
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


def _put(root: Path, files: dict) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


def test_directory_with_new_files(make_repo, marker, capsys) -> None:
    repo = make_repo({"src.py": M})
    (repo / "explorer/data").mkdir(parents=True)
    (repo / "explorer/index.html").write_text("<p>hi</p>\n")
    _put(repo, marker)
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 0, out
    assert out["paths"] == [
        "explorer/data/model.json",
        "explorer/data/state.json",
        "explorer/index.html",
    ]


def test_no_content_check_refuses_a_template_name_without_a_build_marker(
    make_repo, git, capsys
) -> None:
    # A target's own explorer/app.js, with no state.json from a build, is not the skill's.
    repo = make_repo({"explorer/app.js": "var mine = 1;\n"})
    pre = head(git, repo)
    (repo / "explorer/app.js").write_text("var mine = 2;\n")
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 2 and "explorer/app.js" in out["_err"], out
    assert head(git, repo) == pre and staged(git, repo) == ""


def test_no_content_check_refuses_a_template_name_behind_a_foreign_state(
    make_repo, git, capsys
) -> None:
    # r2/p1: the target's own state.json is not the build's marker.
    repo = make_repo(
        {
            "explorer/app.js": "export function realCode() { return 42; }\n",
            "explorer/data/state.json": '{"saved": "ui state"}\n',
        }
    )
    pre = head(git, repo)
    (repo / "explorer/app.js").write_text("export function realCode() { return 0; }\n")
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 2 and "explorer/app.js" in out["_err"], out
    assert head(git, repo) == pre and staged(git, repo) == ""


@pytest.mark.parametrize("trusted", [False, True])
def test_no_content_check_refuses_target_code_under_explorer_data(
    make_repo, git, capsys, marker, trusted: bool
) -> None:
    # r2/p3 (no marker) and r2/p4 (a stray next to a build's data).
    repo = make_repo({"explorer/data/loader.js": "export const f = () => 1;\n"})
    if trusted:
        _put(repo, marker)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "build")
    pre = head(git, repo)
    (repo / "explorer/data/loader.js").write_text("export const f = () => 2;\n")
    (repo / "explorer/data/x.js").write_text("x\n")
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 2 and "explorer/data/loader.js" in out["_err"], out
    assert "explorer/data/x.js" in out["_err"]
    assert head(git, repo) == pre and staged(git, repo) == ""


def test_no_content_check_refuses_a_target_file_under_explorer(make_repo, git, capsys) -> None:
    repo = make_repo({"explorer/app.py": "x = 1\n"})
    pre = head(git, repo)
    (repo / "explorer/app.py").write_text("x = 2\n")
    (repo / "explorer/index.html").write_text("<p>hi</p>\n")
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 2 and "explorer/app.py" in out["_err"], out
    assert head(git, repo) == pre and staged(git, repo) == ""


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


needs_symlinks = pytest.mark.skipif(
    sys.platform == "win32", reason="creating a symlink needs a privilege on Windows"
)


@needs_symlinks
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


@needs_symlinks
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


def test_hook_rewrites_docs_without_staging_restores_staged_bytes(
    make_repo, git, capsys, marker
) -> None:
    repo = make_repo({"README.md": "old\n"})
    hook(repo, "pre-commit", "printf 'hooked\\n' > README.md\necho junk > explorer/data/x.txt\n")
    _put(repo, marker)
    (repo / "explorer/index.html").write_text("a\n")
    (repo / "README.md").write_text("new docs\n")
    code, out = commit(capsys, repo, "README.md", "explorer", ref=None)
    assert code == 1 and out["status"] == "undone", out
    assert (repo / "README.md").read_text() == "new docs\n"
    hook_file = repo / "explorer/data/x.txt"
    assert not hook_file.exists(), "a file the hook made under the list is removed"
    assert (repo / "explorer/index.html").read_text() == "a\n"


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


@needs_symlinks
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


# --- task-13b review 2 fixes ---------------------------------------------------------------------


def test_wrong_case_directory_untracked_doc_is_refused_not_deleted_r2i1(
    make_repo, git, capsys
) -> None:
    """On a case-insensitive filesystem ``A/new.md`` opens ``a/new.md``; the undo used to delete
    it. On a case-sensitive one the path does not exist. Either way: exit 2, file kept."""
    repo = make_repo({"a/m.py": M})
    pre = head(git, repo)
    (repo / "a/new.md").write_text("new docs\n")
    code, out = commit(capsys, repo, "A/new.md", ref=None)
    assert code == 2, out
    assert (repo / "a/new.md").read_text() == "new docs\n"
    assert head(git, repo) == pre and staged(git, repo) == ""


def test_wrong_case_directory_tracked_doc_is_refused_r2i1(make_repo, git, capsys) -> None:
    repo = make_repo({"a/doc.md": "old\n"})
    (repo / "a/doc.md").write_text("new\n")
    code, out = commit(capsys, repo, "A/doc.md", ref=None)
    assert code == 2, out
    assert (repo / "a/doc.md").read_text() == "new\n"
    assert git(repo, "status", "--porcelain") == " M a/doc.md\n"


def test_wrong_case_directory_ref_mode_is_refused_r2i1(make_repo, git, capsys) -> None:
    repo = make_repo({"a/m.py": M})
    (repo / "a/m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "A/m.py")
    assert code == 2, out
    assert (repo / "a/m.py").read_text() == M_COMMENTED


def test_on_disk_spelling_mismatch_message_r2i1(make_repo, monkeypatch) -> None:
    """The spelling check itself, independent of the filesystem's case rules."""
    repo = make_repo({"a/m.py": M})
    real_listdir = os.listdir
    monkeypatch.setattr(
        commit_mod.os, "listdir", lambda p: ["A" if n == "a" else n for n in real_listdir(p)]
    )
    with pytest.raises(commit_mod.InputError, match="spelled differently on disk"):
        commit_mod.normalize_paths(repo, ["a/m.py"])


def test_restore_never_unlinks_a_misspelled_path_r2i1(make_repo, git, monkeypatch) -> None:
    repo = make_repo({"keep.md": "k\n"})
    (repo / "a").mkdir()
    (repo / "a/new.md").write_text("x\n")
    real_listdir = os.listdir
    monkeypatch.setattr(
        commit_mod.os, "listdir", lambda p: ["A" if n == "a" else n for n in real_listdir(p)]
    )
    with pytest.raises(commit_mod.GitError, match="spelled differently"):
        commit_mod._restore(repo, head(git, repo), ["a"])
    assert (repo / "a/new.md").exists()


def test_undo_os_error_reports_the_bad_commit_r2m1(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    hook(repo, "pre-commit", "printf 'x = 9\\n' > m.py\ngit add m.py\n")
    (repo / "m.py").write_text(M_COMMENTED)

    def fail(*args: Any) -> list[str]:
        raise PermissionError("c is read-only")

    monkeypatch.setattr(commit_mod, "_restore", fail)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop", out
    assert out["sha"] and out["sha"] != pre and out["pre"] == pre
    assert "was undone" in out["detail"] and "c is read-only" in out["detail"]
    assert "nothing was committed" not in out["detail"]


def test_interrupt_during_git_commit_is_stop_r2m4(make_repo, git, capsys, monkeypatch) -> None:
    repo = make_repo({"m.py": M})
    pre = head(git, repo)
    (repo / "m.py").write_text(M_COMMENTED)
    real = commit_mod._run

    def interrupted(top: Path, *args: str) -> Any:
        proc = real(top, *args)
        if args[0] == "commit":
            raise KeyboardInterrupt("Ctrl-C after the commit landed")
        return proc

    monkeypatch.setattr(commit_mod, "_run", interrupted)
    code, out = commit(capsys, repo, "m.py")
    assert code == 1 and out["status"] == "stop", out
    assert "was undone" in out["detail"] and head(git, repo) == pre


def test_misspelled_stops_at_a_non_directory_r2i1(make_repo) -> None:
    repo = make_repo({"m.py": M})
    assert commit_mod._misspelled(repo, "m.py/x", precompose=False) is None


def test_undo_failure_before_reset_says_head_may_hold_it_r2m1(
    make_repo, git, capsys, monkeypatch
) -> None:
    repo = make_repo({"m.py": M})
    hook(repo, "pre-commit", "printf 'x = 9\\n' > m.py\ngit add m.py\n")
    (repo / "m.py").write_text(M_COMMENTED)
    real_resolve = commit_mod._resolve_commit

    def fail(*args: Any) -> list[str]:
        def broken(*a: Any) -> str:
            raise commit_mod.GitError("HEAD unreadable")

        monkeypatch.setattr(commit_mod, "_resolve_commit", broken)
        raise OSError("reset failed")

    monkeypatch.setattr(commit_mod, "_take_back", fail)
    code, out = commit(capsys, repo, "m.py")
    monkeypatch.setattr(commit_mod, "_resolve_commit", real_resolve)
    assert code == 1 and out["status"] == "stop", out
    assert "may be on HEAD" in out["detail"] and "reset failed" in out["detail"]


# --- round 3: a hook that reformats the explorer's JSON ------------------------------------------

REFORMAT_JSON = (
    "for f in $(git diff --cached --name-only --diff-filter=AM | grep '\\.json$'); do\n"
    f'  {sys.executable} -c "import json,sys;p=sys.argv[1];d=json.load(open(p));'
    'open(p,\'w\').write(json.dumps(d,indent=4)+\'\\n\')" "$f"; git add "$f"\n'
    "done\n"
)


def _built_explorer(repo: Path) -> None:
    from document_repo.build import TEMPLATE_DIR, install_template, write_explorer_data

    fixture = Path(__file__).parent / "fixtures" / "sample_model.json"
    install_template(TEMPLATE_DIR, repo / "explorer")
    write_explorer_data(json.loads(fixture.read_text()), repo / "explorer" / "data")


def test_a_hook_that_reformats_json_keeps_the_explorer_ours(make_repo, git, capsys) -> None:
    # r3/hk: lint-staged / pretty-format-json re-indents model.json and state.json.
    repo = make_repo({"main.py": "x = 1\n"})
    hook(repo, "pre-commit", REFORMAT_JSON)
    _built_explorer(repo)
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 0 and out["status"] == "ok", out
    assert b"    " in (repo / "explorer/data/state.json").read_bytes(), "the hook did run"
    # git commit --only leaves the pre-hook bytes in the index; the commit resets it to HEAD.
    assert git(repo, "status", "--porcelain", "-uall") == ""


def test_undone_names_the_ownership_failure(make_repo, git, capsys) -> None:
    # A hook that changes the model's content: the app files are not the problem, the marker is.
    repo = make_repo({"main.py": "x = 1\n"})
    hook(
        repo,
        "pre-commit",
        f"{sys.executable} -c \"import json;p='explorer/data/model.json';d=json.load(open(p));"
        "d['meta']['generated_at']='x';open(p,'w').write(json.dumps(d))\"\n"
        "git add explorer/data/model.json\n",
    )
    _built_explorer(repo)
    pre = head(git, repo)
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 1 and out["status"] == "undone", out
    assert "no longer reads as one a build made" in out["detail"], out["detail"]
    assert "explorer/data/model.json" in out["detail"]
    assert head(git, repo) == pre


def test_a_failed_index_reset_after_the_commit_is_reported_not_raised(
    make_repo, git, capsys, monkeypatch
) -> None:
    repo = make_repo({"README.md": "old\n"})
    (repo / "README.md").write_text("new\n")
    real = commit_mod._out
    calls = {"reset": 0}

    def flaky(top, *args):
        if args == ("reset", "-q"):
            calls["reset"] += 1
            if calls["reset"] > 1:  # the first empties the index before staging
                raise commit_mod.GitError("git reset -q failed: index.lock exists")
        return real(top, *args)

    monkeypatch.setattr(commit_mod, "_out", flaky)
    code, out = commit(capsys, repo, "README.md", ref=None)
    assert code == 0 and out["status"] == "ok", out
    assert "index could not be reset" in out["detail"], out["detail"]


# --- acceptance fix 1: ignored files under a listed directory ------------------------------------
#
# open-brain's .gitignore has ``data/``. ``git add -- explorer`` skipped explorer/data/*, the
# commit said ``ok``, and the branch held an explorer with no data. The commit now refuses first.


def _snapshot(git: Callable[..., str], repo: Path) -> tuple[str, str, str]:
    """HEAD, the index (modes, shas, paths) and the work tree: what a refusal must not change."""
    return (
        head(git, repo),
        git(repo, "ls-files", "-s"),
        git(repo, "status", "--porcelain", "-uall", "--ignored"),
    )


def _ignoring_data(repo_files: dict | None = None, rule: str = "data/\n") -> dict:
    return {".gitignore": rule, "main.py": M, **(repo_files or {})}


def test_a_commit_that_would_drop_ignored_explorer_data_is_refused(make_repo, git, capsys) -> None:
    repo = make_repo(_ignoring_data())
    _built_explorer(repo)
    (repo / "main.py").write_text(M_CHANGED)
    git(repo, "add", "main.py")  # someone else's staged work: a refusal must leave it staged
    before = _snapshot(git, repo)
    code, out = commit(capsys, repo, "explorer", ref=None)
    err = out["_err"]
    assert code == 2 and "status" not in out, out
    for name in ("model.json", "model.js", "state.json"):
        assert f"explorer/data/{name} (.gitignore:1:data/)" in err, err
    assert "ignored by git" in err and "left out of the commit" in err, err
    assert (
        "negation rule" in err and "`!explorer/data/`" in err and "keep the directory local" in err
    )
    assert _snapshot(git, repo) == before
    assert staged(git, repo) == "main.py\n"


def test_a_negation_rule_lets_the_whole_explorer_commit(make_repo, git, capsys) -> None:
    repo = make_repo(_ignoring_data(rule="data/\n!explorer/data/\n"))
    _built_explorer(repo)
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 0 and out["status"] == "ok", out
    for name in ("model.json", "model.js", "state.json"):
        assert f"explorer/data/{name}" in out["paths"], out["paths"]
    assert git(repo, "ls-files", "explorer/data").split() == [
        "explorer/data/model.js",
        "explorer/data/model.json",
        "explorer/data/state.json",
    ]
    assert git(repo, "status", "--porcelain", "-uall") == ""


def test_ignored_build_output_in_the_template_is_refused_too(make_repo, git, capsys) -> None:
    # The template holds explorer/vendor/. A ``vendor/`` rule drops it, and ``vendor`` is a
    # directory the inventory skips, but this is the skill's own output: it must be carried.
    repo = make_repo(_ignoring_data(rule="vendor/\n"))
    _built_explorer(repo)
    pre = head(git, repo)
    code, out = commit(capsys, repo, "explorer", ref=None)
    err = out["_err"]
    assert code == 2, out
    assert "explorer/vendor/mermaid.min.js (.gitignore:1:vendor/)" in err, err
    assert "explorer/vendor/README.md (.gitignore:1:vendor/)" in err, err
    assert head(git, repo) == pre and staged(git, repo) == ""


@pytest.mark.parametrize(
    "files",
    [
        {"explorer/.DS_Store": "x", "explorer/data/.DS_Store": "x"},
        {"explorer/__pycache__/x.pyc": "x", "explorer/data/helper.pyc": "x"},
        {"explorer/node_modules/pkg/index.js": "x", "explorer/node_modules/pkg/README.md": "x"},
        {"explorer/data/.model.json.swp": "x", "explorer/index.html~": "x"},
        {"explorer/dist/bundle.js": "x", "explorer/.venv/lib/README.md": "x"},
    ],
)
def test_ignored_junk_under_a_listed_directory_does_not_stop_the_commit(
    make_repo, git, capsys, files: dict
) -> None:
    rules = ".DS_Store\n__pycache__/\n*.pyc\nnode_modules/\n*.swp\n*~\ndist/\n.venv/\n"
    repo = make_repo(_ignoring_data(rule=rules))
    _built_explorer(repo)
    _put(repo, files)
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 0 and out["status"] == "ok", out
    tracked = git(repo, "ls-files").split("\n")
    assert not [p for p in tracked if p in files], tracked


def test_ignored_markdown_in_a_dependency_directory_is_junk(make_repo, git, capsys) -> None:
    # A docs site keeps its dependencies under docs/: hundreds of READMEs, none of them ours.
    repo = make_repo({".gitignore": "node_modules/\n", "main.py": M})
    _put(repo, {"docs/guide.md": "# g\n", "docs/node_modules/x/README.md": "# x\n"})
    code, out = commit(capsys, repo, "docs", ref=None)
    assert code == 0 and out["paths"] == ["docs/guide.md"], out


def test_an_ignored_readme_under_a_listed_docs_directory_is_refused(make_repo, git, capsys) -> None:
    repo = make_repo({".gitignore": "internal/\n", "main.py": M})
    _put(repo, {"docs/guide.md": "# g\n", "docs/internal/README.md": "# i\n"})
    before = _snapshot(git, repo)
    code, out = commit(capsys, repo, "docs", ref=None)
    err = out["_err"]
    assert code == 2 and "docs/internal/README.md (.gitignore:1:internal/)" in err, out
    assert "docs/guide.md" not in err, "only the files left out are named"
    assert _snapshot(git, repo) == before


def test_the_directory_you_list_is_not_judged_by_its_own_name(make_repo, git, capsys) -> None:
    # ``vendor`` is above the listed root, so it is not a dependency directory under it.
    repo = make_repo({".gitignore": "private/\n", "main.py": M})
    _put(repo, {"vendor/docs/guide.md": "# g\n", "vendor/docs/private/README.md": "# p\n"})
    code, out = commit(capsys, repo, "vendor/docs", ref=None)
    assert code == 2 and "vendor/docs/private/README.md" in out["_err"], out


@pytest.mark.parametrize(
    "where,rule,source",
    [
        (".gitignore", "NOTES.md\n", ".gitignore:1:NOTES.md"),
        ("docs/.gitignore", "NOTES.md\n", "docs/.gitignore:1:NOTES.md"),
        (".git/info/exclude", "# local\nNOTES.md\n", ".git/info/exclude:2:NOTES.md"),
    ],
)
def test_the_refusal_names_the_file_line_and_pattern_of_the_rule(
    make_repo, capsys, where: str, rule: str, source: str
) -> None:
    files = {"main.py": M, "docs/guide.md": "# g\n"}
    if not where.startswith(".git/"):
        files[where] = rule  # a tracked rule file is not a change under docs/
    repo = make_repo(files)
    if where.startswith(".git/"):
        (repo / where).write_text(rule)
    _put(repo, {"docs/guide.md": "# g2\n", "docs/NOTES.md": "# n\n"})
    code, out = commit(capsys, repo, "docs", ref=None)
    assert code == 2 and f"docs/NOTES.md ({source})" in out["_err"], out


def test_a_global_excludes_file_is_honoured(make_repo, git, capsys, tmp_path) -> None:
    exclude = tmp_path / "global-ignore"
    exclude.write_text("data/\n")
    repo = make_repo({"main.py": M})
    git(repo, "config", "core.excludesFile", str(exclude))
    _built_explorer(repo)
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 2 and f"explorer/data/state.json ({exclude}:1:data/)" in out["_err"], out


def test_a_tracked_file_that_matches_a_rule_is_not_left_out(make_repo, git, capsys) -> None:
    # Git keeps tracking a file that matches an ignore rule: only untracked ones are dropped.
    repo = make_repo(_ignoring_data())
    _put(repo, {"docs/data/old.md": "old\n"})
    git(repo, "add", "-f", "docs/data/old.md")
    git(repo, "commit", "-q", "-m", "force-added")
    (repo / "docs/data/old.md").write_text("new\n")
    code, out = commit(capsys, repo, "docs", ref=None)
    assert code == 0 and out["paths"] == ["docs/data/old.md"], out


def test_an_ignored_source_file_is_not_the_skills_to_carry(make_repo, git, capsys) -> None:
    # The inventory never lists an ignored file, so the skill never comments one: a local
    # settings file or a virtualenv under a module is not work the commit would lose. Only
    # Markdown and the skill's own explorer output are expected in a commit (``is_exempt``).
    repo = make_repo({".gitignore": "local_settings.py\nenv/\n", "src/m.py": M})
    _put(repo, {"src/local_settings.py": "SECRET = 1\n", "src/env/lib/site.py": "x = 1\n"})
    (repo / "src/m.py").write_text(M_COMMENTED)
    code, out = commit(capsys, repo, "src")
    assert code == 0 and out["paths"] == ["src/m.py"], out


def test_a_long_list_of_ignored_files_is_cut_and_counted(make_repo, git, capsys) -> None:
    extra = 5
    total = commit_mod.IGNORED_SHOWN + extra
    repo = make_repo({".gitignore": "gen/\n", "main.py": M})
    _put(repo, {"docs/guide.md": "# g\n"})
    _put(repo, {f"docs/gen/{i:03}.md": "# x\n" for i in range(total)})
    code, out = commit(capsys, repo, "docs", ref=None)
    err = out["_err"]
    assert code == 2, out
    assert err.count(".md (.gitignore:1:gen/)") == commit_mod.IGNORED_SHOWN, err
    assert f"and {extra} more" in err, err


def test_nested_listed_directories_count_each_ignored_file_once(make_repo, git, capsys) -> None:
    repo = make_repo({".gitignore": "gen/\n", "main.py": M})
    _put(repo, {"docs/sub/a.md": "# a\n", "docs/sub/gen/x.md": "# x\n"})
    code, out = commit(capsys, repo, "docs", "docs/sub", ref=None)
    err = out["_err"]
    assert code == 2 and err.count("docs/sub/gen/x.md") == 1, err
    assert "more" not in err, err


def test_listing_only_files_never_asks_git_about_ignored_files(
    make_repo, git, capsys, monkeypatch
) -> None:
    def boom(argv: list[str]) -> Any:
        raise AssertionError(f"unexpected scan: {argv}")

    repo = make_repo(_ignoring_data({"a/m.py": M}))
    (repo / "a/m.py").write_text(M_COMMENTED)
    monkeypatch.setattr(commit_mod, "_stream", boom)
    code, out = commit(capsys, repo, "a/m.py")
    assert code == 0 and out["status"] == "ok", out


def test_a_git_failure_while_looking_for_ignored_files_commits_nothing(
    make_repo, git, capsys, monkeypatch
) -> None:
    def fail(argv: list[str]) -> Any:
        raise commit_mod.GitError("git ls-files failed: index file corrupt")
        yield  # pragma: no cover - makes this a generator, like the real one

    repo = make_repo(_ignoring_data())
    _built_explorer(repo)
    (repo / "main.py").write_text(M_CHANGED)
    git(repo, "add", "main.py")
    before = _snapshot(git, repo)
    monkeypatch.setattr(commit_mod, "_stream", fail)
    code, out = commit(capsys, repo, "explorer", ref=None)
    assert code == 2 and out["status"] == "error", out
    assert "nothing was committed" in out["detail"] and "index file corrupt" in out["detail"]
    assert _snapshot(git, repo) == before


# The streaming reader, on commands that are not git so every edge can be built exactly.


def _printf(payload: bytes, code: int = 0, err: str = "") -> list[str]:
    script = (
        "import sys; sys.stdout.buffer.write(%r); sys.stdout.buffer.flush(); "
        "sys.stderr.write(%r); sys.exit(%d)" % (payload, err, code)
    )
    return [sys.executable, "-c", script]


def test_stream_yields_each_nul_separated_path() -> None:
    got = list(commit_mod._stream(_printf(b"a/b.md\0c d.md\0\0e.md\0")))
    assert got == ["a/b.md", "c d.md", "e.md"]


def test_stream_joins_a_path_split_across_reads(monkeypatch) -> None:
    monkeypatch.setattr(commit_mod, "_CHUNK", 3)
    got = list(commit_mod._stream(_printf("dir/ünï.md\0second.md\0".encode())))
    assert got == ["dir/ünï.md", "second.md"]


def test_stream_keeps_a_last_path_that_has_no_terminator() -> None:
    assert list(commit_mod._stream(_printf(b"a.md\0b.md"))) == ["a.md", "b.md"]


def test_stream_keeps_bytes_that_are_not_utf8() -> None:
    (got,) = commit_mod._stream(_printf(b"a\xffb.md\0"))
    assert got.encode("utf-8", "surrogateescape") == b"a\xffb.md"


def test_stream_raises_when_git_fails_so_a_short_list_never_reads_as_complete() -> None:
    with pytest.raises(commit_mod.GitError, match="boom"):
        list(commit_mod._stream(_printf(b"a.md\0", code=128, err="fatal: boom")))


def test_stream_stops_the_command_when_the_reader_stops() -> None:
    script = "import sys,time\nwhile True: sys.stdout.write('a\\0'*5000); sys.stdout.flush()\n"
    gen = commit_mod._stream([sys.executable, "-c", script])
    assert next(gen) == "a"
    gen.close()  # must not hang: the writer gets SIGPIPE once the pipe is closed


# ignore_rules: the rule git names for each path, negations left out.


def test_ignore_rules_names_source_line_and_pattern(make_repo) -> None:
    repo = make_repo({".gitignore": "# c\n*.log\n!keep.log\ndata/\n", "x.py": M})
    got = commit_mod.ignore_rules(
        repo, ["a.log", "keep.log", "x.py", "explorer/data/state.json", "gone/none.log"]
    )
    assert got == {
        "a.log": ".gitignore:2:*.log",
        "explorer/data/state.json": ".gitignore:4:data/",
        "gone/none.log": ".gitignore:2:*.log",
    }


def test_ignore_rules_with_no_paths_runs_nothing(tmp_path) -> None:
    assert commit_mod.ignore_rules(tmp_path / "not-a-repo", []) == {}


def test_ignore_rules_fails_loudly_when_git_does(tmp_path) -> None:
    with pytest.raises(commit_mod.GitError, match="check-ignore"):
        commit_mod.ignore_rules(tmp_path, ["a.md"])


def test_left_out_drops_paths_git_tracks(make_repo, git) -> None:
    repo = make_repo(_ignoring_data())
    _put(repo, {"explorer/data/state.json": "{}\n"})
    git(repo, "add", "-f", "explorer/data/state.json")
    paths = ["explorer/data/state.json", "explorer/data/model.js"]
    assert commit_mod.ignore_rules(repo, paths).keys() == set(paths)
    assert commit_mod.left_out(repo, paths) == {"explorer/data/model.js": ".gitignore:1:data/"}


def test_left_out_is_empty_when_nothing_is_ignored(make_repo) -> None:
    repo = make_repo({"main.py": M})
    assert commit_mod.left_out(repo, ["explorer/data/state.json"]) == {}
