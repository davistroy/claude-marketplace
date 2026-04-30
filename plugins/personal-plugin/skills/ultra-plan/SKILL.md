---
name: ultra-plan
description: "Structured implementation planning for bug lists, feature requests, or change sets. Enforces deep investigation, interaction mapping, and integrated solution design before any code changes. Use when given a list of issues/features/changes that need a cohesive implementation plan."
allowed-tools: Read, Glob, Grep, Agent
---

# Ultra Plan

ultrathink

Build a detailed, architecturally sound implementation plan for the provided issues, changes, updates, or features. This is a **rigid workflow** -- follow every phase in order. Do not skip phases or combine them. Each phase produces a distinct deliverable that gates the next.

> **See also:** `/create-plan` for requirements-driven planning. `/plan-improvements` for codebase analysis and improvement recommendations.

## Inputs

The user provides one or more of:
- A bug list, feature request list, or change set
- A GitHub issue or PR with identified problems
- A review document or audit with findings
- Verbal description of needed changes

If the input is ambiguous or incomplete, ask clarifying questions before starting Phase 0.

## Arguments

| Argument | Description |
|----------|-------------|
| (none) | Default mode: run the full rigid workflow (Phases 0-6) |
| `--refresh` | Drift detection mode: compare existing plan against current code state (see below) |

## Drift Detection Mode (`--refresh`)

When invoked with `--refresh`, ultra-plan skips the normal Phase 0-6 workflow and instead checks whether an existing plan still matches the codebase.

**Prerequisites:**
- IMPLEMENTATION_PLAN.md (or `--input <path>`) must exist
- If no plan file exists, report: "No implementation plan found. Run `/ultra-plan` to create one, or specify a path with `--refresh --input <path>`."

**Workflow:**

### Step 1: Read the Plan

Read the plan file. Extract all work items with their:
- Files Affected (expected file paths)
- Acceptance Criteria (expected behaviors)
- Status (PENDING, IN_PROGRESS, COMPLETE)

### Step 2: Check Each Item Against Code

For each work item (focus on COMPLETE items — they're most likely to drift):

1. **File existence:** Do the listed files still exist? Were any renamed or deleted?
2. **Acceptance criteria:** For COMPLETE items, do the acceptance criteria still hold? (Read the relevant code and check.)
3. **New code:** Has code been added in the affected areas that the plan doesn't account for?

For large plans (>8 items), use Explore sub-agents to parallelize the checks.

### Step 3: Produce Drift Report

| Work Item | Plan Status | Drift Status | Evidence | Recommended Action |
|-----------|-------------|--------------|----------|-------------------|
| [N.M] | COMPLETE | Accurate | [Files unchanged, criteria hold] | None |
| [N.M] | COMPLETE | Drifted | [File X was refactored; criterion Y no longer holds] | Update plan or re-verify |
| [N.M] | PENDING | Obsolete | [The problem was fixed by a different approach] | Remove from plan |
| [N.M] | — | New | [New file X.md was added, not in any plan item] | Add to plan or document as out-of-scope |

**Drift status values:**
- **Accurate**: Code matches what the plan describes
- **Drifted**: Code has diverged from the plan's expectations
- **Obsolete**: Plan item is no longer relevant (problem solved differently, feature removed, etc.)
- **New**: Code or files exist that the plan doesn't account for

### Step 4: Recommendations

Based on the drift report:
- If drift is minimal (≤2 items), suggest targeted plan updates
- If drift is significant (>30% of items), suggest re-running `/ultra-plan` from scratch
- For PENDING items that are now obsolete, suggest removing them

After the drift report, return to normal mode — do NOT proceed with Phase 0-6.

## Phase 0 -- Constitution Check

> **Note:** Phase 0-6 below is the default workflow. If invoked with `--refresh`, skip to the Drift Detection Mode section above.

Before investigating any items, establish the project's non-negotiable constraints. These constraints gate every subsequent phase -- no proposed solution may violate them.

**Skip conditions:** Skip Phase 0 entirely if (a) the user says "skip constitution", (b) the task is clearly L0-L1 scope per plan-gate classification, or (c) the input is a single well-scoped bug fix.

### 0a. Read Existing Constraints

Read CLAUDE.md (and any `constitution.md` if present) for documented project constraints. Look for:

| Category | What to find |
|----------|-------------|
| **Test policy** | Required coverage, test frameworks, "never skip tests" rules |
| **Deployment target** | Cloud provider, container runtime, edge constraints |
| **Stack lock-in** | Required languages, frameworks, versions, "do not add dependencies" rules |
| **Security non-negotiables** | Auth requirements, data handling rules, compliance standards |
| **Observability minimum** | Logging requirements, metric collection, alerting |
| **Definition of done baseline** | What "done" means for this project (PR required? Review required? CI must pass?) |
| **Data sovereignty** | Where data can be stored/processed, residency requirements |

### 0b. Fill Gaps (if needed)

If CLAUDE.md is comprehensive on most categories, note the constraints and proceed. If significant gaps exist (≥3 categories with no documented position), ask the user up to 7 targeted questions -- one per missing category. Frame each question with a sensible default:

> "I don't see a documented test policy. Default assumption: tests are encouraged but not gating. Is that correct, or do you have a stricter requirement?"

Record answers. These constraints apply to all subsequent phases.

### 0c. Output

Produce a **Constraints Summary** -- a compact table of all documented and answered constraints. This summary:
- Feeds into the Summary Report (Phase 5) as "Pre-Plan Gates"
- Is checked during Solution Design (Phase 4) -- every proposed change must comply
- Is included in the plan generation output for downstream consumption

## Phase 2 -- Investigation

For **each item** in the input list, investigate and document:

**Scale gate:** If the input contains **>5 items**, spawn Explore sub-agents for parallel investigation (see below). For **≤5 items**, investigate inline using the table below.

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

Present Phase 2 findings as a structured table or list before proceeding.

### Sub-Agent Investigation (>5 items)

When the input list has more than 5 items, use the Agent tool with `subagent_type: "Explore"` to parallelize investigation. This preserves main context for the high-value Phases 3-6.

**Dispatch pattern:**
1. Group related items (items that likely share code paths) into clusters of 2-3
2. For each cluster, spawn an Explore sub-agent with this prompt template:

> Investigate these items in the codebase at [project root]. For each item, find and document:
> - **Root cause:** The structural reason this exists (trace the code, don't guess)
> - **Blast radius:** Every component, state, data flow, and contract this touches
> - **Current behavior:** What actually happens now (read the actual code)
> - **Expected behavior:** What should happen after the fix/change
> - **Preserved assumptions:** Assumptions the fix must not violate
> - **Risk:** What could go wrong if done poorly
>
> Items to investigate:
> [list items in this cluster]
>
> Return findings as a structured table with one row per item.

3. Launch sub-agents in parallel using `run_in_background: true`
4. Collect results as each completes
5. Merge all findings into a single Phase 2 deliverable before proceeding to Phase 3

**Graceful degradation:** If the Agent tool is unavailable or sub-agents fail, fall back to inline investigation for all items. Note the fallback in the Phase 2 output.

## Phase 3 -- Interaction Mapping

Before proposing **any** solution, map the interactions:

### 3a. Item-to-Item Interactions
Build a matrix or dependency graph showing:
- Which items share code paths, state, data, or constraints
- Which items MUST be solved together (atomic change sets)
- Where fixing one item could break, complicate, or conflict with another
- Items that are actually the same root cause manifesting differently

### 3b. Change-to-System Interactions
For each potential change area:
- What upstream components feed into it
- What downstream components depend on it
- What configuration, environment, or runtime state it reads/writes
- What contracts (APIs, interfaces, data formats) it participates in

### 3c. Grouping
Group items into **coherent change sets** -- items that should be designed and implemented together because they share root causes, touch the same code, or have ordering dependencies.

Present the interaction map before proceeding. This is the most important phase -- it prevents the whack-a-mole fix loop.

## Phase 4 -- Solution Design

Design integrated changes for each change set from Phase 3.

**Design constraints:**
- Fit within the existing architecture and design intent
- Minimize technical debt -- no patches, no band-aids, no "we'll clean this up later"
- Each implementation step must leave the system in a working state
- Solve exactly what's needed -- if a broader refactor is warranted, **flag it separately** with rationale rather than embedding it silently
- Identify prerequisites and coordination requirements (changes that must ship together)
- Consider rollback: if something goes wrong, how do we undo it?
- Comply with all constraints from Phase 0 -- if a proposed solution would violate a documented constraint, flag it explicitly rather than proceeding

**For each change set, specify:**
1. What changes, where (files, functions, configs)
2. Why this approach over alternatives (trade-offs considered)
3. Implementation sequence within the set
4. Verification criteria -- how to confirm the change works
5. Verification commands -- specific runnable commands that confirm the change works (e.g., `pytest tests/test_auth.py -v`, `ruff check src/auth/`). These feed into the plan's Definition of Done section.

**Anti-patterns to avoid:**
- Patching symptoms instead of fixing root causes
- Changes that solve one item but create new problems for others
- Scope creep — gold-plating or architectural rewrites beyond what's needed
- Implicit dependencies between change sets that aren't called out

See `references/anti-patterns.md` for the full catalog with detection heuristics and mitigation strategies.

### ADR Generation (L3+ tasks)

For each change set that involves choosing between fundamentally different approaches (not minor implementation variants), generate an Architecture Decision Record:

**Trigger question:** "Does this change set involve an architectural decision that should outlive the plan — a choice between fundamentally different approaches where the reasoning matters for future developers?"

**If yes:**
1. Create `docs/adr/ADR-NNNN-[slug].md` using the template from `references/adr-template.md`
2. Populate Context from Phase 2 investigation findings
3. Populate Decision from the chosen approach in Phase 4
4. Populate Alternatives from the rejected approaches with specific rejection reasons
5. Set Status to "Proposed"
6. List the generated ADR in the Phase 5 Summary Report

**Skip conditions:** Skip ADR generation when the task is L0-L2 (per plan-gate classification) AND the user hasn't explicitly requested it. Simple implementation decisions (naming, file organization, configuration values) don't need ADRs.

### Creative Branching (L4+ tasks)

For L4+ tasks (greenfield architecture, multi-system integration, fundamental redesign) where **2-3 fundamentally different valid approaches** exist, generate a comparison table before committing to one approach.

**Trigger question:** "Are there 2+ fundamentally different architectures that could solve this, where the choice has lasting consequences?" If yes, and the task is L4+ scope, branch.

**Skip conditions:** Skip when (a) the task is L0-L3, (b) there is only one viable approach, or (c) the differences between approaches are minor implementation variants rather than fundamentally different architectures.

**Comparison table format:**

| Dimension | [Approach A] | [Approach B] | [Approach C] |
|-----------|-------------|-------------|-------------|
| Architecture | [High-level design] | [High-level design] | [High-level design] |
| Estimated Effort | [S/M/L] | [S/M/L] | [S/M/L] |
| Risk Level | [Low/Med/High] | [Low/Med/High] | [Low/Med/High] |
| Pros | [Key advantages] | [Key advantages] | [Key advantages] |
| Cons | [Key disadvantages] | [Key disadvantages] | [Key disadvantages] |
| Best When | [Conditions favoring this approach] | [Conditions] | [Conditions] |

**After presenting the table:**

1. Ask the user to pick an approach (or suggest a hybrid)
2. Generate the solution design for the chosen approach
3. Generate an ADR documenting the decision (leverages the ADR Generation section above)
4. Rejected approaches become "Alternatives Considered" in the ADR

## Phase 5 -- Summary Report

Deliver a structured summary containing all of the following:

### Pre-Plan Gates
- Constraints summary from Phase 0
- Compliance check: verify every proposed change in Phase 4 respects documented constraints
- Flag any proposed change that conflicts with a constraint -- present the conflict and ask the user to decide

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

### Unknowns
- Epistemic uncertainties identified during investigation and solution design
- For each unknown: what we don't know, severity (High/Medium/Low), which phase/item it affects, and a resolution strategy
- High-severity unknowns should be resolved before the affected phase begins
- Distinct from risks: unknowns are knowledge gaps, risks are probabilistic events

### Implementation Sequence
- Ordered list of change sets with dependencies
- Prerequisites and coordination requirements
- Suggested verification points (where to stop and test)

### Scope Boundaries
- What this plan covers
- What it explicitly does NOT cover (and why)
- Recommended follow-up work, if any

### Verification Commands
- All runnable verification commands specified per change set in Phase 4
- These feed into the plan's Definition of Done (Runnable) section when generated via create-plan
- Organized by change set: list the Check name and Command for each

### Generated ADRs (if any)
- List of ADR files generated during Phase 4
- Each with: ADR number, title, status (Proposed), and the change set it documents
- Note: ADRs are generated only for L3+ tasks; this section may be empty for smaller scopes

---

After presenting the summary report, ask:

> Review the plan above. You can approve as-is, adjust items, ask questions, or redirect. When ready, say **implement** and I'll generate the formal implementation plan.

## Phase 6 -- Plan Generation

When the user approves, produce a formal implementation plan using the appropriate command:

### 6a. Check for Existing Plans

Run `/personal-plugin:plan-next` first to assess the current repo state:
- Is there an existing IMPLEMENTATION_PLAN.md?
- Are there in-progress or pending work items?
- What's the current git state?

This determines the routing below.

### 6b. Route to Plan Command

| Situation | Action |
|-----------|--------|
| **No existing plan** | Invoke `/personal-plugin:create-plan`, feeding it the Phase 4 solution design as the requirements input. The investigation findings, interaction map, and change sets become the source material for plan generation. |
| **Existing plan, all items complete** | Invoke `/personal-plugin:create-plan` to append new phases to the existing plan. The new phases correspond to the change sets from Phase 4. |
| **Existing plan with pending/in-progress items** | Present the conflict to the user. Options: (1) append new phases after existing work, (2) replace the existing plan, (3) defer until current plan completes. Do not silently overwrite in-progress work. |

### 6c. Feed Ultra Plan Analysis into Create-Plan

The Phase 2-5 analysis is the requirements input for `/personal-plugin:create-plan`. Map ultra-plan outputs to create-plan inputs:

| Ultra Plan Output | Create-Plan Input |
|-------------------|-------------------|
| Change sets (Phase 3c) | Phase groupings |
| Solution design per set (Phase 4) | Work items with acceptance criteria |
| Implementation sequence (Phase 5) | Phase ordering and dependencies |
| Risk assessment (Phase 5) | Risk mitigation table |
| Scope boundaries (Phase 5) | Plan scope and exclusions |
| Unknowns (Phase 5) | Unknowns Register |
| Verification commands (Phase 5) | Definition of Done (Runnable) per phase |

The resulting IMPLEMENTATION_PLAN.md inherits the architectural coherence from ultra-plan's analysis -- it is NOT a fresh discovery process, but a structured encoding of decisions already made.

### 6d. Verify Plan Quality

After the plan is generated, verify:
- Every item from the approved Phase 5 summary appears in the plan
- Change set groupings are preserved (items that must ship together are in the same phase)
- The interaction dependencies from Phase 3 are reflected in phase ordering
- No items were silently dropped or split in a way that breaks atomic change sets

If anything is missing or misaligned, fix it before presenting the final plan.

### 6e. Present Final Plan

Report:
- Location of IMPLEMENTATION_PLAN.md
- Phase count and work item count
- Whether the plan was created fresh or appended to existing
- Next step: run `/personal-plugin:plan-next` or `/implement-plan` to begin execution
