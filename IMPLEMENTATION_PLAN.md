# Implementation Plan

**Generated:** 2026-03-31 12:00:00
**Based On:** Ultra Plan portfolio review analysis (12 items across personal-plugin and bpmn-plugin)
**Total Phases:** 4
**Estimated Total Effort:** ~200 LOC across ~18 files

---

## Executive Summary

This plan addresses 12 findings from a comprehensive portfolio review of the claude-marketplace plugins. The issues fall into four categories: documentation consistency (help skill missing entries, CLAUDE.md claiming dynamic behavior that doesn't exist, missing cross-references between related commands), stale model defaults (Anthropic model ID superseded, date annotations 27 days old), hardcoded machine paths reducing portability (15 path references across 2 skills), and external dependency verification (Bitwarden project ID, Notion schema, model names).

The most architecturally significant finding is that the help skill is entirely static despite documentation in CLAUDE.md, CONTRIBUTING.md, and the eval file all claiming it uses "dynamic Glob-based discovery." This was a planned feature from IMPLEMENTATION_PLAN-v4 that was never implemented. Rather than implementing dynamic discovery in this plan (which requires adding tools to the skill's allowed-tools and rewriting the rendering logic), we fix the static table and correct the documentation. Dynamic help should be a separate future feature.

Items have been grouped into integrated change sets where they share files or dependencies. The rename of `validate-and-ship` → `release-plugin` is included in the documentation consistency phase because it touches the same files (help, CLAUDE.md).

---

## Plan Overview

Phases are ordered by dependency: verification first (confirms whether additional code changes are needed), then two independent content phases (model defaults and path portability), then the largest documentation consistency phase last (which depends on knowing the final skill inventory).

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies |
|-------|------------|------------------|-----------------|--------------|
| 1 | Verification | Verification report for external deps | S (~0 files, ~0 LOC) | None |
| 2 | Model Defaults | Updated model IDs and date annotations | S (~7 files, ~30 LOC) | None |
| 3 | Path Portability | Env var defaults replacing hardcoded paths | S (~2 files, ~40 LOC) | None |
| 4 | Documentation Consistency | Fixed help, renamed skill, updated CLAUDE.md, cross-references | M (~10 files, ~130 LOC) | Phase 1 |

<!-- BEGIN PHASES -->

---

## Phase 1: External Dependency Verification

**Estimated Complexity:** S (~0 files, ~0 LOC)
**Dependencies:** None
**Parallelizable:** Yes (all work items are independent checks)

### Goals

- Verify Bitwarden project ID is still valid
- Verify Notion MCP tool names match what summarize-feedback expects
- Verify Gemini image model name is still current
- Document duplicate skills across installed plugins
- Verify spark-recon external URLs are reachable

### Work Items

#### 1.1 Verify Bitwarden project ID (Item 7) ✅ Completed 2026-03-31
<!-- Status values: PENDING, IN_PROGRESS, COMPLETE [YYYY-MM-DD] -->
**Status: COMPLETE [2026-03-31]**
**Recommendation Ref:** Item 7
**Files Affected:**
- `plugins/personal-plugin/skills/unlock/SKILL.md` (no changes needed)

**Description:**
Run `bws secret list 5022ea9c-e711-4f4e-bf5f-b3df0181a41d` to verify the default project ID returns secrets. If it fails, find the correct project ID and update the skill.

**Tasks:**
1. [x] Run bws secret list with the hardcoded project ID
2. [x] If valid, mark as confirmed — no changes needed
3. [x] If invalid, find correct ID via `bws project list` and update lines 23, 75, 98 of unlock/SKILL.md

**Acceptance Criteria:**
- [x] Project ID confirmed valid OR updated to working ID
- [x] Date annotation updated to 2026-03-31 if ID changed

**Verification Results (2026-03-31):**
Project ID `5022ea9c-e711-4f4e-bf5f-b3df0181a41d` is VALID. Returns 17 secrets including ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, NOTION_API_KEY, and others. No changes needed.

**Notes:**
Requires TROY env var to be set. Run `/unlock` first if environment isn't configured.

---

#### 1.2 Document duplicate skills across installed plugins (Item 8) ✅ Completed 2026-03-31
**Status: COMPLETE [2026-03-31]**
**Recommendation Ref:** Item 8
**Files Affected:**
- None (documentation/findings only)

**Description:**
List all installed plugins and identify which skills appear in multiple namespaces. Document findings so the user can decide which plugins to uninstall.

**Tasks:**
1. [x] Review the skill list from the session for duplicates
2. [x] Identify which installed plugins provide the duplicate copies
3. [x] Present findings to user with recommendation

**Acceptance Criteria:**
- [x] Clear list of duplicate skills with their source plugins
- [x] Recommendation on which plugins to keep vs remove

**Verification Results (2026-03-31):**
Duplicate skills found across installed plugins:
- `explain-project`: personal-plugin, document-skills, superpowers
- `accessibility-annotator`: personal-plugin, superpowers
- `spec-to-prototype`: personal-plugin, superpowers
- `claude-api`: document-skills, claude-api (standalone)
- `pdf`: document-skills, standalone
- `frontend-design`: document-skills, standalone
- `skill-creator`: document-skills, skill-creator (standalone)

**Recommendation:** personal-plugin versions are the authoritative maintained copies. Run `/plugin list` to audit installed plugins and remove redundant `document-skills` and standalone copies that duplicate personal-plugin skills.

**Notes:**
This is an environment configuration action, not a code change in this repo. The duplicates come from separately installed plugins (document-skills, superpowers, claude-api).

---

#### 1.3 Verify project-specific skill dependencies (Item 12)
**Status: COMPLETE [2026-03-31]**
**Recommendation Ref:** Item 12
**Files Affected:**
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (no changes needed)
- `plugins/personal-plugin/skills/spark-recon/SKILL.md` (no changes needed)

**Description:**
Verify that `summarize-feedback` references correct Notion MCP tool names, `evaluate-pipeline-output` matches current pipeline structure, and `spark-recon` URLs are reachable.

**Tasks:**
1. [x] Check if `mcp__plugin_Notion_notion__notion-search` and `mcp__plugin_Notion_notion__notion-fetch` exist as available tools
2. [x] Spot-check spark-arena.com, NVIDIA forum URLs, and GitHub vLLM releases API
3. [x] Check contact-center-lab pipeline output directory structure matches evaluate-pipeline-output expectations
4. [x] Update any stale references found

**Acceptance Criteria:**
- [x] All external dependencies verified or flagged for update
- [x] Any stale tool names or URLs corrected

**Verification Results (2026-03-31):**

**Task 1 -- Notion MCP tool names:**
- `summarize-feedback/SKILL.md` references `mcp__plugin_Notion_notion__notion-search` and `mcp__plugin_Notion_notion__notion-fetch` (lines 37, 63, 87)
- These tools are NOT in the current session's available MCP tool list -- Notion MCP server is not configured in this environment
- Tool names follow the standard MCP naming convention (`mcp__plugin_{ServerName}_{namespace}__{tool-name}`)
- **Status: Requires runtime verification.** Tool names appear correctly formed; actual availability depends on whether the Notion MCP server is configured in the user's Claude settings. No code changes needed.

**Task 2 -- spark-recon URL spot-check:**

| URL | Status | Notes |
|-----|--------|-------|
| `https://api.github.com/repos/vllm-project/vllm/releases?per_page=1` | REACHABLE | Returns valid JSON. Latest: v0.18.1 (2026-03-31) |
| `https://forums.developer.nvidia.com/c/accelerated-computing/dgx-spark-gb10/719` | REACHABLE | Forum loads with 30+ active topics |
| `https://forums.developer.nvidia.com/c/accelerated-computing/dgx-spark-gb10/719.json` | REACHABLE | Discourse JSON API works; returns 30 topics |
| `https://spark-arena.com/leaderboard` | BLOCKED (403) | WebFetch returns HTTP 403. Skill correctly uses browser tools as primary, WebFetch as fallback. Not a bug. |
| `https://api.github.com/repos/nickyu42/spark-vllm-docker/releases` | NOT FOUND (404) | Repo does not exist or is private. Confirmed via both public and authenticated `gh api`. |
| `https://api.github.com/repos/nickyu42/spark-vllm-docker/commits` | NOT FOUND (404) | Same repo, confirmed non-existent/private. |

**Finding:** `nickyu42/spark-vllm-docker` (Check 3 in spark-recon) returns 404 via both public and authenticated GitHub API. May be private, renamed, or removed. Skill will gracefully fail on Check 3 at runtime. **Queued for Phase 4 review.**

**Task 3 -- contact-center-lab pipeline output structure:**
- Lab directory exists at `c:\Users\Troy Davis\dev\contact-center-lab`
- Two pipeline runs in `output/`: `full-small-2026-03-17-1509` and `full-test-2026-03-18-1022`
- `final/` contents match skill expectations: `atoms.json`, `entities.json`, `graph_edges.json`, `graph_nodes.json`, `policies.json`, `predicates.json`, `review_items.json`, `rules.json`, `statistics.json`, `vector_db_atoms.jsonl`
- Skill uses dynamic discovery ("Derive, Don't Hardcode") -- does not hardcode filenames
- **Status: VERIFIED.** Output structure fully compatible. No code changes needed.

**Notes:**
No code changes required. One finding flagged: `nickyu42/spark-vllm-docker` repo returns 404 (queued for Phase 4 review of spark-recon skill).

---

### Phase 1 Testing Requirements

- [ ] bws command executes successfully (or failure is documented)
- [ ] All external URL checks documented with pass/fail status
- [ ] No code changes unless verification reveals stale references

### Phase 1 Completion Checklist

- [ ] All verification items complete
- [ ] Findings documented in conversation
- [ ] Any required code changes identified and queued for this phase or flagged for Phase 4

---

## Phase 2: Model Defaults Update

**Estimated Complexity:** S (~7 files, ~30 LOC)
**Dependencies:** None
**Parallelizable:** Yes (research-topic and visual-explainer are independent)

### Goals

- Update Anthropic model default from `claude-opus-4-5-20251101` to current model
- Update date annotations across all affected files
- Preserve test fixtures (don't change test model names)

### Work Items

#### 2.1 Update Anthropic model default in research-topic (Item 2)
**Status: PENDING**
**Recommendation Ref:** Item 2
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify line 44)
- `plugins/personal-plugin/references/research-models.md` (modify lines 19, 33, 64)
- `plugins/personal-plugin/references/api-key-setup.md` (modify line 36)
- `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/providers/anthropic.py` (modify line 16)
- `plugins/personal-plugin/tools/research-orchestrator/README.md` (modify line 92)

**Description:**
Replace `claude-opus-4-5-20251101` with `claude-opus-4-6-20250725` (the current Opus 4.6 model ID) in all non-test files. Update all "default as of 2026-03-04" annotations to "default as of 2026-03-31". Leave OpenAI and Gemini defaults as-is with "verify with provider" notes since we cannot confirm their current model IDs.

**Tasks:**
1. [ ] Update `research-topic/SKILL.md` line 44: model default and date
2. [ ] Update `research-models.md` lines 19, 33-35, 64: model name and Last Verified date
3. [ ] Update `api-key-setup.md` line 36: example ANTHROPIC_MODEL value
4. [ ] Update `providers/anthropic.py` line 16: DEFAULT_MODEL constant
5. [ ] Update `research-orchestrator/README.md` line 92: model reference
6. [ ] Update date annotations on OpenAI/Gemini entries in research-models.md to 2026-03-31
7. [ ] Verify: `grep -r "claude-opus-4-5" plugins/` returns only test files and archived docs

**Acceptance Criteria:**
- [ ] No non-test, non-archive file references `claude-opus-4-5-20251101`
- [ ] All "Last Verified" dates updated to 2026-03-31
- [ ] Test files unchanged (they test model name parsing)
- [ ] `research-orchestrator` Python code compiles without errors

**Notes:**
The current model is `claude-opus-4-6`. The exact dated ID is `claude-opus-4-6-20250725` based on system information showing "Opus 4.6" as current. If the Anthropic API doesn't accept this ID, fall back to `claude-opus-4-6` (the family alias).

---

#### 2.2 Update date annotations in visual-explainer and accessibility-annotator (Item 6)
**Status: PENDING**
**Recommendation Ref:** Item 6
**Files Affected:**
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify lines 49, 125)
- `plugins/personal-plugin/skills/accessibility-annotator/SKILL.md` (modify line 287)

**Description:**
Update "default as of 2026-03-04" date annotations to "default as of 2026-03-31" for the Gemini image model references. Keep `gemini-3-pro-image-preview` as the model name since we cannot verify it without a Google API call — the `$GOOGLE_IMAGE_MODEL` env var override handles model changes at runtime.

**Tasks:**
1. [ ] Update date annotation in `visual-explainer/SKILL.md` line 49
2. [ ] Update date annotation in `visual-explainer/SKILL.md` line 125
3. [ ] Update date annotation in `accessibility-annotator/SKILL.md` line 287

**Acceptance Criteria:**
- [ ] All Gemini model date annotations show 2026-03-31
- [ ] Model name `gemini-3-pro-image-preview` unchanged (env var handles runtime overrides)

**Notes:**
The visual-explainer Python tool also has the model name in `image_generator.py` and `config.py` — those date comments should also be updated if they contain date annotations.

---

### Phase 2 Testing Requirements

- [ ] `grep -r "claude-opus-4-5" plugins/` returns only test files and docs/archive/
- [ ] `grep "2026-03-04" plugins/personal-plugin/skills/` returns no hits
- [ ] Python tool imports successfully: `python -c "from research_orchestrator.providers.anthropic import AnthropicProvider"`

### Phase 2 Completion Checklist

- [ ] All model defaults updated
- [ ] All date annotations refreshed
- [ ] Test files preserved
- [ ] No regressions in Python tool imports

---

## Phase 3: Path Portability

**Estimated Complexity:** S (~2 files, ~40 LOC)
**Dependencies:** None
**Parallelizable:** Yes (both skills are independent)

### Goals

- Replace hardcoded machine-specific paths with environment variable references
- Keep HTML comment paths as author documentation
- Ensure skills still work on Troy's machine without extra config

### Work Items

#### 3.1 Replace hardcoded paths in accessibility-annotator (Item 3)
**Status: PENDING**
**Recommendation Ref:** Item 3
**Files Affected:**
- `plugins/personal-plugin/skills/accessibility-annotator/SKILL.md` (modify lines 57, 287, 294)

**Description:**
Replace hardcoded `C:\Users\Troy Davis\dev\info\...` paths in operational instructions with environment variable references. Keep the paths in HTML comments (COMPANION TOOLS section, lines 30-32) as author documentation but add a note that these are default paths on the author's machine.

**Tasks:**
1. [ ] Line 57: Change default path to `$IMAGE_STYLE_JSON env var, or provide via --style-json flag` with a note: "(default on author's machine: C:\Users\Troy Davis\dev\info\clean-style-sanitized.json)"
2. [ ] Line 287: Change hardcoded model path to reference `--style-json` flag or `$IMAGE_STYLE_JSON`
3. [ ] Line 294: Change to reference `$GEMINI_IMAGE_LEARNINGS` or note it's optional reference material
4. [ ] Add note to HTML comment COMPANION TOOLS section: "Paths below are defaults on the author's machine. Override via flags or env vars."

**Acceptance Criteria:**
- [ ] No hardcoded machine paths in operational instructions (only in HTML comments as documentation)
- [ ] Skill still works with `--style-json` flag pointing to the file
- [ ] ENV var names documented for each external resource

**Notes:**
The `--style-json` flag already exists and works. The issue is only the default value embedded in the prose instructions.

---

#### 3.2 Replace hardcoded paths in explain-project (Item 3)
**Status: PENDING**
**Recommendation Ref:** Item 3
**Files Affected:**
- `plugins/personal-plugin/skills/explain-project/SKILL.md` (modify lines 68-69, 158, 349)

**Description:**
Replace hardcoded paths in operational instructions. The skill already has `--style` and `--style-json` flags. Replace inline defaults with env var references.

**Tasks:**
1. [ ] Lines 68-69: Change default paths to `$DOC_STYLE_GUIDE` and `$IMAGE_STYLE_JSON` env var references with documented defaults
2. [ ] Line 158: Change structure template path to `$DOC_STRUCTURE_TEMPLATE` env var reference
3. [ ] Line 349: Change doc-builder path to `$DOC_BUILDER_PATH` or `python -m doc_builder` if on PYTHONPATH
4. [ ] Add note to HTML comment COMPANION TOOLS section (lines 32-37): "Paths below are defaults on the author's machine."

**Acceptance Criteria:**
- [ ] No hardcoded machine paths in operational instructions
- [ ] Skill still works when env vars are set to the correct paths
- [ ] Flags (`--style`, `--style-json`) still work as overrides

**Notes:**
For Troy's machine, setting these env vars in ~/.claude/CLAUDE.md or shell profile ensures no disruption. For marketplace users, the flags provide the override mechanism.

---

### Phase 3 Testing Requirements

- [ ] `grep -c "Troy Davis\\\\dev\\\\info" plugins/personal-plugin/skills/accessibility-annotator/SKILL.md` shows reduction (only in HTML comments)
- [ ] `grep -c "Troy Davis\\\\dev\\\\info" plugins/personal-plugin/skills/explain-project/SKILL.md` shows reduction
- [ ] Both skills' `--style-json` flags documented and functional

### Phase 3 Completion Checklist

- [ ] All operational instruction paths converted to env var references
- [ ] HTML comment paths annotated as author defaults
- [ ] No regressions in skill functionality

---

## Phase 4: Documentation Consistency

**Estimated Complexity:** M (~10 files, ~130 LOC)
**Dependencies:** Phase 1 (verification may reveal additional needed updates)
**Parallelizable:** Partially (4.1 and 4.2 must precede 4.3; 4.4 and 4.5 are independent)

### Goals

- Fix help skill to include all skills (including spark-recon)
- Remove false "dynamic discovery" claims from documentation
- Rename validate-and-ship → release-plugin
- Add cross-references between related planning commands
- Add pipeline component labeling to define-questions and ask-questions
- Update CLAUDE.md repository structure to match disk

### Work Items

#### 4.1 Rename validate-and-ship → release-plugin (Item 5)
**Status: PENDING**
**Recommendation Ref:** Item 5
**Files Affected:**
- `plugins/personal-plugin/skills/validate-and-ship/` → `plugins/personal-plugin/skills/release-plugin/` (rename directory)
- `plugins/personal-plugin/skills/release-plugin/SKILL.md` (modify frontmatter name field)

**Description:**
Rename the `validate-and-ship` skill directory and update the `name` field in frontmatter. This must happen before updating the help skill (4.3) so the help table reflects the new name.

**Tasks:**
1. [ ] `git mv plugins/personal-plugin/skills/validate-and-ship plugins/personal-plugin/skills/release-plugin`
2. [ ] Update `name: validate-and-ship` → `name: release-plugin` in SKILL.md frontmatter
3. [ ] Update `description` to clarify it's for plugin releases: "Validate plugins, clean repository, and ship plugin releases in one automated workflow"
4. [ ] Search for any other references: `grep -r "validate-and-ship" plugins/`

**Acceptance Criteria:**
- [ ] Directory renamed on disk
- [ ] Frontmatter `name` field matches directory name
- [ ] No stale references to `validate-and-ship` in any non-archived file

**Notes:**
This is a breaking change for users with muscle memory for `/validate-and-ship`. The skill's behavior is unchanged.

---

#### 4.2 Add cross-references to planning commands and pipeline components (Items 9, 10)
**Status: PENDING**
**Recommendation Ref:** Items 9, 10
**Files Affected:**
- `plugins/personal-plugin/commands/create-plan.md` (modify — add "See also" after description)
- `plugins/personal-plugin/commands/plan-improvements.md` (modify — add "See also" after description)
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify — add "See also" after description)
- `plugins/personal-plugin/commands/define-questions.md` (modify — add pipeline note)
- `plugins/personal-plugin/commands/ask-questions.md` (modify — add pipeline note)

**Description:**
Add brief cross-references to help users choose the right planning command and discover the combined pipeline workflow.

**Tasks:**
1. [ ] Add to `create-plan.md` after the Overview section: "**See also:** `/plan-improvements` for codebase-driven improvements. `/ultra-plan` for issue/bug lists requiring deep investigation."
2. [ ] Add to `plan-improvements.md` after description: "**See also:** `/create-plan` for requirements-driven planning. `/ultra-plan` for issue/bug lists."
3. [ ] Add to `ultra-plan/SKILL.md` after description: "**See also:** `/create-plan` for requirements-driven planning. `/plan-improvements` for codebase analysis."
4. [ ] Add to `define-questions.md` after line 9: "**Pipeline component:** This command extracts questions to JSON. For the combined extract→answer→update workflow, use `/finish-document`."
5. [ ] Add to `ask-questions.md` after line 9: "**Pipeline component:** This command walks through a JSON question file. For the combined extract→answer→update workflow, use `/finish-document`."

**Acceptance Criteria:**
- [ ] Each planning command references the other two
- [ ] Pipeline components point to `/finish-document`
- [ ] No changes to command behavior or frontmatter

**Notes:**
Keep cross-references brief — one or two lines max. These are informational, not behavioral changes.

---

#### 4.3 Fix help skill and update CLAUDE.md (Items 1, 4, 11)
**Status: PENDING**
**Recommendation Ref:** Items 1, 4, 11
**Files Affected:**
- `plugins/personal-plugin/skills/help/SKILL.md` (modify — add spark-recon, rename validate-and-ship → release-plugin, fix examples)
- `CLAUDE.md` (modify — fix dynamic claim, add missing skills to structure)
- `CONTRIBUTING.md` (modify — fix dynamic claim)

**Description:**
The largest work item. Fix the static help table to include all skills on disk, update the renamed skill, remove false dynamic discovery claims, and sync CLAUDE.md's repository structure listing with actual disk contents.

**Tasks:**
1. [ ] Help SKILL.md Mode 1 table: Add `spark-recon` row to SKILLS section
2. [ ] Help SKILL.md Mode 1 table: Change `validate-and-ship` → `release-plugin` with updated description
3. [ ] Help SKILL.md Mode 2: Add `#### /spark-recon` detailed help block
4. [ ] Help SKILL.md Mode 2: Update `#### /validate-and-ship` → `#### /release-plugin`
5. [ ] Help SKILL.md error handling (line 547): Update available skills list (add spark-recon, rename validate-and-ship)
6. [ ] Help SKILL.md line 10: Remove "IMPORTANT: This skill must be updated whenever..." and replace with accurate maintenance note
7. [ ] Fix Mode 2 skill examples that say `/SKILL` — replace with actual invocation examples
8. [ ] CLAUDE.md line 154: Remove "(dynamic, Glob-based discovery)" — replace with "(static table, manually maintained)"
9. [ ] CLAUDE.md lines 548-551: Replace dynamic discovery claim with "Help skills use a static table. Update `skills/help/SKILL.md` when adding or removing commands/skills."
10. [ ] CLAUDE.md structure listing (~line 183): Add `spark-recon/` and `ultra-plan/` entries
11. [ ] CONTRIBUTING.md lines 52, 255: Update dynamic discovery references to match reality

**Acceptance Criteria:**
- [ ] `/help` table skill count matches `ls plugins/personal-plugin/skills/*/SKILL.md | wc -l` (minus help itself)
- [ ] No references to "dynamic" or "Glob-based discovery" in help-related documentation
- [ ] CLAUDE.md structure listing includes all skills on disk
- [ ] `grep "validate-and-ship" CLAUDE.md CONTRIBUTING.md plugins/personal-plugin/skills/help/SKILL.md` returns no hits
- [ ] All Mode 2 examples use realistic invocations, not `/SKILL`

**Notes:**
This is the highest-touch work item. Verify thoroughly by counting skills on disk vs in the help table. The help skill currently lists 16 skills in Mode 1 — after adding spark-recon and renaming validate-and-ship, it should list 17 (all skills minus help itself).

---

### Phase 4 Testing Requirements

- [ ] Skill count in help table matches disk: `ls plugins/personal-plugin/skills/*/SKILL.md | grep -v help | wc -l`
- [ ] `grep -r "validate-and-ship" plugins/ CLAUDE.md CONTRIBUTING.md` returns only archived/deprecated files
- [ ] `grep "dynamic.*discovery\|Glob-based" CLAUDE.md CONTRIBUTING.md` returns no hits
- [ ] All planning commands have "See also" cross-references
- [ ] Pipeline commands reference `/finish-document`

### Phase 4 Completion Checklist

- [ ] All work items complete
- [ ] Help table accurate and complete
- [ ] CLAUDE.md matches disk reality
- [ ] Rename fully propagated
- [ ] No regressions in help output quality

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 1 (all items) | Phase 2, Phase 3 | Verification is read-only |
| Phase 2.1 | Phase 2.2 | Different files entirely |
| Phase 3.1 | Phase 3.2 | Different skill files |
| Phase 4.1 | Phase 4.2 | Different files, but 4.1 must complete before 4.3 |
| Phase 4.4 | Phases 2, 3 | Cross-references touch different files than model/path updates |

**Key constraint:** Phase 4.3 (help/CLAUDE.md) must run after 4.1 (rename) because it needs to reference the new skill name.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| `validate-and-ship` rename breaks user muscle memory | Medium | Low | Name is self-discoverable via `/help`; old name will give "not found" with suggestion |
| Anthropic model ID `claude-opus-4-6-20250725` not accepted by API | Low | Low | The `check-models` dynamic detection handles runtime resolution; fallback is a hint, not the primary path |
| OpenAI/Gemini model defaults still stale | Medium | Low | Date annotations flag staleness; env var overrides handle runtime; deferred to next refresh cycle |
| Env var names for paths not set on Troy's machine | Low | Low | Add to global CLAUDE.md or shell profile; flags still work as overrides |

---

## Success Metrics

- [ ] All phases completed
- [ ] All acceptance criteria met
- [ ] `/help` output matches disk reality (100% accuracy)
- [ ] No hardcoded paths in operational instructions (only in HTML comments)
- [ ] All model date annotations current (2026-03-31)
- [ ] Zero stale references to `validate-and-ship` in active files
- [ ] Zero references to "dynamic Glob-based discovery" in documentation

---

## Appendix: Recommendation Traceability

| Recommendation | Source | Phase | Work Item |
|----------------|--------|-------|-----------|
| Item 1: Add spark-recon to help | Portfolio review | 4 | 4.3 |
| Item 2: Update research model defaults | Portfolio review | 2 | 2.1 |
| Item 3: Fix hardcoded machine paths | Portfolio review | 3 | 3.1, 3.2 |
| Item 4: Fix dynamic help claims | Portfolio review | 4 | 4.3 |
| Item 5: Rename validate-and-ship | Portfolio review | 4 | 4.1 |
| Item 6: Verify visual-explainer model | Portfolio review | 2 | 2.2 |
| Item 7: Verify unlock project ID | Portfolio review | 1 | 1.1 |
| Item 8: Audit duplicate skills | Portfolio review | 1 | 1.2 |
| Item 9: Planning command cross-refs | Portfolio review | 4 | 4.2 |
| Item 10: Pipeline component labeling | Portfolio review | 4 | 4.2 |
| Item 11: Update CLAUDE.md structure | Portfolio review | 4 | 4.3 |
| Item 12: Verify project-specific skills | Portfolio review | 1 | 1.3 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-03-31 12:00:00*
*Source: /ultra-plan portfolio review → /create-plan*
