# Logging Patterns

This document defines patterns for audit logging, progress reporting, and performance documentation.

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

## Progress Reporting

### Standard Progress Format

```
Phase X of Y: [Phase Name]
- Step 1: [Description] (completed)
- Step 2: [Description] (in progress)
- Step 3: [Description] (pending)
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

## Performance Documentation

Commands with variable or extended duration SHOULD document expected timing.

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
