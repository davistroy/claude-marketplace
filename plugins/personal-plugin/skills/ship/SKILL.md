---
name: ship
allowed-tools: Bash(git:*), Bash(gh:*), Bash(tea:*)
description: Create branch, commit, push, open PR, auto-review, fix issues, and merge
---

You are automating the complete git workflow to ship code changes. After creating the PR, you will automatically review it, fix any issues, and merge it. The user may provide a branch name and description as arguments: $ARGUMENTS

## Input Validation

**Optional Arguments:**
- `<branch-name>` - Custom branch name (default: auto-generated from changes)
- `draft` - Create PR as draft
- `--dry-run` - Preview all operations without making any changes
- `--audit` - Log all git and PR operations to `.claude-plugin/audit.log` (see common-patterns.md)

**Dry-Run Mode:**
When `--dry-run` is specified:
- Show what branch name would be created
- Show what files would be staged and committed
- Show the proposed commit message
- Show the PR title and body that would be created
- Prefix all output with `[DRY-RUN]` to clearly indicate preview mode
- Do NOT execute any git commands that modify state (checkout, add, commit, push, pr create)

**Audit Mode:**
When `--audit` is specified:
- Log every git and PR operation to `.claude-plugin/audit.log`
- Each log entry is a JSON line with: timestamp, command, action, details, success
- Create `.claude-plugin/` directory if it doesn't exist
- Append to log file (never overwrite existing entries)

Example log entries:
```json
{"timestamp": "2026-01-14T10:30:00Z", "command": "ship", "action": "git_checkout", "details": {"branch": "feat/new-feature"}, "success": true}
{"timestamp": "2026-01-14T10:30:01Z", "command": "ship", "action": "git_commit", "details": {"sha": "abc1234", "message": "feat: add new feature"}, "success": true}
{"timestamp": "2026-01-14T10:30:02Z", "command": "ship", "action": "git_push", "details": {"remote": "origin", "branch": "feat/new-feature"}, "success": true}
{"timestamp": "2026-01-14T10:30:03Z", "command": "ship", "action": "pr_create", "details": {"number": 42, "url": "https://github.com/..."}, "success": true}
{"timestamp": "2026-01-14T10:30:30Z", "command": "ship", "action": "pr_merge", "details": {"number": 42, "strategy": "squash"}, "success": true}
```

## Pre-flight Checks
1. Verify this is a git repository
2. Confirm there are uncommitted changes (staged or unstaged) - if not, abort with a clear message
3. Confirm the current branch is `main` - if not, ask the user if they want to proceed from the current branch or abort

## Phase 0: Platform Detection

Detect the git hosting platform and select the appropriate CLI:

1. Parse `git remote -v` for the push remote URL
2. **If URL contains `github.com`** → set `PLATFORM=github`
   - Verify `gh auth status` succeeds
   - If `gh` is not installed or not authenticated, abort with install/auth instructions
3. **Otherwise** → set `PLATFORM=gitea`
   - Verify `tea login list` shows a login matching the remote URL's host
   - If `tea` is not installed, abort with: `Install tea CLI: https://gitea.com/gitea/tea`
   - If no matching login exists, abort with: `Run: tea login add --url <host-url> --name <name> --token <token>`
4. Store the platform choice for all subsequent steps
5. Display: `Platform detected: [GitHub|Gitea] (using [gh|tea] CLI)`

**Draft PR limitation:** The `tea` CLI does not support `--draft` for PR creation. When the `draft` argument is passed on a Gitea repo, warn the user that draft PRs are not supported on Gitea and create a normal PR instead.

## Execution Steps

### Step 1: Determine Branch Name
- If the user provided a branch name in arguments, use it
- If not, analyze the staged/unstaged changes and generate a descriptive kebab-case branch name (e.g., `fix-login-validation`, `add-user-export-feature`)
- Confirm the branch name with the user before proceeding

### Step 2: Create and Switch to New Branch
```bash
git checkout -b <branch-name>
```

### Step 3: Stage and Commit
- Stage all changes: `git add -A`
- Analyze the diff to generate a clear, conventional commit message
- Format: `<type>: <concise description>` (e.g., `feat: add CSV export for user data`)
- Include a body if changes are complex enough to warrant explanation
- Show the user the proposed commit message and proceed unless they object

### Step 4: Push to Remote
```bash
git push -u origin <branch-name>
```

### Step 5: Create Pull Request
- Set the PR title to match or expand on the commit message
- Generate a PR body that includes:
  - Summary of what changed and why
  - Key files modified
  - Any testing notes if apparent from the changes
- Target branch: `main`

**GitHub:**
```bash
gh pr create --title "..." --body "..." [--draft]
```

**Gitea:**
```bash
tea pr create --title "..." --description "..."
# Note: --draft is not supported by tea CLI
# If user requested draft, warn and create normal PR
```

- Open the PR as a draft if the user included "draft" in their arguments (GitHub only)

## Output
After completion, display:
- Branch name created
- Commit SHA
- Direct link to the PR

## Error Handling
- If any git command fails, stop immediately and show the error
- If push fails due to remote rejection, suggest possible causes
- If PR creation fails, provide the manual `gh pr create` or `tea pr create` command the user can run

---

## Phase 7: Auto-Review

After the PR is created, automatically analyze it for issues.

### 7.1 Fetch PR Information

**GitHub:**
```bash
# Get the PR number from the just-created PR
PR_NUMBER=$(gh pr view --json number -q '.number')

# Fetch the diff for analysis
gh pr diff $PR_NUMBER
```

**Gitea:**
```bash
# Get the PR number (parse from tea pr create output, or list open PRs)
PR_NUMBER=$(tea pr list --output json --fields index --state open | jq '.[0].index')

# Fetch the diff for analysis
tea pr view $PR_NUMBER --fields diff --output simple
```

### 7.2 Analyze the PR

Perform a comprehensive review across these dimensions:

**Security Analysis (CRITICAL/WARNING)**
- Hardcoded secrets, API keys, or credentials
- SQL injection vulnerabilities
- XSS vulnerabilities
- Insecure dependencies
- Missing input validation
- Authentication/authorization issues
- Sensitive data exposure in logs

**Performance Analysis (WARNING)**
- N+1 query patterns
- Unbounded loops or recursion
- Large file reads into memory
- Missing pagination
- Inefficient algorithms (O(n²) when O(n) possible)
- Blocking operations in async contexts

**Code Quality Analysis (WARNING)**
- DRY violations (copy-paste code)
- Functions/methods over 50 lines
- High cyclomatic complexity
- Inconsistent naming conventions
- Missing error handling
- Magic numbers without constants
- Dead code or unused imports

**Test Coverage Analysis (WARNING)**
- New code paths without tests
- Modified code with outdated tests
- Missing edge case coverage

**Documentation Analysis (WARNING for public APIs)**
- Public APIs without documentation
- Complex logic without comments
- Missing README updates for new features

### 7.3 Classify Issues

Categorize each issue by severity:
- **CRITICAL**: Must fix - blocks merge (security vulnerabilities, data integrity risks)
- **WARNING**: Should fix - blocks merge (quality issues, missing tests)
- **SUGGESTION**: Nice to have - does NOT block merge

### 7.4 Output

```
Phase 7: Auto-Review
====================
PR #[number] analyzed.

Issues Found:
  Critical: [N] (must fix)
  Warnings: [N] (should fix)
  Suggestions: [N] (non-blocking)

[If no blocking issues]
✓ All checks passed! Proceeding to merge.

[If blocking issues exist]
Found [N] blocking issues. Starting fix loop.
```

---

## Phase 8: Fix Loop

If there are CRITICAL or WARNING issues, attempt to fix them automatically.

### 8.1 Loop Parameters

- **Maximum attempts**: 5
- **Blocking issues**: CRITICAL + WARNING only (suggestions don't block)
- **Exit conditions**:
  - All blocking issues resolved → proceed to merge
  - Unfixable issue detected → report and stop
  - Max attempts reached → report exhaustion and stop

### 8.2 Fix Loop Logic

```
FOR attempt = 1 TO 5:
    IF no blocking issues: EXIT LOOP → go to Phase 9 (merge)

    Display: "Fix Attempt [attempt] of 5"
    Display: "[N] critical, [N] warnings remaining"

    FOR each blocking issue:
        Display: "Fixing [ID]: [title]..."

        IF issue is fixable:
            Read the affected file
            Apply the appropriate fix
            Mark as fixed
        ELSE:
            Mark as unfixable with reason

    IF has unfixable issues:
        EXIT LOOP → go to Phase 9 (failure report)

    Commit fixes:
        git add -A
        git commit -m "fix: address PR review issues (attempt [N]/5)

        Resolved:
        - [C1] Issue description
        - [W1] Issue description

        Co-Authored-By: Claude <noreply@anthropic.com>"

    Push:
        git push

    Re-analyze PR

    IF all blocking issues resolved:
        Display: "✓ All issues resolved!"
        EXIT LOOP → go to Phase 9 (merge)

IF attempt > 5 AND blocking issues remain:
    EXIT LOOP → go to Phase 9 (exhaustion report)
```

### 8.3 Fix Strategies by Issue Type

| Issue Type | Fix Approach |
|------------|--------------|
| Hardcoded secrets | Replace with `process.env.VAR_NAME` reference |
| SQL injection | Convert to parameterized query |
| XSS vulnerability | Add sanitization/escaping |
| N+1 queries | Add eager loading or batching |
| Long functions | Split into smaller focused functions |
| Missing error handling | Add try/catch with appropriate handling |
| Magic numbers | Extract to named constants |
| Missing tests | Generate basic test stubs |
| Missing docs | Generate JSDoc/docstring comments |

### 8.4 Unfixable Issue Detection

Mark an issue as "unfixable" if:
- **Requires external changes**: Database schema, external API, infrastructure
- **Architectural decision needed**: Multiple valid approaches, needs human choice
- **Cyclical issue**: Same fix keeps being undone or introduces new issues
- **Beyond scope**: Would require changes outside the PR's files
- **False positive**: Code is actually correct, analysis was wrong

When unfixable:
```
Unfixable: [ID] [title]
Reason: [why it cannot be auto-fixed]
Suggestion: [what the user should do manually]
```

---

## Phase 9: Completion

Three possible outcomes: success (merge), failure (unfixable), or exhaustion (max attempts).

### 9.1 Success Path (All Blocking Issues Resolved)

Execute merge:
```bash
# --- GitHub ---
gh pr merge $PR_NUMBER --squash --delete-branch

# --- Gitea ---
tea pr merge $PR_NUMBER --style squash
git push origin --delete $BRANCH_NAME   # tea doesn't auto-delete the branch

# --- Both platforms ---
git checkout main
git pull

# Clean up local branch if it exists
git branch -d $BRANCH_NAME 2>/dev/null || true
```

Prune stale branches:
```bash
# Fetch and prune remote tracking branches that no longer exist on remote
git remote prune origin

# Find local branches where upstream is gone and delete them (merged only)
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs -r git branch -d 2>/dev/null
```

**Note:** Only fully merged branches are deleted (`-d` not `-D`). Unmerged branches with deleted remotes are preserved and reported as warnings.

Display:
```
Phase 9: Completion
===================
✓ PR #[number] successfully merged!

Summary:
  Branch: [branch-name]
  Fix Attempts: [N]
  Issues Resolved: [N] critical, [N] warnings
  Merge Strategy: Squash

Branches Cleaned:
  ✓ origin/[branch-name] (deleted)
  ✓ local/[branch-name] (deleted)

Stale Branches Pruned:
  ✓ [stale-branch-1] (remote gone, merged)
  ✓ [stale-branch-2] (remote gone, merged)
  [If no stale branches: "None found"]
  [If unmerged branches with gone remotes exist:]
  ⚠ [unmerged-branch] (remote gone, NOT deleted - has unmerged changes)

PR URL: [url]
```

### 9.2 Failure Path (Unfixable Issues Exist)

Do NOT merge. Report to user:
```
Phase 9: Completion (Manual Review Required)
============================================
✗ PR #[number] NOT merged - unfixable issues detected.

Fix Attempts Made: [N]
Issues Resolved: [N]
Issues Remaining: [N]

Unfixable Issues:
-----------------

[C1] [Issue title]
File: [path/to/file] (lines [X-Y])
Reason: [Why it cannot be auto-fixed]
Suggestion: [Manual steps to resolve]

[W2] [Issue title]
File: [path/to/file] (lines [X-Y])
Reason: [Why it cannot be auto-fixed]
Suggestion: [Manual steps to resolve]

Next Steps:
-----------
1. Review the unfixable issues above
2. Make manual fixes in your editor
3. Push additional commits to the PR
4. Run /ship again to retry analysis and merge

PR URL: [url] (still open)
Branch: [branch-name] (preserved for manual work)
```

### 9.3 Exhaustion Path (Max Attempts Reached)

Do NOT merge. Report with diagnostics:
```
Phase 9: Completion (Fix Loop Exhausted)
========================================
✗ PR #[number] NOT merged - max fix attempts (5) reached.

Attempts Made: 5
Issues Found: [N]
Issues Resolved: [N]
Issues Still Blocking: [N]

Remaining Issues:
-----------------

[C1] [Issue title]
File: [path/to/file]
Status: [e.g., "Fixed 3 times but keeps returning"]

Diagnostic Information:
-----------------------
Attempt 1: Fixed [issues], then [what happened]
Attempt 2: Fixed [issues], then [what happened]
...

This typically indicates:
- Generated/compiled code being modified
- Conflicting linting rules
- Circular dependency between fixes

Recommendation:
---------------
1. Review the diagnostic information above
2. Manually inspect the recurring issues
3. Consider excluding generated files
4. Push manual fix and run /ship again

PR URL: [url] (still open)
Branch: [branch-name] (preserved for manual work)
```

---

## Summary of Workflow

| Phase | Action | Outcome |
|-------|--------|---------|
| Pre-flight | Verify git, gh/tea, changes | Ready to ship |
| Phase 0 | Detect platform (GitHub/Gitea) | CLI selected |
| Step 1 | Determine branch name | Branch name confirmed |
| Step 2 | Create branch | On new branch |
| Step 3 | Stage and commit | Changes committed |
| Step 4 | Push to remote | Branch pushed |
| Step 5 | Create PR | PR opened |
| Phase 7 | Auto-review PR | Issues identified |
| Phase 8 | Fix loop (up to 5x) | Issues fixed or marked unfixable |
| Phase 9 | Complete | Merged, branches pruned, or failure report |
