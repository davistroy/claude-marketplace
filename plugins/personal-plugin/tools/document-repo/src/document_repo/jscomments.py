"""The own-line comments of a JavaScript or TypeScript file, found with a small lexer.

``traps`` needs to know whether a line such as ``// Traps: x`` is a comment or only text that
looks like one: a line inside a template literal, a string or a regular expression. The verifier
answers that question with the TypeScript compiler, which needs node and is slow to start for each
file. This module answers it for the one thing ``traps`` asks, with the standard library only.

It is a lexer, not a parser. It tracks strings (single line, with escapes), template literals
(including nested ``${ ... }`` expressions), regular-expression literals, line comments and block
comments. Whether a ``/`` starts a regular expression or is a division is decided from the text
before it, the way every lexer without a parser has to; a wrong guess can only make it read a
little of the code as a regex or a division, and a quote that never closes on its own line is
just a character (JSX text has apostrophes). A template literal that is opened and never closed
swallows the rest of the file, which hides comments from ``traps``; it never invents one.

``comment_lines`` returns an entry for every line of every comment that starts on a line of its
own: a ``/* ... */`` after code, and ``{/* ... */}`` in JSX, are not headers and are left out.
"""

from __future__ import annotations

import re

# One token at a time. Order matters: a line comment before the slash, a closed block comment before
# an unclosed one, a string before the lone-character fallback that catches a quote with no partner.
_STRING = (
    r"'[^'\\\n]*(?:\\.[^'\\\n]*)*'"  # single-quoted, may continue a line with a backslash
    "|"
    r'"[^"\\\n]*(?:\\.[^"\\\n]*)*"'
)
_TOKEN = re.compile(
    "|".join(
        [
            r"(?P<line>//[^\n]*)",
            r"(?P<block>/\*.*?\*/)",
            r"(?P<open>/\*.*)",
            f"(?P<string>{_STRING})",
            r"(?P<template>`)",
            r"(?P<brace>[{}])",
            r"(?P<slash>/)",
            r"(?P<plain>[^/'\"`{}]+)",
            r"(?P<lone>.)",
        ]
    ),
    re.S,
)
# The text of a template literal up to the next backtick, backslash or dollar sign.
_TEMPLATE_RUN = re.compile(r"[^`\\$]*")
# A regular-expression literal: a body without an unescaped slash (a slash inside [...] is fine),
# then flags. It stays on one line, so a wrong guess costs at most that line.
_REGEX = re.compile(
    r"/(?![/*])[^/\\\n\[]*(?:(?:\\.|\[[^\]\\\n]*(?:\\.[^\]\\\n]*)*\])[^/\\\n\[]*)*/[A-Za-z]*"
)
_TRAILING_WORD = re.compile(r"[A-Za-z_$][\w$]*$")

#: A slash after one of these starts a regular expression: it cannot be a division.
_REGEX_AFTER_CHARS = frozenset("(,=:[!&|?{};+-*%<>~^")
_REGEX_AFTER_WORDS = frozenset(
    {
        "return",
        "typeof",
        "instanceof",
        "in",
        "of",
        "new",
        "delete",
        "void",
        "throw",
        "case",
        "do",
        "else",
        "yield",
        "await",
    }
)

#: The key of a line comment, as in ``verify.LINE_COMMENT``. A block comment is numbered from 1.
LINE_COMMENT = 0


def comment_lines(text: str) -> list[tuple[int, int, str]]:
    """``(1-based line, key, text)`` for each line of each comment that starts on its own line.

    ``key`` is ``LINE_COMMENT`` for a ``//`` comment and the block's number for a ``/* */``
    comment. ``text`` is what is inside the comment on that line, with only the opening and closing
    marker removed (``// x`` gives `` x``; a block line keeps its leading ``*``). Lines end at
    ``\\n``, and a ``\\r`` before it is not part of the text. Nothing is read twice, so the cost is
    linear.
    """
    found: list[tuple[int, int, str]] = []
    size = len(text)
    pos = 0
    line_no, line_pos = 1, 0
    blocks = 0
    open_braces: list[int] = []  # one per open ``${``: the ``{`` not yet closed inside it
    in_template = False
    prev, word = "", ""  # the last character of code before this point, and the word it ends
    while pos < size:
        if in_template:
            while pos < size:
                run = _TEMPLATE_RUN.match(text, pos)
                assert run is not None  # the pattern can match nothing, so it always matches
                pos = run.end()
                if pos >= size:
                    break
                char = text[pos]
                if char == "`":
                    pos, in_template, prev, word = pos + 1, False, "`", ""
                    break
                if char == "$" and text.startswith("${", pos):
                    open_braces.append(0)
                    pos, in_template, prev, word = pos + 2, False, "{", ""
                    break
                pos += 2 if char == "\\" else 1
            continue
        token = _TOKEN.match(text, pos)
        assert token is not None  # the last alternative matches any one character
        kind, start, pos = token.lastgroup, token.start(), token.end()
        if kind in ("line", "block", "open"):
            if text[text.rfind("\n", 0, start) + 1 : start].strip():
                continue  # code comes first on this line: not a header
            line_no += text.count("\n", line_pos, start)
            line_pos = start
            body = token.group()
            if kind == "line":
                found.append((line_no, LINE_COMMENT, body[2:].removesuffix("\r")))
                continue
            blocks += 1
            # An unclosed comment ends at the end of the text: a final newline ends its last line.
            inner = body[2:-2] if kind == "block" else body[2:].removesuffix("\n")
            found.extend(
                (line_no + offset, blocks, part.removesuffix("\r"))
                for offset, part in enumerate(inner.split("\n"))
            )
        elif kind == "template":
            in_template = True
        elif kind == "brace":
            char = token.group()
            if open_braces and char == "{":
                open_braces[-1] += 1
            elif open_braces and open_braces[-1] == 0:
                open_braces.pop()
                in_template = True  # the expression ended: back into the template text
            elif open_braces:
                open_braces[-1] -= 1
            prev, word = char, ""
        elif kind == "slash":
            if prev == "" or prev in _REGEX_AFTER_CHARS or word in _REGEX_AFTER_WORDS:
                regex = _REGEX.match(text, start)
                if regex is not None:
                    pos, prev, word = regex.end(), "0", ""  # a value: the next slash divides
                    continue
            prev, word = "/", ""
        elif kind == "plain":
            tail = token.group().rstrip()
            if tail:
                found_word = _TRAILING_WORD.search(tail)
                prev, word = tail[-1], found_word.group() if found_word else ""
        else:  # a string, or a lone character such as a quote that never closes on its line
            prev, word = token.group()[-1], ""
    return found
