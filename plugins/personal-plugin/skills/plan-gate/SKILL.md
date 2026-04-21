---
name: plan-gate
description: Before starting complex multi-step implementation tasks, assess scope and route to the right planning approach — native plan mode for simple changes, /plan-improvements for codebase refactoring, or /create-plan for requirements-driven work
effort: low
allowed-tools: Read, Glob, Grep
---

# Plan Gate

Proactively assess task complexity before implementation begins and route to the appropriate planning mechanism. This skill acts as a lightweight decision point that prevents both under-planning (jumping straight into code on a multi-phase effort) and over-planning (running a full `/plan-improvements` cycle for a simple bug fix).

**This skill is read-only. It NEVER modifies files, commits, or pushes.**

## Proactive Triggers

Claude should proactively suggest this skill when ALL of these are true:

1. The user has requested an implementation task (not research, not a question)
2. The task appears non-trivial — any of these signals:
   - Will likely touch more than 3 files
   - Involves architectural decisions or trade-offs
   - Requires phased delivery or has internal dependencies
   - The user's description is ambiguous about scope
   - Multiple valid implementation approaches exist
   - The task mentions "refactor", "redesign", "overhaul", "migrate", "add feature", or similar scope indicators
3. No planning has been done yet (no active IMPLEMENTATION_PLAN.md for this work)

**Do NOT fire when:**
- The task is a single-file fix, typo, or small tweak
- The user has already invoked a planning command
- The user explicitly says "just do it" or "skip planning"
- The task is purely research or exploration

## Instructions

### Step 1: Quick Scope Assessment

Spend no more than 30 seconds on this. Do NOT do a deep codebase analysis — that's what the planning commands are for. Just answer these questions by scanning the request and doing minimal file checks:

**Task Signals:**

| Signal | Check |
|--------|-------|
| Files affected | Will this touch > 3 files? > 10 files? |
| Phasing needed | Can this be done in one pass, or does it need stages? |
| Dependencies | Are there ordering constraints between sub-tasks? |
| Ambiguity | Is the scope clearly defined, or does it need scoping? |
| Requirements docs | Do BRD/PRD/TDD files exist in the repo? |
| Existing plan | Does IMPLEMENTATION_PLAN.md already exist? |
| Codebase familiarity | Has `/prime` been run recently? Is CLAUDE.md comprehensive? |

### Step 2: Check for Existing Artifacts

Quickly check for these files (Glob, not deep reads):

```
IMPLEMENTATION_PLAN.md    # Existing plan — may just need /implement-plan
RECOMMENDATIONS.md        # Previous analysis — plan may already exist
PROGRESS.md               # Active execution — plan is in flight
PRD*.md, BRD*.md, TDD*.md # Requirements docs — /create-plan is appropriate
docs/requirements/*.md    # Requirements in docs folder
```

### Step 3: Route to the Right Approach

Based on the assessment, recommend ONE of these paths:

#### Path A: Just Do It (No Planning Needed)

**When:** Task is clearly scoped, touches 1-3 files, no ambiguity, single-session work.

```text
This looks straightforward — I'll proceed directly.
```

Do not display the routing table below. Just start working.

#### Path B: Native Plan Mode

**When:** Task is moderate (4-8 files), single feature, fits in one session, no requirements docs to synthesize.

```text
Scope Assessment
================
This task is moderate in scope — it will touch several files but fits within
a single session. I'll enter plan mode to design the approach before coding.

Recommended: Native plan mode (interactive, immediate)
```

Then enter plan mode to design the approach before coding.

#### Path B.5: /batch (Parallel Decomposition)

**When:** Task naturally decomposes into 5–30 independent units that can run concurrently with no ordering constraints between them. Each unit is self-contained — no unit's output feeds another's input. Examples: running the same transformation across many files, migrating multiple independent endpoints, updating 10+ skill frontmatter fields with the same pattern.

Signals: user description contains "each", "all N of", "across all", "for every"; task is essentially the same operation repeated across multiple discrete targets.

```text
Scope Assessment
================
This task decomposes into [N] independent units that can run concurrently.
Sequential execution is unnecessary — there are no ordering constraints
between units.

Recommended: /batch
  - Dispatches one background agent per unit (up to 30)
  - Each agent runs in its own isolated worktree
  - Completes in parallel rather than sequentially
  - Suitable when units are fully independent (no shared state)

Trade-off: /batch loses visibility into per-unit progress in real time.
If you need step-by-step review, use Path B (native plan mode) instead.

Shall I decompose and dispatch via /batch?
```

#### Path C: /plan-improvements

**When:** Task involves improving or refactoring existing code, no formal requirements docs, need to analyze current state first.

```text
Scope Assessment
================
This is a multi-phase effort that needs structured planning. It involves
improving existing code, so I should analyze the codebase first to produce
prioritized recommendations and a phased implementation plan.

Recommended: /plan-improvements
  - Deep investigation of root causes and interrelationships between issues
  - Generates RECOMMENDATIONS.md with integrated, architecturally coherent fixes
  - Generates IMPLEMENTATION_PLAN.md with phased work items
  - Produces cohesive changes, not isolated patches
  - Execute later with /implement-plan

Estimated planning time: [size-based estimate]

Shall I run /plan-improvements now?
```

#### Path D: /create-plan

**When:** Requirements documents (BRD, PRD, TDD) exist in the repo — the task is requirements-driven, not codebase-driven.

```text
Scope Assessment
================
I found requirements documents that should drive this implementation:
  - [list discovered docs]

The right approach is to generate a structured implementation plan from
these requirements.

Recommended: /create-plan
  - Deep investigation of each requirement's impact and dependencies
  - Maps interrelationships between requirements to avoid conflicting changes
  - Synthesizes requirements into integrated, architecturally coherent phases
  - Generates phased IMPLEMENTATION_PLAN.md
  - Execute later with /implement-plan

Shall I run /create-plan now?
```

#### Path D.5: /ultraplan (Deep Pre-Planning)

**When:** Task needs more than 30 minutes of planning OR involves a high-risk architectural decision where getting the design wrong is expensive. Use when the scope is clear enough to know it's large, but the *approach* is uncertain — competing valid architectures, significant unknowns, or the task will shape work for weeks.

Signals: user says "I'm not sure how to approach", "there are a few ways we could do this", "this needs careful design"; task involves replacing a core system, choosing between fundamentally different architectures, or integrating a new platform/protocol.

```text
Scope Assessment
================
This task involves [architectural complexity / scope / unknowns]. Before
generating an implementation plan, a deep pre-planning pass is warranted
to evaluate competing approaches and surface hidden constraints.

Recommended: /ultraplan
  - Multi-agent structured analysis of the problem space
  - Evaluates trade-offs across competing approaches
  - Surfaces dependencies and risk factors before committing to a path
  - Produces a design decision record + recommended implementation strategy
  - Run /create-plan or /plan-improvements after /ultraplan to generate IMPLEMENTATION_PLAN.md

When to skip: If you already know the approach and just need a plan, go
directly to /create-plan or /plan-improvements (Path C or D).

Shall I run /ultraplan for pre-planning analysis?
```

#### Path E: /implement-plan (Resume)

**When:** IMPLEMENTATION_PLAN.md already exists with incomplete work items.

```text
Scope Assessment
================
An existing implementation plan was found with work remaining:
  - IMPLEMENTATION_PLAN.md: [N] phases, [M] items incomplete
  - Last progress: [date from PROGRESS.md if exists]

Recommended: /implement-plan (resume execution)

Shall I continue executing the existing plan?
```

#### Path F: Needs Scoping First

**When:** The request is too vague to route confidently. Need more information before choosing a path.

```text
Scope Assessment
================
This task could go several directions depending on scope. Before I can
recommend the right planning approach, I need to understand:

1. [Specific clarifying question]
2. [Specific clarifying question]

Once clarified, I'll route to the appropriate planning tool.
```

Ask the user clarifying questions to get the answers, then re-assess.

### Step 4: Execute or Hand Off

- **Path A**: Start working immediately
- **Path B**: Enter plan mode
- **Path B.5**: Confirm unit decomposition with user, then invoke `/batch`
- **Paths C/D/E**: Ask the user for confirmation, then invoke the appropriate command
- **Path D.5**: Ask the user for confirmation, then invoke `/ultraplan`; after completion route to Path C or D for plan generation
- **Path F**: Ask clarifying questions, then re-route

## Decision Flowchart

```text
User requests implementation task
         |
         v
   Trivial? (1-3 files, obvious approach)
    YES --> Path A: Just do it
    NO  |
        v
   IMPLEMENTATION_PLAN.md exists with incomplete items?
    YES --> Path E: /implement-plan (resume)
    NO  |
        v
   5-30 fully independent parallel units? (same op repeated, no cross-deps)
    YES --> Path B.5: /batch
    NO  |
        v
   Requirements docs (PRD/BRD/TDD) exist?
    YES --> Path D: /create-plan
    NO  |
        v
   High-risk architectural decision or >30-min planning needed?
    YES --> Path D.5: /ultraplan
    NO  |
        v
   Multi-phase? (>8 files, phased delivery, architectural changes)
    YES --> Path C: /plan-improvements
    NO  |
        v
   Moderate scope? (4-8 files, single feature)
    YES --> Path B: Native plan mode
    NO  |
        v
   Unclear scope?
    YES --> Path F: Ask clarifying questions
    NO  --> Path A: Just do it
```

## Examples

### Example 1: Simple bug fix
```text
User: "Fix the typo in the README"
Plan Gate: [Does not fire — trivial task]
```

### Example 2: Moderate feature
```text
User: "Add a --verbose flag to the validate-plugin command"
Plan Gate:
  Scope Assessment: Moderate — touches the command file, possibly validation
  logic, and help docs. ~4-5 files.
  Route: Path B (native plan mode)
```

### Example 3: Major refactoring
```text
User: "Refactor the BPMN plugin to support collaborative editing"
Plan Gate:
  Scope Assessment: Multi-phase — new architecture patterns, multiple
  components, testing infrastructure. 15+ files.
  Route: Path C (/plan-improvements)
```

### Example 4: Requirements-driven build
```text
User: "Build the app described in the PRD"
Plan Gate:
  Found: PRD.md (4,200 words), TDD.md (5,100 words)
  Route: Path D (/create-plan)
```

### Example 5: Continuing previous work
```text
User: "Let's keep working on the implementation"
Plan Gate:
  Found: IMPLEMENTATION_PLAN.md (12 items, 8 incomplete)
  Route: Path E (/implement-plan)
```

### Example 6: Large parallel refactor (Path B.5)
```text
User: "Update the paths: frontmatter field in all 23 skills across both plugins to use the new glob syntax"
Plan Gate:
  Scope Assessment: 23 files, all receiving the same structural frontmatter
  change with no ordering constraints between them. Each skill is independent.
  Route: Path B.5 (/batch)
  Decomposition: 23 units, one per skill file, dispatched concurrently.
```

### Example 7: Deep architectural decision (Path D.5)
```text
User: "I need to decide whether to keep the Python research orchestrator or replace it with native subagent dispatch — and then build whichever we choose"
Plan Gate:
  Scope Assessment: Two competing architectures with significant trade-offs
  (streaming progress vs. dependency elimination). Getting this wrong is
  expensive — the Python tool has 20+ files. Approach is unclear.
  Route: Path D.5 (/ultraplan)
  Reason: Pre-planning analysis needed before committing to an approach.
  After /ultraplan, run /create-plan to generate IMPLEMENTATION_PLAN.md.
```

## Error Handling

| Condition | Cause | Action |
|-----------|-------|--------|
| Cannot determine task scope | User request is too vague or ambiguous to classify | Route to Path F (Needs Scoping First) and ask specific clarifying questions before recommending a planning approach |
| IMPLEMENTATION_PLAN.md exists but is corrupt or unparseable | Malformed markdown or missing expected sections | Warn: "Found IMPLEMENTATION_PLAN.md but could not parse it. Treat as if no plan exists and route based on the task description." |
| Glob tool unavailable | Tool restrictions prevent file discovery | Skip Step 2 (artifact checks) and route based solely on the user's request description. Note: "Could not check for existing artifacts — routing based on task description only." |
| Multiple conflicting artifacts found | Both requirements docs and IMPLEMENTATION_PLAN.md exist with different scopes | Present both options to the user: "Found existing plan AND requirements docs. Would you like to resume the existing plan (Path E) or create a new plan from requirements (Path D)?" |
| Skill fires inappropriately | Task is trivial but scope signals were ambiguous | Self-correct quickly: "On closer look, this is straightforward — proceeding directly." Route to Path A without further ceremony. |

## Performance

This skill should complete in under 10 seconds. It is a routing decision, not an analysis tool. If you find yourself reading more than 5 files, you're doing too much — pick a path and let the downstream command do the heavy lifting.
