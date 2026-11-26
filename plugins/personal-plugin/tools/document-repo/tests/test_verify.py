import json
import subprocess
import sys
from pathlib import Path

import pytest

from document_repo.cli import main
from document_repo.languages import detect
from document_repo.verify import changed_files, comment_chunk_ok, verify_blobs, verify_file

BASE_PY = "def add(a, b):\n    return a + b\n"


def test_python_comments_and_docstrings_pass(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text(
        '"""Math helpers."""\n\n# Why: keep it simple.\ndef add(a, b):\n'
        '    """Add two numbers."""\n    return a + b  # sum\n'
    )
    r = verify_file(repo, "m.py")
    assert r.ok and r.method == "python-ast", r.detail


def test_python_docstring_added_to_pass_body(make_repo) -> None:
    repo = make_repo({"m.py": "def f():\n    pass\n"})
    (repo / "m.py").write_text('def f():\n    """Doc."""\n    pass\n')
    assert verify_file(repo, "m.py").ok


def test_python_code_change_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text("# note\ndef add(a, b):\n    return a - b\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and r.method == "python-ast"


def test_python_syntax_error_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text("def add(a, b:\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and "parse" in r.detail


def test_file_not_in_base_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "new.py").write_text("x = 1\n")
    r = verify_file(repo, "new.py")
    assert not r.ok and r.method == "none"


def test_unknown_language_fails(make_repo) -> None:
    repo = make_repo({"d.json": "{}\n"})
    assert not verify_file(repo, "d.json").ok


SQL = "select 1;\nselect 2;\n"


@pytest.mark.parametrize(
    "after",
    [
        "-- Header\nselect 1;\nselect 2;\n",
        "/* block\n   more */\nselect 1;\nselect 2;\n",
        "select 1;\n\n-- why the second query\nselect 2;\n",
        "/* one-line block */\nselect 1;\nselect 2;\n",
    ],
)
def test_sql_comment_only_passes(make_repo, after: str) -> None:
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").write_text(after)
    r = verify_file(repo, "q.sql")
    assert r.ok and r.method == "comment-lines", r.detail


@pytest.mark.parametrize(
    "after,needle",
    [
        ("select 1;\nselect 3;\n", "replace"),
        ("select 1;\n", "delete"),
        ("select 1; -- trailing\nselect 2;\n", "replace"),
        ("/* open\nselect 1;\nselect 2;\n", "unterminated"),
        ("/* x */ select 0;\nselect 1;\nselect 2;\n", "code after"),
        ("select 0;\nselect 1;\nselect 2;\n", "non-comment"),
    ],
)
def test_sql_negative_cases_fail(make_repo, after: str, needle: str) -> None:
    # Negative tests: a guard that cannot fail is worse than none (repo rule).
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").write_text(after)
    r = verify_file(repo, "q.sql")
    assert not r.ok and needle in r.detail, r.detail


def test_shell_code_added_fails(make_repo) -> None:
    repo = make_repo({"run.sh": "#!/bin/sh\necho a\n"})
    (repo / "run.sh").write_text("#!/bin/sh\n# say a\necho a\necho b\n")
    assert not verify_file(repo, "run.sh").ok


def test_comment_chunk_block_end_must_close_line() -> None:
    lang = detect("x.css")
    assert comment_chunk_ok(["/* a", " b */"], lang) == (True, "")
    ok, why = comment_chunk_ok(["/* a", " b */ x {}"], lang)
    assert not ok and "code after" in why


def test_changed_files(make_repo, marker) -> None:
    repo = make_repo(
        {
            "a.py": "x = 1\n",
            "README.md": "# r\n",
            "explorer/app.js": "x\n",
            **marker,
            "b.py": "y = 1\n",
        }
    )
    (repo / "a.py").write_text("# c\nx = 1\n")
    (repo / "README.md").write_text("# r2\n")
    (repo / "explorer/app.js").write_text("y\n")
    assert changed_files(repo, "HEAD") == ["a.py"]


def test_cli_verify_exit_codes(make_repo, capsys) -> None:
    repo = make_repo({"a.py": "x = 1\n", "b.py": "y = 1\n"})
    (repo / "a.py").write_text("# ok\nx = 1\n")
    assert main(["verify", "--repo", str(repo), "a.py"]) == 0
    (repo / "b.py").write_text("y = 2\n")
    capsys.readouterr()
    assert main(["verify", "--repo", str(repo), "--changed"]) == 1
    results = json.loads(capsys.readouterr().out)
    assert {r["path"]: r["ok"] for r in results} == {"a.py": True, "b.py": False}


def test_cli_verify_needs_files_or_changed(make_repo) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    assert main(["verify", "--repo", str(repo)]) == 2


# Fail-closed branches the brief's tests do not reach.
def test_python_base_that_does_not_parse_fails(make_repo) -> None:
    repo = make_repo({"m.py": "def add(a, b:\n"})
    (repo / "m.py").write_text("# note\ndef add(a, b:\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and r.method == "python-ast" and "base version does not parse" in r.detail


def test_non_utf8_base_fails(make_repo) -> None:
    repo = make_repo({"q.sql": b"select '\xe9';\n"})
    (repo / "q.sql").write_text("-- note\nselect 1;\n", encoding="utf-8")
    r = verify_file(repo, "q.sql")
    assert not r.ok and r.method == "none" and "UTF-8" in r.detail


def test_deleted_working_file_fails(make_repo) -> None:
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").unlink()
    r = verify_file(repo, "q.sql")
    assert not r.ok and r.method == "none" and "cannot read edited file" in r.detail


# ---------------------------------------------------------------------------
# Task 4b: verifier hardening. Every case in FALSE_PASSES returned ok=True before the guards
# existed (a false pass); each now fails with the named guard. POSITIVE_CASES keep ordinary
# comment insertions passing in every language.
# ---------------------------------------------------------------------------


def _run(make_repo, rel: str, before: str, after: str):
    """Commit ``before`` (bytes, so CR survives), write ``after`` to the work tree, verify."""
    repo = make_repo({rel: before.encode("utf-8")})
    (repo / rel).write_bytes(after.encode("utf-8"))
    return verify_file(repo, rel)


DIRECTIVE = "inserted directive-like comment"
CONT_END = "comment ends with a line continuation"
HEADER = "inserted above a protected header line"
EOL = "line endings changed"
VERBATIM = "inside a verbatim region"
AFTER_CONT = "after a line continuation"
BLOCK_TAIL = "would join the block scalar"

FALSE_PASSES = [
    # A1: line endings.
    ("sh-lf-to-crlf", "run.sh", "#!/bin/sh\necho a\n", "#!/bin/sh\r\n# a\r\necho a\r\n", EOL),
    ("py-crlf-to-lf", "m.py", "x = 1\r\ny = 2\r\n", "# c\nx = 1\ny = 2\n", EOL),
    ("sql-crlf-comment-in-lf", "q.sql", "select 1;\n", "-- c\r\nselect 1;\n", EOL),
    ("sql-lf-comment-in-crlf", "q.sql", "select 1;\r\n", "-- c\nselect 1;\r\n", EOL),
    ("sh-formfeed-inserted", "run.sh", "echo a\n", "# c\x0cecho a\n", "non-newline line break"),
    ("css-formfeed-base", "s.css", "a{}\x0cb{}\n", "a{}\x0c/* c */\nb{}\n", "physical line"),
    # A2: directive-like inserted comments.
    ("py-noqa", "m.py", "x = 1\n", "# noqa\nx = 1\n", DIRECTIVE),
    ("py-type-ignore", "m.py", "x = 1\n", "# type: ignore\nx = 1\n", DIRECTIVE),
    ("py-pylint", "m.py", "x = 1\n", "# pylint: disable=all\nx = 1\n", DIRECTIVE),
    ("py-fmt", "m.py", "x = 1\n", "# fmt: off\nx = 1\n", DIRECTIVE),
    ("py-isort", "m.py", "x = 1\n", "# isort: skip_file\nx = 1\n", DIRECTIVE),
    ("py-pyright", "m.py", "x = 1\n", "# pyright: basic\nx = 1\n", DIRECTIVE),
    ("py-mypy", "m.py", "x = 1\n", "# mypy: ignore-errors\nx = 1\n", DIRECTIVE),
    ("py-pragma", "m.py", "x = 1\n", "x = 1\n# pragma: no cover\n", DIRECTIVE),
    ("py-shebang", "m.py", "x = 1\n", "#!/usr/bin/env python3\nx = 1\n", DIRECTIVE),
    ("py-cookie-line1", "m.py", "x = 1\n", "# -*- coding: latin-1 -*-\nx = 1\n", DIRECTIVE),
    (
        "py-cookie-line2",
        "m.py",
        "x = 1\n",
        "# c\n# vim: set fileencoding=ascii :\nx = 1\n",
        DIRECTIVE,
    ),
    ("go-build", "m.go", "package m\n", "//go:build ignore\n\npackage m\n", DIRECTIVE),
    ("go-plus-build", "m.go", "package m\n", "// +build ignore\n\npackage m\n", DIRECTIVE),
    ("go-line", "m.go", "package m\n", "package m\n//line other.go:10\n", DIRECTIVE),
    ("sh-shellcheck", "a.sh", "echo $x\n", "# shellcheck disable=SC2086\necho $x\n", DIRECTIVE),
    ("sh-shebang-later", "a.sh", "echo a\n", "echo a\n#!/bin/bash\n", DIRECTIVE),
    ("sql-mysql-exec", "q.sql", "select 1;\n", "/*! SET x = 1 */\nselect 1;\n", DIRECTIVE),
    (
        "docker-syntax",
        "Dockerfile",
        "FROM a\n",
        "# syntax=docker/dockerfile:1\nFROM a\n",
        DIRECTIVE,
    ),
    ("docker-escape", "Dockerfile", "FROM a\n", "# ESCAPE = `\nFROM a\n", DIRECTIVE),
    ("docker-check", "Dockerfile", "FROM a\n", "#check=skip=all\nFROM a\n", DIRECTIVE),
    # A3: the inserted comment itself ends in a backslash and swallows the next line.
    (
        "make-comment-backslash",
        "Makefile",
        "all:\n\techo a\n",
        "# note \\\nall:\n\techo a\n",
        CONT_END,
    ),
    ("c-comment-backslash", "m.c", "int x;\n", "// note \\\nint x;\n", CONT_END),
    ("py-comment-backslash", "m.py", "x = 1\n", "# note \\\nx = 1\n", CONT_END),
    # A4: inserted above a protected header line.
    ("sh-above-shebang", "a.sh", "#!/bin/sh\necho a\n", "# hdr\n#!/bin/sh\necho a\n", HEADER),
    (
        "py-above-shebang",
        "m.py",
        "#!/usr/bin/env python3\nx = 1\n",
        "# h\n#!/usr/bin/env python3\nx = 1\n",
        HEADER,
    ),
    (
        "py-above-cookie",
        "m.py",
        "# -*- coding: utf-8 -*-\nx = 1\n",
        "# h\n# -*- coding: utf-8 -*-\nx = 1\n",
        HEADER,
    ),
    (
        "docker-between-directives",
        "Dockerfile",
        "# syntax=d/d:1\n# escape=`\nFROM a\n",
        "# syntax=d/d:1\n# note\n# escape=`\nFROM a\n",
        HEADER,
    ),
    # B5: existing Python docstrings are frozen (they are runtime data: PLY, argparse, doctest).
    (
        "py-ply-docstring",
        "m.py",
        'def p_e(p):\n    "e : e PLUS t"\n    p[0] = 1\n',
        'def p_e(p):\n    "e : e MINUS t"\n    p[0] = 1\n',
        "existing docstring changed: p_e",
    ),
    (
        "py-module-docstring",
        "m.py",
        '"""Usage: tool A."""\nx = 1\n',
        '"""Usage: tool B."""\nx = 1\n',
        "existing docstring changed: <module>",
    ),
    (
        "py-docstring-removed",
        "m.py",
        'def f():\n    """Doc."""\n',
        "def f():\n    pass\n",
        "existing docstring changed: f",
    ),
    (
        "py-dup-name-docstring",
        "m.py",
        'class C:\n    def x(self):\n        """A."""\n    def x(self):\n        """B."""\n',
        'class C:\n    def x(self):\n        """A."""\n    def x(self):\n        """Z."""\n',
        "existing docstring changed: C.x#1",
    ),
    # C6: inserted after a base line that ends in a continuation.
    ("sh-continuation", "a.sh", "echo a \\\n  b\n", "echo a \\\n# c\n  b\n", AFTER_CONT),
    ("make-continuation", "Makefile", "X = a \\\n  b\n", "X = a \\\n\n  b\n", AFTER_CONT),
    (
        "c-macro-continuation",
        "m.h",
        "#define M(x) \\\n  (x)\n",
        "#define M(x) \\\n// c\n  (x)\n",
        AFTER_CONT,
    ),
    # C7: verbatim regions, where a new line becomes data.
    ("sh-heredoc", "a.sh", "cat <<EOF\nhi\nEOF\n", "cat <<EOF\n# c\nhi\nEOF\n", VERBATIM),
    (
        "sh-heredoc-dash-quoted",
        "a.sh",
        "cat <<-'END'\n\thi\n\tEND\necho\n",
        "cat <<-'END'\n\thi\n# c\n\tEND\necho\n",
        VERBATIM,
    ),
    (
        "sh-heredoc-indented-word-is-body",
        "a.sh",
        "cat <<EOF\n  EOF\nhi\nEOF\n",
        "cat <<EOF\n  EOF\n# c\nhi\nEOF\n",
        VERBATIM,
    ),
    ("sh-multiline-dq", "a.sh", 'MSG="one\ntwo"\n', 'MSG="one\n# c\ntwo"\n', VERBATIM),
    (
        "docker-heredoc",
        "Dockerfile",
        "FROM a\nRUN <<EOF\necho hi\nEOF\n",
        "FROM a\nRUN <<EOF\n# c\necho hi\nEOF\n",
        VERBATIM,
    ),
    (
        "make-define",
        "Makefile",
        "define T\nline\nendef\n",
        "define T\n# c\nline\nendef\n",
        VERBATIM,
    ),
    (
        "yaml-block-inside",
        "ci.yml",
        "run: |\n  make\n  test\n",
        "run: |\n  make\n  # c\n  test\n",
        VERBATIM,
    ),
    (
        "yaml-block-one-past",
        "ci.yml",
        "a:\n  run: |\n    make\n  b: 1\n",
        "a:\n  run: |\n    make\n    # c\n  b: 1\n",
        BLOCK_TAIL,
    ),
    ("yaml-folded-after-dash", "ci.yml", "- >-\n  text\n", "- >-\n  # c\n  text\n", VERBATIM),
    ("yaml-quoted-multiline", "c.yml", 'k: "a\n  b"\n', 'k: "a\n  # c\n  b"\n', VERBATIM),
    (
        "yaml-plain-multiline",
        "c.yml",
        "k: a long\n  plain scalar\nj: 1\n",
        "k: a long\n\n  plain scalar\nj: 1\n",
        VERBATIM,
    ),
    # SE-H2: a plain scalar in a sequence entry continues on any line deeper than its dash.
    ("yaml-seq-plain-multiline", "c.yml", "- foo\n  bar\n", "- foo\n# c\n  bar\n", VERBATIM),
    (
        "yaml-nested-seq-plain-multiline",
        "c.yml",
        "a:\n  - foo\n    bar\n",
        "a:\n  - foo\n  # c\n    bar\n",
        VERBATIM,
    ),
    (
        "yaml-seq-plain-multiline-shallow",
        "c.yml",
        "- foo\n bar\n",
        "- foo\n # c\n bar\n",
        VERBATIM,
    ),
    ("sql-string", "q.sql", "select 'a\nb';\n", "select 'a\n-- c\nb';\n", VERBATIM),
    (
        "sql-dollar",
        "q.sql",
        "create function f() returns int as $$\nselect 1;\n$$ language sql;\n",
        "create function f() returns int as $$\n-- c\nselect 1;\n$$ language sql;\n",
        VERBATIM,
    ),
    (
        "sql-dollar-tag",
        "q.sql",
        "do $body$\nbegin end\n$body$;\n",
        "do $body$\n\nbegin end\n$body$;\n",
        VERBATIM,
    ),
    (
        "sql-copy-stdin",
        "d.sql",
        "COPY t (a) FROM stdin;\n1\n\\.\n",
        "COPY t (a) FROM stdin;\n-- c\n1\n\\.\n",
        VERBATIM,
    ),
    ("toml-basic-ml", "c.toml", 'k = """\na\n"""\n', 'k = """\n# c\na\n"""\n', VERBATIM),
    ("toml-literal-ml", "c.toml", "k = '''\na\n'''\n", "k = '''\n# c\na\n'''\n", VERBATIM),
    ("go-raw-string", "m.go", "var s = `a\nb`\n", "var s = `a\n// c\nb`\n", VERBATIM),
    (
        "go-cgo-preamble",
        "m.go",
        'package m\n\n// #include <stdio.h>\nimport "C"\n',
        'package m\n\n// #include <stdio.h>\n// c\nimport "C"\n',
        VERBATIM,
    ),
    (
        "java-text-block",
        "A.java",
        'String s = """\n  a\n  """;\n',
        'String s = """\n  // c\n  a\n  """;\n',
        VERBATIM,
    ),
    (
        "cs-raw",
        "A.cs",
        'var s = """\n  a\n  """;\n',
        'var s = """\n  // c\n  a\n  """;\n',
        VERBATIM,
    ),
    ("cs-verbatim", "A.cs", 'var s = @"a\nb";\n', 'var s = @"a\n// c\nb";\n', VERBATIM),
    ("cpp-raw", "a.cpp", 'auto s = R"x(a\nb)x";\n', 'auto s = R"x(a\n// c\nb)x";\n', VERBATIM),
    # SE-C1: a C++ header is lexed as C++, so a multi-line raw string in it is data, not code.
    (
        "h-cpp-raw",
        "q.h",
        'static const char* kQuery = R"(\nSELECT id\nFROM users\n)";\n',
        'static const char* kQuery = R"(\nSELECT id\n// Only active users are selected here.\n'
        'FROM users\n)";\n',
        VERBATIM,
    ),
    ("rust-raw-hash", "a.rs", 'let s = r#"a\nb"#;\n', 'let s = r#"a\n// c\nb"#;\n', VERBATIM),
    ("rust-plain-multiline", "a.rs", 'let s = "a\nb";\n', 'let s = "a\n// c\nb";\n', VERBATIM),
    (
        "html-textarea",
        "i.html",
        "<textarea>\na\n</textarea>\n",
        "<textarea>\n<!-- c -->\na\n</textarea>\n",
        VERBATIM,
    ),
    (
        "html-script",
        "i.html",
        "<SCRIPT>\nf();\n</SCRIPT>\n",
        "<SCRIPT>\n<!-- c -->\nf();\n</SCRIPT>\n",
        VERBATIM,
    ),
    ("html-pre", "i.html", "<pre>\na\n</pre>\n", "<pre>\na\n<!-- c -->\n</pre>\n", VERBATIM),
    (
        "html-style",
        "i.html",
        "<style>\na{}\n</style>\n",
        "<style>\n<!-- c -->\na{}\n</style>\n",
        VERBATIM,
    ),
    (
        "html-inside-comment",
        "i.html",
        "<!--\nold\n-->\n<p>x</p>\n",
        "<!--\n<!-- c -->\nold\n-->\n<p>x</p>\n",
        VERBATIM,
    ),
    ("css-inside-comment", "s.css", "/*\nold\n*/\na{}\n", "/*\n/* c */\nold\n*/\na{}\n", VERBATIM),
    ("sh-unterminated-quote", "a.sh", "echo 'a\necho b\n", "echo 'a\necho b\n# c\n", VERBATIM),
]


@pytest.mark.parametrize(
    "rel,before,after,needle", [c[1:] for c in FALSE_PASSES], ids=[c[0] for c in FALSE_PASSES]
)
def test_false_pass_now_fails(make_repo, rel: str, before: str, after: str, needle: str) -> None:
    r = _run(make_repo, rel, before, after)
    assert not r.ok and needle in r.detail, (r.method, r.detail)


POSITIVE_CASES = [
    (
        "python",
        "m.py",
        "#!/usr/bin/env python3\nimport os\n\n\ndef f():\n    return os.sep\n",
        (
            "#!/usr/bin/env python3\n# Path helpers.\nimport os\n\n\ndef f():\n"
            '    """Return the separator."""\n    # Why: portable.\n    return os.sep  # sep\n'
        ),
    ),
    ("python-crlf", "m.py", "x = 1\r\ny = 2\r\n", "# c\r\nx = 1\r\ny = 2\r\n"),
    (
        "sql",
        "q.sql",
        (
            "create function f() returns int as $$ select 1 $$ language sql;\nselect 'it''s';\n"
            "-- it's fine\nselect 2;\n"
        ),
        (
            "-- Schema.\ncreate function f() returns int as $$ select 1 $$ language sql;\n"
            "-- Quote test.\nselect 'it''s';\n-- it's fine\n\n/* second */\nselect 2;\n"
        ),
    ),
    (
        "shell",
        "a.sh",
        '#!/bin/sh\n# cat <<EOF\ncat <<EOF\nhi\nEOF\necho "${#x}" # it\'s\n',
        (
            "#!/bin/sh\n# Header.\n# cat <<EOF\ncat <<EOF\nhi\nEOF\n# After heredoc.\n"
            'echo "${#x}" # it\'s\n'
        ),
    ),
    (
        "yaml",
        "ci.yml",
        (
            "# key: |\nname: ci\non: push\njobs:\n  build:\n    steps:\n      - run: |\n"
            "          make\n\n      - name: x\n        uses: a/b\n"
        ),
        (
            "# key: |\n# Workflow.\nname: ci\non: push\n# Jobs.\njobs:\n  build:\n    # Steps.\n"
            "    steps:\n      - run: |\n          make\n\n      - name: x\n        # Action.\n"
            "        uses: a/b\n"
        ),
    ),
    (
        "toml",
        "c.toml",
        '# """\n[a]\nk = """\nx\n"""\nj = \'it\'\n',
        '# """\n# Section a.\n[a]\nk = """\nx\n"""\n# j.\nj = \'it\'\n',
    ),
    (
        "dockerfile",
        "Dockerfile",
        '# syntax=docker/dockerfile:1\nFROM alpine\nRUN <<EOF\necho\nEOF\nCMD ["x"]\n',
        (
            "# syntax=docker/dockerfile:1\n# Base image.\nFROM alpine\nRUN <<EOF\necho\nEOF\n"
            '# Entry.\nCMD ["x"]\n'
        ),
    ),
    (
        "make",
        "Makefile",
        "define T\nx\nendef\nall:\n\techo a\n",
        "# Template.\ndefine T\nx\nendef\n# Default target.\nall:\n\techo a\n",
    ),
    (
        "css",
        "s.css",
        "a { color: red; }\nb::after { content: '//'; }\n",
        "/* Links. */\na { color: red; }\n\n/* After. */\nb::after { content: '//'; }\n",
    ),
    (
        "html",
        "i.html",
        "<!-- <script> -->\n<div>\n<p>x</p>\n</div>\n<pre>a</pre>\n<p>y</p>\n",
        (
            "<!-- <script> -->\n<div>\n<!-- Paragraph. -->\n<p>x</p>\n</div>\n<pre>a</pre>\n"
            "<!-- After pre. -->\n<p>y</p>\n"
        ),
    ),
    (
        "go",
        "m.go",
        "package m\n\n// use `x`\nvar s = `a\nb`\n\nfunc F() {}\n",
        (
            "// Package m does things.\npackage m\n\n// use `x`\nvar s = `a\nb`\n\n"
            "// F does nothing.\nfunc F() {}\n"
        ),
    ),
    (
        "rust",
        "a.rs",
        "fn f<'a>(x: &'a str) -> &'a str {\n    x\n}\nlet c = '\"';\n",
        (
            "/// Identity.\nfn f<'a>(x: &'a str) -> &'a str {\n    // Why: borrow.\n    x\n}\n"
            "let c = '\"';\n"
        ),
    ),
    (
        "java",
        "A.java",
        'class A {\n  String s = """\n    a\n    """;\n  char q = \'"\';\n}\n',
        (
            '/** A class. */\nclass A {\n  String s = """\n    a\n    """;\n  // Quote char.\n'
            "  char q = '\"';\n}\n"
        ),
    ),
    (
        "c",
        "m.c",
        "#include <stdio.h>\nint main(void) {\n  return 0;\n}\n",
        "/* Entry point. */\n#include <stdio.h>\nint main(void) {\n  // Done.\n  return 0;\n}\n",
    ),
    (
        "c-header",
        "m.h",
        "#ifndef M_H\n#define M_H\nint add(int a, int b);\n#endif\n",
        "#ifndef M_H\n#define M_H\n/* Add two ints. */\nint add(int a, int b);\n// end\n#endif\n",
    ),
    (
        "cpp",
        "a.cpp",
        'auto s = R"(a)";\nint n = 1\'000;\nint main() {}\n',
        'auto s = R"(a)";\n// Thousand.\nint n = 1\'000;\nint main() {}\n',
    ),
    ("csharp", "A.cs", 'var s = @"a";\nclass A {}\n', 'var s = @"a";\n// A type.\nclass A {}\n'),
    (
        "sh-after-shebang-crlf-free",
        "b.sh",
        "#!/bin/sh\necho a\n",
        "#!/bin/sh\n\n# Say a.\necho a\n# end\n",
    ),
    ("no-trailing-newline", "q.sql", "select 1;", "select 1;\n-- end\n"),
]


@pytest.mark.parametrize(
    "rel,before,after", [c[1:] for c in POSITIVE_CASES], ids=[c[0] for c in POSITIVE_CASES]
)
def test_comment_insertions_still_pass(make_repo, rel: str, before: str, after: str) -> None:
    r = _run(make_repo, rel, before, after)
    assert r.ok, (r.method, r.detail)


@pytest.fixture
def ts_ok(monkeypatch) -> None:
    """Stand in for Task 5's ts-printer: it says "comments only", so the common guards decide.

    JS/TS are verified only by ts-printer (fix round 3, D1). These tests exercise the guards that
    run after it passes, not the printer itself.
    """
    import document_repo.verify as verify_mod

    def fake_ts(repo, rel, before, after):
        return verify_mod.Result(rel, "ts-printer", True)

    monkeypatch.setattr(verify_mod, "_ts_verify", fake_ts)


#: Directive-like comments in JS/TS: the common guards must fail them after a passing ts-printer.
JS_GUARD_FAILS = [
    ("ts-ignore", "a.ts", "f();\n", "// @ts-ignore\nf();\n", DIRECTIVE),
    ("ts-expect-error", "a.ts", "f();\n", "// @ts-expect-error\nf();\n", DIRECTIVE),
    ("ts-nocheck", "a.ts", "f();\n", "// @ts-nocheck\nf();\n", DIRECTIVE),
    ("js-ts-check", "a.js", "f();\n", "// @ts-check\nf();\n", DIRECTIVE),
    ("js-eslint-disable", "a.js", "f();\n", "/* eslint-disable */\nf();\n", DIRECTIVE),
    ("js-eslint-enable", "a.js", "f();\n", "f();\n// eslint-enable\n", DIRECTIVE),
    ("js-prettier", "a.js", "f();\n", "// prettier-ignore\nf();\n", DIRECTIVE),
    ("js-istanbul", "a.js", "f();\n", "/* istanbul ignore next */\nf();\n", DIRECTIVE),
    ("js-c8", "a.js", "f();\n", "/* c8 ignore next */\nf();\n", DIRECTIVE),
    ("js-biome", "a.js", "f();\n", "// biome-ignore lint: x\nf();\n", DIRECTIVE),
    ("js-jsx-pragma", "a.jsx", "f();\n", "/** @jsx h */\nf();\n", DIRECTIVE),
    ("js-jsx-import", "a.tsx", "f();\n", "/** @jsxImportSource preact */\nf();\n", DIRECTIVE),
    ("js-jsx-runtime", "a.jsx", "f();\n", "/** @jsxRuntime classic */\nf();\n", DIRECTIVE),
    ("js-flow", "a.js", "f();\n", "// @flow\nf();\n", DIRECTIVE),
    ("ts-triple-slash", "a.ts", "f();\n", '/// <reference types="node" />\nf();\n', DIRECTIVE),
]


@pytest.mark.parametrize(
    "rel,before,after,needle", [c[1:] for c in JS_GUARD_FAILS], ids=[c[0] for c in JS_GUARD_FAILS]
)
def test_js_directive_fails_after_ts_printer(
    make_repo, ts_ok, rel: str, before: str, after: str, needle: str
) -> None:
    r = _run(make_repo, rel, before, after)
    assert not r.ok and r.method == "ts-printer" and needle in r.detail, (r.method, r.detail)


#: Ordinary JS/TS comment insertions: the common guards must not false-fail them.
JS_POSITIVE = [
    (
        "typescript",
        "a.ts",
        "const t = `a\nb`;\nexport function f(): number {\n  return 1;\n}\n",
        (
            "const t = `a\nb`;\n\n/** Returns one. */\nexport function f(): number {\n"
            "  // Why: constant.\n  return 1;\n}\n"
        ),
    ),
    (
        "javascript",
        "a.js",
        "const r = 'x'; // it's\nmodule.exports = r;\n",
        "// Module header.\nconst r = 'x'; // it's\n/* export */\nmodule.exports = r;\n",
    ),
    (
        "tsx-generic",
        "a.ts",
        "const m = new Map<string, number>();\nfunction g<T>(x: T): T {\n  return x;\n}\n",
        (
            "const m = new Map<string, number>();\n// Identity.\nfunction g<T>(x: T): T {\n"
            "  return x;\n}\n"
        ),
    ),
]


@pytest.mark.parametrize(
    "rel,before,after", [c[1:] for c in JS_POSITIVE], ids=[c[0] for c in JS_POSITIVE]
)
def test_js_comment_insertions_pass_after_ts_printer(
    make_repo, ts_ok, rel: str, before: str, after: str
) -> None:
    r = _run(make_repo, rel, before, after)
    assert r.ok and r.method == "ts-printer", (r.method, r.detail)


def test_ascii_cookie_rejects_non_ascii_comment(make_repo) -> None:
    # ast.parse(str) ignores the cookie; the real import would fail on the non-ASCII byte.
    before = "# -*- coding: ascii -*-\nx = 1\n"
    r = _run(make_repo, "m.py", before, before + "# caf\u00e9\n")
    assert not r.ok and r.method == "python-ast" and "does not parse" in r.detail, r.detail


def test_new_docstring_with_doctest_fails(make_repo) -> None:
    r = _run(
        make_repo,
        "m.py",
        "def f():\n    pass\n",
        'def f():\n    """Doc.\n\n    >>> f()\n    """\n    pass\n',
    )
    assert not r.ok and "doctest" in r.detail, r.detail


def test_shebang_removed_fails(make_repo) -> None:
    # Deleting or rewriting a directive passes python-ast (comments are invisible to it).
    r = _run(make_repo, "m.py", "#!/usr/bin/env python3\nx = 1\n", "x = 1\n")
    assert not r.ok and "removed or changed directive-like" in r.detail, r.detail


def test_insert_below_next_line_directive_fails(make_repo, ts_ok) -> None:
    before = "// eslint-disable-next-line no-eval\neval(x);\n"
    after = "// eslint-disable-next-line no-eval\n// Why: legacy.\neval(x);\n"
    r = _run(make_repo, "a.js", before, after)
    assert not r.ok and "below a directive-like comment" in r.detail, r.detail


def test_make_tab_indented_comment_fails(make_repo) -> None:
    # A tab-indented line in a recipe is a shell command that make echoes, not a make comment.
    r = _run(make_repo, "Makefile", "all:\n\techo a\n", "all:\n\t# say a\n\techo a\n")
    assert not r.ok and "recipe line" in r.detail, r.detail


def test_sql_dashdash_without_space_fails(make_repo) -> None:
    # MySQL needs whitespace after "--"; "--x" is two minus signs.
    r = _run(make_repo, "q.sql", "select 1;\n", "--note\nselect 1;\n")
    assert not r.ok and "--" in r.detail, r.detail


def test_bom_added_fails(make_repo) -> None:
    r = _run(make_repo, "m.py", "x = 1\n", "\ufeff# c\nx = 1\n")
    assert not r.ok and "byte order mark" in r.detail, r.detail


def test_autocrlf_checkout_is_not_a_line_ending_change(make_repo, git) -> None:
    # With core.autocrlf the work tree is CRLF while the blob is LF; compare like checkout does.
    repo = make_repo({"q.sql": b"select 1;\n"})
    git(repo, "config", "core.autocrlf", "true")
    (repo / "q.sql").write_bytes(b"-- c\r\nselect 1;\r\n")
    r = verify_file(repo, "q.sql")
    assert r.ok, r.detail


def test_guard_runs_after_any_passing_method(make_repo, monkeypatch) -> None:
    # A future ts-printer pass must still go through the common guards.
    import document_repo.verify as verify_mod

    def fake_ts(repo, rel, before, after):
        return verify_mod.Result(rel, "ts-printer", True)

    monkeypatch.setattr(verify_mod, "_ts_verify", fake_ts)
    r = _run(make_repo, "a.ts", "f();\n", "// @ts-ignore\nf();\n")
    assert not r.ok and r.method == "ts-printer" and DIRECTIVE in r.detail, r.detail


# ---------------------------------------------------------------------------
# Fix round 1. Item 1: C# XML doc comments pass; the triple-slash pattern is TS/JS only.
# Item 2: a comment right after a YAML block scalar passes unless it is indented deeper than the
# opener line.
# ---------------------------------------------------------------------------

CS_BEFORE = "class Calc {\n    public int Add(int a, int b) {\n        return a + b;\n    }\n}\n"
CS_AFTER = (
    "class Calc {\n"
    "    /// <summary>\n"
    "    /// Adds two numbers.\n"
    "    /// </summary>\n"
    '    /// <param name="a">Left operand.</param>\n'
    '    /// <param name="b">Right operand.</param>\n'
    "    /// <returns>The sum.</returns>\n"
    "    public int Add(int a, int b) {\n        return a + b;\n    }\n}\n"
)


def test_csharp_xml_doc_comments_pass(make_repo) -> None:
    r = _run(make_repo, "Calc.cs", CS_BEFORE, CS_AFTER)
    assert r.ok and r.method == "comment-lines", (r.method, r.detail)


@pytest.mark.parametrize("rel", ["a.ts", "a.tsx", "a.mts", "a.js", "a.jsx", "a.mjs"])
def test_triple_slash_directive_still_fails_in_js_and_ts(make_repo, ts_ok, rel: str) -> None:
    r = _run(make_repo, rel, "f();\n", '/// <reference path="x" />\nf();\n')
    assert not r.ok and DIRECTIVE in r.detail, (r.method, r.detail)


@pytest.mark.parametrize(
    "rel,before,after",
    [
        ("m.go", "package m\n\nfunc F() {}\n", "package m\n\n// F does nothing.\nfunc F() {}\n"),
        ("a.rs", "fn f() {}\n", "// Does nothing.\nfn f() {}\n"),
        ("A.java", "class A {\n  int x;\n}\n", "class A {\n  // The count.\n  int x;\n}\n"),
        (
            "m.c",
            "int main(void) {\n  return 0;\n}\n",
            "// Entry point.\nint main(void) {\n  return 0;\n}\n",
        ),
        ("a.cpp", "int main() {}\n", "// Entry point.\nint main() {}\n"),
        ("A.cs", "class A {\n  int x;\n}\n", "class A {\n  // The count.\n  int x;\n}\n"),
    ],
    ids=["go", "rust", "java", "c", "cpp", "csharp"],
)
def test_c_family_slash_comment_insertions_pass(
    make_repo, rel: str, before: str, after: str
) -> None:
    r = _run(make_repo, rel, before, after)
    assert r.ok and r.method == "comment-lines", (r.method, r.detail)


GHA_BEFORE = (
    "name: ci\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
    "      - run: |\n          make build\n          make test\n"
    "      - name: next\n        run: echo done\n"
)


def _gha_with(inserted: list[str], at: int) -> str:
    lines = GHA_BEFORE.splitlines()
    return "\n".join([*lines[:at], *inserted, *lines[at:]]) + "\n"


def test_yaml_comment_after_block_at_step_indent_passes(make_repo) -> None:
    # Directly above "- name: next", at the same indentation as "- name:" (and "- run:").
    r = _run(make_repo, "ci.yml", GHA_BEFORE, _gha_with(["      # Report the result."], 9))
    assert r.ok and r.method == "comment-lines", (r.method, r.detail)


def test_yaml_comment_after_block_dedented_passes(make_repo) -> None:
    r = _run(make_repo, "ci.yml", GHA_BEFORE, _gha_with(["    # Steps continue.", ""], 9))
    assert r.ok, (r.method, r.detail)


def test_yaml_comment_after_block_deeper_than_run_key_fails(make_repo) -> None:
    # "run:" is at column 8; a comment at column 10 is content of the literal block.
    r = _run(make_repo, "ci.yml", GHA_BEFORE, _gha_with(["          # Report the result."], 9))
    assert not r.ok and BLOCK_TAIL in r.detail, (r.method, r.detail)


@pytest.mark.parametrize("indent", [7, 8, 10, 12])
def test_yaml_comment_after_block_deeper_than_opener_fails(make_repo, indent: int) -> None:
    # The threshold is the opener LINE's indent (6 here), not the key column, so it fails closed.
    r = _run(make_repo, "ci.yml", GHA_BEFORE, _gha_with([" " * indent + "# Report."], 9))
    assert not r.ok and BLOCK_TAIL in r.detail, (r.method, r.detail)


def test_yaml_comment_inside_block_fails(make_repo) -> None:
    r = _run(make_repo, "ci.yml", GHA_BEFORE, _gha_with(["          # Note."], 8))
    assert not r.ok and VERBATIM in r.detail, (r.method, r.detail)


def test_yaml_comment_before_first_block_line_fails(make_repo) -> None:
    r = _run(make_repo, "ci.yml", GHA_BEFORE, _gha_with(["      # Note."], 7))
    assert not r.ok and VERBATIM in r.detail, (r.method, r.detail)


def test_yaml_comment_appended_after_final_block_passes(make_repo) -> None:
    r = _run(make_repo, "ci.yml", "run: |\n  make\n", "run: |\n  make\n# The end.\n")
    assert r.ok, (r.method, r.detail)


def test_yaml_blank_line_after_keep_block_fails(make_repo) -> None:
    before = "run: |+\n  make\nname: x\n"
    r = _run(make_repo, "ci.yml", before, "run: |+\n  make\n\nname: x\n")
    assert not r.ok and "keep-chomped" in r.detail, (r.method, r.detail)


# ---------------------------------------------------------------------------
# Fix round 2 (review findings).
# ---------------------------------------------------------------------------

UNTERMINATED = "unterminated block comment in inserted lines"


# Item 1: SQL (PostgreSQL) and Rust nest /* */, so "/*" inside a comment opens another level.
@pytest.mark.parametrize(
    "rel,before,comment",
    [
        ("q.sql", "select 1;\nselect 2;\n", "/* Imports staging/*.csv */"),
        ("m.rs", "fn main() {}\n", "/* Reads src/*.rs at build time */"),
        ("m.rs", "fn main() {}\n", "/* a /* b */"),
    ],
    ids=["sql-glob", "rust-glob", "rust-unbalanced"],
)
def test_nested_block_glob_comment_fails(make_repo, rel: str, before: str, comment: str) -> None:
    r = _run(make_repo, rel, before, f"{comment}\n{before}")
    assert not r.ok and UNTERMINATED in r.detail, (r.method, r.detail)


@pytest.mark.parametrize("rel,before", [("q.sql", "select 1;\n"), ("m.rs", "fn main() {}\n")])
@pytest.mark.parametrize(
    "comment",
    ["/* a /* b */ c */", "/* a\n   /* b */\n   c */", "/*/* x */*/"],
    ids=["one-line", "multi-line", "tight"],
)
def test_properly_nested_block_comment_passes(
    make_repo, rel: str, before: str, comment: str
) -> None:
    r = _run(make_repo, rel, before, f"{comment}\n{before}")
    assert r.ok, (r.method, r.detail)


def test_nested_block_code_after_close_fails(make_repo) -> None:
    r = _run(make_repo, "m.rs", "fn main() {}\n", "/* a /* b */ c */ fn x() {}\nfn main() {}\n")
    assert not r.ok and "code after" in r.detail, (r.method, r.detail)


@pytest.mark.parametrize(
    "rel,before",
    [("s.css", "a { color: red; }\n"), ("A.java", "class A {}\n"), ("m.c", "int x;\n")],
)
def test_glob_comment_passes_in_non_nesting_languages(make_repo, rel: str, before: str) -> None:
    r = _run(make_repo, rel, before, f"/* Imports staging/*.csv */\n{before}")
    assert r.ok, (r.method, r.detail)


def test_nested_block_flag_is_set_for_sql_and_rust_only() -> None:
    from document_repo.languages import EXT, NAMES

    nesting = {lg.name for lg in (*EXT.values(), *NAMES.values()) if lg.nested_block}
    assert nesting == {"sql", "rust"}


# Item 2: verify --changed covers every changed or untracked file but docs and explorer output.
def _changed_repo(make_repo, marker):
    repo = make_repo(
        {
            "package.json": "{}\n",
            "a.rb": "x = 1\n",
            "README.md": "# r\n",
            "docs/x.md": "# x\n",
            "explorer/app.js": "x\n",
            **marker,
            "keep.py": "k = 1\n",
            "gone.py": "g = 1\n",
            ".gitignore": "ignored.py\nbuild/\n",
        }
    )
    (repo / "package.json").write_text('{"a": 1}\n')
    (repo / "a.rb").write_text("# c\nx = 1\n")
    (repo / "README.md").write_text("# r2\n")
    (repo / "docs/x.md").write_text("# x2\n")
    (repo / "explorer/app.js").write_text("y\n")
    (repo / "explorer/data/model.js").write_text("var m;\n")
    (repo / "gone.py").unlink()
    (repo / "conftest.py").write_text("import pytest\n")
    (repo / "ignored.py").write_text("i = 1\n")
    (repo / "build").mkdir()
    (repo / "build/out.js").write_text("o\n")
    (repo / "notes.txt").write_text("n\n")
    return repo


def test_changed_files_lists_every_changed_or_untracked_file(make_repo, marker) -> None:
    import document_repo.verify as verify_mod

    repo = _changed_repo(make_repo, marker)
    assert verify_mod.changed_files(repo, "HEAD") == [
        "a.rb",
        "conftest.py",
        "gone.py",
        "notes.txt",
        "package.json",
    ]


def test_changed_files_includes_both_sides_of_a_rename(make_repo, git) -> None:
    import document_repo.verify as verify_mod

    repo = make_repo({"old.py": "x = 1\n" * 20})
    git(repo, "mv", "old.py", "new.py")
    assert verify_mod.changed_files(repo, "HEAD") == ["new.py", "old.py"]


def test_doc_suffixes_constant() -> None:
    import document_repo.verify as verify_mod

    assert verify_mod.DOC_SUFFIXES == (".md",)


def test_cli_verify_changed_fails_unknown_and_untracked_files(make_repo, marker, capsys) -> None:
    repo = _changed_repo(make_repo, marker)
    capsys.readouterr()
    assert main(["verify", "--repo", str(repo), "--changed"]) == 1
    results = {r["path"]: r for r in json.loads(capsys.readouterr().out)}
    assert set(results) == {"a.rb", "conftest.py", "gone.py", "notes.txt", "package.json"}
    assert not any(r["ok"] for r in results.values())
    assert results["package.json"]["method"] == "none"
    assert results["a.rb"]["method"] == "none"
    assert "not in HEAD" in results["conftest.py"]["detail"]


# Item 3: Go example output. From "// Output:" to the function's "}" the comments are compared by
# `go test`; a line directly above "// Output:" joins its comment group and hides the prefix.
GO_EXAMPLE = (
    'package x\n\nimport "fmt"\n\nfunc ExampleAdd() {\n\tfmt.Println(1 + 2)\n'
    '\tfmt.Println("ok")\n\t// Output:\n\t// 3\n\t// ok\n}\n\nfunc helper() int {\n'
    "\treturn 1\n}\n"
)


def _go_insert(base: str, before_line: int, text: str = "\t// Note.") -> str:
    lines = base.splitlines(keepends=True)
    return "".join(lines[:before_line] + [text + "\n"] + lines[before_line:])


@pytest.mark.parametrize(
    "before_line",
    [7, 8, 9, 10],
    ids=["above-output-line", "after-output-line", "middle-of-run", "end-of-run"],
)
def test_go_example_output_run_is_verbatim(make_repo, before_line: int) -> None:
    r = _run(make_repo, "x_test.go", GO_EXAMPLE, _go_insert(GO_EXAMPLE, before_line))
    # Directly below "// Output:" the older below-a-directive guard fires first; both are right.
    assert not r.ok and ("example output" in r.detail or "below a directive" in r.detail), (
        r.method,
        r.detail,
    )


def test_go_unordered_output_run_is_verbatim(make_repo) -> None:
    base = GO_EXAMPLE.replace("// Output:", "// Unordered output:")
    r = _run(make_repo, "x_test.go", base, _go_insert(base, 9))
    assert not r.ok and "example output" in r.detail, (r.method, r.detail)


def test_go_block_comment_output_is_verbatim(make_repo) -> None:
    base = GO_EXAMPLE.replace("\t// Output:\n\t// 3\n\t// ok\n", "\t/* Output:\n\t3\n\tok\n\t*/\n")
    r = _run(make_repo, "x_test.go", base, _go_insert(base, 11))
    assert not r.ok and "example output" in r.detail, (r.method, r.detail)


@pytest.mark.parametrize(
    "before_line,text",
    [(5, "\t// Prints the sum."), (4, "// ExampleAdd shows Add."), (13, "\t// Why: constant.")],
    ids=["first-statement", "doc-comment", "other-function"],
)
def test_go_comment_elsewhere_in_example_passes(make_repo, before_line: int, text: str) -> None:
    r = _run(make_repo, "x_test.go", GO_EXAMPLE, _go_insert(GO_EXAMPLE, before_line, text))
    assert r.ok, (r.method, r.detail)


def test_go_blank_separated_comment_above_output_passes(make_repo) -> None:
    # A comment group separated from "// Output:" by a blank line is its own group, so go/doc
    # still sees "Output:" in the function's last comment group.
    base = GO_EXAMPLE.replace('\tfmt.Println("ok")\n', '\tfmt.Println("ok")\n\n')
    r = _run(make_repo, "x_test.go", base, _go_insert(base, 7, "\t// Two lines are printed."))
    assert r.ok, (r.method, r.detail)


# Item 5: a tab in YAML indentation is a parse error.
@pytest.mark.parametrize("line", ["\t# note", "  \t# note", "\t"])
def test_yaml_tab_indented_insert_fails(make_repo, line: str) -> None:
    r = _run(make_repo, "ci.yml", "a: 1\nb: 2\n", f"a: 1\n{line}\nb: 2\n")
    assert not r.ok and "tab" in r.detail, (r.method, r.detail)


# Item 7: prose that only looks like a directive.
def test_python_docstring_with_template_braces_passes(make_repo) -> None:
    after = 'def f():\n    """Render {{ name }} and {% raw %}."""\n    pass\n'
    r = _run(make_repo, "m.py", "def f():\n    pass\n", after)
    assert r.ok, (r.method, r.detail)


def test_python_transcoding_docstring_on_line_one_passes(make_repo) -> None:
    r = _run(make_repo, "m.py", "x = 1\n", '"""Transcoding: helpers."""\nx = 1\n')
    assert r.ok, (r.method, r.detail)


# ---------------------------------------------------------------------------
# Fix round 3 (convergence).
# ---------------------------------------------------------------------------

TS_MISSING = (
    "TypeScript compiler not available; JS/TS files cannot be verified "
    "(install with: npm install -g typescript@5.6.3)"
)


@pytest.fixture
def no_node(monkeypatch) -> None:
    """Make the machine look like it has no node, so ts-printer cannot run."""
    import document_repo.verify as verify_mod

    monkeypatch.setattr(verify_mod, "node_binary", lambda: None)


# D1: JS/TS are verified only by ts-printer. Without it they fail; there is no fallback.
@pytest.mark.parametrize("rel", ["a.ts", "a.tsx", "a.mts", "a.js", "a.jsx", "a.mjs", "a.cjs"])
def test_js_ts_without_ts_printer_fail(make_repo, no_node, rel: str) -> None:
    r = _run(make_repo, rel, "const a = 1;\n", "// Why: one.\nconst a = 1;\n")
    assert not r.ok and r.method == "none" and r.detail == TS_MISSING, (r.method, r.detail)


def test_ts_pure_comment_insertion_fails_without_ts_printer(make_repo, no_node) -> None:
    before = "export function f(): number {\n  return 1;\n}\n"
    after = "/** Returns one. */\nexport function f(): number {\n  return 1;\n}\n"
    r = _run(make_repo, "a.ts", before, after)
    assert not r.ok and r.detail == TS_MISSING, (r.method, r.detail)


# D2 (end to end): a multi-line ESLint config comment fails after a passing ts-printer.
def test_multiline_eslint_config_fails_after_ts_printer(make_repo, ts_ok) -> None:
    before = "const a = 1;\nconst b = 2;\n"
    after = "const a = 1;\n/* eslint\n   no-console: off */\nconst b = 2;\n"
    r = _run(make_repo, "a.js", before, after)
    assert not r.ok and DIRECTIVE in r.detail, (r.method, r.detail)


# D3: only markdown is left out of --changed; other text files are listed, so they fail.
def test_changed_files_lists_non_markdown_text_files(make_repo) -> None:
    repo = make_repo(
        {
            "requirements.txt": "requests==2.0\n",
            "CMakeLists.txt": "project(x)\n",
            "docs/page.mdx": "import X from './x'\n",
            "docs/index.rst": "Title\n",
            "README.md": "# r\n",
            "docs/GUIDE.MD": "# g\n",
        }
    )
    (repo / "requirements.txt").write_text("requests==2.0\nevil-pkg\n")
    (repo / "CMakeLists.txt").write_text("project(x)\nadd_compile_definitions(EVIL)\n")
    (repo / "docs/page.mdx").write_text("import X from './evil'\n")
    (repo / "docs/index.rst").write_text("Title\n.. include:: x\n")
    (repo / "README.md").write_text("# r2\n")
    (repo / "docs/GUIDE.MD").write_text("# g2\n")
    assert changed_files(repo, "HEAD") == [
        "CMakeLists.txt",
        "docs/index.rst",
        "docs/page.mdx",
        "requirements.txt",
    ]
    assert not any(verify_file(repo, f).ok for f in changed_files(repo, "HEAD"))


# D4: a change of file mode (executable bit, symlink) is a behaviour change.
needs_posix_modes = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows has no executable bit: os.chmod cannot set it, and git runs with filemode off",
)


@needs_posix_modes
def test_executable_bit_added_fails(make_repo) -> None:
    import os

    repo = make_repo({"run.sh": "echo a\n"})
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    os.chmod(repo / "run.sh", 0o755)
    r = verify_file(repo, "run.sh")
    assert not r.ok and "file mode changed" in r.detail, (r.method, r.detail)


@needs_posix_modes
def test_executable_bit_removed_fails(make_repo, git) -> None:
    import os

    repo = make_repo({"run.sh": "echo a\n"})
    os.chmod(repo / "run.sh", 0o755)
    git(repo, "add", "run.sh")
    git(repo, "commit", "-q", "-m", "exec")
    os.chmod(repo / "run.sh", 0o644)
    r = verify_file(repo, "run.sh")
    assert not r.ok and "file mode changed" in r.detail, (r.method, r.detail)


@needs_posix_modes
def test_unchanged_executable_bit_passes(make_repo, git) -> None:
    import os

    repo = make_repo({"run.sh": "echo a\n"})
    os.chmod(repo / "run.sh", 0o755)
    git(repo, "add", "run.sh")
    git(repo, "commit", "-q", "-m", "exec")
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    r = verify_file(repo, "run.sh")
    assert r.ok, (r.method, r.detail)


def test_executable_bit_ignored_when_git_ignores_it(make_repo, git) -> None:
    # core.fileMode=false (Windows, some mounts): git records no mode change, so none ships.
    import os

    repo = make_repo({"run.sh": "echo a\n"})
    git(repo, "config", "core.fileMode", "false")
    os.chmod(repo / "run.sh", 0o755)
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    r = verify_file(repo, "run.sh")
    assert r.ok, (r.method, r.detail)


# Fix round 4, item 1: git decides what is a mode change (core.fileMode, the index), not lstat.
@pytest.mark.parametrize(
    "stage",
    [("update-index", "--chmod=+x"), ("add", "--chmod=+x")],
    ids=["update-index", "add"],
)
def test_executable_bit_staged_with_filemode_false_fails(make_repo, git, stage) -> None:
    # core.fileMode=false hides the work-tree bit, but the index still records the mode, and a
    # commit would ship it. lstat sees a plain file; git sees 100644 -> 100755.
    repo = make_repo({"run.sh": "echo a\n"})
    git(repo, "config", "core.fileMode", "false")
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    git(repo, *stage, "run.sh")
    r = verify_file(repo, "run.sh")
    assert not r.ok and "file mode changed" in r.detail, (r.method, r.detail)


def test_executable_bit_chmod_with_filemode_false_passes(make_repo, git) -> None:
    # A plain chmod with core.fileMode=false and nothing staged: git records no change.
    import os

    repo = make_repo({"run.sh": "echo a\n"})
    git(repo, "config", "core.fileMode", "false")
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    os.chmod(repo / "run.sh", 0o755)
    assert git(repo, "diff", "HEAD", "--raw", "--", "run.sh").count("100755") == 0
    r = verify_file(repo, "run.sh")
    assert r.ok, (r.method, r.detail)


def test_executable_bit_staged_only_fails_by_default(make_repo, git) -> None:
    # Default config: the work tree still looks plain (lstat and "git diff HEAD" agree with the
    # base), but the index carries the executable bit.
    import os

    repo = make_repo({"run.sh": "echo a\n"})
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    git(repo, "add", "--chmod=+x", "run.sh")
    os.chmod(repo / "run.sh", 0o644)  # the work tree is a plain file again
    assert git(repo, "diff", "HEAD", "--raw", "--", "run.sh").split()[:2] == [":100644", "100644"]
    r = verify_file(repo, "run.sh")
    assert not r.ok and "file mode changed" in r.detail, (r.method, r.detail)


@needs_posix_modes
def test_executable_bit_dropped_in_index_only_fails(make_repo, git) -> None:
    import os

    repo = make_repo({"run.sh": "echo a\n"})
    os.chmod(repo / "run.sh", 0o755)
    git(repo, "add", "run.sh")
    git(repo, "commit", "-q", "-m", "exec")
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    git(repo, "update-index", "--chmod=-x", "run.sh")
    assert os.stat(repo / "run.sh").st_mode & 0o100  # the work tree still has the bit
    r = verify_file(repo, "run.sh")
    assert not r.ok and "file mode changed" in r.detail, (r.method, r.detail)


def test_file_removed_from_index_fails(make_repo, git) -> None:
    # "git rm --cached" leaves the work-tree file and drops it from the next commit.
    repo = make_repo({"run.sh": "echo a\n"})
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    git(repo, "rm", "-q", "--cached", "run.sh")
    r = verify_file(repo, "run.sh")
    assert not r.ok and "file mode changed" in r.detail, (r.method, r.detail)


def test_mode_check_treats_the_path_literally(make_repo, git) -> None:
    # "a[1].sh" is a glob that also matches a1.sh; only a1.sh changed mode.
    import os

    repo = make_repo({"a[1].sh": "echo a\n", "a1.sh": "echo a\n"})
    os.chmod(repo / "a1.sh", 0o755)
    (repo / "a[1].sh").write_text("# Say a.\necho a\n")
    r = verify_file(repo, "a[1].sh")
    assert r.ok, (r.method, r.detail)


def test_mode_check_fails_closed_when_git_diff_fails(make_repo, monkeypatch) -> None:
    import subprocess

    from document_repo import verify as verify_mod

    repo = make_repo({"run.sh": "echo a\n"})
    (repo / "run.sh").write_text("# Say a.\necho a\n")
    real = subprocess.run

    def broken_diff(cmd, *args, **kwargs):
        if "diff" in cmd:
            return subprocess.CompletedProcess(cmd, 128, b"", b"fatal: boom")
        return real(cmd, *args, **kwargs)

    monkeypatch.setattr(verify_mod.subprocess, "run", broken_diff)
    r = verify_file(repo, "run.sh")
    assert not r.ok and "git diff failed" in r.detail, (r.method, r.detail)


def _symlink_or_skip(target: str, link) -> None:
    import os

    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError, AttributeError) as exc:
        pytest.skip(f"symlinks not supported here: {exc}")


def test_file_replaced_by_symlink_fails(make_repo) -> None:
    repo = make_repo({"a.py": "x = 1\n", "link.py": "x = 1\n"})
    (repo / "link.py").unlink()
    _symlink_or_skip("a.py", repo / "link.py")
    r = verify_file(repo, "link.py")
    assert not r.ok and "symlink" in r.detail, (r.method, r.detail)


def test_symlink_in_base_fails(make_repo, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    _symlink_or_skip("a.py", repo / "link.py")
    git(repo, "add", "link.py")
    git(repo, "commit", "-q", "-m", "link")
    r = verify_file(repo, "link.py")
    assert not r.ok and "symlink" in r.detail, (r.method, r.detail)


# D5: --repo may be any directory in the work tree; paths are relative to its top level.
def test_changed_files_from_a_subdirectory_lists_the_whole_repo(make_repo) -> None:
    repo = make_repo({"sub/s.py": "q = 1\n", "a.py": "x = 1\n"})
    (repo / "a.py").write_text("# c\nx = 1\n")
    (repo / "newdir").mkdir()
    (repo / "newdir/n.py").write_text("n = 1\n")
    assert changed_files(repo / "sub", "HEAD") == ["a.py", "newdir/n.py"]


def test_verify_file_from_a_subdirectory_uses_toplevel_paths(make_repo) -> None:
    repo = make_repo({"sub/s.py": "q = 1\n", "a.py": "x = 1\n"})
    (repo / "a.py").write_text("# c\nx = 1\n")
    r = verify_file(repo / "sub", "a.py")
    assert r.ok and r.method == "python-ast", (r.method, r.detail)


def test_cli_verify_changed_from_a_subdirectory(make_repo, capsys) -> None:
    repo = make_repo({"sub/s.py": "q = 1\n", "a.py": "x = 1\n"})
    (repo / "a.py").write_text("# c\nx = 1\n")
    (repo / "newdir").mkdir()
    (repo / "newdir/n.py").write_text("n = 1\n")
    capsys.readouterr()
    assert main(["verify", "--repo", str(repo / "sub"), "--changed"]) == 1
    results = {r["path"]: r["ok"] for r in json.loads(capsys.readouterr().out)}
    assert results == {"a.py": True, "newdir/n.py": False}


def test_verify_file_outside_a_git_work_tree_fails(tmp_path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    r = verify_file(tmp_path, "a.py")
    assert not r.ok and r.method == "none" and "git work tree" in r.detail, (r.method, r.detail)


def test_cli_verify_changed_outside_a_git_work_tree_is_bad_input(tmp_path) -> None:
    assert main(["verify", "--repo", str(tmp_path), "--changed"]) == 2


# D6 (end to end): a Go block comment starting with "Output:" turns on an example's output check.
GO_NO_OUTPUT = 'package x\n\nimport "fmt"\n\nfunc ExampleHi() {\n\tfmt.Println("hi")\n}\n'


@pytest.mark.parametrize(
    "chunk", ["\t/* Output: hi */", "\t/*\n\tOutput: hi\n\t*/"], ids=["one-line", "multi-line"]
)
def test_go_new_block_output_comment_fails(make_repo, chunk: str) -> None:
    after = GO_NO_OUTPUT.replace('("hi")\n', '("hi")\n' + chunk + "\n")
    r = _run(make_repo, "x_test.go", GO_NO_OUTPUT, after)
    assert not r.ok and DIRECTIVE in r.detail, (r.method, r.detail)


# --- the exempt set: the explorer files a build writes, only in an explorer a build made ---------


def _put(root: Path, files: dict) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


@pytest.mark.parametrize(
    "path,exempt",
    [
        ("explorer/index.html", True),
        ("explorer/app.js", True),
        ("explorer/styles.css", True),
        ("explorer/vendor/mermaid.min.js", True),
        ("explorer/data/model.json", True),
        ("explorer/data/model.js", True),
        ("explorer/data/state.json", True),
        ("explorer/data/run-report.md", True),
        ("explorer/data/loader.js", False),
        ("explorer/data/x.js", False),
        ("explorer/data/sub/model.json", False),
        ("explorer/app.py", False),
        ("explorer/server/main.go", False),
        ("explorer/vendor/other.js", False),
        ("explorer/data", False),
        ("src/explorer/app.js", False),
        ("explorer", False),
        ("NOTES.md", True),
    ],
)
def test_is_exempt_in_an_explorer_a_build_made(
    tmp_path: Path, marker, path: str, exempt: bool
) -> None:
    from document_repo.verify import is_exempt

    _put(tmp_path, marker)
    assert is_exempt(path, tmp_path) is exempt


FOREIGN_MARKERS = {
    "no-state": {"explorer/data/model.json": "{}\n"},
    "ui-state": {"explorer/data/state.json": '{"saved": "ui state"}\n'},
    "extra-key": "extra",
    "missing-key": "missing",
    "hash-mismatch": "mismatch",
    "not-json": {"explorer/data/state.json": "not json\n", "explorer/data/model.json": "{}\n"},
    "a-list": {"explorer/data/state.json": "[]\n", "explorer/data/model.json": "{}\n"},
    "no-model": "no-model",
}


def _foreign_marker(kind: str, marker: dict) -> dict:
    spec = FOREIGN_MARKERS[kind]
    if isinstance(spec, dict):
        return spec
    state = json.loads(marker["explorer/data/state.json"])
    files = dict(marker)
    if spec == "extra":
        state["saved"] = "ui"
    elif spec == "missing":
        del state["generated_at"]
    elif spec == "mismatch":
        files["explorer/data/model.json"] = b'{"other": 1}\n'
    elif spec == "no-model":
        del files["explorer/data/model.json"]
    files["explorer/data/state.json"] = json.dumps(state) + "\n"
    return files


@pytest.mark.parametrize("kind", sorted(FOREIGN_MARKERS))
@pytest.mark.parametrize(
    "path",
    [
        "explorer/app.js",
        "explorer/index.html",
        "explorer/data/model.json",
        "explorer/data/state.json",
    ],
)
def test_nothing_under_explorer_is_exempt_without_a_trusted_state(
    tmp_path: Path, marker, kind: str, path: str
) -> None:
    from document_repo.verify import is_exempt

    _put(tmp_path, _foreign_marker(kind, marker))
    assert not is_exempt(path, tmp_path)
    assert is_exempt("explorer/data/run-report.md", tmp_path)  # Markdown, wherever it is


def test_a_symlinked_state_is_not_trusted(tmp_path: Path, marker) -> None:
    from document_repo.build import is_our_explorer
    from document_repo.verify import is_exempt

    _put(tmp_path, marker)
    real = tmp_path / "elsewhere.json"
    state = tmp_path / "explorer/data/state.json"
    real.write_bytes(state.read_bytes())
    state.unlink()
    state.symlink_to(real)
    assert not is_our_explorer(tmp_path / "explorer")
    assert not is_exempt("explorer/app.js", tmp_path)


def test_a_symlinked_data_directory_is_not_trusted(tmp_path: Path, marker) -> None:
    from document_repo.build import is_our_explorer

    _put(tmp_path / "real", marker)
    (tmp_path / "explorer").mkdir()
    (tmp_path / "explorer/data").symlink_to(tmp_path / "real/explorer/data")
    assert not is_our_explorer(tmp_path / "explorer")


def test_the_exempt_set_is_read_from_the_template_directory(tmp_path: Path, marker) -> None:
    from document_repo.build import TEMPLATE_DIR, template_files
    from document_repo.verify import is_exempt

    installed = template_files(TEMPLATE_DIR)
    on_disk = {
        p.relative_to(TEMPLATE_DIR).as_posix()
        for p in TEMPLATE_DIR.rglob("*")
        if p.is_file() and p.relative_to(TEMPLATE_DIR).parts[0] != "data"
    }
    assert installed == on_disk and "app.js" in installed
    _put(tmp_path, marker)
    assert all(is_exempt("explorer/" + rel, tmp_path) for rel in installed)


def test_a_target_file_under_explorer_is_verified(make_repo, marker) -> None:
    repo = make_repo({"explorer/app.py": "x = 1\n", "explorer/app.js": "var a;\n"})
    (repo / "explorer/app.py").write_text("x = 2\n")
    (repo / "explorer/app.js").write_text("var b;\n")
    # No trusted state.json: the target's own app.js is judged despite its name.
    assert changed_files(repo, "HEAD") == ["explorer/app.js", "explorer/app.py"]
    _put(repo, marker)
    assert changed_files(repo, "HEAD") == ["explorer/app.py"]
    r = verify_file(repo, "explorer/app.py")
    assert not r.ok and "syntax tree changed" in r.detail, r.detail


def test_target_code_under_explorer_data_is_verified(make_repo, marker) -> None:
    # r2/p3: the target's own explorer/data/loader.js, with or without a trusted state.
    repo = make_repo({"explorer/data/loader.js": "export const f = () => 1;\n"})
    (repo / "explorer/data/loader.js").write_text("export const f = () => 2;\n")
    assert changed_files(repo, "HEAD") == ["explorer/data/loader.js"]
    _put(repo, marker)
    assert "explorer/data/loader.js" in changed_files(repo, "HEAD")


def test_a_stray_under_explorer_data_is_verified(make_repo, marker) -> None:
    # r2/p4: a new file next to the data a build writes is judged, and fails as not in base.
    repo = make_repo(dict(marker))
    (repo / "explorer/data/x.js").write_text("x\n")
    assert changed_files(repo, "HEAD") == ["explorer/data/x.js"]
    assert not verify_file(repo, "explorer/data/x.js").ok


def test_without_the_template_only_the_data_files_are_exempt(monkeypatch, tmp_path, marker) -> None:
    from document_repo import build
    from document_repo import verify as verify_mod

    monkeypatch.setattr(build, "TEMPLATE_DIR", tmp_path / "missing")
    verify_mod._skill_output.cache_clear()
    try:
        _put(tmp_path, marker)
        assert not verify_mod.is_exempt("explorer/app.js", tmp_path)
        assert verify_mod.is_exempt("explorer/data/model.json", tmp_path)
    finally:
        verify_mod._skill_output.cache_clear()


def test_a_crlf_checkout_keeps_the_explorer_exempt(make_repo, git, tmp_path) -> None:
    # r3/e2e/crlf: Git for Windows checks text out with CRLF (core.autocrlf=true).
    import json as _json

    from document_repo.build import TEMPLATE_DIR, install_template, write_explorer_data

    repo = make_repo({"main.py": "x = 1\n"})
    install_template(TEMPLATE_DIR, repo / "explorer")
    fixture = Path(__file__).parent / "fixtures" / "sample_model.json"
    write_explorer_data(_json.loads(fixture.read_text()), repo / "explorer" / "data")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "explorer")
    git(repo, "config", "core.autocrlf", "true")
    import shutil as _shutil

    _shutil.rmtree(repo / "explorer")
    git(repo, "checkout", "HEAD", "--", "explorer")
    assert b"\r\n" in (repo / "explorer/data/model.json").read_bytes()
    assert git(repo, "status", "--porcelain") == ""
    (repo / "explorer/app.js").write_bytes((repo / "explorer/app.js").read_bytes() + b"\r\n")
    assert changed_files(repo, "HEAD") == []


# --- verify_blobs: both sides read from commits (SE-H1) ----------------------------------------


def _two_commits(make_repo, commit_files, rel: str, before: str, after: str):
    repo = make_repo({rel: before})
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    head = commit_files(repo, {rel: after}, "edit")
    return repo, base, head


def test_verify_blobs_passes_a_committed_comment(make_repo, commit_files) -> None:
    repo, base, head = _two_commits(make_repo, commit_files, "m.py", BASE_PY, "# c\n" + BASE_PY)
    (repo / "m.py").write_text("x = 'the work tree is not read'\n")
    r = verify_blobs(repo, base, head, "m.py")
    assert r.ok and r.method == "python-ast", r.detail


def test_verify_blobs_fails_a_committed_code_change(make_repo, commit_files) -> None:
    after = BASE_PY.replace("a + b", "a - b")
    repo, base, head = _two_commits(make_repo, commit_files, "m.py", BASE_PY, after)
    (repo / "m.py").write_text("# c\n" + BASE_PY)  # a comment-only work tree changes nothing
    assert not verify_blobs(repo, base, head, "m.py").ok


def test_verify_blobs_runs_the_guards(make_repo, commit_files) -> None:
    before, after = "cat <<EOF\nhi\nEOF\n", "cat <<EOF\n# c\nhi\nEOF\n"
    repo, base, head = _two_commits(make_repo, commit_files, "a.sh", before, after)
    r = verify_blobs(repo, base, head, "a.sh")
    assert not r.ok and r.method == "comment-lines", r.detail


def test_verify_blobs_fails_closed_on_missing_sides_and_bad_input(
    make_repo, commit_files, tmp_path
) -> None:
    repo, base, head = _two_commits(make_repo, commit_files, "m.py", BASE_PY, BASE_PY + "# c\n")
    assert "not in" in verify_blobs(repo, base, head, "new.py").detail
    commit_files(repo, {"new.py": "x = 1\n"}, "add")
    assert f"not in {base}" in verify_blobs(repo, base, "HEAD", "new.py").detail
    git_rm = ["git", "-C", str(repo), "rm", "-q", "m.py"]
    subprocess.run(git_rm, check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "rm"], check=True)
    assert "not in HEAD" in verify_blobs(repo, base, "HEAD", "m.py").detail
    assert not verify_blobs(repo, base, head, "d.json").ok
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    assert "not inside a git work tree" in verify_blobs(outside, base, head, "m.py").detail


def test_verify_blobs_fails_a_committed_mode_change(make_repo, commit_files) -> None:
    repo, base, _ = _two_commits(make_repo, commit_files, "a.sh", "echo a\n", "echo a\n# c\n")
    (repo / "a.sh").chmod(0o755)
    subprocess.run(["git", "-C", str(repo), "add", "--chmod=+x", "a.sh"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "x"], check=True)
    r = verify_blobs(repo, base, "HEAD", "a.sh")
    assert not r.ok and "100644 -> 100755" in r.detail, r.detail


def test_verify_blobs_fails_a_committed_symlink(make_repo, commit_files) -> None:
    repo, base, _ = _two_commits(make_repo, commit_files, "a.sh", "echo a\n", "echo a\n# c\n")
    blob = (
        subprocess.run(
            ["git", "-C", str(repo), "hash-object", "-w", "--stdin"],
            input=b"a.sh.real",
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .strip()
    )
    subprocess.run(
        ["git", "-C", str(repo), "update-index", "--cacheinfo", f"120000,{blob},a.sh"], check=True
    )
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "link"], check=True)
    r = verify_blobs(repo, base, "HEAD", "a.sh")
    assert not r.ok and "symlink" in r.detail, r.detail
