---
description: Convert plugin hook bash scripts to PowerShell for Windows compatibility
---

# Convert Hooks Command

Convert bash hook scripts to PowerShell for any installed Claude Code plugin. This fixes Windows path handling issues where bash scripts fail due to paths containing spaces.

## Input Validation

**Required Arguments:**
- `<plugin-name>` - Name of the installed plugin to convert hooks for

**Optional Arguments:**
- `--dry-run` - Preview conversions without modifying any files
- `--verbose` - Show detailed output including script contents
- `--list` - List all installed plugins with hooks (does not perform conversion)

**Validation:**
If arguments are missing, display:
```
Usage: /convert-hooks <plugin-name> [--dry-run] [--verbose] [--list]

Examples:
  /convert-hooks ralph-wiggum           # Convert hooks for ralph-wiggum plugin
  /convert-hooks my-plugin --dry-run    # Preview changes without modifying
  /convert-hooks --list                 # Show all plugins with hooks

This command converts bash (.sh) hook scripts to PowerShell (.ps1) and updates
the plugin's hooks.json to reference the PowerShell scripts instead.
```

If plugin is not found, display:
```
Error: Plugin '[name]' not found in installed plugins.

Run '/convert-hooks --list' to see available plugins with hooks.

Plugin cache locations checked:
  - %USERPROFILE%\.claude\plugins\cache\
```

## Instructions

### Phase 1: Discover Plugin Location

1. **Determine plugin cache directory:**
   - Windows: `%USERPROFILE%\.claude\plugins\cache\`
   - Unix: `~/.claude/plugins/cache/`

2. **Search for the plugin:**
   - Look in subdirectories matching pattern: `*/[plugin-name]/*/`
   - Plugin may be under a registry namespace (e.g., `claude-code-plugins/ralph-wiggum/1.0.0/`)
   - Find the most recent version if multiple exist

3. **Verify plugin has hooks:**
   - Check for `hooks/hooks.json` in the plugin directory
   - If no hooks.json exists, report and exit

4. **Report discovery:**
   Show plugin name, location, and hooks config path.

### Phase 2: Parse Hooks Configuration

1. **Read hooks.json** and identify hook events (Stop, PreToolUse, PostToolUse, SessionStart, SessionEnd)

2. **Identify bash script references:**
   - Look for command patterns containing `.sh` files
   - Common patterns: `bash`, `sh`, `/bin/bash`

3. **Build conversion list** showing which scripts need conversion

### Phase 3: Convert Bash Scripts to PowerShell

For each bash script identified:

1. **Read the bash script content**

2. **Perform intelligent conversion** using these mappings:

   **Variable Syntax:**
   - `$VAR` stays the same
   - `${VAR}` becomes `$VAR`
   - `$1, $2, ...` becomes `$args[0], $args[1], ...`
   - `$@` becomes `$args`
   - `$?` becomes `$LASTEXITCODE`

   **Control Structures:**
   - `if [ condition ]; then ... fi` becomes `if (condition) { ... }`
   - `for i in items; do ... done` becomes `foreach ($i in $items) { ... }`
   - `while [ condition ]; do ... done` becomes `while (condition) { ... }`
   - `case $var in ... esac` becomes `switch ($var) { ... }`

   **File Operations:**
   - `[ -f file ]` becomes `Test-Path file`
   - `[ -d dir ]` becomes `Test-Path dir -PathType Container`
   - `[ -z "$var" ]` becomes `[string]::IsNullOrEmpty($var)`
   - `cat file` becomes `Get-Content file -Raw`
   - `echo "text"` becomes `Write-Output "text"`
   - `rm file` becomes `Remove-Item file -Force`

   **JSON Handling:**
   - `jq '.field'` becomes `ConvertFrom-Json` with property access

3. **Add PowerShell header** with `$ErrorActionPreference = "Stop"`

4. **Preserve logic and comments**

5. **Write the PowerShell script** with `.ps1` extension

### Phase 4: Update hooks.json

1. **Transform hook commands:**
   - Before: `bash "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh"`
   - After: `powershell.exe -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.ps1"`

2. **Preserve non-bash hooks** (Python, Node, etc.)

3. **Backup original hooks.json** as `hooks.json.bak`

4. **Write updated hooks.json** with proper formatting

### Phase 5: Show Summary

Display files created, files modified, and backup created. Remind user to restart Claude Code.

## Dry-Run Mode (--dry-run)

Preview conversions without modifying any files. Show what scripts would be converted and how hooks.json would change.

## List Mode (--list)

Show all installed plugins that have hooks, their versions, hook types, and how many bash scripts need conversion.

## Error Handling

- **Plugin not found:** List available plugins and check spelling
- **No hooks.json:** Report that plugin has no hooks configured
- **Script read failure:** Report which script failed to read
- **Complex bash constructs:** Warn about manual review needed
- **Write permission denied:** Suggest running with elevated permissions

## Conversion Quality Notes

**Fully Automated:**
- Simple conditionals and loops
- File existence checks
- Variable assignments
- JSON parsing (jq to ConvertFrom-Json)
- Exit codes
- Echo/print statements

**May Need Manual Review:**
- Process substitution `<(...)` and `>(...)`
- Here-documents `<<EOF`
- Complex regex in sed/awk
- Signal handling (trap)
- Background processes (&)
- Pipelines with multiple stages

When complex constructs are detected, add TODO comments in the PowerShell output.

## Example Usage

```
User: /convert-hooks ralph-wiggum

Claude:
Plugin Discovery
----------------
Plugin: ralph-wiggum
Location: C:\Users\...\ralph-wiggum\1.0.0
Hooks Config: hooks/hooks.json

Hooks Analysis
--------------
Hook Event: Stop
  Script: stop-hook.sh (178 lines)
  Status: Converting to PowerShell...

Converting stop-hook.sh... Done

Updating hooks.json...
  Backup created: hooks.json.bak
  Updated Stop hook command

Hook Conversion Complete

Files Created:
  1. hooks/stop-hook.ps1

Files Modified:
  1. hooks/hooks.json

The plugin's hooks are now configured to use PowerShell.
Restart Claude Code to use the updated hooks.
```
