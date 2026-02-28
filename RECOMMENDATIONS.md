# Recommendations: Personal Plugin Command & Skill Quality Overhaul

**Generated:** 2026-02-28
**Based On:** Critical review of all 23 commands and 9 skills (excluding 3 recently-upgraded planning commands and help skill)
**Quality Baseline:** The recently-upgraded planning commands (`create-plan.md`, `plan-improvements.md`, `implement-plan.md`) which feature: `allowed-tools` frontmatter, task-based instructions, concrete sizing heuristics, structured output templates, error handling sections, context management, and related-command cross-references.

---

## Executive Summary

32 files reviewed across commands and skills. Average rating: 3.5/5. The planning pipeline upgrade exposed a significant quality gap between those three commands and the rest of the plugin. Six systemic issues affect nearly every file, and several individual files need structural overhauls.

**Rating Distribution:**

| Rating | Count | Files |
|--------|-------|-------|
| 5/5 | 3 | prime, unlock, plan-gate |
| 4/5 | 12 | review-intent, review-pr, remove-ip, ship, summarize-feedback, visual-explainer, validate-and-ship, bump-version, clean-repo, new-skill, validate-plugin, ask-questions |
| 3.5/5 | 4 | analyze-transcript, assess-document, finish-document, test-project |
| 3/5 | 9 | define-questions, develop-image-prompt, review-arch, convert-hooks, convert-markdown, new-command, scaffold-plugin, security-analysis, check-updates |
| 2.5/5 | 1 | consolidate-documents |
| 2/5 | 2 | plan-next, setup-statusline |

---

## Cross-Cutting Issues (Affect Multiple Files)

### S1. Missing `allowed-tools` Frontmatter [ALL FILES]

**Impact:** High | **Effort:** Low

Every command and skill reviewed is missing `allowed-tools` in its YAML frontmatter. The planning commands specify exactly which tools are permitted, preventing unintended tool use. This is a batch fix — add appropriate `allowed-tools` declarations to all 32 files.

**Recommended values by command type:**
- Read-only commands (review-arch, review-intent, check-updates): `Read, Glob, Grep`
- Read + git (review-pr, plan-next): `Read, Glob, Grep, Bash(gh:*), Bash(git:*)`
- File generators (analyze-transcript, assess-document, etc.): `Read, Write, Edit, Glob, Grep`
- Shell-dependent (test-project, convert-markdown): `Read, Write, Edit, Glob, Grep, Bash`
- Skills with external tools (research-topic, visual-explainer): `Read, Write, Bash, WebSearch, WebFetch`

### S2. Missing Error Handling Sections [20+ FILES]

**Impact:** High | **Effort:** Medium

Most commands lack a structured `## Error Handling` section. The planning commands have explicit error handling for every failure mode with user-facing message examples. Common missing handlers: file not found, empty/binary input, context window exhaustion, tool unavailability, permission errors.

### S3. Missing "Related Commands" Sections [ALL COMMANDS]

**Impact:** Medium | **Effort:** Low

No command has a "Related Commands" section linking to related functionality. Natural groupings:
- Document pipeline: define-questions → ask-questions → finish-document
- Review suite: review-arch, review-intent, review-pr
- Planning pipeline: plan-improvements → create-plan → implement-plan
- Scaffolding: scaffold-plugin → new-command → new-skill
- Ship pipeline: validate-plugin → validate-and-ship → ship

### S4. Missing Proactive Trigger Sections [ALL SKILLS EXCEPT plan-gate]

**Impact:** High | **Effort:** Medium

Only `plan-gate` has explicit "When to suggest this skill" trigger conditions. Every other skill lacks this, which is the most important differentiator between skills and commands.

### S5. Inconsistent Flag Coverage

**Impact:** Medium | **Effort:** Medium

Flags like `--preview`, `--no-prompt`, `--dry-run`, and `--format` exist in some commands but not others with no consistent pattern. Commands that write output files should standardize on a common flag set.

### S6. Dead References to Non-Existent Files

**Impact:** Medium | **Effort:** Low

Three commands (`new-command.md`, `new-skill.md`, `scaffold-plugin.md`) reference `python scripts/generate-help.py` and `python scripts/update-readme.py` which do not exist. Two commands (`define-questions.md`, `finish-document.md`) reference a `schemas/` directory for validation files that does not exist.

### S7. Hardcoded Plugin Lists

**Impact:** Low | **Effort:** Low

Multiple commands (`bump-version`, `check-updates`, `validate-plugin`) hardcode `personal-plugin` and `bpmn-plugin` instead of dynamically scanning the `plugins/` directory.

### S8. Secrets Policy Violations

**Impact:** High | **Effort:** Low

`research-topic` and `visual-explainer` skills include API key setup wizards that write keys directly to `.env` files, contradicting the global CLAUDE.md Bitwarden-first policy. Should reference `/unlock` as primary path.

---

## Individual Recommendations by Priority

### Priority 1: Major Overhauls (Rating 2-2.5)

#### R1. Rewrite `plan-next.md` [Rating: 2/5]

**Current state:** 47 lines. Uses "Ultrathink" jargon, no methodology, no error handling, no examples, no output template.

**Recommended changes:**
1. Expand to 150-200 lines with structured methodology
2. Add plan-awareness: check for existing IMPLEMENTATION_PLAN.md and RECOMMENDATIONS.md first
3. Add git-awareness: check for uncommitted changes, open branches, open PRs
4. Add decision matrix: blocked work > critical fixes > next plan phase > highest-priority recommendation
5. Replace "~100K tokens" with standard S/M/L sizing table
6. Add structured output template: Current State, Recommended Action, Rationale, Scope Estimate
7. Add error handling and examples
8. Add `allowed-tools` to frontmatter

#### R2. Rewrite `setup-statusline.md` [Rating: 2/5]

**Current state:** 175 lines. 80% PowerShell script dump with no command structure, no validation, no error handling. Overwrites `settings.json` without merging.

**Recommended changes:**
1. Add phased structure: pre-flight checks → create script → merge settings → verification
2. Add `pwsh` version detection (PowerShell 7+ required)
3. Add settings.json merge logic instead of overwrite
4. Add backup of existing files before modification
5. Add `--dry-run` and `--uninstall` flags
6. Add verification step that tests statusline output
7. Add error handling section

#### R3. Overhaul `consolidate-documents.md` [Rating: 2.5/5]

**Current state:** 134 lines. Contradictory input flow, no output example, no error handling, no flags.

**Recommended changes:**
1. Expand to 250+ lines with proper depth
2. Resolve contradictory input flow — pick one mechanism
3. Add complete output example with consolidation notes
4. Add `--format`, `--preview`, `--no-prompt` flags
5. Add error handling for missing files, format mismatches, single document, identical documents
6. Define how `[topic]` is derived in output filename

### Priority 2: Structural Improvements (Rating 3)

#### R4. Fix `define-questions.md` phantom schema references [Rating: 3/5]

1. Either create `schemas/questions.json` or replace references with inline validation rules
2. Standardize on one field name (`question` or `text`) across all formats
3. Add `priority` field to JSON schema example to match CSV format
4. Add error handling and related-commands sections

#### R5. Fix `finish-document.md` phantom references and resume contradiction [Rating: 3.5/5]

1. Resolve schema references (same approach as R4)
2. Pick one resume mechanism (auto-detect or explicit flag) and document consistently
3. Expand error handling section
4. Add bounds checking for `go to [N]` navigation
5. Add performance guidance

#### R6. Restructure `review-arch.md` [Rating: 3/5]

1. Rewrite assessment dimensions as imperative tasks (matching plan-improvements style)
2. Add structured output template: Executive Summary, Scorecard, Findings, Remediation Roadmap
3. Define T-shirt sizes with standard S/M/L table
4. Add examples section
5. Move "DO NOT MAKE ANY CHANGES" guardrail to top of file

#### R7. Rethink `check-updates.md` [Rating: 3/5]

1. Either: (a) make it a true remote check fetching latest marketplace.json from GitHub, or (b) reframe as "version consistency audit"
2. Remove misleading "Updates Available" language if keeping local-only
3. Add proper error handling section

#### R8. Fix `scaffold-plugin.md` correctness bug [Rating: 3/5]

1. Fix bug: change `skills/help.md` to `skills/help/SKILL.md` in output report (lines 259, 353)
2. Remove dead `python scripts/` references
3. Extract 80-line inline help template to a template file
4. Add `--dry-run` flag
5. Fix JSON `keywords` example

#### R9. Improve `convert-hooks.md` honesty [Rating: 3/5]

1. Add prominent warning that automated conversion handles only simple scripts
2. Add concrete before/after example
3. Add platform detection instead of listing both paths
4. Add `--validate` step for generated PowerShell scripts

#### R10. Expand `convert-markdown.md` [Rating: 3/5]

1. Either make the analysis step useful (customize pandoc flags) or remove it
2. Add proper error handling for pandoc failures
3. Add `--no-toc`, `--style` option flags
4. Add `--dry-run` flag

#### R11. Fix `new-command.md` [Rating: 3/5]

1. Remove dead `python scripts/` references — replace with help skill update instruction
2. Add plugin target parameter (detect or prompt)
3. Add `orchestration` to pattern types
4. Add post-generation validation step

#### R12. Overhaul `security-analysis` skill [Rating: 3/5]

1. Add input validation section with arguments (path scope, `--quick`, `--dependencies-only`)
2. Add `allowed-tools` to frontmatter
3. Add proactive trigger section
4. Add error handling, examples, output location, performance expectations
5. Remove inline technology patterns that duplicate the separate reference files
6. Replace emoji severity with text labels

### Priority 3: Targeted Fixes (Rating 3.5-4)

#### R13. Fix `test-project.md` safety issues [Rating: 3.5/5]

1. Replace `git add -A` with selective staging
2. Update Co-Authored-By to `Claude Opus 4.6`
3. Replace auto-merge with user confirmation prompt
4. Add `--coverage <n>` optional argument
5. Add scope confirmation gate before making changes

#### R14. Fix `assess-document.md` naming inconsistency [Rating: 3.5/5]

1. Fix output file naming — pick ONE pattern, remove alternatives
2. Add score anchor definitions for the 1-5 rubric
3. Fix `yaml` code fence language to `text` in examples
4. Add error handling section

#### R15. Improve `analyze-transcript.md` [Rating: 3.5/5]

1. Add error handling section
2. Add `--no-prompt` flag for consistency
3. Replace vague "paste content" note with concrete interactive flow
4. Add context/size management for large transcripts

#### R16. Improve `develop-image-prompt.md` [Rating: 3/5]

1. Add `--dimensions` flag to override default 11x17
2. Add complete example of an actual generated prompt
3. Resolve contradictory input flow
4. Define when style variations are generated vs skipped

#### R17. Fix `review-intent.md` minor issues [Rating: 4/5]

1. Add argument detection instructions
2. Add `allowed-tools` to frontmatter
3. Replace shell redirection save suggestion with proper file write offer
4. Define "sparse" explicitly
5. Add calculation guidance for Phase 3.3 metrics

#### R18. Fix `review-pr.md` minor issues [Rating: 4/5]

1. Add `Read` to allowed-tools
2. Move review guidelines before Phase 1
3. Inline severity definitions instead of referencing external file
4. Add error handling for: diff exceeds context, binary files, merged PR, draft PR

#### R19. Fix `remove-ip.md` structural issue [Rating: 4/5]

1. Remove "Trigger phrases" section (command pattern, not skill pattern)
2. Add `allowed-tools` and error handling
3. Add web research tool guidance

#### R20. Fix `ship` skill issues [Rating: 4/5]

1. Renumber phases consistently
2. Add proactive trigger section
3. Add risk/destructive-action warning
4. Update Co-Authored-By format

#### R21. Fix `research-topic` skill [Rating: 4/5]

1. Extract API key setup wizard to reference file (cuts 130+ lines)
2. Fix secrets policy violation — reference `/unlock` instead of `.env` writes
3. Add `--skip-model-check` to arguments table
4. Add proactive trigger section

#### R22. Fix remaining skills [Rating: 4/5]

Batch fixes for `summarize-feedback`, `visual-explainer`, `validate-and-ship`:
1. Add proactive trigger sections to all three
2. `summarize-feedback`: add context-size guardrail for large entry counts
3. `visual-explainer`: document `--json` flag, fix default threshold, reference `/unlock`
4. `validate-and-ship`: clarify delegation mechanism, add `--skip-ship` flag

#### R23. Fix utility commands [Rating: 4/5]

Batch fixes for `bump-version`, `clean-repo`, `new-skill`, `validate-plugin`, `ask-questions`:
1. `bump-version`: dynamic plugin scanning instead of hardcoded list
2. `clean-repo`: replace `find` commands with Glob tool instructions, add context management
3. `new-skill`: remove dead script references, add plugin target parameter
4. `validate-plugin`: fix duplicate section numbering, fix skill path example
5. `ask-questions`: align resume support with output schema

#### R24. Fix `unlock` skill shell injection risk [Rating: 5/5]

1. Fix shell injection risk in Linux `eval` pattern — use `shlex.quote()` for secret values
2. Add proactive trigger section

---

## Implementation Sizing Summary

| Priority | Recommendations | Est. Complexity |
|----------|----------------|-----------------|
| P1: Major Overhauls | R1-R3 (3 files) | L (~500-1500 LOC) |
| P2: Structural Improvements | R4-R12 (9 files) | L (~500-1500 LOC) |
| P3: Targeted Fixes | R13-R24 (20+ files) | M-L (repetitive but extensive) |
| Cross-cutting batch fixes | S1-S8 | M (~100-500 LOC per fix, repetitive) |

**Total scope:** ~32 files modified, ~2000-3000 LOC of changes across 24 recommendations.

---

## Not Recommended

### NR1. Splitting `validate-plugin.md` into multiple commands
**Why Considered:** At 1184 lines, it's the longest command.
**Why Rejected:** Phases are tightly coupled. `--scorecard` flag provides clean separation.
**Reconsider If:** Command grows beyond 1500 lines.

### NR2. Converting `remove-ip.md` to a skill
**Why Considered:** It has trigger phrases, which is a skill pattern.
**Why Rejected:** Workflow is too long and complex for proactive suggestion. Better to remove trigger phrases.
**Reconsider If:** A lightweight version is needed for proactive offering.

### NR3. Merging `new-command.md` and `new-skill.md`
**Why Considered:** They share 70% of logic.
**Why Rejected:** Commands and skills have fundamentally different structures and frontmatter. Separate commands prevent wrong-type creation.
**Reconsider If:** A unified `/new --type command|skill` proves more discoverable.

---

*Recommendations generated by Claude on 2026-02-28*
*Source: Critical quality review of personal-plugin commands and skills*
