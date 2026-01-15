# Common Command Patterns

This document serves as an index to the modular pattern files. Each pattern area has been split into a focused document for maintainability.

## Pattern Files

| Pattern File | Description | Key Content |
|--------------|-------------|-------------|
| [naming.md](patterns/naming.md) | File and command naming | Timestamp format, output file naming, type prefixes |
| [validation.md](patterns/validation.md) | Input validation and error handling | Error message formats, schema validation, dependency checks |
| [output.md](patterns/output.md) | Output files, directories, preview | Directory auto-creation, preview mode, completion summaries |
| [workflow.md](patterns/workflow.md) | State management, resume, sessions | Resume detection, session commands, multi-phase workflows |
| [testing.md](patterns/testing.md) | Argument testing, dry-run | Test categories, dry-run pattern, test checklist |
| [logging.md](patterns/logging.md) | Audit logging, progress reporting | Audit log format, performance documentation |

## Quick Reference

### Timestamp Format
`YYYYMMDD-HHMMSS` (e.g., `20260114-143052`)

See: [patterns/naming.md](patterns/naming.md)

### Output File Naming
`[type]-[source]-[timestamp].[ext]`

See: [patterns/naming.md](patterns/naming.md)

### Output Locations

| Output Type | Directory |
|-------------|-----------|
| Analysis reports | `reports/` |
| Reference data (JSON) | `reference/` |
| Generated documents | Same as source |
| Temporary files | `.tmp/` |

See: [patterns/naming.md](patterns/naming.md)

### Directory Auto-Creation

```bash
mkdir -p reports/  # or reference/, .tmp/, etc.
```

See: [patterns/output.md](patterns/output.md)

### Error Message Format

```
Error: [Brief description]

Expected: [What was expected]
Received: [What was provided]

Suggestion: [How to fix]
```

See: [patterns/validation.md](patterns/validation.md)

### Issue Severity Levels

| Severity | Label | Action Required |
|----------|-------|-----------------|
| **CRITICAL** | Must fix | Immediate |
| **WARNING** | Should fix | Before merge |
| **SUGGESTION** | Nice to have | At discretion |

See: [patterns/validation.md](patterns/validation.md)

### Session Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `help` | `?`, `commands` | Show available commands |
| `status` | `progress` | Show progress |
| `back` | `previous`, `prev` | Previous item |
| `skip` | `next`, `pass` | Skip current item |
| `quit` | `exit`, `stop` | Exit with save prompt |

See: [patterns/workflow.md](patterns/workflow.md)

### Completion Summary Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Command Name] Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Summary:**
- [Metric 1]: [Value]

**Output:**
- [File path]

**Next Steps:**
- [Suggestion]
```

See: [patterns/output.md](patterns/output.md)

## Usage in Commands

When creating or updating commands, reference specific pattern files:

```markdown
See `references/patterns/validation.md` for error message format.
See `references/patterns/workflow.md` for session commands.
```

## Pattern File Maintenance

When updating patterns:
1. Edit the specific pattern file, not this index
2. Update this index only if adding new pattern files
3. Ensure templates reference specific pattern files
4. Test that all links work correctly
