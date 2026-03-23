---
command: finish-document
type: command
fixtures: [docs/draft-prd.md]
---

# Eval: /finish-document

## Purpose

Full pipeline: extracts questions from a document (like `/define-questions`), walks through answering them interactively (like `/ask-questions`), then updates the document with the answers. Good behavior: the source document is updated in place with answers incorporated, and TBD/open question markers are resolved.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/draft-prd.md` | Incomplete PRD with TBDs and open questions to resolve |

## Test Scenarios

### S1: Full pipeline — extract, answer, update

**Setup:** Copy `fixtures/docs/draft-prd.md` to a working copy (e.g., `working-draft-prd.md`) to avoid modifying the fixture.

**Invocation:** `/finish-document working-draft-prd.md`

**Must:**
- [ ] Extracts questions from the document (mentions count of questions found)
- [ ] Presents questions one at a time for interactive answering
- [ ] After all answers collected, updates the document with answers incorporated
- [ ] TBD markers in the document are replaced with the provided answers
- [ ] Updated document is still valid markdown

**Should:**
- [ ] Creates a backup of the original before modification (or mentions it's updating in place)
- [ ] Reports which sections were updated

**Must NOT:**
- [ ] Modify the document before all questions are answered
- [ ] Delete sections of the document while incorporating answers
- [ ] Leave raw Q&A output in the document body (answers should be integrated, not appended)

---

### S2: Aborted session (user quits mid-way)

**Setup:** Start the Q&A, answer 2 questions, then respond "quit" or "exit".

**Must:**
- [ ] Stops the Q&A session cleanly
- [ ] Either saves partial progress or asks whether to save
- [ ] Does not leave the document in a partially-modified state without warning

---

### S3: Document with no open questions

**Setup:** Use `fixtures/docs/sample-prd.md` which has no TBDs.

**Invocation:** `/finish-document fixtures/docs/sample-prd.md`

**Must:**
- [ ] Reports "No open questions found" or equivalent
- [ ] Does not modify the document

---

### S4: Error — file not found

**Invocation:** `/finish-document nonexistent.md`

**Must:**
- [ ] Error message for missing file
- [ ] No modification attempted

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Questions extracted and presented one at a time | Required |
| Document updated with answers after all questions answered | Required |
| TBD markers resolved in updated document | Required |
| Source document integrity maintained | Required |
| Abort handling does not corrupt document | Required |
