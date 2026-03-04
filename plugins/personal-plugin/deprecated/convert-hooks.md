---
description: Convert plugin hook bash scripts to PowerShell for Windows compatibility
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Convert Hooks Command

Convert bash hook scripts to PowerShell for any installed Claude Code plugin. This fixes Windows path handling issues where bash scripts fail due to paths containing spaces.

**Limitation:** Automated conversion handles only simple bash scripts -- variable assignments, conditionals, file existence checks, echo/print statements, exit codes, and basic path manipulations. Scripts that use pipes, process substitution, awk/sed, signal handling (`trap`), background processes, or here-documents will require manual review. The converter inserts `# TODO: Manual review required` comments wherever it encounters constructs it cannot reliably translate.

## Input Validation

**Required Arguments:**
- `<plugin-name>` - Name of the installed plugin to convert hooks for

**Optional Arguments:**
- `--dry-run` - Preview conversions without modifying any files
- `--verbose` - Show detailed output including script contents
- `--list` - List all installed plugins with hooks (does not perform conversion)
- `--validate` - After conversion, validate that generated PowerShell scripts are syntactically correct

**Validation:**
If arguments are missing, display:
```text
Usage: /convert-hooks <plugin-name> [--dry-run] [--verbose] [--list] [--validate]

Examples:
  /convert-hooks my-plugin              # Convert hooks for my-plugin plugin
  /convert-hooks my-plugin --dry-run    # Preview changes without modifying
  /convert-hooks my-plugin --validate   # Convert and validate output
  /convert-hooks --list                 # Show all plugins with hooks

This command converts bash (.sh) hook scripts to PowerShell (.ps1) and updates
the plugin's hooks.json to reference the PowerShell scripts instead.
```

If plugin is not found, display:
```text
Error: Plugin '[name]' not found in installed plugins.

Run '/convert-hooks --list' to see available plugins with hooks.

Plugin cache locations checked:
  - %USERPROFILE%\.claude\plugins\cache\
```

## Instructions

### Phase 1: Detect Platform and Determine Conversion Direction

Detect the current platform:
- **Windows:** Convert bash (.sh) to PowerShell (.ps1)
- **macOS/Linux:** Convert PowerShell (.ps1) to bash (.sh) if PowerShell hooks exist

Do not present both conversion directions. Detect the platform and offer the relevant conversion only. Display:
```text
Platform detected: [Windows/macOS/Linux]
Conversion direction: [bash -> PowerShell / PowerShell -> bash]
```

### Phase 2: Discover Plugin Location

1. **Determine plugin cache directory:**
   - Windows: `%USERPROFILE%\.claude\plugins\cache\`
   - Unix: `~/.claude/plugins/cache/`

2. **Search for the plugin:**
   - Look in subdirectories matching pattern: `*/[plugin-name]/*/`
   - Plugin may be under a registry namespace (e.g., `claude-code-plugins/my-plugin/1.0.0/`)
   - Find the most recent version if multiple exist

3. **Verify plugin has hooks:**
   - Check for `hooks/hooks.json` in the plugin directory
   - If no hooks.json exists, report and exit

4. **Report discovery:**
   Show plugin name, location, and hooks config path.

### Phase 3: Parse Hooks Configuration

1. **Read hooks.json** and identify hook events (Stop, PreToolUse, PostToolUse, SessionStart, SessionEnd)

2. **Identify source script references:**
   - On Windows: look for `.sh` files (bash scripts to convert)
   - On macOS/Linux: look for `.ps1` files (PowerShell scripts to convert)

3. **Build conversion list** showing which scripts need conversion

### Phase 4: Convert Scripts

For each script identified:

1. **Read the source script content**

2. **Assess complexity** before converting. Warn the user if the script contains constructs that cannot be reliably automated:

   | Construct | Automatable? | Notes |
   |-----------|-------------|-------|
   | Variable assignment | Yes | Direct mapping |
   | if/else/fi | Yes | Syntax differs but logic maps cleanly |
   | File existence checks | Yes | `[ -f ]` to `Test-Path` |
   | echo/printf | Yes | `Write-Output` |
   | exit codes | Yes | `$LASTEXITCODE` |
   | for/while loops | Yes | Simple iteration maps well |
   | Pipes (`\|`) | Partial | Simple pipes work; complex chains need review |
   | Process substitution `<()` | No | No PowerShell equivalent |
   | Here-documents `<<EOF` | No | Use here-strings `@" "@ ` but semantics differ |
   | sed/awk | No | Requires manual rewrite with `-replace` or `Select-String` |
   | trap (signal handling) | No | Use `try/finally` but behavior differs |
   | Background processes (`&`) | No | Use `Start-Job` but semantics differ |
   | Arrays (`${arr[@]}`) | Partial | Array syntax differs significantly |

3. **Perform conversion** using these mappings (bash to PowerShell direction shown):

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

4. **For non-automatable constructs**, insert TODO comments:
   ```powershell
   # TODO: Manual review required — original bash used process substitution <(...)
   # Original line: diff <(sort file1.txt) <(sort file2.txt)
   ```

5. **Add PowerShell header** with `$ErrorActionPreference = "Stop"`

6. **Preserve logic and comments**

7. **Write the converted script** with the target extension

#### Concrete Before/After Example

**Bash input** (`hooks/stop-hook.sh`):
```bash
#!/bin/bash
HOOK_DIR="$(dirname "$0")"
CONFIG_FILE="${HOOK_DIR}/../config.json"

if [ -f "$CONFIG_FILE" ]; then
  SETTING=$(cat "$CONFIG_FILE" | jq -r '.cleanup')
  if [ "$SETTING" = "true" ]; then
    echo "Running cleanup..."
    rm -f "${HOOK_DIR}/../.tmp/"*.log
    echo "Cleanup complete (exit code: $?)"
  fi
else
  echo "Warning: Config file not found"
  exit 1
fi
```

**PowerShell output** (`hooks/stop-hook.ps1`):
```powershell
$ErrorActionPreference = "Stop"

$HOOK_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$CONFIG_FILE = Join-Path (Split-Path -Parent $HOOK_DIR) "config.json"

if (Test-Path $CONFIG_FILE) {
    $config = Get-Content $CONFIG_FILE -Raw | ConvertFrom-Json
    $SETTING = $config.cleanup
    if ($SETTING -eq "true") {
        Write-Output "Running cleanup..."
        Remove-Item (Join-Path (Split-Path -Parent $HOOK_DIR) ".tmp\*.log") -Force -ErrorAction SilentlyContinue
        Write-Output "Cleanup complete (exit code: $LASTEXITCODE)"
    }
} else {
    Write-Output "Warning: Config file not found"
    exit 1
}
```

### Phase 5: Update hooks.json

1. **Transform hook commands:**
   - Before: `bash "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh"`
   - After: `powershell.exe -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.ps1"`

2. **Preserve non-target hooks** (Python, Node, etc. are left unchanged)

3. **Backup original hooks.json** as `hooks.json.bak`

4. **Write updated hooks.json** with proper formatting

### Phase 6: Validate Generated Scripts (--validate)

If `--validate` flag is provided (or always recommended), validate the generated scripts:

**On Windows (PowerShell validation):**
```powershell
# Parse-only check — does not execute the script
powershell.exe -Command "Get-Command -Syntax ([ScriptBlock]::Create((Get-Content 'hooks/stop-hook.ps1' -Raw)))" 2>&1
```

Or use `pwsh` if PowerShell 7+ is available:
```powershell
pwsh -Command "[System.Management.Automation.Language.Parser]::ParseFile('hooks/stop-hook.ps1', [ref]$null, [ref]$errors); if ($errors) { $errors | ForEach-Object { Write-Error $_ } }"
```

**Report validation results:**
```text
Validation Results:
  hooks/stop-hook.ps1    PASS (valid PowerShell syntax)
  hooks/pre-tool.ps1     FAIL (line 12: unexpected token ')')
```

If validation fails, warn the user and suggest manual review. Do not delete the generated file — the user may want to fix it manually.

### Phase 7: Show Summary

Display files created, files modified, backup created, and any TODO comments that require manual attention. Remind user to restart Claude Code.

```text
----------------------------------------------
Hook Conversion Complete
----------------------------------------------

Files Created:
  1. hooks/stop-hook.ps1

Files Modified:
  1. hooks/hooks.json

Backup Created:
  1. hooks/hooks.json.bak

Manual Review Required: [count] TODO comments in generated scripts
  - hooks/stop-hook.ps1:15 — process substitution
  - hooks/stop-hook.ps1:23 — sed regex replacement

Restart Claude Code to use the updated hooks.
```

## Dry-Run Mode (--dry-run)

Preview conversions without modifying any files. Show what scripts would be converted, any complexity warnings, and how hooks.json would change.

## List Mode (--list)

Show all installed plugins that have hooks, their versions, hook types, and how many scripts need conversion.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Plugin not found | Plugin name misspelled or not installed | List available plugins with `--list`, check spelling |
| No hooks.json | Plugin has no hooks configured | Report that plugin has no hooks; nothing to convert |
| Source hook file not found | hooks.json references a script that doesn't exist | Report the missing file path; may indicate a broken plugin installation |
| Unsupported script complexity | Script uses constructs that cannot be automated | Warn the user, insert TODO comments, suggest manual conversion for those sections |
| PowerShell/bash not installed | Target shell not available on the system | Provide installation instructions (e.g., `winget install Microsoft.PowerShell` on Windows) |
| Script read failure | Permission denied or encoding issue | Report which script failed and suggest checking file permissions or encoding |
| Write permission denied | Cannot write to plugin cache directory | Suggest running with elevated permissions or copying plugin locally |
| Validation failure | Generated script has syntax errors | Report specific errors with line numbers; do not delete the generated file |

## Related Commands

- `/convert-markdown` -- Convert markdown files to Word format (another conversion command)
- `/validate-plugin` -- Verify plugin structure including hook Windows compatibility
- `/scaffold-plugin` -- Create a new plugin with proper structure
