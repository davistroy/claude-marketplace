# Claude Marketplace — Lab Notebook

**Project:** Claude Code plugin marketplace — two plugins (personal-plugin, bpmn-plugin) extending Claude Code with 25+ commands and 20+ skills for documentation, architecture review, research, BPMN modeling, and workflow automation.
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

| D34 | **task-sync skill design (approved, not yet built):** per-repo committed `tasks.json` reconciled bidirectionally with the repo's tracker (GitHub `gh` / Gitea `tea`); skill-as-interface (in-session tables + gitignored `TASKS.md`); 3-way sync, last-write-wins by `updated_at` with genuine conflicts surfaced; prune-on-close archiving (tracker = permanent archive); ONE list with per-finding confidentiality dispositions (keep/anonymize/redact/remove, remembered by content hash); milestone as the "project" grouping; IMPLEMENTATION_PLAN.md stays separate (backlog vs execution blueprint). Full design: `docs/plans/2026-07-18-task-sync-design.md` | 2026-07-18 | E047 | Two-file private lane — rejected (user wants one list); standalone TUI app — rejected (YAGNI, in-session table suffices); flatten plans into tasks / drop markdown plans — rejected (loses the structure /implement-plan needs); bespoke `project` field — rejected (milestone round-trips to the tracker); bash+jq reconcile vs Python tool — deferred to plan time (lean Python for testability) |
| D33 | **Retire the mypy count-ratchet; use bare `mypy src/ --ignore-missing-imports` for all 3 tools** (delete both `.mypy-baseline` files). All tools are mypy-clean (D24), so the ratchet is scaffolding; converge on the simpler existing form (feedback-docx's). Behavior-identical (baseline-0 ratchet passes iff mypy=0). **Supersedes D24's ratchet mechanism** (D24's zero-goal stands) | 2026-07-17 | E045 | Give feedback-docx a `.mypy-baseline=0` for symmetry — rejected (spreads the more-complex form to all 3; keeps an escape-hatch to raise the ceiling that contradicts hard-zero) |
| D32 | Eval execution = deterministic **structural linter now** (extend `check_eval_mapping.py`: scenario/Must/Rubric structure + coverage gate + `command:` validation); **LLM-judge behavioral runner DEFERRED** to its own go/no-go (ADR-0009, Accepted) | 2026-07-17 | E043 | Build the LLM-judge runner now — rejected (would be the repo's FIRST CI secret, can't run on fork PRs, flaky per non-deterministic grading, real cost; a CI-posture decision not an impl task). Hybrid re-author all 45 evals with machine-readable markers — rejected (largest diff, gate ends up ≈ structural linter). Close #150 as human-run-by-design — rejected (leaves the 10-surface coverage gap + dead cross-cutting `command:` field). Basis: `evals/README.md:87` says evals are human-run by design, so CI-executing them is an architecture change, not a bugfix |
| D31 | Personal marketplace does NOT accept third-party/vendor plugins — especially remote-MCP plugins with non-LLM egress (esp. write-capable). Decline #97 (xquik) | 2026-07-16 | ACTIVE | E037 | Accept-with-changes (schema loosen for `mcpServers` + SECURITY.md egress-policy update + strict validation + auth reconcile + `disable-model-invocation`) — rejected (establishes a vendor-plugin acceptance policy the owner doesn't want, contradicts the SECURITY.md "LLM-API egress only" model). Leave-open — rejected (no path to yes). Basis: this is the owner's own read-only/analysis tooling, not a registry; `schemas/plugin.json` forbids `mcpServers` (`additionalProperties:false`) so vendor-MCP plugins can't merge without an owned schema change anyway |

Status values: ACTIVE · SUPERSEDED (by D#) · REVERSED (in E#)

## Action Items

Track follow-ups that emerge from experiments. Move to Completed when done.

### Open

| # | Action | Created | Source Entry |
|---|--------|---------|-------------|
| — | **No open action items.** Canonical backlog is the GitHub issues list (A2/A12 directive): currently **#155** (feedback-docx mypy-gate unification, P4) and **#156** (lab-notebook `rotate` operation + threshold, P5) — both scoped OUT of the #149–#154 plan. | — | E043 |

### Completed

| # | Action | Created | Completed | Source Entry |
|---|--------|---------|-----------|-------------|
| C1 | v8.0.0 marketplace modernization — 7-phase plan, all complete | 2026-04-21 | 2026-04-21 | Pre-notebook |
| C2 | Remove research-orchestrator Python tool (27 files) | 2026-04-21 | 2026-04-21 | Pre-notebook |
| C3 | Remove stale CI jobs referencing deleted tool and help-sync check | 2026-04-21 | 2026-04-21 | Pre-notebook |
| C4 | Plan template refinements — 7 improvements to plan-template.md | 2026-04-30 | 2026-04-30 | E001 |
| C5 | Update implement-plan.md to set Completed header field during finalization (A2) | 2026-04-30 | 2026-04-30 | E003 |
| C6 | Update implement-plan.md to parse Depends On for parallelization map (A3) | 2026-04-30 | 2026-04-30 | E003 |
| C7 | Update implement-plan.md to update Risk Mitigation Status during execution (A4) | 2026-04-30 | 2026-04-30 | E003 |
| C8 | Execute gap-analysis IMPLEMENTATION_PLAN.md — 6 phases, 17 items, all complete (A5) | 2026-04-30 | 2026-04-30 | E003 |
| C9 | Fix /ultraplan → /ultra-plan reference ambiguity in plan-gate and create-plan (A6) | 2026-04-30 | 2026-04-30 | E003 |
| C10 | Update validate-plugin: fix stale counts, add plan template + reference inventory validation | 2026-04-30 | 2026-04-30 | E004 |
| C11 | Reinstall plugin to sync spark-recon (A1) — superseded, not executed as originally framed: spark-recon was rewritten multiple times since (v9.1–9.3); reinstall model was based on an incomplete picture of cache sync (see D19) | 2026-04-30 | 2026-07-08 | E007 |
| C12 | Reinstall plugin to sync gap-analysis changes (A7) — superseded: cache auto-syncs from GitHub `origin/main` (`autoUpdate: true`), confirmed cache already at 9.3.0 = origin tip before any manual action; the actual gap was the local dev clone lagging origin by 1 commit, fixed via `git pull --ff-only` | 2026-04-30 | 2026-07-08 | E007 |
| C13 | Bump personal-plugin version to 9.0.0 (A8) — done via commit `3b9679d`, since surpassed (now 9.3.0) | 2026-04-30 | 2026-04-30 | E003 |
| C14 | Execute the 13 review recommendations R1–R13 (A9) — full 8-phase/35-item plan executed via /implement-plan; released as 10.0.0/4.2.0/1.2.0/3.3.0 | 2026-07-08 | 2026-07-08 | E008–E010 |
| C15 | Force plugin cache to release versions + arch-review smoke test (A10) — cache at 10.0.0/4.2.0/1.2.0 verified on disk; dispatch mechanics green; new definitions restart-gated (load next session) | 2026-07-08 | 2026-07-08 | E011 |
| C16 | Regenerate 5 tool lockfiles for patched CVE versions (plan item 4.2) — 0 pyproject.toml floor changes needed; pip-audit clean ×3 tools; coverage floors held (92.32%/67.03%/96.95%); neither flagged risk (lxml 6.1, pillow 12.2) regressed | 2026-07-12 | 2026-07-12 | E012 |
| C17 | Plan item 4.3 (A11): `.github/dependabot.yml` created (pip ×3 tool dirs + github-actions, grouped weekly); PR #99 opened from `fix/dependency-cves-2026-07`; all 15 CI checks green on ubuntu + windows; squash-merged | 2026-07-12 | 2026-07-12 | E013 |
| C18 | Author `clear-prep` skill (context-clear handoff) + refresh 4-version-stale Current Baseline (prime finding); `claude plugin validate --strict` passed | 2026-07-16 | 2026-07-16 | E015 |
| C19 | Ship personal-plugin 10.3.0 (clear-prep) via PR #108 — squash-merged `df33eef`, all 25 checks green both OSes, cache updated 10.2.0→10.3.0; folded a one-line setuptools-CVE (PYSEC-2026-3447) CI hygiene fix to unblock the audit gate | 2026-07-16 | 2026-07-16 | E016 |
| C20 | Execute the 8-phase arch-review remediation (IMPLEMENTATION_PLAN v9, 32 items) via /implement-plan — one branch+PR+merge per phase (PRs #109/#110/#111/#112/#118/#119/#120/#121), all 18 checks green each after 2 Windows fix rounds; merges `8a2988a→039c2cc→c093904→7fe821d→99d0610→9cf8963→e3bf0a4→0e0895c`. Deferred: SE-11, PLAT-012, PERF-01-wiring + plan scope-outs | 2026-07-16 | 2026-07-16 | E017–E024 |
| C22 | **A2 CLOSED — its tracked issues #125–#131 are all closed** (burndown complete, E026–E033); the row had gone stale on the dashboard while still listed Open. Its standing directive ("all tasks/work are managed from the GitHub issues list") is now carried by A12 | 2026-07-16 | 2026-07-17 | E039 |
| C23 | **Prime findings synced → canonical GitHub backlog (#149–#154)** — 6 issues filed against existing labels using the `[Pn]` convention; tracker went 0 → 6 open, 0 duplicates of closed work. Verification corrections applied *before* filing: repo-level secret scanning + push protection already `enabled` (top risk-agent finding NOT filed — it was wrong); mypy ratchet logic sound, only its comments stale (filed as docs). Gitea's 17 open issues are `davistroy/homeserver` (fleet, incl. 2 P0 rotations) — deliberately out of scope here | 2026-07-17 | 2026-07-17 | E039 |
| C21 | **Dependabot triage (A1)** — 5 merged (#104 google-genai 2.11 MAJOR verified-safe, #113/#114/#115 SHA-pinned action bumps, #116 bpmn2drawio group), 1 closed with root-cause (#117 broken pydantic/pydantic-core lockfile). main `37868fb→6bf2d84`, all tool lockfiles CVE-clean. Course-corrected A1's plan (see D25) | 2026-07-16 | 2026-07-16 | E026 |
| C24 | **A12 CLOSED — executed the #149–#154 plan via `/implement-plan`** (7 phases/16 items, one commit per phase, PR #159 squash-merged `e594158`, all 20 checks green). #149–#154 closed on GitHub; #155/#156 filed for scoped-out work; ADR-0009 added; notebook rotated (E001–E016 archived). Follow-up CONTRIBUTING skills-first cleanup shipped separately (PR #160 `e2f33e5`, E044). Root cause confirmed: 5 of 6 issues were "guards that never gated" | 2026-07-17 | 2026-07-17 | E042–E044 |

---

## Prior Work Summary

This marketplace has been under active development since January 2025, growing from 8 commands and 1 skill to 25+ commands and 20+ skills across two plugins. The project lives at `davistroy/claude-marketplace` on GitHub and is installed into Claude Code via `/plugin marketplace add davistroy/claude-marketplace`.

### Architecture

The marketplace follows Claude Code's plugin discovery conventions with strict structural rules discovered through trial and error (see CLAUDE.md "Verified Operational Rules"). The two plugins — `personal-plugin` (productivity/analysis/planning) and `bpmn-plugin` (BPMN 2.0 workflow modeling) — share a top-level `.claude-plugin/marketplace.json` manifest. Each plugin has its own `plugin.json`, commands directory (flat `.md` files), skills directory (nested `name/SKILL.md`), and optional references, tools, hooks, and agents directories.

### Major Milestones

The project has gone through 8 major versions of personal-plugin and 4 of bpmn-plugin. Key inflection points:

- **v3.x** (Jan 2026): Added research-topic with multi-provider Python orchestrator, visual-explainer with Gemini image generation, ship skill with Gitea support, implement-plan with subagent orchestration
- **v4.x** (Feb 2026): Added prime, review-intent, parallel execution in implement-plan, plan append mode
- **v5.x** (Mar 2026): Breaking deprecations (convert-hooks, setup-statusline, check-updates), shared plan template, comprehensive allowed-tools and error handling across all 36 files
- **v6.x** (Mar-Apr 2026): Added lab-notebook, brain-entry, spark-recon, ultra-plan, arch-review (9-agent team), hooks system, evaluate-pipeline-output, argument-hint and effort frontmatter
- **v7.x** (Apr 2026): Prime reads LAB_NOTEBOOK.md in Phase 0
- **v8.0.0** (Apr 21, 2026): Major modernization — adopted `context:fork`, `isolation:worktree`, `paths:` auto-activation, dynamic `!cmd` injection. Consolidated audit/recon skills (~50% LOC reduction). Removed research-orchestrator Python tool entirely (replaced with 3 parallel subagents). Deleted deprecated help skills and review-pr.

### Current State

*(This subsection is a point-in-time snapshot as of the v8.0.0 modernization, 2026-04-21 — for live version numbers, always check the "Current Baseline" section below, not this paragraph.)* As of 2026-04-21 the marketplace was at v2.0.0, personal-plugin v8.0.0, bpmn-plugin v4.0.0. The v8.0.0 modernization plan (7 phases, 28 work items) completed successfully that day — see `IMPLEMENTATION_PLAN.md` for the current (later) plan and `docs/archive/` for prior plan versions (v4, v5, v6).

Historical note: at the time of Entry 001 (2026-04-30) the installed plugin cache had a stale `spark-recon/SKILL.md` that didn't match the repo version. This was resolved by v9.3.0 (Entry 007, 2026-07-08 baseline check confirmed cache and origin/main agree) — see D19 for how cache sync actually works (GitHub `autoUpdate`, not manual reinstall).

### Planning System

The project has a mature planning workflow: `/ultra-plan` for deep investigation, `/create-plan` for requirements-driven planning, `/plan-improvements` for codebase analysis, and `/implement-plan` for automated execution via subagent orchestration. All share a unified `references/plan-template.md` template. The template was refined today (2026-04-30) with 7 improvements — see Entry 001.

### Key Learnings (from memory files and CLAUDE.md)

Plugin discovery is fragile and fails silently. The five verified operational rules (CLAUDE.md) are non-negotiable: nested skill dirs, `name` in skill frontmatter, no `name` in command frontmatter, no `tools` in plugin.json, no `hooks` in plugin.json. The hooks.json format migration from array to record format (2026-03-31) was another silent failure. These are documented in both CLAUDE.md and the project memory files.

## Current Baseline

- **Marketplace version:** 3.3.0
- **personal-plugin version:** 11.1.0 (23 commands, 28 skills, 10 named agents in `.claude/agents/`, hooks system) — E038: released the post-11.0.0 burndown work (visual-explainer parallel image-gen `--concurrency` #128, cli.py decomposition, coverage 69→93%, mypy 0, command extraction). Prior 11.0.0: arch-review hardening (E017–E025)
- **bpmn-plugin version:** 4.3.1 (2 skills, bpmn2drawio Python tool) — E035: integrated external PR #98 (DI-layout preservation, `auto` default layout mode, geometric lane assignment, data-store cylinders, label/pool fixes); E036: partial-DI guard (`auto`→`preserve` only on complete DI, #143)
- **slide-gen version:** 1.2.0 (9 skills, 7-step presentation pipeline)
- **Git:** clean, main branch, synced with `origin/main` (2026-07-17)
- **Last commit:** `e2f33e5` — docs(contributing): skills-first cleanup (PR #160, E044).
- **2026-07-17 session (prime → issues → ultra-plan → implement-plan → cleanup):** `/prime` surfaced 6 issues (#149–#154), filed as the canonical backlog, planned via `/ultra-plan` (7 phases), executed via `/implement-plan` (PR #159 `e594158`, 7 commits, 20/20 checks). **Net: the repo's "guards that never gated" are now wired + negative-tested** — README-sync guard (`update-readme.py --check`, was a silent no-op that couldn't fail), eval **structural+coverage** linter (was mapping-only), installable pre-commit hook (dead `help.md` check removed). Frontmatter rule reconciled: commands forbid `name` / skills require `name`==dir, now enforced in BOTH `validate.yml` (was dead code) AND the hook + `CONTRIBUTING.md`. Coverage floors moved into each tool's `[tool.coverage.report]` (local `pytest` reproduces the gate; feedback-docx got `branch=true`). Stale mypy "54/98 errors" comments corrected (baselines are 0). **ADR-0009** (D32): ship structural eval linter, defer LLM-judge runner. **Notebook rotated** — E001–E016 → `docs/archive/LAB_NOTEBOOK-E001-E016.md` (1511→822 lines, Decision Log D1–D31 intact, byte-identical move). Pre-existing flaky wall-clock test fixed (cold-start asymmetry → deterministic in-flight counting, E041). CONTRIBUTING.md reframed skills-first (#160/E044). **Backlog now #155/#156** (scoped-out follow-ups). No version bump (autoUpdate). Verification discipline lesson: a guard that can't fail is worse than none — negative-test every new gate.
- **HISTORICAL (prior baseline):** `98439cc` — fix: bpmn2drawio partial-DI guard → **bpmn-plugin 4.3.1** (E036, PR #146, closes #143). Prior: #98 integrated → 4.3.0 (E035, `d2b702e`, contributor Oleksandr Panasenko); **Backlog burndown COMPLETE** (Entries 026–033): all deferred issues #125–#131 + dependabot triage (A1) closed across 9 merged PRs. Key outcomes: visual-explainer cli.py decomposed 1,814→299 across 6 modules (#125); package coverage 69→**93%**, floor gate **65→85** (#127); eval corpus 35→**45**, slide-gen zero→6 skills (#126); memory-bounded parallel image gen, **2.92× speedup**, `--concurrency` re-wired (#128); **both tools mypy-clean** (baselines 101/57→**0**, D24 achieved) (#129); 3 oversized command bodies <500 via references/ (#131); Python 3.10/3.12 advisory CI (#130, D28). google-genai on 2.11 (verified, #104). **#135 CLOSED** (E034/D29 — the 2s `CodeQL` aggregate failure was a GitHub transient isolated to PR #134, non-required, self-resolved; no config change). **#98 MERGED** (E035 → 4.3.0); **#143 FIXED** (E036 → 4.3.1, `98439cc`); **#97 DECLINED** (E037/D31 — vendor remote-MCP plugin, out of scope for a personal marketplace + fails Schema Validation). **Backlog EMPTY** — no open issues, no open PRs. Next work starts from new GitHub issues.
- **Test/type posture (post-burndown):** visual-explainer 894 tests / 93% cov / mypy 0; bpmn2drawio 640 tests / 92.84% cov / mypy 0 (E036); feedback-docx 69 tests / mypy strict-clean. All green on 3.10/3.11/3.12 (3.10/3.12 advisory). 45 behavioral evals mapped.
- **Dependencies:** GitHub Actions SHA-pinned at v6/v7 (checkout/setup-python/setup-node); visual-explainer on google-genai **2.11.0** (verified API-compatible, E026); pydantic 2.13.4 / pydantic-core 2.46.4 (lockstep — do not bump independently, D25/E026)
- **Arch-review remediation (2026-07-16):** 8-phase plan (32 items) COMPLETE. Branch protection now ENFORCED on `main` (14 required checks, PR-required, `enforce_admins=false`); CI gates hardened (per-tool tests linted, mypy count-ratchet, schema-data validation, SHA-pinned actions, pip-audit scoped, xdist); tool code hardened (XXE, SSRF, `.env` 0600, atomic writes); injection surface reduced (Bash scoped in 23 files, 4 fleet skills user-invoke-only); slide-gen honest (ADR-0008 external-dep + preflight); egress/supply-chain policy in SECURITY.md; cruft removed. **No plugin version bumps** — these were hardening changes, not feature releases (personal-plugin stays 10.3.0 / bpmn 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0); autoUpdate propagates content regardless of version. Deferred (documented): SE-11, PLAT-012, PERF-01 wiring, cli.py decomposition, full eval corpus, visual-explainer floor→85%.
- **Plugin cache status:** in sync — marketplace source is GitHub (`davistroy/claude-marketplace`) with `autoUpdate: true` (see D19); cache tracks `origin/main` automatically, independent of local working tree state
- **CI/CD:** GitHub Actions — `test.yml` (pytest matrix, per-tool coverage gates, pip-audit, JSON schema validation), `validate.yml` (plugin.json/frontmatter/version-sync checks, ruff, markdownlint)
- **Platform:** Linux (this session); prior sessions ran Windows 11 — see root CLAUDE.md "Dual environment" section

---

## Experiment Log

> **Earlier entries archived:** E001–E016 (2026-04-30 → 2026-07-16) live in [`docs/archive/LAB_NOTEBOOK-E001-E016.md`](docs/archive/LAB_NOTEBOOK-E001-E016.md). Every decision they established remains in the Decision Log above (D1–D31). Entries below start at E017.

--- New session: 2026-07-16 — /arch-review (9-agent) → /ultra-plan → /implement-plan: executing the 8-phase arch-review remediation, one branch+PR+merge per phase, Sonnet implementer subagents ---

### Entry 017 — Implement-Plan Phase 1: Distribution Governance [ci] [decision] [build]

**Date:** 2026-07-16
**Environment:** Linux VM, Claude Code CLI, main at `29096cc` (plan v9 committed), branch `impl/phase-1-governance`, orchestrator=Opus, implementer subagents=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 1 (the single Critical finding) — enable branch protection on `main` (checks-only, no required review, `enforce_admins=false`) so the CI suite becomes enforced rather than advisory; add a maintainer rollback runbook; add CODEOWNERS + soften SECURITY.md hard SLAs; correct the inaccurate D19 `autoUpdate` documentation (item 1.4). Ship as one PR, merge on green CI.

**Hypothesis:** Enabling branch protection via `gh api PUT` takes effect immediately at the repo level, so this PR (and all subsequent phase PRs) will require the authored-workflow status checks to pass before merge. Required set = the stable authored-workflow job checks (Run Tests ×2 OS, the 3 per-tool test jobs ×2 OS, Validate Plugins ×2, Schema Validation, Lint Markdown, Python Lint & Format, Dependency Security Audit). CodeQL/GitGuardian left advisory-not-required to avoid deadlock on app-managed check contexts (documented in ADR-0007); `enforce_admins=false` is the safety valve. Expect: ADR-0007 (Accepted), `docs/RUNBOOK.md`, `.github/CODEOWNERS`, SECURITY.md SLA softening, D19 correction; all CI green; squash-merge.

**Rollback Plan:** All file work on branch `impl/phase-1-governance` (never main); `git branch -D` reverts pre-merge. Branch protection is API-managed, reversible via `gh api -X DELETE repos/davistroy/claude-marketplace/branches/main/protection`. Every file git-tracked. Post-merge, `git revert <sha>` undoes the docs; protection removed via the DELETE call.

**Actions & Results:**

1. **Item 1.1 (branch protection):** orchestrator ran `gh api PUT .../branches/main/protection` → enabled with 14 required status checks (Run Tests + 3 per-tool test jobs ×2 OS, Validate Plugins ×2, Schema Validation, Lint Markdown, Python Lint & Format, Dependency Security Audit), `required_pull_request_reviews.required_approving_review_count=0` (PR required, no approval — bus factor 1), `enforce_admins=false` (safety valve). CodeQL/GitGuardian left advisory-not-required (app/default-setup contexts). PLAT-001 closed at the infra level. ADR-0007 written by a Sonnet subagent (Accepted).
2. **Item 1.2:** `docs/RUNBOOK.md` (maintainer detect→revert→verify→propagate→user-escape-hatch, ~30 min RTO) + TROUBLESHOOTING.md cross-link (Sonnet subagent).
3. **Item 1.3:** `.github/CODEOWNERS` (`* @davistroy`, ownership-clarity not a review gate) + SECURITY.md SLAs softened to best-effort + RUNBOOK cross-ref (Sonnet subagent).
4. **Item 1.4 (D19 correction):** done by orchestrator — see the D19 row correction note in the Decision Log above.

**Status:** COMPLETE. PR #109 squash-merged as `8a2988a`, all 18 checks green under the newly-enabled branch protection (proving the gate is enforced end-to-end: the protection allowed the merge only after checks passed). Branch protection live on `main` (14 required checks, PR-required 0-approvals, `enforce_admins=false`). The Critical finding PLAT-001 is closed. Local main fast-forwarded 29096cc→8a2988a.
**Duration:** ~25 minutes

---

### Entry 018 — Implement-Plan Phase 2: Tool Security Hardening (Code) [skill] [decision] [debug]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `8a2988a` (branch-protected), branch `impl/phase-2-security`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 2 — close the exploitable-in-code paths: (2.1) harden the bpmn2drawio lxml parser against XXE + cap the `lxml>=4.9.0` floor to `>=5.0,<7`; (2.2) harden visual-explainer's `.env` key write (chmod 600 + warning) and amend ADR-0003 to sanction the local-runtime path (decision D3); (2.3) add an SSRF guard to `concept_analyzer.fetch_url`; (2.4) switch Gemini backoff classification from `str(e)` substring-matching to typed exceptions; (2.5) make checkpoint/JSON writes atomic (temp+`os.replace`, add `schema_version`) and use the full-length cache hash key. Ship as one PR, merge on green CI.

**Hypothesis:** All five are additive/hardening changes to Python tool code with existing test suites and coverage floors (bpmn2drawio 90%, visual-explainer 65%) as the regression guard. Expect: new XXE regression test (parser rejects external SYSTEM entities) and SSRF test (metadata IP blocked) pass; the 585 bpmn2drawio tests + visual-explainer suite stay green at/above floor; `ruff` clean. File-disjoint parallelization: batch1 [2.1 bpmn2drawio, 2.3 concept_analyzer.py, 2.4 image_generator.py] parallel; then [2.2 api_setup.py+ADR-0003, 2.5 checkpoint-writers+concept_analyzer cache-key] — 2.5 sequenced after 2.3 since both touch concept_analyzer.py. Risk: hardened lxml parser could reject legit BPMN using DTDs (low — BPMN rarely does; 585-test suite guards).

**Rollback Plan:** All work on branch `impl/phase-2-security` (never main); `git branch -D` reverts pre-merge. Every file git-tracked; coverage floors + the new security tests guard regressions. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **2.1 (lxml/XXE):** module-level hardened `XMLParser(resolve_entities=False, no_network=True, load_dtd=False, dtd_validation=False, huge_tree=False)` threaded through both `parse`/`fromstring`; `pyproject.toml` floor `lxml>=5.0,<7`; new `test_xxe.py` (3 tests) — **588 passed, 92% coverage**; empirically verified `/etc/hostname` content never leaks (entity unresolved / `BPMNParseError`).
2. **2.3 (SSRF):** `_check_host_is_safe`/`_validate_url_target`/`SSRFError` in `concept_analyzer.py` resolve via `getaddrinfo` and block private/loopback/link-local/reserved/multicast (incl. 169.254.169.254) + non-http(s); `fetch_url_content` disables auto-redirects and re-validates each hop (≤5); new `test_ssrf.py` (23 tests) — **634 passed, 67.9%**.
3. **2.4 (typed backoff):** new `_classify_exception` prefers typed `google.genai.errors` `.code` (429→rate, 5xx→retry) + `httpx.TimeoutException`, string-match fallback retained; 4 new tests — **611 passed, 66%**; `image_generator.py` at 87%.
4. **2.2 (.env + ADR-0003):** `_create_env_file` now `chmod 0600` + explicit plaintext-storage warning (OSError-tolerant); ADR-0003 amended with a "Sanctioned exception: standalone-tool local runtime" section (Status still Accepted); README security note — **634 passed, 68%**.
5. **2.5 (atomic + cache key):** `_atomic_write_text` (temp+`os.replace`) applied to checkpoint/metadata/eval/concepts writers in both `output.py` and the live `cli.py` path; `schema_version` on checkpoints (tolerated-if-absent on load); concept cache key now full SHA-256 (was `[:16]`); 2 new tests incl. interrupted-write-doesn't-corrupt — **636 passed, 68%**.
6. **Orchestrator pre-commit gate:** `uvx ruff@0.14.10 check` surfaced one F841 (unused `family` from the SSRF `getaddrinfo` unpack) + 2 files needing `ruff format` (concept_analyzer.py, output.py) — fixed with `ruff format` + `--fix --unsafe-fixes`; re-verified ruff check + format clean (CI src scope), markdownlint clean. (Same subagents-skip-ruff-format class as E013.)

7. **PR #110 first CI round:** 24/25 green, but **BPMN2DrawIO Tests (windows-latest)** failed at collection — `test_xxe.py` read `Path("/etc/hostname").read_text()` at **module level**, which raises `FileNotFoundError` on Windows (`\etc\hostname` absent), aborting the whole suite. Root cause: a POSIX-only hardcoded path used as the XXE exfil target. Fix: rewrote the test to create a `tmp_path` sentinel file and point the SYSTEM entity at `Path.as_uri()` (valid `file://` on both OSes), removing all module-level filesystem reads; ruff dropped the now-unused `pytest` import. Re-verified on Linux: 3 XXE tests pass, full suite 588 pass / 92%. This is the OS-fidelity value of the windows-latest matrix leg — a Linux-only subagent test check missed it.

**Status:** COMPLETE. PR #110 squash-merged as `039c2cc` (second CI round all 18 checks green after the Windows XXE-test portability fix). All 5 exploitable-in-code paths closed (XXE, plaintext-key, SSRF, brittle backoff, corruptible checkpoints); coverage floors held (bpmn 92%, visual-explainer 68%). Local main fast-forwarded 8a2988a→039c2cc.
**Duration:** ~50 minutes (including the Windows test-portability fix + one CI re-run)

---

### Entry 019 — Implement-Plan Phase 3: Injection-Surface Reduction [skill] [decision] [cleanup]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `039c2cc` (branch-protected), branch `impl/phase-3-injection`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 3 — reduce the prompt-injection "lethal trifecta" surface: (3.1) scope `Bash` narrowly in the skills/commands that currently grant unscoped `Bash` (inventory found **24** files: 14 skills + 10 commands — more than the ~15 estimate); (3.2) separate untrusted-fetch from local-action in the recon/audit skills; (3.3) resolve RI-03 (do spark-audit/jetson-audit SSH into fleet hosts with sudo?) and document the trust boundary in SECURITY.md. Ship as one PR, merge on green CI.

**Hypothesis:** The regression risk here is real and **cannot be runtime-tested** (skills are LLM-interpreted; U2). Mitigation: scope CONSERVATIVELY — for each file, `allowed-tools: Bash(<cmd>:*)` covering the UNION of shell commands its body actually invokes; where a skill genuinely needs unbounded analysis bash (e.g. arch-review), LEAVE `Bash` with a one-line justification and rely on 3.2's fetch/act separation instead of breaking it. Gate = `claude plugin validate --strict` green on all touched plugins + markdownlint. Expect no new CI test failures (frontmatter-only + SECURITY.md doc). Parallel: [3.1-skills, 3.1-commands, 3.3] disjoint file sets; 3.2 sequenced after 3.1 (both touch recon skill files).

**Rollback Plan:** All work on branch `impl/phase-3-injection`; `git branch -D` reverts pre-merge; every file git-tracked; revert per-skill if a scope proves insufficient. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **3.1 (Bash scoping):** 16 skills — 13 scoped to the exact command union (e.g. fleet-health→`Bash(ssh:*),Bash(curl:*)`; new-project→10 scopes; research-topic→5), 3 kept broad with an inline YAML justification because they run genuinely-dynamic scanners (security-analysis ≈9 native audit tools by stack; leak-risk-audit writes+runs ad-hoc Python scans; arch-review's 9 domain subagents run semgrep/bandit/lizard/trivy/etc.). 7 commands scoped (scaffold-plugin→mkdir, validate-plugin→git/sed/gh/base64, clean-repo→git/grep, convert-markdown→pandoc, bump-version→git, arch-synthesize→ls/echo, arch-review-single→mkdir); new-skill had no Bash. All enumerable — zero command carve-outs needed. `claude plugin validate --strict` exit 0.
2. **3.3 (RI-03 resolved):** spark-audit/jetson-audit DO SSH with passwordless sudo (`sudo dmesg`/`sudo tegrastats`/`sudo nvpmodel`/`sudo jetson_clocks`); the fleet `claude` user's sudo set includes root-equivalent `rm/chmod/chown/mount/apt/reboot`. Sharpest finding: **jetson-recon combines untrusted WebFetch/WebSearch (Checks 1-4) + a live SSH read (Check 5) in one skill** — the full trifecta. spark-recon does NOT SSH. SECURITY.md gained a "Fleet recon/audit trust boundary" section making SEC-01 explicit.
3. **3.2 (fetch/act separation):** all 4 fleet skills (spark-recon, jetson-recon, spark-audit, jetson-audit) gained `disable-model-invocation: true` (user-invoke-only — injected content can no longer auto-trigger an SSH/sudo skill) + a "Trust Boundary" section: fetched content is data-only, never determines which commands run; jetson-recon's ordering fixed (untrusted fetch first as data → then a fixed 10-command SSH allowlist). `claude plugin validate --strict` exit 0.

**Findings:** U3 resolved (yes, SSH+sudo). U2 (does scoping break skills?) mitigated by conservative union-scoping + the 3 documented broad carve-outs + `claude plugin validate --strict` green; residual runtime-regression risk accepted (skills are LLM-interpreted, not runtime-testable in CI) — the `disable-model-invocation` change is the highest-value net reduction (4 SSH-capable skills can no longer be injection-triggered at all).

**Status:** COMPLETE. PR #111 squash-merged as `c093904`, all 18 checks green (26 files, +98/−33). Injection surface reduced: 23 files scoped, 4 fleet SSH/sudo skills made user-invoke-only with trust boundaries, RI-03 answered + documented. Local main c093904.
**Duration:** ~40 minutes

---

### Entry 020 — Implement-Plan Phase 4: CI Gate Integrity [ci] [decision] [debug]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `c093904` (branch-protected), branch `impl/phase-4-ci`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 4 — make the now-enforced CI gates correct and complete: (4.1) lint the per-tool `tests/` dirs (fix ~28 hidden ruff errors, extend globs); (4.2) make mypy gate meaningfully (ratchet — see below); (4.3) validate schema *data* + fix `schemas/plugin.json` contradictions; (4.4) SHA-pin GitHub Actions + fix the dependabot false-claim + add concurrency/timeout; (4.5) scope pip-audit to tool deps + de-dup redundant root-suite runs + root coverage. Ship as one PR, merge on green CI.

**Hypothesis:** These edit `.github/workflows/{validate.yml,test.yml}` — the gates protecting every other PR — so a mistake here reddens CI for the whole repo. Run **sequentially** (4 of 5 items touch the same two workflow files; the plan marks Phase 4 Sequential) to avoid collisions. Critical ordering: 4.1 must fix the per-tool test lint errors BEFORE extending the ruff glob (else this PR's CI reddens). **U4 resolved:** mypy on the CI target surfaces **54 errors (bpmn2drawio) + 98 (visual-explainer) = 152** — far too many to zero-out safely here, so 4.2 uses a COUNT-RATCHET (fail only if the error count exceeds a committed per-tool baseline; feedback-docx stays strict at 0), removing `continue-on-error` so the ratchet actually gates against *new* type debt. Reaching 0 is deferred to a separate cleanup (like the flagged-out cli.py decomposition). Baselines must be computed in a CI-matching env (Python 3.11, `pip install -e .[dev]`) to avoid false failures.

**Rollback Plan:** All work on branch `impl/phase-4-ci`; `git branch -D` reverts pre-merge. Workflow edits are git-tracked and revert cleanly. If a workflow change reddens CI, fix-forward on the branch before merge (nothing reaches main until the PR is green). Post-merge `git revert <sha>`.

**Actions & Results:**

1. **4.1 (lint per-tool tests):** fixed 28 ruff errors in `plugins/*/tools/*/tests/` (25 auto I001 import-sort + 3 manual E501) + 19 files reformatted; extended validate.yml ruff check/format globs to include `plugins/*/tools/*/tests/`. Full-scope ruff check + format clean.
2. **4.2 (mypy count-ratchet):** U4 measured 54 (bpmn2drawio) + 98 (visual-explainer) = 152 existing errors — too many to zero-out here, so a ratchet: `.mypy-baseline` files (57 / 101 = measured+3 margin), test.yml mypy steps rewritten to fail only if count > baseline, `continue-on-error` REMOVED (now actually gates net-new type debt); feedback-docx stays strict. Full cleanup deferred (separate plan).
3. **4.3 (schema-data validation):** `schemas/plugin.json` fixed — removed the forbidden `tools` property, tightened version pattern to `^\d+\.\d+\.\d+$`, `additionalProperties:false` (after confirming all 9 real keys are declared). New `scripts/validate_schema_data.py` validates the 3 manifests against the schema, wired into the `Schema Validation` job. U6 clean (current manifests pass). Noted follow-up: `schemas/command.json` has `additionalProperties:false` without `argument-hint`/`effort` — enforcing as-is would fail every command, so left un-enforced (out of scope).
4. **4.4 (SHA-pin + concurrency/timeout):** `actions/checkout@v4`→`34e1148…`, `setup-python@v5`→`a26af69…`, `setup-node@v4`→`49933ea…` (real SHAs via `gh api`, tag kept as trailing comment for Dependabot); `concurrency: cancel-in-progress` + `timeout-minutes` on all 10 jobs; dependabot.yml's false SHA-pin claim made truthful.
5. **4.5 (scope pip-audit + de-dup):** `Dependency Security Audit` now runs `pip-audit --requirement <lock>` per tool instead of auditing the whole runner env (removes the Entry-016 setuptools-workaround, which was deleted); removed the redundant `pytest tests/integration/` step (the full `pytest tests/` covers it) + added root `--cov` reporting; removed validate.yml's duplicate root-pytest step (job kept 3 substantive steps, name unchanged). **All 10 job names verified byte-for-byte unchanged** (branch-protection required checks depend on job-name identity).
6. **Orchestrator gate:** all 3 workflow/config files YAML-valid; `scripts/validate_schema_data.py` exit 0; ruff full-scope clean; job-name grep confirms `Run Tests (${{ matrix.os }})` etc. intact.

7. **PR #112 first CI round:** 16/18 green; **BPMN2DrawIO + Visual Explainer Tests (windows-latest)** failed. Root cause: GitHub Actions defaults `run:` steps to **PowerShell** on Windows runners, and the new multi-line mypy-ratchet **bash** script (`set +e`, `[ "$ERRORS" -gt "$BASELINE" ]`, `if…then`) is not valid PowerShell (`ParserError: Missing '(' after 'if'`). The pre-existing single-command `run:` steps (pip/pytest) work under pwsh, which is why only the two NEW ratchet steps broke. Fix: added `shell: bash` to both ratchet steps (Git bash on Windows runners supports the `grep -oP` extraction). ubuntu legs were unaffected (bash default). This is the OS-fidelity value of the windows matrix again (cf. E018 XXE fix).

**Status:** COMPLETE. PR #112 squash-merged as `7fe821d` (second CI round all 18 green after the pwsh→`shell: bash` ratchet fix). CI gates now correct & complete: per-tool tests linted, mypy ratchet gating net-new type debt, schema *data* validated, actions SHA-pinned, pip-audit scoped. All job names preserved. Local main 7fe821d.
**Duration:** ~65 minutes (sequential 5-item phase + one Windows CI fix round)

---

### Entry 021 — Implement-Plan Phase 5: External-Call Robustness [skill] [ci]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `7fe821d` (branch-protected), branch `impl/phase-5-external`, orchestrator=Opus, implementer=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 5 — make the raw-curl research/brain-entry integrations fail fast and cleanly: (5.1) add `--max-time`/`--connect-timeout` to every curl; (5.2) check HTTP status / non-empty job ID after submit, fast-fail, honor 429/Retry-After; (5.3) move the Gemini research key from URL query to `x-goog-api-key` header + include a run TIMESTAMP in `/tmp` response filenames. Ship as one PR, merge on green CI.

**Hypothesis:** All 3 items edit the SAME file (`plugins/personal-plugin/references/research-provider-protocols.md`, plus brain-entry for 5.1), so ONE subagent does all three sequentially to avoid a self-collision (not 3 parallel). These are markdown instruction-file edits (curl invocations inside the protocol reference) — no Python, no tests exercise them, so CI risk is limited to markdownlint + plugin validation. Expect all 18 checks green.

**Rollback Plan:** All work on branch `impl/phase-5-external`; `git branch -D` reverts pre-merge; instruction-file edits are git-tracked. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **5.1 (timeouts):** `--connect-timeout 10` on every curl; `--max-time` tuned per call (600s Anthropic sync extended-thinking, 60s submits/POSTs, 30s poll GETs); poll GETs get `--retry 2` (idempotent), submits don't (avoid duplicate jobs).
2. **5.2 (status/error):** every submit captures curl exit code + HTTP status via `-w '%{http_code}'` and fast-fails on curl error / HTTP ≥400 / empty ID BEFORE any poll loop (kills the ~30-min-poll-a-nonexistent-job failure mode); Anthropic response checked for `error` before parse; poll loops treat missing `status`/`state` as error and honor HTTP 429 `Retry-After` (via `-D` header dump, 30s fallback).
3. **5.3 (key + temp files):** Gemini `?key=` moved to `x-goog-api-key` header (submit + poll); all `/tmp` response + header-dump filenames now include `[TIMESTAMP]` (reused the doc's existing placeholder, no new var).
4. **Gate:** `claude plugin validate --strict` exit 0; markdownlint 0 errors on both files; all 6 embedded bash blocks pass `bash -n`.

**Status:** COMPLETE. PR #118 squash-merged as `99d0610`, all 18 checks green (4 files, +212/−37). The raw-curl research/brain-entry legs now fail fast (timeouts + submit-status checks) instead of hanging, and the Gemini key no longer rides in the URL. Local main 99d0610.
**Duration:** ~20 minutes

---

### Entry 022 — Implement-Plan Phase 6: slide-gen Integrity [plugin] [decision] [skill]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `99d0610` (branch-protected), branch `impl/phase-6-slidegen`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 6 (decision D2: declare external, do NOT vendor) — (6.1) formally declare slide-gen an external-dependency plugin + add an `sg` preflight health-check + ADR-0008; (6.2) fix the `plugin.json` homepage (points at the wrong repo) + add prominent External-Dependency sections to slide-gen + root READMEs; (6.3) add CHANGELOGs to slide-gen + bpmn-plugin + cross-reference the two divergent Gemini image paths. Ship as one PR, merge on green CI.

**Hypothesis:** **U1 RESOLVED — the `slide-generator` engine repo is PRIVATE** (`gh repo view` → visibility PRIVATE), so slide-gen is genuinely owner-only today (confirms SA-001). ADR-0008 and the preflight must state this honestly rather than implying public installability: the preflight (`sg --version` early-exit with a clear "slide-gen requires the private slide-generator engine; not available to non-owners" message) is the key deliverable so a fresh non-owner install fails loudly-and-clearly instead of cryptically mid-pipeline. All changes are additive docs + skill-body preflight + a new ADR — no Python, so CI risk is markdownlint + plugin validation. Parallel: [6.1, 6.3] disjoint (6.1: slide-gen README/sg-full-workflow/ADR-0008; 6.3: CHANGELOGs + sg-generate-images), then 6.2 (plugin.json + slide-gen README + root README) after 6.1 (shared slide-gen README).

**Rollback Plan:** All work on branch `impl/phase-6-slidegen`; additive; `git branch -D` reverts pre-merge. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **6.1 (declare external + preflight + ADR-0008):** `docs/adr/0008-slide-gen-dependency-model.md` (Accepted) documents the external-dependency decision honestly — slide-gen is owner-only until `slide-generator` is public; alternatives (vendor / deprecate / status-quo) rejected with reasons. slide-gen README gained a prominent "External Dependency (REQUIRED)" section; `sg-full-workflow` gained a fail-fast Preflight (Step 0: `sg --version` → clear owner-only message if absent); one-line preflight bullets added to the 7 pipeline skills.
2. **6.3 (CHANGELOGs + Gemini cross-ref):** new `plugins/slide-gen/CHANGELOG.md` + `plugins/bpmn-plugin/CHANGELOG.md` (Keep-a-Changelog, backfilled from git history — the two-tier versioning is now fully instrumented); `sg-generate-images` gained a "Related Gemini Image Path" note (SA-004: the two Gemini paths are intentionally separate; changes must be applied in both). Verified 6.1's preflight bullet + 6.3's note BOTH survived on the shared `sg-generate-images/SKILL.md` (no lost update).
3. **6.2 (homepage + root README):** `plugins/slide-gen/plugin.json` homepage fixed `slide-generator`→`claude-marketplace` (RISK-01/PLAT-013); root README gained a slide-gen external-dependency note. `marketplace.json` carries no per-plugin `homepage`, so the version-sync check was correctly NOT extended (nothing to compare — INT-05 partially N/A).
4. **Gate:** `claude plugin validate --strict` green on slide-gen + bpmn-plugin; markdownlint clean on all touched files; JSON valid.

**Status:** COMPLETE. PR #119 squash-merged as `9cf8963`, all 18 checks green. slide-gen now honest: external-dependency declaration (ADR-0008), fail-fast preflight, fixed homepage, CHANGELOGs for all 3 plugins. U1 resolved (private repo → owner-only). Local main 9cf8963.
**Duration:** ~30 minutes

---

### Entry 023 — Implement-Plan Phase 7: Governance Docs, Egress Policy & Hygiene [config] [cleanup] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `9cf8963` (branch-protected), branch `impl/phase-7-docs`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 7 — close the documentation/policy debt + remove cruft: (7.1) SECURITY.md data-egress/confidentiality policy; (7.2) SECURITY.md supply-chain controls section; (7.3) resolve the ADR-0004 help-skill drift; (7.4) cruft removal (GITHUB_ERRORS.md ×2, gap-analysis, placeholder uv.lock, stale ruff.toml entry) + oversized command bodies → references; (7.5) skill error sections. Ship as one PR, merge on green CI.

**Hypothesis:** Additive docs + deletions + config, so CI risk is markdownlint + plugin validation. **DEFERRED: PLAT-012 (7.5's CI Python-matrix expansion 3.10/3.12)** — adding `python-version` to the matrix would change the job check names (e.g. `Run Tests (ubuntu-latest)` → `(ubuntu-latest, 3.11)`), which are branch-protection REQUIRED checks — renaming them would deadlock merges until the protection config is updated in lockstep. That coordinated change is out of scope for a clean phase; 7.5 does only the skill error-section work (SE-10). Batching: 4 disjoint-file subagents — [A] 7.1+7.2 (both edit SECURITY.md, one subagent), [B] 7.3 (docs/adr/0004 + generate-help.py), [C] 7.4 (root cruft + commands/), [D] 7.5 (skills/ error sections). `uv.lock` removal note: it's gitignored but tracked (committed before the ignore rule), so `git rm --cached` + `rm`.

**Rollback Plan:** All work on branch `impl/phase-7-docs`; `git branch -D` reverts pre-merge; deletions recoverable via git history. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **7.1+7.2 (SECURITY.md):** added a "Data Egress & Confidentiality Policy" section (classification tiers, NEVER-send list, tool→provider egress table, provider-DPA pointers with a verify-before-regulated-data caveat) + a "Supply-Chain Controls" section (Dependabot/pip-audit/CodeQL/GitGuardian/branch-protection, each with cadence + enforcement); sections renumbered, cross-referenced. Subagent fact-checked the evidence-trail citations (E016 is clear-prep, not the pip-audit scope — corrected to E017/E020).
2. **7.3 (ADR-0004 help drift):** amended ADR-0004 (2026-07-16 amendment) to drop the per-plugin help-skill requirement (superseded by ADR-0006 skills-first + native `/help`; no plugin ever implemented it); deleted the dead `scripts/generate-help.py`. Follow-up cleanup subagent removed the now-stale live references: `scripts/pre-commit` help.md-sync block (Check 5), CONTRIBUTING.md, TROUBLESHOOTING.md §6.2, docs/PLUGIN-DEVELOPMENT.md (checklist/PR-template/mistakes) — `bash -n` clean; only historical refs remain (CHANGELOG, docs/archive).
3. **7.4 (cruft + config):** deleted `GITHUB_ERRORS.md` (root + docs/archive/), `gap-analysis-2026-04-30.md`, root placeholder `uv.lock` (verified 52 bytes, zero packages; real visual-explainer uv.lock untouched); removed stale `research_orchestrator` from `ruff.toml` isort; removed the now-dead `GITHUB_ERRORS.md` markdownlint ignore from `.markdownlint.json`. **SE-11 (oversized command-body extraction) DEFERRED** — mechanically refactoring 3 large frozen-legacy commands (validate-plugin 675 / implement-plan 573 / new-skill 530) without runtime tests is disproportionate risk for a Low finding.
4. **7.5 (skill error sections):** added tailored `## Error Handling` sections to **14** skills that lacked one (SE-10 estimated ~8) — each 5-6 bullets on that skill's real failure branches. **PLAT-012 (CI Python-matrix 3.10/3.12) DEFERRED** — adding `python-version` to the matrix renames the branch-protection required checks (deadlock risk); needs a coordinated protection update, out of scope.
5. **Gate:** `claude plugin validate --strict` green ×3 plugins; markdownlint clean on all touched .md; ruff.toml (TOML) + .markdownlint.json (JSON) parse OK; `bash -n scripts/pre-commit` clean.

**Status:** COMPLETE. PR #120 squash-merged as `e3bf0a4`, all 18 checks green. Egress/supply-chain policy documented, ADR-0004 help drift resolved + dead script/refs removed, cruft deleted, 14 skills gained error-handling. SE-11 + PLAT-012 deferred. Local main e3bf0a4.
**Duration:** ~40 minutes

---

### Entry 024 — Implement-Plan Phase 8: Test/Eval Safety Net (scoped) [skill] [ci] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `e3bf0a4` (branch-protected), branch `impl/phase-8-tests`, orchestrator=Opus, implementers=Sonnet

**Objective:** Execute IMPLEMENTATION_PLAN.md Phase 8 (final) — (8.1) resolve the dead `generate_batch`/`--concurrency` PERF-01 finding; (8.2) fix the contradictory/conditional test skips (QA-07 key-gated mocked full-pipeline test, QA-08 runtime-conditional resize skips); (8.3) add an eval-mapping CI check (every `evals/*.eval.md` maps to a live skill/command) + targeted evals for the 4 highest-blast-radius skills; (8.4) add `pytest -n auto` to per-tool CI jobs. Ship as one PR, merge on green CI.

**Hypothesis:** **8.1 decision: REMOVE, not wire.** The `--concurrency` flag + `asyncio.Semaphore` + `generate_batch()` are inert (the CLI runs images serially); wiring them up (parallel images + a memory cap per PERF-05) is a genuine async rewrite better suited to a dedicated effort with the flagged-out cli.py decomposition — for this scoped phase, REMOVING the inert knob closes PERF-01 honestly with zero regression risk (removing dead code + an advertised-but-inert flag; PERF-05 becomes moot). Batching: 8.1 first (src: image_generator.py/cli.py), then [8.2 test files, 8.3 evals+validate.yml+script, 8.4 test.yml+pyproject×3] parallel (disjoint file sets). Coverage floors (bpmn 90 / visual-explainer 65 / feedback 95) + `-n auto` xdist coverage-aggregation are the CI guards; expect green.

**Rollback Plan:** All work on branch `impl/phase-8-tests`; `git branch -D` reverts pre-merge; coverage floors guard regressions. Post-merge `git revert <sha>`.

**Actions & Results:**

1. **8.1 (PERF-01, REMOVE):** deleted the inert `generate_batch()`, `asyncio.Semaphore`, `max_concurrent`, and the `--concurrency` CLI flag + `GenerationConfig.concurrency` field; removed the corresponding tests. Serial generation path untouched. 624 passed, 68% (coverage UP — dead code removed). PERF-05 (concurrent-buffer memory) now moot. Stale `--concurrency` README refs cleaned separately.
2. **8.2 (QA-07/QA-08):** un-gated `test_full_pipeline_success` from `ANTHROPIC_API_KEY` (root cause: `concept_analyzer` has a key-presence guard before the mocked client — satisfied with the `mock_env_with_api_keys` fixture, verified no real network call with `env -u`); made the resize test deterministic (`max_size_bytes` forces the branch) + removed the Pillow-absent skip (hard dep). 64 previously-skipped→run, full suite 626 passed.
3. **8.3 (QA-03 subset/SA-006):** `scripts/check_eval_mapping.py` (every `evals/*.eval.md` → live skill/command; `cross-cutting`+`maps_to` escape hatch) wired into validate.yml's `plugin-validate` job; removed 3 drifted evals (help, new-command, and a bonus `validate-and-ship`→`release-plugin` rename); added 4 high-blast-radius evals (release-plugin, arch-review, ultra-plan, leak-risk-audit). 35 evals all map; verified exits 1 on injected drift.
4. **8.4 (PERF-06):** `pytest-xdist>=3.5` added to all 3 tools' `[dev]` extras + `-n auto` on the 3 per-tool CI jobs; all xdist-safe locally (bpmn 588/92.27%, visual-explainer 624/67.74%, feedback 69/96.95%). Job names unchanged.
5. **Combined gate:** visual-explainer 626 passed/68% (8.1+8.2 merged state); eval-mapping exit 0 (35); schema-data exit 0; ruff full-scope clean; test.yml + validate.yml YAML valid + all job names intact; `claude plugin validate --strict` OK. **PERF-01 wiring deferred** (chose safe remove).

**Status:** COMPLETE. PR #121 squash-merged as `0e0895c`, all 18 checks green (mypy ratchet held after the dead-code removal; xdist parallelism worked cross-OS). This was the final phase — **the entire 8-phase arch-review remediation (32/32 items) is now merged to `main`.**
**Duration:** ~55 minutes (Phase 8: 4 items + README cleanup, single CI round — no fix needed)

**Remediation retrospective (Entries 017–024):**
- **Outcome:** 1 Critical + 14 High + the load-bearing Mediums/Lows closed across 8 PRs, each independently CI-gated and squash-merged. `IMPLEMENTATION_PLAN.md` `Completed: 2026-07-16` (v9 → will be archived as v9 by the next plan).
- **What worked:** per-phase branch+PR+merge kept blast radius small and let branch protection (enabled in Phase 1) gate every subsequent phase — the governance-first ordering paid off literally. Conservative choices (mypy ratchet not cleanup, Bash union-scoping with documented carve-outs, remove-not-wire for PERF-01, defer PLAT-012/SE-11) avoided regressions on changes that couldn't be runtime-tested.
- **Recurring failure class:** the **windows-latest matrix** caught 2 defects a Linux-only check missed — a `/etc/hostname` XXE test (E018) and a PowerShell-vs-bash mypy-ratchet step (E020). Lesson reinforced: any new multi-line CI `run:` step needs `shell: bash`; any test with an OS-specific path needs a portable fixture (`tmp_path`/`Path.as_uri()`). See [[ci-learnings]].
- **Branch-protection self-consistency:** required checks are keyed by JOB NAME, so every workflow edit (Phases 4, 8) had to preserve job names byte-for-byte; the Python-matrix expansion (PLAT-012) was deferred precisely because it would rename them.
- **Open follow-ups (deferred, not lost):** SE-11 (oversized-command extraction), PLAT-012 (CI Python matrix + coordinated protection update), PERF-01 wiring (parallel image gen + memory cap), and the plan's explicit scope-outs (cli.py decomposition, full 39-skill eval corpus, visual-explainer floor→85%), plus a possible coordinated version bump to signal the hardening release.

---

### Entry 025 — Release personal-plugin 11.0.0 (arch-review hardening) [plugin] [build] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `689842c` (branch-protected), branch `release/personal-plugin-11.0.0`, personal-plugin v10.3.0 pre-release

**Objective:** Bump personal-plugin **10.3.0 → 11.0.0** (MAJOR) to signal the arch-review hardening as a proper release, rather than shipping materially-changed skills/tools under the same 10.3.0. Lockstep plugin.json + marketplace.json bump; CHANGELOG 11.0.0 sections in root + plugin changelogs summarizing Entries 017–024. Merge on green CI, update installed cache.

**Hypothesis:** MAJOR is the correct SemVer tier because the remediation changed user-facing/interface behavior: visual-explainer's `--concurrency` CLI flag was REMOVED (8.1); ~15 skills' + 7 commands' `allowed-tools` were narrowed (3.1) — a capability-grant change; 4 fleet skills gained `disable-model-invocation: true` (3.2) — they're no longer model-triggerable; tool internals hardened (XXE/SSRF/`.env`/atomic writes). Only personal-plugin is bumped (bpmn-plugin 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0 unchanged — marketplace_version is not bumped for single-plugin updates per CLAUDE.md). Expect `claude plugin validate --strict` exit 0, version-sync gate green (plugin.json == marketplace.json == 11.0.0), all 18 CI checks green under branch protection, squash-merge, cache update 10.3.0→11.0.0.

**Rollback Plan:** All work on branch `release/personal-plugin-11.0.0`; `git branch -D` reverts pre-merge. Version/CHANGELOG edits git-tracked. Installed cache is rebuildable API-managed state (D19) — `claude plugin update personal-plugin@troys-plugins` re-syncs. Post-merge `git revert <sha>`.

**Actions & Results:**

1. Branch created; Entry 025 logged (this entry) before any commit.

2. Bumped plugin.json + marketplace.json 10.3.0→11.0.0 (version-sync gate green); wrote `## [11.0.0]` MAJOR sections into root + plugin CHANGELOGs (Changed-breaking / Security / Added / Fixed / Removed). `claude plugin validate --strict` exit 0.
3. Committed, opened **PR #123**, all 18 checks green under branch protection, squash-merged as **`fbb1437`**; local main fast-forwarded 689842c→fbb1437.
4. Installed cache: `claude plugin update personal-plugin@troys-plugins` → 10.3.0→11.0.0 (restart-gated; new definitions load next session).

**Status:** COMPLETE. personal-plugin **11.0.0** live on main (`fbb1437`), plugin.json == marketplace.json == 11.0.0; the arch-review hardening is now a tagged-by-version release. bpmn-plugin 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0 unchanged. Current Baseline updated below.
**Duration:** ~15 minutes

--- New session: 2026-07-16 — post-11.0.0 backlog burndown. User directive: prioritize the whole GitHub-issue backlog (dependabot PRs + deferred #125–#131) and work through it autonomously, one item at a time, stopping only when blocked or finished. This entry covers Action Item A1 (dependabot triage). ---

### Entry 026 — Dependabot triage: 6 open dependency PRs [ci] [decision] [build]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `37868fb` (branch-protected, 14 required checks, `enforce_admins=false`), personal-plugin 11.0.0 / bpmn 4.2.0 / slide-gen 1.2.0 / marketplace 3.3.0. Open dep PRs: #113/#114/#115 (GitHub Actions), #116 (bpmn2drawio group), #117 (visual-explainer group), #104 (google-genai 1.75→2.11 MAJOR).

**Objective:** Clear the dependabot PR queue (A1). Merge safe bumps, resolve the one blocked check, and correctly dispose the risky google-genai major bump.

**Hypothesis (with A1 CORRECTION):** A1's original plan was to CLOSE #113/#114/#115 on the premise they "conflict with Phase-4 SHA-pinning." **Investigation refuted that premise:** these actions are SHA-pinned with a trailing `# vN` comment, and each dependabot PR updates *both* the pinned SHA *and* the comment (e.g. `actions/setup-python@ece7cb06…  # v6.3.0`) — it preserves the SHA-pinning discipline exactly. All three are `CLEAN` (14/14 checks green). So the corrected disposition is **MERGE #113/#114/#115**, not close. #116 (bpmn2drawio patch/minor group) is `CLEAN` → merge. #117 (visual-explainer group) is `BLOCKED` solely by a failing **Dependency Security Audit** (pip-audit) — the other 14 checks pass; hypothesis is the audit is stale/transient (branch predates a main-side scope/ignore) → rebase onto current main and re-run, merge if green. #104 (google-genai **1.75→2.11 MAJOR**) is `CLEAN` in CI but tests are fully mocked (cannot catch API breaks): typed-error contract VERIFIED intact in v2.11.0 (`APIError.code:int`, `ClientError`/`ServerError` subclasses all present at the v2.11.0 tag), but broader API surface (`genai.Client`, `types.HttpOptions/ImageConfig/GenerateContentConfig`, `client.models.generate_content`, response `.parts`/`.candidates`) is under source-level verification by a subagent → merge only if that returns SAFE, else HOLD with a documented reason. Success = green main after each merge, no CI regression, clean queue.

**Rollback Plan:** Each dependabot merge is a squash/merge commit on main → `git revert <sha>` via a follow-up PR (branch-protected, so revert is itself a PR). Closing a PR is reversible (reopen). #104 HOLD is a no-op. This Entry 026 + the A1/A2 Action-Item and Current-Baseline doc edits land via a small docs PR on branch `docs/session-2026-07-16-triage`; `git branch -D` reverts pre-merge.

**Actions & Results:**

1. Entry 026 logged (this entry) before any merge. Verified branch protection: `strict_up_to_date=false` (no rebase needed between merges), `required_approving=0`, `enforce_admins=false` → owner can merge on green checks.
2. **#116 / #115 / #113 / #114 → MERGED** (squash). #113/#114/#115 confirmed as correct SHA-pinned bumps (SHA + `# vN` comment both updated), 14/14 green; #116 bpmn2drawio group green. main `37868fb → e8d3317`, no conflicts (the two workflow-file PRs 3-way-merged cleanly).
3. **#104 (google-genai 1.75→2.11 MAJOR) → MERGED** (squash), main `→ 6bf2d84`. Disposition changed from A1's "HOLD" to MERGE after two independent verifications: (a) subagent confirmed the full API surface used by `image_generator.py` — `genai.Client`, `types.HttpOptions(timeout=ms)`, `types.ImageConfig`, `types.GenerateContentConfig(image_config=…)`, `client.models.generate_content`, and response `.parts`/`.candidates`/`inline_data.data`/`finish_reason` — is unchanged at the v2.11.0 tag; the 2.0.0 breaking changes are scoped to the *Interactions API* (changelog: "GenerateContent usage is unaffected"), which this code never touches; typed-error contract (`APIError.code`, `ClientError`/`ServerError`) also intact. (b) Local `pip-audit --python 3.11` on #104's lockfile: resolves cleanly (consistent `pydantic 2.13.4` / `pydantic-core 2.46.4`), "No known vulnerabilities found" against today's advisory DB. pyproject floor widened to `google-genai>=1.0.0,<3.0.0`.
4. **#117 (visual-explainer minor group) → CLOSED.** Root-caused the BLOCKED "Dependency Security Audit": *not* a CVE — a broken lockfile. Dependabot's grouped bump raised `pydantic-core` 2.46.4→**2.47.0** but left `pydantic` at 2.13.4, which pins `pydantic-core==2.46.4` exactly → `ResolutionImpossible` (reproduced locally on Python 3.11, matching CI). pip-audit fails because it can't install the inconsistent set to scan it. Closed with an explanatory comment; #104 regenerates this same lockfile with a consistent pair, so dependabot will re-propose the residual valid minors (anyio 4.14.1→4.14.2, google-auth 2.55.2→2.56.0) against the post-#104 baseline.
5. Post-merge verification: `pip-audit` clean on all three tool lockfiles on main `6bf2d84`; the docs PR carrying this entry runs the full 14-check suite against the merged state (combined verification, since `strict=false` skipped a merged-state re-run).

**What Worked:** Reproducing pip-audit locally via `uvx --python 3.11 pip-audit --requirement <lockfile>` (system `python3-venv` is absent, but `uv` is present) gave a definitive root cause in seconds where the CI logs were unretrievable via `gh run --log-failed`. Verifying a major-bump's real API surface at the pinned source tag (not just the changelog) is what flipped #104 from HOLD to a confident MERGE.

**Findings (course-corrections vs the A1 plan):**
- **A1 was wrong to propose closing #113/#114/#115.** SHA-pinned actions are updated *correctly* by dependabot (bumps both the pinned SHA and the trailing `# vN` comment). They preserve the pin discipline and should merge, not close. See D25.
- **A1's HOLD on #104 was over-cautious given verification is cheap.** Source-tag API verification + local audit resolved it to a safe MERGE. Kept the HOLD discipline (didn't merge blind) but discharged it with evidence.
- **Dependabot grouped updates can split tightly-coupled pins** (`pydantic`/`pydantic-core` are lockstep-versioned). This produces an un-installable lockfile that surfaces as a pip-audit *install* failure, not a vuln. Pattern logged to ci-learnings + CLAUDE.md.

**Status:** COMPLETE. Queue cleared: 5 merged (#104/#113/#114/#115/#116), 1 closed with rationale (#117). main `6bf2d84`, all tool lockfiles CVE-clean, google-genai on 2.11.0. A1 → Completed (C21). External contributor PRs #97/#98 are out of scope for this triage.
**Duration:** ~35 minutes

### Entry 027 — Decompose visual-explainer cli.py god module (#125 / P1) [refactor] [decision] [debug]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `da5d1b6` (branch-protected), branch `refactor/ve-cli-decompose`. visual-explainer cli.py = **1,814 lines**, 37% line coverage (drags package to 68%). Local test env: `uv` venv (Python 3.11) at scratchpad, baseline **626 passed / 0 failed** with google-genai 2.11.0.

**Objective:** Break the 1,814-line `cli.py` god module into cohesive, independently-testable modules WITHOUT changing behavior (#125/P1). This is the keystone that unblocks #127 (raise the package-wide coverage floor 65→85% — cli.py at 37% is the ceiling).

**Hypothesis:** cli.py splits along 6 clean seams (a read-only subagent mapped it): (1) `terminal.py` — console singleton + capability checks (`is_interactive`, `supports_unicode`, `get_console`, `RICH_AVAILABLE`, `_console`, Rich imports); (2) `cli_args.py` — argparse (`_bounded_float/int`, `create_parser`, `__version__`); (3) `io_utils.py` — `_atomic_write_text`; (4) `reporting.py` — all `display_*` + `GenerationProgress` + `estimate_cost` + `prompt_for_*`; (5) `pipeline.py` — the 7 async pipeline/orchestration fns (`_analyze_concepts`, `_generate_prompts`, `_evaluate_and_refine`, `_execute_generation_loop`, `_save_outputs`, `run_generation_pipeline`, `load_checkpoint_and_resume`); (6) `cli.py` remains a thin ~200-line entry layer (import-time side effects + re-exports for the entry contract + `main` + `__main__` guard). Expect: nothing outside cli.py breaks (only `__main__.py` + `[project.scripts]` `visual_explainer.cli:main` import from it, and no sibling imports cli — no circular-import risk); all 626 tests still pass; total coverage ≥68% (unchanged — this PR moves code, doesn't add tests). **The one sharp hazard is `unittest.mock.patch` name-resolution:** `test_cli_extended.py` patches ~30 symbols on `visual_explainer.cli.*`. Contract preserved by (a) consumers referencing cross-module patchable *terminal* symbols module-qualified (`terminal.get_console()`, `terminal.RICH_AVAILABLE`) so one patch point intercepts everywhere; (b) *pipeline* helpers called bare within pipeline.py (same-module patch intercepts); (c) repointing the test patch strings to the new defining module (`terminal.*` / `pipeline.*`) — but KEEPING `cli.GenerationConfig` (×4) and `cli.load_checkpoint_and_resume` (×1) since `main` (stays in cli) uses cli's binding. A mis-repointed patch makes the *real* fn run → the test FAILS loudly (not a silent pass), so the 626-green criterion is trustworthy. Success = 626 pass, coverage ≥68%, test diff is patch-target strings only (zero assertion changes), all 14 CI checks green on both OSes.

**Rollback Plan:** All work on branch `refactor/ve-cli-decompose`; `git branch -D` reverts pre-merge; post-merge `git revert <squash-sha>` via PR. Pure code-move + test-patch-repoint — no schema/data/external-state change. The local `uv` venv is throwaway (scratchpad). Behavior-preservation is verified by the unchanged 626-test suite before each commit.

**Actions & Results:**

1. Read-only map produced (subagent); green baseline (626) captured; Entry 027 logged before any edit.
2. Extraction executed (opus-implementer, verbatim function moves) into `terminal.py` (106), `cli_args.py` (196), `io_utils.py` (35), `reporting.py` (546), `pipeline.py` (817); `cli.py` **1,814 → 299** lines (docstring + import-time side effects + `__all__` re-export contract + `main` + guard).
3. Patch contract preserved as designed: terminal symbols referenced module-qualified (`terminal.get_console()`, `terminal.RICH_AVAILABLE`); pipeline helpers bare within pipeline.py; 9 test patch-string types repointed to `terminal.*` / `pipeline.*`; `cli.GenerationConfig` + `cli.load_checkpoint_and_resume` kept on cli. One extra, honestly-flagged test edit: the `_console` singleton reset alias `import visual_explainer.cli as cli_mod` → `...terminal as cli_mod` (5 sites) — necessary since `_console` moved to terminal; still a pure repoint, no assertion change.
4. **Independent verification (my uv venv, not the subagent's self-report):** full suite **626 passed / 0 failed**, coverage **69%** (≥68); `ruff check src/ tests/` + `ruff format --check` clean; `mypy src/ --ignore-missing-imports` = **97 errors ≤ 101** baseline (`.mypy-baseline`); test diff grep for any changed line NOT referencing `cli`/`terminal`/`pipeline` module paths → **empty** (zero logic/assertion change). End-to-end smoke: `import visual_explainer.cli` still fires import-time `PYTHONIOENCODING=utf-8`; `cli.main.__module__` == `visual_explainer.cli`; all re-exports present; `python -m visual_explainer --help`/`--version` exit 0.
5. Rich-import split (subagent deviation, reviewed & accepted): `terminal.py` imports only `Console`; `Panel`/`Table`/`Prompt`/`Progress` move with their consumers under their existing `try/except ImportError` guards — preserves the "cli importable without Rich" property. The harness's Pyright "could not resolve `.cli_args`/possibly-unbound Panel" diagnostics are IDE-env artifacts (Pyright not using the editable venv); CI runs ruff+mypy+pytest, not Pyright, and all three are green + the package imports/runs.

**Status:** COMPLETE. Committed `40a8f01`, **PR #133** all 14 checks green both OSes (incl. Windows matrix + mypy ratchet), squash-merged **`72c6fdc`**; issue #125 auto-closed. cli.py 1,814→299 lines across 6 modules, 626 tests green, zero behavior change. Coverage floor still 65% (raising to 85% is #127, now unblocked).
**Duration:** ~50 minutes (incl. read-only map + opus implementer + independent verification)

### Entry 028 — Raise visual-explainer coverage floor 65% → 85% (#127 / P3) [test] [ci]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `72c6fdc` (post-#125), branch `test/ve-coverage-85`. Package coverage **69%** (816 line+branch units missed of ~2632). Floor gate: `.github/workflows/test.yml:125` `--cov-fail-under=65` (package-wide `--cov=visual_explainer`). Local uv venv baseline: 626 passed.

**Objective:** Raise the package-wide coverage gate 65 → 85% (#127/P3), enabled by #125's decomposition making cli's former internals independently testable. Write meaningful characterization tests (real assertions, not coverage-gaming), then bump the `--cov-fail-under` floor.

**Hypothesis:** The gap is concentrated in the decomposed modules that inherited cli.py's 37% coverage — reporting.py (157 miss), pipeline.py (154), cli.py/main (52), terminal.py (18), io_utils.py (8) = 389 — plus two pre-existing low modules with test files, concept_analyzer.py (98) and api_setup.py (185). To reach 85% total miss must drop from 816 to ≤~395 (cover ~420 units). Covering the 5 decomposed modules to ~90% (~389) gets to ~84%; adding concept_analyzer top-up clears 85%; api_setup adds margin. Plan: 6 parallel test-writers (sonnet-implementer), each a distinct NEW or appended test file (no cross-conflict), using the rich conftest fixtures (`sample_generation_config`, `sample_concept_analysis`, `sample_image_prompt`, `sample_evaluation_result`, `checkpoint_file`, mock API responses); each self-checks with a unique `COVERAGE_FILE`. I integrate, run the full suite, and bump the floor to the honest achieved number (target ≥85; if genuinely-hard interactive/api paths block a true 85, set the floor to the achieved value and document). Success = full suite green, total coverage ≥85% (or documented honest floor), floor gate raised, all 14 CI checks green.

**Rollback Plan:** All on branch `test/ve-coverage-85`; tests-only + one CI-gate number change (no product-code change) → lowest-risk category. `git branch -D` pre-merge; `git revert` post-merge. If a test-writer produces flaky/gaming tests, they're dropped before commit (I review each new file).

**Actions & Results:**

1. Coverage baseline captured (69%, 626 tests); Entry 028 logged before any test added.
2. 6 parallel sonnet-implementer test-writers dispatched (4 new files for decomposed modules + 2 appends to existing files), each with strict no-coverage-gaming rules and a unique `COVERAGE_FILE`. Results per module: **reporting 14→99%** (test_reporting.py, 61 tests), **pipeline 8→99%** (test_pipeline.py, 30), **cli 50→97%** (test_cli_main.py, 26; complements existing test_cli_extended.py), **terminal 50→91% / io_utils →100%** (test_terminal.py, 25), **concept_analyzer 53→99%** (test_concept_analyzer.py +63 appended), **api_setup 43→98%** (test_api_setup.py +52 appended). +257 tests total.
3. Integration: stripped 2 unused imports (ruff `--fix`), ran `ruff format` on the 6 files (writers hadn't formatted — the CI format gate would've failed). Synced the local uv venv to `.[dev,all]` (docx/pypdf/bs4/xdist) to MIRROR the CI job's install (`pip install -e ".[dev,all]"`, test.yml:121) so the new SSRF/docx/pdf/httpx tests run under CI-identical deps.
4. **Verified with the exact CI command** (`pytest tests/ -n auto --cov=visual_explainer --cov-branch --cov-fail-under=85`): **883 passed, total coverage 93.29%**, "Required test coverage of 85% reached", gate exit 0. `ruff check` + `ruff format --check` clean. Every module ≥78% (lowest: prompt_generator 78; the 6 targeted modules 91–100%). Uncovered remainder is import-time optional-dep guards + `__main__` script-entry lines (documented per module) + one Windows-only ctypes branch (unreachable on Linux).
5. Bumped the floor gate `test.yml:125` `--cov-fail-under` **65 → 85**. Chose 85 (the issue's target) over a tighter 90: actual 93.29% leaves 8pts headroom, well above cross-OS coverage variance (~0.2%, from platform-branch differences like terminal's Windows ctypes path), so the Windows runner also clears 85 without flakiness; future work can ratchet higher (ratchet philosophy per D24).

6. Committed `abce39a`, opened **PR #134**. **Windows-latest CI caught 2 OS-specific test defects Linux missed** (the documented Windows-matrix value): `test_terminal.py::…test_fallthrough_to_legacy_returns_false` and `test_api_setup.py::…test_ctypes_fallback_returns_false_on_non_windows_ctypes` both `assert supports_unicode() is False` but got `True` on Windows. **Root cause:** the writers (running on Linux) relied on `ctypes.windll` being *absent* (→ AttributeError → False); on real Windows `ctypes.windll` exists and `GetConsoleOutputCP()` returns 65001 (UTF-8) → `True`. Windows coverage itself was fine (93.21% > 85). **Fix:** mock `ctypes.windll` (`create=True`) so `GetConsoleOutputCP` returns a legacy code page 437 (non-UTF8) → deterministically `False` on any host OS; renamed the api_setup test to `test_ctypes_legacy_codepage_returns_false`. (CodeQL's 2s "fail" is a non-required check — ignored.) Re-verified locally: 883 passed, 93.27%, ruff clean.

**Status:** COMPLETE. Fix committed `e033577`, PR #134 CI green both OSes, squash-merged **`2cb6fed`**; issue #127 auto-closed. Coverage 69→**93%**, floor gate **65→85** live on main. Filed **#135** (CodeQL default-setup fails 2s on every PR — non-required/non-blocking, low-pri hygiene). Reinforces standing rule: any test touching an OS-specific path needs a portable fixture (fully mock the platform probe).
**Duration:** ~55 minutes (6 parallel test-writers + integration + 1 Windows-portability fix round)

### Entry 029 — Grow the behavioral eval corpus (#126 / P2) [test] [ci]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `2cb6fed`, branch `test/eval-corpus-expansion`. Corpus already at 35 evals (14 skills + 21 commands); `check_eval_mapping.py` (stdlib) enforces every eval maps to a live skill/command.

**Objective:** Add behavioral evals for the next ~8–10 high-traffic skills that lack a dedicated eval (#126/P2, arch-review QA-03/SA-006), keeping `check_eval_mapping.py` green and following the established `.eval.md` format.

**Hypothesis:** The gap (computed: skills whose name is not a `command:`/`maps_to:` target of any eval) is 9 personal-plugin + 9 slide-gen skills; bpmn-plugin already has coverage (the issue's "bpmn zero" is stale). Highest-value tranche = **slide-gen ×6** (sg-research/outline/draft/optimize/build/full-workflow — a whole-plugin surface from zero) + **personal-plugin ×4** (clear-prep, new-project, archive-project, wiki — user-facing). 10 new `evals/skills/<name>.eval.md` files, each a real behavioral contract (Purpose/Fixtures/Setup/Scenarios with Must/Should/Must-NOT + Rubric) derived from the actual SKILL.md, `command: <name>` + `type: skill` frontmatter. Written by 4 parallel eval-writers (distinct new files → no conflict). Expect `python3 scripts/check_eval_mapping.py` exit 0, markdownlint clean, all CI green. Success = 10 evals added, mapping-check green, no fixture needed (these skills are self-contained or use their own inputs).

**Rollback Plan:** New-files-only additions in `evals/skills/` on branch `test/eval-corpus-expansion`; `git branch -D` pre-merge, `git revert` post-merge. Zero product-code/CI-gate change (pure eval docs + no changes to `check_eval_mapping.py`).

**Actions & Results:**

1. Gap computed, format internalized (ship.eval.md template + README), Entry 029 logged before any eval written.
2. 4 parallel sonnet-implementer eval-writers, each deriving contracts from the actual SKILL.md (not invented). **10 new `evals/skills/*.eval.md`:** slide-gen — sg-research/sg-outline/sg-draft (6 scenarios each), sg-optimize/sg-build/sg-full-workflow (6–7 each, incl. fail-fast preflight + mid-pipeline-halt + missing-artifact); personal-plugin — clear-prep (5), new-project (6), archive-project (10, incl. 2 protect-unrecoverable-work failure scenarios), wiki (11, all sub-ops: ingest/lint/query/propagate + layout detection). Writers correctly adapted to `disable-model-invocation: true` (new-project, archive-project → no proactive-trigger scenario).
3. **Independent verification:** `python3 scripts/check_eval_mapping.py` → "45 eval file(s) all map to a live skill or command" (exit 0); exactly 10 new files, all with correct `command: <name>` + `type: skill` frontmatter; `markdownlint-cli` clean on all 10. Quality spot-check (clear-prep.eval.md) confirmed a real behavioral contract with accurate Must/Should/Must-NOT + rubric, not boilerplate — even encodes the clear-prep-vs-new-project boundary.

**Status:** COMPLETE. Committed `e4d3fc1`, **PR #136** all checks green, squash-merged **`ddd5006`**; issue #126 auto-closed. Corpus 35 → 45 evals; slide-gen zero → 6-skill coverage. Docs-only.
**Duration:** ~20 minutes (4 parallel eval-writers + verification)

### Entry 030 — Wire parallel image generation with a memory cap (#128 / P4, PERF-01) [refactor] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `ddd5006`, branch `perf/ve-parallel-image-gen`. visual-explainer serial path: `pipeline._execute_generation_loop` runs a serial `for prompt in prompts:` loop; each image runs its own generate→evaluate→refine attempt chain. Local uv venv (883 tests green).

**Objective:** Re-introduce real cross-image parallelism with a memory cap (PERF-01/PERF-05) so multi-image runs aren't fully serialized — bounded ≤3 concurrent (per PERF-05), RSS under the 1.5 GB ceiling, with a re-wired `--concurrency` knob (the inert flag was removed in Phase 8/8.1).

**Hypothesis:** Real parallelism is achievable because `image_generator.generate_image` already releases the event loop — `_attempt_generation` runs the blocking google-genai call via `loop.run_in_executor(None, self._generate_sync, …)` — so `asyncio.gather` over per-image tasks runs `_generate_sync` in worker threads concurrently. Design: (a) extract the per-image body of `_execute_generation_loop` into an async `_generate_single_image(...) -> (ImageResult, api_calls)`; (b) add `concurrency` to `GenerationConfig` (default 3, ge=1 le=8) + `--concurrency` in cli_args + thread through `from_cli_and_env` and `main`; (c) in `_execute_generation_loop`, effective = `min(config.concurrency, len(prompts))` — if 1, keep the exact serial path + full `GenerationProgress` live spinner (zero behavior change); if >1, `asyncio.Semaphore(effective)`-bounded `gather` (gather preserves input order → results already sorted by image_number). Per-image `api_calls` summed from task returns (no shared-counter race; the loop's own counter, not the generator's `_api_call_count`). Concurrent-mode progress: a concurrency-safe reporter (per-image start/complete lines, no shared live per-attempt render state) since `GenerationProgress`'s live spinner is single-active-image. Memory bound = the semaphore capping concurrent in-flight 4K buffers. Success = existing 883 tests still green (serial path unchanged), new tests prove (i) concurrent path returns correctly-ordered results, (ii) the semaphore bound is actually enforced (a tracking mock asserts observed max-concurrency ≤ limit), (iii) api_calls summed correctly; a benchmark with a mocked sleeping `generate_image` shows concurrency=3 wall-clock < serial; mypy ≤ baseline, ruff clean, 14 CI checks green.

**Decision (D27):** default `concurrency=3` (parallel-by-default for multi-image runs), not serial-by-default. Rationale: the feature's entire value is wall-clock reduction; 3 concurrent 4K JPEG buffers (~10-30 MB each) stay far under the 1.5 GB ceiling; rate-limit spikes are already handled by the retry/backoff path (`_classify_exception` 429 → `_should_retry`). `--concurrency 1` restores exact serial behavior. Alt: default 1 (opt-in) — rejected (feature dormant by default, low value); unbounded gather — rejected (violates the 1.5 GB ceiling with 4K buffers).

**Rollback Plan:** All on branch `perf/ve-parallel-image-gen`; `git branch -D` pre-merge, `git revert` post-merge. `--concurrency 1` is a runtime escape hatch to the exact prior serial behavior even post-merge. Pure code + tests; no schema/data/external-state change.

**Actions & Results:**

1. Serial path + async-executor analysis complete (gather will genuinely parallelize); Entry 030 + D27 logged before any edit.
2. Implemented (opus-implementer): `concurrency` field on `GenerationConfig` (default 3, ge=1 le=8) + `to_metadata_dict`; `--concurrency` `_bounded_int(1,8)` flag; threaded through `from_cli_and_env` + both `main`/resume call sites; extracted `_generate_single_image(...)` (per-image body, verbatim); `_execute_generation_loop` serial/concurrent split (`effective = min(concurrency, len(prompts))`, serial if ≤1 else `Semaphore(effective)`-bounded `gather`, prompt-ordered results, api_calls summed per-task); new `ConcurrentGenerationProgress` reporter driven polymorphically (per-attempt spinner gated to serial only — the unsafe shared-live-render path).
3. **Independent verification:** full suite **894 passed** (883 + 11 new), 0 failed, no existing test touched; coverage gate `-n auto --cov-fail-under=85` → **93.39%** (new pipeline/reporting code covered); `ruff check`+`format --check` clean; `mypy` **97 ≤ 101** (no new error categories — remainder pre-existing loose typing). Reviewed the concurrent branch: correct `async with semaphore` + `gather`. Key tests: `test_semaphore_bounds_max_concurrency` asserts observed `max_depth == 2` at concurrency=2 (bound both **respected and actually reached**); `test_concurrent_generation_overlaps_wall_clock` asserts concurrent < 2×delay. **Benchmark** (3 images, 0.05s each): serial **0.154s** → concurrent(3) **0.053s** = **2.92× speedup**. `--concurrency 1` = exact serial path. `--help` shows the flag; `import` smoke clean.

**Status:** COMPLETE. Committed `fe92936`, **PR #137** squash-merged **`aa2d466`**; issue #128 auto-closed. **CI saga (recorded in ci-learnings):** the initial push hit a GitHub Actions dispatch glitch — only CodeQL ran, `test.yml`/`validate.yml` never dispatched → PR `BLOCKED` on absent required checks (`gh pr checks --watch` misleadingly exited 0). close+reopen did NOT fix it; an **empty commit** (`d88ef21`, `synchronize` event) re-dispatched all workflows; the overlapping triggers then left one `test.yml` run `cancelled` (`cancel-in-progress`), which `gh run rerun` cleared → green → merged. Parallel image gen (2.92× on 3 images) live; `--concurrency 1` restores serial.
**Duration:** ~40 minutes (opus impl + verification + CI-dispatch recovery)

### Entry 031 — Tighten mypy ratchet baselines (#129 / P5) [ci] [cleanup]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `aa2d466`, branch `chore/mypy-baseline-tighten`. Baselines: bpmn2drawio `.mypy-baseline` **57** (actual **54**), visual-explainer `.mypy-baseline` **101** (actual **97**). feedback-docx-generator is already strict-clean (no baseline). Local uv venvs for both tools (883/894 + bpmn tests green).

**Objective:** Knock down real mypy errors in both tool codebases and lower the `.mypy-baseline` ceilings toward 0 (#129/P5, D24's ratchet-tightening), keeping CI green and behavior unchanged.

**Hypothesis:** Errors are genuine loose-typing, fixable behavior-neutrally. visual-explainer 97: `[union-attr]` 59 (attr access on `X | None`), `[no-any-return]` 11, `[arg-type]` 9 — concentrated in prompt_generator(23)/concept_analyzer(20)/prompt_refiner(13)/image_evaluator(13)/pipeline(11). bpmn2drawio 54: `[operator]` 16, `[assignment]` 16, `[union-attr]` 8 — in validation(15)/layout(12)/generator(10). Plan: 2 parallel implementers (one per tool, distinct files + distinct `.mypy-baseline` → no conflict), each fixing errors with PROPER narrowing/annotations (assert/isinstance/None-guards where provably non-None; `# type: ignore[code]`+justification only for genuine stub-gap false positives, counted separately), running the full tool test suite to prove behavior preserved, then setting `.mypy-baseline` to the new actual count. Success = both counts reduced meaningfully, `.mypy-baseline` = new actual (still a ceiling), all tool tests green, ruff clean, coverage floors held, 14 CI checks green. Target this round: ve ≤ ~65, bpmn ≤ ~40 (incremental — full 0 is future work per the issue).

**Rollback Plan:** All on branch `chore/mypy-baseline-tighten`; `git branch -D` pre-merge, `git revert` post-merge. Behavior preserved by the unchanged test suites (gate before commit). Type-only + baseline-number changes; no logic change.

**Actions & Results:**

1. Both tools measured + categorized; Entry 031 logged before any edit.
2. 2 parallel sonnet-implementer type-fixers (one per tool, disjoint files). **Both zeroed — far past the incremental targets:** bpmn2drawio **54 → 0** (all genuine fixes, 0 ignores: int→float accumulator annotations, `Optional` narrowing with documented call-site invariants, `-> None` on untyped `__init__`s that had left `self.*` as `Any`, a `_local_name` rewrite around a known mypy unannotated-param-reassignment limitation); visual-explainer **97 → 0** (90 real fixes + 7 justified `# type: ignore` with reasons — 5× `response.content[0].text` where `isinstance(TextBlock)` narrowing would break the duck-typed `MagicMock(text=…)` test mocks; 2× pydantic `@computed_field` prop-decorator needing the unconfigured pydantic mypy plugin). Real fixes included `object`→concrete-class typing of the pipeline `style`/`prompt_generator`/etc. params, a genuine `CheckpointState.image_results` `int|str` key-type fix (int live / str after JSON round-trip), and two real pydantic alias bugs surfaced (`FlowConnection next_image→next`, `LogicalFlowStep from_concept/to_concept→from/to`).
3. **Independent verification (both venvs):** ve `mypy → Success: no issues found` (0), `.mypy-baseline`=0, **894 passed**, coverage **93.37%** (≥85), ruff+format clean; bpmn `mypy → Success` (0), `.mypy-baseline`=0, **588 passed**, coverage **92.40%** (≥90), ruff+format clean. Behavior preserved (both suites green). feedback-docx-generator was already strict-clean. **All three tools are now mypy-clean; the ratchet is a hard zero-errors gate.**

**Status:** COMPLETE. Committed `1c027d1`, **PR #138** all 14 required checks green both OSes (mypy ratchet now baseline 0 on both tools), squash-merged **`ab429c2`**; issue #129 auto-closed. All three tools mypy-clean; D24 goal achieved.
**Duration:** ~35 minutes (2 parallel type-fixers + independent verification)

### Entry 032 — Extract oversized command bodies to references/ (#131 / P7, SE-11) [command] [cleanup]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `ab429c2`, branch `chore/extract-command-bodies`. Three frozen-legacy commands over the <500-line house budget: `validate-plugin.md` (675), `implement-plan.md` (573), `new-skill.md` (530). `claude plugin validate plugins/personal-plugin --strict` → passed (baseline). Reference-pointer pattern established (`See \`references/<name>-examples.md\` for …`; existing refs: clean-repo-examples, validation-output-examples, ship-output-templates, …).

**Objective:** Bring each of the 3 oversized command bodies under 500 lines by extracting bulk (examples, output samples, embedded reference scripts/templates) into `references/`, preserving all core instructions and keeping `--strict` validation green (#131/P7, SE-11).

**Hypothesis:** Each command has extractable illustrative bulk that isn't core control-flow: `validate-plugin` (Example Usage, verbose mode descriptions, the embedded owner/repo-derivation script) needs ~175+ lines out; `implement-plan` (~75+); `new-skill` (~35+ — the smallest cut). Moving only examples/samples/templates (never phase logic or instructions) into `references/<name>-examples.md` with a pointer keeps each command fully functional. 3 parallel extractors (one per command, distinct command file + distinct new reference file → no conflict). Expect each body <500 lines, `claude plugin validate plugins/personal-plugin --strict` exit 0, markdownlint clean, all CI green.

**Rollback Plan:** All on branch `chore/extract-command-bodies`; `git branch -D` pre-merge, `git revert` post-merge. Pure docs move (command bulk → references/); no behavior/logic change (the command instructions are preserved; only illustrative material relocates behind a pointer).

**Actions & Results:**

1. Sizes measured, reference-pointer pattern + `--strict` acceptance check confirmed; Entry 032 logged before any edit.
2. 3 parallel extractors (one per command, disjoint files). Results — **all under 500 with margin, all core logic preserved:** `validate-plugin.md` 675 → **480** (moved usage/error text, dir-structure diagram, namespace-registry sample, gh-fallback message → `validate-plugin-examples.md` 87L; Phase 8.4 now points at existing `common-patterns.md`; all 40 Phase-subsections intact); `implement-plan.md` 573 → **462** (moved Input-Validation errors, resume/rollback/phase prompts, COMPLETION-REPORT template, flag-usage examples → `implement-plan-examples.md` 171L; orchestration/state-file/rollback/phase-gate logic untouched); `new-skill.md` 530 → **385** (moved 3 worked SKILL.md examples → `new-skill-examples.md` 150L; scaffolding + frontmatter rules intact).
3. **Independent verification:** all 3 command bodies < 500; 3 new `references/*-examples.md` created + cited via the house `See \`references/…\`` pointer; `claude plugin validate plugins/personal-plugin --strict` → "Validation passed"; `markdownlint-cli` clean on all 6 files; git status = exactly 3 modified commands + 3 new refs + LAB_NOTEBOOK. Pure docs move — no behavior change. (The <500 budget is a house rule per SE-11, not a CI gate, so this is a clean improvement.)

**Status:** COMPLETE. Committed `61d7aff`, **PR #139** all checks green, squash-merged **`3a38363`**; issue #131 auto-closed. All 3 commands now < 500 (480/462/385), 3 new `references/*-examples.md`. Docs-only.
**Duration:** ~15 minutes (3 parallel extractors + verification)

### Entry 033 — CI Python 3.10/3.12 compat as ADVISORY jobs (#130 / P6, PLAT-012) [ci] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `3a38363`, branch `ci/python-compat-advisory`. Required checks: 14 (incl. `Run Tests (ubuntu-latest)` / `(windows-latest)`, named by `${{ matrix.os }}` only). All 3 tools declare `requires-python = ">=3.10"` (visual-explainer also `target-version = py310`), but CI only exercises 3.11.

**Objective:** Verify the tools' 3.10+ support claim by running their test suites on Python 3.10 and 3.12 in CI (#130/P6, PLAT-012) — **without** the branch-protection required-check rename that makes the naive matrix-expansion deadlock merges.

**Decision (D28, user-chosen 2026-07-16):** Add a NEW **advisory** `python-compat` job (distinct check names `Python Compat (3.10)` / `(3.12)`, NOT added to branch-protection required contexts) rather than expanding the existing required `Run Tests`/tool-test job matrices. Rationale: expanding a required job's matrix appends `matrix.python-version` to its check name (`Run Tests (ubuntu-latest)` → `(ubuntu-latest, 3.11)`), so the old required context stops reporting → all PRs deadlock until branch protection is updated in lockstep (recoverable only via admin bypass). The advisory job gets real multi-version signal (red on the PR if 3.10/3.12 breaks) with ZERO deadlock risk and no branch-protection edit. Alt A (full matrix + required-check rename, the issue's literal acceptance) — rejected by the owner as disproportionate risk for a P6/low-value item; failures on 3.10/3.12 stay advisory and can be promoted to required later. Alt C (defer) — rejected; the claim is cheap to verify.

**Hypothesis:** A `python-compat` job (`runs-on: ubuntu-latest`, matrix `python-version: ['3.10','3.12']`, name `Python Compat (${{ matrix.python-version }})`) that `pip install -e ".[dev,all|dev]"` + `pytest tests/` for each of the 3 tools will pass — the tools genuinely support 3.10+ (deps resolve via pyproject ranges, not the 3.11-pinned lockfiles). ubuntu-only (compat is a version concern, not an OS concern; the required jobs already cover Windows on 3.11). No `--cov-fail-under`/mypy in the compat job (those stay on the required 3.11 jobs). Success = the new job appears as 2 NON-required checks, both green, the 14 required contexts unchanged, a test PR still merges. I verify locally on 3.10/3.12 via `uv` venvs before pushing to avoid a known-red advisory check.

**Rollback Plan:** Single additive job in `.github/workflows/test.yml` on branch `ci/python-compat-advisory`; `git branch -D` pre-merge, `git revert` post-merge. No branch-protection change, so nothing to un-wind there. If the advisory job is red on a real 3.10/3.12 gap, that's informative (not blocking) — fix or document the gap separately.

**Actions & Results:**

1. Tool `requires-python` confirmed (all `>=3.10`); D28 logged (user chose advisory path); Entry 033 logged before any edit.
2. Added `python-compat` job to `.github/workflows/test.yml` (before `dependency-audit`): `runs-on: ubuntu-latest`, matrix `python-version: ['3.10','3.12']`, name `Python Compat (${{ matrix.python-version }})`, SHA-pinned checkout/setup-python (matching the rest of the file), 3 steps installing + `pytest tests/`-ing visual-explainer (`.[dev,all]`), bpmn2drawio + feedback-docx (`.[dev]`). A comment documents WHY it's separate/advisory (PLAT-012 rename deadlock).
3. **Local pre-push verification** (`uv` venvs, mirroring the job): YAML valid; **Python 3.10** → visual-explainer **894 passed** (93%), bpmn2drawio **588 passed**, feedback-docx **69 passed**; **Python 3.12** → visual-explainer **894 passed** (47 deprecation warnings, non-fatal). The tools genuinely support 3.10/3.12, so the advisory job is green on first push (not a known-red check).

**Status:** COMPLETE. Committed `48069ad`, **PR #140** merged **`af23557`**; issue #130 auto-closed. `Python Compat (3.10)` + `(3.12)` ran green as NON-required advisory checks (18 total on the PR); branch protection untouched (no branch-protection command was ever issued — Option B was additive-to-`test.yml` only; #140 merged through the intact gate). **All 8 deferred issues (#125–#131 + A1) now closed.**
**Duration:** ~20 minutes (CI edit + local 3.10/3.12 verification)

--- Backlog burndown complete: 2026-07-16 session closed out all of #125–#131 + the dependabot triage (A1) as 9 merged PRs (#132/#133/#134/#136/#137/#138/#139/#140 + dep PRs #104/#113/#114/#115/#116). Filed #135 (CodeQL default-setup broken check). No plugin version bumps (hardening + tests + one perf feature; feature-flagged parallel gen is backward-compatible). ---

--- New session: 2026-07-16 — post-burndown. Backlog is a single low-pri issue (#135) + 2 external PRs (#97, #98). This session investigates & dispositions #135. ---

### Entry 034 — #135 CodeQL "2s failure" is a self-resolved GitHub transient, not a config bug [ci] [decision] [debug]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `238aa59`, clean/synced with origin/main. CodeQL runs via GitHub **default setup** (no `.github/workflows/codeql*.yml`), configured `languages: [actions, python]`, `query_suite: default`, `threat_model: remote`, `updated_at: 2026-07-16T14:37:49Z`. Read-only investigation of open issue #135.

**Objective:** Root-cause the "CodeQL check fails in ~2s on every PR" reported in #135, then pick a proportionate disposition (reconfigure / disable / advanced-setup / close).

**Hypothesis:** #135 posited a default-setup misconfiguration (2s = errors during init, e.g. a language with no compatible code, or a default/advanced conflict). Expected to find either a persistent per-PR failure needing a config change, OR evidence it was transient. Success = a definitive root cause backed by the check-run history, not a guess.

**Rollback Plan:** N/A — read-only investigation (`gh api …/check-runs`, `gh run list`, branch-protection contexts). Disposition (close #135, docs edits) touches no plugin/CI/code; nothing to un-wind.

**Actions & Results:**

1. **Distinguished two different checks.** `gh api commits/<sha>/check-runs` showed the real analyses `Analyze (python)` + `Analyze (actions)` (each ~30–60s) are SEPARATE from a GitHub-managed aggregate check literally named `CodeQL` (~2s) that default setup posts **only on `pull_request` events** (absent on main-push commits). The 2s check is a status rollup, not the analysis.
2. **Traced the aggregate `CodeQL` check across 8 PRs:** #132 ✓ (19:35) · #133 ✓ (20:11) · **#134a ✗ (20:51)** · **#134b ✗ (20:59)** · #136 ✓ (21:11) · #137 ✓ (21:52) · #138–#141 ✓. The failure was **isolated to PR #134's two commits**; every PR before and after passed.
3. **The real scans never failed.** `Analyze (python)` and `Analyze (actions)` both passed on #134 too — CodeQL actually analyzed the code fine; only the 2s rollup blipped.
4. **No config change caused it.** Default-setup config last modified `14:37:49Z` — ~6h before #134's 20:51 failure. Stable config → the blip is GitHub infra, not our config.
5. **Never blocked a merge.** Branch-protection required contexts = the 14 test/validate/lint jobs; `CodeQL`/`Analyze (…)`/`Python Compat (…)` are NOT among them. #134 merged normally.
6. **Root cause:** GitHub-side transient in the default-setup aggregate `CodeQL` status check, isolated to #134 (20:51–20:59, 2026-07-16), self-resolved by #136 (21:11). #135 was filed at 21:01 — one minute after #134's 2nd failure, before #136 showed recovery — so "fails on every PR" was an honest overgeneralization from a single bad data point.

**Decision (D29, user-chosen):** Close #135 with the evidence documented; make NO CodeQL config change. Advanced-setup `codeql.yml` and disabling default setup were both offered and rejected as disproportionate (added maintenance / lost security scanning) for a self-resolved, non-required transient. Matches the project's proportionate-response line (D22/D28).

**What Worked:** Ground-truthing via `commits/<sha>/check-runs` (not `gh run list`, which conflates the workflow run with the posted check and hid the aggregate/analysis split). The per-PR pass/fail timeline turned a vague "every PR" report into a precise "#134-only, 2 commits" finding.

**Status:** COMPLETE. #135 commented (evidence table) + closed as self-resolved transient. No `.github/`, repo-security, or code changes. CI-learnings memory updated so a future session doesn't re-investigate the benign 2s `CodeQL` check. Backlog now: 2 external PRs (#97, #98) only.
**Duration:** ~15 minutes (read-only investigation + disposition)

### Entry 035 — Integrate external PR #98 (bpmn2drawio DI-layout fix) onto current main [plugin] [bpmn] [ci]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `8209965`, clean/synced. PR #98 "fix(bpmn2drawio): preserve DI layout and fix swimlane/label placement" by external contributor **AlexanderV** (4 commits: `6b692f1` DI preserve + geometric lanes, `ad09169` data stores as cylinders, `92ad0f0` pool title alignment, `b735bd4` data labels below shape). Merge-base `c2da962` (2026-07-08 era, BEFORE the 8-phase arch-review remediation and the #129 mypy-zeroing) → PR sits on a stale base; that's the conflict source. Fetched as local ref `pr-98`. +926/−33 across 14 files.

**Objective:** Land PR #98's genuine bug fix (heavily-overlapping shapes when converting BPMN that already carries full DI coordinates, e.g. Bizagi exports) onto current main, crediting the author, with all 14 required checks green on both OSes.

**Hypothesis:** Overlap with main is 3 src files (`generator.py`/`parser.py`/`swimlanes.py`) — all AUTO-MERGE cleanly per `git merge-tree`; only 2 test files (`test_converter.py`, `test_parser.py`) content-conflict (both sides appended tests → adjacent-addition conflicts, resolvable by keeping both blocks). GitHub's "CONFLICTING" is pessimistic. Real risk is the pre-mypy-0 / pre-ruff-format-gate base: the CI gate is `pytest --cov-branch --cov-fail-under=90` + a mypy count-ratchet (`.mypy-baseline`=**0**, `mypy src/` only, LENIENT config — `warn_return_any` but no `disallow_untyped_defs`, so only genuine type errors fail) + `ruff check`/`ruff format --check` (0.14.10) on src+tests. Expect 0–few mypy fixes and possibly a `ruff format` pass on the contributor's code. Success = (a) merged tree builds; (b) bpmn2drawio suite passes at ≥90% branch cov; (c) `mypy src/` = 0; (d) ruff check+format clean on src+tests; (e) new integration PR green on all 14 required checks both OSes; (f) #98 credited + closed. Version bump (bpmn-plugin 4.2.0→?) decided after the diff/review is understood (bug fix ⇒ patch, but the new default `auto` layout mode may argue minor).

**Rollback Plan:** All work on integration branch `integrate/pr98-bpmn-di-layout` off `origin/main`; `git merge --abort` if the local merge misbehaves; `git branch -D` pre-push; `git revert <squash-sha>` post-merge. No shared state touched until push; the contributor's fork branch is never force-pushed (integration via a new branch on origin, not their fork). No plugin version bump committed until the bump level is decided. A parallel read-only correctness review (general-purpose subagent) gates the decision to land vs. send-back.

**Actions & Results:**

1. Structural recon (read-only): merge-base `c2da962`; overlap = 3 src files (clean auto-merge) + 2 test-file conflicts; CI gate mapped (cov-fail-under=90, mypy baseline 0 lenient, ruff 0.14.10 on src+tests). Correctness-review subagent dispatched. Entry 035 logged before any merge.
2. **Integration via cherry-pick** onto `integrate/pr98-bpmn-di-layout` (off `origin/main`) — preserves Oleksandr's authorship per-commit (all 3 merge methods allowed on the repo). Both test conflicts (`test_converter.py`, `test_parser.py`) were the same shape: main had a single-line assert, the PR wrapped it + appended a new test class. Resolved by keeping main's CI-passing assert + the PR's new class (`TestAutoLayoutMode`, `TestGeometricLaneAssignment`), dropping the duplicate wrapped assert. All 4 commits applied clean; src auto-merged as predicted.
3. **CI-gate verification** (venv py3.11, `pip install -e .[dev]`): `pytest -n auto --cov-branch` → **636 passed, 92.83%** (≥90 gate). `mypy src/ --ignore-missing-imports` → **0 errors** (baseline 0 — the pre-mypy-0 PR code passes because the config is lenient and it auto-merged with main's annotations; the anticipated big risk did not materialize).
4. **ruff (pinned 0.14.10, exact CI globs):** the PR predated the ruff gate — 8 `check` errors (6× I001 unsorted in-method imports in test_parser.py; 2× E501 >100 in test_swimlanes.py) + 2 files needing `format` (parser.py, test_swimlanes.py). Fixed via `ruff check --fix` + `ruff format`; re-verified **check + format --check both clean**. Committed as a separate authored fixup `ce17d17` (formatting/import-order only; pytest 636 + mypy 0 still green after). Line-length is 100 (`ruff.toml`).
5. **End-to-end smoke (verify the behavior, not just tests):** CLI on `geometric_lanes.bpmn` (default `auto`) → DI preserved, Start/Do Work/End at 3 DISTINCT positions (50,40 / 150,30 / 350,40), lanes separated, valid mxfile — the exact overlap bug is fixed. CLI on non-DI `minimal.bpmn` → `auto` falls back to graphviz, 3 distinct positions, NO regression for the common case despite the default change.
6. **Version bump → bpmn-plugin 4.2.0 → 4.3.0** (MINOR): new user-facing feature (the `auto` default layout mode) + behavior fix, backward-compatible (`--layout graphviz` and non-DI output unchanged). plugin.json + marketplace.json lockstep; both root + plugin CHANGELOGs credit the contributor; markdownlint clean.
7. **Correctness review returned SOUND-WITH-FIXES** — and its 3 blockers were exactly the ones already resolved above: (#1) the 2 test-file conflicts (resolved identically to its recommendation), (#2) `ruff format` on parser.py, (#3) the 2 E501 lines in test_swimlanes.py. It independently confirmed DI-preservation correctness (traced the fixture geometry → no double-offset), the per-process constraint, mypy-clean, and no non-DI regression — corroborating my own verification. Non-blocking findings actioned: applied the loop-invariant hoist (#5) + added an exact-lane-relative-coordinate test (closes the "double-offset would pass" gap the reviewer flagged) → commit `98d3f91` (637 passed). Filed **#143** for the one substantive edge (finding #4: `auto` default sends partial-DI files to `preserve`, dropping non-DI shapes to origin — rare, Bizagi exports are fully-DI) + the noted coverage gaps. #6/#7 documented (tie-breaking deterministic; malformed-DI is pre-existing and caught by `Converter.convert`).
8. Pushed `integrate/pr98-bpmn-di-layout`; opened **PR #144** (`Closes #98`, credits Oleksandr). Dispatch clean (Tests + Plugin Validation + CodeQL); all 14 required checks green both OSes (BPMN2DrawIO Windows 3m27s — slow but green). **Squash-merged `d2b702e`** (user chose repo-convention squash over rebase-merge; Oleksandr credited via `Co-Authored-By` on the squash commit + a thank-you on #98). #98 auto-closed; main synced. bpmn-plugin 4.3.0 propagates to the plugin cache automatically via marketplace `autoUpdate` (D19) — no manual reinstall.

**What Worked:** (a) `git merge-tree` up front correctly predicted the true conflict surface (2 test files, not the whole tool GitHub flagged) — cheap, non-destructive, deflated the "CONFLICTING" scare before any branch work. (b) Cherry-pick onto a fresh integration branch preserved the contributor's per-commit authorship while letting my fixups stand as separate authored commits. (c) The pre-mypy-0 risk I flagged in the hypothesis did NOT bite — the lenient `[tool.mypy]` config (no `disallow_untyped_defs`) + clean auto-merge with main's annotations meant 0 errors; the real gate friction was ruff-format/E501 on the pre-gate code, all mechanical. (d) A background correctness-review subagent run in parallel with the mechanical integration independently reproduced my findings and its 3 blockers were already fixed — high confidence at no serial cost.

**Status:** COMPLETE. PR #98 integrated → **bpmn-plugin 4.3.0** (`d2b702e`), all 14 required checks green both OSes. 637 tests / 92.83% branch cov / mypy 0 / ruff clean; DI-preservation verified end-to-end with no non-DI regression. Contributor authorship + credit preserved. Follow-up #143 filed (partial-DI edge). Backlog now: 1 external PR (#97 xquik) + #143.
**Duration:** ~50 minutes (recon → cherry-pick/resolve → verify → review integration → release → merge)

### Entry 036 — #143 partial-DI guard: `auto` picks `preserve` only on COMPLETE DI [plugin] [bpmn] [decision]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `e02147d` (post-4.3.0), branch `fix/partial-di-guard`. bpmn2drawio 637 tests / mypy 0 / ruff clean baseline.

**Objective:** Close #143 — the 4.3.0 `auto` default sends a *partially*-DI file to `preserve` (because `has_di_coordinates` is all-or-nothing: `bool(self._di_shapes)`, parser.py:94), stranding the DI-less elements at the origin. Fully-DI (Bizagi) and fully-non-DI files are unaffected; only mixed files regress vs pre-4.3.0 graphviz.

**Decision (D30):** Option 1 (guard `_effective_layout`) over Option 2 (hybrid partial-fallback: graphviz-layout only the DI-less elements) and Option 3 (document-only). Add a `BPMNModel.has_complete_di_coordinates` property (`has_di_coordinates AND every element has x/y`) and gate `auto`→`preserve` on it; partial-DI ⇒ graphviz. Alt 2 rejected — hybrid layouts are fiddly (graphviz doesn't know the DI-fixed positions → new overlap risk) and disproportionate for a rare edge. Alt 3 rejected — a silent "some shapes at (0,0)" is a poor default. The guard restores exact pre-4.3.0 behavior for partial-DI files (full graphviz) while keeping preserve for fully-DI. Conservative-but-safe consequence: a fully-DI file with even ONE element missing DI now uses graphviz for all (consistent layout beats one shape at origin). `has_di_coordinates` semantics unchanged (still used by the preserve-warning at converter.py:99 and lane_organizer.py:69).

**Hypothesis:** `auto`→`preserve` iff `has_complete_di_coordinates`. Existing tests stay green: `with_di.bpmn` and `geometric_lanes.bpmn` are fully-DI (verified: every flow-node has a BPMNShape) → still `preserve`; `minimal.bpmn` has no DI → still `graphviz`. New: a `partial_di.bpmn` fixture (Start/End with DI, Task without) resolves `auto`→`graphviz` and lays out ALL elements (none at origin). Success = new + existing tests pass, mypy 0, ruff clean, coverage ≥90; patch bump 4.3.0→4.3.1.

**Rollback Plan:** All on branch `fix/partial-di-guard`; `git branch -D` pre-merge / `git revert` post-merge. Change is additive (one property + a one-line predicate swap in `_effective_layout` + a fixture + tests); no change to `has_di_coordinates`, `preserve`/`graphviz` internals, or the 4.3.0 feature for fully-DI files.

**Actions & Results:**

1. Traced the mechanism (parser.py:94 all-or-nothing `has_di_coordinates`; converter.py:72 `auto`→`preserve`); confirmed `with_di.bpmn` + `geometric_lanes.bpmn` are fully-DI (every flow-node has a BPMNShape) so the guard won't regress the existing preserve tests. Entry 036 + D30 logged before any code.
2. Implemented: `BPMNModel.has_complete_di_coordinates` property (`has_di_coordinates AND all(e.has_coordinates())`); `_effective_layout` swapped to gate on it; `has_di_coordinates` semantics untouched (still drives the preserve-warning + lane_organizer). Added `tests/fixtures/partial_di.bpmn` (Start/End DI, Task none).
3. **Pre-test sanity** (venv): `with_di`/`geometric_lanes` → complete=True → `auto=preserve` (unchanged); `partial_di` → has_di=True/complete=False → **`auto=graphviz`**; `minimal` → graphviz. End-to-end on `partial_di` in auto mode: all 3 elements laid out at DISTINCT positions, **none at (0,0)**, no warnings — regression fixed.
4. Tests added: `test_has_complete_di_coordinates` (full/partial/none), `test_effective_layout_falls_back_to_graphviz_for_partial_di`, `test_auto_partial_di_lays_out_all_elements` (e2e origin check). Full gate green: **640 passed**, 92.84% branch cov, mypy 0, ruff (0.14.10) check+format clean. Committed `99335dd`.
5. Patch bump **4.3.0 → 4.3.1** (plugin.json + marketplace.json lockstep; both CHANGELOGs). *(PR next)*

**Status:** COMPLETE. **PR #146 squash-merged `98439cc`** (all 20 checks green), #143 auto-closed. #143 fixed via the complete-DI guard; bpmn2drawio 640 tests / 92.84% / mypy 0 / ruff clean; e2e confirms no origin-stranding with fully-DI/non-DI behavior unchanged. bpmn-plugin → **4.3.1**.
**Duration:** ~25 minutes (trace → implement → verify → release → merge)

### Entry 037 — #97 xquik vendor-MCP plugin DECLINED (trust/policy) [plugin] [decision] [security]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `98439cc`. External PR #97 by @kriptoburak (first-time contributor, only PR) — adds a thin `xquik-x-data` plugin wiring Claude to a commercial vendor's remote MCP endpoint `https://xquik.com/mcp`, plus `marketplace.json` + `README.md` edits.

**Objective:** Decide whether to accept a third-party vendor's remote-MCP plugin into the personal marketplace. Owner's call; I ran a security/trust review (background subagent) + presented for decision.

**Decision (D31, owner-chosen):** DECLINE + close #97 (not-planned), with a courteous, specific explanation. NOT a quality/malware judgment (the plugin is cleanly built — env-var key, opt-in install, no install-time code, sane skill guardrails; xquik.com is a real live service). It's a curation/policy call: this marketplace is the owner's own read-only/analysis tooling, not a third-party registry. Alternatives — Accept-with-changes (add `mcpServers` to `schemas/plugin.json`, update SECURITY.md egress policy, add strict validation, reconcile auth, `disable-model-invocation`) rejected: would establish a vendor-plugin acceptance policy the owner doesn't want; Leave-open rejected (no path to yes).

**Review findings that drove it:** (1) it adds a **write-capable** (publish-to-X) third-party egress destination that contradicts SECURITY.md §1/§2 (data leaves only via LLM APIs); (2) textbook vendor-distribution pattern (author=Xquik, linked repo `x-twitter-scraper`); (3) **can't merge as-is anyway** — `plugin.json` `mcpServers` key fails the required `Schema Validation` check (`schemas/plugin.json` is `additionalProperties:false` and doesn't list it). Positives noted: no hardcoded secret, genuine opt-in, guardrails present.

**Hypothesis / Rollback:** N/A — decision + issue-close + docs only; no repo code touched. (Closing a PR is reversible: reopen if the owner changes course.)

**Status:** COMPLETE. #97 commented (decline rationale + suggested they publish their own marketplace) + closed. No code/schema/SECURITY.md changes (the accept-path work was declined). Establishes the third-party-plugin acceptance policy (D31) for future contributor PRs.
**Duration:** ~5 minutes (post-review decision + close; review was a parallel background subagent)

### Entry 038 — personal-plugin 11.0.0 → 11.1.0: release the accumulated burndown work [plugin] [release]

**Date:** 2026-07-16
**Environment:** Linux VM, main at `f00973f`, branch `release/personal-plugin-11.1.0`. Trigger: user ran `/bump-version all minor`.

**Objective:** Version the post-11.0.0 backlog-burndown work (#125–#131) that landed on main WITHOUT a bump — headlined by the new visual-explainer memory-bounded parallel image-generation feature (#128).

**Decision (course-correction on `all minor`):** Bump **personal-plugin only** (minor, 11.0.0→11.1.0), NOT all three. `all minor` doesn't match state: bpmn-plugin was just released 4.3.1 this session (nothing since → an empty bump); slide-gen 1.2.0 has only test/hardening since (no features → minor overstates). personal-plugin is the one plugin with genuine unreleased changes incl. a backward-compatible feature, so minor is correct there. Owner chose "personal-plugin minor only" from the presented options; `[Unreleased]` was empty so no other pending work. Alt "all three minor" (coordinated release) — rejected by owner (2 empty bumps); "+ slide-gen patch" — rejected (hardening not worth a version).

**Hypothesis:** plugin.json + marketplace.json → 11.1.0 (lockstep, version-sync gate green); a real (non-placeholder) `personal-plugin v11.1.0` CHANGELOG entry for #125/#127/#128/#129/#131; markdownlint clean; all 14 required checks green; 11.1.0 propagates via `autoUpdate` (D19). No code change — pure release metadata.

**Rollback Plan:** All on `release/personal-plugin-11.1.0`; `git branch -D` pre-merge / `git revert` post-merge. Metadata-only (2 version fields + CHANGELOG + this entry); no skill/command/tool code touched.

**Actions & Results:**

1. Verified state before bumping: personal-plugin 11.0.0 has real unreleased burndown work (parallel-gen feature #128 + visual-explainer decomposition/coverage/mypy + command extraction); bpmn-plugin 4.3.1 + slide-gen 1.2.0 have no unreleased features; `[Unreleased]` empty. Presented → owner chose personal-plugin-only. Entry 038 logged before the marketplace.json edit.
2. Bumped plugin.json + marketplace.json 11.0.0→11.1.0 (lockstep); added a real `personal-plugin v11.1.0` CHANGELOG section (#125/#127/#128/#129/#131). markdownlint clean; version-sync 11.1.0==11.1.0.
3. Push `release/personal-plugin-11.1.0` → release PR → on green CI (both OSes) squash-merge; 11.1.0 then propagates via `autoUpdate`.

**Status:** Bump COMPLETE on-branch (metadata-only; the burndown code was already on main); release PR is the remaining mechanical step. bpmn-plugin 4.3.1 + slide-gen 1.2.0 deliberately NOT bumped (no unreleased features). Target marketplace state: personal-plugin 11.1.0 / bpmn-plugin 4.3.1 / slide-gen 1.2.0 / marketplace 3.3.0.
**Duration:** ~10 minutes (state check → bump → release)

### Entry 039 — Sync prime findings → GitHub issues (canonical backlog) [decision] [cleanup]
**Date:** 2026-07-17
**Environment:** Linux VM, main at `2789dd7` (clean, synced with origin/main), personal-plugin 11.1.0 / bpmn-plugin 4.3.1 / slide-gen 1.2.0 / marketplace 3.3.0. Trigger: user ran `/prime`, then directed "make sure all tasks are synced with the github issues list — it is the canonical master list", then `/ultra-plan` on the result.
**Status:** IN PROGRESS

**Objective:** Make the GitHub issues list the true canonical backlog by filing the 6 actionable findings from the 2026-07-17 `/prime` run. Post-burndown the tracker is EMPTY (0 issues / 0 PRs) while real work exists only in a conversation-scoped prime report — a direct violation of A2's standing directive ("all tasks/work are managed from the GitHub issues list"). Also close stale Action Item A2, whose tracked issues (#125–#131) are all closed.

**Root cause of the findings being filed:** Not 6 independent defects. The repo has excellent *artifacts* of discipline that aren't *mechanically enforced* — `update-readme.py --check` (not in CI), the pre-commit hook (opt-in, verified NOT installed at `.git/hooks/pre-commit`), the 45 evals (mapping-checked, never executed), and the coverage floors (CI-command-line only, absent from config). Every drift/staleness finding traces to that one gap, which is why they accumulated during a fast burst where CI stayed green throughout.

**Hypothesis:** 6 issues file cleanly against existing labels (ci/tech-debt/test/enhancement/documentation) using the established `[Pn]` title convention (matching closed #125–#131). Expected end state: `gh issue list` returns exactly 6 open, none duplicating a closed issue, dependency P1→P3 recorded in the bodies. Issue creation is metadata-only — zero repo files touched, CI unaffected, no version bump (nothing ships).

**Rollback Plan:** Issues are pure GitHub metadata, fully reversible and touch no code. To undo: `gh issue close <n> --reason "not planned"` for each created issue (numbers logged below as they're minted), or `gh issue delete <n>` for a hard remove. The LAB_NOTEBOOK edit (this entry + the A2 Action Item move) is git-tracked and revertible via `git checkout LAB_NOTEBOOK.md` pre-commit or `git revert` post-commit. No plugin/tool/CI file is modified in this step, so plugin discovery and the 14 required checks cannot regress.

**Verification corrections carried in from the prime run (do not re-litigate):**
- The risk pass named "no repo-level secrets scanning" as the top gap. **Wrong** — verified via `gh api`: `secret_scanning`, `secret_scanning_push_protection`, and `dependabot_security_updates` are all `enabled` on this public repo. Push protection specifically blocks the direct-push bypass that finding described. NOT filed.
- `.mypy-baseline` is `0` for BOTH tools (verified by reading the files); `test.yml:78,130` comments still describe "pre-existing debt (54/98 errors)". The ratchet logic is correct and now acts as a hard zero-gate — only the prose is stale. Filed as docs, not a logic fix.
- `update-readme.py --check` exits 0 / "README.md is up to date" while `README.md:41` says "24 skills" against 28 on disk — the script syncs *tables* only, never prose. That is why the drift survived.
- Gitea (`gitea.tale-mamba.ts.net`) hosts NO claude-marketplace repo; its 17 open issues are all `davistroy/homeserver` (fleet), incl. 2 P0 credential rotations. Out of scope for this project's backlog — deliberately NOT filed here.

**Actions & Results:**

1. Verified tracker state before filing: `gh issue list --state open` → **empty**; `gh pr list --state open` → **empty**. Confirmed the premise — post-burndown the canonical list held nothing while real work existed only in a conversation-scoped report.
2. Read existing labels + the `[Pn]` title convention from closed #125–#131 to file consistently rather than inventing a taxonomy.
3. Entry 039 (Objective/Hypothesis/Rollback) logged **before** the first `gh issue create` — protocol Rule 1 satisfied.
4. Filed 6 issues, priority-ordered by leverage with the dependency recorded in-body:
   - **#149 [P1]** wire the unwired guards — `ci`,`tech-debt` — ROOT CAUSE; **blocks #151**
   - **#150 [P2]** make the 45 evals executable — `test`,`enhancement`
   - **#151 [P3]** `name:`-frontmatter contradiction — `ci`,`tech-debt` — depends on #149
   - **#152 [P4]** stale mypy ratchet comments — `documentation`,`ci`
   - **#153 [P5]** README:41 skill count — `documentation`
   - **#154 [P6]** rotate LAB_NOTEBOOK.md — `documentation`,`tech-debt`
5. Verified end state: `gh issue list` → exactly **6 open**, labels applied as intended, no duplicates of closed work. Hypothesis **confirmed** — no repo file touched, CI untouched, no version bump.
6. Action Items updated (Rule 7): A2 → Completed as **C22** (stale — its #125–#131 all closed); C23 records this sync; new **A12** points at #149–#154 as a pointer row, explicitly not a parallel backlog.

**What Worked:**
- **Verifying agent findings before filing them.** The risk pass called "no repo-level secrets scanning" the single most actionable gap; `gh api` showed `secret_scanning` + push protection + Dependabot all `enabled`, and push protection blocks the exact bypass it described. Filing it would have put a fictional security gap on the canonical list. Two of three agent findings needed correction before they were fit to file — the pattern holds: **treat subagent output as a lead, not a conclusion.**
- Reading the existing label set and `[Pn]` convention first meant zero taxonomy drift against the closed #125–#131.
- Issue-creation-as-metadata proved a genuinely clean rollback surface: 6 `gh issue close` calls, no code risk, so the protocol cost was seconds.

**System insight:** The tracker being *empty* was itself the defect, and it was invisible precisely because every conventional health signal was green (clean tree, synced main, 14/14 checks passing, zero TODOs). A backlog that lives only in a report is indistinguishable from no backlog — the "everything's green" state actively camouflaged it. The same class as the D17/D19 lesson (a clean `git status` proving nothing about origin): **absence of a signal is not evidence of health.**

**Status:** COMPLETE. Canonical backlog is now GitHub #149–#154 (6 open). Next: Entry 040 — `/ultra-plan` over these 6 to produce a sequenced implementation plan.
**Duration:** ~15 minutes (verify → log → file 6 → verify → dashboard update)

### Entry 040 — /ultra-plan the prime backlog (#149–#154) → fresh IMPLEMENTATION_PLAN.md [plan] [decision]
**Date:** 2026-07-17
**Environment:** Linux VM, main at `2789dd7` (clean + Entry 039 uncommitted), personal-plugin 11.1.0 / bpmn 4.3.1 / slide-gen 1.2.0 / marketplace 3.3.0. Trigger: user ran `/personal-plugin:ultra-plan` on the 6 canonical issues, approved the Phase 4 summary, said "implement".
**Status:** IN PROGRESS

**Objective:** Generate a formal, sequenced IMPLEMENTATION_PLAN.md for GitHub issues #149–#154, and file 2 scoped-out follow-up issues. "Implement" here = Phase 5 plan generation (the code changes are Phases 1–7, executed later one-branch-per-phase), per the ultra-plan contract I set with the user.

**Investigation overturned 4 of the 6 issues as filed (all verified in main context, not just by subagents):**
1. **`update-readme.py` is STRUCTURALLY DEAD, not prose-blind** — I ran it: "Found 0 skills" (nested-skills glob `skills/*.md` misses `skills/*/SKILL.md`) + "Commands table not found" (anchor `**Commands:**` no longer matches the count-prefixed `**23 Commands:**` header added in `6c40719`). Exit 2 is unreachable; it reports "up to date" for ANY drift. My 2026-07-17 prime report's "syncs tables only" was WRONG. ⇒ #149(b) is a REPAIR; wiring `--check` before repair ships a green no-op gate (false assurance, worse than nothing). Hard order: repair→wire.
2. **#151 does NOT depend on #149** (I mis-filed it) — it fixes validate.yml's dead skills-frontmatter branch, independent of hook install. Also there are THREE contradicting voices, not 2: `scripts/pre-commit` (name REQUIRED for skills, CORRECT), `validate.yml:128` (name FORBIDDEN, globs skills too — the BUG, dormant only because `glob('*.md')` is non-recursive), `CONTRIBUTING.md:707` (sides with the wrong one). Tiebreaker: `claude plugin validate --strict` passes WITH `name:` in all 39 skills ⇒ pre-commit is right. Fix by path-branching; NEVER strip name; use `glob('*/SKILL.md')` NOT `rglob` (rglob catches 15 frontmatter-less reference .md → 15 false errors).
3. **#153 is NOT a 5-min typo, and NOT independent** — it's a byproduct of the #149(b) repair. 3 stale counts (README:41/70/108) + 5 skills MISSING from tables (archive-project, clear-prep, fleet-health, new-project, build-cfa-deck). Hand-fixing line 41 gets overwritten by the repair and leaves 5 skills invisible. Also: 5 README rows carry hand-edited flag docs ("supports `--focus`") absent from frontmatter — must migrate to frontmatter BEFORE regen or they're silently destroyed.
4. **#150 overturns a DOCUMENTED design** — `evals/README.md:87`: "Evals are designed to be executed in a live Claude Code session. They are not automated unit tests." CI-not-executing is the original intent, not a regression. My prime "largest structural gap" framing was imprecise. ⇒ ADR-0009 required. Also CI has ZERO secrets (`grep secrets. .github/` empty) ⇒ an LLM-judge runner needs the repo's first CI secret + can't run on fork PRs (breaks external PRs like #98).

**Key blocker found (CS5):** Decision Log jumps D13→D19. **D14–D18 exist ONLY in entry bodies** (E005 L341–343, E006 L392/394), never promoted (Rule 7 lapse, May 2026). ADR-0005 (Accepted) cites "D14 (Lab Notebook E005)"; CLAUDE.md:26 (top Verified Operational Rule) rests on D17. Rotating the notebook without first promoting D14–D18 = silently deleting 5 decisions + orphaning an Accepted ADR's precedent = violating the very Rule 4 #154 cites. ⇒ promotion is a standalone prerequisite commit, independently valuable.

**User decisions (AskUserQuestion, this session):**
- **#150 → Ship structural linter now, DEFER the runner** (option A). Extend `check_eval_mapping.py` (structure gate + close 10-surface coverage gap + validate `command:` on cross-cutting + normalize bare-`Must:`). Stays stdlib-only/auth-free/deterministic/required. LLM-judge runner → its own go/no-go = **ADR-0009**. Alts rejected: full runner now (first CI secret, flake, fork-PR breakage); hybrid re-authoring (largest diff, likely = option A with extra steps); close #150 (leaves coverage gap + dead field).
- **CS5 → Promote D14–D18 FIRST, then rotate @line 830** (option A). Cut@830 = session marker, 43% reduction, keeps E017–E039 arc that Current Baseline + SECURITY.md:359 + IMPLEMENTATION_PLAN.md:825 narrate live. Alts rejected: promote-only/drop-rotation; cut@1056 (60% but strands E017–E025 that are cited live).

**Hypothesis:** Fresh IMPLEMENTATION_PLAN.md, 7 phases (≤6 items each), one-branch-per-phase, each green on all 14 required checks; `autoUpdate` propagates content so NO version bump. Old completed arch-review plan archived → `docs/archive/IMPLEMENTATION_PLAN-v9.md` (v4–v8 precedent). 2 follow-up issues filed (feedback-docx mypy asymmetry; lab-notebook `rotate` operation). Plan file + notebook edits stay UNCOMMITTED on main (user commits per-phase during execution; harness rule: branch before committing on main).

**Rollback Plan:** All artifacts reversible & non-code. Plan file: `git checkout IMPLEMENTATION_PLAN.md docs/archive/IMPLEMENTATION_PLAN-v9.md` (pre-commit) — v9 archive is a fresh copy, deletable via `rm`. Notebook: `git checkout LAB_NOTEBOOK.md`. Issues: `gh issue close <n> --reason "not planned"` (numbers logged below). NO plugin/tool/CI/skill file touched in THIS step — plugin discovery + the 14 checks cannot regress from plan generation. Actual Phases 1–7 each carry their own per-branch rollback in the plan's Risk Mitigation table.

**Actions & Results:**

1. Ran per-phase Explore investigation (3 clustered subagents) + verified every load-bearing claim in main context. Key verifications: ran `update-readme.py --check` (confirmed dead — "0 skills", "Commands table not found", exit 0); confirmed Decision Log D13→D19 gap + D14–D18 in bodies only; `grep secrets. .github/` empty (zero CI secrets); `claude plugin validate --strict` green with `name:` in all 39 skills; root `pyproject.toml` aggregates 3 suites (one configfile per pytest run → no double-apply). Constitution (Phase 0): CLAUDE.md comprehensive, no gap-filling questions needed.
2. Archived completed arch-review plan → `docs/archive/IMPLEMENTATION_PLAN-v9.md` (1126 lines; matches v4–v8 precedent).
3. Wrote fresh `IMPLEMENTATION_PLAN.md`: 7 phases / 15 work items, one-branch-per-phase, ≤6 items/phase, plan-template schema (Files Affected / Description / Tasks / Acceptance Criteria WHEN-THEN / Depends On / DOD). Verified: all 6 issues referenced (149×16, 150×7, 151×5, 152×3, 153×6, 154×12), 7 balanced DOD blocks, no atomic set split (README #149a/b+#153 co-located P2; frontmatter 3-file #151 co-located P3; test.yml #149c+#152 co-located P4).
4. Filed 2 scoped-out follow-ups: **#155** feedback-docx mypy-gate asymmetry (P4, two-sided decision, split from #152); **#156** lab-notebook `rotate` operation + threshold (P5, else #154 recurs in ~40 entries). Backlog now 8 open (#149–#156).
5. User AskUserQuestion decisions recorded above (#150 = structural-linter-now/defer-runner→ADR-0009; CS5 = promote-D14–D18-then-cut@830).

**What Worked:**
- **Verifying subagent claims before trusting them (again).** The guards agent claimed `update-readme.py` was fully dead, contradicting my OWN prime report ("syncs tables only"). I ran it — the agent was right, my prime was wrong. Two of three prime risk-findings and my own two filed dependencies (#151→#149, #153-as-typo) were wrong until investigation corrected them. Pattern holds firmly: subagent output AND prior-session conclusions are leads, not facts.
- **Per-phase clustered Explore dispatch** kept ~2600 lines of file reads out of main context while surfacing the D14–D18 blocker that a symptom-level plan would have walked straight into.
- **AskUserQuestion for the 2 genuine forks** (CI-secret posture; rotation depth) rather than deciding unilaterally — both were owner-domain calls (bus-factor-1 CI risk; permanent-record shape).

**System insight:** 5 of 6 "independent" issues collapsed to one root cause (verification artifacts that exist but aren't wired to run), and the 6th (#154) hid a data-integrity landmine (D14–D18) that ONLY surfaces under the action the issue requests. Filing issues from a symptom-level scan (my prime) produced a correct *list* but wrong *shape* — the deep investigation didn't add items, it re-grouped and re-sequenced them and found the blocker. Lesson for the prime→issues→plan pipeline: the plan phase is where symptom-issues get their true root-cause structure; don't over-trust the issue text (even your own).

**Status:** COMPLETE (plan generation). `IMPLEMENTATION_PLAN.md` (7 phases) + `docs/archive/IMPLEMENTATION_PLAN-v9.md` + Entry 040 + #155/#156 filed. All UNCOMMITTED on main (working tree: LAB_NOTEBOOK.md, IMPLEMENTATION_PLAN.md, docs/archive/IMPLEMENTATION_PLAN-v9.md) — per "commit only when asked" + "branch before committing on main". Next: execute Phase 1 (start with `/implement-plan`, or a manual branch), OR user commits the planning artifacts first.
**Duration:** ~35 minutes (3-agent investigation → constitution → interaction map → design → 2 user decisions → plan gen → 2 follow-ups → verify).

### Entry 041 — Fix flaky wall-clock concurrency test (visual-explainer) [test] [debug] [ci]
**Date:** 2026-07-17
**Environment:** Linux VM, branch `fix/flaky-concurrent-timing-test` off `docs/ultra-plan-prime-backlog` (stacked). Trigger: during `/ship` of the planning artifacts (PR #157), the required check **Visual Explainer Tests (windows-latest)** failed on `test_concurrent_generation_overlaps_wall_clock` — twice.
**Status:** COMPLETE

**Objective:** Unblock PR #157 (docs-only) by fixing a pre-existing flaky timing test that #157 merely surfaced. User chose "fix first (separate PR), then merge #157" (AskUserQuestion).

**Symptom:** `assert concurrent_elapsed < 2 * delay` (delay=0.05 → threshold 0.10s) failed on windows-latest: attempt 1 `0.110 < 0.100`, attempt 2 `0.175 < 0.100`. Coverage passed (93.37%); 893/894 passed. My PR touches ZERO Python — the Python is byte-identical to green `main` tip 2789dd7. So: flaky, not a regression.

**Root cause (systematic-debugging, deeper than the symptom):** The test measures the CONCURRENT run FIRST (line ~1707) and the SERIAL run SECOND. The first-measured run pays a one-time cold-start cost (asyncio loop init, first mock/import warmup) the second does not. Proven locally: run in ISOLATION (cold) the test FAILED even my first fix attempt (subtraction form) in 43.96s; run inside its 9-test class (warm) it PASSED. Under xdist on Windows, whichever worker schedules this test early hits the cold path → the wall-clock overlap signal collapses → intermittent red. An *absolute* threshold (`< 2*delay`) breaks whenever fixed overhead exceeds one delay; a *subtraction* threshold (`concurrent < serial - delay`, my first attempt) still breaks under cold-start ASYMMETRY because the overhead isn't equal across the two measured runs.

**Fix:** Abandon wall-clock timing entirely (an inherently CI-fragile proxy). Instrument ACTUAL overlap: `fake_generate` increments/decrements an `in_flight` counter around its `await asyncio.sleep`, tracking `max_in_flight`. asyncio is single-threaded/cooperative, so the counter is lock-free-safe (mutates only between awaits). Assert `state_c["max_in_flight"] >= 2` (concurrent genuinely overlapped) and `state_s["max_in_flight"] == 1` (serial never did). Deterministic, timing-independent, and STILL catches a broken concurrency path (if images didn't overlap, max_in_flight stays 1 and the concurrent assert fails). Removed now-unused `import time` + 4 `perf_counter` calls; reduced `delay` 0.05→0.02 (no longer timing-load-bearing, just holds tasks in flight).

**Hypothesis:** deterministic assertions pass on every runner incl. windows-latest under xdist; coverage stays ≥85%; ruff clean.

**Rollback Plan:** Single-file test change (`test_pipeline.py`) + this entry, both on `fix/flaky-concurrent-timing-test`. `git checkout 289e45eb88c7c70854ba7a743997637132e79fdf -- plugins/personal-plugin/tools/visual-explainer/tests/test_pipeline.py` pre-commit; `git branch -D` pre-merge / revert the fix PR post-merge. No src/ code touched — only the test.

**Actions & Results:**
1. Read the full test (lines 1677–1742): it ALREADY measured both concurrent + serial; the fragile part was the absolute `< 2*delay` line plus cold-start ordering.
2. First attempt (subtraction `concurrent < serial - delay`): FAILED in isolated cold run → revealed the cold-start-asymmetry root cause, not just threshold tightness. Discarded.
3. Rewrote to deterministic in-flight counting. Local verification via tool `.venv`: ISOLATED (the failing cold case) → **1 passed**; full class → **9 passed**; full suite → **894 passed, cov 93.37%** (gate 85); `uvx ruff@0.14.10 check` + `format --check` clean.

**What Worked:** Reproducing the failure LOCALLY in isolation (not just re-running CI) exposed that the subtraction fix was insufficient — the isolated cold run is the same condition as an early-scheduled xdist worker. Had I shipped the subtraction fix (which "looked right" and passes warm), it would have stayed flaky. Deterministic instrumentation > any wall-clock proxy for concurrency tests.

**System insight:** Wall-clock timing assertions in CI are an anti-pattern — they encode an environment assumption (overhead << signal) that loaded, cold, parallel runners violate unpredictably. The behavior under test (does concurrency overlap?) is directly observable via an in-flight counter; test the property, not a timing proxy for it. Filed nothing new — this is a fix, and #128 (which introduced the test) is already closed.
**Duration:** ~20 minutes (2 CI failures → local repro → root cause → 2 fix iterations → full-suite verify).

### Entry 042 — Promote D14–D18 into the Decision Log (Phase 1 of prime-backlog plan) [decision] [docs]
**Date:** 2026-07-17
**Environment:** Linux VM, `claude-marketplace` main, personal-plugin 11.1.0 / bpmn 4.3.1 / slide-gen 1.2.0 / marketplace 3.3.0. Phase 1 of the `/implement-plan` run against `IMPLEMENTATION_PLAN.md` (7-phase prime-backlog plan from Entry 040).
**Status:** COMPLETE

**Objective:** Promote the 5 body-only decisions (D14–D18) into the Decision Log table, restoring a gapless D1–D31 and unblocking the notebook rotation gated on this in Phase 7 (per the Risk Mitigation row "Rotation deletes D14–D18 / orphans ADR-0005").

**Hypothesis:** After the edit, the Decision Log reads D1..D31 contiguous with no gap; ADR-0005's citation of "D14 (Lab Notebook E005)" is now resolvable directly in the table, not only in an entry body; and the file stays markdownlint-clean under the project's `.markdownlint.json`.

**Rollback Plan:** `git checkout LAB_NOTEBOOK.md` — this is a table-only insertion; no existing decision row or entry text was altered.

**Actions & Results:**
1. Inserted 5 rows (D14–D18) into the Decision Log table, in D-number order, immediately after D13 and before D19, drawn verbatim from the entry bodies: D14–D16 from Entry 005 (agent naming, escalation cap, orchestrator advisory), D17–D18 from Entry 006 (origin/main-is-truth, surgical file-level cherry-pick).
2. Confirmed D17 stays ACTIVE (not SUPERSEDED) — D19 references D17's root cause as a "second occurrence" but is a distinct decision about plugin cache freshness, not a replacement of D17.
3. Verified `grep -oP '^\| D\K[0-9]+' LAB_NOTEBOOK.md | sort -n | uniq` prints a contiguous 1..31 with no gap at 14–18.
4. `markdownlint-cli` run against `LAB_NOTEBOOK.md` and `IMPLEMENTATION_PLAN.md` — exit 0.
5. Set `IMPLEMENTATION_PLAN.md` work item 1.1 to `COMPLETE [2026-07-17]` and updated the Risk Mitigation row for "Rotation deletes D14–D18 / orphans ADR-0005" to reflect the mitigation as applied.

**Status:** COMPLETE. Decision Log is now gapless D1–D31. Phase 7 (notebook rotation) is unblocked on this precondition.
**Duration:** ~10 minutes (extract verbatim decision text from E005/E006 → insert rows → verify contiguity → markdownlint → update plan file).

### Entry 043 — Execute prime-backlog plan Phases 2–6 (code/CI enforcement) [build] [ci] [plugin]
**Date:** 2026-07-17
**Environment:** Linux VM, branch `impl/prime-backlog-149-156` (off main `4e1568c`), via `/implement-plan`. Running entry — updated before each phase commit (Rule 11).
**Status:** COMPLETE

**Objective:** Implement Phases 2–6 of IMPLEMENTATION_PLAN.md (the code/CI enforcement phases): repair the README guard (#149a/b+#153), reconcile the frontmatter rule (#151), reproduce coverage gates locally + fix mypy comments (#149c+#152), install the pre-commit hook (#149d), and build the eval structural linter + ADR-0009 (#150). No version bump (autoUpdate, D19).

**Rollback Plan:** Each phase is one commit on the feature branch; `git revert <sha>` per phase, or reset the branch. `last_good_sha` tracked in `.implement-plan-state.json`. No merge to main until the final PR (human-reviewed, no --auto-merge).

**Phase 2 (README guard) — Hypothesis:** After migrating hand-edited flag-doc rows into frontmatter (2.1), repairing `update-readme.py`'s dead skills glob (`*/SKILL.md`) + count-prefixed table anchors + adding prose-count rewrite (2.2), and wiring `--check` as a STEP in the existing `plugin-validate` job (2.3, no new required-check name): `update-readme.py --check` exits 0 clean / 2 on drift (currently unreachable), README shows 28 skills + all 62 surfaces incl. the 5 missing ones, no hand-edited flag note lost, markdownlint clean. Hard order 2.1→2.2→2.3 (wiring a dead script = green no-op gate).

**Actions & Results:** (per phase, appended below)
- Phase 2 (README guard) COMPLETE: `update-readme.py` was DEAD in two ways — nested-skill glob (`*/SKILL.md` fix) + count-prefixed anchor regex; also a masked bug (all skill names resolved to "SKILL"). Added surgical prose-count rewrite. Verified guard now detects drift: `--check` clean-exit=0, drift-exit=2 (was unreachable). 3 genuine hand-edited flag-doc rows migrated to frontmatter (consolidate-documents, validate-plugin, lab-notebook) — 5 others already covered by argument-hint, left alone. README regenerated: 28 skills + all 62 surfaces incl. the 5 previously-missing (archive-project/clear-prep/fleet-health/new-project/build-cfa-deck). Wired `--check` as a STEP in the existing `Validate Plugins (official CLI)` job (no new required-check name, avoids PLAT-012 deadlock). Removed unused `Optional` import. Closes #149a/b + #153.
- Phase 3 (frontmatter rule) COMPLETE: branched validate.yml's "Validate command frontmatter" step by artifact type — commands FORBID `name` (unchanged), skills REQUIRE `name` matching the dir, via `glob('*/SKILL.md')` (NOT rglob — that would catch 15 frontmatter-less reference .md). Check NAME unchanged (no branch-protection rename). Verified against the real tree: all commands nameless, all 39 skills name==dir, strict-validate exit 0. Aligned the 3rd voice `CONTRIBUTING.md:707` to the two-part rule (`PLUGIN-DEVELOPMENT.md:333` already correct). Closes #151.
- Phase 4 (reproduce gates locally) COMPLETE: moved the 3 coverage floors (90/85/95) from CI command lines into each tool's `[tool.coverage.report] fail_under`; feedback-docx got a NEW `[tool.coverage.run] branch=true` (else its 95 floor would silently measure laxer line-coverage) AND a NEW `[tool.pytest.ini_options] addopts=--cov=...` (subagent-caught: without it, bare pytest in that dir inherited the root config with no --cov, so the floor never activated — now consistent with the other 2 tools). Removed `--cov-fail-under=9x` from CI test lines; pinned `--cov-fail-under=0` on the 3 advisory python-compat invocations. Double --cov (CLI+addopts) verified non-breaking (69 passed, 96.95% branch, floor enforced). Rewrote the stale "54/98 errors" mypy comments to describe the current hard-zero gate (logic + baselines untouched, both still 0). feedback-docx mypy asymmetry left to #155. Closes #149c + #152.
- Phase 5 (install the hook) COMPLETE: removed the dead `check_help_sync` from `scripts/pre-commit` (looked for `skills/help/SKILL.md` which exists nowhere — reported PASS while checking nothing, would have spammed contributors). Created idempotent `scripts/install-hooks.sh` + documented `bash scripts/install-hooks.sh` install + `test -x` verify in CONTRIBUTING.md. Aligned the hook to Phase 3: added the name==dir check for skills (was only checking name present). Verified end-to-end in a temp repo (valid pass / missing-name fail / name-mismatch fail); deliberately did NOT install into this repo's .git/hooks (would interfere with the in-flight implement-plan commits). Closes #149d. Pre-existing tangent noted, NOT fixed (out of plan scope): CONTRIBUTING.md still has stale `/new-command` + `skills/help/SKILL.md` references (lines ~51/91).
- Phase 6 (eval structural linter + ADR-0009) COMPLETE: extended `check_eval_mapping.py` from mapping-only to a structural + coverage gate (every scenario has invocation + Must:, every eval has a Rubric, `command:` validated even for cross-cutting — fixed the dead `description-triggers` field; normalized `**Context:**`/`**Invocation:**` variance; fixed 2 malformed specs prime/scaffold-plugin). Added a COVERAGE_ALLOWLIST + gate: every live surface needs an eval OR a reasoned allowlist entry. Closed the 10-surface gap: authored 2 well-formed stubs (arch-review-single, arch-synthesize), allowlisted 8 (fleet/spark/jetson need SSH; build-cfa-deck/sg-* need the external engine+keys per ADR-0008; evaluate-pipeline-output pins a machine path). Stays stdlib-only (`__future__`/pathlib/re/sys), 0.04s. **NEGATIVE-TESTED (learned from the update-readme.py no-op trap): gate exits 1 on a stripped-Must eval AND on an uncovered surface, 0 when restored — it genuinely gates.** ADR-0009 (Accepted) records ship-linter-now / defer-LLM-judge-runner (CI-secret/fork-PR/flake/cost rationale). Closes #150. Pyright `object`-not-iterable nits on the parser are static-inference only (scripts/ outside CI mypy scope; runtime-correct, both test paths exercised).
- Phase 7 (rotate notebook) — Hypothesis: archive E001–E016 (lines 143–834, verbatim, banner+back-pointer, `git add -f` since docs/archive/ is gitignored) → cut them from the live notebook (keep the `## Experiment Log` header + a forward pointer + E017 onward) → re-point external refs (SECURITY.md:359, ADR-0005/0006, CLAUDE.md:26). Expect D1–D31 Decision Log fully intact (unblocked by Phase 1), archive = 16 entries, notebook ~43% smaller, markdownlint clean both files, commit-gate hook still passes (mtime+today-date). Rollback: `git checkout LAB_NOTEBOOK.md` + `rm` the archive (all pre-commit).
- Phase 7 (rotate notebook) COMPLETE: opus implementer archived E001–E016 verbatim → `docs/archive/LAB_NOTEBOOK-E001-E016.md` (banner + back-pointer, **force-added** past the global `archive/` gitignore) and cut them at the E017 session-marker boundary, inserting a forward pointer. Independently verified: **Decision Log D1–D31 fully intact** (Phase 1 promotion held), archive = exactly 16 entries **byte-identical** to the removed 691-line slice, zero live/archive entry overlap (clean MOVE, no loss per Rule 4), live notebook **1511 → 822 lines (~46% off, ~54K → ~30K tokens)**, commit-gate hook still satisfied (today's date present ×11), markdownlint clean. Re-pointed SECURITY.md:359 + ADR-0005/0006 prose refs with archive hints; implementer skipped the optional CLAUDE.md:26 hint by sound judgment (D17/D19 resolve via the live Decision Log; avoid marginal agent-directed CLAUDE.md edits). Closes #154. Recurrence prevention deferred to #156 (a `rotate` op + threshold for the lab-notebook skill).

**What Worked (whole run):** Per-phase subagent dispatch (sonnet for 1–6, opus for 7) with independent main-thread verification of every phase's DOD — never trusting a subagent's self-report on a gate. The update-readme.py no-op trap (a "guard" that silently passed) made me negative-test EVERY new gate this run (README --check drift-exit=2; eval linter exits 1 on bad input); both are now proven real, not decorative. Two subagents caught issues my plan missed: the feedback-docx `[tool.pytest.ini_options]` gap (4.1) and the cross-scenario invocation-tracking needed to avoid 35 false eval failures (6.1).

**System insight:** A verification artifact that can't fail is worse than none — it converts "unchecked" into a false "checked". Three of this backlog's six issues (README, evals, hook) were exactly that class: guards that existed but never gated. The fix pattern is uniform — make the guard capable of failing, prove it fails on bad input, THEN wire it in. Order matters: repair-before-wire (Phase 2), promote-before-rotate (Phase 1→7), remove-dead-check-before-install (Phase 5).

**Status:** COMPLETE — all 7 phases (16 items) implemented, tested, committed one-per-phase; #149–#154 closed, #155/#156 filed for scoped-out work. Final step: PR (no auto-merge; human review).
**Duration:** ~90 minutes across the 7 phases (investigation + 8 subagent dispatches + per-phase verification).

### Entry 044 — CONTRIBUTING.md skills-first cleanup (close E043 tangent) [docs] [cleanup]
**Date:** 2026-07-17
**Environment:** Linux VM, branch `docs/contributing-skills-first` off main `e594158` (post-#159 merge). Trigger: user "tackle that last thing" — the stale CONTRIBUTING.md refs flagged in E043 Phase 5.
**Status:** COMPLETE

**Objective:** Make CONTRIBUTING.md factually correct and consistent with ADR-0006 (skills-first). Investigation showed the flagged refs were broader than 2 lines: `/new-command` is DEPRECATED (in `deprecated/`) yet the Quick Start led with it; the dead help skill (`skills/help/SKILL.md`, no such dir/file anywhere) was referenced in the Quick Start step 2 and the plugin scaffold step, contradicting the doc's own line 248.

**Decision:** Reframe "Quick Start: Adding a Command" → "Quick Start: Adding a Skill" (primary path via `/new-skill`, which exists), add a frozen-legacy banner to the "Adding a New Command" reference section (kept — still valid for the 23 existing commands), and remove every dead help.md reference (native `/help` handles discovery). Alt considered: minimal 2-line patch — rejected, it would leave the Quick Start telling new contributors to use a deprecated tool. Alt: full command→skill doc rewrite — rejected as disproportionate; the command reference sections are valid legacy.

**Rollback Plan:** Single-file docs change (CONTRIBUTING.md) + this entry; `git checkout` pre-commit / revert the PR post-merge. Docs-only — no code, no version bump.

**Actions & Results:** Edited ToC, Quick Start (command→skill via `/new-skill`), plugin scaffold step (help.md→removed, `/new-command`→`/new-skill`), PR-template test plan (`/new-command`→`/my-skill`, "shows all commands"→"native /help lists command/skill"), and added the ADR-0006 legacy banner. Verified: zero remaining deprecated `/new-command` tool refs or dead help.md/skills-help refs (only legit `my-new-command.md` example filenames + the kept legacy ToC entry remain); all `/help` mentions are native; markdownlint clean; README sync guard still exit 0 (counts untouched).
**Duration:** ~10 minutes.

### Entry 045 — Unify the mypy gate: retire the ratchet, bare `mypy` everywhere (#155) [ci] [decision]
**Date:** 2026-07-17
**Environment:** Linux VM, branch `fix/unify-mypy-gate-155` off main `c3e9742`. Trigger: user "tackle #155 then #156".
**Status:** COMPLETE

**Objective:** Resolve the mypy-gate asymmetry (#155, scoped out of the #149–#154 plan): bpmn2drawio + visual-explainer use a `.mypy-baseline` count-ratchet; feedback-docx uses bare `mypy src/`.

**Decision (D33):** Converge on **bare `mypy src/ --ignore-missing-imports` for ALL three tools**; delete both `.mypy-baseline` files and the ratchet CI blocks. Rationale: all three are at 0 errors (D24 achieved), so the ratchet is now scaffolding, not a working ceiling. Converging on the SIMPLER existing form (feedback-docx's bare mypy) removes complexity rather than spreading the ratchet to a third tool. Enforcement is identical — a baseline-0 ratchet passes iff `mypy` finds 0 errors, exactly what bare `mypy` checks — so this is behavior-preserving at the current state. The ratchet's only remaining feature is an escape hatch to raise the ceiling above 0, which contradicts the project's hard-zero stance (D24); the honest response to a new error is to fix it or add a scoped `# type: ignore` with a reason, not raise a global ceiling. **Supersedes the ratchet portion of D24** (D24's debt-paydown goal stands; its "ratchet is now a hard zero gate" mechanism is retired in favor of plain hard-zero). Alt: give feedback-docx a `.mypy-baseline=0` for symmetry — rejected (spreads the more-complex form to all three; keeps an unwanted escape hatch).

**Hypothesis:** 2 ratchet CI blocks → the 3-line bare-mypy step; 2 `.mypy-baseline` files deleted; YAML parses; all 3 tool mypy jobs stay green (they were at 0, bare mypy also exits 0). No version bump.

**Rollback Plan:** `git revert` / branch delete. CI-config + 2 deleted marker files; no tool source touched. Baselines recoverable from git history if ever needed.

**Actions & Results:** (below)

1. Replaced both count-ratchet CI blocks with the 3-line bare `mypy src/ --ignore-missing-imports` step (matching feedback-docx); deleted both `.mypy-baseline` files. All 3 tools now use one identical hard-zero mypy step.
2. Verified bare mypy clean locally: bpmn2drawio "Success: no issues found in 23 source files"; visual-explainer clean too. YAML parses; 0 ratchet refs remain.
**Duration:** ~10 min.

### Entry 046 — Add `rotate` operation to the lab-notebook skill (#156) [skill] [decision]
**Date:** 2026-07-17
**Environment:** Linux VM, branch `feat/lab-notebook-rotate-156` off main `646093e`. Trigger: user "tackle #155 then #156".
**Status:** COMPLETE

**Objective:** Close #156 — the notebook rotation I did manually in E043 (#154) had no automation, so it would recur in ~40 entries. Encode it as a repeatable skill operation with the hard-won invariants.

**Hypothesis:** A `rotate` operation added to the lab-notebook skill + a threshold rule in CLAUDE.md means the next rotation is routine, not a from-scratch judgment call. Skill body stays <500 (detailed procedure in `references/`); plugin validate --strict + markdownlint clean; no version bump.

**Rollback Plan:** Additive skill/docs change (SKILL.md + new references/rotation.md + CLAUDE.md Rule 12); `git revert` / branch delete. No tool code touched.

**Actions & Results:**
1. Added `rotate` to the skill's operations list + a compact "On `rotate`" section (SKILL.md 499 lines, under budget); full step-by-step in new `plugins/personal-plugin/skills/lab-notebook/references/rotation.md`.
2. Encoded the E042/E043 invariants as the procedure's load-bearing steps: **Step 0 (BLOCKING) promote body-only decisions FIRST** (the D14–D18 near-loss), cut only at a session marker, **`git add -f`** the archive (docs/archive/ globally gitignored), banner + bidirectional pointers, and a verify block (Decision Log contiguous / archive count == removed / zero live-archive overlap / lint clean).
3. Stated the trigger in CLAUDE.md as **Rule 12: Rotate When Large** (~40 entries or ~1200 lines → keep last ~20) and mirrored a one-line rotation note into the skill's injected Rule-7 template so new projects inherit it.
4. Verified: SKILL.md 499 lines; markdownlint clean (SKILL + rotation.md + CLAUDE.md); `claude plugin validate --strict` passed; eval-mapping + README guards still green (the frontmatter-less reference file isn't scanned as a skill).

**What Worked:** Doing the manual rotation first (E043) then encoding it (E046) — the reference file is a direct transcription of what actually worked, including the two gotchas (body-only decisions, gitignored archive) that only surfaced by doing it. Codify-after-doing beats codify-from-imagination.
**Duration:** ~20 min.

### Entry 047 — Design the task-sync skill (brainstorm) [skill] [decision] [design]
**Date:** 2026-07-18
**Environment:** Linux VM, branch `docs/task-sync-design` off main `5348369`. Trigger: user wants a new `task-sync` skill; "explore and discuss before you build anything."
**Status:** COMPLETE (design only — implementation not started)

**Objective:** Produce an approved design for `task-sync`: a per-repo JSON task list kept in sync with the repo's issue tracker (GitHub or Gitea), driven from the terminal.

**Hypothesis:** N/A — design/brainstorm entry (no system change). Rollback Plan: N/A — additive design doc only.

**Decisions (all validated with the user, one section at a time):** captured as **D34** and in full at `docs/plans/2026-07-18-task-sync-design.md`. Headlines:
- Storage = one committed `tasks.json` (canonicalized); interface = the skill (in-session sortable/filterable tables) + a gitignored `TASKS.md` for glancing; no standalone TUI (user runs no GUI; terminal tables are TUI-native).
- Sync = reconciling 3-way merge against a committed `last_synced` base (safe across the user's two machines); tiebreaker = last-write-wins by `updated_at` but **surface genuine two-sided conflicts** rather than clobber. Key reframe accepted: the tracker is NOT a passive mirror (dependabot/PR-close/web-filed issues), so sync must be bidirectional even though the user drives from local.
- Archiving = prune `done` after N days; the tracker's closed issues are the permanent archive.
- Confidentiality = ONE list, always the sanitized version; scan (reuse leak-risk-audit/remove-ip) offers keep/anonymize/redact/remove per finding, applied to the stored task and remembered by content hash; recommendation tuned by repo visibility. (User rejected a second gitignored private file — wants exactly one list.)
- Grouping = optional `milestone` field (round-trips to GitHub/Gitea milestones), NOT a bespoke `project` field.
- Relationship to IMPLEMENTATION_PLAN.md: keep both — task list = backlog (what/whether), plan = execution blueprint (how) that /implement-plan runs. They form a pipeline (backlog → ultra-plan → plan → implement-plan → close). Do NOT flatten plans into tasks or drop markdown plans.

**Status mapping:** issue open/closed native; backlog/in-progress/blocked ride on `status/*` labels; priority on `priority/*` — matching the homeserver Gitea convention.

**Open implementation fork (for plan time):** deterministic reconcile as a small bundled Python tool (`tools/task-sync/`, testable) vs skill-driven bash+jq. Lean: Python tool.

**What Worked:** Section-by-section validation surfaced two reframes the user hadn't stated but agreed with — (1) "mirror" is actually bidirectional, (2) format choice doesn't buy sort/filter/edit; the interface does. Also caught the public-repo trap (committed `tasks.json` is world-readable), which reshaped the confidentiality model.
**Next:** `/ultra-plan` the design → resolve the Python-vs-bash fork → `/implement-plan`.
**Duration:** ~design conversation.

### Entry 048 — /ultra-plan task-sync → fresh IMPLEMENTATION_PLAN.md [plan] [skill]
**Date:** 2026-07-18
**Environment:** Linux VM, branch `plan/task-sync` off main `a6955cc`. Trigger: `/ultra-plan docs/plans/2026-07-18-task-sync-design.md`, user chose Python-tool (fork A), approved Phase 4 summary, said "implement".
**Status:** COMPLETE (plan generation; build is the next /implement-plan run)

**Objective:** Turn the approved task-sync design (D34, `docs/plans/2026-07-18-task-sync-design.md`) into a formal 6-phase IMPLEMENTATION_PLAN.md.

**Investigation corrections folded in (Phase 1):**
1. **Confidentiality "reuse" was false** — `leak-risk-audit`/`remove-ip` are PROMPT-ONLY, no callable machinery. Real deterministic patterns live in sibling repo `contact-center-lab` (`stage_B_redaction/patterns.py`, `leak_scan.py`, `mapping_db.py`) — copy/adapt, not importable. Neither covers generic secrets/tokens (the #1 tracker-push leak) → task-sync builds its own secret detector + adapts cc-lab's GENERIC structural regexes only. **⚠ cc-lab's hardcoded client brand terms must NOT be copied into this public repo — that would itself leak; sensitive-terms are per-repo config.**
2. **Gitea reads need the REST API** — `tea` CLI JSON omits `updated_at`/`body` (labels space-joined), breaking last-write-wins. Verified the Gitea REST API (token in tea config, reachable) returns the full GitHub-compatible shape → both providers read via REST behind one normalized adapter interface.
Confirmed: bundled Python tool = 7 files + 1 CI job (2 required checks) + branch-protection lockstep + root-pyproject aggregation + dependency-audit line; new skill needs an eval (#150 gate), README regen (#149), SECURITY.md egress note, personal-plugin minor bump.

**Key design decision (ADR-0010, to be authored in build phase 6):** Python tool (not bash+jq) — reconcile/confidentiality are deterministic, correctness-critical, test-worthy; bash+jq untestable + Windows-fragile; a sync bug silently corrupts task lists. Tool is NON-interactive (plan→decide→apply protocol: `sync --plan --json` emits push/pull/conflicts/confidentiality-findings; SKILL renders + prompts; `sync --apply --decisions`); the SKILL owns all interaction, the tool owns logic.

**Hypothesis:** Fresh IMPLEMENTATION_PLAN.md, 6 phases (~18 items), one-branch-per-phase; each phase leaves CI green (tool CI job runs un-required until phase 6 proves it green, then branch protection updated — avoids the D28 deadlock). Old prime-backlog plan archived → v10.

**Rollback Plan:** Plan-doc + notebook + v10 archive only (no code). `git checkout` pre-commit / branch delete. Actual Phases 1-6 each carry their own rollback in the plan.

**Actions & Results:** archived completed prime-backlog plan → `docs/archive/IMPLEMENTATION_PLAN-v10.md`; wrote fresh IMPLEMENTATION_PLAN.md (below).

**Duration:** ~plan generation. **Next:** /implement-plan (6 phases, one PR each; tool CI job stays un-required until Phase 6).

### Entry 049 — Build task-sync (implement-plan execution) [skill] [build] [ci]
**Date:** 2026-07-18
**Environment:** Linux VM, branch `impl/task-sync` (off main `b181b4f`), via `/implement-plan` on IMPLEMENTATION_PLAN.md (task-sync, 6 phases/18 items). Running entry — updated before each phase commit (Rule 11).
**Status:** IN PROGRESS

**Objective:** Build the task-sync skill + bundled Python tool per the plan (D34, E048): tool skeleton+model → providers (GitHub gh / Gitea REST) → reconcile engine → confidentiality scanner → SKILL.md → registration+release.

**Hypothesis:** Each phase leaves CI green; tool built bottom-up with tests to the coverage floor (start 90) + bare mypy + ruff; the tool CI job runs UN-required until Phase 6; personal-plugin → 11.2.0 at release. One feature branch, commit per phase, one PR at end (human-reviewed, no auto-merge).

**Rollback Plan:** All on `impl/task-sync`; `git revert`/branch-delete per phase; `last_good_sha` in `.implement-plan-state.json`. No merge to main until the final reviewed PR. NON-NEGOTIABLE guardrail (Phase 4): never commit contact-center-lab client brand terms into this public repo.

**Actions & Results:** (per phase, below)

- Phase 1 (tool skeleton + model) COMPLETE: scaffolded `plugins/personal-plugin/tools/task-sync/` (stdlib-only package `task_sync`, argparse CLI with 8 subcommand stubs, `Task`/`TaskList` dataclass model, canonical atomic JSON store, pure-function `TASKS.md` renderer). Wired into root pyproject test aggregation + a new NON-required `Task Sync Tests` CI job (branch protection untouched — Phase 6). 63 tests / 96.8% coverage (floor 90) / mypy + ruff clean; independently re-verified (8/8 DoD checks pass).
- Phase 2 (provider abstraction) COMPLETE: normalized `Issue` model + `Provider` protocol; GitHub adapter over `gh` (subprocess), Gitea adapter over the REST API via stdlib urllib (token from tea config — needed because `tea` CLI JSON lacks updated_at/body); provider detection from the git remote (github/gitea/none). Zero runtime deps; all provider I/O mocked in tests (no live network). Coverage ≥90, mypy+ruff clean.
