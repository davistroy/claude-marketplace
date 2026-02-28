---
description: Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs)
---

# Create Plan Command

Generate a comprehensive, phased implementation plan from requirements and design documents in the project. This command discovers and analyzes BRDs, PRDs, TDDs, and other specification documents, then produces an actionable IMPLEMENTATION_PLAN.md ready for execution with `/implement-plan`.

## Overview

This command:

1. Discovers requirements and design documents in the project
2. Surveys the existing codebase to detect tech stack, test infrastructure, and already-implemented features
3. Analyzes and synthesizes requirements across all documents, accounting for existing code
4. Presents a scope summary (features, phases, assumptions) and waits for user approval before proceeding
5. Breaks down work into appropriately-sized phases
6. Generates detailed work items with acceptance criteria
7. Outputs IMPLEMENTATION_PLAN.md to the repository root

## Input Validation

**Arguments:** None required

**Optional Arguments:**
- `<document-paths>` - Specific documents to use (space-separated)
- `--output <path>` - Custom output path (default: `IMPLEMENTATION_PLAN.md`)
- `--phases <n>` - Target number of phases (default: auto-calculated)
- `--verbose` - Show detailed analysis during generation

**Examples:**
```text
/create-plan                              # Auto-discover documents
/create-plan PRD.md TDD.md               # Use specific documents
/create-plan --phases 5                   # Target 5 phases
/create-plan docs/requirements/*.md       # Use glob pattern
```

## Instructions

### Phase 1: Document Discovery

#### 1.1 Auto-Discovery Mode

When no documents are specified, search for requirements documents:

**Search patterns (in order of priority):**
```markdown
# Root level
*.md containing "requirements", "specification", "design"
PRD*.md, BRD*.md, TDD*.md, SRS*.md, FRD*.md
requirements.md, spec.md, design.md

# Common directories
docs/*.md
documentation/*.md
specs/*.md
requirements/*.md
design/*.md

# Nested patterns
**/PRD*.md, **/BRD*.md, **/TDD*.md
**/requirements/*.md
**/specs/*.md
```

**Document type detection by content:**
- **BRD (Business Requirements):** Contains "business requirements", "business objectives", "stakeholder", "ROI"
- **PRD (Product Requirements):** Contains "product requirements", "user stories", "features", "acceptance criteria"
- **TDD (Technical Design):** Contains "technical design", "architecture", "API", "database schema", "system design"
- **SRS (Software Requirements Spec):** Contains "software requirements", "functional requirements", "non-functional"
- **FRD (Functional Requirements):** Contains "functional requirements", "use cases", "business rules"

#### 1.2 Explicit Document Mode

When documents are specified as arguments:
1. Verify each file exists
2. Read and classify each document
3. Report any files not found

**Error if no documents found:**
```text
Error: No requirements documents found.

Searched locations:
  - Root directory (PRD*.md, BRD*.md, etc.)
  - docs/, documentation/, specs/, requirements/

To create a plan, provide requirements documents:
  /create-plan path/to/requirements.md
  /create-plan PRD.md TDD.md

Or create a PRD.md file with your requirements.
```

#### 1.3 Document Inventory Report

Display discovered documents before proceeding:

```text
Requirements Documents Found
============================

Business Requirements:
  - docs/BRD-Q1-Initiative.md (2,450 words)

Product Requirements:
  - PRD.md (4,200 words)
  - docs/PRD-Phase2.md (1,800 words)

Technical Design:
  - TDD.md (5,100 words)
  - docs/api-design.md (1,200 words)

Other Specifications:
  - docs/data-model.md (890 words)

Total: 7 documents, ~15,640 words

Proceeding with plan generation...
```

### Phase 1.5: Codebase Reconnaissance

Before analyzing requirements, survey the existing codebase so the plan accounts for what already exists. This prevents greenfield-on-brownfield plans and ensures work items extend rather than rebuild existing functionality.

**Time budget:** 5-10 minutes maximum. This is a lightweight scan, not a full `/plan-improvements` analysis.

#### 1.5.1 Project Structure Scan

Survey the codebase to understand its shape:

1. **Directory tree:** Run `find . -type f -not -path './.git/*' -not -path './node_modules/*' -not -path './.next/*' -not -path './dist/*' -not -path './build/*' -not -path './__pycache__/*' -not -path './venv/*' | head -200` to get a file listing (or equivalent for the platform)
2. **Tech stack detection:** Identify from manifest files:
   - `package.json` → Node.js/JavaScript/TypeScript (check for React, Next.js, Vue, etc.)
   - `pyproject.toml` / `setup.py` / `requirements.txt` → Python
   - `Cargo.toml` → Rust
   - `go.mod` → Go
   - `*.csproj` / `*.sln` → .NET
   - `pom.xml` / `build.gradle` → Java/Kotlin
3. **Entry points:** Identify main entry files (`src/index.*`, `src/main.*`, `app.*`, `__main__.py`, etc.)
4. **Configuration:** Note config files (`.env*`, `*.config.*`, `tsconfig.json`, `eslint.*`, `prettier.*`, `.editorconfig`)

#### 1.5.2 Test & CI/CD Infrastructure

Identify existing quality infrastructure:

1. **Test framework:** Look for test directories (`tests/`, `__tests__/`, `test/`, `spec/`), test config (`jest.config.*`, `pytest.ini`, `vitest.config.*`), and test files (`*.test.*`, `*.spec.*`, `*_test.*`)
2. **Test coverage:** Note approximate test count and whether coverage tooling is configured
3. **CI/CD:** Check for `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`, `azure-pipelines.yml`
4. **Linting/formatting:** Note configured linters and formatters

#### 1.5.3 Existing Feature Cross-Reference

This is the critical step. For each major feature or capability described in the requirements documents:

1. **Search the codebase** for keywords, function names, route paths, component names, or module names that correspond to the requirement
2. **Classify each requirement** as one of:
   - **Not implemented** — No matching code exists; plan from scratch
   - **Partially implemented** — Some code exists but incomplete; plan should extend
   - **Already implemented** — Feature exists and appears functional; plan should verify/skip or enhance
3. **Flag overlaps** clearly in a table:

```text
Codebase Reconnaissance Results
================================

Tech Stack: [detected stack]
Structure: [N] source files, [M] test files, [K] config files
Test Infrastructure: [framework] with [N] tests
CI/CD: [detected pipeline or "None detected"]

Feature Overlap Analysis:
| Requirement | Status | Existing Code | Recommendation |
|-------------|--------|---------------|----------------|
| User auth (PRD §2.1) | Already implemented | src/auth/ (JWT + OAuth) | Skip or enhance |
| Search API (PRD §3.2) | Partially implemented | src/api/search.ts (basic) | Extend, not rebuild |
| Dashboard (PRD §4.1) | Not implemented | — | Plan from scratch |
| Data export (PRD §5.3) | Already implemented | src/export/ | Verify, skip if sufficient |
```

4. **Note architectural patterns** the codebase follows (e.g., MVC, layered architecture, module conventions, naming patterns) so work items conform to existing conventions

#### 1.5.4 Feed Into Plan Generation

The reconnaissance output directly affects subsequent phases:

- **Phase 2 (Requirements Analysis):** Already-implemented features are deprioritized or marked as "verify only"
- **Phase 3 (Phase Planning):** Work items reference existing code paths and follow detected conventions
- **Phase 4 (Generate Plan):** Work item descriptions include "Extend existing `src/auth/` module" rather than "Create authentication system"
- **Complexity estimates** account for existing code (extending is typically S-M; building from scratch is M-L)

**If no meaningful codebase exists** (empty repo, only config files, or only requirements docs), report:

```text
Codebase Reconnaissance: Greenfield project detected.
No existing source code found. Plan will assume fresh implementation.
```

And proceed directly to Phase 2.

### Phase 2: Requirements Analysis

#### 2.1 Extract Key Information

From each document, extract:

**From BRD:**
- Business objectives and success metrics
- Stakeholder requirements
- Constraints and dependencies
- Timeline expectations

**From PRD:**
- Feature list and priorities (P0, P1, P2)
- User stories and acceptance criteria
- UI/UX requirements
- Integration requirements

**From TDD:**
- Architecture decisions
- Technology stack
- API specifications
- Database schema
- System components

**From all documents:**
- Explicit dependencies between features
- Risk factors mentioned
- Performance requirements
- Security requirements

#### 2.2 Synthesize Requirements

Combine information across documents:

1. **Deduplicate:** Identify overlapping requirements
2. **Resolve conflicts:** Flag contradictions for user clarification
3. **Map dependencies:** Create dependency graph of features
4. **Prioritize:** Use explicit priorities or infer from language

#### 2.3 Conflict Detection

If conflicting requirements are found:

```text
⚠️  Requirement Conflicts Detected

Conflict 1:
  PRD.md (line 45): "API response time must be < 100ms"
  TDD.md (line 123): "Batch processing may take up to 5 seconds"

  Resolution needed: Are these different endpoints?

Conflict 2:
  BRD.md: "Launch by Q2"
  PRD.md: "Phase 2 features required for launch"
  TDD.md: "Phase 2 estimated at 8 weeks"

  Resolution needed: Scope or timeline adjustment?

How should I proceed?
  1. Continue with conservative assumptions
  2. Pause for clarification
```

### Phase 2.5: Scope Confirmation

**Before generating the full plan, pause and present a scope summary for user approval.** This checkpoint prevents wasted generation time if the user disagrees with scope, phasing, or assumptions.

#### 2.5.1 Build Scope Summary

After completing requirements analysis (Phase 2) and codebase reconnaissance (Phase 1.5), compile a compact summary table:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plan Scope Summary — Review Before Generation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source Documents: [N] files ([total word count] words)

Extracted Features:
| # | Feature | Priority | Status | Source |
|---|---------|----------|--------|--------|
| 1 | [Feature name] | P0 | Not implemented | PRD §2.1 |
| 2 | [Feature name] | P0 | Partially implemented | PRD §3.2 |
| 3 | [Feature name] | P1 | Already implemented | PRD §4.1 |
| ... | ... | ... | ... | ... |

Proposed Plan Shape:
  Phases:           [N] phases
  Total Work Items: ~[N] (estimated)
  Estimated Effort: ~[X] LOC across ~[Y] files
  Critical Path:    [Phase sequence summary]

Phase Grouping (draft):
  Phase 1: [Title] — [brief scope, e.g., "Foundation: auth, config, DB schema"]
  Phase 2: [Title] — [brief scope]
  Phase 3: [Title] — [brief scope]
  ...

Assumptions:
  - [Assumption 1, e.g., "Using existing auth module in src/auth/"]
  - [Assumption 2, e.g., "PostgreSQL as primary datastore per TDD §3.1"]
  - [Assumption 3, e.g., "No mobile targets — web only"]
  ...

Features Skipped (already implemented):
  - [Feature name] — [reason, e.g., "Fully implemented in src/export/"]
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 2.5.2 Ask for Approval

After presenting the summary, ask:

```text
Proceed with this scope?
  1. Yes — generate the full implementation plan
  2. Adjust — tell me what to change (add/remove features, regroup phases, change priorities)
  3. Abort — stop here (analysis results above are yours to keep)
```

**Wait for the user to respond.** Do not proceed to Phase 3 until the user explicitly approves.

#### 2.5.3 Handle Responses

- **"Yes" / "1" / approve:** Proceed to Phase 3 (Phase Planning) with the confirmed scope.
- **"Adjust" / "2":** Accept the user's modifications. Update the feature list, phase grouping, priorities, or assumptions as directed. Re-display the updated summary and ask for approval again.
- **"Abort" / "3":** Stop execution. Display:
  ```text
  Plan generation aborted. Analysis results:
    - [N] documents analyzed ([word count] words)
    - [N] features extracted
    - [N] already implemented, [N] partially implemented
    - Codebase reconnaissance completed

  To resume later, run /create-plan with the same documents.
  ```

#### 2.5.4 Design Constraints

- **Keep it compact:** The summary should be scannable in 30 seconds. Use tables, not paragraphs.
- **No partial generation:** Do not start generating plan phases before approval.
- **Assumptions are explicit:** Every inference made during analysis (tech choices, scope exclusions, priority assignments) must appear in the Assumptions list so the user can correct them.
- **Already-implemented features visible:** Features detected by codebase reconnaissance that will be skipped or only verified must be listed so the user can override if the detection was wrong.

### Phase 3: Phase Planning

#### 3.1 Work Item Extraction

Convert requirements into discrete work items:

**For each feature/requirement:**
1. Identify the deliverable
2. List files likely to be affected
3. Estimate complexity (XS/S/M/L/XL)
4. Identify dependencies
5. Define acceptance criteria

**Complexity estimation:**
| Size | Files Changed | LOC Changed | Example |
|------|---------------|-------------|---------|
| S | 1-3 files | <100 LOC | Config change, small fix, single file edit |
| M | 3-8 files | 100-500 LOC | Feature with tests, API endpoint, refactoring |
| L | 8-15 files | 500-1500 LOC | Complex feature, major refactoring, integration |

If a work item would be XL (15+ files or 1500+ LOC), split it into smaller items.

#### 3.2 Phase Construction

Group work items into phases following these rules:

**Phase sizing constraints:**
Each phase should be completable by a single subagent session:
- Target: read 5-8 files, modify 3-5 files, change ~500 LOC
- Maximum: L complexity (8-15 files, 500-1500 LOC)
- Minimum: 2 files changed (avoid trivial phases)
- If a phase would be XL (15+ files or 1500+ LOC), split into sub-phases (e.g., Phase 3a, 3b)
- Target S-M per phase (max L)

**Grouping criteria:**
1. **Dependencies:** Items depending on each other go in sequence
2. **Cohesion:** Related items grouped together
3. **Risk:** High-risk items early (fail fast)
4. **Value:** High-value items prioritized
5. **Parallelization:** Independent items in same phase

**Phase ordering principles:**
1. Foundation/infrastructure first
2. Core features before enhancements
3. Integration points after dependent components
4. Polish/optimization last

#### 3.3 Dependency Analysis

For each phase, verify:
- All dependencies from previous phases are met
- No circular dependencies exist
- Critical path is identified

### Phase 4: Generate IMPLEMENTATION_PLAN.md

#### Append vs Overwrite Logic

**Before writing, check if IMPLEMENTATION_PLAN.md already exists.**

- **If the file does NOT exist:** Create it fresh with the full structure below.
- **If the file DOES exist:**
  1. Read the existing file
  2. Preserve the existing header (everything up to and including the `---` after Plan Overview / Phase Summary Table)
  3. Identify the highest existing phase number (e.g., if Phase 4 is the last, new phases start at Phase 5)
  4. Renumber all new phases to continue from the highest existing phase
  5. Renumber all new work items accordingly (e.g., 5.1, 5.2, 6.1...)
  6. Append the new phases after the last existing phase section
  7. Update the Phase Summary Table to include both old and new phases
  8. Update the total phase count, estimated total effort, and any metadata in the header
  9. Append new entries to Parallel Work Opportunities, Risk Mitigation, Success Metrics, and Requirement Traceability tables
  10. Add a separator comment before the new content: `<!-- Appended on [YYYY-MM-DD HH:MM:SS] from /create-plan -->`

**Tell the user what happened:**
```text
Existing IMPLEMENTATION_PLAN.md found with [N] phases.
Appending [M] new phases (Phase [N+1] through Phase [N+M]).
```

Create the implementation plan with this structure:

```markdown
# Implementation Plan

**Generated:** [YYYY-MM-DD HH:MM:SS]
**Based On:** [List of analyzed documents]
**Total Phases:** [N]
**Estimated Total Effort:** ~[X] LOC across [Y] files

---

## Executive Summary

[2-3 paragraph overview of what will be built, key architectural decisions, and implementation strategy]

---

## Plan Overview

[Summary of the implementation strategy and phasing rationale. Explain why phases are ordered this way and what the critical path is.]

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | [Area] | [Deliverables] | M (~N files, ~N LOC) | None |
| 2 | [Area] | [Deliverables] | M (~N files, ~N LOC) | Phase 1 |
| ... | ... | ... | ... | ... |

---

## Phase 1: [Phase Title]

**Estimated Complexity:** [S/M/L] (~N files, ~N LOC)
**Dependencies:** [None | List of phases]
**Parallelizable:** [Yes/No - can work items run concurrently]

### Goals

- [Goal 1 - high-level objective]
- [Goal 2 - high-level objective]

### Work Items

#### 1.1 [Work Item Title]
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: PENDING**
**Requirement Refs:** [PRD §2.1, TDD §4.3]
**Files Affected:**
- `path/to/file1.ts` (create)
- `path/to/file2.ts` (modify)
- `path/to/file3.test.ts` (create)

**Description:**
[Detailed description of what needs to be implemented. Include specific technical details, algorithms, or approaches to use.]

**Tasks:**
1. [ ] [Specific task 1 with enough detail to execute]
2. [ ] [Specific task 2 with enough detail to execute]
3. [ ] [Specific task 3 with enough detail to execute]
4. [ ] [Write unit tests for...]
5. [ ] [Update documentation for...]

**Acceptance Criteria:**
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

**Notes:**
[Any additional context, gotchas, or implementation hints]

---

#### 1.2 [Work Item Title]
...

---

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

---

## Parallel Work Opportunities

[Identify which phases or work items can be executed concurrently]

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 1.1 | Phase 1.2 | [Why these are independent] |
| Phase 2.1 | Phase 2.3 | [Why these are independent] |
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
- [ ] [Business metric 1 from BRD]
- [ ] [Performance metric from TDD]
- [ ] [User satisfaction metric from PRD]

---

## Appendix: Requirement Traceability

| Requirement | Source | Phase | Work Item |
|-------------|--------|-------|-----------|
| [Req 1] | PRD §2.1 | 1 | 1.1 |
| [Req 2] | TDD §3.2 | 1 | 1.2 |
| ... | ... | ... | ... |

---

*Implementation plan generated by Claude on [YYYY-MM-DD HH:MM:SS]*
*Source: /create-plan command*
```

### Phase 5: Save and Report

#### 5.1 Save the Plan

Save IMPLEMENTATION_PLAN.md to the repository root (or custom path if specified). If appending to an existing file, the save overwrites the file with the merged content (existing + new phases).

#### 5.2 Summary Report

Display a summary to the user:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Implementation Plan Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source Documents: 5 files analyzed
  - PRD.md (Product Requirements)
  - TDD.md (Technical Design)
  - docs/BRD.md (Business Requirements)
  - docs/api-spec.md (API Specification)
  - docs/data-model.md (Data Model)

Plan Summary:
  Total Phases:     4
  Total Work Items: 18
  Estimated Effort: ~2,400 LOC across 22 files

Phase Breakdown:
  Phase 1: Foundation        (M, ~8 files, ~500 LOC, 5 work items)
  Phase 2: Core Features     (L, ~10 files, ~800 LOC, 6 work items)
  Phase 3: Integration       (M, ~6 files, ~600 LOC, 4 work items)
  Phase 4: Polish & Launch   (S, ~4 files, ~500 LOC, 3 work items)

Critical Path: Phase 1 → Phase 2 → Phase 3 → Phase 4
Parallelization: 8 work items can run concurrently

Risks Identified: 4 (1 high, 2 medium, 1 low)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Output: IMPLEMENTATION_PLAN.md

Next Steps:
  1. Review the generated plan
  2. Adjust phases or work items as needed
  3. Run '/implement-plan' to begin execution
```

## Execution Guidelines

- **Be thorough:** This plan informs significant work—capture all requirements
- **Be specific:** Include file paths, function names, concrete approaches
- **Be realistic:** Estimate effort honestly; overrunning phases causes problems
- **Be practical:** Prioritize impact over elegance; ship value to users
- **Consider context:** Factor in existing codebase (use reconnaissance results), tech debt, team constraints
- **Extend, don't rebuild:** When codebase reconnaissance identifies existing features, plan to extend or enhance them rather than building from scratch
- **Enable parallelism:** Structure phases so multiple streams can work simultaneously
- **Preserve stability:** Each phase should leave the codebase in a working state
- **Maintain traceability:** Link every work item back to source requirements

## Error Handling

### No Requirements Documents

```text
Error: No requirements documents found.

Create at least one of:
  - PRD.md (Product Requirements Document)
  - BRD.md (Business Requirements Document)
  - TDD.md (Technical Design Document)
  - requirements.md

Or specify documents explicitly:
  /create-plan path/to/your/requirements.md
```

### Incomplete Requirements

If critical information is missing:

```text
⚠️  Incomplete Requirements Detected

Missing information:
  - No database schema defined (needed for data layer)
  - API authentication method not specified
  - Error handling strategy not documented

Options:
  1. Continue with assumptions (I'll document them)
  2. Pause for you to update requirements
  3. Generate partial plan for defined areas only

How should I proceed?
```

### Conflicting Requirements

See Phase 2.3 for conflict handling.

## Performance

**Typical Duration:**

| Document Volume | Expected Time |
|-----------------|---------------|
| Light (< 5K words) | 1-2 minutes |
| Medium (5-15K words) | 2-4 minutes |
| Heavy (15-30K words) | 4-8 minutes |
| Extensive (30K+ words) | 8-15 minutes |

**Factors Affecting Performance:**
- Number and size of source documents
- Complexity of requirements (many dependencies)
- Conflict resolution needed
- Level of detail in output

## Related Commands

- `/plan-improvements` - Generate improvement plan from existing codebase analysis
- `/implement-plan` - Execute an IMPLEMENTATION_PLAN.md
- `/plan-next` - Get recommendation for next action
- `/assess-document` - Evaluate document quality before planning
