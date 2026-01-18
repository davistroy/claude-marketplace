# PLAN: Research-Topic Terminal UI Improvement

## Problem Statement

The research-orchestrator tool has Rich UI code implemented (`ui.py`), but during execution within Claude Code:
1. **No real-time progress visible** — The 5-15 minute research execution appears as a black box
2. **Output is plain/minimal** — Despite Rich being available, the beautiful terminal UI isn't rendering
3. **Status updates are buffered** — Live updates don't stream through to the user

Root causes to investigate:
- Rich's `Live` display may not work when stdout is captured/piped
- Python output buffering prevents real-time visibility
- The bash command may complete before output is flushed

## Goals

1. **Real-time progress visibility** — User sees status updates as they happen
2. **Beautiful terminal formatting** — Leverage Rich's panels, tables, spinners, progress bars
3. **Works in both contexts** — Claude Code and standalone terminal execution
4. **Graceful degradation** — Falls back cleanly if Rich unavailable or terminal incompatible

## Investigation Tasks (Pre-Implementation)

Before implementing, verify:

- [ ] **Test current Rich UI standalone** — Run `python -m research_orchestrator execute` directly in terminal to confirm Rich works
- [ ] **Test output buffering** — Check if `-u` flag or `PYTHONUNBUFFERED=1` helps in Claude Code context
- [ ] **Check Rich Live detection** — Rich may disable Live updates when it detects non-interactive terminal

## Implementation Plan

### Phase 1: Fix Output Visibility in Claude Code Context

**File:** `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/cli.py`

1. **Force unbuffered output**
   ```python
   import sys
   import os

   # At module level or in main()
   os.environ['PYTHONUNBUFFERED'] = '1'
   sys.stdout.reconfigure(line_buffering=True)
   sys.stderr.reconfigure(line_buffering=True)
   ```

2. **Add Rich terminal detection override**
   ```python
   # Allow forcing Rich output even in non-interactive terminals
   if os.environ.get('FORCE_RICH_UI', '').lower() in ('1', 'true'):
       console = Console(force_terminal=True)
   ```

3. **Use `Console.print()` with `flush=True`** for all status output

### Phase 2: Improve RichUI Class

**File:** `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/ui.py`

1. **Add spinner animation per provider**
   ```python
   from rich.spinner import Spinner
   from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
   ```

2. **Enhanced status table layout**
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │                     🔬 Research in Progress                      │
   ├─────────────────────────────────────────────────────────────────┤
   │  Provider   │  Phase        │  Status                │  Time    │
   │─────────────│───────────────│────────────────────────│──────────│
   │  ⣾ Claude   │  Thinking     │  Extended reasoning... │  2m 15s  │
   │  ⣷ OpenAI   │  Researching  │  Searching web...      │  3m 42s  │
   │  ✓ Gemini   │  Completed    │  Done                  │  5m 10s  │
   ├─────────────────────────────────────────────────────────────────┤
   │  Overall: 2/3 complete │ Elapsed: 5m 10s │ Est. remaining: ~2m  │
   └─────────────────────────────────────────────────────────────────┘
   ```

3. **Progress bar for polling operations**
   - OpenAI and Gemini use polling; show indeterminate progress during poll cycles
   - Update every 5 seconds with poll count

4. **Phase-specific icons**
   ```python
   PHASE_ICONS = {
       ProviderPhase.INITIALIZING: "⏳",
       ProviderPhase.CONNECTING: "🔌",
       ProviderPhase.THINKING: "🧠",
       ProviderPhase.RESEARCHING: "🔍",
       ProviderPhase.POLLING: "⏱️",
       ProviderPhase.PROCESSING: "⚙️",
       ProviderPhase.COMPLETED: "✓",
       ProviderPhase.FAILED: "✗",
   }
   ```

### Phase 3: Add Streaming Progress Mode (Fallback)

For non-interactive terminals where Rich Live won't work:

**New class: `StreamingUI`**

```python
class StreamingUI:
    """Line-by-line progress output for piped/captured contexts."""

    def update_provider(self, provider: str, phase: ProviderPhase, message: str):
        # Each update is a new line, immediately flushed
        icon = PHASE_ICONS.get(phase, "•")
        elapsed = self._format_elapsed(provider)
        print(f"[{provider.upper():8}] {icon} {phase.value:12} │ {message[:40]:40} │ {elapsed}", flush=True)
```

This ensures visibility even when Rich's Live display can't function.

### Phase 4: Enhanced Summary Display

After research completes, show a rich summary panel:

```
╭──────────────────────────────────────────────────────────────────╮
│                    ✅ Research Complete                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 Results Summary                                              │
│  ────────────────                                                │
│  ✓ Claude    4m 20s   Success   ~3,200 words                    │
│  ✗ OpenAI   12m 05s   Timeout   (exceeded 720s limit)           │
│  ✓ Gemini    8m 15s   Success   ~2,800 words                    │
│                                                                  │
│  📁 Output Files                                                 │
│  ────────────────                                                │
│  • reports/research-claude-20260118-143052.md                   │
│  • reports/research-gemini-20260118-143052.md                   │
│                                                                  │
│  ⏱️  Total Duration: 12m 05s                                     │
│  📝 Combined Output: ~6,000 words                                │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯
```

### Phase 5: Update Skill to Enable Rich Output

**File:** `plugins/personal-plugin/skills/research-topic/SKILL.md`

Modify the bash command invocation:

```bash
# Force Rich UI and unbuffered output
PYTHONUNBUFFERED=1 FORCE_RICH_UI=1 PYTHONPATH="$TOOL_SRC" python -u -m research_orchestrator execute ...
```

The `-u` flag forces unbuffered stdout/stderr.

### Phase 6: Increase Timeout to 30 Minutes

**Current:** 720 seconds (12 minutes)
**New:** 1800 seconds (30 minutes)

Deep research APIs (especially OpenAI's o3 and Gemini's deep-research) can take significant time for comprehensive queries. The current 12-minute timeout caused OpenAI to fail in the dry eye research.

**Files to update:**

1. **CLI default** — `cli.py` line ~65: `--timeout` default value
2. **Skill documentation** — `SKILL.md`: Update timeout references
3. **Provider polling** — Verify providers respect the passed timeout

```python
# cli.py execute_parser
execute_parser.add_argument(
    "--timeout",
    type=float,
    default=1800.0,  # Changed from 720.0
    help="Timeout per provider in seconds (default: 1800 = 30 minutes)",
)
```

## Files to Modify

| File | Changes |
|------|---------|
| `tools/research-orchestrator/src/research_orchestrator/ui.py` | Enhanced RichUI, new StreamingUI, icons, spinners |
| `tools/research-orchestrator/src/research_orchestrator/cli.py` | Unbuffered output, force_terminal option, UI selection logic, **timeout default 720→1800** |
| `tools/research-orchestrator/src/research_orchestrator/models.py` | Add word count to ProviderResult (optional) |
| `tools/research-orchestrator/src/research_orchestrator/providers/*.py` | Verify timeout is passed through to API calls |
| `skills/research-topic/SKILL.md` | Update bash invocation with env vars, **update timeout documentation** |

## Testing Plan

1. **Standalone terminal test**
   ```bash
   cd plugins/personal-plugin/tools/research-orchestrator
   PYTHONPATH=src python -m research_orchestrator execute -p "test prompt" --sources claude --depth brief
   ```
   Expected: Beautiful Rich UI with live updates

2. **Piped output test**
   ```bash
   PYTHONPATH=src python -m research_orchestrator execute -p "test" --sources claude --depth brief | cat
   ```
   Expected: StreamingUI fallback with line-by-line updates

3. **Claude Code integration test**
   - Run `/research-topic test --depth brief --sources claude`
   - Expected: Real-time progress visible in Claude Code terminal

## Estimated Effort

| Phase | Effort | Description |
|-------|--------|-------------|
| Investigation | 15 min | Verify current behavior, identify root cause |
| Phase 1 | 30 min | Fix buffering, add force options |
| Phase 2 | 45 min | Enhance RichUI with spinners, icons, layout |
| Phase 3 | 30 min | Implement StreamingUI fallback |
| Phase 4 | 20 min | Enhanced summary panel |
| Phase 5 | 10 min | Update skill invocation |
| Phase 6 | 15 min | Change timeout to 30 minutes across all files |
| Testing | 20 min | All three test scenarios |
| **Total** | ~3 hours | |

## Success Criteria

- [ ] User sees real-time status updates during research execution
- [ ] Spinner/animation visible for active providers
- [ ] Clear phase progression shown (Connecting → Thinking → Researching → etc.)
- [ ] Beautiful formatted summary at completion
- [ ] Works identically in Claude Code and standalone terminal
- [ ] Graceful fallback when Rich unavailable
- [ ] **Default timeout is 30 minutes (1800s)** — prevents premature timeouts on comprehensive research

## Open Questions

1. **Should we add ETA estimation?** — Based on depth level and historical timing
2. **Word count during execution?** — Would require streaming response parsing
3. **Sound notification on completion?** — Terminal bell (`\a`) for long-running research?

---

**Ready for implementation upon approval.**
