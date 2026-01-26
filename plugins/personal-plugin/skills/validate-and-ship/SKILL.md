---
name: validate-and-ship
allowed-tools: Bash(git:*), Bash(gh:*), Bash(tea:*), Glob, Grep, Read, Edit, Write
description: Validate plugins, clean repository, and ship changes in one automated workflow
---

# Validate and Ship

Automated pre-flight checks and shipping workflow. Executes validation, cleanup, and git workflow in sequence, stopping only when user intervention is required.

## Input Validation

**Optional Arguments:**
- `--skip-validate` - Skip plugin validation phase
- `--skip-cleanup` - Skip repository cleanup phase
- `--dry-run` - Preview all phases without executing changes
- `<branch-name>` - Custom branch name for shipping (passed to ship phase)

**Dry-Run Mode:**
When `--dry-run` is specified:
- Run validation (read-only, always safe)
- Preview cleanup changes without executing
- Preview ship operations without executing
- Prefix all output with `[DRY-RUN]`

## Workflow Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Phase 1:       │     │  Phase 2:       │     │  Phase 3:       │
│  Validate       │────▶│  Clean Repo     │────▶│  Ship           │
│  Plugins        │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   STOP if errors          Continue with           Full ship
   CONTINUE if warnings    artifact cleanup        workflow
```

## Execution

Execute each phase in sequence. Only stop for blocking issues that require user intervention.

---

## Phase 1: Plugin Validation

Run `/validate-plugin --all` to check all plugins in the repository.

### 1.1 Execute Validation

Perform the full validation as defined in `/validate-plugin`:
- Structure validation
- Skill structure validation (nested directories, `name` field)
- Frontmatter validation
- Marketplace schema validation
- Version synchronization
- Content validation
- Namespace collision detection
- Pattern compliance

### 1.2 Evaluate Results

**Blocking (STOP):**
- Any validation errors (missing required fields, invalid structure, version mismatch)
- Display the error summary and stop

**Non-blocking (CONTINUE):**
- Warnings (namespace collisions for `/help`, code blocks in tools/ directory)
- Display warning summary and proceed

### 1.3 Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: Plugin Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Validation output from /validate-plugin --all]

Result: [PASS/FAIL]
  Errors:   [N]
  Warnings: [N]

[If PASS or warnings only]
✓ Validation passed. Proceeding to cleanup.

[If FAIL with errors]
✗ Validation failed with [N] error(s).
  Fix the errors above before shipping.

  [WORKFLOW STOPPED]
```

---

## Phase 2: Repository Cleanup

Run `/clean-repo` to clean artifacts and validate structure.

### 2.1 Execute Cleanup

Perform cleanup as defined in `/clean-repo`:
- Artifact cleanup (temp files, pycache, OS artifacts)
- Structure validation
- Documentation audit
- Configuration consistency check
- Git hygiene

### 2.2 Handle Cleanup Actions

**Auto-execute without confirmation:**
- Delete untracked temp files and artifacts
- Remove `__pycache__` directories
- Prune stale remote branches

**Skip (don't block on):**
- Missing optional documentation
- Suggestions for improvement
- Non-critical warnings

**Require confirmation (STOP if declined):**
- Deleting tracked files
- Moving files to new locations
- Modifying documentation content

### 2.3 Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: Repository Cleanup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Cleanup output from /clean-repo]

Result: [CLEAN/CLEANED]
  Artifacts removed: [N]
  Issues found: [N] (non-blocking)

✓ Repository clean. Proceeding to ship.
```

---

## Phase 3: Ship

Run `/ship` to create branch, commit, push, open PR, auto-review, fix issues, and merge.

### 3.1 Pre-flight Check

Before shipping, verify there are changes to ship:

```bash
git status --porcelain
```

**If no changes:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: Ship
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No changes to ship. Working directory is clean.

✓ Workflow complete (nothing to ship).
```

### 3.2 Execute Ship Workflow

If there are changes, execute the full `/ship` workflow:

1. **Create Branch** - Auto-generate or use provided branch name
2. **Stage and Commit** - Stage all changes, generate commit message
3. **Push to Remote** - Push branch with tracking
4. **Create PR** - Generate PR with summary
5. **Auto-Review** - Analyze for security, performance, quality issues
6. **Fix Loop** - Auto-fix blocking issues (up to 5 attempts)
7. **Merge** - Squash merge and cleanup branches

### 3.3 Handle Ship Results

**Success:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: Ship
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Ship output]

✓ PR #[N] merged successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workflow Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Phase 1 (Validate): PASSED
  Phase 2 (Cleanup):  CLEANED
  Phase 3 (Ship):     MERGED

PR URL: [url]
```

**Failure (unfixable issues):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: Ship
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Ship output with unfixable issues]

✗ Ship failed - manual intervention required.

PR URL: [url] (still open)

[WORKFLOW STOPPED]
```

---

## Stopping Conditions

The workflow stops only when:

| Condition | Phase | Action Required |
|-----------|-------|-----------------|
| Validation errors | 1 | Fix plugin structure/content |
| User declines file operation | 2 | Approve or skip the operation |
| No git/gh/tea CLI available | 3 | Install required tools |
| Unfixable PR issues | 3 | Manual code fixes needed |
| Max fix attempts reached | 3 | Review recurring issues |

The workflow does NOT stop for:
- Validation warnings (namespace collisions, non-blocking issues)
- Cleanup suggestions
- Stale branches (auto-pruned)
- PR review suggestions (non-blocking)

---

## Error Handling

### Phase 1 Errors
```
Validation Error: [specific error]

To fix:
  [Specific remediation steps]

After fixing, run /validate-and-ship again.
```

### Phase 2 Errors
```
Cleanup Error: [specific error]

The cleanup phase encountered an issue:
  [Details]

Options:
  1. Fix the issue and run /validate-and-ship again
  2. Run /validate-and-ship --skip-cleanup to bypass
```

### Phase 3 Errors
```
Ship Error: [specific error]

The ship phase could not complete:
  [Details]

PR URL: [url] (if created)

Manual steps required:
  [Specific steps to resolve]
```

---

## Example Usage

### Standard Flow
```
User: /validate-and-ship

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: Plugin Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Validation runs...]
✓ Validation passed (2 warnings, 0 errors)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: Repository Cleanup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Cleanup runs...]
✓ Repository clean (4 artifacts removed)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: Ship
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Ship workflow runs...]
✓ PR #42 merged successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workflow Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR URL: https://github.com/user/repo/pull/42
```

### With Custom Branch
```
User: /validate-and-ship feat/new-feature

Claude: [Runs all phases, uses "feat/new-feature" as branch name]
```

### Dry Run
```
User: /validate-and-ship --dry-run

Claude:
[DRY-RUN] Phase 1: Validation would check all plugins
[DRY-RUN] Phase 2: Cleanup would remove 4 temp files
[DRY-RUN] Phase 3: Would create branch, commit 3 files, open PR

No changes made. Run without --dry-run to execute.
```

### Skip Phases
```
User: /validate-and-ship --skip-validate

Claude: [Skips Phase 1, runs Phases 2 and 3]
```
