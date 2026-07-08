# Learnings

## Summary

- Three cross-phase findings from this release; all were caught by testing/validation gates before shipping, none reached the release unmitigated.
- Escalation pattern (4.2): a line-budget target collided with a byte-intact protection clause — resolved by separating structural moves (illustrations) from logic edits; pre-authorize that distinction in future item specs when the two could collide.
- Contract-change pattern (3.3): restructuring a shared artifact (shared `.meta.json` → per-agent files) missed two call sites — a whole-file grep for the old artifact name is required on any contract change, not just the primary call sites.
- Syntax-safety pattern (8.2): generated YAML scalars containing `: ` (e.g., "Suggest when:") silently broke plain-scalar parsing across 12 skills — always quote or rephrase such scalars; this class of error is now CI-guarded via the plugin-validate job.
- All three were caught by this plan's own gates (phase testing; 8.6's strict-validate sweep) — the layered Definition-of-Done structure is working as designed.
- Net effect: every escalation and fix is now encoded as either a spec-discipline lesson (4.2, 3.3) or a permanent automated guard (8.2).

- [2026-07-08] 4.2 escalated sonnet→opus: the item's ≤500-line target conflicted with its own byte-intact protection; opus resolved by moving illustration blocks only (470 lines, zero behavior change). Lesson: when a size target and a protection clause can collide, pre-authorize the illustration/logic distinction in the item spec.
- [2026-07-08] 3.3: arch-review per-agent meta rewrite missed the Step 1 shared-meta seed and Step 6 summary — caught by phase testing. Lesson: contract changes need a whole-file grep for the old artifact name.
- [2026-07-08] 8.2: folding trigger text into YAML descriptions introduced unquoted 'Suggest when:' colons that broke plain-scalar parsing in 12 skills — caught by 8.6's strict-validate sweep. Lesson: any generated YAML scalar containing ': ' must be quoted or rephrased; the CI plugin-validate job now guards this class.
