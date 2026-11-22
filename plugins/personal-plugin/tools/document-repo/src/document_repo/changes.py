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
"""

from __future__ import annotations

import itertools
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from .inventory import OUTPUT_DIR
from .languages import detect
from .verify import DOC_SUFFIXES, toplevel, verify_file

#: A SHA-1 or SHA-256 object name. ``HEAD`` or a branch would diff a commit against itself (or
#: against a moving target) and report that nothing changed, so only a full hash is accepted.
_FULL_HASH = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}", re.IGNORECASE)


def _prefix(module_path: str) -> str:
    """A module path as a ``/``-separated prefix; ``""`` for the repo root (``.``)."""
    prefix = PurePosixPath(module_path).as_posix().strip("/")
    return "" if prefix == "." else prefix


def module_for(path: str, modules: list[dict[str, Any]]) -> str | None:
    """The id of the module that owns ``path``: the longest matching path prefix wins.

    The root module (path ``.``) owns only top-level files, so a file in a directory no module
    names stays unowned instead of falling to the root.
    """
    best: str | None = None
    best_len = -1
    for module in modules:
        prefix = _prefix(module["path"])
        if not prefix:
            if "/" not in path and best_len < 0:
                best, best_len = module["id"], 0
        elif (path == prefix or path.startswith(prefix + "/")) and len(prefix) > best_len:
            best, best_len = module["id"], len(prefix)
    return best


def _git(top: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    # --no-optional-locks: this only reads, so it must not rewrite the index of a repo in use.
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(top), *args], capture_output=True
    )


def _git_out(top: Path, *args: str) -> bytes:
    proc = _git(top, *args)
    if proc.returncode != 0:
        why = proc.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"git {args[0]} failed: {why}")
    return proc.stdout


def _ignored(path: str) -> bool:
    """Output the skill writes itself (the explorer, at the repo root) and markdown docs."""
    return path.startswith(OUTPUT_DIR + "/") or path.lower().endswith(DOC_SUFFIXES)


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


def _work_tree(repo: Path) -> Path:
    top = toplevel(repo)
    if top is None:
        raise ValueError(f"not inside a git work tree: {repo}")
    if not os.path.samefile(top, repo):
        raise ValueError(f"repo must be the top level of its git work tree ({top}), not {repo}")
    return top


def _require_clean(top: Path) -> None:
    if _git_out(top, "status", "--porcelain", "-z", "--untracked-files=normal"):
        raise ValueError(
            "working tree is not clean: commit or stash local changes first (the comment-only "
            "check reads the working tree, the list of changed files reads commits)"
        )


def compute_changes(repo: Path, state: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    """Report what changed between ``state["source_commit"]`` and HEAD, by module.

    Returns ``since``, ``head``, ``changed_files`` (``{"status", "path"}``, the new path for a
    rename), ``comment_only_files`` (edited, proven comment-only, so not a change),
    ``removed_files``, ``affected_modules`` and ``unmapped_files`` (changed, owned by no module).
    A rename affects the module it left and the one it entered. A file that is a document or part
    of the explorer owns nothing, on either side of a rename.

    Raises ``ValueError`` for input that cannot be answered from: a state without a full
    ``source_commit``, a model without ``modules``, a commit not in this repository, a ``repo``
    that is not the top of a git work tree, or a working tree that is not clean.
    """
    modules = _modules(model)
    since = _source_commit(state)
    top = _work_tree(repo)
    if _git(top, "cat-file", "-e", f"{since}^{{commit}}").returncode != 0:
        raise ValueError(f"source_commit {since} is not in this repository's history")
    _require_clean(top)
    head = _git_out(top, "rev-parse", "HEAD").decode("ascii").strip()
    diff = _git_out(top, "diff", "--name-status", "-z", "-M", since, head, "--")
    changed: list[dict[str, str]] = []
    comment_only: list[str] = []
    removed: list[str] = []
    unmapped: set[str] = set()
    affected: set[str] = set()
    for kind, old, new in _parse_name_status(diff):
        if _ignored(old) and _ignored(new):
            continue
        if kind == "M" and detect(new) is not None and verify_file(top, new, since).ok:
            comment_only.append(new)
            continue
        changed.append({"status": kind, "path": new})
        if kind == "D":
            removed.append(old)
        for path in {old, new}:
            if _ignored(path):
                continue
            module_id = module_for(path, modules)
            if module_id is not None:
                affected.add(module_id)
            elif path == new and kind != "D":
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
