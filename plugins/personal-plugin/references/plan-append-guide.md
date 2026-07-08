# Plan Append/Archive Guide

**Purpose:** Defines what to do when IMPLEMENTATION_PLAN.md already exists at the target path — the all-items-COMPLETE archive-vs-append decision, the archive-to-`docs/archive/` steps, and the append mechanics for adding new phases to an existing plan.

**Consumers:** `/create-plan`, `/plan-improvements`. This guide is the single source of truth for append/archive behavior — both commands point here instead of inlining their own copy, so the procedure cannot drift between them.

---

## Append vs Overwrite Logic

**Before writing, check if IMPLEMENTATION_PLAN.md already exists.**

- **If the file does NOT exist:** Create it fresh with the full structure below.
- **If the file DOES exist:**

  **First, check if ALL work items are COMPLETE.** Scan every `**Status:**` field in the file. If every item has `Status: COMPLETE`, the plan is finished. Present this prompt:

  ```text
  Existing IMPLEMENTATION_PLAN.md found with all [N] items COMPLETE.

  Options:
    (1) Archive and create fresh — move completed plan to docs/archive/, generate new plan
    (2) Append — add new phases after the completed ones (preserves history in one file)
  ```

  **Option (1) Archive and create fresh:**
  1. Scan `docs/archive/` for existing `IMPLEMENTATION_PLAN-v*.md` files
  2. Extract the highest version number N (default 0 if none exist)
  3. Create `docs/archive/` directory if it doesn't exist
  4. Move the plan file to `docs/archive/IMPLEMENTATION_PLAN-v{N+1}.md`
  5. Report: `Archived completed plan as docs/archive/IMPLEMENTATION_PLAN-v{N+1}.md`
  6. Then create a fresh IMPLEMENTATION_PLAN.md using the full structure below.

  **Option (2) Append:** Proceed with the append logic below.

  **If NOT all items are COMPLETE** (some are PENDING or IN_PROGRESS), proceed directly to the append logic below.

  **Append logic:**
  1. Read the existing file
  2. Locate the machine-readable markers to find insertion points:
     - `<!-- BEGIN PHASES -->` / `<!-- END PHASES -->` — bracket all phase sections
     - `<!-- BEGIN TABLES -->` / `<!-- END TABLES -->` — bracket the trailing tables (Parallel Work, Risk Mitigation, Success Metrics, Traceability)
  3. Identify the highest existing phase number (e.g., if Phase 4 is the last, new phases start at Phase 5)
  4. Renumber all new phases to continue from the highest existing phase
  5. Renumber all new work items accordingly (e.g., 5.1, 5.2, 6.1...)
  6. Insert the new phases immediately before `<!-- END PHASES -->`, preceded by a separator comment: `<!-- Appended on [YYYY-MM-DD HH:MM:SS] from /[command-name] -->` — `/create-plan` and `/plan-improvements` each substitute their own command name for `[command-name]` when they perform the append
  7. Update the Phase Summary Table to include both old and new phases
  8. Update the total phase count, estimated total effort, and any metadata in the header
  9. Append new entries to the tables between `<!-- BEGIN TABLES -->` and `<!-- END TABLES -->` (Parallel Work Opportunities, Risk Mitigation, Success Metrics, Traceability)
  10. **Partially-executed plans:** If any existing items have `Status: COMPLETE` or `Status: IN_PROGRESS`, preserve them exactly as-is. Warn the user: `"This plan has items in progress. New phases will be appended after existing content."`

**Tell the user what happened:**
```text
Existing IMPLEMENTATION_PLAN.md found with [N] phases.
Appending [M] new phases (Phase [N+1] through Phase [N+M]).
```

**Append Example — Before & After:**

*Before (existing 3-phase plan):*
```markdown
<!-- BEGIN PHASES -->

## Phase 1: Foundation
...
## Phase 2: Core Features
...
## Phase 3: Integration
...

<!-- END PHASES -->

<!-- BEGIN TABLES -->

## Parallel Work Opportunities
| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2 | Independent modules |

...
<!-- END TABLES -->
```

*After (2 new phases appended):*
```markdown
<!-- BEGIN PHASES -->

## Phase 1: Foundation
...
## Phase 2: Core Features
...
## Phase 3: Integration
...

<!-- Appended on 2026-02-28 14:30:00 from /[command-name] -->

## Phase 4: Error Handling
...
## Phase 5: Polish
...

<!-- END PHASES -->

<!-- BEGIN TABLES -->

## Parallel Work Opportunities
| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2 | Independent modules |
| 4.1 | 4.2 | New independent items |

...
<!-- END TABLES -->
```
