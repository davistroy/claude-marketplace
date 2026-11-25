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

Files are read one at a time and the result is a generator underneath, so memory stays at one
file. A file over ``MAX_BYTES`` (``MAX_PYTHON_BYTES`` for Python), one that is not UTF-8, a
symlink, anything that is not a regular file, and a Python file that does not parse (the verifier
would have failed it) are skipped.
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
from .verify import LINE_COMMENT, changed_files, comment_scan, docstring_stmts, git_show

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


def _read(path: Path, limit: int) -> str | None:
    """The text of a regular, readable, UTF-8 file of at most ``limit`` bytes, else None."""
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
            return None
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


def _file_traps(top: Path, sha: str, rel: str) -> Iterator[Trap]:
    lang = detect(rel)
    if lang is None:
        return
    after = _read(top / rel, MAX_PYTHON_BYTES if lang.verify_method == "python-ast" else MAX_BYTES)
    if after is None or TRAPS_LABEL not in after:
        return
    # Without the mark, on both sides, a comment on line 1 is still the first thing on its line.
    after = after.removeprefix(BOM)
    before = (git_show(top, sha, rel) or "").removeprefix(BOM)
    lines = split_lines(after)
    added = _added_ranges(before, lines)
    yield from _traps_in(_entries_on_added_lines(after, lines, added, lang), rel)


def iter_traps(top: Path, sha: str) -> Iterator[Trap]:
    """The traps the work tree at ``top`` added to ``sha``, one file at a time, in path order.

    ``top`` is the top level of the work tree and ``sha`` a commit that exists: ``harvest_traps``
    checks both.
    """
    for rel in changed_files(top, sha):
        yield from _file_traps(top, sha, rel)


def harvest_traps(repo: Path, before: str) -> list[Trap]:
    """Every ``Traps:`` label added since ``before``, sorted by path then line.

    ``InputError`` when ``repo`` is not the top level of a work tree or ``before`` does not name a
    commit; ``GitError`` when git fails while listing the changes.
    """
    top = _top(repo)
    sha = _resolve_commit(top, before, "--before")
    try:
        return sorted(iter_traps(top, sha), key=lambda t: (t.path, t.line))
    except subprocess.CalledProcessError as exc:
        why = (exc.stderr or b"").decode("utf-8", "replace").strip() or str(exc)
        raise GitError(f"git failed while listing the branch's changes: {why}") from exc
