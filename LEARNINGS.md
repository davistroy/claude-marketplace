# Learnings

- [2026-07-08] 4.2 escalated sonnet→opus: the item's ≤500-line target conflicted with its own byte-intact protection; opus resolved by moving illustration blocks only (470 lines, zero behavior change). Lesson: when a size target and a protection clause can collide, pre-authorize the illustration/logic distinction in the item spec.
- [2026-07-08] 3.3: arch-review per-agent meta rewrite missed the Step 1 shared-meta seed and Step 6 summary — caught by phase testing. Lesson: contract changes need a whole-file grep for the old artifact name.
