---
command: convert-markdown
type: command
fixtures: [docs/sample-prd.md]
---

# Eval: /convert-markdown

## Purpose

Converts a markdown file to a nicely formatted Microsoft Word document (.docx). Good output: a .docx file that preserves all headings, tables, bullet lists, and code blocks from the source markdown.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/sample-prd.md` | Well-structured PRD with headings, tables, bullets |

## Test Scenarios

### S1: Happy path — convert PRD to Word

**Invocation:** `/convert-markdown fixtures/docs/sample-prd.md`

**Must:**
- [ ] Creates a `.docx` file named after the source (e.g., `sample-prd.docx`)
- [ ] Reports the output file path to the user
- [ ] Does not modify the source markdown file

**Should:**
- [ ] Tables in the markdown appear as proper Word tables in the .docx
- [ ] Headings are mapped to Word heading styles (H1 → Heading 1, etc.)
- [ ] Output path is in the same directory as the source or a specified output directory

**Must NOT:**
- [ ] Delete or overwrite the source `.md` file
- [ ] Create a zero-byte .docx file

---

### S2: Error — file not found

**Invocation:** `/convert-markdown fixtures/docs/nonexistent.md`

**Must:**
- [ ] Error message referencing the missing file
- [ ] No output file created

---

### S3: Error — non-markdown file

**Invocation:** `/convert-markdown fixtures/json/questions-sample.json`

**Must:**
- [ ] Either converts the JSON as plain text with a warning, or rejects with a clear error
- [ ] Does not silently produce a corrupted .docx

---

### S4: Dependency check — pandoc or python-docx

**Setup:** Ensure the required conversion tool is installed (pandoc or python-docx depending on implementation).

**Must:**
- [ ] If the required tool is missing, displays a clear installation instruction
- [ ] Does not fail silently

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| .docx file created | Required |
| Source markdown not modified | Required |
| Structural elements preserved (headings, tables, lists) | Should |
| Output file path reported to user | Required |
| Missing dependency handled gracefully | Required |
