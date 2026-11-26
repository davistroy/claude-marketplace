"""Prove that an edited file changed only in its comments.

The skill promises never to change behaviour. This module is the proof. For
each file it compares the version at a base git ref with the working tree:

- python-ast: parse both, drop docstrings, compare the syntax trees.
- ts-printer: (JS/TS) re-print both with comments removed via the
  TypeScript compiler and compare the text. The file is parsed as its extension says
  (``.ts``/``.mts``/``.cts`` TypeScript, ``.tsx`` TSX, ``.js``/``.mjs``/``.cjs`` JavaScript,
  ``.jsx`` JSX; see ts_print.js). A parse error in either version fails the file, because
  TypeScript skips the tokens it cannot parse. Layout a comment changes without changing
  the code is normalised first (empty blocks, JSX children the compiler discards). The
  compiler is found from explicit candidates only (``ts_search_paths``), must be the pinned
  ``TS_VERSION`` with a known ``lib/typescript.js`` hash, and its version and location are
  recorded in the passing result. There is no fallback: without
  node and typescript a JS/TS file fails, because no line-based check can
  tell a comment from text inside a template literal, regex or JSX.
- comment-lines: (everything else) a line diff may only INSERT lines, and
  every inserted line must be blank or a comment in that language.

Before any method, git must report no mode change against the base (``_mode_guard``): neither
``git diff --raw`` (work tree) nor ``git diff --cached --raw`` (index) may show one, so git's
own ``core.fileMode`` rule decides what counts, and neither side may be a symlink. A new
executable bit changes behaviour without changing one line. Before that, no attribute source
outside the commit may apply (``attribute_source_problem``): attributes decide line-ending
conversion and filters, so an uncommitted one would decide what is judged.

After a method passes, ``guards.common_guards`` runs for every method (directives, line
endings, protected headers, continuations). comment-lines also runs ``guards.context_guard``
(no new line inside a heredoc, string, block scalar and so on). See guards.py for each rule and
why it exists.

A file that fails is reverted by the skill. This check is deliberately strict:
a false failure costs one reverted file; a false pass could ship a bug.
"""

from __future__ import annotations

import ast
import difflib
import functools
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Iterable, Iterator
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


def git_blob(repo: Path, ref: str, rel: str) -> str | None:
    """Return ``rel`` at ``ref`` exactly as git stores it (no filters), or None if it was not there.

    What a commit changed is the difference between two stored blobs. Read through
    ``--filters``, both sides would be converted by whatever attributes the work tree holds
    today, which need not be the commit's (review fix 1): an untracked ``* text eol=crlf`` turns a
    committed LF -> CRLF change into two equal CRLF texts.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "blob", f"{ref}:{rel}"], capture_output=True
    )
    if proc.returncode != 0:
        return None
    try:
        return proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


#: The name git reads per-directory attributes from. Compared case-insensitively: on a
#: case-insensitive file system ``.GitAttributes`` is opened as ``.gitattributes``.
GITATTRIBUTES = ".gitattributes"

#: Pathspec for every ``.gitattributes`` in the repository, in any case.
_ATTR_PATHSPEC = ":(glob,icase)**/.gitattributes"

#: Directories git falls back to for the system attributes file when ``git var`` cannot say.
_SYSTEM_ATTR_FALLBACK = ("/etc/gitattributes", "/usr/local/etc/gitattributes")


def _git_plain(top: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """Run git with pathspec magic on, whatever the caller's environment says."""
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("GIT_LITERAL_PATHSPECS", "GIT_NOGLOB_PATHSPECS", "GIT_GLOB_PATHSPECS")
    }
    return subprocess.run(["git", "-C", str(top), *args], capture_output=True, env=env)


def _has_rules(path: Path) -> bool:
    """True when the attributes file ``path`` holds any line that is not blank or a comment.

    A file that exists but cannot be read counts as holding rules (fail closed). Read a line at a
    time, so a huge file costs one line of memory.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return any(line.strip() and not line.lstrip().startswith("#") for line in fh)
    except FileNotFoundError:
        return False
    except OSError:
        return path.exists()


def _outside_attr_files(top: Path) -> list[Path] | None:
    """The attribute files git reads that no commit holds: info, per-user and system-wide.

    None when git cannot say where the repository's ``info/attributes`` is (fail closed).
    """
    proc = _git_plain(top, "rev-parse", "--git-path", "info/attributes")
    if proc.returncode != 0:
        return None
    info = Path(os.fsdecode(proc.stdout.strip()))
    files = [info if info.is_absolute() else top / info]
    for var in ("GIT_ATTR_GLOBAL", "GIT_ATTR_SYSTEM"):
        proc = _git_plain(top, "var", var)
        if proc.returncode == 0 and proc.stdout.strip():
            files.append(Path(os.fsdecode(proc.stdout.strip())))
        elif proc.returncode != 0 and var == "GIT_ATTR_GLOBAL":
            # Older git (< 2.42) has no ``git var GIT_ATTR_*``: derive the per-user file.
            conf = _git_plain(top, "config", "--path", "--get", "core.attributesFile")
            if conf.returncode == 0 and conf.stdout.strip():
                files.append(Path(os.fsdecode(conf.stdout.strip())).expanduser())
            xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
            files.append(Path(xdg, "git", "attributes"))
        elif proc.returncode != 0 and not os.environ.get("GIT_ATTR_NOSYSTEM"):
            files.extend(Path(p) for p in _SYSTEM_ATTR_FALLBACK)
    return files


def _attr_file_problem(top: Path, rel: str) -> str | None:
    """Why the ``.gitattributes`` at ``rel`` is not exactly HEAD's, or None when it is.

    It must be tracked, carry no ``assume-unchanged`` / ``skip-worktree`` flag, and match HEAD
    in both the index and the work tree. A file in neither the index nor the work tree is fine.
    """
    tag = _git_plain(top, "--literal-pathspecs", "ls-files", "-v", "-z", "--", rel).stdout[:1]
    if not tag:
        if os.path.lexists(top / rel):
            return f"{rel} is not tracked"
        return None
    if tag != b"H":
        return f"{rel} is flagged assume-unchanged or skip-worktree"
    for extra in ((), ("--cached",)):
        proc = _git_plain(top, "--literal-pathspecs", "diff", "--quiet", *extra, "HEAD", "--", rel)
        if proc.returncode != 0:
            return f"{rel} differs from HEAD"
    return None


def attribute_source_problem(top: Path, rel: str | None = None) -> str | None:
    """Refuse when attributes that no commit holds could decide how a file is read (review fix 1).

    Attributes pick line-ending conversion and filters, so they decide what ``git_show``,
    ``git add`` and ``hash-object --path`` see. Only attributes committed at HEAD and unchanged
    are trusted. Refused: a ``.git/info/attributes``, per-user (``core.attributesFile``) or
    system attributes file with any rule; ``attr.tree`` or ``GIT_ATTR_SOURCE`` (attributes read
    from another tree); and a ``.gitattributes`` (any case) that is untracked, ignored, flagged
    ``assume-unchanged`` / ``skip-worktree`` or differs from HEAD. With ``rel`` only the
    directories that hold ``rel`` are looked at (the files git reads for it); without it, the
    whole repository, ignored directories included.
    """
    outside = _outside_attr_files(top)
    if outside is None:
        return "attributes cannot be checked: git cannot locate info/attributes"
    for path in outside:
        if _has_rules(path):
            return f"attributes outside any commit: {path} sets rules"
    if os.environ.get("GIT_ATTR_SOURCE"):
        return "attributes outside any commit: GIT_ATTR_SOURCE is set"
    if _git_plain(top, "config", "--get", "attr.tree").returncode == 0:
        return "attributes outside any commit: attr.tree is configured"
    names: set[str] = set()
    if rel is None:
        for args in (
            ("ls-files", "-z"),
            ("ls-files", "-z", "--others"),
            ("diff", "--name-only", "-z", "HEAD"),
            ("diff", "--name-only", "-z", "--cached", "HEAD"),
        ):
            proc = _git_plain(top, *args, "--", _ATTR_PATHSPEC)
            if proc.returncode != 0:
                return "attributes cannot be checked: git failed listing .gitattributes files"
            names.update(os.fsdecode(p) for p in proc.stdout.split(b"\0") if p)
    else:
        parts = Path(rel).parts[:-1]
        for depth in range(len(parts) + 1):
            here = "/".join(parts[:depth])
            names.add(f"{here}/{GITATTRIBUTES}" if here else GITATTRIBUTES)
            try:
                entries = os.listdir(top / here)
            except OSError:
                continue
            names.update(
                f"{here}/{e}" if here else e for e in entries if e.lower() == GITATTRIBUTES
            )
    for name in sorted(names):
        why = _attr_file_problem(top, name)
        if why:
            return (
                f"attributes outside any commit: {why}, so line endings and filters would not "
                "be the commit's. Commit, restore or remove it and run again"
            )
    return None


def git_size(repo: Path, ref: str, rel: str) -> int | None:
    """The size in bytes of ``rel`` at ``ref`` as git stores it, or None if it was not there.

    Cheap: git reads the object header, not the file. ``git_show`` after it reads the whole file.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-s", f"{ref}:{rel}"], capture_output=True
    )
    return int(proc.stdout) if proc.returncode == 0 else None


_DocParent = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
_DOC_PARENTS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _docstring_stmt(node: _DocParent) -> ast.Expr | None:
    """The statement that is ``node``'s docstring, or None. The one definition of a docstring."""
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[0]
    return None


def _strip_docstrings(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, _DOC_PARENTS) and _docstring_stmt(node) is not None:
            node.body = node.body[1:] or [ast.Pass()]


def docstring_stmts(tree: ast.AST) -> list[ast.Expr]:
    """Every docstring statement in ``tree``, in tree order (not line order).

    A docstring is what ``_strip_docstrings`` removes, so the two cannot disagree about which
    string statements are comments.
    """
    found = []
    for node in ast.walk(tree):
        stmt = _docstring_stmt(node) if isinstance(node, _DOC_PARENTS) else None
        if stmt is not None:
            found.append(stmt)
    return found


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


#: The ``comment_scan`` key of a line comment. A block comment is numbered from 1 in its chunk.
LINE_COMMENT = 0


def iter_comment_scan(
    lines: Iterable[str], lang: Lang, problems: list[str] | None = None
) -> Iterator[tuple[int, str] | None]:
    """Classify each line of an inserted chunk as blank, a comment, or something else, lazily.

    Yields one item per line. It is None for a blank line or any line that is not comment, else
    ``(key, text)``: ``key`` is ``LINE_COMMENT`` for a line comment, or the number of the block
    comment the line belongs to. ``text`` is what is inside the comment on that line, with the
    opening and closing marker removed and nothing else (``// x`` gives `` x``; a block line
    inside ``/** ... */`` keeps its leading ``*``).

    ``problems``, when given, receives the first reason the chunk is not all blank and comment
    lines, once the scan has read far enough to know it (an unterminated block comment is known at
    the end). Nothing is kept per line, so a reader that handles one item at a time needs memory
    for one.

    For ``lang.nested_block`` languages the block-comment depth is counted, so ``/* a /* b */``
    is still open; a chunk must end at depth 0 with nothing but blanks after the final close.
    This is the one definition of "a comment line" that ``comment_chunk_ok`` and ``traps`` share.
    """
    block: tuple[str, str] | None = None
    depth = 0
    key = LINE_COMMENT
    for raw in lines:
        s = raw.strip()
        if block is None:
            if not s:
                yield None
                continue
            marker = next((m for m in lang.line if s.startswith(m)), None)
            if marker is not None:
                yield (LINE_COMMENT, s[len(marker) :])
                continue
            block = next(((b, e) for b, e in lang.block if s.startswith(b)), None)
            if block is None:
                if problems is not None and not problems:
                    problems.append(f"non-comment line added: {raw!r}")
                yield None
                continue
            s, depth, key = s[len(block[0]) :], 1, key + 1
        depth, close = _block_close(s, block[0], block[1], depth, lang.nested_block)
        if close < 0:
            yield (key, s)
            continue
        if s[close:].strip() and problems is not None and not problems:
            problems.append(f"code after block-comment end: {raw!r}")
        yield (key, s[: close - len(block[1])])
        block = None
    if block is not None and problems is not None and not problems:
        problems.append("unterminated block comment in inserted lines")


def comment_scan(lines: list[str], lang: Lang) -> tuple[list[tuple[int, str] | None], str]:
    """``iter_comment_scan`` as a list and the first reason the chunk is not all comment, or "".

    Returns ``(found, why)``. ``found[i]`` is the item for ``lines[i]``.
    """
    problems: list[str] = []
    found = list(iter_comment_scan(lines, lang, problems))
    return found, problems[0] if problems else ""


def comment_chunk_ok(lines: list[str], lang: Lang) -> tuple[bool, str]:
    """True when every line in an inserted chunk is blank or a comment (see ``comment_scan``)."""
    why = comment_scan(lines, lang)[1]
    return not why, why


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


TS_SCRIPT = Path(__file__).with_name("ts_print.js")

#: The one TypeScript compiler the printer trusts (SEC-01): its ``package.json`` must say name
#: ``typescript`` and this version, and ``lib/typescript.js`` must hash to ``TS_SHA256``. npm
#: tarballs are deterministic, so every install of 5.6.3 holds these bytes. Mirrored in
#: ``ts_print.js``, which checks them before running any of the package; a test keeps the two
#: in step.
TS_VERSION = "5.6.3"
TS_SHA256 = "f316520790d4db220a10d890c5f85310e26a1bd3c104b8d3b5eb62ba0491651b"

#: Set to exactly ``1`` to let the printer also look in the target repo's own directories.
TS_ALLOW_REPO_ENV = "DOCUMENT_REPO_TS_ALLOW_REPO"

#: Seconds one printer run may take, and the V8 heap (MB) it may use. A run that exceeds either
#: fails the file instead of hanging or growing past the per-process memory ceiling.
TS_TIMEOUT = 120
TS_HEAP_MB = 1024

#: ``ts_print.js`` exit codes besides 0: it ran but could not print, and no typescript package.
_TS_NOT_FOUND = 3
_TS_TIMED_OUT = 124


def node_binary() -> str | None:
    return shutil.which("node")


def _neutral_dir() -> str:
    """A directory to run ``npm`` in that belongs to neither the target repo nor the caller's cwd.

    The user's home, or the tool's own directory when there is no home. ``npm`` reads the
    ``.npmrc`` of the project around its cwd, and the CLI is usually started inside the repo
    being verified, so the repo's configuration must not decide where the global root is.
    """
    home = os.path.expanduser("~")
    return home if os.path.isdir(home) else str(Path(__file__).parent)


@functools.lru_cache(maxsize=1)
def _npm_global_root() -> str | None:
    npm = shutil.which("npm")
    if npm is None:
        return None
    try:
        proc = subprocess.run(
            [npm, "root", "-g"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
            cwd=_neutral_dir(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _dirs_up_to(start: Path, root: Path) -> list[Path]:
    """``start`` and its parents up to and including ``root``; empty if ``start`` is outside."""
    chain = [start, *start.parents]
    return chain[: chain.index(root) + 1] if root in chain else []


def ts_search_paths(repo: Path, rel: str | None = None) -> list[str]:
    """Candidate locations for the typescript package, in the order ``ts_print.js`` tries them.

    ``ts_print.js`` loads the first candidate that holds the pinned compiler (name
    ``typescript``, version ``TS_VERSION``, ``lib/typescript.js`` hashing to ``TS_SHA256``) and
    skips, without running, any candidate holding something else. It never walks up from a
    candidate. A candidate is a project directory (it holds ``node_modules/typescript``), a
    ``node_modules`` directory, or the package directory itself. In order:

    1. each entry of ``DOCUMENT_REPO_TS_PATHS`` (an ``os.pathsep``-separated list).
    2. the npm global root, asked from a neutral directory so a repo ``.npmrc`` cannot steer it.
    3. only when ``DOCUMENT_REPO_TS_ALLOW_REPO=1``: every directory from the one holding
       ``repo / rel`` up to and including ``repo``, nearest first. Never above ``repo``; a
       ``rel`` that leaves the work tree contributes nothing. Without ``rel`` this is just
       ``repo``. The target's own directories come last and only on request because whatever
       they hold is the code being judged (SEC-01): a ``typescript`` there is untrusted even
       when it passes the pin, so it never outranks a tool-owned one.

    A directory that repeats an earlier one is dropped, keeping its first place.
    """
    ordered: list[str] = []
    extra = os.environ.get("DOCUMENT_REPO_TS_PATHS")
    if extra:
        ordered.extend(p for p in extra.split(os.pathsep) if p)
    global_root = _npm_global_root()
    if global_root:
        ordered.append(global_root)
    if os.environ.get(TS_ALLOW_REPO_ENV) == "1":
        root = Path(os.path.normpath(repo))
        local = [str(root)]
        if rel is not None:
            own = Path(os.path.normpath(root / rel)).parent
            local = [str(d) for d in _dirs_up_to(own, root)] or local
        ordered.extend(local)
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in ordered:
        key = os.path.normcase(os.path.normpath(candidate))
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _run_printer(
    repo: Path, rel: str, before: str, after: str
) -> subprocess.CompletedProcess[str] | None:
    """Run ``ts_print.js`` on both texts. None means there is no ``node`` to run it with.

    ``rel`` is only a name: its extension picks the script kind. The texts go through files as
    bytes, so every ``\\r`` reaches TypeScript untouched (``write_text`` would turn each ``\\n``
    into ``\\r\\n`` on Windows).
    """
    node = node_binary()
    if node is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp, "before"), Path(tmp, "after")
        a.write_bytes(before.encode("utf-8"))
        b.write_bytes(after.encode("utf-8"))
        cmd = [
            node,
            f"--max-old-space-size={TS_HEAP_MB}",
            str(TS_SCRIPT),
            json.dumps(ts_search_paths(repo, rel)),
            str(a),
            str(b),
            rel,
        ]
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, errors="replace", timeout=TS_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                cmd, _TS_TIMED_OUT, "", f"timed out after {TS_TIMEOUT}s"
            )


def typescript_available(repo: Path) -> bool:
    proc = _run_printer(repo, "probe.ts", "", "")
    return proc is not None and proc.returncode == 0


def _printer_verdict(stdout: str) -> tuple[bool, int, int, str, str] | None:
    """Parse ``ts_print.js`` output into ``(equal, before_errors, after_errors, version, where)``.

    None when any of the five is missing or of the wrong type, or the version is not
    ``TS_VERSION``. ``version`` is the compiler's own ``ts.version`` and ``where`` the package
    directory it was loaded from: output that does not say which compiler ran is not trusted.
    """
    try:
        data = json.loads(stdout)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    equal, before_errors, after_errors, version, where = (
        data.get(key) for key in ("equal", "before_errors", "after_errors", "version", "location")
    )
    if (
        isinstance(equal, bool)
        and type(before_errors) is int
        and type(after_errors) is int
        and version == TS_VERSION
        and isinstance(where, str)
        and where
    ):
        return equal, before_errors, after_errors, version, where
    return None


def _ts_verify(repo: Path, rel: str, before: str, after: str) -> Result | None:
    """Printer-based proof for JS/TS. None means "printer unavailable" (verify_file then fails)."""
    proc = _run_printer(repo, rel, before, after)
    if proc is None or proc.returncode == _TS_NOT_FOUND:
        return None
    if proc.returncode != 0:
        why = f"printer failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        return Result(rel, "ts-printer", False, why)
    verdict = _printer_verdict(proc.stdout)
    if verdict is None:
        return Result(rel, "ts-printer", False, "printer returned unreadable output")
    equal, before_errors, after_errors, version, where = verdict
    if before_errors or after_errors:
        # TypeScript skips the tokens it cannot parse, so two broken versions can print equal
        # while the code differs. Neither side may have a parse error.
        why = (
            "file does not parse cleanly as TypeScript/JavaScript "
            f"(before: {before_errors} errors, after: {after_errors} errors)"
        )
        return Result(rel, "ts-printer", False, why)
    if equal:
        return Result(rel, "ts-printer", True, f"ts-printer (typescript {version} from {where})")
    return Result(
        rel, "ts-printer", False, "code changed (printed output differs with comments removed)"
    )


TS_MISSING = (
    "TypeScript compiler not available; JS/TS files cannot be verified "
    f"(install with: npm install -g typescript@{TS_VERSION})"
)

_SYMLINK = "120000"


def _base_mode(top: Path, ref: str, rel: str) -> str | None:
    """The git mode of ``rel`` at ``ref`` (``100644``, ``100755``, ``120000``), or None."""
    proc = subprocess.run(
        ["git", "-C", str(top), "ls-tree", "-z", ref, "--", rel], capture_output=True
    )
    entry = proc.stdout.decode("utf-8", "surrogateescape").split("\0")[0]
    return entry.split(" ", 1)[0] if proc.returncode == 0 and entry else None


#: The ``:<old mode> <new mode> `` head of each ``git diff --raw`` record. Any other shape (such
#: as a combined-diff ``::`` record) puts a colon in the old mode, so it differs and fails closed.
_RAW_MODES = re.compile(r"^:(\S+) (\S+) ", re.MULTILINE)


def _git_mode_change(top: Path, ref: str, rel: str, staged: bool) -> str | None:
    """Ask git whether ``rel`` has a different mode than at ``ref``. Return a detail, or None.

    ``staged`` compares the index with ``ref`` (``git diff --cached``); otherwise the work tree
    (``git diff``). Git applies its own rules, ``core.fileMode`` included, so a bit the work tree
    cannot record is not a change, while one staged with ``update-index --chmod`` or
    ``add --chmod`` is. A path that left the index (``git rm --cached``) reads as mode 000000.
    """
    where = "index" if staged else "working tree"
    cmd = ["git", "--literal-pathspecs", "-C", str(top), "diff", "--raw", "--no-renames"]
    proc = subprocess.run(
        [*cmd, *(["--cached"] if staged else []), ref, "--", rel], capture_output=True
    )
    if proc.returncode != 0:
        return f"cannot compare the {where} file mode with {ref}: git diff failed"
    for old, new in _RAW_MODES.findall(proc.stdout.decode("utf-8", "surrogateescape")):
        if old != new:
            return f"file mode changed: {old} -> {new} ({where})"
    return None


def _mode_guard(top: Path, ref: str, rel: str) -> str | None:
    """Fail a symlink on either side, or any mode change that git reports against ``ref``.

    A symlink is found from the base mode and ``lstat``. Every other mode change is git's call,
    not ``lstat``'s: ``git diff --raw`` (work tree vs ``ref``) and ``git diff --cached --raw``
    (index vs ``ref``) both run, so git applies its own ``core.fileMode`` rule. A plain
    ``chmod`` that git does not record passes; an executable bit staged with
    ``update-index --chmod`` or ``add --chmod`` fails, as does one in the work tree by default.
    """
    base = _base_mode(top, ref, rel)
    try:
        st = os.lstat(top / rel)
    except OSError:
        return None  # a missing file is reported by the read below
    linked = stat.S_ISLNK(st.st_mode)
    if base == _SYMLINK or linked:
        now = "a symlink" if linked else "not a symlink"
        return f"symlink: file mode {base} in base, the working-tree path is {now}"
    return _git_mode_change(top, ref, rel, staged=False) or _git_mode_change(
        top, ref, rel, staged=True
    )


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
    why = attribute_source_problem(top, rel)
    if why:
        return Result(rel, "none", False, why)
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
    return _judge(top, rel, before, after, lang)


def verify_blobs(repo: Path, base: str, head: str, rel: str) -> Result:
    """Compare ``rel`` as committed at ``head`` with ``base``, reading both from git objects.

    The work tree, the index and ``git status`` play no part, so an ``assume-unchanged`` or
    ``skip-worktree`` flag, a stale stat cache or a filesystem monitor cannot make a committed
    change look like the comment-only bytes on disk (SE-H1). Both sides are the blobs exactly as
    git stores them (``git_blob``, no filters): the change a commit makes is the change between
    stored bytes, and attributes the work tree holds today cannot convert it away, so a committed
    LF -> CRLF change fails the line-ending guard (review fix 1). The attribute sources are
    checked as ``verify_file`` checks them, so the two judges refuse the same repositories. The
    mode check is the committed one: a symlink on either side, or any mode that differs between
    the two commits, fails.
    """
    lang = detect(rel)
    if lang is None:
        return Result(rel, "none", False, "no known comment syntax for this file type")
    top = toplevel(repo)
    if top is None:
        return Result(rel, "none", False, f"not inside a git work tree: {repo}")
    why = attribute_source_problem(top, rel)
    if why:
        return Result(rel, "none", False, why)
    before = git_blob(top, base, rel)
    if before is None:
        return Result(rel, "none", False, f"file is not in {base} (or is not UTF-8)")
    after = git_blob(top, head, rel)
    if after is None:
        return Result(rel, "none", False, f"file is not in {head} (or is not UTF-8)")
    old, new = _base_mode(top, base, rel), _base_mode(top, head, rel)
    if _SYMLINK in (old, new):
        return Result(rel, "none", False, f"symlink: file mode {old} in base, {new} in {head}")
    if old != new:
        return Result(rel, "none", False, f"file mode changed: {old} -> {new} (committed)")
    return _judge(top, rel, before, after, lang)


def _judge(top: Path, rel: str, before: str, after: str, lang: Lang) -> Result:
    """The language's proof, then the guards every method shares (and comment-lines' own)."""
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


@functools.lru_cache(maxsize=1)
def _skill_output() -> frozenset[str]:
    """Every path a build writes under ``explorer/``: the app's own files, read once from the
    template, and the data files ``write_explorer_data`` writes."""
    from .build import DATA_DIR, DATA_FILES, TEMPLATE_DIR, template_files

    app = {f"{OUTPUT_DIR}/{rel}" for rel in template_files(TEMPLATE_DIR)}
    return frozenset(app | {f"{OUTPUT_DIR}/{DATA_DIR}/{name}" for name in DATA_FILES})


def is_explorer_output_name(path: str) -> bool:
    """True for a path a build writes under ``explorer/``, whoever owns the directory."""
    return path in _skill_output()


def is_exempt(path: str, top: Path) -> bool:
    """True for a path the verifier never judges: Markdown, and the skill's own explorer output.

    ``path`` is relative to ``top``, the top level of the work tree. The explorer output is the
    app's own files exactly as ``build.install_template`` copies them from the template, plus
    the three files ``build.write_explorer_data`` writes into ``explorer/data/``, and only while
    ``build.is_our_explorer`` holds for ``top/explorer``: its ``state.json`` has exactly the
    keys a build writes and the hash of the ``model.json`` beside it. A target's own
    ``explorer/app.js`` or ``state.json`` is not ours because of its name. Every other path
    under ``explorer/`` (``explorer/data/loader.js``, say) is the target's and is always judged.
    Markdown is exempt anywhere, by name only: a symlink or any other entry named ``*.md`` is
    exempt whatever it holds or points at. This is the one definition of the exempt set:
    ``changed_files`` and ``changes`` leave these paths out, and ``commit --no-content-check``
    refuses every other path.
    """
    if path.lower().endswith(DOC_SUFFIXES):
        return True
    if not is_explorer_output_name(path):
        return False
    from .build import is_our_explorer

    return is_our_explorer(top / OUTPUT_DIR)


def _git_paths(repo: Path, *args: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True
    ).stdout.decode("utf-8", "surrogateescape")
    return [p for p in out.split("\0") if p]


def changed_files(repo: Path, ref: str) -> list[str]:
    """Every path that differs from ``ref`` in the working tree, plus untracked, unignored files.

    Paths are relative to the top level of the work tree that contains ``repo``, whatever
    directory inside it ``repo`` names. Only the explorer output and markdown (``DOC_SUFFIXES``)
    are left out. Everything else is returned, including files with no known comment syntax,
    new files and deleted files: ``verify_file`` fails each of those, so ``verify --changed``
    cannot pass a change it did not check. Renames are listed as a delete plus an add
    (``--no-renames``), so both sides show.
    """
    top = toplevel(repo)
    if top is None:
        raise NotADirectoryError(f"not inside a git work tree: {repo}")
    tracked = _git_paths(top, "diff", "--name-only", "--no-renames", "-z", ref, "--")
    untracked = _git_paths(top, "ls-files", "--others", "--exclude-standard", "-z")
    return sorted(p for p in set(tracked) | set(untracked) if not is_exempt(p, top))


def tracked_files(repo: Path) -> list[str]:
    """Every tracked path that is not exempt, sorted: what ``changed_files`` would list for a base
    that has none of them.

    Paths are relative to the top level of the work tree that contains ``repo``. A tracked file
    deleted from the work tree is listed (the index still has it); the reader decides what to do
    with it. Untracked and ignored files are not.
    """
    top = toplevel(repo)
    if top is None:
        raise NotADirectoryError(f"not inside a git work tree: {repo}")
    return sorted(p for p in set(_git_paths(top, "ls-files", "-z")) if not is_exempt(p, top))
