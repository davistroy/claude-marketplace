"""Write generated text into docs without touching the human-written parts.

Generated text always lives between a start and an end marker, which are
invisible HTML comments in rendered Markdown. A later run replaces only what
is between the markers, so a person's edits elsewhere in the file survive.
"""

from __future__ import annotations

import re
from pathlib import Path

from .fsutil import write_bytes_atomic

_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")


def marker_pair(name: str) -> tuple[str, str]:
    if not _NAME.fullmatch(name):
        raise ValueError(f"section name {name!r} must match {_NAME.pattern}")
    return f"<!-- document-repo:start:{name} -->", f"<!-- document-repo:end:{name} -->"


def upsert_section(text: str, name: str, body: str) -> str:
    """Replace section ``name`` in ``text``, or append it when absent.

    The file's own line ending is used for the generated lines: CRLF when the text contains
    CRLF, LF otherwise. Existing lines outside the markers are never rewritten.
    """
    start, end = marker_pair(name)
    eol = "\r\n" if "\r\n" in text else "\n"
    generated = body.replace("\r\n", "\n").strip().replace("\n", eol)
    block = f"{start}{eol}{generated}{eol}{end}"
    count = text.count(start)
    if count > 1:
        raise ValueError(f"start marker for {name!r} appears more than once")
    if count == 0:
        if end in text:
            raise ValueError(f"end marker for {name!r} without a start marker")
        if not text.strip():
            return block + eol
        return text.rstrip("\r\n") + eol + eol + block + eol
    s = text.index(start)
    e = text.find(end, s)
    if e == -1:
        raise ValueError(f"start marker for {name!r} has no end marker")
    return text[:s] + block + text[e + len(end) :]


def upsert_file(path: Path, name: str, body: str) -> None:
    """Upsert section ``name`` in the file at ``path``, creating the file if needed.

    The file is read as bytes and decoded as UTF-8 without translating newlines, so CRLF lines
    outside the markers come back exactly as they were. The write is atomic: a crash leaves
    either the old file or the new one.
    """
    raw = path.read_bytes() if path.exists() else b""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: not valid UTF-8 ({exc.reason})") from exc
    out = upsert_section(text, name, body)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_bytes_atomic(path, out.encode("utf-8"))
