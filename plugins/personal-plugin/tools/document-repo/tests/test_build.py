import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest

from document_repo.build import (
    assemble_model,
    install_template,
    normalize_remote,
    read_json,
    read_object,
    write_explorer_data,
)
from document_repo.cli import main
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
    (explorer / "data").mkdir(parents=True)
    (explorer / "data" / "model.js").write_text("REAL")
    install_template(template, explorer)
    assert (explorer / "index.html").exists() and (explorer / "vendor" / "m.js").exists()
    assert (explorer / "data" / "model.js").read_text() == "REAL"


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
        ("http://github.com/o/r", "https://github.com/o/r"),
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
    explorer.mkdir()
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
