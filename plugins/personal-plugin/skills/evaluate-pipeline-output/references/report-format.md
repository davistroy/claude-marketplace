# Pipeline Evaluation Report Format

**Purpose:** Phase 13 report template for `skills/evaluate-pipeline-output/SKILL.md`. Populate every bracketed placeholder from the Phase 1-12 findings; do not omit a section even when a category has no findings (state "None found").

**Consumer:** `skills/evaluate-pipeline-output/SKILL.md` — Phase 13.

---

## Report Template

```text
### Phase 13: Evaluation Report

Produce a structured report in this format:

---

**Pipeline Output Evaluation Report**

**Run:** [output directory name]
**Date:** [from statistics.json timestamp or current date]
**Articles processed:** [N]
**Pipeline config:** [LLM backend + model, embedding backend + model, key thresholds]
**Stages run:** [list stages found in output]
**Mode:** [test/validation/production]

---

**Executive Summary**

[2-4 sentence summary: did the run succeed, what are the top 2-3 issues, is it ready for scale-up. Mention any CRITICAL infrastructure issues (LLM failures, HDBSCAN failures) first.]

---

**Infrastructure Health**

| Check | Status | Detail |
|-------|--------|--------|
| LLM failure rate (Stage 3) | pass/warn/fail | X% (N failures of M calls) |
| LLM failure rate (Stage 6) | pass/warn/fail | X% |
| LLM failure rate (Stage 7) | pass/warn/fail | X% |
| HDBSCAN (Stage 5) | pass/fail | succeeded/failed |
| HDBSCAN (Stage 8) | pass/fail | succeeded/failed |
| Processing time | info | Xs total (Xs stage 3, Xs stage 6, Xs stage 7) |

---

**Counts vs Expectations**

| Metric | Expected | Actual | Per Article | Status |
|--------|----------|--------|-------------|--------|
| Articles ingested | — | N | — | info |
| Atoms (total) | N x range | ... | .../article | pass/warn/fail |
| Entities (total) | N x range (discounted) | ... | .../article | pass/warn/fail |
| Entity fragmentation ratio | <2.0 | ... | — | pass/warn/fail |
| Triples | N x range | ... | .../article | pass/warn/fail |
| Unmapped predicates | <20% | ...% | — | pass/warn/fail |
| Procedure single-step rate | 40-65% | ...% | — | pass/warn/fail |
| Procedure stub rate | <5% | ...% | — | pass/warn/fail |
| DERIVED_FROM completeness | 100% | ...% | — | pass/warn/fail |
| Isolated nodes | scale-adjusted | ...% | — | pass/warn/fail |
| Embedding dimension | [from config] | ... | — | pass/warn/fail |
| Dedup removal rate | 0-15% | ...% | — | pass/warn/fail |

---

**Regression Analysis** (if --baseline provided)

| Metric | Baseline | Current | Delta | Status |
|--------|----------|---------|-------|--------|

---

**Findings**

For each finding, use the full deep-dive format. Group by severity.

CRITICAL (data loss, infrastructure failure, or semantic corruption):

> **[C1] Title**
> - **Symptom:** What was observed, with specific data/quotes
> - **Issue:** What is actually wrong (not just the symptom)
> - **Root Cause:** Which stage/function/logic path, confirmed by reading code
> - **Cascade:** What downstream stages and outputs are affected, and how
> - **Fix:** Architectural fix that addresses root cause permanently, not a patch
> - **Verification:** How to confirm the fix worked

HIGH (semantic errors that produce wrong answers at query time):
> [same format as above for each finding]

MEDIUM (quality issues that degrade usefulness):
> [same format]

LOW (observations worth tracking across runs):
> [same format — cascade and fix may be "none needed" for pure observations]

---

**Causal Chain Summary**

After all individual findings, consolidate any findings that share a root cause into chains:

> **Chain 1:** [Root cause stage + description]
> → [First downstream effect] (finding [X1])
> → [Second downstream effect] (finding [X2])
> → [Final output impact] (finding [X3])
> **Single fix resolves:** [X1], [X2], [X3]

This section ensures the user sees that fixing one root cause eliminates multiple findings, and knows which fix to prioritize.

---

**Scale Readiness Assessment**

[Direct answer: is this output good enough to run the full corpus? What must be fixed first vs what can wait? What will improve naturally at scale (entity resolution, dedup) vs what will get worse (any linear bug gets multiplied)?]

---

**Recommended Next Steps**

Ordered by impact (root causes that resolve the most causal chains first):

1. [Fix from finding [X]: what to change, in which file/function, why this is the architecturally sound approach, and which other findings this resolves]
2. [next fix, same format]
3. ...

**Do not list symptom-level patches here.** Every recommendation must trace back to a root cause identified in the Findings section. If a recommendation would add a special case, workaround, or hardcoded fix, explain why no better alternative exists.

---
```
