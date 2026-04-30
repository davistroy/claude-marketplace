# Anti-Patterns Catalog

Shared reference for planning and implementation anti-patterns. Referenced by `/ultra-plan` (Solution Design phase), `/create-plan`, and `/plan-improvements`.

---

## Planning Anti-Patterns

### 1. Symptom Patching
**Description:** Fixing the visible symptom instead of tracing to the structural root cause. Leads to recurring issues and whack-a-mole fix cycles.
**Detection:** The proposed fix doesn't answer "why does this happen?" — it only addresses "what went wrong this time?"
**Mitigation:** Ask "why" at least three times before proposing a fix. Trace the data flow to the point of origin.

### 2. Implicit Dependencies
**Description:** Change sets that depend on each other's completion order but don't declare it. Causes integration failures when items are implemented in the wrong order or in parallel.
**Detection:** Two work items touch the same file/function/API but have no declared dependency. Parallel execution would produce merge conflicts or broken state.
**Mitigation:** Run Phase 2 (Interaction Mapping) thoroughly. Every shared code path, state, or contract must appear in the dependency graph.

### 3. Scope Creep / Gold-Plating
**Description:** Embedding architectural rewrites, premature abstractions, or "nice-to-have" improvements inside a targeted fix. Inflates scope, delays delivery, introduces untested changes.
**Detection:** The diff touches files or systems not mentioned in the original issue. Work item description includes "while we're at it" or "we should also."
**Mitigation:** If a broader refactor is warranted, flag it as a separate follow-up. Solve exactly what's needed — nothing more.

### 4. Mid-Plan Scope Addition
**Description:** Adding new requirements or items to an in-progress plan without re-running discovery and interaction mapping. New items may conflict with existing change sets.
**Detection:** A new work item appears in a plan without a corresponding entry in the interaction map or traceability appendix.
**Mitigation:** New items go through the full pipeline: investigation → interaction mapping → solution design. Append as new phases with explicit dependencies on existing work.

### 5. Freeform Untestable Acceptance Criteria
**Description:** Acceptance criteria written as vague prose that cannot be mechanically verified. "The system should be fast" or "The UI should be intuitive."
**Detection:** Criterion cannot be translated to a pass/fail assertion or a concrete measurement with a threshold.
**Mitigation:** Use EARS notation for behavioral criteria: `WHEN [condition] THEN [component] SHALL [behavior]`. Use thresholds for metrics: "P95 latency < 200ms" not "should be fast."

---

## Implementation Anti-Patterns

### 6. Cross-Item Conflicts
**Description:** Implementing one work item in a way that breaks, complicates, or undermines another planned item. Usually caused by skipping interaction mapping.
**Detection:** After implementing item A, item B's acceptance criteria can no longer be met without reworking A.
**Mitigation:** Review the interaction map before each implementation. If implementing item A changes assumptions for item B, update both items' plans before proceeding.

### 7. TBD/Placeholder Pollution
**Description:** Generating plans with "TBD", "TODO", or empty placeholder sections that never get resolved. Creates false confidence — the plan looks complete but has unresolved gaps.
**Detection:** Grep for "TBD", "TODO", "placeholder", or empty table cells in the generated plan.
**Mitigation:** Every field must be filled at generation time. If information is genuinely unknown, move it to the Unknowns Register with a resolution strategy — don't leave it inline.

### 8. Vague File References
**Description:** Work items that say "update the relevant files" or "modify the configuration" without listing specific file paths. Implementers waste time on discovery.
**Detection:** Files Affected section contains no file paths, or paths use wildcards without justification.
**Mitigation:** Every work item must list specific file paths with action (create/modify/delete). If the exact files aren't known, that's an unknown — resolve it before implementation starts.

### 9. Generating Tasks Referencing Undefined Symbols
**Description:** Plans that reference functions, classes, variables, or APIs that don't exist in the codebase — usually from hallucinated or assumed code structure.
**Detection:** File paths in "Files Affected" don't exist. Function names in task descriptions aren't found via grep. API endpoints in acceptance criteria aren't defined.
**Mitigation:** Investigation phase (Phase 1/2) must read actual code and verify symbol existence. Never reference a function without grepping for it first.

---

## Verification Anti-Patterns

### 10. Claiming Tests Pass Without Running
**Description:** Marking a work item as "tests pass" based on reading the code rather than executing the test suite. Silent failures, environment differences, and integration issues are missed.
**Detection:** No test execution output in the implementation log. "Tests should pass" instead of "ran `npm test`, output: all 47 tests pass."
**Mitigation:** The Definition of Done (Runnable) section provides specific commands. Execute every command and capture the output. No exceptions.

### 11. Self-Review Without Running Verification
**Description:** The implementation agent reviews its own code changes and declares them correct without running any automated checks. Confirmation bias is guaranteed.
**Detection:** Work item completion log shows file edits but no command execution. Subagent summary says "changes look correct" without evidence.
**Mitigation:** Separate the implementation and testing subagents. Testing subagent runs verification commands independently and reports pass/fail with output.
