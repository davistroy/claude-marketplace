# Implementation Plan

**Generated:** 2026-04-30 16:45:00
**Based On:** Gap analysis (`gap-analysis-2026-04-30.md`) — ultra-plan skill vs. AI-native planning best practices (Spec Kit, Kiro, BMAD, Anthropic patterns). Ultra-plan Phase 1-4 analysis of all 13 recommended items across 3 priority tiers.
**Total Phases:** 6
**Estimated Total Effort:** ~880 LOC across ~16 files (10 modified, 6 new)

---

## Executive Summary

This plan upgrades the planning pipeline (ultra-plan, create-plan, plan-improvements, implement-plan, plan-template) to incorporate AI-native planning best practices identified in a gap analysis comparing the current system against Spec Kit, Amazon Kiro, BMAD v6, and Anthropic's own guidance. The 13 recommended items are grouped into 6 coherent change sets ordered by dependency: template enhancements first (foundation), then ultra-plan rewrite (core skill), then downstream consumer updates and extensions.

The most architecturally significant changes are: (1) adding EARS-notation acceptance criteria and a runnable Definition of Done to the shared plan template — making plans machine-verifiable rather than human-only; (2) rewriting ultra-plan with a new Phase 0 constitution check and optional sub-agent investigation for large item lists; (3) updating implement-plan to consume multiple verification commands instead of a single test command. The highest-risk change is the implement-plan state file schema evolution (Change Set D), mitigated by backward-compatible fallback logic.

Interrelated items are grouped into integrated change sets: Items 1+2 (EARS + DoD) are synergistic and share the plan template; Items 6+7 (constitution + sub-agents) both restructure ultra-plan's phases; Items 9+13 (ADR + branching) are complementary L3+/L4+ extensions. Each phase leaves the pipeline functional — no phase depends on a later phase to restore a working state.

---

## Plan Overview

Phases are ordered by the dependency graph from the interaction mapping analysis. Change Set B (anti-patterns) is independent and ships first as a quick win. Change Set A (template enhancements) is the foundation that Change Set D (consumer updates) builds on. Change Set C (ultra-plan rewrite) is the foundation that Change Set E (extensions) builds on. Change Set F (hooks, AGENTS.md) is independent and ships last.

The critical path is: Phase 1 → Phase 3 (template must land before consumer updates) and Phase 2 → Phase 4 (ultra-plan rewrite must land before extensions). Phases 1 and 2 can run in parallel. Phase 6 is fully independent.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|------------|------------------|-----------------|--------------|----------------|
| 1 | Plan Template Enhancements | EARS notation, runnable DoD, execution hints, unknowns register in plan-template.md | M (~2 files, ~150 LOC) | None | Sequential |
| 2 | Anti-Patterns Reference + Ultra-Plan Rewrite | New anti-patterns.md; ultra-plan Phase 0 constitution, sub-agent investigation, reference fixes | M-L (~5 files, ~280 LOC) | None | Sequential |
| 3 | Downstream Consumer Updates | create-plan and plan-improvements emit DoD and execution hints; implement-plan consumes them | M (~3 files, ~150 LOC) | Phase 1 | Sequential |
| 4 | Ultra-Plan Extensions | ADR generation (L3+), drift detection (--refresh), creative branching (L4+) | M (~2 files, ~200 LOC) | Phase 2 | Sequential |
| 5 | Implement-Plan Verification Upgrade | State file schema evolution, multi-command testing subagent, Lab Notebook action items A2-A4 | M (~1 file, ~100 LOC) | Phase 1, Phase 3 | Sequential |
| 6 | Hook Recipes + AGENTS.md | Optional hook examples, AGENTS.md companion template | S (~3 files, ~100 LOC) | None | Parallel |

### Milestones

| Milestone | Phases | Description |
|-----------|--------|-------------|
| Template Foundation | 1–2 | Plan template and ultra-plan skill upgraded with all gap-analysis patterns; pipeline functional with new sections |
| Pipeline Integration | 3–5 | All consumers (create-plan, plan-improvements, implement-plan) updated to generate and consume new template sections |
| Polish | 6 | Optional reference files for hooks and cross-tool compatibility |

<!-- BEGIN PHASES -->

---

## Phase 1: Plan Template Enhancements

**Estimated Complexity:** M (~2 files, ~150 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Add EARS-notation guidance and examples to acceptance criteria (Item 1)
- Add runnable Definition of Done section to each phase (Item 2)
- Add Execution Hints section to plan header area (Item 3)
- Add Unknowns Register alongside Risk Mitigation (Item 5)
- Update structural rules to cover new sections

### Work Items

#### 1.1 Add EARS-Notation Acceptance Criteria Guidance ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis C2, §4.1 — EARS notation from Kiro
**Files Affected:**
- `plugins/personal-plugin/references/plan-template.md` (modify)

**Description:**
Update the acceptance criteria field in the plan template to include EARS (Easy Approach to Requirements Syntax) notation guidance and examples. The current template uses freeform `[Measurable criterion]` placeholders. EARS format — `WHEN [event] THEN [system] SHALL [action]` — makes criteria unambiguous and directly translatable to test assertions. Not all criteria need EARS (binary criteria like "coverage ≥80%" remain as-is), but behavioral criteria should use the notation.

**Tasks:**
1. [ ] In `plan-template.md`, update the Acceptance Criteria field within the work item template to include EARS notation guidance and 2-3 examples
2. [ ] Add a brief note that binary/threshold criteria (coverage, lint clean, no TODOs) don't need EARS — only behavioral criteria
3. [ ] Add a structural rule (rule 13) documenting the EARS convention as recommended-not-required
4. [ ] Update the ultra-plan SKILL.md Phase 3 (now Phase 4 after rewrite in Phase 2) verification criteria to mention EARS notation for behavioral criteria

**Acceptance Criteria:**
- [ ] WHEN a plan is generated using the template THEN acceptance criteria for behavioral requirements SHALL use EARS notation (`WHEN ... THEN ... SHALL`)
- [ ] WHEN a criterion is binary or threshold-based THEN the criterion SHALL remain in simple checkbox format without EARS
- [ ] Template backward compatibility preserved — existing plans without EARS still parse correctly

**Notes:**
The EARS guidance goes in the template example section (around line 86-89). Keep it concise — 3-5 lines of guidance + 2 examples.

---

#### 1.2 Add Runnable Definition of Done Section ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis C3 — Verification Harness
**Depends On:** 1.1
**Files Affected:**
- `plugins/personal-plugin/references/plan-template.md` (modify)

**Description:**
Add a `## Definition of Done (Runnable)` section to the per-phase template, positioned after the Completion Checklist. This section contains actual shell commands that downstream `/implement-plan` can execute to verify phase completion. Commands are populated by the plan generators (create-plan, plan-improvements) based on detected project infrastructure — the template provides the structure and placeholder examples.

**Tasks:**
1. [ ] Add `## Definition of Done (Runnable)` section after each phase's Completion Checklist in the template
2. [ ] Include placeholder command slots: test command, lint command, typecheck command, coverage command, custom project-specific checks
3. [ ] Add a `pass_criteria` field per command (e.g., "exit code 0", "coverage ≥ 80%")
4. [ ] Add structural rule (rule 14) documenting the DoD section format and that it's optional for backward compatibility
5. [ ] Add DoD markers: `<!-- BEGIN DOD -->` and `<!-- END DOD -->` to bracket the section for machine parsing

**Acceptance Criteria:**
- [ ] WHEN a plan phase includes a DoD section THEN each entry SHALL have a `command` and `pass_criteria` field
- [ ] WHEN a plan is generated without DoD data (e.g., no test infrastructure detected) THEN the DoD section SHALL be omitted rather than populated with placeholders
- [ ] Existing plans without DoD sections parse and execute correctly (backward compat)

**Notes:**
DoD section format:
```markdown
### Definition of Done (Runnable)
<!-- BEGIN DOD -->
| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check src/` | Exit code 0 |
| Types | `mypy src/` | Exit code 0 |
| Coverage | `pytest --cov=src/ --cov-fail-under=80` | ≥80% on changed files |
<!-- END DOD -->
```

---

#### 1.3 Add Execution Hints Section ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis H2 — Context-budget and model-tier directives
**Files Affected:**
- `plugins/personal-plugin/references/plan-template.md` (modify)

**Description:**
Add an `## Execution Hints` section to the plan-level template (between Phase Summary Table and `<!-- BEGIN PHASES -->`). This section provides directives for downstream `/implement-plan`: suggested model tier per phase, context budget guidance, subagent grouping recommendations, and optional hook hints. The Agent tool supports a `model` parameter (`sonnet`, `opus`, `haiku`), making model-tier hints mechanically enforceable.

**Tasks:**
1. [ ] Add `## Execution Hints` section to the plan template between Phase Summary Table and Milestones
2. [ ] Include fields: `Model Tier` (per phase or default), `Context Budget` (tokens per subagent), `Parallelization Notes`, `Hook Hints` (optional)
3. [ ] Add structural rule (rule 15) documenting execution hints format
4. [ ] Document that hints are advisory by default but model tier can be enforced via Agent tool's `model` parameter

**Acceptance Criteria:**
- [ ] WHEN a plan includes execution hints THEN the model tier field SHALL use valid Agent tool model values (`sonnet`, `opus`, `haiku`)
- [ ] WHEN implement-plan reads a plan with execution hints THEN it SHOULD use the suggested model tier for subagent invocations (implementation in Phase 5)
- [ ] Plans without execution hints section work exactly as before

---

#### 1.4 Add Unknowns Register ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis H1 — Risk & Unknowns Register
**Files Affected:**
- `plugins/personal-plugin/references/plan-template.md` (modify)

**Description:**
Add an `## Unknowns Register` section alongside the existing Risk Mitigation table. Unknowns (epistemic uncertainty — things we don't know yet) are categorically different from risks (probabilistic — things that could go wrong). The unknowns register tracks items that need resolution before or during implementation, with severity classification and resolution strategies. High-severity unknowns should be resolved before the affected phase begins.

**Tasks:**
1. [ ] Add `## Unknowns Register` section between Risk Mitigation and Success Metrics in the template
2. [ ] Table columns: ID, Unknown, Severity (High/Medium/Low), Affects (phase/item refs), Resolution Strategy, Status (Open/Resolved)
3. [ ] Add guidance note: High-severity unknowns should be resolved before the affected phase starts
4. [ ] Place inside `<!-- BEGIN TABLES -->` / `<!-- END TABLES -->` markers
5. [ ] Add structural rule (rule 16) documenting unknowns register format and status values

**Acceptance Criteria:**
- [ ] WHEN a plan identifies unknowns during generation THEN they SHALL appear in the Unknowns Register, not the Risk Mitigation table
- [ ] WHEN an unknown has Severity: High THEN it SHALL reference the specific phase/item it affects
- [ ] Plans without unknowns register parse and execute correctly (backward compat)

---

### Phase 1 Testing Requirements

- [ ] Read the updated plan-template.md and verify all 4 new sections are syntactically correct markdown
- [ ] Verify structural rules count is updated (was 12, now 16)
- [ ] Verify `<!-- BEGIN/END -->` markers are properly nested
- [ ] Verify existing plan structure (from v6 archive) would still parse correctly with the new template

### Phase 1 Completion Checklist

- [ ] All work items complete
- [ ] plan-template.md has 4 new sections with correct marker placement
- [ ] Structural rules updated from 12 to 16
- [ ] No regressions to existing template structure
- [ ] ultra-plan SKILL.md updated with EARS reference (1.1 task 4)

---

## Phase 2: Anti-Patterns Reference + Ultra-Plan Rewrite

**Estimated Complexity:** M-L (~5 files, ~280 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Create shared anti-patterns reference file (Item 4)
- Add Phase 0 constitution check to ultra-plan (Item 6)
- Add sub-agent investigation guidance for large item lists (Item 7)
- Fix `/ultraplan` vs `/ultra-plan` reference ambiguity (Item 11 fix)
- Add `allowed-tools` to ultra-plan frontmatter

### Work Items

#### 2.1 Create Shared Anti-Patterns Reference ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis N2 — Anti-pattern catalog expansion
**Files Affected:**
- `plugins/personal-plugin/references/anti-patterns.md` (create)
- `plugins/personal-plugin/references/common-patterns.md` (modify)
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**
Extract the 4 inline anti-patterns from ultra-plan Phase 3 into a shared `references/anti-patterns.md` file. Expand the catalog to 11+ items organized by category (Planning, Implementation, Verification), drawing from the gap analysis's recommended additions. Update ultra-plan Phase 3 to reference the shared file. Add index entry to common-patterns.md.

**Tasks:**
1. [ ] Create `references/anti-patterns.md` with three categories: Planning Anti-Patterns, Implementation Anti-Patterns, Verification Anti-Patterns
2. [ ] Include existing 4 from ultra-plan Phase 3: symptom patching, cross-item conflicts, scope creep, implicit dependencies
3. [ ] Add 7 new from gap analysis: TBD/placeholder pollution, claiming tests pass without running, vague file references, mid-plan scope additions without re-running discovery, freeform untestable acceptance criteria, self-review without running verification, generating tasks referencing undefined symbols
4. [ ] Each anti-pattern: name, description (1-2 sentences), detection heuristic (how to spot it), mitigation (how to prevent it)
5. [ ] Update `common-patterns.md` to add anti-patterns.md to the pattern file index
6. [ ] Update ultra-plan SKILL.md Phase 3 anti-patterns section: keep the section header and a one-line summary per pattern, add "See `references/anti-patterns.md` for the full catalog with detection heuristics"

**Acceptance Criteria:**
- [ ] WHEN a planning command references anti-patterns THEN it SHALL point to `references/anti-patterns.md` as the canonical source
- [ ] Anti-patterns file has ≥11 entries across 3 categories
- [ ] Each entry has all 4 fields: name, description, detection heuristic, mitigation
- [ ] common-patterns.md index is consistent with the new file

---

#### 2.2 Add Phase 0: Constitution Check to Ultra-Plan ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis C1 — Constitution / Project-Rules phase
**Depends On:** 2.1
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**
Add a new Phase 0 to ultra-plan that checks for project-wide non-negotiable constraints before investigation begins. Phase 0 reads CLAUDE.md and any `constitution.md` for existing project constraints. If no constraints are documented, it runs a brief 5-7 question interview to establish: test policy, deployment target, stack constraints, security non-negotiables, observability minimum, definition-of-done baseline, and data sovereignty posture. Results are recorded in the Summary Report (Phase 5 after renumber) and used as gates for the Solution Design phase.

This is NOT a separate `constitution.md` file — for solo-builder context, project constraints live in CLAUDE.md. Phase 0 reads what's there and fills gaps via interview.

**Tasks:**
1. [ ] Add Phase 0 section before current Phase 1 in ultra-plan SKILL.md
2. [ ] Phase 0 logic: read CLAUDE.md for existing constraints (test policy, deployment, stack, security, etc.). If constraints are comprehensive, note them and proceed. If gaps exist, ask 5-7 targeted questions to fill them.
3. [ ] Define the 7 constraint categories: test policy, deployment target, stack lock-in, security non-negotiables, observability minimum, definition-of-done baseline, data sovereignty
4. [ ] Add a "Pre-Plan Gates" output: a checklist at the top of the Summary Report that verifies the plan complies with each documented constraint
5. [ ] Add skip logic: if the user says "skip constitution" or the task is clearly small-scope (L0-L1 per plan-gate), skip Phase 0 entirely
6. [ ] Renumber all subsequent phases: Phase 1→2, Phase 2→3, Phase 3→4, Phase 4→5, Phase 5→6

**Acceptance Criteria:**
- [ ] WHEN ultra-plan is invoked on a project with a comprehensive CLAUDE.md THEN Phase 0 SHALL extract constraints without asking questions
- [ ] WHEN ultra-plan is invoked on a project with no documented constraints THEN Phase 0 SHALL ask ≤7 targeted questions
- [ ] WHEN a user says "skip constitution" or the task is L0-L1 scope THEN Phase 0 SHALL be skipped
- [ ] Summary Report includes Pre-Plan Gates checklist verifying compliance with documented constraints

---

#### 2.3 Add Sub-Agent Investigation Guidance ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis H7 — Formalize parallel research agents
**Depends On:** 2.2
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**
Add guidance to ultra-plan Phase 1 (now Phase 2 after renumber) for using the Agent tool with `subagent_type: Explore` when investigating large item lists (>5 items). For smaller lists, keep inline investigation as the default. Sub-agents return structured summaries that feed Phase 3 (Interaction Mapping). This preserves main context for the high-value Phases 4-6 (Solution Design, Summary Report, Plan Generation).

**Tasks:**
1. [ ] Add a decision gate at the start of Phase 2 (Investigation): "If the input contains >5 items, spawn Explore sub-agents for codebase investigation. Otherwise, investigate inline."
2. [ ] Define the sub-agent prompt template: read specific files, trace data flows, return structured findings (Item, Root Cause, Blast Radius, Current Behavior, Expected Behavior, Preserved Assumptions, Risk)
3. [ ] Add guidance: launch sub-agents in parallel (one per item or grouped by related items), collect results, then proceed to Phase 3 inline
4. [ ] Add graceful degradation: if Agent tool is unavailable or sub-agents fail, fall back to inline investigation
5. [ ] Update ultra-plan frontmatter to add `allowed-tools: Read, Glob, Grep, Agent`

**Acceptance Criteria:**
- [ ] WHEN ultra-plan is invoked with >5 items THEN Phase 2 SHALL spawn Explore sub-agents for investigation
- [ ] WHEN ultra-plan is invoked with ≤5 items THEN Phase 2 SHALL investigate inline (current behavior)
- [ ] WHEN Agent tool is unavailable THEN investigation SHALL fall back to inline mode
- [ ] Sub-agent results follow the same structured format as inline investigation findings

---

#### 2.4 Fix Ultra-Plan Reference Ambiguity ✅ Completed 2026-04-30
**Status: COMPLETE [2026-04-30]**
**Requirement Refs:** Gap Analysis N8 — Rename consideration (reference fix only)
**Files Affected:**
- `plugins/personal-plugin/skills/plan-gate/SKILL.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Fix the ambiguous references to `/ultraplan` (no hyphen) in plan-gate and create-plan. Currently, plan-gate Path D.5 says "Recommended: /ultraplan" and create-plan's pre-planning quality gate says "Run `/ultraplan` first." The personal-plugin skill is named `/ultra-plan` (with hyphen). These references may be misrouted to Anthropic's built-in `/ultraplan` instead. Clarify that the personal-plugin skill is `/ultra-plan` and add a note distinguishing it from Anthropic's built-in.

**Tasks:**
1. [x] In plan-gate SKILL.md Path D.5: change `/ultraplan` references to `/ultra-plan`. Add a one-line note: "Note: `/ultra-plan` is the personal-plugin deep pre-planning skill. Anthropic's built-in `/ultraplan` (no hyphen) is a distinct cloud planning feature."
2. [x] In create-plan.md pre-planning quality gate: change `/ultraplan` references to `/ultra-plan`. Same disambiguation note.
3. [x] In ultra-plan SKILL.md "See also" line: verify it correctly references `/create-plan` and `/plan-improvements` (currently correct)
4. [x] Grep for any other `/ultraplan` references in the codebase and fix them

**Acceptance Criteria:**
- [x] WHEN plan-gate routes to the deep pre-planning skill THEN it SHALL reference `/ultra-plan` (with hyphen)
- [x] WHEN create-plan suggests pre-planning THEN it SHALL reference `/ultra-plan` (with hyphen)
- [x] No ambiguous `/ultraplan` references remain in personal-plugin files (excluding references to Anthropic's built-in in disambiguation notes)

---

### Phase 2 Testing Requirements

- [ ] Ultra-plan SKILL.md has 7 phases (0-6) with correct numbering and gate logic
- [ ] Anti-patterns reference has ≥11 entries with all required fields
- [ ] Plan-gate and create-plan reference `/ultra-plan` (with hyphen) consistently
- [ ] Ultra-plan frontmatter includes `allowed-tools: Read, Glob, Grep, Agent`
- [ ] Grep for `/ultraplan` in personal-plugin — only in disambiguation notes

### Phase 2 Completion Checklist

- [ ] All work items complete
- [ ] Ultra-plan rewrite tested with a simple invocation
- [ ] Anti-patterns file indexed in common-patterns.md
- [ ] Reference ambiguity resolved across all files
- [ ] No regressions to plan-gate routing

---

## Phase 3: Downstream Consumer Updates

**Estimated Complexity:** M (~3 files, ~150 LOC)
**Dependencies:** Phase 1 (template enhancements must be in place)
**Execution Mode:** Sequential

### Goals

- Update create-plan to generate DoD sections and execution hints (Items 2↓, 3↓)
- Update plan-improvements to generate DoD sections and execution hints (Items 2↓, 3↓)
- Update ultra-plan Phase 4 (Solution Design) and Phase 5 (Summary Report) to include unknowns alongside risks (Item 5↓)

### Work Items

#### 3.1 Update Create-Plan to Generate DoD and Execution Hints
**Status: PENDING**
**Requirement Refs:** Gap Analysis C3↓, H2↓ — consumer-side of template enhancements
**Files Affected:**
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Update create-plan to populate the new template sections. Phase 1.5 (Codebase Reconnaissance) already detects test infrastructure — extend it to capture lint, typecheck, and coverage commands. Phase 4 (Generate Plan) emits the DoD section with captured commands. Phase 3 (Phase Planning) emits execution hints based on phase complexity.

**Tasks:**
1. [ ] Extend Phase 1.5.2 (Test & CI/CD Infrastructure): after detecting test framework, also detect lint command (`ruff`, `eslint`, `flake8`), typecheck command (`mypy`, `tsc --noEmit`, `pyright`), coverage command (from config files), and any custom verification scripts
2. [ ] Add the detected commands to the Codebase Reconnaissance Results output
3. [ ] In Phase 4 (Generate Plan): for each phase, emit a `### Definition of Done (Runnable)` section populated with the detected verification commands
4. [ ] In Phase 3 (Phase Planning): emit an `## Execution Hints` section with model tier suggestions (Opus for L-complexity phases, Sonnet for S-M phases) and context budget per phase based on work item count
5. [ ] In Phase 2 (Requirements Analysis): when flagging unknowns or ambiguities, capture them for the Unknowns Register instead of only the Risk Mitigation table

**Acceptance Criteria:**
- [ ] WHEN create-plan detects test infrastructure THEN the generated plan SHALL include a DoD section per phase with runnable commands
- [ ] WHEN create-plan generates a plan with L-complexity phases THEN execution hints SHALL suggest Opus model tier for those phases
- [ ] WHEN requirements analysis identifies unknowns THEN they SHALL appear in the Unknowns Register, not the Risk Mitigation table

---

#### 3.2 Update Plan-Improvements to Generate DoD and Execution Hints
**Status: PENDING**
**Requirement Refs:** Gap Analysis C3↓, H2↓ — consumer-side of template enhancements
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Update plan-improvements to populate the new template sections. Phase 1 (Deep Analysis) already scans test infrastructure — extend it to capture all verification commands. Phase 3 (Generate Plan) emits DoD and execution hints. Phase 1 unknowns go to the Unknowns Register.

**Tasks:**
1. [ ] Extend Phase 1 Deep Analysis: in the "CI/CD Pipeline" assessment section, add explicit detection of lint, typecheck, and coverage commands alongside the existing test framework detection
2. [ ] In Phase 3 (Generate Plan): emit `### Definition of Done (Runnable)` per phase and `## Execution Hints` at plan level, following the same pattern as create-plan (3.1)
3. [ ] In Phase 1 analysis: when analysis identifies unknowns or unresolvable questions, capture them for the Unknowns Register

**Acceptance Criteria:**
- [ ] WHEN plan-improvements detects verification infrastructure THEN the generated plan SHALL include DoD sections
- [ ] WHEN plan-improvements generates execution hints THEN model tier suggestions SHALL match phase complexity
- [ ] Unknowns from analysis appear in Unknowns Register

---

#### 3.3 Update Ultra-Plan Solution Design and Summary Report
**Status: PENDING**
**Requirement Refs:** Gap Analysis H1↓, C3↓ — ultra-plan consuming new template sections
**Depends On:** 3.1
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**
Update ultra-plan's Solution Design (Phase 4 after renumber) and Summary Report (Phase 5 after renumber) to produce unknowns alongside risks, and to specify verification commands per change set that feed into the DoD section when the plan is generated via create-plan.

**Tasks:**
1. [ ] In Phase 4 (Solution Design): add "Verification commands" to the per-change-set specification — what commands confirm the change works (not just freeform criteria, but actual runnable commands when applicable)
2. [ ] In Phase 5 (Summary Report): add "### Unknowns" section alongside the existing "### Risk Assessment" — unknowns that need resolution before or during implementation
3. [ ] In Phase 5 (Summary Report): add "### Verification Commands" section listing all commands from Phase 4 that should be included in the plan's DoD
4. [ ] In Phase 6 (Plan Generation): map unknowns → Unknowns Register and verification commands → DoD section when feeding analysis to create-plan

**Acceptance Criteria:**
- [ ] WHEN ultra-plan identifies unknowns THEN they SHALL appear in the Summary Report's Unknowns section, separate from risks
- [ ] WHEN ultra-plan specifies verification commands per change set THEN they SHALL be mapped to the plan's DoD section in Phase 6

---

### Phase 3 Testing Requirements

- [ ] Read updated create-plan.md and verify DoD generation logic is present in Phase 4
- [ ] Read updated plan-improvements.md and verify DoD generation logic is present in Phase 3
- [ ] Read updated ultra-plan SKILL.md and verify unknowns + verification commands in Phases 4-6
- [ ] Verify all three files reference the plan-template.md DoD format consistently

### Phase 3 Completion Checklist

- [ ] All work items complete
- [ ] create-plan generates DoD sections
- [ ] plan-improvements generates DoD sections
- [ ] ultra-plan produces unknowns and verification commands
- [ ] No regressions to existing plan generation

---

## Phase 4: Ultra-Plan Extensions

**Estimated Complexity:** M (~2 files, ~200 LOC)
**Dependencies:** Phase 2 (ultra-plan rewrite must be complete)
**Execution Mode:** Sequential

### Goals

- Add ADR generation for L3+ tasks (Item 9)
- Add drift detection `--refresh` mode (Item 8)
- Add creative branching for L4+ tasks (Item 13)

### Work Items

#### 4.1 Add ADR Generation for L3+ Tasks
**Status: PENDING**
**Requirement Refs:** Gap Analysis H4 — Architecture Decision Records
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)
- `plugins/personal-plugin/references/adr-template.md` (create)

**Description:**
Add conditional ADR generation to ultra-plan's Solution Design phase. When the task involves significant architectural decisions (L3+ complexity per plan-gate classification), ultra-plan generates ADR files in `docs/adr/` using the standard format. ADR generation is triggered by a question in Phase 4: "Does this change set involve an architectural decision that should outlive the plan?" If yes, generate an ADR. The ADR template follows the standard: Title, Status (Proposed), Context, Decision, Consequences, Alternatives Considered.

**Tasks:**
1. [ ] Create `references/adr-template.md` with standard ADR format: Title, Date, Status (Proposed/Accepted/Deprecated/Superseded), Context, Decision, Consequences, Alternatives Considered
2. [ ] In ultra-plan Phase 4 (Solution Design): add a conditional check — "For each change set that involves choosing between fundamentally different approaches, flag it for ADR generation"
3. [ ] Add ADR generation step: create `docs/adr/ADR-NNNN-[slug].md` from the template, populated with the decision context from Phase 4
4. [ ] In Phase 5 (Summary Report): list generated ADRs with status
5. [ ] Add skip logic: only generate ADRs when the task is L3+ or when the user explicitly requests it

**Acceptance Criteria:**
- [ ] WHEN ultra-plan encounters an architectural decision on an L3+ task THEN it SHALL generate an ADR file in `docs/adr/`
- [ ] WHEN the task is L0-L2 THEN ADR generation SHALL be skipped unless explicitly requested
- [ ] Generated ADRs follow the standard format from `references/adr-template.md`

---

#### 4.2 Add Drift Detection Mode
**Status: PENDING**
**Requirement Refs:** Gap Analysis H5 — Living spec / drift detection
**Depends On:** 4.1
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**
Add a `--refresh` invocation mode to ultra-plan. When invoked with `--refresh`, ultra-plan reads the current IMPLEMENTATION_PLAN.md (or a specified plan file), spawns Explore sub-agents to check each work item's assumptions against current code state, and produces a drift report. The drift report classifies each spec item as: Accurate (code matches plan), Drifted (code diverged from plan), Obsolete (plan item no longer relevant), or New (code introduced something not in the plan).

**Tasks:**
1. [ ] Add `--refresh` argument handling to ultra-plan SKILL.md (check `$ARGUMENTS` for `--refresh`)
2. [ ] Define the refresh workflow: (a) read IMPLEMENTATION_PLAN.md, (b) for each work item, spawn an Explore sub-agent to verify the item's files and acceptance criteria against current code, (c) compile a drift report
3. [ ] Drift report format: table with columns — Work Item, Status (Accurate/Drifted/Obsolete/New), Evidence, Recommended Action
4. [ ] Add guidance: when drift is detected, suggest either updating the plan or flagging the divergence for review
5. [ ] Keep the refresh workflow under 50 lines in SKILL.md — if it grows larger, note that it should be extracted to a separate skill in a future iteration

**Acceptance Criteria:**
- [ ] WHEN ultra-plan is invoked with `--refresh` THEN it SHALL read the existing plan and compare against current code
- [ ] WHEN drift is detected THEN the report SHALL classify each item and suggest an action
- [ ] WHEN no plan file exists THEN `--refresh` SHALL report an error with guidance to generate a plan first
- [ ] Default `/ultra-plan` invocation (no args) works exactly as before

---

#### 4.3 Add Creative Branching for L4+ Tasks
**Status: PENDING**
**Requirement Refs:** Gap Analysis N4 — Branching for creative exploration
**Depends On:** 4.1
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**
Add optional creative exploration to ultra-plan's Solution Design phase for L4+ tasks (greenfield, multi-repo). When the task has 2-3 fundamentally different valid approaches, Phase 4 generates a comparison table with trade-offs across dimensions (speed, cost, maintainability, risk). User picks one approach; others are preserved as ADR alternatives (leveraging Item 9's ADR infrastructure).

**Tasks:**
1. [ ] In Phase 4 (Solution Design): add a conditional check — "For L4+ tasks where multiple valid architectures exist, generate a comparison table before committing to one approach"
2. [ ] Comparison table format: Approach Name, Pros, Cons, Estimated Effort, Risk Level, Recommended When
3. [ ] After user picks an approach: generate the solution design for the chosen approach; generate ADRs for the decision with rejected approaches listed as Alternatives Considered
4. [ ] Add skip logic: only offer branching when there are genuinely different approaches (not minor variants)

**Acceptance Criteria:**
- [ ] WHEN an L4+ task has 2+ fundamentally different valid approaches THEN Phase 4 SHALL present a comparison table
- [ ] WHEN user picks an approach THEN rejected approaches SHALL be documented as ADR alternatives
- [ ] WHEN the task is L0-L3 or has only one viable approach THEN branching SHALL be skipped

---

### Phase 4 Testing Requirements

- [ ] Ultra-plan SKILL.md `--refresh` mode handles: existing plan (drift report), no plan (error), and default invocation (unchanged)
- [ ] ADR template renders correctly with all standard fields
- [ ] Creative branching conditional fires only for L4+ tasks with multiple viable approaches

### Phase 4 Completion Checklist

- [ ] All work items complete
- [ ] ADR template created and referenced
- [ ] Drift detection mode functional
- [ ] Creative branching integrated with ADR generation
- [ ] Default ultra-plan behavior unchanged

---

## Phase 5: Implement-Plan Verification Upgrade

**Estimated Complexity:** M (~1 file, ~100 LOC)
**Dependencies:** Phase 1 (DoD template), Phase 3 (generators emit DoD)
**Execution Mode:** Sequential

### Goals

- Evolve implement-plan state file schema to support multiple verification commands (Item 2 consumer)
- Update testing subagent to run all DoD commands (Item 2 consumer)
- Fold in Lab Notebook action items A2, A3, A4 from Entry 001

### Work Items

#### 5.1 Evolve State File Schema and Testing Subagent
**Status: PENDING**
**Requirement Refs:** Gap Analysis C3↓ — implement-plan consuming DoD; Lab Notebook A2, A3, A4
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Update implement-plan to consume the new DoD and execution hints sections from the plan template. The state file's `project_context.test_command` (single string) evolves to `project_context.verification_commands` (array of `{name, command, pass_criteria}` objects). The testing subagent prompt is updated to run all verification commands, not just the test command. Backward compatibility: check for `verification_commands` first, fall back to `test_command`.

Also fold in the three open action items from Lab Notebook Entry 001:
- A2: Set `Completed` header field during finalization
- A3: Parse `Depends On` field for parallelization map
- A4: Update Risk Mitigation `Status` column during execution

**Tasks:**
1. [ ] In Step 1 (Initial plan scan): update the startup subagent prompt to detect all verification commands from the plan's DoD sections — not just the test command. Return them as a `verification_commands` array.
2. [ ] In Step 2 (Write initial state file): change `project_context.test_command` to `project_context.verification_commands` (array of `{name, command, pass_criteria}` objects). Keep `test_command` as a fallback field.
3. [ ] In Step A2/B3 (Testing): update the testing subagent prompt to run ALL verification commands from the state file's `verification_commands` array (or fall back to `test_command` if the array is absent)
4. [ ] Add backward compat note: "If the state file has `test_command` but no `verification_commands`, wrap it as `[{name: 'tests', command: test_command, pass_criteria: 'exit code 0'}]`"
5. [ ] In Step 1 (Initial plan scan): also parse `Depends On` fields from work items and use them to build a more accurate `parallelization_map` (A3)
6. [ ] In FINALIZATION Final Step 1 (Documentation Polish): set the `**Completed:**` header field in the plan file to today's date (A2)
7. [ ] In the implementation subagent prompt: when completing a work item that has an associated risk in the Risk Mitigation table, update the risk's Status to `Mitigated` (A4)
8. [ ] If execution hints specify a model tier, use the Agent tool's `model` parameter when spawning implementation subagents for that phase

**Acceptance Criteria:**
- [ ] WHEN a plan has DoD sections THEN the testing subagent SHALL run all listed verification commands, not just tests
- [ ] WHEN a state file has `test_command` but no `verification_commands` THEN implement-plan SHALL wrap it into the new format (backward compat)
- [ ] WHEN all items are COMPLETE THEN finalization SHALL set the `Completed` header field
- [ ] WHEN work items have `Depends On` fields THEN the parallelization map SHALL respect those dependencies
- [ ] WHEN execution hints specify a model tier THEN subagents SHALL be spawned with that model

---

### Phase 5 Testing Requirements

- [ ] Read updated implement-plan.md and verify state file schema evolution is documented
- [ ] Verify backward compat logic for old state files is present
- [ ] Verify testing subagent prompt includes all verification commands
- [ ] Verify finalization sets Completed header
- [ ] Verify Depends On parsing is integrated into parallelization map

### Phase 5 Completion Checklist

- [ ] All work items complete
- [ ] State file schema documented with new and legacy formats
- [ ] Testing subagent runs multi-command verification
- [ ] Action items A2, A3, A4 resolved
- [ ] No regressions to implement-plan resume logic

---

## Phase 6: Hook Recipes + AGENTS.md

**Estimated Complexity:** S (~3 files, ~100 LOC)
**Dependencies:** None
**Execution Mode:** Parallel

### Goals

- Ship optional hook recipe examples (Item 10)
- Ship AGENTS.md companion template (Item 12)

### Work Items

#### 6.1 Create Hook Recipe Examples
**Status: PENDING**
**Requirement Refs:** Gap Analysis N5 — Hook recipes
**Files Affected:**
- `plugins/personal-plugin/references/hooks/planning-stop-hook.md` (create)
- `plugins/personal-plugin/references/hooks/verification-post-edit-hook.md` (create)
- `plugins/personal-plugin/references/hooks/session-start-hook.md` (create)
- `plugins/personal-plugin/references/common-patterns.md` (modify)

**Description:**
Create three optional hook recipe example files that users can adapt for their projects. These are documentation/examples, NOT auto-installed hooks. They demonstrate how Claude Code hooks integrate with the planning pipeline.

**Tasks:**
1. [ ] Create `references/hooks/planning-stop-hook.md`: example Stop hook that warns if IMPLEMENTATION_PLAN.md has unchecked items when the session ends. Include the hooks.json snippet and explanation.
2. [ ] Create `references/hooks/verification-post-edit-hook.md`: example PostToolUse hook that runs DoD verification commands after Edit operations on source files. Include the hooks.json snippet and explanation.
3. [ ] Create `references/hooks/session-start-hook.md`: example SessionStart hook that reads IMPLEMENTATION_PLAN.md (if present) and primes context with current plan status. Include the hooks.json snippet and explanation.
4. [ ] Update `common-patterns.md` to add a hooks section pointing to the recipe files

**Acceptance Criteria:**
- [ ] Each hook recipe includes a valid hooks.json snippet and prose explanation
- [ ] Recipes are clearly marked as EXAMPLES that users copy and adapt
- [ ] No auto-installation — the existing `hooks/hooks.json` is NOT modified

---

#### 6.2 Create AGENTS.md Companion Template
**Status: PENDING**
**Requirement Refs:** Gap Analysis N1 — AGENTS.md companion output
**Files Affected:**
- `plugins/personal-plugin/references/agents-md-template.md` (create)
- `plugins/personal-plugin/commands/create-plan.md` (modify)
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Create an AGENTS.md template that can be generated alongside plans for cross-tool compatibility (Codex, Cursor, Aider). Add an optional step to create-plan and plan-improvements: if no AGENTS.md exists in the repo, offer to generate one from CLAUDE.md + plan context.

**Tasks:**
1. [ ] Create `references/agents-md-template.md` with standard AGENTS.md structure: project description, tech stack, conventions, build/test commands, planning workflow guidance
2. [ ] In create-plan Phase 5 (Save and Report): add optional step — "If no AGENTS.md exists, offer to generate one from CLAUDE.md + codebase reconnaissance results"
3. [ ] In plan-improvements Phase 4 (Save and Report): same optional step
4. [ ] Generation logic: read CLAUDE.md, extract project-relevant sections, map to AGENTS.md format. Do NOT duplicate CLAUDE.md verbatim — extract the cross-tool-relevant subset.

**Acceptance Criteria:**
- [ ] WHEN no AGENTS.md exists and a plan is generated THEN the command SHALL offer to create one (not auto-create)
- [ ] WHEN AGENTS.md already exists THEN the offer SHALL be skipped
- [ ] Generated AGENTS.md contains project-relevant guidance, not a full CLAUDE.md copy

---

### Phase 6 Testing Requirements

- [ ] Each hook recipe file has valid JSON snippets
- [ ] AGENTS.md template renders correctly
- [ ] create-plan and plan-improvements offer AGENTS.md generation only when file is absent

### Phase 6 Completion Checklist

- [ ] All work items complete
- [ ] Hook recipes are clearly marked as examples
- [ ] AGENTS.md template created
- [ ] common-patterns.md updated with hooks index
- [ ] No auto-installation of hooks or AGENTS.md

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Execution Hints

- **Model tier:** Opus for Phases 2, 4 (architectural decisions, skill rewrite). Sonnet for Phases 1, 3, 5, 6 (template edits, consumer updates).
- **Context budget:** All phases are M-complexity or smaller; no phase exceeds 6 work items. Standard subagent context is sufficient.
- **Parallelization notes:** Phases 1 and 2 can run in parallel. Phase 6 items can run in parallel. All other phases are sequential due to dependencies.

---

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 1 (all items) | Phase 2 (all items) | Different files except ultra-plan SKILL.md; 1.1 task 4 touches ultra-plan but can be deferred to Phase 2 |
| 6.1 | 6.2 | Completely independent — different files, different features |
| 3.1 | 3.2 | Different files (create-plan vs plan-improvements), same pattern |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy | Status |
|------|------------|--------|---------------------|--------|
| implement-plan state file schema change breaks resume from old state files | Medium | High | Backward compat: check `verification_commands` first, fall back to `test_command`. Document migration in implement-plan.md. | Open |
| Ultra-plan phase renumbering breaks external references | Low | Medium | References in plan-gate and create-plan use skill name and phase purpose, not numbers. Grep and fix all references in Phase 2. | Open |
| Constitution Phase 0 adds friction for quick tasks | Medium | Low | Skip logic: skip Phase 0 when task is L0-L1 scope or user says "skip constitution" | Open |
| Sub-agent investigation returns too-compressed summaries | Medium | Medium | Structured return format with mandatory fields matching inline investigation table. Fallback to inline. | Open |
| Drift detection (`--refresh`) grows too complex for SKILL.md | Medium | Low | 50-line cap in SKILL.md; if exceeded, extract to separate skill in follow-up | Open |
| Anti-pattern catalog becomes stale | Low | Low | Living document; review during each planning skill major version bump | Open |

---

## Unknowns Register

| ID | Unknown | Severity | Affects | Resolution Strategy | Status |
|----|---------|----------|---------|---------------------|--------|
| U1 | Does plan-gate's `/ultraplan` reference (Path D.5) route to Anthropic's built-in or personal-plugin skill? | High | Phase 2, Item 2.4 | Test routing after reference fix — invoke from plan-gate and verify which skill activates | Open |
| U2 | Can implement-plan's testing subagent reliably parse and execute multiple verification commands from a DoD table? | Medium | Phase 5, Item 5.1 | Prototype the subagent prompt with 3-4 commands and test on a real project | Open |
| U3 | Will `--refresh` drift detection work across large plans (20+ work items) within context limits? | Medium | Phase 4, Item 4.2 | Use Explore sub-agents for verification (same pattern as Phase 2 investigation); cap at 20 items per refresh | Open |

---

## Success Metrics

- [ ] All 6 phases completed
- [ ] All 13 gap-analysis items addressed (5 Tier-1, 3 Tier-2, 5 Tier-3)
- [ ] Plan template has 4 new sections (EARS, DoD, execution hints, unknowns)
- [ ] Ultra-plan has 7 phases (0-6) with constitution check, sub-agent investigation, and 3 extension modes
- [ ] implement-plan consumes multi-command verification
- [ ] 6 new reference files created
- [ ] Backward compatibility preserved — existing plans and state files still work
- [ ] Lab Notebook action items A2, A3, A4 resolved

---

## Appendix: Requirement Traceability

| Requirement | Source | Phase | Work Item |
|-------------|--------|-------|-----------|
| EARS-notation acceptance criteria | Gap Analysis C2, Kiro pattern | 1 | 1.1 |
| Runnable Definition of Done | Gap Analysis C3 | 1, 3, 5 | 1.2, 3.1, 3.2, 5.1 |
| Execution hints (model tier, context budget) | Gap Analysis H2 | 1, 3, 5 | 1.3, 3.1, 3.2, 5.1 |
| Anti-pattern catalog | Gap Analysis N2 | 2 | 2.1 |
| Unknowns register | Gap Analysis H1 | 1, 3 | 1.4, 3.1, 3.2, 3.3 |
| Constitution Phase 0 | Gap Analysis C1, Spec Kit | 2 | 2.2 |
| Sub-agent formalization | Gap Analysis H7 | 2 | 2.3 |
| Ultra-plan reference fix | Gap Analysis N8 | 2 | 2.4 |
| ADR generation (L3+) | Gap Analysis H4 | 4 | 4.1 |
| Drift detection (--refresh) | Gap Analysis H5, Kiro | 4 | 4.2 |
| Creative branching (L4+) | Gap Analysis N4, Spec Kit | 4 | 4.3 |
| Hook recipes | Gap Analysis N5 | 6 | 6.1 |
| AGENTS.md companion | Gap Analysis N1 | 6 | 6.2 |
| Lab Notebook A2 (Completed header) | Lab Notebook E001 | 5 | 5.1 |
| Lab Notebook A3 (Depends On parsing) | Lab Notebook E001 | 5 | 5.1 |
| Lab Notebook A4 (Risk Status updates) | Lab Notebook E001 | 5 | 5.1 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-04-30 16:45:00*
*Source: /ultra-plan command — gap analysis implementation*
