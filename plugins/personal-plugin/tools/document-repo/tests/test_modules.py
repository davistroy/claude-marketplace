import json
from pathlib import Path

import pytest

from document_repo.cli import main
from document_repo.modules import module_key, propose_modules, slug


@pytest.mark.parametrize(
    "path,key",
    [
        ("setup.py", "root"),
        ("src/main.py", "src"),
        ("src/api/a.py", "src/api"),
        ("packages/web/src/x.ts", "packages/web"),
        ("web/index.ts", "web"),
        (".github/workflows/ci.yml", ".github"),
    ],
)
def test_module_key(path: str, key: str) -> None:
    assert module_key(path) == key


@pytest.mark.parametrize(
    "key,expected",
    [("root", "root"), ("src/api", "src-api"), (".github", "github"), ("A B", "a-b")],
)
def test_slug(key: str, expected: str) -> None:
    assert slug(key) == expected


def _inv() -> dict:
    files = [
        ("src/api/a.py", None, 10),
        ("src/api/b.py", None, 5),
        ("src/main.py", None, 3),
        ("web/index.ts", None, 7),
        ("README.md", "no-comment-syntax", 1),
        ("setup.py", None, 2),
    ]
    return {"files": [{"path": p, "skip": s, "lines": n} for p, s, n in files]}


def test_propose_groups_and_sorts() -> None:
    mods = propose_modules(_inv())["modules"]
    assert [m["id"] for m in mods] == ["root", "src", "src-api", "web"]
    api = next(m for m in mods if m["id"] == "src-api")
    assert api == {
        "id": "src-api",
        "path": "src/api",
        "files": ["src/api/a.py", "src/api/b.py"],
        "lines": 15,
    }
    assert next(m for m in mods if m["id"] == "root")["path"] == "."
    assert all("README.md" not in m["files"] for m in mods)


def test_cli_modules(tmp_path: Path) -> None:
    inv = tmp_path / "inv.json"
    inv.write_text(json.dumps(_inv()))
    out = tmp_path / "mods.json"
    assert main(["modules", str(inv), "--out", str(out)]) == 0
    assert len(json.loads(out.read_text())["modules"]) == 4
