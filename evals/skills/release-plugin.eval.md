---
command: release-plugin
type: skill
fixtures: []
---

# Eval: /release-plugin (skill)

## Purpose

Automated pre-flight-and-ship workflow: runs `/validate-plugin --all` (Phase 1), `/clean-repo` (Phase 2), then the full `/ship` workflow (Phase 3) in sequence, stopping only when user intervention is required. `disable-model-invocation: true` — must only run via explicit `/release-plugin` invocation, never silently auto-triggered. Good behavior: each phase gates the next (blocking errors stop the workflow; warnings do not), and phases can be individually skipped via flags.

## Fixtures

None — operates on the live repository and its plugins.

## Setup

Run on a feature branch with 1-2 changed files, from the marketplace repo root.

## Test Scenarios

### S1: Happy path — full pipeline

**Setup:** All plugins pass validation; a small change is uncommitted.

**Invocation:** `/release-plugin`

**Must:**
- [ ] Runs Phase 1 (`/validate-plugin --all`) first and reports PASS/FAIL with error/warning counts
- [ ] Proceeds to Phase 2 (`/clean-repo`) only if Phase 1 has no blocking errors
- [ ] Proceeds to Phase 3 (full `/ship` workflow: branch, commit, push, PR, auto-review, fix loop, merge) only if Phase 2 completes
- [ ] Reports each phase in sequence with a clear header (e.g., "Phase 1: Plugin Validation")
- [ ] Prints a final summary showing all three phase results and the PR URL

**Should:**
- [ ] Non-blocking warnings (e.g., namespace collisions) are logged but do not stop progression

**Must NOT:**
- [ ] Auto-invoke without an explicit `/release-plugin` call (it has `disable-model-invocation: true`)
- [ ] Push directly to main
- [ ] Skip a phase without the corresponding `--skip-*` flag

---

### S2: Validation failure blocks the pipeline

**Setup:** Temporarily break a plugin (e.g., remove `name` from a skill's frontmatter) so validation fails with a blocking error.

**Invocation:** `/release-plugin`

**Must:**
- [ ] Runs Phase 1 and detects the blocking error
- [ ] Does NOT proceed to Phase 2 (cleanup) or Phase 3 (ship)
- [ ] Displays the error summary and remediation guidance, then reports `[WORKFLOW STOPPED]`

---

### S3: `--dry-run` mode

**Invocation:** `/release-plugin --dry-run`

**Must:**
- [ ] Runs validation (read-only)
- [ ] Previews cleanup changes and ship operations without executing them
- [ ] Prefixes preview output with `[DRY-RUN]`
- [ ] Makes no git changes and does not push or open a PR

---

### S4: `--skip-ship` (pre-flight only)

**Setup:** Have uncommitted changes ready.

**Invocation:** `/release-plugin --skip-ship`

**Must:**
- [ ] Runs Phase 1 and Phase 2 normally
- [ ] Reports Phase 3 as `SKIPPED`, not executed
- [ ] Does not create a branch, commit, or PR
- [ ] Reports "Ready to ship when you are" (or equivalent) rather than treating this as a failure

---

### S5: `--skip-validate` and `--skip-cleanup`

**Invocation:** `/release-plugin --skip-validate`

**Must:**
- [ ] Skips Phase 1 entirely (no validation output)
- [ ] Runs Phase 2 and Phase 3 as normal

---

### S6: Nothing to ship

**Setup:** Working directory is clean (no changes) but validation and cleanup still have something to check.

**Invocation:** `/release-plugin`

**Must:**
- [ ] Runs Phase 1 and Phase 2 normally
- [ ] Phase 3 detects no changes via `git status --porcelain` and reports "nothing to ship" without creating an empty commit or PR

---

### S7: Custom branch name passed through

**Invocation:** `/release-plugin feat/my-branch`

**Must:**
- [ ] Passes `feat/my-branch` through to the Phase 3 ship workflow as the branch name
- [ ] Does not auto-generate a different branch name

## Rubric

| Criterion | Pass Threshold |
|-----------|-----------------|
| Never auto-invokes without explicit `/release-plugin` | Required |
| Blocking validation errors stop the pipeline before cleanup/ship | Required |
| `--dry-run` makes no git changes and previews all three phases | Required |
| `--skip-validate` / `--skip-cleanup` / `--skip-ship` each work independently | Required |
| Custom branch name is honored, not overridden | Required |
| Never pushes to main | Required |
| Nothing-to-ship handled gracefully (no empty commit/PR) | Required |
