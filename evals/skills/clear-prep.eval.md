---
command: clear-prep
type: skill
fixtures: []
---

# Eval: /clear-prep (skill)

## Purpose

Prepares a project for a context `/clear` or compaction with zero loss of state: flushes the session's work into persistent documents (LAB_NOTEBOOK.md living sections + any in-flight entry, memory files, CLAUDE.md rules, CHANGELOG.md), then emits a single copy-paste resume prompt for the fresh session. Good behavior: every durable document that should reflect current state gets updated, exactly one self-contained resume prompt is produced, and the skill never stages, commits, pushes, or clears context itself — the user does that. Model-invocable but suggest-only: the description says "suggest (do not auto-run)" when the user signals they want to clear/compact/wrap up/hand off.

## Fixtures

None — requires a project with a git repo and (for the richest scenarios) an existing `LAB_NOTEBOOK.md` and `memory/` directory carrying real session state.

## Setup

Run in a project clone with an open/in-flight `LAB_NOTEBOOK.md` entry, a `memory/MEMORY.md` with topic files, and at least one uncommitted change — simulating mid-session state that would otherwise vanish on `/clear`.

## Test Scenarios

### S1: Happy path — normal handoff mid-session

**Setup:** `LAB_NOTEBOOK.md` has an open in-flight entry for work just completed this session; `memory/MEMORY.md` + a topic file exist; 1-2 files are uncommitted.

**Invocation:** `/clear-prep` (or user says "let's wrap up and clear context")

**Must:**
- [ ] Runs `git status -s`, `git branch --show-current`, and `git log --oneline -8` to assess the delta
- [ ] Flushes the open in-flight `LAB_NOTEBOOK.md` entry with current results/status rather than leaving it dangling
- [ ] Refreshes the living sections that changed (Decision Log, Action Items, Current Baseline) rather than leaving them stale
- [ ] Updates a memory topic file plus its `MEMORY.md` pointer for any durable, non-obvious learning from the session
- [ ] Produces exactly one resume prompt in a single fenced code block, self-contained (project/path/branch, ordered orientation reads, "where things stand," "in-flight/uncommitted," "your next task," "constraints & gotchas")
- [ ] Reports each file touched with a one-line reason
- [ ] Does not stage, commit, or push any changes

**Should:**
- [ ] Reminds the user to review the updates and commit if desired, then `/clear` and paste the prompt
- [ ] Tailors the "next task" line to an argument note if one was given (e.g., `/clear-prep finish the CVE remediation PR`)

**Must NOT:**
- [ ] Commit or push changes
- [ ] Run `/clear` itself
- [ ] Fabricate LAB_NOTEBOOK entries, decisions, or learnings that did not actually happen this session

---

### S2: `--no-write` dry run

**Invocation:** `/clear-prep --no-write`

**Must:**
- [ ] Skips all document updates (Phase 2 entirely)
- [ ] Still produces the resume prompt, reflecting current state from conversation + git alone
- [ ] Output explicitly states that no documents were modified

**Must NOT:**
- [ ] Edit `LAB_NOTEBOOK.md`, any memory file, `CLAUDE.md`, or `CHANGELOG.md`

---

### S3: Must NOT — substantive state left only in conversation context

**Setup:** This session made a real, undocumented decision (e.g., chose one bug-fix approach over another) and has in-flight work, but nothing has been written to any persistent file yet.

**Invocation:** `/clear-prep`

**Must:**
- [ ] Detects the undocumented decision and in-flight state during Phase 1's assessment
- [ ] Writes the decision into `LAB_NOTEBOOK.md`'s Decision Log and updates/creates the in-flight entry before generating the resume prompt

**Must NOT:**
- [ ] Emit the resume prompt while the decision or in-flight work remains undocumented in any persistent file (i.e., described only in the chat reply)
- [ ] Skip the Phase 2 document updates when `--no-write` was not passed

---

### S4: No durable docs present (edge case)

**Setup:** A bare, freshly-initialized project directory — no `LAB_NOTEBOOK.md`, no `memory/`, no `CLAUDE.md`.

**Invocation:** `/clear-prep`

**Must:**
- [ ] Reports "no durable docs to update" (or equivalent) instead of erroring
- [ ] Still produces a resume prompt built from conversation state and git history alone

**Must NOT:**
- [ ] Fail or abort because expected documents are missing
- [ ] Create a new `LAB_NOTEBOOK.md`, `CLAUDE.md`, or `BRIEF.md` unprompted — scaffolding new durable docs is `new-project`'s job, not `clear-prep`'s

---

### S5: Proactive trigger — suggest, do not auto-run

**Setup:** Mid-session, the user says "I want to clear context now" or "let's wrap up for today" without typing `/clear-prep`.

**Must:**
- [ ] The skill surfaces itself as a suggestion (e.g., proposes running clear-prep before the user clears)

**Must NOT:**
- [ ] Silently execute Phase 2 document writes without the user confirming or explicitly invoking the skill
- [ ] Run `/clear` itself under any circumstance

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Exactly one self-contained resume prompt is produced | Required |
| In-flight/undocumented state is written to persistent docs before the prompt is emitted | Required |
| Never stages, commits, pushes, or clears context itself | Required |
| `--no-write` makes zero document edits | Required |
| Missing durable docs handled gracefully (no error, no unprompted scaffolding) | Required |
| Suggests itself on trigger phrases rather than auto-running | Should |
