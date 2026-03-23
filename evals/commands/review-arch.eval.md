---
command: review-arch
type: command
fixtures: []
---

# Eval: /review-arch

## Purpose

Read-only architectural audit of the current project. Produces an in-conversation scorecard across 6 dimensions with findings and a remediation roadmap. Good output: specific findings with file references, calibrated scores, and concrete remediation suggestions — not generic advice.

## Fixtures

None — operates on the current repository.

## Test Scenarios

### S1: Full analysis — marketplace repo

**Invocation:** `/review-arch`

**Must:**
- [ ] Performs codebase reconnaissance before reporting (maps structure, reads manifests)
- [ ] Produces a scorecard table with all 6 dimensions (structure, code quality, dependencies, testing, security, performance)
- [ ] Each dimension has a score (1–5) and a one-line note
- [ ] Findings section references specific files from this repo (e.g., `plugins/personal-plugin/commands/*.md`)
- [ ] Remediation roadmap organizes fixes by effort (S/M/L/XL)
- [ ] No files are created or modified

**Should:**
- [ ] Executive summary is 2–3 paragraphs, not bullet points
- [ ] Identifies the lack of unit tests as a finding (this is a known gap in the marketplace repo)
- [ ] Findings include finding IDs (F1, F2, ...)

**Must NOT:**
- [ ] Create any files (this is a read-only command)
- [ ] Make git commits
- [ ] Give scores without justification

---

### S2: Focused analysis — security and testing only

**Invocation:** `/review-arch --focus security,testing`

**Must:**
- [ ] Output includes "Focused analysis — only security, testing evaluated" note
- [ ] Scorecard contains only 2 dimension rows
- [ ] Overall score is the average of only those 2 dimensions
- [ ] No findings for architecture, code quality, dependencies, or performance

---

### S3: Invalid focus dimension

**Invocation:** `/review-arch --focus security,badvalue`

**Must:**
- [ ] Displays error listing "badvalue" as invalid
- [ ] Lists valid dimension names

---

### S4: JSON output

**Invocation:** `/review-arch --json`

**Must:**
- [ ] Outputs valid JSON only (no surrounding text)
- [ ] JSON contains `scorecard`, `findings`, `remediation` keys
- [ ] Each finding has `id`, `severity`, `category`, `description`, `location`, `recommendation`

---

### S5: Non-code project (edge case)

**Setup:** Run from a directory containing only markdown documentation files.

**Invocation:** `/review-arch`

**Must:**
- [ ] Detects no source code files
- [ ] Suggests `/assess-document` instead
- [ ] Does not produce a confusing scorecard for a documentation-only project

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| All 6 dimensions scored with justification | Required |
| Findings reference actual files in the repo | Required |
| No files created | Required |
| Focused mode excludes non-selected dimensions | Required |
| JSON output is valid when --json specified | Required |
