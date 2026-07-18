# Implementation Plan

**Generated:** 2026-07-18
**Completed:** _(in progress)_
**Based On:** `/ultra-plan` of the approved task-sync design (`docs/plans/2026-07-18-task-sync-design.md`, D34) — user selected the Python-tool architecture (fork A). Prior plan (prime-backlog, COMPLETE) archived at `docs/archive/IMPLEMENTATION_PLAN-v10.md`.
**Total Phases:** 6
**Estimated Total Effort:** ~2,500 LOC across ~40 files (a new bundled Python tool + tests, a new skill + references, an eval, CI/registration wiring)

---

## Executive Summary

Build **task-sync**: a new `personal-plugin` skill that keeps a per-repo JSON task list reconciled with the repo's issue tracker (GitHub via `gh`, Gitea via its REST API). The design is settled (D34); this plan encodes the build.

The architecture, chosen at plan time, is a **bundled Python tool (`tools/task-sync/`) that does all deterministic work, plus a thin `SKILL.md` that owns interaction.** The tool never prompts — it runs a **plan → decide → apply** protocol: `sync --plan --json` emits everything it would push/pull/create _plus_ the conflicts and confidentiality findings that need a human call; the skill renders those, asks the user, and calls `sync --apply --decisions <file>`. This keeps the correctness-critical logic (3-way reconcile, last-write-wins, confidentiality scanning) pure and unit-testable to the repo's coverage bar, and confines LLM interaction to the skill. `--dry-run` is simply "plan, don't apply."

Two facts uncovered during investigation shape the build and must not be lost:

1. **The confidentiality "reuse" from `leak-risk-audit`/`remove-ip` does not exist** — both are prompt-only skills with no callable code. task-sync builds its own detector: a new **secret/token** detector (the number-one risk when pushing task text to an issue, which neither existing skill covers) plus **generic structural** regexes (email, phone, IP, internal hostnames) adapted from the sibling `contact-center-lab` repo. **The sensitive-terms list (client names, internal hostnames) is per-repo configuration supplied by the user — never hardcoded in this public repo.** Copying `contact-center-lab`'s hardcoded client brand terms into the marketplace would itself be a leak; do not do it.
2. **Gitea reads must use the REST API, not the `tea` CLI** — `tea`'s JSON omits `updated_at` and `body`, which would break last-write-wins. The Gitea REST API (token already in `~/.config/tea/config.yml`, network reachable) returns the full GitHub-compatible shape. Both providers therefore read via REST behind one normalized adapter interface.

No behavior in existing plugins changes. The only cross-cutting cost is a new CI test job and the branch-protection checks it adds — sequenced to avoid the D28/PLAT-012 deadlock.

---

## Plan Overview

The build is bottom-up: model (Phase 1) → providers (Phase 2) → reconcile (Phase 3) → confidentiality (Phase 4) → skill orchestration (Phase 5) → registration & release (Phase 6). Phases 1–4 are the Python tool, each independently unit-tested and green before the next. Phase 5 wires the SKILL.md to the finished tool. Phase 6 does everything required to ship a new skill in this repo and flips the CI job to required.

Critical ordering — the branch-protection deadlock is avoided by sequencing, not luck: the tool's CI job is added in Phase 1 as a **non-required** job (it runs and must be green, but no PR is blocked on a not-yet-existing check). Only in Phase 6, after six phases have proven the job green on every PR, are the two new checks added to branch protection.

Phase 3 (reconcile) and Phase 4 (confidentiality) are the correctness- and leak-critical cores and carry the heaviest tests; they run on the `opus` tier. The rest is `sonnet`.

### Phase Summary Table

| Phase | Focus | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|-------|------------------|-----------------|--------------|----------------|
| 1 | Tool skeleton & data model | `tools/task-sync/` package, `tasks.json` model + canonical store, `TASKS.md` renderer, CI job (un-required), root-pyproject aggregation | M (~10 files, ~450 LOC) | None | Sequential |
| 2 | Provider abstraction | Normalized Issue model + provider interface; GitHub (`gh`) & Gitea (REST) adapters; provider detection; fixture-mocked tests | M (~8 files, ~500 LOC) | Phase 1 | Sequential |
| 3 | Reconcile engine | 3-way classify, last-write-wins + conflict detection, status/label/milestone mapping, prune, plan/apply emitter | L (~6 files, ~600 LOC) | Phases 1–2 | Sequential |
| 4 | Confidentiality scanner | Secret detector + generic structural detectors (adapt cc-lab), per-repo terms config, keep/redact/remove/anonymize, content-hash memory | L (~6 files, ~500 LOC) | Phase 1 | Sequential |
| 5 | SKILL.md orchestration | Commands + NL, plan→decide→apply, dry-run, init, visibility guardrail, TASKS.md regen, `references/` | M (~5 files, ~450 LOC) | Phases 1–4 | Sequential |
| 6 | Registration & release | Eval, README regen, SECURITY.md egress note, ADR-0010, CHANGELOG, version bump, dependency-audit, branch-protection update | M (~12 files, ~250 LOC) | Phases 1–5 | Sequential |

### Execution Hints

| Phase | Model Tier | Notes |
|-------|-----------|-------|
| All (default) | `sonnet` | Override below |
| 3 | `opus` | Reconcile is the correctness core — a bug silently corrupts task lists |
| 4 | `opus` | Leak-critical; false negatives push secrets to a tracker |

### Milestones

- **M1 (Phases 1–2):** a testable tool that can model tasks and read/write both trackers.
- **M2 (Phases 3–4):** the tool can reconcile and scan — the hard logic, fully unit-tested.
- **M3 (Phase 5):** the skill drives the tool end-to-end from a Claude session.
- **M4 (Phase 6):** shipped — eval + README + version bump + required CI check.

---

## Constraints (Pre-Plan Gates — from Phase 0)

| Constraint | Applies to |
|-----------|-----------|
| Skill: `skills/task-sync/SKILL.md`, `name: task-sync`, body <500 lines, bulk → `references/` | Phase 5 |
| Every new skill needs an eval (the #150 coverage gate blocks merge otherwise) | Phase 6 |
| README sync guard (#149) — run `update-readme.py` or the `--check` step fails | Phase 6 |
| New functionality = version bump — personal-plugin minor (11.1.0 → 11.2.0) | Phase 6 |
| Bundled tool: pyproject/src/tests, coverage floor in `[tool.coverage.report]`, bare `mypy` (D33), ruff 0.14.10 | Phases 1–4, 6 |
| Adding a CI **job** = new required checks — coordinate with branch protection in lockstep, ordered to avoid deadlock (D28) | Phases 1, 6 |
| Tools run from source via `PYTHONPATH` — never declared in plugin.json `tools` (D3) | Phases 1, 5 |
| `python3` not `python`; tool tests need the tool `.venv/bin/python` | all |
| markdownlint MD049 consistent-emphasis / MD012; run `--config .markdownlint.json --fix` | all |
| SECURITY.md is LLM-API-egress-only — tracker egress is a new class to document | Phase 6 |
| No client-specific/proprietary terms hardcoded in this public repo (secrets management, SECURITY.md) | Phase 4 |
| Lab notebook entry before each phase's first commit (Rule 11) | all |

---

## Phase 1: Tool Skeleton & Data Model

**Estimated Complexity:** M (~10 files, ~450 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Stand up a testable `tools/task-sync/` package wired into the repo's test infrastructure.
- Define the `tasks.json` schema, a canonical (deterministic) store, and the read-only `TASKS.md` renderer.
- Add the CI test job as **non-required** so it runs green without blocking any PR.

### Work Items

#### 1.1 Scaffold the `task-sync` tool package ✅ Completed 2026-07-18
**Status: COMPLETE [2026-07-18]**
**Model Tier: sonnet**
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/pyproject.toml` (new — copy feedback-docx's shape; `fail_under = 90` to start)
- `plugins/personal-plugin/tools/task-sync/src/task_sync/__init__.py`, `__main__.py` (new — `main()` entry, argparse skeleton)
- `plugins/personal-plugin/tools/task-sync/tests/conftest.py` (new)
- `plugins/personal-plugin/tools/task-sync/requirements-lock.txt` (new)
- `pyproject.toml` (root — add tool to `testpaths` + `pythonpath`)
- `.github/workflows/test.yml` (new job "Task Sync Tests", matrix ubuntu+windows, copied from feedback-docx; **do NOT add to branch protection yet**)

**Description:**
Create the src-layout package `task_sync` with an argparse `main()` dispatching subcommands (stubs for now: `sync`, `list`, `add`, `edit`, `done`, `remove`, `status`, `init`). Minimal runtime deps (prefer stdlib `json`/`argparse`/`urllib` + dataclasses; add `httpx` only if the Gitea adapter needs it in Phase 2). Wire into root `pyproject.toml` aggregation and add the CI job.

**Acceptance Criteria:**
- [ ] WHEN `PYTHONPATH=.../task-sync/src python3 -m task_sync --help` runs THEN it SHALL list the subcommands and exit 0.
- [ ] WHEN the new CI job runs on a PR THEN it SHALL execute and be green, and SHALL NOT be in the required-checks list yet.
- [ ] WHEN root `pytest` runs THEN it SHALL discover the new tool's tests.

**Notes:** Decide dataclasses vs pydantic here; lean stdlib dataclasses for minimal deps unless Phase 2/3 validation needs pydantic. Record the choice in a code comment.

#### 1.2 Task model + canonical `tasks.json` store ✅ Completed 2026-07-18
**Status: COMPLETE [2026-07-18]**
**Model Tier: sonnet**
**Files Affected:**
- `src/task_sync/models.py` (new — `Task`, `TaskList` header dataclasses; status/priority enums)
- `src/task_sync/store.py` (new — canonical load/save, atomic write)
- `tests/test_store.py` (new)

**Description:**
Implement the schema from the design (`id`, `title`, `body`, `status`, `priority`, `labels`, `milestone`, `issue_number`, timestamps, `last_synced`, `confidentiality`) plus the file header (`provider`, `repo`, `last_sync_at`, config). Canonicalize on save: stable key order, tasks sorted by `id`, trailing newline — so git diffs are clean and sync is deterministic. Atomic write (temp + rename, like `visual_explainer/io_utils`).

**Acceptance Criteria:**
- [ ] WHEN a task list is saved twice with no changes THEN the two files SHALL be byte-identical.
- [ ] WHEN a task list is loaded and re-saved THEN unrelated fields and ordering SHALL be preserved deterministically.
- [ ] WHEN an invalid status/priority is loaded THEN it SHALL raise a clear validation error.

#### 1.3 `TASKS.md` renderer + status summary ✅ Completed 2026-07-18
**Status: COMPLETE [2026-07-18]**
**Model Tier: sonnet**
**Files Affected:**
- `src/task_sync/render.py` (new — table renderer + summary)
- `tests/test_render.py` (new)
- `references/` note that `TASKS.md` is gitignored (finalized in Phase 5/6 `.gitignore`)

**Description:**
Render the open-tasks table (the design's mock: `#`, priority, status, title, labels, blocked-marker, private-marker) and the status summary line, sortable/filterable by status/priority/milestone. Pure function `render(tasklist, filters) -> str`.

**Acceptance Criteria:**
- [ ] WHEN rendering a fixture list filtered to `status=todo` THEN only todo tasks SHALL appear, in the specified sort order.
- [ ] WHEN a task has no issue number THEN its `#` column SHALL show `—`.

### Phase 1 Testing Requirements

- [ ] `python3 -m pytest` in the tool dir passes at the coverage floor.
- [ ] `mypy src/` clean; `ruff@0.14.10 check` + `format --check` clean.
- [ ] The new CI job is green on the phase PR and absent from branch protection.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tool runs | `PYTHONPATH=plugins/personal-plugin/tools/task-sync/src python3 -m task_sync --help` | exit 0, lists subcommands |
| Tests + coverage | `cd plugins/personal-plugin/tools/task-sync && .venv/bin/python -m pytest tests/ -q` | passes at floor |
| Canonical determinism | (test in `test_store.py`) | double-save byte-identical |
| Types | `cd plugins/personal-plugin/tools/task-sync && mypy src/ --ignore-missing-imports` | 0 errors |

<!-- END DOD -->

---

## Phase 2: Provider Abstraction

**Estimated Complexity:** M (~8 files, ~500 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Sequential

### Goals

- One normalized `Issue` model and a provider interface; two adapters (GitHub via `gh`, Gitea via REST) behind it.
- Provider detection from the git remote, plus `none` (local-only) mode.
- Full test coverage using recorded fixtures — no live API calls in CI.

### Work Items

#### 2.1 Normalized Issue model + provider interface ✅ Completed 2026-07-18
**Status: COMPLETE [2026-07-18]**
**Model Tier: sonnet**
**Files Affected:**
- `src/task_sync/providers/base.py` (new — `Issue` dataclass; `Provider` protocol: `list_issues`, `create_issue`, `update_issue`, `set_state`, `ensure_labels`, `ensure_milestone`, `visibility`)
- `tests/test_providers_base.py` (new)

**Description:**
Define a provider-agnostic `Issue` (number, title, body, state, labels, milestone, updated_at, closed_at) and the `Provider` interface both adapters implement. All reconcile logic in Phase 3 speaks only this interface.

**Acceptance Criteria:**
- [ ] WHEN either adapter returns issues THEN they SHALL be normalized to the same `Issue` shape (labels as a list, timestamps as aware datetimes).

#### 2.2 GitHub adapter ✅ Completed 2026-07-18
**Status: COMPLETE [2026-07-18]**
**Model Tier: sonnet**
**Files Affected:**
- `src/task_sync/providers/github.py` (new — wraps `gh issue list --json …`, `gh issue create/edit/close/reopen`, `gh api` for milestones + visibility)
- `tests/test_provider_github.py` (new — subprocess mocked)

**Description:**
Implement the interface over `gh`. Read via `gh issue list --state all --json number,title,body,state,updatedAt,closedAt,labels,milestone`. Milestones/visibility via `gh api`. Never make live calls in tests — mock `subprocess`/`gh` output with recorded fixtures.

**Acceptance Criteria:**
- [ ] WHEN `list_issues` runs against mocked `gh` output THEN it SHALL return normalized `Issue`s including `updated_at`.
- [ ] WHEN `visibility()` runs THEN it SHALL return public/private from `gh repo view`.

#### 2.3 Gitea adapter (REST) ✅ Completed 2026-07-18
**Status: COMPLETE [2026-07-18]**
**Model Tier: sonnet**
**Files Affected:**
- `src/task_sync/providers/gitea.py` (new — REST client; token + base URL from `~/.config/tea/config.yml`; GET/POST/PATCH issues, labels, milestones)
- `tests/test_provider_gitea.py` (new — HTTP mocked)

**Description:**
Implement the interface over the Gitea REST API (`/api/v1/repos/{owner}/{repo}/issues` etc.), reading the token/URL from the tea config. This is required because the `tea` CLI JSON lacks `updated_at`/`body`. Mock HTTP in tests (recorded responses).

**Acceptance Criteria:**
- [ ] WHEN `list_issues` runs against a mocked Gitea response THEN it SHALL return normalized `Issue`s with `updated_at` and `body`.
- [ ] WHEN the token/URL is absent THEN it SHALL raise a clear, actionable error (points to `tea login`).

#### 2.4 Provider detection ✅ Completed 2026-07-18
**Status: COMPLETE [2026-07-18]**
**Model Tier: sonnet**
**Files Affected:**
- `src/task_sync/detect.py` (new — parse `git remote get-url origin` → github/gitea/none)
- `tests/test_detect.py` (new)

**Acceptance Criteria:**
- [ ] WHEN the remote host is `github.com` THEN detection SHALL return `github`; a Gitea host → `gitea`; no remote → `none` (local-only).

### Phase 2 Testing Requirements

- [ ] All adapter tests pass with mocked I/O; zero live network in CI.
- [ ] mypy/ruff clean; coverage at floor.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Provider tests | `cd plugins/personal-plugin/tools/task-sync && .venv/bin/python -m pytest tests/test_provider_*.py -q` | pass, no network |
| Detection | `.venv/bin/python -m pytest tests/test_detect.py -q` | github/gitea/none resolved |
| Types | `mypy src/ --ignore-missing-imports` | 0 errors |

<!-- END DOD -->

---

## Phase 3: Reconcile Engine

**Estimated Complexity:** L (~6 files, ~600 LOC)
**Dependencies:** Phases 1–2
**Execution Mode:** Sequential

### Goals

- The 3-way reconcile that keeps `tasks.json` and the tracker in agreement, with last-write-wins and surfaced conflicts.
- Status/priority/milestone mapping both directions; prune-on-close.
- Emit a structured **plan** (for `--dry-run` and the skill's decide step) and **apply** it with resolved decisions.

### Work Items

#### 3.1 Three-way classifier
**Status: PENDING**
**Model Tier: opus**
**Files Affected:**
- `src/task_sync/reconcile/classify.py` (new — match on `issue_number`, diff task vs issue vs `last_synced` base)
- `tests/test_classify.py` (new — the core matrix)

**Description:**
For every task/issue, classify against the `last_synced` base: new-local (no issue #), new-remote (issue not in JSON), changed-local-only, changed-remote-only, changed-both, unchanged. `last_synced` stores a content hash + timestamp so "changed since last sync" is decidable on each side.

**Acceptance Criteria:**
- [ ] WHEN only the local task changed since base THEN it SHALL classify as changed-local-only.
- [ ] WHEN both sides changed THEN it SHALL classify as changed-both (a conflict candidate).
- [ ] WHEN an issue exists with no matching task THEN it SHALL classify as new-remote (adopt).

#### 3.2 Resolution + field mapping
**Status: PENDING**
**Model Tier: opus**
**Files Affected:**
- `src/task_sync/reconcile/resolve.py` (new — last-write-wins by `updated_at`; conflicts emitted, not auto-resolved)
- `src/task_sync/reconcile/mapping.py` (new — status ↔ `status/*` label + open/closed; priority ↔ `priority/*`; milestone both ways)
- `tests/test_resolve.py`, `tests/test_mapping.py` (new)

**Description:**
One-sided changes apply to the other side. Two-sided conflicts are collected into the plan for the human to resolve (not silently clobbered). Map the five statuses onto issue state + `status/*` labels (design table), priority onto `priority/*`, and milestone both ways, creating labels/milestones on the tracker as needed.

**Acceptance Criteria:**
- [ ] WHEN a conflict exists THEN resolution SHALL emit it as a pending decision, never overwrite.
- [ ] WHEN `status=in-progress` pushes THEN the issue SHALL be open with a `status/in-progress` label and no other `status/*` label.
- [ ] WHEN an issue is closed remotely THEN the task SHALL become `done` on pull.

#### 3.3 Plan/apply + prune
**Status: PENDING**
**Model Tier: opus**
**Files Affected:**
- `src/task_sync/reconcile/plan.py` (new — build a `SyncPlan` [creates/pushes/pulls/conflicts/confidentiality-findings]; serialize to JSON)
- `src/task_sync/reconcile/apply.py` (new — execute a plan + a decisions file; refresh `last_synced`; prune `done` closed > N days)
- `src/task_sync/cli` wiring for `sync --plan/--apply/--dry-run`
- `tests/test_plan_apply.py`, `tests/test_prune.py` (new)

**Description:**
`--plan` produces the JSON plan and writes nothing. `--apply --decisions <file>` executes it, applying human resolutions for conflicts and confidentiality findings, then updates `last_synced` and prunes stale `done` tasks (leaving the closed issue as the archive). `--dry-run` == `--plan` with a human-readable summary.

**Acceptance Criteria:**
- [ ] WHEN `sync --dry-run` runs THEN it SHALL print the plan and write nothing (verified by a clean git status + unchanged tasks.json).
- [ ] WHEN `sync --apply` runs with a decisions file THEN it SHALL execute exactly the planned actions and refresh `last_synced`.
- [ ] WHEN a `done` task's issue closed > N days ago THEN apply SHALL prune it from `tasks.json` and leave the issue closed.

### Phase 3 Testing Requirements

- [ ] The classify matrix and conflict cases are exhaustively unit-tested against fixtures.
- [ ] `--dry-run` provably writes nothing.
- [ ] mypy/ruff clean; coverage at floor (this phase should push overall coverage up, not down).

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Reconcile tests | `cd plugins/personal-plugin/tools/task-sync && .venv/bin/python -m pytest tests/test_classify.py tests/test_resolve.py tests/test_plan_apply.py -q` | pass |
| Dry-run writes nothing | (test: run `sync --dry-run` on a fixture repo, assert tasks.json unchanged) | unchanged |
| Types | `mypy src/ --ignore-missing-imports` | 0 errors |

<!-- END DOD -->

---

## Phase 4: Confidentiality Scanner

**Estimated Complexity:** L (~6 files, ~500 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Sequential

### Goals

- Detect secrets/tokens and configurable sensitive terms in task content before anything is pushed.
- Offer keep/redact/remove/anonymize per finding; apply deterministically; remember by content hash.
- Ship only generic detectors — no client-specific terms in this public repo.

### Work Items

#### 4.1 Secret/token detector
**Status: PENDING**
**Model Tier: opus**
**Files Affected:**
- `src/task_sync/confidential/secrets.py` (new — regexes: `ghp_`/`gho_`/`github_pat_`, `sk-`, AWS `AKIA`, PEM blocks, generic bearer/high-entropy)
- `tests/test_secrets.py` (new — positive + negative fixtures)

**Description:**
The primary tracker-push risk. Detect common secret shapes with precise regexes (favor precision to limit false positives, but never miss the well-known token formats). GitGuardian remains an advisory CI backstop; this is the primary gate.

**Acceptance Criteria:**
- [ ] WHEN a task body contains a `ghp_…` token THEN it SHALL be flagged CRITICAL.
- [ ] WHEN a task contains an ordinary sentence THEN it SHALL NOT be flagged (no false positive on the negative-fixture corpus).

#### 4.2 Structural identifier detectors (adapt cc-lab, generic only)
**Status: PENDING**
**Model Tier: opus**
**Files Affected:**
- `src/task_sync/confidential/patterns.py` (new — GENERIC regexes adapted from `contact-center-lab/pipeline/stage_B_redaction/patterns.py`: email, phone, IPv4, internal-hostname TLDs, ticket/asset IDs — with an attribution comment)
- `tests/test_patterns.py` (new)

**Description:**
Adapt only the **structural, non-client-specific** regexes. **Do NOT copy `contact-center-lab`'s hardcoded brand/company term lists (`leak_scan.py`) into this repo** — those are client-identifying and would leak. Client/sensitive terms come from per-repo config (4.3), not code.

**Acceptance Criteria:**
- [ ] WHEN task text contains an email or an internal `*.corp`/`*.internal` hostname THEN it SHALL be flagged.
- [ ] WHEN the repo is grepped for known client brand strings THEN NONE SHALL be present in the tool source (verified by a test/CI check).

#### 4.3 Terms config, dispositions, and memory
**Status: PENDING**
**Model Tier: opus**
**Files Affected:**
- `src/task_sync/confidential/scan.py` (new — combine detectors + per-repo sensitive-terms list from the tasks.json header/config; produce findings)
- `src/task_sync/confidential/apply.py` (new — keep [no-op], redact [mask], remove [drop], anonymize [stable-token map]; content-hash memory)
- `tests/test_scan.py`, `tests/test_confidential_apply.py` (new)

**Description:**
A finding carries {span, category, severity, suggestion}. Dispositions transform the stored task (redact/remove/anonymize) or leave it (keep), and are recorded as `confidentiality: {decision, reviewed_hash, at}`. On re-scan, unchanged content (hash match) is honored silently; changed content re-scans. Anonymize uses a deterministic stable-token map in the tool; a richer Claude-judged generalization is an optional skill-layer enhancement (Phase 5), not required here.

**Acceptance Criteria:**
- [ ] WHEN a finding is dispositioned `redact` THEN the stored task SHALL have the span masked and the decision remembered.
- [ ] WHEN a previously-reviewed task is unchanged THEN a re-scan SHALL NOT re-flag it.
- [ ] WHEN the task text changes THEN the finding SHALL re-surface.

### Phase 4 Testing Requirements

- [ ] Detector precision/recall verified on positive + negative fixtures.
- [ ] A test/CI check asserts no client-specific terms exist in the tool source.
- [ ] mypy/ruff clean; coverage at floor.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Confidentiality tests | `cd plugins/personal-plugin/tools/task-sync && .venv/bin/python -m pytest tests/test_secrets.py tests/test_patterns.py tests/test_scan.py -q` | pass |
| No client terms in source | `grep -rIER '<known-client-brand-regex>' plugins/personal-plugin/tools/task-sync/src \|\| echo CLEAN` | CLEAN |
| Types | `mypy src/ --ignore-missing-imports` | 0 errors |

<!-- END DOD -->

---

## Phase 5: SKILL.md Orchestration

**Estimated Complexity:** M (~5 files, ~450 LOC)
**Dependencies:** Phases 1–4
**Execution Mode:** Sequential

### Goals

- The `task-sync` skill: commands + natural language, driving the tool via plan → decide → apply.
- Own all interaction (conflict prompts, confidentiality dispositions, table rendering), dry-run, init, the public-repo visibility guardrail, and `TASKS.md` regeneration.

### Work Items

#### 5.1 SKILL.md (frontmatter + body)
**Status: PENDING**
**Model Tier: sonnet**
**Files Affected:**
- `plugins/personal-plugin/skills/task-sync/SKILL.md` (new — `name: task-sync`, description ≤1024 with triggers, body <500 lines)
- `plugins/personal-plugin/skills/task-sync/references/*.md` (new — command reference, sync semantics, confidentiality flow, config)

**Description:**
Author the skill via `/new-skill` conventions. Commands: `sync` (default), `list`/`ls`, `add`, `edit`, `done`/`close`, `remove`/`rm`, `status`, `init`; natural-language equivalents. Body stays under 500 lines — detail in `references/`. Invoke the tool via `PYTHONPATH="$CLAUDE_PLUGIN_ROOT/tools/task-sync/src" python3 -m task_sync …`.

**Acceptance Criteria:**
- [ ] WHEN `plugin validate --strict` runs THEN the skill SHALL pass (name==dir, valid frontmatter).
- [ ] WHEN the SKILL.md body is counted THEN it SHALL be < 500 lines.

#### 5.2 Plan → decide → apply orchestration
**Status: PENDING**
**Model Tier: sonnet**
**Files Affected:**
- `SKILL.md` (the orchestration section)

**Description:**
The skill runs `sync --plan --json`, renders the plan (creates/pushes/pulls) plus any conflicts and confidentiality findings as tables, prompts the user for each decision, writes a decisions file, and runs `sync --apply --decisions`. It warns loudly before pushing to a **public** repo (visibility guardrail), supports `--dry-run` (plan only), auto-`init`s on first run, and regenerates the gitignored `TASKS.md` after apply.

**Acceptance Criteria:**
- [ ] WHEN a sync surfaces a conflict THEN the skill SHALL present both sides and apply only the user's choice.
- [ ] WHEN the repo is public THEN the skill SHALL warn before the first push.
- [ ] WHEN `--dry-run` is used THEN the skill SHALL show the plan and write nothing.

### Phase 5 Testing Requirements

- [ ] `plugin validate --strict` passes; SKILL.md < 500 lines; markdownlint clean.
- [ ] An end-to-end smoke test of the tool's plan/apply against a fixture git repo (local-only mode) succeeds.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Skill validates | `npx --yes @anthropic-ai/claude-code@2.1.204 plugin validate plugins/personal-plugin --strict` | exit 0 |
| Body under budget | `wc -l plugins/personal-plugin/skills/task-sync/SKILL.md` | < 500 |
| Markdown lint | `npx markdownlint-cli --config .markdownlint.json plugins/personal-plugin/skills/task-sync/**/*.md` | exit 0 |

<!-- END DOD -->

---

## Phase 6: Registration & Release

**Estimated Complexity:** M (~12 files, ~250 LOC)
**Dependencies:** Phases 1–5
**Execution Mode:** Sequential

### Goals

- Everything required to ship a new skill in this repo, and flip the CI job to required now that it is proven green.

### Work Items

#### 6.1 Eval + README + docs
**Status: PENDING**
**Model Tier: sonnet**
**Files Affected:**
- `evals/skills/task-sync.eval.md` (new — scenarios: init, add, push-create, adopt-remote, conflict, confidentiality disposition, prune; passes the #150 structural gate)
- `README.md` (regenerated via `update-readme.py`)
- `SECURITY.md` (new subsection: issue-tracker egress + the confidentiality scan)
- `docs/PLUGIN-DEVELOPMENT.md` (optional — note task-sync as the reference tool-backed skill)

**Acceptance Criteria:**
- [ ] WHEN `check_eval_mapping.py` runs THEN task-sync SHALL be covered (eval present and well-formed).
- [ ] WHEN `update-readme.py --check` runs THEN it SHALL exit 0 (README lists task-sync).
- [ ] WHEN SECURITY.md is read THEN it SHALL document the tracker egress class.

#### 6.2 ADR-0010 + CHANGELOG + version bump
**Status: PENDING**
**Model Tier: sonnet**
**Files Affected:**
- `docs/adr/0010-task-sync-tool-architecture.md` (new — Status Accepted; Python tool + plan/apply + REST providers; alternatives: bash+jq, tea-CLI reads)
- `CHANGELOG.md` (new task-sync entry)
- `plugins/personal-plugin/.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` (version 11.1.0 → **11.2.0**, lockstep)

**Acceptance Criteria:**
- [ ] WHEN ADR-0010 is read THEN it SHALL record the tool-vs-bash decision with alternatives.
- [ ] WHEN version-sync validation runs THEN plugin.json and marketplace.json SHALL both read 11.2.0.

#### 6.3 CI registration + branch protection
**Status: PENDING**
**Model Tier: sonnet**
**Files Affected:**
- `.github/workflows/test.yml` (add task-sync lock to the `dependency-audit` job; optionally add a `python-compat` step — advisory)
- Branch protection (via `gh api`) — add `Task Sync Tests (ubuntu-latest)` + `(windows-latest)` to required checks

**Description:**
Now that the job has been green across Phases 1–5, add its two checks to branch protection. Order: ensure the release PR is green first, then `gh api … --method PATCH` the required-checks list, then merge. This is the only step that touches branch protection and it happens last (avoids the D28 deadlock).

**Acceptance Criteria:**
- [ ] WHEN the required-checks list is read after this item THEN it SHALL include the two Task Sync checks (16 total).
- [ ] WHEN `pip-audit` runs THEN it SHALL include the task-sync lock file.

### Phase 6 Testing Requirements

- [ ] All 14 (→16) required checks green; eval-mapping + README `--check` + plugin validate --strict pass.
- [ ] markdownlint clean across new docs.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Eval covered | `python3 scripts/check_eval_mapping.py` | exit 0 |
| README synced | `python3 scripts/update-readme.py --check` | exit 0 |
| Version sync | `grep -r '"version": "11.2.0"' plugins/personal-plugin/.claude-plugin .claude-plugin/marketplace.json` | both match |
| Branch protection | `gh api repos/davistroy/claude-marketplace/branches/main/protection --jq '.required_status_checks.contexts \| length'` | 16 |

<!-- END DOD -->

---

## Risk Mitigation

| Risk | Phase/Item | Severity | Mitigation | Rollback |
|------|-----------|----------|-----------|----------|
| Copying `contact-center-lab` client terms into this public repo (leak) | 4.2 | **High** | Adapt only generic structural regexes; terms are per-repo config; a CI check asserts no client terms in source | Revert; strip the terms |
| Branch-protection deadlock from a new required check | 1.1 → 6.3 | Medium | Add job un-required in Phase 1; require it only in Phase 6 after it is proven green | Remove the check from protection |
| Reconcile bug silently corrupts a task list | Phase 3 | Medium | Plan/apply split, `--dry-run` default posture, exhaustive unit tests, committed `last_synced` base | Revert the sync via git (tasks.json is committed) |
| Secret slips into an issue (detector false negative) | 4.1 | Medium | Precise well-known-token regexes + GitGuardian backstop + public-repo visibility guardrail | Close/delete the issue; rotate the secret |
| Gitea API pagination/rate limits on large repos | 2.3 | Low | Paginate reads; back off on 429 | n/a |
| Windows CI portability (paths, subprocess) | all | Low | Pure Python, `pathlib`, no shell assumptions; the matrix catches it | Fix per failure |

## Unknowns Register

| Unknown | Severity | Affects | Resolution |
|---------|----------|---------|-----------|
| dataclasses vs pydantic for the models | Low | 1.2 | Decide in 1.1; lean stdlib dataclasses unless validation grows |
| Anonymize quality: deterministic stable-token vs Claude-judged generalization | Low | 4.3 / 5.2 | Ship deterministic in the tool; optional Claude generalization in the skill |
| Exact secret-regex set (precision vs recall) | Medium | 4.1 | Tune against a fixture corpus; favor precision + GitGuardian backstop |
| Gitea milestone/label API shape vs GitHub | Low | 2.3, 3.2 | Both are GitHub-compatible; verify with recorded fixtures |

## Scope Boundaries

**Covered:** the task-sync skill + bundled Python tool, GitHub + Gitea providers, reconcile with conflict surfacing, confidentiality scan, `TASKS.md`, per-repo config, full registration + release.

**Explicitly NOT covered (v1):**
- Cross-machine private tasks (the one-list design has no travelling private lane).
- A standalone interactive TUI (the in-session table is the view).
- `/ultra-plan` ↔ `/implement-plan` milestone auto-wiring (a phase-2 integration).
- Issue comment/attachment sync (core fields only).
- Cross-repo aggregation (per-repo only).

## Generated ADRs

| ADR | Title | Status | Change Set |
|-----|-------|--------|-----------|
| ADR-0010 | task-sync tool architecture (Python tool, plan/apply, REST providers) | Proposed → Accepted (6.2) | Phase 6 |

## Execution Notes

- One branch + PR + merge per phase; each PR green on all required checks before merge.
- The tool's CI job runs from Phase 1 but is **not** a required check until Phase 6 — this is the deadlock-avoidance ordering; do not add it to branch protection earlier.
- personal-plugin bumps to **11.2.0** in Phase 6 (a feature); marketplace_version unchanged (no schema change).
- Log a LAB_NOTEBOOK entry before the first commit of each phase (Rule 11).
- Suggested verification points: stop after Phase 3 (reconcile proven) and Phase 5 (skill drives the tool) before proceeding.
- `contact-center-lab` is a working dir — read it to adapt the generic patterns; never copy client-identifying content into this repo.

---

_Plan generated by `/ultra-plan` on 2026-07-18 from `docs/plans/2026-07-18-task-sync-design.md` (D34). Prior plan archived at `docs/archive/IMPLEMENTATION_PLAN-v10.md`._
