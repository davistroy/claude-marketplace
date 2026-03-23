---
command: remove-ip
type: command
fixtures: [docs/ip-document.md]
---

# Eval: /remove-ip

## Purpose

Sanitizes a document by removing or replacing company identifiers, employee names, internal URLs, and proprietary tool names while preserving the document's meaning and utility. Good output: a sanitized version where specific identifiers are replaced with generic equivalents and no original identifiers remain.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/ip-document.md` | Internal doc with "Acme Corp", "Sarah Johnson", "Mike Chen", "IntelliFlow", "ProjectNova", internal URLs |

## Test Scenarios

### S1: Happy path — sanitize internal doc

**Invocation:** `/remove-ip fixtures/docs/ip-document.md`

**Must:**
- [ ] Creates a sanitized output file (e.g., `ip-document-sanitized.md` or timestamped variant)
- [ ] "Acme Corp" is replaced throughout
- [ ] "Sarah Johnson" is replaced throughout
- [ ] "Mike Chen" is replaced throughout
- [ ] "IntelliFlow" is replaced throughout
- [ ] "ProjectNova" is replaced throughout
- [ ] `acmecorp.internal`, `acmecorp.slack.com`, `acmecorp-engineering` URLs/hostnames are replaced or removed
- [ ] `sarah.johnson@acmecorp.com` email address is replaced
- [ ] Original fixture file is NOT modified

**Should:**
- [ ] Replacements are consistent (same company name → same generic replacement throughout)
- [ ] Generic replacements make semantic sense in context (e.g., "[Company]", "[Internal Wiki Tool]")
- [ ] Document structure and non-sensitive content are preserved

**Must NOT:**
- [ ] Modify `fixtures/docs/ip-document.md` in place
- [ ] Leave any of the specific identifiers listed above in the output
- [ ] Remove entire sections that only need identifier replacement

---

### S2: Already-sanitized document (idempotent)

**Setup:** Run remove-ip on the output of S1 (a document that is already sanitized).

**Must:**
- [ ] Reports "no identifiers found" or produces identical output
- [ ] Does not introduce new errors or corruption

---

### S3: Error — file not found

**Invocation:** `/remove-ip fixtures/docs/nonexistent.md`

**Must:**
- [ ] Error message for missing file
- [ ] No output file created

---

### S4: Preview / dry-run

**Invocation:** `/remove-ip fixtures/docs/ip-document.md --preview` (if supported)

**Must:**
- [ ] Shows what would be replaced without writing output
- [ ] Lists the identifiers it found

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| All specific identifiers removed from output | Required |
| Source document not modified | Required |
| Replacements are consistent (not random per occurrence) | Required |
| Document meaning and structure preserved | Required |
| Output file created with clear naming | Required |
