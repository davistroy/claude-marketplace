# implement-plan State File Schema (`.implement-plan-state.json`)

**Purpose:** Full annotated schema for the ephemeral execution-state file that `/implement-plan` uses as its ground truth. The state file persists minimal progress between loop iterations so the orchestrator never needs to re-read the full plan or accumulate conversational history. It is created during STARTUP, updated after every batch, gitignored, and deleted on completion.

**Consumer:** `/implement-plan`. The command keeps a compact field-summary table inline and points here for the complete shape and the annotated example below. Keep this file in sync with the command's field-summary table if fields are added or renamed.

---

## Annotated Example

```json
{
  "plan_file": "IMPLEMENTATION_PLAN.md",
  "plan_identity": {
    "generated": "2026-02-28",
    "total_phases": 4,
    "phase_titles": ["Phase 1: Plan Schema", "Phase 2: Tooling", "Phase 3: Context Window Management", "Phase 4: Docs"],
    "item_ids": ["1.1", "1.2", "2.1", "2.2", "2.3", "3.1", "3.2", "4.1"]
  },
  "started_at": "2026-02-28T14:30:00",
  "current_phase": "Phase 3: Context Window Management",
  "current_item": "3.2",
  "in_progress": {
    "item": "3.2",
    "phase": "Phase 3",
    "description": "Restructure implement-plan loop",
    "started_at": "2026-02-28T15:42:00"
  },
  "completed": [
    { "item": "1.1", "phase": "Phase 1", "description": "Add Tasks and Notes fields", "status": "COMPLETE", "sha": "abc1234", "files": ["plan-improvements.md"] },
    { "item": "1.2", "phase": "Phase 1", "description": "Standardize headers", "status": "COMPLETE", "sha": "def5678", "files": ["plan-improvements.md", "create-plan.md"] }
  ],
  "failed": [
    { "item": "2.3", "phase": "Phase 2", "description": "Update allowed-tools", "error": "Test failure in...", "attempts": 2 }
  ],
  "project_context": {
    "project_description": "React dashboard app with REST API backend",
    "tech_stack": "TypeScript, React, Jest",
    "test_command": "npm test",
    "verification_commands": [
      {"name": "tests", "command": "npm test", "pass_criteria": "exit code 0"},
      {"name": "lint", "command": "eslint src/", "pass_criteria": "exit code 0"},
      {"name": "typecheck", "command": "tsc --noEmit", "pass_criteria": "exit code 0"}
    ],
    "conventions": "kebab-case files, ESM imports"
  },
  "execution_hints": {
    "default_model": "sonnet",
    "phase_overrides": {"Phase 2": "opus"}
  },
  "item_model_tiers": {
    "1.1": "haiku",
    "1.2": "sonnet",
    "2.1": "opus"
  },
  "last_good_sha": "def5678",
  "checkpoints": {
    "1.1": "abc1234",
    "1.2": "def5678"
  },
  "parallelization_map": {
    "Phase 1": { "parallel": ["1.1", "1.2"], "sequential": ["1.3", "1.4"] },
    "Phase 2": { "parallel": ["2.1", "2.2", "2.3"], "sequential": ["2.4"] }
  }
}
```

## Field Reference

| Field | Type | Purpose |
|-------|------|---------|
| `plan_file` | string | Resolved path to the plan file (the command's `PLAN_FILE`). **A path, not an identity** — see `plan_identity`. |
| `plan_identity` | object | Which plan this state belongs to: `generated` (the `**Generated:**` value), `total_phases`, `phase_titles` (the `## Phase N: …` lines verbatim, minus the leading `## `), `item_ids` (the **first** `N.M` token on each `#### ` line, extracted with `match()` rather than anchored to the start — the completion marker is not reliably a suffix). Written at STARTUP Step 2, verified at STARTUP Step 0 before anything else in the file is trusted. |
| `started_at` | ISO timestamp | When the session began. |
| `current_phase` | string | Name of the phase currently executing. |
| `current_item` | string \| null | Item number currently being worked; `null` when the phase just completed. |
| `in_progress` | object \| absent | The single item being implemented right now (**single-item batch**). Present only between mark-in-progress (Step 0) and commit (Step 5). |
| `in_progress_batch` | array \| absent | The items being implemented right now (**parallel batch**), one object per item. Present only between Step 0 and Step 5. |
| `completed` | array | Finished items, each `{item, phase, description, status:"COMPLETE", sha, files}`. |
| `failed` | array | Failed/skipped items, each `{item, phase, description, error, attempts}`. |
| `project_context` | object | Orientation for subagents: `project_description`, `tech_stack`, `test_command` (legacy fallback), `verification_commands`, `conventions`. |
| `project_context.verification_commands` | array | Ordered checks, each `{name, command, pass_criteria}`. Authoritative source for the testing step. |
| `execution_hints` | object | `default_model` (session default, typically `sonnet`) and `phase_overrides` (phase name → tier). |
| `item_model_tiers` | map | Per-item model tier, e.g. `{"1.1":"haiku"}`. **Primary** tier source; takes precedence over `execution_hints`. |
| `last_good_sha` | string \| null | Most recent commit where all tests passed — the rollback target. |
| `checkpoints` | map | Item number → commit SHA for every completed item. |
| `parallelization_map` | object | Per-phase `{ "parallel": [...], "sequential": [...] }` groups, built at startup from `**Depends On:**` fields. |

## Notes

- **`in_progress` / `in_progress_batch` are transient markers.** Exactly one of them (or neither) is present at a time: `in_progress` for a single-item batch, `in_progress_batch` for a parallel batch. Each is set in Step 0 (before implementation) and removed in Step 5 (after the commit succeeds). If either field is present at STARTUP, the previous session was interrupted mid-implementation — the resume logic in the command's Step 0 detects this and offers retry/skip/mark-complete options.
- **Parallel completion shares one SHA.** All items in a parallel batch are committed together, so every item's `completed` entry and `checkpoints` mapping carry the same commit SHA.
- **The orchestrator reads and writes this file directly** — it is small, structured JSON; no subagent is needed.
- **`plan_identity` keys on item *numbers*, never item titles.** The plan file is modified while it executes: `**Status:**` fields flip to `COMPLETE`, `**Completed:**` is appended at finalization, and item headings are decorated with ` ✅ Completed YYYY-MM-DD`. Only `**Generated:**`, `**Total Phases:**`, the `## Phase N: …` headings, and the `N.M` numbers survive a run unchanged. A fingerprint over the file's text — or over heading titles — would differ from itself after the first completed item and reject every legitimate resume.
- **Deletion is the last action of the run, not the first action of FINALIZATION.** The COMPLETION REPORT is generated by reading this file, and its documented fallback for a missing file is "No work items were completed" — so deleting before the report makes a successful run report the opposite of the truth. Deleting after it is what stops the file being inherited by the next plan written to the same path (#235).
