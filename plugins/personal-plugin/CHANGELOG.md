# Changelog

All notable changes to personal-plugin will be documented in this file.

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
