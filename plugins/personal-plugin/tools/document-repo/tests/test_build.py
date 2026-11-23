import copy
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from document_repo import build
from document_repo.build import (
    JS_PREFIX,
    _git,
    assemble_model,
    install_template,
    normalize_remote,
    read_json,
    read_object,
    write_explorer_data,
)
from document_repo.cli import main
from document_repo.fsutil import write_bytes_atomic
from document_repo.schema import validate

FIXTURE = Path(__file__).parent / "fixtures" / "sample_model.json"
SYSTEM_KEYS = ("project", "architecture", "flows", "glossary", "paths", "agent_notes")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("git@github.com:owner/repo.git", "https://github.com/owner/repo"),
        ("ssh://git@github.com/owner/repo.git", "https://github.com/owner/repo"),
        ("https://github.com/owner/repo.git", "https://github.com/owner/repo"),
        ("https://x-token:secret@github.com/owner/repo", "https://github.com/owner/repo"),
        ("https://gitea.example.com/a/b/", "https://gitea.example.com/a/b"),
        ("/local/path/repo", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_remote(url, expected) -> None:
    assert normalize_remote(url) == expected


def _run_dir(tmp_path: Path, with_db_record: bool = True) -> Path:
    fixture = json.loads(FIXTURE.read_text())
    run = tmp_path / "run"
    (run / "modules").mkdir(parents=True)
    (run / "modules.final.json").write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "id": "db",
                        "path": "db",
                        "files": ["db/migrations/001_init.sql"],
                        "lines": 1,
                    },
                    {
                        "id": "src-api",
                        "path": "src/api",
                        "files": ["src/api/routes.py"],
                        "lines": 20,
                    },
                ]
            }
        )
    )
    (run / "system.json").write_text(json.dumps({k: fixture[k] for k in SYSTEM_KEYS}))
    mods = {m["id"]: m for m in fixture["modules"]}
    (run / "modules" / "src-api.json").write_text(
        json.dumps(
            {
                "module": mods["src-api"],
                "files": [
                    {
                        "path": "src/api/routes.py",
                        "summary": "Routes.",
                        "callers": ["uvicorn"],
                        "side_effects": ["DB insert"],
                    }
                ],
            }
        )
    )
    if with_db_record:
        (run / "modules" / "db.json").write_text(json.dumps({"module": mods["db"], "files": []}))
    return run


def test_assemble_full(make_repo, tmp_path: Path, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    git(repo, "remote", "add", "origin", "git@github.com:example/demo.git")
    model, notes = assemble_model(_run_dir(tmp_path), repo, now="2026-11-22T00:00:00+00:00")
    assert validate(model) == []
    assert list(model) == [
        "meta",
        "project",
        "architecture",
        "modules",
        "flows",
        "glossary",
        "paths",
        "agent_notes",
    ]
    assert model["meta"]["repo_url"] == "https://github.com/example/demo"
    assert model["meta"]["repo_name"] == "repo"
    assert model["meta"]["source_commit"] == git(repo, "rev-parse", "HEAD").strip()
    assert [n["path"] for n in notes] == ["src/api/routes.py"]


def test_assemble_stub_for_missing_record(make_repo, tmp_path: Path) -> None:
    model, _ = assemble_model(_run_dir(tmp_path, with_db_record=False), make_repo({"a.py": "x\n"}))
    db = next(m for m in model["modules"] if m["id"] == "db")
    assert db["status"] == "not_analyzed" and db["path"] == "db"
    assert validate(model) == []


def test_assemble_uses_base_model_for_untouched_modules(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path, with_db_record=False)
    (run / "system.json").unlink()
    base = json.loads(FIXTURE.read_text())
    base["modules"][0]["name"] = "From base"
    model, _ = assemble_model(run, make_repo({"a.py": "x\n"}), base_model=base)
    assert next(m for m in model["modules"] if m["id"] == "db")["name"] == "From base"
    assert model["project"] == base["project"]


def test_assemble_without_system_or_base_fails(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path)
    (run / "system.json").unlink()
    with pytest.raises(ValueError, match="system.json"):
        assemble_model(run, make_repo({"a.py": "x\n"}))


def test_write_explorer_data(tmp_path: Path) -> None:
    model = json.loads(FIXTURE.read_text())
    state = write_explorer_data(model, tmp_path / "data")
    js = (tmp_path / "data" / "model.js").read_text()
    assert js.startswith("window.PROJECT_MODEL = ") and js.endswith(";\n")
    assert json.loads(js[len("window.PROJECT_MODEL = ") : -2]) == model
    raw = (tmp_path / "data" / "model.json").read_bytes()
    assert state["model_hash"] == hashlib.sha256(raw).hexdigest()
    assert json.loads((tmp_path / "data" / "state.json").read_text()) == state
    assert state["source_commit"] == model["meta"]["source_commit"]


def test_write_explorer_data_rejects_invalid(tmp_path: Path) -> None:
    model = json.loads(FIXTURE.read_text())
    del model["project"]
    with pytest.raises(ValueError, match="project: missing"):
        write_explorer_data(model, tmp_path / "data")
    assert not (tmp_path / "data").exists()


def test_install_template_keeps_existing_data(tmp_path: Path) -> None:
    template = tmp_path / "tpl"
    (template / "vendor").mkdir(parents=True)
    (template / "index.html").write_text("<html></html>")
    (template / "vendor" / "m.js").write_text("//m")
    (template / "data").mkdir()
    (template / "data" / "model.js").write_text("TEMPLATE")
    explorer = tmp_path / "repo" / "explorer"
    _write_marker(explorer)
    (explorer / "data" / "model.js").write_text("REAL")
    install_template(template, explorer)
    assert (explorer / "index.html").exists() and (explorer / "vendor" / "m.js").exists()
    assert (explorer / "data" / "model.js").read_text() == "REAL"


def _write_marker(explorer: Path, model: bytes = b"{}\n") -> None:
    """Make ``explorer`` one a build made: model.json plus a state.json that hashes it."""
    (explorer / "data").mkdir(parents=True, exist_ok=True)
    (explorer / "data" / "model.json").write_bytes(model)
    state = {
        "source_commit": "0" * 40,
        "schema_version": 1,
        "model_hash": hashlib.sha256(model).hexdigest(),
        "generated_at": "2026-01-01T00:00:00Z",
    }
    (explorer / "data" / "state.json").write_text(json.dumps(state))


def _tiny_template(tmp_path: Path) -> Path:
    template = tmp_path / "tpl"
    (template / "vendor").mkdir(parents=True)
    (template / "index.html").write_text("<html></html>")
    (template / "app.js").write_text("// app")
    (template / "vendor" / "m.js").write_text("//m")
    return template


def test_template_files_lists_what_install_copies(tmp_path: Path) -> None:
    template = _tiny_template(tmp_path)
    (template / "data").mkdir()
    (template / "data" / "model.js").write_text("TEMPLATE")
    (template / "vendor" / "data").mkdir()
    (template / "vendor" / "data" / "x.js").write_text("deep")
    assert build.template_files(template) == {
        "index.html",
        "app.js",
        "vendor/m.js",
        "vendor/data/x.js",
    }
    explorer = tmp_path / "explorer"
    install_template(template, explorer)
    copied = {p.relative_to(explorer).as_posix() for p in explorer.rglob("*") if p.is_file()}
    assert copied == build.template_files(template)


@pytest.mark.parametrize(
    "rel,content",
    [
        ("app.py", "print('mine')\n"),  # a file the template does not have
        ("app.js", "// my own app\n"),  # a template name with the target's own content
        ("vendor/lib/x.js", "x\n"),
    ],
)
def test_install_template_refuses_a_directory_it_did_not_make(
    tmp_path: Path, rel: str, content: str
) -> None:
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "repo" / "explorer"
    (explorer / rel).parent.mkdir(parents=True, exist_ok=True)
    (explorer / rel).write_text(content)
    with pytest.raises(ValueError, match="not made by document-repo"):
        install_template(template, explorer)
    assert (explorer / rel).read_text() == content
    assert not (explorer / "index.html").exists()


def test_install_template_reinstalls_over_its_own_directory(tmp_path: Path) -> None:
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "repo" / "explorer"
    install_template(template, explorer)
    # A half-made explorer (template files only, no data yet) is ours.
    install_template(template, explorer)
    # With a trusted state.json, an explorer from an older template is ours too, and the data
    # files a build writes (and Markdown) may sit in data/.
    (explorer / "old.js").write_text("// removed from the template since")
    (explorer / "app.js").write_text("// older app")
    _write_marker(explorer)
    (explorer / "data" / "model.js").write_text("var m;")
    (explorer / "data" / "run-report.md").write_text("# r")
    install_template(template, explorer)
    assert (explorer / "app.js").read_text() == "// app"


def test_is_our_explorer_trusts_what_write_explorer_data_writes(tmp_path: Path) -> None:
    model = json.loads(FIXTURE.read_text())
    write_explorer_data(model, tmp_path / "explorer" / "data")
    assert build.is_our_explorer(tmp_path / "explorer")
    (tmp_path / "explorer" / "data" / "model.json").write_text("{}\n")
    assert not build.is_our_explorer(tmp_path / "explorer"), "model edited after the build"
    assert not build.is_our_explorer(tmp_path / "absent")


@pytest.mark.parametrize(
    "state",
    [
        {"saved": "ui state"},
        "extra-key",
        "missing-key",
        "wrong-hash",
        "not-an-object",
        "not-json",
    ],
)
def test_is_our_explorer_rejects_a_state_a_build_did_not_write(tmp_path: Path, state) -> None:
    explorer = tmp_path / "explorer"
    _write_marker(explorer)
    path = explorer / "data" / "state.json"
    good = json.loads(path.read_text())
    if state == "extra-key":
        path.write_text(json.dumps({**good, "saved": 1}))
    elif state == "missing-key":
        path.write_text(json.dumps({k: v for k, v in good.items() if k != "schema_version"}))
    elif state == "wrong-hash":
        path.write_text(json.dumps({**good, "model_hash": "0" * 64}))
    elif state == "not-an-object":
        path.write_text(json.dumps(list(good)))
    elif state == "not-json":
        path.write_bytes(b"\xff{")
    else:
        path.write_text(json.dumps(state))
    assert not build.is_our_explorer(explorer)


def test_install_template_refuses_behind_a_foreign_state(tmp_path: Path) -> None:
    # r2/p1: the target's own state.json does not make its explorer/ ours.
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "explorer"
    (explorer / "data").mkdir(parents=True)
    (explorer / "app.js").write_text("export function realCode(){return 42}\n")
    (explorer / "data" / "state.json").write_text('{"saved":"ui state"}\n')
    with pytest.raises(ValueError, match="not made by document-repo"):
        install_template(template, explorer)
    assert (explorer / "app.js").read_text() == "export function realCode(){return 42}\n"


@pytest.mark.parametrize("trusted", [False, True])
def test_install_template_refuses_other_files_in_data(tmp_path: Path, trusted: bool) -> None:
    # r2/p3 (no marker) and r2/p4 (a stray next to a build's data).
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "explorer"
    if trusted:
        _write_marker(explorer)
    (explorer / "data").mkdir(parents=True, exist_ok=True)
    (explorer / "data" / "loader.js").write_text("export const f = () => 1;\n")
    with pytest.raises(ValueError, match="data/loader.js"):
        install_template(template, explorer)
    assert not (explorer / "index.html").exists()


@pytest.mark.parametrize("trusted", [False, True])
@pytest.mark.parametrize("where", ["vendor", "data", "."])
def test_install_template_refuses_symlinks(tmp_path: Path, trusted: bool, where: str) -> None:
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "explorer"
    explorer.mkdir()
    if trusted:
        _write_marker(explorer)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.js").write_text("keep")
    link = explorer / where / "lib" if where != "." else explorer / "lib"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        install_template(template, explorer)
    assert sorted(p.name for p in outside.iterdir()) == ["keep.js"]


def test_install_template_refuses_a_symlinked_explorer_dir(tmp_path: Path) -> None:
    template = _tiny_template(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    explorer = tmp_path / "explorer"
    explorer.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        install_template(template, explorer)
    assert list(outside.iterdir()) == []


def test_install_template_refuses_a_vendor_symlink_the_template_would_write_through(
    tmp_path: Path,
) -> None:
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "explorer"
    _write_marker(explorer)
    outside = tmp_path / "outside"
    outside.mkdir()
    (explorer / "vendor").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        install_template(template, explorer)
    assert list(outside.iterdir()) == []


def test_cli_build_refuses_a_foreign_explorer(tmp_path: Path, capsys) -> None:
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "explorer"
    explorer.mkdir()
    (explorer / "app.js").write_text("// mine\n")
    model = tmp_path / "model.json"
    model.write_text(FIXTURE.read_text())
    code = main(
        [
            "build",
            "--model",
            str(model),
            "--explorer-dir",
            str(explorer),
            "--template",
            str(template),
        ]
    )
    assert code == 2 and "not made by document-repo" in capsys.readouterr().err
    assert (explorer / "app.js").read_text() == "// mine\n"
    assert not (explorer / "data").exists()


def test_cli_assemble_and_build(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path)
    repo = make_repo({"a.py": "x\n"})
    assert main(["assemble", "--run-dir", str(run), "--repo", str(repo)]) == 0
    assert (run / "model.json").exists() and (run / "file-notes.json").exists()
    assert (
        main(
            [
                "build",
                "--model",
                str(run / "model.json"),
                "--explorer-dir",
                str(tmp_path / "ex"),
                "--validate-only",
            ]
        )
        == 0
    )
    assert not (tmp_path / "ex").exists()
    tpl = tmp_path / "tpl"
    tpl.mkdir()
    (tpl / "index.html").write_text("x")
    assert (
        main(
            [
                "build",
                "--model",
                str(run / "model.json"),
                "--explorer-dir",
                str(tmp_path / "ex"),
                "--template",
                str(tpl),
            ]
        )
        == 0
    )
    assert (tmp_path / "ex" / "index.html").exists()
    assert (tmp_path / "ex" / "data" / "state.json").exists()


def test_cli_build_invalid_exits_1(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "m.json"
    bad.write_text("{}")
    assert (
        main(
            [
                "build",
                "--model",
                str(bad),
                "--explorer-dir",
                str(tmp_path / "ex"),
                "--validate-only",
            ]
        )
        == 1
    )
    assert "meta: missing" in capsys.readouterr().err


# --- credentials never reach the model -----------------------------------------------------------

SECRET = "s3cr3t-t0ken"


@pytest.mark.parametrize(
    "url,expected",
    [
        # Credentials: an unescaped "@" in the password must not leave a fragment behind.
        ("https://user:p@ss@github.com/o/r", "https://github.com/o/r"),
        (f"https://{SECRET}@github.com/o/r.git", "https://github.com/o/r"),
        (f"ssh://user:{SECRET}@host.example/o/r.git", "https://host.example/o/r"),
        # A "/" in the password moves the authority boundary; guessing would leak, so refuse.
        (f"https://user:pa/{SECRET}@github.com/o/r", None),
        (f"https://u:12/{SECRET}@host/o/r", None),
        # Query strings and fragments can carry tokens.
        (f"https://github.com/o/r?token={SECRET}#frag", "https://github.com/o/r"),
        (f"git@github.com:o/r.git?token={SECRET}", None),
        # Other shapes a remote takes.
        ("ssh://git@host.example:2222/o/r.git", "https://host.example/o/r"),
        ("deploy@gitea.example.com:a/b.git", "https://gitea.example.com/a/b"),
        ("git@host.example:/srv/o/r.git", "https://host.example/srv/o/r"),
        ("git://github.com/o/r.git", "https://github.com/o/r"),
        # The scheme survives for http (a self-hosted forge without TLS); SSH and git become https.
        ("http://github.com/o/r", "http://github.com/o/r"),
        ("http://localhost:3000/a/b.git", "http://localhost:3000/a/b"),
        ("HTTP://Host.Example/o/r", "http://host.example/o/r"),
        (f"http://u:{SECRET}@localhost:3000/a/b", "http://localhost:3000/a/b"),
        (f"http://h.example/o/r?token={SECRET}#frag", "http://h.example/o/r"),
        (f"http://user:pa/{SECRET}@h.example/o/r", None),
        ("git://host.example:9418/o/r.git", "https://host.example/o/r"),
        ("ssh://git@host.example:22/o/r.git", "https://host.example/o/r"),
        ("https://h.example:8443/o/r.git", "https://h.example:8443/o/r"),
        # Git output decoded with surrogateescape: bytes that are not UTF-8 never reach the model.
        ("https://h.example/o/r\udcff", None),
        ("git@h.example:o/r\udcff", None),
        ("HTTPS://GitHub.com/o/r", "https://github.com/o/r"),
        ("https://gitea.example.com:3000/a/b.git", "https://gitea.example.com:3000/a/b"),
        ("  git@github.com:owner/repo.git\n", "https://github.com/owner/repo"),
        # Not a browsable remote.
        ("https://github.com:notaport/o/r", None),
        ("https://github.com/o/r with space", None),
        ("https://[::1]/o/r", None),
        ("https:///o/r", None),
        ("https://github.com", None),
        ("https://github.com/.git", None),
        ("file:///srv/git/r.git", None),
        ("C:\\repo", None),
        ("../relative/repo", None),
    ],
)
def test_normalize_remote_edge_cases(url: str, expected: str | None) -> None:
    assert normalize_remote(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        f"https://{SECRET}@h.example/o/r",
        f"https://u:{SECRET}@h.example/o/r",
        f"https://u:{SECRET}@h.example:8443/o/r.git",
        f"https://u:x@{SECRET}@h.example/o/r",
        f"https://u:{SECRET}/x@h.example/o/r",
        f"http://u:{SECRET}@h.example/o/r/",
        f"http://u:{SECRET}@localhost:3000/o/r.git",
        f"http://u:/{SECRET}#@h.example:3000/o/r",
        f"http://localhost:3000/o/r?token={SECRET}",
        f"ssh://u:{SECRET}@h.example:2222/o/r",
        f"u:{SECRET}@h.example:o/r",
        f"git@h.example:o/r?{SECRET}",
        f"https://h.example/o/r?token={SECRET}",
        f"https://h.example/o/r#{SECRET}",
        f"https://h.example/o/{SECRET}@r",
        # A "/" in the password ends the authority early; the "@" that follows lands in the
        # path, query or fragment, where urlsplit no longer sees it as a delimiter.
        f"https://u:/{SECRET}#@h.example/o/r",
        f"https://u:/{SECRET}?@h.example:8443/o/r",
        f"git://tok:/:{SECRET}#\\@h.example:22/o/r",
        f"https://u:abc@{SECRET}/x@h.example/o/r",
        f"https://u:12#{SECRET}@h.example/o/r",
    ],
)
def test_normalize_remote_never_returns_a_secret(url: str) -> None:
    assert SECRET not in (normalize_remote(url) or "")


def test_assemble_strips_remote_credentials(make_repo, tmp_path: Path, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    git(repo, "remote", "add", "origin", f"https://x-token:{SECRET}@github.com/example/demo.git")
    run = _run_dir(tmp_path)
    assert main(["assemble", "--run-dir", str(run), "--repo", str(repo)]) == 0
    text = (run / "model.json").read_text()
    assert SECRET not in text
    assert json.loads(text)["meta"]["repo_url"] == "https://github.com/example/demo"


# --- assemble_model ------------------------------------------------------------------------------


def _base_with(**changes: Any) -> dict[str, Any]:
    base = json.loads(FIXTURE.read_text())
    base.update(changes)
    return base


def _module(model: dict[str, Any], module_id: str) -> dict[str, Any]:
    return next(m for m in model["modules"] if m["id"] == module_id)


def _write_final(run: Path, ids: list[str]) -> None:
    specs = [{"id": i, "path": i, "files": [], "lines": 1} for i in ids]
    (run / "modules.final.json").write_text(json.dumps({"modules": specs}))


# --- module precedence and order -----------------------------------------------------------------
# A fresh record beats the base model, the base model beats a stub, a module that is not in
# modules.final.json is gone, and the output is sorted by id whatever order final lists.


def test_assemble_fresh_record_beats_a_different_base_entry(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path)  # src-api has a fresh record
    base = _base_with()
    stale = _module(base, "src-api")
    stale["name"] = "Stale base name"
    record = json.loads((run / "modules" / "src-api.json").read_text())["module"]
    assert stale["name"] != record["name"]
    model, notes = assemble_model(run, make_repo({"a.py": "x\n"}), base_model=base)
    assert _module(model, "src-api") == record
    assert [n["path"] for n in notes] == ["src/api/routes.py"]  # notes come from the record


def test_assemble_drops_base_modules_that_final_no_longer_lists(make_repo, tmp_path: Path) -> None:
    base = _base_with()
    retired = copy.deepcopy(base["modules"][0])
    retired.update(id="retired", name="Retired", path="retired")
    base["modules"].append(retired)
    model, _ = assemble_model(_run_dir(tmp_path), make_repo({"a.py": "x\n"}), base_model=base)
    assert [m["id"] for m in model["modules"]] == ["db", "src-api"]


def test_assemble_sorts_modules_by_id_whatever_the_order_of_final(
    make_repo, tmp_path: Path
) -> None:
    run = _run_dir(tmp_path)
    _write_final(run, ["src-api", "db"])
    model, _ = assemble_model(run, make_repo({"a.py": "x\n"}))
    assert [m["id"] for m in model["modules"]] == ["db", "src-api"]


# --- assemble_model input validation -------------------------------------------------------------

UNSAFE_IDS = ["../x", "a/b", "/abs", "", "X", "db\n", "db.json", "-a", "a--b", "a b", "a\\b"]


@pytest.mark.parametrize("bad_id", UNSAFE_IDS)
def test_assemble_rejects_an_unsafe_id_in_final_before_using_it_in_a_path(
    make_repo, tmp_path: Path, bad_id: str
) -> None:
    run = _run_dir(tmp_path)
    _write_final(run, [bad_id])
    # What "../x" would read if the id reached a path. It must never be read: the error has to
    # be about the id, not about this file.
    (run / "x.json").write_text("{not json")
    with pytest.raises(ValueError, match=r"modules\.final\.json: invalid module id"):
        assemble_model(run, make_repo({"a.py": "x\n"}))


@pytest.mark.parametrize(
    "modules,message",
    [
        (None, "base model: modules must be a list"),
        ("db", "base model: modules must be a list"),
        ({"id": "db"}, "base model: modules must be a list"),
        ([1], "base model: modules must be a list of objects with a string id"),
        ([None], "base model: modules must be a list of objects with a string id"),
        ([{"name": "x"}], "base model: modules must be a list of objects with a string id"),
        ([{"id": 5}], "base model: modules must be a list of objects with a string id"),
        ([{"id": "../x"}], "base model: invalid module id"),
        ([{"id": "ok"}, {"id": "Bad Id"}], "base model: invalid module id"),
    ],
)
def test_assemble_rejects_malformed_base_modules(
    make_repo, tmp_path: Path, modules: Any, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        assemble_model(
            _run_dir(tmp_path), make_repo({"a.py": "x\n"}), base_model=_base_with(modules=modules)
        )


def test_assemble_rejects_a_base_model_without_modules(make_repo, tmp_path: Path) -> None:
    base = _base_with()
    del base["modules"]
    with pytest.raises(ValueError, match="base model: missing modules"):
        assemble_model(_run_dir(tmp_path), make_repo({"a.py": "x\n"}), base_model=base)


def test_assemble_still_accepts_a_base_model_with_an_empty_module_list(
    make_repo, tmp_path: Path
) -> None:
    model, _ = assemble_model(
        _run_dir(tmp_path, with_db_record=False),
        make_repo({"a.py": "x\n"}),
        base_model=_base_with(modules=[]),
    )
    assert _module(model, "db")["status"] == "not_analyzed"


# --- git output that is not UTF-8 ----------------------------------------------------------------


def _set_origin_bytes(repo: Path, url: bytes) -> None:
    with (repo / ".git" / "config").open("ab") as config:
        config.write(b'[remote "origin"]\n\turl = ' + url + b"\n")


def test_git_helper_decodes_with_surrogateescape(make_repo) -> None:
    repo = make_repo({"a.py": "x\n"})
    _set_origin_bytes(repo, b"https://h.example/o/r\xff")
    assert _git(repo, "remote", "get-url", "origin") == "https://h.example/o/r\udcff"


def test_assemble_survives_a_remote_that_is_not_utf8(make_repo, tmp_path: Path) -> None:
    repo = make_repo({"a.py": "x\n"})
    _set_origin_bytes(repo, b"https://h.example/o/r\xff")
    model, _ = assemble_model(_run_dir(tmp_path), repo)
    assert model["meta"]["repo_url"] is None
    write_explorer_data(model, tmp_path / "data")  # the model can be encoded


def test_assemble_repo_name_never_carries_a_lone_surrogate(
    make_repo, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo({"a.py": "x\n"})
    real_git = build._git

    def fake_git(where: Path, *args: str) -> str | None:
        if args == ("rev-parse", "--show-toplevel"):
            return "/srv/re\udcffpo"
        return real_git(where, *args)

    monkeypatch.setattr(build, "_git", fake_git)
    model, _ = assemble_model(_run_dir(tmp_path), repo)
    assert model["meta"]["repo_name"] == "re\ufffdpo"
    write_explorer_data(model, tmp_path / "data")


def test_assemble_defaults_generated_at_to_utc_now(make_repo, tmp_path: Path) -> None:
    model, _ = assemble_model(_run_dir(tmp_path), make_repo({"a.py": "x\n"}))
    stamp = datetime.fromisoformat(model["meta"]["generated_at"])
    assert stamp.utcoffset() is not None and stamp.utcoffset().total_seconds() == 0


def test_assemble_names_the_repo_after_its_work_tree_root(make_repo, tmp_path: Path) -> None:
    repo = make_repo({"sub/a.py": "x\n"})
    model, _ = assemble_model(_run_dir(tmp_path), repo / "sub")
    assert model["meta"]["repo_name"] == "repo"


def test_assemble_outside_a_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A temp directory inside some repository must not be mistaken for a work tree.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    plain = tmp_path / "plain"
    plain.mkdir()
    model, _ = assemble_model(_run_dir(tmp_path), plain)
    assert model["meta"]["source_commit"] == ""
    assert model["meta"]["repo_name"] == "plain"
    assert model["meta"]["repo_url"] is None
    assert validate(model) == []


def test_assemble_base_model_must_carry_the_system_sections(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path)
    (run / "system.json").unlink()
    base = json.loads(FIXTURE.read_text())
    del base["glossary"]
    with pytest.raises(ValueError, match="base model: missing glossary"):
        assemble_model(run, make_repo({"a.py": "x\n"}), base_model=base)


def _corrupt(run: Path, name: str, content: str) -> None:
    (run / name).write_text(content, encoding="utf-8")


@pytest.mark.parametrize(
    "name,content,message",
    [
        ("modules.final.json", "{not json", r"modules\.final\.json: .*[Ee]xpect"),
        ("modules.final.json", "[]", "modules.final.json: expected a JSON object"),
        ("modules.final.json", "{}", "modules.final.json: missing modules"),
        ("modules.final.json", '{"modules": [{"id": "db"}]}', "string id and path"),
        ("modules.final.json", '{"modules": ["db"]}', "string id and path"),
        ("modules.final.json", '{"modules": [{"path": "db"}]}', "string id and path"),
        ("modules.final.json", '{"modules": [{"id": 5, "path": "db"}]}', "string id and path"),
        ("modules.final.json", '{"modules": [{"id": "db", "path": 5}]}', "string id and path"),
        ("modules.final.json", '{"modules": {"id": "db"}}', "string id and path"),
        ("system.json", '{"project": {}}', "system.json: missing architecture"),
        ("modules/db.json", "{", r"db\.json: "),
        ("modules/db.json", '{"files": []}', "db.json: missing module"),
        ("modules/db.json", '{"module": []}', "db.json: module.id must be 'db'"),
        ("modules/db.json", '{"module": {"id": "other"}}', "db.json: module.id must be 'db'"),
        ("modules/db.json", '{"module": {"id": "db"}, "files": "x"}', "db.json: files must be"),
    ],
)
def test_assemble_rejects_malformed_run_files(
    make_repo, tmp_path: Path, name: str, content: str, message: str
) -> None:
    run = _run_dir(tmp_path)
    _corrupt(run, name, content)
    with pytest.raises(ValueError, match=message):
        assemble_model(run, make_repo({"a.py": "x\n"}))


def test_assemble_rejects_non_utf8_run_file(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path)
    (run / "system.json").write_bytes(b"\xff\xfe\x00")
    with pytest.raises(ValueError, match=r"system\.json: "):
        assemble_model(run, make_repo({"a.py": "x\n"}))


def test_read_json_and_read_object(tmp_path: Path) -> None:
    target = tmp_path / "x.json"
    target.write_text('{"a": 1}')
    assert read_json(target) == {"a": 1}
    assert read_object(target, "a") == {"a": 1}
    with pytest.raises(ValueError, match="x.json: missing b, c"):
        read_object(target, "b", "c")
    target.write_text("[1]")
    assert read_json(target) == [1]
    with pytest.raises(ValueError, match="expected a JSON object"):
        read_object(target)
    with pytest.raises(OSError):
        read_json(tmp_path / "absent.json")


# --- write_explorer_data -------------------------------------------------------------------------


def test_write_explorer_data_is_deterministic_and_keeps_non_ascii(tmp_path: Path) -> None:
    model = json.loads(FIXTURE.read_text())
    model["project"]["tagline"] = "Notes, naïvely — ✓ 😀"
    first = write_explorer_data(model, tmp_path / "a")
    second = write_explorer_data(model, tmp_path / "b")
    assert first == second
    js = (tmp_path / "a" / "model.js").read_text(encoding="utf-8")
    assert json.loads(js[len("window.PROJECT_MODEL = ") : -2]) == model
    assert json.loads((tmp_path / "a" / "model.json").read_text(encoding="utf-8")) == model


EXPLORER_FILES = ("model.json", "model.js", "state.json")


def _model_with_tagline(text: str) -> dict[str, Any]:
    model = json.loads(FIXTURE.read_text())
    model["project"]["tagline"] = text
    return model


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


@pytest.mark.parametrize("name", EXPLORER_FILES)
def test_write_explorer_data_writes_bytes_with_no_newline_translation(
    tmp_path: Path, windows_text_mode: None, name: str
) -> None:
    write_explorer_data(json.loads(FIXTURE.read_text()), tmp_path)
    data = (tmp_path / name).read_bytes()
    assert b"\r" not in data
    assert data.endswith(b"\n")


def test_write_explorer_data_hashes_the_bytes_on_disk(
    tmp_path: Path, windows_text_mode: None
) -> None:
    model = json.loads(FIXTURE.read_text())
    state = write_explorer_data(model, tmp_path)
    on_disk = (tmp_path / "model.json").read_bytes()
    assert state["model_hash"] == hashlib.sha256(on_disk).hexdigest()
    assert on_disk == (json.dumps(model, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    assert json.loads((tmp_path / "state.json").read_bytes()) == state


def test_write_explorer_data_unencodable_text_writes_nothing(tmp_path: Path) -> None:
    out = tmp_path / "data"
    with pytest.raises(ValueError):
        write_explorer_data(_model_with_tagline("bad \ud800 text"), out)
    assert not out.exists()


def test_write_explorer_data_unencodable_text_error_says_why(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="UTF-8") as excinfo:
        write_explorer_data(_model_with_tagline("bad \ud800 text"), tmp_path / "data")
    assert "surrogate" in str(excinfo.value)


def test_write_explorer_data_unencodable_text_leaves_existing_files_alone(tmp_path: Path) -> None:
    out = tmp_path / "data"
    out.mkdir()
    before = {name: b"previous " + name.encode() for name in EXPLORER_FILES}
    for name, data in before.items():
        (out / name).write_bytes(data)
    with pytest.raises(ValueError):
        write_explorer_data(_model_with_tagline("bad \ud800 text"), out)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_write_explorer_data_failed_replace_keeps_old_files_and_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "data"
    out.mkdir()
    before = {name: b"previous " + name.encode() for name in EXPLORER_FILES}
    for name, data in before.items():
        (out / name).write_bytes(data)

    def refuse(src: str, dst: str) -> None:
        raise OSError("disk says no")

    monkeypatch.setattr(os, "replace", refuse)
    with pytest.raises(OSError, match="disk says no"):
        write_explorer_data(_model_with_tagline("fine"), out)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_write_bytes_atomic_replaces_the_file(tmp_path: Path) -> None:
    path = tmp_path / "f.json"
    path.write_bytes(b"old")
    write_bytes_atomic(path, b"new bytes")
    assert path.read_bytes() == b"new bytes"
    assert [p.name for p in tmp_path.iterdir()] == ["f.json"]


def test_write_bytes_atomic_creates_a_new_file(tmp_path: Path) -> None:
    path = tmp_path / "new.json"
    write_bytes_atomic(path, b"fresh")
    assert path.read_bytes() == b"fresh"
    assert [p.name for p in tmp_path.iterdir()] == ["new.json"]


needs_posix_modes = pytest.mark.skipif(
    sys.platform == "win32",
    reason="os.chmod on Windows only toggles the read-only flag, so st_mode never reads back 0o644",
)


@needs_posix_modes
def test_write_bytes_atomic_keeps_an_existing_file_mode(tmp_path: Path) -> None:
    path = tmp_path / "f.json"
    path.write_bytes(b"old")
    path.chmod(0o644)
    write_bytes_atomic(path, b"new")
    assert path.stat().st_mode & 0o777 == 0o644


def test_write_bytes_atomic_failure_leaves_original_and_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "f.json"
    path.write_bytes(b"original \x00\xff bytes")
    before = path.read_bytes()

    def refuse(src: str, dst: str) -> None:
        raise OSError("replace refused")

    monkeypatch.setattr(os, "replace", refuse)
    with pytest.raises(OSError, match="replace refused"):
        write_bytes_atomic(path, b"replacement")
    assert path.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["f.json"]


def test_write_bytes_atomic_no_temp_created_still_raises_and_keeps_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "f.json"
    path.write_bytes(b"original")

    def no_temp(*args: object, **kwargs: object) -> None:
        raise OSError("no space for a temp file")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", no_temp)
    with pytest.raises(OSError, match="no space"):
        write_bytes_atomic(path, b"replacement")
    assert path.read_bytes() == b"original"
    assert [p.name for p in tmp_path.iterdir()] == ["f.json"]


def test_write_bytes_atomic_failure_before_replace_removes_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "f.json"
    path.write_bytes(b"original")

    def fail_fsync(fd: int) -> None:
        raise OSError("fsync failed")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="fsync failed"):
        write_bytes_atomic(path, b"replacement")
    assert path.read_bytes() == b"original"
    assert [p.name for p in tmp_path.iterdir()] == ["f.json"]


def test_model_js_is_ascii_and_model_json_keeps_the_text(tmp_path: Path) -> None:
    text = "line\u2028sep\u2029para, naïve — ✓ 😀"
    model = _model_with_tagline(text)
    write_explorer_data(model, tmp_path)
    js = (tmp_path / "model.js").read_bytes()
    assert js.isascii()
    payload = js.decode("ascii")
    # U+2028 and U+2029 end a line in a JavaScript string literal before ES2019.
    assert "\u2028" not in payload and "\\u2028" in payload
    assert json.loads(payload[len(JS_PREFIX) : -2]) == model
    assert text in (tmp_path / "model.json").read_text(encoding="utf-8")


# --- install_template ----------------------------------------------------------------------------


def test_install_template_skips_only_the_top_level_data_dir(tmp_path: Path) -> None:
    template = tmp_path / "tpl"
    (template / "vendor" / "lib" / "data").mkdir(parents=True)
    (template / "vendor" / "lib" / "data" / "x.js").write_text("//x")
    (template / "data").mkdir()
    (template / "data" / "model.js").write_text("TEMPLATE")
    explorer = tmp_path / "explorer"
    install_template(template, explorer)
    assert (explorer / "vendor" / "lib" / "data" / "x.js").read_text() == "//x"
    assert not (explorer / "data").exists()


def test_install_template_overwrites_stale_app_files(tmp_path: Path) -> None:
    template = tmp_path / "tpl"
    template.mkdir()
    (template / "index.html").write_text("new")
    explorer = tmp_path / "explorer"
    _write_marker(explorer)  # a build made this explorer
    (explorer / "index.html").write_text("old")
    install_template(template, explorer)
    assert (explorer / "index.html").read_text() == "new"


# --- CLI -----------------------------------------------------------------------------------------


def test_cli_assemble_invalid_model_exits_1_and_still_writes(
    make_repo, tmp_path: Path, capsys
) -> None:
    run = _run_dir(tmp_path)
    system = json.loads((run / "system.json").read_text())
    system["paths"][0]["steps"][0]["ref_id"] = "../escape.md"
    (run / "system.json").write_text(json.dumps(system))
    repo = make_repo({"a.py": "x\n"})
    assert main(["assemble", "--run-dir", str(run), "--repo", str(repo)]) == 1
    assert "invalid doc path" in capsys.readouterr().err
    assert (run / "model.json").exists() and (run / "file-notes.json").exists()


def test_cli_assemble_uses_base_model(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path, with_db_record=False)
    (run / "system.json").unlink()
    base_path = tmp_path / "base.json"
    base = json.loads(FIXTURE.read_text())
    base_path.write_text(json.dumps(base))
    repo = make_repo({"a.py": "x\n"})
    args = ["assemble", "--run-dir", str(run), "--repo", str(repo), "--base-model", str(base_path)]
    assert main(args) == 0
    assert json.loads((run / "model.json").read_text())["project"] == base["project"]


def test_cli_assemble_bad_input_exits_2(make_repo, tmp_path: Path, capsys) -> None:
    repo = make_repo({"a.py": "x\n"})
    run = _run_dir(tmp_path)
    (run / "system.json").unlink()
    assert main(["assemble", "--run-dir", str(run), "--repo", str(repo)]) == 2
    assert "system.json" in capsys.readouterr().err
    assert not (run / "model.json").exists()
    missing_run = tmp_path / "nope"
    assert main(["assemble", "--run-dir", str(missing_run), "--repo", str(repo)]) == 2
    assert "modules.final.json" in capsys.readouterr().err
    assert main(["assemble", "--run-dir", str(run), "--repo", str(tmp_path / "gone")]) == 2
    assert "is not a directory" in capsys.readouterr().err


def test_cli_assemble_bad_base_model_exits_2(make_repo, tmp_path: Path, capsys) -> None:
    repo = make_repo({"a.py": "x\n"})
    run = _run_dir(tmp_path)
    base = tmp_path / "base.json"
    base.write_text("[1]")
    args = ["assemble", "--run-dir", str(run), "--repo", str(repo), "--base-model", str(base)]
    assert main(args) == 2
    assert "base.json: expected a JSON object" in capsys.readouterr().err


def test_cli_assemble_bad_ids_exit_2_and_name_the_file(make_repo, tmp_path: Path, capsys) -> None:
    repo = make_repo({"a.py": "x\n"})
    run = _run_dir(tmp_path)
    _write_final(run, ["../x"])
    assert main(["assemble", "--run-dir", str(run), "--repo", str(repo)]) == 2
    assert "modules.final.json: invalid module id" in capsys.readouterr().err
    assert not (run / "model.json").exists()


@pytest.mark.parametrize("modules", [None, [1], [{"name": "x"}], [{"id": "../x"}]])
def test_cli_assemble_bad_base_modules_exit_2(
    make_repo, tmp_path: Path, capsys, modules: Any
) -> None:
    repo = make_repo({"a.py": "x\n"})
    run = _run_dir(tmp_path)
    base = tmp_path / "base.json"
    base.write_text(json.dumps(_base_with(modules=modules)))
    args = ["assemble", "--run-dir", str(run), "--repo", str(repo), "--base-model", str(base)]
    assert main(args) == 2
    assert capsys.readouterr().err.startswith("assemble: base model: ")
    assert not (run / "model.json").exists()


@pytest.mark.parametrize("blocked", ["model.json", "file-notes.json"])
def test_cli_assemble_unwritable_output_exits_2(
    make_repo, tmp_path: Path, capsys, blocked: str
) -> None:
    # A directory where an output file belongs: the write fails on every OS and for root too,
    # unlike a chmod, and the inputs stay readable.
    run = _run_dir(tmp_path)
    (run / blocked).mkdir()
    repo = make_repo({"a.py": "x\n"})
    assert main(["assemble", "--run-dir", str(run), "--repo", str(repo)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("assemble: ") and blocked in err


def test_cli_build_unencodable_model_exits_2(tmp_path: Path, capsys) -> None:
    model_path = tmp_path / "m.json"
    model_path.write_text(json.dumps(_model_with_tagline("bad \ud800 text")))  # as a \ud800 escape
    assert main(["build", "--model", str(model_path), "--explorer-dir", str(tmp_path / "ex")]) == 2
    assert "build: " in capsys.readouterr().err
    assert not (tmp_path / "ex").exists()


def test_cli_build_prints_state_and_writes_data(tmp_path: Path, capsys) -> None:
    model_path = tmp_path / "m.json"
    model_path.write_text(FIXTURE.read_text())
    assert main(["build", "--model", str(model_path), "--explorer-dir", str(tmp_path / "ex")]) == 0
    state = json.loads(capsys.readouterr().out)
    assert state == json.loads((tmp_path / "ex" / "data" / "state.json").read_text())
    assert not (tmp_path / "ex" / "index.html").exists()


@pytest.mark.parametrize("content", ["{broken", ""])
def test_cli_build_unparseable_model_exits_2(tmp_path: Path, capsys, content: str) -> None:
    bad = tmp_path / "m.json"
    bad.write_text(content)
    assert main(["build", "--model", str(bad), "--explorer-dir", str(tmp_path / "ex")]) == 2
    assert "m.json" in capsys.readouterr().err
    assert not (tmp_path / "ex").exists()


def test_cli_build_missing_model_exits_2(tmp_path: Path, capsys) -> None:
    args = ["build", "--model", str(tmp_path / "gone.json"), "--explorer-dir", str(tmp_path / "ex")]
    assert main(args) == 2
    assert "gone.json" in capsys.readouterr().err


def test_cli_build_non_object_model_exits_1(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "m.json"
    bad.write_text("[]")
    assert main(["build", "--model", str(bad), "--explorer-dir", str(tmp_path / "ex")]) == 1
    assert "(root): expected object" in capsys.readouterr().err


def test_cli_build_missing_template_exits_2(tmp_path: Path, capsys) -> None:
    model_path = tmp_path / "m.json"
    model_path.write_text(FIXTURE.read_text())
    args = [
        "build",
        "--model",
        str(model_path),
        "--explorer-dir",
        str(tmp_path / "ex"),
        "--template",
        str(tmp_path / "no-template"),
    ]
    assert main(args) == 2
    assert "no-template" in capsys.readouterr().err


# --- explorer-status: Phase 0's ownership check ---------------------------------------------


def _status(capsys, repo: Path) -> tuple[int, dict]:
    code = main(["explorer-status", "--repo", str(repo)])
    out = capsys.readouterr().out
    return code, (json.loads(out) if out.strip() else {})


def test_explorer_status_absent(make_repo, capsys) -> None:
    repo = make_repo({"main.py": "x = 1\n"})
    assert _status(capsys, repo) == (0, {"explorer": "absent", "foreign_files": []})


def test_explorer_status_ours(make_repo, capsys, marker) -> None:
    repo = make_repo({"main.py": "x = 1\n", **marker})
    install_template(build.TEMPLATE_DIR, repo / "explorer")
    assert _status(capsys, repo) == (0, {"explorer": "ours", "foreign_files": []})


@pytest.mark.parametrize(
    "files,foreign",
    [
        ({"explorer/app.js": "var a;\n"}, ["app.js"]),  # C2: no marker
        (  # r2/p1: a state.json the build did not write
            {"explorer/app.js": "var a;\n", "explorer/data/state.json": '{"saved": "ui"}\n'},
            ["app.js", "data/state.json"],
        ),
        ({"explorer/data/loader.js": "var f;\n"}, ["data/loader.js"]),  # r2/p3
        ({"explorer/data/x.js": "x\n", "MARKER": ""}, ["data/x.js"]),  # r2/p4
    ],
)
def test_explorer_status_foreign(make_repo, capsys, marker, files, foreign) -> None:
    if files.pop("MARKER", None) is not None:
        files.update(marker)
    repo = make_repo({"main.py": "x = 1\n", **files})
    assert _status(capsys, repo) == (0, {"explorer": "foreign", "foreign_files": foreign})


def test_explorer_status_needs_a_repo(tmp_path: Path, capsys) -> None:
    assert main(["explorer-status", "--repo", str(tmp_path / "nope")]) == 2


def test_explorer_status_needs_the_top_level(make_repo, capsys) -> None:
    repo = make_repo({"sub/x.py": "x = 1\n"})
    assert main(["explorer-status", "--repo", str(repo / "sub")]) == 2
    assert "top level" in capsys.readouterr().err


def test_install_template_refuses_a_symlinked_file(tmp_path: Path) -> None:
    # The copy would write the template's app.js through the link, into the file it names.
    template = _tiny_template(tmp_path)
    explorer = tmp_path / "explorer"
    _write_marker(explorer)
    outside = tmp_path / "outside.js"
    outside.write_text("mine")
    (explorer / "app.js").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink.*app.js"):
        install_template(template, explorer)
    assert outside.read_text() == "mine"


# --- round 3: build without --template, line endings and reformatting, empty directories ---------


def _build_cli(explorer: Path, model: Path, template: Path | None = None) -> int:
    argv = ["build", "--model", str(model), "--explorer-dir", str(explorer)]
    return main(argv + (["--template", str(template)] if template else []))


def test_cli_build_without_template_refuses_a_foreign_explorer(make_repo, tmp_path, capsys) -> None:
    # r3/nt: without --template, build used to write a valid marker into the target's explorer/.
    repo = make_repo({"explorer/app.js": "export function realCode(){return 42}\n"})
    model = tmp_path / "model.json"
    model.write_text(FIXTURE.read_text())
    assert _build_cli(repo / "explorer", model) == 2
    assert "not made by document-repo" in capsys.readouterr().err
    assert not (repo / "explorer" / "data").exists()
    assert _status(capsys, repo) == (0, {"explorer": "foreign", "foreign_files": ["app.js"]})


def test_cli_build_without_template_refuses_a_stray_in_data(tmp_path: Path, capsys) -> None:
    explorer = tmp_path / "explorer"
    _write_marker(explorer)
    (explorer / "data" / "loader.js").write_text("var f;\n")
    model = tmp_path / "model.json"
    model.write_text(FIXTURE.read_text())
    assert _build_cli(explorer, model) == 2
    assert "data/loader.js" in capsys.readouterr().err
    assert (explorer / "data" / "model.json").read_bytes() == b"{}\n"


def _built(tmp_path: Path) -> Path:
    explorer = tmp_path / "explorer"
    write_explorer_data(json.loads(FIXTURE.read_text()), explorer / "data")
    return explorer


def test_ownership_survives_a_crlf_checkout(tmp_path: Path) -> None:
    explorer = _built(tmp_path)
    for name in ("model.json", "state.json"):
        path = explorer / "data" / name
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert build.is_our_explorer(explorer)


@pytest.mark.parametrize(
    "dumps",
    [
        lambda m: json.dumps(m, indent=4) + "\n",  # pretty-format-json, ensure_ascii on
        lambda m: json.dumps(m, separators=(",", ":")),  # minified, no final newline
        lambda m: json.dumps(m, indent="\t", ensure_ascii=False),
    ],
    ids=["indent-4-ascii", "minified", "tabs"],
)
def test_ownership_survives_json_reformatting(tmp_path: Path, dumps) -> None:
    explorer = _built(tmp_path)
    for name in ("model.json", "state.json"):
        path = explorer / "data" / name
        path.write_text(dumps(json.loads(path.read_text(encoding="utf-8"))), encoding="utf-8")
    assert build.is_our_explorer(explorer)


@pytest.mark.parametrize(
    "change",
    [
        lambda m: {k: m[k] for k in reversed(list(m))},  # key order is part of the model's form
        lambda m: {**m, "extra": 1},
        "not json",
    ],
    ids=["keys-reordered", "value-changed", "not-json"],
)
def test_ownership_fails_when_the_model_itself_changed(tmp_path: Path, change) -> None:
    explorer = _built(tmp_path)
    path = explorer / "data" / "model.json"
    if isinstance(change, str):
        path.write_text(change)
    else:
        path.write_text(json.dumps(change(json.loads(path.read_text(encoding="utf-8")))))
    assert not build.is_our_explorer(explorer)


@pytest.mark.parametrize("layout", ["empty", "empty-data", "template-only"])
def test_explorer_status_reads_an_installable_directory_as_absent(
    make_repo, capsys, layout: str
) -> None:
    # r3/em: what moving files aside or an interrupted install leaves. build accepts it, so
    # Phase 0 must not stop on it (and "Check again" must not loop on an empty list).
    repo = make_repo({"main.py": "x = 1\n"})
    explorer = repo / "explorer"
    explorer.mkdir()
    if layout == "empty-data":
        (explorer / "data").mkdir()
    elif layout == "template-only":
        install_template(build.TEMPLATE_DIR, explorer)
    assert _status(capsys, repo) == (0, {"explorer": "absent", "foreign_files": []})
    model = repo.parent / "model.json"
    model.write_text(FIXTURE.read_text())
    assert _build_cli(explorer, model, build.TEMPLATE_DIR) == 0
    capsys.readouterr()
    assert _status(capsys, repo)[1]["explorer"] == "ours"


def test_a_refusal_after_a_partial_build_says_how_to_recover(tmp_path: Path, capsys) -> None:
    # write_explorer_data replaced model.json and stopped: the old state no longer matches.
    explorer = _built(tmp_path)
    (explorer / "data" / "model.json").write_text('{"half": "written"}\n')
    model = tmp_path / "model.json"
    model.write_text(FIXTURE.read_text())
    assert _build_cli(explorer, model, build.TEMPLATE_DIR) == 2
    err = capsys.readouterr().err
    assert "git checkout HEAD -- explorer" in err, err
