"""Update-mode change detection: which modules changed since the docs were built."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from document_repo import changes
from document_repo.changes import (
    _parse_name_status,
    _require_plain_index_entry,
    compute_changes,
    module_for,
    modules_for,
)
from document_repo.cli import main
from document_repo.verify import Result, typescript_available

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


# Two modules may name the same directory (a split module, or "src" and "./src/"). Both own its
# files, so a change there must reach both, or one module's docs go stale without a trace.
TWINS = [
    {"id": "src-b", "path": "src"},
    {"id": "src-a", "path": "src"},
    {"id": "web", "path": "web"},
]


def test_modules_for_returns_every_module_that_ties_on_the_longest_prefix() -> None:
    assert modules_for("src/x.py", TWINS) == ["src-a", "src-b"]  # sorted, not in list order
    assert modules_for("src", TWINS) == ["src-a", "src-b"]
    assert modules_for("web/i.ts", TWINS) == ["web"]
    assert modules_for("other/z.py", TWINS) == []
    assert modules_for("srcx/a.py", TWINS) == []


def test_modules_for_ties_include_other_spellings_of_the_same_path() -> None:
    modules = [
        {"id": "a", "path": "src"},
        {"id": "b", "path": "./src/"},
        {"id": "c", "path": "src/api"},
    ]
    assert modules_for("src/x.py", modules) == ["a", "b"]
    assert modules_for("src/api/z.py", modules) == ["c"]  # the longer prefix still wins alone


def test_modules_for_root_modules_tie_on_top_level_files_only() -> None:
    modules = [{"id": "r2", "path": "."}, {"id": "r1", "path": ""}, {"id": "s", "path": "src"}]
    assert modules_for("setup.py", modules) == ["r1", "r2"]
    assert modules_for("src/a.py", modules) == ["s"]
    assert modules_for("pkg/a.py", modules) == []


@pytest.mark.parametrize("order", [TWINS, list(reversed(TWINS))])
def test_modules_for_is_the_same_for_any_module_order(order: list[dict[str, str]]) -> None:
    assert modules_for("src/x.py", order) == ["src-a", "src-b"]


def test_module_for_still_returns_the_first_module_of_a_tie() -> None:
    assert module_for("src/x.py", TWINS) == "src-b"  # the first in the list given
    assert module_for("src/x.py", list(reversed(TWINS))) == "src-a"


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


def test_compute_changes(make_repo, commit_files, git, marker) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(
        repo,
        {
            "src/api/a.py": "def f():\n    return 2\n",
            "web/w.py": "# comment only\nw = 1\n",
            "README.md": "# docs\n",
            "explorer/data/model.js": "x\n",
            **marker,
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


def test_docs_and_explorer_output_are_ignored(make_repo, commit_files, git, marker) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(
        repo,
        {
            "README.md": "# r\n",
            "src/GUIDE.MD": "# g\n",
            **marker,
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


def test_a_target_file_under_explorer_is_a_change(make_repo, commit_files, git, marker) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(
        repo, {"explorer/app.py": "x = 1\n", "explorer/data/loader.js": "var f;\n", **marker}
    )
    paths = [c["path"] for c in compute_changes(repo, state, model)["changed_files"]]
    assert "explorer/app.py" in paths and "explorer/data/loader.js" in paths
    assert "explorer/data/state.json" not in paths


def test_a_foreign_state_does_not_hide_explorer_changes(make_repo, commit_files, git) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(
        repo, {"explorer/app.js": "var a;\n", "explorer/data/state.json": '{"saved": "ui"}\n'}
    )
    paths = [c["path"] for c in compute_changes(repo, state, model)["changed_files"]]
    assert paths == ["explorer/app.js", "explorer/data/state.json"]


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


# --- modules that share a path -------------------------------------------------------------


def test_a_change_marks_every_module_that_shares_the_path(make_repo, commit_files, git) -> None:
    repo = make_repo({"src/a.py": "a = 1\n", "web/w.py": "w = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {"src/a.py": "a = 2\n"})
    twins = {"modules": [{"id": "src-part1", "path": "src"}, {"id": "src-part2", "path": "src"}]}
    result = compute_changes(repo, state, twins)
    assert result["affected_modules"] == ["src-part1", "src-part2"]
    assert result["unmapped_files"] == []


def test_a_rename_marks_every_module_on_both_sides(make_repo, git) -> None:
    repo = make_repo({"src/a.py": "a = 1\n", "web/w.py": "w = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    git(repo, "mv", "src/a.py", "web/a.py")
    git(repo, "commit", "-q", "-m", "mv")
    modules = [
        {"id": "src-1", "path": "src"},
        {"id": "src-2", "path": "src"},
        {"id": "web-1", "path": "web"},
        {"id": "web-2", "path": "web"},
    ]
    result = compute_changes(repo, state, {"modules": modules})
    assert result["affected_modules"] == ["src-1", "src-2", "web-1", "web-2"]


# --- unmapped_files ------------------------------------------------------------------------


def test_a_modified_file_no_module_claims_is_unmapped_not_only_a_new_one(
    make_repo, commit_files, git
) -> None:
    # unmapped_files is every changed file that no module path claims. It is not limited to new
    # files: the caller must still look at an edited file in a directory the model never covered.
    repo = make_repo({"setup.py": "x = 1\n", "tools/old.py": "t = 1\n", "src/a.py": "a = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {"tools/old.py": "t = 2\n"})
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["changed_files"] == [{"status": "M", "path": "tools/old.py"}]
    assert result["unmapped_files"] == ["tools/old.py"]
    assert result["affected_modules"] == []


def test_a_renamed_file_is_unmapped_by_its_new_path(make_repo, git) -> None:
    repo = make_repo({"tools/old.py": "t = 1\n", "src/a.py": "a = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    (repo / "scripts").mkdir()
    git(repo, "mv", "tools/old.py", "scripts/new.py")
    git(repo, "commit", "-q", "-m", "mv")
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["unmapped_files"] == ["scripts/new.py"]
    assert result["affected_modules"] == []


# --- file type changes ---------------------------------------------------------------------

needs_symlinks = pytest.mark.skipif(
    sys.platform == "win32", reason="creating a symlink needs a privilege on Windows"
)


def _replace_with_symlink(repo: Path, git, rel: str, target: str) -> None:
    (repo / rel).unlink()
    os.symlink(target, repo / rel)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "type change")


@needs_symlinks
def test_a_file_replaced_by_a_symlink_marks_its_module(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    _replace_with_symlink(repo, git, "web/w.py", "../setup.py")
    assert git(repo, "diff", "--name-status", state["source_commit"], "HEAD").startswith("T\t")
    result = compute_changes(repo, state, model)
    assert result["changed_files"] == [{"status": "T", "path": "web/w.py"}]
    assert result["comment_only_files"] == []
    assert result["affected_modules"] == ["web"]


@needs_symlinks
def test_a_symlink_replaced_by_a_file_marks_its_module(make_repo, commit_files, git) -> None:
    repo, _, model = _setup(make_repo, git)
    _replace_with_symlink(repo, git, "web/w.py", "../setup.py")
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    (repo / "web" / "w.py").unlink()
    commit_files(repo, {"web/w.py": "w = 1\n"})
    assert git(repo, "diff", "--name-status", state["source_commit"], "HEAD").startswith("T\t")
    result = compute_changes(repo, state, model)
    assert result["changed_files"] == [{"status": "T", "path": "web/w.py"}]
    assert result["affected_modules"] == ["web"]


@needs_symlinks
def test_a_retargeted_symlink_named_like_code_is_a_change_not_an_error(
    make_repo, git, commit_files
) -> None:
    repo, _, model = _setup(make_repo, git)
    os.symlink("a.py", repo / "src" / "api" / "link.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "link")
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    (repo / "src" / "api" / "link.py").unlink()
    os.symlink("../../web/w.py", repo / "src" / "api" / "link.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "retarget")
    result = compute_changes(repo, state, model)
    assert result["changed_files"] == [{"status": "M", "path": "src/api/link.py"}]
    assert result["affected_modules"] == ["src-api"]


# The verifier refuses a symlink on its own, so a real type change cannot show that compute_changes
# keeps the guard itself. A verifier that says "comment-only" for everything can: only a plain
# edit (status M) may ever be counted as comment-only.


@pytest.fixture
def lenient_verifier(monkeypatch):
    monkeypatch.setattr(changes, "verify_file", lambda top, rel, ref: Result(rel, "stub", True))


@needs_symlinks
@pytest.mark.parametrize("to_symlink", [True, False])
def test_a_type_change_is_never_comment_only_whatever_the_verifier_says(
    make_repo, commit_files, git, lenient_verifier, to_symlink: bool
) -> None:
    repo, state, model = _setup(make_repo, git)
    _replace_with_symlink(repo, git, "web/w.py", "../setup.py")
    if not to_symlink:  # the other direction: the work tree now holds a regular file
        state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
        (repo / "web" / "w.py").unlink()
        commit_files(repo, {"web/w.py": "w = 1\n"})
    assert git(repo, "diff", "--name-status", state["source_commit"], "HEAD").startswith("T\t")
    result = compute_changes(repo, state, model)
    assert result["comment_only_files"] == []
    assert result["affected_modules"] == ["web"]


def test_only_a_plain_edit_is_comment_only_whatever_the_verifier_says(
    make_repo, commit_files, git, lenient_verifier
) -> None:
    repo, state, model = _setup(make_repo, git)
    git(repo, "mv", "src/old.py", "web/old.py")
    git(repo, "rm", "-q", "setup.py")
    commit_files(repo, {"src/new.py": "n = 1\n", "web/w.py": "# edited\nw = 1\n"})
    result = compute_changes(repo, state, model)
    assert result["comment_only_files"] == ["web/w.py"]  # the one plain edit
    assert {c["path"] for c in result["changed_files"]} == {"web/old.py", "setup.py", "src/new.py"}
    assert result["affected_modules"] == ["root", "src", "web"]


# --- submodules ----------------------------------------------------------------------------

SUB_MODULES = [*MODULES, {"id": "lib-foo", "path": "libs/foo"}]


def _with_submodule(make_repo, git) -> Path:
    """A repo with a submodule at libs/foo, committed."""
    sub = make_repo({"s.py": "s = 1\n"})
    repo = make_repo({"setup.py": "x = 1\n", "src/a.py": "a = 1\n"})
    git(repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub), "libs/foo")
    git(repo, "commit", "-q", "-m", "add submodule")
    return repo


def _hide_submodule(repo: Path, git, how: str) -> None:
    """Tell git to ignore the submodule, the three ways a repo or a user can."""
    if how == "gitmodules":
        git(repo, "config", "-f", ".gitmodules", "submodule.libs/foo.ignore", "all")
        git(repo, "add", ".gitmodules")
        git(repo, "commit", "-q", "-m", "ignore the submodule")
    elif how == "config":
        git(repo, "config", "diff.ignoreSubmodules", "all")
        git(repo, "config", "status.ignoreSubmodules", "all")
    else:
        assert how == "none"


def _commit_in_submodule(repo: Path, git) -> str:
    foo = repo / "libs" / "foo"
    (foo / "s.py").write_text("s = 2\n")
    git(foo, "add", "-A")
    git(foo, "commit", "-q", "-m", "advance")
    return git(foo, "rev-parse", "HEAD").strip()


HIDING = ["none", "gitmodules", "config"]


@pytest.mark.parametrize("how", HIDING)
def test_a_bumped_submodule_pointer_marks_its_module(make_repo, git, how: str) -> None:
    repo = _with_submodule(make_repo, git)
    _hide_submodule(repo, git, how)
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    new = _commit_in_submodule(repo, git)
    # "git add libs/foo" would skip an ignored submodule, so record the new pointer directly.
    git(repo, "update-index", "--cacheinfo", f"160000,{new},libs/foo")
    git(repo, "commit", "-q", "-m", "bump the pointer")
    assert git(repo, "status", "--porcelain") == ""
    result = compute_changes(repo, state, {"modules": SUB_MODULES})
    assert result["changed_files"] == [{"status": "M", "path": "libs/foo"}]
    assert result["affected_modules"] == ["lib-foo"]


def _modify_submodule_file(repo: Path, git) -> None:
    (repo / "libs" / "foo" / "s.py").write_text("s = 99\n")


def _add_untracked_file_in_submodule(repo: Path, git) -> None:
    (repo / "libs" / "foo" / "new.py").write_text("n = 1\n")


def _move_submodule_head(repo: Path, git) -> None:
    _commit_in_submodule(repo, git)


@pytest.mark.parametrize("how", ["gitmodules", "config"])
@pytest.mark.parametrize(
    "dirty", [_modify_submodule_file, _add_untracked_file_in_submodule, _move_submodule_head]
)
def test_a_dirty_submodule_fails_the_clean_tree_gate(make_repo, git, how: str, dirty) -> None:
    repo = _with_submodule(make_repo, git)
    _hide_submodule(repo, git, how)
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    dirty(repo, git)
    with pytest.raises(ValueError, match="working tree is not clean"):
        compute_changes(repo, state, {"modules": SUB_MODULES})


def test_a_clean_submodule_passes_the_gate(make_repo, commit_files, git) -> None:
    repo = _with_submodule(make_repo, git)
    _hide_submodule(repo, git, "gitmodules")
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {"src/a.py": "a = 2\n"})
    assert compute_changes(repo, state, {"modules": SUB_MODULES})["affected_modules"] == ["src"]


# --- a flagged index entry cannot hide an edit --------------------------------------------

FLAGS = [("--assume-unchanged", "assume-unchanged"), ("--skip-worktree", "skip-worktree")]


@pytest.mark.parametrize("flag,name", FLAGS)
def test_a_flagged_file_cannot_hide_a_committed_code_change(
    make_repo, commit_files, git, flag: str, name: str
) -> None:
    # Commit "w = 2", put "w = 1" back on disk and tell git not to look: git status is clean, and
    # the proof that the file only gained comments would pass against the old text.
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {"web/w.py": "w = 2\n"})
    (repo / "web" / "w.py").write_text("w = 1\n")
    git(repo, "update-index", flag, "web/w.py")
    assert git(repo, "status", "--porcelain") == ""  # the premise: git sees nothing
    with pytest.raises(ValueError, match=rf"web/w\.py is {name}:"):
        compute_changes(repo, state, model)


@pytest.mark.parametrize("flag,name", FLAGS)
def test_a_flagged_file_is_refused_even_when_it_matches_head(
    make_repo, commit_files, git, flag: str, name: str
) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {"web/w.py": "# comment only\nw = 1\n"})
    git(repo, "update-index", flag, "web/w.py")
    with pytest.raises(ValueError, match=rf"web/w\.py is {name}:"):
        compute_changes(repo, state, model)


def test_a_file_with_both_flags_names_both(make_repo, commit_files, git) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {"web/w.py": "# comment only\nw = 1\n"})
    git(repo, "update-index", "--assume-unchanged", "web/w.py")
    git(repo, "update-index", "--skip-worktree", "web/w.py")  # git shows both flags as "s"
    assert git(repo, "ls-files", "-v", "--", "web/w.py").startswith("s ")
    with pytest.raises(ValueError, match=r"web/w\.py is assume-unchanged and skip-worktree:"):
        compute_changes(repo, state, model)


def test_a_flag_on_a_file_the_diff_does_not_list_is_not_checked(
    make_repo, commit_files, git
) -> None:
    repo, state, model = _setup(make_repo, git)
    git(repo, "update-index", "--assume-unchanged", "setup.py")
    commit_files(repo, {"web/w.py": "w = 2\n"})
    assert compute_changes(repo, state, model)["affected_modules"] == ["web"]


def test_a_flagged_file_that_cannot_be_comment_only_is_reported_not_refused(
    make_repo, commit_files, git
) -> None:
    # Only a file whose edit might be comment-only needs a trustworthy working tree; the rest is
    # reported as changed from the commits alone.
    repo, _, model = _setup(make_repo, git)
    commit_files(repo, {"web/data.bin": b"\0\1\2"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {"web/data.bin": b"\0\1\3"})
    git(repo, "update-index", "--assume-unchanged", "web/data.bin")
    result = compute_changes(repo, state, model)
    assert result["changed_files"] == [{"status": "M", "path": "web/data.bin"}]
    assert result["affected_modules"] == ["web"]


def test_an_entry_that_is_not_a_plain_tracked_file_is_refused(make_repo, git) -> None:
    repo, _, _ = _setup(make_repo, git)
    with pytest.raises(ValueError, match=r"nope\.py.*unexpected index state"):
        _require_plain_index_entry(repo, "nope.py")


def test_a_flag_on_a_glob_sibling_is_not_mistaken_for_the_file(
    make_repo, commit_files, git
) -> None:
    # As a pathspec, "web/w[1].py" also selects "web/w1.py", whose flag says nothing about it.
    repo = make_repo({"web/w[1].py": "w = 1\n", "web/w1.py": "w = 1\n"})
    git(repo, "update-index", "--assume-unchanged", "web/w1.py")
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {"web/w[1].py": "# comment only\nw = 1\n"})
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["comment_only_files"] == ["web/w[1].py"]


needs_colon_filenames = pytest.mark.skipif(
    sys.platform == "win32", reason="Windows file names cannot contain a colon"
)


@needs_colon_filenames
def test_a_path_that_looks_like_pathspec_magic_is_a_plain_path(
    make_repo, commit_files, git
) -> None:
    # ":(top)x.py" as a pathspec means "x.py"; the file is really named with the colon.
    odd = ":(top)x.py"
    repo = make_repo({odd: "x = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {odd: "# comment only\nx = 1\n"})
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["comment_only_files"] == [odd]


needs_sh = pytest.mark.skipif(sys.platform == "win32", reason="the stale hook is a /bin/sh script")


@needs_sh
def test_a_working_tree_that_differs_from_head_is_refused_though_git_status_is_clean(
    make_repo, commit_files, git, tmp_path: Path
) -> None:
    # A filesystem monitor that reports "nothing changed" makes git status trust a stale answer,
    # with no flag set on the file. Only the file's own hash tells the truth.
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {"web/w.py": "w = 2\n"})
    hook = tmp_path / "fsmonitor-hook.sh"
    hook.write_text('#!/bin/sh\nprintf "token\\0"\n')  # a token and no changed paths
    hook.chmod(0o755)
    git(repo, "config", "core.fsmonitor", str(hook))
    git(repo, "status", "--porcelain")  # records the token; from here on git believes the hook
    (repo / "web" / "w.py").write_text("w = 1\n")
    assert git(repo, "status", "--porcelain") == ""  # the premise: git sees nothing
    with pytest.raises(ValueError, match=r"web/w\.py differs from HEAD"):
        compute_changes(repo, state, model)


def test_crlf_in_the_working_tree_under_autocrlf_is_not_a_difference(
    make_repo, commit_files, git
) -> None:
    # The hash is taken through the same filters as git add, so CRLF on disk and LF in the blob
    # are the same file; without that every file in such a checkout would be refused.
    repo = make_repo({"web/w.py": "w = 1\n"})
    git(repo, "config", "core.autocrlf", "true")
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    commit_files(repo, {"web/w.py": b"# comment only\r\nw = 1\r\n"})
    assert git(repo, "status", "--porcelain") == ""
    result = compute_changes(repo, state, {"modules": MODULES})
    assert result["comment_only_files"] == ["web/w.py"]
    assert result["affected_modules"] == []


# --- command line ---------------------------------------------------------------------------


def test_cli_changes_names_the_top_level_rule_before_reading_state(make_repo, git, capsys) -> None:
    # A subdirectory has no explorer/data of its own; the clear message must win over the
    # "no such file" one.
    repo, _, _ = _setup(make_repo, git)
    assert main(["changes", "--repo", str(repo / "src")]) == 2
    err = capsys.readouterr().err
    assert err.startswith("changes: repo must be the top level")
    assert "state.json" not in err


def test_cli_changes_names_a_missing_work_tree_before_reading_state(tmp_path: Path, capsys) -> None:
    assert main(["changes", "--repo", str(tmp_path / "nowhere")]) == 2
    err = capsys.readouterr().err
    assert "not inside a git work tree" in err
    assert "state.json" not in err


@pytest.mark.parametrize("flag,name", FLAGS)
def test_cli_changes_with_a_flagged_file_exits_2(
    make_repo, commit_files, git, capsys, flag: str, name: str
) -> None:
    repo, state, model = _setup(make_repo, git)
    _write_inputs(repo / "explorer", state, model)
    commit_files(repo, {"web/w.py": "w = 2\n"})
    (repo / "web" / "w.py").write_text("w = 1\n")
    git(repo, "update-index", flag, "web/w.py")
    assert main(["changes", "--repo", str(repo)]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith(f"changes: web/w.py is {name}:")
    assert captured.out == ""
