---
description: A valid sample command for testing
---

# Sample Command

A sample command that demonstrates proper structure and formatting.

## Input Validation

**Required Arguments:**
- `<input-file>` - Path to the input file

**Optional Arguments:**
- `--verbose` - Enable verbose output
- `--format [json|md]` - Output format (default: md)

**Validation:**
If arguments are missing, display:
```
Usage: /sample-command <input-file> [--verbose] [--format json|md]
Example: /sample-command document.md
```

## Instructions

### Phase 1: Input Processing

1. Read the specified input file
2. Validate the file exists
3. Parse the content

### Phase 2: Analysis

1. Analyze the content
2. Generate findings

### Phase 3: Output

1. Format the results
2. Display to user

## Output Format

Results are displayed inline in the conversation.

## Examples

```
User: /sample-command document.md

Claude: Analyzing document.md...

Analysis complete. Found 5 items.
```
