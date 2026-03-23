---
command: evaluate-pipeline-output
type: skill
fixtures: []
---

# Eval: /evaluate-pipeline-output (skill)

## Purpose

Evaluates contact-center-lab pipeline output quality against expected benchmarks. Good output: a structured report with CRITICAL/HIGH/MEDIUM/LOW findings, per-metric pass/warn/fail status, and a scale-readiness assessment.

## Fixtures

None provided here — this skill requires actual pipeline output from the contact-center-lab project. Use a real pipeline run output directory for testing.

## Setup

This skill is specific to the `c:\Users\Troy Davis\dev\contact-center-lab` project. Run evals from that project's context.

**Minimum required output directory structure:**
```
output/<run-name>/
  final/
    statistics.json
    atoms.json
    entities.json
    graph_edges.json
    vector_db_atoms.jsonl
  stage_4_atoms.json
  stage_6_triples.jsonl
  stage_7_procedures.jsonl
  ...
```

## Test Scenarios

### S1: Single-article run evaluation

**Setup:** Have a completed single-article pipeline run in `output/`.

**Invocation:** `/evaluate-pipeline-output output/<run-name>`

**Must:**
- [ ] Reads `final/statistics.json` and extracts all counts
- [ ] Runs all phases (0 through 9)
- [ ] Produces a structured report with Executive Summary, Counts vs Expectations table, Findings by severity
- [ ] Scale Readiness Assessment is present
- [ ] Counts vs Expectations table uses pass/warn/fail status per metric

**Should:**
- [ ] Atom count is validated against 35-60 per article range
- [ ] Entity fragmentation ratio calculated
- [ ] Embedding dimension verified (1024 expected)
- [ ] Isolated node rate assessed against appropriate threshold

**Must NOT:**
- [ ] Modify any pipeline output files
- [ ] Commit anything

---

### S2: Missing output directory

**Invocation:** `/evaluate-pipeline-output output/nonexistent-run`

**Must:**
- [ ] Reports that the directory does not exist
- [ ] Lists what directories are available in `output/`

---

### S3: Report format compliance

**Must:**
- [ ] Report begins with "Pipeline Output Evaluation Report" header
- [ ] Findings use [C1], [H1], [M1], [L1] notation
- [ ] Each finding includes Stage reference and Evidence

---

### S4: Multi-article scaling

**Invocation:** `/evaluate-pipeline-output output/<run-name> --articles 10`

**Must:**
- [ ] Uses 10x single-article expectations for all metric thresholds
- [ ] Isolated node threshold adjusts to <30% (not <50%)

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| All 10 phases executed | Required |
| Findings categorized by severity | Required |
| Scale Readiness Assessment present | Required |
| No pipeline files modified | Required |
| Metric thresholds scale correctly with article count | Required |
