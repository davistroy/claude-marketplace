---
command: test-project
type: command
fixtures: []
---

# Eval: /test-project

## Purpose

Ensures 90%+ test coverage, runs all tests with sub-agents, fixes failures, then creates a PR. This is a comprehensive test-and-ship workflow. Evals should run against a project that has tests, not the marketplace repo itself.

## Fixtures

None — requires a code project with tests. Use a separate Node.js or Python project for eval.

## Setup

```bash
# Create a minimal test project with some failing tests
mkdir /tmp/eval-test-project && cd /tmp/eval-test-project
git init && git checkout -b main
npm init -y
npm install --save-dev jest
# Create a simple module with tests (some passing, some failing)
```

## Test Scenarios

### S1: Project with passing tests

**Setup:** Project with a test suite where all tests pass.

**Invocation:** `/test-project`

**Must:**
- [ ] Discovers and runs existing tests
- [ ] Reports test results (pass count, fail count, coverage percentage)
- [ ] If coverage < 90%, adds tests to close the gap
- [ ] Creates a PR after tests pass

**Should:**
- [ ] Uses sub-agents to run tests in parallel when possible
- [ ] Provides a summary of what was tested

**Must NOT:**
- [ ] Delete existing tests to "fix" coverage
- [ ] Skip tests to get a passing suite
- [ ] Push to main branch

---

### S2: Project with failing tests

**Setup:** Project with one deliberately failing test.

**Invocation:** `/test-project`

**Must:**
- [ ] Identifies the failing test(s)
- [ ] Attempts to fix the failing tests
- [ ] Re-runs tests after fix to verify resolution
- [ ] Does not create a PR until tests pass

**Should:**
- [ ] Reports what the test failure was and how it was fixed

**Must NOT:**
- [ ] Delete failing tests as a "fix"
- [ ] Create a PR with failing tests

---

### S3: --auto-merge flag

**Invocation:** `/test-project --auto-merge` (in isolated test project)

**Must:**
- [ ] Creates PR and merges it after all tests pass

---

### S4: Prerequisite — not on main

**Setup:** Be on main branch.

**Invocation:** `/test-project`

**Must:**
- [ ] Detects main branch and either creates a feature branch or errors

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Tests discovered and run | Required |
| Failing tests fixed before PR creation | Required |
| Coverage gap addressed | Should (≥ 90% target) |
| PR created on feature branch, not main | Required |
| No tests deleted to improve pass rate | Required |
