---
command: validate-and-ship
type: skill
fixtures: []
---

# Eval: /validate-and-ship (skill)

## Purpose

Composite workflow: validates all plugins, cleans the repository, and ships changes in one automated sequence. Good behavior: validation runs first, issues are fixed or reported before shipping, and clean-up happens before the PR is created.

## Fixtures

None — operates on the current repository state.

## Setup

Run on a feature branch with some changes staged.

## Test Scenarios

### S1: Happy path — all plugins valid, ship changes

**Setup:** Have a feature branch with 1-2 changed files (e.g., updated command description). All plugins pass validation.

**Invocation:** `/validate-and-ship`

**Must:**
- [ ] Runs `/validate-plugin --all` first
- [ ] If validation passes, proceeds to clean-up
- [ ] After clean-up, ships changes via the `/ship` workflow
- [ ] Reports each phase (validate → clean → ship) in sequence

**Should:**
- [ ] Reports validation result before proceeding to next phase
- [ ] Summary at end shows PR URL

**Must NOT:**
- [ ] Skip validation and go straight to ship
- [ ] Push to main

---

### S2: Validation failures block shipping

**Setup:** Temporarily break a plugin (e.g., remove `name` from a skill frontmatter).

**Invocation:** `/validate-and-ship`

**Must:**
- [ ] Runs validation
- [ ] Detects the failure
- [ ] Does NOT proceed to ship
- [ ] Reports what failed and how to fix it

---

### S3: Nothing to ship

**Setup:** Working directory is clean.

**Invocation:** `/validate-and-ship`

**Must:**
- [ ] Runs validation (pass or fail)
- [ ] Reports "nothing to commit" and exits gracefully without creating an empty PR

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Validate runs before ship | Required |
| Validation failures block shipping | Required |
| Each phase clearly reported | Should |
| Does not push to main | Required |
| Empty working directory handled gracefully | Required |
