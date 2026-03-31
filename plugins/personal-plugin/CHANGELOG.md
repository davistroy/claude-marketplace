# Changelog

All notable changes to personal-plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.6.0] - 2026-03-31

### Added
- New `brain-entry` skill — Send captures to Open Brain (summarize sessions, log decisions, capture ideas) via the captures API

## [6.5.0] - 2026-03-31

### Added
- New `ultra-plan` skill — Structured implementation planning for bug lists, feature requests, or change sets with deep investigation and interaction mapping
- New `spark-recon` skill — Periodic intelligence scan of DGX Spark inference performance landscape
- Plan archive-on-completion workflow in `plan-next` (P9) and `create-plan` (auto-detect completed plans)
- Cross-references between planning commands (`create-plan`, `plan-improvements`, `ultra-plan`)
- Pipeline component notes in `define-questions` and `ask-questions` pointing to `/finish-document`

### Changed
- Renamed `validate-and-ship` → `release-plugin` for clarity (plugin-specific release workflow)
- Updated Anthropic model default from `claude-opus-4-5-20251101` to `claude-opus-4-6-20250725`
- Updated all provider date annotations to 2026-03-31 (research-topic, visual-explainer, accessibility-annotator)
- Replaced hardcoded machine paths in `accessibility-annotator` and `explain-project` with environment variable references (`$IMAGE_STYLE_JSON`, `$DOC_STYLE_GUIDE`, `$DOC_BUILDER_PATH`, etc.)

### Fixed
- Help skill: added missing `spark-recon`, replaced `/SKILL` placeholder examples with real invocations
- CLAUDE.md: removed false "dynamic Glob-based discovery" claims, added missing skills to structure listing
- CONTRIBUTING.md: corrected dynamic help references to match static table reality

## [6.2.0] - 2026-03-23

### Added
- New `leak-risk-audit` skill — Audit datasets for proprietary information leaks before sharing with public/cloud services
- New `spec-to-prototype` skill — Build visual HTML/CSS prototypes from spec documents, design system references, or wireframe descriptions
- Evaluation framework (`evals/`) with eval specs for all 23 commands and 11 skills, plus test fixtures

### Fixed
- `spec-to-prototype` skill: Added missing language specifier to code block

## [6.1.0] - 2026-03-21

### Fixed
- CLAUDE.md: Added missing evaluate-pipeline-output skill to repository structure listing
- flag-consistency.md: Corrected --focus dimensions for /assess-document and /review-arch to match actual commands
- api-key-setup.md: Clarified TROY vs BWS_ACCESS_TOKEN env var relationship
- research-models.md: Fixed invalid OpenAI "xhigh" effort level to "high"
- templates/planning.md: Aligned effort format with plan-template.md (S/M/L with file count + LOC)
- analyze-transcript.md: Fixed example filenames to match documented naming convention
- bump-version.md: Added handling for missing CHANGELOG.md and absent [Unreleased] header
- remove-ip.md: Added WebSearch to allowed-tools frontmatter (was referenced but missing)
- plan-gate/SKILL.md: Replaced non-existent EnterPlanMode/AskUserQuestion tool references with natural language
- research-topic/SKILL.md: Replaced AskUserQuestion references with natural language
- test-project.md: Clarified Agent vs Task tool usage for parallel test execution
- clean-repo.md, consolidate-documents.md, review-arch.md: Removed phantom --output flag references from JSON Output sections

### Added
- effort: high frontmatter to security-analysis, summarize-feedback, visual-explainer skills
- Performance section to evaluate-pipeline-output skill

## [6.0.0] - 2026-03-21

### Added
- `argument-hint` frontmatter field to all 22 commands that accept arguments
- `effort` frontmatter field to 10 planning commands/skills (low/medium/high/max)
- `disable-model-invocation: true` to ship and validate-and-ship skills
- Hooks system (`hooks/hooks.json`) with Stop and SessionStart workflow automation hooks
- Deep investigation planning philosophy: root cause analysis, interrelationship mapping, architectural coherence
- Examples sections to analyze-transcript, create-plan, finish-document commands
- Performance sections to develop-image-prompt, review-pr commands

### Changed
- Standardized "Proactive Triggers" section naming in plan-gate and security-analysis skills
- Updated all planning commands/skills with integrated fix philosophy (no isolated patches)
- plugin.json now registers hooks via `"hooks": "./hooks/hooks.json"`

## [5.1.2] - 2026-03-21

### Changed
- Added deep investigation philosophy to all planning commands and skills: root cause analysis, interrelationship mapping, and architectural coherence requirements
- Updated create-plan with "Deep Investigation Before Planning" execution guidelines
- Updated plan-improvements Phase 1 with root cause and interrelationship analysis mandate
- Updated review-arch Phase 4 with cross-cutting analysis before remediation roadmap construction
- Updated plan-next recommendation output to reference integrated planning approach
- Updated review-intent realignment actions to require grouped, root-cause-driven corrective actions
- Updated implement-plan with implementation philosophy section for architectural coherence
- Updated plan-gate routing descriptions for /plan-improvements and /create-plan paths
- Updated prime Phase 6 recommendations to require holistic finding review before action planning
- Updated plan-template executive summary and overview to reference integrated solutions

## [5.1.1] - 2026-03-13

### Changed
- Rewrote evaluate-pipeline-output skill for resilience to pipeline code changes
- Skill now discovers schemas, field names, thresholds, and config at runtime from pipeline source code
- Added Finding Analysis Protocol mandating symptom/issue/root-cause/cascade/fix/verification per finding
- Added Infrastructure Health phase (LLM failure rates, HDBSCAN success, processing time)
- Added Stage A ingestion evaluation (previously unchecked)
- Added regression analysis via --baseline flag for run-over-run comparison
- Added --mode test|validation|production for severity calibration
- Added causal chain summary consolidating findings with shared root causes

## [5.1.0] - 2026-03-04

### Added
- Performance sections to all 13 commands and 6 skills missing them
- Examples sections to 4 commands and 3 skills missing them
- Ruff linting/formatting CI job with `ruff.toml` configuration
- `pip-audit` dependency security scanning in CI
- Windows CI test matrix support
- `pytest.ini` for local test discovery
- Type hints to feedback-docx-generator utility functions

### Changed
- Markdown linting now blocking in CI (removed `|| true`)
- Standardized example section headings to `## Examples`

### Fixed
- Removed 5 committed `.coverage` files from git tracking
- Dead code removal in bpmn2drawio converter.py
- TROUBLESHOOTING.md content review

## [5.0.0] - 2026-03-04

### Breaking Changes
- Deprecated `/convert-hooks` — use Claude ad-hoc for bash-to-PowerShell conversion
- Deprecated `/setup-statusline` — use built-in statusline-setup agent
- Deprecated `/check-updates` — use `/validate-plugin --check-updates`

### Added
- `/validate-plugin --check-updates` — version drift detection (folded from check-updates)
- `/review-pr` MCP GitHub integration — line-level review comments
- `--json` output flag on `/consolidate-documents`, `/clean-repo`, `/review-arch`
- `--focus` dimension filter on `/assess-document`, `/review-arch`
- Dynamic help skill — auto-discovers commands/skills at runtime
- Shared plan template at `references/plan-template.md`
- Environment variable overrides for model names and Bitwarden project ID

### Fixed
- `/test-project` missing Read/Write/Edit/Glob/Grep in allowed-tools (command was non-functional)
- `summarize-feedback` skill missing Bash for Python execution
- `security-analysis` skill missing Write for report generation
- `prime` skill contradictory allowed-tools (had Write, claimed read-only)
- `ship` skill missing Read/Edit for auto-fix loop
- Schema inconsistency: `generated_at` vs `generated_date` standardized
- Severity label mismatch in `/review-pr` standardized to 5-level scale

### Changed
- Extracted reference tables from `research-topic`, `bpmn-generator`, `validate-plugin` to reduce prompt length
- Tightened `new-command` and `new-skill` allowed-tools (removed unnecessary Bash)
- Added `Bash(git:*)` to `review-intent` and `create-plan` for git history access
- `plan-improvements` security dimension scoped to static analysis

## [4.1.0] - 2026-02-28

### Added
- `allowed-tools` frontmatter to all 28 commands/skills that lacked them
- `Related Commands` sections to all 23 commands
- Proactive trigger sections to all 10 skills
- Error handling tables to all 36 command/skill files
- `references/api-key-setup.md` — extracted Bitwarden-based key setup workflow
- `references/flag-consistency.md` — comprehensive flag reference across all commands
- `plan-gate` skill for assessing task complexity and routing to right planning approach

## [3.13.0] - 2026-01-27

### Added
- `/summarize-feedback` skill: Synthesize employee feedback from Notion Voice Captures into a professional .docx assessment document
- Bundled `feedback-docx-generator` Python tool for .docx document generation

## [3.10.0] - 2026-01-19

### Added
- Phase 0: Deep Repository Analysis in `/clean-repo` command (required before cleanup)
- `--docs-only` flag for documentation-focused repository cleanup

### Changed
- `/clean-repo` now requires thorough codebase understanding before any actions
- Documentation sync is now action-oriented (applies updates immediately)
- Streamlined command structure with verification checklists

## [3.9.0] - 2026-01-19

### Added
- Non-interactive mode detection for visual-explainer CLI (enables use from scripts, CI, and agents)
- Windows console encoding fixes with ASCII spinner fallback for legacy terminals
- Unicode support detection with graceful degradation

### Changed
- Visual-explainer now returns sensible defaults when stdin is not a TTY
- API key setup wizard skips prompts in non-interactive mode with clear error messages

## [3.8.0] - 2026-01-19

### Added
- Infographic mode for visual-explainer (`--infographic` flag)
- Information-dense 11x17 inch page generation
- Multi-page content distribution algorithm

### Fixed
- Removed YAML frontmatter from CHANGELOG.md that could cause plugin parser issues
- Fixed potential Bun crash caused by CHANGELOG.md being incorrectly parsed as a command file

## [3.7.0] - 2026-01-18

### Added
- Visual Concept Explainer skill (`/visual-explainer`) - transforms text/documents into AI-generated explanatory images
- Gemini Pro 3 integration for 4K image generation
- Claude Sonnet Vision integration for quality evaluation
- Iterative refinement with escalating strategies (up to 5 attempts)
- Checkpoint/resume support for long-running generations
- Bundled styles: professional-clean and professional-sketch
- Multiple input formats: .md, .txt, .docx, .pdf, URLs
- Comprehensive test suite (195 tests)

## [3.6.0] - 2026-01-18

### Added
- Enhanced terminal UI for research-orchestrator with Rich library integration
- StreamingUI mode for real-time progress visibility in piped/captured contexts
- Smart UI mode detection (Rich, Streaming, or Simple fallback)
- Phase-specific status icons and spinner animations
- Beautiful summary panel on research completion

### Changed
- Default timeout increased from 720s (12 min) to 1800s (30 min) for deep research APIs
- Forced unbuffered Python output for immediate status visibility

### Fixed
- Windows console encoding compatibility (ASCII fallback for cp1252)
- Unicode/emoji support detection with graceful degradation

## [3.5.0] - 2026-01-18

### Added
- Audience profile detection from CLAUDE.md files
- API key setup wizard with step-by-step guidance
- Rich UI progress display (initial implementation)
- Bug reporter for detecting research anomalies
- Parallel dependency checking during clarification phase

## [3.4.0] - Previous

- Earlier versions (see git history)
