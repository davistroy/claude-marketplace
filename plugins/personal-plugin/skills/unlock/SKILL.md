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
| BWS project ID | `5022ea9c-e711-4f4e-bf5f-b3df0181a41d` |
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
$env:BWS_ACCESS_TOKEN = $token
$json = bws secret list 5022ea9c-e711-4f4e-bf5f-b3df0181a41d 2>&1
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
JSON=$(BWS_ACCESS_TOKEN="$TOKEN" bws secret list 5022ea9c-e711-4f4e-bf5f-b3df0181a41d 2>&1)

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

## Security Considerations

- **No eval with external data:** The Linux/macOS path uses `shlex.quote()` to escape secret values and writes to a temporary file with `chmod 600` permissions, then sources it. The dangerous `eval` pattern that could allow shell injection through crafted secret values is eliminated.
- **Key name validation:** Both Windows and Linux/macOS paths validate that secret key names match `^[A-Za-z_][A-Za-z0-9_]*$` before using them as environment variable names. Invalid keys are skipped with a warning.
- **Temp file security:** The export file is created with `mktemp` (unpredictable filename) and restricted to owner-only read/write (`chmod 600`). It is deleted immediately after sourcing.
- Access token is set in env only for the duration of the `bws` call, then cleared.
- Secret **values** are never printed — only key names.
- No persistent files are written — secrets exist only in process environment.
- The project ID is not sensitive — it is useless without the access token.
