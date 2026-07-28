# Opus 5 / Sonnet 5 Optimization Audit — Full Report

**Date:** 2026-07-28
**Scope:** Entire marketplace at main `795f92f` — personal-plugin 11.3.0, bpmn-plugin 4.3.1, slide-gen 1.2.0, marketplace 3.3.0
**Target posture:** Claude **Opus 5** (`claude-opus-5`) as primary execution model, **Sonnet 5** (`claude-sonnet-5`) as secondary, Haiku 4.5 unchanged as the small/fast tier. Tier aliases `haiku`/`sonnet`/`opus`/`fable`/`inherit` resolve at dispatch (ADR-0005).
**Method:** Six parallel read-only review subagents, one rubric (stale model refs · ADR-0005 compliance · effort calibration · prompt-style anachronisms · harness currency · triggering metadata · context economy · tier-routing logic), covering: 23 commands (+4 deprecated), 29 personal-plugin skills, 2 bpmn skills, 9 slide-gen skills, 13 agent definitions, ~50 reference/template/pattern files, 3 Python tools, hooks, evals, CI, schemas, and 8 top-level docs (~150 files). Findings are file:line-anchored; per-component detail is in Sections A–F below.

---

## Executive summary

**The marketplace is in unusually good shape for a model transition — the ADR-0005 alias discipline worked.** All 13 agent definitions (`haiku/sonnet/opus-implementer` + the 10 arch-review architects) carry clean tier-alias or `inherit` frontmatter, so `/implement-plan` and `/arch-review` pick up Opus 5 and Sonnet 5 automatically with **zero changes**. 28 of 29 personal-plugin skills and all 11 bpmn/slide-gen skills contain no Claude model reference of any vintage. The evals suite is model-agnostic by design. CI and schemas carry no model pins.

The work that *is* needed falls into three tiers:

1. **Functional breaks that exist today, independent of any model change (P0).** The most serious: the research pipeline's Claude leg sends `thinking: {type: "enabled", budget_tokens: N}`, which returns **HTTP 400 on the entire current model family** (Opus 4.8 and Opus 5 alike) — every `/research-topic` Claude dispatch fails right now. Plus: 20 unguarded `` !`git …` `` parse-time injections across 5 skills (confirmed issue #183 — they abort the skill in non-git dirs), `ship`'s diff-size gate computing the literal string `deletions(-)` instead of a number (its >500-line safety gate can never fire), `prime` mandating fork dispatch its `allowed-tools` doesn't grant, `bpmn-to-drawio`'s SKILL re-teaching the partial-DI bug (#143) its own bundled tool fixed in v4.3.x, and all three hook recipe docs shipping a JSON shape that silently fails to load.

2. **Stale model references, ranked by propagation risk (P1).** Only ~10 files carry stale Claude IDs, but four of them are *generators/templates* whose content is copied into every future skill: `references/templates/skill.md` (`claude-opus-4`), `references/common-patterns.md` (`claude-opus-4-5`, retired `claude-haiku-3-5`), `references/patterns/advanced-features.md` (`claude-opus-4`, never-existed `claude-haiku-4`), and `commands/new-skill.md` (3 occurrences). The one behavior-affecting runtime default: `research-topic`/`research-models.md`/`api-key-setup.md` pin `claude-opus-4-8` → drop-in upgrade to `claude-opus-5`.

3. **Recalibration for the stronger model pair (P2–P5).** Sonnet 5's step-change moves the sonnet/opus routing boundary up (one coordinated edit across exactly 3 files); a `fable`-tier policy needs one deliberate sentence; `ultra-plan` — the deepest-reasoning skill — has **no effort field** and relies on a dead `ultrathink` keyword; ~15 skills lack `effort:` entirely; hard-coded 200K-era token budgets force needless chunking under 1M-context primaries; and a systematic contradiction (11 skills carry "Suggest when…" trigger prose inside descriptions that `disable-model-invocation: true` deletes from context) makes that trigger metadata dead weight for Sonnet 5's dispatcher.

**Verdict roll-up: 22 components NEEDS-CHANGE, ~44 MINOR, ~85 OK. Findings: 21 High, ~92 Medium, ~142 Low.**

| Section | Scope | NEEDS-CHANGE | High | Med | Low |
|---|---|---|---|---|---|
| A | 23 commands + deprecated | 3 (create-plan, new-skill, plan-improvements) | 3 | 18 | 31 |
| B | 13 skills A–L | 3 (clear-prep, explain-project, leak-risk-audit) | 3 | 12 | 23 |
| C | 16 skills M–Z | 6 (prime, research-topic, ship, spark-audit, spark-recon, ultra-plan) | 6 | 23 | 39 |
| D | bpmn-plugin + slide-gen | 3 (bpmn-generator, bpmn-to-drawio, build-cfa-deck) | 1 | ~14 | ~15 |
| E | agents + references + hooks | 6 (research-models, research-provider-protocols, common-patterns, advanced-features, templates/skill.md, hooks recipes) | 7 | 19 | 25 |
| F | tools, evals, CI, schemas, docs | 1 (api-key-setup.md) | 1 | 6 | 9 |
| **Total** | ~150 files | **22** | **21** | **~92** | **~142** |

---

## Prioritized change plan

### P0 — Functional breaks (fix first; broken today regardless of model)

| # | Fix | Where |
|---|---|---|
| P0.1 | **Research pipeline 400s**: replace `thinking.budget_tokens` depth mapping with adaptive thinking + `output_config.effort`; bump default `claude-opus-4-8` → `claude-opus-5` in the same pass | `references/research-provider-protocols.md:27-29`, `references/research-models.md:48-53,19,33,64`, `skills/research-topic/SKILL.md:35,153,190-196,219,238`, `references/api-key-setup.md:36` |
| P0.2 | **Issue #183 — guard or delete all 20 unguarded `` !`git …` `` injections**: prime (7), ship (6), clear-prep (3), explain-project (2, which also inject the *wrong repo's* history in GitHub-URL mode), leak-risk-audit (2, with impossible parse-time `<dataset-path>` placeholders) | `skills/prime/SKILL.md:60-68`, `skills/ship/SKILL.md:15-30`, `skills/clear-prep/SKILL.md:27-29`, `skills/explain-project/SKILL.md:142-143`, `skills/leak-risk-audit/SKILL.md:56-57` |
| P0.3 | **Correct the #183 root-cause doc**: `advanced-features.md:132`'s "failure is silent" claim is wrong — injection failure aborts the skill; keep the `\|\| echo` fix, fix the failure-mode description | `references/patterns/advanced-features.md:132` |
| P0.4 | **ship diff-size gate**: `git diff --stat \| tail -1 \| awk '{print $NF}'` yields `deletions(-)`, never a number — the >500-line gate never fires → `git diff --shortstat`-based arithmetic | `skills/ship/SKILL.md:30,80,275` |
| P0.5 | **prime can't do what it says**: body mandates `context: fork` + `agent: Explore` dispatch but `allowed-tools` grants no dispatch tool → add it; run Phases 1/3/5 in parallel | `skills/prime/SKILL.md:5,26,44,86,148` |
| P0.6 | **bpmn-to-drawio layout guidance re-teaches fixed bug #143**: rewrite Steps 4/5 around the tool's v4.3.x `--layout auto` default; update the CLI reference table and tool README to match | `skills/bpmn-to-drawio/SKILL.md:93-148`, `references/bpmn2drawio-reference.md:30`, `tools/bpmn2drawio/README.md:47-66` |
| P0.7 | **Hook recipes silently fail to load**: rewrite all 3 snippets in the nested matcher/hooks format the live `hooks/hooks.json` uses; fix seconds-vs-ms timeout and env-var-vs-stdin parsing | `references/hooks/*.md` (3 files) |
| P0.8 | **allowed-tools mismatches** (documented flow hits denials): explain-project missing `Write`; accessibility-annotator missing `Glob`/`Grep`; ship `--audit` missing `Write`; test-project grants stale `Task` but prose says Agent tool; create-plan's `find` outside its grants; brain-entry/fleet-health compound commands outside their Bash scopes; spark-recon grants `Bash(ssh:*)` its own trust boundary forbids | per-component detail, Sections A–C |
| P0.9 | **build-cfa-deck dead snippet**: `import os` after use guarantees NameError so the worse fallback always runs; also delete the superseded duplicate slide-removal snippet | `skills/build-cfa-deck/SKILL.md:72-79,187-203,253-269` |
| P0.10 | **visual-explainer documents the wrong env var**: `$GOOGLE_IMAGE_MODEL` → actual `VISUAL_EXPLAINER_GEMINI_MODEL`; also document `VISUAL_EXPLAINER_CLAUDE_MODEL` | `skills/visual-explainer/SKILL.md:40,116` |

### P1 — Stale model references (ranked by propagation)

1. **Templates/generators first** (each copy multiplies): `references/templates/skill.md:12` (`claude-opus-4` → `opus` + ADR-0005 note), `references/common-patterns.md:164` (`claude-opus-4-5`/`claude-sonnet-4-5`/retired `claude-haiku-3-5` → tier aliases) and :169-170 (state the alias rule directly), `references/patterns/advanced-features.md:51,57-58` (`claude-opus-4`, never-existed `claude-haiku-4` → `opus`/`haiku`, add `fable`), `commands/new-skill.md:169,198,294` (3× pinned IDs → aliases; drop the "as of late 2025" stamp at :282), `deprecated/new-command.md:193` (fix or add a stale-examples banner to deprecated/README.md).
2. **Runtime defaults**: research stack `claude-opus-4-8` → `claude-opus-5` (P0.1 covers it); re-verify the two third-party research defaults (`o3-deep-research-2025-06-26`, `deep-research-pro-preview-12-2025`).
3. **Test straggler**: `tools/visual-explainer/tests/test_prompt_generator.py:57` retired `claude-opus-4-20250514` → `claude-opus-5`.
4. **Prose/docs**: `CONTRIBUTING.md:389` co-author template "Claude Opus 4.5" → current/generic; `README.md:179-180` "Model pinned in frontmatter" contradicts ADR-0005 → reword; sg-* skill docs strip engine internals (`budget_tokens=4096`, "temperature=1.0 required", batch sizes, assistant-prefill) down to intent-level descriptions; verify/genericize `gemini-3-pro-image-preview` in sg-generate-images:56, accessibility-annotator:321, and visual-explainer config; `image_evaluator.py:36` "5x cheaper than Opus" comment → current ~1.7x ratio; ask-questions.md:357 "GPT-4/Whisper" example → genericize; develop-image-prompt DALL-E-3/SD1.x parameter blocks → refresh or genericize.

### P2 — Tier-routing recalibration (one coordinated edit)

- **Move the sonnet/opus boundary up in exactly 3 synchronized places**: `sonnet-implementer.md` (widen profile: multi-file changes with clear specs, diagnosed bug fixes, described-API features; escalate only on unresolved architecture/genuine ambiguity), `opus-implementer.md` (reserve for ambiguity, competing designs, cross-cutting debugging), `references/plan-template.md` Rule 17 (multi-file refactors move from categorically-opus to sonnet-when-specified).
- **Make the `fable` policy explicit** (one sentence each): `opus-implementer.md` ("no escalation above Opus" now reads as staleness — document fable's deliberate exclusion on cost, or allow one opus→fable escalation on explicit user request), `implement-plan.md:232` (same ceiling), `plan-template.md:253`.
- **Opus 5 behavioral calibration in opus-implementer**: add scope-discipline ("deliver at the intended scope; don't widen") and leaf-implementer ("do not sub-delegate to subagents") lines.
- **Reword the "run the orchestrator on Opus" advisories** — now satisfied by session defaults: `implement-plan.md:41`, `create-plan.md:310`, `plan-improvements.md:350`.
- **visual-explainer knob split**: `config.py` single `claude_model` feeds analysis + generation + evaluation → split into `claude_model` (default `claude-opus-5`: one-shot, quality-driving) and `claude_eval_model` (default `claude-sonnet-5`: high-volume vision loop), each env-overridable; auth ping (`api_setup.py:229`) → `claude-haiku-4-5`.
- `common-patterns.md:167`: add "sonnet is the default workhorse" to the haiku-triage/opus-synthesis guidance.

### P3 — Effort calibration

- **Fix the inversion**: `ultra-plan` (deepest-reasoning skill) has no `effort:` and opens with a dead `ultrathink` keyword → delete keyword, add `effort: max` (or high). Same anachronism in `references/templates/planning.md:66-68` and `plan-improvements.md:34,36` ("Ultrathink"/"extended thinking enabled").
- **A/B the two `effort: max` planners** (`create-plan`, `plan-improvements`) against `high` on Opus 5 — overthinking/latency risk; keep max only if measurably better.
- **Add missing `effort:`** (~15 files): high — clean-repo, remove-ip, bpmn-generator; medium — develop-image-prompt, release-plugin, ship, jetson-audit, jetson-recon, wiki (optional), sg-full-workflow; low — fleet-health, archive-project, new-project, unlock, bpmn-to-drawio, and all 8 sg-* wrappers.
- **Consider downgrades on mechanical work**: validate-plugin high→medium, analyze-transcript high→medium, visual-explainer high→medium, arch-synthesize low→medium (upgrade — cross-domain conflict resolution is judgment work).

### P4 — 200K-era context assumptions → context-relative

Hard token thresholds sized for 200K windows force needless chunking/sampling under 1M-context primaries: `analyze-transcript.md:96-102` (30K/50K/20K), `assess-document.md:72` (~100K), `plan-improvements.md:53,414-421` (absolute token budget table), `summarize-feedback/SKILL.md:90-110` (100-entry/25-batch guardrail). Re-express all as fractions of available context — `consolidate-documents.md` ("~60% of available context") is the in-repo exemplar.

### P5 — Dispatch metadata & harness currency

- **Resolve the `disable-model-invocation` vs "Suggest when…" contradiction in 11 skills** (archive-project, brain-entry, create-wiki, lab-notebook, jetson-recon, new-project, release-plugin, ship, unlock, visual-explainer, spark-recon): the flag deletes the description that carries the triggers, so the metadata is dead. Per-skill decision: drop the flag (brain-entry, create-wiki, lab-notebook, clear-prep-style suggestible skills — and arguably ship) or keep it and strip the trigger prose (expensive/costly-side-effect skills). arch-review shows the correct flag usage to copy.
- **Fix new-skill's description guidance**: "≤150 chars ideal" contradicts the house ≤1024-with-all-trigger-info rule — undersized descriptions actively harm Sonnet 5 dispatch of generated skills (`new-skill.md:98,287`).
- **Adopt AskUserQuestion** where hand-rolled text menus predate it: ask-questions.md:134-149 (and finish-document by reference), bpmn-generator:104-227 (simulated REPL), spec-to-prototype:30,62 (one-at-a-time), visual-explainer:233-282 (numbered menus). Keep text protocols as fallback.
- **Verify-or-prune unverified frontmatter/features** (E043 doctrine — a guard that can't fire is worse than none): `paths:`, `hooks: pre/post`, `isolation: worktree` (as skill frontmatter), `agent: Think|Code`, `$CLAUDE_CONTEXT`, `$CLAUDE_TOOL_NAME` — all documented in common-patterns/advanced-features/templates/skill.md/new-skill-examples but absent from CLAUDE.md's field list and uncorroborated; negative-test each against `claude plugin validate --strict` + a live probe, then prune or mark verified. Affects the paths-gated flows in security-analysis, spark-audit, spark-recon, jetson-audit.
- **Remove the fictional `/schedule` integration** in 4 skills (jetson-audit, jetson-recon, spark-audit, spark-recon) → current mechanisms (Routines/`create_trigger`, `/loop`).
- **Unify the dispatch-tool vocabulary** (`Task` vs `Agent` split across ~8 files; two generators disagree on agent names — new-skill says `Explore, Think, Code`, scaffold-plugin says `explorer`) after verifying the current harness names.
- **`${CLAUDE_PLUGIN_ROOT}`-relative paths** for cross-file references that break outside the repo clone: spark-audit:138, spark-recon:21-23, bpmn skills' `../references/` paths; move the shared audit/recon template out of spark-recon's SKILL into the shared reference both jetson/spark pairs load.
- **Missing/incomplete `argument-hint`** on ~8 components (lab-notebook, brain-entry, leak-risk-audit, accessibility-annotator, convert-markdown, validate-plugin, bpmn pair).

### P6 — Guards, evals, and doc sync

- **Enforce ADR-0005 in CI**: nothing today stops a pinned ID in agent frontmatter (README even claims models are "pinned"). Add a tier-alias allowlist check (`haiku|sonnet|opus|fable|inherit`) to BOTH `validate.yml` and `scripts/pre-commit`, negative-tested with a deliberately pinned ID before wiring (E043 rule). Optionally mirror as an agent-frontmatter schema enum.
- **Re-baseline model-sensitive evals** after the switch: run `evals/skills/description-triggers.eval.md` FIRST (trigger behavior is what shifts across generations); re-baseline `assess-document.eval.md`'s absolute score bands (3.5-4.5 / 2.0-3.0) or convert to its own relative criterion.
- **Doc sync**: CLAUDE.md skills inventory (+5 missing skills), bpmn README 4.2.0→4.3.1, slide-gen CHANGELOG "8 skills"→9, ADR-0008 one-sentence build-cfa-deck carve-out, lab-notebook-gate.sh misleading `--no-verify` bypass comment.

### Suggested shipping shape

Five PRs, in order: **(1)** P0 bundle (functional fixes — several close/relate to open issue #183), **(2)** P1 model-reference bundle, **(3)** P2+P3 tier/effort recalibration (the 3-file sync + fable policy + effort fields), **(4)** P5 metadata bundle (after the verify-or-prune probe results), **(5)** P6 CI guard + doc sync. Re-run the eval suite (description-triggers first) after PR 3. Each PR is a personal-plugin minor bump except (1), which is arguably a patch-level bugfix release; bpmn-plugin and slide-gen take one minor each.

### Verify-before-applying caveats

This is an audit, not a verified patch set. Before applying, confirm against the live harness/API: (a) current Opus 5/Sonnet 5 pricing used in the tiering rationale; (b) whether skill-frontmatter `effort` accepts levels beyond the documented low/medium/high/max; (c) the exact set of supported skill frontmatter keys (`paths:`/`hooks:`/`isolation:`/`agent:` values) — the P5 verify-or-prune step IS this confirmation; (d) current Gemini image-model IDs; (e) the `budget_tokens` 400 behavior on your API tier (verified against current API docs during this audit, but cheap to re-confirm with one curl before rewriting the protocol reference).

---

## What is already optimized (no action)

- **All 13 agent definitions** — tier-alias/`inherit` frontmatter throughout; `/implement-plan` and `/arch-review` inherit Opus 5/Sonnet 5 automatically (ADR-0005's structural elimination of pin-drift worked).
- **The implement-plan tier pipeline** (planner → Model Tier hints → dispatch → escalation) — alias-based end-to-end; its heavy proceduralism is a state machine, not micro-management, and its parallel/worktree/resume mechanics are current best practice.
- **28 of 29 personal-plugin skills and all 11 bpmn/slide-gen skills** — zero Claude model references of any vintage.
- **Evals** — model-agnostic by design; **CI/scripts/schemas** — no model pins; **hooks/hooks.json** — correct format the recipe docs should copy.
- **House exemplars worth propagating**: task-sync (design + calibration), plan-gate (`effort: low` exactly right), wiki, plan-next, bump-version, validate-plugin's reference extraction, consolidate-documents' context-relative budgeting, arch-review's #183 injection guard, the jetson/spark trust boundaries, create-wiki's reference-template indirection, leak-risk-audit's parent-writes/subagents-return-JSON concurrency discipline, sg-full-workflow's ADR-0008 preflight, fleet-health's trigger-rich description, build-cfa-deck's "content generation happens in this session" framing.

---

# Section A — personal-plugin commands


### analyze-transcript.md
**Verdict:** MINOR
- [Med] [hard-coded-sizes] analyze-transcript.md:96,100-102 — Chunking thresholds written for a 200K-context era: "Content exceeds 50K tokens → process in sections", "chunks (~20K tokens each)", two-pass pipeline triggered at 30K tokens → with 1M-context Opus 5/Sonnet 5 primaries, single-pass handles far larger transcripts; raise thresholds (e.g., trigger sectioning only above several hundred K tokens) or express as a fraction of available context.
- [Low] [effort] analyze-transcript.md:4 — `effort: high` for extraction/summarization work → `medium` is sufficient on the stronger primary; high buys little on structured extraction.
- [Good] Type-detection table, interview-record format, and error handling are data-driven and appropriately non-prescriptive; no model references.

### arch-review-single.md
**Verdict:** OK
- [Low] [metadata] arch-review-single.md:3 — `argument-hint: <agent-name> <path-to-target>` is the only unquoted argument-hint in the set → quote for consistency.
- [Good] Modern Agent-tool dispatch with namespaced `subagent_type` and graceful fallback; correct `effort: medium`; agent supplies its own system prompt (no duplication).

### arch-synthesize.md
**Verdict:** OK
- [Low] [effort] arch-synthesize.md:4 — `effort: low` but step 6 (cross-domain conflict detection/resolution with business-impact tiebreaking) is judgment work → consider `medium`; low risks shallow conflict resolution even on a strong model.
- [Good] Compact, judgment-trusting instructions ("Synthesize from what exists"); guarded shell commands (`2>/dev/null || echo`).

### ask-questions.md
**Verdict:** MINOR
- [Med] [harness] ask-questions.md:134-149 — Hand-rolled text menu ("**[A] Recommended:** … Your choice (A/B/C/D/S):") predates the AskUserQuestion tool, which renders native multiple-choice and blocks until answered → permit/prefer AskUserQuestion for option presentation (keep the text protocol as fallback and for `save`/`go to N` session commands).
- [Low] [stale-model] ask-questions.md:357 — Worked example offers "Use GPT-4 (OpenAI) for both AI and transcription (Whisper)" — 2023-era model naming in a copyable example → genericize so the example doesn't date.
- [Low] [context-economy] ask-questions.md:90-106,276-302 — Three near-identical validation error/warning message blocks → consolidate to one pattern + pointer to `references/patterns/validation.md`.
- [Good] "ONE AT A TIME" and "wait for input" rules are deliberate interview UX, not anachronistic micro-management — keep.

### assess-document.md
**Verdict:** MINOR
- [Low] [hard-coded-sizes] assess-document.md:72 — "File exceeds context window capacity (~100K tokens)" → stale for 1M-context primaries; raise or phrase as a fraction of context.
- [Low] [context-economy] assess-document.md:179-343 — ~165 lines of inline report template + full JSON schema → candidate for extraction to `references/`.
- [Good] Score rubric with anchors is load-bearing (comparability across runs); `effort: high` justified for multi-dimension judgment.

### bump-version.md
**Verdict:** OK
- [Low] [prompt-style] bump-version.md:88-99 — Table plus rules spelling out semver arithmetic ("major: Increment first number, reset others to 0") → trim to the table alone.
- [Good] `effort: low` correctly calibrated; dry-run mode, safety rules, dynamic plugin discovery all clean.

### clean-repo.md
**Verdict:** MINOR
- [Med] [metadata] clean-repo.md:1-5 — No `effort:` field on a deep multi-phase analysis + documentation-sync command (Phase 3 cross-references every doc claim against code) → add `effort: high` (or `medium`).
- [Low] [prompt-style] clean-repo.md:36,75,126 — Repeated defensive emphasis ("CRITICAL: This phase must be completed thoroughly", "Use the Glob tool (NOT shell `find`)" twice, "Never delete files without listing them first" restated) → state each rule once.
- [Good] Phase ordering rationale, batch processing, DO-update/ASK-before-update split well judged.

### consolidate-documents.md
**Verdict:** OK
- [Low] [context-economy] consolidate-documents.md:255-299 — Inline JSON schema + two long example transcripts (~130 lines) → move to `references/consolidate-documents-examples.md`.
- [Good] Context strategy is context-relative ("exceeds approximately 60% of available context") rather than hard token counts — the pattern other files should copy; `effort: high` justified.

### convert-markdown.md
**Verdict:** OK
- [Low] [metadata] convert-markdown.md:3 — `argument-hint` omits documented `--dry-run` and `--highlight <style>` flags (lines 21-22) → add them.
- [Good] `effort: low` correct for a pandoc wrapper; dependency-check-before-processing is the house pattern.

### create-plan.md
**Verdict:** NEEDS-CHANGE
- [Med] [effort] create-plan.md:4 — `effort: max` → re-evaluate for Opus 5: `max` shows diminishing returns and overthinking risk on routine planning; `high` likely equal-quality at lower latency/cost. A/B one representative plan before keeping `max`.
- [Med] [harness] create-plan.md:5 vs :107 — `allowed-tools: Read, Glob, Grep, Write, Edit, Agent, Bash(git:*)` doesn't cover the Phase 1.5.1 instruction to run `find . -type f …` — that Bash call hits a permission prompt mid-recon → use Glob (the repo's own convention) or extend allowed-tools.
- [Low] [tier-routing] create-plan.md:310 — Orchestrator note "implement-plan itself benefits from running on Opus" written when session defaults were weaker → reword for the Opus-5-primary era ("run on `opus` — the default — or `fable` for exceptionally large plans"); same note in plan-improvements.md:350 and implement-plan.md:41.
- [Good] Per-item Model Tier assignment (line 262) and Execution Hints use tier aliases only — fully ADR-0005 compliant; pre-planning quality gate + scope-confirmation checkpoint are excellent.

### define-questions.md
**Verdict:** OK
- [Low] [prompt-style] define-questions.md:300 — "Typically completes in under 30 seconds regardless of document size" contradicts its own large-document sectioned-processing path (line 270) → drop "regardless of document size".
- [Good] `effort: low` correctly calibrated; schema rules are the downstream contract, appropriately explicit.

### develop-image-prompt.md
**Verdict:** MINOR
- [Med] [stale-model] develop-image-prompt.md:247-256,331-339 — Generator-specific parameters target "DALL-E 3" and SD1.x-era Stable Diffusion settings ("Sampler: DPM++ 2M Karras, CFG Scale: 7") — 2024 image-gen snapshot templated into every generated prompt file → refresh to current generators or make generic.
- [Low] [metadata] develop-image-prompt.md:1-5 — No `effort:` field; creative visual composition benefits from thinking → add `effort: medium`.
- [Good] Dimension/composition logic and style presets are timeless; no Claude model references.

### finish-document.md
**Verdict:** OK
- [Low] [harness] finish-document.md:150-152 — Phase 2 inherits ask-questions' hand-rolled choice UI by reference; fixing ask-questions (AskUserQuestion) covers this file automatically.
- [Good] Backup-before-modify, atomic-update, resume support solid; delegating display formats to `/ask-questions` is the right context-economy call.

### implement-plan.md
**Verdict:** MINOR
- [Med] [tier-routing] implement-plan.md:232 — Escalation ceiling: "If the current tier is already `opus`, do not escalate further" — written before the `fable` alias existed above `opus`. Decide policy explicitly: either allow a final opus→fable escalation for judgment-critical failures, or add one line stating fable is deliberately excluded (cost). Silence reads as oversight rather than decision.
- [Low] [tier-routing] implement-plan.md:41 — "the orchestrator benefits from running on Opus… starting a session on Opus before invoking is recommended" — with Opus 5 as primary session model this is satisfied by default → reword; reserve the advisory for `fable` on very large plans.
- [Low] [tier-routing] implement-plan.md:165,202 — Default tier "typically `sonnet`" remains correct, but add one-line note that Sonnet 5 now covers most work formerly tiered `opus` so re-planners don't over-tier upward (full rubric in `references/plan-template.md` rule 17 — update there too).
- [Low] [context-economy] implement-plan.md — At 45KB the largest command; Overview (37-127) restates much of Instructions; Performance/duration table generic → compress or push to `references/`.
- [Good] Exemplary harness currency: tier aliases only, parallel-first dispatch with `run_in_background: true`, per-phase `isolation: worktree` with loop guard, state-file resume, alias-passing fallback. The heavy proceduralism is a state machine, not micro-management — keep it.

### new-skill.md
**Verdict:** NEEDS-CHANGE
- [High] [stale-model][ADR-0005] new-skill.md:169 — Generated frontmatter template (tool-restrictions variant) emits `# model: claude-opus-4` — pinned ID of a deprecated model, stamped into every future skill this command scaffolds → `# model: opus   # tier alias (haiku/sonnet/opus/fable/inherit) — never pinned IDs (ADR-0005)`.
- [High] [stale-model][ADR-0005] new-skill.md:198 — Same `# model: claude-opus-4` in the no-restrictions template variant → same fix.
- [High] [stale-model][ADR-0005] new-skill.md:294 — Field-reference table: "`model` | Optional | `claude-opus-4`, `claude-sonnet-4-5`, etc." → replace with tier aliases and cite ADR-0005.
- [Med] [stale-model] new-skill.md:282 — "All fields supported by Claude Code as of late 2025" — stale currency stamp → remove or update.
- [Med] [metadata] new-skill.md:98,287 — "under 150 characters ideal" / "Free text ≤ 150 chars" for `description` contradicts the repo's own ≤1024-chars-with-all-trigger-info rule → align; under-sized descriptions harm proactive triggering of generated skills.
- [Med] [harness] new-skill.md:308 — Dynamic-injection example `` !`git status -s` `` documented without the issue-#183 guard — teaches future authors the unguarded pattern → guarded form (`` !`git status -s 2>/dev/null || true` ``) + gotcha note.
- [Low] [harness] new-skill.md:293 — `agent: Explore, Think, Code` vs scaffold-plugin.md:195's `agent: explorer` — generators disagree on agent-name vocabulary → verify against current harness and unify.
- [Good] Skills-vs-commands `name` rules, nested-directory enforcement, pattern-adaptation transforms precise and current.

### plan-improvements.md
**Verdict:** NEEDS-CHANGE
- [Med] [effort] plan-improvements.md:4 — `effort: max` → same re-evaluation as create-plan; if `max` stays anywhere it's here — but verify rather than inherit.
- [Med] [prompt-style] plan-improvements.md:34,36 — "### Phase 1: Deep Codebase Analysis (Ultrathink)" / "with extended thinking enabled" — legacy thinking-mode invocations; thinking is adaptive for the primary model and "Ultrathink" is a dead magic keyword → delete both.
- [Med] [hard-coded-sizes] plan-improvements.md:53,414-421 — "Reserve at least 40% of context… stop at 60%" plus Context Budget table in absolute tokens ("~30K analysis / ~70K output") — sized for 200K window; forces unnecessary sampling on 1M-context primaries → re-express as fractions only, raise the 100-file full-read threshold, or delete the token table.
- [Low] [prompt-style] plan-improvements.md:72-127 — Checklists pin arbitrary numbers ("trace the 3 most common workflows", "files exceeding 300 lines") → mark as defaults rather than requirements.
- [Low] [tier-routing] plan-improvements.md:350 — Same orchestrator-on-Opus advisory rewording as create-plan.md:310.
- [Good] Priority rubric, Impact/Effort matrix, Unknowns-vs-Risks routing — strong, judgment-preserving structure; tier guidance is alias-only.

### plan-next.md
**Verdict:** OK — no findings. P0-P9 decision matrix is policy worth encoding, `effort: medium` right, git/gh probes guarded, "Do NOT auto-invoke /plan-improvements" correct restraint. Cleanest file alongside bump-version.

### remove-ip.md
**Verdict:** MINOR
- [Med] [metadata] remove-ip.md:1-4 — No `effort:` field on the most judgment-intensive command (adversarial mosaic testing, least-lossy generalization) → add `effort: high`; clearest "absent where it matters" case.
- [Good] Mode split, generalization ladder, safe-default questioning excellent; WebSearch grant matches `--web-research`; no model references.

### review-arch.md
**Verdict:** OK
- [Low] [prompt-style] review-arch.md:10,250-255 — "READ-ONLY COMMAND — DO NOT MAKE ANY CHANGES" banner duplicated while `allowed-tools: Read, Glob, Grep` already enforces read-only → one mention suffices.
- [Good] `effort: high` justified; cross-cutting analysis before roadmap is the right anti-patchwork instruction; correctly routes standard review to native `/review`.

### review-intent.md
**Verdict:** OK
- [Low] [prompt-style] review-intent.md:56,399 — "DO NOT MAKE ANY CHANGES" stated twice → once suffices (Write legitimately allowed for `--save`).
- [Good] Intent-source priority table, confidence levels, metric formulas, "not all drift is bad" framing — mature judgment-trusting design; `effort: high` justified.

### scaffold-plugin.md
**Verdict:** MINOR
- [Med] [harness] scaffold-plugin.md:195 — Templates out `# agent: explorer` — disagrees with new-skill.md's `Explore`/`Think`/`Code` vocabulary; both are generators whose output propagates → verify current harness agent names and unify.
- [Low] [ADR-0005] scaffold-plugin.md:184-197 — Quick reference omits a `model:` row (which prevents stale pins); if added for parity, tier aliases only.
- [Low] [metadata] scaffold-plugin.md:1-4 — No `effort:` field; mechanical scaffolding → `low` (optional).
- [Good] Skills-first ADR-0006 messaging consistent; `--with-commands` legacy gating well-handled; no model IDs anywhere.

### test-project.md
**Verdict:** MINOR
- [Med] [harness] test-project.md:5,156 — `allowed-tools` ends with `Task` but line 156 says "Use the Agent tool (with `run_in_background: true`)… Use the Task tool for tracking progress" — Agent not granted; bare `Task` stale vs the `TaskCreate/TaskUpdate/TaskList/TaskOutput` family → fix grant list and prose.
- [Low] [prompt-style] test-project.md:370-378 — Dead duplicated branch: both merge arms run `gh pr merge --squash` (editing leftover) → delete second arm or supply the actual fallback.
- [Low] [prompt-style] test-project.md:270-283 — Selective-staging mock commands can mislead (`git add tests/` stages unrelated files); rules list beneath fully covers policy → drop the mock commands.
- [Good] Scope-confirmation gate, fix-loop iteration cap with user escalation, no-`git add -A` policy sound; `effort: high` justified for the fix loop.

### validate-plugin.md
**Verdict:** MINOR
- [Med] [effort] validate-plugin.md:4 — `effort: high` on a mostly mechanical checklist runner → `medium` sufficient; keep `high` only if `--scorecard` judgment is frequent.
- [Low] [metadata] validate-plugin.md:3 — `argument-hint` omits `--report`, `--scorecard`, `--check-updates` (documented at 22-24) → add.
- [Good] Strongest context-economy example — output samples externalized to `references/validation-output-examples.md`; dynamic plugin discovery; Phase 8.5.3 checks tier words, not pinned IDs; guarded `gh` fetch with local fallback.

### deprecated/ (skim)
**Verdict:** MINOR (one actively-harmful item)
- [Med] [stale-model][ADR-0005] deprecated/new-command.md:193 — `model` | "Override model per subagent" | `claude-opus-4-5` — pinned ID in the direct ancestor of the new-skill templating flow; readers mining the archive will copy it → fix to tier alias, or add a stale-examples banner to deprecated/README.md.
- [Low] deprecated/setup-statusline.md:354 — "e.g., 'Claude Opus'" display-name example — harmless. check-updates.md, convert-hooks.md — no model content.

## Summary table

| File | Verdict | High | Med | Low |
|---|---|---|---|---|
| analyze-transcript.md | MINOR | 0 | 1 | 1 |
| arch-review-single.md | OK | 0 | 0 | 1 |
| arch-synthesize.md | OK | 0 | 0 | 1 |
| ask-questions.md | MINOR | 0 | 1 | 2 |
| assess-document.md | MINOR | 0 | 0 | 2 |
| bump-version.md | OK | 0 | 0 | 1 |
| clean-repo.md | MINOR | 0 | 1 | 1 |
| consolidate-documents.md | OK | 0 | 0 | 1 |
| convert-markdown.md | OK | 0 | 0 | 1 |
| create-plan.md | NEEDS-CHANGE | 0 | 2 | 2 |
| define-questions.md | OK | 0 | 0 | 1 |
| develop-image-prompt.md | MINOR | 0 | 1 | 1 |
| finish-document.md | OK | 0 | 0 | 2 |
| implement-plan.md | MINOR | 0 | 1 | 3 |
| new-skill.md | NEEDS-CHANGE | 3 | 3 | 2 |
| plan-improvements.md | NEEDS-CHANGE | 0 | 3 | 2 |
| plan-next.md | OK | 0 | 0 | 0 |
| remove-ip.md | MINOR | 0 | 1 | 0 |
| review-arch.md | OK | 0 | 0 | 1 |
| review-intent.md | OK | 0 | 0 | 1 |
| scaffold-plugin.md | MINOR | 0 | 1 | 2 |
| test-project.md | MINOR | 0 | 1 | 2 |
| validate-plugin.md | MINOR | 0 | 1 | 1 |
| deprecated/ (4 files) | MINOR | 0 | 1 | 1 |
| **Totals** | 3 NC / 10 MINOR / 10 OK (+deprecated) | **3** | **18** | **31** |

## Themes (commands)

ADR-0005 discipline held almost everywhere: the entire implement-plan tier-routing pipeline uses aliases exclusively; only one live file, `new-skill.md`, carries pinned stale IDs — the worst possible file, since it is a generator whose templates propagate into every future skill (all three High findings; fix first). Second: stale capacity assumptions — hard-coded token budgets (30K/50K/100K thresholds, absolute context-budget tables) sized for 200K-context models now force unnecessary chunking/sampling under 1M-context primaries. Third: effort calibration drifted both directions — the two `effort: max` planners should be A/B'd against `high` on Opus 5 (overthinking risk); validate-plugin's `high` over-provisions mechanical checks; clean-repo and remove-ip (genuine judgment work) have no effort field. Fourth: tier-routing prose predates the `fable` alias — implement-plan's escalation ceiling stops silently at `opus`, and the "run the orchestrator on Opus" advisory is now satisfied by session defaults. Finally, small harness drift: test-project's stale `Task` grant with no `Agent` tool, create-plan's `find` outside allowed-tools, generator disagreement on `agent:` names, ask-questions predating AskUserQuestion, and new-skill's docs table teaching the unguarded issue-#183 `` !`git …` `` pattern. plan-next, bump-version, and validate-plugin's reference-extraction stand as house exemplars.

---

# Section B — personal-plugin skills A–L (13 skills)

### skills/accessibility-annotator
**Verdict:** MINOR
- [Med] [harness/allowed-tools] SKILL.md:5 — `allowed-tools: Read, Write, Bash(pandoc:*), Bash(bws:*), Bash(python3:*), Task` lacks Glob/Grep (and any `ls`-capable Bash), yet Step 2 says "Read the project directory structure … and 2-3 key source files" and Phase 2 Step 1 requires deep-reading source — with only Read the model cannot enumerate files → add Glob, Grep.
- [Low] [harness] SKILL.md:5 vs arch-review:6 — repo mixes `Task` (here, explain-project, templates/skill.md) and `Agent` (arch-review, jetson-audit, leak-risk-audit) for the dispatch tool; standardize on whichever the current harness resolves.
- [Low] [stale-model/portability] SKILL.md:321 — pinned external image model `gemini-3-pro-image-preview` "(default as of 2026-03-31)" hard-coded in skill prose; dated IDs belong in env-overridable config, not skill text.
- [Low] [triggering] frontmatter — no `argument-hint` despite two required positional args plus `--generate-images`/`--style-json` flags.
- [Low] [context-economy] SKILL.md:8-43, 63-77, 106-114, 226-240, 280-309, 349-355, 376-382 — ~90 lines of decorative HTML comment banners loaded on every invocation; slim and move HISTORY + "Lessons Learned" (384-404) to `references/`.
- Good: Phase 1 fork→Explore dispatch, per-image parallel subagents with rate-limit-aware concurrency cap and parent-only XML writes, `effort: high` appropriate, zero stale Claude references.

### skills/arch-review
**Verdict:** OK
- [Low] [tier-routing] SKILL.md:87-121 — dispatch table sets no effort/model expectations for the 9 domain agents; with Sonnet 5 now strong, domain agents are sonnet-tier candidates while lead synthesis (Steps 4-5) stays opus. Routing lives in `agents/*.md`, but a one-line expectation here keeps orchestration and agent config aligned.
- [Low] [harness] SKILL.md:6 — `Agent` in allowed-tools vs `Task` elsewhere; pick one.
- Good: line 44 explicitly documents and guards the exact #183 parse-time-injection pitfall; genuinely parallel dispatch; `disable-model-invocation: true` appropriate here (expensive run, description carries no suggest-triggers); justified unscoped Bash with inline rationale; re-spawn-on-incomplete behavior.

### skills/archive-project
**Verdict:** MINOR
- [Med] [triggering] SKILL.md:3,6 — description ends with "Suggest when the user says archive project, retire project, sunset repo…" but `disable-model-invocation: true` removes the description from session context — dead metadata. Either drop the flag (Phase 0's mandatory confirmation already guards the destructive part) or strip the suggest-prose.
- [Low] [effort] frontmatter — no `effort:`; mechanical/confirmation-gated → explicit `effort: low`.
- Good: destructive-action confirmation gating, remote-classification branch table, thorough error handling, correct `argument-hint`.

### skills/brain-entry
**Verdict:** MINOR
- [Med] [triggering] SKILL.md:3-4 — same contradiction: "Suggest (do not auto-run) when — user says log/capture/remember…, end of session…" is unreachable under `disable-model-invocation: true`. Remove the flag (the skill only POSTs after generating content the user asked for).
- [Med] [harness/allowed-tools] SKILL.md:5 vs 48-76, 87 — `Bash(curl:*)` is the only Bash scope, but Step 3's script is a compound (`RAW=$(curl…)`, `tail`, `sed`, `echo`, `exit`) and Step 4 pipes `$BODY` into `python3` — neither matches, so the documented flow hits permission prompts/denials. Widen scope or restructure into pure-curl + model-side parsing.
- [Low] [triggering] frontmatter — no `argument-hint` (`"<instruction>"`).
- Good: compact body, heredoc/JSON hygiene, HTTP-status verification before claiming success, 50K truncation rule.

### skills/clear-prep
**Verdict:** NEEDS-CHANGE
- [High] [harness/#183] SKILL.md:27-29 — three unguarded live injections: `` !`git status -s` ``, `` !`git log --oneline -8` ``, `` !`git branch --show-current` ``. In a non-git directory these abort the whole skill at parse time — before the Error Handling promise at line 132 can execute. Guard each (`` !`git status -s 2>/dev/null || true` ``) or delete the block: Phase 1 step 1 re-runs the identical commands via Bash anyway, making the injections redundant.
- Good: everything else — `effort: medium` right, description carries triggers with no `disable-model-invocation` (correctly suggestible), tight 136-line body, writes-docs-only/never-commits contract, resume-prompt template high-value and judgment-shaped.

### skills/create-wiki
**Verdict:** MINOR
- [Med] [triggering] SKILL.md:3-4 — "Suggest (do not auto-run) when — project accumulating complexity, context loss between sessions…" is dead under `disable-model-invocation: true`. Precisely a skill that benefits from proactive suggestion; drop the flag.
- [Low] [harness] SKILL.md:43-56 — Maintenance Mode framed around "when `paths:` auto-activation fires" but frontmatter declares no `paths:` — references a mechanism the skill doesn't configure. Add the `paths:` block or reword.
- Good: model progressive disclosure — reads `references/wiki-readme-template.md` and `references/claude-md-wiki-section.md` at run time instead of inlining; idempotency rules; "seeded, not empty" quality bar; judgment-based maintenance philosophy fits a frontier model well.

### skills/evaluate-pipeline-output
**Verdict:** MINOR
- [Med] [parallelism] SKILL.md:76-78, 153-427 — 13 phases run forced-serial, yet Phases 2-10 are independent per-stage evaluations once Phases 0-1 complete; references cite 25-40 minute runs at large sizes. Add guidance to dispatch independent phases as parallel fork subagents on medium+ runs, parent doing Phase 11-13 synthesis.
- [Low] [prompt-style] SKILL.md:53-72 + "apply Finding Analysis Protocol to each" repeated at 174, 193, 225, 245, 276, 307, 340, 371, 399, 426 — protocol is good; per-phase repetition and "Do not skip this protocol" defensiveness is anachronistic for Opus 5. State once.
- [Low] [context-economy] SKILL.md — 496 lines, brushing the 500 cap; per-phase "Key findings" severity lists could fold into the guidance reference.
- Good: "Derive, Don't Hardcode" (42-48) is exactly right for a strong model; references split already done; read-only contract; `effort: high` correct.

### skills/explain-project
**Verdict:** NEEDS-CHANGE
- [High] [harness/#183] SKILL.md:142-143 — unguarded injections `` !`git log --oneline -20` `` and `` !`git shortlog -sn --no-merges | head -10` ``: (a) abort the skill outside a git dir; (b) in GitHub-URL mode they execute in the invoking cwd before the clone exists, injecting the wrong project's git history. Guard with `2>/dev/null || true`, or better delete — the fork'd Explore agent can run these post-clone in the right directory.
- [Med] [harness/allowed-tools] SKILL.md:5 vs 369-377 — no `Write` in allowed-tools, but Phase 4 requires "Write the complete content as a JSON file" before invoking doc-builder. Add Write (and note `git shortlog | head` won't match `Bash(git:*)` as a compound).
- [Low] [harness] SKILL.md:102-106 — `isolation: worktree` presented as inline YAML mid-body for the clone step; worktree isolation is a dispatch/frontmatter property — verify placement takes effect, or move the clone inside an isolated subagent dispatch.
- [Low] [context-economy] SKILL.md:8-47, 119-133, 165-231, 312-365, 404-455 — ~140 lines of decorative banners plus 15-item Lessons Learned (456-486); move lessons + doc-builder JSON schema to `references/`.
- Good: fork→Explore dispatch for Phases 1/3.5, verification-against-runtime-data phase (anti-fabrication grounded in artifacts, not boilerplate), `--update` incremental mode, `effort: high` correct.

### skills/fleet-health
**Verdict:** OK
- [Low] [effort] frontmatter — no `effort:`; targets "under 60 seconds" of mechanical probing → explicit `effort: low`.
- [Low] [harness/allowed-tools] SKILL.md:4, 67 — "background each machine's SSH session with `&`, then `wait`" produces compounds that won't match `Bash(ssh:*)`/`Bash(curl:*)` scopes → mid-run prompts. Alternative: per-host probes as independent parallel Bash calls in one block.
- Good: description (561 chars) carries all triggers with no `disable-model-invocation` — exactly right; Known States false-alarm section is exemplary encoded judgment; grep-able `VERDICT:` contract; explicitly read-only.

### skills/jetson-audit
**Verdict:** MINOR
- [Med] [harness] SKILL.md:244-255, 267 — `/schedule create --name jetson-audit-weekly … --skill jetson-audit`: no `schedule` command exists in the repo or current harness (current: Routines/triggers, or loop-style recurring skill). Same dead blocks in jetson-recon and baseline template. Replace or mark aspirational.
- [Low] [triggering] SKILL.md:4-8 — `disable-model-invocation: true` combined with `paths:` auto-activation; Loop Guard presumes paths-triggering fires. Verify interaction; `paths:` absent from CLAUDE.md's optional-frontmatter list (documented in `references/patterns/advanced-features.md:84`) — reconcile.
- [Low] [effort] frontmatter — absent; drift-comparison judgment → `effort: medium`.
- [Low] [context-economy/coupling] SKILL.md:259-261 — "create it using the template in jetson-recon/SKILL.md" forces loading a second full skill; template belongs in shared `audit-recon-system.md`.
- Good: Trust Boundary (28-30) first-rate — fixed read-only SSH allowlist never derived from read content; concrete flag/severity matrices; zero stale Claude model references.

### skills/jetson-recon
**Verdict:** MINOR
- [Med] [triggering] SKILL.md:3-4 — description is pure trigger prose yet `disable-model-invocation: true` removes it from context — dead triggers. Report-only skill; drop the flag or rewrite description as plain summary.
- [Med] [harness] SKILL.md:150-163, 236-240 — same nonexistent `/schedule` integration as jetson-audit.
- [Low] [hard-coding] SKILL.md:110 — "Qwen3.5-4B Q4_K_M workload (SM87, CUDA 12.6)" duplicates values tracked in `JETSON_BASELINE.md`; instruct "the current model/CUDA from the baseline".
- [Low] [effort] frontmatter — absent; web-research synthesis → `effort: medium`.
- Good: two-tier Trust Boundary (untrusted web content strictly data; SSH strictly fixed 10-command allowlist) is a model prompt-injection defense; parallel check structure; error handling covers fetched-instructions explicitly.

### skills/lab-notebook
**Verdict:** MINOR
- [Med] [context-economy] SKILL.md:256-373 — ~115-line verbatim CLAUDE.md injection template inlined, pushing body to 499 lines (at cap). Move to `references/claude-md-notebook-section.md`, read at inject time (create-wiki proves the pattern). Cuts ~25% of the always-loaded body.
- [Med] [triggering] SKILL.md:3,5 — "Suggest (do not auto-run) when — infrastructure/experimental/expensive-failure projects…" dead under `disable-model-invocation: true`. `status` is harmless to model-invoke, init confirmation-shaped; drop the flag.
- [Low] [triggering] frontmatter — no `argument-hint` despite four subcommands (`"[init | entry \"title\" | status | rotate]"`).
- Good: `references/rotation.md` excellent progressive disclosure; hook documentation and D14-D18 near-loss lesson encoded; `effort: medium` sensible; no stale model references.

### skills/leak-risk-audit
**Verdict:** NEEDS-CHANGE
- [High] [harness/#183] SKILL.md:56-57 — `` !`ls -la <dataset-path>` `` and `` !`find <dataset-path> …` `` with "Replace `<dataset-path>` with the actual path from arguments" cannot work: `` !`cmd` `` injection runs at parse time, before arguments exist, so literal `<dataset-path>` reaches bash — where `<`/`>` are redirection operators — guaranteed breakage. The exact pitfall arch-review/SKILL.md:44 documents. Fix: delete injection framing; run `ls`/`find` via Bash after parsing `$ARGUMENTS`.
- [Low] [prompt-style] SKILL.md:10 — "You have seen careers end and companies sued over a single leaked vendor name…" — dramatized persona filler; severity taxonomy and Important Rules carry the behavior. Trim the theater.
- [Low] [triggering] frontmatter — no `argument-hint` (`"<path> [--output <file>] [--glossary <path>]"`); description minimal (170 chars) — room for suggest-triggers since there's no `disable-model-invocation`.
- Good: 4-tier parallel `context: fork` dispatch with parent-exclusive report writing and JSON-only subagent returns is correct, modern concurrency design; unscoped Bash carries inline justification; "do not leak in the report itself" rule shows real judgment encoding.

## Summary table

| Skill | Verdict | High | Med | Low |
|---|---|---|---|---|
| accessibility-annotator | MINOR | 0 | 1 | 4 |
| arch-review | OK | 0 | 0 | 2 |
| archive-project | MINOR | 0 | 1 | 1 |
| brain-entry | MINOR | 0 | 2 | 1 |
| clear-prep | NEEDS-CHANGE | 1 | 0 | 0 |
| create-wiki | MINOR | 0 | 1 | 1 |
| evaluate-pipeline-output | MINOR | 0 | 1 | 2 |
| explain-project | NEEDS-CHANGE | 1 | 1 | 2 |
| fleet-health | OK | 0 | 0 | 2 |
| jetson-audit | MINOR | 0 | 1 | 3 |
| jetson-recon | MINOR | 0 | 2 | 2 |
| lab-notebook | MINOR | 0 | 2 | 1 |
| leak-risk-audit | NEEDS-CHANGE | 1 | 0 | 2 |
| **Totals** | | **3** | **12** | **23** |

## Themes (skills A–L)

(1) Model hygiene clean: zero Claude model references of any vintage across all 13 skill dirs; only pin is a dated Gemini image model in accessibility-annotator. (2) Three live #183-class injection bugs (clear-prep, explain-project, leak-risk-audit) are the only Highs — arch-review already documents the failure mode and fix in-repo; copy-the-known-pattern repair. (3) Systematic `disable-model-invocation` vs "Suggest when…" contradiction in five skills (archive-project, brain-entry, create-wiki, lab-notebook, jetson-recon): the flag deletes the description carrying the suggest-triggers — dead metadata; each needs a deliberate keep-flag-trim-description or drop-flag decision. (4) allowed-tools drift: missing Write (explain-project), missing Glob/Grep (accessibility-annotator), over-narrow Bash scopes vs compound scripts (brain-entry, fleet-health), unresolved `Task` vs `Agent` naming split. (5) Vestigial `/schedule` integration in both jetson skills references a command that exists nowhere. (6) Effort calibration good where present, absent on five skills — most consequentially fleet-health (explicit `low` matches its sub-60-second contract). (7) Patterns worth propagating: arch-review's injection guard, jetson pair's trust boundaries, create-wiki's reference-template indirection, leak-risk-audit/accessibility-annotator's parent-writes/subagents-return-JSON concurrency discipline.

---

# Section C — personal-plugin skills M–Z (16 skills)

Verified against the current model catalog: `claude-opus-5` (primary), `claude-sonnet-5` (secondary), `claude-haiku-4-5` (small tier), `fable` alias above opus. Key API fact used below: on Opus 5 / Sonnet 5 / Opus 4.8/4.7, `thinking: {type: "enabled", budget_tokens: N}` is **rejected with HTTP 400** — adaptive thinking + `output_config.effort` replaced it.

### skills/new-project
**Verdict:** MINOR
- [Med] [triggering] SKILL.md:3-5 — description says "Suggest (do not auto-run) when the user says new project…" but `disable-model-invocation: true` removes the description from session context, so the "suggest" intent can never fire → either drop the flag (invocation is confirmation-gated anyway) or strip the dead trigger prose.
- [Low] [effort] SKILL.md:1-7 — no `effort:`; mechanical scaffolding → add `effort: low`.
- Good: validation-first ordering, hook-aware step sequencing, secrets hygiene, template placeholder tables; no model references.

### skills/plan-gate
**Verdict:** OK
- [Low] [effort] SKILL.md:4 — `effort: low` sanity-checked: **correct**. Self-describes as "a routing decision, not an analysis tool… complete in under 10 seconds"; low is exactly right with a stronger primary model.
- Good: Path B.5 (parallel decomposition via worktree-isolated agents) and D.5 (ultra-plan) show current harness awareness; read-only `allowed-tools` correctly minimal; no stale model references. No changes needed.

### skills/prime
**Verdict:** NEEDS-CHANGE
- [High] [harness/#183] SKILL.md:60-68 — seven unguarded `` !`git …` `` dynamic injections (`git log --oneline -20`, `git shortlog`, `git status -s`, etc.). These abort the skill in non-git directories, directly contradicting its own error handling ("If not in a git repository: Note this in the report, skip git-dependent analysis", line 343) → guard each (`git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git … || echo "not a git repo"`) or drop the injections and run git via Bash inside Phase 2 where failure is handleable.
- [High] [harness] SKILL.md:5 vs 26,44,86,148 — body mandates per-phase dispatch "via `context: fork` + `agent: Explore`" for Phases 1/3/5, but `allowed-tools: Read, Glob, Grep, Bash(git:*)` grants no Agent/Task tool, so the prescribed fork dispatch is impossible as configured → add the agent-dispatch tool to allowed-tools (and dispatch Phases 1, 3, 5 in parallel — they are independent; current text implies serial).
- [Low] [prompt-style] SKILL.md:349-356 — fixed duration table ("Very Large: 5-10 minutes") is a hard-coded assumption that shifts with parallel dispatch and a faster model; make approximate or drop.
- [Low] [effort] `effort: high` appropriate for full-repo assessment. Report template and Phase 0 lab-notebook-first rule are good; keep.

### skills/release-plugin
**Verdict:** MINOR
- [Med] [triggering] SKILL.md:4-5 — same disable-model-invocation contradiction: description carries "Suggest when — plugin changes complete and ready to ship…" but the flag removes it from context → strip trigger prose or drop the flag.
- [Low] [harness] SKILL.md:62-70 — Phase 1 re-implements validation "inline"; repo rules name `claude plugin validate --strict` as the validator tiebreaker → note the CLI as preferred first check, falling back to inline logic.
- [Low] [prompt-style] SKILL.md:84-103,139-151,213-247,283-317 — heavy verbatim box-drawn output templates for every phase/outcome; Opus 5 needs the content contract, not the ASCII art → compress to one example + rules, or move to `references/`.
- [Low] [effort] no `effort:`; orchestration with judgment in the ship phase → `effort: medium` reasonable.

### skills/research-topic
**Verdict:** NEEDS-CHANGE
- [High] [stale-model] SKILL.md:35 and SKILL.md:153 — `ANTHROPIC_MODEL` default `claude-opus-4-8` is one generation stale → change both to `claude-opus-5`. Same stale ID in the plugin-level source of truth this skill defers to: `references/research-models.md:19,33,64` (marked "verified 2026-07-08").
- [High] [stale-model/API-break] SKILL.md:190-196,219,238 + `references/research-provider-protocols.md:27-29` — the Claude depth mechanism is `thinking.budget_tokens` (4,000/10,000/32,000). **`budget_tokens` returns HTTP 400 on `claude-opus-4-8` and `claude-opus-5` alike** — the Claude leg of this skill fails on every request under the current default, not just after the ID bump → replace the depth mapping with `output_config: {effort: …}` (+ adaptive thinking or omit; thinking is on by default on Opus 5), and update the curl body in the protocol reference.
- [Med] [tier-routing] SKILL.md:12,237 — the Claude leg is a single synchronous messages call (parametric knowledge only) while the OpenAI/Gemini legs are true web-connected deep-research agents; capability asymmetry biases the synthesis → add the web-search server tool to the Claude API request, or let the fork subagent (which already holds WebSearch/WebFetch) do agentic research natively instead of one raw curl.
- [Med] [harness] SKILL.md:200-224 — subagent prompt template begins with the literal line "`context: fork`" inside the prompt text; that is a frontmatter/dispatch directive, not prompt content — as prompt text it's a no-op → move fork semantics to the actual dispatch and delete the line from the template.
- [Low] [stale-model] SKILL.md:36-37 — third-party defaults `o3-deep-research-2025-06-26` and `deep-research-pro-preview-12-2025` likely stale by 2026-07; ADR-0005's "reviewed at release" cadence has lapsed → re-verify both.
- Good: parallel dispatch, graceful per-provider key-skip, partial-result synthesis, progressive disclosure to two reference files.

### skills/security-analysis
**Verdict:** MINOR
- [Med] [context-economy] SKILL.md:221 — "refer to the reference files in the plugin's `references/` directory" is a broken pointer: the 13 per-stack files (`node_security.md` … `vue_security.md`) live flat inside `skills/security-analysis/` itself → fix the pointer (and optionally move them into `skills/security-analysis/references/`).
- [Med] [triggering] SKILL.md:6-12 — `paths:` frontmatter key is not among the house-documented skill keys; if the validator/loader ignores it, the entire "Auto-Activation Confirmation" flow (19-28) is dead code → negative-test with `claude plugin validate --strict` and an actual manifest edit (E043 rule). Same key in spark-audit/spark-recon.
- [Low] [prompt-style] SKILL.md:97 — "**IMPORTANT**: Always run native security audit tools FIRST" — rule fine, shouted emphasis is legacy-model insurance.
- Good: `effort: high` correct; scope-vs-`/security-review` routing table current; per-stack files proper progressive disclosure; no stale model references in any of the 13 reference files (verified by scan).

### skills/ship
**Verdict:** NEEDS-CHANGE
- [High] [harness/#183] SKILL.md:15,18,21,24,27,30 — six unguarded `` !`git …` `` injections ("Pre-loaded Context"). In a non-git directory these abort the skill before its own pre-flight check (line 77) can run → guard every injection.
- [Med] [harness] SKILL.md:30 — `` !`git diff --stat | tail -1 | awk '{print $NF}'` `` — the last field of `git diff --stat`'s summary line is the literal string `deletions(-)`, never a number, so the "Diff size" value is garbage and the >500 large-diff gate (lines 80, 275) can never trigger — large diffs silently enter the auto-fix loop the gate was built to prevent → use `git diff --shortstat | awk '{print $4+$6}'` or similar.
- [Med] [triggering] SKILL.md:4-5 — `disable-model-invocation: true` + elaborate "Suggest when the user signals completion (done, ready to ship…)" trigger prose that can never fire. Ship is arguably the skill the user *wants* proactively suggested on "ready to ship" → decide: proactive (drop flag) or manual-only (trim description).
- [Med] [harness] SKILL.md:3,57-62 — `--audit` mode must create/append `.claude-plugin/audit.log`, but `allowed-tools` grants no `Write` and Bash is scoped to git/gh/tea → add `Write` or drop `--audit`.
- [Low] [effort] no `effort:` on a skill containing a full code-review + fix loop (Phases 6-7) → `effort: medium` (or high).
- Good: documentation gate (LAB_NOTEBOOK hard gate), platform detection (gh/tea), unfixable-issue taxonomy, templates offloaded to `references/ship-output-templates.md`.

### skills/spark-audit
**Verdict:** NEEDS-CHANGE
- [Med] [harness] SKILL.md:138 — load-bearing reference "Follow the Audit Five-Check Template in `plugins/personal-plugin/references/patterns/audit-recon-system.md`" is repo-relative, but documented usage is from `~/dev/personal/spark/` where that path doesn't exist (and installed plugins don't have the repo layout) → use `${CLAUDE_PLUGIN_ROOT}/references/patterns/audit-recon-system.md` with standard fallback.
- [Med] [harness] SKILL.md:205-215,237 — `/schedule create --name spark-audit-weekly --cron …` — no `/schedule` command exists in this repo or the current harness; scheduling is now Routines (`create_trigger`) or the `/loop` skill → rewrite (also inside the baseline template it emits).
- [Med] [triggering] SKILL.md:6-9 — `paths:` frontmatter unverified (see security-analysis); if inert, the Loop Guard section (13-21) guards a trigger that never happens.
- [Low] [harness] SKILL.md:5 — `Agent` in allowed-tools; cross-check the exact dispatch-tool name (research-topic uses `Task` for the same purpose — the two disagree).
- [Low] [context-economy] SKILL.md:231 — "create it using the template in spark-recon/SKILL.md" — fragile cross-skill pointer; move template to a shared reference.
- Good: Trust Boundary (fixed command allowlist, reference files never source commands) is excellent prompt-injection hygiene; check configs dated and self-annotating.

### skills/spark-recon
**Verdict:** NEEDS-CHANGE
- [Med] [harness] SKILL.md:21-23 — same load-bearing repo-relative path → `${CLAUDE_PLUGIN_ROOT}`-relative.
- [Med] [harness] SKILL.md:224-237,306-310 — `/schedule` integration (and Automation Schedule table in the emitted SPARK_BASELINE template) references a nonexistent command → Routines/`/loop`.
- [Med] [harness] SKILL.md:5 vs 19,247 — `allowed-tools` grants `Bash(ssh:*)` and `Bash(curl:*)` while the skill's own trust boundary asserts "this skill runs no SSH/Bash commands at all… never touches the Spark system" → remove `Bash(ssh:*)` (and curl if WebFetch covers the Firestore REST calls); the grant contradicts the security invariant.
- [Med] [stale-content] SKILL.md:170,184 — console report template says "Top FP8 **Qwen3.5**" / "No new models beyond **Qwen3.5**" while the config (line 62) and Check 4 say Qwen3.6; baseline trigger table line 299 likewise "Qwen4 OR Qwen3.5 successor" — leftover from the previous model generation → sync to Qwen3.6 or parameterize on `current_model`.
- [Low] [triggering] SKILL.md:4,6-8 — `disable-model-invocation: true` with `paths:` auto-trigger + description trigger text; same verification/consistency issue as spark-audit.
- Good: untrusted-content trust boundary for fetched web data, per-check fallback chains (Firestore → browser MCP → WebFetch → WebSearch), fail-one-continue-rest error handling.

### skills/spec-to-prototype
**Verdict:** MINOR
- [Med] [harness] SKILL.md:30,62 — "Ask clarifying questions **one at a time**, multiple choice preferred" is a forced-serial anachronism; AskUserQuestion presents multiple structured questions in one interaction → batch the 3-5 essential questions via AskUserQuestion, one-at-a-time as fallback.
- [Low] [harness] SKILL.md:74,19 — depends on invoking the `frontend-design` skill, not bundled in this plugin and possibly absent → add graceful fallback.
- [Low] [effort] `effort: high` defensible; with Opus 5, `medium` likely suffices — optional.
- Good: dot-graph process, build rules, common-mistakes table, browser-test loop compact and current; description has excellent trigger/anti-trigger coverage.

### skills/summarize-feedback
**Verdict:** MINOR
- [Med] [prompt-style] SKILL.md:90-110 — "Context Size Guardrail" hard-codes 100-entry batching, batches of 25, and a "60% of estimated context window" warning — calibrated for a 200K-era model. On a 1M-token window the guardrail triggers far too early and forces a meta-synthesis pass ("roughly doubles synthesis time") that's rarely needed → raise thresholds substantially or make the check qualitative.
- [Low] [prompt-style] SKILL.md:8,112-114 — "synthesize them with Claude… Feed all structured feedback entries to Claude" — orchestrator-era phrasing; the skill *is* the model doing inline synthesis. Cosmetic. (The rigid JSON output schema is justified — the docx generator consumes it.)
- [Low] [effort] `effort: high` appropriate for evidence-grounded synthesis; keep.
- Good: Notion MCP prerequisite checks, evidence-citation requirements, bundled-tool invocation pattern (PYTHONPATH per house convention) all correct.

### skills/task-sync
**Verdict:** OK
- [Low] [harness] SKILL.md:16 — `allowed-tools: … Bash` unscoped; could tighten since the invocation surface is fully known — optional hardening.
- Good: **the model skill in the set** — current-era design (plan→decide→apply, tool owns all mutations, human-in-the-loop only where judgment is needed, four tight reference files, folded description within limits, `effort: medium` correctly calibrated). No model references, no anachronisms.

### skills/ultra-plan
**Verdict:** NEEDS-CHANGE
- [High] [effort/prompt-style] SKILL.md:9 — bare "`ultrathink`" magic keyword as line 1 of the body, and **no `effort:` frontmatter at all** on the repo's deepest-reasoning skill. The thinking-keyword hack is a pre-adaptive-thinking mechanism; the sanctioned lever is now the `effort` field → delete `ultrathink`, add `effort: max` (or `high`).
- [Med] [prompt-style] SKILL.md:120-385 — phase numbering internally inconsistent from a past renumbering: Phase 1 ends with "Present Phase 2 findings" (142); Phase 2's subsections are 3a/3b/3c (177-190); Phase 3 opens "for each change set from Phase 3" (196) and its ADR section cites "Phase 2 investigation findings"/"Phase 4" for its own content (231-233); Phase 5's subsections are 6a-6e; error handling cites "the approved Phase 5 summary" for the Phase 4 report (385). A rigid follow-every-phase workflow with contradictory cross-references invites mis-execution → renumber consistently.
- [Med] [tier-routing] SKILL.md:89,236,244 — "L0-L1 scope per plan-gate classification", "L3+ tasks", "L4+ tasks" — plan-gate defines no L-level taxonomy (it routes via Paths A-F); the referenced classification doesn't exist anywhere in scope → define the L-levels inline or map to plan-gate's actual paths.
- [Low] [prompt-style] SKILL.md:11 — "This is a rigid workflow — follow every phase in order. Do not skip phases" then Phase 0 defines three skip conditions and Phase 1 a scale gate; the absolutist framing fights the actual design; soften to match.
- Good: sub-agent investigation with clustering + `run_in_background` parallel dispatch and graceful degradation (169) is current harness practice; interaction-mapping-before-solutions discipline is the skill's real value.

### skills/unlock
**Verdict:** MINOR
- [Med] [triggering] SKILL.md:3-4 vs 169-176 — `disable-model-invocation: true`, yet description says "Suggest (do not auto-run) when…" (dead prose) **and** the "Proactive trigger before research" example shows Claude "Runs /unlock automatically", which the flag explicitly forbids → reconcile: if unlock should be auto-suggested before research-topic/visual-explainer (both tell users to run it), drop the flag; otherwise delete the proactive example and trigger prose.
- [Low] [harness] SKILL.md:88-117 — export mechanism assumes a persistent shell across Bash calls; on harnesses where shell state doesn't persist (e.g., remote/web sessions), sourced exports vanish → add a note or `--print-exports` fallback.
- [Low] [effort] no `effort:`; mechanical → `effort: low` optional.
- Good: shlex.quote/no-eval security posture, key-name validation, never-print-values discipline exemplary.

### skills/visual-explainer
**Verdict:** MINOR
- [Med] [harness] SKILL.md:40,116 — documents the Gemini override as "`$GOOGLE_IMAGE_MODEL` env var", but the tool actually reads `VISUAL_EXPLAINER_GEMINI_MODEL` (config.py:364); setting the documented variable does nothing → fix SKILL.md to the real name. Also document the Claude-side override `VISUAL_EXPLAINER_CLAUDE_MODEL` (config.py:365), currently undocumented.
- [Med] [triggering] SKILL.md:3-6 — `disable-model-invocation: true` + "Suggest when — user has document/report/concept to visualize…" dead trigger prose; same systematic contradiction → pick one behavior.
- [Low] [tier-routing/good] Tool defaults `claude-sonnet-5` everywhere — current and correctly tiered for the vision/refinement loop; env-overridable per ADR-0005. SKILL.md's "Claude Sonnet Vision" prose (line 11) consistent. (See Section F for the recommended analysis/eval knob split.)
- [Low] [effort] `effort: high` for a skill that mostly shepherds a Python pipeline through interactive menus → `medium` likely sufficient.
- [Low] [harness] SKILL.md:233-282 — Phase 5/6 numbered-menu prompts ("Select style [1-4]") are AskUserQuestion candidates.
- [Low] [stale-claims] SKILL.md:53-58 — "Tested Results" block (score ranges, retry counts) measured under the older evaluator model; re-baseline or date-stamp.

### skills/wiki
**Verdict:** OK
- [Low] [effort] no `effort:`; `ingest`/`query` involve genuine cross-page synthesis → `effort: medium` optional.
- Good: dual-layout detection with contract-wins deference (AGENTS.md governs), delegate-to-`tools/lint.py`-instead-of-reimplementing, marker-vocabulary uncertainty handling, ingest-lessons checklist — current best practice. No model references, no anachronisms, no injections.

## Summary table

| Skill | Verdict | High | Med | Low |
|---|---|---|---|---|
| new-project | MINOR | 0 | 1 | 2 |
| plan-gate | OK | 0 | 0 | 2 |
| prime | NEEDS-CHANGE | 2 | 0 | 2 |
| release-plugin | MINOR | 0 | 1 | 3 |
| research-topic | NEEDS-CHANGE | 2 | 2 | 2 |
| security-analysis | MINOR | 0 | 2 | 2 |
| ship | NEEDS-CHANGE | 1 | 3 | 2 |
| spark-audit | NEEDS-CHANGE | 0 | 3 | 3 |
| spark-recon | NEEDS-CHANGE | 0 | 4 | 2 |
| spec-to-prototype | MINOR | 0 | 1 | 3 |
| summarize-feedback | MINOR | 0 | 1 | 3 |
| task-sync | OK | 0 | 0 | 2 |
| ultra-plan | NEEDS-CHANGE | 1 | 2 | 2 |
| unlock | MINOR | 0 | 1 | 3 |
| visual-explainer | MINOR | 0 | 2 | 4 |
| wiki | OK | 0 | 0 | 2 |
| **Totals** | 6 NC / 7 MINOR / 3 OK | **6** | **23** | **39** |

## Themes (skills M–Z)

(1) The only stale Claude model reference is research-topic's `claude-opus-4-8` default, but the deeper problem is mechanism, not ID: its `thinking.budget_tokens` depth mapping 400s on the entire current model family, so the Claude research leg is broken today — migrate to `output_config.effort` when bumping to `claude-opus-5`. (2) Issue #183 confirmed in prime (7 injections) and ship (6 injections); ship additionally has a broken diff-size computation that permanently disables its large-diff safety gate. (3) The `disable-model-invocation` + "Suggest when…" contradiction spans six more skills here (new-project, release-plugin, ship, unlock, visual-explainer, spark-recon). (4) Effort calibration inverted in one place: the deepest-reasoning skill (ultra-plan) has no `effort` and relies on a legacy `ultrathink` keyword, while plan-gate's `low` is exactly right. (5) Portability/currency debt clusters in the spark pair: repo-relative reference paths that break at the documented run location, a fictional `/schedule` command, and the unvalidated `paths:` frontmatter key (also security-analysis) — per the house negative-test rule, that key must be proven live or the guard flows built on it are illusory. Conversely, task-sync, wiki, and plan-gate need essentially nothing; visual-explainer's Python tool is already correctly on `claude-sonnet-5` — only its SKILL.md env-var documentation is wrong.

---

# Section D — bpmn-plugin & slide-gen (all components)

### bpmn-plugin/skills/bpmn-generator (SKILL.md, 494 lines)
**Verdict:** NEEDS-CHANGE
- [Med] [prompt-style/harness] SKILL.md:104-227 — "For EVERY clarifying question, use this EXACT format" + A/B/C/D/E options + a hand-rolled REPL of session commands (`help`/`status`/`back`/`skip`/`quit`, 186-219) is a pre-AskUserQuestion anachronism. Opus 5 handles adaptive clarification natively → replace the rigid text protocol with AskUserQuestion (add to `allowed-tools`), keep the 7-phase checklist as a coverage guide, drop the simulated command interpreter. The "Adaptive Questioning" section (221-227) already concedes judgment should drive this.
- [Med] [context-economy] SKILL.md:104-227 duplicates `references/clarification-patterns.md:7-28` (same exact-format template) — body at 494/500 lines with no headroom → trim the Q&A framework to a summary + pointer.
- [Med] [harness] SKILL.md:239,256,262,299,482-495 — reference paths inconsistent AND wrong: some `references/bpmn-elements.md`, others `../references/...`. From the skill dir the real location is `../../references/` (plugin root) → standardize on `${CLAUDE_PLUGIN_ROOT}/references/...` with plugin-root fallback, as personal-plugin skills already do.
- [Med] [effort] frontmatter — no `effort:`; genuine in-session generation (element mapping, DI coordinate math, validation) → add `effort: high` (or `medium`) — the one bpmn/sg skill where extra reasoning budget under Opus 5 pays off directly.
- [Low] [stale-model] SKILL.md:461-468 — performance table ("Simple ... 1-3 minutes", "Complex ... 8-15 minutes") encodes duration claims measured on an older model era → drop or relabel as rough guidance.
- [Low] [doc-drift] SKILL.md:344 `exporterVersion="2.0"` vs `templates/bpmn-skeleton.xml:24` `exporterVersion="1.1"` → align.
- [Low] [triggering] frontmatter:11 — `argument-hint` omits the documented `--preview` flag (line 62) → add.
- Good: `name` matches dir; description (582 chars) carries all triggers plus explicit "Do NOT use for" boundary vs bpmn-to-drawio; validation checklist and error handling are judgment-scaffolding, not micromanagement; zero `` !`git ...` `` injections; zero stale Claude model references.

### bpmn-plugin/skills/bpmn-to-drawio (SKILL.md, 341 lines)
**Verdict:** NEEDS-CHANGE
- [High] [doc-drift/harness] SKILL.md:93-98,117-133,136-148 — layout-decision logic predates the bundled tool's own v4.3.0/4.3.1 fixes. The skill instructs a manual `grep -q "bpmndi:BPMNDiagram"` HAS_DI check and explicit `--layout=preserve`/`--layout=graphviz` selection, but the CLI now defaults to `--layout auto` (cli.py:54-58), which resolves preserve-vs-graphviz using **complete**-DI detection. The skill's all-or-nothing grep reproduces exactly the partial-DI bug (#143) that 4.3.1 fixed — "HAS_DI=true → can skip Graphviz with `--layout=preserve`" strands DI-less shapes at (0,0) on partial-DI files → rewrite Steps 4/5: default invocation with no `--layout` flag (auto); keep `--layout=preserve` only as an explicit no-Graphviz escape hatch with the partial-DI caveat.
- [Med] [harness] SKILL.md:239 — troubleshooting says `bpmn2drawio input.bpmn output.drawio --verbose`, a bare command that only exists after `pip install -e .`; the skill's own invocation pattern is `PYTHONPATH="$TOOL_SRC" python -m bpmn2drawio ...` → fix the snippet.
- [Low] [effort] frontmatter — no `effort:`; mostly mechanical tool invocation → `effort: low` (or `medium` weighting the manual-conversion fallback, 297-320).
- [Low] [harness] SKILL.md:170,176,210,216,301-303,336-341 — same `../references/` / `../templates/` path issue as bpmn-generator.
- [Low] [triggering] frontmatter:11 — `argument-hint: "<bpmn-file-path>"` — workflow also takes output path/theme/layout → extend.
- Good: `${CLAUDE_PLUGIN_ROOT}` tool-path pattern (33-39) matches house rules; progressive disclosure to `bpmn2drawio-reference.md` is the right shape; dependency-check-then-ask matches CLAUDE.md.

### bpmn-plugin/.claude-plugin/plugin.json
**Verdict:** OK — v4.3.1 matches marketplace.json; no `tools`/`hooks` keys; no model references.

### bpmn-plugin/README.md
**Verdict:** MINOR
- [Med] [doc-drift] README.md:28 — "Version 4.2.0" vs plugin.json/marketplace 4.3.1 → update (consider adding plugin READMEs to the README-sync CI check that guards the root README).

### bpmn-plugin/references/ (skim)
**Verdict:** MINOR
- [Med] [doc-drift] bpmn2drawio-reference.md:30 — CLI table lists `--layout` choices `graphviz, preserve`, default `graphviz`; actual CLI is `auto|graphviz|preserve`, default `auto` → update (it's the authoritative CLI reference the skill defers to, so it currently reinforces the skill's stale logic).
- [Low] [doc-drift] bpmn2drawio-reference.md:129 — Python API example pins `layout="graphviz"`; should mention `auto`.
- Good: bpmn-elements.md, bpmn-elements-reference.md, xml-namespaces.md, markdown-parsing-guide.md, clarification-patterns.md, BPMN-to-DrawIO-Conversion-Standard.md contain zero model-era references or prompt-style boilerplate; archive/ correctly quarantined with README.

### bpmn-plugin/templates/ and examples/ (skim)
**Verdict:** OK
- [Low] [doc-drift] templates/bpmn-skeleton.xml:24 `exporterVersion="1.1"` vs SKILL.md's required "2.0" → align one direction. Everything else content-only; no model refs.

### bpmn-plugin/tools/bpmn2drawio/ (docs/model-ref check only)
**Verdict:** MINOR
- [Med] [doc-drift] README.md:47-66 — usage section never mentions the `auto` layout mode that is now the default; "All options" example shows `--layout=graphviz` only → add `auto`.
- [Low] [doc-drift] README.md:4 — "Python 3.9+" badge vs pyproject.toml `requires-python = ">=3.10"` → fix badge.
- [Low] [harness] VISUAL_TESTING_WORKFLOW.md:23-34 — "Claude navigates to app.diagrams.net... takes screenshots" assumes browser-automation tooling without naming which → name the required harness capability.
- Good: zero model IDs anywhere in the Python tool or docs; pyproject deps/lockfiles current per 4.2.0 CVE pass.

### slide-gen/skills/sg-research
**Verdict:** MINOR
- [Med] [effort] (FAMILY finding, applies to all 8 sg-* skills) — no `effort:` frontmatter on any sg-* skill. Thin wrappers whose heavy lifting happens in the external `sg` engine; under an Opus 5 primary, default effort overspends on mechanical shell-outs → add `effort: low` to all eight (sg-full-workflow arguably `medium` for orchestration/resume judgment).
- [Low] [prompt-style] SKILL.md:3,10 — "using Claude Agent SDK" is engine-internal detail in the trigger description; drift-prone → optional trim.
- Good: ADR-0008 preflight line present and current; dynamic injections all guarded (`|| echo`) — no bug-#183 exposure anywhere in either plugin.

### slide-gen/skills/sg-outline
**Verdict:** MINOR
- [Med] [stale-model] SKILL.md:10 — "Uses Claude with extended thinking (budget_tokens=4096)" is a model-era engine internal baked into the skill doc; the number lives (and will change) in the private `sg` engine → describe the behavior ("deep-reasoning outline pass"), not the parameter.
- [Low] [effort] — family `effort: low`.

### slide-gen/skills/sg-draft
**Verdict:** MINOR
- [Med] [stale-model/prompt-style] SKILL.md:10,49-54 — "one API call per slide (not 4 separate calls)", "batches of 4", "rolling 5-slide context window", "Temperature 0.5" are Claude-3/4-era cost/context mitigations documented as skill behavior → collapse "How It Works" to intent-level description; re-evaluate the batching strategy in the `sg` engine (out of repo).
- [Low] [effort] — family `effort: low`.

### slide-gen/skills/sg-optimize
**Verdict:** MINOR
- [Med] [stale-model] SKILL.md:10,48 — "extended thinking (budget_tokens=4096, temperature=1.0 required)": the "temperature=1.0 required" constraint is an old-generation extended-thinking requirement; stating it as current fact will mislead once the engine moves to Claude 5 → remove parameter-level claims.
- [Low] [stale-model] SKILL.md:50-52 — "Representative sampling for decks >15 slides" (context-size workaround) and "Assistant prefill: Forces structured JSON" (legacy technique; structured outputs are standard now) — re-check against a Claude 5 engine; delete from the skill doc either way.
- [Low] [triggering] SKILL.md:33 — "`--output` (default: overwrites input with `_optimized` suffix)" self-contradictory (overwrite vs suffix); Output section (64) hedges both ways → state the actual default.
- [Low] [effort] — family `effort: low`.

### slide-gen/skills/sg-validate-graphics
**Verdict:** OK — cleanest of the family. Only the shared `effort: low` addition. Preflight current, description/argument-hint accurate, `.graphics_validated` marker documented.

### slide-gen/skills/sg-generate-images
**Verdict:** MINOR
- [Med] [stale-model] SKILL.md:56 — "**Gemini Pro** (`gemini-3-pro-image-preview`)": a dated, preview-suffixed image-model ID in prose (July 2026). Doesn't gate behavior (real ID lives in the external engine) but is exactly the doc that drifts → verify against the current engine; update or drop the literal ID.
- [Low] [stale-model] SKILL.md:71-73 — cost estimates (~$0.10/image, ~$2.00/deck) tied to that model's pricing → mark approximate or refresh alongside the ID.
- [Low] [triggering] frontmatter:3 — description invites proactive use of a step that spends real Google API money; `.graphics_validated` gate mitigates, but weigh tempering proactive invocation.
- [Low] [effort] — family `effort: low`.
- Good: SKILL.md:89-91 "Related Gemini Image Path" note is exemplary — explicitly names the dual-maintenance obligation with personal-plugin's visual-explainer; use it when refreshing the model ID.

### slide-gen/skills/sg-build
**Verdict:** OK — accurate prerequisites (correctly no ANTHROPIC key needed), guarded injections, custom-template docs concise. Only the family `effort: low`.

### slide-gen/skills/sg-full-workflow
**Verdict:** MINOR
- [Low] [harness] SKILL.md:69-75 — the Quick Path (`sg full-workflow ... --no-interactive`) is a long-running foreground Bash call; modern harness supports `run_in_background` + monitoring → background the non-interactive run so a 20-slide image run doesn't block the session.
- [Low] [effort] — family finding; `medium` defensible here.
- Good: the ADR-0008 reference implementation — layered preflight (injected check + Step 0 + verbatim owner-only message + mid-pipeline fallback row) current with README and ADR wording. Serial step ordering is correct, not an anachronism: every stage consumes the previous stage's artifact; per-image parallelism already lives in the engine. Nothing to parallelize at the skill layer.

### slide-gen/skills/build-cfa-deck (SKILL.md, 325 lines, effort: high)
**Verdict:** NEEDS-CHANGE
- [Med] [harness] SKILL.md:72-79 — Step 2's primary snippet is dead code: calls `os.path.expanduser(...)` on line 74 but `import os` appears on line 78 (after use), guaranteeing NameError, so the `||` fallback (which omits placeholder **types**) always runs → fix import order and delete the fallback, or keep only one correct snippet.
- [Med] [context-economy] SKILL.md:157-269 — ~110 lines of inline python-pptx code including two overlapping slide-removal implementations: `remove_samples` (187-203) and the "use this reliable approach" `remove_all_slides` (253-269). Keeping the superseded one invites the model to pick the flaky path → delete `remove_samples`; move the pattern block to `references/` or a shipped helper script.
- [Med] [doc-drift] SKILL.md:18-34,58,166 — all assets hard-coded to `~/dev/stratfield/slide-generator/examples/...`, a machine-specific path outside both this repo and the documented `sg` dependency → parameterize (e.g. `CFA_ASSETS_DIR` env var with current default), note the asset prerequisite next to the ADR-0008 story.
- [Low] [harness] frontmatter:5 — `allowed-tools` grants `Agent` but the workflow never dispatches a subagent; `Glob` absent though asset discovery could use it → drop `Agent` or use it; add `Glob`.
- [Low] [prompt-style] SKILL.md:51,150 — "Follow these steps exactly. Do not skip or reorder." mostly justified (build pipeline), but hard-coded "all 28 sample slides" will rot with any template update → "remove all existing sample slides".
- [Low] [harness] SKILL.md:143,274 — writes the build script to `/tmp/build_cfa_deck.py`; house convention is `.tmp/` → align.
- Good: `effort: high` correctly calibrated — the one slide-gen skill where the session model IS the content engine; "No API key needed — content generation happens in this Claude Code session" is exactly the right Opus-5-era framing; content-density/color-sequencing rules are genuine brand constraints.

### slide-gen/.claude-plugin/plugin.json + README.md
**Verdict:** OK — v1.2.0 consistent across plugin.json/marketplace/README; "External Dependency (REQUIRED)" section current, honest, matches ADR-0008; "9 Skills" list complete including build-cfa-deck.

### slide-gen/CHANGELOG.md (+ ADR-0008 currency note)
**Verdict:** MINOR
- [Low] [doc-drift] CHANGELOG.md:16 — "All 8 skills (...)" then lists nine names → "All 9 skills".
- [Med] [doc-drift] docs/adr/0008-slide-gen-dependency-model.md:9 — claims "Every skill body invokes `sg <subcommand>` directly; none of the ... logic lives inside `plugins/slide-gen/`" — false for build-cfa-deck (in-session python-pptx, no `sg`, no API key), which postdates the ADR framing → one-sentence carve-out so the ADR's dependency claim stays accurate.

## Summary table

| Component | Verdict | Highest finding |
|---|---|---|
| bpmn-generator SKILL.md | NEEDS-CHANGE | Med: pre-AskUserQuestion Q&A protocol; broken/inconsistent reference paths; at 494/500 line budget |
| bpmn-to-drawio SKILL.md | NEEDS-CHANGE | High: layout guidance contradicts bundled tool's v4.3.x `auto` default; re-teaches fixed bug #143 |
| bpmn plugin.json | OK | — |
| bpmn README.md | MINOR | Med: version 4.2.0 vs actual 4.3.1 |
| bpmn references/ | MINOR | Med: CLI reference table missing `auto` layout |
| bpmn templates+examples | OK | Low: exporterVersion mismatch |
| bpmn2drawio tool docs | MINOR | Med: README lacks `auto` mode; Python badge 3.9 vs 3.10 |
| sg-research | MINOR | Med (family): no `effort:` on any sg-* skill |
| sg-outline | MINOR | Med: `budget_tokens=4096` model-era internal |
| sg-draft | MINOR | Med: batching/temperature/context-window internals in doc |
| sg-optimize | MINOR | Med: "temperature=1.0 required" old-generation constraint |
| sg-validate-graphics | OK | Low: effort only |
| sg-generate-images | MINOR | Med: dated `gemini-3-pro-image-preview` ID in prose |
| sg-build | OK | Low: effort only |
| sg-full-workflow | MINOR | Low: consider backgrounded long runs; best-in-class preflight |
| build-cfa-deck | NEEDS-CHANGE | Med: dead code snippet; duplicate removal snippets; machine-specific asset paths |
| slide-gen plugin.json + README | OK | — |
| slide-gen CHANGELOG (+ADR-0008) | MINOR | Med: ADR-0008 misdescribes build-cfa-deck |

## Themes (bpmn + slide-gen)

Neither plugin contains a single stale Claude model ID or ADR-0005 violation — the alias discipline held completely; every "model staleness" finding is second-order: engine internals (budget_tokens, temperatures, batch sizes, assistant-prefill, a preview-suffixed Gemini ID) copied into sg-* skill docs where they will silently drift from the private engine, and duration/cost tables measured in an older-model era. The single highest-risk finding is intra-plugin doc drift, not model drift: bpmn-to-drawio's SKILL.md and its CLI reference both predate the bundled tool's own v4.3.x `auto`-layout upgrade and actively re-teach the partial-DI failure mode the tool just fixed. Prompt-style anachronisms concentrate in one place (bpmn-generator's simulated Q&A REPL, replaceable with AskUserQuestion under Opus 5); the pipelines' serial structure is data-dependent and correct — no parallelization changes warranted. Effort calibration is the cheapest win: one line (`effort: low`) across eight sg-* wrappers, `effort: high` for bpmn-generator, with build-cfa-deck already calibrated correctly.

---

# Section E — implementer agents, arch-review agents, references/, hooks

### .claude/agents/haiku-implementer.md
**Verdict:** OK
- [Low] [tier-routing] Task profile (renames, format conversions, regex edits, boilerplate, classification, lookups, small summarization) still correctly scoped for Haiku 4.5, which remains the small/fast tier. ESCALATE criteria appropriate. No change needed.

### .claude/agents/sonnet-implementer.md
**Verdict:** MINOR
- [Med] [tier-routing] lines 4,13-14 — profile caps sonnet at "single-file refactors" and "straightforward bug fixes," and the description escalates on "multi-file refactoring." That boundary was calibrated for Sonnet 4.x; Sonnet 5 is near-Opus on coding/agentic work → widen the profile to include multi-file changes with clear specs, moderately complex diagnosed bug fixes, and feature work whose API surface is described; make sonnet the default for most implementation work (plan-template already defaults to `sonnet`, so widening here shifts more items away from opus without any plan change).
- [Med] [tier-routing] line 31 — ESCALATE trigger "Multi-file refactoring with system-wide coupling not anticipated in the plan" now over-fires → recalibrate to escalate only on unresolved architectural decisions, genuinely ambiguous requirements, or coupling the plan did not anticipate; a multi-file change per se is no longer an escalation reason.
- [Low] [adr-0005] `model: sonnet` frontmatter — compliant, resolves to Sonnet 5 at dispatch. Good.

### .claude/agents/opus-implementer.md
**Verdict:** MINOR
- [Med] [tier-routing] lines 4,27 — "This is the highest tier — there is no escalation above Opus." With `fable` now existing above `opus` in the alias set, this reads as stale rather than deliberate → keep opus as the top routing tier (Fable is premium-priced and not the default upgrade path), but add one sentence documenting the choice, e.g. "`fable` exists above this tier but is deliberately outside the /implement-plan rotation (cost) — the orchestrator may only re-dispatch to it on explicit user request." Prevents a future reader from "fixing" it blindly in either direction.
- [Med] [prompt-style] lines 11-17 — calibrate for Opus 5's behavioral shifts: (a) add a scope-discipline line ("deliver what the plan asks at the intended scope; make routine judgment calls, don't widen or transform the item") — Opus 5 is more prone to expanding task scope; (b) add "do not sub-delegate to subagents — you are the leaf implementer" — Opus 5 reaches for subagents far more readily than 4.x and the agent has unrestricted tools.
- [Low] [good] The "Return minimal output (max 5 sentences)" constraint is well-matched to Opus 5 — keep.

### plugins/personal-plugin/agents/ (all 10 architect agents)
**Verdict:** OK
- [Low] [adr-0005] all 10 files, line 5 — `model: inherit` + `effort: high` in every agent; zero pinned IDs. Fully ADR-0005 compliant. Explicitly good.
- [Low] [prompt-style] all 10, "Process" sections (e.g. data-architect.md:34-139, security-architect.md:43-137) — ~100 lines of prescriptive grep/find scripts per agent is micro-managed for a frontier model. They do function as domain checklists, so optional: reframe the command blocks as "suggested starting probes — adapt to the codebase" and let the model consolidate. Not blocking.
- [Low] [prompt-style] all 10, Instrumentation + Meta Output — the manual START_TIME echo / compute-runtime-from-ISO-timestamps choreography is busywork a current model handles fine but could be one sentence. Harmless; leave unless touching anyway.
- [Low] [good] sre-operator.md — gotchas verified live 2026-07-12; precise negative-space instructions ("act only on the specific task, not ambient opportunities") are exactly the right style for Opus 5.

### references/research-models.md
**Verdict:** NEEDS-CHANGE
- [High] [stale-model] lines 19,33,64 — default `claude-opus-4-8` (last verified 2026-07-08) → `claude-opus-5` (same pricing tier, drop-in per migration guidance; cost table stays roughly valid).
- [High] [harness] lines 48-53 — depth-mapping column "Anthropic budget_tokens" (4,000/10,000/32,000) is functionally broken: `thinking: {type:"enabled", budget_tokens:N}` returns **400 on Opus 4.8 and Opus 5** (removed, not deprecated) → replace with an `output_config.effort` mapping (e.g. Brief→`medium`, Standard→`high`, Comprehensive→`max`) and adaptive thinking.
- [Med] [stale-model] line 19 — "Synchronous (extended thinking)" mode label → "Synchronous (adaptive thinking + effort)".
- [Low] [stale-model] lines 34-35 — OpenAI/Google defaults last verified 2026-03-31; re-verify.

### references/research-provider-protocols.md
**Verdict:** NEEDS-CHANGE
- [High] [harness] lines 27-29 — the copy-pasteable Anthropic request body sends `"thinking": {"type": "enabled", "budget_tokens": [BUDGET_TOKENS]}`. **Every dispatch of the Claude research leg 400s** on the current default model and on Opus 5 → change to adaptive thinking + `"output_config": {"effort": "[EFFORT_LEVEL]"}`; on Opus 5 the thinking field can simply be omitted.
- [Med] [stale-model] line 13 — "Extended-thinking requests at higher depths (`budget_tokens` up to 32,000)…" → reword in effort terms; the `--max-time 600` rationale still holds (Opus 5 turns can run minutes at high effort — keep or raise the timeout).
- [Low] [good] submit/poll error-handling discipline (fast-fail before polling, bounded curl, Retry-After honoring) solid and current.

### references/api-key-setup.md
**Verdict:** MINOR
- [Med] [stale-model] line 36 — example `ANTHROPIC_MODEL=claude-opus-4-8` → `claude-opus-5`.
- [Low] [prompt-style] line 19 — "Claude Extended Thinking" purpose label → "Claude deep research (adaptive thinking)".
- [Low] [harness] lines 53-54 — a note paragraph is wedged between two table rows, breaking the markdown table. Cosmetic fix.

### references/common-patterns.md
**Verdict:** NEEDS-CHANGE
- [High] [stale-model][propagation] line 164 — `model: claude-opus-4-5   # or claude-sonnet-4-5, claude-haiku-3-5, etc.` — pinned IDs, one of which (`claude-haiku-3-5`) is **retired** (Feb 2026). This is the "canonical field catalog" that `/new-skill` links, so it propagates into every new skill → replace with tier aliases: `model: opus   # or sonnet, haiku, fable, inherit`.
- [Med] [adr-0005] lines 169-170 — gotcha "Model IDs change with releases; pin to a family name if you want automatic upgrade (check Claude Code docs for alias support)" hedges on the thing ADR-0005 already mandates → state directly: "Always use tier aliases (`haiku`/`sonnet`/`opus`/`fable`/`inherit`), never pinned IDs (ADR-0005)."
- [Med] [tier-routing] line 167 — "routing cheap triage steps to Haiku and expensive synthesis to Opus" is valid but incomplete → add that sonnet is the default workhorse (Sonnet 5 handles most synthesis) and opus is for judgment-heavy work.
- [Med] [harness][propagation] lines 176-259 — documents `paths:`, `hooks: pre/post`, `isolation: worktree`, `shell:` as skill frontmatter. Three of these (`paths`, `hooks`, `isolation`) are not in the repo's own CLAUDE.md optional-field list and are not corroborated by current Claude Code docs → verify each against `claude plugin validate --strict` / official docs; prune or clearly mark aspirational. Because this catalog feeds `/new-skill`, unverified fields multiply.
- [Low] [prompt-style] line 124 — "Canonical reference for late-2025 Claude Code features" → drop the dated framing.

### references/patterns/advanced-features.md
**Verdict:** NEEDS-CHANGE
- [High] [harness] line 132 — "**Gotcha — failure is silent:** If the command fails (non-zero exit), the output is empty — no error is surfaced to Claude." This is the confirmed wrong claim behind issue #183: unguarded `` !`git …` `` injections actually **abort the skill** in non-git dirs → rewrite the gotcha: dynamic-injection command failure can abort the skill outright; guard with `2>/dev/null || echo "unavailable"` (the `|| echo` advice in the same paragraph is the right fix for the wrong reason — keep the fix, correct the failure-mode description).
- [High] [stale-model][propagation] lines 51,57-58 — `model: claude-opus-4` example plus recommendations to "override to `claude-opus-4`" / "override to `claude-haiku-4`". `claude-opus-4` is a deprecated form and `claude-haiku-4` **never existed** → replace all three with tier aliases (`opus`, `haiku`); add `fable` to the mentioned set.
- [Med] [harness] lines 29,34-41 — `agent: Think | Code` capability profiles are not documented Claude Code agent types (only `Explore` and named custom agents corroborated) → verify or remove the Think/Code rows.
- [Med] [harness] lines 136-152 — `$CLAUDE_CONTEXT` ("active file/selection in the user's editor") is not a documented substitution variable → verify; if unconfirmed, remove and take the path via `$ARGUMENTS`.
- [Med] [harness][propagation] lines 64-111,156-171 — `isolation: worktree`, `paths:`, `hooks: pre/post` — same unverified-field concern as common-patterns.md. Verify against the harness before this "canonical reference" mints more copies.
- [Low] [prompt-style] line 3 — "added in late 2025" framing → drop the date.
- [Low] [stale-model] line 37 — "`Think` | Deep reasoning, extended thinking" — extended-thinking framing obsolete (adaptive thinking/effort).

### references/templates/skill.md
**Verdict:** NEEDS-CHANGE
- [High] [stale-model][propagation] line 12 — `# model: claude-opus-4   # override model for this skill…` — pinned, deprecated-model ID in the scaffolding template that every `/new-skill` run copies. **Highest-multiplication stale reference in the repo** → `# model: opus   # tier alias (haiku|sonnet|opus|fable|inherit) — never pinned IDs (ADR-0005)`.
- [Med] [harness] line 7 — comment `# disable-model-invocation: false   # true = no LLM call; pure-tool skill` misdescribes the field. Per CLAUDE.md: it prevents proactive model invocation and removes the description from session context; it does not make the skill "no LLM call" → correct the gloss.
- [Med] [harness] lines 11,39-40 — `agent: Explore | Think | Code` and `$CLAUDE_CONTEXT` — same unverified items as advanced-features.md, here inside the generated template.
- [Med] [harness][propagation] lines 15-27 — commented `paths:`/`hooks:`/`isolation:` blocks — verify or prune.
- [Low] [effort-enum] line 5 — `# effort: medium   # low | medium | high | max` — if the harness supports an `xhigh` level between high and max (as current API effort enums do), add it after verifying against `claude plugin validate --strict`; otherwise leave the documented four.

### references/new-skill-examples.md
**Verdict:** MINOR
- [Med] [harness] lines 128,150 — Example C leans on `$CLAUDE_CONTEXT` to identify the triggering file; unverified variable → fix alongside the catalog, or the worked example teaches a variable that expands to empty string.
- [Low] [harness] lines 101-110 — Example C's `paths:` auto-activation frontmatter depends on the unverified `paths:` field.
- [Low] [good] Examples A and B (tier-alias-free frontmatter, `context: fork` + `agent: Explore`, guarded `` !`cmd` `` pre-loads with bounded output) clean and current.

### references/plan-template.md
**Verdict:** MINOR
- [Med] [tier-routing] line 255 — Rule 17 rubric puts "multi-file refactors" categorically under opus. With Sonnet 5, well-specified multi-file work belongs in sonnet; opus reserved for ambiguous requirements, competing designs, cross-cutting debugging → recalibrate in lockstep with the sonnet-/opus-implementer profile edits (**three places must stay in sync: this rubric + the two agent files**).
- [Low] [tier-routing] line 253 — Execution Hints example shows `opus` for "phases needing a more capable model"; fine, but note that `fable` is intentionally not a plan tier (mirror the opus-implementer note).
- [Low] [good][adr-0005] lines 46-49,82,253 — Model Tier system uses only tier aliases mapped to the named implementer agents. Fully compliant.

### references/hooks/ (3 recipe files)
**Verdict:** NEEDS-CHANGE
- [Med] [harness][propagation] planning-stop-hook.md:13-21, session-start-hook.md:11-19, verification-post-edit-hook.md:11-21 — all three "copy and adapt" snippets use a flat top-level format (`{"Stop": [{"type": "command", …}]}`) that does not match the working format the repo's own `hooks/hooks.json` uses (`{"hooks": {"Event": [{"matcher": …, "hooks": [{…}]}]}}`). Copied verbatim, these recipes silently fail to load → rewrite all three snippets in the nested matcher/hooks format.
- [Med] [harness] verification-post-edit-hook.md:16,34 — relies on `$CLAUDE_TOOL_NAME` / `$CLAUDE_FILE_PATH` env vars; Claude Code delivers tool info as JSON on stdin (as the repo's real PreToolUse hook correctly does with `jq -r .tool_input.command`), and tool filtering belongs in the `matcher` field → replace env-var grep with matcher + stdin parse.
- [Med] [harness] verification-post-edit-hook.md:17 — `"timeout": 10000` — hook timeouts are in **seconds** (live hooks.json correctly uses 10 and 5); 10000 is a wrong-unit copy-paste hazard.
- [Low] [harness] planning-stop-hook.md:11 — "Add this to your project's `.claude/hooks.json`" — project hooks live in `.claude/settings.json` under the `hooks` key (plugins use `hooks/hooks.json`); correct the path.

### references/templates/planning.md
**Verdict:** MINOR
- [Med] [prompt-style][stale-model] lines 66-68 — "### Phase 1: Deep Analysis (Ultrathink) / Thoroughly analyze the target scope with extended thinking enabled" — "ultrathink" keyword magic and "extended thinking enabled" are pre-adaptive-thinking anachronisms; the template already sets `effort: high`, which is the current mechanism → drop the label and reword.

### references/templates/read-only.md
**Verdict:** MINOR
- [Low] [prompt-style] lines 19,62,231 — "DO NOT MAKE ANY CHANGES — ONLY ANALYZE AND REPORT" appears three times in all-caps → keep one instance (the `allowed-tools: Read, Glob, Grep` restriction already enforces it mechanically).

### references/templates/ — other 8 files (conversion, generator, interactive, utility, workflow, synthesis, brief, project-claude-md)
**Verdict:** OK
- [Low] [prompt-style] interactive.md:84,239 — "CRITICAL: Never batch items…" / "ONE AT A TIME — This is critical" — the constraint is load-bearing (interactive UX contract, forced-serial is *correct* here); duplicated all-caps emphasis could soften to a single statement. No functional change.
- [Low] [good] No model references, no stale harness claims in all eight.

### references/patterns/ — other 6 files (naming, validation, output, workflow, testing, logging, audit-recon-system)
**Verdict:** OK
- [Low] [harness] naming.md:35 — example "prefer `review-pr` over `code-review-pull-request`" cites a command deprecated 2026-04-21 → swap for a live command.
- [Low] [good] audit-recon-system.md tool-selection table (WebSearch/WebFetch/browser MCP/HF MCP, year-scoped queries) current and well-calibrated. Remaining five files model-agnostic.

### references/ — remaining 17 top-level files
**Verdict:** OK
- [Low] [good] No model references, no harness claims, no anachronisms. implement-plan-state-schema.md and create-plan-examples.md:359-361 use tier aliases correctly. anti-patterns.md items 10-11 (never claim tests pass without running; separate testing subagent) remain valid on Opus 5 — honesty-of-evidence scaffolding, not redundant tell-it-to-verify scaffolding; no change.
- [Low] [stale-model] flag-consistency.md:5 — "Last Updated: 2026-03-04" — content fine; refresh date when next touched.

### hooks/hooks.json + hooks/scripts/
**Verdict:** OK
- [Low] [good] hooks.json — correct nested matcher/hooks format, seconds-based timeouts (10/5), stdin JSON parsed with jq, `${CLAUDE_PLUGIN_ROOT}` used properly. No model references. **This is the file the broken recipe docs should be rewritten to match.**
- [Low] [harness] hooks/scripts/lab-notebook-gate.sh:7 — "Bypass: git commit --no-verify" is misleading: the gate is a PreToolUse hook that greps for "git commit", so `--no-verify` still trips it (`--no-verify` only bypasses git-native hooks). Either exempt `--no-verify` in the hook's grep or correct the comment (line 52 repeats it).

## Summary table

| File / Group | Verdict | High | Med | Low |
|---|---|---|---|---|
| haiku-implementer.md | OK | 0 | 0 | 1 |
| sonnet-implementer.md | MINOR | 0 | 2 | 1 |
| opus-implementer.md | MINOR | 0 | 2 | 1 |
| agents/ (10 architect agents) | OK | 0 | 0 | 4 |
| references/research-models.md | NEEDS-CHANGE | 2 | 1 | 1 |
| references/research-provider-protocols.md | NEEDS-CHANGE | 1 | 1 | 1 |
| references/api-key-setup.md | MINOR | 0 | 1 | 2 |
| references/common-patterns.md | NEEDS-CHANGE | 1 | 3 | 1 |
| references/patterns/advanced-features.md | NEEDS-CHANGE | 2 | 3 | 2 |
| references/templates/skill.md | NEEDS-CHANGE | 1 | 3 | 1 |
| references/new-skill-examples.md | MINOR | 0 | 1 | 2 |
| references/plan-template.md | MINOR | 0 | 1 | 2 |
| references/hooks/ (3 recipes) | NEEDS-CHANGE | 0 | 3 | 1 |
| references/templates/planning.md | MINOR | 0 | 1 | 0 |
| references/templates/read-only.md | MINOR | 0 | 0 | 1 |
| other templates/ (8 files) | OK | 0 | 0 | 2 |
| other patterns/ (6 files) | OK | 0 | 0 | 2 |
| remaining 17 top-level references | OK | 0 | 0 | 2 |
| hooks/hooks.json + scripts | OK | 0 | 0 | 2 |

## Themes (agents + references)

**First, the ADR-0005 machinery works where it was applied and fails where it wasn't:** every agent file (all 13) is clean tier-alias/`inherit` frontmatter, and the plan-template/implement-plan tier system is fully alias-based — but the documentation layer that teaches skill authors (`templates/skill.md`, `common-patterns.md`, `advanced-features.md`) still carries pinned, deprecated, retired, and in one case never-existent model IDs, and these are precisely the files `/new-skill` copies into every future skill — they multiply fastest and should be fixed first. **Second, the "late-2025 modern features" catalog has drifted from the actual harness:** the same three files (plus new-skill-examples.md and the hook recipes) document fields and variables (`paths:`, `hooks: pre/post`, `isolation: worktree`, `agent: Think/Code`, `$CLAUDE_CONTEXT`, `$CLAUDE_TOOL_NAME`, flat hooks.json, ms timeouts) that either contradict the repo's own working config and CLAUDE.md field list or can't be corroborated against current Claude Code — a verify-against-`claude plugin validate --strict`-and-prune pass is warranted, and the wrong "silent failure" injection claim (#183) needs an outright reversal. **Third, tier routing needs one coordinated recalibration, not scattered edits:** Sonnet 5's step-change means the sonnet/opus boundary should move up (multi-file-with-clear-spec → sonnet; opus reserved for ambiguity and architecture) in exactly three synchronized places — sonnet-implementer.md, opus-implementer.md, plan-template.md Rule 17 — plus a one-line deliberate-exclusion note for `fable` so "no escalation above Opus" reads as a decision rather than staleness. The only outright functional break found is the research pipeline's `budget_tokens` request body, which 400s on its own default model — convert to adaptive thinking + effort alongside the `claude-opus-5` default bump.

---

# Section F — Python tools, evals, CI, schemas, top-level docs

### plugins/personal-plugin/tools/visual-explainer/
**Verdict:** MINOR
- [High] [stale-test-id] tests/test_prompt_generator.py:57 — `PromptGenerator(api_key="test-key", model="claude-opus-4-20250514")` — retired ID (retired 2026-06-15). Mocked, so no runtime failure, but the only non-`claude-sonnet-5` Claude ID in the tool and propagates a dead ID → `claude-opus-5` (assertion `"opus" in gen.model.lower()` still passes).
- [Med] [default-choice] src/visual_explainer/config.py:344,365 — single `claude_model` knob (`claude-sonnet-5`, env `VISUAL_EXPLAINER_CLAUDE_MODEL`) drives ALL call sites: concept analysis (concept_analyzer.py:910), prompt generation (pipeline.py:144), image evaluation (pipeline.py:475). ID current; design stale for Opus-5-primary posture: analysis/generation (one-shot, quality-driving) and evaluation (high-volume vision loop) want different tiers → split into `claude_model` (default `claude-opus-5`) + `claude_eval_model` (default `claude-sonnet-5`), each env-overridable.
- [Low] [stale-comment] src/visual_explainer/image_evaluator.py:36 — "Sonnet is sufficient for vision, 5x cheaper than Opus" — Opus 4.x-era ratio; Opus 5 $5/$25 vs Sonnet 5 $3/$15 ≈ 1.7x → update comment; Sonnet 5 remains the right evaluator default.
- [Low] [no-override] src/visual_explainer/api_setup.py:229 — key-validation ping hardcodes `model="claude-sonnet-5"` inline (no env override) → `claude-haiku-4-5` better (1-token request, quality irrelevant), or route through config.
- [Low] [image-model] src/visual_explainer/config.py:340,364 — `gemini-3-pro-image-preview` — `-preview`-suffixed default in a shipped tool is suspect by July 2026; verify at next release per ADR-0005.
- [Low] [stale-doc] README.md:421-426 — cost table reflects pre-Sonnet-5 pricing → refresh alongside any default change.
- OK: prompt_generator.py:51, prompt_refiner.py:36, image_evaluator.py:37, conftest.py:120, test_image_generator.py:41 all consistently `claude-sonnet-5`.

### feedback-docx-generator / bpmn2drawio tools
**Verdict:** OK — no Claude/model references at all in either tool (source or tests). Nothing to update.

### references/api-key-setup.md
**Verdict:** NEEDS-CHANGE
- [Med] [stale-default] api-key-setup.md:36 — `ANTHROPIC_MODEL=claude-opus-4-8` documented `.env` example for the research pipeline; superseded → `claude-opus-5`. Must move in lockstep with `references/research-models.md:19,33,64` (pins `claude-opus-4-8`, last reviewed 2026-07-08).
- [Low] [era-language] line 19 — "Claude Extended Thinking" as the key's purpose — fixed-budget extended thinking deprecated on Opus 5 (adaptive thinking / effort) → reword.
- [Low] [non-Claude staleness] lines 37-38 — `o3-deep-research-2025-06-26` (13 months old) and `deep-research-pro-preview-12-2025` (a Dec-2025 preview ID) obviously dated → verify at next release.

### evals/
**Verdict:** MINOR
- OK: no Claude model IDs anywhere in evals/** — model-agnostic by design (README:3 scopes evals to survive "model upgrades"). Right structure.
- [Med] [calibration] evals/commands/assess-document.eval.md:17-18,29,52,61 — hard score bands ("Overall score between 3.5 and 4.5", "between 2.0 and 3.0") calibrated on prior model era; Opus 5 can legitimately score outside → re-baseline under Opus 5 or convert to the relative criterion already at line 140.
- [Med] [behavior-shift] evals/skills/description-triggers.eval.md (whole file) — auto-invocation/trigger expectations are the behavior class that shifts across model generations. The eval is the correct guard — flag as the FIRST suite to re-run after the model change; expect drift in "should activate" scenarios.
- [Low] [stale-dependency] evals/skills/research-topic.eval.md:34 — passes against config pinning `claude-opus-4-8`; no text change needed once research-models.md moves, but note the coupling.

### .github/workflows/ + scripts/
**Verdict:** OK
- No model IDs anywhere in validate.yml, test.yml, or scripts/*. Only pinned Anthropic artifact is the CLI (`validate.yml:326` — `@anthropic-ai/claude-code@2.1.204`), a tooling pin, deliberately pinned.
- [Med] [missing-guard] Nothing in CI or pre-commit asserts model names — ADR-0005's tier-alias rule for `.claude/agents/*.md` frontmatter is UNENFORCED: a pinned `claude-opus-4-20250514` in an agent file would pass validate.yml, scripts/pre-commit, and `claude plugin validate --strict` silently. Per E043 (negative-test every gate), add a small allowlist check (`haiku|sonnet|opus|fable|inherit`) to BOTH validate.yml and scripts/pre-commit — negative-tested with a deliberately pinned ID before wiring.

### schemas/
**Verdict:** OK
- No schema constrains a `model` field anywhere (command.json forbids extra frontmatter keys, but commands never carry `model`; no skill/agent frontmatter schema exists). Both `fable` and `claude-opus-5` would "pass" trivially — schemas neither block the optimization nor enforce ADR-0005. If the CI guard is added, schemas need no change; alternatively an agent-frontmatter schema with `"model": {"enum": ["haiku","sonnet","opus","fable","inherit"]}` is the schema-level home for the same rule.

### Top-level docs
**Verdict:** MINOR
- [Med] [contradicts-ADR] README.md:179-180 — ".claude/agents/ … Named implementer agents (haiku/sonnet/opus-implementer) — Model pinned in frontmatter" — "pinned" directly contradicts ADR-0005 and will mislead contributors → reword to "model: tier alias in frontmatter (never pinned IDs, ADR-0005)", matching CLAUDE.md:168-169. (update-readme.py does not generate this section — edit README directly.) If a `fable`-tier implementer is added, this listing needs it.
- [Low] [stale-model-name] CONTRIBUTING.md:389 — commit template `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>` — two generations stale; contributors stamp a stale name into history → current model name or generic placeholder.
- [Low] [stale-inventory] CLAUDE.md (Repository Structure skills list) — missing five live skills: archive-project, clear-prep, fleet-health, new-project, task-sync (29 dirs on disk vs 24 listed) → sync while editing.
- OK: CLAUDE.md:24 tier-alias bullet current (includes `fable`); QUICK-REFERENCE.md, TROUBLESHOOTING.md, WORKFLOWS.md, docs/PLUGIN-DEVELOPMENT.md, docs/RUNBOOK.md contain no model names/IDs or tier-routing guidance — nothing to update.

## ADR-0005 Python-tool model-default roll call

(Opus 5 $5/$25, Sonnet 5 $3/$15, Haiku 4.5 $1/$5 per Mtok)

| Call site | Default | Verdict | Recommend | Rationale |
|---|---|---|---|---|
| visual-explainer config.py:344,365 (`claude_model`, env-overridable; feeds concept analysis) | claude-sonnet-5 | Current ID; tier debatable | claude-opus-5 | Concept analysis runs once per document, determines everything downstream; Opus premium now only ~1.7x |
| prompt_generator.py:51 (DEFAULT_MODEL) | claude-sonnet-5 | Current | claude-opus-5 | Low-volume, quality-driving — a better prompt reduces expensive Gemini regeneration cycles |
| prompt_refiner.py:36 (DEFAULT_MODEL) | claude-sonnet-5 | Current | claude-opus-5 | Fires only on failed images; each failed refinement costs another Gemini generation + evaluation round — per-token savings false economy |
| image_evaluator.py:37 (DEFAULT_MODEL) | claude-sonnet-5 | Current — keep | claude-sonnet-5 | Highest-volume call (every image × every attempt), structured vision scoring; same high-res vision tier as Opus 5; latency/cost dominate. Fix stale "5x cheaper" comment |
| api_setup.py:229 (key-validation ping, hardcoded) | claude-sonnet-5 | Current ID; wrong tier | claude-haiku-4-5 | 1-token liveness check; quality irrelevant; add env override while touching |
| tests/test_prompt_generator.py:57 | claude-opus-4-20250514 | STALE — retired 2026-06-15 | claude-opus-5 | Dead ID, sole inconsistency; the `"opus" in model` assertion survives the swap |
| tests/conftest.py:120, tests/test_image_generator.py:41 | claude-sonnet-5 | Current | keep (track config if knob splits) | Fixtures mirror config default |
| feedback-docx-generator, bpmn2drawio | — | n/a | — | No model references |
| (adjacent doc: api-key-setup.md:36 + research-models.md:19,33,64) | claude-opus-4-8 | STALE | claude-opus-5 | Deep-research role is exactly the Opus-5-primary use case; drop-in upgrade at identical pricing |

Structural catch: one config value (`claude_model`) feeds analysis, generation, AND evaluation (pipeline.py:144,475), so "Opus for reasoning, Sonnet for evaluation" requires splitting that knob (plus second env var) — otherwise the per-module DEFAULT_MODEL constants are dead defaults applying only to direct construction.

## Summary table

| Area | Verdict | High | Med | Low |
|---|---|---|---|---|
| visual-explainer tool | MINOR | 1 | 1 | 4 |
| feedback-docx-generator / bpmn2drawio | OK | 0 | 0 | 0 |
| references/api-key-setup.md (+research-models.md) | NEEDS-CHANGE | 0 | 1 | 2 |
| evals/ | MINOR | 0 | 2 | 1 |
| CI + scripts | OK | 0 | 1 (guard gap) | 0 |
| schemas/ | OK | 0 | 0 | 0 |
| Top-level docs | MINOR | 0 | 1 | 2 |

## Themes (tools/evals/CI/docs)

Unusually good model hygiene: exactly one live stale Claude ID in scope (retired `claude-opus-4-20250514` in a mocked test); everything else consistently `claude-sonnet-5`. The real work is three judgment items: (1) visual-explainer's single-knob design forces one model onto three call sites with different cost/quality profiles — Opus-5-primary posture wants the knob split (Opus 5 for analysis/generation/refinement, Sonnet 5 for the high-volume vision-evaluation loop, Haiku for the auth ping); the stale "5x cheaper than Opus" comment shows the original tiering was decided under pricing that no longer holds; (2) the research pipeline's documented `ANTHROPIC_MODEL=claude-opus-4-8` (api-key-setup.md + research-models.md) is the one genuinely behavior-affecting stale default — a free upgrade to `claude-opus-5` at identical pricing; (3) nothing — no schema, no CI step, no pre-commit check — enforces ADR-0005's tier-alias rule, and README.md even says "Model pinned in frontmatter"; per E043 doctrine, ship the enforcement guard (negative-tested) along with the doc fix. Eval-side: the suite is correctly model-agnostic; only assess-document's absolute score bands and description-triggers' trigger expectations encode prior-model calibration — re-baseline under Opus 5 rather than rewrite.
