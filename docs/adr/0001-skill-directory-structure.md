# ADR-0001: Skill Directory Structure

**Date:** 2026-02-16
**Status:** Accepted

## Context

Claude Code plugins support two types of extensibility: commands and skills. Commands are user-initiated slash commands (e.g., `/review-arch`), while skills are discrete capabilities that Claude can proactively suggest after completing related work.

Claude Code's plugin loader discovers skills by scanning for a specific filesystem pattern: `skills/*/SKILL.md`. The directory name becomes the skill identifier, and the file must be named exactly `SKILL.md` (uppercase). Flat markdown files placed directly in the `skills/` directory (e.g., `skills/ship.md`) are silently ignored -- they do not cause errors, but they are never discovered or registered. This is a hard constraint imposed by Claude Code's runtime, not a design preference.

This stands in contrast to how commands work: commands use a flat structure where any `.md` file in the `commands/` directory is discovered, and the filename (minus extension) becomes the command name. Early development of this marketplace attempted to use the same flat pattern for skills, which resulted in skills that appeared structurally correct but were never available at runtime. Debugging this required tracing Claude Code's plugin loading behavior to understand the `skills/*/SKILL.md` glob pattern requirement.

## Decision

All skills in this marketplace use the nested directory structure `skills/<skill-name>/SKILL.md`, where:

- The directory name exactly matches the skill's `name` field in its YAML frontmatter
- The file is named exactly `SKILL.md` (uppercase)
- Each skill directory contains only the single `SKILL.md` file (no subdirectories or auxiliary files)

Commands continue to use the flat `commands/<command-name>.md` pattern.

## Consequences

### Positive
- Skills are reliably discovered by Claude Code's plugin loader every time
- The directory name serves as a single source of truth for the skill identifier, reducing naming mismatches
- The pattern is self-documenting: seeing `skills/ship/SKILL.md` makes it immediately clear this is a skill named "ship"
- Consistent across all plugins in the marketplace, reducing cognitive load for contributors

### Negative
- Creates more directories than a flat structure would require -- each skill needs its own subdirectory even though it contains only one file
- The asymmetry between commands (flat) and skills (nested) is a source of confusion for new contributors who naturally assume both follow the same pattern
- Renaming a skill requires renaming both the directory and updating the `name` field in the YAML frontmatter, creating two points of change

### Neutral
- The `SKILL.md` filename convention (uppercase) follows a pattern similar to other well-known convention files like `README.md`, `CHANGELOG.md`, and `Makefile`
- This constraint is imposed by Claude Code's runtime and is unlikely to change without a major version update to the plugin system
