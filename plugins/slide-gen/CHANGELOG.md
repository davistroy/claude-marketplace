# Changelog

All notable changes to slide-gen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-07-29

### Fixed
- `build-cfa-deck`: the primary snippet used `Presentation` before importing it, and two different slide-removal implementations were both broken. One working implementation now lives in the new `references/cfa-deck-helpers.md`.
- Machine-specific asset paths replaced with a `CFA_ASSETS_DIR` override.

## [1.2.0] - 2026-07-08

Coordinated with marketplace v3.3.0, personal-plugin v10.0.0, bpmn-plugin v4.2.0 (8-phase modernization pass against current official Anthropic guidance).

### Added
- `README.md`, `LICENSE` at plugin root

### Changed
- All 8 skills (`sg-research`, `sg-outline`, `sg-draft`, `sg-optimize`, `sg-validate-graphics`, `sg-generate-images`, `sg-build`, `sg-full-workflow`, `build-cfa-deck`): body "Proactive Triggers" sections folded into frontmatter `description` per official trigger-info-in-frontmatter guidance

## [1.1.0] - 2026-05-14

### Added
- `build-cfa-deck` skill — generates complete, on-brand Chick-fil-A PowerPoint presentations from a topic prompt using the CFA "Support Now" template (64 layouts, 194 SVG icons, embedded Apercu fonts) and brand guidelines

## [1.0.1] - 2026-05-06

### Changed
- Version sync bump alongside marketplace v3.0.1 (no functional changes)

## [1.0.0] - 2026-05-05

### Added
- Initial slide-gen plugin: 7 individual pipeline-step skills (`sg-research`, `sg-outline`, `sg-draft`, `sg-optimize`, `sg-validate-graphics`, `sg-generate-images`, `sg-build`) plus `sg-full-workflow` orchestrator skill running the complete pipeline
- Wraps the external `slide-generator` (`sg`) CLI for AI-assisted presentation generation from topic to PowerPoint, including the Gemini Pro image-generation step (`sg generate-images`)
