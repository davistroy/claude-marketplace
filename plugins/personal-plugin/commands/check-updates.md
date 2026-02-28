---
description: Check for available plugin updates by comparing local versions against remote marketplace
allowed-tools: Read, Glob, Grep, Bash(gh:*)
---

# Check Updates Command

Compare locally installed plugin versions against the remote marketplace registry on GitHub and report any available updates. This is a read-only command that does not modify any files.

## How It Works

This command performs a **remote version check** by fetching the latest `marketplace.json` from the `davistroy/claude-marketplace` GitHub repository using `gh api`. It compares the remote versions against locally installed plugin versions found in `plugins/*/.claude-plugin/plugin.json`.

**Requirements:**
- `gh` CLI must be installed and authenticated
- Network access to GitHub API
- If `gh` is unavailable or network is down, the command falls back to a local-only version consistency report

## Input Validation

**Required Arguments:**
None

**Optional Arguments:**
- `--verbose` - Show additional details including file locations and changelog if available
- `--local` - Skip remote check, only report local version consistency between plugin.json and marketplace.json

**Validation:**
This command requires no arguments.
```text
Usage: /check-updates [--verbose] [--local]
Example: /check-updates
Example: /check-updates --verbose
Example: /check-updates --local
```

## Instructions

### 1. Discover Local Plugins

**Plugin Discovery:** Use the Glob tool to scan `plugins/*/.claude-plugin/plugin.json` to discover all installed plugins dynamically. Do NOT rely on a hardcoded list of plugin names.

Read the local marketplace registry: `.claude-plugin/marketplace.json` in the repository root.

If no plugins are found in the `plugins/` directory, report:
```text
Error: No plugins found in the plugins/ directory.
```

### 2. Fetch Remote Version Data

Unless `--local` is specified, fetch the latest marketplace.json from GitHub:

```bash
gh api repos/davistroy/claude-marketplace/contents/.claude-plugin/marketplace.json \
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

Then proceed with local-only comparison (Step 3 only compares local files against each other).

### 3. Compare Versions

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

### 4. Generate Report

**With remote data available:**

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Version Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Plugin           | Local   | Remote  | Status           |
|------------------|---------|---------|------------------|
| personal-plugin  | 2.0.0   | 2.1.0   | Update available [MINOR] |
| bpmn-plugin      | 1.6.0   | 1.6.0   | Up to date       |

Updates available: 1

To update, pull the latest changes from the repository:
  git pull origin main

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Without remote data (local-only fallback):**

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Version Report (Local Only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Note: Remote check unavailable. Showing local version consistency only.

| Plugin           | plugin.json | marketplace.json | Consistent |
|------------------|-------------|------------------|------------|
| personal-plugin  | 2.0.0       | 2.0.0            | Yes        |
| bpmn-plugin      | 1.6.0       | 1.5.0            | No         |

Inconsistencies: 1

To sync versions, run: /bump-version [plugin-name] [major|minor|patch]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5. Handle Edge Cases

**Plugin not in local marketplace.json:**
```text
Warning: [plugin-name] exists in plugins/ but is not registered in marketplace.json.
  Run /validate-plugin [plugin-name] to check plugin structure.
```

**Remote plugin not installed locally:**
```text
Available remotely: [plugin-name] v1.0.0 (not installed locally)
```

**Version parsing errors:**
```text
Warning: Could not parse version for [plugin-name] (local: "[value]", remote: "[value]")
```

## Verbose Output

When `--verbose` is specified, include additional details:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plugin Version Check (Verbose)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

personal-plugin
  Local version:  2.0.0  (plugins/personal-plugin/.claude-plugin/plugin.json)
  Remote version: 2.1.0  (davistroy/claude-marketplace@main)
  Update type:    MINOR
  Status:         Update available

bpmn-plugin
  Local version:  1.6.0  (plugins/bpmn-plugin/.claude-plugin/plugin.json)
  Remote version: 1.6.0  (davistroy/claude-marketplace@main)
  Status:         Up to date

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

| Error Condition | Behavior |
|-----------------|----------|
| **`gh` CLI not installed** | Display installation link, fall back to local-only report |
| **`gh` not authenticated** | Display: `Run 'gh auth login' to authenticate.` Fall back to local-only report |
| **Network unavailable** | Display: `Network error. Falling back to local version report.` |
| **Remote marketplace.json not found** | Display: `Remote marketplace not found at davistroy/claude-marketplace.` Fall back to local-only |
| **Local marketplace.json missing** | Display: `Error: Could not read .claude-plugin/marketplace.json` |
| **Invalid version format** | Log warning for the specific plugin, continue processing others |
| **No plugins found** | Display: `Error: No plugins found in the plugins/ directory.` |

## Safety Notes

- This command is **read-only** and does not modify any files
- Remote data is fetched via `gh api` (GitHub's authenticated REST API)
- Plugin updates must be performed manually by pulling repository changes
- The command does not execute any installation or update operations
- The `--local` flag skips all network requests

## Related Commands

- `/bump-version` — Update plugin version numbers across all config files
- `/validate-plugin` — Verify plugin structure and version synchronization
- `/clean-repo` — Full repository cleanup including version consistency checks
