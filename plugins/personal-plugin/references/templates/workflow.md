---
description: {{DESCRIPTION}}
---

# {{TITLE}}

{{INTRO_PARAGRAPH}}

## Input Validation

**Optional Arguments:**
- `--dry-run` - Preview all changes without executing them

**Dry-Run Mode:**
When `--dry-run` is specified:
- Perform all analysis phases normally
- Show what changes would be made
- Prefix all proposed actions with `[DRY-RUN]` to clearly indicate preview mode
- Do NOT execute any modifications
- Skip all confirmation prompts (nothing will be executed anyway)

## Phase 1: Preparation

[Describe initial setup and validation steps]

1. [First preparation step]
2. [Second preparation step]
3. [Third preparation step]

**Actions:**
1. [List specific actions]
2. [Confirm prerequisites]

## Phase 2: Execution

[Describe the main workflow steps]

### Step 1: [Step Name]

[Detailed instructions for this step]

**Actions:**
1. [Action 1]
2. [Action 2]

### Step 2: [Step Name]

[Detailed instructions for this step]

**Actions:**
1. [Action 1]
2. [Action 2]

### Step 3: [Step Name]

[Detailed instructions for this step]

**Actions:**
1. [Action 1]
2. [Action 2]

## Phase 3: Verification

[Describe verification and validation steps]

1. [Verification check 1]
2. [Verification check 2]
3. [Verification check 3]

## Phase 4: Completion

[Describe cleanup and reporting steps]

### Summary Report

```
----------------------------------------------
{{TITLE}} Complete
----------------------------------------------

**Summary:**
- [Metric 1]: [Value]
- [Metric 2]: [Value]

**Changes Made:**
- [Change 1]
- [Change 2]

**Next Steps:**
- [Suggested action 1]
- [Suggested action 2]
```

## Execution Instructions

1. **Scan first, act second** - Complete all analysis before making changes
2. **Present findings** - Show a summary of planned actions
3. **Confirm before bulk operations** - Get user approval before:
   - Making multiple changes
   - Performing irreversible actions
4. **Make changes incrementally** - Execute approved changes, showing progress
5. **Summarize results** - Report what was completed and any remaining items

## Safety Rules

- **Never skip confirmations** - Always get user approval for significant changes
- **Preserve originals** - Back up before destructive operations
- **Skip if uncertain** - Flag ambiguous situations for user decision

## Example Usage

```
User: /{{COMMAND_NAME}}

Claude:
Phase 1: Preparation
--------------------
[PASS] Prerequisite 1 verified
[PASS] Prerequisite 2 verified
[INFO] Found X items to process

Phase 2: Execution
------------------
Proceeding with the workflow...

[Step details]

Phase 3: Verification
---------------------
[PASS] Verification check 1
[PASS] Verification check 2

----------------------------------------------
{{TITLE}} Complete
----------------------------------------------

**Summary:**
- Items processed: X
- Changes made: Y

**Next Steps:**
- [Recommendation]
```

```
User: /{{COMMAND_NAME}} --dry-run

Claude:
[DRY-RUN] Phase 1: Preparation
------------------------------
[DRY-RUN] Would check prerequisites...
[DRY-RUN] Found X items to process

[DRY-RUN] Phase 2: Planned Changes
----------------------------------
[DRY-RUN] Would perform action 1
[DRY-RUN] Would perform action 2

No changes made. Run without --dry-run to execute.
```
