"""Unit tests for guards.py: the public API and each context scanner's edge cases."""

import re

import pytest

import document_repo.guards as guards_mod
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
        ("k: &a !t |\n  x\nj: 1\n", {1}),  # props before block indicator
        ("--- |\n  x\n", {1}),  # document-level block scalar
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


# ---------------------------------------------------------------------------
# Fix round 1, item 1: directive patterns are scoped to the languages whose tools read them.
# ---------------------------------------------------------------------------

DIRECTIVE = "inserted directive-like comment"

#: One home-language sample per scoped pattern: the directive must still fail where it is read.
SCOPED_HOME = [
    # JS/TS tools
    ("a.ts", "// @ts-ignore"),
    ("a.js", "// eslint-disable-next-line"),
    ("a.js", '/* eslint eqeqeq: "off" */'),
    ("a.js", "/* global $ */"),
    ("a.js", "/* globals jQuery */"),
    ("a.js", "/* jshint esversion: 6 */"),
    ("a.js", "/* istanbul ignore next */"),
    ("a.ts", "/* v8 ignore next */"),
    ("a.ts", "// deno-lint-ignore no-explicit-any"),
    ("a.ts", "// deno-fmt-ignore"),
    ("a.jsx", "/** @jsx h */"),
    ("a.js", "// @flow"),
    ("a.ts", '/// <reference path="x" />'),
    ("a.js", '/// <reference lib="dom" />'),
    ("a.js", "/*#__PURE__*/"),
    ("a.ts", "/* #__NO_SIDE_EFFECTS__ */"),
    ("a.js", '/* webpackChunkName: "x" */'),
    ("a.js", "/* @vite-ignore */"),
    ("a.js", "/** @jest-environment jsdom */"),
    ("a.js", "/*@cc_on @*/"),
    ("a.js", "//# sourceMappingURL=a.js.map"),
    ("s.css", "/*# sourceMappingURL=a.css.map */"),
    # Go tools
    ("m.go", "//go:build ignore"),
    ("m.go", "// +build ignore"),
    ("m.go", "// +kubebuilder:object:generate=true"),
    ("m.go", "//line other.go:10"),
    ("m.go", "//export Foo"),
    ("m.go", "// Output: 3"),
    ("m.go", "// Unordered output: a"),
    # Python tools
    ("m.py", "# type: ignore"),
    ("m.py", "# pylint: disable=all"),
    ("m.py", "# fmt: off"),
    ("m.py", "# pyre-ignore"),
    # coverage.py in Python; detect-secrets reads the same marker in any '#' file
    ("m.py", "# pragma: no cover"),
    ("ci.yml", "# pragma: allowlist secret"),
    ("a.sh", "# pragma: allowlist secret"),
    ("c.toml", "# pragma: allowlist secret"),
    ("Dockerfile", "# pragma: allowlist secret"),
    ("Makefile", "# pragma: allowlist secret"),
    # CSS tools
    ("s.css", "/* stylelint-disable */"),
    ("s.scss", "/* purgecss ignore */"),
    ("s.css", "/* autoprefixer: off */"),
    ("s.css", "/*rtl:ignore*/"),
    # Java reads unicode escapes before lexing
    ("A.java", "// done \\u000a"),
    # Dockerfile parser directives
    ("Dockerfile", "# syntax=docker/dockerfile:1"),
]

#: Ordinary prose that only looks like a directive in a language that does not read it. Each of
#: these failed before the scoping (a false failure) and must pass now.
SCOPED_ELSEWHERE = [
    ("A.cs", "/// <summary>"),
    ("A.cs", "/// </summary>"),
    ("A.cs", '/// <param name="a">Left operand.</param>'),
    ("A.cs", "/// <returns>The sum.</returns>"),
    ("A.cs", '/// <see cref="Calc.Add"/>'),
    ("A.cs", "/// <inheritdoc/>"),
    ("a.rs", "/// <T> is the element type."),
    ("m.cpp", "/// <b>Bold</b> doc."),
    ("m.h", "/// <br> a line break"),
    ("m.c", "/* global counter, reset per run */"),
    ("A.java", "/* globals are avoided here */"),
    ("A.java", "// +1 because the index starts at zero"),
    ("a.rs", "// +5 for padding"),
    ("A.cs", "// Output: a sorted list"),
    ("m.c", "// Output: the checksum"),
    ("A.java", "//export list"),
    ("A.cs", "// go: the next step"),
    ("m.cpp", "// see #pragma pack for the layout"),
    ("m.c", "// uses #pragma once"),
    ("values.yaml", "# type: string"),
    ("a.sh", "# type: file or dir"),
    ("c.toml", "# type: integer"),
    ("ci.yml", "# fmt: json output"),
    ("ci.yml", "# Run eslint on changed files"),
    ("Makefile", "# eslint target"),
    ("a.sh", "# run eslint-disable audits weekly"),
    ("Dockerfile", "# needed for autoprefixer"),
    ("A.java", "// rtl: right-to-left text"),
    ("a.rs", "// stylelint is not used here"),
    ("Makefile", "# check=1 enables the strict mode"),
    ("ci.yml", "# syntax = yaml 1.2"),
    ("m.c", "// decodes \\u00e9 as e-acute"),
    ("a.js", "// matches \\u00e9 and friends"),
    ("m.py", "# matches \\u00e9 and friends"),
    ("a.rs", "// a \\u00e9 literal"),
    ("A.cs", "// the @jsx pragma is JavaScript only"),
    ("m.go", "// see the @ts-ignore docs"),
    ("m.py", "# eslint is run by the web team"),
    ("a.html", "<!-- eslint is not run on this page -->"),
    ("q.sql", "-- istanbul ignore is a JS thing"),
    ("a.sh", "# sourceMappingURL= is read by browsers"),
    ("a.sh", "# webpackChunkName: only in JS"),
]


@pytest.mark.parametrize("rel,line", SCOPED_HOME)
def test_scoped_directive_still_fails_where_it_is_read(rel: str, line: str) -> None:
    why = common_guards(rel, "x\n", f"{line}\nx\n", lang_for(rel))
    assert why is not None and DIRECTIVE in why, why


@pytest.mark.parametrize("rel,line", SCOPED_ELSEWHERE)
def test_scoped_directive_is_plain_prose_elsewhere(rel: str, line: str) -> None:
    assert common_guards(rel, "x\n", f"{line}\nx\n", lang_for(rel)) is None


def lang_for(rel: str):
    result = detect(rel)
    assert result is not None
    return result


def test_every_scoped_pattern_has_a_home_case() -> None:
    """A pattern scoped to some languages must be exercised in one of them."""
    for pattern, scope in guards_mod.DIRECTIVE_SCOPES:
        if scope is None:
            continue
        homes = [
            line
            for rel, line in SCOPED_HOME
            if lang_for(rel).name in scope and pattern.search(line)
        ]
        assert homes, f"no home-language case for {pattern.pattern!r} scoped to {sorted(scope)}"


def test_scope_names_are_real_languages() -> None:
    from document_repo.languages import EXT, NAMES

    known = {lg.name for lg in (*EXT.values(), *NAMES.values())}
    for pattern, scope in guards_mod.DIRECTIVE_SCOPES:
        assert scope is None or (scope and scope <= known), (pattern.pattern, scope)


def test_directive_patterns_is_every_scoped_pattern() -> None:
    assert DIRECTIVE_PATTERNS == tuple(p for p, _ in guards_mod.DIRECTIVE_SCOPES)


@pytest.mark.parametrize(
    "rel",
    ["m.py", "a.ts", "a.js", "q.sql", "a.sh", "ci.yml", "c.toml", "Dockerfile", "Makefile"]
    + ["s.css", "i.html", "m.go", "a.rs", "A.java", "m.c", "a.cpp", "A.cs"],
)
@pytest.mark.parametrize(
    "line", ["noqa", "prettier-ignore", "biome-ignore lint: x", "{{ x }}", "@generated", "nolint"]
)
def test_cross_language_directives_apply_to_every_language(rel: str, line: str) -> None:
    why = common_guards(rel, "x\n", f"{line}\nx\n", lang_for(rel))
    assert why is not None and DIRECTIVE in why


# ---------------------------------------------------------------------------
# Fix round 1, item 2: the position right after a YAML block scalar.
# ---------------------------------------------------------------------------

GHA = "jobs:\n  b:\n    steps:\n      - run: |\n          make\n          test\n      - name: x\n"


def test_yaml_block_tail_is_not_in_the_interior_set() -> None:
    # Interior positions 4 and 5 stay unsafe; position 6 (directly above "- name:") is decided in
    # context_guard, where the inserted lines are known.
    assert unsafe(GHA, "ci.yml") == {4, 5}


@pytest.mark.parametrize(
    "inserted,ok",
    [
        ("      # same as the next step", True),
        ("    # shallower", True),
        ("# column zero", True),
        ("", True),  # a blank line: clip chomping drops trailing blanks
        ("      ", True),  # whitespace no deeper than the opener
        ("       # one deeper than the opener line", False),
        ("        # at the run: key", False),
        ("          # at the content indent", False),
        ("            # deeper than the content", False),
        ("            ", False),  # blanks deeper than the opener are scalar content
        ("\t# tab-indented", False),  # a tab is indentation we cannot compare: fail closed
    ],
)
def test_yaml_block_tail_indent_rule(inserted: str, ok: bool) -> None:
    sh = lang("yaml")
    base = GHA.splitlines()
    after = "\n".join([*base[:6], inserted, *base[6:]]) + "\n"
    why = context_guard(GHA, after, sh)
    assert (why is None) is ok, why
    if not ok:
        assert why and "would join the block scalar" in why and "base line 6" in why, why


def test_yaml_block_tail_checks_every_inserted_line() -> None:
    sh = lang("yaml")
    base = GHA.splitlines()
    after = "\n".join([*base[:6], "      # fine", "          # joins the block", *base[6:]]) + "\n"
    why = context_guard(GHA, after, sh)
    assert why and "would join the block scalar" in why and "edited line 8" in why, why


@pytest.mark.parametrize(
    "chomp,ok",
    [("|", True), ("|-", True), ("|2", True), ("|+", False), (">+", False), ("|2+", False)],
)
def test_yaml_blank_line_after_keep_chomped_block(chomp: str, ok: bool) -> None:
    sh = lang("yaml")
    before = f"k: {chomp}\n  x\nj: 1\n"
    after = f"k: {chomp}\n  x\n\nj: 1\n"
    why = context_guard(before, after, sh)
    assert (why is None) is ok, why
    if not ok:
        assert why and "keep-chomped" in why, why


def test_yaml_block_tail_at_end_of_file() -> None:
    sh = lang("yaml")
    assert context_guard("k: |\n  x\n", "k: |\n  x\n# end\n", sh) is None
    assert context_guard("k: |\n  x\n", "k: |\n  x\n  # end\n", sh) is not None


def test_yaml_block_tail_uses_opener_line_indent_for_dash_items() -> None:
    sh = lang("yaml")
    before = "- - |\n    x\n- y\n"
    # The opener line starts at column 0, so anything deeper than 0 may join the block.
    assert context_guard(before, "- - |\n    x\n# c\n- y\n", sh) is None
    assert context_guard(before, "- - |\n    x\n  # c\n- y\n", sh) is not None


def test_yaml_block_tail_does_not_relax_other_unsafe_positions() -> None:
    sh = lang("yaml")
    # A block whose last line ends in a backslash is still a continuation.
    before = "k: |\n  x \\\nj: 1\n"
    assert context_guard(before, "k: |\n  x \\\n# c\nj: 1\n", sh) is not None
    # Quoted multi-line scalars and plain continuations keep their own interior rule.
    assert context_guard('k: "a\n  b"\nj: 1\n', 'k: "a\n  # c\n  b"\nj: 1\n', sh) is not None


@pytest.mark.parametrize(
    "before,after",
    [
        # Document-level block scalar: its content may sit at column 0, so nothing is safe after.
        ("--- |\nhello\n", "--- |\n# c\nhello\n"),
        ("--- >-\n  hello\n", "--- >-\n  hello\n# c\n"),
        ("|\nhello\n", "|\n# c\nhello\n"),
        # Header alone on its line, indented deeper than its content: the opener line says nothing
        # about where the content starts.
        ("k:\n    |\n  text\nj: 1\n", "k:\n    |\n  # c\n  text\nj: 1\n"),
        ("k:\n  !!str |\n  text\nj: 1\n", "k:\n  !!str |\n  # c\n  text\nj: 1\n"),
        ("&a |\n  text\n", "&a |\n  text\n# c\n"),
    ],
)
def test_yaml_unanchored_block_header_keeps_the_old_rule(before: str, after: str) -> None:
    # Only a "key: |" or "- |" opener tells us the content is indented deeper than that line.
    why = context_guard(before, after, lang("yaml"))
    assert why and "not a `key: |`" in why, why


@pytest.mark.parametrize(
    "before,after",
    [
        ("- |\n  x\n- y\n", "- |\n  x\n# c\n- y\n"),
        ("- !!str |\n  x\n- y\n", "- !!str |\n  x\n# c\n- y\n"),
        ("a:\n  k: &x !!str >-\n    x\n  j: 1\n", "a:\n  k: &x !!str >-\n    x\n  # c\n  j: 1\n"),
        ('"a: b": |\n  x\nj: 1\n', '"a: b": |\n  x\n# c\nj: 1\n'),
    ],
)
def test_yaml_anchored_block_header_gets_the_new_rule(before: str, after: str) -> None:
    assert context_guard(before, after, lang("yaml")) is None
