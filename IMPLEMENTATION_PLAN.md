# Implementation Plan

**Generated:** 2026-01-14
**Based On:** RECOMMENDATIONS.md (post v2.1.0)
**Total Phases:** 4

---

## Plan Overview

This plan organizes 16 recommendations into 4 phases, prioritizing documentation and quick wins first, then building quality assurance infrastructure, and finally addressing ecosystem maturity. Each phase is designed to deliver standalone value while building toward comprehensive quality assurance.

**Phasing Strategy:**
- **Phase 1:** Documentation & Quick Wins - Immediate user-facing improvements
- **Phase 2:** Quality Assurance Foundation - Schema validation and testing patterns
- **Phase 3:** Testing Infrastructure - Integration tests and shared test utilities
- **Phase 4:** Ecosystem Maturity - Plugin system improvements and advanced UX

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Tokens | Dependencies |
|-------|------------|------------------|-------------|--------------|
| 1 | Documentation | WORKFLOWS.md, TROUBLESHOOTING.md, SECURITY.md, dependency checks | ~40K | None |
| 2 | Quality Foundation | Runtime schema validation, argument testing patterns | ~50K | None |
| 3 | Testing Infrastructure | Integration tests, shared test utilities | ~70K | Phase 2 |
| 4 | Ecosystem Maturity | Namespace support, preview mode, state management | ~60K | Phase 1 |

---

## Phase 1: Documentation & Quick Wins

**Estimated Effort:** ~40,000 tokens (including testing/fixes)
**Dependencies:** None
**Parallelizable:** Yes - all items are independent

### Goals
- Improve user self-service with documentation
- Prevent cryptic errors from missing dependencies
- Show users how to chain commands effectively
- Build trust with security documentation

### Work Items

#### 1.1 Create Workflow Documentation
**Recommendation Ref:** W1
**Files Affected:**
- `WORKFLOWS.md` (new)
- `README.md` (add link)

**Description:**
Create comprehensive workflow documentation showing how to chain commands for common use cases:

1. **Document Completion Workflow**
   - `/define-questions` -> `/ask-questions` -> `/finish-document`
   - Include file naming patterns and expected outputs

2. **Code Review Workflow**
   - `/review-pr` -> fix issues -> `/ship`
   - Show typical iteration cycle

3. **Architecture Analysis Workflow**
   - `/review-arch` for quick analysis
   - `/plan-improvements` for deep analysis with implementation plan
   - Working through IMPLEMENTATION_PLAN.md phases

4. **Repository Maintenance Workflow**
   - `/validate-plugin` -> `/bump-version` -> `/ship`
   - `/clean-repo` for periodic cleanup

5. **New Command Development Workflow**
   - `/new-command` -> test -> `/ship`
   - Reference to CONTRIBUTING.md

**Acceptance Criteria:**
- [ ] WORKFLOWS.md created with 5+ documented workflows
- [ ] Each workflow shows complete command sequence
- [ ] File naming patterns documented
- [ ] README.md links to WORKFLOWS.md

---

#### 1.2 Create Troubleshooting Guide
**Recommendation Ref:** D1
**Files Affected:**
- `TROUBLESHOOTING.md` (new)
- `README.md` (add link)

**Description:**
Create troubleshooting guide covering common issues:

1. **Installation Issues**
   - Missing Python dependencies
   - PATH configuration problems
   - Permission errors

2. **Dependency Issues**
   - pandoc not found (`/convert-markdown`)
   - graphviz not found (`/bpmn-to-drawio`)
   - Platform-specific installation instructions

3. **Command Failures**
   - Invalid argument errors
   - File not found errors
   - Schema validation failures

4. **Output Problems**
   - Wrong output directory
   - Malformed JSON/XML
   - Missing expected files

5. **Workflow Issues**
   - Interrupted sessions
   - Resume problems
   - State file conflicts

Format: Symptom -> Cause -> Solution (with commands)

**Acceptance Criteria:**
- [ ] TROUBLESHOOTING.md created with 10+ documented issues
- [ ] Each issue has symptom, cause, solution format
- [ ] Platform-specific solutions where applicable
- [ ] README.md links to TROUBLESHOOTING.md

---

#### 1.3 Create Security Documentation
**Recommendation Ref:** D2
**Files Affected:**
- `SECURITY.md` (new)
- `README.md` (add link)

**Description:**
Document security model and considerations:

1. **Data Handling**
   - What data commands process
   - Where data is stored
   - What gets sent to Claude API

2. **Secret Detection**
   - `/ship` auto-review scans for hardcoded secrets
   - Other commands don't scan by default
   - Recommendations for sensitive documents

3. **Input Safety**
   - Commands trust input files
   - No sandboxing or isolation
   - User responsibility for input validation

4. **Output Safety**
   - Output files may contain sensitive data
   - `.gitignore` recommendations
   - Backup file handling

5. **Vulnerability Reporting**
   - Contact information
   - Response timeline expectations

**Acceptance Criteria:**
- [ ] SECURITY.md created
- [ ] Honest about current limitations
- [ ] Clear vulnerability reporting process
- [ ] README.md links to SECURITY.md

---

#### 1.4 Add Dependency Verification
**Recommendation Ref:** E1
**Files Affected:**
- `plugins/personal-plugin/commands/convert-markdown.md`
- `plugins/bpmn-plugin/skills/bpmn-to-drawio.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Add dependency checks to commands requiring external tools:

1. Update `common-patterns.md` with dependency check pattern:
```markdown
## Dependency Verification

Commands requiring external tools MUST check for them before processing:

1. Check if tool exists: `which <tool>` or `where <tool>` (Windows)
2. If missing, display platform-specific installation instructions
3. Exit with clear error message

Example error format:
```
Error: Required dependency 'pandoc' not found

/convert-markdown requires pandoc for document conversion.

Installation instructions:
  Windows: winget install pandoc
  Mac:     brew install pandoc
  Linux:   apt install pandoc

After installing, run the command again.
```
```

2. Update `/convert-markdown` with pandoc check
3. Update `/bpmn-to-drawio` with graphviz check

**Acceptance Criteria:**
- [ ] Dependency check pattern documented in common-patterns.md
- [ ] `/convert-markdown` checks for pandoc before processing
- [ ] `/bpmn-to-drawio` checks for graphviz before processing
- [ ] Error messages include platform-specific installation instructions

---

#### 1.5 Add Performance Expectations
**Recommendation Ref:** D3
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md`
- `plugins/personal-plugin/commands/test-project.md`
- `plugins/personal-plugin/commands/review-arch.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Add performance guidance to long-running commands:

1. Update `common-patterns.md` with performance documentation pattern:
```markdown
## Performance Expectations

Commands with variable duration SHOULD document expected timing:

## Performance
- Small inputs: 30-60 seconds
- Medium inputs: 1-3 minutes
- Large inputs: 3-10 minutes

Factors affecting performance:
- Input size and complexity
- Number of issues/questions found
- Network latency
```

2. Add performance section to:
   - `/plan-improvements` - Depends on codebase size
   - `/test-project` - Depends on test count and fix iterations
   - `/review-arch` - Depends on codebase complexity

**Acceptance Criteria:**
- [ ] Performance documentation pattern in common-patterns.md
- [ ] 3+ commands have performance expectations documented
- [ ] Guidance helps users identify abnormal behavior

---

### Phase 1 Testing Requirements
- Verify all new documentation files render correctly
- Test dependency verification catches missing tools
- Confirm documentation links work in README

### Phase 1 Completion Checklist
- [ ] All work items complete
- [ ] Documentation reviewed for accuracy
- [ ] README updated with links
- [ ] CHANGELOG updated

---

## Phase 2: Quality Assurance Foundation

**Estimated Effort:** ~50,000 tokens (including testing/fixes)
**Dependencies:** None (can run parallel to Phase 1)
**Parallelizable:** Yes - 2.1 and 2.2 are independent

### Goals
- Implement runtime schema validation
- Document argument testing patterns
- Establish quality assurance conventions

### Work Items

#### 2.1 Implement Runtime Schema Validation
**Recommendation Ref:** QA2
**Files Affected:**
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/ask-questions.md`
- `plugins/personal-plugin/commands/finish-document.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Add schema validation to commands that generate or consume structured data:

1. Update `common-patterns.md` with schema validation pattern:
```markdown
## Schema Validation

Commands generating JSON output MUST validate against schema before saving:

1. Generate output in memory
2. Validate against schema (schemas/questions.json, schemas/answers.json)
3. If valid: Save file and report success
4. If invalid: Report specific validation errors
5. Offer `--force` flag to save despite validation errors

Success message:
"Output validated against schemas/questions.json. Saved to reports/questions-*.json"

Error message:
"Schema validation failed:
  - questions[3].id: Required field missing
  - questions[7].priority: Must be one of: high, medium, low

Use --force to save anyway (not recommended)."
```

2. Update `/define-questions`:
   - Validate output against `schemas/questions.json`
   - Report validation status
   - Support `--force` flag

3. Update `/ask-questions`:
   - Validate input against `schemas/questions.json`
   - Validate output against `schemas/answers.json`

4. Update `/finish-document`:
   - Validate input against `schemas/answers.json`

**Acceptance Criteria:**
- [ ] Schema validation pattern documented
- [ ] `/define-questions` validates output
- [ ] `/ask-questions` validates input and output
- [ ] `/finish-document` validates input
- [ ] `--force` flag documented for override

---

#### 2.2 Document Argument Testing Patterns
**Recommendation Ref:** QA3
**Files Affected:**
- `CONTRIBUTING.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Document how to test command argument handling:

1. Update `common-patterns.md` with argument testing pattern:
```markdown
## Argument Testing

Commands SHOULD be tested for argument handling:

### Required Argument Missing
Input: `/command-name` (no arguments)
Expected: Standard error format with usage example

### Invalid Argument Value
Input: `/command-name invalid-file.xyz`
Expected: Clear error explaining what's wrong

### Optional Argument Defaults
Input: `/command-name file.md` (no --format)
Expected: Default format used (documented in Input Validation)

### Flag Parsing
Input: `/command-name file.md --dry-run`
Expected: Dry-run behavior (no side effects)
```

2. Update `CONTRIBUTING.md` with testing guidance:
```markdown
## Testing Your Command

Before submitting a PR, test your command with:
1. Missing required arguments
2. Invalid argument values
3. Default optional argument behavior
4. All documented flags (--dry-run, --format, etc.)

Document test results in PR description.
```

**Acceptance Criteria:**
- [ ] Argument testing patterns documented in common-patterns.md
- [ ] Testing guidance added to CONTRIBUTING.md
- [ ] Checklist format for PR testing

---

### Phase 2 Testing Requirements
- Test schema validation catches invalid JSON
- Verify validation error messages are helpful
- Confirm `--force` flag works correctly

### Phase 2 Completion Checklist
- [ ] All work items complete
- [ ] Schema validation working
- [ ] Testing patterns documented
- [ ] CHANGELOG updated

---

## Phase 3: Testing Infrastructure

**Estimated Effort:** ~70,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (schema validation)
**Parallelizable:** Partially - 3.1 and 3.2 can run in parallel after 3.1 fixtures created

### Goals
- Create integration tests for Q&A workflow
- Establish shared test infrastructure
- Enable CI/CD quality gates

### Work Items

#### 3.1 Create Integration Tests for Q&A Chain
**Recommendation Ref:** QA1
**Files Affected:**
- `tests/integration/` (new directory)
- `tests/fixtures/` (new directory)
- `tests/integration/test_qa_workflow.py` (new)
- `.github/workflows/test.yml` (new or update)

**Description:**
Create integration tests validating the Q&A workflow:

1. Create test fixtures:
   - `tests/fixtures/sample-prd.md` - Sample document with questions
   - `tests/fixtures/expected-questions.json` - Expected question extraction
   - `tests/fixtures/sample-answers.json` - Sample answers
   - `tests/fixtures/expected-updated-prd.md` - Expected final document

2. Create integration tests:
```python
# tests/integration/test_qa_workflow.py

def test_define_questions_output_schema():
    """Verify /define-questions output conforms to schema"""
    # Run command on sample document
    # Validate output against schemas/questions.json

def test_ask_questions_accepts_define_output():
    """Verify /ask-questions can parse /define-questions output"""
    # Load expected-questions.json
    # Verify it can be parsed as input

def test_finish_document_updates_correctly():
    """Verify /finish-document updates document with answers"""
    # Load sample-answers.json
    # Run /finish-document
    # Compare output to expected-updated-prd.md
```

3. Create GitHub Actions workflow:
```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install pytest jsonschema
      - run: pytest tests/integration/
```

**Acceptance Criteria:**
- [ ] Test fixtures created
- [ ] Integration tests for Q&A workflow
- [ ] Tests validate schema compliance
- [ ] GitHub Actions workflow runs tests

---

#### 3.2 Create Shared Test Infrastructure
**Recommendation Ref:** QA4
**Files Affected:**
- `tests/conftest.py` (new)
- `tests/helpers/` (new directory)
- `tests/helpers/schema_validator.py` (new)
- `tests/helpers/file_comparator.py` (new)
- `CONTRIBUTING.md`

**Description:**
Create shared test utilities that can be used across plugins:

1. Create `tests/conftest.py` with common fixtures:
```python
import pytest
import json
from pathlib import Path

@pytest.fixture
def schema_dir():
    return Path(__file__).parent.parent / "schemas"

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def questions_schema(schema_dir):
    with open(schema_dir / "questions.json") as f:
        return json.load(f)
```

2. Create `tests/helpers/schema_validator.py`:
```python
from jsonschema import validate, ValidationError

def validate_against_schema(data, schema):
    """Validate JSON data against schema, return errors"""
    try:
        validate(instance=data, schema=schema)
        return []
    except ValidationError as e:
        return [str(e)]
```

3. Create `tests/helpers/file_comparator.py`:
```python
def compare_files(expected_path, actual_path, ignore_timestamps=True):
    """Compare two files, optionally ignoring timestamps"""
    # Implementation
```

4. Update `CONTRIBUTING.md` with test infrastructure docs

**Acceptance Criteria:**
- [ ] Shared fixtures in conftest.py
- [ ] Schema validation helper
- [ ] File comparison helper
- [ ] Testing infrastructure documented

---

### Phase 3 Testing Requirements
- Integration tests pass on CI
- Test coverage reported
- Tests catch schema violations

### Phase 3 Completion Checklist
- [ ] All work items complete
- [ ] CI pipeline running tests
- [ ] Test infrastructure documented
- [ ] CHANGELOG updated

---

## Phase 4: Ecosystem Maturity

**Estimated Effort:** ~60,000 tokens (including testing/fixes)
**Dependencies:** Phase 1 (workflow documentation)
**Parallelizable:** Yes - all items are independent

### Goals
- Improve plugin ecosystem readiness
- Enhance user experience with preview and state management
- Enable future plugin composition

### Work Items

#### 4.1 Add Plugin Namespace Support
**Recommendation Ref:** E2
**Files Affected:**
- `plugins/personal-plugin/commands/validate-plugin.md`
- `plugins/personal-plugin/skills/help.md`
- `CLAUDE.md`

**Description:**
Implement optional namespace support for commands:

1. Document namespace convention in `CLAUDE.md`:
```markdown
## Command Namespacing

Commands can be invoked with explicit namespace:
- `/personal-plugin:review-arch` - Explicit namespace
- `/review-arch` - Short form (works if unambiguous)

If two plugins have commands with the same name, explicit namespace is required.
```

2. Update `/validate-plugin` to check for naming collisions:
   - Scan all plugins for command names
   - Warn if collision detected
   - Suggest namespace usage

3. Update `/help` to show namespace when relevant

**Acceptance Criteria:**
- [ ] Namespace convention documented
- [ ] `/validate-plugin` checks for collisions
- [ ] Warning message suggests namespace usage

---

#### 4.2 Add Plugin Dependency Declaration
**Recommendation Ref:** E3
**Files Affected:**
- `schemas/plugin.json` (new)
- `plugins/personal-plugin/commands/validate-plugin.md`
- `CLAUDE.md`

**Description:**
Add optional dependency declaration to plugin.json:

1. Create `schemas/plugin.json` with dependency support:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "dependencies": {
      "type": "object",
      "additionalProperties": {
        "type": "string",
        "description": "Semver version requirement"
      }
    }
  }
}
```

2. Document in `CLAUDE.md`:
```markdown
## Plugin Dependencies

Plugins can declare dependencies on other plugins:

```json
{
  "name": "advanced-plugin",
  "dependencies": {
    "personal-plugin": ">=2.0.0"
  }
}
```
```

3. Update `/validate-plugin` to check dependencies

**Acceptance Criteria:**
- [ ] Plugin schema with dependencies field
- [ ] Dependency syntax documented
- [ ] `/validate-plugin` validates dependencies

---

#### 4.3 Add Output Preview Mode
**Recommendation Ref:** U1
**Files Affected:**
- `plugins/personal-plugin/commands/define-questions.md`
- `plugins/personal-plugin/commands/analyze-transcript.md`
- `plugins/bpmn-plugin/skills/bpmn-generator.md`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Add `--preview` flag to commands generating structured output:

1. Document preview pattern in `common-patterns.md`:
```markdown
## Output Preview

Commands generating structured output SHOULD support `--preview`:

1. Generate output in memory
2. Validate against schema
3. Display summary (not full output):
   "Generated 15 questions in 3 categories"
   "Schema validation: PASSED"
4. Ask for confirmation: "Save to reports/questions-*.json? (y/n)"
5. Save only on confirmation
```

2. Add `--preview` to Input Validation of:
   - `/define-questions`
   - `/analyze-transcript`
   - `/bpmn-generator`

**Acceptance Criteria:**
- [ ] Preview pattern documented
- [ ] `--preview` flag added to 3+ commands
- [ ] Preview shows summary and validation status
- [ ] Confirmation required before save

---

#### 4.4 Add Workflow State Management
**Recommendation Ref:** W2
**Files Affected:**
- `plugins/personal-plugin/commands/ask-questions.md`
- `plugins/personal-plugin/commands/finish-document.md`
- `schemas/answers.json`
- `plugins/personal-plugin/references/common-patterns.md`

**Description:**
Implement resume capability for interrupted workflows:

1. Update `schemas/answers.json` with status field:
```json
{
  "metadata": {
    "status": { "enum": ["in_progress", "completed"] },
    "last_question_answered": { "type": "integer" }
  }
}
```

2. Document state management in `common-patterns.md`:
```markdown
## Workflow State Management

Interactive commands SHOULD support resuming:

1. On start, check for existing answer file
2. If found with status "in_progress":
   "Found incomplete session (15/47 questions). Resume? (y/n)"
3. If resume: Continue from last_question_answered
4. If not resume: Offer to start fresh or abort
```

3. Update `/ask-questions` and `/finish-document` with resume logic

**Acceptance Criteria:**
- [ ] Answer schema includes status field
- [ ] State management pattern documented
- [ ] `/ask-questions` supports resume
- [ ] `/finish-document` supports resume

---

#### 4.5 Add Audit Logging
**Recommendation Ref:** E4
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md`
- `plugins/personal-plugin/commands/clean-repo.md`
- `plugins/personal-plugin/skills/ship.md`

**Description:**
Add optional audit logging for commands with side effects:

1. Document audit logging pattern in `common-patterns.md`:
```markdown
## Audit Logging

Commands with side effects MAY support `--audit` flag:

1. Log file: `.claude-plugin/audit.log` (JSON lines)
2. Log entry format:
   {"timestamp": "...", "command": "clean-repo", "action": "delete", "path": "old-file.md"}
3. Enabled via `--audit` flag
4. Off by default for performance/privacy
```

2. Add `--audit` to `/clean-repo` and `/ship`
3. Log significant actions (file changes, git operations)

**Acceptance Criteria:**
- [ ] Audit logging pattern documented
- [ ] `/clean-repo` supports `--audit`
- [ ] `/ship` supports `--audit`
- [ ] Log format is JSON lines

---

### Phase 4 Testing Requirements
- Test namespace collision detection
- Verify preview mode works correctly
- Test resume functionality

### Phase 4 Completion Checklist
- [ ] All work items complete
- [ ] New features documented
- [ ] Examples updated
- [ ] CHANGELOG updated

---

## Parallel Work Opportunities

| Work Item A | Can Run With | Notes |
|-------------|--------------|-------|
| 1.1 Workflow docs | 1.2 Troubleshooting | Independent docs |
| 1.3 Security docs | 1.4 Dependency verification | Docs vs code |
| 2.1 Schema validation | 2.2 Testing patterns | Independent |
| 3.1 Integration tests | 3.2 Test infrastructure | After fixtures |
| 4.1 Namespace support | 4.2 Dependencies | Independent |
| 4.3 Preview mode | 4.4 State management | Different commands |

**Maximum Parallelism:**
- Phase 1: 3 parallel streams (1.1+1.2, 1.3+1.4, 1.5)
- Phase 2: 2 parallel streams (2.1, 2.2)
- Phase 3: 2 parallel streams (3.1, 3.2 after fixtures)
- Phase 4: 3 parallel streams (4.1+4.2, 4.3+4.4, 4.5)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema validation breaks existing workflows | Medium | High | `--force` flag for override; document migration |
| Integration tests flaky on CI | Medium | Medium | Use deterministic fixtures; avoid timing dependencies |
| Resume functionality complex | Medium | Medium | Start with simple detection; iterate |
| Namespace changes break existing usage | Low | High | Backward compatible; short form always works |
| Audit logging performance impact | Low | Low | Off by default; opt-in only |

---

## Success Metrics

| Metric | Current | Target | Measured By |
|--------|---------|--------|-------------|
| Documentation completeness | 3 docs | 6 docs | File count |
| Schema validation coverage | 0% | 100% for Q&A chain | Command audit |
| Integration test coverage | 0% | 80% for Q&A workflow | pytest coverage |
| Commands with --preview | 0 | 3+ | Grep for --preview |
| Commands with --audit | 0 | 2+ | Grep for --audit |

---

## Post-Implementation

After all phases complete:
1. Run `/validate-plugin` on entire repo
2. Update all version numbers (use `/bump-version`)
3. Create release notes from CHANGELOG
4. Consider additional phases for:
   - Workflow recommendation command (W3) - deferred, lower priority
   - Progress persistence (U2) - deferred, complex state management

---

*Implementation plan generated by Claude on 2026-01-14*
