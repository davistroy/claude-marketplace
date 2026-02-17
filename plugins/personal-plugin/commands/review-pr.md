---
description: Structured PR review with security, performance, and code quality analysis
allowed-tools: Bash(gh:*), Bash(git:*)
---

# PR Review Command

Perform a comprehensive review of a GitHub Pull Request, analyzing code changes for security concerns, performance implications, code style compliance, test coverage, and documentation needs.

## Input Validation

**Required Arguments:**
- `<pr-number-or-url>` - PR number (e.g., `123`) or full GitHub PR URL

**Validation:**
If arguments are missing, display:
```text
Usage: /review-pr <pr-number-or-url>

Examples:
  /review-pr 123                                    # Review PR #123
  /review-pr https://github.com/owner/repo/pull/42 # Review from URL

The command will:
  1. Fetch PR details and diff
  2. Analyze changes for issues
  3. Generate a structured review
  4. Optionally post the review to GitHub
```

If the PR number is invalid or not found, display:
```text
Error: PR #[number] not found.

Verify:
  - The PR number is correct
  - You have access to this repository
  - The GitHub CLI is authenticated (run: gh auth status)
```

## Instructions

### Phase 1: Fetch PR Information

Use the GitHub CLI to gather PR context:

```bash
# Get PR details
gh pr view [number] --json title,body,author,baseRefName,headRefName,files,additions,deletions,changedFiles,labels,reviewRequests

# Get the diff
gh pr diff [number]

# Get existing reviews if any
gh pr view [number] --json reviews
```

Parse the PR URL if provided to extract owner/repo and PR number.

### Phase 2: Analyze Changes

Review the diff systematically across these dimensions:

#### 2.1 Security Analysis

Check for:
- Hardcoded secrets, API keys, or credentials
- SQL injection vulnerabilities
- XSS vulnerabilities in web code
- Insecure dependencies being added
- Unsafe file operations
- Missing input validation
- Authentication/authorization changes
- Sensitive data exposure in logs

**Flag with severity (see common-patterns.md):**
- **CRITICAL**: Direct security vulnerabilities
- **WARNING**: Potential security issues requiring review
- **SUGGESTION**: Security-related improvements

#### 2.2 Performance Analysis

Check for:
- N+1 query patterns
- Unbounded loops or recursion
- Large file reads into memory
- Missing pagination
- Inefficient algorithms (O(n^2) when O(n) is possible)
- Blocking operations in async contexts
- Missing caching opportunities
- Unnecessary re-renders (React/frontend)

#### 2.3 Code Quality Analysis

Check for:
- Violations of DRY principle
- Functions/methods that are too long (>50 lines)
- High cyclomatic complexity
- Inconsistent naming conventions
- Missing or inadequate error handling
- Magic numbers without constants
- Dead code or unused imports
- Unclear variable/function names

Reference CLAUDE.md patterns if available in the repository.

#### 2.4 Test Coverage Analysis

Check for:
- New code paths without tests
- Modified code with outdated tests
- Missing edge case coverage
- Test quality (not just presence)
- Integration test needs
- Missing mock/stub for external services

#### 2.5 Documentation Analysis

Check for:
- Public APIs without documentation
- Complex logic without comments
- README updates needed for new features
- Changelog entries needed
- Breaking changes without migration notes

### Phase 3: Generate Review Report

Create a structured review with this format:

```markdown
# PR Review: [PR Title]

**PR:** #[number] by @[author]
**Branch:** [head] -> [base]
**Changes:** +[additions] -[deletions] across [files] files

---

## Summary

[2-3 sentence summary of what this PR does and its overall quality]

---

## Issues Found

### CRITICAL Issues (Must Fix)

[List critical issues that block approval]

#### C1. [Issue Title]
**File:** `path/to/file.ext` (line X-Y)
**Issue:** [Description]
**Suggestion:** [How to fix]

### WARNING Issues (Should Fix)

[List important issues that should be addressed]

#### W1. [Issue Title]
...

### SUGGESTION Issues (Nice to Have)

[List minor improvements and nice-to-haves]

#### S1. [Issue Title]
...

---

## Analysis Summary

| Category | Status | Notes |
|----------|--------|-------|
| Security | [PASS/WARN/FAIL] | [Brief note] |
| Performance | [PASS/WARN/FAIL] | [Brief note] |
| Code Quality | [PASS/WARN/FAIL] | [Brief note] |
| Test Coverage | [PASS/WARN/FAIL] | [Brief note] |
| Documentation | [PASS/WARN/FAIL] | [Brief note] |

---

## Recommendation

**[APPROVE / REQUEST_CHANGES / COMMENT]**

[Reasoning for the recommendation]

---

## Files Reviewed

[List of files with brief notes on each]

- `file1.ext` - [Brief note]
- `file2.ext` - [Brief note]
```

### Phase 4: Offer to Post Review

After generating the report, ask the user:

```text
Review complete. Would you like me to post this review to GitHub?

Options:
  1. Post as APPROVE (if no critical/warning issues)
  2. Post as REQUEST_CHANGES (if critical issues found)
  3. Post as COMMENT (observations only)
  4. Don't post (just keep the local report)

Enter your choice (1-4):
```

If the user chooses to post, use:

```bash
# For approval
gh pr review [number] --approve --body "[review body]"

# For request changes
gh pr review [number] --request-changes --body "[review body]"

# For comment only
gh pr review [number] --comment --body "[review body]"
```

### Phase 5: Report Results

Display final summary:

```yaml
PR Review Complete
==================

PR: #[number] - [title]
Recommendation: [APPROVE/REQUEST_CHANGES/COMMENT]

Issues Found:
  CRITICAL: [count]
  WARNING: [count]
  SUGGESTION: [count]

[If posted] Review posted to GitHub: [URL]
[If not posted] Review saved locally.
```

## Review Guidelines

### Be Constructive
- Focus on the code, not the person
- Explain *why* something is an issue
- Provide specific suggestions for improvement
- Acknowledge good patterns and improvements

### Be Thorough But Efficient
- Review all changed files
- Focus more on complex/critical changes
- Don't nitpick minor style issues if not project convention
- Consider the PR's stated goals

### Consider Context
- Is this a hotfix or feature work?
- What's the project's maturity level?
- Are there existing patterns to follow?
- Is this a refactor or new functionality?

### Prioritize Correctly
- Security > Correctness > Performance > Style
- Breaking changes need extra scrutiny
- Public APIs need more documentation

## Error Handling

- **gh not installed:** Display installation instructions
- **Not authenticated:** Prompt `gh auth login`
- **PR not found:** Verify number and permissions
- **Rate limited:** Wait and retry, or use local diff
- **Large PR:** Warn about review scope, offer to focus on specific files

## Example Usage

```yaml
User: /review-pr 42

Claude: [Fetches PR #42, analyzes diff]

# PR Review: Add user authentication module

**PR:** #42 by @developer
**Branch:** feature/auth -> main
**Changes:** +450 -23 across 12 files

---

## Summary

This PR adds a comprehensive authentication module with JWT support. The implementation is solid overall, but there are a few security considerations that should be addressed before merging.

---

## Issues Found

### CRITICAL Issues (Must Fix)

#### C1. JWT Secret Hardcoded
**File:** `src/auth/config.ts` (line 15)
**Issue:** JWT secret is hardcoded in source code
**Suggestion:** Move to environment variable: `process.env.JWT_SECRET`

### WARNING Issues (Should Fix)

#### W1. Missing Rate Limiting
**File:** `src/auth/login.ts` (lines 20-45)
**Issue:** Login endpoint has no rate limiting, vulnerable to brute force
**Suggestion:** Add rate limiting middleware (e.g., express-rate-limit)

...

## Recommendation

**REQUEST_CHANGES**

The authentication implementation is well-structured, but the hardcoded JWT secret is a critical security issue that must be fixed before merging.

---

Review complete. Would you like me to post this review to GitHub?
```
