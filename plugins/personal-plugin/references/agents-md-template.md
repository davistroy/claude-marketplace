# AGENTS.md Template

**Purpose:** Generate an AGENTS.md file alongside implementation plans for cross-tool compatibility (Codex, Cursor, Aider, Windsurf). AGENTS.md provides project context that any AI coding tool can consume, complementing Claude Code's CLAUDE.md.

**When to generate:** Offered by `/create-plan` and `/plan-improvements` when no AGENTS.md exists in the repo root.

---

## Template

```markdown
# AGENTS.md

## Project Overview

[One-paragraph project description. Extract from CLAUDE.md "Project Overview" section or generate from codebase reconnaissance.]

## Tech Stack

- **Language:** [Primary language(s)]
- **Framework:** [Key frameworks]
- **Build:** [Build tool and command]
- **Test:** [Test framework and command]
- **Lint:** [Linter and command]

## Key Conventions

[3-7 bullet points covering the most important project conventions. Extract from CLAUDE.md — focus on conventions that affect code generation: naming patterns, file organization, import style, error handling approach.]

## Build & Test Commands

| Task | Command |
|------|---------|
| Install dependencies | `[command]` |
| Run tests | `[command]` |
| Run linter | `[command]` |
| Type check | `[command]` |
| Build | `[command]` |

## Architecture Notes

[2-3 sentences about the project's architecture that any AI tool should know. High-level component relationships, key design decisions, data flow patterns.]

## Working with This Project

[Guidance for AI tools: what to read first, what conventions to follow, what to avoid. Keep tool-agnostic — no Claude-specific instructions.]
```

---

## Generation Rules

1. **Extract, don't duplicate.** Pull relevant sections from CLAUDE.md and codebase reconnaissance — don't copy CLAUDE.md verbatim. AGENTS.md should be 30-50 lines, not a CLAUDE.md mirror.
2. **Tool-agnostic.** No Claude Code-specific features (skills, commands, hooks). Focus on universal project context.
3. **Keep it fresh.** AGENTS.md can become stale. Include a comment at the bottom: `<!-- Generated from CLAUDE.md and codebase analysis on [date]. Regenerate with /create-plan or /plan-improvements. -->`
4. **Don't overwrite.** If AGENTS.md exists, never overwrite — the user may have customized it.
