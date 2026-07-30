# Changelog

All notable changes to bpmn-plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.4.0] - 2026-07-29

### Changed
- `bpmn-generator`: the simulated `help`/`status`/`back`/`skip`/`quit` REPL is gone (494 → 442 lines). `skip` and `quit` are native controls; `status` is redundant in a visible transcript. Its Question Format and Auto-Accept blocks now defer to `references/clarification-patterns.md` instead of duplicating them.
- `references/clarification-patterns.md`: all 22 question blocks plus both normative blocks converted to `AskUserQuestion`. Auto-accept is preserved via the free-text **Other** box — nothing native absorbs the old `E)` slot, so dropping it would have removed a real capability.

### Fixed
- `bpmn-to-drawio`: the skill's own `HAS_DI` branch re-taught the partial-DI layout bug the tool fixed in 4.3.x, silently corrupting diagram layout. Deleted — the skill now delegates to `--layout auto`.
- `cli.py --layout` help said `auto` preserves DI "when present"; the resolver gates on *complete* DI (every element positioned).

## [4.3.1] - 2026-07-16

### Fixed
- **Partial-DI files no longer strand shapes at the origin (#143).** The 4.3.0 `auto` default resolved to `preserve` whenever *any* shape carried DI (`has_di_coordinates` is all-or-nothing), so a file where only some elements had DI coordinates left the DI-less elements at (0,0). `auto` now resolves to `preserve` only when DI is **complete** (every element positioned) via the new `BPMNModel.has_complete_di_coordinates`, and falls back to a full graphviz layout otherwise. Fully-DI (e.g. Bizagi) and non-DI behavior is unchanged.

## [4.3.0] - 2026-07-16

Integrates external contributor PR #98 (Oleksandr Panasenko / @AlexanderV) — DI-layout preservation and swimlane/label fixes for the bundled bpmn2drawio tool, rebased onto current `main` and brought up to the repo's ruff/mypy/coverage gates.

### Added
- **`auto` layout mode (now the default):** preserves a BPMN file's existing DI (Diagram Interchange) coordinates when present, and falls back to graphviz auto-layout when absent. Explicit `--layout graphviz` / `--layout preserve` behave as before.
- Geometric lane/pool assignment: when lanes declare no `flowNodeRef`, membership is inferred from DI bounds, constrained to the element's own process to avoid cross-process misassignment.
- Data stores render as cylinders with inherited labels; event-based and complex gateway styles added to the theme path.

### Fixed
- DI-carrying files (e.g. Bizagi exports) whose lanes have no `flowNodeRef` no longer collapse every shape into a single pool while graphviz reflows shapes that already had valid coordinates — the root cause of heavily-overlapping output.
- Empty phantom pools (no lanes, no elements) that overlapped content are now skipped.
- Event/gateway labels placed below the shape so long names no longer overflow the small circles/diamonds; data-element labels placed below; pool title strip aligned with the lane inset.

### Tests
- 32 new tests (parser geometry, auto-layout resolution, phantom-pool skipping, label alignment). Integrated suite: 636 passing, 92.83% branch coverage; mypy clean (baseline 0); ruff check + format clean.

## [4.2.0] - 2026-07-16

### Added
- `references/bpmn2drawio-reference.md` extracted from `bpmn-to-drawio` skill body as part of a progressive-disclosure pass
- `tests/test_xxe.py` (3 tests) covering the XXE hardening below

### Changed
- `bpmn-generator`, `bpmn-to-drawio`: added explicit "Do NOT use for" negative scope disambiguating the two skills from each other and from personal-plugin's `explain-project`/`spec-to-prototype`
- `bpmn-to-drawio`: trimmed toward the ~500-line progressive-disclosure budget
- CI: per-tool `tests/` lint pass (28 hidden ruff errors fixed), mypy count-ratchet against existing baseline, `schemas/plugin.json` tightened (`tools` field forbidden, stricter version pattern, `additionalProperties: false`), GitHub Actions pinned to commit SHAs

### Fixed
- `tools/bpmn2drawio/src/bpmn2drawio/parser.py`: hardened lxml parser against XXE (`resolve_entities=False`, `no_network`, DTD loading disabled); `lxml` capped to `>=5.0,<7`
- `tools/bpmn2drawio/requirements-lock.txt`, `requirements-dev-lock.txt`: regenerated for patched CVEs (lxml 6.1.1 among others)

## [4.1.0] - 2026-05-14

### Changed
- Coordinated minor version bump alongside marketplace v3.2.0, personal-plugin v9.2.0, slide-gen v1.1.0 (release cadence; no bpmn-plugin-specific functional changes)

## [4.0.0] - 2026-04-21

### Removed
- `help` skill — superseded by native `/help`

## [3.4.0] - 2026-03-31

### Fixed
- `hooks.json` (repo-wide) migrated from deprecated array format to record-keyed-by-event format

### Changed
- Coordinated bump alongside marketplace v1.6.0, personal-plugin v6.7.0

## [3.3.0] - 2026-03-31

### Changed
- Coordinated bump alongside marketplace v1.5.0, personal-plugin v6.6.0 (brain-entry skill docs)

## [3.2.0] - 2026-03-31

### Changed
- Coordinated bump alongside marketplace v1.4.0, personal-plugin v6.5.0

## [3.1.0] - 2026-03-21

### Fixed
- `bpmn-generator`: question numbering overlap (Phase 3 and Phase 4 both claimed Q11)
- `help` skill: added maintenance note to Mode 2 hardcoded references

## [3.0.0] - 2026-03-21

### Added
- `${CLAUDE_PLUGIN_ROOT}` environment variable support in `bpmn-to-drawio` tool paths — enables reliable marketplace installation
- `references/archive/` directory for historical reference documents

### Changed
- Archived `converter-fixes-20260118-123946.md` to `references/archive/` (historical record; fixes already in codebase)
- `argument-hint` frontmatter field added to all 3 skills

## [2.4.0] - 2026-03-04

### Added
- Performance sections to all 3 skills (`help`, `bpmn-generator`, `bpmn-to-drawio`)

### Fixed
- Dead code removal in `bpmn2drawio` `converter.py` (`merge_theme_with_config` unused call)

## [2.3.0] - 2026-03-04

### Added
- `allowed-tools` declarations on all 3 skills (`bpmn-generator`, `bpmn-to-drawio`, `help`)

### Changed
- Extracted BPMN element mapping tables to `references/bpmn-elements.md`
- `bpmn-generator` SKILL.md reduced from ~620 to <500 lines

## [2.2.0] - 2026-02-16

### Added
- `bpmn2drawio` test coverage expanded to 544 tests / 92% (Phase 3 of internal improvement plan)

### Fixed
- `bpmn2drawio`: infinite loop in layout engine for cyclic graphs (#59)
- `bpmn2drawio`: converter edge cases for multi-pool diagrams (#46)

### Changed
- Phase 1-6 internal quality pass: dependency hygiene, CI pipeline hardening, refactoring and ADRs, final coverage sweep

## [2.1.0] - 2026-01-17

### Changed
- Version bump for consistency with personal-plugin release cycle

## [2.0.0] - 2026-01-17

### Changed
- Major version bump for breaking changes in plugin structure

## [1.8.0] - 2026-01-17

### Added
- Visual testing infrastructure for `bpmn2drawio`

### Fixed
- Visual bug fixes for layout and positioning (#24)
- `bpmn2drawio`: BFS rank assignment now properly re-queues successors when rank improves
- `bpmn2drawio`: fallback positions added for elements not positioned by graphviz
- `bpmn2drawio`: subprocess-relative coordinate adjustment for proper Draw.io rendering
- `bpmn2drawio`: pool parent assignment for laneless pools
- Removed unsupported `tools` field from `plugin.json`
- Added required `name` field to skill frontmatter for discovery

### Changed
- Skills restructured to nested `skills/<name>/SKILL.md` format (from flat `.md` files)

## [1.7.0] - 2026-01-15

### Changed
- Version bump for consistency with personal-plugin release cycle; `help.md` updated for `--scorecard` flag parity

## [1.6.0] - 2026-01-14

### Added
- `help.md` skill with comprehensive skill reference
- `--preview` flag support referenced from `bpmn-generator.md` and `bpmn-to-drawio.md`
- Dependency verification guidance for external tools (graphviz) in `bpmn-to-drawio.md`

## [1.5.0] - 2026-01-14

### Added
- Bundled `bpmn2drawio` Python tool directly in `bpmn-plugin` (no external package dependency)
- Auto-detect and install dependencies in the `bpmn-to-drawio` skill

### Fixed
- Run bundled `bpmn2drawio` tool directly without requiring `pip install`
- Python 3.14 / lxml compatibility fix
- Fallback layout scaling and complex-scenario test fixes
- Positioning of elements without DI coordinates
- Visual layout issues with lanes and element positioning
- Lane-to-pool assignment now correctly tracks `process_id` for proper pool matching
- Lane Y positions now start at 0 within each pool instead of cumulative across all pools
- Subprocess parsing order fixed to set `_is_subprocess` before generic element handling
- Boundary events now correctly parented to their attached subprocess with relative coordinates
- Added missing `boundaryEvent`, `subProcess`, and `callActivity` styles to `themes.py`

### Changed
- `bpmn2drawio` test coverage improved from 84% to 92% (49 additional tests, including a comprehensive complex-scenario fixture)

## [1.4.0] - 2026-01-13

### Changed
- Updated examples with an AI Community Management Process sample

## [1.3.0] - 2026-01-12

### Added
- Integrated `bpmn2drawio` Python tool into the `bpmn-to-drawio` skill

### Changed
- BPMN-to-DrawIO Conversion Standard reference updated to v1.1

## [1.2.0] - 2026-01-12

### Changed
- Version bump for consistency with marketplace release

## [1.1.0] - 2026-01-12

### Added
- `bpmn-to-drawio` skill for converting BPMN XML to Draw.io format

## [1.0.0] - 2026-01-12

### Added
- Initial `bpmn-plugin`: BPMN 2.0 XML generation from natural language descriptions or structured markdown business process documents
