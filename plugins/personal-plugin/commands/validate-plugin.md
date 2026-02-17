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
```text
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
```text
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
```text
plugins/[plugin-name]/
  .claude-plugin/
    plugin.json              # REQUIRED
  commands/                  # At least one of commands/ or skills/
    *.md                     # Flat structure: filename becomes command name
  skills/
    [skill-name]/            # REQUIRED: Nested directory structure
      SKILL.md               # REQUIRED: Must be exactly SKILL.md (uppercase)
```

**Report:**
```text
Structure Validation
--------------------
[PASS] plugin.json exists
[PASS] commands/ directory exists (15 files)
[PASS] skills/ directory exists (3 skills)
```

Or on failure:
```text
[FAIL] plugin.json missing at plugins/[name]/.claude-plugin/plugin.json
```

#### 1.2 Skill Directory Structure Validation

**CRITICAL:** Skills must use a nested directory structure with `SKILL.md` files (not flat `.md` files).

**Check for each item in skills/ directory:**
1. Item is a directory (not a file)
2. Directory contains `SKILL.md` (exact name, uppercase)

**Valid structure:**
```text
skills/
  ship/
    SKILL.md              # ✓ Correct
  help/
    SKILL.md              # ✓ Correct
```

**Invalid structures:**
```text
skills/
  ship.md                 # ✗ Flat file - NOT discovered by Claude Code
  help.md                 # ✗ Flat file - NOT discovered by Claude Code
  broken-skill/
    skill.md              # ✗ Wrong filename - must be SKILL.md (uppercase)
```

**Report:**
```text
Skill Structure Validation
--------------------------
[PASS] skills/ship/SKILL.md - Valid skill structure
[PASS] skills/help/SKILL.md - Valid skill structure
[PASS] skills/research-topic/SKILL.md - Valid skill structure
```

Or on failure:
```text
[FAIL] Invalid skill structure detected

      The following skills will NOT be discovered by Claude Code:

      skills/ship.md
        Problem: Flat file in skills/ directory
        Fix: Move to skills/ship/SKILL.md

      skills/broken-skill/skill.md
        Problem: Wrong filename (must be SKILL.md, uppercase)
        Fix: Rename to skills/broken-skill/SKILL.md

      Skills require a nested directory structure:
        skills/[skill-name]/SKILL.md

      Run with --fix to automatically restructure skills.
```

**Auto-fix with --fix:**
When `--fix` is specified, automatically restructure invalid skills:
```text
Auto-Fix Applied:
  skills/ship.md -> skills/ship/SKILL.md (created directory, moved file)
  skills/help.md -> skills/help/SKILL.md (created directory, moved file)

2 skills restructured. Skills should now be discoverable.
```

#### 1.2 plugin.json Validation

**Check:**
- File is valid JSON (parseable)
- Required fields present: `name`, `description`, `version`
- `version` follows semver format (X.Y.Z)

**Report:**
```text
plugin.json Validation
----------------------
[PASS] Valid JSON syntax
[PASS] Required field 'name' present
[PASS] Required field 'description' present
[PASS] Required field 'version' present (1.6.0)
[PASS] Version follows semver format
```

#### 1.3 Marketplace Schema Validation

Validate that marketplace.json plugin entries only contain fields recognized by Claude Code's schema.

**Valid Plugin Entry Fields:**
- `name` (required)
- `source` (required)
- `description` (required)
- `version` (required)
- `category` (optional)
- `tags` (optional)

**Known Invalid Fields:**
- `last_updated` - Not part of Claude Code's plugin schema

**Check:**
1. Parse `.claude-plugin/marketplace.json`
2. For each plugin entry, check for unrecognized fields
3. Flag any fields not in the valid fields list

**Report:**
```text
Marketplace Schema Validation
-----------------------------
[PASS] All plugin entries use valid schema fields
```

Or on failure:
```text
[FAIL] marketplace.json contains invalid schema fields

      Plugin 'personal-plugin' has unrecognized fields:
        - last_updated (line 18)

      Claude Code's schema does not recognize these fields.
      This will cause "schema validation failed" errors when
      other repositories try to install plugins from this marketplace.

      Remove these fields from marketplace.json to fix.
```

**Auto-fix with --fix:**
When `--fix` is specified, automatically remove unrecognized fields:
```text
Auto-Fix Applied:
  marketplace.json: Removed 'last_updated' from plugin 'personal-plugin'
  marketplace.json: Removed 'last_updated' from plugin 'bpmn-plugin'

2 invalid fields removed. Marketplace schema now valid.
```

### Phase 2: Frontmatter Validation

Check all `.md` files in commands/ and skills/ directories.

#### 2.1 YAML Syntax

For each markdown file:
1. Check for frontmatter delimiters (`---` at start)
2. Parse YAML between delimiters
3. Report any syntax errors

**Report:**
```text
Frontmatter Validation: commands/assess-document.md
--------------------------------------------------
[PASS] Frontmatter delimiters present
[PASS] Valid YAML syntax
```

Or on failure:
```text
[FAIL] commands/broken-command.md
      Line 3: Invalid YAML - unexpected character ':'
```

#### 2.2 Required Fields

**Check:**
- `description` field present and non-empty

**Report:**
```text
[PASS] Required field 'description' present
```

Or:
```text
[FAIL] commands/my-command.md
      Missing required field: description
```

#### 2.3 Name Field Validation (Commands vs Skills)

**CRITICAL:** Commands and skills have OPPOSITE requirements for the `name` field:

| Component | `name` Field | Reason |
|-----------|--------------|--------|
| Commands | **FORBIDDEN** | Filename determines command name |
| Skills | **REQUIRED** | Needed for skill registration and discovery |

**For Commands (files in `commands/`):**

Check that no `name` field is present.

**Report:**
```text
[PASS] commands/my-command.md - No forbidden 'name' field
```

Or:
```text
[FAIL] commands/my-command.md
      Forbidden field 'name' found - filename determines command name
      Remove: name: my-command
```

**For Skills (files in `skills/*/SKILL.md`):**

Check that `name` field IS present and matches the directory name.

**Report:**
```text
[PASS] skills/ship/SKILL.md - Required 'name' field present and matches directory
```

Or:
```text
[FAIL] skills/ship/SKILL.md
      Missing required 'name' field in skill frontmatter
      Add: name: ship

      Skills REQUIRE the 'name' field for Claude Code to discover them.
      The name must match the skill's directory name.
```

Or if name doesn't match directory:
```text
[FAIL] skills/ship/SKILL.md
      'name' field doesn't match directory name
      Frontmatter: name: shipper
      Directory: ship

      Fix: Change 'name' to match directory: name: ship
```

#### 2.4 Optional Field Validation

If `allowed-tools` is present:
- Check it's a valid string format
- Warn if format appears incorrect (e.g., missing parentheses)

**Report:**
```text
[PASS] allowed-tools format valid: Bash(git:*)
```

Or:
```text
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
```text
Version Synchronization
-----------------------
plugin.json version:      1.6.0
marketplace.json version: 1.6.0
[PASS] Versions are synchronized
```

Or:
```text
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
```text
Content Validation: commands/assess-document.md
----------------------------------------------
[PASS] Markdown parses correctly
```

Or:
```text
[FAIL] commands/broken.md
      Line 45: Unclosed code block (opened with ```)
```

#### 4.2 Code Block Language Specifiers

Check that fenced code blocks have language specifiers:

````markdown
# Good
```json
{"key": "value"}
```

# Bad - missing language
```
{"key": "value"}
```
````

**Report:**
```text
[PASS] All code blocks have language specifiers
```

Or:
```text
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
```text
[PASS] All internal references valid
```

Or:
```text
[WARN] commands/my-command.md
      Line 15: Reference 'common-patterns.md' not found
      Expected at: plugins/personal-plugin/references/common-patterns.md
```

### Phase 5: Namespace Collision Detection

When running with `--all`, check for command/skill naming collisions across plugins.

#### 5.1 Collect All Command Names

For each plugin, build a registry of command and skill names:

```text
Plugin: personal-plugin
  Commands: analyze-transcript, ask-questions, assess-document, ...
  Skills: help, ship

Plugin: bpmn-plugin
  Commands: (none)
  Skills: bpmn-generator, bpmn-to-drawio, help
```

#### 5.2 Detect Collisions

Compare names across plugins:

```text
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
```text
[PASS] No namespace collisions detected
```

#### 5.3 Single Plugin Mode

When validating a single plugin (not `--all`), skip collision detection and display:
```text
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
```text
Dependency Validation
---------------------
[PASS] personal-plugin: >=2.0.0 (installed: 2.0.0)
[FAIL] missing-plugin: ^1.0.0 (not found)
[FAIL] outdated-plugin: >=3.0.0 (installed: 2.5.0)
```

Or if no dependencies declared:
```text
[PASS] No dependencies declared
```

#### 6.3 Semver Validation

Check that version strings follow semver patterns:
- `>=X.Y.Z`, `<=X.Y.Z`, `>X.Y.Z`, `<X.Y.Z`
- `^X.Y.Z` (caret range - compatible with)
- `~X.Y.Z` (tilde range - approximately)
- `X.Y.Z` (exact version)

**Report invalid version syntax:**
```text
[FAIL] Invalid version syntax in dependencies
       bpmn-plugin: "latest" (not valid semver)

       Valid formats: >=1.0.0, ^1.0.0, ~1.0.0, 1.0.0
```

### Phase 7: Hook Windows Compatibility

Check if the plugin has hooks that may not work on Windows due to bash script dependencies.

#### 7.1 Detect Hooks Configuration

**Check for hooks in these locations:**
- `plugins/[plugin-name]/hooks/hooks.json` (in marketplace)
- `%USERPROFILE%\.claude\plugins\cache\*/[plugin-name]/*/hooks/hooks.json` (installed)

**Report:**
```text
Hook Detection
--------------
[PASS] No hooks.json found (plugin has no hooks)
```

Or if hooks exist:
```text
[INFO] hooks.json found at plugins/[plugin-name]/hooks/hooks.json
       Checking Windows compatibility...
```

#### 7.2 Analyze Hook Commands

Parse hooks.json and identify hook commands that reference bash scripts:

**Bash Script Indicators:**
- Command starts with `bash ` or `sh `
- Command contains `/bin/bash` or `/bin/sh`
- Command references `.sh` file extension
- Command uses `${CLAUDE_PLUGIN_ROOT}/hooks/*.sh`

**Report for each hook event:**
```text
Hook: Stop
  Command: bash "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh"
  [WARN] Uses bash script - may fail on Windows
```

#### 7.3 Check for PowerShell Equivalents

For each bash script found, check if a PowerShell equivalent exists:

**Check:**
- If `hooks/stop-hook.sh` exists, check for `hooks/stop-hook.ps1`
- Verify hooks.json has Windows-compatible alternative configured

**Report:**
```text
PowerShell Equivalents
----------------------
[PASS] stop-hook.sh has PowerShell equivalent: stop-hook.ps1
[FAIL] pre-tool-hook.sh missing PowerShell equivalent
```

#### 7.4 Windows Compatibility Summary

**If bash-only hooks detected:**
```text
Hook Windows Compatibility
--------------------------
[WARN] Plugin has hooks that may not work on Windows

       Bash Scripts Without PowerShell Equivalents:
         - hooks/stop-hook.sh
         - hooks/pre-tool-hook.sh

       To fix, run:
         /convert-hooks [plugin-name]

       This will:
         1. Convert bash scripts to PowerShell
         2. Update hooks.json to use PowerShell on Windows
```

**If all hooks are Windows-compatible:**
```text
[PASS] All hooks have Windows-compatible configurations
```

**If no hooks exist:**
```text
[PASS] Plugin has no hooks configured
```

#### 7.5 Hook Script Syntax Validation

For any bash scripts found, perform basic syntax validation:

**Check for common issues:**
- Shebang line present (`#!/bin/bash` or `#!/usr/bin/env bash`)
- No Windows-incompatible paths (hardcoded `/home/`, `/usr/`, etc.)
- No missing closing brackets/braces

**Report:**
```text
Hook Script Validation
----------------------
[PASS] stop-hook.sh - Valid bash syntax
[WARN] pre-tool-hook.sh - Missing shebang line
[WARN] post-tool-hook.sh - Contains hardcoded Unix path: /usr/local/bin
```

### Phase 8: Pattern Compliance Checks

Validate commands against the schema defined in `schemas/command.json` and pattern conventions.

#### 8.1 Command Frontmatter Schema Validation

For each command markdown file, validate frontmatter against `schemas/command.json`:

**Check:**
- `description` field present (required)
- `description` length between 10-200 characters
- No forbidden `name` field present
- `allowed-tools` format valid if present

**Report:**
```text
Command Schema Validation
-------------------------
[PASS] commands/assess-document.md - Schema valid
[PASS] commands/define-questions.md - Schema valid
[WARN] commands/my-command.md - description too short (8 chars, minimum 10)
```

#### 8.2 Required Sections Check

Verify each command contains required sections:

**Required Sections:**
1. `## Input Validation` - Must document arguments
2. `## Instructions` - Must have step-by-step guidance

**Report:**
```text
Required Sections Validation
----------------------------
[PASS] commands/assess-document.md - All required sections present
[FAIL] commands/my-command.md - Missing section: Input Validation
[WARN] commands/other.md - Missing section: Instructions
```

#### 8.3 Output Naming Convention Compliance

Check that commands generating output follow the naming pattern:
`[type]-[source]-[timestamp].[ext]`

**Check for patterns like:**
- Output file naming in documentation
- Examples showing correct naming

**Report:**
```text
Output Naming Compliance
------------------------
[PASS] commands/define-questions.md - Follows naming convention
[WARN] commands/my-command.md - Non-standard output naming: 'output.json'
       Expected: [type]-[source]-YYYYMMDD-HHMMSS.[ext]
```

#### 8.4 Error Message Format Adherence

Check that commands document error handling following the standard format:

**Standard Format:**
```text
Error: [Brief description]

Expected: [What was expected]
Received: [What was provided]

Suggestion: [How to fix]
```

**Report:**
```text
Error Format Compliance
-----------------------
[PASS] commands/define-questions.md - Error format compliant
[WARN] commands/my-command.md - Non-standard error format at line 45
```

#### 8.5 Flag Usage Consistency

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
```text
Flag Consistency Check
----------------------
[PASS] All flags follow standard conventions
```

Or:
```text
[WARN] commands/my-command.md - Non-standard flag '--skip-validation'
       Consider using '--force' for similar behavior
```

### Phase 9: Summary Report

Generate a final validation summary.

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Validation: [plugin-name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure Validation     [PASS]
Skill Structure          [PASS] (3 skills in correct format)
Marketplace Schema       [PASS]
Frontmatter Validation   [PASS] (15 files checked)
Version Synchronization  [PASS]
Content Validation       [WARN] (2 warnings)
Namespace Collisions     [WARN] (1 collision)  # Only with --all
Dependency Validation    [PASS]
Hook Windows Compat      [PASS]  # Or [WARN] if bash-only hooks found
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
```text
Validation complete. Exit code: 0 (success)
```

Or:
```text
Validation complete. Exit code: 1 (errors found)
```

## Auto-Fix Mode (--fix)

When `--fix` is specified, attempt to fix simple issues:

| Issue | Auto-Fix Action |
|-------|-----------------|
| Missing frontmatter | Add template frontmatter |
| Empty description | Prompt for description |
| Forbidden name field (commands) | Remove the field |
| Missing name field (skills) | Add `name: [directory-name]` |
| Name doesn't match directory (skills) | Update name to match directory |
| Code block without language | Add `text` as default |
| Invalid marketplace schema fields | Remove unrecognized fields (e.g., `last_updated`) |
| Flat skill file (`skills/name.md`) | Create directory, move to `skills/name/SKILL.md` |
| Wrong skill filename (`skill.md` lowercase) | Rename to `SKILL.md` |

**Report fixes:**
```text
Auto-Fix Applied:
  commands/my-command.md: Removed forbidden 'name' field
  commands/other.md: Added 'text' language to code block at line 23
  skills/my-skill/SKILL.md: Added required 'name: my-skill' field

3 issues fixed. Re-run validation to confirm.
```

## Strict Mode (--strict)

When `--strict` is specified, treat warnings as errors:

**Behavior:**
- All WARN results become FAIL results
- Exit code is 1 if ANY issues found (warnings OR errors)
- Recommended for CI/CD pipelines

**Report with --strict:**
```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Validation: personal-plugin (STRICT MODE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure Validation     [PASS]
Marketplace Schema       [PASS]
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
```text
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
- All command `.md` files have valid frontmatter
- All skills use correct directory structure (`skills/[name]/SKILL.md`)
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

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Maturity Scorecard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugin: personal-plugin
-----------------------
Level 1 (Basic)        [################] 100%
  [x] Valid plugin.json
  [x] Required fields present
  [x] Semver version format
  [x] Skill structure correct (skills/[name]/SKILL.md)
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
```text
Overall Score = (L1_score * 0.1) + (L2_score * 0.2) + (L3_score * 0.3) + (L4_score * 0.4)
```

**Current Level Assignment:**
- Level 1: All L1 criteria met
- Level 2: Level 1 + all L2 criteria met
- Level 3: Level 2 + all L3 criteria met
- Level 4: Level 3 + all L4 criteria met

### Example Usage with Scorecard

```yaml
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

```yaml
User: /validate-plugin personal-plugin

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validating Plugin: personal-plugin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Structure Validation
-----------------------------
[PASS] plugin.json exists
[PASS] commands/ directory (15 files)
[PASS] skills/ directory (3 skills)
[PASS] Skill structure valid (all use skills/[name]/SKILL.md format)
[PASS] references/ directory (1 file)
[PASS] Marketplace schema valid

Phase 2: Frontmatter Validation
-------------------------------
Checking 16 markdown files...
[PASS] All frontmatter valid
[PASS] All descriptions present
[PASS] Commands: No forbidden 'name' fields
[PASS] Skills: All have required 'name' field matching directory

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

```yaml
User: /validate-plugin --all

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validating All Plugins
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugin: personal-plugin
-----------------------
[PASS] Structure valid
[PASS] Marketplace schema valid
[PASS] Frontmatter valid (16 files)
[PASS] Versions synchronized
[WARN] 2 content warnings

Plugin: bpmn-plugin
-------------------
[PASS] Structure valid
[PASS] Marketplace schema valid
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
