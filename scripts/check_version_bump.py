#!/usr/bin/env python3
"""
Release-integrity CI gate (stdlib only) -- issues #226 and #210.

Two defects motivate this script, and they pull in OPPOSITE directions on one
single path, which is why this is ONE script with TWO conditional rules rather
than two independent gates:

  #226 -- PR #222 shipped 42 items of behavior change under `plugins/` at an
          UNCHANGED version 11.5.1. `claude plugin update` compares version
          strings, so an unbumped change leaves two materially different trees
          under one version and every installed cache reports "already up to
          date" forever. Nobody ever gets the change. Every gate was green:
          version bumping is a `/bump-version` step, not a check;
          `claude plugin validate --strict` checks manifest SHAPE, not
          CURRENCY; `update-readme.py --check` is version-blind.

  #210  -- the per-plugin `CHANGELOG.md` files had fallen 28 entries behind the
          root `CHANGELOG.md`, including all three plugins' currently-shipped
          versions. A bump with no changelog entry is a silent release.

The rules:

  Rule 1 (bump-required)
      If any BUMP-WORTHY path under `plugins/<name>/` changed, then
      `plugins/<name>/.claude-plugin/plugin.json`'s `version` MUST have changed.

  Rule 2 (changelog-required)
      If `plugins/<name>/.claude-plugin/plugin.json`'s `version` changed, then
      `plugins/<name>/CHANGELOG.md` MUST contain an entry for the NEW version.

`plugins/<name>/CHANGELOG.md` is EXEMPT from Rule 1 and MANDATORY under
Rule 2. That conditional is the entire reason these are not two gates: this
plan's own item 1.1 was a CHANGELOG-only backfill with no version bump, and a
naive "anything under plugins/ requires a bump" gate would have rejected it.

Both rules are evaluated PER PLUGIN. "Any plugin changed => all three must
bump" is explicitly forbidden by D45 (no empty coordinated bumps).

BOTH sides of every comparison are derived from git (`git show <ref>:<path>`),
never from a constant restated in this file. There are no hardcoded version
numbers and no hardcoded plugin names -- plugins are discovered by globbing
`plugins/*/.claude-plugin/plugin.json` in the git tree at the head ref.
CLAUDE.md: "A check that restates an external truth will drift into agreeing
with the bug -- derive it, don't copy it."

EVENT LEGS
----------
`.github/workflows/validate.yml` triggers on BOTH `push: [main]` and
`pull_request: [main]`. On the push-to-main leg there is no meaningful base --
a naive `git diff origin/main...HEAD` diffs main against itself, finds an
empty diff, and silently passes. This script therefore branches EXPLICITLY on
`GITHUB_EVENT_NAME` and exits 0 with an explanation on the push leg; the PR leg
already gated that exact content before it merged.

That branch is itself the E043 hazard ("a verification guard that can't fail is
worse than none" -- this repo has shipped three). A leg condition written wrong
no-ops on BOTH legs and converts "unchecked" into a false "checked". `--self-test`
therefore asserts the SAME violating tree exits 1 on the pull_request leg and 0
on the push leg, and asserts exit 1 on every violation class -- not merely
exit 0 on the happy path.

Usage:
    python3 scripts/check_version_bump.py                  # CI: leg from env
    python3 scripts/check_version_bump.py --base main      # local override
    python3 scripts/check_version_bump.py --self-test      # negative-test it

Exit codes:
    0 - all rules satisfied, nothing to check, or non-PR event leg
    1 - at least one rule violated (or misconfigured leg, or self-test failed)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REPO_ROOT = Path(__file__).resolve().parent.parent

PLUGINS_DIR = "plugins"
MANIFEST_REL = ".claude-plugin/plugin.json"
CHANGELOG_REL = "CHANGELOG.md"

# ---------------------------------------------------------------------------
# Rule 1's exemption set -- the SINGLE source of truth, used by both the
# classifier and --self-test's fixtures. Derived from the 375-file census in
# IMPLEMENTATION_PLAN.md 2.2: everything under `plugins/<name>/` is bump-worthy
# EXCEPT these. Paths are relative to `plugins/<name>/` and always POSIX.
#
# CHANGELOG.md is exempt here and mandatory under Rule 2 -- see module docstring.
# ---------------------------------------------------------------------------
EXEMPT_EXACT: tuple[str, ...] = (
    CHANGELOG_REL,
    "LICENSE",
    "README.md",
)

# Segment-wise globs. `*` matches exactly one path segment; `**` matches one or
# more trailing segments. Deliberately NOT fnmatch: fnmatch translates `*` to
# `.*`, which spans `/`, so `tools/*/tests/**` would also exempt
# `tools/x/src/tests/y.py` -- a source-tree directory that merely happens to be
# named `tests`. The exemption is for a tool's own top-level test suite only.
EXEMPT_GLOBS: tuple[str, ...] = (
    "tools/*/tests/**",
    "examples/**",
)


def _glob_matches(glob: str, rel_path: str) -> bool:
    """Segment-wise match. `*` = exactly one segment, `**` = one or more
    trailing segments (must be the final pattern segment)."""
    pattern = glob.split("/")
    parts = rel_path.split("/")
    for i, seg in enumerate(pattern):
        if seg == "**":
            # `**` is only meaningful as the last pattern segment and requires
            # at least one remaining path segment.
            return i < len(parts)
        if i >= len(parts):
            return False
        if seg == "*":
            continue
        if seg != parts[i]:
            return False
    return len(parts) == len(pattern)


def is_bump_worthy(rel_path: str) -> bool:
    """True if a change to `plugins/<name>/<rel_path>` obliges a version bump."""
    if rel_path in EXEMPT_EXACT:
        return False
    return not any(_glob_matches(g, rel_path) for g in EXEMPT_GLOBS)


# ---------------------------------------------------------------------------
# git plumbing -- subprocess only; no third-party dependency. The
# `plugin-validate` job has no `setup-python` step and every existing script
# step in it is stdlib-only; an import here would force a new CI step.
# ---------------------------------------------------------------------------


class GitError(RuntimeError):
    pass


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def git_try(repo: Path, *args: str) -> str | None:
    try:
        return git(repo, *args)
    except GitError:
        return None


def rev_parse(repo: Path, ref: str) -> str | None:
    out = git_try(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    return out.strip() if out else None


def show(repo: Path, ref: str, path: str) -> str | None:
    """File content at `ref`, or None if the path does not exist there."""
    return git_try(repo, "show", f"{ref}:{path}")


def changed_paths(repo: Path, base: str, head: str) -> list[str]:
    """Paths differing between merge-base(base, head) and head.

    `--no-renames` so a rename surfaces as BOTH the deleted and the added path;
    with rename detection on, `--name-only` reports the destination only, which
    would hide a bump-worthy file being moved OUT of a plugin.
    """
    out = git(repo, "diff", "--name-only", "--no-renames", f"{base}...{head}")
    return [line for line in out.splitlines() if line.strip()]


def plugins_at(repo: Path, ref: str) -> list[str]:
    """Plugin names discovered by globbing `plugins/*/.claude-plugin/plugin.json`
    in the git tree at `ref`. Never a hardcoded list."""
    out = git(repo, "ls-tree", "-r", "--name-only", ref, "--", PLUGINS_DIR)
    names: set[str] = set()
    for line in out.splitlines():
        parts = line.strip().split("/")
        if len(parts) >= 4 and parts[0] == PLUGINS_DIR:
            if "/".join(parts[2:]) == MANIFEST_REL:
                names.add(parts[1])
    return sorted(names)


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

RULE_LABELS = {
    "R1": "Rule 1: bump-required",
    "R2": "Rule 2: changelog-required",
    "R0": "Rule 0: unreadable manifest",
}


@dataclass(frozen=True)
class Finding:
    rule: str
    plugin: str
    summary: str
    details: tuple[str, ...] = ()
    remediation: str = ""

    def render(self) -> str:
        lines = [f"  [{RULE_LABELS[self.rule]}] {self.plugin}", f"      {self.summary}"]
        for d in self.details:
            lines.append(f"        - {d}")
        if self.remediation:
            lines.append(f"      Fix: {self.remediation}")
        return "\n".join(lines)


def manifest_version(repo: Path, ref: str, plugin: str) -> tuple[str | None, str | None]:
    """(version, error). version is None when the manifest is absent at `ref`."""
    path = f"{PLUGINS_DIR}/{plugin}/{MANIFEST_REL}"
    raw = show(repo, ref, path)
    if raw is None:
        return None, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"{path} at {ref} is not valid JSON: {exc}"
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        return None, f"{path} at {ref} has no usable string `version` field"
    return version.strip(), None


def changelog_has_entry(text: str, version: str) -> bool:
    """True if the changelog text has a markdown heading naming `version`.

    Accepts the Keep-a-Changelog form this repo uses (`## [1.2.3] - 2026-07-29`)
    and the bare form (`## 1.2.3`). The trailing negative lookahead stops
    `1.2.3` from matching a `## [1.2.30]` heading.

    Deliberately asserts EXISTENCE ONLY -- it does NOT compare the release date
    against the root CHANGELOG.md. Seven versions already on `main` have dates
    that disagree between the two files (one is literally dated `Previous`);
    asserting parity would turn this gate red on legacy history the day it lands
    and deadlock every merge.
    """
    pattern = re.compile(
        r"^\s{0,3}#{1,6}[ \t]+\[?" + re.escape(version) + r"\]?(?![0-9A-Za-z.\-])",
        re.MULTILINE,
    )
    return bool(pattern.search(text))


def check(repo: Path, base: str, head: str) -> list[Finding]:
    findings: list[Finding] = []
    changed = changed_paths(repo, base, head)

    # Candidate plugins: those present at head, plus any name appearing in the
    # diff (so a plugin added in this PR is covered even though it is absent
    # from the base tree).
    candidates: set[str] = set(plugins_at(repo, head))
    for path in changed:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == PLUGINS_DIR:
            candidates.add(parts[1])

    for plugin in sorted(candidates):
        prefix = f"{PLUGINS_DIR}/{plugin}/"
        touched = [p for p in changed if p.startswith(prefix)]

        new_version, new_err = manifest_version(repo, head, plugin)
        if new_version is None and new_err is None:
            # No manifest at head: either a deleted plugin or a stray directory.
            # Nothing to bump and nothing to changelog.
            continue
        if new_err is not None:
            if touched:
                findings.append(
                    Finding(
                        rule="R0",
                        plugin=plugin,
                        summary=new_err,
                        remediation="repair the manifest, then re-run this check",
                    )
                )
            continue

        old_version, old_err = manifest_version(repo, base, plugin)
        if old_err is not None:
            # Base manifest is broken; treat as "no comparable prior version"
            # rather than blaming this PR for pre-existing damage.
            old_version = None

        # Both `None` paths for new_version are already handled above: absent
        # manifest -> continue (line ~289), unparseable manifest -> R0 + continue.
        # The assert is purely a type-narrowing aid -- Pyright cannot follow the
        # compound `new_version is None and new_err is None` guard, and without it
        # reports a false positive on the changelog_has_entry call below. It must
        # stay an assert, not a branch: a runtime branch here would be dead code
        # that looks like a handled case and invites someone to "fix" the guard
        # above by deleting it.
        assert new_version is not None

        version_changed = old_version != new_version
        bump_worthy = sorted(p for p in touched if is_bump_worthy(p[len(prefix):]))

        # --- Rule 1 --------------------------------------------------------
        if bump_worthy and not version_changed:
            shown = bump_worthy[:8]
            more = len(bump_worthy) - len(shown)
            details = list(shown) + ([f"...and {more} more"] if more else [])
            findings.append(
                Finding(
                    rule="R1",
                    plugin=plugin,
                    summary=(
                        f"{len(bump_worthy)} bump-worthy file(s) changed but "
                        f"{PLUGINS_DIR}/{plugin}/{MANIFEST_REL} still says version "
                        f"{new_version!r}. Without a bump, `claude plugin update` reports "
                        f'"already up to date" and nobody ever receives this change (#226).'
                    ),
                    details=tuple(details),
                    remediation=f"/bump-version {plugin} <major|minor|patch>",
                )
            )

        # --- Rule 2 --------------------------------------------------------
        if version_changed:
            changelog_path = f"{PLUGINS_DIR}/{plugin}/{CHANGELOG_REL}"
            text = show(repo, head, changelog_path)
            if text is None:
                findings.append(
                    Finding(
                        rule="R2",
                        plugin=plugin,
                        summary=(
                            f"version changed {old_version or '(new plugin)'} -> {new_version} "
                            f"but {changelog_path} does not exist (#210)."
                        ),
                        remediation=(
                            f"create {changelog_path} with a `## [{new_version}] - YYYY-MM-DD` "
                            f"section (/bump-version {plugin} <level> scaffolds it)"
                        ),
                    )
                )
            elif not changelog_has_entry(text, new_version):
                findings.append(
                    Finding(
                        rule="R2",
                        plugin=plugin,
                        summary=(
                            f"version changed {old_version or '(new plugin)'} -> {new_version} "
                            f"but {changelog_path} has no entry for {new_version} (#210)."
                        ),
                        remediation=(
                            f"add a `## [{new_version}] - YYYY-MM-DD` section to "
                            f"{changelog_path} (/bump-version {plugin} <level> adds the "
                            f"placeholder; fill it in before pushing)"
                        ),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Event-leg resolution -- the highest-risk part of this script. See docstring.
# ---------------------------------------------------------------------------

PR_EVENTS = ("pull_request", "pull_request_target")
DEFAULT_LOCAL_BASE = "main"


@dataclass(frozen=True)
class Leg:
    action: str  # "diff" | "skip" | "error"
    base_ref: str | None
    message: str


def resolve_leg(env: Mapping[str, str], base_arg: str | None) -> Leg:
    if base_arg:
        return Leg("diff", base_arg, f"explicit --base {base_arg!r}")

    event = env.get("GITHUB_EVENT_NAME", "").strip()

    if event in PR_EVENTS:
        base_ref = env.get("GITHUB_BASE_REF", "").strip()
        if not base_ref:
            return Leg(
                "error",
                None,
                f"GITHUB_EVENT_NAME={event!r} but GITHUB_BASE_REF is empty -- refusing to "
                "guess a base. Failing closed rather than silently passing.",
            )
        return Leg("diff", base_ref, f"{event} leg, base ref {base_ref!r}")

    if event == "push":
        return Leg(
            "skip",
            None,
            "push leg: there is no meaningful diff base (a `main...HEAD` diff compares "
            "main against itself and always passes vacuously). The pull_request leg "
            "already gated this exact content before it merged. Exiting 0 by design.",
        )

    if event:
        return Leg("skip", None, f"event {event!r} is not a pull_request or push leg. Exiting 0.")

    return Leg(
        "diff",
        DEFAULT_LOCAL_BASE,
        f"local run (no GITHUB_EVENT_NAME); base {DEFAULT_LOCAL_BASE!r}",
    )


def resolve_base_commit(repo: Path, base_ref: str) -> tuple[str | None, list[str]]:
    """Resolve a base ref name to a commit, trying `origin/<ref>` first.

    In CI, `actions/checkout` creates no local branch for the base, so a bare
    `main` does not resolve but `origin/main` does. Locally, `origin/main` is
    the source of truth per CLAUDE.md ("the local working tree can silently lag
    origin"), so preferring it is also the house rule. Fixture repos have no
    remote, which exercises the fallback.
    """
    candidates = [base_ref] if "/" in base_ref else [f"origin/{base_ref}", base_ref]
    for cand in candidates:
        sha = rev_parse(repo, cand)
        if sha:
            return sha, candidates
    return None, candidates


def run(
    repo: Path,
    env: Mapping[str, str],
    base_arg: str | None = None,
    head: str = "HEAD",
    stream: TextIO | None = None,
) -> int:
    out = stream if stream is not None else sys.stdout

    def emit(line: str = "") -> None:
        print(line, file=out)

    leg = resolve_leg(env, base_arg)

    if leg.action == "skip":
        emit(f"check_version_bump: SKIP -- {leg.message}")
        return 0
    if leg.action == "error":
        emit(f"check_version_bump: FAIL -- {leg.message}")
        return 1

    assert leg.base_ref is not None
    base_sha, tried = resolve_base_commit(repo, leg.base_ref)
    if base_sha is None:
        emit(
            f"check_version_bump: FAIL -- could not resolve a base commit for "
            f"{leg.base_ref!r} (tried: {', '.join(tried)}). If this is CI, the "
            f"`plugin-validate` job needs `fetch-depth: 0` on its checkout step."
        )
        return 1

    head_sha = rev_parse(repo, head)
    if head_sha is None:
        emit(f"check_version_bump: FAIL -- could not resolve head ref {head!r}.")
        return 1

    try:
        findings = check(repo, base_sha, head_sha)
    except GitError as exc:
        emit(
            f"check_version_bump: FAIL -- {exc}\n"
            f"  A shallow clone has no merge-base; the `plugin-validate` job needs "
            f"`fetch-depth: 0`."
        )
        return 1

    emit(f"check_version_bump: {leg.message}")
    emit(f"  base {base_sha[:7]} ... head {head_sha[:7]}")

    if not findings:
        emit("  OK -- every changed plugin is bumped, and every bump has a CHANGELOG entry.")
        return 0

    emit()
    emit(f"check_version_bump: FAILED -- {len(findings)} release-integrity violation(s):")
    emit()
    for finding in findings:
        emit(finding.render())
        emit()
    emit(
        "  Rule 1 (bump-required): a bump-worthy change under plugins/<name>/ requires a "
        "version bump in that plugin's plugin.json (#226)."
    )
    emit(
        "  Rule 2 (changelog-required): a version bump requires a matching entry in that "
        "plugin's CHANGELOG.md (#210)."
    )
    emit(
        f"  Exempt from Rule 1: {', '.join(EXEMPT_EXACT)}, {', '.join(EXEMPT_GLOBS)}."
    )
    return 1


# ---------------------------------------------------------------------------
# --self-test
#
# CLAUDE.md, standing rule: "a verification guard that can't fail is worse than
# none -- negative-test every new gate before wiring it in. It converts
# 'unchecked' into a false 'checked'." This repo has shipped three such guards.
#
# So this self-test asserts exit 1 on EVERY violation class, not merely exit 0
# on the happy path, and it asserts the SAME violating tree behaves differently
# on the two event legs -- a leg condition written wrong no-ops on both.
#
# Exemption fixtures are GENERATED FROM `EXEMPT_EXACT` / `EXEMPT_GLOBS`, not
# from a hand-typed second list that could drift alongside a bug (#208), and
# every glob is paired with an out-of-set neighbour (`tools/demo/src/app.py`
# next to `tools/*/tests/**`) because bugs of this class live entirely in the
# unrecognized-value branch.
# ---------------------------------------------------------------------------

PR_ENV = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main"}
PUSH_ENV = {"GITHUB_EVENT_NAME": "push", "GITHUB_REF_NAME": "main"}

FIXTURE_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_AUTHOR_NAME": "selftest",
    "GIT_AUTHOR_EMAIL": "selftest@example.invalid",
    "GIT_COMMITTER_NAME": "selftest",
    "GIT_COMMITTER_EMAIL": "selftest@example.invalid",
    "GIT_TERMINAL_PROMPT": "0",
}


def _fixture_git(repo: Path, *args: str) -> None:
    env = dict(os.environ)
    env.update(FIXTURE_GIT_ENV)
    proc = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, env=env
    )
    if proc.returncode != 0:
        raise GitError(f"fixture git {' '.join(args)}: {proc.stderr.strip()}")


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _changelog(plugin: str, versions: list[str]) -> str:
    body = [f"# Changelog\n\nAll notable changes to {plugin}.\n"]
    for v in versions:
        body.append(f"## [{v}] - 2026-01-01\n\n### Added\n\n- entry for {v}\n")
    return "\n".join(body)


def _manifest(plugin: str, version: str) -> str:
    data = {"name": plugin, "description": "fixture", "version": version}
    return json.dumps(data, indent=2) + "\n"


def _glob_fixture_path(glob: str) -> str:
    """Turn an EXEMPT_GLOBS pattern into a concrete file path. Derived from the
    constant so a new exemption automatically gains a fixture."""
    parts = []
    for seg in glob.split("/"):
        if seg == "**":
            parts.append("nested/file.txt")
        elif seg == "*":
            parts.append("demo")
        else:
            parts.append(seg)
    return "/".join(parts)


def _build_base_tree(root: Path) -> None:
    _write(root, "README.md", "repo root readme\n")
    for plugin, version in (("alpha", "1.0.0"), ("beta", "2.0.0")):
        base = f"{PLUGINS_DIR}/{plugin}"
        _write(root, f"{base}/{MANIFEST_REL}", _manifest(plugin, version))
        _write(root, f"{base}/{CHANGELOG_REL}", _changelog(plugin, [version]))
        _write(root, f"{base}/README.md", f"{plugin} readme\n")
        _write(root, f"{base}/LICENSE", "MIT\n")
        _write(root, f"{base}/skills/demo/SKILL.md", "---\nname: demo\n---\n\nbody\n")
        _write(root, f"{base}/tools/demo/src/app.py", "print('hi')\n")
        for glob in EXEMPT_GLOBS:
            _write(root, f"{base}/{_glob_fixture_path(glob)}", "fixture\n")


def _bump(root: Path, plugin: str, version: str) -> None:
    _write(root, f"{PLUGINS_DIR}/{plugin}/{MANIFEST_REL}", _manifest(plugin, version))


def _add_changelog_entry(root: Path, plugin: str, version: str) -> None:
    path = root / PLUGINS_DIR / plugin / CHANGELOG_REL
    existing = path.read_text(encoding="utf-8")
    marker = "\n## ["
    head, sep, tail = existing.partition(marker)
    entry = f"## [{version}] - 2026-07-30\n\n### Added\n\n- entry for {version}\n\n"
    path.write_text(head + "\n" + entry + sep[1:] + tail, encoding="utf-8")


def _touch(root: Path, rel: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    prior = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(prior + "\n# touched by self-test\n", encoding="utf-8")


# --- mutations -------------------------------------------------------------


def _m_rule1_skill_edit(root: Path) -> None:
    _touch(root, f"{PLUGINS_DIR}/alpha/skills/demo/SKILL.md")


def _m_changelog_only(root: Path) -> None:
    _touch(root, f"{PLUGINS_DIR}/alpha/{CHANGELOG_REL}")


def _m_readme_license_only(root: Path) -> None:
    for rel in EXEMPT_EXACT:
        if rel == CHANGELOG_REL:
            continue
        _touch(root, f"{PLUGINS_DIR}/alpha/{rel}")


def _m_exempt_globs(root: Path) -> None:
    for glob in EXEMPT_GLOBS:
        _touch(root, f"{PLUGINS_DIR}/alpha/{_glob_fixture_path(glob)}")


def _m_tools_src_edit(root: Path) -> None:
    _touch(root, f"{PLUGINS_DIR}/alpha/tools/demo/src/app.py")


def _m_bump_without_entry(root: Path) -> None:
    _touch(root, f"{PLUGINS_DIR}/alpha/skills/demo/SKILL.md")
    _bump(root, "alpha", "1.1.0")


def _m_new_plugin_no_changelog(root: Path) -> None:
    _write(root, f"{PLUGINS_DIR}/gamma/{MANIFEST_REL}", _manifest("gamma", "1.0.0"))
    _write(root, f"{PLUGINS_DIR}/gamma/skills/x/SKILL.md", "---\nname: x\n---\n")


def _m_clean_bump(root: Path) -> None:
    _touch(root, f"{PLUGINS_DIR}/alpha/skills/demo/SKILL.md")
    _bump(root, "alpha", "1.1.0")
    _add_changelog_entry(root, "alpha", "1.1.0")


def _m_clean_alpha_dirty_beta(root: Path) -> None:
    _m_clean_bump(root)
    _touch(root, f"{PLUGINS_DIR}/beta/skills/demo/SKILL.md")


def _m_both_rules(root: Path) -> None:
    _touch(root, f"{PLUGINS_DIR}/alpha/skills/demo/SKILL.md")
    _touch(root, f"{PLUGINS_DIR}/beta/skills/demo/SKILL.md")
    _bump(root, "beta", "2.1.0")


def _m_root_file_only(root: Path) -> None:
    _touch(root, "README.md")


def _m_manifest_only_clean(root: Path) -> None:
    _bump(root, "alpha", "1.1.0")
    _add_changelog_entry(root, "alpha", "1.1.0")


def _m_plugin_manifest_removed_changelog_kept(root: Path) -> None:
    # Delete alpha's manifest but LEAVE its CHANGELOG in place. `manifest_version`
    # returns (None, None) for an absent manifest -- no parse error -- so this is
    # the one shape that reaches the `new_version is None and new_err is None`
    # guard with a non-empty `touched` list. Removing a plugin is a legitimate
    # diff and must exit 0: there is no version left to bump and no changelog
    # entry to require. This case pins that guard, which is otherwise the only
    # thing standing between Rule 2 and `changelog_has_entry(text, None)`.
    (root / "plugins" / "alpha" / ".claude-plugin" / "plugin.json").unlink()


def _m_substring_collision_entry(root: Path) -> None:
    # Bump to 1.1.0 but document 11.1.0 -- "1.1.0" IS a substring of "11.1.0",
    # so a naive `version in text` check reports a false PASS here. This case
    # is what forces the heading-anchored regex; it kills that mutant.
    _bump(root, "alpha", "1.1.0")
    _add_changelog_entry(root, "alpha", "11.1.0")


def _m_trailing_digit_entry(root: Path) -> None:
    # Bump to 1.1.1 but document 1.1.10 -- the new version is a prefix of the
    # documented heading, which an anchored-but-unbounded regex would accept.
    # This case is what forces the trailing negative lookahead.
    _bump(root, "alpha", "1.1.1")
    _add_changelog_entry(root, "alpha", "1.1.10")


@dataclass(frozen=True)
class Case:
    name: str
    mutate: object
    env: Mapping[str, str]
    base_arg: str | None
    expect_exit: int
    expect_rules: frozenset  # of (rule, plugin) pairs
    expect_in_output: tuple[str, ...] = ()


SELF_TEST_CASES: tuple[Case, ...] = (
    Case(
        "rule1-violation-skill-edit",
        _m_rule1_skill_edit,
        PR_ENV,
        None,
        1,
        frozenset({("R1", "alpha")}),
        ("alpha", "Rule 1: bump-required", "/bump-version alpha"),
    ),
    Case("rule1-exempt-changelog-only", _m_changelog_only, PR_ENV, None, 0, frozenset()),
    Case("rule1-exempt-readme-license", _m_readme_license_only, PR_ENV, None, 0, frozenset()),
    Case("rule1-exempt-derived-globs", _m_exempt_globs, PR_ENV, None, 0, frozenset()),
    Case(
        "rule1-fires-on-tools-src (out-of-set neighbour of tools/*/tests/**)",
        _m_tools_src_edit,
        PR_ENV,
        None,
        1,
        frozenset({("R1", "alpha")}),
    ),
    Case(
        "rule2-violation-bump-without-entry",
        _m_bump_without_entry,
        PR_ENV,
        None,
        1,
        frozenset({("R2", "alpha")}),
        ("Rule 2: changelog-required", "1.0.0 -> 1.1.0"),
    ),
    Case(
        "rule2-violation-new-plugin-no-changelog",
        _m_new_plugin_no_changelog,
        PR_ENV,
        None,
        1,
        frozenset({("R2", "gamma")}),
    ),
    Case(
        "rule2-violation-substring-collision (bump 1.1.0, documented 11.1.0)",
        _m_substring_collision_entry,
        PR_ENV,
        None,
        1,
        frozenset({("R2", "alpha")}),
    ),
    Case(
        "rule2-violation-trailing-digit (bump 1.1.1, documented 1.1.10)",
        _m_trailing_digit_entry,
        PR_ENV,
        None,
        1,
        frozenset({("R2", "alpha")}),
    ),
    Case(
        "pass-clean-bump-and-entry (D45: beta untouched, not dragged)",
        _m_clean_bump,
        PR_ENV,
        None,
        0,
        frozenset(),
    ),
    Case(
        "pass-manifest-only-bump-with-entry",
        _m_manifest_only_clean,
        PR_ENV,
        None,
        0,
        frozenset(),
    ),
    Case("pass-no-plugin-changes", _m_root_file_only, PR_ENV, None, 0, frozenset()),
    Case(
        "plugin-manifest-removed-changelog-kept (must not crash)",
        _m_plugin_manifest_removed_changelog_kept,
        PR_ENV,
        None,
        0,
        frozenset(),
    ),
    Case(
        "per-plugin-isolation (alpha clean, beta dirty -> only beta fires)",
        _m_clean_alpha_dirty_beta,
        PR_ENV,
        None,
        1,
        frozenset({("R1", "beta")}),
    ),
    Case(
        "both-rules-fire-independently",
        _m_both_rules,
        PR_ENV,
        None,
        1,
        frozenset({("R1", "alpha"), ("R2", "beta")}),
    ),
    Case(
        "push-leg-noop (SAME violating tree as case 1)",
        _m_rule1_skill_edit,
        PUSH_ENV,
        None,
        0,
        frozenset(),
        ("SKIP", "push leg"),
    ),
    Case(
        "explicit --base override with empty env",
        _m_rule1_skill_edit,
        {},
        "main",
        1,
        frozenset({("R1", "alpha")}),
    ),
    Case(
        "pull_request leg with empty GITHUB_BASE_REF fails closed",
        _m_rule1_skill_edit,
        {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": ""},
        None,
        1,
        frozenset(),
        ("refusing to guess a base",),
    ),
)


def _build_case_repo(tmp: Path, case: Case) -> Path:
    repo = tmp / re.sub(r"[^a-z0-9]+", "-", case.name.lower())[:40]
    repo.mkdir(parents=True, exist_ok=True)
    _fixture_git(repo, "init", "-q", "-b", "main")
    _build_base_tree(repo)
    _fixture_git(repo, "add", "-A", "-f")
    _fixture_git(repo, "commit", "-q", "-m", "base")
    _fixture_git(repo, "checkout", "-q", "-b", "feature")
    case.mutate(repo)  # type: ignore[operator]
    _fixture_git(repo, "add", "-A", "-f")
    _fixture_git(repo, "commit", "-q", "-m", "head")
    return repo


def self_test() -> int:
    import io

    print("=== check_version_bump.py --self-test ===\n")
    print(f"-- Rule 1 exemptions under test (derived from constants): "
          f"{list(EXEMPT_EXACT)} + {list(EXEMPT_GLOBS)} --\n")

    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="check_version_bump_selftest_") as tmpdir:
        tmp = Path(tmpdir)
        for case in SELF_TEST_CASES:
            try:
                repo = _build_case_repo(tmp, case)
            except GitError as exc:
                failures.append(f"{case.name}: fixture build failed: {exc}")
                print(f"  [FAIL] {case.name}: fixture build failed: {exc}")
                continue

            buf = io.StringIO()
            # `check()` is re-run so the rule/plugin pairs can be asserted, not
            # just the exit code -- an exit code alone cannot tell "failed for
            # the right reason" from "failed for an unrelated one".
            code = run(repo, case.env, case.base_arg, "HEAD", stream=buf)
            output = buf.getvalue()

            problems: list[str] = []
            if code != case.expect_exit:
                problems.append(f"exit {code}, expected {case.expect_exit}")

            if case.expect_rules or case.expect_exit == 1:
                leg = resolve_leg(case.env, case.base_arg)
                if leg.action == "diff" and leg.base_ref:
                    base_sha, _ = resolve_base_commit(repo, leg.base_ref)
                    if base_sha:
                        got = frozenset((f.rule, f.plugin) for f in check(repo, base_sha, "HEAD"))
                        if got != case.expect_rules:
                            problems.append(
                                f"rules {sorted(got)}, expected {sorted(case.expect_rules)}"
                            )

            for needle in case.expect_in_output:
                if needle not in output:
                    problems.append(f"output missing {needle!r}")

            status = "PASS" if not problems else "FAIL"
            print(f"  [{status}] exit={code} expect={case.expect_exit}  {case.name}")
            if problems:
                for p in problems:
                    print(f"           -> {p}")
                print("           --- captured output ---")
                for line in output.splitlines():
                    print(f"           | {line}")
                failures.append(f"{case.name}: " + "; ".join(problems))

    print()
    violation_cases = [c for c in SELF_TEST_CASES if c.expect_exit == 1]
    print(
        f"-- {len(violation_cases)} of {len(SELF_TEST_CASES)} cases assert exit 1 "
        f"(this gate CAN fail) --"
    )

    if failures:
        print(f"\nself-test FAILED -- {len(failures)} problem(s):\n")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nself-test PASSED -- every violation exits 1, every exemption exits 0, "
          "and the push leg no-ops on a tree the PR leg rejects.")
    return 0


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Enforce Rule 1 (a bump-worthy change under plugins/<name>/ requires a version "
            "bump) and Rule 2 (a version bump requires a CHANGELOG entry for the new version)."
        )
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Base ref to diff against (overrides event-leg detection). Local use.",
    )
    parser.add_argument("--head", default="HEAD", help="Head ref to diff (default: HEAD).")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Negative-test this checker against synthetic git repos and exit.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    return run(REPO_ROOT, os.environ, args.base, args.head)


if __name__ == "__main__":
    sys.exit(main())
