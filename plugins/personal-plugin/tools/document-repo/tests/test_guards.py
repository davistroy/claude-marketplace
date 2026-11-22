"""Unit tests for guards.py: the public API and each context scanner's edge cases."""

import re

import pytest

from document_repo.guards import (
    DIRECTIVE_PATTERNS,
    common_guards,
    context_guard,
    inserted_lines,
    unsafe_insert_points,
)
from document_repo.languages import detect


def lang(name: str):
    path = {"dockerfile": "Dockerfile", "make": "Makefile"}.get(name, f"x.{name}")
    result = detect(path)
    assert result is not None
    return result


def unsafe(text: str, path: str) -> set[int]:
    lg = detect(path)
    assert lg is not None
    return unsafe_insert_points(text.splitlines(), lg)


def test_directive_patterns_are_compiled() -> None:
    assert DIRECTIVE_PATTERNS and all(isinstance(p, re.Pattern) for p in DIRECTIVE_PATTERNS)


def test_inserted_lines_reports_inserts_and_replace_b_side() -> None:
    before = "a\nb\nc\n"
    after = "# x\na\nB\nc\n# y\n"
    assert inserted_lines(before, after) == [(0, 1, ["# x"]), (1, 3, ["B"]), (3, 5, ["# y"])]


def test_common_guards_clean_and_dirty() -> None:
    sh = lang("sh")
    assert common_guards("a.sh", "echo a\n", "# why\necho a\n", sh) is None
    assert "directive" in (common_guards("a.sh", "echo a\n", "#!/bin/sh\necho a\n", sh) or "")


def test_cookie_beyond_line_two_is_plain_text() -> None:
    py = lang("py")
    assert common_guards("m.py", "a = 1\nb = 2\n", "a = 1\nb = 2\n# coding: x\n", py) is None


def test_docker_directives_stop_at_first_other_line() -> None:
    d = lang("dockerfile")
    before = "# syntax=a\nFROM x\n# escape=`\n"
    # Position 1 (after the directive run) is fine; the later "# escape=" is just a comment.
    assert common_guards("Dockerfile", before, "# syntax=a\n# c\nFROM x\n# escape=`\n", d) is None


def test_continuation_points() -> None:
    assert unsafe("a \\\nb\nc\n", "a.c") == {1}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("echo $'a\\'\nb'\n", {1}),  # ANSI-C quote with escaped quote spans the line
        ('echo "$(echo "x")"\nok\n', set()),  # nested quotes in $( ) inside "..."
        ("echo ${x:-'a\nb'}\n", {1}),  # quote inside ${ }
        ("x=$(\n  cmd\n)\n", {1, 2}),  # multi-line $( ) fails closed
        ("echo `a\nb`\n", {1}),  # backticks
        ('echo "`a\nb`"\n', {1}),  # backticks inside double quotes
        ('echo "${a\n}"\n', {1}),  # ${ } inside double quotes
        ('echo "a$(b\nc)"\n', {1}),  # $( ) inside double quotes
        ("echo ${a:-${b\n}}\n", {1}),  # nested ${ }
        ("echo ${a:-$(b\n)}\n", {1}),  # $( ) inside ${ }
        ('echo ${a:-"b\n"}\n', {1}),  # double quote inside ${ }
        ("echo a\\'b\nok\n", set()),  # escaped quote in code
        ("cat <<A <<B\na\nA\nb\nB\nok\n", {1, 2, 3, 4}),  # two heredocs on one line
        ('cat <<"E O"\nx\nE O\n', {1, 2}),  # double-quoted delimiter
        ("cat <<<'here'\nok\n", set()),  # here-string is not a heredoc
        ("echo $# ${#a} x#y\nok\n", set()),  # '#' that is not a comment
    ],
)
def test_shell_scanner(text: str, expected: set[int]) -> None:
    assert unsafe(text, "a.sh") == expected


def test_make_scanner() -> None:
    text = "define A\ndefine B\nx\nendef\ny\nendef\nall:\n\tcat <<E\n\tz\nE\nok:\n"
    assert unsafe(text, "Makefile") == {1, 2, 3, 4, 5, 8, 9}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("k: 'it''s\n  x'\n", {1}),  # single-quoted with '' escape spans lines
        ('k: "a\\"\n  b"\n', {1}),  # escaped double quote does not close
        ("k: 'done'\nj: 1\n", set()),
        ("- - a\n  - b\n", set()),  # nested dash items, sibling not continuation
        ("k: &a !t |\n  x\nj: 1\n", {1, 2}),  # props before block indicator
        ("--- |\n  x\n", {1, 2}),  # document-level block scalar
        ("k: [a,\n  b]\nj: 1\n", {1}),  # multi-line flow collection fails closed
        ("k: a\n  # c\n  b\n", set()),  # comment ends the plain scalar
        ("k: 'open\n", {1}),  # unterminated quote at EOF fails closed
    ],
)
def test_yaml_scanner(text: str, expected: set[int]) -> None:
    assert unsafe(text, "c.yml") == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("/* a /* b */\nc */\nok;\n", {1}),  # postgres nests block comments
        # Dialects disagree on backslash escapes; the union of readings fails closed.
        ("select 'a\\'\nb';\n", {1, 2}),
        ("select `a\nb`;\n", {1}),  # MySQL backtick identifier
        ('select "a\nb";\n', {1}),  # quoted identifier / MySQL string
        # '#' is a comment only in MySQL; in Postgres the quote opens a string.
        ("# it's mysql\nselect 1;\n", {1, 2}),
        ("select a$b$c;\nok\n", set()),  # '$' inside an identifier is not a dollar quote
        ("select 1 --x'\n;\n", {1, 2}),  # MySQL: "--x" is not a comment, so the quote opens
        ("-- it's\nselect 1;\n", set()),
    ],
)
def test_sql_scanner(text: str, expected: set[int]) -> None:
    assert unsafe(text, "q.sql") == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ('k = """a\\"""\nb"""\n', {1}),  # escaped quote inside basic multi-line
        ('k = """a""""\nj = 1\n', set()),  # closing run of up to five quotes
        ('k = "a#b" # c\nj = "x\\"y"\n', set()),
        ('k = "open\nj = 1\n', {1, 2}),  # unterminated basic string fails closed
    ],
)
def test_toml_scanner(text: str, expected: set[int]) -> None:
    assert unsafe(text, "c.toml") == expected


@pytest.mark.parametrize(
    "path,text,expected",
    [
        ("a.rs", "/* a /* b */\nc */\nok\n", {1}),  # Rust nests block comments
        ("a.rs", 'let s = br"a\nb";\n', {1}),
        ("a.rs", "let c = '\\'';\nlet s = r\"a\nb\";\n", {2}),  # escaped char literal
        ("a.cs", 'var s = $@"a\nb";\n', {1}),
        ("a.cs", 'var s = @$"a""\nb";\n', {1}),  # doubled quote does not close verbatim
        ("a.cs", 'var s = $"""\na\n""";\n', {1, 2}),  # interpolated raw
        ("a.cs", 'var s = $"x{y}";\nok\n', set()),
        ("a.c", 'char *s = "a\\\nb";\n', {1}),  # continued string keeps state
        ("a.c", "char c = '\\n';\nint x;\n", set()),
        ("a.go", "var r = '`'\nvar s = \"`\"\nok\n", set()),  # backtick in rune and string
        ("a.css", 'a::after { content: "/*"; }\nb {}\n', set()),
        ("a.ts", "const s = `a${'}'}b`;\nok;\n", set()),  # brace inside string in ${ }
        ("a.ts", "const s = `${ {a: 1}.a }`;\nok;\n", set()),  # object literal in ${ }
        ("a.ts", "const s = `\\`\n`;\n", {1}),  # escaped backtick
        ("a.js", "function f() {\n  return <div/>;\n}\n", {2, 3}),  # JSX after return
        ("a.js", "if (a <b) {}\nok\n", set()),  # comparison is not JSX
    ],
)
def test_clike_scanner(path: str, text: str, expected: set[int]) -> None:
    assert unsafe(text, path) == expected


def test_go_cgo_preamble_and_grouped_import() -> None:
    text = 'package m\n\n/*\n#include <a.h>\n*/\nimport "C"\n'
    assert unsafe(text, "m.go") >= {2, 3, 4, 5}
    assert 3 in unsafe('package m\nimport (\n\t// x\n\t"C"\n)\n', "m.go")


@pytest.mark.parametrize(
    "text,expected",
    [
        ('<a title="x>\ny">\nok\n', {1}),  # quoted '>' in an attribute stays in the tag
        ("<div\n  class=a>\nok\n", {1}),  # multi-line open tag
        ("<!DOCTYPE html\n>\nok\n", {1}),
        ("</textarea>\nok\n", set()),  # a closing tag does not open raw text
        ("<script>a\n</script >\nok\n", {1}),
    ],
)
def test_html_scanner(text: str, expected: set[int]) -> None:
    assert unsafe(text, "i.html") == expected


def test_context_guard_reports_position() -> None:
    sh = lang("sh")
    why = context_guard("cat <<E\nx\nE\n", "cat <<E\n# c\nx\nE\n", sh)
    assert why and "verbatim" in why and "base line 1" in why
    assert context_guard("echo\n", "# c\necho\n", sh) is None


def test_line_ending_guard_edge_cases() -> None:
    sql = lang("sql")
    # An equal line whose terminator changed from LF to CR-only.
    assert "line endings changed" in (common_guards("q.sql", "a;\nb;\n", "a;\rb;\n", sql) or "")
    # A file with no terminator at all: an appended LF line is fine.
    assert common_guards("q.sql", "a;", "a;\n-- c\n", sql) is None
