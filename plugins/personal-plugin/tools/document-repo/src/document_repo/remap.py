"""Move model line numbers to a newer commit.

Comments inserted in Phase 2 push code down. A line_map built from the analysed commit and the
commented commit says where each old line now lives. Comment-only edits are pure insertions, so
the mapping is exact; for anything else it is a best effort, and the caller gets a warning.

Lines are counted the way git and editors count them: a line ends at "\\n" (a CRLF ending loses
its "\\r"), and nothing else. ``str.splitlines`` also breaks at a form feed, NEL and U+2028, which
would put the model's line numbers (taken from the file as an editor shows it) out of step.
"""

from __future__ import annotations

import bisect
import copy
import difflib
import json
import subprocess
from pathlib import Path
from typing import Any

from .fsutil import write_bytes_atomic
from .schema import MAX_SNIPPET_LINES, validate
from .verify import git_show, toplevel


class RemapError(ValueError):
    """An expected failure caused by the input: a bad model, a repo or ref that is not usable.

    The CLI reports these with exit 2. Any other ValueError is a bug and is left to propagate.
    """


def _split_lines(text: str) -> list[str]:
    """Lines of ``text`` as an editor numbers them, without their line endings."""
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return [line[:-1] if line.endswith("\r") else line for line in lines]


def _insertion_map(before: list[str], after: list[str]) -> list[int] | None:
    """Where each ``before`` line sits if ``after`` only adds lines; None if it does more.

    Each line takes the first equal line at or after the previous match, so a code line can
    never be paired with a look-alike elsewhere in the file (a longest-block diff can, when a body
    repeats and only one copy was commented). When an inserted line equals an old line, the
    earliest equal line wins. Cost is O(n log n).
    """
    spots: dict[str, list[int]] = {}
    for j, text in enumerate(after):
        spots.setdefault(text, []).append(j)
    mapping: list[int] = []
    cursor = 0
    for text in before:
        candidates = spots.get(text, [])
        k = bisect.bisect_left(candidates, cursor)
        if k == len(candidates):
            return None
        cursor = candidates[k] + 1
        mapping.append(cursor)
    return mapping


def _diff_map(before: list[str], after: list[str]) -> tuple[list[int], bool]:
    """The line map, and whether it is exact (``after`` only inserted lines)."""
    exact = _insertion_map(before, after)
    if exact is not None:
        return exact, True
    mapping = [1] * len(before)
    last = max(len(after), 1)
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        for k in range(i1, i2):
            if tag == "equal":
                mapping[k] = j1 + (k - i1) + 1
            else:
                mapping[k] = min(j1 + (k - i1), max(j1, j2 - 1)) + 1
            mapping[k] = min(max(mapping[k], 1), last)
    return mapping, False


def line_map(before: list[str], after: list[str]) -> list[int]:
    """Index i holds the 1-based line in ``after`` for line i+1 of ``before``."""
    return _diff_map(before, after)[0]


def _commit(repo: Path, ref: str, unknown: str) -> str:
    """The full sha of the commit ``ref`` names (a tag is peeled), or RemapError(``unknown``)."""
    if ref.startswith("-"):  # never let a ref be read as an option
        raise RemapError(unknown)
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RemapError(unknown)
    return proc.stdout.decode("ascii", "replace").strip()


def remap_model(
    model: dict[str, Any], repo: Path, new_ref: str
) -> tuple[dict[str, Any], list[str]]:
    """Return a copy of ``model`` whose line numbers refer to ``new_ref``, and any warnings.

    File paths in the model are relative to the top of the work tree that contains ``repo``, as in
    ``verify``. Raises RemapError for a model that fails ``schema.validate``, a ``repo`` outside a
    work tree, a ``meta.source_commit`` that is not a commit in it, or an unknown ``new_ref``.
    """
    errors = validate(model)
    if errors:
        raise RemapError("model is invalid:\n" + "\n".join(errors))
    top = toplevel(repo)
    if top is None:
        raise RemapError(f"{repo} is not inside a git work tree")
    source = model["meta"]["source_commit"]
    old_sha = _commit(top, source, f"meta.source_commit {source!r} is not a commit in {top}")
    new_sha = _commit(top, new_ref, f"unknown ref {new_ref!r}")
    out = copy.deepcopy(model)
    warnings: list[str] = []
    cache: dict[str, tuple[list[int], list[str]] | None] = {}

    def warn(message: str) -> None:
        if message not in warnings:
            warnings.append(message)

    def lookup(path: str) -> tuple[list[int], list[str]] | None:
        if path not in cache:
            before, after = git_show(top, old_sha, path), git_show(top, new_sha, path)
            if before is None or after is None:
                warn(
                    f"{path}: not found, or not UTF-8 text, at {old_sha[:12]} or {new_sha[:12]}; "
                    "line numbers left unchanged"
                )
                cache[path] = None
            else:
                after_lines = _split_lines(after)
                mapping, exact = _diff_map(_split_lines(before), after_lines)
                if not exact:
                    warn(f"{path}: changed by more than inserted lines; numbers are approximate")
                cache[path] = (mapping, after_lines)
        return cache[path]

    def move(path: str, line: int) -> int:
        found = lookup(path)
        if found is None:
            return line
        mapping = found[0]
        if line > len(mapping):
            warn(f"{path}: line {line} is past the end of the file at {old_sha[:12]}")
            if not mapping:
                return line
            line = len(mapping)
        return mapping[line - 1]

    for module in out["modules"]:
        for item in module["interface"]:
            item["line"] = move(item["file"], item["line"])
    for flow in out["flows"]:
        for step in flow["steps"]:
            step["line_start"] = move(step["file"], step["line_start"])
            step["line_end"] = max(move(step["file"], step["line_end"]), step["line_start"])
            found = lookup(step["file"])
            if "snippet" in step and found is not None:
                end = min(step["line_end"], step["line_start"] + MAX_SNIPPET_LINES - 1)
                chunk = found[1][step["line_start"] - 1 : end]
                # The validator counts snippet lines with str.splitlines, which splits at a form
                # feed inside a line; drop trailing lines until it agrees the snippet fits.
                while len("\n".join(chunk).splitlines()) > MAX_SNIPPET_LINES:
                    chunk.pop()
                step["snippet"] = "\n".join(chunk)
    out["meta"]["source_commit"] = new_sha
    return out, warnings


def write_model(path: Path, model: dict[str, Any]) -> None:
    """Write ``model`` as UTF-8 JSON bytes (no newline translation, as ``build`` writes it).

    The write is atomic (see ``fsutil.write_bytes_atomic``). The text is encoded before anything is
    written, so text that cannot be encoded (a lone surrogate) raises RemapError and leaves any
    existing file as it was.
    """
    try:
        data = (json.dumps(model, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    except UnicodeEncodeError as exc:
        raise RemapError(f"model cannot be encoded as UTF-8: {exc}") from exc
    write_bytes_atomic(path, data)
