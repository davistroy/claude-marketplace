"""Update-mode change detection: which modules changed since the docs were built."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from document_repo.changes import _parse_name_status, compute_changes, module_for
from document_repo.cli import main
from document_repo.verify import typescript_available

MODULES = [
    {"id": "root", "path": "."},
    {"id": "src", "path": "src"},
    {"id": "src-api", "path": "src/api"},
    {"id": "web", "path": "web"},
]


@pytest.mark.parametrize(
    "path,expected",
    [
        ("setup.py", "root"),
        ("src/x.py", "src"),
        ("src/api/a.py", "src-api"),
        ("src/api", "src-api"),
        ("web/i.ts", "web"),
        ("other/z.py", None),
        ("srcx/a.py", None),
        ("src/apix/a.py", "src"),
    ],
)
def test_module_for(path: str, expected: str | None) -> None:
    assert module_for(path, MODULES) == expected


@pytest.mark.parametrize("order", [MODULES, list(reversed(MODULES))])
def test_module_for_longest_prefix_wins_in_any_order(order: list[dict[str, str]]) -> None:
    assert module_for("src/api/a.py", order) == "src-api"
    assert module_for("src/x.py", order) == "src"
    assert module_for("top.py", order) == "root"


@pytest.mark.parametrize("root_path", [".", "", "./", "/"])
def test_module_for_root_spellings_claim_only_top_level_files(root_path: str) -> None:
    modules = [{"id": "r", "path": root_path}]
    assert module_for("setup.py", modules) == "r"
    assert module_for("pkg/a.py", modules) is None


@pytest.mark.parametrize("src_path", ["src", "src/", "./src", "./src/", "src//"])
def test_module_for_normalises_module_paths(src_path: str) -> None:
    assert module_for("src/a.py", [{"id": "s", "path": src_path}]) == "s"
    assert module_for("srcx/a.py", [{"id": "s", "path": src_path}]) is None


def _setup(make_repo, git):
    repo = make_repo(
        {
            "setup.py": "x = 1\n",
            "src/api/a.py": "def f():\n    return 1\n",
            "web/w.py": "w = 1\n",
            "src/old.py": "y = 1\n",
        }
    )
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    model = {"modules": MODULES}
    return repo, state, model


def test_compute_changes(make_repo, commit_files, git) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(
        repo,
        {
            "src/api/a.py": "def f():\n    return 2\n",
            "web/w.py": "# comment only\nw = 1\n",
            "README.md": "# docs\n",
            "explorer/data/model.js": "x\n",
            "tools/new.py": "z = 1\n",
        },
    )
    git(repo, "rm", "-q", "src/old.py")
    git(repo, "commit", "-q", "-m", "rm")
    result = compute_changes(repo, state, model)
    assert result["since"] == state["source_commit"]
    assert result["affected_modules"] == ["src", "src-api"]
    assert result["comment_only_files"] == ["web/w.py"]
    assert result["unmapped_files"] == ["tools/new.py"]
    assert result["removed_files"] == ["src/old.py"]
    assert {c["path"] for c in result["changed_files"]} == {
        "src/api/a.py",
        "tools/new.py",
        "src/old.py",
    }
    assert {c["path"]: c["status"] for c in result["changed_files"]} == {
        "src/api/a.py": "M",
        "tools/new.py": "A",
        "src/old.py": "D",
    }
    assert result["head"] == git(repo, "rev-parse", "HEAD").strip()


def test_nothing_changed(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    result = compute_changes(repo, state, model)
    assert result == {
        "since": state["source_commit"],
        "head": state["source_commit"],
        "changed_files": [],
        "comment_only_files": [],
        "removed_files": [],
        "affected_modules": [],
        "unmapped_files": [],
    }


def test_comment_only_edit_is_not_a_change_but_a_code_edit_in_the_same_file_is(
    make_repo, commit_files, git
) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {"web/w.py": "# comment only\nw = 1\n"})
    result = compute_changes(repo, state, model)
    assert result["comment_only_files"] == ["web/w.py"]
    assert result["affected_modules"] == []
    commit_files(repo, {"web/w.py": "# comment only\nw = 2\n"})
    result = compute_changes(repo, state, model)
    assert result["comment_only_files"] == []
    assert result["affected_modules"] == ["web"]


def test_comment_only_typescript_edit_is_not_a_change(make_repo, commit_files, git) -> None:
    repo = make_repo({"web/i.ts": "export const a = 1;\n"})
    if not typescript_available(repo):
        message = "node + typescript not available (install with: npm install -g typescript)"
        if os.environ.get("CI"):
            pytest.fail(message)
        pytest.skip(message)
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {"web/i.ts": "// comment only\nexport const a = 1;\n"})
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["comment_only_files"] == ["web/i.ts"]
    assert result["affected_modules"] == []
    commit_files(repo, {"web/i.ts": "// comment only\nexport const a = 2;\n"})
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["comment_only_files"] == []
    assert result["affected_modules"] == ["web"]


def test_mode_only_change_counts_as_a_change(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    (repo / "setup.py").chmod(0o755)  # where git tracks modes, the work tree must match the index
    git(repo, "update-index", "--chmod=+x", "setup.py")
    git(repo, "commit", "-q", "-m", "chmod")
    result = compute_changes(repo, state, model)
    assert result["comment_only_files"] == []
    assert result["affected_modules"] == ["root"]


def test_rename_marks_both_modules(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    git(repo, "mv", "src/old.py", "web/old.py")
    git(repo, "commit", "-q", "-m", "mv")
    result = compute_changes(repo, state, model)
    assert result["affected_modules"] == ["src", "web"]
    assert result["changed_files"] == [{"status": "R", "path": "web/old.py"}]
    assert result["removed_files"] == []


def test_a_doc_renamed_into_code_marks_only_the_code_side(make_repo, git) -> None:
    repo = make_repo({"notes.md": "x = 1\n", "src/a.py": "a = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    git(repo, "mv", "notes.md", "src/notes.py")
    git(repo, "commit", "-q", "-m", "mv")
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["affected_modules"] == ["src"]  # the root module did not own a code file


def test_code_renamed_into_a_doc_marks_the_module_it_left(make_repo, git) -> None:
    repo = make_repo({"src/a.py": "a = 1\n", "web/w.py": "w = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    git(repo, "mv", "src/a.py", "notes.md")
    git(repo, "commit", "-q", "-m", "mv")
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["affected_modules"] == ["src"]
    assert result["unmapped_files"] == []


def test_docs_and_explorer_output_are_ignored(make_repo, commit_files, git) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(
        repo,
        {
            "README.md": "# r\n",
            "src/GUIDE.MD": "# g\n",
            "explorer/data/state.json": "{}\n",
            "explorer/app.js": "var a;\n",
        },
    )
    result = compute_changes(repo, state, model)
    assert result["changed_files"] == []
    assert result["affected_modules"] == []
    assert result["unmapped_files"] == []


def test_explorer_is_ignored_only_at_the_repo_root(make_repo, commit_files, git) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {"src/explorer/x.py": "x = 1\n", "explorer.py": "y = 1\n"})
    result = compute_changes(repo, state, model)
    assert result["affected_modules"] == ["root", "src"]


def test_a_deleted_unmapped_file_is_removed_but_not_unmapped(make_repo, commit_files, git) -> None:
    repo, _, model = _setup(make_repo, git)
    commit_files(repo, {"tools/gone.py": "g = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    git(repo, "rm", "-q", "tools/gone.py")
    git(repo, "commit", "-q", "-m", "rm")
    result = compute_changes(repo, state, model)
    assert result["removed_files"] == ["tools/gone.py"]
    assert result["unmapped_files"] == []
    assert result["affected_modules"] == []


# The spaces, tab and non-ASCII characters below arrive in git's output verbatim only with -z; a
# tab-split parse would cut "tab\tname.py" in two and git would quote the others.
needs_tab_filenames = pytest.mark.skipif(
    sys.platform == "win32", reason="Windows file names cannot contain a tab"
)


def test_paths_with_spaces_and_non_ascii_characters(make_repo, commit_files, git) -> None:
    spaced, accented = "dir with space/a b.py", "src/naïve 日本.py"
    modules = [*MODULES, {"id": "spaced", "path": "dir with space"}]
    repo = make_repo({spaced: "a = 1\n", accented: "b = 1\n", "web/w.py": "w = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {spaced: "a = 2\n", accented: "# note\nb = 1\n"})
    git(repo, "mv", "web/w.py", "web/w v2.py")
    git(repo, "commit", "-q", "-m", "mv")
    result = compute_changes(repo, state, {"modules": modules})
    assert result["affected_modules"] == ["spaced", "web"]
    assert result["comment_only_files"] == [accented]
    assert {c["path"] for c in result["changed_files"]} == {spaced, "web/w v2.py"}


@needs_tab_filenames
def test_a_path_with_a_tab_is_one_path(make_repo, commit_files, git) -> None:
    tabbed = "src/tab\tname.py"
    repo = make_repo({tabbed: "t = 1\n", "web/w.py": "w = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {tabbed: "t = 2\n", "src/other\tfile.py": "o = 1\n"})
    git(repo, "mv", "web/w.py", "web/w\tmoved.py")
    git(repo, "commit", "-q", "-m", "mv")
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["affected_modules"] == ["src", "web"]
    assert {c["path"] for c in result["changed_files"]} == {
        tabbed,
        "src/other\tfile.py",
        "web/w\tmoved.py",
    }
    assert result["unmapped_files"] == []


def test_parse_name_status() -> None:
    raw = (
        b"M\0src/a b.py\0"
        b"A\0tab\tname.py\0"
        b"D\0line\nbreak.py\0"
        b"R087\0old name.py\0new\tname.py\0"
        b"C75\0from.py\0to.py\0"
        b"T\0link\0"
    )
    assert _parse_name_status(raw) == [
        ("M", "src/a b.py", "src/a b.py"),
        ("A", "tab\tname.py", "tab\tname.py"),
        ("D", "line\nbreak.py", "line\nbreak.py"),
        ("R", "old name.py", "new\tname.py"),
        ("C", "from.py", "to.py"),
        ("T", "link", "link"),
    ]
    assert _parse_name_status(b"") == []


@pytest.mark.parametrize(
    "raw,message",
    [
        (b"M\0", "unexpected git diff output"),
        (b"M\0a.py", "unexpected git diff output"),
        (b"R100\0only-one.py\0", "unexpected git diff output"),
        (b"\0a.py\0", "unexpected git diff output"),
        (b"M\0\0", "unexpected git diff output"),
        (b"M\0caf\xe9.py\0", "not valid UTF-8"),
    ],
)
def test_parse_name_status_rejects_what_it_cannot_read(raw: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _parse_name_status(raw)


def test_a_git_failure_is_reported_not_swallowed(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    (repo / ".git" / "index").write_bytes(b"not an index")
    with pytest.raises(ValueError, match="git status failed: .*index"):
        compute_changes(repo, state, model)


def test_unknown_commit_raises(make_repo, git) -> None:
    repo, _, model = _setup(make_repo, git)
    with pytest.raises(ValueError, match="not in this repository"):
        compute_changes(repo, {"source_commit": "f" * 40}, model)


@pytest.mark.parametrize("value", ["HEAD", "main", "abc123", "-q", " " + "a" * 40, "g" * 40])
def test_source_commit_must_be_a_full_hash(make_repo, git, value: str) -> None:
    # "HEAD" would diff HEAD against itself and report that nothing changed.
    repo, _, model = _setup(make_repo, git)
    with pytest.raises(ValueError, match="full commit hash"):
        compute_changes(repo, {"source_commit": value}, model)


def test_an_uppercase_hash_is_accepted(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    upper = {"source_commit": state["source_commit"].upper()}
    assert compute_changes(repo, upper, model)["since"] == state["source_commit"]


def test_a_non_commit_object_is_not_in_the_history(make_repo, git) -> None:
    repo, _, model = _setup(make_repo, git)
    blob = git(repo, "rev-parse", "HEAD:setup.py").strip()
    with pytest.raises(ValueError, match="not in this repository"):
        compute_changes(repo, {"source_commit": blob}, model)


@pytest.mark.parametrize(
    "state",
    [{}, {"source_commit": ""}, {"source_commit": None}, {"source_commit": 7}, [], "abc", None],
)
def test_missing_source_commit_raises(make_repo, git, state) -> None:
    repo, _, model = _setup(make_repo, git)
    with pytest.raises(ValueError, match="no source_commit"):
        compute_changes(repo, state, model)


@pytest.mark.parametrize(
    "model",
    [
        {},
        [],
        None,
        {"modules": None},
        {"modules": {}},
        {"modules": ["src"]},
        {"modules": [{"id": "a"}]},
        {"modules": [{"path": "a"}]},
        {"modules": [{"id": 1, "path": "a"}]},
        {"modules": [{"id": "a", "path": None}]},
    ],
)
def test_a_model_without_usable_modules_raises(make_repo, git, model) -> None:
    repo, state, _ = _setup(make_repo, git)
    with pytest.raises(ValueError, match="modules"):
        compute_changes(repo, state, model)


def test_a_model_with_no_modules_leaves_every_file_unmapped(make_repo, commit_files, git) -> None:
    repo, state, _ = _setup(make_repo, git)
    commit_files(repo, {"setup.py": "x = 2\n"})
    result = compute_changes(repo, state, {"modules": []})
    assert result["affected_modules"] == []
    assert result["unmapped_files"] == ["setup.py"]


def test_not_a_git_work_tree_raises(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(ValueError, match="not inside a git work tree"):
        compute_changes(plain, {"source_commit": "a" * 40}, {"modules": MODULES})


def test_a_subdirectory_of_a_work_tree_is_refused(make_repo, git) -> None:
    # Model paths and diff paths must be relative to the same directory. Anything but the top
    # level would leave every changed file "unmapped" and report that nothing needs analysis.
    repo, state, model = _setup(make_repo, git)
    with pytest.raises(ValueError, match="top level"):
        compute_changes(repo / "src", state, model)


def test_the_top_level_may_be_named_with_dot_segments(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    assert compute_changes(repo / "src" / "..", state, model)["since"] == state["source_commit"]


def _edit(repo: Path, git) -> None:
    (repo / "setup.py").write_text("x = 2\n")


def _untracked(repo: Path, git) -> None:
    (repo / "new.py").write_text("n = 1\n")


def _delete(repo: Path, git) -> None:
    (repo / "setup.py").unlink()


def _stage(repo: Path, git) -> None:
    _edit(repo, git)
    git(repo, "add", "setup.py")


def _doc(repo: Path, git) -> None:
    (repo / "README.md").write_text("# r\n")


def _explorer(repo: Path, git) -> None:
    (repo / "explorer").mkdir()
    (repo / "explorer" / "x.js").write_text("x\n")


@pytest.mark.parametrize("dirty", [_edit, _untracked, _delete, _stage, _doc, _explorer])
def test_a_dirty_working_tree_raises(make_repo, git, dirty) -> None:
    repo, state, model = _setup(make_repo, git)
    dirty(repo, git)
    with pytest.raises(ValueError, match="working tree is not clean"):
        compute_changes(repo, state, model)


def test_a_dirty_working_tree_cannot_hide_a_committed_code_change(
    make_repo, commit_files, git
) -> None:
    # The diff reads commits, the comment-only proof reads the working tree. With the old text
    # restored on disk (uncommitted), the proof would pass a file whose code really changed.
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {"web/w.py": "w = 2\n"})
    (repo / "web" / "w.py").write_text("w = 1\n")
    with pytest.raises(ValueError, match="working tree is not clean"):
        compute_changes(repo, state, model)
    git(repo, "checkout", "--", "web/w.py")
    assert compute_changes(repo, state, model)["affected_modules"] == ["web"]


def test_a_gitignored_file_does_not_make_the_tree_dirty(make_repo, commit_files, git) -> None:
    repo, _, model = _setup(make_repo, git)
    state = {"source_commit": commit_files(repo, {".gitignore": "*.log\n"})}
    (repo / "run.log").write_text("noise\n")
    assert compute_changes(repo, state, model)["affected_modules"] == []


def _write_inputs(explorer: Path, state: object, model: object) -> None:
    data = explorer / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "state.json").write_text(json.dumps(state))
    (data / "model.json").write_text(json.dumps(model))


def test_cli_changes(make_repo, commit_files, git, capsys) -> None:
    repo, state, model = _setup(make_repo, git)
    _write_inputs(repo / "explorer", state, model)
    commit_files(repo, {"setup.py": "x = 2\n"})
    assert main(["changes", "--repo", str(repo)]) == 0
    assert json.loads(capsys.readouterr().out)["affected_modules"] == ["root"]
    _write_inputs(repo / "explorer", {"source_commit": "0" * 40}, model)
    commit_files(repo, {})
    assert main(["changes", "--repo", str(repo)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("changes: ")
    assert "not in this repository" in err


def test_cli_changes_with_an_explorer_dir_outside_the_repo(
    make_repo, commit_files, git, tmp_path, capsys
) -> None:
    repo, state, model = _setup(make_repo, git)
    elsewhere = tmp_path / "elsewhere"
    _write_inputs(elsewhere, state, model)
    commit_files(repo, {"web/w.py": "w = 2\n"})
    assert main(["changes", "--repo", str(repo), "--explorer-dir", str(elsewhere)]) == 0
    assert json.loads(capsys.readouterr().out)["affected_modules"] == ["web"]


def test_cli_changes_on_a_dirty_tree_exits_2(make_repo, commit_files, git, capsys) -> None:
    repo, state, model = _setup(make_repo, git)
    _write_inputs(repo / "explorer", state, model)
    commit_files(repo, {})
    (repo / "setup.py").write_text("x = 2\n")
    assert main(["changes", "--repo", str(repo)]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("changes: working tree is not clean")
    assert captured.out == ""


@pytest.mark.parametrize("missing", ["state.json", "model.json"])
def test_cli_changes_missing_input_exits_2(make_repo, commit_files, git, capsys, missing) -> None:
    repo, state, model = _setup(make_repo, git)
    _write_inputs(repo / "explorer", state, model)
    (repo / "explorer" / "data" / missing).unlink()
    commit_files(repo, {})
    assert main(["changes", "--repo", str(repo)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("changes: ")
    assert missing in err


@pytest.mark.parametrize("broken", ["state.json", "model.json"])
@pytest.mark.parametrize("content", [b"{not json", b"\xff\xfe\x00"])
def test_cli_changes_unreadable_input_exits_2(
    make_repo, commit_files, git, capsys, broken, content
) -> None:
    repo, state, model = _setup(make_repo, git)
    _write_inputs(repo / "explorer", state, model)
    commit_files(repo, {"explorer/data/" + broken: content})
    assert main(["changes", "--repo", str(repo)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("changes: ")
    assert broken in err


def test_cli_changes_state_without_source_commit_exits_2(
    make_repo, commit_files, git, capsys
) -> None:
    repo, _, model = _setup(make_repo, git)
    _write_inputs(repo / "explorer", {"built_at": "yesterday"}, model)
    commit_files(repo, {})
    assert main(["changes", "--repo", str(repo)]) == 2
    assert capsys.readouterr().err == "changes: state has no source_commit\n"


def test_cli_changes_model_without_modules_exits_2(make_repo, commit_files, git, capsys) -> None:
    repo, state, _ = _setup(make_repo, git)
    _write_inputs(repo / "explorer", state, {"meta": {}})
    commit_files(repo, {})
    assert main(["changes", "--repo", str(repo)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("changes: ")
    assert "modules" in err


def test_cli_changes_outside_a_git_work_tree_exits_2(tmp_path: Path, capsys) -> None:
    _write_inputs(tmp_path / "explorer", {"source_commit": "a" * 40}, {"modules": MODULES})
    assert main(["changes", "--repo", str(tmp_path)]) == 2
    assert "not inside a git work tree" in capsys.readouterr().err
