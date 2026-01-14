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

## Progress Reporting

```
Phase X of Y: [Phase Name]
- Step 1: [Description] ✓
- Step 2: [Description] (in progress)
- Step 3: [Description] (pending)
```

## Session Commands (for interactive commands)

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `back` | Return to previous step |
| `skip` | Skip current item |
| `status` | Show progress |
| `quit` | Exit session (with save prompt) |

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

## Error Message Format

```
Error: [Brief description of what went wrong]

Expected: [What was expected]
Received: [What was actually provided]

Suggestion: [How to fix the issue]
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
