"""``jscomments.comment_lines``: the own-line comments of a JavaScript or TypeScript file.

This is a lexer, not the TypeScript compiler. It exists so ``traps`` can scan a whole file and
tell a comment from text that only looks like one (a template literal, a string, a regex).
"""

from __future__ import annotations

import pytest

from document_repo.jscomments import comment_lines

LINE = 0  # the key of a line comment (verify.LINE_COMMENT)


def found(text: str) -> list[tuple[int, int, str]]:
    return list(comment_lines(text))


def test_line_comments_on_their_own_line_with_their_numbers() -> None:
    assert found("a;\n// one\n  // two\nb;\n") == [(2, LINE, " one"), (3, LINE, " two")]


def test_a_comment_after_code_is_not_on_its_own_line() -> None:
    assert found("a; // trailing\nb; /* trailing */\n") == []


def test_a_block_comment_gives_one_entry_per_line_with_one_key() -> None:
    assert found("/**\n * Role: x.\n * Traps: y\n */\nz;\n") == [
        (1, 1, "*"),
        (2, 1, " * Role: x."),
        (3, 1, " * Traps: y"),
        (4, 1, " "),
    ]


def test_a_one_line_block_comment_and_two_of_them_get_two_keys() -> None:
    assert found("/* a */\n/* b */\n") == [(1, 1, " a "), (2, 2, " b ")]


def test_a_block_comment_that_is_not_closed_runs_to_the_end() -> None:
    assert found("x;\n/* open\n * more\n") == [(2, 1, " open"), (3, 1, " * more")]


def test_a_block_comment_does_not_end_at_a_slash_star_slash() -> None:
    assert found("/*/ still inside */\n") == [(1, 1, "/ still inside ")]


def test_a_line_comment_inside_a_block_comment_is_part_of_the_block() -> None:
    assert found("/*\n// not a line comment\n*/\n") == [
        (1, 1, ""),
        (2, 1, "// not a line comment"),
        (3, 1, ""),
    ]


def test_crlf_line_endings_keep_the_numbering() -> None:
    assert found("a;\r\n// one\r\n/* two */\r\n") == [(2, LINE, " one"), (3, 1, " two ")]


@pytest.mark.parametrize(
    "text",
    [
        "const s = `\n// Traps: inside a template\n`;\n",
        "const s = `\n/* Traps: inside a template */\n`;\n",
        "const s = `a ${ x } b\n// Traps: after an expression\n c`;\n",
        "const s = `a ${ `b ${ c }\n// Traps: nested` } d\n// Traps: still in\n`;\n",
        "const s = `a ${ {x: 1}.x }\n// Traps: braces in the expression\n`;\n",
        "const s = 'a // Traps: x';\n",
        'const s = "a // Traps: x";\n',
        "const s = 'it\\'s // Traps: x';\n",
        "const s = 'line one \\\n// Traps: after a continued string';\n",
        "const r = /[/]\\/\\/ Traps: x/;\n",
    ],
    ids=[
        "template",
        "template-block",
        "template-expression",
        "template-nested",
        "template-braces",
        "single-quoted",
        "double-quoted",
        "escaped-quote",
        "continued-string",
        "regex",
    ],
)
def test_text_that_only_looks_like_a_comment_is_not_one(text: str) -> None:
    assert found(text) == []


def test_comments_after_a_template_regex_or_division_are_found() -> None:
    text = (
        "const s = `a ${ `b ${c}` } d`;\n"
        "// Traps: after a nested template\n"
        "const re = /[\"'`]/g;\n"
        "// Traps: after a regex holding quotes\n"
        "const q = a / b / c;\n"
        "// Traps: after a division\n"
        "const t = x.replace(/\\//g, '');\n"
        "// Traps: after a regex with an escaped slash\n"
    )
    assert [(n, t) for n, _k, t in found(text)] == [
        (2, " Traps: after a nested template"),
        (4, " Traps: after a regex holding quotes"),
        (6, " Traps: after a division"),
        (8, " Traps: after a regex with an escaped slash"),
    ]


@pytest.mark.parametrize(
    "before",
    ["return ", "x = ", "f(", "[", "{ a: ", "a && ", "!", "typeof ", "case ", "; ", ", "],
)
def test_a_slash_after_these_starts_a_regex(before: str) -> None:
    text = f"x;\n{before}/['\"`]+/.test(s);\n// Traps: real\n"
    assert [(n, t) for n, _k, t in found(text)] == [(3, " Traps: real")]


@pytest.mark.parametrize("before", ["a ", "a) ", "a] ", "1 ", "x.y "])
def test_a_slash_after_a_value_is_a_division(before: str) -> None:
    # Treated as a regex, ``/ 2 + '`` would swallow the quote and desync the rest of the file.
    text = f"v = {before}/ 2 + '\n// Traps: real\n"
    assert [(n, t) for n, _k, t in found(text)] == [(2, " Traps: real")]


def test_a_quote_that_never_closes_on_its_line_is_just_a_character() -> None:
    # JSX text: an apostrophe is not a string.
    assert [(n, t) for n, _k, t in found("<p>don't</p>;\n// Traps: after jsx\n")] == [
        (2, " Traps: after jsx")
    ]


def test_jsx_comment_braces_are_not_an_own_line_comment() -> None:
    assert found("<a>\n  {/* Traps: x */}\n</a>\n") == []


def test_a_shebang_and_strict_directive_do_not_matter() -> None:
    assert found("#!/usr/bin/env node\n'use strict';\n// Traps: x\n") == [(3, LINE, " Traps: x")]


def test_a_closing_brace_outside_a_template_expression_is_just_a_brace() -> None:
    assert [n for n, _k, _t in found("}\n}\n// Traps: x\n")] == [3]


def test_a_template_that_never_closes_swallows_the_rest() -> None:
    assert found("const s = `abc\n// Traps: x\n") == []


def test_empty_and_comment_free_text() -> None:
    assert found("") == []
    assert found("export const a = 1;\n") == []


def test_a_slash_at_the_very_start_of_the_text_starts_a_regex() -> None:
    assert [(n, t) for n, _k, t in found("/['\"`]+/.test(s);\n// Traps: real\n")] == [
        (2, " Traps: real")
    ]


@pytest.mark.parametrize(
    "text",
    [
        "const s = `a \\` still inside\n// Traps: x\n`;\n",
        "const s = `cost $5 and $ alone\n// Traps: x\n`;\n",
        "const s = `a \\${ not an expression\n// Traps: x\n`;\n",
    ],
    ids=["escaped-backtick", "bare-dollar", "escaped-expression"],
)
def test_a_template_literal_ends_only_at_an_unescaped_backtick(text: str) -> None:
    assert found(text) == []


def test_an_unclosed_block_comment_does_not_invent_a_last_line() -> None:
    assert found("/* a\n * b") == [(1, 1, " a"), (2, 1, " * b")]


def test_a_block_that_closes_after_a_template_expression_is_not_a_template_again() -> None:
    text = "function f() {\n  const s = `a ${x} b`;\n}\n// Traps: real\nconst o = { a: 1 };\n"
    assert [(n, t) for n, _k, t in found(text)] == [(4, " Traps: real")]


def test_braces_inside_and_after_several_templates_stay_balanced() -> None:
    text = (
        "const a = `${ {x: 1}.x }`;\n"
        "const b = `${ f({y: 2}) } and ${ g() }`;\n"
        "if (a) { b; }\n"
        "}\n"
        "// Traps: real\n"
    )
    assert [(n, t) for n, _k, t in found(text)] == [(5, " Traps: real")]


@pytest.mark.parametrize("text", ["const s = `abc\\", "const s = `abc$", "const s = `abc"])
def test_a_template_that_ends_the_text_inside_an_escape_or_a_dollar(text: str) -> None:
    assert found(text) == []


# --- review round 2: linear in the length of a line, and lazy -----------------------------------


def test_comment_lines_is_lazy() -> None:
    stream = comment_lines("// a\n" * 1_000_000)
    assert next(stream) == (1, LINE, " a")  # the other 999,999 are not read yet


@pytest.mark.parametrize(
    "text, expected",
    [
        ("  \t// indented\n", [(1, LINE, " indented")]),
        ("\u00a0// no-break space\n", [(1, LINE, " no-break space")]),
        ("/* a */ // b\n", [(1, 1, " a ")]),
        ("x; /* a */\n// b\n", [(2, LINE, " b")]),
        ("/* a\nb */ // c\n", [(1, 1, " a"), (2, 1, "b ")]),
        ("/* a\n*/ /* b */\n", [(1, 1, " a"), (2, 1, "")]),
        ("a\n\n  /* x */\n\t// y\n", [(3, 1, " x "), (4, LINE, " y")]),
    ],
    ids=[
        "indent",
        "nbsp",
        "after-block",
        "after-code",
        "after-multiline-block",
        "two-blocks",
        "blank-lines",
    ],
)
def test_a_comment_is_on_its_own_line_only_when_nothing_but_space_comes_first(
    text: str, expected: list[tuple[int, int, str]]
) -> None:
    assert found(text) == expected


def test_many_comments_on_one_long_line_cost_time_linear_in_the_line() -> None:
    """One minified line with 100,000 trailing comments: each used to re-scan the line so far."""
    import time

    text = "// header\n" + "x=1;/*c*/" * 100_000 + "\n"
    start = time.perf_counter()
    assert found(text) == [(1, LINE, " header")]
    assert time.perf_counter() - start < 3.0
