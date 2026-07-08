# Validation Output Examples

Reference for `/validate-plugin`. Loaded on demand. This file holds only the sample output an operator would see — PASS/FAIL/WARN/INFO report blocks, mode reports, and end-to-end transcripts — one section per validation phase and per output mode.

The command file (`commands/validate-plugin.md`) holds the authoritative check logic: the numbered checks, pass/fail criteria, error-detection rules, and mode semantics live there and are the source of truth. Nothing here changes behavior; every block below is an illustration of what a check prints. Placeholders follow the command file's convention: `[N]` for counts, `[X.Y.Z]` for versions, `[YYYY-MM-DD]` for dates, and `<owner>/<repo>` for the derived origin repository.

## Table of Contents

- [Phase 1: Structure Validation](#phase-1-structure-validation)
- [Phase 2: Frontmatter Validation](#phase-2-frontmatter-validation)
- [Phase 3: Version Synchronization](#phase-3-version-synchronization)
- [Phase 4: Content Validation](#phase-4-content-validation)
- [Phase 5: Namespace Collision Detection](#phase-5-namespace-collision-detection)
- [Phase 6: Dependency Validation](#phase-6-dependency-validation)
- [Phase 7: Hook Windows Compatibility](#phase-7-hook-windows-compatibility)
- [Phase 8: Pattern Compliance Checks](#phase-8-pattern-compliance-checks)
- [Phase 8.5: Plan Template Validation](#phase-85-plan-template-validation)
- [Phase 8.6: Reference File Inventory](#phase-86-reference-file-inventory)
- [Phase 9: Summary Report](#phase-9-summary-report)
- [Phase 9.5: Version Update Check](#phase-95-version-update-check)
- [Auto-Fix Mode (--fix)](#auto-fix-mode---fix)
- [Strict Mode (--strict)](#strict-mode---strict)
- [Report Mode (--report)](#report-mode---report)
- [Example Usage (end-to-end transcripts)](#example-usage-end-to-end-transcripts)

---

## Phase 1: Structure Validation

### 1.1 Required Files Check

Report:

```text
Structure Validation
--------------------
[PASS] plugin.json exists
[PASS] commands/ directory exists ([N] files)
[PASS] skills/ directory exists ([N] skills)
```

Or on failure:

```text
[FAIL] plugin.json missing at plugins/[name]/.claude-plugin/plugin.json
```

### 1.2 Skill Directory Structure Validation

Valid structure:

```text
skills/
  ship/
    SKILL.md              # ✓ Correct
  help/
    SKILL.md              # ✓ Correct
```

Invalid structures:

```text
skills/
  ship.md                 # ✗ Flat file - NOT discovered by Claude Code
  help.md                 # ✗ Flat file - NOT discovered by Claude Code
  broken-skill/
    skill.md              # ✗ Wrong filename - must be SKILL.md (uppercase)
```

Report:

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

Auto-fix output (`--fix`):

```text
Auto-Fix Applied:
  skills/ship.md -> skills/ship/SKILL.md (created directory, moved file)
  skills/help.md -> skills/help/SKILL.md (created directory, moved file)

2 skills restructured. Skills should now be discoverable.
```

### 1.3 plugin.json Validation

Report:

```text
plugin.json Validation
----------------------
[PASS] Valid JSON syntax
[PASS] Required field 'name' present
[PASS] Required field 'description' present
[PASS] Required field 'version' present ([X.Y.Z])
[PASS] Version follows semver format
```

### 1.4 Marketplace Schema Validation

Report:

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

Auto-fix output (`--fix`):

```text
Auto-Fix Applied:
  marketplace.json: Removed 'last_updated' from plugin 'personal-plugin'
  marketplace.json: Removed 'last_updated' from plugin 'bpmn-plugin'

2 invalid fields removed. Marketplace schema now valid.
```

---

## Phase 2: Frontmatter Validation

### 2.1 YAML Syntax

Report:

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

### 2.2 Required Fields

Report:

```text
[PASS] Required field 'description' present
```

Or:

```text
[FAIL] commands/my-command.md
      Missing required field: description
```

### 2.3 Name Field Validation (Commands vs Skills)

For Commands (files in `commands/`) — Report:

```text
[PASS] commands/my-command.md - No forbidden 'name' field
```

Or:

```text
[FAIL] commands/my-command.md
      Forbidden field 'name' found - filename determines command name
      Remove: name: my-command
```

For Skills (files in `skills/*/SKILL.md`) — Report:

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

### 2.4 Optional Field Validation

Report:

```text
[PASS] allowed-tools format valid: Bash(git:*)
```

Or:

```text
[WARN] commands/my-command.md
      allowed-tools format may be invalid: 'git:*'
      Expected format: ToolName(pattern) or ToolName
```

---

## Phase 3: Version Synchronization

### 3.1 Version Locations

Report:

```text
Version Synchronization
-----------------------
plugin.json version:      [X.Y.Z]
marketplace.json version: [X.Y.Z]
[PASS] Versions are synchronized
```

Or:

```text
[FAIL] Version mismatch
      plugin.json:      [X.Y.Z]
      marketplace.json: [X.Y.Z-1]

      Run '/bump-version [plugin] patch' to synchronize.
```

---

## Phase 4: Content Validation

### 4.1 Markdown Parsing

Report:

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

### 4.2 Code Block Language Specifiers

Good vs. bad code fences:

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

Report:

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

### 4.3 Internal Link Validation

Report:

```text
[PASS] All internal references valid
```

Or:

```text
[WARN] commands/my-command.md
      Line 15: Reference 'common-patterns.md' not found
      Expected at: plugins/personal-plugin/references/common-patterns.md
```

---

## Phase 5: Namespace Collision Detection

### 5.2 Detect Collisions

Collision detected:

```text
Namespace Collision Detection
-----------------------------
[WARN] Collision detected: /help
       - personal-plugin/skills/help/SKILL.md
       - bpmn-plugin/skills/help/SKILL.md

       Users must use explicit namespace:
         /personal-plugin:help
         /bpmn-plugin:help
```

If no collisions:

```text
[PASS] No namespace collisions detected
```

### 5.3 Single Plugin Mode

```text
Note: Run with --all to check for naming collisions across plugins.
```

---

## Phase 6: Dependency Validation

### 6.1 Parse Dependencies

Example `dependencies` block being parsed from plugin.json:

```json
{
  "dependencies": {
    "personal-plugin": ">=2.0.0"
  }
}
```

### 6.2 Validate Dependencies

Report:

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

### 6.3 Semver Validation

Report invalid version syntax:

```text
[FAIL] Invalid version syntax in dependencies
       bpmn-plugin: "latest" (not valid semver)

       Valid formats: >=1.0.0, ^1.0.0, ~1.0.0, 1.0.0
```

---

## Phase 7: Hook Windows Compatibility

### 7.1 Detect Hooks Configuration

Report:

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

### 7.2 Analyze Hook Commands

Report for each hook event:

```text
Hook: Stop
  Command: bash "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh"
  [WARN] Uses bash script - may fail on Windows
```

### 7.3 Check for PowerShell Equivalents

Report:

```text
PowerShell Equivalents
----------------------
[PASS] stop-hook.sh has PowerShell equivalent: stop-hook.ps1
[FAIL] pre-tool-hook.sh missing PowerShell equivalent
```

### 7.4 Windows Compatibility Summary

If bash-only hooks detected:

```text
Hook Windows Compatibility
--------------------------
[WARN] Plugin has hooks that may not work on Windows

       Bash Scripts Without PowerShell Equivalents:
         - hooks/stop-hook.sh
         - hooks/pre-tool-hook.sh

       To fix, manually convert bash scripts to PowerShell equivalents
       and update hooks.json to use PowerShell on Windows.
```

If all hooks are Windows-compatible:

```text
[PASS] All hooks have Windows-compatible configurations
```

If no hooks exist:

```text
[PASS] Plugin has no hooks configured
```

### 7.5 Hook Script Syntax Validation

Report:

```text
Hook Script Validation
----------------------
[PASS] stop-hook.sh - Valid bash syntax
[WARN] pre-tool-hook.sh - Missing shebang line
[WARN] post-tool-hook.sh - Contains hardcoded Unix path: /usr/local/bin
```

---

## Phase 8: Pattern Compliance Checks

### 8.1 Command Frontmatter Schema Validation

Report:

```text
Command Schema Validation
-------------------------
[PASS] commands/assess-document.md - Schema valid
[PASS] commands/define-questions.md - Schema valid
[WARN] commands/my-command.md - description too short (8 chars, minimum 10)
```

### 8.2 Required Sections Check

Report:

```text
Required Sections Validation
----------------------------
[PASS] commands/assess-document.md - All required sections present
[FAIL] commands/my-command.md - Missing section: Input Validation
[WARN] commands/other.md - Missing section: Instructions
```

### 8.3 Output Naming Convention Compliance

Report:

```text
Output Naming Compliance
------------------------
[PASS] commands/define-questions.md - Follows naming convention
[WARN] commands/my-command.md - Non-standard output naming: 'output.json'
       Expected: [type]-[source]-YYYYMMDD-HHMMSS.[ext]
```

### 8.4 Error Message Format Adherence

Report:

```text
Error Format Compliance
-----------------------
[PASS] commands/define-questions.md - Error format compliant
[WARN] commands/my-command.md - Non-standard error format at line 45
```

### 8.5 Flag Usage Consistency

Report:

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

---

## Phase 8.5: Plan Template Validation

### 8.5.1 Template File Presence

Report:

```text
Plan Template Validation
------------------------
[PASS] references/plan-template.md exists
```

Or:

```text
[SKIP] references/plan-template.md not found — skipping plan template validation
```

### 8.5.2 Structural Rules Enumeration

Report:

```text
[PASS] [N] structural rules defined (expected ≥17, no numbering gaps)
```

Or:

```text
[FAIL] Only [N] structural rules found (expected ≥17)
       Missing rule numbers: [list]
```

### 8.5.3 Key Rule Content Validation

Report:

```text
Structural Rule Content Validation
-----------------------------------
[PASS] Rule 13 — EARS notation guidance present
[PASS] Rule 14 — Definition of Done markers present
[PASS] Rule 15 — Execution Hints with model tiers present
[PASS] Rule 16 — Unknowns Register with status values present
[PASS] Rule 17 — Model Tier assignment present
```

Or on failure:

```text
[FAIL] Rule 14 — Missing required keywords: BEGIN DOD, END DOD
       Rule 14 text: "[actual rule text]"
       Expected keywords: Definition of Done, BEGIN DOD, END DOD
```

### 8.5.4 Sizing Constraints Check

Report:

```text
[PASS] Sizing constraints defined (max [N] phases, max [N] items/phase)
```

Or:

```text
[WARN] Sizing constraints section missing or incomplete
```

---

## Phase 8.6: Reference File Inventory

Present/missing/extra sample against the required set (see the command file's Phase 8.6 for the authoritative required set and diff logic):

```text
Reference File Inventory
------------------------
[PASS] [N]/[N] required top-level files present
[PASS] references/hooks/ ([N] files) — all required hook references present
[PASS] references/patterns/ ([N] files)
[PASS] references/templates/ ([N] files)
[INFO] Extra (present, not in required set): api-key-setup.md, research-models.md
```

Or on failure:

```text
[FAIL] Missing required reference file: references/anti-patterns.md
       Used by /ultra-plan and /create-plan for anti-pattern detection.
       Create it manually or regenerate via the planning pipeline.
[WARN] references/hooks/session-start-hook.md — MISSING (documentation reference)
[WARN] references/patterns/ — directory missing or empty
```

---

## Phase 9: Summary Report

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Validation: [plugin-name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure Validation     [PASS]
Skill Structure          [PASS] ([N] skills in correct format)
Marketplace Schema       [PASS]
Frontmatter Validation   [PASS] ([N] files checked)
Version Synchronization  [PASS]
Content Validation       [WARN] (2 warnings)
Namespace Collisions     [WARN] (1 collision)  # Only with --all
Dependency Validation    [PASS]
Hook Windows Compat      [PASS]  # Or [WARN] if bash-only hooks found
Pattern Compliance       [PASS] (all commands checked)
Plan Template            [PASS] ([N] rules validated)
Reference Inventory      [PASS] ([N] expected files present)

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

---

## Phase 9.5: Version Update Check

### 9.5.4 Generate Version Report

With remote data available:

```text
Version Update Check
--------------------

| Plugin           | Local   | Remote  | Status           |
|------------------|---------|---------|------------------|
| personal-plugin  | 2.0.0   | 2.1.0   | Update available [MINOR] |
| bpmn-plugin      | 1.6.0   | 1.6.0   | Up to date       |

Updates available: 1

To update, pull the latest changes from the repository:
  git pull origin main
```

Without remote data (local-only fallback):

```text
Version Update Check (Local Only)
----------------------------------

Note: Remote check unavailable. Showing local version consistency only.

| Plugin           | plugin.json | marketplace.json | Consistent |
|------------------|-------------|------------------|------------|
| personal-plugin  | 2.0.0       | 2.0.0            | Yes        |
| bpmn-plugin      | 1.6.0       | 1.5.0            | No         |

Inconsistencies: 1

To sync versions, run: /bump-version [plugin-name] [major|minor|patch]
```

### 9.5.5 Verbose Output (--verbose)

```text
Version Update Check (Verbose)
-------------------------------

personal-plugin
  Local version:  2.0.0  (plugins/personal-plugin/.claude-plugin/plugin.json)
  Remote version: 2.1.0  (<owner>/<repo>@main)
  Update type:    MINOR
  Status:         Update available

bpmn-plugin
  Local version:  1.6.0  (plugins/bpmn-plugin/.claude-plugin/plugin.json)
  Remote version: 1.6.0  (<owner>/<repo>@main)
  Status:         Up to date
```

### 9.5.6 Edge Cases

Plugin not in local marketplace.json:

```text
Warning: [plugin-name] exists in plugins/ but is not registered in marketplace.json.
  Run /validate-plugin [plugin-name] to check plugin structure.
```

Remote plugin not installed locally:

```text
Available remotely: [plugin-name] v1.0.0 (not installed locally)
```

Version parsing errors:

```text
Warning: Could not parse version for [plugin-name] (local: "[value]", remote: "[value]")
```

---

## Auto-Fix Mode (--fix)

Report fixes:

```text
Auto-Fix Applied:
  commands/my-command.md: Removed forbidden 'name' field
  commands/other.md: Added 'text' language to code block at line 23
  skills/my-skill/SKILL.md: Added required 'name: my-skill' field

3 issues fixed. Re-run validation to confirm.
```

---

## Strict Mode (--strict)

Report with --strict:

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
Plan Template            [PASS]
Reference Inventory      [PASS]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Result: FAIL (strict mode treats warnings as errors)
Exit code: 1

Fix all issues or run without --strict to allow warnings.
```

---

## Report Mode (--report)

Example Report Structure:

```markdown
# Plugin Validation Report

**Generated:** [YYYY-MM-DD]T[HH:MM:SS]Z
**Plugin:** personal-plugin
**Version:** [X.Y.Z]

## Executive Summary

| Phase | Status | Issues |
|-------|--------|--------|
| Structure | PASS | 0 |
| Frontmatter | PASS | 0 |
| Version Sync | PASS | 0 |
| Content | WARN | 2 |
| Pattern Compliance | PASS | 0 |
| Plan Template | PASS | 0 |
| Reference Inventory | PASS | 0 |

**Overall:** PASS (with 2 warnings)

## Detailed Findings

### Content Validation

#### Warnings
1. **commands/clean-repo.md:45** - Code block missing language specifier
2. **commands/clean-repo.md:89** - Code block missing language specifier

### Pattern Compliance

All [N] commands follow pattern conventions:
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

Console Output with --report:

```text
Validation complete. Exit code: 0

Report saved to: reports/validation-[YYYY-MM-DD]-[HHMMSS].md
```

---

## Example Usage (end-to-end transcripts)

Single-plugin run:

```yaml
User: /validate-plugin personal-plugin

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validating Plugin: personal-plugin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Structure Validation
-----------------------------
[PASS] plugin.json exists
[PASS] commands/ directory ([N] files)
[PASS] skills/ directory ([N] skills)
[PASS] Skill structure valid (all use skills/[name]/SKILL.md format)
[PASS] references/ directory ([N] files)
[PASS] Marketplace schema valid

Phase 2: Frontmatter Validation
-------------------------------
Checking [N] markdown files...
[PASS] All frontmatter valid
[PASS] All descriptions present
[PASS] Commands: No forbidden 'name' fields
[PASS] Skills: All have required 'name' field matching directory

Phase 3: Version Synchronization
--------------------------------
[PASS] plugin.json: [X.Y.Z]
[PASS] marketplace.json: [X.Y.Z]
[PASS] Versions synchronized

Phase 4: Content Validation
---------------------------
[PASS] All markdown parses correctly
[WARN] 2 code blocks missing language specifiers
[PASS] All internal references valid

Phase 8.5: Plan Template Validation
------------------------------------
[PASS] references/plan-template.md exists
[PASS] [N] structural rules defined (expected ≥17, no numbering gaps)
[PASS] Rule 13 — EARS notation guidance present
[PASS] Rule 14 — Definition of Done markers present
[PASS] Rule 15 — Execution Hints with model tiers present
[PASS] Rule 16 — Unknowns Register with status values present
[PASS] Rule 17 — Model Tier assignment present
[PASS] Sizing constraints defined

Phase 8.6: Reference File Inventory
-------------------------------------
[PASS] All [N] expected reference files present
[PASS] references/hooks/ ([N] files)
[PASS] references/patterns/ ([N] files)
[PASS] references/templates/ ([N] files)

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

All-plugins run:

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
[PASS] Frontmatter valid ([N] files)
[PASS] Versions synchronized
[WARN] 2 content warnings
[PASS] Plan template valid ([N] rules)
[PASS] Reference inventory complete

Plugin: bpmn-plugin
-------------------
[PASS] Structure valid
[PASS] Marketplace schema valid
[PASS] Frontmatter valid ([N] files)
[PASS] Versions synchronized
[PASS] Content valid
[SKIP] No plan template (skipped)
[SKIP] No references/ directory (skipped)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugins validated: 2
Total errors:      0
Total warnings:    2

Result: PASS (with warnings)
Exit code: 0
```
