# Workflow Patterns

This document defines patterns for state management, session handling, and resumable workflows.

## Workflow State Management

Interactive commands SHOULD support resuming interrupted sessions. This allows users to continue where they left off if a session is interrupted.

### State File Format

The answer file (`schemas/answers.json`) includes state management fields:

```json
{
  "metadata": {
    "status": "in_progress",
    "last_question_answered": 15,
    "total_questions": 47,
    "started_at": "2026-01-14T10:00:00Z"
  },
  "answers": [...]
}
```

### Resume Detection

On startup, commands supporting resume MUST:

1. **Check for existing answer file** matching the source document:
   - Look for `answers-[document-name]-*.json` in expected output directory
   - Parse metadata to check status

2. **If found with status "in_progress":**
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Incomplete session detected
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Previous session: answers-PRD-20260114-100000.json
   Progress: 15 of 47 questions answered (32%)
   Last activity: 2026-01-14T10:45:00Z

   Options:
   [R] Resume from question 16
   [S] Start fresh (overwrites previous progress)
   [A] Abort

   Your choice (R/S/A):
   ```

3. **If resume selected (R):**
   - Load existing answers into state
   - Continue from `last_question_answered + 1`
   - Preserve existing answer entries

4. **If start fresh selected (S):**
   - Backup existing file: `answers-PRD-20260114-100000.backup.json`
   - Start new session from question 1

### State Updates

During the session:

1. **After each answer:** Update `last_question_answered` in memory
2. **On explicit save or quit:** Write state to file with `status: "in_progress"`
3. **On session complete:** Set `status: "completed"` and add `completed_at`

### Commands Supporting Resume

| Command | State File | Resume Behavior |
|---------|------------|-----------------|
| `/ask-questions` | `answers-*.json` | Resume from last answered question |
| `/finish-document` | `reference/answers-*.json` | Resume Q&A phase from last answered |

### Implementation Requirements

Commands implementing resume MUST:
1. Check for existing state files on startup
2. Display resume prompt with progress information
3. Preserve existing answers when resuming
4. Update state file on each answer (or on explicit save)
5. Handle backup of overwritten files

## Session Commands

Interactive commands that process items one at a time MUST support these standard session commands. Users can type these at any prompt during the session.

| Command | Aliases | Description |
|---------|---------|-------------|
| `help` | `?`, `commands` | Show available session commands and their descriptions |
| `status` | `progress` | Show current position (e.g., "Question 5 of 20") and summary of completed/remaining items |
| `back` | `previous`, `prev` | Return to the previous item to review or change the answer |
| `skip` | `next`, `pass` | Skip the current item (can return later) |
| `quit` | `exit`, `stop` | Exit the session with a prompt to save progress |

### Help Response Format

When user types `help` during an interactive session, display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session Commands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  help      Show this help message
  status    Show current progress (X of Y completed)
  back      Return to previous item
  skip      Skip current item (can return later)
  quit      Exit session (progress will be saved)

Additional commands:
  go to N   Jump to item number N
  save      Save progress without exiting

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Status Response Format

When user types `status` during an interactive session, display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session Progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current: Item 5 of 20
Completed: 4 (20%)
Skipped: 1
Remaining: 15

Type 'help' for available commands.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Implementation Requirements

Interactive commands implementing session commands:
- `/ask-questions`
- `/finish-document`
- `/bpmn-generator` (Interactive mode)

All implementations MUST:
1. Check for session commands before processing user input as an answer
2. Handle command aliases (e.g., `?` = `help`, `prev` = `back`)
3. Be case-insensitive (`HELP` = `help` = `Help`)
4. Show the help message when an unrecognized command is entered

## Multi-Phase Workflow Pattern

For commands with multiple distinct phases:

```markdown
## Phase 1: [Phase Name]

1. [Step 1 description]
2. [Step 2 description]

**Output:** [What this phase produces]

## Phase 2: [Phase Name]

1. [Step 1 description]
2. [Step 2 description]

**Output:** [What this phase produces]
```

### Phase Transitions

Between phases, report progress:

```
Phase 1 complete: [Summary of what was done]

Proceeding to Phase 2: [Phase Name]
```

## Backup and Safety Patterns

### Pre-Modification Backup

Before modifying any user files:

1. Create a backup with timestamp: `[filename].backup-[timestamp].[ext]`
2. Verify the backup was created successfully
3. Only then proceed with modifications

### Atomic Updates

For multi-file updates:

1. Generate all changes in memory
2. Verify all changes are valid
3. Apply changes in sequence
4. If any change fails, offer to restore from backup

### Rollback Support

Commands that modify multiple files SHOULD track changes for potential rollback:

```json
{
  "changes": [
    {"file": "path/to/file.md", "backup": "path/to/file.backup-20260114.md"},
    {"file": "path/to/other.md", "backup": "path/to/other.backup-20260114.md"}
  ],
  "timestamp": "2026-01-14T14:30:00Z"
}
```
