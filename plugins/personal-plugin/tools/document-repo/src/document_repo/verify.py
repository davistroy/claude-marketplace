"""Prove that an edited file changed only in its comments.

The skill promises never to change behaviour. This module is the proof. For
each file it compares the version at a base git ref with the working tree:

- python-ast: parse both, drop docstrings, compare the syntax trees.
- ts-printer: (JS/TS) re-print both with comments removed via the
  TypeScript compiler and compare the text. There is no fallback: without
  node and typescript a JS/TS file fails, because no line-based check can
  tell a comment from text inside a template literal, regex or JSX.
- comment-lines: (everything else) a line diff may only INSERT lines, and
  every inserted line must be blank or a comment in that language.

Before any method, the file mode must match the base (``_mode_guard``): a new
executable bit or a symlink changes behaviour without changing one line.

After a method passes, ``guards.common_guards`` runs for every method (directives, line
endings, protected headers, continuations), and comment-lines also runs
``guards.context_guard`` (no new line inside a heredoc, string, block scalar and so on). See
guards.py for each rule and why it exists.

A file that fails is reverted by the skill. This check is deliberately strict:
a false failure costs one reverted file; a false pass could ship a bug.
"""

from __future__ import annotations

import ast
import difflib
import os
import stat
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .guards import common_guards, context_guard
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


def toplevel(repo: Path) -> Path | None:
    """The work-tree root that contains ``repo``, or None when ``repo`` is not in a work tree.

    Every path the verifier reads or reports is relative to this root, so ``--repo`` may name any
    directory inside the repository.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"], capture_output=True
    )
    if proc.returncode != 0:
        return None
    return Path(proc.stdout.decode("utf-8", "surrogateescape").strip())


def git_show(repo: Path, ref: str, rel: str) -> str | None:
    """Return ``rel`` as checkout at ``ref`` would write it, or None if it was not there.

    ``cat-file --filters`` applies the same eol/autocrlf conversion as a checkout, so a CRLF work
    tree from ``core.autocrlf`` compares equal, while a real line-ending change does not.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--filters", f"{ref}:{rel}"], capture_output=True
    )
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


_DOC_OWNERS = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _docstrings(tree: ast.AST) -> dict[tuple[str, ...], str]:
    """Docstrings keyed by the chain of class/def names (``name#n`` for the n-th duplicate)."""
    found: dict[tuple[str, ...], str] = {}

    def visit(node: ast.AST, key: tuple[str, ...], seen: dict[str, int]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _DOC_OWNERS):
                n = seen.get(child.name, 0)
                seen[child.name] = n + 1
                child_key = (*key, child.name if n == 0 else f"{child.name}#{n}")
                doc = ast.get_docstring(child, clean=False)
                if doc is not None:
                    found[child_key] = doc
                visit(child, child_key, {})
            else:
                visit(child, key, seen)

    module_doc = ast.get_docstring(tree, clean=False) if isinstance(tree, ast.Module) else None
    if module_doc is not None:
        found[()] = module_doc
    visit(tree, (), {})
    return found


def _docstring_guard(tree_before: ast.AST, tree_after: ast.AST) -> str | None:
    """Existing docstrings are runtime data (PLY, argparse, doctest): they must not change."""
    old, new = _docstrings(tree_before), _docstrings(tree_after)
    for key, doc in old.items():
        if new.get(key) != doc:
            return f"existing docstring changed: {'.'.join(key) or '<module>'}"
    for key, doc in new.items():
        if key not in old and ">>>" in doc:
            return f"new docstring contains a doctest: {'.'.join(key) or '<module>'}"
    return None


def _python(rel: str, before: str, after: str) -> Result:
    # Parse bytes, not str, so a coding cookie is honoured exactly as the real import would.
    try:
        tree_before = ast.parse(before.encode("utf-8"))
    except SyntaxError as exc:
        return Result(rel, "python-ast", False, f"base version does not parse: {exc}")
    try:
        tree_after = ast.parse(after.encode("utf-8"))
    except SyntaxError as exc:
        return Result(rel, "python-ast", False, f"edited version does not parse: {exc}")
    why = _docstring_guard(tree_before, tree_after)
    if why:
        return Result(rel, "python-ast", False, why)
    _strip_docstrings(tree_before)
    _strip_docstrings(tree_after)
    if ast.dump(tree_before) == ast.dump(tree_after):
        return Result(rel, "python-ast", True)
    return Result(
        rel, "python-ast", False, "syntax tree changed (code, not just comments or docstrings)"
    )


def _block_close(text: str, start: str, end: str, depth: int, nested: bool) -> tuple[int, int]:
    """Scan ``text`` inside a block comment at ``depth``.

    Return ``(depth, index just past the close)``; the index is -1 when the line ends still open.
    Without nesting the first ``end`` closes the comment, whatever ``start``s it contains.
    """
    i = 0
    while i < len(text):
        if nested and text.startswith(start, i):
            depth, i = depth + 1, i + len(start)
        elif text.startswith(end, i):
            depth, i = depth - 1, i + len(end)
            if depth == 0:
                return 0, i
        else:
            i += 1
    return depth, -1


def comment_chunk_ok(lines: list[str], lang: Lang) -> tuple[bool, str]:
    """True when every line in an inserted chunk is blank or a comment.

    For ``lang.nested_block`` languages the block-comment depth is counted, so ``/* a /* b */``
    is still open; a chunk must end at depth 0 with nothing but blanks after the final close.
    """
    block: tuple[str, str] | None = None
    depth = 0
    for raw in lines:
        s = raw.strip()
        if block is None:
            if not s or any(s.startswith(m) for m in lang.line):
                continue
            block = next(((b, e) for b, e in lang.block if s.startswith(b)), None)
            if block is None:
                return False, f"non-comment line added: {raw!r}"
            s, depth = s[len(block[0]) :], 1
        depth, close = _block_close(s, block[0], block[1], depth, lang.nested_block)
        if close >= 0:
            if s[close:].strip():
                return False, f"code after block-comment end: {raw!r}"
            block = None
    if block is not None:
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
    """Placeholder until Task 5: None means "the TypeScript compiler is not available"."""
    return None


TS_MISSING = (
    "TypeScript compiler not available; JS/TS files cannot be verified "
    "(install with: npm install -g typescript)"
)

_SYMLINK, _EXEC, _PLAIN = "120000", "100755", "100644"


def _base_mode(top: Path, ref: str, rel: str) -> str | None:
    """The git mode of ``rel`` at ``ref`` (``100644``, ``100755``, ``120000``), or None."""
    proc = subprocess.run(
        ["git", "-C", str(top), "ls-tree", "-z", ref, "--", rel], capture_output=True
    )
    entry = proc.stdout.decode("utf-8", "surrogateescape").split("\0")[0]
    return entry.split(" ", 1)[0] if proc.returncode == 0 and entry else None


def _filemode_tracked(top: Path) -> bool:
    """False when ``core.fileMode`` is false: git then records no executable-bit change."""
    proc = subprocess.run(
        ["git", "-C", str(top), "config", "--bool", "core.fileMode"], capture_output=True
    )
    return proc.stdout.strip() != b"false"


def _mode_guard(top: Path, ref: str, rel: str) -> str | None:
    """Fail a symlink on either side, or an executable bit that differs from the base."""
    base = _base_mode(top, ref, rel)
    try:
        st = os.lstat(top / rel)
    except OSError:
        return None  # a missing file is reported by the read below
    if stat.S_ISLNK(st.st_mode):
        work = _SYMLINK
    else:
        work = _EXEC if st.st_mode & stat.S_IXUSR else _PLAIN
        if work != base and base in (_EXEC, _PLAIN) and not _filemode_tracked(top):
            work = base
    if _SYMLINK in (base, work):
        return f"symlink: file mode {base} in base, {work} in working tree"
    if base != work:
        return f"file mode changed: {base} -> {work}"
    return None


def verify_file(repo: Path, rel: str, before_ref: str = "HEAD") -> Result:
    """Compare the working-tree ``rel`` with ``before_ref``. See module docstring.

    ``rel`` is relative to the top level of the work tree that contains ``repo``.
    """
    lang = detect(rel)
    if lang is None:
        return Result(rel, "none", False, "no known comment syntax for this file type")
    top = toplevel(repo)
    if top is None:
        return Result(rel, "none", False, f"not inside a git work tree: {repo}")
    before = git_show(top, before_ref, rel)
    if before is None:
        return Result(rel, "none", False, f"file is not in {before_ref} (or is not UTF-8)")
    why = _mode_guard(top, before_ref, rel)
    if why:
        return Result(rel, "none", False, why)
    try:
        # Bytes, then decode: keeps every "\r" so the line-ending guard can see it.
        after = (top / rel).read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return Result(rel, "none", False, f"cannot read edited file: {exc}")
    result = _method_result(top, rel, before, after, lang)
    if not result.ok:
        return result
    why = common_guards(rel, before, after, lang)
    if why is None and result.method == "comment-lines":
        why = context_guard(before, after, lang)
    return Result(rel, result.method, False, why) if why else result


def _method_result(repo: Path, rel: str, before: str, after: str, lang: Lang) -> Result:
    """Run the language's own proof: python-ast, ts-printer (no fallback) or comment-lines."""
    if lang.verify_method == "python-ast":
        return _python(rel, before, after)
    if lang.verify_method == "ts-printer":
        return _ts_verify(repo, rel, before, after) or Result(rel, "none", False, TS_MISSING)
    return _comment_lines(rel, before, after, lang)


#: Documentation the skill writes, which is never verified. Markdown only: ``.txt`` is also
#: ``requirements.txt`` and ``CMakeLists.txt``, ``.mdx`` is JSX and ``.rst`` has directives.
DOC_SUFFIXES = (".md",)


def _git_paths(repo: Path, *args: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True
    ).stdout.decode("utf-8", "surrogateescape")
    return [p for p in out.split("\0") if p]


def changed_files(repo: Path, ref: str) -> list[str]:
    """Every path that differs from ``ref`` in the working tree, plus untracked, unignored files.

    Paths are relative to the top level of the work tree that contains ``repo``, whatever
    directory inside it ``repo`` names. Only the explorer output and markdown (``DOC_SUFFIXES``)
    are left out. Everything else
    is returned, including files with no known comment syntax, new files and deleted files:
    ``verify_file`` fails each of those, so ``verify --changed`` cannot pass a change it did not
    check. Renames are listed as a delete plus an add (``--no-renames``), so both sides show.
    """
    top = toplevel(repo)
    if top is None:
        raise NotADirectoryError(f"not inside a git work tree: {repo}")
    tracked = _git_paths(top, "diff", "--name-only", "--no-renames", "-z", ref, "--")
    untracked = _git_paths(top, "ls-files", "--others", "--exclude-standard", "-z")
    return sorted(
        p
        for p in set(tracked) | set(untracked)
        if not p.startswith(OUTPUT_DIR + "/") and not p.lower().endswith(DOC_SUFFIXES)
    )
