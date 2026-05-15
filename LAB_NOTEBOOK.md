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

Status values: ACTIVE · SUPERSEDED (by D#) · REVERSED (in E#)

## Action Items

Track follow-ups that emerge from experiments. Move to Completed when done.

### Open

| # | Action | Created | Source Entry | Priority |
|---|--------|---------|-------------|----------|
| A1 | Reinstall plugin to sync spark-recon changes to Claude Code environment | 2026-04-30 | E001 | High — loaded skill is stale vs repo |
| A7 | Reinstall plugin to sync all gap-analysis changes to Claude Code environment | 2026-04-30 | E003 | High — loaded plugin cache is stale vs repo |
| A8 | Bump personal-plugin version to 9.0.0 (major: new template sections, ultra-plan rewrite) | 2026-04-30 | E003 | Medium — version bump needed before merge |

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

The marketplace is at **v2.0.0** (marketplace), **personal-plugin v8.0.0**, **bpmn-plugin v4.0.0**. The repo is clean, synced with origin/main. The v8.0.0 modernization plan (7 phases, 28 work items) completed successfully on 2026-04-21 — see `IMPLEMENTATION_PLAN.md` for full details and `docs/archive/` for prior plan versions (v4, v5).

One known issue: the installed plugin cache (`~/.claude/plugins/cache/troys-plugins/personal-plugin/8.0.0/`) has a stale `spark-recon/SKILL.md` that doesn't match the repo version. The repo version has dynamic state reading from `SPARK_BASELINE.md` and generalized model family matching; the cached version has hardcoded `Qwen/Qwen3.5-35B-A3B` references. `jetson-recon` is in sync. Reinstalling the plugin (`/plugin install personal-plugin@troys-plugins`) would resolve this.

### Planning System

The project has a mature planning workflow: `/ultra-plan` for deep investigation, `/create-plan` for requirements-driven planning, `/plan-improvements` for codebase analysis, and `/implement-plan` for automated execution via subagent orchestration. All share a unified `references/plan-template.md` template. The template was refined today (2026-04-30) with 7 improvements — see Entry 001.

### Key Learnings (from memory files and CLAUDE.md)

Plugin discovery is fragile and fails silently. The five verified operational rules (CLAUDE.md) are non-negotiable: nested skill dirs, `name` in skill frontmatter, no `name` in command frontmatter, no `tools` in plugin.json, no `hooks` in plugin.json. The hooks.json format migration from array to record format (2026-03-31) was another silent failure. These are documented in both CLAUDE.md and the project memory files.

## Current Baseline

- **Marketplace version:** 2.0.0
- **personal-plugin version:** 8.0.0 (25 commands, 22 skills, 9 agents, hooks system)
- **bpmn-plugin version:** 4.0.0 (2 skills, bpmn2drawio Python tool)
- **Git:** clean, main branch, synced with origin/main
- **Last commit:** `c8e9a15` (2026-04-21) — fix: remove research-orchestrator CI jobs
- **Plugin cache status:** jetson-recon in sync; spark-recon stale (needs reinstall)
- **CI/CD:** GitHub Actions (markdownlint); research-orchestrator and help-sync jobs removed in latest commits
- **Platform:** Windows 11, Claude Code CLI

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

*Entries continue below.*
