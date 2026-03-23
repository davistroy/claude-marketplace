---
command: define-questions
type: command
fixtures: [docs/draft-prd.md, docs/sample-prd.md]
---

# Eval: /define-questions

## Purpose

Analyzes a document and extracts all open questions, TBDs, ambiguities, and gaps into a structured JSON file. Good output: a valid JSON file compatible with the questions schema, containing every actionable open item from the document.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/draft-prd.md` | PRD with 6 explicit open questions + multiple TBDs embedded in text |
| `docs/sample-prd.md` | Complete PRD with "None" open questions — tests the no-questions case |

## Test Scenarios

### S1: Happy path — document with open questions

**Invocation:** `/define-questions fixtures/docs/draft-prd.md`

**Must:**
- [ ] Creates `reference/questions-draft-prd-*.json` (timestamped)
- [ ] Output is valid JSON
- [ ] JSON contains `questions` array with at least 5 questions (doc has 6 explicit + implicit gaps)
- [ ] JSON contains `metadata` object with `source_document`, `total_questions`, `generated_date`
- [ ] Each question has `id`, `question`, `context`, `priority` fields
- [ ] Schema validation PASSED is reported

**Should:**
- [ ] Captures the 6 questions from Section 7 "Open Questions"
- [ ] Also captures the TBD items embedded in Sections 1.2, 3.1, 3.2, 4.1 (implicit questions)
- [ ] Priority assignments are reasonable (time zone handling = high, data retention = medium)
- [ ] Questions are deduplicated (same question not listed twice)

**Must NOT:**
- [ ] Invent questions not derivable from the document
- [ ] Miss the explicit "TBD" markers

---

### S2: Document with no open questions

**Invocation:** `/define-questions fixtures/docs/sample-prd.md`

**Must:**
- [ ] Either: reports "No questions, open items, or TBDs found" (document appears complete)
- [ ] Or: produces a JSON with 0 questions and a note
- [ ] Does not generate a file with fabricated questions for a complete document

**Should:**
- [ ] Suggests running `/assess-document` for a quality check

---

### S3: CSV format

**Invocation:** `/define-questions fixtures/docs/draft-prd.md --format csv`

**Must:**
- [ ] Creates `reference/questions-draft-prd-*.csv` (not .json)
- [ ] CSV has header row: `id,question,context,topic,sections,priority`
- [ ] CSV is valid (no unescaped commas breaking fields)

---

### S4: Preview mode

**Invocation:** `/define-questions fixtures/docs/draft-prd.md --preview`

**Must:**
- [ ] Shows question count and topic breakdown before saving
- [ ] Shows schema validation status
- [ ] Asks "Save this file? (y/n)"
- [ ] On "n" response: does not create the file

---

### S5: Error — file not found

**Invocation:** `/define-questions fixtures/docs/nonexistent.md`

**Must:**
- [ ] Error message: "Document not found at [path]"
- [ ] No output file created

---

### S6: Schema validation failure

**Setup:** Temporarily corrupt the question generation logic by testing with `--force`.

**Invocation:** `/define-questions fixtures/docs/draft-prd.md --force`

**Must:**
- [ ] If validation fails with --force, saves with warning message
- [ ] Warning clearly states "schema validation failed"

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Captures ≥ 5 questions from draft-prd.md | Required |
| JSON schema valid (all required fields present) | Required |
| Schema validation status reported | Required |
| No fabricated questions for complete docs | Required |
| Timestamped output file in `reference/` | Required |
