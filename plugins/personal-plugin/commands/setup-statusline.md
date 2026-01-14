---
description: "[Personal] Troy's custom status line setup (Windows/PowerShell)"
---

# Troy's Status Line Setup

> **Note:** This command is specific to Troy's Windows environment and uses hardcoded paths. Use as a reference for creating your own status line configuration.

Set up Troy's custom status line for Claude Code on Windows.

## Instructions

1. Create the PowerShell script at `C:\Users\Troy Davis\.claude\statusline.ps1` with this content:

```powershell
# Claude Code Status Line Script
# Reads JSON input from stdin and displays formatted status line

$input_data = $input | ConvertFrom-Json

# ANSI color codes
$cyan = "`e[36m"
$green = "`e[32m"
$yellow = "`e[33m"
$red = "`e[31m"
$magenta = "`e[35m"
$blue = "`e[34m"
$gray = "`e[90m"
$reset = "`e[0m"

# Extract model display name
$model_name = $input_data.model.display_name

# Calculate context window usage
$usage = $input_data.context_window.current_usage
$context_window_size = $input_data.context_window.context_window_size

if ($null -ne $usage) {
    # Calculate total current tokens from all sources
    $input_tokens = $usage.input_tokens
    $cache_read = $usage.cache_read_input_tokens
    $cache_creation = $usage.cache_creation_input_tokens
    $current_tokens = $input_tokens + $cache_read + $cache_creation
    $output_tokens = $usage.output_tokens

    # Calculate percentage
    $percentage = [math]::Round(($current_tokens / $context_window_size) * 100)

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
if (Test-Path (Join-Path $current_dir ".git")) {
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

2. Update the global settings at `C:\Users\Troy Davis\.claude\settings.json` to include:

```json
{
  "statusLine": {
    "type": "command",
    "command": "pwsh -NoProfile -File \"C:\\Users\\Troy Davis\\.claude\\statusline.ps1\""
  }
}
```

## Status Line Format

The status line displays in this order:
1. **Model name** (Cyan) - e.g., "Claude Opus 4.5"
2. **Progress bar** (Color-coded) - 10-character visual bar
3. **Percentage** (Same color as progress bar) - Context window usage %
4. **Tokens** (Magenta) - currentK / maxK format
5. **Git branch** (Green) - Only shown when in a git repo
6. **Project name** (Blue) - Current folder name

### Color Coding
- Progress bar turns **green** when <50% full
- Progress bar turns **yellow** when 50-75% full
- Progress bar turns **red** when >75% full
- All separators are **gray**

### Context Calculation
Total context usage is calculated from:
- `cache_read_input_tokens` - tokens read from cache
- `cache_creation_input_tokens` - tokens written to cache
- `input_tokens` - uncached tokens
