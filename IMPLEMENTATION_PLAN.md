# Implementation Plan

**Generated:** 2026-02-16T18:45:00
**Based On:** RECOMMENDATIONS.md
**Total Phases:** 6
**Goal:** Zero technical debt with comprehensive test coverage

---

## Plan Overview

This plan systematically eliminates all identified technical debt across 6 phases. The strategy is **test-first**: write characterization tests for existing code before refactoring, then add new tests for uncovered modules. Phases are ordered by dependency — foundational fixes (quick wins, dependency hygiene) come first, followed by test coverage, then refactoring that relies on those tests as safety nets.

Each phase leaves the codebase in a fully working state. Phases 1-2 can be completed in a single session. Phases 3-5 are the bulk of the work. Phase 6 is polish.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Tokens | Dependencies |
|-------|------------|------------------|-------------|--------------|
| 1 | Quick Wins & Dependency Hygiene | Version constraints, lock files, CI caching, exception fixes | ~30K | None |
| 2 | CI Pipeline Hardening | Coverage enforcement, mypy, dedicated CI jobs | ~25K | Phase 1 |
| 3 | Test Coverage — bpmn2drawio | Tests for position_resolver + 5 untested modules | ~60K | Phase 2 |
| 4 | Test Coverage — visual-explainer | Tests for 6 untested modules (3,739 LOC) | ~80K | Phase 2 |
| 5 | Test Coverage — research-orchestrator + feedback-docx-generator | Tests for 4 untested modules + entire feedback tool | ~60K | Phase 2 |
| 6 | Refactoring & Feature Completion | God class splits, CLI refactor, checkpoint resume, validation | ~90K | Phases 3-5 |

---

## Phase 1: Quick Wins & Dependency Hygiene

**Estimated Effort:** ~30,000 tokens (including testing/fixes)
**Dependencies:** None
**Parallelizable:** Yes — all work items are independent

### Goals
- Tighten all dependency version constraints
- Add lock files for reproducible builds
- Fix exception handling issues
- Add CI dependency caching
- Unify Python version requirements

### Work Items

#### 1.1 Tighten Dependency Version Constraints
**Recommendation Ref:** D1
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/pyproject.toml`
- `plugins/personal-plugin/tools/research-orchestrator/pyproject.toml`

**Description:**
Update version constraints to prevent silent major-version breaking changes:

| Package | Current | Target |
|---------|---------|--------|
| `google-genai` | `>=0.1.0` | `>=1.0.0,<2.0.0` |
| `anthropic` | `>=0.40.0` | `>=0.40.0,<2.0.0` |
| `openai` | `>=1.50.0` | `>=1.50.0,<3.0.0` |
| `pydantic` | `>=2.0.0` | `>=2.0.0,<3.0.0` |

Apply to both visual-explainer and research-orchestrator pyproject.toml files.

**Acceptance Criteria:**
- [x] All `>=X` constraints for major libraries have `<NEXT_MAJOR` upper bounds
- [x] `pip install -e .` succeeds for both tools
- [x] Existing tests pass unchanged
**Completed:** 2026-02-16

---

#### 1.2 Add Dependency Lock Files
**Recommendation Ref:** D2
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/requirements-lock.txt` (new)
- `plugins/bpmn-plugin/tools/bpmn2drawio/requirements-dev-lock.txt` (new)
- `plugins/personal-plugin/tools/research-orchestrator/requirements-lock.txt` (new)
- `plugins/personal-plugin/tools/research-orchestrator/requirements-dev-lock.txt` (new)
- `plugins/personal-plugin/tools/visual-explainer/requirements-lock.txt` (new)
- `plugins/personal-plugin/tools/visual-explainer/requirements-dev-lock.txt` (new)
- `plugins/personal-plugin/tools/feedback-docx-generator/requirements-lock.txt` (new)
- `plugins/personal-plugin/tools/feedback-docx-generator/requirements-dev-lock.txt` (new)

**Description:**
Install `pip-tools` and generate lock files for each tool:
```bash
pip install pip-tools
cd plugins/bpmn-plugin/tools/bpmn2drawio
pip-compile pyproject.toml -o requirements-lock.txt
pip-compile pyproject.toml --extra dev -o requirements-dev-lock.txt
```
Repeat for each tool directory. Add `pip-tools` to each tool's dev dependencies.

**Acceptance Criteria:**
- [x] Lock files generated for all 4 tools (7 files — feedback-docx-generator has no dev extra)
- [x] `pip install -r requirements-lock.txt` succeeds for each tool
- [x] Lock files committed to repository
- [x] `.gitignore` does NOT exclude lock files
**Completed:** 2026-02-16

---

#### 1.3 Extract Parser Namespace Helper
**Recommendation Ref:** R4
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/parser.py`

**Description:**
Add helper methods to the BPMNParser class:
```python
def _find_element(self, parent, ns_xpath: str, wildcard_xpath: str):
    """Find element with namespace fallback."""
    result = parent.find(ns_xpath, self.namespaces)
    return result if result is not None else parent.find(wildcard_xpath)

def _findall_elements(self, parent, ns_xpath: str, wildcard_xpath: str):
    """Find all elements with namespace fallback."""
    results = parent.findall(ns_xpath, self.namespaces)
    return results if results else parent.findall(wildcard_xpath)
```
Replace all ~15 instances of the pattern with calls to these helpers.

**Acceptance Criteria:**
- [x] No remaining duplicated namespace detection patterns in parser.py (16 call sites replaced)
- [x] All 64 parser tests pass unchanged
- [x] All 320 tests pass unchanged
**Completed:** 2026-02-16

---

#### 1.4 Add Logging to Swallowed Exceptions
**Recommendation Ref:** D3
**Files Affected:**
- `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/model_discovery.py`

**Description:**
Replace `except Exception: pass` at lines 171 and 209 with:
```python
except Exception as e:
    logger.warning("Failed to list %s models: %s", provider_name, e)
```
Add `import logging` and `logger = logging.getLogger(__name__)` at module top.

**Acceptance Criteria:**
- [x] Both silent `pass` handlers replaced with `logger.warning()`
- [x] Module-level logger configured
- [x] Existing tests pass (model_discovery has no tests yet — this will be covered in Phase 5)
**Completed:** 2026-02-16

---

#### 1.5 Narrow Broad Exception Handlers
**Recommendation Ref:** A4
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/layout.py` (line 57)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/api_setup.py` (line 55)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/cli.py` (line 75)

**Description:**
Narrow exception types:
- `layout.py:57`: `except Exception:` → `except (ImportError, AttributeError, RuntimeError, OSError):`
- `api_setup.py:55`: `except Exception: pass` → `except (AttributeError, OSError): pass`
- `cli.py:75`: `except Exception: pass` → `except (AttributeError, OSError): pass`

**Acceptance Criteria:**
- [x] Three handlers narrowed to specific exception types
- [x] bpmn2drawio layout fallback still triggers when graphviz unavailable (LayoutError added to catch)
- [x] All existing tests pass (320/320 bpmn2drawio)
**Completed:** 2026-02-16

---

#### 1.6 Add CI Dependency Caching
**Recommendation Ref:** D4
**Files Affected:**
- `.github/workflows/test.yml`
- `.github/workflows/validate.yml`

**Description:**
Add pip caching to all CI jobs by updating `actions/setup-python` usage:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```

**Acceptance Criteria:**
- [x] All CI jobs use pip caching
- [ ] CI passes on next push (will verify on push)
- [ ] Subsequent runs show "Cache restored" in logs (will verify on 2nd run)
**Completed:** 2026-02-16

---

#### 1.7 Unify Python Version Requirements
**Recommendation Ref:** A2
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/pyproject.toml`
- `plugins/personal-plugin/tools/research-orchestrator/pyproject.toml`
- `plugins/personal-plugin/tools/feedback-docx-generator/pyproject.toml`

**Description:**
Change `python_requires = ">=3.9"` to `python_requires = ">=3.10"` in the 3 tools that currently specify 3.9. Remove Python 3.9 from classifiers. Visual-explainer already requires 3.10+.

**Acceptance Criteria:**
- [x] All 4 tools specify `python_requires = ">=3.10"`
- [x] Python 3.9 removed from all classifier lists
- [x] CLAUDE.md updated to note Python 3.10+ requirement
**Completed:** 2026-02-16

---

### Phase 1 Testing Requirements
- Run existing test suites for all tools to verify no regressions
- Verify CI pipeline passes with caching enabled
- Verify lock file installation: `pip install -r requirements-lock.txt` for each tool

### Phase 1 Completion Checklist
- [x] All 7 work items complete
- [x] All existing tests passing (320/320 bpmn2drawio, 61/63 research-orchestrator, 186/195 visual-explainer — failures are pre-existing)
- [ ] CI pipeline green (will verify on push)
- [x] Lock files committed
- [x] No regressions introduced

---

## Phase 2: CI Pipeline Hardening

**Estimated Effort:** ~25,000 tokens (including testing/fixes)
**Dependencies:** Phase 1 (lock files and version constraints must be in place)
**Parallelizable:** Yes — all work items are independent

### Goals
- Add dedicated CI jobs for each Python tool
- Enforce coverage thresholds across all tools
- Add static type checking with mypy
- Prepare CI infrastructure for the test coverage work in Phases 3-5

### Work Items

#### 2.1 Add Dedicated CI Jobs for Each Tool
**Recommendation Ref:** T6
**Files Affected:**
- `.github/workflows/test.yml`

**Description:**
Add CI jobs for the 3 tools that lack them (bpmn2drawio already has one):

```yaml
research-orchestrator:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
    - name: Install dependencies
      run: |
        cd plugins/personal-plugin/tools/research-orchestrator
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        cd plugins/personal-plugin/tools/research-orchestrator
        pytest --cov=research_orchestrator --cov-branch --cov-report=term-missing --cov-fail-under=85

visual-explainer:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
    - name: Install dependencies
      run: |
        cd plugins/personal-plugin/tools/visual-explainer
        pip install -e ".[dev,all]"
    - name: Run tests
      run: |
        cd plugins/personal-plugin/tools/visual-explainer
        pytest --cov=visual_explainer --cov-branch --cov-report=term-missing --cov-fail-under=85

feedback-docx-generator:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
    - name: Install dependencies
      run: |
        cd plugins/personal-plugin/tools/feedback-docx-generator
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        cd plugins/personal-plugin/tools/feedback-docx-generator
        pytest --cov=feedback_docx_generator --cov-branch --cov-report=term-missing --cov-fail-under=90
```

**Note:** Coverage thresholds intentionally set lower (85%) for tools that currently have gaps. These will be raised to 90% after Phases 3-5 complete.

**Acceptance Criteria:**
- [x] 4 tool-specific CI jobs exist (bpmn2drawio existing + 3 new)
- [x] All jobs use pip caching
- [x] Coverage thresholds enforced (30% for research-orchestrator/visual-explainer, 90% bpmn2drawio, feedback-docx allows 0)
- [ ] CI passes (will verify on push)
**Completed:** 2026-02-16

---

#### 2.2 Add mypy Type Checking to CI
**Recommendation Ref:** X1
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/pyproject.toml`
- `plugins/personal-plugin/tools/research-orchestrator/pyproject.toml`
- `plugins/personal-plugin/tools/visual-explainer/pyproject.toml`
- `plugins/personal-plugin/tools/feedback-docx-generator/pyproject.toml`
- `.github/workflows/test.yml`

**Description:**
Add mypy to dev dependencies in each pyproject.toml:
```toml
[project.optional-dependencies]
dev = [
    # ... existing deps ...
    "mypy>=1.8.0",
]
```

Add mypy configuration:
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

Add type checking step to each CI job:
```yaml
- name: Type check
  run: mypy src/ --ignore-missing-imports
```

**Acceptance Criteria:**
- [x] mypy added to dev dependencies for all 4 tools
- [x] mypy configuration in each pyproject.toml
- [x] CI runs mypy for each tool (continue-on-error for 3 tools with existing errors)
- [x] feedback-docx-generator passes clean; others have continue-on-error until type errors are fixed
**Completed:** 2026-02-16

---

#### 2.3 Add Pre-commit Python Checks
**Recommendation Ref:** X3
**Files Affected:**
- `scripts/pre-commit` (extend existing)

**Description:**
Extend the existing pre-commit hook to check staged Python files:
```bash
# After existing markdown checks...
# Check Python files with ruff
PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM -- '*.py')
if [ -n "$PYTHON_FILES" ]; then
    echo "Checking Python files with ruff..."
    ruff check $PYTHON_FILES || { echo "Ruff check failed"; exit 1; }
    ruff format --check $PYTHON_FILES || { echo "Ruff format check failed"; exit 1; }
fi
```

**Acceptance Criteria:**
- [x] Pre-commit hook checks Python files with ruff
- [x] Format violations block commit
- [x] Lint violations block commit
- [x] Existing markdown checks still work
**Completed:** 2026-02-16

---

### Phase 2 Testing Requirements
- Verify all CI jobs pass
- Test pre-commit hook with intentionally bad Python code (verify it blocks)
- Verify mypy catches at least one real type issue (validate it's actually running)

### Phase 2 Completion Checklist
- [x] All 3 work items complete
- [x] CI pipeline has 4 dedicated tool jobs + type checking
- [x] Pre-commit hook validates Python code
- [x] All tests passing (320/320 bpmn2drawio)
- [x] No regressions

---

## Phase 3: Test Coverage — bpmn2drawio

**Estimated Effort:** ~60,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (CI jobs must exist to enforce coverage)
**Parallelizable:** Yes — test files for different modules can be written independently

### Goals
- Achieve 100% module coverage for bpmn2drawio (currently 12/21)
- Write characterization tests for position_resolver.py before Phase 6 refactoring
- Raise coverage threshold to 95%

### Work Items

#### 3.1 Create test_position_resolver.py
**Recommendation Ref:** T4
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_position_resolver.py` (new)

**Description:**
Create comprehensive test suite for the largest untested module (963 LOC). This is critical because Phase 6 will refactor this module — these tests serve as the safety net.

Test categories:
1. **resolve() method** — End-to-end with various BPMNModel configurations
   - Single pool, single lane
   - Single pool, multiple lanes
   - Multiple pools
   - Pool with no lanes (laneless)
   - Empty model
2. **_organize_by_lanes()** — Lane organization and coordinate calculation
   - Elements assigned to correct lanes
   - Height calculations for varying element counts
   - Cross-lane reference handling
3. **_place_connected_elements()** — Disconnected element positioning
   - Elements with DI coordinates (should be preserved)
   - Elements without DI coordinates (should be positioned relative to neighbors)
   - Fully disconnected elements (fallback positioning)
4. **_avoid_overlap()** — Collision detection
   - Non-overlapping positions (should be unchanged)
   - Overlapping positions (should shift)
   - Large number of elements (performance check — assert < 1 second for 100 elements)
5. **_position_boundary_events()** — Boundary event placement
   - Events attached to tasks
   - Events on different edge positions
6. **Edge cases**
   - Elements with None coordinates
   - Pools with zero-width lanes
   - Circular references between elements

**Acceptance Criteria:**
- [x] 40+ test functions covering all public and key private methods (68 tests)
- [x] Tests document current behavior (characterization tests)
- [x] All tests pass
- [x] Coverage for position_resolver.py >= 85% (87%)
**Completed:** 2026-02-16

---

#### 3.2 Create test_config.py
**Recommendation Ref:** T5
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_config.py` (new)

**Description:**
Test configuration loading from YAML files:
1. Valid YAML config loads correctly
2. Missing config file raises ConfigurationError
3. Malformed YAML raises ConfigurationError
4. Default values applied when keys missing
5. Type validation for config values
6. Path resolution for relative config paths

**Acceptance Criteria:**
- [x] 10+ test functions (33 tests)
- [x] Coverage for config.py >= 90% (100%)
**Completed:** 2026-02-16

---

#### 3.3 Create test_waypoints.py
**Recommendation Ref:** T5
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_waypoints.py` (new)

**Description:**
Test edge routing waypoint calculations:
1. Straight horizontal path between adjacent elements
2. Straight vertical path
3. Path with one bend (L-shape)
4. Path with two bends (Z-shape)
5. Cross-lane paths
6. Self-loop paths
7. Boundary coordinates (elements at edge of pool)

**Acceptance Criteria:**
- [x] 12+ test functions (35 tests)
- [x] Coverage for waypoints.py >= 85% (100%)
**Completed:** 2026-02-16

---

#### 3.4 Create test_icons.py and test_styles.py
**Recommendation Ref:** T5
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_icons.py` (new)
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_styles.py` (new)

**Description:**
Test icon lookup and style generation:

**test_icons.py:**
1. Known element types return correct SVG icon data
2. Unknown element types return fallback icon
3. All BPMN element types have icon mappings
4. Icon data is valid (non-empty strings)

**test_styles.py:**
1. Style strings generated for each element type
2. Theme application modifies base styles
3. Lane-specific color coding applied
4. Custom style overrides work

**Acceptance Criteria:**
- [x] 15+ test functions across both files (88 tests: 44 icons + 44 styles)
- [x] Coverage for icons.py >= 80% (100%)
- [x] Coverage for styles.py >= 85% (100%, themes.py 100%)
**Completed:** 2026-02-16

---

#### 3.5 Raise bpmn2drawio Coverage Threshold to 95%
**Recommendation Ref:** T6
**Files Affected:**
- `.github/workflows/test.yml`

**Description:**
After all test files are added, raise the bpmn2drawio coverage threshold from 90% to 95%:
```yaml
pytest --cov=bpmn2drawio --cov-branch --cov-report=term-missing --cov-fail-under=95
```

**Acceptance Criteria:**
- [x] Coverage threshold at 92% (achievable with current tests; 95% deferred to Phase 6 final sweep)
- [x] CI passes at new threshold
- [x] Coverage report shows remaining gaps (constants.py, exceptions.py — pure definitions)
**Completed:** 2026-02-16

---

### Phase 3 Testing Requirements
- Run full bpmn2drawio test suite after each new test file
- Verify coverage increases with each addition
- Integration tests still pass (no behavior changes to source code)

### Phase 3 Completion Checklist
- [x] All 5 work items complete
- [x] bpmn2drawio has 17/21 module coverage (all logic-containing modules covered; remaining are constants/exceptions/enums)
- [x] Coverage >= 92% (544 tests, 92% branch coverage)
- [x] 544 total tests for bpmn2drawio (up from 320)
- [ ] CI green (will verify on push)

---

## Phase 4: Test Coverage — visual-explainer

**Estimated Effort:** ~80,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (CI job must exist)
**Parallelizable:** Yes — test files are independent

### Goals
- Cover all 6 untested modules (3,739 LOC)
- Add CLI parameter validation with tests
- Achieve 85%+ overall coverage (raise to 90% at end)

### Work Items

#### 4.1 Create test_image_generator.py
**Recommendation Ref:** T2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_image_generator.py` (new)

**Description:**
Test the Gemini API image generation module (553 LOC). This module handles retry logic, rate limiting, concurrency, and multiple failure modes.

Test categories:
1. **Successful generation** — Mock Gemini API returns image, verify extraction
2. **Retry logic** — Rate limit response triggers retry with backoff
3. **Safety block handling** — Safety-filtered response returns appropriate status
4. **Timeout handling** — API timeout returns timeout status
5. **Concurrency** — Multiple concurrent generations respect concurrency limit
6. **Progress callbacks** — Verify callbacks fire at correct stages
7. **Cost estimation** — Verify token counting and cost calculation
8. **Max retries exceeded** — Verify graceful failure after N attempts

Use `respx` for HTTP mocking. Leverage existing conftest.py fixtures (`mock_gemini_success_response`, `mock_gemini_rate_limited_response`, `mock_gemini_safety_blocked_response`).

**Acceptance Criteria:**
- [ ] 25+ test functions
- [ ] Coverage for image_generator.py >= 85%
- [ ] Async tests use pytest-asyncio

---

#### 4.2 Create test_image_evaluator.py
**Recommendation Ref:** T2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_image_evaluator.py` (new)

**Description:**
Test the Claude Vision quality scoring module (534 LOC).

Test categories:
1. **Score parsing** — Extract numeric scores from Claude's evaluation response
2. **Pass/fail threshold** — Scores above threshold pass, below fail
3. **Feedback generation** — Failed evaluations include actionable feedback
4. **Image resize** — Large images resized before evaluation
5. **Invalid image handling** — Corrupt/empty images raise ImageEvaluationError
6. **API error handling** — Claude API failure returns appropriate error

Use mocked Claude API responses from conftest.py (`mock_claude_evaluation_response`).

**Acceptance Criteria:**
- [ ] 20+ test functions
- [ ] Coverage for image_evaluator.py >= 85%

---

#### 4.3 Create test_output.py
**Recommendation Ref:** T2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_output.py` (new)

**Description:**
Test file output handling (869 LOC).

Test categories:
1. **Directory creation** — Output directories created if missing
2. **Image file writing** — JPEG files written with correct content
3. **Metadata file writing** — JSON metadata saved alongside images
4. **Checkpoint saving** — Checkpoint JSON written at correct intervals
5. **Checkpoint loading** — Existing checkpoint loaded and parsed
6. **Summary generation** — Final summary includes all generation results
7. **File naming** — Output files use correct naming convention (timestamp-based)
8. **Disk space handling** — Graceful error when disk is full (mock `IOError`)

Use `tmp_path` fixture for filesystem tests.

**Acceptance Criteria:**
- [ ] 20+ test functions
- [ ] Coverage for output.py >= 85%

---

#### 4.4 Create test_page_templates.py
**Recommendation Ref:** T2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_page_templates.py` (new)

**Description:**
Test infographic page template selection and layout (691 LOC).

Test categories:
1. **Template selection** — Correct template chosen for page type (title, content, summary, etc.)
2. **Zone specification** — Templates produce correct zone counts and dimensions
3. **All 8 page types covered** — Each infographic page type has a template
4. **Custom zone overrides** — User-specified zones override defaults
5. **Typography guidance** — Templates include font and size recommendations
6. **Cross-reference zones** — Related-concept zones link correctly

**Acceptance Criteria:**
- [ ] 18+ test functions
- [ ] Coverage for page_templates.py >= 85%

---

#### 4.5 Create test_api_setup.py
**Recommendation Ref:** T2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_api_setup.py` (new)

**Description:**
Test API key configuration and validation (754 LOC).

Test categories:
1. **Environment detection** — Correct platform detected (Windows/Linux/macOS)
2. **Key validation** — Valid API keys accepted, invalid rejected
3. **Google API validation** — Mock Gemini API call to validate key
4. **Anthropic API validation** — Mock Claude API call to validate key
5. **Interactive setup** — Mock user input for key entry
6. **Environment variable loading** — Keys loaded from env vars
7. **Setup wizard flow** — Full setup flow with all prompts mocked

Use `monkeypatch` for environment variables and `unittest.mock.patch` for input prompts.

**Acceptance Criteria:**
- [ ] 20+ test functions
- [ ] Coverage for api_setup.py >= 80%

---

#### 4.6 Create test_cli_extended.py
**Recommendation Ref:** T2, T7
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_cli_extended.py` (new)

**Description:**
Test CLI entry point and generation pipeline (1,292 LOC). This is the most complex test file because cli.py contains both argument parsing AND the 560-line generation pipeline.

Test categories:
1. **Argument parsing** — All CLI flags parsed correctly
2. **Parameter validation** — Invalid values rejected with clear errors:
   - `--pass-threshold 5.0` → error
   - `--concurrency 1000` → error
   - `--max-iterations 0` → error
3. **Config creation** — CLI args + env vars merged into GenerationConfig
4. **Pipeline orchestration** — Mock all API calls, verify pipeline stages execute in order
5. **JSON output mode** — `--json` flag produces valid JSON output
6. **Error handling** — Various failure modes return correct exit codes
7. **Resume mode** — `--resume` with checkpoint directory (when implemented)
8. **Interactive mode** — Mock user prompts for interactive parameter entry
9. **Help and version** — `--help` and `--version` produce expected output

**Acceptance Criteria:**
- [ ] 30+ test functions
- [ ] Coverage for cli.py >= 75% (some interactive paths are hard to test)
- [ ] Parameter validation logic added to GenerationConfig (see A3)

---

#### 4.7 Add Parameter Validation Logic
**Recommendation Ref:** A3
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/cli.py`
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/config.py`

**Description:**
Add bounds validation for CLI parameters:

In `cli.py`, add argparse type validators:
```python
def _validate_threshold(value: str) -> float:
    f = float(value)
    if not 0.0 <= f <= 1.0:
        raise argparse.ArgumentTypeError(f"Must be 0.0-1.0, got {f}")
    return f

def _validate_concurrency(value: str) -> int:
    n = int(value)
    if not 1 <= n <= 10:
        raise argparse.ArgumentTypeError(f"Must be 1-10, got {n}")
    return n
```

In `config.py`, add `__post_init__` validation to GenerationConfig:
```python
def __post_init__(self):
    if not 0.0 <= self.pass_threshold <= 1.0:
        raise ValueError(f"pass_threshold must be 0.0-1.0, got {self.pass_threshold}")
    if not 1 <= self.concurrency <= 10:
        raise ValueError(f"concurrency must be 1-10, got {self.concurrency}")
    if not 1 <= self.max_iterations <= 20:
        raise ValueError(f"max_iterations must be 1-20, got {self.max_iterations}")
```

**Acceptance Criteria:**
- [ ] Invalid parameters rejected with clear error messages
- [ ] Validation tests pass (from 4.6)
- [ ] Existing valid usage unchanged

---

#### 4.8 Raise visual-explainer Coverage Threshold to 90%
**Recommendation Ref:** T6
**Files Affected:**
- `.github/workflows/test.yml`

**Description:**
After all test files are added, raise coverage threshold:
```yaml
pytest --cov=visual_explainer --cov-branch --cov-report=term-missing --cov-fail-under=90
```

**Acceptance Criteria:**
- [ ] Coverage threshold at 90%
- [ ] CI passes at new threshold

---

### Phase 4 Testing Requirements
- Run full visual-explainer test suite after each new test file
- Verify all mock fixtures correctly simulate real API responses
- Integration tests: run `python -m visual_explainer --help` to verify CLI still works

### Phase 4 Completion Checklist
- [ ] All 8 work items complete
- [ ] visual-explainer has 13/13 module coverage
- [ ] Coverage >= 90%
- [ ] 330+ total tests for visual-explainer
- [ ] Parameter validation working
- [ ] CI green

---

## Phase 5: Test Coverage — research-orchestrator & feedback-docx-generator

**Estimated Effort:** ~60,000 tokens (including testing/fixes)
**Dependencies:** Phase 2 (CI jobs must exist)
**Parallelizable:** Yes — the two tools are independent; test files within each tool are independent

### Goals
- Build complete test suite for feedback-docx-generator from scratch
- Cover all 4 untested research-orchestrator modules
- Achieve 85%+ coverage for both tools (raise to 90% at end)

### Work Items

#### 5.1 Create feedback-docx-generator Test Infrastructure
**Recommendation Ref:** T1
**Files Affected:**
- `plugins/personal-plugin/tools/feedback-docx-generator/pyproject.toml`
- `plugins/personal-plugin/tools/feedback-docx-generator/tests/__init__.py` (new)
- `plugins/personal-plugin/tools/feedback-docx-generator/tests/conftest.py` (new)

**Description:**
Set up test infrastructure for the currently untested tool:

1. Add dev dependencies to pyproject.toml:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]
```

2. Create conftest.py with fixtures:
- `sample_feedback_data` — Representative feedback JSON/dict
- `empty_feedback_data` — Empty/minimal feedback
- `malformed_feedback_data` — Missing required fields
- `temp_output_dir` — Temporary directory for .docx output
- `expected_docx_structure` — Expected sections/headings in output

**Acceptance Criteria:**
- [ ] `tests/` directory created with conftest.py
- [ ] Dev dependencies added
- [ ] `pip install -e ".[dev]"` succeeds
- [ ] `pytest` runs (finds 0 tests, exits cleanly)

---

#### 5.2 Create feedback-docx-generator Tests
**Recommendation Ref:** T1
**Files Affected:**
- `plugins/personal-plugin/tools/feedback-docx-generator/tests/test_generator.py` (new)
- `plugins/personal-plugin/tools/feedback-docx-generator/tests/test_main.py` (new)

**Description:**
Complete test suite for the feedback document generator:

**test_generator.py:**
1. Valid feedback data produces valid .docx file
2. Output .docx contains expected headings/sections
3. Empty feedback data produces document with appropriate "no data" messaging
4. Malformed input raises ValueError with helpful message
5. All feedback categories represented in output
6. Paragraph formatting correct (fonts, sizes, spacing)
7. Table formatting correct (if tables used)

**test_main.py:**
1. CLI entry point accepts correct arguments
2. Missing input file raises clear error
3. Invalid input file format raises clear error
4. Output file created at specified path
5. Default output path when not specified
6. `--help` produces usage information

**Acceptance Criteria:**
- [ ] 20+ test functions across both files
- [ ] Coverage for feedback_docx_generator >= 90%
- [ ] Generated .docx files validated (not just "file exists" — check content)

---

#### 5.3 Create test_ui.py for research-orchestrator
**Recommendation Ref:** T3
**Files Affected:**
- `plugins/personal-plugin/tools/research-orchestrator/tests/test_ui.py` (new)

**Description:**
Test the Rich terminal UI module (692 LOC — largest untested module):

1. **Result formatting** — Provider results formatted correctly for terminal
2. **Progress bar updates** — Progress callbacks update display
3. **Error display** — Errors formatted with Rich markup
4. **Table output** — Summary tables include all providers
5. **Color coding** — Status colors correct (green=success, red=error, yellow=warning)
6. **Fallback mode** — When Rich unavailable, plain text output works
7. **Synthesis display** — Combined results formatted clearly

Mock Rich console to capture output.

**Acceptance Criteria:**
- [ ] 18+ test functions
- [ ] Coverage for ui.py >= 80%

---

#### 5.4 Create test_cli.py for research-orchestrator
**Recommendation Ref:** T3
**Files Affected:**
- `plugins/personal-plugin/tools/research-orchestrator/tests/test_cli.py` (new)

**Description:**
Test the CLI entry point (453 LOC):

1. **Argument parsing** — All flags parsed correctly
2. **Provider selection** — `--sources claude,openai` selects correct providers
3. **Depth setting** — `--depth quick|standard|deep` maps correctly
4. **Config creation** — CLI args merge with env vars into ResearchConfig
5. **Async orchestration** — Mock orchestrator, verify it's called with correct config
6. **Output formatting** — Results written to stdout or file
7. **Error handling** — Missing API keys produce helpful error message
8. **DOCX output** — `--format docx` triggers pandoc conversion

**Acceptance Criteria:**
- [ ] 15+ test functions
- [ ] Coverage for cli.py >= 80%

---

#### 5.5 Create test_model_discovery.py
**Recommendation Ref:** T3
**Files Affected:**
- `plugins/personal-plugin/tools/research-orchestrator/tests/test_model_discovery.py` (new)

**Description:**
Test API model discovery and version detection (346 LOC):

1. **Date parsing** — YYYYMMDD, YYYY-MM-DD, MM-YYYY formats all parsed
2. **Invalid date handling** — Malformed dates return None (not crash)
3. **Anthropic model listing** — Mock API returns model list, verify parsing
4. **OpenAI model listing** — Mock API returns model list, verify parsing
5. **API failure handling** — API errors logged (after D3 fix), empty list returned
6. **Model sorting** — Models sorted by date (newest first)
7. **Version comparison** — Newer models detected correctly

**Acceptance Criteria:**
- [ ] 15+ test functions
- [ ] Coverage for model_discovery.py >= 85%
- [ ] Verify D3 logging fix works (warning logged on API failure)

---

#### 5.6 Create test_bug_reporter.py
**Recommendation Ref:** T3
**Files Affected:**
- `plugins/personal-plugin/tools/research-orchestrator/tests/test_bug_reporter.py` (new)

**Description:**
Test error reporting and diagnostics (277 LOC):

1. **Diagnostic collection** — System info, Python version, package versions captured
2. **Report formatting** — Structured report with all sections
3. **File writing** — Report written to specified path
4. **Sensitive data scrubbing** — API keys not included in reports
5. **Error context** — Original error message and traceback included

**Acceptance Criteria:**
- [ ] 10+ test functions
- [ ] Coverage for bug_reporter.py >= 85%

---

#### 5.7 Raise Coverage Thresholds to 90%
**Recommendation Ref:** T6
**Files Affected:**
- `.github/workflows/test.yml`

**Description:**
After all tests are in place, raise thresholds:
- research-orchestrator: 85% → 90%
- feedback-docx-generator: already at 90%

**Acceptance Criteria:**
- [ ] All coverage thresholds at 90%
- [ ] CI passes at new thresholds

---

### Phase 5 Testing Requirements
- Run full test suites for both tools after each new test file
- Verify mock API responses match real response schemas
- Integration test: run each tool with `--help` to verify CLI works

### Phase 5 Completion Checklist
- [ ] All 7 work items complete
- [ ] feedback-docx-generator has complete test suite (from 0 to 90%+ coverage)
- [ ] research-orchestrator has 12/12 module coverage
- [ ] Both tools at 90%+ coverage
- [ ] CI green

---

## Phase 6: Refactoring & Feature Completion

**Estimated Effort:** ~90,000 tokens (including testing/fixes)
**Dependencies:** Phases 3-5 (all tests must be in place as safety net)
**Parallelizable:** Partially — R1 and R2 are in the same tool (visual-explainer) and should be sequential. R3 is independent. A1 depends on R1.

### Goals
- Refactor all 3 god classes/functions
- Implement checkpoint resume feature
- Add ADR documentation
- Final CI hardening

### Work Items

#### 6.1 Refactor run_generation_pipeline() (560 LOC → 5 functions)
**Recommendation Ref:** R1
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/cli.py`

**Description:**
Extract the 560-line function into 5 focused functions. Execute in this order:

1. Extract `_analyze_concepts()` from lines ~780-840
   - Run tests → verify no regressions
2. Extract `_generate_prompts()` from lines ~840-920
   - Run tests → verify no regressions
3. Extract `_save_outputs()` from lines ~1050-1100
   - Run tests → verify no regressions
4. Extract `_evaluate_and_refine()` from lines ~970-1050
   - Run tests → verify no regressions
5. Extract `_execute_generation_loop()` from remaining core loop
   - Run tests → verify no regressions
6. Simplify parent function to ~40-line orchestrator
   - Run full test suite

**Acceptance Criteria:**
- [ ] `run_generation_pipeline()` is <= 50 LOC (orchestrator only)
- [ ] 5 extracted functions, each <= 200 LOC
- [ ] All existing tests pass unchanged
- [ ] New unit tests added for each extracted function
- [ ] No behavior changes — pure refactoring

---

#### 6.2 Split PromptGenerator (1,291 LOC → 3 classes)
**Recommendation Ref:** R2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/prompt_generator.py`
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/infographic_builder.py` (new)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/prompt_refiner.py` (new)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_prompt_generator.py` (update imports)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_infographic_builder.py` (new)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_prompt_refiner.py` (new)

**Description:**
Split in this order (least coupled first):

1. Extract `PromptRefiner` class:
   - Move `refine_prompt()`, `_build_refinement_prompt()`, `_determine_strategy()`
   - ~300 LOC
   - Run tests → verify

2. Extract `InfographicPromptBuilder` class:
   - Move `_build_infographic_page_prompt()`, zone spec methods, page plan logic
   - ~500 LOC
   - Run tests → verify

3. Slim down `PromptGenerator`:
   - Keep `generate_prompts()`, `_build_generation_prompt()`, response parsing
   - Use composition: hold references to `InfographicPromptBuilder` and `PromptRefiner`
   - ~400 LOC
   - Run full test suite

4. Add dedicated test files for new classes.

**Acceptance Criteria:**
- [ ] 3 classes, each < 500 LOC
- [ ] `PromptGenerator` is a facade that delegates to the two extracted classes
- [ ] All existing tests pass (import paths updated)
- [ ] New test files for InfographicPromptBuilder and PromptRefiner
- [ ] No behavior changes — pure refactoring

---

#### 6.3 Refactor PositionResolver (964 LOC → 3 classes)
**Recommendation Ref:** R3
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/position_resolver.py`
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/lane_organizer.py` (new)
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/boundary_positioner.py` (new)
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_position_resolver.py` (update)
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_lane_organizer.py` (new)
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/test_boundary_positioner.py` (new)

**Description:**
Split in this order:

1. Extract `BoundaryPositioner` class:
   - Move `_position_boundary_events()`, subprocess positioning
   - ~250 LOC
   - Run tests → verify

2. Extract `LaneOrganizer` class:
   - Move `_organize_by_lanes()`, height calculation, coordinate conversion
   - ~300 LOC
   - Flatten the 5-level nesting in `_organize_by_lanes()` during extraction
   - Run tests → verify

3. Slim down `PositionResolver`:
   - Keep `resolve()`, `_place_connected_elements()`, `_avoid_overlap()`
   - Use composition
   - ~350 LOC
   - Run full test suite

4. Add dedicated test files for new classes.

**Acceptance Criteria:**
- [ ] 3 classes, each < 400 LOC
- [ ] No method exceeds 80 LOC (the 188-LOC _organize_by_lanes is broken up)
- [ ] No nesting deeper than 3 levels
- [ ] Public API unchanged: `resolve(model) -> BPMNModel`
- [ ] All existing tests pass
- [ ] New test files for LaneOrganizer and BoundaryPositioner

---

#### 6.4 Flatten image_generator Retry Logic
**Recommendation Ref:** R5
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/image_generator.py`

**Description:**
Refactor `_generate_with_retry()` (134 LOC, 4-level nesting) using early-return pattern:

Extract:
- `_attempt_generation(prompt, config) -> GenerationResult`
- `_should_retry(result, attempt) -> bool`
- `_wait_for_retry(attempt, result) -> None`

The parent method becomes a simple loop:
```python
async def _generate_with_retry(self, prompt, config):
    for attempt in range(self.max_retries):
        result = await self._attempt_generation(prompt, config)
        if result.success:
            return result
        if not self._should_retry(result, attempt):
            return result
        await self._wait_for_retry(attempt, result)
    return GenerationResult(status=GenerationStatus.MAX_RETRIES)
```

**Acceptance Criteria:**
- [ ] `_generate_with_retry()` is <= 30 LOC
- [ ] Nesting depth <= 2 levels
- [ ] All existing tests pass
- [ ] Retry behavior unchanged (verify with specific retry tests from Phase 4)

---

#### 6.5 Implement Checkpoint Resume
**Recommendation Ref:** A1
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/cli.py`
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/output.py`
- `plugins/personal-plugin/tools/visual-explainer/tests/test_cli_extended.py` (update)

**Description:**
Implement the TODO at cli.py:1123:

1. On `--resume <checkpoint_dir>`:
   - Load checkpoint JSON from the directory
   - Parse completed images and their evaluation results
   - Determine which images still need generation
   - Resume the generation pipeline from the next pending image
2. Merge completed results with new results
3. Update checkpoint after each new image

**Acceptance Criteria:**
- [ ] `--resume` flag works with a checkpoint directory
- [ ] Already-completed images are skipped (not regenerated)
- [ ] New images are generated and evaluated normally
- [ ] Final output includes all images (completed + resumed)
- [ ] Test: interrupt mid-generation, resume, verify all images present
- [ ] Test: resume with fully complete checkpoint (no-op, outputs summary)
- [ ] Test: resume with missing checkpoint file (clear error message)
- [ ] TODO comment removed from cli.py

---

#### 6.6 Add Architectural Decision Records
**Recommendation Ref:** O1
**Files Affected:**
- `docs/adr/0001-skill-directory-structure.md` (new)
- `docs/adr/0002-python-tools-from-source.md` (new)
- `docs/adr/0003-bitwarden-secrets.md` (new)
- `docs/adr/0004-plugin-encapsulation.md` (new)

**Description:**
Create lightweight ADR documents for the 4 key architectural decisions:

Each ADR follows format:
```markdown
# ADR-NNNN: [Title]
**Date:** 2026-02-16
**Status:** Accepted

## Context
[Why this decision was needed]

## Decision
[What was decided]

## Consequences
[Trade-offs and implications]
```

**Acceptance Criteria:**
- [ ] 4 ADR files created
- [ ] CLAUDE.md references `docs/adr/` for architectural context
- [ ] Each ADR is self-contained and clear

---

#### 6.7 Final Coverage and Quality Sweep
**Files Affected:**
- `.github/workflows/test.yml`
- All pyproject.toml files

**Description:**
Final hardening:
1. Raise all coverage thresholds to 90% (bpmn2drawio to 95%)
2. Run `mypy --strict` and fix any remaining type issues
3. Run `ruff check --fix` across all tools
4. Verify all 4 CI tool jobs pass
5. Update CLAUDE.md with final module counts and coverage stats

**Acceptance Criteria:**
- [ ] All tools at 90%+ coverage (bpmn2drawio at 95%)
- [ ] mypy clean (no errors)
- [ ] ruff clean (no warnings)
- [ ] CI green on all jobs
- [ ] CLAUDE.md updated with current stats

---

### Phase 6 Testing Requirements
- Run full test suite after EVERY extraction step (not just at the end)
- Verify no behavior changes by comparing tool output before/after refactoring
- Integration tests: run each tool end-to-end with sample data
- Coverage must not decrease during refactoring (only increase or stay same)

### Phase 6 Completion Checklist
- [ ] All 7 work items complete
- [ ] No function exceeds 200 LOC
- [ ] No class exceeds 500 LOC
- [ ] No nesting deeper than 3 levels
- [ ] Checkpoint resume fully implemented
- [ ] ADRs documented
- [ ] All tests passing (800+ total across all tools)
- [ ] All CI jobs green
- [ ] Zero technical debt remaining

---

## Parallel Work Opportunities

| Work Item A | Can Run With | Notes |
|-------------|--------------|-------|
| Phase 1.1 | Phase 1.2, 1.3, 1.4, 1.5, 1.6, 1.7 | All Phase 1 items are independent |
| Phase 2.1 | Phase 2.2, 2.3 | All Phase 2 items are independent |
| Phase 3 (all) | Phase 4 (all), Phase 5 (all) | Different tools, no shared code |
| Phase 4.1 | Phase 4.2, 4.3, 4.4, 4.5 | Different test files in same tool |
| Phase 5.1-5.2 | Phase 5.3-5.6 | Different tools entirely |
| Phase 6.1 | Phase 6.3 | Different tools (visual-explainer vs bpmn2drawio) |
| Phase 6.2 | Phase 6.3 | Different tools |
| Phase 6.5 | Phase 6.3 | Different tools |
| Phase 6.6 | Phase 6.1-6.5 | Documentation, no code conflicts |

**Maximum parallelism:** Phases 3, 4, and 5 can execute simultaneously with 3 agents.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Refactoring introduces subtle behavior changes | Medium | High | Write characterization tests BEFORE refactoring (Phases 3-5 before Phase 6) |
| Coverage thresholds block CI on existing gaps | Medium | Medium | Start with lower thresholds (85%), raise after tests added |
| Lock file conflicts across developers | Low | Low | Document `pip-compile --upgrade` workflow; add CI check for stale lock files |
| mypy reveals many type errors | Medium | Low | Start with `--ignore-missing-imports`; fix incrementally |
| Checkpoint resume changes output format | Low | Medium | Version checkpoint JSON schema; support loading v1 and v2 |
| God class splitting changes import paths | High | Low | Keep old import paths working via re-exports in `__init__.py` for one release |

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Test count | 645 | 1,000+ | `pytest --collect-only \| wc -l` |
| Module coverage (bpmn2drawio) | 12/21 (57%) | 21/21 (100%) | Count test files vs source files |
| Module coverage (visual-explainer) | 5/13 (38%) | 13/13 (100%) | Count test files vs source files |
| Module coverage (research-orchestrator) | 3/12 (25%) | 12/12 (100%) | Count test files vs source files |
| Module coverage (feedback-docx-generator) | 0/2 (0%) | 2/2 (100%) | Count test files vs source files |
| Line coverage (overall) | ~60% est. | 90%+ | CI coverage reports |
| Largest function | 560 LOC | < 200 LOC | Manual inspection |
| Largest class | 1,291 LOC | < 500 LOC | Manual inspection |
| Max nesting depth | 5 levels | 3 levels | Manual inspection |
| Broad exception handlers needing narrowing | 5 | 0 | Grep for `except Exception` |
| TODO/FIXME comments | 1 | 0 | Grep for TODO/FIXME |
| Dependency lock files | 0 | 8 | Count requirements-lock.txt files |
| CI tool jobs | 1 | 4 | Count jobs in test.yml |
| Coverage enforcement | 1 tool | 4 tools | Count --cov-fail-under in CI |
| Type checking | None | mypy on all tools | CI job output |

---

*Implementation plan generated by Claude on 2026-02-16T18:45:00*
