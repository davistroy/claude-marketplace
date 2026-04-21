# Implementation Plan

**Generated:** 2026-04-21 11:28:18
**Based On:** `.tmp/modernization-requirements-20260421.md` (ultra-plan synthesis from portfolio assessment)
**Total Phases:** 7
**Estimated Total Effort:** ~1,580 LOC across ~52 files

---

## Executive Summary

This plan modernizes the troys-plugins marketplace to adopt Claude Code features added in late 2025 (`context: fork`, `isolation: worktree`, `paths:` auto-activation, dynamic context injection), deprecates items now fully covered by native commands (`/help`, `/skills`, `/review`, `/ultrareview`), and consolidates ~70% textual duplication between the jetson/spark audit and recon skills into a shared reference. The scope covers 23 skills and 25 commands across two plugins; `brain-entry` and `ask-questions` are explicitly excluded per user instruction.

The most architecturally significant change is Phase 4's audit/recon consolidation — extracting the shared five-check framework into a reusable reference file and thinning each machine-specific skill to a config layer. The highest-risk change is Phase 7's replacement of the research-orchestrator Python tool with 3 parallel `context: fork` subagents (Option A, user-approved; loses real-time streaming progress on long runs). Interrelated findings have been grouped into integrated change sets rather than per-item patches — for example, scaffolding generator modernization (Phase 2) and cross-cutting pattern adoption (Phase 5) share the same feature vocabulary and must teach the same syntax.

Phase ordering favors low-risk quick wins first (deprecations, doc fixes), then the foundational scaffolding updates (Phase 2), then progressively higher-risk modernization work. Every phase leaves the repository in a working, shippable state.

---

## Plan Overview

Phases are ordered by blast radius and risk: Phase 1 is isolated deletions and documentation (LOW risk, unblocks nothing but reduces stale references). Phase 2 updates the three scaffolding generators to teach modern features — this is foundational because it prevents future drift regardless of whether existing skills get modernized. Phases 3–7 apply the modern patterns to existing skills, grouped by coherent change sets rather than by pattern-type (avoiding the same file being touched in multiple phases).

The critical path runs sequentially phase-by-phase. Within each phase, work items are frequently parallelizable (flagged in the Parallel Work Opportunities table). Phases 1–4 could run in parallel if multiple contributors are available; Phase 5 benefits from Phase 2 preceding it so the modern frontmatter field catalog is already documented.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | Deprecations & Doc Fixes | 2 help skills deleted, review-pr deleted, 3 disambiguation notes | S (~6 files, ~80 LOC) | None |
| 2 | Scaffolding Modernization | Modern frontmatter catalog in new-skill/new-command/scaffold-plugin; common-patterns "Advanced Features" section | M (~4 files, ~200 LOC) | None |
| 3 | Planning Workflow Modernization | `/ultraplan` + `/batch` routing; per-phase worktree isolation in implement-plan; Execution Mode in plan-template | M (~5 files, ~150 LOC) | None |
| 4 | Audit/Recon Consolidation | Shared reference file; 4 skills thinned to config layer; `/schedule` integration docs; `paths:` with loop guard | L (~7 files, ~300 LOC) | None |
| 5 | Analysis Skills Modernization | `context: fork` + dynamic injection across 5 analysis skills; arch-review explicit subagent_type + worktree | M-L (~5 files, ~250 LOC) | Phase 2 recommended |
| 6 | Ship + Hooks + Wiki paths | Dynamic injection in ship; opt-in pre-commit hook; `paths:` for create-wiki and security-analysis | M (~5 files, ~200 LOC) | Phase 2 recommended |
| 7 | Research-Topic Restructure | Remove Python tool directory; rewrite SKILL.md with 3 parallel `context: fork` subagents | L (~20+ files, ~400 LOC net deletion) | None |

<!-- BEGIN PHASES -->

---

## Phase 1: Deprecations & Documentation Fixes

**Estimated Complexity:** S (~6 files, ~80 LOC)
**Dependencies:** None
**Parallelizable:** Yes (all six items touch different files)

### Goals

- Remove items fully covered by native Claude Code commands
- Add scope-disambiguation notes where custom skills overlap with native capabilities
- Clean up stale references in CLAUDE.md and marketplace.json

### Work Items

#### 1.1 Delete personal-plugin help skill
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: PENDING**
**Requirement Refs:** CS-1 Item 1 (modernization-requirements Phase 1)
**Files Affected:**
- `plugins/personal-plugin/skills/help/SKILL.md` (delete)
- `plugins/personal-plugin/skills/help/` directory (remove)

**Description:**
Native `/help` and `/skills` commands fully cover this skill's functionality. The existing skill uses a static hardcoded table that the skill itself flags as a maintenance burden. Delete the entire directory via `git rm -r`.

**Tasks:**
1. [ ] Run `git rm -r plugins/personal-plugin/skills/help/`
2. [ ] Search repo for references: `grep -r "skills/help" --include="*.md" --include="*.json"`
3. [ ] Verify `/skills` no longer lists it after reinstall

**Acceptance Criteria:**
- [ ] Directory removed; git status shows deletion
- [ ] No remaining references to `skills/help` in repo markdown or JSON
- [ ] Native `/help` and `/skills` work unchanged

**Notes:**
Git history preserves the file. No archiving needed.

---

#### 1.2 Delete bpmn-plugin help skill
**Status: PENDING**
**Requirement Refs:** CS-1 Item 2
**Files Affected:**
- `plugins/bpmn-plugin/skills/help/SKILL.md` (delete)
- `plugins/bpmn-plugin/skills/help/` directory (remove)

**Description:**
Same rationale as 1.1 — native `/help` and `/skills` cover this. The bpmn-plugin version has the same static-table code smell.

**Tasks:**
1. [ ] Run `git rm -r plugins/bpmn-plugin/skills/help/`
2. [ ] Verify no cross-references from bpmn-plugin docs

**Acceptance Criteria:**
- [ ] Directory removed; git status shows deletion
- [ ] `/skills` does not list bpmn-plugin help after reinstall

**Notes:**
—

---

#### 1.3 Deprecate review-pr command
**Status: PENDING**
**Requirement Refs:** CS-1 Item 3
**Files Affected:**
- `plugins/personal-plugin/commands/review-pr.md` (delete)
- `CLAUDE.md` (add deprecation note)

**Description:**
Native `/review` (local PR review) and `/ultrareview` (multi-agent cloud review) cover this command's use case. Delete the command file. Add a short note in the project CLAUDE.md pointing users to the native alternatives.

**Tasks:**
1. [ ] Run `git rm plugins/personal-plugin/commands/review-pr.md`
2. [ ] Edit `CLAUDE.md` under a new "## Deprecated" section: add line "`review-pr` (deprecated 2026-04-21) — use native `/review` for standard PR review or `/ultrareview` for multi-agent deep review"
3. [ ] Grep for `/review-pr` references in repo; update to point at native

**Acceptance Criteria:**
- [ ] Command file removed
- [ ] CLAUDE.md has one-line deprecation note with pointer to native alternatives
- [ ] No stale `/review-pr` references remain

**Notes:**
Decision: user confirmed deprecate (not keep with comparison matrix).

---

#### 1.4 Add scope note to security-analysis skill
**Status: PENDING**
**Requirement Refs:** CS-1 Item 4
**Files Affected:**
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify)

**Description:**
Add a "Comparison to `/security-review`" section near the top of the skill body (after description, before first phase). Explain that native `/security-review` covers pending changes (what you're about to commit), while this skill covers full-project static analysis + dependency audit + CVE verification. Include one-line routing guidance.

**Tasks:**
1. [ ] Read current `plugins/personal-plugin/skills/security-analysis/SKILL.md` to find insertion point after frontmatter
2. [ ] Insert "## Scope vs `/security-review`" section: ~100 words explaining the distinction and routing
3. [ ] Verify the note reads cleanly in context

**Acceptance Criteria:**
- [ ] Section added between frontmatter and first phase
- [ ] Reader can tell within 30 seconds which command to use for their situation

**Notes:**
Keep it short — this is disambiguation, not a tutorial.

---

#### 1.5 Add project-specific banner to evaluate-pipeline-output
**Status: PENDING**
**Requirement Refs:** CS-1 Item 5
**Files Affected:**
- `plugins/personal-plugin/skills/evaluate-pipeline-output/SKILL.md` (modify)

**Description:**
Add prominent banner at top of skill body (after description, before first phase): "**Scope:** Specialized for the contact-center-lab pipeline. Not generalizable without substantial rewrite. See LAB_NOTEBOOK.md in that project for pipeline schema." This makes the skill's narrow applicability obvious to users browsing the marketplace.

**Tasks:**
1. [ ] Edit skill file, insert scope banner after frontmatter
2. [ ] Verify banner renders prominently (bold + callout formatting)

**Acceptance Criteria:**
- [ ] Banner visible within first screen of the skill file
- [ ] User browsing `/skills` understands this isn't general-purpose

**Notes:**
Decision: user confirmed keep specialized with banner (not generalize, not move to local plugin).

---

#### 1.6 Clean up marketplace.json and CLAUDE.md references
**Status: PENDING**
**Requirement Refs:** CS-1 Item 6
**Files Affected:**
- `.claude-plugin/marketplace.json` (modify if references deleted items)
- `CLAUDE.md` (modify if references deleted items)
- `plugins/personal-plugin/.claude-plugin/plugin.json` (modify if references deleted items)
- `plugins/bpmn-plugin/.claude-plugin/plugin.json` (modify if references deleted items)

**Description:**
Search all top-level metadata and documentation for references to the deleted items (help skills from 1.1/1.2, review-pr command from 1.3). Update or remove stale references. Must run after items 1.1–1.3 to catch all references at once.

**Tasks:**
1. [ ] Grep: `grep -rn "help\|review-pr" .claude-plugin/ plugins/*/\.claude-plugin/ CLAUDE.md`
2. [ ] For each hit: determine if reference is to the deleted item or something else; update as needed
3. [ ] Verify `/plugin install` still works end-to-end

**Acceptance Criteria:**
- [ ] No marketplace.json or plugin.json entries reference deleted skill/command names
- [ ] Install instructions in CLAUDE.md remain accurate
- [ ] `/plugin marketplace add` and `/plugin install` succeed for both plugins

**Notes:**
This item should execute after 1.1/1.2/1.3 complete to catch all their references in one pass.

---

### Phase 1 Testing Requirements

- [ ] Reinstall both plugins and verify `/skills` and `/help` list expected (not deleted) items
- [ ] Grep confirms no dangling references to deleted items
- [ ] CLAUDE.md and README render cleanly

### Phase 1 Completion Checklist

- [ ] All 6 work items complete
- [ ] `git diff` shows only deletions + small doc additions
- [ ] No regressions in other skill/command behavior
- [ ] Commit message references CS-1 scope

---

## Phase 2: Scaffolding Generator Modernization

**Estimated Complexity:** M (~4 files, ~200 LOC)
**Dependencies:** None
**Parallelizable:** Yes (4 items touch different files)

### Goals

- Teach all three scaffolding commands (new-skill, new-command, scaffold-plugin) the modern frontmatter catalog
- Provide worked examples demonstrating each modern feature
- Document cross-cutting features in common-patterns.md "Advanced Features" section

### Work Items

#### 2.1 Modernize new-skill command
**Status: PENDING**
**Requirement Refs:** CS-2 Item 1
**Files Affected:**
- `plugins/personal-plugin/commands/new-skill.md` (modify; ~60 LOC added)

**Description:**
Expand the generated skill's frontmatter to include all modern fields as commented options: `context`, `agent`, `model`, `paths`, `isolation`, `when_to_use`, `hooks`, `shell`, plus existing `name`, `description`, `allowed-tools`, `effort`, `disable-model-invocation`, `argument-hint`. Add a "Frontmatter Field Reference" table in the command body explaining each. Add 3 worked examples at the bottom: (a) basic skill, (b) fork-to-Explore skill with `!`cmd`` dynamic context injection, (c) paths-activated skill with auto-trigger.

**Tasks:**
1. [ ] Read existing new-skill.md frontmatter template (lines 139–156)
2. [ ] Expand template with commented-out modern fields
3. [ ] Add Frontmatter Field Reference table after the template
4. [ ] Add 3 worked example skill bodies
5. [ ] Test: run `/new-skill test-skill` mentally — verify generated output teaches modern options

**Acceptance Criteria:**
- [ ] Template includes all 12+ frontmatter fields (as comments where optional)
- [ ] Field reference table documents syntax, purpose, when-to-use for each
- [ ] 3 worked examples show real usage patterns
- [ ] Output doc is < 500 lines

**Notes:**
—

---

#### 2.2 Modernize new-command command
**Status: PENDING**
**Requirement Refs:** CS-2 Item 2
**Files Affected:**
- `plugins/personal-plugin/commands/new-command.md` (modify; ~50 LOC added)

**Description:**
Same expansion as 2.1, adapted for commands (omit `name` per commands rule; commands can still use `context`, `agent`, `model`, `isolation`, `when_to_use`, `allowed-tools`, dynamic injection). Update the existing "9 pattern types" section to call out which patterns benefit from subagent isolation: orchestration pattern → `context: fork` + `isolation: worktree`; parallel-analysis pattern → multiple `context: fork` dispatches.

**Tasks:**
1. [ ] Read existing new-command.md (lines 183–193, 104–137)
2. [ ] Expand frontmatter field table with modern fields
3. [ ] Update pattern-type descriptions with subagent isolation callouts
4. [ ] Add worked example commands demonstrating modern patterns

**Acceptance Criteria:**
- [ ] Pattern types section maps each pattern to appropriate modern feature
- [ ] Frontmatter field coverage matches 2.1 (minus `name`)
- [ ] Generated commands benefit from modern dispatch patterns

**Notes:**
Critical: must not include `name` in command frontmatter — this breaks command discovery per CLAUDE.md.

---

#### 2.3 Modernize scaffold-plugin command
**Status: PENDING**
**Requirement Refs:** CS-2 Item 3
**Files Affected:**
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify; ~40 LOC)

**Description:**
Update the generated `plugin.json` example to current schema (verified). Remove the generated `help` skill template — native `/help` covers plugin-local help (cross-reference Phase 1 deletions). If scaffold-plugin is to generate any skill templates, ensure they use modern frontmatter.

**Tasks:**
1. [ ] Read scaffold-plugin.md (lines 153–166, 177–259)
2. [ ] Verify current `plugin.json` schema — ensure no stale fields (no `tools`, no `hooks` — per CLAUDE.md learnings)
3. [ ] Remove or modernize the generated help-skill template section
4. [ ] Add comment pointing scaffolded-plugin users at Phase 2.1/2.2's worked examples for skill/command creation

**Acceptance Criteria:**
- [ ] Generated plugin.json matches current schema
- [ ] No help-skill scaffolding (aligns with Phase 1 deprecation)
- [ ] New plugins scaffolded post-change are modern by default

**Notes:**
If user prefers scaffold-plugin to include an optional `--with-help` flag, consider keeping minimal help generation behind an off-by-default flag.

---

#### 2.4 Create Advanced Features section in common-patterns.md
**Status: PENDING**
**Requirement Refs:** CS-2 Item 4
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md` (modify; ~50 LOC added)

**Description:**
Add an "Advanced Features" section to common-patterns.md covering each modern frontmatter field and feature: `context: fork`, `agent:` selection, `model:` override, `paths:` glob patterns (with loop-guard warning), `isolation: worktree`, `when_to_use:` phrases, `hooks:` lifecycle, `shell:` selection, dynamic context injection (`!`cmd``), string substitution variables. Each sub-section: syntax, use case, gotchas. Keep under 200 total lines.

**Tasks:**
1. [ ] Read current common-patterns.md to determine insertion point
2. [ ] Draft Advanced Features section with one sub-entry per feature
3. [ ] Include gotchas: `paths:` loop-guard, `context: fork` loses conversation history, `!`cmd`` runs before Claude sees it
4. [ ] Cross-link from new-skill.md and new-command.md examples

**Acceptance Criteria:**
- [ ] Each modern feature documented (syntax + use case + gotcha)
- [ ] Section is scannable (tables or short blocks, not paragraphs)
- [ ] Total reference file stays under 300 lines

**Notes:**
This section becomes the canonical reference new-skill/new-command examples link to.

---

### Phase 2 Testing Requirements

- [ ] Scaffold a fresh test skill via `/new-skill` — verify frontmatter options and examples present
- [ ] Scaffold a fresh test command via `/new-command` — same
- [ ] Scaffold a test plugin via `/scaffold-plugin` — verify plugin.json is current and no help skill generated
- [ ] common-patterns.md "Advanced Features" section renders cleanly

### Phase 2 Completion Checklist

- [ ] All 4 work items complete
- [ ] Scaffolded test artifacts produce modern skill/command/plugin files
- [ ] No regression to existing scaffolded items (they remain untouched until per-skill modernization)

---

## Phase 3: Planning Workflow Modernization

**Estimated Complexity:** M (~5 files, ~150 LOC)
**Dependencies:** None
**Parallelizable:** Mostly (5 items touch different files; 3.5 touches plan-template consumed by 3.2 and 3.3 but only as a schema addition)

### Goals

- Route to native `/ultraplan` and `/batch` where appropriate
- Add per-phase `isolation: worktree` to implement-plan's subagent dispatch
- Add optional "Execution Mode" field to plan-template schema

### Work Items

#### 3.1 Add /ultraplan and /batch routing to plan-gate
**Status: PENDING**
**Requirement Refs:** CS-3 Item 1
**Files Affected:**
- `plugins/personal-plugin/skills/plan-gate/SKILL.md` (modify; ~40 LOC added)

**Description:**
Add two new paths to the routing decision tree (currently A–F): **Path B.5** routes to `/batch` when task naturally decomposes into 5–30 independent units (parallelization opportunity). **Path D.5** routes to `/ultraplan` when task needs >30-min planning or high-risk architectural decision. Add matching worked examples to the Examples section.

**Tasks:**
1. [ ] Read current routing tree (lines 180–209) and Examples (lines 211–251)
2. [ ] Insert Path B.5 after Path B with trigger criteria and routing logic
3. [ ] Insert Path D.5 after Path D with trigger criteria and routing logic
4. [ ] Add two Examples demonstrating B.5 and D.5 routing decisions
5. [ ] Update the decision flowchart diagram if present

**Acceptance Criteria:**
- [ ] Running `/plan-gate` on a 20-item parallel refactor list routes to B.5 (`/batch`)
- [ ] Running `/plan-gate` on a deep architectural decision routes to D.5 (`/ultraplan`)
- [ ] All 6 original paths (A–F) remain intact

**Notes:**
Preserve existing paths; additions are non-breaking.

---

#### 3.2 Add /ultraplan routing to create-plan
**Status: PENDING**
**Requirement Refs:** CS-3 Item 2
**Files Affected:**
- `plugins/personal-plugin/commands/create-plan.md` (modify; ~20 LOC)

**Description:**
Currently line 24 mentions `/ultra-plan` in "See also" but provides no routing condition. Upgrade to routing: at Phase 1.1 (document discovery, lines 49–71), add conditional — if discovered documents are vague, issue-heavy, or scope is ambiguous, suggest running `/ultraplan` first for pre-planning analysis. At Phase 5 output (lines 550–589), add to "Next Steps" a suggestion to use `/batch /implement-plan` when the generated plan has 6+ phases or 20+ total work items.

**Tasks:**
1. [ ] Read current Phase 1.1 and Phase 5 sections
2. [ ] Add routing conditional at Phase 1.1 with explicit trigger criteria
3. [ ] Update line 24 "See also" from "`/ultra-plan` for issue/bug lists" to describe routing
4. [ ] Add Next Steps guidance at Phase 5 for `/batch /implement-plan` on large plans

**Acceptance Criteria:**
- [ ] `/create-plan` on vague requirements suggests `/ultraplan` first
- [ ] Generated plans with 6+ phases include `/batch /implement-plan` suggestion in Next Steps
- [ ] Existing `/create-plan` workflow unchanged for simple cases

**Notes:**
—

---

#### 3.3 Add /batch guidance to plan-improvements
**Status: PENDING**
**Requirement Refs:** CS-3 Item 3
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify; ~15 LOC)

**Description:**
At Phase 1 intro (lines 34–48), add note: "If analysis yields 20+ independent improvement items, consider using `/batch` for parallel implementation rather than sequential `/implement-plan`. `/batch` automatically decomposes into 5–30 units with one background agent per unit in isolated worktrees."

**Tasks:**
1. [ ] Read Phase 1 intro section
2. [ ] Add guidance block at end of Phase 1 intro
3. [ ] Verify plan-improvements output still renders cleanly

**Acceptance Criteria:**
- [ ] Guidance present at Phase 1
- [ ] Users reviewing a large improvement list understand the `/batch` option

**Notes:**
—

---

#### 3.4 Inject worktree isolation into implement-plan subagent dispatches
**Status: PENDING**
**Requirement Refs:** CS-3 Item 4
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify; ~40 LOC)

**Description:**
At Step A1 (sequential implementation prompt, lines 339–349) and Step B1 (parallel implementation prompt, lines 457–470), inject the instruction: "For this phase, use `isolation: worktree phase-[PHASE_NUMBER]` so all work items in this phase share one isolated worktree. Merge to main branch on phase completion." Default to per-phase worktree (not per-item) — simpler coordination, matches phase-gate mental model.

**Tasks:**
1. [ ] Read Step A1 and Step B1 subagent prompts
2. [ ] Insert worktree isolation instruction at the top of each prompt (before "Complete ALL tasks")
3. [ ] Verify the prompt still reads coherently
4. [ ] Document the worktree-per-phase pattern in a new "Worktree Strategy" section

**Acceptance Criteria:**
- [ ] Subagent prompts include worktree instruction
- [ ] Phase boundary = merge point in the documented strategy
- [ ] Existing IMPLEMENTATION_PLAN.md files still execute (instruction is additive)

**Notes:**
Worktree strategy: per-phase (not per-item). Trade-off: per-phase means intra-phase parallel items share a tree; per-item means each item gets its own tree. Per-phase wins for coordination simplicity.

---

#### 3.5 Add Execution Mode field to plan-template
**Status: PENDING**
**Requirement Refs:** CS-3 Item 5
**Files Affected:**
- `plugins/personal-plugin/references/plan-template.md` (modify; ~20 LOC)

**Description:**
Add optional "Execution Mode" field to the Phase section template (after the "Parallelizable" line, around template line 47). Values: `Sequential | Parallel | Worktree-Isolated`. Add matching column to the Phase Summary Table schema (around line 34). Field is OPTIONAL — existing IMPLEMENTATION_PLAN.md files without it must still parse cleanly.

**Tasks:**
1. [ ] Read current Phase section template and Phase Summary Table schema
2. [ ] Add optional "Execution Mode" line after "Parallelizable"
3. [ ] Add "Execution Mode" column to Phase Summary Table
4. [ ] Update any Structural Rules or field-order notes
5. [ ] Verify existing plans (including this one) still parse

**Acceptance Criteria:**
- [ ] Field added as OPTIONAL with allowed values documented
- [ ] Existing plans without the field still parse in `/implement-plan`
- [ ] Column added to summary table

**Notes:**
Keep backward-compatible — don't make mandatory.

---

### Phase 3 Testing Requirements

- [ ] Run `/plan-gate` on synthetic inputs triggering each of the 8 paths (A, B, B.5, C, D, D.5, E, F) — verify correct routing
- [ ] Generate a test plan via `/create-plan` on vague requirements — verify `/ultraplan` suggestion appears
- [ ] Run `/implement-plan` on a simple test plan — verify subagent receives worktree instruction
- [ ] Parse existing plan files with new plan-template — verify no regressions

### Phase 3 Completion Checklist

- [ ] All 5 work items complete
- [ ] Plan-gate routing tree covers 8 paths
- [ ] Implement-plan spawned agents use worktree isolation
- [ ] Plan-template schema is backward-compatible

---

## Phase 4: Audit/Recon Consolidation + /schedule Integration

**Estimated Complexity:** L (~7 files, ~300 LOC)
**Dependencies:** None
**Parallelizable:** Yes (4.2 and 4.3 parallel; 4.4 covers both recon skills together; 4.1 must complete before 4.2–4.4 since they reference it)

### Goals

- Eliminate ~70% textual duplication between jetson-audit/spark-audit and between jetson-recon/spark-recon
- Extract shared five-check framework into a single reference file
- Add `/schedule` integration docs so users can automate periodic recon
- Add `paths:` auto-activation with explicit loop guard

### Work Items

#### 4.1 Create audit-recon-system reference file
**Status: PENDING**
**Requirement Refs:** CS-4 Item 1
**Files Affected:**
- `plugins/personal-plugin/references/patterns/audit-recon-system.md` (create; ~200 LOC)

**Description:**
Consolidate the shared five-check framework into a single reference. Sections: (1) Execution Framework (7 phases shared between audit and recon), (2) Shared Audit Five-Check Template (Config Drift, Missing Optimizations, Memory Budget, System Health, Version Currency) with generic structure (Purpose | Commands | Analysis | Return), (3) Shared Recon Five-Check Template with trigger-parsing logic, (4) Config Hooks — YAML anchors each skill supplies for machine-specific values (SSH target, baseline file, service/container names, ports, memory ceilings), (5) Severity matrices and cross-correlation logic, (6) LAB_NOTEBOOK entry templates (audit + recon flavors), (7) Web research patterns (when to use WebSearch vs WebFetch vs browser vs API endpoints).

**Tasks:**
1. [ ] Create `plugins/personal-plugin/references/patterns/` directory if missing
2. [ ] Draft Execution Framework section
3. [ ] Draft Audit Five-Check Template with generic field structure
4. [ ] Draft Recon Five-Check Template with trigger-parsing
5. [ ] Draft Config Hooks YAML anchor pattern with all 4 skills' field requirements
6. [ ] Draft shared severity/correlation/LAB_NOTEBOOK templates
7. [ ] Draft Web Research Patterns section

**Acceptance Criteria:**
- [ ] Reference file compiles all shared content from current 4 skills
- [ ] Config Hooks section accommodates machine-specific differences (Jetson systemctl vs Spark docker, Tegra thermals vs nvidia-smi)
- [ ] File under 300 LOC

**Notes:**
Must be completed before 4.2–4.4.

---

#### 4.2 Refactor jetson-audit skill
**Status: PENDING**
**Requirement Refs:** CS-4 Item 2
**Files Affected:**
- `plugins/personal-plugin/skills/jetson-audit/SKILL.md` (modify; net ~-100 LOC after consolidation)

**Description:**
Thin jetson-audit to a config layer plus reference pointer. Body structure: (1) frontmatter, (2) short description of what this skill does, (3) machine-config block (SSH target: `claude@jetson.k4jda.net`, baseline file: `JETSON_BASELINE.md`, device type: arm64-jetson-orin-nano, memory constraint: 8GB-unified, service: `myscript`, inference port: 8080, thermals path: `/sys/devices/virtual/thermal/thermal_zone*/temp`), (4) pointer: "Follow audit-recon-system.md Audit Five-Check Template using the config above," (5) machine-specific check commands (llama-server flag extraction via `ps aux | grep llama-server`, tegrastats, JetPack version, L4T/CUDA checks). Preserve every machine-specific nuance from current skill.

**Tasks:**
1. [ ] Read current jetson-audit/SKILL.md in full
2. [ ] Extract machine-specific values into YAML config block matching 4.1's anchor schema
3. [ ] Replace five Check sections with reference pointer + machine-specific commands only
4. [ ] Preserve specific commands: `ps aux | grep llama-server`, `cat /sys/devices/virtual/thermal/thermal_zone*/temp`, `tegrastats`, JetPack version checks
5. [ ] Run regression check: describe test target → compare output structure pre/post

**Acceptance Criteria:**
- [ ] SKILL.md is < 150 LOC (down from ~400+)
- [ ] Every machine-specific command preserved
- [ ] Regression test: skill output structure unchanged

**Notes:**
If the skill depends on LAB_NOTEBOOK.md entries from prior audits for baseline comparison, ensure that linkage remains explicit.

---

#### 4.3 Refactor spark-audit skill
**Status: PENDING**
**Requirement Refs:** CS-4 Item 3
**Files Affected:**
- `plugins/personal-plugin/skills/spark-audit/SKILL.md` (modify; net ~-100 LOC)

**Description:**
Same shape as 4.2 but with Spark-specific config: SSH target `claude@spark.k4jda.net`, baseline file `SPARK_BASELINE.md`, Docker-based container inspection (`docker inspect qwen35 --format '{{json .Config.Cmd}}'`), vLLM optimizations (FLASHINFER, prefix caching, VLLM env vars), nvidia-smi for GPU, 121.6 GiB GPU memory constraint, container health endpoints (8000/8001/8002). Preserve every Spark-specific detail.

**Tasks:**
1. [ ] Read current spark-audit/SKILL.md in full
2. [ ] Build YAML config block with Spark-specific values
3. [ ] Replace five Check sections with reference pointer + Spark-specific commands
4. [ ] Preserve: docker inspect commands, vLLM optimization checks, nvidia-smi driver/CUDA checks, container restart counts, dmesg errors
5. [ ] Run regression check against known Spark target

**Acceptance Criteria:**
- [ ] SKILL.md < 150 LOC
- [ ] All Spark-specific commands preserved
- [ ] Regression test passes

**Notes:**
—

---

#### 4.4 Refactor jetson-recon and spark-recon skills
**Status: PENDING**
**Requirement Refs:** CS-4 Item 4
**Files Affected:**
- `plugins/personal-plugin/skills/jetson-recon/SKILL.md` (modify; net ~-80 LOC)
- `plugins/personal-plugin/skills/spark-recon/SKILL.md` (modify; net ~-80 LOC)

**Description:**
Same consolidation shape as 4.2/4.3 but for recon skills. Each thins to config layer plus recon-specific sources: jetson-recon (NVIDIA developer/JetsonHacks releases, llama.cpp GitHub, HuggingFace small-model landscape, NVIDIA Jetson forum, live SSH health check), spark-recon (Arena leaderboard via spark-arena.com, vLLM GitHub, spark-vllm-docker/eugr builds, Qwen large-model landscape, DGX Spark Discourse forum JSON endpoints). Preserve trigger-matching logic (AND/OR boolean, version comparisons).

**Tasks:**
1. [ ] Read both recon SKILL.md files
2. [ ] Build YAML recon-sources config for each
3. [ ] Replace shared recon logic with reference pointer
4. [ ] Preserve: trigger-matching AND/OR logic, source-specific URL patterns, fallback strategies (browser → WebFetch → MCP)
5. [ ] Add "/schedule Integration" section at bottom with copy-pasteable registration command (e.g., `/schedule create --name jetson-recon-weekly --cron "0 23 * * 0" --skill jetson-recon`)

**Acceptance Criteria:**
- [ ] Both recon SKILL.md files < 150 LOC each
- [ ] Recon-source lists complete per skill
- [ ] `/schedule` registration docs present in each

**Notes:**
The `/schedule` command is native; this just adds docs and copy-pasteable triggers.

---

#### 4.5 Add Automation Schedule template to baseline docs
**Status: PENDING**
**Requirement Refs:** CS-4 Item 5
**Files Affected:**
- `plugins/personal-plugin/skills/jetson-audit/SKILL.md` (modify baseline template section)
- `plugins/personal-plugin/skills/spark-audit/SKILL.md` (modify baseline template section)

**Description:**
Each audit skill's body describes a template for initializing `JETSON_BASELINE.md` or `SPARK_BASELINE.md` if missing. Add an "Automation Schedule" table to those templates documenting recommended `/schedule` triggers (e.g., "audit weekly Tuesday 02:00 UTC | recon bi-weekly Sunday 23:00 UTC"). Users who initialize baselines post-change get scheduling guidance embedded.

**Tasks:**
1. [ ] Locate the baseline-template section in each audit skill
2. [ ] Add Automation Schedule table with Frequency | Recommended time | Notes columns
3. [ ] Verify the template section still generates valid markdown

**Acceptance Criteria:**
- [ ] Both audit skills' templates include Automation Schedule table
- [ ] Running the skill on a machine without baseline produces a baseline with schedule guidance

**Notes:**
—

---

#### 4.6 Add paths auto-activation with loop guard to audit skills
**Status: PENDING**
**Requirement Refs:** CS-4 Item 6
**Files Affected:**
- `plugins/personal-plugin/skills/jetson-audit/SKILL.md` (frontmatter + body; ~15 LOC)
- `plugins/personal-plugin/skills/spark-audit/SKILL.md` (frontmatter + body; ~15 LOC)
- `plugins/personal-plugin/skills/jetson-recon/SKILL.md` (frontmatter + body; ~15 LOC)
- `plugins/personal-plugin/skills/spark-recon/SKILL.md` (frontmatter + body; ~15 LOC)

**Description:**
Add `paths:` frontmatter trigger on changes to `JETSON_BASELINE.md` / `SPARK_BASELINE.md` / `*_CONFIG.md` files (scoped per skill). **Critical loop guard**: body of each skill MUST include a check at entry — "Before proceeding, check LAB_NOTEBOOK.md for an entry within last 5 minutes from this skill. If present, exit immediately (self-triggered re-entry likely)." Without loop guard, skill writes baseline → paths trigger → skill re-runs indefinitely.

**Tasks:**
1. [ ] Add `paths:` field to each skill's frontmatter (skill-specific patterns)
2. [ ] Insert loop-guard check at the very start of each skill body
3. [ ] Document bypass: user can invoke skill directly with `--force` flag to override guard
4. [ ] Test: touch baseline file → verify skill fires once, not infinitely

**Acceptance Criteria:**
- [ ] All 4 skills have `paths:` frontmatter with appropriate glob
- [ ] All 4 skills have loop-guard check at entry
- [ ] Touching baseline fires skill once; skill writing baseline does not re-fire
- [ ] `--force` flag bypasses guard (documented)

**Notes:**
Loop guard is the riskiest part of Phase 4. Test thoroughly before merge.

---

### Phase 4 Testing Requirements

- [ ] Run `/jetson-audit` against a test target — verify output structure matches pre-consolidation version
- [ ] Run `/spark-audit` — same
- [ ] Run `/jetson-recon` and `/spark-recon` — verify recon sources all reachable
- [ ] Touch a baseline file — verify paths trigger fires skill once, not infinitely
- [ ] Register a `/schedule` trigger from the skill docs — verify it activates

### Phase 4 Completion Checklist

- [ ] All 6 work items complete
- [ ] audit-recon-system.md reference is loaded correctly by all 4 skills
- [ ] ~70% LOC reduction in skill bodies verified
- [ ] Loop guard prevents infinite re-entry
- [ ] `/schedule` registration docs functional

---

## Phase 5: Analysis Skills Modernization

**Estimated Complexity:** M-L (~5 files, ~250 LOC)
**Dependencies:** Phase 2 recommended (for frontmatter patterns reference)
**Parallelizable:** Yes (5 items touch different skill files)

### Goals

- Apply `context: fork` + `agent:` dispatch to analysis-heavy phases
- Use dynamic context injection for static pre-loads (git stats, file lists)
- Add `isolation: worktree` where subagents write to shared disk paths
- Add missing `allowed-tools` frontmatter to skills currently unrestricted

### Work Items

#### 5.1 Modernize prime skill
**Status: PENDING**
**Requirement Refs:** CS-5 Item 1
**Files Affected:**
- `plugins/personal-plugin/skills/prime/SKILL.md` (modify; ~60 LOC)

**Description:**
Dispatch Phases 1, 3, 5 to `context: fork` + `agent: Explore` (these are read-only analysis phases that benefit from isolation). Replace inline git commands in Phase 2 (lines 66–78) with dynamic injection: `!`git log --oneline -20``, `!`git shortlog -sn --no-merges | head -10``, etc. Keep Phase 0 (lab notebook) and Phase 6 (recommendations) inline — they need main-conversation context. Update the opening instruction (line 35) to be prescriptive per-phase rather than a general hint.

**Tasks:**
1. [ ] Read current prime SKILL.md
2. [ ] Replace Phase 2 git command blocks with `!`cmd`` dynamic injection
3. [ ] Add explicit "This phase runs via context: fork + agent: Explore" directive at Phases 1/3/5 entry
4. [ ] Update line-35 general instruction to reference per-phase dispatch
5. [ ] Test: run `/prime` on the marketplace repo — verify output unchanged structurally

**Acceptance Criteria:**
- [ ] Phases 1/3/5 dispatch to Explore agent in isolated context
- [ ] Git commands run before Claude sees the prompt
- [ ] Phase 0 and 6 remain inline
- [ ] Output report structure matches pre-change version

**Notes:**
Report-synthesis step (Phase 6) must stay inline because it draws on all prior phase outputs.

---

#### 5.2 Modernize arch-review skill (explicit dispatch + worktree)
**Status: PENDING**
**Requirement Refs:** CS-5 Item 2
**Files Affected:**
- `plugins/personal-plugin/skills/arch-review/SKILL.md` (modify; ~50 LOC)

**Description:**
Modernization only — the skill's 9-agent Task dispatch already works. Changes: (1) In the agent-prompt template (lines 92–112), make `subagent_type` explicit per role: `solutions-architect`, `data-architect`, `integration-architect`, `software-engineer`, `performance-engineer`, `qa-architect`, `security-architect`, `platform-engineer`, `risk-compliance`. (2) Add `isolation: worktree` to each dispatched agent to prevent concurrent writes to `.meta.json`. (3) Convert intake.md disk-write-then-re-read pattern: write once to parent's scratch, pass content directly in each agent's prompt via `!`cat <path>/intake.md`` dynamic injection. (4) Replace mkdir bash calls with dynamic injection.

**Tasks:**
1. [ ] Read current arch-review SKILL.md (lines 88–126 especially)
2. [ ] Update agent-prompt template to include `subagent_type` field per agent
3. [ ] Add `isolation: worktree` line to each Task call's config
4. [ ] Convert intake-pass disk-write to dynamic injection for subagent prompts
5. [ ] Convert lines 38–44 (mkdir commands) to `!`cmd`` injection
6. [ ] Test end-to-end against a known project — compare output to pre-change

**Acceptance Criteria:**
- [ ] Each of 9 Task dispatches uses role-specific `subagent_type`
- [ ] No `.meta.json` write collisions during concurrent dispatch
- [ ] Intake content passed in subagent prompts (no disk-file re-read)
- [ ] Output executive summary matches pre-change structure/quality

**Notes:**
This is NOT a bug fix — skill works. Changes strictly improve isolation and dispatch precision.

---

#### 5.3 Modernize leak-risk-audit skill
**Status: PENDING**
**Requirement Refs:** CS-5 Item 3
**Files Affected:**
- `plugins/personal-plugin/skills/leak-risk-audit/SKILL.md` (modify; ~40 LOC)

**Description:**
Exercise the orphaned `Agent` permission (line 5 frontmatter declares it, nothing uses it). Dispatch scanning phases (Steps 3 and 4, lines 52–75) to `context: fork` subagents — one per severity tier (CRITICAL, HIGH, MEDIUM, LOW) for parallelism. Dynamic context injection for file inventory (`!`ls -la <dataset-path>``, `!`find <dataset-path> -type f -name '*.csv' -o -name '*.jsonl' | head -100``). Keep final Write operations (LEAK_RISK.md output) in the parent skill to avoid concurrent writes.

**Tasks:**
1. [ ] Read current leak-risk-audit SKILL.md
2. [ ] Restructure scanning procedure to dispatch 4 parallel subagents (one per severity tier)
3. [ ] Add dynamic injection for dataset inventory
4. [ ] Keep parent skill as aggregator/writer
5. [ ] Update Important Rules section to reflect new dispatch pattern

**Acceptance Criteria:**
- [ ] 4 parallel subagents dispatch for scanning
- [ ] Dataset inventory pre-loaded via dynamic injection
- [ ] Only parent writes LEAK_RISK.md (no concurrent write conflicts)
- [ ] Report output structure unchanged

**Notes:**
Python-via-Bash scanning can stay inside the subagents — each runs its tier's scan autonomously.

---

#### 5.4 Modernize explain-project skill
**Status: PENDING**
**Requirement Refs:** CS-5 Item 4
**Files Affected:**
- `plugins/personal-plugin/skills/explain-project/SKILL.md` (modify; ~60 LOC)

**Description:**
(1) Add missing `allowed-tools` frontmatter — currently unrestricted. Declare: `Read, Glob, Grep, Bash, Task`. (2) GitHub URL mode (lines 98–115): switch from `/tmp/explain-project-<name>` clone to `isolation: worktree`. Worktree auto-cleanup replaces manual cleanup. (3) Phase 1 deep analysis (lines 127–145) and Phase 3.5 verification (lines 303–315) dispatch to `context: fork` + `agent: Explore`. (4) Dynamic injection for git stats (`!`git log --oneline -20``, `!`git shortlog``).

**Tasks:**
1. [ ] Add `allowed-tools: Read, Glob, Grep, Bash, Task` to frontmatter
2. [ ] Replace /tmp clone logic with `isolation: worktree` for GitHub URL mode
3. [ ] Dispatch Phase 1 and Phase 3.5 to isolated Explore subagent
4. [ ] Replace bash git commands with dynamic injection
5. [ ] Test: run on a local project and a GitHub URL — verify both paths work

**Acceptance Criteria:**
- [ ] allowed-tools present and correct
- [ ] GitHub URL mode uses worktree (no /tmp artifacts)
- [ ] Phase 1 and 3.5 run in isolated context
- [ ] Both project modes (local + GitHub) produce equivalent output

**Notes:**
Worktree cleanup is automatic if no changes made — explain-project is read-only, so cleanup is safe.

---

#### 5.5 Modernize accessibility-annotator skill
**Status: PENDING**
**Requirement Refs:** CS-5 Item 5
**Files Affected:**
- `plugins/personal-plugin/skills/accessibility-annotator/SKILL.md` (modify; ~40 LOC)

**Description:**
(1) Add missing `allowed-tools` frontmatter — currently unrestricted. Declare: `Read, Write, Bash, Task`. (2) Phase 1 concept analysis (lines 78–212) — entire phase forks to `context: fork` + `agent: Explore`. (3) Phase 2 image generation (lines 267–304) dispatches one subagent per image for parallelism. (4) Retain Phase 2 document-skills:docx invocation in parent (cross-skill coupling should stay in main context).

**Tasks:**
1. [ ] Add `allowed-tools: Read, Write, Bash, Task` to frontmatter
2. [ ] Restructure Phase 1 to dispatch entire analysis to isolated Explore subagent
3. [ ] Restructure Phase 2 image step for per-image parallel dispatch
4. [ ] Preserve document-skills:docx invocation in parent
5. [ ] Test on a sample doc end-to-end

**Acceptance Criteria:**
- [ ] allowed-tools present
- [ ] Phase 1 analysis runs in isolated Explore context
- [ ] Image generation parallelizes across multiple subagents
- [ ] Final Word document output structure unchanged

**Notes:**
Image generation parallelism can cause Gemini API rate-limit issues; consider adding a simple concurrency limit (e.g., max 3 parallel image subagents).

---

### Phase 5 Testing Requirements

- [ ] Run `/prime` on marketplace repo — verify output unchanged
- [ ] Run `/arch-review` against a known test project — verify 9 agents dispatch with correct subagent_type and no .meta.json collisions
- [ ] Run `/leak-risk-audit` on a sample dataset — verify 4 parallel subagents dispatch
- [ ] Run `/explain-project` on both local path and GitHub URL — verify worktree used for URL mode
- [ ] Run `/accessibility-annotator` on a sample doc — verify Phase 1 dispatch and parallel images

### Phase 5 Completion Checklist

- [ ] All 5 work items complete
- [ ] Each skill end-to-end regression tested
- [ ] No skill produces degraded output vs pre-modernization
- [ ] allowed-tools declared where missing

---

## Phase 6: Ship Enhancement + Lab-Notebook Hook + Wiki paths

**Estimated Complexity:** M (~5 files, ~200 LOC)
**Dependencies:** Phase 2 recommended
**Parallelizable:** Mostly (6.1 isolated; 6.2 touches hooks.json + lab-notebook; 6.3 and 6.4 independent)

### Goals

- Speed up ship skill via dynamic context injection
- Add opt-in pre-commit hook enforcing lab-notebook Rule 11
- Enable `paths:` auto-activation for create-wiki and security-analysis

### Work Items

#### 6.1 Enhance ship skill with dynamic injection
**Status: PENDING**
**Requirement Refs:** CS-6 Item 1
**Files Affected:**
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify; ~30 LOC)

**Description:**
Replace inline git commands in pre-flight with dynamic context injection: `!`git status -s``, `!`git diff --stat``, `!`git remote -v``, `!`git branch --show-current``. Phase 3.1 LAB_NOTEBOOK gate reuses Phase 1 injected diff (no re-call). Optional enhancement: when injected diff shows >500 lines changed, suggest `/ultrareview` in the PR review step instead of standard review.

**Tasks:**
1. [ ] Read current ship/SKILL.md pre-flight (lines 60–63 area)
2. [ ] Replace bash git calls with `!`cmd`` injection at top of skill
3. [ ] Reuse injected diff in Phase 3.1 LAB_NOTEBOOK gate
4. [ ] Add diff-size check + `/ultrareview` suggestion in PR review step
5. [ ] Test: run dry-run → verify no redundant git calls

**Acceptance Criteria:**
- [ ] Git status and diff pre-loaded via injection
- [ ] Phase 3.1 reuses injected diff (not re-called)
- [ ] Large-diff PRs suggest `/ultrareview`

**Notes:**
Small perf win (~2-3s per run) but meaningful UX improvement.

---

#### 6.2 Add opt-in pre-commit hook for lab-notebook
**Status: PENDING**
**Requirement Refs:** CS-6 Item 2
**Files Affected:**
- `plugins/personal-plugin/hooks/hooks.json` (modify; +~15 LOC)
- `plugins/personal-plugin/hooks/scripts/lab-notebook-gate.sh` (create; ~30 LOC)
- `plugins/personal-plugin/skills/lab-notebook/SKILL.md` (modify; ~15 LOC)

**Description:**
Add `PreToolUse` hook matcher for `Bash(git commit*)` that runs `lab-notebook-gate.sh`. Script checks: (a) Does `LAB_NOTEBOOK.md` exist in the git root? If not → exit 0 (opt-in: no notebook, no enforcement). (b) Does the file have an entry dated within last 24h? If yes → exit 0. If no → print reminder, exit 1 (block commit). Update lab-notebook/SKILL.md with a "Pre-commit enforcement" section documenting the hook, opt-in behavior, and `git commit --no-verify` bypass.

**Tasks:**
1. [ ] Create `plugins/personal-plugin/hooks/scripts/` directory
2. [ ] Write `lab-notebook-gate.sh` with opt-in logic (no notebook → no enforcement)
3. [ ] Add PreToolUse entry to hooks.json (append, preserve existing SessionStart)
4. [ ] Update lab-notebook/SKILL.md with "Pre-commit enforcement" section
5. [ ] Test: in a project with stale notebook → commit blocked; in project without notebook → commit proceeds

**Acceptance Criteria:**
- [ ] Hook blocks commits in projects with stale LAB_NOTEBOOK.md
- [ ] Hook no-ops in projects without LAB_NOTEBOOK.md (opt-in)
- [ ] `git commit --no-verify` bypass documented
- [ ] Existing SessionStart hook unchanged

**Notes:**
Hook script must exit quickly (<1s) or it'll annoy users. Use `find` with `-newer` or `stat` mtime check, not full file parse.

---

#### 6.3 Add paths auto-activation to create-wiki
**Status: PENDING**
**Requirement Refs:** CS-6 Item 3
**Files Affected:**
- `plugins/personal-plugin/skills/create-wiki/SKILL.md` (modify; ~10 LOC)

**Description:**
Add `paths:` frontmatter triggering on changes to `wiki/sources/**/*`, `CLAUDE.md`, `LAB_NOTEBOOK.md`. When triggered, skill runs maintenance routine (update wiki pages from new source content) rather than full wiki initialization. Add body logic: if `wiki/` already exists, run maintenance; if not, run initialization (current behavior).

**Tasks:**
1. [ ] Add `paths:` field to frontmatter
2. [ ] Add entry-point conditional: if wiki/ exists → maintenance; else → initialization
3. [ ] Ensure maintenance mode is idempotent (running twice doesn't corrupt state)
4. [ ] Test: add file to wiki/sources/ → verify skill fires in maintenance mode

**Acceptance Criteria:**
- [ ] `paths:` present with appropriate globs
- [ ] Auto-trigger runs maintenance mode (not re-initialization)
- [ ] Idempotent

**Notes:**
Avoid triggering on every CLAUDE.md edit — may want to narrow to specific sections or require an annotation marker.

---

#### 6.4 Add paths auto-activation to security-analysis
**Status: PENDING**
**Requirement Refs:** CS-6 Item 4
**Files Affected:**
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify; ~10 LOC)

**Description:**
Add `paths:` frontmatter triggering on changes to dependency manifests: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `requirements.txt`, `Gemfile`. Auto-trigger declares intent to scan — but must still confirm with user before running a full security scan (scans are expensive). Add prompt-for-confirmation logic at entry.

**Tasks:**
1. [ ] Add `paths:` field to frontmatter
2. [ ] Add entry-point prompt: "Dependency manifest changed. Run security scan now? (y/n)"
3. [ ] Only proceed on explicit user confirmation
4. [ ] Test: edit a dependency file → verify confirmation prompt fires (not full scan)

**Acceptance Criteria:**
- [ ] `paths:` present with dependency file globs
- [ ] Auto-trigger prompts for confirmation (not direct scan)
- [ ] User can opt in or decline

**Notes:**
Aggressive auto-scanning on every dep change would be annoying; confirmation prompt is the right balance.

---

### Phase 6 Testing Requirements

- [ ] Run `/ship` on a small branch — verify git calls collapse to pre-flight injection
- [ ] Run `/ship` with >500-line diff — verify `/ultrareview` suggestion fires
- [ ] Commit in project with stale LAB_NOTEBOOK.md — verify hook blocks
- [ ] Commit in project without LAB_NOTEBOOK.md — verify hook no-ops
- [ ] Touch `wiki/sources/new.md` — verify create-wiki fires in maintenance mode
- [ ] Edit `package.json` — verify security-analysis prompts for scan

### Phase 6 Completion Checklist

- [ ] All 4 work items complete
- [ ] Hooks don't break any existing workflow
- [ ] `paths:` triggers don't create infinite loops
- [ ] Bypass mechanisms (--no-verify, decline prompt) work

---

## Phase 7: Research-Topic Restructure (Option A)

**Estimated Complexity:** L (~20+ files touched mostly via deletion, ~400 LOC net change)
**Dependencies:** None
**Parallelizable:** No (sequential: delete tool → rewrite skill → verify)

### Goals

- Remove Python research-orchestrator tool and all its dependencies
- Rewrite research-topic skill to dispatch 3 parallel `context: fork` subagents (one per LLM provider)
- Accept loss of real-time streaming progress (trade-off explicitly documented)

### Work Items

#### 7.1 Remove research-orchestrator Python tool
**Status: PENDING**
**Requirement Refs:** CS-7 Item 1
**Files Affected:**
- `plugins/personal-plugin/tools/research-orchestrator/` (delete entire directory, ~20 files)
- `CLAUDE.md` (modify; remove Python tool reference if present)
- Any other doc references to the Python tool

**Description:**
Delete the entire tool directory (src/, pyproject.toml, any docs) via `git rm -rf`. Grep repo for any references to the tool path or module name; remove or update. **Do not run this item until item 7.2 is complete and tested** — keep the Python tool in place as fallback until the new subagent dispatch is verified working.

**Tasks:**
1. [ ] Wait for 7.2 completion and verification
2. [ ] Run `git rm -rf plugins/personal-plugin/tools/research-orchestrator/`
3. [ ] Grep: `grep -rn "research-orchestrator\|research_orchestrator" . --include="*.md" --include="*.json"`
4. [ ] Clean up any stale references found
5. [ ] Verify `/research-topic` still works (now via subagents, not Python tool)

**Acceptance Criteria:**
- [ ] Directory removed
- [ ] No dangling references
- [ ] `/research-topic` end-to-end test passes using new subagent dispatch

**Notes:**
Order-sensitive: 7.2 MUST complete and verify before 7.1 runs. Git history preserves the deleted tool.

---

#### 7.2 Rewrite research-topic skill with 3 parallel context:fork subagents
**Status: PENDING**
**Requirement Refs:** CS-7 Item 2
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (rewrite; net ~-100 LOC after Python-tool removal)

**Description:**
Replace Python-tool invocation pattern with native subagent dispatch. New structure:
1. **Intake + clarification** (unchanged — ask user for research question, depth, etc.)
2. **Confirmation** with user (unchanged)
3. **Parallel dispatch:** three `context: fork` subagents, one per provider (Claude/OpenAI/Gemini). Each subagent's prompt contains: research question, depth level, provider-specific model name (from env var via `!`echo $ANTHROPIC_MODEL`` etc.), instruction to run provider-specific API call (via curl or SDK) and write synthesis to `reports/research-<provider>-<timestamp>.md`.
4. **Read outputs + cross-provider synthesis** (parent skill reads 3 files, synthesizes)
5. **Final unified report** written to `reports/research-<topic>-<timestamp>.md`
6. **Optional DOCX** via pandoc (if installed)

**Tasks:**
1. [ ] Read current research-topic/SKILL.md in full
2. [ ] Design new subagent prompts per provider (each must be self-contained with its API key env var, model, depth, output path)
3. [ ] Rewrite skill body: remove Python tool invocation (check-ready/check-models/execute steps), add 3 parallel Task dispatches
4. [ ] Add cross-provider synthesis step in parent (read 3 outputs, unified report)
5. [ ] Preserve pandoc DOCX step (keeps working)
6. [ ] Add explicit note: "Trade-off: no real-time streaming progress. For long runs (30+ min), watch agent-in-progress indicators."
7. [ ] Test against a known-quality query: compare output quality vs Python-tool baseline

**Acceptance Criteria:**
- [ ] 3 subagents dispatch in parallel
- [ ] Each subagent produces provider-specific synthesis file
- [ ] Parent produces unified cross-provider report
- [ ] DOCX option still works
- [ ] Output quality equivalent to (or better than) Python-tool baseline on test query

**Notes:**
Biggest risk in the plan. Test thoroughly before 7.1 deletes the fallback.

---

#### 7.3 Document trade-offs and test end-to-end
**Status: PENDING**
**Requirement Refs:** CS-7 Item 3
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (minor doc addition; ~15 LOC)

**Description:**
Add "Trade-offs vs Previous Implementation" section to skill body. Document: loss of real-time streaming progress; gained simpler architecture (no Python dependency), easier debugging, cross-platform portability. Include guidance: users expecting visibility on 30+ min runs should watch the in-progress agent indicators.

**Tasks:**
1. [ ] Write Trade-offs section
2. [ ] Run end-to-end test with a comprehensive research query (~15 min expected runtime)
3. [ ] Compare outputs (new vs Python-tool from a prior run if available)
4. [ ] Document any adjustment needed to subagent prompts based on output comparison

**Acceptance Criteria:**
- [ ] Trade-offs clearly documented
- [ ] End-to-end test passes
- [ ] Output quality validated

**Notes:**
This item is the verification gate before 7.1 can proceed.

---

### Phase 7 Testing Requirements

- [ ] Small query (brief depth, ~2 min) — verify 3 subagents dispatch correctly
- [ ] Standard query (~5 min) — verify synthesis is coherent
- [ ] Comprehensive query (~15–30 min) — verify end-to-end success and output quality
- [ ] DOCX generation step still works
- [ ] After 7.1: `/research-topic` runs without the Python tool directory

### Phase 7 Completion Checklist

- [ ] All 3 work items complete
- [ ] Python tool directory deleted
- [ ] Skill rewrite tested end-to-end at multiple depth levels
- [ ] Trade-offs documented

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2, 1.3, 1.4, 1.5 | All independent file touches |
| 1.6 | — | Must run after 1.1–1.3 complete to catch references |
| 2.1 | 2.2, 2.3 | Different command files |
| 2.4 | 2.1, 2.2, 2.3 | References file is separate from commands |
| 3.1 | 3.2, 3.3, 3.4, 3.5 | Different files; plan-template change is additive |
| 4.1 | — | Reference file must exist before 4.2–4.6 |
| 4.2 | 4.3 | Jetson and Spark audit are independent |
| 4.4 | 4.5, 4.6 | Recon refactor independent of Automation Schedule template and paths addition |
| 4.5 | 4.4 | Template addition is self-contained |
| 4.6 | 4.2, 4.3, 4.4 | Adds to files already being refactored — coordinate commits |
| 5.1 | 5.2, 5.3, 5.4, 5.5 | All independent skill files |
| 6.1 | 6.3, 6.4 | Ship, wiki, security-analysis are independent skills |
| 6.2 | 6.1, 6.3, 6.4 | Hook script + hooks.json are separate from skill bodies |
| 7.2 | — | Must complete before 7.1 (7.1 deletes fallback) |
| 7.3 | 7.2 | Verification runs concurrent with rewrite testing |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Deleting help skill breaks references | Low | Low | Phase 1.6 explicitly grep-and-clean before phase complete |
| Scaffolding changes confuse existing users | Low | Low | Modern fields are commented options, defaults unchanged |
| `/ultraplan`/`/batch` routing misfires | Medium | Low | Test routing with synthetic inputs per path; preserve fallback to existing paths |
| Worktree-per-phase in implement-plan causes merge issues | Medium | Medium | Test on small 2-phase plan first; document merge strategy |
| Audit/recon consolidation drops machine-specific nuance | Medium-High | High | Per-skill regression test output structure pre vs post; retain specific commands in config block |
| `paths:` auto-activation infinite loop | High (without guard) | High | Explicit 5-minute self-entry check in Phase 4.6; test by touching baseline |
| arch-review output changes surprise users | Medium | Medium | A/B test against known project before committing; keep old subagent_type fallback |
| Pre-commit hook blocks legitimate commits | Low (opt-in) | Medium | Opt-in: only activates if LAB_NOTEBOOK.md exists; `--no-verify` bypass |
| Research-topic rewrite produces degraded output | High | High | Do NOT delete Python tool until rewrite tested against known-quality baseline (7.1 waits for 7.2/7.3) |
| Worktree features require Claude Code version > user's | Low | Low | Document minimum version in CLAUDE.md; skills degrade gracefully if fields unrecognized |

---

## Success Metrics

- [ ] All 7 phases completed with acceptance criteria met
- [ ] 2 help skills deleted, 1 command deprecated, 3 disambiguation notes added
- [ ] Scaffolding generators teach 12+ modern frontmatter fields with worked examples
- [ ] Planning workflow has 8 routing paths (original 6 + B.5 + D.5); implement-plan uses worktree isolation
- [ ] Audit/recon skill bodies reduced ~70% via consolidation into shared reference; `/schedule` integration documented
- [ ] 5 analysis skills use `context: fork` dispatch and dynamic injection; arch-review has explicit `subagent_type` per role
- [ ] Ship uses dynamic injection (2–3s faster); lab-notebook pre-commit hook opt-in; wiki + security auto-activate on paths
- [ ] Research-topic works Python-free with 3 parallel subagent dispatch; output quality validated against baseline
- [ ] Net LOC change: ~+500 (new references/scaffolding) minus ~-1000 (consolidation/deletion) = ~-500 net reduction
- [ ] All marketplace install/validate tests pass post-change

---

## Appendix: Requirement Traceability

| Requirement | Source | Phase | Work Item |
|-------------|--------|-------|-----------|
| CS-1 Item 1: Delete personal-plugin help | modernization-requirements §CS-1 | 1 | 1.1 |
| CS-1 Item 2: Delete bpmn-plugin help | modernization-requirements §CS-1 | 1 | 1.2 |
| CS-1 Item 3: Deprecate review-pr | modernization-requirements §CS-1 | 1 | 1.3 |
| CS-1 Item 4: security-analysis scope note | modernization-requirements §CS-1 | 1 | 1.4 |
| CS-1 Item 5: evaluate-pipeline banner | modernization-requirements §CS-1 | 1 | 1.5 |
| CS-1 Item 6: Clean marketplace refs | modernization-requirements §CS-1 | 1 | 1.6 |
| CS-2 Item 1: Modernize new-skill | modernization-requirements §CS-2 | 2 | 2.1 |
| CS-2 Item 2: Modernize new-command | modernization-requirements §CS-2 | 2 | 2.2 |
| CS-2 Item 3: Modernize scaffold-plugin | modernization-requirements §CS-2 | 2 | 2.3 |
| CS-2 Item 4: Advanced Features section | modernization-requirements §CS-2 | 2 | 2.4 |
| CS-3 Item 1: plan-gate routing | modernization-requirements §CS-3 | 3 | 3.1 |
| CS-3 Item 2: create-plan `/ultraplan` routing | modernization-requirements §CS-3 | 3 | 3.2 |
| CS-3 Item 3: plan-improvements `/batch` guidance | modernization-requirements §CS-3 | 3 | 3.3 |
| CS-3 Item 4: implement-plan worktree | modernization-requirements §CS-3 | 3 | 3.4 |
| CS-3 Item 5: plan-template Execution Mode | modernization-requirements §CS-3 | 3 | 3.5 |
| CS-4 Item 1: Create audit-recon reference | modernization-requirements §CS-4 | 4 | 4.1 |
| CS-4 Item 2: Refactor jetson-audit | modernization-requirements §CS-4 | 4 | 4.2 |
| CS-4 Item 3: Refactor spark-audit | modernization-requirements §CS-4 | 4 | 4.3 |
| CS-4 Item 4: Refactor recon skills + /schedule | modernization-requirements §CS-4 | 4 | 4.4 |
| CS-4 Item 5: Automation Schedule template | modernization-requirements §CS-4 | 4 | 4.5 |
| CS-4 Item 6: paths auto-activation + loop guard | modernization-requirements §CS-4 | 4 | 4.6 |
| CS-5 Item 1: Modernize prime | modernization-requirements §CS-5 | 5 | 5.1 |
| CS-5 Item 2: Modernize arch-review | modernization-requirements §CS-5 | 5 | 5.2 |
| CS-5 Item 3: Modernize leak-risk-audit | modernization-requirements §CS-5 | 5 | 5.3 |
| CS-5 Item 4: Modernize explain-project | modernization-requirements §CS-5 | 5 | 5.4 |
| CS-5 Item 5: Modernize accessibility-annotator | modernization-requirements §CS-5 | 5 | 5.5 |
| CS-6 Item 1: Ship dynamic injection | modernization-requirements §CS-6 | 6 | 6.1 |
| CS-6 Item 2: Lab-notebook pre-commit hook | modernization-requirements §CS-6 | 6 | 6.2 |
| CS-6 Item 3: create-wiki paths | modernization-requirements §CS-6 | 6 | 6.3 |
| CS-6 Item 4: security-analysis paths | modernization-requirements §CS-6 | 6 | 6.4 |
| CS-7 Item 1: Remove research Python tool | modernization-requirements §CS-7 | 7 | 7.1 |
| CS-7 Item 2: Rewrite with 3 parallel subagents | modernization-requirements §CS-7 | 7 | 7.2 |
| CS-7 Item 3: Document trade-offs + test | modernization-requirements §CS-7 | 7 | 7.3 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-04-21 11:28:18*
*Source: /create-plan command (invoked via /ultra-plan Phase 5)*
