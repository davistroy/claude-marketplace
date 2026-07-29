---
name: clear-prep
description: Prepare a project for a context clear (/clear) or compaction with zero loss of state. Flushes the current session's work into all persistent documents — LAB_NOTEBOOK.md living sections and in-flight entry, memory files, CLAUDE.md rules, CHANGELOG — then emits a single copy-paste resume prompt to run in the fresh session so a zero-context Claude picks up exactly where you left off. Suggest (do not auto-run) when the user says they want to clear context, compact, wrap up the session, or hand off.
effort: medium
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
---

# Clear Prep

Prepare the project to survive a context reset. When you are about to run `/clear` (or a compaction is imminent), the volatile session state — what you just did, what is half-done, what the next step is — lives only in conversation context and is lost the moment context clears. This skill persists that state into the project's durable documents, then hands you a ready-to-paste **resume prompt** so the next session continues seamlessly.

Two guarantees:
1. **Nothing in-flight is lost** — every persistent document that should reflect the current state is updated before you clear.
2. **The next session starts oriented** — the resume prompt tells a zero-context Claude exactly what to read, where things stand, and what to do next.

**This skill writes only to documentation/state files (all git-recoverable). It does NOT commit, push, or clear context — you do that.**

## Input

**Arguments:** `$ARGUMENTS`

Optional:
- A short note on the intended next task (e.g., `finish the CVE remediation PR`) — sharpens the "next task" line in the resume prompt.
- `--no-write` — skip document updates; only generate the resume prompt from current state (dry-run / read-only).

Dynamic context available:
- `` !`git status -s 2>/dev/null || echo "(not a git repository)"` `` — uncommitted changes
- `` !`git log --oneline -8 2>/dev/null || echo "(not a git repository)"` `` — recent commits
- `` !`git branch --show-current 2>/dev/null || echo "(not a git repository)"` `` — active branch

## Instructions

Execute the phases in order. Phase 2 is skipped when `--no-write` is passed.

### Phase 1: Assess Session State

Reconstruct what this session actually changed and what remains open. Gather:

1. **Git delta** — run `git status -s`, `git branch --show-current`, and `git log --oneline -8`. Identify: uncommitted/untracked files, current branch, whether work has been committed or is still loose in the working tree.
2. **What was done this session** — from the conversation, summarize the concrete work: decisions made, files created/edited, problems solved, experiments run. Be specific (files, versions, PR numbers), not vague.
3. **What is in-flight** — anything half-finished: a partially written function, an unmerged PR, a plan phase mid-execution, an unanswered question, a failing test.
4. **The single next action** — the one most important thing the next session should do first. Prefer the argument note if the user gave one.
5. **Orientation surface** — detect which durable documents this project uses so the resume prompt can point at them:
   - `LAB_NOTEBOOK.md` (Decision Log, Open Action Items, most recent entry, Current Baseline)
   - `memory/MEMORY.md` and its topic files (locate the memory dir; on this repo it is `<repo>/memory/` or the per-project `~/.claude/projects/.../memory/`)
   - `CLAUDE.md`, `IMPLEMENTATION_PLAN.md`, `CHANGELOG.md`, `README.md`, `BRIEF.md`, `docs/`

### Phase 2: Update All Documents (skip on `--no-write`)

Persist the session state into the durable documents. Only touch what genuinely changed — never fabricate entries to look busy.

1. **LAB_NOTEBOOK.md** (if present — this project mandates it):
   - **Flush any in-flight entry.** If the session opened an entry that is not yet closed, update it with current results/status per the notebook's logging rules. This is the notebook's Rule 6 ("Write Before Risky Operations") — a context clear is exactly such an operation. If substantive work happened with no entry, add one now (Objective / what was done / Status).
   - **Refresh living sections** so they reflect reality: **Decision Log** (add new decisions, mark superseded), **Action Items** (add follow-ups, check off completed), and **Current Baseline** (correct any stale version numbers, git state, or measurements — verify against `origin/main`, never trust local HEAD alone).
2. **Memory** (if a memory dir + `MEMORY.md` exist): capture any durable, non-obvious learning from this session per the project's learning-capture protocol — write/update the topic file, add the one-line pointer to `MEMORY.md`. Do not record what code or git history already captures.
3. **CLAUDE.md**: if a new *verified operational rule* emerged this session, add/update the relevant bullet. Do not churn it otherwise.
4. **CHANGELOG.md**: if a version shipped or is staged, ensure its section is accurate.
5. **Other project docs**: update `IMPLEMENTATION_PLAN.md` progress markers, `README`, `BRIEF.md`, or a `TODO`/`PROGRESS` file if the session changed their truth.

Report each file touched and the one-line reason. **Do not stage, commit, or push** — leave that to the user. If the working tree is dirty, that fact goes into the resume prompt (below) rather than being silently committed.

### Phase 3: Generate the Resume Prompt

Emit a single fenced block the user can copy verbatim into the fresh session after `/clear`. It must be self-contained — assume the reader has zero prior context. Use this shape:

```text
Resume work on <project> at <repo path> (branch <branch>).

Read first, in this order:
1. <orientation file> — <what to extract from it>
2. <orientation file> — <what to extract from it>
3. Run `git log --oneline -5` and `git status -s` for current state.

Where things stand:
<2-4 sentences: what was just completed, current versions/state>

In-flight / uncommitted:
<anything half-done or not yet committed; "working tree clean, all committed" if so>

Your next task:
<the single most important, specific, actionable next step>

Constraints & gotchas:
<project-specific rules the next session must honor — e.g. mandatory LAB_NOTEBOOK logging before any change; version source of truth is origin/main>
```

Tailor every line to the actual project. For a project with a `LAB_NOTEBOOK.md`, the first orientation step is always "read the Decision Log and Open Action Items tables plus the latest entry." Where the project has a `prime`-style skill, you may point the next session at it, but still include the concrete next task so it does not have to re-derive it.

## Output

1. A short summary of documents updated (file → reason), or "no document changes needed" / "`--no-write`: skipped".
2. The resume prompt in a single copy-paste code block.
3. A one-line reminder: review the updates, commit if desired, then run `/clear` and paste the resume prompt.

## Example

```
User: /clear-prep finish the CVE remediation PR

Claude: Updated:
  - LAB_NOTEBOOK.md — closed Entry 013 (PR #99 status), refreshed Current Baseline versions
  - memory/marketplace-learnings.md — added markdownlint MD012 EOF gotcha + MEMORY.md pointer

Resume prompt (copy after /clear):
```text
Resume work on claude-marketplace at /home/davistroy/dev/personal/claude-marketplace (branch main).

Read first, in this order:
1. LAB_NOTEBOOK.md — Decision Log, Open Action Items, and Entry 013 (most recent).
2. memory/MEMORY.md — project memory index.
3. Run `git log --oneline -5` and `git status -s`.

Where things stand:
personal-plugin is at 10.2.0, marketplace 3.3.0. CVE remediation lockfiles regenerated on
branch fix/dependency-cves-2026-07; PR #99 open, CI green on both OSes.

In-flight / uncommitted:
Working tree clean; PR #99 awaiting squash-merge.

Your next task:
Squash-merge PR #99, then verify open high-severity Dependabot alerts drop to 0.

Constraints & gotchas:
LAB_NOTEBOOK logging is a blocking precondition before any change. Version source of
truth is origin/main — git fetch before trusting local state.
```
Review, commit if desired, then /clear and paste the prompt above.
```

## Error Handling

- **Not a git repo:** skip git-delta steps; reconstruct session state from the conversation and file mtimes; still produce the resume prompt.
- **No LAB_NOTEBOOK/memory/CLAUDE.md:** update whatever durable docs exist (README, TODO, plan); if none, note "no durable docs to update" and produce the resume prompt from conversation state alone — the prompt is still the primary deliverable.
- **Nothing changed this session:** say so; still emit a resume prompt that orients the next session to current state and open action items.
- **Uncommitted work present:** never auto-commit; surface it in the resume prompt's "In-flight / uncommitted" section so it is not lost or accidentally clobbered.
- **`--no-write`:** produce only the resume prompt; make clear no documents were modified.
