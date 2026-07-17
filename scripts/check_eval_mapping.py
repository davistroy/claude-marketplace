#!/usr/bin/env python3
"""
Eval-mapping / structural-linter / coverage-gate CI check (stdlib only).

Every `evals/**/*.eval.md` file is a behavioral contract for one live skill
or command. Without a check, an eval can silently outlive the surface it
tests -- a skill gets renamed or removed, and its eval keeps passing review
because nobody notices it now describes nothing (see IMPLEMENTATION_PLAN.md
8.3 / arch-review SA-006, which found exactly this for `help.eval.md` and
`new-command.eval.md`). This script runs three independent checks:

1. MAPPING -- every eval maps to something real (IMPLEMENTATION_PLAN.md 8.3).
2. STRUCTURE -- every eval has the minimum shape needed to actually test
   something: at least one scenario, an established invocation, and a
   scored Rubric (IMPLEMENTATION_PLAN.md 6.1 / #150).
3. COVERAGE -- every live skill/command is referenced by at least one eval,
   or has a justified allowlist entry (IMPLEMENTATION_PLAN.md 6.2 / #150).

Mapping rules:

  - A normal eval declares `command: <name>` in its frontmatter, naming the
    skill or command under test. `<name>` must match a live skill
    (`plugins/*/skills/<name>/SKILL.md`) or command
    (`plugins/*/commands/<name>.md`) in some plugin.

  - A cross-cutting eval that intentionally exercises multiple skills/commands
    at once (e.g. `description-triggers.eval.md`, which regression-guards
    auto-invocation across several unrelated skills) declares
    `type: cross-cutting` plus a `maps_to: [name1, name2, ...]` list instead
    of a single `command:` target. Every name in `maps_to` must independently
    resolve to a live skill or command. This is an explicit, auditable escape
    hatch -- not a way to silently exempt a file from the check.

    The `command:` field is still required on cross-cutting evals, but it is
    not a live-surface reference (that is what `maps_to` is for) -- it is a
    stable self-identifying slug and must equal the eval's own filename
    (`description-triggers.eval.md` -> `command: description-triggers`).
    Without this, `command:` on a cross-cutting eval was a dead field: the
    mapping loop `continue`d past it as soon as `maps_to` validated, so a
    blank or garbage `command:` value was never caught.

Structure rules (stdlib grammar, not a full markdown parser):

  - The file has at least one `### S<n>: ...` scenario heading.
  - Every scenario has at least one `**Must:**` or `**Must NOT:**` block --
    a scenario asserting nothing is not a test. (`**Must NOT:**`-only
    scenarios, e.g. "must never auto-invoke", are legitimate and count.)
  - Every eval establishes an invocation at least once, via `**Invocation:**`
    or `**Context:**` (both spellings are used across the corpus and are
    equivalent for this purpose). A scenario that omits its own line
    inherits the most recently established invocation earlier in the same
    file -- this is the dominant, legitimate pattern for follow-on scenarios
    that continue a prior scenario's setup (e.g. "S2: Health metrics
    accuracy" following "S1: Invocation: `/prime`"). Only a scenario with
    no invocation of its own AND no earlier scenario to inherit from fails.
  - The file has a `## Rubric` section.

Coverage rule:

  - Every live skill/command must be resolved by some eval's `command:` or
    `maps_to:`, or have a reasoned entry in COVERAGE_ALLOWLIST below. A bare
    gap (neither) fails the build so a new surface can never silently ship
    without either a test or a documented reason it has none.

Usage:
    python3 scripts/check_eval_mapping.py

Exits 0 if mapping, structure, and coverage all pass; exits 1 with a report
of every failure otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = REPO_ROOT / "evals"
PLUGINS_DIR = REPO_ROOT / "plugins"

EVAL_SUFFIX = ".eval.md"

INVOCATION_MARKERS = ("**Invocation:**", "**Context:**")
MUST_MARKERS = ("**Must:**", "**Must NOT:**")

# A scenario heading looks like "### S1: <name>" or "### S12 <name>".
_HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$", re.MULTILINE)
_SCENARIO_TITLE_RE = re.compile(r"^S\d+\b")

# ---------------------------------------------------------------------------
# Coverage allowlist
#
# Every live skill/command must be referenced by at least one eval file
# (directly via `command:`, or via `maps_to:` in a cross-cutting eval) OR
# have an entry here with a one-line reason it cannot carry its own eval.
# A bare gap (neither) fails the check -- this is what prevents a new
# surface from silently shipping without any test coverage or documented
# exemption. Keep reasons specific enough to justify the exemption on their
# own (IMPLEMENTATION_PLAN.md 6.2 / #150).
# ---------------------------------------------------------------------------
COVERAGE_ALLOWLIST: dict[str, str] = {
    # Fleet-ops skills read live state from specific personal-fleet hosts over
    # SSH; there is no CI-reachable equivalent of that hardware.
    "fleet-health": "reads live status from 5 specific home-fleet hosts over SSH -- not runnable in CI",
    "spark-audit": "SSH to the DGX Spark host specifically -- not runnable in CI",
    "spark-recon": "SSH to the DGX Spark host specifically -- not runnable in CI",
    "jetson-audit": "SSH to the Jetson host specifically -- not runnable in CI",
    "jetson-recon": "SSH to the Jetson host specifically -- not runnable in CI",
    # slide-gen surfaces that shell out to the external `sg` engine, which
    # requires image-generation API keys per ADR-0008 (not present in CI).
    "build-cfa-deck": "needs the external slide-gen engine + API keys (ADR-0008) -- not runnable in CI",
    "sg-generate-images": "needs the external slide-gen engine + Gemini API key (ADR-0008) -- not runnable in CI",
    "sg-validate-graphics": "needs the external slide-gen engine (ADR-0008) -- not runnable in CI",
    # Has an eval file (so it is not a mapping/coverage gap on its own merits),
    # but its scenarios pin a machine-specific Windows path and cannot
    # actually execute in CI -- documented here for the same reason the
    # SSH-only and engine-only surfaces above are.
    "evaluate-pipeline-output": "has an eval, but its scenarios pin a machine-specific Windows path -- unrunnable in CI",
}


def parse_frontmatter(text: str) -> dict[str, object]:
    """Minimal parser for the flat frontmatter shape used by evals/**/*.eval.md.

    Every key so far is either a bare scalar (`command: help`) or a single
    inline bracketed list (`fixtures: [a, b]`, `maps_to: [a, b]`). This is not
    a general YAML parser -- it deliberately covers only that shape so the
    script stays stdlib-only (no PyYAML dependency for a CI-critical check).
    """
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    data: dict[str, object] = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
        else:
            data[key] = value
    return data


def parse_scenarios(text: str) -> list[tuple[str, str]]:
    """Split an eval body into (scenario_title, scenario_body) pairs.

    A scenario begins at a `### S<n>: ...` heading and ends at the next
    heading of level 2 or 3 -- either the next scenario, or a sibling
    section like `## Rubric`. Using heading boundaries (not just the next
    `### S`) keeps a scenario's body from bleeding into `## Rubric` prose,
    which could otherwise contain a stray "must" that looks like a match.
    """
    headings = [(m.start(), m.group(1), m.group(2).strip()) for m in _HEADING_RE.finditer(text)]

    scenarios: list[tuple[str, str]] = []
    for idx, (pos, level, title) in enumerate(headings):
        if level == "###" and _SCENARIO_TITLE_RE.match(title):
            end = headings[idx + 1][0] if idx + 1 < len(headings) else len(text)
            scenarios.append((title, text[pos:end]))
    return scenarios


def validate_structure(rel: Path, text: str) -> list[str]:
    """Validate the minimum shape needed for an eval to actually test something."""
    errors: list[str] = []

    if "## Rubric" not in text:
        errors.append(f"{rel}: missing required `## Rubric` section")

    scenarios = parse_scenarios(text)
    if not scenarios:
        errors.append(f"{rel}: no test scenarios found (expected `### S1: <name>` headings)")
        return errors

    seen_invocation = False
    for title, body in scenarios:
        has_invocation = any(marker in body for marker in INVOCATION_MARKERS)
        has_must = any(marker in body for marker in MUST_MARKERS)

        if has_invocation:
            seen_invocation = True
        elif not seen_invocation:
            errors.append(
                f"{rel}: scenario '{title}' has no **Invocation:**/**Context:** line, "
                "and no earlier scenario in this file establishes one to inherit"
            )

        if not has_must:
            errors.append(
                f"{rel}: scenario '{title}' has no **Must:** or **Must NOT:** block "
                "(a scenario asserting nothing is not a test)"
            )

    return errors


def live_skills_and_commands() -> tuple[set[str], set[str]]:
    """Scan plugins/*/skills/*/SKILL.md and plugins/*/commands/*.md."""
    skills: set[str] = set()
    commands: set[str] = set()

    if not PLUGINS_DIR.is_dir():
        return skills, commands

    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue

        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                    skills.add(skill_dir.name)

        commands_dir = plugin_dir / "commands"
        if commands_dir.is_dir():
            for cmd_file in commands_dir.glob("*.md"):
                commands.add(cmd_file.stem)

    return skills, commands


def main() -> int:
    skills, commands = live_skills_and_commands()
    live = skills | commands

    eval_files = sorted(EVALS_DIR.rglob("*.eval.md"))
    if not eval_files:
        print("No eval files found under evals/ -- nothing to check.")
        return 0

    errors: list[str] = []
    covered: set[str] = set()

    for eval_file in eval_files:
        rel = eval_file.relative_to(REPO_ROOT)
        text = eval_file.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)

        # --- Mapping ---------------------------------------------------
        eval_type = frontmatter.get("type")
        maps_to = frontmatter.get("maps_to")

        if eval_type == "cross-cutting" or maps_to:
            if not maps_to:
                errors.append(f"{rel}: type: cross-cutting requires a non-empty `maps_to` list")
            else:
                missing = [name for name in maps_to if name not in live]
                if missing:
                    errors.append(
                        f"{rel}: maps_to references nonexistent skill/command(s): "
                        f"{', '.join(missing)}"
                    )
                covered.update(name for name in maps_to if isinstance(name, str))

            # `command:` on a cross-cutting eval is not a live-surface
            # reference (maps_to is) -- it must still be present and must
            # equal the eval's own filename slug, so it can never silently
            # go blank or drift without the check noticing.
            file_stem = eval_file.name[: -len(EVAL_SUFFIX)]
            cmd = frontmatter.get("command")
            if not cmd:
                errors.append(f"{rel}: cross-cutting eval is missing required `command` frontmatter field")
            elif cmd != file_stem:
                errors.append(
                    f"{rel}: cross-cutting eval's `command: {cmd}` must equal its own "
                    f"filename slug `{file_stem}` (maps_to resolves to live surfaces; "
                    "`command` is just a stable self-identifier)"
                )
        else:
            name = frontmatter.get("command")
            if not name:
                errors.append(f"{rel}: missing required `command` frontmatter field")
            else:
                if name not in live:
                    errors.append(
                        f"{rel}: `command: {name}` matches no live skill "
                        f"(plugins/*/skills/{name}/SKILL.md) or command "
                        f"(plugins/*/commands/{name}.md)"
                    )
                covered.add(name)

        # --- Structure ---------------------------------------------------
        errors.extend(validate_structure(rel, text))

    # --- Coverage ----------------------------------------------------------
    gap = sorted(live - covered - set(COVERAGE_ALLOWLIST))
    for name in gap:
        errors.append(
            f"coverage gap: '{name}' is a live skill/command with no eval "
            "(`command:`/`maps_to:`) and no COVERAGE_ALLOWLIST entry -- add an "
            "eval or a justified allowlist entry in scripts/check_eval_mapping.py"
        )

    for name, reason in COVERAGE_ALLOWLIST.items():
        if name not in live:
            errors.append(
                f"COVERAGE_ALLOWLIST entry '{name}' matches no live skill or command "
                "-- stale entry, remove it"
            )
        if not reason.strip():
            errors.append(f"COVERAGE_ALLOWLIST entry '{name}' has an empty reason")

    if errors:
        print(f"Eval-mapping check FAILED -- {len(errors)} issue(s):\n")
        for error in errors:
            print(f"  - {error}")
        print(
            "\nFix by updating the eval's `command`/`maps_to` frontmatter or scenario "
            "structure to match the current skill/command, adding a missing eval, "
            "adding a COVERAGE_ALLOWLIST entry with a reason, or deleting the eval if "
            "the surface it tests no longer exists."
        )
        return 1

    print(
        f"Eval-mapping check passed: {len(eval_files)} eval file(s), "
        f"{len(live)} live surface(s) -- all mapped, structurally sound, and covered."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
