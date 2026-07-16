#!/usr/bin/env python3
"""
Eval-mapping CI check (stdlib only).

Every `evals/**/*.eval.md` file is a behavioral contract for one live skill
or command. Without a check, an eval can silently outlive the surface it
tests — a skill gets renamed or removed, and its eval keeps passing review
because nobody notices it now describes nothing (see IMPLEMENTATION_PLAN.md
8.3 / arch-review SA-006, which found exactly this for `help.eval.md` and
`new-command.eval.md`).

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
    hatch — not a way to silently exempt a file from the check.

Usage:
    python3 scripts/check_eval_mapping.py

Exits 0 if every eval file maps to something real; exits 1 with a report of
every eval that maps to nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = REPO_ROOT / "evals"
PLUGINS_DIR = REPO_ROOT / "plugins"


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

    for eval_file in eval_files:
        rel = eval_file.relative_to(REPO_ROOT)
        frontmatter = parse_frontmatter(eval_file.read_text(encoding="utf-8"))

        eval_type = frontmatter.get("type")
        maps_to = frontmatter.get("maps_to")

        if eval_type == "cross-cutting" or maps_to:
            if not maps_to:
                errors.append(f"{rel}: type: cross-cutting requires a non-empty `maps_to` list")
                continue
            missing = [name for name in maps_to if name not in live]
            if missing:
                errors.append(
                    f"{rel}: maps_to references nonexistent skill/command(s): "
                    f"{', '.join(missing)}"
                )
            continue

        name = frontmatter.get("command")
        if not name:
            errors.append(f"{rel}: missing required `command` frontmatter field")
            continue

        if name not in live:
            errors.append(
                f"{rel}: `command: {name}` matches no live skill "
                f"(plugins/*/skills/{name}/SKILL.md) or command "
                f"(plugins/*/commands/{name}.md)"
            )

    if errors:
        print(f"Eval-mapping check FAILED -- {len(errors)} eval file(s) map to nothing:\n")
        for error in errors:
            print(f"  - {error}")
        print(
            "\nFix by updating the eval's `command`/`maps_to` frontmatter to match the "
            "current skill/command name, or deleting the eval if the surface it tests "
            "no longer exists."
        )
        return 1

    print(
        f"Eval-mapping check passed: {len(eval_files)} eval file(s) all map to a "
        "live skill or command."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
