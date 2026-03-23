---
command: review-pr
type: command
fixtures: []
---

# Eval: /review-pr

## Purpose

Performs a structured code review of a pull request, covering security, performance, and code quality. Good output: specific findings with file and line references, severity ratings, and actionable recommendations.

## Fixtures

None — requires a GitHub PR to review. Use a real or test PR from the marketplace repo.

## Setup

Create a simple test PR against the marketplace repo for eval purposes, or use a recent real PR.

## Test Scenarios

### S1: Happy path — review a real PR

**Setup:** Have a PR number ready (e.g., an open PR against the marketplace repo).

**Invocation:** `/review-pr <PR-number>` or `/review-pr` (prompts for PR)

**Must:**
- [ ] Fetches the PR diff (via `gh pr diff` or equivalent)
- [ ] Produces findings organized by severity (CRITICAL, HIGH, MEDIUM, LOW)
- [ ] Each finding includes: description, file path and line reference, recommendation
- [ ] Produces a summary at the end (total findings count by severity)

**Should:**
- [ ] Checks for security issues (hardcoded secrets, injection risks)
- [ ] Checks for obvious bugs in changed code
- [ ] Notes positive aspects ("looks good, no security concerns in auth flow")

**Must NOT:**
- [ ] Create any commits or push anything
- [ ] Approve or merge the PR
- [ ] Fabricate findings for code that was not changed

---

### S2: PR with no concerns

**Setup:** A trivial PR (e.g., fixing a typo in a README).

**Must:**
- [ ] Reports "no significant findings" or equivalent
- [ ] Does not fabricate issues to seem thorough

---

### S3: Error — invalid PR number

**Invocation:** `/review-pr 99999999`

**Must:**
- [ ] Displays error indicating the PR was not found
- [ ] Does not crash

---

### S4: Missing argument (interactive)

**Invocation:** `/review-pr` (no PR number)

**Must:**
- [ ] Prompts for the PR number or URL

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Findings reference specific files/lines from the diff | Required |
| Severity levels used correctly | Required |
| No commits or merges performed | Required |
| Does not fabricate findings for unchanged code | Required |
| Summary count of findings provided | Should |
