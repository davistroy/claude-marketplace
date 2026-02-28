# Implementation Plan

**Generated:** 2026-02-28T22:00:00
**Based On:** RECOMMENDATIONS.md (Personal Plugin Command & Skill Quality Overhaul)
**Total Phases:** 7
**Estimated Total Effort:** ~2,500-3,500 LOC across 32 files
**Plan Status: COMPLETE [2026-02-28]**

---

## Completion Summary

All **32 work items** across **7 phases** completed on **2026-02-28**. Every recommendation (R1-R24) and cross-cutting issue (S1-S8) from the quality review has been addressed.

| Phase | Work Items | Status |
|-------|-----------|--------|
| Phase 1: Cross-Cutting Batch Fixes | 5 | Complete |
| Phase 2: Major Overhauls | 3 | Complete |
| Phase 3: Structural Improvements A | 4 | Complete |
| Phase 4: Structural Improvements B | 5 | Complete |
| Phase 5: Targeted Fixes A | 4 | Complete |
| Phase 6: Targeted Fixes B | 5 | Complete |
| Phase 7: Skill Improvements & Final Polish | 6 | Complete |
| **Total** | **32** | **Complete** |

**Key outcomes:** All 32 files now have `allowed-tools` frontmatter, error handling sections, and related-commands cross-references. All 9 skills have proactive trigger sections. Three commands fully rewritten (plan-next, setup-statusline, consolidate-documents). Security fix applied to unlock skill. Secrets policy enforced across all skills. Help skill updated to reflect all changes. Flag consistency audited and documented.

---

## Executive Summary

This plan upgrades all 23 commands and 9 skills in the personal plugin to match the quality bar set by the recently-upgraded planning commands (`create-plan`, `plan-improvements`, `implement-plan`). The work addresses 24 individual recommendations (R1-R24) and 8 cross-cutting systemic issues (S1-S8) identified in the quality review.

The strategy is **cross-cutting first, then depth**: Phase 1 applies batch fixes that touch every file (allowed-tools, related commands, dead references, hardcoded lists, secrets policy), establishing a consistent baseline. Phases 2-3 tackle the files that need the most structural work (major overhauls and deep structural improvements). Phases 4-6 apply targeted fixes to files that are already close to production quality. Phase 7 finishes with skill-specific improvements and a final consistency sweep.

All changes are to markdown command/skill files (prompt/instruction text only). No source code changes. Risk of breaking existing functionality is low since the changes refine instructions rather than alter architecture. Each phase leaves the plugin in a functional state.

---

## Plan Overview

The seven phases are organized into three tiers:

- **Tier 1 (Phase 1):** Cross-cutting batch fixes that establish a consistent baseline across all 32 files. These must go first because subsequent phases would otherwise need to add these elements individually.
- **Tier 2 (Phases 2-4):** Structural work on files rated 2-3/5 that need significant rewrites or restructuring. Ordered by severity: major overhauls first, then structural improvements in two batches to stay within phase size limits.
- **Tier 3 (Phases 5-7):** Targeted fixes to files rated 3.5-5/5 that need specific improvements, plus final skill improvements and a consistency sweep.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | Cross-Cutting Batch Fixes | allowed-tools on 32 files, related commands on 23 commands, dead ref removal, dynamic plugin scanning, secrets policy fixes | L (~32 files, ~500-800 LOC) | None |
| 2 | Major Overhauls | Rewritten plan-next, setup-statusline, consolidate-documents | M (~3 files, ~400-600 LOC) | Phase 1 |
| 3 | Structural Improvements A | Overhauled define-questions, finish-document, review-arch, check-updates | M (~4 files, ~300-500 LOC) | Phase 1 |
| 4 | Structural Improvements B | Fixed scaffold-plugin, convert-hooks, convert-markdown, new-command, security-analysis | M (~5 files, ~300-500 LOC) | Phase 1 |
| 5 | Targeted Fixes A | Fixed test-project, assess-document, analyze-transcript, develop-image-prompt | M (~4 files, ~200-300 LOC) | Phase 1 |
| 6 | Targeted Fixes B | Fixed review-intent, review-pr, remove-ip, ship, research-topic | M (~5 files, ~200-400 LOC) | Phase 1 |
| 7 | Skill Improvements & Final Polish | Remaining skills batch, utility commands batch, unlock fix, error handling audit, proactive triggers, flag consistency | M (~8 files, ~300-500 LOC) | Phases 1-6 |

<!-- BEGIN PHASES -->

---

## Phase 1: Cross-Cutting Batch Fixes

**Estimated Complexity:** L (~32 files, ~500-800 LOC)
**Dependencies:** None
**Parallelizable:** Yes — work items 1.1 through 1.5 touch different aspects of the same files but can be done in a single pass per file

### Goals
- Every command and skill has `allowed-tools` in its frontmatter
- Every command has a "Related Commands" section linking to logical groupings
- Dead references to non-existent scripts and directories are removed
- Hardcoded plugin lists replaced with dynamic scanning instructions
- Secrets policy violations fixed in research-topic and visual-explainer

### Work Items

#### 1.1 Add `allowed-tools` Frontmatter to All Commands and Skills
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** S1
**Files Affected:**
- `plugins/personal-plugin/commands/analyze-transcript.md` (modify)
- `plugins/personal-plugin/commands/ask-questions.md` (modify)
- `plugins/personal-plugin/commands/assess-document.md` (modify)
- `plugins/personal-plugin/commands/bump-version.md` (modify)
- `plugins/personal-plugin/commands/check-updates.md` (modify)
- `plugins/personal-plugin/commands/clean-repo.md` (modify)
- `plugins/personal-plugin/commands/consolidate-documents.md` (modify)
- `plugins/personal-plugin/commands/convert-hooks.md` (modify)
- `plugins/personal-plugin/commands/convert-markdown.md` (modify)
- `plugins/personal-plugin/commands/define-questions.md` (modify)
- `plugins/personal-plugin/commands/develop-image-prompt.md` (modify)
- `plugins/personal-plugin/commands/finish-document.md` (modify)
- `plugins/personal-plugin/commands/new-command.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/commands/plan-next.md` (modify)
- `plugins/personal-plugin/commands/remove-ip.md` (modify)
- `plugins/personal-plugin/commands/review-arch.md` (modify)
- `plugins/personal-plugin/commands/review-intent.md` (modify)
- `plugins/personal-plugin/commands/review-pr.md` (modify)
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify)
- `plugins/personal-plugin/commands/setup-statusline.md` (modify)
- `plugins/personal-plugin/commands/test-project.md` (modify)
- `plugins/personal-plugin/commands/validate-plugin.md` (modify)
- `plugins/personal-plugin/skills/prime/SKILL.md` (modify)
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify)
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify)
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify)
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (modify)
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)
- `plugins/personal-plugin/skills/validate-and-ship/SKILL.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)

**Description:**
Add `allowed-tools` declarations to the YAML frontmatter of every command and skill that currently lacks one. Use the recommended values by command type from S1 in RECOMMENDATIONS.md.

**Tasks:**
1. [ ] For each read-only command (`review-arch`, `review-intent`, `check-updates`, `plan-next`), add `allowed-tools: Read, Glob, Grep`
2. [ ] For read+git commands (`review-pr`), add `allowed-tools: Read, Glob, Grep, Bash(gh:*), Bash(git:*)`
3. [ ] For file generator commands (`analyze-transcript`, `assess-document`, `ask-questions`, `define-questions`, `develop-image-prompt`, `finish-document`, `consolidate-documents`, `remove-ip`), add `allowed-tools: Read, Write, Edit, Glob, Grep`
4. [ ] For shell-dependent commands (`test-project`, `convert-markdown`, `convert-hooks`, `setup-statusline`, `clean-repo`), add `allowed-tools: Read, Write, Edit, Glob, Grep, Bash`
5. [ ] For scaffolding/utility commands (`scaffold-plugin`, `new-command`, `new-skill`, `bump-version`, `validate-plugin`), add `allowed-tools: Read, Write, Edit, Glob, Grep, Bash`
6. [ ] For skills with external tools (`research-topic`, `visual-explainer`), add `allowed-tools: Read, Write, Bash, WebSearch, WebFetch`
7. [ ] For workflow skills (`ship`, `validate-and-ship`), add `allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(gh:*)`
8. [ ] For analysis skills (`prime`, `security-analysis`, `summarize-feedback`), add `allowed-tools: Read, Glob, Grep, Write`
9. [ ] For `unlock` skill, add `allowed-tools: Bash(bws:*), Bash(export:*)`
10. [ ] Verify all 32 files (excluding the 3 planning commands and help skill which already have `allowed-tools`) now have the declaration

**Acceptance Criteria:**
- [ ] All 32 reviewed files have `allowed-tools` in their YAML frontmatter
- [ ] Tool declarations match the command type (read-only commands do not have Write, etc.)
- [ ] No existing frontmatter fields are lost or reordered

**Notes:**
`plan-next` is listed as read-only here but needs `Bash(git:*), Bash(gh:*)` once R1 is implemented (Phase 2). The Phase 1 value is correct for its current state; Phase 2 will update it.

---

#### 1.2 Add "Related Commands" Sections to All Commands
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** S3
**Files Affected:**
- All 23 command files in `plugins/personal-plugin/commands/` (modify)

**Description:**
Add a `## Related Commands` section to the bottom of every command file, linking to logically related commands and skills. Use the natural groupings defined in S3.

**Tasks:**
1. [ ] Add "Related Commands" section to document pipeline commands (`define-questions`, `ask-questions`, `finish-document`) cross-referencing each other
2. [ ] Add "Related Commands" section to review suite commands (`review-arch`, `review-intent`, `review-pr`) cross-referencing each other
3. [ ] Add "Related Commands" section to scaffolding commands (`scaffold-plugin`, `new-command`, `new-skill`) cross-referencing each other and `/validate-plugin`
4. [ ] Add "Related Commands" section to ship pipeline commands (`validate-plugin`, `test-project`) linking to `/validate-and-ship` and `/ship` skills
5. [ ] Add "Related Commands" section to planning pipeline commands (`plan-improvements`, `create-plan`, `implement-plan`) — these may already have cross-references; verify and standardize format
6. [ ] Add "Related Commands" sections to remaining commands with appropriate links: `consolidate-documents` links to document pipeline; `convert-markdown` and `convert-hooks` link to each other; `analyze-transcript` and `assess-document` link to each other; `develop-image-prompt` links to `/visual-explainer`; `clean-repo` links to `/validate-plugin`; `bump-version` and `check-updates` link to each other; `remove-ip` links to document pipeline; `setup-statusline` stands alone; `plan-next` links to planning pipeline
7. [ ] Use consistent format: `- **`/command-name`** — Brief description of when to use it after this command`

**Acceptance Criteria:**
- [ ] All 23 commands have a "Related Commands" section
- [ ] Cross-references are bidirectional (if A links to B, B links to A)
- [ ] Format is consistent across all commands

**Notes:**
Place the "Related Commands" section at the very end of each file, after all other content. Keep entries to 1 line each with a dash-separated command name and brief context.

---

#### 1.3 Remove Dead References to Non-Existent Files
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** S6
**Files Affected:**
- `plugins/personal-plugin/commands/new-command.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify)
- `plugins/personal-plugin/commands/define-questions.md` (modify)
- `plugins/personal-plugin/commands/finish-document.md` (modify)
- `plugins/personal-plugin/commands/ask-questions.md` (modify)
- `plugins/personal-plugin/commands/validate-plugin.md` (modify)
- `plugins/personal-plugin/references/templates/*.md` (modify, 8 files)
- `plugins/personal-plugin/references/patterns/validation.md` (modify)
- `plugins/personal-plugin/references/patterns/workflow.md` (modify)

**Description:**
Remove or replace references to `python scripts/generate-help.py`, `python scripts/update-readme.py`, and `schemas/` directory that do not exist in the repository.

**Tasks:**
1. [x] In `new-command.md`: find and remove references to `python scripts/generate-help.py` and `python scripts/update-readme.py`. Replace with instruction: "Update the plugin's `skills/help/SKILL.md` with the new command entry."
2. [x] In `new-skill.md`: find and remove the same dead script references. Replace with the same help skill update instruction.
3. [x] In `scaffold-plugin.md`: find and remove dead `python scripts/` references. Replace with instruction to manually update help skill. Also fixed `help.md` -> `help/SKILL.md` path bug in output reports.
4. [x] In `define-questions.md`: find references to `schemas/questions.json` or `schemas/` directory. Replace with inline validation rules embedded in the command itself.
5. [x] In `finish-document.md`: find and remove `schemas/` directory references. Replace with inline validation rules matching the approach taken in `define-questions.md`.
6. [x] Search all other files for any remaining references to `scripts/generate-help.py`, `scripts/update-readme.py`, or `schemas/` and fix any found. Fixed: `ask-questions.md` (7 refs), `validate-plugin.md` (2 refs), 8 template files (1 ref each), `validation.md` (5 refs), `workflow.md` (1 ref).

**Acceptance Criteria:**
- [x] Zero references to `python scripts/generate-help.py` or `python scripts/update-readme.py` in any file
- [x] Zero references to `schemas/` directory in any file
- [x] All removed references replaced with working alternatives

---

#### 1.4 Replace Hardcoded Plugin Lists with Dynamic Scanning
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** S7
**Files Affected:**
- `plugins/personal-plugin/commands/bump-version.md` (modify)
- `plugins/personal-plugin/commands/check-updates.md` (modify)
- `plugins/personal-plugin/commands/validate-plugin.md` (modify)

**Description:**
Replace hardcoded references to `personal-plugin` and `bpmn-plugin` with instructions to dynamically scan the `plugins/` directory for all installed plugins.

**Tasks:**
1. [x] In `bump-version.md`: find hardcoded plugin list and replace with instruction: "Scan the `plugins/` directory to discover all installed plugins. List them for the user to select from."
2. [x] In `check-updates.md`: find hardcoded plugin list and replace with dynamic scanning instruction
3. [x] In `validate-plugin.md`: find hardcoded plugin list and replace with dynamic scanning. Update `--all` flag behavior to scan `plugins/` directory.
4. [x] In each file, add fallback: "If no plugins are found in `plugins/`, report an error."

**Acceptance Criteria:**
- [x] Zero hardcoded references to `personal-plugin` or `bpmn-plugin` as fixed lists in these three files
- [x] All three commands discover plugins dynamically from the `plugins/` directory
- [x] Adding a new plugin directory automatically makes it visible to these commands

**Notes:**
The marketplace.json file can also be used as a secondary source. But directory scanning is the primary mechanism since a plugin can exist locally without being registered in marketplace.json yet.

---

#### 1.5 Fix Secrets Policy Violations
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** S8
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)

**Description:**
Remove API key setup wizards that write keys directly to `.env` files. Replace with references to the `/unlock` skill as the primary path for loading secrets, per the global CLAUDE.md Bitwarden-first policy.

**Tasks:**
1. [x] In `research-topic/SKILL.md`: locate the API key setup wizard section. Replace with: "API keys should be loaded via the `/unlock` skill (Bitwarden-first policy). If secrets are not in the environment, suggest running `/unlock` before proceeding. Do NOT write API keys to `.env` files."
2. [x] In `visual-explainer/SKILL.md`: locate the API key setup wizard section. Apply the same replacement.
3. [x] In both files, retain the list of which API keys are needed (e.g., ANTHROPIC_API_KEY, OPENAI_API_KEY) but remove the code that writes them to `.env`
4. [x] Add a note: "See CLAUDE.md Secrets Management Policy for details."

**Acceptance Criteria:**
- [x] Zero instances of writing API keys to `.env` files in any skill
- [x] Both skills reference `/unlock` as the primary secrets path
- [x] Required API key names are still documented (for user awareness)

---

### Phase 1 Testing Requirements
- [ ] Verify every command and skill file has `allowed-tools` in frontmatter by scanning all `.md` files
- [ ] Verify every command has a "Related Commands" section
- [ ] Grep for `scripts/generate-help.py`, `scripts/update-readme.py`, `schemas/` — zero results
- [ ] Grep for hardcoded `personal-plugin` and `bpmn-plugin` in bump-version, check-updates, validate-plugin — zero fixed-list results
- [ ] Grep for `.env` write patterns in research-topic and visual-explainer — zero results

### Phase 1 Completion Checklist
- [ ] All work items complete
- [ ] All 32 files have consistent frontmatter
- [ ] Cross-references are bidirectional
- [ ] No dead references remain
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 2: Major Overhauls

**Estimated Complexity:** M (~3 files, ~400-600 LOC)
**Dependencies:** Phase 1
**Parallelizable:** Yes — all three files are independent

### Goals
- `plan-next` is rewritten from scratch as a useful, methodology-driven command
- `setup-statusline` has proper structure, validation, and safety
- `consolidate-documents` has clear input flow, output examples, and error handling

### Work Items

#### 2.1 Rewrite `plan-next.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R1
**Files Affected:**
- `plugins/personal-plugin/commands/plan-next.md` (modify)

**Description:**
Complete rewrite of plan-next from its current 47-line skeleton to a 150-200 line structured command. Replaces "Ultrathink" jargon with concrete methodology, adds plan-awareness, git-awareness, a decision matrix, structured output template, error handling, and examples.

**Tasks:**
1. [ ] Replace the entire command body with a new structured format
2. [ ] Add plan-awareness: "Step 1: Check for IMPLEMENTATION_PLAN.md. If found, read it and identify the next PENDING work item. Check for RECOMMENDATIONS.md. Report both."
3. [ ] Add git-awareness: "Step 2: Run `git status`, check for uncommitted changes. Run `git branch --list` and `gh pr list` to check for open branches and PRs."
4. [ ] Add decision matrix section: "Priority order: (1) Blocked work — items marked IN_PROGRESS or with uncommitted changes, (2) Critical fixes — any RECOMMENDATIONS.md items marked Critical, (3) Next plan phase — next PENDING item in IMPLEMENTATION_PLAN.md, (4) Highest-priority recommendation — if no plan exists"
5. [ ] Add structured output template: "## Current State" (plan status, git status, open PRs), "## Recommended Action" (what to do next), "## Rationale" (why this action), "## Scope Estimate" (S/M/L with standard sizing table)
6. [ ] Replace "~100K tokens" with standard S/M/L sizing table matching plan-improvements format
7. [ ] Add error handling section: no plan file found, no recommendations found, all items complete, dirty git state
8. [ ] Add example of output for each scenario (plan in progress, no plan, all complete)
9. [ ] Update `allowed-tools` to: `Read, Glob, Grep, Bash(git:*), Bash(gh:*)`

**Acceptance Criteria:**
- [ ] Command is 150-200 lines with clear methodology
- [ ] Checks for IMPLEMENTATION_PLAN.md and RECOMMENDATIONS.md
- [ ] Checks git status and open PRs
- [ ] Produces structured output with Current State, Recommended Action, Rationale, Scope Estimate
- [ ] Zero instances of "Ultrathink" jargon
- [ ] Has error handling and examples sections

**Notes:**
This is the highest-value rewrite. A working plan-next command closes the loop on the planning pipeline — plan-improvements generates recommendations, create-plan builds the plan, implement-plan executes it, and plan-next tells you what to do next at any point.

---

#### 2.2 Rewrite `setup-statusline.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R2
**Files Affected:**
- `plugins/personal-plugin/commands/setup-statusline.md` (modify)

**Description:**
Restructure setup-statusline from a PowerShell script dump into a proper phased command with pre-flight checks, safe file operations, and verification. Currently 175 lines with 80% being a raw script and no validation or error handling.

**Tasks:**
1. [ ] Add phased structure: Phase 1 (Pre-flight checks) -> Phase 2 (Create/update script) -> Phase 3 (Merge settings) -> Phase 4 (Verification)
2. [ ] Phase 1: Detect `pwsh` version (require PowerShell 7+). Check if `settings.json` already exists. Check if statusline script already exists.
3. [ ] Phase 2: Write the statusline PowerShell script to the target location. If file exists, back it up first with timestamp suffix.
4. [ ] Phase 3: Implement settings.json merge logic — read existing settings, add/update the statusline configuration, write back. Do NOT overwrite the entire file.
5. [ ] Phase 4: Run a verification step that tests the statusline script produces expected output format
6. [ ] Add `--dry-run` flag: show what would be changed without making changes
7. [ ] Add `--uninstall` flag: remove statusline configuration and script, restoring backups if available
8. [ ] Add error handling section: pwsh not found, wrong version, settings.json parse error, script write failure, permission errors
9. [ ] Add backup documentation: "All overwritten files are backed up to `[filename].backup.[timestamp]`"

**Acceptance Criteria:**
- [ ] Command has 4 distinct phases with clear boundaries
- [ ] Never overwrites settings.json without merging
- [ ] Backs up existing files before modification
- [ ] `--dry-run` and `--uninstall` flags documented
- [ ] PowerShell version detection present
- [ ] Error handling section with specific failure modes

**Notes:**
The PowerShell script content itself is fine and does not need to change. The issue is the command's structure around it — no validation, no merge logic, no safety nets.

---

#### 2.3 Overhaul `consolidate-documents.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R3
**Files Affected:**
- `plugins/personal-plugin/commands/consolidate-documents.md` (modify)

**Description:**
Expand consolidate-documents from 134 lines to 250+ lines. Resolve contradictory input flow, add complete output example with consolidation notes, add flags, and add error handling.

**Tasks:**
1. [ ] Resolve contradictory input flow: pick one mechanism for specifying input files. Recommended: accept file paths as arguments, with interactive prompting as fallback if no arguments given.
2. [ ] Add `--format` flag: output format (markdown, text). Default: markdown.
3. [ ] Add `--preview` flag: show consolidated outline before writing full output
4. [ ] Add `--no-prompt` flag: skip confirmation prompts for automation
5. [ ] Define how `[topic]` is derived in output filename: "Use the common topic across all input documents. If documents have different topics, prompt the user for a topic name."
6. [ ] Add complete output example showing: header with source documents listed, consolidation notes explaining what was merged/resolved, the consolidated content itself
7. [ ] Add error handling section: no files specified and none found, single document provided (nothing to consolidate), files in different formats, identical documents (no consolidation needed), file not found, binary file provided
8. [ ] Add context management: "For large documents, read each document's structure first (headings, sections) before reading full content. If total content exceeds 60% of context, summarize less important sections."

**Acceptance Criteria:**
- [ ] Single, clear input mechanism (no contradictions)
- [ ] `--format`, `--preview`, `--no-prompt` flags documented
- [ ] Complete output example present
- [ ] Topic derivation logic defined
- [ ] Error handling section with 6+ failure modes
- [ ] Expanded to 250+ lines

**Notes:**
This is the most complex overhaul in terms of design decisions. The contradictory input flow is the root cause of user confusion — resolving it cleanly is the priority.

---

### Phase 2 Testing Requirements
- [ ] Verify plan-next produces structured output with all four sections
- [ ] Verify setup-statusline has merge logic for settings.json
- [ ] Verify consolidate-documents has single clear input mechanism
- [ ] Verify all three files have error handling sections

### Phase 2 Completion Checklist
- [ ] All work items complete
- [ ] All three commands significantly expanded and restructured
- [ ] Documentation updated (help skill entries for changed commands)
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 3: Structural Improvements Part A

**Estimated Complexity:** M (~4 files, ~300-500 LOC)
**Dependencies:** Phase 1
**Parallelizable:** Yes — all four files are independent

### Goals
- define-questions and finish-document have consistent, working schema references
- review-arch uses task-based assessment with structured output template
- check-updates has an honest description of what it actually does

### Work Items

#### 3.1 Fix `define-questions.md` Phantom Schema References
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R4
**Files Affected:**
- `plugins/personal-plugin/commands/define-questions.md` (modify)

**Description:**
Replace references to non-existent `schemas/questions.json` with inline validation rules. Standardize field names and add missing fields to ensure JSON and CSV formats are consistent.

**Tasks:**
1. [x] Remove all references to `schemas/questions.json` or `schemas/` directory
2. [x] Add inline validation rules section: define the expected JSON schema directly in the command file with required fields, types, and constraints
3. [x] Standardize on one field name: use `question` (not `text`) across all output formats
4. [x] Add `priority` field to JSON schema example to match CSV format (both formats should have the same fields)
5. [x] Add error handling section: file not found, empty document, binary file, no questions found, document too large for context
6. [x] Add "Related Commands" section linking to `/ask-questions` and `/finish-document` (if not already added in Phase 1)

**Acceptance Criteria:**
- [x] Zero references to `schemas/` directory
- [x] Inline validation rules present in the command
- [x] Field names consistent between JSON and CSV formats
- [x] `priority` field present in both formats
- [x] Error handling section present

---

#### 3.2 Fix `finish-document.md` Phantom References and Resume Contradiction
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R5
**Files Affected:**
- `plugins/personal-plugin/commands/finish-document.md` (modify)

**Description:**
Resolve phantom schema references (same approach as 3.1), fix the contradictory resume mechanism, add bounds checking for navigation, and expand error handling.

**Tasks:**
1. [x] Remove all `schemas/` directory references. Add inline validation rules matching the approach in define-questions (work item 3.1)
2. [x] Pick one resume mechanism: auto-detect unanswered questions from the JSON file (recommended). Remove the contradictory explicit flag approach. Document the chosen mechanism clearly.
3. [x] Add bounds checking for `go to [N]` navigation: "Validate that N is within the range of questions (1 to total). If out of bounds, display available range and reprompt."
4. [x] Expand error handling section: questions file not found, questions file has no unanswered items, source document not found, source document is read-only, question index out of bounds, malformed JSON in questions file
5. [x] Add performance guidance: "For documents with 50+ questions, process in batches of 10. Show progress indicator."

**Acceptance Criteria:**
- [x] Zero references to `schemas/` directory
- [x] Single, clear resume mechanism (no contradiction)
- [x] Bounds checking for question navigation
- [x] Error handling section with 6+ failure modes
- [x] Performance guidance for large question sets

---

#### 3.3 Restructure `review-arch.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R6
**Files Affected:**
- `plugins/personal-plugin/commands/review-arch.md` (modify)

**Description:**
Rewrite assessment dimensions as imperative tasks (matching plan-improvements style). Add structured output template. Define T-shirt sizes. Add examples. Move read-only guardrail to top.

**Tasks:**
1. [x] Move "DO NOT MAKE ANY CHANGES TO FILES" guardrail from wherever it is to the top of the file, immediately after frontmatter, before any instructions
2. [x] Rewrite assessment dimensions from descriptive/question format to imperative task-based format. For example: "Trace the 3 most common user workflows..." instead of "Consider the usability of..."
3. [x] Add structured output template: "## Executive Summary" (2-3 paragraphs), "## Architecture Scorecard" (table with dimensions and ratings), "## Findings" (numbered, severity-tagged), "## Remediation Roadmap" (prioritized list with T-shirt sizes)
4. [x] Define T-shirt sizes with standard S/M/L table matching plan-improvements complexity scale
5. [x] Add examples section: show a sample scorecard table and 2-3 sample findings with proper formatting
6. [x] Add error handling section: empty project, project too large for context, no source code found

**Acceptance Criteria:**
- [x] Read-only guardrail is at the top of the file
- [x] Assessment dimensions use imperative tasks, not questions
- [x] Structured output template with 4 sections
- [x] T-shirt size definitions present
- [x] Examples section present

---

#### 3.4 Rethink `check-updates.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R7
**Files Affected:**
- `plugins/personal-plugin/commands/check-updates.md` (modify)

**Description:**
Either make check-updates a true remote check (fetching latest marketplace.json from GitHub) or reframe it honestly as a "version consistency audit". Remove misleading "Updates Available" language if keeping local-only. Add error handling.

**Tasks:**
1. [x] Decide approach: implement true remote check using `gh api` to fetch the latest `marketplace.json` from the `davistroy/claude-marketplace` repository, comparing remote versions against locally installed versions
2. [x] If remote check approach: add `gh api repos/davistroy/claude-marketplace/contents/.claude-plugin/marketplace.json` call to fetch remote version data. Compare remote `version` fields against local `plugins/*/. claude-plugin/plugin.json` versions.
3. [x] Remove misleading "Updates Available" language if the command cannot actually check remote versions. Replace with "Version Consistency Report" if local-only.
4. [x] Add proper error handling section: GitHub API unavailable, no network connection, marketplace not configured, invalid version format, local plugin not in marketplace
5. [x] Add output format: table showing plugin name, local version, remote version (or N/A), status (up-to-date, update available, local-only)

**Acceptance Criteria:**
- [x] Command either checks remote versions or is honestly labeled as local-only
- [x] No misleading "Updates Available" language if local-only
- [x] Error handling section present
- [x] Clear output format defined

**Notes:**
The remote check approach is preferred since the entire point of this command is to know if updates exist. A local-only version consistency audit is a fallback if remote access proves unreliable. **Decision taken:** Implemented remote check as primary with graceful local-only fallback when `gh` is unavailable or network fails.

---

### Phase 3 Testing Requirements
- [ ] Verify zero references to `schemas/` in define-questions and finish-document
- [ ] Verify review-arch produces structured output with scorecard and findings
- [ ] Verify check-updates has accurate description of its capabilities
- [ ] Verify all four files have error handling sections

### Phase 3 Completion Checklist
- [ ] All work items complete
- [ ] Schema references resolved consistently
- [ ] Review-arch output template tested
- [ ] Check-updates honestly represents its capabilities
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 4: Structural Improvements Part B

**Estimated Complexity:** M (~5 files, ~300-500 LOC)
**Dependencies:** Phase 1
**Parallelizable:** Yes — all five files are independent

### Goals
- scaffold-plugin produces correct skill paths
- convert-hooks has honest expectations about conversion quality
- convert-markdown has useful analysis or removes dead analysis step
- new-command references working post-generation steps
- security-analysis has proper structure for a skill

### Work Items

#### 4.1 Fix `scaffold-plugin.md` Correctness Bug
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R8
**Files Affected:**
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify)

**Description:**
Fix the bug where scaffold-plugin outputs `skills/help.md` instead of the correct `skills/help/SKILL.md`. Remove dead script references. Extract inline help template. Add `--dry-run` flag. Fix JSON keywords example.

**Tasks:**
1. [ ] Fix bug: change `skills/help.md` to `skills/help/SKILL.md` in the output report/generation sections (search for all occurrences)
2. [ ] Remove dead `python scripts/` references (may already be done in Phase 1 work item 1.3; verify and remove any remaining)
3. [ ] Extract the ~80-line inline help template to a reference file or clearly mark it as an embedded template with start/end markers for maintainability
4. [ ] Add `--dry-run` flag: "Show the directory structure and file list that would be created without creating any files"
5. [ ] Fix JSON `keywords` example: ensure the example shows valid JSON array syntax
6. [ ] Add error handling section: target directory already exists, invalid plugin name (special characters), disk full, permission errors

**Acceptance Criteria:**
- [ ] All references to help skill use correct path `skills/help/SKILL.md`
- [ ] Zero dead script references
- [ ] `--dry-run` flag documented
- [ ] JSON examples are valid
- [ ] Error handling section present

---

#### 4.2 Improve `convert-hooks.md` Honesty
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R9
**Files Affected:**
- `plugins/personal-plugin/commands/convert-hooks.md` (modify)

**Description:**
Add prominent warning about conversion limitations, add concrete before/after example, add platform detection, and add validation step for generated scripts.

**Tasks:**
1. [ ] Add prominent warning at the top (after frontmatter): "**Limitation:** Automated conversion handles only simple bash scripts (variable assignments, conditionals, file operations, path manipulations). Complex scripts with pipes, process substitution, awk/sed, or signal handling require manual review."
2. [ ] Add concrete before/after example: show a simple bash hook (5-10 lines) and its PowerShell equivalent
3. [ ] Add platform detection: "Detect the current platform. On Windows, convert bash to PowerShell. On macOS/Linux, convert PowerShell to bash. Do not present both conversion directions — detect and offer the relevant one."
4. [ ] Add `--validate` step: "After generating the PowerShell script, run `pwsh -c 'Get-Command -Syntax ...'` or equivalent syntax check to verify the script is valid PowerShell"
5. [ ] Add error handling section: source hook file not found, unsupported script complexity, PowerShell not installed, validation failure

**Acceptance Criteria:**
- [ ] Conversion limitation warning is prominently placed
- [ ] Before/after example present
- [ ] Platform detection replaces manual direction listing
- [ ] Validation step documented
- [ ] Error handling section present

---

#### 4.3 Expand `convert-markdown.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R10
**Files Affected:**
- `plugins/personal-plugin/commands/convert-markdown.md` (modify)

**Description:**
Either make the pre-conversion analysis step useful (by customizing pandoc flags based on document content) or remove it. Add error handling for pandoc failures. Add optional flags.

**Tasks:**
1. [ ] Decide on analysis step: keep it and make it useful by having it detect document features (tables, code blocks, images, math) and add corresponding pandoc flags (`--highlight-style`, `--reference-doc`, `--toc`). If features detected, explain what flags were added and why.
2. [ ] Add `--no-toc` flag: skip table of contents generation
3. [ ] Add `--style <path>` flag: use a custom reference document for styling
4. [ ] Add `--dry-run` flag: show the pandoc command that would be run without executing it
5. [ ] Add error handling section: pandoc not installed (with installation instructions per platform), source file not found, pandoc conversion failure (exit code != 0), output file already exists (overwrite confirmation), unsupported markdown features

**Acceptance Criteria:**
- [ ] Analysis step either produces actionable pandoc flag customization or is removed
- [ ] `--no-toc`, `--style`, `--dry-run` flags documented
- [ ] Error handling section with pandoc-specific failure modes
- [ ] Platform-specific pandoc installation instructions

---

#### 4.4 Fix `new-command.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R11
**Files Affected:**
- `plugins/personal-plugin/commands/new-command.md` (modify)

**Description:**
Remove dead script references (verify Phase 1 cleanup), add plugin target parameter, add `orchestration` pattern type, add post-generation validation.

**Tasks:**
1. [ ] Verify dead `python scripts/` references were removed in Phase 1 (work item 1.3). If any remain, remove them now. Replace with: "After generation, update `skills/help/SKILL.md` with the new command entry."
2. [ ] Add plugin target parameter: "Detect which plugin the user is working in. If multiple plugins exist, prompt for target plugin. If only one plugin exists, use it automatically."
3. [ ] Add `orchestration` to the list of command pattern types (alongside generator, read-only, interactive, workflow, etc.)
4. [ ] Add post-generation validation step: "After creating the command file, run a quick validation: check frontmatter has required fields, check file is in the correct `commands/` directory, verify no duplicate command name exists."
5. [ ] Add error handling: invalid command name, command already exists, target plugin not found

**Acceptance Criteria:**
- [ ] Zero dead script references
- [ ] Plugin target detection implemented
- [ ] `orchestration` pattern type listed
- [ ] Post-generation validation step present
- [ ] Error handling section present

---

#### 4.5 Overhaul `security-analysis` Skill
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R12
**Files Affected:**
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify)

**Description:**
Add input validation with arguments, add proactive trigger section, add error handling, remove duplicate inline technology patterns (that duplicate separate reference files), and replace emoji severity labels with text.

**Tasks:**
1. [ ] Add input validation section with optional arguments: path scope (directory to analyze), `--quick` (surface scan only), `--dependencies-only` (only check dependency vulnerabilities)
2. [ ] Add proactive trigger section: "Suggest this skill when: (1) user mentions security, vulnerabilities, or audit; (2) after scaffolding a new project; (3) before a release or deployment; (4) when reviewing code that handles authentication, authorization, or user input"
3. [ ] Add error handling section: no source files found, project too large, audit tools not installed, permission denied on file access
4. [ ] Add output location: "Write security report to `reports/security-analysis-[timestamp].md`"
5. [ ] Add performance expectations: "Quick scan: 1-3 minutes. Full scan: 5-15 minutes depending on codebase size."
6. [ ] Remove inline technology detection patterns that duplicate content already in the `references/` directory. Replace with: "Refer to reference files for technology-specific patterns."
7. [ ] Replace emoji severity indicators (if any) with text labels: CRITICAL, HIGH, MEDIUM, LOW

**Acceptance Criteria:**
- [ ] Input arguments documented (path, --quick, --dependencies-only)
- [ ] Proactive trigger section present
- [ ] Error handling section present
- [ ] No duplicate content between skill and reference files
- [ ] Severity uses text labels, not emoji

---

### Phase 4 Testing Requirements
- [ ] Verify scaffold-plugin generates correct `skills/help/SKILL.md` path
- [ ] Verify convert-hooks has limitation warning and before/after example
- [ ] Verify convert-markdown analysis step is useful or removed
- [ ] Verify new-command has plugin target detection
- [ ] Verify security-analysis has proactive triggers

### Phase 4 Completion Checklist
- [ ] All work items complete
- [ ] All five files significantly improved
- [ ] Documentation updated (help skill entries for changed commands/skills)
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 5: Targeted Fixes Part A

**Estimated Complexity:** M (~4 files, ~200-300 LOC)
**Dependencies:** Phase 1
**Parallelizable:** Yes — all four files are independent

### Goals
- test-project uses safe git patterns and modern Co-Authored-By
- assess-document has consistent output naming and score anchors
- analyze-transcript has error handling and context management
- develop-image-prompt has clear input flow and complete examples

### Work Items

#### 5.1 Fix `test-project.md` Safety Issues
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R13
**Files Affected:**
- `plugins/personal-plugin/commands/test-project.md` (modify)

**Description:**
Replace unsafe git patterns, update Co-Authored-By format, replace auto-merge with confirmation, add coverage argument, and add scope confirmation gate.

**Tasks:**
1. [ ] Replace all instances of `git add -A` with selective staging: "Use `git add [specific-files]` listing only the files that were modified during testing. Run `git status --short` first to identify changes."
2. [ ] Update Co-Authored-By tag from any older format to: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
3. [ ] Replace auto-merge behavior with user confirmation: "After all tests pass and PR is created, ask: 'Tests passing. Merge this PR? (yes/no)'. Do NOT merge automatically."
4. [ ] Add `--coverage <n>` optional argument: "Target coverage percentage (default: 90). Example: `--coverage 80`"
5. [ ] Add scope confirmation gate at the start: "Before making any changes, present: files that will be modified, test frameworks detected, current coverage (if measurable). Ask: 'Proceed with this scope? (yes/adjust/abort)'"

**Acceptance Criteria:**
- [ ] Zero instances of `git add -A`
- [ ] Co-Authored-By uses `Claude Opus 4.6` format
- [ ] No auto-merge — user confirmation required
- [ ] `--coverage` flag documented
- [ ] Scope confirmation gate present before changes

---

#### 5.2 Fix `assess-document.md` Naming Inconsistency
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R14
**Files Affected:**
- `plugins/personal-plugin/commands/assess-document.md` (modify)

**Description:**
Fix output file naming to use ONE consistent pattern. Add score anchor definitions. Fix code fence language. Add error handling.

**Tasks:**
1. [ ] Find all output file naming patterns in the command. Pick ONE: `assessment-[source]-[timestamp].md`. Remove all alternative naming patterns.
2. [ ] Add score anchor definitions for the 1-5 rubric: "1 = Fundamentally flawed, requires rewrite. 2 = Significant gaps, major revision needed. 3 = Adequate, several improvements needed. 4 = Good, minor improvements needed. 5 = Excellent, ready for use."
3. [ ] Fix `yaml` code fence language to `text` in examples where the content is not actually YAML
4. [ ] Add error handling section: file not found, binary file, empty file, file too large for context, unsupported format

**Acceptance Criteria:**
- [ ] ONE output file naming pattern, consistently used
- [ ] Score anchor definitions present for all 5 levels
- [ ] Code fence languages are accurate
- [ ] Error handling section present

---

#### 5.3 Improve `analyze-transcript.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R15
**Files Affected:**
- `plugins/personal-plugin/commands/analyze-transcript.md` (modify)

**Description:**
Add error handling, add `--no-prompt` flag, replace vague input flow with concrete interactive flow, add context management for large transcripts.

**Tasks:**
1. [ ] Add error handling section: no transcript provided, empty transcript, transcript too large (>50K tokens), binary file, no actionable content found
2. [ ] Add `--no-prompt` flag: "Skip confirmation prompts. Use defaults for all options."
3. [ ] Replace vague "paste content" note with concrete interactive flow: "Step 1: Ask user for transcript source (file path or paste). Step 2: If file path, read file. If paste, accept multi-line input. Step 3: Confirm transcript length and estimated analysis time."
4. [ ] Add context/size management: "For transcripts exceeding 30K tokens, process in sections: first pass extracts key decisions and action items from each section, second pass synthesizes across sections."

**Acceptance Criteria:**
- [ ] Error handling section with 5+ failure modes
- [ ] `--no-prompt` flag documented
- [ ] Clear, concrete input flow (no vague instructions)
- [ ] Context management for large transcripts

---

#### 5.4 Improve `develop-image-prompt.md`
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R16
**Files Affected:**
- `plugins/personal-plugin/commands/develop-image-prompt.md` (modify)

**Description:**
Add dimensions flag, add complete example, resolve contradictory input flow, define when style variations are generated.

**Tasks:**
1. [ ] Add `--dimensions <WxH>` flag: "Override default dimensions (default: 11x17). Example: `--dimensions 16x9`"
2. [ ] Add complete example of an actual generated prompt: show the full output for a sample input, including the image prompt text, dimensions, style notes, and any variations
3. [ ] Resolve contradictory input flow: pick one mechanism. Recommended: accept a file path or topic as argument, prompt interactively if neither provided
4. [ ] Define when style variations are generated: "Generate 2-3 style variations when the input has multiple possible visual interpretations. Skip variations when the input specifies a clear single visual direction."
5. [ ] Add error handling: no input provided, file not found, content too abstract to visualize, unsupported file format

**Acceptance Criteria:**
- [ ] `--dimensions` flag documented with default value
- [ ] Complete example with actual prompt output present
- [ ] Single clear input mechanism (no contradiction)
- [ ] Style variation rules defined
- [ ] Error handling section present

---

### Phase 5 Testing Requirements
- [ ] Verify zero instances of `git add -A` in test-project
- [ ] Verify assess-document has single naming pattern
- [ ] Verify analyze-transcript has concrete input flow
- [ ] Verify develop-image-prompt has complete example output

### Phase 5 Completion Checklist
- [ ] All work items complete
- [ ] All four files have targeted improvements
- [ ] Documentation updated (help skill entries)
- [ ] No regressions in existing command functionality
- [ ] Code reviewed (if applicable)

---

## Phase 6: Targeted Fixes Part B

**Estimated Complexity:** M (~5 files, ~200-400 LOC)
**Dependencies:** Phase 1
**Parallelizable:** Yes — all five files are independent

### Goals
- review-intent, review-pr, and remove-ip have proper tool restrictions and error handling
- ship skill has consistent phase numbering and proactive triggers
- research-topic has extracted API key wizard and proper secrets policy

### Work Items

#### 6.1 Fix `review-intent.md` Minor Issues
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R17
**Files Affected:**
- `plugins/personal-plugin/commands/review-intent.md` (modify)

**Description:**
Add argument detection, update allowed-tools, replace shell redirection save with proper file write offer, define "sparse" explicitly, add calculation guidance.

**Tasks:**
1. [x] Add argument detection instructions: "Check if the user provided a file path or directory as argument. If provided, scope the review to that path. If not provided, review the entire project."
2. [x] Verify `allowed-tools` was set correctly in Phase 1 (should be `Read, Glob, Grep` for a read-only command). Confirm it does not include Write.
3. [x] Replace any shell redirection save suggestion (e.g., `> output.txt`) with: "Offer to save the review to a file using the Write tool: 'Would you like me to save this review to `reports/intent-review-[timestamp].md`?'"
4. [x] Define "sparse" explicitly: "A 'sparse' area is one where fewer than 20% of source files have corresponding test files, or where documentation covers fewer than 50% of public APIs."
5. [x] Add calculation guidance for any metrics (e.g., Phase 3.3 coverage metrics): "Calculate coverage as: (documented public APIs / total public APIs) * 100. Report as both fraction and percentage."

**Acceptance Criteria:**
- [x] Argument detection documented
- [x] Correct `allowed-tools` in frontmatter
- [x] No shell redirection patterns — uses Write tool for saving
- [x] "Sparse" defined with concrete thresholds
- [x] Metric calculation guidance present

**Notes:**
If the user wants to save the review, the command needs `Write` in allowed-tools. Update to `Read, Glob, Grep, Write` and add the save-to-file offer.

---

#### 6.2 Fix `review-pr.md` Minor Issues
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R18
**Files Affected:**
- `plugins/personal-plugin/commands/review-pr.md` (modify)

**Description:**
Add Read to allowed-tools, reorder review guidelines, inline severity definitions, add error handling for edge cases.

**Tasks:**
1. [x] Add `Read` to the `allowed-tools` frontmatter (needed to read file contents during review)
2. [x] Move review guidelines section to appear before Phase 1 (before analysis begins), so guidelines are established before code is read
3. [x] Inline severity definitions instead of referencing an external file: "CRITICAL: Security vulnerability, data loss risk, or production crash. HIGH: Logic error, missing validation, or broken feature. MEDIUM: Code quality issue, missing test, or unclear logic. LOW: Style, naming, or minor optimization."
4. [x] Add error handling for: diff exceeds context window (suggest reviewing by file), binary files in diff (skip with note), already-merged PR (inform user, offer to review commit instead), draft PR (note draft status, proceed with review)

**Acceptance Criteria:**
- [x] `Read` in allowed-tools
- [x] Review guidelines appear before Phase 1
- [x] Severity definitions inlined (no external file reference)
- [x] Error handling for 4 edge cases

---

#### 6.3 Fix `remove-ip.md` Structural Issue
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R19
**Files Affected:**
- `plugins/personal-plugin/commands/remove-ip.md` (modify)

**Description:**
Remove the "Trigger phrases" section (which is a skill pattern, not a command pattern). Add allowed-tools and error handling. Add web research tool guidance.

**Tasks:**
1. [x] Remove the "Trigger phrases" section entirely — commands are invoked explicitly, not triggered by phrases
2. [x] Verify `allowed-tools` was set correctly in Phase 1 (should be `Read, Write, Edit, Glob, Grep` for a file generator)
3. [x] Add error handling section: file not found, binary file, file has no identifiable IP to remove, file is already de-identified, permission errors
4. [x] Add web research tool guidance: "If the user asks to verify that company information has been removed, use WebSearch to check if remaining terms are generic (not company-specific). Do not use web tools by default — only when verification is requested."

**Acceptance Criteria:**
- [x] Zero "Trigger phrases" sections
- [x] Correct `allowed-tools` in frontmatter
- [x] Error handling section present
- [x] Web research guidance present (optional use only)

---

#### 6.4 Fix `ship` Skill Issues
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R20
**Files Affected:**
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify)

**Description:**
Fix phase numbering inconsistency, add proactive trigger section, add destructive action warning, update Co-Authored-By format.

**Tasks:**
1. [x] Audit all phase/step numbers in the skill. Renumber consistently: Phase 1 (Branch), Phase 2 (Stage & Commit), Phase 3 (Push), Phase 4 (PR). Fix any gaps or duplicates.
2. [x] Add proactive trigger section: "Suggest this skill when: (1) user says 'done', 'ready to ship', or 'push this'; (2) after completing a work item from an implementation plan; (3) after all tests pass; (4) user asks to create a PR"
3. [x] Add risk/destructive-action warning: "This skill modifies git state (creates branches, commits, pushes). Before proceeding, confirm the user intends to ship. Never force-push or push to main/master directly."
4. [x] Update Co-Authored-By to: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

**Acceptance Criteria:**
- [x] Phase numbers are consistent and sequential
- [x] Proactive trigger section present
- [x] Destructive action warning present
- [x] Co-Authored-By uses current format

---

#### 6.5 Fix `research-topic` Skill
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R21
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify)
- `plugins/personal-plugin/references/api-key-setup.md` (create)

**Description:**
Extract API key setup wizard to reduce file size, fix secrets policy violation (reference /unlock), add `--skip-model-check` argument, add proactive trigger section.

**Tasks:**
1. [x] Extract the API key setup wizard (~130+ lines) to a reference file at `plugins/personal-plugin/references/api-key-setup.md`. Replace in-skill content with: "For API key configuration, see `references/api-key-setup.md`. Primary method: run `/unlock` to load keys from Bitwarden."
2. [x] Fix secrets policy: ensure the extracted reference file and the skill itself reference `/unlock` as the primary path. Remove any instructions that write keys to `.env` files (verify Phase 1 work item 1.5 is complete).
3. [x] Add `--skip-model-check` to the arguments table: "Skip the model availability check at startup. Useful when you know models are available and want to start immediately."
4. [x] Add proactive trigger section: "Suggest this skill when: (1) user asks to research a topic in depth; (2) user wants to compare perspectives across multiple AI providers; (3) user needs a comprehensive analysis that benefits from multi-source synthesis"

**Acceptance Criteria:**
- [x] API key setup wizard extracted to reference file (~130+ lines removed from skill)
- [x] `/unlock` is the primary secrets path
- [x] Zero `.env` write instructions in the skill
- [x] `--skip-model-check` documented
- [x] Proactive trigger section present

---

### Phase 6 Testing Requirements
- [x] Verify review-intent has argument detection and defined metrics
- [x] Verify review-pr has inlined severity definitions
- [x] Verify remove-ip has no trigger phrases section
- [x] Verify ship has consistent phase numbering
- [x] Verify research-topic API key wizard is extracted and /unlock is primary

### Phase 6 Completion Checklist
- [x] All work items complete
- [x] All five files have targeted improvements
- [x] Documentation updated (help skill entries)
- [x] No regressions in existing command functionality
- [x] Code reviewed (if applicable)

---

## Phase 7: Skill Improvements & Final Polish

**Estimated Complexity:** M (~8 files, ~300-500 LOC)
**Dependencies:** Phases 1-6
**Parallelizable:** Yes — work items 7.1-7.5 are independent; 7.6 depends on all others

### Goals
- Remaining skills have proactive triggers and targeted fixes
- Utility commands have batch fixes applied
- Unlock skill shell injection risk is fixed
- Error handling audit confirms coverage across all files
- Proactive trigger coverage is complete for all skills
- Flag patterns are consistent across commands

### Work Items

#### 7.1 Fix Remaining Skills Batch
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R22
**Files Affected:**
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)
- `plugins/personal-plugin/skills/validate-and-ship/SKILL.md` (modify)

**Description:**
Batch fixes for summarize-feedback, visual-explainer, and validate-and-ship: add proactive triggers to all three, plus targeted fixes per skill.

**Tasks:**
1. [ ] `summarize-feedback`: Add proactive trigger section: "Suggest when: user mentions feedback analysis, Notion export, or assessment report generation"
2. [ ] `summarize-feedback`: Add context-size guardrail: "For entry counts exceeding 100, process in batches of 25. Warn user if total input exceeds 60% of context window."
3. [ ] `visual-explainer`: Add proactive trigger section: "Suggest when: user has a document or concept they want visualized, after generating a report or analysis that would benefit from visual summary"
4. [ ] `visual-explainer`: Document the `--json` flag if it exists but is undocumented. Fix default confidence threshold if the current default produces too many or too few images.
5. [ ] `visual-explainer`: Verify secrets policy fix from Phase 1 (work item 1.5). Reference `/unlock` for API keys.
6. [ ] `validate-and-ship`: Add proactive trigger section: "Suggest when: user is done making changes to a plugin, after running /validate-plugin, before shipping plugin updates"
7. [ ] `validate-and-ship`: Clarify the delegation mechanism: explain how this skill coordinates between `/validate-plugin` and `/ship` — whether it runs them sequentially or delegates.
8. [ ] `validate-and-ship`: Add `--skip-ship` flag: "Run validation only, do not proceed to shipping. Useful for pre-flight checks."

**Acceptance Criteria:**
- [ ] All three skills have proactive trigger sections
- [ ] summarize-feedback has context-size guardrail
- [ ] visual-explainer has documented flags and correct secrets policy
- [ ] validate-and-ship has clear delegation description and `--skip-ship` flag

---

#### 7.2 Fix Utility Commands Batch
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R23
**Files Affected:**
- `plugins/personal-plugin/commands/bump-version.md` (modify)
- `plugins/personal-plugin/commands/clean-repo.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/commands/validate-plugin.md` (modify)
- `plugins/personal-plugin/commands/ask-questions.md` (modify)

**Description:**
Batch fixes for five utility commands: dynamic scanning, tool usage, dead reference removal, section numbering fix, and resume support alignment.

**Tasks:**
1. [x] `bump-version`: Verify dynamic plugin scanning was implemented in Phase 1 (work item 1.4). Add any remaining improvements to plugin discovery.
2. [x] `clean-repo`: Replace `find` command usage with Glob tool instructions. Example: replace `find . -name "*.tmp"` with "Use the Glob tool to find temporary files: `**/*.tmp`, `**/.DS_Store`, `**/Thumbs.db`"
3. [x] `clean-repo`: Add context management: "For large repositories (100+ files), process directories in batches. Show progress."
4. [x] `new-skill`: Remove dead script references (verify Phase 1 work item 1.3). Add plugin target parameter: "Detect which plugin the user is working in. If multiple plugins exist, prompt."
5. [x] `validate-plugin`: Fix duplicate section numbering: search for any duplicate heading numbers and renumber sequentially
6. [x] `validate-plugin`: Fix skill path example: ensure examples show `skills/name/SKILL.md` (nested), not `skills/name.md` (flat)
7. [x] `ask-questions`: Align resume support with the output JSON schema. Ensure the JSON format includes a field (e.g., `answered: true/false`) that enables resume detection when re-running the command.

**Acceptance Criteria:**
- [x] bump-version discovers plugins dynamically
- [x] clean-repo uses Glob tool, not shell `find`
- [x] new-skill has no dead references and has plugin target parameter
- [x] validate-plugin has correct section numbering and skill path examples
- [x] ask-questions resume support aligns with JSON schema

---

#### 7.3 Fix `unlock` Skill Shell Injection Risk
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** R24
**Files Affected:**
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)

**Description:**
Fix the shell injection risk in the Linux `eval` pattern for loading secrets. Add proactive trigger section.

**Tasks:**
1. [x] Find the Linux `eval` pattern used for loading secrets into the environment. Replace with a safe alternative: use `shlex.quote()` (or equivalent shell escaping) for secret values before passing them to `eval` or `export`. Example: instead of `eval "export KEY=$VALUE"`, use `export KEY='properly-escaped-value'` with single quotes and internal single-quote escaping.
2. [x] Alternatively, replace `eval` entirely with direct `export` statements that properly quote values: `export KEY="$(bws get secret <id> | jq -r .value)"` where the subshell handles escaping naturally.
3. [x] Add proactive trigger section: "Suggest this skill when: (1) user starts a session and environment variables are needed; (2) before running skills that require API keys (research-topic, visual-explainer); (3) user mentions Bitwarden or secrets"

**Acceptance Criteria:**
- [x] No unescaped `eval` patterns with user/external data
- [x] Secret values are properly quoted or escaped before shell expansion
- [x] Proactive trigger section present

**Notes:**
This is a security fix on a 5/5-rated skill. The skill is excellent otherwise — this is the one gap.

---

#### 7.4 Error Handling Audit
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** S2
**Files Affected:**
- All 32 command and skill files (audit; modify as needed)

**Description:**
Audit all files for error handling sections. Add missing error handling to the ~20 files that lack it (most should have been added in Phases 2-6; this catches any gaps).

**Tasks:**
1. [x] Scan all 32 files for `## Error Handling` sections
2. [x] For files modified in Phases 2-6 that should already have error handling, verify it is present and adequate (3+ failure modes per file)
3. [x] For any remaining files without error handling, add a minimal section with the most likely failure modes: file not found, empty input, context window exhaustion, tool unavailability
4. [x] Ensure every error handling section uses a consistent format: failure mode name, description, recommended recovery action

**Acceptance Criteria:**
- [x] All 32 files have an error handling section (or equivalent inline handling)
- [x] Each error handling section has at least 3 failure modes
- [x] Consistent format across all files

**Notes:**
This is a sweep to catch gaps. Most error handling should have been added in the individual file improvements (Phases 2-6). This work item adds the last few. Audit completed 2026-02-28: 27 of 32 files already had error handling from Phases 2-6. Added error handling sections to the 5 remaining files: plan-improvements.md, review-intent.md, clean-repo.md, ask-questions.md, and skills/plan-gate/SKILL.md. All sections use consistent table format (Condition | Cause | Action) with 5-8 domain-specific failure modes each.

---

#### 7.5 Proactive Trigger Audit and Flag Consistency
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** S4, S5
**Files Affected:**
- All 9 skill files (audit; modify as needed)
- Commands that write output files (audit; modify as needed)

**Description:**
Audit all skills for proactive trigger sections. Audit commands for flag consistency. Skills should have been given triggers in Phases 4-7; this catches gaps. Commands that write files should have consistent flag sets.

**Tasks:**
1. [x] Audit all 9 skills (excluding plan-gate which already has triggers) for proactive trigger sections. Skills modified in earlier phases should already have them; verify.
2. [x] For `prime` skill: add proactive trigger: "Suggest when: user starts a new session, asks about the project, or says 'what is this project'"
3. [x] For `help` skill: add proactive trigger: "Suggest when: user asks what commands are available, says 'help', or seems unsure of what to do"
4. [x] Audit flag consistency across commands that write output files: ensure `--no-prompt`, `--preview`, and `--format` flags are consistently available where appropriate. At minimum: all file-generating commands should support `--no-prompt` for automation.
5. [x] Create a flag consistency reference: document which flags each command supports. This is for internal reference, not for end users.

**Acceptance Criteria:**
- [x] All 9 skills (excluding plan-gate) have proactive trigger sections
- [x] Commands that write files consistently support `--no-prompt`
- [x] Flag usage patterns documented for reference

---

#### 7.6 Update Help Skill and Final Verification
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-02-28]**
**Recommendation Ref:** (housekeeping)
**Files Affected:**
- `plugins/personal-plugin/skills/help/SKILL.md` (modify)

**Description:**
Update the help skill to reflect all changes made across Phases 1-7. Add entries for any new flags, arguments, or capabilities. Remove entries for anything removed. Verify all command and skill names are accurate.

**Tasks:**
1. [x] Review every command entry in help skill. Update descriptions to reflect new capabilities, flags, and arguments added in this plan.
2. [x] Review every skill entry in help skill. Update descriptions to reflect new proactive triggers and arguments.
3. [x] Verify all command names match actual filenames in `commands/` directory
4. [x] Verify all skill names match actual directory names in `skills/` directory
5. [x] Add entries for any new reference files created (e.g., `references/api-key-setup.md`)
6. [x] Run a final cross-check: for each command/skill listed in help, verify the file exists and the description is accurate

**Acceptance Criteria:**
- [x] Help skill accurately reflects all 26 commands and 10 skills
- [x] All new flags and arguments are documented in help entries
- [x] No stale or inaccurate entries remain

---

### Phase 7 Testing Requirements
- [x] Verify all skills have proactive trigger sections
- [x] Verify unlock skill has no shell injection vulnerability
- [x] Verify error handling is present in all 32 files
- [x] Verify help skill is accurate and complete
- [x] Verify flag patterns are consistent

### Phase 7 Completion Checklist
- [x] All work items complete
- [x] All skills have proactive triggers
- [x] Error handling audit complete
- [x] Flag consistency verified
- [x] Help skill updated
- [x] No regressions in existing command functionality
- [x] Code reviewed (if applicable)

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2, 1.3, 1.4, 1.5 | All modify different aspects of the same files; can be combined into a single pass per file |
| 2.1 | 2.2, 2.3 | Three independent files (plan-next, setup-statusline, consolidate-documents) |
| 3.1 | 3.2, 3.3, 3.4 | Four independent files |
| 4.1 | 4.2, 4.3, 4.4, 4.5 | Five independent files |
| 5.1 | 5.2, 5.3, 5.4 | Four independent files |
| 6.1 | 6.2, 6.3, 6.4, 6.5 | Five independent files |
| 7.1 | 7.2, 7.3 | Independent file groups (skills vs commands vs unlock) |
| 7.4 | 7.5 | Audit tasks can run in parallel |

**Cross-phase parallelism:** Phases 2-6 all depend only on Phase 1, not on each other. After Phase 1 completes, Phases 2-6 can run in any order or in parallel. Phase 7 depends on all prior phases.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Phase 1 batch changes introduce inconsistencies | Medium | Medium | Use a checklist per file to ensure all 5 cross-cutting fixes are applied consistently. Grep verification after each work item. |
| Major overhauls (Phase 2) break existing workflows | Low | High | Keep the same command names and invocation patterns. Only change internal instructions and structure. |
| allowed-tools restrictions are too narrow | Medium | Medium | Start with the recommended values. If a command fails due to tool restriction, widen the allowed-tools. |
| Dead reference removal misses some instances | Low | Low | Run global grep after Phase 1 to catch any remaining references. |
| Proactive triggers cause unwanted skill suggestions | Low | Medium | Make trigger conditions specific (3-4 conditions each). Test by describing scenarios and verifying triggers match. |
| Help skill update (7.6) misses changes | Medium | Low | Use a diff of all files changed in this plan as the checklist for help updates. |

---

## Success Metrics

- [x] All 32 files have `allowed-tools` in frontmatter
- [x] All 23 commands have "Related Commands" sections
- [x] All 9 skills (excluding plan-gate) have proactive trigger sections
- [x] All 32 files have error handling sections
- [x] Zero dead references to non-existent scripts or directories
- [x] Zero hardcoded plugin lists
- [x] Zero secrets policy violations
- [x] Average file rating improves from 3.5/5 to 4.5/5
- [x] All 24 individual recommendations (R1-R24) addressed
- [x] All 8 cross-cutting issues (S1-S8) resolved
- [x] Help skill accurately reflects all commands and skills

---

## Appendix: Recommendation Traceability

| Recommendation | Category | Phase | Work Item |
|----------------|----------|-------|-----------|
| S1 | Cross-Cutting: allowed-tools | 1 | 1.1 |
| S3 | Cross-Cutting: Related Commands | 1 | 1.2 |
| S6 | Cross-Cutting: Dead References | 1 | 1.3 |
| S7 | Cross-Cutting: Hardcoded Lists | 1 | 1.4 |
| S8 | Cross-Cutting: Secrets Policy | 1 | 1.5 |
| R1 | Major Overhaul: plan-next | 2 | 2.1 |
| R2 | Major Overhaul: setup-statusline | 2 | 2.2 |
| R3 | Major Overhaul: consolidate-documents | 2 | 2.3 |
| R4 | Structural: define-questions | 3 | 3.1 |
| R5 | Structural: finish-document | 3 | 3.2 |
| R6 | Structural: review-arch | 3 | 3.3 |
| R7 | Structural: check-updates | 3 | 3.4 |
| R8 | Structural: scaffold-plugin | 4 | 4.1 |
| R9 | Structural: convert-hooks | 4 | 4.2 |
| R10 | Structural: convert-markdown | 4 | 4.3 |
| R11 | Structural: new-command | 4 | 4.4 |
| R12 | Structural: security-analysis | 4 | 4.5 |
| R13 | Targeted Fix: test-project | 5 | 5.1 |
| R14 | Targeted Fix: assess-document | 5 | 5.2 |
| R15 | Targeted Fix: analyze-transcript | 5 | 5.3 |
| R16 | Targeted Fix: develop-image-prompt | 5 | 5.4 |
| R17 | Targeted Fix: review-intent | 6 | 6.1 |
| R18 | Targeted Fix: review-pr | 6 | 6.2 |
| R19 | Targeted Fix: remove-ip | 6 | 6.3 |
| R20 | Targeted Fix: ship | 6 | 6.4 |
| R21 | Targeted Fix: research-topic | 6 | 6.5 |
| R22 | Skill Batch: summarize-feedback, visual-explainer, validate-and-ship | 7 | 7.1 |
| R23 | Utility Batch: bump-version, clean-repo, new-skill, validate-plugin, ask-questions | 7 | 7.2 |
| R24 | Security Fix: unlock | 7 | 7.3 |
| S2 | Cross-Cutting: Error Handling Audit | 7 | 7.4 |
| S4 | Cross-Cutting: Proactive Triggers | 7 | 7.5 |
| S5 | Cross-Cutting: Flag Consistency | 7 | 7.5 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-02-28T22:00:00*
*Source: /plan-improvements command — Personal Plugin Command & Skill Quality Overhaul*
