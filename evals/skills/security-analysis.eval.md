---
command: security-analysis
type: skill
fixtures: []
---

# Eval: /security-analysis (skill)

## Purpose

Comprehensive security analysis with tech stack detection, vulnerability scanning, and remediation planning. Good output: specific, actionable security findings with severity ratings, file references, and a remediation plan — not a generic security checklist.

## Fixtures

None — operates on the current repository.

## Test Scenarios

### S1: Analyze marketplace repo

**Invocation:** `/security-analysis`

**Must:**
- [ ] Identifies the tech stack (Node.js, Python tools, bash scripts)
- [ ] Scans for hardcoded secrets, credentials, or API keys in source files
- [ ] Produces findings organized by severity (CRITICAL, HIGH, MEDIUM, LOW)
- [ ] Findings reference specific files and line numbers
- [ ] Produces a remediation plan

**Should:**
- [ ] Notes that `.env` files are gitignored (positive finding)
- [ ] Notes Bitwarden secrets management as a positive security practice
- [ ] Identifies any shell scripts that use unquoted variables (injection risk)

**Must NOT:**
- [ ] Modify any files
- [ ] Fabricate CRITICAL findings if none exist
- [ ] Give generic security advice not grounded in the actual codebase

---

### S2: Findings are codebase-specific

**Must:**
- [ ] At least 2 findings reference actual files from this repo (not generic "check for SQL injection" for a project with no SQL)

---

### S3: Remediation plan quality

**Must:**
- [ ] Each HIGH/CRITICAL finding has a concrete remediation step
- [ ] Remediations are ordered by priority

---

### S4: Read-only behavior

**Must:**
- [ ] Does not modify any files
- [ ] Does not install tools or packages

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Tech stack correctly identified | Required |
| Findings are codebase-specific | Required |
| File/line references in findings | Required |
| No files modified | Required |
| Remediation plan included | Required |
