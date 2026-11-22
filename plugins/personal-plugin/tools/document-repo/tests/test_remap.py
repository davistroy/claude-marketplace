import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from document_repo.cli import main
from document_repo.remap import line_map, remap_model, write_model
from document_repo.schema import MAX_SNIPPET_LINES, validate

FIXTURE = Path(__file__).parent / "fixtures" / "sample_model.json"
# Line 1 import, lines 2-11 blank, line 12 is the function (matches the fixture's line 12).
ROUTES = (
    "import x\n"
    + "\n" * 10
    + "async def create_note(body):\n    row = await db.insert(body)\n    return row\n"
)
ROUTES_PATH = "src/api/routes.py"


def test_line_map_pure_insertions() -> None:
    assert line_map(["a", "b", "c"], ["# h", "a", "# why", "b", "c"]) == [2, 4, 5]


def test_line_map_replacement_is_clamped() -> None:
    assert line_map(["a", "b"], ["a", "z"]) == [1, 2]
    assert line_map(["a", "b", "c"], ["a"]) == [1, 1, 1]


def test_line_map_empty_sides() -> None:
    assert line_map([], ["a", "b"]) == []
    assert line_map(["a", "b"], []) == [1, 1]


def test_line_map_repeated_blocks_follow_the_insertions() -> None:
    # Two identical bodies. Every line of the first is commented, the second only at its edges.
    # A longest-matching-block diff pairs the first body with the second; the true mapping is the
    # one where only inserted lines moved.
    body = [f"    step_{i}()" for i in range(10)]
    before = ["def a():", *body, "def b():", *body, "def c():"]
    after = ["def a():"]
    for line in body:
        after += ["    # note", line]
    after += ["def b():", "    # why", *body, "# end", "def c():"]
    expected = [1, *range(3, 22, 2), 22, *range(24, 34), 35]
    assert line_map(before, after) == expected
    assert [after[n - 1] for n in expected] == before


def _model(sha: str) -> dict[str, Any]:
    model: dict[str, Any] = json.loads(FIXTURE.read_text())
    model["meta"]["source_commit"] = sha
    return model


def _point_at(model: dict[str, Any], rel: str, start: int, end: int) -> None:
    """Aim the fixture's one interface item and one flow step at ``rel``."""
    item = model["modules"][1]["interface"][0]
    item["file"], item["line"] = rel, start
    step = model["flows"][0]["steps"][0]
    step["file"], step["line_start"], step["line_end"] = rel, start, end


def test_remap_model_moves_lines_and_refreshes_snippet(make_repo, commit_files, git) -> None:
    repo = make_repo({"src/api/routes.py": ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    commented = '"""Routes."""\n' + ROUTES.replace(
        "async def", "# Why: one insert per request.\nasync def"
    )
    new = commit_files(repo, {"src/api/routes.py": commented})
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert warnings == []
    assert model["meta"]["source_commit"] == new
    assert model["modules"][1]["interface"][0]["line"] == 14
    step = model["flows"][0]["steps"][0]
    assert (step["line_start"], step["line_end"]) == (14, 16)
    assert step["snippet"].startswith("async def create_note")
    assert validate(model) == []


def test_remap_model_returns_a_copy(make_repo, commit_files, git) -> None:
    repo = make_repo({"src/api/routes.py": ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {"src/api/routes.py": "# h\n" + ROUTES})
    original = _model(base)
    snapshot = json.loads(json.dumps(original))
    remapped, _ = remap_model(original, repo, "HEAD")
    assert original == snapshot
    assert remapped is not original


def test_remap_warns_on_missing_file(make_repo, git) -> None:
    repo = make_repo({"other.py": "x\n"})
    base = git(repo, "rev-parse", "HEAD").strip()
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert any("src/api/routes.py" in w for w in warnings)
    assert model["modules"][1]["interface"][0]["line"] == 12
    assert validate(model) == []


def test_remap_warns_once_per_file(make_repo, git) -> None:
    repo = make_repo({"other.py": "x\n"})
    _, warnings = remap_model(_model(git(repo, "rev-parse", "HEAD").strip()), repo, "HEAD")
    assert len([w for w in warnings if ROUTES_PATH in w]) == 1


def test_remap_warns_when_a_file_changed_by_more_than_insertions(
    make_repo, commit_files, git
) -> None:
    repo = make_repo({ROUTES_PATH: ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: "# h\n" + ROUTES.replace("return row", "return dict(row)")})
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert len(warnings) == 1
    assert ROUTES_PATH in warnings[0] and "approximate" in warnings[0]
    assert model["modules"][1]["interface"][0]["line"] == 13
    assert validate(model) == []


def test_remap_warns_on_a_line_past_the_end_of_the_base_file(make_repo, commit_files, git) -> None:
    repo = make_repo({ROUTES_PATH: ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: "# h\n" + ROUTES})
    stale = _model(base)
    _point_at(stale, ROUTES_PATH, 99, 120)
    model, warnings = remap_model(stale, repo, "HEAD")
    assert any("line 99" in w and ROUTES_PATH in w for w in warnings)
    assert model["modules"][1]["interface"][0]["line"] == 15  # the last line, moved down by one
    assert validate(model) == []


def test_remap_keeps_numbers_when_the_base_file_was_empty(make_repo, commit_files, git) -> None:
    repo = make_repo({ROUTES_PATH: ""})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: ROUTES})
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert any("line 12" in w for w in warnings)
    assert model["modules"][1]["interface"][0]["line"] == 12
    assert model["flows"][0]["steps"][0]["snippet"].startswith("async def create_note")
    assert validate(model) == []


def test_remap_resolves_the_target_to_a_commit_sha(make_repo, commit_files, git) -> None:
    repo = make_repo({ROUTES_PATH: ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    new = commit_files(repo, {ROUTES_PATH: "# h\n" + ROUTES})
    git(repo, "tag", "-a", "v1", "-m", "release")
    for ref in ("v1", "main", new[:10]):
        model, _ = remap_model(_model(base), repo, ref)
        assert model["meta"]["source_commit"] == new


def test_remap_accepts_a_subdirectory_of_the_work_tree(make_repo, commit_files, git) -> None:
    repo = make_repo({ROUTES_PATH: ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: "# h\n" + ROUTES})
    model, warnings = remap_model(_model(base), repo / "src", "HEAD")
    assert warnings == []
    assert model["modules"][1]["interface"][0]["line"] == 13


def test_remap_counts_lines_the_way_an_editor_does(make_repo, commit_files, git) -> None:
    # A form feed (or NEL, or U+2028) inside a line is not a line break to git or an editor,
    # although str.splitlines treats it as one.
    for sep in ("\x0c", "\x1c", "\x85", " "):
        repo = make_repo({ROUTES_PATH: ROUTES.replace("import x", f"import x{sep}# page", 1)})
        base = git(repo, "rev-parse", "HEAD").strip()
        commented = ROUTES.replace("import x", f"import x{sep}# page", 1).replace(
            "async def", "# why\nasync def"
        )
        commit_files(repo, {ROUTES_PATH: "# h\n" + commented})
        model, warnings = remap_model(_model(base), repo, "HEAD")
        assert warnings == [], repr(sep)
        assert model["modules"][1]["interface"][0]["line"] == 14, repr(sep)
        assert model["flows"][0]["steps"][0]["snippet"].startswith("async def create_note")
        assert validate(model) == []


def test_remap_snippet_stays_within_the_schema_limit(make_repo, commit_files, git) -> None:
    lines = [f"line {n}" for n in range(1, 61)]
    repo = make_repo({ROUTES_PATH: "\n".join(lines) + "\n"})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: "# h\n# i\n" + "\n".join(lines) + "\n"})
    wide = _model(base)
    _point_at(wide, ROUTES_PATH, 5, 50)
    model, warnings = remap_model(wide, repo, "HEAD")
    step = model["flows"][0]["steps"][0]
    assert warnings == []
    assert (step["line_start"], step["line_end"]) == (7, 52)
    assert step["snippet"].splitlines() == lines[4 : 4 + MAX_SNIPPET_LINES]
    assert validate(model) == []


def test_remap_snippet_limit_holds_under_the_validators_own_line_count(
    make_repo, commit_files, git
) -> None:
    # The validator counts with str.splitlines, which splits at a form feed. Every file line here
    # holds one, so 30 file lines would read as 60 lines to the validator.
    lines = [f"a{n}\x0cb{n}" for n in range(1, 41)]
    repo = make_repo({ROUTES_PATH: "\n".join(lines) + "\n"})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: "# h\n" + "\n".join(lines) + "\n"})
    wide = _model(base)
    _point_at(wide, ROUTES_PATH, 1, 40)
    model, _ = remap_model(wide, repo, "HEAD")
    snippet = model["flows"][0]["steps"][0]["snippet"]
    assert snippet.startswith("a1\x0cb1\na2")
    assert 0 < len(snippet.splitlines()) <= MAX_SNIPPET_LINES
    assert validate(model) == []


def test_remap_snippet_has_no_carriage_returns(make_repo, commit_files, git) -> None:
    crlf = ROUTES.replace("\n", "\r\n").encode()
    repo = make_repo({ROUTES_PATH: crlf})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: b"# h\r\n" + crlf})
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert warnings == []
    step = model["flows"][0]["steps"][0]
    assert (step["line_start"], step["line_end"]) == (13, 15)
    assert step["snippet"] == (
        "async def create_note(body):\n    row = await db.insert(body)\n    return row"
    )


def test_remap_handles_a_last_line_with_no_newline(make_repo, commit_files, git) -> None:
    unterminated = ROUTES.rstrip("\n")
    repo = make_repo({ROUTES_PATH: unterminated})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: "# h\n" + unterminated})
    model, warnings = remap_model(_model(base), repo, "HEAD")
    step = model["flows"][0]["steps"][0]
    assert warnings == []
    assert (step["line_start"], step["line_end"]) == (13, 15)
    assert step["snippet"].endswith("    return row")
    assert validate(model) == []


def test_remap_leaves_a_step_without_a_snippet_without_one(make_repo, commit_files, git) -> None:
    repo = make_repo({ROUTES_PATH: ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_files(repo, {ROUTES_PATH: "# h\n" + ROUTES})
    bare = _model(base)
    del bare["flows"][0]["steps"][0]["snippet"]
    model, _ = remap_model(bare, repo, "HEAD")
    assert "snippet" not in model["flows"][0]["steps"][0]
    assert model["flows"][0]["steps"][0]["line_start"] == 13


def test_remap_treats_a_non_utf8_file_as_unreadable(make_repo, commit_files, git) -> None:
    repo = make_repo({ROUTES_PATH: b"\xff\xfe" + ROUTES.encode()})
    base = git(repo, "rev-parse", "HEAD").strip()
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert any(ROUTES_PATH in w for w in warnings)
    assert model["modules"][1]["interface"][0]["line"] == 12


def test_remap_rejects_an_invalid_model(make_repo, git) -> None:
    repo = make_repo({"a.py": "x\n"})
    broken = _model(git(repo, "rev-parse", "HEAD").strip())
    del broken["flows"]
    with pytest.raises(ValueError, match="model is invalid"):
        remap_model(broken, repo, "HEAD")
    with pytest.raises(ValueError, match="model is invalid"):
        remap_model([], repo, "HEAD")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["", "0123456789abcdef0123456789abcdef01234567", "-x", "nope"])
def test_remap_rejects_a_source_commit_not_in_history(make_repo, bad: str) -> None:
    repo = make_repo({"a.py": "x\n"})
    with pytest.raises(ValueError, match="meta.source_commit"):
        remap_model(_model(bad), repo, "HEAD")


@pytest.mark.parametrize("bad", ["nope", "-x", "--output=x", ""])
def test_remap_rejects_an_unknown_target_ref(make_repo, git, bad: str) -> None:
    repo = make_repo({"a.py": "x\n"})
    base = git(repo, "rev-parse", "HEAD").strip()
    with pytest.raises(ValueError, match="unknown ref"):
        remap_model(_model(base), repo, bad)


def test_remap_rejects_a_directory_that_is_not_a_work_tree(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(ValueError, match="not inside a git work tree"):
        remap_model(_model("0" * 40), plain, "HEAD")


@pytest.fixture
def windows_text_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Emulate Windows text mode on any OS: ``Path.write_text`` writes CRLF for every LF."""

    def write_text(
        self: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        return self.write_bytes(
            data.replace("\n", "\r\n").encode(encoding or "utf-8", errors or "strict")
        )

    monkeypatch.setattr(Path, "write_text", write_text)


def test_write_model_writes_utf8_bytes_with_no_newline_translation(
    tmp_path: Path, windows_text_mode: None
) -> None:
    model = json.loads(FIXTURE.read_text(encoding="utf-8"))
    model["project"]["tagline"] = "café ✓"
    path = tmp_path / "model.json"
    write_model(path, model)
    data = path.read_bytes()
    assert b"\r" not in data and data.endswith(b"\n")
    assert data == (json.dumps(model, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    assert "café".encode() in data


def test_write_model_unencodable_text_raises_and_leaves_the_file(tmp_path: Path) -> None:
    path = tmp_path / "model.json"
    path.write_bytes(b"keep me")
    model = json.loads(FIXTURE.read_text(encoding="utf-8"))
    model["project"]["tagline"] = "bad \ud800 text"
    with pytest.raises(ValueError, match="UTF-8"):
        write_model(path, model)
    assert path.read_bytes() == b"keep me"


def test_cli_remap(make_repo, commit_files, git, tmp_path: Path) -> None:
    repo = make_repo({"src/api/routes.py": ROUTES})
    path = tmp_path / "model.json"
    path.write_text(json.dumps(_model(git(repo, "rev-parse", "HEAD").strip())))
    commit_files(repo, {"src/api/routes.py": "# h\n" + ROUTES})
    assert main(["remap", "--model", str(path), "--repo", str(repo)]) == 0
    assert json.loads(path.read_text())["modules"][1]["interface"][0]["line"] == 13


def test_cli_remap_prints_warnings_and_rewrites_the_model_bytes_exactly(
    make_repo, git, tmp_path: Path, capsys, windows_text_mode: None
) -> None:
    repo = make_repo({"other.py": "x\n"})
    path = tmp_path / "model.json"
    path.write_bytes(json.dumps(_model(git(repo, "rev-parse", "HEAD").strip())).encode())
    assert main(["remap", "--model", str(path), "--repo", str(repo), "--to", "HEAD"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert list(out) == ["warnings"] and ROUTES_PATH in out["warnings"][0]
    data = path.read_bytes()
    assert b"\r" not in data
    assert json.loads(data)["meta"]["source_commit"] == git(repo, "rev-parse", "HEAD").strip()
    assert data == (json.dumps(json.loads(data), indent=2, ensure_ascii=False) + "\n").encode()


def test_cli_remap_output_validates(make_repo, commit_files, git, tmp_path: Path) -> None:
    repo = make_repo({ROUTES_PATH: ROUTES})
    path = tmp_path / "model.json"
    path.write_text(json.dumps(_model(git(repo, "rev-parse", "HEAD").strip())))
    commit_files(repo, {ROUTES_PATH: "# h\n" + ROUTES})
    assert main(["remap", "--model", str(path), "--repo", str(repo)]) == 0
    assert validate(json.loads(path.read_text())) == []


def _cli_bad_input(
    argv: list[str], capsys: pytest.CaptureFixture[str], needle: str, model: Path | None = None
) -> None:
    before = model.read_bytes() if model is not None else None
    assert main(["remap", *argv]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("remap: ") and needle in captured.err
    assert captured.out == ""
    if model is not None:
        assert model.read_bytes() == before  # a refused remap never touches the model


def _model_file(tmp_path: Path, repo: Path, git: Callable[..., str]) -> Path:
    path = tmp_path / "model.json"
    path.write_text(json.dumps(_model(git(repo, "rev-parse", "HEAD").strip())))
    return path


def test_cli_remap_unknown_target_ref_exits_2(make_repo, git, tmp_path: Path, capsys) -> None:
    repo = make_repo({"a.py": "x\n"})
    path = _model_file(tmp_path, repo, git)
    argv = ["--model", str(path), "--repo", str(repo), "--to", "no-such-ref"]
    _cli_bad_input(argv, capsys, "no-such-ref", path)


def test_cli_remap_source_commit_not_in_history_exits_2(make_repo, tmp_path: Path, capsys) -> None:
    repo = make_repo({"a.py": "x\n"})
    path = tmp_path / "model.json"
    path.write_text(FIXTURE.read_text())  # its source_commit is not a commit of this repo
    _cli_bad_input(["--model", str(path), "--repo", str(repo)], capsys, "meta.source_commit", path)


def test_cli_remap_missing_model_exits_2(make_repo, tmp_path: Path, capsys) -> None:
    repo = make_repo({"a.py": "x\n"})
    _cli_bad_input(["--model", str(tmp_path / "gone.json"), "--repo", str(repo)], capsys, "gone")


@pytest.mark.parametrize("content", [b"{broken", b"", b"\xff\xfe\x00"])
def test_cli_remap_unparseable_model_exits_2_and_names_the_file(
    make_repo, tmp_path: Path, capsys, content: bytes
) -> None:
    repo = make_repo({"a.py": "x\n"})
    path = tmp_path / "model.json"
    path.write_bytes(content)
    _cli_bad_input(["--model", str(path), "--repo", str(repo)], capsys, "model.json", path)


@pytest.mark.parametrize("content", [b"[1]", b"{}", b'{"meta": {}}'])
def test_cli_remap_invalid_model_exits_2(make_repo, tmp_path: Path, capsys, content: bytes) -> None:
    repo = make_repo({"a.py": "x\n"})
    path = tmp_path / "model.json"
    path.write_bytes(content)
    _cli_bad_input(["--model", str(path), "--repo", str(repo)], capsys, "model is invalid", path)


def test_cli_remap_not_a_work_tree_exits_2(tmp_path: Path, capsys) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    path = tmp_path / "model.json"
    path.write_text(FIXTURE.read_text())
    _cli_bad_input(["--model", str(path), "--repo", str(plain)], capsys, "work tree", path)


def test_cli_remap_unencodable_model_exits_2_and_keeps_the_file(
    make_repo, git, tmp_path: Path, capsys
) -> None:
    repo = make_repo({"a.py": "x\n"})
    model = _model(git(repo, "rev-parse", "HEAD").strip())
    model["project"]["tagline"] = "bad \ud800 text"
    path = tmp_path / "model.json"
    path.write_text(json.dumps(model))  # written as a \ud800 escape
    _cli_bad_input(["--model", str(path), "--repo", str(repo)], capsys, "UTF-8", path)


def test_cli_remap_unwritable_model_exits_2(
    make_repo, git, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo({"a.py": "x\n"})
    path = _model_file(tmp_path, repo, git)

    def refuse(self: Path, data: bytes) -> int:
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_bytes", refuse)
    _cli_bad_input(["--model", str(path), "--repo", str(repo)], capsys, "disk full", path)
