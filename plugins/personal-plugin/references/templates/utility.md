---
description: {{DESCRIPTION}}
---

# {{TITLE}}

{{INTRO_PARAGRAPH}}

## Input Validation

**Required Arguments:**
- `<{{ARG_NAME}}>` - {{ARG_DESCRIPTION}}

**Optional Arguments:**
- `--all` - Apply to all targets
- `--fix` - Attempt to auto-fix issues
- `--verbose` - Show detailed output

**Validation:**
If arguments are missing, display:
```
Usage: /{{COMMAND_NAME}} <{{ARG_NAME}}> [--all] [--fix] [--verbose]

Examples:
  /{{COMMAND_NAME}} target-name          # Process single target
  /{{COMMAND_NAME}} --all                # Process all targets
  /{{COMMAND_NAME}} target-name --fix    # Auto-fix issues
```

If target is not found (and --all not specified), display:
```
Error: Target '[name]' not found.

Available targets:
  - target-1
  - target-2

Use --all to process all targets.
```

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
----------------------------------------------
{{TITLE}}: [target-name]
----------------------------------------------

Phase 1: Validation      [PASS]
Phase 2: Processing      [PASS] (X items)

----------------------------------------------

Issues Found:
  Errors:   0
  Warnings: 2

Warnings:
  1. [Warning description]
  2. [Warning description]

----------------------------------------------

Result: PASS (with warnings)
```

### Exit Codes (for CI/Script Use)

When processing completes:
- **Exit 0:** All checks passed (warnings OK)
- **Exit 1:** One or more errors found

## Auto-Fix Mode (--fix)

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

## Error Handling

- **File read failure:** Report file path and skip to next
- **Parse error:** Report detailed error with line number
- **Permission denied:** Report and suggest checking permissions

## Example Usage

```
User: /{{COMMAND_NAME}} target-name

Claude:
----------------------------------------------
Processing: target-name
----------------------------------------------

Phase 1: Validation
-------------------
[PASS] Structure valid
[PASS] Content valid

Phase 2: Processing
-------------------
[PASS] Step 1 complete
[WARN] Step 2 has minor issue

----------------------------------------------
Summary
----------------------------------------------

Errors:   0
Warnings: 1

Result: PASS (with warnings)
Exit code: 0
```

```
User: /{{COMMAND_NAME}} --all

Claude:
----------------------------------------------
Processing All Targets
----------------------------------------------

Target: target-1
----------------
[PASS] All checks passed

Target: target-2
----------------
[PASS] All checks passed

----------------------------------------------
Overall Summary
----------------------------------------------

Targets processed: 2
Total errors:      0
Total warnings:    0

Result: PASS
Exit code: 0
```
