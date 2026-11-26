"""Write generated text into docs without touching the human-written parts.

Generated text always lives between a start and an end marker, which are
invisible HTML comments in rendered Markdown. A later run replaces only what
is between the markers, so a person's edits elsewhere in the file survive.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

from .fsutil import write_bytes_atomic

_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
_BREAK = re.compile(r"\r\n|\r|\n")
# Any marker of this tool, whatever its section name, once the line has been stripped.
_MARKER_LINE = re.compile(r"<!-- document-repo:(start|end):(\S+) -->")
# A code fence opens with three or more backticks or tildes. The info string of a backtick
# fence cannot hold a backtick; otherwise the line is inline code, not a fence.
_FENCE = re.compile(r"(`{3,}|~{3,})(.*)")
_BOM = "﻿"
# What counts as blank around a line. Deliberately not str.strip(): a no-break space is text.
_SPACE = " \t\f\v"
_MARKER_FRAGMENTS = ("document-repo:start:", "document-repo:end:")


class _Marker(NamedTuple):
    kind: str  # "start" or "end"
    name: str
    offset: int  # where the marker text begins in the file text
    line: int  # 1-based line number, for error messages
    text: str


def marker_pair(name: str) -> tuple[str, str]:
    if not _NAME.fullmatch(name):
        raise ValueError(f"section name {name!r} must match {_NAME.pattern}")
    return f"<!-- document-repo:start:{name} -->", f"<!-- document-repo:end:{name} -->"


def upsert_section(text: str, name: str, body: str) -> str:
    """Replace section ``name`` in ``text``, or append it when absent.

    Text outside the markers is never rewritten: the bytes before the start marker and after
    the end marker come back exactly as they were, including line endings, trailing blank lines
    and a leading BOM. The one exception is a file that is empty or only spaces and tabs with no
    line break; that has nothing to keep, and the section is written alone.

    A marker counts only when its line, stripped of surrounding spaces and tabs, is exactly the
    marker, and the line is not inside a fenced code block (``` or ~~~; a fence closes on the
    same character, at least as many of it, and nothing else but whitespace). So a README that
    shows the markers in an example, or mentions one in a sentence, is not mistaken for a section.
    An unclosed fence raises ``ValueError``, because where the sections lie is then ambiguous.

    Appending keeps ``text`` verbatim. If it does not end with a line break one is added, then
    one blank line unless it already ends with one, then the section and a final line break.

    Generated lines use the file's line ending: that of its last line break, ``\\n`` if it has
    none. The body is cut to its content: a leading BOM and leading and trailing blank lines are
    dropped, but indentation is kept, so a body that opens with an indented code line stays
    intact. Line breaks in the body (CRLF, CR or LF) become the file's line ending.

    Raises ``ValueError`` for a bad name, a body that contains a marker (it would corrupt the
    file on the next run), a duplicate start marker, a start without an end, an end without a
    start, and a section that overlaps or nests with another marker.
    """
    start, end = marker_pair(name)
    if any(fragment in body for fragment in _MARKER_FRAGMENTS):
        raise ValueError(
            f"body contains a document-repo marker ({' or '.join(_MARKER_FRAGMENTS)}); "
            "a section body must not hold markers"
        )
    markers = _markers(text)
    eol = _file_eol(text)
    block = f"{start}{eol}{eol.join(_body_lines(body))}{eol}{end}"
    starts = [m for m in markers if m.kind == "start" and m.name == name]
    if len(starts) > 1:
        raise ValueError(f"start marker for {name!r} appears more than once")
    if not starts:
        if any(m.kind == "end" and m.name == name for m in markers):
            raise ValueError(f"end marker for {name!r} without a start marker")
        return _append(text, block, eol)
    opening = starts[0]
    closing = next(
        (m for m in markers if m.kind == "end" and m.name == name and m.offset > opening.offset),
        None,
    )
    if closing is None:
        raise ValueError(f"start marker for {name!r} has no end marker")
    for other in markers:
        if opening.offset < other.offset < closing.offset:
            raise ValueError(
                f"section {name!r} contains {other.text} on line {other.line}; "
                "sections must not overlap or nest"
            )
    return text[: opening.offset] + block + text[closing.offset + len(end) :]


def _lines(text: str, pos: int) -> Iterator[tuple[int, str]]:
    """Yield ``(offset, content)`` for each line from ``pos``, line break excluded."""
    while pos < len(text):
        brk = _BREAK.search(text, pos)
        stop = brk.start() if brk else len(text)
        yield pos, text[pos:stop]
        pos = brk.end() if brk else len(text)


def _markers(text: str) -> list[_Marker]:
    """Find the marker lines that are outside fenced code, in file order."""
    found: list[_Marker] = []
    fence: tuple[str, int, int] | None = None  # (character, length, line it opened on)
    # A BOM belongs to the file, not to its first line.
    first = len(_BOM) if text.startswith(_BOM) else 0
    for lineno, (offset, line) in enumerate(_lines(text, first), 1):
        stripped = line.strip(_SPACE)
        if fence is not None:
            char, size, _ = fence
            if len(stripped) >= size and stripped == char * len(stripped):
                fence = None
            continue
        opener = _FENCE.fullmatch(stripped)
        if opener and not (opener[1][0] == "`" and "`" in opener[2]):
            fence = (opener[1][0], len(opener[1]), lineno)
            continue
        marker = _MARKER_LINE.fullmatch(stripped)
        if marker:
            indent = len(line) - len(line.lstrip(_SPACE))
            found.append(_Marker(marker[1], marker[2], offset + indent, lineno, stripped))
    if fence is not None:
        raise ValueError(
            f"the code fence opened on line {fence[2]} is never closed, "
            "so the sections in this file cannot be told apart from examples"
        )
    return found


def _file_eol(text: str) -> str:
    """The line ending of the file's last line break; ``\\n`` when it has none."""
    last = max(text.rfind("\n"), text.rfind("\r"))
    if last == -1:
        return "\n"
    if text[last] == "\n":
        return "\r\n" if text[last - 1 : last] == "\r" else "\n"
    return "\r"


def _body_lines(body: str) -> list[str]:
    """The body's lines without a BOM or leading and trailing blank lines; indent is kept."""
    lines = _BREAK.split(body.lstrip(_BOM))
    content = [i for i, line in enumerate(lines) if line.strip(_SPACE)]
    return lines[content[0] : content[-1] + 1] if content else []


def _append(text: str, block: str, eol: str) -> str:
    """Add ``block`` after ``text``, which is kept byte for byte."""
    bom = _BOM if text.startswith(_BOM) else ""
    rest = text[len(bom) :]
    if not rest.strip(_SPACE):
        # Empty, or spaces and tabs with no line break: nothing worth keeping.
        return f"{bom}{block}{eol}"
    parts = _BREAK.split(rest)
    unterminated = parts[-1]
    out = text
    if unterminated:
        out += eol
        last_line = unterminated
    else:
        last_line = parts[-2]
    if last_line.strip(_SPACE):
        out += eol
    return f"{out}{block}{eol}"


def _is_under(path: str, top: str) -> bool:
    return os.path.commonpath([path, top]) == top


def _lexical_top(path: Path) -> Path:
    """The work-tree top that lexically holds ``path``: the default for ``upsert_file``.

    The walk goes up the path as written, never through a link: the first directory that holds
    a ``.git`` entry and is not itself a symlink is the candidate, and git must agree it is a top
    level. A candidate reached through a symlink (``repo/a -> ../other`` with a work tree at
    ``other/sub``) is refused: an enclosing work tree whose real path does not hold the
    candidate's real path means a link left it, so the caller must say which repo it means.
    """
    from .verify import toplevel

    found: Path | None = None
    d = Path(os.path.abspath(path)).parent
    while True:
        if os.path.lexists(d / ".git") and not os.path.islink(d):
            if found is None:
                top = toplevel(d)
                if top is None or not os.path.samefile(top, d):
                    raise ValueError(f"{path}: {d} holds .git but is not a work-tree top level")
                found = d
            elif not _is_under(os.path.realpath(found), os.path.realpath(d)):
                raise ValueError(
                    f"{path}: the work tree at {found} is reached through a symlink out of "
                    f"{d}; pass --repo to name the repository"
                )
        if d.parent == d:
            break
        d = d.parent
    if found is None:
        raise ValueError(f"{path}: not inside a git work tree; pass --repo")
    return found


def _explicit_top(repo: Path) -> Path:
    from .verify import toplevel

    top = toplevel(repo)
    if top is None or not os.path.samefile(top, repo):
        raise ValueError(f"--repo {repo} is not the top level of a git work tree")
    return Path(os.path.abspath(repo))


def contained_target(path: Path, repo: Path | None = None) -> Path:
    """The real file ``upsert_file`` writes for ``path``; ``ValueError`` when it may not (H-SYM).

    Symlinks are resolved, so ``CLAUDE.md -> AGENTS.md`` names ``AGENTS.md``. The resolved file
    must lie inside the real path of the work tree (``repo``, or the one that lexically holds
    ``path``, see ``_lexical_top``) and outside its ``.git`` directory. A dangling symlink
    anywhere on the way is refused rather than having its target created. A write outside the
    work tree is invisible to every git check and cannot be undone through git.
    """
    top = _explicit_top(repo) if repo is not None else _lexical_top(path)
    lexical = Path(os.path.abspath(path))
    rel = os.path.relpath(lexical, top)
    if rel == os.curdir or rel.split(os.sep)[0] == os.pardir:
        raise ValueError(f"{path} is not under the repository {top}")
    step = top
    for part in Path(rel).parts:
        step = step / part
        if os.path.islink(step) and not os.path.exists(step):
            raise ValueError(f"{path}: {step} is a dangling symlink; refusing to create its target")
    real_top = os.path.realpath(top)
    target = os.path.realpath(lexical)
    if target == real_top or not _is_under(target, real_top):
        raise ValueError(f"{path} resolves to {target}, outside the work tree {real_top}")
    if ".git" in Path(os.path.relpath(target, real_top)).parts:
        raise ValueError(f"{path} resolves to {target}, inside the .git directory")
    return Path(target)


def upsert_file(path: Path, name: str, body: str, repo: Path | None = None) -> None:
    """Upsert section ``name`` in the file at ``path``, creating the file if needed.

    A symlink is written through when it stays in the work tree: the path is resolved first, so
    ``CLAUDE.md -> AGENTS.md`` updates ``AGENTS.md`` and the link stays a link. A path that
    resolves outside the work tree (``repo``, or the one that holds ``path``), into ``.git``, or
    through a dangling link raises ``ValueError`` and writes nothing (``contained_target``).

    The file is read as bytes and decoded as UTF-8 without translating newlines, so CRLF lines
    outside the markers come back exactly as they were. The write is atomic: a crash leaves
    either the old file or the new one.
    """
    target = contained_target(path, repo)
    raw = target.read_bytes() if target.exists() else b""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: not valid UTF-8 ({exc.reason})") from exc
    out = upsert_section(text, name, body)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_bytes_atomic(target, out.encode("utf-8"))
