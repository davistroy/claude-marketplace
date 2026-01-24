---
name: unlock
description: Unlock Bitwarden session and load project secrets into environment
---

# Unlock Skill

Automatically unlock your Bitwarden vault and load project-specific secrets into the current environment. Fully automated - no manual password entry required.

## Purpose

This skill provides a one-command workflow for accessing project secrets:
1. Reads master password from `~\.claude\.env`
2. Unlocks Bitwarden vault automatically (if locked)
3. Auto-detects current project name from working directory
4. Loads secrets from Bitwarden into environment variables

## Security Model

**Automated approach:**
- Master password stored in `~\.claude\.env` (local file, not in repo)
- Password is passed via environment variable, immediately cleared after use
- Session tokens are cached for subsequent operations

## Implementation

When the user invokes `/unlock`, execute the unlock-and-load script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\scripts\unlock-and-load.ps1"
```

**The script will:**
1. Check Bitwarden vault status
2. If locked, read password from `~\.claude\.env` and unlock automatically
3. Auto-detect project name from current directory
4. Load secrets from `dev/<PROJECT_NAME>/api-keys` in Bitwarden
5. Set them as environment variables in the current session

## Error Handling

### Password File Not Found
If `~\.claude\.env` doesn't exist or doesn't contain `BITWARDEN_MASTER_PASSWORD`:
- Create the file with: `BITWARDEN_MASTER_PASSWORD=your-password-here`

### Project Not Found in Bitwarden
If no secrets exist for the current project:
- Script will show available `dev/*` items
- Create new item via: `~\.claude\scripts\store-secrets.ps1 <PROJECT_NAME>`

## Usage Examples

```powershell
cd C:\projects\slide-generator
/unlock
# Vault unlocked successfully!
# Loaded 3 secret(s) for 'slide-generator'
```

## Related Scripts

- `~\.claude\scripts\unlock-and-load.ps1` - Combined unlock + load script
- `~\.claude\scripts\get-secrets.ps1` - Load secrets (requires unlocked vault)
- `~\.claude\scripts\store-secrets.ps1` - Create/update Bitwarden items
- `~\.claude\.env` - Contains `BITWARDEN_MASTER_PASSWORD`
