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
from document_repo.traps import HEADER_LABELS, Skipped, Trap, harvest_traps, iter_traps
from document_repo.verify import comment_chunk_ok, comment_scan, tracked_files

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
    monkeypatch.setattr(traps_mod, "harvest_traps", lambda repo, before, skipped=None: [odd])
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


@pytest.mark.parametrize("argv", [["--before", "HEAD"], []])
def test_repo_is_required(argv: list[str], capsys) -> None:
    """``--before`` became optional (see "without --before" below); ``--repo`` did not."""
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


# --- without --before: every Traps: line in the tracked files ----------------------------------


def run_all(capsys: pytest.CaptureFixture[str], repo: Path, *extra: str) -> tuple[int, Any, str]:
    """Run ``traps`` with no ``--before``."""
    capsys.readouterr()
    code = main(["traps", "--repo", str(repo), *extra])
    cap = capsys.readouterr()
    return code, (json.loads(cap.out) if cap.out.strip() else None), cap.err


def test_without_before_every_trap_in_the_tracked_files_is_listed(make_repo, capsys) -> None:
    repo = make_repo(
        {
            "a.py": "# Traps: owner one\n#   continued\nx = 1\n",
            "src/b.js": "/**\n * Traps: owner two\n */\nexport const b = 1;\n",
            "c.sql": "-- Role: t\n-- Traps: owner three\nselect 1;\n",
            "d.py": '"""Mod.\n\nTraps: owner four\n"""\n',
            "README.md": "<!-- Traps: markdown -->\n",
            "notes.txt": "# Traps: no comment syntax\n",
        }
    )
    code, out, err = run_all(capsys, repo)
    assert (code, err) == (0, "")
    assert [(t["path"], t["line"], t["text"]) for t in out] == [
        ("a.py", 1, "owner one continued"),
        ("c.sql", 2, "owner three"),
        ("d.py", 3, "owner four"),
        ("src/b.js", 2, "owner two"),
    ]
    assert all(list(t) == ["path", "line", "text"] for t in out)


def test_without_before_the_branchs_traps_and_uncommitted_ones_are_in_it_too(
    make_repo, commit_files, git
) -> None:
    repo = make_repo({"a.py": "# Traps: owner\nx = 1\n", "b.py": "y = 1\n", "c.py": "z = 1\n"})
    commit_files(repo, {"b.py": "# Traps: committed\ny = 1\n"}, "branch")
    (repo / "c.py").write_text("# Traps: uncommitted\nz = 1\n")
    assert [(t.path, t.text) for t in harvest_traps(repo)] == [
        ("a.py", "owner"),
        ("b.py", "committed"),
        ("c.py", "uncommitted"),
    ]


def test_with_before_is_a_subset_of_without(make_repo, commit_files, git) -> None:
    repo = make_repo({"a.py": "# Traps: owner\nx = 1\n", "b.py": "y = 1\n"})
    sha = head(git, repo)
    commit_files(repo, {"b.py": "# Traps: mine\ny = 1\n"}, "branch")
    since = set(harvest_traps(repo, sha))
    everything = set(harvest_traps(repo))
    assert since == {Trap("b.py", 1, "mine")}
    assert since < everything and Trap("a.py", 1, "owner") in everything


def test_without_before_an_untracked_file_is_not_listed_but_a_staged_one_is(make_repo, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    (repo / "staged.py").write_text("# Traps: staged\n")
    git(repo, "add", "staged.py")
    (repo / "loose.py").write_text("# Traps: untracked\n")
    assert [t.path for t in harvest_traps(repo)] == ["staged.py"]


def test_without_before_the_skills_own_explorer_output_is_not_listed(make_repo, marker) -> None:
    repo = make_repo(
        {"a.py": "x = 1\n", **marker, "explorer/index.html": "<!-- Traps: ours -->\n<p/>\n"}
    )
    assert harvest_traps(repo) == []


def test_without_before_a_tracked_file_deleted_from_the_work_tree_is_skipped(make_repo) -> None:
    repo = make_repo({"a.py": "# Traps: gone\nx = 1\n", "b.py": "# Traps: here\ny = 1\n"})
    (repo / "a.py").unlink()
    assert [t.path for t in harvest_traps(repo)] == ["b.py"]


@pytest.mark.parametrize(
    "path, text",
    [
        ("a.py", 'print("Traps: x")\n'),
        ("a.py", "x = 1  # Traps: inline\n"),
        ("a.py", 's = """\nTraps: in a string\n"""\n'),
        ("a.js", 'console.log("Traps: x");\n'),
        ("run.sh", 'echo "Traps: x"\n'),
    ],
)
def test_without_before_a_label_inside_code_is_still_not_a_trap(make_repo, path, text) -> None:
    assert harvest_traps(make_repo({path: text})) == []


def test_without_before_a_symlink_and_a_non_utf8_file_are_skipped(make_repo, tmp_path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("# Traps: outside the repo\n")
    repo = make_repo({"bad.py": b"# Traps: \xff\n", "ok.py": "# Traps: fine\n"})
    try:
        (repo / "link.py").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not available")
    assert [t.path for t in harvest_traps(repo)] == ["ok.py"]


def test_an_empty_before_is_still_an_error_not_the_whole_tree(make_repo, capsys) -> None:
    """``--before "$(cat base.txt)"`` with a missing base.txt must not quietly list everything."""
    repo = make_repo({"a.py": "# Traps: owner\nx = 1\n"})
    capsys.readouterr()
    assert main(["traps", "--repo", str(repo), "--before="]) == 2
    err = capsys.readouterr().err
    assert err.startswith("traps: ") and "--before is empty" in err


def test_without_before_a_subdirectory_or_a_non_repo_exits_2(make_repo, tmp_path, capsys) -> None:
    repo = make_repo({"sub/a.py": "# Traps: x\n"})
    assert run_all(capsys, repo / "sub")[0] == 2
    assert run_all(capsys, tmp_path)[0] == 2


def test_without_before_files_are_read_one_at_a_time(
    make_repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo({"a.py": "# Traps: a\n", "b.py": "# Traps: b\n"})
    asked: list[str] = []
    real = traps_mod._read

    def spy(path: Path, limit: int) -> str | None:
        asked.append(path.name)
        return real(path, limit)

    monkeypatch.setattr(traps_mod, "_read", spy)
    stream = iter_traps(repo, None)
    assert next(stream).path == "a.py"
    assert asked == ["a.py"]
    assert [t.path for t in stream] == ["b.py"]


def test_tracked_files_are_sorted_and_leave_out_what_is_exempt(make_repo, marker, git) -> None:
    repo = make_repo(
        {
            ".gitignore": "ignored.py\n",
            "z.py": "x = 1\n",
            "a/b.py": "x = 1\n",
            "README.md": "# r\n",
            "explorer/app.js": "x\n",
            **marker,
        }
    )
    (repo / "untracked.py").write_text("x = 1\n")
    (repo / "ignored.py").write_text("x = 1\n")
    assert tracked_files(repo) == [".gitignore", "a/b.py", "z.py"]


def test_tracked_files_outside_a_work_tree_is_an_error(tmp_path) -> None:
    with pytest.raises(NotADirectoryError):
        tracked_files(tmp_path)


# --- a file over the size cap is named on stderr -----------------------------------------------

LONG = "# Traps: " + "long " * 20 + "\nx = 1\n"


def test_a_file_over_the_cap_is_named_on_stderr_with_its_size(
    make_repo, commit_files, git, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"big.py": "x = 1\n", "small.py": "x = 1\n"},
        {"big.py": LONG, "small.py": "# Traps: short\nx = 1\n"},
    )
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    code, out, err = run_traps(capsys, repo, sha)
    size = len(LONG.encode("utf-8"))
    assert code == 0
    assert out == [{"path": "small.py", "line": 1, "text": "short"}]  # still a plain list
    assert err == f"traps: skipped big.py: {size} bytes is over the 40-byte limit, not read\n"


def test_each_skipped_file_gets_one_line_in_path_order(
    make_repo, commit_files, git, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"z.py": "x = 1\n", "a.py": "x = 1\n", "m.sh": "x=1\n", "ok.py": "x = 1\n"},
        {"z.py": LONG, "a.py": LONG, "m.sh": LONG, "ok.py": "# Traps: ok\nx = 1\n"},
    )
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    monkeypatch.setattr(traps_mod, "MAX_BYTES", 40)
    code, out, err = run_traps(capsys, repo, sha)
    assert code == 0 and [t["path"] for t in out] == ["ok.py"]
    assert [line.split(":")[1].strip() for line in err.splitlines()] == [
        "skipped a.py",
        "skipped m.sh",
        "skipped z.py",
    ]


def test_python_and_other_files_are_judged_by_their_own_cap(
    make_repo, commit_files, git, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": "x = 1\n", "a.sh": "x=1\n"},
        {"a.py": LONG, "a.sh": LONG},
    )
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    monkeypatch.setattr(traps_mod, "MAX_BYTES", 400)
    code, out, err = run_traps(capsys, repo, sha)
    assert [t["path"] for t in out] == ["a.sh"]
    assert err.count("\n") == 1 and "a.py" in err and "40-byte limit" in err


def test_nothing_is_said_when_nothing_was_skipped(make_repo, commit_files, git, capsys) -> None:
    repo, sha = branch(make_repo, commit_files, git, {"a.py": "x = 1\n"}, {"a.py": LONG})
    assert run_traps(capsys, repo, sha)[2] == ""


def test_a_big_file_is_named_even_though_it_was_never_read(
    make_repo, commit_files, git, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The cap is checked before the file is opened, so the note cannot say it had a label."""
    repo, sha = branch(
        make_repo, commit_files, git, {"a.py": "x = 1\n"}, {"a.py": "# no label here\n" * 10}
    )
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    code, out, err = run_traps(capsys, repo, sha)
    assert (code, out) == (0, []) and err.startswith("traps: skipped a.py: ")


def test_skipped_files_are_reported_with_out_and_without_before(
    make_repo, capsys, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo({"big.py": LONG, "small.py": "# Traps: short\n"})
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    target = tmp_path / "t.json"
    code, out, err = run_all(capsys, repo, "--out", str(target))
    assert (code, out) == (0, None)
    assert json.loads(target.read_text(encoding="utf-8")) == [
        {"path": "small.py", "line": 1, "text": "short"}
    ]
    assert err.startswith("traps: skipped big.py: ") and err.count("\n") == 1


def test_harvest_fills_the_skipped_list(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(make_repo, commit_files, git, {"a.py": "x = 1\n"}, {"a.py": LONG})
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    skipped: list[Skipped] = []
    assert harvest_traps(repo, sha, skipped) == []
    assert skipped == [Skipped("a.py", len(LONG.encode("utf-8")), 40)]


def test_the_help_says_where_skipped_files_go_and_what_no_before_means(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["traps", "--help"])
    assert exc.value.code == 0
    text = " ".join(capsys.readouterr().out.split())
    assert "Without --before" in text and "every" in text and "tracked" in text
    assert "over the size limit" in text and "stderr" in text and "stdout" in text
    assert f"cut at {traps_mod.MAX_TRAP_CHARS} characters" in text


# --- review round 1: a trap inside an existing block comment (JS/TS) ----------------------------

OWNER_JSDOC = "/**\n * Role: thing.\n */\nexport const a = 1;\n"


@pytest.mark.parametrize("path", ["a.js", "a.ts", "a.tsx", "a.mjs", "a.jsx", "a.cts"])
def test_a_trap_added_inside_an_owner_block_comment_is_found(
    path: str, make_repo, commit_files, git
) -> None:
    """The TypeScript printer accepts this edit, so a verified branch can hold it."""
    after = (
        "/**\n * Role: thing.\n * Traps: a bare call loses data.\n *   continued.\n */\n"
        "export const a = 1;\n"
    )
    repo, sha = branch(make_repo, commit_files, git, {path: OWNER_JSDOC}, {path: after})
    assert found(repo, sha) == [(path, 3, "a bare call loses data. continued.")]


def test_a_trap_inside_an_owner_block_comment_does_not_absorb_the_owners_lines(
    make_repo, commit_files, git
) -> None:
    base = "/**\n * Role: thing.\n * owner text after.\n */\nexport const a = 1;\n"
    after = "/**\n * Role: thing.\n * Traps: new.\n * owner text after.\n */\nexport const a = 1;\n"
    repo, sha = branch(make_repo, commit_files, git, {"a.js": base}, {"a.js": after})
    assert found(repo, sha) == [("a.js", 3, "new.")]


def test_an_owner_trap_inside_a_block_comment_is_not_reported_in_before_mode(
    make_repo, commit_files, git
) -> None:
    base = "/**\n * Traps: owner.\n */\nexport const a = 1;\n"
    after = "/**\n * Traps: owner.\n * Traps: mine.\n */\nexport const a = 1;\n"
    repo, sha = branch(make_repo, commit_files, git, {"a.js": base}, {"a.js": after})
    assert found(repo, sha) == [("a.js", 3, "mine.")]


def test_a_line_comment_trap_added_inside_a_block_comment_is_part_of_it_not_a_line_comment(
    make_repo, commit_files, git
) -> None:
    base = "/*\n * Role: x.\n */\nexport const a = 1;\n"
    after = "/*\n * Role: x.\n// Traps: not a comment here\n */\nexport const a = 1;\n"
    repo, sha = branch(make_repo, commit_files, git, {"a.js": base}, {"a.js": after})
    assert found(repo, sha) == []


def test_the_repro_repo_shape(make_repo, commit_files, git) -> None:
    """The reviewer's repro: a JS block insert, a template literal, and an SQL continuation."""
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.js": OWNER_JSDOC, "q.sql": "-- Role: x\nselect 1;\n"},
        {
            "a.js": (
                "/**\n * Role: thing.\n * Traps: a bare call loses data.\n *   continued.\n */\n"
                "export const a = 1;\nconst t = `\n// Traps: inside template\n`;\n"
            ),
            "q.sql": (
                "-- Role: x\n-- Traps: returns -1 on miss\n"
                "--   -1 means not found; !important\nselect 1;\n"
            ),
        },
    )
    assert found(repo, sha) == [
        ("a.js", 3, "a bare call loses data. continued."),
        ("q.sql", 2, "returns -1 on miss -1 means not found; !important"),
    ]


# --- review round 1: a label inside text that only looks like a comment ------------------------


@pytest.mark.parametrize("path", ["a.js", "a.ts", "a.tsx"])
def test_without_before_a_trap_inside_a_template_literal_is_not_listed(
    path: str, make_repo
) -> None:
    text = (
        "// Traps: real header\n"
        "export const t = `\n// Traps: inside the template\n`;\n"
        "/* Traps: real block */\n"
        "export const u = `\n/* Traps: inside again */\n`;\n"
    )
    repo = make_repo({path: text})
    assert [(t.line, t.text) for t in harvest_traps(repo)] == [
        (1, "real header"),
        (5, "real block"),
    ]


def test_with_before_a_trap_inside_an_added_template_literal_is_not_listed(
    make_repo, commit_files, git
) -> None:
    after = "const t = `\n// Traps: inside\n`;\n// Traps: after\nexport const a = 1;\n"
    repo, sha = branch(
        make_repo, commit_files, git, {"a.js": "export const a = 1;\n"}, {"a.js": after}
    )
    assert found(repo, sha) == [("a.js", 4, "after")]


def test_a_trap_after_a_regex_that_holds_a_quote_is_found(make_repo) -> None:
    text = "const re = /[\"'`]/g;\n// Traps: after the regex\nexport const a = 1;\n"
    assert [(t.line, t.text) for t in harvest_traps(make_repo({"a.js": text}))] == [
        (2, "after the regex")
    ]


def test_the_comment_scanner_for_other_languages_is_unchanged_inside_a_heredoc(make_repo) -> None:
    """Documented limit: outside Python and JS/TS a heredoc line can pass for a comment."""
    text = "cat <<'EOF'\n# Traps: inside a heredoc\nEOF\n"
    assert [t.text for t in harvest_traps(make_repo({"run.sh": text}))] == ["inside a heredoc"]


# --- review round 1: exactly one comment marker is removed -------------------------------------


@pytest.mark.parametrize(
    "path, text, expected",
    [
        ("q.sql", "-- Traps: a\n--   -1 means not found\n", "a -1 means not found"),
        ("q.sql", "-- Traps: a\n--   --flag is on\n", "a --flag is on"),
        ("a.js", "// Traps: a\n//   /usr/bin is special\n", "a /usr/bin is special"),
        ("a.js", "// Traps: a\n// !important\n", "a !important"),
        ("a.js", "// Traps: a\n//!important\n", "a !important"),
        ("a.rs", "//! Traps: a\n//!\n//! unrelated\n", "a"),
        ("a.js", "// Traps: a\n//x y\n", "a x y"),
        ("run.sh", "# Traps: a\n#x y\n", "a x y"),
        ("p.html", "<!-- Traps: a\n * not decoration -->\n", "a * not decoration"),
        ("a.go", "// Traps: a\n//   //nolint is ignored\n", "a //nolint is ignored"),
        ("run.sh", "# Traps: a\n#   -x flag\n", "a -x flag"),
        ("run.sh", "# Traps: a\n#   #hash tag\n", "a #hash tag"),
        ("a.py", "# Traps: a\n#   #hash tag\n#   -1 is a miss\n", "a #hash tag -1 is a miss"),
        ("a.js", "/**\n * Traps: a\n *   *bold* text\n */\n", "a *bold* text"),
        ("a.js", "/**\n * Traps: a\n *   * b\n */\n", "a * b"),
    ],
    ids=[
        "sql-minus-one",
        "sql-double-dash",
        "slashes-path",
        "bang",
        "bang-adjacent",
        "rust-empty-doc-line",
        "letter-then-space",
        "shell-letter-then-space",
        "html-star-is-text",
        "go-nolint",
        "shell-flag",
        "shell-hash",
        "python-hash",
        "jsdoc-bold",
        "block-star",
    ],
)
def test_only_one_marker_is_removed_from_a_continuation(
    path: str, text: str, expected: str, make_repo
) -> None:
    assert [t.text for t in harvest_traps(make_repo({path: text}))] == [expected]


@pytest.mark.parametrize(
    "path, text",
    [
        ("a.rs", "//! Traps: a\n//!   b\n"),
        ("a.rs", "/// Traps: a\n///   b\n"),
        ("run.sh", "## Traps: a\n##   b\n"),
        ("q.sql", "--- Traps: a\n---   b\n"),
    ],
    ids=["rust-inner", "rust-outer", "double-hash", "triple-dash"],
)
def test_a_doc_comment_marker_is_one_marker(path: str, text: str, make_repo) -> None:
    assert [t.text for t in harvest_traps(make_repo({path: text}))] == ["a b"]


# --- review round 1: the base blob is capped too ----------------------------------------------


def test_a_base_over_the_cap_is_named_and_not_read(
    make_repo, commit_files, git, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    big_base = "x = 1\n" + "# filler line\n" * 10
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.py": big_base},
        {"a.py": "# Traps: shrunk below the cap\nx = 1\n"},
    )
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 60)
    asked: list[str] = []
    real = traps_mod.git_show
    monkeypatch.setattr(traps_mod, "git_show", lambda *a: asked.append(a[2]) or real(*a))
    code, out, err = run_traps(capsys, repo, sha)
    assert (code, out) == (0, [])
    assert asked == []
    assert harvest_traps(repo, sha) == []  # without a list to fill, the file is still not read
    assert (
        err == f"traps: skipped a.py: {len(big_base.encode())} bytes is over the 60-byte limit, "
        "not read\n"
    )


def test_a_base_exactly_at_the_cap_is_read(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = "x = 1\n" + "# filler\n" * 3
    repo, sha = branch(
        make_repo, commit_files, git, {"a.py": base}, {"a.py": "# Traps: a\nx = 1\n"}
    )
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", len(base.encode()))
    skipped: list[Skipped] = []
    assert [t.text for t in harvest_traps(repo, sha, skipped)] == ["a"]
    assert skipped == []
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", len(base.encode()) - 1)
    assert harvest_traps(repo, sha, skipped) == []
    assert skipped == [Skipped("a.py", len(base.encode()), len(base.encode()) - 1)]


def test_a_new_file_has_no_base_to_cap(make_repo, git, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    sha = head(git, repo)
    (repo / "new.py").write_text("# Traps: new\n")
    monkeypatch.setattr(traps_mod, "MAX_PYTHON_BYTES", 40)
    assert [t.path for t in harvest_traps(repo, sha)] == ["new.py"]


# --- review round 2: memory, the diff guard and the size of a trap -------------------------------


def _peak_bytes(call) -> int:
    """The most memory Python allocated, in bytes, while ``call`` ran."""
    import gc
    import tracemalloc

    gc.collect()
    tracemalloc.start()
    try:
        call()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def test_traps_in_reads_its_entries_one_at_a_time() -> None:
    pulled: list[int] = []

    def source():
        for n in (1, 2, 10):
            pulled.append(n)
            yield (n, 1, "Traps: a" if n == 1 else "more")
        for n in range(11, 1_000_000):  # never reached when the reader stops early
            pulled.append(n)
            yield (n, 1, "x")

    stream = traps_mod._traps_in(source(), "p")
    assert next(stream) == Trap("p", 1, "a more")
    assert pulled == [1, 2, 10]


def test_a_trap_is_cut_at_the_cap_and_ends_in_dots() -> None:
    cap = traps_mod.MAX_TRAP_CHARS
    entries = [(1, 1, "Traps: start")]
    entries += [(n, 1, "word " * 20) for n in range(2, 3000)]
    entries += [(3000, 1, "Traps: next")]
    found_traps = list(traps_mod._traps_in(iter(entries), "p"))
    assert [t.line for t in found_traps] == [1, 3000]
    first = found_traps[0].text
    assert first.startswith("start word word") and first.endswith(" ...")
    assert len(first) <= cap + 4
    assert found_traps[1].text == "next"


@pytest.mark.parametrize("extra, dots", [(0, False), (1, True)])
def test_a_trap_of_exactly_the_cap_is_not_cut(extra: int, dots: bool) -> None:
    cap = traps_mod.MAX_TRAP_CHARS
    text = "w" * (cap + extra)
    [only] = traps_mod._traps_in(iter([(1, 1, "Traps: " + text)]), "p")
    assert only.text.endswith("...") is dots
    assert len(only.text) <= cap + 4


def test_a_long_run_of_comment_lines_after_a_trap_gives_one_short_trap(make_repo) -> None:
    repo = make_repo({"a.js": "// Traps: first\n" + "// word\n" * 5000 + "// Traps: second\n"})
    got = harvest_traps(repo)
    assert [t.line for t in got] == [1, 5002]
    assert got[0].text.endswith(" ...") and len(got[0].text) <= traps_mod.MAX_TRAP_CHARS + 4
    assert got[1].text == "second"


@pytest.mark.parametrize("path, unit", [("a.js", "// a\n"), ("b.sh", "# a\n"), ("c.py", "# a\n")])
def test_memory_stays_a_small_multiple_of_the_file_for_a_file_of_comment_lines(
    path: str, unit: str, make_repo, git
) -> None:
    """16 MiB of comment lines took 1.1 to 1.3 GB: a tuple and a string for every line, twice."""
    size = 1024 * 1024
    head = "// Traps: x\n//\n" if path.endswith(".js") else "# Traps: x\n#\n"
    repo = make_repo({path: "x = 1\n"})
    sha = head_sha = git(repo, "rev-parse", "HEAD").strip()
    (repo / path).write_text(head + unit * (size // len(unit)))
    assert head_sha == sha
    whole = _peak_bytes(lambda: harvest_traps(repo))
    since = _peak_bytes(lambda: harvest_traps(repo, sha))
    # JS keeps only the text; the line-based paths keep the lines too (about 13 bytes a byte).
    bound = (6 if path.endswith(".js") else 24) * size
    assert whole < bound, f"whole-tree peak {whole / size:.1f} x the file"
    assert since < bound, f"--before peak {since / size:.1f} x the file"


def test_one_files_memory_is_freed_before_the_next_file_is_read(make_repo) -> None:
    size = 512 * 1024
    body = "// Traps: x\n//\n" + "// a\n" * (size // 5)
    one = make_repo({"a.js": body})
    two = make_repo({"a.js": body, "b.js": body, "c.js": body})
    peak_one = _peak_bytes(lambda: harvest_traps(one))
    peak_three = _peak_bytes(lambda: harvest_traps(two))
    assert peak_three < peak_one * 1.5, (peak_one, peak_three)


# --- the diff guard (Minor 1) -----------------------------------------------------------------

IDENTICAL = "// a\n" * 60


class _NoDifflib:
    """Stands in for ``difflib`` in traps.py: using the matcher fails the test."""

    class SequenceMatcher:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("difflib was used where the guard should have sent git")


def _identical_lines_branch(make_repo, commit_files, git):
    return branch(
        make_repo,
        commit_files,
        git,
        {"a.js": IDENTICAL},
        {"a.js": "// Traps: x\n//\n" + IDENTICAL},
    )


def test_many_matching_lines_are_diffed_by_git_not_difflib(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = _identical_lines_branch(make_repo, commit_files, git)
    monkeypatch.setattr(traps_mod, "MAX_DIFF_PAIRS", 100)
    monkeypatch.setattr(traps_mod, "difflib", _NoDifflib)
    assert found(repo, sha) == [("a.js", 1, "x")]


def test_too_many_lines_are_diffed_by_git_not_difflib(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.sh": "".join(f"echo {n}\n" for n in range(50))},
        {"a.sh": "# Traps: x\n" + "".join(f"echo {n}\n" for n in range(50))},
    )
    monkeypatch.setattr(traps_mod, "MAX_DIFF_LINES", 10)
    monkeypatch.setattr(traps_mod, "difflib", _NoDifflib)
    assert found(repo, sha) == [("a.sh", 1, "x")]


def test_an_ordinary_file_is_still_diffed_by_difflib(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = _identical_lines_branch(make_repo, commit_files, git)
    monkeypatch.setattr(traps_mod, "difflib", _NoDifflib)
    with pytest.raises(AssertionError, match="difflib was used"):
        harvest_traps(repo, sha)


def test_the_pair_count_is_only_taken_when_the_product_could_exceed_the_limit(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = _identical_lines_branch(make_repo, commit_files, git)

    def no_counter(*args, **kwargs):
        raise AssertionError("counted lines of a small file")

    monkeypatch.setattr(traps_mod, "Counter", no_counter)
    assert found(repo, sha) == [("a.js", 1, "x")]


def test_whole_tree_mode_never_builds_a_matcher(make_repo, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no base every line is added: the matcher's index of the file was most of the memory."""
    repo = make_repo({"a.js": "// Traps: x\n", "b.sh": "# Traps: y\n", "c.py": "# Traps: z\n"})
    monkeypatch.setattr(traps_mod, "difflib", _NoDifflib)
    assert [t.text for t in harvest_traps(repo)] == ["x", "y", "z"]


@pytest.mark.parametrize(
    "base, after",
    [
        ("a\nb\nc\n", "# Traps: x\na\nb\nc\n"),
        ("a\nb\nc\n", "a\nb\n# Traps: x\nc\n"),
        ("a\nb\nc\n", "a\nb\nc\n# Traps: x\n"),
        ("a\nb\nc\n", "# Traps: x\n#\na\n# Traps: y\nb\nc\n# end\n"),
        ("a\r\nb\r\n", "a\r\n# Traps: x\r\nb\r\n"),
        ("", "# Traps: x\n"),
        ("a\n", "a\n\n\n# Traps: x\n\n"),
    ],
    ids=[
        "top",
        "middle",
        "end",
        "several-hunks",
        "crlf",
        "empty-base",
        "blank-lines",
    ],
)
def test_git_and_difflib_agree_on_what_a_comment_only_insert_added(
    base: str, after: str, make_repo, commit_files, git
) -> None:
    repo, sha = branch(make_repo, commit_files, git, {"a.sh": base}, {"a.sh": after})
    from document_repo.remap import split_lines

    expected = traps_mod._difflib_ranges(split_lines(base), split_lines(after))
    assert traps_mod._git_added_ranges(repo, sha, "a.sh") == expected


def test_git_counts_an_unterminated_last_line_as_changed_when_lines_follow_it(
    make_repo, commit_files, git
) -> None:
    """The one place git and difflib differ for an insert: ``c`` and ``c`` + newline differ."""
    repo, sha = branch(
        make_repo, commit_files, git, {"a.sh": "a\nb\nc"}, {"a.sh": "a\nb\nc\n# Traps: x\n"}
    )
    from document_repo.remap import split_lines

    assert traps_mod._difflib_ranges(
        split_lines("a\nb\nc"), split_lines("a\nb\nc\n# Traps: x\n")
    ) == [(3, 4)]
    assert traps_mod._git_added_ranges(repo, sha, "a.sh") == [(2, 4)]


def test_git_ranges_leave_out_a_pure_deletion(make_repo, commit_files, git) -> None:
    repo, sha = branch(
        make_repo, commit_files, git, {"a.sh": "a\nb\nc\n"}, {"a.sh": "a\nc\n# Traps: x\n"}
    )
    assert traps_mod._git_added_ranges(repo, sha, "a.sh") == [(2, 3)]


def test_git_ranges_use_git_even_when_the_file_has_a_diff_driver_or_looks_binary(
    make_repo, commit_files, git
) -> None:
    repo = make_repo({"a.sh": "a\n", ".gitattributes": "a.sh -diff\n"})
    sha = head(git, repo)
    commit_files(repo, {"a.sh": "a\n# Traps: x\n"}, "branch")
    assert traps_mod._git_added_ranges(repo, sha, "a.sh") == [(1, 2)]


def test_git_ranges_name_a_failure(make_repo) -> None:
    from document_repo.commit import GitError

    repo = make_repo({"a.sh": "a\n"})
    with pytest.raises(GitError, match="git diff"):
        traps_mod._git_added_ranges(repo, "0" * 40, "a.sh")


def test_the_guarded_and_unguarded_paths_find_the_same_traps(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {
        "a.js": OWNER_JSDOC,
        "b.sh": "echo hi\n",
        "c.py": "x = 1\n",
        "d.sql": "select 1;\n",
    }
    changed = {
        "a.js": (
            "/**\n * Role: thing.\n * Traps: in a block.\n */\n"
            "export const a = 1;\n// Traps: tail\n"
        ),
        "b.sh": "# Traps: shell\n#   more\necho hi\n",
        "c.py": '"""Mod.\n\nTraps: doc.\n"""\n# Traps: hash\nx = 1\n',
        "d.sql": "-- Traps: sql\nselect 1;\n",
    }
    repo, sha = branch(make_repo, commit_files, git, files, changed)
    plain = found(repo, sha)
    assert len(plain) == 6
    monkeypatch.setattr(traps_mod, "MAX_DIFF_LINES", 0)
    assert found(repo, sha) == plain
    monkeypatch.setattr(traps_mod, "MAX_DIFF_LINES", 10**9)
    monkeypatch.setattr(traps_mod, "MAX_DIFF_PAIRS", 0)
    assert found(repo, sha) == plain


@pytest.mark.parametrize(
    "text, count",
    [("", 0), ("a", 1), ("a\n", 1), ("a\n\n", 2), ("\n", 1), ("a\nb", 2), ("a\r\nb\r\n", 2)],
)
def test_line_count_is_the_number_of_editor_lines(text: str, count: int) -> None:
    from document_repo.remap import split_lines

    assert traps_mod._line_count(text) == count == len(split_lines(text))


def test_iter_comment_scan_is_comment_scan_without_the_list() -> None:
    from itertools import islice

    from document_repo.verify import comment_scan, iter_comment_scan

    lang = detect("x.sh")
    assert lang is not None
    lines = ["# a", "", "code", "/* x", "# b"]
    assert list(iter_comment_scan(iter(lines), lang)) == comment_scan(lines, lang)[0]
    assert list(iter_comment_scan(islice(lines, 1, 3), lang)) == comment_scan(lines[1:3], lang)[0]
    stream = iter_comment_scan(iter(["# a"] * 1_000_000), lang)
    assert next(stream) == (0, " a")


def test_harvest_raises_git_error_when_the_fallback_diff_fails(
    make_repo, commit_files, git, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, sha = branch(make_repo, commit_files, git, {"a.sh": "a\n"}, {"a.sh": "# Traps: x\na\n"})
    monkeypatch.setattr(traps_mod, "MAX_DIFF_LINES", 0)

    def broken(top, ref, rel):
        from document_repo.commit import GitError

        raise GitError("git diff failed: boom")

    monkeypatch.setattr(traps_mod, "_git_added_ranges", broken)
    code, out, err = run_traps(capsys, repo, sha)
    assert (code, out) == (2, None) and "boom" in err


def test_a_tokenizer_that_fails_midway_keeps_what_it_read(
    make_repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tokenize

    real = tokenize.generate_tokens

    def flaky(readline):
        seen = 0
        for tok in real(readline):
            if tok.type == tokenize.COMMENT:
                seen += 1
                if seen == 2:
                    raise tokenize.TokenError("boom")
            yield tok

    monkeypatch.setattr(traps_mod.tokenize, "generate_tokens", flaky)
    repo = make_repo({"a.py": "# Traps: a\nx = 1\n# Traps: b\ny = 2\n"})
    assert [t.text for t in harvest_traps(repo)] == ["a"]


@pytest.mark.parametrize(
    "line, expected",
    [
        (0, False),
        (1, True),
        (2, True),
        (3, False),
        (4, False),
        (5, False),
        (6, True),
        (7, True),
        (8, False),
    ],
)
def test_is_added_reads_one_based_lines_against_zero_based_half_open_ranges(
    line: int, expected: bool
) -> None:
    assert traps_mod._is_added([(0, 2), (5, 7)])(line) is expected
    assert traps_mod._is_added([])(line) is False


def _line_counts(base: str, after: str) -> tuple[int, int]:
    return traps_mod._line_count(base), traps_mod._line_count(after)


def test_the_line_limit_is_inclusive(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    base, after = IDENTICAL, "// Traps: x\n//\n" + IDENTICAL
    repo, sha = branch(make_repo, commit_files, git, {"a.js": base}, {"a.js": after})
    total = sum(_line_counts(base, after))
    monkeypatch.setattr(traps_mod, "MAX_DIFF_LINES", total)  # exactly at the limit: difflib
    assert [t.text for t in harvest_traps(repo, sha)] == ["x"]
    monkeypatch.setattr(traps_mod, "MAX_DIFF_LINES", total - 1)  # one over: git
    monkeypatch.setattr(traps_mod, "difflib", _NoDifflib)
    assert [t.text for t in harvest_traps(repo, sha)] == ["x"]
    monkeypatch.setattr(traps_mod, "MAX_DIFF_LINES", total)
    with pytest.raises(AssertionError, match="difflib was used"):
        harvest_traps(repo, sha)


def test_the_pair_limit_is_inclusive(
    make_repo, commit_files, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    base, after = IDENTICAL, "// Traps: x\n//\n" + IDENTICAL
    repo, sha = branch(make_repo, commit_files, git, {"a.js": base}, {"a.js": after})
    pairs = traps_mod._matching_pairs(base.splitlines(), after.splitlines())
    assert pairs == 60 * 60 + 0  # every line of the base equals 60 lines of the new file
    monkeypatch.setattr(traps_mod, "MAX_DIFF_PAIRS", pairs)  # exactly at the limit: difflib
    monkeypatch.setattr(traps_mod, "difflib", _NoDifflib)
    with pytest.raises(AssertionError, match="difflib was used"):
        harvest_traps(repo, sha)
    monkeypatch.setattr(traps_mod, "MAX_DIFF_PAIRS", pairs - 1)  # one over: git
    assert [t.text for t in harvest_traps(repo, sha)] == ["x"]


@pytest.mark.parametrize(
    "before, after, pairs",
    [
        (["a", "a"], ["a", "a", "a"], 6),
        (["a", "b"], ["b", "b", "c"], 2),
        (["a"], ["b"], 0),
        ([], ["a"], 0),
        (["x"] * 3, ["x"] * 4, 12),
    ],
)
def test_matching_pairs_is_the_sum_of_count_products(before, after, pairs) -> None:
    assert traps_mod._matching_pairs(before, after) == pairs


def test_a_trap_holds_no_more_than_the_cap_however_long_its_comment_runs() -> None:
    """The text is cut at the cap, but the lines past it must not be kept on the way there."""

    def entries():
        yield (1, 1, "Traps: start")
        for n in range(2, 300_000):
            yield (n, 1, "word " * 4)

    holder: list[Trap] = []
    peak = _peak_bytes(lambda: holder.extend(traps_mod._traps_in(entries(), "p")))
    assert len(holder) == 1 and holder[0].text.endswith(" ...")
    assert peak < 200_000, f"{peak} bytes held for one trap"


def test_added_ranges_of_an_empty_file_is_empty(make_repo) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    assert traps_mod._added_ranges(repo, None, "a.py", "", "") == []
    assert traps_mod._added_ranges(repo, "0" * 40, "a.py", "", "") == []


def test_a_new_file_in_before_mode_never_builds_a_matcher(
    make_repo, git, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No base means every line is new: the matcher's index of the file is memory for nothing."""
    repo = make_repo({"a.py": "x = 1\n"})
    sha = head(git, repo)
    (repo / "new.js").write_text("// Traps: new\n" + "// a\n" * 50)
    (repo / "new.sh").write_text("# Traps: new\n" + "# a\n" * 50)
    monkeypatch.setattr(traps_mod, "difflib", _NoDifflib)
    assert [t.path for t in harvest_traps(repo, sha)] == ["new.js", "new.sh"]


def test_python_entries_come_out_in_line_order_with_comments_and_docstrings_mixed() -> None:
    from document_repo.remap import split_lines

    text = (
        '"""Module.\n\nTraps: one.\n"""\n'  # 1-4
        "# Traps: two.\n"  # 5
        "class C:\n"  # 6
        '    """Class doc.\n    Traps: three.\n    """\n'  # 7-9
        "    # comment in the class\n"  # 10
        "    def m(self):\n"  # 11
        '        """Method doc.\n        Traps: four.\n        """\n'  # 12-14
        "        # Traps: five.\n"  # 15
        "        return 1\n"
    )
    lang = detect("x.py")
    assert lang is not None
    got = list(traps_mod._python_entries(text, split_lines(text), lang))
    assert [line for line, _key, _text in got] == sorted(line for line, _key, _text in got)
    assert [(line, body) for line, _key, body in got if body.startswith("Traps")] == [
        (3, "Traps: one."),
        (5, "Traps: two."),
        (8, "Traps: three."),
        (13, "Traps: four."),
        (15, "Traps: five."),
    ]


def test_git_ranges_ignore_a_user_inter_hunk_context(make_repo, commit_files, git) -> None:
    """``diff.interHunkContext`` would merge two inserts and report the owner's line as added."""
    repo, sha = branch(
        make_repo,
        commit_files,
        git,
        {"a.sh": "a\n# Traps: owner\nb\n"},
        {"a.sh": "a\n# x\n# Traps: owner\nb\n# y\n"},
    )
    git(repo, "config", "diff.interHunkContext", "100")
    assert traps_mod._git_added_ranges(repo, sha, "a.sh") == [(1, 2), (4, 5)]
