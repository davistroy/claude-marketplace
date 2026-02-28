---
description: Analyze codebase and generate prioritized improvement recommendations with phased implementation plan
allowed-tools: Read, Glob, Grep, Write, Edit, Agent
---

# Plan Improvements Command

Perform a comprehensive analysis of the current codebase to identify improvement opportunities, then generate detailed recommendations and a phased implementation plan.

## Optional Arguments

| Argument | Alias | Description |
|----------|-------|-------------|
| `--recommendations-only` | `--no-plan` | Stop after generating RECOMMENDATIONS.md — skip implementation plan generation. Enables a two-stage workflow where you review/edit recommendations before running `/create-plan RECOMMENDATIONS.md` to generate the plan. |
| `--max-phases <n>` | | Maximum number of phases to generate (default: 8). If analysis yields more phases than this limit, group related items to stay within bounds or suggest splitting into multiple plan files. |

**Argument detection:** Check if the user's message includes `--recommendations-only` or `--no-plan`. If either is present, set the internal flag `RECOMMENDATIONS_ONLY = true`. Otherwise, `RECOMMENDATIONS_ONLY = false`. Check for `--max-phases <n>` and set `MAX_PHASES` accordingly (default: 8).

## Input Validation

Before proceeding, verify:
- This is a code project with meaningful source files (not empty or purely documentation)
- The repository structure is readable and accessible
- There is sufficient existing code to analyze for improvements

For trivial projects or fresh repositories, ask the user if they want a full improvement plan or just architectural guidance.

## Instructions

### Phase 1: Deep Codebase Analysis (Ultrathink)

Thoroughly analyze the codebase with extended thinking enabled.

#### Context Management (Read This First)

Before reading any source files, apply the following sampling strategy to avoid exhausting the context window. **Reserve at least 40% of context for output generation.** If analysis has consumed over 60% of available context, stop reading files and begin generating output with what you have.

**Threshold rule:** For codebases with fewer than 100 source files, full analysis is fine — read everything. For codebases over 100 files, use the sampling strategy below.

**Sampling strategy (priority order):**

1. **Always read — config and metadata files:** `package.json`, `pyproject.toml`, `Cargo.toml`, `tsconfig.json`, `.eslintrc.*`, `Makefile`, `Dockerfile`, CI configs, and any project-level `CLAUDE.md` or `README.md`. These are small and define the project's shape.
2. **Always read — entry points and public API surfaces:** `main.*`, `index.*`, `app.*`, route definitions, exported module interfaces, CLI entry points. These reveal architecture without reading internals.
3. **Sample 2-3 representative files per module/directory:** Pick one well-structured file (to understand conventions), one complex file (to find pain points), and optionally one test file (to assess coverage patterns). Use file size and modification recency as selection heuristics — recently modified large files are highest signal.
4. **Deep-read only flagged files:** Files identified as high-complexity, high-churn, or problematic during steps 1-3. Do not deep-read speculatively.
5. **Use Glob/Grep for broad patterns:** Instead of reading every file, use `Glob` to count files per directory and `Grep` to search for specific patterns (e.g., `TODO`, `FIXME`, deprecated API usage, duplicated code signatures). This gives coverage without consuming context.

**What to skip:** Generated files (`dist/`, `build/`, `node_modules/`, `*.min.js`), vendored dependencies, lock files, large data fixtures, and binary assets. These consume context without informing recommendations.

**Codebase size estimation:** At the start of analysis, run a quick `Glob` pass to count source files by extension and estimate total codebase size. Report the count to yourself and decide sampling vs. full-read before proceeding.

Focus on:

#### Usability Assessment
- Trace the 3 most common user workflows from entry point to completion. For each, count the number of steps, identify any redundant or unnecessary operations, and note where error handling is missing or unhelpful.
- Locate all user-facing error messages (catch blocks, validation failures, CLI output). Classify each as actionable ("File not found: expected config.json at /path") vs. opaque ("Something went wrong"). Count the ratio.
- List every configuration option and its discovery path. Flag options that require reading source code to understand, lack defaults, or have no documentation.
- Identify all points where the user must provide input or make a decision. For each, assess whether the prompt is clear, whether defaults are sensible, and whether invalid input is handled gracefully.

#### Output Quality Assessment
- Generate or trace sample output from 3 representative inputs (one minimal, one typical, one edge-case). Compare each against professional standards for the output type. Note format inconsistencies, missing sections, or degraded quality.
- Identify all output templates, format strings, or generation patterns. Check for consistency: do all outputs use the same date format, naming convention, section structure, and style?
- List all validation or quality checks applied to output before it is saved or displayed. Flag any output path that writes results without validation.
- Find 3 edge cases that produce poor, empty, or malformed output. Document the input, the actual output, and what the expected output should be.

#### Architecture & Design
- Map the dependency graph between top-level modules or directories. Identify circular dependencies and modules with more than 5 direct dependents.
- List all files exceeding 300 lines. For each, identify whether the length is justified (e.g., generated code, data tables) or indicates a need to split.
- Flag all functions or methods exceeding 50 lines as complexity hotspots. Note the file path and function name.
- Identify all `catch`/`except`/error-handling blocks that swallow errors silently (no re-throw, no logging, no user notification). Count them and list locations.
- Check for consistent application of patterns: if the codebase uses a pattern (e.g., factory, middleware, plugin), verify it is applied uniformly. List any deviations.

#### Developer Experience
- Execute the "add a new feature" workflow: determine what files must be created or modified, what conventions must be followed, and what documentation must be updated. Note every undocumented convention a new contributor would miss.
- Check for a contributing guide, code style documentation, and example implementations. Assess completeness — can a new developer ship a feature using only the documentation?
- Identify all testing patterns: unit tests, integration tests, end-to-end tests. Count coverage by module. Flag modules with zero test coverage.
- List all manual steps required for common development tasks (build, test, lint, deploy). Flag any that could be automated but are not.

#### Missing Capabilities
- Build a capabilities checklist appropriate for this project type and compare against the codebase. For CLI tools: help system, verbose/quiet modes, config file support, meaningful exit codes, shell completion, version flag. For web apps: error pages, loading states, accessibility (WCAG), responsive design. For libraries: API documentation, usage examples, changelog, type definitions.
- Identify 3-5 features that comparable projects in the ecosystem provide but this project lacks. Reference specific projects where possible.
- List all manual or repetitive tasks in the project's workflow that could be automated (e.g., release process, changelog generation, dependency updates, code generation).

#### Security Posture
- Scan for hardcoded secrets, API keys, tokens, or credentials in source files (check `.env` files committed to version control, config files with inline secrets, string literals matching key patterns)
- Assess input validation gaps: identify user-facing inputs (CLI args, HTTP params, file uploads) that lack sanitization or type checking
- Review authentication and authorization patterns: are protected routes/endpoints enforced consistently? Are there privilege escalation paths?
- Check for dependency CVEs: run `npm audit`, `pip-audit`, `cargo audit`, or equivalent if the tooling is available; otherwise note the absence of audit tooling
- Identify unsafe patterns: `eval()`, SQL string concatenation, shell injection via unsanitized interpolation, disabled TLS verification

#### Performance & Scalability
- Identify N+1 query patterns: look for database calls inside loops, repeated API requests that could be batched, sequential awaits that could be parallelized
- Flag blocking operations in async contexts: synchronous file I/O, CPU-heavy computation on the event loop, missing `await` on promises
- Assess caching: are there repeated expensive computations or API calls without caching? Is there a caching layer and is it invalidated correctly?
- Check resource cleanup: unclosed file handles, database connections, event listeners that accumulate without removal
- Review memory management: unbounded collections that grow with input size, large objects retained beyond their useful lifetime, missing pagination on large result sets

#### Dependency Health
- Check for outdated dependencies: compare installed versions against latest stable releases. Flag any dependency more than 2 major versions behind.
- Assess version pinning: are dependencies pinned to exact versions or using floating ranges? Is there a lock file (`package-lock.json`, `poetry.lock`, `Cargo.lock`) and is it committed?
- Review license compliance: identify dependencies with copyleft licenses (GPL, AGPL) that may conflict with the project's license
- Check for transitive vulnerability exposure: identify dependencies that pull in known-vulnerable transitive dependencies
- Flag abandoned dependencies: packages with no releases in 2+ years or archived repositories

#### CI/CD Pipeline
- Assess build pipeline completeness: is there a CI configuration (GitHub Actions, GitLab CI, etc.)? Does it run on PRs and on merge to main?
- Check test coverage enforcement: is there a coverage threshold configured? Does CI fail on coverage regression?
- Review quality gates: linting, type checking, security scanning — which are present and which are missing from the pipeline?
- Evaluate deployment complexity: how many manual steps are required to deploy? Is there a staging environment? Are rollbacks automated?
- Check for environment parity: do dev, test, and production configurations diverge in ways that cause "works on my machine" failures?

### Priority Rubric

When assigning **Priority** to each recommendation, apply these definitions consistently. Definitions are ported from `/review-arch` Phase 3 (Technical Debt Inventory) for cross-command consistency.

| Priority | Definition | Examples |
|----------|-----------|----------|
| **Critical** | Security vulnerability, data integrity risk, or production stability threat. Fix before shipping anything else. | Hardcoded secrets in source, SQL injection, unhandled crash in core path, data loss on edge case |
| **High** | Architectural violation or gap that blocks feature development or causes regular developer friction. Should be addressed in the current planning cycle. | Missing validation causing repeated bugs, circular dependency blocking refactoring, broken CI pipeline |
| **Medium** | Code quality issue that slows velocity but does not block work. Address when touching affected code or in a dedicated quality sprint. | Inconsistent naming conventions, duplicated logic across modules, missing test coverage for non-critical paths |
| **Low** | Nice-to-have optimization, style improvement, or minor inconsistency. Address opportunistically or batch into a polish phase. | Minor code style inconsistencies, optional performance micro-optimizations, cosmetic UI tweaks |

**Effort scale reference:**

| Effort | Time Estimate | Scope |
|--------|---------------|-------|
| **XS** | < 30 min | Single-line fix, config change, typo |
| **S** | 30 min – 2 hrs | Single-file change, small refactor |
| **M** | 2 hrs – 1 day | Multi-file change, new feature with tests |
| **L** | 1 – 3 days | Cross-module refactor, significant new capability |
| **XL** | 3+ days | Architectural change, migration, major new system |

### Impact/Effort Matrix

After categorizing all recommendations, plot each one on the following 2x2 Impact vs Effort matrix. Use this matrix to mechanically populate the Quick Wins and Strategic Initiatives sections — do not populate those sections by ad-hoc judgment.

```
                    HIGH IMPACT
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     │   QUICK WINS     │   STRATEGIC      │
     │   (Do First)     │   INITIATIVES    │
     │                  │   (Plan Carefully)│
     │   High Impact    │   High Impact    │
     │   Low Effort     │   High Effort    │
     │   (XS, S, M)     │   (L, XL)        │
     │                  │                  │
─────┼──────────────────┼──────────────────┼───── EFFORT
     │                  │                  │
     │   FILL-INS       │   DEPRIORITIZE   │
     │   (Batch Later)  │   (Reconsider)   │
     │                  │                  │
     │   Low Impact     │   Low Impact     │
     │   Low Effort     │   High Effort    │
     │   (XS, S, M)     │   (L, XL)        │
     │                  │                  │
     └──────────────────┼──────────────────┘
                        │
                    LOW IMPACT
```

**Quadrant-to-section mapping:**

| Quadrant | Priority + Effort | Populates Section |
|----------|-------------------|-------------------|
| Quick Wins | Critical/High impact + XS/S/M effort | `## Quick Wins` |
| Strategic Initiatives | Critical/High impact + L/XL effort | `## Strategic Initiatives` |
| Fill-Ins | Medium/Low impact + XS/S/M effort | Include in phased plan, batch into polish phases |
| Deprioritize | Medium/Low impact + L/XL effort | Candidates for `## Not Recommended` or defer indefinitely |

**Impact assessment criteria** (use to determine High vs Low Impact):
- **High Impact**: Fixes a Critical/High priority issue, OR affects >50% of users/workflows, OR unblocks multiple downstream improvements
- **Low Impact**: Fixes a Medium/Low priority issue AND affects a narrow use case AND has no downstream dependencies

**Instructions:**
1. After writing all recommendations with their Priority and Effort ratings, classify each into one of the four quadrants
2. Populate `## Quick Wins` with all items from the Quick Wins quadrant, ordered by Priority (Critical first) then Effort (XS first)
3. Populate `## Strategic Initiatives` with all items from the Strategic Initiatives quadrant, ordered by Priority then dependency order
4. Items in the Fill-Ins quadrant go into the implementation plan phases but are not highlighted in Quick Wins or Strategic Initiatives
5. Items in the Deprioritize quadrant should be evaluated for the `## Not Recommended` section

### Phase 2: Generate RECOMMENDATIONS.md

Create a comprehensive recommendations document with this structure:

```markdown
# Improvement Recommendations

**Generated:** [YYYY-MM-DD HH:MM:SS]
**Analyzed Project:** [project name/path]

---

## Executive Summary

[2-3 paragraph overview of key findings and highest-impact recommendations]

---

## Recommendation Categories

Use 3-7 categories derived from actual findings. The categories below are starting suggestions, not a rigid structure. Add Security, Performance, CI/CD, or Dependency Health categories when findings warrant them. Omit categories with no findings.

**Category prefix mapping for recommendation IDs:**

| Prefix | Category |
|--------|----------|
| U | Usability Improvements |
| Q | Output Quality Enhancements |
| A | Architectural Improvements |
| D | Developer Experience |
| N | New Capabilities |
| S | Security |
| P | Performance |
| CI | CI/CD Pipeline |
| DH | Dependency Health |

### Category: Usability Improvements

#### U1. [Recommendation Title]

**Priority:** Critical | High | Medium | Low
**Effort:** XS | S | M | L | XL
**Impact:** [Description of benefit]

**Current State:**
[What exists now and why it's problematic]

**Recommendation:**
[Specific, actionable improvement]

**Implementation Notes:**
[Technical considerations, dependencies, risks]

---

### Category: Output Quality Enhancements

#### Q1. [Recommendation Title]
...

---

### Category: Architectural Improvements

#### A1. [Recommendation Title]
...

---

### Category: Developer Experience

#### D1. [Recommendation Title]
...

---

### Category: New Capabilities

#### N1. [Recommendation Title]
...

---

### Category: Security

#### S1. [Recommendation Title]
...

---

### Category: Performance

#### P1. [Recommendation Title]
...

---

### Category: CI/CD Pipeline

#### CI1. [Recommendation Title]
...

---

### Category: Dependency Health

#### DH1. [Recommendation Title]
...

---

## Quick Wins

Populated mechanically from the Impact/Effort matrix — High-Impact/Low-Effort quadrant (Critical/High priority items with XS/S/M effort). Order by Priority (Critical first), then by Effort (XS first). Each entry should reference the recommendation ID and include a one-line summary.

| Ref | Recommendation | Priority | Effort | Why Quick Win |
|-----|---------------|----------|--------|---------------|
| [U1] | [Title] | Critical | S | [One-line rationale] |
| ... | ... | ... | ... | ... |

---

## Strategic Initiatives

Populated mechanically from the Impact/Effort matrix — High-Impact/High-Effort quadrant (Critical/High priority items with L/XL effort). Order by Priority, then by dependency order (items that unblock others first). Each entry should include sequencing rationale.

| Ref | Recommendation | Priority | Effort | Dependencies / Sequencing |
|-----|---------------|----------|--------|---------------------------|
| [A1] | [Title] | Critical | L | [Why this order, what it unblocks] |
| ... | ... | ... | ... | ... |

---

## Not Recommended

Include a minimum of 3 items. Every non-trivial analysis should identify at least 3 approaches that were considered and rejected — this prevents future revisiting and documents decision rationale.

For each rejected item, use this template:

### [NR-1] [Item Title]

**Why Considered:** [What made this seem like a viable improvement]
**Why Rejected:** [Specific reason it was rejected — cost/benefit, architectural conflict, better alternative exists, premature optimization, etc.]
**Conditions for Reconsideration:** [What would need to change for this to become worth doing — e.g., "If codebase exceeds 500 files", "If team grows beyond 3 developers", "If performance benchmarks show >2s response time"]

---

### [NR-2] [Item Title]
...

### [NR-3] [Item Title]
...

---

*Recommendations generated by Claude on [YYYY-MM-DD HH:MM:SS]*
```

### Phase 2→3 Transition: Save Recommendations Early

**Before beginning Phase 3, save RECOMMENDATIONS.md to disk immediately.** This ensures recommendations are preserved if the session is interrupted during plan generation or if context pressure causes issues.

1. Write RECOMMENDATIONS.md to the repository root
2. Confirm the file was written successfully

**If `RECOMMENDATIONS_ONLY` is true:** Skip Phase 3 entirely and proceed directly to Phase 4 (Save and Report). The summary report will omit plan details and instead guide the user to generate a plan separately.

### Phase 3: Generate IMPLEMENTATION_PLAN.md

#### Append vs Overwrite Logic

**Before writing, check if IMPLEMENTATION_PLAN.md already exists.**

- **If the file does NOT exist:** Create it fresh with the full structure below.
- **If the file DOES exist:**
  1. Read the existing file
  2. Locate the machine-readable markers to find insertion points:
     - `<!-- BEGIN PHASES -->` / `<!-- END PHASES -->` — bracket all phase sections
     - `<!-- BEGIN TABLES -->` / `<!-- END TABLES -->` — bracket the trailing tables (Parallel Work, Risk Mitigation, Success Metrics, Traceability)
  3. Identify the highest existing phase number (e.g., if Phase 4 is the last, new phases start at Phase 5)
  4. Renumber all new phases to continue from the highest existing phase
  5. Renumber all new work items accordingly (e.g., 5.1, 5.2, 6.1...)
  6. Insert the new phases immediately before `<!-- END PHASES -->`, preceded by a separator comment: `<!-- Appended on [YYYY-MM-DD HH:MM:SS] from /plan-improvements -->`
  7. Update the Phase Summary Table to include both old and new phases
  8. Update the total phase count, estimated total effort, and any metadata in the header
  9. Append new entries to the tables between `<!-- BEGIN TABLES -->` and `<!-- END TABLES -->` (Parallel Work Opportunities, Risk Mitigation, Success Metrics, Traceability)
  10. **Partially-executed plans:** If any existing items have `Status: COMPLETE` or `Status: IN_PROGRESS`, preserve them exactly as-is. Warn the user: `"This plan has items in progress. New phases will be appended after existing content."`

**Tell the user what happened:**
```text
Existing IMPLEMENTATION_PLAN.md found with [N] phases.
Appending [M] new phases (Phase [N+1] through Phase [N+M]).
```

**Append Example — Before & After:**

*Before (existing 3-phase plan):*
```markdown
<!-- BEGIN PHASES -->

## Phase 1: Foundation
...
## Phase 2: Core Features
...
## Phase 3: Integration
...

<!-- END PHASES -->

<!-- BEGIN TABLES -->

## Parallel Work Opportunities
| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2 | Independent modules |

...
<!-- END TABLES -->
```

*After (2 new phases appended):*
```markdown
<!-- BEGIN PHASES -->

## Phase 1: Foundation
...
## Phase 2: Core Features
...
## Phase 3: Integration
...

<!-- Appended on 2026-02-28 14:30:00 from /plan-improvements -->

## Phase 4: Error Handling
...
## Phase 5: Polish
...

<!-- END PHASES -->

<!-- BEGIN TABLES -->

## Parallel Work Opportunities
| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2 | Independent modules |
| 4.1 | 4.2 | New independent items |

...
<!-- END TABLES -->
```

Transform recommendations into an actionable, phased implementation plan:

```markdown
# Implementation Plan

**Generated:** [YYYY-MM-DD HH:MM:SS]
**Based On:** RECOMMENDATIONS.md
**Total Phases:** [N]
**Estimated Total Effort:** ~[X] LOC across [Y] files

---

## Executive Summary

[2-3 paragraph overview of what will be changed, key improvement themes, and implementation strategy]

---

## Plan Overview

[Summary of the implementation strategy and phasing rationale]

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | [Area] | [Deliverables] | M (~N files, ~N LOC) | None |
| 2 | [Area] | [Deliverables] | M (~N files, ~N LOC) | Phase 1 |
| ... | ... | ... | ... | ... |

<!-- BEGIN PHASES -->

---

## Phase 1: [Phase Title]

**Estimated Complexity:** [S/M/L] (~N files, ~N LOC)
**Dependencies:** [None | List of phases]
**Parallelizable:** [Yes/No - can work items run concurrently]

### Goals
- [Goal 1]
- [Goal 2]

### Work Items

#### 1.1 [Task Title]
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: PENDING**
**Recommendation Ref:** [U1, A2, etc.]
**Files Affected:**
- `path/to/file1.ext` (create)
- `path/to/file2.ext` (modify)

**Description:**
[Detailed task description]

**Tasks:**
1. [ ] [Specific task 1 with enough detail to execute]
2. [ ] [Specific task 2 with enough detail to execute]
3. [ ] [Specific task 3 with enough detail to execute]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Notes:**
[Any additional context, gotchas, or implementation hints]

---

#### 1.2 [Task Title]
...

### Phase 1 Testing Requirements

- [ ] [Specific test requirement 1]
- [ ] [Specific test requirement 2]
- [ ] All new code has >80% test coverage
- [ ] Integration tests pass

### Phase 1 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No regressions introduced
- [ ] Code reviewed (if applicable)

---

## Phase 2: [Phase Title]
...

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

[Identify which phases or work items can be executed concurrently]

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 1.1 | Phase 1.2 | [Why these are independent] |
| ... | ... | ... |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [Strategy] |
| [Risk 2] | Low/Med/High | Low/Med/High | [Strategy] |

---

## Success Metrics

[How to measure overall success of the implementation]

- [ ] All phases completed
- [ ] All acceptance criteria met
- [ ] [Impact metric 1 from recommendations]
- [ ] [Impact metric 2 from recommendations]

---

## Appendix: Recommendation Traceability

| Recommendation | Source | Phase | Work Item |
|----------------|--------|-------|-----------|
| [U1] | RECOMMENDATIONS.md | 1 | 1.1 |
| [A2] | RECOMMENDATIONS.md | 1 | 1.2 |
| ... | ... | ... | ... |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on [YYYY-MM-DD HH:MM:SS]*
*Source: /plan-improvements command*
```

#### Work Item Construction Guidelines

For each work item, generate all seven fields in this order:

1. **Status** — always `PENDING` when generating the plan. Updated by `/implement-plan` during execution (PENDING → IN_PROGRESS → COMPLETE [YYYY-MM-DD]).
2. **Recommendation Ref** — the recommendation ID(s) from RECOMMENDATIONS.md (e.g., U1, A2)
3. **Files Affected** — list with `(create)` or `(modify)` annotations per file
4. **Description** — detailed explanation of the change and why it matters
5. **Tasks** — numbered checkbox list of specific, actionable sub-steps that an implementer can execute sequentially. Each task should be concrete enough to complete without further decomposition. Include testing and documentation tasks.
6. **Acceptance Criteria** — measurable conditions that verify the work item is done
7. **Notes** — optional context, gotchas, dependencies, or implementation hints. Omit if there is nothing noteworthy to add.

### Phase Sizing Guidelines

Each phase should be completable by a single subagent session. Use these concrete heuristics:

**Per-phase guidelines:**
- Read 5-8 files, modify 3-5 files, change ~500 LOC
- Have clear boundaries and deliverables
- Be independently testable
- Not leave the codebase in a broken state if stopped mid-plan
- Enable parallel work where possible
- If a phase exceeds these bounds, split it

**Complexity scale:**
| Size | Files Changed | LOC Changed | Example |
|------|---------------|-------------|---------|
| S | 1-3 files | <100 LOC | Config change, small fix, single file edit |
| M | 3-8 files | 100-500 LOC | Feature with tests, API endpoint, refactoring |
| L | 8-15 files | 500-1500 LOC | Complex feature, major refactoring, integration |

If a phase would be XL (15+ files or 1500+ LOC), split into sub-phases (e.g., Phase 3a, 3b).

**Target:** S-M per phase (max L). Minimum 2 files per phase to avoid trivial phases.

### Plan Size Limits

Plans must stay within bounds that `/implement-plan` can execute reliably. Apply these limits during plan generation:

**Maximum phases:** 8 phases per plan file (configurable via `--max-phases`). If analysis produces more than the limit:
1. Merge related phases to reduce count (prefer cohesion over granularity)
2. If merging is insufficient, split into multiple plan files (e.g., `IMPLEMENTATION_PLAN.md` and `IMPLEMENTATION_PLAN-PHASE2.md`) and inform the user
3. Never silently drop phases or work items to meet the limit

**Maximum work items per phase:** 6 work items. If a phase has more than 6 items, split the phase.

**Work item granularity:** Each work item should touch no more than 5-8 files and change ~500 LOC. If a work item exceeds these bounds, split it into sub-items (e.g., 3.1a, 3.1b) or promote sub-tasks to separate work items.

**Why these limits matter:** `/implement-plan` executes each phase via a subagent with finite context. Oversized plans cause subagents to lose context mid-execution, produce incomplete work, or silently skip items. Smaller, focused phases complete reliably.

### Phase 4: Save and Report

**If `RECOMMENDATIONS_ONLY` is false (default — full mode):**

1. Save RECOMMENDATIONS.md to the repository root (already saved in Phase 2→3 transition; overwrite if updated)
2. Save IMPLEMENTATION_PLAN.md to the repository root
3. Report a summary to the user including:
   - Total recommendations by category and priority
   - Number of phases in the implementation plan
   - Top 3 highest-impact recommendations
   - Suggested starting point

**If `RECOMMENDATIONS_ONLY` is true (recommendations-only mode):**

1. Confirm RECOMMENDATIONS.md was saved (already written in Phase 2→3 transition)
2. Do NOT generate or save IMPLEMENTATION_PLAN.md
3. Report a summary to the user including:
   - Total recommendations by category and priority
   - Top 3 highest-impact recommendations
   - Next-step guidance:
     ```
     To generate an implementation plan from these recommendations, run:
       /create-plan RECOMMENDATIONS.md
     You can edit RECOMMENDATIONS.md first to adjust priorities, remove items, or add context before generating the plan.
     ```

## Execution Guidelines

- **Be thorough**: This analysis informs significant work—miss nothing important
- **Be specific**: Vague recommendations waste time; include file paths, concrete approaches
- **Be realistic**: Estimate effort honestly; overrunning phases causes problems
- **Be practical**: Prioritize impact over elegance; ship value to users
- **Consider context**: Factor in the project's maturity, goals, and constraints
- **Enable parallelism**: Structure phases so multiple streams can work simultaneously when possible
- **Preserve stability**: Each phase should leave the codebase in a working state

## Performance

**Typical Duration:**

| Codebase Size | Expected Time |
|---------------|---------------|
| Small (< 50 files) | 1-2 minutes |
| Medium (50-200 files) | 3-5 minutes |
| Large (200-500 files) | 5-10 minutes |
| Very Large (500+ files) | 10-20 minutes |

**Context Budget:**

| Codebase Size | Analysis Budget | Output Reserve | Sampling? |
|---------------|-----------------|----------------|-----------|
| Small (< 50 files) | ~30K tokens | ~70K tokens | No — full read |
| Medium (50-200 files) | ~50K tokens | ~50K tokens | Yes — sample per module |
| Large (200-500 files) | ~70K tokens | ~30K tokens | Yes — strict sampling |
| Very Large (500+ files) | ~70K tokens | ~30K tokens | Yes — strict sampling + Grep-only for low-priority dirs |

**Factors Affecting Performance:**
- **File count**: More files = longer analysis
- **Code complexity**: Complex interdependencies slow pattern detection
- **Language diversity**: Multiple languages require broader analysis
- **Documentation depth**: Comprehensive recommendations take longer to formulate
- **Context pressure**: Large codebases require sampling; analysis quality depends on good file selection

**Signs of Abnormal Behavior:**
- No output activity after 5 minutes
- Repeated file reading without progress
- Error messages about file access

**If the command seems stuck:**
1. Check for output activity (phase progress indicators)
2. Wait at least 10 minutes for large codebases
3. If no activity, interrupt and try `/review-arch` for a quicker analysis
4. Consider breaking into smaller scope (specific directories)

## Related Commands

- `/create-plan` — Generate implementation plan from requirements documents (complementary planning)
- `/implement-plan` — Execute an IMPLEMENTATION_PLAN.md via orchestrated subagents
- `/plan-next` — Quick recommendation for the next logical action
- `/review-arch` — Lighter-weight architectural audit (read-only, no files generated)
- `/assess-document` — Evaluate document quality before improvement planning

---

## Example Usage

### Full mode (default)

```yaml
User: /plan-improvements

Claude: [Performs deep analysis of the codebase]

I've completed the improvement analysis for claude-marketplace.

**RECOMMENDATIONS.md created** with 23 recommendations across 5 categories:
- Usability: 6 (2 Critical, 2 High, 2 Medium)
- Output Quality: 4 (1 High, 3 Medium)
- Architecture: 5 (1 Critical, 2 High, 2 Medium)
- Developer Experience: 4 (2 High, 2 Low)
- New Capabilities: 4 (1 High, 2 Medium, 1 Low)

**IMPLEMENTATION_PLAN.md created** with 4 phases:
- Phase 1: Foundation (M, ~8 files, ~400 LOC) - Critical fixes and quick wins
- Phase 2: Quality (M, ~6 files, ~300 LOC) - Output improvements
- Phase 3: Architecture (L, ~12 files, ~800 LOC) - Structural refactoring
- Phase 4: Features (M, ~5 files, ~350 LOC) - New capabilities

**Top 3 Highest-Impact Recommendations:**
1. [A1] Standardize command frontmatter validation
2. [U2] Add interactive parameter prompting
3. [Q1] Implement output template system

**Suggested Starting Point:** Phase 1, Item 1.1 - addresses critical stability issue

Files saved:
- RECOMMENDATIONS.md
- IMPLEMENTATION_PLAN.md
```

### Recommendations-only mode

```yaml
User: /plan-improvements --recommendations-only

Claude: [Performs deep analysis of the codebase]

I've completed the improvement analysis for claude-marketplace.

**RECOMMENDATIONS.md created** with 23 recommendations across 5 categories:
- Usability: 6 (2 Critical, 2 High, 2 Medium)
- Output Quality: 4 (1 High, 3 Medium)
- Architecture: 5 (1 Critical, 2 High, 2 Medium)
- Developer Experience: 4 (2 High, 2 Low)
- New Capabilities: 4 (1 High, 2 Medium, 1 Low)

**Top 3 Highest-Impact Recommendations:**
1. [A1] Standardize command frontmatter validation
2. [U2] Add interactive parameter prompting
3. [Q1] Implement output template system

Files saved:
- RECOMMENDATIONS.md

To generate an implementation plan from these recommendations, run:
  /create-plan RECOMMENDATIONS.md
You can edit RECOMMENDATIONS.md first to adjust priorities, remove items,
or add context before generating the plan.
```
