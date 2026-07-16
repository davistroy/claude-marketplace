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
| D19 | Plugin cache freshness is governed by install-side origin/main tracking, not by manual local reinstall | 2026-07-08 | ACTIVE (corrected E017) | E007 | Manual reinstall (A1/A7 premise) — superseded; cache already tracks GitHub origin automatically. The real risk is the local dev clone lagging origin (second occurrence of D17's root cause). **Correction (E017, item 1.4):** the original wording cited an `autoUpdate: true` setting *in marketplace.json* — verified inaccurate; `.metadata` holds only description/marketplace_version/schema_version. Auto-propagation is Claude Code's install-side default for GitHub-sourced marketplaces, NOT a repo-declared flag. |
| D20 | Agent `model:` fields use tier aliases (haiku/sonnet/opus/inherit), never pinned IDs (ADR-0005, Accepted) | 2026-07-08 | ACTIVE | E009/E010 | Pinned + periodic review — rejected, drifted twice undetected (9.1.0→9.3.0) |
| D21 | Skills-first authoring: new functionality ships as skills; commands/ frozen legacy; new-command deprecated, patterns ported to /new-skill --pattern (ADR-0006, Accepted) | 2026-07-08 | ACTIVE | E009/E010 | Mass-migrate 24 commands — rejected (churn, zero functional gain); status quo — rejected (diverges from official direction) |
| D22 | Distribution safety = branch-protection-only (required CI checks + PR-required 0-approvals + enforce_admins=false), NOT a stable/tagged release channel (ADR-0007, Accepted) | 2026-07-16 | ACTIVE | E017 | Stable/tagged channel + consumer pinning — rejected as disproportionate for a solo marketplace; required approving review — rejected (bus factor 1 deadlock); status quo — rejected (the Critical PLAT-001) |
| D23 | slide-gen = external-dependency plugin (the `sg` engine stays in the private `davistroy/slide-generator` repo) with a fail-fast preflight, NOT vendored in-tree (ADR-0008, Accepted) | 2026-07-16 | ACTIVE | E022 | Vendor engine per ADR-0002 — rejected (large cross-repo import + sync burden); deprecate slide-gen — rejected (actively used by owner). Consequence: owner-only until slide-generator is public |
| D24 | mypy enforced as a count-RATCHET (baselines bpmn 57 / visual-explainer 101, fail on net-new errors) rather than zeroing the 152 pre-existing errors | 2026-07-16 | ACTIVE | E020 | Full 152-error cleanup — deferred (disproportionate, risks behavior changes); leave advisory (continue-on-error) — rejected (the SE-04/QA-05/PLAT-006 finding). Tighten baseline toward 0 over time |
| D25 | Dependabot GitHub-Actions version bumps are MERGED as-is (they update both the pinned SHA and the `# vN` comment, preserving Phase-4 SHA-pinning), NOT closed. Corrects Action Item A1's premise. | 2026-07-16 | ACTIVE | E026 | Close + let dependabot "re-propose SHA bumps" (A1's plan) — rejected: dependabot's bump ALREADY is the SHA bump; closing just loses the update. Pin to floating `# vN` tags — rejected (defeats supply-chain pinning) |
| D26 | Decompose visual-explainer `cli.py` into 6 modules (terminal / cli_args / io_utils / reporting / pipeline + thin cli entry); cross-module *patchable* symbols referenced module-qualified so `unittest.mock.patch` intercepts at one point; test patch strings repointed to defining module | 2026-07-16 | ACTIVE | E027 | Fewer/larger modules — rejected (reporting+pipeline still 780/490 LOC, but further splitting fragments cohesion); keep monolith + only add tests — rejected (37%→85% needs testable units, not one 1,814-line file); `from .terminal import x` in consumers — rejected (binds a copy, defeats single-point patching) |

Status values: ACTIVE · SUPERSEDED (by D#) · REVERSED (in E#)

## Action Items

Track follow-ups that emerge from experiments. Move to Completed when done.

### Open

| # | Action | Created | Source Entry |
|---|--------|---------|-------------|
| A2 | **Deferred remediation items → now tracked as GitHub issues #125–#131 (P1–P7).** #125 P1 decompose `cli.py`; #126 P2 grow eval corpus; #127 P3 visual-explainer floor→85%; #128 P4 PERF-01 wiring; #129 P5 tighten mypy baselines; #130 P6 PLAT-012 CI matrix; #131 P7 SE-11. **Going forward all tasks/work are managed from the GitHub issues list** (user directive 2026-07-16). Full rationale: `arch-review/reports/ultra-plan-analysis.md` + Entry 024 | 2026-07-16 | post-E025 session |

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
| C18 | Author `clear-prep` skill (context-clear handoff) + refresh 4-version-stale Current Baseline (prime finding); `claude plugin validate --strict` passed | 2026-07-16 | 2026-07-16 | E015 |
| C19 | Ship personal-plugin 10.3.0 (clear-prep) via PR #108 — squash-merged `df33eef`, all 25 checks green both OSes, cache updated 10.2.0→10.3.0; folded a one-line setuptools-CVE (PYSEC-2026-3447) CI hygiene fix to unblock the audit gate | 2026-07-16 | 2026-07-16 | E016 |
| C20 | Execute the 8-phase arch-review remediation (IMPLEMENTATION_PLAN v9, 32 items) via /implement-plan — one branch+PR+merge per phase (PRs #109/#110/#111/#112/#118/#119/#120/#121), all 18 checks green each after 2 Windows fix rounds; merges `8a2988a→039c2cc→c093904→7fe821d→99d0610→9cf8963→e3bf0a4→0e0895c`. Deferred: SE-11, PLAT-012, PERF-01-wiring + plan scope-outs | 2026-07-16 | 2026-07-16 | E017–E024 |
| C21 | **Dependabot triage (A1)** — 5 merged (#104 google-genai 2.11 MAJOR verified-safe, #113/#114/#115 SHA-pinned action bumps, #116 bpmn2drawio group), 1 closed with root-cause (#117 broken pydantic/pydantic-core lockfile). main `37868fb→6bf2d84`, all tool lockfiles CVE-clean. Course-corrected A1's plan (see D25) | 2026-07-16 | 2026-07-16 | E026 |

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
- **personal-plugin version:** 11.0.0 (23 commands, 28 skills, 10 named agents in `.claude/agents/`, hooks system) — arch-review hardening release (E017–E025); MAJOR (removed visual-explainer `--concurrency`, scoped `allowed-tools`, 4 fleet skills user-invoke-only)
- **bpmn-plugin version:** 4.2.0 (2 skills, bpmn2drawio Python tool)
- **slide-gen version:** 1.2.0 (9 skills, 7-step presentation pipeline)
- **Git:** clean, main branch, synced with `origin/main` (2026-07-16)
- **Last commit:** `6bf2d84` — deps: google-genai 1.75→2.11 MAJOR (PR #104), atop the dependabot triage merges #113/#114/#115/#116 (E026/C21). 11.0.0 release is `fbb1437` (PR #123); remediation Entries 017–025, see C20. Dependency queue cleared; all 3 tool lockfiles CVE-clean. Next: deferred issues #125–#131 (backlog burndown, A2)
- **Dependencies:** GitHub Actions SHA-pinned at v6/v7 (checkout/setup-python/setup-node); visual-explainer on google-genai **2.11.0** (verified API-compatible, E026); pydantic 2.13.4 / pydantic-core 2.46.4 (lockstep — do not bump independently, D25/E026)
- **Arch-review remediation (2026-07-16):** 8-phase plan (32 items) COMPLETE. Branch protection now ENFORCED on `main` (14 required checks, PR-required, `enforce_admins=false`); CI gates hardened (per-tool tests linted, mypy count-ratchet, schema-data validation, SHA-pinned actions, pip-audit scoped, xdist); tool code hardened (XXE, SSRF, `.env` 0600, atomic writes); injection surface reduced (Bash scoped in 23 files, 4 fleet skills user-invoke-only); slide-gen honest (ADR-0008 external-dep + preflight); egress/supply-chain policy in SECURITY.md; cruft removed. **No plugin version bumps** — these were hardening changes, not feature releases (personal-plugin stays 10.3.0 / bpmn 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0); autoUpdate propagates content regardless of version. Deferred (documented): SE-11, PLAT-012, PERF-01 wiring, cli.py decomposition, full eval corpus, visual-explainer floor→85%.
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
5. Commit `04c4ddc` (6 files, explicit-path staged), pushed, opened **PR #108**.
6. First CI run: **24 of 25 checks pass on both OSes** — all Validate/Schema/Lint/CodeQL/test-matrix green. **One failure: `Dependency Security Audit` (pip-audit).** Root cause is NOT this PR: the audit runs bare `pip-audit` over the whole CI env, which includes `setuptools 79.0.1` (whatever `actions/setup-python@v5` ships for 3.11 — the step upgrades `pip` but not `setuptools`), and a newly-disclosed advisory **PYSEC-2026-3447** (fix: setuptools 83.0.0) now flags it. This is a pre-existing condition on `main` (nothing here touches setuptools) that surfaced because pip-audit queries the live advisory DB — the same env was green in E013/E014. Fix surface: one CI line (`pip install --upgrade setuptools`) in the audit job's install step.

**Finding:** the `Dependency Security Audit` job audits the *runner environment* (implicit build tools like setuptools included), not just declared tool deps — so it can fail on an unrelated feature PR the moment a new setuptools/pip/wheel CVE lands. Contrast E013's lockfile audit, which only saw declared deps. Mitigation options weighed with the user (scope-isolate per E013 precedent vs fold the one-line CI hygiene fix into this release).

7. **Decision (user):** fold the one-line CI hygiene fix into #108 (over scope-isolation into a separate PR, and over admin-merging past the red gate). Rationale: single workflow-file line, unblocks immediately, keeps `main`'s audit green, and hardens the gate against future stale-build-tool CVEs for every subsequent PR — the isolation concern (E013) applies to *tool dependency* churn, not a one-line runner-hygiene patch. Added `python -m pip install --upgrade setuptools` to the audit job's install step in `.github/workflows/test.yml` (with an explanatory comment). CHANGELOG deliberately untouched — CI-infra hygiene is not a plugin-facing change.
8. CI fix committed `8ee1eae`, pushed to #108. Second run: **ALL 25 checks pass, both OSes** — including `Dependency Security Audit` (31s, now green with patched setuptools). Runs 29507058656 (test.yml) + 29507058648 (validate.yml).
9. Squash-merged as **`df33eef`** ("personal-plugin 10.3.0: clear-prep skill for context-clear handoffs (#108)"); remote branch deleted; local main fast-forwarded c9d3dd4→df33eef, clean.
10. Installed cache: `claude plugin marketplace update troys-plugins` + `claude plugin update personal-plugin@troys-plugins` → updated 10.2.0→10.3.0; verified `~/.claude/plugins/cache/troys-plugins/personal-plugin/10.3.0/skills/clear-prep/SKILL.md` present. New skill is restart-gated (E011) — appears in the live skill list next fresh session.

**Status:** COMPLETE. personal-plugin 10.3.0 live on main (`df33eef`), plugin.json == marketplace.json == 10.3.0, `clear-prep` skill shipped and in the installed cache. CI hardened against stale-build-tool CVEs. Current Baseline refreshed below.
**Duration:** ~35 minutes (including the setuptools CVE detour + one CI re-run)

---

--- New session: 2026-07-16 — /arch-review (9-agent) → /ultra-plan → /implement-plan: executing the 8-phase arch-review remediation, one branch+PR+merge per phase, Sonnet implementer subagents ---

### Entry 017 — Implement-Plan Phase 1: Distribution Governance [ci] [decision] [build]

**Date:** 2026-07-16
**Environment:** Linux VM, Claude Code CLI, main at `29096cc` (plan v9 committed), branch `impl/phase-1-governance`, orchestrator=Opus, implementer subagents=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 1 (the single Critical finding) — enable branch protection on `main` (checks-only, no required review, `enforce_admins=false`) so the CI suite becomes enforced rather than advisory; add a maintainer rollback runbook; add CODEOWNERS + soften SECURITY.md hard SLAs; correct the inaccurate D19 `autoUpdate` documentation (item 1.4). Ship as one PR, merge on green CI.

**Hypothesis:** Enabling branch protection via `gh api PUT` takes effect immediately at the repo level, so this PR (and all subsequent phase PRs) will require the authored-workflow status checks to pass before merge. Required set = the stable authored-workflow job checks (Run Tests ×2 OS, the 3 per-tool test jobs ×2 OS, Validate Plugins ×2, Schema Validation, Lint Markdown, Python Lint & Format, Dependency Security Audit). CodeQL/GitGuardian left advisory-not-required to avoid deadlock on app-managed check contexts (documented in ADR-0007); `enforce_admins=false` is the safety valve. Expect: ADR-0007 (Accepted), `docs/RUNBOOK.md`, `.github/CODEOWNERS`, SECURITY.md SLA softening, D19 correction; all CI green; squash-merge.

**Rollback Plan:** All file work on branch `impl/phase-1-governance` (never main); `git branch -D` reverts pre-merge. Branch protection is API-managed, reversible via `gh api -X DELETE repos/davistroy/claude-marketplace/branches/main/protection`. Every file git-tracked. Post-merge, `git revert <sha>` undoes the docs; protection removed via the DELETE call.

**Actions & Results:**

1. **Item 1.1 (branch protection):** orchestrator ran `gh api PUT .../branches/main/protection` → enabled with 14 required status checks (Run Tests + 3 per-tool test jobs ×2 OS, Validate Plugins ×2, Schema Validation, Lint Markdown, Python Lint & Format, Dependency Security Audit), `required_pull_request_reviews.required_approving_review_count=0` (PR required, no approval — bus factor 1), `enforce_admins=false` (safety valve). CodeQL/GitGuardian left advisory-not-required (app/default-setup contexts). PLAT-001 closed at the infra level. ADR-0007 written by a Sonnet subagent (Accepted).
2. **Item 1.2:** `docs/RUNBOOK.md` (maintainer detect→revert→verify→propagate→user-escape-hatch, ~30 min RTO) + TROUBLESHOOTING.md cross-link (Sonnet subagent).
3. **Item 1.3:** `.github/CODEOWNERS` (`* @davistroy`, ownership-clarity not a review gate) + SECURITY.md SLAs softened to best-effort + RUNBOOK cross-ref (Sonnet subagent).
4. **Item 1.4 (D19 correction):** done by orchestrator — see the D19 row correction note in the Decision Log above.

**Status:** COMPLETE. PR #109 squash-merged as `8a2988a`, all 18 checks green under the newly-enabled branch protection (proving the gate is enforced end-to-end: the protection allowed the merge only after checks passed). Branch protection live on `main` (14 required checks, PR-required 0-approvals, `enforce_admins=false`). The Critical finding PLAT-001 is closed. Local main fast-forwarded 29096cc→8a2988a.
**Duration:** ~25 minutes

---

### Entry 018 — Implement-Plan Phase 2: Tool Security Hardening (Code) [skill] [decision] [debug]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `8a2988a` (branch-protected), branch `impl/phase-2-security`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 2 — close the exploitable-in-code paths: (2.1) harden the bpmn2drawio lxml parser against XXE + cap the `lxml>=4.9.0` floor to `>=5.0,<7`; (2.2) harden visual-explainer's `.env` key write (chmod 600 + warning) and amend ADR-0003 to sanction the local-runtime path (decision D3); (2.3) add an SSRF guard to `concept_analyzer.fetch_url`; (2.4) switch Gemini backoff classification from `str(e)` substring-matching to typed exceptions; (2.5) make checkpoint/JSON writes atomic (temp+`os.replace`, add `schema_version`) and use the full-length cache hash key. Ship as one PR, merge on green CI.

**Hypothesis:** All five are additive/hardening changes to Python tool code with existing test suites and coverage floors (bpmn2drawio 90%, visual-explainer 65%) as the regression guard. Expect: new XXE regression test (parser rejects external SYSTEM entities) and SSRF test (metadata IP blocked) pass; the 585 bpmn2drawio tests + visual-explainer suite stay green at/above floor; `ruff` clean. File-disjoint parallelization: batch1 [2.1 bpmn2drawio, 2.3 concept_analyzer.py, 2.4 image_generator.py] parallel; then [2.2 api_setup.py+ADR-0003, 2.5 checkpoint-writers+concept_analyzer cache-key] — 2.5 sequenced after 2.3 since both touch concept_analyzer.py. Risk: hardened lxml parser could reject legit BPMN using DTDs (low — BPMN rarely does; 585-test suite guards).

**Rollback Plan:** All work on branch `impl/phase-2-security` (never main); `git branch -D` reverts pre-merge. Every file git-tracked; coverage floors + the new security tests guard regressions. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **2.1 (lxml/XXE):** module-level hardened `XMLParser(resolve_entities=False, no_network=True, load_dtd=False, dtd_validation=False, huge_tree=False)` threaded through both `parse`/`fromstring`; `pyproject.toml` floor `lxml>=5.0,<7`; new `test_xxe.py` (3 tests) — **588 passed, 92% coverage**; empirically verified `/etc/hostname` content never leaks (entity unresolved / `BPMNParseError`).
2. **2.3 (SSRF):** `_check_host_is_safe`/`_validate_url_target`/`SSRFError` in `concept_analyzer.py` resolve via `getaddrinfo` and block private/loopback/link-local/reserved/multicast (incl. 169.254.169.254) + non-http(s); `fetch_url_content` disables auto-redirects and re-validates each hop (≤5); new `test_ssrf.py` (23 tests) — **634 passed, 67.9%**.
3. **2.4 (typed backoff):** new `_classify_exception` prefers typed `google.genai.errors` `.code` (429→rate, 5xx→retry) + `httpx.TimeoutException`, string-match fallback retained; 4 new tests — **611 passed, 66%**; `image_generator.py` at 87%.
4. **2.2 (.env + ADR-0003):** `_create_env_file` now `chmod 0600` + explicit plaintext-storage warning (OSError-tolerant); ADR-0003 amended with a "Sanctioned exception: standalone-tool local runtime" section (Status still Accepted); README security note — **634 passed, 68%**.
5. **2.5 (atomic + cache key):** `_atomic_write_text` (temp+`os.replace`) applied to checkpoint/metadata/eval/concepts writers in both `output.py` and the live `cli.py` path; `schema_version` on checkpoints (tolerated-if-absent on load); concept cache key now full SHA-256 (was `[:16]`); 2 new tests incl. interrupted-write-doesn't-corrupt — **636 passed, 68%**.
6. **Orchestrator pre-commit gate:** `uvx ruff@0.14.10 check` surfaced one F841 (unused `family` from the SSRF `getaddrinfo` unpack) + 2 files needing `ruff format` (concept_analyzer.py, output.py) — fixed with `ruff format` + `--fix --unsafe-fixes`; re-verified ruff check + format clean (CI src scope), markdownlint clean. (Same subagents-skip-ruff-format class as E013.)

7. **PR #110 first CI round:** 24/25 green, but **BPMN2DrawIO Tests (windows-latest)** failed at collection — `test_xxe.py` read `Path("/etc/hostname").read_text()` at **module level**, which raises `FileNotFoundError` on Windows (`\etc\hostname` absent), aborting the whole suite. Root cause: a POSIX-only hardcoded path used as the XXE exfil target. Fix: rewrote the test to create a `tmp_path` sentinel file and point the SYSTEM entity at `Path.as_uri()` (valid `file://` on both OSes), removing all module-level filesystem reads; ruff dropped the now-unused `pytest` import. Re-verified on Linux: 3 XXE tests pass, full suite 588 pass / 92%. This is the OS-fidelity value of the windows-latest matrix leg — a Linux-only subagent test check missed it.

**Status:** COMPLETE. PR #110 squash-merged as `039c2cc` (second CI round all 18 checks green after the Windows XXE-test portability fix). All 5 exploitable-in-code paths closed (XXE, plaintext-key, SSRF, brittle backoff, corruptible checkpoints); coverage floors held (bpmn 92%, visual-explainer 68%). Local main fast-forwarded 8a2988a→039c2cc.
**Duration:** ~50 minutes (including the Windows test-portability fix + one CI re-run)

---

### Entry 019 — Implement-Plan Phase 3: Injection-Surface Reduction [skill] [decision] [cleanup]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `039c2cc` (branch-protected), branch `impl/phase-3-injection`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 3 — reduce the prompt-injection "lethal trifecta" surface: (3.1) scope `Bash` narrowly in the skills/commands that currently grant unscoped `Bash` (inventory found **24** files: 14 skills + 10 commands — more than the ~15 estimate); (3.2) separate untrusted-fetch from local-action in the recon/audit skills; (3.3) resolve RI-03 (do spark-audit/jetson-audit SSH into fleet hosts with sudo?) and document the trust boundary in SECURITY.md. Ship as one PR, merge on green CI.

**Hypothesis:** The regression risk here is real and **cannot be runtime-tested** (skills are LLM-interpreted; U2). Mitigation: scope CONSERVATIVELY — for each file, `allowed-tools: Bash(<cmd>:*)` covering the UNION of shell commands its body actually invokes; where a skill genuinely needs unbounded analysis bash (e.g. arch-review), LEAVE `Bash` with a one-line justification and rely on 3.2's fetch/act separation instead of breaking it. Gate = `claude plugin validate --strict` green on all touched plugins + markdownlint. Expect no new CI test failures (frontmatter-only + SECURITY.md doc). Parallel: [3.1-skills, 3.1-commands, 3.3] disjoint file sets; 3.2 sequenced after 3.1 (both touch recon skill files).

**Rollback Plan:** All work on branch `impl/phase-3-injection`; `git branch -D` reverts pre-merge; every file git-tracked; revert per-skill if a scope proves insufficient. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **3.1 (Bash scoping):** 16 skills — 13 scoped to the exact command union (e.g. fleet-health→`Bash(ssh:*),Bash(curl:*)`; new-project→10 scopes; research-topic→5), 3 kept broad with an inline YAML justification because they run genuinely-dynamic scanners (security-analysis ≈9 native audit tools by stack; leak-risk-audit writes+runs ad-hoc Python scans; arch-review's 9 domain subagents run semgrep/bandit/lizard/trivy/etc.). 7 commands scoped (scaffold-plugin→mkdir, validate-plugin→git/sed/gh/base64, clean-repo→git/grep, convert-markdown→pandoc, bump-version→git, arch-synthesize→ls/echo, arch-review-single→mkdir); new-skill had no Bash. All enumerable — zero command carve-outs needed. `claude plugin validate --strict` exit 0.
2. **3.3 (RI-03 resolved):** spark-audit/jetson-audit DO SSH with passwordless sudo (`sudo dmesg`/`sudo tegrastats`/`sudo nvpmodel`/`sudo jetson_clocks`); the fleet `claude` user's sudo set includes root-equivalent `rm/chmod/chown/mount/apt/reboot`. Sharpest finding: **jetson-recon combines untrusted WebFetch/WebSearch (Checks 1-4) + a live SSH read (Check 5) in one skill** — the full trifecta. spark-recon does NOT SSH. SECURITY.md gained a "Fleet recon/audit trust boundary" section making SEC-01 explicit.
3. **3.2 (fetch/act separation):** all 4 fleet skills (spark-recon, jetson-recon, spark-audit, jetson-audit) gained `disable-model-invocation: true` (user-invoke-only — injected content can no longer auto-trigger an SSH/sudo skill) + a "Trust Boundary" section: fetched content is data-only, never determines which commands run; jetson-recon's ordering fixed (untrusted fetch first as data → then a fixed 10-command SSH allowlist). `claude plugin validate --strict` exit 0.

**Findings:** U3 resolved (yes, SSH+sudo). U2 (does scoping break skills?) mitigated by conservative union-scoping + the 3 documented broad carve-outs + `claude plugin validate --strict` green; residual runtime-regression risk accepted (skills are LLM-interpreted, not runtime-testable in CI) — the `disable-model-invocation` change is the highest-value net reduction (4 SSH-capable skills can no longer be injection-triggered at all).

**Status:** COMPLETE. PR #111 squash-merged as `c093904`, all 18 checks green (26 files, +98/−33). Injection surface reduced: 23 files scoped, 4 fleet SSH/sudo skills made user-invoke-only with trust boundaries, RI-03 answered + documented. Local main c093904.
**Duration:** ~40 minutes

---

### Entry 020 — Implement-Plan Phase 4: CI Gate Integrity [ci] [decision] [debug]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `c093904` (branch-protected), branch `impl/phase-4-ci`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 4 — make the now-enforced CI gates correct and complete: (4.1) lint the per-tool `tests/` dirs (fix ~28 hidden ruff errors, extend globs); (4.2) make mypy gate meaningfully (ratchet — see below); (4.3) validate schema *data* + fix `schemas/plugin.json` contradictions; (4.4) SHA-pin GitHub Actions + fix the dependabot false-claim + add concurrency/timeout; (4.5) scope pip-audit to tool deps + de-dup redundant root-suite runs + root coverage. Ship as one PR, merge on green CI.

**Hypothesis:** These edit `.github/workflows/{validate.yml,test.yml}` — the gates protecting every other PR — so a mistake here reddens CI for the whole repo. Run **sequentially** (4 of 5 items touch the same two workflow files; the plan marks Phase 4 Sequential) to avoid collisions. Critical ordering: 4.1 must fix the per-tool test lint errors BEFORE extending the ruff glob (else this PR's CI reddens). **U4 resolved:** mypy on the CI target surfaces **54 errors (bpmn2drawio) + 98 (visual-explainer) = 152** — far too many to zero-out safely here, so 4.2 uses a COUNT-RATCHET (fail only if the error count exceeds a committed per-tool baseline; feedback-docx stays strict at 0), removing `continue-on-error` so the ratchet actually gates against *new* type debt. Reaching 0 is deferred to a separate cleanup (like the flagged-out cli.py decomposition). Baselines must be computed in a CI-matching env (Python 3.11, `pip install -e .[dev]`) to avoid false failures.

**Rollback Plan:** All work on branch `impl/phase-4-ci`; `git branch -D` reverts pre-merge. Workflow edits are git-tracked and revert cleanly. If a workflow change reddens CI, fix-forward on the branch before merge (nothing reaches main until the PR is green). Post-merge `git revert <sha>`.

**Actions & Results:**

1. **4.1 (lint per-tool tests):** fixed 28 ruff errors in `plugins/*/tools/*/tests/` (25 auto I001 import-sort + 3 manual E501) + 19 files reformatted; extended validate.yml ruff check/format globs to include `plugins/*/tools/*/tests/`. Full-scope ruff check + format clean.
2. **4.2 (mypy count-ratchet):** U4 measured 54 (bpmn2drawio) + 98 (visual-explainer) = 152 existing errors — too many to zero-out here, so a ratchet: `.mypy-baseline` files (57 / 101 = measured+3 margin), test.yml mypy steps rewritten to fail only if count > baseline, `continue-on-error` REMOVED (now actually gates net-new type debt); feedback-docx stays strict. Full cleanup deferred (separate plan).
3. **4.3 (schema-data validation):** `schemas/plugin.json` fixed — removed the forbidden `tools` property, tightened version pattern to `^\d+\.\d+\.\d+$`, `additionalProperties:false` (after confirming all 9 real keys are declared). New `scripts/validate_schema_data.py` validates the 3 manifests against the schema, wired into the `Schema Validation` job. U6 clean (current manifests pass). Noted follow-up: `schemas/command.json` has `additionalProperties:false` without `argument-hint`/`effort` — enforcing as-is would fail every command, so left un-enforced (out of scope).
4. **4.4 (SHA-pin + concurrency/timeout):** `actions/checkout@v4`→`34e1148…`, `setup-python@v5`→`a26af69…`, `setup-node@v4`→`49933ea…` (real SHAs via `gh api`, tag kept as trailing comment for Dependabot); `concurrency: cancel-in-progress` + `timeout-minutes` on all 10 jobs; dependabot.yml's false SHA-pin claim made truthful.
5. **4.5 (scope pip-audit + de-dup):** `Dependency Security Audit` now runs `pip-audit --requirement <lock>` per tool instead of auditing the whole runner env (removes the Entry-016 setuptools-workaround, which was deleted); removed the redundant `pytest tests/integration/` step (the full `pytest tests/` covers it) + added root `--cov` reporting; removed validate.yml's duplicate root-pytest step (job kept 3 substantive steps, name unchanged). **All 10 job names verified byte-for-byte unchanged** (branch-protection required checks depend on job-name identity).
6. **Orchestrator gate:** all 3 workflow/config files YAML-valid; `scripts/validate_schema_data.py` exit 0; ruff full-scope clean; job-name grep confirms `Run Tests (${{ matrix.os }})` etc. intact.

7. **PR #112 first CI round:** 16/18 green; **BPMN2DrawIO + Visual Explainer Tests (windows-latest)** failed. Root cause: GitHub Actions defaults `run:` steps to **PowerShell** on Windows runners, and the new multi-line mypy-ratchet **bash** script (`set +e`, `[ "$ERRORS" -gt "$BASELINE" ]`, `if…then`) is not valid PowerShell (`ParserError: Missing '(' after 'if'`). The pre-existing single-command `run:` steps (pip/pytest) work under pwsh, which is why only the two NEW ratchet steps broke. Fix: added `shell: bash` to both ratchet steps (Git bash on Windows runners supports the `grep -oP` extraction). ubuntu legs were unaffected (bash default). This is the OS-fidelity value of the windows matrix again (cf. E018 XXE fix).

**Status:** COMPLETE. PR #112 squash-merged as `7fe821d` (second CI round all 18 green after the pwsh→`shell: bash` ratchet fix). CI gates now correct & complete: per-tool tests linted, mypy ratchet gating net-new type debt, schema *data* validated, actions SHA-pinned, pip-audit scoped. All job names preserved. Local main 7fe821d.
**Duration:** ~65 minutes (sequential 5-item phase + one Windows CI fix round)

---

### Entry 021 — Implement-Plan Phase 5: External-Call Robustness [skill] [ci]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `7fe821d` (branch-protected), branch `impl/phase-5-external`, orchestrator=Opus, implementer=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 5 — make the raw-curl research/brain-entry integrations fail fast and cleanly: (5.1) add `--max-time`/`--connect-timeout` to every curl; (5.2) check HTTP status / non-empty job ID after submit, fast-fail, honor 429/Retry-After; (5.3) move the Gemini research key from URL query to `x-goog-api-key` header + include a run TIMESTAMP in `/tmp` response filenames. Ship as one PR, merge on green CI.

**Hypothesis:** All 3 items edit the SAME file (`plugins/personal-plugin/references/research-provider-protocols.md`, plus brain-entry for 5.1), so ONE subagent does all three sequentially to avoid a self-collision (not 3 parallel). These are markdown instruction-file edits (curl invocations inside the protocol reference) — no Python, no tests exercise them, so CI risk is limited to markdownlint + plugin validation. Expect all 18 checks green.

**Rollback Plan:** All work on branch `impl/phase-5-external`; `git branch -D` reverts pre-merge; instruction-file edits are git-tracked. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **5.1 (timeouts):** `--connect-timeout 10` on every curl; `--max-time` tuned per call (600s Anthropic sync extended-thinking, 60s submits/POSTs, 30s poll GETs); poll GETs get `--retry 2` (idempotent), submits don't (avoid duplicate jobs).
2. **5.2 (status/error):** every submit captures curl exit code + HTTP status via `-w '%{http_code}'` and fast-fails on curl error / HTTP ≥400 / empty ID BEFORE any poll loop (kills the ~30-min-poll-a-nonexistent-job failure mode); Anthropic response checked for `error` before parse; poll loops treat missing `status`/`state` as error and honor HTTP 429 `Retry-After` (via `-D` header dump, 30s fallback).
3. **5.3 (key + temp files):** Gemini `?key=` moved to `x-goog-api-key` header (submit + poll); all `/tmp` response + header-dump filenames now include `[TIMESTAMP]` (reused the doc's existing placeholder, no new var).
4. **Gate:** `claude plugin validate --strict` exit 0; markdownlint 0 errors on both files; all 6 embedded bash blocks pass `bash -n`.

**Status:** COMPLETE. PR #118 squash-merged as `99d0610`, all 18 checks green (4 files, +212/−37). The raw-curl research/brain-entry legs now fail fast (timeouts + submit-status checks) instead of hanging, and the Gemini key no longer rides in the URL. Local main 99d0610.
**Duration:** ~20 minutes

---

### Entry 022 — Implement-Plan Phase 6: slide-gen Integrity [plugin] [decision] [skill]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `99d0610` (branch-protected), branch `impl/phase-6-slidegen`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 6 (decision D2: declare external, do NOT vendor) — (6.1) formally declare slide-gen an external-dependency plugin + add an `sg` preflight health-check + ADR-0008; (6.2) fix the `plugin.json` homepage (points at the wrong repo) + add prominent External-Dependency sections to slide-gen + root READMEs; (6.3) add CHANGELOGs to slide-gen + bpmn-plugin + cross-reference the two divergent Gemini image paths. Ship as one PR, merge on green CI.

**Hypothesis:** **U1 RESOLVED — the `slide-generator` engine repo is PRIVATE** (`gh repo view` → visibility PRIVATE), so slide-gen is genuinely owner-only today (confirms SA-001). ADR-0008 and the preflight must state this honestly rather than implying public installability: the preflight (`sg --version` early-exit with a clear "slide-gen requires the private slide-generator engine; not available to non-owners" message) is the key deliverable so a fresh non-owner install fails loudly-and-clearly instead of cryptically mid-pipeline. All changes are additive docs + skill-body preflight + a new ADR — no Python, so CI risk is markdownlint + plugin validation. Parallel: [6.1, 6.3] disjoint (6.1: slide-gen README/sg-full-workflow/ADR-0008; 6.3: CHANGELOGs + sg-generate-images), then 6.2 (plugin.json + slide-gen README + root README) after 6.1 (shared slide-gen README).

**Rollback Plan:** All work on branch `impl/phase-6-slidegen`; additive; `git branch -D` reverts pre-merge. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **6.1 (declare external + preflight + ADR-0008):** `docs/adr/0008-slide-gen-dependency-model.md` (Accepted) documents the external-dependency decision honestly — slide-gen is owner-only until `slide-generator` is public; alternatives (vendor / deprecate / status-quo) rejected with reasons. slide-gen README gained a prominent "External Dependency (REQUIRED)" section; `sg-full-workflow` gained a fail-fast Preflight (Step 0: `sg --version` → clear owner-only message if absent); one-line preflight bullets added to the 7 pipeline skills.
2. **6.3 (CHANGELOGs + Gemini cross-ref):** new `plugins/slide-gen/CHANGELOG.md` + `plugins/bpmn-plugin/CHANGELOG.md` (Keep-a-Changelog, backfilled from git history — the two-tier versioning is now fully instrumented); `sg-generate-images` gained a "Related Gemini Image Path" note (SA-004: the two Gemini paths are intentionally separate; changes must be applied in both). Verified 6.1's preflight bullet + 6.3's note BOTH survived on the shared `sg-generate-images/SKILL.md` (no lost update).
3. **6.2 (homepage + root README):** `plugins/slide-gen/plugin.json` homepage fixed `slide-generator`→`claude-marketplace` (RISK-01/PLAT-013); root README gained a slide-gen external-dependency note. `marketplace.json` carries no per-plugin `homepage`, so the version-sync check was correctly NOT extended (nothing to compare — INT-05 partially N/A).
4. **Gate:** `claude plugin validate --strict` green on slide-gen + bpmn-plugin; markdownlint clean on all touched files; JSON valid.

**Status:** COMPLETE. PR #119 squash-merged as `9cf8963`, all 18 checks green. slide-gen now honest: external-dependency declaration (ADR-0008), fail-fast preflight, fixed homepage, CHANGELOGs for all 3 plugins. U1 resolved (private repo → owner-only). Local main 9cf8963.
**Duration:** ~30 minutes

---

### Entry 023 — Implement-Plan Phase 7: Governance Docs, Egress Policy & Hygiene [config] [cleanup] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `9cf8963` (branch-protected), branch `impl/phase-7-docs`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 7 — close the documentation/policy debt + remove cruft: (7.1) SECURITY.md data-egress/confidentiality policy; (7.2) SECURITY.md supply-chain controls section; (7.3) resolve the ADR-0004 help-skill drift; (7.4) cruft removal (GITHUB_ERRORS.md ×2, gap-analysis, placeholder uv.lock, stale ruff.toml entry) + oversized command bodies → references; (7.5) skill error sections. Ship as one PR, merge on green CI.

**Hypothesis:** Additive docs + deletions + config, so CI risk is markdownlint + plugin validation. **DEFERRED: PLAT-012 (7.5's CI Python-matrix expansion 3.10/3.12)** — adding `python-version` to the matrix would change the job check names (e.g. `Run Tests (ubuntu-latest)` → `(ubuntu-latest, 3.11)`), which are branch-protection REQUIRED checks — renaming them would deadlock merges until the protection config is updated in lockstep. That coordinated change is out of scope for a clean phase; 7.5 does only the skill error-section work (SE-10). Batching: 4 disjoint-file subagents — [A] 7.1+7.2 (both edit SECURITY.md, one subagent), [B] 7.3 (docs/adr/0004 + generate-help.py), [C] 7.4 (root cruft + commands/), [D] 7.5 (skills/ error sections). `uv.lock` removal note: it's gitignored but tracked (committed before the ignore rule), so `git rm --cached` + `rm`.

**Rollback Plan:** All work on branch `impl/phase-7-docs`; `git branch -D` reverts pre-merge; deletions recoverable via git history. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **7.1+7.2 (SECURITY.md):** added a "Data Egress & Confidentiality Policy" section (classification tiers, NEVER-send list, tool→provider egress table, provider-DPA pointers with a verify-before-regulated-data caveat) + a "Supply-Chain Controls" section (Dependabot/pip-audit/CodeQL/GitGuardian/branch-protection, each with cadence + enforcement); sections renumbered, cross-referenced. Subagent fact-checked the evidence-trail citations (E016 is clear-prep, not the pip-audit scope — corrected to E017/E020).
2. **7.3 (ADR-0004 help drift):** amended ADR-0004 (2026-07-16 amendment) to drop the per-plugin help-skill requirement (superseded by ADR-0006 skills-first + native `/help`; no plugin ever implemented it); deleted the dead `scripts/generate-help.py`. Follow-up cleanup subagent removed the now-stale live references: `scripts/pre-commit` help.md-sync block (Check 5), CONTRIBUTING.md, TROUBLESHOOTING.md §6.2, docs/PLUGIN-DEVELOPMENT.md (checklist/PR-template/mistakes) — `bash -n` clean; only historical refs remain (CHANGELOG, docs/archive).
3. **7.4 (cruft + config):** deleted `GITHUB_ERRORS.md` (root + docs/archive/), `gap-analysis-2026-04-30.md`, root placeholder `uv.lock` (verified 52 bytes, zero packages; real visual-explainer uv.lock untouched); removed stale `research_orchestrator` from `ruff.toml` isort; removed the now-dead `GITHUB_ERRORS.md` markdownlint ignore from `.markdownlint.json`. **SE-11 (oversized command-body extraction) DEFERRED** — mechanically refactoring 3 large frozen-legacy commands (validate-plugin 675 / implement-plan 573 / new-skill 530) without runtime tests is disproportionate risk for a Low finding.
4. **7.5 (skill error sections):** added tailored `## Error Handling` sections to **14** skills that lacked one (SE-10 estimated ~8) — each 5-6 bullets on that skill's real failure branches. **PLAT-012 (CI Python-matrix 3.10/3.12) DEFERRED** — adding `python-version` to the matrix renames the branch-protection required checks (deadlock risk); needs a coordinated protection update, out of scope.
5. **Gate:** `claude plugin validate --strict` green ×3 plugins; markdownlint clean on all touched .md; ruff.toml (TOML) + .markdownlint.json (JSON) parse OK; `bash -n scripts/pre-commit` clean.

**Status:** COMPLETE. PR #120 squash-merged as `e3bf0a4`, all 18 checks green. Egress/supply-chain policy documented, ADR-0004 help drift resolved + dead script/refs removed, cruft deleted, 14 skills gained error-handling. SE-11 + PLAT-012 deferred. Local main e3bf0a4.
**Duration:** ~40 minutes

---

### Entry 024 — Implement-Plan Phase 8: Test/Eval Safety Net (scoped) [skill] [ci] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `e3bf0a4` (branch-protected), branch `impl/phase-8-tests`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 8 (final) — (8.1) resolve the dead `generate_batch`/`--concurrency` PERF-01 finding; (8.2) fix the contradictory/conditional test skips (QA-07 key-gated mocked full-pipeline test, QA-08 runtime-conditional resize skips); (8.3) add an eval-mapping CI check (every `evals/*.eval.md` maps to a live skill/command) + targeted evals for the 4 highest-blast-radius skills; (8.4) add `pytest -n auto` to per-tool CI jobs. Ship as one PR, merge on green CI.

**Hypothesis:** **8.1 decision: REMOVE, not wire.** The `--concurrency` flag + `asyncio.Semaphore` + `generate_batch()` are inert (the CLI runs images serially); wiring them up (parallel images + a memory cap per PERF-05) is a genuine async rewrite better suited to a dedicated effort with the flagged-out cli.py decomposition — for this scoped phase, REMOVING the inert knob closes PERF-01 honestly with zero regression risk (removing dead code + an advertised-but-inert flag; PERF-05 becomes moot). Batching: 8.1 first (src: image_generator.py/cli.py), then [8.2 test files, 8.3 evals+validate.yml+script, 8.4 test.yml+pyproject×3] parallel (disjoint file sets). Coverage floors (bpmn 90 / visual-explainer 65 / feedback 95) + `-n auto` xdist coverage-aggregation are the CI guards; expect green.

**Rollback Plan:** All work on branch `impl/phase-8-tests`; `git branch -D` reverts pre-merge; coverage floors guard regressions. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **8.1 (PERF-01, REMOVE):** deleted the inert `generate_batch()`, `asyncio.Semaphore`, `max_concurrent`, and the `--concurrency` CLI flag + `GenerationConfig.concurrency` field; removed the corresponding tests. Serial generation path untouched. 624 passed, 68% (coverage UP — dead code removed). PERF-05 (concurrent-buffer memory) now moot. Stale `--concurrency` README refs cleaned separately.
2. **8.2 (QA-07/QA-08):** un-gated `test_full_pipeline_success` from `ANTHROPIC_API_KEY` (root cause: `concept_analyzer` has a key-presence guard before the mocked client — satisfied with the `mock_env_with_api_keys` fixture, verified no real network call with `env -u`); made the resize test deterministic (`max_size_bytes` forces the branch) + removed the Pillow-absent skip (hard dep). 64 previously-skipped→run, full suite 626 passed.
3. **8.3 (QA-03 subset/SA-006):** `scripts/check_eval_mapping.py` (every `evals/*.eval.md` → live skill/command; `cross-cutting`+`maps_to` escape hatch) wired into validate.yml's `plugin-validate` job; removed 3 drifted evals (help, new-command, and a bonus `validate-and-ship`→`release-plugin` rename); added 4 high-blast-radius evals (release-plugin, arch-review, ultra-plan, leak-risk-audit). 35 evals all map; verified exits 1 on injected drift.
4. **8.4 (PERF-06):** `pytest-xdist>=3.5` added to all 3 tools' `[dev]` extras + `-n auto` on the 3 per-tool CI jobs; all xdist-safe locally (bpmn 588/92.27%, visual-explainer 624/67.74%, feedback 69/96.95%). Job names unchanged.
5. **Combined gate:** visual-explainer 626 passed/68% (8.1+8.2 merged state); eval-mapping exit 0 (35); schema-data exit 0; ruff full-scope clean; test.yml + validate.yml YAML valid + all job names intact; `claude plugin validate --strict` OK. **PERF-01 wiring deferred** (chose safe remove).

**Status:** COMPLETE. PR #121 squash-merged as `0e0895c`, all 18 checks green (mypy ratchet held after the dead-code removal; xdist parallelism worked cross-OS). This was the final phase — **the entire 8-phase arch-review remediation (32/32 items) is now merged to `main`.**
**Duration:** ~55 minutes (Phase 8: 4 items + README cleanup, single CI round — no fix needed)

**Remediation retrospective (Entries 017–024):**
- **Outcome:** 1 Critical + 14 High + the load-bearing Mediums/Lows closed across 8 PRs, each independently CI-gated and squash-merged. `IMPLEMENTATION_PLAN.md` `Completed: 2026-07-16` (v9 → will be archived as v9 by the next plan).
- **What worked:** per-phase branch+PR+merge kept blast radius small and let branch protection (enabled in Phase 1) gate every subsequent phase — the governance-first ordering paid off literally. Conservative choices (mypy ratchet not cleanup, Bash union-scoping with documented carve-outs, remove-not-wire for PERF-01, defer PLAT-012/SE-11) avoided regressions on changes that couldn't be runtime-tested.
- **Recurring failure class:** the **windows-latest matrix** caught 2 defects a Linux-only check missed — a `/etc/hostname` XXE test (E018) and a PowerShell-vs-bash mypy-ratchet step (E020). Lesson reinforced: any new multi-line CI `run:` step needs `shell: bash`; any test with an OS-specific path needs a portable fixture (`tmp_path`/`Path.as_uri()`). See [[ci-learnings]].
- **Branch-protection self-consistency:** required checks are keyed by JOB NAME, so every workflow edit (Phases 4, 8) had to preserve job names byte-for-byte; the Python-matrix expansion (PLAT-012) was deferred precisely because it would rename them.
- **Open follow-ups (deferred, not lost):** SE-11 (oversized-command extraction), PLAT-012 (CI Python matrix + coordinated protection update), PERF-01 wiring (parallel image gen + memory cap), and the plan's explicit scope-outs (cli.py decomposition, full 39-skill eval corpus, visual-explainer floor→85%), plus a possible coordinated version bump to signal the hardening release.

---

### Entry 025 — Release personal-plugin 11.0.0 (arch-review hardening) [plugin] [build] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `689842c` (branch-protected), branch `release/personal-plugin-11.0.0`, personal-plugin v10.3.0 pre-release

**Objective:** Bump personal-plugin **10.3.0 → 11.0.0** (MAJOR) to signal the arch-review hardening as a proper release, rather than shipping materially-changed skills/tools under the same 10.3.0. Lockstep plugin.json + marketplace.json bump; CHANGELOG 11.0.0 sections in root + plugin changelogs summarizing Entries 017–024. Merge on green CI, update installed cache.

**Hypothesis:** MAJOR is the correct SemVer tier because the remediation changed user-facing/interface behavior: visual-explainer's `--concurrency` CLI flag was REMOVED (8.1); ~15 skills' + 7 commands' `allowed-tools` were narrowed (3.1) — a capability-grant change; 4 fleet skills gained `disable-model-invocation: true` (3.2) — they're no longer model-triggerable; tool internals hardened (XXE/SSRF/`.env`/atomic writes). Only personal-plugin is bumped (bpmn-plugin 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0 unchanged — marketplace_version is not bumped for single-plugin updates per CLAUDE.md). Expect `claude plugin validate --strict` exit 0, version-sync gate green (plugin.json == marketplace.json == 11.0.0), all 18 CI checks green under branch protection, squash-merge, cache update 10.3.0→11.0.0.

**Rollback Plan:** All work on branch `release/personal-plugin-11.0.0`; `git branch -D` reverts pre-merge. Version/CHANGELOG edits git-tracked. Installed cache is rebuildable API-managed state (D19) — `claude plugin update personal-plugin@troys-plugins` re-syncs. Post-merge `git revert <sha>`.

**Actions & Results:**

1. Branch created; Entry 025 logged (this entry) before any commit.

2. Bumped plugin.json + marketplace.json 10.3.0→11.0.0 (version-sync gate green); wrote `## [11.0.0]` MAJOR sections into root + plugin CHANGELOGs (Changed-breaking / Security / Added / Fixed / Removed). `claude plugin validate --strict` exit 0.
3. Committed, opened **PR #123**, all 18 checks green under branch protection, squash-merged as **`fbb1437`**; local main fast-forwarded 689842c→fbb1437.
4. Installed cache: `claude plugin update personal-plugin@troys-plugins` → 10.3.0→11.0.0 (restart-gated; new definitions load next session).

**Status:** COMPLETE. personal-plugin **11.0.0** live on main (`fbb1437`), plugin.json == marketplace.json == 11.0.0; the arch-review hardening is now a tagged-by-version release. bpmn-plugin 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0 unchanged. Current Baseline updated below.
**Duration:** ~15 minutes

--- New session: 2026-07-16 — post-11.0.0 backlog burndown. User directive: prioritize the whole GitHub-issue backlog (dependabot PRs + deferred #125–#131) and work through it autonomously, one item at a time, stopping only when blocked or finished. This entry covers Action Item A1 (dependabot triage). ---

### Entry 026 — Dependabot triage: 6 open dependency PRs [ci] [decision] [build]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `37868fb` (branch-protected, 14 required checks, `enforce_admins=false`), personal-plugin 11.0.0 / bpmn 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0. Open dep PRs: #113/#114/#115 (GitHub Actions), #116 (bpmn2drawio group), #117 (visual-explainer group), #104 (google-genai 1.75→2.11 MAJOR).

**Objective:** Clear the dependabot PR queue (A1). Merge safe bumps, resolve the one blocked check, and correctly dispose the risky google-genai major bump.

**Hypothesis (with A1 CORRECTION):** A1's original plan was to CLOSE #113/#114/#115 on the premise they "conflict with Phase-4 SHA-pinning." **Investigation refuted that premise:** these actions are SHA-pinned with a trailing `# vN` comment, and each dependabot PR updates *both* the pinned SHA *and* the comment (e.g. `actions/setup-python@ece7cb06…  # v6.3.0`) — it preserves the SHA-pinning discipline exactly. All three are `CLEAN` (14/14 checks green). So the corrected disposition is **MERGE #113/#114/#115**, not close. #116 (bpmn2drawio patch/minor group) is `CLEAN` → merge. #117 (visual-explainer group) is `BLOCKED` solely by a failing **Dependency Security Audit** (pip-audit) — the other 14 checks pass; hypothesis is the audit is stale/transient (branch predates a main-side scope/ignore) → rebase onto current main and re-run, merge if green. #104 (google-genai **1.75→2.11 MAJOR**) is `CLEAN` in CI but tests are fully mocked (cannot catch API breaks): typed-error contract VERIFIED intact in v2.11.0 (`APIError.code:int`, `ClientError`/`ServerError` subclasses all present at the v2.11.0 tag), but broader API surface (`genai.Client`, `types.HttpOptions/ImageConfig/GenerateContentConfig`, `client.models.generate_content`, response `.parts`/`.candidates`) is under source-level verification by a subagent → merge only if that returns SAFE, else HOLD with a documented reason. Success = green main after each merge, no CI regression, clean queue.

**Rollback Plan:** Each dependabot merge is a squash/merge commit on main → `git revert <sha>` via a follow-up PR (branch-protected, so revert is itself a PR). Closing a PR is reversible (reopen). #104 HOLD is a no-op. This Entry 026 + the A1/A2 Action-Item and Current-Baseline doc edits land via a small docs PR on branch `docs/session-2026-07-16-triage`; `git branch -D` reverts pre-merge.

**Actions & Results:**

1. Entry 026 logged (this entry) before any merge. Verified branch protection: `strict_up_to_date=false` (no rebase needed between merges), `required_approving=0`, `enforce_admins=false` → owner can merge on green checks.
2. **#116 / #115 / #113 / #114 → MERGED** (squash). #113/#114/#115 confirmed as correct SHA-pinned bumps (SHA + `# vN` comment both updated), 14/14 green; #116 bpmn2drawio group green. main `37868fb → e8d3317`, no conflicts (the two workflow-file PRs 3-way-merged cleanly).
3. **#104 (google-genai 1.75→2.11 MAJOR) → MERGED** (squash), main `→ 6bf2d84`. Disposition changed from A1's "HOLD" to MERGE after two independent verifications: (a) subagent confirmed the full API surface used by `image_generator.py` — `genai.Client`, `types.HttpOptions(timeout=ms)`, `types.ImageConfig`, `types.GenerateContentConfig(image_config=…)`, `client.models.generate_content`, and response `.parts`/`.candidates`/`inline_data.data`/`finish_reason` — is unchanged at the v2.11.0 tag; the 2.0.0 breaking changes are scoped to the *Interactions API* (changelog: "GenerateContent usage is unaffected"), which this code never touches; typed-error contract (`APIError.code`, `ClientError`/`ServerError`) also intact. (b) Local `pip-audit --python 3.11` on #104's lockfile: resolves cleanly (consistent `pydantic 2.13.4` / `pydantic-core 2.46.4`), "No known vulnerabilities found" against today's advisory DB. pyproject floor widened to `google-genai>=1.0.0,<3.0.0`.
4. **#117 (visual-explainer minor group) → CLOSED.** Root-caused the BLOCKED "Dependency Security Audit": *not* a CVE — a broken lockfile. Dependabot's grouped bump raised `pydantic-core` 2.46.4→**2.47.0** but left `pydantic` at 2.13.4, which pins `pydantic-core==2.46.4` exactly → `ResolutionImpossible` (reproduced locally on Python 3.11, matching CI). pip-audit fails because it can't install the inconsistent set to scan it. Closed with an explanatory comment; #104 regenerates this same lockfile with a consistent pair, so dependabot will re-propose the residual valid minors (anyio 4.14.1→4.14.2, google-auth 2.55.2→2.56.0) against the post-#104 baseline.
5. Post-merge verification: `pip-audit` clean on all three tool lockfiles on main `6bf2d84`; the docs PR carrying this entry runs the full 14-check suite against the merged state (combined verification, since `strict=false` skipped a merged-state re-run).

**What Worked:** Reproducing pip-audit locally via `uvx --python 3.11 pip-audit --requirement <lockfile>` (system `python3-venv` is absent, but `uv` is present) gave a definitive root cause in seconds where the CI logs were unretrievable via `gh run --log-failed`. Verifying a major-bump's real API surface at the pinned source tag (not just the changelog) is what flipped #104 from HOLD to a confident MERGE.

**Findings (course-corrections vs the A1 plan):**
- **A1 was wrong to propose closing #113/#114/#115.** SHA-pinned actions are updated *correctly* by dependabot (bumps both the pinned SHA and the trailing `# vN` comment). They preserve the pin discipline and should merge, not close. See D25.
- **A1's HOLD on #104 was over-cautious given verification is cheap.** Source-tag API verification + local audit resolved it to a safe MERGE. Kept the HOLD discipline (didn't merge blind) but discharged it with evidence.
- **Dependabot grouped updates can split tightly-coupled pins** (`pydantic`/`pydantic-core` are lockstep-versioned). This produces an un-installable lockfile that surfaces as a pip-audit *install* failure, not a vuln. Pattern logged to ci-learnings + CLAUDE.md.

**Status:** COMPLETE. Queue cleared: 5 merged (#104/#113/#114/#115/#116), 1 closed with rationale (#117). main `6bf2d84`, all tool lockfiles CVE-clean, google-genai on 2.11.0. A1 → Completed (C21). External contributor PRs #97/#98 are out of scope for this triage.
**Duration:** ~35 minutes

### Entry 027 — Decompose visual-explainer cli.py god module (#125 / P1) [refactor] [decision] [debug]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `da5d1b6` (branch-protected), branch `refactor/ve-cli-decompose`. visual-explainer cli.py = **1,814 lines**, 37% line coverage (drags package to 68%). Local test env: `uv` venv (Python 3.11) at scratchpad, baseline **626 passed / 0 failed** with google-genai 2.11.0.

**Objective:** Break the 1,814-line `cli.py` god module into cohesive, independently-testable modules WITHOUT changing behavior (#125/P1). This is the keystone that unblocks #127 (raise the package-wide coverage floor 65→85% — cli.py at 37% is the ceiling).

**Hypothesis:** cli.py splits along 6 clean seams (a read-only subagent mapped it): (1) `terminal.py` — console singleton + capability checks (`is_interactive`, `supports_unicode`, `get_console`, `RICH_AVAILABLE`, `_console`, Rich imports); (2) `cli_args.py` — argparse (`_bounded_float/int`, `create_parser`, `__version__`); (3) `io_utils.py` — `_atomic_write_text`; (4) `reporting.py` — all `display_*` + `GenerationProgress` + `estimate_cost` + `prompt_for_*`; (5) `pipeline.py` — the 7 async pipeline/orchestration fns (`_analyze_concepts`, `_generate_prompts`, `_evaluate_and_refine`, `_execute_generation_loop`, `_save_outputs`, `run_generation_pipeline`, `load_checkpoint_and_resume`); (6) `cli.py` remains a thin ~200-line entry layer (import-time side effects + re-exports for the entry contract + `main` + `__main__` guard). Expect: nothing outside cli.py breaks (only `__main__.py` + `[project.scripts]` `visual_explainer.cli:main` import from it, and no sibling imports cli — no circular-import risk); all 626 tests still pass; total coverage ≥68% (unchanged — this PR moves code, doesn't add tests). **The one sharp hazard is `unittest.mock.patch` name-resolution:** `test_cli_extended.py` patches ~30 symbols on `visual_explainer.cli.*`. Contract preserved by (a) consumers referencing cross-module patchable *terminal* symbols module-qualified (`terminal.get_console()`, `terminal.RICH_AVAILABLE`) so one patch point intercepts everywhere; (b) *pipeline* helpers called bare within pipeline.py (same-module patch intercepts); (c) repointing the test patch strings to the new defining module (`terminal.*` / `pipeline.*`) — but KEEPING `cli.GenerationConfig` (×4) and `cli.load_checkpoint_and_resume` (×1) since `main` (stays in cli) uses cli's binding. A mis-repointed patch makes the *real* fn run → the test FAILS loudly (not a silent pass), so the 626-green criterion is trustworthy. Success = 626 pass, coverage ≥68%, test diff is patch-target strings only (zero assertion changes), all 14 CI checks green on both OSes.

**Rollback Plan:** All work on branch `refactor/ve-cli-decompose`; `git branch -D` reverts pre-merge; post-merge `git revert <squash-sha>` via PR. Pure code-move + test-patch-repoint — no schema/data/external-state change. The local `uv` venv is throwaway (scratchpad). Behavior-preservation is verified by the unchanged 626-test suite before each commit.

**Actions & Results:**

1. Read-only map produced (subagent); green baseline (626) captured; Entry 027 logged before any edit.
2. Extraction executed (opus-implementer, verbatim function moves) into `terminal.py` (106), `cli_args.py` (196), `io_utils.py` (35), `reporting.py` (546), `pipeline.py` (817); `cli.py` **1,814 → 299** lines (docstring + import-time side effects + `__all__` re-export contract + `main` + guard).
3. Patch contract preserved as designed: terminal symbols referenced module-qualified (`terminal.get_console()`, `terminal.RICH_AVAILABLE`); pipeline helpers bare within pipeline.py; 9 test patch-string types repointed to `terminal.*` / `pipeline.*`; `cli.GenerationConfig` + `cli.load_checkpoint_and_resume` kept on cli. One extra, honestly-flagged test edit: the `_console` singleton reset alias `import visual_explainer.cli as cli_mod` → `...terminal as cli_mod` (5 sites) — necessary since `_console` moved to terminal; still a pure repoint, no assertion change.
4. **Independent verification (my uv venv, not the subagent's self-report):** full suite **626 passed / 0 failed**, coverage **69%** (≥68); `ruff check src/ tests/` + `ruff format --check` clean; `mypy src/ --ignore-missing-imports` = **97 errors ≤ 101** baseline (`.mypy-baseline`); test diff grep for any changed line NOT referencing `cli`/`terminal`/`pipeline` module paths → **empty** (zero logic/assertion change). End-to-end smoke: `import visual_explainer.cli` still fires import-time `PYTHONIOENCODING=utf-8`; `cli.main.__module__` == `visual_explainer.cli`; all re-exports present; `python -m visual_explainer --help`/`--version` exit 0.
5. Rich-import split (subagent deviation, reviewed & accepted): `terminal.py` imports only `Console`; `Panel`/`Table`/`Prompt`/`Progress` move with their consumers under their existing `try/except ImportError` guards — preserves the "cli importable without Rich" property. The harness's Pyright "could not resolve `.cli_args`/possibly-unbound Panel" diagnostics are IDE-env artifacts (Pyright not using the editable venv); CI runs ruff+mypy+pytest, not Pyright, and all three are green + the package imports/runs.

**Status:** COMPLETE. Committed `40a8f01`, **PR #133** all 14 checks green both OSes (incl. Windows matrix + mypy ratchet), squash-merged **`72c6fdc`**; issue #125 auto-closed. cli.py 1,814→299 lines across 6 modules, 626 tests green, zero behavior change. Coverage floor still 65% (raising to 85% is #127, now unblocked).
**Duration:** ~50 minutes (incl. read-only map + opus implementer + independent verification)

### Entry 028 — Raise visual-explainer coverage floor 65% → 85% (#127 / P3) [test] [ci]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `72c6fdc` (post-#125), branch `test/ve-coverage-85`. Package coverage **69%** (816 line+branch units missed of ~2632). Floor gate: `.github/workflows/test.yml:125` `--cov-fail-under=65` (package-wide `--cov=visual_explainer`). Local uv venv baseline: 626 passed.

**Objective:** Raise the package-wide coverage gate 65 → 85% (#127/P3), enabled by #125's decomposition making cli's former internals independently testable. Write meaningful characterization tests (real assertions, not coverage-gaming), then bump the `--cov-fail-under` floor.

**Hypothesis:** The gap is concentrated in the decomposed modules that inherited cli.py's 37% coverage — reporting.py (157 miss), pipeline.py (154), cli.py/main (52), terminal.py (18), io_utils.py (8) = 389 — plus two pre-existing low modules with test files, concept_analyzer.py (98) and api_setup.py (185). To reach 85% total miss must drop from 816 to ≤~395 (cover ~420 units). Covering the 5 decomposed modules to ~90% (~389) gets to ~84%; adding concept_analyzer top-up clears 85%; api_setup adds margin. Plan: 6 parallel test-writers (sonnet-implementer), each a distinct NEW or appended test file (no cross-conflict), using the rich conftest fixtures (`sample_generation_config`, `sample_concept_analysis`, `sample_image_prompt`, `sample_evaluation_result`, `checkpoint_file`, mock API responses); each self-checks with a unique `COVERAGE_FILE`. I integrate, run the full suite, and bump the floor to the honest achieved number (target ≥85; if genuinely-hard interactive/api paths block a true 85, set the floor to the achieved value and document). Success = full suite green, total coverage ≥85% (or documented honest floor), floor gate raised, all 14 CI checks green.

**Rollback Plan:** All on branch `test/ve-coverage-85`; tests-only + one CI-gate number change (no product-code change) → lowest-risk category. `git branch -D` pre-merge; `git revert` post-merge. If a test-writer produces flaky/gaming tests, they're dropped before commit (I review each new file).

**Actions & Results:**

1. Coverage baseline captured (69%, 626 tests); Entry 028 logged before any test added.
2. 6 parallel sonnet-implementer test-writers dispatched (4 new files for decomposed modules + 2 appends to existing files), each with strict no-coverage-gaming rules and a unique `COVERAGE_FILE`. Results per module: **reporting 14→99%** (test_reporting.py, 61 tests), **pipeline 8→99%** (test_pipeline.py, 30), **cli 50→97%** (test_cli_main.py, 26; complements existing test_cli_extended.py), **terminal 50→91% / io_utils →100%** (test_terminal.py, 25), **concept_analyzer 53→99%** (test_concept_analyzer.py +63 appended), **api_setup 43→98%** (test_api_setup.py +52 appended). +257 tests total.
3. Integration: stripped 2 unused imports (ruff `--fix`), ran `ruff format` on the 6 files (writers hadn't formatted — the CI format gate would've failed). Synced the local uv venv to `.[dev,all]` (docx/pypdf/bs4/xdist) to MIRROR the CI job's install (`pip install -e ".[dev,all]"`, test.yml:121) so the new SSRF/docx/pdf/httpx tests run under CI-identical deps.
4. **Verified with the exact CI command** (`pytest tests/ -n auto --cov=visual_explainer --cov-branch --cov-fail-under=85`): **883 passed, total coverage 93.29%**, "Required test coverage of 85% reached", gate exit 0. `ruff check` + `ruff format --check` clean. Every module ≥78% (lowest: prompt_generator 78; the 6 targeted modules 91–100%). Uncovered remainder is import-time optional-dep guards + `__main__` script-entry lines (documented per module) + one Windows-only ctypes branch (unreachable on Linux).
5. Bumped the floor gate `test.yml:125` `--cov-fail-under` **65 → 85**. Chose 85 (the issue's target) over a tighter 90: actual 93.29% leaves 8pts headroom, well above cross-OS coverage variance (~0.2%, from platform-branch differences like terminal's Windows ctypes path), so the Windows runner also clears 85 without flakiness; future work can ratchet higher (ratchet philosophy per D24).

6. Committed `abce39a`, opened **PR #134**. **Windows-latest CI caught 2 OS-specific test defects Linux missed** (the documented Windows-matrix value): `test_terminal.py::…test_fallthrough_to_legacy_returns_false` and `test_api_setup.py::…test_ctypes_fallback_returns_false_on_non_windows_ctypes` both `assert supports_unicode() is False` but got `True` on Windows. **Root cause:** the writers (running on Linux) relied on `ctypes.windll` being *absent* (→ AttributeError → False); on real Windows `ctypes.windll` exists and `GetConsoleOutputCP()` returns 65001 (UTF-8) → `True`. Windows coverage itself was fine (93.21% > 85). **Fix:** mock `ctypes.windll` (`create=True`) so `GetConsoleOutputCP` returns a legacy code page 437 (non-UTF8) → deterministically `False` on any host OS; renamed the api_setup test to `test_ctypes_legacy_codepage_returns_false`. (CodeQL's 2s "fail" is a non-required check — ignored.) Re-verified locally: 883 passed, 93.27%, ruff clean.

**Status:** COMPLETE. Fix committed `e033577`, PR #134 CI green both OSes, squash-merged **`2cb6fed`**; issue #127 auto-closed. Coverage 69→**93%**, floor gate **65→85** live on main. Filed **#135** (CodeQL default-setup fails 2s on every PR — non-required/non-blocking, low-pri hygiene). Reinforces standing rule: any test touching an OS-specific path needs a portable fixture (fully mock the platform probe).
**Duration:** ~55 minutes (6 parallel test-writers + integration + 1 Windows-portability fix round)

### Entry 029 — Grow the behavioral eval corpus (#126 / P2) [test] [ci]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `2cb6fed`, branch `test/eval-corpus-expansion`. Corpus already at 35 evals (14 skills + 21 commands); `check_eval_mapping.py` (stdlib) enforces every eval maps to a live skill/command.

**Objective:** Add behavioral evals for the next ~8–10 high-traffic skills that lack a dedicated eval (#126/P2, arch-review QA-03/SA-006), keeping `check_eval_mapping.py` green and following the established `.eval.md` format.

**Hypothesis:** The gap (computed: skills whose name is not a `command:`/`maps_to:` target of any eval) is 9 personal-plugin + 9 slide-gen skills; bpmn-plugin already has coverage (the issue's "bpmn zero" is stale). Highest-value tranche = **slide-gen ×6** (sg-research/outline/draft/optimize/build/full-workflow — a whole-plugin surface from zero) + **personal-plugin ×4** (clear-prep, new-project, archive-project, wiki — user-facing). 10 new `evals/skills/<name>.eval.md` files, each a real behavioral contract (Purpose/Fixtures/Setup/Scenarios with Must/Should/Must-NOT + Rubric) derived from the actual SKILL.md, `command: <name>` + `type: skill` frontmatter. Written by 4 parallel eval-writers (distinct new files → no conflict). Expect `python3 scripts/check_eval_mapping.py` exit 0, markdownlint clean, all CI green. Success = 10 evals added, mapping-check green, no fixture needed (these skills are self-contained or use their own inputs).

**Rollback Plan:** New-files-only additions in `evals/skills/` on branch `test/eval-corpus-expansion`; `git branch -D` pre-merge, `git revert` post-merge. Zero product-code/CI-gate change (pure eval docs + no changes to `check_eval_mapping.py`).

**Actions & Results:**

1. Gap computed, format internalized (ship.eval.md template + README), Entry 029 logged before any eval written.
2. 4 parallel sonnet-implementer eval-writers, each deriving contracts from the actual SKILL.md (not invented). **10 new `evals/skills/*.eval.md`:** slide-gen — sg-research/sg-outline/sg-draft (6 scenarios each), sg-optimize/sg-build/sg-full-workflow (6–7 each, incl. fail-fast preflight + mid-pipeline-halt + missing-artifact); personal-plugin — clear-prep (5), new-project (6), archive-project (10, incl. 2 protect-unrecoverable-work failure scenarios), wiki (11, all sub-ops: ingest/lint/query/propagate + layout detection). Writers correctly adapted to `disable-model-invocation: true` (new-project, archive-project → no proactive-trigger scenario).
3. **Independent verification:** `python3 scripts/check_eval_mapping.py` → "45 eval file(s) all map to a live skill or command" (exit 0); exactly 10 new files, all with correct `command: <name>` + `type: skill` frontmatter; `markdownlint-cli` clean on all 10. Quality spot-check (clear-prep.eval.md) confirmed a real behavioral contract with accurate Must/Should/Must-NOT + rubric, not boilerplate — even encodes the clear-prep-vs-new-project boundary.

**Status:** IMPLEMENTATION VERIFIED locally (45 evals mapped, markdownlint clean); committing + PR next. Corpus grew 35 → 45 evals; slide-gen went from zero to 6-skill coverage. Docs-only additions (no product-code, no CI-gate, no `check_eval_mapping.py` change).
