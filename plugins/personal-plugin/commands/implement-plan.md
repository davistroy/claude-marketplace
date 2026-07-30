---
description: Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic testing, documentation, and git workflow
argument-hint: "[--input <path>] [--auto-merge] [--pause-between-phases]"
effort: high
allowed-tools: Agent, TaskCreate, TaskUpdate, TaskList, TaskOutput, Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(npx:*), Bash(yarn:*), Bash(pnpm:*), Bash(pytest:*), Bash(python:*), Bash(jest:*), Bash(vitest:*), Bash(bun:*)
---

# Implement Plan Command

Execute an IMPLEMENTATION_PLAN.md file by orchestrating subagents in a loop. Each work item is implemented, tested, documented, and committed by dedicated subagents while the main agent retains only minimal state — preserving context window capacity for long-running plans.

## Input Validation

**Optional Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--input <path>` | `IMPLEMENTATION_PLAN.md` | Plan file path (absolute or relative to repo root). Use when the plan lives at a non-default location. |
| `--auto-merge` | `false` | Merge the PR and clean up the branch after all items complete. Without it, the command creates the PR and stops. |
| `--pause-between-phases` | `false` | Pause and ask for confirmation before starting each new phase. |
| `--progress` | `false` | Update PROGRESS.md even if absent. By default PROGRESS.md is touched only if it already exists (avoids duplicating `git log`). |

**Argument Resolution:** If `--input <path>` was provided, use it (relative paths resolve against the repository root); otherwise default to `IMPLEMENTATION_PLAN.md` in the repository root. Store the result as `PLAN_FILE` and use it for ALL plan-file references below.

**Prerequisites Validation:** verify that `PLAN_FILE` exists at the resolved path; the current branch is NOT main or master; the working directory is clean (no uncommitted changes); and GitHub CLI (`gh`) is authenticated.

**If the plan file is missing:** output an error stating `[PLAN_FILE]` was not found, and suggest `/plan-improvements` (generate from codebase analysis), `/create-plan` (generate from requirements documents), or a custom path via `/implement-plan --input <path-to-plan>`; then stop.

**If on main/master:** output an error that the command cannot run on main/master, and instruct the user to create a feature branch first (`git checkout -b feature/implementation`); then stop.

**If working directory is dirty:** check if `.implement-plan-state.json` exists and contains an `"in_progress"` or `"in_progress_batch"` field.
- **If so** (dirty state likely from an interrupted implementation session): present three options — (1) commit these changes and resume (as `"[X.Y] interrupted work"`), (2) stash these changes and resume, (3) abort to inspect manually first. Wait for the user's choice and execute accordingly before proceeding.
- **If not** (no state file or no IN_PROGRESS item): output the standard error that uncommitted changes must be committed or stashed before running the command; then stop.

See `references/implement-plan-examples.md` for the exact wording of each of these error and prompt messages.

## Overview

This command automates a phased implementation plan: it reads the plan and tracks progress, implements each work item via subagents dispatched by model tier (haiku/sonnet/opus), runs tests and fixes failures, optionally updates PROGRESS.md (if it exists) and LEARNINGS.md (only when tests had issues), captures non-trivial learnings to project memory at phase boundaries, commits after each batch, and creates a PR when complete (merge only with `--auto-merge`).

> **Orchestrator model:** This command (the orchestrator) benefits from running on Opus. It makes tier-assignment decisions, routes escalations, and dispatches sub-agents — a wrong call costs more in re-runs than the orchestrator's token count. The model is determined by the user's session; for complex or large plans, starting a session on Opus before invoking `/implement-plan` is recommended.

**Prerequisites:** a plan file at the expected path (default `IMPLEMENTATION_PLAN.md`, or `--input`); a feature branch (not main/master); a clean working directory; authenticated `gh`. See Input Validation above for the exact checks and error messages.

## Execution Strategy

### Context Window Discipline

**This is the most important principle.** Large plans can span dozens of work items. If the main agent reads files, holds implementation details, or accumulates subagent output, the context window fills up and the agent loses coherence before the plan completes.

**Rules:**

| Do | Do Not |
|----|--------|
| Delegate ALL file reading to subagents | Read the plan file or source files directly |
| Retain only: status, files changed, errors | Ask subagents to return file contents |
| Use `.implement-plan-state.json` as the sole source of truth | Accumulate work item status in conversational memory |
| Use TaskCreate/TaskUpdate for progress tracking (not subagent launching) | Hold work item details in conversational memory |
| Spawn fresh subagents for each step | Reuse subagent context across work items |
| Launch parallel subagents with `run_in_background: true` | Wait for one item to finish before starting an independent one |
| Fold plan-file updates into implementation subagent | Spawn a separate doc subagent for every work item |
| Use a single commit for parallel batches | Create individual commits for each parallel item |
| Shed old subagent summaries every 5 items | Keep all iteration results in conversation history |
| Capture non-trivial learnings to memory files at phase boundaries | Skip memory updates because "context discipline" says to shed state |

### State File (`.implement-plan-state.json`)

The state file is the **ground truth** for execution progress. It persists minimal state between loop iterations so the main agent never needs to re-read the full plan or accumulate conversational history.

**Fields (summary):**

| Field | Type | Purpose |
|-------|------|---------|
| `plan_file` | string | Resolved path to the plan file (`PLAN_FILE`) |
| `plan_identity` | object | Fingerprint of *which plan* this state belongs to — `generated`, `total_phases`, `phase_titles`, `item_ids`. A path is a label; this is the content. See "Plan Identity" below |
| `started_at` | ISO timestamp | When the session began |
| `current_phase` | string | Name of the phase currently executing |
| `current_item` | string \| null | Item number being worked; `null` when a phase just finished |
| `in_progress` | object \| absent | Single item being implemented now (sequential batch); present only between Step 0 and Step 5 |
| `in_progress_batch` | array \| absent | Items being implemented now (parallel batch); present only between Step 0 and Step 5 |
| `completed` | array | Finished items: `{item, phase, description, status, sha, files}` |
| `failed` | array | Failed/skipped items: `{item, phase, description, error, attempts}` |
| `project_context` | object | `project_description`, `tech_stack`, `test_command`, `verification_commands`, `conventions` |
| `project_context.verification_commands` | array | Ordered checks: `{name, command, pass_criteria}` |
| `execution_hints` | object | `default_model` + `phase_overrides` (phase name → tier) |
| `item_model_tiers` | map | Per-item model tier, e.g. `{"1.1":"haiku"}` (primary tier source) |
| `last_good_sha` | string \| null | Most recent commit where all tests passed (rollback target) |
| `checkpoints` | map | Item number → commit SHA for each completed item |
| `parallelization_map` | object | Per-phase `{ "parallel": [...], "sequential": [...] }` groups |

**Full annotated schema and a complete JSON example:** `references/implement-plan-state-schema.md`. Read it once if you need the exact shape when writing or updating the file.

**`in_progress` / `in_progress_batch`:** Exactly one of these (or neither) is present at a time — `in_progress` for a single-item batch, `in_progress_batch` for a parallel batch. Set in Step 0 (before implementation) and removed in Step 5 (after commit). On resume, if either exists, an item was interrupted mid-implementation — the resume logic in Step 0 handles this.

### Plan Identity (`plan_identity`)

`plan_file` is a **path**, and a path is a label. The default path `IMPLEMENTATION_PLAN.md` is reused by every plan the repo ever runs — completed plans are archived to `docs/archive/IMPLEMENTATION_PLAN-vN.md` and a new one is written to the same path. So a surviving state file from a *finished* run will match the next plan's `plan_file` exactly while describing entirely different work. That is #235: resume reads `current_phase: COMPLETE`, finds nothing remaining, routes to `ALL_COMPLETE`, and reports a successful run having implemented nothing — with a completion report drawn from the previous plan's items.

`plan_identity` fixes that by recording **content, not the identifier**:

```json
"plan_identity": {
  "generated": "2026-07-29",
  "total_phases": 8,
  "phase_titles": ["Phase 1: Injection Doctrine and the Guards Built On It", "Phase 2: ..."],
  "item_ids": ["1.1", "1.2", "1.3", "2.1"]
}
```

**These four fields, and only these four, are invariant while a plan executes.** The plan file is *modified* during a run, so most of it is unusable as a fingerprint:

| Plan content | Changes during a run? | In the fingerprint? |
|---|---|---|
| `**Generated:**` | No | **Yes** |
| `**Total Phases:**` | No | **Yes** |
| `## Phase N: [Title]` headings | No — never decorated | **Yes** (verbatim, without the leading `## `) |
| `#### N.M` item **numbers** | No | **Yes** |
| `#### N.M` item **titles** | **Yes** — decorated on completion with ` ✅ Completed YYYY-MM-DD` | **No** |
| `**Status:**` fields | **Yes** — `PENDING` → `COMPLETE [date]` | **No** |
| `**Completed:**` header field | **Yes** — added at finalization | **No** |
| Task/acceptance checkboxes | **Yes** | **No** |

A fingerprint over the whole file, or over heading *text*, would differ from itself after the very first item and reject every legitimate resume — turning a data-loss bug into a resume-never-works bug. Key on the item **number**, never its title.

Derive the fingerprint with three commands over `PLAN_FILE` — no hashing tool, so it works identically on every platform and a human can read a mismatch:

```bash
grep -E '^\*\*(Generated|Total Phases):' "$PLAN_FILE"
grep -E '^## Phase [0-9]+:' "$PLAN_FILE"
awk '/^#### /{ if (match($0, /[0-9]+\.[0-9]+/)) print substr($0, RSTART, RLENGTH) }' "$PLAN_FILE"
```

**Extract the item id with `match()`, not by anchoring it to the start of the heading.** The completion decoration is *supposed* to be a suffix (`#### 1.1 Title ✅ Completed 2026-07-30`) but is not reliably one: two items in plan v13 came back as `#### ✅ Completed 2026-07-30 — 7.1 Title`, and an anchored `^#### [0-9]+\.[0-9]+` silently dropped both — an item-count that is quietly 17 instead of 19. `match()` takes the **first** `N.M` anywhere on the line, which is the item number under either decoration and is unaffected by a version-like string later in the title.

When you decorate a completed heading, **append** the marker and never place anything before the item number — `plan_identity` parses that number, and a prefix decoration is one regex away from breaking the guard.

**State file rules:**
- Created during STARTUP; the main agent reads/writes it directly (small, structured — no subagent); gitignored (ephemeral, not a project artifact); deleted during FINALIZATION **after** the COMPLETION REPORT has been generated from it.
- Updated BEFORE implementation starts (mark item IN_PROGRESS) and AFTER commit succeeds (mark item COMPLETE, clear the in-progress marker).
- On STARTUP, if it exists, resume from where it left off instead of re-reading the full plan; if resume detects an in-progress entry, offer the user retry/skip/complete options before continuing.

### State Shedding

**After every 5 completed work items**, actively shed accumulated conversational state: the state file contains everything needed to continue, so discard all prior subagent summaries, file lists, and error details and derive the next iteration's work item and context exclusively from the state file. The only conversational state to retain is the `PLAN_FILE` path, the user flags (`--auto-merge`, `--pause-between-phases`), and the state file path.

### Orchestration Pattern

The main agent is a **thin loop controller**: it decides what to do next, spawns subagents to do it, records outcomes in 1-2 sentences, and moves on — all heavy lifting (reading, coding, testing, docs) happens inside subagents whose context is discarded after they return. **Parallel-first:** when the plan marks items parallelizable (same phase, no inter-dependencies), launch them concurrently with `run_in_background: true` to cut total execution time.

### Implementation Philosophy

Each work item must be an integrated, architecturally coherent change, not an isolated patch. Before coding, the implementation subagent should understand how the item relates to the broader plan and codebase; if implementing it would conflict with or undermine another planned change, surface that rather than proceed blindly. The goal is elegant, cohesive changes that fit the project's architecture and avoid technical debt or a whack-a-mole fix cycle.

### Worktree Strategy

All file-modifying work in a phase runs inside a shared isolated worktree named `phase-[PHASE_NUMBER]` (e.g., `phase-3`). The merge point is the phase boundary — once all work items in a phase are implemented, tested, and committed, the worktree is merged back to the main branch before the next phase begins.

**Granularity is per-phase, not per-item:** per-phase gives simpler coordination (all items in a phase share context) and one merge event per phase, at the cost of intra-phase parallel items sharing a tree (write conflicts avoided by the 3-subagent cap); per-item would maximize isolation but add N merge events per phase and coordination overhead for parallel items that read each other's output.

**Lifecycle:** the worktree `phase-[N]` is created automatically when the phase's first subagent declares `isolation: worktree phase-[N]`; every sequential and parallel implementation subagent and the testing subagent in that phase declare the same name and share it; at the phase boundary it is merged to the main branch and the next phase starts fresh.

**Loop guard:** the name includes the phase number, so if a subagent re-declares a prior phase's name Claude Code reuses the existing worktree rather than creating a second (no data loss) — but always use the current phase number. **Graceful degradation:** if Claude Code lacks `isolation: worktree` support (older version), the instruction is a no-op and work runs in the standard working tree; plan execution is unaffected.

### Workflow Per Batch

The MAIN LOOP processes one **batch** per iteration — a single work item (sequential) or multiple independent items in one phase (parallel, the preferred case). Batch cardinality is the only thing that varies; the step sequence is identical: mark in-progress → implement (one subagent per item, parallel items concurrent) → test the whole batch with one subagent → optionally update PROGRESS.md/LEARNINGS.md and capture phase-boundary learnings → single commit + push → update the state file. The MAIN LOOP below specifies each step, calling out the single-item vs batch variations inline.

### Finalization

When all work items are complete: polish documentation, create a PR with a descriptive title, and (only with `--auto-merge`) merge it and clean up the branch. See the FINALIZATION section for the exact steps.

## Instructions

Follow these steps exactly. Use the **Agent tool** to spawn subagents (with `subagent_type` and `prompt: "..."`). Use **TaskCreate/TaskUpdate/TaskList** only for progress tracking — they do NOT launch subagents. After each subagent returns, retain only the minimal summary described — discard everything else.

### STARTUP (do this ONCE at the beginning)

**Step 0: Check for existing state file (resume support)**

Check if `.implement-plan-state.json` exists in the repository root. Read it directly (it is small JSON — no subagent needed).

- **If the state file does not exist or is corrupted:** Continue with Step 1 below.
- **If the state file exists and is valid:** verify it belongs to *this* plan before trusting anything else in it (see below), then resume execution. Skip the STARTUP subagent. Read `current_phase`, `current_item`, `completed`, `failed`, and `parallelization_map` from it.

  **Check plan identity FIRST (before the IN_PROGRESS check).** Run the two greps from "Plan Identity" above against `PLAN_FILE`, build the same four fields, and compare them to the state file's `plan_identity`. This must come first: an `in_progress` entry that belongs to a different plan names an item number that means something else here, so acting on it before establishing identity is acting on the wrong plan.

  - **Fields match:** the state belongs to this plan. Continue to the IN_PROGRESS check.
  - **`plan_identity` is absent** (a state file written before this field existed): do not guess. Report `Existing state file has no plan_identity — it predates identity tracking and cannot be matched to [PLAN_FILE].` and present the same three options as a mismatch.
  - **Fields differ:** the state file describes a *different* plan. Do NOT resume. Report the mismatch concretely — name each field that differs and show both values, e.g. `state: generated 2026-07-29, 8 phases, 42 items (1.1-8.6) | plan file: generated 2026-07-30, 8 phases, 19 items (1.1-8.3)` — then present three options and wait:
    - **(1) Start fresh (recommended):** delete `.implement-plan-state.json` and continue with Step 1. This is the right choice whenever a previous plan was archived and a new one written to the same path.
    - **(2) Resume anyway:** keep the state file and continue to the IN_PROGRESS check. Only correct if the plan was legitimately edited mid-run (items added or renumbered) and the completed items still refer to the same work.
    - **(3) Abort:** stop so the user can inspect both files manually.

  **Never treat a matching `plan_file` path as identity.** Completed plans are archived to `docs/archive/IMPLEMENTATION_PLAN-vN.md` and the next plan is written to the same default path, so the path always matches and proves nothing.

  **A state file that says the plan is already finished is not a completed run.** If `plan_identity` matches and nothing remains (`current_phase` is `COMPLETE`, or no item in `parallelization_map` is outside `completed`/`failed`), do NOT route to `ALL_COMPLETE` and generate a completion report — that report would describe work this invocation did not do. Report `[PLAN_FILE] is already complete ([N] items, finished [date]). Nothing to do. Delete .implement-plan-state.json to re-run it from scratch.` and stop.

  **Check for interrupted work items (IN_PROGRESS detection):** Check for an `"in_progress"` field (single-item batch) or `"in_progress_batch"` field (parallel batch). These are set in Step 0 of the MAIN LOOP (before implementation) and cleared in Step 5 (after commit). If either is present, an item was interrupted mid-implementation — present a resume prompt with three options: retry, skip, or mark complete. See `references/implement-plan-examples.md` for the exact prompt text.

  Wait for the user's choice:
  - **(1) Retry:** Remove the `in_progress` (or `in_progress_batch`) entry. Set `current_item` to this item (or the first item in the batch). Proceed to the MAIN LOOP — the item(s) will be implemented fresh.
  - **(2) Skip:** Move the item(s) to `failed` with `"error": "Skipped by user on resume"`. Advance `current_item` to the next item after the skipped one(s). Proceed to the MAIN LOOP.
  - **(3) Mark complete:** Run `git log -1 --format="%H"` for the current HEAD SHA. Add the item(s) to `completed` with that SHA. Update the plan file's Status field(s) to `COMPLETE [today's date]` via a subagent. Advance `current_item`. Proceed to the MAIN LOOP.

  For `in_progress_batch`, present ALL interrupted items in the message and apply the user's choice to the entire batch. **If no IN_PROGRESS items found:** report "Resuming from [current_item] in [current_phase]. [N] items already completed." and proceed to the MAIN LOOP.

**Step 1: Initial plan scan (subagent)**

Launch an Agent (subagent_type: "general-purpose") to read `PLAN_FILE`, PROGRESS.md (if exists), and LEARNINGS.md (if exists). Prompt the Agent to return ONLY:

- **First incomplete phase**: phase name + each work item (number + brief description).
- **Full parallelization map** for ALL phases: per-phase parallel groups vs sequential items (compact metadata, not plan content). Parse each item's `**Depends On:**` field — items with no intra-phase dependency can run in parallel; items with `Depends On: [item]` run after those complete (more accurate than file-based heuristics alone).
- **Verification commands**: parse `### Definition of Done (Runnable)` sections (between `<!-- BEGIN DOD -->` and `<!-- END DOD -->`) into `{name, command, pass_criteria}` entries; if none exist, detect the test command from project config files.
- **Execution hints**: parse `### Execution Hints` for phase-level tiers (`sonnet`/`opus`/`haiku`), context budget, and parallelization notes → `{ default_model, phase_overrides: { "Phase N": "tier" } }`.
- **Item model tiers**: parse every item's `**Model Tier:**` field (e.g. `**Model Tier: haiku**`) → flat map `{ "1.1": "haiku", ... }`; items without one default to the execution-hints default (usually `sonnet`). Per-item tiers take precedence over phase hints at dispatch.
- **Project context** (from CLAUDE.md, package.json, pyproject.toml, Makefile, or similar): `project_description` (one-sentence summary), `tech_stack` (primary language/framework), `test_command` (still detected as a legacy fallback), `conventions` (3-5 key ones, e.g. "kebab-case files, ESM imports, SKILL.md uppercase").
- Current progress summary (1-2 sentences) and total work items remaining across all phases.

**Step 2: Write initial state file**

Using the subagent's response, write `.implement-plan-state.json` to the repository root **with the Write tool** (not a shell heredoc), following the field table above and the full schema in `references/implement-plan-state-schema.md`. Initialize `completed`/`failed` to `[]`, `checkpoints` to `{}`, and `last_good_sha` to `null`; set `plan_file`, `plan_identity` (run the two greps from "Plan Identity" above against `PLAN_FILE` and record `generated`, `total_phases`, `phase_titles`, `item_ids` — do this *now*, while the plan is still un-decorated, so the recorded `item_ids` are the full set), `started_at` (current ISO timestamp), and `current_phase`/`current_item` (the first incomplete phase and its first item); fill `project_context` (with `verification_commands` as `{name, command, pass_criteria}` entries — tests plus any detected lint/typecheck), `execution_hints` (default `default_model` `sonnet`, `phase_overrides` `{}` if none), `item_model_tiers`, and `parallelization_map` from the subagent.

**Step 3: Ensure state file is gitignored**

Read `.gitignore` (treat a missing file as empty). If it does not already contain a `.implement-plan-state.json` line, add that line via the Edit tool (or the Write tool if `.gitignore` does not yet exist). If `.gitignore` was modified, stage and commit only it:
```bash
git add .gitignore && git commit -m "Add .implement-plan-state.json to .gitignore"
```

**Step 4: Create task list**

Create a task list using TaskCreate to track each remaining work item in the first phase, with metadata noting which items can run in parallel. **Use the parallelization map from the state file for the entire execution:** when entering a phase, consult `parallelization_map` to determine which items are independent and launch them concurrently.

### MAIN LOOP — Repeat until all work items are complete:

Before each iteration, consult the `parallelization_map` in `.implement-plan-state.json` to select the next **batch**: routing `NEXT:` → a **single item** (alone in the phase, or dependent on incomplete items) = **cardinality 1, sequential**; routing `PARALLEL:` → **2-3 independent items** in one phase = **cardinality N, parallel** (the **preferred** case — always check for parallelization before falling back to a single item).

The steps below are **cardinality-parameterized**: they execute identically for a batch of 1 or a batch of N, except where a step explicitly calls out its **single-item** vs **batch** variation. "The batch" always means the set of items processed this iteration.

---

#### Step 0: MARK IN_PROGRESS (Main Agent — do this yourself)

Before launching any implementation subagent, mark the whole batch as in progress:

1. **Update state file:** Read `.implement-plan-state.json`, add the in-progress marker for the batch's cardinality, and write it back:
   - **Single item:** set `"in_progress": { "item": "[N.M]", "phase": "[phase name]", "description": "[brief]", "started_at": "[ISO timestamp]" }` and set `current_item` to `[N.M]`.
   - **Batch:** set `"in_progress_batch": [ { "item": "[N.M]", "phase": "...", "description": "...", "started_at": "[ISO]" }, ... ]` listing **all** items in the batch.
2. **Update plan file:** Launch a single quick Agent (subagent_type: "general-purpose"):

   > In [PLAN_FILE], find work item(s) **[N.M]** (single) — or **[N.M, N.N, ...]** (batch) — and update each item's `**Status:**` field from `PENDING` to `IN_PROGRESS`.
   > Return: STATUS_UPDATED when complete.

This ensures that if the session is interrupted during implementation, the resume logic can detect the incomplete work. (One subagent handles the whole batch — for a batch it lists every item.)

#### Step 1: IMPLEMENTATION (Agent — one per item)

**Model tier per item** (priority order): `item_model_tiers["[ITEM]"]` (primary; set by the planner) → `execution_hints.phase_overrides["[phase]"]` (phase-level fallback) → `execution_hints.default_model` (session default, typically `sonnet`). Tiers resolve independently per item — parallel items in one batch may dispatch to different tiers, which is expected and correct.

**Dispatch by tier:** `haiku` → `Agent(subagent_type: "haiku-implementer")` (deterministic transforms, low cost); `sonnet` → `Agent(subagent_type: "sonnet-implementer")` (standard coding, default); `opus` → `Agent(subagent_type: "opus-implementer")` (judgment-heavy, architectural). If a named implementer agent is not installed (`.claude/agents/[tier]-implementer.md`), fall back to `Agent(subagent_type: "general-purpose", model: "[tier]")`.

**Dispatch mode by cardinality:**
- **Single item:** launch the implementer agent (foreground) and wait for it to return.
- **Batch:** launch ALL items in the batch in a **single message with multiple Agent tool calls**, each with **`run_in_background: true`**, so they execute truly concurrently.

Launch each implementer agent with this prompt (the ONLY implementer prompt — for a batch, each subagent receives exactly one item as its `[ITEM ...]`):

> **Project Context:** [project_description]. Tech stack: [tech_stack]. Test command: [test_command]. Conventions: [conventions].
>
> **Worktree Isolation:** Use `isolation: worktree phase-[PHASE_NUMBER]` for all file-modifying operations in this phase. All work items in this phase — sequential and parallel — share one isolated worktree named `phase-[PHASE_NUMBER]`; individual items do NOT get separate worktrees. This shared-per-phase approach lets parallel items coordinate while isolating phase work from the main branch, and prevents partial changes from polluting the working tree if implementation is interrupted. Merge to the main branch on phase completion.
>
> Read [PLAN_FILE]. Implement work item: **[ITEM — phase name, item number, brief description]**.
> Complete ALL tasks in this work item.
> When implementation is complete, also update [PLAN_FILE]: change this item's `**Status:**` field to `COMPLETE [YYYY-MM-DD]` (today's date), and add the completion date to the heading (e.g., `#### N.M Title ✅ Completed YYYY-MM-DD`).
> After completing the work item, check if [PLAN_FILE]'s Risk Mitigation table has any risk entries related to this work item. If so, update the risk's `Status` column from `Open` to `Mitigated`.
> Return ONLY: (1) files created/modified, (2) implementation summary (max 3 sentences), (3) DONE or error description.

(Populate `[project_description]`, `[tech_stack]`, `[test_command]`, and `[conventions]` from the `project_context` object in `.implement-plan-state.json`.)

**Batch constraints (parallel case only):** maximum 3 parallel implementation subagents at once (to avoid file conflicts); if items touch overlapping files, run them sequentially instead; use TaskOutput to check background agent results (you will be notified as each completes).

**Collect results.** For a single item you already have its result. For a batch, as each background Agent completes (TaskOutput notifies you), record per item: work item name, files changed, and success / failure / escalation status. Then proceed to Step 1b.

#### Step 1b: ESCALATION HANDLING (conditional — only if an agent returned ESCALATE)

Apply this handler to **each** item whose implementer returned `ESCALATE: [reason]` instead of `DONE`:

1. **Determine next tier:** haiku → sonnet → opus. If the current tier is already `opus`, do not escalate further — treat as `DONE`, accept the agent's partial output, and proceed to Step 2 for that item.
2. **Log the escalation:** Launch a quick Agent:
   > Append one line to LEARNINGS.md: "Item [N.M] escalated from [current tier] to [next tier]: [reason]". Return: LOGGED.
3. **Update state file:** Set `item_model_tiers["[N.M]"]` to the next tier so the escalation is recorded.
4. **Re-dispatch at higher tier:** Return to Step 1 for this item with the updated tier. Run the higher-tier implementer once — no further escalation allowed. The orchestrator (running on Opus) accepts the result.

**Batch note:** Handle escalated items sequentially with the handler above — do NOT block already-completed items while handling escalations; process escalations after all non-escalated results are collected. If any agent failed **outright** (not an escalation), handle its work item sequentially in a follow-up (re-dispatch, or surface to the user if it cannot proceed).

#### Step 2: TESTING (single Agent)

Run ONE testing subagent after the entire batch is implemented (after the single item, or after ALL parallel items complete). First read `verification_commands` from `.implement-plan-state.json`'s `project_context`. **Backward compatibility:** if the state file has `test_command` but no `verification_commands`, wrap it as `[{"name": "tests", "command": "[test_command value]", "pass_criteria": "exit code 0"}]`.

Launch an Agent (subagent_type: "general-purpose") with this prompt (the ONLY testing prompt):

> **Project Context:** [project_description]. Verification commands: [list all verification_commands from state file — name, command, pass_criteria for each].
>
> Run ALL of the following verification commands and report pass/fail per command:
> [For each entry in verification_commands:]
> - **[name]**: `[command]` — pass criteria: [pass_criteria]
>
> For each command:
> 1. Run the command
> 2. Check the result against the pass criteria
> 3. If it fails, diagnose root cause and fix the issue
> 4. Re-run the failed command
> 5. Repeat until it passes or 3 fix attempts are exhausted
> If after 3 fix attempts the same command(s) still fail, STOP and return TESTS_STUCK with: failing command names, error messages, and what you tried.
>
> When all verification commands pass, return:
> - Per-command results (command name, pass/fail, output summary)
> - For each issue fixed: problem, solution, prevention tip (1 line each)
> - ALL_TESTS_PASS confirmation

**If ALL_TESTS_PASS:** Proceed to Step 3. Note any issues briefly for the LEARNINGS.md update.

**If TESTS_STUCK:** The testing subagent could not fix the failures. Offer the user a rollback choice (scope is the whole batch — "this item" for a single item, "this batch" for parallel): (1) rollback to `last_good_sha` and skip, (2) skip but keep changes and mark failed, (3) pause for manual intervention. See `references/implement-plan-examples.md` for the exact prompt text.

Wait for the user's choice:
- **(1) Rollback:** `git checkout -- .` (the failed work is uncommitted, so this restores the tree to `last_good_sha`); add the item(s) to `failed` with `"error": "Tests stuck — rolled back by user", "attempts": 3`; set `current_item` to the next item after the [item | batch]; record in LEARNINGS.md via a quick Agent; continue to the NEXT ITERATION.
- **(2) Skip:** add the item(s) to `failed` with `"error": "Tests stuck — skipped by user", "attempts": 3`; discard uncommitted changes with `git checkout -- .`; set `current_item` to the next item after the [item | batch]; continue to the NEXT ITERATION.
- **(3) Pause:** output the failing test details and stop execution. The user can fix manually and re-run `/implement-plan` to resume from the state file.

#### Step 3: OPTIONAL DOCUMENTATION UPDATE (Main Agent — conditional)

The plan-file update is already folded into the implementation subagent(s) (Step 1). The remaining tracking files are updated only when warranted:

1. **PROGRESS.md** — Only update if PROGRESS.md already exists in the repo OR `--progress` was set. If updating, append `[YYYY-MM-DD] [ITEM] — [FILES_LIST]` — **a single line** for a single item, or **one line for each completed item** in a batch.
2. **LEARNINGS.md** — Only update if the testing subagent (Step 2) reported actual issues that required fixes; if tests passed clean, skip entirely. If updating, launch a quick Agent:

   > Append to LEARNINGS.md: for each issue encountered (across the batch, if parallel), add "[ITEM]: [ISSUE_SUMMARY] — [FIX_APPLIED]" (one line per issue).
   > Return: DOCS_UPDATED when complete.

#### Step 3b: LEARNING CAPTURE (Main Agent — at phase boundaries)

**This step runs at the LAST work item of each phase, not after every batch.** When the current batch completes its phase (check `parallelization_map`), and only if the project has a CLAUDE.md with learning-capture rules and a memory directory (else skip entirely), review this phase's retained implementation and testing summaries for non-trivial findings. If any occurred (SQL injection fixes, architectural pattern discoveries, deployment gotchas, test infrastructure patterns, dead code found, etc.):

1. **Update the project's memory files** — write findings to the appropriate topic file in the project's memory directory (what was found, why it matters, what to watch for).
2. **Update MEMORY.md** — add a concise bullet + link to the topic file.
3. **Update CLAUDE.md** — add an operational rule if the finding warrants one (e.g., "never use sql.raw() with variables").

**What counts as non-trivial:** security fixes, patterns that took multiple attempts, architectural decisions made during implementation, dead/orphaned code discovered, integration-test infrastructure choices, any fix whose root cause was not obvious. **What to skip:** routine implementation (added a function, wrote tests that passed first try), documentation-only updates, config file changes. **Cardinality note:** parallel batches often complete a whole phase at once, so this step fires more frequently in the parallel case — review all the batch's subagent summaries (not just one) plus any test fixes when deciding what to capture.

#### Step 4: COMMIT (Main Agent — do this yourself)

A single commit covers the whole batch. Run these git commands directly:
1. `git status --short` — review changed files.
2. **If `git status` shows unexpected untracked files not in any subagent's file list, warn the user and do not stage them.**
3. `git add [FILES] [PLAN_FILE]` — stage the implementation files and the plan file (already updated by the implementation subagent(s)); also stage PROGRESS.md and/or LEARNINGS.md only if they were updated in Step 3. `[FILES]` = `[FILES_FROM_SUBAGENT]` for a single item, or `[ALL_FILES_FROM_ALL_SUBAGENTS]` for a batch.
4. Commit with the cardinality-appropriate message: **single item** → `git commit -m "Complete [WORK_ITEM_NAME]"`; **batch** → `git commit -m "Complete [PHASE_NAME]: [ITEM_1], [ITEM_2], ..."`.
5. `git push`

#### Step 5: UPDATE STATE FILE (Main Agent — do this yourself)

After the commit succeeds, read `.implement-plan-state.json` and update it: remove the in-progress marker (`in_progress` for a single item, `in_progress_batch` for a batch); append to `completed` one entry `{ "item", "phase", "description", "status": "COMPLETE", "sha", "files" }` per item — **for a batch, every item's entry shares the single commit SHA from Step 4**; add the item→SHA mapping(s) to `checkpoints` (the single item, or every batch item mapped to the shared SHA); set `last_good_sha` to the Step 4 SHA (the most recent known-good checkpoint); set `current_item` to the next item (or null if the phase is complete); write it back. Then mark the corresponding task(s) completed via TaskUpdate.

**State shedding check:** If the `completed` array length is a multiple of 5 — or crossed a multiple of 5 with this batch — this is a shedding boundary. From this point forward, derive all context from the state file only; do not reference earlier conversation history for work item details, file lists, or error summaries.

---

#### NEXT ITERATION (applies to every batch)

**Primary path: Use the state file (no subagent needed).** Read `.implement-plan-state.json` directly. From `completed`, `current_phase`, and `parallelization_map`, find the items in the current phase not yet in `completed` or `failed`; if any remain, consult `parallelization_map` for whether they are parallel or sequential; if none remain, advance `current_phase` to the next phase (and consult its map); if no phases remain, the plan is complete. Then determine the routing token:

- `PHASE_CHANGE [new phase name] PARALLEL: [item1], [item2], [item3]` — moving to a new phase with multiple independent items
- `PHASE_CHANGE [new phase name] NEXT: [item description]` — moving to a new phase with a single/dependent item
- `PARALLEL: [item1], [item2], [item3]` — staying in the same phase with multiple independent items
- `NEXT: [item description]` — staying in the same phase with only one item or all remaining have dependencies
- `ALL_COMPLETE` — nothing remains

**Fallback path: Subagent plan re-read (only if state file is missing or ambiguous).** If the state file does not exist, is corrupted, or the parallelization map lacks enough information, launch an Agent (subagent_type: "general-purpose") to check `PLAN_FILE`:

> Read [PLAN_FILE]. List ALL remaining incomplete work items with their phase and item numbers.
> For the next batch: are any of them parallelizable (independent, no shared file dependencies)?
> Return ONLY one of the routing tokens (`PHASE_CHANGE ... PARALLEL:`, `PHASE_CHANGE ... NEXT:`, `PARALLEL:`, `NEXT:`, or `ALL_COMPLETE`) using the exact formats listed in the primary path above.
> Also return a parallelization map for ALL remaining phases so the state file can be rebuilt.

If the fallback path was used, rewrite `.implement-plan-state.json` with the updated information.

**Phase transition handling (quality gate + optional pause):** If the routing determination indicates `PHASE_CHANGE`, run the phase boundary quality gate **before** proceeding to the next phase, regardless of whether `--pause-between-phases` is set.

**Step T1: Phase Validation (Agent).** Launch an Agent (subagent_type: "general-purpose") to validate the completed phase:

> Read [PLAN_FILE]. Find the **Phase Completion Checklist** and **Testing Requirements** sections for **[completed phase name]**.
> For each checklist item and testing requirement, verify whether it has been satisfied (marked with [x] or evidenced by work item completions).
> Cross-reference against the completed work items: [list item numbers from state file's completed array for this phase].
> Return ONLY:
> - `PHASE_VALID` if all checklist items and testing requirements are satisfied, OR
> - `PHASE_ISSUES: [list of unchecked/unsatisfied items]` if any items remain incomplete.

**Step T2: Present Phase Summary.** Display the phase summary to the user (always, regardless of flags):

```text
Phase [completed phase] complete. [M] items implemented, [F] failed/skipped.
Validation: [PHASE_VALID | PHASE_ISSUES]
[If PHASE_ISSUES: list the unchecked items]
Next up: Phase [new phase] ([N] work items).
```

**Step T3: Handle Validation Issues.** If the validation subagent returned `PHASE_ISSUES`, present the unchecked items and ask for guidance: (1) continue anyway, (2) pause to address the issues manually, or (3) abort to FINALIZATION with whatever is complete so far. See `references/implement-plan-examples.md` for the exact prompt text.

Wait for the response: **(1) Continue anyway** — log the issues to LEARNINGS.md via a quick Agent, then proceed; **(2) Pause** — stop execution (the user fixes issues and re-runs `/implement-plan` to resume from the state file); **(3) Abort** — proceed to FINALIZATION.

**Step T4: Phase Pause (only when `--pause-between-phases` is set).** If `--pause-between-phases` was passed AND the phase validated successfully (PHASE_VALID or user chose "Continue anyway"), ask for confirmation before proceeding:

```text
Continue to Phase [new phase]? (yes/no/skip phase/abort)
```

Wait for the response: **yes** — proceed to the next phase (the next batch enters the MAIN LOOP as a single item or parallel batch, per the routing); **no** or **abort** — proceed to FINALIZATION with whatever is complete so far; **skip phase** — mark all items in the upcoming phase as skipped in `failed` with `"error": "Phase skipped by user"`, and continue to the phase after. If `--pause-between-phases` is NOT set (default) and the phase is valid, proceed automatically.

**Routing:** If **PARALLEL**, begin the next MAIN LOOP iteration with a multi-item (parallel) batch. If **NEXT**, begin the next iteration with a single-item (sequential) batch. If **ALL_COMPLETE**, proceed to FINALIZATION.

**Do not stop early.** Continue looping until the state file (or subagent fallback) indicates ALL_COMPLETE (or the user aborts via a `--pause-between-phases` confirmation). Every work item in the plan must be implemented, tested, and committed before finalization. **If execution cannot continue** (context window exhaustion, user interrupt, unfixable error, or user abort from the phase gate), proceed to the COMPLETION REPORT section before stopping.

### COMPLETION REPORT (output on EVERY exit path)

Before stopping execution — whether from normal completion, early termination, user abort, or error — read `.implement-plan-state.json` and output a report with these sections, in order: a banner, the status line, session start time, current phase, a completed-items list (with SHAs), a failed/skipped-items list (with errors), a remaining-items list, an in-progress warning (only if `in_progress`/`in_progress_batch` exists), the last checkpoint, and resume instructions. This is the **last thing the command outputs** regardless of how it exits. See `references/implement-plan-examples.md` for the exact template and formatting.

**Report generation rules:**

1. **Read the state file** for `completed`, `failed`, `in_progress`/`in_progress_batch`, `current_phase`, `last_good_sha`, and `plan_file`.
2. **Remaining items** = the full per-phase item list from `parallelization_map` minus everything in `completed` and `failed`.
3. **Status line:** `COMPLETE` (all items completed, none remaining); `PARTIAL — context exhaustion` (running low on context window); `PARTIAL — user abort` (stopped at a phase gate or confirmation prompt); `PARTIAL — unfixable error` (TESTS_STUCK with user choosing Pause); `PARTIAL — interrupted` (any other early stop).
4. **Resume guidance:** always show the `/implement-plan` command needed to resume (including `--input` if the plan path is non-default) — except on `COMPLETE`, where the "Remaining" section shows `(none)` and the resume line is omitted.
5. **No state file** (e.g., error before state file creation): output a minimal report — "No state file found. No work items were completed. Run `/implement-plan` to start fresh." **This fallback is only ever correct before the state file is created.** Never reach it by having deleted the file yourself — the deletion in FINALIZATION happens *after* this report is generated, precisely so a successful run cannot end up asserting that no work items were completed.

### FINALIZATION (only when ALL work items are complete)

#### Final Step 1: Documentation Polish (Agent)

Launch an Agent to review and update all documentation:

> Review and update all documentation:
> - README.md: ensure accuracy, update any outdated sections
> - [PLAN_FILE]: verify all items marked complete. Set the `**Completed:**` header field in the plan file to today's date (YYYY-MM-DD). The field is in the plan header area (after `**Generated:**`, before `**Based On:**`). If the `**Completed:**` field does not exist, add it on the line after `**Generated:**`.
> - PROGRESS.md (if it exists): add completion summary at end
> - LEARNINGS.md (if it exists): synthesize all entries into a SUMMARY section at the top (max 10 bullet points)
>
> Return: DOCS_FINALIZED

#### Final Step 2: Create PR (Main Agent)

1. `git status --short` — review changes; warn the user about any unexpected untracked files.
2. `git add [PLAN_FILE] README.md` (plus PROGRESS.md/LEARNINGS.md only if they exist and were modified), then `git commit -m "Polish documentation" && git push`.
3. Build a **descriptive** PR title from the phases actually implemented (e.g., "Implement: Unified Schema, Tool API Fix, Context Management") — NOT a generic title like "Implementation Complete".
4. Create the PR via `gh pr create` with that title and a body summarizing all phases completed, the number of work items, key changes, and any learnings; output the PR URL to the user.

**Default behavior (no `--auto-merge` flag): STOP HERE.** The user reviews and merges the PR manually.

#### Final Step 2b: Auto-Merge (only if `--auto-merge` was specified)

If `--auto-merge` was passed: merge the PR with `gh pr merge --squash`, delete the remote branch, then `git checkout main && git pull`.

#### Final Step 3: Output (Completion Report)

Output the **COMPLETION REPORT** (defined above) with `Status: COMPLETE`, then add the PR URL (PR-only mode) or merge confirmation (`--auto-merge`), plus any key learnings or issues encountered (1-3 bullet points max).

#### Final Step 4: Clean Up State File

**Only after the COMPLETION REPORT has been output**, delete the state file — it is ephemeral execution state and must not survive the run:

```bash
rm -f .implement-plan-state.json
```

**This is the last action of the command, and the ordering is load-bearing in both directions.** It must come *after* Final Step 3 because the COMPLETION REPORT is generated by reading this file (report rule 1) and its documented behaviour for a missing file is "No work items were completed" — deleting first makes a fully successful run report the opposite of the truth. It must not be skipped, because a state file that outlives its run is inherited by the next plan written to the same path (#235). If any earlier Final Step failed and you are stopping short of a complete run, **do not delete the file** — that is the Early Termination path in Error Handling, where the state is what makes resume possible.

## Output Files

This command creates/updates:

| File | Purpose | When Updated |
|------|---------|--------------|
| `PLAN_FILE` (default: IMPLEMENTATION_PLAN.md) | Marks work items complete with dates | Always (updated by implementation subagent) |
| PROGRESS.md | Chronological log of completed work | Only if file already exists or `--progress` flag set |
| LEARNINGS.md | Issues encountered and solutions | Only when testing subagent reports actual issues |
| `.implement-plan-state.json` | Ephemeral execution state (gitignored, deleted on completion) | Always |

## Error Handling

**Missing Plan File:** if `PLAN_FILE` does not exist at the resolved path, output the error shown in Input Validation ("If the plan file is missing") and stop.

**Test Failures That Cannot Be Fixed (TESTS_STUCK):** when the testing subagent returns TESTS_STUCK (failures unfixed after 3 attempts), Step 2 offers Rollback / Skip / Pause. Rollback and Skip both discard uncommitted work with `git checkout -- .` (failed items are never committed, so this returns the tree to `last_good_sha` with no history rewrite) and mark the item(s) failed; Pause stops for manual fixing, resumable via `/implement-plan`. `last_good_sha` always points to the most recent all-tests-passing commit.

**Early Termination:** if execution stops before completion, output the COMPLETION REPORT with the matching partial status and preserve `.implement-plan-state.json` (do NOT delete it) so `/implement-plan` can resume — **context exhaustion** → `PARTIAL — context exhaustion`; **user interrupt** → resume on next run, and if able to output first, `PARTIAL — user abort`; **unfixable error** (Pause at TESTS_STUCK) → `PARTIAL — unfixable error` with failing-test details; **user abort at phase gate** (Abort, or "no" at a `--pause-between-phases` prompt) → `PARTIAL — user abort`.

**Git/PR Failures:** if commit or PR operations fail, report the error to the user, provide manual commands to complete the workflow, and preserve local changes.

## Performance

**Typical Duration:**

| Plan Size | Expected Duration |
|-----------|------------------|
| Small (5-10 work items) | 15-30 minutes |
| Medium (10-20 work items) | 30-60 minutes |
| Large (20-40 work items) | 1-2 hours |
| Very Large (40+ work items) | 2+ hours |

Duration scales with work item complexity, test suite size and duration, the number of test failures to fix, and documentation scope. **Abnormal signs:** the same work item attempted 3+ times, the testing subagent looping 10+ iterations, or no progress after 15 minutes. **If stuck:** check the task list and testing-loop messages, review PROGRESS.md for the last successful work item, and consider interrupting and re-running — the command resumes from `.implement-plan-state.json` at the last incomplete work item.

## Examples

See `references/implement-plan-examples.md` for usage examples of each flag and flag combination (default PR-only mode, `--auto-merge`, `--input`, `--pause-between-phases`, and combined flags).

On each run the orchestrator scans the plan (or resumes from `.implement-plan-state.json`), then loops one batch at a time: mark in-progress → implement (parallel where the plan allows) → test → optional docs → commit → update state, advancing phase by phase through the quality gate until all items are done. Default mode ends by creating a PR and printing its URL; `--auto-merge` merges the PR and returns to `main`.

## Related Commands

- `/plan-improvements` - Generate IMPLEMENTATION_PLAN.md from codebase analysis
- `/create-plan` - Generate IMPLEMENTATION_PLAN.md from requirements documents
- `/plan-next` - Get recommendation for next action
- `/test-project` - Run comprehensive test workflow
