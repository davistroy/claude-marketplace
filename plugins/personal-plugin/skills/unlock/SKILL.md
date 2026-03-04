---
name: unlock
description: Load secrets from Bitwarden Secrets Manager into environment using bws CLI
allowed-tools: Bash(bws:*), Bash(command:*), Bash(which:*), Bash(where:*), Bash(echo:*), Bash(export:*), Bash(powershell*), Bash(python:*)
---

# Unlock Skill

Load project secrets from Bitwarden Secrets Manager into the current environment using the `bws` CLI. Fully stateless — no vault unlock or session tokens required.

## Proactive Triggers

Suggest this skill when:
1. User starts a session and environment variables (API keys) are needed
2. Before running skills that require API keys — `research-topic`, `visual-explainer`, `summarize-feedback`
3. User mentions Bitwarden, secrets, API keys, or "unlock"
4. A command fails with an authentication or missing-key error

## Configuration

| Item | Value |
|------|-------|
| BWS project ID | `$BWS_PROJECT_ID` env var, or `5022ea9c-e711-4f4e-bf5f-b3df0181a41d` (default project ID for Troy's vault — override via `BWS_PROJECT_ID`. Default as of 2026-03-04 — verify if errors occur) |
| Access token env var | `TROY` |
| bws install docs | https://bitwarden.com/help/secrets-manager-cli/ |

## Implementation

When the user invokes `/unlock`, follow these steps:

### Step 1: Detect platform and locate bws

**Windows (win32):**
```powershell
where.exe bws 2>$null || (Test-Path "$env:USERPROFILE\bin\bws.exe")
```

**Linux/macOS:**
```bash
command -v bws || test -x "$HOME/bin/bws"
```

If not found, tell the user to install bws from https://bitwarden.com/help/secrets-manager-cli/ and stop.

### Step 2: Get access token

The access token is stored in the `TROY` environment variable.

**Windows** — check process env first, then Windows user env:
```powershell
$token = $env:TROY
if (-not $token) { $token = [System.Environment]::GetEnvironmentVariable('TROY', 'User') }
```

**Linux/macOS** — check process env:
```bash
TOKEN="$TROY"
```

If empty, tell the user:
- **Windows:** Set via `[System.Environment]::SetEnvironmentVariable('TROY', 'your-token', 'User')`
- **Linux/macOS:** Add `export TROY="your-token"` to `~/.bashrc` or `~/.zshrc`

Then stop.

### Step 3: Fetch secrets and export

Run bws with the access token set for that single command, then parse the JSON output and export each secret as an environment variable.

**Windows:**
```powershell
# Use BWS_PROJECT_ID env var if set, otherwise fall back to default
# Default project ID for Troy's vault — override via BWS_PROJECT_ID
# Default as of 2026-03-04 — verify if errors occur
$projectId = if ($env:BWS_PROJECT_ID) { $env:BWS_PROJECT_ID } else { '5022ea9c-e711-4f4e-bf5f-b3df0181a41d' }
$env:BWS_ACCESS_TOKEN = $token
$json = bws secret list $projectId 2>&1
Remove-Item env:BWS_ACCESS_TOKEN -ErrorAction SilentlyContinue
$secrets = $json | ConvertFrom-Json
foreach ($s in $secrets) {
    # Validate key name: only alphanumeric and underscores allowed
    if ($s.key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
        Write-Warning "Skipping invalid key name: $($s.key)"
        continue
    }
    [System.Environment]::SetEnvironmentVariable($s.key, $s.value, 'Process')
}
```

**Linux/macOS:**

**SECURITY: No eval with external data.** Use Python to write a temporary script with properly escaped values, source it, then delete it.

```bash
# Use BWS_PROJECT_ID env var if set, otherwise fall back to default
# Default project ID for Troy's vault — override via BWS_PROJECT_ID
# Default as of 2026-03-04 — verify if errors occur
PROJECT_ID="${BWS_PROJECT_ID:-5022ea9c-e711-4f4e-bf5f-b3df0181a41d}"
JSON=$(BWS_ACCESS_TOKEN="$TOKEN" bws secret list "$PROJECT_ID" 2>&1)

# Generate safe export statements using shlex.quote() — never eval raw values
EXPORT_FILE=$(mktemp /tmp/bws-exports.XXXXXX)
chmod 600 "$EXPORT_FILE"

echo "$JSON" | python3 -c "
import json, sys, shlex, re

data = json.load(sys.stdin)
for s in data:
    key = s['key']
    value = s['value']
    # Validate key: must be a valid shell variable name
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
        print(f'# SKIPPED invalid key: {key!r}', file=sys.stderr)
        continue
    # Use shlex.quote() to safely escape the value for shell
    safe_value = shlex.quote(value)
    print(f'export {key}={safe_value}')
" > "$EXPORT_FILE"

# Source the safe exports, then remove the temp file
source "$EXPORT_FILE"
rm -f "$EXPORT_FILE"
```

### Step 4: Report results

Print the count and list of secret names loaded (never print values). Example output:

```text
Loaded 8 secret(s) from Bitwarden Secrets Manager:
  ANTHROPIC_API_KEY
  OPENAI_API_KEY
  GOOGLE_API_KEY
  NOTION_API_KEY
  PUSHOVER_API_TOKEN
  PUSHOVER_USER_KEY
  NOTION_VOICE_CAPTURES_DB_ID
  NOTION_WEEKLY_SUMMARIES_DB_ID
```

## Error Handling

| Error | Action |
|-------|--------|
| `bws` not found | Print install URL and stop |
| `TROY` env var empty | Print platform-specific setup instructions and stop |
| `bws secret list` fails | Print the error output from bws and stop |
| JSON parse fails | Print raw output for debugging and stop |
| Invalid key name in secrets | Log warning, skip that secret, continue with remaining secrets |
| Temp file creation fails | Print error and stop — do not fall back to eval |

## Performance

Typically completes in under 5 seconds. Single bws CLI call with JSON parsing.

## Examples

**Standard unlock at session start:**
```text
/unlock
```
Output:
```text
Loaded 8 secret(s) from Bitwarden Secrets Manager:
  ANTHROPIC_API_KEY
  OPENAI_API_KEY
  GOOGLE_API_KEY
  NOTION_API_KEY
  PUSHOVER_API_TOKEN
  PUSHOVER_USER_KEY
  NOTION_VOICE_CAPTURES_DB_ID
  NOTION_WEEKLY_SUMMARIES_DB_ID
```

**Proactive trigger before research:**
```text
User: /research-topic "RAG system best practices"
Claude: I need API keys to run multi-provider research. Let me load them first.
  → Runs /unlock automatically
  → Loaded 8 secret(s) from Bitwarden Secrets Manager
  → Proceeds with research-topic
```

**When bws CLI is not installed:**
```text
/unlock
```
Output:
```text
bws CLI not found. Install it from:
  https://bitwarden.com/help/secrets-manager-cli/
```

**When access token is not configured:**
```text
/unlock
```
Output:
```text
TROY environment variable is not set.
Windows: [System.Environment]::SetEnvironmentVariable('TROY', 'your-token', 'User')
Linux/macOS: Add export TROY="your-token" to ~/.bashrc or ~/.zshrc
```

## Security Considerations

- **No eval with external data:** The Linux/macOS path uses `shlex.quote()` to escape secret values and writes to a temporary file with `chmod 600` permissions, then sources it. The dangerous `eval` pattern that could allow shell injection through crafted secret values is eliminated.
- **Key name validation:** Both Windows and Linux/macOS paths validate that secret key names match `^[A-Za-z_][A-Za-z0-9_]*$` before using them as environment variable names. Invalid keys are skipped with a warning.
- **Temp file security:** The export file is created with `mktemp` (unpredictable filename) and restricted to owner-only read/write (`chmod 600`). It is deleted immediately after sourcing.
- Access token is set in env only for the duration of the `bws` call, then cleared.
- Secret **values** are never printed — only key names.
- No persistent files are written — secrets exist only in process environment.
- The project ID is not sensitive — it is useless without the access token.
