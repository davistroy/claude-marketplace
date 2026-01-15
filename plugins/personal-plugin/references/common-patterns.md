# Common Command Patterns

This document defines standard patterns used across personal-plugin commands.

## Timestamp Format

`YYYYMMDD-HHMMSS` (e.g., `20260114-143052`)

## Output File Naming

`[type]-[source]-[timestamp].[ext]`

Examples:
- `assessment-PRD-20260114-143052.md`
- `questions-requirements-20260114-150000.json`
- `answers-design-doc-20260114-160030.json`
- `meeting-analysis-20260114-093000.md`

## Output Locations

| Output Type | Directory | Example |
|-------------|-----------|---------|
| Analysis reports | `reports/` | `reports/assessment-PRD-20260114.md` |
| Reference data (JSON) | `reference/` | `reference/questions-PRD-20260114.json` |
| Generated documents | Same as source | `docs/PRD.docx` |
| Temporary files | `.tmp/` | `.tmp/cache-20260114.json` |

### Directory Auto-Creation

Commands MUST automatically create output directories if they don't exist before writing files. Use the following pattern:

```bash
# Ensure output directory exists before writing
mkdir -p reports/  # or reference/, .tmp/, etc.
```

This ensures commands work correctly in fresh repositories or when output directories have been cleaned up.

## Progress Reporting

```
Phase X of Y: [Phase Name]
- Step 1: [Description] ✓
- Step 2: [Description] (in progress)
- Step 3: [Description] (pending)
```

## Session Commands (for interactive commands)

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

## Input Validation Pattern

Commands that accept arguments should include a validation section:

```markdown
## Input Validation

**Required Arguments:**
- `<argument-name>` - Description of argument

**Optional Arguments:**
- `--flag [value]` - Description (default: value)

**Validation:**
If required arguments missing, display:
"Usage: /command-name <required-arg> [--optional-arg value]"
```

## Issue Severity Levels

All assessment and review commands MUST use these standardized severity levels:

| Severity | Label | Description | Action Required |
|----------|-------|-------------|-----------------|
| **CRITICAL** | Must fix | Blocks progress, security vulnerabilities, data integrity risks | Immediate resolution required |
| **WARNING** | Should fix | Quality issues, missing tests, potential problems | Should be addressed before merge/approval |
| **SUGGESTION** | Nice to have | Improvements, best practices, minor enhancements | Non-blocking, at discretion |

### Usage in Reports

```markdown
### CRITICAL Issues (Must Fix)
#### C1. [Issue Title]
...

### WARNING Issues (Should Fix)
#### W1. [Issue Title]
...

### SUGGESTION Issues (Nice to Have)
#### S1. [Issue Title]
...
```

### Issue Summary Format

```markdown
| Severity | Count |
|----------|-------|
| CRITICAL | X |
| WARNING | X |
| SUGGESTION | X |
| **Total** | **X** |
```

Commands using these levels:
- `/assess-document` - Document quality evaluation
- `/review-pr` - PR code review
- `/ship` - Auto-review during PR workflow

## Error Message Format

### Standard Error Format

For general errors, use this format:

```
Error: [Brief description of what went wrong]

Expected: [What was expected]
Received: [What was actually provided]

Suggestion: [How to fix the issue]
```

### Missing/Invalid Argument Error Format

When required arguments are missing or invalid, use this standardized format:

```
Error: Missing required argument

Usage: /command-name <required-arg> [optional-arg]
Example: /command-name my-file.md

Arguments:
  <required-arg>  Description of required argument
  [optional-arg]  Description of optional argument (default: value)
```

**Format Rules:**
- `<arg>` denotes required arguments
- `[arg]` denotes optional arguments
- Include at least one concrete example
- List all arguments with descriptions
- Show default values for optional arguments

### Input Type Error Format

When a command accepts multiple input types, clarify which types are valid:

```
Error: Invalid input type

Usage: /command-name <input>

Input can be one of:
  1. File path      - Path to a document (e.g., docs/spec.md)
  2. Pasted content - Content provided directly in chat
  3. Concept        - Brief description in quotes (e.g., "user authentication flow")

Examples:
  /command-name architecture.md
  /command-name "microservices patterns"
```

### Multiple Document Requirement Format

When a command requires multiple inputs:

```
Error: Insufficient documents provided

Usage: /command-name <doc1> <doc2> [doc3...]

This command requires at least 2 documents to compare and consolidate.

Examples:
  /command-name draft-v1.md draft-v2.md
  /command-name spec-a.md spec-b.md spec-c.md
```

## Confirmation Prompts

For destructive or irreversible actions:

```
⚠️ This will [describe action].

Affected items:
- [Item 1]
- [Item 2]

Type 'confirm' to proceed or 'cancel' to abort:
```

## Completion Summaries

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Command Name] Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Summary:**
- [Metric 1]: [Value]
- [Metric 2]: [Value]

**Output:**
- [File path or result]

**Next Steps:**
- [Suggested action 1]
- [Suggested action 2]
```
