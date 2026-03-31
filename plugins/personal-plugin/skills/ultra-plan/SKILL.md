---
name: ultra-plan
description: "Structured implementation planning for bug lists, feature requests, or change sets. Enforces deep investigation, interaction mapping, and integrated solution design before any code changes. Use when given a list of issues/features/changes that need a cohesive implementation plan."
---

# Ultra Plan

ultrathink

Build a detailed, architecturally sound implementation plan for the provided issues, changes, updates, or features. This is a **rigid workflow** -- follow every phase in order. Do not skip phases or combine them. Each phase produces a distinct deliverable that gates the next.

## Inputs

The user provides one or more of:
- A bug list, feature request list, or change set
- A GitHub issue or PR with identified problems
- A review document or audit with findings
- Verbal description of needed changes

If the input is ambiguous or incomplete, ask clarifying questions before starting Phase 1.

## Phase 1 -- Investigation

For **each item** in the input list, investigate and document:

| Field | What to capture |
|-------|----------------|
| **Item** | The issue/feature as stated |
| **Root cause** | The structural reason this exists -- not the symptom. Ask "why" until you hit bedrock. |
| **Blast radius** | Every component, state, data flow, config, and contract this touches |
| **Current behavior** | What actually happens now (read the code, don't guess) |
| **Expected behavior** | What should happen after the fix/change |
| **Preserved assumptions** | Assumptions in existing code that the fix must not violate |
| **Risk** | What could go wrong if this is done poorly |

**Investigation rules:**
- Read the actual code. Trace the actual data flow. Grep for usages. Check callers and callees.
- Do not accept the first plausible explanation. Verify against reality.
- If an item seems simple, that's when you're most likely to miss something. Investigate anyway.
- Document what you found, including anything surprising.

Present Phase 1 findings as a structured table or list before proceeding.

## Phase 2 -- Interaction Mapping

Before proposing **any** solution, map the interactions:

### 2a. Item-to-Item Interactions
Build a matrix or dependency graph showing:
- Which items share code paths, state, data, or constraints
- Which items MUST be solved together (atomic change sets)
- Where fixing one item could break, complicate, or conflict with another
- Items that are actually the same root cause manifesting differently

### 2b. Change-to-System Interactions
For each potential change area:
- What upstream components feed into it
- What downstream components depend on it
- What configuration, environment, or runtime state it reads/writes
- What contracts (APIs, interfaces, data formats) it participates in

### 2c. Grouping
Group items into **coherent change sets** -- items that should be designed and implemented together because they share root causes, touch the same code, or have ordering dependencies.

Present the interaction map before proceeding. This is the most important phase -- it prevents the whack-a-mole fix loop.

## Phase 3 -- Solution Design

Design integrated changes for each change set from Phase 2.

**Design constraints:**
- Fit within the existing architecture and design intent
- Minimize technical debt -- no patches, no band-aids, no "we'll clean this up later"
- Each implementation step must leave the system in a working state
- Solve exactly what's needed -- if a broader refactor is warranted, **flag it separately** with rationale rather than embedding it silently
- Identify prerequisites and coordination requirements (changes that must ship together)
- Consider rollback: if something goes wrong, how do we undo it?

**For each change set, specify:**
1. What changes, where (files, functions, configs)
2. Why this approach over alternatives (trade-offs considered)
3. Implementation sequence within the set
4. Verification criteria -- how to confirm the change works

**Anti-patterns to avoid:**
- Patching symptoms instead of fixing root causes
- Changes that solve one item but create new problems for others
- Scope creep -- gold-plating or architectural rewrites beyond what's needed
- Implicit dependencies between change sets that aren't called out

## Phase 4 -- Summary Report

Deliver a structured summary containing all of the following:

### Investigation Findings
- Key discoveries per item -- what you found, what was surprising
- Any items that turned out to be duplicates or misdiagnosed

### Interaction Map
- Visual or tabular representation of item relationships
- Change set groupings with rationale

### Proposed Changes
- Organized by change set / area
- Each with: what, where, why, and trade-offs
- Flagged items: anything that needs broader refactoring (separate from the plan)

### Risk Assessment
- What could go wrong with each change set
- Rollback approach for each
- Items with highest uncertainty or risk

### Implementation Sequence
- Ordered list of change sets with dependencies
- Prerequisites and coordination requirements
- Suggested verification points (where to stop and test)

### Scope Boundaries
- What this plan covers
- What it explicitly does NOT cover (and why)
- Recommended follow-up work, if any

---

After presenting the summary report, ask:

> Review the plan above. You can approve as-is, adjust items, ask questions, or redirect. When ready, say **implement** and I'll generate the formal implementation plan.

## Phase 5 -- Plan Generation

When the user approves, produce a formal implementation plan using the appropriate command:

### 5a. Check for Existing Plans

Run `/personal-plugin:plan-next` first to assess the current repo state:
- Is there an existing IMPLEMENTATION_PLAN.md?
- Are there in-progress or pending work items?
- What's the current git state?

This determines the routing below.

### 5b. Route to Plan Command

| Situation | Action |
|-----------|--------|
| **No existing plan** | Invoke `/personal-plugin:create-plan`, feeding it the Phase 3 solution design as the requirements input. The investigation findings, interaction map, and change sets become the source material for plan generation. |
| **Existing plan, all items complete** | Invoke `/personal-plugin:create-plan` to append new phases to the existing plan. The new phases correspond to the change sets from Phase 3. |
| **Existing plan with pending/in-progress items** | Present the conflict to the user. Options: (1) append new phases after existing work, (2) replace the existing plan, (3) defer until current plan completes. Do not silently overwrite in-progress work. |

### 5c. Feed Ultra Plan Analysis into Create-Plan

The Phase 1-4 analysis is the requirements input for `/personal-plugin:create-plan`. Map ultra-plan outputs to create-plan inputs:

| Ultra Plan Output | Create-Plan Input |
|-------------------|-------------------|
| Change sets (Phase 2c) | Phase groupings |
| Solution design per set (Phase 3) | Work items with acceptance criteria |
| Implementation sequence (Phase 4) | Phase ordering and dependencies |
| Risk assessment (Phase 4) | Risk mitigation table |
| Scope boundaries (Phase 4) | Plan scope and exclusions |

The resulting IMPLEMENTATION_PLAN.md inherits the architectural coherence from ultra-plan's analysis -- it is NOT a fresh discovery process, but a structured encoding of decisions already made.

### 5d. Verify Plan Quality

After the plan is generated, verify:
- Every item from the approved Phase 4 summary appears in the plan
- Change set groupings are preserved (items that must ship together are in the same phase)
- The interaction dependencies from Phase 2 are reflected in phase ordering
- No items were silently dropped or split in a way that breaks atomic change sets

If anything is missing or misaligned, fix it before presenting the final plan.

### 5e. Present Final Plan

Report:
- Location of IMPLEMENTATION_PLAN.md
- Phase count and work item count
- Whether the plan was created fresh or appended to existing
- Next step: run `/personal-plugin:plan-next` or `/implement-plan` to begin execution
