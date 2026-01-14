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

**Validation:**
If arguments are missing, display:
```
Usage: /validate-plugin <plugin-name> [--all] [--fix] [--verbose]

Examples:
  /validate-plugin personal-plugin          # Validate single plugin
  /validate-plugin --all                    # Validate all plugins
  /validate-plugin bpmn-plugin --verbose    # Detailed output
  /validate-plugin personal-plugin --fix    # Auto-fix simple issues

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
Frontmatter Validation: commands/doc-assessment.md
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
Content Validation: commands/doc-assessment.md
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

### Phase 5: Summary Report

Generate a final validation summary.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Validation: [plugin-name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure Validation     [PASS]
Frontmatter Validation   [PASS] (15 files checked)
Version Synchronization  [PASS]
Content Validation       [WARN] (2 warnings)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues Found:
  Errors:   0
  Warnings: 2

Warnings:
  1. commands/my-command.md:23 - Code block missing language specifier
  2. commands/my-command.md:67 - Code block missing language specifier

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
  1. commands/cleanup.md:45 - Code block missing language specifier
  2. commands/cleanup.md:89 - Code block missing language specifier

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
