---
description: Version history and release notes for personal-plugin
---

# Changelog

All notable changes to personal-plugin will be documented in this file.

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
