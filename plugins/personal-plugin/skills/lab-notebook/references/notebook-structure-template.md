# LAB_NOTEBOOK.md Structure Template

**Purpose:** Verbatim skeleton emitted by `skills/lab-notebook/SKILL.md` Step 2 when creating a new project's `LAB_NOTEBOOK.md`. Content must be copied byte-for-byte — do not paraphrase or reformat. Placeholders in `{braces}` are filled in per-project; everything else (headings, table columns, section order) is fixed structure.

**Consumer:** `skills/lab-notebook/SKILL.md` — Step 2 ("Create LAB_NOTEBOOK.md").

---

## Template

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
