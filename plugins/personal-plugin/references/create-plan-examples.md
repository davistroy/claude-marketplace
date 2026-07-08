# Create-Plan Examples & Output Templates

**Purpose:** Reference material for `/create-plan` — the full search-pattern glob list, output display samples (document inventory, codebase reconnaissance, requirement conflicts, scope summary), prompt/error-message displays, the Execution-Hints and Definition-of-Done table formats, the full AGENTS.md generation procedure, the Phase 5.2 summary-report output format, and a full end-to-end example transcript. `/create-plan` keeps compact inline pointers to these sections so the command body stays within the progressive-disclosure line budget.

**Consumers:** `/create-plan`.

---

## AGENTS.md Generation (full procedure)

Check if `AGENTS.md` exists in the repo root:
- **If AGENTS.md exists:** Skip this step entirely.
- **If AGENTS.md does not exist:** Offer to generate one:

> "No AGENTS.md found. This file provides cross-tool compatibility for AI coding tools (Codex, Cursor, Aider). Would you like me to generate one from CLAUDE.md and the codebase reconnaissance results?"

If the user accepts:
1. Read CLAUDE.md and extract project-relevant sections (Project Overview, tech stack, conventions, build/test commands)
2. Generate AGENTS.md using the template from `references/agents-md-template.md`
3. Write to repo root as `AGENTS.md`
4. Note: Do NOT include Claude Code-specific features (skills, commands, hooks) — AGENTS.md is tool-agnostic

---

## Phase 5.2 Summary Report Format

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

[If plan has 6+ phases OR 20+ total work items, append this block:]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Large Plan Detected — Consider Parallel Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This plan has [N] phases and [M] work items. '/implement-plan'
handles both sequential and parallel execution. Phases whose
Execution Mode is 'Parallel' or 'Worktree-Isolated' in the
Phase Summary Table are dispatched as concurrent background
agents in isolated worktrees, significantly reducing wall-clock
time for large independent phase sets.

  '/implement-plan'                  # All phases; parallel phases
                                     # auto-dispatched by /implement-plan
                                     # when Execution Mode is set

Set Execution Mode: Parallel or Worktree-Isolated on phases
that are mostly independent (check the Parallel Work
Opportunities table in the plan). Leave sequential for phases
with tight dependencies or shared mutable state.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Full Example Transcript

```text
User: /create-plan

Claude:
Searching for requirements documents...

Requirements Documents Found
============================
Product Requirements:
  - PRD.md (4,200 words)
Technical Design:
  - TDD.md (5,100 words)

Total: 2 documents, ~9,300 words

Surveying existing codebase...

Codebase Reconnaissance Results
================================
Tech Stack: TypeScript, React, PostgreSQL
Structure: 45 source files, 12 test files
Test Infrastructure: Jest with 38 tests

Feature Overlap Analysis:
| Requirement       | Status              | Existing Code       |
|-------------------|---------------------|---------------------|
| User auth         | Already implemented | src/auth/ (JWT)     |
| Search API        | Not implemented     | —                   |
| Dashboard         | Partially done      | src/pages/dash.tsx  |

Plan Scope Summary — Review Before Generation
...
Proceed with this scope? (1) Yes (2) Adjust (3) Abort

User: 1

Claude:
Generating implementation plan...

Output: IMPLEMENTATION_PLAN.md
  4 phases, 16 work items
  Estimated: ~2,400 LOC across 22 files
```

---

## Document Discovery: Search Patterns (full glob list)

Used by Phase 1.1 (Auto-Discovery Mode), in order of priority:

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

---

## Document Discovery: "No documents found" error (Phase 1.2)

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

---

## Document Inventory Report (Phase 1.3 sample)

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

---

## Pre-Planning Investigation prompt (Phase 1.4)

Shown when a quality-gate trigger fires. List the specific detected signals in place of the examples.

```text
⚠️  Pre-Planning Investigation Recommended

Your requirements documents have signals that suggest planning directly
may produce a low-quality or unexecutable plan:

  [List specific signals detected, e.g.:]
  - 8 of 12 features marked "TBD" or missing acceptance criteria
  - No technical design document — architecture decisions unmade

Recommended: Run `/ultra-plan` first to resolve ambiguities, then
return to `/create-plan` with sharper requirements.

Options:
  1. Run `/ultra-plan` first (recommended)
  2. Continue with `/create-plan` anyway — I'll flag gaps as assumptions
  3. Abort
```

---

## Codebase Reconnaissance Results (Phase 1.5.3 sample)

```text
Codebase Reconnaissance Results
================================

Tech Stack: [detected stack]
Structure: [N] source files, [M] test files, [K] config files
Test Infrastructure: [framework] with [N] tests
CI/CD: [detected pipeline or "None detected"]

Verification Commands Detected:
  Test:      [command or "None detected"]
  Lint:      [command or "None detected"]
  Typecheck: [command or "None detected"]
  Coverage:  [command or "None detected"]
  Custom:    [command or "None detected"]

Feature Overlap Analysis:
| Requirement | Status | Existing Code | Recommendation |
|-------------|--------|---------------|----------------|
| User auth (PRD §2.1) | Already implemented | src/auth/ (JWT + OAuth) | Skip or enhance |
| Search API (PRD §3.2) | Partially implemented | src/api/search.ts (basic) | Extend, not rebuild |
| Dashboard (PRD §4.1) | Not implemented | — | Plan from scratch |
| Data export (PRD §5.3) | Already implemented | src/export/ | Verify, skip if sufficient |
```

Greenfield notice (Phase 1.5.4 — shown when no meaningful codebase exists):

```text
Codebase Reconnaissance: Greenfield project detected.
No existing source code found. Plan will assume fresh implementation.
```

---

## Requirement Conflicts report (Phase 2.3 sample)

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

---

## Plan Scope Summary display template (Phase 2.5.1)

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

Abort response display (Phase 2.5.3):

```text
Plan generation aborted. Analysis results:
  - [N] documents analyzed ([word count] words)
  - [N] features extracted
  - [N] already implemented, [N] partially implemented
  - Codebase reconnaissance completed

To resume later, run /create-plan with the same documents.
```

---

## Execution Hints table format (Phase 3.2)

```markdown
### Execution Hints

| Phase | Model Tier | Context Budget | Notes |
|-------|------------|----------------|-------|
| All (default) | `sonnet` | Standard | Per-item Model Tier fields take precedence over phase defaults |
| [Phase N] | `opus` | Extended | [Reason — e.g., "All items in this phase require architectural judgment"] |
| [Phase M] | `haiku` | Minimal | [Reason — e.g., "Purely mechanical config updates"] |
```

---

## Definition of Done table format (Phase 4.1)

```markdown
### Definition of Done (Runnable)
<!-- BEGIN DOD -->
| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `[detected test command]` | Exit code 0 |
| Lint | `[detected lint command]` | Exit code 0 |
| Types | `[detected typecheck command]` | Exit code 0 |
| Coverage | `[detected coverage command]` | [detected threshold or "Exit code 0"] |
| [Custom] | `[detected custom command]` | [criteria] |
<!-- END DOD -->
```

---

## Error Handling displays

### No Requirements Documents (Error Handling section)

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
