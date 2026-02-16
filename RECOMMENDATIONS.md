# Improvement Recommendations

**Generated:** 2026-02-16T18:45:00
**Analyzed Project:** claude-marketplace (davistroy/claude-marketplace)
**Analysis Scope:** Full repository — 2 plugins, 25 commands, 11 skills, 4 Python tools (~70K LOC)

---

## Executive Summary

The claude-marketplace repository is architecturally sound with excellent plugin structure, strong command/skill patterns, and proper secrets management. The primary technical debt concentrates in three areas: **test coverage gaps** (feedback-docx-generator has zero tests, visual-explainer and research-orchestrator have large untested modules), **code complexity hotspots** (god classes in position_resolver.py and prompt_generator.py, a 560-line function in visual-explainer's CLI), and **dependency management** (all floating versions with no lock files, one dangerously loose constraint).

The path to zero technical debt requires 37 targeted actions across 6 phases. The highest-value work is closing test coverage gaps (currently ~645 tests but missing coverage on ~6,500 lines of source code), refactoring the 3 complexity hotspots, and tightening the dependency and CI pipeline. None of the issues are production-breaking — this is debt reduction, not emergency triage.

---

## Recommendation Categories

### Category 1: Test Coverage & Quality (T)

#### T1. Add Complete Test Suite for feedback-docx-generator

**Priority:** Critical
**Effort:** M
**Impact:** Eliminates the only tool with zero test coverage; prevents regressions in .docx generation

**Current State:**
The feedback-docx-generator tool (`plugins/personal-plugin/tools/feedback-docx-generator/`) has 2 source modules (~270 lines) and absolutely no tests — no `tests/` directory, no conftest.py, no CI job.

**Recommendation:**
Create a full test suite covering:
- `__init__.py` module functions (69 lines)
- `__main__.py` CLI entry point and document generation (~200 lines)
- Edge cases: empty input, malformed data, missing python-docx dependency
- Integration test generating an actual .docx file and validating structure

**Implementation Notes:**
- Add `tests/` directory with conftest.py providing sample feedback data fixtures
- Add pytest + python-docx to dev dependencies in pyproject.toml
- Add dedicated CI job in `.github/workflows/test.yml` with 90% coverage threshold
- Pattern after visual-explainer's conftest.py for fixture design

---

#### T2. Add Tests for visual-explainer Untested Modules (3,739 LOC)

**Priority:** Critical
**Effort:** L
**Impact:** Covers 6 large untested modules that contain the tool's core generation pipeline

**Current State:**
6 modules totaling 3,739 lines have zero test coverage:
- `cli.py` (1,292 lines) — main entry point, generation pipeline
- `output.py` (869 lines) — file output handling
- `api_setup.py` (754 lines) — API key configuration
- `page_templates.py` (691 lines) — infographic page layouts
- `image_evaluator.py` (534 lines) — Claude Vision quality scoring
- `image_generator.py` (553 lines) — Gemini API image generation

**Recommendation:**
Add test files for each untested module:
- `test_cli.py` — CLI argument parsing, config creation, pipeline orchestration (mock API calls)
- `test_output.py` — File writing, directory creation, checkpoint saving/loading
- `test_api_setup.py` — Key validation, interactive prompts, environment detection
- `test_page_templates.py` — Template selection, zone specifications, layout validation
- `test_image_evaluator.py` — Score parsing, threshold checking, feedback generation
- `test_image_generator.py` — Retry logic, rate limiting, error handling, concurrency

**Implementation Notes:**
- The existing conftest.py already provides 60+ fixtures including mock API responses — leverage these
- Use `respx` for HTTP mocking (already in dev dependencies)
- Focus on unit tests with mocked API calls; integration tests can use recorded responses
- Target 90% coverage per module

---

#### T3. Add Tests for research-orchestrator Untested Modules (1,768 LOC)

**Priority:** Critical
**Effort:** M
**Impact:** Covers 4 untested modules including the largest module (ui.py, 692 lines)

**Current State:**
4 modules totaling 1,768 lines have zero test coverage:
- `ui.py` (692 lines) — Rich terminal UI, progress bars, result formatting
- `cli.py` (453 lines) — CLI entry point, argument parsing, orchestration
- `model_discovery.py` (346 lines) — API model listing, date parsing, version detection
- `bug_reporter.py` (277 lines) — Error reporting, diagnostic collection

**Recommendation:**
Add test files for each untested module:
- `test_ui.py` — Output formatting, progress callbacks, result rendering (mock Rich console)
- `test_cli.py` — Argument parsing, config creation, async orchestration entry
- `test_model_discovery.py` — API model listing, date format parsing, error handling
- `test_bug_reporter.py` — Diagnostic collection, report formatting, file writing

**Implementation Notes:**
- Mock Rich console output for UI tests
- Use `unittest.mock.AsyncMock` for async orchestrator calls in CLI tests
- model_discovery.py has 2 silent `except Exception: pass` handlers (lines 171, 209) — tests should verify these paths log warnings after the fix in D3

---

#### T4. Add Tests for bpmn2drawio position_resolver.py (963 LOC)

**Priority:** High
**Effort:** M
**Impact:** Covers the single largest untested module in the most-tested tool

**Current State:**
`position_resolver.py` is 963 lines with 13 methods and is the largest untested module in bpmn2drawio. The tool has 320 tests covering 12/21 modules, but this critical layout module has no dedicated tests. Some coverage may exist indirectly through integration tests.

**Recommendation:**
Create `test_position_resolver.py` covering:
- `resolve()` method with various pool/lane configurations
- `_organize_by_lanes()` with single-lane, multi-lane, and laneless scenarios
- `_place_connected_elements()` with disconnected and connected graph fragments
- `_avoid_overlap()` with overlapping and non-overlapping positions
- `_position_boundary_events()` with elements attached to different edge positions
- Edge cases: empty pools, elements without DI coordinates, cross-pool references

**Implementation Notes:**
- Create test fixtures with minimal BPMNModel instances for each scenario
- Test coordinate math with known expected positions
- Verify O(n^2) overlap avoidance doesn't degrade with large element counts (add performance assertion)

---

#### T5. Add Tests for Remaining bpmn2drawio Untested Modules

**Priority:** Medium
**Effort:** S
**Impact:** Completes 100% module coverage for bpmn2drawio (currently 12/21)

**Current State:**
6 additional modules lack dedicated tests:
- `config.py` (153 lines) — Configuration loading
- `constants.py` (127 lines) — Constant values
- `exceptions.py` (43 lines) — Exception hierarchy
- `icons.py` (298 lines) — SVG icon definitions
- `styles.py` (104 lines) — Draw.io style strings
- `waypoints.py` (149 lines) — Edge routing waypoints

**Recommendation:**
Add test files for modules with logic (skip pure-constant modules):
- `test_config.py` — YAML loading, default values, error handling for malformed configs
- `test_waypoints.py` — Waypoint calculation, edge routing between elements
- `test_icons.py` — Icon lookup by element type, fallback behavior
- `test_styles.py` — Style string generation, theme application
- Skip `constants.py` and `exceptions.py` (pure definitions, no logic to test)

**Implementation Notes:**
- config.py handles YAML parsing — test with valid, invalid, and missing files
- waypoints.py calculates geometric paths — test with known coordinate inputs/outputs

---

#### T6. Enforce Coverage Thresholds in CI for All Tools

**Priority:** High
**Effort:** S
**Impact:** Prevents coverage regression; currently only bpmn2drawio enforces 90%

**Current State:**
- bpmn2drawio: 90% threshold enforced via `--cov-fail-under=90` (CI fails if below)
- research-orchestrator: Coverage reported but NOT enforced
- visual-explainer: Coverage reported but NOT enforced
- feedback-docx-generator: No coverage at all

**Recommendation:**
Add dedicated CI jobs for each tool with coverage enforcement:
```yaml
research-orchestrator:
  runs-on: ubuntu-latest
  steps:
    - pip install -e ".[dev]"
    - pytest --cov=research_orchestrator --cov-fail-under=85

visual-explainer:
  runs-on: ubuntu-latest
  steps:
    - pip install -e ".[dev]"
    - pytest --cov=visual_explainer --cov-fail-under=85

feedback-docx-generator:
  runs-on: ubuntu-latest
  steps:
    - pip install -e ".[dev]"
    - pytest --cov=feedback_docx_generator --cov-fail-under=90
```

**Implementation Notes:**
- Start with 85% threshold for tools currently lacking tests (raise after initial test pass)
- bpmn2drawio keeps its existing 90% threshold
- Add `--cov-branch` for branch coverage on all tools

---

#### T7. Add CLI Parameter Validation Tests

**Priority:** Medium
**Effort:** S
**Impact:** Catches invalid user input before it causes confusing errors downstream

**Current State:**
CLI parameters like `--pass-threshold`, `--concurrency`, and image count accept any value without bounds checking. `--pass-threshold 5.0` or `--concurrency 1000` are accepted silently.

**Recommendation:**
Add validation tests that verify:
- `--pass-threshold` rejects values outside 0.0-1.0
- `--concurrency` rejects values outside 1-10
- `--max-iterations` rejects values outside 1-20
- Image count prompts enforce upper bound (e.g., max 50)
- Invalid combinations are caught (e.g., `--json` with `--interactive`)

**Implementation Notes:**
- Tests should be paired with validation logic in `GenerationConfig.from_cli_and_env()` (see A5)

---

### Category 2: Code Complexity & Refactoring (R)

#### R1. Refactor visual-explainer run_generation_pipeline() (560 LOC)

**Priority:** High
**Effort:** M
**Impact:** Breaks the largest function in the codebase into testable, maintainable units

**Current State:**
`visual_explainer/cli.py` lines 777-1100 contain a single 560-line function that handles concept analysis, prompt generation, image generation loop, quality evaluation, prompt refinement, and output finalization. This function is untestable as a unit and has high cognitive load.

**Recommendation:**
Extract into 5 focused functions:
1. `_analyze_concepts(config, source) -> ConceptAnalysis` (~60 LOC)
2. `_generate_prompts(config, analysis) -> List[Prompt]` (~80 LOC)
3. `_execute_generation_loop(config, prompts, progress) -> List[GenerationResult]` (~200 LOC)
4. `_evaluate_and_refine(config, results) -> List[GenerationResult]` (~120 LOC)
5. `_save_outputs(config, results) -> OutputSummary` (~60 LOC)

The parent `run_generation_pipeline()` becomes a ~40-line orchestrator calling these functions.

**Implementation Notes:**
- Extract one function at a time, running tests after each extraction
- Keep the progress callback threading unchanged (pass progress object to each function)
- The checkpoint/resume logic stays in the orchestrator
- Each extracted function becomes independently testable

---

#### R2. Split PromptGenerator God Class (1,291 LOC, 23 methods)

**Priority:** High
**Effort:** M
**Impact:** Separates 3 distinct responsibilities into focused, testable classes

**Current State:**
`visual_explainer/prompt_generator.py` lines 59-1350 contain a single class handling prompt generation, infographic page prompts, and prompt refinement — three distinct responsibilities with different dependencies and change frequencies.

**Recommendation:**
Split into 3 classes:
1. `PromptGenerator` (core) — `generate_prompts()`, `_build_generation_prompt()`, response parsing (~400 LOC)
2. `InfographicPromptBuilder` — `_build_infographic_page_prompt()`, zone specs, page plan logic (~500 LOC)
3. `PromptRefiner` — `refine_prompt()`, strategy determination, refinement prompt building (~300 LOC)

**Implementation Notes:**
- Use composition: `PromptGenerator` holds references to `InfographicPromptBuilder` and `PromptRefiner`
- External callers continue using `PromptGenerator` as the facade
- Existing tests for `prompt_generator.py` (31 tests) will need import path updates
- Extract in order: Refiner first (least coupled), then InfographicPromptBuilder

---

#### R3. Refactor PositionResolver God Class (964 LOC, 13 methods)

**Priority:** High
**Effort:** M
**Impact:** Makes the most complex layout module testable and maintainable

**Current State:**
`bpmn2drawio/position_resolver.py` is 964 lines with `_organize_by_lanes()` at 188 LOC containing 5 levels of nesting. The class handles position resolution, lane organization, boundary event positioning, subprocess positioning, and overlap avoidance.

**Recommendation:**
Extract into focused modules:
1. `PositionResolver` (core) — `resolve()`, `_place_connected_elements()`, `_avoid_overlap()` (~350 LOC)
2. `LaneOrganizer` — `_organize_by_lanes()`, height calculation, coordinate conversion (~300 LOC)
3. `BoundaryPositioner` — boundary event and subprocess internal positioning (~250 LOC)

**Implementation Notes:**
- `PositionResolver.resolve()` orchestrates the three collaborators
- Must maintain the same public API — `resolve(model: BPMNModel) -> BPMNModel`
- Write tests for T4 BEFORE refactoring (characterization tests)
- Deep nesting in `_organize_by_lanes()` will naturally flatten when extracted

---

#### R4. Extract Parser Namespace Helper (DRY violation, ~15 repetitions)

**Priority:** Medium
**Effort:** XS
**Impact:** Eliminates 15 copies of the same namespace fallback pattern

**Current State:**
`bpmn2drawio/parser.py` repeats this pattern ~15 times:
```python
element = root.find(".//ns:Element", self.namespaces)
if element is None:
    element = root.find(".//{*}Element")
```

**Recommendation:**
Extract to helper method:
```python
def _find_element(self, parent, ns_xpath: str, wildcard_xpath: str):
    result = parent.find(ns_xpath, self.namespaces)
    return result if result is not None else parent.find(wildcard_xpath)
```

**Implementation Notes:**
- Pure refactoring — behavior is identical
- Existing parser tests (14 tests) serve as regression guard
- Also add a `_findall_elements()` variant for the `findall` usages

---

#### R5. Flatten Deep Nesting in image_generator._generate_with_retry()

**Priority:** Low
**Effort:** S
**Impact:** Improves readability of retry logic; enables extraction to reusable pattern

**Current State:**
`image_generator.py` lines 328-461 (134 LOC) have 4-level nesting with retry loop, status checking, and progress callbacks interleaved.

**Recommendation:**
Extract retry strategy to separate method or use early-return pattern:
```python
async def _generate_with_retry(self, prompt, config):
    for attempt in range(max_retries):
        result = await self._attempt_generation(prompt, config)
        if result.success:
            return result
        if not self._should_retry(result, attempt):
            return result
        await self._wait_for_retry(attempt, result)
    return GenerationResult(status=GenerationStatus.MAX_RETRIES)
```

**Implementation Notes:**
- Requires T2 tests for image_generator first (characterization tests before refactoring)
- Keep the retry delay calculation logic unchanged
- Consider extracting to a generic `RetryStrategy` class for reuse across tools

---

### Category 3: Dependency & Build Management (D)

#### D1. Tighten google-genai Version Constraint

**Priority:** Critical
**Effort:** XS
**Impact:** Prevents silent breaking changes from major version upgrades

**Current State:**
`visual-explainer/pyproject.toml` specifies `google-genai>=0.1.0` — this accepts any future version including hypothetical 5.0.0 with completely different API.

**Recommendation:**
Change to: `google-genai>=1.0.0,<2.0.0`

Also review and tighten other loose constraints:
- `anthropic>=0.40.0` → `anthropic>=0.40.0,<1.0.0` (if still 0.x) or `>=0.40.0,<2.0.0`
- `openai>=1.50.0` → `openai>=1.50.0,<3.0.0`

**Implementation Notes:**
- Check current installed versions first: `pip show google-genai anthropic openai`
- Apply same tightening to research-orchestrator's pyproject.toml
- Keep `>=` for minimum, add `<NEXT_MAJOR` for upper bound

---

#### D2. Add Dependency Lock Files

**Priority:** High
**Effort:** S
**Impact:** Ensures reproducible builds in CI and across developer machines

**Current State:**
No lock files exist (no poetry.lock, Pipfile.lock, requirements.txt with pinned versions). CI installs latest compatible versions on each run, making builds non-deterministic.

**Recommendation:**
Add `requirements-lock.txt` files generated by `pip-compile` (from `pip-tools`) for each tool:
```bash
pip-compile pyproject.toml -o requirements-lock.txt
pip-compile pyproject.toml --extra dev -o requirements-dev-lock.txt
```

**Implementation Notes:**
- Add `pip-tools` to each tool's dev dependencies
- CI should install from lock files: `pip install -r requirements-lock.txt`
- Add a CI job or pre-commit check that verifies lock files are up-to-date
- Developers update lock files when changing pyproject.toml: `pip-compile --upgrade`

---

#### D3. Add Logging to Swallowed Exceptions

**Priority:** Medium
**Effort:** XS
**Impact:** Silent API failures in model_discovery.py become diagnosable

**Current State:**
Two `except Exception: pass` handlers silently swallow API listing failures:
- `research_orchestrator/model_discovery.py:171` — Anthropic model listing
- `research_orchestrator/model_discovery.py:209` — OpenAI model listing

One in test code:
- `tests/integration/test_bump_version.py:60` — Version write failure

**Recommendation:**
Replace `pass` with `logging.debug()` or `logging.warning()`:
```python
except Exception as e:
    logger.warning(f"Failed to list Anthropic models: {e}")
```

**Implementation Notes:**
- Import `logging` and create module-level logger
- Use `warning` level for API failures (user should know if model discovery fails)
- Use `debug` level for the test helper (less critical)

---

#### D4. Add GitHub Actions Dependency Caching

**Priority:** Medium
**Effort:** S
**Impact:** Reduces CI build times by caching pip downloads

**Current State:**
Each CI run installs all dependencies from scratch. No `actions/cache` or `setup-python` caching configured.

**Recommendation:**
Add pip caching to all CI jobs:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```

**Implementation Notes:**
- Add to both test.yml and validate.yml workflows
- Cache key should include pyproject.toml hash for automatic invalidation
- Expected CI time reduction: 30-60 seconds per job

---

### Category 4: Architecture & Design (A)

#### A1. Implement Checkpoint Resume for visual-explainer

**Priority:** Medium
**Effort:** L
**Impact:** Enables resuming long-running image generation after interruption

**Current State:**
`visual_explainer/cli.py:1123` has a TODO comment: "Implement full checkpoint resume logic". The `--resume` flag exists in the CLI but returns `"resume_not_implemented"`. Checkpoint saving infrastructure exists (checkpoint files are written during generation) but loading/resuming is stubbed.

**Recommendation:**
Implement checkpoint resume:
1. On `--resume <checkpoint_dir>`, load the checkpoint JSON
2. Determine which images were already generated and passed evaluation
3. Resume generation from the next pending image
4. Merge completed results with checkpoint state

**Implementation Notes:**
- Checkpoint JSON structure already defined in `models.py`
- The conftest.py already has checkpoint fixtures for testing
- This is a feature completion, not a refactor — add after T2 tests are in place
- Test with: interrupted mid-generation, all images complete, no checkpoint file

---

#### A2. Unify Python Version Requirements

**Priority:** Low
**Effort:** XS
**Impact:** Simplifies contributor setup; removes confusion about Python version needed

**Current State:**
- bpmn2drawio: requires Python >=3.9
- research-orchestrator: requires Python >=3.9
- visual-explainer: requires Python >=3.10
- feedback-docx-generator: requires Python >=3.9

The visual-explainer requires 3.10+ (uses `match` statements or union type syntax).

**Recommendation:**
Standardize all tools to `python_requires = ">=3.10"` since that's the effective minimum (visual-explainer blocks 3.9). Document this in CLAUDE.md and README.

**Implementation Notes:**
- Update pyproject.toml for 3 tools (remove 3.9 from classifiers)
- Update CI matrix if needed (currently Python 3.11 only, so no CI change needed)
- Check if any 3.9-specific workarounds can be removed

---

#### A3. Add Input Validation to CLI Parameters

**Priority:** Medium
**Effort:** S
**Impact:** Prevents confusing errors from invalid parameter combinations

**Current State:**
Visual-explainer CLI accepts:
- `--pass-threshold 5.0` (should be 0.0-1.0)
- `--concurrency 1000` (should be 1-10)
- `--max-iterations 999` (should be 1-20)
- No upper bound on interactive image count prompt

**Recommendation:**
Add validation in `GenerationConfig.from_cli_and_env()` or via argparse `type` functions:
```python
parser.add_argument('--pass-threshold', type=float,
                    choices=None,  # use custom validator
                    help='Quality threshold (0.0-1.0)')

def validate_threshold(value):
    f = float(value)
    if not 0.0 <= f <= 1.0:
        raise argparse.ArgumentTypeError(f"Must be 0.0-1.0, got {f}")
    return f
```

**Implementation Notes:**
- Add argparse type validators for bounded numeric parameters
- Add max image count (50) to interactive prompt
- Pair with T7 validation tests

---

#### A4. Narrow Broad Exception Handlers

**Priority:** Medium
**Effort:** S
**Impact:** Prevents masking of unexpected errors; improves debuggability

**Current State:**
33 `except Exception` handlers across the codebase. Most are legitimate (top-level CLI handlers, API error wrapping), but several should be narrowed:
- `layout.py:57` — Graphviz fallback catches everything including `KeyboardInterrupt`
- `model_discovery.py:171,209` — Silent API failures (addressed in D3)
- `api_setup.py:55`, `cli.py:75` — Windows encoding detection

**Recommendation:**
Narrow the non-top-level handlers:
- `layout.py:57`: Change to `except (ImportError, AttributeError, RuntimeError, OSError):`
- `api_setup.py:55`: Change to `except (AttributeError, OSError):`
- `cli.py:75`: Change to `except (AttributeError, OSError):`

Leave top-level CLI handlers (`cli.py:1279`, `api_setup.py:747`) as `except Exception` — these are legitimate catch-alls for user-facing error messages.

**Implementation Notes:**
- Run tests after each change to verify no behavior change
- For layout.py, verify that the graphviz fallback path still triggers correctly

---

### Category 5: Developer Experience (X)

#### X1. Add Type Checking with mypy to CI

**Priority:** Medium
**Effort:** S
**Impact:** Catches type errors at CI time; leverages existing 90%+ type hint coverage

**Current State:**
All tools have excellent type hint coverage (90%+) but no static type checker runs in CI. Type hints are documentation-only — they don't catch errors.

**Recommendation:**
Add mypy to each tool's dev dependencies and CI:
```yaml
- name: Type check
  run: mypy src/ --ignore-missing-imports
```

**Implementation Notes:**
- Start with `--ignore-missing-imports` to avoid third-party stubs issues
- Add `mypy.ini` or `[tool.mypy]` section to each pyproject.toml
- Use `--strict` mode incrementally (start with basic checks, enable strictness over time)
- Expected initial findings: some `Any` type escapes, missing return types on internal helpers

---

#### X2. Consolidate Common Patterns Across Python Tools

**Priority:** Low
**Effort:** L
**Impact:** Reduces duplicated code; creates a shared foundation for new tools

**Current State:**
Common patterns are reimplemented in each tool:
- API key loading from environment (research-orchestrator, visual-explainer)
- Rich console output with fallback (research-orchestrator, visual-explainer)
- CLI argument parsing boilerplate (all 4 tools)
- Retry logic with exponential backoff (research-orchestrator, visual-explainer)
- Configuration loading from environment + defaults (all tools)

**Recommendation:**
Create a shared library `plugins/shared/claude-plugin-utils/` with:
- `config.py` — Environment variable loading, API key management
- `cli.py` — Common argparse patterns, output formatting
- `retry.py` — Generic retry with exponential backoff
- `console.py` — Rich console with graceful fallback

**Implementation Notes:**
- This is a nice-to-have, not urgent — each tool works fine independently
- Start by extracting retry logic (most duplicated, highest value)
- Keep tools independently runnable (shared lib is optional dependency)
- Consider whether maintenance cost of shared lib exceeds duplication cost

---

#### X3. Add Pre-commit Type and Lint Checks

**Priority:** Low
**Effort:** S
**Impact:** Catches issues before commit; integrates with existing pre-commit hook

**Current State:**
The pre-commit hook validates markdown frontmatter and help skill sync but does not check Python code quality.

**Recommendation:**
Extend pre-commit hook or add `.pre-commit-config.yaml` with:
- `ruff check` — Fast Python linting (already in dev deps)
- `ruff format --check` — Formatting validation
- `mypy` — Type checking (after X1)

**Implementation Notes:**
- Use the `pre-commit` framework rather than custom bash scripts
- Configure to only check staged Python files (fast)
- Keep existing markdown validation as-is

---

### Category 6: Documentation & Operations (O)

#### O1. Document Architectural Decisions (ADRs)

**Priority:** Low
**Effort:** S
**Impact:** Prevents re-debating resolved decisions; helps new contributors understand "why"

**Current State:**
Key architectural decisions are embedded in CLAUDE.md comments but not formally documented:
1. Why skills use nested directories but commands use flat files
2. Why Python tools run from source via PYTHONPATH instead of being installed
3. Why secrets are in Bitwarden instead of .env files
4. Why no cross-plugin references exist

**Recommendation:**
Create `docs/adr/` directory with decision records:
- `0001-skill-directory-structure.md`
- `0002-python-tools-from-source.md`
- `0003-bitwarden-secrets.md`
- `0004-plugin-encapsulation.md`

**Implementation Notes:**
- Use lightweight ADR format (context, decision, consequences)
- Reference from CLAUDE.md for discoverability
- Not urgent — CLAUDE.md already captures most of this

---

## Quick Wins

Items achievable in < 2 hours each, high impact-to-effort ratio:

1. **D1** — Tighten `google-genai>=0.1.0` to `>=1.0.0,<2.0.0` (5 minutes)
2. **R4** — Extract parser namespace helper to eliminate 15 duplications (30 minutes)
3. **D3** — Add logging to 2 swallowed exceptions in model_discovery.py (15 minutes)
4. **A4** — Narrow `except Exception` in layout.py:57 to specific types (15 minutes)
5. **D4** — Add pip caching to CI workflows (20 minutes)
6. **A2** — Unify Python version requirement to >=3.10 (15 minutes)

---

## Strategic Initiatives

Larger efforts requiring multi-phase execution:

1. **T1+T2+T3+T4+T5+T6** — Close all test coverage gaps and enforce thresholds (~6,500 lines to cover)
2. **R1+R2+R3** — Refactor 3 complexity hotspots (PromptGenerator, PositionResolver, CLI pipeline)
3. **D2** — Add dependency lock files for reproducible builds
4. **A1** — Implement checkpoint resume for visual-explainer
5. **X2** — Consolidate shared patterns into common library

---

## Not Recommended

Items considered but rejected, with rationale:

| Item | Rationale |
|------|-----------|
| Migrate to poetry/uv for dependency management | Current pyproject.toml + pip-tools approach is simpler and sufficient |
| Add Docker support | Plugins run inside Claude Code's environment; containerization adds no value |
| Add cross-plugin dependency injection | Plugins should remain independent; coupling would complicate marketplace installs |
| Convert pre-commit hook to Python | Bash hook works, is fast, and the pre-commit framework would add a new dependency |
| Add GraphQL API for plugin metadata | Over-engineering; marketplace.json is simple and effective |
| Replace Rich with custom console output | Rich is well-maintained and provides significant value; replacing it wastes effort |

---

*Recommendations generated by Claude on 2026-02-16T18:45:00*
