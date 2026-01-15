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

## Dependency Verification

Commands requiring external tools MUST check for their availability before processing. This prevents cryptic errors and provides clear installation guidance.

### Check Pattern

Before performing any work that requires an external tool:

1. **Check if tool exists** using `which` (Unix) or `where` (Windows)
2. **If missing**, display the standardized error format below
3. **Exit gracefully** without partial processing

### Platform Detection

```bash
# Detect platform for appropriate commands
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
    # Windows
    where pandoc >nul 2>&1 || echo "NOT_FOUND"
else
    # Unix/macOS
    which pandoc >/dev/null 2>&1 || echo "NOT_FOUND"
fi
```

### Error Message Format

When a required dependency is missing, display:

```
Error: Required dependency '[tool-name]' not found

/[command-name] requires [tool-name] for [purpose].

Installation instructions:
  Windows: [windows-command]
  macOS:   [mac-command]
  Linux:   [linux-command]

After installing, run the command again.
```

### Example: Pandoc Dependency

```
Error: Required dependency 'pandoc' not found

/convert-markdown requires pandoc for document conversion.

Installation instructions:
  Windows: winget install pandoc
  macOS:   brew install pandoc
  Linux:   sudo apt install pandoc

After installing, run the command again.
```

### Example: Graphviz Dependency

```
Error: Required dependency 'graphviz' not found

/bpmn-to-drawio requires Graphviz for automatic diagram layout.

Installation instructions:
  Windows: choco install graphviz
  macOS:   brew install graphviz
  Linux:   sudo apt install graphviz libgraphviz-dev

After installing Graphviz, also install the Python bindings:
  pip install pygraphviz

After installing, run the command again.

Note: If your BPMN file already has layout coordinates, you can skip
Graphviz and use: /bpmn-to-drawio input.bpmn output.drawio --layout=preserve
```

### Commands Requiring External Dependencies

| Command | Dependency | Purpose |
|---------|------------|---------|
| `/convert-markdown` | pandoc | Document format conversion |
| `/bpmn-to-drawio` | graphviz | Automatic diagram layout |

### Implementation Requirements

Commands with external dependencies MUST:
1. Check for the tool BEFORE processing any input
2. Display the full error message including all platform installation options
3. Exit cleanly without partial output
4. Document the dependency in the command's markdown file

## Performance Expectations

Commands with variable or extended duration SHOULD document expected timing to help users identify abnormal behavior and plan their workflows.

### Documentation Pattern

Add a Performance section to commands that may take significant time:

```markdown
## Performance

**Typical Duration:**
| Input Size | Expected Time |
|------------|---------------|
| Small (< 100 files) | 30-60 seconds |
| Medium (100-500 files) | 1-3 minutes |
| Large (500+ files) | 3-10 minutes |

**Factors Affecting Performance:**
- [Factor 1: description]
- [Factor 2: description]
- [Factor 3: description]

**Signs of Abnormal Behavior:**
- No output after [X] minutes
- Memory usage exceeding [X] GB
- Repeated errors in output
```

### Performance Indicators to Document

1. **Input size thresholds**: How input size affects duration
2. **Complexity factors**: What makes processing slower
3. **Network dependencies**: If network latency is a factor
4. **Iteration counts**: For commands with fix loops
5. **Timeout guidance**: When to interrupt and retry

### Commands Requiring Performance Documentation

| Command | Primary Factors |
|---------|-----------------|
| `/plan-improvements` | Codebase size, file count |
| `/test-project` | Test count, fix iterations |
| `/review-arch` | Codebase complexity, file count |
| `/clean-repo` | Repository size, file count |

### User Guidance Template

Include guidance for users who experience unexpected delays:

```markdown
**If the command seems stuck:**
1. Check for output activity (scrolling text)
2. Wait at least [X] minutes for large inputs
3. If no activity, interrupt and retry with a smaller scope
4. Report persistent issues to maintainers
```

### Progress Reporting for Long-Running Commands

Commands that may run for extended periods SHOULD report progress:

```
Phase 1 of 4: Analyzing codebase structure...
  - Scanning directories: 247 found
  - Identifying file types: 1,823 files
  - Building dependency graph: 89% complete

Phase 2 of 4: Evaluating architecture patterns...
```

This helps users distinguish between "working" and "stuck".

## Output Preview Mode

Commands generating structured output SHOULD support the `--preview` flag to allow users to review and confirm before saving.

### Preview Pattern

When `--preview` is specified:

1. **Generate output in memory** - Create the complete output structure
2. **Validate against schema** - Check all required fields and types
3. **Display summary** - Show a compact summary, not the full output:
   ```
   Preview: /define-questions
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Source: PRD.md
   Questions found: 15

   By topic:
     Technical Architecture: 5
     User Experience: 3
     Data Model: 7

   Schema validation: PASSED
   Output file: questions-PRD-20260114-143052.json
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Save this file? (y/n):
   ```
4. **Wait for confirmation** - Only save on explicit 'y' or 'yes'
5. **On rejection** - Display message and exit without saving

### Preview vs Dry-Run

| Flag | Purpose | Behavior |
|------|---------|----------|
| `--preview` | Review output before saving | Generates output, shows summary, asks confirmation |
| `--dry-run` | Test without any side effects | Shows what would happen, never executes |

### Commands Supporting Preview

| Command | Output Type | Preview Summary |
|---------|-------------|-----------------|
| `/define-questions` | JSON | Question count, topics, validation status |
| `/analyze-transcript` | MD/JSON | Section count, action items, decisions |
| `/bpmn-generator` | BPMN XML | Element counts, lanes, validation status |

### Implementation Requirements

Commands implementing `--preview` MUST:
1. Document the `--preview` flag in their Input Validation section
2. Generate complete output before showing preview (not partial)
3. Show validation status in the preview summary
4. Require explicit user confirmation before saving
5. Handle 'n' response gracefully (no error, just exit)

## Schema Validation

Commands generating or consuming JSON output MUST validate against their respective schemas before saving or processing. This ensures data integrity across the Q&A workflow chain (`/define-questions` -> `/ask-questions` -> `/finish-document`).

### Schema Locations

| Command | Direction | Schema |
|---------|-----------|--------|
| `/define-questions` | Output | `schemas/questions.json` |
| `/ask-questions` | Input | `schemas/questions.json` |
| `/ask-questions` | Output | `schemas/answers.json` |
| `/finish-document` | Input | `schemas/answers.json` |

### Validation Behavior

Commands generating JSON output follow this process:

1. **Generate output in memory** - Create the complete JSON structure
2. **Validate against schema** - Check all required fields and types
3. **If valid:** Save file and report success with validation status
4. **If invalid:** Report specific validation errors with actionable guidance
5. **Offer `--force` flag** to save despite validation errors (not recommended)

### Success Message Format

```
Output validated against schemas/questions.json. Saved to reports/questions-PRD-20260114-143052.json

Validation: PASSED
- Required fields: All present
- Field types: All correct
- Total questions: 15
```

### Error Message Format

```
Schema validation failed:

Errors:
  - questions[3].id: Required field missing
  - questions[7].priority: Must be one of: high, medium, low
  - metadata.generated_at: Invalid date-time format

Fix these issues or use --force to save anyway (not recommended).

Note: Files saved with --force may not work correctly with downstream commands.
```

### Input Validation Behavior

Commands consuming JSON input follow this process:

1. **Load the JSON file**
2. **Validate against expected schema**
3. **If valid:** Proceed with processing
4. **If invalid:** Report validation errors and suggest fixes
5. **Offer `--force` flag** to proceed despite validation errors

### Input Validation Error Format

```
Input validation failed for questions-PRD-20260114.json:

Errors:
  - metadata.source_document: Required field missing
  - questions[2]: Missing required field 'context'

The input file may have been created with an older version or manually edited.
Use --force to proceed anyway (some features may not work correctly).
```

### Implementation Requirements

Commands implementing schema validation MUST:

1. Document the `--force` flag in their Input Validation section
2. Show validation status in completion summary
3. Provide specific error locations (e.g., `questions[3].id`)
4. Suggest how to fix validation errors
5. Warn about consequences of using `--force`

### Commands Requiring Schema Validation

| Command | Validates |
|---------|-----------|
| `/define-questions` | Output against `schemas/questions.json` |
| `/ask-questions` | Input against `schemas/questions.json`, Output against `schemas/answers.json` |
| `/finish-document` | Input against `schemas/answers.json` |

## Audit Logging

Commands with significant side effects MAY support an optional `--audit` flag to log actions for troubleshooting and compliance.

### Audit Log Format

Log file: `.claude-plugin/audit.log` (JSON lines format)

Each line is a self-contained JSON object:

```json
{"timestamp": "2026-01-14T10:30:00Z", "command": "clean-repo", "action": "delete", "path": "old-file.md", "success": true}
{"timestamp": "2026-01-14T10:30:01Z", "command": "clean-repo", "action": "delete", "path": "temp/cache.json", "success": true}
{"timestamp": "2026-01-14T10:30:02Z", "command": "ship", "action": "git_commit", "details": {"sha": "abc123", "message": "feat: add feature"}, "success": true}
{"timestamp": "2026-01-14T10:30:03Z", "command": "ship", "action": "pr_create", "details": {"number": 42, "url": "https://..."}, "success": true}
```

### Log Entry Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | When the action occurred |
| `command` | string | Yes | Command that performed the action |
| `action` | string | Yes | Type of action (delete, move, git_commit, pr_create, etc.) |
| `path` | string | No | File path affected (for file operations) |
| `details` | object | No | Additional context (git SHA, PR number, etc.) |
| `success` | boolean | Yes | Whether the action succeeded |
| `error` | string | No | Error message if success is false |

### Action Types

| Action | Used By | Description |
|--------|---------|-------------|
| `delete` | `/clean-repo` | File or directory deletion |
| `move` | `/clean-repo` | File relocation |
| `git_checkout` | `/ship` | Branch creation/switch |
| `git_commit` | `/ship` | Commit creation |
| `git_push` | `/ship` | Push to remote |
| `pr_create` | `/ship` | PR creation |
| `pr_merge` | `/ship` | PR merge |

### Implementation Requirements

Commands implementing audit logging MUST:

1. **Document the `--audit` flag** in their Input Validation section
2. **Create log directory** if `.claude-plugin/` doesn't exist
3. **Append to log file** (never overwrite)
4. **Log failures** with error messages
5. **Keep log entries atomic** (one JSON object per line)

### Enabling Audit Logging

Audit logging is **off by default** for privacy and performance. Enable with:

```
/clean-repo --audit
/ship --audit
```

### Log Rotation

The audit log is not automatically rotated. Users should manage log size by:
- Periodically archiving: `mv .claude-plugin/audit.log .claude-plugin/audit-$(date +%Y%m%d).log`
- Adding to `.gitignore`: `.claude-plugin/audit*.log`

### Commands Supporting Audit

| Command | Actions Logged |
|---------|----------------|
| `/clean-repo` | delete, move |
| `/ship` | git_checkout, git_commit, git_push, pr_create, pr_merge |

## Argument Testing

Commands SHOULD be tested for argument handling to ensure consistent user experience and helpful error messages. This section documents the standard test cases for command argument validation.

### Test Categories

#### 1. Required Argument Missing

Test that the command provides helpful guidance when required arguments are not provided.

**Test Input:**
```
/command-name
```
(no arguments)

**Expected Behavior:**
- Standard error format with usage example
- Clear explanation of what's required
- Example of correct usage

**Example Expected Output:**
```
Error: Missing required argument

Usage: /command-name <required-arg> [optional-arg]
Example: /command-name my-file.md

Arguments:
  <required-arg>  Description of required argument
  [optional-arg]  Description of optional argument (default: value)
```

#### 2. Invalid Argument Value

Test that the command provides clear feedback when an argument value is invalid.

**Test Input:**
```
/command-name invalid-file.xyz
```

**Expected Behavior:**
- Clear error explaining what's wrong
- Guidance on valid values or formats
- No partial execution or side effects

**Example Expected Output:**
```
Error: Invalid file type

/command-name requires a markdown file (.md)

Received: invalid-file.xyz
Expected: *.md file path

Example: /command-name docs/requirements.md
```

#### 3. Optional Argument Defaults

Test that optional arguments use documented default values when not provided.

**Test Input:**
```
/command-name file.md
```
(no --format specified)

**Expected Behavior:**
- Command uses default format as documented in Input Validation section
- Output indicates which default was used (if applicable)
- Behavior matches documentation

**Verification:**
- Check output format matches documented default
- Verify no error messages about missing optional args

#### 4. Flag Parsing

Test that flags are correctly parsed and applied.

**Test Input:**
```
/command-name file.md --dry-run
```

**Expected Behavior:**
- Dry-run behavior (no side effects, no file writes)
- Output indicates dry-run mode is active
- Full operation simulation shown

**Test Input:**
```
/command-name file.md --force
```

**Expected Behavior:**
- Override behavior (e.g., proceed despite validation errors)
- Warning shown about using --force
- Operation completes with warning

#### 5. Unknown Arguments

Test that unrecognized arguments are handled gracefully.

**Test Input:**
```
/command-name file.md --unknown-flag
```

**Expected Behavior:**
- Clear error about unrecognized argument
- List of valid arguments shown
- No partial execution

**Example Expected Output:**
```
Error: Unknown argument '--unknown-flag'

Valid arguments for /command-name:
  <file-path>     Required: Path to input file
  --format        Optional: Output format (json|md)
  --force         Optional: Proceed despite validation errors

Example: /command-name file.md --format json
```

### Test Checklist

Use this checklist when testing command argument handling:

- [ ] Missing required argument shows usage with example
- [ ] Invalid argument value shows clear error and guidance
- [ ] Optional arguments use documented defaults
- [ ] All documented flags work as described
- [ ] --dry-run (if supported) produces no side effects
- [ ] --force (if supported) overrides with warning
- [ ] Unknown arguments show clear error
- [ ] Error messages include example of correct usage

### Commands with Argument Handling

| Command | Required Args | Optional Args | Flags |
|---------|--------------|---------------|-------|
| `/define-questions` | `<document-path>` | `--format` | `--force` |
| `/ask-questions` | `<questions-file>` | | `--force` |
| `/finish-document` | `<document-path>` | | `--auto`, `--force` |
| `/assess-document` | `<document-path>` | | |
| `/review-pr` | | `<pr-number>` | |
| `/convert-markdown` | `<markdown-file>` | `--output` | |
