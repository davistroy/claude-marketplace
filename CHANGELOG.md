# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/davistroy/claude-marketplace/compare/v1.7.0...HEAD
[1.7.0]: https://github.com/davistroy/claude-marketplace/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/davistroy/claude-marketplace/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/davistroy/claude-marketplace/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/davistroy/claude-marketplace/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/davistroy/claude-marketplace/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/davistroy/claude-marketplace/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/davistroy/claude-marketplace/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/davistroy/claude-marketplace/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/davistroy/claude-marketplace/releases/tag/v1.0.0
