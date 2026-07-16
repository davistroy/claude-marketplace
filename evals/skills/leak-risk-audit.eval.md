---
command: leak-risk-audit
type: skill
fixtures: []
---

# Eval: /leak-risk-audit (skill)

## Purpose

Audits a dataset for proprietary information leaks before it's shared with public/cloud services, producing a `LEAK_RISK.md` report. Dispatches 4 parallel `context: fork` subagents (one per severity tier: CRITICAL, HIGH, MEDIUM, LOW), aggregates their JSON findings, and writes the report itself (subagents never write files). Good behavior: err toward flagging over silence, catch obfuscated variants (underscore-joined, email-embedded, possessive, typo, Unicode), and never leak the actual company/individual name verbatim in the report itself.

## Fixtures

None — operates on a user-supplied dataset path (CSV/JSON/JSONL/TSV/XLSX).

## Test Scenarios

### S1: Happy path — dataset audit

**Invocation:** `/leak-risk-audit <path-to-dataset>`

**Must:**
- [ ] Builds a file inventory and reads a representative sample (or all rows, for small files)
- [ ] Dispatches 4 `context: fork` subagents in parallel (one per severity tier), not sequentially
- [ ] Each subagent returns structured JSON findings; only the parent aggregates and writes `LEAK_RISK.md`
- [ ] Report includes an Overall risk rating (BLOCKED/CONDITIONAL PASS/PASS), Findings by Severity tables (CRITICAL/HIGH/MEDIUM/LOW), a Cross-Reference Risk Assessment, and specific (not vague) remediation per finding
- [ ] IDs are renumbered sequentially per tier (C-1, C-2, H-1, ...)

**Must NOT:**
- [ ] Have a subagent write `LEAK_RISK.md` or any output file directly
- [ ] Rely on reading only a handful of rows and guessing instead of programmatic scanning

---

### S2: Missing dataset path

**Invocation:** `/leak-risk-audit` (no path)

**Must:**
- [ ] Asks the user for the dataset path rather than guessing one

---

### S3: Low-confidence finding still reported

**Setup:** A potential finding is roughly 60% confident (a term that's ambiguous but plausibly proprietary).

**Must:**
- [ ] Flags it in the report with `confidence: LOW` (or MEDIUM) rather than omitting it
- [ ] Does not drop a finding purely for being unsure ("err on the side of caution")

---

### S4: A severity-tier subagent fails or times out

**Must:**
- [ ] Retries that subagent once
- [ ] If it still fails, notes that tier's coverage as incomplete in the Appendix: Scan Methodology rather than silently omitting its findings from the report

---

### S5: `--glossary` path unreadable

**Invocation:** `/leak-risk-audit <path> --glossary <bad-path>`

**Must:**
- [ ] Proceeds with severity-tier scanning regardless
- [ ] Notes the missing/unreadable glossary in the Replacement Quality Assessment section instead of failing the whole audit

---

### S6: Report does not leak the real name

**Setup:** The dataset contains an actual identifiable company or individual name.

**Must:**
- [ ] References the identified entity obliquely in `LEAK_RISK.md` (e.g., "the original company name") rather than printing it verbatim
- [ ] Still accurately conveys the finding's severity and remediation without the verbatim name

---

### S7: Variant completeness for a sanitized dataset

**Setup:** Dataset was previously desensitized; the original company name has some inconsistently-caught variants (e.g., email-embedded `name@vendor.com`, underscore-joined `name_platform`).

**Must:**
- [ ] Flags the inconsistent variants specifically (not just "sanitization looks incomplete")
- [ ] Replacement Quality Assessment names the specific missed variant pattern with an example

## Rubric

| Criterion | Pass Threshold |
|-----------|-----------------|
| 4 severity-tier subagents dispatched in parallel via `context: fork` | Required |
| Only the parent writes `LEAK_RISK.md`; subagents return JSON only | Required |
| Low-confidence findings are still surfaced, never silently dropped | Required |
| Report never contains the real company/individual name verbatim | Required |
| Missing dataset path prompts the user instead of guessing | Required |
| Subagent failure degrades to noted incomplete coverage, not silent omission | Required |
| Variant-completeness gaps are named specifically with examples | Should |
