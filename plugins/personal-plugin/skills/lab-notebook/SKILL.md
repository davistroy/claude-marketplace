---
name: lab-notebook
description: Initialize mandatory experiment logging using scientific notebook, ADR, and postmortem patterns. For projects involving system changes, benchmarks, debugging, or exploratory work. Creates LAB_NOTEBOOK.md with living decision/action tracking and injects iron-clad CLAUDE.md rules that make logging a PRECONDITION for every action. Suggest when — infrastructure/experimental/expensive-failure projects, multi-session work, or keywords like optimize/benchmark/debug/configure. Confirms before writing anything when suggested rather than invoked.
effort: medium
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), AskUserQuestion
---

# Lab Notebook

Establish mandatory, structured experiment logging for a project. Once initialized, every system modification, benchmark, configuration change, build attempt, and debugging step MUST be logged in `LAB_NOTEBOOK.md` — no exceptions.

The notebook combines three proven documentation patterns:
- **Scientific lab notebook** — hypothesis-driven entries with environment context and reproducibility
- **Architecture Decision Records** — decisions with alternatives considered and lifecycle tracking
- **Incident postmortem** — blameless failure analysis, action items, and "what went well"

## Input

**Arguments:** `$ARGUMENTS`

Supported arguments:
- `init` — Full initialization: discover prior work, create LAB_NOTEBOOK.md, inject CLAUDE.md rules
- `entry "title"` — Add a new numbered entry to an existing notebook
- `status` — Show notebook health: entries, staleness, open action items, active decisions
- `rotate` — Archive the oldest experiment entries to `docs/archive/` once the log grows large, keeping the living sections and recent entries. Preserves every decision (a move, never a delete).
- No arguments — Same as `init` if no notebook exists, same as `status` if one does

## Phase 0: Self-Invocation Confirmation

**This skill can be model-invoked, and every mode except `status` writes to the project** —
`init` creates `LAB_NOTEBOOK.md` *and* injects binding rules into `CLAUDE.md`; `entry`
appends; `rotate` moves entries into `docs/archive/`. None of that may happen unasked.

**If you are invoking this skill on your own initiative** — because the work looks
experimental, a benchmark is starting, or the user said something like "I keep losing track
of what I tried" — rather than the user typing `/lab-notebook`, confirm first with
`AskUserQuestion`:

```json
{
  "questions": [
    {
      "question": "Set up a lab notebook for this project?",
      "header": "Notebook",
      "multiSelect": false,
      "options": [
        {
          "label": "Yes, initialize it",
          "description": "Creates LAB_NOTEBOOK.md and adds logging rules to CLAUDE.md that make an entry a precondition for every system-modifying action"
        },
        {
          "label": "No, not now",
          "description": "Nothing is written; you can run /lab-notebook yourself at any time"
        }
      ]
    }
  ]
}
```

- **Confirmed:** proceed with the instructions below.
- **Declined or skipped:** reply "Skipped — run `/lab-notebook` whenever you want one." and
  exit immediately. Create nothing, modify nothing.

**When the user invokes this skill directly, skip this gate entirely** and proceed. `status`
is read-only and never needs the gate.

---

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

**Full structure:** Read [`references/notebook-structure-template.md`](references/notebook-structure-template.md) — in this skill's own `references/` directory, alongside `rotation.md` — and emit its `## Template` fenced block verbatim as the new `LAB_NOTEBOOK.md`, filling in the `{braced}` placeholders from Step 1's discovery. It defines, in order: a header block (`# {Project Name} — Lab Notebook` + Project/Started/Systems), the **Decision Log** table (# / Decision / Date / Status / Entry / Alternatives Considered), the **Action Items** Open + Completed tables, the **Prior Work Summary** and **Current Baseline** narrative sections, and the **Experiment Log** with a first `### Entry 001` containing Date/Duration/Environment/Status, Objective, Hypothesis, Rollback Plan, Actions & Results, What Worked, What Failed, Decision + Alternatives Considered, and Follow-ups.

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

**The CLAUDE.md section to inject:** Read [`references/claude-md-injection-template.md`](references/claude-md-injection-template.md) — in this skill's own `references/` directory, alongside `rotation.md` — and emit its `## Template` fenced block verbatim as the appended (or new) CLAUDE.md section. It defines `## Lab Notebook — MANDATORY Logging Protocol` with 11 numbered rules plus an Enforcement summary:

1. Hypothesize, Plan Rollback, THEN Act — every system-modifying action needs an entry with Objective, Hypothesis (with success criteria), and Rollback Plan *before* it runs.
2. Log Results As They Happen — exact command, result, raw error output on failure, performance numbers, environment context; never batch after the fact.
3. Analyze Failures — Root Cause, Not Symptoms — exact error, root cause, system insight, next approach, and a pattern table when a failure class recurs.
4. Document Decisions with Alternatives — decision + why + alternatives considered, always mirrored into the Decision Log table; supersede, never delete.
5. Track What Worked, Not Just What Failed — a "What Worked" section for mixed-outcome entries, to prevent drift toward excessive caution.
6. Write Before Risky Operations — flush all findings before anything that could crash the session or take a long time, so a crash is recoverable from the notebook alone.
7. Maintain Living Sections — Decision Log and Action Items updated after every entry; rotate past ~40 entries via the notebook's own `rotate` operation.
8. Tag and Contextualize Every Entry — Tags, Environment, and Duration (on completion) on every entry.
9. Pattern Tables for Repeated Issues — consolidate same-root-cause failures into an Attempt/Error/Root Cause/Fix table.
10. Session Boundaries — a `--- New session: {date} — {context} ---` marker before the first entry of a new session.
11. Log Before You Commit — BLOCKING PRECONDITION on `git commit` touching application code: a current notebook entry must exist first, not be backfilled after.

**Enforcement** closes the template: rules are blocking preconditions, not suggestions, with no exceptions for "quick," "obvious," or "simple" changes.

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

Also report **rotation health**: if the Experiment Log exceeds **~40 entries or LAB_NOTEBOOK.md exceeds ~1200 lines**, recommend `/lab-notebook rotate` (the mandatory first-read is getting expensive).

### On `rotate`:

Archive the oldest entries once the log grows large, so the mandatory first-read stays cheap. A MOVE (archive + bidirectional pointers), never a delete (Rule 4). **Full procedure: [`references/rotation.md`](references/rotation.md).** Load-bearing invariants, in order:

1. **Promote body-only decisions FIRST** — scan entries being archived for decisions in entry bodies only (`**Decision (Dxx):**`, `Dxx:` bullets) that are not yet Decision Log rows; promote them before archiving, or the archive silently removes live decisions (this nearly lost D14–D18).
2. **Cut at a session-marker boundary** (`--- New session:`), never mid-session/entry; keep ~20 recent entries plus all living sections.
3. **`git add -f` the archive** — `docs/archive/` is matched by a global gitignore, so plain `git add` skips new archive files.
4. Banner + back-pointer in the archive, forward pointer in the live notebook; re-point external prose refs to archived entries.
5. **Verify before commit:** Decision Log contiguous (no gaps), archive entry count == removed, zero live/archive overlap, both markdownlint-clean.

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

```text
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
