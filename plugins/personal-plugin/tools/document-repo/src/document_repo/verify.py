"""Prove that an edited file changed only in its comments.

The skill promises never to change behaviour. This module is the proof. For
each file it compares the version at a base git ref with the working tree:

- python-ast: parse both, drop docstrings, compare the syntax trees.
- ts-printer: (JS/TS) re-print both with comments removed via the
  TypeScript compiler and compare the text. Falls back to comment-lines
  when node or typescript is not available.
- comment-lines: (everything else) a line diff may only INSERT lines, and
  every inserted line must be blank or a comment in that language.

A file that fails is reverted by the skill. This check is deliberately strict:
a false failure costs one reverted file; a false pass could ship a bug.
"""

from __future__ import annotations

import ast
import difflib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .inventory import OUTPUT_DIR
from .languages import Lang, detect


@dataclass
class Result:
    path: str
    method: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def git_show(repo: Path, ref: str, rel: str) -> str | None:
    """Return ``rel`` as it was at ``ref``, or None if it did not exist there."""
    proc = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True)
    if proc.returncode != 0:
        return None
    try:
        return proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _strip_docstrings(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]


def _python(rel: str, before: str, after: str) -> Result:
    try:
        tree_before = ast.parse(before)
    except SyntaxError as exc:
        return Result(rel, "python-ast", False, f"base version does not parse: {exc}")
    try:
        tree_after = ast.parse(after)
    except SyntaxError as exc:
        return Result(rel, "python-ast", False, f"edited version does not parse: {exc}")
    _strip_docstrings(tree_before)
    _strip_docstrings(tree_after)
    if ast.dump(tree_before) == ast.dump(tree_after):
        return Result(rel, "python-ast", True)
    return Result(
        rel, "python-ast", False, "syntax tree changed (code, not just comments or docstrings)"
    )


def comment_chunk_ok(lines: list[str], lang: Lang) -> tuple[bool, str]:
    """True when every line in an inserted chunk is blank or a comment."""
    in_block: str | None = None
    for raw in lines:
        s = raw.strip()
        if in_block is not None:
            if in_block in s:
                if s.split(in_block, 1)[1].strip():
                    return False, f"code after block-comment end: {raw!r}"
                in_block = None
            continue
        if not s or any(s.startswith(m) for m in lang.line):
            continue
        for start, end in lang.block:
            if s.startswith(start):
                rest = s[len(start) :]
                if end in rest:
                    if rest.split(end, 1)[1].strip():
                        return False, f"code after block-comment end: {raw!r}"
                else:
                    in_block = end
                break
        else:
            return False, f"non-comment line added: {raw!r}"
    if in_block is not None:
        return False, "unterminated block comment in inserted lines"
    return True, ""


def _comment_lines(rel: str, before: str, after: str, lang: Lang) -> Result:
    a, b = before.splitlines(), after.splitlines()
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag != "insert":
            return Result(rel, "comment-lines", False, f"{tag} of base lines {i1 + 1}-{i2}")
        ok, why = comment_chunk_ok(b[j1:j2], lang)
        if not ok:
            return Result(rel, "comment-lines", False, f"{why} (edited lines {j1 + 1}-{j2})")
    return Result(rel, "comment-lines", True)


def _ts_verify(repo: Path, rel: str, before: str, after: str) -> Result | None:
    """Placeholder until Task 5: None means "use comment-lines instead"."""
    return None


def verify_file(repo: Path, rel: str, before_ref: str = "HEAD") -> Result:
    """Compare the working-tree ``rel`` with ``before_ref``. See module docstring."""
    lang = detect(rel)
    if lang is None:
        return Result(rel, "none", False, "no known comment syntax for this file type")
    before = git_show(repo, before_ref, rel)
    if before is None:
        return Result(rel, "none", False, f"file is not in {before_ref} (or is not UTF-8)")
    try:
        after = (repo / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return Result(rel, "none", False, f"cannot read edited file: {exc}")
    if lang.verify_method == "python-ast":
        return _python(rel, before, after)
    if lang.verify_method == "ts-printer":
        ts_result = _ts_verify(repo, rel, before, after)
        if ts_result is not None:
            return ts_result
    return _comment_lines(rel, before, after, lang)


def changed_source_files(repo: Path, ref: str) -> list[str]:
    """Files changed in the working tree vs ``ref`` that have comment syntax.

    Markdown (no comment syntax) and the explorer output are excluded: they
    are documentation, not code, so they are never verified.
    """
    out = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", ref, "--"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(
        p
        for p in out.splitlines()
        if p and not p.startswith(OUTPUT_DIR + "/") and detect(p) is not None
    )
