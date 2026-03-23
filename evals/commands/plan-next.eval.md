---
command: plan-next
type: command
fixtures: []
---

# Eval: /plan-next

## Purpose

Analyzes the current repository state (git status, recent commits, open issues, existing plans) and recommends the next logical action. Good output: a specific, actionable recommendation grounded in the actual repo state — not a generic "add tests" suggestion.

## Fixtures

None — operates on the current repository state.

## Test Scenarios

### S1: Repo with no open plan

**Setup:** Ensure no `IMPLEMENTATION_PLAN.md` exists in the repo root.

**Invocation:** `/plan-next`

**Must:**
- [ ] Reads recent git log, git status, and project structure
- [ ] Produces a recommendation for the next action
- [ ] Recommendation is specific (references actual files, commands, or issues)
- [ ] Provides a rationale for why this is the next action

**Should:**
- [ ] If recent commits suggest a feature in progress, recommends continuing or testing it
- [ ] If documentation is outdated relative to recent commits, recommends updating it

**Must NOT:**
- [ ] Recommend an action already reflected in recent commits as "done"
- [ ] Give the same recommendation regardless of repo state (must be context-aware)

---

### S2: Repo with completed IMPLEMENTATION_PLAN.md

**Setup:** Copy `fixtures/plans/implementation-plan.md` to repo root and manually set all STATUS markers to `done`.

**Invocation:** `/plan-next`

**Must:**
- [ ] Detects that the plan is complete
- [ ] Does not recommend implementing an already-complete plan
- [ ] Recommends something appropriate for "plan complete" state (e.g., bump version, clean up, create PR)

---

### S3: Repo with uncommitted changes

**Setup:** Modify a file and leave it uncommitted.

**Invocation:** `/plan-next`

**Must:**
- [ ] Notes the uncommitted changes in its analysis
- [ ] May recommend committing or completing the in-progress work before starting something new

---

### S4: Read-only behavior

**Must:**
- [ ] Does not create any files
- [ ] Does not make git commits
- [ ] Analysis is in-conversation only

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Recommendation is context-specific to this repo | Required |
| Rationale provided | Required |
| No files created or modified | Required |
| Does not recommend already-completed work | Required |
