"""Verified commits in the target repo, and the branch-wide backstop.

``commit_paths`` replaces the hand-filled shell block the skill used to run (decision D76). It
makes one commit of exactly the listed paths and proves it, failing closed at every step:

1. **Inputs.** ``repo`` must be the top level of a git work tree with a commit. Every path must
   lie inside it, not pass through a symlink, and exist (unless HEAD has it: a deletion) as a
   path git knows. An empty list, a path outside the repo, the repo itself, a ref that does not
   resolve or is not an ancestor of HEAD is bad input (``InputError``). Without a ref (docs
   mode), a changed path outside the exempt set of ``verify.is_exempt`` is bad input too. So is
   a listed directory that holds an untracked file git ignores which the commit is expected to
   carry (see ``_refuse_ignored``): ``git add`` skips it without a word, so the commit would be
   partial and still say ``ok``.
2. **Index.** ``git reset -q`` empties the index of every other path, so nothing staged by
   someone else can ride along. It also discards content of other paths that was staged and
   never written to the work tree; the work tree keeps its bytes. The skill never stages, so a
   run does not reach that case.
3. **Stage, then precheck.** The paths are staged (``git add``, which stages deletions too), and
   with a ref every changed path under the list is verified comment-only against it.
4. **Commit.** ``git commit --only`` of the listed paths. The message is an argv element: no
   shell sees it.
5. **Post-commit checks.** Exactly one new commit on top of the old HEAD; no path outside the list
   in it; without a ref, no path in it outside the exempt set; the work tree equal to it for the
   listed paths; with a ref, the committed files verified again. Hooks run between 4 and 5, which
   is why 5 exists: a hook can rewrite, re-stage, add files, or make a commit of its own.
   When every check passes, ``git reset -q`` sets the index to HEAD: under ``--only`` the real
   index keeps the listed paths' pre-hook bytes after a hook re-stages them, and the work tree
   already equals the commit, so only those stale staged bytes go. A failure of that reset is
   noted in ``detail``; the outcome stays ``ok``.
6. **Undo.** When a check in 5 fails, ``git reset --soft`` moves the branch back to the old HEAD,
   the index is emptied, and only the listed paths are restored: to the old HEAD with a ref (the
   change is dropped), to the bytes that were staged without one (the work is kept, a hook's
   rewrite is dropped). Edits to other paths stay as they are.
7. **Anything else after the commit ran.** An exception of any kind (a git failure, a crash in
   the verifier, an interrupt) once ``git commit`` has run is a ``stop`` outcome: the commit is
   undone as in 6 if it is ours, and the result says whether that worked. Only failures before
   the commit reach the caller as exceptions.

Every git call takes an argv list and literal pathspecs (``:(literal)``), so a path with spaces or
glob characters means itself.
"""

from __future__ import annotations

import hashlib
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .changes import work_tree
from .inventory import OUTPUT_DIR, SKIP_DIRS
from .verify import changed_files, is_exempt, is_explorer_output_name, verify_file

#: Hooks ``git commit`` runs unless ``--no-verify`` is given (``post-commit`` cannot refuse).
COMMIT_HOOKS = ("pre-commit", "prepare-commit-msg", "commit-msg")
#: Phrases git prints when it cannot sign a commit (gpg, ssh and x509 formats).
SIGNING_MARKERS = ("gpg failed to sign", "failed to sign", "signing failed", "gpg.program")
#: The most ignored files the refusal names; it counts the rest.
IGNORED_SHOWN = 20
#: Bytes read from a git listing at a time. A directory with a million ignored files costs no
#: more memory than one with ten.
_CHUNK = 1 << 16


class InputError(ValueError):
    """Bad input to ``commit_paths`` or ``backstop``: exit 2, nothing changed."""


class GitError(RuntimeError):
    """A git command failed where it should not have."""


@dataclass
class Outcome:
    """What ``commit_paths`` did. ``status`` decides the exit code (see ``exit_code``)."""

    status: str
    detail: str
    #: The commit HEAD named before the command ran. After ``stop``, commits above it were not
    #: verified by this command.
    pre: str | None = None
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
            "pre": self.pre,
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


def _precomposes(top: Path) -> bool:
    """True when git stores this repo's paths precomposed (NFC), as git on macOS can."""
    if sys.platform != "darwin":
        return False
    proc = _run(top, "config", "--bool", "--get", "core.precomposeunicode")
    return proc.stdout.strip() == b"true"


def _symlink_component(top: Path, rel: str) -> str | None:
    """The first directory on the way to ``rel`` that is a symlink, or None."""
    parts = rel.split("/")[:-1]
    for i in range(1, len(parts) + 1):
        prefix = "/".join(parts[:i])
        if os.path.islink(os.path.join(top, prefix)):
            return prefix
    return None


def _misspelled(top: Path, rel: str, precompose: bool) -> str | None:
    """How the disk spells ``rel`` when some component of it exists under another spelling.

    On a case-insensitive filesystem ``A/new.md`` opens ``a/new.md``, but git treats it as a
    different path: staging, committing and restoring then act on a file git never held. Each
    component must appear exactly in ``os.listdir`` of its parent (NFC-compared when git
    precomposes). None when the spelling matches, or when the path stops existing first.
    """
    parts = rel.split("/")
    here = str(top)
    for i, part in enumerate(parts):
        try:
            names = os.listdir(here)
        except OSError:
            return None
        norm = (lambda n: unicodedata.normalize("NFC", n)) if precompose else (lambda n: n)
        found = [n for n in names if norm(n) == norm(part)]
        if not found:
            if not os.path.lexists(os.path.join(here, part)):
                return None
            other = [n for n in names if n.casefold() == part.casefold()]
            return "/".join([*parts[:i], other[0] if other else "?", *parts[i + 1 :]])
        here = os.path.join(here, found[0])
    return None


def _git_knows(top: Path, rel: str) -> bool:
    """Whether git tracks, or would add, some path at or under ``rel``."""
    proc = _run(
        top, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *_spec([rel])
    )
    return proc.returncode == 0 and bool(proc.stdout.strip(b"\0"))


def normalize_paths(top: Path, raw: list[str]) -> list[str]:
    """Each path relative to ``top``, in posix form and git's spelling, checked to be real.

    A path must exist (or be a deletion of a path in HEAD) and be one git knows. Paths through a
    symlinked directory, inside a submodule, spelled in the wrong case on a case-insensitive
    filesystem, or holding only ignored files are refused: git would match nothing for them, and
    the module's work would be lost without a signal.
    """
    if not raw:
        raise InputError("no paths given: list at least one file or directory after --")
    real_top = os.path.realpath(top)
    precompose = _precomposes(top)
    out: list[str] = []
    for item in raw:
        if not item.strip():
            raise InputError("an empty path was given (an unfilled placeholder?)")
        absolute = item if os.path.isabs(item) else os.path.join(top, item)
        rel = os.path.relpath(os.path.normpath(absolute), top).replace(os.sep, "/")
        rel = posixpath.normpath(rel)
        if precompose:
            # git precomposes its own argv here, so it records and reports the NFC spelling.
            rel = unicodedata.normalize("NFC", rel)
        if rel == ".":
            raise InputError(f"{item!r} names the whole repository; list the paths to commit")
        if rel == ".." or rel.startswith("../"):
            raise InputError(f"{item!r} is outside the repository {top}")
        if rel == ".git" or rel.startswith(".git/"):
            raise InputError(f"{item!r} is inside .git")
        parent = os.path.realpath(os.path.join(top, posixpath.dirname(rel)))
        if parent != real_top and not parent.startswith(real_top + os.sep):
            raise InputError(f"{item!r} resolves outside the repository {top} (a symlink?)")
        disk = _misspelled(top, rel, precompose)
        if disk is not None:
            raise InputError(f"{item!r} is spelled differently on disk ({disk!r}): list it so")
        link = _symlink_component(top, rel)
        if link is not None:
            raise InputError(f"{item!r} passes through the symlink {link!r}: list the real path")
        exists = os.path.lexists(os.path.join(top, rel))
        if not exists and not _in_tree(top, "HEAD", rel):
            raise InputError(f"{item!r} does not exist and is not in HEAD (a wrong path?)")
        if exists and not _in_tree(top, "HEAD", rel):
            if _run(top, "check-ignore", "-q", "--no-index", "--", rel).returncode == 0:
                raise InputError(f"{item!r} is ignored by git and cannot be committed")
        if exists and not _git_knows(top, rel):
            raise InputError(
                f"{item!r} exists but git knows no file under it (a case mismatch, a path "
                "inside a submodule, or only ignored files?)"
            )
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
    precompose = _precomposes(top)
    for rel in differing:
        if rel not in present:
            disk = _misspelled(top, rel, precompose)
            if disk is not None:
                raise GitError(f"refusing to delete {rel}: spelled differently on disk ({disk})")
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


def _not_ours(top: Path, source: list[str]) -> list[str]:
    """The paths in ``source`` that would be exempt if ``explorer/`` were one a build made.

    Non-empty means the refusal is about ownership, not about those files: ``data/state.json``
    no longer holds the hash of ``data/model.json`` (or is missing), so nothing there is exempt.
    """
    from .build import is_our_explorer

    named = [p for p in source if is_explorer_output_name(p)]
    return named if named and not is_our_explorer(top / OUTPUT_DIR) else []


OWNERSHIP_LOST = (
    "explorer/ no longer reads as one a build made: data/state.json must be the file build "
    "wrote, with the hash of data/model.json's model"
)


def _refuse_source(top: Path, changed: list[str]) -> None:
    """``--no-content-check`` is for docs: refuse any changed path the verifier would judge."""
    source = [p for p in changed if not is_exempt(p, top)]
    if not source:
        return
    lost = _not_ours(top, source)
    why = f"{OWNERSHIP_LOST}, so these are not exempt: {', '.join(lost)}. " if lost else ""
    raise InputError(
        why + "--no-content-check commits only Markdown and the files a build writes in an "
        "explorer it made (the app, data/model.json, model.js, state.json), and these "
        f"changed paths are none of those: {', '.join(source)}. "
        "Commit them with --verify-against"
    )


def _stream(argv: list[str]) -> Iterator[str]:
    """The NUL-separated paths ``argv`` prints, one at a time.

    ``GitError`` after the last path when the command fails: a list cut short must not read as a
    complete one. A reader that stops early ends the command (the pipe closes, the writer gets
    SIGPIPE).
    """
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=err)
        assert proc.stdout is not None
        try:
            tail = b""
            while chunk := proc.stdout.read(_CHUNK):
                *whole, tail = (tail + chunk).split(b"\0")
                for raw in whole:
                    if raw:
                        yield raw.decode("utf-8", "surrogateescape")
            if tail:
                yield tail.decode("utf-8", "surrogateescape")
        finally:
            proc.stdout.close()
            code = proc.wait()
        if code != 0:
            err.seek(0)
            msg = err.read().decode("utf-8", "replace").strip()
            raise GitError(f"{argv[0]} failed with exit {code}: {msg}")


def ignore_rules(top: Path, paths: list[str]) -> dict[str, str]:
    """The rule that ignores each of ``paths``, as ``{path: "source:line:pattern"}``.

    ``git check-ignore --no-index -v``: ``source`` is the file the rule is in (``.gitignore``,
    ``docs/.gitignore``, ``.git/info/exclude``, or the absolute path of ``core.excludesFile``),
    ``line`` its line there. The index is not consulted, so a tracked path is judged by the rules
    like any other, and a path that does not exist yet like one that does. A path no rule
    ignores, or that a negated rule (``!pattern``) lets back in, is left out. ``GitError`` when
    git itself fails.
    """
    if not paths:
        return {}
    given = b"".join(p.encode("utf-8", "surrogateescape") + b"\0" for p in paths)
    argv = ["git", "-C", str(top), "check-ignore", "--no-index", "-v", "-z", "--stdin"]
    proc = subprocess.run(argv, input=given, capture_output=True, check=False)
    if proc.returncode not in (0, 1):  # 1: none of them is ignored
        msg = proc.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git check-ignore failed: {msg}")
    fields = proc.stdout.decode("utf-8", "surrogateescape").split("\0")
    rules: dict[str, str] = {}
    for i in range(0, len(fields) - 1, 4):  # source, line, pattern, path; one NUL after each
        source, line, pattern, path = fields[i : i + 4]
        if not pattern.startswith("!"):
            rules[path] = f"{source}:{line}:{pattern}"
    return rules


#: ``source:line:pattern``, the form ``ignore_rules`` returns. A source path may hold colons.
_RULE = re.compile(r"(?P<source>.+?):(?P<line>\d+):(?P<pattern>.*)", re.DOTALL)


def tracked_paths(top: Path, paths: list[str]) -> set[str]:
    """The ones among ``paths`` that the index holds (a path that does not exist can be one)."""
    if not paths:
        return set()
    held = _paths(top, "ls-files", "-z", "--cached", "--", *_spec(paths))
    return set(held) & set(paths)


def rule_in_place(top: Path, rule: str) -> bool:
    """Whether the rule ``source:line:pattern`` is still in its file.

    The pattern is looked for on every line, so a rule whose line moved is found. A negation the
    owner added after it is not noticed: this says the rule was not deleted, not that it still
    ignores the path. ``source`` is relative to ``top`` or absolute (``core.excludesFile``).
    """
    found = _RULE.fullmatch(rule)
    if found is None:
        return False
    pattern = found["pattern"].rstrip()
    try:
        with open(top / found["source"], encoding="utf-8") as fh:
            return any(line.rstrip("\r\n").rstrip() == pattern for line in fh)
    except (OSError, UnicodeDecodeError):
        return False


def left_out(top: Path, paths: list[str]) -> dict[str, str]:
    """``ignore_rules`` for the paths ``git add`` would skip: ignored and not tracked.

    Git keeps tracking a file that matches an ignore rule (a force-added one), and stages its
    changes, so a tracked path is not at risk.
    """
    rules = ignore_rules(top, paths)
    if not rules:
        return {}
    tracked = tracked_paths(top, list(rules))
    return {p: rule for p, rule in rules.items() if p not in tracked}


def _carried(top: Path, path: str, below: str) -> bool:
    """Whether a commit of the listed directory is expected to carry this ignored file.

    ``below`` is ``path`` relative to the listed directory. The commit is expected to carry what
    ``verify.is_exempt`` accepts: Markdown, and the files a build writes in an explorer it made.
    Source files are left out on purpose. The inventory lists with ``--exclude-standard``, so
    the skill never comments an ignored file, and ``local_settings.py`` or a virtualenv under a
    module is not work the commit would lose. A file under a dependency or build directory
    (``inventory.SKIP_DIRS``: ``node_modules``, ``.venv``, ``dist``, ``__pycache__``...) below the
    listed one is junk, Markdown included; the skill's own output is never junk, whatever it
    sits under (the template's ``explorer/vendor/``). ``.DS_Store``, ``*.pyc`` and swap files
    are not Markdown or build output at all.
    """
    junk = any(part in SKIP_DIRS for part in below.split("/")[:-1])
    return is_exempt(path, top) and (is_explorer_output_name(path) or not junk)


def _ignored_in(top: Path, roots: list[str]) -> tuple[list[str], int]:
    """The ignored, untracked files under the listed directories that a commit should carry.

    Returns the first ``IGNORED_SHOWN`` of them and the count of all. Listed files are skipped:
    ``normalize_paths`` already refused an ignored one, and a tracked one is never ignored by
    git. Streamed, so a huge ignored tree (``node_modules``) is read and dropped, not held.
    """
    dirs = [r for r in roots if os.path.isdir(top / r) and not os.path.islink(top / r)]
    shown: list[str] = []
    total = 0
    done: list[str] = []
    for root in dirs:
        argv = ["git", "-C", str(top), "ls-files", "--others", "--ignored", "--exclude-standard"]
        for path in _stream([*argv, "-z", "--", *_spec([root])]):
            if _under(path, done) or not _carried(top, path, path[len(root) + 1 :]):
                continue  # counted under a directory listed before it, or not ours to carry
            total += 1
            if len(shown) < IGNORED_SHOWN:
                shown.append(path)
        done.append(root)
    return shown, total


def _negation(top: Path, path: str, rule: str) -> str:
    """The line that lets ``path`` back in, and the file it goes in: "`!docs/gen/` in `.gitignore`".

    A negation cannot re-include a file whose directory is ignored, so when some directory above
    ``path`` is ignored (a ``gen/`` rule), the line names the shallowest one. Otherwise it names
    the file (a ``NOTES.md`` rule). The line is relative to the directory of the file it goes in:
    ``docs/.gitignore`` holds ``!gen/``, while ``.gitignore``, ``.git/info/exclude`` and a global
    excludes file hold the path from the repository root.
    """
    parts = path.split("/")
    dirs = ["/".join(parts[:i]) + "/" for i in range(1, len(parts))]
    found = ignore_rules(top, [*dirs, path])
    target = next((d for d in dirs if d in found), path)
    owner = _RULE.fullmatch(found.get(target, rule))
    assert owner is not None  # ``ignore_rules`` and the caller only make ``source:line:pattern``
    source = owner["source"]
    local = posixpath.basename(source) == ".gitignore" and not os.path.isabs(source)
    base = posixpath.dirname(source) if local else ""
    return f"`!{target[len(base) + 1 :] if base else target}` in `{source}`"


def _refuse_ignored(top: Path, roots: list[str]) -> None:
    """Refuse to commit a directory when git would leave part of it out, and say which part.

    ``git add -- explorer`` skips untracked files that match an ignore rule and does not say so:
    with ``data/`` in .gitignore, the explorer's ``data/model.json``, ``model.js`` and
    ``state.json`` stay out and the commit still reports ``ok``. The tool fails closed: nothing
    is staged, and the error names each file with the rule that ignores it
    (``source:line:pattern``). It never forces the file in (``git add -f``) and never edits
    .gitignore: a rule may be a privacy guard, so overriding it is the owner's decision.
    ``_carried`` says which ignored files count.
    """
    shown, total = _ignored_in(top, roots)
    if not total:
        return
    rules = ignore_rules(top, shown)
    named = ", ".join(f"{p} ({rules.get(p, 'rule not found')})" for p in shown)
    more = f" and {total - len(shown)} more" if total > len(shown) else ""
    # ``keep-local`` writes explorer/.gitignore. Its ``*`` is then the deciding rule for every file,
    # and a negation placed in it would let in one file, not the explorer.
    from .build import LOCAL_MARKER

    marker = f"{OUTPUT_DIR}/{LOCAL_MARKER}"
    kept = [p for p in shown if rules.get(p, "").startswith(marker + ":")]
    first = next((p for p in shown if p in rules and p not in kept), None)
    line = f" ({_negation(top, first, rules[first])})" if first is not None else ""
    local = (
        f" {marker} keeps this explorer local (`document_repo keep-local` wrote it): to commit "
        f"the explorer, delete {marker} first."
        if kept
        else ""
    )
    raise InputError(
        f"these files are ignored by git and would be left out of the commit: {named}{more}. "
        f"Add a negation rule{line} after the ignoring rule, or keep the directory "
        f"local.{local} This command does not edit .gitignore or force files in: that is the "
        "owner's call"
    )


def commit_paths(
    repo: Path,
    paths: list[str],
    messages: list[str],
    verify_against: str | None,
    skip_hooks: bool = False,
) -> Outcome:
    """Commit exactly ``paths`` and prove the commit; see the module docstring.

    ``verify_against`` is the ref every changed path must be comment-only against, or None for
    docs mode: only paths ``is_exempt`` accepts (Markdown, and the files a build writes in an
    explorer it made), content not checked.
    Raises ``InputError`` on bad input, before the repo is touched (an untracked file that git
    ignores under a listed directory, which ``git add`` would leave out, is bad input too). Once
    ``git commit`` has run,
    nothing raises: every failure is an ``Outcome``.
    """
    top = _top(repo)
    if not messages or not all(m.strip() for m in messages):
        raise InputError("the commit message is empty")
    pre = _resolve_commit(top, "HEAD", "HEAD")
    ref = None
    if verify_against is not None:
        ref = _resolve_commit(top, verify_against, "--verify-against")
        if _run(top, "merge-base", "--is-ancestor", ref, pre).returncode != 0:
            raise InputError(
                f"--verify-against {verify_against!r} is not an ancestor of HEAD "
                "(use HEAD, or the base sha for a restore commit)"
            )
    roots = normalize_paths(top, paths)
    if ref is None:
        _refuse_source(top, _changed(top, "HEAD", roots))
    _refuse_ignored(top, roots)

    _out(top, "reset", "-q")
    changed = _changed(top, "HEAD", roots)
    if not changed:
        return Outcome("skip", "nothing under the listed paths differs from HEAD", pre=pre)

    # Stage first, then verify: the verifier also checks the index mode against the ref, so it
    # judges exactly what will be committed (a restored file is in the index again). In git 2.x
    # ``git add <pathspec>`` stages deletions too.
    _out(top, "add", "--", *_spec(roots))
    if ref is not None:
        checks = [verify_file(top, rel, ref).to_dict() for rel in changed]
        if not all(r["ok"] for r in checks):
            _out(top, "reset", "-q")
            return Outcome(
                "precheck",
                f"a file is not comment-only against {ref[:12]}; nothing was committed",
                pre=pre,
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
    run = _Run(top, pre, ref, staged, roots, before, changed, skip_hooks)
    try:
        # The commit call is inside the try: an interrupt while it waits may come after the
        # commit landed.
        return _after_commit(run, _run(top, *argv, "--", *_spec(roots)))
    except BaseException as exc:  # any failure here may leave a commit on HEAD
        return _after_exception(run, exc)


@dataclass
class _Run:
    """The state of one ``commit_paths`` call once ``git commit`` has run."""

    top: Path
    pre: str
    ref: str | None
    staged: str
    roots: list[str]
    before: dict[str, str | None]
    changed: list[str]
    skip_hooks: bool


def _after_commit(run: _Run, proc: subprocess.CompletedProcess[bytes]) -> Outcome:
    top, pre, ref, roots = run.top, run.pre, run.ref, run.roots
    output = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip()
    head = _resolve_commit(top, "HEAD", "HEAD")
    if proc.returncode != 0:
        if head != pre:
            return Outcome(
                "stop",
                "git commit failed but HEAD moved; history was not touched",
                pre=pre,
                sha=head,
                git_output=output,
            )
        _out(top, "reset", "-q")
        restored = _restore(top, run.staged, roots)
        return Outcome(
            "commit-failed",
            _commit_failure(top, output, run.skip_hooks)
            + "; nothing was committed and the index is empty"
            + ("; the listed files were reset to the bytes that were staged" if restored else ""),
            pre=pre,
            paths=run.changed,
            restored=restored,
            strays=_strays(run.before, _dirty_snapshot(top, roots)),
            git_output=output,
        )

    parents = _out(top, "rev-list", "--parents", "-n", "1", head).split()[1:]
    if head == pre or parents != [pre]:
        return Outcome(
            "stop",
            "the commit is not exactly one new commit on the old HEAD (a hook made a commit?); "
            "history was not touched",
            pre=pre,
            sha=head,
            git_output=output,
        )
    committed = _paths(
        top, "diff-tree", "-r", "-z", "--no-commit-id", "--name-only", "--no-renames", pre, head
    )
    problem = None
    results: list[dict[str, Any]] = []
    extra = [p for p in committed if not _under(p, roots)]
    source = [p for p in committed if not is_exempt(p, top)] if ref is None else []
    differs = _changed(top, "HEAD", roots)
    if extra:
        problem = f"the commit also held {', '.join(extra)} (added by a hook?)"
    elif source and _not_ours(top, source):
        data = [p for p in committed if p.startswith(f"{OUTPUT_DIR}/data/")]
        problem = (
            f"the commit changed {', '.join(data) or 'explorer/data/'}, so {OWNERSHIP_LOST} "
            "(a hook reformatted or rewrote the model?). The other explorer files are fine"
        )
    elif source:
        problem = (
            f"the commit held {', '.join(source)}, which is not Markdown or explorer output "
            "(added by a hook?)"
        )
    elif differs:
        problem = (
            f"the work tree differs from the commit at {', '.join(differs)} (a hook changed "
            "files without staging them)"
        )
    elif ref is not None:
        results = [verify_file(top, rel, ref).to_dict() for rel in committed]
        if not all(r["ok"] for r in results):
            problem = (
                f"a committed file is not comment-only against {ref[:12]} (a hook rewrote it?)"
            )
            results = [r for r in results if not r["ok"]]
    if problem is None:
        detail = "committed and verified" if ref else "committed (content not checked: docs only)"
        # A hook that re-stages a file under ``git commit --only`` changes the commit, and the
        # real index keeps the bytes staged before the hook. The work tree equals the commit
        # (checked above), so the index is set to HEAD as well, leaving the tree clean.
        try:
            _out(top, "reset", "-q")
        except GitError as exc:
            detail += f"; the index could not be reset to HEAD ({exc})"
        return Outcome(
            "ok",
            detail,
            pre=pre,
            sha=head,
            paths=committed,
            strays=_strays(run.before, _dirty_snapshot(top, roots)),
            git_output=output,
        )
    return _undo(run, problem, committed, results, output)


def _take_back(run: _Run) -> list[str]:
    """Undo the commit on HEAD (checked to be ours) and restore the listed paths."""
    _out(run.top, "reset", "-q", "--soft", run.pre)
    _out(run.top, "reset", "-q")
    return _restore(run.top, run.pre if run.ref else run.staged, run.roots)


def _undo(
    run: _Run,
    problem: str,
    committed: list[str],
    results: list[dict[str, Any]],
    output: str,
) -> Outcome:
    bad = _resolve_commit(run.top, "HEAD", "HEAD")
    try:
        restored = _take_back(run)
    except BaseException as exc:  # report the bad commit, never "nothing was committed"
        try:
            moved = _resolve_commit(run.top, "HEAD", "HEAD") == run.pre
        except BaseException:  # the state cannot be read: say so
            moved = False
        state = f"commit {bad[:12]} was undone" if moved else f"commit {bad[:12]} may be on HEAD"
        return Outcome(
            "stop",
            f"{problem}; {state} but restoring the listed paths failed "
            f"({type(exc).__name__}: {exc})",
            pre=run.pre,
            sha=bad,
            paths=committed,
            verify=results,
            git_output=output,
        )
    to = "the old HEAD (the change is dropped)" if run.ref else "the bytes that were staged"
    return Outcome(
        "undone",
        f"{problem}; commit {bad[:12]} was undone and the listed paths reset to {to}",
        pre=run.pre,
        sha=bad,
        paths=committed,
        verify=results,
        restored=restored,
        strays=_strays(run.before, _dirty_snapshot(run.top, run.roots)),
        git_output=output,
    )


def _after_exception(run: _Run, exc: BaseException) -> Outcome:
    """Any failure once ``git commit`` ran: take our commit back if it is on HEAD, then ``stop``.

    The result is ``stop`` even when the undo worked, because the command could not finish its
    checks. ``detail`` says what happened to HEAD.
    """
    why = f"{type(exc).__name__}: {exc}"
    sha: str | None = None
    try:
        sha = _resolve_commit(run.top, "HEAD", "HEAD")
        parents = _out(run.top, "rev-list", "--parents", "-n", "1", sha).split()[1:]
        if sha == run.pre:
            _out(run.top, "reset", "-q")
            note = "HEAD did not move; nothing was committed and the index is empty"
        elif parents == [run.pre]:
            _take_back(run)
            note = f"commit {sha[:12]} was undone and the listed paths reset"
        else:
            note = "HEAD is not one new commit on the old HEAD, so history was not touched"
    except BaseException as inner:  # report, never raise, after the commit
        note = f"the undo failed too ({type(inner).__name__}: {inner}); HEAD may hold the commit"
    return Outcome("stop", f"an error after git commit ran ({why}); {note}", pre=run.pre, sha=sha)


def backstop(repo: Path, base: str) -> dict[str, Any]:
    """Verify every change on the branch since ``base`` and check the tree is clean.

    Returns ``{"ok", "base", "verify", "status"}``. ``InputError`` for a bad repo or base.
    """
    top = _top(repo)
    sha = _resolve_commit(top, base, "--base")
    if _run(top, "merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
        raise InputError(f"--base {base!r} is not an ancestor of HEAD")
    try:
        files = changed_files(top, sha)
    except subprocess.CalledProcessError as exc:
        why = (exc.stderr or b"").decode("utf-8", "replace").strip() or str(exc)
        raise GitError(f"git failed while listing the branch's changes: {why}") from exc
    results = [verify_file(top, rel, sha).to_dict() for rel in files]
    raw = _out(top, "status", "--porcelain=v1", "-z", "-uall")
    status = [e for e in raw.split("\0") if e]
    ok = all(r["ok"] for r in results) and not status
    return {"ok": ok, "base": sha, "verify": results, "status": status}
