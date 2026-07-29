# Common Command Patterns

This document serves as an index to the modular pattern files. Each pattern area has been split into a focused document for maintainability.

## Pattern Files

| Pattern File | Description | Key Content |
|--------------|-------------|-------------|
| [naming.md](patterns/naming.md) | File and command naming | Timestamp format, output file naming, type prefixes |
| [validation.md](patterns/validation.md) | Input validation and error handling | Error message formats, schema validation, dependency checks |
| [output.md](patterns/output.md) | Output files, directories, preview | Directory auto-creation, preview mode, completion summaries |
| [workflow.md](patterns/workflow.md) | State management, resume, sessions | Resume detection, session commands, multi-phase workflows |
| [testing.md](patterns/testing.md) | Argument testing, dry-run | Test categories, dry-run pattern, test checklist |
| [logging.md](patterns/logging.md) | Audit logging, progress reporting | Audit log format, performance documentation |
| [anti-patterns.md](anti-patterns.md) | Planning & implementation anti-patterns | Symptom patching, scope creep, placeholder pollution, untestable criteria |
| [hooks/](hooks/) | Hook recipe examples | Planning stop warning, post-edit verification, session start primer |

## Quick Reference

### Timestamp Format
`YYYYMMDD-HHMMSS` (e.g., `20260114-143052`)

See: [patterns/naming.md](patterns/naming.md)

### Output File Naming
`[type]-[source]-[timestamp].[ext]`

See: [patterns/naming.md](patterns/naming.md)

### Output Locations

| Output Type | Directory |
|-------------|-----------|
| Analysis reports | `reports/` |
| Reference data (JSON) | `reference/` |
| Generated documents | Same as source |
| Temporary files | `.tmp/` |

See: [patterns/naming.md](patterns/naming.md)

### Directory Auto-Creation

```bash
mkdir -p reports/  # or reference/, .tmp/, etc.
```

See: [patterns/output.md](patterns/output.md)

### Error Message Format

```
Error: [Brief description]

Expected: [What was expected]
Received: [What was provided]

Suggestion: [How to fix]
```

See: [patterns/validation.md](patterns/validation.md)

### Issue Severity Levels

| Severity | Label | Action Required |
|----------|-------|-----------------|
| **CRITICAL** | Must fix | Immediate |
| **WARNING** | Should fix | Before merge |
| **SUGGESTION** | Nice to have | At discretion |

See: [patterns/validation.md](patterns/validation.md)

### Session Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `help` | `?`, `commands` | Show available commands |
| `status` | `progress` | Show progress |
| `back` | `previous`, `prev` | Previous item |
| `skip` | `next`, `pass` | Skip current item |
| `quit` | `exit`, `stop` | Exit with save prompt |

See: [patterns/workflow.md](patterns/workflow.md)

### Completion Summary Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Command Name] Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Summary:**
- [Metric 1]: [Value]

**Output:**
- [File path]

**Next Steps:**
- [Suggestion]
```

See: [patterns/output.md](patterns/output.md)

## Usage in Commands

When creating or updating commands, reference specific pattern files:

```markdown
See `references/patterns/validation.md` for error message format.
See `references/patterns/workflow.md` for session commands.
```

## Pattern File Maintenance

When updating patterns:
1. Edit the specific pattern file, not this index
2. Update this index only if adding new pattern files
3. Ensure templates reference specific pattern files
4. Test that all links work correctly

---

## Advanced Features — Modern Frontmatter Field Catalog

Canonical reference for late-2025 Claude Code features. `new-skill.md` links here for full field documentation.

### `context: fork`

**Syntax:**
```yaml
context: fork
```
Used inside a Task dispatch block, not in the skill's own frontmatter.

**Use case:** Spawns an isolated subagent with its own conversation context. The subagent cannot read or write the parent's conversation history. Ideal for analysis phases (read-only exploration), parallel scanning tiers, or any work that doesn't need to report back interactively.

**Gotchas:**
- The forked context has no memory of prior conversation turns — pass all needed information explicitly in the prompt.
- Forked subagents cannot call back into the parent mid-run; use output files or return values for hand-off.
- Do NOT fork synthesis/aggregation steps — those need the full parent context.

---

### `agent:`

**Syntax:**
```yaml
agent: Explore          # or: software-engineer, solutions-architect, data-architect,
                        #     integration-architect, performance-engineer, qa-architect,
                        #     security-architect, platform-engineer, risk-compliance
```

**Use case:** Selects the subagent persona/specialization for a Task dispatch. Pair with `context: fork` for analysis roles. Use domain-specific types (e.g., `security-architect`) in multi-agent orchestration to improve role separation.

**Gotchas:**
- `Explore` is the generic read-only agent; use named roles when domain framing matters.
- Unrecognized agent types raise a validation error during skill load — verify the type string is one of `Explore | Plan | general-purpose` or a custom named agent file. See ADR-0005 for custom agent dispatch.

---

### `model:`

**Syntax:**
```yaml
model: opus             # tier alias: haiku | sonnet | opus | fable
```

**Use case:** Override the default model for a skill or subagent dispatch. Useful for routing cheap triage steps to Haiku and expensive synthesis to Opus.

**Gotchas:**
- Always use tier aliases (`haiku`, `sonnet`, `opus`, `fable`), never pinned model IDs (ADR-0005). Tier aliases resolve at dispatch time, preventing silent staleness when models are retired or upgraded.
- Overriding in a subagent Task prompt takes precedence over frontmatter.

---

### `paths:`

**Syntax:**
```yaml
paths:
  - "package.json"
  - "pyproject.toml"
  - "src/**/*.ts"
  - "*_BASELINE.md"
```

**Use case:** A conditional **load gate**, not a save-trigger. A skill declaring `paths:` is invisible — to Claude and to a user typing its slash command alike — until Claude's own Read, Edit, or Write tool call touches a file whose relative path matches one of the patterns during that session. From that point on it is loaded like any other skill for the rest of the session. Nothing runs automatically; activation only makes the skill *findable*, it does not invoke it. See [ADR-0012](../../../docs/adr/0012-artifact-derived-documentation.md) for the harness internals this is derived from.

**Gotchas:**
- **No loop guard needed.** Activation is one-shot per session — the harness records the skill's name as activated and never re-processes it, so a skill that later writes a file matching its own `paths:` pattern triggers nothing further. A "check if this ran in the last 5 minutes" guard defends against a state transition the harness cannot produce; do not add one.
- Glob syntax follows `.gitignore` conventions. Double-star `**` matches across directories.
- Not a filesystem watcher: a file changed by git, another process, or a human editing outside the session activates nothing. Only Claude's own in-session Read/Edit/Write calls count.
- Pairing `paths:` with `disable-model-invocation: true` is usually wrong: since the skill doesn't exist to the lookup until Claude itself touches a matching file, and `disable-model-invocation: true` means Claude can never invoke it either way, the combination can leave a nominally user-invocable skill unreachable by the user on a fresh session — see ADR-0012 F4.

---

### `isolation:` — not a skill frontmatter field

`isolation: worktree` (temporary git worktree) and `isolation: remote` (remote sandbox) are real Claude Code features — but they belong to **agent** frontmatter (`.claude/agents/*.md`) and the `Agent` tool call, never to a `SKILL.md` file. The skill frontmatter schema is `.strict()`: an unrecognized key like `isolation:` fails validation and the skill is silently dropped from the skill list (logged internally as a YAML-frontmatter parse failure — no session crash, the skill just never loads). To isolate a subagent's execution scope from a skill body, dispatch it via the `Agent` tool with `isolation: "worktree"` as a call parameter, or define a custom agent file with `isolation: worktree` in its own frontmatter — do not add `isolation:` to the skill's own frontmatter.

---

### `when_to_use:`

**Syntax:**
```yaml
when_to_use: "Use when starting a new project or after a significant architecture change"
```

**Use case:** Human-readable trigger guidance shown in `/skills` listings. Helps users know when to invoke the skill vs a native command or alternative.

**Gotchas:**
- Keep to one sentence. Verbose `when_to_use` descriptions clutter the skills list.

---

### `hooks:`

**Syntax:**
```yaml
hooks:
  Stop:
    - matcher: any
      hooks:
        - type: command
          command: "bash scripts/cleanup.sh"
          timeout: 5
```

**Use case:** Lifecycle hooks that run at Claude Code events (SessionStart, Stop, PreToolUse, etc.). Hooks fire once per session when their matcher conditions are met. See `hooks/hooks.json` for complete event list and the hook-recipe files in `references/hooks/` for worked examples.

**Gotchas:**
- Hook commands must be fast (<5s) or they block session flow noticeably.
- Do NOT re-declare hooks in `plugin.json` — Claude Code auto-loads `hooks/hooks.json`. Duplicate declarations cause errors.
- The `hooks:` shape is an event-record: keyed by event name → array of matcher-group objects, each with `matcher` and `hooks` array. See the working `hooks/hooks.json` as ground truth.

---

### `shell:`

**Syntax:**
```yaml
shell: bash   # or: zsh, sh, pwsh
```

**Use case:** Specifies the shell for Bash tool invocations within the skill. Default is the user's login shell. Explicit `shell: bash` ensures cross-platform consistency for skills using bash-specific syntax.

**Gotchas:**
- On Windows hosts, `bash` resolves to Git Bash or WSL bash — behavior may differ from Linux.
- `pwsh` (PowerShell 7+) is available on all platforms but has different pipeline semantics.

---

### Dynamic Context Injection — `` !`cmd` ``

**Syntax:**
```markdown
!`git log --oneline -20`
!`cat path/to/file.md`
!`ls -la src/`
```

**Use case:** Runs a shell command and injects its output into the prompt before Claude sees it. Eliminates a round-trip Bash tool call for static pre-loads (git stats, file inventories, config values). Most valuable for information that is cheap to gather and needed immediately at skill start.

**Gotchas:**
- The command runs **before Claude sees any of the prompt** — errors or empty output are injected literally.
- Keep injected commands fast and bounded. `find / -type f` will block skill startup.
- Injected output counts against context length; limit with `head`, `tail`, or line limits.
- Not available inside forked subagent prompts passed as template strings — only in the top-level skill body.

---

### String Substitution Variables

**Syntax:**
```markdown
$ARGUMENTS          # Full argument string passed to the skill/command
$CLAUDE_PLUGIN_ROOT # Absolute path to the plugin directory
```

**Use case:** `$ARGUMENTS` is the primary input variable — it contains everything the user typed after the skill name. Parse it for flags, paths, or free-form input. `$CLAUDE_PLUGIN_ROOT` is essential for referencing bundled tools or reference files without hardcoded paths.

**Gotchas:**
- `$ARGUMENTS` is a raw string — parse flags manually (e.g., check if it contains `--dry-run`) or use a structured intake step.
- Variables are substituted at skill load time, not at runtime — avoid using them in loops or conditionals that expect dynamic values.
- Unset variables expand to empty string (no error); always check before use if the skill depends on them.
