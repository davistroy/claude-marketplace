---
command: implement-plan
type: command
fixtures: [plans/implementation-plan.md]
---

# Eval: /implement-plan

## Purpose

Executes an `IMPLEMENTATION_PLAN.md` using orchestrated subagents. Each work item is implemented, tested, and committed by a dedicated subagent. Good behavior: items are implemented in order, status markers are updated, tests pass, and a PR is created at the end.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `plans/implementation-plan.md` | 2-phase, 5-item plan for the standup bot MVP |

## Setup

**IMPORTANT:** This command is destructive and must only be run in an isolated git repository set up for eval purposes. It creates branches, makes commits, and opens a GitHub PR.

```bash
git clone <a-test-project-repo> /tmp/eval-implement-plan
cd /tmp/eval-implement-plan
cp <fixtures>/plans/implementation-plan.md IMPLEMENTATION_PLAN.md
git checkout -b eval-test-branch
```

## Test Scenarios

### S1: Prerequisite validation — on main branch

**Setup:** Be on `main` branch with an IMPLEMENTATION_PLAN.md present.

**Invocation:** `/implement-plan`

**Must:**
- [ ] Detects that current branch is main/master
- [ ] Displays error: "Cannot run on main/master branch"
- [ ] Does not start implementation

---

### S2: Prerequisite validation — plan file missing

**Invocation:** `/implement-plan` (no IMPLEMENTATION_PLAN.md in directory)

**Must:**
- [ ] Error message explaining plan file is missing
- [ ] Suggests `/plan-improvements` or `/create-plan` to generate it
- [ ] Does not make any changes

---

### S3: Custom plan path

**Setup:** Plan file at non-default location.

**Invocation:** `/implement-plan --input fixtures/plans/implementation-plan.md`

**Must:**
- [ ] Reads plan from the specified path
- [ ] Does not look for IMPLEMENTATION_PLAN.md at repo root

---

### S4: Full execution (integration — run in isolated env)

**Setup:** Clean feature branch, IMPLEMENTATION_PLAN.md copied to repo root, `gh` authenticated.

**Invocation:** `/implement-plan`

**Must:**
- [ ] Processes items in plan order (1.1 before 1.2, Phase 1 before Phase 2)
- [ ] Updates `<!-- STATUS:todo -->` to `<!-- STATUS:done -->` as items complete
- [ ] Creates a PR at the end (without `--auto-merge`)
- [ ] Does not push directly to main

**Should:**
- [ ] Each work item gets its own commit
- [ ] PR description references the plan items

**Must NOT:**
- [ ] Push to main
- [ ] Auto-merge without `--auto-merge` flag

---

### S5: Pause between phases

**Invocation:** `/implement-plan --pause-between-phases`

**Must:**
- [ ] Completes Phase 1 items, then pauses and asks for confirmation before starting Phase 2
- [ ] Waits for explicit "yes/continue" before proceeding

---

### S6: --auto-merge flag

**Invocation:** `/implement-plan --auto-merge` (in isolated test repo only)

**Must:**
- [ ] Creates PR and merges it automatically after all items complete
- [ ] Reports merged PR URL

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Prerequisites validated before starting | Required |
| Items executed in plan order | Required |
| STATUS markers updated as items complete | Required |
| PR created (not auto-merged without flag) | Required |
| Does not push to main | Required |
