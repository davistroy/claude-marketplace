# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [personal-plugin 4.1.0] - 2026-02-28

### Added
- `allowed-tools` frontmatter to all 28 commands/skills that lacked them
- `Related Commands` sections to all 23 commands
- Proactive trigger sections to all 10 skills
- Error handling tables to all 36 command/skill files
- `references/api-key-setup.md` — extracted Bitwarden-based key setup workflow
- `references/flag-consistency.md` — comprehensive flag reference across all commands
- `plan-gate` skill for assessing task complexity and routing to right planning approach

### Changed
- Rewrote `plan-next.md` from scratch (47 → 234 lines) with priority decision matrix and plan-awareness
- Rewrote `setup-statusline.md` with 4-phase approach, safety checks, and `--dry-run`/`--uninstall` flags
- Overhauled `consolidate-documents.md` with standardized input flow and 4 new flags
- Restructured `review-arch.md` with task-based assessment and Architecture Scorecard
- Reimplemented `check-updates.md` with true remote version checking via GitHub API
- Overhauled `security-analysis` skill with input validation, trigger conditions, and structured error handling
- Expanded `convert-hooks.md` with limitation warnings, before/after examples, and `--validate` flag
- Expanded `convert-markdown.md` with analysis-driven flag selection and 4 new flags
- Expanded `develop-image-prompt.md` with `--dimensions` flag (8 presets) and 8 style presets
- Improved `test-project.md` safety: selective staging replaces `git add -A`, PR-only default (merge requires `--auto-merge`)
- Fixed `ship` skill phase numbering and updated Co-Authored-By to `Claude Opus 4.6`
- Replaced hardcoded plugin lists with dynamic filesystem scanning in bump-version, check-updates, validate-plugin

### Fixed
- Removed 37 dead references to non-existent `scripts/` and `schemas/` across 17 files
- Fixed secrets policy violations in research-topic and visual-explainer (removed API key wizards, use `/unlock` instead)
- Fixed shell injection vulnerability in `unlock` skill (safe quoting, key name validation)
- Fixed `scaffold-plugin.md` skills path references (`help.md` → `help/SKILL.md`)
- Fixed `define-questions.md` phantom schema references
- Fixed `finish-document.md` resume contradiction
- Fixed `validate-plugin.md` duplicate section numbering
- Fixed `remove-ip.md` trigger phrase removal
- Removed contradictory input patterns in consolidate-documents

## [personal-plugin 4.0.0] - 2026-02-16

### Added
- `/review-intent` command: Determine original project intent and compare against current implementation
- `/prime` skill: Evaluate codebase to produce detailed report on project purpose, health, status, and next steps
- `/implement-plan` parallel execution: PATH B launches independent work items concurrently via background subagents
- `/create-plan` and `/plan-improvements` append mode: If IMPLEMENTATION_PLAN.md exists, new phases are appended with renumbered items instead of overwriting

### Changed
- `/implement-plan` restructured with dual execution paths (PATH A: sequential, PATH B: parallel) and parallelization map built at startup
- README.md updated with all 9 skills (was showing only 3) and 26 commands
- CLAUDE.md repository structure updated with review-intent command and prime skill
- CLAUDE.md Patterns Used section now covers all 26 commands across 14 pattern categories
- SECURITY.md updated with multi-provider API data flow, security-relevant skills, and current third-party dependencies
- TROUBLESHOOTING.md Python version requirement corrected (3.8 → 3.10)
- QUICK-REFERENCE.md expanded with 5 new flags and a skills section
- Help skill error section updated with complete command and skill lists
- 11 code blocks in bpmn-plugin tool docs fixed with language specifiers

### Fixed
- Documentation drift: 22 fixes across 8 files for stale references, missing features, and incorrect claims
- SECURITY.md "No Audit Trail" claim corrected — audit logging available via `--audit` flag

## [personal-plugin 3.14.0] - 2026-02-15

### Changed
- `/implement-plan` command: Removed Ralph Wiggum loop dependency, replaced with native subagent orchestration pattern
  - Main agent now acts as thin loop controller using Task tool directly
  - Added explicit "Context Window Discipline" rules table
  - Instructions use blockquoted subagent prompts with `subagent_type: "general-purpose"`
  - Progress tracking via TaskCreate/TaskUpdate instead of external loop state
  - Added "Do not stop early" directive to ensure full plan completion

## [personal-plugin 3.12.0] - 2026-01-26

### Added
- Help skill updated with `/unlock` skill listing and detailed usage documentation

### Changed
- Version bump to 3.12.0

### Removed
- `SHIP_GITEA_PLAN.md` planning document (completed, no longer needed)

## [personal-plugin 3.11.1] - 2026-01-26

### Added
- `/unlock` skill: Unlock Bitwarden vault and load project secrets into environment
  - Reads master password from `~\.claude\.env` (local, not in repo)
  - Auto-detects project name from working directory
  - Loads secrets from `dev/<project>/api-keys` in Bitwarden
  - Recovered from plugin cache (was installed but missing from source repo)

## [personal-plugin 3.11.0] - 2026-01-26

### Added
- `/ship` skill: Gitea platform support with `tea` CLI auto-detection
  - Phase 0 platform detection parses git remote to select GitHub (`gh`) or Gitea (`tea`)
  - Platform-conditional commands for PR creation, review, and merge
  - Draft PR limitation documented (tea CLI does not support `--draft`)
  - Gitea branch cleanup after merge (tea doesn't auto-delete branches)
- `/validate-and-ship` skill: Added `tea` CLI to allowed tools and stopping conditions

### Changed
- `/ship` skill: `allowed-tools` now includes `Bash(tea:*)`
- `/validate-and-ship` skill: `allowed-tools` now includes `Bash(tea:*)`
- Help skill updated with Gitea platform support notes for `/ship`

## [personal-plugin 3.8.0] - 2026-01-18

### Changed
- visual-explainer: Updated skill documentation to reflect actual CLI behavior (removed non-existent `check-ready` command)
- visual-explainer: Updated tested results with latest testing data (4 documents, 17 images, multiple formats)
- visual-explainer: Added `google-genai` to core dependency list in documentation

### Fixed
- visual-explainer: Skill documentation now matches actual tool CLI options

## [personal-plugin 3.7.2] - 2026-01-18

### Added
- visual-explainer: **Infographic mode** (`--infographic` flag) for information-dense 11x17 inch page generation
- visual-explainer: Adaptive page count (1-6 pages) based on document complexity, word count, and content types
- visual-explainer: 8 page types: Hero Summary, Problem Landscape, Framework Overview, Framework Deep-Dive, Comparison Matrix, Dimensions/Variations, Reference/Action, Data/Evidence
- visual-explainer: Zone-based layout system with explicit typography specifications (headline/subhead/body/caption)
- visual-explainer: Page templates library with predefined layouts for each page type
- visual-explainer: Content type detection (statistics, process, comparison, hierarchy, timeline, framework, narrative, list, matrix)

### Changed
- visual-explainer: Concept analyzer now produces page recommendations with zone assignments when in infographic mode
- visual-explainer: Prompt generator creates information-dense prompts with explicit text specifications
- visual-explainer: CLI displays page plan summary including page types, content focus, and compression warnings

## [personal-plugin 3.7.1] - 2026-01-18

### Fixed
- visual-explainer: Image resizing for Claude's 5MB API limit (uses 3.5MB raw limit to account for base64 encoding overhead)
- visual-explainer: Windows path sanitization - removes invalid characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`) from output folder names

### Added
- visual-explainer: google-genai and Pillow dependencies in pyproject.toml
- visual-explainer: Technical notes section in SKILL.md with API details and tested results
- visual-explainer: DOCX conversion tip and input format handling table in SKILL.md
- visual-explainer: `--json` output mode for programmatic use
- visual-explainer: Image size limit and Windows path troubleshooting sections in README.md

### Changed
- visual-explainer: Uses google-genai SDK with `gemini-3-pro-image-preview` model
- visual-explainer: Default pass threshold recommendation: 0.75-0.85 for optimal quality/iteration balance

## [bpmn-plugin 2.2.0] - 2026-01-18

### Fixed
- bpmn2drawio: Lane-to-pool assignment now correctly tracks process_id for proper pool matching
- bpmn2drawio: Lane Y positions now start at 0 within each pool instead of cumulative across all pools
- bpmn2drawio: Subprocess parsing order fixed to set _is_subprocess property before generic element handling
- bpmn2drawio: Nested subprocess parsing now correctly sets _is_subprocess property
- bpmn2drawio: Boundary events now correctly parented to their attached subprocess with relative coordinates
- bpmn2drawio: Boundary event parent resolution in generator now checks subprocess cell IDs
- bpmn2drawio: Added missing boundaryEvent, subProcess, and callActivity styles to themes.py
- bpmn2drawio: Nested subprocess parent resolution now uses element.subprocess_id attribute

### Added
- Comprehensive edge case test file (examples/comprehensive_edge_case_test.bpmn)
- Converter fixes documentation (references/converter-fixes-20260118-123946.md)

## [personal-plugin 3.6.1] - 2026-01-18

### Changed
- `/research-topic` skill: Increased default timeout from 720s to 1800s (30 minutes) for deep research APIs
- `/research-topic` skill: Enhanced terminal UI with StreamingUI for real-time progress visibility
- `/research-topic` skill: Added `PYTHONUNBUFFERED=1` and `STREAMING_UI=1` environment variables for proper output streaming

### Fixed
- Research execution now displays live progress updates instead of buffered output

## [personal-plugin 3.6.0] - 2026-01-18

### Added
- `/research-topic` skill: Rich terminal UI with progress panels and status indicators
- `/research-topic` skill: Bug reporting system with automatic anomaly detection
- `/research-topic` skill: Parallel dependency checking (runs in background during clarification)

### Changed
- `/research-topic` skill: Dependency check now starts immediately and runs parallel to user interaction

## [personal-plugin 3.5.0] - 2026-01-18

### Added
- `/research-topic` skill: Audience profile detection (Phase 1.5)
  - Searches for existing profile in project, local, and global CLAUDE.md files
  - Allows confirmation or modification of detected profile for each session
  - Prompts for profile creation if none found, with template
  - Offers to save user-provided profile to global CLAUDE.md
- `/research-topic` skill: New `--no-audience` flag to skip profile detection
- `/research-topic` skill: Interactive API key setup wizard
  - Detailed instructions for obtaining keys from Anthropic, OpenAI, and Google
  - Direct links to each provider's API key management page
  - Collects keys interactively and creates/updates .env file
  - Shows masked key confirmation after setup
  - Warns if .env is not in .gitignore

### Changed
- `/research-topic` skill: Research prompts now include detected/collected audience profile
- `/research-topic` skill: Research Brief now shows Target Audience section with profile summary
- `/research-topic` skill: Execution Summary expanded from 14 to 15 steps

## [personal-plugin 3.4.0] - 2026-01-18

### Changed
- `/research-topic` skill: Clarified tool vs Claude responsibilities with new section
- `/research-topic` skill: Phase 5 now explicitly instructs Claude to read and synthesize provider outputs
- `/research-topic` skill: Phase 6 now explicitly instructs Claude to write synthesized markdown and generate DOCX via pandoc
- `/research-topic` skill: Execution Summary expanded from 9 to 11 explicit steps

### Fixed
- Research topic skill now properly guides Claude through post-tool-execution steps (synthesis and output generation)

## [personal-plugin 3.3.0] - 2026-01-18

### Fixed
- Cache deployment issue: v3.2.0 source code fixes were not deployed to marketplace cache
  - OpenAI and Gemini providers now properly call `_status_update` method from BaseProvider
  - Users should reinstall plugin to get the fixed version: `/plugin install personal-plugin@troys-plugins --force`

## [personal-plugin 3.2.0] - 2026-01-17

### Added
- Progress updates during polling for OpenAI and Gemini deep research (every 30s)

### Changed
- Increased default timeout from 180s to 720s for deep research APIs (OpenAI/Gemini can take 5-10 minutes)
- Clarification loop now REQUIRED in `/research-topic` skill unless `--no-clarify` specified
- Model version check step changed from conditional to recommended (skip with `--skip-model-check`)

### Fixed
- OpenAI and Gemini deep research timeout failures (300s was insufficient)
- Gemini SDK experimental API warnings now suppressed
- Documentation inconsistencies for timeout values (now consistently 720s)

## [personal-plugin 3.1.0] - 2026-01-17

### Added
- `/validate-and-ship` skill - Automated pre-flight checks and shipping workflow
  - Chains `/validate-plugin`, `/clean-repo`, and `/ship` in sequence
  - Stops only on blocking errors, continues through warnings
  - Supports `--skip-validate`, `--skip-cleanup`, `--dry-run` flags
- Stale branch pruning in `/ship` skill completion phase
  - Auto-prunes remote tracking branches that no longer exist
  - Cleans local branches where upstream is gone (merged only)

### Changed
- `/ship` skill now reports pruned stale branches in completion output

## [bpmn-plugin 2.1.0] - 2026-01-17

### Changed
- Version bump for consistency with personal-plugin release cycle

## [personal-plugin 3.0.0] - 2026-01-17

### Changed
- Major version bump for breaking changes in plugin structure and command conventions

## [bpmn-plugin 2.0.0] - 2026-01-17

### Changed
- Major version bump for breaking changes in plugin structure

## [bpmn-plugin 1.8.0] - 2026-01-16

### Fixed
- bpmn2drawio: Fix BFS rank assignment to properly re-queue successors when rank improves
- bpmn2drawio: Add flow validation logging in layout engine for debugging
- bpmn2drawio: Add fallback positions for elements not positioned by graphviz
- bpmn2drawio: Add subprocess-relative coordinate adjustment for proper Draw.io rendering
- bpmn2drawio: Improve connected element detection to include subprocess internals
- bpmn2drawio: Add pool parent assignment for laneless pools

## [2.5.0] - 2026-01-16

### Added
- `/create-plan` command for generating IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD)
  - Auto-discovers requirements documents in project
  - Synthesizes requirements across multiple documents
  - Generates phased implementation plan with work items and acceptance criteria
  - Includes requirement traceability matrix
- `/implement-plan` command for executing IMPLEMENTATION_PLAN.md via orchestrated subagents
  - Uses subagent orchestration pattern for context-efficient execution
  - Spawns subagents for implementation, testing, and documentation
  - Automatic test-fix loop until all tests pass
  - Updates PROGRESS.md and LEARNINGS.md tracking files
  - Commits after each work item, creates PR on completion

### Changed
- Updated CLAUDE.md with new commands and "Orchestration commands" pattern category
- Planning commands now include create-plan, plan-improvements, and plan-next

## [2.4.0] - 2026-01-15

### Added
- `schemas/command.json` - JSON Schema for command frontmatter validation
- Modular pattern files in `plugins/personal-plugin/references/patterns/`:
  - `naming.md` - File and command naming conventions
  - `validation.md` - Input validation and error handling patterns
  - `output.md` - Output files, directories, preview patterns
  - `workflow.md` - State management, resume, session patterns
  - `testing.md` - Argument testing and dry-run patterns
  - `logging.md` - Audit logging and progress reporting patterns
- `--strict` flag to `/validate-plugin` for failing on any pattern violation
- `--report` flag to `/validate-plugin` for generating detailed compliance reports
- Schema Validation Summary section to Q&A commands (define-questions, ask-questions, finish-document)
- 3 new command templates: `synthesis.md`, `conversion.md`, `planning.md`
- `docs/PLUGIN-DEVELOPMENT.md` - Step-by-step plugin developer onboarding guide
- Integration tests for validate-plugin and bump-version commands (37 new tests)
- Test fixtures for valid and invalid plugin structures
- "Common Development Mistakes" section in TROUBLESHOOTING.md (7 documented mistakes)
- `.github/workflows/validate.yml` - CI/CD validation pipeline with plugin validation, markdown linting, and help sync checks
- `--scorecard` flag to `/validate-plugin` for plugin maturity assessment (4 levels)
- Interactive parameter prompting to `/define-questions` and `/assess-document` with `--no-prompt` flag
- `QUICK-REFERENCE.md` - Single-page quick reference card for plugin developers (under 100 lines)

### Changed
- README command tables now use natural sentence truncation and hyperlink to source files
- BPMN plugin help.md now includes full descriptions with operating modes and examples
- Marketplace versioning decoupled from plugin versions (marketplace_version: 1.0.0)
- Pre-commit hook now blocks commits with new commands not documented in help.md
- Generator commands (assess-document, define-questions, analyze-transcript) now auto-create output directories
- `common-patterns.md` converted to index linking to modular pattern files
- All 5 command templates updated with explicit section order markers and pattern file references
- `/validate-plugin` now includes Phase 7: Pattern Compliance Checks
- Q&A commands now have uniform `--force` flag behavior and validation status output
- `/new-command` now offers 8 template options (added synthesis, conversion, planning)
- CONTRIBUTING.md now links to the plugin developer onboarding guide
- README.md now includes CI badges and links to QUICK-REFERENCE.md
- `/validate-plugin` now supports `--scorecard` for maturity assessment

## [2.3.0] - 2026-01-15

### Added
- `/remove-ip` command for sanitizing documents by removing company identifiers and intellectual property
  - Supports STANDARD mode (preserve context) and STRICT mode (maximum redaction)
  - Auto-detects company name from document content
  - Generates detailed redaction log with risk categorization
  - Mosaic attack protection in STRICT mode
  - Optional web research for public information verification

## [2.2.0] - 2026-01-15

### Added
- `WORKFLOWS.md` - Comprehensive workflow documentation for chaining commands
- `TROUBLESHOOTING.md` - Solutions for 19 common issues with symptom/cause/solution format
- `SECURITY.md` - Security model documentation and vulnerability reporting process
- `schemas/plugin.json` - JSON Schema for plugin.json with dependency support
- Integration test suite for Q&A workflow chain (30 tests)
- Shared test infrastructure (`tests/conftest.py`, `tests/helpers/`)
- GitHub Actions workflow for running tests on push/PR
- `--preview` flag to `/define-questions`, `/analyze-transcript`, `/bpmn-generator`
- `--force` flag to Q&A commands for bypassing schema validation
- `--audit` flag to `/clean-repo` and `/ship` for optional JSON audit logging
- Workflow state management with resume support for interrupted Q&A sessions
- Plugin namespace support (`/personal-plugin:command-name` syntax)
- Plugin dependency declaration support with semver version requirements
- Dependency verification for external tools (pandoc, graphviz) with platform-specific instructions

### Changed
- Updated `schemas/answers.json` with status and last_question_answered fields
- Enhanced `/validate-plugin` with namespace collision detection and dependency validation
- Added runtime schema validation to Q&A chain commands
- Extended `common-patterns.md` with 6 new patterns (dependency verification, performance expectations, schema validation, argument testing, output preview, workflow state management, audit logging)
- Added testing guidance to `CONTRIBUTING.md`
- Added performance expectations to long-running commands (`/plan-improvements`, `/test-project`, `/review-arch`)

### Fixed
- Documentation links in README.md now point to new WORKFLOWS.md, TROUBLESHOOTING.md, SECURITY.md

## [2.1.0] - 2026-01-14

### Added
- `/new-command` command for generating new command scaffolds from templates
- `/scaffold-plugin` command for creating new plugin directory structures
- `/check-updates` command for checking plugin version updates
- JSON schemas for command chain contracts (`schemas/questions.json`, `schemas/answers.json`)
- Command templates for 5 pattern types (read-only, interactive, workflow, generator, utility)
- `scripts/generate-help.py` for automated help.md generation
- `scripts/update-readme.py` for automated README command table updates
- `--dry-run` flag to `/ship`, `/clean-repo`, and `/bump-version` commands
- `--format` flag to `/define-questions` (json|csv), `/assess-document` (md|json), `/analyze-transcript` (md|json)
- Standard session commands (help, status, back, skip, quit) to all interactive commands
- Issue severity levels standardization (CRITICAL, WARNING, SUGGESTION)
- Standard argument validation error formats

### Changed
- `/consolidate-documents` now outputs to `reports/` directory
- `/develop-image-prompt` now outputs to `reports/` directory
- Extended pre-commit hook with help.md sync and timestamp format validation
- Updated CLAUDE.md with Utility commands pattern category
- All assessment commands now use consistent severity naming

### Fixed
- Output location consistency across all commands
- Argument validation messages now follow standard format

## [2.0.0] - 2026-01-14

### Changed
- Enhanced `/ship` skill with auto-review, fix loop, and merge workflow
  - Automatically reviews PR for security, performance, code quality, test coverage, and documentation
  - Fixes CRITICAL and WARNING issues automatically (up to 5 attempts)
  - Squash merges PR when all blocking issues resolved
- Improved bpmn2drawio test coverage from 87% to 92%

## [1.7.0] - 2026-01-14

### Added
- `/help` skill in personal-plugin with comprehensive command reference
- `/help` skill in bpmn-plugin with skill reference
- Documentation about help skill maintenance in CLAUDE.md and CONTRIBUTING.md

### Changed
- Renamed all commands to consistent action-object pattern:
  - `arch-review` → `review-arch`
  - `doc-assessment` → `assess-document`
  - `transcript-analysis` → `analyze-transcript`
  - `next-step` → `plan-next`
  - `cleanup` → `clean-repo`
  - `consolidate` → `consolidate-documents`
  - `wordify` → `convert-markdown`
  - `image-prompt` → `develop-image-prompt`
  - `troy-statusline` → `setup-statusline`
  - `fully-test-project` → `test-project`
- Renamed `help-commands` skill to `help`
- Merged `doc-review` command into `clean-repo` (enhanced Phase 3)
- Updated `review-arch` description to clarify it's for quick audits vs `plan-improvements`

### Removed
- `doc-review` command (merged into `clean-repo`)

## [1.6.0] - 2026-01-14

### Added
- `bump-version` command for automated version bumping across plugin files
- `validate-plugin` command for plugin structure and content validation
- `review-pr` command for structured PR review with security/performance analysis
- `help-commands` skill for command discovery and help system
- `references/common-patterns.md` with shared patterns documentation
- `CONTRIBUTING.md` with contributor guidelines
- `scripts/pre-commit` hook for validating plugin changes

### Changed
- Standardized timestamp format to `YYYYMMDD-HHMMSS` across all commands
- Added Input Validation sections to all argument-accepting commands
- Updated CLAUDE.md with Output Locations and Timestamp Format conventions
- Improved bpmn2drawio test coverage from 84% to 92% (49 additional tests)

### Fixed
- Removed forbidden `name` field from bpmn-generator.md and bpmn-to-drawio.md frontmatter
- Updated README.md with all 15+ commands (was missing 5)

## [1.5.0] - 2025-01-14

### Added
- `plan-improvements` command for generating improvement recommendations with phased implementation plan
- `fully-test-project` command for ensuring 90%+ test coverage, running tests, fixing failures, and merging PR

## [1.4.1] - 2025-01-10

### Fixed
- Remove name field from frontmatter to fix command discovery in personal-plugin
- Sync marketplace.json version with personal-plugin (1.1.0 to 1.4.0)

## [1.4.0] - 2025-01-09

### Added
- `image-prompt` command for AI image generation prompts from content
- `wordify` command for markdown to Word document conversion
- `consolidate` command for merging multiple document versions

### Fixed
- bpmn2drawio Python 3.14 / lxml compatibility fix
- bpmn2drawio fallback layout scaling and complex test fixes
- bpmn2drawio positioning of elements without DI coordinates
- bpmn2drawio visual layout issues with lanes and element positioning

### Changed
- Auto-detect and install dependencies in bpmn-plugin skill
- Run bundled bpmn2drawio tool directly without pip install
- Bundle bpmn2drawio Python tool in bpmn-plugin

## [1.3.0] - 2025-01-06

### Added
- Integrate bpmn2drawio Python tool into bpmn-to-drawio skill
- Update examples with AI Community Management Process

### Changed
- Update BPMN-to-DrawIO Conversion Standard to v1.1

## [1.2.0] - 2025-01-05

### Added
- `bpmn-to-drawio` skill for converting BPMN XML to Draw.io format

## [1.1.0] - 2025-01-04

### Added
- `bpmn-plugin` for BPMN 2.0 XML generation from natural language or markdown
- `cleanup` command for repository cleanup and organization
- `finish-document` command for extracting questions, answering interactively, and updating documents

### Changed
- Add YAML frontmatter to all commands
- Update README and CLAUDE.md for marketplace structure

## [1.0.0] - 2025-01-03

### Added
- Initial marketplace structure with multi-plugin format
- `personal-plugin` with core commands:
  - `arch-review` for deep architectural review
  - `doc-review` for documentation audit and cleanup
  - `transcript-analysis` for meeting transcript conversion
  - `define-questions` for extracting questions from docs
  - `ask-questions` for interactive Q&A sessions
  - `doc-assessment` for document quality evaluation
  - `next-step` for analyzing repo and recommending actions
  - `troy-statusline` for custom Windows/PowerShell status line
- `ship` skill for git workflow automation

[Unreleased]: https://github.com/davistroy/claude-marketplace/compare/v2.4.0...HEAD
[2.5.0]: https://github.com/davistroy/claude-marketplace/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/davistroy/claude-marketplace/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/davistroy/claude-marketplace/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/davistroy/claude-marketplace/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/davistroy/claude-marketplace/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/davistroy/claude-marketplace/compare/v1.7.0...v2.0.0
[1.7.0]: https://github.com/davistroy/claude-marketplace/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/davistroy/claude-marketplace/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/davistroy/claude-marketplace/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/davistroy/claude-marketplace/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/davistroy/claude-marketplace/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/davistroy/claude-marketplace/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/davistroy/claude-marketplace/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/davistroy/claude-marketplace/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/davistroy/claude-marketplace/releases/tag/v1.0.0
