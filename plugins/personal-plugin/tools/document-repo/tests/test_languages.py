import pytest

from document_repo.languages import EXT, NAMES, VERIFY_METHODS, detect


@pytest.mark.parametrize(
    "path,name",
    [
        ("a/b.py", "python"),
        ("x.ts", "typescript"),
        ("x.tsx", "typescript"),
        ("x.mts", "typescript"),
        ("x.js", "javascript"),
        ("x.mjs", "javascript"),
        ("x.jsx", "javascript"),
        ("db/001.sql", "sql"),
        ("run.sh", "shell"),
        ("ci.yml", "yaml"),
        ("ci.YAML", "yaml"),
        ("Dockerfile", "dockerfile"),
        ("Dockerfile.dev", "dockerfile"),
        ("Makefile", "make"),
        ("s.css", "css"),
        ("p.html", "html"),
    ],
)
def test_detect_known(path: str, name: str) -> None:
    lang = detect(path)
    assert lang is not None and lang.name == name


@pytest.mark.parametrize("path", ["data.json", "README.md", "img.png", "noext", "x.lock"])
def test_detect_unknown(path: str) -> None:
    assert detect(path) is None


@pytest.mark.parametrize("lang", [*EXT.values(), *NAMES.values()])
def test_every_lang_is_well_formed(lang) -> None:
    # Derived from the tables themselves, never a copied list (repo rule).
    assert lang.verify_method in VERIFY_METHODS
    assert lang.line or lang.block
    for start, end in lang.block:
        assert start and end


def test_python_and_ts_methods() -> None:
    py = detect("a.py")
    ts = detect("a.ts")
    sql = detect("a.sql")
    assert py is not None and py.verify_method == "python-ast"
    assert ts is not None and ts.verify_method == "ts-printer"
    assert sql is not None and sql.verify_method == "comment-lines"
