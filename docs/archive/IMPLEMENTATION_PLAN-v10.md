# Implementation Plan

**Generated:** 2026-07-17
**Completed:** 2026-07-17
**Based On:** `/prime` health assessment 2026-07-17 → GitHub issues #149–#154 (the canonical backlog), refined by a `/ultra-plan` investigation that overturned 4 of the 6 issues as filed. Prior plan (arch-review remediation, COMPLETE) archived at `docs/archive/IMPLEMENTATION_PLAN-v9.md`.
**Total Phases:** 7
**Estimated Total Effort:** ~900 LOC across ~35 files (script repair, CI config, tool config, 45 eval specs touched lightly, notebook rotation, 1 ADR)

---

## Executive Summary

This plan discharges the six-issue backlog filed from the 2026-07-17 prime run. The investigation's central finding is that the six issues are **not six independent defects** — five of them are symptoms of one root cause: the repo has excellent _artifacts_ of verification discipline (a README-sync script, a pre-commit hook, coverage floors, an eval corpus) that are **not mechanically enforced**. Every drift and staleness finding traces back to that gap. The plan therefore sequences by _wiring the guards_, not by patching the symptoms one at a time.

Investigation overturned four of the six issues as they were filed, and each correction changes the work:

1. **#149(b) is a repair, not an extension.** `scripts/update-readme.py` is _structurally dead_ — verified by running it: it finds 0 skills (its glob misses nested `SKILL.md`) and cannot locate the commands table (its anchor predates the count-prefixed headers), so `--check` exits 0 for _any_ drift. Wiring it into CI before repairing it would ship a green no-op gate — false assurance, strictly worse than nothing. This forces a hard repair→wire ordering inside Phase 2.
2. **#153 is a byproduct of #149, not a standalone typo.** Three README counts are stale (41/70/108) and five skills are entirely absent from the tables. The #149(b) repair regenerates those tables; #153 closes as a consequence. Hand-fixing line 41 would be overwritten and still leave five skills invisible.
3. **#151 has three contradicting sources, not two,** and does NOT depend on #149 (a mis-filing). `claude plugin validate --strict` — which passes with `name:` present in all 39 skills — is the authoritative tiebreaker: the pre-commit hook is correct, `validate.yml` is the bug. The fix branches the rule by path and must never strip `name:`.
4. **#150 overturns a documented design decision.** `evals/README.md:87` states evals are human-run behavioral contracts, _not_ automated tests. Making them CI-executable is an architecture change, so it is split: a deterministic **structural** linter ships now (this plan), and the LLM-judge behavioral runner is deferred to **ADR-0009** as an explicit go/no-go — a decision about whether CI should hold its first secret.

A fifth finding is a latent data-integrity bug that blocks the notebook rotation: the Decision Log jumps **D13 → D19**. Decisions **D14–D18 exist only inside entry bodies** and were never promoted to the table (a Rule 7 lapse from May 2026). ADR-0005 (Accepted) cites D14; CLAUDE.md's top operational rule rests on D17. Rotating the notebook without first promoting these five decisions would silently delete them and orphan an Accepted ADR's cited precedent — violating the very Rule 4 that issue #154 invokes. The promotion is therefore a standalone Phase 1, independently valuable even if rotation never happens.

All changes propagate to installs via `autoUpdate` from `origin/main` (D19), so **no plugin version bump is required** — these are correctness and enforcement changes, not feature releases.

---

## Plan Overview

The critical path is **Phase 2 → Phase 3** (repair the README guard before wiring it; the frontmatter reconcile is independent but shares the enforcement theme) with everything else parallelizable after. Phase 1 (D14–D18 promotion) leads because it is a correctness fix to the permanent record, is cheap, and is the hard prerequisite for Phase 7 (rotation). Phase 7 trails because it is the largest single diff, touches the most external cross-references, and is the lowest-urgency item — and it is only safe once Phase 1 has landed.

Findings sharing a root cause are single work items or co-located in one phase: README drift (#149a/b + #153) → Phase 2; frontmatter contradiction across three files (#151 + CONTRIBUTING.md) → Phase 3; local-gate reproduction + stale mypy prose (#149c + #152, both in `test.yml`) → Phase 4.

Two items are explicitly scoped OUT to their own follow-up issues (filed with this plan): the `feedback-docx-generator` mypy-gate asymmetry (a real two-sided decision, not a docs fix), and a `rotate` operation for the `lab-notebook` skill (without which #154 re-files itself in ~40 entries).

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|------------|------------------|-----------------|--------------|----------------|
| 1 | Notebook data integrity | Promote D14–D18 into the Decision Log (refs E005/E006) | S (~1 file, ~10 lines) | None | Sequential |
| 2 | Repair the README guard | Fix `update-readme.py` (dead glob + dead anchor + prose counts), migrate hand-edited rows to frontmatter, wire `--check` as a step in `plugin-validate` | M (~8 files, ~180 LOC) | None | Sequential (repair→wire) |
| 3 | Reconcile the frontmatter rule | Path-branch `validate.yml` (commands forbid / skills require `name`), recurse into `SKILL.md`, align CONTRIBUTING.md | S (~2 files, ~40 LOC) | None | Sequential |
| 4 | Reproduce gates locally | Coverage floors → `[tool.coverage.report]` (+`branch=true` for feedback-docx), drop CI-line floors, guard `python-compat`, rewrite stale mypy comments | M (~6 files, ~60 LOC) | None | Sequential |
| 5 | Install the hook | Install `pre-commit`, remove the dead `help.md` sync check, document verifiable installation | S (~3 files, ~30 LOC) | Phase 3 | Sequential |
| 6 | Eval structural linter + ADR | Extend `check_eval_mapping.py` (structure + coverage gap + `command:` validation + normalization), ADR-0009 defers the runner | M (~8 files, ~150 LOC) | None | Sequential |
| 7 | Rotate the notebook | Archive E001–E016 (banner + back-pointer), cut @line 830, re-point 7 external referrers | M (~6 files, ~700 lines moved) | Phase 1 | Sequential |

### Execution Hints

| Phase | Model Tier | Context Budget | Notes |
|-------|------------|----------------|-------|
| All (default) | `sonnet` | Standard | Override per-phase below |
| 2 | `sonnet` | Extended | The `update-readme.py` prose-count rewrite must be surgically scoped to the count sentence; regeneration must not clobber hand-edited rows (mitigated by task 2.1) |
| 6 | `sonnet` | Extended | Normalizing 45 heterogeneous eval specs is fiddly; the structural grammar must tolerate real variance (`**Context:**` vs `**Invocation:**`, `Must NOT` before `Must`) |
| 7 | `opus` | Extended | Judgment-heavy: choosing exactly what moves, preserving every decision, re-pointing cross-references without breaking them |

### Milestones

- **M1 (Phase 1):** Decision Log is complete D1–D31, no gaps. ADR-0005's cited precedent is restored. Independently shippable.
- **M2 (Phases 2–3):** The README can no longer drift silently, and the two frontmatter validators agree. The root cause is closed.
- **M3 (Phases 4–6):** Local dev reproduces the CI gates; contributors get the hook automatically; eval structure is enforced and the coverage gap is closed.
- **M4 (Phase 7):** The mandatory first-read notebook is ~43% smaller with zero decision loss.

---

## Constraints (Pre-Plan Gates — from Phase 0)

Every work item below was checked against these. No item violates one; two items are explicitly shaped by them (3.x preserves the house `name`-for-skills rule; 7.x keeps the Decision Log canonical in the main file).

| Constraint | Applies to |
|-----------|-----------|
| Skills require `name:` (house convention, ADR-0006); commands forbid it | Phase 3, Phase 5 |
| 14 required CI checks; adding a _step_ to an existing job keeps the check name (no branch-protection rename) | Phases 2, 4, 6 |
| `python3` only on this VM; `validate.yml` is ubuntu-only (bare `python3` safe there) | Phases 2, 6 |
| Coverage floors are gating (90/85/95, branch coverage); mypy hard-zero | Phase 4 |
| markdownlint globs `**/*.md` with no `docs/archive/` ignore | Phases 1, 6, 7 |
| Rule 4 (never delete decisions) / Rule 6 (continue from notebook alone) / Rule 7 (dashboard current) | Phases 1, 7 |
| `autoUpdate` propagates content — no version bump | All |

---

## Phase 1: Notebook Data Integrity — Promote D14–D18

**Estimated Complexity:** S (~1 file, ~10 lines)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Restore the Decision Log to a complete, gapless D1–D31 record before anything archives the entries that currently hold D14–D18.
- Fix the Rule 7 lapse independently of whether rotation (Phase 7) ever happens.

### Work Items

#### 1.1 Promote D14–D18 into the Decision Log table ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #154 (prerequisite)
**Files Affected:**
- `LAB_NOTEBOOK.md` (modify — Decision Log table only)

**Description:**
The Decision Log jumps from D13 (line 25) to D19 (line 29). D14–D18 were recorded only in entry bodies (E005 lines 341–343: D14 agent naming, D15 escalation cap, D16 orchestrator advisory; E006 lines 392/394: D17 origin/main-is-truth, D18 surgical cherry-pick) and never promoted. Add five table rows between D13 and D19, drawn verbatim from those entry bodies, each with Status ACTIVE (or SUPERSEDED where a later decision revisits it — verify D17 against D19's "second occurrence" language), Date, Entry (E005/E006), and Alternatives.

**Tasks:**
1. [ ] Extract D14–D18 statements + alternatives from E005 (L341–343) and E006 (L392/394).
2. [ ] Insert five rows in D-number order between D13 and D19; keep the table's column format exactly.
3. [ ] Cross-check: does any later decision supersede one of these? (D19 references D17's root cause — mark the relationship, do not mark D17 superseded unless a decision actually replaces it.)
4. [ ] markdownlint the file.

**Acceptance Criteria:**
- [ ] WHEN the Decision Log is read top-to-bottom THEN it SHALL contain D1 through D31 with no missing numbers.
- [ ] WHEN ADR-0005's "per D14 (Lab Notebook E005)" reference is followed THEN D14 SHALL be present in the Decision Log table, not only in an entry body.
- [ ] WHEN markdownlint runs THEN it SHALL exit 0.

**Notes:** Worth doing on its own merits even if #154 is dropped — it is a correctness fix to the permanent record. Ship as its own PR so it can stand alone.

### Phase 1 Testing Requirements

- [ ] `grep '^| D' LAB_NOTEBOOK.md` shows a contiguous D1–D31 sequence.
- [ ] markdownlint clean.

### Phase 1 Completion Checklist

- [ ] D14–D18 present in the table with alternatives and entry refs.
- [ ] No decision text altered — promotion is verbatim, not a rewrite.
- [ ] Living-section dashboard still accurate (Rule 7).

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Decision Log complete | `grep -oP '^\| D\K[0-9]+' LAB_NOTEBOOK.md \| sort -n \| uniq \| tr '\n' ' '` | Contiguous 1..31, no gap at 14–18 |
| Markdown lint | `npx markdownlint-cli 'LAB_NOTEBOOK.md'` | Exit 0 |

<!-- END DOD -->

---

## Phase 2: Repair the README Guard (#149a/b + #153)

**Estimated Complexity:** M (~8 files, ~180 LOC)
**Dependencies:** None
**Execution Mode:** Sequential (repair MUST precede wire)

### Goals

- Make `update-readme.py --check` actually detect drift (today it is dead in two independent places).
- Close #153 as a byproduct of a working regenerator, without destroying hand-edited content.
- Wire the working guard into CI as a step in an existing required job (no new check name).

### Work Items

#### 2.1 Migrate hand-edited README rows into frontmatter ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #149(b) prerequisite
**Files Affected:**
- 5 skill/command source files whose README rows carry flag docs absent from frontmatter (the "(supports `--focus`)"/"(supports `--json`)" rows at `README.md:50,57,60,64,67`)

**Description:**
`README.md` rows 50/57/60/64/67 contain flag documentation that exists in _no_ frontmatter `description`. `generate_table` rebuilds rows from frontmatter, so regenerating (2.2) would silently delete this. Move the flag info into the source `description` (respecting the ≤1024-char budget) first, so regeneration is content-preserving.

**Tasks:**
1. [x] Diff each README row's text against its source `description`; identify every row with extra info.
2. [x] Fold the extra info into the frontmatter `description`, or drop it if redundant with `argument-hint`.
3. [x] Confirm no row loses information after the move.

**Acceptance Criteria:**
- [x] WHEN 2.2 regenerates the tables THEN no currently-documented flag/behavior note SHALL disappear from the README.

**Notes:** Do this BEFORE 2.2. This is the single silent-data-loss risk in the phase. A systematic diff of every command/skill row against its frontmatter (not just the 5 originally-flagged lines) found only 3 genuine losses — `consolidate-documents` (`--json`), `validate-plugin` (`--check-updates`), and `lab-notebook` (scientific-notebook/ADR/postmortem framing, absent from frontmatter entirely) — folded into their `description` fields. `assess-document`, `clean-repo`, `new-skill`, `review-arch`, and `develop-image-prompt` were dropped per the argument-hint escape valve: each flag is already documented in that file's `argument-hint`.

#### 2.2 Repair `update-readme.py` (dead glob, dead anchor, prose counts) ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #149(b), #153
**Files Affected:**
- `scripts/update-readme.py` (modify)
- `README.md` (regenerated: tables + counts at lines 41, 70, 108, 124)

**Description:**
Three defects: (a) `skills_dir.glob('*.md')` (~line 141) misses nested `skills/<name>/SKILL.md` → 0 skills; fix to `glob('*/SKILL.md')`. (b) The commands-table anchor `r'(\*\*Commands:\*\*\n)...'` (~line 213) no longer matches the count-prefixed `**23 Commands:**` header; relax to tolerate the optional `N ` prefix, and likewise for Skills. (c) The prose counts at `README.md:41` ("24 skills"), `:70` ("24 Skills"), `:108` ("8 Skills") are hand-typed literals no code computes; add a prose-count pass that rewrites the "`N commands and M skills`" sentence and the "`**M Skills:**`"/"`**N Commands:**`" headers from the scanned counts. Scope the prose rewrite surgically to the count tokens — do not reflow surrounding text.

**Tasks:**
1. [x] Fix the skills glob to `glob('*/SKILL.md')` (NOT `rglob` — it catches 15 frontmatter-less reference `.md` files).
2. [x] Relax both table anchors to tolerate the optional count prefix.
3. [x] Add prose-count computation + surgical rewrite for the sentence and the `**N Skills:**`/`**N Commands:**` headers across all three plugin sections.
4. [x] Remove the unused `import os` (line 26) if ruff would later flag it.
5. [x] Run `python3 scripts/update-readme.py`; verify the 5 missing skills appear and counts read 28/9.
6. [x] Preserve the exit-code contract: 0 = up to date, 2 = drift (with `--check`), 1 = error.

**Acceptance Criteria:**
- [x] WHEN `python3 scripts/update-readme.py --check` runs against a drifted README THEN it SHALL exit 2 (currently unreachable).
- [x] WHEN the tables are regenerated THEN personal-plugin SHALL show 28 skills, slide-gen 9, and all 62 surfaces SHALL appear.
- [x] WHEN `README.md:41` is read THEN it SHALL say "23 commands and 28 skills".

**Depends On:** 2.1
**Notes:** The two structural breaks were verified by running the script; this is a repair of never-working code, not a tweak. Also fixed a corollary bug the dead glob was masking: skill `CommandEntry.name` was derived from `md_file.stem` (always `"SKILL"` for nested files) — now uses `md_file.parent.name`. Verified: clean tree exits 0, a deliberate count edit exits 2, restoring returns to exit 0, markdownlint clean.

#### 2.3 Wire `--check` into CI as a step in `plugin-validate` ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #149(a)
**Files Affected:**
- `.github/workflows/validate.yml` (modify — add a step to the existing `plugin-validate` job)

**Description:**
Add `python3 scripts/update-readme.py --check` as a step in the `Validate Plugins (official CLI)` job, next to `check_eval_mapping.py` (both stdlib-only, no setup-python, ubuntu-only). Adding a _step_ to an existing job does NOT change any of the 14 required check names — avoiding the branch-protection rename deadlock (PLAT-012/D28).

**Tasks:**
1. [ ] Add the `--check` step after `check_eval_mapping.py` in the `plugin-validate` job.
2. [ ] Confirm the job still reports under its existing check name.
3. [ ] Push a throwaway drift to confirm the step goes red, then revert.

**Acceptance Criteria:**
- [ ] WHEN a PR drifts the README counts/tables THEN the `Validate Plugins (official CLI)` check SHALL fail.
- [ ] WHEN branch protection is inspected THEN the required-check name set SHALL be unchanged (still 14).

**Depends On:** 2.2
**Notes:** MUST come after 2.2 — wiring a dead script yields a green no-op gate.

### Phase 2 Testing Requirements

- [ ] `python3 scripts/update-readme.py --check` exits 0 on a clean tree, 2 after a deliberate count edit.
- [ ] README shows all 62 surfaces; no hand-edited flag note lost (diff vs pre-change).
- [ ] markdownlint clean on README.

### Phase 2 Completion Checklist

- [ ] Script repaired and verified drift-detecting.
- [ ] #153 counts corrected as a byproduct; 5 missing skills now listed.
- [ ] `--check` wired without a new required-check name.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Guard detects drift | `python3 scripts/update-readme.py --check; echo $?` | 0 on clean tree; 2 after a test count edit |
| Counts correct | `grep -c '23 commands and 28 skills' README.md` | ≥1 |
| All surfaces listed | `for s in archive-project clear-prep fleet-health new-project build-cfa-deck; do grep -q "$s" README.md \|\| echo MISSING $s; done` | no output |
| Markdown lint | `npx markdownlint-cli 'README.md'` | Exit 0 |

<!-- END DOD -->

---

## Phase 3: Reconcile the Frontmatter Rule (#151)

**Estimated Complexity:** S (~2 files, ~40 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Make all validators agree that commands forbid `name:` and skills require it.
- Activate the currently-dead skills-frontmatter validation in CI without breaking all 39 skills.

### Work Items

#### 3.1 Path-branch the `validate.yml` frontmatter check + recurse into SKILL.md ✅ Completed 2026-07-17
**Status:** COMPLETE [2026-07-17]
**Model Tier: sonnet**
**Recommendation Ref:** #151
**Files Affected:**
- `.github/workflows/validate.yml` (modify — the inline frontmatter-check step, ~lines 82–145)

**Description:**
The check globs `['commands','skills']` with one rule that treats `name` as forbidden, dormant only because `cmd_dir.glob('*.md')` is non-recursive and never sees `skills/<name>/SKILL.md`. Branch the rule by artifact type: for `commands/*.md`, `name` forbidden (unchanged); for `skills/*/SKILL.md`, `name` REQUIRED and must match the directory name. Use `glob('*/SKILL.md')` — NOT `rglob('*.md')`, which catches 15 frontmatter-less reference files and produces 15 false errors.

**Tasks:**
1. [ ] Split the loop: command files vs `skills/*/SKILL.md`.
2. [ ] Command branch: assert `name` absent (unchanged).
3. [ ] Skill branch: assert `name` present AND equal to the parent directory name.
4. [ ] Verify against all 39 skills (should pass) and against `tests/fixtures/invalid-plugin/commands/forbidden-name-field.md` (should still fail).

**Acceptance Criteria:**
- [ ] WHEN a `skills/<n>/SKILL.md` omits `name` THEN CI SHALL fail.
- [ ] WHEN a `commands/*.md` includes `name` THEN CI SHALL fail (the negative fixture still trips).
- [ ] WHEN all 39 current skills are validated THEN CI SHALL pass (no regression).
- [ ] WHEN non-SKILL reference `.md` files under `skills/*/` are scanned THEN they SHALL NOT be treated as skills.

**Notes:** `claude plugin validate --strict` passing with `name:` present is the authoritative tiebreaker. NEVER resolve this by stripping `name:` from skills.

#### 3.2 Align the third voice in CONTRIBUTING.md ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #151
**Files Affected:**
- `CONTRIBUTING.md` (modify — line ~707)

**Description:**
`CONTRIBUTING.md:707` states "No forbidden `name` field in frontmatter" unconditionally, describing it as the hook's behavior — but the hook (correctly) _requires_ `name` for skills. Correct the wording to the branched rule: commands forbid `name`, skills require it (matching the dir name).

**Tasks:**
1. [ ] Rewrite the line to state both halves of the rule.
2. [ ] Scan CONTRIBUTING.md + docs/PLUGIN-DEVELOPMENT.md for any other unconditional statement of the rule.

**Acceptance Criteria:**
- [ ] WHEN a contributor reads the frontmatter rule in CONTRIBUTING.md THEN it SHALL match what pre-commit and validate.yml enforce.

**Depends On:** none (doc-only; can land with 3.1)

### Phase 3 Testing Requirements

- [ ] validate.yml frontmatter step passes on all 39 skills, fails on the negative fixture.
- [ ] markdownlint clean.

### Phase 3 Completion Checklist

- [ ] Three sources (pre-commit, validate.yml, CONTRIBUTING.md) agree.
- [ ] Skills frontmatter now actually validated in CI.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Skills validate | `npx --yes @anthropic-ai/claude-code@2.1.204 plugin validate plugins/personal-plugin --strict` | Exit 0 (all skills have valid `name`) |
| Negative fixture trips | (run the validate.yml frontmatter logic against `tests/fixtures/invalid-plugin`) | Reports the forbidden-name error |
| Markdown lint | `npx markdownlint-cli 'CONTRIBUTING.md'` | Exit 0 |

<!-- END DOD -->

---

## Phase 4: Reproduce Gates Locally (#149c + #152)

**Estimated Complexity:** M (~6 files, ~60 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Make `pytest` in a tool dir reproduce the CI coverage gate.
- Correct the stale mypy ratchet comments (comments-only; the logic is already a hard zero-gate).
- Do both in one PR since both edit `test.yml` (avoids sibling-PR conflicts).

### Work Items

#### 4.1 Move coverage floors into `[tool.coverage.report]` ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #149(c)
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/pyproject.toml` (add `fail_under = 90`)
- `plugins/personal-plugin/tools/visual-explainer/pyproject.toml` (add `fail_under = 85`)
- `plugins/personal-plugin/tools/feedback-docx-generator/pyproject.toml` (create `[tool.coverage.run] branch = true` + `[tool.coverage.report] fail_under = 95`)
- `.github/workflows/test.yml` (drop `--cov-fail-under=N` from lines 73/125/177; pin `--cov-fail-under=0` on `python-compat`)

**Description:**
Floors live only on the CI command lines, so local `pytest` enforces none. Put `fail_under` in `[tool.coverage.report]` (NOT pytest `addopts` — that makes local single-file runs spuriously fail). feedback-docx has no coverage config at all and its 95 floor was measured _with_ `--cov-branch`; create the section AND `branch = true`, else the floor silently measures a laxer metric. The `python-compat` advisory job runs from tool dirs and would inherit the floor — pin `--cov-fail-under=0` there.

**Tasks:**
1. [ ] Add `fail_under` to the two existing `[tool.coverage.report]` sections.
2. [ ] Create feedback-docx's `[tool.coverage.run] branch = true` + `[tool.coverage.report] fail_under = 95`.
3. [ ] Remove `--cov-fail-under=N` from `test.yml:73,125,177`.
4. [ ] Add `--cov-fail-under=0` (or `--no-cov`) to the `python-compat` invocations.
5. [ ] Verify the root aggregated run is unaffected (it reads only the root `pyproject.toml`, which has no `fail_under`).

**Acceptance Criteria:**
- [ ] WHEN `pytest` runs in a tool dir THEN it SHALL fail if coverage is below that tool's floor.
- [ ] WHEN the three tool CI jobs run THEN they SHALL still enforce 90/85/95 with branch coverage (no silent weakening).
- [ ] WHEN `python-compat` runs THEN it SHALL NOT fail on coverage.
- [ ] WHEN the root aggregated suite runs THEN no floor SHALL apply (unchanged behavior).

**Notes:** The double-apply risk I first suspected is false — pytest reads one configfile per run. The real risk is the feedback-docx `--cov-branch` omission; task 2 handles it.

#### 4.2 Rewrite the stale mypy ratchet comments ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #152
**Files Affected:**
- `.github/workflows/test.yml` (modify comment blocks at lines ~78–82 and ~130–134)

**Description:**
Both comment blocks claim "pre-existing mypy debt (54/98 errors as of 2026-07-16)" and advise tightening toward 0. Both `.mypy-baseline` files contain `0` (verified) — the debt was paid in #129. The ratchet logic is correct and now acts as a hard zero-errors gate. Rewrite the prose to describe the current state; keep the baseline files (the ratchet's data source) and the control flow untouched.

**Tasks:**
1. [ ] Replace the two comment blocks with an accurate description: baseline 0, any new error fails the build, raising the baseline requires justification.
2. [ ] Do NOT alter the ratchet control flow or delete the `.mypy-baseline` files.

**Acceptance Criteria:**
- [ ] WHEN the mypy step comments are read THEN they SHALL state the baseline is 0 and the gate is zero-new-errors.
- [ ] WHEN the mypy jobs run THEN their behavior SHALL be identical to before (comments-only change).

**Notes:** The feedback-docx mypy-gate asymmetry (no baseline, bare `mypy src/`) is deliberately OUT of scope — separate follow-up issue, because unifying it is a two-sided decision.

### Phase 4 Testing Requirements

- [ ] All three tool test jobs pass with unchanged floors.
- [ ] A deliberate coverage drop in a tool fails local `pytest` in that dir.
- [ ] `python-compat` stays green (advisory, no coverage enforcement).

### Phase 4 Completion Checklist

- [ ] Floors reproduce locally.
- [ ] feedback-docx measures branch coverage against its 95 floor.
- [ ] mypy comments accurate; logic untouched.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Local floor enforced | `cd plugins/personal-plugin/tools/visual-explainer && python3 -m pytest tests/ -q` | Fails if coverage < 85 |
| Baseline still 0 | `cat plugins/*/tools/*/.mypy-baseline` | all `0` |
| Comments accurate | `grep -c '54 errors\|98 errors' .github/workflows/test.yml` | 0 |

<!-- END DOD -->

---

## Phase 5: Install the Hook (#149d)

**Estimated Complexity:** S (~3 files, ~30 LOC)
**Dependencies:** Phase 3 (the hook's skill-`name` rule must match the reconciled validators)
**Execution Mode:** Sequential

### Goals

- Make the pre-commit hook run automatically instead of relying on an undocumented manual copy.
- Remove the dead `help.md` sync check so installing the hook doesn't spam every contributor.

### Work Items

#### 5.1 Remove the dead `help.md` sync check ✅ Completed 2026-07-17
**Status:** COMPLETE [2026-07-17]
**Model Tier: sonnet**
**Recommendation Ref:** #149(d) prerequisite
**Files Affected:**
- `scripts/pre-commit` (modify — remove the `check_help_sync` path, ~lines 136–142, 189, 285–286)

**Description:**
`scripts/pre-commit:136` looks for `$plugin_dir/skills/help/SKILL.md`, which exists in no plugin. Every plugin hits the WARN+return, then the script prints "[PASS] help.md sync check complete" — it reports PASS while checking nothing, and its error tips reference a non-existent contract. Remove the dead check so installing the hook (5.2) doesn't hand contributors three phantom warnings per commit.

**Tasks:**
1. [ ] Remove the `check_help_sync` function, its call, and the stale error tips.
2. [ ] Verify the remaining checks (frontmatter, code-block closure, timestamp, ruff) still run and the <5s target holds.

**Acceptance Criteria:**
- [ ] WHEN the hook runs THEN it SHALL NOT emit help.md warnings.
- [ ] WHEN the hook runs THEN it SHALL still enforce frontmatter, code-block, timestamp, and ruff checks.

#### 5.2 Make hook installation automatic and verifiable ✅ Completed 2026-07-17
**Status:** COMPLETE [2026-07-17]
**Model Tier: sonnet**
**Recommendation Ref:** #149(d)
**Files Affected:**
- `scripts/pre-commit` (ensure skill-`name` rule matches Phase 3)
- `CONTRIBUTING.md` (document install + a verification command)
- optionally `scripts/install-hooks.sh` (new — copies the hook and chmods it) OR a documented `core.hooksPath` pointer

**Description:**
The hook is opt-in via manual `cp scripts/pre-commit .git/hooks/`; `.git/hooks/` is verified empty. Provide a scripted, documented install (a tiny `install-hooks.sh` or `git config core.hooksPath`), and document how to verify it's installed. Ensure the hook's skill-`name` requirement matches the Phase 3 reconciliation exactly.

**Tasks:**
1. [ ] Provide a scripted install path + document it in CONTRIBUTING.md.
2. [ ] Add a verification command (e.g. `test -x .git/hooks/pre-commit`).
3. [ ] Confirm the hook's `name`-for-skills logic matches Phase 3.

**Acceptance Criteria:**
- [ ] WHEN a contributor follows CONTRIBUTING.md THEN the hook SHALL be installed with one documented command.
- [ ] WHEN the hook and validate.yml both run on the same tree THEN they SHALL agree on the frontmatter rule.

**Depends On:** 5.1, Phase 3

### Phase 5 Testing Requirements

- [ ] Fresh `.git/hooks/` → documented install → hook fires on a test commit.
- [ ] No help.md warnings; frontmatter/timestamp/ruff checks still fire.

### Phase 5 Completion Checklist

- [ ] Dead check removed.
- [ ] Install scripted, documented, verifiable.
- [ ] Hook rule matches CI rule.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| No dead check | `grep -c 'help.md sync\|check_help_sync' scripts/pre-commit` | 0 |
| Hook runs clean | (install per docs, then) `git commit --allow-empty -m test` in a scratch clone | frontmatter/ruff checks run, no help.md warning |

<!-- END DOD -->

---

## Phase 6: Eval Structural Linter + ADR-0009 (#150)

**Estimated Complexity:** M (~8 files, ~150 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Gate eval _structure_ deterministically (stdlib-only, auth-free) and close the 10-surface coverage gap.
- Record the decision to defer the LLM-judge behavioral runner as ADR-0009.

### Work Items

#### 6.1 Extend `check_eval_mapping.py` into a structural linter ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #150 (CS6a)
**Files Affected:**
- `scripts/check_eval_mapping.py` (modify)
- a few `evals/**/*.eval.md` (normalize non-conforming scenarios, e.g. `prime.eval.md:44` bare `**Must:**`)

**Description:**
Extend the mapping check to also validate structure: every scenario has an Invocation/Context line and ≥1 `Must:` block; every `.eval.md` has a Rubric; and validate the `command:` field even for cross-cutting evals (today `description-triggers.eval.md:2` declares a `command:` matching no live surface and passes only because the cross-cutting branch `continue`s before checking). Tolerate real variance (`**Context:**` vs `**Invocation:**`; `Must NOT` before `Must`) with a normalization pass. Stay stdlib-only (no PyYAML) — this is a required CI check.

**Tasks:**
1. [ ] Add a structural grammar validator (scenario shape, Must presence, Rubric presence).
2. [ ] Normalize scenario-header variants before validating.
3. [ ] Validate `command:` for cross-cutting evals too (fix the dead-field gap).
4. [ ] Fix or normalize the non-conforming specs the validator flags.
5. [ ] Keep it stdlib-only and fast (<2s).

**Acceptance Criteria:**
- [ ] WHEN an eval scenario lacks a `Must:` block THEN the check SHALL fail.
- [ ] WHEN a cross-cutting eval's `command:` names no live surface THEN the check SHALL fail.
- [ ] WHEN the check runs THEN it SHALL import only the stdlib.

#### 6.2 Close the 10-surface eval coverage gap ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #150 (CS6a)
**Files Affected:**
- `scripts/check_eval_mapping.py` (add a coverage assertion + explicit allowlist)
- new `evals/**/*.eval.md` stubs OR allowlist entries for the 10 uncovered surfaces (`arch-review-single`, `arch-synthesize`, `build-cfa-deck`, `fleet-health`, `jetson-audit`, `jetson-recon`, `sg-generate-images`, `sg-validate-graphics`, `spark-audit`, `spark-recon`)

**Description:**
52 of 62 surfaces are covered; 10 are not. Add a coverage gate: every live surface has an eval OR an explicit, justified allowlist entry (e.g. `evaluate-pipeline-output` is pinned to a machine-specific path and is unrunnable in CI — allowlist it with a reason). Silent gaps become CI failures.

**Tasks:**
1. [ ] Add the coverage assertion (live surfaces ⊆ evals ∪ allowlist).
2. [ ] Author minimal eval stubs for the runnable uncovered surfaces; allowlist the unrunnable ones with a stated reason.

**Acceptance Criteria:**
- [ ] WHEN a new skill/command lands without an eval or allowlist entry THEN the check SHALL fail.
- [ ] WHEN the allowlist is read THEN each entry SHALL carry a reason.

**Depends On:** 6.1

#### 6.3 ADR-0009 — defer the LLM-judge behavioral runner ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: sonnet**
**Recommendation Ref:** #150 (decision record)
**Files Affected:**
- `docs/adr/0009-eval-execution-strategy.md` (new)

**Description:**
Record the decision (this session): ship the deterministic structural linter now; defer the LLM-judge runner to an explicit future go/no-go. Context = `evals/README.md:87` (evals are human-run by design) + CI has zero secrets. Decision = structural gate now. Alternatives = full runner now (rejected: first CI secret, fork-PR breakage, flake, cost), hybrid re-authoring (rejected: largest diff, likely equals the structural linter with extra steps), close #150 (rejected: leaves coverage gap + dead field). Status = Accepted.

**Tasks:**
1. [ ] Write ADR-0009 from `references/adr-template.md`; populate Context/Decision/Alternatives from this session.
2. [ ] List it in the Generated ADRs section and reference it from the notebook.

**Acceptance Criteria:**
- [ ] WHEN ADR-0009 is read THEN it SHALL state the structural-linter-now / runner-deferred decision with alternatives and rationale.

**Depends On:** none

### Phase 6 Testing Requirements

- [ ] The extended check passes on the current tree after stub/allowlist additions.
- [ ] A deliberately malformed eval (missing Must) fails the check.
- [ ] markdownlint clean on ADR-0009 and any new evals.

### Phase 6 Completion Checklist

- [ ] Structure gated; coverage gap closed or allowlisted with reasons.
- [ ] Dead `command:` field fixed.
- [ ] ADR-0009 Accepted.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Structural check passes | `python3 scripts/check_eval_mapping.py` | Exit 0 |
| ADR present | `test -f docs/adr/0009-eval-execution-strategy.md && echo ok` | ok |
| Markdown lint | `npx markdownlint-cli 'docs/adr/0009-eval-execution-strategy.md'` | Exit 0 |

<!-- END DOD -->

---

## Phase 7: Rotate the Notebook (#154)

**Estimated Complexity:** M (~6 files, ~700 lines moved)
**Dependencies:** Phase 1 (D14–D18 must be in the Decision Log first)
**Execution Mode:** Sequential

### Goals

- Reduce the mandatory first-read notebook by ~43% with zero decision loss.
- Establish a partial-extraction archive convention (banner + bidirectional pointers) the repo lacks.

### Work Items

#### 7.1 Create the archive file with banner + back-pointer ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: opus**
**Recommendation Ref:** #154
**Files Affected:**
- `docs/archive/LAB_NOTEBOOK-E001-E016.md` (new)

**Description:**
Extract entries E001–E016 (up to the session marker at line 830) verbatim into a new archive file. Prepend a banner: date archived, source (`LAB_NOTEBOOK.md`), entry range, and a back-pointer to the live notebook. The existing `docs/archive/IMPLEMENTATION_PLAN-v*` precedent is whole-file snapshots and doesn't transfer — a partial extraction needs an explicit banner because the slice isn't self-describing. The file must pass markdownlint (`**/*.md` globs it, no ignore).

**Tasks:**
1. [ ] Copy E001–E016 verbatim into the archive.
2. [ ] Add the banner + back-pointer to `../../LAB_NOTEBOOK.md`.
3. [ ] markdownlint the archive.
4. [ ] `git add -f docs/archive/LAB_NOTEBOOK-E001-E016.md` — **`docs/archive/` is matched by the global `~/.gitignore_global` `archive/` rule**, so new files there are ignored; the existing v4–v9 archives are all force-added. A plain `git add -A` will silently skip it.

**Acceptance Criteria:**
- [ ] WHEN the archive is opened THEN its banner SHALL state the range, archive date, and a pointer to the live notebook.
- [ ] WHEN each archived entry's `### Entry NNN` anchor is sought THEN it SHALL be present verbatim.

#### 7.2 Cut E001–E016 from the live notebook + add a forward pointer ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: opus**
**Recommendation Ref:** #154
**Files Affected:**
- `LAB_NOTEBOOK.md` (remove the archived entries; add an archive pointer at the top of the Experiment Log)

**Description:**
Remove the archived entries from the live file (cut at the line-830 session marker so no session narrative is split — re-verify the exact boundary at implementation time, since Phase 1 and Entry 040 shift line numbers). Keep all living sections (Decision Log incl. the Phase-1 D14–D18 rows, Action Items, Prior Work Summary, Current Baseline) and E017–E039. Add a one-line forward pointer at the top of the Experiment Log. Result: ~43% smaller.

**Tasks:**
1. [ ] Re-locate the E016/E017 session-marker boundary (line numbers moved since investigation).
2. [ ] Cut E001–E016; do not split a session or an entry.
3. [ ] Insert the forward pointer.
4. [ ] Re-verify the commit-gate hook still passes (it stats mtime + greps a today/yesterday date; recent entries remain).

**Acceptance Criteria:**
- [ ] WHEN the live notebook is read THEN it SHALL contain the complete D1–D31 Decision Log, E017 onward, and a pointer to the archive.
- [ ] WHEN a session crashes THEN the next session SHALL still continue from `LAB_NOTEBOOK.md` alone (Rule 6 — every decision is still present).
- [ ] WHEN the lab-notebook commit gate runs THEN it SHALL still pass.

**Depends On:** 7.1, Phase 1

#### 7.3 Re-point external references to archived entries ✅ Completed 2026-07-17
**Status: COMPLETE [2026-07-17]**
**Model Tier: opus**
**Recommendation Ref:** #154
**Files Affected:**
- `SECURITY.md` (line ~359 — refs E012/E013/E016)
- `IMPLEMENTATION_PLAN.md` (this file — any ref into E001–E016)
- optionally `CLAUDE.md:26` (E006/E007) and `docs/adr/0005` (E005) — prose mentions

**Description:**
Seven genuine external referrers point at entries that move (CLAUDE.md:26 → E006; SECURITY.md:359 → E012/E013/E016; IMPLEMENTATION_PLAN → E012/E013/E016; ADR-0005 → E005; ADR-0006 → E009 which stays). They are prose mentions ("Entry 0NN"/"E0NN"), not markdown links, so archiving _degrades_ them (a reader must know to look in the archive) rather than _breaking_ them. Add an archive-path hint to the ones worth updating (SECURITY.md, this plan). Do NOT touch the frozen `docs/archive/*` self-references.

**Tasks:**
1. [ ] Add "(archived — see `docs/archive/LAB_NOTEBOOK-E001-E016.md`)" next to the SECURITY.md:359 and IMPLEMENTATION_PLAN references into E001–E016.
2. [ ] Decide per-ref whether CLAUDE.md:26 / ADR-0005 warrant a hint (low value — those decisions are now in the Decision Log table).
3. [ ] Confirm no markdown _link_ target broke (none exist — all are prose).

**Acceptance Criteria:**
- [ ] WHEN an external file references an archived entry THEN either it points at the archive OR the reference resolves via the still-present Decision Log entry.
- [ ] WHEN the repo is searched for broken markdown links to LAB_NOTEBOOK THEN none SHALL exist.

**Depends On:** 7.1

### Phase 7 Testing Requirements

- [ ] Live notebook ~43% smaller; Decision Log complete; E017 onward intact.
- [ ] Archive passes markdownlint; every archived entry present verbatim.
- [ ] Commit-gate hook still passes.
- [ ] No broken links repo-wide.

### Phase 7 Completion Checklist

- [ ] E001–E016 archived with banner + bidirectional pointers.
- [ ] Zero decisions lost (D1–D31 all in the live Decision Log).
- [ ] External refs re-pointed or resolve via the Decision Log.

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Notebook shrunk | `wc -l LAB_NOTEBOOK.md` | materially smaller (~43% fewer lines) |
| Decisions intact | `grep -oP '^\| D\K[0-9]+' LAB_NOTEBOOK.md \| sort -n \| tail -1` | 31 (and no gap 14–18) |
| Archive verbatim | `grep -c '^### Entry' docs/archive/LAB_NOTEBOOK-E001-E016.md` | 16 |
| Markdown lint | `npx markdownlint-cli 'LAB_NOTEBOOK.md' 'docs/archive/LAB_NOTEBOOK-E001-E016.md'` | Exit 0 |

<!-- END DOD -->

---

## Risk Mitigation

| Risk | Phase/Item | Severity | Mitigation | Rollback |
|------|-----------|----------|-----------|----------|
| Wiring the dead README script yields a green no-op gate | 2.2→2.3 | High | Hard order: repair (2.2), verify exit-2, then wire (2.3) | Revert the PR |
| Regenerating README destroys hand-edited flag docs | 2.1→2.2 | Medium | Migrate flag info to frontmatter (2.1) before regen (2.2) | Revert; rows restored from git |
| Recursive glob fails all 39 skills | 3.1 | High | Use `glob('*/SKILL.md')`, never `rglob`; verify against strict CLI | Revert the workflow change |
| feedback-docx floor silently weakens (branch omitted) | 4.1 | Medium | Mitigated — `branch = true` added alongside `fail_under = 95` in `[tool.coverage.run]` | Revert pyproject |
| `python-compat` inherits the floor and goes red | 4.1 | Low | Mitigated — `--cov-fail-under=0` pinned on all three python-compat pytest invocations | Revert workflow line |
| Rotation deletes D14–D18 / orphans ADR-0005 | Phase 1 gates Phase 7 | High | Mitigated — Phase 1 (Entry 042) promoted D14–D18 into the Decision Log table; Phase 7 no longer blocked | Restore from git / archive |
| Installing the hook spams contributors (dead help.md check) | 5.1→5.2 | Low | Mitigated — dead check removed (5.1) before scripted install added (5.2) | Revert hook |
| New required-check name deadlocks merges (PLAT-012 class) | 2.3, 3.1, 6.x | Medium | Only add _steps_ to existing jobs; never rename/add required checks | Revert; check set unchanged |
| Branch protection blocks self-merge (bus factor 1) | all PRs | Low | `enforce_admins=false` (D22) permits owner merge on green | n/a |

## Unknowns Register

| Unknown | Severity | Affects | Resolution |
|---------|----------|---------|-----------|
| Should CI ever hold a secret for an LLM-judge eval runner? | Medium | #150 follow-up | Deferred to ADR-0009 as explicit go/no-go — NOT decided here |
| Which direction to unify the feedback-docx mypy asymmetry (give it a baseline, or drop both baselines for bare `mypy`)? | Low | Phase 4 scope-out | Separate follow-up issue; both directions valid |
| Exact prose-count rewrite scope in `update-readme.py` (sentence + headers only, no reflow) | Low | 2.2 | Resolve during implementation with a tight regex on the count tokens |
| Exact E016/E017 cut line after Phases 1 + Entry 040 shift line numbers | Low | 7.2 | Re-locate the session marker at implementation time, not by the static 830 |

## Scope Boundaries

**This plan covers:** the six canonical issues #149–#154, with the four re-scopings the investigation forced, plus the D14–D18 data-integrity prerequisite and ADR-0009.

**This plan explicitly does NOT cover:**
- The LLM-judge behavioral eval runner (deferred to ADR-0009; a CI-posture decision).
- The `feedback-docx-generator` mypy-gate asymmetry (separate follow-up issue).
- A `rotate` operation for the `lab-notebook` skill (separate follow-up issue; without it #154 recurs in ~40 entries).
- `evals/skills/evaluate-pipeline-output.eval.md`'s machine-specific path (allowlisted in 6.2, not fixed).

## Generated ADRs

| ADR | Title | Status | Change Set |
|-----|-------|--------|-----------|
| ADR-0009 | Eval execution strategy (structural linter now, behavioral runner deferred) | Proposed → Accepted (in 6.3) | Phase 6 |

## Execution Notes

- One branch + PR + merge per phase (per the C20 precedent). Each PR must be green on all 14 required checks (ubuntu + windows) before merge.
- `autoUpdate` propagates content from `origin/main` — **no version bump** for any phase.
- Log a LAB_NOTEBOOK entry before the first commit of each phase (Rule 11).
- Suggested verification points: stop after Phase 2 (root cause closed) and after Phase 4 (gates reproducible) to confirm before proceeding.
- Phases 1, 3, 4, 6 are mutually independent and could run in any order or as parallel branches; 2 is the highest-leverage; 5 depends on 3; 7 depends on 1.

---

_Plan generated by `/ultra-plan` on 2026-07-17 from the `/prime` backlog (#149–#154). Prior plan archived at `docs/archive/IMPLEMENTATION_PLAN-v9.md`._
