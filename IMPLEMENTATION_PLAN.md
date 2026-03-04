# Implementation Plan

**Generated:** 2026-03-04 21:35:00
**Based On:** RECOMMENDATIONS.md
**Total Phases:** 4
**Estimated Total Effort:** ~600 LOC across ~35 files

---

## Executive Summary

This plan addresses all findings from the post-v5.0.0 codebase analysis. The repository is already in excellent structural shape — no blocking bugs or architectural issues remain. The work focuses on two themes: hardening the CI/CD pipeline (adding Python linting, security scanning, cross-platform testing) and completing documentation coverage (Performance and Examples sections across 25+ files).

The implementation follows a dependency-ordered approach: CI improvements first (Phase 1) since they may surface issues that affect later phases, then quick wins (Phase 2) that clean up minor inconsistencies, then documentation completeness (Phases 3-4). Each phase leaves the repository in a working, marketplace-compatible state.

Key decisions:
- Ruff is used for both linting and formatting (single tool, already cached locally)
- Performance sections use a tiered format (single-line for fast commands, table for scaling commands)
- Windows CI testing targets Python tool tests only (not the full validation suite which depends on Linux tools)

---

## Plan Overview

Phases are ordered by dependency and blast radius:
- **Phase 1** (S) hardens CI/CD — adds ruff, pip-audit, fixes markdown linting. May surface issues that later phases need to address.
- **Phase 2** (S) handles quick wins — removes .coverage files, fixes heading inconsistencies, adds pytest.ini, cleans dead code.
- **Phase 3** (M) adds Performance sections to all 25 files missing them — the largest batch of changes.
- **Phase 4** (M) adds Examples sections to 7 files and adds Windows to CI matrix.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | CI/CD Hardening | Ruff linting, pip-audit, markdown lint fix | S (~5 files, ~80 LOC) | None |
| 2 | Quick Wins & Cleanup | .coverage removal, pytest.ini, heading standardization, dead code | S (~8 files, ~30 LOC) | None |
| 3 | Performance Documentation | Performance sections for 13 commands + 12 skills | M (~25 files, ~300 LOC) | Phase 1 (ruff may flag issues) |
| 4 | Examples & Cross-Platform CI | Examples for 7 files, Windows CI matrix | M (~8 files, ~200 LOC) | Phase 1 |

<!-- BEGIN PHASES -->

---

## Phase 1: CI/CD Hardening

**Estimated Complexity:** S (~5 files, ~80 LOC)
**Dependencies:** None
**Parallelizable:** Yes — all 4 work items are independent CI config changes

### Goals

- Add Python linting and formatting enforcement to CI
- Add dependency security scanning
- Make markdown linting blocking
- Establish a shared ruff configuration

### Work Items

#### 1.1 Add Ruff Linting and Formatting to CI (COMPLETE 2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** CI1, D2
**Files Affected:**
- `ruff.toml` (create)
- `.github/workflows/validate.yml` (modify)

**Description:**
Add a `ruff.toml` configuration at the repo root targeting all Python tool source directories. Add a ruff lint + format check job to `validate.yml`. Start with a conservative rule set (`E`, `F`, `W`, `I`) and expand later. Use `ruff format --check` to enforce formatting without autofix.

**Tasks:**
1. [ ] Create `ruff.toml` at repo root with target directories (`plugins/*/tools/*/src/`, `tests/`), line-length=100, rule selection `E`, `F`, `W`, `I`
2. [ ] Add a `python-lint` job to `validate.yml` that installs ruff and runs `ruff check --output-format=github` and `ruff format --check`
3. [ ] Run ruff locally to identify and fix any existing violations
4. [ ] Verify CI passes with the new job

**Acceptance Criteria:**
- [ ] `ruff.toml` exists with documented rule selections
- [ ] `validate.yml` has a `python-lint` job that blocks on failures
- [ ] All existing Python code passes ruff check and format check
- [ ] CI workflow passes

**Notes:**
The `.ruff_cache/0.14.10` directory suggests ruff 0.14.10 has been used locally. Pin ruff version in CI to match.

---

#### 1.2 Add Dependency Security Scanning — COMPLETE 2026-03-04
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** CI2
**Files Affected:**
- `.github/workflows/test.yml` (modify)

**Description:**
Add `pip-audit` as a step in the test workflow to scan installed Python packages for known CVEs. Run after `pip install` but before tests, so vulnerabilities are detected early.

**Tasks:**
1. [ ] Add `pip install pip-audit` step to the test workflow
2. [ ] Add `pip-audit --strict` step after each tool's dependency installation
3. [ ] Verify the step passes (no known CVEs in current dependencies)
4. [ ] Add a comment explaining that pip-audit checks the NIST NVD and PyPI advisory databases

**Acceptance Criteria:**
- [ ] `pip-audit` runs in CI for all 4 Python tools
- [ ] Current dependencies have no known CVEs (or any are documented as accepted risks)
- [ ] CI workflow passes

---

#### 1.3 Make Markdown Linting Blocking (2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** CI3
**Files Affected:**
- `.github/workflows/validate.yml` (modify)

**Description:**
Remove the `|| true` suffix from the markdownlint step in `validate.yml` so that markdown lint failures actually block the build. Run markdownlint locally first to identify and fix any remaining violations.

**Tasks:**
1. [ ] Run markdownlint locally against all `.md` files to identify current violations
2. [ ] Fix any remaining violations (or add targeted exclusions to `.markdownlint.json` for intentional deviations like long table lines)
3. [ ] Remove `|| true` from the markdownlint step in `validate.yml`
4. [ ] Verify CI passes

**Acceptance Criteria:**
- [ ] Markdown linting step in CI fails on errors (no `|| true`)
- [ ] All `.md` files pass markdownlint
- [ ] Any exclusions in `.markdownlint.json` are documented with rationale

---

#### 1.4 Add ruff.toml Configuration (COMPLETE 2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** CI1
**Files Affected:**
- `ruff.toml` (create — same file as 1.1, but this item covers the detailed configuration)

**Description:**
This work item is merged into 1.1. The ruff.toml creation and CI integration are done together.

**Tasks:**
1. [ ] (Covered by 1.1)

**Acceptance Criteria:**
- [ ] (Covered by 1.1)

**Notes:**
This item exists for traceability — the actual work is in 1.1. Mark complete when 1.1 is complete.

---

### Phase 1 Testing Requirements

- [ ] `ruff check` and `ruff format --check` pass on all Python code
- [ ] `pip-audit` passes for all 4 tools
- [ ] `markdownlint` passes on all `.md` files
- [ ] Full CI workflow (test.yml + validate.yml) passes

### Phase 1 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing
- [ ] CI workflow passes end-to-end
- [ ] No regressions in existing validation steps

---

## Phase 2: Quick Wins & Cleanup

**Estimated Complexity:** S (~8 files, ~30 LOC)
**Dependencies:** None
**Parallelizable:** Yes — all 5 work items are independent

### Goals

- Remove tracked files that should be gitignored
- Add local test configuration
- Standardize minor inconsistencies
- Clean dead code

### Work Items

#### 2.1 Remove Committed .coverage Files (COMPLETE 2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** A1
**Files Affected:**
- `.coverage` (remove from tracking)
- `plugins/bpmn-plugin/tools/bpmn2drawio/.coverage` (remove from tracking)
- `plugins/personal-plugin/tools/feedback-docx-generator/.coverage` (remove from tracking)
- `plugins/personal-plugin/tools/research-orchestrator/.coverage` (remove from tracking)
- `plugins/personal-plugin/tools/visual-explainer/.coverage` (remove from tracking)

**Description:**
Remove 5 `.coverage` files (~588 KB total) from git tracking. These were committed before `.gitignore` was properly configured. The `.gitignore` already has entries to prevent re-addition.

**Tasks:**
1. [ ] Run `git rm --cached .coverage plugins/*/tools/*/.coverage` (or list each path explicitly)
2. [ ] Verify `.gitignore` has `.coverage` and `.coverage.*` entries
3. [ ] Commit the removal

**Acceptance Criteria:**
- [ ] No `.coverage` files in `git ls-files` output
- [ ] `.gitignore` prevents re-addition
- [ ] Repository size reduced by ~588 KB

---

#### 2.2 Add pytest.ini for Local Testing — COMPLETE 2026-03-04
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** D1
**Files Affected:**
- `pytest.ini` (create)

**Description:**
Create a root-level `pytest.ini` that configures test discovery for running `pytest` from the repo root. Register markers for `integration` and `slow` tests.

**Tasks:**
1. [ ] Create `pytest.ini` with `testpaths = tests`, `addopts = -v --tb=short`, and marker registrations
2. [ ] Verify `pytest` from repo root discovers and runs tests
3. [ ] Verify `pytest -m "not integration"` skips integration tests

**Acceptance Criteria:**
- [ ] `pytest` from repo root runs all tests
- [ ] Markers `integration` and `slow` are registered (no warnings)
- [ ] CI behavior unchanged (CI specifies test paths explicitly)

---

#### 2.3 Standardize Examples Section Headings (COMPLETE 2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** Q4
**Files Affected:**
- `plugins/personal-plugin/commands/convert-markdown.md` (modify)
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)
- `plugins/personal-plugin/commands/develop-image-prompt.md` (modify)

**Description:**
Rename non-standard example section headings to `## Examples` for consistency. `convert-markdown` and `plan-improvements` use `## Example Usage`, `develop-image-prompt` uses `## Complete Example`.

**Tasks:**
1. [ ] Change `## Example Usage` to `## Examples` in `convert-markdown.md`
2. [ ] Change `## Example Usage` to `## Examples` in `plan-improvements.md`
3. [ ] Change `## Complete Example` to `## Examples` in `develop-image-prompt.md`

**Acceptance Criteria:**
- [ ] All commands use `## Examples` as the section heading
- [ ] No content changes — only the heading text changes

---

#### 2.4 Clean Dead Code in bpmn2drawio converter.py — COMPLETE 2026-03-04
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** A2
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/converter.py` (modify)

**Description:**
Remove the dead `merge_theme_with_config` call at line ~54 that is immediately overwritten by the next assignment. Verify behavior is unchanged by running the bpmn2drawio test suite.

**Tasks:**
1. [ ] Read converter.py to confirm the merge result at line ~54 is unused
2. [ ] Remove the dead line
3. [ ] Run `pytest` for bpmn2drawio to verify no regressions

**Acceptance Criteria:**
- [ ] Dead code line removed
- [ ] All bpmn2drawio tests pass
- [ ] No behavior change

---

#### 2.5 Review TROUBLESHOOTING.md (COMPLETE 2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** U1
**Files Affected:**
- `TROUBLESHOOTING.md` (modify or remove)

**Description:**
Check if TROUBLESHOOTING.md has substantive content. If it's a stub with fewer than 3 entries, populate it with common issues (marketplace installation, Python dependency conflicts, API key configuration, Windows-specific issues) or remove it and reference troubleshooting in README.md instead.

**Tasks:**
1. [ ] Read TROUBLESHOOTING.md and assess content depth
2. [ ] If substantive (3+ entries), leave as-is
3. [ ] If stub, either populate with common troubleshooting entries or remove and add a troubleshooting section to README.md

**Acceptance Criteria:**
- [ ] TROUBLESHOOTING.md either has 3+ useful entries or is removed
- [ ] If removed, README.md includes basic troubleshooting guidance

---

### Phase 2 Testing Requirements

- [ ] `git ls-files` shows no `.coverage` files
- [ ] `pytest` from repo root discovers tests
- [ ] All headings in commands use `## Examples`
- [ ] bpmn2drawio tests pass after dead code removal

### Phase 2 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing
- [ ] No regressions introduced
- [ ] Markdown linting passes (Phase 1 makes this blocking)

---

## Phase 3: Performance Documentation

**Estimated Complexity:** M (~25 files, ~300 LOC)
**Dependencies:** Phase 1 (ruff may flag issues in files we're editing)
**Parallelizable:** Yes — command and skill updates are independent

### Goals

- Add Performance sections to all 13 commands missing them
- Add Performance sections to all 12 skills missing them
- Use consistent format: single-line for fast operations, table for scaling operations

### Work Items

#### 3.1 Add Performance Sections to Fast Commands (COMPLETE 2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** Q1
**Files Affected:**
- `plugins/personal-plugin/commands/bump-version.md` (modify)
- `plugins/personal-plugin/commands/new-command.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/commands/define-questions.md` (modify)
- `plugins/personal-plugin/commands/ask-questions.md` (modify)
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify)

**Description:**
Add single-line Performance sections to commands that complete quickly regardless of input size. These commands don't scale with codebase size — they operate on single files or generate boilerplate.

Format: `## Performance\n\nTypically completes in under [N] seconds.`

**Tasks:**
1. [ ] Add `## Performance` section to each of the 6 commands listed above
2. [ ] Place the section after `## Error Handling` and before `## Related Commands` (consistent with existing commands)
3. [ ] Verify section placement matches the pattern used in `review-intent.md` and `create-plan.md`

**Acceptance Criteria:**
- [ ] All 6 commands have a Performance section
- [ ] Section placement is consistent across all commands
- [ ] Markdown linting passes

---

#### 3.2 Add Performance Sections to Scaling Commands — COMPLETE 2026-03-04
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** Q1
**Files Affected:**
- `plugins/personal-plugin/commands/analyze-transcript.md` (modify)
- `plugins/personal-plugin/commands/assess-document.md` (modify)
- `plugins/personal-plugin/commands/clean-repo.md` (modify)
- `plugins/personal-plugin/commands/consolidate-documents.md` (modify)
- `plugins/personal-plugin/commands/convert-markdown.md` (modify)
- `plugins/personal-plugin/commands/remove-ip.md` (modify)
- `plugins/personal-plugin/commands/review-arch.md` (modify)

**Description:**
Add table-format Performance sections to commands whose execution time scales with input size or codebase size. Use the same format as `create-plan.md` and `plan-improvements.md`:

```markdown
## Performance

| Input Size | Expected Duration |
|------------|-------------------|
| Small (< X) | Y seconds |
| Medium (X-Y) | Z seconds |
| Large (Y+) | W+ seconds |
```

**Tasks:**
1. [ ] Add table-format Performance sections to each of the 7 commands
2. [ ] Calibrate duration estimates based on what the command does (file I/O, LLM calls, git operations)
3. [ ] For `convert-markdown`, note external dependency latency (pandoc)
4. [ ] For `review-arch`, note that duration scales with codebase size
5. [ ] Place sections consistently (after Error Handling, before Related Commands)

**Acceptance Criteria:**
- [ ] All 7 commands have table-format Performance sections
- [ ] Duration estimates are realistic for the command's workload
- [ ] Markdown linting passes

---

#### 3.3 Add Performance Sections to Skills (COMPLETE 2026-03-04)
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** Q2
**Files Affected:**
- `plugins/personal-plugin/skills/help/SKILL.md` (modify)
- `plugins/personal-plugin/skills/plan-gate/SKILL.md` (modify)
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify)
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify)
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify)

**Description:**
Add Performance sections to 6 personal-plugin skills (batch 1). For cost-bearing skills (`research-topic`), include both duration and cost. For quick skills (`help`, `plan-gate`, `unlock`), use single-line format.

**Tasks:**
1. [ ] Add single-line Performance to: help, plan-gate, unlock
2. [ ] Add table-format Performance to: ship (scales with number of changes), security-analysis (scales with codebase)
3. [ ] Add Performance with cost reference to: research-topic (reference `references/research-models.md` for cost details)
4. [ ] Place sections consistently within each skill file

**Acceptance Criteria:**
- [ ] All 6 skills have Performance sections
- [ ] Cost-bearing skills reference external cost data
- [ ] Markdown linting passes

---

#### 3.4 Add Performance Sections to Remaining Skills — COMPLETE 2026-03-04
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Recommendation Ref:** Q2
**Files Affected:**
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (modify)
- `plugins/personal-plugin/skills/validate-and-ship/SKILL.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)
- `plugins/bpmn-plugin/skills/help/SKILL.md` (modify)
- `plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md` (modify)
- `plugins/bpmn-plugin/skills/bpmn-to-drawio/SKILL.md` (modify)

**Description:**
Add Performance sections to remaining 6 skills (batch 2). `visual-explainer` is cost-bearing (Gemini image generation). BPMN skills scale with process complexity.

**Tasks:**
1. [ ] Add single-line Performance to: bpmn-plugin help
2. [ ] Add table-format Performance to: bpmn-generator, bpmn-to-drawio (scale with process complexity)
3. [ ] Add Performance with cost note to: visual-explainer (Gemini per-image cost), summarize-feedback (Python tool execution time)
4. [ ] Add table-format Performance to: validate-and-ship (depends on validation + git operations)

**Acceptance Criteria:**
- [ ] All 6 skills have Performance sections
- [ ] Markdown linting passes

---

### Phase 3 Testing Requirements

- [ ] All modified `.md` files pass markdownlint
- [ ] Performance section placement is consistent across all commands and skills
- [ ] No content outside the Performance section was changed

### Phase 3 Completion Checklist

- [ ] All work items complete
- [ ] 25 files updated with Performance sections
- [ ] All tests passing
- [ ] No regressions introduced

---

## Phase 4: Examples & Cross-Platform CI

**Estimated Complexity:** M (~8 files, ~200 LOC)
**Dependencies:** Phase 1 (CI must be healthy before adding Windows matrix)
**Parallelizable:** Yes — examples (4.1, 4.2) and CI (4.3) are independent

### Goals

- Add Examples sections to all 7 files missing them
- Add Windows to the CI test matrix
- Add type hints to feedback-docx utility functions

### Work Items

#### 4.1 Add Examples to Commands Missing Them
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: PENDING**
**Recommendation Ref:** Q3
**Files Affected:**
- `plugins/personal-plugin/commands/clean-repo.md` (modify)
- `plugins/personal-plugin/commands/consolidate-documents.md` (modify)
- `plugins/personal-plugin/commands/implement-plan.md` (modify)
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify)

**Description:**
Add `## Examples` sections showing typical invocations and expected output summaries. Follow the existing yaml code block format with User/Claude dialog. For `implement-plan`, show both fresh execution and resume scenarios.

**Tasks:**
1. [ ] Add Examples to `clean-repo.md` showing `--dry-run` and full execution
2. [ ] Add Examples to `consolidate-documents.md` showing multi-document synthesis
3. [ ] Add Examples to `implement-plan.md` showing: fresh run, resume with `--progress`, `--pause-between-phases`
4. [ ] Add Examples to `scaffold-plugin.md` showing generated directory tree
5. [ ] Use consistent yaml code block format matching existing examples

**Acceptance Criteria:**
- [ ] All 4 commands have `## Examples` sections
- [ ] `implement-plan` has at least 2 examples (fresh + resume)
- [ ] Examples follow existing format conventions
- [ ] Markdown linting passes

---

#### 4.2 Add Examples to Skills Missing Them
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: PENDING**
**Recommendation Ref:** Q3
**Files Affected:**
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify)
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (modify)
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)

**Description:**
Add Examples sections to the 3 skills missing them. Show typical trigger scenarios and expected output format.

**Tasks:**
1. [ ] Add Examples to `security-analysis` showing typical scan output summary
2. [ ] Add Examples to `summarize-feedback` showing input format and generated .docx description
3. [ ] Add Examples to `unlock` showing successful key loading and partial-key scenarios

**Acceptance Criteria:**
- [ ] All 3 skills have Examples sections
- [ ] Markdown linting passes

---

#### 4.3 Add Windows to CI Test Matrix
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: PENDING**
**Recommendation Ref:** CI4
**Files Affected:**
- `.github/workflows/test.yml` (modify)

**Description:**
Add `windows-latest` to the test matrix in `test.yml`. Target the Python tool test suites only. Skip the optional `pygraphviz` dependency on Windows (it requires system-level Graphviz which is difficult to install in CI).

**Tasks:**
1. [ ] Add `matrix.os: [ubuntu-latest, windows-latest]` to the test job
2. [ ] Add `if: runner.os != 'Windows'` condition to the pygraphviz installation step
3. [ ] Verify all 4 Python tool test suites pass on Windows
4. [ ] Fix any Windows-specific path issues (backslash vs forward slash)

**Acceptance Criteria:**
- [ ] CI runs tests on both Ubuntu and Windows
- [ ] All tests pass on both platforms (excluding pygraphviz on Windows)
- [ ] No new test failures introduced

---

#### 4.4 Add Type Hints to feedback-docx Utility Functions
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: PENDING**
**Recommendation Ref:** A3
**Files Affected:**
- `plugins/personal-plugin/tools/feedback-docx-generator/src/feedback_docx_generator/generator.py` (modify)

**Description:**
Add type annotations to all utility functions in the feedback-docx-generator (lines 49-138). Use `python-docx` types where available, `str | None` syntax for optionals. Run mypy after to catch any latent type errors.

**Tasks:**
1. [ ] Add `from __future__ import annotations` at the top of `generator.py`
2. [ ] Add type hints to all functions: `_set_run_style()`, `_add_heading()`, `_add_body()`, `_safe_get()`, etc.
3. [ ] Run mypy to verify type correctness
4. [ ] Run pytest to verify no regressions

**Acceptance Criteria:**
- [ ] All functions in generator.py have type annotations
- [ ] mypy passes without errors
- [ ] All tests pass

---

### Phase 4 Testing Requirements

- [ ] All modified `.md` files pass markdownlint
- [ ] CI passes on both Ubuntu and Windows
- [ ] feedback-docx-generator tests pass with new type hints
- [ ] mypy passes for feedback-docx-generator

### Phase 4 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing on both platforms
- [ ] Documentation updated
- [ ] No regressions introduced

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 1 (all items) | Phase 2 (all items) | CI changes and cleanup are independent |
| 3.1 | 3.2, 3.3, 3.4 | All Performance section additions are independent |
| 4.1 | 4.2, 4.3, 4.4 | Examples, CI, and type hints are independent |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Ruff flags many existing violations | Medium | Low | Fix violations in 1.1 before merging. Start with conservative rule set. |
| pip-audit finds CVEs in current deps | Low | Medium | Document accepted risks. Update deps if patches available. |
| Windows CI tests fail on path handling | Medium | Low | Use `pathlib.Path` consistently. Add `if: runner.os != 'Windows'` for known incompatibilities. |
| Markdown linting removal of `\|\| true` reveals many errors | Low | Low | Run locally first. The v5.0.0 overhaul already fixed code block specifiers. |

---

## Success Metrics

- [ ] All phases completed
- [ ] All acceptance criteria met
- [ ] CI pipeline has: Python linting, security scanning, blocking markdown lint, Windows testing
- [ ] 100% of commands have Performance and Examples sections
- [ ] 100% of skills have Performance and Examples sections
- [ ] Zero .coverage files tracked in git

---

## Appendix: Recommendation Traceability

| Recommendation | Source | Phase | Work Item |
|----------------|--------|-------|-----------|
| CI1 | RECOMMENDATIONS.md | 1 | 1.1 |
| CI2 | RECOMMENDATIONS.md | 1 | 1.2 |
| CI3 | RECOMMENDATIONS.md | 1 | 1.3 |
| D2 | RECOMMENDATIONS.md | 1 | 1.1 |
| A1 | RECOMMENDATIONS.md | 2 | 2.1 |
| D1 | RECOMMENDATIONS.md | 2 | 2.2 |
| Q4 | RECOMMENDATIONS.md | 2 | 2.3 |
| A2 | RECOMMENDATIONS.md | 2 | 2.4 |
| U1 | RECOMMENDATIONS.md | 2 | 2.5 |
| Q1 | RECOMMENDATIONS.md | 3 | 3.1, 3.2 |
| Q2 | RECOMMENDATIONS.md | 3 | 3.3, 3.4 |
| Q3 | RECOMMENDATIONS.md | 4 | 4.1, 4.2 |
| CI4 | RECOMMENDATIONS.md | 4 | 4.3 |
| A3 | RECOMMENDATIONS.md | 4 | 4.4 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-03-04 21:35:00*
*Source: /plan-improvements command*
