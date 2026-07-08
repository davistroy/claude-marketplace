---
description: Validate plugin structure, frontmatter, and content for consistency and correctness
argument-hint: "<plugin-name> [--all] [--fix] [--verbose] [--strict]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Validate Plugin Command

Perform comprehensive validation of a plugin's structure, frontmatter, version synchronization, and content quality. Use this command before committing changes to catch common errors.

## Input Validation

**Required Arguments:**
- `<plugin-name>` - Name of the plugin to validate (must match a subdirectory in `plugins/` that contains `.claude-plugin/plugin.json`)

**Optional Arguments:**
- `--all` - Validate all plugins in the repository
- `--fix` - Attempt to auto-fix simple issues (formatting, missing fields)
- `--verbose` - Show detailed output for all checks (not just failures)
- `--strict` - Fail on any pattern violation (treats warnings as errors)
- `--report` - Generate detailed compliance report to `reports/validation-[timestamp].md`
- `--scorecard` - Generate maturity scorecard for plugins (see Maturity Scorecard section)
- `--check-updates` - Check for available plugin updates by comparing local vs remote marketplace versions

**Validation:**
If arguments are missing, display:
```text
Usage: /validate-plugin <plugin-name> [--all] [--fix] [--verbose] [--strict] [--report] [--scorecard] [--check-updates]

Examples:
  /validate-plugin personal-plugin          # Validate single plugin
  /validate-plugin --all                    # Validate all plugins
  /validate-plugin bpmn-plugin --verbose    # Detailed output
  /validate-plugin personal-plugin --fix    # Auto-fix simple issues
  /validate-plugin --all --strict           # Fail on any violation
  /validate-plugin --all --report           # Generate compliance report
  /validate-plugin --all --scorecard        # Generate maturity scorecard
  /validate-plugin --all --check-updates    # Include remote version check

Available plugins:
  [Scan the plugins/ directory for subdirectories containing .claude-plugin/plugin.json.
   List each discovered plugin name.]
```

If plugin-name is not found (and --all not specified), display:
```text
Error: Plugin '[name]' not found.

Available plugins:
  [Scan the plugins/ directory for subdirectories containing .claude-plugin/plugin.json.
   List each discovered plugin name.]

Use --all to validate all plugins.
```

**Plugin Discovery:** Use the Glob tool to scan `plugins/*/.claude-plugin/plugin.json`. Each match yields a valid plugin name from the directory path. If no plugins are found, report: "Error: No plugins found in the plugins/ directory."

**--all Flag Behavior:** When `--all` is specified, scan `plugins/` for all subdirectories containing `.claude-plugin/plugin.json` and validate each one. Do NOT rely on a hardcoded list of plugin names.

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

Output samples: see `references/validation-output-examples.md` §1.1

#### 1.2 Skill Directory Structure Validation

**CRITICAL:** Skills must use a nested directory structure with `SKILL.md` files (not flat `.md` files).

**Check for each item in skills/ directory:**
1. Item is a directory (not a file)
2. Directory contains `SKILL.md` (exact name, uppercase)

Output samples: see `references/validation-output-examples.md` §1.2

**Auto-fix with --fix:**
When `--fix` is specified, automatically restructure invalid skills:
Sample confirmation: see `references/validation-output-examples.md` §1.2

#### 1.3 plugin.json Validation

**Check:**
- File is valid JSON (parseable)
- Required fields present: `name`, `description`, `version`
- `version` follows semver format (X.Y.Z)

Output samples: see `references/validation-output-examples.md` §1.3

#### 1.4 Marketplace Schema Validation

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

Output samples: see `references/validation-output-examples.md` §1.4

**Auto-fix with --fix:**
When `--fix` is specified, automatically remove unrecognized fields:
Sample confirmation: see `references/validation-output-examples.md` §1.4

### Phase 2: Frontmatter Validation

Check all `.md` files in commands/ and skills/ directories.

#### 2.1 YAML Syntax

For each markdown file:
1. Check for frontmatter delimiters (`---` at start)
2. Parse YAML between delimiters
3. Report any syntax errors

Output samples: see `references/validation-output-examples.md` §2.1

#### 2.2 Required Fields

**Check:**
- `description` field present and non-empty

Output samples: see `references/validation-output-examples.md` §2.2

#### 2.3 Name Field Validation (Commands vs Skills)

**CRITICAL:** Commands and skills have OPPOSITE requirements for the `name` field:

| Component | `name` Field | Reason |
|-----------|--------------|--------|
| Commands | **FORBIDDEN** | Filename determines command name |
| Skills | **REQUIRED** | Needed for skill registration and discovery |

**For Commands (files in `commands/`):**

Check that no `name` field is present.

Output samples: see `references/validation-output-examples.md` §2.3

**For Skills (files in `skills/*/SKILL.md`):**

Check that `name` field IS present and matches the directory name.

Output samples: see `references/validation-output-examples.md` §2.3

#### 2.4 Optional Field Validation

If `allowed-tools` is present:
- Check it's a valid string format
- Warn if format appears incorrect (e.g., missing parentheses)

Output samples: see `references/validation-output-examples.md` §2.4

### Phase 3: Version Synchronization

Verify versions match across all configuration files.

#### 3.1 Version Locations

**Check these files:**
- `plugins/[plugin-name]/.claude-plugin/plugin.json` -> `version` field
- `.claude-plugin/marketplace.json` -> plugin entry's `version` field

Output samples: see `references/validation-output-examples.md` §3.1

### Phase 4: Content Validation

Check markdown content quality.

#### 4.1 Markdown Parsing

Verify markdown parses without errors:
- Check for unclosed code blocks
- Check for malformed links
- Check for unbalanced formatting

Output samples: see `references/validation-output-examples.md` §4.1

#### 4.2 Code Block Language Specifiers

Check that fenced code blocks have language specifiers:

Good/bad code-fence examples and Report/warning samples: see `references/validation-output-examples.md` §4.2

#### 4.3 Internal Link Validation

Check that internal file references exist:

**Check for patterns like:**
- `See common-patterns.md`
- `[link](../references/file.md)`
- References to other commands

Output samples: see `references/validation-output-examples.md` §4.3

### Phase 5: Namespace Collision Detection

When running with `--all`, check for command/skill naming collisions across plugins.

#### 5.1 Collect All Command Names

For each plugin, build a registry of command and skill names:

```text
Plugin: personal-plugin
  Commands: [dynamically discovered from commands/*.md]
  Skills: [dynamically discovered from skills/*/SKILL.md]

Plugin: bpmn-plugin
  Commands: (none)
  Skills: bpmn-generator, bpmn-to-drawio, help
```

#### 5.2 Detect Collisions

Compare names across plugins:

Output samples: see `references/validation-output-examples.md` §5.2

#### 5.3 Single Plugin Mode

When validating a single plugin (not `--all`), skip collision detection and display:
Output samples: see `references/validation-output-examples.md` §5.3

### Phase 6: Dependency Validation

Check if plugin.json declares dependencies and validate them.

#### 6.1 Parse Dependencies

If `dependencies` field exists in plugin.json:
Example `dependencies` block and validation samples: see `references/validation-output-examples.md` §6.1

#### 6.2 Validate Dependencies

For each declared dependency:
1. Check if the plugin exists in the marketplace
2. Parse the version requirement (semver syntax)
3. Compare against the installed plugin version

Output samples: see `references/validation-output-examples.md` §6.2

#### 6.3 Semver Validation

Check that version strings follow semver patterns:
- `>=X.Y.Z`, `<=X.Y.Z`, `>X.Y.Z`, `<X.Y.Z`
- `^X.Y.Z` (caret range - compatible with)
- `~X.Y.Z` (tilde range - approximately)
- `X.Y.Z` (exact version)

Output samples: see `references/validation-output-examples.md` §6.3

### Phase 7: Hook Windows Compatibility

Check if the plugin has hooks that may not work on Windows due to bash script dependencies.

#### 7.1 Detect Hooks Configuration

**Check for hooks in these locations:**
- `plugins/[plugin-name]/hooks/hooks.json` (in marketplace)
- `%USERPROFILE%\.claude\plugins\cache\*/[plugin-name]/*/hooks/hooks.json` (installed)

Output samples: see `references/validation-output-examples.md` §7.1

#### 7.2 Analyze Hook Commands

Parse hooks.json and identify hook commands that reference bash scripts:

**Bash Script Indicators:**
- Command starts with `bash ` or `sh `
- Command contains `/bin/bash` or `/bin/sh`
- Command references `.sh` file extension
- Command uses `${CLAUDE_PLUGIN_ROOT}/hooks/*.sh`

Output samples: see `references/validation-output-examples.md` §7.2

#### 7.3 Check for PowerShell Equivalents

For each bash script found, check if a PowerShell equivalent exists:

**Check:**
- If `hooks/stop-hook.sh` exists, check for `hooks/stop-hook.ps1`
- Verify hooks.json has Windows-compatible alternative configured

Output samples: see `references/validation-output-examples.md` §7.3

#### 7.4 Windows Compatibility Summary

Emit one of three summaries depending on detection:
- **If bash-only hooks detected:** warn, listing the bash scripts without PowerShell equivalents and how to fix them.
- **If all hooks are Windows-compatible:** report PASS.
- **If no hooks exist:** report PASS (no hooks configured).

Output samples: see `references/validation-output-examples.md` §7.4

#### 7.5 Hook Script Syntax Validation

For any bash scripts found, perform basic syntax validation:

**Check for common issues:**
- Shebang line present (`#!/bin/bash` or `#!/usr/bin/env bash`)
- No Windows-incompatible paths (hardcoded `/home/`, `/usr/`, etc.)
- No missing closing brackets/braces

Output samples: see `references/validation-output-examples.md` §7.5

### Phase 8: Pattern Compliance Checks

Validate commands against the command frontmatter rules and pattern conventions.

#### 8.1 Command Frontmatter Schema Validation

For each command markdown file, validate frontmatter against these rules:

**Check:**
- `description` field present (required)
- `description` length between 10-200 characters
- No forbidden `name` field present
- `allowed-tools` format valid if present

Output samples: see `references/validation-output-examples.md` §8.1

#### 8.2 Required Sections Check

Verify each command contains required sections:

**Required Sections:**
1. `## Input Validation` - Must document arguments
2. `## Instructions` - Must have step-by-step guidance

Output samples: see `references/validation-output-examples.md` §8.2

#### 8.3 Output Naming Convention Compliance

Check that commands generating output follow the naming pattern:
`[type]-[source]-[timestamp].[ext]`

**Check for patterns like:**
- Output file naming in documentation
- Examples showing correct naming

Output samples: see `references/validation-output-examples.md` §8.3

#### 8.4 Error Message Format Adherence

Check that commands document error handling following the standard format:

**Standard Format:**
```text
Error: [Brief description]

Expected: [What was expected]
Received: [What was provided]

Suggestion: [How to fix]
```

Output samples: see `references/validation-output-examples.md` §8.4

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

Output samples: see `references/validation-output-examples.md` §8.5

### Phase 8.5: Plan Template Validation

Validate the plan template structural rules if `references/plan-template.md` exists. This phase ensures the template stays self-consistent and includes all expected structural rules.

#### 8.5.1 Template File Presence

**Check:**
- `plugins/[plugin-name]/references/plan-template.md` exists

Output samples: see `references/validation-output-examples.md` §8.5.1

If the file is missing, skip the rest of Phase 8.5.

#### 8.5.2 Structural Rules Enumeration

Read the `## Structural Rules` section from `plan-template.md`. Parse the numbered rules list.

**Check:**
- At least 17 structural rules are defined (numbered 1-17)
- No gaps in numbering (1, 2, ... N with no missing numbers)

Output samples: see `references/validation-output-examples.md` §8.5.2

#### 8.5.3 Key Rule Content Validation

Verify that the following high-value structural rules are present and contain their required keywords. These rules were added in v9.0.0 and are load-bearing for plan generation and execution.

| Rule | Required Keywords | Purpose |
|------|-------------------|---------|
| 13 | `EARS`, `WHEN`, `SHALL` | Behavioral acceptance criteria format |
| 14 | `Definition of Done`, `BEGIN DOD`, `END DOD` | Runnable verification section |
| 15 | `Execution Hints`, `Model Tier`, `sonnet` or `opus` or `haiku` | Sub-agent model routing |
| 16 | `Unknowns Register`, `Severity`, `Open` or `Resolved` or `Accepted` | Epistemic uncertainty tracking |
| 17 | `Model Tier`, `haiku` or `sonnet` or `opus` | Per-task model tier assignment |

**Check for each rule:**
1. The numbered rule exists in the structural rules list
2. The rule text contains all required keywords (case-insensitive)

Output samples: see `references/validation-output-examples.md` §8.5.3

#### 8.5.4 Sizing Constraints Check

Verify that the `## Sizing Constraints` section exists and contains the expected limits.

**Check:**
- Section `## Sizing Constraints` exists
- Contains "Maximum phases per plan" with a numeric limit
- Contains "Maximum work items per phase" with a numeric limit

Output samples: see `references/validation-output-examples.md` §8.5.4

### Phase 8.6: Reference File Inventory

Validate that expected reference files are present. The planning pipeline depends on specific reference files; missing files cause silent degradation rather than hard errors. This check is dynamic: it lists the actual contents of `references/` and diffs them against a required set, so adding, renaming, or removing a reference file is reported here without editing this command.

#### 8.6.1 Required Reference Set

The required set, relative to the plugin root (`plugins/[plugin-name]/`), is data — maintain this list here, not a per-file prose table:

**Top-level files (`references/`):**
- `plan-template.md`
- `common-patterns.md`
- `anti-patterns.md`
- `adr-template.md`
- `agents-md-template.md`
- `flag-consistency.md`
- `validation-maturity-scorecard.md`
- `plan-append-guide.md`
- `recommendations-template.md`
- `create-plan-examples.md`
- `implement-plan-state-schema.md`
- `validation-output-examples.md`

**Hook reference files (`references/hooks/`):**
- `planning-stop-hook.md`
- `verification-post-edit-hook.md`
- `session-start-hook.md`

**Required non-empty subdirectories:**
- `references/patterns/` (at least one file)
- `references/templates/` (at least one file)

#### 8.6.2 Dynamic Inventory Check

1. Use Glob to list `references/**` recursively (files and directories).
2. Diff the discovered set against the required set above and classify each entry:
   - **Present** — a required file or directory that exists: PASS.
   - **Missing** — a required entry that is absent: FAIL for top-level files and for the `patterns/`/`templates/` directories; WARN for individual `hooks/` files (they are documentation references and their absence does not affect plugin functionality).
   - **Extra** — a file present under `references/` but not in the required set: reported for awareness (INFO), never an error.
3. For `references/patterns/` and `references/templates/`, confirm each contains at least one file.

Only top-level required files and the two required subdirectories are treated as errors when missing; hook reference files are warnings.

Output samples (present/missing/extra): see `references/validation-output-examples.md` → Phase 8.6

### Phase 9: Summary Report

Generate a final validation summary.

Output samples: see `references/validation-output-examples.md` §Phase 9

### Phase 9.5: Version Update Check (--check-updates only)

This phase only executes when `--check-updates` is passed. It does NOT run during normal validation (no new network calls without the flag).

#### 9.5.1 Discover Local Plugin Versions

Use the Glob tool to scan `plugins/*/.claude-plugin/plugin.json` to discover all installed plugins dynamically. Do NOT rely on a hardcoded list of plugin names.

Read each discovered `plugin.json` to extract the `version` field.

Also read the local marketplace registry: `.claude-plugin/marketplace.json` in the repository root.

If no plugins are found in the `plugins/` directory, report:
```text
Error: No plugins found in the plugins/ directory.
```

#### 9.5.2 Fetch Remote Version Data

Fetch the latest marketplace.json from GitHub:

```bash
# Derive owner/repo from the origin remote (supports https and ssh URLs)
REPO=$(git remote get-url origin | sed -E 's#(^git@[^:]+:|^https?://[^/]+/)##; s#\.git$##')
gh api "repos/$REPO/contents/.claude-plugin/marketplace.json" \
  --jq '.content' | base64 -d
```

**If the `gh` command fails** (not installed, not authenticated, no network):
```text
Note: Could not fetch remote versions (gh CLI unavailable or network error).
Falling back to local version consistency report.

To enable remote checks:
  1. Install gh CLI: https://cli.github.com
  2. Authenticate: gh auth login
```

Then proceed with local-only comparison (Step 9.5.3 only compares local files against each other).

#### 9.5.3 Compare Versions

For each locally discovered plugin:

**From remote marketplace.json (if available):**
- Latest version available on the remote repository

**From local plugin.json:**
- Currently installed version

**From local marketplace.json:**
- Locally registered version

Compare using semantic versioning (MAJOR.MINOR.PATCH):
- Determine if a remote update is available (remote version > local version)
- Determine if local versions are consistent (plugin.json matches local marketplace.json)
- Categorize update type:
  - **MAJOR**: Breaking changes (X.0.0)
  - **MINOR**: New features (0.X.0)
  - **PATCH**: Bug fixes (0.0.X)

#### 9.5.4 Generate Version Report

**With remote data available:** print a per-plugin table (Plugin / Local / Remote / Status), the count of available updates, and the `git pull origin main` instruction.

**Without remote data (local-only fallback):** print a per-plugin table (Plugin / plugin.json / marketplace.json / Consistent), the count of inconsistencies, and the `/bump-version` instruction.

Output samples: see `references/validation-output-examples.md` §9.5.4

#### 9.5.5 Verbose Output (--verbose)

When `--verbose` is also specified alongside `--check-updates`, include per-plugin file path detail:

Output samples: see `references/validation-output-examples.md` §9.5.5

#### 9.5.6 Edge Cases

Handle these edge cases, each with a user-facing message:
- **Plugin not in local marketplace.json** — warn that it exists under `plugins/` but is unregistered, and suggest running structure validation.
- **Remote plugin not installed locally** — note that it is available remotely but not installed.
- **Version parsing errors** — warn, echoing the unparseable local/remote values.

Output samples: see `references/validation-output-examples.md` §9.5.6

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

Report-fixes sample: see `references/validation-output-examples.md` → Auto-Fix Mode (--fix)

## Strict Mode (--strict)

When `--strict` is specified, treat warnings as errors:

**Behavior:**
- All WARN results become FAIL results
- Exit code is 1 if ANY issues found (warnings OR errors)
- Recommended for CI/CD pipelines

Strict-mode report sample: see `references/validation-output-examples.md` → Strict Mode (--strict)

## Report Mode (--report)

When `--report` is specified, generate a detailed compliance report file:

**Output:** `reports/validation-[timestamp].md`

**Report Contents:**
- Full validation results for all phases
- Per-command compliance breakdown
- Pattern adherence statistics
- Recommendations for improvement

Example report structure and console output: see `references/validation-output-examples.md` → Report Mode (--report)

## Maturity Scorecard Mode (--scorecard)

When `--scorecard` is requested, read `references/validation-maturity-scorecard.md` (relative to this plugin's directory) for the complete scoring framework, including:
- 4-level maturity model (Basic, Standard, Complete, Exemplary) with criteria for each level
- Scorecard output format with per-level progress bars and criteria checklists
- Scorecard calculation logic (weighted scoring formula, level assignment rules)
- Example usage and aggregate scorecard format

Evaluate each plugin against the criteria defined in the reference file and generate the scorecard output.

## Error Handling

- **File read failure:** Report file path and skip to next
- **JSON parse error:** Report detailed error with line number
- **YAML parse error:** Report error with line number and context
- **Permission denied:** Report and suggest checking file permissions

## Example Usage

Full end-to-end transcripts — a single-plugin run and an `--all` run: see `references/validation-output-examples.md` → Example Usage.

## Related Commands

- `/bump-version` — Update version numbers (run validation after bumping)
- `/scaffold-plugin` — Create a new plugin with proper structure
- `/new-command` — Add a new command (run validation after adding)
- `/new-skill` — Add a new skill (run validation after adding)
- `/clean-repo` — Full repository cleanup and documentation sync
