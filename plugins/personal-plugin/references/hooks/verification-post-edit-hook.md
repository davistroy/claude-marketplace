# Hook Recipe: Post-Edit Verification

**Type:** Example — copy and adapt for your project. NOT auto-installed.

## Purpose

Runs verification commands (lint, typecheck) after Edit or Write operations on source files. Catches issues immediately rather than at phase end.

## hooks.json Snippet

Add this to your project's `.claude/settings.json` under the `hooks` key (or to `hooks/hooks.json` in a plugin):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "ruff check --fix . 2>/dev/null; exit 0",
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

- Fires after an `Edit` or `Write` tool call completes (`PostToolUse` event)
- **The `matcher` does the tool filtering.** It is matched against the tool name, so the command body does not need to re-check which tool ran
- Runs the linter (example: `ruff check --fix`)
- The trailing `exit 0` keeps a lint failure from interrupting the session; drop it if you want failures to surface
- Timeout prevents hanging on large codebases

**The matcher must name the tool you want to act on.** Pairing `"matcher": "Bash"` with a body that tests whether the tool was `Edit` yields a hook that registers cleanly, validates fine, and **never runs its payload** — the matcher already guaranteed the tool was `Bash`, so the `Edit` test can never be true. Match on `Edit|Write` and let the matcher do the work.

## Customization

- Replace `ruff check --fix` with your project's lint command (`eslint --fix`, `cargo clippy`, etc.)
- Add typecheck: `mypy src/ 2>/dev/null` or `tsc --noEmit 2>/dev/null`
- Restrict to specific file patterns by reading the edited path from the hook's **stdin JSON** — there is no `$CLAUDE_FILE_PATH` environment variable:

  ```json
  {
    "type": "command",
    "command": "bash -c 'INPUT=$(cat); F=$(echo \"$INPUT\" | jq -r \".tool_input.file_path // empty\"); case \"$F\" in *.py) ruff check --fix \"$F\" 2>/dev/null;; esac; exit 0'",
    "timeout": 10
  }
  ```

- Adjust timeout based on your project size

**Ground truth:** this structure matches the working hook in `plugins/personal-plugin/hooks/hooks.json`. That one pairs `"matcher": "Bash"` with a `jq` read of `.tool_input.command` — the correct pairing, because the field it inspects belongs to the tool it matched.
