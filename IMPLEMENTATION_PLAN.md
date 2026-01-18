# Implementation Plan

**Generated:** 2026-01-18 15:30:00
**Source Documents:**
- IMAGE_GEN_PLAN.md (Visual Concept Explainer design specification)

**Total Phases:** 5
**Estimated Total Effort:** ~280,000 tokens

---

## Executive Summary

This plan implements the **Visual Concept Explainer** skill for the personal-plugin, a tool that transforms text or documents into AI-generated images that explain concepts visually. The implementation follows the architecture patterns established by the research-orchestrator tool.

The skill combines:
- **Gemini Pro 3** for 4K image generation
- **Claude Sonnet Vision** for quality evaluation
- **Iterative refinement** with configurable max attempts (default: 5)
- **Checkpoint/resume** support for long-running generations
- **Bundled style configurations** adapted from slide-generator

The critical path runs through: Foundation → Core Modules → Generation Pipeline → Skill Integration → Polish. Phases 2 and 3 have internal parallelization opportunities.

---

## Plan Overview

The implementation is organized into 5 phases following dependency order:

1. **Foundation** - Project scaffolding, configuration, API setup wizard
2. **Core Modules** - Data models, style loading, concept analysis
3. **Generation Pipeline** - Gemini integration, evaluation, refinement loop
4. **Skill Integration** - SKILL.md, CLI orchestration, output organization
5. **Testing & Polish** - Tests, documentation, help updates

Each phase leaves the codebase in a working (if incomplete) state. Phases are designed for sequential execution, with parallel work items within each phase.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Tokens | Dependencies |
|-------|------------|------------------|-------------|--------------|
| 1 | Foundation | pyproject.toml, config.py, api_setup.py, styles/ | ~45K | None |
| 2 | Core Modules | models.py, style_loader.py, concept_analyzer.py | ~55K | Phase 1 |
| 3 | Generation Pipeline | image_generator.py, image_evaluator.py, prompt_generator.py | ~70K | Phase 2 |
| 4 | Skill Integration | SKILL.md, cli.py, __main__.py, output organization | ~60K | Phase 3 |
| 5 | Testing & Polish | Unit tests, integration tests, help updates, docs | ~50K | Phase 4 |

---

## Phase 1: Foundation

**Estimated Effort:** ~45,000 tokens (including testing/fixes)
**Dependencies:** None
**Parallelizable:** Yes - work items 1.1-1.4 can run concurrently

### Goals

- Establish project structure following research-orchestrator patterns
- Create configuration system with Pydantic models
- Implement first-run API key setup wizard
- Copy and adapt bundled style configurations

### Work Items

#### 1.1 Create Project Scaffolding

**Requirement Refs:** IMAGE_GEN_PLAN §2.1
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/pyproject.toml` (create)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/__init__.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/__main__.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/README.md` (create)

**Description:**
Create the tool directory structure mirroring research-orchestrator. The pyproject.toml should include all dependencies from §9.1 with optional extras for DOCX and PDF support.

**Tasks:**
1. [ ] Create directory structure: `tools/visual-explainer/src/visual_explainer/`
2. [ ] Create `pyproject.toml` with dependencies: httpx, anthropic, python-dotenv, pydantic, aiofiles
3. [ ] Add optional dependencies: python-docx, PyPDF2, beautifulsoup4
4. [ ] Add dev dependencies: pytest, pytest-asyncio, pytest-cov, ruff, black
5. [ ] Create minimal `__init__.py` with version
6. [ ] Create `__main__.py` that imports and runs cli.main()
7. [ ] Create README.md with tool overview

**Acceptance Criteria:**
- [ ] `pip install -e .` succeeds in the tool directory
- [ ] `python -m visual_explainer --help` runs (even if just shows placeholder)
- [ ] pyproject.toml follows research-orchestrator patterns

**Notes:**
Use `requires-python = ">=3.10"` to match the plan. Include `[project.scripts]` entry point.

---

#### 1.2 Implement Configuration System

**Requirement Refs:** IMAGE_GEN_PLAN §5.1, §5.2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/config.py` (create)

**Description:**
Create Pydantic models for all configuration options. Include defaults from the decision log: max_iterations=5, pass_threshold=0.85, resolution=high, concurrency=3.

**Tasks:**
1. [ ] Create `GenerationConfig` Pydantic model with all user-configurable parameters
2. [ ] Create `InternalConfig` for non-exposed defaults (negative prompt, cache settings)
3. [ ] Create `StyleConfig` model matching the style JSON schema
4. [ ] Implement config loading from CLI args, env vars, and defaults (priority order)
5. [ ] Add validation for parameter ranges (max_iterations 1-10, pass_threshold 0-1, etc.)
6. [ ] Include the default negative prompt from §5.2

**Acceptance Criteria:**
- [ ] All 12 CLI parameters from §5.1 are represented
- [ ] Default values match the decision log exactly
- [ ] Pydantic validation catches invalid configurations
- [ ] Config can be serialized to JSON for metadata output

**Notes:**
Reference research-orchestrator's config.py for patterns. Use `Field()` with descriptions for CLI help generation.

---

#### 1.3 Implement API Key Setup Wizard

**Requirement Refs:** IMAGE_GEN_PLAN §6.2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/api_setup.py` (create)

**Description:**
Create interactive first-run setup that detects missing API keys, provides step-by-step instructions, validates keys against the APIs, and creates the .env file.

**Tasks:**
1. [ ] Implement `check_api_keys()` to detect GOOGLE_API_KEY and ANTHROPIC_API_KEY
2. [ ] Implement `validate_google_key()` with async httpx call to list models
3. [ ] Implement `validate_anthropic_key()` with minimal messages.create call
4. [ ] Create interactive prompts for each missing key with full instructions from §6.2
5. [ ] Implement `create_env_file()` to write keys and update .gitignore
6. [ ] Display cost information summary after setup
7. [ ] Support 'skip' option to defer setup
8. [ ] Add `--setup-keys` CLI flag to force re-running setup

**Acceptance Criteria:**
- [ ] Running with no .env prompts for both keys with detailed instructions
- [ ] Invalid keys are rejected with clear error message
- [ ] Valid keys are saved to .env with timestamp comment
- [ ] .gitignore is updated if .env not already listed
- [ ] Cost summary matches §6.2 estimates

**Notes:**
Use Rich library for formatted output (already a dependency via research-orchestrator patterns).

---

#### 1.4 Copy and Adapt Style Configurations

**Requirement Refs:** IMAGE_GEN_PLAN §5.3, §12.2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/styles/professional-clean.json` (create)
- `plugins/personal-plugin/tools/visual-explainer/styles/professional-sketch.json` (create)
- `plugins/personal-plugin/tools/visual-explainer/styles/README.md` (create)

**Description:**
Copy the sanitized style files from slide-generator and adapt them for the visual-explainer use case. Create documentation explaining the style schema.

**Tasks:**
1. [ ] Copy `C:\dev\stratfield\slide-generator\styles\clean-style-sanitized.json` to `styles/professional-clean.json`
2. [ ] Copy `C:\dev\stratfield\slide-generator\styles\sketch-style-sanitized.json` to `styles/professional-sketch.json`
3. [ ] Review and update StyleName to match new tool
4. [ ] Verify PromptRecipe sections are complete (CoreStylePrompt, NegativePrompt, etc.)
5. [ ] Create `styles/README.md` documenting the schema structure
6. [ ] Document how to create custom style files

**Acceptance Criteria:**
- [ ] Both style files are valid JSON
- [ ] StyleName fields updated to "Visual_Explainer_*"
- [ ] README explains all schema sections with examples
- [ ] Custom style creation process is documented

**Notes:**
Keep the comprehensive structure - it's proven in slide-generator.

---

### Phase 1 Testing Requirements

- [ ] pyproject.toml installs without errors
- [ ] Config validation rejects invalid values
- [ ] API setup wizard displays correctly (manual test)
- [ ] Style files parse as valid JSON

### Phase 1 Completion Checklist

- [ ] All 4 work items complete
- [ ] Directory structure matches IMAGE_GEN_PLAN §2.1
- [ ] Tool can be imported as Python module
- [ ] No ruff/black errors in new code

---

## Phase 2: Core Modules

**Estimated Effort:** ~55,000 tokens (including testing/fixes)
**Dependencies:** Phase 1
**Parallelizable:** Yes - work items 2.1-2.3 can run concurrently after Phase 1

### Goals

- Define data models for concepts, prompts, and evaluations
- Implement style loading with priority resolution
- Create concept analyzer using Claude for document analysis

### Work Items

#### 2.1 Implement Data Models

**Requirement Refs:** IMAGE_GEN_PLAN §3 (Phase 2, 4, 6), §8 (Metadata Schema)
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/models.py` (create)

**Description:**
Create Pydantic models for all data structures: extracted concepts, image prompts, evaluation results, and generation metadata. These provide the contract between modules.

**Tasks:**
1. [ ] Create `Concept` model with id, name, description, relationships, complexity, visual_potential
2. [ ] Create `ConceptAnalysis` model with title, summary, target_audience, concepts list, logical_flow, recommended_image_count
3. [ ] Create `ImagePrompt` model with image_number, title, concepts_covered, visual_intent, prompt details, success_criteria, flow_connection
4. [ ] Create `EvaluationResult` model with scores, strengths, weaknesses, verdict, refinement_suggestions
5. [ ] Create `ImageResult` model tracking attempts, evaluations, final selection
6. [ ] Create `GenerationMetadata` model matching §8 schema exactly
7. [ ] Add JSON serialization methods for all models

**Acceptance Criteria:**
- [ ] All JSON structures from §3 and §8 have corresponding Pydantic models
- [ ] Models validate correctly and reject invalid data
- [ ] Serialization produces JSON matching the spec exactly
- [ ] Relationships between models are clear (ConceptAnalysis contains Concepts, etc.)

**Notes:**
Use Pydantic v2 features. Consider using `model_dump(mode='json')` for serialization.

---

#### 2.2 Implement Style Loader

**Requirement Refs:** IMAGE_GEN_PLAN §5.3
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/style_loader.py` (create)

**Description:**
Create a module to load style configurations with the priority order specified: user path → named bundled style → interactive selection → default. Extract PromptRecipe for injection into prompts.

**Tasks:**
1. [ ] Implement `load_style(style_arg: str | None) -> StyleConfig`
2. [ ] Handle full path (user-provided JSON file)
3. [ ] Handle named style ("professional-clean" → look up in bundled styles/)
4. [ ] Implement bundled style discovery from package resources
5. [ ] Return default "professional-clean" when no style specified
6. [ ] Extract and format PromptRecipe sections for prompt injection
7. [ ] Validate loaded style against StyleConfig model
8. [ ] Handle missing/invalid style files with clear error messages

**Acceptance Criteria:**
- [ ] `--style professional-clean` loads bundled style
- [ ] `--style /path/to/custom.json` loads user style
- [ ] Invalid style paths produce helpful error
- [ ] PromptRecipe extraction works for prompt generation

**Notes:**
Use `importlib.resources` for accessing bundled styles. Consider caching loaded styles.

---

#### 2.3 Implement Concept Analyzer

**Requirement Refs:** IMAGE_GEN_PLAN §3 (Phase 2), Appendix A.1
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/concept_analyzer.py` (create)

**Description:**
Create the module that uses Claude to analyze input documents and extract structured concepts. Implement caching based on content hash to avoid re-analyzing unchanged documents.

**Tasks:**
1. [ ] Implement `analyze_document(text: str, config: GenerationConfig) -> ConceptAnalysis`
2. [ ] Create the analysis prompt from Appendix A.1 template
3. [ ] Call Claude API (Sonnet) for concept extraction
4. [ ] Parse JSON response into ConceptAnalysis model
5. [ ] Implement SHA-256 content hashing for cache key
6. [ ] Implement cache storage at `.cache/visual-explainer/concepts-[hash].json`
7. [ ] Load from cache when hash matches (unless --no-cache)
8. [ ] Handle input type detection (raw text vs file path vs URL)
9. [ ] Implement file readers: .md, .txt, .docx, .pdf
10. [ ] Implement URL content extraction with BeautifulSoup

**Acceptance Criteria:**
- [ ] Returns valid ConceptAnalysis with concepts and logical_flow
- [ ] Caching works: second call with same content uses cache
- [ ] --no-cache forces fresh analysis
- [ ] Supports .md, .txt, .docx, .pdf, and URLs
- [ ] Handles errors gracefully (empty input, unsupported format)

**Notes:**
For .docx and .pdf, make them optional - catch ImportError and suggest installing extras. URL fetching should respect robots.txt basics.

---

### Phase 2 Testing Requirements

- [ ] Models serialize/deserialize round-trip correctly
- [ ] Style loader finds bundled styles
- [ ] Concept analyzer returns valid structure (mock API test)
- [ ] Cache hits/misses work correctly

### Phase 2 Completion Checklist

- [ ] All 3 work items complete
- [ ] All models have comprehensive type hints
- [ ] Unit tests cover model validation
- [ ] Concept analysis works with sample text

---

## Phase 3: Generation Pipeline

**Estimated Effort:** ~70,000 tokens (including testing/fixes)
**Dependencies:** Phase 2
**Parallelizable:** Partially - 3.1 and 3.2 can run concurrently; 3.3 depends on both

### Goals

- Integrate Gemini Pro 3 for 4K image generation
- Implement Claude Vision evaluation with scoring
- Build the refinement loop with prompt iteration strategies

### Work Items

#### 3.1 Implement Image Generator (Gemini)

**Requirement Refs:** IMAGE_GEN_PLAN §5 (Phase 5), §6.3
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/image_generator.py` (create)

**Description:**
Create the async Gemini API client for image generation. Support all aspect ratios and resolutions, with proper error handling for rate limits and safety filters.

**Tasks:**
1. [ ] Create `GeminiImageGenerator` class following §6.3 pattern
2. [ ] Implement `generate_image(prompt, aspect_ratio, resolution, negative_prompt) -> bytes`
3. [ ] Configure for 4K output (LARGE/3200x1800) by default
4. [ ] Set 300-second timeout for 4K generation
5. [ ] Implement retry logic with exponential backoff for rate limits (429)
6. [ ] Handle safety filter blocks (log and return None)
7. [ ] Extract base64 image data from response
8. [ ] Implement concurrent generation with semaphore (max 3 default)
9. [ ] Add progress callback support for UI updates

**Acceptance Criteria:**
- [ ] Generates 4K images successfully with valid API key
- [ ] Rate limit (429) triggers backoff and retry
- [ ] Safety filter blocks are logged, not crashed
- [ ] Concurrent generation respects semaphore limit
- [ ] Timeout set to 300s for 4K

**Notes:**
Use httpx for async. Reference slide-generator's async_gemini_client.py for patterns. Don't use the google-genai SDK - stick with raw API for control.

---

#### 3.2 Implement Image Evaluator (Claude Vision)

**Requirement Refs:** IMAGE_GEN_PLAN §3 (Phase 6), §6.4
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/image_evaluator.py` (create)

**Description:**
Create the Claude Vision evaluation module that scores generated images against success criteria and provides refinement suggestions.

**Tasks:**
1. [ ] Create `ImageEvaluator` class using Claude Sonnet 4
2. [ ] Implement `evaluate_image(image_bytes, intent, criteria, context) -> EvaluationResult`
3. [ ] Build evaluation prompt from §6.4 template
4. [ ] Send image as base64 with multimodal message
5. [ ] Parse JSON response into EvaluationResult model
6. [ ] Implement verdict thresholds: PASS ≥0.85, NEEDS_REFINEMENT 0.5-0.84, FAIL <0.5
7. [ ] Extract refinement_suggestions for prompt iteration
8. [ ] Handle evaluation errors gracefully

**Acceptance Criteria:**
- [ ] Returns valid EvaluationResult with all fields
- [ ] Verdict matches threshold rules exactly
- [ ] Refinement suggestions are actionable text
- [ ] Works with JPEG image bytes

**Notes:**
Use anthropic SDK for cleaner multimodal handling. Consider caching evaluations by image hash if useful.

---

#### 3.3 Implement Prompt Generator with Refinement

**Requirement Refs:** IMAGE_GEN_PLAN §3 (Phase 4, 7), Appendix A.2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/prompt_generator.py` (create)

**Description:**
Create the module that generates image prompts from concepts and refines them based on evaluation feedback. Implement the escalating refinement strategy from the plan.

**Tasks:**
1. [ ] Implement `generate_prompts(analysis: ConceptAnalysis, style: StyleConfig) -> list[ImagePrompt]`
2. [ ] Create prompt generation using Appendix A.2 template
3. [ ] Inject style PromptRecipe (CoreStylePrompt, ColorConstraintPrompt, etc.)
4. [ ] Apply default negative prompt from config
5. [ ] Implement `refine_prompt(original: ImagePrompt, feedback: EvaluationResult, attempt: int) -> ImagePrompt`
6. [ ] Implement escalating refinement strategy per attempt:
   - Attempt 2: Add specific fixes from feedback
   - Attempt 3: Strengthen weak areas, simplify
   - Attempt 4: Try alternative visual metaphor
   - Attempt 5: Fundamental restructure
7. [ ] Generate success_criteria list for each image
8. [ ] Handle flow_connection between sequential images

**Acceptance Criteria:**
- [ ] Generates ImagePrompt for each planned image
- [ ] Style injection produces coherent combined prompt
- [ ] Refinement produces meaningfully different prompts
- [ ] Success criteria are specific and evaluatable
- [ ] Sequential images have flow connections

**Notes:**
The refinement strategy is key to quality. Log the refinement reasoning for debugging.

---

### Phase 3 Testing Requirements

- [ ] Image generator returns bytes (mock API or integration test)
- [ ] Evaluator parses Claude response correctly
- [ ] Prompt refinement produces different prompts per attempt
- [ ] Full generate→evaluate loop works end-to-end (integration)

### Phase 3 Completion Checklist

- [ ] All 3 work items complete
- [ ] API error handling is robust
- [ ] Retry logic works for transient failures
- [ ] Components integrate cleanly

---

## Phase 4: Skill Integration

**Estimated Effort:** ~60,000 tokens (including testing/fixes)
**Dependencies:** Phase 3
**Parallelizable:** Partially - 4.1 and 4.2 can start together; 4.3 depends on 4.2

### Goals

- Create the orchestrating CLI that ties everything together
- Implement checkpoint/resume for interruption recovery
- Create the SKILL.md for Claude Code integration
- Organize outputs per the specification

### Work Items

#### 4.1 Implement Output Organization

**Requirement Refs:** IMAGE_GEN_PLAN §3 (Phase 8)
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/output.py` (create)

**Description:**
Create the output management module that organizes generated files according to the directory structure specification.

**Tasks:**
1. [ ] Implement `OutputManager` class to handle all file operations
2. [ ] Create output directory structure: `visual-explainer-[topic-slug]-[timestamp]/`
3. [ ] Create image subdirectories: `image-01/`, `image-02/`, etc.
4. [ ] Save attempt images as `attempt-01.jpg`, `attempt-02.jpg`
5. [ ] Save prompts as `prompt-v1.txt`, `prompt-v2.txt`
6. [ ] Save evaluations as `evaluation-01.json`, `evaluation-02.json`
7. [ ] Create `final.jpg` symlink/copy to best attempt
8. [ ] Create `all-images/` with numbered final images
9. [ ] Write `metadata.json` with GenerationMetadata
10. [ ] Write `concepts.json` with ConceptAnalysis
11. [ ] Generate `summary.md` human-readable report
12. [ ] Implement checkpoint save/load for resume support

**Acceptance Criteria:**
- [ ] Directory structure matches §3 Phase 8 exactly
- [ ] All files are created in correct locations
- [ ] summary.md is human-readable with key stats
- [ ] Checkpoint enables resume after interruption
- [ ] Metadata JSON matches schema

**Notes:**
Use aiofiles for async I/O. Topic slug should be URL-safe (lowercase, hyphens).

---

#### 4.2 Implement CLI Orchestrator

**Requirement Refs:** IMAGE_GEN_PLAN §4.1, §4.2, §4.3, §4.4
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/cli.py` (create)

**Description:**
Create the main CLI that orchestrates the full generation pipeline. Support both command-line arguments and interactive mode.

**Tasks:**
1. [ ] Create argparse/click CLI with all parameters from §5.1
2. [ ] Implement `main()` entry point
3. [ ] Add `--setup-keys` subcommand for API key setup
4. [ ] Check for API keys on startup, run setup if missing
5. [ ] Implement interactive mode when no --input provided
6. [ ] Display concept analysis summary per §4.2
7. [ ] Prompt for style selection if not specified
8. [ ] Confirm image count with user options
9. [ ] Implement generation progress display per §4.3
10. [ ] Display completion summary per §4.4
11. [ ] Support `--resume [checkpoint]` to continue interrupted generation
12. [ ] Implement `--dry-run` to show plan without generating

**Acceptance Criteria:**
- [ ] All 12 CLI parameters work
- [ ] Interactive mode guides user through options
- [ ] Progress display shows per-image status
- [ ] Resume continues from checkpoint
- [ ] Dry-run shows plan only

**Notes:**
Use Rich for formatted output (progress bars, tables). Consider async main with asyncio.run().

---

#### 4.3 Create SKILL.md

**Requirement Refs:** IMAGE_GEN_PLAN §4, §12.1
**Files Affected:**
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (create)

**Description:**
Create the skill definition file that integrates with Claude Code. Follow research-topic SKILL.md patterns for structure.

**Tasks:**
1. [ ] Create `skills/visual-explainer/` directory
2. [ ] Create SKILL.md with required frontmatter (name, description)
3. [ ] Document input validation and arguments
4. [ ] Document environment requirements (API keys)
5. [ ] Define skill phases matching the workflow
6. [ ] Include tool invocation instructions with PYTHONPATH pattern
7. [ ] Document interactive flow for style/image count selection
8. [ ] Include progress display format
9. [ ] Document completion summary format
10. [ ] Add examples for common use cases

**Acceptance Criteria:**
- [ ] Frontmatter has name: visual-explainer
- [ ] Description matches tool purpose
- [ ] All CLI parameters documented
- [ ] Tool invocation pattern correct
- [ ] Follows research-topic SKILL.md structure

**Notes:**
The skill orchestrates Claude's interaction with the Python tool. Keep tool responsibilities clear.

---

### Phase 4 Testing Requirements

- [ ] CLI parses all arguments correctly
- [ ] Interactive mode works (manual test)
- [ ] Output directory structure is correct
- [ ] Resume from checkpoint works
- [ ] SKILL.md loads in Claude Code

### Phase 4 Completion Checklist

- [ ] All 3 work items complete
- [ ] Full pipeline runs end-to-end
- [ ] Output matches specification
- [ ] Skill integrates with Claude Code

---

## Phase 5: Testing & Polish

**Estimated Effort:** ~50,000 tokens (including fixes)
**Dependencies:** Phase 4
**Parallelizable:** Yes - work items 5.1-5.3 can run concurrently

### Goals

- Achieve >80% test coverage for core modules
- Update plugin help documentation
- Create example outputs and documentation
- Final validation and cleanup

### Work Items

#### 5.1 Implement Unit Tests

**Requirement Refs:** IMAGE_GEN_PLAN §10.1
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_config.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_models.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_style_loader.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_concept_analyzer.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_prompt_generator.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/tests/__init__.py` (create)
- `plugins/personal-plugin/tools/visual-explainer/tests/conftest.py` (create)

**Description:**
Create comprehensive unit tests for all modules. Use mocks for API calls.

**Tasks:**
1. [ ] Create test fixtures in conftest.py (sample concepts, styles, etc.)
2. [ ] Test config validation (valid and invalid cases)
3. [ ] Test model serialization/deserialization
4. [ ] Test style loader with bundled and custom styles
5. [ ] Test concept analyzer with mocked Claude API
6. [ ] Test prompt generator output structure
7. [ ] Test refinement strategy produces different prompts
8. [ ] Test evaluation result parsing
9. [ ] Test output manager file operations
10. [ ] Achieve >80% coverage on core modules

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Coverage >80% for core modules
- [ ] Mocks properly isolate API calls
- [ ] Edge cases covered (empty input, invalid config, etc.)

**Notes:**
Use pytest-asyncio for async tests. Use respx or unittest.mock for API mocking.

---

#### 5.2 Implement Integration Tests

**Requirement Refs:** IMAGE_GEN_PLAN §10.2
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/test_integration.py` (create)

**Description:**
Create integration tests that verify the full pipeline works with mocked APIs.

**Tasks:**
1. [ ] Create mock Gemini API responses (base64 image data)
2. [ ] Create mock Claude API responses (concept analysis, evaluation)
3. [ ] Test full pipeline: input → concepts → prompts → images → evaluation
4. [ ] Test retry logic with simulated rate limits
5. [ ] Test checkpoint/resume with interrupted generation
6. [ ] Test error recovery (API failures, timeouts)
7. [ ] Verify output directory structure

**Acceptance Criteria:**
- [ ] Full pipeline test passes with mocks
- [ ] Retry logic works under simulated failures
- [ ] Resume correctly continues from checkpoint
- [ ] Error messages are helpful

**Notes:**
Consider pytest markers for slow integration tests.

---

#### 5.3 Update Documentation

**Requirement Refs:** IMAGE_GEN_PLAN §12.4
**Files Affected:**
- `plugins/personal-plugin/skills/help/SKILL.md` (modify)
- `plugins/personal-plugin/tools/visual-explainer/README.md` (modify)

**Description:**
Update all documentation to reflect the completed implementation.

**Tasks:**
1. [ ] Add visual-explainer entry to help SKILL.md
2. [ ] Document all CLI parameters in help
3. [ ] Add usage examples to help
4. [ ] Update tool README with:
   - Installation instructions
   - Configuration options
   - API key setup guide
   - Style customization guide
   - Example usage
5. [ ] Add troubleshooting section
6. [ ] Include sample output screenshots/descriptions

**Acceptance Criteria:**
- [ ] `/help visual-explainer` shows correct info
- [ ] README is comprehensive
- [ ] Examples are copy-paste ready
- [ ] Troubleshooting covers common issues

**Notes:**
Keep examples practical - real use cases the user would actually run.

---

### Phase 5 Testing Requirements

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage report shows >80%
- [ ] Help output is correct

### Phase 5 Completion Checklist

- [ ] All 3 work items complete
- [ ] Full test suite passes
- [ ] Documentation is complete
- [ ] No known bugs remaining

---

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 1.1 | Phase 1.2, 1.3, 1.4 | All Phase 1 items are independent |
| Phase 2.1 | Phase 2.2, 2.3 | Models, style loader, analyzer are independent |
| Phase 3.1 | Phase 3.2 | Gemini and Claude integrations are independent |
| Phase 4.1 | Phase 4.2 | Output and CLI can develop in parallel |
| Phase 5.1 | Phase 5.2, 5.3 | Tests and docs are independent |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Gemini API rate limits | Medium | Medium | Implement conservative concurrency (3), exponential backoff |
| Safety filter false positives | Low | Medium | Log blocked attempts, allow retry with modified prompt |
| Large documents exceed context | Low | Medium | Summarize before analysis, warn user |
| Claude evaluation inconsistent | Medium | Low | Use structured JSON output, validate against schema |
| Style files missing | Low | High | Validate on startup, provide clear error with fix instructions |

---

## Success Metrics

- [ ] All 5 phases completed
- [ ] All acceptance criteria met
- [ ] Test coverage >80% on core modules
- [ ] Full pipeline generates images from sample document
- [ ] Resume from checkpoint works
- [ ] Help documentation is complete
- [ ] Cost estimates match actual usage (within 20%)

---

## Appendix: Requirement Traceability

| Requirement | Source | Phase | Work Item |
|-------------|--------|-------|-----------|
| Project structure | §2.1 | 1 | 1.1 |
| Configuration system | §5.1, §5.2 | 1 | 1.2 |
| API key setup | §6.2 | 1 | 1.3 |
| Bundled styles | §5.3 | 1 | 1.4 |
| Data models | §3, §8 | 2 | 2.1 |
| Style loading | §5.3 | 2 | 2.2 |
| Concept analysis | §3 Phase 2 | 2 | 2.3 |
| Image generation | §3 Phase 5, §6.3 | 3 | 3.1 |
| Image evaluation | §3 Phase 6, §6.4 | 3 | 3.2 |
| Prompt generation/refinement | §3 Phase 4, 7 | 3 | 3.3 |
| Output organization | §3 Phase 8 | 4 | 4.1 |
| CLI orchestration | §4.1-4.4 | 4 | 4.2 |
| SKILL.md | §12.1 | 4 | 4.3 |
| Unit tests | §10.1 | 5 | 5.1 |
| Integration tests | §10.2 | 5 | 5.2 |
| Documentation | §12.4 | 5 | 5.3 |

---

*Implementation plan generated by Claude on 2026-01-18*
*Source: /create-plan based on IMAGE_GEN_PLAN.md*
