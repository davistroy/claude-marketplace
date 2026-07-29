# Hook Recipe: Post-Edit Verification

**Type:** Example — copy and adapt for your project. NOT auto-installed.

## Purpose

Runs verification commands (lint, typecheck) after Edit operations on source files. Catches issues immediately rather than at phase end.

## hooks.json Snippet

Add this to your project's `.claude/settings.json` under the `hooks` key (or to `hooks/hooks.json` in a plugin):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'INPUT=$(cat); if command -v jq >/dev/null 2>&1; then TOOL=$(echo \"$INPUT\" | jq -r \".tool_name // empty\" 2>/dev/null); else TOOL=\"$INPUT\"; fi; if echo \"$TOOL\" | grep -q \"Edit\"; then ruff check --fix . 2>/dev/null; exit 0; fi; exit 0'",
            "timeout": 10,
            "statusMessage": "Running verification checks…"
          }
        ]
      }
    ]
  }
}
```

## How It Works

- Fires after any tool use (PostToolUse event)
- Checks if the tool was Edit
- If so, runs the linter (example: `ruff check --fix`)
- Timeout prevents hanging on large codebases

## Customization

- Replace `ruff check --fix` with your project's lint command (`eslint --fix`, `cargo clippy`, etc.)
- Add typecheck: `mypy src/ 2>/dev/null` or `tsc --noEmit 2>/dev/null`
- Restrict to specific file patterns by checking `$CLAUDE_FILE_PATH`
- Adjust timeout based on your project size
