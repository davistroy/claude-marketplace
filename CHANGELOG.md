# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [personal-plugin v11.10.0] - 2026-07-31

Plan v14 — the remainder of the E052 audit backlog (#200, #199, #238, #216, #198), executed against the *investigated* shape of each issue rather than the filed text.

### Removed
- Two live deep-reasoning prompt injections plus the generator template that minted them. Both fired on every component load; three in-repo surfaces had asserted the mechanism was a no-op.

### Changed
- `ultra-plan` declares `effort: xhigh` explicitly, replacing an implicit unsanctioned escalation with a sanctioned one rather than de-escalating the skill.

## [personal-plugin v11.9.0] - 2026-07-30

Mitigations for #232 — a long-lived session serves the plugin version it resolved at start-up, so a current bundled tool can be read against a stale skill-body contract.

### Added
- `task-sync` version-skew preflight: warns when the served `$CLAUDE_PLUGIN_ROOT` version differs from `installed_plugins.json`.

### Changed
- `task-sync` enumerates the plan JSON's actual keys and halts on an unrecognized one, rather than parsing for a list restated in prose.

## [personal-plugin v11.8.0] - 2026-07-30

Plan identity for `/implement-plan`'s state file (#235) — a completed run's state was inherited by a different plan at the same path and reported success having done nothing.

### Added
- `plan_identity` (`generated`, `total_phases`, `phase_titles`, item ids) written at STARTUP and verified before resume; mismatch offers start-fresh / resume-anyway / abort.
- A guard so a state file describing a finished plan is reported as already-complete rather than routed to `ALL_COMPLETE`.

### Fixed
- State-file deletion moved from Final Step 0 to Final Step 4, after the COMPLETION REPORT that reads it.
- Item ids parsed with `match()` instead of an anchored regex, which had silently dropped two prefix-decorated headings.

## [personal-plugin v11.6.0] - 2026-07-29

The 16-issue correctness backlog (E060 plan, 8 phases / 42 items, PR #222). Grouped by root cause rather than by issue.

### Added
- **ADR-0011 — dynamic-injection doctrine**, and `scripts/check_injections.py`, the only linter that can enforce it: it **replays the harness pre-pass** instead of grepping (74 textual matches under `plugins/` vs 14 live sites). Wired as a step in the existing validate job and as pre-commit Check 4.
- **ADR-0012 — artifact-derived documentation**, correcting `paths:` (a conditional *load gate*, not a save-trigger), `hooks:` (an event record, not `pre:`/`post:`), and `isolation:` (agent frontmatter, not skill).
- `scripts/check_agent_models.py` + pre-commit Check 5 — ADR-0005 tier aliases are now enforced, not just documented.
- Phase-0 confirmation gates on `lab-notebook` and `create-wiki`.
- task-sync: `ORPHAN_LOCAL` classification, `SyncPlan.orphans`, fail-loud saturation guard, and real REST pagination.

### Changed
- **`Agent` is the single dispatch-tool name in `allowed-tools`** (D56). `Task` is retired from every live component; `TaskCreate`/`TaskUpdate`/`TaskList`/`TaskOutput` remain as the distinct progress-tracking family.
- **`lab-notebook` and `create-wiki` dropped `disable-model-invocation`** in exchange for their new gates (D57) — they may now be suggested proactively, but write nothing before confirming.
- Every hand-rolled text menu in `ask-questions`, `finish-document`, `spec-to-prototype`, `visual-explainer`, `summarize-feedback`, and `bpmn-generator` now uses the native `AskUserQuestion` tool.
- Eleven flagged skills' descriptions rewritten as capability statements — the `disable-model-invocation` flag removes a description from context, so trigger prose on a flagged skill was unreachable metadata.
- `evals/skills/description-triggers.eval.md`: S11–S14 rewritten. Their `Should` criteria had required the model to suggest a skill *because it matched trigger prose the flag deletes* — the eval encoded the very defect it guarded.
- `evals/commands/assess-document.eval.md`: absolute score bands replaced with relative assertions.

### Fixed
- **task-sync `sync --apply` aborted on two of the three documented decisions-file shapes.** `_load_decisions` is called twice on one file, and its "key absent → return the whole dict" fallthrough handed conflict ids to the fail-loud orphan validator. Fail-safe (aborted before mutation), but only the fully-wrapped form worked.
- `prime` mandated `context: fork` dispatch it did not grant, and claimed in three places that Phase 2 git values were "pre-loaded via dynamic context injection" — they never were; those injections are inert.
- `ship`'s diff-size gate computed the literal string `deletions(-)`, so the >500-line guard could never fire.
- The `verification-post-edit` hook recipe registered but could never run its payload: `matcher: "Bash"` guarantees the tool is `Bash`, so its test for `Edit` was unreachable.
- `visual-explainer`: `$GOOGLE_IMAGE_MODEL` was a phantom variable; the real override is `VISUAL_EXPLAINER_GEMINI_MODEL`. Authoritative 15-variable table added.
- Stale and never-existent pinned Claude model IDs across the generator templates and docs.

### Notes
- Behavior changed without an API break, hence a minor bump. **Anyone on 11.5.1 must update** — the 11.5.1 tree published before this release carries different content under the same version.

## [bpmn-plugin v4.4.0] - 2026-07-29

### Changed
- `bpmn-generator`: the simulated `help`/`status`/`back`/`skip`/`quit` REPL is gone (494 → 442 lines). `skip` and `quit` are native controls; `status` is redundant in a visible transcript. Its Question Format and Auto-Accept blocks now defer to `references/clarification-patterns.md` instead of duplicating them.
- `references/clarification-patterns.md`: all 22 question blocks plus both normative blocks converted to `AskUserQuestion`. Auto-accept is preserved via the free-text **Other** box — nothing native absorbs the old `E)` slot, so dropping it would have removed a real capability.

### Fixed
- `bpmn-to-drawio`: the skill's own `HAS_DI` branch re-taught the partial-DI layout bug the tool fixed in 4.3.x, silently corrupting diagram layout. Deleted — the skill now delegates to `--layout auto`.
- `cli.py --layout` help said `auto` preserves DI "when present"; the resolver gates on *complete* DI (every element positioned).

## [slide-gen v1.3.0] - 2026-07-29

### Fixed
- `build-cfa-deck`: the primary snippet used `Presentation` before importing it, and two different slide-removal implementations were both broken. One working implementation now lives in the new `references/cfa-deck-helpers.md`.
- Machine-specific asset paths replaced with a `CFA_ASSETS_DIR` override.

## [personal-plugin v11.5.1] - 2026-07-29

### Fixed
- `new-skill` and `leak-risk-audit` failed on **every** invocation in **every** directory. Both carried live `` !`…` `` shell injections: `/new-skill` injected the literal placeholder `cmd` (exit 127) and `/leak-risk-audit` injected `ls -la <dataset-path>`, a bash syntax error (exit 2). A non-zero exit aborts prompt expansion rather than degrading to empty output, so neither skill ever reached the model. `references/templates/skill.md` seeded the same defect into every scaffolded skill.

## [personal-plugin v11.5.0] - 2026-07-29

### Fixed
- `research-topic`: the Claude leg returned HTTP 400 on every dispatch — `thinking.budget_tokens` is removed from the Messages API across the whole current model family. Replaced with adaptive thinking + `output_config.effort` (closes #189).
- `research-topic`: a safety refusal (HTTP 200, `stop_reason: "refusal"`, no `error` body) passed every fast-fail check and wrote a silently empty research report. Guard added and mutation-tested.

### Changed
- `research-topic`: default Claude model `claude-opus-4-8` → `claude-opus-5`; depth ladder re-derived as `low`/8k, `medium`/16k, `high`/32k.

## [personal-plugin v11.4.1] - 2026-07-29

### Fixed
- `task-sync`: `sync --apply` crashed on any push because `--remove-milestone` does not exist in `gh`; milestones are now cleared via the REST API and only when one is set (closes #212).

## [personal-plugin v11.4.0] - 2026-07-29

### Fixed
- `task-sync`: unrecognized `priority/*` / `status/*` labels are preserved instead of being stripped on pull and `--remove-label`'d from the issue on the next push (closes #208).

### Added
- `task-sync`: `P0` accepted as a priority value.

## [personal-plugin v11.3.0] - 2026-07-22

### Added
- **task-sync `scan-apply` subcommand** — applying a confidentiality disposition (`keep`/`redact`/`remove`/`anonymize`) is now a first-class, tested CLI subcommand instead of an inline `python3` heredoc embedded in the skill. Takes the same `{task_id: disposition}` JSON shape as `sync --decisions` (flat, or wrapped under a `"decisions"` key), then saves `tasks.json` and regenerates `TASKS.md`. It validates **every** task id and disposition before mutating anything, so one bad entry rejects the whole batch and writes nothing — the previous inline script raised a bare `KeyError` mid-loop and silently discarded the dispositions it had already applied (closes #168).
- **`sync --adopt-all`** — full-mirror escape hatch that adopts every tracker issue regardless of how long ago it closed (the pre-11.3.0 behavior).
- **`adopt_closed_within_days` config key** (default `0`) — governs which unadopted tracker issues a sync will adopt.

### Changed
- **task-sync `sync` no longer adopts closed issues you never tracked.** By default (`adopt_closed_within_days: 0`) only **open** issues are adopted; a larger value adds a grace window for recently-closed ones. Previously every issue ever closed was adopted as a `done` task — in an established repo the first sync flooded the list with long-finished work, and because adoption (`apply.py:207`) and pruning (`:209-211`) happen in the *same* `apply()` call, an issue closed past the prune window was adopted and destroyed within one sync and then re-proposed on **every** subsequent sync, forever (closes #167).
  - The window gates **new adoptions only**. An already-adopted task keeps full remote fidelity — it still learns that its issue was closed, however long afterward.
  - The tracker fetch is unchanged (`--state all`). Filtering at the provider layer was rejected: `classify()` treats the fetched issue list as authoritative, so a missing issue silently downgrades a genuine both-sides-changed **conflict into a one-sided push** (a remote clobber), and that push carries `state`, which could even reopen a long-closed issue.
  - Existing `tasks.json` files predate the new key; an absent key resolves to `0` (open-only), not to the unrelated 30-day prune window.

- **`sync` plans now report what they skipped.** `sync --plan`/`--dry-run` emit `skipped (closed outside adopt window): N — use --adopt-all to mirror them`, `sync --apply` says the same in its summary, and the `--plan --json` payload gained a `skipped_adopts` array of the affected issue numbers (key order: `creates, pushes, pulls, conflicts, skipped_adopts, confidentiality_findings`). Without this, a plan that adopted nothing printed "already in sync — nothing to do" while issues sat unadopted.
- **`scan-apply` is idempotent.** Re-running the same decisions file over unchanged content writes nothing and reports `N task(s) already carry the requested disposition`. A task is skipped only when its recorded decision matches *and* its content is unchanged since review; re-deciding with a different disposition still applies.

### Fixed
- **task-sync `scan-apply` now stamps `updated_at`.** It previously mutated `title`/`body` without touching the timestamp, so the conflict recommender's last-write-wins comparison saw a stale local time and recommended `remote` for a task redacted seconds earlier — and accepting that recommendation would restore the un-redacted content from the tracker. Every other content-mutating command already stamped it.
- **task-sync adoption now keys off `issue.state`, not the nullable `closed_at`.** A `state="closed"` issue whose `closed_at` was absent from the tracker payload (both adapters read it with `.get()`), or whose timestamp was in the future due to clock skew, was still adopted. The predicate is now fail-closed: a closed issue is adopted only when its age is provably inside the window.
- **task-sync: a missing or malformed `--decisions` file now reports the path** instead of raising an unhandled `FileNotFoundError` traceback (`cannot read decisions file <path>: …`). Affects both the new `scan-apply` and the pre-existing `sync --apply`.
- **task-sync docs:** `sync-semantics.md` claimed a locally-changed task whose issue vanished is "re-created instead of pushed" — the reachable code path **pushes** to the recorded issue number (`classify()` returns `NEW_LOCAL` whenever `issue_number` is `None`, so `resolve()`'s re-create branch is unreachable from the pipeline). `config-reference.md` claimed `tasks.json` "is meant to be committed"; this repo gitignores both it and `TASKS.md`, so committing is now described as an optional per-repo choice.
- **CI:** the `task-sync` job in `test.yml` still carried a "NON-required … withheld from branch protection" comment; both matrix legs have been required checks since Phase 6.

## [personal-plugin v11.2.1] - 2026-07-18

### Fixed
- **task-sync Gitea sync path: `init` now persists `config.gitea_url`** from the origin remote instead of leaving it unset (closes #173).
- **task-sync Gitea sync path: `_build_provider` now falls back to the tea CLI config** (`~/.config/tea/config.yml`) for the Gitea base URL and token when `$GITEA_URL`/`$GITEA_TOKEN` are unset, with env vars overriding tea config when both are present (closes #174).
- **task-sync SKILL.md / config-reference docs** now accurately describe this env → tea-config → unset resolution order (closes #172).

## [personal-plugin v11.2.0] - 2026-07-18

Adds **task-sync**: a new skill that keeps a per-repo `tasks.json` (with a generated `TASKS.md` view) reconciled with the repo's issue tracker (GitHub via `gh`, Gitea via its REST API). Built per ADR-0010 / D34.

### Added
- **task-sync skill + bundled Python tool** (`plugins/personal-plugin/tools/task-sync/`, stdlib-only): direct commands (`init`/`list`/`add`/`edit`/`done`/`remove`/`status`) plus a `sync` subcommand driven by a `plan → decide → apply` protocol — `sync --plan --json` computes creates/pushes/pulls/conflicts/confidentiality findings read-only, the skill renders them and collects explicit decisions, `sync --apply` executes exactly what was decided.
- **3-way reconcile engine** classifying each task against its last-synced base (new-local/new-remote/changed-local/changed-remote/changed-both/unchanged); conflicts (both sides changed) are always surfaced for an explicit user decision and never auto-resolved, with last-write-wins offered only as a recommendation.
- **Confidentiality scanner**: secret/token detection (`ghp_`/`sk-`/AWS keys/PEM/bearer tokens) plus generic structural detectors (email/phone/IP/internal hostname/ticket/asset id) and per-repo `sensitive_terms` config, gating every outbound create/push; `CRITICAL` findings require an explicit `keep`/`redact`/`remove`/`anonymize` disposition before anything leaves the machine.
- **Public-repo visibility guardrail**: warns and requires explicit confirmation before the first push/create of a sync session against a public GitHub/Gitea repo.
- **Prune**: `done` tasks whose linked issue has been closed longer than `config.prune_closed_after_days` (default 30) are pruned during `sync --apply` only.
- New `Task Sync Tests` CI job (non-required through Phases 1–5, added to branch protection in Phase 6) and its lockfile added to the dependency-audit gate.

## [personal-plugin v11.1.0] - 2026-07-16

Releases the post-11.0.0 backlog-burndown work (#125–#131) that had landed on `main` without a version bump — headlined by a new visual-explainer image-generation feature.

### Added
- **visual-explainer memory-bounded parallel image generation** (`--concurrency`, default 3): parallelizes Gemini image calls under an `asyncio.Semaphore` for a ~2.92× speedup; `--concurrency 1` restores exact serial behavior. Backward-compatible. (#128)

### Changed
- **visual-explainer:** decomposed the 1,814-line `cli.py` god module into 6 focused modules (terminal / cli_args / io_utils / reporting / pipeline + a thin cli entry). (#125)
- Extracted 3 oversized command bodies (`validate-plugin`, `implement-plan`, `new-skill`) under the 500-line house budget via `references/*-examples.md`. (#131)

### Fixed / Internal
- visual-explainer test coverage raised 69% → 93%, coverage-floor gate 65 → 85. (#127)
- visual-explainer mypy baseline zeroed (101 → 0); the tool is now mypy-clean. (#129)
- Behavioral eval corpus grown 35 → 45 across high-traffic skills. (#126)

## [bpmn-plugin v4.3.1] - 2026-07-16

### Fixed
- **bpmn2drawio partial-DI files no longer strand shapes at the origin (#143).** `auto` now resolves to `preserve` only when DI is complete (every element positioned) — `BPMNModel.has_complete_di_coordinates` — and falls back to a full graphviz layout otherwise. Fully-DI (Bizagi) and non-DI behavior unchanged.

## [bpmn-plugin v4.3.0] - 2026-07-16

Integrates external contributor PR #98 (Oleksandr Panasenko / @AlexanderV) into the bundled bpmn2drawio tool, rebased onto current `main` and brought up to the ruff/mypy/coverage gates.

### Added
- **bpmn2drawio `auto` layout mode (now default):** preserves existing BPMN DI coordinates when present, else falls back to graphviz. `--layout graphviz`/`preserve` unchanged.
- Geometric lane/pool assignment from DI bounds for `flowNodeRef`-less lanes (per-process constrained); data stores as cylinders; event-based/complex gateway theme styles.

### Fixed
- DI-carrying exports (e.g. Bizagi) no longer collapse all shapes into one pool / reflow valid coordinates; phantom empty pools skipped; event/gateway/data labels placed below shapes; pool title aligned to lane inset.
- 32 new tests; integrated suite 636 passing / 92.83% branch cov, mypy 0, ruff clean.

## [personal-plugin v11.0.0] - 2026-07-16

Architecture-review hardening release (8-phase remediation, LAB_NOTEBOOK Entries 017–024 -- archived, see `docs/archive/LAB_NOTEBOOK-E017-E050.md`). MAJOR: interface/capability changes below.

### Changed (breaking)
- **visual-explainer:** removed the inert `--concurrency` CLI flag + `GenerationConfig.concurrency` field (the concurrent code path was never called; generation was always serial). *(PERF-01)*
- **Tool permissions:** narrowed `allowed-tools` from unscoped `Bash` to specific `Bash(<cmd>:*)` scopes across ~16 skills + 7 commands (3 skills kept broad with justification). *(SEC-05)*
- **Fleet skills:** `spark-recon`, `jetson-recon`, `spark-audit`, `jetson-audit` are now `disable-model-invocation: true` (user-invoke-only) with explicit trust-boundary sections — they can no longer be auto-triggered by injected content. *(SEC-01)*

### Security
- bpmn2drawio BPMN parser hardened against XXE (no external entities/DTD/network); `lxml>=5.0,<7`. *(DA-01/SE-02/SEC-02)*
- visual-explainer: SSRF guard on URL fetch (blocks private/link-local/metadata IPs); `.env` key writes now `chmod 0600` + warning (ADR-0003 amended); atomic checkpoint writes. *(SEC-03/SEC-04/DA-02)*
- Research/brain-entry curl calls: connect/max timeouts + submit status-checks (fast-fail) + Gemini key moved to header. *(INT-01/02/03)*
- SECURITY.md: data-egress/confidentiality policy + supply-chain controls sections.

### Added
- 14 skills gained `## Error Handling` sections; error-classification for Gemini backoff uses typed exceptions.

### Fixed
- Contradictory test skips un-gated (full-pipeline + resize now run in CI). *(QA-07/08)*

## [personal-plugin v10.3.0] - 2026-07-16

### Added
- **`clear-prep` skill**: prepares a project to survive a context `/clear` or compaction with zero state loss — flushes the current session's work into all durable documents (LAB_NOTEBOOK living sections + in-flight entry, memory, CLAUDE.md, CHANGELOG), then emits a single copy-paste "resume prompt" the user runs in the fresh session so a zero-context Claude continues seamlessly. Writes only git-recoverable docs; never commits or clears context. Supports a `--no-write` dry-run that only generates the resume prompt.

## [personal-plugin v10.2.0] - 2026-07-12

### Added
- **`fleet-health` skill**: read-only, one-shot health snapshot across the 5-machine personal fleet (DGX Spark, Jetson Orin Nano, homeserver, bond, obvm) — uptime/load/disk/memory plus per-host inference/service endpoint checks over SSH and curl, rendered as a single status table with a pass/fail verdict
- **`new-project` skill**: end-to-end new-project scaffolder — git init, remote (GitHub by default, Gitea with `--gitea`), `CLAUDE.md`, type-appropriate `.gitignore`, placeholder-only `.env`, mandatory `LAB_NOTEBOOK.md`, kill-criteria `BRIEF.md`, and initial commit/push
- **`archive-project` skill**: retires a project repo — status header in README, tag/commit, optional remote archive (GitHub only), relocation to `~/dev/archive/`, and a logged line in `~/dev/PORTFOLIO.md`
- **`sre-operator` agent**: new named agent for the 5-machine homelab fleet — SSH-based diagnosis and scoped, explicitly-authorized remediation with mandatory LAB_NOTEBOOK logging
- **`project-claude-md.md`, `brief.md` templates**: new scaffolding templates consumed by `new-project`

### Fixed
- **Lab-notebook gate hook**: `PreToolUse` hook now parses `tool_input.command` from stdin JSON (via `jq`, falling back to raw stdin) and propagates the gate script's actual exit code — the prior form matched the wrong field and always returned 0, so it could never actually block a commit

## [10.1.0] - 2026-07-12

### Added
- `wiki` skill: layout detection with a new **OKF bundle mode** — drives kb/-rooted wikis from their repo's own `AGENTS.md` contract (per-directory indexes, contract frontmatter, delegated `tools/lint.py`, repo-native log format). Legacy `wiki/` + `schema.yaml` behavior unchanged.
- `wiki` skill: new `propagate <fact>` subcommand — sweeps all pages for stale variants of a newly resolved fact, applies edits, closes markers, logs once.
- `analyze-transcript`: new `--format interview-record` — dated markdown record with YAML frontmatter for knowledge-repo immutable sources directories.

## [marketplace v3.3.0, personal-plugin v10.0.0, bpmn-plugin v4.2.0, slide-gen v1.2.0] - 2026-07-08

Coordinated release closing an 8-phase, 35-item modernization pass against current official Anthropic guidance (see `IMPLEMENTATION_PLAN.md`, ADR-0005, ADR-0006).

### Added
- **Agent frontmatter**: all 9 arch-review agents (solutions-architect, data-architect, integration-architect, software-engineer, performance-engineer, qa-architect, security-architect, platform-engineer, risk-compliance) now register with `name`, `description`, least-privilege `tools`, `model: inherit`, and `effort: high` — dispatch-by-name replaces prompt-inlining
- **`/new-skill --pattern`**: scaffold a skill from any of the 8 command-pattern templates (conversion, generator, interactive, planning, read-only, synthesis, utility, workflow), adapted to skill form at generation time
- **CI**: `plugin-validate` job runs the official `claude plugin validate --strict` (pinned CLI version) against all three plugins plus non-strict against the marketplace manifest
- **Trigger evals**: `evals/skills/description-triggers.eval.md` — should-trigger/should-not-trigger scenarios for the big-5 overlap-prone skills and the four locked-down skills
- **14 new reference files** from progressive-disclosure extractions, incl. `plan-append-guide.md`, `recommendations-template.md`, `create-plan-examples.md`, `implement-plan-state-schema.md`, `validation-output-examples.md`, `research-provider-protocols.md`, `ship-output-templates.md`, `clean-repo-examples.md`, `claude-md-wiki-section.md`, `wiki-readme-template.md`, `skill-patterns.md`, `bpmn2drawio-reference.md`, and skill-local `evaluate-pipeline-output/references/{report-format,evaluator-guidance}.md`
- **Per-plugin README + LICENSE**: `plugins/{personal-plugin,bpmn-plugin,slide-gen}/{README.md,LICENSE}`
- **`.gitattributes`**: explicit LF line-ending rules for text files; binary protection for `.zip`
- **`LEARNINGS.md`**: repo-root log of implementation escalations and cross-cutting lessons from this release

### Changed
- **Implementer agents**: `.claude/agents/{haiku,sonnet,opus}-implementer.md` pinned model IDs replaced with tier aliases (`haiku`/`sonnet`/`opus`) per ADR-0005 — swap models globally without touching plans
- **arch-review**: dispatch simplified to `subagent_type`-by-name (no more agent-file inlining); per-agent `findings/<agent>.meta.json` replaces the shared, collision-prone `.meta.json`; `arch-review-single` and `arch-synthesize` aligned to match
- **Planning family single-sourced**: `create-plan` (470 lines), `plan-improvements` (490 lines), and `implement-plan` (573 lines) now point to `references/plan-template.md` for the model-tier rubric, sizing tables, and append procedure instead of carrying drifting inline copies; `implement-plan`'s duplicated PATH A/PATH B collapsed into one flow parameterized on batch cardinality
- **`validate-plugin`**: refactored to 675 lines with a dynamic reference-file inventory (diffs `references/` against a required set instead of a hand-synced table); sample output moved to `validation-output-examples.md`
- **13 oversized files** brought to/toward the ~500-line progressive-disclosure budget across both plugins (validate-plugin, research-topic, ship, clean-repo, finish-document, bpmn-to-drawio, create-wiki, evaluate-pipeline-output, test-project, plus the three planning commands above)
- **21 skills'** body "Proactive Triggers" sections folded into frontmatter `description` (or `when_to_use`) per official trigger-info-in-frontmatter guidance
- **Big-5 descriptions** (bpmn-generator, bpmn-to-drawio, explain-project, spec-to-prototype, accessibility-annotator): added explicit "Do NOT use for" negative scope disambiguating overlapping skills
- **`scaffold-plugin`**: defaults flipped to skills-first — `skills/` scaffolded by default, `commands/` only via explicit `--with-commands` (ADR-0006)
- **CLAUDE.md**: refreshed to current spec — skills-first policy, new frontmatter fields, description budgets, hook fields, updated structure/counts
- **8 skills** (4 pre-existing + 4 new: brain-entry, unlock, lab-notebook, create-wiki) now carry `disable-model-invocation: true`, preventing unwanted auto-invocation of side-effect-primary skills

### Fixed
- **15 `/batch` + 11 `/ultrareview` dangling references** replaced with real mechanics (`/implement-plan` parallel phases, background Agent dispatch) and the current `/code-review ultra` alias
- **ultra-plan**: phase-numbering gap (Phase 0 → Phase 2) renumbered to a contiguous 0–5 sequence
- **validate-plugin**: rule-count check synced from 16 to the template's actual 17 rules
- **Stale model IDs**: `research-topic` (`claude-opus-4-6` → `claude-opus-4-8`; dead `agent:`-field misuse removed from the fork header); `visual-explainer` (dead `config.claude_model` plumbing wired through both construction sites, `DEFAULT_MODEL` constants updated, dead `TargetModelHint` style key removed from both style JSONs)
- **Portability**: hardcoded `C:\Users\...` paths rewritten to portable equivalents across 3 skills; CRLF line endings normalized with `.gitattributes` preventing recurrence
- **`unlock`**: malformed `Bash(powershell*)` permission glob corrected to `Bash(powershell:*)`

### Deprecated
- **`/new-command`**: moved to `deprecated/`; replaced by `/new-skill --pattern` per the skills-first authoring policy (ADR-0006)

## [personal-plugin v9.3.0] - 2026-06-15

### Changed
- **spark-recon**: refreshed stale Machine Config — `current_model` → `Qwen/Qwen3.6-35B-A3B-FP8`, quantization → pre-quantized FP8; broadened Check 2 keyword classifier (Qwen3.6/3.7, DFlash, speculative); Check 1/4 instructions updated to Qwen3.6 context; documented the Firestore `benchmarks`-collection REST access path (unfreezes Arena tracking); dropped permanently-removed NVIDIA forum category 720
- **spark-audit**: dropped permanently-removed NVIDIA forum category 720; removed the obsolete "pre-quant FP8 hangs" CRITICAL anti-pattern (production intentionally runs pre-quant FP8 since 2026-05-18) and corrected the attention-backend expectation (FLASH_ATTN auto-selected on SM121; FlashInfer is MoE-only)

## [marketplace v3.2.0, personal-plugin v9.2.0, bpmn-plugin v4.1.0, slide-gen v1.1.0] - 2026-05-14

### Added
- **slide-gen: build-cfa-deck skill** — generate complete, on-brand Chick-fil-A PowerPoint presentations from a topic prompt using the CFA "Support Now" template (64 layouts, 194 SVG icons, embedded Apercu fonts) and brand guidelines

### Changed
- Coordinated minor bump across all plugins and marketplace (build-cfa-deck was the trigger; bpmn-plugin and personal-plugin bumped for release cadence)

## [marketplace v3.1.0, personal-plugin v9.1.0, slide-gen v1.0.1] - 2026-05-10

### Added
- **slide-gen plugin**: 8-skill AI presentation pipeline — research, outline, draft, optimize, validate-graphics, generate-images, build, and full-workflow orchestrator (`/sg-research`, `/sg-outline`, `/sg-draft`, `/sg-optimize`, `/sg-validate-graphics`, `/sg-generate-images`, `/sg-build`, `/sg-full-workflow`)
- **Model routing in planning pipeline**: Per-task `**Model Tier:**` field (haiku/sonnet/opus) in plan template; `create-plan` and `plan-improvements` assign tiers using rubric at plan-time; `implement-plan` dispatches to named sub-agents (`haiku-implementer` / `sonnet-implementer` / `opus-implementer`) with escalation pattern
- **Named implementer agents** in `.claude/agents/`: model pinned in frontmatter, plans reference agent name (not model) — swap models globally without touching plans
- **Plan template Rule 17**: Model Tier field with full haiku/sonnet/opus rubric and backward-compatibility guarantee (items without Model Tier default to `sonnet`)

### Changed
- **Implement-plan**: Per-item `**Model Tier:**` takes priority over phase-level execution hints; state file adds `item_model_tiers` map; escalations logged to LEARNINGS.md with single re-dispatch at next tier
- **Create-plan Phase 3.1**: Step 5 assigns model tier with rubric and escalation criterion guidance; Phase 3.2 Execution Hints updated to position per-item tiers as primary, phase hints supplementary
- **Plan-improvements**: Work item construction now includes Model Tier as field 2 with inline rubric
- **README**: Added slide-gen plugin section; added `.claude/agents/` to repository structure diagram
- **CLAUDE.md**: Added slide-gen to install commands and repository structure; added `.claude/agents/` section; updated references list with v9.0.0 additions

### Fixed
- **arch-review**: Replaced parse-time bash hooks with model-driven Bash/Read calls (removes hook dependency from review workflow)

## [marketplace v3.0.0, personal-plugin v9.0.0] - 2026-04-30

### Added
- **Plan template**: EARS acceptance criteria notation, runnable Definition of Done (`<!-- BEGIN/END DOD -->`), execution hints (model tier directives), unknowns register — structural rules 13-16
- **Ultra-plan Phase 0**: Constitution check reads CLAUDE.md constraints, fills gaps via targeted interview, produces Pre-Plan Gates
- **Ultra-plan sub-agent investigation**: >5 items triggers parallel Explore sub-agents for investigation
- **Ultra-plan `--refresh`**: Drift detection mode compares existing plan against current code state
- **Ultra-plan creative branching**: L4+ tasks get comparison tables across competing architectures
- **Ultra-plan ADR generation**: L3+ tasks conditionally generate Architecture Decision Records
- **Anti-patterns catalog**: 11 entries across Planning, Implementation, Verification categories (`references/anti-patterns.md`)
- **ADR template**: Standard Architecture Decision Record format (`references/adr-template.md`)
- **Hook recipes**: 3 example hooks — planning-stop warning, post-edit verification, session-start plan primer (`references/hooks/`)
- **AGENTS.md template**: Cross-tool compatibility template for Codex, Cursor, Aider (`references/agents-md-template.md`)
- Optional AGENTS.md generation in `/create-plan` and `/plan-improvements`
- **Validate-plugin**: Phase 8.5 plan template structural rule validation (checks rules 13-16 keywords: EARS, DoD markers, Execution Hints, Unknowns Register)
- **Validate-plugin**: Phase 8.6 reference file inventory check (core references, hook references, pattern/template subdirectories)

### Changed
- **Ultra-plan**: Rewritten from 5 phases to 7 phases (0-6) with constitution check, sub-agent support, ADR/drift/branching extensions
- **Create-plan**: Phase 1.5 detects lint/typecheck/coverage commands; Phase 4 generates DoD sections and execution hints; unknowns routed to register
- **Plan-improvements**: Phase 1 detects verification commands; Phase 3 generates DoD and execution hints; unknowns routed to register
- **Implement-plan**: State file schema evolved — `verification_commands` array replaces single `test_command` (backward-compatible); testing subagent runs all DoD commands; `Depends On` parsing for parallelization; execution hints consumed for model tier; Risk Mitigation Status updated on completion; `Completed` header set during finalization
- **Plan-gate**: `/ultraplan` references fixed to `/ultra-plan` with disambiguation notes
- **Validate-plugin**: Replaced hardcoded example counts (15 files, 3 skills, 16 files, 21 commands) with `[N]` dynamic placeholders to prevent stale output drift

### Fixed
- `/ultraplan` vs `/ultra-plan` reference ambiguity in plan-gate and create-plan (9+ references corrected)

## [marketplace v2.0.0, personal-plugin v8.0.0, bpmn-plugin v4.0.0] - 2026-04-21

### Changed
- **personal-plugin v8.0.0**: Marketplace modernization — adopted late-2025 Claude Code features (`context:fork`, `isolation:worktree`, `paths:` auto-activation, dynamic `!cmd` injection) across all major skills; deleted deprecated help skills and review-pr command; consolidated audit/recon skills (~50% LOC reduction via shared reference framework; thinned jetson/spark audit+recon to config-layer only); added lab-notebook PreToolUse hook; rewrote research-topic with parallel multi-provider subagents; removed research-orchestrator Python tool entirely
- **bpmn-plugin v4.0.0**: Help skill removed (superseded by native `/help`)
- **marketplace v2.0.0**: Schema version bump reflecting breaking plugin changes (removed skills/commands, restructured scaffolding)

## [marketplace v1.7.1, personal-plugin v7.0.1] - 2026-04-19

### Changed
- Added mandatory Phase 0 to `/prime` skill to read `LAB_NOTEBOOK.md` before any other analysis when present

## [personal-plugin v6.8.0] - 2026-04-11

### Fixed
- Added missing `## Instructions` section to `plan-next`, `review-arch`, and `test-project` commands for pattern compliance

## [marketplace v1.6.2, personal-plugin v6.7.2] - 2026-04-02

### Changed
- Enhanced `/prime` skill to read `LAB_NOTEBOOK.md` when present — extracts Decision Log, Open Action Items, recent experiment entries, and Current Baseline into the prime report

## [marketplace v1.6.0, personal-plugin v6.7.0, bpmn-plugin v3.4.0] - 2026-03-31

### Added
- Documentation gate in `/ship` skill — enforces LAB_NOTEBOOK.md updates before commit/push

### Fixed
- personal-plugin hooks.json migrated from deprecated array format to record format

### Changed
- Updated README.md skills table (16 → 19 skills), replaced stale `validate-and-ship` with `release-plugin`
- Bumped personal-plugin 6.6.0 → 6.7.0, bpmn-plugin 3.3.0 → 3.4.0, marketplace 1.5.0 → 1.6.0
- Cleaned 4 stale remote branches, 4 egg-info build artifact directories

## [marketplace v1.3.0] - 2026-03-30

### Changed
- Bumped `marketplace_version` from 1.2.0 to 1.3.0

## [personal-plugin v6.4.0] - 2026-03-30

### Added
- `lab-notebook` skill — initialize mandatory experiment logging combining scientific notebook, ADR, and incident postmortem patterns
- GITHUB_ERRORS.md error check log tracked at repo root

### Changed
- Enhanced `explain-project` skill with `--update` incremental mode, runtime data verification phase (Phase 3.5), glossary hyperlink navigation, production number sourcing rules, document freshness metadata, and "Known Limitations" / "Operational State" sections
- Updated README.md skill count and table (15 → 16 skills)
- Updated CLAUDE.md directory listing with lab-notebook skill
- Updated help skill with lab-notebook entry

## [personal-plugin v6.3.0] - 2026-03-27

### Added
- `accessibility-annotator` skill — analyze technical documents for CS/ML concepts and add explanation annotations for non-CS readers
- `explain-project` skill — generate comprehensive annotated technical overview document for non-technical stakeholders

### Changed
- Updated README.md skill count and table (11 → 15 skills)
- Updated CLAUDE.md directory listing with new skills
- Added missing CHANGELOG entry for v6.2.0

## [personal-plugin v6.2.0] - 2026-03-25

### Added
- `leak-risk-audit` skill — audit datasets for proprietary information leaks before sharing with public/cloud services
- `spec-to-prototype` skill — build visual HTML/CSS prototypes from spec documents or wireframe descriptions
- Evaluation framework (`evals/`) for automated plugin quality assessment

### Fixed
- Trailing space in help skill (MD009 lint violation)

### Changed
- Bumped `marketplace_version` to 1.2.0

## [personal-plugin v6.1.0] - 2026-03-21

### Fixed
- 21 documentation accuracy and internal consistency issues identified during comprehensive evaluation
- Corrected stale reference docs (flag-consistency dimensions, research-models effort levels, api-key-setup env vars)
- Removed phantom --output flag references, fixed example filenames, aligned template formats
- Replaced non-existent tool references (EnterPlanMode, AskUserQuestion) with natural language
- Added missing effort frontmatter to 3 skills and Performance section to evaluate-pipeline-output

## [bpmn-plugin v3.1.0] - 2026-03-21

### Fixed
- bpmn-generator question numbering overlap (Phase 3/4 both claimed Q11)
- Added maintenance note to help skill Mode 2 hardcoded references

## [personal-plugin v6.0.0] - 2026-03-21

### Added
- `argument-hint` frontmatter field to all 22 commands that accept arguments — improves UI discoverability
- `effort` frontmatter field to 10 planning commands/skills — controls thinking depth (low/medium/high/max)
- `disable-model-invocation: true` to destructive skills (ship, validate-and-ship) — prevents accidental auto-triggering
- Hooks system (`hooks/hooks.json`) with Stop and SessionStart hooks for workflow automation
- Deep investigation planning philosophy across all 8 planning commands/skills — root cause analysis, interrelationship mapping, architectural coherence
- Missing Examples sections to 3 commands (analyze-transcript, create-plan, finish-document)
- Missing Performance sections to 2 commands (develop-image-prompt, review-pr)

### Changed
- Standardized "Proactive Triggers" section naming across all skills (plan-gate, security-analysis)
- Updated CLAUDE.md with new frontmatter field documentation (argument-hint, effort, disable-model-invocation, context, agent)
- Updated README.md structure to include hooks directory
- plugin.json now registers hooks configuration

## [bpmn-plugin v3.0.0] - 2026-03-21

### Added
- `argument-hint` frontmatter field to all 3 skills — improves UI discoverability
- `${CLAUDE_PLUGIN_ROOT}` environment variable support in bpmn-to-drawio tool paths — enables reliable marketplace installation
- `references/archive/` directory for historical reference documents

### Changed
- Archived converter-fixes-20260118-123946.md to references/archive/ (historical record, fixes already in codebase)

## [personal-plugin v5.1.0] - 2026-03-04

### Added
- Performance sections to all 25 commands and skills (13 commands, 12 skills)
- Examples sections to 7 files missing them (4 commands, 3 skills)
- Ruff linting and formatting enforcement in CI (`ruff.toml`, validate.yml)
- Dependency security scanning via `pip-audit` in CI
- Windows (`windows-latest`) added to CI test matrix
- `pytest.ini` for local test discovery from repo root
- Type hints to feedback-docx-generator utility functions

### Changed
- Markdown linting now blocking in CI (removed `|| true`)
- Standardized example section headings to `## Examples` across all commands

### Fixed
- Removed 5 committed `.coverage` files (~588 KB) from git tracking
- Removed dead `merge_theme_with_config` call in bpmn2drawio converter.py
- TROUBLESHOOTING.md reviewed and verified substantive

## [bpmn-plugin v2.4.0] - 2026-03-04

### Added
- Performance sections to all 3 skills (help, bpmn-generator, bpmn-to-drawio)

### Fixed
- Dead code removal in bpmn2drawio converter.py

## [personal-plugin v5.0.0] - 2026-03-04

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

## [bpmn-plugin v2.3.0] - 2026-03-04

### Added
- `allowed-tools` declarations on all 3 skills (bpmn-generator, bpmn-to-drawio, help)

### Changed
- Extracted BPMN element mapping tables to `references/bpmn-elements.md`
- `bpmn-generator` SKILL.md reduced from ~620 to <500 lines

## [personal-plugin 4.1.0] - 2026-02-28

### Added
- `allowed-tools` frontmatter to all 28 commands/skills that lacked them
- `Related Commands` sections to all 23 commands
- Proactive trigger sections to all 10 skills
- Error handling tables to all 36 command/skill files
- `references/api-key-setup.md` — extracted Bitwarden-based key setup workflow
- `references/flag-consistency.md` — comprehensive flag reference across all commands
- `plan-gate` skill for assessing task complexity and routing to right planning approach

### Changed
- Rewrote `plan-next.md` from scratch (47 → 234 lines) with priority decision matrix and plan-awareness
- Rewrote `setup-statusline.md` with 4-phase approach, safety checks, and `--dry-run`/`--uninstall` flags
- Overhauled `consolidate-documents.md` with standardized input flow and 4 new flags
- Restructured `review-arch.md` with task-based assessment and Architecture Scorecard
- Reimplemented `check-updates.md` with true remote version checking via GitHub API
- Overhauled `security-analysis` skill with input validation, trigger conditions, and structured error handling
- Expanded `convert-hooks.md` with limitation warnings, before/after examples, and `--validate` flag
- Expanded `convert-markdown.md` with analysis-driven flag selection and 4 new flags
- Expanded `develop-image-prompt.md` with `--dimensions` flag (8 presets) and 8 style presets
- Improved `test-project.md` safety: selective staging replaces `git add -A`, PR-only default (merge requires `--auto-merge`)
- Fixed `ship` skill phase numbering and updated Co-Authored-By to `Claude Opus 4.6`
- Replaced hardcoded plugin lists with dynamic filesystem scanning in bump-version, check-updates, validate-plugin

### Fixed
- Removed 37 dead references to non-existent `scripts/` and `schemas/` across 17 files
- Fixed secrets policy violations in research-topic and visual-explainer (removed API key wizards, use `/unlock` instead)
- Fixed shell injection vulnerability in `unlock` skill (safe quoting, key name validation)
- Fixed `scaffold-plugin.md` skills path references (`help.md` → `help/SKILL.md`)
- Fixed `define-questions.md` phantom schema references
- Fixed `finish-document.md` resume contradiction
- Fixed `validate-plugin.md` duplicate section numbering
- Fixed `remove-ip.md` trigger phrase removal
- Removed contradictory input patterns in consolidate-documents

## [personal-plugin 4.0.0] - 2026-02-16

### Added
- `/review-intent` command: Determine original project intent and compare against current implementation
- `/prime` skill: Evaluate codebase to produce detailed report on project purpose, health, status, and next steps
- `/implement-plan` parallel execution: PATH B launches independent work items concurrently via background subagents
- `/create-plan` and `/plan-improvements` append mode: If IMPLEMENTATION_PLAN.md exists, new phases are appended with renumbered items instead of overwriting

### Changed
- `/implement-plan` restructured with dual execution paths (PATH A: sequential, PATH B: parallel) and parallelization map built at startup
- README.md updated with all 9 skills (was showing only 3) and 26 commands
- CLAUDE.md repository structure updated with review-intent command and prime skill
- CLAUDE.md Patterns Used section now covers all 26 commands across 14 pattern categories
- SECURITY.md updated with multi-provider API data flow, security-relevant skills, and current third-party dependencies
- TROUBLESHOOTING.md Python version requirement corrected (3.8 → 3.10)
- QUICK-REFERENCE.md expanded with 5 new flags and a skills section
- Help skill error section updated with complete command and skill lists
- 11 code blocks in bpmn-plugin tool docs fixed with language specifiers

### Fixed
- Documentation drift: 22 fixes across 8 files for stale references, missing features, and incorrect claims
- SECURITY.md "No Audit Trail" claim corrected — audit logging available via `--audit` flag

## [personal-plugin 3.14.0] - 2026-02-15

### Changed
- `/implement-plan` command: Removed Ralph Wiggum loop dependency, replaced with native subagent orchestration pattern
  - Main agent now acts as thin loop controller using Task tool directly
  - Added explicit "Context Window Discipline" rules table
  - Instructions use blockquoted subagent prompts with `subagent_type: "general-purpose"`
  - Progress tracking via TaskCreate/TaskUpdate instead of external loop state
  - Added "Do not stop early" directive to ensure full plan completion

## [personal-plugin 3.12.0] - 2026-01-26

### Added
- Help skill updated with `/unlock` skill listing and detailed usage documentation

### Changed
- Version bump to 3.12.0

### Removed
- `SHIP_GITEA_PLAN.md` planning document (completed, no longer needed)

## [personal-plugin 3.11.1] - 2026-01-26

### Added
- `/unlock` skill: Unlock Bitwarden vault and load project secrets into environment
  - Reads master password from `~\.claude\.env` (local, not in repo)
  - Auto-detects project name from working directory
  - Loads secrets from `dev/<project>/api-keys` in Bitwarden
  - Recovered from plugin cache (was installed but missing from source repo)

## [personal-plugin 3.11.0] - 2026-01-26

### Added
- `/ship` skill: Gitea platform support with `tea` CLI auto-detection
  - Phase 0 platform detection parses git remote to select GitHub (`gh`) or Gitea (`tea`)
  - Platform-conditional commands for PR creation, review, and merge
  - Draft PR limitation documented (tea CLI does not support `--draft`)
  - Gitea branch cleanup after merge (tea doesn't auto-delete branches)
- `/validate-and-ship` skill: Added `tea` CLI to allowed tools and stopping conditions

### Changed
- `/ship` skill: `allowed-tools` now includes `Bash(tea:*)`
- `/validate-and-ship` skill: `allowed-tools` now includes `Bash(tea:*)`
- Help skill updated with Gitea platform support notes for `/ship`

## [personal-plugin 3.8.0] - 2026-01-18

### Changed
- visual-explainer: Updated skill documentation to reflect actual CLI behavior (removed non-existent `check-ready` command)
- visual-explainer: Updated tested results with latest testing data (4 documents, 17 images, multiple formats)
- visual-explainer: Added `google-genai` to core dependency list in documentation

### Fixed
- visual-explainer: Skill documentation now matches actual tool CLI options

## [personal-plugin 3.7.2] - 2026-01-18

### Added
- visual-explainer: **Infographic mode** (`--infographic` flag) for information-dense 11x17 inch page generation
- visual-explainer: Adaptive page count (1-6 pages) based on document complexity, word count, and content types
- visual-explainer: 8 page types: Hero Summary, Problem Landscape, Framework Overview, Framework Deep-Dive, Comparison Matrix, Dimensions/Variations, Reference/Action, Data/Evidence
- visual-explainer: Zone-based layout system with explicit typography specifications (headline/subhead/body/caption)
- visual-explainer: Page templates library with predefined layouts for each page type
- visual-explainer: Content type detection (statistics, process, comparison, hierarchy, timeline, framework, narrative, list, matrix)

### Changed
- visual-explainer: Concept analyzer now produces page recommendations with zone assignments when in infographic mode
- visual-explainer: Prompt generator creates information-dense prompts with explicit text specifications
- visual-explainer: CLI displays page plan summary including page types, content focus, and compression warnings

## [personal-plugin 3.7.1] - 2026-01-18

### Fixed
- visual-explainer: Image resizing for Claude's 5MB API limit (uses 3.5MB raw limit to account for base64 encoding overhead)
- visual-explainer: Windows path sanitization - removes invalid characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`) from output folder names

### Added
- visual-explainer: google-genai and Pillow dependencies in pyproject.toml
- visual-explainer: Technical notes section in SKILL.md with API details and tested results
- visual-explainer: DOCX conversion tip and input format handling table in SKILL.md
- visual-explainer: `--json` output mode for programmatic use
- visual-explainer: Image size limit and Windows path troubleshooting sections in README.md

### Changed
- visual-explainer: Uses google-genai SDK with `gemini-3-pro-image-preview` model
- visual-explainer: Default pass threshold recommendation: 0.75-0.85 for optimal quality/iteration balance

## [bpmn-plugin 2.2.0] - 2026-01-18

### Fixed
- bpmn2drawio: Lane-to-pool assignment now correctly tracks process_id for proper pool matching
- bpmn2drawio: Lane Y positions now start at 0 within each pool instead of cumulative across all pools
- bpmn2drawio: Subprocess parsing order fixed to set _is_subprocess property before generic element handling
- bpmn2drawio: Nested subprocess parsing now correctly sets _is_subprocess property
- bpmn2drawio: Boundary events now correctly parented to their attached subprocess with relative coordinates
- bpmn2drawio: Boundary event parent resolution in generator now checks subprocess cell IDs
- bpmn2drawio: Added missing boundaryEvent, subProcess, and callActivity styles to themes.py
- bpmn2drawio: Nested subprocess parent resolution now uses element.subprocess_id attribute

### Added
- Comprehensive edge case test file (examples/comprehensive_edge_case_test.bpmn)
- Converter fixes documentation (references/converter-fixes-20260118-123946.md)

## [personal-plugin 3.6.1] - 2026-01-18

### Changed
- `/research-topic` skill: Increased default timeout from 720s to 1800s (30 minutes) for deep research APIs
- `/research-topic` skill: Enhanced terminal UI with StreamingUI for real-time progress visibility
- `/research-topic` skill: Added `PYTHONUNBUFFERED=1` and `STREAMING_UI=1` environment variables for proper output streaming

### Fixed
- Research execution now displays live progress updates instead of buffered output

## [personal-plugin 3.6.0] - 2026-01-18

### Added
- `/research-topic` skill: Rich terminal UI with progress panels and status indicators
- `/research-topic` skill: Bug reporting system with automatic anomaly detection
- `/research-topic` skill: Parallel dependency checking (runs in background during clarification)

### Changed
- `/research-topic` skill: Dependency check now starts immediately and runs parallel to user interaction

## [personal-plugin 3.5.0] - 2026-01-18

### Added
- `/research-topic` skill: Audience profile detection (Phase 1.5)
  - Searches for existing profile in project, local, and global CLAUDE.md files
  - Allows confirmation or modification of detected profile for each session
  - Prompts for profile creation if none found, with template
  - Offers to save user-provided profile to global CLAUDE.md
- `/research-topic` skill: New `--no-audience` flag to skip profile detection
- `/research-topic` skill: Interactive API key setup wizard
  - Detailed instructions for obtaining keys from Anthropic, OpenAI, and Google
  - Direct links to each provider's API key management page
  - Collects keys interactively and creates/updates .env file
  - Shows masked key confirmation after setup
  - Warns if .env is not in .gitignore

### Changed
- `/research-topic` skill: Research prompts now include detected/collected audience profile
- `/research-topic` skill: Research Brief now shows Target Audience section with profile summary
- `/research-topic` skill: Execution Summary expanded from 14 to 15 steps

## [personal-plugin 3.4.0] - 2026-01-18

### Changed
- `/research-topic` skill: Clarified tool vs Claude responsibilities with new section
- `/research-topic` skill: Phase 5 now explicitly instructs Claude to read and synthesize provider outputs
- `/research-topic` skill: Phase 6 now explicitly instructs Claude to write synthesized markdown and generate DOCX via pandoc
- `/research-topic` skill: Execution Summary expanded from 9 to 11 explicit steps

### Fixed
- Research topic skill now properly guides Claude through post-tool-execution steps (synthesis and output generation)

## [personal-plugin 3.3.0] - 2026-01-18

### Fixed
- Cache deployment issue: v3.2.0 source code fixes were not deployed to marketplace cache
  - OpenAI and Gemini providers now properly call `_status_update` method from BaseProvider
  - Users should reinstall plugin to get the fixed version: `/plugin install personal-plugin@troys-plugins --force`

## [personal-plugin 3.2.0] - 2026-01-17

### Added
- Progress updates during polling for OpenAI and Gemini deep research (every 30s)

### Changed
- Increased default timeout from 180s to 720s for deep research APIs (OpenAI/Gemini can take 5-10 minutes)
- Clarification loop now REQUIRED in `/research-topic` skill unless `--no-clarify` specified
- Model version check step changed from conditional to recommended (skip with `--skip-model-check`)

### Fixed
- OpenAI and Gemini deep research timeout failures (300s was insufficient)
- Gemini SDK experimental API warnings now suppressed
- Documentation inconsistencies for timeout values (now consistently 720s)

## [personal-plugin 3.1.0] - 2026-01-17

### Added
- `/validate-and-ship` skill - Automated pre-flight checks and shipping workflow
  - Chains `/validate-plugin`, `/clean-repo`, and `/ship` in sequence
  - Stops only on blocking errors, continues through warnings
  - Supports `--skip-validate`, `--skip-cleanup`, `--dry-run` flags
- Stale branch pruning in `/ship` skill completion phase
  - Auto-prunes remote tracking branches that no longer exist
  - Cleans local branches where upstream is gone (merged only)

### Changed
- `/ship` skill now reports pruned stale branches in completion output

## [bpmn-plugin 2.1.0] - 2026-01-17

### Changed
- Version bump for consistency with personal-plugin release cycle

## [personal-plugin 3.0.0] - 2026-01-17

### Changed
- Major version bump for breaking changes in plugin structure and command conventions

## [bpmn-plugin 2.0.0] - 2026-01-17

### Changed
- Major version bump for breaking changes in plugin structure

## [bpmn-plugin 1.8.0] - 2026-01-16

### Fixed
- bpmn2drawio: Fix BFS rank assignment to properly re-queue successors when rank improves
- bpmn2drawio: Add flow validation logging in layout engine for debugging
- bpmn2drawio: Add fallback positions for elements not positioned by graphviz
- bpmn2drawio: Add subprocess-relative coordinate adjustment for proper Draw.io rendering
- bpmn2drawio: Improve connected element detection to include subprocess internals
- bpmn2drawio: Add pool parent assignment for laneless pools

## [2.5.0] - 2026-01-16

### Added
- `/create-plan` command for generating IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD)
  - Auto-discovers requirements documents in project
  - Synthesizes requirements across multiple documents
  - Generates phased implementation plan with work items and acceptance criteria
  - Includes requirement traceability matrix
- `/implement-plan` command for executing IMPLEMENTATION_PLAN.md via orchestrated subagents
  - Uses subagent orchestration pattern for context-efficient execution
  - Spawns subagents for implementation, testing, and documentation
  - Automatic test-fix loop until all tests pass
  - Updates PROGRESS.md and LEARNINGS.md tracking files
  - Commits after each work item, creates PR on completion

### Changed
- Updated CLAUDE.md with new commands and "Orchestration commands" pattern category
- Planning commands now include create-plan, plan-improvements, and plan-next

## [2.4.0] - 2026-01-15

### Added
- `schemas/command.json` - JSON Schema for command frontmatter validation
- Modular pattern files in `plugins/personal-plugin/references/patterns/`:
  - `naming.md` - File and command naming conventions
  - `validation.md` - Input validation and error handling patterns
  - `output.md` - Output files, directories, preview patterns
  - `workflow.md` - State management, resume, session patterns
  - `testing.md` - Argument testing and dry-run patterns
  - `logging.md` - Audit logging and progress reporting patterns
- `--strict` flag to `/validate-plugin` for failing on any pattern violation
- `--report` flag to `/validate-plugin` for generating detailed compliance reports
- Schema Validation Summary section to Q&A commands (define-questions, ask-questions, finish-document)
- 3 new command templates: `synthesis.md`, `conversion.md`, `planning.md`
- `docs/PLUGIN-DEVELOPMENT.md` - Step-by-step plugin developer onboarding guide
- Integration tests for validate-plugin and bump-version commands (37 new tests)
- Test fixtures for valid and invalid plugin structures
- "Common Development Mistakes" section in TROUBLESHOOTING.md (7 documented mistakes)
- `.github/workflows/validate.yml` - CI/CD validation pipeline with plugin validation, markdown linting, and help sync checks
- `--scorecard` flag to `/validate-plugin` for plugin maturity assessment (4 levels)
- Interactive parameter prompting to `/define-questions` and `/assess-document` with `--no-prompt` flag
- `QUICK-REFERENCE.md` - Single-page quick reference card for plugin developers (under 100 lines)

### Changed
- README command tables now use natural sentence truncation and hyperlink to source files
- BPMN plugin help.md now includes full descriptions with operating modes and examples
- Marketplace versioning decoupled from plugin versions (marketplace_version: 1.0.0)
- Pre-commit hook now blocks commits with new commands not documented in help.md
- Generator commands (assess-document, define-questions, analyze-transcript) now auto-create output directories
- `common-patterns.md` converted to index linking to modular pattern files
- All 5 command templates updated with explicit section order markers and pattern file references
- `/validate-plugin` now includes Phase 7: Pattern Compliance Checks
- Q&A commands now have uniform `--force` flag behavior and validation status output
- `/new-command` now offers 8 template options (added synthesis, conversion, planning)
- CONTRIBUTING.md now links to the plugin developer onboarding guide
- README.md now includes CI badges and links to QUICK-REFERENCE.md
- `/validate-plugin` now supports `--scorecard` for maturity assessment

## [2.3.0] - 2026-01-15

### Added
- `/remove-ip` command for sanitizing documents by removing company identifiers and intellectual property
  - Supports STANDARD mode (preserve context) and STRICT mode (maximum redaction)
  - Auto-detects company name from document content
  - Generates detailed redaction log with risk categorization
  - Mosaic attack protection in STRICT mode
  - Optional web research for public information verification

## [2.2.0] - 2026-01-15

### Added
- `WORKFLOWS.md` - Comprehensive workflow documentation for chaining commands
- `TROUBLESHOOTING.md` - Solutions for 19 common issues with symptom/cause/solution format
- `SECURITY.md` - Security model documentation and vulnerability reporting process
- `schemas/plugin.json` - JSON Schema for plugin.json with dependency support
- Integration test suite for Q&A workflow chain (30 tests)
- Shared test infrastructure (`tests/conftest.py`, `tests/helpers/`)
- GitHub Actions workflow for running tests on push/PR
- `--preview` flag to `/define-questions`, `/analyze-transcript`, `/bpmn-generator`
- `--force` flag to Q&A commands for bypassing schema validation
- `--audit` flag to `/clean-repo` and `/ship` for optional JSON audit logging
- Workflow state management with resume support for interrupted Q&A sessions
- Plugin namespace support (`/personal-plugin:command-name` syntax)
- Plugin dependency declaration support with semver version requirements
- Dependency verification for external tools (pandoc, graphviz) with platform-specific instructions

### Changed
- Updated `schemas/answers.json` with status and last_question_answered fields
- Enhanced `/validate-plugin` with namespace collision detection and dependency validation
- Added runtime schema validation to Q&A chain commands
- Extended `common-patterns.md` with 6 new patterns (dependency verification, performance expectations, schema validation, argument testing, output preview, workflow state management, audit logging)
- Added testing guidance to `CONTRIBUTING.md`
- Added performance expectations to long-running commands (`/plan-improvements`, `/test-project`, `/review-arch`)

### Fixed
- Documentation links in README.md now point to new WORKFLOWS.md, TROUBLESHOOTING.md, SECURITY.md

## [2.1.0] - 2026-01-14

### Added
- `/new-command` command for generating new command scaffolds from templates
- `/scaffold-plugin` command for creating new plugin directory structures
- `/check-updates` command for checking plugin version updates
- JSON schemas for command chain contracts (`schemas/questions.json`, `schemas/answers.json`)
- Command templates for 5 pattern types (read-only, interactive, workflow, generator, utility)
- `scripts/generate-help.py` for automated help.md generation
- `scripts/update-readme.py` for automated README command table updates
- `--dry-run` flag to `/ship`, `/clean-repo`, and `/bump-version` commands
- `--format` flag to `/define-questions` (json|csv), `/assess-document` (md|json), `/analyze-transcript` (md|json)
- Standard session commands (help, status, back, skip, quit) to all interactive commands
- Issue severity levels standardization (CRITICAL, WARNING, SUGGESTION)
- Standard argument validation error formats

### Changed
- `/consolidate-documents` now outputs to `reports/` directory
- `/develop-image-prompt` now outputs to `reports/` directory
- Extended pre-commit hook with help.md sync and timestamp format validation
- Updated CLAUDE.md with Utility commands pattern category
- All assessment commands now use consistent severity naming

### Fixed
- Output location consistency across all commands
- Argument validation messages now follow standard format

## [2.0.0] - 2026-01-14

### Changed
- Enhanced `/ship` skill with auto-review, fix loop, and merge workflow
  - Automatically reviews PR for security, performance, code quality, test coverage, and documentation
  - Fixes CRITICAL and WARNING issues automatically (up to 5 attempts)
  - Squash merges PR when all blocking issues resolved
- Improved bpmn2drawio test coverage from 87% to 92%

## [1.7.0] - 2026-01-14

### Added
- `/help` skill in personal-plugin with comprehensive command reference
- `/help` skill in bpmn-plugin with skill reference
- Documentation about help skill maintenance in CLAUDE.md and CONTRIBUTING.md

### Changed
- Renamed all commands to consistent action-object pattern:
  - `arch-review` → `review-arch`
  - `doc-assessment` → `assess-document`
  - `transcript-analysis` → `analyze-transcript`
  - `next-step` → `plan-next`
  - `cleanup` → `clean-repo`
  - `consolidate` → `consolidate-documents`
  - `wordify` → `convert-markdown`
  - `image-prompt` → `develop-image-prompt`
  - `troy-statusline` → `setup-statusline`
  - `fully-test-project` → `test-project`
- Renamed `help-commands` skill to `help`
- Merged `doc-review` command into `clean-repo` (enhanced Phase 3)
- Updated `review-arch` description to clarify it's for quick audits vs `plan-improvements`

### Removed
- `doc-review` command (merged into `clean-repo`)

## [1.6.0] - 2026-01-14

### Added
- `bump-version` command for automated version bumping across plugin files
- `validate-plugin` command for plugin structure and content validation
- `review-pr` command for structured PR review with security/performance analysis
- `help-commands` skill for command discovery and help system
- `references/common-patterns.md` with shared patterns documentation
- `CONTRIBUTING.md` with contributor guidelines
- `scripts/pre-commit` hook for validating plugin changes

### Changed
- Standardized timestamp format to `YYYYMMDD-HHMMSS` across all commands
- Added Input Validation sections to all argument-accepting commands
- Updated CLAUDE.md with Output Locations and Timestamp Format conventions
- Improved bpmn2drawio test coverage from 84% to 92% (49 additional tests)

### Fixed
- Removed forbidden `name` field from bpmn-generator.md and bpmn-to-drawio.md frontmatter
- Updated README.md with all 15+ commands (was missing 5)

## [1.5.0] - 2025-01-14

### Added
- `plan-improvements` command for generating improvement recommendations with phased implementation plan
- `fully-test-project` command for ensuring 90%+ test coverage, running tests, fixing failures, and merging PR

## [1.4.1] - 2025-01-10

### Fixed
- Remove name field from frontmatter to fix command discovery in personal-plugin
- Sync marketplace.json version with personal-plugin (1.1.0 to 1.4.0)

## [1.4.0] - 2025-01-09

### Added
- `image-prompt` command for AI image generation prompts from content
- `wordify` command for markdown to Word document conversion
- `consolidate` command for merging multiple document versions

### Fixed
- bpmn2drawio Python 3.14 / lxml compatibility fix
- bpmn2drawio fallback layout scaling and complex test fixes
- bpmn2drawio positioning of elements without DI coordinates
- bpmn2drawio visual layout issues with lanes and element positioning

### Changed
- Auto-detect and install dependencies in bpmn-plugin skill
- Run bundled bpmn2drawio tool directly without pip install
- Bundle bpmn2drawio Python tool in bpmn-plugin

## [1.3.0] - 2025-01-06

### Added
- Integrate bpmn2drawio Python tool into bpmn-to-drawio skill
- Update examples with AI Community Management Process

### Changed
- Update BPMN-to-DrawIO Conversion Standard to v1.1

## [1.2.0] - 2025-01-05

### Added
- `bpmn-to-drawio` skill for converting BPMN XML to Draw.io format

## [1.1.0] - 2025-01-04

### Added
- `bpmn-plugin` for BPMN 2.0 XML generation from natural language or markdown
- `cleanup` command for repository cleanup and organization
- `finish-document` command for extracting questions, answering interactively, and updating documents

### Changed
- Add YAML frontmatter to all commands
- Update README and CLAUDE.md for marketplace structure

## [1.0.0] - 2025-01-03

### Added
- Initial marketplace structure with multi-plugin format
- `personal-plugin` with core commands:
  - `arch-review` for deep architectural review
  - `doc-review` for documentation audit and cleanup
  - `transcript-analysis` for meeting transcript conversion
  - `define-questions` for extracting questions from docs
  - `ask-questions` for interactive Q&A sessions
  - `doc-assessment` for document quality evaluation
  - `next-step` for analyzing repo and recommending actions
  - `troy-statusline` for custom Windows/PowerShell status line
- `ship` skill for git workflow automation

[Unreleased]: https://github.com/davistroy/claude-marketplace/compare/v2.4.0...HEAD
[2.5.0]: https://github.com/davistroy/claude-marketplace/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/davistroy/claude-marketplace/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/davistroy/claude-marketplace/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/davistroy/claude-marketplace/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/davistroy/claude-marketplace/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/davistroy/claude-marketplace/compare/v1.7.0...v2.0.0
[1.7.0]: https://github.com/davistroy/claude-marketplace/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/davistroy/claude-marketplace/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/davistroy/claude-marketplace/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/davistroy/claude-marketplace/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/davistroy/claude-marketplace/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/davistroy/claude-marketplace/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/davistroy/claude-marketplace/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/davistroy/claude-marketplace/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/davistroy/claude-marketplace/releases/tag/v1.0.0
