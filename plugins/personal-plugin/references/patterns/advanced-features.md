# Advanced Frontmatter Features

Reference for modern Claude Code skill/command frontmatter fields added in late 2025. Each section covers syntax, use case, and gotchas. This is the canonical reference linked from `/new-skill` and `/new-command`.

---

## `context: fork`

**Syntax:**
```yaml
context: fork
```

**What it does:** Spawns an isolated subagent with no access to the parent conversation history. The parent skill waits for the subagent to complete, then reads its output (typically a file written by the subagent).

**When to use:**
- Analysis phases that are noisy/long and would pollute the main conversation
- Any step where you want a "clean slate" context to avoid prior context bias
- Parallelism: multiple `context: fork` dispatches can run concurrently

**Gotcha:** The forked subagent has no conversation history. Pass all context explicitly in the prompt body or via `` !`cmd` `` injection. The subagent cannot ask clarifying questions — it must be self-contained.

---

## `agent:`

**Syntax:**
```yaml
agent: Explore        # or: Think | Code | solutions-architect | etc.
```

**What it does:** Selects the subagent capability profile. Only meaningful with `context: fork`.

| Value | Profile | Best for |
|-------|---------|---------|
| `Explore` | Broad read-only analysis | Codebase surveys, architecture review, recon |
| `Think` | Deep reasoning, extended thinking | Trade-off analysis, design decisions |
| `Code` | Implementation focus | Writing/editing code, refactoring |
| Role strings | Domain-specific (e.g., `security-architect`) | Specialized review roles |

**When to use:** Match the agent to the phase. Analysis phases → `Explore`. Generation phases → `Code`. Decision phases → `Think`.

**Gotcha:** `agent:` without `context: fork` is a no-op.

---

## `model:`

**Syntax:**
```yaml
model: claude-opus-4
```

**What it does:** Overrides the model used for this skill's execution. Useful for routing expensive skills to more capable models, or cheap/fast skills to smaller models.

**When to use:**
- High-stakes analysis: override to `claude-opus-4`
- High-volume/fast utility skills: override to `claude-haiku-4`

**Gotcha:** Model availability depends on the user's subscription. Skills with model overrides may fail for users without access to the specified model. Prefer omitting and letting the user's configured model handle it unless the use case demands a specific model.

---

## `isolation: worktree`

**Syntax:**
```yaml
isolation: worktree
```

**What it does:** Creates a git worktree for the skill run. All file writes happen in the worktree. If the skill exits without changes, the worktree is auto-cleaned up. If changes were made, the worktree is available for review/merge.

**When to use:**
- Skills that write files where concurrent runs would conflict
- Multi-agent parallel dispatch where each subagent needs its own working tree
- Skills that should stage changes for review rather than writing directly to the working copy

**Gotcha:** Worktrees require a clean-ish HEAD. Skills invoking `isolation: worktree` will fail in repos with staged conflicts. Document this precondition in the skill body.

**Worktree naming:** Claude Code generates a name from the skill name + run timestamp. To use a specific name (e.g., per-phase worktrees in implement-plan): `isolation: worktree phase-2`.

---

## `paths:`

**Syntax:**
```yaml
paths:
  - "**/*.spec.ts"
  - "package.json"
  - "config/**/*.yaml"
```

**What it does:** Auto-activates the skill when the user opens or saves a file matching one of the glob patterns. No manual invocation needed.

**When to use:**
- Validation skills that should run whenever a schema/config changes
- Audit skills triggered by baseline file modifications
- Auto-documentation that updates when source files change

**Gotcha — infinite loop:** If the skill writes to a file that matches its own `paths:` pattern, it re-triggers itself. **Always add a loop guard at skill entry:**

```
Entry guard: Check for a sentinel file at `.tmp/[skill-name].last-run`.
If it was written within the last 5 minutes → exit immediately (self-triggered re-entry).
Otherwise: write sentinel `echo $(date +%s) > .tmp/[skill-name].last-run` and proceed.
```

**Gotcha — breadth:** Broad globs like `**/*.md` will fire frequently. Scope patterns tightly to the specific files that require the skill's response. Consider a user-confirmation prompt for expensive skills.

---

## Dynamic Context Injection: `` !`cmd` ``

**Syntax:**
```
!`git status -s`
!`cat config/schema.json | python -m json.tool | head -50`
```

Place at the top of the skill body (before any instructions). The output is spliced into the prompt before Claude reads it.

**What it does:** Runs a shell command and injects its stdout directly into the prompt. Claude sees the output as part of the prompt text — it is not a tool call.

**When to use:**
- Pre-loading expensive but stable data (git log, file lists, env vars)
- Avoiding redundant tool calls mid-skill (inject once, reference multiple times)
- Passing structured data to forked subagents without disk roundtrips

**Gotcha — runs before Claude:** `` !`cmd` `` commands execute before any LLM call. They cannot be conditional on Claude's analysis. Put unconditional, fast, read-only commands here. Avoid writes or commands with side effects.

**Gotcha — failure is silent:** If the command fails (non-zero exit), the output is empty — no error is surfaced to Claude. Wrap with `|| echo "COMMAND FAILED"` if failure matters.

---

## `$ARGUMENTS` and `$CLAUDE_CONTEXT`

**Syntax:** Use directly in skill body text.

```
User provided: $ARGUMENTS
Active file: $CLAUDE_CONTEXT
```

| Variable | Contains |
|----------|---------|
| `$ARGUMENTS` | Raw string the user passed when invoking the skill |
| `$CLAUDE_CONTEXT` | The file path or selected text in the user's editor (if any) |

**When to use:** Any skill that should behave differently based on user arguments or the currently active file.

**Gotcha:** `$CLAUDE_CONTEXT` is empty when the skill is invoked from the terminal without an active editor context. Skills relying on it should have a fallback prompt asking the user for the file path.

---

## `hooks:`

**Syntax:**
```yaml
hooks:
  pre:  "npm run build"
  post: "rm -rf .tmp/skill-scratch/"
```

**What it does:** Runs shell commands before (`pre`) or after (`post`) the skill executes.

**When to use:**
- `pre`: ensure prerequisites (build, compile, fetch data)
- `post`: cleanup (temp files, worktrees, sentinels)

**Gotcha:** Hook failures block the skill (for `pre`) or are logged silently (for `post`). Keep hooks fast and idempotent.

---

## `shell:`

**Syntax:**
```yaml
shell: bash    # or: zsh | sh
```

**What it does:** Overrides the shell used for Bash tool calls within this skill.

**When to use:** Skills that use bash-specific syntax (arrays, process substitution) or zsh-specific features. Most skills can omit this and use the system default.

---

## Feature Interaction Matrix

| Feature | Works with | Incompatible with | Notes |
|---------|------------|-------------------|-------|
| `context: fork` | `agent:`, `isolation: worktree` | — | Core parallelism primitive |
| `agent:` | `context: fork` | Standalone (no-op) | Always pair with fork |
| `isolation: worktree` | `context: fork` | Repos with staged conflicts | Auto-cleanup when no changes |
| `paths:` | Any | Itself (loop) | Loop guard required |
| `` !`cmd` `` | Any | Conditional logic | Runs unconditionally |
| `model:` | Any | User subscription limits | Graceful fallback recommended |

---

*Referenced from: `commands/new-skill.md`, `commands/new-command.md`*
*See also: `references/templates/skill.md` (generated template), `references/templates/*.md` (pattern-specific templates)*
