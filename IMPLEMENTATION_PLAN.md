# Implementation Plan

**Generated:** 2026-07-29
**Based On:** `/ultra-plan` over the 24-item open backlog (LAB_NOTEBOOK E060). Phase 1 investigation ran 11 parallel Explore agents; **22 of 24 issues required correction**, so this plan encodes the *investigated* shape of each item, not the filed text. Prior plan (task-sync build, COMPLETE) archived at `docs/archive/IMPLEMENTATION_PLAN-v11.md`.
**Total Phases:** 8
**Estimated Total Effort:** ~42 work items across ~70 files (predominantly markdown behavior-surfaces; one Python change set, one CI gate, two ADRs)

---

## Executive Summary

This plan fixes **16 issues that are either producing wrong output today or actively multiplying defects into future work**. It deliberately defers 8 calibration and hygiene issues to a later plan — none of those is currently wrong, and front-loading them behind silent-corruption bugs would be the wrong ordering.

Three findings from investigation reshaped the work and are load-bearing throughout:

1. **The dynamic-injection escaping rule is inverted.** The harness blanks an inline-code span unless the character before its opening backtick is `` ` `` or `!`, so the *tidy* `` `` !`cmd` `` `` form is **live** and the *sloppy* `` `!`cmd`` `` form is **inert**. This is why `prime` (7 sites) and `explain-project` (2) — the two largest blocks cited in #183 — execute nothing, while two components crashed on every invocation (already fixed, 11.5.1). Phase 1 codifies the rule as ADR-0011 and builds the only linter that can enforce it: one that **replays the pre-pass rather than grepping**.

2. **#202 as filed would delete working features.** Six of the eight "unverified" frontmatter keys are real. The actual defect is *correct keys documented with wrong semantics* — `paths:` is a load-gate, not a save-trigger; `hooks:` takes an event-record, not `pre:`/`post:`; `isolation:` is agent frontmatter, not skill. Phase 5 inverts the remedy accordingly.

3. **The generator layer is the highest-leverage surface in the repo.** Five files (`commands/new-skill.md`, `references/templates/skill.md`, `common-patterns.md`, `patterns/advanced-features.md`, `new-skill-examples.md`) are implicated by six separate issues and propagate every defect into every future skill. Phase 5 treats them as one atomic change set rather than six colliding PRs.

The plan groups by **root cause, not by issue number**. Four issues (#183, #192, #197, #201) are split across phases where their sub-defects belong to different causes; two (#183/#190) share a single line and are fixed in one edit.

---

## Plan Overview

Ordering is driven by three constraints established in Phase 2 interaction mapping:

- **Active harm first.** Phases 2–4 fix things producing wrong output now: bpmn-to-drawio silently corrupts diagram layout, `build-cfa-deck`'s two slide-removal implementations both fail, and task-sync can silently clobber a remote issue. These precede the documentation multipliers.
- **Doctrine before its dependents.** Phase 1 must land before Phase 7 touches `prime`: without the corrected injection rule, a well-meaning "tidy the backticks" edit would **switch on 7 shell executions that have never run**, four of which `Bash(git:*)` rejects for containing pipes — breaking a skill that currently works.
- **Enumerations before enforcement.** Phase 5 corrects the `agent:` vocabulary that Phase 7 then applies; Phase 5 corrects the `disable-model-invocation` definition that Phase 8 then acts on.

The critical path is **1 → 5 → 7 → 8**. Phases 2, 3, and 4 are independent of it and of each other, and can run in parallel with anything.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|------------|------------------|-----------------|--------------|----------------|
| 1 | Injection doctrine + `ship`/`clear-prep` | ADR-0011; corrected root-cause doc; guarded injections; two dead gates repaired; a pre-pass-replaying linter | M (~7 files, ~250 LOC) | None | Sequential |
| 2 | bpmn silent corruption + visual-explainer env vars | `HAS_DI` branch deleted; 15-var table; tool version truth | M (~8 files, ~200 LOC) | None | Parallel |
| 3 | Hook recipes + build-cfa-deck | 3 recipes structurally correct; one working slide-removal impl; `CFA_ASSETS_DIR` | M (~7 files, ~250 LOC) | None | Parallel |
| 4 | task-sync orphan handling + pagination | `ORPHAN_LOCAL` class; `SyncPlan.orphans`; fail-loud saturation; REST pagination | L (~10 files, ~600 LOC) | None | Sequential |
| 5 | Generator / harness-feature catalog | ADR-0012; `paths:`/`hooks:`/`agent:`/`effort` corrected; fictional keys removed; tier aliases | L (~8 files, ~450 LOC) | Phase 1 (doctrine) | Sequential |
| 6 | ADR-0005 enforcement + model-ID instances | CI gate (step), pre-commit Check 5, README fix, remaining stale IDs | M (~9 files, ~200 LOC) | None | Sequential |
| 7 | `allowed-tools` grant sets | `Agent`/`Task` resolved; 10 components corrected; AskUserQuestion adopted | M (~16 files, ~250 LOC) | Phases 1, 5 | Sequential |
| 8 | Trigger metadata + eval re-baseline | 11 skills resolved 3 ways; 2 new Phase-0 gates; evals re-baselined | M (~15 files, ~250 LOC) | Phase 5 | Sequential |

### Execution Hints

| Phase | Model Tier | Context Budget | Notes |
|-------|------------|----------------|-------|
| All (default) | `sonnet` | Standard | Per-item Model Tier takes precedence |
| 1 | `opus` | Extended | One line (`ship:30`) is owned by two issues and must satisfy both; the linter must be negative-tested before wiring |
| 4 | `opus` | Extended | Reconcile-engine change with a documented never-clobber invariant (ADR-0010, D35) |
| 5 | `opus` | Extended | Inverted remedy — the risk is deleting working capability, not missing a fix |

### Milestones

| Milestone | Phases | Description |
|-----------|--------|-------------|
| Correctness | 1–4 | Nothing in the repo silently produces wrong output. Shippable on its own. |
| Class-closed | 1–6 | The defect *classes* are gated: injections linted, ADR-0005 enforced, catalog verified against the harness. |
| Complete | 1–8 | Grant sets and dispatch metadata consistent; evals re-baselined under Opus 5. |

---

## Phase 1: Injection Doctrine and the Guards Built On It

**Execution Mode:** Sequential

### Goals

Establish the true semantics of `` !`cmd` `` injection as an ADR, correct the reference doc that taught the opposite, guard the injections that legitimately fail outside a git repo, repair two gates that cannot fire, and build a linter that can actually detect the defect class.

### Work Items

#### 1.1 ADR-0011: dynamic-injection doctrine, and correct the root-cause doc ✅ Completed 2026-07-28
**Status: COMPLETE 2026-07-28**
**Model Tier: opus**
**Recommendation Ref:** #183 (root cause)
**Depends On:** None
**Files Affected:**
- `docs/adr/0011-dynamic-injection-doctrine.md` (create)
- `plugins/personal-plugin/references/patterns/advanced-features.md` (modify)

**Description:**
`advanced-features.md:132` states that a failed injection produces empty output and surfaces no error. The decompiled handler `throw`s on a `ShellError`: `Promise.all` rejects, prompt expansion fails, and the skill never reaches the model. The doc teaches the opposite of the truth, and every unguarded injection in the repo traces to it. ADR-0011 records four facts: injections expand at **parse time** (before `$ARGUMENTS` exists); a **non-zero exit aborts skill load**; injections are **permission-checked against `allowed-tools`**; and the escaping rule is inverted, so documentation examples must use the nested form.

**Tasks:**
1. [x] Write `docs/adr/0011-dynamic-injection-doctrine.md` (status: Accepted) covering all four facts, with the `Jds`/`Cfo` mechanism and the LIVE/INERT table
2. [x] Rewrite `advanced-features.md:113-132` to state both rules, replacing the false "failure is silent" sentence
3. [x] Convert every example in that file to the inert nested form (6 currently-live forms; documentation-only, so nothing executes today, but they teach the dangerous shape)
4. [x] Cross-link ADR-0011 from `CLAUDE.md`'s Verified Operational Rules

**Acceptance Criteria:**
- [x] WHEN a reader follows `advanced-features.md` THEN the guidance SHALL state that a non-zero exit aborts skill load, not that it yields empty output
- [x] WHEN the extractor replay is run against `advanced-features.md` THEN it SHALL report 0 live injections
- [x] ADR-0011 exists with status Accepted and is referenced from CLAUDE.md

**Notes:**
Evidence is in LAB_NOTEBOOK E059. Do not soften the escaping-rule table — its counterintuitiveness is the entire point.

**Completion notes (2026-07-28):**
- **Facts re-derived from the binary, not from E059's summary** (E039). `Jds`, `Cfo`, `WFe`, `en_`, and `Aee` were recovered verbatim from `~/.local/share/claude/versions/2.1.220` and are quoted in the ADR. The recovery surfaced a **fifth** live form E059 had not enumerated: `Cfo` unions a second matcher, `soy`, matching a fenced block whose info string is `!`, which runs against the **raw** text — a `!`-fenced block is never pre-passed and is therefore live regardless of context, including inside a quoted example. That is now F1, and it is the specific case R4 cites as invisible to any grep.
- **The replay was negative-tested before its zeros were trusted** (E043): tidy-form fixture → LIVE=1, nested-form fixture → LIVE=0, in the same run that reported 0 for the edited files. Nine forms were enumerated by replay for the ADR's LIVE/INERT table, not reasoned about.
- **`advanced-features.md` 6 → 0 live**, and the ADR and `CLAUDE.md` were both replayed to 0 as well. The ADR's first draft was itself **1 LIVE** — the literal `soy` regex contains a `!`-fence — which is why the ADR writes that regex as a string concatenation and why dangerous forms in it use a visible `\!` neutralizer.
- **Risk-table row deliberately left `Open`.** "Someone 'tidies' `prime`'s backticks…" is scoped to **7.3**, and its mitigation has two halves: ADR-0011 landing first (done here) and 7.3 carrying an explicit do-not instruction (not done). Flipping it to `Mitigated` now would tell Phase 7's implementer the do-not instruction is unnecessary — the precise harm the row describes. It closes when 7.3 closes.

---

#### 1.2 `ship`: guard the five git injections and repair the diff-size gate
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #183, #190 (atomic)
**Depends On:** 1.1
**Files Affected:**
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify)

**Description:**
`ship:30` is a single line owned by two issues. #183 needs it exit-0-safe; #190 needs it to compute a number. It currently emits the literal string `deletions(-)` — `$NF` is always the trailing *word* of `git diff --stat`'s summary line, never a number — so the `> 500` comparison is string-vs-int and the gate has never fired. Two further defects the issue misses: the metric needs insertions **plus** deletions summed, and `git diff --stat` covers *unstaged* changes only, so the normal pre-ship state (everything already `git add`-ed) yields empty regardless of size.

**Tasks:**
1. [ ] Guard `:15, :18, :21, :24, :27` with `2>/dev/null || echo "(not a git repository)"`
2. [ ] Replace `:30` with `git diff HEAD --shortstat 2>/dev/null | grep -oE '[0-9]+ (insertions?|deletions?)' | awk '{s+=$1} END {print s+0}'` — covers staged+unstaged, sums both, and `s+0` forces numeric `0` rather than empty
3. [ ] Repair the second dead gate at `:77` ("remote output above will be empty if not a git repo; abort if so") — unreachable today, and a false positive for a valid repo with no remote configured
4. [ ] Verify `:80` and `:275` need no text change once the injected value is numeric

**Acceptance Criteria:**
- [ ] WHEN `ship` loads in a non-git directory THEN every injection SHALL exit 0 and the pre-flight SHALL abort on the sentinel rather than on expansion failure
- [ ] WHEN a 550-line change is staged THEN the diff-size gate SHALL evaluate `550 > 500` and route to `/code-review ultra`
- [ ] WHEN all changes are already staged THEN the gate SHALL still see the full line count
- [ ] The extractor replay reports 6 live injections in `ship/SKILL.md`, all exiting 0 in a non-git directory

**Notes:**
Verified empirically: `git diff HEAD~5 HEAD --stat | tail -1 | awk '{print $NF}'` returns `deletions(-)` on a 550-line change; the replacement returns `550`. Do not split this item — a #183-only fix leaves the gate broken, a #190-only fix leaves it exit-unsafe.

---

#### 1.3 `ship`: grant the tools `--audit` needs
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #190
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify)

**Description:**
`:57-62` requires creating `.claude-plugin/` and appending `.claude-plugin/audit.log`, but `allowed-tools` grants no `Write` and no `Bash(mkdir:*)`. `Edit` cannot create a file. `commands/clean-repo.md:4` grants `Write` for the identical audit-log pattern.

**Tasks:**
1. [ ] Add `Write` and `Bash(mkdir:*)` to `ship`'s `allowed-tools`
2. [ ] Add `Bash(tail:*)`, `Bash(awk:*)`, `Bash(grep:*)` for the injection pipes in `:30`

**Acceptance Criteria:**
- [ ] WHEN `ship --audit` runs THEN it SHALL create the audit directory and append the log without a permission prompt
- [ ] Every binary invoked by a `ship` injection appears in its `allowed-tools`

---

#### 1.4 `clear-prep`: guard three git injections
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #183
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/clear-prep/SKILL.md` (modify)

**Description:**
`:27, :28, :29` abort the skill in a non-git directory (`:28` is the originally-reported failure). `clear-prep`'s own Error Handling at `:130-132` promises "Not a git repo: skip git-delta steps" — currently unreachable. Phase 1 step 1 re-runs the same three commands via Bash anyway, so deletion is also a valid fix.

**Tasks:**
1. [ ] Guard all three with `2>/dev/null || echo "(not a git repository)"`
2. [ ] Confirm the Error Handling clause at `:130-132` is now reachable

**Acceptance Criteria:**
- [ ] WHEN `clear-prep` loads outside a git repository THEN it SHALL load successfully and skip the git-delta steps per its documented behavior

---

#### 1.5 Correct #183's location table
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #183
**Depends On:** 1.1
**Files Affected:**
- (GitHub issue #183 — no repo file)

**Description:**
**#183's table is 50% wrong by site.** `prime` (7) and `explain-project` (2) are **inert** and must be removed; `commands/new-skill.md` must be added (fixed in 11.5.1); `leak-risk-audit` must be recharacterized from "non-git" to "every directory" (also fixed in 11.5.1). The mechanism half of the issue is verified correct and stands.

**Tasks:**
1. [ ] Post a correcting comment on #183 with the replay-verified live/inert table
2. [ ] Note that `references/**` and `deprecated/**` sites are never expanded

**Acceptance Criteria:**
- [ ] #183's scope reflects the 14 live sites in executable surfaces, not the 74 textual matches

---

#### 1.6 Injection linter that replays the pre-pass
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #183 (class closure)
**Depends On:** 1.1, 1.2, 1.4
**Files Affected:**
- `scripts/check_injections.py` (create)
- `.github/workflows/validate.yml` (modify — **step**, not job)
- `scripts/pre-commit` (modify)

**Description:**
A textual grep for `` !` `` finds 74 sites under `plugins/`, only 14 of which are live in an executable surface — a grep-based linter would be 81% false positives and would still miss the blanking rule. The linter must replay `Jds` + the extractor regex, then assert that every live injection in a skill or command body is exit-0-safe (guarded, or a pipe-terminated form) and that every binary it invokes appears in that component's `allowed-tools`.

**Tasks:**
1. [ ] Implement `scripts/check_injections.py` (stdlib only — the `plugin-validate` job installs no Python)
2. [ ] Restrict scanning to `plugins/*/skills/*/SKILL.md` and `plugins/*/commands/*.md`; exclude `references/**` and `deprecated/**`
3. [ ] **Negative-test before wiring**: a fixture with an unguarded live injection must exit 1; the current tree must exit 0
4. [ ] Wire as a step in the existing `Validate Plugins (official CLI)` job and as a block in `scripts/pre-commit`

**Acceptance Criteria:**
- [ ] WHEN an unguarded live injection is added to any skill body THEN the linter SHALL exit 1 naming the file, line, and command
- [ ] WHEN the inert nested form is used in documentation THEN the linter SHALL NOT flag it
- [ ] WHEN run against the current tree THEN the linter SHALL exit 0
- [ ] The linter is added as a **step**; the required-check name is unchanged (D28)

**Notes:**
This is the E043 rule applied to itself: the guard must be shown to fail against deliberately-bad input before it is trusted.

---

### Phase 1 Testing Requirements

- [ ] Extractor replay reports the expected live counts per file before and after
- [ ] Every `ship`/`clear-prep` injection exits 0 in a scratch non-git directory
- [ ] The diff-size gate returns a number on a >500-line staged change
- [ ] Linter negative-tested in both directions

### Phase 1 Completion Checklist

- [ ] All work items complete
- [ ] ADR-0011 Accepted and cross-linked
- [ ] markdownlint clean on every touched file
- [ ] No regressions to `prime`, `explain-project`, or the 24 correctly-guarded slide-gen injections

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Injection linter | `python3 scripts/check_injections.py` | Exit code 0 |
| Linter negative test | `python3 scripts/check_injections.py --self-test` | Exit code 0 (asserts a bad fixture exits 1) |
| Markdown lint | `npx markdownlint-cli2 "plugins/**/*.md" "docs/**/*.md"` | Exit code 0 |
| Plugin validation | `claude plugin validate --strict ./plugins/personal-plugin` | Exit code 0 |
| Pre-commit | `bash scripts/pre-commit` | Exit code 0 |

<!-- END DOD -->

---

## Phase 2: bpmn-to-drawio Silent Corruption and visual-explainer Env Vars

**Execution Mode:** Parallel

### Goals

Stop a SKILL.md from instructing Claude to override a correct tool default with the exact value that shipped as a P1 regression, and make the visual-explainer documentation describe the env vars the tool actually reads.

### Work Items

#### 2.1 bpmn-to-drawio: delete the `HAS_DI` decision, let `auto` decide
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #193
**Depends On:** None
**Files Affected:**
- `plugins/bpmn-plugin/skills/bpmn-to-drawio/SKILL.md` (modify)

**Description:**
The skill greps for `bpmndi:BPMNDiagram` — an **any-DI** test — concludes `HAS_DI=true`, and instructs `--layout=preserve`. That is the pre-4.3.1 `has_di_coordinates` semantics reimplemented in bash, and it overrides the tool's `auto`, which resolves to `preserve` only on **complete** DI (`converter.py:73-75`). On a partially-DI file the DI-less shapes are stranded at (0,0) — issue #143 verbatim, re-issued as an instruction. The output is valid XML with exit 0 and no warning, so it presents as a tool bug.

**Tasks:**
1. [ ] Delete the `HAS_DI` grep and branch (`:96`, `:123`, `:131-132`)
2. [ ] Rewrite `:136-148` so bare invocation is described as `--layout auto`, not "graphviz auto-layout"
3. [ ] Correct `:65` (Graphviz is not required for complete-DI files), `:89-90`, `:192`, `:230` (troubleshooting row diagnoses the wrong cause), and `:332` (recommends the bug-triggering flag as a *performance optimization*)
4. [ ] Keep the `--layout=preserve`/`--layout=graphviz` flags documented — only the recommendation to hand-select them is removed

**Acceptance Criteria:**
- [ ] WHEN a partially-DI BPMN file is converted THEN the skill SHALL NOT instruct `--layout=preserve`
- [ ] WHEN a file has no DI THEN `auto` SHALL resolve to graphviz without the skill special-casing it
- [ ] All 9 contradicting sites reconciled against `converter.py` / `models.py`

**Notes:**
D30 records the tool-side fix. Do not widen `converter.py:101-105`'s warning as part of a docs fix — that would be a behavior change to a released tool.

---

#### 2.2 bpmn2drawio reference and README: `auto` exists and is the default
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #193
**Depends On:** None
**Files Affected:**
- `plugins/bpmn-plugin/references/bpmn2drawio-reference.md` (modify)
- `plugins/bpmn-plugin/tools/bpmn2drawio/README.md` (modify)
- `plugins/bpmn-plugin/README.md` (modify)

**Tasks:**
1. [ ] `reference.md:30`: choices are `auto|graphviz|preserve`, default `auto`
2. [ ] `reference.md:129`: drop the pinned `layout="graphviz"` from the Python example
3. [ ] Tool README: document `auto`; correct the "Python 3.9+" badge to 3.10+ (`pyproject.toml:11`)
4. [ ] `plugins/bpmn-plugin/README.md:28`: `4.2.0` → `4.3.1`
5. [ ] `cli.py:23-28`: the `--help` epilog example never mentions `auto`

**Acceptance Criteria:**
- [ ] WHEN a reader consults any bpmn2drawio doc THEN the documented `--layout` default SHALL match `cli.py:55-56`

---

#### 2.3 bpmn2drawio: make `--version` tell the truth
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #193 (unfiled)
**Depends On:** None
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/pyproject.toml` (modify)
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/__init__.py` (modify)

**Description:**
Both declare `version = "1.0.0"` while the plugin is 4.3.1, so `bpmn2drawio --version` prints `1.0.0`. A user told to "verify you're on 4.3.1" — the release that fixed the very bug 2.1 is about — cannot do so from the tool.

**Tasks:**
1. [ ] Set both to `4.3.1`; add a note tying tool version to plugin version
2. [ ] Confirm no test asserts `1.0.0`

**Acceptance Criteria:**
- [ ] WHEN `bpmn2drawio --version` runs THEN it SHALL report the plugin version

---

#### 2.4 visual-explainer SKILL: correct the env var names
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #196
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)

**Description:**
`$GOOGLE_IMAGE_MODEL` (`:40`, `:116`) appears **zero** times in the tool. It was the name *proposed* in `IMPLEMENTATION_PLAN-v4.md:724`; the implementation used `VISUAL_EXPLAINER_GEMINI_MODEL` (`config.py:364`). Setting the documented variable is a silent no-op.

**Tasks:**
1. [ ] Rename to `VISUAL_EXPLAINER_GEMINI_MODEL`; add `VISUAL_EXPLAINER_CLAUDE_MODEL`
2. [ ] Reconcile the "Tested Results" block at `:53-58` — it cites threshold 0.75 while the shipped default is 0.85

**Acceptance Criteria:**
- [ ] WHEN a user exports the documented model-override variable THEN the tool SHALL use it
- [ ] `references/api-key-setup.md` is **not** modified — its model vars belong to `/research-topic`

---

#### 2.5 visual-explainer README: the authoritative 15-variable table
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #196
**Depends On:** 2.4
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/README.md` (modify)

**Description:**
Documentation covers 2 of the tool's 15 environment variables (13%). Worse, `:176-190` claims the internal defaults "can be customized **in code**" — false; all six are env-overridable via `InternalConfig.from_env`, and the class docstring says so.

**Tasks:**
1. [ ] Add the full 15-variable table (name, default, effect, code site)
2. [ ] Delete the "customized in code" claim
3. [ ] Do not hand-edit `PKG-INFO` (build artifact)

**Acceptance Criteria:**
- [ ] Documented variable count equals the count read by `config.py` (15)

---

### Phase 2 Testing Requirements

- [ ] A partial-DI fixture converts without stranded shapes when following the skill
- [ ] `bpmn2drawio --version` matches `plugin.json`
- [ ] Each documented env var is greppable in `config.py`

### Phase 2 Completion Checklist

- [ ] All work items complete
- [ ] bpmn2drawio suite still green (640 tests / 92.84%)
- [ ] markdownlint clean

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| bpmn tests | `cd plugins/bpmn-plugin/tools/bpmn2drawio && PYTHONPATH=src python -m pytest tests/ -q` | Exit code 0 |
| visual-explainer tests | `cd plugins/personal-plugin/tools/visual-explainer && PYTHONPATH=src python -m pytest tests/ -q` | Exit code 0 |
| Env-var doc parity | `python3 -c "import re,pathlib; s=pathlib.Path('plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/config.py').read_text(); print(len(set(re.findall(r'os.getenv\(\"([A-Z_]+)\"', s))))"` | Matches documented count |
| Markdown lint | `npx markdownlint-cli2 "plugins/**/*.md"` | Exit code 0 |

<!-- END DOD -->

---

## Phase 3: Hook Recipes and build-cfa-deck

**Execution Mode:** Parallel

### Goals

Make the three hook recipes loadable, and make `build-cfa-deck`'s documented procedure actually execute.

### Work Items

#### 3.1 Hook recipes: fix both structural levels
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #194
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/references/hooks/planning-stop-hook.md` (modify)
- `plugins/personal-plugin/references/hooks/session-start-hook.md` (modify)
- `plugins/personal-plugin/references/hooks/verification-post-edit-hook.md` (modify)

**Description:**
Two **independent** structural errors: the missing top-level `hooks` wrapper, and the missing matcher-group level (`{ "matcher": …, "hooks": [ … ] }`). A partial fix that adds only the wrapper swaps a silent no-op for a schema error. Also: `timeout: 10000` is milliseconds where the schema takes seconds; `$CLAUDE_TOOL_NAME` / `$CLAUDE_FILE_PATH` do not exist (the working hook parses stdin JSON via `jq`); and `.claude/hooks.json` is not a loader input at all — project hooks live under the `hooks` key of `.claude/settings.json`. Failure is **silent**, which is why this survived.

**Tasks:**
1. [ ] Rewrite all three JSON blocks against `plugins/personal-plugin/hooks/hooks.json` as ground truth
2. [ ] Correct timeouts to seconds; replace env-var access with `matcher` or stdin `jq`
3. [ ] Correct the target path in `planning-stop-hook.md:11`
4. [ ] Fix `hooks/scripts/lab-notebook-gate.sh:7,52` — the `--no-verify` bypass claim is false (the gate is PreToolUse-only)
5. [ ] Keep the "NOT auto-installed" banners and the filenames (referenced by `validate-plugin.md:314`)

**Acceptance Criteria:**
- [ ] WHEN a recipe is copied into `.claude/settings.json` THEN the hook SHALL register and fire
- [ ] Each corrected JSON block validates against the same shape as the working `hooks/hooks.json`
- [ ] `common-patterns.md:243` (already correct) and the recipes no longer contradict each other

---

#### 3.2 build-cfa-deck: fix the dead primary snippet
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #195
**Depends On:** None
**Files Affected:**
- `plugins/slide-gen/skills/build-cfa-deck/SKILL.md` (modify)

**Description:**
`os` is referenced at `:74` and imported at `:78`, so the snippet raises `NameError` before reaching the import. `2>/dev/null` swallows the traceback and `||` triggers the fallback — **100% of the time, on every machine**. The fallback prints only placeholder indices, dropping the placeholder *type* that step 4 (`:150`) depends on.

**Tasks:**
1. [ ] Move `import os` above `:74`
2. [ ] Delete the now-redundant fallback at `:79-86` and the `2>/dev/null` mask
3. [ ] Verify step 4's idx/type mapping instructions are satisfiable from the primary output

**Acceptance Criteria:**
- [ ] WHEN step 2 runs THEN it SHALL emit placeholder index **and** type on the first attempt

---

#### 3.3 build-cfa-deck: one working slide-removal implementation
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #195
**Depends On:** 3.2
**Files Affected:**
- `plugins/slide-gen/skills/build-cfa-deck/SKILL.md` (modify)
- `plugins/slide-gen/references/cfa-deck-helpers.md` (create)

**Description:**
Both implementations fail against the installed python-pptx 1.0.2: `prs.presentation.sldIdLst` raises `AttributeError` (no such attribute) and `del prs.part.rels[rId]` raises `TypeError` (`_Relationships` is a `Mapping`, not `MutableMapping`). The one labelled "use this reliable approach" is not. Verified replacements: `prs.slides._sldIdLst` and `prs.part.drop_rel(rId)`. The error-handling row at `:306` routes failures back into the broken branch.

**Tasks:**
1. [ ] Keep `remove_all_slides` (better rId resolution); apply both substitutions
2. [ ] Delete `remove_samples` and its dead `copy`/`lxml` imports
3. [ ] **Execute the result against the real template** before the doc claims it works
4. [ ] Pin the python-pptx version assumption in Prerequisites (`_sldIdLst` is a private attribute)
5. [ ] Extract the ~110-line inline block to `references/` — an extracted helper is runnable and therefore testable

**Acceptance Criteria:**
- [ ] WHEN slide removal runs against `CFA PPT Template2.pptx` THEN it SHALL remove the sample slides without raising
- [ ] Exactly one removal implementation exists in the repo
- [ ] The error-handling row no longer points at a removed implementation

**Notes:**
Fixing this by reading would repeat the exact defect — the current text already carries a reliability claim that execution disproves.

---

#### 3.4 build-cfa-deck: parameterize the asset root and stop on MISSING
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #195
**Depends On:** None
**Files Affected:**
- `plugins/slide-gen/skills/build-cfa-deck/SKILL.md` (modify)
- `docs/adr/0008-slide-gen-dependency-model.md` (modify)

**Description:**
Ten sites hard-code `~/dev/stratfield/slide-generator/examples` (the issue lists eight; `:74` and `:82` are missed). The preflights at `:18-24` print "MISSING" and the skill **proceeds anyway** — the exact failure mode ADR-0008's fail-fast principle exists to prevent, in the one skill that omits the `sg --version` preflight all eight siblings have. Owner-only status covers the `sg` engine; it has never covered an undeclared asset root.

**Tasks:**
1. [ ] Introduce `CFA_ASSETS_DIR` (default `~/dev/stratfield/slide-generator/examples`); use it at all ten sites
2. [ ] Add a hard stop when any preflight reports MISSING
3. [ ] Move `/tmp/build_cfa_deck.py` to `.tmp/` per the house convention
4. [ ] Add a one-sentence build-cfa-deck carve-out to ADR-0008:9, which this skill currently falsifies (zero `sg` invocations, ~110 lines of PowerPoint logic in-plugin)

**Acceptance Criteria:**
- [ ] WHEN `CFA_ASSETS_DIR` is unset and the default path is absent THEN the skill SHALL stop with a clear message rather than proceeding
- [ ] No absolute machine-specific path remains in the skill body
- [ ] ADR-0008 no longer makes a claim this skill contradicts

---

### Phase 3 Testing Requirements

- [ ] Each corrected hook recipe parses against the working `hooks.json` shape
- [ ] Slide removal executed against the real `.pptx`, not reviewed
- [ ] Preflight stop verified with `CFA_ASSETS_DIR` pointed at a nonexistent path

### Phase 3 Completion Checklist

- [ ] All work items complete
- [ ] markdownlint clean
- [ ] `claude plugin validate --strict ./plugins/slide-gen` passes

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Hook JSON shape | `python3 -c "import json,glob,re,pathlib; [json.loads(re.search(r'\`\`\`json\n(.*?)\n\`\`\`', pathlib.Path(f).read_text(), re.S).group(1)) for f in glob.glob('plugins/personal-plugin/references/hooks/*.md')]"` | Exit code 0 |
| slide-gen validation | `claude plugin validate --strict ./plugins/slide-gen` | Exit code 0 |
| Markdown lint | `npx markdownlint-cli2 "plugins/**/*.md" "docs/**/*.md"` | Exit code 0 |

<!-- END DOD -->

---

## Phase 4: task-sync Orphan Handling and Pagination

**Execution Mode:** Sequential

### Goals

Close the one path where task-sync can silently clobber or lose data, and make the fetched issue list — which `classify` treats as authoritative — actually complete.

### Work Items

#### 4.1 `ClassKind.ORPHAN_LOCAL`: classify a vanished issue as its own kind
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #181
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/src/task_sync/reconcile/classify.py` (modify)
- `plugins/personal-plugin/tools/task-sync/src/task_sync/reconcile/resolve.py` (modify)
- `plugins/personal-plugin/tools/task-sync/tests/test_classify.py` (modify)
- `plugins/personal-plugin/tools/task-sync/tests/test_resolve.py` (modify)

**Description:**
`ClassKind` has no orphan member, so `classify` maps a vanished issue onto `CHANGED_LOCAL`/`UNCHANGED` and nulls only the `issue` field — **`task.issue_number` stays populated**. `resolve.py:212` tests `c.task.issue_number is None`, gets `False`, and emits a `PushAction`. Two outcomes, both bad: the issue is genuinely gone and `gh issue edit` raises mid-loop (leaving `tasks.json` unsaved, so just-created issue numbers are lost and re-created as duplicates next run); or the issue exists but wasn't fetched, and the push **silently clobbers the remote**, carrying `state` — which can reopen a closed issue. The `UNCHANGED` orphan is worse and unfiled: it appears in **no** plan section at all.

**Tasks:**
1. [ ] Add `ClassKind.ORPHAN_LOCAL`, emitted for both the changed and unchanged sub-cases, carrying `local_changed`
2. [ ] `resolve`: emit an `Orphan` record into a new `ResolveResult.orphans` — never a `PushAction`, never a `CreateAction`
3. [ ] Preserve `classify`'s "each task and each issue appears exactly once" invariant (pinned by `test_classify.py:219-228`)
4. [ ] Mutation-test: delete the orphan branch and confirm the new tests go red

**Acceptance Criteria:**
- [ ] WHEN a local task references an issue absent from the fetched list THEN `classify` SHALL emit `ORPHAN_LOCAL` and `resolve` SHALL NOT emit a push
- [ ] WHEN an orphaned task has no local edit THEN it SHALL still be surfaced, not silently omitted
- [ ] `test_classify.py:219-228` passes unchanged

---

#### 4.2 `SyncPlan.orphans`: surface them, and count them in `is_empty()`
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #181
**Depends On:** 4.1
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/src/task_sync/reconcile/plan.py` (modify)
- `plugins/personal-plugin/tools/task-sync/tests/test_plan.py` (modify)

**Description:**
Additive key in `to_dict()`, a summary line, and inclusion in `is_empty()`. Omitting the `is_empty()` term recreates the `skipped_adopts` bug exactly — an orphan-only plan would report "already in sync".

**Tasks:**
1. [ ] Add `orphans` to `SyncPlan`, `to_dict()`, `summarize_plan`, and `is_empty()`
2. [ ] Mutation-test the `is_empty()` term specifically

**Acceptance Criteria:**
- [ ] WHEN a plan contains only orphans THEN `is_empty()` SHALL return False and the summary SHALL name the affected issue numbers
- [ ] Existing SKILL parsing of `creates`/`pushes`/`pulls`/`conflicts`/`skipped_adopts` is unaffected

---

#### 4.3 Orphan decisions: keep or drop, validated up front
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #181
**Depends On:** 4.2
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/src/task_sync/reconcile/apply.py` (modify)
- `plugins/personal-plugin/tools/task-sync/src/task_sync/__main__.py` (modify)
- `plugins/personal-plugin/skills/task-sync/SKILL.md` (modify)
- `plugins/personal-plugin/skills/task-sync/references/sync-semantics.md` (modify)

**Description:**
Orphan ids and conflict ids are disjoint by construction (a conflict requires `issue is not None`), so the existing flat decisions map can carry both. `keep` clears `issue_number` and the synced base so the next run re-creates via the tested `creates` path; `drop` removes the task. Validate every id and value **before** mutating anything (D36).

**Tasks:**
1. [ ] Extend the decision handling for `keep`/`drop`, validated up front
2. [ ] Ensure a `drop` cannot run before the create/push loops (`by_id` lookups assume the task survives)
3. [ ] Render an Orphans section in the SKILL, prompting per orphan; undecided orphans resurface next run
4. [ ] Derive tests from the real disposition constant and include an out-of-set value

**Acceptance Criteria:**
- [ ] WHEN an orphan decision file contains an unknown id or value THEN the whole batch SHALL be rejected with nothing written
- [ ] WHEN an orphan is left undecided THEN it SHALL remain untouched and reappear in the next plan

---

#### 4.4 Delete the unreachable re-create branch and correct the docs
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #181
**Depends On:** 4.1
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/src/task_sync/reconcile/resolve.py` (modify)
- `plugins/personal-plugin/skills/task-sync/references/sync-semantics.md` (modify)

**Description:**
`resolve.py:212-217` is unreachable from the pipeline — `classify` emits `CHANGED_LOCAL` only where `issue_number` is non-`None`. Its comment ("An orphan (issue vanished)") is factually wrong and is what keeps it looking alive.

**Tasks:**
1. [ ] Delete the branch and its comment; keep the hand-built-`Classification` test or delete it with the branch
2. [ ] Correct `sync-semantics.md:23-30`

**Acceptance Criteria:**
- [ ] No unreachable branch remains in `resolve.py`; coverage does not drop

---

#### 4.5 GitHub `list_issues`: fail loud on saturation
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #182
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/src/task_sync/providers/github.py` (modify)
- `plugins/personal-plugin/tools/task-sync/tests/test_provider_github.py` (modify)

**Description:**
`--limit 1000` with no saturation check. Because `classify` treats the fetched list as authoritative, truncation manufactures the #181 orphan condition en masse. Step 1 keeps `gh issue list` and raises when `len(data) >= limit` — fail-loud satisfies "never silent", is trivially mutation-testable, and changes no argv shape. `gh label list --limit 1000` at `:215` has the same defect and is unfiled.

**Tasks:**
1. [ ] Raise a `RuntimeError` naming the truncation when the fetch saturates
2. [ ] Apply the same guard to `ensure_labels`
3. [ ] Mutation-test: delete the guard, confirm a saturated-fetch test goes red

**Acceptance Criteria:**
- [ ] WHEN the issue fetch returns exactly the limit THEN the tool SHALL abort before any write

---

#### 4.6 GitHub `list_issues`: real pagination via REST
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #182
**Depends On:** 4.5
**Files Affected:**
- `plugins/personal-plugin/tools/task-sync/src/task_sync/providers/github.py` (modify)
- `plugins/personal-plugin/tools/task-sync/tests/test_provider_github.py` (modify)

**Description:**
Three traps in the obvious fix. `--slurp` does not exist on the verified `gh` 2.45.0 baseline, so `gh api --paginate` emits **concatenated** JSON arrays that `json.loads` rejects — needs `json.JSONDecoder().raw_decode` or `--jq '.[]'` + JSONL. REST `/repos/{}/issues` **includes pull requests**, which would adopt every open PR as a task. And REST is snake_case while `_normalize`/`_view` are keyed to `gh --json` camelCase — a second normalizer would be #208-class drift, so use one field-alias layer.

**Tasks:**
1. [ ] Implement the paginated REST fetch with a `raw_decode` loop
2. [ ] Filter `"pull_request" not in item`
3. [ ] Route both shapes through one alias layer, not two normalizers
4. [ ] Fixture must be **two `[...]` blobs concatenated with no separator** — a pre-merged array would prove the fix while the real `gh` still crashes (#212's failure mode verbatim)

**Acceptance Criteria:**
- [ ] WHEN a repo has more issues than one page THEN all are fetched
- [ ] WHEN the repo has open PRs THEN none is adopted as a task
- [ ] Gitea's `_PAGE_SIZE` loop and `type: issues` filter remain unchanged

---

### Phase 4 Testing Requirements

- [ ] New guards mutation-tested individually (orphan branch, `is_empty()` term, saturation guard)
- [ ] Orphan decision tests derived from the real constant, with an out-of-set value
- [ ] Pagination fixture uses concatenated blobs
- [ ] Coverage ≥90% maintained

### Phase 4 Completion Checklist

- [ ] All work items complete
- [ ] Full task-sync suite green on both OSes
- [ ] `tasks.json` backed up before any live verification (gitignored, not git-recoverable)

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests | `cd plugins/personal-plugin/tools/task-sync && PYTHONPATH=src python -m pytest tests/ -q` | Exit code 0 |
| Coverage | `cd plugins/personal-plugin/tools/task-sync && PYTHONPATH=src python -m pytest --cov=src --cov-fail-under=90 -q` | ≥90% |
| Lint | `uvx ruff@0.14.10 check plugins/personal-plugin/tools/task-sync/src plugins/personal-plugin/tools/task-sync/tests` | Exit code 0 |
| Types | `cd plugins/personal-plugin/tools/task-sync && mypy src/ --ignore-missing-imports` | Exit code 0 |

<!-- END DOD -->

---

## Phase 5: Generator and Harness-Feature Catalog

**Execution Mode:** Sequential

### Goals

Make the documentation layer that teaches skill authoring describe the harness that actually exists — correcting semantics rather than deleting capability — and stop the generator propagating stale model IDs.

### Work Items

#### 5.1 ADR-0012 and the `paths:` semantics inversion
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #202
**Depends On:** None
**Files Affected:**
- `docs/adr/0012-artifact-derived-documentation.md` (create)
- `plugins/personal-plugin/references/patterns/advanced-features.md` (modify)
- `plugins/personal-plugin/references/common-patterns.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/skills/{spark-audit,jetson-audit,spark-recon,jetson-recon,security-analysis}/SKILL.md` (modify)

**Description:**
The docs teach `paths:` as an *event trigger* ("auto-activates when the user opens or saves a matching file"). The harness implements a *load gate*: "the skill only loads when **the model** touches matching files." Every loop guard built on the doc's reading is dead code. Worse and unfiled: all four fleet skills pair `paths:` with `disable-model-invocation: true` — since `paths:` gates on model file access and the flag forbids model invocation entirely, **the pairing is self-cancelling**. ADR-0012 generalizes the root cause shared by #193, #194, #196, #202 and #218: documentation of a bundled artifact must be derived from or verified against the artifact.

**Tasks:**
1. [ ] Write ADR-0012 (Accepted), including the rule that a freshness claim requires a mechanism or must be deleted
2. [ ] Correct `paths:` semantics in all three teaching sites
3. [ ] Remove the dead loop guards from the five skills carrying them
4. [ ] Record the self-cancelling `paths:` + `disable-model-invocation` pairing and resolve it per skill

**Acceptance Criteria:**
- [ ] WHEN a reader consults any `paths:` documentation THEN it SHALL describe a model-access load gate
- [ ] No skill retains a loop guard for an event that cannot occur
- [ ] ADR-0012 exists with status Accepted

---

#### 5.2 `hooks:` frontmatter: the event-record shape
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #202
**Depends On:** 5.1
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md` (modify)
- `plugins/personal-plugin/references/patterns/advanced-features.md` (modify)
- `plugins/personal-plugin/references/templates/skill.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)

**Description:**
The `hooks: pre:/post:` shape taught in four places is invalid. The value is a record keyed by hook event → array of matchers. A string under `pre:`/`post:` fails validation and emits `Invalid hooks in plugin skill '<name>'`. Same defect class as the three hook recipes in Phase 3.

**Tasks:**
1. [ ] Rewrite all four sites to the event-record form with the valid event names
2. [ ] Cross-reference the working `hooks/hooks.json`

**Acceptance Criteria:**
- [ ] WHEN a skill author copies the documented `hooks:` shape THEN it SHALL load without a validation error

---

#### 5.3 Delete the two fictional keys
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #202
**Depends On:** 5.1
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md` (modify)
- `plugins/personal-plugin/references/patterns/advanced-features.md` (modify)
- `plugins/personal-plugin/references/templates/skill.md` (modify)
- `plugins/personal-plugin/references/new-skill-examples.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)

**Description:**
`isolation: worktree` is **agent** frontmatter, not skill — and the skill schema is `.strict()`, so an unknown key is **rejected**, not ignored. `$CLAUDE_CONTEXT` does not exist as a template variable (only the unrelated `CLAUDE_CONTEXT_COLLAPSE` env vars do); `new-skill-examples.md:128` is a worked example that silently degrades.

**Tasks:**
1. [ ] Remove `isolation:` from skill-frontmatter documentation; relocate to an agent-frontmatter note if kept at all
2. [ ] Delete `$CLAUDE_CONTEXT` and its worked example from all five sites

**Acceptance Criteria:**
- [ ] WHEN a generated skill's frontmatter is validated THEN it SHALL contain no key the strict schema rejects
- [ ] No documented template variable expands to nothing

---

#### 5.4 Frontmatter enum corrections: `agent:`, `effort`, and the flag definition
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #202, #192 (row 8), #201, #199 (partial)
**Depends On:** 5.1
**Files Affected:**
- `plugins/personal-plugin/references/common-patterns.md` (modify)
- `plugins/personal-plugin/references/patterns/advanced-features.md` (modify)
- `plugins/personal-plugin/references/templates/skill.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/commands/scaffold-plugin.md` (modify)
- `CLAUDE.md` (modify)

**Description:**
Four enum defects in one pass, all in the same files. `agent:` — built-ins are `Explore`, `Plan`, `general-purpose`; `Think` and `Code` are fictional, and unknown types **raise** rather than falling back silently as `common-patterns.md:156` claims. This also resolves #192's row 8 (`scaffold-plugin.md:194`'s `# agent: explorer` is the lone outlier against five correct usages). `effort` — the documented enum omits **`xhigh`**, which is Claude Code's own default and the recommended level for agentic work. `disable-model-invocation` — misdefined as "no LLM call" in two of three sites; `CLAUDE.md:116` is the only correct rendering.

**Tasks:**
1. [ ] `agent:` enum → `Explore | Plan | general-purpose | <named custom agent>`; correct the silent-fallback claim
2. [ ] `scaffold-plugin.md:194`: `explorer` → `Explore`
3. [ ] Add `xhigh` to the `effort` enum in `CLAUDE.md:105` and every generator site
4. [ ] Correct the flag definition at `new-skill.md:287` and `templates/skill.md:7` to match `CLAUDE.md:116`

**Acceptance Criteria:**
- [ ] WHEN a generated skill declares `agent:` THEN the value SHALL be one the harness resolves
- [ ] The documented `effort` enum matches the harness enum exactly
- [ ] All three `disable-model-invocation` definitions agree

**Notes:**
Only the `effort` **enum** half of #199 lands here; the 31-component `effort:` sweep is deferred to the follow-on plan. Do not close #199 on this phase.

---

#### 5.5 `/schedule`: keep the integration, rewrite the invocations
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #202
**Depends On:** 5.1
**Files Affected:**
- `plugins/personal-plugin/skills/{spark-audit,spark-recon,jetson-audit,jetson-recon}/SKILL.md` (modify)

**Description:**
**#202 asserts** `/schedule` does not exist and proposes replacing it with `create_trigger`. **The reverse is true**: `/schedule` is a currently-shipping built-in skill; `create_trigger` appears zero times in the harness. What *is* fictional is the invocation syntax — `/schedule create --name … --cron …` — because `/schedule` is a natural-language skill, not a flag CLI.

**Tasks:**
1. [ ] Keep all four `/schedule` integration sections
2. [ ] Rewrite the eight invocation blocks as natural-language requests
3. [ ] Do **not** introduce `create_trigger`

**Acceptance Criteria:**
- [ ] WHEN a user follows a scheduling section THEN the described invocation SHALL match how `/schedule` is actually invoked

---

#### 5.6 Generator templates: tier aliases, not pinned IDs
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #197 (class a)
**Depends On:** 5.4
**Files Affected:**
- `plugins/personal-plugin/references/templates/skill.md` (modify)
- `plugins/personal-plugin/commands/new-skill.md` (modify)
- `plugins/personal-plugin/references/common-patterns.md` (modify)
- `plugins/personal-plugin/references/patterns/advanced-features.md` (modify)
- `plugins/personal-plugin/deprecated/new-command.md` (modify)

**Description:**
Six sites emit pinned model IDs into every generated skill, including one **retired** (`claude-haiku-3-5`) and one that **never existed** (`claude-haiku-4`). `common-patterns.md:170` also hedges ("pin to a family name if you want automatic upgrade") on exactly what ADR-0005 mandates.

**Tasks:**
1. [ ] Replace all pinned IDs with tier aliases plus an ADR-0005 pointer
2. [ ] Replace the `:170` hedge with the mandate
3. [ ] Update the stale currency stamp at `new-skill.md:282`

**Acceptance Criteria:**
- [ ] WHEN `/new-skill` generates a skill THEN any emitted `model:` SHALL be a tier alias
- [ ] No retired or nonexistent model ID remains in the generator layer

---

### Phase 5 Testing Requirements

- [ ] Every documented frontmatter key verified against the harness schema
- [ ] A skill generated by `/new-skill` validates under `--strict`
- [ ] No documented template variable expands to nothing

### Phase 5 Completion Checklist

- [ ] All work items complete
- [ ] ADR-0012 Accepted
- [ ] `/new-skill` end-to-end produces a valid, loadable skill

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Plugin validation | `claude plugin validate --strict ./plugins/personal-plugin` | Exit code 0 |
| Injection linter | `python3 scripts/check_injections.py` | Exit code 0 |
| Markdown lint | `npx markdownlint-cli2 "plugins/**/*.md" "docs/**/*.md" "CLAUDE.md"` | Exit code 0 |
| Pre-commit | `bash scripts/pre-commit` | Exit code 0 |

<!-- END DOD -->

---

## Phase 6: ADR-0005 Enforcement and Remaining Model-ID Instances

**Execution Mode:** Sequential

### Goals

Make a pinned model ID in agent frontmatter impossible to merge, and clear the remaining stale references.

### Work Items

#### 6.1 CI gate: tier-alias enforcement as a step
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #204
**Depends On:** None
**Files Affected:**
- `scripts/check_agent_models.py` (create)
- `.github/workflows/validate.yml` (modify)

**Description:**
Both frontmatter validators enumerate `commands/` and `skills/` only; `agents/` was never added, and `.claude/agents/` lives outside `plugins/` so no job walks it. All 13 agent files are **already compliant** (`haiku`/`sonnet`/`opus`/`inherit`×10), so a correctly-scoped gate is **green on day one**.

**Tasks:**
1. [ ] Implement `scripts/check_agent_models.py` — stdlib only (the `plugin-validate` job installs no Python, so parse the frontmatter block with `re`, not `yaml`)
2. [ ] Scope to `.claude/agents/*.md` and `plugins/*/agents/*.md`
3. [ ] **Negative-test**: set one agent to a pinned ID, confirm exit 1; restore, confirm exit 0
4. [ ] Add as a **step** after `:318` in `Validate Plugins (official CLI)`, following the `check_eval_mapping.py` / `update-readme.py --check` precedents

**Acceptance Criteria:**
- [ ] WHEN an agent declares a pinned model ID THEN CI SHALL fail naming the file and value
- [ ] WHEN run against the current tree THEN the gate SHALL exit 0
- [ ] The required-check name is unchanged (D28)
- [ ] The gate does **not** flag pinned IDs in Python tools, which ADR-0005 explicitly permits

**Notes:**
Scope creep to a repo-wide pinned-ID grep would fire on the 8 legal `claude-sonnet-5` defaults, redden `main`'s own push build, and **deadlock every subsequent PR**. This is the single highest-risk item in the plan.

---

#### 6.2 pre-commit: Check 5
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #204
**Depends On:** 6.1
**Files Affected:**
- `scripts/pre-commit` (modify)

**Description:**
`STAGED_FILES` at `:33` must **not** be widened — the whole `:39-184` block (name/dir-match rules) would then misfire on flat agent files. Add a self-contained block between `:207` and `:209`, outside the `fi` at `:184`, so it runs on an agent-only commit.

**Tasks:**
1. [ ] Add the block with its own `git diff --cached` list and regex
2. [ ] Increment `ERRORS` in the main shell (not a subshell)
3. [ ] Add a tip line to the failure block at `:223-230`

**Acceptance Criteria:**
- [ ] WHEN a pinned agent model is staged THEN the commit SHALL be blocked
- [ ] WHEN no agent file is staged THEN the check SHALL be skipped without error

---

#### 6.3 README: stop contradicting ADR-0005
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #204
**Depends On:** None
**Files Affected:**
- `README.md` (modify)

**Description:**
`:179-180` reads "Model pinned in frontmatter" — the exact practice ADR-0005 rejects. The corrected twin already exists at `CLAUDE.md:165-173`. Safe to hand-edit: `update-readme.py` rewrites only command/skill tables and prose counts, and the line sits in a hand-maintained fence.

**Tasks:**
1. [ ] Replace with the CLAUDE.md wording
2. [ ] Confirm `update-readme.py --check` still exits 0

**Acceptance Criteria:**
- [ ] README no longer teaches a practice the gate rejects

---

#### 6.4 Remaining stale model references: prose and code
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #197 (classes b, c)
**Depends On:** None
**Files Affected:**
- `CONTRIBUTING.md` (modify)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/image_evaluator.py` (modify)
- `plugins/personal-plugin/tools/visual-explainer/tests/test_prompt_generator.py` (modify)

**Tasks:**
1. [ ] `CONTRIBUTING.md:389`: use the generic `Co-Authored-By: Claude` form the two in-repo templates already use
2. [ ] `image_evaluator.py:36`: the "5x cheaper than Opus" comment is the stated justification for the tier choice; the real ratio is ~1.7x
3. [ ] `test_prompt_generator.py:57`: retired dated ID `claude-opus-4-20250514` → `claude-opus-5` (the only retired ID left in executable code)
4. [ ] Do **not** change `DEFAULT_MODEL = "claude-sonnet-5"` — ADR-0005 permits pinned IDs in Python tools

**Acceptance Criteria:**
- [ ] No retired or nonexistent Claude model ID remains outside `docs/`, `reports/`, `LAB_NOTEBOOK.md`, and `CHANGELOG.md`

---

#### 6.5 `develop-image-prompt`: stop templating SD1.x parameters into user output
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #197
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/commands/develop-image-prompt.md` (modify)

**Description:**
`:242-256` and `:326-339` template DALL-E 3 / Stable Diffusion 1.x parameter blocks (`DPM++ 2M Karras`, `CFG Scale: 7`) into every generated prompt file. This is a generator in disguise — the stale block is copied into user output, making it the highest-value non-Claude item in #197.

**Tasks:**
1. [ ] Replace the pinned parameter blocks with model-agnostic guidance
2. [ ] Keep the structure; only the generation parameters are stale

**Acceptance Criteria:**
- [ ] WHEN a prompt file is generated THEN it SHALL NOT carry SD1.x-era sampler parameters as current guidance

---

### Phase 6 Testing Requirements

- [ ] Both gates negative-tested in both directions before wiring
- [ ] Existing 22 required checks unchanged in name and count

### Phase 6 Completion Checklist

- [ ] All work items complete
- [ ] Branch-protection required checks unchanged
- [ ] `update-readme.py --check` exits 0

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Agent-model gate | `python3 scripts/check_agent_models.py` | Exit code 0 |
| Gate negative test | `python3 scripts/check_agent_models.py --self-test` | Exit code 0 (asserts a pinned ID exits 1) |
| README sync | `python3 scripts/update-readme.py --check` | Exit code 0 |
| Pre-commit | `bash scripts/pre-commit` | Exit code 0 |
| visual-explainer tests | `cd plugins/personal-plugin/tools/visual-explainer && PYTHONPATH=src python -m pytest tests/ -q` | Exit code 0 |

<!-- END DOD -->

---

## Phase 7: `allowed-tools` Grant Sets

**Execution Mode:** Sequential

### Goals

Make every component's tool grant match the workflow its body documents — including removing one grant that should never have existed.

### Work Items

#### 7.1 Resolve `Agent` vs `Task` and correct eight components
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #192
**Depends On:** Phase 5
**Files Affected:**
- `plugins/personal-plugin/skills/explain-project/SKILL.md` (modify)
- `plugins/personal-plugin/skills/accessibility-annotator/SKILL.md` (modify)
- `plugins/personal-plugin/skills/brain-entry/SKILL.md` (modify)
- `plugins/personal-plugin/skills/fleet-health/SKILL.md` (modify)
- `plugins/personal-plugin/commands/test-project.md` (modify)
- `plugins/personal-plugin/commands/create-plan.md` (modify)

**Description:**
The repo uses `Task` and `Agent` inconsistently for the same dispatch tool. Decide once (`Agent` — `arch-review`'s precedent and the first name in the harness's identity check) and apply. Note row 1's compound sub-claim is **wrong**: `Bash(head:*)` *is* granted to `explain-project` (added in `c093904` for that exact pipe) — only the `Write` gap at `:369` and an unreported `Agent` gap are real.

**Tasks:**
1. [ ] Record the `Agent` decision in the Decision Log
2. [ ] `explain-project`: add `Write` and `Agent` (two `context: fork` blocks at `:135-139`, `:328-332`)
3. [ ] `accessibility-annotator`: add `Glob`, `Grep`
4. [ ] `test-project`: `Task` → `Agent` plus the `TaskCreate/Update/List/Output` family, matching `implement-plan.md:5`
5. [ ] `create-plan`: add `Bash(find:*)`, `Bash(head:*)`
6. [ ] `brain-entry`: add `Bash(tail/sed/echo/python3:*)`; `fleet-health`: shell job control
7. [ ] Exclude D39's three carve-outs entirely

**Acceptance Criteria:**
- [ ] WHEN any component executes its documented workflow THEN every tool it uses SHALL be granted
- [ ] `security-analysis`, `leak-risk-audit`, and `arch-review` retain unscoped `Bash` with their justification comments

---

#### 7.2 `spark-recon`: remove a vestigial grant that contradicts its own trust boundary
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #192 (row 7, reframed)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/spark-recon/SKILL.md` (modify)

**Description:**
This row is inverted in the issue: `spark-recon` does not lack grants, it has **excess** ones. Its body contains no `ssh` or `curl` call — the only occurrences are frontmatter and two invariant sentences stating "this skill runs no SSH/Bash commands at all". The shared reference it delegates to has none either. The grant is fully vestigial, and material because the skill ingests untrusted web content.

**Tasks:**
1. [ ] Delete `Bash(ssh:*)` and `Bash(curl:*)`
2. [ ] Verify the stated invariant now holds structurally

**Acceptance Criteria:**
- [ ] `spark-recon`'s grants match its documented trust boundary

---

#### 7.3 `prime`: grant the dispatch it mandates
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #191
**Depends On:** 7.1, Phase 1
**Files Affected:**
- `plugins/personal-plugin/skills/prime/SKILL.md` (modify)

**Description:**
`prime` mandates `context: fork` / `agent: Explore` dispatch in Phases 1/3/5 while granting neither `Agent` nor `Task`. A second, unfiled gap on the same line: `Bash(git:*)` cannot match its own Phase 2 compounds (`:62,:63,:64,:67` all pipe into `head`/`wc`). Since prime's injections are **inert**, Bash is the only way those values can be obtained.

**Tasks:**
1. [ ] Add `Agent` (the token decided in 7.1)
2. [ ] Add `Bash(head:*)`, `Bash(wc:*)` — do **not** grant unscoped `Bash`, which would void the read-only guarantee at `:13`
3. [ ] Correct `:59`'s false claim that Phase 2 values are "pre-loaded via dynamic context injection"
4. [ ] State that Phases 1/3/5 dispatch **concurrently**, using `arch-review:89`'s house wording
5. [ ] Do **not** convert `:60-68` to the live injection form — that would switch on 7 dead executions (ADR-0011)

**Acceptance Criteria:**
- [ ] WHEN `prime` reaches Phase 1 THEN it SHALL be able to dispatch `agent: Explore` without a denial
- [ ] `prime` remains read-only
- [ ] `:343`'s non-git path, which currently works, still works

---

#### 7.4 AskUserQuestion: convert the two shared upstreams first
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #203
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/references/patterns/workflow.md` (modify)
- `plugins/bpmn-plugin/references/clarification-patterns.md` (modify)

**Description:**
`workflow.md:35-48` is the resume/fresh/abort menu that both `ask-questions` and `finish-document` cite; `clarification-patterns.md` carries **24** hand-rolled menu blocks, not the single duplicate the issue implies. Converting consumers while leaving these leaves the anachronism intact and the docs contradicting each other. The native Skip button and free-text box absorb every `[D] Custom` / `[S] Skip` slot, freeing all four option slots for real answers.

**Tasks:**
1. [ ] Convert `workflow.md`'s R/S/A menu
2. [ ] Convert all 24 blocks in `clarification-patterns.md`
3. [ ] Do **not** add `None`/`Other` options — the harness supplies both

**Acceptance Criteria:**
- [ ] No hand-rolled option menu remains in either shared upstream
- [ ] Every converted question has 2–4 options

---

#### 7.5 AskUserQuestion: convert the six consumers
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #203
**Depends On:** 7.4
**Files Affected:**
- `plugins/personal-plugin/commands/ask-questions.md` (modify)
- `plugins/personal-plugin/commands/finish-document.md` (modify)
- `plugins/personal-plugin/skills/spec-to-prototype/SKILL.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (modify)
- `plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md` (modify)

**Description:**
None of the six currently grants `AskUserQuestion`. `spec-to-prototype` is the best fit (its `:62` "one at a time" contradicts `:68`'s "3-5 questions is typical" in the same section); `visual-explainer`'s two menus are already exactly AskUserQuestion-shaped. `finish-document`'s `--auto` mode and its own Session Commands are local and must survive.

**Tasks:**
1. [ ] Add `AskUserQuestion` to all six `allowed-tools`
2. [ ] Convert each menu, keeping the text protocol as a documented fallback where session commands (`save`, `go to N`) can't be expressed
3. [ ] `spec-to-prototype`: batch Q1–4 in one call; edit the diagram label at `:30` in lockstep
4. [ ] Leave `references/templates/interactive.md` as-is — its ONE-AT-A-TIME rule is a deliberate interview contract

**Acceptance Criteria:**
- [ ] WHEN a converted component asks a multiple-choice question THEN it SHALL use the native tool
- [ ] `--auto` mode still auto-selects without prompting

---

#### 7.6 `bpmn-generator`: drop the simulated REPL
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #203
**Depends On:** 7.5
**Files Affected:**
- `plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md` (modify)

**Description:**
`:186-219` hand-rolls a REPL (`help`/`status`/`back`/`skip`/`quit`). `skip` and `quit` are native; `status` is redundant under a native UI; `back` has no equivalent and is not worth 34 lines of interpreter. The file is **494/500 lines** — deleting this block plus deduplicating `:106-123` against `clarification-patterns.md` creates the headroom the conversion needs. Net negative diff.

**Tasks:**
1. [ ] Delete `:186-219`
2. [ ] Deduplicate `:106-123` against the shared reference
3. [ ] Confirm the body is comfortably under 500 lines

**Acceptance Criteria:**
- [ ] No simulated command interpreter remains
- [ ] `bpmn-generator/SKILL.md` is under the 500-line budget

---

### Phase 7 Testing Requirements

- [ ] Each converted component's documented workflow executes without a permission prompt
- [ ] D39 carve-outs untouched

### Phase 7 Completion Checklist

- [ ] All work items complete
- [ ] `Agent`/`Task` decision recorded in the Decision Log
- [ ] All three plugins validate `--strict`

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Plugin validation | `for p in personal-plugin bpmn-plugin slide-gen; do claude plugin validate --strict ./plugins/$p \|\| exit 1; done` | Exit code 0 |
| Injection linter | `python3 scripts/check_injections.py` | Exit code 0 |
| Body-size budget | `awk 'END{if (NR>=500) exit 1}' plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md` | Exit code 0 |
| Markdown lint | `npx markdownlint-cli2 "plugins/**/*.md"` | Exit code 0 |

<!-- END DOD -->

---

## Phase 8: Trigger Metadata and Eval Re-baseline

**Execution Mode:** Sequential

### Goals

Resolve the contradiction between `disable-model-invocation` and eleven skills' trigger prose, then re-baseline the evals that encode it.

### Work Items

#### 8.1 D40-protected skills: rewrite descriptions, keep the flag
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #201
**Depends On:** Phase 5
**Files Affected:**
- `plugins/personal-plugin/skills/spark-recon/SKILL.md` (modify)
- `plugins/personal-plugin/skills/jetson-recon/SKILL.md` (modify)

**Description:**
`disable-model-invocation: true` removes the description from session context, so trigger prose in these descriptions is unreachable. Both are D40-protected (`jetson-recon` combines untrusted WebFetch/WebSearch with a live SSH read into a passwordless-sudo account) and the flag must stay. Their descriptions are *entirely* trigger prose, so stripping leaves nothing — they need rewriting as capability statements, using `arch-review` as the model.

**Tasks:**
1. [ ] Rewrite both descriptions as capability statements
2. [ ] Preserve the Trust Boundary sections verbatim

**Acceptance Criteria:**
- [ ] WHEN either skill's frontmatter is read THEN the description SHALL state capability, not triggers
- [ ] Both retain `disable-model-invocation: true`

---

#### 8.2 Six skills: keep the flag, strip the dead prose
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** #201
**Depends On:** Phase 5
**Files Affected:**
- `plugins/personal-plugin/skills/{unlock,visual-explainer,new-project,release-plugin,archive-project,brain-entry}/SKILL.md` (modify)
- `plugins/personal-plugin/skills/ship/SKILL.md` (modify)

**Description:**
Seven skills (including `ship`, per the approved decision to keep its flag) keep `disable-model-invocation: true` for sound reasons — secrets loading, paid image generation, remote repo creation, irreversible publishing, destructive-adjacent moves, external POST with no gate, and push/merge respectively — and simply lose the unreachable trigger prose. `new-project` also resolves a self-contradiction: `:13` already declares it never runs proactively while `:3` says "Suggest…".

**Tasks:**
1. [ ] Strip "Suggest when…" prose from all seven descriptions, leaving capability statements
2. [ ] Fix `unlock/SKILL.md:169-176`, which shows Claude running `/unlock` automatically — teaching exactly what the flag forbids

**Acceptance Criteria:**
- [ ] No skill carrying the flag also carries trigger prose in its description
- [ ] All seven retain the flag

---

#### 8.3 Two skills: drop the flag, but add a Phase-0 gate first
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** #201
**Depends On:** 8.2
**Files Affected:**
- `plugins/personal-plugin/skills/lab-notebook/SKILL.md` (modify)
- `plugins/personal-plugin/skills/create-wiki/SKILL.md` (modify)
- `evals/skills/description-triggers.eval.md` (modify)

**Description:**
Both have the highest proactive-suggestion value in the set — their triggers ("benchmark work starting", "I keep forgetting…") are ones the user provably cannot self-serve. **But neither has a pre-action confirmation gate**; their "Confirm" steps are post-creation verification. Dropping the flag as a one-line edit would let the model unilaterally create files and inject CLAUDE.md rules. The gate must land in the same change.

**Tasks:**
1. [ ] Add a Phase-0 confirmation gate to each, before any file creation
2. [ ] Remove `disable-model-invocation: true`
3. [ ] Update `description-triggers.eval.md` S13/S14, which currently assert the opposite

**Acceptance Criteria:**
- [ ] WHEN either skill is model-invoked THEN it SHALL confirm before creating any file
- [ ] S13/S14 assert the new contract

---

#### 8.4 Re-baseline the model-sensitive evals
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** #205
**Depends On:** 8.1, 8.2, 8.3
**Files Affected:**
- `evals/skills/description-triggers.eval.md` (modify)
- `evals/commands/assess-document.eval.md` (modify)

**Description:**
S11–S14 each carry a **Should** criterion requiring the model to verbally suggest a skill based on documented trigger prose the flag has deleted from its context — unsatisfiable as written, and the same defect #201 describes, encoded into the eval meant to guard it. Separately, `assess-document.eval.md` asserts absolute score bands (`:17-18`, `:29`, `:52`, `:61`) as **Must** criteria; the file already contains the correct relative form at `:140`. There is **no baseline artifact** in the repo — "re-baseline" means editing the eval spec text. Item 3 of #205 (`research-topic.eval.md:34`) is already resolved by #189 and needs no work.

**Tasks:**
1. [ ] Rewrite S11–S14's unsatisfiable Should criteria
2. [ ] Convert `assess-document`'s absolute bands to the relative form already present at `:140`
3. [ ] Run the 14 `description-triggers` scenarios under Opus 5 and record results out-of-band
4. [ ] Close #205 item 3 as already-fixed

**Acceptance Criteria:**
- [ ] No eval criterion depends on prose the harness has removed from context
- [ ] `check_eval_mapping.py` still passes (scenario/Must-block/rubric gates)

**Notes:**
ADR-0009/D32 stands — this stays human-run; CI has zero secrets.

---

### Phase 8 Testing Requirements

- [ ] Eval structural linter passes after every edit
- [ ] Both newly-invocable skills verified to gate before writing

### Phase 8 Completion Checklist

- [ ] All work items complete
- [ ] `description-triggers` scenarios run under Opus 5
- [ ] No skill's dispatch metadata contradicts its flag

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Eval linter | `python3 scripts/check_eval_mapping.py` | Exit code 0 |
| Plugin validation | `claude plugin validate --strict ./plugins/personal-plugin` | Exit code 0 |
| Description budget | `python3 -c "import pathlib,re,sys; [sys.exit(1) for f in pathlib.Path('plugins').rglob('SKILL.md') if len((re.search(r'^description:\s*(.+)$', f.read_text(), re.M) or [''])[0]) > 1024]"` | Exit code 0 |
| Markdown lint | `npx markdownlint-cli2 "plugins/**/*.md" "evals/**/*.md"` | Exit code 0 |

<!-- END DOD -->

---

## Parallel Work Opportunities

| Phases | Can run concurrently | Rationale |
|--------|---------------------|-----------|
| 2, 3, 4 | Yes — with each other and with 1 | Zero shared files; three different plugins/tools |
| 2.1–2.3 vs 2.4–2.5 | Yes | bpmn-plugin vs personal-plugin |
| 3.1 vs 3.2–3.4 | Yes | hook recipes vs slide-gen |
| 6.3, 6.4, 6.5 | Yes | Independent single-file edits |
| 1, 5, 7, 8 | **No** | The critical path — each corrects an enumeration the next applies |

---

## Risk Mitigation

<!-- BEGIN TABLES -->

| Risk | Phase/Item | Likelihood | Impact | Mitigation | Status |
|------|-----------|-----------|--------|------------|--------|
| #204 gate scope creeps to a repo-wide pinned-ID grep, reddening `main` and deadlocking all PRs | 6.1 | Medium | **Critical** | Scope to agent frontmatter only; negative-test both directions; ADR-0005 explicitly permits pinned IDs in Python tools | Open |
| Someone "tidies" `prime`'s backticks, switching on 7 dead executions under a grant that rejects 4 | 7.3 | Medium | High | Phase 1 lands ADR-0011 first; 7.3 carries an explicit do-not instruction | Open |
| 3.3's slide-removal fix claimed working without execution | 3.3 | Medium | High | Acceptance criterion requires execution against the real `.pptx`; current text already carries a reliability claim execution disproves | Open |
| 4.6's mock proves `--paginate` works while real `gh` 2.45 crashes | 4.6 | Medium | High | Fixture must be two concatenated blobs, not a pre-merged array (#212's mode verbatim) | Open |
| `SyncPlan.orphans` omitted from `is_empty()` → orphan-only plan reports "already in sync" | 4.2 | Medium | High | Explicit acceptance criterion + dedicated mutation test | Open |
| Phase 5 deletes a working frontmatter key as "unverified" | 5.3 | Medium | High | Six of eight keys verified real against the harness schema; only `isolation:` and `$CLAUDE_CONTEXT` are deleted | Open |
| 8.3 drops a flag without its gate, making file creation model-triggerable | 8.3 | Low | High | Gate and flag removal are one work item, not two | Open |
| A new CI **job** instead of a step deadlocks merges | 1.6, 6.1 | Low | Critical | Both items specify "step"; D28 cited inline | Open |
| Rewording plan-template Rule 17 breaks `/validate-plugin`'s literal keyword check | Deferred (#198) | — | — | Not in this plan; recorded for the follow-on | Deferred |

<!-- END TABLES -->

---

## Unknowns Register

<!-- BEGIN TABLES -->

| ID | Unknown | Severity | Affects | Resolution Strategy | Status |
|----|---------|----------|---------|---------------------|--------|
| U1 | Does `$PWD` work as a template variable? Documented at `common-patterns.md:287`; 3 binary hits with no schema context | Low | 5.3 | Live probe in a scratch skill; delete if unverified | Open |
| U2 | Do `context: fork` subagents draw tool permissions from skill frontmatter or session settings? | Medium | 7.1, 7.3 | Live probe before finalizing grant sets; affects whether grant fixes are load-bearing or cosmetic | Open |
| U3 | Exact python-pptx version contract for `_sldIdLst` (private attribute) | Medium | 3.3 | Pin the version in Prerequisites; verify against the installed 1.0.2 | Open |
| U4 | Does the harness surface a distinguishable error when a `.strict()` skill schema rejects a key, or does the skill silently not load? | Medium | 5.3 | Probe with a deliberately-bad key; determines whether 5.3 is a crash fix or a hygiene fix | Open |
| U5 | Whether `agent: general-purpose` is valid in *skill* frontmatter or only in the Agent tool | Low | 5.4 | Verify against the harness enum before publishing the corrected vocabulary | Open |

<!-- END TABLES -->

---

## Success Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Skills/commands producing silently wrong output | 3 (bpmn-to-drawio, build-cfa-deck, task-sync orphan path) | 0 |
| Live injections in executable surfaces that can abort a skill | 9 (ship 6, clear-prep 3) | 0 unguarded |
| Guards that cannot fire | 5 (ship diff gate, ship remote check, `paths:` loop guards, no ADR-0005 gate, no injection linter) | 0 |
| Documented frontmatter keys contradicted by the harness | 5 (`paths:` semantics, `hooks:` shape, `isolation:`, `$CLAUDE_CONTEXT`, `agent:` enum) | 0 |
| visual-explainer env-var doc coverage | 2/15 (13%) | 15/15 |
| Components whose `allowed-tools` cannot run their documented workflow | 10 | 0 |
| Skills whose description contradicts their dispatch flag | 11 | 0 |
| CI gates enforcing a documented rule | 2 (eval mapping, README sync) | 4 (+ injection linter, + ADR-0005) |

---

## Appendix: Recommendation Traceability

| Issue | Phase(s) | Items | Investigation verdict |
|-------|----------|-------|----------------------|
| #183 | 1 | 1.1, 1.2, 1.4, 1.5, 1.6 | PARTIALLY-WRONG — mechanism right, 50% of locations wrong |
| #190 | 1 | 1.2, 1.3 | ACCURATE headline, 3 defects not 1, plus a second dead gate |
| #193 | 2 | 2.1, 2.2, 2.3 | ACCURATE core, blast radius 9 sites not 3 |
| #196 | 2 | 2.4, 2.5 | ACCURATE, understated (2/15 coverage) |
| #194 | 3 | 3.1 | ACCURATE (all five sub-claims) |
| #195 | 3 | 3.2, 3.3, 3.4 | ACCURATE and UNDERSTATED — both impls broken |
| #181 | 4 | 4.1, 4.2, 4.3, 4.4 | ACCURATE and understated (`UNCHANGED` orphan invisible) |
| #182 | 4 | 4.5, 4.6 | ACCURATE (wording nit: hard cap, not unpaginated) |
| #202 | 5 | 5.1, 5.2, 5.3, 5.4, 5.5 | PARTIALLY-WRONG — remedy inverted; 6 of 8 keys real |
| #197 | 5, 6 | 5.6, 6.4, 6.5 | Upheld with 2 corrections; misses 3 sites |
| #204 | 6 | 6.1, 6.2, 6.3 | FULLY UPHELD |
| #192 | 5, 7 | 5.4, 7.1, 7.2 | PARTIALLY-WRONG — row 1 half-wrong, row 7 inverted, true count 10 |
| #191 | 7 | 7.3 | PARTIALLY-WRONG — primary right, injection sub-claim wrong |
| #203 | 7 | 7.4, 7.5, 7.6 | ACCURATE but INCOMPLETE — ≥7 surfaces, not 4 |
| #201 | 5, 8 | 5.4, 8.1, 8.2, 8.3 | ACCURATE (count of 11 exact) |
| #205 | 8 | 8.4 | PARTIALLY-WRONG — item 3 already fixed by #189 |

**Deferred to the follow-on plan (8 issues, none currently producing wrong output):** #198 (tier routing — 7 files, plus a literal-keyword constraint in `validate-plugin.md`), #199 (the 31-component `effort:` sweep and ultra-plan's ~20 off-by-one phase references; the enum half lands in 5.4), #200 (context-relative thresholds; note Haiku 4.5 is still 200K), #216 (stream the Claude research leg), #218 (delete the unbacked freshness column), #206 (CLAUDE.md inventory drift; its context-economy half is **wrong** — zero budget violations), #210 (bidirectional CHANGELOG backfill, 11+2 versions), #217 (**rewrite the issue first** — 3 of 4 claims are wrong and `/unlock` is blocked by an unrelated `$TROY` defect).

---

## Execution Notes

- One branch + PR + merge per phase; all 22 required checks green before each merge. `main` is PR-protected.
- Log a LAB_NOTEBOOK entry before the first commit of each phase (Rule 11).
- Phases 2, 3, and 4 are independent of the critical path and of each other — run them in parallel with Phase 1 if capacity allows.
- **Two new CI gates land in this plan (1.6, 6.1). Both must be added as STEPS in an existing job** — a new job creates a required check that deadlocks merges (D28/PLAT-012). Both must be negative-tested against deliberately-bad input before wiring (E043).
- Back up `tasks.json` before any live task-sync verification — it is gitignored and therefore not git-recoverable.
- Suggested verification points: stop after Phase 4 (all active harm fixed, shippable) and after Phase 6 (defect classes gated) before proceeding.

---

*Plan generated by `/ultra-plan` on 2026-07-29 from a 24-item backlog investigation (LAB_NOTEBOOK E060). Prior plan archived at `docs/archive/IMPLEMENTATION_PLAN-v11.md`.*
