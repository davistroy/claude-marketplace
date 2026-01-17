# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [personal-plugin 3.0.0] - 2026-01-17

### Added
- [Describe new features]

### Changed
- [Describe changes to existing features]

### Fixed
- [Describe bug fixes]

## [bpmn-plugin 2.0.0] - 2026-01-17

### Added
- [Describe new features]

### Changed
- [Describe changes to existing features]

### Fixed
- [Describe bug fixes]

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
  - Uses Ralph Wiggum loop pattern for context-efficient execution
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

[Unreleased]: https://github.com/davistroy/claude-marketplace/compare/v2.5.0...HEAD
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
