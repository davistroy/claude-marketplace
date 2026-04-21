---
name: lab-notebook
description: Initialize mandatory experiment logging for projects involving system changes, benchmarks, debugging, or exploratory work. Creates LAB_NOTEBOOK.md with living decision/action tracking and injects iron-clad CLAUDE.md rules that make logging a PRECONDITION for every action.
effort: medium
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
---

# Lab Notebook

Establish mandatory, structured experiment logging for a project. Once initialized, every system modification, benchmark, configuration change, build attempt, and debugging step MUST be logged in `LAB_NOTEBOOK.md` — no exceptions.

The notebook combines three proven documentation patterns:
- **Scientific lab notebook** — hypothesis-driven entries with environment context and reproducibility
- **Architecture Decision Records** — decisions with alternatives considered and lifecycle tracking
- **Incident postmortem** — blameless failure analysis, action items, and "what went well"

## Proactive Triggers

Suggest this skill when:
1. The project involves **infrastructure or system administration** (servers, containers, GPU configs, networking)
2. Work is **experimental** — trying configurations, measuring performance, debugging issues
3. The project has **expensive failures** — changes that are hard to reverse, take time to diagnose, or affect shared systems
4. **Multiple sessions** will work on the same system (context loss between sessions is likely)
5. The user mentions "optimize", "benchmark", "debug", "configure", "deploy", or "experiment"

**Do NOT fire when:**
- The task is straightforward code implementation with git tracking
- The user explicitly declines structured logging
- A LAB_NOTEBOOK.md already exists and CLAUDE.md already has the lab notebook section

## Input

**Arguments:** `$ARGUMENTS`

Supported arguments:
- `init` — Full initialization: discover prior work, create LAB_NOTEBOOK.md, inject CLAUDE.md rules
- `entry "title"` — Add a new numbered entry to an existing notebook
- `status` — Show notebook health: entries, staleness, open action items, active decisions
- No arguments — Same as `init` if no notebook exists, same as `status` if one does

## Instructions

### On `init` (or no notebook exists):

Execute ALL steps below. Do not skip any.

#### Step 1: Discover Prior Work and Project Context

This is the most important step. Before creating the notebook, perform a THOROUGH survey of all existing work, history, and context. The goal: the notebook's opening section should be a coherent synthesis that lets anyone — including a future Claude session with zero context — understand exactly where things stand.

**1a. Read project documentation:**
- `CLAUDE.md` — operational rules, system configuration, known issues
- `README.md`, `docs/` — project purpose, architecture
- Any `*PLAN*.md`, `*TODO*.md`, `*STATUS*.md`, `*PROGRESS*.md` files — ongoing work, priorities, session handoffs
- `LEARNINGS.md` or similar — distilled insights from prior work
- Memory files (if accessible) — `MEMORY.md` and referenced memory files

**1b. Reconstruct history from artifacts:**
- `git log --oneline -30` — recent commits, what changed, who worked on what
- `git log --all --oneline --graph -20` — branch structure, parallel work streams
- `git diff HEAD~10 --stat` — scope of recent changes
- Check for config management artifacts (snapshots, backups, deployment scripts)
- Docker images and containers (`docker images`, `docker ps -a`) — what's been built, what's running
- Build logs, test results, benchmark outputs — any prior experiment data

**1c. Assess current system state (for infrastructure projects):**
- Running services, versions, health status
- Resource utilization (CPU, memory, GPU, disk)
- Configuration values that affect behavior
- Known issues, warnings in logs, error states

**1d. Check for undocumented work:**
- Stale branches with uncommitted experiments
- Docker images with meaningful tags (e.g., `v2-test`, `pre-migration`)
- Log files, temp files, benchmark results in `/tmp` or project dirs
- Config snapshots or backup files

**1e. Mine existing docs for decisions and action items:**

While reading project documentation, actively extract two things:

*Decisions* — look for them in:
- `CLAUDE.md` operational rules (each rule that reflects a choice, not just a universal constraint)
- `LEARNINGS.md` findings (each "we chose X over Y" is a decision)
- Config files with parameter choices (thresholds, backend selection)
- `*PLAN*.md` files with chosen approaches
- Git commit messages that explain "why" not just "what"

Not every operational rule is a decision. Focus on choices that have alternatives — where someone might reasonably ask "why not X instead?" Universal constraints (e.g., "never send data to cloud services") are project rules, not decisions. Decisions imply a choice was made: "We chose threshold 0.98 over 0.975 because..."

Each decision that affects future work goes in the Decision Log.

*Open action items* — look for them in:
- `PROGRESS*.md` and handoff files ("What Needs To Happen Next" sections)
- TODO comments in code (`grep -r "TODO\|FIXME\|HACK" --include="*.py"`)
- Stale branches (represent unfinished work streams)
- GitHub issues (if accessible)
- Any "future work" or "next steps" sections in documentation

Each open item goes in the Action Items table. Also capture 2-5 recently completed major milestones for the Completed table — this establishes the project's velocity and recent trajectory. Don't exhaustively list everything ever done, just significant recent completions that provide context.

**If existing `LAB_NOTEBOOK.md` is found:** Read it, verify CLAUDE.md has the mandatory logging section (Step 3), and skip to Step 4. Do NOT recreate or overwrite an existing notebook.

#### Step 2: Create LAB_NOTEBOOK.md

Create `LAB_NOTEBOOK.md` in the project root. The notebook has two kinds of content:

1. **Living sections** (top) — updated continuously as work progresses. These are the "dashboard" view.
2. **Chronological entries** (bottom) — append-only experiment log. These are the detailed record.

**Full structure:**

```markdown
# {Project Name} — Lab Notebook

**Project:** {Brief description — what this project IS and what it DOES}
**Started:** {Today's date}
**Systems:** {Key systems involved — servers, containers, services, etc.}

---

## Decision Log

Decisions are tracked here with their lifecycle. When a decision is revisited, update its status to SUPERSEDED and link to the new entry. Never delete old decisions. For decisions originating in another project's notebook, note the source.

| # | Decision | Date | Status | Entry | Alternatives Considered |
|---|----------|------|--------|-------|------------------------|
| D1 | {example: Use Marlin FP8 over CUTLASS} | {date} | ACTIVE | E001 | {CUTLASS FP8: works but 7.6% slower} |

Status values: ACTIVE · SUPERSEDED (by D#) · REVERSED (in E#)

## Action Items

Track follow-ups that emerge from experiments. Move to Completed when done.

### Open
| # | Action | Created | Source Entry | Priority |
|---|--------|---------|-------------|----------|
| A1 | {example: Re-test prefix caching on vLLM upgrade} | {date} | E005 | When upgrading |

### Completed
| # | Action | Created | Completed | Source Entry |
|---|--------|---------|-----------|-------------|

---

## Prior Work Summary

{A coherent, well-written synthesis of all work that happened BEFORE this notebook was created.

Target length: 500-1500 words for established projects with significant history, shorter for new projects. Focus on decisions, failures, current state, and open work. Don't reproduce the content of existing documentation — reference it. ("See LEARNINGS.md for detailed findings from each quality iteration.") The summary complements existing docs, it doesn't replace them.

This section answers:
- What has been accomplished so far?
- What approaches were tried? Which succeeded, which failed, and why?
- What is the current state of the system?
- What decisions were made, and what was the reasoning?
- What remains to be done?

Write as a narrative with structure — use tables for comparisons, timelines for history, and decision records for key choices.

Source from: git history, config snapshots, build logs, existing documentation, Docker artifacts, and any other evidence discovered in Step 1.}

## Current Baseline

{Actual measured state of the system RIGHT NOW. Not placeholders — real values:
- Running services and their versions
- Key configuration parameters
- Performance baselines (measured, not assumed)
- System resources (memory, disk, GPU if relevant)
- Health status of all components}

---

## Experiment Log

### Entry 001 — {Title} [tag1] [tag2]
**Date:** {timestamp}
**Duration:** {how long this entry's work took — fill in when complete}
**Environment:** {system state — see guidance below}
**Status:** IN PROGRESS

**Objective:** {What we're trying to achieve}

**Hypothesis:** {What we expect to happen and why. Include success criteria.
Example: "Removing --enforce-eager will increase throughput by 20-30% because CUDA graphs reduce CPU launch overhead. Success: > 30 tok/s single-request."
For administrative/documentation entries: "N/A — documentation entry."}

**Rollback Plan:** {How to undo this change if it fails.
Example: "spark-config.sh apply pipeline-v3-final"
For read-only operations: "N/A — read-only measurement."
For additive-only operations: "N/A — additive only."}

**Actions & Results:**
{Each action taken with its immediate result. Log these AS YOU GO, not after the fact.}

**What Worked:** {Positive outcomes — what succeeded and why. Not just failures.}

**What Failed:** {For each failure: exact error, root cause analysis, what it tells us about the system.}

**Decision:** {What we decided and WHY.}
- **Alternatives Considered:** {What other options were evaluated and why they were rejected.
  Example: "Considered CUTLASS FP8 (44.9 tok/s, no NaN) vs Marlin FP8 (48.6 tok/s). Chose Marlin: 7.6% faster, proven stable."}

**Follow-ups:** {Action items that emerge. Copy these to the Action Items table above.}

---

*Entries continue below.*
```

**Scoping the Prior Work Summary:**

For new projects with little history, the summary may be a single paragraph. For mature projects with months of work, extensive documentation, and multiple contributors, resist the urge to include everything. Focus on what a new session needs to make decisions: key decisions and their reasoning, significant failures and what they taught you, current system state, and what's next. Reference existing docs for details rather than reproducing them.

**Project-specific tags:**

Define 3-5 project-specific tags based on the project's domain. Add these alongside the standard tags. Examples by project type:

| Project type | Specific tags |
|-------------|--------------|
| ML pipeline | `[pipeline]` `[solver]` `[eval]` `[staging]` `[quality]` |
| Infrastructure | `[gpu]` `[network]` `[container]` `[monitoring]` |
| ML training | `[training]` `[dataset]` `[model]` `[inference]` |
| Web application | `[api]` `[frontend]` `[database]` `[deploy]` |

Standard tags available for all projects:
`[build]` `[config]` `[benchmark]` `[debug]` `[decision]` `[incident]` `[performance]` `[memory]` `[network]` `[security]` `[cleanup]` `[init]`

**Environment field guidance:**

For single-system projects: `Environment: Ubuntu 24.04, vLLM v0.17.0rc1, pipeline-v3-final config`

For multi-system projects, structure as: `Environment: Dev: laptop (Windows) | Inference: DGX Spark (sm121-inject, 48.6 tok/s) | Data: homeserver (Docker DOWN)`

Capture which system each action targets. This is critical for reproducibility.

**Entry types and required sections:**

Every entry requires: Date, Status, Tags, Environment, Objective, Hypothesis, Rollback Plan, Actions & Results.

Sections used when applicable:
- **Duration** — fill in when entry is completed. Helps estimate future similar work.
- **What Worked / What Failed** — for entries with mixed outcomes or failures. Administrative entries (init, handoff) may omit these.
- **Decision + Alternatives** — when a choice is made. Always update the Decision Log.
- **Follow-ups** — when action items emerge. Always copy to the Action Items table.

For administrative entries (init, handoff, documentation), Hypothesis and Rollback Plan may be "N/A" but the fields must still be present to maintain template consistency.

**Cross-notebook references:**

When this project depends on experiments documented in another project's notebook, include references: `(See [project-path]/LAB_NOTEBOOK.md Entry NNN)`. In the Decision Log, note which project a decision originates from if it was made elsewhere.

**Quality bar for the Prior Work Summary:** A new Claude session reading ONLY this section should be able to:
1. Understand what the project is trying to achieve
2. Know what has been tried and what the results were
3. Understand the current system state without running any commands
4. Make informed decisions about what to do next without repeating past mistakes

#### Step 3: Inject CLAUDE.md Lab Notebook Section

This is the critical enforcement step. Add the following section to the project's `CLAUDE.md`. If no `CLAUDE.md` exists, create one with this section. If one exists, append this section.

**Before injecting:** Adapt the examples and tag lists to match the project's domain. Replace generic examples with project-relevant ones — e.g., for a pipeline project use "Expect Stage 6 to complete 10K articles in ~4 hours at concurrency 8" instead of a generic container example. Update the tag list in Rule 8 with the project-specific tags defined in Step 2.

**After injecting:** Add `LAB_NOTEBOOK.md — Experiment log with decision tracking and action items` to any existing "Key References" or "Key Files" section in CLAUDE.md. If no such section exists, add a brief one above the rules section. This ensures the notebook is discoverable from CLAUDE.md.

**The CLAUDE.md section to inject:**

```markdown
## Lab Notebook — MANDATORY Logging Protocol

**LAB_NOTEBOOK.md is the permanent experiment record for this project. The following rules are NON-NEGOTIABLE and have the HIGHEST PRIORITY after user safety.**

### Rule 1: Hypothesize, Plan Rollback, THEN Act

Before executing ANY system-modifying action, you MUST add an entry to LAB_NOTEBOOK.md with:
- **Objective:** What you're trying to achieve
- **Hypothesis:** What you expect to happen and why. Include measurable success criteria. Even simple expectations count: "Expect container to start and pass health check within 3 minutes."
- **Rollback Plan:** How to undo this change. For read-only operations, state "N/A — read-only." For destructive operations, this is CRITICAL — document the undo BEFORE you do the thing.

This applies to: commands on remote systems, container operations, config changes, builds, benchmarks, database operations, network changes, and any action that could fail or be hard to reverse.

**If you catch yourself about to run a command without an entry: STOP. Create the entry first. No exceptions.**

### Rule 2: Log Results As They Happen

Update the entry immediately after each action with:
- The exact command or operation performed
- The result: success, failure, or unexpected behavior
- Raw error output for failures — not just "it failed" but the actual message
- Performance numbers with units, conditions, and comparison to baseline
- Environment context: which image, config, system state was active

Do NOT batch-log multiple actions after the fact. Log each one as it completes.

### Rule 3: Analyze Failures — Root Cause, Not Symptoms

Failed attempts are MORE valuable than successes. For every failure:
- **Exact error:** The literal message or behavior observed
- **Root cause:** WHY it failed — trace to the underlying reason
- **System insight:** What this failure reveals about how the system works
- **Next approach:** What to try differently based on this understanding
- **Pattern recognition:** If this is the same class of failure as a previous entry, create or update a pattern table

### Rule 4: Document Decisions with Alternatives

Every decision must include:
- **The decision itself** and WHY it was made
- **Alternatives considered** — what other options were evaluated, with their trade-offs
- **Update the Decision Log table** at the top of LAB_NOTEBOOK.md (Decision, Status=ACTIVE, Entry reference, Alternatives)

When revisiting a previous decision: update the old decision's status to SUPERSEDED and reference the new entry. Never delete old decisions.

Bad: "Reverted to the old config"
Good: "Reverted to Marlin FP8 (48.6 tok/s) over CUTLASS FP8 (44.9 tok/s). CUTLASS works correctly (no NaN) but Marlin's weight-only kernel is more optimized for this hardware. Alternatives: CUTLASS FP8 (functional but 7.6% slower), Triton FP8 MoE (untested)."

### Rule 5: Track What Worked, Not Just What Failed

Include a "What Worked" section in entries with mixed outcomes. Successes establish positive patterns:
- Which approaches are reliable
- Which configurations are stable
- What the system does well

This prevents drift toward excessive caution — not everything is a problem to solve.

### Rule 6: Write Before Risky Operations

Before any operation that could crash the session, corrupt state, or take a long time:
- Flush ALL current findings to LAB_NOTEBOOK.md
- Include intermediate results, even if incomplete
- Update the Decision Log and Action Items tables
- If the session crashes, the next session must be able to continue from LAB_NOTEBOOK.md alone

### Rule 7: Maintain Living Sections

After EVERY completed entry, update the living sections at the top of LAB_NOTEBOOK.md:
- **Decision Log:** Add new decisions, update superseded ones
- **Action Items:** Add follow-ups from the entry, mark completed items

These tables are the "dashboard" — they must always reflect the current state.

### Rule 8: Tag and Contextualize Every Entry

Every entry must have:
- **Tags** in the title line — for searchability. Use project-specific tags defined during init alongside standard tags.
- **Environment** field: which system, image, config snapshot, backend. For multi-system projects, note which system each action targets. Critical for reproducibility.
- **Duration** (when completed): how long the work took. Helps estimate future work.

### Rule 9: Pattern Tables for Repeated Issues

When failures share a root cause or pattern, consolidate them into a table:

| Attempt | Error | Root Cause | Fix |
|---------|-------|-----------|-----|
| ... | ... | ... | ... |

This transforms individual failures into systematic understanding.

### Rule 10: Session Boundaries

When starting a new session on a project with an existing notebook, add a session boundary marker before your first entry:

`--- New session: {date} — {brief context of what this session will focus on} ---`

This traces context switches between sessions and helps explain gaps, changes in approach, or fresh perspectives. Read the Decision Log and Open Action Items before starting work — they are your orientation to current state.

### Rule 11: Log Before You Commit

**BLOCKING PRECONDITION on `git commit`:** Before every commit that touches application code (not just docs), the LAB_NOTEBOOK.md must have a current entry covering what you're about to commit. If the entry doesn't exist yet, create it before staging files. One entry can cover multiple related commits, but the entry must be written BEFORE the first commit in that sequence, not after.

This is the rule that prevents batching. It's easy to skip a "log results" step. It's harder to skip when the log IS the commit workflow.

### Enforcement

These rules are BLOCKING PRECONDITIONS, not suggestions. The mechanical process is:
1. Create/update entry with Hypothesis + Rollback Plan
2. Execute the action
3. Log the result immediately
4. **Before `git commit`: verify the notebook entry exists and covers this change**
5. Update Decision Log and Action Items if applicable
6. Repeat

There are NO exceptions for "quick" changes, "obvious" fixes, or "simple" tests. The cost of logging is seconds. The cost of NOT logging is hours of forensic reconstruction when a session crashes.
```

#### Step 4: Verify Setup

After creating both files:
1. Confirm `LAB_NOTEBOOK.md` exists with:
   - Prior Work Summary (not placeholders — real narrative with references to existing docs)
   - Current Baseline (measured values)
   - Decision Log table (populated with decisions mined from existing docs)
   - Action Items table (populated with open items from handoff/progress files)
   - At least one entry (Entry 001)
2. Confirm `CLAUDE.md` has the "Lab Notebook — MANDATORY Logging Protocol" section with all 11 rules, adapted with project-specific examples and tags
3. Report to the user: "Lab notebook initialized. {N} prior work items synthesized. {N} decisions tracked. {N} action items captured. All future actions will be logged."

### On `entry "title"`:

1. Read the current `LAB_NOTEBOOK.md`
2. Determine the next entry number
3. Add a new entry with:
   - Title + appropriate tags (suggest tags based on title keywords)
   - Current timestamp
   - Environment context (carry forward from most recent entry if system state hasn't changed; update if it has)
   - IN PROGRESS status
   - Objective pre-filled from conversation context
   - Hypothesis section ready to fill (prompt: "What do you expect to happen?")
   - Rollback Plan section ready to fill
4. Leave Actions/Results and remaining sections ready to fill as work progresses

### On `status`:

1. Read `LAB_NOTEBOOK.md`
2. Report:
   - Total entries and date range
   - Last entry: title, status, date
   - Active decisions (count + list from Decision Log)
   - Open action items (count + list)
   - Completed action items (count)
   - Tags used across entries (frequency)
   - Any entries still marked IN PROGRESS — **if the last IN PROGRESS entry is older than 7 days, flag it: "WARNING: Entry NNN has been IN PROGRESS since {date}. This may indicate incomplete or abandoned work. Review and update its status."**
3. Check if CLAUDE.md has the mandatory logging section — warn loudly if missing: "CRITICAL: CLAUDE.md is missing the Lab Notebook logging rules. The notebook exists but enforcement is not active. Run `/lab-notebook init` to reinject the rules."

## Relationship to Existing Documentation

The lab notebook doesn't replace other documentation patterns — it complements them:

| Existing pattern | Relationship to LAB_NOTEBOOK |
|-----------------|------------------------------|
| `LEARNINGS.md` | Notebook captures raw experiments. LEARNINGS captures distilled wisdom. Periodically extract key insights from recent entries into LEARNINGS. |
| `PROGRESS*.md` / session handoffs | The notebook's Action Items table partially replaces "What Needs To Happen Next" sections. Keep PROGRESS files for high-level session summaries; use the notebook for detailed experiment records. |
| `*PLAN*.md` files | Plans describe intended work. The notebook records what actually happened when executing them — including deviations, surprises, and plan changes. |
| Git commit messages | Commits record code changes. The notebook records the experiments, benchmarks, and decisions that motivated those changes. |
| Another project's `LAB_NOTEBOOK.md` | Cross-reference with `(See [path]/LAB_NOTEBOOK.md Entry NNN)`. Common when infrastructure changes (e.g., GPU optimization) affect application projects (e.g., pipeline performance). |

## Pre-Commit Enforcement (Hook)

The `personal-plugin` ships a `PreToolUse` hook that enforces Rule 11 at the git level — blocking `git commit` when `LAB_NOTEBOOK.md` exists but has no entry in the last 24 hours.

### Opt-in behavior

The hook is **opt-in via presence**: it only activates when `LAB_NOTEBOOK.md` exists in the git root. Projects without a notebook are completely unaffected — the hook exits 0 immediately.

### What counts as a "recent entry"

The hook uses a two-stage check (both cheap, <1ms):

1. **File mtime** — if the notebook file itself was modified within 24 hours, the commit is allowed.
2. **Date stamp scan** — if the file hasn't been touched recently, the hook scans for a `YYYY-MM-DD` pattern matching today or yesterday anywhere in the file. This catches cases where an existing entry was appended earlier today without changing mtime.

Either check passing → commit proceeds. Both failing → commit blocked.

### Bypass

To skip enforcement on a specific commit (e.g., a docs-only change where a new notebook entry is genuinely not warranted):

```bash
git commit --no-verify
```

This bypasses all git hooks, including the lab-notebook gate. Use it deliberately, not habitually — the intent is to make skipping a conscious choice, not an obstacle.

### Enforcement message

When blocked, the hook prints:

```
LAB_NOTEBOOK.md exists but has no entry in the last 24 hours.
Update it before committing (Rule 11 from lab-notebook CLAUDE.md section).

To bypass: git commit --no-verify
```

### Hook implementation

Script: `plugins/personal-plugin/hooks/scripts/lab-notebook-gate.sh`
Hook entry: `PreToolUse` → `Bash` matcher in `hooks/hooks.json`

---

## What Makes This Work

**Three layers of enforcement:**

1. **CLAUDE.md rules** (highest priority instruction layer) — survive session crashes, context compression, and new conversations. Written as blocking preconditions, not suggestions. 11 rules covering the full lifecycle from hypothesis to follow-up, with Rule 11 tying logging to the git commit cycle to prevent batch-logging.

2. **Living sections** (Decision Log + Action Items at top of notebook) — force continuous maintenance, not just append-only logging. Decisions have lifecycle tracking (ACTIVE → SUPERSEDED). Action items have explicit status. Session boundaries mark context switches.

3. **Hypothesis-driven entries** — transform logging from "I did X" (activity log) into "I predicted Y, tried X, and learned Z" (scientific notebook). Forces thinking before acting. Success criteria make outcomes objective.

**Design principles:**
- **One file** — everything in LAB_NOTEBOOK.md. No separate ADR files, no external tracking systems. One file to read, one file to search.
- **Living + chronological** — dashboard tables at top for quick orientation, detailed entries below for full context. Both maintained simultaneously.
- **Required + optional sections** — every entry has Date/Tags/Environment/Hypothesis/Rollback/Actions. Sections like What Worked, Alternatives, Follow-ups are used when applicable, not forced on trivial entries.
- **Searchable via tags** — consistent project-specific + standard tags across entries enable "show me all [build] entries" or "all [performance] results."
- **Scales with complexity** — a simple benchmark gets a lightweight entry. A multi-day optimization saga gets detailed sub-entries with pattern tables. Same template, different depth.
- **Complements, doesn't replace** — works alongside LEARNINGS.md, PROGRESS files, git history, and other project notebooks. Each serves a different purpose.
