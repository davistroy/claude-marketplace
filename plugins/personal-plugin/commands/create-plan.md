---
description: Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs)
---

# Create Plan Command

Generate a comprehensive, phased implementation plan from requirements and design documents in the project. This command discovers and analyzes BRDs, PRDs, TDDs, and other specification documents, then produces an actionable IMPLEMENTATION_PLAN.md ready for execution with `/implement-plan`.

## Overview

This command:

1. Discovers requirements and design documents in the project
2. Analyzes and synthesizes requirements across all documents
3. Breaks down work into appropriately-sized phases
4. Generates detailed work items with acceptance criteria
5. Outputs IMPLEMENTATION_PLAN.md to the repository root

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
| Size | Token Estimate | Example |
|------|----------------|---------|
| XS | 1K-5K | Config change, small fix |
| S | 5K-15K | Single component, simple feature |
| M | 15K-30K | Feature with tests, API endpoint |
| L | 30K-60K | Complex feature, refactoring |
| XL | 60K-100K | Major system component |

#### 3.2 Phase Construction

Group work items into phases following these rules:

**Phase sizing constraints:**
- Target: ~80,000 tokens per phase (with 20% buffer)
- Maximum: 100,000 tokens per phase
- Minimum: 20,000 tokens per phase (avoid tiny phases)

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
- **Consider context:** Factor in existing codebase, tech debt, team constraints
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
