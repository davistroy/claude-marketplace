---
description: Analyze repo and recommend the next logical action
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(gh:*)
---

# Next Step Analysis

Analyze the current state of this repository and recommend the single highest-priority next action. This command is plan-aware, git-aware, and produces structured output with clear rationale.

## Input Validation

**No Arguments Required:** This command takes no arguments.

If extra arguments are provided, they are ignored.

Before proceeding, verify:
- This is a valid git repository (`.git/` directory exists)
- Key project files are accessible (at minimum, one of: README.md, CLAUDE.md, or source files)
- The repository has meaningful content (not an empty init)

If the repository is empty or inaccessible, stop and report:
```text
Error: Cannot analyze repository

The repository appears to be empty or inaccessible. Ensure you are in the
root of a git repository with at least some committed content.
```

## Analysis Process

Execute the following steps in order. Each step feeds into the decision logic below.

### Step 1: Check for Active Plans

Search for planning artifacts in the repository root:

1. **IMPLEMENTATION_PLAN.md** — Read it if found. Identify:
   - Total phases and which phase is current
   - The next `PENDING` work item (by phase order)
   - Any `IN_PROGRESS` items (these take priority — they represent interrupted work)
   - Overall completion percentage (count COMPLETE vs total items)
2. **RECOMMENDATIONS.md** — Read it if found. Note:
   - Whether recommendations exist that have no corresponding implementation plan
   - Any items marked as Critical priority
3. **PROGRESS.md** or **TODO.md** — Read if found. Note any tracked items.
4. **Open GitHub Issues** — Run `gh issue list --limit 10 --state open` (if `gh` is available). Note count and any high-priority labels.

Record what was found and what was not.

### Step 2: Check Git State

Run these commands and record the results:

1. `git status --short` — Check for uncommitted changes (staged, unstaged, untracked)
2. `git branch --show-current` — Get current branch name
3. `git log --oneline -5` — Get recent commit messages for context
4. `git stash list` — Check for stashed changes
5. `gh pr list --author @me --state open --limit 5` — Check for open PRs (if `gh` available)

Classify the git state:
- **Clean on main/master**: No uncommitted changes, on default branch
- **Clean on feature branch**: No uncommitted changes, on a non-default branch
- **Dirty**: Uncommitted changes exist (staged or unstaged)
- **Stashed work**: Stash entries exist
- **Open PRs**: PRs awaiting review or merge

### Step 3: Assess Repository Health

Quickly scan for:
- Test failures: Look for test configuration files (jest.config, pytest.ini, etc.) and recent test output
- Build errors: Check for lock files, node_modules issues, or build artifacts
- Documentation gaps: Missing README, outdated CLAUDE.md, empty doc directories

### Step 4: Apply Decision Logic

Use this priority matrix to determine the recommended action. Work through it top-to-bottom; the first matching condition is the recommendation.

| Priority | Condition | Recommended Action |
|----------|-----------|-------------------|
| **P0 — Blocked Work** | `IN_PROGRESS` items exist in IMPLEMENTATION_PLAN.md | Resume the in-progress work item. It was interrupted and should be completed before starting anything new. |
| **P1 — Dirty State** | Uncommitted changes exist (`git status` is dirty) | Commit, stash, or discard uncommitted changes. Nothing else should start until the working tree is clean. |
| **P2 — Open PR** | Open PRs exist for the current user | Review/merge/close open PRs. Lingering PRs create merge conflicts and context drift. |
| **P3 — Stashed Work** | `git stash list` has entries | Review stashed changes. Either apply and complete them or drop them. Stale stashes are technical debt. |
| **P4 — Critical Fix** | RECOMMENDATIONS.md has items marked Critical or High priority | Address the highest-priority recommendation. If no IMPLEMENTATION_PLAN.md exists, suggest running `/create-plan` first. |
| **P5 — Next Plan Phase** | IMPLEMENTATION_PLAN.md exists with PENDING items | Execute the next pending work item. Provide the phase number, item number, and a brief description. |
| **P6 — Unplanned Recommendations** | RECOMMENDATIONS.md exists but no IMPLEMENTATION_PLAN.md | Run `/create-plan` to convert recommendations into an actionable implementation plan. |
| **P7 — Fresh Assessment** | No plan, no recommendations, repo has code | Run `/plan-improvements` to analyze the codebase and generate recommendations. |
| **P8 — New Project** | No plan, no recommendations, repo is mostly empty | Define the project's purpose. Create a README.md or PRD, then run `/create-plan`. |
| **P9 — All Complete** | Plan exists and all items are COMPLETE | Celebrate. Run `/plan-improvements` to find the next round of improvements, or archive the completed plan. |

## Output Format

Present results using this exact structure:

---

### Current State

| Aspect | Status |
|--------|--------|
| **Branch** | `[branch name]` |
| **Working Tree** | Clean / Dirty ([N] files modified, [M] untracked) |
| **Open PRs** | [count] or None |
| **Stashed Changes** | [count] or None |
| **Implementation Plan** | Found — Phase [X] of [Y], [N]% complete / Not found |
| **Recommendations** | Found — [N] items ([M] critical) / Not found |
| **Open Issues** | [count] or None / gh not available |

### Recommended Action

**[Clear, actionable title — e.g., "Resume Phase 3, Item 3.2: Fix finish-document.md"]**

[2-4 sentences explaining exactly what to do. Be specific — name files, commands, or work items.]

### Rationale

[Why this is the highest priority right now. Reference the decision matrix priority level (P0-P9). Explain what would happen if this were deferred.]

### Scope Estimate

| Size | Description |
|------|-------------|
| **S (Small)** | 1-3 files, <100 LOC, <30 min |
| **M (Medium)** | 4-10 files, 100-500 LOC, 30-90 min |
| **L (Large)** | 10+ files, 500+ LOC, 90+ min |

**This action is: [S/M/L]** — [brief justification]

### What This Unblocks

[1-2 sentences on what becomes possible after this action is complete.]

---

## Error Handling

Handle these edge cases explicitly:

| Scenario | Behavior |
|----------|----------|
| **Not a git repo** | Report error, suggest `git init` |
| **gh CLI not available** | Skip PR and issue checks, note in output that GitHub data is unavailable |
| **IMPLEMENTATION_PLAN.md is malformed** | Report parse error, suggest running `/create-plan` to regenerate |
| **All items in plan are COMPLETE** | Recommend archiving the plan and running `/plan-improvements` for next round |
| **Multiple plans found** | Use the one in the repository root. If ambiguous, ask the user which to use. |
| **Empty repository** | Recommend creating initial project structure (README, CLAUDE.md) |
| **Extremely large repo** | Focus analysis on root-level planning files and git state; skip deep file scanning |

## Examples

### Example 1: Plan In Progress

```text
### Current State

| Aspect | Status |
|--------|--------|
| **Branch** | `feature/implementation` |
| **Working Tree** | Clean |
| **Open PRs** | None |
| **Stashed Changes** | None |
| **Implementation Plan** | Found — Phase 3 of 7, 28% complete |
| **Recommendations** | Found — 24 items (0 critical) |
| **Open Issues** | None |

### Recommended Action

**Execute Phase 3, Item 3.1: Fix define-questions.md Phantom Schema References**

Remove all references to non-existent `schemas/questions.json`, add inline
validation rules, and standardize field names between JSON and CSV output formats.

### Rationale

Priority P5 — Next Plan Phase. Phase 2 is complete and Phase 3 has no
blockers. Item 3.1 is the first pending work item. Deferring would leave
the plan stalled with no progress.

### Scope Estimate

**This action is: S** — Single file modification, ~50 LOC of changes.

### What This Unblocks

Completing 3.1 enables items 3.2-3.4 (though they are independent) and
moves the plan toward Phase 4.
```

### Example 2: No Plan Exists

```text
### Current State

| Aspect | Status |
|--------|--------|
| **Branch** | `main` |
| **Working Tree** | Clean |
| **Open PRs** | None |
| **Stashed Changes** | None |
| **Implementation Plan** | Not found |
| **Recommendations** | Not found |
| **Open Issues** | 3 open |

### Recommended Action

**Run `/plan-improvements` to assess codebase and generate recommendations**

No implementation plan or recommendations exist. Run a codebase analysis
to identify improvement opportunities and generate a structured plan.

### Rationale

Priority P7 — Fresh Assessment. Without a plan or recommendations, there
is no structured path forward. A codebase analysis establishes priorities
and prevents ad-hoc work.

### Scope Estimate

**This action is: M** — The analysis itself takes 30-60 minutes and
produces RECOMMENDATIONS.md as output.

### What This Unblocks

Generates RECOMMENDATIONS.md, which can then be converted to an
IMPLEMENTATION_PLAN.md via `/create-plan`.
```

## Related Commands

- `/plan-improvements` — Deep codebase analysis with full RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md
- `/create-plan` — Generate implementation plan from requirements documents
- `/implement-plan` — Execute an existing IMPLEMENTATION_PLAN.md
- `/review-arch` — Quick architectural audit for understanding current state
- `/review-intent` — Compare original intent vs current implementation
