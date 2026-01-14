# Implementation Plan

**Generated:** 2026-01-14
**Based On:** RECOMMENDATIONS.md
**Total Phases:** 4
**Status:** ✅ **COMPLETE** (2026-01-14)

---

## Implementation Summary

All 4 phases have been successfully implemented:

| Phase | Status | Key Deliverables |
|-------|--------|------------------|
| Phase 1 | ✅ Complete | README updated, frontmatter fixed, CHANGELOG created |
| Phase 2 | ✅ Complete | Timestamps standardized, output locations documented, validation patterns added |
| Phase 3 | ✅ Complete | CONTRIBUTING.md, bump-version, validate-plugin, pre-commit hook |
| Phase 4 | ✅ Complete | review-pr, help-commands, 87% test coverage |

**New Commands Added:** 4 (bump-version, validate-plugin, review-pr, help-commands)
**Test Coverage:** 87% (target was 85%)
**Documentation:** Fully updated (README, CLAUDE.md, CHANGELOG, CONTRIBUTING.md)

---

## Plan Overview

This plan organizes 19 recommendations into 4 phases, prioritizing quick wins and critical fixes first, then building toward strategic improvements. Each phase is sized to complete within approximately 100,000 tokens including testing and fixes.

**Phasing Strategy:**
- **Phase 1:** Critical fixes and quick wins (immediate value, unblocks users)
- **Phase 2:** Standardization and consistency (foundation for future work)
- **Phase 3:** Developer experience improvements (reduce friction for contributors)
- **Phase 4:** New capabilities (extend functionality)

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Tokens | Dependencies |
|-------|------------|------------------|-------------|--------------|
| 1 | Critical Fixes | README update, frontmatter fix, CHANGELOG | ~40K | None |
| 2 | Standardization | Timestamps, output locations, common patterns | ~70K | Phase 1 |
| 3 | Developer Experience | Contributing guide, version automation, validation | ~85K | Phase 2 |
| 4 | New Capabilities | PR review command, help system, workflow basics | ~95K | Phase 3 |

---

## Phase 1: Critical Fixes and Quick Wins

**Estimated Effort:** ~40,000 tokens (including testing/fixes)
**Dependencies:** None
**Parallelizable:** Yes - all items are independent

### Goals
- Fix all critical issues blocking user discovery
- Eliminate convention violations
- Establish version history tracking
- Maximum impact with minimal effort

### Work Items

#### 1.1 Update README.md with All Commands
**Recommendation Ref:** U1
**Files Affected:** `README.md`
**Description:**
Update the personal-plugin commands table to include all 15 commands. Currently missing:
- `/consolidate` - Analyze multiple document variations and synthesize
- `/wordify` - Convert markdown to formatted Word document
- `/image-prompt` - Generate AI image prompts from content
- `/plan-improvements` - Generate improvement recommendations with implementation plan
- `/fully-test-project` - Ensure 90%+ coverage, run tests, fix, merge PR

Cross-reference each command's frontmatter description for accuracy.

**Acceptance Criteria:**
- [x] README lists all 15 commands from personal-plugin
- [x] Descriptions match frontmatter in command files
- [x] Table formatting is consistent

---

#### 1.2 Fix bpmn-generator.md Frontmatter
**Recommendation Ref:** A1
**Files Affected:** `plugins/bpmn-plugin/skills/bpmn-generator.md`
**Description:**
Remove the `name: bpmn-generator` field from line 2 of the frontmatter. CLAUDE.md explicitly prohibits this as it can prevent command discovery.

Also check `bpmn-to-drawio.md` for the same issue.

**Acceptance Criteria:**
- [x] bpmn-generator.md frontmatter has no `name` field
- [x] bpmn-to-drawio.md frontmatter has no `name` field
- [x] Both skills still discoverable after change (test with `/bpmn-generator`)

---

#### 1.3 Create CHANGELOG.md
**Recommendation Ref:** A2
**Files Affected:** `CHANGELOG.md` (new file)
**Description:**
Create CHANGELOG.md following Keep a Changelog format. Reconstruct recent history from git log:

```bash
git log --oneline --since="2026-01-01"
```

Include entries for:
- 1.6.0: plan-improvements, fully-test-project commands
- 1.5.0: image-prompt command (estimate date from git)
- Earlier versions as determinable

**Acceptance Criteria:**
- [x] CHANGELOG.md exists in repo root
- [x] Follows Keep a Changelog format (keepachangelog.com)
- [x] Includes all versions from 1.0.0 to current
- [x] Each version has date and categorized changes (Added, Changed, Fixed)

---

#### 1.4 Standardize Timestamp Format Documentation
**Recommendation Ref:** Q1 (partial)
**Files Affected:** `CLAUDE.md`
**Description:**
Document the standard timestamp format in CLAUDE.md's conventions section:

```markdown
### Timestamp Format
All generated files use `YYYYMMDD-HHMMSS` format for timestamps.
Example: `assessment-PRD-20260114-143052.md`
```

Actual command updates happen in Phase 2.

**Acceptance Criteria:**
- [x] CLAUDE.md documents timestamp convention
- [x] Format specified: `YYYYMMDD-HHMMSS`

---

### Phase 1 Testing Requirements
- Verify README renders correctly on GitHub
- Confirm BPMN skills are discoverable after frontmatter fix
- Validate CHANGELOG.md format with a linter or manual review

### Phase 1 Completion Checklist
- [x] All work items complete
- [x] README accurate and complete
- [x] No frontmatter violations
- [x] CHANGELOG established
- [x] Documentation committed

---

## Phase 2: Standardization and Consistency

**Estimated Effort:** ~70,000 tokens (including testing/fixes)
**Dependencies:** Phase 1 (timestamp documentation)
**Parallelizable:** Partially - 2.1-2.3 can run in parallel; 2.4 depends on them

### Goals
- Eliminate inconsistencies across commands
- Establish patterns that future commands follow
- Improve output organization

### Work Items

#### 2.1 Update Commands with Standard Timestamp Format
**Recommendation Ref:** Q1
**Files Affected:**
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/transcript-analysis.md`
- Any other commands using non-standard formats
**Description:**
Update all commands to use `YYYYMMDD-HHMMSS` format:

**define-questions.md** currently uses `YYYYMMDD`:
```markdown
# Before
Save to: reference/questions-[document-name]-[YYYYMMDD].json

# After
Save to: reference/questions-[document-name]-[YYYYMMDD-HHMMSS].json
```

**transcript-analysis.md** currently uses `YYYY-MM-DD`:
```markdown
# Before
Output: meeting-analysis-2026-01-10.md

# After
Output: meeting-analysis-20260110-143052.md
```

**Acceptance Criteria:**
- [x] All commands use `YYYYMMDD-HHMMSS` format
- [x] Output file naming is consistent
- [x] Examples in commands updated to match

---

#### 2.2 Document Standard Output Locations
**Recommendation Ref:** Q2
**Files Affected:** `CLAUDE.md`
**Description:**
Add output location conventions to CLAUDE.md:

```markdown
### Output Locations
- Analysis reports → `reports/` directory
- Reference data (JSON) → `reference/` directory
- Generated documents → same directory as source
- Temporary files → `.tmp/` (auto-cleaned)
```

**Acceptance Criteria:**
- [x] CLAUDE.md documents output location conventions
- [x] Categories are clear and comprehensive
- [x] Exceptions/overrides documented

---

#### 2.3 Add Argument Validation Patterns
**Recommendation Ref:** U3
**Files Affected:**
- `plugins/personal-plugin/commands/doc-assessment.md`
- `plugins/personal-plugin/commands/finish-document.md`
- `plugins/personal-plugin/commands/consolidate.md`
- Other commands accepting arguments
**Description:**
Add input validation section to commands that accept arguments:

```markdown
## Input Validation

**Required Arguments:**
- `<document-path>` - Path to document to assess

**Optional Arguments:**
- `--format [json|md]` - Output format (default: md)

**Validation:**
If required arguments missing, display:
"Usage: /doc-assessment <document-path> [--format json|md]"
```

**Acceptance Criteria:**
- [x] All argument-accepting commands have Input Validation section
- [x] Required vs optional clearly marked
- [x] Usage examples provided
- [x] Error message format standardized

---

#### 2.4 Create Common Patterns Reference
**Recommendation Ref:** A4 (partial)
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md` (new)
**Description:**
Extract repeated patterns into a shared reference document:

```markdown
# Common Command Patterns

## Timestamp Format
YYYYMMDD-HHMMSS (e.g., 20260114-143052)

## Output File Naming
[type]-[source]-[timestamp].[ext]
Examples:
- assessment-PRD-20260114-143052.md
- questions-requirements-20260114-150000.json

## Progress Reporting
Phase X of Y: [Phase Name]
- Step 1: [Description] ✓
- Step 2: [Description] (in progress)
- Step 3: [Description] (pending)

## Session Commands (for interactive commands)
- `help` - Show available commands
- `back` - Return to previous step
- `skip` - Skip current item
- `status` - Show progress
- `quit` - Exit session (with save prompt)
```

**Acceptance Criteria:**
- [x] `references/` directory exists in personal-plugin
- [x] common-patterns.md covers: timestamps, naming, progress, session commands
- [x] Patterns match actual usage in commands

---

### Phase 2 Testing Requirements
- Generate output from updated commands, verify naming
- Confirm argument validation produces helpful errors
- Check references are accurate

### Phase 2 Completion Checklist
- [x] All work items complete
- [x] Timestamps consistent across commands
- [x] Output conventions documented
- [x] Argument validation added
- [x] Common patterns extracted

---

## Phase 3: Developer Experience

**Estimated Effort:** ~85,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (patterns established)
**Parallelizable:** Yes - 3.1, 3.2, 3.3 can run in parallel; 3.4 can start once 3.1 done

### Goals
- Make it easy to contribute new commands
- Automate repetitive version management
- Catch errors before commit

### Work Items

#### 3.1 Create CONTRIBUTING.md
**Recommendation Ref:** D1
**Files Affected:** `CONTRIBUTING.md` (new)
**Description:**
Create contributor guidelines covering:

1. **Adding a New Command**
   - File location: `plugins/[plugin]/commands/[name].md`
   - Frontmatter requirements (description, optional allowed-tools)
   - No `name` field in frontmatter
   - Pattern selection (read-only, interactive, workflow, etc.)

2. **Adding a New Skill**
   - When to use skill vs command
   - File location and structure

3. **Version Management**
   - When to bump versions
   - Files to update (until automation exists)
   - CHANGELOG update process

4. **Pull Request Process**
   - Branch naming
   - Commit message format
   - Review expectations

Include a command template snippet.

**Acceptance Criteria:**
- [x] CONTRIBUTING.md exists in repo root
- [x] Covers command and skill creation
- [x] Includes template/example
- [x] References CLAUDE.md for detailed conventions
- [x] Version management documented

---

#### 3.2 Create Version Bump Command
**Recommendation Ref:** A3
**Files Affected:**
- `plugins/personal-plugin/commands/bump-version.md` (new)
**Description:**
Create `/bump-version` command that automates version updates:

```markdown
## Usage
/bump-version [plugin] [major|minor|patch]

## Behavior
1. Read current version from plugin.json
2. Calculate new version based on bump type
3. Update:
   - plugins/[plugin]/.claude-plugin/plugin.json
   - .claude-plugin/marketplace.json (plugin entry)
4. Add CHANGELOG entry placeholder
5. Report changes and prompt for commit
```

**Acceptance Criteria:**
- [x] Command handles major, minor, patch bumps
- [x] Updates all required version locations
- [x] Creates CHANGELOG placeholder
- [x] Shows diff before committing
- [x] Handles both personal-plugin and bpmn-plugin

---

#### 3.3 Create Plugin Validation Command
**Recommendation Ref:** A5, D3
**Files Affected:**
- `plugins/personal-plugin/commands/validate-plugin.md` (new)
**Description:**
Create `/validate-plugin` command that checks:

1. **Frontmatter Validation**
   - Valid YAML syntax
   - `description` field present
   - No `name` field (forbidden)
   - `allowed-tools` valid if present

2. **Structure Validation**
   - plugin.json exists and valid
   - Version numbers in sync
   - All referenced files exist

3. **Content Validation**
   - Markdown parses correctly
   - Code blocks have language specifiers
   - No broken internal links

**Acceptance Criteria:**
- [x] Command validates frontmatter
- [x] Checks version synchronization
- [x] Reports errors with file:line references
- [x] Exits with error code on failures (for CI use)

---

#### 3.4 Add Pre-commit Hook Setup Instructions
**Recommendation Ref:** D3
**Files Affected:** `CONTRIBUTING.md`
**Description:**
Add instructions to CONTRIBUTING.md for setting up pre-commit validation:

```bash
# Install pre-commit hook
cp scripts/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

Create `scripts/pre-commit` that runs `/validate-plugin`.

**Acceptance Criteria:**
- [x] `scripts/pre-commit` exists
- [x] Hook runs validation on staged .md files
- [x] Instructions in CONTRIBUTING.md
- [x] Hook is not auto-installed (opt-in)

---

### Phase 3 Testing Requirements
- Create test command, verify validation catches errors
- Test version bump with dry-run
- Verify pre-commit hook blocks invalid commits

### Phase 3 Completion Checklist
- [x] All work items complete
- [x] CONTRIBUTING.md comprehensive
- [x] Version bump automation working
- [x] Validation command operational
- [x] Pre-commit hook documented

---

## Phase 4: New Capabilities

**Estimated Effort:** ~95,000 tokens (including testing/fixes)
**Dependencies:** Phase 3 (validation ensures quality)
**Parallelizable:** Yes - 4.1 and 4.2 can run in parallel; 4.3 after both

### Goals
- Add highly-requested PR review capability
- Improve discoverability with help system
- Improve test coverage for Python tool

### Work Items

#### 4.1 Create PR Review Command
**Recommendation Ref:** N1
**Files Affected:**
- `plugins/personal-plugin/commands/review-pr.md` (new)
**Description:**
Create `/review-pr` command that provides structured PR review:

```markdown
## Usage
/review-pr [PR-number-or-url]

## Workflow
1. Fetch PR details: `gh pr view [number]`
2. Get diff: `gh pr diff [number]`
3. Analyze changes:
   - Security concerns
   - Performance implications
   - Code style/conventions
   - Test coverage
   - Documentation updates needed
4. Generate review with:
   - Summary of changes
   - Issues found (by severity)
   - Suggested improvements
   - Approval recommendation
5. Optionally post review: `gh pr review`
```

**Acceptance Criteria:**
- [x] Command fetches and analyzes PR
- [x] Checks against project conventions (from CLAUDE.md)
- [x] Categorizes findings by severity
- [x] Offers to post review via `gh pr review`
- [x] Works with PR number or URL

---

#### 4.2 Create Help Commands Skill
**Recommendation Ref:** U4
**Files Affected:**
- `plugins/personal-plugin/skills/help-commands.md` (new)
**Description:**
Create `/help-commands` skill for command discovery:

```markdown
## Behavior
1. Scan plugins/*/commands/*.md and plugins/*/skills/*.md
2. Extract descriptions from frontmatter
3. Group by category (from CLAUDE.md patterns)
4. Display formatted list:

Available Commands:

**Analysis (read-only)**
- /arch-review - Deep architectural review
- /doc-assessment - Document quality evaluation

**Interactive Workflows**
- /ask-questions - Q&A session from JSON
- /finish-document - Complete incomplete docs

**Generation**
- /define-questions - Extract questions to JSON
...

Use /help-commands [name] for details on a specific command.
```

**Acceptance Criteria:**
- [x] Lists all commands and skills
- [x] Groups by category
- [x] Shows descriptions
- [x] Supports detail view for specific command

---

#### 4.3 Improve bpmn2drawio Test Coverage
**Recommendation Ref:** D4
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/*.py`
- `plugins/bpmn-plugin/tools/bpmn2drawio/pyproject.toml`
**Description:**
Improve test coverage for the Python conversion tool:

1. Add coverage reporting to pyproject.toml:
```toml
[tool.pytest.ini_options]
addopts = "--cov=bpmn2drawio --cov-report=term-missing --cov-report=html"
```

2. Run coverage and identify gaps:
```bash
cd plugins/bpmn-plugin/tools/bpmn2drawio
pytest --cov=bpmn2drawio
```

3. Add tests for uncovered code paths, focusing on:
   - position_resolver.py (most complex)
   - Edge cases in layout.py
   - Error recovery scenarios

4. Update README with coverage badge

**Acceptance Criteria:**
- [x] Coverage reporting configured
- [x] Coverage report generated
- [x] Coverage improved to 85%+ (achieved 87%)
- [x] Critical paths fully covered
- [x] Badge added to tool README

---

### Phase 4 Testing Requirements
- Test PR review on actual PRs
- Verify help-commands discovers all commands
- Coverage report validates improvement

### Phase 4 Completion Checklist
- [x] All work items complete
- [x] PR review command functional
- [x] Help system complete
- [x] Test coverage improved (87%)
- [x] All new commands validated with /validate-plugin

---

## Parallel Work Opportunities

| Work Item A | Can Run With | Notes |
|-------------|--------------|-------|
| 1.1 README | 1.2 Frontmatter | Independent files |
| 1.1 README | 1.3 CHANGELOG | Independent files |
| 1.2 Frontmatter | 1.3 CHANGELOG | Independent files |
| 2.1 Timestamps | 2.2 Output locations | Both update different files |
| 2.1 Timestamps | 2.3 Argument validation | Different commands |
| 3.1 CONTRIBUTING | 3.2 Version bump | Independent |
| 3.1 CONTRIBUTING | 3.3 Validation | Independent |
| 4.1 PR Review | 4.2 Help Commands | Independent commands |

**Maximum Parallelism:**
- Phase 1: 3 parallel streams (1.1+1.2+1.3, then 1.4)
- Phase 2: 3 parallel streams (2.1+2.2+2.3, then 2.4)
- Phase 3: 3 parallel streams (3.1+3.2+3.3, then 3.4)
- Phase 4: 2 parallel streams (4.1+4.2, then 4.3)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Frontmatter change breaks discovery | Low | High | Test immediately after change |
| Version bump automation has edge cases | Medium | Medium | Manual review of first few bumps |
| PR review scope creep | Medium | Low | Define clear boundaries upfront |
| Test coverage improvement reveals bugs | Medium | Medium | Fix bugs as found; track in issues |
| Commands reference non-existent patterns | Low | Medium | Validate references in Phase 2.4 |

---

## Success Metrics

| Metric | Baseline | Target | Measured By |
|--------|----------|--------|-------------|
| Commands documented in README | 10/15 | 15/15 | Manual count |
| Frontmatter violations | 1+ | 0 | /validate-plugin |
| Timestamp format consistency | Mixed | 100% | Grep for timestamp patterns |
| Version sync errors | Occasional | 0 | /validate-plugin |
| bpmn2drawio test coverage | Unknown | 85%+ | pytest --cov |

---

## Post-Implementation

After all phases complete:
1. Run `/validate-plugin` on entire repo
2. Update all version numbers (use /bump-version)
3. Create release notes from CHANGELOG
4. Consider Phase 5: Workflow composition (N3) if demand exists

---

*Implementation plan generated by Claude on 2026-01-14*
