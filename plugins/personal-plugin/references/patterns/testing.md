# Testing Patterns

This document defines patterns for testing commands, argument handling, and dry-run behavior.

## Argument Testing

Commands SHOULD be tested for argument handling to ensure consistent user experience and helpful error messages.

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

## Test Checklist

Use this checklist when testing command argument handling:

- [ ] Missing required argument shows usage with example
- [ ] Invalid argument value shows clear error and guidance
- [ ] Optional arguments use documented defaults
- [ ] All documented flags work as described
- [ ] --dry-run (if supported) produces no side effects
- [ ] --force (if supported) overrides with warning
- [ ] Unknown arguments show clear error
- [ ] Error messages include example of correct usage

## Dry-Run Pattern

Commands with side effects SHOULD support `--dry-run` for safe testing.

### Dry-Run Behavior

When `--dry-run` is specified:
- Perform all analysis phases normally
- Show what changes would be made
- Prefix all proposed actions with `[DRY-RUN]` to clearly indicate preview mode
- Do NOT execute any modifications
- Skip all confirmation prompts (nothing will be executed anyway)

### Dry-Run Output Format

```
[DRY-RUN] Phase 1: Preparation
------------------------------
[DRY-RUN] Would check prerequisites...
[DRY-RUN] Found X items to process

[DRY-RUN] Phase 2: Planned Changes
----------------------------------
[DRY-RUN] Would perform action 1
[DRY-RUN] Would perform action 2

No changes made. Run without --dry-run to execute.
```

## Commands with Argument Handling

| Command | Required Args | Optional Args | Flags |
|---------|--------------|---------------|-------|
| `/define-questions` | `<document-path>` | `--format` | `--force`, `--preview` |
| `/ask-questions` | `<questions-file>` | | `--force` |
| `/finish-document` | `<document-path>` | | `--auto`, `--force` |
| `/assess-document` | `<document-path>` | | |
| `/review-pr` | | `<pr-number>` | |
| `/convert-markdown` | `<markdown-file>` | `--output` | |
| `/validate-plugin` | `<plugin-name>` | | `--all`, `--fix`, `--verbose`, `--strict`, `--report` |
