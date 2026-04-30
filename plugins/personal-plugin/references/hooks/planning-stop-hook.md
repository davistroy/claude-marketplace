# Hook Recipe: Planning Stop Warning

**Type:** Example — copy and adapt for your project. NOT auto-installed.

## Purpose

Warns when a session ends and IMPLEMENTATION_PLAN.md has unchecked work items. Prevents accidentally abandoning in-progress plans.

## hooks.json Snippet

Add this to your project's `.claude/hooks.json` (or `hooks/hooks.json` in a plugin):

```json
{
  "Stop": [
    {
      "type": "command",
      "command": "bash -c 'if [ -f IMPLEMENTATION_PLAN.md ] && grep -q \"Status: PENDING\\|Status: IN_PROGRESS\" IMPLEMENTATION_PLAN.md; then echo \"⚠️  IMPLEMENTATION_PLAN.md has incomplete work items. Run /implement-plan to continue.\"; fi'"
    }
  ]
}
```

## How It Works

- Fires when the Claude Code session ends (Stop event)
- Checks if IMPLEMENTATION_PLAN.md exists and contains PENDING or IN_PROGRESS items
- If found, prints a warning reminder
- No-op if no plan exists or all items are complete

## Customization

- Change the file path if your plan lives elsewhere
- Add additional checks (e.g., warn about uncommitted changes)
- Combine with other Stop hooks in the same array
