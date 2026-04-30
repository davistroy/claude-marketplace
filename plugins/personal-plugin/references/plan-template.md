# IMPLEMENTATION_PLAN.md Template

**Purpose:** Shared output template for `/create-plan` and `/plan-improvements`. Both commands generate IMPLEMENTATION_PLAN.md files using this structure. Changes here apply to both commands, preventing template drift.

**Usage:** Commands reference this template for structural consistency. Command-specific fields (e.g., requirement refs vs recommendation refs, source attribution) are noted with `[COMMAND-SPECIFIC]` placeholders that each command fills in according to its context.

---

## Template Structure

```markdown
# Implementation Plan

**Generated:** [YYYY-MM-DD HH:MM:SS]
**Completed:** [YYYY-MM-DD — set by /implement-plan on finalization; omit until then]
**Based On:** [COMMAND-SPECIFIC: list of analyzed documents OR RECOMMENDATIONS.md]
**Total Phases:** [N]
**Estimated Total Effort:** ~[X] LOC across [Y] files

---

## Executive Summary

[2-3 paragraph overview of what will be built/changed, key architectural decisions, and implementation strategy. Include a brief note on how interrelated issues have been grouped into integrated solutions rather than isolated patches.]

---

## Plan Overview

[Summary of the implementation strategy and phasing rationale. Explain why phases are ordered this way and what the critical path is. Highlight any cases where multiple findings share a root cause and are addressed by a single cohesive work item rather than separate fixes.]

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|------------|------------------|-----------------|--------------|----------------|
| 1 | [Area] | [Deliverables] | M (~N files, ~N LOC) | None | Sequential |
| 2 | [Area] | [Deliverables] | M (~N files, ~N LOC) | Phase 1 | Parallel |
| ... | ... | ... | ... | ... | ... |

### Execution Hints (optional)

[Directives for `/implement-plan` when executing this plan. Omit if defaults are appropriate.]

| Phase | Model Tier | Context Budget | Notes |
|-------|------------|----------------|-------|
| All (default) | `sonnet` | Standard | [Override per-phase below if needed] |
| [Phase N] | `opus` | Extended | [Why this phase needs a more capable model] |

<!-- Model tier values: sonnet (default), opus (complex/architectural), haiku (simple/mechanical) — maps to Agent tool `model` parameter -->
<!-- Context budget: Standard (default), Extended (large files or complex reasoning), Minimal (simple edits) -->

### Milestones (optional)

[Group phases into logical deliverables when the plan has 4+ phases. Omit for small plans.]

| Milestone | Phases | Description |
|-----------|--------|-------------|
| [MVP / v1 / Foundation] | 1–3 | [What is usable/shippable after these phases] |
| [GA / Complete] | 1–N | [Full scope delivered] |

<!-- BEGIN PHASES -->

---

## Phase 1: [Phase Title]

**Estimated Complexity:** [S/M/L] (~N files, ~N LOC)
**Dependencies:** [None | List of phases]
**Execution Mode:** [Sequential | Parallel | Worktree-Isolated]

### Goals

- [Goal 1 - high-level objective]
- [Goal 2 - high-level objective]

### Work Items

#### 1.1 [Work Item Title]
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
<!-- On completion, /implement-plan decorates the heading: #### 1.1 Title ✅ Completed YYYY-MM-DD -->
**Status: PENDING**
**[COMMAND-SPECIFIC: "Requirement Refs:" or "Recommendation Ref:"]** [COMMAND-SPECIFIC: PRD §2.1, TDD §4.3 OR U1, A2, etc.]
**Depends On:** [None | Item refs within this phase, e.g., 1.1, 1.2 — omit if no intra-phase dependencies]
**Files Affected:**
- `path/to/file1.ext` (create)
- `path/to/file2.ext` (modify)

**Description:**
[Detailed description of what needs to be implemented. Include specific technical details, algorithms, or approaches to use.]

**Tasks:**
1. [ ] [Specific task 1 with enough detail to execute]
2. [ ] [Specific task 2 with enough detail to execute]
3. [ ] [Specific task 3 with enough detail to execute]

**Acceptance Criteria:**
<!-- Use EARS notation for behavioral criteria: WHEN [event/condition] THEN [system/component] SHALL [expected behavior]. Binary/threshold criteria (coverage ≥80%, lint clean, no TODOs) stay as simple checkboxes. -->
- [ ] WHEN [trigger event or condition] THEN [system/component] SHALL [expected observable behavior]
- [ ] WHEN [alternate scenario or edge case] THEN [system/component] SHALL [expected fallback behavior]
- [ ] [Binary/threshold criterion, e.g., "Coverage ≥80% on changed files" or "No lint errors"]

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

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

[Populated by plan generators based on detected project infrastructure. Omit section entirely if no verification commands are detected.]

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `[test command, e.g., pytest tests/ -v]` | Exit code 0 |
| Lint | `[lint command, e.g., ruff check src/]` | Exit code 0 |
| Types | `[typecheck command, e.g., mypy src/]` | Exit code 0 |
| Coverage | `[coverage command, e.g., pytest --cov=src/ --cov-fail-under=80]` | ≥80% on changed files |
| [Custom] | `[project-specific check]` | [criteria] |

<!-- END DOD -->

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

| Risk | Likelihood | Impact | Mitigation Strategy | Status |
|------|------------|--------|---------------------|--------|
| [Risk 1] | Low/Med/High | Low/Med/High | [Strategy] | Open |
| [Risk 2] | Low/Med/High | Low/Med/High | [Strategy] | Open |

<!-- Status values: Open (default at generation), Mitigated (risk addressed during implementation), Materialized (risk occurred — document impact in Notes) -->

---

## Unknowns Register

[Track epistemic uncertainties — things we don't know yet that could affect implementation. Categorically different from risks: unknowns are knowledge gaps, risks are probabilistic events.]

| ID | Unknown | Severity | Affects | Resolution Strategy | Status |
|----|---------|----------|---------|---------------------|--------|
| U1 | [What we don't know] | High/Med/Low | Phase N, Item N.M | [How to resolve: spike, prototype, ask stakeholder, etc.] | Open |
| U2 | [What we don't know] | High/Med/Low | Phase N, Item N.M | [How to resolve] | Open |

<!-- Severity: High (blocks progress — resolve before affected phase), Medium (complicates implementation — resolve during phase), Low (nice to know — resolve opportunistically) -->
<!-- Status values: Open (default), Resolved [YYYY-MM-DD] (answered — document the answer), Accepted (decided to proceed without resolving) -->
<!-- High-severity unknowns SHOULD be resolved before the affected phase begins -->

---

## Success Metrics

[How to measure overall success of the implementation]

- [ ] All phases completed
- [ ] All acceptance criteria met
- [ ] [COMMAND-SPECIFIC: Business/performance/impact metrics from source documents]

---

## Appendix: [COMMAND-SPECIFIC: "Requirement Traceability" or "Recommendation Traceability"]

| [COMMAND-SPECIFIC: "Requirement" or "Recommendation"] | Source | Phase | Work Item |
|----------------|--------|-------|-----------|
| [Ref 1] | [COMMAND-SPECIFIC: PRD §2.1 or RECOMMENDATIONS.md] | 1 | 1.1 |
| [Ref 2] | [COMMAND-SPECIFIC: source reference] | 1 | 1.2 |
| ... | ... | ... | ... |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on [YYYY-MM-DD HH:MM:SS]*
*Source: [COMMAND-SPECIFIC: /create-plan or /plan-improvements]*
```

---

## Command-Specific Field Reference

Each command fills in `[COMMAND-SPECIFIC]` placeholders as follows:

| Placeholder | `/create-plan` | `/plan-improvements` |
|-------------|----------------|----------------------|
| **Completed** | Set by `/implement-plan` on finalization; omit at generation time | Same |
| **Based On** | List of analyzed documents (e.g., PRD.md, TDD.md) | RECOMMENDATIONS.md |
| **Ref field name** | `Requirement Refs:` | `Recommendation Ref:` |
| **Ref values** | Document section refs (PRD §2.1, TDD §4.3) | Recommendation IDs (U1, A2, etc.) |
| **Success Metrics** | Business/performance metrics from BRD/PRD/TDD | Impact metrics from recommendations |
| **Traceability title** | Requirement Traceability | Recommendation Traceability |
| **Traceability column** | Requirement | Recommendation |
| **Traceability source** | Source document references | RECOMMENDATIONS.md |
| **Footer source** | `/create-plan command` | `/plan-improvements command` |

## Structural Rules

These rules apply to all plans regardless of source command:

1. **Status values:** PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD]
2. **Heading decoration on completion:** `#### N.M Title ✅ Completed YYYY-MM-DD` — set by `/implement-plan`, not by plan generators
3. **Phase markers:** `<!-- BEGIN PHASES -->` and `<!-- END PHASES -->` bracket all phase sections
4. **Table markers:** `<!-- BEGIN TABLES -->` and `<!-- END TABLES -->` bracket trailing tables
5. **Work item fields (in order):** Status, Ref, Depends On (optional), Files Affected, Description, Tasks, Acceptance Criteria, Notes
6. **Phase sections (in order):** Goals, Work Items, Testing Requirements, Completion Checklist, Definition of Done (optional)
7. **Phase header fields (in order):** Estimated Complexity, Dependencies, Execution Mode
8. **Execution Mode values:** `Sequential` (default; items run in order), `Parallel` (items run concurrently in shared tree), `Worktree-Isolated` (each phase or item runs in a dedicated git worktree; use when parallel writes to shared paths risk collision)
9. **Header fields (in order):** Generated, Completed (optional — set on finalization), Based On, Total Phases, Estimated Total Effort
10. **Risk Mitigation Status values:** `Open` (default at generation), `Mitigated` (risk addressed), `Materialized` (risk occurred)
11. **Milestones section:** Optional; include when plan has 4+ phases to group them into logical deliverables. Placed between Phase Summary Table and `<!-- BEGIN PHASES -->`
12. **Backward compatibility:** Existing plans without `Completed`, `Depends On`, `Execution Mode`, `Milestones`, `Execution Hints`, `Definition of Done`, or Risk `Status` fields parse and execute correctly — all are additive
13. **EARS notation:** Behavioral acceptance criteria SHOULD use EARS format (`WHEN [condition] THEN [component] SHALL [behavior]`). Binary/threshold criteria (pass/fail, coverage ≥N%) use simple checkbox format. EARS is recommended, not required — existing plans without it parse correctly
14. **Definition of Done (Runnable):** Optional per-phase section after Completion Checklist, bracketed by `<!-- BEGIN DOD -->` and `<!-- END DOD -->`. Columns: Check, Command, Pass Criteria. Populated by plan generators from detected project infrastructure (test runner, linter, typechecker, coverage tool). Omit entirely when no verification commands are detected — never populate with empty placeholders. `/implement-plan` executes these commands to verify phase completion
15. **Execution Hints:** Optional section between Phase Summary Table and Milestones. Columns: Phase, Model Tier (`sonnet`/`opus`/`haiku` — maps to Agent tool `model` parameter), Context Budget (Standard/Extended/Minimal), Notes. Hints are advisory; model tier can be mechanically enforced by implement-plan via the Agent tool's `model` parameter
16. **Unknowns Register:** Optional section between Risk Mitigation and Success Metrics (inside `<!-- BEGIN/END TABLES -->` markers). Columns: ID, Unknown, Severity (High/Medium/Low), Affects (phase/item refs), Resolution Strategy, Status (Open/Resolved [date]/Accepted). High-severity unknowns should be resolved before the affected phase begins. Distinct from Risk Mitigation: unknowns are knowledge gaps, risks are probabilistic events

## Sizing Constraints

| Constraint | Limit |
|------------|-------|
| Maximum phases per plan | 8 (configurable via `--max-phases`) |
| Maximum work items per phase | 6 |
| Work item file scope | 5-8 files max |
| Work item LOC scope | ~500 LOC max |
| Phase complexity target | S-M (max L) |

If limits are exceeded, split phases or work items. Never silently drop items.
