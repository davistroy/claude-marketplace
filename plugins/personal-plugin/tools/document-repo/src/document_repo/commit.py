"""Verified commits in the target repo, and the branch-wide backstop.

``commit_paths`` replaces the hand-filled shell block the skill used to run (decision D76). It
makes one commit of exactly the listed paths and proves it, failing closed at every step:

1. **Inputs.** ``repo`` must be the top level of a git work tree with a commit. Every path must
   lie inside it and exist, unless HEAD has it (a deletion). An empty list, a path outside the
   repo, the repo itself or a ref that does not resolve is bad input (``InputError``).
2. **Index.** The index is reset to HEAD, so no path staged by someone else can ride along.
3. **Precheck.** With a ref, every changed path under the list is verified comment-only against
   it before anything is staged.
4. **Commit.** The paths are staged and committed with ``git commit --only``. The message is an
   argv element: no shell sees it.
5. **Post-commit checks.** Exactly one new commit on top of the old HEAD; no path outside the list
   in it; the work tree equal to it for the listed paths; with a ref, the committed files verified
   again. Hooks run between 4 and 5, which is why 5 exists: a hook can rewrite, re-stage, add
   files, or make a commit of its own.
6. **Undo.** When a check in 5 fails, ``git reset --soft`` moves the branch back to the old HEAD,
   the index is emptied, and only the listed paths are restored: to the old HEAD with a ref (the
   change is dropped), to the bytes that were staged without one (the work is kept, a hook's
   rewrite is dropped). Edits to other paths stay as they are.

Every git call takes an argv list and literal pathspecs (``:(literal)``), so a path with spaces or
glob characters means itself.
"""

from __future__ import annotations

import hashlib
import os
import posixpath
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .changes import work_tree
from .verify import changed_files, verify_file

#: Hooks ``git commit`` runs unless ``--no-verify`` is given (``post-commit`` cannot refuse).
COMMIT_HOOKS = ("pre-commit", "prepare-commit-msg", "commit-msg")
#: Phrases git prints when it cannot sign a commit (gpg, ssh and x509 formats).
SIGNING_MARKERS = ("gpg failed to sign", "failed to sign", "signing failed", "gpg.program")


class InputError(ValueError):
    """Bad input to ``commit_paths`` or ``backstop``: exit 2, nothing changed."""


class GitError(RuntimeError):
    """A git command failed where it should not have."""


@dataclass
class Outcome:
    """What ``commit_paths`` did. ``status`` decides the exit code (see ``exit_code``)."""

    status: str
    detail: str
    sha: str | None = None
    paths: list[str] = field(default_factory=list)
    verify: list[dict[str, Any]] = field(default_factory=list)
    restored: list[str] = field(default_factory=list)
    strays: list[str] = field(default_factory=list)
    git_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "detail": self.detail,
            "sha": self.sha,
            "paths": self.paths,
            "verify": self.verify,
            "restored": self.restored,
            "strays": self.strays,
            "git_output": self.git_output,
        }

    @property
    def exit_code(self) -> int:
        return 0 if self.status in ("ok", "skip") else 1


def _run(top: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(top), *args], capture_output=True, check=False)


def _out(top: Path, *args: str) -> str:
    proc = _run(top, *args)
    if proc.returncode != 0:
        msg = proc.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git {' '.join(args)} failed: {msg}")
    return proc.stdout.decode("utf-8", "surrogateescape")


def _paths(top: Path, *args: str) -> list[str]:
    return [p for p in _out(top, *args).split("\0") if p]


def _spec(paths: list[str]) -> list[str]:
    return [f":(literal){p}" for p in paths]


def _resolve_commit(top: Path, ref: str, what: str) -> str:
    if not ref.strip():
        raise InputError(f"{what} is empty (an unfilled placeholder or an unset variable?)")
    proc = _run(top, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if proc.returncode != 0:
        raise InputError(f"{what} {ref!r} does not name a commit in {top}")
    return proc.stdout.decode().strip()


def _top(repo: Path) -> Path:
    try:
        return work_tree(repo)
    except (ValueError, OSError) as exc:
        raise InputError(str(exc)) from exc


def _in_tree(top: Path, tree: str, rel: str) -> bool:
    return bool(_paths(top, "ls-tree", "-r", "-z", "--name-only", tree, "--", *_spec([rel])))


def normalize_paths(top: Path, raw: list[str]) -> list[str]:
    """Each path relative to ``top``, in posix form, checked to exist (or to be a deletion)."""
    if not raw:
        raise InputError("no paths given: list at least one file or directory after --")
    real_top = os.path.realpath(top)
    out: list[str] = []
    for item in raw:
        if not item.strip():
            raise InputError("an empty path was given (an unfilled placeholder?)")
        absolute = item if os.path.isabs(item) else os.path.join(top, item)
        rel = os.path.relpath(os.path.normpath(absolute), top).replace(os.sep, "/")
        rel = posixpath.normpath(rel)
        if rel == ".":
            raise InputError(f"{item!r} names the whole repository; list the paths to commit")
        if rel == ".." or rel.startswith("../"):
            raise InputError(f"{item!r} is outside the repository {top}")
        if rel == ".git" or rel.startswith(".git/"):
            raise InputError(f"{item!r} is inside .git")
        parent = os.path.realpath(os.path.join(top, posixpath.dirname(rel)))
        if parent != real_top and not parent.startswith(real_top + os.sep):
            raise InputError(f"{item!r} resolves outside the repository {top} (a symlink?)")
        if not os.path.lexists(os.path.join(top, rel)) and not _in_tree(top, "HEAD", rel):
            raise InputError(f"{item!r} does not exist and is not in HEAD (a wrong path?)")
        if os.path.lexists(os.path.join(top, rel)) and not _in_tree(top, "HEAD", rel):
            if _run(top, "check-ignore", "-q", "--no-index", "--", rel).returncode == 0:
                raise InputError(f"{item!r} is ignored by git and cannot be committed")
        if rel not in out:
            out.append(rel)
    return out


def _under(path: str, roots: list[str]) -> bool:
    return any(path == r or path.startswith(r + "/") for r in roots)


def _changed(top: Path, against: str, roots: list[str]) -> list[str]:
    """Paths under ``roots`` whose work-tree state differs from ``against``, untracked included."""
    spec = _spec(roots)
    tracked = _paths(top, "diff", "--name-only", "-z", "--no-renames", against, "--", *spec)
    untracked = _paths(top, "ls-files", "--others", "--exclude-standard", "-z", "--", *spec)
    return sorted(set(tracked) | set(untracked))


def _hash(path: Path) -> str | None:
    if path.is_symlink():
        return "link:" + os.readlink(path)
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dirty_snapshot(top: Path, roots: list[str]) -> dict[str, str | None]:
    """Every dirty or untracked path outside ``roots``, with a content hash (None: deleted)."""
    raw = _out(top, "status", "--porcelain=v1", "-z", "-uall", "--no-renames")
    snap: dict[str, str | None] = {}
    for entry in raw.split("\0"):
        if len(entry) > 3:
            rel = entry[3:]
            if not _under(rel, roots):
                snap[rel] = _hash(top / rel)
    return snap


def _strays(before: dict[str, str | None], after: dict[str, str | None]) -> list[str]:
    keys = set(before) | set(after)
    return sorted(k for k in keys if before.get(k, "clean") != after.get(k, "clean"))


def _differs(top: Path, source: str, roots: list[str]) -> list[str]:
    """Paths under ``roots`` whose work-tree state differs from the tree ``source``.

    Compared through a throwaway index loaded from ``source``, so the real index (which may not
    match ``source``) cannot hide or invent a difference.
    """
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(tmp, "index")}

        def paths(*args: str) -> list[str]:
            proc = subprocess.run(
                ["git", "-C", str(top), *args], capture_output=True, check=False, env=env
            )
            if proc.returncode != 0:
                msg = proc.stderr.decode("utf-8", "replace").strip()
                raise GitError(f"git {args[0]} failed: {msg}")
            raw = proc.stdout.decode("utf-8", "surrogateescape")
            return [p for p in raw.split("\0") if p]

        paths("read-tree", source)
        spec = _spec(roots)
        tracked = paths("diff", "--name-only", "-z", "--no-renames", "--", *spec)
        untracked = paths("ls-files", "--others", "--exclude-standard", "-z", "--", *spec)
    return sorted(set(tracked) | set(untracked))


def _restore(top: Path, source: str, roots: list[str]) -> list[str]:
    """Make the listed paths in the work tree equal ``source``; return what changed.

    A path ``source`` has is checked out of it; a path it lacks is deleted. The index is not
    touched. ``GitError`` when the result still differs.
    """
    differing = _differs(top, source, roots)
    present = [p for p in differing if _in_tree(top, source, p)]
    if present:
        _out(top, "restore", f"--source={source}", "--worktree", "--", *_spec(present))
    for rel in differing:
        if rel not in present:
            path = top / rel
            if path.is_symlink() or path.is_file():
                path.unlink()
    left = _differs(top, source, roots)
    if left:
        raise GitError(f"could not restore {', '.join(left)} from {source[:12]}")
    return differing


def _hooks_that_run(top: Path) -> list[str]:
    hooks = Path(_out(top, "rev-parse", "--git-path", "hooks").strip())
    if not hooks.is_absolute():
        hooks = top / hooks
    return [h for h in COMMIT_HOOKS if os.access(hooks / h, os.X_OK)]


def _commit_failure(top: Path, output: str, skip_hooks: bool) -> str:
    lower = output.lower()
    if any(m in lower for m in SIGNING_MARKERS):
        return (
            "git could not sign the commit (commit.gpgsign or a signing key is set and the "
            "signing program failed). Skipping hooks does not help: fix signing, then run again"
        )
    hooks = [] if skip_hooks else _hooks_that_run(top)
    if hooks:
        return (
            f"git commit failed; these hooks ran and one may have refused: {', '.join(hooks)}. "
            "Read git_output"
        )
    return "git commit failed and no commit hook ran. Read git_output"


def commit_paths(
    repo: Path,
    paths: list[str],
    messages: list[str],
    verify_against: str | None,
    skip_hooks: bool = False,
) -> Outcome:
    """Commit exactly ``paths`` and prove the commit; see the module docstring.

    ``verify_against`` is the ref every changed path must be comment-only against, or None to skip
    the content check (Markdown, ``explorer/``). Raises ``InputError`` on bad input, before the
    repo is touched.
    """
    top = _top(repo)
    if not messages or not all(m.strip() for m in messages):
        raise InputError("the commit message is empty")
    pre = _resolve_commit(top, "HEAD", "HEAD")
    ref = None
    if verify_against is not None:
        ref = _resolve_commit(top, verify_against, "--verify-against")
    roots = normalize_paths(top, paths)

    _out(top, "reset", "-q")
    changed = _changed(top, "HEAD", roots)
    if not changed:
        return Outcome("skip", "nothing under the listed paths differs from HEAD")

    # Stage first, then verify: the verifier also checks the index mode against the ref, so it
    # judges exactly what will be committed (a restored file is in the index again).
    _out(top, "add", "-A", "--", *_spec(roots))
    if ref is not None:
        checks = [verify_file(top, rel, ref).to_dict() for rel in changed]
        if not all(r["ok"] for r in checks):
            _out(top, "reset", "-q")
            return Outcome(
                "precheck",
                f"a file is not comment-only against {ref[:12]}; nothing was committed",
                paths=changed,
                verify=[r for r in checks if not r["ok"]],
            )
    staged = _out(top, "write-tree").strip()
    before = _dirty_snapshot(top, roots)
    argv = ["commit", "-q", "--only"]
    if skip_hooks:
        argv.append("--no-verify")
    for message in messages:
        argv += ["-m", message]
    proc = _run(top, *argv, "--", *_spec(roots))
    output = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip()

    head = _resolve_commit(top, "HEAD", "HEAD")
    if proc.returncode != 0:
        if head != pre:
            return Outcome(
                "stop",
                "git commit failed but HEAD moved; history was not touched",
                sha=head,
                git_output=output,
            )
        _out(top, "reset", "-q")
        restored = _restore(top, staged, roots)
        return Outcome(
            "commit-failed",
            _commit_failure(top, output, skip_hooks)
            + "; nothing was committed and the index is empty"
            + ("; the listed files were reset to the bytes that were staged" if restored else ""),
            paths=changed,
            restored=restored,
            strays=_strays(before, _dirty_snapshot(top, roots)),
            git_output=output,
        )

    parents = _out(top, "rev-list", "--parents", "-n", "1", head).split()[1:]
    if head == pre or parents != [pre]:
        return Outcome(
            "stop",
            "the commit is not exactly one new commit on the old HEAD (a hook made a commit?); "
            "history was not touched",
            sha=head,
            git_output=output,
        )
    committed = _paths(
        top, "diff-tree", "-r", "-z", "--no-commit-id", "--name-only", "--no-renames", pre, head
    )
    problem = None
    results: list[dict[str, Any]] = []
    extra = [p for p in committed if not _under(p, roots)]
    if extra:
        problem = f"the commit also held {', '.join(extra)} (added by a hook?)"
    elif _changed(top, "HEAD", roots):
        problem = (
            "the work tree differs from the commit (a hook changed files without staging them)"
        )
    elif ref is not None:
        results = [verify_file(top, rel, ref).to_dict() for rel in committed]
        if not all(r["ok"] for r in results):
            problem = (
                f"a committed file is not comment-only against {ref[:12]} (a hook rewrote it?)"
            )
            results = [r for r in results if not r["ok"]]
    if problem is None:
        return Outcome(
            "ok",
            "committed and verified",
            sha=head,
            paths=committed,
            strays=_strays(before, _dirty_snapshot(top, roots)),
            git_output=output,
        )
    return _undo(top, pre, ref, staged, roots, before, problem, committed, results, output)


def _undo(
    top: Path,
    pre: str,
    ref: str | None,
    staged: str,
    roots: list[str],
    before: dict[str, str | None],
    problem: str,
    committed: list[str],
    results: list[dict[str, Any]],
    output: str,
) -> Outcome:
    bad = _resolve_commit(top, "HEAD", "HEAD")
    _out(top, "reset", "-q", "--soft", pre)
    _out(top, "reset", "-q")
    target = pre if ref else staged
    try:
        restored = _restore(top, target, roots)
    except GitError as exc:
        return Outcome(
            "stop",
            f"{problem}; the commit was undone but {exc}",
            sha=bad,
            paths=committed,
            verify=results,
            git_output=output,
        )
    to = "the old HEAD (the change is dropped)" if ref else "the bytes that were staged"
    return Outcome(
        "undone",
        f"{problem}; commit {bad[:12]} was undone and the listed paths reset to {to}",
        sha=bad,
        paths=committed,
        verify=results,
        restored=restored,
        strays=_strays(before, _dirty_snapshot(top, roots)),
        git_output=output,
    )


def backstop(repo: Path, base: str) -> dict[str, Any]:
    """Verify every change on the branch since ``base`` and check the tree is clean.

    Returns ``{"ok", "base", "verify", "status"}``. ``InputError`` for a bad repo or base.
    """
    top = _top(repo)
    sha = _resolve_commit(top, base, "--base")
    if _run(top, "merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
        raise InputError(f"--base {base!r} is not an ancestor of HEAD")
    results = [verify_file(top, rel, sha).to_dict() for rel in changed_files(top, sha)]
    raw = _out(top, "status", "--porcelain=v1", "-z", "-uall")
    status = [e for e in raw.split("\0") if e]
    ok = all(r["ok"] for r in results) and not status
    return {"ok": ok, "base": sha, "verify": results, "status": status}
