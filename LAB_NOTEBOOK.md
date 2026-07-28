# Claude Marketplace — Lab Notebook

**Project:** Claude Code plugin marketplace — three plugins (`personal-plugin`, `bpmn-plugin`, `slide-gen`) providing 23 commands and 40 skills for documentation, architecture review, research, BPMN modeling, presentation generation, and workflow automation.
**Started:** 2026-04-30
**Systems:** GitHub (davistroy/claude-marketplace), Claude Code CLI (Windows 11), installed via `/plugin marketplace add`

---

## Decision Log

Decisions are tracked here with their lifecycle. When a decision is revisited, update its status to SUPERSEDED and link to the new entry. Never delete old decisions. For decisions originating in another project's notebook, note the source.

| # | Decision | Date | Status | Entry | Alternatives Considered |
|---|----------|------|--------|-------|------------------------|
| D1 | Skills use nested dirs (`skills/name/SKILL.md`), commands use flat files (`commands/name.md`) | 2025-01-03 | ACTIVE | Pre-notebook | Claude Code loader requires this; flat skill files silently fail |
| D2 | Skills MUST have `name` in frontmatter; commands MUST NOT | 2025-01-10 | ACTIVE | Pre-notebook | Discovered via silent discovery failures — no error, just missing |
| D3 | Do NOT declare `tools` or `hooks` in plugin.json | 2026-03-31 | ACTIVE | Pre-notebook | `tools` → "Unrecognized key" error; `hooks` → "Duplicate" error (auto-discovered) |
| D4 | Shared plan template (`references/plan-template.md`) for create-plan and plan-improvements | 2026-03-04 | ACTIVE | Pre-notebook | Avoids template drift between the two plan generators |
| D5 | Replace research-orchestrator Python tool with 3 parallel `context:fork` subagents | 2026-04-21 | ACTIVE | Pre-notebook | Python tool (27 files): complex deps, cross-platform issues. Subagents: simpler, no deps. Trade-off: lost real-time streaming progress |
| D6 | Consolidate audit/recon skills into shared reference + config layer | 2026-04-21 | ACTIVE | Pre-notebook | ~50% LOC reduction. Alt: keep duplicated — rejected due to maintenance burden |
| D7 | hooks.json uses record format (keyed by event), not array | 2026-03-31 | ACTIVE | Pre-notebook | Array format broke with "expected record, received array". `type: prompt` also removed — only `type: command` |
| D8 | Deprecate review-pr, help skills — superseded by native `/review`, `/help` | 2026-04-21 | ACTIVE | Pre-notebook | Native commands are maintained by Anthropic; custom versions drift |
| D9 | Plan template: drop `Parallelizable` field, consolidate into `Execution Mode` | 2026-04-30 | ACTIVE | E001 | Two fields carried the same signal; `Execution Mode` is more expressive (Sequential/Parallel/Worktree-Isolated) |
| D10 | Plan template: add `Depends On` field to work items for intra-phase dependency tracking | 2026-04-30 | ACTIVE | E001 | Previously only phase-level dependencies existed; item-level deps were only in the disconnected Parallel Work table |
| D11 | Fold Lab Notebook A2, A3, A4 into gap-analysis implementation plan Phase 5 | 2026-04-30 | ACTIVE | E002 | Execute separately — rejected, they naturally fit Phase 5's implement-plan updates |
| D12 | Fix `/ultraplan` vs `/ultra-plan` reference ambiguity (no full rename) | 2026-04-30 | ACTIVE | E002 | Full rename — rejected, breaking change for user muscle memory. Hyphen already distinguishes. |
| D13 | Constitution constraints live in CLAUDE.md, not separate constitution.md | 2026-04-30 | ACTIVE | E002 | Separate constitution.md (Spec Kit pattern) — rejected, artifact sprawl for solo-builder context |
| D14 | Name the implementer agents `haiku-implementer` / `sonnet-implementer` / `opus-implementer` (agent name encodes tier), referenced by plan by name only | 2026-05-10 | ACTIVE | E005 | Use `model:` param directly in Agent calls — rejected because it couples model selection to plan content; a global model swap would require editing every plan |
| D15 | One escalation per item allowed (lower → next tier); accept at the highest tier even if imperfect | 2026-05-10 | ACTIVE | E005 | Unlimited escalation loop — rejected because it can cycle; capping at one step keeps orchestrator budget bounded |
| D16 | Orchestrator advisory note in `implement-plan.md` recommends Opus for large plans; not enforced programmatically | 2026-05-10 | ACTIVE | E005 | Skip the note — rejected because a cheap orchestrator with wrong tier assignment costs more than its token savings |
| D17 | Version source of truth is always `origin/main`, never the local working tree | 2026-05-14 | ACTIVE | E006 | (No fix was needed for the misdiagnosed slide-gen "drift" — the 1.1.0 local plugin.json was an unpushed pre-session edit); accepting local state as truth — rejected, it caused version-bump math on a stale base |
| D18 | Use `git checkout <branch> -- <path>` to cherry-pick a single file from a stale branch rather than rebasing the whole branch | 2026-05-14 | ACTIVE | E006 | Rebase the whole branch — rejected, it drags in all the conflicting version changes; file-level checkout is surgical |
| D19 | Plugin cache freshness is governed by install-side origin/main tracking, not by manual local reinstall | 2026-07-08 | ACTIVE (corrected E017) | E007 | Manual reinstall (A1/A7 premise) — superseded; cache already tracks GitHub origin automatically. The real risk is the local dev clone lagging origin (second occurrence of D17's root cause). **Correction (E017, item 1.4):** the original wording cited an `autoUpdate: true` setting *in marketplace.json* — verified inaccurate; `.metadata` holds only description/marketplace_version/schema_version. Auto-propagation is Claude Code's install-side default for GitHub-sourced marketplaces, NOT a repo-declared flag. |
| D20 | Agent `model:` fields use tier aliases (haiku/sonnet/opus/inherit), never pinned IDs (ADR-0005, Accepted) | 2026-07-08 | ACTIVE | E009/E010 | Pinned + periodic review — rejected, drifted twice undetected (9.1.0→9.3.0) |
| D21 | Skills-first authoring: new functionality ships as skills; commands/ frozen legacy; new-command deprecated, patterns ported to /new-skill --pattern (ADR-0006, Accepted) | 2026-07-08 | ACTIVE | E009/E010 | Mass-migrate 24 commands — rejected (churn, zero functional gain); status quo — rejected (diverges from official direction) |
| D22 | Distribution safety = branch-protection-only (required CI checks + PR-required 0-approvals + enforce_admins=false), NOT a stable/tagged release channel (ADR-0007, Accepted) | 2026-07-16 | ACTIVE | E017 | Stable/tagged channel + consumer pinning — rejected as disproportionate for a solo marketplace; required approving review — rejected (bus factor 1 deadlock); status quo — rejected (the Critical PLAT-001) |
| D23 | slide-gen = external-dependency plugin (the `sg` engine stays in the private `davistroy/slide-generator` repo) with a fail-fast preflight, NOT vendored in-tree (ADR-0008, Accepted) | 2026-07-16 | ACTIVE | E022 | Vendor engine per ADR-0002 — rejected (large cross-repo import + sync burden); deprecate slide-gen — rejected (actively used by owner). Consequence: owner-only until slide-generator is public |
| D24 | mypy enforced as a count-RATCHET (baselines bpmn 57 / visual-explainer 101, fail on net-new errors) rather than zeroing the 152 pre-existing errors. **UPDATE (E031, #129): baselines reached 0 — all 3 tools now mypy-clean; the ratchet is now a hard zero-errors gate** | 2026-07-16 | SUPERSEDED by D33 (ratchet retired 2026-07-17; zero-goal still ACTIVE) | E020/E031 | Full 152-error cleanup — originally deferred (disproportionate); done incrementally in E031 (both tools 0, genuine fixes, tests green). Leave advisory — rejected (the SE-04/QA-05/PLAT-006 finding) |
| D25 | Dependabot GitHub-Actions version bumps are MERGED as-is (they update both the pinned SHA and the `# vN` comment, preserving Phase-4 SHA-pinning), NOT closed. Corrects Action Item A1's premise. | 2026-07-16 | ACTIVE | E026 | Close + let dependabot "re-propose SHA bumps" (A1's plan) — rejected: dependabot's bump ALREADY is the SHA bump; closing just loses the update. Pin to floating `# vN` tags — rejected (defeats supply-chain pinning) |
| D26 | Decompose visual-explainer `cli.py` into 6 modules (terminal / cli_args / io_utils / reporting / pipeline + thin cli entry); cross-module *patchable* symbols referenced module-qualified so `unittest.mock.patch` intercepts at one point; test patch strings repointed to defining module | 2026-07-16 | ACTIVE | E027 | Fewer/larger modules — rejected (reporting+pipeline still 780/490 LOC, but further splitting fragments cohesion); keep monolith + only add tests — rejected (37%→85% needs testable units, not one 1,814-line file); `from .terminal import x` in consumers — rejected (binds a copy, defeats single-point patching) |
| D27 | Parallel image generation defaults to `concurrency=3` (memory-bounded via `asyncio.Semaphore`), parallel-by-default; `--concurrency 1` restores exact serial behavior | 2026-07-16 | ACTIVE | E030 | Default 1 / opt-in — rejected (feature dormant, near-zero value by default); unbounded `gather` — rejected (4K buffers breach the 1.5 GB ceiling). 3 chosen per PERF-05; rate-limit spikes handled by existing 429 backoff |
| D28 | Python 3.10/3.12 CI coverage added as a NON-required advisory `python-compat` job, NOT by expanding the required job matrices | 2026-07-16 | ACTIVE | E033 | Expand required `Run Tests`/tool matrices + lockstep branch-protection required-check rename (issue's literal acceptance) — rejected by owner as disproportionate deadlock-risk for a P6 item; defer — rejected (cheap to verify). Advisory can be promoted to required later |
| D29 | Keep CodeQL **default setup** as-is (`languages: [actions, python]`); close #135 as a self-resolved GitHub-side transient, make NO config change | 2026-07-16 | ACTIVE | E034 | Migrate to advanced-setup `codeql.yml` — rejected (adds a workflow to keep green on both OSes; doesn't prevent an infra transient); disable default setup — rejected (loses real security scanning, which passed on every commit incl. #134). The 2s `CodeQL` aggregate check failed only on #134's two commits, is non-required, and passed on #132/#133 before and #136–#141 after |
| D30 | bpmn2drawio `auto` layout resolves to `preserve` only on **complete** DI (`has_complete_di_coordinates` — every element positioned), not any-DI; partial-DI ⇒ graphviz | 2026-07-16 | ACTIVE | E036 | Hybrid partial-fallback (graphviz-layout only the DI-less elements) — rejected (fiddly, graphviz doesn't know the DI-fixed positions → new overlap risk); document-only — rejected (silent (0,0) stranding is a poor default). Guard restores exact pre-4.3.0 graphviz for partial-DI files while keeping the 4.3.0 preserve for fully-DI (Bizagi). Refines D-none; fixes #143 introduced by the 4.3.0 `auto` default (E035) |
| D31 | Personal marketplace does NOT accept third-party/vendor plugins — especially remote-MCP plugins with non-LLM egress (esp. write-capable). Decline #97 (xquik) | 2026-07-16 | ACTIVE | E037 | Accept-with-changes (schema loosen for `mcpServers` + SECURITY.md egress-policy update + strict validation + auth reconcile + `disable-model-invocation`) — rejected (establishes a vendor-plugin acceptance policy the owner doesn't want, contradicts the SECURITY.md "LLM-API egress only" model). Leave-open — rejected (no path to yes). Basis: this is the owner's own read-only/analysis tooling, not a registry; `schemas/plugin.json` forbids `mcpServers` (`additionalProperties:false`) so vendor-MCP plugins can't merge without an owned schema change anyway |
| D32 | Eval execution = deterministic **structural linter now** (extend `check_eval_mapping.py`: scenario/Must/Rubric structure + coverage gate + `command:` validation); **LLM-judge behavioral runner DEFERRED** to its own go/no-go (ADR-0009, Accepted) | 2026-07-17 | ACTIVE | E043 | Build the LLM-judge runner now — rejected (would be the repo's FIRST CI secret, can't run on fork PRs, flaky per non-deterministic grading, real cost; a CI-posture decision not an impl task). Hybrid re-author all 45 evals with machine-readable markers — rejected (largest diff, gate ends up ≈ structural linter). Close #150 as human-run-by-design — rejected (leaves the 10-surface coverage gap + dead cross-cutting `command:` field). Basis: `evals/README.md:87` says evals are human-run by design, so CI-executing them is an architecture change, not a bugfix |
| D33 | **Retire the mypy count-ratchet; use bare `mypy src/ --ignore-missing-imports` for all 3 tools** (delete both `.mypy-baseline` files). All tools are mypy-clean (D24), so the ratchet is scaffolding; converge on the simpler existing form (feedback-docx's). Behavior-identical (baseline-0 ratchet passes iff mypy=0). **Supersedes D24's ratchet mechanism** (D24's zero-goal stands) | 2026-07-17 | ACTIVE | E045 | Give feedback-docx a `.mypy-baseline=0` for symmetry — rejected (spreads the more-complex form to all 3; keeps an escape-hatch to raise the ceiling that contradicts hard-zero) |
| D34 | **task-sync skill design (approved, not yet built):** per-repo committed `tasks.json` reconciled bidirectionally with the repo's tracker (GitHub `gh` / Gitea `tea`); skill-as-interface (in-session tables + gitignored `TASKS.md`); 3-way sync, last-write-wins by `updated_at` with genuine conflicts surfaced; prune-on-close archiving (tracker = permanent archive); ONE list with per-finding confidentiality dispositions (keep/anonymize/redact/remove, remembered by content hash); milestone as the "project" grouping; IMPLEMENTATION_PLAN.md stays separate (backlog vs execution blueprint). Full design: `docs/plans/2026-07-18-task-sync-design.md` | 2026-07-18 | ACTIVE | E047 | Two-file private lane — rejected (user wants one list); standalone TUI app — rejected (YAGNI, in-session table suffices); flatten plans into tasks / drop markdown plans — rejected (loses the structure /implement-plan needs); bespoke `project` field — rejected (milestone round-trips to the tracker); bash+jq reconcile vs Python tool — deferred to plan time (lean Python for testability) |
| D35 | **task-sync adoption window = the existing `prune_closed_after_days`, applied ONLY to the `NEW_REMOTE`→pull branch in `resolve.py`.** Rationale was that the identical strict-`>` predicate as `_should_prune` makes adopt/prune consistent by construction, with zero new config surface | 2026-07-22 | **SUPERSEDED by D37** | E051 | Filter in `providers/*.list_issues` (the issue's own suggestion) — **rejected, actively dangerous**: `classify.py:141-151` treats the fetched list as authoritative, so a missing issue turns a `CHANGED_BOTH` conflict into a one-sided push (silent remote clobber) and can even reopen a closed issue via the pushed `state` field. Filter inside `classify()` — rejected, breaks its documented "each task and each issue appears exactly once" invariant (pinned by `test_classify.py:219-228`); classification is ground truth, adoption is policy. **Both rejections still stand and carry forward into D37** — only the window's *source* changed |
| D36 | **`scan-apply` is its own subcommand taking `{task_id: disposition}`, validating every id/disposition BEFORE mutating anything** | 2026-07-22 | ACTIVE | E051 | Extend the existing `sync --decisions` payload — rejected, `_load_decisions` returns flat `dict[str,str]` and its wrapper branch discards sibling keys. Fold into `sync --apply` — rejected, dispositions must land before `build_plan(classify(...))` or `creates`/`pushes` push pre-redaction text. Keep the inline heredoc — rejected, it's the ADR-0010 fragility class and it raises a bare `KeyError` mid-loop, silently discarding already-applied dispositions |
| D37 | **Adoption window is its OWN config key `adopt_closed_within_days` (default `0` = adopt OPEN issues only); adoption and prune answer different questions** — "is this issue actionable enough to track at all?" vs "how long do we keep completed work?". An absent key (every pre-11.3.0 `tasks.json`) resolves to `0`, never to the 30-day prune window. `--adopt-all` restores full-mirror adoption. **Supersedes D35** (whose placement rejections still hold) | 2026-07-22 | ACTIVE | E051 | D35's shared key — **built, then rejected on live measurement**: it left `pull: 25` unchanged because this repo's oldest closure is 6 days old, so "recently closed" == "all history"; it satisfied the letter of #167 but not its intent. Arbitrary small default such as 3 days — rejected: it only looked reasonable because it happened to fit this repo's current age distribution (`pull: 8`) and would drift as the repo aged. Basis for `0`: D34 already makes the tracker the permanent archive, so a closed issue you never tracked locally is not your backlog |
| D38 | **ADR-0003 (Bitwarden-only secrets) gains a sanctioned exception for standalone-tool local runtime:** visual-explainer's `_create_env_file` may write a plaintext API key to a local `.env`, mitigated by `chmod 0600` + an explicit plaintext-storage warning. ADR-0003 status stays Accepted | 2026-07-16 | ACTIVE | E018 | Route the standalone tool through `bws` — rejected (the tool must run without the Bitwarden CLI); leave the key world-readable — rejected (the SE finding) |
| D39 | **Three skills deliberately keep unscoped `Bash`, with an inline YAML justification, instead of being narrowed:** `security-analysis` (~9 native audit tools chosen by detected stack), `leak-risk-audit` (writes+runs ad-hoc Python scans), `arch-review` (9 domain subagents run semgrep/bandit/lizard/trivy). Injection risk is mitigated by E019's fetch/act separation instead | 2026-07-16 | ACTIVE | E019 | Enumerate their command union — rejected, the command set is genuinely dynamic and scoping would break them; leave all 24 files unscoped — rejected (23 were enumerable, so only 3 carve-outs were needed) |
| D40 | **The 4 fleet SSH/sudo skills (spark-recon, jetson-recon, spark-audit, jetson-audit) are `disable-model-invocation: true` — user-invoke-only** — plus a Trust Boundary section stating fetched content is data-only and never determines which commands run. Rationale: jetson-recon combined untrusted WebFetch/WebSearch with a live SSH read in one skill (the full lethal trifecta) | 2026-07-16 | ACTIVE | E019 | Scope their `Bash` and leave them model-triggerable — rejected: an injected page could still auto-trigger an SSH + passwordless-sudo skill; the fleet `claude` user's sudo set includes `rm`/`chmod`/`chown`/`mount`/`apt`/`reboot` |
| D41 | **`schemas/command.json` is deliberately NOT enforced by the Schema Validation job.** It declares `additionalProperties: false` without `argument-hint`/`effort`, so enforcing it as written would fail every command file. Enforcement requires fixing the schema first | 2026-07-16 | ACTIVE | E020 | Wire it in as-is — rejected (reddens CI repo-wide); delete the schema — rejected (it is the intended contract, merely incomplete) |
| D42 | **ADR-0004's per-plugin help-skill requirement is dropped** (2026-07-16 amendment), superseded by ADR-0006 skills-first + native `/help`; no plugin ever implemented it. `scripts/generate-help.py` deleted along with the `pre-commit` help.md-sync check and the CONTRIBUTING/TROUBLESHOOTING/PLUGIN-DEVELOPMENT references | 2026-07-16 | ACTIVE | E023 | Implement help skills to satisfy the ADR — rejected (duplicates a native, Anthropic-maintained command — same reasoning as D8) |
| D43 | **PERF-01 closed by REMOVING the inert `--concurrency` flag + `generate_batch()` + `asyncio.Semaphore`, not by wiring them** — an honest close with zero regression risk for a scoped phase | 2026-07-16 | **REVERSED (in E030)** | E024 | Wire parallel generation with a memory cap — deferred at the time as a genuine async rewrite; subsequently done in E030 (D27, 2.92× on 3 images) |
| D44 | **Narrowing `allowed-tools`, adding `disable-model-invocation`, or removing a CLI flag are user-facing capability changes ⇒ MAJOR SemVer bump** (this is why the arch-review hardening shipped as 11.0.0 rather than staying on 10.3.0) | 2026-07-16 | ACTIVE | E025 | Ship the hardening under the existing version — rejected: materially-changed skills under an unchanged version leave the cache indistinguishable from the old one to a reader |
| D45 | **Bump only the plugins with genuine unreleased changes; never issue an empty coordinated bump.** `/bump-version all minor` was course-corrected to personal-plugin-only (11.0.0→11.1.0) because bpmn-plugin had just shipped 4.3.1 and slide-gen had only test/hardening work | 2026-07-16 | ACTIVE | E038 | All-three-minor coordinated release — rejected by owner (2 empty bumps); + slide-gen patch — rejected (hardening alone isn't worth a version) |
| D46 | **A completed `IMPLEMENTATION_PLAN.md` is archived to `docs/archive/IMPLEMENTATION_PLAN-vN.md` (force-added past the `archive/` gitignore) before a new plan is written** — the v4–v10 precedent | 2026-07-17 | ACTIVE | E040 | Overwrite in place — rejected (loses the executed plan's acceptance criteria, which later entries cite); keep multiple live plan files — rejected (ambiguous which one `/implement-plan` runs) |
| D47 | **CONTRIBUTING.md is reframed skills-first:** the Quick Start teaches `/new-skill`; the "Adding a New Command" section is kept behind an explicit ADR-0006 frozen-legacy banner (still valid for the 23 existing commands) | 2026-07-17 | ACTIVE | E044 | Minimal 2-line patch — rejected, it left the Quick Start pointing new contributors at the deprecated `/new-command`; full command→skill doc rewrite — rejected as disproportionate |
| D48 | **Notebook rotation is codified as a `rotate` operation on the lab-notebook skill + CLAUDE.md Rule 12**, threshold ~40 entries or ~1200 lines, keeping the living sections + ~20 recent entries; full procedure in `skills/lab-notebook/references/rotation.md` with three load-bearing invariants (promote body-only decisions first, cut at a session marker, `git add -f`) | 2026-07-17 | ACTIVE | E046 | Leave rotation a from-scratch judgment call — rejected, #154 would recur in ~40 entries; put the whole procedure in SKILL.md — rejected (blows the <500-line body budget) |
| D49 | **ADR-0010 — task-sync is a bundled Python tool (not bash+jq) driven by a NON-interactive plan→decide→apply protocol:** `sync --plan --json` emits pushes/pulls/conflicts/confidentiality findings, the SKILL renders + prompts, `sync --apply --decisions <file>` executes. The tool owns deterministic logic, the skill owns all interaction. **Resolves the fork D34 deferred to plan time.** Both providers read via REST behind one normalized adapter (`tea` CLI JSON omits `updated_at`/`body`, which would break last-write-wins) | 2026-07-18 | ACTIVE | E048 | bash+jq in the skill — rejected: untestable, Windows-fragile, and a sync bug silently corrupts task lists; interactive tool — rejected, it must stay scriptable and CI-exercisable |
| D50 | **Gitea credential resolution order is fixed in one place (`_build_provider`):** base_url = `$GITEA_URL` → `config['gitea_url']` → tea config; token = `$GITEA_TOKEN` → tea config. Env always wins; a missing/unreadable tea config degrades to a `ValueError` naming the remedy, never a crash. `init` persists `config.gitea_url` from an http(s) origin remote | 2026-07-18 | ACTIVE | E050 | Env-only (the pre-11.2.1 behavior) — rejected, a valid `tea login` still 401'd; tea-config-only — rejected, it offers no override path and breaks on ssh remotes where scheme/port aren't derivable |
| D51 | **Audit/report findings are filed as ~18 coherent-bundle issues, one per work unit — not one per finding** (250+ singletons would be unusable) — using the `[Pn]` title prefix; an existing issue that already covers a finding gets an extending comment, never a duplicate issue | 2026-07-28 | ACTIVE | E053 | One issue per finding — rejected (unusable tracker); one mega-issue per report section — rejected (not independently closable) |

Status values: ACTIVE · SUPERSEDED (by D#) · REVERSED (in E#)

## Action Items

Track follow-ups that emerge from experiments. Move to Completed when done.

### Open

| # | Action | Created | Source Entry |
|---|--------|---------|-------------|
| — | **No open action items** — the canonical backlog is the GitHub issues list (A2/A12 directive), summarized in Current Baseline above. **#208 and #212 were fixed and shipped this session** (11.4.0 / 11.4.1, E056/E057); **#210** (plugin CHANGELOG missing 11.2.0/11.3.0) is the only new open item. Landing order for the E052 audit set is unchanged: #189 (P0) → #190/#196/#197 (quick P1s) → #191/#192 with #183 (they share fix lines) → #193/#194/#195 → #198–#206. Two constraints carry forward from E053: #201 must land before #205's `description-triggers` re-run or the causes conflate, and #197/#204 are an instance-fix + class-close pair (negative-test the guard before wiring it). **Traps:** `gh issue view <n>` silently resolves PR numbers — derive issue ranges from `gh issue list`; and the installed plugin's *active* version lags the cache until a fresh session (11.4.1 is downloaded, `claude plugin list` still reports 11.3.0). | — | E043 |

### Completed

| # | Action | Created | Completed | Source Entry |
|---|--------|---------|-----------|-------------|
| C1–C17 | Pre-2026-07-16 follow-ups: v8.0.0 modernization, research-orchestrator removal, plan-template refinements, gap-analysis execution, validate-plugin update, the cache-sync corrections later superseded by D19, the 9.0.0/10.0.0/10.3.0 releases, R1–R13 execution, lockfile CVE regeneration, `dependabot.yml`, and clear-prep. All closed — full narrative in [`docs/archive/LAB_NOTEBOOK-E001-E016.md`](docs/archive/LAB_NOTEBOOK-E001-E016.md). | 2026-04-21 → 07-16 | 2026-07-16 | E001–E016 |
| C18 | Author `clear-prep` skill (context-clear handoff) + refresh 4-version-stale Current Baseline (prime finding); `claude plugin validate --strict` passed | 2026-07-16 | 2026-07-16 | E015 |
| C19 | Ship personal-plugin 10.3.0 (clear-prep) via PR #108 — squash-merged `df33eef`, all 25 checks green both OSes, cache updated 10.2.0→10.3.0; folded a one-line setuptools-CVE (PYSEC-2026-3447) CI hygiene fix to unblock the audit gate | 2026-07-16 | 2026-07-16 | E016 |
| C20 | Execute the 8-phase arch-review remediation (IMPLEMENTATION_PLAN v9, 32 items) via /implement-plan — one branch+PR+merge per phase (PRs #109/#110/#111/#112/#118/#119/#120/#121), all 18 checks green each after 2 Windows fix rounds; merges `8a2988a→039c2cc→c093904→7fe821d→99d0610→9cf8963→e3bf0a4→0e0895c`. Deferred: SE-11, PLAT-012, PERF-01-wiring + plan scope-outs | 2026-07-16 | 2026-07-16 | E017–E024 |
| C21 | **Dependabot triage (A1)** — 5 merged (#104 google-genai 2.11 MAJOR verified-safe, #113/#114/#115 SHA-pinned action bumps, #116 bpmn2drawio group), 1 closed with root-cause (#117 broken pydantic/pydantic-core lockfile). main `37868fb→6bf2d84`, all tool lockfiles CVE-clean. Course-corrected A1's plan (see D25) | 2026-07-16 | 2026-07-16 | E026 |
| C22 | **A2 CLOSED — its tracked issues #125–#131 are all closed** (burndown complete, E026–E033); the row had gone stale on the dashboard while still listed Open. Its standing directive ("all tasks/work are managed from the GitHub issues list") is now carried by A12 | 2026-07-16 | 2026-07-17 | E039 |
| C23 | **Prime findings synced → canonical GitHub backlog (#149–#154)** — 6 issues filed against existing labels using the `[Pn]` convention; tracker went 0 → 6 open, 0 duplicates of closed work. Verification corrections applied *before* filing: repo-level secret scanning + push protection already `enabled` (top risk-agent finding NOT filed — it was wrong); mypy ratchet logic sound, only its comments stale (filed as docs). Gitea's 17 open issues are `davistroy/homeserver` (fleet, incl. 2 P0 rotations) — deliberately out of scope here | 2026-07-17 | 2026-07-17 | E039 |
| C24 | **A12 CLOSED — executed the #149–#154 plan via `/implement-plan`** (7 phases/16 items, one commit per phase, PR #159 squash-merged `e594158`, all 20 checks green). #149–#154 closed on GitHub; #155/#156 filed for scoped-out work; ADR-0009 added; notebook rotated (E001–E016 archived). Follow-up CONTRIBUTING skills-first cleanup shipped separately (PR #160 `e2f33e5`, E044). Root cause confirmed: 5 of 6 issues were "guards that never gated" | 2026-07-17 | 2026-07-17 | E042–E044 |

---

## Prior Work Summary

Active since January 2025. Three plugins share a root `.claude-plugin/marketplace.json`. The structural rules were discovered by trial and error and are now enforced (CLAUDE.md "Verified Operational Rules", ADR-0001/0006): nested `skills/name/SKILL.md`; `name` **required** in skill frontmatter and **forbidden** in command frontmatter; no `tools`/`hooks` keys in plugin.json; record-format `hooks.json`. Plugin discovery fails **silently** — each of those rules cost a debugging session.

Pre-notebook milestones (v3.x–v8.0.0, Jan–Apr 2026): research-topic, visual-explainer, ship, implement-plan (v3); prime, review-intent, parallel execution (v4); shared plan template + allowed-tools sweep (v5); lab-notebook, spark-recon, ultra-plan, arch-review, hooks (v6); **v8.0.0** modernization — `context:fork`, `isolation:worktree`, `paths:`, dynamic `!cmd`, audit/recon consolidation (~50% LOC), research-orchestrator Python tool removed (D5). Full narrative: [`docs/archive/LAB_NOTEBOOK-E001-E016.md`](docs/archive/LAB_NOTEBOOK-E001-E016.md).

Planning pipeline: `/ultra-plan` → `/create-plan` / `/plan-improvements` → `/implement-plan`, all sharing `references/plan-template.md`. Completed plans are archived as `docs/archive/IMPLEMENTATION_PLAN-vN.md` (v4–v10) before a new one is written (D46).

## Current Baseline

*Verified 2026-07-29 against `origin/main` @ `84e031a`.*

| Item | State |
|---|---|
| Versions | marketplace **3.3.0** · personal-plugin **11.4.1** (E057) · bpmn-plugin **4.3.1** (E036) · slide-gen **1.2.0** |
| Surfaces | 23 commands · 40 skills (personal 29 / slide-gen 9 / bpmn 2) · 3 implementer agents in `.claude/agents/` · 10 arch-review agents in `plugins/personal-plugin/agents/` |
| Bundled tools | visual-explainer 894 tests / 93% · bpmn2drawio 640 / 92.84% · feedback-docx 69 / 96.95% · **task-sync 427 / 96.33%**. All bare-`mypy` clean (D33) and ruff clean; green on 3.10/3.11/3.12 |
| Evals | **48** `.eval.md` specs; structural + coverage linter in CI (`check_eval_mapping.py`, ADR-0009/D32); LLM-judge runner deliberately deferred |
| CI | `test.yml` (pytest ×2 OS, coverage floors in each tool's `[tool.coverage.report]`, pip-audit per lockfile, advisory `Python Compat (3.10)/(3.12)`) · `validate.yml` (plugin/frontmatter/version-sync, README-sync `--check`, eval linter, ruff, markdownlint). **Branch protection on `main`: 21 required checks, PR-required 0-approvals, `enforce_admins=false`** (ADR-0007/D22) |
| Plugin cache | Auto-propagates from the GitHub marketplace source. **There is no `autoUpdate` key in marketplace.json** — that is Claude Code's install-side default, not a repo-declared flag (D19 correction). Refresh with `claude plugin marketplace update`; `claude plugin update <plugin>` can report "Plugin not found" (E051) |
| Dependencies | Actions SHA-pinned (checkout/setup-python/setup-node) · google-genai 2.11.0 · pydantic 2.13.4 / pydantic-core 2.46.4 **lockstep — never bump independently** (D25) |
| Open backlog | **#189–#206** (18 E052-audit issues, #189 the only P0) · **#210** (plugin CHANGELOG missing 11.2.0/11.3.0) · **#183** (20 unguarded `` !`git` `` injections across 5 skills) · #181/#182 (task-sync) · #169/#170/#171 (v2 scope-outs, deliberately deferred). **#189 is the only P0.** |
| Platform | Linux VM (current sessions); earlier sessions Windows 11 — see root CLAUDE.md "Dual environment" |

---

## Experiment Log

> **Earlier entries archived:** E001–E016 (2026-04-30 → 2026-07-16) in [`docs/archive/LAB_NOTEBOOK-E001-E016.md`](docs/archive/LAB_NOTEBOOK-E001-E016.md); E017–E050 (2026-07-16 → 2026-07-18) in [`docs/archive/LAB_NOTEBOOK-E017-E050.md`](docs/archive/LAB_NOTEBOOK-E017-E050.md). Every decision they established is in the Decision Log above (D1–D51). The digest below summarizes E017–E050; full entries resume at E051.

### Archived Entry Digest (E017–E050)

Full entries live in [`docs/archive/LAB_NOTEBOOK-E017-E050.md`](docs/archive/LAB_NOTEBOOK-E017-E050.md). Every decision they established is in the Decision Log above (D1–D51). These headings deliberately avoid the `### Entry NNN` form so the live/archive overlap check in `rotation.md` stays meaningful.

| E | Date | What shipped | Durable takeaway / where it lives now |
|---|---|---|---|
| E017 | 07-16 | Arch-review Phase 1: branch protection on `main` (14 required checks then, 21 now; PR-required 0-approvals; `enforce_admins=false`); `docs/RUNBOOK.md`; CODEOWNERS; the D19 `autoUpdate` correction | ADR-0007 / **D22**. Governance-first ordering paid off — protection gated every later phase |
| E018 | 07-16 | Phase 2 security: XXE-hardened lxml parser + `lxml>=5,<7`; SSRF guard in `concept_analyzer` (blocks 169.254.169.254, re-validates each redirect hop); `.env` chmod 600; typed Gemini backoff; atomic checkpoint writes | **D38**. Windows CI caught a module-level `/etc/hostname` read in the XXE test — OS-specific paths need `tmp_path` + `Path.as_uri()` |
| E019 | 07-16 | Phase 3: `Bash` union-scoped across 23 files; 4 fleet SSH/sudo skills made user-invoke-only with Trust Boundary sections; RI-03 answered (yes, they SSH with passwordless sudo) | **D39**, **D40**; SECURITY.md "Fleet recon/audit trust boundary" |
| E020 | 07-16 | Phase 4: per-tool `tests/` linted (28 ruff errors); mypy count-ratchet (later retired, D33); schema-*data* validation; Actions SHA-pinned; pip-audit scoped per lockfile | **D41**. Windows runners default `run:` to **PowerShell** — any multi-line CI step needs `shell: bash` |
| E021 | 07-16 | Phase 5: `--connect-timeout`/`--max-time` on every curl; submit-status fast-fail before any poll loop; 429 `Retry-After`; Gemini key moved from `?key=` to the `x-goog-api-key` header | `references/research-provider-protocols.md` |
| E022 | 07-16 | Phase 6: slide-gen declared external-dependency (engine repo is PRIVATE ⇒ owner-only) + fail-fast `sg --version` preflight; homepage fixed; CHANGELOGs for all 3 plugins | ADR-0008 / **D23** |
| E023 | 07-16 | Phase 7: SECURITY.md egress + supply-chain sections; ADR-0004 help-skill requirement dropped + dead `generate-help.py` removed; cruft deleted; 14 skills gained Error Handling | **D42** |
| E024 | 07-16 | Phase 8: inert `--concurrency` removed; contradictory test skips fixed (64 skipped → run); `check_eval_mapping.py` created; `pytest -n auto`. Closed the 32/32-item remediation | **D43 — REVERSED in E030/D27.** Required checks are keyed by JOB NAME: preserve them byte-for-byte on every workflow edit |
| E025 | 07-16 | personal-plugin **11.0.0** — the hardening as a real release | **D44** |
| E026 | 07-16 | Dependabot triage: #104/#113/#114/#115/#116 merged, #117 closed | **D25**. #117 was not a CVE — a grouped bump split the lockstep `pydantic`/`pydantic-core` pair → `ResolutionImpossible`. A red pip-audit can mean "won't install", not "vulnerable" |
| E027 | 07-16 | visual-explainer `cli.py` **1,814 → 299** lines across 6 modules, zero behavior change, 626 tests green | **D26**. Cross-module patchable symbols must be referenced module-qualified so one `mock.patch` intercepts everywhere |
| E028 | 07-16 | Coverage **69 → 93%**, floor gate **65 → 85** (+257 tests from 6 parallel writers) | Windows caught 2 defects: `ctypes.windll` **exists** on real Windows — fully mock the platform probe rather than relying on its absence |
| E029 | 07-16 | Eval corpus **35 → 45**; slide-gen went from zero to 6-skill coverage | — |
| E030 | 07-16 | Parallel image generation re-wired: `Semaphore`-bounded `gather`, default 3, **2.92× on 3 images**; `--concurrency 1` restores exact serial behavior | **D27**; reverses D43. Also: a GitHub Actions dispatch glitch needed an **empty commit** to re-dispatch — close+reopen did not work |
| E031 | 07-16 | mypy `.mypy-baseline` **101 → 0** and **57 → 0**; all 3 tools clean | **D24** goal achieved (mechanism later retired by D33). Surfaced 2 real pydantic alias bugs |
| E032 | 07-16 | 3 oversized command bodies → `references/*-examples.md` (675/573/530 → 480/462/385) | The <500-line body budget is a house rule, not a CI gate |
| E033 | 07-16 | Python 3.10/3.12 added as a NON-required advisory `python-compat` job | **D28**. Expanding a *required* job's matrix renames its check context and deadlocks every merge |

#### E034 (07-16) — #135 CodeQL "2s failure" [ci] [debug]

The ~2s check literally named `CodeQL` is a GitHub-managed **status rollup** posted only on `pull_request` events — distinct from the real `Analyze (python)` / `Analyze (actions)` scans, which never failed. The failure was isolated to PR #134's two commits (every PR before and after passed) and self-resolved; config had last been touched 6h earlier. Closed with **no config change** (**D29**). Ground-truth via `gh api commits/<sha>/check-runs`, not `gh run list` — the latter conflates the workflow run with the posted check.

#### E035 (07-16) — Integrate external PR #98 → bpmn-plugin 4.3.0 [build]

DI-layout preservation from an outside contributor, landed on a base 3 sessions newer. `git merge-tree` up front showed GitHub's "CONFLICTING" was pessimistic — only 2 test files truly conflicted. Cherry-picked onto a fresh integration branch to preserve per-commit authorship; the anticipated mypy risk never materialized (lenient config), and the real gate friction was `ruff format`/E501 on pre-gate code. Method captured in memory `external-pr-integration.md`.

#### E036 (07-16) — #143 partial-DI guard → bpmn-plugin 4.3.1 [debug]

`has_di_coordinates` was all-or-nothing, so 4.3.0's new `auto` default sent *partially*-DI files to `preserve` and stranded the DI-less shapes at (0,0). Fixed with `has_complete_di_coordinates`; partial-DI now falls back to graphviz, restoring exact pre-4.3.0 behavior for that case (**D30**).

#### E037 (07-16) — #97 xquik vendor-MCP plugin DECLINED [decision]

Not a quality judgment — a curation call (**D31**). It added a **write-capable** third-party egress destination contradicting SECURITY.md §1/§2, and could not have merged anyway: `schemas/plugin.json` is `additionalProperties: false` and forbids `mcpServers`.

#### E038 (07-16) — personal-plugin 11.1.0 [build]

`/bump-version all minor` course-corrected to personal-plugin-only — bpmn had just shipped 4.3.1 and slide-gen had no features (**D45**).

#### E039 (07-17) — Prime findings → GitHub issues #149–#154 [decision]

The tracker being *empty* was itself the defect, invisible because every conventional health signal was green — the same class as D17/D19: **absence of a signal is not evidence of health.** Two of three agent findings needed correction before they were fit to file (the "no secret scanning" finding was simply wrong — `gh api` showed it enabled). **Treat subagent output as a lead, not a conclusion.** Established the `[Pn]` title convention.

#### E040 (07-17) — /ultra-plan the prime backlog [plan]

Investigation **overturned 4 of 6 issues as filed**, including two of my own dependency claims: `update-readme.py` was *structurally dead* (nested-skill glob + stale anchor), not prose-blind, so wiring `--check` before repairing it would have shipped a green no-op; #151 didn't depend on #149 and had *three* contradicting voices, not two; #153 was a byproduct of the repair, not a typo; #150 overturned a documented design (`evals/README.md:87`). **Found the D14–D18 blocker** — five decisions living only in E005/E006 bodies while an Accepted ADR cited one — which is why rotation.md Step 0 exists. Produced ADR-0009 (**D32**) and **D46**. Lesson: the plan phase is where symptom-issues get their true root-cause structure — don't over-trust the issue text, even your own.

#### E041 (07-17) — Flaky wall-clock concurrency test [debug]

The concurrent run was measured *first* and paid a one-time cold-start cost the serial run didn't; under xdist an early-scheduled worker collapsed the signal. A subtraction threshold also failed cold. Fixed by instrumenting the actual property (max in-flight coroutines, deterministic under asyncio's single-threaded loop). **Test the property, not a timing proxy for it; reproduce flakes locally in isolation, not by re-running CI.** Full write-up: `LEARNINGS.md`.

#### E042 (07-17) — Promote D14–D18 into the Decision Log [cleanup]

Table-only insertion restoring a gapless D1–D31; unblocked the E001–E016 rotation. Direct precedent for this entry's own D38–D51 promotion.

#### E043 (07-17) — Execute prime-backlog Phases 2–6 (the doctrine entry) [ci] [decision]

Five of six issues collapsed to one root cause: **verification artifacts that existed but never gated.** `update-readme.py --check` exited 0 for any drift; the eval check validated mapping only; the pre-commit hook was uninstalled with a dead `help.md` check inside; `validate.yml`'s skills-frontmatter branch was dead code (non-recursive glob). Every new gate this run was **negative-tested against deliberately-bad input before being wired in**. Ordering is load-bearing: repair-before-wire, promote-before-rotate, remove-dead-check-before-install. Also rotated E001–E016 (1511 → 822 lines). **A verification artifact that cannot fail is worse than none — it converts "unchecked" into a false "checked."** Now a CLAUDE.md Verified Operational Rule.

#### E044 (07-17) — CONTRIBUTING.md skills-first cleanup [docs]

The Quick Start was leading contributors to the deprecated `/new-command` and referencing a help skill that exists nowhere (**D47**).

#### E045 (07-17) — Retire the mypy ratchet (#155) [ci]

Both `.mypy-baseline` files deleted; all 3 tools moved to bare `mypy src/ --ignore-missing-imports`. Behavior-identical at baseline 0, and it removes an escape hatch that contradicted the hard-zero stance (**D33**).

#### E046 (07-17) — Add `rotate` to the lab-notebook skill (#156) [skill]

Encoded *after* doing the rotation manually, so `references/rotation.md` transcribes what actually worked — including the two gotchas that only surfaced by doing it (body-only decisions; the globally-gitignored archive dir). **Codify-after-doing beats codify-from-imagination** (**D48**).

#### E047 (07-18) — Design task-sync [decision]

One committed `tasks.json`; 3-way sync against a committed base with genuine two-sided conflicts surfaced, never clobbered; tracker = permanent archive; ONE list with per-finding confidentiality dispositions remembered by content hash; `milestone` as grouping (**D34**). Two reframes the user hadn't stated but agreed with: the "mirror" is actually bidirectional (dependabot / web-filed issues), and format choice doesn't buy sort/filter — the interface does. Full design: `docs/plans/2026-07-18-task-sync-design.md`.

#### E048 (07-18) — /ultra-plan task-sync [plan]

Two investigation corrections shaped the build: the confidentiality "reuse" from `leak-risk-audit`/`remove-ip` **did not exist** (both are prompt-only, no callable code), and Gitea must be read via REST because `tea` CLI JSON omits `updated_at`/`body` (**D49** / ADR-0010). Guardrail recorded: another project's hardcoded client brand terms must never be copied into this public repo — sensitive terms are per-repo config.

#### E049 (07-18) — Build task-sync → personal-plugin 11.2.0 [build]

6 phases / 18 items; final suite 335 tests / 95.89%. Independent verification caught a real integration gap: the confidentiality scanner was built and unit-tested but **never wired into `sync --plan`**, so findings were always empty and the skill worked around it with inline `python3` heredocs. **"Built + unit-tested" is not "integrated" — a verify pass that only re-runs unit tests would have missed it.** The plan/apply split is what made the whole thing testable.

#### E050 (07-18) — Fix the task-sync Gitea path → 11.2.1 [debug]

Two issues — #173 (`init` never persisted `config.gitea_url`) and #174 (`_build_provider` read only `$GITEA_TOKEN`, so a valid `tea login` still 401'd) — were genuinely coupled: fixing either alone still fails for one class of repo. Designing the resolution order once, in one place, makes both disappear (**D50**). Real-`git`-repo test fixtures (`git init` + `git remote add` in `tmp_path`) proved less brittle than mocking `subprocess.run`.

--- New session: 2026-07-22 — close out the remaining task-sync polish backlog (#167 adoption window, #168 disposition-apply CLI) as one 11.3.0 release. User chose both-together, no formal plan doc (the /ultra-plan Phase 3 design is the spec), one branch/one PR. ---

### Entry 051 — task-sync adoption window + `scan-apply` subcommand (#167/#168) [skill] [decision] [build]
**Date:** 2026-07-22
**Environment:** Linux VM, branch `fix/task-sync-167-168` off main `71cca6a` (clean, 0/0 vs `origin/main`). personal-plugin 11.2.1 → 11.3.0, marketplace 3.3.0. Investigation via 2 parallel Explore subagents; `/ultra-plan` Phases 0–4 run, Phase 5 (formal plan doc) deliberately skipped by user choice.
**Status:** COMPLETE — shipped as personal-plugin 11.3.0 (PR #184, main `1d5eacd`)

**Objective:** Ship the last two task-sync backlog items as personal-plugin 11.3.0 — (#167) stop adopting long-closed issues on sync, and (#168) make confidentiality disposition-apply a first-class CLI subcommand instead of an inline heredoc in the skill.

**Investigation corrections that changed the design (both issues' own "Where:" guidance was wrong):**

1. **#167 is NOT a first-sync problem, and NOT a provider-layer fix.**
   - *Not first-sync:* adoption happens at `reconcile/apply.py:207`, prune at `:209-211` — the **same `apply()` call**. A task adopted from a >30-day-closed issue is created and destroyed within one apply; no local task ends up referencing the issue, so the next `sync --plan` re-classifies it `NEW_REMOTE` again. **`pull: 17` recurs on every sync, forever** — the prune rule never quiets the plan output, contrary to the issue text.
   - *Not the provider layer:* the issue proposed filtering in `providers/*.list_issues`. `classify.py:141-151` documents "the fetched issue list is assumed authoritative" and falls back to local-side-only when a linked issue is absent. Subagent demonstrated against real code that filtering at fetch turns a genuine `CHANGED_BOTH` **conflict into a one-sided push** (`pushes [('t-1', 5, 'open')]`, conflicts 0) — a silent remote clobber, violating the tool's core never-auto-clobber invariant (ADR-0010). Worse, that push carries `state="open"` (`mapping.py:93` → `apply.py:88` → `github.py:181-185` `gh issue reopen`), so a noise-reduction filter could **reopen a long-closed issue**. Rejected.
   - *Not in `classify()` either:* its docstring pins "each task and each issue appears exactly once" (`classify.py:126-129`), enforced by `test_classify.py:219-228`. Classification is ground truth; whether to *adopt* is policy.
   - **Chosen:** guard the `NEW_REMOTE`→`PullAction` branch in `resolve.py:140-150` **only**, leaving `CHANGED_REMOTE` (`:152+`) untouched — so unadopted old issues are skipped while already-tracked tasks keep full remote fidelity.

2. **#168's decisions cannot ride the existing `--decisions` file.** `_load_decisions` (`__main__.py:97-111`) returns a flat `dict[str,str]`, and its wrapper branch (`data = data["decisions"]`) **discards sibling keys** — a co-located `"confidentiality"` key would be silently thrown away. Separately, folding apply into `sync --apply` is wrong: dispositions must land *before* `build_plan(classify(...))` (`__main__.py:196`), because `creates`/`pushes` snapshot field text at classify time — a fold-in would push **pre-redaction** content. Hence a distinct `scan-apply` subcommand.

**Key design decisions:**
- **D35/D37 — adoption window is its own key `adopt_closed_within_days`, default `0` (open issues only).** *This decision was revised mid-entry by live measurement — see "Course correction" below.* The window gates `NEW_REMOTE` only; `CHANGED_REMOTE` is untouched so an adopted task keeps full remote fidelity forever. An absent key (every pre-11.3.0 `tasks.json`; `init` is a no-op on an existing file, `commands.py:112-115`) resolves to `0`, not to the 30-day prune window.
- **D36 — `scan-apply` validates all dispositions before mutating anything.** The current heredoc raises a bare `KeyError` on an unknown task id mid-loop and silently discards dispositions already applied (its single save is after the loop). The subcommand collects every unknown id / invalid disposition and reports them in one error → exit 1, nothing written.
- Determinism: `resolve`/`build_plan` gain an injectable `now` seam; the plan path currently has no wall-clock and must not acquire a hidden one (`plan.py:1-8` purity property, `test_dry_run_writes_nothing`).
- No `--json` on `scan-apply`: `sync --apply` deliberately ignores `--json` and there is no JSON-on-mutation convention in this CLI; not inventing one.
- ADR-0010 line 56 ("`sync` remains the only subcommand that goes through plan→decide→apply; every other subcommand mutates directly and immediately") still holds — `scan-apply` mutates directly from an already-made decision. No ADR amendment.

**Hypothesis:** Both change sets are additive and default-guarded, so all ~14 existing `classify`/`build_plan` test call sites and `test_provider_github.py:103` (which asserts `--state all` in argv — the fetch is deliberately unchanged) stay green. After the fix, a `sync --plan` in this repo drops from `pull: 17` to `pull: 0`. New subcommand auto-enrols in the `SUBCOMMANDS` help-smoke tests. Coverage holds ≥90 (currently ~96). Ships as personal-plugin **11.3.0** (minor: new subcommand + changed default adoption behavior), one PR, closing #167 and #168.

**Rollback Plan:** Both changes are additive and behind defaults; no schema change, no config migration, no data touched (user's local `tasks.json` is gitignored and untouched). `git revert` the squash commit, or delete the branch pre-merge. Version bump reverts with it.

**Scoped in (fold-ins found while verifying):**
- `test.yml:154-159` still comments the task-sync CI job "NON-required … withheld from branch protection until Phase 6"; branch protection **does** require `Task Sync Tests (ubuntu-latest)`/`(windows-latest)` (verified via API). Stale comment.
- `sync-semantics.md:23-24` + `resolve.py:12-14` claim a vanished-issue `CHANGED_LOCAL` is re-created; the reachable path **pushes** (the `issue_number is None` branch is unreachable from `classify`, which returns `NEW_LOCAL` in that case). Doc/docstring truth fix.
- `config-reference.md:59-67` says `tasks.json` "is meant to be committed"; this repo gitignores it (`3c47f68`). Truth fix.

**Scoped out (filed as new issues, not fixed here):** **#181** — no orphan/"issue deleted" handling despite the design doc specifying "flag and ask; never silent" (`2026-07-18-task-sync-design.md:128`), plus the unreachable re-create branch in `resolve.py`'s `CHANGED_LOCAL` arm; **#182** — GitHub `list_issues` `--limit 1000` unpaginated silent truncation (`github.py:106-107`), which is dangerous specifically because `classify` treats the fetched list as authoritative. Both are features/latent hazards, not #167/#168.

**Course correction — the first #167 design was built, measured against the live tracker, and rejected.**

The reuse-the-prune-window design (original D35) was fully implemented and green (357 tests, 96.02%) before it was verified end-to-end. The live check killed it:

| Adoption policy | First-sync `pull:` in this repo |
|---|---|
| open only (`window=0`) | **5** |
| open + closed ≤1d | 5 |
| open + closed ≤3d | 8 |
| open + closed ≤7d | 25 |
| open + closed ≤30d (the built design) | **25** |
| adopt-all (pre-11.3.0 behavior) | 25 |

Measured issue ages: 5 open (#167–#171), 20 closed — **all 3–6 days old, and zero closed more than 30 days ago.** So a 30-day adoption window excluded nothing: `sync --plan` and `sync --plan --adopt-all` printed *identical* output. The design satisfied the letter of #167 ("adopt open + recently-closed, not all history") while, in a young repo, "recently closed" == "all history".

**Root cause of the misdesign:** I derived the window from an internal consistency argument (adopt/prune can't flap if they share a predicate) instead of from the data the issue was actually reported against. The consistency property was real but irrelevant — it optimized a boundary that no issue in the repo was anywhere near. The user chose open-only-with-a-tunable-key; the `0` default is justified by D34's existing "tracker = permanent archive" principle: a closed issue you never tracked locally was never your backlog.

**System insight:** the adopt→prune recurrence bug and the first-sync-flood complaint looked like one problem and are two. The recurrence (adopt at `apply.py:207`, prune at `:209-211`, re-propose forever) only bites issues closed *past* the prune window; the flood bites issues closed *within* it. A single shared threshold can fix at most one of them at a time. Separate keys fix both — which is why the "one key, two uses" elegance was actively wrong rather than merely unnecessary.

**What worked:** dispatching the two Explore investigators before any design paid for itself twice — each issue's own "Where:" guidance pointed at the wrong layer, and the subagent *demonstrated against real code* that the provider-layer filter turns a `CHANGED_BOTH` conflict into a one-sided push (`pushes [('t-1', 5, 'open')]`, conflicts 0). Backing up `tasks.json` before touching it was cheap insurance for a file that is gitignored and therefore **not** git-recoverable. And running the tool against the live tracker — not just the test suite — is what caught the misdesign; 357 green tests had nothing to say about it.

**Verification (live, this branch):**
- First sync simulated from a pre-existing `tasks.json` with the key absent (the migration case): `pull: 25 → 5`; `--adopt-all` restores 25. Live `tasks.json` md5 unchanged (`7ae236e3…`) across every run — `--plan` wrote nothing, as designed.
- `scan-apply` end-to-end: a task body containing a `ghp_…` token and an email redacted to `[REDACTED]`, `task.confidentiality` stamped `{decision, reviewed_hash, at}`; `init` writes the new `adopt_closed_within_days: 0` key.
- Validate-before-mutate guard: a mixed batch (one valid id + one unknown id + one invalid disposition) exits 1 with `unknown task id(s): t-alsobad, t-nosuch; invalid disposition(s): t-alsobad='bogus' (must be one of ('keep', 'redact', 'remove', 'anonymize'))`, leaves `tasks.json` byte-unchanged, and does **not** partially apply the valid entry.
- Suite: **386 tests, 96.26% coverage** (floor 90), `ruff check` + `format --check` clean, `mypy src` clean (23 files).

**Adversarial review remediation (opus reviewer, mutation-tested — 5 SHOULD-FIX, 0 blockers).** The reviewer did not just read the diff; it introduced 10 deliberate defects and checked whether the suite caught them. That method found things reading could not:

| # | Finding | Why it mattered |
|---|---|---|
| F1 | **The invalid-disposition guard could not fail.** Deleting the entire up-front `invalid` check left all 386 tests green | `apply_review` independently raises on a bad disposition *mid-loop* — after mutating earlier tasks in memory. The existing test used one task and asserted only file bytes, so it could not distinguish up-front from mid-loop validation. Literally the E043 lesson recurring inside the fix for a different bug |
| F3 | **`scan-apply` never stamped `updated_at`**, so `_recommend`'s last-write-wins saw a stale local timestamp and recommended `remote` for a task redacted seconds earlier | Accepting that recommendation **restores the un-redacted secret from the tracker**. A data-leak path in the one command whose whole job is preventing leaks |
| F4 | **Adopt predicate keyed off nullable `closed_at`, not authoritative `state`** | `Issue.state` is validated non-null; `closed_at` is populated via `.get()` in both adapters. A `state="closed"` issue with no `closed_at` — or a future one (clock skew) — was still adopted, reintroducing #167. Now fail-closed: adopt only when the age is *provably* inside the window |
| F5 | **Skipped adoptions were silent and the plan printed "already in sync — nothing to do"** while 20 issues sat unadopted | My own new tests asserted that misleading output, pinning the lie. Fixed by adding `skipped_adopts` (issue numbers, not a count — the numbers are what make it actionable) to the plan, a summary line, and `is_empty()` |
| F2 | Missing `--decisions` file raised a raw `FileNotFoundError` traceback | `--decisions` is `required=True` on `scan-apply`, so a stale `/tmp` path is the likeliest user error. Fixed in `_load_decisions` (the only place that knows the path) so every failure normalizes to a `ValueError` naming the file — one fix covering both `scan-apply` and the pre-existing `sync --apply` hole |

Also fixed: F6 (a comment citing #168 for the #167 bug), F7 (the combined-error path was untested — `raise ValueError(problems[0])` left 386 green), F8 (`_adopt_window` → public `adopt_window`), F9 (**`scan-apply` was not idempotent** — `apply_review` stamps `at: now()` unconditionally, so a repeat run rewrote `tasks.json` and dirtied git; now skipped when the recorded decision matches *and* content is unchanged), F11 (`sync --apply --adopt-all` documented but untested).

**F3/F9 interaction, resolved deliberately:** stamping `updated_at` (F3) could have defeated the idempotence skip (F9). It does not, for two independent reasons: `content_hash` hashes only `title/body/status/priority/labels/milestone` — `updated_at` is excluded by design — so the stamp never perturbs `reviewed_hash`; and the skip is evaluated *before* both `apply_review` and the stamp, so a skipped pair gets neither. Verified: a no-op re-run leaves `tasks.json` byte-identical.

**System insight — coverage is not verification.** This change set sat at 96.26% coverage with every gate green while containing a guard that could be deleted without a single test failing, plus a leak path (F3) and a silent-truncation lie (F5). Two of the three were introduced *by the fix itself*, and one was pinned in place by my own new tests. High coverage measures which lines ran, not whether any assertion would notice their absence. The cheap, repeatable countermeasure is what the reviewer did: delete or invert each new guard and confirm the suite goes red. Every guard added here has now been negative-tested that way.

**Post-remediation verification:** **409 tests, 96.36%** coverage, ruff check + format clean, `mypy src` clean. Live re-checks: first sync `pull: 8, skipped: 20` with the 20 issue numbers enumerated (previously "already in sync"); `scan-apply` re-run byte-identical no-op; missing decisions file → `task-sync scan-apply: cannot read decisions file /nope/missing.json: No such file or directory`, exit 1.

**Note for the #167 close comment:** the issue's stated acceptance criterion is "an open *or recently-closed* one **is** adopted", and the shipped default (`0`) deliberately does not adopt recently-closed issues. That reversal is evidence-based (D37) and user-approved, but it must be stated on the issue or a future reader will read the criterion, read the test asserting the opposite, and conclude the fix is wrong. **Done** — posted as a comment on #167 with the measurement table and both investigation findings.

**Windows CI failure (one round, root-caused not retried).** `Task Sync Tests (windows-latest)` failed while ubuntu passed: 3 of the new `_load_decisions` tests used `pytest.raises(..., match=str(path))`. **`match` is a regex**, and the Windows tmp path `C:\Users\runneradmin\...` makes `\U` an incomplete escape, so `re.compile` raised `re.error` before the assertion was ever evaluated. Ubuntu passed only because POSIX paths contain no backslashes. Reproduced locally by running the real Windows path through `re.search` (`re.error: incomplete escape \U at position 2`), then fixed with plain substring assertions on the exception message — same property checked, no regex in the path. **Pattern for the future: never interpolate a filesystem path into `pytest.raises(match=...)`; use a substring assert or `re.escape`.**

**Result:** Shipped as personal-plugin **11.3.0** via PR #184 (squash-merged to main `1d5eacd`; 2 commits — feature + the Windows fix). All 21 required checks green on both OSes. #167/#168 auto-closed; #181/#182 filed from the investigation. Installed plugin cache updated 11.2.1 → **11.3.0** (`claude plugin marketplace update` — note `claude plugin update personal-plugin` reported "Plugin not found"; the marketplace-level refresh is what pulls a new version). Both features verified live **from the cache**: `scan-apply --help` present, and `sync --plan` against the real tracker prints `pull: 6, skipped (closed outside adopt window): 22 — use --adopt-all to mirror them`.

**Duration:** ~one session (investigate → design → build → measure → redesign → review → remediate → ship).

--- New session: 2026-07-28 — full-marketplace audit: evaluate every plugin, skill, command, agent, and reference for optimization targeting Opus 5 (primary) / Sonnet 5 (secondary); deliverable is a detailed report on branch `claude/opus5-plugin-optimization-mf4ycb`. ---

### Entry 052 — Opus 5 / Sonnet 5 optimization audit across all plugins [plugin] [skill] [command] [docs] [decision]
**Date:** 2026-07-28
**Environment:** Linux VM (Claude Code remote), branch `claude/opus5-plugin-optimization-mf4ycb` off main `795f92f` (clean, 0/0 vs `origin/main`). personal-plugin 11.3.0, bpmn-plugin 4.3.1, slide-gen 1.2.0, marketplace 3.3.0.
**Status:** COMPLETE — audit report on branch; findings await owner triage into GitHub issues

**Objective:** Thoroughly evaluate all three plugins (23 commands, 33 skills, 3 implementer agents, 10 arch-review agents, references/hooks/tools/evals/CI) and determine changes needed to optimize for Claude Opus 5 (`claude-opus-5`, primary) and Sonnet 5 (`claude-sonnet-5`, secondary). Deliverable: a full per-component report in `reports/`, committed to the audit branch. This entry covers the audit itself; any code changes it recommends are follow-up work, not this entry.

**Hypothesis:** (a) Agent frontmatter is already future-proof (ADR-0005 tier aliases) so `model: opus` resolves to Opus 5 with zero changes; (b) the main staleness is in docs/references and Python-tool defaults — initial grep already shows `claude-opus-4-8` in `research-topic`, `research-models.md`, `api-key-setup.md`, plus `claude-opus-4`/`claude-sonnet-4-5`/`claude-haiku-3-5` examples in `new-skill.md`, `common-patterns.md`, `templates/skill.md`, `patterns/advanced-features.md` (visual-explainer tooling already moved to `claude-sonnet-5`); (c) tier-routing guidance (implement-plan D14–D16 escalation, advanced-features model-override advice) will need recalibration because the sonnet tier is now substantially stronger; (d) most prompt bodies will need style-level trims (micro-step scaffolding written for weaker models) rather than structural change. Success criteria: every component gets an explicit verdict (OK / minor / needs-change) with file:line-anchored recommendations.

**Method:** 6 parallel read-only review subagents (commands / personal skills ×2 / bpmn+slide-gen / agents+references+hooks / tools+evals+CI+docs), each with the same rubric: stale model IDs, ADR-0005 compliance, effort calibration, prompt-style anachronisms, harness-feature currency, triggering metadata, context economy, tier-routing logic. Synthesis by orchestrator into `docs/model-optimization-audit-opus5-sonnet5-20260728.md`.

**Rollback Plan:** N/A — audit is read-only over plugin content; the only writes are additive (this entry + the report file) on a feature branch. Undo = delete the branch.

**Result:** COMPLETE — report shipped at `docs/model-optimization-audit-opus5-sonnet5-20260728.md` (924 lines, ~150 files examined, 106 per-component verdicts). **22 components NEEDS-CHANGE, ~44 MINOR, ~85 OK; 21 High / ~92 Med / ~142 Low findings.** Hypothesis outcomes:

- **(a) CONFIRMED, fully:** all 13 agent definitions (3 implementers + 10 architects) are clean tier-alias/`inherit` frontmatter — `/implement-plan` and `/arch-review` pick up Opus 5/Sonnet 5 with zero changes. ADR-0005's structural fix worked exactly as designed.
- **(b) CONFIRMED with a critical addition:** staleness is concentrated in docs/references/generators as predicted — but the audit found a **live functional break, not just stale IDs**: the research pipeline's Claude leg sends `thinking.budget_tokens`, which returns HTTP 400 on the entire current model family (Opus 4.8 AND Opus 5). `/research-topic`'s Claude dispatch fails on every request today. The fix (adaptive thinking + `output_config.effort`) must ship with the `claude-opus-4-8`→`claude-opus-5` bump (report P0.1).
- **(c) CONFIRMED:** tier-routing recalibration needed, but surgically — exactly 3 files must move in sync (sonnet-implementer, opus-implementer, plan-template Rule 17: multi-file-with-clear-spec moves from opus to sonnet), plus a one-sentence deliberate `fable` policy so "no escalation above Opus" reads as decision, not staleness.
- **(d) PARTIALLY confirmed:** style-level trims are needed (ultrathink keywords, 200K-era token budgets, hand-rolled pre-AskUserQuestion menus) but the bigger systematic finds were behavioral: **20 unguarded `` !`git …` `` injections across 5 skills (#183 confirmed in prime/ship/clear-prep/explain-project/leak-risk-audit)**; an 11-skill `disable-model-invocation`-vs-"Suggest when…" contradiction (the flag deletes the very description carrying the triggers — dead metadata); ship's diff-size gate computing the literal string `deletions(-)` so its >500-line gate can never fire (another E043-class guard-that-cannot-fire); prime mandating fork dispatch its allowed-tools doesn't grant; bpmn-to-drawio's SKILL re-teaching the partial-DI bug (#143) its own bundled tool fixed in 4.3.x; and all 3 hook recipe docs shipping a JSON shape that silently fails to load.

**Pattern recognition (E043 class recurs):** four independent guards-that-cannot-fire found in one audit — ship's diff gate, prime's impossible dispatch, the 11 dead trigger descriptions, and the unenforced ADR-0005 rule itself (no CI/pre-commit/schema check stops a pinned ID in agent frontmatter; README.md:179 even says "Model pinned in frontmatter"). Report P6 recommends the tier-alias allowlist gate in BOTH validate.yml and scripts/pre-commit, negative-tested before wiring, per the E043 rule.

**What worked:** the 6-way parallel fan-out with a single shared rubric completed the full ~150-file sweep in one pass with zero scope overlap; grounding the rubric in this repo's own doctrine (ADR-0005/0006, E043, #183, D14-D16) made the subagents find contradictions between the repo's rules and its files (README vs ADR-0005; advanced-features.md's wrong "failure is silent" claim vs #183) rather than generic style nits. Live verification by subagents (e.g. reading visual-explainer's config.py to catch the SKILL.md documenting a nonexistent env var `GOOGLE_IMAGE_MODEL`) caught things a doc-only pass would have missed.

**Follow-up:** report's "Suggested shipping shape" = 5 PRs (P0 functional fixes → P1 model refs → P2+P3 tier/effort → P5 metadata after verify-or-prune probes → P6 CI guard + doc sync), eval re-baseline (description-triggers first) after PR 3. Awaiting owner triage into the GitHub-issues canonical backlog (A2/A12 directive) — no issues filed from this session (not requested).

**Duration:** ~1 hour (6 parallel subagents ~6-7 min each; synthesis + report assembly the remainder).

### Entry 053 — File the E052 audit findings as GitHub issues (canonical backlog sync) [decision] [cleanup]
**Date:** 2026-07-28
**Environment:** Same session as E052, branch `claude/opus5-plugin-optimization-mf4ycb` at `95cb0d4`. Filing via GitHub MCP.
**Status:** COMPLETE

**Objective:** Per user request, convert the E052 audit report (`docs/model-optimization-audit-opus5-sonnet5-20260728.md`) into GitHub issues — the canonical backlog (A2/A12 directive) — with each issue body carrying the findings/evidence and a follow-up comment carrying the corresponding recommendations.

**Plan:** ~18 issues mapped to the report's P0–P6 plan, one per coherent work bundle (not one per finding — 250+ singleton issues would be unusable). Duplicate-avoidance: #183 already covers 18 of the 20 unguarded `` !`git …` `` injections (clear-prep/prime/explain-project/ship) plus the advanced-features.md:132 root-cause fix — it gets an EXTENDING COMMENT (leak-risk-audit's 2 impossible parse-time `<dataset-path>` injections; explain-project's wrong-repo injection in GitHub-URL mode), not a duplicate issue. Conventions followed: `[Pn]` title prefix (per E039/C23); labels restricted to the existing set (`bug`, `enhancement`, `tech-debt`, `docs`, `priority/P2`, `priority/P3` — probed; no P0/P1 labels exist).

**Hypothesis:** 18 create calls + 19 comment calls succeed; tracker open count goes 6 → 24; no duplicates of #169-171/#181-183.

**Rollback Plan:** Issues can be closed (`not_planned`) if the owner rejects the triage; the extending comment on #183 is additive. No repo files are touched beyond this notebook entry.

**Result:** COMPLETE — all 37 API calls succeeded, zero duplicates. **Issues #189–#206 filed** (body = findings/evidence with file:line; first comment = recommendations, per the requested format), plus the extending comment on #183. Mapping:

| # | Title (abridged) | Report section |
|---|---|---|
| #189 | [P0] research-topic Claude leg 400s (budget_tokens) + stale claude-opus-4-8 | P0.1 |
| #190 | [P1] ship diff-size gate computes "deletions(-)" — gate can never fire | P0.4 |
| #191 | [P1] prime mandates fork dispatch its allowed-tools doesn't grant | P0.5 |
| #192 | [P1] allowed-tools drift — 8 components | P0.8 |
| #193 | [P1] bpmn-to-drawio re-teaches the fixed partial-DI bug (#143) | P0.6 |
| #194 | [P1] hooks recipes ship a JSON shape that silently fails to load | P0.7 |
| #195 | [P1] build-cfa-deck dead snippet / duplicates / machine paths | P0.9 |
| #196 | [P1] visual-explainer documents nonexistent $GOOGLE_IMAGE_MODEL | P0.10 |
| #197 | [P1] stale/pinned model IDs in generator templates + docs | P1 |
| #198 | [P2] tier-routing recalibration (3-file sync + fable policy + knob split) | P2 |
| #199 | [P2] effort calibration (ultra-plan ultrathink; ~15 missing effort fields) | P3 |
| #200 | [P2] 200K-era token thresholds → context-relative | P4 |
| #201 | [P2] disable-model-invocation deletes 11 skills' trigger descriptions | P5 |
| #202 | [P2] verify-or-prune unverified harness features + fictional /schedule | P5 |
| #203 | [P3] AskUserQuestion adoption (4 components) | P5 |
| #204 | [P3] enforce ADR-0005 in CI + pre-commit (negative-tested) | P6 |
| #205 | [P3] re-baseline model-sensitive evals under Opus 5 | P6 |
| #206 | [P3] doc/inventory sync + context-economy cleanup | P6 |

**#183 extension:** 5th affected skill (leak-risk-audit — parse-time `<dataset-path>` placeholders, breaks in EVERY directory) + explain-project's wrong-repo injection in GitHub-URL mode; count 18 → 20 injections. Cross-links recorded: #190/#191 share fix lines with #183; #201 must land before #205's description-triggers re-run; #197 and #204 are instance-fix + class-close pair.

**What worked:** probing label existence before filing (only priority/P2, priority/P3, docs exist — no P0/P1 labels; `[Pn]` title prefix carries priority per E039's convention) avoided create failures; reading #183 first turned a would-be duplicate into a higher-value extending comment.

**Duration:** ~15 min.

--- New session: 2026-07-29 — land the E052/E053 audit work on `main` and priority-pass the resulting backlog. ---

### Entry 054 — Land the E052/E053 audit work on main + priority-pass the backlog [docs] [decision] [cleanup]
**Date:** 2026-07-29
**Environment:** Linux VM, branch `docs/e052-audit-landing` off `main` `795f92f`. personal-plugin 11.3.0, bpmn-plugin 4.3.1, slide-gen 1.2.0, marketplace 3.3.0.
**Status:** COMPLETE

**Landing context.** E052 and E053 were written but never merged — they sat on `claude/opus5-plugin-optimization-mf4ycb`, 3 commits ahead of `main` (`dc4cb97` opens E052 → `95cb0d4` adds the report → `e5e0187` adds E053), so a fresh session reading `main`'s notebook alone saw only "18 issues appeared from nowhere after E051." That is the Rule 6 failure mode the notebook exists to prevent, and it is worth naming: **an entry that is written but unmerged is, from the next session's point of view, an entry that does not exist.** Docs-only branches need to land as promptly as code branches.

**Objective (this session):** merge the branch to `main` so the audit report and E052/E053 enter the permanent record; reconcile the Action Items row; correct E053's `Status`. Scope was deliberately capped at landing — **no issue fixes** (the owner chose "land the branch only"); #189–#206 all stay open.

**Hypothesis:** docs-only PR, all required checks green (the report is new markdown that has never been linted, so markdownlint is the only real risk). No version bump — nothing under `plugins/` changes.

**Rollback Plan:** revert the squash-merge commit on `main`; the branch and all 18 issues are untouched by this PR.

**Corrections applied while landing:**

1. **The audit set is #189–#206 (18 issues), not #186–#206.** #186/#187/#188 are open **Dependabot PRs** (`actions/checkout`, `bpmn2drawio`, `visual-explainer` bumps). `gh issue list` correctly omits them, but `gh issue view <n>` resolves a PR number without complaint — so spot-checking "the range" by number makes three PRs masquerade as audit issues. Recorded in the Action Items row so the next session doesn't repeat it.
2. **E053's `Status: IN PROGRESS` contradicted its own `Result: COMPLETE`** — corrected to COMPLETE.
3. **The Action Items row had two competing edits** — one committed on the branch, one uncommitted in the working tree — both rewriting the same line. Merged rather than picking a side: the branch's landing-order guidance plus the working tree's P0/P1 detail.

**Independent verification of the two headline claims** (audit findings were produced by subagents, so the P0 was re-checked against a primary source rather than taken on trust):

- **#189 CONFIRMED against the `claude-api` skill** (authoritative, not the audit's own reasoning): `thinking: {type: "enabled", budget_tokens: N}` is **removed — not merely deprecated** — and returns **400 on Fable 5 / Opus 5 / Opus 4.8 / Opus 4.7 / Sonnet 5**. It survives only on Opus 4.6 / Sonnet 4.6 as a transitional escape hatch. So `/research-topic`'s Claude leg fails on every dispatch today and would still fail after a naive model-ID bump. The fix is `thinking: {type: "adaptive"}` + `output_config: {effort: …}` (`low`|`medium`|`high`|`xhigh`|`max`), shipped together with `claude-opus-4-8` → `claude-opus-5`. Note `claude-opus-4-8` is **not retired** — it is a current model one generation back at identical pricing ($5/$25 per MTok), so the bump is a genuine drop-in, exactly as the issue claims.
- **#190 CONFIRMED empirically**, not by reading: running the skill's own injection against this repo's working tree returned the literal string `deletion(-)`. `git diff --stat`'s summary line ends in an English word, never a number, so the `> 500` comparison is string-vs-int and the gate cannot fire. Fourth guard-that-cannot-fire in the E043 class.

**Priority pass (no work done, recorded for whoever picks this up):**

| Tier | Issues | Character |
|---|---|---|
| **P0 — live breakage** | #189 | The only issue where something is broken *right now*, independent of any model change. Fix first. |
| **P1 — quick, high-value** | #190, #196, #197 | Small diffs, disproportionate value: a guard that can't fire, a documented env var that does nothing, and stale model IDs sitting in the generator templates — which multiply into every future skill, so they decay fastest if deferred. |
| **P1 — structural** | #191, #192 | `allowed-tools` grants that can't execute their own documented workflows across 8 components. Overlaps **#183**'s injection guarding in `prime`/`ship` — land them together or they'll conflict. |
| **P1 — self-contained doc rewrites** | #193, #194, #195 | One component each, no cross-cutting risk. Parallelizable. |
| **P2/P3 — recalibration** | #198–#206 | Real work, no urgency. Two carry hidden cost: **#202** needs live harness probes to verify-or-prune unverified frontmatter keys, and **#201** is 11 independent per-skill judgment calls, not one mechanical edit. |

**Sequencing constraints** (from E053's cross-links, still binding): #201 must land before #205's `description-triggers` eval re-run, or the two causes conflate. #197 (fix the instances) and #204 (add the CI guard that closes the class) are a pair — guard after instances, and **negative-test the guard before wiring it** (E043).

**Lint findings on landing.** The 924-line report had never been linted — it was committed straight to the branch — and failed 14 markdownlint rules (MD052 ×12, MD012 ×1, plus an MD018 in E053's own body), so the branch would have gone red in CI. All three root causes and their fixes are now a standing rule: see CLAUDE.md, "Lint long markdown before you COMMIT it". Per E043 the linter was negative-tested rather than trusted — a deliberately-malformed file exits 1, both real files exit 0.

**Result:** COMPLETE. PR #207 squash-merged to `main` as `e38a6ea` (2026-07-28T19:41Z); the audit report and E052/E053 are now on `main`, all 22 checks green. #189–#206 remain open — no fixes were in scope. *Correction to E053: `priority/P0` and `priority/P1` labels were created after that entry was written and are now applied to #189–#197, so its "no P0/P1 labels exist" note no longer holds. Relabelling then exposed a task-sync bug — `VALID_PRIORITIES` has no `P0`, so a `priority/P0` label is dropped on pull and would be `--remove-label`'d from the issue on the next push (filed as #208).*

**Duration:** ~1 session (verify → land → relabel → file #208).

### Entry 055 — Rotate E017–E050 to archive + condense the living sections [cleanup] [decision] [docs]
**Date:** 2026-07-29
**Environment:** Linux VM, branch `docs/notebook-rotation-e017-e050` off `main` `e38a6ea`. Notebook at 1211 lines / 37 entries before this work — past Rule 12's ~1200-line threshold, under its 40-entry one.
**Status:** COMPLETE

**Objective:** Bound the notebook's first-read size without losing anything future-meaningful. User directive: "remove any information that is no longer relevant, and summarize any older information as much as possible while keeping any information that may be meaningful or important in the future."

**Method:** A read-only subagent audited all 1211 lines and produced the plan; its load-bearing claims were then independently verified before execution rather than taken on trust (E039's "treat subagent output as a lead, not a conclusion").

**Hypothesis:** Archiving E017–E050 verbatim while leaving a greppable per-entry digest lands the notebook near ~430 lines (~65% reduction) with every decision preserved in the Decision Log and every external citation still resolving. Success criteria: D1–D51 gapless; 34 entry headings in the archive and zero overlap with the live file; a digest hit for every one of E017–E050; markdownlint clean; `git status` shows the force-added archive.

**Rollback Plan:** Single-commit revert. The archive is an additive new file and the cut is a contiguous line range, so `git revert <sha>` restores the 1211-line original exactly. The D38–D51 promotion is a **separate, earlier commit** (E042 precedent) so a bad promotion can be reverted without losing the rotation, and vice versa.

**Deliberate deviation from `references/rotation.md`, recorded per Rule 4.** The documented heuristic is "keep the living sections + the last ~20 entries." This rotation keeps only E051–E055 live and archives 34 entries — chosen because the user asked to summarize as aggressively as possible, and because the by-the-book alternative (cut at E033, ~790 lines) leaves ~300 lines of thrice-duplicated, fully-closed 2026-07-16→18 narrative live for almost no headroom. The mitigation is the **digest**: a 2–5 sentence live record of every archived entry, which is both cheaper to read than 20 full entries and *better* for citation integrity than the E043-precedent rotation, which left nothing behind. Alternatives considered: Option B (by-the-book, cut at E033, ~790 lines) — rejected as above; delete the old entries outright — rejected, violates Rule 12's MOVE-never-delete invariant.

**Result:** COMPLETE — **1211 → 458 lines (62% reduction)**, 37 entries → 5 live + 34 archived, with 852 lines moved verbatim to the archive. Hypothesis confirmed on every criterion.

| Check | Result |
|---|---|
| Decision Log gapless + monotonic | D1–D51 ✅ (14 promoted, D31–D34 reordered) |
| Entry headings in archive | 34 ✅ |
| Live/archive heading overlap | 0 ✅ |
| Digest covers E017–E050 | all 34 ✅ (guard negative-tested) |
| markdownlint | exit 0 on both files ✅ |
| Archive force-added past `archive/` gitignore | `A docs/archive/LAB_NOTEBOOK-E017-E050.md` ✅ |

**What worked:** splitting the promotion into its own commit (E042 precedent) meant the destructive cut had a clean, independently-revertable predecessor. Locating the cut boundaries **by content** (`--- New session: 2026-07-16 — /arch-review` … `--- New session: 2026-07-22`) rather than by hardcoded line numbers made the splice immune to the +14-line shift the D-promotion had just introduced — hardcoded numbers from the audit would have silently cut the wrong range.

**Verifying the auditor.** The plan came from a subagent, so its load-bearing claims were re-checked before execution rather than trusted (E039). All held: S1 (23 commands / 40 skills), S2 (3 + 10 agents), S3 (48 evals), S4 (no `autoUpdate` key in marketplace.json — the claim three separate places still repeated after D19 corrected it), S8 (0 `.mypy-baseline` files). The most valuable catch was one the audit made and a mechanical sweep would have destroyed: **E018's "decision D3" and E022's "decision D2" cite the arch-review IMPLEMENTATION_PLAN's own internal numbering, not this Decision Log** — where D2/D3 are the frontmatter and plugin.json rules. Promoting those by `grep` would have written two false rows.

**Pattern recognition — the audit's own traps bit this edit, exactly as predicted.** Its Risk #5 warned that the digest would trip MD018 and MD049. Both fired on the first lint: `#173 (…` at column 1 parsed as a heading, and `_underscore_` emphasis collided with this file's established asterisk style. That is the third consecutive session in which markdownlint caught something only at commit time — the standing rule (CLAUDE.md, "Lint long markdown before you COMMIT it") is now earning its place.

**Deviation accepted, on the record:** only 5 entries remain live against `rotation.md`'s "~20" heuristic. The digest is the mitigation — it is greppable, so all 13 external prose citations degrade to "shorter but present" rather than "gone", which is strictly better than the E043-precedent rotation that left nothing behind. **Do not "fix" the digest's `####` headings into `### Entry NNN`** — the zero-overlap check in `rotation.md` depends on the live file having no `### Entry` heading for an archived entry.

**Follow-up:** `rotation.md` should record the digest variant as a sanctioned option, since this is now the second rotation and the two used different shapes.

**Duration:** ~1 session (audit → verify → promote → rotate → condense).

--- New session: 2026-07-29 — fix #208, the task-sync P0 priority round-trip bug found while relabelling the E052 audit backlog. ---

### Entry 056 — Fix #208: task-sync drops and then deletes `priority/P0` [debug] [decision] [build]
**Date:** 2026-07-29
**Environment:** Linux VM, branch `fix/task-sync-p0-priority` off `main` `cb6a225`. personal-plugin 11.3.0. Repo source verified byte-identical to the installed 11.3.0 cache before starting.
**Status:** COMPLETE

**Objective:** Close #208 — `VALID_PRIORITIES` is `("P1","P2","P3","P4")`, so a `priority/P0` label is discarded on pull *and* `--remove-label`'d from the issue on the next push. Fix the enum, fix the silent-discard class the enum gap exposed, and add the regression tests that would have caught it.

**Root cause (two independent defects that compound).** The enum gap alone would only mis-sort. The data loss comes from pairing it with an over-broad ownership predicate:

1. `_priority_from_issue` returns the suffix only `if suffix in VALID_PRIORITIES`, else falls through to `None` — silently.
2. `is_managed_label` claims **every** `status/*` and `priority/*` label for the tool regardless of whether the suffix is recognized, so `user_labels()` strips it from the user set too.

Together the label is dropped twice on pull; then on push `task_to_issue_fields` omits it from `desired`, and the GitHub provider's `for name in sorted(current - desired): --remove-label` deletes it from the tracker. The tool destroys a label it never understood — the D35 silent-remote-clobber class.

**Hypothesis:** Adding `P0` fixes the reported symptom, but the *class* is fixed only by narrowing `is_managed_label` to recognized suffixes, so any unknown `status/*` or `priority/*` label is preserved as a user label and therefore survives the round-trip. Success criteria: a round-trip property test over every valid suffix **plus unknown suffixes** passes; each new test is mutation-tested (revert the fix, confirm it fails); coverage stays ≥90; full suite green on both OSes.

**Rollback Plan:** Single-commit revert; the change is confined to `models.py`, `reconcile/mapping.py`, and tests. `tasks.json` files are untouched by this change — it alters no on-disk schema, only which label values are recognized. No migration needed either way.

**Deliberate scope decision — `P4` stays.** #208 asked whether it should go, since nothing uses it. Removing it is a **breaking change for data at rest**: `Task.__post_init__` validates `priority` on load, so any existing `tasks.json` carrying `P4` would fail to load with a `ValueError` after the change. task-sync is a general per-repo tool, not private to this marketplace, so the blast radius is unknown. Widening the enum is additive and safe; narrowing it is not. Alternatives: drop `P4` for a clean P0–P3 scale matching this repo's `[Pn]` title convention — rejected on the data-at-rest risk; leave the scale alone and special-case P0 — rejected, it doesn't fix the class.

**The fix (two parts, each mutation-tested independently).**

1. `models.py` — `VALID_PRIORITIES` gains `P0`: `("P0","P1","P2","P3","P4")`.
2. `reconcile/mapping.py` — `is_managed_label` now requires **both** a managed prefix *and* a recognized suffix (`VALID_STATUSES` / `VALID_PRIORITIES`). An unknown suffix is left in the user label set, so it round-trips instead of being stripped-then-deleted. Module docstring corrected — it claimed the reverse mapping "strips every `status/*` / `priority/*` label", which is exactly the over-broad behavior that caused the bug.

**Result:** COMPLETE. 425 tests pass (was 415); coverage 96.37% (floor 90) with `mapping.py` at **100%**; ruff, ruff-format, and mypy all clean.

| Mutation | Expected | Observed |
|---|---|---|
| Drop `P0` from the enum, keep the predicate fix | fail | **1 failed** (`test_p0_is_a_valid_priority`) |
| Revert the predicate, keep `P0` | fail | **9 failed** |
| Both fixes in place | pass | **425 passed** |

Before writing the fix, the new tests were run against the *unfixed* code and 9 failed — proving they catch the bug rather than merely covering the line. The control (`test_every_valid_priority_survives_a_full_round_trip`) passed for P1–P4 throughout, confirming the harness itself was sound.

**End-to-end verified**, not just unit-tested (E049): replaying #208's exact repro against the fixed source, `priority/P0` now maps to `P0` and proposes no `--remove-label`; so does `priority/urgent`, an unknown suffix the tool still refuses to delete.

**System insight — the test agreed with the bug.** `test_priority_round_trip` was parametrized over a *hardcoded* `["P1","P2","P3","P4"]` rather than over `VALID_PRIORITIES`. It passed at 100% line coverage on `mapping.py` while the P0 path was broken, because the literal list drifted from the enum in lockstep with the defect. Re-derived it from `VALID_PRIORITIES` so the same drift cannot recur. This is the sharpest instance yet of E051's "coverage is not verification": `mapping.py` was already at 100% *before* the fix.

**Scope decision recorded above:** `P4` stays (removing it would break `tasks.json` files at rest).

**Doc layer synced in the same PR.** Three sites still documented the scale as `P1`-`P4` and would have contradicted the code: `references/command-reference.md` (×2, the `--priority` filter and the validation rule) and `references/sync-semantics.md`. This is the same drift class the E052 audit kept finding (#193, where the bpmn-to-drawio docs re-taught a bug the bundled tool had already fixed) — a tool change is not done until the layer that documents it moves too.

**Follow-ups filed / noted:**
- **#210** — `plugins/personal-plugin/CHANGELOG.md` is missing 11.2.0 and 11.3.0 entirely (found while adding the 11.4.0 entry). Another documented-step-with-no-gate, E043 class.
- **Local data repair still pending.** The fix prevents recurrence but does not heal the already-corrupted record: this repo's `tasks.json` still holds `priority: null` for #189, and because the remote has not changed since, `sync --plan` reports 0 pulls — the tool considers the wrong value in sync. Repair after the 11.4.0 cache update.

**Version:** 11.3.0 → **11.4.0** (minor, not patch): `P0` becoming an accepted value is additive user-visible capability, and unknown-label push behavior changes. Under D44 a capability *narrowing* would have been major; this widens.

**Duration:** ~1 session (repro → TDD → fix → mutation-test → release prep).

### Entry 057 — Fix #212: `sync --apply` crashes on every push (`--remove-milestone` does not exist) [debug] [build]
**Date:** 2026-07-29
**Environment:** Linux VM, branch `fix/task-sync-milestone-clear` off `main` `9e72747`. personal-plugin 11.4.0. `gh version 2.45.0`.
**Status:** COMPLETE

**Objective:** Close #212. `providers/github.py` appends `--remove-milestone` whenever a pushed task has no milestone, but `gh` 2.45 has no such flag — so `gh issue edit` exits non-zero and `apply` raises, aborting the run part-way through.

**Root cause.** Two compounding mistakes, the same shape as #208 one layer up:
1. `task_to_issue_fields` **always** emits `milestone`, so `"milestone" in fields` is always true; when the task has no milestone the provider asks `gh` to clear one — even when the issue has no milestone either and there is nothing to clear.
2. The flag it uses does not exist. `gh` 2.45 has `--remove-assignee` / `--remove-label` / `--remove-project`, but milestone removal was never in that family.

**Why it survived the test suite — the mock agreed with the bug.** `test_update_issue_clears_milestone` asserted `"--remove-milestone" in edit_call`. Because `subprocess.run` is mocked, the assertion encoded a flag `gh` does not accept and passed happily. Argv-shape tests only catch real defects if the argv is checked against the real CLI's surface; otherwise they pin the mistake in place. Directly analogous to #208, where a hardcoded `["P1".."P4"]` had drifted alongside the enum.

**Hypothesis:** Fixing (1) alone removes the crash for every real-world push, since both sides are almost always `None`. Fixing (2) as well makes a genuine clear work on any `gh`. Success criteria: a test asserting the emitted argv contains **no** `--remove-milestone`; a genuine-clear test asserting the portable call; suite green; mutation-tested.

**Rollback Plan:** Single-commit revert; the change is confined to `providers/github.py` and its tests. No schema or on-disk format changes.

**Portable spelling — verified empirically, not guessed** (guessing a flag is what caused this). `gh api` is already used in this file by `ensure_milestone`, so it is not a new dependency. Probed against a nonexistent issue number so the request 404s and mutates nothing, with `--verbose` to read the outgoing body:

- `-F milestone=null` → `"milestone": null` (JSON null — what the REST API needs to clear)
- `-f milestone=null` → `"milestone": "null"` (a string — the wrong thing, and the trap)

So the clear is `gh api repos/<repo>/issues/<n> -X PATCH -F milestone=null`, which works on every `gh` version. **No minimum-`gh` floor or preflight version check is needed** — that was the open question in #212, now closed by measurement rather than by declaring a requirement.

**The fix.** `update_issue` now (a) clears a milestone only when `self._view(number)` shows one is actually set, and (b) does the clear via `gh api repos/<repo>/issues/<n> -X PATCH -F milestone=null` after the main edit succeeds, rather than as a flag on it. `changed` is no longer set for a no-op milestone, so a push that changes nothing no longer triggers a spurious `gh issue edit` (which would bump `updated_at` and perturb last-write-wins). Sequencing the API call *after* the edit avoids a partial application where the milestone is cleared but the edit then fails.

**Result:** COMPLETE. 425 → 427 tests; ruff, ruff-format, mypy clean; coverage 96.33% (floor 90).

| Mutation | Expected | Observed |
|---|---|---|
| Restore `--remove-milestone` | fail | **2 failed** |
| Clear unconditionally (drop the has-milestone check) | fail | **1 failed** |
| Fix in place | pass | **427 passed** |

**End-to-end on live data — the real proof.** Re-ran the exact `sync --apply` that had been raising: `applied 0 create(s), 1 push(es), 3 pull(s); 0 conflict(s)`, and a follow-up plan came back **all zeros**. #189 still carries `["bug","priority/P0"]` after a real push, so this run simultaneously confirms the #208 fix under the condition that used to destroy the label.

**System insight — mocks pin mistakes in place.** `test_update_issue_clears_milestone` asserted `"--remove-milestone" in edit_call` and passed for the tool's whole life, because `subprocess.run` was mocked. An argv-shape assertion is only as good as the argv's agreement with the real CLI. This is the third variant of one pattern in two days: a hardcoded priority list that drifted from its enum (#208), a mock that asserted a nonexistent flag (#212), and E043's guards that could not fail — **all cases where the check agreed with the defect and reported success.** Coverage was 92% on `github.py` throughout.

**Decision closed by measurement, not declaration.** #212 left open whether to declare a minimum `gh` version. Probing `gh api`'s `-F` against a 404 endpoint showed a portable spelling exists, so no version floor and no preflight check are needed — strictly better than pinning a requirement onto every user.

**Version:** 11.4.0 → **11.4.1** (patch: crash fix, no capability change).

**Duration:** ~1 session (repro → probe → TDD → fix → mutation-test → live verify).
