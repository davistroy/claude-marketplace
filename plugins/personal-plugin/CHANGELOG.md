# Changelog

All notable changes to personal-plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [11.9.0] - 2026-07-30

Mitigations for #232 — a session serving a stale skill body against a current bundled tool. Characterized in LAB_NOTEBOOK Entry 066; the root cause is **not** an upstream loader bug.

### Added
- **`task-sync`: version-skew preflight.** Compares the version segment of `$CLAUDE_PLUGIN_ROOT` (the path the session is actually being served from) against `installed_plugins.json`, and warns when they differ. A warning, not a gate — an older body is usually still usable and the caller should know rather than be blocked. Only warns on a segment that parses as a version, so a repo-source `PLUGIN_DIR` reports "unknown" instead of a false positive.

### Changed
- **`task-sync` parses the keys the tool emits, instead of a key list restated in prose.** The skill now enumerates the plan JSON's actual top-level keys, maps each to its handling, and **halts on an unrecognized key** rather than ignoring it. The known-key list is documented as a convenience and explicitly not the contract. This is what failed in #232: a body predating `orphans` parsed for six keys, silently dropped the seventh, and reported the backlog fully reconciled while discarding the exact finding `orphans` was added to surface. Enumerating what is present cannot fail that way, and a *missing* key is the benign direction (treat as empty).

### Notes
- Evidence for the mechanism is on disk: Claude Code writes `.in_use/<pid>` refcount markers into each served cache version directory, and the count a live process holds scales with its age (a session from 2026-07-15 pinned four personal-plugin versions; one from 2026-07-30 pinned one). `claude plugin update` prints "Restart to apply changes" — it provisions the next process, not the running one.
- **Pruning old cache version directories is now documented as unsafe** and was rejected as a candidate fix. The `.in_use` markers exist to stop the cache GC deleting a tree a live process is still serving; pruning would break running sessions.

## [11.8.0] - 2026-07-30

Plan identity for `/implement-plan`'s state file (#235). A completed run's state was inherited by a different plan written to the same path, and the run reported success having implemented nothing.

### Added
- **`plan_identity` in `.implement-plan-state.json`** — `generated`, `total_phases`, `phase_titles`, and the `N.M` item ids, written at STARTUP Step 2 and verified at STARTUP Step 0 *before* the IN_PROGRESS check and before anything else in the file is trusted. `plan_file` is a path, and completed plans are archived to `docs/archive/IMPLEMENTATION_PLAN-vN.md` while the next plan takes the same default path — so the path always matches and proves nothing. On mismatch the command reports both fingerprints field by field and offers start-fresh (recommended) / resume-anyway / abort; a state file with no `plan_identity` at all gets the same prompt rather than a guess.
- **Guard against reporting a finished plan as this run's work** — if the identity matches but nothing remains, `/implement-plan` now says the plan is already complete and stops, instead of routing to `ALL_COMPLETE` and generating a completion report describing items it did not implement.

### Fixed
- **FINALIZATION deleted the state file before the report that reads it.** `rm -f .implement-plan-state.json` was Final Step 0, four steps ahead of the COMPLETION REPORT, whose generation rule 1 is "read the state file" and whose documented fallback for a missing file is "No work items were completed" — so a fully successful run had to either report the opposite of the truth or keep the file. Deletion moves to Final Step 4, after the report, and is explicitly the last action of the command.
- **Item ids are parsed with `match()`, not anchored to the start of the heading.** The completion marker is meant to be a suffix but is not reliably one: two of plan v13's 19 items came back as `#### ✅ Completed 2026-07-30 — 7.1 Title`, which an anchored `^#### [0-9]+\.[0-9]+` silently dropped — an item count of 17 where the plan has 19. `references/plan-template.md` now states the append-only rule normatively rather than in passing.

### Notes
- The fingerprint deliberately excludes everything `/implement-plan` mutates while a plan runs — `**Status:**` fields, the `**Completed:**` header, and item heading *titles* (decorated on completion). Verified against `docs/archive/IMPLEMENTATION_PLAN-v12.md`, which executed 42/42 items: the four recorded fields are byte-identical before and after that run. A fingerprint over the file text, or over heading titles, would differ from itself after the first item and reject every legitimate resume.

## [11.7.0] - 2026-07-30

Close-the-loop correctness backlog (Phase 4 of the E062 plan, #231). Repairs a scarred `/ultra-plan` skill left behind by a prior 1–6 → 0–5 phase renumbering.

### Fixed
- **`ultra-plan/SKILL.md` phase numbering** — 29 sites (8 `###` sub-headings, 18 cross-reference lines, 2 anchors, plus a `Phase 1-4` → `Phase 0-3` range) still named the old 1–6 phase scheme after only the `##` headings were renumbered to 0–5. `evals/skills/ultra-plan.eval.md:43` copied the same defect and is fixed atomically with the skill so a passing eval doesn't regress. `:350` ("Change sets (Phase 2c)") was the one reference that had survived correctly and is untouched, along with the rest of its mapping table.
- **Phantom L0–L4 scope taxonomy removed** — `ultra-plan` gated the Phase 0 constitution check, ADR generation, and creative branching on an "L-level per plan-gate classification" that `plan-gate` never defines (it emits Path recommendations, not scope levels). Deleted at all 8 `SKILL.md` sites and both `references/adr-template.md` sites; the existing trigger questions (already equivalent to the L3+/L4+ tests) now gate alone, and the unreachable Phase-0 skip condition (b) is removed outright since ultra-plan is only reached via plan-gate's Path D.5.
- **`/unlock` read a variable nothing sets (#217, Phase 5)** — `skills/unlock/SKILL.md` read `$TROY`, which is unset on this machine while `BWS_ACCESS_TOKEN` is set and current; `/unlock` hard-stopped at Step 2 on every invocation and never reached `bws`. Now reads `BWS_ACCESS_TOKEN` as the primary source, with `$TROY` kept as an explicitly-labelled deprecated fallback (same rename in `skills/new-project/SKILL.md` and `references/api-key-setup.md`). `allowed-tools` widened to cover every command Step 3 actually issues (`python3`, `mktemp`, `chmod`, `rm`, `source`, `test`, `unset`) — the Linux/macOS `bws` call was also rewritten from an inline `VAR=value cmd` prefix (which `Bash(bws:*)` does not cover) to an `export`/`unset` pair, matching the Windows path's existing pattern. The one genuine probe leak, `api-key-setup.md`'s bare `bws secret list` diagnostic (prints every secret's plaintext value), is replaced with `bws secret list >/dev/null; echo $?`. `disable-model-invocation: true` is unchanged. Manual `/unlock` verification is owner-only (ADR-0009/D32 — CI carries zero secrets); the skill now documents a pre-run cache-vs-repo diff against #232 before that manual run is trusted.
- **`CLAUDE.md`'s inventory was never generated, so it carried 8 defects while README carried none (#206, Phase 6)** — `scripts/update-readme.py` hard-coded `README.md` as its only target, which made the `update-readme.py --check` CI gate green-by-construction on `CLAUDE.md` drift. `main()` now scans once and feeds a target list; `scan_plugin()` is unchanged (it already returned 23/29/9/2), joined by a `scan_agent_names()` sibling for the `agents/` directory README has no table for. Cleared: 5 personal-plugin skills missing from the tree (`archive-project`, `clear-prep`, `fleet-health`, `new-project`, `task-sync`), `build-cfa-deck` missing from slide-gen, and the absent `plugins/personal-plugin/agents/` (10 files) and `plugins/slide-gen/references/` directories. Regeneration is scoped by a `BEGIN:inventory`/`END:inventory` anchor pair **and** by directory key, so the four hand-written annotations inside the fence and the curated "Command Patterns" table outside it are structurally unreachable. Negative-tested before wiring per the standing rule: a deleted skill name yields **exit 2**, restore yields **0** — and the test itself exposed two fail-*open* paths (anchors absent, plugin node absent) that had exited 0; both now exit 1. Also fixed in `CLAUDE.md`: the dangling `IMPLEMENTATION_PLAN.md` pointer to a plan archived under `docs/archive/`, and the "Deprecated" section, which named 1 of 5 retired commands and omitted D42's dropped `skills/help/` requirement.
- **3 generator templates and the `ask-questions` residual still minted prose `(y/n)` prompts and the legacy `[A]/[B]/[C]/[D] Custom/[S] Skip` menu (#223, #233, Phase 7 item 7.2)** — `references/patterns/output.md:42`, `references/templates/generator.md:199`, and `references/templates/synthesis.md:281` now ask via `AskUserQuestion` (Save/Discard, Proceed/Cancel) instead of rendering `Save this file? (y/n):` / `Proceed with synthesis? (y/n):` into every artifact built from them. `commands/ask-questions.md:409-424`'s `## Example Interaction` — the **second** false green from PR #222 item 7.5 (the first is LAB_NOTEBOOK `:869-878`) — no longer contradicts its own file's `:145`/`:175`; it now shows an `AskUserQuestion` call and a selected-option response. `references/templates/interactive.md` is deliberately untouched (its one-at-a-time interview contract).
- **The 4 model-invocable write-consent gates converted to `AskUserQuestion` (D64, #223, Phase 7.1)** — `security-analysis:19-28`, `wiki:207`, `wiki:241`, and `task-sync:247` were prose blockquotes ending `(y/n)`/`(yes/no)`, inconsistent with the `AskUserQuestion` pattern PR #222 established for `lab-notebook` and `create-wiki`. `security-analysis`'s conversion is a 3-option question ("Yes — dependencies only" / "Yes — full scan" / "No") so its `--dependencies-only`-on-confirm default and `--quick` override are still conveyed, not flattened away; `task-sync`'s public-repo publish gate is a 3-way question ("Yes" / "No" / "Show plan again") preserving its warning text verbatim. `AskUserQuestion` added to `allowed-tools` on all three skills (`security-analysis` inserted before the trailing ` #` comment to avoid re-triggering the colon-space frontmatter-collapse hazard documented in E061; `wiki` and `task-sync` didn't have it). Each invocation-source condition (skip the gate on direct user invocation) is preserved verbatim in meaning. D39's unscoped `Bash` grant and its inline justification comment on `security-analysis` are untouched.
- **All 12 unbacked freshness stamps deleted, plus the phantom `check-models` reference and both templating generators (D62, #218, Phase 8.1)** — `research-models.md` lost its `Last Verified` column (nothing ever probes OpenAI/Google IDs, and the file said so on the very next line), the `check-models` command it named in Resolution Order (deliberately deleted per archived plan v6, reference never cleaned up), and the phantom `## Model Check Output Examples` section documenting that command's output. Eight more "default as of"/"Last Updated" stamps removed across `flag-consistency.md`, `visual-explainer/SKILL.md` (×2), `accessibility-annotator/SKILL.md`, `unlock/SKILL.md` (the same BWS project-id constant, corrected identically at all 3 duplicated sites), `spark-recon/SKILL.md`, and `docs/PLUGIN-DEVELOPMENT.md`, keeping the underlying "verify with the provider if errors occur" caveats where genuinely warranted and dropping only the date that implied someone checked. `explain-project/SKILL.md` and `create-wiki/SKILL.md` — the two generators that were minting new instances of the defect into every document they produce — no longer template a verification-date field.

<!-- Later phases of the E062 backlog append here -->

## [11.6.0] - 2026-07-29

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

## [11.5.1] - 2026-07-29

### Fixed
- `commands/new-skill.md`: `/new-skill` aborted on **every** invocation in **every** directory. Lines 308 and 316 documented the dynamic-injection syntax using the double-backtick form `` `` !`cmd` `` `` — which the harness's pre-pass treats as **live**, not escaped — so invoking the command executed the literal placeholder `cmd` (exit 127). A non-zero exit throws and aborts prompt expansion; it does not degrade to empty output. The command also grants no `Bash`, so the permission gate would have rejected the injection regardless. Rewritten to the inert nested form (`` `!`cmd`` ``) already used by `prime` and `arch-review`, plus a gotcha explaining that the tidier-looking form is the dangerous one.
- `references/templates/skill.md`: carried the same live form, seeding it into every skill `/new-skill` scaffolds. Now inert, and documents the two rules authors need — injections expand at parse time (before `$ARGUMENTS` exists) and a non-zero exit aborts skill load.
- `skills/leak-risk-audit/SKILL.md`: aborted on **every** invocation in **every** directory. `` !`ls -la <dataset-path>` `` is a bash syntax error (`<`/`>` are redirects, exit 2), and the placeholder could never have been substituted — injections expand before arguments are parsed. Replaced with a Bash-tool invocation on the resolved path, matching the precedent already documented in `skills/arch-review/SKILL.md:44`.

## [11.5.0] - 2026-07-29

### Fixed
- `skills/research-topic`: the Claude research leg failed on **every** dispatch. Its request body sent `thinking: {"type": "enabled", "budget_tokens": N}`, a parameter **removed** (not deprecated) from the Messages API, which returns HTTP 400 on the entire current model family — `claude-opus-4-8` and `claude-opus-5` alike. Depth is now expressed as `thinking: {"type": "adaptive"}` plus `output_config: {"effort": ...}`. Closes #189.
- `references/research-provider-protocols.md`: the Claude leg's fast-fail now also catches a **safety refusal**, which arrives as HTTP 200 with `stop_reason: "refusal"`, no `error` body, and empty or partial content. The previous three checks (curl exit, HTTP status, `error` key) all passed it, so a declined request wrote a silently empty research report that then flowed into synthesis. Handling this is part of the Opus 5 move, which is what introduces the path.

### Changed
- `skills/research-topic`: default Claude model `claude-opus-4-8` → `claude-opus-5` (same pricing tier, drop-in). Updated in all five places it was duplicated — `SKILL.md`, `references/research-models.md` (×3 tables), `references/api-key-setup.md`.
- `skills/research-topic`: the depth ladder is re-derived, not translated — `budget_tokens` was a thinking-token ceiling while `effort` governs thinking depth *and* total token spend, so there is no 1:1 mapping. brief → `low`/8,000, standard → `medium`/16,000, comprehensive → `high`/32,000. `max_tokens` now scales with depth because it caps thinking **plus** response text.
- `references/research-provider-protocols.md`: Claude leg `curl --max-time` 600s → 900s, sized against the comprehensive tier's 32,000-token ceiling (~9 min at ~60 tok/s).

### Notes
- The ladder deliberately stops at `high` rather than `xhigh`/`max`: Anthropic requires `max_tokens` >= 64,000 at those levels, which cannot finish inside a non-streaming request. Converting the leg to streaming is tracked separately.

## [11.4.1] - 2026-07-29

### Fixed
- `tools/task-sync`: `sync --apply` no longer aborts on every push. `providers/github.py` appended `--remove-milestone`, a flag `gh` does not have (verified against gh 2.45.0), whenever a pushed task had no milestone — which is nearly always, since `task_to_issue_fields` always emits the field. The whole `apply` raised and left the run partially applied. A milestone is now cleared only when one is actually set, and via `gh api ... -X PATCH -F milestone=null` (portable across gh versions; `-F` sends a real JSON null where `-f` would send the string `"null"`). Closes #212.

## [11.4.0] - 2026-07-29

### Fixed
- `tools/task-sync`: a `priority/*` or `status/*` label whose suffix the tool does not recognize is no longer silently discarded on pull and then **deleted from the tracker** on the next push. `is_managed_label` now requires both a managed prefix and a recognized suffix, so an unknown label stays in the user label set and survives the round-trip (closes #208).

### Added
- `tools/task-sync`: `P0` is now a valid priority (`VALID_PRIORITIES` is `P0`-`P4`). Previously the highest-severity level was the one value the tool could not represent, so a `priority/P0` label mapped to no priority at all.

## [11.3.0] - 2026-07-22

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

## [11.2.1] - 2026-07-18

### Fixed
- `tools/task-sync`: `init` now persists `config.gitea_url` from the origin remote instead of leaving it unset (closes #173).
- `tools/task-sync`: `_build_provider` now falls back to the tea CLI config (`~/.config/tea/config.yml`) for the Gitea base URL and token when `$GITEA_URL`/`$GITEA_TOKEN` are unset, with env vars overriding tea config when both are present (closes #174).
- `skills/task-sync/SKILL.md` + config-reference docs now accurately describe this env → tea-config → unset resolution order (closes #172).

## [11.2.0] - 2026-07-18

Adds **task-sync**: a new skill that keeps a per-repo `tasks.json` (with a generated `TASKS.md` view) reconciled with the repo's issue tracker (GitHub via `gh`, Gitea via its REST API). Built per ADR-0010 / D34.

### Added
- **task-sync skill + bundled Python tool** (`plugins/personal-plugin/tools/task-sync/`, stdlib-only): direct commands (`init`/`list`/`add`/`edit`/`done`/`remove`/`status`) plus a `sync` subcommand driven by a `plan → decide → apply` protocol — `sync --plan --json` computes creates/pushes/pulls/conflicts/confidentiality findings read-only, the skill renders them and collects explicit decisions, `sync --apply` executes exactly what was decided.
- **3-way reconcile engine** classifying each task against its last-synced base (new-local/new-remote/changed-local/changed-remote/changed-both/unchanged); conflicts (both sides changed) are always surfaced for an explicit user decision and never auto-resolved, with last-write-wins offered only as a recommendation.
- **Confidentiality scanner**: secret/token detection (`ghp_`/`sk-`/AWS keys/PEM/bearer tokens) plus generic structural detectors (email/phone/IP/internal hostname/ticket/asset id) and per-repo `sensitive_terms` config, gating every outbound create/push; `CRITICAL` findings require an explicit `keep`/`redact`/`remove`/`anonymize` disposition before anything leaves the machine.
- **Public-repo visibility guardrail**: warns and requires explicit confirmation before the first push/create of a sync session against a public GitHub/Gitea repo.
- **Prune**: `done` tasks whose linked issue has been closed longer than `config.prune_closed_after_days` (default 30) are pruned during `sync --apply` only.
- New `Task Sync Tests` CI job (non-required through Phases 1–5, added to branch protection in Phase 6) and its lockfile added to the dependency-audit gate.

## [11.1.0] - 2026-07-16

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

## [9.2.0] - 2026-05-14

### Changed
- Coordinated minor bump across all plugins and marketplace (build-cfa-deck was the trigger; bpmn-plugin and personal-plugin bumped for release cadence)

## [9.1.0] - 2026-05-10

### Added
- **Model routing in planning pipeline**: Per-task `**Model Tier:**` field (haiku/sonnet/opus) in plan template; `create-plan` and `plan-improvements` assign tiers using rubric at plan-time; `implement-plan` dispatches to named sub-agents (`haiku-implementer` / `sonnet-implementer` / `opus-implementer`) with escalation pattern
- **Named implementer agents** in `.claude/agents/`: model pinned in frontmatter, plans reference agent name (not model) — swap models globally without touching plans
- **Plan template Rule 17**: Model Tier field with full haiku/sonnet/opus rubric and backward-compatibility guarantee (items without Model Tier default to `sonnet`)

### Changed
- **Implement-plan**: Per-item `**Model Tier:**` takes priority over phase-level execution hints; state file adds `item_model_tiers` map; escalations logged to LEARNINGS.md with single re-dispatch at next tier
- **Create-plan Phase 3.1**: Step 5 assigns model tier with rubric and escalation criterion guidance; Phase 3.2 Execution Hints updated to position per-item tiers as primary, phase hints supplementary
- **Plan-improvements**: Work item construction now includes Model Tier as field 2 with inline rubric

### Fixed
- **arch-review**: Replaced parse-time bash hooks with model-driven Bash/Read calls (removes hook dependency from review workflow)

## [9.0.0] - 2026-04-30

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

## [7.0.1] - 2026-04-19

### Changed
- Added mandatory Phase 0 to `/prime` skill to read `LAB_NOTEBOOK.md` before any other analysis when present

## [6.8.0] - 2026-04-11

### Fixed
- Added missing `## Instructions` section to `plan-next`, `review-arch`, and `test-project` commands for pattern compliance

## [6.7.2] - 2026-04-02

### Changed
- Enhanced `/prime` skill to read `LAB_NOTEBOOK.md` when present — extracts Decision Log, Open Action Items, recent experiment entries, and Current Baseline into the prime report

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

## [6.4.0] - 2026-03-30

### Added
- `lab-notebook` skill — initialize mandatory experiment logging combining scientific notebook, ADR, and incident postmortem patterns
- GITHUB_ERRORS.md error check log tracked at repo root

### Changed
- Enhanced `explain-project` skill with `--update` incremental mode, runtime data verification phase (Phase 3.5), glossary hyperlink navigation, production number sourcing rules, document freshness metadata, and "Known Limitations" / "Operational State" sections
- Updated README.md skill count and table (15 → 16 skills)
- Updated CLAUDE.md directory listing with lab-notebook skill
- Updated help skill with lab-notebook entry

## [6.3.0] - 2026-03-27

### Added
- `accessibility-annotator` skill — analyze technical documents for CS/ML concepts and add explanation annotations for non-CS readers
- `explain-project` skill — generate comprehensive annotated technical overview document for non-technical stakeholders

### Changed
- Updated README.md skill count and table (11 → 15 skills)
- Updated CLAUDE.md directory listing with new skills
- Added missing CHANGELOG entry for v6.2.0

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

## [4.0.0] - 2026-02-16

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

## [3.14.0] - 2026-02-15

### Changed
- `/implement-plan` command: Removed Ralph Wiggum loop dependency, replaced with native subagent orchestration pattern
  - Main agent now acts as thin loop controller using Task tool directly
  - Added explicit "Context Window Discipline" rules table
  - Instructions use blockquoted subagent prompts with `subagent_type: "general-purpose"`
  - Progress tracking via TaskCreate/TaskUpdate instead of external loop state
  - Added "Do not stop early" directive to ensure full plan completion

## [3.13.0] - 2026-01-27

### Added
- `/summarize-feedback` skill: Synthesize employee feedback from Notion Voice Captures into a professional .docx assessment document
- Bundled `feedback-docx-generator` Python tool for .docx document generation

## [3.12.0] - 2026-01-26

### Added
- Help skill updated with `/unlock` skill listing and detailed usage documentation

### Changed
- Version bump to 3.12.0

### Removed
- `SHIP_GITEA_PLAN.md` planning document (completed, no longer needed)

## [3.11.1] - 2026-01-26

### Added
- `/unlock` skill: Unlock Bitwarden vault and load project secrets into environment
  - Reads master password from `~\.claude\.env` (local, not in repo)
  - Auto-detects project name from working directory
  - Loads secrets from `dev/<project>/api-keys` in Bitwarden
  - Recovered from plugin cache (was installed but missing from source repo)

## [3.11.0] - 2026-01-26

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

## [3.7.2] - 2026-01-18

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

## [3.7.1] - 2026-01-18

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

## [3.6.1] - 2026-01-18

### Changed
- `/research-topic` skill: Increased default timeout from 720s to 1800s (30 minutes) for deep research APIs
- `/research-topic` skill: Enhanced terminal UI with StreamingUI for real-time progress visibility
- `/research-topic` skill: Added `PYTHONUNBUFFERED=1` and `STREAMING_UI=1` environment variables for proper output streaming

### Fixed
- Research execution now displays live progress updates instead of buffered output

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

## [3.3.0] - 2026-01-18

### Fixed
- Cache deployment issue: v3.2.0 source code fixes were not deployed to marketplace cache
  - OpenAI and Gemini providers now properly call `_status_update` method from BaseProvider
  - Users should reinstall plugin to get the fixed version: `/plugin install personal-plugin@troys-plugins --force`

## [3.2.0] - 2026-01-17

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

## [3.1.0] - 2026-01-17

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

## [3.0.0] - 2026-01-17

### Changed
- Major version bump for breaking changes in plugin structure and command conventions
