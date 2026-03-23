---
command: create-plan
type: command
fixtures: [docs/sample-prd.md, docs/draft-prd.md]
---

# Eval: /create-plan

## Purpose

Generates a detailed `IMPLEMENTATION_PLAN.md` from requirements documents (BRD, PRD, TDD, design specs). Good output: a machine-readable plan with phases, work items, sizing estimates, acceptance criteria, and status markers — following the standard schema used by `/implement-plan`.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/sample-prd.md` | Well-formed PRD — good source for a complete plan |
| `docs/draft-prd.md` | Incomplete PRD — tests handling of ambiguous requirements |

## Test Scenarios

### S1: Happy path — complete PRD input

**Invocation:** `/create-plan fixtures/docs/sample-prd.md`

**Must:**
- [ ] Creates `IMPLEMENTATION_PLAN.md` in the current directory (or specified output)
- [ ] Plan has at least 2 phases
- [ ] Each work item has: Status (todo), Size (S/M/L), Tasks list, Acceptance Criteria
- [ ] Items include `<!-- STATUS:todo -->` machine-readable markers
- [ ] Plan covers the P0 requirements from the PRD (F-01, F-07 at minimum)
- [ ] Total phases ≤ 8, items per phase ≤ 6 (plan size limits)

**Should:**
- [ ] Work items align with the PRD's functional requirements (F-01 through F-15)
- [ ] Phases are logically ordered (e.g., database schema before API layer)
- [ ] Sizing estimates (S/M/L) are proportional to the described complexity
- [ ] Non-goals from PRD Section 1.4 are NOT included as work items

**Must NOT:**
- [ ] Include more than 8 phases
- [ ] Include work items for features explicitly listed as out of scope
- [ ] Create the file without status markers (plan is not machine-readable without them)

---

### S2: Draft/incomplete PRD input

**Invocation:** `/create-plan fixtures/docs/draft-prd.md`

**Must:**
- [ ] Either: generates a plan with placeholder/TBD items for unresolved requirements
- [ ] Or: asks clarifying questions before generating the plan
- [ ] Does not generate a plan that assumes specific answers to open questions in the PRD

**Should:**
- [ ] Notes which requirements were ambiguous and how they were interpreted

---

### S3: Scope confirmation before generating

**Invocation:** `/create-plan fixtures/docs/sample-prd.md`

**Must:**
- [ ] Presents a scope summary before writing the plan file
- [ ] Asks for confirmation or allows user to adjust scope

---

### S4: Custom output path

**Invocation:** `/create-plan fixtures/docs/sample-prd.md --output docs/standup-plan.md`

**Must:**
- [ ] Creates the plan at the specified path, not at `IMPLEMENTATION_PLAN.md`

---

### S5: Error — file not found

**Invocation:** `/create-plan fixtures/docs/nonexistent.md`

**Must:**
- [ ] Error message referencing the missing file
- [ ] No plan file created

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| STATUS markers present in all work items | Required |
| Phases logically ordered | Required |
| Acceptance criteria are specific and testable | Required |
| P0 requirements from PRD covered | Required |
| Out-of-scope items excluded | Required |
| Plan size limits respected (≤8 phases, ≤6 items/phase) | Required |
