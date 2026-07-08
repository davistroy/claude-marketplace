---
description: Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs)
argument-hint: "[<document-paths>...] [--output <path>] [--phases <n>]"
effort: max
allowed-tools: Read, Glob, Grep, Write, Edit, Agent, Bash(git:*)
---

# Create Plan Command

Generate a comprehensive, phased implementation plan from requirements and design documents in the project. This command discovers and analyzes BRDs, PRDs, TDDs, and other specification documents, then produces an actionable IMPLEMENTATION_PLAN.md ready for execution with `/implement-plan`.

## Overview

This command:

1. Discovers requirements and design documents in the project
2. Surveys the existing codebase to detect tech stack, test infrastructure, and already-implemented features
3. Analyzes and synthesizes requirements across all documents, accounting for existing code
4. Presents a scope summary (features, phases, assumptions) and waits for user approval before proceeding
5. Breaks down work into appropriately-sized phases
6. Generates detailed work items with acceptance criteria
7. Outputs IMPLEMENTATION_PLAN.md to the repository root

> **See also:** `/plan-improvements` for codebase-driven improvement analysis. `/ultra-plan` for deep pre-planning when requirements are vague, scope is ambiguous, or the problem needs investigation before a plan can be written. Use `/implement-plan` to execute the generated plan; for large plans (6+ phases or 20+ independent work items), set `Execution Mode: Parallel` or `Worktree-Isolated` in the Phase Summary Table so `/implement-plan` dispatches those phases as concurrent background agents in isolated worktrees.

## Input Validation

**Arguments:** None required

**Optional Arguments:**
- `<document-paths>` - Specific documents to use (space-separated)
- `--output <path>` - Custom output path (default: `IMPLEMENTATION_PLAN.md`)
- `--phases <n>` - Target number of phases (default: auto-calculated)
- `--max-phases <n>` - Maximum number of phases to generate (default: 8). Overrides `--phases` if `--phases` exceeds this limit.
- `--verbose` - Show detailed analysis during generation

**Examples:**
```text
/create-plan                              # Auto-discover documents
/create-plan PRD.md TDD.md               # Use specific documents
/create-plan --phases 5                   # Target 5 phases
/create-plan docs/requirements/*.md       # Use glob pattern
```

## Instructions

### Phase 1: Document Discovery

#### 1.1 Auto-Discovery Mode

When no documents are specified, search for requirements documents:

**Search patterns (in order of priority):** root-level named docs first (`PRD*.md`, `BRD*.md`, `TDD*.md`, `SRS*.md`, `FRD*.md`, plus `requirements.md`/`spec.md`/`design.md` and any `*.md` containing "requirements"/"specification"/"design"), then common doc directories (`docs/`, `documentation/`, `specs/`, `requirements/`, `design/`), then nested (`**/`) equivalents. See `references/create-plan-examples.md` → "Document Discovery: Search Patterns" for the full glob list.

**Document type detection by content:**
- **BRD (Business Requirements):** Contains "business requirements", "business objectives", "stakeholder", "ROI"
- **PRD (Product Requirements):** Contains "product requirements", "user stories", "features", "acceptance criteria"
- **TDD (Technical Design):** Contains "technical design", "architecture", "API", "database schema", "system design"
- **SRS (Software Requirements Spec):** Contains "software requirements", "functional requirements", "non-functional"
- **FRD (Functional Requirements):** Contains "functional requirements", "use cases", "business rules"

#### 1.2 Explicit Document Mode

When documents are specified as arguments:
1. Verify each file exists
2. Read and classify each document
3. Report any files not found

**Error if no documents found:** report that no requirements documents were found, list the searched locations, and show how to provide documents explicitly. See `references/create-plan-examples.md` → "Document Discovery: 'No documents found' error" for the display text.

#### 1.3 Document Inventory Report

Display discovered documents before proceeding, grouped by type (Business/Product/Technical/Other) with per-file word counts and a total, ending with a "Proceeding with plan generation..." line. See `references/create-plan-examples.md` → "Document Inventory Report" for the sample.

#### 1.4 Pre-Planning Quality Gate

After inventorying documents, perform a rapid quality scan **before** investing time in full analysis. Evaluate whether the inputs are ready for direct planning or require pre-planning investigation first.

**Trigger `/ultra-plan` instead if any of the following are true:**

Note: `/ultra-plan` is the personal-plugin deep pre-planning skill. Anthropic's built-in `/ultraplan` (no hyphen) is a distinct feature.

| Signal | Threshold | What to do |
|--------|-----------|------------|
| Vague requirements | >30% of features described with "TBD", "to be determined", "unclear", or missing acceptance criteria | Recommend `/ultra-plan` |
| Issue/bug list input | Documents consist primarily of bug reports, tickets, or issues rather than requirements | Recommend `/ultra-plan` |
| Scope ambiguity | Multiple conflicting scope boundaries or contradictory prioritizations that can't be reconciled by inspection | Recommend `/ultra-plan` |
| No technical design | BRD/PRD only, no TDD, with complex architectural decisions unmade | Recommend `/ultra-plan` |
| Single vague document | One document under 500 words with no feature breakdown | Recommend `/ultra-plan` |

**If any trigger fires, present the pre-planning prompt and stop.** The prompt lists the specific signals detected and offers three options: (1) run `/ultra-plan` first (recommended), (2) continue with `/create-plan` anyway — gaps flagged as assumptions, (3) abort. See `references/create-plan-examples.md` → "Pre-Planning Investigation prompt" for the display text.

**If none of the triggers fire**, proceed silently to Phase 1.5 (Codebase Reconnaissance).

**Important:** This gate must not be a speed bump for well-specified requirements. Only interrupt when genuine signals are present. When in doubt, continue and flag gaps in Phase 2.3 (Conflict Detection) rather than blocking here.

### Phase 1.5: Codebase Reconnaissance

Before analyzing requirements, survey the existing codebase so the plan accounts for what already exists. This prevents greenfield-on-brownfield plans and ensures work items extend rather than rebuild existing functionality.

**Time budget:** 5-10 minutes maximum. This is a lightweight scan, not a full `/plan-improvements` analysis.

#### 1.5.1 Project Structure Scan

Survey the codebase to understand its shape:

1. **Directory tree:** Run `find . -type f -not -path './.git/*' -not -path './node_modules/*' -not -path './.next/*' -not -path './dist/*' -not -path './build/*' -not -path './__pycache__/*' -not -path './venv/*' | head -200` to get a file listing (or equivalent for the platform)
2. **Tech stack detection:** Identify from manifest files:
   - `package.json` → Node.js/JavaScript/TypeScript (check for React, Next.js, Vue, etc.)
   - `pyproject.toml` / `setup.py` / `requirements.txt` → Python
   - `Cargo.toml` → Rust
   - `go.mod` → Go
   - `*.csproj` / `*.sln` → .NET
   - `pom.xml` / `build.gradle` → Java/Kotlin
3. **Entry points:** Identify main entry files (`src/index.*`, `src/main.*`, `app.*`, `__main__.py`, etc.)
4. **Configuration:** Note config files (`.env*`, `*.config.*`, `tsconfig.json`, `eslint.*`, `prettier.*`, `.editorconfig`)

#### 1.5.2 Test & CI/CD Infrastructure

Identify existing quality infrastructure:

1. **Test framework:** Look for test directories (`tests/`, `__tests__/`, `test/`, `spec/`), test config (`jest.config.*`, `pytest.ini`, `vitest.config.*`), and test files (`*.test.*`, `*.spec.*`, `*_test.*`). Record the detected **test command** (e.g., `pytest tests/ -v`, `npm test`, `jest`, `cargo test`).
2. **Test coverage:** Note approximate test count and whether coverage tooling is configured. Record the detected **coverage command** (e.g., `pytest --cov=src/ --cov-fail-under=80`, `jest --coverage`, `cargo llvm-cov`). Check for coverage config in `pytest.ini`, `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.coverage]`), `package.json` (jest `--coverage` in scripts), or `.nycrc`.
3. **CI/CD:** Check for `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`, `azure-pipelines.yml`. Also check `Makefile` for `check`, `lint`, `test`, or `verify` targets — these often wrap the canonical verification commands.
4. **Linting/formatting:** Note configured linters and formatters. Record the detected **lint command** by checking:
   - Python: `ruff` (in `pyproject.toml [tool.ruff]` or `ruff.toml`), `flake8` (in `setup.cfg`, `.flake8`), `pylint` (in `.pylintrc`, `pyproject.toml`)
   - JavaScript/TypeScript: `eslint` (in `.eslintrc.*`, `eslint.config.*`, `package.json` scripts), `biome`
   - Rust: `cargo clippy`
   - Go: `golangci-lint`
5. **Type checking:** Record the detected **typecheck command** by checking:
   - Python: `mypy` (in `pyproject.toml [tool.mypy]`, `mypy.ini`, `setup.cfg`), `pyright` (in `pyrightconfig.json`, `pyproject.toml`)
   - TypeScript: `tsc --noEmit` (presence of `tsconfig.json`)
   - Use the package manager's script if defined (e.g., `npm run typecheck`)
6. **Custom verification:** Check for project-specific verification scripts: `Makefile` targets (`make check`, `make lint`, `make test`), `package.json` scripts (`verify`, `check`, `validate`), CI workflow steps that run verification commands not covered above

#### 1.5.3 Existing Feature Cross-Reference

This is the critical step. For each major feature or capability described in the requirements documents:

1. **Search the codebase** for keywords, function names, route paths, component names, or module names that correspond to the requirement
2. **Classify each requirement** as one of:
   - **Not implemented** — No matching code exists; plan from scratch
   - **Partially implemented** — Some code exists but incomplete; plan should extend
   - **Already implemented** — Feature exists and appears functional; plan should verify/skip or enhance
3. **Flag overlaps** clearly by emitting a "Codebase Reconnaissance Results" report: tech stack, structure counts, test infrastructure, CI/CD, the detected Verification Commands (Test/Lint/Typecheck/Coverage/Custom), and a Feature Overlap Analysis table (Requirement | Status | Existing Code | Recommendation). See `references/create-plan-examples.md` → "Codebase Reconnaissance Results" for the sample.

4. **Note architectural patterns** the codebase follows (e.g., MVC, layered architecture, module conventions, naming patterns) so work items conform to existing conventions

#### 1.5.4 Feed Into Plan Generation

The reconnaissance output directly affects subsequent phases:

- **Phase 2 (Requirements Analysis):** Already-implemented features are deprioritized or marked as "verify only"
- **Phase 3 (Phase Planning):** Work items reference existing code paths and follow detected conventions
- **Phase 4 (Generate Plan):** Work item descriptions include "Extend existing `src/auth/` module" rather than "Create authentication system"
- **Complexity estimates** account for existing code (extending is typically S-M; building from scratch is M-L)

**If no meaningful codebase exists** (empty repo, only config files, or only requirements docs), report a "Greenfield project detected" notice (see `references/create-plan-examples.md` → "Codebase Reconnaissance Results" → Greenfield notice) and proceed directly to Phase 2.

### Phase 2: Requirements Analysis

#### 2.1 Extract Key Information

From each document, extract:

**From BRD:**
- Business objectives and success metrics
- Stakeholder requirements
- Constraints and dependencies
- Timeline expectations

**From PRD:**
- Feature list and priorities (P0, P1, P2)
- User stories and acceptance criteria
- UI/UX requirements
- Integration requirements

**From TDD:**
- Architecture decisions
- Technology stack
- API specifications
- Database schema
- System components

**From all documents:**
- Explicit dependencies between features
- Risk factors mentioned
- Performance requirements
- Security requirements

#### 2.2 Synthesize Requirements

Combine information across documents:

1. **Deduplicate:** Identify overlapping requirements
2. **Resolve conflicts:** Flag contradictions for user clarification
3. **Map dependencies:** Create dependency graph of features
4. **Prioritize:** Use explicit priorities or infer from language

#### 2.3 Conflict Detection

If conflicting requirements are found, present a "Requirement Conflicts Detected" report — for each conflict, show both sources (file + line) and the contradiction, state the resolution needed, then ask how to proceed: (1) continue with conservative assumptions, or (2) pause for clarification. See `references/create-plan-examples.md` → "Requirement Conflicts report" for the sample.

#### 2.4 Unknowns vs. Risks Classification

During requirements analysis, distinguish between **risks** (probabilistic events that could go wrong) and **unknowns** (knowledge gaps — things we don't know yet). Route them to the correct plan section:

- **Risks** → Risk Mitigation table. Examples: "third-party API may have rate limits," "migration could cause downtime," "new dependency may have security vulnerabilities."
- **Unknowns** → Unknowns Register. Examples: "database schema not specified in requirements," "authentication provider not chosen," "unclear whether feature X requires real-time updates or batch processing."

When the requirements analysis identifies ambiguities, missing specifications, unresolved design choices, or questions that cannot be answered from the source documents, capture each as an unknown with severity classification:

- **High:** Blocks progress on a phase — must be resolved before that phase starts
- **Medium:** Complicates implementation — resolve during the affected phase
- **Low:** Nice to know — resolve opportunistically

### Phase 2.5: Scope Confirmation

**Before generating the full plan, pause and present a scope summary for user approval.** This checkpoint prevents wasted generation time if the user disagrees with scope, phasing, or assumptions.

#### 2.5.1 Build Scope Summary

After completing requirements analysis (Phase 2) and codebase reconnaissance (Phase 1.5), compile a compact summary table containing: source-document count and word total; an Extracted Features table (# | Feature | Priority | Status | Source); the Proposed Plan Shape (phase count, estimated work-item count, estimated LOC/files, critical path); a draft Phase Grouping; an explicit Assumptions list; and a Features Skipped (already implemented) list. See `references/create-plan-examples.md` → "Plan Scope Summary display template" for the full display.

#### 2.5.2 Ask for Approval

After presenting the summary, ask:

```text
Proceed with this scope?
  1. Yes — generate the full implementation plan
  2. Adjust — tell me what to change (add/remove features, regroup phases, change priorities)
  3. Abort — stop here (analysis results above are yours to keep)
```

**Wait for the user to respond.** Do not proceed to Phase 3 until the user explicitly approves.

#### 2.5.3 Handle Responses

- **"Yes" / "1" / approve:** Proceed to Phase 3 (Phase Planning) with the confirmed scope.
- **"Adjust" / "2":** Accept the user's modifications. Update the feature list, phase grouping, priorities, or assumptions as directed. Re-display the updated summary and ask for approval again.
- **"Abort" / "3":** Stop execution. Display an abort notice that summarizes the analysis (documents analyzed, features extracted, already/partially implemented counts, reconnaissance completed) and states how to resume later. See `references/create-plan-examples.md` → "Abort response display".

#### 2.5.4 Design Constraints

- **Keep it compact:** The summary should be scannable in 30 seconds. Use tables, not paragraphs.
- **No partial generation:** Do not start generating plan phases before approval.
- **Assumptions are explicit:** Every inference made during analysis (tech choices, scope exclusions, priority assignments) must appear in the Assumptions list so the user can correct them.
- **Already-implemented features visible:** Features detected by codebase reconnaissance that will be skipped or only verified must be listed so the user can override if the detection was wrong.

### Phase 3: Phase Planning

#### 3.1 Work Item Extraction

Convert requirements into discrete work items:

**For each feature/requirement:**
1. Identify the deliverable
2. List files likely to be affected
3. Estimate complexity (XS/S/M/L/XL)
4. Identify dependencies
5. **Assign model tier** — default to the lowest tier that plausibly works (`haiku` for deterministic transforms, `sonnet` for standard coding — the default when unsure, `opus` for judgment-heavy work). For borderline items, choose the lower tier and add an explicit escalation criterion to the Notes field. See `references/plan-template.md` rule 17 for the full rubric and escalation guidance.

6. Define acceptance criteria — Use EARS notation for behavioral criteria: `WHEN [condition] THEN [component] SHALL [behavior]`. Binary/threshold criteria remain as simple checkboxes. See `references/plan-template.md` rule 13.

**Complexity estimation:** See `references/plan-template.md`'s Sizing Constraints table for file/LOC bounds per size (S/M/L).

If a work item would be XL (15+ files or 1500+ LOC), split it into smaller items.

#### 3.2 Phase Construction

Group work items into phases following these rules:

**Phase sizing constraints:**
Each phase should be completable by a single subagent session:
- Target: read 5-8 files, modify 3-5 files, change ~500 LOC
- Maximum: L complexity (8-15 files, 500-1500 LOC)
- Minimum: 2 files changed (avoid trivial phases)
- If a phase would be XL (15+ files or 1500+ LOC), split into sub-phases (e.g., Phase 3a, 3b)
- Target S-M per phase (max L)

**Grouping criteria:**
1. **Dependencies:** Items depending on each other go in sequence
2. **Cohesion:** Related items grouped together
3. **Risk:** High-risk items early (fail fast)
4. **Value:** High-value items prioritized
5. **Parallelization:** Independent items in same phase

**Phase ordering principles:**
1. Foundation/infrastructure first
2. Core features before enhancements
3. Integration points after dependent components
4. Polish/optimization last

#### Execution Hints Generation

**Primary mechanism: per-item Model Tier** (step 3.1.5 above). Each work item already carries a `**Model Tier:**` field that `implement-plan` reads directly. The Execution Hints section provides **phase-level overrides** — use it only when an entire phase warrants a uniform departure from item-level tiers, or to set a context budget hint.

After constructing phases, emit an `### Execution Hints` section at the plan level (between the Phase Summary Table and Milestones) only when phase-level guidance adds value beyond per-item tiers. Populate it as follows:

- **Default model tier:** `sonnet` for all phases (most items will have explicit per-item tiers that take precedence)
- **L-complexity phases where ALL items need opus:** Override at phase level to avoid redundant item-level markup
- **Simple mechanical phases** (config changes, dependency updates, formatting): Suggest `haiku` as a phase default
- **Context budget:** `Standard` for S-M phases, `Extended` for L phases with many files

**Format:** a `### Execution Hints` table with columns Phase | Model Tier | Context Budget | Notes — an "All (default)" row (`sonnet`, Standard, noting per-item tiers take precedence) plus per-phase override rows. See `references/create-plan-examples.md` → "Execution Hints table format".

If all phases are S-M complexity and per-item tiers are already set, omit the Execution Hints section entirely (per template rule 15). The per-item `**Model Tier:**` fields are sufficient on their own.

> **Orchestrator note:** `implement-plan` itself benefits from running on Opus. The orchestrator makes decomposition decisions, resolves escalations, and sets phase routing — a wrong call costs more in re-runs than the orchestrator's tokens. Model selection for the orchestrator is controlled by the user's session, not this command.

#### 3.2.1 Plan Size Limits

Plans must stay within bounds that `/implement-plan` can execute reliably. Apply these limits during plan generation:

**Maximum phases:** 8 phases per plan file (configurable via `--max-phases`). If requirements decompose into more than the limit:
1. Merge related phases to reduce count (prefer cohesion over granularity)
2. If merging is insufficient, split into multiple plan files (e.g., `IMPLEMENTATION_PLAN.md` and `IMPLEMENTATION_PLAN-PHASE2.md`) and inform the user
3. Never silently drop phases or work items to meet the limit

**Maximum work items per phase:** 6 work items. If a phase has more than 6 items, split the phase.

**Work item granularity:** Each work item should touch no more than 5-8 files and change ~500 LOC. If a work item exceeds these bounds, split it into sub-items (e.g., 3.1a, 3.1b) or promote sub-tasks to separate work items.

**Why these limits matter:** `/implement-plan` executes each phase via a subagent with finite context. Oversized plans cause subagents to lose context mid-execution, produce incomplete work, or silently skip items. Smaller, focused phases complete reliably.

#### 3.3 Dependency Analysis

For each phase, verify:
- All dependencies from previous phases are met
- No circular dependencies exist
- Critical path is identified

### Phase 4: Generate IMPLEMENTATION_PLAN.md

#### Append vs Overwrite Logic

**Before writing, check if IMPLEMENTATION_PLAN.md already exists.**

- **File missing:** Create it fresh with the full structure below.
- **File exists, all items `Status: COMPLETE`:** Prompt the user to choose — (1) archive the completed plan to `docs/archive/IMPLEMENTATION_PLAN-v{N+1}.md` and start fresh, or (2) append new phases after the completed ones.
- **File exists, some items PENDING/IN_PROGRESS:** Append new phases directly — no prompt needed.

Follow `references/plan-append-guide.md` for the full procedure (archive versioning, marker-based insertion points, phase/item renumbering, partial-execution handling, user messaging, and a Before/After example), using separator `from /create-plan`.

Read the plan template from `references/plan-template.md` (relative to this command's plugin directory) and use it as the output structure for IMPLEMENTATION_PLAN.md.

**Command-specific field values for `/create-plan`:**
- **Based On:** List of analyzed documents (e.g., PRD.md, TDD.md, docs/BRD.md)
- **Ref field:** Use `Requirement Refs:` with document section references (e.g., PRD §2.1, TDD §4.3)
- **Success Metrics:** Include business metrics from BRD, performance metrics from TDD, user satisfaction metrics from PRD
- **Traceability:** Title the appendix "Requirement Traceability" with columns: Requirement, Source, Phase, Work Item
- **Footer:** `*Source: /create-plan command*`

#### 4.1 Definition of Done Generation

For each phase, emit a `### Definition of Done (Runnable)` section after the Phase Completion Checklist, populated with verification commands detected during Phase 1.5.2 (Codebase Reconnaissance).

**Rules:**
- Only include commands that were actually detected. If no verification infrastructure was found, omit the DoD section entirely (per template rule 14 — never populate with empty placeholders).
- Use the same commands for every phase unless a phase has phase-specific verification needs (e.g., a database migration phase might add a migration check command).
- The DoD section is bracketed by `<!-- BEGIN DOD -->` and `<!-- END DOD -->` markers for machine parsing.

**Format:** a `### Definition of Done (Runnable)` section wrapped in `<!-- BEGIN DOD -->` / `<!-- END DOD -->` markers, containing a Check | Command | Pass Criteria table with one row per detected command (Tests/Lint/Types/Coverage/Custom). See `references/create-plan-examples.md` → "Definition of Done table format".

**Mapping from Phase 1.5.2 detection to DoD rows:**

| Detected Command | DoD Check Name | Pass Criteria |
|------------------|----------------|---------------|
| Test command | Tests | Exit code 0 |
| Lint command | Lint | Exit code 0 |
| Typecheck command | Types | Exit code 0 |
| Coverage command | Coverage | Threshold from config, or ≥80% default |
| Custom verification | [Descriptive name] | Exit code 0 or project-specific |

#### 4.2 Unknowns Register Population

When generating the plan, populate the Unknowns Register (inside `<!-- BEGIN TABLES -->` / `<!-- END TABLES -->` markers) with all unknowns captured during Phase 2.4 (Unknowns vs. Risks Classification). Each entry needs: ID (U1, U2, ...), the unknown, severity, affected phase/item refs, resolution strategy, and status (Open).

#### 4.3 Acceptance Criteria with EARS Notation

When writing acceptance criteria for work items, use EARS notation for behavioral criteria: `WHEN [condition] THEN [component] SHALL [behavior]`. Binary/threshold criteria (coverage ≥80%, lint clean, no TODOs) remain as simple checkboxes. See `references/plan-template.md` rule 13.

### Phase 5: Save and Report

#### 5.1 Save the Plan

Save IMPLEMENTATION_PLAN.md to the repository root (or custom path if specified). If appending to an existing file, the save overwrites the file with the merged content (existing + new phases).

#### AGENTS.md Generation (optional)

If `AGENTS.md` doesn't already exist in the repo root, offer to generate one from CLAUDE.md and the codebase reconnaissance results, using `references/agents-md-template.md` (tool-agnostic — no Claude Code-specific features). See `references/create-plan-examples.md` for the full check/offer/generate procedure.

#### 5.2 Summary Report

Display a summary to the user; emit it in the format shown in `references/create-plan-examples.md` (document/phase breakdown, critical path, risks identified, next steps, and — when the plan has 6+ phases or 20+ work items — a "Large Plan Detected" parallel-execution callout).

## Execution Guidelines

### Deep Investigation Before Planning

Before constructing the plan, aggressively investigate each identified change, gap, or requirement to ensure you fully understand:

1. **Root causes** — Do not accept surface-level symptoms. For each issue or requirement, trace it to its origin. Why does this gap exist? What created the need?
2. **Impact and risk** — For each item, assess the blast radius. What else depends on this? What breaks if we get it wrong?
3. **Interrelationships** — Map the connections between items. Changes to item A may conflict with, enable, or constrain item B. Identify these interactions BEFORE constructing the plan so that work items are sequenced and grouped to resolve related issues together.
4. **Architectural coherence** — Every work item must fit within the project's overall architecture and intent. Do not propose isolated patches that create technical debt or trigger a whack-a-mole fix cycle. Instead, design integrated, cohesive changes where a single well-designed modification addresses multiple related concerns.

**The goal is a plan that produces elegant, architecturally sound changes — not a patchwork of isolated fixes.**

### General Principles

- **Be thorough:** This plan informs significant work—capture all requirements
- **Be specific:** Include file paths, function names, concrete approaches
- **Be realistic:** Estimate effort honestly; overrunning phases causes problems
- **Be practical:** Prioritize impact over elegance; ship value to users
- **Consider context:** Factor in existing codebase (use reconnaissance results), tech debt, team constraints
- **Extend, don't rebuild:** When codebase reconnaissance identifies existing features, plan to extend or enhance them rather than building from scratch
- **Enable parallelism:** Structure phases so multiple streams can work simultaneously
- **Preserve stability:** Each phase should leave the codebase in a working state
- **Maintain traceability:** Link every work item back to source requirements

## Error Handling

### No Requirements Documents

Report that no requirements documents were found, then list the documents to create (PRD/BRD/TDD/requirements.md) or how to specify them explicitly. See `references/create-plan-examples.md` → "Error Handling displays" → "No Requirements Documents".

### Incomplete Requirements

If critical information is missing, present an "Incomplete Requirements Detected" report listing the missing information and offer three options: (1) continue with documented assumptions, (2) pause for the user to update requirements, or (3) generate a partial plan for defined areas only. See `references/create-plan-examples.md` → "Error Handling displays" → "Incomplete Requirements".

### Conflicting Requirements

See Phase 2.3 for conflict handling.

## Examples

```text
User: /create-plan docs/requirements/*.md --phases 3

Claude:
[Uses specified documents and targets 3 phases]
```

See `references/create-plan-examples.md` for a full transcript covering document discovery, codebase reconnaissance, and scope confirmation through plan generation.

## Performance

**Typical Duration:**

| Document Volume | Expected Time |
|-----------------|---------------|
| Light (< 5K words) | 1-2 minutes |
| Medium (5-15K words) | 2-4 minutes |
| Heavy (15-30K words) | 4-8 minutes |
| Extensive (30K+ words) | 8-15 minutes |

**Factors Affecting Performance:**
- Number and size of source documents
- Complexity of requirements (many dependencies)
- Conflict resolution needed
- Level of detail in output

## Related Commands

- `/plan-improvements` - Generate improvement plan from existing codebase analysis
- `/implement-plan` - Execute an IMPLEMENTATION_PLAN.md
- `/plan-next` - Get recommendation for next action
- `/assess-document` - Evaluate document quality before planning
