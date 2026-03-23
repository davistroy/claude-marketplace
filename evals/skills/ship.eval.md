---
command: ship
type: skill
fixtures: []
---

# Eval: /ship (skill)

## Purpose

Creates a feature branch, stages changes, commits, pushes, opens a PR, reviews it, fixes issues, and merges. Good behavior: complete git workflow with appropriate confirmation points and no direct pushes to main.

## Fixtures

None — requires a git repository with uncommitted changes.

## Setup

Run in an isolated git repo clone. Make a small change (e.g., edit a README line) to create staged changes.

## Test Scenarios

### S1: Happy path — ship a small change

**Setup:** Have 1-2 modified files ready (not staged).

**Invocation:** `/ship` (or user says "ready to ship" / "push this")

**Must:**
- [ ] Creates a feature branch (not main)
- [ ] Stages and commits the changes with a descriptive commit message
- [ ] Pushes the branch to remote
- [ ] Opens a GitHub PR with a title and description
- [ ] Does not push directly to main

**Should:**
- [ ] Asks for confirmation before staging if unrelated files are present
- [ ] Auto-reviews the PR and notes any issues
- [ ] PR description is meaningful (not just "update files")

**Must NOT:**
- [ ] Force push
- [ ] Push to main
- [ ] Stage sensitive files (.env, credentials)

---

### S2: --dry-run mode

**Invocation:** `/ship --dry-run`

**Must:**
- [ ] Shows proposed branch name, files to stage, commit message, PR title
- [ ] Prefixes output with `[DRY-RUN]`
- [ ] Makes no git changes
- [ ] Does not push or create PR

---

### S3: Custom branch name

**Invocation:** `/ship my-feature-branch`

**Must:**
- [ ] Uses `my-feature-branch` as the branch name
- [ ] Does not auto-generate a different name

---

### S4: Draft PR

**Invocation:** `/ship draft`

**Must:**
- [ ] Creates PR as draft (`gh pr create --draft`)

---

### S5: Nothing to commit

**Setup:** Working directory is clean (no changes).

**Invocation:** `/ship`

**Must:**
- [ ] Detects no changes
- [ ] Reports "nothing to commit" and does not create an empty commit

---

### S6: Proactive trigger

**Setup:** After implementing a feature, user says "done" or "let's ship it".

**Must:**
- [ ] Skill proactively suggests itself or begins the ship workflow
- [ ] Does not require explicit `/ship` invocation

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Never pushes to main | Required |
| Dry-run mode shows all planned operations | Required |
| PR created with meaningful title/description | Required |
| Sensitive files not staged | Required |
| Confirmation requested when unrelated changes detected | Should |
