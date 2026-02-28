# Implementation Plan

**Generated:** 2026-02-28T14:30:00
**Based On:** RECOMMENDATIONS.md (Planning & Execution Pipeline Analysis)
**Total Phases:** 6
**Estimated Total Effort:** ~3,500 LOC across 6 files

---

## Executive Summary

This plan upgrades the three core planning and execution commands (`create-plan`, `plan-improvements`, `implement-plan`) plus the `plan-gate` skill to production quality. The work is organized into 6 phases across 3 tiers. Tier 1 (Phases 1-2) fixes broken functionality — the unified schema and implement-plan tool API corrections. Tier 2 (Phases 3-4) improves execution quality — context management, analysis depth, and user guardrails. Tier 3 (Phases 5-6) adds robustness and polish — append logic, parallel safety, documentation overhead reduction.

Each phase modifies markdown command files (no source code). Changes are to prompt/instruction text only. The risk of breaking existing functionality is low since the changes refine instructions rather than alter architecture.

---

## Plan Overview

The strategy is **bottom-up stabilization**: fix the structural foundation first (schema, tool API), then improve what flows through that foundation (analysis quality, context management), then harden the edges (error handling, resume, parallelism). Phases 1-2 must be done first because every downstream improvement depends on a consistent schema and a working executor. Phases 3-6 can be done in any order after Phases 1-2, though the listed order minimizes rework.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | Unified Schema | Canonical work item schema, standardized headers, sizing heuristics | M (~3 files, ~200 LOC changed) | None |
| 2 | implement-plan Tool API Fix | Agent tool references, selective git staging, PR-only default | M (~1 file, ~300 LOC changed) | None |
| 3 | Context Window Management | Sampling strategy, state file, two-stage output option | M (~3 files, ~150 LOC changed) | Phases 1-2 |
| 4 | Analysis Quality & User Guardrails | Missing dimensions, priority rubric, task-based analysis, confirmation gates | M (~2 files, ~250 LOC changed) | Phase 1 |
| 5 | Resume, Rollback & Phase Gates | Machine-readable status, checkpoint SHAs, phase validation, circuit breakers | M (~2 files, ~200 LOC changed) | Phases 1-2 |
| 6 | Robustness & Polish | Append markers, parallel safety, doc overhead reduction, allowed-tools, plan limits | S (~4 files, ~150 LOC changed) | Phases 1-2 |

<!-- BEGIN PHASES -->

---

## Phase 1: Unified IMPLEMENTATION_PLAN.md Schema

**Estimated Complexity:** M (~3 files, ~200 LOC changed)
**Dependencies:** None
**Parallel Groups:** [1.1, 1.2] then [1.3] then [1.4]

### Goals
- Both planning commands produce structurally identical IMPLEMENTATION_PLAN.md files
- `/implement-plan` can consume plans from either source with zero parsing differences
- Phase sizing uses concrete heuristics instead of fictional token estimates

### Work Items

#### 1.1 Add Tasks and Notes Fields to plan-improvements Work Item Template ✅ Completed 2026-02-28
**Recommendation Ref:** S1
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Update the IMPLEMENTATION_PLAN.md template section in plan-improvements.md to include the **Tasks** (numbered checkbox list) and **Notes** fields that exist in create-plan's template. Also add (create)/(modify) annotations to the Files Affected field.

**Tasks:**
1. [x] Locate the work item template in plan-improvements.md (lines ~207-218)
2. [x] Add `**Tasks:**` field with numbered checkboxes between Description and Acceptance Criteria
3. [x] Add `**Notes:**` field after Acceptance Criteria
4. [x] Update Files Affected format to include `(create)` / `(modify)` annotations
5. [x] Update the work item instructions in Phase 3 to instruct Claude to generate Tasks sub-steps

**Acceptance Criteria:**
- [x] plan-improvements work item template has all 6 fields matching create-plan: Ref, Files Affected (annotated), Description, Tasks, Acceptance Criteria, Notes
- [x] The ordering of fields is identical between both commands

**Notes:**
The ref field name intentionally differs (Recommendation Ref vs Requirement Refs) since the semantics differ. The structural position and all other fields should be identical.

---

#### 1.2 Standardize Headers, Metadata, and Table Columns ✅ Completed 2026-02-28
**Recommendation Ref:** S2
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Align the header metadata, section structure, and table column names across both planning commands so the IMPLEMENTATION_PLAN.md they produce is structurally identical above and below the phase content.

**Tasks:**
1. [x] Add `**Estimated Total Effort:**` line to plan-improvements header template
2. [x] Add `## Executive Summary` section to plan-improvements template (after header, before Plan Overview)
3. [x] Standardize Risk Mitigation table column: both use `Mitigation Strategy` (not `Mitigation`)
4. [x] Standardize Parallel Work table column: both use `Work Item` (not `Work Item A`)
5. [x] Add `## Appendix: Recommendation Traceability` table to plan-improvements template (maps recommendation IDs to phases/items)
6. [x] Standardize the Phase Completion Checklist to 5 items in both (add "Code reviewed (if applicable)" to plan-improvements)
7. [x] Standardize Testing Requirements format to checkbox lists in both
8. [x] Standardize Generated timestamp format to `[YYYY-MM-DD HH:MM:SS]` in both

**Acceptance Criteria:**
- [x] Header fields are identical (Generated, Based On/Source Documents, Total Phases, Estimated Total Effort)
- [x] Both have Executive Summary section
- [x] All table column names match exactly
- [x] Both have traceability appendix (Requirement or Recommendation)
- [x] Footer format matches

**Notes:**
The Based On value differs by design (RECOMMENDATIONS.md vs document list). The header field name should be `**Based On:**` in both, with the value varying.

---

#### 1.3 Replace Token Estimates with Concrete Sizing Heuristics ✅ Completed 2026-02-28
**Recommendation Ref:** S3, S4
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Replace token-based phase sizing throughout both commands with concrete, observable heuristics (file count, LOC estimate, relative complexity). Reframe the "100K token" constraint as a context window limit rather than an output budget.

**Tasks:**
1. [x] Rewrite Phase Sizing Guidelines in plan-improvements to use file/LOC heuristics
2. [x] Rewrite Phase Sizing Guidelines in create-plan (Section 3.2) to match
3. [x] Change Phase Summary Table column from `Est. Tokens` to `Est. Complexity` in both templates
4. [x] Change per-phase header from `**Estimated Effort:** ~X0,000 tokens` to `**Estimated Complexity:** [S/M/L] (~N files, ~N LOC)`
5. [x] Reframe phase constraint: "Each phase should be completable by a single subagent session. Guideline: read 5-8 files, modify 3-5 files, change ~500 LOC. If a phase exceeds these bounds, split it."
6. [x] Update complexity scale: S (1-3 files, <100 LOC), M (3-8 files, 100-500 LOC), L (8-15 files, 500-1500 LOC)
7. [x] Add: "If a phase would be XL (15+ files), split into sub-phases (e.g., Phase 3a, 3b)"
8. [x] Unify both commands to use same target (S-M per phase, max L), min 2 files per phase

**Acceptance Criteria:**
- [x] No references to "tokens" in Phase Sizing Guidelines, Phase Summary Table, or per-phase headers
- [x] Both commands use identical sizing scale and guidelines
- [x] Per-phase and per-work-item estimates use files/LOC, not tokens
- [x] Explicit guidance for splitting oversized phases

**Notes:**
The Performance sections at the bottom of each command can retain time estimates (those are for the command's own runtime, not the plan's execution).

---

#### 1.4 Add Status Field to Work Item Template
**Recommendation Ref:** U5 (partial)
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Add a machine-readable `**Status: PENDING**` field to the work item template in both commands. This field will be updated by `/implement-plan` during execution (PENDING → IN_PROGRESS → COMPLETE [date]).

**Tasks:**
1. [ ] Add `**Status: PENDING**` as the first field in the work item template (before Ref field) in both commands
2. [ ] Document the three valid status values in a comment: `<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->`

**Acceptance Criteria:**
- [ ] Both planning commands generate work items with `**Status: PENDING**` field
- [ ] Status field is the first field in each work item (easy to scan)

**Notes:**
The actual status transitions are implemented in Phase 5 (implement-plan changes). This phase just ensures the plans are generated with the field.

---

### Phase 1 Testing Requirements
- [ ] Manually verify both templates produce identical work item structure by comparing side-by-side
- [ ] Verify all table column names match between the two templates
- [ ] Confirm no remaining references to token estimates in sizing guidelines

### Phase 1 Completion Checklist
- [ ] All work items complete
- [ ] Templates verified consistent
- [ ] Documentation updated (CLAUDE.md if schema changes warrant)
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 2: Fix implement-plan Tool API and Safety

**Estimated Complexity:** M (~1 file, ~300 LOC changed)
**Dependencies:** None
**Parallel Groups:** [2.1, 2.2, 2.3] then [2.4]

### Goals
- All subagent invocations reference the correct Agent tool API
- Git operations are safe (selective staging, no auto-merge)
- Parallel execution path uses actual background agent mechanism

### Work Items

#### 2.1 Rewrite Subagent Invocations to Use Agent Tool
**Recommendation Ref:** T1
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Replace all references to "Task tool" with "Agent tool" throughout implement-plan.md. Update parameter names and invocation patterns to match the actual Claude Code Agent tool API. Fix the parallel path (Path B) to use `run_in_background: true` on Agent tool calls and `TaskOutput` for collecting results.

**Tasks:**
1. [ ] Replace STARTUP instructions: change "Spawn a subagent (subagent_type: 'general-purpose')" to "Launch an Agent (subagent_type: 'general-purpose', prompt: '...')"
2. [ ] Update all sequential subagent invocations (Steps A1, A2, A3) with correct Agent tool syntax
3. [ ] Update all parallel subagent invocations (Steps B1) to use `run_in_background: true` on Agent tool
4. [ ] Rewrite Step B2 (Collect Results): replace "read output files" with "use TaskOutput to check background agent results; you will be notified when each completes"
5. [ ] Update NEXT ITERATION subagent invocation
6. [ ] Update finalization documentation polish subagent invocation
7. [ ] Clarify in the Context Window Discipline table: "Task" refers to TaskCreate/TaskUpdate/TaskList (progress tracking), "Agent" refers to launching subagents

**Acceptance Criteria:**
- [ ] Zero references to "Task tool" for spawning subagents (Task is only for TaskCreate/TaskUpdate/TaskList)
- [ ] All subagent invocations use Agent tool with correct parameters
- [ ] Path B uses `run_in_background: true` and `TaskOutput` for result collection
- [ ] Context Window Discipline table correctly distinguishes Task (tracking) from Agent (delegation)

**Notes:**
The `allowed-tools` frontmatter currently lists `Task, Skill`. After this change, it should list `Agent, Task` (Agent for subagents, Task for progress tracking). See work item 2.3 for allowed-tools changes.

---

#### 2.2 Replace git add -A with Selective Staging
**Recommendation Ref:** T3
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Replace all instances of `git add -A` with selective staging using the file lists returned by subagents. Add a pre-staging check to surface unexpected files.

**Tasks:**
1. [ ] Replace Step A4 commit sequence with: (a) `git status --short` to detect unexpected files, (b) `git add [files-from-subagent] IMPLEMENTATION_PLAN.md`, (c) optionally add PROGRESS.md and LEARNINGS.md if they were updated, (d) `git commit -m "..."`
2. [ ] Replace Step B5 commit sequence with same pattern but collecting file lists from all parallel subagents
3. [ ] Replace finalization commit with explicit file staging
4. [ ] Add instruction: "If `git status` shows unexpected untracked files not in the subagent's file list, warn the user and do not stage them"

**Acceptance Criteria:**
- [ ] Zero instances of `git add -A` in the command
- [ ] All commit sequences start with `git status --short` check
- [ ] Staging uses explicit file paths from subagent results

**Notes:**
The implementation subagent prompt already says "Return ONLY: (1) files created/modified" — this output is what drives the staging list.

---

#### 2.3 Update allowed-tools and Default Behavior
**Recommendation Ref:** T2, U2
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Update the frontmatter `allowed-tools` to include Agent tool and comprehensive Bash permissions (matching test-project patterns). Remove unused Skill permission. Change finalization default from auto-merge to PR-only.

**Tasks:**
1. [ ] Update frontmatter `allowed-tools` to: `Agent, Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(npx:*), Bash(yarn:*), Bash(pnpm:*), Bash(pytest:*), Bash(python:*), Bash(jest:*), Bash(vitest:*), Bash(bun:*), Task`
2. [ ] Remove `Skill` from allowed-tools
3. [ ] Change Finalization Step 2 default: create PR with comprehensive body, output URL, STOP
4. [ ] Add `--auto-merge` flag description in Input Validation section
5. [ ] When `--auto-merge` is specified, execute current merge behavior
6. [ ] Generate descriptive PR title from actual phases implemented, not "Implementation Complete"

**Acceptance Criteria:**
- [ ] `allowed-tools` includes Agent and comprehensive Bash permissions
- [ ] `Skill` removed from allowed-tools
- [ ] Default finalization creates PR and stops (no merge)
- [ ] `--auto-merge` flag documented and triggers merge behavior
- [ ] PR title is descriptive (e.g., "Implement: [Phase titles]")

**Notes:**
Test whether subagents inherit parent's allowed-tools restrictions. If they do, the comprehensive Bash list is critical. If they don't, it's still good practice for the parent agent.

---

#### 2.4 Add Input Arguments to implement-plan
**Recommendation Ref:** R7 (partial)
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Add optional arguments that the command currently lacks: `--input <path>` for non-default plan locations, `--auto-merge` for opting into merge behavior, and `--pause-between-phases` for interactive mode.

**Tasks:**
1. [ ] Add Optional Arguments section to Input Validation: `--input <path>` (default: IMPLEMENTATION_PLAN.md), `--auto-merge` (default: false), `--pause-between-phases` (default: false)
2. [ ] Update the IMPLEMENTATION_PLAN.md existence check to use the `--input` path
3. [ ] Thread the input path through all subagent prompts that reference "Read IMPLEMENTATION_PLAN.md"

**Acceptance Criteria:**
- [ ] `--input` flag works for custom plan file locations
- [ ] `--auto-merge` and `--pause-between-phases` flags documented
- [ ] Default behavior (no flags) reads from repo root and stops at PR creation

**Notes:**
This resolves the misalignment where `/create-plan --output docs/plan.md` creates a plan that `/implement-plan` can't find.

---

### Phase 2 Testing Requirements
- [ ] Verify all subagent invocation patterns match actual Agent tool API
- [ ] Verify no instances of `git add -A` remain
- [ ] Verify finalization defaults to PR-only

### Phase 2 Completion Checklist
- [ ] All work items complete
- [ ] Agent tool references verified correct
- [ ] Git safety improvements in place
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 3: Context Window Management

**Estimated Complexity:** M (~3 files, ~150 LOC changed)
**Dependencies:** Phases 1-2
**Parallel Groups:** [3.1, 3.2] then [3.3]

### Goals
- plan-improvements reliably completes on 200+ file codebases
- implement-plan remains coherent through 30+ work items
- Graceful degradation when context pressure is detected

### Work Items

#### 3.1 Add Sampling Strategy to plan-improvements
**Recommendation Ref:** C1
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Add explicit context management instructions to Phase 1 (Deep Codebase Analysis) that prevent context exhaustion on medium-to-large codebases. Add a Context Budget row to the Performance table.

**Tasks:**
1. [ ] Add "Context Management" subsection at the start of Phase 1 with sampling strategy: (a) always read config/metadata files, (b) always read entry points and public API surfaces, (c) sample 2-3 representative files per module/directory, (d) deep-read only files flagged as high-complexity or problematic
2. [ ] Add threshold: "For codebases over 100 files, use sampling. For under 100 files, full analysis is fine."
3. [ ] Add instruction: "Reserve at least 40% of context for output generation. If analysis has consumed over 60% of available context, stop reading files and begin generating output."
4. [ ] Add Context Budget row to Performance table: "Small: ~30K tokens for analysis. Medium: ~50K. Large: ~70K. Reserve remainder for output."

**Acceptance Criteria:**
- [ ] Sampling strategy documented with clear thresholds
- [ ] Context budget guidance in Performance table
- [ ] 40% reservation instruction present

**Notes:**
The sampling strategy should also mention using Agent tool with `subagent_type=Explore` for broad codebase searches to avoid flooding main context.

---

#### 3.2 Restructure implement-plan Loop for State Shedding
**Recommendation Ref:** C2
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Redesign the main loop to use a lightweight state file as the ground truth rather than accumulating conversational state. STARTUP returns only the first batch, not everything. NEXT ITERATION uses the state file rather than re-reading the full plan.

**Tasks:**
1. [ ] Define state file format: `.implement-plan-state.json` with fields: `current_phase`, `current_item`, `completed` (array), `failed` (array), `project_context` (tech_stack, test_command, conventions), `checkpoints` (item→SHA mapping)
2. [ ] Modify STARTUP: return only the first phase's items + parallelization info + project context. Write initial state file.
3. [ ] Modify NEXT ITERATION: read state file to determine next item/batch. Only spawn a plan-reading subagent if state file is missing or ambiguous.
4. [ ] Add state shedding instruction: "After every 5 completed work items, discard previous subagent summaries from conversational memory. The state file is the sole source of truth."
5. [ ] After each work item completion, update state file (add to `completed`, update `current_item`)

**Acceptance Criteria:**
- [ ] `.implement-plan-state.json` defined with all required fields
- [ ] STARTUP returns only first batch, not full inventory
- [ ] NEXT ITERATION reads state file, not full plan
- [ ] State shedding instruction present

**Notes:**
The state file should be added to `.gitignore` since it's ephemeral execution state, not a project artifact.

---

#### 3.3 Add Optional Two-Stage Output to plan-improvements
**Recommendation Ref:** C3
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Add a `--recommendations-only` flag that stops after generating RECOMMENDATIONS.md. Add graceful degradation that saves recommendations early if context pressure is detected.

**Tasks:**
1. [ ] Add `--recommendations-only` (alias `--no-plan`) to Optional Arguments section
2. [ ] When flag is set, skip Phase 3 (plan generation) and go directly to Phase 4 (save and report)
3. [ ] Add instruction in Phase 2 → Phase 3 transition: "Save RECOMMENDATIONS.md to disk before beginning Phase 3 (plan generation). This ensures recommendations are preserved if the session is interrupted during plan generation."
4. [ ] Add to summary report: "To generate an implementation plan from these recommendations, run `/create-plan RECOMMENDATIONS.md`"

**Acceptance Criteria:**
- [ ] `--recommendations-only` flag documented and functional
- [ ] RECOMMENDATIONS.md saved before plan generation begins
- [ ] Summary report includes next-step guidance when plan is skipped

**Notes:**
This requires `/create-plan` to accept RECOMMENDATIONS.md as a valid "requirements document" in its discovery phase. Add "RECOMMENDATIONS.md" to the search patterns in create-plan's Phase 1.1.

---

### Phase 3 Testing Requirements
- [ ] Verify plan-improvements sampling strategy produces actionable output on large codebases
- [ ] Verify implement-plan state file is written and read correctly through multi-item execution
- [ ] Verify `--recommendations-only` stops after RECOMMENDATIONS.md

### Phase 3 Completion Checklist
- [ ] All work items complete
- [ ] Context management tested on representative codebases
- [ ] State file mechanism documented
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 4: Analysis Quality and User Guardrails

**Estimated Complexity:** M (~2 files, ~250 LOC changed)
**Dependencies:** Phase 1
**Parallel Groups:** [4.1, 4.2, 4.3] then [4.4, 4.5]

### Goals
- plan-improvements catches security, performance, and dependency issues
- Analysis produces evidence-based findings rather than subjective commentary
- create-plan accounts for existing codebase and confirms scope with user

### Work Items

#### 4.1 Add Missing Analysis Dimensions to plan-improvements
**Recommendation Ref:** A1
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Add Security Posture, Performance, Dependency Health, and CI/CD Pipeline as first-class analysis dimensions in Phase 1. Port specific analysis patterns from `/review-arch`. Make recommendation categories dynamic rather than fixed at 5.

**Tasks:**
1. [ ] Add "Security Posture" subsection: hardcoded secrets/credentials, input validation gaps, authentication/authorization patterns, dependency CVEs (check with audit tools if available)
2. [ ] Add "Performance & Scalability" subsection: N+1 queries, blocking ops in async contexts, missing caching, resource cleanup, memory management
3. [ ] Add "Dependency Health" subsection: outdated dependencies, floating versions without lock files, license compliance, transitive vulnerabilities
4. [ ] Add "CI/CD Pipeline" subsection: build pipeline health, coverage enforcement, quality gates, deployment complexity
5. [ ] Change recommendation categories instruction: "Use 3-7 categories derived from actual findings. The listed categories are starting suggestions, not a rigid structure. Add Security, Performance, or CI/CD categories when findings warrant them."
6. [ ] Add category prefix mapping for new categories: S = Security, P = Performance, CI = CI/CD, DH = Dependency Health

**Acceptance Criteria:**
- [ ] 9 analysis dimensions total (5 existing + 4 new)
- [ ] Each new dimension has 3-5 specific things to look for (not open questions)
- [ ] Recommendation categories are dynamic (3-7) not fixed (5)
- [ ] New category prefixes defined for recommendation IDs

**Notes:**
These additions increase analysis thoroughness but also increase context consumption. The sampling strategy from Phase 3 (work item 3.1) helps offset this.

---

#### 4.2 Define Priority Rubric and Impact/Effort Matrix
**Recommendation Ref:** A2
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Add explicit definitions for Priority levels and instruction to populate Quick Wins mechanically from an Impact/Effort matrix.

**Tasks:**
1. [ ] Add Priority Rubric subsection before Phase 2: Critical = production outage risk, security vulnerability, or data integrity threat. High = blocks feature development or causes regular developer friction. Medium = improves code quality but is not blocking. Low = nice-to-have optimization or style improvement.
2. [ ] Add instruction: "After categorizing all recommendations, plot them on a 2x2 Impact vs Effort matrix. Populate the Quick Wins section from the High-Impact/Low-Effort quadrant. Populate Strategic Initiatives from the High-Impact/High-Effort quadrant."
3. [ ] Add minimum 3 items requirement for Not Recommended section with per-item template: Title, Why Considered, Why Rejected, Conditions for Reconsideration

**Acceptance Criteria:**
- [ ] Priority definitions documented with examples
- [ ] Quick Wins populated mechanically from matrix
- [ ] Not Recommended section has structured template and minimum 3 items

**Notes:**
Port severity definitions from `/review-arch` Phase 3 (Technical Debt Inventory).

---

#### 4.3 Replace Question-Based with Task-Based Analysis
**Recommendation Ref:** A3
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Rewrite Phase 1 analysis subsections from open-ended questions to concrete, countable tasks that produce evidence-based findings with file references.

**Tasks:**
1. [ ] Rewrite Usability Assessment: "Trace the 3 most common user workflows from entry point to completion. For each, count the steps, identify redundant operations, and note error handling gaps."
2. [ ] Rewrite Output Quality Assessment: "Generate sample output from 3 representative inputs. Compare against professional standards. Identify format inconsistencies, missing validations, and edge cases that produce degraded output."
3. [ ] Rewrite Architecture & Design: "Map the dependency graph between top-level modules. Identify all files exceeding 300 lines. Flag functions over 50 lines as complexity hotspots. List all `catch`/`except` blocks that swallow errors silently."
4. [ ] Rewrite Developer Experience: "Attempt the 'new feature' workflow: what files must be created/modified and what conventions must be followed? Identify all undocumented conventions that a new contributor would miss."
5. [ ] Rewrite Missing Capabilities: "Compare against a capabilities checklist for this project type. For CLI tools: help system, verbose/quiet modes, config file support, exit codes, shell completion. For web apps: error pages, loading states, accessibility. For libraries: documentation, examples, changelog."

**Acceptance Criteria:**
- [ ] Each analysis dimension uses 3-5 concrete tasks instead of open questions
- [ ] Tasks produce countable, file-referenced findings
- [ ] No analysis prompt is phrased as a yes/no or subjective question

**Notes:**
This is the biggest quality-of-output improvement. Task-based prompts produce enumerated findings; question-based prompts produce paragraphs of commentary.

---

#### 4.4 Add Codebase Reconnaissance to create-plan
**Recommendation Ref:** A4
**Files Affected:**
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Add a lightweight codebase scan between document discovery and requirements analysis so plans account for existing code rather than assuming greenfield.

**Tasks:**
1. [ ] Add "Phase 1.5: Codebase Reconnaissance" section between Phase 1 (Document Discovery) and Phase 2 (Requirements Analysis)
2. [ ] Scan: project structure, tech stack, test infrastructure, CI/CD configuration
3. [ ] Cross-reference: identify features in requirements documents that already exist in the codebase. Flag: "PRD section X describes [feature] — the project already has [path]. Plan should extend, not rebuild."
4. [ ] Feed into Phase 3: existing code patterns inform implementation approach in work items

**Acceptance Criteria:**
- [ ] Codebase reconnaissance step documented
- [ ] Already-implemented features detected and flagged
- [ ] Plan accounts for existing code (extends rather than rebuilds)

**Notes:**
Keep this lightweight (5-10 minutes max). It's not a full `/plan-improvements` analysis — just enough to avoid greenfield-on-brownfield plans.

---

#### 4.5 Add Confirmation Checkpoint to create-plan
**Recommendation Ref:** U1
**Files Affected:**
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Add a user approval gate between requirements analysis and plan generation, presenting the extracted feature list, proposed phases, and assumptions.

**Tasks:**
1. [ ] Add "Phase 2.5: Scope Confirmation" section after Phase 2 (Requirements Analysis)
2. [ ] Present: extracted feature list with proposed priorities, proposed number of phases and rough grouping, scoping assumptions, any features flagged as already implemented
3. [ ] Ask: "Proceed with this scope? (yes / adjust / abort)"
4. [ ] If "adjust": accept modifications and re-plan
5. [ ] If "abort": stop and report what was analyzed

**Acceptance Criteria:**
- [ ] Scope confirmation presented before plan generation begins
- [ ] User can approve, adjust, or abort
- [ ] Assumptions explicitly listed

**Notes:**
Keep the confirmation compact — a table, not a multi-page document. The goal is a 30-second review, not a deep read.

---

### Phase 4 Testing Requirements
- [ ] Verify new analysis dimensions produce findings on representative codebases
- [ ] Verify priority rubric produces consistent priority assignments across runs
- [ ] Verify task-based analysis produces file-referenced findings
- [ ] Verify codebase reconnaissance catches already-implemented features
- [ ] Verify scope confirmation checkpoint pauses for user input

### Phase 4 Completion Checklist
- [ ] All work items complete
- [ ] Analysis quality verified on representative projects
- [ ] User guardrails tested
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 5: Resume, Rollback, and Phase Gates

**Estimated Complexity:** M (~2 files, ~200 LOC changed)
**Dependencies:** Phases 1-2
**Parallel Groups:** [5.1] then [5.2, 5.3] then [5.4]

### Goals
- implement-plan resume works reliably after interruption
- Bad commits can be reverted without restarting the plan
- Phase boundaries are validated before moving forward

### Work Items

#### 5.1 Implement Machine-Readable Resume with State File
**Recommendation Ref:** U5
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Implement robust resume using the `.implement-plan-state.json` file (defined in Phase 3, work item 3.2). Mark items IN_PROGRESS before implementation starts. Detect IN_PROGRESS items on resume and offer retry/skip/complete options.

**Tasks:**
1. [ ] Add to implementation subagent pre-step: update state file to mark current item `IN_PROGRESS`, update IMPLEMENTATION_PLAN.md Status field to `IN_PROGRESS`
2. [ ] Add to post-test step: update state file to mark current item `COMPLETE`, update IMPLEMENTATION_PLAN.md Status field to `COMPLETE [YYYY-MM-DD]`
3. [ ] Add resume detection in STARTUP: if state file exists, check for IN_PROGRESS items. If found, present: "Work item [X] was in progress when the previous session ended. Options: (1) Retry implementation, (2) Skip and mark incomplete, (3) Mark as complete (if it was finished but not recorded)"
4. [ ] Add to Prerequisites validation: if working directory is dirty AND state file shows an IN_PROGRESS item, offer to commit or stash the interrupted work before resuming

**Acceptance Criteria:**
- [ ] Items marked IN_PROGRESS before implementation, COMPLETE after testing
- [ ] Resume detects IN_PROGRESS items and offers options
- [ ] Dirty working directory from interrupted session handled gracefully

**Notes:**
The Status field in IMPLEMENTATION_PLAN.md was added in Phase 1, work item 1.4. This phase adds the transitions.

---

#### 5.2 Add Rollback/Checkpoint Capability
**Recommendation Ref:** U3
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Record commit SHA checkpoints after each successful test pass. Offer rollback to last checkpoint when tests can't be fixed.

**Tasks:**
1. [ ] After each successful test pass (ALL_TESTS_PASS), record the commit SHA in state file: `checkpoints[item_id] = sha`
2. [ ] Also record `last_good_sha` in state file (the most recent checkpoint)
3. [ ] When testing subagent returns TESTS_STUCK (see Phase 6, work item 6.2): offer "(1) Revert to last checkpoint [sha], (2) Skip this item and continue, (3) Pause for manual intervention"
4. [ ] If revert chosen: `git revert --no-commit HEAD~N` back to checkpoint, then `git commit -m "Revert: [item] - tests could not be fixed"`

**Acceptance Criteria:**
- [ ] Checkpoint SHAs recorded after each successful test
- [ ] Rollback offered on unfixable test failures
- [ ] Revert produces a clean commit (not destructive reset)

**Notes:**
Use `git revert` not `git reset --hard` — reverts are safe and preserve history.

---

#### 5.3 Add Phase Boundary Quality Gates
**Recommendation Ref:** U4
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
After the last work item in each phase, validate the phase's completion checklist and testing requirements before proceeding. Optionally pause for user confirmation.

**Tasks:**
1. [ ] After the NEXT ITERATION subagent signals a phase transition (next item is in a new phase), spawn a validation subagent: "Read IMPLEMENTATION_PLAN.md Phase [N] Completion Checklist and Testing Requirements. Verify each item. Return: PHASE_VALID or PHASE_ISSUES with list of unchecked items."
2. [ ] Present phase summary: "Phase [N] complete. [M] items implemented. Validation: [PASS/ISSUES]."
3. [ ] If `--pause-between-phases` flag set: ask "Proceed to Phase [N+1]? (yes / review / abort)"
4. [ ] If PHASE_ISSUES: present the unchecked items and ask for guidance

**Acceptance Criteria:**
- [ ] Phase boundary detected by NEXT ITERATION subagent
- [ ] Completion checklist validated at each boundary
- [ ] Summary presented to user
- [ ] `--pause-between-phases` pauses for confirmation

**Notes:**
Default behavior (no flag) presents summary and continues. The pause flag is for when the user wants tighter control.

---

#### 5.4 Add Partial Completion Reporting
**Recommendation Ref:** R4 (partial)
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Add an instruction for what to output if the command is interrupted or stops early, so the user knows exactly what was accomplished and how to resume.

**Tasks:**
1. [ ] Add "Early Termination" section: "If execution stops before ALL_COMPLETE (context exhaustion, user interrupt, unfixable error), output a completion report: items completed this session, current item status, last checkpoint SHA, how to resume (`/implement-plan` will pick up from the state file)"
2. [ ] Add instruction to always output this report even on normal completion

**Acceptance Criteria:**
- [ ] Completion report documented for all exit paths (normal, interrupt, error)
- [ ] Report includes items completed, current status, resume guidance

---

### Phase 5 Testing Requirements
- [ ] Verify resume detects IN_PROGRESS items from interrupted session
- [ ] Verify rollback produces clean git history
- [ ] Verify phase boundary validation catches incomplete checklists
- [ ] Verify completion report outputs on all exit paths

### Phase 5 Completion Checklist
- [ ] All work items complete
- [ ] Resume/rollback tested with simulated interruptions
- [ ] Phase gates tested with incomplete checklists
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 6: Robustness and Polish

**Estimated Complexity:** S (~4 files, ~150 LOC changed)
**Dependencies:** Phases 1-2
**Parallel Groups:** [6.1, 6.2, 6.3, 6.4] then [6.5]

### Goals
- Append logic is deterministic with machine-readable markers
- Parallel execution has safety checks
- Documentation overhead is reduced
- Planning commands have proper tool restrictions

### Work Items

#### 6.1 Add Machine-Readable Markers for Append Logic
**Recommendation Ref:** R1
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Add HTML comment markers to the IMPLEMENTATION_PLAN.md template so append operations have unambiguous insertion points.

**Tasks:**
1. [ ] Add `<!-- BEGIN PHASES -->` before the first `## Phase 1:` section in both templates
2. [ ] Add `<!-- END PHASES -->` after the last phase section (before Parallel Work Opportunities) in both templates
3. [ ] Add `<!-- BEGIN TABLES -->` before Parallel Work Opportunities in both templates
4. [ ] Add `<!-- END TABLES -->` after the last table section in both templates
5. [ ] Update Append vs Overwrite instructions in both commands to reference these markers instead of ambiguous `---` separators
6. [ ] Add a before/after example showing append of 2 new phases to an existing 3-phase plan
7. [ ] Add handling for partially-executed plans: "If some items have Status: COMPLETE, preserve them exactly. Warn: 'This plan has items in progress. New phases will be appended after existing content.'"

**Acceptance Criteria:**
- [ ] Machine-readable markers present in both templates
- [ ] Append instructions reference markers, not `---` separators
- [ ] Before/after example included
- [ ] Partially-executed plan handling documented

---

#### 6.2 Add Testing Circuit Breaker to implement-plan
**Recommendation Ref:** R2
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Add explicit iteration limits to testing subagent prompts to prevent infinite fix loops.

**Tasks:**
1. [ ] Modify sequential testing prompt (Step A2): add "If after 3 fix-and-rerun cycles tests still fail, stop and return: TESTS_STUCK, list of remaining failures, what was tried and why it didn't work"
2. [ ] Modify parallel testing prompt (Step B3): same circuit breaker
3. [ ] Add main agent handling for TESTS_STUCK: "If TESTS_STUCK, offer: (1) Revert to checkpoint, (2) Skip this item, (3) Pause for manual intervention"

**Acceptance Criteria:**
- [ ] Both testing prompts have 3-attempt circuit breaker
- [ ] TESTS_STUCK return format defined
- [ ] Main agent has handling for TESTS_STUCK response

---

#### 6.3 Add Subagent Project Context and Reduce Doc Overhead
**Recommendation Ref:** R3, R4
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify)

**Description:**
Add project context to subagent prompts and fold documentation updates into the implementation subagent to reduce overhead.

**Tasks:**
1. [ ] Modify STARTUP prompt to also extract: tech stack, test command, 3-5 key conventions from CLAUDE.md or project config. Store in state file under `project_context`.
2. [ ] Add Project Context header to every implementation subagent prompt: "Project: [tech_stack]. Test command: [test_command]. Conventions: [conventions]."
3. [ ] Fold documentation into implementation subagent: add to prompt "When complete, also update IMPLEMENTATION_PLAN.md: change this item's Status to COMPLETE [today's date]."
4. [ ] Remove separate documentation subagent (Steps A3 and B4)
5. [ ] Make PROGRESS.md optional: only generated if tracking file exists or `--progress` flag is set
6. [ ] Only update LEARNINGS.md when testing subagent reports actual issues (not "no issues")

**Acceptance Criteria:**
- [ ] Project context in every implementation subagent prompt
- [ ] No separate documentation subagent step
- [ ] PROGRESS.md optional
- [ ] LEARNINGS.md only updated when there are learnings

---

#### 6.4 Add allowed-tools to Planning Commands and Plan Size Limits
**Recommendation Ref:** R6, R7
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Add tool restrictions to both planning commands and add guidance on maximum plan size.

**Tasks:**
1. [ ] Add `allowed-tools: Read, Glob, Grep, Write, Edit, Agent` to plan-improvements frontmatter
2. [ ] Add `allowed-tools: Read, Glob, Grep, Write, Edit, Agent` to create-plan frontmatter
3. [ ] Add plan size limit guidance to both: "If the plan exceeds 8 phases, suggest splitting into multiple plan files. Add `--max-phases <n>` as an optional argument."
4. [ ] Add guidance on work item granularity: "Each work item should touch no more than 5-8 files and change ~500 LOC. If a work item exceeds these bounds, split it into sub-items."

**Acceptance Criteria:**
- [ ] Both planning commands have `allowed-tools` in frontmatter
- [ ] Plan size limit documented
- [ ] Work item granularity guidance documented

---

#### 6.5 Update Help Skill and CLAUDE.md
**Recommendation Ref:** (housekeeping)
**Files Affected:**
- `plugins/personal-plugin/skills/help/SKILL.md` (modify)
- `C:\Users\Troy Davis\dev\personal\claude-marketplace\CLAUDE.md` (modify)

**Description:**
Update help documentation and CLAUDE.md to reflect new arguments, flags, and capabilities added across all phases.

**Tasks:**
1. [ ] Update `/create-plan` help entry: add `--recommendations-only` note, mention codebase reconnaissance and scope confirmation
2. [ ] Update `/plan-improvements` help entry: add `--recommendations-only`, mention expanded analysis dimensions
3. [ ] Update `/implement-plan` help entry: add `--input`, `--auto-merge`, `--pause-between-phases` flags; mention state file and resume capability
4. [ ] Update CLAUDE.md "Commands vs Skills" or pipeline documentation if significant structural changes warrant it

**Acceptance Criteria:**
- [ ] Help entries reflect all new arguments and flags
- [ ] CLAUDE.md accurate for the updated pipeline

---

### Phase 6 Testing Requirements
- [ ] Verify append logic uses markers correctly
- [ ] Verify testing circuit breaker fires after 3 attempts
- [ ] Verify implementation subagent updates Status field directly
- [ ] Verify allowed-tools restrictions are in frontmatter

### Phase 6 Completion Checklist
- [ ] All work items complete
- [ ] All markdown command files validated
- [ ] Help skill updated
- [ ] CLAUDE.md updated if needed
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

<!-- END PHASES -->

---

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2 | Different files; 1.1 modifies plan-improvements, 1.2 modifies both but different sections |
| 2.1 | 2.2, 2.3 | All modify implement-plan but different sections (subagent invocations vs git staging vs frontmatter) |
| 3.1 | 3.2 | Different files (plan-improvements vs implement-plan) |
| 4.1 | 4.2, 4.3 | All modify plan-improvements but different sections |
| 4.4 | 4.5 | Both modify create-plan but different sections |
| 5.2 | 5.3 | Both modify implement-plan but different sections (rollback vs phase gates) |
| 6.1 | 6.2, 6.3, 6.4 | Different files or non-overlapping sections |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Template changes break existing plans | Medium | High | Only add fields; never remove or rename existing fields. Existing plans remain valid. |
| Agent tool API assumptions wrong | Low | Critical | Test subagent invocations in a real session before committing. Work item 2.1 should be validated empirically. |
| Sampling strategy too aggressive | Medium | Medium | Default to full analysis for <100 files. Sampling only for larger codebases. |
| State file introduces new failure mode | Medium | Medium | State file is optional — if missing, fall back to plan file parsing (current behavior). |
| Parallel safety checks too restrictive | Low | Low | Default to sequential when in doubt. Parallel is an optimization, not a requirement. |

---

## Success Metrics

- [ ] Plans from `/create-plan` and `/plan-improvements` are structurally identical (diff only in content, not schema)
- [ ] `/implement-plan` runs to completion on a 10-item plan without context degradation
- [ ] `/implement-plan` resumes correctly after simulated interruption
- [ ] `/plan-improvements` completes on a 200+ file codebase without context exhaustion
- [ ] No instances of `git add -A` or auto-merge in default behavior
- [ ] All three commands have `allowed-tools` in frontmatter

---

## Appendix: Recommendation Traceability

| Recommendation | Category | Phase | Work Item |
|----------------|----------|-------|-----------|
| S1 | Schema | 1 | 1.1 |
| S2 | Schema | 1 | 1.2 |
| S3 | Schema | 1 | 1.3 |
| S4 | Schema | 1 | 1.3 |
| U5 (partial) | User Experience | 1 | 1.4 |
| T1 | Tool API | 2 | 2.1 |
| T3 | Tool API | 2 | 2.2 |
| T2 | Tool API | 2 | 2.3 |
| U2 | User Experience | 2 | 2.3 |
| R7 (partial) | Robustness | 2 | 2.4 |
| C1 | Context | 3 | 3.1 |
| C2 | Context | 3 | 3.2 |
| C3 | Context | 3 | 3.3 |
| A1 | Analysis | 4 | 4.1 |
| A2 | Analysis | 4 | 4.2 |
| A3 | Analysis | 4 | 4.3 |
| A4 | Analysis | 4 | 4.4 |
| U1 | User Experience | 4 | 4.5 |
| U5 | User Experience | 5 | 5.1 |
| U3 | User Experience | 5 | 5.2 |
| U4 | User Experience | 5 | 5.3 |
| R4 (partial) | Robustness | 5 | 5.4 |
| R1 | Robustness | 6 | 6.1 |
| R2 | Robustness | 6 | 6.2 |
| R3 | Robustness | 6 | 6.3 |
| R4 | Robustness | 6 | 6.3 |
| R6 | Robustness | 6 | 6.4 |
| R7 | Robustness | 6 | 6.4 |
| R8 | Robustness | 4 | 4.2 |

---

*Implementation plan generated by Claude on 2026-02-28T14:30:00*
*Source: /plan-improvements command — Planning & Execution Pipeline overhaul*
