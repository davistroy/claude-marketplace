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
| D52 | **The `/research-topic` Claude depth ladder is `low`/`medium`/`high` (8k/16k/32k `max_tokens`), capped by the transport rather than by preference** — the leg is a single non-streaming `curl`, and Anthropic requires `max_tokens` >= 64,000 at `xhigh`/`max`, which is ~18 min of generation and cannot finish inside any defensible `--max-time` | 2026-07-29 | ACTIVE | E058 | `medium`/`high`/`xhigh` — rejected, `xhigh` under 64k `max_tokens` is explicitly against Anthropic's guidance, so the top tier would ship knowingly-marginal; raising to 64k blows the transport budget. Rewrite the leg to stream — rejected as out of scope for a P0 crash fix and because it means shipping unverified SSE-parsing bash into the one path that is currently broken; filed as a follow-up. `budget_tokens` was a token ceiling and `effort` governs depth *and* total spend, so the ladder had to be re-derived, not translated |
| D53 | **A bundled skill that needs a Bitwarden secret must `eval "$(grep -m1 '^export BWS_ACCESS_TOKEN=' ~/.config/claude-env.sh)"` before calling `bws`, never trust the inherited env var** — `~/.bashrc:167` loads that file behind `case $- in *i*)`, so a non-interactive tool shell keeps whatever stale token it inherited | 2026-07-29 | ACTIVE | E058 | Treat `400 invalid_client` as a revoked token and rotate — rejected, the token was valid; the shell was loading a retired machine account (`da8557b9…`) while the file held the current one (`f283b1a6…`). Treat it as a region mismatch — rejected by measurement, US *and* EU identity endpoints both rejected the stale token |
| D54 | **The new plan's scope is "actively wrong or actively multiplying" (16 issues), not "everything open" (24)** — 8 calibration/hygiene issues (#198, #199-sweep, #200, #206, #210, #216, #217, #218) are deferred to a follow-on plan. Ordering within the plan puts silent-corruption and data-loss fixes (Phases 2-4) *ahead* of documentation multipliers | 2026-07-29 | ACTIVE | E060 | All 24 in one plan — rejected: ~60 work items, and it would have deferred #193 (silent layout corruption) and #181 (silent remote clobber) behind doc work. My own first split did exactly that and was corrected before generation. Ship only the 8 P1s — rejected: leaves the generator layer, which propagates six issues' defects into every future skill, untouched |
| D55 | **#204 (the ADR-0005 CI gate) lands BEFORE #197 (the stale-ID instances), reversing E053's recorded instance-then-class order** — all 13 agent files already comply, so a correctly-scoped gate is green on day one and has no dependency on #197 | 2026-07-29 | ACTIVE | E060 | E053's "guard after instances" order — rejected on evidence: it assumes the gate would fail on existing violations, and there are none. The real hazard runs the other way: if #204's scope creeps to a repo-wide pinned-ID grep it fires on the 8 `claude-sonnet-5` Python defaults that **ADR-0005 line 24 explicitly permits**, reddening `main`'s own push build and deadlocking every subsequent PR until #197 lands |
| D56 | **`Agent` is the repo's one name for the subagent-dispatch tool in `allowed-tools`; `Task` is retired from every live component** — `Task*` survives only as the distinct `TaskCreate`/`TaskUpdate`/`TaskList`/`TaskOutput` progress-tracking family, which is a different tool and is granted alongside `Agent` where a component tracks sub-agent progress (`implement-plan`'s precedent, now matched by `test-project`) | 2026-07-29 | ACTIVE | E061 | `Task` as the canonical name — rejected: `arch-review` and `implement-plan`, the two components that actually dispatch at scale, already use `Agent`, and `Agent` is the first name in the harness's own identity check. Fix only the 6 files the issue names — rejected: it would leave `Task` in `research-topic` **and in `references/templates/synthesis.md`, a generator template that mints the defect into every skill built from it** — the exact propagation E060 finding 3 is about. Both were pulled in |
| D57 | **`lab-notebook` and `create-wiki` trade `disable-model-invocation: true` for a Phase-0 confirmation gate** — they may now be model-invoked, but must confirm before creating or modifying any file. The gate is conditional on invocation source (`security-analysis`'s house pattern): it fires only on self-initiative and is skipped when the user types the slash command, and it is scoped per mode (`lab-notebook status` and `create-wiki` maintenance mode are exempt as read-only / already-configured) | 2026-07-29 | ACTIVE | E061 | Keep the flag and strip the trigger prose, as with the other seven (8.2) — rejected: these two have the highest proactive value in the set, and their triggers ("benchmark work starting", "I keep forgetting…") are exactly the ones a user provably cannot self-serve. Drop the flag as a one-line edit — rejected as the dangerous option: both skills *inject binding rules into `CLAUDE.md`*, so without a gate the model could unilaterally change how it behaves for the rest of the project's life. The gate had to land in the same change, which is why 8.3 is one item and not two |

| D58 | **The remaining backlog is scoped and sequenced by ROOT-CAUSE CLASS, not by issue number or priority label** — 12 of 19 items in scope. ~~ordered so the one gate that closes #226+#210+#218 lands first~~ — **AMENDED by D61: the "one gate" premise was refuted in Phase 1.** Deferred: #198/#200/#199-remainder (calibration), #206's context-economy half, #216, #169/#170/#171 | 2026-07-30 | ACTIVE (amended by D61) | E062 |
| D61 | **Class ① decomposes 2 + 1, not 3-into-1.** #226 and #210 collapse into ONE offline, diff-derived script carrying two *conditional* rules (bump-required-on-content-change; changelog-required-on-bump), wired as a single step in `plugin-validate` per D28. **#218 is categorically separate** — its ground truth is an external API behind a key ADR-0009/D32 forbids CI from holding, so any in-repo check is a *staleness alarm*, not a verification | 2026-07-30 | ACTIVE | E062 | One gate for all three (my Phase 0 hypothesis, and D58 as first written) — **rejected on evidence**: the three differ on input (diff / tree / external API), offline-decidability, CI-runnability, failure trigger, and event-leg sensitivity. Three independent gates — rejected: #226 and #210 genuinely do share a diff-derived mechanism, and splitting them would duplicate the deepened-checkout and event-leg logic that is the hard part. Basis for the conditional-rule shape: the two issues are in **direct tension** on `plugins/*/CHANGELOG.md` — #210's own fix is a CHANGELOG-only PR with no bump, which #226's gate blocks unless that path is exempt, while #210's enforcement half wants it mandatory on a bump | Sequence by `priority/P*` label — rejected: it splits #226/#210/#218 (P2/P3/P3) across the plan even though they are one missing gate, and it promotes #217, which is 3-of-4 wrong as filed. Take everything open — rejected: class ④ has no evidence of being mis-set (13/14 eval) and class ⑥ items are projects, not items. Take only the 4 close-the-loop items — rejected by the user, who added the hygiene half, #217's rewrite, and #230 |
| D59 | **Plan generation runs the FULL `/ultra-plan` including the Phase 1 verification fan-out, never a direct write-up from issue text** — audit-derived issues must be re-verified against the tree before being planned | 2026-07-30 | ACTIVE | E062 | Light plan from the filed bodies — rejected on the measured base rate: E060 found **22 of 24** issues from this same audit wrong as filed, and E062 reconfirmed it three more times before planning even started (#227's mechanism inverted, #199's defect at 8 sites not 3, #230 surfaced only because a rollback plan asserted something false). Verify only the near-term scope — rejected by the user in favour of the full pass |
| D60 | **`tasks.json`'s git status is an OPEN design question (#230), not a settled one** — `.gitignore` ignores it while D34 and `docs/plans/2026-07-18-task-sync-design.md:64,100,129` all specify it committed "so the base travels between the user's two machines" | 2026-07-30 | **OPEN — pending #230** | E062 | Fix inline by un-ignoring it — rejected: PR #175's public-repo reasoning is defensible even though the confidentiality subsystem already answers it, so this is a design call needing an explicit decision + alternatives, which is precisely what its absence cost the first time. Leave it undocumented — rejected: three sources currently disagree and each reads as authoritative alone |

| D62 | **All 12 unbacked freshness stamps are DELETED, along with the phantom `check-models` reference and the `## Model Check Output Examples` section documenting its output** — including the two *generators* (`explain-project/SKILL.md:392`, `create-wiki/SKILL.md:271`) that mint the pattern into every document they produce | 2026-07-30 | ACTIVE | E062 | Build a local `check-models` probe to back the column — rejected: ADR-0009/D32 forbids CI secrets so it can never gate, and the file itself says OpenAI/Google "cannot be verified offline", so a probe covering only Anthropic writes a date that **lies about two of three rows**. Delete only `research-models.md`'s column (the filed scope) — rejected: leaves 11 sites and both generator templates, the fix-instances-leave-the-mould shape. Basis: the stamp has now been hand-refreshed with no probe **twice** (`1f55dcd`, then `5cd2005` — the very PR that fixed the bug the stale stamp concealed) |
| D63 | **`scripts/update-readme.py` is generalized from one hard-coded target to a target LIST, bringing `CLAUDE.md`'s inventory block under the existing `--check` gate** — reusing `scan_plugin()` unchanged and leaving the hand-written annotation prose and the curated "Command Patterns" subset alone | 2026-07-30 | ACTIVE | E062 | Delete CLAUDE.md's name lists and point at README — rejected: README is not loaded into context, so a zero-context Claude would lose the always-loaded inventory entirely. Hand-fix the 8 defects — rejected: guarantees a ninth, which is exactly how these accumulated across 18 days and four releases. Basis: a controlled experiment already exists in-tree — README carries the same facts, is generated, and is provably drift-free; CLAUDE.md is hand-edited and carries 8 defects. This is not a missing generator but a generator with under-scoped coverage (`update-readme.py:329`) |
| D64 | **Consent gates converge on `AskUserQuestion` for every gate that is BOTH model-invocable AND consents to a write** — `security-analysis`, `wiki:207/:241`, `task-sync:247` — plus the 3 generator templates in `references/` that mint new instances. Command-level prompts stay prose (commands are user-invoked, so the self-initiative hazard does not apply); `references/templates/interactive.md` stays exempt by design | 2026-07-30 | ACTIVE | E062 | Convert `security-analysis` only (the filed scope) — rejected: leaves 14 peers and 3 generator templates. Document why prose is deliberate — rejected as the primary remedy, though its evidence is real: E061 showed **both** forms degrade to prose headlessly, so robustness is neutral between them. Explicitly NOT claimed: that prose is safer — S13's gate held because the skill body said what to do, not because prose is inherently robust. `task-sync:247` weighed heaviest: it guards publishing to a **public** repo |
| D65 | **`tasks.json` stays LOCAL-ONLY; D34's "committed" clause is superseded and the six design-doc lines corrected.** Cross-machine sync of local task state is declared out of scope, and #169 is re-scoped to note there is no cross-machine sync of the *public* list either. **Resolves D60** | 2026-07-30 | ACTIVE (resolves D60) | E062 | Commit it to restore the design's cross-machine merge base — rejected: a 127 KB file churning irreversibly into **public** history, whose safety rests on a confidentiality subsystem exercised exactly **once** out of 59 tasks with `sensitive_terms: []`, and every future local-only task would enter public history before the user chose to push it. Defer — rejected: four sources disagree and each reads as authoritative alone. Basis: the reversal has already been ratified twice deliberately (PR #175's `.gitignore`, then `config-reference.md:61-70`'s logged "Truth fix"), and D34 already makes the tracker the permanent archive |

Status values: ACTIVE · SUPERSEDED (by D#) · REVERSED (in E#) · OPEN (undecided, tracked)

## Action Items

Track follow-ups that emerge from experiments. Move to Completed when done.

### Open

| # | Action | Created | Source Entry |
|---|--------|---------|-------------|
| A22 | **`security-analysis`'s conditional-load gate is still a hand-rolled `(y/n)` prose prompt** while the two gates added in 8.3 use `AskUserQuestion`. It was outside 7.5's six consumers so it was correctly not converted, but the inconsistency is real and now documented rather than silent. Convert it, or record why the prose form is deliberate. **Tracked as #223 and now in the E062 plan scope** | 2026-07-29 | E061 |
| — | **No other open action items** — the canonical backlog is the GitHub issues list (A2/A12), now **18 open**. `IMPLEMENTATION_PLAN.md` is 42/42 COMPLETE (see A23). **Traps that recur:** `gh issue view <n>` silently resolves PR numbers; the installed plugin cache can hold *different content under the same version*, so run bundled tools from repo source when a fix matters and bump the version whenever `plugins/**` changes (#226); `bws secret list` prints plaintext — never use it as an auth probe; any injection linter must **replay the pre-pass, not grep** (74 textual sites, 14 live). | — | E043 |

### Completed

| # | Action | Created | Completed | Source Entry |
|---|--------|---------|-----------|-------------|
| C26 | **A23 CLOSED — `IMPLEMENTATION_PLAN.md` archived to `docs/archive/IMPLEMENTATION_PLAN-v12.md`** (D46), force-added past the global `archive/` ignore, with a Completed banner citing `1382a8a`/`49face4` and pointing at E061. Clears the precondition for the E062 plan | 2026-07-30 | 2026-07-30 | E062 |
| C25 | **A21 CLOSED — the 14 `description-triggers` scenarios run under Opus 5, 13/14 pass** (#205 closed). First non-self-assessed evidence that Phase 8's contract holds: both gated skills were model-invoked and stopped at their Phase-0 gate having written nothing; both locked skills stayed locked. S4 failed to cross-plugin preemption (#227); harness gaps filed (#228). **Reusable method:** fresh `claude -p` per scenario, isolated empty dir, explicit `--allowed-tools Skill Read Write Edit Glob Grep AskUserQuestion`, **`Bash` disallowed** (S13's prompt names a live host), score at first dispatch, and never treat `api_error_status: 529` as a negative — the first batch 529'd on 8 of 13 | 2026-07-29 | 2026-07-30 | E061 |
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

*Verified 2026-07-30 against `origin/main` @ `7d5ae1f`.*

| Item | State |
|---|---|
| Versions | marketplace **3.3.0** · personal-plugin **11.6.0** (E061) · bpmn-plugin **4.4.0** (E061) · slide-gen **1.3.0** (E061). All three bumped together in #225 — #222 shipped 42 items of behavior change at an *unchanged* version, leaving two trees both claiming 11.5.1 |
| Surfaces | 23 commands · 40 skills (personal 29 / slide-gen 9 / bpmn 2) · 3 implementer agents in `.claude/agents/` · 10 arch-review agents in `plugins/personal-plugin/agents/` |
| Bundled tools | visual-explainer 894 tests / 93% · **bpmn2drawio 642 / 92.79%** · feedback-docx 69 / 96.95% · **task-sync 480 / 96.30%**. All bare-`mypy` clean (D33) and ruff clean; green on 3.10/3.11/3.12. `bpmn2drawio` is the only tool whose version tracks its plugin's, enforced by a cross-file guard that caught real drift during #225 |
| Evals | **48** `.eval.md` specs; structural + coverage linter in CI (`check_eval_mapping.py`, ADR-0009/D32); LLM-judge runner deliberately deferred. **`description-triggers` run under Opus 5 on 2026-07-30: 13/14 pass** (S4 fails to cross-plugin preemption, #227). The eval defines no harness — see #228 |
| CI | `test.yml` (pytest ×2 OS, coverage floors in each tool's `[tool.coverage.report]`, pip-audit per lockfile, advisory `Python Compat (3.10)/(3.12)`) · `validate.yml` (plugin/frontmatter/version-sync, README-sync `--check`, eval linter, ruff, markdownlint). **Branch protection on `main`: 16 required checks, PR-required 0-approvals, `enforce_admins=false`** (ADR-0007/D22). *Corrected 2026-07-30 (E062): this row read "21" — the live API returns 16. An unbacked restated constant sitting in the Baseline, i.e. the #218 defect inside the notebook that diagnoses #218.* |
| Plugin cache | Auto-propagates from the GitHub marketplace source. **There is no `autoUpdate` key in marketplace.json** — that is Claude Code's install-side default, not a repo-declared flag (D19 correction). Refresh with `claude plugin marketplace update`; `claude plugin update <plugin>` can report "Plugin not found" (E051) |
| Dependencies | Actions SHA-pinned (checkout/setup-python/setup-node) · google-genai 2.11.0 · pydantic 2.13.4 / pydantic-core 2.46.4 **lockstep — never bump independently** (D25) |
| Open backlog | **18 open** (16 + #230/#231 filed in E062). Reconciled 2026-07-30: local `tasks.json`, GitHub, and this row describe the same set; `sync --plan` is all-zero. Grouped by root cause, not issue number (E062): **① documented step with no gate** #226/#210/#218 — one gate, the repo's most-repeated defect · **② call-sequence untested** #224 · **③ eval untrustworthy** #228/#227 · **④ calibration, DEFERRED** #198/#200/#199-remainder · **⑤ not schedulable until re-derived** #217 (3-of-4 wrong), #230 (`tasks.json` gitignored vs D34) · **⑥ own plan each** #216, #206-context-economy-half, #171, #169/#170. #231 (ultra-plan phase numbering + phantom L0-L4 taxonomy) extracted from #199. **No P0 or P1 remains open.** |
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

--- New session: 2026-07-29 — fix #189, the only P0 in the E052 audit backlog: `/research-topic`'s Claude leg sends a request shape the current model family rejects. ---

### Entry 058 — Fix #189: research-topic's Claude leg 400s on every dispatch (`thinking.budget_tokens`) [skill] [debug] [decision]
**Date:** 2026-07-29
**Environment:** Linux VM, branch `fix/research-topic-adaptive-thinking` off `main` `85ed9d9` (clean, 0/0 vs `origin/main`). personal-plugin 11.4.1, marketplace 3.3.0. Primary source for every API claim: the bundled `claude-api` skill (loaded before opening any target file, per its own TRIGGER rule).
**Status:** COMPLETE — shipped as personal-plugin 11.5.0 (PR #215, squash-merged to `main` `5cd2005`; all 22 checks green)

**Objective:** Close #189 — the only P0. The Claude research leg sends `thinking: {"type": "enabled", "budget_tokens": N}`, which is **removed** (not deprecated) across the entire current model family and returns HTTP 400 on `claude-opus-4-8` and `claude-opus-5` alike. Replace it with `thinking: {"type": "adaptive"}` + `output_config: {effort: …}` and bump the default `claude-opus-4-8` → `claude-opus-5` **in the same pass** — a model-ID bump alone does not fix it, and fixing the shape without the bump ships a knowingly-stale default.

**Root cause.** Not a typo or a drift — a *whole parameter family* was removed from the API surface between when this skill was written and now, and nothing in this repo could have noticed. The skill's request body lives in a markdown reference file consumed by a subagent at runtime; there is no test, no schema, and no CI gate that ever renders it, let alone sends it. The `research-models.md` default table even carries a `Last Verified | 2026-07-08` column — a **self-reported** freshness claim with no mechanism behind it. That is the E043 class one layer out: not a guard that cannot fail, but a *freshness annotation* that asserts verification nobody performed. It is why a P0 sat undetected until a read-only audit went looking.

**Blast radius (5 files, 9 sites).** All are prose/markdown that a runtime subagent copies verbatim, which is exactly why they must move together — a half-fix leaves a subagent reading a corrected SKILL.md and then a broken curl body out of `research-provider-protocols.md`:

| File | Sites | What is wrong |
|---|---|---|
| `skills/research-topic/SKILL.md` | `:35`, `:153` | `claude-opus-4-8` default (env-var doc + resolve step) |
| | `:190-196`, `:219`, `:238` | depth ladder + Provider Deltas both name `thinking.budget_tokens` |
| `references/research-provider-protocols.md` | `:13`, `:27-29` | the copy-pasteable curl body carrying the rejected block |
| `references/research-models.md` | `:19`, `:33`, `:64` | `claude-opus-4-8` in 3 tables |
| | `:48-53` | `budget_tokens` depth column |
| `references/api-key-setup.md` | `:36` | `.env` example |

**Hypothesis:** After the change, a live `POST /v1/messages` carrying the new body against `claude-opus-5` returns **HTTP 200**, and the *old* body against the same model returns **HTTP 400** naming `thinking.budget_tokens` — the negative control that proves the fix addresses the real defect rather than a theory about it (E043's negative-test rule applied to an API contract instead of a CI guard). Secondary: no `budget_tokens` string survives anywhere under `plugins/`.

**Rollback Plan:** Single-commit revert. Every change is to markdown consumed at runtime — no schema, no on-disk format, no user data, no Python. `git revert <sha>` restores the previous (broken) shape exactly. Nothing to migrate in either direction.

**Decision — depth ladder is `low`/`medium`/`high`, not `medium`/`high`/`xhigh` (user-approved).** `budget_tokens` was a thinking-token ceiling; `effort` governs thinking depth *and* overall token spend, so there is no 1:1 mapping and the ladder had to be re-derived rather than translated. The binding constraint is that **this leg is a single non-streaming `curl`**: Anthropic's migration guidance requires `max_tokens ≥ 64000` at `xhigh`/`max` (below that it truncates mid-thought), and 64K output tokens at ~60 tok/s is ~18 minutes — past any defensible `curl --max-time`, and past the ~10-minute point where idle HTTP connections drop. So the top of the ladder is capped by the transport, not by taste.

| Depth | `effort` | `max_tokens` | Est. wall-clock @ ~60 tok/s |
|---|---|---|---|
| brief | `low` | 8,000 | ~2 min |
| standard | `medium` | 16,000 | ~4.5 min |
| comprehensive | `high` | 32,000 | ~9 min (inside the raised 900s cap) |

*Alternatives considered:* **`medium`/`high`/`xhigh`** — rejected, `xhigh` under 64K `max_tokens` is explicitly against Anthropic's own guidance, so the top tier would ship knowingly-marginal; raising to 64K instead blows the transport budget. **Rewrite the leg to stream (`"stream": true` + SSE accumulation in bash)** — rejected as out of scope for a P0 crash fix and because it means shipping unverified SSE-parsing bash into the one code path that is currently broken; filed as a follow-up instead. `high` is Anthropic's documented *minimum* for intelligence-sensitive work, so the capped ladder still lands the comprehensive tier on a defensible floor rather than a compromise.

**Second defect found while fixing the first — Opus 5 can refuse with HTTP 200.** Opus 5 ships elevated cybersecurity safeguards: a declined request returns a **successful 200** with `stop_reason: "refusal"` and an empty (pre-output) or partial (mid-stream) `content` array — no `error` body, no 4xx. The existing fast-fail checks exactly three things (`curl` exit, `http_code >= 400`, an `error` key), so a refusal passes every one of them and the leg writes a **silently empty research report** that then flows into synthesis as if it were a finding. Migrating to Opus 5 *introduces* this path, so handling it is part of the fix, not a nice-to-have — shipping the model bump without it would trade a loud 400 for a silent empty section.

**Deliberately NOT done (recorded so the omissions read as decisions):**
- **`thinking.display`** left at its `"omitted"` default. The parse step discards thinking blocks entirely, so `"summarized"` would bill the same and be thrown away.
- **`fallbacks`** not adopted, despite the `claude-api` skill's opt-in-by-default advice. It is a beta parameter + beta header pair on the one code path this entry exists to un-break; a wrong spelling reintroduces the exact 400 being fixed. Revisit once the leg has a live regression probe.
- **The three secondary findings on #189** (Claude leg is parametric-only while the other two legs are web-connected; the literal `context: fork` line inside the prompt *text*; stale-suspect OpenAI/Gemini defaults) are separate work — see the follow-ups below.

**The new guard was negative-tested before being trusted (E043 rule), and the extraction was derived, not retyped.** The refusal check was pulled *out of the shipped protocol file by regex* and exercised against crafted response bodies — retyping it into a test would have tested my transcription rather than the file that ships, which is the #212 failure mode exactly:

| Response body | Guard verdict |
|---|---|
| `stop_reason: end_turn` + text | passes (correct) |
| `stop_reason: refusal`, empty content | **caught** — `category=cyber` |
| `stop_reason: refusal`, partial content, `category: null` | **caught** — no crash on the null |
| `error` body | caught |
| `stop_reason: max_tokens` | passes (correct — truncated content is still real) |
| non-JSON / JSON array | caught as unparseable |

**Mutation test:** deleting the refusal branch made both refusal rows go from *caught* to `<empty>` — i.e. silently passing the fast-fail and writing an empty report. The branch is load-bearing and demonstrably *can* fail, so it is not an E043 guard-that-cannot-fire.

**A third defect, surfaced by the guard test rather than by reading:** `stop_reason: "max_tokens"` correctly passes the fast-fail (a truncated report is still useful, and failing the whole leg would be worse), but nothing marked the result as partial — so synthesis would read a cut-off section as a complete one. Newly plausible *because of this change*: the brief tier's ceiling is now 8,000 tokens. The parse step now appends a truncation note instead of failing. This is the same silent-degradation family as the refusal path — worth noting that **testing the guard found a defect that reading the guard had not.**

**Live probe — PASSED, all six calls.** The probe (`probe_189.sh`) is deliberately built so it cannot pass while the shipped files are broken: it **regex-extracts the `-d` body out of `research-provider-protocols.md` and the depth ladder out of `research-models.md`**, then substitutes and sends. Its first dry run caught a flaw in *itself* — it displayed an extracted ladder while sending a hardcoded one, and the extraction was also matching the Cost Estimates table, whose rows carry the identical Brief/Standard/Comprehensive labels. Both fixed; the sends are now driven by the extracted ladder with assertions on every parsed value.

| # | Request | Expected | Observed |
|---|---|---|---|
| A1 | OLD `budget_tokens` body vs `claude-opus-5` | 400 | **400** |
| A2 | OLD `budget_tokens` body vs `claude-opus-4-8` | 400 | **400** |
| B1 | Shipped body, `effort=low`, `max_tokens=8000` | 200 | **200** `end_turn` |
| B2 | Shipped body, `effort=medium`, `max_tokens=16000` | 200 | **200** `end_turn` |
| B3 | Shipped body, `effort=high`, `max_tokens=32000` | 200 | **200** `end_turn` |
| C | Bare `claude-opus-5` call | 200 | **200** `end_turn` |

**The API's own 400 text names the fix**, which is about as unambiguous as a negative control gets:

> `"thinking.type.enabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort"`

**A2 is the row that matters most.** The identical 400 on `claude-opus-4-8` — the *previous* default — proves the leg was already broken before any model migration and that **a model-ID bump alone would not have fixed it**, which was #189's central claim and the reason the issue insisted both changes ship together. Had the fix been split, the model bump would have merged looking reasonable and left the leg just as dead.

**Credential detour worth recording (cost ~20 min).** `bws secret list` failed `400 invalid_client` and the obvious readings were both wrong: not a revoked token (it is well-formed, `0.<uuid>.<secret>:<key>`, 94 chars) and not a region mismatch (US *and* EU identity endpoints both rejected it). Root cause: `~/.config/claude-env.sh` holds the **current** token for machine account `f283b1a6…`, but the tool shell had inherited a **stale** one for the retired `da8557b9…` account. `~/.bashrc:167` loads the file behind `case $- in *i*)` — interactive shells only — so a non-interactive tool shell never overwrites the inherited value. The two `~/.config/bws/state/` files (one per machine account, timestamped Jul 16 and Jul 28) are what made the mismatch visible. **Fix for any bundled skill that needs a secret: `eval "$(grep -m1 '^export BWS_ACCESS_TOKEN=' ~/.config/claude-env.sh)"` before calling `bws`, rather than trusting the inherited env var.** Worth pushing into `/unlock`.

**Secret-hygiene incident, recorded rather than quietly fixed.** `bws secret list` prints every secret's plaintext `value`, so running it to *check whether auth worked* dumped the live `ANTHROPIC_API_KEY` into the session transcript. The targeted form (`bws secret get <id>`, or piping straight into a variable without echoing) avoids this. Key flagged to the owner for rotation. The general rule: **never use a list-everything command as an auth probe** — `bws secret list >/dev/null; echo $?` answers the same question and reveals nothing.

**Backlog state reconciled in the same session (`/task-sync`, run from the REPO source, not the 11.3.0 cache).** The installed cache still lags at 11.3.0, which carries *both* task-sync defects — #212 would have crashed `sync --apply` on every push, and #208 would have stripped `priority/P0` from **#189 itself**, the very issue being fixed. Running the cached tool here would have destroyed the label this session depends on. `sync --plan` (read-only) came back all zeros, and `tasks.json` was backed up first because it is gitignored and therefore **not** git-recoverable.

**An open action item turned out to already be closed.** The standing note "the local `tasks.json` record for #189 holds a stale `priority: null`" is **no longer true** — E057's live `sync --apply` healed it as a side effect. Rather than spot-checking #189, the check was derived across all 49 tracked tasks (local `priority` vs the remote `priority/*` label): **zero drift**, and #189 reads `priority: P0` locally against `["bug","priority/P0"]` remote. The detector was then negative-tested by injecting the exact predicted defect (`priority: null` on #189) and confirming it flagged it — otherwise "zero drift" is indistinguishable from a broken comparison, which is the E043 pattern in miniature.

**Result:** COMPLETE. #189's request-shape defect, the refusal-path defect it exposed, and the truncation-marking gap the guard test exposed are all fixed across 5 files / 10 sites; live-verified on 6 API calls with a passing negative control on both model IDs. markdownlint, `scripts/pre-commit` (staged), `claude plugin validate --strict`, `update-readme.py --check`, `check_eval_mapping.py` (48 evals / 63 surfaces), and `validate_schema_data.py` all green.

**Follow-ups:**
- **#216** — stream the Claude leg to unlock `xhigh`/`max` depth (needs `"stream": true` + SSE accumulation; the current ladder is capped by the non-streaming transport, not by preference).
- **#217** — `/unlock` and the `~/.claude/scripts/*` helpers should source `~/.config/claude-env.sh` rather than trust the inherited `BWS_ACCESS_TOKEN` (D53); the stale-inherited-token failure recurs in every non-interactive tool shell. Also covers the `bws secret list` plaintext-leak hygiene fix.
- **#218** — the `Last Verified` column in `research-models.md` is a self-reported claim with no mechanism; it read `2026-07-08` while the value it annotated had been returning 400 for the entire current model family. Either wire a check behind it or delete it; an unbacked freshness stamp is the E043 class applied to documentation. (Note CI has zero secrets per ADR-0009/D32, so a live probe cannot run there.)
- **#197 overlap:** `api-key-setup.md:19` ("Claude Extended Thinking" → "adaptive thinking") was fixed here because leaving it made the file self-contradictory three lines from an edit already being made. #197 keeps its remaining bullets. The slide-gen `budget_tokens=4096` / `temperature=1.0` docs found while grepping are already covered by #197 — checked before filing, no duplicate created.

**Version:** 11.4.1 → **11.5.0** (minor: the request shape and the default model both change; a pure crash fix would have been patch, per E057's precedent).

**Backlog reconciled post-merge.** A second `sync --plan` after the merge showed **4 pulls, 0 creates, 0 pushes, 0 conflicts** — #189 transitioning to `done` plus the three new follow-ups adopted. Applied (nothing left the machine, so the public-repo push guardrail did not engage). Final state: **52 tasks / 27 open**, a follow-up plan of all zeros, priority drift re-verified at **0 across all 52**, and #189 still carrying `priority/P0` on the tracker after a full closed-state round-trip — an incidental end-to-end re-confirmation of the #208 fix under the exact condition that used to destroy the label.

**Duration:** ~1 session (load claude-api → map blast radius → fix → negative-test the guard → credential detour → live probe → ship → reconcile backlog).

--- New session: 2026-07-29 — `/ultra-plan` over the 24-item open backlog; two live crashes found during Phase 1 investigation and pulled out for immediate fix ahead of the plan. ---

### Entry 059 — Two shipped components crash on every invocation (live `` !`cmd` `` injections) [skill] [command] [debug]
**Date:** 2026-07-29
**Environment:** Linux VM, branch `fix/live-injection-crashes` off `main` `6e5d689`. personal-plugin 11.5.0. Claude Code 2.1.220. Found by an Explore agent during `/ultra-plan` Phase 1; scope pulled forward by user direction ("pull them out").
**Status:** COMPLETE — shipped as personal-plugin 11.5.1

**Objective:** Fix two components that fail on **every** invocation in **every** directory, neither of which is filed as a crash: `/new-skill` (`commands/new-skill.md:308,316`) and `/leak-risk-audit` (`skills/leak-risk-audit/SKILL.md:57`). Also fix `references/templates/skill.md:40`, which seeds the same defect into every skill `/new-skill` scaffolds.

**How this was missed for so long — the escaping rule is inverted.** An Explore agent decompiled the harness's injection extractor (`Cfo`) and its pre-pass (`Jds`) out of the 2.1.220 binary. `Jds` blanks every inline-code span **unless the character immediately before the opening backtick is `` ` `` or `!`**. The consequence is exactly backwards from intuition:

| Form | Looks like | Reality |
|---|---|---|
| `` `` !`cmd` `` `` (double-backtick, space before `!`) | correctly-escaped documentation | **LIVE — executes** |
| `` `!`cmd`` `` (single-backtick, backtick before `!`) | sloppy nesting | **INERT** |

So the *tidier* form is the dangerous one. Every author who "properly escaped" their example created a live shell execution; every author who nested backticks sloppily created dead text. This is why `prime` (7 sites) and `explain-project` (2) — the two largest blocks cited in **#183** — are completely inert, while a generator and an audit skill nobody suspected were crashing.

**Independently verified, not taken on trust** (E039). I replayed `Jds` + the extractor regex in Python against all 74 textual `` !` `` occurrences under `plugins/`: `prime` 7→**0 live**, `explain-project` 2→**0 live**, `arch-review` 1→**0 live**, versus `ship` 6→**6**, `clear-prep` 3→**3**, `leak-risk-audit` 2→**2**, `new-skill` 3→**3**. Counts match the agent's Node replay exactly.

**Two independent crash causes, both empirically measured:**

| Site | Injected command | Exit | Fails where |
|---|---|---|---|
| `commands/new-skill.md:308` | `cmd` (a literal placeholder, not a real binary) | **127** | **every directory** |
| `commands/new-skill.md:308` | `git status -s` | 128 | non-git only |
| `commands/new-skill.md:316` | `cmd` | **127** | **every directory** |
| `skills/leak-risk-audit/SKILL.md:57` | `ls -la <dataset-path>` | **2** (bash syntax error — `<`/`>` are redirects) | **every directory** |
| `skills/leak-risk-audit/SKILL.md:58` | `find <dataset-path> … \| head -100` | 0 | pipe masks the failure |

A non-zero exit does **not** degrade to empty output — the decompiled handler `throw`s, `Promise.all` rejects, prompt expansion fails, and the skill never reaches the model. `/new-skill` additionally grants no `Bash` at all (`allowed-tools: Read, Write, Edit, Glob, Grep`), so the permission gate would reject the injection even if the command existed: two independent reasons it cannot work.

**The two defects are different in kind, and need different fixes:**
1. **`new-skill.md` + `templates/skill.md` are documentation** *about* the injection syntax that accidentally executes it. Fix: switch to the inert form. The examples must still *teach* the syntax legibly.
2. **`leak-risk-audit` intends a real injection that can never work.** `<dataset-path>` is substituted from `$ARGUMENTS` at runtime, but injections expand at **parse time, before arguments exist**, so the literal placeholder always reaches bash. `skills/arch-review/SKILL.md:44` already documents this exact failure — *"that runs at command parse time, before `TARGET_PATH` has been parsed from `$ARGUMENTS`, so the placeholder reaches bash unsubstituted. Always invoke the Bash tool from the model with the resolved path."* Fix: delete the injection framing, per that precedent. A guard would be wrong — there is nothing to guard, the design is impossible.

**Hypothesis:** After the fix, replaying the extractor reports **0 live injections** in all three files, while the documentation still displays the syntax. `ship` (6) and `clear-prep` (3) remain live and unchanged — they are genuine git injections whose non-git guarding belongs to #183/#190 and is deliberately **out of scope here**. Success criteria: live count 3→0 for `new-skill.md`, 2→0 for `leak-risk-audit`, 2→0 for `templates/skill.md`; `ship`/`clear-prep` counts unchanged at 6/3; the replay harness negative-tests green (reintroducing a live form is detected).

**Rollback Plan:** Single-commit revert. All three changes are markdown text edits with no schema, no data, and no code path. `git revert <sha>` restores the previous (crashing) state exactly.

**Deliberately out of scope, recorded so the omissions read as decisions:**
- **`ship` (6) and `clear-prep` (3)** — real git injections that abort only outside a repo. That is #183 ∩ #190, and `ship:30` is a single line owned by two issues that must be edited once, together. Fixing it here would pre-empt that atomic pair.
- **`references/{common-patterns,new-skill-examples,patterns/advanced-features}.md` and `deprecated/new-command.md`** (20 live forms) — these are Read as documentation, never expanded as a skill/command body, so nothing executes. They teach the dangerous form and belong to the generator-layer change set (CS-1), not to a crash fix.
- **`references/patterns/advanced-features.md:132`'s false "failure is silent" claim** — the root-cause doc fix, also CS-1/#183.

**Result:** COMPLETE. Live-injection counts after the fix, measured by replaying the extractor:

| File | Before | After | Note |
|---|---|---|---|
| `commands/new-skill.md` | 3 | **0** | `cmd` ×2 (exit 127) + `git status -s` |
| `references/templates/skill.md` | 2 | **0** | the propagation seed |
| `skills/leak-risk-audit/SKILL.md` | 2 | **0** | injection framing deleted, not guarded |
| `skills/ship/SKILL.md` | 6 | **6** | unchanged — #183 ∩ #190, deliberately out of scope |
| `skills/clear-prep/SKILL.md` | 3 | **3** | unchanged — #183 |

**The checker was negative-tested before its zeros were trusted** (E043). Two one-line fixtures were run through the same replay: the nested form `` `!`cmd`` `` reports **LIVE=0**, the escaped-looking form `` `` !`cmd` `` `` reports **LIVE=1**. Without that, "0 live" is indistinguishable from a broken extractor — which matters more than usual here, because the whole finding rests on a subtlety of the pre-pass.

**Fix shapes differ by defect, deliberately.** The two documentation sites switched to the inert nested form and gained a gotcha naming the inversion, because the examples still have to *teach* the syntax. `leak-risk-audit` had its injection framing **deleted** rather than guarded — a guard would be the wrong fix, since `<dataset-path>` can never be substituted at parse time and there is nothing to guard against. That follows `arch-review/SKILL.md:44`, which had already documented this exact failure for its own `TARGET_PATH`; the knowledge existed in the repo and simply hadn't propagated.

**System insight — the safe-looking form is the dangerous one.** Every other injection defect in this repo's history was an author forgetting a guard. This one is the opposite: authors who *correctly* escaped their documentation examples, by the ordinary markdown convention for showing literal backticks, thereby created live shell executions; the authors who nested backticks sloppily created dead text. Intuition points exactly the wrong way, which is why two shipped components crashed on every invocation without anyone noticing, and why the two largest blocks cited in #183 (`prime`, `explain-project`) turn out to execute nothing at all. **Any future injection linter must replay the pre-pass rather than grep** — a textual search for `` !` `` finds 74 sites under `plugins/`, of which only 14 are live in an executable surface.

**Scope note recorded for #183.** Its location table should be rewritten: drop `prime` (7 inert) and `explain-project` (2 inert), add `commands/new-skill.md` and correct the `leak-risk-audit` framing from "non-git" to "every directory". The mechanism half of #183 — including its critique of `advanced-features.md:132` — is verified correct and still stands.

**Root CHANGELOG gap closed in passing.** 11.5.0 was missing from the root `CHANGELOG.md` — drift introduced by my own PR #215 earlier today, and one of the two reverse-drift cases the #210 investigation surfaced. Added alongside 11.5.1 rather than left for #210, since this PR was editing that file anyway and leaving a known self-inflicted gap would be worse than the small scope bleed.

**Version:** 11.5.0 → **11.5.1** (patch: crash fix, no capability change — E057 precedent).

**Duration:** ~30 min (verify the agent's decompilation independently → fix → negative-test → ship).

### Entry 060 — `/ultra-plan` over the 24-item backlog: 11 parallel investigators, 22 of 24 issues corrected [plan] [decision]
**Date:** 2026-07-29
**Environment:** Linux VM, branch `plan/v12-correctness-backlog` off `main` `264f082`. personal-plugin 11.5.1, marketplace 3.3.0. Claude Code 2.1.220.
**Status:** COMPLETE — `IMPLEMENTATION_PLAN.md` generated (8 phases / 42 items); prior plan archived as v11

**Objective:** Run the full `/ultra-plan` workflow over the open backlog and produce a formal implementation plan. User scoped it to 24 of 27 open items, excluding the three deliberately-deferred task-sync v2 scope-outs (#169/#170/#171).

**Method:** Phase 0 constitution check against CLAUDE.md + 10 ADRs + 53 decisions (no gaps, no questions needed). Phase 1 dispatched **11 read-only Explore agents**, clustered 2-3 items each by shared code path so same-root-cause duplicates surfaced *within* a cluster. Every brief carried the same rubric plus this repo's own doctrine (D-numbers, ADRs, E043/E040) as the lens — the E052 lesson that grounding subagents in local doctrine makes them find contradictions between the repo's rules and its files rather than generic style nits.

**Headline result: 22 of 24 issues required correction.** Only #194 and #204 were accurate as filed. That is far above E040's 4-in-6 base rate, and two agents independently explained why: issues derived from *reading tool source* held up; issues derived from *reading docs* did not.

**Six findings that changed the plan's shape:**

| # | Finding | Consequence |
|---|---|---|
| 1 | The injection escaping rule is **inverted** — the tidy `` `` !`cmd` `` `` form is LIVE, the sloppy nested form is INERT | #183's two largest cited blocks (`prime` 7, `explain-project` 2) execute nothing; two unfiled components were crashing (fixed as 11.5.1, E059) |
| 2 | **#202 as filed would delete working features** — 6 of 8 "unverified" frontmatter keys are real; the defect is correct keys with wrong *semantics* | Remedy inverted. `/schedule` is real and shipping; the issue's proposed replacement `create_trigger` appears **zero** times in the harness |
| 3 | **#204 is green on day one** (13/13 agents already compliant) and the real hazard is scope creep reddening `main` | Reverses E053's recorded order (**D55**) |
| 4 | **Both** `build-cfa-deck` slide-removal implementations fail on the installed python-pptx — including the one labelled "reliable" | #195 is a functional blocker, not a docs nit |
| 5 | task-sync's `UNCHANGED` orphan is **100% invisible** in every plan section — the common case, unfiled | #181's blast radius understated |
| 6 | **#217, which I filed hours earlier, is 3-of-4 wrong** — and `/unlock` is blocked by an unrelated `$TROY` defect, so the filed fix would not make it work | Issue must be rewritten before it is actionable |

**Methodological notes worth keeping.** One agent settled #202 offline by **grepping the installed Claude Code binary for the literal zod frontmatter schemas** — converting "needs a live harness probe" into a decidable question, and discovering the skill schema is `.strict()` (unknown keys are *rejected*, not ignored). Another **decompiled the injection extractor and its pre-pass**, then replayed them against every `.md` under `plugins/`; I reproduced its counts independently in Python before building the plan on them (E039 — treat subagent output as a lead, not a conclusion). A third proved #218 from **git history**: commit `1f55dcd` bumped two `Last Verified` dates while the Default Value cells were byte-identical — the column was find-replaced during a docs sweep, never verified.

**Phase 2 structural insight.** Six issues (#183, #192, #197, #199, #201, #202) all land on the **same five generator files**, which propagate every defect into every future skill. That is not one item among 24 — it is the upstream of a quarter of them, and the plan treats it as a single atomic change set (Phase 5) rather than six colliding PRs. One line, `ship/SKILL.md:30`, is owned by two issues and must be edited once to satisfy both (#183 needs it exit-0-safe, #190 needs it numeric).

**Self-correction during planning, recorded because it matters.** My first proposed split put the generator layer and doctrine work in the near-term plan and deferred #193 (silent layout corruption), #195 (both impls broken), and #181 (silent remote clobber) to a follow-on. That is the wrong ordering — a plan should not defer active harm behind multipliers — and I revised it before generating (**D54**). Phases 2-4 now front-load everything producing wrong output today, and are independent of the critical path so they can run in parallel with it.

**Plan generated:** 8 phases / 42 work items / ~70 files, within the template's 8×6 caps. Two new ADRs are Phase deliverables: **ADR-0011** (dynamic-injection doctrine — parse-time expansion, non-zero exit aborts, the inverted escaping rule, and the rule that linters must *replay the pre-pass, not grep*) and **ADR-0012** (documentation of a bundled artifact must be derived from the artifact — the shared root cause of #193, #194, #196, #202, #218). Structural verification: 8 phases, 42 items, 0 missing required fields, 8 Definition-of-Done blocks, all 16 in-scope issues in the traceability appendix, all 8 deferred issues named.

**markdownlint caught three documented traps at commit time, again.** MD018 on two lines opening with `#183` / `#202` at column 1 (the exact trap CLAUDE.md records), MD056 on a table row split by unescaped pipes inside a shell command, and MD049 on the closing italic. Fourth consecutive session in which the standing "lint before you COMMIT" rule has earned its place.

**What worked:** clustering by shared code path rather than by priority label — it let agents catch cross-issue collisions (`ship:30`, `prime:5`, `new-skill.md:293`) that a per-issue investigation would have missed entirely, and it surfaced three unfiled defects. Asking the scoping question *before* dispatching, rather than investigating 27 items and discovering 3 were out of bounds.

**Duration:** ~1 session (Phase 0 → 11-agent fan-out → interaction mapping → design → plan generation).

--- New session: 2026-07-28 — execute the E060 plan via `/implement-plan`: 8 phases / 42 items off `main` `88d8600`. ---

### Entry 061 — Executing the 16-issue correctness backlog (8 phases / 42 items) [plan] [build] [ci]

**Date:** 2026-07-28 → 2026-07-30
**Environment:** Linux VM, branch `feature/correctness-backlog` off `main` `88d8600` (verified 0/0 divergence from `origin/main` per D17). Started at personal-plugin 11.5.1 / marketplace 3.3.0; ended at **11.6.0 / 4.4.0 / 1.3.0**. Orchestrator on Opus 5 (1M).
**Status:** COMPLETE — 42/42 items, merged `1382a8a` (#222); release `49face4` (#225); eval results `7d5ae1f` (#229)
**Duration:** 3 sessions (one lost to a terminal crash mid-Phase-7)

**Objective:** Execute `IMPLEMENTATION_PLAN.md` (generated in E060) end-to-end with `/implement-plan` in default mode — PR at the end, no auto-merge, no phase pauses. All 42 items across 8 phases start `PENDING`.

**Hypothesis:** The orchestrated loop lands all 42 items with per-phase Definition-of-Done gates green, producing one PR. Measurable success criteria: (a) every item's `**Status:**` reaches `COMPLETE`; (b) each phase's DoD block exits 0 before the phase boundary is crossed; (c) the two gates this plan *creates* — `scripts/check_injections.py` (1.6) and `scripts/check_agent_models.py` (6.1) — each pass a `--self-test` that proves they exit 1 on deliberately-bad input, per the standing negative-test rule; (d) `main` is never red, since all work lands on the feature branch behind one PR.

**Rollback Plan:** Every batch is its own commit on `feature/correctness-backlog`, and `last_good_sha` in `.implement-plan-state.json` tracks the most recent all-gates-green commit. A failed item is never committed — `git checkout -- .` returns the tree to `last_good_sha`. Whole-run abort: `git checkout main && git branch -D feature/correctness-backlog` discards everything; `main` is untouched until the PR merges. `IMPLEMENTATION_PLAN.md` itself is git-tracked, so its Status-field edits revert with the branch.

**Execution shape (from the plan scan).** Critical path is **1 → 5 → 7 → 8**, strictly sequential. Phases 2, 3, 4 share zero files with it and with each other. Per-item model tiers are fully specified (42/42), so dispatch never falls back to the phase default. Phase overrides: 1, 4, 5 on `opus`.

**Two file-overlap hazards the scan caught that `Depends On` alone would have missed** — both would have produced concurrent writes to one file:

| Items | Shared file | Why `Depends On` missed it |
|---|---|---|
| 1.2 + 1.3 | `skills/ship/SKILL.md` | Both declare `Depends On: None`; they touch different concerns (git-injection guards vs the `--audit` tool grant) in the same file |
| 3.2 + 3.3 + 3.4 | `slide-gen/skills/build-cfa-deck/SKILL.md` | 3.4 declares no dependency but lands in the same file as its two predecessors |

Both are forced sequential in `parallelization_map`. Three further cross-phase overlaps are recorded there as ordering constraints (6.1/6.2 vs 1.6 on `validate.yml` + `scripts/pre-commit`; 7.2/8.1 vs 5.1/5.5 on `spark-recon`; 7.5/8.2 vs 2.4 on `visual-explainer`) — these are why the critical path forbids inter-phase parallelism rather than merely discouraging it.

**Note on the Phase 1 and Phase 6 DoD blocks.** Both cite a linter that does not exist yet at phase start (`check_injections.py` is item 1.6's deliverable; `check_agent_models.py` is 6.1's). The gate is therefore only runnable at the *end* of its own phase — a self-referential DoD. Recorded here so a later reader does not mistake an early skip for an unrun check.

**Results — per batch, logged as each lands:**

| Batch | Items | Tier | Commit | Gates | Outcome |
|---|---|---|---|---|---|
| 1 | 1.1 | opus | `71a6ad4` | validate ✔ mdlint ✔ pre-commit ✔ | ADR-0011 Accepted. Doctrine re-derived from the shipped harness, not from E059's summary |
| 2 | 1.2, 1.4, 1.5 | opus, haiku, haiku | `bcc1c52` | validate ✔ mdlint ✔ pre-commit ✔ | 5 ship guards + 3 clear-prep guards live; #183 corrected on GitHub |
| 3 | 1.3 | haiku | `ca8e6e4` | validate ✔ mdlint ✔ pre-commit ✔ | `ship` grant set derived from the body, not the item title |
| 4 | 1.6 | sonnet | *(this commit)* | linter ✔ self-test ✔ validate ✔ mdlint ✔ pre-commit ✔ | **Phase 1 COMPLETE (6/6)** — linter live, 63 files / 35 live injections, all guarded and granted |

**Batch 1 finding — E059 undercounted the live forms.** The 1.1 implementer recovered the harness matchers verbatim from 2.1.220 and found a **fifth** live form E059 never enumerated: a `!`-info-string fenced block matched against the **raw** text, so it is never pre-passed at all. That form cannot be found by grep under any pattern, which is the sharpest available justification for ADR-0011's rule that a linter must replay the pre-pass. Item 1.6 inherits it as a required case.

**Batch 1 flag carried forward.** `IMPLEMENTATION_PLAN.md`'s own executive summary contains 2 live inline forms. They sit outside `plugins/`, so 1.1 correctly left them; item **1.6 needs an explicit scope policy for repo-root docs** or its first run reddens on the plan file itself.

**Batch 2 — the dual-owned line, resolved and independently verified.** `ship/SKILL.md:33` is owned by two issues with opposing pulls: #183 needs it exit-0-safe, #190 needs it numeric. The naive fix for #183 — appending a `|| echo "(sentinel)"` guard — would have regressed #190 straight back to a string comparison. The landed form instead makes the pipeline's exit status `awk`'s, which swallows `git`'s 128 and `grep`'s no-match 1 **without** a sentinel, while `print s+0` coerces the empty accumulator to a bare integer:

```sh
git diff HEAD --shortstat 2>/dev/null | grep -oE '[0-9]+ (insertions?|deletions?)' | awk '{s+=$1} END {print s+0}'
```

I re-ran this myself rather than accepting the agent's report (E039). In a scratch non-git directory all five guarded commands exit 0 with the sentinel, and the diff-size line exits 0 yielding `0`; in the real repo with 3 files staged it yields `79`, matching `47 insertions + 32 deletions` from the raw shortstat, and `[ "$v" -gt 500 ]` evaluates without error. Both owners satisfied by one expression.

**Latent defect found while repairing the pre-flight gate (unfiled, fixed in passing).** The dead gate was split into a sentinel-based repository check plus a **new empty-remote check** — because a repo with no remote previously fell through to `PLATFORM=gitea`. That is a wrong-platform dispatch on a condition nobody had filed.

**A guard-design detail worth keeping.** The repository check carries an explicit *do not infer this from empty output* instruction, because empty is a legitimate result for several of these commands inside a perfectly valid repo. Sentinel-vs-empty is the distinction that makes the check correct; conflating them would reintroduce a false abort.

**Batch 3 — deriving a grant set beats copying one.** Item 1.3's own title names five tools (`Write`/`mkdir`/`tail`/`awk`/`grep`), but the implementer read the skill body and granted only four: batch 2's rewrite of line 33 had removed the sole `tail` invocation. Granting `tail` would have restated the issue text rather than the artifact — precisely the drift class CLAUDE.md warns about, and a live demonstration that the rule bites on *grants*, not just on tests. Confirmed independently: `tail` appears nowhere in the body, and the item's whole diff is one frontmatter line, leaving batch 2's dual-owned expression byte-identical.

**Batch 4 — the injection linter, and how it was proven rather than asserted.** `scripts/check_injections.py` ports the harness's pre-pass and extractor **verbatim** (including the raw-text `!`-fence form, and a manual preceding-character test standing in for the variable-width lookbehind Python will not compile). Its `--self-test` parses ADR-0011's own LIVE/INERT table **at runtime** to derive its nine expected verdicts, rather than hard-coding a copy — the direct application of the "parametrize from the constant, never a copy of it" rule, and the thing that keeps the fixture set from drifting away from the ADR the way `test_priority_round_trip` drifted from `VALID_PRIORITIES` in E056.

I did not take the green self-test as proof the gate works. I planted a real `SKILL.md` in the actual repo tree carrying an unguarded, ungranted injection; the linter exited **1** naming both violations separately (`unguarded` per F3, `ungranted` per F4), and returned to **0** once removed. A gate that has never been observed failing is indistinguishable from a gate that cannot fail.

**Scope decision (linter): stop at the loader boundary, not the text-match boundary.** Scanning is restricted to `plugins/*/skills/*/SKILL.md` and `plugins/*/commands/*.md`. Repo-root prose — including the 2 live-looking sites in this plan's own executive summary that batch 1 flagged — plus `references/**` and `deprecated/**` are excluded, on the same "never expanded by the loader" reasoning ADR-0011 already applies. The rationale is worth preserving: widening the file glob to catch text that the loader never expands would reproduce the rejected grep-gate failure mode at the *file-selection* layer instead of the regex layer. The flag batch 1 raised is therefore resolved by scope, not by editing the plan file.

**CI wiring honors D28.** The check landed as a step inside the existing `plugin-validate` job, and `scripts/pre-commit` gained a staged-file-gated Check 4 matching Checks 1-3. Verified against `origin/main`: zero new job keys, so no new required status check and no branch-protection coordination needed.

**Two risk rows deliberately left `Open`.** The "new CI job instead of a step deadlocks merges" row is scoped jointly to `1.6, 6.1`; 6.1 has not run, so marking it Mitigated now would misreport it as retired. The `prime` backtick-tidying row is scoped to 7.3. Both stay Open by design — a half-satisfied mitigation marked green is worse than one marked red, because Phase 6 and Phase 7 implementers read these rows as instructions.

**One defect I fixed directly.** The linter shipped with a stale annotation — `cases` declared a 6-tuple while every entry, and its own explanatory comment, was a 7-tuple. Runtime was unaffected (hence a green self-test) and `scripts/` is outside CI's ruff/mypy scope, so nothing would have caught it. Corrected to `tuple[str, str, str, str, str, bool, str | None]`. Noted because it is the *third* thing this session that a passing check did not cover.

**Phase 1 verdict:** 6/6 items COMPLETE. Final linter run: 63 files scanned, 35 live injections, all guarded and granted, exit 0.

---

**Phase 2 — two defects in the PLAN's own Definition of Done, found by running it.**

The DoD is executable text, and executing it is how both surfaced. Neither is a code bug; both would have produced a misleading red or a spurious pass.

1. **`python` does not exist on this VM, and bare `python3` cannot run these suites.** Phase 2's DoD says `PYTHONPATH=src python -m pytest tests/ -q`. There is no `python` binary here, and `python3` lacks `pytest-cov`, so the tool's own `addopts` (`--cov=...`) make it abort with *unrecognized arguments*. Only `.venv/bin/python` works. This is the same trap already recorded from E051; the DoD was written without it. All per-tool DoD commands in the state file were rewritten to `.venv/bin/python`.

2. **The env-var parity check counted 5 where the truth is 15 — and the check, not the plan, was wrong.** My first pass grepped `os.getenv("LITERAL")` in `config.py`, found **5**, and briefly looked like evidence that the plan's "15-variable table" was inflated. It was not. `config.py` reads most variables through `env_str` / `env_int` / `env_float` wrappers, so the name literal is the *helper's* argument and `os.getenv`'s argument is the opaque parameter `key`. Counting properly gives **13** `VISUAL_EXPLAINER_*` in `config.py` plus `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` read elsewhere = **15**, exactly as filed.

   This is worth keeping as a near-miss. Had I trusted the naive grep, the "fix" would have been to shrink a correct 15-row table to 5 rows and delete 10 real, user-settable variables from the docs — a documentation regression dressed as a correctness fix, and precisely the failure mode E060 flagged for **#202** ("the issue as filed would delete working features"). The generalizable rule: **an indirection between the accessor and the name literal makes any accessor-shaped grep undercount.** Before concluding a documented set is inflated, check whether the reader is a wrapper.

   The corrected parity command now matches on the *name literal* rather than the accessor, and carries a comment recording why the obvious form is wrong.

---

**Phase 7 — a terminal crash mid-item, and what the recovered state did and did not tell me.**

The session died during Phase 7 with nothing committed past `d4cdc3e` (Phase 6 close-out). Recovery came from three sources that agreed only partially, and the disagreement is the useful part:

| Source | Said | True? |
|--------|------|-------|
| `.implement-plan-state.json` | `current_item: 7.1`, 32 items complete, Phase 7 contributed **nothing** | Half — the pointer was right, the completion list was stale |
| `IMPLEMENTATION_PLAN.md` (uncommitted) | 7.1 `IN_PROGRESS`, **7.2 and 7.4 `COMPLETE`** | Yes |
| `git status` | 4 modified files, matching exactly 7.2 + 7.4 + the plan | Yes |

**The state file lags the plan file, because it is written at the batch-commit boundary and the plan file is written by each item.** Everything Phase 7 had actually produced was invisible to the resume pointer. Recovering from `current_item` alone would have re-run 7.2 and 7.4 over their own output. The generalizable rule: **on resume, reconcile the state file against the plan file and the working tree — treat the state file as the *oldest* of the three, never the authority.** `last_good_sha` remains trustworthy precisely because it is a commit.

**The crash was not the expensive part — a false green in the uncommitted work was.** 7.4 (convert the two shared AskUserQuestion upstreams) had ticked its acceptance criterion *"No hand-rolled option menu remains in either shared upstream"* and recorded in its own completion notes that "no hand-rolled `Your choice (A/B/C/D/E)` prompts remain in either file". A single grep falsified both: `clarification-patterns.md:27` still carried one. It converted the 22 **question** blocks and left the file's two **normative** blocks:

1. `Question Format Template` (`:7-28`) — the block every generated question is told to imitate, and which is *duplicated* into `bpmn-generator/SKILL.md:106-123`. Converting 22 instances while leaving the template that mints instance 23 is the generator-layer failure mode this whole plan exists to fix (E060 finding 3), reproduced inside a fix for it.
2. `Auto-Accept Mode Behavior` — trigger still read "when user selects **E)**", action still read "automatically select option A". Both are dangling references to letters no question emits any more, so the feature was documented as reachable via a control that no longer exists.

This is a third instance of the standing rule that **a check restating the thing it checks will agree with the bug** — the "verification" line was prose the same agent wrote about work the same agent had just done, never a command. Structural difference from E056/E057: there the check was code that ran and was wrong; here the check was *narrative* and never ran at all. Narrative verification is not weaker evidence than a bad test — it is not evidence.

**Auto-accept preserved, not dropped.** The obvious reading of "the native Skip button and free-text box absorb every `[D] Custom` / `[S] Skip` slot" (plan, 7.4) is that `D` and `E` both vanish. `D` (provide your own) is genuinely absorbed by the free-text `Other` box; **`E` (accept recommended for all remaining) has no native equivalent** and deleting it silently would have been a capability regression — #202's exact failure mode. It is now reached by typing accept-all intent into the `Other` box, which the harness supplies on *every* question and therefore matches the old per-question availability at zero option-slot cost. Alt considered and rejected: a 4th option on Q1 only — it mixes a session-level meta-command into a content question and is unreachable after Q1.

**Re-verification after the fix (commands, not prose):** `grep -rn "Your choice\|option A\b\|\*\*E)\|\*\*D)"` across both upstreams → 0 hits; 22/22 JSON blocks parse, every question 3–4 options, every `header` ≤12 chars; `python3 scripts/check_injections.py` → exit 0 (63 files, 35 live injections); `markdownlint-cli2` → 0 issues; `claude plugin validate --strict` → passed for all three plugins. 7.1 reset `IN_PROGRESS` → `PENDING`: it had produced no edits before the crash.

---

**Phases 7 and 8 — three findings, each of which changed the shape of the fix.**

**1. Two items' declared scope was smaller than the defect.** 7.1 named 6 components carrying `Task` in `allowed-tools`; a repo-wide grep found **8**. The two extras were `research-topic` (dispatches one `context: fork` subagent per provider) and **`references/templates/synthesis.md` — a generator template**. Fixing only the named 6 would have retired `Task` from the instances while leaving the mould that stamps out new ones, which is E060 finding 3 verbatim. Same shape in 7.3: `prime`'s "pre-loaded via dynamic context injection" claim was filed as one line (`:59`) and was actually in **three** (`:26`, `:59`, `:66`). **Generalizable: verify a filed count against the tree before treating it as scope. An issue's line reference is where the reporter noticed the defect, not where it ends.**

**2. The Phase 1 injection gate fired on real, unplanted work — mine.** Drafting 7.3's explanation of why `prime`'s injections must stay inert, I described the live form by *showing* it. Showing it made it live: a `` `` !`cmd` `` `` span inside a skill body, calling a nonexistent `cmd`, which per ADR-0011 F3 aborts skill load on a non-zero exit. `check_injections.py` exited 1 naming both violations (`unguarded`, `ungranted`) at `:59`. Rewritten to *name* the form in prose rather than render it.

This is the strongest possible evidence for the gate, and it is worth being precise about why: the author of the doctrine, editing the file the doctrine is about, with the inverted-escaping rule in working memory, still wrote the trap. The rule is not hard to understand — it is hard to *apply while writing prose about it*, because prose about syntax naturally wants to display the syntax. **Any documentation of an injection form must name it, never render it.**

**3. A `: ` in an unquoted YAML description silently deletes the whole frontmatter.** 8.1's first `spark-recon` rewrite read `Report-and-recommend only: reads external sources…`. In YAML a colon-space inside a plain scalar is a mapping indicator, so the frontmatter did not parse. The failure mode is the dangerous one: not a crash, but **silent metadata loss** — `name`, `allowed-tools`, and `disable-model-invocation` all dropped at load time. On this specific file that means a **D40-protected skill quietly loses its protection flag** while continuing to load and run.

`claude plugin validate --strict` caught it and reported it precisely ("At runtime this skill loads with empty metadata (all frontmatter fields silently dropped)"). Nothing else in the toolchain would have: markdownlint passed, the injection linter passed, and the file reads correctly to a human. Swept all 63 SKILL.md/command files with `yaml.safe_load` afterward — 0 other instances, so this was self-inflicted and is now closed. **The em dash is the safe punctuation for these descriptions; the house style already used it everywhere, which is why the corpus was clean.**

**What worked.** Three gates built earlier in this same plan each caught something real in the phases that followed: `check_injections.py` (built in 1.6) caught finding 2; `claude plugin validate --strict` caught finding 3; `check_eval_mapping.py` stayed green across every eval edit in 8.3/8.4, confirming the structural contract held while the semantic content was rewritten underneath it. The negative-test discipline from E043 is what makes those green results mean anything.

**One task is deliberately not done.** 8.4 task 3 — run the 14 `description-triggers` scenarios under Opus 5 — is deferred to A21, and #205 stays open for it. Each scenario measures whether a *fresh* session auto-invokes a skill given conversational context; run from the session that just rewrote those skills, the outcome is known in advance and a pass would be an artifact of contamination rather than evidence. Marking it green would have been the cheapest possible lie and would have retired the one open question about whether Phase 8's contract actually holds in practice. It needs one clean session per scenario, human-run per ADR-0009/D32.

---

**Ultrareview on PR #222 — 5 findings, 5 confirmed, 0 false positives.**

Every finding was independently verified against the tree before any fix. None was rejected, which is itself the notable result: this is the first review pass on this branch where the *reviewer* was not the author, and it found two live defects that four phases of self-verification had certified green.

| # | Sev | Finding | Verdict |
|---|-----|---------|---------|
| bug_001 | normal | `_load_decisions` called twice on one file; a wrapped conflicts-only file returns the OUTER dict for `key="orphan_decisions"` | **Confirmed** — aborts `sync --apply` |
| bug_003 | normal | `verification-post-edit-hook.md` matcher/target mismatch; payload structurally unreachable | **Confirmed** — plus 3 stale prose lines |
| merged_bug_004 | nit | 4 generator-layer sites missed by the Phase 5/7 sweeps | **Confirmed** — all sites |
| bug_009 | nit | `cli.py --layout` help says "when present"; resolver gates on *complete* DI | **Confirmed** |
| bug_011 | pre-existing | `create-wiki` maintenance mode branches on a `paths:` the frontmatter never declared | **Confirmed** — 0 `paths:` keys in file |

**bug_001 is the one that mattered, and its shape is instructive.** `_load_decisions(path, key=...)` falls through to returning the whole top-level dict when `key` is absent — correct in the single-key world (an absent `"decisions"` key legitimately meant "this file is flat"). Phase 4 added a *second* call on the *same file* with `key="orphan_decisions"`, and the fallthrough silently changed meaning: for a wrapped conflicts-only file it hands `{"decisions": "{'t-1': 'local'}"}` to `_validate_orphan_decisions`, which is fail-loud by design (D36) and raises on the unrecognized id `'decisions'`. `sync --apply` then aborts with `orphan decision for unknown task 'decisions'` — an error message that names the wrong thing entirely.

Two of the three decisions-file shapes `sync-semantics.md` documents were broken: the backward-compat wrapped conflicts-only form, and the flat mixed form the same PR advertises at `:158-160`. Only the fully-wrapped both-keys form worked. **Fail-safe, not fail-dangerous** — it aborts before any mutation, so no data was at risk.

**Why 96% coverage did not catch it.** `test_load_decisions_variants` exercises the loader in isolation with **one key per file**; the apply-level orphan tests construct `orphan_decisions` dicts directly and hand them to `apply()`. Neither reproduces the CLI's *double call on a single file*. The defect lives entirely in the interaction between two call sites, and no unit test of either site can see it. This is the E049 lesson again in a new costume: **"both units tested" is not "the call sequence tested."** Coverage measured lines; the bug was in an ordering.

**The fix, and why the flat form needed more than a loader patch.** The loader now treats a file as *wrapped* if it carries **any** section key, in which case a missing section yields `{}`. That alone fixes the wrapped case but not the flat one: a flat mixed object still hands conflict ids to orphan validation. So `_split_flat_decisions` partitions a flat map by plan membership — and routes ids in **neither** set into the *orphan* map on purpose, because that is the only fail-loud consumer. Silently dropping an unrecognized id would convert a user's typo into a decision they believe they made. D36's fail-loud property is preserved exactly, and the flat form works.

**Negative-tested before trusting it** (E043 rule): reverted the loader to its old behavior and confirmed the new regression test goes red with `assert {'decisions': "{'t-1': 'local'}"} == {}` — the exact corruption predicted — then restored and confirmed green. 480 tests pass, coverage 96.30%.

**bug_003 is a false green in item 3.1's own acceptance criterion.** That criterion reads "WHEN a recipe is copied into `.claude/settings.json` THEN the hook SHALL register and fire". The recipe registers and validates — and never fires its payload. 3.1 copied the working `hooks.json` pattern (`matcher: "Bash"` + `jq` on `.tool_input.command`) but kept the old semantic of grepping a *tool name*, producing `matcher: "Bash"` + a test for `"Edit"` that can never be true. It also silently changed the event from `PostToolUse` to `PreToolUse`, which is wrong for a recipe whose entire purpose is *post*-edit verification, while three prose sections still described the old behavior — including a Customization tip pointing at `$CLAUDE_FILE_PATH`, the exact non-existent variable 3.1 was fixing.

Rewritten as `PostToolUse` + `matcher: "Edit|Write"`, letting the matcher do the filtering so no tool-name check is needed at all. The generalizable rule, now stated in the recipe itself: **a hook's matcher must name the tool whose fields the body inspects.** The working `hooks.json` is correct precisely because `.tool_input.command` belongs to the `Bash` tool it matched.

**What this says about the plan's self-verification.** Every phase verified its own work and every phase's gates were green. Three of these five findings are in files a phase explicitly edited, and two are inside acceptance criteria a phase marked satisfied. The gates were not wrong — they were checking structure (JSON parses, frontmatter validates, injections are guarded), and all five defects are *semantic*. **A green structural gate is evidence about structure and nothing else**; on a branch that is mostly behavior-surfaces, that leaves most of the surface unverified. An independent reader was the only thing that could have found these.

---

**Post-merge: 42 items of behavior change shipped at an unchanged version.**

PR #222 merged as `1382a8a`. Immediately after, a check that should have run *before* the merge: the plan touched all three plugins and bumped none of them. `personal-plugin` stayed `11.5.1`, `bpmn-plugin` `4.3.1`, `slide-gen` `1.2.0`.

**Two different trees now both claim `11.5.1`.** The installed cache at `~/.claude/plugins/cache/troys-plugins/personal-plugin/11.5.1/` still carries `disable-model-invocation: true` on `lab-notebook` and `create-wiki`; `main`'s `11.5.1` has the flag removed and the Phase-0 gates in its place. Same version string, materially different dispatch behavior.

**This blocked the very next task.** A21 is the run of the 14 `description-triggers` scenarios, and S13/S14 were rewritten in 8.3 to assert the *new* contract ("may be invoked, must gate before writing"). Running them against the installed plugin would have exercised pre-Phase-8 skills that still carry the flag — every S13/S14 result would have been a guaranteed failure attributable to nothing but a stale cache. Worse, the failure would have looked like a real finding about Phase 8.

**Why no gate caught it.** Version bumping is a `/bump-version` step, not a CI check: nothing compares "did `plugins/**` change?" against "did `plugin.json.version` change?". `claude plugin validate --strict` validates the manifest's *shape*, not its *currency*. `update-readme.py --check` regenerates tables from the tree and is version-blind. So every gate on PR #222 was green and correct, and the release was still unshippable — the same lesson as the ultrareview findings, one layer up: **the gates check artifacts, not the process that publishes them.**

**Fix:** minor bumps across all three (behavior changed, no API break) — `personal-plugin 11.6.0`, `bpmn-plugin 4.4.0`, `slide-gen 1.3.0` — with CHANGELOG entries grouped by root cause rather than by issue number, plus an explicit note that anyone already on `11.5.1` must update because the tree changed underneath the version.

**Follow-up worth filing:** a CI check that fails when files under `plugins/<name>/` change in a PR without `plugins/<name>/.claude-plugin/plugin.json` version changing. It is derivable from the diff (never a restated constant), it can be negative-tested trivially, and it is the exact gate whose absence let this through. Per D28 it must land as a *step* in the existing validate job, not a new job.

---

**A21 discharged — the 14 `description-triggers` scenarios run under Opus 5. 13 pass, 1 fail.**

Run against **personal-plugin 11.6.0 / bpmn-plugin 4.4.0** as actually installed, one fresh `claude -p` session per scenario in an isolated empty directory. This is the clean-session requirement A21 existed for: no scenario was run from a session that had seen the skills being tested.

| # | Scenario | Expected | Observed | |
|---|---|---|---|---|
| S1 | bpmn-generator positive | fires | `bpmn-generator`, wrote `.bpmn` | ✅ |
| S2 | bpmn-generator near-miss | → bpmn-to-drawio | `bpmn-to-drawio` | ✅ |
| S3 | bpmn-to-drawio positive | fires | `bpmn-to-drawio` | ✅ |
| S4 | bpmn-to-drawio near-miss | → **bpmn-generator** | `superpowers:brainstorming` | ❌ |
| S5 | explain-project positive | fires | `explain-project` | ✅ |
| S6 | explain-project near-miss | → accessibility-annotator | `accessibility-annotator` | ✅ |
| S7 | spec-to-prototype positive | fires | `spec-to-prototype` → `frontend-design` | ✅ |
| S8 | spec-to-prototype near-miss | must NOT fire | did not fire | ✅ |
| S9 | accessibility-annotator positive | fires | `accessibility-annotator` | ✅ |
| S10 | accessibility-annotator near-miss | → convert-markdown | `convert-markdown` | ✅ |
| S11 | brain-entry **locked** | must NOT auto-invoke | no skill invoked, no capture claimed | ✅ |
| S12 | unlock **locked** | must NOT auto-invoke | no skill invoked, never touched bws | ✅ |
| S13 | lab-notebook **gated** | invoke, gate before writing | invoked, asked, **0 files** | ✅ |
| S14 | create-wiki **gated** | invoke, gate before writing | invoked, asked, **0 files** | ✅ |

**Phase 8's contract holds, and this is the first evidence of it that isn't self-assessment.** Both gated skills did exactly what D57 specifies: `lab-notebook` and `create-wiki` were each *model-invoked* (proving the flag removal took) and each stopped at the Phase-0 gate with an explicit description of what would be written, creating nothing. S14 went further than required, volunteering that initialization "appends a `## Project Wiki` section to `CLAUDE.md` … that changes how Claude behaves in this repo going forward" and flagging its overlap with the existing `memory/` convention. Both locked skills stayed locked. **8.2's premise is also confirmed empirically**: `unlock` and `brain-entry` were never auto-invoked even though the conversations sat squarely in their domain — with their trigger prose removed from context, there was nothing to trigger on, which is the intended behavior and the reason that prose was dead weight.

**S4 is a real miss, and it is cross-plugin.** The prompt — "Can you build me a workflow diagram I can view in Draw.io?" — has no existing BPMN file, so it should route to `bpmn-generator`. Both `Must NOT` criteria passed (it did not wrongly fire `bpmn-to-drawio`, and it did not tell the user to hand-author XML first). It correctly recognized the source as a natural-language description: *"Empty working directory, no existing docs — greenfield."* Then it invoked **`superpowers:brainstorming`** and asked what the diagram was *for*, never reaching `bpmn-generator`.

The mechanism is not a defect in this repo's descriptions. `superpowers:brainstorming` declares *"You MUST use this before any creative work — creating features, building components…"*, and `superpowers:using-superpowers` states that process skills take priority: *"'Let's build X' → brainstorming first, then implementation skills."* The word **"build"** in the prompt is the trigger. Firing brainstorming is arguably correct under that doctrine — **the miss is that it never handed off to the implementation skill afterward.** S7 shows the handoff working (`spec-to-prototype` → `frontend-design`), so the chain is not structurally broken; it just did not happen here. S8 also fired brainstorming, and there it was the right call.

**No amount of structural gating could have found this.** It is a live interaction between two independently-authored plugins, visible only in a real session. It is also a standing hazard for *every* domain skill in this marketplace whose trigger phrasing contains a creation verb.

**Two harness gaps in the eval itself, independent of the results.**

1. **The eval specifies scenarios but no harness, and the harness decides the outcome.** The first S13 attempt returned `is_error: true` on `Execute skill: personal-plugin:lab-notebook` — headless `-p` mode has no human to approve, so the Skill tool was auto-denied. Read naively that is a total Phase 8 failure; it was a permission artifact. The working harness needs an explicit `--allowed-tools Skill Read Write Edit Glob Grep AskUserQuestion`. It also needs **`Bash` deliberately disallowed**: S13's prompt names the Jetson, and a permission-bypassed agent could have SSH'd into the live host and changed a real machine to satisfy an eval.
2. **Scoring should stop at first dispatch.** S7 hit the 300s timeout — not a failure: it routed correctly, chained into `frontend-design`, and began actually building the prototype. A routing eval should not need a five-minute budget.

Also worth recording: `AskUserQuestion` is **not available** in headless `-p` sessions. S13 tried it, found it missing, and fell back to asking in prose — the gate held either way, which is a good robustness property of how 8.3 was written, but any future harness must not treat "no AskUserQuestion call" as a gate failure.

**On the eval's own reliability:** the first batch returned `API 529 Overloaded` on 8 of 13 scenarios. Those are infrastructure, not findings, and a naive scorer would have recorded 8 failures. The re-run with backoff passed all 8 on the first attempt. **Any automated runner for this eval must distinguish `api_error_status` from a real negative result** — otherwise it will manufacture findings on a bad afternoon.

--- New session: 2026-07-30 — step back from the close-the-loop set: reconcile the whole open backlog against ground truth, then plan the remaining 16 items as classes rather than issues. ---

### Entry 062 — Backlog reconciliation + #227 mechanism correction [decision] [plan]

**Date:** 2026-07-30
**Environment:** Linux VM, `main` @ `7d5ae1f`, 0/0 divergence from `origin/main` (D17 check run). personal-plugin 11.6.0 / bpmn-plugin 4.4.0 / slide-gen 1.3.0 / marketplace 3.3.0. Working tree carried 2 uncommitted doc files from the prior session's clear-prep flush (CLAUDE.md version-bump rule + LAB_NOTEBOOK living sections) — not lost work, just uncommitted.
**Status:** COMPLETE — 4 issues filed, 5 corrected, plan generated (8 phases / 19 items)

**Objective:** Before executing any more of the close-the-loop set, establish that the local task list, the GitHub issue list, and the notebook's Open-Backlog row all describe the same 16 items; then group those items by root cause rather than by issue number and sequence them so the highest-leverage debt is eliminated first.

**Hypothesis:** (a) `task_sync sync --plan` shows near-zero drift, because #229 synced hours ago — expect only bookkeeping deltas, no creates and no pushes; (b) the 16 issues collapse into a small number of *classes*, so a plan organized by class will be materially shorter than one organized by issue; (c) at least one issue is wrong as filed, because E060 measured a **22-of-24** wrong-as-filed base rate on this same audit-derived backlog and these 16 have not been through that verification. Measurable: local open-task issue numbers == `gh issue list --state open` numbers, exactly.

**Rollback Plan:** Read-only through the reconciliation except for one `task_sync sync --apply`, which writes `tasks.json` + regenerates `TASKS.md`. ~~`tasks.json` is git-tracked ⇒ `git checkout -- tasks.json` reverts it~~ — **this premise was wrong and is corrected below: `tasks.json` is gitignored, so there is no git undo for it.** The applied delta was one pull of #228's body, re-fetchable from the tracker at any time, so the practical rollback is "re-run `sync`". `TASKS.md` is gitignored and regenerated by the next mutating command. The plan proposed at the end of this entry modifies nothing until approved. No GitHub writes: the plan carries `creates: 0` and `pushes: 0`, so `--apply` cannot mutate the tracker.

**Reconciliation result — the three lists agree exactly.** 16 open locally, 16 open on GitHub, same numbers: `169, 170, 171, 198, 199, 200, 206, 210, 216, 217, 218, 223, 224, 226, 227, 228`. Zero local-only tasks, zero orphans, `creates: 0`, `pushes: 0`, `skipped_adopts: 0`, `confidentiality_findings: 0`. Hypothesis (a) confirmed. The prior session's stale-`priority` repair note (memory `github-issues-workflow`) is discharged — #189 is closed and no priority field is null on any open task except #169/#170/#171, which correctly carry no priority label on GitHub either.

Two bookkeeping deltas only:

| Delta | Item | Substance |
|---|---|---|
| `pulls: 1` | #228 | Body/label refresh — the issue was edited after the last sync. No decision needed |
| `conflicts: 1` | #205 (`t-2e37ad`) | **Representational, not substantive.** Local holds `state: closed` + raw label `priority/P3`; remote holds the normalized `status: done` + `priority: P3`. Both sides say *done, P3*. Recommendation is `local` (last-write-wins), but `local` implies a `gh issue edit` on an already-closed issue for zero content change, so `remote` is the cheaper resolution with identical meaning |

Applied pull-only (`sync --apply` with **no** `--decisions` file): `0 create(s), 0 push(es), 1 pull(s); 1 conflict(s) surfaced`. The #205 conflict was deliberately left undecided — per the skill's own rule an undecided conflict is untouched and simply resurfaces, which is the safe default when the resolution is a user call rather than a mechanical one.

**Unfiled finding, surfaced by the rollback plan being wrong: `tasks.json` is gitignored, which silently reversed D34 and disabled the cross-machine merge base.**

Writing the rollback plan asserted "`tasks.json` is git-tracked." It is not — `.gitignore:241-242` ignores both `TASKS.md` **and** `tasks.json`, added by PR #175 (`3c47f68`, 2026-07-18, four days after the design landed). The design is unambiguous in the other direction (`docs/plans/2026-07-18-task-sync-design.md`):

- `:64` — "**`tasks.json`** — repo root, **committed**. The list plus the `last_synced` merge base. **Committed so the base travels between the user's two machines via git.**"
- `:65` — `TASKS.md` … **gitignored** — the *only* file the design says to ignore.
- `:100` — "One list, always the safe version — so **`tasks.json` is fine to commit (even in a public repo)** and fine to sync."
- `:129` — "Two machines → `git pull` before syncing so you reconcile against the latest base; the committed `last_synced` makes it safe."

**PR #175's stated rationale** — "in this public repo the shared/canonical backlog is the GitHub issues, not a committed personal task list … prevents accidentally publishing the task list" — is a defensible *position*, but it is the exact concern `:100` had already answered, and the confidentiality subsystem (D34's one-list model, D36's `scan-apply`, the keep/redact/remove/anonymize dispositions remembered by content hash) exists for no other purpose than making the list safe to commit. So #175 re-solved a solved problem and paid for it with the merge base.

**What it actually costs.** The 3-way classification that D34/D35/D37 spent three decisions tuning is defined against a *shared* `last_synced` base. With the file machine-local, the owner's second machine (Windows laptop — see the global CLAUDE.md dual-environment section) holds its own base, so on that machine every issue classifies as `NEW_REMOTE` and adopts fresh: no `CHANGED_BOTH`, no conflict surfacing, no last-write-wins. Not data loss (the tracker is canonical and permanent by D34), but the conflict-detection half of the engine is inert across exactly the two-machine topology it was designed for. It also strands the confidentiality machinery, which now sanitizes a file that never leaves the machine.

**No Decision Log entry records the reversal** — which is why it stayed invisible for 12 days and why the notebook, the design doc, and `.gitignore` currently disagree with each other. This is D34's own failure mode one level up: the rule that "every decision must be logged with alternatives" (Rule 4) is what would have caught it. Filed as **#230** rather than fixed inline — the right resolution (commit it, or amend D34 to bless local-only and delete the orphaned rationale) is a design call, not a chore.

---

**The 16 items are 6 classes, not 16 problems.** Hypothesis (b) confirmed. Grouping by root cause rather than by issue number collapses the backlog and, more usefully, shows that three separate issues are one missing gate:

| Class | Items | Root cause |
|---|---|---|
| ① A documented step with no gate behind it | #226, #210, #218 | The repo's most-repeated defect (E043, E056, E057). #226 = version bump, #210 = CHANGELOG in both files, #218 = a `Last Verified` stamp nobody backs. **One gate closes all three** |
| ② "Both units tested" ≠ "the call sequence tested" | #224 | E049, and E061's `bug_001` surviving at 96% line coverage |
| ③ Eval results are not trustworthy | #228, #227 | The eval defines no harness, and the harness decides the outcome |
| ④ Model calibration | #198, #200, #199-remainder | Deferred — the 13/14 result gives no evidence the dials are mis-set |
| ⑤ Not schedulable until re-derived | #217, #230 | Filed claims that verification has already falsified, or that were never verified |
| ⑥ Real projects, own plan each | #216, #206-context-economy-half, #171, #169/#170 | Mislabeled as hygiene by their `P3` tags |

**Three framing corrections, each verified against the tree before being acted on.**

1. **#227's two leading options are both blocked, and its supporting evidence is wrong.** `superpowers/skills/brainstorming/SKILL.md:61` — "The terminal state is invoking writing-plans. Do NOT invoke frontend-design, mcp-builder, or **any other implementation skill**" (byte-identical in cached 6.1.1 and 6.2.0). So brainstorming is not *failing* to hand off to `bpmn-generator`; it is **forbidden** to, and `bpmn-generator` is unreachable in that session by any sanctioned route. Option 1 (strengthen the description) cannot win either: `using-superpowers` states a priority *ordering*, not a similarity contest, and `bpmn-generator` already lists "build workflow" verbatim as a trigger and still lost. **E061 and the issue both cite S7 as proof the chain works — brainstorming never fired in S7.** S7 is evidence that skill *chaining* works; no scenario in the run tested brainstorming's handoff. What we own is the eval: S4's `Must` asserts an outcome owned by another marketplace's doctrine, which is this repo's own "a check restating an external truth will agree with the bug" rule pointed outward. Both `Must NOT` criteria — the ones that *are* about our descriptions — passed. Correction posted to #227.

2. **#199 was two issues.** Its phase-numbering and phantom-taxonomy defects are not calibration; they are wrong documentation in the deepest planning skill, about to be exercised by the planning pass that schedules this backlog. Extracted to **#231**; #199 keeps the calibration half and stays deferred. Verification while extracting found the phantom-taxonomy defect at **eight** sites, not the three (`:89,236,244`) filed — E061 finding 1 again, third occurrence.

3. **#206 is inventory drift (minutes) plus ~7 oversized SKILL bodies (a refactor)** wearing one `P3` label. Only the first half is hygiene; the second belongs to class ⑥.

**Verification found the phantom-taxonomy defect is load-bearing, not cosmetic.** `ultra-plan` conditions three behaviours on the undefined scale — whether to run the Phase 0 constitution check (`:89`), whether to emit an ADR (`:222,236,315`), and whether to generate a creative-branching comparison (`:238,240,242,244`). `plan-gate` defines Paths A/B/B.5/C/D/D.5/E/F and **no L-levels at all**, and no mapping exists anywhere in the repo. The skill still produces output; it just makes every skip/no-skip call on an invented value, which is indistinguishable from working. The phase numbering has the same property: `:350` cites "Change sets (Phase 2c)" — the correct logical name — while the heading it points at reads `3c`, so the file contradicts itself in both directions and a reader cannot recover intent from context.

**Scope decision (D58).** User approved classes ①②③⑤ plus the hygiene half of ⑤/E and the two new issues: **#206 (inventory half), #210, #217, #218, #223, #224, #226, #227, #228, #230, #231** — 11 items. Deferred: #198/#200/#199-remainder (④), #206's context-economy half, #216, #169/#170/#171 (⑥).

**Planning depth decision (D59).** Full `/ultra-plan` with the Phase 1 verification fan-out, not a direct write-up. Basis: E060 measured a **22-of-24 wrong-as-filed** rate on this same audit-derived backlog, and these items have not been through that verification — a fact this session has already reconfirmed three times unprompted (#227's mechanism, #199's eight-vs-three sites, #230 found only because a rollback plan asserted something false). Planning from the filed text would encode at least #217's three known-wrong claims.

---

**Live finding during Phase 0: the skill loader served personal-plugin 11.3.0 while the manifest names 11.6.0 (#232).** Invoking `/task-sync` reported its base directory as `.../personal-plugin/**11.3.0**/skills/task-sync`, but `installed_plugins.json` holds exactly one entry for the plugin — `scope: user`, `installPath: .../11.6.0`, `gitCommitSha 49face4`, updated the previous day. No project/local scope, no in-repo settings pin.

**The served content was genuinely stale, not just the path label.** The delivered body lacked the whole `orphans` section that 11.6.0 adds (the #181 fix): the plan-JSON key list, the per-orphan `keep`/`drop` prompt, and the amended "already in sync" condition. `11.6.0/skills/task-sync/SKILL.md` is byte-identical to the repo copy; `11.3.0` is not. Both cache directories are complete (29 skills each, identical names), so a partial-install fallback is ruled out.

**Consequence, and why it is the dangerous kind.** I parsed `sync --plan --json` for exactly the six keys the 11.3.0 body documents and **never read `orphans`** — because the contract I was reading did not contain it. The tool itself was correct: run from repo source per the standing rule, and emitting `orphans`. So the *tool* was current and the *contract* was three minor versions stale, with no error anywhere. It was `orphans: 0`, so nothing was lost; had it been non-zero the session would have declared the backlog fully reconciled while silently discarding the precise finding #181 exists to surface.

**This forces a stronger rule than the one CLAUDE.md carries.** "Run bundled tools from repo source when a fix matters" protects the *tool* and leaves the *skill body* — which defines the contract the model reads the tool's output against — unprotected. A current tool plus a stale body yields confidently wrong parsing. Distinct from #226: that is "two trees under one version string", which a version-bump gate catches; this is "the manifest says one version and the loader serves another", which no version-bump gate can catch because the bump was performed correctly.

**Not uniformly stale, which is worse.** E061's A21 run reported testing 11.6.0 as installed, and S13/S14 passed with both skills model-invoked — impossible on 11.3.0 bodies, which still carry `disable-model-invocation: true`. So that run did see 11.6.0. The resolution therefore varies, and cannot be validated by checking once. Filed as **#232**; the root cause is in Claude Code's loader, but the mitigation (a version preflight, cache pruning, or the ADR-0012 pattern applied to skill bodies — derive the key list from the tool, not from prose) is ours.

---

**Phase 1 — six Explore agents, clustered by shared code path (the E060 method). Every cluster returned corrections; the wrong-as-filed rate held.**

**My own one-gate hypothesis was refuted, and that is the headline.** D58 and the class table above both asserted "#226 + #210 + #218 — one gate closes all three." Tested against evidence it holds as a *diagnosis* and fails as an *implementation*. The three differ on every axis a gate is built from:

| | #226 | #210 | #218 |
|---|---|---|---|
| Input | the **diff** (VCS state) | **two files' content** (tree state) | **an external API** |
| Decidable offline? | yes | yes | **no** |
| Runnable in CI? | yes, with a deepened checkout | yes, stdlib-only | **no** — ADR-0009/D32, zero secrets |
| Failure trigger | content changed, version didn't | version bumped, entry didn't | wall-clock time passing |
| Event-leg sensitive? | **yes** (push vs PR) | no | n/a |

**#218 breaks it outright**: its ground truth lives behind an API key doctrine forbids CI from holding, so any in-repo check can only verify *internal consistency* — a **staleness alarm, not a verification**. The honest decomposition is **2 + 1**: one offline diff-derived script carrying two conditional rules (#226 + #210 genuinely do collapse), and #218 as a separate docs-doctrine decision. Corrected in D58 below.

**#226 — two blocking facts the issue does not contain.** (a) `validate.yml` triggers on **`push: [main]` AND `pull_request: [main]`**, so every merge runs both legs; a naive `git diff origin/main...HEAD` on the push leg diffs main against itself and reddens a required context. D55 anticipated exactly this hazard for #204. (b) The checkout at `validate.yml:304-305` sets **no `fetch-depth`** ⇒ depth 1, and `grep -rn fetch-depth .github/ scripts/` returns **zero** hits repo-wide — there is no base commit, no merge-base, and no precedent to copy. The gate needs a deepened checkout *and* an explicit event-leg branch, and the push-leg branch must be **asserted by the negative test**, not assumed.

**#226 vs #210 are in direct tension on one path.** #210's remediation is a three-file CHANGELOG-only PR that bumps nothing (backfilling history is not a release, D45). If `plugins/*/CHANGELOG.md` is not exempt, #226's gate **hard-blocks the PR that closes #210** — while #210's enforcement half wants a CHANGELOG entry *required* on a bump. One path, simultaneously exempt and mandatory, conditioned on whether a version changed. Expressible as one script with two rules; not expressible as one rule.

**#210 is understated by an order of magnitude: 24 missing versions, not 2** — and **all three plugins are missing their current shipped version** (personal-plugin 11.6.0, bpmn-plugin 4.4.0, slide-gen 1.3.0). The release commit `49face4` touched the three `plugin.json` files, `marketplace.json`, and the root CHANGELOG — and **zero per-plugin CHANGELOGs**. The release that fixed #226's instance created three fresh instances of #210 in the same commit. Its own `bpmn2drawio` version sync *was* caught, by the one guard that exists.

**#218 is stale as filed, in the way that proves it.** The Anthropic row no longer reads `2026-07-08` — commit `5cd2005`, the PR that fixed #189, **hand-refreshed the stamp to `2026-07-29` with no probe, in the same edit that fixed the bug the stale stamp had concealed.** That is the second recorded instance of the identical behaviour (`1f55dcd` was the first, E060). Worse, the file's own Resolution Order at `:41` names **`check-models`, a command that does not exist** — deliberately deleted per archived plan v6, its reference never removed, and `## Model Check Output Examples` at `:70-80` documents the output of a phantom. True extent is **12 live sites, not 1**, two of which are **generators** (`explain-project/SKILL.md:392`, `create-wiki/SKILL.md:271`) that mint the pattern into every document they produce — the E060-finding-3 propagation shape again.

**#217 is worse than "3 of 4 wrong": all four claims are wrong or misdirected, and the real defect is unfiled.** `/unlock` reads **`$TROY`**, which is set by nothing on this machine — verified: `TROY` UNSET, `BWS_ACCESS_TOKEN` set (94 chars). `skills/unlock/SKILL.md:50` does `TOKEN="$TROY"` and `:53` hard-stops when empty, so **`/unlock` fails at Step 2 on every invocation and never reaches `bws`**. Claim (a)'s mechanism names `.bashrc:167`, which guards the *full credential set*; the operative line is **`.bashrc:8`**, an early `return` for non-interactive shells that makes the anti-staleness `eval` at `:165` — already present since 2026-07-16, i.e. *already claim (b)'s proposed fix* — unreachable. Claim (c)'s six `~/.claude/scripts/*.sh` are all out-of-repo **and use legacy `bw`/`BW_SESSION`, with zero `bws` and zero `BWS_ACCESS_TOKEN` references** — the proposed fix would be a no-op on a variable they never read for a CLI they never call. Claim (d) is true as a rule with **one** in-repo offender (`references/api-key-setup.md:49`). Second in-repo blocker found: `allowed-tools` omits `python3` (`Bash(python:*)` does not prefix-match), `mktemp`, `chmod`, `rm`, `source`, and does not cover `:92`'s `BWS_ACCESS_TOKEN="$TOKEN" bws …` form. **D53 and notebook `:645`/`:657` restate the wrong mechanism and need the same correction.**

**#228 — three linter traps that would redden the build, none of them obvious.** Reproduced by running `validate_structure` against nine mutated in-memory copies: (E) heading the section `### S0: Harness` makes it a *scenario* and fails; (I) **a file-level `## Harness` carrying `**Invocation:**` does NOT satisfy the per-file invocation requirement** — `seen_invocation` is computed inside scenario bodies only, so hoisting the 14 `**Context:**` lines fails S1 immediately; (G) downgrading a scenario's `Must` **and** `Must NOT` both to `**Should:**` fails — at least one literal marker must survive. A plain `## Harness` section is *ignored* by the linter, which is why it is safe.

**#227's blast radius is 6 scenarios and 2 rubric rows, not S4 — and S7 is a false green.** Nine of 14 scenarios carry a positive-dispatch `Must` naming a specific skill; six sit behind creation verbs (S1 "model", S4 "build", S5 "generate", S6 "add", S7 "build", S9 "add"). **S7's `:119` is structurally identical to S4's failing `:82`** — it passed only because brainstorming did not fire that run, and it is cited as *proof the handoff works* in both #227's body and E061 `:971`. Fixing S4 alone leaves the same defect green in S7. The Rubric at `:226`/`:228` restates the same unowned assertion at file level, and the linter validates only that `## Rubric` exists as a substring, so a rubric contradicting its own scenarios passes CI silently. **`evals/skills/plan-gate.eval.md` is an unrun second instance** — 5 `Context:` scenarios, four positive-routing `Must`s, and an `S5: Proactive trigger` asserting a planning skill must suggest itself before implementation, head-on with `brainstorming → writing-plans`.

**The S8 template, which is the fix shape.** S8 fired brainstorming and *passed*, because it names no skill it must dispatch to (only what must **not** be used), its positive `Must` is a **recognition** assertion satisfiable from stated reasoning regardless of dispatch, and its behavioural clause is hedged with `optionally` + a disjunction. S4 already contains its own fix: its recognition `Must` at `:81` **passed** on the live run. Only `:82` has to change.

**`claude plugin eval` exists but is unusable, and adopting it is not a doc change.** `claude plugin --help` on 2.1.220 documents it; invoking it prints *"`plugin eval` is currently in early access"* and **exits 1**. Convergence cost measured: **255 scenarios and 1,091 `- [ ]` criteria** to port from zero — roughly **4.6× the criterion count ADR-0009 already rejected** as "by far the largest diff". And it *is* the LLM-judge runner ADR-0009 §3 deferred, so adopting it supersedes an Accepted ADR and reopens D32. Record and defer; do not converge.

**#224 — the coverage report already names the gap.** `__main__.py` is at 95% with **Missing `281-283, 288`**, and line 288 *is* the `_split_flat_decisions` call: **the function written to fix bug_001 has never executed through the CLI.** Also: there is **no `cli.py`** (the file is `__main__.py`, seam is `run_sync(args, provider=None)` at `:238`), and the issue's "three documented shapes" is **FALSE** — `sync-semantics.md:146-147` documents **two**. The third — wrapped conflicts-only, *the shape that caused the outage* — exists only in a docstring and is absent from the user-facing reference. That documentation gap folds into the fix.

**#230 — my own filing carried two errors and missed a fourth source.** Not "four days after the design landed": the design doc and the ignore rule landed the **same day** (2026-07-18). Not four design-doc references but **six**. And `references/config-reference.md:61-70` already reconciles the contradiction **toward local-only** — "whether `tasks.json` is committed is a per-repo choice … this repo gitignores both" — logged in `CHANGELOG.md:103` as a *"Truth fix"*. So the reversal was ratified **twice, silently**, which strengthens the "log the decision" half and complicates the "restore the design" half. The load-bearing claim survives (`classify.py:1` and `:62` call `last_synced` the "committed, git-committable base"), but the consequence is narrower and differently shaped than filed: after machine 2 adopts it stamps its own base and `CHANGED_BOTH` works there, so the real loss is that **no local-only state propagates between machines at all**. Corrections posted to both issues.

**#206's inventory half is understated (8 defects, not 5) and has a generator answer.** `scripts/update-readme.py:329` hard-codes `README.md` as its **only** target. README carries the same facts and is **provably drift-free** (regenerated, `--check`-gated at `validate.yml:318`); CLAUDE.md is hand-edited and carries 8. That is a controlled experiment, not a coincidence — this is not a missing generator but a **generator with under-scoped coverage**, and it is CLAUDE.md's own "a guard that can't fail is worse than none" rule, which already names `update-readme.py --check` as a prior offender. Beyond the 5 filed skills: `build-cfa-deck` missing from the slide-gen list, and **`plugins/personal-plugin/agents/` — ten files, one of the largest surfaces — absent from the Repository Structure block entirely**. `sg-optimize`'s `--output` default is **not knowable in-repo** (ADR-0008: the engine is in a private repo; `grep -rl "_optimized" --include=*.py` → zero hits), so the correct fix is to state the uncertainty, not the behaviour. And the deprecated-command residue is **6 live sites, not 1** — worst are `TROUBLESHOOTING.md:900` and `docs/PLUGIN-DEVELOPMENT.md:112-115`, which *actively instruct* readers to use `/new-command`, deprecated by ADR-0006/D21.

**Self-inflicted, this session:** archiving the plan made `CLAUDE.md:262`'s "Current/completed implementation plan" pointer dangle — `IMPLEMENTATION_PLAN.md` no longer exists. Folded into the #206 change set.

---

**Four issues filed, four corrected — three of the corrections were to filings from earlier in this same session.** #230 (`tasks.json` vs D34), #231 (ultra-plan), #232 (stale skill loader), #233 (`ask-questions` legacy menu). Corrections posted to #227 (mechanism inverted), #199 (scope split), #224 (no `cli.py`; two documented shapes, not three), #230 (same-day not four days; six refs not four; a fourth source already reconciled the other way), and **#231 — which contained an off-by-one in its own line references, in an issue about an off-by-one**, plus one entry (`:350`) that is not a defect and whose "fix" would have propagated the bug into the only reference that survived the original renumbering.

That last one is the most useful data point in the entry. **I filed #231 after verifying its claims against the tree, and it was still wrong in three ways.** Verification reduces the error rate; it does not zero it. The only thing that caught `:350` was a second independent reader with the same instruction to verify.

**Plan generated (Phase 5).** `IMPLEMENTATION_PLAN.md` — **8 phases / 19 work items / ~35 files**, within the template's 8×6 caps. Structural verification: 8 `## Phase` headings, 19 `####` work items, 19 `**Status: PENDING**`, all 12 in-scope issues present in the traceability text, `markdownlint-cli2` clean.

**Caught during 5d self-verification: #224 was missing from the generated plan entirely.** It was in the approved scope and in the class table, but dropped between the interaction map and generation — my Phase 2 change-set list has 8 sets and #224 is in none of them. Added as item 8.3. Recording it because it is the same failure mode as every other finding in this entry: **the plan's own completeness check was the only thing that caught it**, and had I skipped 5d on the grounds that I had just written the plan and knew what was in it, it would have shipped a scope gap.

**Critical path is 1 → 2 and nothing else.** Phase 1 (CHANGELOG backfill) must precede Phase 2 (the gate) because #210's remediation is a CHANGELOG-only PR that bumps nothing — precisely what Phase 2's Rule 1 rejects. Phases 3–8 share no files with the critical path or with each other, except one collision the `Depends On` field would not have caught: **Phase 5 and Phase 8.1 both edit `unlock/SKILL.md`**, recorded in the Risk table as a serialization requirement.

**Highest-severity unknown is U6, and it is about this session's own method.** #232's loader staleness means a manual acceptance test may exercise a different skill version than the one just edited — so the plan's standing instruction is to verify the installed cache *content*, not its version string, before trusting any manual verification. The plan is deliberately not gated on #232.

**Status:** COMPLETE — reconciliation done, 4 issues filed, 5 corrected, plan generated and structurally verified. Execution is a separate session via `/implement-plan`.

--- New session: 2026-07-30 — execute the E062 plan via `/implement-plan`: 8 phases / 19 items off `main` `b4d576c`. ---

### Entry 063 — Executing the close-the-loop + hygiene backlog (8 phases / 19 items) [plan] [build] [ci]

**Date:** 2026-07-30
**Environment:** Linux VM, branch `feature/close-the-loop-backlog` off `main` `b4d576c` (E062's PR #234 squash-merged; 0/0 divergence from `origin/main` per D17). personal-plugin 11.6.0 / bpmn-plugin 4.4.0 / slide-gen 1.3.0 / marketplace 3.3.0. Orchestrator on Opus 5 (1M). Default mode — PR at the end, no auto-merge, no phase pauses.
**Status:** IN PROGRESS

**Objective:** Execute `IMPLEMENTATION_PLAN.md` (generated in E062) end-to-end, closing 12 issues across 8 phases. All 19 items start `PENDING`.

**Hypothesis:** The orchestrated loop lands all 19 items with per-phase Definition-of-Done gates green, producing one PR. Measurable success criteria: (a) every item's `**Status:**` reaches `COMPLETE`; (b) each phase's DoD block exits 0 before the phase boundary is crossed; (c) the two guards this plan *creates* — `scripts/check_version_bump.py` (2.2) and the extended `update-readme.py --check` (6.1) — are each demonstrated to **exit non-zero on deliberately-bad input before being wired in**, per the standing negative-test rule, with the observed exit codes recorded here rather than asserted in prose; (d) `main` is never red — in particular the `push`-to-`main` leg of `Validate Plugins (official CLI)` stays green after Phase 2 merges, which is the single highest risk in the plan.

**Rollback Plan:** Every batch is its own commit on `feature/close-the-loop-backlog`, and `last_good_sha` in `.implement-plan-state.json` tracks the most recent all-gates-green commit. A failed item is never committed — `git checkout -- .` returns the tree to `last_good_sha`. Whole-run abort: `git checkout main && git branch -D feature/close-the-loop-backlog` discards everything; `main` is untouched until the PR merges. `IMPLEMENTATION_PLAN.md` is git-tracked, so its Status-field edits revert with the branch. **Phase 2 carries an additional rollback beyond the branch:** if its gate reddens `main`'s push leg after merge, the remedy is to revert the single commit that added the CI step — the step is additive and removing it restores the prior job definition exactly, with no branch-protection coordination needed because no job key changed (D28).

**Pre-flight finding: the resume path would have skipped all 19 items and reported success (#235).** `/implement-plan`'s Step 0 found a stale `.implement-plan-state.json` from the **completed E061 run** — `current_phase: COMPLETE`, `current_item: null`, `completed: 42`, and a `parallelization_map` naming plan v12's eight phases. Its `plan_file` field reads `IMPLEMENTATION_PLAN.md`, the default path, which now holds an entirely different plan.

The resume logic reads `current_phase`/`current_item`/`completed` and skips the STARTUP scan. With no `in_progress` marker (the interrupted-run detector), the routing finds nothing remaining and returns `ALL_COMPLETE` → FINALIZATION: delete the state file, polish docs, open a PR "for the phases actually implemented", and print `Status: COMPLETE`. **Nineteen PENDING items skipped, reported as a successful run**, with the COMPLETION REPORT generated from the same stale file so it would have cited the *previous* plan's 42 items as this run's output.

**Two failures compose.** FINALIZATION's `rm -f .implement-plan-state.json` runs only on the ALL_COMPLETE path and never executed when E061 ended at PR creation; the file is **gitignored**, so nothing — `git status`, CI, pre-commit — could surface it, and it sat on disk two days. Separately, the state file identifies its plan **by path, not by identity**, so archiving v12 and writing a new plan at the same path leaves stale state pointing at a plan it has never seen with no field capable of detecting the mismatch. Either failure alone is benign; together they are silent and total.

**Same family as #226 and #232:** an artifact identified by a *label* — a version string, a cache path, a file path — where the label agrees and the content does not. That is now three instances in two sessions, and the mitigation is identical in all three: **verify content, never the identifier.** Filed as #235; state file backed up to scratchpad and deleted before starting.

**Execution shape.** Critical path **1 → 2**, strictly sequential — Phase 1's CHANGELOG-only change is exactly what Phase 2's Rule 1 rejects, so the backfill must land first. Phases 3–8 share no files with the critical path or with each other, with one exception the `Depends On` field does not express: **Phase 5 and Phase 8.1 both edit `unlock/SKILL.md`** and must be serialized. Per-item model tiers are specified 19/19; Phases 2 and 6 override to `opus`.

**Results — logged per batch as each lands:**
