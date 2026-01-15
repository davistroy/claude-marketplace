# Implementation Plan

**Generated:** 2026-01-15T09:45:00
**Based On:** RECOMMENDATIONS.md (v2.3.0 analysis)
**Total Phases:** 4

---

## Plan Overview

This plan organizes 20 recommendations into 4 phases, building from quick wins and enforcement improvements to strategic infrastructure changes. Each phase delivers standalone value while laying foundation for subsequent phases.

**Phasing Strategy:**
- **Phase 1:** Quick Wins & Enforcement - Immediate improvements, blocking validation
- **Phase 2:** Architecture & Patterns - Modularization, validation framework
- **Phase 3:** Developer Experience - Templates, onboarding, testing expansion
- **Phase 4:** Advanced Capabilities - CI/CD, maturity scorecard, analytics

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Tokens | Dependencies |
|-------|------------|------------------|-------------|--------------|
| 1 | Quick Wins & Enforcement | README tables, help sync blocking, directory auto-creation | ~35K | None |
| 2 | Architecture & Patterns | common-patterns modularization, validation framework | ~80K | Phase 1 |
| 3 | Developer Experience | New templates, onboarding guide, core command tests | ~70K | Phase 2 |
| 4 | Advanced Capabilities | CI/CD pipeline, maturity scorecard | ~55K | Phase 3 |

---

## Phase 1: Quick Wins & Enforcement

**Estimated Effort:** ~35,000 tokens (including testing/fixes)
**Dependencies:** None
**Parallelizable:** Yes - all items are independent

### Goals
- Complete README documentation gaps
- Make help.md synchronization blocking
- Ensure output directories auto-create
- Fix BPMN plugin help descriptions

### Work Items

#### 1.1 Complete README Command Tables
**Recommendation Ref:** U2
**Files Affected:**
- `scripts/update-readme.py`
- `README.md`

**Description:**
Update README to show complete command descriptions without truncation.

1. Review current `update-readme.py` for truncation logic
2. Modify to show first complete sentence (natural truncation at period)
3. Add hyperlinks to individual command files
4. Regenerate README.md

**Acceptance Criteria:**
- [x] Command descriptions no longer show ellipsis
- [x] Each command links to its source file
- [x] Table formatting remains readable

---

#### 1.2 Make Help.md Synchronization Blocking
**Recommendation Ref:** U1
**Files Affected:**
- `scripts/pre-commit`
- `plugins/personal-plugin/commands/validate-plugin.md`

**Description:**
Ensure help.md files cannot drift from actual commands.

1. Update `scripts/pre-commit` to run help.md validation
2. Add clear error message when out of sync
3. Document the blocking behavior in CONTRIBUTING.md

**Acceptance Criteria:**
- [x] Pre-commit hook runs help.md validation
- [x] Commits touching command files require synced help.md
- [x] Error message shows how to fix (`/validate-plugin --fix`)

---

#### 1.3 Implement Output Directory Auto-Creation
**Recommendation Ref:** Q1
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md`
- `plugins/personal-plugin/commands/assess-document.md`
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/analyze-transcript.md`

**Description:**
Ensure commands auto-create output directories before writing.

1. Add directory auto-creation pattern to common-patterns.md
2. Update 3 most-used generator commands with explicit mkdir step
3. Test with fresh repo (no reports/ directory)

**Acceptance Criteria:**
- [x] Pattern documented in common-patterns.md
- [x] Commands create reports/ and reference/ as needed
- [x] No user confirmation required for standard directories

---

#### 1.4 Improve BPMN Plugin Help Descriptions
**Recommendation Ref:** U6
**Files Affected:**
- `plugins/bpmn-plugin/skills/help.md`

**Description:**
Expand BPMN skill descriptions with operating modes and examples.

1. Add full descriptions for bpmn-generator and bpmn-to-drawio
2. Include operating modes (Interactive vs Document Parsing)
3. Add example invocations

**Acceptance Criteria:**
- [x] Each skill has complete description (2-3 lines)
- [x] Operating modes documented
- [x] Example command shown for each skill

---

#### 1.5 Separate Marketplace Versioning
**Recommendation Ref:** A5
**Files Affected:**
- `.claude-plugin/marketplace.json`
- `CLAUDE.md`

**Description:**
Decouple marketplace version from individual plugin versions.

1. Change marketplace.json version strategy
2. Add `last_updated` timestamp to plugin entries
3. Document versioning strategy in CLAUDE.md

**Acceptance Criteria:**
- [x] Marketplace version independent of plugin versions
- [x] Each plugin entry has last_updated timestamp
- [x] Versioning strategy documented

---

### Phase 1 Testing Requirements
- Run pre-commit hook with help.md out of sync
- Run generator command in repo without reports/ directory
- Verify README renders correctly with updated tables

### Phase 1 Completion Checklist
- [x] All work items complete
- [x] Pre-commit hook tested
- [x] README regenerated
- [x] CHANGELOG updated

---

## Phase 2: Architecture & Patterns

**Estimated Effort:** ~80,000 tokens (including testing/fixes)
**Dependencies:** Phase 1 (help sync blocking)
**Parallelizable:** Partially - 2.1 must complete before 2.2

### Goals
- Modularize common-patterns.md for maintainability
- Create comprehensive plugin validation framework
- Standardize command section order

### Work Items

#### 2.1 Modularize Common-Patterns Reference
**Recommendation Ref:** A1
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md`
- `plugins/personal-plugin/references/patterns/` (new directory)

**Description:**
Split 892-line common-patterns.md into focused pattern files.

Create new files:
```
references/patterns/
  naming.md          - File and command naming (~100 lines)
  validation.md      - Input validation and error handling (~150 lines)
  output.md          - Output files, directories, preview (~120 lines)
  workflow.md        - State management, resume, sessions (~180 lines)
  testing.md         - Argument testing, dry-run (~100 lines)
  logging.md         - Audit logging, progress reporting (~100 lines)
```

Keep common-patterns.md as index linking to each pattern file.

**Acceptance Criteria:**
- [x] 6 focused pattern files created
- [x] common-patterns.md becomes index with links
- [x] All content preserved (no patterns lost)
- [x] Command templates updated to reference specific files

---

#### 2.2 Create Plugin Validation Framework
**Recommendation Ref:** A2
**Files Affected:**
- `plugins/personal-plugin/commands/validate-plugin.md`
- `schemas/command.json` (new)

**Description:**
Extend validate-plugin to check pattern compliance.

Add validation for:
1. Command frontmatter against schema
2. Required sections (Input Validation, Instructions)
3. Output naming convention compliance
4. Error message format adherence
5. Flag usage consistency

Add new flags:
- `--strict` - Fail on any pattern violation
- `--report` - Generate detailed compliance report

**Acceptance Criteria:**
- [x] Command schema created
- [x] Section order validation implemented
- [x] `--strict` mode fails on violations
- [x] `--report` generates compliance summary

---

#### 2.3 Standardize Command Section Order
**Recommendation Ref:** A4
**Files Affected:**
- `plugins/personal-plugin/references/templates/*.md` (all 5 templates)
- Selected commands needing reordering

**Description:**
Define and enforce canonical section order.

Canonical order:
1. Frontmatter (description, allowed-tools)
2. Title (# Command Name)
3. Brief description paragraph
4. Input Validation
5. Instructions
6. Output Format (if applicable)
7. Examples
8. Performance (if applicable)

1. Update all 5 command templates with section comments
2. Audit existing commands for compliance
3. Reorder any commands that deviate

**Acceptance Criteria:**
- [x] Templates updated with explicit section order
- [x] Audit identifies non-compliant commands
- [x] Top 5 most-used commands reordered if needed

---

#### 2.4 Strengthen Schema Validation Enforcement
**Recommendation Ref:** Q2
**Files Affected:**
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/ask-questions.md`
- `plugins/personal-plugin/commands/finish-document.md`

**Description:**
Ensure consistent schema validation across Q&A workflow.

1. Audit current validation behavior in each command
2. Ensure `--force` flag behavior is uniform
3. Add validation status to output messages
4. Consider adding schema for assessment output

**Acceptance Criteria:**
- [x] All 3 Q&A commands validate consistently
- [x] `--force` flag documented and working
- [x] Validation status shown in command output

---

### Phase 2 Testing Requirements
- Test validation framework catches known violations
- Verify modularized patterns are discoverable
- Test `--strict` mode fails appropriately

### Phase 2 Completion Checklist
- [x] All work items complete
- [x] Pattern modularization verified
- [x] Validation framework tested
- [x] CHANGELOG updated

---

## Phase 3: Developer Experience

**Estimated Effort:** ~70,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (validation framework)
**Parallelizable:** Yes - all items are independent

### Goals
- Expand command templates for all pattern types
- Create plugin developer onboarding guide
- Add integration tests for core commands

### Work Items

#### 3.1 Expand Command Pattern Templates
**Recommendation Ref:** D1
**Files Affected:**
- `plugins/personal-plugin/references/templates/synthesis.md` (new)
- `plugins/personal-plugin/references/templates/conversion.md` (new)
- `plugins/personal-plugin/references/templates/planning.md` (new)
- `plugins/personal-plugin/commands/new-command.md`

**Description:**
Add missing templates for synthesis, conversion, and planning patterns.

1. Create synthesis.md based on consolidate-documents
2. Create conversion.md based on convert-markdown
3. Create planning.md based on plan-improvements
4. Update /new-command to offer template selection

**Acceptance Criteria:**
- [x] 3 new templates created with all required sections
- [x] Templates include pattern-specific guidance
- [x] /new-command offers 8 template options

---

#### 3.2 Create Plugin Developer Onboarding Guide
**Recommendation Ref:** D2
**Files Affected:**
- `docs/PLUGIN-DEVELOPMENT.md` (new)
- `CONTRIBUTING.md` (add link)

**Description:**
Create step-by-step tutorial for new plugin developers.

Sections:
1. Prerequisites and setup (5 min read)
2. Creating your first command (15 min tutorial)
3. Testing your command locally
4. Understanding patterns (links to pattern files)
5. Submitting for review (PR checklist)
6. Common mistakes and solutions

**Acceptance Criteria:**
- [x] Guide created with all 6 sections
- [x] Tutorial uses existing command as example
- [x] Common mistakes section complete
- [x] CONTRIBUTING.md links to new guide

---

#### 3.3 Add Integration Tests for Core Commands
**Recommendation Ref:** D3
**Files Affected:**
- `tests/integration/test_validate_plugin.py` (new)
- `tests/integration/test_bump_version.py` (new)
- `tests/fixtures/valid-plugin/` (new)
- `tests/fixtures/invalid-plugin/` (new)

**Description:**
Add integration tests for validate-plugin and bump-version commands.

1. Create test fixtures (valid and invalid plugin structures)
2. Test validate-plugin catches known violations
3. Test bump-version updates all version locations
4. Add to CI pipeline

**Acceptance Criteria:**
- [x] Test fixtures created for valid/invalid plugins
- [x] validate-plugin tests pass known-good, fail known-bad
- [x] bump-version tests verify multi-file updates
- [x] Tests run in CI

---

#### 3.4 Document Common Development Mistakes
**Recommendation Ref:** D4
**Files Affected:**
- `CONTRIBUTING.md` or `TROUBLESHOOTING.md`

**Description:**
Add section documenting common development mistakes.

Document:
1. Adding `name` field to frontmatter (causes discovery issues)
2. Forgetting to update help.md (sync drift)
3. Using wrong output directory
4. Missing Input Validation section
5. Inconsistent flag naming

**Acceptance Criteria:**
- [x] 5+ common mistakes documented
- [x] Each includes the fix
- [x] References validation that would catch it

---

### Phase 3 Testing Requirements
- Test new templates with /new-command
- Verify onboarding guide is followable
- Run integration tests on CI

### Phase 3 Completion Checklist
- [x] All work items complete
- [x] Templates tested with /new-command
- [x] Integration tests passing
- [x] CHANGELOG updated

---

## Phase 4: Advanced Capabilities

**Estimated Effort:** ~55,000 tokens (including testing/fixes)
**Dependencies:** Phase 3 (tests for validation)
**Parallelizable:** Yes - N1 and N2 are independent

### Goals
- Add CI/CD validation pipeline
- Create plugin maturity scorecard
- Implement interactive parameter prompting

### Work Items

#### 4.1 Add CI/CD Validation Pipeline
**Recommendation Ref:** N1
**Files Affected:**
- `.github/workflows/validate.yml` (new)
- `README.md` (add badge)

**Description:**
Create GitHub Actions workflow for automated validation.

Workflow steps:
1. Run `/validate-plugin --all --strict`
2. Check help.md synchronization
3. Run pytest tests
4. Verify CHANGELOG updated for version changes
5. Lint markdown files

**Acceptance Criteria:**
- [x] Workflow file created
- [x] All checks pass on main branch
- [x] Status check required for merge
- [x] Badge added to README

---

#### 4.2 Create Plugin Maturity Scorecard
**Recommendation Ref:** N2
**Files Affected:**
- `plugins/personal-plugin/commands/validate-plugin.md`

**Description:**
Add scorecard feature to validate-plugin command.

Maturity levels:
- **Level 1 (Basic)**: Valid plugin.json, commands parse
- **Level 2 (Standard)**: Help.md complete, all patterns followed
- **Level 3 (Complete)**: Tests exist, all flags implemented
- **Level 4 (Exemplary)**: Full documentation, CI validation

Add `--scorecard` flag to validate-plugin.

**Acceptance Criteria:**
- [x] Scorecard logic implemented
- [x] 4 maturity levels defined
- [x] Per-plugin and aggregate scores
- [x] Output shows improvement suggestions

---

#### 4.3 Add Interactive Parameter Prompting
**Recommendation Ref:** U5
**Files Affected:**
- `plugins/personal-plugin/references/patterns/validation.md`
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/assess-document.md`

**Description:**
Add prompting for missing required parameters.

1. Document prompting pattern in validation.md
2. Implement in 2 generator commands
3. Add `--no-prompt` flag for scripts

**Acceptance Criteria:**
- [x] Prompting pattern documented
- [x] 2 commands prompt for missing parameters
- [x] `--no-prompt` disables prompting

---

#### 4.4 Create Quick Reference Card
**Recommendation Ref:** U3
**Files Affected:**
- `QUICK-REFERENCE.md` (new)
- `README.md` (add link)

**Description:**
Create single-page quick reference for developers.

Contents:
- Command naming rules
- Frontmatter template
- Output file naming pattern
- Output directory table
- Input validation template
- Common flags table

**Acceptance Criteria:**
- [x] Quick reference under 100 lines
- [x] Covers all essential patterns
- [x] README links to quick reference

---

### Phase 4 Testing Requirements
- Test CI workflow on PR
- Test scorecard output accuracy
- Verify prompting works correctly

### Phase 4 Completion Checklist
- [x] All work items complete
- [x] CI pipeline active
- [x] Scorecard working
- [x] CHANGELOG updated

---

## Parallel Work Opportunities

| Work Item A | Can Run With | Notes |
|-------------|--------------|-------|
| 1.1 README tables | 1.2 Help sync blocking | Independent |
| 1.3 Directory creation | 1.4 BPMN help | Different plugins |
| 2.1 Pattern modularization | 2.3 Section order | Can reference same files |
| 3.1 Templates | 3.2 Onboarding guide | Templates inform guide |
| 4.1 CI/CD pipeline | 4.2 Scorecard | Independent |
| 4.3 Parameter prompting | 4.4 Quick reference | Independent |

**Maximum Parallelism:**
- Phase 1: 3 parallel streams (1.1+1.2, 1.3+1.4, 1.5)
- Phase 2: 2 parallel streams (2.1+2.3, 2.2+2.4)
- Phase 3: 2 parallel streams (3.1+3.2, 3.3+3.4)
- Phase 4: 2 parallel streams (4.1+4.2, 4.3+4.4)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Pattern modularization breaks references | Medium | Medium | Maintain common-patterns.md as index; update templates |
| Validation framework too strict | Medium | Low | Start with warnings; add --strict for blocking |
| CI pipeline slows development | Low | Medium | Keep checks fast (<2 min); allow skip for docs-only |
| Scorecard criteria unclear | Medium | Low | Start simple; iterate based on feedback |

---

## Success Metrics

| Metric | Current | Target | Measured By |
|--------|---------|--------|-------------|
| README completeness | Truncated | Full descriptions | Manual review |
| Help.md sync | Optional | Blocking | Pre-commit hook |
| Pattern files | 1 (892 lines) | 7 (modular) | File count |
| Command templates | 5 | 8 | Template count |
| Test coverage | Q&A only | +validate, bump | pytest count |
| CI validation | None | Active | GitHub status |

---

## Post-Implementation

After all phases complete:
1. Run `/validate-plugin --all --scorecard` on entire repo
2. Update all version numbers (use `/bump-version`)
3. Create release notes from CHANGELOG
4. Consider additional phases for:
   - Audit logging (deferred - low priority)
   - Usage analytics (deferred - privacy concerns)
   - Cross-plugin chaining (deferred - complex)

---

*Implementation plan generated by Claude on 2026-01-15T09:45:00*
