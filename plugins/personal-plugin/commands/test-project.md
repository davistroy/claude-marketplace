---
description: Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then create and merge PR
allowed-tools: Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(npx:*), Bash(yarn:*), Bash(pnpm:*), Bash(pytest:*), Bash(python:*), Bash(go:*), Bash(cargo:*), Bash(dotnet:*), Bash(jest:*), Bash(vitest:*), Bash(bun:*), Task
---

# Fully Test Project Command

Execute a comprehensive test-fix-ship workflow that ensures high test coverage, passes all tests, and ships the changes via a merged PR.

## Overview

This command implements an iterative test-driven workflow:
1. Verify/achieve 90%+ test coverage
2. Run ALL tests using parallel sub-agents
3. Fix any failures and repeat until all pass
4. Update documentation, clean up, create PR, and merge

## Phase 1: Pre-flight Checks

### 1.1 Environment Verification
- Verify this is a git repository
- Check that GitHub CLI (gh) is installed and authenticated
- Identify the project's test framework and coverage tool
- Identify the package manager in use (npm, yarn, pnpm, pip, cargo, go, etc.)

### 1.2 Detect Test Infrastructure

Identify the testing setup by checking for:

**JavaScript/TypeScript:**
- `jest.config.*`, `vitest.config.*`, `*.test.js`, `*.spec.ts`
- Coverage: `nyc`, `c8`, `istanbul`, built-in jest/vitest coverage

**Python:**
- `pytest.ini`, `setup.cfg [tool:pytest]`, `pyproject.toml [tool.pytest]`
- Coverage: `pytest-cov`, `coverage.py`

**Go:**
- `*_test.go` files
- Coverage: `go test -cover`

**Rust:**
- `#[test]` annotations, `tests/` directory
- Coverage: `cargo-tarpaulin`, `cargo-llvm-cov`

**Other:**
- Adapt to the detected framework

### 1.3 Current State Assessment
- Check for uncommitted changes
- Note current branch (warn if not on a feature branch)
- Identify existing test coverage baseline

## Phase 2: Coverage Verification

### 2.1 Run Coverage Analysis
Execute the appropriate coverage command for the detected framework:

```bash
# Examples by framework:
# Jest: npx jest --coverage
# Vitest: npx vitest run --coverage
# pytest: pytest --cov=. --cov-report=term-missing
# Go: go test -coverprofile=coverage.out ./...
# Cargo: cargo tarpaulin
```

### 2.2 Evaluate Coverage
- Parse coverage output to determine current percentage
- If coverage is below 90%, identify uncovered areas
- Report coverage by file/module

### 2.3 Coverage Gap Resolution (if needed)
If coverage is below 90%:

1. **Identify gaps**: List files/functions with lowest coverage
2. **Prioritize**: Focus on critical paths and business logic first
3. **Generate tests**: Write tests for uncovered code
4. **Re-run coverage**: Verify improvement
5. **Iterate**: Repeat until 90%+ achieved

Report to user before proceeding:
```
Coverage Status:
- Current: XX%
- Target: 90%
- Status: ✅ Met / ⚠️ Below target
```

## Phase 3: Parallel Test Execution

### 3.1 Spawn Test Sub-agents
Use the Task tool to run tests in parallel where possible:

**Strategy A - By test type:**
- Sub-agent 1: Unit tests
- Sub-agent 2: Integration tests
- Sub-agent 3: E2E tests (if applicable)

**Strategy B - By module/package:**
- Sub-agent per major module or package
- Useful for monorepos or large codebases

**Strategy C - Single comprehensive run:**
- For smaller projects, one sub-agent running full suite

Select strategy based on project size and test organization.

### 3.2 Sub-agent Instructions
Each test sub-agent should:
1. Run assigned tests with verbose output
2. Capture all failures with full stack traces
3. Report: total tests, passed, failed, skipped
4. Return structured results for aggregation

### 3.3 Aggregate Results
Collect results from all sub-agents:
```
Test Results Summary:
├── Unit Tests: XX passed, XX failed
├── Integration Tests: XX passed, XX failed
├── E2E Tests: XX passed, XX failed
└── Total: XX passed, XX failed, XX skipped
```

## Phase 4: Fix-Test Loop

### 4.1 Failure Analysis
For each failing test:
1. Identify the failing test file and test name
2. Capture the error message and stack trace
3. Locate the source code under test
4. Determine root cause (code bug vs test bug)

### 4.2 Fix Implementation
For each failure:
1. Analyze whether it's a code issue or test issue
2. Implement the minimal fix required
3. Document what was changed and why

### 4.3 Re-test Loop
```
WHILE tests_failing:
    1. Apply fixes for all identified failures
    2. Re-run ONLY the previously failing tests first (fast feedback)
    3. If those pass, run the FULL test suite
    4. IF new failures found:
         - Add to failure list
         - Continue loop
    5. IF all pass:
         - Exit loop
    6. IF iteration count > 10:
         - Report to user: "Fix loop exceeded 10 iterations"
         - Ask for guidance before continuing
```

### 4.4 Loop Exit Criteria
Exit the fix loop when:
- ✅ All tests pass
- ❌ Max iterations reached (ask user)
- ❌ Unfixable issue identified (report to user)

## Phase 5: Finalization

### 5.1 Update Documentation
After all tests pass:

1. **Update README if needed:**
   - New features should be documented
   - Changed behavior should be noted
   - Installation/usage changes reflected

2. **Update CHANGELOG if present:**
   - Add entry for changes made
   - Follow existing changelog format

3. **Update inline documentation:**
   - Ensure new code has appropriate comments
   - Update JSDoc/docstrings if signatures changed

### 5.2 Clean Up Temporary Files
Remove artifacts created during testing:
```bash
# Common cleanup targets:
# - coverage/ or .coverage
# - .nyc_output/
# - *.log files in project root
# - __pycache__/ (if in .gitignore)
# - node_modules/.cache/ (if applicable)
# - Any *.tmp or *.temp files
```

Only delete files that:
- Are generated artifacts (not source)
- Are in .gitignore or commonly ignored
- Were created during this session

### 5.3 Final Coverage Verification
Run coverage one final time to confirm 90%+ maintained after fixes.

## Phase 6: Create and Merge PR

### 6.1 Prepare Changes
```bash
git add -A
git status
```

Review what will be committed. Exclude any files that shouldn't be committed.

### 6.2 Create Feature Branch (if on main)
If currently on main:
```bash
git checkout -b test-fixes-YYYYMMDD-HHMMSS
```
Example: `test-fixes-20260114-143052`

### 6.3 Commit Changes
Create a comprehensive commit:
```bash
git commit -m "$(cat <<'EOF'
test: achieve 90%+ coverage and fix all test failures

- Added/updated tests to achieve XX% coverage
- Fixed N failing tests
- Updated documentation
- Cleaned up temporary files

Coverage: XX% (target: 90%)
Tests: XX passed, 0 failed

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 6.4 Push and Create PR
```bash
git push -u origin [branch-name]

gh pr create --title "test: achieve 90%+ coverage and fix all failures" --body "$(cat <<'EOF'
## Summary
- Achieved XX% test coverage (target: 90%)
- Fixed all failing tests
- Updated documentation
- Cleaned up temporary files

## Changes
- [List key changes]

## Test Results
- Total tests: XX
- Passed: XX
- Coverage: XX%

## Checklist
- [x] All tests passing
- [x] Coverage ≥ 90%
- [x] Documentation updated
- [x] Temp files cleaned

🤖 Generated with [Claude Code](https://claude.ai/claude-code)
EOF
)"
```

### 6.5 Merge PR
After PR is created:
```bash
gh pr merge --auto --squash
```

If auto-merge isn't available:
```bash
gh pr merge --squash
```

### 6.6 Clean Up
After successful merge:
```bash
git checkout main
git pull
git branch -d [feature-branch]
```

## Output Summary

Upon completion, display:
```
✅ Fully Test Project Complete

Coverage:
  Before: XX%
  After:  XX%
  Target: 90% ✅

Tests:
  Total:   XXX
  Passed:  XXX
  Fixed:   XX

Changes:
  Files modified: XX
  Tests added:    XX
  Docs updated:   XX

PR: https://github.com/owner/repo/pull/XXX
Status: Merged ✅
```

## Error Handling

### Coverage Cannot Reach 90%
If 90% coverage is unachievable:
1. Report current coverage and gap
2. List files that are difficult to test (generated code, vendor files, etc.)
3. Ask user if they want to:
   - Continue with current coverage
   - Add exclusions to coverage config
   - Abort the workflow

### Persistent Test Failures
If a test cannot be fixed after 3 attempts:
1. Report the specific test and failure
2. Provide analysis of why it's failing
3. Ask user for guidance:
   - Skip this test (mark as `.skip`)
   - Provide more context
   - Abort the workflow

### PR/Merge Failures
If PR creation or merge fails:
1. Report the specific error
2. Provide manual commands to complete the workflow
3. Ensure local changes are preserved

## Performance

**Typical Duration:**

| Project Size | Expected Time |
|--------------|---------------|
| Small (< 50 tests) | 2-5 minutes |
| Medium (50-200 tests) | 5-15 minutes |
| Large (200-500 tests) | 15-30 minutes |
| Very Large (500+ tests) | 30-60 minutes |

**Factors Affecting Performance:**
- **Test count**: More tests = longer execution
- **Fix iterations**: Each round of fixes adds 2-5 minutes
- **Coverage gap**: Writing new tests adds significant time
- **Test type**: E2E tests are slower than unit tests
- **CI complexity**: Integration with CI adds overhead

**Iteration Estimates:**
- First pass (run tests): 1-5 minutes depending on test count
- Fix cycle (per round): 2-5 minutes
- Coverage improvement: 5-15 minutes per 10% coverage increase
- Documentation updates: 2-5 minutes
- PR creation and merge: 2-5 minutes

**Signs of Abnormal Behavior:**
- Fix loop exceeding 10 iterations
- Same test failing repeatedly with different fixes
- Coverage not improving despite adding tests
- Tests timing out or hanging

**If the command seems stuck:**
1. Check for fix loop iteration count
2. Look for test timeout messages
3. Consider interrupting and running tests manually
4. Check for flaky tests that pass/fail randomly
5. Review CI logs if using CI integration

---

## Execution Notes

- **Be methodical**: Work through failures systematically, don't rush
- **Preserve stability**: Each fix should be minimal and targeted
- **Communicate progress**: Report status after each major phase
- **Respect CI**: If the project has CI, ensure it would pass
- **Ask when uncertain**: Don't guess on coverage exclusions or test skips
