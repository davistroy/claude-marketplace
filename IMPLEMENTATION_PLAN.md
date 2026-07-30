# Implementation Plan

**Generated:** 2026-07-30
**Based On:** `/ultra-plan` over the 13-item close-the-loop + hygiene backlog (LAB_NOTEBOOK E062). Phase 1 dispatched **6 parallel Explore agents** clustered by shared code path; **every cluster returned corrections**, including two to issues filed earlier in the same session. This plan encodes the *investigated* shape of each item, not the filed text. Prior plan (16-issue correctness backlog, 42/42 COMPLETE) archived at `docs/archive/IMPLEMENTATION_PLAN-v12.md`.
**Total Phases:** 8
**Estimated Total Effort:** ~85 work sites across ~35 files — predominantly markdown behavior-surfaces, plus one new CI gate script, one generator extension, and one Python test module

---

## Executive Summary

This plan closes 13 open issues that share three root causes, none of which is "a bug in a feature." The first is **a documented step with no gate behind it** — the repo's most-repeated defect (E043, E056, E057), now instantiated as a missing version-bump check (#226), 28 missing CHANGELOG entries (#210), and 12 freshness stamps that assert a verification nobody performed (#218). The second is **a check that restates an external truth and therefore drifts into agreeing with the bug** — eval scenario S4 asserting dispatch behavior another marketplace owns (#227), and `ultra-plan.eval.md:43` having copied the very phase-numbering defect it should catch (#231). The third is **fixing instances while leaving the mould** — the generator layer that mints defects into every future artifact (#218's two document templates, #223's three interaction templates, #206's under-scoped inventory generator).

Phase 1 investigation changed the plan's shape four times. My own opening hypothesis — that #226, #210 and #218 were one gate — was **refuted on evidence** (D61): the three differ on input, offline-decidability, CI-runnability and event-leg sensitivity, and #218's ground truth lives behind an API key doctrine forbids CI from holding. The honest decomposition is 2 + 1. Worse, #226 and #210 turned out to be in **direct tension** on `plugins/*/CHANGELOG.md` — #210's own remediation is a CHANGELOG-only PR with no version bump, which #226's gate would hard-block, while #210's enforcement half wants that path mandatory on a bump. That forces the backfill ahead of the gate and the gate into two conditional rules rather than one.

Interrelated issues are grouped into integrated change sets rather than isolated patches: #228 and #227 are one item because they edit the same file and two PRs would revert each other's line context; #231 is atomic across three files because fixing the skill without its eval converts a passing check into a false failure; #223 and #233 are one set because they are the same defect class. Four design forks were resolved by the user with explicit alternatives recorded as D62–D65.

---

## Plan Overview

Phases are ordered by **dependency, not priority label**. The critical path is **1 → 2** (CHANGELOG truth must land before the gate that would block it). Phases 3–8 share no files with each other or with the critical path and are fully parallelizable.

Two phases carry a trap that `Depends On` alone would miss, so both are marked Sequential internally: Phase 4 (`ultra-plan`) must edit `SKILL.md`, its eval, and `adr-template.md` in one commit; Phase 3 (evals) must apply #228's section and #227's re-scope to one file in one pass.

Phase 2 is the highest-risk item in the plan and the only one that can redden `main`. It is the sole `opus`-tier phase for that reason, and it carries a mandatory negative test before wiring.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|------------|------------------|-----------------|--------------|----------------|
| 1 | CHANGELOG truth (#210) | 28 backfilled entries across 3 plugin CHANGELOGs | M (~3 files, ~200 lines) | None | Sequential |
| 2 | Release-integrity gate (#226 + #210 enforcement) | `scripts/check_version_bump.py`, deepened checkout, CI step, pre-commit check | L (~4 files, ~250 LOC) | Phase 1 | Sequential |
| 3 | Eval trustworthiness (#228 + #227) | Harness section, 6 re-scoped scenarios, 2 rubric rows, upstream report | M (~3 files) | None | Sequential |
| 4 | ultra-plan correctness (#231) | 29 sites across SKILL.md + eval + adr-template | M (~3 files) | None | Sequential |
| 5 | `/unlock` actually works (#217) | `$TROY`→`BWS_ACCESS_TOKEN`, `allowed-tools`, probe leak | S (~3 files) | None | Sequential |
| 6 | Inventory generator (#206) | `update-readme.py` target list, CLAUDE.md block, 6 deprecated sites | M (~10 files, ~80 LOC) | None | Sequential |
| 7 | Consent-gate consistency (#223 + #233) | 4 gates converted, 3 generator templates | M (~8 files) | None | Parallel |
| 8 | Freshness stamps + task-sync (#218 + #230 + #224) | 12 stamps deleted, D34 superseded, CLI-level decisions test | M (~13 files, ~150 LOC) | None | Parallel |

### Execution Hints

| Phase | Model Tier | Context Budget | Notes |
|-------|------------|----------------|-------|
| All (default) | `sonnet` | Standard | Predominantly markdown edits against fully-specified site lists |
| Phase 2 | `opus` | Extended | The only phase that can redden a required check on `main`. Event-leg branching, shallow-clone semantics, and two conditional rules in tension — judgment work, not mechanical |
| Phase 6 | `opus` | Extended | Mechanically edits an always-loaded file; the generator extension must preserve hand-written annotation prose while regenerating name lists |

### Milestones

| Milestone | Phases | Description |
|-----------|--------|-------------|
| Gate restored | 1–2 | The repo can no longer ship a plugin change without a version bump or a CHANGELOG entry. Closes the defect that invalidated the last task's eval run |
| Evidence trustworthy | 1–4 | Eval results mean something; the planning skill no longer routes on an invented variable |
| Complete | 1–8 | All 13 issues closed; every generator that mints a defect is fixed alongside its instances |

<!-- BEGIN PHASES -->

---

## Phase 1: CHANGELOG Truth

**Estimated Complexity:** M (~3 files, ~200 lines)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Restore all three per-plugin CHANGELOGs to agreement with the root CHANGELOG
- Land before Phase 2's gate, which would otherwise block this very change

### Work Items

#### 1.1 Backfill the 28 missing per-plugin CHANGELOG entries
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #210
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/CHANGELOG.md` (modify)
- `plugins/bpmn-plugin/CHANGELOG.md` (modify)
- `plugins/slide-gen/CHANGELOG.md` (modify)

**Description:**
The issue names 2 missing versions. Verification found **24** missing from personal-plugin, **3** from bpmn-plugin (`4.4.0`, `2.1.0`, `2.0.0`), and **1** from slide-gen (`1.3.0`) — and **all three plugins are missing their current shipped version**. Backfill by *extraction* from the root `CHANGELOG.md`, never by paraphrase, or drift is reintroduced in the opposite direction.

personal-plugin's 24, newest first: `11.6.0, 11.3.0, 11.2.0, 11.1.0, 9.2.0, 9.1.0, 9.0.0, 7.0.1, 6.8.0, 6.7.2, 6.4.0, 6.3.0, 4.0.0, 3.14.0, 3.12.0, 3.11.1, 3.11.0, 3.7.2, 3.7.1, 3.6.1, 3.3.0, 3.2.0, 3.1.0, 3.0.0`.

The root CHANGELOG uses at least four heading grammars (`[plugin vX.Y.Z]`, `[plugin X.Y.Z]`, a combined `[marketplace vA, plugin vB, …]`, and bare `[X.Y.Z]`). Parse all four when locating source sections, or entries will be silently under-extracted.

**Tasks:**
1. [ ] Extract each missing version's section from root `CHANGELOG.md`, handling all four heading grammars
2. [ ] Insert into the correct per-plugin file in descending version order, preserving Keep-a-Changelog format (declared at each file's `:5-6`)
3. [ ] Verify no version present in a plugin file but absent from root is disturbed — 9 personal-plugin and 10 bpmn-plugin versions are pre-consolidation history, not defects
4. [ ] Run `markdownlint-cli2` over all three files before committing

**Acceptance Criteria:**
- [ ] WHEN the version set of each `plugins/*/CHANGELOG.md` is compared against the versions attributed to that plugin in the root CHANGELOG THEN every root-attributed version SHALL be present in the plugin file
- [ ] WHEN each plugin's `plugin.json` version is read THEN that exact version SHALL have an entry in its plugin CHANGELOG
- [ ] No version bump in this change set — backfilling history is not a release (D45)
- [ ] `markdownlint-cli2` exits 0

**Notes:**
This must land **before** Phase 2. A CHANGELOG-only PR bumps nothing, which Phase 2's gate would reject unless the exemption is already in place. Landing the data fix first removes the ordering hazard entirely.

---

### Phase 1 Testing Requirements

- [ ] No automated tests — documentation-only change
- [ ] Manual verification: version-set diff between root and each plugin file is empty in the root→plugin direction

### Phase 1 Completion Checklist

- [ ] All work items complete
- [ ] `markdownlint-cli2` clean
- [ ] No `plugin.json` modified
- [ ] LAB_NOTEBOOK entry updated

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Lint | `npx markdownlint-cli2 "plugins/*/CHANGELOG.md"` | Exit code 0 |
| Version presence | `for p in personal-plugin bpmn-plugin slide-gen; do v=$(python3 -c "import json;print(json.load(open('plugins/$p/.claude-plugin/plugin.json'))['version'])"); grep -q "\[$v\]" plugins/$p/CHANGELOG.md \|\| echo "MISSING $p $v"; done` | No output |
| Plugin validation | `claude plugin validate plugins/personal-plugin --strict` | Exit code 0 |

<!-- END DOD -->

---

## Phase 2: Release-Integrity Gate

**Estimated Complexity:** L (~4 files, ~250 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Sequential

### Goals

- Make "content changed ⇒ version changed" and "version changed ⇒ CHANGELOG entry added" machine-checkable
- Land it without reddening a required check on `main`

### Work Items

#### 2.1 Deepen the checkout in the `plugin-validate` job
**Status: PENDING**
**Model Tier: opus**
**Issue Refs:** #226
**Depends On:** None
**Files Affected:**
- `.github/workflows/validate.yml` (modify)

**Description:**
`validate.yml:304-305` checks out with **no `with:` block**, so `actions/checkout` defaults to `fetch-depth: 1` — a single-commit shallow clone with no base commit and no merge-base. `grep -rn "fetch-depth" .github/ scripts/` returns **zero** hits repo-wide, so there is no precedent to copy. Any diff-derived gate is impossible until this changes.

**Tasks:**
1. [ ] Add `with: fetch-depth: 0` to the `Checkout repository` step in the `plugin-validate` job only
2. [ ] Confirm the job name string `Validate Plugins (official CLI)` is byte-identical after the edit — it is one of 16 required contexts

**Acceptance Criteria:**
- [ ] WHEN the `plugin-validate` job runs THEN `git merge-base` between the PR base and head SHALL resolve without error
- [ ] The `name:` value of every job in `validate.yml` is unchanged (D22 — required-check names are load-bearing)

**Notes:**
Full history on this repo is small; `fetch-depth: 0` is cheaper than the fragility of a computed depth.

---

#### 2.2 Write `scripts/check_version_bump.py` with two conditional rules
**Status: PENDING**
**Model Tier: opus**
**Issue Refs:** #226, #210
**Depends On:** 2.1
**Files Affected:**
- `scripts/check_version_bump.py` (create)

**Description:**
One stdlib-only script (the `plugin-validate` job has no `setup-python` step and all four existing script steps are stdlib-only — adding a dependency would force a new step). It implements **two conditional rules**, not one, because #226 and #210 are in direct tension on `plugins/*/CHANGELOG.md`:

- **Rule 1 (bump-required):** if any *bump-worthy* path under `plugins/<name>/` changed, then `plugins/<name>/.claude-plugin/plugin.json`'s `version` must have changed.
- **Rule 2 (changelog-required):** if `plugins/<name>/.claude-plugin/plugin.json`'s `version` changed, then `plugins/<name>/CHANGELOG.md` must contain an entry for the new version.

`CHANGELOG.md` is **exempt from Rule 1 and mandatory under Rule 2** — that conditional is the whole reason this is one script rather than two gates.

Bump-worthy paths, derived from the 375-file census: everything under `plugins/<name>/` **except** `CHANGELOG.md`, `LICENSE`, `README.md`, `tools/*/tests/**`, and `examples/**`. Per-plugin, never "any plugin changed ⇒ all three bump" (D45 forbids empty coordinated bumps).

**Tasks:**
1. [ ] Implement per-plugin diff classification from `git diff --name-only <base>...<head>`
2. [ ] Read both old and new `plugin.json` via `git show <ref>:<path>` — derive both sides, never restate a constant
3. [ ] Implement Rule 1 with the exemption list, and Rule 2 keyed on the *new* version string
4. [ ] Branch explicitly on event leg: on `pull_request` use base↔head; on `push` to main **exit 0 with an explanatory message** — there is no meaningful base and the PR leg already gated the content
5. [ ] Add `--self-test` that constructs synthetic diffs and asserts exit 1 on each violation and exit 0 on each exemption
6. [ ] Emit the offending plugin, rule, and remediation command (`/bump-version <plugin> <level>`) on failure

**Acceptance Criteria:**
- [ ] WHEN a PR modifies `plugins/<name>/skills/**` without changing that plugin's `version` THEN the script SHALL exit non-zero naming the plugin and Rule 1
- [ ] WHEN a PR modifies only `plugins/<name>/CHANGELOG.md` THEN the script SHALL exit 0 (Rule 1 exemption — this is Phase 1's own shape)
- [ ] WHEN a PR bumps `version` without adding a matching `CHANGELOG.md` entry THEN the script SHALL exit non-zero naming Rule 2
- [ ] WHEN the script runs on the `push`-to-`main` leg THEN it SHALL exit 0 and print why, never attempting a base diff
- [ ] WHEN a PR modifies only `plugins/bpmn-plugin/tools/bpmn2drawio/tests/**` THEN the script SHALL exit 0
- [ ] `python3 scripts/check_version_bump.py --self-test` exits 0, and each synthetic violation within it is asserted to exit 1
- [ ] Script imports only stdlib

**Notes:**
The push-leg branch is itself the E043 hazard: a condition written wrong no-ops on *both* legs and converts "unchecked" into a false "checked". Task 5's self-test must assert the PR leg still fails, not merely that the push leg passes.

---

#### 2.3 Negative-test the gate against a deliberately-bad branch before wiring it
**Status: PENDING**
**Model Tier: opus**
**Issue Refs:** #226
**Depends On:** 2.2
**Files Affected:**
- (none — verification only)

**Description:**
CLAUDE.md's standing rule: a verification guard that cannot fail is worse than none, and this repo has shipped three of them. Before the script is referenced from CI, prove it fails on real input, not only on synthetic fixtures.

**Tasks:**
1. [ ] Create a scratch branch; edit one file under `plugins/personal-plugin/skills/` without bumping; run the script against `main...HEAD`; confirm **exit 1**
2. [ ] Bump the version but add no CHANGELOG entry; confirm **exit 1** citing Rule 2
3. [ ] Add the CHANGELOG entry; confirm **exit 0**
4. [ ] Edit only `plugins/personal-plugin/CHANGELOG.md`; confirm **exit 0**
5. [ ] Record all four observed exit codes in the LAB_NOTEBOOK entry
6. [ ] Delete the scratch branch

**Acceptance Criteria:**
- [ ] All four scenarios produce the documented exit code, observed and recorded — not asserted in prose
- [ ] WHEN the guard is wired into CI THEN its failing behavior SHALL already have been demonstrated on a real branch

---

#### 2.4 Wire the gate as a step in `plugin-validate` and a pre-commit check
**Status: PENDING**
**Model Tier: opus**
**Issue Refs:** #226
**Depends On:** 2.3
**Files Affected:**
- `.github/workflows/validate.yml` (modify)
- `scripts/pre-commit` (modify)

**Description:**
A **step**, never a job (D28) — a new job creates a new required check that must be coordinated with branch protection or it deadlocks merges. This mirrors `check_agent_models.py`'s dual wiring (CI step at `validate.yml:341` + pre-commit Check 5 at `scripts/pre-commit:202-221`), which is the house shape precisely because it adds zero job keys.

The pre-commit leg needs a **new staged-file filter**: the existing one at `scripts/pre-commit:36` matches only `commands/*.md` and `skills/*/SKILL.md`, so it cannot see `tools/`, `references/`, `agents/`, or `hooks/`.

**Tasks:**
1. [ ] Add the step to the `plugin-validate` job, after `check_agent_models.py`, with a comment noting stdlib-only
2. [ ] Add pre-commit Check 7 with a filter covering all bump-worthy paths
3. [ ] Verify the 16 required contexts are unchanged: `gh api repos/davistroy/claude-marketplace/branches/main/protection --jq '.required_status_checks.contexts | length'` returns 16

**Acceptance Criteria:**
- [ ] WHEN `validate.yml` is parsed THEN the set of `name:` values SHALL be identical to before this change
- [ ] The live required-context count remains 16
- [ ] WHEN a plugin file is staged without a version bump THEN `scripts/pre-commit` SHALL exit non-zero

---

### Phase 2 Testing Requirements

- [ ] `--self-test` passes and internally asserts non-zero exits on bad input
- [ ] All four negative-test scenarios from 2.3 observed and recorded
- [ ] No new required status check introduced

### Phase 2 Completion Checklist

- [ ] All work items complete
- [ ] Required-context count verified at 16
- [ ] Negative-test results recorded in LAB_NOTEBOOK
- [ ] `main`'s push build green after merge

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Self-test | `python3 scripts/check_version_bump.py --self-test` | Exit code 0 |
| Stdlib-only | `python3 -c "import ast,sys; t=ast.parse(open('scripts/check_version_bump.py').read()); mods={n.module or '' for n in ast.walk(t) if isinstance(n,ast.ImportFrom)}\|{a.name.split('.')[0] for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names}; print(sorted(mods))"` | No third-party modules |
| Required checks | `gh api repos/davistroy/claude-marketplace/branches/main/protection --jq '.required_status_checks.contexts \| length'` | Returns `16` |
| Pre-commit | `bash scripts/pre-commit` | Exit code 0 on a clean tree |

<!-- END DOD -->

---

## Phase 3: Eval Trustworthiness

**Estimated Complexity:** M (~3 files)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Make the `description-triggers` results reproducible by a cold runner
- Stop asserting outcomes another marketplace owns — in all 6 fragile scenarios, not just the one that failed

### Work Items

#### 3.1 Add harness documentation — generalizable facts to `evals/README.md`, the Bash prohibition to the eval
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #228
**Depends On:** None
**Files Affected:**
- `evals/README.md` (modify)
- `evals/skills/description-triggers.eval.md` (modify)

**Description:**
Four of the five harness facts are not eval-specific and belong in `evals/README.md` under "Running Evals" (`:89`), where ADR-0009 and D32 already point readers: the `Skill` tool is auto-denied headless without explicit `--allowed-tools`; `AskUserQuestion` is unavailable in `-p` sessions and its absence must not score as a gate failure; `api_error_status: 529` is not a result (8 of 13 in the first batch); score at first dispatch rather than budgeting five minutes.

The fifth — **`Bash` must be disallowed** — is scenario-specific and belongs in the eval file with its justification: S13's prompt names the Jetson, and **three installed skills in this same plugin grant `Bash(ssh:*)` to that host** (`jetson-audit/SKILL.md:5`, `fleet-health/SKILL.md:4`, `jetson-recon`). This is a live-fire safety control, not tidiness.

**Three linter traps, reproduced against `validate_structure`:**
- Heading the section `### S0: Harness` makes it a **scenario** and fails the build.
- A file-level `## Harness` carrying `**Invocation:**` does **not** satisfy the per-file invocation requirement — `seen_invocation` is computed inside scenario bodies only. **All 14 `**Context:**` lines must stay where they are.**
- A plain `## Harness` heading is *ignored* by the linter, which is why it is safe.

**Tasks:**
1. [ ] Add a "Headless Execution" subsection to `evals/README.md` covering the four generalizable facts
2. [ ] Add a `## Harness` section (not `### S0:`) to `description-triggers.eval.md` with the invocation, the `Bash` prohibition, and its rationale
3. [ ] Record `claude plugin eval`'s existence and its **deferral** with an explicit ADR-0009 pointer — it exits 1 ("early access"), and adopting it would mean porting 255 scenarios and 1,091 criteria, ~4.6× the diff ADR-0009 already rejected
4. [ ] Do **not** move any `**Context:**` line
5. [ ] Run `python3 scripts/check_eval_mapping.py` and confirm exit 0

**Acceptance Criteria:**
- [ ] WHEN `check_eval_mapping.py` runs after the edit THEN it SHALL exit 0
- [ ] WHEN a cold runner follows the Harness section THEN the invocation SHALL include `--allowed-tools Skill Read Write Edit Glob Grep AskUserQuestion` and exclude `Bash`
- [ ] All 14 `**Context:**` lines remain inside their scenario bodies
- [ ] The section heading is not of the form `### S<n>`

---

#### 3.2 Re-scope all 6 preemption-fragile scenarios and both rubric rows
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #227
**Depends On:** 3.1
**Files Affected:**
- `evals/skills/description-triggers.eval.md` (modify)

**Description:**
The issue scopes this to S4. Verification found **9 scenarios carry a positive-dispatch `Must` naming a specific skill, 6 of them behind creation verbs**: S1 ("model"), S4 ("build"), S5 ("generate"), S6 ("add"), S7 ("build"), S9 ("add"). **S7 is a false green** — its `:119` is structurally identical to S4's failing `:82` and passed only because brainstorming did not fire that run, yet it is cited as *proof the handoff works* in both #227's body and E061.

**The S8 template is the fix shape.** S8 fired brainstorming and passed because it names no skill it must dispatch to (only what must **not** be used), its positive `Must` is a **recognition** assertion satisfiable from stated reasoning, and its behavioral clause is hedged with `optionally` plus a disjunction. S4 already contains its own fix: its recognition `Must` at `:81` **passed** on the live run — only `:82` must change.

Rubric rows `:226` and `:228` restate the same unowned assertion at file level. The linter validates only that `## Rubric` exists as a substring, so a rubric contradicting its own scenarios passes CI silently.

**Tasks:**
1. [ ] Rewrite each of the 6 positive-dispatch `Must` criteria on the S8 pattern: keep recognition assertions as `Must`, demote first-dispatch ordering to `Should` or a harness-logged observation
2. [ ] Keep every `Must NOT` — they are ours and they all passed
3. [ ] Reword rubric rows `:226` and `:228` to match
4. [ ] Add a note that a process skill firing first is an **environment-dependent observation the harness logs**, not a failure — and that the runner must record which competing plugins were installed
5. [ ] Verify at least one literal `**Must:**` or `**Must NOT:**` marker survives in every touched scenario
6. [ ] Run `check_eval_mapping.py`; confirm exit 0

**Acceptance Criteria:**
- [ ] WHEN any scenario in this file is scored THEN no `Must` criterion SHALL assert which skill is dispatched first
- [ ] WHEN `check_eval_mapping.py` runs THEN it SHALL exit 0 (downgrading both `Must` and `Must NOT` in one scenario fails structure validation)
- [ ] Every touched scenario retains ≥1 literal `**Must:**`/`**Must NOT:**` marker
- [ ] Rubric rows no longer assert cross-marketplace dispatch order

**Notes:**
`evals/skills/plan-gate.eval.md` is an unrun second instance with 4 positive-routing `Must` criteria and an `S5: Proactive trigger` colliding head-on with `brainstorming → writing-plans`. **Out of scope here** — file as a follow-up rather than expanding this phase.

---

#### 3.3 File the upstream report against superpowers
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #227
**Depends On:** 3.2
**Files Affected:**
- (none in-repo — external issue)

**Description:**
The user-facing dead-end is only fixable upstream. `brainstorming/SKILL.md:61` makes `writing-plans` the sole permitted successor, so for a request like "build me a workflow diagram", the domain skill is unreachable by any sanctioned route. Report it factually: the mechanism, the observed session, and the blast radius (every domain skill whose realistic trigger phrasing contains a creation verb).

**Tasks:**
1. [ ] Draft the report with the verbatim `:61` quote and the S4 transcript summary
2. [ ] Confirm the destination repo and open the issue
3. [ ] Link it from #227 and close #227

**Acceptance Criteria:**
- [ ] WHEN #227 is closed THEN it SHALL link both the eval re-scope commit and the upstream issue
- [ ] The report makes no claim about this repo's descriptions being at fault

---

### Phase 3 Testing Requirements

- [ ] `check_eval_mapping.py` exits 0 after each item
- [ ] Manual read-through confirming no `Must` asserts cross-marketplace behavior

### Phase 3 Completion Checklist

- [ ] All work items complete
- [ ] Eval linter green
- [ ] #227 and #228 closed with links
- [ ] Follow-up filed for `plan-gate.eval.md`

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Eval structure | `python3 scripts/check_eval_mapping.py` | Exit code 0 |
| Lint | `npx markdownlint-cli2 "evals/**/*.md"` | Exit code 0 |
| No dispatch-order Musts | `awk '/^\*\*Must:\*\*/,/^$/' evals/skills/description-triggers.eval.md \| grep -niE '(routes to\|activates).*(first\|instead)'` | No output |

<!-- END DOD -->

---

## Phase 4: ultra-plan Correctness

**Estimated Complexity:** M (~3 files)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Make every `Phase N` reference name the phase it describes
- Stop gating three behaviors on a taxonomy no file defines

### Work Items

#### 4.1 Repair the phase numbering across all 29 sites, atomically with its eval
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #231
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)
- `evals/skills/ultra-plan.eval.md` (modify)

**Description:**
A single 1–6 → 0–5 renumbering touched the `##` headings and a few body lines but missed the `###` sub-headings and 18 cross-references. Every defect is explained by one transform: **old N → new N−1**.

**8 sub-headings:** `:175`, `:182`, `:189` (`3a/3b/3c` → `2a/2b/2c`); `:327`, `:336`, `:344`, `:360`, `:370` (`6a-6e` → `5a-5e`).

**18 cross-reference lines:** `:116`, `:117`, `:142`, `:167` (two wrong tokens), `:169`, `:196`, `:230`, `:231`, `:234`, `:270`, `:308`, `:313`, `:340`, `:341`, `:346`, `:363`, `:365`, `:382` (only its "Phase 2 output" clause).

**2 anchors that must move in lockstep:** `:384` ("see 6b routing table") and `:385` ("see 6d") — correct today, dangling the moment the headings renumber.

**1 site outside the file:** `evals/skills/ultra-plan.eval.md:43` copied the defect verbatim from `SKILL.md:167`. **Fixing the skill without the eval converts a passing eval into a false failure against a now-correct skill.**

**DO NOT TOUCH `:350`.** "Change sets (Phase 2c)" is *correct* — it is the one reference that survived the renumbering and the diagnostic tell. Renumbering it to `3c` propagates the bug into the only place that escaped it. The whole `:349-356` table is correct in all 8 rows.

**Tasks:**
1. [ ] Apply the 8 sub-heading renumberings
2. [ ] Apply the 18 cross-reference corrections
3. [ ] Update the 2 anchors at `:384`/`:385`
4. [ ] Update `evals/skills/ultra-plan.eval.md:43` in the **same commit**
5. [ ] Leave `:350` and the entire `:349-356` table unchanged
6. [ ] Grep `Phase [0-9]` across the file and read every hit against its containing phase — a partial fix is worse than none

**Acceptance Criteria:**
- [ ] WHEN any `Phase N` reference in `ultra-plan/SKILL.md` is read THEN it SHALL name the phase it describes
- [ ] WHEN a `###` sub-heading is read THEN its leading digit SHALL equal its parent phase number
- [ ] `:350` still reads "Change sets (Phase 2c)"
- [ ] `evals/skills/ultra-plan.eval.md:43` reads "Phase 1 deliverable" and is in the same commit as `SKILL.md:167`
- [ ] No self-contradiction remains: `:363` and `:385` refer to the same artifact by the same phase number

---

#### 4.2 Delete the phantom L0–L4 taxonomy at all 10 sites, including the generator template
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #231
**Depends On:** 4.1
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)
- `plugins/personal-plugin/references/adr-template.md` (modify)

**Description:**
Eight sites in `SKILL.md` (`:89`, `:222`, `:236`, `:238`, `:240`, `:242`, `:244`, `:315`) plus **two in `references/adr-template.md` (`:7`, `:58`)** — the file `SKILL.md:229` instructs the model to load when writing an ADR, so the phantom scale is restated in the shipped template the skill consumes at runtime. A fix scoped to the skill body leaves the mould minting the defect.

`plan-gate` defines Paths A/B/B.5/C/D/D.5/E/F and **no L-levels**; a repo-wide sweep found no definition anywhere. It cannot emit a scope level even in principle — its output is a *Path recommendation*, so "per plan-gate classification" requests a kind of value the cited skill does not produce.

**Delete, don't define** (D62-adjacent reasoning): at `:236`/`:242`/`:244` the L-clause is ANDed onto a trigger question that is already sufficient and answerable — `:226` *"Does this change set involve an architectural decision that should outlive the plan?"* **is** the L3+ test; `:242` *"Are there 2+ fundamentally different architectures…?"* **is** the L4+ test. `:89`(b) should be deleted outright: ultra-plan is reached only as Path D.5, so anything plan-gate would call "L0-L1" routes to Path A or B and never arrives.

**Tasks:**
1. [ ] Delete the L-clause and the "per plan-gate classification" attribution at all 8 `SKILL.md` sites
2. [ ] Retitle `:222` and `:238` to "(conditional)" and let the existing trigger questions gate
3. [ ] Delete `:89`'s condition (b) entirely
4. [ ] Remove both `adr-template.md` L3+ references
5. [ ] Confirm body stays under 500 lines (currently 385, 115 headroom)

**Acceptance Criteria:**
- [ ] WHEN `grep -nE 'L[0-9]' plugins/personal-plugin/skills/ultra-plan/SKILL.md` runs THEN it SHALL return no output
- [ ] WHEN `grep -nE 'L[0-9]\+' plugins/personal-plugin/references/adr-template.md` runs THEN it SHALL return no output
- [ ] WHEN a conditional gate in `ultra-plan` is evaluated THEN it SHALL depend only on a question answerable from text present in the repo
- [ ] `ultra-plan/SKILL.md` remains under 500 lines

---

### Phase 4 Testing Requirements

- [ ] `check_eval_mapping.py` exits 0
- [ ] `claude plugin validate plugins/personal-plugin --strict` exits 0

### Phase 4 Completion Checklist

- [ ] All work items complete
- [ ] `:350` verified unchanged
- [ ] Eval and skill changed in one commit
- [ ] Version bumped (Phase 2's gate will now require it)

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| No L-taxonomy | `grep -rnE 'L[0-9]\+?' plugins/personal-plugin/skills/ultra-plan/SKILL.md plugins/personal-plugin/references/adr-template.md` | No output |
| :350 intact | `grep -c 'Change sets (Phase 2c)' plugins/personal-plugin/skills/ultra-plan/SKILL.md` | Returns `1` |
| Body budget | `wc -l < plugins/personal-plugin/skills/ultra-plan/SKILL.md` | < 500 |
| Validation | `claude plugin validate plugins/personal-plugin --strict` | Exit code 0 |

<!-- END DOD -->

---

## Phase 5: `/unlock` Actually Works

**Estimated Complexity:** S (~3 files)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Fix the total, in-repo `/unlock` failure that #217's filed remedy would not have touched
- Correct the record: D53 and two notebook lines restate a mechanism that is wrong

### Work Items

#### 5.1 Read the token from `BWS_ACCESS_TOKEN`, not the unset `$TROY`
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #217
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)
- `plugins/personal-plugin/skills/new-project/SKILL.md` (modify)
- `plugins/personal-plugin/references/api-key-setup.md` (modify)

**Description:**
`skills/unlock/SKILL.md:50` does `TOKEN="$TROY"` and `:53` hard-stops when empty. **`TROY` is set by nothing on this machine** — verified UNSET, while `BWS_ACCESS_TOKEN` is set (94 chars) and current. So `/unlock` prints "TROY environment variable is not set" and never reaches `bws`, on every invocation.

Second in-repo blocker: `allowed-tools` (`:5`) omits `python3` (`Bash(python:*)` does not prefix-match `python3`), `mktemp`, `chmod`, `rm`, `source`, `test`, and does not cover `:92`'s `BWS_ACCESS_TOKEN="$TOKEN" bws …` form, which is not `bws`-prefixed. Step 3 stalls even once the variable is fixed.

The one genuine probe leak is `references/api-key-setup.md:49` — a bare `bws secret list` used as a diagnostic, which prints every secret's plaintext value. The functional uses at `unlock:70,92` and `new-project:62` capture to a variable and are **not** offenders.

**Tasks:**
1. [ ] Read `${BWS_ACCESS_TOKEN}` as primary, `$TROY` as a deprecated fallback; update the error text and the `$TROY` references at `:17`, `:40`, `:44-45`, `:54-55`, `:140`, `:199-201`
2. [ ] Same rename at `new-project/SKILL.md:62` and `api-key-setup.md:51,53`
3. [ ] Widen `allowed-tools` to cover `python3`, `mktemp`, `chmod`, `rm`, `source`, `test`, and the `VAR=… bws` form
4. [ ] Replace `api-key-setup.md:49`'s bare probe with `bws secret list >/dev/null; echo $?`
5. [ ] Keep `disable-model-invocation: true` — do not relax it

**Acceptance Criteria:**
- [ ] WHEN `/unlock` runs in a tool shell with `BWS_ACCESS_TOKEN` set and `TROY` unset THEN it SHALL load secrets and report names only
- [ ] WHEN any documented helper runs on its success path THEN no secret value SHALL be printed to stdout
- [ ] WHEN Step 3 executes THEN every command it issues SHALL be covered by `allowed-tools`
- [ ] `disable-model-invocation: true` is unchanged
- [ ] `claude plugin validate plugins/personal-plugin --strict` exits 0

**Notes:**
Cannot be verified in CI (ADR-0009/D32, zero secrets). Acceptance is a manual `/unlock` run. **Out of scope, not fixable here:** the nine `~/.claude/scripts/*.sh` (all legacy `bw`/`BW_SESSION`, zero `bws` references), `~/.bashrc:8`'s early return, and the global CLAUDE.md's nonexistent `~/bin/bws.exe`.

---

#### 5.2 Correct D53 and rewrite #217
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #217
**Depends On:** 5.1
**Files Affected:**
- `LAB_NOTEBOOK.md` (modify)

**Description:**
D53 and notebook lines `:645`/`:657` restate claim (a)'s mechanism, which is wrong: `.bashrc:167` guards the *full credential set*, not the token; the operative line is `.bashrc:8`, an early `return` for non-interactive shells that makes the anti-staleness `eval` at `:165` — already present since 2026-07-16, i.e. already #217's proposed fix — unreachable. The E058 stale-token incident was real but transient and host-level; it does not reproduce.

**Tasks:**
1. [ ] Amend D53 with the corrected mechanism, preserving the original text struck through (Rule 4 — never delete a decision)
2. [ ] Correct notebook `:645` and `:657`
3. [ ] Rewrite #217's body to the in-repo scope and close it on merge

**Acceptance Criteria:**
- [ ] WHEN D53 is read THEN it SHALL name `.bashrc:8` as the operative mechanism and mark the `:167` attribution as corrected
- [ ] #217's body no longer names out-of-repo scripts as fix sites

---

### Phase 5 Testing Requirements

- [ ] Manual `/unlock` invocation succeeds in a tool shell
- [ ] `grep -rn 'bws secret list' plugins/` shows no bare diagnostic use

### Phase 5 Completion Checklist

- [ ] All work items complete
- [ ] Manual verification recorded in LAB_NOTEBOOK
- [ ] Version bumped

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| No bare probe | `grep -rn 'bws secret list' plugins/ \| grep -v '>/dev/null' \| grep -v 'TOKEN' ` | No output |
| No stale $TROY | `grep -rn '\$TROY' plugins/ \| grep -v 'deprecated fallback'` | No output |
| Validation | `claude plugin validate plugins/personal-plugin --strict` | Exit code 0 |

<!-- END DOD -->

---

## Phase 6: Inventory Generator

**Estimated Complexity:** M (~10 files, ~80 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Bring `CLAUDE.md`'s inventory under the generator that already keeps README drift-free
- Clear the 6 live sites still teaching deprecated commands

### Work Items

#### 6.1 Generalize `update-readme.py` to a target list and regenerate CLAUDE.md's inventory
**Status: PENDING**
**Model Tier: opus**
**Issue Refs:** #206
**Depends On:** None
**Files Affected:**
- `scripts/update-readme.py` (modify)
- `CLAUDE.md` (modify)

**Description:**
`update-readme.py:329` hard-codes `README.md` as its only target, which is why the CI gate at `validate.yml:318` is green-by-construction on CLAUDE.md drift. README carries the same facts and is provably drift-free; CLAUDE.md is hand-edited and carries **8** defects: 5 missing personal-plugin skills (`archive-project`, `clear-prep`, `fleet-health`, `new-project`, `task-sync`), `build-cfa-deck` missing from slide-gen, and two absent directories (`plugins/personal-plugin/agents/` — ten files — and `plugins/slide-gen/references/`).

`scan_plugin()` needs **zero changes** — it already returns correct counts (23/29/9/2). Generalize `main()` to a `(path, renderer, anchor)` list and add a renderer that regenerates only the name lists inside the fence, leaving hand-written annotation prose alone — the same surgical posture `rewrite_prose_counts()` already takes.

**Do not let the generator touch `CLAUDE.md:180-189`** ("Command Patterns") — a deliberately curated 13-of-23 subset, not machine-derivable.

**Tasks:**
1. [ ] Generalize `main()` from one path to a target list, reusing `scan_plugin()` verbatim
2. [ ] Add the CLAUDE.md renderer with explicit anchors (consider `<!-- BEGIN/END:inventory -->` markers for strictness)
3. [ ] Regenerate the block; add the two missing directories
4. [ ] **Negative-test before wiring:** delete a skill name from the block, run `--check`, confirm **exit 2**; restore and confirm exit 0
5. [ ] Fix `CLAUDE.md:262`'s dangling `IMPLEMENTATION_PLAN.md` pointer (archived this session) and `:266-268`'s Deprecated section, which lists 1 of 5 deprecated commands
6. [ ] Correct `LAB_NOTEBOOK.md:122` — "10 arch-review agents" is 9; the 10th is `sre-operator`, a fleet-ops agent

**Acceptance Criteria:**
- [ ] WHEN a skill directory is added or removed THEN `python3 scripts/update-readme.py --check` SHALL exit 2 until CLAUDE.md is regenerated
- [ ] WHEN `--check` runs on the current tree THEN it SHALL exit 0
- [ ] The negative test's exit-2 observation is recorded, not asserted in prose
- [ ] `CLAUDE.md:180-189` is byte-identical after regeneration
- [ ] Hand-written annotation comments inside the fence survive

**Notes:**
This mechanically edits an always-loaded file. Per the standing rule, the extended `--check` must be negative-tested before it is trusted — this repo has shipped three guards that could not fail, and `update-readme.py --check` was one of them.

---

#### 6.2 Clear the 6 live deprecated-command sites and the two unresolvable-doc items
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #206
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/references/patterns/naming.md` (modify)
- `QUICK-REFERENCE.md` (modify)
- `TROUBLESHOOTING.md` (modify)
- `docs/PLUGIN-DEVELOPMENT.md` (modify)
- `plugins/slide-gen/CHANGELOG.md` (modify)
- `plugins/slide-gen/skills/sg-optimize/SKILL.md` (modify)

**Description:**
The issue names one deprecated-command site; there are **six**. The worst two *actively instruct* readers to use `/new-command`, deprecated by ADR-0006/D21: `TROUBLESHOOTING.md:900` and `docs/PLUGIN-DEVELOPMENT.md:112-115`. Also `naming.md:33` (filed as `:35` — off by two), `QUICK-REFERENCE.md:10`, `docs/PLUGIN-DEVELOPMENT.md:43`, `TROUBLESHOOTING.md:377`.

`plugins/slide-gen/CHANGELOG.md:16` says "All 8 skills" and lists nine — fix **the arithmetic only**, never the names (ADR-0008:9 independently confirms nine).

`sg-optimize/SKILL.md:33` is self-contradictory in a single parenthetical: `(default: overwrites input with _optimized suffix)` — two mutually exclusive behaviors. **The truth is not knowable in-repo**: slide-gen is an external-dependency plugin (ADR-0008/D23), the engine is in a private repo, and `grep -rl "_optimized" --include=*.py .` returns zero hits. **State the uncertainty, do not guess the behavior.**

**Tasks:**
1. [ ] Replace the 4 example/teaching references to deprecated commands with live equivalents
2. [ ] Rewrite `TROUBLESHOOTING.md:900` and `docs/PLUGIN-DEVELOPMENT.md:112-115` to direct readers to `/new-skill` (ADR-0006)
3. [ ] Fix `docs/PLUGIN-DEVELOPMENT.md:43`'s tree (shows `new-command.md` in `commands/`; it is in `deprecated/`) and `:44`'s `skills/help/` (dropped by D42)
4. [ ] Correct `slide-gen/CHANGELOG.md:16` from 8 to 9
5. [ ] Rewrite `sg-optimize/SKILL.md:33` and `:64` to state the uncertainty and point at `sg optimize --help`

**Acceptance Criteria:**
- [ ] WHEN a reader follows any live doc instruction THEN it SHALL name a command that exists and is not deprecated
- [ ] `slide-gen/CHANGELOG.md:16`'s stated count equals the number of names listed
- [ ] WHEN `sg-optimize`'s `--output` documentation is read THEN it SHALL NOT assert a default behavior that is unverifiable from this repo
- [ ] `markdownlint-cli2` exits 0

**Notes:**
Also worth filing separately, not fixed here: `tests/integration/test_validate_plugin.py:191-199` still assert every valid plugin ships `skills/help/SKILL.md` — the ADR-0004 requirement D42 dropped. Retired doctrine encoded as a green test.

---

### Phase 6 Testing Requirements

- [ ] `update-readme.py --check` negative test observed at exit 2
- [ ] `pytest tests/` passes

### Phase 6 Completion Checklist

- [ ] All work items complete
- [ ] Negative-test result recorded
- [ ] Version bumped where `plugins/**` changed

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Inventory sync | `python3 scripts/update-readme.py --check` | Exit code 0 |
| No deprecated refs | `grep -rn 'new-command\|review-pr' --include=*.md . \| grep -v docs/archive \| grep -v CHANGELOG \| grep -v LAB_NOTEBOOK \| grep -v deprecated/` | Only deprecation notices |
| Lint | `npx markdownlint-cli2 "**/*.md"` | Exit code 0 |
| Tests | `pytest tests/ -q` | Exit code 0 |

<!-- END DOD -->

---

## Phase 7: Consent-Gate Consistency

**Estimated Complexity:** M (~8 files)
**Dependencies:** None
**Execution Mode:** Parallel

### Goals

- One interaction model for every gate that is model-invocable and consents to a write
- Fix the templates that mint new instances, not only the instances

### Work Items

#### 7.1 Convert the 4 model-invocable write-consent gates to `AskUserQuestion`
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #223
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/security-analysis/SKILL.md` (modify)
- `plugins/personal-plugin/skills/wiki/SKILL.md` (modify)
- `plugins/personal-plugin/skills/task-sync/SKILL.md` (modify)

**Description:**
Per D64, convert every gate that is **both** model-invocable **and** consents to a write: `security-analysis:19-28`, `wiki:207` and `:241`, `task-sync:247`. `task-sync:247` weighed heaviest — it guards **publishing to a public repo** and is a 3-way choice (`yes / no / show plan again`).

**Frontmatter edit hazard.** `security-analysis/SKILL.md:5`'s `allowed-tools` value is a plain scalar terminated by ` #`, and the trailing comment *contains* `unscoped: ` — a colon-space, inert **only because it sits after the `#`**. A colon-space in an unquoted scalar silently drops the **entire frontmatter** with no crash. Insert `, AskUserQuestion` **before** the two-space + `#`, and do not move the `#`. `claude plugin validate --strict` is the only gate that catches a slip.

`security-analysis`'s yes-branch carries behavior, not decoration: it sets `--dependencies-only` as the default and documents `--quick`/full overrides. A 2-option conversion would drop that — use 3 options ("Yes — dependencies only" / "Yes — full scan" / "No") or retain a follow-on sentence.

D39's unscoped-`Bash` sanction is untouched by appending a tool to the list.

**Tasks:**
1. [ ] Add `AskUserQuestion` to `security-analysis`'s `allowed-tools`, before the ` #`
2. [ ] Convert its gate, preserving the invocation-source condition verbatim (D57's cited house pattern) and the scan-mode payload
3. [ ] Convert `wiki:207` and `:241`; add `AskUserQuestion` to its `allowed-tools` if absent
4. [ ] Convert `task-sync:247` as a 3-option question, preserving the public-repo warning text
5. [ ] Run `claude plugin validate plugins/personal-plugin --strict` after **each** frontmatter edit

**Acceptance Criteria:**
- [ ] WHEN any converted skill loads THEN `claude plugin validate --strict` SHALL report full frontmatter, not empty metadata
- [ ] WHEN `security-analysis`'s gate is confirmed THEN the `--dependencies-only` default SHALL still be conveyed
- [ ] The invocation-source condition ("skip when invoked directly") survives verbatim in all four
- [ ] D39's unscoped `Bash` and its inline justification comment are unchanged

---

#### 7.2 Fix the 3 generator templates and the `ask-questions` residual
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #223, #233
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/references/patterns/output.md` (modify)
- `plugins/personal-plugin/references/templates/generator.md` (modify)
- `plugins/personal-plugin/references/templates/synthesis.md` (modify)
- `plugins/personal-plugin/commands/ask-questions.md` (modify)

**Description:**
Three `references/` templates still mint `Save this file? (y/n):` / `Proceed with synthesis? (y/n):` into every artifact built from them — the propagation shape this backlog keeps hitting.

`commands/ask-questions.md:409-424` still renders the full legacy `[A]/[B]/[C]/[D] Custom/[S] Skip` + `Your choice (A/B/C/D/S):` menu, **contradicting its own file** at `:145` ("Ask with `AskUserQuestion`") and `:175` ("must not be re-added as options"), and mis-serving `finish-document.md:139`'s cross-reference. PR #222 item 7.5 claimed this file among its conversions. **This is the second false green in that phase** — the first is recorded at LAB_NOTEBOOK `:869-878`.

**Do not touch `references/templates/interactive.md:120,226`** — preserved on purpose by plan v12 item 7.5 task 4; its one-at-a-time rule is a deliberate interview contract.

**Tasks:**
1. [ ] Replace the prose prompts in the 3 generator templates with `AskUserQuestion` shapes
2. [ ] Rewrite `ask-questions.md:409-424` to show an `AskUserQuestion` call and response
3. [ ] Leave `interactive.md` untouched
4. [ ] Grep for the **rendered artifact** (`Your choice`, `[D] Custom`, `(y/n)`), not the frontmatter grant, and confirm the remaining hits are the deliberate exemptions

**Acceptance Criteria:**
- [ ] WHEN `grep -rn 'Your choice (A/B/C' plugins/` runs THEN the only hits SHALL be `references/templates/interactive.md`
- [ ] `ask-questions.md`'s example no longer contradicts `:145` and `:175`
- [ ] `finish-document.md:139`'s cross-reference points at a correct example

---

### Phase 7 Testing Requirements

- [ ] `claude plugin validate --strict` after every frontmatter edit
- [ ] Rendered-artifact grep confirms only deliberate exemptions remain

### Phase 7 Completion Checklist

- [ ] All work items complete
- [ ] Frontmatter intact on all edited skills
- [ ] Version bumped

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Frontmatter | `claude plugin validate plugins/personal-plugin --strict` | Exit code 0 |
| No stray menus | `grep -rn 'Your choice (A/B/C' plugins/ \| grep -v interactive.md` | No output |
| Injections | `python3 scripts/check_injections.py` | Exit code 0 |

<!-- END DOD -->

---

## Phase 8: Freshness Stamps and task-sync

**Estimated Complexity:** M (~13 files, ~150 LOC)
**Dependencies:** None
**Execution Mode:** Parallel

### Goals

- Delete every stamp that asserts a verification nobody performed (D62)
- Make the four `tasks.json` sources agree, with one logged decision (D65)
- Close the call-sequence coverage gap that let `bug_001` ship at 96%

### Work Items

#### 8.1 Delete all 12 freshness stamps, the phantom `check-models` reference, and both generators
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #218
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/references/research-models.md` (modify)
- `plugins/personal-plugin/references/flag-consistency.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)
- `plugins/personal-plugin/skills/accessibility-annotator/SKILL.md` (modify)
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)
- `plugins/personal-plugin/skills/spark-recon/SKILL.md` (modify)
- `plugins/personal-plugin/skills/explain-project/SKILL.md` (modify)
- `plugins/personal-plugin/skills/create-wiki/SKILL.md` (modify)
- `plugins/slide-gen/skills/build-cfa-deck/SKILL.md` (modify)
- `docs/PLUGIN-DEVELOPMENT.md` (modify)

**Description:**
Per D62. The issue names one file; there are **12 live sites**, and two of them are **generators** — `explain-project/SKILL.md:392` prescribes *"**Last verified:** date when claims were last checked"* into every document it produces, and `create-wiki/SKILL.md:271` templates `Last updated: … | Last lint: never`.

Beyond the column: `research-models.md:41`'s Resolution Order names **`check-models`, a command that does not exist** (deliberately deleted per archived plan v6, reference never removed), and `:70-80` documents the output of that phantom. `:29` claims "All defaults are annotated with their last-verified date" while `:37` says OpenAI and Google IDs "cannot be verified offline" — and `:34-35` carry stamps anyway.

`unlock/SKILL.md:16,67,90` is the same constant duplicated three times, so any edit must land in all three or the file self-contradicts. **Coordinate with Phase 5**, which also edits this file.

**Tasks:**
1. [ ] Delete the `Last Verified` column and its note from `research-models.md:31-37`
2. [ ] Delete the `check-models` reference at `:41` and the phantom `## Model Check Output Examples` at `:70-80`
3. [ ] Delete the "default as of …" hedges at the 9 remaining sites
4. [ ] Remove the templated stamp from both generators
5. [ ] Where a value genuinely needs a caveat, state the *uncertainty* ("verify with the provider if errors occur") without a date that implies someone checked

**Acceptance Criteria:**
- [ ] WHEN `grep -rn 'Last Verified\|last verified\|default as of\|Default as of' plugins/ docs/` runs THEN it SHALL return no output
- [ ] WHEN `grep -rn 'check-models' .` runs (excluding `docs/archive/`) THEN it SHALL return no output
- [ ] WHEN a generator produces a document THEN that document SHALL NOT contain a freshness stamp field
- [ ] No remaining claim asserts a verification event that no mechanism performs

---

#### 8.2 Bless `tasks.json` local-only and reconcile all four sources
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #230
**Depends On:** None
**Files Affected:**
- `docs/plans/2026-07-18-task-sync-design.md` (modify)
- `LAB_NOTEBOOK.md` (modify)
- `plugins/personal-plugin/skills/task-sync/SKILL.md` (modify)

**Description:**
Per D65. `.gitignore` keeps ignoring `tasks.json`; the *documentation* changes to match, and the decision is logged with alternatives — the absence of that log entry is the actual defect this issue records.

Six design-doc lines assert the opposite: `:19`, `:64`, `:65` (correct — `TASKS.md` only), `:100`, `:129`, `:153`. `references/config-reference.md:61-70` already reconciles toward local-only and needs no change — it is the source that was right.

**Tasks:**
1. [ ] Correct design-doc lines `:19`, `:64`, `:100`, `:129`, `:153` to describe local-only, with a pointer to the superseding decision
2. [ ] Mark D34's "committed" clause SUPERSEDED by D65 in the Decision Log; never delete it (Rule 4)
3. [ ] Add a short note to `task-sync/SKILL.md` stating that cross-machine sync of local state is out of scope and the tracker is the archive of record
4. [ ] Re-scope #169 to record that there is no cross-machine sync of the *public* list either
5. [ ] Note in the skill that `tasks.json` is **not git-recoverable**, so a destructive command has no undo

**Acceptance Criteria:**
- [ ] WHEN any of the four sources is read THEN it SHALL describe `tasks.json` as local-only
- [ ] D34's original text survives, marked SUPERSEDED with a pointer to D65
- [ ] `.gitignore` is unchanged
- [ ] #169's body reflects the corrected scope

---

#### 8.3 CLI-level integration test for `sync --apply --decisions` across every accepted shape
**Status: PENDING**
**Model Tier: sonnet**
**Issue Refs:** #224
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/tests/test_plan_apply.py` (modify)
- `plugins/personal-plugin/skills/task-sync/references/sync-semantics.md` (modify)

**Description:**
`bug_001` shipped at 96% line coverage because the defect lived entirely in the *interaction between two call sites*, and no unit test of either could see it. **The coverage report already names the gap:** `__main__.py` sits at 95% with Missing `281-283, 288` — and line 288 *is* the `_split_flat_decisions` call, so the function written to fix `bug_001` **has never executed through the CLI**.

The two call sites are `__main__.py:273` (`_load_decisions(args.decisions)`) and `:280` (same path, `key="orphan_decisions"`), with the flat-detection heuristic at `:284` and the split at `:288`.

**Corrections to the issue as filed:** there is **no `cli.py`** — the file is `__main__.py`, and the seam is `run_sync(args, provider=None)` at `:238` (`main(argv)` dispatches `func(args)` with one argument and cannot inject a provider). And "three documented shapes" is **wrong**: `sync-semantics.md:146-147` documents **two**. The third — wrapped conflicts-only, *the shape that actually caused the outage* — exists only in the loader docstring and is **absent from the user-facing reference**. That documentation gap is fixed here too.

The real accepted set is **five** in-set inputs: absent path → `{}`; wrapped both keys; wrapped `decisions` only; wrapped `orphan_decisions` only; flat mapping. Out-of-set values that must raise `ValueError` at `:161-162`: bare list, JSON `null`, scalar, `{"decisions": null}` — plus missing-file and malformed-JSON paths.

**Parametrize from `_DECISION_SECTIONS` (`__main__.py:100`), never from a hardcoded copy** — that is the exact `VALID_PRIORITIES` drift that produced #208/E056 — and always include an out-of-set value, since bugs of this class live in the unrecognized-value branch.

**Why the existing mock is safe here (E057 does not apply):** `conftest.py:19`'s `MockProvider` is structurally verified against the real `Provider` protocol by `test_mock_provider_satisfies_protocol`, so it cannot invent an interface. Assert against **observable real state** — `tasks.json` on disk after apply, and exit code + stderr for the fail-loud orphan path — not the mock's shape.

**Tasks:**
1. [ ] Add CLI-level tests driving `run_sync(--apply)` with a real `--decisions` file in each of the five in-set shapes
2. [ ] Add out-of-set cases asserting exit 1, the path named in stderr, and **nothing written**
3. [ ] Add the degenerate case where a wrapped file's two sections are byte-identical — the `:284` value-equality heuristic misroutes it into `_split_flat_decisions`
4. [ ] Parametrize from `_DECISION_SECTIONS`
5. [ ] Document the third (wrapped conflicts-only) shape in `sync-semantics.md:146-160` and correct "two formats" to three
6. [ ] Confirm `__main__.py` lines `281-283` and `288` are covered

**Acceptance Criteria:**
- [ ] WHEN `run_sync(--apply)` is driven with each documented decisions-file shape THEN the correct task ids SHALL reach the conflict and orphan consumers respectively
- [ ] WHEN driven with an out-of-set decisions file THEN it SHALL exit non-zero naming the file and SHALL leave `tasks.json` byte-identical
- [ ] `__main__.py` coverage no longer reports `281-283, 288` as missing
- [ ] `sync-semantics.md` documents all three shapes and no longer says "two formats"
- [ ] task-sync branch coverage ≥ the current 96.30% and above the `fail_under = 90` floor

**Notes:**
D36's fail-loud orphan validation must be preserved exactly — unrecognized ids route to the *orphan* map on purpose, because that is the only fail-loud consumer, and silently dropping one would convert a user's typo into a decision they believe they made.

---

### Phase 8 Testing Requirements

- [ ] `claude plugin validate --strict` for all three plugins
- [ ] Grep sweeps for stamps and `check-models` return empty
- [ ] task-sync suite green with coverage ≥96.30% and `281-283, 288` covered

### Phase 8 Completion Checklist

- [ ] All work items complete
- [ ] Phase 5's `unlock` edits reconciled with 8.1's
- [ ] Version bumped
- [ ] All 13 issues closed

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| No stamps | `grep -rniE '(last verified\|default as of)' plugins/ docs/ --include=*.md \| grep -v archive` | No output |
| No phantom cmd | `grep -rn 'check-models' plugins/ docs/ \| grep -v archive` | No output |
| Validation | `for p in personal-plugin bpmn-plugin slide-gen; do claude plugin validate plugins/$p --strict; done` | All exit 0 |
| Lint | `npx markdownlint-cli2 "**/*.md"` | Exit code 0 |

<!-- END DOD -->

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 3 | Phases 4, 5, 6, 7, 8 | Only file is `evals/skills/description-triggers.eval.md` + `evals/README.md` |
| Phase 4 | Phases 3, 5, 6, 7 | Touches `ultra-plan/SKILL.md`, its eval, `adr-template.md` — no overlap |
| Phase 5 | Phases 3, 4, 6, 7 | **Conflicts with Phase 8.1** on `unlock/SKILL.md` — see Risk table |
| Phase 6 | Phases 3, 4, 5, 7 | `CLAUDE.md`, `update-readme.py`, docs |
| Phase 7 | Phases 3, 4, 5, 6 | `security-analysis`, `wiki`, `task-sync` skills + 3 templates |
| Phase 8.2 | All | Design docs + notebook only |
| Phase 8.3 | All | Python tests + one reference file; no overlap with 8.1/8.2 |
| 3.1 → 3.2 | Sequential | Same file; 3.2 must apply after 3.1's section exists |
| 4.1 → 4.2 | Sequential | Same file |
| 2.1 → 2.2 → 2.3 → 2.4 | Strictly sequential | Each gates the next; 2.3 must observe failure before 2.4 wires it |

**Critical path:** Phase 1 → Phase 2. Everything else is independent.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy | Status |
|------|------------|--------|---------------------|--------|
| Phase 2's gate reddens the required `Validate Plugins (official CLI)` check on `main`'s push leg | Med | **High** — a red required context on main | Explicit event-leg branch (2.2 task 4) with the push leg exiting 0; 2.3's negative test must assert the **PR leg still fails**, not merely that push passes | Open |
| Phase 2's gate blocks Phase 1's own CHANGELOG-only PR | High if mis-ordered | Med | Phase 1 lands first; `CHANGELOG.md` is explicitly exempt from Rule 1 | Open |
| The gate no-ops on both legs — "unchecked" becomes a false "checked" (E043) | Med | **High** | `--self-test` asserts exit 1 per violation; 2.3 observes four real exit codes on a scratch branch and records them | Open |
| Phase 4 fixes `SKILL.md` without `ultra-plan.eval.md:43`, turning a passing eval into a false failure | Med | Med | Both files in one commit (4.1 task 4); DoD greps for the eval line | Open |
| `:350` "corrected" to `3c`, propagating the bug into the one surviving-correct reference | Med | Med | Explicit do-not-touch in 4.1; DoD asserts the string still present | Open |
| Frontmatter silently dropped by a colon-space when editing `security-analysis:5` | Low | **High** — a D40-class skill loads unprotected | Insert before the ` #`; run `validate --strict` after each frontmatter edit (7.1 task 5) | Open |
| Phase 5 and Phase 8.1 both edit `unlock/SKILL.md` | High if parallel | Med | Serialize: run 8.1's `unlock` edits after Phase 5 merges, or fold them into Phase 5 | Open |
| Phase 6's generator mangles hand-written annotation prose in an always-loaded file | Med | Med | Regenerate name lists only; `CLAUDE.md:180-189` byte-identical assertion in DoD; negative-test at exit 2 first | Open |
| Backfilled CHANGELOG entries paraphrased rather than extracted, reintroducing drift inverted | Med | Low | 1.1 task 1 mandates extraction; acceptance compares version *sets*, not prose | Open |

---

## Unknowns Register

| ID | Unknown | Severity | Affects | Resolution Strategy | Status |
|----|---------|----------|---------|---------------------|--------|
| U1 | Does `fetch-depth: 0` measurably slow the `plugin-validate` job past its 10-minute timeout? | Low | Phase 2, 2.1 | Measure the first CI run; repo history is small so this is expected to be negligible | Open |
| U2 | On the `pull_request` leg, is `github.event.pull_request.base.sha` reliably present, or must the base be derived via `merge-base`? | Med | Phase 2, 2.2 | Resolve during 2.3's negative test on a real PR before wiring | Open |
| U3 | Does `wiki/SKILL.md` already grant `AskUserQuestion`? | Low | Phase 7, 7.1 | Read the frontmatter at implementation time | Open |
| U4 | Is the upstream destination for #227's report the `superpowers` plugin repo or its marketplace repo? | Low | Phase 3, 3.3 | Check the plugin manifest's `homepage`/`repository` before filing | Open |
| U5 | Will `claude plugin eval` leave early access during this plan's life, changing #228's deferral calculus? | Low | Phase 3, 3.1 | Record the deferral with a dated pointer to ADR-0009; revisit only if the command becomes invocable | Accepted |
| U6 | Does the stale-skill-loader behavior (#232) affect which version of an edited skill a verification run actually exercises? | **High** | All phases' manual verification | **Before trusting any manual acceptance test, verify the cache content, not its version string.** Tracked separately as #232; do not gate this plan on it | Open |

---

## Success Metrics

- [ ] All 8 phases completed
- [ ] All acceptance criteria met
- [ ] 12 issues closed: #206, #210, #217, #218, #223, #224, #226, #227, #228, #230, #231, #233 (#232 deferred — characterize before fixing; root cause is upstream)
- [ ] `main` is never red: every required check green on both OSes at each phase boundary
- [ ] Two new guards (`check_version_bump.py`, the extended `update-readme.py --check`) each demonstrated to **fail** on deliberately-bad input before being wired in
- [ ] Every generator that mints a defect is fixed alongside its instances — 2 document templates (#218), 3 interaction templates (#223), 1 inventory generator (#206), 1 ADR template (#231)
- [ ] No issue closed on narrative verification: every acceptance criterion is a command with an observed exit code

<!-- END TABLES -->
