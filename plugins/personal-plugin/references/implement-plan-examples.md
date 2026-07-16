# Implement-Plan Examples & Output Templates

**Purpose:** Reference material for `/implement-plan` — the exact wording of error messages, resume/decision prompts, the COMPLETION REPORT template, and usage examples. `/implement-plan` keeps compact inline pointers to these sections (with the underlying logic still described in the command body) so the command stays within the progressive-disclosure line budget.

**Consumers:** `/implement-plan`.

---

## Error Messages (Input Validation)

### Missing plan file

```text
Error: [PLAN_FILE] not found.

Run one of these commands to generate an implementation plan:
- /plan-improvements — Generate from codebase analysis
- /create-plan — Generate from requirements documents

Or specify a custom path: /implement-plan --input <path-to-plan>
```

### On main/master branch

```text
Error: Cannot run on main/master branch.

Create a feature branch first:
  git checkout -b feature/implementation
```

### Dirty working directory — interrupted session detected

Shown when `.implement-plan-state.json` exists and contains an `"in_progress"` or `"in_progress_batch"` field:

```text
Uncommitted changes detected. State file shows work item [X.Y] was in progress.
This may be leftover from an interrupted session.

Options:
  (1) Commit these changes and resume (git add + commit as "[X.Y] interrupted work")
  (2) Stash these changes and resume (git stash)
  (3) Abort — inspect manually first
```

### Dirty working directory — standard error

Shown when there is no state file or no in-progress item:

```text
Error: Uncommitted changes detected.

Commit or stash your changes before running this command:
  git status
  git add <files> && git commit -m "Message"
```

---

## Resume Prompt — Interrupted Work Item Detected (STARTUP Step 0)

Shown on resume when an `"in_progress"` or `"in_progress_batch"` entry is found in the state file:

```text
Resuming from interrupted session. [N] items already completed.
Work item [X.Y] ("[description]") was in progress when the previous session ended.

Options:
  (1) Retry — re-implement this work item from scratch
  (2) Skip — mark as skipped and move to the next item
  (3) Mark complete — the work was finished but not recorded; mark it done and continue
```

For `in_progress_batch`, all interrupted items are listed in the message and the user's choice applies to the entire batch. The effect of each option (Retry / Skip / Mark complete) is defined in the command body — this block is only the display text.

---

## Test Failure Prompt (Step 2 — TESTS_STUCK)

Shown when the testing subagent cannot fix failures after 3 attempts:

```text
Tests cannot be fixed for [work item [N.M] | parallel batch [N.M, N.N, ...]] after 3 attempts.
Failing: [test names from subagent]

Options:
  (1) Rollback — revert to last checkpoint [last_good_sha] and skip this [item | batch]
  (2) Skip — keep the changes but mark [the item | all items in the batch] as failed, continue
  (3) Pause — stop execution for manual intervention
```

The effect of each option (Rollback / Skip / Pause) is defined in the command body — this block is only the display text.

---

## Phase Validation Issues Prompt (Step T3)

Shown when the phase-validation subagent returns `PHASE_ISSUES`:

```text
Phase [completed phase] has unchecked completion items:
[list of issues]

Options:
  (1) Continue anyway — proceed to the next phase despite incomplete items
  (2) Pause — stop execution to address the issues manually, then resume with /implement-plan
  (3) Abort — proceed to FINALIZATION with whatever is complete so far
```

The effect of each option (Continue anyway / Pause / Abort) is defined in the command body — this block is only the display text.

---

## Completion Report Template

Output on every exit path (normal completion, early termination, user abort, or error) — the last thing the command outputs regardless of how it exits:

```text
═══════════════════════════════════════════════════════
 IMPLEMENTATION PROGRESS REPORT
═══════════════════════════════════════════════════════

 Status: [COMPLETE | PARTIAL — reason]
 Session started: [started_at from state file]
 Current phase: [current_phase from state file]

 ✓ Completed ([N] items):
   [For each item in completed array:]
   - [item] [description] (SHA: [first 7 chars of sha])

 ✗ Failed/Skipped ([N] items):
   [For each item in failed array:]
   - [item] [description] — [error]

 ◌ Remaining ([N] items):
   [For each item not in completed or failed:]
   - [item] [description]

 [If in_progress or in_progress_batch exists:]
 ⚠ In Progress (interrupted):
   - [item] [description] — started [started_at]

 Last checkpoint: [last_good_sha from state file] ([item number])

 To resume: /implement-plan [include --input flag if non-default path]
 The state file (.implement-plan-state.json) will resume from where this session stopped.
═══════════════════════════════════════════════════════
```

The field-population rules (what goes in each bracket, and the status-line values) are defined in the command body's "Report generation rules."

---

## Usage Examples

```yaml
# Default: PR-only (no merge) — creates a PR and stops for manual review
/implement-plan

# Creates the PR, then merges it and cleans up the branch
/implement-plan --auto-merge

# Use a plan file at a custom path
/implement-plan --input docs/migration-plan.md

# Pause for confirmation before each new phase (interactive)
/implement-plan --pause-between-phases

# Combined flags
/implement-plan --input plans/refactor.md --pause-between-phases --auto-merge
```
