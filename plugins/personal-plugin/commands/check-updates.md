---
description: Check for available plugin updates by comparing installed versions to marketplace
---

# Check Updates Command

Compare installed plugin versions against the marketplace registry and report any available updates. This is a read-only command that does not modify any files.

## Input Validation

**Required Arguments:**
None

**Optional Arguments:**
- `--verbose` - Show additional details including changelogs if available

**Validation:**
This command requires no arguments.
```
Usage: /check-updates [--verbose]
Example: /check-updates
Example: /check-updates --verbose
```

## Instructions

### 1. Locate Configuration Files

Find and read the following files:
- **Marketplace registry:** `.claude-plugin/marketplace.json` in the repository root
- **Plugin metadata:** `plugin.json` files in each plugin's `.claude-plugin/` directory

### 2. Extract Version Information

For each plugin listed in the marketplace:

**From marketplace.json:**
- Plugin name
- Latest version available
- Description
- Any changelog or release notes if present

**From plugin.json:**
- Installed version

### 3. Compare Versions

For each plugin, compare the installed version against the marketplace version:
- Parse versions as semantic versioning (MAJOR.MINOR.PATCH)
- Determine if an update is available (marketplace version > installed version)
- Categorize the update type:
  - **Major**: Breaking changes (X.0.0)
  - **Minor**: New features (0.X.0)
  - **Patch**: Bug fixes (0.0.X)

### 4. Generate Report

Display a formatted report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Update Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Updates Available: X

personal-plugin: 1.9.0 → 2.0.0 [MAJOR]
  - Added /new-command skill
  - Breaking: Changed output format for /assess-document

bpmn-plugin: 1.5.0 → 1.6.0 [MINOR]
  - Added Draw.io color mapping
  - Improved cross-lane edge handling

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Up to Date: Y

other-plugin: 1.2.0 (current)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5. Handle Edge Cases

**Plugin not in marketplace:**
```
Warning: installed-plugin is installed but not found in marketplace
```

**Marketplace plugin not installed:**
```
Available: marketplace-plugin v1.0.0 (not installed)
```

**Version parsing errors:**
```
Warning: Could not parse version for plugin-name (installed: "invalid", marketplace: "1.0.0")
```

**Missing files:**
```
Error: Could not read marketplace.json at .claude-plugin/marketplace.json
```

## Verbose Output

When `--verbose` is specified, include additional details:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Update Check (Verbose)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

personal-plugin
  Installed: 1.9.0
  Available: 2.0.0
  Update Type: MAJOR
  Location: ./plugins/personal-plugin

  Changelog:
  - Added /new-command skill for creating commands
  - Added /scaffold-plugin for new plugin creation
  - Breaking: /assess-document now outputs to reports/ directory
  - Fixed: Output location consistency across all commands

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Example Output

### All plugins up to date

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Update Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All plugins are up to date!

personal-plugin: 2.0.0 (current)
bpmn-plugin: 1.6.0 (current)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Updates available

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Update Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Updates Available: 1

personal-plugin: 2.0.0 → 2.1.0 [MINOR]
  - Added /check-updates command
  - Improved error messages

Up to Date: 1

bpmn-plugin: 1.6.0 (current)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To update plugins, pull the latest changes from the repository.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Safety Notes

- This command is **read-only** and does not modify any files
- No network requests are made; all version information comes from local files
- Plugin updates must be performed manually by pulling repository changes
- The command does not execute any installation or update operations
