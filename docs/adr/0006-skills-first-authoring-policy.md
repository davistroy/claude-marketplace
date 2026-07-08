# ADR-0006: Skills-First Authoring Policy

**Date:** 2026-07-08
**Status:** Proposed
**Deciders:** Troy Davis (proposed via /ultra-plan session, Lab Notebook E009)

## Context

Claude Code has unified custom slash commands and skills: both `commands/*.md` and `skills/name/SKILL.md` load identically, and the official documentation plus Anthropic's own `example-plugin` now describe `commands/` as the legacy format — "Use `skills/` for new plugins" (code.claude.com/docs/en/skills, github.com/anthropics/claude-plugins-official). Skills additionally support fields commands historically lacked in this repo's usage: `paths:` auto-activation, `context: fork` + `agent:`, `when_to_use`, scoped `hooks`.

personal-plugin carries 24 commands and 24 skills. The scaffolding tooling (`/new-command`, `/scaffold-plugin`, `references/templates/` — 8 command-pattern templates vs 1 skill template) still generates and teaches the legacy format by default.

## Decision

1. **New functionality ships as skills.** The `commands/` directories are frozen legacy surface — maintained, not extended.
2. **`/new-command` is deprecated** (moved to `deprecated/` per house convention). Its 8 pattern templates remain in `references/templates/` and become inputs to `/new-skill`, which gains pattern support and adapts them to SKILL.md form (nested dir, `name:` frontmatter) on generation.
3. **`/scaffold-plugin` defaults to skills-first**: generates `skills/` by default, `commands/` only on explicit request (marked legacy); "Next Steps" leads with `/new-skill`.
4. **No mass migration** of the 24 existing commands. They keep working indefinitely (the runtime loads both formats identically). Individual commands migrate opportunistically only when a change would benefit from skill-only fields.
5. CLAUDE.md documents the policy in Verified Operational Rules.

## Consequences

### Positive
- Aligned with the platform's documented direction before more legacy surface accumulates
- Single authoring path and template set to maintain; skill-only capabilities available to all new work
- User-visible invocation is unchanged — skills and commands both invoke as `/name`

### Negative
- Mixed formats persist indefinitely; contributors must know commands are frozen
- Anyone with `/new-command` muscle memory gets a deprecation pointer instead of a scaffold

### Neutral
- The 24 existing commands' behavior, names, and namespacing are untouched
- House frontmatter rules stay: commands never carry `name:`; skills always do (stricter than the 2026 spec, kept as convention)

## Alternatives Considered

### Mass-migrate all 24 commands to skills
- **Description:** Convert every `commands/*.md` into `skills/name/SKILL.md` in one release.
- **Pros:** Single format; full feature surface everywhere; clean story.
- **Cons:** Large diff with zero functional gain; risks discovery regressions across install scopes; invalidates docs, README tables, and user habits in one shot; contradicts "leave working systems alone."
- **Why rejected:** All cost, no capability the frozen commands actually need today.

### Status quo (keep authoring commands)
- **Description:** Continue generating commands via /new-command; treat the unification as cosmetic.
- **Pros:** No change effort.
- **Cons:** Diverges from official guidance; every new command deepens the legacy surface; scaffolding teaches a format the platform documents as legacy.
- **Why rejected:** The gap only widens; the cheapest time to switch defaults is now.
