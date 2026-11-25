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
file; each file's own state is freed when its traps are returned. Within a file nothing is kept per
comment line: entries are produced lazily and only a ``Traps:`` line and the lines after it are
held, up to ``MAX_TRAP_CHARS`` characters, after which the text is cut and ends in " ...". The
added lines come from difflib, as the verifier finds them, unless the file is big or full of equal
lines (``MAX_DIFF_LINES``, ``MAX_DIFF_PAIRS``), where difflib does work in proportion to the
pairs of equal lines and git's diff does not; with no base no diff is run. A file over
``MAX_BYTES`` (``MAX_PYTHON_BYTES`` for Python), or whose version at ``before`` is, is not read
and is reported in the ``skipped`` list. A file that is not UTF-8, a symlink,
anything that is not a regular file, and a Python file that does not parse (the verifier would
have failed it) are skipped without a report: none of them can hold a trap the skill wrote.
"""

from __future__ import annotations

import ast
import difflib
import heapq
import io
import os
import re
import stat
import subprocess
import tempfile
import tokenize
from bisect import bisect_right
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
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
    docstring_stmts,
    git_show,
    git_size,
    iter_comment_scan,
    tracked_files,
)

#: The labels comment-standards.md has headers use. A trap ends where the next one starts.
HEADER_LABELS = ("Role", "Used by", "Inputs", "Outputs", "Side effects", "Invariants", "Traps")

TRAPS_LABEL = "Traps:"
_ANY_LABEL = re.compile("(?:" + "|".join(re.escape(name) for name in HEADER_LABELS) + "):")

#: A file larger than this (or whose base version is) is not read. Peak RSS of the real CLI on this
#: machine for a file of that size (a header and then nothing but comment lines, the worst case
#: for a scanner), alone: 16 MiB of JavaScript 105 MB with ``--before`` and 59 MB without; 16 MiB of
#: shell 317 MB, mostly its list of lines. All three probes below in one run took 570 MB, so the
#: files do not add up: each file's memory is freed before the next is read.
MAX_BYTES = 16 * 1024 * 1024
#: The same limit for Python, whose syntax tree costs about 110 times the file. A 4 MiB Python file
#: of code peaked at 486 MB (a 9.4 MB one at 1.1 GB, and 1.6 GB while the tokens were kept in a
#: list), which is why Python has the lower limit. Together with the 16 MiB JavaScript and shell
#: files the whole run peaked at 570 MB, inside the 1.5 GB ceiling.
MAX_PYTHON_BYTES = 4 * 1024 * 1024
#: A trap's text is cut here and ends in " ...". A trap is one or two sentences; a header that
#: runs on for thousands of comment lines is not one, and its text would be the file.
MAX_TRAP_CHARS = 2000

#: Above this many lines, both sides together, git finds the added lines, not difflib.
MAX_DIFF_LINES = 200_000
#: difflib (as the verifier calls it, without its popular-line shortcut) does work in proportion to
#: the pairs of equal lines between the two sides: about 50 ns each on this machine, so 25 million
#: pairs is 1.3 s and 400 million is 25 s. A file of identical comment lines against its base has
#: that many pairs and ran over 150 s. Above this many pairs git finds the added lines instead.
MAX_DIFF_PAIRS = 25_000_000

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


def _chunk_entries(lines: list[str], first: int, lang: Lang) -> Iterator[Entry]:
    for i, hit in enumerate(iter_comment_scan(lines, lang)):
        if hit is not None:
            yield (first + i, hit[0], _clean(hit[1], hit[0], lang))


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


def _python_comments(text: str, lang: Lang) -> Iterator[Entry]:
    """Every ``#`` comment on a line of its own, from the tokenizer, in line order."""
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT and not tok.line[: tok.start[1]].strip():
                yield (tok.start[0], LINE_COMMENT, _clean(tok.string[1:], LINE_COMMENT, lang))
    except (SyntaxError, tokenize.TokenError, ValueError):
        return  # the parser accepted the file, so this is rare: keep what was read


def _python_entries(text: str, lines: list[str], lang: Lang) -> Iterator[Entry]:
    """Every ``#`` comment on a line of its own and every docstring line, in line order.

    Nothing if the file does not parse. The tokenizer is what tells a comment from a ``#`` inside
    a string, and the syntax tree is what tells a docstring from any other string statement.
    """
    try:
        tree = ast.parse(text.encode("utf-8"))
    except (SyntaxError, ValueError):
        return
    stmts = sorted(docstring_stmts(tree), key=lambda stmt: (stmt.lineno, stmt.col_offset))
    del tree  # the tree is most of the memory (about 110 times the file) and is not read again
    docstrings = (
        (stmt.lineno + i, n, " ".join(line.split()))
        for n, stmt in enumerate(stmts, start=1)
        for i, line in enumerate(_docstring_text(lines, stmt))
    )
    yield from heapq.merge(_python_comments(text, lang), docstrings)


def _js_entries(text: str, lang: Lang) -> Iterator[Entry]:
    for n, key, line in comment_lines(text):
        yield (n, key, _clean(line, key, lang))


def _line_count(text: str) -> int:
    """How many lines ``split_lines`` would make of ``text``, without making them."""
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0)


def _difflib_ranges(before: list[str], after: list[str]) -> list[tuple[int, int]]:
    """The 0-based, half-open ranges of ``after`` that ``before`` does not have."""
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    return [
        (j1, j2) for tag, _i1, _i2, j1, j2 in matcher.get_opcodes() if tag in ("insert", "replace")
    ]


_HUNK = re.compile(rb"^@@ -[0-9]+(?:,[0-9]+)? \+([0-9]+)(?:,([0-9]+))? @@")


def _git_added_ranges(top: Path, sha: str, rel: str) -> list[tuple[int, int]]:
    """The same ranges from ``git diff -U0`` of the work tree against ``sha``.

    Git's diff does not slow down on many equal lines, and nothing of the file is held here: the
    output is read a line at a time and only the ``@@`` headers are kept. A file with a diff driver
    or an attribute that says binary is still diffed as text. ``GitError`` if git fails.

    For an insert the ranges are difflib's, with one exception: when the base's last line has no
    newline and lines follow it, git calls that line changed (``c`` and ``c`` + newline differ),
    which difflib does not. A trap on that one line would be listed as added.
    """
    argv = ["git", "--literal-pathspecs", "-C", str(top), "diff", "-U0", "--inter-hunk-context=0"]
    argv += ["--no-ext-diff"]
    argv += ["--no-textconv", "--no-color", "--no-renames", "--text", sha, "--", rel]
    found: list[tuple[int, int]] = []
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=err)
        assert proc.stdout is not None
        try:
            for raw in proc.stdout:
                hunk = _HUNK.match(raw)
                if hunk:
                    start = int(hunk.group(1)) - 1
                    count = int(hunk.group(2)) if hunk.group(2) is not None else 1
                    if count:  # a hunk with no added lines only deleted some
                        found.append((start, start + count))
        finally:
            proc.stdout.close()
            code = proc.wait()
        if code != 0:
            err.seek(0)
            why = err.read().decode("utf-8", "replace").strip()
            raise GitError(f"git diff failed with exit {code} for {rel}: {why}")
    return found


def _matching_pairs(before: list[str], after: list[str]) -> int:
    """How many pairs of equal lines there are between the two sides: difflib's cost."""
    counts = Counter(after)
    return sum(n * counts[line] for line, n in Counter(before).items() if line in counts)


def _added_ranges(
    top: Path, sha: str | None, rel: str, before: str, after: str
) -> list[tuple[int, int]]:
    """The 0-based, half-open line ranges of ``after`` that ``before`` does not have.

    ``before`` empty means there is nothing to compare with (no ``sha``, a new file, or an empty
    base), so every line is new and no diff is run. Otherwise difflib, which is what the verifier
    uses, unless the files are big or full of equal lines (``MAX_DIFF_LINES``, ``MAX_DIFF_PAIRS``),
    where git finds the same ranges for an insert and does not slow down.
    """
    new_lines = _line_count(after)
    if not before:
        return [(0, new_lines)] if new_lines else []
    assert sha is not None  # a base exists only when there is a commit to read it from
    old_lines = _line_count(before)
    if old_lines + new_lines > MAX_DIFF_LINES:
        return _git_added_ranges(top, sha, rel)
    old, new = split_lines(before), split_lines(after)
    if old_lines * new_lines > MAX_DIFF_PAIRS and _matching_pairs(old, new) > MAX_DIFF_PAIRS:
        return _git_added_ranges(top, sha, rel)
    return _difflib_ranges(old, new)


def _is_added(added: list[tuple[int, int]]) -> Callable[[int], bool]:
    """A test for "is this 1-based line in one of the sorted, disjoint 0-based ranges"."""
    starts = [start for start, _ in added]

    def test(line: int) -> bool:
        i = bisect_right(starts, line - 1) - 1
        return i >= 0 and line - 1 < added[i][1]

    return test


def _entries_on_added_lines(
    after: str, added: list[tuple[int, int]], lang: Lang
) -> Iterator[Entry]:
    """Every comment entry on an added line, with adjacent entries of one comment sharing a key.

    Python and JS/TS are scanned whole and masked by the added lines, because an added line can
    sit inside a comment that was already there (a ``Traps:`` line inserted into an owner's
    ``/** ... */``, which the TypeScript printer accepts) and a chunk of added lines alone cannot
    tell. The others are scanned one added chunk at a time with the verifier's chunk scanner, which
    is what the verifier proves for them: an added chunk must be whole comments.

    A generator, and a chunk is scanned lazily too: no entry is kept once it is read.
    """
    if lang.verify_method == "python-ast":
        is_added = _is_added(added)
        yield from (e for e in _python_entries(after, split_lines(after), lang) if is_added(e[0]))
    elif lang.verify_method == "ts-printer":
        is_added = _is_added(added)
        yield from (e for e in _js_entries(after, lang) if is_added(e[0]))
    else:
        lines = split_lines(after)
        # A chunk is one run of added lines, and two runs are never adjacent (an unchanged line
        # sits between them), so a block-comment number repeated in two chunks cannot join them.
        for j1, j2 in added:
            yield from _chunk_entries(lines[j1:j2], j1 + 1, lang)


def _finish(path: str, line: int, parts: list[str], cut: bool) -> Trap | None:
    text = " ".join(part for part in parts if part)
    if cut or len(text) > MAX_TRAP_CHARS:
        text = text[:MAX_TRAP_CHARS].rstrip() + " ..."
    return Trap(path, line, text) if text else None


def _traps_in(entries: Iterable[Entry], path: str) -> Iterator[Trap]:
    """One ``Trap`` per ``Traps:`` entry, read from ``entries`` one at a time.

    A trap goes on over the entries after it that are on the next line, in the same comment, not
    empty and not another header label. Once its text reaches ``MAX_TRAP_CHARS`` the rest of its
    lines are read and dropped, and the text ends in " ...".
    """
    line = key = last = size = 0
    parts: list[str] = []
    cut = collecting = False
    for n, k, body in entries:
        if collecting:
            if n == last + 1 and k == key and body and not _ANY_LABEL.match(body):
                last = n
                if size < MAX_TRAP_CHARS:
                    parts.append(body)
                    size += len(body) + 1
                else:
                    cut = True
                continue
            collecting = False
            trap = _finish(path, line, parts, cut)
            if trap:
                yield trap
        if body.startswith(TRAPS_LABEL):
            first = body[len(TRAPS_LABEL) :].strip()
            line, key, last, size, parts, cut, collecting = (
                n,
                k,
                n,
                len(first),
                [first],
                False,
                True,
            )
    if collecting:
        trap = _finish(path, line, parts, cut)
        if trap:
            yield trap


def _file_traps(top: Path, sha: str | None, rel: str, skipped: list[Skipped] | None) -> list[Trap]:
    """The traps of one file. A list, not a generator: everything else this builds is freed on
    return, before the next file is read."""
    lang = detect(rel)
    if lang is None:
        return []
    limit = MAX_PYTHON_BYTES if lang.verify_method == "python-ast" else MAX_BYTES
    try:
        after = _read(top / rel, limit)
    except _TooLarge as big:
        if skipped is not None:
            skipped.append(Skipped(rel, big.size, limit))
        return []
    if after is None or TRAPS_LABEL not in after:
        return []
    # Without the mark, on both sides, a comment on line 1 is still the first thing on its line.
    after = after.removeprefix(BOM)
    before = ""  # no base: every line of the file counts as added
    if sha:
        base_size = git_size(top, sha, rel)  # the base is read whole too, so it has the same cap
        if base_size is not None and base_size > limit:
            if skipped is not None:
                skipped.append(Skipped(rel, base_size, limit))
            return []
        before = (git_show(top, sha, rel) or "").removeprefix(BOM)
    added = _added_ranges(top, sha, rel, before, after)
    del before  # not needed again: the scan below holds the file once, not the base too
    return list(_traps_in(_entries_on_added_lines(after, added, lang), rel))


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
