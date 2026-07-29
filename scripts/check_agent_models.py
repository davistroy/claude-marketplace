#!/usr/bin/env python3
"""
Agent model-alias enforcement CI check (stdlib only) -- ADR-0005 / D20.

Both frontmatter validators wired into `plugin-validate` enumerate
`commands/` and `skills/` only; `agents/` was never added, and
`.claude/agents/` lives outside `plugins/` entirely, so no job in this repo
has ever walked agent frontmatter. That gap is exactly how the defect ADR-0005
records happened *twice*: `.claude/agents/sonnet-implementer.md` and
`opus-implementer.md` pinned dated model IDs (`claude-sonnet-4-6`,
`claude-opus-4-7`) that silently drifted behind the current lineup across two
release cycles (9.1.0 -> 9.3.0) with nothing to catch it.

ADR-0005's decision: every agent `model:` frontmatter value in this repo must
be a tier ALIAS -- `haiku` | `sonnet` | `opus` | `fable` | `inherit` -- which
the harness resolves to the current model of that tier at dispatch time.
Pinned model IDs are exactly the failure mode the ADR eliminates; this script
enforces that no agent file regresses to one.

Scope is deliberately narrow: `.claude/agents/*.md` and
`plugins/*/agents/*.md` only. ADR-0005 explicitly permits pinned model IDs in
Python tools that call the API directly and cannot use CLI aliases (they keep
configurable model values with env overrides, reviewed at release time) --
this script never looks at `tools/**`, so it cannot flag those legitimate
pins. Widening the glob to a repo-wide grep would also catch the 8 *correct*
`claude-sonnet-5`-style defaults baked into Python tool source, reddening
`main`'s own push build and deadlocking every subsequent PR -- the single
highest-risk failure mode called out for this item in IMPLEMENTATION_PLAN.md
6.1's Notes.

Usage:
    python3 scripts/check_agent_models.py              # scan agents, exit 0/1
    python3 scripts/check_agent_models.py --self-test   # negative-test the checker itself

Exit codes:
    0 - No agent declares a non-alias `model:` value (or self-test passed)
    1 - At least one agent declares a pinned ID / missing / unrecognized
        value (or self-test failed)
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ADR-0005's decision, verbatim: "Claude Code agent frontmatter now officially
# supports model aliases -- haiku, sonnet, opus, fable, inherit". This is the
# SINGLE source of truth for the allowed set in this script -- both the
# checker's validation logic and --self-test's fixtures are derived from this
# one constant, never a hand-copied second list. A test parametrized over a
# copy of an enum drifts alongside the bug and still passes at 100% coverage
# -- that exact defect shipped in this repo as #208 (a hardcoded
# ["P1".."P4"] list that had drifted from VALID_PRIORITIES, silently
# excluding the P0 path). See CLAUDE.md: "derive it, don't copy it."
ALLOWED_MODEL_ALIASES = frozenset({"haiku", "sonnet", "opus", "fable", "inherit"})

_MODEL_LINE_RE = re.compile(r"^model:\s*(.+?)\s*$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def split_frontmatter(content: str) -> str | None:
    """Return the YAML frontmatter block's inner text, or None if absent/malformed."""
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def extract_model(frontmatter: str) -> str | None:
    """Return the raw `model:` value from a frontmatter block, or None if absent.

    Strips a trailing inline comment and surrounding quotes, matching the
    tolerant parsing style used elsewhere in this repo's stdlib-only CI
    checks (see `parse_allowed_tools` in check_injections.py).
    """
    m = _MODEL_LINE_RE.search(frontmatter)
    if not m:
        return None
    value = m.group(1).strip()
    value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
    value = value.strip('"').strip("'")
    return value or None


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    file: Path
    value: str | None
    reason: str  # "missing" (no `model:` line / no frontmatter) or "invalid" (not an alias)


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0


def agent_files(root: Path) -> list[Path]:
    """`.claude/agents/*.md` and `plugins/*/agents/*.md` -- the only two
    locations agent definitions live in this repo (IMPLEMENTATION_PLAN.md
    6.1). Deliberately excludes `tools/**`, where ADR-0005 permits pinned
    model IDs.
    """
    files: list[Path] = []

    dot_claude_agents = root / ".claude" / "agents"
    if dot_claude_agents.is_dir():
        files.extend(sorted(dot_claude_agents.glob("*.md")))

    plugins_dir = root / "plugins"
    if plugins_dir.is_dir():
        for plugin_dir in sorted(plugins_dir.iterdir()):
            if not plugin_dir.is_dir():
                continue
            agents_dir = plugin_dir / "agents"
            if agents_dir.is_dir():
                files.extend(sorted(agents_dir.glob("*.md")))

    return files


def check_file(path: Path, root: Path) -> Finding | None:
    text = path.read_text(encoding="utf-8")
    frontmatter = split_frontmatter(text)
    rel = path.relative_to(root) if path.is_relative_to(root) else path

    if frontmatter is None:
        return Finding(file=rel, value=None, reason="missing")

    value = extract_model(frontmatter)
    if value is None:
        return Finding(file=rel, value=None, reason="missing")

    if value not in ALLOWED_MODEL_ALIASES:
        return Finding(file=rel, value=value, reason="invalid")

    return None


def scan(root: Path) -> ScanResult:
    result = ScanResult()
    for path in agent_files(root):
        finding = check_file(path, root)
        if finding is not None:
            result.findings.append(finding)
        result.files_scanned += 1
    return result


def report(result: ScanResult) -> int:
    if result.findings:
        print(f"Agent model-alias check FAILED -- {len(result.findings)} issue(s):\n")
        for f in result.findings:
            if f.reason == "missing":
                print(f"  - {f.file}: no `model:` frontmatter value found")
            else:
                print(f"  - {f.file}: model: {f.value!r} is not a tier alias")
        allowed = ", ".join(sorted(ALLOWED_MODEL_ALIASES))
        print(
            f"\nFix by setting `model:` to one of the ADR-0005 tier aliases ({allowed}) -- "
            "never a pinned model ID. Pinned IDs silently go stale as new models ship "
            "(this drifted undetected twice, across 9.1.0 -> 9.3.0); aliases resolve to the "
            "current model of that tier at dispatch time. See docs/adr/0005-model-aliases-"
            "in-agent-definitions.md. (Pinned IDs remain legal in Python tools under "
            "tools/**, which this check does not scan.)"
        )
        return 1

    print(
        f"Agent model-alias check passed: {result.files_scanned} agent file(s) scanned, "
        "all use ADR-0005 tier aliases."
    )
    return 0


# ---------------------------------------------------------------------------
# --self-test
#
# CLAUDE.md's rule applied to itself: a verification guard that can't fail is
# worse than none -- it converts "unchecked" into a false "checked". This
# builds deliberately-bad fixtures and asserts the checker exits 1 on them,
# AND asserts it exits 0 on known-good fixtures, in both directions.
#
# Positive fixtures are generated by ITERATING ALLOWED_MODEL_ALIASES, not by
# a hand-typed list that could drift from it. Negative fixtures deliberately
# include an out-of-set value (a bare "gpt-4"-shaped string, matching
# neither an alias nor a `claude-*` pin) alongside a pinned model ID and a
# missing `model:` line -- CLAUDE.md: "always include an out-of-set value
# (bugs of this class live entirely in the unrecognized-value branch)".
# ---------------------------------------------------------------------------


def _write_fixture_agent(root: Path, location: str, name: str, frontmatter_extra: str) -> Path:
    """Write a minimal agent .md fixture at either `.claude/agents/<name>.md`
    (location="dot-claude") or `plugins/p/agents/<name>.md` (location="plugin").
    `frontmatter_extra` is the raw text inserted for the `model:` line (or
    omitted entirely if empty, to fixture the "missing" case).
    """
    if location == "dot-claude":
        agents_dir = root / ".claude" / "agents"
    else:
        agents_dir = root / "plugins" / "p" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    path = agents_dir / f"{name}.md"
    lines = ["---", f"name: {name}", "description: self-test fixture"]
    if frontmatter_extra:
        lines.append(frontmatter_extra)
    lines.append("---")
    path.write_text("\n".join(lines) + "\n\nFixture body.\n", encoding="utf-8")
    return path


def _self_test_positive_fixtures() -> list[str]:
    """One fixture per ALLOWED_MODEL_ALIASES entry -- derived from the
    constant, not a copy of it. Every one must pass (0 findings).
    """
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="check_agent_models_selftest_pos_") as tmp:
        root = Path(tmp)
        for alias in sorted(ALLOWED_MODEL_ALIASES):
            path = _write_fixture_agent(root, "dot-claude", f"good-{alias}", f"model: {alias}")
            finding = check_file(path, root)
            status = "PASS" if finding is None else "FAIL"
            outcome = "no finding" if finding is None else finding.reason
            print(f"  [{status}] model: {alias} -> {outcome}")
            if finding is not None:
                failures.append(f"alias {alias!r} (from ALLOWED_MODEL_ALIASES) was flagged: {finding}")
    return failures


def _self_test_negative_fixtures() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="check_agent_models_selftest_neg_") as tmp:
        root = Path(tmp)

        cases: list[tuple[str, str, str, str]] = [
            # (case name, location, frontmatter model line ("" = omit), expected reason)
            ("pinned-id-dated", "dot-claude", "model: claude-opus-4-7", "invalid"),
            ("pinned-id-dot-claude-sonnet", "dot-claude", "model: claude-sonnet-4-6", "invalid"),
            ("out-of-set-value", "plugin", "model: gpt-4", "invalid"),
            ("missing-model-line", "plugin", "", "missing"),
        ]

        for name, location, frontmatter_extra, expected_reason in cases:
            path = _write_fixture_agent(root, location, name, frontmatter_extra)
            finding = check_file(path, root)
            ok = finding is not None and finding.reason == expected_reason
            status = "PASS" if ok else "FAIL"
            print(
                f"  [{status}] {name}: expect reason={expected_reason!r} "
                f"got={finding.reason if finding else None!r}"
            )
            if not ok:
                failures.append(f"fixture case {name!r} did not classify as expected: {finding}")

        # Full-scan wiring check: a directory containing only a bad fixture
        # must make scan() (the function main() actually calls) return a
        # non-empty finding list; a directory containing only good fixtures
        # must return empty. This is the "wire it in" half of the negative
        # test, not just the per-file classification half above.
        bad_root = Path(tmp) / "bad-tree"
        _write_fixture_agent(bad_root, "dot-claude", "bad-pinned", "model: claude-opus-4-7")
        bad_result = scan(bad_root)
        if not bad_result.findings:
            failures.append(
                "scan() over a tree containing only a pinned-ID agent found 0 issues"
            )

        good_root = Path(tmp) / "good-tree"
        _write_fixture_agent(good_root, "dot-claude", "good-inherit", "model: inherit")
        good_result = scan(good_root)
        if good_result.findings:
            failures.append(
                f"scan() over a tree containing only alias-compliant agents found issues: "
                f"{good_result.findings}"
            )

    return failures


def self_test() -> int:
    print("=== check_agent_models.py --self-test ===\n")

    aliases = sorted(ALLOWED_MODEL_ALIASES)
    print(f"-- Positive fixtures, one per ALLOWED_MODEL_ALIASES entry ({aliases}) --")
    failures = _self_test_positive_fixtures()

    print("\n-- Negative fixtures (pinned ID x2, out-of-set value, missing model line) + scan() wiring --")
    failures += _self_test_negative_fixtures()

    print("\n-- Real repo tree (must be green: all 13 agent files are already alias-compliant) --")
    real_result = scan(REPO_ROOT)
    real_ok = not real_result.findings
    print(
        f"  [{'PASS' if real_ok else 'FAIL'}] {REPO_ROOT} -> "
        f"{real_result.files_scanned} file(s), {len(real_result.findings)} finding(s)"
    )
    if not real_ok:
        for f in real_result.findings:
            print(f"      {f.file}: model: {f.value!r} [{f.reason}]")
        failures.append("the real repo tree is not clean -- see findings above")

    print()
    if failures:
        print(f"self-test FAILED -- {len(failures)} problem(s):\n")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("self-test PASSED -- all fixtures classified correctly in both directions.")
    return 0


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Agent `model:` frontmatter tier-alias enforcement (ADR-0005).",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Negative-test the checker itself against deliberately-bad and known-good fixtures.",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    result = scan(REPO_ROOT)
    return report(result)


if __name__ == "__main__":
    sys.exit(main())
