---
description: Validate plugin structure, frontmatter, and content for consistency and correctness
---

# Validate Plugin Command

Perform comprehensive validation of a plugin's structure, frontmatter, version synchronization, and content quality. Use this command before committing changes to catch common errors.

## Input Validation

**Required Arguments:**
- `<plugin-name>` - Name of the plugin to validate (e.g., `personal-plugin`, `bpmn-plugin`)

**Optional Arguments:**
- `--all` - Validate all plugins in the repository
- `--fix` - Attempt to auto-fix simple issues (formatting, missing fields)
- `--verbose` - Show detailed output for all checks (not just failures)
- `--strict` - Fail on any pattern violation (treats warnings as errors)
- `--report` - Generate detailed compliance report to `reports/validation-[timestamp].md`
- `--scorecard` - Generate maturity scorecard for plugins (see Maturity Scorecard section)

**Validation:**
If arguments are missing, display:
```
Usage: /validate-plugin <plugin-name> [--all] [--fix] [--verbose] [--strict] [--report] [--scorecard]

Examples:
  /validate-plugin personal-plugin          # Validate single plugin
  /validate-plugin --all                    # Validate all plugins
  /validate-plugin bpmn-plugin --verbose    # Detailed output
  /validate-plugin personal-plugin --fix    # Auto-fix simple issues
  /validate-plugin --all --strict           # Fail on any violation
  /validate-plugin --all --report           # Generate compliance report
  /validate-plugin --all --scorecard        # Generate maturity scorecard

Available plugins:
  - personal-plugin
  - bpmn-plugin
```

If plugin-name is not found (and --all not specified), display:
```
Error: Plugin '[name]' not found.

Available plugins:
  - personal-plugin
  - bpmn-plugin

Use --all to validate all plugins.
```

## Instructions

### Phase 1: Structure Validation

Verify the plugin has the required directory structure and files.

#### 1.1 Required Files Check

**Check for:**
```
plugins/[plugin-name]/
  .claude-plugin/
    plugin.json              # REQUIRED
  commands/                  # At least one of commands/ or skills/
    *.md
  skills/
    *.md
```

**Report:**
```
Structure Validation
--------------------
[PASS] plugin.json exists
[PASS] commands/ directory exists (15 files)
[PASS] skills/ directory exists (1 file)
```

Or on failure:
```
[FAIL] plugin.json missing at plugins/[name]/.claude-plugin/plugin.json
```

#### 1.2 plugin.json Validation

**Check:**
- File is valid JSON (parseable)
- Required fields present: `name`, `description`, `version`
- `version` follows semver format (X.Y.Z)

**Report:**
```
plugin.json Validation
----------------------
[PASS] Valid JSON syntax
[PASS] Required field 'name' present
[PASS] Required field 'description' present
[PASS] Required field 'version' present (1.6.0)
[PASS] Version follows semver format
```

### Phase 2: Frontmatter Validation

Check all `.md` files in commands/ and skills/ directories.

#### 2.1 YAML Syntax

For each markdown file:
1. Check for frontmatter delimiters (`---` at start)
2. Parse YAML between delimiters
3. Report any syntax errors

**Report:**
```
Frontmatter Validation: commands/assess-document.md
--------------------------------------------------
[PASS] Frontmatter delimiters present
[PASS] Valid YAML syntax
```

Or on failure:
```
[FAIL] commands/broken-command.md
      Line 3: Invalid YAML - unexpected character ':'
```

#### 2.2 Required Fields

**Check:**
- `description` field present and non-empty

**Report:**
```
[PASS] Required field 'description' present
```

Or:
```
[FAIL] commands/my-command.md
      Missing required field: description
```

#### 2.3 Forbidden Fields

**Check:**
- No `name` field present (per CLAUDE.md conventions)

**Report:**
```
[PASS] No forbidden 'name' field
```

Or:
```
[FAIL] commands/my-command.md
      Forbidden field 'name' found - filename determines command name
      Remove: name: my-command
```

#### 2.4 Optional Field Validation

If `allowed-tools` is present:
- Check it's a valid string format
- Warn if format appears incorrect (e.g., missing parentheses)

**Report:**
```
[PASS] allowed-tools format valid: Bash(git:*)
```

Or:
```
[WARN] commands/my-command.md
      allowed-tools format may be invalid: 'git:*'
      Expected format: ToolName(pattern) or ToolName
```

### Phase 3: Version Synchronization

Verify versions match across all configuration files.

#### 3.1 Version Locations

**Check these files:**
- `plugins/[plugin-name]/.claude-plugin/plugin.json` -> `version` field
- `.claude-plugin/marketplace.json` -> plugin entry's `version` field

**Report:**
```
Version Synchronization
-----------------------
plugin.json version:      1.6.0
marketplace.json version: 1.6.0
[PASS] Versions are synchronized
```

Or:
```
[FAIL] Version mismatch
      plugin.json:      1.6.0
      marketplace.json: 1.5.0

      Run '/bump-version [plugin] patch' to synchronize.
```

### Phase 4: Content Validation

Check markdown content quality.

#### 4.1 Markdown Parsing

Verify markdown parses without errors:
- Check for unclosed code blocks
- Check for malformed links
- Check for unbalanced formatting

**Report:**
```
Content Validation: commands/assess-document.md
----------------------------------------------
[PASS] Markdown parses correctly
```

Or:
```
[FAIL] commands/broken.md
      Line 45: Unclosed code block (opened with ```)
```

#### 4.2 Code Block Language Specifiers

Check that fenced code blocks have language specifiers:

```markdown
# Good
```json
{"key": "value"}
```

# Bad - missing language
```
{"key": "value"}
```
```

**Report:**
```
[PASS] All code blocks have language specifiers
```

Or:
```
[WARN] commands/my-command.md
      Line 23: Code block missing language specifier
      Line 67: Code block missing language specifier

      Add language (e.g., ```json, ```bash, ```markdown)
```

#### 4.3 Internal Link Validation

Check that internal file references exist:

**Check for patterns like:**
- `See common-patterns.md`
- `[link](../references/file.md)`
- References to other commands

**Report:**
```
[PASS] All internal references valid
```

Or:
```
[WARN] commands/my-command.md
      Line 15: Reference 'common-patterns.md' not found
      Expected at: plugins/personal-plugin/references/common-patterns.md
```

### Phase 5: Namespace Collision Detection

When running with `--all`, check for command/skill naming collisions across plugins.

#### 5.1 Collect All Command Names

For each plugin, build a registry of command and skill names:

```
Plugin: personal-plugin
  Commands: analyze-transcript, ask-questions, assess-document, ...
  Skills: help, ship

Plugin: bpmn-plugin
  Commands: (none)
  Skills: bpmn-generator, bpmn-to-drawio, help
```

#### 5.2 Detect Collisions

Compare names across plugins:

```
Namespace Collision Detection
-----------------------------
[WARN] Collision detected: /help
       - personal-plugin/skills/help.md
       - bpmn-plugin/skills/help.md

       Users must use explicit namespace:
         /personal-plugin:help
         /bpmn-plugin:help
```

If no collisions:
```
[PASS] No namespace collisions detected
```

#### 5.3 Single Plugin Mode

When validating a single plugin (not `--all`), skip collision detection and display:
```
Note: Run with --all to check for naming collisions across plugins.
```

### Phase 6: Dependency Validation

Check if plugin.json declares dependencies and validate them.

#### 6.1 Parse Dependencies

If `dependencies` field exists in plugin.json:
```json
{
  "dependencies": {
    "personal-plugin": ">=2.0.0"
  }
}
```

#### 6.2 Validate Dependencies

For each declared dependency:
1. Check if the plugin exists in the marketplace
2. Parse the version requirement (semver syntax)
3. Compare against the installed plugin version

**Report:**
```
Dependency Validation
---------------------
[PASS] personal-plugin: >=2.0.0 (installed: 2.0.0)
[FAIL] missing-plugin: ^1.0.0 (not found)
[FAIL] outdated-plugin: >=3.0.0 (installed: 2.5.0)
```

Or if no dependencies declared:
```
[PASS] No dependencies declared
```

#### 6.3 Semver Validation

Check that version strings follow semver patterns:
- `>=X.Y.Z`, `<=X.Y.Z`, `>X.Y.Z`, `<X.Y.Z`
- `^X.Y.Z` (caret range - compatible with)
- `~X.Y.Z` (tilde range - approximately)
- `X.Y.Z` (exact version)

**Report invalid version syntax:**
```
[FAIL] Invalid version syntax in dependencies
       bpmn-plugin: "latest" (not valid semver)

       Valid formats: >=1.0.0, ^1.0.0, ~1.0.0, 1.0.0
```

### Phase 7: Pattern Compliance Checks

Validate commands against the schema defined in `schemas/command.json` and pattern conventions.

#### 7.1 Command Frontmatter Schema Validation

For each command markdown file, validate frontmatter against `schemas/command.json`:

**Check:**
- `description` field present (required)
- `description` length between 10-200 characters
- No forbidden `name` field present
- `allowed-tools` format valid if present

**Report:**
```
Command Schema Validation
-------------------------
[PASS] commands/assess-document.md - Schema valid
[PASS] commands/define-questions.md - Schema valid
[WARN] commands/my-command.md - description too short (8 chars, minimum 10)
```

#### 7.2 Required Sections Check

Verify each command contains required sections:

**Required Sections:**
1. `## Input Validation` - Must document arguments
2. `## Instructions` - Must have step-by-step guidance

**Report:**
```
Required Sections Validation
----------------------------
[PASS] commands/assess-document.md - All required sections present
[FAIL] commands/my-command.md - Missing section: Input Validation
[WARN] commands/other.md - Missing section: Instructions
```

#### 7.3 Output Naming Convention Compliance

Check that commands generating output follow the naming pattern:
`[type]-[source]-[timestamp].[ext]`

**Check for patterns like:**
- Output file naming in documentation
- Examples showing correct naming

**Report:**
```
Output Naming Compliance
------------------------
[PASS] commands/define-questions.md - Follows naming convention
[WARN] commands/my-command.md - Non-standard output naming: 'output.json'
       Expected: [type]-[source]-YYYYMMDD-HHMMSS.[ext]
```

#### 7.4 Error Message Format Adherence

Check that commands document error handling following the standard format:

**Standard Format:**
```
Error: [Brief description]

Expected: [What was expected]
Received: [What was provided]

Suggestion: [How to fix]
```

**Report:**
```
Error Format Compliance
-----------------------
[PASS] commands/define-questions.md - Error format compliant
[WARN] commands/my-command.md - Non-standard error format at line 45
```

#### 7.5 Flag Usage Consistency

Check that flags follow naming conventions:

| Standard Flag | Purpose |
|---------------|---------|
| `--all` | Apply to all targets |
| `--fix` | Auto-fix issues |
| `--force` | Proceed despite validation errors |
| `--verbose` | Show detailed output |
| `--preview` | Preview before saving |
| `--dry-run` | Simulate without changes |
| `--strict` | Fail on any violation |
| `--report` | Generate report file |

**Report:**
```
Flag Consistency Check
----------------------
[PASS] All flags follow standard conventions
```

Or:
```
[WARN] commands/my-command.md - Non-standard flag '--skip-validation'
       Consider using '--force' for similar behavior
```

### Phase 8: Summary Report

Generate a final validation summary.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Validation: [plugin-name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure Validation     [PASS]
Frontmatter Validation   [PASS] (15 files checked)
Version Synchronization  [PASS]
Content Validation       [WARN] (2 warnings)
Namespace Collisions     [WARN] (1 collision)  # Only with --all
Dependency Validation    [PASS]
Pattern Compliance       [PASS] (all commands checked)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues Found:
  Errors:   0
  Warnings: 3

Warnings:
  1. commands/my-command.md:23 - Code block missing language specifier
  2. commands/my-command.md:67 - Code block missing language specifier
  3. Namespace collision: /help (use /personal-plugin:help)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Result: PASS (with warnings)

Warnings don't block commits but should be addressed.
```

### Exit Codes (for CI/Script Use)

When validation completes:
- **Exit 0:** All checks passed (warnings OK)
- **Exit 1:** One or more errors found

Report the exit code at the end:
```
Validation complete. Exit code: 0 (success)
```

Or:
```
Validation complete. Exit code: 1 (errors found)
```

## Auto-Fix Mode (--fix)

When `--fix` is specified, attempt to fix simple issues:

| Issue | Auto-Fix Action |
|-------|-----------------|
| Missing frontmatter | Add template frontmatter |
| Empty description | Prompt for description |
| Forbidden name field | Remove the field |
| Code block without language | Add `text` as default |

**Report fixes:**
```
Auto-Fix Applied:
  commands/my-command.md: Removed forbidden 'name' field
  commands/other.md: Added 'text' language to code block at line 23

2 issues fixed. Re-run validation to confirm.
```

## Strict Mode (--strict)

When `--strict` is specified, treat warnings as errors:

**Behavior:**
- All WARN results become FAIL results
- Exit code is 1 if ANY issues found (warnings OR errors)
- Recommended for CI/CD pipelines

**Report with --strict:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Validation: personal-plugin (STRICT MODE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure Validation     [PASS]
Frontmatter Validation   [PASS]
Version Synchronization  [PASS]
Content Validation       [FAIL] (2 issues - strict mode)
Pattern Compliance       [PASS]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Result: FAIL (strict mode treats warnings as errors)
Exit code: 1

Fix all issues or run without --strict to allow warnings.
```

## Report Mode (--report)

When `--report` is specified, generate a detailed compliance report file:

**Output:** `reports/validation-[timestamp].md`

**Report Contents:**
- Full validation results for all phases
- Per-command compliance breakdown
- Pattern adherence statistics
- Recommendations for improvement

**Example Report Structure:**
```markdown
# Plugin Validation Report

**Generated:** 2026-01-15T10:30:00Z
**Plugin:** personal-plugin
**Version:** 2.3.0

## Executive Summary

| Phase | Status | Issues |
|-------|--------|--------|
| Structure | PASS | 0 |
| Frontmatter | PASS | 0 |
| Version Sync | PASS | 0 |
| Content | WARN | 2 |
| Pattern Compliance | PASS | 0 |

**Overall:** PASS (with 2 warnings)

## Detailed Findings

### Content Validation

#### Warnings
1. **commands/clean-repo.md:45** - Code block missing language specifier
2. **commands/clean-repo.md:89** - Code block missing language specifier

### Pattern Compliance

All 21 commands follow pattern conventions:
- Required sections: 100% compliant
- Output naming: 100% compliant
- Error format: 100% compliant
- Flag consistency: 100% compliant

## Recommendations

1. Add language specifiers to code blocks in clean-repo.md
2. Consider adding Performance section to long-running commands

---
*Generated by /validate-plugin --report*
```

**Console Output with --report:**
```
Validation complete. Exit code: 0

Report saved to: reports/validation-20260115-103000.md
```

## Maturity Scorecard Mode (--scorecard)

When `--scorecard` is specified, evaluate plugins against a 4-level maturity model and generate a comprehensive scorecard.

### Maturity Levels

| Level | Name | Criteria | Score Range |
|-------|------|----------|-------------|
| **1** | Basic | Valid plugin.json, commands parse without errors | 0-25% |
| **2** | Standard | Help.md complete, all patterns followed, frontmatter valid | 26-50% |
| **3** | Complete | Tests exist, all standard flags implemented, no warnings | 51-75% |
| **4** | Exemplary | Full documentation, CI validation passing, 90%+ test coverage | 76-100% |

### Level 1 (Basic) Criteria

A plugin achieves Level 1 when:
- `plugin.json` exists and contains valid JSON
- Required fields present: `name`, `description`, `version`
- Version follows semver format (X.Y.Z)
- All command/skill `.md` files have valid frontmatter
- YAML in frontmatter parses without errors

### Level 2 (Standard) Criteria

A plugin achieves Level 2 when all Level 1 criteria are met, plus:
- `help.md` exists and documents all commands/skills
- All commands have `## Input Validation` section
- All commands have `## Instructions` section
- No forbidden `name` field in frontmatter
- Output naming follows convention: `[type]-[source]-[timestamp].[ext]`
- Error messages follow standard format

### Level 3 (Complete) Criteria

A plugin achieves Level 3 when all Level 2 criteria are met, plus:
- Tests exist in `tests/` directory for the plugin
- Standard flags implemented where applicable:
  - `--verbose` for detailed output
  - `--preview` for commands generating output
  - `--force` for validation override
- Zero warnings in validation output
- All code blocks have language specifiers
- All internal references resolve correctly

### Level 4 (Exemplary) Criteria

A plugin achieves Level 4 when all Level 3 criteria are met, plus:
- Documentation complete (README, CONTRIBUTING if applicable)
- CI/CD workflow validates the plugin
- Test coverage at 90% or higher
- Examples provided for all commands
- Performance notes for long-running commands

### Scorecard Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Maturity Scorecard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugin: personal-plugin
-----------------------
Level 1 (Basic)        [################] 100%
  [x] Valid plugin.json
  [x] Required fields present
  [x] Semver version format
  [x] Frontmatter parses

Level 2 (Standard)     [################] 100%
  [x] help.md complete
  [x] Input Validation sections
  [x] Instructions sections
  [x] No forbidden fields
  [x] Output naming compliant

Level 3 (Complete)     [############----]  75%
  [x] Tests exist
  [x] Standard flags implemented
  [ ] Zero warnings (2 warnings found)
  [x] Code block languages

Level 4 (Exemplary)    [########--------]  50%
  [x] CI/CD workflow exists
  [ ] Test coverage 90%+ (currently 85%)
  [x] Examples in all commands
  [ ] Performance notes missing

Current Level: 3 (Complete)
Overall Score: 81%

-----------------------
Plugin: bpmn-plugin
-----------------------
Level 1 (Basic)        [################] 100%
Level 2 (Standard)     [################] 100%
Level 3 (Complete)     [################] 100%
Level 4 (Exemplary)    [################] 100%

Current Level: 4 (Exemplary)
Overall Score: 100%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aggregate Scorecard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Plugin | Level | Score | Status |
|--------|-------|-------|--------|
| personal-plugin | 3 | 81% | Complete |
| bpmn-plugin | 4 | 100% | Exemplary |

Average Score: 90.5%
Plugins at Level 4: 1/2 (50%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Improvement Suggestions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

personal-plugin:
  To reach Level 4 (Exemplary):
  1. Fix 2 code block warnings (add language specifiers)
  2. Increase test coverage to 90%+ (currently 85%)
  3. Add Performance section to long-running commands

Priority: Address warnings first (quick win for Level 3 completion)
```

### Scorecard Calculation Logic

**Level Score Calculation:**
- Each level has a set of criteria (checkboxes)
- Level percentage = (criteria met / total criteria) * 100
- A level is "achieved" when 100% of its criteria are met

**Overall Score Calculation:**
```
Overall Score = (L1_score * 0.1) + (L2_score * 0.2) + (L3_score * 0.3) + (L4_score * 0.4)
```

**Current Level Assignment:**
- Level 1: All L1 criteria met
- Level 2: Level 1 + all L2 criteria met
- Level 3: Level 2 + all L3 criteria met
- Level 4: Level 3 + all L4 criteria met

### Example Usage with Scorecard

```
User: /validate-plugin --all --scorecard

Claude: [Evaluates all plugins and generates scorecard]

Plugin Maturity Scorecard generated.

Summary:
- personal-plugin: Level 3 (81%)
- bpmn-plugin: Level 4 (100%)

Average marketplace maturity: 90.5%

Top improvement opportunities:
1. personal-plugin: Add language specifiers to reach 100% Level 3
2. personal-plugin: Increase test coverage for Level 4
```

## Error Handling

- **File read failure:** Report file path and skip to next
- **JSON parse error:** Report detailed error with line number
- **YAML parse error:** Report error with line number and context
- **Permission denied:** Report and suggest checking file permissions

## Example Usage

```
User: /validate-plugin personal-plugin

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validating Plugin: personal-plugin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Structure Validation
-----------------------------
[PASS] plugin.json exists
[PASS] commands/ directory (15 files)
[PASS] skills/ directory (1 file)
[PASS] references/ directory (1 file)

Phase 2: Frontmatter Validation
-------------------------------
Checking 16 markdown files...
[PASS] All frontmatter valid
[PASS] All descriptions present
[PASS] No forbidden 'name' fields

Phase 3: Version Synchronization
--------------------------------
[PASS] plugin.json: 1.6.0
[PASS] marketplace.json: 1.6.0
[PASS] Versions synchronized

Phase 4: Content Validation
---------------------------
[PASS] All markdown parses correctly
[WARN] 2 code blocks missing language specifiers
[PASS] All internal references valid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validation Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Errors:   0
Warnings: 2

Warnings:
  1. commands/clean-repo.md:45 - Code block missing language specifier
  2. commands/clean-repo.md:89 - Code block missing language specifier

Result: PASS (with warnings)
Exit code: 0

Tip: Run with --fix to auto-add language specifiers.
```

```
User: /validate-plugin --all

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validating All Plugins
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugin: personal-plugin
-----------------------
[PASS] Structure valid
[PASS] Frontmatter valid (16 files)
[PASS] Versions synchronized
[WARN] 2 content warnings

Plugin: bpmn-plugin
-------------------
[PASS] Structure valid
[PASS] Frontmatter valid (2 files)
[PASS] Versions synchronized
[PASS] Content valid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugins validated: 2
Total errors:      0
Total warnings:    2

Result: PASS (with warnings)
Exit code: 0
```
