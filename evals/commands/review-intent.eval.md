---
command: review-intent
type: command
fixtures: [docs/sample-prd.md]
---

# Eval: /review-intent

## Purpose

Determines the original project intent from documentation and design artifacts, then compares it against the current implementation to identify discrepancies. Good output: a clear statement of intended behavior versus actual behavior, with specific gaps called out.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/sample-prd.md` | Intent reference document for comparison |

## Test Scenarios

### S1: Repo with CLAUDE.md and plugin docs as intent sources

**Invocation:** `/review-intent`

**Must:**
- [ ] Reads intent sources (CLAUDE.md, README.md, plugin.json descriptions)
- [ ] Reads current implementation (command files, skill files)
- [ ] Produces a comparison report in conversation
- [ ] Lists at least one area where implementation matches intent (positive finding)
- [ ] Lists at least one area where implementation diverges or is unclear
- [ ] No files created

**Should:**
- [ ] Notes that `deprecated/` commands are not in the active command list (intent vs reality)
- [ ] Notes if any command in CLAUDE.md's command list is missing from the actual files
- [ ] Organizes findings by severity or impact

**Must NOT:**
- [ ] Modify any files
- [ ] Fabricate discrepancies that don't exist

---

### S2: With explicit requirements document

**Invocation:** `/review-intent fixtures/docs/sample-prd.md`

**Must:**
- [ ] Uses `sample-prd.md` as the primary intent document
- [ ] Compares PRD requirements against what exists in the current codebase
- [ ] Notes that the PRD describes a Slack bot, and the current repo is a Claude plugin marketplace (clear discrepancy — good test of honesty)

**Must NOT:**
- [ ] Pretend the repo matches the PRD when it clearly does not

---

### S3: Read-only behavior

**Must:**
- [ ] Does not create files
- [ ] Does not make git commits

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Intent sources identified and cited | Required |
| Both matching and diverging areas identified | Required |
| No files created or modified | Required |
| Does not fabricate discrepancies | Required |
