---
name: plan-gate
description: Before starting complex multi-step implementation tasks, assess scope and route to the right planning approach — native plan mode for simple changes, /plan-improvements for codebase refactoring, or /create-plan for requirements-driven work
---

# Plan Gate

Proactively assess task complexity before implementation begins and route to the appropriate planning mechanism. This skill acts as a lightweight decision point that prevents both under-planning (jumping straight into code on a multi-phase effort) and over-planning (running a full `/plan-improvements` cycle for a simple bug fix).

**This skill is read-only. It NEVER modifies files, commits, or pushes.**

## When This Skill Should Fire

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

Then enter plan mode using `EnterPlanMode`.

#### Path C: /plan-improvements

**When:** Task involves improving or refactoring existing code, no formal requirements docs, need to analyze current state first.

```text
Scope Assessment
================
This is a multi-phase effort that needs structured planning. It involves
improving existing code, so I should analyze the codebase first to produce
prioritized recommendations and a phased implementation plan.

Recommended: /plan-improvements
  - Generates RECOMMENDATIONS.md with prioritized findings
  - Generates IMPLEMENTATION_PLAN.md with phased work items
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
  - Synthesizes requirements across all documents
  - Generates phased IMPLEMENTATION_PLAN.md
  - Execute later with /implement-plan

Shall I run /create-plan now?
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

Use `AskUserQuestion` to get the answers, then re-assess.

### Step 4: Execute or Hand Off

- **Path A**: Start working immediately
- **Path B**: Call `EnterPlanMode`
- **Paths C/D/E**: Ask the user for confirmation, then invoke the appropriate command
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
   Requirements docs (PRD/BRD/TDD) exist?
    YES --> Path D: /create-plan
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

## Performance

This skill should complete in under 10 seconds. It is a routing decision, not an analysis tool. If you find yourself reading more than 5 files, you're doing too much — pick a path and let the downstream command do the heavy lifting.
