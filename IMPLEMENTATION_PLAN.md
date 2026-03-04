# Implementation Plan

**Generated:** 2026-03-04 18:45:00
**Based On:** Comprehensive plugin marketplace evaluation report (39 commands/skills audited)
**Total Phases:** 6
**Estimated Total Effort:** ~1,400 LOC across ~40 files

---

## Executive Summary

This plan addresses all findings from the comprehensive evaluation of the claude-marketplace plugin repository. The evaluation audited all 26 commands and 13 skills across 2 plugins, identifying 5 blocking bugs (broken allowed-tools), 3 deprecation candidates, 5 quality/consistency issues, and 5 enhancement opportunities.

The implementation follows a risk-ordered approach: fix blocking bugs first (Phase 1), then clean up deprecated commands (Phase 2), improve quality and consistency (Phase 3), add enhancements (Phases 4-5), and finish with a comprehensive documentation audit and marketplace verification (Phase 6). Each phase leaves the repository in a working, marketplace-compatible state.

Key architectural decisions:
- Deprecated commands move to `plugins/personal-plugin/deprecated/` with README explaining why
- `check-updates` logic folds into `validate-plugin` as a `--check-updates` flag rather than being silently dropped
- Help skills become dynamic (Glob-based discovery) to eliminate the static table maintenance burden
- The shared IMPLEMENTATION_PLAN.md template extracts to `references/plan-template.md` to DRY up `create-plan` and `plan-improvements`

---

## Plan Overview

Phases are ordered by blast radius and dependency:
- **Phase 1** (S) fixes frontmatter-only bugs — zero risk, immediate value
- **Phase 2** (M) handles deprecations — requires help skill updates and marketplace.json cleanup
- **Phase 3** (M) improves quality — depends on Phase 2 (help skills rebuilt, command count changes)
- **Phase 4** (M) enhances commands — independent of Phase 3, but logically follows
- **Phase 5** (M) optimizes skills — independent of Phase 4
- **Phase 6** (M) final documentation audit — depends on all previous phases completing

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | Fix Blocking Tool Restriction Bugs | 9 frontmatter fixes across 9 files | S (~9 files, ~30 LOC) | None |
| 2 | Deprecations & Consolidation | 3 commands deprecated, check-updates logic folded into validate-plugin | M (~10 files, ~250 LOC) | None |
| 3 | Quality & Consistency Improvements | Template extraction, schema fixes, permission tightening, dynamic help | M (~12 files, ~400 LOC) | Phase 2 |
| 4 | Command Enhancements | MCP migration for review-pr, --json and --focus flags | M (~6 files, ~300 LOC) | None |
| 5 | Skill Optimization | Extract reference tables, replace hardcoded values | M (~8 files, ~250 LOC) | None |
| 6 | Documentation & Final Polish | Full doc audit, CHANGELOG, flag consistency, marketplace verification | M (~10 files, ~200 LOC) | Phases 1-5 |

<!-- BEGIN PHASES -->

---

## Phase 1: Fix Blocking Tool Restriction Bugs

**Estimated Complexity:** S (~9 files, ~30 LOC)
**Dependencies:** None
**Parallelizable:** Yes — all 6 work items are independent frontmatter edits

### Goals

- Fix 5 skills and 1 command with broken or contradictory `allowed-tools` declarations
- Add missing `allowed-tools` to all 3 bpmn-plugin skills
- Ensure every command and skill can execute its documented functionality

### Work Items

#### 1.1 Fix `/test-project` allowed-tools — add Read, Write, Edit, Glob, Grep
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P0 #1
**Files Affected:**
- `plugins/personal-plugin/commands/test-project.md` (modify)

**Description:**
The `/test-project` command generates test files and fixes source code (Phase 2.3 and Phase 4.2) but its `allowed-tools` only includes Bash variants and Task. Without `Read, Write, Edit, Glob, Grep`, the command cannot read files, write new tests, or edit source code — its core purpose is completely broken.

**Tasks:**
1. [ ] Edit the frontmatter `allowed-tools` line to add `Read, Write, Edit, Glob, Grep` before the existing Bash entries

**Current frontmatter:**
```yaml
allowed-tools: Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(npx:*), Bash(yarn:*), Bash(pnpm:*), Bash(pytest:*), Bash(python:*), Bash(go:*), Bash(cargo:*), Bash(dotnet:*), Bash(jest:*), Bash(vitest:*), Bash(bun:*), Task
```

**Target frontmatter:**
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(npx:*), Bash(yarn:*), Bash(pnpm:*), Bash(pytest:*), Bash(python:*), Bash(go:*), Bash(cargo:*), Bash(dotnet:*), Bash(jest:*), Bash(vitest:*), Bash(bun:*), Task
```

**Acceptance Criteria:**
- [ ] `allowed-tools` includes `Read, Write, Edit, Glob, Grep` in addition to existing entries
- [ ] No other frontmatter fields changed
- [ ] Command body unchanged

**Notes:**
Most critical bug — this command is completely non-functional without file access tools.

---

#### 1.2 Fix `summarize-feedback` skill allowed-tools — add Bash
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P0 #2
**Files Affected:**
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (modify)

**Description:**
The skill runs `python -m feedback_docx_generator` and `python -c "import docx"` for prerequisites checks, both requiring Bash access. Current `allowed-tools: Read, Glob, Grep, Write` lacks Bash entirely.

**Tasks:**
1. [ ] Add `Bash(python:*), Bash(pip:*)` to the `allowed-tools` line

**Current:** `allowed-tools: Read, Glob, Grep, Write`
**Target:** `allowed-tools: Read, Glob, Grep, Write, Bash(python:*), Bash(pip:*)`

**Acceptance Criteria:**
- [ ] `allowed-tools` includes `Bash(python:*), Bash(pip:*)`
- [ ] Bash access is scoped to python/pip only (not open Bash)

---

#### 1.3 Fix `security-analysis` skill allowed-tools — add Write
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P0 #3
**Files Affected:**
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify)

**Description:**
The skill writes a report to `reports/security-analysis-[timestamp].md` but `Write` is not in `allowed-tools`. The skill cannot produce its primary output.

**Tasks:**
1. [ ] Add `Write` to the `allowed-tools` line

**Current:** `allowed-tools: Read, Glob, Grep, Bash, WebSearch`
**Target:** `allowed-tools: Read, Write, Glob, Grep, Bash, WebSearch`

**Acceptance Criteria:**
- [ ] `allowed-tools` includes `Write`

---

#### 1.4 Fix `prime` skill allowed-tools — remove Write, add Bash(git:*)
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P0 #4
**Files Affected:**
- `plugins/personal-plugin/skills/prime/SKILL.md` (modify)

**Description:**
The skill declares itself "read-only" in its body but has `Write` in allowed-tools (contradiction). It also references git history analysis commands (`git log`, `git shortlog`) but lacks Bash access to execute them.

**Tasks:**
1. [ ] Replace `Write` with `Bash(git:*)` in the `allowed-tools` line

**Current:** `allowed-tools: Read, Glob, Grep, Write`
**Target:** `allowed-tools: Read, Glob, Grep, Bash(git:*)`

**Acceptance Criteria:**
- [ ] `Write` removed from allowed-tools
- [ ] `Bash(git:*)` added to allowed-tools
- [ ] Skill body "read-only" claim is now consistent with tool restrictions

---

#### 1.5 Fix `ship` skill allowed-tools — add Read, Edit for fix loop
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P0 #5
**Files Affected:**
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify)

**Description:**
The ship skill's auto-review + fix loop (Phases 6-7) needs to read files and apply code fixes, but `allowed-tools` only grants `Bash(git:*), Bash(gh:*), Bash(tea:*)`. Without `Read` and `Edit`, the fix loop cannot inspect or modify source code.

**Tasks:**
1. [ ] Add `Read, Edit, Glob, Grep` to the `allowed-tools` line

**Current:** `allowed-tools: Bash(git:*), Bash(gh:*), Bash(tea:*)`
**Target:** `allowed-tools: Read, Edit, Glob, Grep, Bash(git:*), Bash(gh:*), Bash(tea:*)`

**Acceptance Criteria:**
- [ ] `allowed-tools` includes `Read, Edit, Glob, Grep`
- [ ] Existing Bash restrictions preserved

---

#### 1.6 Add `allowed-tools` to all 3 bpmn-plugin skills
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P0 #6
**Files Affected:**
- `plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md` (modify)
- `plugins/bpmn-plugin/skills/bpmn-to-drawio/SKILL.md` (modify)
- `plugins/bpmn-plugin/skills/help/SKILL.md` (modify)

**Description:**
None of the 3 bpmn-plugin skills declare `allowed-tools`, making them unrestricted. Each should have appropriate restrictions based on what they actually do.

**Tasks:**
1. [ ] Add `allowed-tools: Read, Write, Glob, Grep` to `bpmn-generator/SKILL.md` frontmatter (reads input docs, writes BPMN XML)
2. [ ] Add `allowed-tools: Read, Write, Bash, Glob, Grep` to `bpmn-to-drawio/SKILL.md` frontmatter (reads BPMN XML, runs Python tool, writes .drawio)
3. [ ] Add `allowed-tools: Read, Glob, Grep` to `help/SKILL.md` frontmatter (read-only help display)

**For bpmn-generator, insert after the closing description block:**
```yaml
allowed-tools: Read, Write, Glob, Grep
```

**For bpmn-to-drawio, insert after the closing description block:**
```yaml
allowed-tools: Read, Write, Bash, Glob, Grep
```

**For help, add after the description line:**
```yaml
allowed-tools: Read, Glob, Grep
```

**Acceptance Criteria:**
- [ ] All 3 bpmn-plugin skills have `allowed-tools` in frontmatter
- [ ] bpmn-generator: `Read, Write, Glob, Grep`
- [ ] bpmn-to-drawio: `Read, Write, Bash, Glob, Grep`
- [ ] help: `Read, Glob, Grep`
- [ ] No changes to skill bodies

---

### Phase 1 Testing Requirements

- [ ] Run `/validate-plugin personal-plugin` — all frontmatter checks pass
- [ ] Run `/validate-plugin bpmn-plugin` — all frontmatter checks pass, allowed-tools present
- [ ] Spot-check: invoke `/test-project --help` or similar to confirm it loads without error

### Phase 1 Completion Checklist

- [ ] All 6 work items complete
- [ ] All 9 files modified with correct frontmatter
- [ ] `/validate-plugin --all` passes
- [ ] No regressions in other commands/skills

---

## Phase 2: Deprecations & Consolidation

**Estimated Complexity:** M (~10 files, ~250 LOC)
**Dependencies:** None (can run in parallel with Phase 1, but logically follows)
**Parallelizable:** Items 2.1-2.2 can run concurrently; 2.3 is independent

### Goals

- Remove 3 commands that overlap with built-in Claude Code features or have minimal use
- Preserve the unique `check-updates` logic (version drift detection) by folding it into `validate-plugin`
- Update all references (help skills, marketplace config, CLAUDE.md)

### Work Items

#### 2.1 Deprecate `convert-hooks` command
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P1 #7
**Files Affected:**
- `plugins/personal-plugin/commands/convert-hooks.md` (move)
- `plugins/personal-plugin/deprecated/README.md` (create)
- `plugins/personal-plugin/skills/help/SKILL.md` (modify — remove entry)

**Description:**
The `convert-hooks` command converts bash hook scripts to PowerShell. This was needed once during Windows setup but is rarely used. Claude Code may now handle cross-platform hooks natively, and users can ask Claude ad-hoc for this conversion.

**Tasks:**
1. [ ] Create directory `plugins/personal-plugin/deprecated/`
2. [ ] Move `plugins/personal-plugin/commands/convert-hooks.md` to `plugins/personal-plugin/deprecated/convert-hooks.md`
3. [ ] Create `plugins/personal-plugin/deprecated/README.md` with deprecation notices for all 3 deprecated commands (convert-hooks, setup-statusline, check-updates) including dates, reasons, and replacements
4. [ ] Remove the `/convert-hooks` entry from `plugins/personal-plugin/skills/help/SKILL.md`

**Acceptance Criteria:**
- [ ] `convert-hooks.md` no longer in `commands/` directory
- [ ] `deprecated/` directory exists with README and archived command
- [ ] Help skill no longer lists `/convert-hooks`

---

#### 2.2 Deprecate `setup-statusline` command
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P1 #8
**Files Affected:**
- `plugins/personal-plugin/commands/setup-statusline.md` (move)
- `plugins/personal-plugin/skills/help/SKILL.md` (modify — remove entry)

**Description:**
Claude Code now has a built-in `statusline-setup` agent type that configures status lines. This command is Windows/PowerShell-specific and duplicates built-in functionality.

**Tasks:**
1. [ ] Move `plugins/personal-plugin/commands/setup-statusline.md` to `plugins/personal-plugin/deprecated/setup-statusline.md`
2. [ ] Remove the `/setup-statusline` entry from `plugins/personal-plugin/skills/help/SKILL.md`

**Acceptance Criteria:**
- [ ] `setup-statusline.md` no longer in `commands/` directory
- [ ] Help skill no longer lists `/setup-statusline`

---

#### 2.3 Fold `check-updates` logic into `validate-plugin`, then deprecate
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P1 #9
**Files Affected:**
- `plugins/personal-plugin/commands/check-updates.md` (move)
- `plugins/personal-plugin/commands/validate-plugin.md` (modify — add --check-updates phase)
- `plugins/personal-plugin/skills/help/SKILL.md` (modify — remove check-updates, update validate-plugin entry)

**Description:**
The `check-updates` command's unique value is its three-way version comparison (remote marketplace.json vs local plugin.json vs local marketplace.json). This logic should be folded into `validate-plugin` as a new `--check-updates` flag, adding a Phase 9.5 (Version Update Check) between the existing Phase 9 (Summary) and the report output. The remote fetch via `gh api` and local consistency check logic transfers directly. After folding, deprecate the standalone command.

**Tasks:**
1. [ ] Read `check-updates.md` fully to extract the version comparison logic
2. [ ] Add a `--check-updates` flag to `validate-plugin.md`:
   - Document the flag in the Optional Arguments section
   - Add a new Phase 9.5: Version Update Check section after the existing Phase 9
   - Include: remote marketplace.json fetch via `gh api`, semver comparison, local consistency check (plugin.json vs marketplace.json version drift), and tabular report output
   - The phase should gracefully degrade if `gh` is unavailable (local consistency only)
   - Include `--verbose` support for per-plugin file path detail
3. [ ] Move `check-updates.md` to `plugins/personal-plugin/deprecated/check-updates.md`
4. [ ] Update help skill: remove `/check-updates` entry, add `--check-updates` flag to `/validate-plugin` description

**Acceptance Criteria:**
- [ ] `/validate-plugin --check-updates` produces same output as old `/check-updates`
- [ ] `/validate-plugin` without `--check-updates` is unchanged (no new network calls)
- [ ] `check-updates.md` no longer in `commands/` directory
- [ ] Help skill updated

**Notes:**
The `check-updates` logic is ~200 lines. When folding into validate-plugin, add it as a self-contained section that only executes when `--check-updates` is passed. Do not interleave it with existing validation phases.

---

#### 2.4 Update marketplace references and version
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P1 (cross-cutting)
**Files Affected:**
- `plugins/personal-plugin/.claude-plugin/plugin.json` (modify — bump version)
- `.claude-plugin/marketplace.json` (modify — bump personal-plugin version)
- `plugins/bpmn-plugin/.claude-plugin/plugin.json` (modify — bump version)
- `.claude-plugin/marketplace.json` (modify — bump bpmn-plugin version)
- `CLAUDE.md` (modify — update command count, remove deprecated command references)

**Description:**
After deprecations, update version numbers and documentation to reflect the new command count (23 commands instead of 26) and bpmn-plugin changes (added allowed-tools).

**Tasks:**
1. [ ] Bump `personal-plugin` version from 4.1.0 to 5.0.0 in both `plugin.json` and `marketplace.json` (major bump: 3 commands deprecated/removed is a breaking change)
2. [ ] Bump `bpmn-plugin` version from 2.2.0 to 2.3.0 in both `plugin.json` and `marketplace.json` (minor bump: added allowed-tools, no breaking changes)
3. [ ] Update CLAUDE.md: remove `convert-hooks.md`, `setup-statusline.md`, `check-updates.md` from the command listing; add `deprecated/` directory to the structure diagram; update command count from 26 to 23
4. [ ] Add `--check-updates` to the validate-plugin entry in CLAUDE.md

**Acceptance Criteria:**
- [ ] personal-plugin version: 5.0.0 in both files
- [ ] bpmn-plugin version: 2.3.0 in both files
- [ ] CLAUDE.md accurately reflects current command inventory
- [ ] No references to deprecated commands in active documentation

---

### Phase 2 Testing Requirements

- [ ] Run `/validate-plugin --all` — passes with no errors about missing commands
- [ ] Verify `deprecated/` directory has all 3 archived commands plus README
- [ ] Verify help skill shows 23 commands (not 26)
- [ ] Confirm CLAUDE.md command listing matches actual `commands/` directory

### Phase 2 Completion Checklist

- [ ] All 4 work items complete
- [ ] 3 commands archived to `deprecated/`
- [ ] validate-plugin has `--check-updates` functionality
- [ ] Version numbers bumped
- [ ] CLAUDE.md updated
- [ ] Help skill updated

---

## Phase 3: Quality & Consistency Improvements

**Estimated Complexity:** M (~12 files, ~400 LOC)
**Dependencies:** Phase 2 (help skills are updated there; command count changes affect this phase)
**Parallelizable:** Items 3.1-3.4 can run concurrently; 3.5 depends on Phase 2 completion

### Goals

- Eliminate template duplication between `create-plan` and `plan-improvements`
- Fix schema field naming inconsistencies across commands
- Tighten tool restrictions on commands with unnecessarily broad Bash access
- Make help skills dynamic to eliminate static table maintenance

### Work Items

#### 3.1 Extract shared IMPLEMENTATION_PLAN.md template to `references/plan-template.md`
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P2 #10
**Files Affected:**
- `plugins/personal-plugin/references/plan-template.md` (create)
- `plugins/personal-plugin/commands/create-plan.md` (modify)
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
Both `create-plan` and `plan-improvements` contain near-identical IMPLEMENTATION_PLAN.md output templates (~200 lines each). Extract the shared template into `references/plan-template.md` and have both commands reference it. This prevents drift when one command's template is updated but not the other's.

**Tasks:**
1. [ ] Read the Phase 4 template section from `create-plan.md` (the markdown template starting from "Create the implementation plan with this structure:")
2. [ ] Read the equivalent template section from `plan-improvements.md`
3. [ ] Diff the two templates to identify any intentional differences
4. [ ] Create `plugins/personal-plugin/references/plan-template.md` containing the unified template with a header explaining its purpose
5. [ ] In `create-plan.md`, replace the inline template with a reference: "Read the plan template from `references/plan-template.md` (relative to this command's plugin directory) and use it as the output structure."
6. [ ] In `plan-improvements.md`, replace the inline template with the same reference
7. [ ] Preserve any command-specific additions (e.g., append/overwrite logic stays in create-plan, not in the shared template)

**Acceptance Criteria:**
- [ ] `references/plan-template.md` exists with the unified template
- [ ] Both commands reference the shared template instead of inlining it
- [ ] Command-specific logic (append behavior, etc.) remains in the individual commands
- [ ] The generated IMPLEMENTATION_PLAN.md output is unchanged

**Notes:**
The append/overwrite logic with `<!-- BEGIN PHASES -->` / `<!-- END PHASES -->` markers is specific to `create-plan` and should stay there. The shared template is the markdown structure itself.

---

#### 3.2 Fix schema inconsistencies across commands
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P2 #11
**Files Affected:**
- `plugins/personal-plugin/commands/define-questions.md` (modify)
- `plugins/personal-plugin/commands/finish-document.md` (modify)
- `plugins/personal-plugin/commands/review-pr.md` (modify)

**Description:**
Two distinct inconsistencies need fixing:

**Issue A — `generated_date` vs `generated_at`:**
In `define-questions.md`: the schema template (line ~80) and example output (line ~180) use `generated_date`, but the validation rules section (line ~210) and validation error examples (line ~243) use `generated_at`. Same pattern in `finish-document.md` (schema uses `generated_date`, validation uses `generated_at`). Standardize to `generated_date` everywhere (it's the more common usage and appears in the authoritative schema section).

**Issue B — Severity labels in `review-pr`:**
The report template uses CRITICAL/WARNING/SUGGESTION but the severity definitions section uses CRITICAL/HIGH/MEDIUM/LOW/INFO. Standardize to CRITICAL/HIGH/MEDIUM/LOW/INFO (the 5-level scale) everywhere, and map the report display to use these same labels.

**Tasks:**
1. [ ] In `define-questions.md`: replace all occurrences of `generated_at` with `generated_date` in the validation rules section and validation error examples
2. [ ] In `finish-document.md`: replace all occurrences of `generated_at` with `generated_date` in the validation error examples
3. [ ] In `review-pr.md`: replace CRITICAL/WARNING/SUGGESTION labels in the report template with CRITICAL/HIGH/MEDIUM/LOW/INFO to match the severity definitions; update the issue count format and Analysis Summary table accordingly

**Acceptance Criteria:**
- [ ] `define-questions.md` uses `generated_date` consistently (zero occurrences of `generated_at`)
- [ ] `finish-document.md` uses `generated_date` consistently (zero occurrences of `generated_at`)
- [ ] `review-pr.md` uses CRITICAL/HIGH/MEDIUM/LOW/INFO consistently in both definitions and report template

---

#### 3.3 Tighten and loosen tool permissions on 4 commands
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P2 #12, #13
**Files Affected:**
- `plugins/personal-plugin/commands/new-command.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/commands/review-intent.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
Two related fixes — tighten permissions where too loose, loosen where too tight:

**Tighten:** `new-command` and `new-skill` include open `Bash` access but only need to create files. Remove `Bash`.

**Loosen:** `review-intent` has a `--deep` flag that analyzes git history but lacks `Bash(git:*)`. `create-plan` references `find` commands in codebase reconnaissance but lacks Bash. Add scoped Bash access to both.

**Tasks:**
1. [ ] `new-command.md`: Change `allowed-tools: Read, Write, Edit, Glob, Grep, Bash` to `allowed-tools: Read, Write, Edit, Glob, Grep`
2. [ ] `new-skill.md`: Change `allowed-tools: Read, Write, Edit, Glob, Grep, Bash` to `allowed-tools: Read, Write, Edit, Glob, Grep`
3. [ ] `review-intent.md`: Change `allowed-tools: Read, Glob, Grep, Write` to `allowed-tools: Read, Glob, Grep, Write, Bash(git:*)`
4. [ ] `create-plan.md`: Change `allowed-tools: Read, Glob, Grep, Write, Edit, Agent` to `allowed-tools: Read, Glob, Grep, Write, Edit, Agent, Bash(git:*)`

**Acceptance Criteria:**
- [ ] `new-command.md` and `new-skill.md` have no `Bash` in allowed-tools
- [ ] `review-intent.md` and `create-plan.md` have `Bash(git:*)` in allowed-tools

---

#### 3.4 Fix `plan-improvements` audit instructions
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P2 (discovered during review)
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**
The `plan-improvements` command references running `npm audit`, `pip-audit`, and `cargo audit` in its security analysis dimension but only has `Read, Glob, Grep, Write, Edit, Agent` in allowed-tools. Revise the instructions to scope security checks to static analysis (reading manifest files), since the command's primary purpose is improvement planning, not security scanning.

**Tasks:**
1. [ ] In the security analysis dimension section, change instructions from "Run npm audit, pip-audit, cargo audit" to "Check manifest files (package.json, requirements.txt, Cargo.toml) for known problematic patterns and outdated dependencies. For comprehensive security scanning, recommend `/security-analysis`."
2. [ ] No change to allowed-tools

**Acceptance Criteria:**
- [ ] Security analysis dimension references static manifest analysis, not CLI audit tools
- [ ] Cross-reference to `/security-analysis` added

---

#### 3.5 Make help skills dynamic
**Status: COMPLETE 2026-03-04**
**Requirement Refs:** Evaluation Report P2 #14
**Files Affected:**
- `plugins/personal-plugin/skills/help/SKILL.md` (modify — major rewrite of Mode 1)
- `plugins/bpmn-plugin/skills/help/SKILL.md` (modify — major rewrite of Mode 1)

**Description:**
Both help skills maintain static hardcoded tables that go stale whenever commands/skills are added, removed, or modified. Replace the static tables with dynamic discovery using Glob to read the `commands/` and `skills/` directories at runtime, then read each file's frontmatter to build the table dynamically.

**Tasks:**
1. [ ] Rewrite Mode 1 of `personal-plugin/skills/help/SKILL.md`:
   - Replace the static table with instructions to:
     a. Use Glob to list all `*.md` files in the plugin's `commands/` directory
     b. Use Glob to list all `*/SKILL.md` files in the plugin's `skills/` directory
     c. Read the first 5 lines of each file to extract the `description` from frontmatter
     d. Build and display the table dynamically, grouping commands by category using keyword matching on descriptions (Planning, Document, Review, Utility, etc.)
   - Remove the hardcoded "26 commands, 10 skills" count — compute dynamically
   - Keep Mode 2 (detailed help) which already reads individual files
   - Remove the "IMPORTANT: This skill must be updated whenever commands or skills are added" warning
2. [ ] Rewrite Mode 1 of `bpmn-plugin/skills/help/SKILL.md` with the same dynamic pattern:
   - Glob `skills/*/SKILL.md` to discover skills
   - Read frontmatter for descriptions
   - Build table dynamically
   - Remove "IMPORTANT" update warning

**Acceptance Criteria:**
- [ ] Help skills discover commands/skills at runtime via Glob
- [ ] No static counts or hardcoded tables remain in Mode 1
- [ ] Adding a new command/skill automatically appears in `/help` output
- [ ] Mode 2 (detailed help) still works correctly
- [ ] Output format is visually comparable to current static tables

**Notes:**
The category grouping in personal-plugin help (Planning & Analysis, Document Processing, etc.) is valuable. Implement keyword-based categorization: if description contains "plan", "review", "arch" -> Planning & Analysis; "document", "transcript", "question" -> Document Processing; etc. Include a fallback "Other" category.

---

### Phase 3 Testing Requirements

- [ ] Run `/validate-plugin --all` — passes with updated frontmatter
- [ ] Run `/personal-plugin:help` — dynamically discovers all 23 commands and 10 skills
- [ ] Run `/bpmn-plugin:help` — dynamically discovers all 3 skills
- [ ] Verify `references/plan-template.md` exists and is well-formed
- [ ] Grep for `generated_at` in define-questions.md and finish-document.md — zero matches
- [ ] Grep for `WARNING` or `SUGGESTION` severity labels in review-pr.md report template — zero matches

### Phase 3 Completion Checklist

- [ ] All 5 work items complete
- [ ] Shared template extracted
- [ ] Schema inconsistencies resolved
- [ ] Tool permissions tightened/loosened as specified
- [ ] Help skills are dynamic
- [ ] No regressions

---

## Phase 4: Command Enhancements

**Estimated Complexity:** M (~6 files, ~300 LOC)
**Dependencies:** None (independent of Phases 1-3)
**Parallelizable:** Items 4.1-4.3 can run concurrently

### Goals

- Enhance `/review-pr` with MCP GitHub integration for richer reviews
- Add `--json` output to key commands for CI/CD integration
- Add `--focus` flags for targeted analysis

### Work Items

#### 4.1 Migrate `/review-pr` to use MCP GitHub tools
**Status: PENDING**
**Requirement Refs:** Evaluation Report P3 #15
**Files Affected:**
- `plugins/personal-plugin/commands/review-pr.md` (modify)

**Description:**
The current `/review-pr` command uses only `gh` CLI for PR interaction. The environment has MCP GitHub tools (`pull_request_read`, `add_comment_to_pending_review`, `pull_request_review_write`) that enable richer integration — specifically line-level review comments instead of a single review body.

Migrate the command to use MCP tools as the primary interface, with `gh` CLI as fallback.

**Tasks:**
1. [ ] Update the allowed-tools to note MCP tool usage (MCP tools don't require allowed-tools declaration but should be documented)
2. [ ] Rewrite Phase 1 (Fetch PR Data) to use `pull_request_read` with method `get` and `get_diff` instead of `gh pr view` and `gh pr diff`
3. [ ] Rewrite Phase 2 file listing to use `pull_request_read` with method `get_files`
4. [ ] Rewrite Phase 4 (Post Review) to use MCP tools:
   - Create a pending review (`pull_request_review_write` method `create`, no event)
   - Add line-level comments for each finding (`add_comment_to_pending_review` with `line`, `path`, `side: RIGHT`)
   - Submit the review (`pull_request_review_write` method `submit_pending` with event: APPROVE/REQUEST_CHANGES/COMMENT)
5. [ ] Keep `gh` CLI as fallback for environments without MCP tools
6. [ ] Update the "Post to GitHub" flow to explain line-level comments as the default

**Acceptance Criteria:**
- [ ] Command uses MCP tools for PR data fetching when available
- [ ] Line-level comments posted for specific findings
- [ ] Fallback to `gh` CLI works if MCP tools unavailable
- [ ] Severity labels use the unified CRITICAL/HIGH/MEDIUM/LOW/INFO scale

---

#### 4.2 Add `--json` output flag to `consolidate-documents`, `clean-repo`, and `review-arch`
**Status: PENDING**
**Requirement Refs:** Evaluation Report P3 #16
**Files Affected:**
- `plugins/personal-plugin/commands/consolidate-documents.md` (modify)
- `plugins/personal-plugin/commands/clean-repo.md` (modify)
- `plugins/personal-plugin/commands/review-arch.md` (modify)

**Description:**
Add a `--json` flag to 3 commands that currently only output markdown/text. This enables CI/CD pipeline integration and programmatic consumption of results.

**Tasks:**
1. [ ] For each command, add `--json` to the Optional Arguments section with description
2. [ ] For each command, define a JSON output schema:
   - `consolidate-documents`: `{sources: [], consolidation_decisions: [], output_file: string, stats: {sections_merged, conflicts_resolved, content_dropped}}`
   - `clean-repo`: `{phases: [{name, actions: [{type, path, status}]}], summary: {files_deleted, files_moved, docs_updated}}`
   - `review-arch`: `{scorecard: {dimension: score}, findings: [{id, severity, category, description, recommendation}], remediation: [{id, effort, impact, description}]}`
3. [ ] Add instructions: "When `--json` is specified, output ONLY the JSON to stdout. Write to file if `--output` is also specified."

**Acceptance Criteria:**
- [ ] Each command accepts `--json` flag
- [ ] JSON output is valid, parseable JSON
- [ ] JSON captures same information as text output
- [ ] Default behavior (no flag) unchanged

---

#### 4.3 Add `--focus` flags to `assess-document` and `review-arch`
**Status: PENDING**
**Requirement Refs:** Evaluation Report P3 #18
**Files Affected:**
- `plugins/personal-plugin/commands/assess-document.md` (modify)
- `plugins/personal-plugin/commands/review-arch.md` (modify)

**Description:**
Add a `--focus` flag that limits analysis to specific dimensions, saving time and context when users only care about particular aspects.

**Tasks:**
1. [ ] `assess-document`: Add `--focus <dimensions>` flag accepting comma-separated names from: `completeness, clarity, consistency, specificity, structure, feasibility`. Only score and report focused dimensions. Overall score = average of focused dimensions.
2. [ ] `review-arch`: Add `--focus <dimensions>` flag accepting comma-separated names from: `code-quality, architecture, security, performance, testing, dependencies`. Only analyze focused dimensions.
3. [ ] Both: document flag, add examples, add output note: "Focused analysis — only [dimensions] evaluated."

**Acceptance Criteria:**
- [ ] Both commands accept `--focus` with comma-separated dimension names
- [ ] Output only includes focused dimensions
- [ ] Invalid dimension names produce helpful error with valid options listed
- [ ] Default behavior unchanged

---

### Phase 4 Testing Requirements

- [ ] Test `/review-pr` on a real PR with MCP tools — line-level comments appear
- [ ] Test `--json` output on each command — valid JSON produced
- [ ] Test `--focus` on each command — only specified dimensions in output
- [ ] Verify default behavior unchanged on all modified commands

### Phase 4 Completion Checklist

- [ ] All 3 work items complete
- [ ] MCP integration working for review-pr
- [ ] JSON output validated on 3 commands
- [ ] Focus flags working on 2 commands
- [ ] No regressions

---

## Phase 5: Skill Optimization

**Estimated Complexity:** M (~8 files, ~250 LOC)
**Dependencies:** None (independent of Phases 1-4)
**Parallelizable:** Items 5.1 and 5.2 can run concurrently

### Goals

- Reduce skill prompt length by extracting reference tables to files
- Replace hardcoded model names with dynamic detection or configuration

### Work Items

#### 5.1 Extract long reference tables from skills >500 lines
**Status: PENDING**
**Requirement Refs:** Evaluation Report P3 #17
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify)
- `plugins/personal-plugin/references/research-models.md` (create)
- `plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md` (modify)
- `plugins/bpmn-plugin/references/bpmn-elements.md` (create)
- `plugins/personal-plugin/commands/validate-plugin.md` (modify)
- `plugins/personal-plugin/references/validation-maturity-scorecard.md` (create)

**Description:**
Three items exceed 500 lines and contain large reference tables that don't need to be in the main prompt. Extract these to reference files that are loaded on demand, reducing the base prompt size and improving instruction adherence.

**Tasks:**
1. [ ] `research-topic` skill (~698 lines): Extract model configuration tables (model names, parameters, API endpoints), cost estimation tables, and provider-specific instructions into `references/research-models.md`. Keep workflow phases and core logic in SKILL.md. Add pointer: "Read `references/research-models.md` for model configuration and provider-specific parameters."
2. [ ] `bpmn-generator` skill (~620 lines): Extract BPMN element mapping tables (task types, gateway types, event types, DI dimension constants, ID pattern tables) into `references/bpmn-elements.md`. Keep workflow phases, interactive Q&A framework, and generation rules in SKILL.md. Add pointer: "Read `references/bpmn-elements.md` for element type mappings and DI constants."
3. [ ] `validate-plugin` command (~1160 lines): Extract maturity scorecard section (Level 1-4 criteria, weighted scoring formula, example scorecards) into `references/validation-maturity-scorecard.md`. Load only when `--scorecard` is passed. Add: "When `--scorecard` is requested, read `references/validation-maturity-scorecard.md` for the scoring framework."

**Acceptance Criteria:**
- [ ] `research-topic` SKILL.md reduced to <500 lines
- [ ] `bpmn-generator` SKILL.md reduced to <500 lines
- [ ] `validate-plugin` base prompt reduced (scorecard loaded on demand)
- [ ] All reference files created with clear table of contents
- [ ] Functionality unchanged

**Notes:**
Use the pattern: "For [specific data], read `references/[file].md` relative to this plugin's directory." Claude Code resolves plugin-relative paths via `CLAUDE_PLUGIN_ROOT`.

---

#### 5.2 Replace hardcoded model names with dynamic detection
**Status: PENDING**
**Requirement Refs:** Evaluation Report P3 #19
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)

**Description:**
Three skills contain hardcoded values that will go stale:
- `research-topic`: Model names like `claude-opus-4-5-20251101`, `o3-deep-research-2025-06-26`
- `visual-explainer`: `gemini-3-pro-image-preview`
- `unlock`: Bitwarden project ID `5022ea9c-e711-4f4e-bf5f-b3df0181a41d`

Replace with environment variable overrides and date-annotated defaults.

**Tasks:**
1. [ ] `research-topic`: Replace hardcoded model strings with instructions to check environment variables first (`ANTHROPIC_MODEL`, `OPENAI_MODEL`, `GOOGLE_MODEL`), fall back to the skill's existing model check feature, use hardcoded names only as last-resort defaults marked "default as of 2026-03-04, may be outdated"
2. [ ] `visual-explainer`: Replace `gemini-3-pro-image-preview` with check for `GOOGLE_IMAGE_MODEL` env var, fall back to current value with date annotation
3. [ ] `unlock`: Replace hardcoded Bitwarden project ID with check for `BWS_PROJECT_ID` env var, fall back to current ID with comment: "Default project ID for Troy's vault — override via BWS_PROJECT_ID"
4. [ ] Add comment pattern to all hardcoded defaults: `# Default as of 2026-03-04 — verify with provider if errors occur`

**Acceptance Criteria:**
- [ ] No hardcoded model names without env var override and date annotation
- [ ] Bitwarden project ID configurable via `BWS_PROJECT_ID`
- [ ] Existing functionality works with current defaults
- [ ] New env var overrides work when set

---

### Phase 5 Testing Requirements

- [ ] Verify extracted reference files are well-formed and complete
- [ ] Run `/research-topic` — confirm it reads from reference file correctly
- [ ] Run `/bpmn-generator` — confirm element mappings load from reference
- [ ] Run `/validate-plugin --scorecard` — confirm scorecard loads from reference
- [ ] Test env var override: set `BWS_PROJECT_ID` to a test value, verify `unlock` uses it

### Phase 5 Completion Checklist

- [ ] All 2 work items complete
- [ ] 3 reference files created
- [ ] 3 skills updated with dynamic model detection
- [ ] Skill line counts reduced below 500
- [ ] No regressions

---

## Phase 6: Documentation & Final Polish

**Estimated Complexity:** M (~10 files, ~200 LOC)
**Dependencies:** Phases 1-5 (this is the final verification pass after all changes land)
**Parallelizable:** Items 6.1-6.3 can run concurrently; 6.4-6.5 are sequential finalization

### Goals

- Ensure all documentation accurately reflects the post-implementation state of the repository
- Produce CHANGELOG entries for both plugin version bumps
- Update flag consistency reference with all new flags
- Run final validation and clean-repo audit to catch anything missed
- Verify marketplace install flow works end-to-end

### Work Items

#### 6.1 Full CLAUDE.md audit
**Status: PENDING**
**Requirement Refs:** Documentation completeness (cross-cutting)
**Files Affected:**
- `CLAUDE.md` (modify)

**Description:**
CLAUDE.md is the authoritative reference for this repository. After all 5 phases of changes, it needs a comprehensive audit to ensure every section accurately reflects reality. This goes beyond the targeted updates in 2.4 — it's a full reconciliation pass.

**Tasks:**
1. [ ] **Repository Structure diagram:** Verify every directory and file listed actually exists. Add `deprecated/` directory. Remove any files that were moved or deleted. Verify `references/` section lists the new files (`plan-template.md`, `research-models.md`, `validation-maturity-scorecard.md`). Verify bpmn-plugin `references/` lists `bpmn-elements.md`.
2. [ ] **Commands listing:** Verify the command list matches the actual contents of `plugins/personal-plugin/commands/`. Confirm exactly 23 commands (26 minus 3 deprecated). Verify each command's description matches its current frontmatter. Update any description text that changed during implementation.
3. [ ] **Skills listing:** Verify all 10 personal-plugin skills and 3 bpmn-plugin skills are listed with accurate descriptions.
4. [ ] **Command Conventions section:** Verify the pattern descriptions still match. Add any new patterns introduced (e.g., MCP tool usage pattern for review-pr). Update the "Patterns Used" list if any patterns changed.
5. [ ] **Command vs Skills section:** No changes expected, but verify the directory structure examples are still accurate.
6. [ ] **Bundled Python Tools section:** Verify tool paths and descriptions are accurate.
7. [ ] **Versioning Strategy section:** Verify it reflects the current version numbers (personal-plugin 5.0.0, bpmn-plugin 2.3.0).
8. [ ] **Help Skill Maintenance section:** Update to reflect that help skills are now dynamic and no longer need manual updates when commands/skills change. Remove or revise the "When modifying a plugin" checklist items about updating help skills.

**Acceptance Criteria:**
- [ ] Every file path in CLAUDE.md exists on disk
- [ ] Every command/skill listed in CLAUDE.md has a corresponding file
- [ ] No references to deprecated commands (`convert-hooks`, `setup-statusline`, `check-updates`) appear in active sections
- [ ] Version numbers match `plugin.json` and `marketplace.json`
- [ ] Structure diagram matches `find . -type d` output

---

#### 6.2 README.md and supporting docs update
**Status: PENDING**
**Requirement Refs:** Documentation completeness (cross-cutting)
**Files Affected:**
- `README.md` (modify)
- `CONTRIBUTING.md` (modify if it references commands/skills)
- `QUICK-REFERENCE.md` (modify if it exists and references commands)

**Description:**
Update all user-facing documentation beyond CLAUDE.md to reflect the changes. README.md is what GitHub visitors see first and must be accurate.

**Tasks:**
1. [ ] **README.md:** Update command/skill counts, remove any references to deprecated commands, verify installation instructions still work, update version badges or references if present, ensure feature list matches current capabilities
2. [ ] **CONTRIBUTING.md:** If it references adding commands or skills, verify the instructions match the current structure (especially the dynamic help skill — contributors no longer need to manually update help)
3. [ ] **QUICK-REFERENCE.md:** If it lists commands, update to match current 23-command set. Add new flags (`--json`, `--focus`, `--check-updates`) to relevant command entries
4. [ ] **SECURITY.md:** No changes expected unless the security-analysis skill changes affected security documentation
5. [ ] **WORKFLOWS.md:** Verify any documented workflows still reference valid commands

**Acceptance Criteria:**
- [ ] README.md accurately represents current plugin capabilities
- [ ] No references to deprecated commands in any docs
- [ ] New features (MCP integration, --json, --focus, --check-updates) mentioned where relevant

---

#### 6.3 CHANGELOG.md entries and flag consistency update
**Status: PENDING**
**Requirement Refs:** Documentation completeness (cross-cutting)
**Files Affected:**
- `CHANGELOG.md` (modify)
- `plugins/personal-plugin/references/flag-consistency.md` (modify)

**Description:**
Add structured CHANGELOG entries for both plugin version bumps and update the flag consistency reference with all new flags introduced across the plan.

**Tasks:**
1. [ ] **CHANGELOG.md** — Add entry for personal-plugin v5.0.0:
   ```markdown
   ## [personal-plugin v5.0.0] - 2026-03-XX

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
   ```
2. [ ] **CHANGELOG.md** — Add entry for bpmn-plugin v2.3.0:
   ```markdown
   ## [bpmn-plugin v2.3.0] - 2026-03-XX

   ### Added
   - `allowed-tools` declarations on all 3 skills (bpmn-generator, bpmn-to-drawio, help)

   ### Changed
   - Extracted BPMN element mapping tables to `references/bpmn-elements.md`
   - `bpmn-generator` SKILL.md reduced from ~620 to <500 lines
   ```
3. [ ] **flag-consistency.md** — Add new flags to the reference:
   - `--check-updates` on `/validate-plugin` — check for remote plugin updates and local version drift
   - `--json` on `/consolidate-documents`, `/clean-repo`, `/review-arch` — machine-readable JSON output
   - `--focus <dimensions>` on `/assess-document`, `/review-arch` — limit analysis to specific dimensions
   - Document the valid dimension values for each `--focus` flag
   - Verify all existing flag entries are still accurate

**Acceptance Criteria:**
- [ ] CHANGELOG.md has complete entries for both version bumps
- [ ] All breaking changes, additions, fixes, and changes documented
- [ ] flag-consistency.md lists every flag across all 23 commands with accurate descriptions
- [ ] No flag is documented that doesn't exist, and no existing flag is missing

---

#### 6.4 Final validation pass
**Status: PENDING**
**Requirement Refs:** Quality gate (cross-cutting)
**Files Affected:**
- None (read-only validation)

**Description:**
Run comprehensive validation to catch anything missed across all 5 implementation phases.

**Tasks:**
1. [ ] Run `/validate-plugin personal-plugin` — expect zero errors, zero warnings
2. [ ] Run `/validate-plugin bpmn-plugin` — expect zero errors, zero warnings
3. [ ] Run `/validate-plugin --all` — cross-plugin namespace collision check passes
4. [ ] Run `/validate-plugin --check-updates` — verify the newly folded logic works (should show "up to date" for local consistency)
5. [ ] Run `/clean-repo --audit` — verify no stale artifacts, broken references, or orphaned files
6. [ ] Spot-check dynamic help: invoke `/personal-plugin:help` and verify it discovers all 23 commands and 10 skills with correct descriptions
7. [ ] Spot-check dynamic help: invoke `/bpmn-plugin:help` and verify it discovers all 3 skills
8. [ ] Verify no `generated_at` occurrences remain: grep across all command files
9. [ ] Verify no deprecated commands are referenced in active files: grep for `convert-hooks`, `setup-statusline`, `check-updates` in files outside `deprecated/`
10. [ ] Verify version consistency: personal-plugin 5.0.0 in plugin.json, marketplace.json, CLAUDE.md, and CHANGELOG.md. Same for bpmn-plugin 2.3.0.

**Acceptance Criteria:**
- [ ] Zero validation errors across both plugins
- [ ] Zero stale references to deprecated commands
- [ ] Zero schema inconsistencies
- [ ] Version numbers consistent across all 4 touchpoints per plugin
- [ ] Dynamic help produces correct, complete output

**Notes:**
If any issues are found during this pass, fix them immediately rather than creating new work items. This is the cleanup sweep.

---

#### 6.5 Marketplace compatibility verification
**Status: PENDING**
**Requirement Refs:** Marketplace compatibility (CLAUDE.md requirement)
**Files Affected:**
- None (read-only testing)

**Description:**
The CLAUDE.md mandates that all changes maintain marketplace compatibility. Verify the full install flow works after all changes.

**Tasks:**
1. [ ] Verify `.claude-plugin/marketplace.json` is valid JSON with correct structure
2. [ ] Verify both plugin entries have correct `source` paths, `version` numbers, and `description` text
3. [ ] Verify `plugins/personal-plugin/.claude-plugin/plugin.json` matches marketplace entry
4. [ ] Verify `plugins/bpmn-plugin/.claude-plugin/plugin.json` matches marketplace entry
5. [ ] Verify the `deprecated/` directory does NOT interfere with plugin discovery (commands in `deprecated/` should NOT appear as active commands)
6. [ ] If possible, test the full install flow in a fresh Claude Code session:
   ```
   /plugin marketplace add davistroy/claude-marketplace
   /plugin install personal-plugin@troys-plugins
   /help
   ```
   Verify `/help` shows the plugin's commands and the dynamic help skill works.

**Acceptance Criteria:**
- [ ] marketplace.json valid and accurate
- [ ] Both plugin.json files match marketplace entries
- [ ] Deprecated commands do not appear in active plugin command list
- [ ] Fresh install flow works (if testable)

---

### Phase 6 Testing Requirements

- [ ] All validation commands pass with zero errors
- [ ] CHANGELOG entries are complete and correctly formatted
- [ ] flag-consistency.md covers all flags across all 23 commands
- [ ] No stale references found by grep across the repository
- [ ] Version numbers are consistent across all files
- [ ] Marketplace install flow verified

### Phase 6 Completion Checklist

- [ ] All 5 work items complete
- [ ] CLAUDE.md fully audited and accurate
- [ ] README.md and supporting docs updated
- [ ] CHANGELOG.md entries written for both plugins
- [ ] flag-consistency.md updated with new flags
- [ ] Final validation pass clean
- [ ] Marketplace compatibility verified
- [ ] Repository is ready for commit and release

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| 1.1 | 1.2, 1.3, 1.4, 1.5, 1.6 | All Phase 1 items are independent frontmatter edits |
| 2.1 | 2.2 | Both are simple move+delete operations |
| 2.3 | — | Must be done carefully (logic folding into validate-plugin) |
| 3.1 | 3.2, 3.3, 3.4 | Template extraction is independent of schema/permission fixes |
| 3.2 | 3.1, 3.3, 3.4 | Schema fixes are independent |
| 3.3 | 3.1, 3.2, 3.4 | Permission fixes are independent |
| 4.1 | 4.2, 4.3 | MCP migration is independent of JSON/focus flags |
| 4.2 | 4.1, 4.3 | JSON output is independent |
| 5.1 | 5.2 | Reference extraction is independent of model name changes |
| Phase 4 | Phase 5 | Entire phases are independent of each other |
| 6.1 | 6.2, 6.3 | CLAUDE.md audit, README update, and CHANGELOG are independent |
| 6.4 | — | Must run after 6.1-6.3 complete (validates their output) |
| 6.5 | — | Final step, depends on everything passing |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Dynamic help skills produce inconsistent output | Medium | Medium | Include fallback static table; test thoroughly with current command set |
| Extracted reference files not found at runtime | Low | High | Use `CLAUDE_PLUGIN_ROOT` for path resolution; test in fresh install |
| MCP GitHub tools not available in all environments | Medium | Low | Keep `gh` CLI fallback in review-pr; detect MCP availability at runtime |
| Deprecating commands breaks user workflows | Low | Medium | Archive to `deprecated/` (not deleted); document migration path in README |
| Version bump to 5.0.0 causes marketplace compatibility | Low | High | Test with `/plugin marketplace add` after bump; verify install flow |
| Documentation drift after implementation | Medium | Medium | Phase 6 dedicated audit catches inconsistencies before release |

---

## Success Metrics

- [ ] All 6 phases completed
- [ ] `/validate-plugin --all` passes with zero errors
- [ ] All 5 blocking bugs fixed (Phase 1)
- [ ] 3 commands deprecated with clear migration paths (Phase 2)
- [ ] Zero schema inconsistencies across all commands (Phase 3)
- [ ] Help skills dynamically discover all commands/skills (Phase 3)
- [ ] `/review-pr` posts line-level GitHub comments (Phase 4)
- [ ] 3 commands support `--json` output (Phase 4)
- [ ] All skills under 500 lines (Phase 5)
- [ ] Zero hardcoded model names without env var override (Phase 5)
- [ ] All documentation (CLAUDE.md, README.md, CHANGELOG.md) accurate and complete (Phase 6)
- [ ] flag-consistency.md covers all flags across all commands (Phase 6)
- [ ] Marketplace install flow verified end-to-end (Phase 6)
- [ ] Zero stale references to deprecated commands anywhere in active files (Phase 6)

---

## Appendix: Requirement Traceability

| Requirement | Source | Phase | Work Item |
|-------------|--------|-------|-----------|
| Fix test-project allowed-tools | Eval Report P0 #1 | 1 | 1.1 |
| Fix summarize-feedback allowed-tools | Eval Report P0 #2 | 1 | 1.2 |
| Fix security-analysis allowed-tools | Eval Report P0 #3 | 1 | 1.3 |
| Fix prime skill allowed-tools | Eval Report P0 #4 | 1 | 1.4 |
| Fix ship skill allowed-tools | Eval Report P0 #5 | 1 | 1.5 |
| Add allowed-tools to bpmn-plugin skills | Eval Report P0 #6 | 1 | 1.6 |
| Deprecate convert-hooks | Eval Report P1 #7 | 2 | 2.1 |
| Deprecate setup-statusline | Eval Report P1 #8 | 2 | 2.2 |
| Fold check-updates into validate-plugin | Eval Report P1 #9 | 2 | 2.3 |
| Update versions and references | Eval Report P1 (cross-cutting) | 2 | 2.4 |
| Extract shared plan template | Eval Report P2 #10 | 3 | 3.1 |
| Fix schema inconsistencies | Eval Report P2 #11 | 3 | 3.2 |
| Tighten/loosen tool permissions | Eval Report P2 #12, #13 | 3 | 3.3 |
| Fix plan-improvements audit instructions | Eval Report P2 (discovered) | 3 | 3.4 |
| Make help skills dynamic | Eval Report P2 #14 | 3 | 3.5 |
| Migrate review-pr to MCP tools | Eval Report P3 #15 | 4 | 4.1 |
| Add --json output to commands | Eval Report P3 #16 | 4 | 4.2 |
| Add --focus flags | Eval Report P3 #18 | 4 | 4.3 |
| Extract reference tables from long skills | Eval Report P3 #17 | 5 | 5.1 |
| Replace hardcoded model names | Eval Report P3 #19 | 5 | 5.2 |
| Full CLAUDE.md audit | Documentation completeness | 6 | 6.1 |
| README and supporting docs update | Documentation completeness | 6 | 6.2 |
| CHANGELOG entries and flag consistency | Documentation completeness | 6 | 6.3 |
| Final validation pass | Quality gate | 6 | 6.4 |
| Marketplace compatibility verification | Marketplace compatibility | 6 | 6.5 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-03-04 18:45:00*
*Source: /create-plan command — based on comprehensive plugin evaluation report*
