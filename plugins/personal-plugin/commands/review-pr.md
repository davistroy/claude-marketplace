---
description: Structured PR review with security, performance, and code quality analysis
allowed-tools: Read, Bash(gh:*), Bash(git:*)
# MCP tools used (no allowed-tools declaration needed): pull_request_read, add_comment_to_pending_review, pull_request_review_write
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

## Severity Definitions

Use these severity levels consistently throughout the review:

| Severity | Definition | Examples |
|----------|-----------|----------|
| **CRITICAL** | Security vulnerability, data loss risk, or production crash. Must fix before merge. | Hardcoded secrets, SQL injection, unhandled null pointer on critical path |
| **HIGH** | Logic error, missing validation, or broken feature. Should fix before merge. | Incorrect business logic, missing auth check, race condition |
| **MEDIUM** | Code quality issue, missing test, or unclear logic. Should fix but not a blocker. | Long functions, missing edge case tests, unclear naming |
| **LOW** | Style, naming, minor optimization, or minor documentation gaps. Nice to have. | Variable naming, minor refactor opportunity, comment typo |
| **INFO** | Observation, positive feedback, or context-only note. No action required. | Good pattern usage, architectural observation, FYI note |

## Review Guidelines

Establish these guidelines BEFORE beginning the review analysis.

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

## Instructions

### Phase 0: Determine Tool Availability

This command supports two modes of GitHub interaction:

| Mode | Tools Used | Capability |
|------|-----------|------------|
| **MCP (primary)** | `pull_request_read`, `add_comment_to_pending_review`, `pull_request_review_write` | Line-level review comments on specific files and lines |
| **gh CLI (fallback)** | `gh pr view`, `gh pr diff`, `gh pr review` | Single review body comment (no line-level precision) |

**Detection:** Attempt to use `pull_request_read` first. If the MCP tool is available, use MCP mode for all phases. If it fails or is unavailable, fall back to `gh` CLI mode.

Parse the PR URL if provided to extract owner, repo, and PR number. For `gh` CLI fallback, the owner/repo can be inferred from the current git remote.

### Phase 1: Fetch PR Information

#### MCP Mode (Primary)

Use `pull_request_read` to gather PR context:

1. **Get PR details** — Call `pull_request_read` with method `get`, providing `owner`, `repo`, and `pullNumber`. This returns title, body, author, base/head branches, labels, and review requests.

2. **Get the diff** — Call `pull_request_read` with method `get_diff`. This returns the full diff of all changes in the PR.

3. **Get changed files list** — Call `pull_request_read` with method `get_files`. This returns the list of files changed with additions/deletions counts per file. Use pagination parameters (`page`, `perPage`) for large PRs.

4. **Get existing reviews** — Call `pull_request_read` with method `get_reviews` to see any prior reviews.

#### gh CLI Fallback

If MCP tools are not available, fall back to `gh` CLI:

```bash
# Get PR details
gh pr view [number] --json title,body,author,baseRefName,headRefName,files,additions,deletions,changedFiles,labels,reviewRequests

# Get the diff
gh pr diff [number]

# Get existing reviews if any
gh pr view [number] --json reviews
```

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

**Flag with severity (see Severity Definitions above):**
- **CRITICAL**: Direct security vulnerabilities (hardcoded secrets, injection, auth bypass)
- **HIGH**: Potential security issues requiring review (missing input validation, insecure defaults)
- **MEDIUM**: Security-related improvements (missing rate limiting, verbose error messages)

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

### HIGH Issues (Should Fix)

[List important issues that should be addressed]

#### H1. [Issue Title]
...

### MEDIUM Issues (Should Fix, Not Blocking)

[List code quality issues and missing tests]

#### M1. [Issue Title]
...

### LOW Issues (Nice to Have)

[List minor improvements and style suggestions]

#### L1. [Issue Title]
...

### INFO (Observations)

[List positive feedback and context-only notes]

#### I1. [Issue Title]
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

#### MCP Mode (Primary) — Line-Level Comments

When MCP tools are available, post the review with line-level comments for each finding:

**Step 1: Create a pending review**

Call `pull_request_review_write` with:
- `method`: `create`
- `owner`, `repo`, `pullNumber`
- Do NOT include `event` — this creates a pending (draft) review

**Step 2: Add line-level comments for each finding**

For each issue found during analysis (CRITICAL, HIGH, MEDIUM, LOW, INFO), call `add_comment_to_pending_review` with:
- `owner`, `repo`, `pullNumber`
- `path`: the relative file path where the issue was found
- `line`: the specific line number in the diff (for multi-line issues, this is the last line of the range)
- `startLine`: (for multi-line comments) the first line of the range
- `side`: `RIGHT` (commenting on the new/changed code)
- `startSide`: `RIGHT` (for multi-line comments)
- `subjectType`: `LINE`
- `body`: Format as `**[SEVERITY]:** [Issue description]\n\n**Suggestion:** [How to fix]`

If a finding is file-level (not tied to a specific line), use `subjectType: FILE` instead and omit `line`/`side`.

**Step 3: Submit the review**

Call `pull_request_review_write` with:
- `method`: `submit_pending`
- `owner`, `repo`, `pullNumber`
- `body`: The review summary (from the Summary section of the report)
- `event`: One of:
  - `APPROVE` — no CRITICAL or HIGH issues found
  - `REQUEST_CHANGES` — CRITICAL or HIGH issues found
  - `COMMENT` — user chose comment-only

#### gh CLI Fallback

If MCP tools are not available, post as a single review body:

```bash
# For approval
gh pr review [number] --approve --body "[review body]"

# For request changes
gh pr review [number] --request-changes --body "[review body]"

# For comment only
gh pr review [number] --comment --body "[review body]"
```

**Note:** The `gh` CLI fallback posts the entire review as a single comment body. It does not support line-level comments. When using fallback mode, inform the user: "Posting review as a single comment (line-level comments require MCP GitHub tools)."

### Phase 5: Report Results

Display final summary:

```yaml
PR Review Complete
==================

PR: #[number] - [title]
Recommendation: [APPROVE/REQUEST_CHANGES/COMMENT]

Issues Found:
  CRITICAL: [count]
  HIGH: [count]
  MEDIUM: [count]
  LOW: [count]
  INFO: [count]

[If posted] Review posted to GitHub: [URL]
[If not posted] Review saved locally.
```

## Error Handling

Handle these error conditions gracefully:

| Error Condition | Detection | Recovery Action |
|----------------|-----------|-----------------|
| **gh CLI not installed** | `command -v gh` fails | Display: "GitHub CLI not found. Install from https://cli.github.com/ then run `gh auth login`" |
| **Not authenticated** | `gh auth status` fails | Display: "Not authenticated. Run `gh auth login` to authenticate with GitHub." |
| **PR not found** | `gh pr view` returns 404 | Display: "PR #[number] not found. Verify the PR number is correct and you have access to this repository." |
| **No permissions** | `gh pr view` returns 403 | Display: "Access denied for PR #[number]. You may not have read access to this repository. Check your GitHub permissions." |
| **Network error** | Connection timeout or DNS failure | Display: "Network error. Check your internet connection and try again." |
| **Rate limited** | 429 response from GitHub API | Display: "GitHub API rate limit reached. Wait a few minutes and try again, or use `gh api rate_limit` to check status." |
| **Diff exceeds context window** | Diff is extremely large (>500 files or >10,000 lines) | Warn user: "This PR has [N] changed files ([N] lines). Reviewing all changes may exceed context. Would you like to focus on specific files or directories?" |
| **Binary files in diff** | Diff contains binary file markers | Skip binary files with note: "Skipping binary file: [path] (binary files cannot be reviewed for code quality)" |
| **Already-merged PR** | PR state is "merged" | Inform user: "PR #[number] is already merged. Would you like to review the merge commit instead?" |
| **Draft PR** | PR is in draft state | Note: "PR #[number] is a draft. Proceeding with review — note that the author may still be making changes." |
| **Empty PR** | No changed files | Display: "PR #[number] has no changed files. Nothing to review." |
| **MCP tools unavailable** | `pull_request_read` call fails or is not recognized | Fall back to `gh` CLI mode. Inform user: "MCP GitHub tools not available. Using gh CLI fallback (line-level comments unavailable)." |
| **Pending review conflict** | `pull_request_review_write` create fails because a pending review already exists | Call `pull_request_review_write` with method `delete_pending` first, then retry creating a new pending review. |

## Related Commands

- `/review-arch` — Quick architectural audit of the full codebase (broader scope)
- `/review-intent` — Compare project intent vs implementation (complementary review)
- `/test-project` — Run comprehensive tests after PR review findings are addressed

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

### HIGH Issues (Should Fix)

#### H1. Missing Rate Limiting
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
