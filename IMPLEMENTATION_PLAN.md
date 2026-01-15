# Implementation Plan

**Generated:** 2026-01-14
**Based On:** RECOMMENDATIONS.md
**Total Phases:** 4

---

## Plan Overview

This plan organizes 18 recommendations into 4 phases, prioritizing quick wins and high-impact improvements first, then building toward strategic infrastructure and new capabilities. Each phase is sized to complete within approximately 100,000 tokens including testing and fixes.

**Phasing Strategy:**
- **Phase 1:** Quick Wins - High impact, low effort improvements (immediate value)
- **Phase 2:** Foundation - Schema contracts and automation infrastructure
- **Phase 3:** Developer Experience - Tooling to reduce maintenance burden
- **Phase 4:** New Capabilities - Additional features and integrations

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Tokens | Dependencies |
|-------|------------|------------------|-------------|--------------|
| 1 | Quick Wins | Output locations, dry-run modes, hook extension | ~50K | None |
| 2 | Foundation | JSON schemas, help automation | ~60K | None |
| 3 | Developer Experience | Command templates, plugin scaffolding | ~70K | Phase 2 |
| 4 | New Capabilities | Output formats, batch execution, update checker | ~60K | Phase 2 |

---

## Phase 1: Quick Wins

**Estimated Effort:** ~50,000 tokens (including testing/fixes)
**Dependencies:** None
**Parallelizable:** Yes - all items are independent

### Goals
- Immediate user experience improvements
- Safety improvements for destructive operations
- Documentation consistency
- Enhanced validation

### Work Items

#### 1.1 Enforce Standard Output Locations
**Recommendation Ref:** Q1
**Files Affected:**
- `plugins/personal-plugin/commands/consolidate-documents.md`
- `plugins/personal-plugin/commands/develop-image-prompt.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Audit all commands for output location compliance and update non-compliant commands:
1. Review each command's output location specification
2. Update `/consolidate-documents` to output to `reports/` directory
3. Update `/develop-image-prompt` to output to `reports/` directory
4. Add auto-creation of output directories if missing

**Acceptance Criteria:**
- [x] All commands specify output location
- [x] Locations follow `common-patterns.md` standards
- [x] Directories created automatically if missing

---

#### 1.2 Add Dry-Run Mode to Destructive Commands
**Recommendation Ref:** N1
**Files Affected:**
- `plugins/personal-plugin/skills/ship.md`
- `plugins/personal-plugin/commands/clean-repo.md`
- `plugins/personal-plugin/commands/bump-version.md`

**Description:**
Add `--dry-run` flag to commands with side effects:
1. `/ship --dry-run` - Show branch, commit, PR without creating
2. `/clean-repo --dry-run` - List files to delete without deleting
3. `/bump-version --dry-run` - Show version changes without applying

Update Input Validation sections to document the flag.

**Acceptance Criteria:**
- [x] `--dry-run` flag documented in Input Validation
- [x] Dry-run output clearly marked as preview
- [x] No side effects when dry-run enabled

---

#### 1.3 Extend Pre-commit Hook
**Recommendation Ref:** D1
**Files Affected:**
- `scripts/pre-commit`

**Description:**
Extend pre-commit hook to catch more issues:
1. Check that help.md has entry for each command/skill filename
2. Validate timestamp format in examples matches `YYYYMMDD-HHMMSS`
3. Warn if output location pattern not found in command

**Acceptance Criteria:**
- [x] Hook checks help.md sync
- [x] Hook validates timestamp format
- [x] Hook runs in < 5 seconds
- [x] Clear error messages with suggestions

---

#### 1.4 Add Utility Command Category
**Recommendation Ref:** U4
**Files Affected:**
- `CLAUDE.md`

**Description:**
Add "Utility commands" pattern to CLAUDE.md patterns section:
```markdown
- **Utility commands** (`validate-plugin`, `bump-version`, `review-pr`): Repository maintenance and automation tools
```

**Acceptance Criteria:**
- [x] New pattern category documented
- [x] All utility commands listed
- [x] Pattern description clear

---

#### 1.5 Standardize Issue Severity Naming
**Recommendation Ref:** Q3
**Files Affected:**
- `plugins/personal-plugin/commands/assess-document.md`
- `plugins/personal-plugin/commands/review-pr.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Standardize severity levels across all assessment commands:
- **CRITICAL** - Must be addressed immediately
- **WARNING** - Should be addressed before completion
- **SUGGESTION** - Optional improvement

Update commands to use consistent terminology.

**Acceptance Criteria:**
- [x] Severity levels documented in common-patterns.md
- [x] All assessment commands use consistent terms
- [x] `/ship` auto-review aligns with standards

---

### Phase 1 Testing Requirements
- Test dry-run flags produce expected preview output
- Verify pre-commit hook catches missing help entries
- Confirm output locations follow standards

### Phase 1 Completion Checklist
- [x] All work items complete
- [x] Documentation updated
- [x] No regressions introduced (320 tests pass)
- [x] CHANGELOG updated

---

## Phase 2: Foundation

**Estimated Effort:** ~60,000 tokens (including testing/fixes)
**Dependencies:** None (can run parallel to Phase 1)
**Parallelizable:** Yes - 2.1 and 2.2 are independent

### Goals
- Establish JSON schema contracts for command chains
- Automate help skill generation
- Reduce documentation drift

### Work Items

#### 2.1 Define JSON Schema Contracts
**Recommendation Ref:** A1
**Files Affected:**
- `schemas/questions.json` (new)
- `schemas/answers.json` (new)
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/ask-questions.md`
- `plugins/personal-plugin/commands/finish-document.md`

**Description:**
Create JSON Schema definitions for command chain outputs:

1. Create `schemas/` directory
2. Define `questions.json` schema:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["metadata", "questions"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["source_document", "generated_at", "total_questions"],
      "properties": {
        "source_document": { "type": "string" },
        "generated_at": { "type": "string", "format": "date-time" },
        "total_questions": { "type": "integer", "minimum": 0 }
      }
    },
    "questions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "text", "context"],
        "properties": {
          "id": { "type": "string" },
          "text": { "type": "string" },
          "context": { "type": "string" },
          "category": { "type": "string" },
          "priority": { "enum": ["high", "medium", "low"] }
        }
      }
    }
  }
}
```

3. Define `answers.json` schema similarly
4. Update commands to reference schemas
5. Add validation guidance to commands

**Acceptance Criteria:**
- [x] Schema files created and valid
- [x] Commands reference schemas
- [x] Schema documentation in README or dedicated doc

---

#### 2.2 Automate Help Skill Generation
**Recommendation Ref:** A2
**Files Affected:**
- `scripts/generate-help.py` (new)
- `plugins/personal-plugin/skills/help.md`
- `plugins/bpmn-plugin/skills/help.md`

**Description:**
Create script to auto-generate help.md from command metadata:

1. Create `scripts/generate-help.py` that:
   - Scans `commands/*.md` and `skills/*.md`
   - Extracts frontmatter description
   - Extracts Input Validation section for arguments
   - Extracts Example section
   - Generates help.md in standard format

2. Output format matches current help.md structure
3. Add to pre-commit hook as optional check
4. Document usage in CONTRIBUTING.md

**Acceptance Criteria:**
- [x] Script generates valid help.md
- [x] Output matches current help.md structure
- [x] Script runs successfully on both plugins
- [x] Usage documented

---

### Phase 2 Testing Requirements
- Validate generated JSON against schemas
- Test help generation produces correct output
- Verify schema validation catches invalid JSON

### Phase 2 Completion Checklist
- [x] All work items complete
- [x] Schemas documented
- [x] Help generation working
- [x] CHANGELOG updated

---

## Phase 3: Developer Experience

**Estimated Effort:** ~70,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (help generation)
**Parallelizable:** Partially - 3.1 and 3.2 can run in parallel

### Goals
- Reduce boilerplate for new commands
- Simplify plugin creation
- Improve contribution workflow

### Work Items

#### 3.1 Create Command Template Generator
**Recommendation Ref:** D2
**Files Affected:**
- `plugins/personal-plugin/commands/new-command.md` (new)
- `plugins/personal-plugin/references/templates/` (new directory)
- `plugins/personal-plugin/references/templates/read-only.md` (new)
- `plugins/personal-plugin/references/templates/interactive.md` (new)
- `plugins/personal-plugin/references/templates/workflow.md` (new)

**Description:**
Create `/new-command` skill that generates command scaffolds:

1. Create template files for each pattern type:
   - `read-only.md` - Analysis commands
   - `interactive.md` - Q&A commands
   - `workflow.md` - Multi-step commands
   - `generator.md` - Output generation commands
   - `utility.md` - Maintenance commands

2. Create `/new-command` skill that:
   - Asks for command name (validates kebab-case)
   - Asks for description
   - Asks for pattern type
   - Generates command file from template
   - Adds help.md entry (or reminds to run generate-help)
   - Reminds about README and CHANGELOG

**Acceptance Criteria:**
- [x] Templates exist for all pattern types
- [x] Generated commands pass validation
- [x] Help entries generated or reminded
- [x] Usage documented in CONTRIBUTING.md

---

#### 3.2 Add Plugin Scaffolding Command
**Recommendation Ref:** A3
**Files Affected:**
- `plugins/personal-plugin/commands/scaffold-plugin.md` (new)

**Description:**
Create `/scaffold-plugin` command for new plugin setup:

1. Asks for plugin name (validates naming conventions)
2. Asks for description
3. Creates directory structure:
   ```
   plugins/[name]/
     .claude-plugin/
       plugin.json
     commands/
     skills/
       help.md
   ```
4. Generates template `plugin.json` with metadata
5. Creates starter `help.md`
6. Adds entry to `marketplace.json`
7. Reports next steps

**Acceptance Criteria:**
- [x] Plugin structure created correctly
- [x] plugin.json valid
- [x] help.md follows template
- [x] marketplace.json updated

---

#### 3.3 Reduce Files Touched for New Commands
**Recommendation Ref:** D4
**Files Affected:**
- `CONTRIBUTING.md`
- `scripts/update-readme.py` (new)

**Description:**
Create automation to reduce manual updates:

1. Create `scripts/update-readme.py` that:
   - Scans command/skill frontmatter
   - Updates README.md command tables automatically
   - Preserves non-table content

2. Update CONTRIBUTING.md with simplified workflow:
   - Create command file
   - Run `scripts/generate-help.py`
   - Run `scripts/update-readme.py`
   - Update CHANGELOG manually

3. Consider combining scripts into single `scripts/sync-docs.py`

**Acceptance Criteria:**
- [x] README tables auto-generated
- [x] CONTRIBUTING.md updated
- [x] Workflow simplified to 3-4 steps

---

### Phase 3 Testing Requirements
- Test command generation with each pattern type
- Verify plugin scaffolding creates valid structure
- Confirm README updates preserve content

### Phase 3 Completion Checklist
- [x] All work items complete
- [x] Templates validated
- [x] Scripts documented
- [x] CONTRIBUTING.md updated
- [x] CHANGELOG updated

---

## Phase 4: New Capabilities

**Estimated Effort:** ~60,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (schemas for format options)
**Parallelizable:** Yes - all items are independent

### Goals
- Add requested features
- Improve integration options
- Enable automation workflows

### Work Items

#### 4.1 Add Output Format Options
**Recommendation Ref:** N2
**Files Affected:**
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/assess-document.md`
- `plugins/personal-plugin/commands/analyze-transcript.md`

**Description:**
Add `--format` flag to relevant commands:

1. `/define-questions --format [json|csv]`
   - JSON: Current behavior (default)
   - CSV: Flat format with columns: id, text, context, category, priority

2. `/assess-document --format [md|json]`
   - MD: Current behavior (default)
   - JSON: Structured with scores, issues array, recommendations

3. `/analyze-transcript --format [md|json]`
   - MD: Current behavior (default)
   - JSON: Structured with sections, action items, decisions

Update Input Validation sections and examples.

**Acceptance Criteria:**
- [x] `--format` flag works for each command
- [x] Default behavior unchanged
- [x] Output formats documented
- [x] Examples updated

---

#### 4.2 Add Interactive Help Within Commands
**Recommendation Ref:** U1
**Files Affected:**
- `plugins/personal-plugin/commands/ask-questions.md`
- `plugins/personal-plugin/commands/finish-document.md`
- `plugins/bpmn-plugin/skills/bpmn-generator.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Standardize session commands across interactive commands:

1. Document standard session commands in `common-patterns.md`:
   - `help` - Show available actions
   - `status` / `progress` - Show current position
   - `back` / `previous` - Return to previous step
   - `skip` - Skip current item
   - `quit` / `exit` - Exit with save prompt

2. Add "Session Commands" section to each interactive command
3. Ensure all interactive commands implement these

**Acceptance Criteria:**
- [x] Session commands documented
- [x] All interactive commands support standard commands
- [x] Help text shown when `help` entered

---

#### 4.3 Add Plugin Update Checker
**Recommendation Ref:** N4
**Files Affected:**
- `plugins/personal-plugin/commands/check-updates.md` (new)

**Description:**
Create `/check-updates` command:

1. Reads installed plugin versions from `plugin.json` files
2. Compares against `marketplace.json`
3. Reports available updates:
   ```
   Plugin Updates Available:

   personal-plugin: 2.0.0 → 2.1.0
   - Added /new-command skill
   - Fixed output location consistency

   bpmn-plugin: 1.6.0 (up to date)
   ```

4. Read-only; no automatic updates

**Acceptance Criteria:**
- [x] Version comparison works
- [x] Clear output format
- [x] No side effects
- [x] Handles network errors gracefully

---

#### 4.4 Standardize Argument Validation Messages
**Recommendation Ref:** U2
**Files Affected:**
- `plugins/personal-plugin/commands/develop-image-prompt.md`
- `plugins/personal-plugin/commands/consolidate-documents.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Update commands with unclear argument handling:

1. Document standard error format in `common-patterns.md`:
   ```
   Error: Missing required argument
   Usage: /command-name <required-arg> [optional-arg]
   Example: /command-name my-file.md

   Arguments:
     <required-arg>  Description of required argument
     [optional-arg]  Description of optional argument (default: value)
   ```

2. Update `/develop-image-prompt` to clarify 3 input types
3. Update `/consolidate-documents` to specify 2+ document requirement clearly

**Acceptance Criteria:**
- [x] Error format documented
- [x] Commands show consistent errors
- [x] Input types clearly distinguished

---

### Phase 4 Testing Requirements
- Test format options produce valid output
- Verify session commands work in interactive modes
- Test update checker with version mismatches

### Phase 4 Completion Checklist
- [x] All work items complete
- [x] New features documented
- [x] Examples updated
- [x] CHANGELOG updated

---

## Parallel Work Opportunities

| Work Item A | Can Run With | Notes |
|-------------|--------------|-------|
| 1.1 Output locations | 1.2 Dry-run modes | Independent files |
| 1.3 Hook extension | 1.4 Utility category | Hook vs docs |
| 2.1 JSON schemas | 2.2 Help automation | Independent systems |
| 3.1 Command templates | 3.2 Plugin scaffolding | Different plugins |
| 4.1 Format options | 4.2 Interactive help | Different commands |
| 4.3 Update checker | 4.4 Argument validation | Independent |

**Maximum Parallelism:**
- Phase 1: 3 parallel streams (1.1+1.2, 1.3+1.4, 1.5)
- Phase 2: 2 parallel streams (2.1, 2.2)
- Phase 3: 2 parallel streams (3.1+3.2, 3.3)
- Phase 4: 3 parallel streams (4.1, 4.2+4.4, 4.3)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema changes break existing files | Medium | High | Version schemas; provide migration guidance |
| Help generation misses edge cases | Medium | Medium | Manual review of generated output |
| Pre-commit hook slows workflow | Low | Medium | Keep checks under 5 seconds; allow bypass |
| Template changes diverge from actual | Low | Medium | Generate templates from working commands |
| Format conversion loses data | Low | High | Test with complex real-world examples |

---

## Success Metrics

| Metric | Current | Target | Measured By |
|--------|---------|--------|-------------|
| Files touched for new command | 5+ | 2-3 | Manual count |
| Help.md sync accuracy | Manual | Automated | Script output |
| Commands with dry-run | 0 | 3 | Grep for --dry-run |
| JSON schema coverage | 0% | 100% for chains | Schema file count |
| Pre-commit validation coverage | Basic | Comprehensive | Hook check count |

---

## Post-Implementation

After all phases complete:
1. Run `/validate-plugin` on entire repo
2. Update all version numbers (use `/bump-version`)
3. Create release notes from CHANGELOG
4. Consider additional phases for:
   - Batch command execution (N3) - deferred due to complexity
   - Command testing framework (D3) - deferred, needs schema foundation
   - Complex algorithm refactoring (A4) - deferred, lower priority

---

*Implementation plan generated by Claude on 2026-01-14*

---

## Implementation Complete

**Completed:** 2026-01-14

All 4 phases (14 work items) have been successfully implemented:
- ✅ Phase 1: Quick Wins (5 items) - Output locations, dry-run modes, pre-commit hook, utility category, severity naming
- ✅ Phase 2: Foundation (2 items) - JSON schemas, help automation
- ✅ Phase 3: Developer Experience (3 items) - Command templates, plugin scaffolding, README automation
- ✅ Phase 4: New Capabilities (4 items) - Output formats, session commands, update checker, argument validation

**Verification:**
- All 320 tests passing (92% coverage)
- Help files up to date (verified with `python scripts/generate-help.py --all --check`)
- README up to date (verified with `python scripts/update-readme.py --check`)
- CHANGELOG updated with v2.1.0 release notes
