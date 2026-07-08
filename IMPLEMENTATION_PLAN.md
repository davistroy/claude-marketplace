# Implementation Plan

**Generated:** 2026-07-08 14:59:15
**Based On:** Ultra-plan analysis of review recommendations R1–R13 (LAB_NOTEBOOK.md Entries 008–009; local report `reports/plugin-review-anthropic-guidance-20260708-114842.md`; ADR-0005, ADR-0006)
**Total Phases:** 8
**Estimated Total Effort:** ~4,100 LOC churn across ~75 files

---

## Executive Summary

This plan modernizes all three plugins against current official Anthropic guidance (July 2026): it restores the arch-review agent subsystem to full function (frontmatter, least-privilege tools, dispatch-by-name — the official `claude plugin validate --strict` fails on this today), eliminates every stale model pin by switching agent definitions to tier aliases (ADR-0005), removes all references to commands that don't exist (`/batch` ×15, `/ultrareview` ×11), and brings the 13 over-budget skill/command files toward the official 500-line progressive-disclosure budget by extracting examples, templates, and duplicated content into `references/`.

Interrelated findings are grouped into integrated change sets rather than isolated patches: the planning family (create-plan, plan-improvements, implement-plan) is consolidated onto `references/plan-template.md` as the single source for the model-tier rubric, sizing tables, and append procedure — the drift class that produced two conflicting Execution-Hints framings and a validator that lags its own template. The implement-plan PATH A/B duplication (~90% identical) collapses into one flow parameterized on batch cardinality, per the verified difference ledger.

The plan closes with platform-direction adoption: a skills-first authoring policy (ADR-0006 — new-command deprecated, pattern support ported into new-skill, scaffold-plugin defaults flipped), official `claude plugin validate` in CI, trigger evals in the existing evals/ idiom, description tuning per the official formula, and a coordinated release (personal-plugin 10.0.0, bpmn-plugin 4.2.0, slide-gen 1.2.0, marketplace 3.3.0).

---

## Plan Overview

Phase 1 kills every actively-misleading reference in one commit and syncs the validator to the template it guards — cheap, high-trust wins that also stabilize files later phases refactor. Phases 2–3 are independent hardening tracks (safety/portability; the agent subsystem + model pins). Phase 4 consolidates the planning family before Phase 5 refactors the remaining giants, so validate-plugin's refactor starts from a rule-synced baseline. Phase 6 lands the skills-first scaffolding before Phase 7 documents the policy and turns on official CI validation (which requires Phase 3's agent fixes to pass strict). Phase 8 is wide-shallow polish plus the coordinated release.

Critical path: Phase 1 → Phase 4 → Phase 5 → Phase 8, with Phase 3 → Phase 7 → Phase 8 as the second spine. Phases 1, 2, 3, and 6 have no incoming dependencies and can start immediately; items within every phase are file-disjoint (verified during interaction mapping) so intra-phase parallel dispatch is safe.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|------------|------------------|-----------------|--------------|----------------|
| 1 | Reference integrity & staleness | Zero dangling refs; plan-gate Path B.5 on real mechanics; validator rule-17 sync; research-topic staleness fixed | M (~13 files, ~250 LOC) | None | Parallel |
| 2 | Safety, portability & tool staleness | 4 side-effect skills locked; C:\ paths portable; .gitattributes; visual-explainer model plumbing | M (~18 files, ~270 LOC — wide-shallow) | None | Parallel |
| 3 | Agent subsystem restoration | 9 agents with frontmatter; alias model pins; dispatch-by-name; per-agent meta; smoke-verified | L (~14 files, ~450 LOC) | None | Parallel |
| 4 | Planning-family consolidation | Single-sourced rubric/tables/append-guide; PATH A/B collapsed; ≤500-line planning commands | L (~9 files, ~1,000 LOC churn) | Phase 1 | Parallel |
| 5 | Progressive disclosure — remaining giants | validate-plugin/research-topic/ship + 6 more files at or near budget; new references | L (~15 files, ~1,300 LOC churn) | Phase 1 | Parallel |
| 6 | Skills-first scaffolding | new-skill pattern support; new-command deprecated; scaffold-plugin skills-first (ADR-0006) | M (~5 files, ~250 LOC) | None | Parallel |
| 7 | Guidance, CI & evals | `claude plugin validate` CI job; trigger evals; CLAUDE.md policy + spec refresh | M (~3 files, ~200 LOC) | Phases 3, 6 | Parallel |
| 8 | Descriptions, polish & release | Official-formula descriptions; mechanical polish; plugin READMEs/LICENSE; coordinated version bump | M (~30 files, ~400 LOC — wide-shallow) | Phases 1–7 | Parallel |

### Execution Hints

| Phase | Model Tier | Context Budget | Notes |
|-------|------------|----------------|-------|
| All (default) | `sonnet` | Standard | Per-item Model Tier fields take precedence over phase defaults |
| 4 | `sonnet` | Extended | Large source files (750–1,050 lines) must be read in full before restructuring; 4.4 is per-item `opus` |
| 5 | `sonnet` | Extended | Same — 5.1 reads a 1,385-line file; 5.1 is per-item `opus` |

### Milestones

| Milestone | Phases | Description |
|-----------|--------|-------------|
| M1: Correctness & Trust | 1–3 | No misleading references anywhere; official validator passes personal-plugin strict; agents routed, least-privileged, alias-pinned; side-effect skills locked |
| M2: Budget & Consolidation | 4–5 | Planning family single-sourced; all 13 oversized files at/near the official 500-line budget or documented-dense |
| M3: Modernization & Release | 6–8 | Skills-first policy live in scaffolding, docs, and CI; descriptions on the official formula; v10.0.0/4.2.0/1.2.0/3.3.0 shipped |

<!-- BEGIN PHASES -->

---

## Phase 1: Reference Integrity & Staleness Sweep

**Estimated Complexity:** M (~13 files, ~250 LOC)
**Dependencies:** None
**Execution Mode:** Parallel

### Goals

- Remove every reference to commands that do not exist (`/batch`, `/ultrareview`) and replace with real mechanics
- Sync validate-plugin to the 17-rule template it validates
- Fix all stale model IDs and dead-tool prose in research-topic and its model registry

### Work Items

#### 1.1 Remove `/batch` references; rewrite plan-gate Path B.5 onto real mechanics ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R3 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/skills/plan-gate/SKILL.md` (modify — lines 93–115, 230, 250, 322)
- `plugins/personal-plugin/commands/create-plan.md` (modify — lines 24, 750–765)
- `plugins/personal-plugin/commands/plan-improvements.md` (modify — line 49)

**Description:**
`/batch` does not exist in this repo or the native harness (15 occurrences repo-wide; research-topic's is handled in 1.5). The evident intent everywhere is "parallel execution of independent units in isolated worktrees." Rewrite plan-gate's Path B.5 (its fullest expression, lines 93–115) to route to real mechanics: `/implement-plan` parallel phases (Execution Mode: Parallel / Worktree-Isolated) and background Agent-tool dispatch. Update the mermaid diagram (250), routing table (230), and example (322) to match the renamed path. In create-plan and plan-improvements, replace the `/batch /implement-plan` suggestions with `/implement-plan` parallel-phase guidance.

**Tasks:**
1. [ ] Rewrite plan-gate Path B.5 as "Parallel Decomposition (via /implement-plan parallel phases)" preserving the routing intent and trade-off notes
2. [ ] Update plan-gate lines 106, 112, 115, 230, 250, 322 to the renamed path with no `/batch` token remaining
3. [ ] Replace create-plan.md `/batch` guidance at lines 24 and 750–765 with `/implement-plan` parallel-execution wording
4. [ ] Replace plan-improvements.md line 49 equivalently

**Acceptance Criteria:**
- [ ] WHEN a user follows plan-gate routing for a large independent-unit task THEN the skill SHALL route to `/implement-plan` parallel phases or background Agent dispatch — never to `/batch`
- [ ] `grep -rn -- '/batch' plugins/ --include='*.md' | grep -v deprecated` returns only research-topic (fixed in 1.5) or nothing
- [ ] Path B.5's decomposition guidance (unit count, worktree isolation trade-offs) is preserved, not deleted

**Notes:**
Do not delete the routing path — the decomposition advice is sound; only the dispatch target is fictional.

---

#### 1.2 Replace `/ultrareview` and stale co-author strings ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: haiku**
**Requirement Refs:** R3, R2 (E008/E009)
**Files Affected:**
- `CLAUDE.md` (modify — line 249)
- `WORKFLOWS.md` (modify — lines 93, 115)
- `plugins/personal-plugin/commands/review-arch.md` (modify — line 339)
- `plugins/personal-plugin/commands/review-intent.md` (modify — line 423)
- `plugins/personal-plugin/commands/test-project.md` (modify — lines 323, 500)
- `plugins/personal-plugin/references/patterns/validation.md` (modify — line 243)
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify — lines 89, 284, 291, 292, 363)

**Description:**
`/ultrareview` is a deprecated alias; the current native form is `/code-review ultra`. Replace at all 10 active sites (leave CHANGELOG and LAB_NOTEBOOK historical mentions). Also replace the hardcoded co-author `Claude Opus 4.6 <noreply@anthropic.com>` (ship:363, test-project:323) with model-agnostic `Claude <noreply@anthropic.com>` so it can never go stale.

**Tasks:**
1. [ ] Replace `/ultrareview` → `/code-review ultra` at the 10 listed sites, adjusting surrounding sentence grammar where needed
2. [ ] Replace both co-author strings with `Claude <noreply@anthropic.com>`

**Acceptance Criteria:**
- [ ] `grep -rn 'ultrareview' plugins/ CLAUDE.md WORKFLOWS.md --include='*.md' | grep -v CHANGELOG` returns nothing
- [ ] `grep -rn 'Claude Opus 4\.' plugins/ --include='*.md' | grep -v CHANGELOG` returns nothing

**Notes:**
Purely mechanical string work; no judgment needed.

---

#### 1.3 Fix ultra-plan phase numbering gap ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: haiku**
**Requirement Refs:** R3 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**
Phase headings jump Phase 0 (line 83) → Phase 2 (line 120) — an orphaned renumber. Renumber Phases 2–6 to 1–5 and update the three body mentions of "Phase 0-6" to "Phase 0-5" (lines 34, 85, 89). Verified safe: plan-gate never references ultra-plan phase numbers.

**Tasks:**
1. [ ] Renumber `## Phase 2` → `## Phase 1` through `## Phase 6` → `## Phase 5`, including all intra-file cross-references (e.g., "Phases 3-6", "Phase 5 summary")
2. [ ] Update "Phase 0-6" → "Phase 0-5" at lines 34, 85, 89

**Acceptance Criteria:**
- [ ] Phase headings run 0,1,2,3,4,5 with no gaps
- [ ] `grep -n 'Phase [0-9]' plugins/personal-plugin/skills/ultra-plan/SKILL.md` shows no reference to a Phase 6 or to the old numbering

---

#### 1.4 Sync validate-plugin to the 17-rule template ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R3 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/commands/validate-plugin.md` (modify — lines 768–790, 796–801, 1308–1312)

**Description:**
validate-plugin checks "at least 16 structural rules (numbered 1-16)" while plan-template.md has 17 (rule 17 = Model Tier, added v9.1.0). Update the count check to ≥17 / "numbered 1-17" (lines 778, 783, 788 and the summary duplicate at 1308–1312), and add a rule-17 row to the key-rule content table (796–801) validating by keywords (`Model Tier`, `haiku`, `sonnet`, `opus`).

**Tasks:**
1. [ ] Update rule-count text and thresholds at 768–790 and the summary at 1308–1312
2. [ ] Add rule-17 keyword-validation row to the key-rule table at 796–801

**Acceptance Criteria:**
- [ ] WHEN `/validate-plugin` runs Phase 8.5 against the current plan-template.md THEN it SHALL PASS with 17 rules detected and rule 17 content-validated
- [ ] No remaining hardcode of "16" as the rule count anywhere in the file

**Notes:**
Minimal sync only — the full progressive-disclosure refactor of this file is item 5.1. Keep this diff small so 5.1 starts from a correct baseline.

---

#### 1.5 research-topic staleness: model IDs, `agent:` misuse, dead prose; refresh research-models.md ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R2, R3 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify — lines 14, 46, 164, 213–217, 543–565, 551)
- `plugins/personal-plugin/references/research-models.md` (modify — lines 19, 33, 64, 69)

**Description:**
Replace the pinned `claude-opus-4-6-20250725` default with `claude-opus-4-8` at :46 and :164 (env-overridable pattern stays). Fix the `agent:` misuse at :215 — it currently puts a model ID where a subagent type belongs; the fork header should omit `agent:` (matching the OpenAI/Gemini blocks) and carry the model in the API payload only. Delete the research-orchestrator history prose (:14 clause, :543–565 "Trade-offs vs Previous Implementation") and the `/batch` suggestion (:551). In research-models.md: update the Anthropic ID to `claude-opus-4-8` with Last Verified 2026-07-08, delete the contradictory :69 "Upgrades Available" line, and leave OpenAI/Google IDs with a note that the skill's runtime model-check step is authoritative for them (unverifiable offline — see U3).

**Tasks:**
1. [ ] Update both SKILL.md model defaults and the :215 fork header
2. [ ] Delete :14 orchestrator clause, :543–565 section, :551 `/batch` line
3. [ ] Refresh research-models.md per description

**Acceptance Criteria:**
- [ ] WHEN the Claude research leg is dispatched THEN its fork header SHALL NOT contain an `agent:` field with a model ID
- [ ] `grep -rn 'claude-opus-4-6\|research-orchestrator' plugins/personal-plugin/skills/research-topic/ plugins/personal-plugin/references/research-models.md` returns nothing
- [ ] research-models.md carries no self-contradictory upgrade guidance

**Notes:**
Structural dedup of the three provider blocks is item 5.2 — keep this to staleness fixes so the two diffs stay reviewable.

---

### Phase 1 Testing Requirements

- [x] Zero-hit greps for `/batch`, `/ultrareview`, `claude-opus-4-6`, `Claude Opus 4.` (excluding CHANGELOG/LAB_NOTEBOOK/docs/archive)
- [x] `/validate-plugin personal-plugin` Phase 8.5 passes against the live template

### Phase 1 Completion Checklist

- [x] All work items complete
- [x] All tests passing
- [x] Documentation updated
- [x] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| Pre-commit | `bash scripts/pre-commit` | Exit code 0 |
| Dangling refs | `! grep -rn -- '/batch\|/ultrareview' plugins/ CLAUDE.md WORKFLOWS.md --include='*.md' \| grep -v 'CHANGELOG\|deprecated'` | No matches |

<!-- END DOD -->

---

## Phase 2: Safety, Portability & Tool Staleness

**Estimated Complexity:** M (~18 files, ~270 LOC — file count is wide-shallow: most edits are 1–5 line frontmatter/path/config changes)
**Dependencies:** None
**Execution Mode:** Parallel

### Goals

- Lock down the four side-effect-primary skills per official `disable-model-invocation` semantics
- Make every hardcoded Windows path portable across the dual Windows/Linux environment
- Prevent line-ending drift permanently; fix visual-explainer's dead model plumbing

### Work Items

#### 2.1 Side-effect skill lockdown ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: haiku**
**Requirement Refs:** R5 (E008/E009; approved defaults in E009)
**Files Affected:**
- `plugins/personal-plugin/skills/brain-entry/SKILL.md` (modify)
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)
- `plugins/personal-plugin/skills/lab-notebook/SKILL.md` (modify)
- `plugins/personal-plugin/skills/create-wiki/SKILL.md` (modify)

**Description:**
brain-entry: add `disable-model-invocation: true` and `allowed-tools: Bash(curl:*)` (its body uses only curl; Cloudflare requires curl UA). unlock: add `disable-model-invocation: true` and fix the malformed permission glob `Bash(powershell*)` → `Bash(powershell:*)`. lab-notebook: add `disable-model-invocation: true` (it injects an 11-rule CLAUDE.md block). create-wiki: add `disable-model-invocation: true` and REMOVE its `paths:` auto-activation lines (redundant — the wiki skill's own docs state the injected CLAUDE.md rules handle automatic maintenance; verified wiki/SKILL.md has no paths and needs none).

**Tasks:**
1. [ ] brain-entry frontmatter additions
2. [ ] unlock frontmatter addition + glob fix
3. [ ] lab-notebook frontmatter addition
4. [ ] create-wiki frontmatter addition + `paths:` removal

**Acceptance Criteria:**
- [ ] WHEN a conversation merely resembles a capture/secret/setup scenario THEN none of these four skills SHALL auto-invoke (model can still suggest them verbally)
- [ ] All four pass `/validate-plugin` frontmatter checks
- [ ] `grep -c 'disable-model-invocation: true' plugins/personal-plugin/skills/*/SKILL.md` increases from 4 to 8

---

#### 2.2 Windows-path portability in three skills ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R4 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/skills/explain-project/SKILL.md` (modify — lines 34, 36, 37, 38, 39, 70, 71, 110, 177, 379)
- `plugins/personal-plugin/skills/accessibility-annotator/SKILL.md` (modify — lines 32, 33, 34, 59)
- `plugins/personal-plugin/skills/evaluate-pipeline-output/SKILL.md` (modify — line 98)

**Description:**
Rewrite `C:\Users\Troy Davis\...` literals to portable equivalents per the verified mapping: doc-builder → `~/dev/tools/doc-builder`; style guides → `~/.claude/styles/CFA_Word_Style_Guide.md`; style JSONs → `~/dev/brand-assets/clients/cfa/styles/clean-style-sanitized.json`; learnings doc → `~/dev/info/gemini-image-generation-learnings.md`; pipeline dir → `~/dev/contact-center-lab/pipeline`; output → `~/Downloads/...`. Keep the existing env-var override pattern (`$DOC_BUILDER_PATH` etc.) — only the author-default literals change. Line 24's illustrative placeholder stays. `~/dev/info/technical-document-structure-template.md` (lines 36/177) is missing on the Linux VM (U4): rewrite the path AND add a one-line existence-check fallback instruction ("if absent, proceed without the structure template and note it in output").

**Tasks:**
1. [ ] Rewrite all 15 path literals per mapping
2. [ ] Add the missing-file fallback note for the structure template
3. [ ] Spot-verify each rewritten path exists on this machine (except the known-missing one)

**Acceptance Criteria:**
- [ ] `grep -rn 'C:\\\\Users\|C:/Users' plugins/ --include='*.md'` returns nothing
- [ ] WHEN explain-project runs on Linux THEN every referenced input path SHALL resolve or be handled by an explicit documented fallback

---

#### 2.3 Line-ending normalization + .gitattributes ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R4 (E008/E009)
**Files Affected:**
- `.gitattributes` (create)
- `plugins/personal-plugin/skills/prime/SKILL.md` (renormalize to LF)
- `.markdownlint.json` (renormalize to LF)

**Description:**
Create `.gitattributes` with explicit rules: `* text=auto`, `*.md text eol=lf`, `*.py text eol=lf`, `*.json text eol=lf`, `*.yml text eol=lf`, `*.sh text eol=lf`, `*.zip binary`. Then `git add --renormalize .` — verified blast radius is exactly two CRLF files (prime/SKILL.md, .markdownlint.json) and one binary (.zip, protected by the binary rule). Confirm prime's `name:` frontmatter parses cleanly post-normalization.

**Tasks:**
1. [ ] Write .gitattributes
2. [ ] Renormalize; confirm `git status` shows only the two expected files
3. [ ] Verify `git ls-files --eol` reports no `i/crlf` or `i/mixed`

**Acceptance Criteria:**
- [ ] `git ls-files --eol | grep -cE 'i/(crlf|mixed)'` returns 0
- [ ] The .zip file is untouched (binary attribute)
- [ ] WHEN a future file is committed from the Windows environment THEN git SHALL normalize it to LF in-repo

---

#### 2.4 visual-explainer model plumbing ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R2 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/cli.py` (modify — construction sites ~940, ~1102)
- `.../src/visual_explainer/image_evaluator.py`, `prompt_generator.py`, `prompt_refiner.py` (modify — DEFAULT_MODEL)
- `.../src/visual_explainer/api_setup.py` (modify — line 228)
- `.../src/visual_explainer/config.py` (modify — default at :315)
- `.../styles/professional-clean.json`, `professional-sketch.json`, `styles/README.md` (modify — remove dead TargetModelHint)
- `.../tests/conftest.py`, `test_prompt_refiner.py` (modify)

**Description:**
`config.claude_model` (env-overridable) is consumed by only one module; the real pipeline always uses hardcoded `DEFAULT_MODEL = "claude-sonnet-4-20250514"` because cli.py never passes `model=`. Fix the root cause: wire `internal_config.claude_model` through the cli.py construction sites (PromptGenerator ~940, ImageEvaluator ~1102 — thread config where it isn't already). Update `DEFAULT_MODEL` constants and config default to `claude-sonnet-5`; api_setup:228's validation ping likewise. Delete the dead `TargetModelHint` key from both style JSONs and its README:37 mention (zero consumers — verified). Fix the brittle exact-string assertion in test_prompt_refiner.py:31-33 to assert pass-through of the constructor arg rather than a hardcoded ID; align conftest fixture model values.

**Tasks:**
1. [ ] Wire config.claude_model through both cli.py construction sites
2. [ ] Update DEFAULT_MODEL ×3, api_setup ping, config.py default to `claude-sonnet-5`
3. [ ] Remove TargetModelHint from 2 JSONs + README
4. [ ] Fix test assertions; run the tool's full pytest suite

**Acceptance Criteria:**
- [ ] WHEN `VISUAL_EXPLAINER_CLAUDE_MODEL` is set THEN the prompt-generation, refinement, and evaluation stages SHALL all use it (not module constants)
- [ ] `grep -rn 'claude-sonnet-4-20250514\|gemini-2.0-flash-exp' plugins/personal-plugin/tools/visual-explainer/` returns nothing
- [ ] visual-explainer pytest suite passes; coverage gate (65%) still met

**Notes:**
Escalate if wiring config through cli.py reveals additional consumers with incompatible constructor signatures — that coupling wasn't fully visible from the investigation.

---

### Phase 2 Testing Requirements

- [x] visual-explainer full pytest suite green at its coverage gate
- [x] Frontmatter validation passes for the four locked skills
- [x] eol audit clean

### Phase 2 Completion Checklist

- [x] All work items complete
- [x] All tests passing
- [x] Documentation updated
- [x] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Tool tests | `python -m pytest plugins/personal-plugin/tools/visual-explainer/tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| EOL | `git ls-files --eol \| grep -cE 'i/(crlf\|mixed)' \| grep -qx 0` | Exit code 0 |
| Paths | `! grep -rn 'C:\\\\Users' plugins/ --include='*.md'` | No matches |

<!-- END DOD -->

---

## Phase 3: Agent Subsystem Restoration

**Estimated Complexity:** L (~14 files, ~450 LOC)
**Dependencies:** None
**Execution Mode:** Parallel

### Goals

- Give all 9 arch-review agents spec-conformant frontmatter (the official validator fails on this today)
- Switch implementer model pins to tier aliases (ADR-0005)
- Simplify dispatch to subagent-by-name; replace the shared `.meta.json` with per-agent meta files; standardize Agent-tool naming

### Work Items

#### 3.1 Frontmatter + per-agent meta for the 9 arch-review agents ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R1 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/agents/solutions-architect.md`, `data-architect.md`, `integration-architect.md`, `software-engineer.md`, `performance-engineer.md`, `qa-architect.md`, `security-architect.md`, `platform-engineer.md`, `risk-compliance.md` (modify — all 9)

**Description:**
Add YAML frontmatter to each: `name:` exactly equal to the filename stem (dispatch uses it as subagent_type — any mismatch breaks routing), `description:` from the extracted one-sentence charters (E009 investigation §5), `tools: Read, Glob, Grep, Bash, Write, Edit` (agents write findings files and run Bash probes — a read-only set would break the pipeline), `model: inherit` (deep reviews run at the session's tier — ADR-0005), `effort: high`. Additionally change each agent's meta-output instruction from "merge into shared `arch-review/findings/.meta.json`" to "write your own `arch-review/findings/<agent-name>.meta.json`" — eliminating the concurrent-write collision that motivated worktree isolation.

**Tasks:**
1. [ ] Add frontmatter block to all 9 files (name = stem, verified descriptions, tools/model/effort as specified)
2. [ ] Update each agent's `.meta.json` instruction to the per-agent filename
3. [ ] Confirm `claude plugin validate --strict ./plugins/personal-plugin` no longer warns on agents

**Acceptance Criteria:**
- [ ] WHEN Claude Code loads personal-plugin THEN all 9 agents SHALL register with routing descriptions and the specified tool set (not "Tools: All tools")
- [ ] `for f in plugins/personal-plugin/agents/*.md; do head -1 "$f" | grep -q '^---$' || echo "FAIL $f"; done` prints nothing
- [ ] Every `name:` value equals its filename stem exactly

---

#### 3.2 Implementer agents: pins → aliases ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: haiku**
**Requirement Refs:** R2, ADR-0005 (E008/E009)
**Files Affected:**
- `.claude/agents/haiku-implementer.md` (modify — line 3)
- `.claude/agents/sonnet-implementer.md` (modify — line 3)
- `.claude/agents/opus-implementer.md` (modify — line 3)

**Description:**
Replace `model: claude-haiku-4-5-20251001` → `model: haiku`; `model: claude-sonnet-4-6` → `model: sonnet`; `model: claude-opus-4-7` → `model: opus`. Bodies reference tiers conceptually only (verified) — no other edits. implement-plan references these agents by name, so no consumer changes are needed.

**Tasks:**
1. [ ] Three one-line frontmatter edits

**Acceptance Criteria:**
- [ ] `grep -h '^model:' .claude/agents/*.md` returns exactly `model: haiku`, `model: sonnet`, `model: opus`
- [ ] WHEN implement-plan dispatches `sonnet-implementer` THEN it SHALL run on the current sonnet-tier model without any plan or command edit

---

#### 3.3 arch-review dispatch simplification ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R1, R11 (E008/E009)
**Depends On:** 3.1
**Files Affected:**
- `plugins/personal-plugin/skills/arch-review/SKILL.md` (modify — frontmatter line 6; dispatch block 86–128; synthesis 134–139)

**Description:**
With agents registered via frontmatter, stop inlining agent-file contents into dispatch prompts: the dispatch block (92–112) passes `subagent_type` (namespaced `personal-plugin:<name>`; verify bare-name fallback in 3.5) plus the intake content and output paths only. Remove the `isolation: worktree` prescriptions (95, 128) — the per-agent meta files from 3.1 eliminate the collision they guarded against, and worktree isolation risks orphaning findings written to relative paths. Update the dispatch table (114–126) to namespaced values. Fix "Task tool" → "Agent tool" at :88 and `Task` → `Agent` in the frontmatter allowed-tools. Update the Lead synthesis step (134–139) to read the 9 per-agent `<agent>.meta.json` files and merge them (replacing the shared-file read).

**Tasks:**
1. [ ] Rewrite dispatch block: subagent_type-by-name, no file inlining, no worktree prose
2. [ ] Update dispatch table to `personal-plugin:` namespaced types
3. [ ] Fix Task→Agent naming (body :88 + frontmatter :6)
4. [ ] Update synthesis to per-agent meta merge

**Acceptance Criteria:**
- [ ] WHEN arch-review dispatches an agent THEN the prompt SHALL NOT contain pasted agent-file contents and SHALL rely on the registered agent's own system prompt
- [ ] `grep -n 'Task tool\|isolation: worktree' plugins/personal-plugin/skills/arch-review/SKILL.md` returns nothing
- [ ] Synthesis instructions reference `findings/<agent>.meta.json` per-agent files

**Notes:**
Escalate if the intake/prompt contract turns out to carry per-agent variation that the registered system prompts can't express — that would require keeping partial inlining.

---

#### 3.4 arch-review-single + arch-synthesize alignment ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R1, R11 (E008/E009)
**Depends On:** 3.1
**Files Affected:**
- `plugins/personal-plugin/commands/arch-review-single.md` (modify — frontmatter line 5; steps 33–40)
- `plugins/personal-plugin/commands/arch-synthesize.md` (modify — meta-reading step)

**Description:**
Mirror 3.3 in the single-agent command: dispatch by subagent_type instead of "Spawn a single Task with the agent's full definition" (L38); fix frontmatter `Task` → `Agent`. In arch-synthesize (read-only synthesizer), update the meta-reading instructions from the shared `.meta.json` to globbing `findings/*.meta.json` and merging.

**Tasks:**
1. [ ] arch-review-single: dispatch-by-name rewrite + frontmatter fix
2. [ ] arch-synthesize: per-agent meta glob + merge

**Acceptance Criteria:**
- [ ] WHEN `/arch-review-single security-architect <target>` runs THEN it SHALL dispatch the registered agent by type and produce `findings/security-architect.md` + `findings/security-architect.meta.json`
- [ ] arch-synthesize correctly aggregates N per-agent meta files

---

#### 3.5 Smoke verification (resolves U1, U2) ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R1 (E009 Unknowns U1, U2)
**Depends On:** 3.1, 3.3, 3.4
**Files Affected:**
- (no repo files — verification item; findings recorded in LAB_NOTEBOOK.md)

**Description:**
Dispatch one arch-review agent (smallest: solutions-architect) against a tiny target directory via the updated arch-review-single flow. Verify: (a) the namespaced subagent_type resolves (U2 — if `personal-plugin:solutions-architect` fails, test bare `solutions-architect` and update the dispatch table accordingly); (b) findings + per-agent meta land in the main working tree (U1 — no worktree isolation in the new design, so files must appear at the expected relative paths). Log results to LAB_NOTEBOOK as part of the phase entry.

**Tasks:**
1. [ ] Run the smoke dispatch; record subagent_type resolution behavior
2. [ ] Verify findings file + meta file exist at expected paths with valid content
3. [ ] Update dispatch tables if the namespace form differs from assumption; mark U1/U2 Resolved in this plan

**Acceptance Criteria:**
- [ ] WHEN the smoke dispatch completes THEN `arch-review/findings/solutions-architect.md` and `.../solutions-architect.meta.json` SHALL exist in the main tree
- [ ] U1 and U2 rows in the Unknowns Register are marked Resolved with the answer

---

### Phase 3 Testing Requirements

- [x] `claude plugin validate --strict ./plugins/personal-plugin` passes (agents were the only strict failure)
- [x] Smoke dispatch (3.5) succeeds end-to-end

### Phase 3 Completion Checklist

- [x] All work items complete
- [x] All tests passing
- [x] Documentation updated
- [x] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| Official strict | `claude plugin validate --strict ./plugins/personal-plugin` | Exit code 0 |
| Agent frontmatter | `for f in plugins/personal-plugin/agents/*.md; do head -1 "$f" \| grep -q '^---$' \|\| exit 1; done` | Exit code 0 |

<!-- END DOD -->

---

## Phase 4: Planning-Family Consolidation

**Estimated Complexity:** L (~9 files, ~1,000 LOC churn)
**Dependencies:** Phase 1
**Execution Mode:** Parallel

### Goals

- Make `references/plan-template.md` the single source for the rubric, sizing tables, and append procedure
- Collapse implement-plan's duplicated PATH A/B into one parameterized flow
- Bring all three planning commands to ≤500 lines

### Work Items

#### 4.1 Create shared planning references ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R7 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/references/plan-append-guide.md` (create)
- `plugins/personal-plugin/references/recommendations-template.md` (create)

**Description:**
Extract the append-vs-overwrite procedure into `plan-append-guide.md` using create-plan's superset version (530–635, including the archive branch that plan-improvements lacks), parameterizing the separator string (`from /create-plan` vs `from /plan-improvements`). Extract the full RECOMMENDATIONS.md output template from plan-improvements 218–370 into `recommendations-template.md` (top-level `<noun>-template.md` naming convention). Both files get a one-paragraph purpose header naming their consumers.

**Tasks:**
1. [ ] Author plan-append-guide.md (procedure steps 1–10 + before/after example + archive branch)
2. [ ] Author recommendations-template.md (header + 10 category blocks + Quick Wins/Strategic/Not-Recommended)

**Acceptance Criteria:**
- [ ] Both files exist with content byte-equivalent in substance to the current inline versions (no semantic drift introduced)
- [ ] Each names both consumer commands and the parameterized separator convention

---

#### 4.2 create-plan.md consolidation ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R6, R7 (E008/E009)
**Depends On:** 4.1
**Files Affected:**
- `plugins/personal-plugin/commands/create-plan.md` (modify — target ≤500 lines)
- `plugins/personal-plugin/references/create-plan-examples.md` (create)

**Description:**
Replace the inline model-tier rubric (437–440) with a pointer to plan-template.md rule 17; replace the S/M/L table (446–451) with a pointer to the template's Sizing Constraints. Replace the append section body (530–635) with a short control-flow summary + pointer to plan-append-guide.md. Move the Phase 5.2 summary-report sample (707–767), AGENTS.md generation details (693–706), and Examples (834–886) to create-plan-examples.md. Core workflow (Phases 1–3 logic, error handling) stays verbatim.

**Tasks:**
1. [ ] Apply pointer replacements (rubric, sizing, append)
2. [ ] Extract the three bulk blocks to create-plan-examples.md
3. [ ] Verify remaining file reads coherently end-to-end and is ≤500 lines

**Acceptance Criteria:**
- [ ] WHEN a planner follows create-plan THEN every rubric/sizing/append decision SHALL resolve via the shared template/guide (no inline copy to drift)
- [ ] `wc -l < plugins/personal-plugin/commands/create-plan.md` ≤ 500
- [ ] `/validate-plugin personal-plugin` passes

**Notes:**
Behavior-preserving (constitution C8): pointers must carry enough inline context (one-line summaries) that the command remains executable without pre-reading every reference. Executed via one sonnet→opus escalation: the ≤500 target conflicted with the byte-intact clause; opus moved illustration blocks only — final 470 lines, decision logic untouched.

---

#### 4.3 plan-improvements.md consolidation ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: sonnet**
**Requirement Refs:** R6, R7 (E008/E009)
**Depends On:** 4.1
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify — target ≤500 lines)

**Description:**
Same treatment: rubric (480–483) and S/M/L table (503–508) become template pointers; RECOMMENDATIONS template body (218–370) becomes a pointer to recommendations-template.md; append example (408–464) points to plan-append-guide.md; AGENTS.md gen (582–619) and Examples (692–756) trimmed to pointers/one short example. Critically, REFRAME the Execution-Hints section (553–568) to the canonical create-plan/template framing — per-item tiers primary, phase-level override secondary, rule-15 column schema (`Phase | Model Tier | Context Budget | Notes`) — resolving the conflicting-framings drift.

**Tasks:**
1. [ ] Pointer replacements (rubric, sizing, RECOMMENDATIONS template, append)
2. [ ] Execution-Hints reframe to rule-15 schema and per-item-primary semantics
3. [ ] Verify ≤500 lines and coherent flow

**Acceptance Criteria:**
- [ ] WHEN plan-improvements emits Execution Hints THEN the columns and semantics SHALL match plan-template.md rule 15 exactly
- [ ] `wc -l < plugins/personal-plugin/commands/plan-improvements.md` ≤ 500
- [ ] The 10-category assessment checklist and priority rubric (core workflow) remain intact

---

#### 4.4 implement-plan.md: PATH collapse + mechanics cleanup ✅ Completed 2026-07-08
**Status: COMPLETE [2026-07-08]**
**Model Tier: opus**
**Requirement Refs:** R6, R11 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/commands/implement-plan.md` (modify — target ≤650 lines)
- `plugins/personal-plugin/references/implement-plan-state-schema.md` (create)

**Description:**
Collapse PATH A (375–522) and PATH B (526–669) into one flow parameterized on batch cardinality, using the verified difference ledger as the spec: singular vs `_batch` state keys; B-only `run_in_background: true` + single-message multi-dispatch + max-3/overlap constraints; commit-message template (single item vs phase+item list); plural wording in TESTS_STUCK/docs steps; B4b/B2 already delegate to A-logic. Extract the implementer prompt (405–413) and testing-subagent prompt (433–452) to appear once each. Move the state-schema JSON (130–181) to `references/implement-plan-state-schema.md` with a field-summary table inline. Drop vestigial `Task` from allowed-tools (line 5; keep Agent + TaskCreate/TaskUpdate/TaskOutput). Replace the `cat << EOF` state-file heredoc (317–347) with a Write-tool instruction and the `grep >> .gitignore` hack (355) with a Read-then-Edit "ensure line present" instruction.

**Tasks:**
1. [ ] Author the unified execution flow encoding BOTH modes' exact semantics (cardinality-parameterized)
2. [ ] Single-instance the two subagent prompts
3. [ ] Extract state schema to the new reference; leave summary table
4. [ ] allowed-tools, heredoc, and gitignore-hack cleanups
5. [ ] Semantic side-by-side check: every A-step and B-step behavior maps to the unified flow

**Acceptance Criteria:**
- [ ] WHEN a phase's Execution Mode is Sequential THEN the unified flow SHALL reproduce PATH A semantics exactly (state keys, commit format, escalation, shedding)
- [ ] WHEN Parallel THEN PATH B semantics exactly (background dispatch, max-3 constraint, batch state, batch commit format)
- [ ] `wc -l < plugins/personal-plugin/commands/implement-plan.md` ≤ 650
- [ ] No instruction references the removed `Task` tool for spawning

**Notes:**
Highest-risk item in the plan. The difference ledger (E009 investigation §3) is the authoritative spec — do not re-derive from scratch. If any A/B difference proves semantic rather than cardinality-mechanical, escalate is moot (already opus): flag it in LEARNINGS and preserve both behaviors explicitly.

---

### Phase 4 Testing Requirements

- [x] `/validate-plugin personal-plugin` passes (template pointers intact, frontmatter clean)
- [x] Line budgets met: create-plan ≤500, plan-improvements ≤500, implement-plan ≤650
- [x] Manual read-through: each command executable without opening references (pointers carry summaries)

### Phase 4 Completion Checklist

- [x] All work items complete
- [x] All tests passing
- [x] Documentation updated
- [x] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| Budgets | `wc -l plugins/personal-plugin/commands/{create-plan,plan-improvements}.md \| awk '$1>500 && $2!="total"{exit 1}'; wc -l < plugins/personal-plugin/commands/implement-plan.md \| awk '{exit ($1>650)}'` | Exit code 0 |
| Rubric single-source | `grep -c 'haiku.*deterministic' plugins/personal-plugin/commands/*.md \| grep -v ':0'` | Only pointers remain (no full rubric copies) |

<!-- END DOD -->

---

## Phase 5: Progressive Disclosure — Remaining Giants

**Estimated Complexity:** L (~15 files, ~1,300 LOC churn)
**Dependencies:** Phase 1
**Execution Mode:** Parallel

### Goals

- Bring validate-plugin, research-topic, ship, and six more files to/toward the official 500-line budget
- Replace hand-synced inventories and hardcoded repo specifics in validate-plugin with dynamic checks

### Work Items

#### 5.1 validate-plugin refactor
**Status: PENDING**
**Model Tier: opus**
**Requirement Refs:** R6 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/commands/validate-plugin.md` (modify — 1,385 → target ≤700 lines)
- `plugins/personal-plugin/references/validation-output-examples.md` (create)

**Description:**
Move the end-to-end example transcripts (1266–1385), mode output samples (--report/--strict/--scorecard, 1151–1257), and per-phase "Report:"/"Or on failure:" sample blocks to `references/validation-output-examples.md`, following the existing scorecard-extraction precedent — each phase keeps a one-line output-format pointer. Make Phase 8.6's reference inventory dynamic: keep a compact required-file list (data), replace the per-file "Required Since" prose table with "list `references/` and diff against the required set." Replace hardcoded `davistroy/claude-marketplace` (997, 1081, 1087) with `git remote get-url origin` derivation, and stale dates/versions (853–859, 878, 887–892, 1199, 1246) with `[N]`-style placeholders per the item-C10 precedent.

**Tasks:**
1. [ ] Extract the three sample-output groups to the new reference
2. [ ] Rewrite Phase 8.6 as required-list + dynamic diff
3. [ ] Dynamic repo-URL + placeholder sweep
4. [ ] Verify all 9 phases + modes remain fully specified; ≤700 lines

**Acceptance Criteria:**
- [ ] WHEN `/validate-plugin --all` runs THEN every phase SHALL execute identically to the pre-refactor behavior (checks unchanged; only sample bulk moved)
- [ ] WHEN a new reference file is added to `references/` THEN Phase 8.6 SHALL report it without any validate-plugin edit
- [ ] `wc -l < plugins/personal-plugin/commands/validate-plugin.md` ≤ 700

**Notes:**
This file is the repo's QA tool — regressions here mask other regressions. Checks move verbatim; only illustrations move to references.

---

#### 5.2 research-topic structural dedup
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R6 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify — 607 → target ≤400 lines)
- `plugins/personal-plugin/references/research-provider-protocols.md` (create)

**Description:**
The three provider prompt blocks (Claude 211–268, OpenAI 270–341, Gemini 343–410) are near-identical. Replace with ONE parameterized subagent-prompt template plus a provider-deltas table (endpoint, auth mechanism, model field name, sync-vs-poll + status field, depth parameter, parse target — the verified table from E009), with full per-provider curl examples living in `references/research-provider-protocols.md`.

**Tasks:**
1. [ ] Author the parameterized prompt + deltas table in SKILL.md
2. [ ] Move full curl/poll examples to the new reference
3. [ ] Verify ≤400 lines and that each provider leg remains independently executable

**Acceptance Criteria:**
- [ ] WHEN any of the three research legs dispatches THEN its subagent SHALL have a complete protocol (template + deltas or reference) with no behavioral change
- [ ] `wc -l < plugins/personal-plugin/skills/research-topic/SKILL.md` ≤ 400

**Notes:**
Escalate if the OpenAI/Gemini polling flows prove too divergent for one template — then keep two templates (sync/async) rather than forcing one.

---

#### 5.3 ship refactor
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R6, R10 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify — 575 → target ≤420 lines)
- `plugins/personal-plugin/references/ship-output-templates.md` (create)

**Description:**
Move the Phase 8 success/failure/exhaustion output templates (444–546) and the fix-loop pseudocode (335–376) to `references/ship-output-templates.md` with inline one-line pointers. Fold the body "Proactive Triggers" section (32–40) into the frontmatter description per the official all-triggers-in-description guidance (this is ship's R10 treatment; the other skills get theirs in Phase 8).

**Tasks:**
1. [ ] Extract templates + pseudocode to the reference
2. [ ] Merge Proactive Triggers into description; delete the body section
3. [ ] Verify ≤420 lines; dynamic git `!` injection block untouched

**Acceptance Criteria:**
- [ ] WHEN ship reaches Phase 8 THEN it SHALL produce the same three output formats via the referenced templates
- [ ] Frontmatter description alone captures all former Proactive-Trigger conditions
- [ ] `wc -l < plugins/personal-plugin/skills/ship/SKILL.md` ≤ 420

---

#### 5.4 Batch A: clean-repo, finish-document, bpmn-to-drawio
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R6 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/commands/clean-repo.md` (modify — 552 → ~440)
- `plugins/personal-plugin/references/clean-repo-examples.md` (create)
- `plugins/personal-plugin/commands/finish-document.md` (modify — 516 → ~420)
- `plugins/bpmn-plugin/skills/bpmn-to-drawio/SKILL.md` (modify — 516 → ~330)
- `plugins/bpmn-plugin/references/bpmn2drawio-reference.md` (create)

**Description:**
clean-repo: move the three example transcripts (462–544) and JSON-output schema (418–447) to a reference. finish-document: replace the duplicated question-flow display/session-command tables/help text (174–265) with pointers to `/ask-questions` (already cross-referenced at 146) and the inline JSON schemas (74–97, 302–326) with schema-file references — its win is de-duplication. bpmn-to-drawio: consolidate the post-line-165 reference material (CLI reference 167–203, themes 206–268, Python API 299–337, element tables 341–393) into `plugins/bpmn-plugin/references/bpmn2drawio-reference.md`; core Steps 1–6 stay.

**Tasks:**
1. [ ] clean-repo extraction (+ new reference)
2. [ ] finish-document de-duplication via pointers
3. [ ] bpmn-to-drawio consolidation (+ new reference in the bpmn-plugin bundle)

**Acceptance Criteria:**
- [ ] Each file at or under its target; every moved block reachable via an explicit pointer
- [ ] WHEN bpmn-to-drawio runs a conversion THEN Steps 1–6 SHALL be fully specified without opening the reference (reference is for options/edge lookup)

---

#### 5.5 Batch B: create-wiki, evaluate-pipeline-output, test-project
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R6 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/skills/create-wiki/SKILL.md` (modify — 503 → ~370)
- `plugins/personal-plugin/references/claude-md-wiki-section.md` (create)
- `plugins/personal-plugin/references/wiki-readme-template.md` (create)
- `plugins/personal-plugin/skills/evaluate-pipeline-output/SKILL.md` (modify — 645 → ~490)
- `plugins/personal-plugin/skills/evaluate-pipeline-output/references/report-format.md` (create)
- `plugins/personal-plugin/commands/test-project.md` (modify — 502 → ~465, light trim)

**Description:**
create-wiki: the verbatim-emitted CLAUDE.md injection block (349–428) and wiki README template (287–341) become reference files the skill Reads at emission time. evaluate-pipeline-output: Phase-13 report template (487–604) and evaluator-guidance tail (606–645) move to a skill-local `references/` dir; the 13-phase core is legitimately dense — do not force further cuts. test-project: trim the verbose Performance section (449–486) inline; no reference file warranted.

**Tasks:**
1. [ ] create-wiki extractions ×2 (+ Read-at-emission instructions)
2. [ ] evaluate-pipeline-output extractions (skill-local references/)
3. [ ] test-project inline trim

**Acceptance Criteria:**
- [ ] WHEN create-wiki performs Step 7/8 THEN it SHALL emit byte-identical README/CLAUDE.md content sourced from the reference files
- [ ] evaluate-pipeline-output ≤500 or documented-dense with extraction complete
- [ ] test-project ≤470

---

### Phase 5 Testing Requirements

- [ ] `/validate-plugin --all` passes (reference inventory picks up 7 new files dynamically per 5.1)
- [ ] All line budgets met or documented-dense
- [ ] Spot execution check: one conversion via bpmn-to-drawio instructions reads coherently

### Phase 5 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| Budgets | `wc -l` on the six refactored files vs targets in item descriptions | All ≤ target |
| Official strict | `claude plugin validate --strict ./plugins/personal-plugin ./plugins/bpmn-plugin 2>/dev/null \|\| claude plugin validate --strict ./plugins/personal-plugin && claude plugin validate --strict ./plugins/bpmn-plugin` | Exit code 0 |

<!-- END DOD -->

---

## Phase 6: Skills-First Scaffolding

**Estimated Complexity:** M (~5 files, ~250 LOC)
**Dependencies:** None
**Execution Mode:** Parallel

### Goals

- Implement ADR-0006: new functionality ships as skills; commands are frozen legacy
- Port pattern-template support into new-skill; deprecate new-command; flip scaffold-plugin defaults

### Work Items

#### 6.1 new-skill pattern support
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R9, ADR-0006 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/commands/new-skill.md` (modify)

**Description:**
Add a pattern argument (e.g., `/new-skill my-skill --pattern generator`) that Reads the corresponding `references/templates/<pattern>.md` (the existing 8 command-pattern templates: conversion, generator, interactive, planning, read-only, synthesis, utility, workflow) and adapts it to SKILL form at generation time: nested `skills/<name>/SKILL.md`, `name:` frontmatter added, command-only guidance dropped. Templates themselves are NOT rewritten — the adapter lives in new-skill's instructions. Document the pattern list in the command's help.

**Tasks:**
1. [ ] Add pattern argument + adaptation instructions (frontmatter transform, nesting, name rule)
2. [ ] Document the 8 patterns with one-line descriptions
3. [ ] Update argument-hint

**Acceptance Criteria:**
- [ ] WHEN `/new-skill foo --pattern generator` runs THEN it SHALL scaffold `skills/foo/SKILL.md` derived from templates/generator.md with skill-conformant frontmatter
- [ ] WHEN no pattern is given THEN behavior SHALL be unchanged from today

---

#### 6.2 Deprecate new-command
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R9, ADR-0006 (E008/E009)
**Depends On:** 6.1
**Files Affected:**
- `plugins/personal-plugin/commands/new-command.md` (move → `plugins/personal-plugin/deprecated/new-command.md`)
- `plugins/personal-plugin/deprecated/README.md` (modify — add entry)
- `README.md` (modify — command table)

**Description:**
Move new-command.md to `deprecated/` per house convention (convert-hooks/setup-statusline/check-updates precedent), with a deprecation header pointing to `/new-skill --pattern`. Add the deprecated/README.md entry (date, reason: official skills-first direction + ADR-0006, replacement). Update the root README command table (remove new-command from active list; note in a deprecation line) and the command count.

**Tasks:**
1. [ ] Move file + add deprecation header
2. [ ] deprecated/README.md entry
3. [ ] Root README table + count update

**Acceptance Criteria:**
- [ ] WHEN personal-plugin loads THEN `/new-command` SHALL no longer register (file outside commands/)
- [ ] deprecated/README.md documents date, rationale (ADR-0006), and replacement
- [ ] README active-command table has 23 commands and no new-command row

---

#### 6.3 scaffold-plugin skills-first defaults
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R9, ADR-0006 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify — lines 103, 123, 141, 176–188, 229, 238–239, 257, 273, 320, 342)

**Description:**
Flip generation defaults: `skills/` scaffolded by default; `commands/` only on explicit request with a "legacy format" note. "Next Steps" leads with `/new-skill` (the 238–239 and 257 mentions of `/new-command` change to `/new-skill`). The skill quick-ref (176–188) becomes the primary authoring guidance.

**Tasks:**
1. [ ] Update the 7 default-generation sites + directory-layout examples
2. [ ] Rewrite Next Steps ordering + replace /new-command mentions

**Acceptance Criteria:**
- [ ] WHEN `/scaffold-plugin` runs with no format flags THEN the generated plugin SHALL contain `skills/` (no `commands/` dir)
- [ ] WHEN the user explicitly requests commands THEN scaffold SHALL generate them with a legacy-format note

---

### Phase 6 Testing Requirements

- [ ] `/validate-plugin personal-plugin` passes with new-command in deprecated/ (count checks use dynamic `[N]`)
- [ ] new-skill pattern flow produces a skill passing frontmatter validation

### Phase 6 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| Deprecation | `test ! -f plugins/personal-plugin/commands/new-command.md && test -f plugins/personal-plugin/deprecated/new-command.md` | Exit code 0 |

<!-- END DOD -->

---

## Phase 7: Guidance, CI & Evals

**Estimated Complexity:** M (~3 files, ~200 LOC)
**Dependencies:** Phases 3, 6
**Execution Mode:** Parallel

### Goals

- Official `claude plugin validate` in CI (strict for plugins, non-strict for marketplace manifest)
- Trigger evals guarding description behavior before Phase 8 edits descriptions
- CLAUDE.md refreshed to current spec + skills-first policy

### Work Items

#### 7.1 CI plugin-validate job
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R8 (E008/E009; approved default: marketplace non-strict)
**Files Affected:**
- `.github/workflows/validate.yml` (modify — new job)

**Description:**
Add a `plugin-validate` job on ubuntu-latest: `actions/setup-node@v4` (node 20, per the existing lint-markdown pattern), `npm install -g @anthropic-ai/claude-code@<pinned current version>`, then `claude plugin validate --strict` for each of the three plugin dirs and plain `claude plugin validate .` for the marketplace manifest (its `metadata.*version` fields are house bookkeeping the runtime ignores — approved default keeps them). No auth secrets — the validate subcommand is auth-free (verified locally on 2.1.204). Run the exact commands locally before pushing; the only current strict failure (agents) is fixed by Phase 3.

**Tasks:**
1. [ ] Author the job with pinned CLI version
2. [ ] Local dry-run of all four commands; confirm green post-Phase-3
3. [ ] Push and confirm the job passes in Actions

**Acceptance Criteria:**
- [ ] WHEN any PR introduces a loader-schema violation (missing frontmatter, bad manifest key) THEN CI SHALL fail on the plugin-validate job
- [ ] Marketplace-manifest validation passes non-strict with the version fields retained

---

#### 7.2 Trigger evals
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R8 (E008/E009)
**Files Affected:**
- `evals/skills/description-triggers.eval.md` (create)

**Description:**
Author should-trigger/should-not-trigger scenarios in the plan-gate.eval.md idiom (frontmatter `command/type/fixtures`; scenarios with `**Context:**` + Must / Must NOT checklists): positive trigger phrases for the big-5 (bpmn-generator, explain-project, bpmn-to-drawio, spec-to-prototype, accessibility-annotator) including near-miss negatives between overlapping pairs (explain-project vs accessibility-annotator vs convert-markdown); Must-NOT-auto-invoke scenarios for the four locked skills (brain-entry, unlock, lab-notebook, create-wiki).

**Tasks:**
1. [ ] Author ~12–16 scenarios covering the two groups
2. [ ] Reference from evals/README.md index if one exists

**Acceptance Criteria:**
- [ ] Each big-5 skill has ≥1 should-trigger and ≥1 near-miss should-not scenario
- [ ] Each locked skill has a Must NOT auto-invoke scenario
- [ ] File follows the existing eval frontmatter/checklist format

---

#### 7.3 CLAUDE.md guidance refresh
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R12, R9 (E008/E009; ADR-0006)
**Files Affected:**
- `CLAUDE.md` (modify)

**Description:**
Update Verified Operational Rules: correct the skill-`name` rule to note the 2026 spec makes it optional (kept as house convention — D2 rationale update); add the skills-first policy line (new functionality ships as skills; commands legacy-frozen; cite ADR-0006); note new frontmatter fields (`when_to_use`, `arguments`, `user-invocable`, `disallowed-tools`, `shell`, scoped `hooks`) and description budgets (≤1024 chars; 1536 combined truncation; SKILL.md <500 lines); note hook fields (`once`, `if`, `statusMessage`). Update the repository-structure section (new-command → deprecated; new references files from Phases 4–5) and the command count. Keep edits surgical — CLAUDE.md is loaded every session.

**Tasks:**
1. [ ] Verified Operational Rules updates (name nuance, skills-first, budgets)
2. [ ] Structure/counts refresh
3. [ ] Cross-check no rule contradicts the validator or template post-Phases-1–6

**Acceptance Criteria:**
- [ ] WHEN a future session reads CLAUDE.md THEN every stated rule SHALL match the current official spec and the repo's actual state
- [ ] No net growth >40 lines (session-context cost discipline)

---

### Phase 7 Testing Requirements

- [ ] CI green on a branch push including the new job
- [ ] Eval file passes markdownlint and matches house eval format

### Phase 7 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| Official validate (all) | `claude plugin validate --strict ./plugins/personal-plugin && claude plugin validate --strict ./plugins/bpmn-plugin && claude plugin validate --strict ./plugins/slide-gen && claude plugin validate .` | Exit code 0 |

<!-- END DOD -->

---

## Phase 8: Descriptions, Polish & Release

**Estimated Complexity:** M (~30 files, ~400 LOC — wide-shallow: 1–5 line edits per file)
**Dependencies:** Phases 1–7
**Execution Mode:** Parallel

### Goals

- Descriptions on the official formula (negative scope; all trigger info in frontmatter)
- Close the small-gaps list (effort, argument-hint, hooks, per-plugin README/LICENSE)
- Coordinated version bump and CHANGELOG release

### Work Items

#### 8.1 Big-5 negative scope
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R10 (E008/E009)
**Files Affected:**
- `plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md`, `bpmn-to-drawio/SKILL.md` (modify — description only)
- `plugins/personal-plugin/skills/explain-project/SKILL.md`, `spec-to-prototype/SKILL.md`, `accessibility-annotator/SKILL.md` (modify — description only)

**Description:**
Add explicit negative scope ("Do NOT use for…") to the five longest, most overlap-prone descriptions, following the official document-skills formula. Disambiguate the known overlap triangle: explain-project (full annotated overview doc) vs accessibility-annotator (annotate an EXISTING document) vs convert-markdown (format conversion only); bpmn-generator (create XML) vs bpmn-to-drawio (convert existing XML). Keep each description ≤1024 chars.

**Tasks:**
1. [ ] Author negative-scope clauses ×5 with pairwise disambiguation
2. [ ] Verify against 7.2's near-miss eval scenarios

**Acceptance Criteria:**
- [ ] All five descriptions contain a "Do NOT use for" clause naming their nearest-neighbor skill
- [ ] Each ≤1024 chars; trigger-eval scenarios from 7.2 read consistently with the new text

---

#### 8.2 Fold Proactive Triggers — personal-plugin skills
**Status: PENDING**
**Model Tier: haiku**
**Requirement Refs:** R10 (E008/E009)
**Files Affected:**
- 12 personal-plugin skills with body "Proactive Triggers" sections: plan-gate, brain-entry, summarize-feedback, lab-notebook, unlock, create-wiki, release-plugin, visual-explainer, security-analysis, research-topic, prime, evaluate-pipeline-output (modify)

**Description:**
Per official guidance, all when-to-use information belongs in the description (or `when_to_use`), not the body. For each file: merge the body "Proactive Triggers" bullets into the frontmatter description (append a compact "Suggest when…" clause) or a `when_to_use:` field where the description would exceed ~600 chars, then delete the body section. For the four locked skills (brain-entry, unlock, lab-notebook, create-wiki), phrase as "Suggest (do not auto-run) when…" consistent with disable-model-invocation.

**Tasks:**
1. [ ] Apply the fold to all 12 files (2–6 line edit each)
2. [ ] Confirm combined description+when_to_use ≤1536 chars everywhere

**Acceptance Criteria:**
- [ ] `grep -rln 'Proactive Triggers' plugins/personal-plugin/skills/` returns nothing
- [ ] Every touched skill passes frontmatter validation; no combined-text truncation

**Notes:**
Wide-shallow: 12 files exceeds the per-item file guideline but each edit is a mechanical 2–6 line move; splitting further would add coordination cost with no risk reduction. ship was handled in 5.3.

---

#### 8.3 Fold Proactive Triggers — slide-gen + cost rewrite
**Status: PENDING**
**Model Tier: haiku**
**Requirement Refs:** R10, R13 (E008/E009)
**Files Affected:**
- 9 slide-gen skills: sg-research, sg-outline, sg-draft, sg-optimize, sg-validate-graphics, sg-generate-images, sg-build, sg-full-workflow, build-cfa-deck (modify)

**Description:**
Same Proactive-Triggers fold for the nine slide-gen skills. Additionally in sg-full-workflow: replace the hardcoded dollar Cost Estimate section (136–142) with qualitative guidance ("image generation dominates cost; `--skip-images` eliminates most of it") — no dated absolutes.

**Tasks:**
1. [ ] Fold ×9
2. [ ] Cost-section rewrite in sg-full-workflow

**Acceptance Criteria:**
- [ ] `grep -rln 'Proactive Triggers' plugins/slide-gen/` returns nothing
- [ ] sg-full-workflow contains no absolute dollar figures

**Notes:**
Wide-shallow justification as 8.2.

---

#### 8.4 Mechanical polish: effort, argument-hint, hooks
**Status: PENDING**
**Model Tier: haiku**
**Requirement Refs:** R13 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/commands/plan-next.md` (modify — add argument-hint)
- ~8 command files gaining `effort:` (modify)
- `plugins/personal-plugin/hooks/hooks.json` (modify — statusMessage ×2)

**Description:**
plan-next gets `argument-hint: "[focus-area]"` (the only command lacking one). Add `effort:` to the clearest command outliers only — heavy analyzers to `high` (assess-document, consolidate-documents, analyze-transcript, validate-plugin, test-project), mechanical ones to `low` (bump-version, convert-markdown, define-questions) — commands only, so no file overlap with 8.2/8.3. Add `statusMessage` to both hooks.json entries ("Checking for in-progress implementation plan…", "Lab-notebook gate: verifying entry before commit…").

**Tasks:**
1. [ ] argument-hint + 8 effort additions
2. [ ] hooks.json statusMessage fields

**Acceptance Criteria:**
- [ ] All 24→23 active commands have argument-hint
- [ ] hooks.json remains valid record-format JSON and both hooks fire with visible status text

---

#### 8.5 Per-plugin README + LICENSE
**Status: PENDING**
**Model Tier: haiku**
**Requirement Refs:** R13 (E008/E009)
**Files Affected:**
- `plugins/personal-plugin/README.md`, `plugins/bpmn-plugin/README.md`, `plugins/slide-gen/README.md` (create)
- `plugins/personal-plugin/LICENSE`, `plugins/bpmn-plugin/LICENSE`, `plugins/slide-gen/LICENSE` (create)

**Description:**
Official convention: every plugin ships README + LICENSE at plugin root. READMEs are brief (purpose, install line, command/skill inventory pointer to root README, version); LICENSE = MIT copy matching root.

**Tasks:**
1. [ ] Three READMEs (~30 lines each)
2. [ ] Three MIT LICENSE copies

**Acceptance Criteria:**
- [ ] `ls plugins/*/README.md plugins/*/LICENSE` lists all six files

---

#### 8.6 Coordinated release
**Status: PENDING**
**Model Tier: sonnet**
**Requirement Refs:** R13, all (E008/E009; approved bumps)
**Depends On:** 8.1, 8.2, 8.3, 8.4, 8.5
**Files Affected:**
- `plugins/personal-plugin/.claude-plugin/plugin.json` (modify — 9.3.0 → 10.0.0)
- `plugins/bpmn-plugin/.claude-plugin/plugin.json` (modify — 4.1.0 → 4.2.0)
- `plugins/slide-gen/.claude-plugin/plugin.json` (modify — 1.1.0 → 1.2.0)
- `.claude-plugin/marketplace.json` (modify — marketplace_version 3.3.0 + three plugin entries)
- `CHANGELOG.md`, `plugins/personal-plugin/CHANGELOG.md` (modify)

**Description:**
Approved bumps: personal-plugin **10.0.0** (major — new-command deprecation, per v5.x/v8.0.0 precedent), bpmn-plugin 4.2.0, slide-gen 1.2.0, marketplace 3.3.0 (repo-wide CI/docs changes). Write the root CHANGELOG entry covering all phases (Added: agent frontmatter/aliases, references, CI job, evals, pattern scaffolding, READMEs; Changed: consolidations/refactors/descriptions; Fixed: dangling refs, paths, CRLF, model plumbing; Deprecated: new-command) and mirror the personal-plugin-specific portion to its plugin CHANGELOG. Final sweep: full DoD suite + `/validate-plugin --all`.

**Tasks:**
1. [ ] Version fields ×4 files (plugin.json ×3 + marketplace.json entries + marketplace_version)
2. [ ] CHANGELOG entries (root + personal-plugin)
3. [ ] Full verification sweep

**Acceptance Criteria:**
- [ ] validate.yml version-sync check passes (plugin.json ↔ marketplace.json agree everywhere)
- [ ] WHEN the release commit lands on main THEN the installed-cache auto-update SHALL deliver 10.0.0/4.2.0/1.2.0 (verify post-merge per D19)
- [ ] Root CHANGELOG names every user-visible change with its R# origin

---

### Phase 8 Testing Requirements

- [ ] Full DoD suite green
- [ ] `/validate-plugin --all` passes end-to-end

### Phase 8 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `python -m pytest tests/ -v` | Exit code 0 |
| Lint | `ruff check .` | Exit code 0 |
| Markdown | `npx markdownlint-cli "**/*.md" --ignore node_modules` | Exit code 0 |
| Official validate (all) | `claude plugin validate --strict ./plugins/personal-plugin && claude plugin validate --strict ./plugins/bpmn-plugin && claude plugin validate --strict ./plugins/slide-gen && claude plugin validate .` | Exit code 0 |
| Version sync | Compare `version` in each plugin.json to its marketplace.json entry | All equal |
| Triggers folded | `! grep -rln 'Proactive Triggers' plugins/` | No matches |

<!-- END DOD -->

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phases 1, 2, 3, 6 | Each other | No shared files; no incoming dependencies — all four can start immediately |
| 1.1–1.5 | Each other | File-disjoint (verified in interaction mapping) |
| 2.1–2.4 | Each other | File-disjoint; 2.4 is an isolated Python tool |
| 3.1, 3.2 | Each other | Plugin agents vs repo agents |
| 3.3, 3.4 | Each other | After 3.1; skill vs commands |
| 4.2, 4.3, 4.4 | Each other | After 4.1; three distinct command files |
| 5.1–5.5 | Each other | File-disjoint including their new reference files |
| 6.1, 6.3 | Each other | 6.2 waits on 6.1 |
| 7.1–7.3 | Each other | Workflow vs eval vs CLAUDE.md |
| 8.1–8.5 | Each other | 8.2/8.3 are skills-only, 8.4 commands-only — no overlap; 8.6 last |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy | Status |
|------|------------|--------|---------------------|--------|
| implement-plan PATH A/B collapse regresses execution semantics | Med | High | E009 difference ledger is the authoritative spec; side-by-side semantic checklist in 4.4 acceptance; opus tier; per-phase commit enables `git revert` | Mitigated |
| arch-review pipeline breaks under new dispatch/meta design | Med | Med | 3.5 smoke test gates phase completion; per-agent meta is strictly simpler than shared-merge; revert path is one commit | Mitigated |
| `claude plugin validate --strict` flags unforeseen issues in CI | Med | Low | Full local dry-run in 7.1 before push; pinned CLI version; only known failure (agents) already fixed by Phase 3 | Open |
| Description edits shift auto-trigger behavior | Low | Med | 7.2 trigger evals land before Phase 8 description edits; near-miss scenarios encode current intended boundaries | Open |
| Renormalization churn or binary corruption | Low | Med | Blast radius pre-verified (2 CRLF text files, 1 zip); explicit `*.zip binary` rule; `git status` check in 2.3 | Mitigated |
| new-skill pattern adapter produces malformed skills | Low | Med | Templates untouched (adapter-only); generated output must pass frontmatter validation per 6.1 acceptance | Open |
| validate-plugin refactor silently weakens a check | Low | High | 5.1 rule: checks move verbatim, only illustrations extracted; post-refactor `/validate-plugin --all` compared against pre-refactor output | Open |

---

## Unknowns Register

| ID | Unknown | Severity | Affects | Resolution Strategy | Status |
|----|---------|----------|---------|---------------------|--------|
| U1 | Whether worktree-isolated subagents return written files to the main tree (motivated dropping worktree isolation) | Med | Phase 3, Item 3.5 | Smoke dispatch verifies findings land in main tree under the new no-worktree design — RESOLVED: no-worktree design confirmed; dispatched agent file-writes land in the main tree | Resolved [2026-07-08] |
| U2 | Whether dispatch requires namespaced (`personal-plugin:x`) or bare (`x`) subagent_type | Low | Phase 3, Items 3.3–3.5 | 3.5 tests both forms; dispatch table updated to whichever resolves — RESOLVED: namespaced `personal-plugin:<agent>` form resolves correctly (smoke-tested) | Resolved [2026-07-08] |
| U3 | Current OpenAI/Google deep-research model IDs (unverifiable offline) | Low | Phase 1, Item 1.5 | Keep the skill's runtime model-check step authoritative; stamp verified-date on Anthropic ID only | Open |
| U4 | `~/dev/info/technical-document-structure-template.md` missing on the Linux VM (sync gap) | Low | Phase 2, Item 2.2 | Fallback instruction added in 2.2; user syncs the file from Windows or accepts the fallback | Open |

---

## Success Metrics

- [ ] All phases completed
- [ ] All acceptance criteria met
- [ ] `claude plugin validate --strict` passes all three plugins; marketplace manifest validates
- [ ] Zero references to nonexistent commands anywhere in active plugin content
- [ ] Zero stale model pins: agent definitions on aliases; Python tools env-overridable at current defaults
- [ ] All 13 previously-oversized files at/under target or documented-dense; ~10 new reference files carry the extracted bulk
- [ ] 8 side-effect/user-only skills carry `disable-model-invocation` (4 pre-existing + 4 new)
- [ ] CI includes official plugin validation; trigger evals guard description behavior
- [ ] personal-plugin 10.0.0 / bpmn-plugin 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0 released with synced manifests and CHANGELOGs

---

## Appendix: Requirement Traceability

| Requirement | Source | Phase | Work Item |
|-------------|--------|-------|-----------|
| R1 Agent frontmatter restoration | E008/E009 §R1 | 3 | 3.1, 3.3, 3.4, 3.5 |
| R2 Stale model pins → aliases/current | E008/E009 §R2 | 1, 2, 3 | 1.2 (co-author), 1.5, 2.4, 3.2 |
| R3 Dangling refs & self-drift bugs | E008/E009 §R3 | 1 | 1.1, 1.2, 1.3, 1.4, 1.5 |
| R4 Dual-environment portability | E008/E009 §R4 | 2 | 2.2, 2.3 |
| R5 Side-effect skill lockdown | E008/E009 §R5 | 2 | 2.1 |
| R6 Progressive-disclosure refactor | E008/E009 §R6 | 4, 5 | 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5 |
| R7 Planning-family single-sourcing | E008/E009 §R7 | 4 | 4.1, 4.2, 4.3 |
| R8 Official validation + trigger evals | E008/E009 §R8 | 7 | 7.1, 7.2 |
| R9 Skills-first policy (ADR-0006) | E008/E009 §R9 | 6, 7 | 6.1, 6.2, 6.3, 7.3 |
| R10 Description/trigger optimization | E008/E009 §R10 | 5, 8 | 5.3, 8.1, 8.2, 8.3 |
| R11 Harness-alignment mechanics | E008/E009 §R11 | 3, 4 | 3.3, 3.4, 4.4 |
| R12 House-rules refresh | E008/E009 §R12 | 7 | 7.3 |
| R13 Polish grab-bag | E008/E009 §R13 | 8 | 8.3 (cost), 8.4, 8.5, 8.6 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-07-08 14:59:15*
*Source: /create-plan command*
