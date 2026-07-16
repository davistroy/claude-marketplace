---
command: ultra-plan
type: skill
fixtures: []
---

# Eval: /ultra-plan (skill)

## Purpose

Structured implementation planning for bug lists, feature requests, or change sets. A **rigid workflow** (Phase 0 Constitution Check -- Phase 1 Investigation -- Phase 2 Interaction Mapping -- Phase 3 Solution Design -- Phase 4 Summary Report -- Phase 5 Plan Generation) that gates each phase on the prior one's deliverable, plus a `--refresh` drift-detection mode. Good behavior: every phase's deliverable is presented before the next begins, items are investigated by reading actual code (not guessed), and interaction mapping happens before any solution is proposed.

## Fixtures

None — operates on a user-supplied bug/feature list or an existing `IMPLEMENTATION_PLAN.md`.

## Test Scenarios

### S1: Happy path — small list (<=5 items)

**Invocation:** `/ultra-plan` with a list of 3 bugs

**Must:**
- [ ] Runs Phase 0 (Constitution Check) unless a skip condition applies, reading CLAUDE.md for documented constraints
- [ ] Investigates each item inline (no sub-agents needed for <=5 items), capturing root cause, blast radius, current/expected behavior, preserved assumptions, and risk
- [ ] Presents an Interaction Map (Phase 2) before proposing any solution
- [ ] Presents Solution Design (Phase 3) only after the Interaction Map, organized by change set
- [ ] Delivers a Phase 4 Summary Report containing Pre-Plan Gates, Investigation Findings, Interaction Map, Proposed Changes, Risk Assessment, Unknowns, Implementation Sequence, Scope Boundaries, and Verification Commands
- [ ] Asks the user to approve, adjust, or redirect before generating the formal plan (does not auto-generate `IMPLEMENTATION_PLAN.md` without approval)

**Must NOT:**
- [ ] Skip or combine phases (e.g., propose a solution before the Interaction Map is presented)
- [ ] Guess root causes without reading the actual code

---

### S2: Large list (>5 items) — sub-agent investigation

**Invocation:** `/ultra-plan` with a list of 9 bugs

**Must:**
- [ ] Groups related items into clusters of 2-3 and dispatches `Explore` sub-agents in parallel (`run_in_background: true`) for Phase 1 investigation
- [ ] Merges all sub-agent findings into a single Phase 2 deliverable before proceeding
- [ ] Falls back to inline investigation for all items (noting the fallback) if the Agent tool is unavailable or a sub-agent fails

---

### S3: `--refresh` drift detection — no existing plan

**Invocation:** `/ultra-plan --refresh` with no `IMPLEMENTATION_PLAN.md` present and no `--input` path

**Must:**
- [ ] Reports that no implementation plan was found
- [ ] Directs the user to run `/ultra-plan` fresh or specify `--refresh --input <path>`
- [ ] Does not proceed with Phase 0-5

---

### S4: `--refresh` drift detection — existing plan

**Setup:** An `IMPLEMENTATION_PLAN.md` exists with some COMPLETE and some PENDING items.

**Invocation:** `/ultra-plan --refresh`

**Must:**
- [ ] Reads the plan and extracts each work item's Files Affected, Acceptance Criteria, and Status
- [ ] For COMPLETE items, checks whether listed files still exist and acceptance criteria still hold by reading the relevant code
- [ ] Produces a Drift Report table with Plan Status, Drift Status (Accurate/Drifted/Obsolete/New), Evidence, and Recommended Action per item
- [ ] Returns to normal mode after the drift report — does NOT proceed with Phase 0-5

---

### S5: Constitution Check skip conditions

**Invocation:** `/ultra-plan` for a single well-scoped bug fix, or with "skip constitution" stated explicitly

**Must:**
- [ ] Skips Phase 0 entirely per the documented skip conditions
- [ ] Proceeds directly to Phase 1 Investigation

---

### S6: Proposed solution conflicts with a Phase 0 constraint

**Setup:** A Phase 3 solution would violate a documented constraint (e.g., "never skip tests") surfaced in Phase 0.

**Must:**
- [ ] Flags the conflict explicitly in the Phase 4 Pre-Plan Gates compliance check
- [ ] Asks the user to decide rather than silently proceeding with the conflicting solution

---

### S7: Routing to Phase 5 with an existing in-progress plan

**Setup:** `IMPLEMENTATION_PLAN.md` exists with some PENDING/IN_PROGRESS items when the user approves the Phase 4 summary.

**Must:**
- [ ] Runs `/personal-plugin:plan-next` first to assess current repo/plan state
- [ ] Presents the conflict (append new phases / replace / defer) instead of silently overwriting in-progress work

## Rubric

| Criterion | Pass Threshold |
|-----------|-----------------|
| Phases run in strict order, none skipped or merged (absent documented skip conditions) | Required |
| Investigation is based on reading real code, not assumption | Required |
| Interaction Mapping precedes any proposed solution | Required |
| >5 items triggers parallel Explore sub-agent investigation | Required |
| `--refresh` mode never proceeds into Phase 0-5 | Required |
| Constraint conflicts are surfaced, not silently overridden | Required |
| Existing in-progress plans are never silently overwritten | Required |
