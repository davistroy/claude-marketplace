# Input Validation Patterns

This document defines patterns for validating input, handling errors, and reporting validation status.

## Input Validation Section Structure

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

## Error Message Formats

### Standard Error Format

For general errors, use this format:

```
Error: [Brief description of what went wrong]

Expected: [What was expected]
Received: [What was actually provided]

Suggestion: [How to fix the issue]
```

### Missing/Invalid Argument Error Format

When required arguments are missing or invalid:

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

## Schema Validation

Commands generating or consuming JSON output MUST validate against their respective schemas before saving or processing.

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

### Validation Success Message Format

```
Output validated against schemas/questions.json. Saved to reports/questions-PRD-20260114-143052.json

Validation: PASSED
- Required fields: All present
- Field types: All correct
- Total questions: 15
```

### Validation Error Message Format

```
Schema validation failed:

Errors:
  - questions[3].id: Required field missing
  - questions[7].priority: Must be one of: high, medium, low
  - metadata.generated_at: Invalid date-time format

Fix these issues or use --force to save anyway (not recommended).

Note: Files saved with --force may not work correctly with downstream commands.
```

### Input Validation Error Format

```
Input validation failed for questions-PRD-20260114.json:

Errors:
  - metadata.source_document: Required field missing
  - questions[2]: Missing required field 'context'

The input file may have been created with an older version or manually edited.
Use --force to proceed anyway (some features may not work correctly).
```

## Dependency Verification

Commands requiring external tools MUST check for their availability before processing.

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

### Missing Dependency Error Format

```
Error: Required dependency '[tool-name]' not found

/[command-name] requires [tool-name] for [purpose].

Installation instructions:
  Windows: [windows-command]
  macOS:   [mac-command]
  Linux:   [linux-command]

After installing, run the command again.
```

### Commands Requiring External Dependencies

| Command | Dependency | Purpose |
|---------|------------|---------|
| `/convert-markdown` | pandoc | Document format conversion |
| `/bpmn-to-drawio` | graphviz | Automatic diagram layout |

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

## Interactive Parameter Prompting

Commands that require file paths or other arguments SHOULD prompt for missing values rather than showing an error, unless `--no-prompt` is specified.

### Prompting Pattern

When a required argument is missing:

1. **Check for `--no-prompt` flag** - If present, show standard error message and exit
2. **Prompt the user interactively** - Ask for the missing value
3. **Validate the response** - Ensure the provided value is valid
4. **Proceed with command execution** - Use the prompted value

### Prompting Format

```
[Command Name] requires a [argument type].

Please provide the [argument description]:
> _

(or use --no-prompt to disable interactive prompting)
```

### Example: File Path Prompting

```
/define-questions requires a document path.

Please provide the path to the document to analyze:
> docs/requirements.md

Analyzing docs/requirements.md...
```

### Example with --no-prompt

```
User: /define-questions --no-prompt

Claude:
Error: Missing required argument

Usage: /define-questions <document-path> [--format json|csv]
Example: /define-questions PRD.md
```

### Implementation Guidelines

**When to Prompt:**
- Required file paths
- Required input values that cannot have sensible defaults
- Commands where the user likely knows the value but forgot to provide it

**When NOT to Prompt:**
- Commands run in scripts or CI/CD (use `--no-prompt`)
- Optional arguments with defaults
- Boolean flags

**Prompting Best Practices:**
- Keep the prompt concise and clear
- Show the expected format or provide an example
- Validate input before proceeding
- Allow the user to cancel (Ctrl+C or "cancel")
- Remember the `--no-prompt` flag for non-interactive contexts

### Commands Supporting Interactive Prompting

| Command | Prompted Argument | Prompt Message |
|---------|-------------------|----------------|
| `/define-questions` | `<document-path>` | "Please provide the path to the document to analyze:" |
| `/assess-document` | `<document-path>` | "Please provide the path to the document to assess:" |

### The --no-prompt Flag

All commands that support interactive prompting MUST also support `--no-prompt`:

```markdown
**Optional Arguments:**
- `--no-prompt` - Disable interactive prompting (for scripts and CI/CD)
```

**Behavior:**
- When `--no-prompt` is specified and a required argument is missing, show the standard error message
- This flag is essential for non-interactive environments like CI/CD pipelines
- Commands should default to prompting when run interactively
