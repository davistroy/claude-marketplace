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
    ("a.js", " * eslint no-console: off"),
    ("a.js", "/* eslint"),
    ("a.js", "/* globals"),
    ("a.ts", "/* jshint"),
    ("a.js", "/* jslint"),
    ("a.js", " * globals foo, bar"),
    ("a.ts", "globals foo"),
    ("a.js", " jshint esversion: 6 */"),
    ("a.js", " * jslint node"),
    ("s.css", "/*# sourceMappingURL=a.css.map */"),
    # Go tools
    ("m.go", "//go:build ignore"),
    ("m.go", "// +build ignore"),
    ("m.go", "// +kubebuilder:object:generate=true"),
    ("m.go", "//line other.go:10"),
    ("m.go", "//export Foo"),
    ("m.go", "// Output: 3"),
    ("m.go", "// Unordered output: a"),
    ("m.go", "/* Output: 3 */"),
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
    ("A.java", " * globals are avoided here"),
    ("m.c", "/* jshint"),
    ("m.py", "  jshint esversion: 6"),
    ("A.cs", " * jslint is a JavaScript tool"),
    ("m.go", "globals foo, bar"),
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
    # "{{ x }}" left this list in fix round 2 (item 7): template markers apply only in template
    # files; see test_template_braces_fail_where_templates_are_evaluated.
    "line",
    ["noqa", "prettier-ignore", "biome-ignore lint: x", "@generated", "nolint"],
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


# ---------------------------------------------------------------------------
# Fix round 2 (review findings).
# ---------------------------------------------------------------------------


# Item 1 (unit): comment_chunk_ok counts nesting depth for nesting languages.
def test_comment_chunk_counts_nesting_depth() -> None:
    from document_repo.verify import comment_chunk_ok

    for name in ("sql", "rs"):
        lg = lang(name)
        assert comment_chunk_ok(["/* a /* b */ c */"], lg) == (True, "")
        assert comment_chunk_ok(["/* a", "/* b */", "c */"], lg) == (True, "")
        ok, why = comment_chunk_ok(["/* staging/*.csv */"], lg)
        assert not ok and why == "unterminated block comment in inserted lines"
        ok, why = comment_chunk_ok(["/* a */ */"], lg)
        assert not ok and "code after" in why
    assert comment_chunk_ok(["/* staging/*.csv */"], lang("css")) == (True, "")


# Item 3 (unit): the Go example-output run, from "// Output:" through the closing "}".
def test_go_example_output_points() -> None:
    text = (
        "package x\n\nfunc ExampleF() {\n\tf()\n\t// Output:\n\t// 1\n}\n\n"
        "func ExampleG() {\n\tg()\n}\n"
    )
    # Line 4 is "// Output:", line 6 the closing "}": positions 4..6 are unsafe.
    assert {4, 5, 6} <= unsafe(text, "x_test.go")
    assert not {0, 1, 2, 3, 7, 8, 9, 10, 11} & unsafe(text, "x_test.go")


def test_go_output_without_closing_brace_fails_closed() -> None:
    text = "func ExampleF() {\n\tf()\n\t// Output:\n\t// 1\n"
    assert {2, 3, 4} <= unsafe(text, "x_test.go")


def test_go_output_comment_outside_example_is_plain() -> None:
    text = "func helper() {\n\tf()\n\t// Output: is logged\n}\nvar x = 1\n"
    assert not unsafe(text, "m.go")


# Item 5 (unit): YAML tabs.
def test_yaml_tab_in_inserted_indentation_fails() -> None:
    y = lang("yaml")
    why = common_guards("ci.yml", "a: 1\n", "\t# c\na: 1\n", y)
    assert why and "tab" in why, why
    assert common_guards("ci.yml", "a: 1\n", "  # c\ta tab inside is fine\na: 1\n", y) is None
    # Tabs are only a YAML rule: shell and make have their own tab handling.
    assert common_guards("a.sh", "echo a\n", "\t# c\necho a\n", lang("sh")) is None


# Item 6: a language with no scanner fails closed at every position.
def test_unknown_scanner_language_fails_closed() -> None:
    from document_repo.languages import Lang

    fake = Lang("klingon", ("#",), (), "comment-lines")
    assert unsafe_insert_points(["a", "b"], fake) == {0, 1, 2}
    why = context_guard("a\nb\n", "a\n# c\nb\n", fake)
    assert why and "verbatim" in why, why


# Item 7: directive patterns that were too broad.
@pytest.mark.parametrize(
    "rel,line",
    [
        ("a.js", "// Shared eslint configuration"),
        ("a.ts", "// eslint runs in CI"),
        ("a.js", "/* Lint with eslint before committing. */"),
        ("ci.yml", "# Encoding: UTF-8"),
        ("ci.yml", "# coding: latin-1 is not read by YAML"),
        ("a.sh", "# encoding=utf-8 for the output"),
        ("A.java", "// Transcoding: helpers"),
        ("m.py", "# {{ name }} is filled in by the caller"),
        ("values.yaml", "# {{ .Values.x }} is rendered by the chart's templates"),
        ("m.go", "// {{.Name}} is a text/template action"),
    ],
)
def test_round2_prose_is_not_a_directive(rel: str, line: str) -> None:
    assert common_guards(rel, "x\n", f"{line}\nx\n", lang_for(rel)) is None


@pytest.mark.parametrize(
    "rel,line",
    [
        ("a.js", "// eslint-disable-line"),
        ("a.js", "/* eslint-disable */"),
        ("a.js", "// eslint-enable no-console"),
        ("a.js", "/* eslint quotes: off */"),
        ("a.js", "/*eslint quotes: off*/"),
        ("a.js", "/* eslint-env node */"),
        ("m.py", "# -*- coding: latin-1 -*-"),
        ("m.py", "# vim: set fileencoding=ascii :"),
        ("ci.yml", "# -*- coding: latin-1 -*-"),
        ("a.sh", "# -*- mode: sh; coding: utf-8 -*-"),
    ],
)
def test_round2_real_directives_still_fail(rel: str, line: str) -> None:
    why = common_guards(rel, "x\n", f"{line}\nx\n", lang_for(rel))
    assert why is not None and DIRECTIVE in why, why


def test_yaml_encoding_note_is_not_a_protected_header() -> None:
    before = "# Encoding: UTF-8\na: 1\n"
    assert common_guards("ci.yml", before, "# CI settings.\n" + before, lang("yaml")) is None
    emacs = "# -*- coding: latin-1 -*-\na: 1\n"
    why = common_guards("ci.yml", emacs, "# CI settings.\n" + emacs, lang("yaml"))
    assert why and "protected header" in why, why


@pytest.mark.parametrize(
    "rel,before",
    [
        ("i.html", "<p>x</p>\n"),
        ("chart/templates/deploy.yaml", "kind: Deployment\n"),
        ("deploy.yaml", "image: {{ .Values.image }}\n"),
        ("{{cookiecutter.slug}}/m.py", "x = 1\n"),
        ("m.py", "T = '{% if x %}'\n"),
    ],
    ids=["html", "helm-templates-dir", "base-is-a-template", "cookiecutter-path", "jinja-in-py"],
)
def test_template_braces_fail_where_templates_are_evaluated(rel: str, before: str) -> None:
    after = f"# {{{{ x }}}}\n<!-- {{{{ x }}}} -->\n{before}"
    why = common_guards(rel, before, after, lang_for(rel))
    assert why is not None and DIRECTIVE in why, why


# Items 8, 9, 10: guards.py hygiene.
GUARDS_SRC = guards_mod.__file__


def test_guards_source_has_no_literal_bom() -> None:
    with open(GUARDS_SRC, "rb") as fh:
        assert b"\xef\xbb\xbf" not in fh.read()


def test_guards_source_has_no_type_comments() -> None:
    import io
    import tokenize

    with open(GUARDS_SRC, encoding="utf-8") as fh:
        tokens = list(tokenize.generate_tokens(io.StringIO(fh.read()).readline))
    comments = [t.string for t in tokens if t.type == tokenize.COMMENT]
    # re.search, as the tool applies its patterns: a "# type:" quoted mid-comment counts too.
    assert not [c for c in comments if re.search(r"#\s*type\s*:", c)]


def test_guards_source_is_not_flagged_by_its_own_directive_patterns() -> None:
    # If the skill ever comments this file, its own comments must not read as directives.
    import io
    import tokenize

    from document_repo.languages import PYTHON

    with open(GUARDS_SRC, encoding="utf-8") as fh:
        tokens = list(tokenize.generate_tokens(io.StringIO(fh.read()).readline))
    flagged = [
        (t.start[0], t.string)
        for t in tokens
        if t.type == tokenize.COMMENT and guards_mod._is_directive(t.string, PYTHON)
    ]
    assert not flagged


def test_guards_source_has_no_assert_statements() -> None:
    import ast

    with open(GUARDS_SRC, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    assert not [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assert)]


# ---------------------------------------------------------------------------
# Fix round 3 (convergence).
# ---------------------------------------------------------------------------


# D1: JS/TS have no comment-lines scanner any more; they are verified only by ts-printer.
@pytest.mark.parametrize("rel", ["a.ts", "a.js"])
def test_js_ts_have_no_context_scanner(rel: str) -> None:
    assert unsafe_insert_points(["const a = 1;", "const b = 2;"], lang_for(rel)) == {0, 1, 2}
    assert "javascript" not in guards_mod._SYNTAX and "typescript" not in guards_mod._SYNTAX


# D2: ESLint and JS global directives written across several lines of a block comment.
@pytest.mark.parametrize(
    "chunk",
    [
        "/* eslint\n   no-console: off */",
        "/*\n eslint no-console: off\n*/",
        "/*\n * eslint quotes: off\n */",
        "/*\neslint\n  quotes: off */",
        "/*\n * eslint-disable\n */",
        "/*\n global foo\n*/",
        "/*\n * exported bar\n */",
        "/* global\n   foo */",
        "/* exported\n   bar */",
    ],
    ids=[
        "eslint-alone-on-opener",
        "eslint-first-word",
        "eslint-after-star",
        "eslint-alone-in-body",
        "eslint-disable-after-star",
        "global-first-word",
        "exported-after-star",
        "global-alone-on-opener",
        "exported-alone-on-opener",
    ],
)
@pytest.mark.parametrize("rel", ["a.js", "a.ts"])
def test_multiline_eslint_and_global_directives_fail(rel: str, chunk: str) -> None:
    before = "const a = 1;\nconst b = 2;\n"
    after = before.replace("const b", chunk + "\nconst b")
    why = common_guards(rel, before, after, lang_for(rel))
    assert why is not None and DIRECTIVE in why, why


# Fix round 4, item 2: globals, jshint and jslint also open a directive on the line after "/*".
@pytest.mark.parametrize(
    "chunk",
    [
        "/*\n globals foo */",
        "/*\nglobals foo, bar\n*/",
        "/*\n jshint esversion: 6 */",
        "/*\n * globals foo\n */",
        "/* globals\n   foo */",
        "/* jshint\n   esversion: 6 */",
        "/*\njslint node: true\n*/",
    ],
    ids=[
        "globals-after-opener",
        "globals-own-line",
        "jshint-after-opener",
        "globals-after-star",
        "globals-alone-on-opener",
        "jshint-alone-on-opener",
        "jslint-own-line",
    ],
)
@pytest.mark.parametrize("rel", ["a.js", "a.ts"])
def test_multiline_globals_and_jshint_directives_fail(rel: str, chunk: str) -> None:
    before = "const a = 1;\nconst b = 2;\n"
    after = before.replace("const b", chunk + "\nconst b")
    why = common_guards(rel, before, after, lang_for(rel))
    assert why is not None and DIRECTIVE in why, why


@pytest.mark.parametrize(
    "chunk",
    [
        "/*\n globals foo */",
        "/*\nglobals foo, bar\n*/",
        "/*\n jshint esversion: 6 */",
    ],
)
@pytest.mark.parametrize("rel", ["m.c", "A.java", "m.py", "m.go", "a.sh"])
def test_multiline_globals_and_jshint_are_prose_outside_javascript(rel: str, chunk: str) -> None:
    before = "x\ny\n"
    after = before.replace("y", chunk + "\ny")
    assert common_guards(rel, before, after, lang_for(rel)) is None


@pytest.mark.parametrize(
    "chunk",
    [
        "// globals are bad",
        "// jshint is not used here",
        "// globals foo",
        "/* The globals are listed below. */",
    ],
)
def test_globals_line_comment_prose_still_passes(chunk: str) -> None:
    before = "const a = 1;\nconst b = 2;\n"
    after = before.replace("const b", chunk + "\nconst b")
    assert common_guards("a.js", before, after, lang("js")) is None


@pytest.mark.parametrize(
    "chunk",
    [
        "// eslint runs in CI",
        "// Shared eslint configuration",
        "/* Lint with eslint before committing. */",
        "/**\n * Shared eslint configuration.\n */",
        "/*eslint*/",
        "// global state lives in store.ts",
    ],
)
def test_eslint_prose_still_passes(chunk: str) -> None:
    before = "const a = 1;\nconst b = 2;\n"
    after = before.replace("const b", chunk + "\nconst b")
    assert common_guards("a.js", before, after, lang("js")) is None


# D6: a Go block comment whose first content line is "Output:" is example output.
@pytest.mark.parametrize(
    "chunk",
    [
        "\t/* Output: hi */",
        "\t/*\n\tOutput: hi\n\t*/",
        "\t/*\n\n\tUnordered output: hi\n\t*/",
        "\t/*Output:\n\thi */",
    ],
    ids=["one-line", "multi-line", "multi-line-unordered-after-blank", "tight"],
)
def test_go_block_output_comment_is_a_directive(chunk: str) -> None:
    before = 'package x\n\nfunc ExampleHi() {\n\tprintln("hi")\n}\n'
    after = before.replace("\n}\n", "\n" + chunk + "\n}\n")
    why = common_guards("x_test.go", before, after, lang("go"))
    assert why is not None and DIRECTIVE in why, why


@pytest.mark.parametrize(
    "chunk", ["\t/*\n\tPrints hi.\n\tOutput: none\n\t*/", "\t/* Prints hi. */", "\t/*\n\t*/"]
)
def test_go_block_comment_without_output_first_passes(chunk: str) -> None:
    before = 'package x\n\nfunc ExampleHi() {\n\tprintln("hi")\n}\n'
    after = before.replace("\n}\n", "\n" + chunk + "\n}\n")
    assert common_guards("x_test.go", before, after, lang("go")) is None


# D7: the Jinja comment opener "{#" is a template marker, with the same scope as "{{" and "{%".
@pytest.mark.parametrize(
    "rel,before",
    [
        ("templates/a.yaml", "a: 1\n"),
        ("i.html", "<p>x</p>\n"),
        ("deploy.yaml", "image: {{ .Values.image }}\n"),
    ],
)
def test_jinja_comment_opener_fails_in_templates(rel: str, before: str) -> None:
    after = f"# {{# note #}}\n<!-- {{# note #}} -->\n{before}"
    why = common_guards(rel, before, after, lang_for(rel))
    assert why is not None and DIRECTIVE in why, why


def test_jinja_comment_opener_is_prose_outside_templates() -> None:
    assert common_guards("ci.yml", "a: 1\n", "# {# not a template\na: 1\n", lang("yml")) is None
    # "${#x}" (shell string length) in a base does not make the file a template.
    sh = lang("sh")
    assert common_guards("a.sh", "echo ${#x}\n", "# {{ x }} note\necho ${#x}\n", sh) is None
