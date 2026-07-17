---
command: arch-synthesize
type: command
fixtures: []
---

# Eval: /arch-synthesize

## Purpose

Re-synthesizes the executive summary from existing domain findings, without re-running any domain agent. Used after manually editing findings, re-running a single agent via `/arch-review-single`, or resolving cross-domain conflicts offline. Good output: a fresh `reports/executive-summary.md` built only from findings files already on disk.

## Fixtures

None — operates on an existing `<target-path>/arch-review/findings/` directory; can be run against this repository itself after a prior `/arch-review` or `/arch-review-single` run.

## Test Scenarios

### S1: Happy path — re-synthesize from existing findings

**Setup:** `<target-path>/arch-review/findings/` already contains at least one `<agent-name>.md` and `<agent-name>.meta.json` pair from a prior review run.

**Invocation:** `/arch-synthesize .`

**Must:**
- [ ] Validates `<target-path>/arch-review/findings/` exists before proceeding
- [ ] Merges per-agent `*.meta.json` coverage into a single coverage map
- [ ] Treats an agent missing its `.meta.json`/`.md` pair as "Domain not reviewed", not an error
- [ ] Reads all present findings files and runs cross-domain conflict detection
- [ ] Overwrites `<target-path>/arch-review/reports/executive-summary.md` with a fresh report, including the Review Coverage table
- [ ] Prints a terminal summary with total findings by severity and the path to the executive summary

**Must NOT:**
- [ ] Dispatch or re-run any domain agent
- [ ] Fabricate a finding for a domain with no findings file present

---

### S2: Error — no findings directory

**Setup:** `<target-path>/arch-review/findings/` does not exist.

**Invocation:** `/arch-synthesize .`

**Must:**
- [ ] Stops without attempting synthesis
- [ ] Suggests running `/arch-review` first

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| No domain agent is re-run | Required |
| Missing per-agent files are flagged as "Domain not reviewed", not fatal | Required |
| Executive summary is rebuilt from findings currently on disk | Required |
| Missing findings directory produces a clean, actionable error | Required |
