---
description: Custom status line setup (Windows/PowerShell)
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Custom Status Line Setup

Set up a custom status line for Claude Code on Windows using PowerShell. This command uses a phased approach with pre-flight checks, safe file operations, backups, and verification.

## Input Validation

**Optional Flags:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be changed without making any modifications |
| `--uninstall` | Remove statusline configuration and script, restoring backups if available |

If no flags are provided, the command runs in normal install mode.

If unrecognized flags are provided, display:
```
Warning: Unrecognized flag "[flag]" — ignoring.
Supported flags: --dry-run, --uninstall
```

---

## Phase 1: Pre-Flight Checks

Before making any changes, validate the environment. If running in `--dry-run` mode, report what each check finds but do not proceed to Phase 2.

### 1.1 Detect PowerShell Version

Run `pwsh --version` to check for PowerShell 7+.

| Result | Action |
|--------|--------|
| PowerShell 7+ detected | Continue to next check |
| PowerShell 5.x detected (Windows PowerShell) | Warn: "Windows PowerShell 5.x detected. This statusline requires PowerShell 7+ (pwsh). Install from https://aka.ms/powershell-release" — stop |
| pwsh not found | Error: "PowerShell 7+ (pwsh) is not installed or not in PATH. Install from https://aka.ms/powershell-release" — stop |

### 1.2 Check Target Paths

Verify these paths are accessible:

1. **Claude config directory**: `$env:USERPROFILE\.claude\` — create if missing
2. **Settings file**: `$env:USERPROFILE\.claude\settings.json` — note if exists (will be merged, not overwritten)
3. **Statusline script**: `$env:USERPROFILE\.claude\statusline.ps1` — note if exists (will be backed up)

### 1.3 Check Existing Configuration

If `settings.json` exists, read it and check:
- Is there already a `statusLine` entry? If yes, note the current configuration for the user.
- Is the JSON valid? If not, report: "Error: settings.json contains invalid JSON. Please fix it manually before running this command." — stop.

### 1.4 Pre-Flight Summary

Display a summary before proceeding:

```
Status Line Setup — Pre-Flight Report
======================================
PowerShell:      pwsh [version] ✓
Config dir:      [path] (exists / will create)
Settings file:   [path] (exists — will merge / will create)
Statusline:      [path] (exists — will backup / will create)

Proceed with installation? (y/n)
```

If `--dry-run`, display the summary and stop with: "Dry run complete. No changes were made."

---

## Phase 2: Create/Update Statusline Script

### 2.1 Backup Existing Script

If `statusline.ps1` already exists:
1. Copy it to `statusline.ps1.backup.YYYYMMDD-HHMMSS`
2. Report: "Backed up existing script to [backup path]"

### 2.2 Write Statusline Script

Write the following PowerShell script to `$env:USERPROFILE\.claude\statusline.ps1`:

```powershell
# Claude Code Status Line Script
# Reads JSON input from stdin and displays formatted status line

# Parse input with error handling
try {
    $input_data = $input | ConvertFrom-Json
} catch {
    Write-Host "Status line unavailable"
    exit 0
}

# Validate required fields exist
if ($null -eq $input_data -or $null -eq $input_data.model) {
    Write-Host "Status line unavailable"
    exit 0
}

# ANSI color codes
$cyan = "`e[36m"
$green = "`e[32m"
$yellow = "`e[33m"
$red = "`e[31m"
$magenta = "`e[35m"
$blue = "`e[34m"
$gray = "`e[90m"
$reset = "`e[0m"

# Safe integer max to prevent overflow (2^31 - 1)
$MAX_SAFE_INT = 2147483647

# Extract model display name
$model_name = $input_data.model.display_name
if ([string]::IsNullOrEmpty($model_name)) {
    $model_name = "Claude"
}

# Calculate context window usage
$usage = $input_data.context_window.current_usage
$context_window_size = $input_data.context_window.context_window_size

# Default context window size if not provided
if ($null -eq $context_window_size -or $context_window_size -le 0) {
    $context_window_size = 200000
}

if ($null -ne $usage) {
    # Safely extract token values with null coalescing and overflow protection
    $input_tokens = if ($null -ne $usage.input_tokens) { [Math]::Min([long]$usage.input_tokens, $MAX_SAFE_INT) } else { 0 }
    $cache_read = if ($null -ne $usage.cache_read_input_tokens) { [Math]::Min([long]$usage.cache_read_input_tokens, $MAX_SAFE_INT) } else { 0 }
    $cache_creation = if ($null -ne $usage.cache_creation_input_tokens) { [Math]::Min([long]$usage.cache_creation_input_tokens, $MAX_SAFE_INT) } else { 0 }

    # Calculate total with overflow protection (sum as long, then cap)
    $current_tokens = [Math]::Min([long]$input_tokens + [long]$cache_read + [long]$cache_creation, $MAX_SAFE_INT)
    $output_tokens = if ($null -ne $usage.output_tokens) { [Math]::Min([long]$usage.output_tokens, $MAX_SAFE_INT) } else { 0 }

    # Calculate percentage safely
    $percentage = [math]::Round(($current_tokens / $context_window_size) * 100)
    $percentage = [Math]::Min($percentage, 100)

    # Determine color based on percentage
    if ($percentage -lt 50) {
        $bar_color = $green
    } elseif ($percentage -lt 75) {
        $bar_color = $yellow
    } else {
        $bar_color = $red
    }

    # Create 10-character progress bar
    $filled = [math]::Floor($percentage / 10)
    $empty = 10 - $filled
    $progress_bar = ("█" * $filled) + ("░" * $empty)

    # Format tokens in K (currentK / maxK)
    $current_k = [math]::Round($current_tokens / 1000)
    $max_k = [math]::Round($context_window_size / 1000)
    $tokens_display = "${current_k}K / ${max_k}K"

    # Build context section
    $context_section = "${bar_color}${progress_bar}${reset} ${bar_color}${percentage}%${reset} ${gray}|${reset} ${magenta}${tokens_display}${reset}"
} else {
    # No usage data yet
    $context_section = "${gray}[No context data]${reset}"
}

# Get git branch (if in git repo)
$git_branch = ""
$current_dir = $input_data.workspace.current_dir
if ([string]::IsNullOrEmpty($current_dir)) {
    $current_dir = (Get-Location).Path
}
if ((Test-Path $current_dir) -and (Test-Path (Join-Path $current_dir ".git"))) {
    try {
        Push-Location $current_dir
        $branch = git -c core.filemode=false -c advice.detachedHead=false branch --show-current 2>$null
        Pop-Location
        if ($branch) {
            $git_branch = " ${gray}|${reset} ${green}${branch}${reset}"
        }
    } catch {
        # Git command failed, skip branch display
    }
}

# Get project name (folder name)
$project_name = Split-Path -Leaf $current_dir

# Build final status line in order:
# 1. Model name (cyan)
# 2. Progress bar (color-coded)
# 3. Percentage (same color as bar)
# 4. Tokens (magenta)
# 5. Git branch (green, if applicable)
# 6. Project name (blue)
$status_line = "${cyan}${model_name}${reset} ${gray}|${reset} ${context_section}${git_branch} ${gray}|${reset} ${blue}${project_name}${reset}"

Write-Host $status_line
```

### 2.3 Verify Script Written

Confirm the file was written successfully by checking:
- File exists at the target path
- File size is greater than 0 bytes
- File is readable

If verification fails, report the error and stop. Do not proceed to Phase 3.

---

## Phase 3: Merge Settings Configuration

**Critical:** Do NOT overwrite `settings.json`. Read the existing content, merge in the statusline configuration, and write back.

### 3.1 Read Existing Settings

If `settings.json` exists:
1. Read the file content
2. Parse as JSON
3. If parsing fails, stop with: "Error: settings.json contains invalid JSON. Backup at [path] — please fix manually."

If `settings.json` does not exist, start with an empty object `{}`.

### 3.2 Backup Existing Settings

If `settings.json` exists:
1. Copy to `settings.json.backup.YYYYMMDD-HHMMSS`
2. Report: "Backed up existing settings to [backup path]"

### 3.3 Merge Statusline Configuration

Add or update the `statusLine` key in the settings object:

```json
{
  "statusLine": {
    "type": "command",
    "command": "pwsh -NoProfile -File \"%USERPROFILE%\\.claude\\statusline.ps1\""
  }
}
```

All other existing keys in `settings.json` must be preserved exactly as they were. Only the `statusLine` key is added or replaced.

### 3.4 Write Merged Settings

Write the merged JSON back to `settings.json` with proper formatting (2-space indentation).

---

## Phase 4: Verification

### 4.1 Verify Files

Check that both files exist and are valid:

| Check | Expected |
|-------|----------|
| `statusline.ps1` exists | Yes |
| `statusline.ps1` is non-empty | Yes |
| `settings.json` exists | Yes |
| `settings.json` is valid JSON | Yes |
| `settings.json` contains `statusLine` key | Yes |
| `statusLine.command` references `statusline.ps1` | Yes |

### 4.2 Test Script Execution

Run a basic test of the statusline script:

```powershell
echo '{"model":{"display_name":"Test Model"},"context_window":{"current_usage":{"input_tokens":1000,"cache_read_input_tokens":500,"cache_creation_input_tokens":200},"context_window_size":200000},"workspace":{"current_dir":"."}}' | pwsh -NoProfile -File "$env:USERPROFILE\.claude\statusline.ps1"
```

If the script produces output without errors, report success. If it fails, report the error but note that the files were written — the user can debug the script directly.

### 4.3 Report Results

Display a final summary:

```
Status Line Setup — Complete
=============================
Script:     [path to statusline.ps1] (written)
Settings:   [path to settings.json] (merged)
Backups:    [list any backup files created]

The status line will appear on your next Claude Code session.

Status Line Format:
  Model | ████████░░ 80% | 160K / 200K | main | project-name
```

---

## Uninstall Flow

If `--uninstall` flag is provided, execute this flow instead of the install flow:

### Step 1: Remove Statusline from Settings

1. Read `settings.json`
2. Remove the `statusLine` key (preserve all other keys)
3. Write back the modified JSON
4. If `settings.json` would be empty (`{}`), optionally remove the file

### Step 2: Remove Statusline Script

1. Delete `statusline.ps1`
2. Report: "Removed statusline script"

### Step 3: Restore Backups (Optional)

Check for backup files (`statusline.ps1.backup.*`, `settings.json.backup.*`):
- If found, ask the user: "Backup files found. Restore the most recent backup? (y/n)"
- If yes, restore the most recent backup
- If no, leave backups in place

### Step 4: Report

```
Status Line Uninstalled
========================
Settings:   statusLine key removed from settings.json
Script:     statusline.ps1 deleted
Backups:    [restored / left in place / none found]
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| **pwsh not found** | Stop with installation instructions for PowerShell 7+ |
| **PowerShell version < 7** | Stop with upgrade instructions |
| **settings.json invalid JSON** | Stop — do not attempt to fix corrupted settings |
| **Permission denied on write** | Report which file and suggest running as administrator |
| **statusline.ps1 write fails** | Stop before Phase 3 — do not update settings for a missing script |
| **Disk full / write error** | Report the OS error message and stop |
| **Backup creation fails** | Stop — do not overwrite files without successful backup |
| **Test execution fails** | Report error but note files were written successfully (non-fatal) |

## Status Line Format Reference

The status line displays in this order:
1. **Model name** (Cyan) — e.g., "Claude Opus 4.5"
2. **Progress bar** (Color-coded) — 10-character visual bar
3. **Percentage** (Same color as progress bar) — Context window usage %
4. **Tokens** (Magenta) — currentK / maxK format
5. **Git branch** (Green) — Only shown when in a git repo
6. **Project name** (Blue) — Current folder name

### Color Coding
- Progress bar turns **green** when <50% full
- Progress bar turns **yellow** when 50-75% full
- Progress bar turns **red** when >75% full
- All separators are **gray**

### Context Calculation
Total context usage is calculated from:
- `cache_read_input_tokens` — tokens read from cache
- `cache_creation_input_tokens` — tokens written to cache
- `input_tokens` — uncached tokens

## Related Commands

- `/convert-hooks` — Convert bash scripts to PowerShell (related Windows/PowerShell tooling)
