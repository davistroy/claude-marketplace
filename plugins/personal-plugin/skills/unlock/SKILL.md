---
name: unlock
description: Load secrets from Bitwarden Secrets Manager into environment using bws CLI
allowed-tools: Bash(bws:*), Bash(command:*), Bash(which:*), Bash(where:*), Bash(echo:*), Bash(export:*), Bash(powershell*), Bash(python:*)
---

# Unlock Skill

Load project secrets from Bitwarden Secrets Manager into the current environment using the `bws` CLI. Fully stateless — no vault unlock or session tokens required.

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

If not found, tell the user to install bws from https://bitwarden.com/help/secrets-manager-cli/  and stop.

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
    [System.Environment]::SetEnvironmentVariable($s.key, $s.value, 'Process')
}
```

**Linux/macOS:**
```bash
JSON=$(BWS_ACCESS_TOKEN="$TOKEN" bws secret list 5022ea9c-e711-4f4e-bf5f-b3df0181a41d 2>&1)
# Parse with python (available on all systems)
eval "$(echo "$JSON" | python3 -c "
import json, sys
for s in json.load(sys.stdin):
    k, v = s['key'], s['value']
    print(f'export {k}=\"{v}\"')
")"
```

### Step 4: Report results

Print the count and list of secret names loaded (never print values). Example output:

```
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

## Security Notes

- Access token is set in env only for the duration of the `bws` call, then cleared
- Secret **values** are never printed — only key names
- No files are written — secrets exist only in process environment
- The project ID is not sensitive — it's useless without the access token
