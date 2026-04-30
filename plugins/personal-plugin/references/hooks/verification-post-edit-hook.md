# Hook Recipe: Post-Edit Verification

**Type:** Example — copy and adapt for your project. NOT auto-installed.

## Purpose

Runs verification commands (lint, typecheck) after Edit operations on source files. Catches issues immediately rather than at phase end.

## hooks.json Snippet

```json
{
  "PostToolUse": [
    {
      "type": "command",
      "command": "bash -c 'if echo \"$CLAUDE_TOOL_NAME\" | grep -q \"Edit\"; then ruff check --fix . 2>/dev/null; fi'",
      "timeout": 10000
    }
  ]
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
