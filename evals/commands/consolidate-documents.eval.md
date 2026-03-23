---
command: consolidate-documents
type: command
fixtures: [docs/multi-variant-a.md, docs/multi-variant-b.md]
---

# Eval: /consolidate-documents

## Purpose

Reads multiple document variants covering the same topic and synthesizes a single, superior consolidated document that captures the best elements from each. Good output: a single document that is more complete than either input alone, clearly resolves contradictions, and attributes key points when appropriate.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/multi-variant-a.md` | REST API design proposal |
| `docs/multi-variant-b.md` | GraphQL API design proposal — same topic, different perspective |

## Test Scenarios

### S1: Two-variant consolidation

**Invocation:** `/consolidate-documents fixtures/docs/multi-variant-a.md fixtures/docs/multi-variant-b.md`

**Must:**
- [ ] Creates a single output document (consolidated version)
- [ ] Output covers both REST and GraphQL perspectives
- [ ] Output includes the "Strengths" and "Weaknesses" content from both variants
- [ ] Output makes a clear recommendation (does not just list both options without synthesis)
- [ ] Output is saved to a timestamped file

**Should:**
- [ ] Notes that both variants agree on the OAuth 2.0 authentication approach
- [ ] Notes where variants disagreed (implementation cost, team experience)
- [ ] Output is better organized than either input alone

**Must NOT:**
- [ ] Simply concatenate the two files end-to-end
- [ ] Delete or modify the original fixture files
- [ ] Invent technical details not present in either source

---

### S2: Single file (edge case)

**Invocation:** `/consolidate-documents fixtures/docs/multi-variant-a.md`

**Must:**
- [ ] Either gracefully handles a single file (returns it as-is with a note) or asks for a second file
- [ ] Does not crash

---

### S3: Error — file not found

**Invocation:** `/consolidate-documents fixtures/docs/multi-variant-a.md fixtures/docs/nonexistent.md`

**Must:**
- [ ] Displays error for the missing file
- [ ] Does not create partial output

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Output synthesizes both inputs rather than concatenating | Required |
| Contradictions resolved with explicit reasoning | Required |
| Recommendation or decision provided | Required |
| Source documents not modified | Required |
| Output saved to timestamped file | Required |
