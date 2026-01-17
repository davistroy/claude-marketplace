# Plugin Marketplace Troubleshooting - 2026-01-17

## Problem
After uninstalling plugins, removing marketplace, restarting Claude Code, and re-adding the marketplace (`davistroy/claude-marketplace`), plugins/commands/skills were not visible.

## Root Cause
Plugins were installed but **disabled** in `~/.claude/settings.json`:

```json
"bpmn-plugin@troys-plugins": false,
"personal-plugin@troys-plugins": false
```

## Solution
Edit `~/.claude/settings.json` and change both to `true`:

```json
"bpmn-plugin@troys-plugins": true,
"personal-plugin@troys-plugins": true
```

Then **restart Claude Code** for changes to take effect.

## Verification Steps After Restart

1. Check plugins are enabled:
   ```
   /plugin list
   ```

2. Verify commands are available:
   ```
   /help
   ```

   Should show personal-plugin commands like `/ship`, `/review-arch`, `/assess-document`, etc.

3. If still not working, check:
   - `~/.claude/settings.json` has plugins set to `true`
   - Marketplace is registered (should see `troys-plugins` in plugin list)

## Repository Structure (Verified Working)
- `.claude-plugin/marketplace.json` - Marketplace config (correct)
- `plugins/personal-plugin/.claude-plugin/plugin.json` - Plugin metadata (correct)
- `plugins/personal-plugin/commands/*.md` - 20+ commands (present)
- `plugins/personal-plugin/skills/*/SKILL.md` - 3 skills (present)
- `plugins/bpmn-plugin/.claude-plugin/plugin.json` - Plugin metadata (correct)
- `plugins/bpmn-plugin/skills/*/SKILL.md` - 3 skills (present)

## Key Insight
The `/plugin marketplace add` command installs plugins but may default them to disabled. Always verify the `enabledPlugins` section in settings.json after installation.
