---
command: assess-document
type: command
fixtures: [docs/sample-prd.md, docs/draft-prd.md]
---

# Eval: /assess-document

## Purpose

Reads a document and produces a scored quality assessment report across six dimensions (completeness, clarity, consistency, specificity, structure, feasibility). Good output is a saved markdown or JSON file with dimensional scores, categorized issues (CRITICAL/WARNING/SUGGESTION), and actionable recommendations.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/sample-prd.md` | Well-formed PRD; expect score 3.5–4.5, few critical issues |
| `docs/draft-prd.md` | Incomplete PRD; expect score 2–3, multiple critical issues |

## Test Scenarios

### S1: Happy path — well-formed document

**Invocation:** `/assess-document fixtures/docs/sample-prd.md`

**Must:**
- [ ] Creates `reports/assessment-sample-prd-*.md` (timestamp-named file)
- [ ] Report contains a score table with all 6 dimensions
- [ ] Overall score is between 3.5 and 4.5
- [ ] At least 2 issues identified (even a good doc has improvements)
- [ ] Executive summary section is present
- [ ] "Saved to" path is reported to user in final summary

**Should:**
- [ ] Identifies that Section 8 "Open Questions" states "None — all resolved" as a strength
- [ ] Flags at least one SUGGESTION-level issue
- [ ] Issue list includes location references (section names or line refs)

**Must NOT:**
- [ ] Modify `fixtures/docs/sample-prd.md`
- [ ] Create output outside `reports/` directory
- [ ] Score overall below 3.0 for this well-formed document

---

### S2: Happy path — draft/incomplete document

**Invocation:** `/assess-document fixtures/docs/draft-prd.md`

**Must:**
- [ ] Creates `reports/assessment-draft-prd-*.md`
- [ ] Overall score is between 2.0 and 3.0
- [ ] At least 2 CRITICAL issues identified (TBDs, missing success criteria, vague requirements)
- [ ] "Completeness" dimension is scored lower than "Clarity"

**Should:**
- [ ] Calls out the "TBD" markers specifically as gaps
- [ ] Notes missing success criteria in Section 6

**Must NOT:**
- [ ] Score overall above 3.5 for this clearly incomplete document

---

### S3: JSON output format

**Invocation:** `/assess-document fixtures/docs/draft-prd.md --format json`

**Must:**
- [ ] Creates `reports/assessment-draft-prd-*.json` (not .md)
- [ ] Output is valid JSON
- [ ] JSON contains `scores` object with all 6 dimension keys
- [ ] JSON contains `issues` array with at least 2 items
- [ ] Each issue has `severity`, `category`, `description`, `recommendation` fields

**Must NOT:**
- [ ] Create a markdown file when `--format json` is specified

---

### S4: Focused analysis

**Invocation:** `/assess-document fixtures/docs/draft-prd.md --focus completeness,specificity`

**Must:**
- [ ] Output includes "Focused analysis — only completeness, specificity evaluated" note
- [ ] Score table contains only 2 dimension rows (not 6)
- [ ] Overall score is the average of only those 2 dimensions

**Must NOT:**
- [ ] Include findings for clarity, consistency, structure, or feasibility
- [ ] Score table contains rows for unfocused dimensions

---

### S5: Error — file not found

**Invocation:** `/assess-document fixtures/docs/nonexistent.md`

**Must:**
- [ ] Displays error message containing "not found" or "File not found"
- [ ] Does not create any file in `reports/`
- [ ] Does not throw an unhandled exception (clean error)

---

### S6: Error — missing argument (interactive prompt)

**Invocation:** `/assess-document` (no arguments)

**Must:**
- [ ] Prompts user for document path
- [ ] Does not immediately error out

---

### S7: Error — missing argument with --no-prompt

**Invocation:** `/assess-document --no-prompt`

**Must:**
- [ ] Displays usage error with example invocations
- [ ] Exits without prompting

---

### S8: Invalid --focus dimension

**Invocation:** `/assess-document fixtures/docs/sample-prd.md --focus clarity,badvalue`

**Must:**
- [ ] Displays error listing "badvalue" as an invalid dimension
- [ ] Lists valid dimension names

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Output file created with correct naming convention | Required |
| Score is calibrated (well-formed doc scores higher than draft) | Required |
| Issues are categorized with severity levels | Required |
| Each issue has a location reference | Should |
| Executive summary is substantive (2+ sentences) | Should |
| Error scenarios produce clean messages without creating output files | Required |
