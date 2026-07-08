# ADR-0005: Model Aliases in Agent Definitions

**Date:** 2026-07-08
**Status:** Proposed
**Deciders:** Troy Davis (proposed via /ultra-plan session, Lab Notebook E009)

## Context

The named implementer agents (`.claude/agents/haiku-implementer.md`, `sonnet-implementer.md`, `opus-implementer.md`) pin full model IDs in frontmatter, per D14 (Lab Notebook E005). By 2026-07-08 two of the three pins had silently drifted behind the current lineup: `claude-sonnet-4-6` (current: Sonnet 5) and `claude-opus-4-7` (current: Opus 4.8). Every `/implement-plan` dispatch ran on outdated models with no warning. The same staleness class appeared in `research-topic` (`claude-opus-4-6-20250725`) and the visual-explainer tool (`claude-sonnet-4-20250514`).

Claude Code agent frontmatter now officially supports model aliases — `haiku`, `sonnet`, `opus`, `fable`, `inherit` — which resolve to the current model of each tier at dispatch time (code.claude.com/docs plugins-reference).

D14's intent was to decouple model selection from plan content so a model swap is a one-line change. Pinned IDs achieved the decoupling but reintroduced a manual maintenance burden that has now failed twice.

## Decision

All agent `model:` frontmatter in this repo uses tier aliases, not pinned IDs:

- `.claude/agents/haiku-implementer.md` → `model: haiku`
- `.claude/agents/sonnet-implementer.md` → `model: sonnet`
- `.claude/agents/opus-implementer.md` → `model: opus`
- `plugins/personal-plugin/agents/*.md` (arch-review team, gaining frontmatter under R1) → `model: inherit` (session-controlled; a deep review should run at the quality tier the user chose for the session)

Documentation and skill bodies reference tiers conceptually ("haiku/sonnet/opus"), never dated IDs. Python tools keep configurable model values with env overrides, defaulting to current IDs, reviewed at release time (they call the API directly and cannot use CLI aliases).

## Consequences

### Positive
- Model pins can never silently go stale — the failure mode observed twice is structurally eliminated
- Plan content, agent names, and dispatch logic remain fully decoupled from model releases (completes D14's intent)
- One mental model repo-wide: tier words everywhere, IDs only where an API call requires one

### Negative
- Behavior shifts silently when Anthropic promotes a new model to a tier — a plan executed in March and re-run in July may use different models (acceptable for a personal marketplace; reproducibility was already broken by the stale pins)
- Cannot pin a known-good model version for a regression-sensitive workflow without reverting to an ID for that agent

### Neutral
- `haiku` alias currently resolves to the same model the old pin named (claude-haiku-4-5)
- Escalation semantics (ESCALATE → next tier) are unaffected; they were always tier-based

## Alternatives Considered

### Keep pinned IDs with periodic manual review
- **Description:** Retain full model IDs; add a release-checklist item to verify pins against the current lineup.
- **Pros:** Reproducible dispatches; explicit control.
- **Cons:** The exact process that already failed — pins drifted through two release cycles (9.1.0 → 9.3.0) unnoticed.
- **Why rejected:** Proven failure mode; the checklist discipline it requires demonstrably did not happen.

### Pinned IDs with CI staleness check
- **Description:** CI job compares pinned IDs against a live model list and fails on deprecation/supersession.
- **Pros:** Keeps reproducibility and catches drift.
- **Cons:** Requires an authenticated API call or a maintained allowlist in CI; adds infrastructure for a problem aliases solve for free.
- **Why rejected:** Complexity disproportionate to the need; aliases are the platform's intended mechanism.
