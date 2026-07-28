# Changelog

All notable changes to personal-plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [11.2.1] - 2026-07-18

### Fixed
- `tools/task-sync`: `init` now persists `config.gitea_url` from the origin remote instead of leaving it unset (closes #173).
- `tools/task-sync`: `_build_provider` now falls back to the tea CLI config (`~/.config/tea/config.yml`) for the Gitea base URL and token when `$GITEA_URL`/`$GITEA_TOKEN` are unset, with env vars overriding tea config when both are present (closes #174).
- `skills/task-sync/SKILL.md` + config-reference docs now accurately describe this env → tea-config → unset resolution order (closes #172).

## [11.0.0] - 2026-07-16

Architecture-review hardening release (8-phase remediation; LAB_NOTEBOOK Entries 017–024 -- archived, see `docs/archive/LAB_NOTEBOOK-E017-E050.md`). MAJOR due to interface/capability changes.

### Changed (breaking)
- `tools/visual-explainer`: removed the inert `--concurrency` CLI flag + `GenerationConfig.concurrency` field (dead concurrent path; generation was always serial). *(PERF-01)*
- `allowed-tools` narrowed from unscoped `Bash` to specific `Bash(<cmd>:*)` scopes across ~16 skills + 7 commands (security-analysis, leak-risk-audit, arch-review kept broad with justification — dynamic scanners). *(SEC-05)*
- `skills/{spark-recon,jetson-recon,spark-audit,jetson-audit}`: `disable-model-invocation: true` + trust-boundary sections — fleet SSH/sudo skills are now user-invoke-only. *(SEC-01)*

### Security
- `tools/bpmn2drawio/parser.py`: hardened lxml parser (XXE); `lxml>=5.0,<7`. *(DA-01/SE-02/SEC-02)*
- `tools/visual-explainer`: SSRF guard in `concept_analyzer` (blocks private/link-local/metadata IPs, re-validates redirects); `.env` writes `chmod 0600` + warning (ADR-0003 amended); atomic durable writes + `schema_version` + full-length cache key. *(SEC-03/SEC-04/DA-02/DA-05)*
- `references/research-provider-protocols.md` + `skills/brain-entry`: curl timeouts, submit status-checks/fast-fail, 429/Retry-After, Gemini key → `x-goog-api-key` header, timestamped temp files. *(INT-01/02/03/07/09)*
- `SECURITY.md`: data-egress/confidentiality policy + supply-chain controls sections. *(RISK-03/RISK-04)*

### Added
- `## Error Handling` sections added to 14 skills. *(SE-10)*
- `tools/visual-explainer/image_generator.py`: typed google-genai/httpx exception classification for backoff. *(SE-05)*

### Fixed
- Un-gated the mocked full-pipeline test from `ANTHROPIC_API_KEY`; deterministic resize test. *(QA-07/QA-08)*

### Removed
- `scripts/generate-help.py` (dead — targeted a never-produced `help.md`; ADR-0004 amended); tracked cruft (`GITHUB_ERRORS.md` ×2, `gap-analysis-2026-04-30.md`, placeholder `uv.lock`).

## [10.3.0] - 2026-07-16

### Added
- `skills/clear-prep/SKILL.md`: prepares a project to survive a context `/clear` or compaction with zero state loss — Phase 1 reconstructs session state from the git delta + conversation; Phase 2 flushes it into durable docs (LAB_NOTEBOOK in-flight-entry flush + Decision Log / Action Items / Current Baseline living sections, memory files, CLAUDE.md rules, CHANGELOG) without committing; Phase 3 emits a single copy-paste "resume prompt" that orients a zero-context session after `/clear`. `allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)`; model-invocation enabled (suggestable on "clear context / compact / wrap up"); `--no-write` dry-run generates only the resume prompt

## [10.2.0] - 2026-07-12

### Added
- `skills/fleet-health/SKILL.md`: read-only, one-shot health snapshot across the 5-machine personal fleet (DGX Spark, Jetson Orin Nano, homeserver, bond, obvm) — uptime/load/disk/memory plus per-host inference/service endpoint checks over SSH and curl, rendered as a single status table with a pass/fail verdict
- `skills/new-project/SKILL.md`: end-to-end new-project scaffolder — git init, remote (GitHub by default, Gitea with `--gitea`), `CLAUDE.md` seeded from `references/templates/project-claude-md.md`, type-appropriate `.gitignore`, placeholder-only `.env`, mandatory `LAB_NOTEBOOK.md`, kill-criteria `BRIEF.md` seeded from `references/templates/brief.md`, and initial commit/push
- `skills/archive-project/SKILL.md`: retires a project repo — writes a status header into README.md, tags and commits, pushes and optionally archives the remote (GitHub only), moves the directory into `~/dev/archive/`, and logs one line to `~/dev/PORTFOLIO.md`
- `agents/sre-operator.md`: new named agent for the 5-machine homelab fleet — SSH-based diagnosis and scoped, explicitly-authorized remediation with mandatory LAB_NOTEBOOK logging; `model: inherit` per ADR-0005
- `references/templates/project-claude-md.md`, `references/templates/brief.md`: new scaffolding templates consumed by `new-project`

### Fixed
- `hooks/hooks.json`: lab-notebook `PreToolUse` gate rewritten to parse `tool_input.command` from stdin JSON via `jq` (falling back to raw stdin if `jq` is unavailable) instead of grepping the `$CLAUDE_TOOL_INPUT` env-var name against the payload, and to propagate the gate script's actual exit code instead of unconditionally returning 0 — the prior form could never block a commit

## [10.1.0] - 2026-07-12

### Added
- `skills/wiki/SKILL.md`: layout detection gained a new **OKF bundle mode** — drives kb/-rooted wikis from their repo's own `AGENTS.md` contract (per-directory indexes, contract frontmatter, delegated `tools/lint.py`, repo-native log format). Legacy `wiki/` + `schema.yaml` behavior unchanged.
- `skills/wiki/SKILL.md`: new `propagate <fact>` subcommand — sweeps all pages for stale variants of a newly resolved fact, applies edits, closes markers, logs once.
- `commands/analyze-transcript.md`: new `--format interview-record` — dated markdown record with YAML frontmatter for knowledge-repo immutable sources directories.

## [10.0.0] - 2026-07-08

Coordinated with marketplace v3.3.0, bpmn-plugin v4.2.0, slide-gen v1.2.0. Closes an 8-phase modernization pass against current official Anthropic guidance (see repo-root `IMPLEMENTATION_PLAN.md`, ADR-0005, ADR-0006).

### Added
- `agents/*.md`: all 9 arch-review agents (solutions-architect, data-architect, integration-architect, software-engineer, performance-engineer, qa-architect, security-architect, platform-engineer, risk-compliance) gained spec-conformant frontmatter (`name`, `description`, least-privilege `tools`, `model: inherit`, `effort: high`) — the official validator's only strict failure, now fixed
- `commands/new-skill.md`: `--pattern` argument scaffolds a skill from any of the 8 command-pattern templates, adapted to skill form at generation time
- New `references/` files: `plan-append-guide.md`, `recommendations-template.md`, `create-plan-examples.md`, `implement-plan-state-schema.md`, `validation-output-examples.md`, `research-provider-protocols.md`, `ship-output-templates.md`, `clean-repo-examples.md`, `claude-md-wiki-section.md`, `wiki-readme-template.md`, `skill-patterns.md`, plus skill-local `evaluate-pipeline-output/references/{report-format,evaluator-guidance}.md`
- `README.md`, `LICENSE` at plugin root

### Changed
- `.claude/agents/{haiku,sonnet,opus}-implementer.md` (repo root): pinned model IDs replaced with tier aliases per ADR-0005 — swap models globally without touching plans
- `skills/arch-review/SKILL.md`, `commands/arch-review-single.md`, `commands/arch-synthesize.md`: dispatch simplified to `subagent_type`-by-name (no more agent-file inlining); per-agent `findings/<agent>.meta.json` replaces the shared, collision-prone `.meta.json`
- `commands/create-plan.md` (470 lines), `commands/plan-improvements.md` (490 lines), `commands/implement-plan.md` (573 lines): single-sourced onto `references/plan-template.md` for the model-tier rubric, sizing tables, and append procedure; `implement-plan`'s duplicated PATH A/PATH B collapsed into one flow parameterized on batch cardinality
- `commands/validate-plugin.md`: refactored to 675 lines with a dynamic reference-file inventory (diffs `references/` against a required set) replacing the hand-synced table; sample output moved to `validation-output-examples.md`
- Progressive-disclosure pass brought `skills/research-topic/SKILL.md`, `skills/ship/SKILL.md`, `commands/clean-repo.md`, `commands/finish-document.md`, `skills/create-wiki/SKILL.md`, `skills/evaluate-pipeline-output/SKILL.md`, and `commands/test-project.md` to/toward the ~500-line budget
- `skills/{plan-gate,brain-entry,summarize-feedback,lab-notebook,unlock,create-wiki,release-plugin,visual-explainer,security-analysis,research-topic,prime,evaluate-pipeline-output}/SKILL.md`: body "Proactive Triggers" sections folded into frontmatter `description`/`when_to_use`
- `skills/explain-project/SKILL.md`, `skills/spec-to-prototype/SKILL.md`, `skills/accessibility-annotator/SKILL.md`: added explicit "Do NOT use for" negative scope disambiguating the explain-project/accessibility-annotator/convert-markdown overlap triangle
- `commands/scaffold-plugin.md`: defaults flipped to skills-first — `skills/` scaffolded by default, `commands/` only via explicit `--with-commands` (ADR-0006)
- 8 skills (`arch-review`, `brain-entry`, `create-wiki`, `lab-notebook`, `release-plugin`, `ship`, `unlock`, `visual-explainer` — 4 pre-existing + 4 new) now carry `disable-model-invocation: true`

### Fixed
- 15 `/batch` + 11 `/ultrareview` dangling references replaced with real mechanics (`/implement-plan` parallel phases, background Agent dispatch) and the current `/code-review ultra` alias
- `skills/ultra-plan/SKILL.md`: phase-numbering gap (Phase 0 → Phase 2) renumbered to a contiguous 0–5 sequence
- `commands/validate-plugin.md`: rule-count check synced from 16 to the template's actual 17 rules
- `skills/research-topic/SKILL.md`: stale `claude-opus-4-6` model ID → `claude-opus-4-8`; dead `agent:`-field misuse removed from the fork header
- `tools/visual-explainer/`: dead `config.claude_model` plumbing wired through both construction sites; `DEFAULT_MODEL` constants updated; dead `TargetModelHint` style key removed from both style JSONs
- `skills/explain-project/SKILL.md`, `skills/accessibility-annotator/SKILL.md`, `skills/evaluate-pipeline-output/SKILL.md`: hardcoded `C:\Users\...` paths rewritten to portable equivalents
- `skills/prime/SKILL.md`: CRLF line endings normalized to LF
- `skills/unlock/SKILL.md`: malformed `Bash(powershell*)` permission glob corrected to `Bash(powershell:*)`

### Deprecated
- `commands/new-command.md`: moved to `deprecated/`; replaced by `/new-skill --pattern` per the skills-first authoring policy (ADR-0006)

## [9.3.0] - 2026-06-15

### Changed
- `skills/spark-recon`: refreshed stale Machine Config — `current_model` → `Qwen/Qwen3.6-35B-A3B-FP8`, `quantization` → pre-quantized FP8; broadened Check 2 keyword classifier (Qwen3.6/3.7, DFlash, speculative); Check 1/4 instructions updated to Qwen3.6 context.
- `skills/spark-recon` Check 1: documented the Firestore `benchmarks`-collection REST access path (App-Check gate on `entries`/`leaderboard`/`recipes`; `benchmarks` is world-readable) — unfreezes Arena tracking.
- `skills/spark-recon` Check 5 + `skills/spark-audit`: dropped permanently-removed NVIDIA forum category 720 (404; topics merged into 719/721).
- `skills/spark-audit`: removed the obsolete "pre-quant FP8 hangs" CRITICAL anti-pattern (production intentionally runs pre-quant FP8 since 2026-05-18) and corrected the attention-backend expectation (FLASH_ATTN auto-selected on SM121; FlashInfer is MoE-only).

## [8.0.0] - 2026-04-21

### Added
- `references/patterns/advanced-features.md` — canonical deep-dive for all 9 modern frontmatter fields (`context:fork`, `isolation:worktree`, `paths:`, dynamic injection, etc.)
- `references/patterns/audit-recon-system.md` — shared 5-check framework, 7-phase execution, YAML config schemas, severity matrices
- `hooks/scripts/lab-notebook-gate.sh` — opt-in PreToolUse hook enforcing LAB_NOTEBOOK.md recency before commit
- `paths:` auto-activation on security-analysis (dependency manifests), create-wiki (wiki sources/CLAUDE.md/LAB_NOTEBOOK.md), jetson-audit, spark-audit, jetson-recon, spark-recon

### Changed
- `prime`, `arch-review`, `leak-risk-audit`, `explain-project`, `accessibility-annotator`, `research-topic`: adopted `context:fork`, `isolation:worktree`, and dynamic `!cmd` context injection
- `jetson-audit`, `spark-audit`, `jetson-recon`, `spark-recon`: thinned to config-layer-only (~40–50% LOC reduction) delegating shared logic to audit-recon-system reference
- `new-skill`, `new-command`: updated with 13-field frontmatter reference, worked examples, modern feature docs
- `scaffold-plugin`: removed auto-generated help skill
- `ship`: dynamic git injection, `/ultrareview` gate for 500+ line diffs
- `research-topic`: rewritten as 3 parallel `context:fork` subagents (Claude/OpenAI/Gemini) with parent synthesis — no external tool required

### Removed
- `skills/help/` — superseded by native `/help`
- `commands/review-pr.md` — superseded by native `/review`
- `tools/research-orchestrator/` — 27-file Python tool eliminated; skill now uses native subagent dispatch

## [6.7.0] - 2026-03-31

### Added
- Documentation gate in `/ship` skill (Phase 3.1) — checks for LAB_NOTEBOOK.md and enforces notebook updates before commit/push per CLAUDE.md rules

### Fixed
- hooks.json migrated from deprecated array format to record-keyed-by-event format (fixes "expected record, received array" plugin load error)

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
