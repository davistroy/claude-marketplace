# Advanced Frontmatter Features

Reference for modern Claude Code skill/command frontmatter fields added in late 2025. Each section covers syntax, use case, and gotchas. This is the canonical reference linked from `/new-skill`.

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

**Gotcha:** The forked subagent has no conversation history. Pass all context explicitly in the prompt body or via `!`cmd`` injection. The subagent cannot ask clarifying questions — it must be self-contained.

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

> **Read [ADR-0012](../../../../docs/adr/0012-artifact-derived-documentation.md) before relying on `paths:` semantics.** The facts below are recovered from the harness's loader and tool-call handlers, not inferred from the key's name.

**Syntax:**
```yaml
paths:
  - "**/*.spec.ts"
  - "package.json"
  - "config/**/*.yaml"
```

**What it does:** Gates the skill's *existence*, not its execution. A skill declaring `paths:` is held out of the normal skill list at load time and is unresolvable by name — to Claude's own Skill tool and to a user typing the slash command alike — until Claude's Read, Edit, or Write tool call touches a file matching one of the patterns in that session. At that point it is added to the available skill set for the rest of the session, exactly as if it had loaded unconditionally from the start. Nothing about the skill's body ever runs automatically; activation only changes whether the skill can be *found*.

**When to use:**
- A model-invocable skill (no `disable-model-invocation: true`) whose relevance only becomes apparent once Claude has touched a specific kind of file this session — e.g., surfacing a dependency-audit skill once Claude has read or edited a manifest (`security-analysis`)
- Not a substitute for direct invocation: a skill meant to be run on demand by a human at any point in a session (including turn one) should omit `paths:` — see the next gotcha

**Gotcha — do not pair with `disable-model-invocation: true`.** `disable-model-invocation: true` means Claude itself can never invoke the skill, only a user can, via its slash command. But `paths:` means the skill does not exist to that same lookup until Claude has already touched a matching file — and a skill Claude is barred from invoking gives Claude no reason to go looking. The combination can make a nominally user-invocable skill unreachable by the user on a fresh session where the trigger file hasn't been touched yet. If the skill is meant for on-demand human invocation, drop `paths:` entirely.

**Gotcha — no loop guard, because there is no re-triggering.** Activation is one-shot per session: once a skill's name is recorded as activated it is never re-evaluated against `paths:` again, so a skill that later writes a file matching its own pattern triggers nothing further. A "have I run in the last 5 minutes" entry guard is defending against a state transition the harness structurally cannot produce — do not add one.

**Gotcha — not a filesystem watcher.** Only Claude's own in-session Read/Edit/Write tool calls feed the gate. A file changed by git, an external editor, or another process activates nothing.

**Gotcha — breadth:** Broad globs like `**/*.md` will match more file touches, activating (making visible) the skill sooner and more often. Scope patterns tightly to the specific files that make the skill relevant.

---

## Dynamic Context Injection: `!`cmd``

> **Read [ADR-0011](../../../../docs/adr/0011-dynamic-injection-doctrine.md) before writing or editing an injection.** Every rule below is derived from the harness internals recorded there, and two of them run opposite to intuition.

**Syntax:** an exclamation mark immediately followed by a backtick-delimited command, at the start of a line or after whitespace — written `!`git status -s`` in a real skill body. Place these at the top of the skill body (before any instructions). The output is spliced into the prompt before Claude reads it.

**What it does:** Runs a shell command and injects its stdout directly into the prompt. Claude sees the output as part of the prompt text — it is not a tool call.

**When to use:**
- Pre-loading expensive but stable data (git log, file lists, env vars)
- Avoiding redundant tool calls mid-skill (inject once, reference multiple times)
- Passing structured data to forked subagents without disk roundtrips

**Gotcha — runs before Claude:** injections execute before any LLM call. They cannot be conditional on Claude's analysis. Put unconditional, fast, read-only commands here. Avoid writes or commands with side effects.

**Gotcha — a non-zero exit aborts skill load.** It does **not** degrade to empty output, and it is not silent. The shell error is thrown, prompt expansion rejects, and the skill never reaches the model at all. Every injection is therefore a load-time precondition: it must exit 0 in *every* directory the skill can be invoked from. Guard anything that can fail and branch on the sentinel in the body:

- `!`git status -s 2>/dev/null || echo "(not a git repository)"``

**Gotcha — it is permission-checked against `allowed-tools`.** A denied command throws the same way a failing one does, with no prompt to the user. Every binary in the pipeline — `git`, `grep`, `awk`, `tail`, … — must appear in the grant set, not just the first one.

**Gotcha — it expands at parse time, before `$ARGUMENTS` exists.** A placeholder meant to be filled from the user's arguments reaches bash literally, so `!`ls -la <target-path>`` exits 2 (a bash syntax error — the angle brackets parse as redirects) in every directory. There is nothing to guard here: delete the injection and invoke the Bash tool from the model with the resolved path instead. See `skills/arch-review/SKILL.md`.

**Gotcha — writing *about* injections executes them, because the escaping rule is inverted.** The harness blanks an inline-code span *unless* the character immediately before its opening backtick is `` ` `` or `!`. So the tidy-looking double-backtick form — the one ordinary markdown convention produces when you escape an example — is **live**, and the ragged nested form is **inert**. Always document the syntax as `!`cmd`` (single backtick, nested). A fenced block opened with three backticks and `!` is live too, and is never pre-passed at all — quoting one inside an example does not make it safe.

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
| `paths:` | Model-invocable skills | `disable-model-invocation: true` (self-cancelling — ADR-0012) | Conditional load gate; no loop guard needed |
| `!`cmd`` | Any | Conditional logic | Runs unconditionally; non-zero exit aborts skill load (ADR-0011) |
| `model:` | Any | User subscription limits | Graceful fallback recommended |

---

*Referenced from: `commands/new-skill.md`*
*See also: `references/templates/skill.md` (generated template), `references/templates/*.md` (pattern-specific templates)*
