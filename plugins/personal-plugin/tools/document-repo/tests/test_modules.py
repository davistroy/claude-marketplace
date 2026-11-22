import json
from pathlib import Path

import pytest

from document_repo.cli import main
from document_repo.modules import module_key, propose_modules, slug


@pytest.mark.parametrize(
    "path,key",
    [
        ("setup.py", "."),
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
        (".github/workflows/ci.yml", None, 4),
        ("README.md", "no-comment-syntax", 1),
        ("setup.py", None, 2),
    ]
    return _inv_of(files)


def _inv_of(files: list[tuple[str, str | None, int]]) -> dict:
    return {"files": [{"path": p, "skip": s, "lines": n} for p, s, n in files]}


def _inv_paths(*paths: str) -> dict:
    return _inv_of([(p, None, 1) for p in paths])


def test_propose_groups_and_sorts() -> None:
    mods = propose_modules(_inv())["modules"]
    # Sorted by id. ".github" has id "github", so sorting by path (".github" before
    # "src") would put root first; sorting by id puts "github" before "root".
    assert [m["id"] for m in mods] == ["github", "root", "src", "src-api", "web"]
    assert [m["path"] for m in mods] == [".github", ".", "src", "src/api", "web"]
    assert [m["path"] for m in mods] != sorted(m["path"] for m in mods)
    api = next(m for m in mods if m["id"] == "src-api")
    assert api == {
        "id": "src-api",
        "path": "src/api",
        "files": ["src/api/a.py", "src/api/b.py"],
        "lines": 15,
    }
    root = next(m for m in mods if m["id"] == "root")
    assert root["path"] == "."
    assert root["files"] == ["setup.py"]
    assert all("README.md" not in m["files"] for m in mods)


def test_cli_modules(tmp_path: Path) -> None:
    inv = tmp_path / "inv.json"
    inv.write_text(json.dumps(_inv()))
    out = tmp_path / "mods.json"
    assert main(["modules", str(inv), "--out", str(out)]) == 0
    mods = json.loads(out.read_text())["modules"]
    assert [(m["id"], m["path"]) for m in mods] == [
        ("github", ".github"),
        ("root", "."),
        ("src", "src"),
        ("src-api", "src/api"),
        ("web", "web"),
    ]
    assert mods == propose_modules(_inv())["modules"]


def _id_to_path(inventory: dict) -> dict[str, str]:
    mods = propose_modules(inventory)["modules"]
    ids = [m["id"] for m in mods]
    assert len(ids) == len(set(ids)), f"duplicate module ids: {ids}"
    return {m["id"]: m["path"] for m in mods}


def test_root_dir_is_not_merged_with_top_level_files() -> None:
    mods = propose_modules(_inv_paths("setup.py", "root/a.py", "root/b.py"))["modules"]
    assert [(m["id"], m["path"], m["files"]) for m in mods] == [
        ("root", ".", ["setup.py"]),
        ("root-2", "root", ["root/a.py", "root/b.py"]),
    ]


def test_root_dir_alone_is_its_own_module() -> None:
    mods = propose_modules(_inv_paths("root/a.py"))["modules"]
    # "root" is reserved for the repo root, so a lone root/ dir never takes it.
    assert [(m["id"], m["path"], m["files"]) for m in mods] == [("root-2", "root", ["root/a.py"])]


def test_dot_prefixed_and_plain_dir_get_distinct_ids() -> None:
    assert _id_to_path(_inv_paths(".config/a.yml", "config/b.py")) == {
        "config": ".config",
        "config-2": "config",
    }


def test_grouped_dir_and_hyphenated_dir_get_distinct_ids() -> None:
    assert _id_to_path(_inv_paths("lib/foo/a.py", "lib-foo/b.py")) == {
        "lib-foo": "lib-foo",
        "lib-foo-2": "lib/foo",
    }


def test_case_variants_get_distinct_ids() -> None:
    assert _id_to_path(_inv_paths("Src/a.py", "src/b.py")) == {"src": "Src", "src-2": "src"}


def test_slug_fallback_does_not_collide_with_root_module() -> None:
    # "_" slugs to the empty-string fallback "root".
    assert _id_to_path(_inv_paths("setup.py", "_/a.py")) == {"root": ".", "root-2": "_"}


def test_root_and_fallback_and_root_dir_all_distinct() -> None:
    assert _id_to_path(_inv_paths("setup.py", "_/a.py", "root/b.py")) == {
        "root": ".",
        "root-2": "_",
        "root-3": "root",
    }


def test_suffix_search_skips_ids_that_are_already_taken() -> None:
    # Keys sort as "A", "a", "a-2". "A" takes "a"; "a" finds "a" taken and takes "a-2";
    # the real "a-2" directory then finds "a-2" taken too and moves on to "a-2-2".
    assert _id_to_path(_inv_paths("A/x.py", "a/y.py", "a-2/z.py")) == {
        "a": "A",
        "a-2": "a",
        "a-2-2": "a-2",
    }


def test_ids_do_not_depend_on_inventory_order() -> None:
    paths = ["setup.py", "_/a.py", "root/b.py", ".config/c", "config/d", "lib/foo/e", "lib-foo/f"]
    forward = propose_modules(_inv_paths(*paths))
    backward = propose_modules(_inv_paths(*reversed(paths)))
    assert forward == backward
