"""``document_repo traps``: the ``Traps:`` labels a branch added to comments.

Each test builds a throwaway git repo with a base commit, then a branch commit (or an uncommitted
edit) that adds headers, and asks for the traps against the base.
"""

from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import document_repo.traps as traps_mod
from document_repo import languages
from document_repo.cli import main
from document_repo.commit import InputError
from document_repo.languages import Lang, detect
from document_repo.traps import HEADER_LABELS, Trap, harvest_traps, iter_traps
from document_repo.verify import comment_chunk_ok, comment_scan

TOOL_SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture(autouse=True)
def _hermetic_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """The tool runs plain ``git``: a developer's global ignore rules must not reach the tests."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


Files = dict[str, "str | bytes"]


def head(git: Callable[..., str], repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


def run_traps(
    capsys: pytest.CaptureFixture[str], repo: Path, before: str, *extra: str
) -> tuple[int, Any, str]:
    """Run the CLI. Return ``(exit code, parsed stdout or None, stderr)``."""
    capsys.readouterr()
    code = main(["traps", "--repo", str(repo), f"--before={before}", *extra])
    cap = capsys.readouterr()
    return code, (json.loads(cap.out) if cap.out.strip() else None), cap.err


def branch(make_repo, commit_files, git, base: Files, change: Files) -> tuple[Path, str]:
    """A repo at ``base``, and the sha of that base. ``change`` is committed on top of it."""
    repo = make_repo(base)
    sha = head(git, repo)
    commit_files(repo, change, "branch")
    return repo, sha


def found(repo: Path, sha: str) -> list[tuple[str, int, str]]:
    return [(t.path, t.line, t.text) for t in harvest_traps(repo, sha)]


# --- one trap per language and comment style ---------------------------------------------------

PY_DOC = (
    '"""Store notes.\n'
    "\n"
    "Role: data layer.\n"
    "Traps: a bare pytest skips slow tests\n"
    "    because addopts adds -m 'not slow'.\n"
    "Invariants: body is non-empty.\n"
    '"""\n'
    "x = 1\n"
)

# (path, base text, text after the branch, expected (line, text) pairs)
CASES: dict[str, tuple[str, str, str, list[tuple[int, str]]]] = {
    "python-hash": (
        "a.py",
        "x = 1\n",
        "# Traps: foo\n#   continued\n# Invariants: x\nx = 1\n",
        [(1, "foo continued")],
    ),
    "python-module-docstring": (
        "a.py",
        "x = 1\n",
        PY_DOC,
        [(4, "a bare pytest skips slow tests because addopts adds -m 'not slow'.")],
    ),
    "python-function-docstring": (
        "a.py",
        "def f():\n    pass\n",
        'def f():\n    """Do f.\n\n    Traps: f is not idempotent.\n    """\n    pass\n',
        [(4, "f is not idempotent.")],
    ),
    "python-class-and-method-docstrings": (
        "a.py",
        "class C:\n    def m(self):\n        pass\n",
        'class C:\n    """Traps: C caches.\n    """\n\n    def m(self):\n'
        '        """Traps: m mutates.\n        """\n        pass\n',
        [(2, "C caches."), (6, "m mutates.")],
    ),
    "python-async-function-docstring": (
        "a.py",
        "async def f():\n    pass\n",
        'async def f():\n    """Traps: f swallows cancellation."""\n    pass\n',
        [(2, "f swallows cancellation.")],
    ),
    "python-one-line-docstring": (
        "a.py",
        "x = 1\n",
        '"""Traps: foo."""\nx = 1\n',
        [(1, "foo.")],
    ),
    "python-raw-docstring-closing-on-the-label-line": (
        "a.py",
        "x = 1\n",
        'r"""Mod.\n\nTraps: C:\\path is not escaped."""\nx = 1\n',
        [(3, "C:\\path is not escaped.")],
    ),
    "python-single-quoted-docstring": (
        "a.py",
        "x = 1\n",
        "'''Mod.\n\nTraps: say \"hi\"'''\nx = 1\n",
        [(3, 'say "hi"')],
    ),
    "python-docstring-closing-line-has-a-trailing-comment": (
        "a.py",
        "x = 1\n",
        '"""Mod.\n\nTraps: foo\n"""  # trailing\nx = 1\n',
        [(3, "foo")],
    ),
    "python-docstring-with-non-ascii-before-the-closing-quotes": (
        "a.py",
        "x = 1\n",
        '"""Traps: é ✓"""  # ü\nx = 1\n',
        [(1, "é ✓")],
    ),
    "python-docstring-on-the-def-line": (
        "a.py",
        "def f(): pass\n",
        'def f(): "Traps: one-liner"\n',
        [(1, "one-liner")],
    ),
    "python-docstring-after-a-default-argument-with-quotes": (
        "a.py",
        "def f(a='x'): pass\n",
        'def f(a="x"): "Traps: y"\n',
        [(1, "y")],
    ),
    "python-single-quoted-docstring-with-an-escaped-quote": (
        "a.py",
        "x = 1\n",
        '"Traps: say \\"hi\\""\nx = 1\n',
        [(1, 'say \\"hi\\"')],
    ),
    "python-hash-below-existing-docstring": (
        "a.py",
        '"""Existing."""\nx = 1\n',
        '"""Existing."""\n# Role: thing.\n# Traps: foo\nx = 1\n',
        [(3, "foo")],
    ),
    "toml": (
        "pyproject.toml",
        '[tool.pytest.ini_options]\naddopts = "-m \\"not slow\\""\n',
        "# Role: pytest configuration.\n"
        '# Traps: a bare pytest skips slow tests: addopts adds -m "not slow".\n'
        '#   Run pytest -m slow or pytest -m "" for the full suite.\n'
        '[tool.pytest.ini_options]\naddopts = "-m \\"not slow\\""\n',
        [
            (
                2,
                'a bare pytest skips slow tests: addopts adds -m "not slow". '
                'Run pytest -m slow or pytest -m "" for the full suite.',
            )
        ],
    ),
    "sql-dashes": (
        "m.sql",
        "create table t (id int);\n",
        "-- Role: notes table.\n-- Traps: applied in production; never edit,\n"
        "--   add a new migration instead.\ncreate table t (id int);\n",
        [(2, "applied in production; never edit, add a new migration instead.")],
    ),
    "sql-block": (
        "m.sql",
        "create table t (id int);\n",
        "/*\n Role: notes table.\n Traps: never edit.\n*/\ncreate table t (id int);\n",
        [(3, "never edit.")],
    ),
    "javascript-slashes": (
        "a.js",
        "export const a = 1;\n",
        "// Role: x.\n// Traps: foo\n//   bar\nexport const a = 1;\n",
        [(2, "foo bar")],
    ),
    "javascript-jsdoc-block": (
        "a.js",
        "export const a = 1;\n",
        "/**\n * Role: x.\n * Traps: foo\n *   bar\n * Invariants: y\n */\nexport const a = 1;\n",
        [(3, "foo bar")],
    ),
    "typescript-jsdoc-block": (
        "a.ts",
        "export const a = 1;\n",
        "/**\n * @file x\n *\n * Traps: foo\n * continued\n */\nexport const a = 1;\n",
        [(4, "foo continued")],
    ),
    "one-line-block": (
        "a.ts",
        "export const a = 1;\n",
        "/* Traps: foo */\nexport const a = 1;\n",
        [(1, "foo")],
    ),
    "html-one-line": (
        "p.html",
        "<p>hi</p>\n",
        "<!-- Traps: foo -->\n<p>hi</p>\n",
        [(1, "foo")],
    ),
    "html-multi-line": (
        "p.html",
        "<p>hi</p>\n",
        "<!--\n  Role: x.\n  Traps: foo\n    bar\n-->\n<p>hi</p>\n",
        [(3, "foo bar")],
    ),
    "css": (
        "s.css",
        "a { color: red; }\n",
        "/* Traps: foo\n   bar */\na { color: red; }\n",
        [(1, "foo bar")],
    ),
    "shell": ("run.sh", "echo hi\n", "# Traps: foo\necho hi\n", [(1, "foo")]),
    "yaml": ("c.yml", "a: 1\n", "# Traps: foo\na: 1\n", [(1, "foo")]),
    "dockerfile": ("Dockerfile", "FROM x\n", "FROM x\n# Traps: foo\nRUN y\n", [(2, "foo")]),
    "makefile": ("Makefile", "all:\n\techo\n", "# Traps: foo\nall:\n\techo\n", [(1, "foo")]),
    "go": ("a.go", "package a\n", "// Traps: foo\n\npackage a\n", [(1, "foo")]),
    "rust-inner-doc": ("a.rs", "fn f() {}\n", "//! Traps: foo\n\nfn f() {}\n", [(1, "foo")]),
    "rust-outer-doc": ("a.rs", "fn f() {}\n", "/// Traps: foo\nfn f() {}\n", [(1, "foo")]),
    "java-block": (
        "A.java",
        "class A {}\n",
        "/**\n * Traps: foo\n */\nclass A {}\n",
        [(2, "foo")],
    ),
    "c-block": ("a.c", "int a;\n", "/* Traps: foo */\nint a;\n", [(1, "foo")]),
}


@pytest.mark.parametrize("case", CASES)
def test_a_trap_added_in_each_comment_style_is_harvested(
    case: str, make_repo, commit_files, git, capsys
) -> None:
    path, base, after, expected = CASES[case]
    repo, sha = branch(make_repo, commit_files, git, {path: base}, {path: after})
    assert found(repo, sha) == [(path, line, text) for line, text in expected]
    code, out, err = run_traps(capsys, repo, sha)
    assert (code, err) == (0, "")
    assert out == [{"path": path, "line": line, "text": text} for line, text in expected]


def test_the_semicolon_comes_from_the_language_table(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No language in the table uses ``;`` today. One that did would work without a code change."""
    monkeypatch.setitem(languages.EXT, ".ini", Lang("ini", (";",), (), "comment-lines"))
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.ini": "[x]\n"},
        {"a.ini": ";; Role: x.\n;; Traps: foo\n;;   bar\n[x]\n"},
    )
    assert found(repo, sha) == [("a.ini", 2, "foo bar")]


# --- what a trap's text is ---------------------------------------------------------------------


def traps_in(
    make_repo, commit_files, git, text: str, base: str = "x = 1\n"
) -> list[tuple[int, str]]:
    repo, sha = branch(make_repo, commit_files, git, {"a.py": base}, {"a.py": text})
    return [(line, t) for _p, line, t in found(repo, sha)]


@pytest.mark.parametrize("label", HEADER_LABELS)
def test_every_other_header_label_ends_a_trap(label: str, make_repo, commit_files, git) -> None:
    text = f"# Traps: foo\n#   bar\n# {label}: ignore me\n#   and me\nx = 1\n"
    expected = [(1, "foo bar")] if label != "Traps" else [(1, "foo bar"), (3, "ignore me and me")]
    assert traps_in(make_repo, commit_files, git, text) == expected


def test_the_label_set_is_the_one_in_comment_standards() -> None:
    assert HEADER_LABELS == (
        "Role",
        "Used by",
        "Inputs",
        "Outputs",
        "Side effects",
        "Invariants",
        "Traps",
    )


def test_two_traps_in_one_header_are_two_entries(make_repo, commit_files, git) -> None:
    text = "# Traps: one\n# Role: x\n# Traps: two\n#   more\nx = 1\n"
    assert traps_in(make_repo, commit_files, git, text) == [(1, "one"), (3, "two more")]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("# Traps: a\n#\n# not part of it\nx = 1\n", [(1, "a")]),
        ("# Traps: a\nx = 1\n# b\n", [(1, "a")]),
        ("# Traps: a\n\n# b\nx = 1\n", [(1, "a")]),
        ("# Traps:\n#   - a\n#   - b\nx = 1\n", [(1, "- a - b")]),
        ("# Traps:   lots   of   space  \n#\tand\ttabs\nx = 1\n", [(1, "lots of space and tabs")]),
        ("## Traps: a\n##   b\nx = 1\n", [(1, "a b")]),
        ("# Traps: é ✓ — ünïcode\nx = 1\n", [(1, "é ✓ — ünïcode")]),
    ],
    ids=[
        "blank-comment-ends",
        "code-ends",
        "blank-line-ends",
        "bullets",
        "space",
        "hashes",
        "utf8",
    ],
)
def test_continuation_rules(make_repo, commit_files, git, text, expected) -> None:
    assert traps_in(make_repo, commit_files, git, text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "# Traps:\nx = 1\n",
        "# Traps:   \n#\nx = 1\n",
        "# see Traps: foo\nx = 1\n",
        "# traps: foo\nx = 1\n",
        "# TRAPS: foo\nx = 1\n",
        "# Trap: foo\nx = 1\n",
        "# Traps foo\nx = 1\n",
        "#Traps\nx = 1\n",
    ],
    ids=[
        "empty",
        "empty-then-blank",
        "mid-line",
        "lowercase",
        "uppercase",
        "singular",
        "no-colon",
        "bare",
    ],
)
def test_text_that_is_not_the_label_is_not_a_trap(make_repo, commit_files, git, text) -> None:
    assert traps_in(make_repo, commit_files, git, text) == []


def test_a_continuation_never_swallows_an_existing_comment(make_repo, commit_files, git) -> None:
    got = traps_in(
        make_repo,
        commit_files,
        git,
        "# Traps: new\n# owner note\nx = 1\n",
        base="# owner note\nx = 1\n",
    )
    assert got == [(1, "new")]


@pytest.mark.parametrize(
    "path, base, after",
    [
        ("a.js", "x;\n", "/* Traps: a */\n// b\nx;\n"),
        ("a.js", "x;\n", "// Traps: a\n/* b */\nx;\n"),
        ("a.js", "x;\n", "/* Traps: a */\n/* b */\nx;\n"),
        ("a.js", "x;\n", "/**\n * Traps: a\n */\n// b\nx;\n"),
        ("a.py", "x = 1\n", '"""Traps: a"""\n# b\nx = 1\n'),
        ("a.py", "x = 1\n", '# Traps: a\n"""b"""\nx = 1\n'),
        ("p.html", "<p/>\n", "<!-- Traps: a -->\n<!-- b -->\n<p/>\n"),
    ],
    ids=["block-line", "line-block", "block-block", "jsdoc-line", "doc-hash", "hash-doc", "html"],
)
def test_a_trap_does_not_run_into_a_comment_of_another_block(
    path: str, base: str, after: str, make_repo, commit_files, git
) -> None:
    repo, sha = branch(make_repo, commit_files, git, {path: base}, {path: after})
    label_line = next(n for n, text in enumerate(after.splitlines(), 1) if "Traps:" in text)
    assert found(repo, sha) == [(path, label_line, "a")]


def test_a_file_over_the_size_cap_is_not_read(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    long_text = "# Traps: " + "long " * 20 + "\nx = 1\n"
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "x = 1\n", "b.py": "x = 1\n"},
        {"a.py": long_text, "b.py": "# Traps: short\nx = 1\n"},
    )
    assert [t.path for t in harvest_traps(repo, sha)] == ["a.py", "b.py"]
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    assert [t.path for t in harvest_traps(repo, sha)] == ["b.py"]


def test_python_has_a_lower_cap_than_other_languages(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The syntax tree costs about 110 times the file, so only Python gets the small limit."""
    long_text = "# Traps: " + "long " * 20 + "\nx = 1\n"
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "x = 1\n", "a.sh": "x=1\n"},
        {"a.py": long_text, "a.sh": long_text},
    )
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    monkeypatch.setattr(traps_mod, "MAX_BYTES", 400)
    assert [t.path for t in harvest_traps(repo, sha)] == ["a.sh"]
    monkeypatch.setattr(traps_mod, "MAX_BYTES", 40)
    assert harvest_traps(repo, sha) == []


# --- only what the branch added counts ---------------------------------------------------------


def test_a_trap_that_existed_at_the_base_is_not_reported(make_repo, commit_files, git) -> None:
    base = "# Traps: owner\nx = 1\n"
    got = traps_in(make_repo, commit_files, git, "# Traps: mine\n" + base, base=base)
    assert got == [(1, "mine")]


def test_the_reported_line_is_the_line_in_the_current_file(make_repo, commit_files, git) -> None:
    base = "# Traps: owner\nx = 1\ny = 2\n"
    text = "# Role: a.\n# Role: b.\n" + base + "# Traps: mine\nz = 3\n"
    got = traps_in(make_repo, commit_files, git, text, base=base + "z = 3\n")
    assert got == [(6, "mine")]


def test_a_continuation_added_under_an_owner_trap_is_not_a_trap(
    make_repo, commit_files, git
) -> None:
    base = "# Traps: owner\nx = 1\n"
    assert (
        traps_in(make_repo, commit_files, git, "# Traps: owner\n#   and more\nx = 1\n", base) == []
    )


def test_an_unchanged_docstring_trap_is_not_reported(make_repo, commit_files, git) -> None:
    base = '"""Mod.\n\nTraps: owner.\n"""\nx = 1\n'
    assert traps_in(make_repo, commit_files, git, base + "# Why: y.\ny = 2\n", base) == []


def test_identical_text_added_beside_an_owner_trap_counts_once(
    make_repo, commit_files, git
) -> None:
    base = "# Traps: same\nx = 1\n"
    got = traps_in(make_repo, commit_files, git, "# Traps: same\n" + base, base=base)
    assert [t for _line, t in got] == ["same"]


def test_the_work_tree_is_compared_not_only_commits(make_repo, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    sha = head(git, repo)
    (repo / "a.py").write_text("# Traps: uncommitted\nx = 1\n")
    assert found(repo, sha) == [("a.py", 1, "uncommitted")]


def test_an_untracked_new_file_is_harvested_whole(make_repo, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    sha = head(git, repo)
    (repo / "pkg").mkdir()
    (repo / "pkg" / "new.sh").write_text("#!/bin/sh\n# Traps: new file\necho\n")
    assert found(repo, sha) == [("pkg/new.sh", 2, "new file")]


def test_a_file_the_branch_deleted_is_skipped(make_repo, git) -> None:
    repo = make_repo({"a.py": "# Traps: gone\nx = 1\n", "b.py": "y = 1\n"})
    sha = head(git, repo)
    (repo / "a.py").unlink()
    assert found(repo, sha) == []


def test_a_gitignored_new_file_is_not_looked_at(make_repo, git) -> None:
    repo = make_repo({".gitignore": "gen/\n", "a.py": "x = 1\n"})
    sha = head(git, repo)
    (repo / "gen").mkdir()
    (repo / "gen" / "g.py").write_text("# Traps: ignored\n")
    assert found(repo, sha) == []


# --- what is not harvested ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "path, text",
    [
        ("README.md", "<!-- Traps: foo -->\n# r\n"),
        ("docs/NOTES.md", "Traps: foo\n"),
        ("docs/UPPER.MD", "<!-- Traps: foo -->\n"),
    ],
)
def test_markdown_is_skipped(path: str, text: str, make_repo, commit_files, git) -> None:
    repo, sha = branch(make_repo, commit_files, git, {path: "# r\n"}, {path: text})
    assert found(repo, sha) == []


def test_the_skills_own_explorer_output_is_skipped(make_repo, commit_files, git, marker) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "x = 1\n", **marker, "explorer/index.html": "<p>x</p>\n"},
        {"explorer/index.html": "<!-- Traps: ours -->\n<p>x</p>\n"},
    )
    assert found(repo, sha) == []


@pytest.mark.parametrize(
    "path, text",
    [
        ("a.py", 'print("Traps: x")\n'),
        ("a.py", "x = 1  # Traps: inline\n"),
        ("a.py", 's = """\nTraps: in a string\n"""\n'),
        ("a.py", 's = """\n# Traps: in a string\n"""\n'),
        ("a.py", "s = '''\n    Traps: in a string\n    '''\n"),
        ("a.py", 'def f():\n    x = """\n    Traps: not the docstring\n    """\n    return x\n'),
        ("a.py", "# not Traps: mid\n"),
        ("a.js", 'console.log("Traps: x");\n'),
        ("a.js", 'const s = "// Traps: x";\n'),
        ("a.js", "const s = 1; // Traps: inline\n"),
        ("run.sh", 'echo "Traps: x"\n'),
        ("run.sh", "echo hi # Traps: inline\n"),
        ("a.go", 'package a\n\nvar s = "// Traps: x"\n'),
        ("m.sql", "select 'Traps: x';\n"),
        ("p.html", "<p>Traps: x</p>\n"),
        ("s.css", "a::after { content: '/* Traps: x */'; }\n"),
    ],
)
def test_a_label_inside_code_is_not_a_trap(
    path: str, text: str, make_repo, commit_files, git
) -> None:
    repo, sha = branch(make_repo, commit_files, git, {path: "x = 1\n"}, {path: text})
    assert found(repo, sha) == []


def test_a_real_header_beside_code_that_looks_like_one(make_repo, commit_files, git) -> None:
    text = '// Traps: real\nconsole.log("Traps: fake");\n// Traps: also real\n'
    repo, sha = branch(make_repo, commit_files, git, {"a.js": "x;\n"}, {"a.js": text})
    assert found(repo, sha) == [("a.js", 1, "real"), ("a.js", 3, "also real")]


def test_a_python_file_that_does_not_parse_is_skipped(make_repo, commit_files, git) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "x = 1\n", "ok.py": "y = 1\n"},
        {"a.py": "# Traps: broken\ndef (:\n", "ok.py": "# Traps: fine\ny = 1\n"},
    )
    assert found(repo, sha) == [("ok.py", 1, "fine")]


def test_a_file_without_a_known_comment_syntax_is_skipped(make_repo, commit_files, git) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.txt": "x\n"},
        {"a.txt": "# Traps: foo\n", "b.json": "{}\n"},
    )
    assert found(repo, sha) == []


def test_a_file_that_is_not_utf8_is_skipped(make_repo, commit_files, git) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "x = 1\n"},
        {"b.py": b"# Traps: \xff\xfe\n", "c.py": "# Traps: fine\n"},
    )
    assert found(repo, sha) == [("c.py", 1, "fine")]


def test_a_symlink_is_not_followed(make_repo, git, tmp_path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("# Traps: outside the repo\n")
    repo = make_repo({"a.py": "x = 1\n"})
    sha = head(git, repo)
    try:
        (repo / "link.py").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not available")
    assert found(repo, sha) == []


def test_a_path_that_became_a_directory_is_skipped_without_a_crash(make_repo, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    sha = head(git, repo)
    (repo / "a.py").unlink()
    (repo / "a.py").mkdir()
    (repo / "a.py" / "inner.py").write_text("# Traps: inner\n")
    assert found(repo, sha) == [("a.py/inner.py", 1, "inner")]


# --- line numbers and line endings ------------------------------------------------------------


def test_crlf_files_keep_their_numbering_and_text(make_repo, commit_files, git) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": b"x = 1\r\ny = 2\r\n"},
        {"a.py": b"# Role: a.\r\n# Traps: foo\r\n#   bar\r\nx = 1\r\ny = 2\r\n"},
    )
    assert found(repo, sha) == [("a.py", 2, "foo bar")]


def test_a_form_feed_does_not_shift_the_line_number(make_repo, commit_files, git) -> None:
    base = "x = 1\n\x0c\ny = 2\n"
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": base, "a.c": "int a;\n\x0c\nint b;\n"},
        {"a.py": base + "# Traps: after the feed\n", "a.c": "int a;\n\x0c\nint b;\n// Traps: c\n"},
    )
    assert found(repo, sha) == [("a.c", 4, "c"), ("a.py", 4, "after the feed")]


def test_a_byte_order_mark_does_not_hide_a_python_trap(make_repo, commit_files, git) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "\ufeffx = 1\n"},
        {"a.py": "\ufeffx = 1\n# Traps: after the mark\n"},
    )
    assert found(repo, sha) == [("a.py", 2, "after the mark")]


@pytest.mark.parametrize(
    "path, text",
    [("a.py", "BOM# Traps: first line\nx = 1\n"), ("a.js", "BOM// Traps: first line\nx;\n")],
    ids=["python", "javascript"],
)
def test_a_trap_on_line_one_after_a_byte_order_mark(path: str, text: str, make_repo, git) -> None:
    repo = make_repo({"keep.txt": "x\n"})
    sha = head(git, repo)
    (repo / path).write_text(text.replace("BOM", "\ufeff"), encoding="utf-8")
    assert found(repo, sha) == [(path, 1, "first line")]


def test_a_byte_order_mark_on_both_sides_is_not_a_change(make_repo, commit_files, git) -> None:
    mark = "\ufeff"
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.js": mark + "// Traps: owner\nx;\n"},
        {"a.js": mark + "// Traps: owner\nx;\n// Traps: mine\n"},
    )
    assert found(repo, sha) == [("a.js", 3, "mine")]


# --- output order and shape --------------------------------------------------------------------


def test_the_output_is_sorted_by_path_then_line(make_repo, commit_files, git, capsys) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"z.py": "a = 1\n", "a/b.py": "a = 1\n", "a.py": "a = 1\n"},
        {
            "z.py": "# Traps: z\na = 1\n",
            "a/b.py": "# Traps: b2\n# Role: r\n# Traps: b1\na = 1\n",
            "a.py": "# Traps: a\na = 1\n",
        },
    )
    code, out, err = run_traps(capsys, repo, sha)
    assert (code, err) == (0, "")
    assert [(t["path"], t["line"], t["text"]) for t in out] == [
        ("a.py", 1, "a"),
        ("a/b.py", 1, "b2"),
        ("a/b.py", 3, "b1"),
        ("z.py", 1, "z"),
    ]
    assert all(list(t) == ["path", "line", "text"] for t in out)
    assert all(type(t["line"]) is int for t in out)


def test_no_traps_prints_an_empty_list(make_repo, commit_files, git, capsys) -> None:
    repo, sha = branch(
        make_repo, commit_files, git, {"a.py": "x = 1\n"}, {"a.py": "# Why: x.\nx = 1\n"}
    )
    assert run_traps(capsys, repo, sha) == (0, [], "")


def test_out_writes_the_file_and_prints_nothing(
    make_repo, commit_files, git, capsys, tmp_path
) -> None:
    repo, sha = branch(
        make_repo, commit_files, git, {"a.py": "x = 1\n"}, {"a.py": "# Traps: é\nx = 1\n"}
    )
    target = tmp_path / "deep" / "traps.json"
    capsys.readouterr()
    code = main(["traps", "--repo", str(repo), "--before", sha, "--out", str(target)])
    cap = capsys.readouterr()
    assert (code, cap.out, cap.err) == (0, "", "")
    assert json.loads(target.read_text(encoding="utf-8")) == [
        {"path": "a.py", "line": 1, "text": "é"}
    ]


def test_a_non_utf8_path_survives_the_output(
    make_repo, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Git hands such a name over as surrogate escapes. ``--out`` writes the original bytes."""
    repo = make_repo({"a.py": "x = 1\n"})
    odd = Trap(b"caf\xe9.py".decode("utf-8", "surrogateescape"), 1, "odd name")
    monkeypatch.setattr(traps_mod, "harvest_traps", lambda repo, before: [odd])
    target = tmp_path / "t.json"
    assert main(["traps", "--repo", str(repo), "--before", "HEAD", "--out", str(target)]) == 0
    assert b'"path": "caf\xe9.py"' in target.read_bytes()


# --- bad input: exit 2, a message on stderr ----------------------------------------------------


def test_a_bad_ref_exits_2(make_repo, capsys) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    code, out, err = run_traps(capsys, repo, "no-such-ref")
    assert (code, out) == (2, None)
    assert err.startswith("traps: ") and "no-such-ref" in err


@pytest.mark.parametrize("before", ["", "   ", "--output=/tmp/x", "-x", "HEAD:a.py"])
def test_an_unusable_before_exits_2(before: str, make_repo, capsys, tmp_path) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    code, out, err = run_traps(capsys, repo, before)
    assert (code, out) == (2, None)
    assert err.startswith("traps: ")


def test_a_directory_that_is_not_a_work_tree_exits_2(tmp_path, capsys) -> None:
    code, out, err = run_traps(capsys, tmp_path, "HEAD")
    assert (code, out) == (2, None)
    assert err.startswith("traps: ")


def test_a_subdirectory_of_a_work_tree_exits_2(make_repo, capsys) -> None:
    repo = make_repo({"sub/a.py": "x = 1\n"})
    code, out, err = run_traps(capsys, repo / "sub", "HEAD")
    assert (code, out) == (2, None)
    assert "top level" in err


def test_a_missing_directory_exits_2(tmp_path, capsys) -> None:
    code, out, err = run_traps(capsys, tmp_path / "nope", "HEAD")
    assert (code, out) == (2, None)
    assert err.startswith("traps: ")


def test_an_empty_repo_argument_exits_2(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["traps", "--repo", " ", "--before", "HEAD"])
    assert exc.value.code == 2
    assert "--repo is empty" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["--repo", "."], ["--before", "HEAD"], []])
def test_repo_and_before_are_required(argv: list[str], capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["traps", *argv])
    assert exc.value.code == 2


def test_a_failed_run_writes_no_out_file(make_repo, capsys, tmp_path) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    target = tmp_path / "t.json"
    assert main(["traps", "--repo", str(repo), "--before", "nope", "--out", str(target)]) == 2
    assert not target.exists()


def test_git_failing_while_listing_changes_exits_2(
    make_repo, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo({"a.py": "x = 1\n"})

    def broken(top: Path, sha: str) -> list[str]:
        raise subprocess.CalledProcessError(128, ["git"], stderr=b"fatal: boom")

    monkeypatch.setattr(traps_mod, "changed_files", broken)
    code, out, err = run_traps(capsys, repo, "HEAD")
    assert (code, out) == (2, None)
    assert "fatal: boom" in err


def test_harvest_raises_input_error_on_a_bad_ref(make_repo) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    with pytest.raises(InputError, match="does not name a commit"):
        harvest_traps(repo, "nope")


def test_the_command_runs_as_a_module(make_repo, commit_files, git) -> None:
    repo, sha = branch(
        make_repo, commit_files, git, {"a.py": "x = 1\n"}, {"a.py": "# Traps: foo\nx = 1\n"}
    )
    proc = subprocess.run(
        [sys.executable, "-m", "document_repo", "traps", "--repo", str(repo), "--before", sha],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(TOOL_SRC)},
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == [{"path": "a.py", "line": 1, "text": "foo"}]


# --- streaming ---------------------------------------------------------------------------------


def test_files_are_read_one_at_a_time(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "x = 1\n", "b.py": "x = 1\n"},
        {"a.py": "# Traps: a\nx = 1\n", "b.py": "# Traps: b\nx = 1\n"},
    )
    asked: list[str] = []
    real = traps_mod.git_show

    def spy(top: Path, ref: str, rel: str) -> str | None:
        asked.append(rel)
        return real(top, ref, rel)

    monkeypatch.setattr(traps_mod, "git_show", spy)
    stream = iter_traps(repo, sha)
    first = next(stream)
    assert (first.path, first.text) == ("a.py", "a")
    assert asked == ["a.py"]
    assert [t.path for t in stream] == ["b.py"]


def test_a_file_without_the_label_is_never_diffed(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(
        make_repo, commit_files, git, {"a.py": "x = 1\n"}, {"a.py": "# Why: nothing.\nx = 1\n"}
    )
    asked: list[str] = []
    real = traps_mod.git_show
    monkeypatch.setattr(traps_mod, "git_show", lambda *a: asked.append(a[2]) or real(*a))
    assert list(iter_traps(repo, sha)) == []
    assert asked == []


# --- comment_scan: the verifier's chunk classifier, now with the text -------------------------


def test_comment_scan_returns_text_key_and_why() -> None:
    sh = detect("x.sh")
    assert sh is not None
    assert comment_scan(["# a", "", "code", "#b"], sh) == (
        [(0, " a"), None, None, (0, "b")],
        "non-comment line added: 'code'",
    )
    css = detect("x.css")
    assert css is not None
    assert comment_scan(["/* a", "b */", "/* c */"], css) == (
        [(1, " a"), (1, "b "), (2, " c ")],
        "",
    )


def test_comment_scan_reports_the_first_failure_only() -> None:
    css = detect("x.css")
    assert css is not None
    _lines, why = comment_scan(["/* a */ x {}", "code"], css)
    assert why == "code after block-comment end: '/* a */ x {}'"
    _lines, why = comment_scan(["/* open"], css)
    assert why == "unterminated block comment in inserted lines"


def _reference_chunk_ok(lines: list[str], lang: Lang) -> tuple[bool, str]:
    """The ``comment_chunk_ok`` of commit edfb1eb, kept to prove the refactor changed nothing."""
    from document_repo.verify import _block_close

    block: tuple[str, str] | None = None
    depth = 0
    for raw in lines:
        s = raw.strip()
        if block is None:
            if not s or any(s.startswith(m) for m in lang.line):
                continue
            block = next(((b, e) for b, e in lang.block if s.startswith(b)), None)
            if block is None:
                return False, f"non-comment line added: {raw!r}"
            s, depth = s[len(block[0]) :], 1
        depth, close = _block_close(s, block[0], block[1], depth, lang.nested_block)
        if close >= 0:
            if s[close:].strip():
                return False, f"code after block-comment end: {raw!r}"
            block = None
    if block is not None:
        return False, "unterminated block comment in inserted lines"
    return True, ""


_POOL = [
    "",
    "   ",
    "# a",
    "// a",
    "-- a",
    "code()",
    "/* a */",
    "/* a",
    "b */",
    "b */ c",
    "/* a /* b */",
    "x /* y",
    "/*",
    "*/",
    "<!-- a -->",
    "<!-- a",
    "--> c",
    "-->",
    " * a",
    "/** a",
    "a */ b /* c */",
]


@pytest.mark.parametrize("name", ["x.sql", "x.rs", "x.css", "x.html", "x.sh", "x.c", "x.js"])
def test_comment_chunk_ok_is_the_reference_on_every_short_chunk(name: str) -> None:
    lang = detect(name)
    assert lang is not None
    for size in (1, 2, 3):
        for chunk in itertools.product(_POOL, repeat=size):
            assert comment_chunk_ok(list(chunk), lang) == _reference_chunk_ok(list(chunk), lang), (
                name,
                chunk,
            )
