"""Find what changed since the docs were built, for --update runs.

Input: state.json (the commit the docs describe) and model.json (module
paths). Output: which modules need fresh analysis. A file edited only in its
comments does not count (the verifier proves this), and documentation files
and the explorer itself are ignored.

Two things are compared here and they must describe the same files. The list of changed paths
comes from commits (``source_commit..HEAD``), while the comment-only proof reads the working
tree (``verify.verify_file``). A working tree that differs from HEAD would let the proof pass a
file whose committed code changed, so a dirty tree is refused rather than guessed at.

Paths are relative to the top level of the work tree, the same root ``inventory`` lists and the
model's module paths use, so ``repo`` must be that top level.

Git may be told to hide changes from both reads: a submodule can be ignored (``.gitmodules``,
``diff.ignoreSubmodules``, ``status.ignoreSubmodules``), and a file can be flagged
``assume-unchanged`` or ``skip-worktree`` so that ``git status`` never looks at it. Each of those
would let a stale or edited work tree pass for the committed one, so submodules are always
compared (``--ignore-submodules=none``) and a file is trusted for the comment-only proof only
after its work-tree bytes are shown to be HEAD's.
"""

from __future__ import annotations

import itertools
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from .languages import detect
from .verify import is_exempt, toplevel, verify_file

#: A SHA-1 or SHA-256 object name. ``HEAD`` or a branch would diff a commit against itself (or
#: against a moving target) and report that nothing changed, so only a full hash is accepted.
_FULL_HASH = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}", re.IGNORECASE)


def _prefix(module_path: str) -> str:
    """A module path as a ``/``-separated prefix; ``""`` for the repo root (``.``)."""
    prefix = PurePosixPath(module_path).as_posix().strip("/")
    return "" if prefix == "." else prefix


def _claim(path: str, prefix: str) -> int:
    """How much of ``path`` a module path claims: its length, 0 for the root, -1 for none."""
    if not prefix:
        return 0 if "/" not in path else -1
    return len(prefix) if path == prefix or path.startswith(prefix + "/") else -1


def _owners(path: str, modules: list[dict[str, Any]]) -> list[str]:
    """Ids of every module that ties for the longest matching path prefix, in the order given."""
    best: list[str] = []
    best_len = -1
    for module in modules:
        length = _claim(path, _prefix(module["path"]))
        if length < 0:
            continue
        if length > best_len:
            best, best_len = [module["id"]], length
        elif length == best_len:
            best.append(module["id"])
    return best


def modules_for(path: str, modules: list[dict[str, Any]]) -> list[str]:
    """The sorted ids of every module that owns ``path``: those with the longest matching prefix.

    More than one module owns a path when they share a path (a module split in two, or the same
    directory spelled ``src`` and ``./src/``). A change there affects all of them, so none may be
    dropped. The root module (path ``.``) owns only top-level files, so a file in a directory no
    module names stays unowned instead of falling to the root. The result is empty then.
    """
    return sorted(set(_owners(path, modules)))


def module_for(path: str, modules: list[dict[str, Any]]) -> str | None:
    """The first module (in list order) that owns ``path``, or None. See ``modules_for``.

    Kept for callers that want one answer; ``compute_changes`` uses ``modules_for`` so that a tie
    marks every module.
    """
    owners = _owners(path, modules)
    return owners[0] if owners else None


def _git(top: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    # --no-optional-locks: this only reads, so it must not rewrite the index of a repo in use.
    # GIT_LITERAL_PATHSPECS: a path here is a file name, never pathspec magic (":(top)x.py") or a
    # glob ("w[1].py").
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(top), *args],
        capture_output=True,
        env={**os.environ, "GIT_LITERAL_PATHSPECS": "1"},
    )


def _git_out(top: Path, *args: str) -> bytes:
    proc = _git(top, *args)
    if proc.returncode != 0:
        why = proc.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"git {args[0]} failed: {why}")
    return proc.stdout


def _ignored(path: str) -> bool:
    """Output the skill writes itself (the explorer, at the repo root) and markdown docs."""
    return is_exempt(path)


def _text(field: bytes) -> str:
    try:
        return field.decode("utf-8")
    except UnicodeDecodeError:
        # The report is JSON, which cannot carry bytes that are not text; surrogate escapes would
        # crash the writer later.
        raise ValueError(f"changed path is not valid UTF-8: {field!r}") from None


def _parse_name_status(raw: bytes) -> list[tuple[str, str, str]]:
    """Parse ``git diff --name-status -z`` into ``(status letter, old path, new path)``.

    The output is ``STATUS NUL PATH NUL``, with two paths for a rename or copy. NUL is the only
    byte a path cannot contain, so a path with a tab, a newline or a space survives intact; a
    tab-separated parse would split it. For a path that was not renamed, old and new are equal.
    """
    if raw and not raw.endswith(b"\0"):
        raise ValueError("unexpected git diff output: it is cut off before its last NUL")
    fields = [_text(field) for field in raw.split(b"\0")[:-1]]  # [-1] is what follows the last NUL
    records: list[tuple[str, str, str]] = []
    rest = iter(fields)
    for status in rest:
        kind = status[:1]
        want = 2 if kind in ("R", "C") else 1
        paths = list(itertools.islice(rest, want))
        if not kind or len(paths) != want or not all(paths):
            raise ValueError(f"unexpected git diff output near {status!r}")
        records.append((kind, paths[0], paths[-1]))
    return records


def _modules(model: Any) -> list[dict[str, Any]]:
    modules = model.get("modules") if isinstance(model, dict) else None
    if not isinstance(modules, list) or not all(
        isinstance(m, dict) and isinstance(m.get("id"), str) and isinstance(m.get("path"), str)
        for m in modules
    ):
        raise ValueError("model has no usable modules[] (each needs a string id and path)")
    return modules


def _source_commit(state: Any) -> str:
    since = state.get("source_commit") if isinstance(state, dict) else None
    if not isinstance(since, str) or not since:
        raise ValueError("state has no source_commit")
    if not _FULL_HASH.fullmatch(since):
        raise ValueError(f"source_commit {since!r} is not a full commit hash")
    return since.lower()


def work_tree(repo: Path) -> Path:
    """The top level of the git work tree ``repo`` names; ``ValueError`` when it is anything else.

    Public so the command line can check it before it reads any other input.
    """
    top = toplevel(repo)
    if top is None:
        raise ValueError(f"not inside a git work tree: {repo}")
    if not os.path.samefile(top, repo):
        raise ValueError(f"repo must be the top level of its git work tree ({top}), not {repo}")
    return top


def _require_clean(top: Path) -> None:
    # --ignore-submodules=none: "ignore = all" (in .gitmodules or the config) would otherwise hide
    # a submodule whose work tree was edited.
    if _git_out(
        top, "status", "--porcelain", "-z", "--untracked-files=normal", "--ignore-submodules=none"
    ):
        raise ValueError(
            "working tree is not clean: commit or stash local changes first (the comment-only "
            "check reads the working tree, the list of changed files reads commits)"
        )


def _require_plain_index_entry(top: Path, path: str) -> None:
    """Refuse a file that git is told not to look at (``assume-unchanged``, ``skip-worktree``).

    ``git status`` reports such a file as clean whatever is on disk. ``git ls-files -v`` shows an
    ordinary tracked file as ``H``; a lowercase tag means assume-unchanged, ``S`` skip-worktree
    (``s``: both). Anything else is refused as well, because it is not what the clean-tree check
    assumed.
    """
    # GIT_LITERAL_PATHSPECS makes the path match itself and nothing else, so the first record is
    # this file's; the tag is its first byte (empty when git lists nothing for it).
    tag = _git_out(top, "ls-files", "-v", "-z", "--", path)[:1].decode("ascii", "replace")
    if tag == "H":
        return
    flags = []
    if tag.islower():
        flags.append("assume-unchanged")
    if tag.upper() == "S":
        flags.append("skip-worktree")
    what = (
        " and ".join(flags)
        or f"in an unexpected index state (git ls-files -v tag: {tag or 'none'})"
    )
    raise ValueError(
        f"{path} is {what}: git status cannot see edits to it, so its comment-only check cannot "
        "be trusted. Clear it (git update-index --no-assume-unchanged --no-skip-worktree "
        "<file>, or widen a sparse checkout) and run again"
    )


def _require_matches_head(top: Path, head: str, path: str) -> None:
    """Refuse a file whose work-tree bytes are not HEAD's blob, whatever ``git status`` says.

    ``git status`` is only as good as the stat cache, flags and filesystem monitor behind it. The
    hash is taken through the same filters as ``git add`` (``--path``: line endings, attributes),
    so a checkout that converts line endings is not mistaken for an edit.
    """
    blob = _git_out(top, "rev-parse", "--verify", f"{head}:{path}").decode("ascii").strip()
    found = _git_out(top, "hash-object", f"--path={path}", "--", str(top / path))
    if found.decode("ascii").strip() != blob:
        raise ValueError(
            f"{path} differs from HEAD although git status reports a clean tree (a stale "
            "filesystem monitor or stat cache?): its comment-only check would read the wrong "
            "file. Run git update-index --really-refresh, or restore the file, and run again"
        )


def _comment_only(top: Path, head: str, since: str, path: str) -> bool:
    """True when ``path`` is proven to differ from ``since`` in comments only.

    The proof reads the work tree, so the work tree must first be shown to be HEAD's file; a file
    that cannot be shown that way raises ``ValueError`` instead of being guessed at.
    """
    _require_plain_index_entry(top, path)
    full = top / path
    if full.is_symlink() or not full.is_file():
        # Not hashable as a file (``hash-object`` would follow the link and hash its target), and
        # never comment-only: a symlink or a submodule directory has no comments.
        return False
    _require_matches_head(top, head, path)
    return verify_file(top, path, since).ok


def compute_changes(repo: Path, state: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    """Report what changed between ``state["source_commit"]`` and HEAD, by module.

    Returns ``since``, ``head``, ``changed_files`` (``{"status", "path"}``, the new path for a
    rename), ``comment_only_files`` (edited, proven comment-only, so not a change),
    ``removed_files``, ``affected_modules`` and ``unmapped_files``.

    ``affected_modules`` holds every module that owns a changed path. When several modules share
    the longest matching path they all own it, and all are marked. A rename affects the module it
    left and the one it entered. A file that is a document or part of the explorer owns nothing,
    on either side of a rename. A submodule is a path like any other: a moved pointer marks the
    module that owns the submodule's path.

    ``unmapped_files`` is every changed file that no module path claims, new or modified (a
    renamed file by its new path). It is not limited to new files: an edited file in a directory
    the model never covered is listed here, and the caller must decide what to do with it. A
    deleted file no module claims is listed only in ``removed_files``.

    Raises ``ValueError`` for input that cannot be answered from: a state without a full
    ``source_commit``, a model without ``modules``, a commit not in this repository, a ``repo``
    that is not the top of a git work tree, a working tree that is not clean (a submodule's
    included), or an edited source file whose work-tree bytes cannot be shown to be HEAD's (it is
    flagged assume-unchanged or skip-worktree, or differs from HEAD although git says it does not).
    """
    modules = _modules(model)
    since = _source_commit(state)
    top = work_tree(repo)
    if _git(top, "cat-file", "-e", f"{since}^{{commit}}").returncode != 0:
        raise ValueError(f"source_commit {since} is not in this repository's history")
    _require_clean(top)
    head = _git_out(top, "rev-parse", "HEAD").decode("ascii").strip()
    diff = _git_out(
        top, "diff", "--name-status", "-z", "-M", "--ignore-submodules=none", since, head, "--"
    )
    changed: list[dict[str, str]] = []
    comment_only: list[str] = []
    removed: list[str] = []
    unmapped: set[str] = set()
    affected: set[str] = set()
    for kind, old, new in _parse_name_status(diff):
        if _ignored(old) and _ignored(new):
            continue
        if kind == "M" and detect(new) is not None and _comment_only(top, head, since, new):
            comment_only.append(new)
            continue
        changed.append({"status": kind, "path": new})
        if kind == "D":
            removed.append(old)
        for path in {old, new}:
            if _ignored(path):
                continue
            owners = modules_for(path, modules)
            affected.update(owners)
            if not owners and path == new and kind != "D":
                unmapped.add(path)
    return {
        "since": since,
        "head": head,
        "changed_files": sorted(changed, key=lambda c: (c["path"], c["status"])),
        "comment_only_files": sorted(comment_only),
        "removed_files": sorted(removed),
        "affected_modules": sorted(affected),
        "unmapped_files": sorted(unmapped),
    }
