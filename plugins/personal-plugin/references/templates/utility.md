<!-- ============================================================
     UTILITY COMMAND TEMPLATE

     Canonical Section Order:
     1. Frontmatter (description, allowed-tools)
     2. Title (# Command Name)
     3. Brief description paragraph
     4. Input Validation
     5. Instructions (organized as phases)
     6. Output Format (validation report)
     7. Examples
     8. Performance (if applicable)

     Pattern References:
     - Validation: references/patterns/validation.md
     - Output: references/patterns/output.md
     - Testing: references/patterns/testing.md (for --dry-run)

     Note: Utility commands perform validation/maintenance tasks
     ============================================================ -->

<!-- SECTION 1: FRONTMATTER -->
---
description: {{DESCRIPTION}}
---

<!-- SECTION 2: TITLE -->
# {{TITLE}}

<!-- SECTION 3: BRIEF DESCRIPTION -->
{{INTRO_PARAGRAPH}}

<!-- SECTION 4: INPUT VALIDATION -->
## Input Validation

**Required Arguments:**
- `<{{ARG_NAME}}>` - {{ARG_DESCRIPTION}}

**Optional Arguments:**
- `--all` - Apply to all targets
- `--fix` - Attempt to auto-fix issues
- `--verbose` - Show detailed output
- `--strict` - Fail on any violation (treats warnings as errors)
- `--report` - Generate detailed report file

**Validation:**
If arguments are missing, display:
```
Error: Missing required argument

Usage: /{{COMMAND_NAME}} <{{ARG_NAME}}> [--all] [--fix] [--verbose] [--strict] [--report]

Examples:
  /{{COMMAND_NAME}} target-name          # Process single target
  /{{COMMAND_NAME}} --all                # Process all targets
  /{{COMMAND_NAME}} target-name --fix    # Auto-fix issues
  /{{COMMAND_NAME}} --all --strict       # Fail on any violation

Arguments:
  <{{ARG_NAME}}>  {{ARG_DESCRIPTION}}
  --all           Process all targets
  --fix           Auto-fix issues
  --verbose       Show detailed output
  --strict        Fail on any violation
  --report        Generate report file
```

If target is not found (and --all not specified), display:
```
Error: Target '[name]' not found.

Available targets:
  - target-1
  - target-2

Use --all to process all targets.
```

See `references/patterns/validation.md` for error message format.

<!-- SECTION 5: INSTRUCTIONS -->
## Instructions

### Phase 1: Validation

Verify the target has the required structure and files.

#### 1.1 Structure Check

**Check for:**
```
expected/
  structure/
    file.ext              # REQUIRED
  optional/               # Optional
    file.ext
```

**Report:**
```
Structure Validation
--------------------
[PASS] Required files exist
[PASS] Optional structure present
```

Or on failure:
```
[FAIL] Required file missing at expected/location
```

#### 1.2 Content Validation

**Check:**
- Required fields present
- Format is valid
- Values are correct

**Report:**
```
Content Validation
------------------
[PASS] Valid format
[PASS] Required fields present
[PASS] Values valid
```

### Phase 2: Processing

Execute the main utility function.

#### 2.1 [Processing Step 1]

[Description of what this step does]

**Check:**
- [Validation point 1]
- [Validation point 2]

**Report:**
```
[PASS] Validation point 1
[WARN] Validation point 2 - minor issue
```

#### 2.2 [Processing Step 2]

[Description of what this step does]

### Phase 3: Summary Report

Generate a final summary.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{TITLE}}: [target-name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Validation      [PASS]
Phase 2: Processing      [PASS] (X items)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues Found:
  Errors:   0
  Warnings: 2

Warnings:
  1. [Warning description]
  2. [Warning description]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Result: PASS (with warnings)
```

See `references/patterns/output.md` for completion summary format.

<!-- SECTION 6: OUTPUT FORMAT -->
## Output Format

### Exit Codes (for CI/Script Use)

When processing completes:
- **Exit 0:** All checks passed (warnings OK)
- **Exit 1:** One or more errors found
- **Exit 1 (--strict):** Any issues found (warnings OR errors)

### Auto-Fix Mode (--fix)

When `--fix` is specified, attempt to fix simple issues:

| Issue | Auto-Fix Action |
|-------|-----------------|
| [Issue type 1] | [Fix action] |
| [Issue type 2] | [Fix action] |

**Report fixes:**
```
Auto-Fix Applied:
  target: [Description of fix]

X issues fixed. Re-run to confirm.
```

### Strict Mode (--strict)

When `--strict` is specified:
- All WARN results become FAIL results
- Exit code is 1 if ANY issues found

See `references/patterns/testing.md` for --strict behavior.

### Report Mode (--report)

When `--report` is specified:
- Generate detailed report to `reports/[type]-[timestamp].md`
- Include per-target breakdown and recommendations

<!-- SECTION 7: EXAMPLES -->
## Examples

### Single Target
```
User: /{{COMMAND_NAME}} target-name

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing: target-name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Validation
-------------------
[PASS] Structure valid
[PASS] Content valid

Phase 2: Processing
-------------------
[PASS] Step 1 complete
[WARN] Step 2 has minor issue

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Errors:   0
Warnings: 1

Result: PASS (with warnings)
Exit code: 0
```

### All Targets
```
User: /{{COMMAND_NAME}} --all

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing All Targets
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Target: target-1
----------------
[PASS] All checks passed

Target: target-2
----------------
[PASS] All checks passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Targets processed: 2
Total errors:      0
Total warnings:    0

Result: PASS
Exit code: 0
```

## Error Handling

- **File read failure:** Report file path and skip to next
- **Parse error:** Report detailed error with line number
- **Permission denied:** Report and suggest checking permissions
