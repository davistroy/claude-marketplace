---
description: Determine original project intent and compare against current implementation, reporting discrepancies
allowed-tools: Read, Glob, Grep, Write
---

# Review Intent

Perform a systematic analysis of what this project was originally intended to do versus what it currently does. This command reconstructs the original vision from project artifacts (README, docs, early commits, architecture decisions, specs) and compares it against the actual implementation to surface scope drift, abandoned features, unfinished work, and misaligned implementations. This is a read-only analysis — no files are modified.

## Input Validation

**Optional Arguments:**
- `<path>` - Specific file, directory, or subproject to analyze (default: repository root)
- `--deep` - Include git history analysis for intent reconstruction (slower but more thorough)
- `--save` - Save the report to a file instead of only displaying in conversation

**Argument Detection:**
Check if the user provided a file path or directory as an argument ($ARGUMENTS). If provided, scope the review to that path only. If not provided, review the entire project from the repository root.

```text
# Examples of argument detection:
/review-intent                     → Review entire project
/review-intent src/api             → Review only src/api directory
/review-intent --deep              → Review entire project with git history
/review-intent src/api --deep      → Review src/api with git history
/review-intent --save              → Review entire project, save report to file
/review-intent src/api --save      → Review src/api, save report to file
```

**Validation:**
Before proceeding, verify:
- This is a code project with sufficient history to infer intent (not an empty repo or single-file script)
- If a specific path was provided, verify it exists and is not empty
- Project has at least one of: README, docs directory, CLAUDE.md, specification files, meaningful commit messages, or architecture decision records
- If no intent artifacts exist, report this early rather than guessing

If the project lacks intent signals:
```text
Unable to determine project intent.

No intent artifacts found. This command requires at least one of:
  - README.md or similar documentation
  - Specification or requirements documents (PRD, BRD, TDD)
  - Architecture decision records (ADRs)
  - CLAUDE.md or similar project instructions
  - Meaningful commit history (not just "initial commit")
  - Issue tracker references or project boards

Suggestion: Create a README describing the project's purpose, then re-run.
```

## Instructions

Execute the following systematic analysis. **DO NOT MAKE ANY CHANGES — ONLY ANALYZE AND REPORT.**

### Phase 1: Intent Reconstruction

Reconstruct the project's original intent by examining artifacts in priority order:

#### 1.1 Primary Intent Sources (examine all that exist)

| Source | What to Extract | Priority |
|--------|----------------|----------|
| README.md / README | Stated purpose, features list, usage examples | Highest |
| CLAUDE.md | Project instructions, architectural decisions, conventions | High |
| Specification docs (PRD, BRD, TDD, design docs) | Requirements, acceptance criteria, feature scope | High |
| Architecture Decision Records (ADRs) | Design rationale, chosen patterns, rejected alternatives | High |
| package.json / pyproject.toml / Cargo.toml | Project name, description, keywords, declared dependencies | Medium |
| CHANGELOG.md | Feature evolution, version milestones, planned work | Medium |
| Issue tracker / TODO files | Planned features, known gaps, deferred work | Medium |
| CI/CD configuration | Intended deployment targets, quality gates | Medium |

#### 1.2 Secondary Intent Sources (if `--deep` specified or primary sources are sparse)

| Source | What to Extract |
|--------|----------------|
| First 5-10 commits | Initial architecture decisions, foundational choices |
| Commit message patterns | Feature themes, refactoring waves, pivot points |
| Branch names (current and merged) | Feature work attempted, work in progress |
| Pull request history (if available) | Feature discussions, design decisions |
| Comments and docstrings | Stated intent at function/module level |

#### 1.3 Synthesize Intent Statement

From all gathered evidence, produce a structured intent profile:

```text
Project Intent Profile
━━━━━━━━━━━━━━━━━━━━━━
Purpose:       [One sentence — what this project exists to do]
Target Users:  [Who this is for]
Core Features: [Numbered list of intended capabilities]
Architecture:  [Intended patterns and structure]
Quality Goals: [Testing, performance, security expectations]
Scope Boundaries: [What was explicitly out of scope, if stated]
```

Assign a confidence level to each element:
- **High** — Explicitly stated in documentation
- **Medium** — Strongly implied by multiple artifacts
- **Low** — Inferred from code structure or naming only

### Phase 2: Current Implementation Analysis

Map what the codebase actually does today.

#### 2.1 Capability Inventory

For each intended feature from the intent profile:
1. Locate the implementing code (files, modules, functions)
2. Assess implementation completeness (fully implemented, partial, stub, absent)
3. Note any deviations from the stated approach
4. Identify test coverage for the feature

#### 2.2 Unplanned Capabilities

Identify code that implements functionality NOT described in any intent artifact:
- Features that exist in code but aren't documented
- Modules with no clear mapping to stated requirements
- Dependencies pulled in but not referenced by intended features
- Configuration for services or integrations not mentioned in docs

#### 2.3 Architectural Reality

Compare the actual architecture against the intended architecture:
- Directory structure vs stated organization
- Design patterns in use vs patterns described in docs
- Dependency graph vs intended module boundaries
- Data flow vs documented data model

### Phase 3: Gap Analysis

Systematically compare intent vs reality across every dimension.

#### 3.1 Discrepancy Categories

Classify every finding into one of these categories:

| Category | Description | Severity |
|----------|-------------|----------|
| **Missing Feature** | Documented in intent but not implemented | Varies by importance |
| **Partial Implementation** | Started but incomplete — stubs, TODOs, half-built modules | WARNING |
| **Scope Drift** | Implemented features that weren't in original intent | SUGGESTION |
| **Misaligned Implementation** | Feature exists but works differently than specified | WARNING or CRITICAL |
| **Abandoned Work** | Evidence of started-then-stopped work (dead code, unused imports) | SUGGESTION |
| **Documentation Drift** | Docs describe something different from what code does | WARNING |
| **Architecture Divergence** | Code structure doesn't match stated architectural intent | WARNING |
| **Dependency Mismatch** | Declared deps unused, or undeclared deps in use | SUGGESTION |

#### 3.2 Per-Feature Assessment

For each intended feature, produce:

```text
Feature: [Feature Name]
Intent Source: [Where this was specified — README line, spec section, etc.]
Status: [Fully Implemented | Partially Implemented | Stub Only | Missing | Divergent]
Implementation: [File paths and modules that implement this]
Coverage: [Test coverage status]
Discrepancies:
  - [Specific difference between intent and reality]
  - [Another difference, if any]
Severity: [CRITICAL | WARNING | SUGGESTION]
```

#### 3.3 Quantitative Summary

Produce metrics with explicit calculations:

- **Intent Coverage**: (fully implemented features / total intended features) * 100. Report as both fraction and percentage (e.g., "7/10 = 70%").
- **Scope Drift Score**: (unplanned features / total intended features) * 100. A score above 50% indicates significant drift. Report as fraction and percentage.
- **Documentation Accuracy**: (documented features that match implementation / total documented features) * 100. Report as fraction and percentage.
- **Test Coverage Density**: (source files with corresponding test files / total source files) * 100. A "sparse" area is one where fewer than 20% of source files have corresponding test files, or where documentation covers fewer than 50% of public APIs.
- **Completion Trajectory**: Based on commit history (if `--deep`), is the project converging toward or diverging from its intent? Express as: Converging, Stable, or Diverging.
- **Files Examined**: Total number of files analyzed during the review.
- **Discrepancies Found**: Total count of all discrepancies across all categories.
- **Severity Breakdown**: Count of CRITICAL, WARNING, and SUGGESTION issues.

**Metrics Summary Table:**
```text
Review Metrics
==============
Files Examined:        [N]
Intent Sources Found:  [N]
Features Intended:     [N]
Features Implemented:  [N] ([X]%)
Unplanned Features:    [N]
Discrepancies Found:   [N]
  CRITICAL:            [N]
  WARNING:             [N]
  SUGGESTION:          [N]
Scope Drift Score:     [X]%
Documentation Accuracy:[X]%
Test Coverage Density: [X]%
```

### Phase 4: Report Generation

Produce the final discrepancy report as an in-conversation analysis.

#### 4.1 Report Structure

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Intent Review: [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Analyzed:** [timestamp]
**Scope:** [what was analyzed]
**Intent Sources:** [list of artifacts examined]

## Executive Summary

[2-3 sentence overview: Is the project aligned with its intent? What's the
biggest gap? What's the overall trajectory?]

## Intent Profile

Purpose: [reconstructed purpose]
Core Features (intended): [count]
Features Implemented: [count] ([percentage]%)
Unplanned Features: [count]
Documentation Accuracy: [percentage]%

## Scorecard

| Dimension | Score | Status |
|-----------|-------|--------|
| Feature Completeness | X/10 | [On Track / Behind / Stalled] |
| Architecture Alignment | X/10 | [Aligned / Drifting / Diverged] |
| Documentation Accuracy | X/10 | [Current / Stale / Misleading] |
| Scope Discipline | X/10 | [Focused / Expanding / Scattered] |
| Overall Intent Alignment | X/10 | [summary] |

## Discrepancy Summary

| Category | Count | Severity |
|----------|-------|----------|
| Missing Features | X | [highest severity] |
| Partial Implementations | X | WARNING |
| Scope Drift | X | SUGGESTION |
| Misaligned Implementations | X | [varies] |
| Abandoned Work | X | SUGGESTION |
| Documentation Drift | X | WARNING |
| Architecture Divergence | X | WARNING |
| **Total Discrepancies** | **X** | |

## Detailed Findings

### CRITICAL Issues
#### C1. [Issue Title]
**Category:** [discrepancy type]
**Intent:** [what was supposed to happen]
**Reality:** [what actually exists]
**Evidence:** [file paths, doc references]
**Impact:** [why this matters]
**Recommendation:** [what to do about it]

### WARNING Issues
#### W1. [Issue Title]
...

### SUGGESTIONS
#### S1. [Issue Title]
...

## Recommendations

### Realignment Actions (if project should match original intent)
1. [Highest priority action to close the biggest gap]
2. [Next priority]
3. [...]

### Documentation Updates (if implementation is correct but docs are stale)
1. [Doc that needs updating and what to change]
2. [...]

### Scope Decisions Needed (features that need explicit keep/kill decisions)
1. [Unplanned feature that should be explicitly adopted or removed]
2. [...]

### Intent Clarification Needed (ambiguous areas)
1. [Area where intent is unclear and implementation chose one path]
2. [...]
```

## Output Format

This is a read-only analysis command. By default, the report is produced inline in conversation.

**If `--save` flag is provided:**
Save the report to a file using the Write tool:
- **Location:** `reports/` directory (create if it does not exist)
- **Filename:** `intent-review-YYYYMMDD-HHMMSS.md`
- **Example:** `reports/intent-review-20260228-143052.md`

After saving, display:
```text
Report saved to: reports/intent-review-[timestamp].md
```

**If `--save` flag is NOT provided:**
After displaying the report, offer to save:
```text
Would you like me to save this review to reports/intent-review-[timestamp].md? (yes/no)
```
If the user accepts, save using the Write tool.

## Examples

```text
User: /review-intent

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Intent Review: claude-marketplace
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Analyzed:** 2026-02-16
**Scope:** Full repository
**Intent Sources:** README.md, CLAUDE.md, marketplace.json, plugin.json (x2)

## Executive Summary

The project is well-aligned with its stated intent as a Claude Code plugin
marketplace. Core functionality (plugin discovery, installation, validation)
is fully implemented. Minor scope drift exists in the form of utility commands
that extend beyond the marketplace's stated purpose. Documentation is current.

## Scorecard

| Dimension | Score | Status |
|-----------|-------|--------|
| Feature Completeness | 9/10 | On Track |
| Architecture Alignment | 9/10 | Aligned |
| Documentation Accuracy | 8/10 | Current |
| Scope Discipline | 7/10 | Expanding |
| Overall Intent Alignment | 8/10 | Strong alignment with healthy growth |

## Discrepancy Summary

| Category | Count | Severity |
|----------|-------|----------|
| Missing Features | 0 | — |
| Partial Implementations | 1 | WARNING |
| Scope Drift | 3 | SUGGESTION |
| Documentation Drift | 2 | WARNING |
| **Total** | **6** | |

...
```

```text
User: /review-intent --deep

Claude:
[Includes git history analysis for richer intent reconstruction]
...

User: /review-intent src/api

Claude:
[Scoped analysis of just the src/api directory]
...
```

## Performance

**Typical Duration:**

| Codebase Size | Expected Time |
|---------------|---------------|
| Small (< 50 files) | 30-60 seconds |
| Medium (50-200 files) | 1-3 minutes |
| Large (200-500 files) | 3-7 minutes |
| Very Large (500+ files) | 7-15 minutes |

With `--deep` flag (git history analysis), add 30-60 seconds for every 100 commits.

**Factors Affecting Performance:**
- **Documentation volume**: More docs means richer intent reconstruction but longer Phase 1
- **File count**: Primary driver of Phase 2 analysis time
- **Git history depth** (`--deep` only): Commit count directly affects history analysis
- **Feature count**: More stated features means more comparisons in Phase 3

**If the command seems stuck:**
1. Check for phase progress indicators
2. Wait at least 5 minutes for medium/large codebases
3. If no activity, interrupt and retry with a specific subdirectory
4. For very large projects, run on specific modules first

## Execution Instructions

- **DO NOT MAKE ANY CHANGES** — ONLY ANALYZE AND REPORT
- Always show your work: cite specific files, line numbers, doc sections, and commit hashes
- When intent is ambiguous, present both interpretations and let the user decide
- Distinguish between "the project failed to implement X" and "the project chose a different approach to X"
- Consider that intent may have legitimately evolved — not all drift is bad
- Flag areas where you need clarification before judging alignment

Begin by examining all available intent artifacts and presenting the Intent Profile before proceeding to implementation analysis.

## Error Handling

| Condition | Cause | Action |
|-----------|-------|--------|
| No intent artifacts found | Repository lacks README, docs, specs, CLAUDE.md, or meaningful commit history | Display the "Unable to determine project intent" message from Input Validation and suggest creating a README |
| Specified path does not exist | User provided a `<path>` argument that is invalid or empty | Report: "Path '[path]' not found or is empty. Verify the path and try again." List available top-level directories as suggestions. |
| Insufficient commit history | Repo has only an initial commit or very few commits when `--deep` is specified | Warn: "Git history is too shallow for meaningful intent reconstruction. Proceeding with documentation-only analysis." Skip Phase 1.2 secondary sources. |
| Git not available | Running in an environment without git (relevant for `--deep` mode) | Skip git history analysis and report: "Git is not available — skipping commit history analysis. Results based on documentation and code structure only." |
| Report save failure (`--save`) | Cannot write to `reports/` directory due to permissions or disk issues | Display the report inline in conversation and report: "Could not save to reports/. Report displayed above — copy it manually if needed." |
| Context window exhaustion | Very large codebase exceeds analysis capacity | Prioritize Phase 1 (intent reconstruction) and Phase 3 (gap analysis) over exhaustive Phase 2 (implementation analysis). Report which modules were sampled. |
| Ambiguous intent signals | Documentation contradicts itself or multiple conflicting intent sources exist | Present both interpretations clearly, flag the conflict, and let the user decide which intent is authoritative |

## Related Commands

- `/review-arch` — Quick architectural audit (complementary review)
- `/review-pr` — Review a specific pull request for code quality
- `/plan-improvements` — Generate improvement recommendations based on codebase analysis
- `/plan-next` — Get a recommendation for the next action based on current state
- `/assess-document` — Evaluate document quality (useful for reviewing spec documents)
