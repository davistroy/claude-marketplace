"""Harvest the ``Traps:`` labels that a branch added to comments.

The Synthesizer writes ``agent_notes.traps`` before any commenter has read a file. The commenters
then find more traps and write them as ``Traps:`` lines in file headers (comment-standards.md),
and nothing carried those back into the model, AGENTS.md or the explorer. ``traps`` lists them so
the orchestrator can fold the ones that matter beyond their own file into the model.

``harvest_traps(repo, before)`` compares the work tree with the commit ``before``, picks files the
way ``verify --changed`` does (``verify.changed_files``: everything but Markdown and the skill's
own explorer output), and returns one ``Trap`` for each ``Traps:`` label on a line the branch
added. A label that existed at ``before`` is the owner's: the analysts already read it in the
source. Only lines of a comment count, found with the same classifier the verifier uses
(``verify.comment_scan`` and, for Python, the docstring rule of ``verify.docstring_stmts`` plus
the tokenizer, which tells a ``#`` line from a ``#`` inside a string). A label inside code
(``print("Traps: x")``) is not a trap.

What a trap's text is: the label's text, then the lines after it that are comment lines of the
same comment (the same ``//`` or ``#`` run, the same block comment, the same docstring), were
added too, are not blank, and do not start another header label. Comment markers, a block
comment's leading ``*``, and runs of whitespace are removed, and the lines are joined with one
space. Lines are numbered as an editor shows them (``remap.split_lines``): a form feed does not
start a line.

Without ``before``, the files are every tracked, non-exempt one and every ``Traps:`` comment in
them counts, the owner's included. A ``--phase docs`` run needs this: its commenters ran in an
earlier run, so no base separates their traps from the owner's.

Files are read one at a time and the result is a generator underneath, so memory stays at one
file. A file over ``MAX_BYTES`` (``MAX_PYTHON_BYTES`` for Python) is not read and is reported in
the ``skipped`` list. One that is not UTF-8, a symlink, anything that is not a regular file, and
a Python file that does not parse (the verifier would have failed it) are skipped without a
report: none of them can hold a trap the skill wrote.
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
from .languages import Lang, detect
from .remap import split_lines
from .verify import (
    LINE_COMMENT,
    changed_files,
    comment_scan,
    docstring_stmts,
    git_show,
    tracked_files,
)

#: The labels comment-standards.md has headers use. A trap ends where the next one starts.
HEADER_LABELS = ("Role", "Used by", "Inputs", "Outputs", "Side effects", "Invariants", "Traps")

TRAPS_LABEL = "Traps:"
_ANY_LABEL = re.compile("(?:" + "|".join(re.escape(name) for name in HEADER_LABELS) + "):")

#: A file larger than this is skipped, so memory stays bounded at one file's worth. Measured on a
#: 9 MB Python file: its syntax tree peaks near 1 GB, a shell file of 7 MB needs about 0.1 GB.
MAX_BYTES = 16 * 1024 * 1024
#: The same limit for Python, whose syntax tree is what costs the memory (about 110 times the
#: file). 4 MiB peaks near 0.5 GB, inside the 1.5 GB ceiling.
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
    """Comment text without its decoration (``//!``, ``##``, a block's ``*``), one space apart."""
    text = text.strip()
    if key == LINE_COMMENT:
        # What a line comment repeats after its marker: `///`, `//!`, `##`, `---`, `;;`.
        text = text.lstrip("".join(m[-1] for m in lang.line) + "!")
    elif any(start == "/*" for start, _ in lang.block):
        text = text.lstrip("*")
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


def _entries_on_added_lines(
    after: str, lines: list[str], added: list[tuple[int, int]], lang: Lang
) -> list[Entry]:
    if lang.verify_method == "python-ast":
        every = _python_entries(after, lines, lang)
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
    # No base: every line of the file counts as added.
    before = (git_show(top, sha, rel) or "").removeprefix(BOM) if sha else ""
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
