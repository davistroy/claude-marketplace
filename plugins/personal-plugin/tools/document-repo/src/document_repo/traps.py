"""Harvest the ``Traps:`` labels that a branch added to comments.

The Synthesizer writes ``agent_notes.traps`` before any commenter has read a file. The commenters
then find more traps and write them as ``Traps:`` lines in file headers (comment-standards.md),
and nothing carried those back into the model, AGENTS.md or the explorer. ``traps`` lists them so
the orchestrator can fold the ones that matter beyond their own file into the model.

``harvest_traps(repo, before)`` compares the work tree with the commit ``before``, picks files the
way ``verify --changed`` does (``verify.changed_files``: everything but Markdown and the skill's
own explorer output), and returns one ``Trap`` for each ``Traps:`` label on a line the branch
added. A label that existed at ``before`` is the owner's: the analysts already read it in the
source. Only lines of a comment count. How a comment is told from text that looks like one
depends on the language, and is exact only where a real tokenizer is used:

- Python is scanned whole with the tokenizer (a ``#`` inside a string is not a comment) and the
  verifier's docstring rule (``verify.docstring_stmts``).
- JavaScript and TypeScript are scanned whole with ``jscomments``, a lexer that knows strings,
  template literals and regular expressions. The whole file, not just the added lines, because the
  TypeScript printer accepts a ``Traps:`` line inserted into an owner's existing ``/** ... */``,
  and an added line alone cannot be seen to be inside a block comment. The result is masked by
  the added lines.
- Every other language is scanned one added run of lines at a time with the verifier's own chunk
  scanner (``verify.comment_scan``). That is what the verifier proves for them: an added run must
  be whole comments. Without ``before`` the run is the whole file, which is not proven, so a
  ``# Traps:`` line inside a shell heredoc or a multi-line string can pass for a comment there.
  The orchestrator filters the list; SKILL.md says so.

A label inside code (``print("Traps: x")``) is not a trap.

What a trap's text is: the label's text, then the lines after it that are comment lines of the
same comment (the same ``//`` or ``#`` run, the same block comment, the same docstring), were
added too, are not blank, and do not start another header label. Exactly one comment marker is
removed from each line (``//``, ``///`` and ``//!`` are each one; so are ``#`` and ``##``), and in
a block comment one leading ``*``. What follows is kept, so ``--   -1 means`` stays ``-1 means``.
Runs of whitespace become one space and the lines are joined with one. Lines are numbered as an
editor shows them (``remap.split_lines``): a form feed does not start a line.

Without ``before``, the files are every tracked, non-exempt one and every ``Traps:`` comment in
them counts, the owner's included. A ``--phase docs`` run needs this: its commenters ran in an
earlier run, so no base separates their traps from the owner's.

Files are read one at a time and the result is a generator underneath, so memory stays at one
file. A file over ``MAX_BYTES`` (``MAX_PYTHON_BYTES`` for Python), or whose version at ``before``
is, is not read and is reported in the ``skipped`` list. A file that is not UTF-8, a symlink,
anything that is not a regular file, and a Python file that does not parse (the verifier would
have failed it) are skipped without a report: none of them can hold a trap the skill wrote.
"""

from __future__ import annotations

import ast
import difflib
import io
import os
import re
import stat
import subprocess
import tokenize
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .commit import GitError, _resolve_commit, _top
from .jscomments import comment_lines
from .languages import Lang, detect
from .remap import split_lines
from .verify import (
    LINE_COMMENT,
    changed_files,
    comment_scan,
    docstring_stmts,
    git_show,
    git_size,
    tracked_files,
)

#: The labels comment-standards.md has headers use. A trap ends where the next one starts.
HEADER_LABELS = ("Role", "Used by", "Inputs", "Outputs", "Side effects", "Invariants", "Traps")

TRAPS_LABEL = "Traps:"
_ANY_LABEL = re.compile("(?:" + "|".join(re.escape(name) for name in HEADER_LABELS) + "):")

#: A file larger than this (or whose base version is) is not read, so memory stays at one file's
#: worth. Peak RSS measured on this machine: a 16 MiB JavaScript file 213 MB, a 7 MB shell file
#: about 0.1 GB.
MAX_BYTES = 16 * 1024 * 1024
#: The same limit for Python, whose syntax tree costs about 110 times the file. Measured: a 9.4 MB
#: Python file peaked at 1.6 GB RSS with a list of every token and at 1.1 GB with the tokens
#: streamed, which is why the limit is lower; a 4 MiB Python file and a 16 MiB shell file in one run
#: peaked at 518 MB, inside the 1.5 GB ceiling.
MAX_PYTHON_BYTES = 4 * 1024 * 1024

BOM = "\ufeff"

#: How a string literal opens: its prefix (``r``, ``u``), then its quote. It always does.
_DOC_OPEN = re.compile(r"""^[^"']*(\"\"\"|'''|"|')""")

# (1-based line, comment key, text). The key is ``LINE_COMMENT`` for a line comment, else it names
# the block comment or docstring the line is in; two lines belong together when they are on
# adjacent lines and have the same key.
Entry = tuple[int, int, str]


@dataclass(frozen=True)
class Trap:
    path: str
    line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Skipped:
    """A file that was not read because it is over the size limit."""

    path: str
    size: int
    limit: int


class _TooLarge(Exception):
    def __init__(self, size: int) -> None:
        super().__init__(size)
        self.size = size


def _read(path: Path, limit: int) -> str | None:
    """The text of a regular, readable, UTF-8 file of at most ``limit`` bytes, else None.

    ``_TooLarge`` for a regular file over ``limit``, so the caller can say it was not read.
    """
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            return None
        if st.st_size > limit:
            raise _TooLarge(st.st_size)
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _clean(text: str, key: int, lang: Lang) -> str:
    """Comment text with exactly one marker's decoration removed, one space between words.

    ``text`` has lost its line marker (``//``, ``#``, ``--``) or block opener already. A doc
    comment marker, ``///`` or ``//!`` or ``##``, is one marker: its extra character goes only when
    it follows the marker with nothing between and is followed by a space or the end. So ``//
    /usr/bin`` and ``--   -1 means``, which have a space first, keep their first character. In a
    block comment, one leading ``*`` goes (the decoration of ``/** ... */``).
    """
    if key == LINE_COMMENT:
        extra = "".join(m[-1] for m in lang.line) + "!"
        if text[:1] and text[0] in extra and (len(text) == 1 or text[1].isspace()):
            text = text[1:]
    else:
        text = text.strip()
        if text.startswith("*") and any(start == "/*" for start, _ in lang.block):
            text = text[1:]
    return " ".join(text.split())


def _chunk_entries(lines: list[str], first: int, lang: Lang) -> list[Entry]:
    found, _why = comment_scan(lines, lang)
    return [
        (first + i, hit[0], _clean(hit[1], hit[0], lang))
        for i, hit in enumerate(found)
        if hit is not None
    ]


def _cut(line: str, start: int, end: int | None) -> str:
    """``line[start:end]`` with offsets in UTF-8 bytes, as ``ast`` counts them."""
    return line.encode("utf-8")[start:end].decode("utf-8", "replace")


def _docstring_text(lines: list[str], stmt: ast.Expr) -> list[str]:
    """The lines of one docstring literal, without its prefix, quotes and what follows it."""
    first, last = stmt.lineno, stmt.end_lineno or stmt.lineno
    chunk = lines[first - 1 : last]
    chunk[-1] = _cut(chunk[-1], 0, stmt.end_col_offset)
    chunk[0] = _cut(chunk[0], stmt.col_offset, None)
    opened = _DOC_OPEN.match(chunk[0])
    assert opened is not None  # a string literal always opens with a quote
    body = [chunk[0][opened.end() :], *chunk[1:]]
    body[-1] = body[-1].removesuffix(opened.group(1))
    return body


def _python_entries(text: str, lines: list[str], lang: Lang) -> list[Entry] | None:
    """Every ``#`` comment on a line of its own and every docstring line, or None if it won't parse.

    The tokenizer is what tells a comment from a ``#`` inside a string, and the syntax tree is what
    tells a docstring from any other string statement.
    """
    found: list[Entry] = []
    try:
        tree = ast.parse(text.encode("utf-8"))
        # Streamed: a list of every token of a large file would hold as much memory as the tree.
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT and not tok.line[: tok.start[1]].strip():
                found.append(
                    (tok.start[0], LINE_COMMENT, _clean(tok.string[1:], LINE_COMMENT, lang))
                )
    except (SyntaxError, tokenize.TokenError, ValueError):
        return None
    for n, stmt in enumerate(docstring_stmts(tree), start=1):
        body = _docstring_text(lines, stmt)
        found.extend((stmt.lineno + i, n, " ".join(line.split())) for i, line in enumerate(body))
    return sorted(found)


def _added_ranges(before: str, after: list[str]) -> list[tuple[int, int]]:
    """The 0-based, half-open ranges of ``after`` that the base does not have."""
    matcher = difflib.SequenceMatcher(a=split_lines(before), b=after, autojunk=False)
    return [
        (j1, j2) for tag, _i1, _i2, j1, j2 in matcher.get_opcodes() if tag in ("insert", "replace")
    ]


def _js_entries(text: str, lang: Lang) -> list[Entry]:
    return [(n, key, _clean(t, key, lang)) for n, key, t in comment_lines(text)]


def _entries_on_added_lines(
    after: str, lines: list[str], added: list[tuple[int, int]], lang: Lang
) -> list[Entry]:
    """Every comment entry on an added line, with adjacent entries of one comment sharing a key.

    Python and JS/TS are scanned whole and masked by the added lines, because an added line can
    sit inside a comment that was already there (a ``Traps:`` line inserted into an owner's
    ``/** ... */``, which the TypeScript printer accepts) and a chunk of added lines alone cannot
    tell. The others are scanned one added chunk at a time with the verifier's chunk scanner, which
    is what the verifier proves for them: an added chunk must be whole comments.
    """
    if lang.verify_method in ("python-ast", "ts-printer"):
        every = (
            _python_entries(after, lines, lang)
            if lang.verify_method == "python-ast"
            else _js_entries(after, lang)
        )
        if every is None:
            return []
        mask = bytearray(len(lines) + 1)
        for j1, j2 in added:
            mask[j1:j2] = b"\x01" * (j2 - j1)
        return [entry for entry in every if mask[entry[0] - 1]]
    # A chunk is one run of added lines, and two runs are never adjacent (an unchanged line sits
    # between them), so a block-comment number repeated in two chunks cannot join them.
    return [e for j1, j2 in added for e in _chunk_entries(lines[j1:j2], j1 + 1, lang)]


def _traps_in(entries: list[Entry], path: str) -> Iterator[Trap]:
    i = 0
    while i < len(entries):
        line, key, body = entries[i]
        if not body.startswith(TRAPS_LABEL):
            i += 1
            continue
        parts = [body[len(TRAPS_LABEL) :].strip()]
        i += 1
        while i < len(entries):
            next_line, next_key, next_body = entries[i]
            if (
                next_line != entries[i - 1][0] + 1
                or next_key != key
                or not next_body
                or _ANY_LABEL.match(next_body)
            ):
                break
            parts.append(next_body)
            i += 1
        text = " ".join(part for part in parts if part)
        if text:
            yield Trap(path, line, text)


def _file_traps(
    top: Path, sha: str | None, rel: str, skipped: list[Skipped] | None
) -> Iterator[Trap]:
    lang = detect(rel)
    if lang is None:
        return
    limit = MAX_PYTHON_BYTES if lang.verify_method == "python-ast" else MAX_BYTES
    try:
        after = _read(top / rel, limit)
    except _TooLarge as big:
        if skipped is not None:
            skipped.append(Skipped(rel, big.size, limit))
        return
    if after is None or TRAPS_LABEL not in after:
        return
    # Without the mark, on both sides, a comment on line 1 is still the first thing on its line.
    after = after.removeprefix(BOM)
    before = ""  # no base: every line of the file counts as added
    if sha:
        base_size = git_size(top, sha, rel)  # the base is read whole too, so it has the same cap
        if base_size is not None and base_size > limit:
            if skipped is not None:
                skipped.append(Skipped(rel, base_size, limit))
            return
        before = (git_show(top, sha, rel) or "").removeprefix(BOM)
    lines = split_lines(after)
    added = _added_ranges(before, lines)
    yield from _traps_in(_entries_on_added_lines(after, lines, added, lang), rel)


def iter_traps(top: Path, sha: str | None, skipped: list[Skipped] | None = None) -> Iterator[Trap]:
    """The traps in the work tree at ``top``, one file at a time, in path order.

    With a commit ``sha``, the ones added to it (the files ``verify --changed`` would check). With
    ``sha`` None, every ``Traps:`` comment in the tracked, non-exempt files. ``top`` is the top
    level of the work tree and ``sha`` a commit that exists: ``harvest_traps`` checks both. A file
    over its size limit is appended to ``skipped`` when a list is given.
    """
    for rel in changed_files(top, sha) if sha else tracked_files(top):
        yield from _file_traps(top, sha, rel, skipped)


def harvest_traps(
    repo: Path, before: str | None = None, skipped: list[Skipped] | None = None
) -> list[Trap]:
    """Every ``Traps:`` label added since ``before``, sorted by path then line.

    With ``before`` None, every ``Traps:`` comment in the tracked files at the work tree, the
    owner's included: a ``--phase docs`` run has no base to compare with, because its commenters
    ran in an earlier run. An empty ``before`` is an error, not "no base", so an unset variable
    cannot turn a narrow question into a whole-tree one. Files over the size limit go to
    ``skipped``.

    ``InputError`` when ``repo`` is not the top level of a work tree or ``before`` does not name a
    commit; ``GitError`` when git fails while listing files.
    """
    top = _top(repo)
    sha = None if before is None else _resolve_commit(top, before, "--before")
    try:
        return sorted(iter_traps(top, sha, skipped), key=lambda t: (t.path, t.line))
    except subprocess.CalledProcessError as exc:
        why = (exc.stderr or b"").decode("utf-8", "replace").strip() or str(exc)
        raise GitError(f"git failed while listing the files to read: {why}") from exc
