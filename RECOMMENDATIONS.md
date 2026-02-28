# Improvement Recommendations

**Generated:** 2026-02-28T14:30:00
**Analyzed Project:** claude-marketplace — Planning & Execution Pipeline
**Analysis Scope:** Three core commands (`create-plan`, `plan-improvements`, `implement-plan`) plus adjacent pipeline (`plan-gate`, `plan-next`)

---

## Executive Summary

The planning and execution pipeline (`/plan-improvements` or `/create-plan` → `/implement-plan`) is the most ambitious subsystem in the personal-plugin. It attempts to turn codebase analysis or requirements documents into phased implementation plans, then autonomously execute those plans through orchestrated subagents. The architecture is sound — the separation between planning and execution, the thin-loop-controller pattern, and the persistent artifact approach are all correct design choices.

However, the pipeline has three categories of problems that significantly degrade real-world reliability. First, **the two planning commands produce structurally different IMPLEMENTATION_PLAN.md files**, meaning `/implement-plan` receives inconsistent input depending on which upstream command generated the plan. The most impactful difference: `/create-plan` generates work items with explicit Tasks checklists that tell subagents exactly what to do, while `/plan-improvements` omits this field entirely, forcing subagents to infer steps from a description paragraph. Second, **`/implement-plan` references the wrong tool API** — it instructs the agent to use "Task tool" with parameters like `subagent_type` and `run_in_background` that belong to the Agent tool, and references "output files" for background agents that don't exist. The parallel execution path (Path B) is likely non-functional as written. Third, **context window management is aspirational rather than structural** — `/plan-improvements` instructs "Ultrathink and thoroughly analyze the entire codebase" without sampling guidance, risking exhaustion before output generation begins, and `/implement-plan` accumulates state linearly across work items despite explicit warnings not to.

Fixing these issues requires 28 targeted changes across three tiers: critical fixes that address broken functionality, execution quality improvements that make plans better and more reliable, and polish items that improve consistency and edge case handling.

---

## Recommendation Categories

### Category 1: Schema & Consistency (S)

#### S1. Unify IMPLEMENTATION_PLAN.md Work Item Schema

**Priority:** Critical
**Effort:** M
**Impact:** All plans produce identical structure for `/implement-plan` to consume; subagent execution quality becomes consistent regardless of which planning command generated the plan

**Current State:**
`/create-plan` generates work items with 6 fields: Requirement Refs, Files Affected (with create/modify annotations), Description, Tasks (numbered checkboxes), Acceptance Criteria, Notes. `/plan-improvements` generates work items with only 4 fields: Recommendation Ref, Files Affected (plain list), Description, Acceptance Criteria. The missing **Tasks** checklist is the most impactful gap — it provides explicit step-by-step instructions that subagents can follow mechanically. Without it, plans from `/plan-improvements` produce lower-quality subagent execution because subagents must infer what to do.

**Recommendation:**
Adopt `/create-plan`'s work item schema as the canonical standard. Both commands should emit work items with: Ref field (Requirement Refs or Recommendation Ref), Files Affected (with create/modify annotations), Description, Tasks (numbered checkbox list), Acceptance Criteria, Notes.

**Implementation Notes:**
- Modify the template in `plan-improvements.md` lines 207-218 to add Tasks and Notes fields
- Standardize Files Affected to include (create)/(modify) annotations in both commands
- The ref field name can differ (Requirement Refs vs Recommendation Ref) since the semantics differ — but the structural position should be identical

---

#### S2. Standardize IMPLEMENTATION_PLAN.md Header and Metadata

**Priority:** High
**Effort:** S
**Impact:** `/implement-plan` can parse plans from either source with consistent expectations; PR generation produces complete summaries

**Current State:**
The two planning commands produce different headers. `/create-plan` includes: Source Documents (list), Estimated Total Effort, and an Executive Summary section. `/plan-improvements` uses: Based On (single value), omits total effort, and has no Executive Summary. The Phase Summary Table columns also differ subtly (Mitigation Strategy vs Mitigation, Work Item vs Work Item A).

**Recommendation:**
Standardize header to include: Generated timestamp (YYYY-MM-DD HH:MM:SS format), Based On (document list or RECOMMENDATIONS.md), Total Phases, Estimated Total Effort, and Executive Summary section. Standardize all table column names across both templates.

**Implementation Notes:**
- Add `**Estimated Total Effort:**` to `/plan-improvements` template
- Add `## Executive Summary` section to `/plan-improvements` template
- Standardize Risk Mitigation column to `Mitigation Strategy`
- Standardize Parallel Work column to `Work Item`
- Add Recommendation Traceability appendix to `/plan-improvements` (maps recommendation IDs to phases/items)

---

#### S3. Standardize Phase Sizing Parameters

**Priority:** Medium
**Effort:** XS
**Impact:** Consistent phase sizing across both planning commands; eliminates confusion about target vs maximum

**Current State:**
`/create-plan` targets ~80K tokens per phase with 20% buffer, max 100K, min 20K. `/plan-improvements` targets ~100K tokens including testing/fixes with no explicit max or min. The token estimate ranges also differ between the two sizing tables.

**Recommendation:**
Use a single sizing specification: target 80K tokens per phase, maximum 100K, minimum 20K. If a phase exceeds 100K, split into sub-phases (e.g., Phase 3a, 3b). Use the same complexity scale in both commands.

**Implementation Notes:**
- Update `/plan-improvements` Phase Sizing Guidelines to match `/create-plan`'s parameters
- Both should use the same complexity table (XS through XL with ranges)

---

#### S4. Replace Fictional Token Estimates with Concrete Heuristics

**Priority:** High
**Effort:** S
**Impact:** Phase sizing becomes meaningful rather than cargo-cult; fewer phase overflows during execution

**Current State:**
Both commands estimate effort in tokens (e.g., "New feature with tests: ~10K-30K tokens"). These numbers are unvalidated guesses — the repo's own previous IMPLEMENTATION_PLAN.md assigned 80-90K tokens to phases that should have been 30-50K by the sizing guide. Token estimation at planning time is pure guesswork; Claude cannot predict how many tokens implementation will consume.

**Recommendation:**
Replace token-based estimates with concrete heuristics that are actually observable: number of files affected, estimated lines of code changed, and relative complexity (S/M/L). Keep the ~80K target as a context window constraint (not an output budget), and reframe it as: "each phase should be completable by a single subagent session — typically 5-8 files read, 3-5 files modified, ~500 LOC changed."

**Implementation Notes:**
- Rewrite Phase Sizing Guidelines in both commands
- Change Phase Summary Table column from `Est. Tokens` to `Est. Complexity` using S/M/L
- Phase header changes from `**Estimated Effort:** ~X0,000 tokens` to `**Estimated Complexity:** [S/M/L] (~N files, ~N LOC)`

---

### Category 2: Tool & API Correctness (T)

#### T1. Fix implement-plan Tool References (Agent Tool, Not Task Tool)

**Priority:** Critical
**Effort:** M
**Impact:** Makes the command actually functional; parallel execution path becomes viable

**Current State:**
`/implement-plan` instructs "Spawn a subagent (subagent_type: "general-purpose")" using the "Task tool" throughout. The actual Claude Code API uses the **Agent tool** with parameters `subagent_type`, `prompt`, and `run_in_background`. The command also references "output files" for background agents (Step B2: "read its output file to get status") — these do not exist. Agent tool returns results inline to the parent agent, or via notification for background agents.

**Recommendation:**
Rewrite all subagent invocation instructions to reference the Agent tool correctly. Replace "output file" references with the actual return mechanism (inline results for foreground agents, notification for background agents via `run_in_background: true`). Update the parallel path (Path B) to use `TaskOutput` for collecting background agent results.

**Implementation Notes:**
- Every instance of "Task tool" or "Spawn a subagent" needs to reference "Agent tool" with correct parameters
- Step B2 (Collect Results) needs complete rewrite to use Agent notification mechanism
- The `Task` in `allowed-tools` refers to TaskCreate/TaskUpdate/TaskList — these are tracking tools, not agent spawn tools. Clarify this distinction.
- Verify whether `allowed-tools` restrictions on the parent command affect subagent tool access

---

#### T2. Expand implement-plan allowed-tools for Subagent Operations

**Priority:** High
**Effort:** XS
**Impact:** Ensures the command can run tests, install dependencies, and execute build tools

**Current State:**
`/implement-plan` declares `allowed-tools: Bash(git:*), Bash(gh:*), Task, Skill`. Compare with `/test-project` which declares Bash permissions for npm, npx, yarn, pnpm, pytest, python, go, cargo, dotnet, jest, vitest, and bun. If `allowed-tools` restricts what the parent agent can do (and subagents inherit unrestricted access), this may be fine. But if subagents inherit the parent's restrictions, they cannot run tests or build code.

**Recommendation:**
Add comprehensive Bash permissions matching `/test-project`'s pattern, or add a general `Bash` permission. Also remove `Skill` from allowed-tools since no skills are invoked.

**Implementation Notes:**
- Test empirically whether subagent tool access is scoped by parent's `allowed-tools`
- If subagents are unrestricted, keep parent permissions minimal but add `Agent` to the list
- Remove unused `Skill` permission

---

#### T3. Replace `git add -A` with Selective Staging

**Priority:** High
**Effort:** S
**Impact:** Prevents accidental commit of secrets, temp files, partial output, and IDE artifacts

**Current State:**
`/implement-plan` uses `git add -A` after every work item (lines 184, 249, 290). This stages everything in the working tree, including temp files from subagents, OS artifacts, and potentially sensitive files. This directly contradicts the system-level instruction: "prefer adding specific files by name rather than using `git add -A`."

**Recommendation:**
Replace with explicit staging: `git add [files-reported-by-subagent] IMPLEMENTATION_PLAN.md PROGRESS.md LEARNINGS.md`. Run `git status --short` first and surface any unexpected untracked files for review.

**Implementation Notes:**
- Implementation subagent already returns "files created/modified" — use that list
- Add `git status --short` check before staging to catch unexpected files
- For parallel batches, collect all file lists then stage explicitly

---

### Category 3: Context Window Management (C)

#### C1. Add Context Sampling Strategy to plan-improvements

**Priority:** Critical
**Effort:** S
**Impact:** Prevents context exhaustion on medium-to-large codebases; command completes reliably

**Current State:**
`/plan-improvements` says "Ultrathink and thoroughly analyze the entire codebase" with no guidance on managing context consumption. For a 200+ file project, reading even half the files exhausts context before output generation begins. The command then needs to generate two large documents (RECOMMENDATIONS.md + IMPLEMENTATION_PLAN.md) in the remaining context.

**Recommendation:**
Add explicit context management instructions: For codebases over 100 files, use a sampling strategy: (1) Read all config/metadata files, (2) Read entry points and public API surfaces, (3) Sample representative files from each module/directory (2-3 per module), (4) Deep-read only files flagged as high-complexity or problematic. Reserve at least 40% of context for output generation.

**Implementation Notes:**
- Add "Context Budget" row to the Performance table
- Add a sampling strategy subsection to Phase 1
- Consider making plan generation a separate stage (`--plan` flag) so recommendations can be generated first, then the plan in fresh context

---

#### C2. Restructure implement-plan Loop to Shed State

**Priority:** High
**Effort:** M
**Impact:** Command remains coherent through 30+ work items instead of degrading

**Current State:**
The "thin loop controller" pattern is correct in principle but violated in practice. The STARTUP subagent returns all remaining work items. Every NEXT ITERATION subagent re-reads the entire plan and returns remaining items. Each implementation/testing/documentation subagent returns summaries that accumulate in conversation. By work item 30, the main agent holds: startup inventory + 30 subagent returns + 30 commit confirmations + 30 TaskUpdate calls + several iteration checks.

**Recommendation:**
(1) STARTUP returns only the first phase's items, not everything. (2) NEXT ITERATION returns only the immediate next item or parallel batch, not all remaining. (3) Use a lightweight state file (`.implement-plan-state.json`) as the sole progress mechanism rather than conversational memory. (4) After every 5 work items, explicitly summarize and discard prior subagent results.

**Implementation Notes:**
- State file format: `{ "current_phase": 2, "current_item": "2.3", "completed": ["1.1", "1.2", ...], "project_context": { "tech_stack": "...", "test_command": "..." } }`
- Main agent reads state file at each iteration rather than accumulating conversation
- NEXT ITERATION subagent writes to state file rather than returning full lists

---

#### C3. Make plan-improvements Two-Stage Output Optional

**Priority:** Medium
**Effort:** S
**Impact:** Graceful degradation for large codebases; prevents losing recommendations when plan generation fails

**Current State:**
The command generates both RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md in a single pass. On large codebases, context pressure degrades the quality of later output (Risk Mitigation, Parallel Work tables, final phases). If the session is interrupted, everything is lost.

**Recommendation:**
Add a `--recommendations-only` flag (or `--no-plan`) that generates just RECOMMENDATIONS.md and stops. Add graceful degradation: if context pressure is detected during plan generation, save RECOMMENDATIONS.md immediately and suggest running `/create-plan RECOMMENDATIONS.md` in fresh context.

**Implementation Notes:**
- Default behavior remains unchanged (both files)
- Add early save of RECOMMENDATIONS.md before plan generation begins
- `/create-plan` should accept RECOMMENDATIONS.md as a "requirements document" via its document discovery

---

### Category 4: Analysis Quality (A)

#### A1. Add Missing Analysis Dimensions to plan-improvements

**Priority:** High
**Effort:** S
**Impact:** Analysis catches security, performance, dependency, and CI/CD issues instead of missing them entirely

**Current State:**
`/plan-improvements` analyzes 5 dimensions: Usability, Output Quality, Architecture & Design, Developer Experience, Missing Capabilities. `/review-arch` analyzes 6 different dimensions: Structure & Organization, Code Quality Patterns, Security Posture, Testability & Reliability, Performance & Scalability, Developer Experience. The plan-improvements command — which is supposed to be more thorough — misses Security, Performance, Dependencies, and CI/CD entirely.

**Recommendation:**
Add as first-class analysis dimensions: Security Posture (hardcoded secrets, input validation, auth patterns, dependency CVEs), Performance (N+1 queries, blocking ops, caching, resource cleanup), Dependency Health (outdated deps, floating versions, license compliance, transitive vulnerabilities), CI/CD Pipeline (build health, coverage enforcement, quality gates). Port the specific analysis patterns from `/review-arch`.

**Implementation Notes:**
- Add 4 new subsections under Phase 1
- Expand recommendation categories to be dynamic (3-7 based on findings) rather than fixed at 5
- Rename existing categories to match what the analysis actually found, not hardcoded names

---

#### A2. Define Priority Rubric for plan-improvements

**Priority:** High
**Effort:** XS
**Impact:** Priority assignments become consistent and defensible rather than subjective

**Current State:**
Priority levels (Critical/High/Medium/Low) are listed in the recommendation template but never defined. No rubric, no examples, no decision criteria. Two runs on the same codebase could produce completely different priority distributions.

**Recommendation:**
Add explicit definitions: Critical = production outage risk, security vulnerability, or data integrity threat. High = blocks feature development or causes regular developer friction. Medium = improves quality but is not blocking. Low = nice-to-have optimization or style improvement.

**Implementation Notes:**
- Port severity definitions from `/review-arch` Phase 3 (Technical Debt Inventory)
- Add an Impact/Effort matrix instruction to populate the Quick Wins section mechanically

---

#### A3. Replace Question-Based Analysis with Task-Based Analysis

**Priority:** Medium
**Effort:** S
**Impact:** Analysis produces evidence-based findings with file references instead of subjective commentary

**Current State:**
Phase 1 analysis prompts are question-based: "How intuitive is the current workflow?", "Is the code organized logically?", "Are there scalability concerns?". These invite impressionistic paragraphs rather than enumerated findings.

**Recommendation:**
Rewrite as concrete tasks: "Identify the 3 highest-friction user workflows by tracing common operations from entry point to completion. For each, note the number of steps, any redundant operations, and error handling gaps." "Identify all files exceeding 300 lines and flag functions over 50 lines as complexity hotspots."

**Implementation Notes:**
- Rewrite each subsection under Phase 1 with 3-5 specific tasks instead of 4-5 open questions
- Tasks should produce countable, file-referenced findings

---

#### A4. Add Codebase Reconnaissance to create-plan

**Priority:** High
**Effort:** S
**Impact:** Plans account for existing code instead of assuming greenfield; avoids re-planning implemented features

**Current State:**
`/create-plan` reads only requirements documents (BRD, PRD, TDD). It does not examine the existing codebase. This means it generates a greenfield plan for what may be a brownfield project — potentially re-planning features that already exist, ignoring tech debt that will affect implementation, and missing architectural patterns the new code must conform to.

**Recommendation:**
Add a "Codebase Reconnaissance" step between document discovery and requirements analysis. Scan: project structure and tech stack, already-implemented features that overlap with requirements, code quality/patterns to inform approach, test infrastructure and CI/CD configuration.

**Implementation Notes:**
- Add as Phase 1.5 (between document discovery and requirements analysis)
- Keep it lightweight — 5-10 minute scan, not a full `/plan-improvements` analysis
- Flag overlapping features: "PRD section 2.3 describes user authentication — the project already has `src/auth/` with JWT-based auth. Plan should extend, not rebuild."

---

### Category 5: User Experience & Guardrails (U)

#### U1. Add Confirmation Checkpoint to create-plan

**Priority:** High
**Effort:** S
**Impact:** User can redirect scope before 4-15 minutes of plan generation; prevents wasted effort

**Current State:**
After discovering documents and resolving conflicts, `/create-plan` proceeds directly to plan generation with no approval gate. Key decisions are made without user input: number of phases, scope boundaries, priority inferences, implementation approach for ambiguous requirements.

**Recommendation:**
Add a checkpoint after Phase 2 (Requirements Analysis) presenting: extracted feature list with proposed priorities, proposed phase count and rough grouping, scoping assumptions. Ask user to approve before proceeding to full plan generation.

**Implementation Notes:**
- Present a compact summary (not the full analysis)
- Offer: "Proceed with this scope? (yes/adjust/abort)"
- This is analogous to how `/plan-improvements` generates RECOMMENDATIONS.md as a review artifact

---

#### U2. Change implement-plan Default to PR-Only (No Auto-Merge)

**Priority:** High
**Effort:** XS
**Impact:** Prevents autonomous merge of potentially hours of unreviewed changes; aligns with pipeline's emphasis on user confirmation at decision points

**Current State:**
Finalization Step 2 automatically creates a PR, merges it, and deletes the branch. No human review. For a command that may have made 40+ commits across hours of autonomous execution, this is aggressive.

**Recommendation:**
Make PR creation the default (stop and notify user). Add `--auto-merge` flag for opt-in autonomous merge. Generate a descriptive PR title from the actual implementation rather than "Implementation Complete."

**Implementation Notes:**
- Change finalization to: create PR with comprehensive body, output URL, stop
- Add `--auto-merge` flag that preserves current behavior
- Generate PR title: "Implement [Phase 1 title] through [Phase N title]" or similar

---

#### U3. Add Rollback/Checkpoint Capability to implement-plan

**Priority:** High
**Effort:** M
**Impact:** Bad commits can be reverted without restarting the entire plan; essential for 2+ hour autonomous runs

**Current State:**
Each work item is committed immediately. If item 8 of 12 introduces a subtle regression not caught by tests, there is no mechanism to revert. The command only moves forward.

**Recommendation:**
Before each work item, record the commit SHA as a checkpoint. If the testing subagent reports unfixable failures, offer to `git revert` to the checkpoint. Maintain a checkpoint log in the state file so resume can identify the last known-good state.

**Implementation Notes:**
- Record `last_good_sha` in `.implement-plan-state.json` after each successful test pass
- On unfixable test failure: offer revert to `last_good_sha`, skip the item, or pause for manual intervention

---

#### U4. Add Phase Boundary Quality Gates to implement-plan

**Priority:** Medium
**Effort:** S
**Impact:** Validates phase deliverables before building on them; catches drift early

**Current State:**
The command moves between phases silently. Phase 1 ends and Phase 2 begins with no checkpoint. Both planning commands generate per-phase completion checklists — but `/implement-plan` never validates them.

**Recommendation:**
After the last work item in a phase, run a validation subagent that checks the phase's completion checklist and testing requirements. Present a brief phase summary. Optionally pause for user confirmation before proceeding to the next phase.

**Implementation Notes:**
- Read the phase's "Completion Checklist" and "Testing Requirements" from the plan
- Run validation subagent to check each item
- Default: present summary and continue; `--pause-between-phases` flag for interactive mode

---

#### U5. Harden Resume Capability in implement-plan

**Priority:** High
**Effort:** M
**Impact:** Resume after interruption works reliably instead of depending on fragile markdown parsing

**Current State:**
Resume depends on IMPLEMENTATION_PLAN.md having items "marked complete" — but no machine-readable status format is defined. If the command is interrupted between implementation and documentation subagents, work is done but not marked, causing re-implementation on resume.

**Recommendation:**
Define machine-readable status markers in IMPLEMENTATION_PLAN.md: `**Status: COMPLETE [2026-02-28]**` / `**Status: IN_PROGRESS**` / `**Status: PENDING**`. Mark items IN_PROGRESS before implementation starts, not just COMPLETE after. Use `.implement-plan-state.json` as the primary state mechanism. On resume, detect IN_PROGRESS items and offer: retry, skip, or mark complete.

**Implementation Notes:**
- Add Status field to work item schema (both planning commands should generate `**Status: PENDING**`)
- implement-plan updates Status before and after each step
- State file is the ground truth; plan file Status is for human readability

---

### Category 6: Robustness & Edge Cases (R)

#### R1. Add Machine-Readable Markers for Append Logic

**Priority:** Medium
**Effort:** XS
**Impact:** Append operations become deterministic instead of depending on markdown parsing

**Current State:**
Both planning commands have a 10-step append procedure that depends on Claude correctly identifying the "header up to `---` after Phase Summary Table" — but the document has multiple `---` separators. No examples are provided. Cross-references in Parallel Work and Risk tables can become stale during renumbering.

**Recommendation:**
Add `<!-- BEGIN PHASES -->` and `<!-- END PHASES -->` markers to the template. Add `<!-- BEGIN TABLES -->` and `<!-- END TABLES -->` markers. Provide a concrete before/after example of an append operation.

**Implementation Notes:**
- Add markers to the plan template in both commands
- Add a 5-line before/after example in the Append vs Overwrite section
- Also add handling for partially-executed plans: "If some items are marked COMPLETE, preserve them exactly and warn the user"

---

#### R2. Add Circuit Breaker to implement-plan Testing Subagent

**Priority:** Medium
**Effort:** XS
**Impact:** Prevents infinite fix loops from exhausting subagent context and producing incoherent results

**Current State:**
The testing subagent prompt says "Repeat until ALL tests pass" with no explicit iteration limit. The error handling section mentions ">10 iterations" as abnormal, but this is observational guidance for the user, not enforcement in the subagent prompt.

**Recommendation:**
Add to the testing subagent prompt: "If after 3 fix-and-rerun cycles tests still fail, stop and return: TESTS_STUCK, list of remaining failures, what was tried." The main agent should then pause and ask the user for guidance.

**Implementation Notes:**
- Modify both sequential (Step A2) and parallel (Step B3) testing prompts
- Define structured return format: `TESTS_STUCK: [failure list]`

---

#### R3. Add Subagent Project Context Header

**Priority:** Medium
**Effort:** S
**Impact:** Subagents write code matching project conventions instead of guessing; reduces consistency issues across long plan execution

**Current State:**
Implementation subagent prompts contain only: "Read IMPLEMENTATION_PLAN.md. Implement work item [X]." No project context — tech stack, test framework, conventions, or what has already been implemented.

**Recommendation:**
Have the STARTUP subagent also extract: tech stack/language, test command, key conventions from CLAUDE.md, build command. Include this as a "Project Context" header (~200 tokens) in every implementation subagent prompt.

**Implementation Notes:**
- Add to STARTUP prompt: "Also return: tech stack, test command (`npm test`/`pytest`/etc.), and 3-5 key conventions from CLAUDE.md"
- Store in `.implement-plan-state.json` under `project_context`
- Prepend to every implementation/testing subagent prompt

---

#### R4. Reduce Documentation Overhead in implement-plan

**Priority:** Medium
**Effort:** S
**Impact:** Removes 33% of subagent invocations per work item; reduces overhead without losing tracking

**Current State:**
Every work item triggers 3 subagent types: implementation, testing, documentation. The documentation subagent reads 3 files and writes to 3 files (IMPLEMENTATION_PLAN.md, PROGRESS.md, LEARNINGS.md). For a 20-item plan, that's 20 extra subagent spawns. PROGRESS.md largely duplicates `git log --oneline`. LEARNINGS.md entries are often "No issues encountered."

**Recommendation:**
Fold documentation updates into the implementation subagent prompt: "When complete, also update IMPLEMENTATION_PLAN.md to mark this item complete with today's date." Make PROGRESS.md optional (only generate if `--progress` flag set). Only update LEARNINGS.md when there are actual learnings (test failures, workarounds).

**Implementation Notes:**
- Add documentation instructions to implementation subagent prompt
- Remove separate documentation subagent (Steps A3 and B4)
- Keep IMPLEMENTATION_PLAN.md updates mandatory; make PROGRESS.md and LEARNINGS.md optional

---

#### R5. Add Parallel Execution Safety Checks

**Priority:** Medium
**Effort:** S
**Impact:** Prevents file conflicts and git index contention during concurrent execution

**Current State:**
Path B launches up to 3 parallel implementation subagents on the same repo. The constraint ("if items touch overlapping files, run sequentially") depends on plan metadata that may be incomplete. On Windows, git index locking and stricter file locking create additional failure modes.

**Recommendation:**
Add post-parallel merge check: after all parallel subagents complete, run `git status` and `git diff` to verify no conflicts. For shared infrastructure files (package.json, config files), always run modifications sequentially. On Windows, reduce max parallel agents to 2 and add index.lock retry handling.

**Implementation Notes:**
- Add conflict check between Step B2 (Collect Results) and Step B3 (Testing)
- Add list of "always-sequential" file patterns: `package.json`, `*.lock`, `tsconfig.json`, `pyproject.toml`
- Add Windows-specific constraint note

---

#### R6. Add allowed-tools to Planning Commands

**Priority:** Medium
**Effort:** XS
**Impact:** Prevents planning commands from accidentally modifying code or running shell commands

**Current State:**
Neither `/create-plan` nor `/plan-improvements` declares `allowed-tools`. Both commands should only read files and write output documents.

**Recommendation:**
Add `allowed-tools` to both: `Read, Glob, Grep, Write, Edit, Agent` — limiting to file operations and subagent delegation. No Bash access needed for planning.

**Implementation Notes:**
- Add to frontmatter of both commands
- Test that Agent tool is allowed (needed if commands ever delegate analysis to subagents)

---

#### R7. Add Plan Size Limits

**Priority:** Low
**Effort:** XS
**Impact:** Prevents generation of plans too large for `/implement-plan` to execute in a single session

**Current State:**
No upper bound on phases or work items. A 20-phase plan with 60+ work items will overwhelm `/implement-plan`'s context window and run for hours.

**Recommendation:**
Default max 8 phases per plan. If the scope requires more, suggest splitting into multiple plans (`IMPLEMENTATION_PLAN_part1.md`, `IMPLEMENTATION_PLAN_part2.md`). Add `--max-phases <n>` flag to both planning commands.

**Implementation Notes:**
- Add check after phase construction: "If phases > 8, warn and suggest splitting"
- `/implement-plan` should also accept an `--input <path>` argument to support non-default plan filenames

---

#### R8. Improve Not Recommended Section in plan-improvements

**Priority:** Low
**Effort:** XS
**Impact:** Prevents "why didn't you recommend X?" loops; documents rejected alternatives with rationale

**Current State:**
The "Not Recommended" section says "[Items considered but rejected, with rationale]" with no structure, no template per item, and no minimum count.

**Recommendation:**
Provide a template per item: Title, Why Considered, Why Rejected (specific rationale), Conditions for Reconsideration. Require at least 3 items — if fewer than 3 things were considered and rejected, the analysis wasn't thorough enough.

**Implementation Notes:**
- Add structured template to RECOMMENDATIONS.md template
- Add instruction: "Include at least 3 not-recommended items"

---

## Quick Wins

1. **S3** — Standardize phase sizing parameters (XS effort, eliminates confusion)
2. **S4** — Replace token estimates with concrete heuristics (S effort, major accuracy improvement)
3. **A2** — Define priority rubric (XS effort, critical for consistency)
4. **T2** — Expand implement-plan allowed-tools (XS effort, may fix tool access)
5. **U2** — Change implement-plan to PR-only default (XS effort, safety improvement)
6. **R1** — Add append logic markers (XS effort, deterministic append)
7. **R2** — Add testing circuit breaker (XS effort, prevents infinite loops)
8. **R6** — Add allowed-tools to planning commands (XS effort, safety)
9. **R7** — Add plan size limits (XS effort, prevents overwhelming executor)
10. **R8** — Improve Not Recommended section (XS effort, quality)

---

## Strategic Initiatives

1. **T1 + T2 + T3** — Fix implement-plan tool API and permissions (Critical, makes the command functional)
2. **S1 + S2** — Unify IMPLEMENTATION_PLAN.md schema (Critical, enables consistent execution)
3. **C1 + C2 + C3** — Context window management across entire pipeline (High, reliability)
4. **U3 + U5** — Rollback and resume hardening (High, essential for long-running execution)
5. **A1 + A3 + A4** — Analysis quality improvements (High, better recommendations)

---

## Not Recommended

### NR1. Split implement-plan Into Separate Per-Phase Commands

**Why Considered:** Running one phase at a time would simplify state management and avoid context window pressure.
**Why Rejected:** The orchestration loop is the right architecture — it just needs the state management fixed. Forcing users to manually invoke each phase loses the "run and walk away" value proposition. The state file approach (C2) solves the context problem without fragmenting the command.
**Reconsider If:** Context window limits prove impossible to work around even with state files.

### NR2. Merge create-plan and plan-improvements Into One Command

**Why Considered:** Maintaining two planning commands that produce the same output format creates ongoing synchronization burden.
**Why Rejected:** They serve genuinely different use cases — one is requirements-driven, the other is codebase-driven. A unified command would need complex mode switching that is harder to maintain than two focused commands. The shared schema (S1, S2) reduces the synchronization burden to acceptable levels.
**Reconsider If:** A third planning command is proposed — at that point, extract the shared schema into a reference template file.

### NR3. Add Real-Time Progress Streaming to implement-plan

**Why Considered:** Users waiting 1-2 hours with no feedback is poor UX.
**Why Rejected:** The TaskCreate/TaskUpdate mechanism already provides progress visibility. Adding streaming would require fundamental changes to the subagent architecture. The state file approach plus task list provides sufficient visibility.
**Reconsider If:** Claude Code adds native progress reporting hooks.

---

*Recommendations generated by Claude on 2026-02-28T14:30:00*
