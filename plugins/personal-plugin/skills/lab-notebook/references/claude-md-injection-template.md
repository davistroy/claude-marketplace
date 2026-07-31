# CLAUDE.md Lab Notebook Injection Template

**Purpose:** Verbatim CLAUDE.md injection block emitted by `skills/lab-notebook/SKILL.md` Step 3 — the 11 mandatory logging rules appended to a project's CLAUDE.md so logging becomes a blocking precondition on every system-modifying action. Content must be copied byte-for-byte — do not paraphrase or reformat. Adapt examples and tag lists to the target project **before** injecting, per Step 3's instructions in SKILL.md, not by editing this file.

**Consumer:** `skills/lab-notebook/SKILL.md` — Step 3 ("Inject CLAUDE.md Lab Notebook Section").

---

## Template

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

These tables are the "dashboard" — they must always reflect the current state. When the Experiment Log grows past ~40 entries, archive the oldest to `docs/archive/` via the notebook's `rotate` operation — a MOVE that promotes any body-only decisions into the Decision Log first, never a delete.

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
