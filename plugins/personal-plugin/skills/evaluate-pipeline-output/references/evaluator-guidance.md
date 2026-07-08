# Evaluator Guidance

**Purpose:** Severity thresholds, false-finding heuristics, and expected run duration for `skills/evaluate-pipeline-output/SKILL.md`. Consult before finalizing severity ratings in Phase 13 or when a finding looks suspicious.

**Consumer:** `skills/evaluate-pipeline-output/SKILL.md` — Phase 13 (severity calibration) and general evaluator judgment throughout Phases 1-12.

---

## Guidance Reference

```text
## Severity Calibration by Mode

| Mode | CRITICAL threshold | HIGH threshold | What it means |
|------|--------------------|----------------|---------------|
| `test` | Data loss or corruption only | Semantic errors affecting >20% of output | Small run, expect rough edges |
| `validation` (default) | Infrastructure failures OR data corruption | Semantic errors >10% | Pre-scale-up gate |
| `production` | Any infrastructure issue OR data corruption | Any semantic error >5% | Full corpus, zero tolerance |

---

## Evaluator Guidance

These are durable heuristics that help the evaluator avoid false findings:

- **Legacy/unused fields:** Some atom or procedure records may have empty fields at the root level that are populated in a nested block instead. Before flagging empty fields, check whether the data lives in a nested structure (e.g., `atom.procedure.steps` vs `atom.normalized_steps`). Inspect the actual data, don't assume.

- **Public entity redaction:** Well-known public companies (carriers, tech giants) appearing in sanitized output may or may not be correct — it depends on whether the relationship with that company is confidential. Check the safelist from config before flagging.

- **Isolated nodes at small scale:** High isolation rates (>50%) are expected and normal for single-article runs. Only flag isolation as a finding if it exceeds the scale-adjusted threshold from the expectations table.

- **Entity type cascade:** Synthetic company names that look like person names (e.g., "Keith-Francis") are a downstream symptom, not a root cause. The root cause is always in Stage B entity type detection. Report the root cause, not the symptom.

- **Standalone tools:** Tools like `extract_terms.py` or `calibrate_thresholds.py` in the pipeline's `tools/` directory are NOT part of the A-through-9 pipeline. They don't affect output quality directly. Don't flag their output or absence.

- **Passthrough is not failure:** Stage 3 passing short segments through without LLM decomposition is by design (configurable via `decomposition_min_length` and `simple_segment_passthrough` in config). High passthrough is only a concern if it cascades to shallow atoms.

- **Embedding model changes:** The pipeline may change embedding models over time. Always read the configured model and its expected dimension from config rather than assuming a specific value. Similarly, all similarity thresholds are model-dependent — read them from config.

---

## Performance

| Pipeline Output Size | Expected Duration |
|---------------------|-------------------|
| Small (< 50 atoms/entities) | 2-5 minutes |
| Medium (50-200 atoms/entities) | 5-15 minutes |
| Large (200-500 atoms/entities) | 15-25 minutes |
| Very Large (500+ atoms/entities) | 25-40 minutes |

Duration scales with the number of pipeline stages to evaluate and the volume of atoms, entities, and triples to cross-reference. The `--mode test` flag reduces severity thresholds but does not significantly affect duration.
```
