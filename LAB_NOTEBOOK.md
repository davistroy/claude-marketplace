# Claude Marketplace — Lab Notebook

**Project:** Claude Code plugin marketplace — two plugins (personal-plugin, bpmn-plugin) extending Claude Code with 25+ commands and 20+ skills for documentation, architecture review, research, BPMN modeling, and workflow automation.
**Started:** 2026-04-30
**Systems:** GitHub (davistroy/claude-marketplace), Claude Code CLI (Windows 11), installed via `/plugin marketplace add`

---

## Decision Log

Decisions are tracked here with their lifecycle. When a decision is revisited, update its status to SUPERSEDED and link to the new entry. Never delete old decisions. For decisions originating in another project's notebook, note the source.

| # | Decision | Date | Status | Entry | Alternatives Considered |
|---|----------|------|--------|-------|------------------------|
| D1 | Skills use nested dirs (`skills/name/SKILL.md`), commands use flat files (`commands/name.md`) | 2025-01-03 | ACTIVE | Pre-notebook | Claude Code loader requires this; flat skill files silently fail |
| D2 | Skills MUST have `name` in frontmatter; commands MUST NOT | 2025-01-10 | ACTIVE | Pre-notebook | Discovered via silent discovery failures — no error, just missing |
| D3 | Do NOT declare `tools` or `hooks` in plugin.json | 2026-03-31 | ACTIVE | Pre-notebook | `tools` → "Unrecognized key" error; `hooks` → "Duplicate" error (auto-discovered) |
| D4 | Shared plan template (`references/plan-template.md`) for create-plan and plan-improvements | 2026-03-04 | ACTIVE | Pre-notebook | Avoids template drift between the two plan generators |
| D5 | Replace research-orchestrator Python tool with 3 parallel `context:fork` subagents | 2026-04-21 | ACTIVE | Pre-notebook | Python tool (27 files): complex deps, cross-platform issues. Subagents: simpler, no deps. Trade-off: lost real-time streaming progress |
| D6 | Consolidate audit/recon skills into shared reference + config layer | 2026-04-21 | ACTIVE | Pre-notebook | ~50% LOC reduction. Alt: keep duplicated — rejected due to maintenance burden |
| D7 | hooks.json uses record format (keyed by event), not array | 2026-03-31 | ACTIVE | Pre-notebook | Array format broke with "expected record, received array". `type: prompt` also removed — only `type: command` |
| D8 | Deprecate review-pr, help skills — superseded by native `/review`, `/help` | 2026-04-21 | ACTIVE | Pre-notebook | Native commands are maintained by Anthropic; custom versions drift |
| D9 | Plan template: drop `Parallelizable` field, consolidate into `Execution Mode` | 2026-04-30 | ACTIVE | E001 | Two fields carried the same signal; `Execution Mode` is more expressive (Sequential/Parallel/Worktree-Isolated) |
| D10 | Plan template: add `Depends On` field to work items for intra-phase dependency tracking | 2026-04-30 | ACTIVE | E001 | Previously only phase-level dependencies existed; item-level deps were only in the disconnected Parallel Work table |

| D11 | Fold Lab Notebook A2, A3, A4 into gap-analysis implementation plan Phase 5 | 2026-04-30 | ACTIVE | E002 | Execute separately — rejected, they naturally fit Phase 5's implement-plan updates |
| D12 | Fix `/ultraplan` vs `/ultra-plan` reference ambiguity (no full rename) | 2026-04-30 | ACTIVE | E002 | Full rename — rejected, breaking change for user muscle memory. Hyphen already distinguishes. |
| D13 | Constitution constraints live in CLAUDE.md, not separate constitution.md | 2026-04-30 | ACTIVE | E002 | Separate constitution.md (Spec Kit pattern) — rejected, artifact sprawl for solo-builder context |
| D19 | Plugin cache freshness is governed by the marketplace's `autoUpdate` setting against `origin/main`, not by manual local reinstall | 2026-07-08 | ACTIVE | E007 | Manual reinstall (A1/A7 premise) — superseded; cache already tracks GitHub origin automatically when `autoUpdate: true`. The real risk is the local dev clone lagging origin (second occurrence of D17's root cause) |
| D20 | Agent `model:` fields use tier aliases (haiku/sonnet/opus/inherit), never pinned IDs (ADR-0005, Accepted) | 2026-07-08 | ACTIVE | E009/E010 | Pinned + periodic review — rejected, drifted twice undetected (9.1.0→9.3.0) |
| D21 | Skills-first authoring: new functionality ships as skills; commands/ frozen legacy; new-command deprecated, patterns ported to /new-skill --pattern (ADR-0006, Accepted) | 2026-07-08 | ACTIVE | E009/E010 | Mass-migrate 24 commands — rejected (churn, zero functional gain); status quo — rejected (diverges from official direction) |

Status values: ACTIVE · SUPERSEDED (by D#) · REVERSED (in E#)

## Action Items

Track follow-ups that emerge from experiments. Move to Completed when done.

### Open

| # | Action | Created | Source Entry |
|---|--------|---------|-------------|
| — | (none) | | |

### Completed

| # | Action | Created | Completed | Source Entry |
|---|--------|---------|-----------|-------------|
| C1 | v8.0.0 marketplace modernization — 7-phase plan, all complete | 2026-04-21 | 2026-04-21 | Pre-notebook |
| C2 | Remove research-orchestrator Python tool (27 files) | 2026-04-21 | 2026-04-21 | Pre-notebook |
| C3 | Remove stale CI jobs referencing deleted tool and help-sync check | 2026-04-21 | 2026-04-21 | Pre-notebook |
| C4 | Plan template refinements — 7 improvements to plan-template.md | 2026-04-30 | 2026-04-30 | E001 |
| C5 | Update implement-plan.md to set Completed header field during finalization (A2) | 2026-04-30 | 2026-04-30 | E003 |
| C6 | Update implement-plan.md to parse Depends On for parallelization map (A3) | 2026-04-30 | 2026-04-30 | E003 |
| C7 | Update implement-plan.md to update Risk Mitigation Status during execution (A4) | 2026-04-30 | 2026-04-30 | E003 |
| C8 | Execute gap-analysis IMPLEMENTATION_PLAN.md — 6 phases, 17 items, all complete (A5) | 2026-04-30 | 2026-04-30 | E003 |
| C9 | Fix /ultraplan → /ultra-plan reference ambiguity in plan-gate and create-plan (A6) | 2026-04-30 | 2026-04-30 | E003 |
| C10 | Update validate-plugin: fix stale counts, add plan template + reference inventory validation | 2026-04-30 | 2026-04-30 | E004 |
| C11 | Reinstall plugin to sync spark-recon (A1) — superseded, not executed as originally framed: spark-recon was rewritten multiple times since (v9.1–9.3); reinstall model was based on an incomplete picture of cache sync (see D19) | 2026-04-30 | 2026-07-08 | E007 |
| C12 | Reinstall plugin to sync gap-analysis changes (A7) — superseded: cache auto-syncs from GitHub `origin/main` (`autoUpdate: true`), confirmed cache already at 9.3.0 = origin tip before any manual action; the actual gap was the local dev clone lagging origin by 1 commit, fixed via `git pull --ff-only` | 2026-04-30 | 2026-07-08 | E007 |
| C13 | Bump personal-plugin version to 9.0.0 (A8) — done via commit `3b9679d`, since surpassed (now 9.3.0) | 2026-04-30 | 2026-04-30 | E003 |
| C14 | Execute the 13 review recommendations R1–R13 (A9) — full 8-phase/35-item plan executed via /implement-plan; released as 10.0.0/4.2.0/1.2.0/3.3.0 | 2026-07-08 | 2026-07-08 | E008–E010 |
| C15 | Force plugin cache to release versions + arch-review smoke test (A10) — cache at 10.0.0/4.2.0/1.2.0 verified on disk; dispatch mechanics green; new definitions restart-gated (load next session) | 2026-07-08 | 2026-07-08 | E011 |
| C16 | Regenerate 5 tool lockfiles for patched CVE versions (plan item 4.2) — 0 pyproject.toml floor changes needed; pip-audit clean ×3 tools; coverage floors held (92.32%/67.03%/96.95%); neither flagged risk (lxml 6.1, pillow 12.2) regressed | 2026-07-12 | 2026-07-12 | E012 |
| C17 | Plan item 4.3 (A11): `.github/dependabot.yml` created (pip ×3 tool dirs + github-actions, grouped weekly); PR #99 opened from `fix/dependency-cves-2026-07`; all 15 CI checks green on ubuntu + windows; squash-merged | 2026-07-12 | 2026-07-12 | E013 |
| C18 | Author `clear-prep` skill (context-clear handoff) + refresh 4-version-stale Current Baseline (prime finding); `claude plugin validate --strict` passed, not yet shipped | 2026-07-16 | 2026-07-16 | E015 |

---

## Prior Work Summary

This marketplace has been under active development since January 2025, growing from 8 commands and 1 skill to 25+ commands and 20+ skills across two plugins. The project lives at `davistroy/claude-marketplace` on GitHub and is installed into Claude Code via `/plugin marketplace add davistroy/claude-marketplace`.

### Architecture

The marketplace follows Claude Code's plugin discovery conventions with strict structural rules discovered through trial and error (see CLAUDE.md "Verified Operational Rules"). The two plugins — `personal-plugin` (productivity/analysis/planning) and `bpmn-plugin` (BPMN 2.0 workflow modeling) — share a top-level `.claude-plugin/marketplace.json` manifest. Each plugin has its own `plugin.json`, commands directory (flat `.md` files), skills directory (nested `name/SKILL.md`), and optional references, tools, hooks, and agents directories.

### Major Milestones

The project has gone through 8 major versions of personal-plugin and 4 of bpmn-plugin. Key inflection points:

- **v3.x** (Jan 2026): Added research-topic with multi-provider Python orchestrator, visual-explainer with Gemini image generation, ship skill with Gitea support, implement-plan with subagent orchestration
- **v4.x** (Feb 2026): Added prime, review-intent, parallel execution in implement-plan, plan append mode
- **v5.x** (Mar 2026): Breaking deprecations (convert-hooks, setup-statusline, check-updates), shared plan template, comprehensive allowed-tools and error handling across all 36 files
- **v6.x** (Mar-Apr 2026): Added lab-notebook, brain-entry, spark-recon, ultra-plan, arch-review (9-agent team), hooks system, evaluate-pipeline-output, argument-hint and effort frontmatter
- **v7.x** (Apr 2026): Prime reads LAB_NOTEBOOK.md in Phase 0
- **v8.0.0** (Apr 21, 2026): Major modernization — adopted `context:fork`, `isolation:worktree`, `paths:` auto-activation, dynamic `!cmd` injection. Consolidated audit/recon skills (~50% LOC reduction). Removed research-orchestrator Python tool entirely (replaced with 3 parallel subagents). Deleted deprecated help skills and review-pr.

### Current State

*(This subsection is a point-in-time snapshot as of the v8.0.0 modernization, 2026-04-21 — for live version numbers, always check the "Current Baseline" section below, not this paragraph.)* As of 2026-04-21 the marketplace was at v2.0.0, personal-plugin v8.0.0, bpmn-plugin v4.0.0. The v8.0.0 modernization plan (7 phases, 28 work items) completed successfully that day — see `IMPLEMENTATION_PLAN.md` for the current (later) plan and `docs/archive/` for prior plan versions (v4, v5, v6).

Historical note: at the time of Entry 001 (2026-04-30) the installed plugin cache had a stale `spark-recon/SKILL.md` that didn't match the repo version. This was resolved by v9.3.0 (Entry 007, 2026-07-08 baseline check confirmed cache and origin/main agree) — see D19 for how cache sync actually works (GitHub `autoUpdate`, not manual reinstall).

### Planning System

The project has a mature planning workflow: `/ultra-plan` for deep investigation, `/create-plan` for requirements-driven planning, `/plan-improvements` for codebase analysis, and `/implement-plan` for automated execution via subagent orchestration. All share a unified `references/plan-template.md` template. The template was refined today (2026-04-30) with 7 improvements — see Entry 001.

### Key Learnings (from memory files and CLAUDE.md)

Plugin discovery is fragile and fails silently. The five verified operational rules (CLAUDE.md) are non-negotiable: nested skill dirs, `name` in skill frontmatter, no `name` in command frontmatter, no `tools` in plugin.json, no `hooks` in plugin.json. The hooks.json format migration from array to record format (2026-03-31) was another silent failure. These are documented in both CLAUDE.md and the project memory files.

## Current Baseline

- **Marketplace version:** 3.3.0
- **personal-plugin version:** 10.2.0 (23 commands, 27→28 skills [clear-prep added E015], 10 named agents in `.claude/agents/`, hooks system)
- **bpmn-plugin version:** 4.2.0 (2 skills, bpmn2drawio Python tool)
- **slide-gen version:** 1.2.0 (9 skills, 7-step presentation pipeline)
- **Git:** clean, main branch, verified synced with `origin/main` via `git fetch` (2026-07-16, 0/0 divergence)
- **Last commit:** `c9d3dd4` — docs: close LAB_NOTEBOOK Entry 014 (PR #105 merged 9c12188, personal-plugin 10.2.0)
- **Plugin cache status:** in sync — marketplace source is GitHub (`davistroy/claude-marketplace`) with `autoUpdate: true` (see D19); cache tracks `origin/main` automatically, independent of local working tree state
- **CI/CD:** GitHub Actions — `test.yml` (pytest matrix, per-tool coverage gates, pip-audit, JSON schema validation), `validate.yml` (plugin.json/frontmatter/version-sync checks, ruff, markdownlint)
- **Platform:** Linux (this session); prior sessions ran Windows 11 — see root CLAUDE.md "Dual environment" section

---

## Experiment Log

### Entry 001 — Plan Template Refinements [config] [decision]
**Date:** 2026-04-30
**Duration:** ~30 minutes
**Environment:** Windows 11, Claude Code CLI, repo at `c8e9a15` (clean main)
**Status:** COMPLETE

**Objective:** Review the plan template (`references/plan-template.md`) used by `/ultra-plan`, `/create-plan`, and `/plan-improvements` against best practices and identify improvements.

**Hypothesis:** The template has been battle-tested through a 7-phase/28-item modernization plan but may have gaps, redundancies, or missing fields revealed by that real-world usage. Success criteria: identify concrete, actionable improvements backed by evidence from the live plan.

**Rollback Plan:** N/A — additive changes to a markdown template. `git checkout -- plugins/personal-plugin/references/plan-template.md` if needed.

**Actions & Results:**

1. Read `plan-template.md`, the live `IMPLEMENTATION_PLAN.md`, `ultra-plan/SKILL.md`, and all three consumer commands (`create-plan.md`, `implement-plan.md`, `plan-improvements.md`).
2. Compared template structure against the live plan — found 7 gaps:
   - Live plan had `**Completed:**` header field not in template
   - `Parallelizable` and `Execution Mode` overlapped (two fields, one signal)
   - Phase Summary Table missing `Execution Mode` column despite structural rules defining it
   - No item-level dependency tracking (`Depends On`)
   - Risk Mitigation table had no resolution tracking (`Status` column)
   - Status field heading decoration (`✅ Completed YYYY-MM-DD`) was an implement-plan convention but not formalized
   - No milestone grouping for large plans
3. Implemented all 7 changes to `plan-template.md`
4. Updated `references/templates/planning.md` to match (had stale `Parallelizable` field)
5. Grepped for `Parallelizable` — found references in existing completed plans (backward-compatible per rule 12) and the `planning.md` template (fixed). Consumer commands don't parse it directly.
6. Updated structural rules from 7 to 12 items covering all new fields

**What Worked:**
- Comparing the template against a real completed plan was the most productive analysis vector — immediately surfaced gaps the template spec missed
- The backward compatibility rule (rule 12) was the right design choice — existing plans parse unchanged

**Decision:** Consolidated `Parallelizable` + `Execution Mode` into a single `Execution Mode` field (D9). Added `Depends On` for intra-phase item dependencies (D10). All changes additive and backward-compatible.
- **Alternatives Considered:** Keeping both `Parallelizable` and `Execution Mode` — rejected because they carry the same signal and `Execution Mode` is strictly more expressive

**Follow-ups:**
- A1: Reinstall plugin to sync spark-recon
- A2: Update implement-plan to set `Completed` header on finalization
- A3: Update implement-plan to parse `Depends On` for parallelization map
- A4: Update implement-plan to update Risk Mitigation `Status` during execution

---

### Entry 002 — Gap Analysis Implementation Planning [skill] [template] [decision]
**Date:** 2026-04-30
**Environment:** Windows 11, Claude Code CLI, repo at `c8e9a15` (clean main), personal-plugin v8.0.0
**Status:** COMPLETE
**Duration:** ~45 minutes

**Objective:** Take the gap analysis (`gap-analysis-2026-04-30.md`) comparing the ultra-plan skill against AI-native planning best practices (Spec Kit, Kiro, BMAD, Anthropic patterns) and plan the implementation of all 13 recommended updates across 3 priority tiers.

**Hypothesis:** The gap analysis was built from a reconstructed picture of ultra-plan (couldn't access actual SKILL.md). After comparing recommendations against actual code, expect ~4 recommendations are already covered by the existing pipeline, leaving ~9 genuine improvements. The 5 Tier-1 items should be implementable without structural changes. Tier-2 items (constitution, sub-agents, drift detection) will require ultra-plan SKILL.md rewrite. Tier-3 items are mostly additive and low-risk. Success criteria: produce an IMPLEMENTATION_PLAN.md with concrete file paths, acceptance criteria, and dependency ordering.

**Rollback Plan:** All changes are to markdown skill/command/template files tracked in git. `git checkout -- plugins/personal-plugin/` restores everything. No external state changes.

**Actions & Results:**

Phase 1 (Investigation) — Read all 8 files in the planning pipeline:
- `ultra-plan/SKILL.md` — 5-phase rigid workflow, 183 lines
- `plan-gate/SKILL.md` — 6-path router with complexity classification
- `create-plan.md` — requirements-driven, 5 phases with codebase recon
- `plan-improvements.md` — codebase-driven, 4 phases with sampling strategy
- `implement-plan.md` — subagent orchestrator with state file, parallel execution
- `plan-next.md` — P0-P9 priority matrix for next-action routing
- `plan-template.md` — shared output template, 12 structural rules
- `references/templates/planning.md` — canonical planning command template

Key findings per item logged in conversation. Proceeding to Phase 2 (Interaction Mapping).

Phase 2 (Interaction Mapping) — Identified 6 change sets:
- A: Template (items 1,2,3,5) — all modify plan-template.md
- B: Anti-patterns (item 4) — independent new file
- C: Ultra-plan rewrite (items 6,7,11-fix) — entangled, must be single rewrite
- D: Consumer updates (items 2↓,3↓) — depends on A
- E: Extensions (items 8,9,13) — depends on C
- F: Misc (items 10,12) — independent
Critical path: A→D and C→E. B and F independent.

Phase 3 (Solution Design) — Designed integrated changes per change set with file paths, trade-offs, verification criteria. Key decisions:
- No full rename of ultra-plan (reference fix only) — breaking change not worth it
- Constitution lives in CLAUDE.md, not separate file — avoids artifact sprawl
- Sub-agents only for >5 items — inline investigation is better for small lists
- implement-plan backward compat via fallback from verification_commands to test_command

Phase 4 (Summary Report) — Presented to user for approval. All 13 items covered plus Lab Notebook A2-A4.

Phase 5 (Plan Generation) — Archived completed v8.0.0 plan as `docs/archive/IMPLEMENTATION_PLAN-v6.md`. Generated new IMPLEMENTATION_PLAN.md with 6 phases, 18 work items, ~880 LOC across 16 files.

**Verification:** All 13 gap-analysis items + 3 lab notebook action items traced in Requirement Traceability appendix. Change set groupings preserved. Dependencies reflected in phase ordering.

**What Worked:**
- Reading all 8 pipeline files before investigation was critical — revealed pre-existing bugs (the `/ultraplan` reference ambiguity) and hidden capabilities (Agent tool `model` parameter)
- The gap analysis's reconstructed picture overestimated several gaps that the existing pipeline already covers

**Decision:** Folded Lab Notebook A2, A3, A4 into Phase 5 of the new plan (D11: ACTIVE, supersedes individual action items)

---

### Entry 003 — Gap Analysis Plan Execution [skill] [template] [command]
**Date:** 2026-04-30
**Environment:** Windows 11, Claude Code CLI, repo at `16a275d` (feature/gap-analysis-implementation branch), personal-plugin v8.0.0
**Status:** COMPLETE
**Duration:** ~45 minutes

**Objective:** Execute the 6-phase, 17-work-item IMPLEMENTATION_PLAN.md generated in Entry 002, upgrading the planning pipeline with AI-native best practices from the gap analysis.

**Hypothesis:** All 17 work items are implementable via subagent orchestration with no structural conflicts. Parallel batches within phases should work cleanly since items were designed to touch non-overlapping file sections. The implement-plan workflow should handle the full plan in a single session.

**Rollback Plan:** `git reset --hard 16a275d` to pre-execution state. Each phase also committed independently for granular rollback.

**Actions & Results:**

| Phase | Items | Parallel | Commit | Files Changed |
|-------|-------|----------|--------|---------------|
| 1: Plan Template Enhancements | 1.1, 1.2, 1.3, 1.4 | 1.1+1.3+1.4 parallel, 1.2 sequential | `204d6d6` | 2 (+60/-13) |
| 2: Anti-Patterns + Ultra-Plan Rewrite | 2.1, 2.2, 2.3, 2.4 | 2.1+2.4 parallel, 2.2→2.3 sequential | `b3a0ee7` | 6 (+207/-59) |
| 3: Consumer Updates | 3.1, 3.2, 3.3 | 3.1+3.2 parallel, 3.3 sequential | `a3c8825` | 4 (+195/-24) |
| 4: Ultra-Plan Extensions | 4.1, 4.2, 4.3 | All sequential | `146c35b` | 3 (+173/-6) |
| 5: Implement-Plan Upgrade | 5.1 | Sequential | `c51b456` | 2 (+64/-24) |
| 6: Hook Recipes + AGENTS.md | 6.1, 6.2 | Parallel | `bbb2889` | 8 (+200/-11) |

All 17 work items completed. All pre-commit hooks passed (plugin validation, frontmatter checks). Zero failures.

**What Worked:**
- Parallel subagent dispatch within phases dramatically reduced execution time — 3 items in Phase 1 completed concurrently
- Non-overlapping file assignments prevented merge conflicts in parallel batches
- The implement-plan workflow handled context shedding well — no context window exhaustion despite 17 items
- Pre-commit hooks caught frontmatter issues early (all passed on first attempt)

**What Could Be Better:**
- Phase 2 item 2.2 (constitution + renumber) was the longest single item (~4 min) due to systematic renumbering of all phase references — could benefit from a mechanical rename script
- Testing subagents ran after each phase but couldn't execute actual CLI commands (/validate-plugin) — relied on structural verification

**Follow-ups:**
- A7: Reinstall plugin to sync all changes
- A8: Bump personal-plugin version to 9.0.0

---

### Entry 004 — Validate-Plugin Full Update [command] [config]
**Date:** 2026-04-30
**Environment:** Windows 11, Claude Code CLI, repo at `bbb2889` (feature/gap-analysis-implementation branch), personal-plugin v9.0.0 (uncommitted)
**Status:** COMPLETE
**Duration:** ~15 minutes

**Objective:** Update `/validate-plugin` command with three improvements: (1) fix hardcoded stale example counts, (2) add plan template structural rule validation, (3) add reference file inventory check.

**Hypothesis:** The v9.0.0 pipeline changes added 4 structural rules (13-16) to plan-template.md and created 6 new reference files (anti-patterns.md, adr-template.md, agents-md-template.md, 3 hook references). validate-plugin's example outputs hardcode "15 files" and "3 skills" from pre-v8.0.0 when the actual counts are 24 commands and 24 skills. New validation phases will catch future reference file drift early. Success criteria: all hardcoded counts replaced with `[N]` placeholders; Phase 8.5 validates rules 13-16 by keyword; Phase 8.6 inventories 7 core + 3 hook + 2 subdirectory reference paths.

**Rollback Plan:** `git checkout -- plugins/personal-plugin/commands/validate-plugin.md CHANGELOG.md`

**Actions & Results:**

1. Read full validate-plugin.md (1176 lines across 9 phases + modes)
2. Replaced 9 hardcoded counts with `[N]` dynamic placeholders:
   - "15 files" → "[N] files" (3 occurrences)
   - "3 skills" → "[N] skills" (3 occurrences)
   - "16 markdown files" → "[N] markdown files" (2 occurrences)
   - "21 commands" → "[N] commands" (1 occurrence)
   - "1 file" → "[N] files" (1 occurrence in references/ check)
3. Added Phase 8.5: Plan Template Validation
   - 8.5.1: Template file presence (graceful skip if absent)
   - 8.5.2: Rule enumeration (≥16 rules, no numbering gaps)
   - 8.5.3: Key rule content validation (rules 13-16 keyword checks)
   - 8.5.4: Sizing constraints section check
4. Added Phase 8.6: Reference File Inventory
   - 8.6.1: 7 core reference files with "Required Since" provenance
   - 8.6.2: 3 hook reference files + directory check
   - 8.6.3: patterns/ and templates/ subdirectory presence
5. Updated Phase 9 summary example, --strict example, --report example, --all example, and full usage example to include new phase rows
6. Hardcoded command list in namespace collision example replaced with dynamic discovery note
7. Updated CHANGELOG.md v9.0.0 entry with 2 Added + 1 Changed items

**What Worked:**
- Dynamic `[N]` placeholders prevent stale count drift permanently — no more maintenance burden from adding commands/skills
- Phase 8.5 keyword-based validation is resilient to rule text rewording while catching structural omissions
- Phase 8.6 "Required Since" column documents provenance — helps distinguish v1.0.0-era core files from v9.0.0 additions

**Decision:** Used `[N]` placeholder notation rather than computing actual dynamic counts in examples. Examples exist to show FORMAT, not data — dynamic counts would become stale again on the next change. `[N]` makes it clear the value is computed at runtime.

---

### Entry 005 — Model Routing: Per-Task Tier Assignment + Named Agent Dispatch [command] [skill] [decision]
**Date:** 2026-05-10
**Environment:** Linux, Claude Code CLI, branch `claude/add-model-routing-planning-jT2ml`, personal-plugin v9.0.0
**Status:** IN PROGRESS

**Objective:** Add model routing to the planning pipeline. Each task in a plan should be tagged with a complexity tier at plan-time (haiku/sonnet/opus); `implement-plan` should dispatch to a named sub-agent whose model is pinned in its definition (`.claude/agents/`). An escalation pattern lets sub-agents return `ESCALATE: [reason]` when work is harder than the brief implied, so the orchestrator can re-dispatch at a higher tier.

**Hypothesis:** Per-task tiers with named agents will reduce cost on mechanical work while keeping architectural tasks on Opus. The escalation loop makes plan-time decisions safe without requiring defensive over-spending upfront. Named agents (`haiku-implementer`, `sonnet-implementer`, `opus-implementer`) decouple model selection from plan content — swapping models is a one-line change in the agent file, not a search-and-replace across plans. Success criteria: (1) `plan-template.md` has a `Model Tier` work item field; (2) `create-plan.md` and `plan-improvements.md` populate it using the rubric; (3) `implement-plan.md` dispatches to named agents with escalation; (4) `.claude/agents/` has all three implementer definitions.

**Rollback Plan:** `git checkout -- plugins/personal-plugin/ .claude/` — all changes are additive markdown edits. No external state affected.

**Files Changing:**
- `plugins/personal-plugin/references/plan-template.md` — add `Model Tier` field and Rule 17
- `plugins/personal-plugin/commands/create-plan.md` — add tier rubric to Phase 3.1, update Phase 3.2 hints
- `plugins/personal-plugin/commands/implement-plan.md` — update state file schema, Steps A1/B1 dispatch, add A1b/B1b escalation
- `plugins/personal-plugin/commands/plan-improvements.md` — add Model Tier to work item construction
- `.claude/agents/haiku-implementer.md` (create)
- `.claude/agents/sonnet-implementer.md` (create)
- `.claude/agents/opus-implementer.md` (create)

**Decisions:**
- D14: Name agents `haiku-implementer` / `sonnet-implementer` / `opus-implementer` (not generic `implementer-haiku`). Agent name encodes tier — cleaner than prefix. Model is in frontmatter; plan references agent name only. (Alt: use `model:` param directly in Agent calls — rejected because it couples model selection to plan content; global model swap would require editing every plan.)
- D15: One escalation per item allowed (lower → next tier); accept at highest tier even if imperfect. (Alt: unlimited escalation loop — rejected because it can cycle; capping at one step keeps orchestrator budget bounded.)
- D16: Orchestrator advisory note added to `implement-plan.md` — recommend Opus for large plans. Not enforced programmatically (orchestrator model is user-controlled). (Alt: skip the note — rejected because it's a real trap: cheap orchestrator with wrong tier assignment costs more than its token savings.)

**Status:** COMPLETE
**Duration:** ~30 minutes

**Actions & Results:**

| File | Change | Result |
|------|--------|--------|
| `.claude/agents/haiku-implementer.md` | Created — model: claude-haiku-4-5-20251001, deterministic transform profile + escalation instructions | OK |
| `.claude/agents/sonnet-implementer.md` | Created — model: claude-sonnet-4-6, standard coding profile | OK |
| `.claude/agents/opus-implementer.md` | Created — model: claude-opus-4-7, judgment-heavy profile, BLOCKED (not ESCALATE) for impossible tasks | OK |
| `plan-template.md` | Added `**Model Tier: sonnet**` field between Status and Ref; updated Rule 5 to include Model Tier in order; added Rule 17 with full rubric; updated Rules 15 comment to reference named agents | OK |
| `create-plan.md` | Added step 5 to Phase 3.1 with full haiku/sonnet/opus rubric and escalation criterion guidance; updated Phase 3.2 Execution Hints to note per-item tiers are primary, phase hints supplementary; added orchestrator Opus advisory | OK |
| `implement-plan.md` | Added orchestrator advisory note in Overview; added `item_model_tiers` to state file schema; updated Step 1 subagent prompt to extract per-item tiers; updated Step 2 JSON to include `item_model_tiers`; replaced model-parameter dispatch in A1/B1 with named agent dispatch; added Step A1b (sequential escalation) and updated B2 (parallel escalation) | OK |
| `plan-improvements.md` | Updated "Work Item Construction Guidelines" from 7 to 8 fields — added Model Tier as field 2 with full rubric | OK |

Commit: `97837ca` — 8 files changed, 215 insertions, 29 deletions

**What Worked:**
- Keeping per-item tier as the primary signal and phase-level hints as fallback is the right hierarchy — preserves backward compat (items without Model Tier fall back to default)
- Named agents decouple model selection from plan content cleanly — changing haiku to a newer model is a one-line edit in the agent file
- The "one escalation allowed" cap keeps orchestrator budget bounded without requiring complex loop logic

---

### Entry 006 — Ship build-cfa-deck skill + coordinated v3.2.0 bump [plugin] [config] [decision]

**Date:** 2026-05-14
**Environment:** Linux VM, Claude Code CLI, main at 8574f0c (personal-plugin v9.1.0, marketplace v3.1.0)
**Status:** COMPLETE

**Objective:** Get `build-cfa-deck` skill (CFA-branded PPTX generator) onto main with correct version bumps. Prior attempt (PR #93) failed because it was built on stale local main (69949eb, ~4 commits behind origin/main), causing version collisions with the v9.1.0/v3.1.0 release already shipped via PR #92.

**Hypothesis:** Cherry-picking only the new `build-cfa-deck/SKILL.md` onto current main, then applying correct next-minor bumps (marketplace 3.1.0→3.2.0, personal-plugin 9.1.0→9.2.0, bpmn-plugin 4.0.0→4.1.0, slide-gen 1.0.1→1.1.0), will produce a clean PR with no version conflicts. Expected: PR merges cleanly, `/validate-plugin --all` passes.

**Rollback Plan:** `git checkout -- .` on the branch discards all changes. PR can be closed without merging. No external state affected.

**Root Cause of PR #93 failure:** Session started with local main behind origin/main by 4 commits. The git status injected at session start showed HEAD=69949eb, but `git pull` had not been run, so the working tree was stale. All version-bump math and "drift fixes" in the session were based on incorrect baseline versions. Lesson: always `git pull` at session start before inspecting version state or making version decisions.

**Actions & Results:**
1. Closed PR #93 with explanatory comment
2. Created `feat/build-cfa-deck` from current main (8574f0c)
3. Cherry-picked `build-cfa-deck/SKILL.md` from `release/3.1.0` via `git checkout release/3.1.0 -- <path>`
4. Applied coordinated minor bumps: marketplace 3.1.0→3.2.0, personal-plugin 9.1.0→9.2.0, bpmn-plugin 4.0.0→4.1.0, slide-gen 1.0.1→1.1.0
5. Added CHANGELOG entry for v3.2.0
6. Committed, pushed, created PR #94, auto-reviewed, merged
7. Deleted stale remote branches: `release/3.1.0`, `claude/add-marketplace-integration-skill-wn65y`, `claude/add-model-routing-planning-jT2ml`

**Decision (D17):** The "slide-gen marketplace drift" diagnosed in the earlier session (plugin.json=1.1.0 vs marketplace.json=1.0.1) did not exist on main — the 1.1.0 in local plugin.json was an uncommitted pre-session edit that was never pushed. No fix was needed. Version source of truth is always `origin/main`, not local working tree.

**Decision (D18):** Use `git checkout <branch> -- <path>` to cherry-pick a single file from a stale branch rather than rebasing the whole branch. Rebase would drag in all the conflicting version changes; file-level checkout is surgical.

**What Worked:**
- Identifying that only 1 file was genuinely new across all "updates everywhere" kept the recovery simple
- Inventory-first approach (check all branches, PRs, stash, untracked) before acting prevented further thrashing

---

### Entry 007 — Prime Assessment + Documentation Drift Remediation [config] [decision]

**Date:** 2026-07-08
**Environment:** Linux VM, Claude Code CLI, local `main` at `fb13d93` at session start (repo showed personal-plugin v9.2.0; installed plugin cache already at v9.3.0)
**Status:** COMPLETE
**Duration:** ~25 minutes

**Objective:** Run `/prime` for a full project health assessment (3 parallel Explore agents: identity, architecture, risk), then remediate every documentation-drift finding it surfaced — most notably this notebook's own stale "Current Baseline" section.

**Hypothesis:** `/prime`'s Phase 0 instructions (and this project's CLAUDE.md) treat this notebook as the most authoritative source for future sessions — if its baseline is wrong, every future session inherits the error. Expect: (1) baseline versions here are behind the actual `.claude-plugin/*.json` state, (2) closing the loop requires checking every doc that states versions, not just this notebook. Success criteria: every version string in tracked docs matches both `.claude-plugin/*.json` and `origin/main`.

**Rollback Plan:** All changes are to git-tracked markdown/config files (this notebook, root CHANGELOG.md, CLAUDE.md, .gitignore). `git diff` is fully reviewable; `git checkout -- <file>` reverts any single file. The `git pull --ff-only` was fast-forward only on a clean, zero-divergent working tree — no destructive risk existed.

**Actions & Results:**

1. Ran `/prime` — 3 parallel Explore agents (identity, architecture, risk) plus direct git/gh checks. Confirmed marketplace v3.2.0, bpmn-plugin v4.1.0, slide-gen v1.1.0; IMPLEMENTATION_PLAN.md fully complete (2026-04-30); no open GitHub PRs/issues.
2. Cross-checked the *installed* plugin cache (`~/.claude/plugins/cache/troys-plugins/personal-plugin/`) against the local repo — found cache at **9.3.0**, one version ahead of the local repo's 9.2.0. Traced via `~/.claude/plugins/known_marketplaces.json`: source is GitHub `davistroy/claude-marketplace` with `autoUpdate: true`, last synced 2026-07-07T18:24:15Z.
3. `git fetch origin` revealed local `main` was behind `origin/main` by exactly 1 commit (`d9a7f06`, PR #95, personal-plugin → 9.3.0, spark-recon/spark-audit config refresh) — a direct recurrence of the D17 root cause from Entry 006 ("version source of truth is always `origin/main`, not local working tree"). `git pull --ff-only origin main` — clean fast-forward, zero conflicts.
4. Corrected root `CHANGELOG.md`: added the missing `[personal-plugin v9.3.0] - 2026-06-15` entry (present in `plugins/personal-plugin/CHANGELOG.md` but never mirrored to root).
5. Corrected `CLAUDE.md` "Key References": `IMPLEMENTATION_PLAN.md` was described as "(v8.0.0 modernization)" but the live file actually documents the completed gap-analysis/planning-pipeline plan; updated to match.
6. Added `._*` to `.gitignore` (macOS AppleDouble sidecar files — `.DS_Store` was already covered, `._`-prefixed files were not) and removed the untracked `._.DS_Store` artifact from the working tree.
7. Updated this notebook's Current Baseline section and closed Action Items A1, A7, A8 (see Decision Log D19 and Completed table C11–C13).
8. Committed all four files as `c7efd1d` ("docs: sync documentation to actual repo state; ignore AppleDouble files") — working tree clean after commit.

**Pattern Table — "local clone behind origin" (2nd occurrence):**

| Entry | Symptom | Root Cause | Fix |
|-------|---------|------------|-----|
| 006 (D17) | Version-bump math built on stale main; PR #93 collided with an already-shipped release | Local main was 4 commits behind origin; `git status` was checked but `git pull` never run before reasoning about versions | Treat `origin/main` as the only source of truth for version state |
| 007 (D19) | This notebook's Current Baseline (and local repo) reported personal-plugin 9.2.0; actual origin/main tip was 9.3.0 | Same — local dev clone was 1 commit behind origin, never pulled at session start | Same fix, now formalized as D19 and added to CLAUDE.md's Verified Operational Rules |

**What Worked:**
- Checking the *installed plugin cache* against the repo (not just internal repo consistency) surfaced a real, live drift a repo-only read would have missed entirely.
- Tracing `known_marketplaces.json` → `autoUpdate: true` → GitHub source explained *why* the cache was ahead instead of behind, which reframed A1/A7 as based on an outdated mental model of how sync actually works.

**Decision:** D19 — plugin cache freshness is governed by the marketplace's `autoUpdate` setting against `origin/main`, not by manual local reinstall. Superseded the A1/A7 "reinstall to sync" framing. **Alternatives Considered:** keep issuing manual-reinstall action items every time a skill changes — rejected, it's the wrong lever; what actually matters is keeping the *local dev clone* current with origin before reasoning about versions.

**Follow-ups:** None open. Given this is the second occurrence of the same failure mode (D17, D19), a `git fetch` + origin-divergence check at session start is now also captured as a Verified Operational Rule in root CLAUDE.md.

---

### Entry 008 — Full Plugin Review vs Official Anthropic Guidance [plugin] [skill] [command] [decision]

**Date:** 2026-07-08
**Environment:** Linux VM, Claude Code CLI 2.1.204, main at `c7efd1d` (marketplace 3.2.0, personal-plugin 9.3.0, bpmn-plugin 4.1.0, slide-gen 1.1.0)
**Status:** COMPLETE
**Duration:** ~30 minutes

**Objective:** Comprehensive review of all 3 plugins (24 commands, 35 skills, 12 agent defs, hooks, manifests) against the CURRENT (July 2026) official Anthropic guidance — code.claude.com/docs, Claude Code changelog, anthropics/skills, anthropics/claude-plugins-official, and the Agent Skills engineering post. Deliverable: prioritized recommendations ranked by benefit.

**Hypothesis:** The repo predates several 2026 platform changes (commands/skills unification, new frontmatter fields, agent model aliases); expect findings concentrated in (a) staleness from hardcoded specifics and (b) oversized files vs the official 500-line budget. Success criteria: every recommendation traceable to a fetched official source or a verified repo finding.

**Rollback Plan:** N/A — read-only review; outputs are a new report file + this entry.

**Method:** 4 parallel subagents — official-docs fetch, official-exemplar extraction, mechanical repo inventory (frontmatter matrix / sizes / model IDs / path portability / stale refs), qualitative deep-read of the 11 largest files. Highest-impact claims spot-verified by hand before reporting.

**Key Findings (full detail in `reports/plugin-review-anthropic-guidance-20260708-114842.md`):**
1. **All 9 arch-review plugin agents have zero YAML frontmatter** — they register with no description, all tools, no model control. Biggest functional gap found.
2. **Stale model pins:** sonnet-implementer=`claude-sonnet-4-6`, opus-implementer=`claude-opus-4-7` (current: sonnet-5, opus-4-8); research-topic pins `claude-opus-4-6-20250725` and misuses it as an `agent:` value; visual-explainer hardcodes `claude-sonnet-4-20250514` in 5 modules and `gemini-2.0-flash-exp` in style JSONs. Agent frontmatter now supports aliases (`sonnet`/`opus`/`haiku`/`fable`/`inherit`) — the permanent fix.
3. **Dangling refs:** `/batch` recommended in 4 files but doesn't exist anywhere; `/ultrareview` (deprecated alias → `/code-review ultra`) in 6 places incl. CLAUDE.md; ultra-plan skips Phase 1; validate-plugin checks 16 template rules while the template has 17.
4. **Platform spec changed under us:** commands are now the documented legacy format ("Use skills/ for new plugins"); SKILL.md `name` is now OPTIONAL (defaults to dir name) — house rule D2's rationale is outdated (kept as convention); `disable-model-invocation: true` now removes the description from session context; new fields: `when_to_use`, `arguments`, `user-invocable`, `disallowed-tools`, `shell`, scoped `hooks`.
5. **13 files exceed the official 500-line budget** (top: validate-plugin 1385, implement-plan 1050 with ~90%-duplicate PATH A/B, create-plan 909); model-tier rubric duplicated across 4 files with two *conflicting* framings — same drift class as D17/D19.
6. **Portability:** `C:\Users\Troy Davis\...` paths break explain-project/accessibility-annotator/evaluate-pipeline-output on Linux; prime/SKILL.md is the repo's only CRLF file; no .gitattributes.
7. **Safety gaps:** brain-entry (external POST) is the only skill missing `allowed-tools` and lacks `disable-model-invocation`; unlock (secret loading) also model-invocable.
8. **Clean bills:** manifests spec-clean and richer than official norm; hooks.json format correct; no committed secrets; no forbidden-`name` violations; bpmn-generator and sg-full-workflow are model progressive-disclosure citizens.
9. **New official tooling to adopt:** `claude plugin validate` CLI (CI candidate) and skill-creator's should-trigger/should-not-trigger description-eval loop.

**Output:** 13 recommendations ranked by benefit (R1 agents-frontmatter → R13 polish) in `reports/plugin-review-anthropic-guidance-20260708-114842.md`. Action item A9 opened.

**What Worked:**
- Splitting "what does Anthropic say" (2 web agents) from "what does the repo do" (2 repo agents) made every recommendation attributable to a source-vs-finding pair
- Mechanical awk/grep frontmatter matrixing over ~70 files caught things a read-through would miss (the 0/9 agent frontmatter, the single CRLF file, the single missing allowed-tools)

---

### Entry 009 — Ultra-Plan over R1–R13 [plugin] [skill] [command] [template] [decision]

**Date:** 2026-07-08
**Environment:** Linux VM, Claude Code CLI 2.1.204, main at `c7efd1d`, executing `/ultra-plan "all items R1 through R13"` from A9
**Status:** IN PROGRESS

**Objective:** Run the full ultra-plan rigid workflow (Phase 0 constitution → investigation → interaction mapping → solution design → summary report → plan generation) over the 13 review recommendations, producing an approved IMPLEMENTATION_PLAN.md.

**Hypothesis:** The 13 recommendations decompose into ~8 coherent change sets grouped by file-overlap rather than one-per-recommendation, because implement-plan/create-plan/plan-improvements/validate-plugin each appear in multiple recommendations. Expect investigation to surface interaction constraints (same-file edits must not land in parallel batches) and 1-2 latent defects beyond the review's findings. Success criteria: every R-item traceable into a change set; plan passes create-plan's structural rules; no constraint violations.

**Rollback Plan:** Investigation is read-only. Generated artifacts (2 ADRs with status Proposed, IMPLEMENTATION_PLAN.md on approval) are new files: `rm docs/adr/0005-*.md docs/adr/0006-*.md` and archive-restore for the plan. No existing files modified until plan execution.

**Investigation results (5 parallel Explore clusters + local checks):**
- **Confirmed beyond review:** plan-gate has an entire routing path (Path B.5, 8 references) built on the nonexistent `/batch`; `/batch` total is 15 occurrences, `/ultrareview` 13 (incl. WORKFLOWS.md:93,115 missed earlier); "Claude Opus 4.6" co-author also in test-project.md:323.
- **arch-review agents are NOT read-only** — all 9 write findings files + merge shared `.meta.json` and run Bash probes → R1 frontmatter needs Read/Glob/Grep/Bash/Write/Edit, and `name:` must exactly match filename stems (used as subagent_type).
- **Latent arch-review design issue:** prose-level `isolation: worktree` (SKILL.md:95,128) likely orphans findings files in discarded worktrees; the `.meta.json` collision it guards against is better fixed with per-agent meta files.
- **Official validator confirms R1 independently:** `claude plugin validate --strict ./plugins/personal-plugin` FAILS today on the missing agent frontmatter. bpmn-plugin and slide-gen pass. Marketplace manifest gets 2 warnings: `metadata.marketplace_version`/`schema_version` are unknown fields Claude Code ignores at load time.
- **visual-explainer model config is effectively dead:** `config.claude_model` is consumed by one module only; cli.py construction sites (940, 1102) never pass `model=`, so hardcoded `DEFAULT_MODEL` constants are the real runtime values. Styles-JSON `TargetModelHint` (`gemini-2.0-flash-exp`) has zero consumers — dead config.
- **Planning-family duplication precisely mapped:** rubric byte-identical in create-plan:438-440 ≡ plan-improvements:481-483 (canonical = template rule 17); plan-improvements' Execution-Hints framing violates template rule 15's column schema; implement-plan PATH A/B differ ONLY on batch cardinality (state keys, background dispatch, commit template, plural text) — prompts already verbatim-shared.
- **Portability:** all C:\ paths map to existing Linux equivalents except `~/dev/info/technical-document-structure-template.md` (missing on VM — sync gap); build-cfa-deck's `~/dev/stratfield` works on both machines (synced repo) → no change needed. CRLF affects prime/SKILL.md AND `.markdownlint.json`.
- **ultra-plan renumber is safe:** plan-gate never references ultra-plan phase numbers.
- **wiki skill has no `paths:`** and documents that injected CLAUDE.md rules handle auto-maintenance → create-wiki's `paths:` auto-activation is redundant; drop rather than move.

**Decisions (approved with plan):**
- **D20 (ADR-0005):** Agent `model:` fields use aliases (`haiku`/`sonnet`/`opus`), not pinned IDs. Pins drifted twice undetected. Alt: pinned + periodic review — rejected, proven failure mode.
- **D21 (ADR-0006):** Skills-first authoring policy — new functionality ships as skills; commands legacy-frozen; new-command deprecated with pattern support ported into new-skill; NO mass migration of the 24 existing commands. Alt: mass-migrate — rejected (churn, muscle-memory breakage, zero functional gain).

**Plan generation (user approved "implement"):**
1. Archived the completed gap-analysis plan: `git mv IMPLEMENTATION_PLAN.md docs/archive/IMPLEMENTATION_PLAN-v7.md` — OK.
2. Routed through `/create-plan` per ultra-plan Phase 6b (discovery/recon/scope-confirmation satisfied by ultra-plan analysis per 6c mapping).
3. Generated fresh `IMPLEMENTATION_PLAN.md`: **8 phases, 35 work items** (~4,100 LOC churn, ~75 files), all items PENDING with per-item Model Tier (3 opus: 4.4 implement-plan PATH collapse, 5.1 validate-plugin refactor; 8 haiku mechanical; rest sonnet). Structure verified: markers ×4, DoD blocks ×8, R1–R13 fully traced, sizing caps respected (wide-shallow items 8.2/8.3 documented).
4. Approved defaults encoded: personal-plugin → 10.0.0 (major: new-command deprecation per v5.x/v8.0.0 precedent), bpmn-plugin 4.2.0, slide-gen 1.2.0, marketplace 3.3.0; marketplace manifest CI-validated non-strict (runtime-ignored `metadata.*version` house fields retained); lab-notebook + create-wiki locked down, create-wiki drops redundant `paths:`.
5. Noted: `reports/` is gitignored — plan traceability anchors to tracked E008/E009 + ADRs instead. AGENTS.md absent (generation offered to user as optional follow-up, not blocking).

**Status:** COMPLETE (planning). Execution is A9's next step via `/implement-plan`.
**Duration:** ~50 minutes (investigation ~25, design/report ~15, plan generation ~10)

---

### Entry 010 — Plan Execution: /implement-plan --auto-merge, full run [plugin] [skill] [command] [ci] [config]

**Date:** 2026-07-08
**Environment:** Linux VM, Claude Code CLI 2.1.204, branch `feat/guidance-modernization-v10` from `c7efd1d`; checkpoint commit `f6678d0` (plan + ADRs + E008/E009); orchestrator on Fable 5
**Status:** IN PROGRESS

**Objective:** Execute all 8 phases / 35 work items of IMPLEMENTATION_PLAN.md continuously (no phase pauses), dispatching per-item model tiers to named implementer sub-agents (haiku/sonnet/opus per plan; user-approved). Orchestrator does no work-item content itself. Ends with PR + auto-merge (user-approved; Entry 006 precedent).

**Hypothesis:** All 35 items are completable by tiered sub-agents against the plan's line-precise specs. File-disjoint parallel batches (verified at interaction-mapping time) prevent write conflicts without worktree isolation. The two opus items (4.4 PATH collapse, 5.1 validate-plugin refactor) are the long poles and the likeliest ESCALATE/iteration sources. Success criteria: every phase's Definition of Done green, `claude plugin validate --strict` passes all plugins, PR merged, versions 10.0.0/4.2.0/1.2.0/3.3.0 live on main.

**Rollback Plan:** Per-item/per-batch commits on the feature branch — `git revert <sha>` for any single item; deleting the branch abandons the whole run (main untouched until squash-merge). `.implement-plan-state.json` (gitignored) enables resume after interruption. Auto-merge is squash — one revert on main undoes the entire release if needed post-merge.

**Execution deviations from the loaded implement-plan workflow (logged up front):**
1. No worktree isolation for sub-agents — the workflow's `isolation: worktree phase-[N]` prose is the exact harness-fighting pattern item 4.4 removes; graceful-degradation clause invoked. File-disjoint batches + ≤3 concurrent cap provide the safety.
2. Implementation sub-agents do NOT edit IMPLEMENTATION_PLAN.md (avoids concurrent same-file writes across parallel agents); a single haiku bookkeeper agent per batch flips Status/heading/risk-table entries after results collect.
3. Startup plan-scan subagent skipped — the orchestrator authored the plan this session; state file written directly from source knowledge.

**Phase results (logged as they complete):**

**Phase 1 verification (testing agent, 2026-07-08):**
- *Objective:* Run Phase 1 DoD suite (pytest, ruff, markdownlint, pre-commit, dangling-ref grep, stale-model-ID grep); fix in-scope failures.
- *Hypothesis:* Phase 1's 13 markdown edits pass all checks; any failure is either pre-existing Python debt or a missed staleness site. Success = all 6 commands pass or remaining failures proven pre-existing.
- *Rollback plan:* Both fixes are single-line text edits in git-tracked files — `git checkout -- <file>` reverts. N/A for read-only checks.
- *Results:*
  - pytest `tests/`: PASS — 67/67 (via `uv run --no-project --with pytest --with jsonschema --with pyyaml`; system python3 has no pytest — CI installs it, env-only gap; no `python` alias on this VM).
  - ruff: FAIL, PRE-EXISTING — 41 errors across 25 `.py` files (bpmn2drawio tests, feedback-docx test, scripts/*.py). No Python touched by Phase 1; identical on HEAD.
  - markdownlint: FAIL, PRE-EXISTING — 3× MD012 in `tests/fixtures/invalid-plugin/commands/*.md` (unchanged since v2.4.0, cb3aec6). All 13 Phase-1 files lint clean.
  - dangling refs (`/batch|/ultrareview`): PASS — zero hits. Note: the DoD command's `--include='*.md'` appears *after* `--`, so GNU grep treats it as a filename (stderr warning, harmless); also the shell's `grep` is a Claude Code ugrep wrapper — verified with `command grep` and corrected flag order.
  - stale model IDs: FAIL initially — 2 sites Phase 1 missed: `references/api-key-setup.md:36` (`claude-opus-4-6-20250725`) and `deprecated/setup-statusline.md:354` ("Claude Opus 4.5"). Both are Staleness-Sweep-class fixes (plan line 201 excludes only CHANGELOG/LAB_NOTEBOOK/docs/archive — deprecated/ is in scope for this grep). Fixed: api-key-setup → `claude-opus-4-8` (matches 1.5's convention + claude-api skill current-alias table; alias form, no date suffix); setup-statusline → "Claude Opus" (model-agnostic per 1.2's never-goes-stale principle; any "4.x" re-matches the DoD pattern). Re-run: zero hits — PASS. Both edited files lint clean.
  - pre-commit: PASS — exit 0 with empty index (by design — validates staged files only); staged-variant run against the 10 Phase 1 command/skill files: 0 errors, 3 pre-existing warnings (no help skill in any plugin), index restored via `git reset`.
- *Pre-existing debt surfaced (candidate Action Items):* (1) ruff: 41 errors / 32 auto-fixable in 25 untouched `.py` files; (2) markdownlint: 3× MD012 in `tests/fixtures/invalid-plugin/commands/`; (3) this VM has no `python` alias and no pytest for system python3 — DoD's literal `python -m pytest` cannot run here without `uv run` or a venv.

**Phase 2 verification (testing agent, 2026-07-08):**
- *Objective:* Run Phase 2 DoD suite — repo pytest, visual-explainer pytest+coverage (≥65%), ruff, markdownlint, EOL check, Windows-path grep, lockdown count (=8), frontmatter YAML sanity on the 4 locked-down skills. Fix in-scope failures (≤3 attempts each); pre-existing debt reported, not fixed.
- *Hypothesis:* Phase 2's frontmatter lockdowns, path rewrites, .gitattributes renormalization, and visual-explainer model plumbing pass all 8 checks; ruff shows exactly the 41 pre-existing errors (nothing new in visual-explainer src/tests); markdownlint shows only 3× MD012 fixture debt. Success = all 8 pass or residual failures proven pre-existing.
- *Rollback plan:* Checks are read-only. Any fix is an edit to a git-tracked file — `git checkout -- <file>` reverts (staged renormalization in index left untouched). N/A otherwise.
- *Results:* ALL 8 PASS on first run — zero fixes needed.
  - repo pytest `tests/`: PASS — 67/67, exit 0 (same uv invocation as Phase 1).
  - visual-explainer suite (`uv run --extra dev python -m pytest tests/` from tool dir): PASS — 607 passed, 2 skipped, 26s; coverage TOTAL **67%** ≥ 65% gate. Both skips are pre-existing conditional guards in files Phase 2 never touched: `test_image_evaluator.py:489` (resize threshold) and `test_integration.py:111` (needs `ANTHROPIC_API_KEY`). Model-plumbing edits (api_setup, cli, config, image_evaluator, prompt_generator, prompt_refiner + conftest/test updates) fully green.
  - ruff: FAIL exit-wise, PRE-EXISTING ONLY — exactly 41 errors, per-file distribution verified with `--output-format concise | cut -d: -f1 | sort | uniq -c`: scripts/generate-help.py 9, scripts/update-readme.py 4, bpmn2drawio tests 27, feedback-docx test 1 (Σ=41). **Zero findings in visual-explainer src/tests** → nothing new from Phase 2's Python changes.
  - markdownlint: FAIL exit-wise, PRE-EXISTING ONLY — exactly the 3 known MD012 in `tests/fixtures/invalid-plugin/commands/` (deliberately invalid fixtures). All Phase 2 markdown (4 lockdown skills, 3 path-rewrite skills, styles/README) lint clean.
  - EOL (DoD): PASS — `git ls-files --eol | command grep -cE 'i/(crlf|mixed)'` = 0. Renormalization of prime/SKILL.md + .markdownlint.json effective; .gitattributes doing its job.
  - Windows paths (DoD): PASS — `command grep -rn 'C:\\Users\|C:/Users' plugins/ --include='*.md'` = no matches.
  - Lockdown count (DoD): PASS — exactly 8 skills with `disable-model-invocation: true` (arch-review, brain-entry, create-wiki, lab-notebook, release-plugin, ship, unlock, visual-explainer) = 4 pre-existing + 4 new.
  - Frontmatter sanity: PASS — brain-entry, unlock, lab-notebook, create-wiki all start with `---`, no BOM, no CRLF, YAML parses to dicts with name/description/allowed-tools/disable-model-invocation (lab-notebook also `effort`).
- *Environment:* Linux VM, ruff 0.6.9 (~/.local/bin), Python 3.11.14 via uv, pytest 9.1.1 (tool venv), markdownlint-cli via npx. Staged renormalization left untouched in index; no commits made.
- *Duration:* ~4 minutes wall (suites run in parallel).

**Phase 3 verification (testing agent, 2026-07-08):**
- *Objective:* Run Phase 3 DoD suite — repo pytest, `claude plugin validate --strict` on personal-plugin, agent frontmatter loop, name=stem check on all 9 agents, implementer model-alias check, markdownlint, stale `findings/.meta.json` grep. Fix in-scope failures (≤3 attempts); pre-existing debt reported, not fixed.
- *Hypothesis:* Phase 3's agent frontmatter + per-agent meta contract + dispatch-by-name rewrites pass all 7 checks; markdownlint shows only the 3 known MD012 fixture errors. Success = all pass or residual failures proven pre-existing.
- *Rollback plan:* Checks are read-only. Any fix is an edit to a git-tracked markdown file — `git checkout -- <file>` reverts. N/A otherwise.
- *Initial results:* 6/7 PASS. Check 7 FAIL — 2 stale shared-meta refs in `plugins/personal-plugin/skills/arch-review/SKILL.md`: line 40 (Step 1 seeds `findings/.meta.json` with `{}`) and line 242 (terminal summary prints `Coverage meta: arch-review/findings/.meta.json`). Root cause: Phase 3's per-agent meta rewrite updated Step 3 (dispatch prompt), Step 4 (glob `*.meta.json`), and both arch commands, but missed Step 1 setup and Step 6 summary — vestiges of the old shared/merged meta contract. Under per-agent meta, no seeding is needed (each agent writes `findings/<agent-name>.meta.json` itself); removing the seed line orphans `WRITE_META`, so `--no-meta` must be rewired into dispatch-prompt construction to stay functional.
- *Fix (arch-review/SKILL.md only):* (1) drop the `.meta.json` seed line from Step 1 + note per-agent meta; (2) reword the Step 1 caution (its "redirection-syntax error" specifics described the removed seed line); (3) Step 3 gains a `WRITE_META`-false branch — omit Meta output path, instruct agent to skip meta; (4) Step 6 summary line → `findings/*.meta.json (one per agent)`; (5) `--no-meta` flag doc → "per-agent `.meta.json` files".
- *Post-fix results:* stale-ref grep clean (exit 1, no matches); `WRITE_META` still consumed (Step 3); edited file markdownlint-clean; `claude plugin validate --strict` still passes; repo pytest unaffected (67/67).
- *Final:* ALL 7 PASS (markdownlint pass-with-preexisting: exactly the 3 known MD012). Environment: Linux VM, Claude Code CLI 2.1.204, Python 3.11.14/pytest 9.1.1 via uv, markdownlint-cli via npx. No commits made.

**Phase 4 verification (testing agent, 2026-07-08):**
- *Objective:* Run Phase 4 DoD suite — repo pytest; line budgets (create-plan ≤500, plan-improvements ≤500, implement-plan ≤650); rubric single-source grep (`deterministic transformations` absent from commands/); markdownlint; pointer integrity for the 4 new reference files; implement-plan PATH-collapse spot-audit (6 sub-checks); `claude plugin validate --strict`. Fix in-scope failures (≤3 attempts); pre-existing debt reported, not fixed.
- *Hypothesis:* Phase 4's planning-family consolidation (create-plan 470 / plan-improvements 490 / implement-plan 573 lines; 4 new references) passes all 7 checks; markdownlint shows only the 3 known MD012 fixture errors. Success = all pass or residual failures proven pre-existing.
- *Rollback plan:* Checks are read-only. Any fix is an edit to a git-tracked markdown file — `git checkout -- <file>` reverts. N/A otherwise.
- *Initial results:* 6/7 PASS — pytest 67/67; line budgets 470/490/573; rubric grep clean (full rubric only in `references/plan-template.md` rule 17); markdownlint exactly the 3 known MD012; pointer sweep: all 6 `references/*.md` pointers across the three commands resolve, the 4 new files at 114/163/416/86 lines (all >50); strict validate exit 0. Check 6 (spot-audit) 5/6 sub-checks — FAIL on allowed-tools: `Agent` present and standalone `Task` correctly dropped (present at 8574f0c), but `TaskCreate/TaskUpdate/TaskOutput` never added even though the collapsed body instructs their use (lines 92, 165, 220, 268, 270, 359). Root cause: 4.4 rewrote the body's tool contract (Agent = subagents, Task\* = tracking only) but never touched the frontmatter line. Change-side bug, not a stale check.
- *Fix (implement-plan.md frontmatter only):* allowed-tools gains `TaskCreate, TaskUpdate, TaskList, TaskOutput` after `Agent` (TaskList included — body line 165 instructs its use). Single-line replacement; line count unchanged at 573.
- *Post-fix results:* allowed-tools grep shows Agent + all four Task-tracking tools, no standalone `Task` token; `claude plugin validate --strict` still exit 0; file still 573 lines; markdownlint on the edited file clean.
- *4.2 escalation note:* create-plan consolidation escalated sonnet→opus — the item's ≤500-line target conflicted with its own byte-intact protection clause; opus resolved by relocating illustration blocks only → 470 lines, zero behavior change.
- *4.4 ledger audit:* confirmed — no PATH A/PATH B tokens; exactly one implementer prompt (L254, "the ONLY implementer prompt") and one testing prompt (L288) with a single "ALL_TESTS_PASS confirmation" instruction (L307); both commit-message forms present (L354: `Complete [WORK_ITEM_NAME]` single, `Complete [PHASE_NAME]:` batch); `in_progress_batch` documented at L48/113/126/176/189; allowed-tools contract correct post-fix.
- *Final:* ALL 7 PASS (markdownlint pass-with-preexisting: exactly the 3 known MD012). Environment: Linux VM, Claude Code CLI 2.1.204, Python 3.11 via uv, markdownlint-cli via npx. No commits made. LEARNINGS.md created at repo root with the 4.2 escalation and 3.3 grep-scope lessons.

**Phase 5 verification (testing agent, 2026-07-08):**
- *Objective:* Run Phase 5 DoD suite — repo pytest; line budgets on the 9 progressive-disclosure refactors (validate-plugin 675, research-topic 421, ship 437, clean-repo 449, finish-document 402, bpmn-to-drawio 340, create-wiki 367, evaluate-pipeline-output 495, test-project 468; each ≤ stated +5); pointer integrity for all Phase 5 reference extractions; markdownlint; `claude plugin validate --strict` on personal-plugin AND bpmn-plugin; orphaned-content checks (no `Proactive Triggers` in ship; validate-plugin Phase 8.6 required-set includes plan-append-guide + validation-output-examples); schemas sanity (questions.json/answers.json exist for finish-document's pointers). Fix in-scope failures (≤3 attempts); pre-existing debt reported, not fixed.
- *Hypothesis:* Phase 5's extractions (8 new reference files, 9 slimmed sources) pass all 7 checks; markdownlint shows only the 3 known MD012 fixture errors. Success = all pass or residual failures proven pre-existing.
- *Rollback plan:* Checks are read-only. Any fix is an edit to a git-tracked markdown file — `git checkout -- <file>` reverts. N/A otherwise.
- *Results:* ALL 7 PASS on first run — zero fixes needed.
  - repo pytest `tests/`: PASS — 67/67, exit 0, 0.21s (same uv invocation as Phases 1-4); no test asserted pre-Phase-5 validate-plugin/command content, so no stale-test adjudication needed.
  - Line budgets: PASS — all nine land *exactly* at their stated counts (675/421/437/449/402/340/367/495/468; 0 over, +5 tolerance unused). validation-output-examples.md confirmed at 1018 lines.
  - Pointer integrity: PASS — DoD grep (9 reference names across `plugins/**/*.md`, excluding `references/` lines) surfaces one bare mention, `validate-plugin.md:475` (`validation-output-examples.md` inside the Phase 8.6 required-set list) → file exists. All 8 Phase 5 reference files exist on disk: personal-plugin/references/{validation-output-examples, research-provider-protocols, ship-output-templates, clean-repo-examples, claude-md-wiki-section, wiki-readme-template}.md, bpmn-plugin/references/bpmn2drawio-reference.md, evaluate-pipeline-output/references/{report-format, evaluator-guidance}.md (skill-local). Every in-file pointer inspected resolves.
  - markdownlint: FAIL exit-wise, PRE-EXISTING ONLY — exactly the 3 known MD012 in `tests/fixtures/invalid-plugin/commands/`; all Phase 5 sources and new reference files lint clean.
  - `claude plugin validate --strict`: PASS — both personal-plugin and bpmn-plugin, exit 0.
  - Orphaned content: PASS — `Proactive Triggers` absent from ship/ (grep exit 1); validate-plugin required-set carries both `plan-append-guide` (×1) and `validation-output-examples` (×44 total mentions in file).
  - Schemas sanity: PASS — `schemas/questions.json` and `schemas/answers.json` both exist for finish-document's schema pointers.
- *Notable:* 5.1's validate-plugin refactor is a 44-pointer extraction to validation-output-examples.md with a checks-intact audit — all validation logic retained in the command; only output examples moved. 5.2 (research-topic 421) and 5.3 (ship 437) are documented-dense outcomes: above the original aspiration but accepted as dense-and-correct at those counts, and both hold their stated budgets exactly.
- *Observation (not a failure, not fixed):* bpmn-to-drawio's 4 new pointers use the `../references/bpmn2drawio-reference.md` idiom — literally one level short from the skill dir, but it mirrors the file's 2 pre-existing `../references/BPMN-to-DrawIO-Conversion-Standard.md` pointers (present at HEAD d903277), and the plugin has exactly one references/ dir, so runtime resolution is unambiguous. Consistency with in-file convention preserved; flag for a future sweep if path pedantry ever matters.
- *Final:* ALL 7 PASS (markdownlint pass-with-preexisting: exactly the 3 known MD012). Environment: Linux VM, Claude Code CLI 2.1.204, Python 3.11 via uv, markdownlint-cli via npx, HEAD d903277 (Phase 5 changes uncommitted in working tree). No commits made.

**Phase 6 verification (testing agent, 2026-07-08):**
- *Objective:* Run Phase 6 DoD suite — repo pytest; deprecation state (`commands/new-command.md` gone, `deprecated/new-command.md` present); zero active `new-command` refs outside deprecated/CHANGELOG/LAB_NOTEBOOK/IMPLEMENTATION_PLAN; pattern flow coherence (new-skill.md Pattern Adaptation ↔ skill-patterns.md ↔ generator.md spot-check); scaffold-plugin skills-first defaults (`--with-commands` legacy + ADR-0006, no commands/ in default tree); `claude plugin validate --strict`; markdownlint; README coherence (23 commands, no new-command row). Fix in-scope failures (≤3 attempts); stale tests updated (counts 24→23), never resurrect the command; pre-existing debt reported, not fixed.
- *Hypothesis:* Phase 6's new-command deprecation, new-skill `--pattern` support, and scaffold skills-first flip pass all 8 checks; any pytest failure on the deprecation is a stale test to update, not a regression. Success = all pass or residual failures proven pre-existing.
- *Rollback plan:* Checks are read-only. Any fix is an edit to a git-tracked file — `git checkout -- <file>` reverts. N/A otherwise.
- *Results:* ALL 8 PASS on first run — zero fixes needed, zero stale tests.
  - repo pytest `tests/`: PASS — 67/67, exit 0, 0.19s (same uv invocation as Phases 1-5). No test asserted the old 24-count or `commands/new-command.md` presence — no stale-test adjudication needed.
  - Deprecation state: PASS — `test ! -f commands/new-command.md && test -f deprecated/new-command.md` exit 0.
  - Zero active refs: PASS — DoD grep over plugins/ README.md WORKFLOWS.md CLAUDE.md (excluding deprecated/CHANGELOG/LAB_NOTEBOOK/IMPLEMENTATION_PLAN) exit 1, no matches. 15-reference sweep held.
  - Pattern flow coherence: PASS — generator.md frontmatter has description/argument-hint/effort/allowed-tools and NO `name`, plus the exact `# NOTE: Do NOT add a 'name' field — that breaks command discovery (name is skills-only)` line that Pattern Adaptation rule 3 quotes verbatim and deletes; rule 1 inverts the template's implied flat `commands/[name].md` placement to `skills/[name]/SKILL.md`; rule 2 inserts `name:` first; rule 6's `{{COMMAND_NAME}}`→`[skill-name]` mapping covers generator.md's `{{COMMAND_NAME}}` uses, and its leave-in-place list matches the template's pattern-specific placeholders (`{{ARG_NAME}}`, `{{OUTPUT_LOCATION}}`, etc.). skill-patterns.md table lists all 8 patterns; all 8 template files exist in references/templates/ (+ default skill.md).
  - Scaffold defaults: PASS — `--with-commands` documented as legacy with ADR-0006 at 5 sites (argument-hint, flag doc, dry-run preview, Phase 3, conditional block); default tree is `.claude-plugin/ + skills/ + references/` only — commands/ created solely under explicit `--with-commands`.
  - `claude plugin validate --strict` personal-plugin: PASS — exit 0.
  - markdownlint: FAIL exit-wise, PRE-EXISTING ONLY — exactly the 3 known MD012 in `tests/fixtures/invalid-plugin/commands/`; all Phase 6 markdown (new-skill.md, skill-patterns.md, scaffold-plugin.md, README) lint clean.
  - README coherence: PASS — line 41 reads "23 commands and 24 skills"; command table has no new-command row; `commands/*.md` on disk = 23, matching.
- *Final:* ALL 8 PASS (markdownlint pass-with-preexisting: exactly the 3 known MD012). Environment: Linux VM, Claude Code CLI 2.1.204, Python 3.11.14/pytest 9.1.1 via uv, markdownlint-cli via npx, HEAD 9991c46 on feat/guidance-modernization-v10 (Phase 6 changes in working tree). No commits made.

**Phase 7 verification (testing agent, 2026-07-08):**
- *Objective:* Run Phase 7 DoD suite — repo pytest; workflow YAML sanity (`plugin-validate` job in `.github/workflows/validate.yml`); markdownlint; CLAUDE.md consistency (stated counts vs disk, ADR-0005/ADR-0006 refs); description-triggers eval structure (14 scenarios, `type: skill` frontmatter). Fix in-scope failures (≤3 attempts); pre-existing debt reported, not fixed.
- *Hypothesis:* Phase 7's plugin-validate CI job (pinned @2.1.204), new eval file, and CLAUDE.md refresh pass all 5 checks; markdownlint shows only the 3 known MD012 fixture errors; a workflow test asserting the old job list is the only stale-test candidate. Success = all pass or residual failures proven pre-existing.
- *Rollback plan:* Checks are read-only. Any fix is an edit to a git-tracked file — `git checkout -- <file>` reverts. N/A otherwise.
- *Results:* ALL 5 PASS on first run — zero fixes needed, zero stale tests.
  - repo pytest `tests/`: PASS — 67/67, exit 0, 0.20s (same uv invocation as Phases 1-6). No test asserted a stale job list — no adjudication needed.
  - Workflow YAML: PASS — `yaml.safe_load` parses validate.yml; jobs = [validate, python-lint, lint-markdown, plugin-validate]; `plugin-validate` present.
  - markdownlint: FAIL exit-wise, PRE-EXISTING ONLY — exactly the 3 known MD012 in `tests/fixtures/invalid-plugin/commands/`; refreshed CLAUDE.md and the new eval file lint clean.
  - CLAUDE.md consistency: PASS — stated `commands/ (23)` matches disk (23 `commands/*.md`); skills listing enumerates 24 names matching 24 skill dirs on disk; ADR-0005 refs ×2 (lines 24, 164) and ADR-0006 refs ×3 (lines 19, 20, 228) present.
  - Eval structure: PASS — `evals/skills/description-triggers.eval.md` has exactly 14 `### S` scenarios; frontmatter carries `command: description-triggers`, `type: skill`, `fixtures: []`.
- *Final:* ALL 5 PASS (markdownlint pass-with-preexisting: exactly the 3 known MD012). Environment: Linux VM, Claude Code CLI 2.1.204, Python 3.11.14/pytest 9.1.1 via uv, markdownlint-cli via npx (Phase 7 changes in working tree). No commits made.

**Phase 8 + run closure (orchestrator, 2026-07-08):**
- Phase 8 (6 items): 8.1 big-5 negative scope (each clause mapped to a guarding eval scenario); 8.2 fold ×12 personal skills; 8.3 fold ×9 slide-gen + qualitative cost; 8.4 mechanical polish (effort ×8, plan-next argument-hint + stale-schemas fix, hooks statusMessage ×2); 8.5 per-plugin README+LICENSE ×3; 8.6 coordinated release 10.0.0/4.2.0/1.2.0/3.3.0 + both CHANGELOGs. Commit `379bbc5`.
- **Regression caught in-run:** 8.2's folds wrote unquoted `Suggest when:` into 12 YAML descriptions — plain-scalar colon broke strict parsing; 8.6's final strict-validate sweep caught it, fixed uniformly (`when:` → `when —`). Exactly the failure class the new CI plugin-validate job guards.
- **Run totals:** 35/35 items COMPLETE across 8 phases; commits f6678d0 (checkpoint), a672970, 220a8fd, 07b8a33, d903277, 9991c46, 807f8fb, 3c041b5, 379bbc5; 1 escalation (4.2 sonnet→opus); 0 failed items; 3 real integration gaps caught by phase testing (3.3 meta-seed, 4.4 allowed-tools tracking tools, 8.2 YAML colon). Every phase's DoD green; official validator strict-passes all three plugins.
- **What worked:** per-item tier dispatch with named agents; phase-boundary testing agents; the illustration-vs-logic authority clause (added after 4.2's escalation — prevented repeat escalations across all five Phase 5 items); file-disjoint parallel batches (zero write conflicts across 24 parallel dispatches).
- **Status:** COMPLETE. Duration ~3.5 h wall-clock. PR #96 merged (squash `6c40719`) at 2026-07-08T21:47Z; branch deleted; local main reset to origin (the morning docs-sync commit `c7efd1d` was never pushed standalone — its content rode in the squash; 1-and-1 divergence resolved by reset, no loss).
- **Post-merge hotfix 1:** CI's `Ruff format check` step (`ruff format --check plugins/*/tools/*/src/ tests/`) failed on main — item 2.4's cli.py edit wasn't formatter-clean. Root cause: the run's DoD used `ruff check` (lint) but never CI's `ruff format --check`; invocation gap between DoD and CI. Fixed with one `ruff format` pass on cli.py (+6/−2, behavior-neutral), hotfixed to main as `db80808`. Lesson: DoD commands must be lifted verbatim from CI workflow steps, not paraphrased.
- **Post-merge hotfix 2 (unrelated to release):** pip-audit CI job failed on a freshly published CVE — pypdf2 3.0.1 / PYSEC-2026-1835. Advisory "fix 3.9.0" refers to the SUCCESSOR package: PyPDF2 ended at 3.0.1 (verified via PyPI; project continued as `pypdf`). Migrated visual-explainer to `pypdf>=3.9.0` (resolves 6.14.2, verbatim drop-in for the PdfReader/pages/extract_text surface used): pyproject ×2 groups, concept_analyzer.py import, README dep list. Verified: 607 tests pass, local pip-audit "No known vulnerabilities", ruff format/check clean. Would have failed on ANY push today — upstream disclosure, not a release regression.

---

### Entry 011 — Force plugin cache update to 10.0.0 + arch-review smoke test (A10) [plugin] [config]

**Date:** 2026-07-08
**Environment:** Linux VM, Claude Code CLI 2.1.204, main at `4194ca6` (post-release + 2 hotfixes), installed cache at personal-plugin 9.3.0 pre-test
**Status:** IN PROGRESS

**Objective:** Force the installed plugin cache to pick up personal-plugin 10.0.0 (plus bpmn 4.2.0 / slide-gen 1.2.0) from origin/main, then smoke-test arch-review dispatch against the NEW agent definitions (frontmatter tools/model/description + per-agent meta contract).

**Hypothesis:** Official CLI plugin-update commands refresh the marketplace clone and cache without manual file surgery. Expected wrinkle: THIS session's agent registry snapshotted at session start — a dispatched `personal-plugin:solutions-architect` may still run the OLD (frontmatter-less) definition even after the cache updates. Discriminator: old body says "merge shared findings/.meta.json"; new body says "write findings/<agent-name>.meta.json"; old registration = all tools, new = Read/Glob/Grep/Bash/Write/Edit only. Success criteria: cache dir shows 10.0.0 with frontmattered agents on disk; smoke dispatch either exercises the new contract (ideal) or proves the session-snapshot behavior (documented, verified in next session).

**Rollback Plan:** Cache is rebuildable API-managed state — worst case `rm -rf ~/.claude/plugins/cache/troys-plugins` + `/plugin install` regenerates from GitHub (D19). Marketplace clone: `git -C ~/.claude/plugins/marketplaces/troys-plugins` is a plain clone of origin/main — re-cloneable. No repo files affected.

**Actions & Results:**

1. `claude plugin marketplace update troys-plugins` — marketplace clone refreshed from GitHub. OK.
2. `claude plugin update <name>` failed with "not found" for bare names — plugins are registered as `name@marketplace`; `claude plugin update personal-plugin@troys-plugins` (and bpmn, slide-gen) succeeded: **9.3.0→10.0.0, 4.1.0→4.2.0, 1.1.0→1.2.0**, each with "Restart to apply changes."
3. Cache verification on disk: `cache/troys-plugins/personal-plugin/10.0.0/` exists; `agents/solutions-architect.md` carries the full new frontmatter (name/description/tools/model: inherit/effort: high); per-agent meta contract present; brain-entry lockdown (`disable-model-invocation` + `allowed-tools: Bash(curl:*)`) live in cache.
4. **Smoke test (discriminator design):** dispatched `personal-plugin:solutions-architect` asking it to quote its meta-output instruction verbatim and write findings+meta using its prescribed FILENAMES. Result: SMOKE_OK mechanically (3-finding mini-review, sane meta counts), but the agent quoted the OLD instruction ("write `arch-review/findings/.meta.json` … merge your entry in") and wrote a shared `.meta.json` — **this session's agent registry is the 9.3.0 snapshot; new definitions apply on next session start**, exactly matching the CLI's restart notice and the E011 hypothesis.

**Findings:**
- `claude plugin update` requires the `plugin@marketplace` qualified form for marketplace-installed plugins (bare name → "not found at user scope").
- Agent definitions are snapshotted into the session registry at startup; cache updates mid-session change disk only. In-session dispatch remains fully functional on the old snapshot.
- The 10.0.0 definitions in cache are byte-correct (frontmatter, per-agent meta, lockdowns) — next session's registry loads them with nothing further to do.

**Status:** COMPLETE. A10 closed (C15): cache forced to release versions and verified on disk; smoke mechanics green; live-registry pickup is restart-gated platform behavior, now demonstrated. First arch-review run in a fresh session exercises the new contract end-to-end.
**Duration:** ~10 minutes

---

### Entry 012 — Regenerate 5 tool lockfiles for patched CVE versions (Plan item 4.2) [plugin] [config] [ci] [decision]

**Date:** 2026-07-12
**Environment:** Linux VM, main at `e9ce9f1` (10.1.0 pushed, item 4.1 complete), Python 3.12.3 system / 3.11.14 + 3.14.0 via uv, uv 0.9.6

**Objective:** Regenerate the 5 pip lockfiles (`visual-explainer` requirements-lock.txt + requirements-dev-lock.txt, `feedback-docx-generator` requirements-lock.txt, `bpmn2drawio` requirements-lock.txt + requirements-dev-lock.txt) to pull in patched versions (pillow 12.2.0, cryptography ≥48.0.1, urllib3 2.7.0, lxml 6.1.0, pyasn1 0.6.3, black 26.3.1, idna 3.15, python-dotenv 1.2.2, requests 2.33.0, pytest 9.0.3, Pygments 2.20.0) that clear the 38 open Dependabot pip alerts on this repo. This closes out GitHub remediation plan item 4.2 (IMPLEMENTATION_PLAN.md Phase 4).

**Hypothesis:** A fresh `pip-compile`/`uv pip compile` run per tool (no pyproject.toml floor changes needed except where a target version fails to resolve under an existing floor) will naturally pick up the patched versions since PyPI's current latest already exceeds all listed targets. Expect zero-to-minimal pyproject.toml edits. Success = pip-audit clean in each tool's locked venv, coverage floors hold (90/65/95), root `pytest tests/` exit 0, ruff==0.14.10 check+format clean. Risk flagged by the plan: lxml 6.1 (bpmn2drawio DI layout) and pillow 12.2 (visual-explainer) are the most likely to break a coverage-gated suite — escalate to opus if either breaks non-trivially.

**Rollback Plan:** All work happens on a new branch `fix/dependency-cves-2026-07`, never on `main`. Every file touched (lockfiles, pyproject.toml where floors rise) is git-tracked; `git checkout main -- <file>` or `git branch -D fix/dependency-cves-2026-07` fully reverts with zero data loss. Throwaway venvs live under each tool's `.venv-lock`/`.venv-test` (gitignored via existing `.venv` pattern), deleted after verification — no persistent state.

**Actions & Results:**

1. Branch `fix/dependency-cves-2026-07` created off `main` at `e9ce9f1`.
2. Built a throwaway `pip-tools` compiler venv (Python 3.14, matching the existing lockfile header convention) via `uv venv --python 3.14` + `uv pip install pip-tools`. Ran `pip-compile --upgrade` per tool/extra against each unmodified `pyproject.toml`:
   - `visual-explainer`: `requirements-lock.txt` + `requirements-dev-lock.txt` (`--extra=dev`)
   - `feedback-docx-generator`: `requirements-lock.txt` only (no dev-lock — matches the pre-existing convention noted in `docs/archive/LEARNINGS-v5.md`)
   - `bpmn2drawio`: `requirements-lock.txt` + `requirements-dev-lock.txt` (`--extra=dev`)
3. **Result: zero `pyproject.toml` floor changes needed.** A clean `--upgrade` compile against the existing (already-permissive `>=`) floors naturally resolved every target above its plan-specified patched version: pillow 12.3.0 (≥12.2.0), cryptography 49.0.0 (≥48.0.1), urllib3 2.7.0 (=2.7.0), lxml 6.1.1 (≥6.1.0, both feedback-docx-generator and bpmn2drawio), pyasn1 0.6.4 (≥0.6.3), black 26.5.1 (≥26.3.1), idna 3.18 (≥3.15), python-dotenv 1.2.2 (=1.2.2), requests 2.34.2 (≥2.33.0), pytest 9.1.1 (≥9.0.3), Pygments 2.20.0 (=2.20.0). `git diff --stat` confirms only the 5 lockfiles changed (100 insertions / 93 deletions across them); `pyproject.toml` ×3 untouched. Side effect noted, not a problem: both dev-locks now pin `mypy` explicitly (2.2.0) where the prior lock was missing it despite `pyproject.toml` declaring `mypy>=1.8.0` in `dev` extras — a pre-existing lock incompleteness, now corrected by the clean recompile.
4. Verification, per tool, in a Python 3.11.14 venv (matches CI's `python-version: '3.11'` matrix) — two venvs per tool: a CI-mirror venv (`pip install -e ".[dev]"` / `".[dev,all]"`, exact test.yml install commands) for pytest+coverage, and a locked venv (`pip install -r requirements-*-lock.txt` + `-e .`) for pip-audit against the actual pinned/Dependabot-visible versions:
   - **bpmn2drawio** (lxml 6.1.1, the plan's flagged DI-layout risk): 585 passed, coverage 92.32% (floor 90%) — **no regression from the lxml bump**. pip-audit: `No known vulnerabilities found` (only the expected `bpmn2drawio` local-package skip).
   - **visual-explainer** (pillow 12.3.0, the plan's other flagged risk): 607 passed, 2 skipped, coverage 67.03% (floor 65%). pip-audit: `No known vulnerabilities found` (local-package skip only).
   - **feedback-docx-generator**: 69 passed, coverage 96.95% (floor 95%). pip-audit: `No known vulnerabilities found` (local-package skip only).
   - Combined pip-audit (all 3 tools installed together in one venv, mirroring CI's `dependency-audit` job exactly): `No known vulnerabilities found`, same 3 expected local-package skips, no cross-tool conflicts.
5. Root `pytest tests/` in a fresh venv with `pytest jsonschema pyyaml` (test.yml's root job deps): 67/67 passed, exit 0 — matches the historical baseline unchanged.
6. `ruff==0.14.10 check plugins/*/tools/*/src/ tests/ --output-format=github` → exit 0, 0 violations. `ruff==0.14.10 format --check` → exit 0, "49 files already formatted."
7. Neither `plugin.json`/`marketplace.json` versions, the root `ruff==0.14.10` pin (`validate.yml:209`), nor the `@anthropic-ai/claude-code@2.1.204` pin (`validate.yml:263`) were touched — confirmed via `git status --porcelain`: only the 5 lockfiles + this notebook entry are modified.

**Findings:**
- The plan's two flagged regression risks (lxml 6.1 DI layout in bpmn2drawio, pillow 12.2 in visual-explainer) did **not** manifest — both coverage-gated suites pass clean with margin above their floors. No escalation needed.
- `pip-compile`'s dependency resolution against unmodified `>=` floors was sufficient for all 11 target packages; none required a floor bump. This confirms the floors were already loose enough — the 38 alerts were purely a "lockfile never regenerated" staleness problem, not a floor-too-low problem.
- CI (`test.yml`) never actually installs from these lockfiles (it always runs `pip install -e ".[dev]"` style, unpinned) — the lockfiles exist purely so GitHub's Dependabot dependency-graph scan (which parses pinned `==` requirement files) has an accurate, patched manifest to alert against. This explains why regenerating them is the correct/sufficient fix for the 38 alerts without touching `test.yml`.

**Status:** COMPLETE. All Phase 4.2 acceptance criteria met: pip-audit clean ×3 tools (individually and combined), coverage floors held (92.32%/67.03%/96.95% vs 90/65/95 floors), root pytest 67/67, ruff 0.14.10 check+format clean. Committed on `fix/dependency-cves-2026-07`; PR opening + dependabot.yml + cross-OS CI verification deferred to plan item 4.3 (not in this item's scope).
**Duration:** ~35 minutes

---

### Entry 013 — Add dependabot.yml, open PR, verify CI both OSes (Plan item 4.3) [plugin] [config] [ci]

**Date:** 2026-07-12
**Environment:** Linux VM, branch `fix/dependency-cves-2026-07` at `5b6d0e3` (item 4.2 complete: 5 lockfiles regenerated), Claude Code CLI, gh CLI authenticated as davistroy

**Objective:** Close out GitHub remediation plan item 4.3 — create `.github/dependabot.yml` (the repo has never had one, which is why the 38 pip alerts closed in 4.2 accumulated with zero automated PRs), push it to the same `fix/dependency-cves-2026-07` branch, open the PR bundling both 4.2 and 4.3, and verify `validate.yml` + `test.yml` pass on both ubuntu and windows before merging.

**Hypothesis:** Four `updates` entries — `pip` at each of the 3 tool directories (`plugins/bpmn-plugin/tools/bpmn2drawio`, `plugins/personal-plugin/tools/visual-explainer`, `plugins/personal-plugin/tools/feedback-docx-generator`) plus `github-actions` at `/` — with weekly schedules and a `groups:` block per entry grouping minor/patch bumps, will parse cleanly and require no CI changes since dependabot.yml is config-only (not exercised by any workflow step). Modeled on the existing `retire` repo's `.github/dependabot.yml` (schedule day/time/timezone, commit-message prefix, labels) with grouping added, since 4.3 explicitly requires grouping (unlike retire's item 1.2, which didn't). Success = all `validate.yml` + `test.yml` jobs green on both OSes, PR mergeable, and after merge `gh api 'repos/davistroy/claude-marketplace/dependabot/alerts?state=open&severity=high' --paginate --jq length` returns 0.

**Rollback Plan:** Single new file (`.github/dependabot.yml`) on a feature branch never touched on `main`. `git checkout main -- .github/dependabot.yml` (i.e., delete it) or `git branch -D fix/dependency-cves-2026-07` fully reverts pre-merge. Post-merge, `git revert <merge-sha>` removes it cleanly since it has zero other file dependents.

**Actions & Results:**

1. Verified branch state: `fix/dependency-cves-2026-07` up to date with origin at `5b6d0e3`, working tree clean, no dependabot.yml present (`cat .github/dependabot.yml` empty), confirming the plan's premise.
2. Confirmed the 3 tool directories via `pyproject.toml` presence and cross-checked against `test.yml`'s per-tool job `working-directory` values — all 3 match exactly.
3. Wrote `.github/dependabot.yml`: pip ×3 tool dirs + github-actions at `/`, weekly (Monday 06:00 America/New_York, matching `retire`'s convention), each with a `groups: <name>-minor-patch: update-types: [minor, patch]` block, `commit-message.prefix` per ecosystem, `labels: [dependencies]`.
4. Validated: `python3 -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"` — parses clean, 4 `updates` entries confirmed with correct ecosystem/directory/group-name values.
5. Committed as `2cb2e81` (dependabot.yml + this entry's initial text, explicit-path staging), pushed, opened **PR #99** ("fix(security): regenerate 5 lockfiles for patched CVEs + add dependabot.yml") bundling 4.2's `5b6d0e3` + this item.
6. First CI run: 14 of 15 checks passed — including GitHub's own `.github/dependabot.yml` config check (pass, 1s: config parses server-side) and `Dependency Security Audit` (pip-audit) — but **Lint Markdown failed**: MD012 at LAB_NOTEBOOK.md:709/710. Root cause: this entry's insertion left a double-blank EOF trailer, and markdownlint counts the implicit line after the final newline as part of the blank-line run, so `content\n\n\n` reads as 2-then-3 consecutive blanks. Local repro confirmed (`npx markdownlint-cli LAB_NOTEBOOK.md` → same 2 errors); fixed by trimming to a single trailing newline; verified with CI's exact invocation (`markdownlint '**/*.md' --ignore node_modules --ignore .git --ignore output --ignore 'tests/fixtures/**'` → exit 0). Committed as `ebf22ad`, pushed.
7. Second CI run (head `ebf22ad`): **ALL 15 checks pass, both OSes** — Run Tests (ubuntu 9s / windows 38s), BPMN2DrawIO (25s / 58s), Visual Explainer (59s / 1m49s), Feedback DOCX Generator (18s / 57s), Dependency Security Audit 35s, Lint Markdown 14s, Python Lint & Format, Validate Plugins ×2, Schema Validation, GitGuardian, dependabot.yml config check. Runs: 29204197207 (validate.yml) + 29204197213 (test.yml).

**Findings:**
- Dependabot config is pure GitHub-platform metadata — no workflow step reads or is affected by it, so CI risk from this change is effectively zero; the only real verification available pre-merge is YAML validity + directory-path correctness. GitHub additionally surfaces a per-PR `.github/dependabot.yml` status check that validates the config server-side — it passed on the first push, satisfying 4.3's "config parses, no error banner" criterion ahead of merge.
- `retire`'s `.github/dependabot.yml` (item 1.2/1.3, same author/plan) established the schedule/commit-message/labels convention this entry reuses; the only addition here is `groups:`, required because 4.3 (unlike 1.2) explicitly calls grouping out as necessary to avoid PR pileup against strict required checks (per the parallel open-brain item 6.6 rationale).
- markdownlint MD012 gotcha: a file ending in one explicit blank line (`\n\n`) is flagged as 2 consecutive blanks because the linter counts the virtual line after EOF. Always end notebook appends with exactly `content\n`.

**Status:** COMPLETE. PR #99 squash-merged as `c538e14` at 2026-07-12T18:43:06Z (repo convention, Entry 010/PR #96 precedent; branch deleted, local main fast-forwarded e9ce9f1→c538e14). Phase 4 DoD: open high-severity alerts 17→0 by 18:45:52Z (~3 min rescan lag), and in fact ALL 38 open alerts (17H/16M/5L) closed — better than the plan's "5 low may lag" expectation. Dependabot proven live within minutes of merge: opened PRs #100–#102 (github-actions bumps) and #103 (pip, correctly using the `visual-explainer-minor-patch` group). Feature PRs #97 (xquik plugin) and #98 (bpmn2drawio DI layout) remain open and untouched — out of scope per plan item 4.3 notes.
**Duration:** ~45 minutes (including two CI rounds and the MD012 fix)

---

### Entry 014 — Ship personal-plugin 10.2.0: fleet-health, new-project, archive-project skills + sre-operator agent + gate stdin fix [plugin] [skill] [config] [ci]

**Date:** 2026-07-12
**Environment:** Linux VM, Claude Code CLI 2.1.207, main at `c12c0ab` (Entry 013/PR #99 merged), personal-plugin v10.1.0 pre-release

**Objective:** Ship personal-plugin 10.2.0 — new `fleet-health`, `new-project`, `archive-project` skills; new `sre-operator` agent for the 5-machine homelab fleet; a fix to the lab-notebook `PreToolUse` hook (stdin parsing + exit-code propagation, since the prior invocation matched `$CLAUDE_TOOL_INPUT` as a raw env var against the whole JSON payload rather than parsing `tool_input.command` from stdin); two new reference templates (`project-claude-md.md`, `brief.md`) consumed by `new-project`; and a CHANGELOG backfill for the 10.1.0 entries that shipped in Entry 013's predecessor work but were never given full changelog treatment.

**Hypothesis:** All payload files are additive (3 new skill dirs, 1 new agent, 2 new reference templates) except the hooks.json fix, which changes hook *behavior* (parses `tool_input.command` via `jq` when available, falls back to raw stdin, and propagates the gate script's exit code instead of always returning 0) — this is a genuine bug fix, not a cosmetic change, since the old form could never actually block a commit (it grepped the hook's own env-var name against JSON that doesn't contain it in the expected shape, and even on a match, `|| exit 0` swallowed the gate's exit code). Expect: `claude plugin validate --strict` and `pytest tests/` both pass unmodified (no test currently exercises hooks.json semantics); CI's `validate.yml` + `test.yml` pass on both OSes; squash-merge; plugin cache updates to 10.2.0 via `claude plugin update personal-plugin@troys-plugins`; installed cache inventory shows exactly 3 new skill dirs + `agents/sre-operator.md`.

**Rollback Plan:** All work happens on branch `release/personal-plugin-10.2.0`, never on `main`. Every file is git-tracked; `git checkout main -- <path>` or `git branch -D release/personal-plugin-10.2.0` fully reverts pre-merge with zero data loss. The installed plugin cache is rebuildable API-managed state (D19) — worst case `claude plugin update personal-plugin@troys-plugins` re-syncs from `origin/main`, or `rm -rf ~/.claude/plugins/cache/troys-plugins/personal-plugin` + reinstall regenerates it.

**Actions & Results:**

1. Sanity: `git status --porcelain` showed exactly the expected payload (2 modified + 6 new paths, nothing unexpected); `git pull --ff-only` already up to date at `c12c0ab`.
2. Version bump per `/bump-version` procedure: personal-plugin 10.1.0→10.2.0 in `plugins/personal-plugin/.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` (lockstep, for the CI version-sync gate); `## [10.2.0] - 2026-07-12` sections with real Added/Fixed entries written into both root `CHANGELOG.md` and `plugins/personal-plugin/CHANGELOG.md`.
3. Pre-flight gates: `claude plugin validate --strict ./plugins/personal-plugin` exit 0; `pytest tests/` 67/67 pass (uv, Python 3.14). Manual review pass on all 6 new files: no hardcoded secrets (the two `sk-ant`/`AKIA` grep hits are documentation of the secrets-guard patterns, not keys); all bodies within budget (fleet-health 164 / new-project 228 / archive-project 226 / sre-operator 80 lines); sre-operator carries report-before-restart, stateful-container escalation, and davistroy-auth-untouchable guardrails.
4. Ship (release-plugin → ship flow; clean-repo phase deliberately SKIPPED — the `--skip-cleanup` equivalent — so no payload file could be relocated or deleted pre-commit): branch `release/personal-plugin-10.2.0`, commit `4e7b2c5` (12 files, +817/−3), pushed, opened **PR #105**.
5. First CI round: 17/18 pass — **Lint Markdown failed** on MD012 at `fleet-health/SKILL.md:165`. Exactly Entry 013's EOF gotcha again (file ended `\n\n`; markdownlint counts the virtual post-EOF line, so one explicit trailing blank reads as two). Trimmed to a single trailing newline, verified with CI's exact invocation (`npx markdownlint-cli '**/*.md' --ignore node_modules --ignore .git --ignore output --ignore 'tests/fixtures/**'` → exit 0), committed `216bc07`, pushed.
6. Second CI round (head `216bc07`): **ALL 18 checks pass, both OSes** — Run Tests (ubuntu/windows), BPMN2DrawIO ×2, Visual Explainer ×2, Feedback DOCX ×2, Dependency Security Audit, Lint Markdown, Python Lint & Format, Validate Plugins + Validate Plugins (official CLI), Schema Validation, CodeQL + Analyze ×2, GitGuardian. Runs: 29212013101 (validate.yml) + 29212013043 (test.yml).
7. Squash-merged as **`9c12188`**; remote + local branch deleted, remote-tracking ref pruned; local main fast-forwarded c12c0ab→9c12188, working tree clean.
8. Installed-plugin update: `claude plugin marketplace update troys-plugins` + `claude plugin update personal-plugin@troys-plugins` (Entry 011's qualified-name mechanism, same as the 10.0.0→10.1.0 update earlier today) — results recorded in Status below.

**Findings:**
- The MD012 EOF gotcha (Entry 013 finding) recurred on the first new file authored since — worth a pre-push `markdownlint` habit or pre-commit hook rather than per-incident fixes; the CI catch-and-fix cost one full round.
- The hooks.json gate fix is behavioral, not cosmetic: the old invocation grepped the expansion of `$CLAUDE_TOOL_INPUT` (an unset env var → empty string) so the gate script never ran, and `|| exit 0` would have swallowed any non-zero exit anyway. The new form parses `tool_input.command` from the PreToolUse stdin JSON contract and propagates the gate's exit code — the first version of the lab-notebook gate that can actually block a commit.

**Status:** COMPLETE. PR #105 squash-merged as `9c12188`; personal-plugin 10.2.0 live on main with plugin.json == marketplace.json == 10.2.0; installed cache updated 10.1.0→10.2.0 and inventory verified (3 new skill dirs + agents/sre-operator.md present in `~/.claude/plugins/cache/troys-plugins/personal-plugin/10.2.0/`). New skill/agent definitions are restart-gated (Entry 011 behavior) — first fresh session loads them; fresh-session skill-list check noted as the trailing verification.
**Duration:** ~40 minutes (including one CI fix round)

---

--- New session: 2026-07-16 — /prime health assessment, then author a new `clear-prep` skill for context-clear handoffs ---

### Entry 015 — Add `clear-prep` skill (context-clear handoff) + refresh stale Current Baseline [plugin] [skill] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, Claude Code CLI, main at `c9d3dd4` (clean, synced with origin/main 0/0), personal-plugin v10.2.0, marketplace 3.3.0

**Objective:** (1) Run `/prime` for a full situational assessment. (2) Author a new skill `clear-prep` in personal-plugin that, on request, flushes the current session's state into all durable documents (LAB_NOTEBOOK living sections + in-flight entry, memory, CLAUDE.md, CHANGELOG) and then emits a single copy-paste "resume prompt" the user runs in a fresh session after `/clear`, so a zero-context Claude continues seamlessly. (3) Remediate the highest prime finding: this notebook's "Current Baseline" living section was 4 versions stale (read 3.2.0/9.3.0/4.1.0/1.1.0; actual 3.3.0/10.2.0/4.2.0/1.2.0) — Entry 014 shipped 10.2.0 but never refreshed the baseline, violating Rule 7.

**Hypothesis:** `clear-prep` is additive — a single new `skills/clear-prep/SKILL.md` under the required nested structure, no plugin.json/marketplace.json edits needed (skills are auto-discovered from `skills/`, unlike plugins which need marketplace registration). Frontmatter follows house convention: `name` present and == dir name (D2), `effort`, `allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)`, `description` carrying the proactive-trigger text (≤1024 chars, no body "Proactive Triggers" section). Design choice: model-invocation ENABLED (suggestable when the user says "clear context / compact / wrap up") rather than `disable-model-invocation: true` — the skill only writes git-recoverable docs and its whole purpose is triggered by that exact intent; alternatives (disable-model-invocation) rejected because it would hide the skill from the very context where it's most useful, and the skill is designed to report-then-let-user-commit, so no risky auto-action. Success = `claude plugin validate --strict ./plugins/personal-plugin` exit 0, `pytest tests/` unchanged, SKILL.md body <500 lines, no hardcoded secrets. NOT shipping (no version bump / PR / commit) this turn — user asked to "create the skill and put it into personal-plugin," not to release; shipping is a separate `/release-plugin` step, flagged to the user.

**Rollback Plan:** Purely additive, all git-tracked. `git checkout -- LAB_NOTEBOOK.md` reverts the baseline refresh + this entry; `rm -rf plugins/personal-plugin/skills/clear-prep` removes the new skill. Zero data loss; nothing outside the working tree is touched (no commit, no cache update, no external state).

**Actions & Results:**

1. `/prime` run: Phase 0 read this notebook in full; git health (`git fetch`, 0/0 divergence, clean, 9 commits/30d) + current versions pulled inline; identity/quality/risk gathered via one Explore agent (`context: fork`). Report delivered in-conversation. Top finding: this notebook's Current Baseline was 4 versions stale (Rule 7 violation from Entry 014). Secondary low-risk findings: dead `research_orchestrator` entry in `ruff.toml` isort first-party list (tool removed per D5); slide-gen `plugin.json` homepage points at wrong repo (`slide-generator`); tracked root cruft (`.DS_Store`, `gap-analysis-2026-04-30.md`, `GITHUB_ERRORS.md`); 52-byte placeholder `uv.lock`.
2. Current Baseline refreshed to 3.3.0 / 10.2.0 / 4.2.0 / 1.2.0, last commit `c9d3dd4`, git verified synced 2026-07-16 (the primary remediation).
3. Created `plugins/personal-plugin/skills/clear-prep/SKILL.md` (136 lines, nested-dir structure per D1). Frontmatter: `name: clear-prep` (== dir, D2), `effort: medium`, `allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)`, `description` 499 chars (≤1024 budget) carrying proactive triggers — no body "Proactive Triggers" section. Body: Phase 1 assess session state (git delta + conversation) → Phase 2 update durable docs (LAB_NOTEBOOK in-flight-entry flush + living sections, memory, CLAUDE.md, CHANGELOG; never commits) → Phase 3 emit copy-paste resume prompt for the post-`/clear` session. Model-invocation left ENABLED (design rationale in Hypothesis).
4. Validation: `claude plugin validate --strict ./plugins/personal-plugin` → **✔ Validation passed**. `markdownlint-cli` on the new file → clean (MD012 EOF gotcha from E013/E014 pre-empted: file ends in exactly one `\n`). `pytest` not installed in this VM's Python/uv env — noted, not blocking: the root suite exercises tool logic (bump_version/qa_workflow/validate_plugin), not skill-markdown discovery, so an additive skill file cannot regress it; the authoritative structural gate (`claude plugin validate --strict`) passed.

**Findings:**
- Skills need no marketplace.json/plugin.json registration — auto-discovered from `skills/`. Confirmed: `claude plugin validate --strict` passed with zero manifest edits. (Contrast: adding a *plugin* requires marketplace.json registration.)
- The restart-gating behavior (Entry 011): the new `clear-prep` definition won't appear in the live session's skill list until the next fresh session loads it — expected, not a defect.

**What Worked:** Following the mandatory-logging discipline in order (Hypothesis+Rollback → act → log) made the additive change trivially safe; the drafted-to-scratchpad-then-copy approach let the SKILL.md be authored while the Explore agent ran in parallel, with zero repo mutation until the notebook entry existed.

**Status:** COMPLETE. `clear-prep` skill live in the working tree, structurally valid; Current Baseline corrected. NOT shipped in E015 — release handled in E016 (user followed up with "ship it (bump + PR)").
**Duration:** ~10 minutes

---

### Entry 016 — Ship personal-plugin 10.3.0: clear-prep skill [plugin] [skill] [ci] [build]

**Date:** 2026-07-16
**Environment:** Linux VM, Claude Code CLI, main at `c9d3dd4`, personal-plugin v10.2.0 pre-release, gh authenticated as davistroy

**Objective:** Release the `clear-prep` skill authored in E015 as personal-plugin **10.3.0** — version bump (plugin.json + marketplace.json lockstep for the CI version-sync gate), CHANGELOG entries in both root and plugin changelogs, PR bundling the skill + E015/E016 notebook work, CI green on both OSes, squash-merge per repo convention, then update the installed cache.

**Hypothesis:** Minor bump (new backward-compatible skill, no breaking change): `10.2.0→10.3.0` in `plugins/personal-plugin/.claude-plugin/plugin.json` and the personal-plugin entry in `.claude-plugin/marketplace.json`. `marketplace_version` stays 3.3.0 (CLAUDE.md: bumped only for schema/shared-tooling/repo-wide changes, not single-plugin updates). CHANGELOG: `## [personal-plugin v10.3.0] - 2026-07-16` under root `[Unreleased]`, `## [10.3.0] - 2026-07-16` in plugin changelog, each with one Added line for clear-prep. Expect `claude plugin validate --strict` exit 0 and all `validate.yml` + `test.yml` checks green on ubuntu + windows. Primary predicted risk: markdownlint MD012 on the notebook append (bit E013 and E014) — pre-empted by ending every appended file in exactly one `\n` and running `markdownlint-cli` locally before push.

**Rollback Plan:** All work on branch `release/personal-plugin-10.3.0`, never on `main`. Every file git-tracked; `git checkout main -- <path>` or `git branch -D release/personal-plugin-10.3.0` fully reverts pre-merge. Post-merge, `git revert <merge-sha>` cleanly undoes the release (additive skill + version/changelog edits, no external dependents). Installed cache is rebuildable API-managed state (D19): `claude plugin update personal-plugin@troys-plugins` re-syncs from origin.

**Actions & Results:**

1. Branch `release/personal-plugin-10.3.0` created off `main` at `c9d3dd4` (carries the uncommitted E015 skill + notebook edits).
2. Version bump: `10.2.0→10.3.0` in `plugins/personal-plugin/.claude-plugin/plugin.json` and the personal-plugin entry in `.claude-plugin/marketplace.json`; `marketplace_version` left at 3.3.0. Sync verified (both read 10.3.0; bpmn 4.2.0 / slide-gen 1.2.0 untouched).
3. CHANGELOG: `## [personal-plugin v10.3.0] - 2026-07-16` added under root `[Unreleased]`; `## [10.3.0] - 2026-07-16` added atop `plugins/personal-plugin/CHANGELOG.md`; one Added line each for `clear-prep`.
4. Pre-flight gates (pre-push): `claude plugin validate --strict ./plugins/personal-plugin` → **✔ Validation passed**. `markdownlint-cli` on all 4 changed `.md` files caught **MD049** (this entry's placeholder used `_underscore_` emphasis; house style is asterisk) — fixed by replacing the placeholder with these logged actions. No MD012 (files end in a single `\n`).
5. Commit + push + PR: recorded in Status below.

**Status:** IN PROGRESS — PR opened, CI pending. Entry closed with the squash-merge SHA in a follow-up `docs:` commit on main (Entry 014 / `c9d3dd4` pattern), since the merge SHA is unknown until after merge.
