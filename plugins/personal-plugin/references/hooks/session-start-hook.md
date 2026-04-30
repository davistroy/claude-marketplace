# Hook Recipe: Session Start Plan Primer

**Type:** Example — copy and adapt for your project. NOT auto-installed.

## Purpose

When a session starts, reads IMPLEMENTATION_PLAN.md and displays current plan status. Primes context so the user (and Claude) know where work left off.

## hooks.json Snippet

```json
{
  "SessionStart": [
    {
      "type": "command",
      "command": "bash -c 'if [ -f IMPLEMENTATION_PLAN.md ]; then echo \"📋 Active plan found:\"; grep -c \"Status: COMPLETE\" IMPLEMENTATION_PLAN.md | xargs -I{} echo \"  Completed: {} items\"; grep -c \"Status: PENDING\\|Status: IN_PROGRESS\" IMPLEMENTATION_PLAN.md | xargs -I{} echo \"  Remaining: {} items\"; echo \"  Run /implement-plan to continue.\"; fi'"
    }
  ]
}
```

## How It Works

- Fires when a Claude Code session starts (SessionStart event)
- Checks if IMPLEMENTATION_PLAN.md exists
- Counts completed and remaining items
- Displays a brief status summary
- No-op if no plan exists

## Customization

- Add PROGRESS.md reading for more detailed status
- Include git branch info: `git branch --show-current`
- Check for stale `.implement-plan-state.json` (interrupted sessions)
