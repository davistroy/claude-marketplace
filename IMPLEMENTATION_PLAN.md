# Implementation Plan

**Generated:** 2026-07-31
**Completed:** 2026-07-31
**Based On:** `/ultra-plan` over the 5-issue remainder (#200, #199, #238, #216, #198), LAB_NOTEBOOK E067. Phase 1 dispatched **6 parallel Explore agents** clustered by shared code path. **Every cluster returned corrections**, two of them by reading the shipped Claude Code binary rather than inferring from prose. This plan encodes the *investigated* shape of each item, not the filed text — in several cases the investigated shape is the opposite of the filed one. Prior plan (close-the-loop + hygiene, 18/19 COMPLETE) archived at `docs/archive/IMPLEMENTATION_PLAN-v13.md`.
**Total Phases:** 8
**Estimated Total Effort:** ~30 work sites across ~40 files — predominantly markdown behavior-surfaces, plus one new bundled Python tool with an offline fixture suite, one new CI gate, and one backward-compatible config change in `visual-explainer`

---

## Executive Summary

Five issues went into investigation. **A large fraction of their filed content is wrong**, consistent with the 22-of-24 base rate E060 established for this audit lineage. Three findings the fan-out produced are worth more than anything that was filed, and two of them were obtained by reading the harness binary rather than reasoning from documentation.

**1. The `ultrathink` keyword is LIVE, and three in-repo surfaces say it is dead.** Recovered from Claude Code 2.1.220: the matcher is `/\bultrathink\b/i` — case-insensitive, word-bounded — applied to the *expanded body* of every command and skill at load. #199, `LAB_NOTEBOOK.md:1385`, and the E052 audit all assert it is "a no-op on the current model family." A **second live site** exists that no one found: `commands/plan-improvements.md:34` reads `### Phase 1: Deep Codebase Analysis (Ultrathink)`, which fires because the regex is case-insensitive and parentheses are word boundaries. That command therefore carries **two stacking escalations** — `effort: max` in frontmatter *and* a live injection in its body. And `references/templates/planning.md:66` is the mould that mints the pattern into every planning command built from it.

**2. An absent `effort:` field is exactly equivalent to `effort: high`.** Proven through the resolver, the model catalog (`claude-opus-5 → default_effort: "high"`), and the final coercion. Consequence: **all three of #199's `high` recommendations are no-ops**, its priority ordering is inverted (only the `low`/`medium` items produce any behavioural delta, and they are *downgrades* the issue never labels as such), and its headline — "the deepest-reasoning skill has the least effort configuration" — is backwards, because `ultra-plan` runs at default `high` **plus** the live injection.

**3. SKILL.md bodies are not always-loaded.** The harness's own skill-doctor legend reads *"full SKILL.md loads only when it runs."* Only the one-line description sits in the system prompt per turn. So #238's cost model — and the E052 audit finding it inherited — is wrong: extracting 116 lines from `lab-notebook` saves nothing until someone invokes it. `LAB_NOTEBOOK.md:166` (E032) already recorded this as *"a house rule, not a CI gate"* and the repo forgot. The 500-line budget is a real Anthropic **authoring** best-practice that this repo mislabelled as "the official 500-line budget."

**The gate in #238 survives anyway, on an argument the issue never makes.** Both over-budget files crossed the line in **one commit** (`1382a8a`), in a PR whose own plan explicitly verified a line budget for a *different* file. That is a documented-step-with-no-gate defect, which is this repo's most-repeated failure class — it is just not a context-economy defect.

Three scope decisions were taken by the owner before generation and are not re-litigated here: **#216 ships the transport rewrite only, keeping the existing ladder**; **#238 ships as a reframed authoring gate**; **#198 ships Rule 17 only, with no replay experiment**.

Two constraints bind throughout. **ADR-0005 rule 2 forbids naming model generations in prose**, so the Rule 17 fix must be expressed in *task properties*, never "Sonnet 5 is now capable of X" — writing it the other way re-creates the exact staleness class ADR-0005 eliminated. And **documenting the `ultrathink` mechanism inside a skill or command body would trigger it**, the E061 name-don't-render lesson in a new form; only Phase 2's own edits may contain the literal token, and only as deletions.

---

## Plan Overview

Ordering is driven by four constraints established in Phase 2 interaction mapping.

**Constraint 1 — corrected doctrine precedes action.** Phase 1 fixes the three surfaces that assert `ultrathink` is dead and the surfaces that assert bodies are always-loaded. Later phases act on the corrected understanding; landing them first would mean implementers reading a false rationale while editing against it.

**Constraint 2 — `commands/plan-improvements.md` is touched by three issues at four separate line regions** and must be serialized: `:4` and `:34` (Phase 2, #199), `:350` (closed as wrong-as-filed, Phase 5), `:414-421` (Phase 4, #200). Phase 2 lands before Phase 4.

**Constraint 3 — `skills/visual-explainer/SKILL.md` is touched by Phase 5 (env-var docs) and Phase 7 (body extraction).** Phase 5 lands before Phase 7.

**Constraint 4 — the #238 gate must be green on arrival.** Both over-budget files are fixed in the same phase as the gate, ordered before it. A red-on-arrival gate reddens `main`'s own push build, which is the D55 deadlock hazard.

### Phase Summary Table

| Phase | Title | Items | Depends On | Execution Mode |
|---|---|---|---|---|
| 1 | Correct the false doctrine | 2 | None | Sequential |
| 2 | The `ultrathink` set — mould and castings | 3 | Phase 1 | Sequential |
| 3 | Effort calibration — only what changes behaviour | 3 | Phase 1 | Parallel with 4 |
| 4 | Context thresholds that are genuinely stale | 4 | Phase 2 | Sequential |
| 5 | Tier-routing prose + the visual-explainer knob | 3 | None | Parallel with 3/4 |
| 6 | `/research-topic` streaming transport | 5 | None | Sequential |
| 7 | SKILL.md body budget — fix, then gate | 3 | Phase 5 | Sequential |
| 8 | Release and issue reconciliation | 2 | All | Sequential |

### Execution Hints

- **Default model tier:** `sonnet`. Phase 1's investigation found direct evidence that this repo has been *over*-provisioning `opus`: across plans v12 and v13, 15 `sonnet` items touched ≥3 files each (max 10) with **zero** escalations, while two v13 `opus` items were a one-line `fetch-depth: 0` edit and a zero-file verification task. Tiers here are assigned on task properties, not on file count.
- **Phase overrides:** Phase 5 item 5.2 and all of Phases 6 and 7.3 override to `opus` — new bundled tool with 13 enumerated failure modes, a new CI gate requiring negative tests, and a backward-compatible config redesign with a live test surface.
- **Phases 3 and 5 are independent of Phase 2's file** and of each other; run them concurrently with Phase 4 where the orchestrator has capacity.
- **Context budget:** every phase is self-contained. No phase requires reading another phase's output.

---

## Phase 1: Correct the False Doctrine

### Goals

Fix the assertions later phases would otherwise be edited against. Both items are documentation-only and change no runtime behaviour, but both correct facts that this repo has been reasoning from incorrectly for weeks.

### Work Items

#### 1.1 Correct the "`ultrathink` is a no-op" claim in every live surface ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #199 item 1 (inverted)
**Depends On:** None
**Files Affected:**
- `LAB_NOTEBOOK.md` (modify — Decision Log and E067)
- `CLAUDE.md` (modify — add a Verified Operational Rule)

**Description:**

Three in-repo surfaces assert that the bare keyword at `skills/ultra-plan/SKILL.md:9` is "a pre-adaptive-thinking mechanism that is a no-op on the current model family." That is false. Recovered from Claude Code 2.1.220: a case-insensitive, word-bounded matcher is applied to the expanded body of every command and skill on load, and emits a system-reminder requesting deeper reasoning. The guard that would exempt plugin content returns true only for MCP and memory-store sources — plugin skills and commands are **not** exempt.

Correct the two **live** surfaces. Do **not** edit `docs/model-optimization-audit-opus5-sonnet5-20260728.md`: it is a dated historical report, and editing it to remove a finding it genuinely made would falsify the record — the same mis-scoping E063's Phase 8 correctly refused. Reference it as superseded instead.

**Tasks:**

1. [x] Correct `LAB_NOTEBOOK.md:1385`'s "no-op on the current model family" **in place** per Rule 4 — strike through, do not delete, and point at this plan's Phase 2.
2. [x] Add a Verified Operational Rule to `CLAUDE.md` stating: the keyword is live and matched case-insensitively with word boundaries against expanded command/skill bodies; it is a **prompt-level attachment**, entirely separate from the `effort` frontmatter field, and the two stack additively; and — per the E061 name-don't-render lesson — prose that *contains* the token inside a skill or command body **fires it**, so the mechanism must be named, never rendered, in any component body.
3. [x] Record that the feature is behind a server-controllable gate that currently defaults on, so this is current behaviour and not a stable contract.

**Acceptance Criteria:**

- [x] WHEN a reader consults `CLAUDE.md`'s Verified Operational Rules THEN they SHALL find the keyword documented as live, with the frontmatter/attachment distinction stated
- [x] WHEN `LAB_NOTEBOOK.md` is read at the corrected line THEN the original claim SHALL still be visible as struck-through text with a pointer, not removed
- [x] `docs/model-optimization-audit-opus5-sonnet5-20260728.md` is byte-identical to its state at `main`
- [x] No file under `plugins/` is modified by this item

**Notes:**

This item is the reason Phase 1 exists. Phase 2 deletes the instances; without this, the next reader re-derives the wrong conclusion from the notebook and re-adds them.

#### 1.2 Correct the "SKILL.md bodies are always-loaded" premise ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #238 (premise)
**Depends On:** None
**Files Affected:**
- `CLAUDE.md` (modify — the body-budget rule's rationale)
- `LAB_NOTEBOOK.md` (modify — Decision Log entry)

**Description:**

`CLAUDE.md`'s body-budget rule is read as a context-economy rule. It is not one. The harness loads a SKILL.md body **only on invocation**; only the one-line description is in the system prompt every turn. The harness's own skill-doctor legend states this verbatim. There is no platform line limit for plugin skills — `claude plugin validate --strict` passes at 540 lines today — and the 500 figure is an Anthropic *authoring* best-practice about progressive disclosure that entered this repo's `CLAUDE.md` labelled "the official 500-line budget," with no citation.

`LAB_NOTEBOOK.md:166` (E032) already records the correct version — *"a house rule, not a CI gate"* — so this is a regression in the repo's own understanding, not a new discovery.

Re-frame the rule as **authoring quality** (keep instructions scannable; push bulk to `references/` so the model reads it on demand) and state explicitly that the always-loaded surface is the `description`, which is why the ≤1024-character half of the same rule has real teeth.

**Tasks:**

1. [x] Rewrite the rationale on `CLAUDE.md`'s body-budget rule: authoring quality, not context economy; description is the always-loaded surface.
2. [x] Add a Decision Log row recording the correction, citing E032 as the prior statement the repo lost track of.
3. [x] Do **not** delete the line budget — Phase 7 still gates it, on the authoring-quality argument.

**Acceptance Criteria:**

- [x] WHEN `CLAUDE.md`'s body-budget rule is read THEN it SHALL NOT claim the body is loaded every turn
- [x] WHEN the rule is read THEN it SHALL state that the `description` is the always-loaded surface
- [x] The `<500` figure itself is unchanged (Phase 7 depends on it)
- [x] A Decision Log row exists citing E032

**Notes:**

Correcting this *before* Phase 7 matters: Phase 7's gate comment must state the right rationale, and a gate that ships explaining itself with a false premise is worse than one that ships silently.

### Phase 1 Testing Requirements

Documentation-only. Verification is the lint gate plus a content assertion that the false claims are gone from live surfaces and intact in the historical one.

### Phase 1 Completion Checklist

- [ ] Both items COMPLETE
- [ ] The audit report is untouched
- [ ] No `plugins/` file modified, so no version bump is required for this phase

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| Lint (mirrors CI exactly) | `npx markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'` | exit 0 |
| Audit report untouched | `git diff --quiet main -- docs/model-optimization-audit-opus5-sonnet5-20260728.md` | exit 0 |
| No plugin change this phase | `git diff --quiet main -- plugins/` | exit 0 |
| Release gate (no-op expected) | `python3 scripts/check_version_bump.py --base main` | exit 0 |

<!-- END DOD -->

---

## Phase 2: The `ultrathink` Set — Mould and Castings

### Goals

Remove the live keyword from both component bodies and from the generator template that mints it. All three move together: fixing the two instances without the template guarantees the next planning command re-introduces it.

**Handling note for the implementer:** these edits necessarily involve the literal token. That is unavoidable for a deletion. Do **not** add explanatory prose containing the token to any file under `plugins/` — explain in the commit message and the notebook instead. This is ADR-0011's name-don't-render rule applied to a different mechanism.

### Work Items

#### 2.1 Remove the bare keyword from `ultra-plan` and decide its `effort:` ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #199 item 1
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/ultra-plan/SKILL.md` (modify)

**Description:**

`:9` is a bare keyword on its own line as the first line of the body. It fires on every invocation. Delete it.

The frontmatter question is **not** "add the missing field" — the skill already runs at `high` by default, so adding `effort: high` changes nothing. The real decision is whether `/ultra-plan` should run *above* the default. Its work is deep multi-file investigation with synthesis, which is the profile the sanctioned guidance calls intelligence-sensitive. Set `effort: xhigh` explicitly and record the reasoning, or leave the field absent and accept `high`. Do not set `effort: high` — it is a no-op that also pins a value where the default already provides it.

**Tasks:**

1. [x] Delete line 9 and any orphaned blank line.
2. [x] Add `effort: xhigh` to frontmatter, with a Decision Log entry recording that this replaces an implicit escalation with an explicit, sanctioned one — or leave absent and record *that* choice. Do not add `effort: high`.
3. [x] Verify frontmatter still parses with `yaml.safe_load` and carries a full key set — not merely that `--strict` exits 0 (the E061 lesson).

**Acceptance Criteria:**

- [x] WHEN `/ultra-plan` is invoked THEN no system-reminder about the keyword SHALL be emitted
- [x] WHEN the frontmatter is parsed by `yaml.safe_load` THEN `name`, `description`, and every pre-existing key SHALL still be present
- [x] The frontmatter does NOT contain `effort: high`
- [x] `claude plugin validate plugins/personal-plugin --strict` exits 0

**Notes:**

The escalation the keyword was providing is real; deleting it without a replacement is a de-escalation, not a neutral cleanup. Whichever way the decision goes, it must be recorded as a decision.

#### 2.2 Remove the second live site from `plan-improvements` ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #199 item 1 (site not identified in the issue)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**

`:34` contains the token inside a section heading, capitalised and parenthesised. It fires: the matcher is case-insensitive and `(` / `)` are word boundaries. This command therefore carries **two stacking escalations** — `effort: max` at `:4` and this injection.

Delete the parenthetical from the heading. Leave `effort: max` alone: whether `max` is right is #199 item 3, which remains open as a measurement task and is explicitly **not** an edit in this plan. Removing this line is a prerequisite for that measurement ever being valid — with two escalations stacked, an A/B of the frontmatter value measures a confounded variable.

**Tasks:**

1. [x] Delete the parenthetical from the `:34` heading, leaving the heading text otherwise unchanged.
2. [x] Search the rest of the file for any further occurrence and remove it.
3. [x] Do NOT modify `:4`.
4. [x] Do NOT modify `:350` (that claim is closed as wrong-as-filed in Phase 5.3).
5. [x] Do NOT modify `:414-421` (that is Phase 4.3, and this file is serialized between the two phases).

**Acceptance Criteria:**

- [x] WHEN the file is loaded as a command body THEN no system-reminder about the keyword SHALL be emitted
- [x] `:4` still reads `effort: max`
- [x] Lines `:350` and `:414-421` are byte-identical to `main`
- [x] The heading at `:34` still names the phase it labels

**Notes:**

This is the single most actionable thing in #199, and it exists only because the fan-out disproved the issue's own premise. Both #199 and the E052 audit recommend deleting this line — *because it is dead*. Right action, wrong reason, and the wrong reason is recorded in three files (Phase 1.1 fixes two of them).

#### 2.3 Fix the mould ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #199 item 1 (ranked lowest in the issue; highest here)
**Depends On:** 2.2
**Files Affected:**
- `plugins/personal-plugin/references/templates/planning.md` (modify)

**Description:**

`:66` emits the same parenthesised heading into every planning command minted from this template. It is inert where it sits — `references/` files are never expanded as a body — but every casting is live. `commands/plan-improvements.md:34` is not a coincidence; it is a casting of this mould.

This is the fourth consecutive plan in which a generator template has had to be fixed alongside its castings (`adr-template.md`, three `references/` consent templates, `update-readme.py`, and now this).

**Tasks:**

1. [x] Remove the parenthetical from `:66`.
2. [x] Check the template's own `effort:` value at `:27` and confirm it is a deliberate choice, not an inherited default; leave it unless it is provably wrong.
3. [x] Grep the whole of `plugins/` for any remaining occurrence and confirm the count is zero.

**Acceptance Criteria:**

- [x] WHEN a new planning command is generated from this template THEN its body SHALL NOT contain the keyword
- [x] Zero occurrences remain anywhere under `plugins/`
- [x] `python3 scripts/update-readme.py --check` exits 0 (template changes must not disturb generated inventory)

**Notes:**

Fixing 2.1 and 2.2 without 2.3 guarantees regression on the next planning command. Fixing 2.3 without 2.1/2.2 leaves both live sites firing.

### Phase 2 Testing Requirements

The property to assert is **zero occurrences under `plugins/`**, matched case-insensitively, since the live matcher is case-insensitive. A case-sensitive grep would have missed `:34` — that is precisely how the issue missed it.

### Phase 2 Completion Checklist

- [ ] All three items COMPLETE
- [ ] Case-insensitive sweep of `plugins/` returns zero
- [ ] `plan-improvements.md` lines `:4`, `:350`, `:414-421` untouched
- [ ] Version bumped and CHANGELOG entry added (this phase changes `plugins/`)

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| Zero live sites, case-insensitive | `! grep -rniE 'ultrathink' plugins/` | exit 0 (grep finds nothing) |
| `effort: max` preserved | `grep -qx 'effort: max' plugins/personal-plugin/commands/plan-improvements.md` | exit 0 |
| Untouched regions in the shared file | `grep -qx 'effort: max' plugins/personal-plugin/commands/plan-improvements.md && grep -q 'Orchestrator note' plugins/personal-plugin/commands/plan-improvements.md && grep -q 'Context Budget' plugins/personal-plugin/commands/plan-improvements.md` | exit 0 (Phase 4 removes the budget table; until then all three must survive) |
| Frontmatter integrity | `python3 -c "import yaml,pathlib,sys; d=yaml.safe_load(pathlib.Path('plugins/personal-plugin/skills/ultra-plan/SKILL.md').read_text().split('---')[1]); sys.exit(0 if {'name','description'} <= set(d) else 1)"` | exit 0 |
| Official validation | `claude plugin validate plugins/personal-plugin --strict` | exit 0 |
| Injections | `python3 scripts/check_injections.py` | exit 0 |
| Inventory | `python3 scripts/update-readme.py --check` | exit 0 |
| Release gate | `python3 scripts/check_version_bump.py --base main` | exit 0 |
| Lint (mirrors CI exactly) | `npx markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'` | exit 0 |

**Negative test required before accepting the sweep:** re-introduce the token in a scratch copy of a skill body and confirm the case-insensitive grep exits non-zero. A sweep that cannot fail is worse than none.

<!-- END DOD -->

---

## Phase 3: Effort Calibration — Only What Changes Behaviour

### Goals

Apply only the `effort:` values that produce a behavioural delta. **All three of #199's `high` recommendations are dropped** — an absent field already resolves to `high`, so they are no-ops. Every item here is a *downgrade* from an effective `high`, or the single upgrade the issue proposed.

### Work Items

#### 3.1 Apply `effort: low` to the mechanically-bounded components ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: haiku**
**Recommendation Ref:** #199 item 2 (low group)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/unlock/SKILL.md` (modify)
- `plugins/personal-plugin/skills/fleet-health/SKILL.md` (modify)
- `plugins/personal-plugin/skills/new-project/SKILL.md` (modify)
- `plugins/slide-gen/skills/sg-build/SKILL.md`, `sg-draft`, `sg-generate-images`, `sg-optimize`, `sg-outline`, `sg-research`, `sg-validate-graphics` (modify — 7 files)

**Description:**

Each of these is a bounded, low-judgment component currently running at the default `high`. `unlock` is four fixed steps of shell-out with zero judgment. `fleet-health` is a fixed 5-host probe set with static thresholds and a sub-60-second contract. `new-project` is pure scaffolding. The seven `sg-*` wrappers are 70–91 lines each with two shell invocations, all real work in the external engine.

**Excluded deliberately:** `sg-full-workflow` — #199 assigns it *two conflicting values*, listing it under `medium` and again inside "all 8 `sg-*` wrappers → `low`". On merits it is `medium` (169 lines, ten invocations, resume/orchestration judgment) and it is handled in 3.2. `archive-project` and `bpmn-to-drawio` are also excluded: the first branches destructively on a classification it makes itself, the second has a real manual-conversion fallback path. Both are `medium` candidates at best and neither is worth the risk here.

**Tasks:**

1. [x] Add `effort: low` to each of the 10 files' frontmatter.
2. [x] Verify each file's frontmatter still parses with `yaml.safe_load` and retains its full key set.
3. [x] Confirm `sg-full-workflow` is NOT modified by this item.

**Acceptance Criteria:**

- [x] WHEN each of the 10 files' frontmatter is parsed THEN `effort` SHALL equal `low` and every pre-existing key SHALL be present
- [x] `sg-full-workflow/SKILL.md` is byte-identical to `main`
- [x] `claude plugin validate --strict` exits 0 for all three plugins

**Notes:**

These are downgrades from an effective `high`, not additions of a missing setting. The commit message must say so.

#### 3.2 Apply `effort: medium` to the defensible orchestrators ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: haiku**
**Recommendation Ref:** #199 item 2 (medium group, re-scoped)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/release-plugin/SKILL.md` (modify)
- `plugins/personal-plugin/skills/jetson-audit/SKILL.md` (modify)
- `plugins/slide-gen/skills/sg-full-workflow/SKILL.md` (modify)
- `plugins/personal-plugin/commands/validate-plugin.md` (modify — `high` → `medium`)
- `plugins/personal-plugin/commands/analyze-transcript.md` (modify — `high` → `medium`)

**Description:**

`release-plugin` is a three-phase delegator — the heavy reasoning happens inside the commands it invokes, each with its own effort. `jetson-audit` is bounded comparison against known-good configuration over a fixed command allowlist. `sg-full-workflow` is orchestration with resume judgment. `validate-plugin` is a checklist runner across nine-and-a-half phases with deterministic pass/fail and one optional judgment mode. `analyze-transcript` is structured extraction into seven fixed sections and three fixed output formats — the archetypal case where added effort buys little.

**Excluded deliberately, against the issue:** `ship` (contains a code-review-and-fix loop, and can push and merge — fix-loop quality is exactly what effort buys), `jetson-recon` (its own description declares a trust boundary against untrusted web content; adversarial-input discipline is not a downgrade candidate), `wiki` (cross-page synthesis in two of its three modes — wrong granularity), `develop-image-prompt` (the issue's own rationale, "creative composition benefits from thinking," argues against its own recommendation), and `visual-explainer` (it decides what to depict and how *before* the tool renders, and generation is billed per image — downgrading the reasoning that decides what to spend money on is the wrong trade).

**Tasks:**

1. [x] Add `effort: medium` to the three components currently absent.
2. [x] Change `effort: high` → `effort: medium` in the two commands.
3. [x] Verify frontmatter integrity on all five with `yaml.safe_load`.
4. [x] Confirm none of the five excluded components is modified.

**Acceptance Criteria:**

- [ ] WHEN each of the 5 files' frontmatter is parsed THEN `effort` SHALL equal `medium` with a full key set
- [ ] `ship`, `jetson-recon`, `wiki`, `develop-image-prompt`, and `visual-explainer` SKILL.md files are byte-identical to `main`
- [ ] `claude plugin validate --strict` exits 0

**Notes:**

Five of #199's `medium` recommendations are rejected here with reasons. That is a larger rejection rate than acceptance, which is the expected shape given the base rate.

#### 3.3 Upgrade `arch-synthesize` to `medium` ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: haiku**
**Recommendation Ref:** #199 item 4 (the only upgrade)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/commands/arch-synthesize.md` (modify)

**Description:**

Currently `low`. Of its eight steps, seven are mechanical. Step 6 is not: it identifies findings in one domain that contradict findings in another and resolves them using business impact as a tiebreaker, then writes the executive summary a human acts on. Cross-domain conflict detection with a value-judgment tiebreaker is under-provisioned at `low`.

This is the only recommendation in #199 whose direction is unaffected by the absent-equals-`high` finding, because it is an upgrade from an explicitly-set value.

**Tasks:**

1. [x] Change `effort: low` → `effort: medium`.
2. [x] Verify frontmatter integrity.

**Acceptance Criteria:**

- [x] WHEN the frontmatter is parsed THEN `effort` SHALL equal `medium`
- [x] `claude plugin validate plugins/personal-plugin --strict` exits 0

**Notes:**

Best-argued item in the issue.

### Phase 3 Testing Requirements

Assert the resulting distribution, not the diff: parse every component's frontmatter and confirm the intended value, and confirm every deliberately-excluded file is unchanged. The exclusions carry as much intent as the changes.

### Phase 3 Completion Checklist

- [ ] All three items COMPLETE
- [ ] Zero components carry a newly-added `effort: high` (it is a no-op)
- [ ] All 8 deliberately-excluded files byte-identical to `main`
- [ ] Version bumped and CHANGELOG entry added

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| No no-op additions | `git diff main -- plugins/ \| grep -c '^+effort: high'` | output `0` |
| Exclusions intact | `git diff --quiet main -- plugins/personal-plugin/skills/ship/SKILL.md plugins/personal-plugin/skills/jetson-recon/SKILL.md plugins/personal-plugin/skills/wiki/SKILL.md plugins/personal-plugin/skills/visual-explainer/SKILL.md plugins/personal-plugin/commands/develop-image-prompt.md` | exit 0 |
| Frontmatter integrity, **every** skill (not only changed ones) | `python3 -c "import yaml,pathlib,sys; bad=[]\nfor p in pathlib.Path('plugins').rglob('SKILL.md'):\n try:\n  d=yaml.safe_load(p.read_text().split('---')[1]); assert isinstance(d,dict) and 'name' in d and 'description' in d\n except Exception: bad.append(str(p))\nprint(bad); sys.exit(1 if bad else 0)"` | exit 0. **Negative-tested:** a planted `description` containing a colon-space exits 1 |
| Official validation ×3 | `for p in personal-plugin bpmn-plugin slide-gen; do claude plugin validate plugins/$p --strict \|\| exit 1; done` | exit 0 |
| Release gate | `python3 scripts/check_version_bump.py --base main` | exit 0 |
| Lint (mirrors CI exactly) | `npx markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'` | exit 0 |

<!-- END DOD -->

---

## Phase 4: Context Thresholds That Are Genuinely Stale

### Goals

Fix the four sites that carry real absolute thresholds, adopting the in-repo exemplar's **four-part** pattern rather than only its phrasing. Three of #200's five filed sites are wrong and are not touched.

**Two traps govern this phase.** The "Output Reserve" column is bounded by *max output tokens*, not context — output did not grow with the context window, so that table must be **deleted**, never rescaled. And the 100-entry threshold in `summarize-feedback` doubles as an API-round-trip warning; the fix must decouple the two rather than remove both.

### Work Items

#### 4.1 `analyze-transcript` — seven sites, moved together ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #200 site 1 (under-scoped by 4 sites)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/commands/analyze-transcript.md` (modify)

**Description:**

The file carries seven coupled sites, of which #200 names three. It is also **internally inconsistent today**: `:96` sets a 50K "too large" threshold while `:100` begins chunking at 30K, so the 50K row triggers nothing that 30K has not already triggered, and `:82` says content under 30K proceeds directly — making the 30K–50K band simultaneously "not too large" and chunked.

The chunking path is real work, not a no-op, and its quality cost is self-documented: `:113` instructs the model to ensure no decisions or action items are lost at chunk boundaries — an instruction to mitigate a problem the chunking itself creates.

Adopt the exemplar's full four-part shape: a relative trigger placed inline at the point of work; a named, concretely-specified degradation strategy that degrades **resolution rather than scope** (structure-first reading keeps the whole input in view, so there are no boundaries to lose items at); an error-table row that delegates to that strategy and carries no number of its own; and a performance-table row keyed on the same relative phrase.

**Tasks:**

1. [x] Replace the absolute triggers at `:82`, `:96`, `:100`, `:102` with a single relative trigger, resolving the 30K/50K contradiction to one threshold.
2. [x] Replace the split-and-reconcile strategy with a structure-first strategy modelled on the exemplar's four numbered steps.
3. [x] Update the user-visible example string at `:117` so it no longer implies a token-band calculation.
4. [x] Re-key the performance table at `:368-371` and the note at `:373` to the relative phrase.
5. [x] Confirm the boundary-loss warning at `:113` is either removed as moot or retained deliberately with a reason.

**Acceptance Criteria:**

- [x] WHEN the file is read THEN it SHALL contain no absolute token threshold governing chunking
- [x] WHEN the file is read THEN exactly one trigger condition SHALL govern the degradation path (no second, differently-numbered trigger)
- [x] WHEN the degradation strategy is read THEN it SHALL specify concrete numbered steps, not a bare instruction
- [x] The output report's seven fixed sections are unchanged

**Notes:**

Moving three of seven sites leaves the file contradicting itself more than it already does.

#### 4.2 `assess-document` — replace an undefined fallback with a strategy ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #200 site 2 (understated)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/commands/assess-document.md` (modify)

**Description:**

Worse than filed, in a way that changes the remedy. `:72` calls ~100K "context window capacity" — wrong in its own era, let alone now — but the real defect is that its degradation path is **undefined**: it says the assessment will focus on "the first N sections" and `N` is never bound anywhere in the file. `:454` repeats the same undefined N.

**Raising the number fixes nothing.** This site needs a strategy borrowed from the exemplar, whose error row carries no number and delegates to a four-step method defined at the point of work.

**Tasks:**

1. [x] Add a relative-trigger context-management block at the point of work, with concrete numbered degradation steps.
2. [x] Rewrite `:72` to delegate to that block and carry no number and no undefined variable.
3. [x] Rewrite `:454` to match.
4. [x] Define a terminal fallback for the case where even the degraded strategy exceeds context, as the exemplar does.

**Acceptance Criteria:**

- [x] WHEN the file is read THEN no instruction SHALL reference an unbound variable such as "the first N sections"
- [x] WHEN the degradation path is triggered THEN a concrete, numbered strategy SHALL be available at the point of work
- [x] WHEN even the degraded strategy is insufficient THEN a terminal fallback message SHALL be specified

**Notes:**

The property to assert is "no unbound variable in an instruction," not "the number changed."

#### 4.3 `plan-improvements` — delete the absolute budget table, touch nothing else ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #200 site 3b (the only genuinely stale part of that file)
**Depends On:** Phase 2.2
**Files Affected:**
- `plugins/personal-plugin/commands/plan-improvements.md` (modify)

**Description:**

**`:53` is already context-relative** and is #200's marquee example — it reserves a *percentage* of available context and auto-scales. Do not touch it. Nor `:447`, which is the same idiom.

`:414-421` is the genuinely absolute part, and it carries the trap: every row sums to exactly 100K, modelling a fixed budget split between reading and writing. **Input context grew to 1M; per-response output did not.** Rescaling the Output Reserve column would produce a meaningless number. Delete the table and let `:53`'s percentages govern the input side, leaving output bounded by the model's own limit.

**`:274-300` must not be swept up.** Those cap plan phases at 5–8 files and ~500 LOC, and `:300` states the reason explicitly: `/implement-plan` executes each phase via a subagent with finite context, and oversized plans cause silent skips. They are codified in `CLAUDE.md` and mirrored in `references/plan-template.md`. They bound an *output artifact*, not a reading budget.

**Tasks:**

1. [x] Delete the Context Budget table at `:414-421` and replace it with a pointer to `:53`'s relative strategy.
2. [x] Leave `:53`, `:447`, and `:55` unmodified.
3. [x] Leave `:274-300` unmodified.
4. [x] Leave `:4`, `:34` (already handled in Phase 2.2), and `:350` unmodified.

**Acceptance Criteria:**

- [x] WHEN the file is read THEN no absolute-token budget table SHALL remain
- [x] Lines `:53`, `:55`, `:274-300`, and `:447` are byte-identical to `main`
- [x] `:4` still reads `effort: max`
- [x] The `/implement-plan` phase-size contract stated at `:300` is intact

**Notes:**

This file is touched by three issues at four regions. Phase 2.2 has already landed its edit; this item must not disturb it.

#### 4.4 `summarize-feedback` — decouple the entry warning from the batching ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #200 site 4 (half wrong as filed)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/summarize-feedback/SKILL.md` (modify)

**Description:**

`:95` is **already context-relative** — do not touch it. `:94` is absolute, but it is an *entry count*, not a token threshold, and it is load-bearing for a second reason the issue missed: the skill makes one API fetch per entry, so 100+ entries means 100+ sequential round-trips and a documented 15–30 minute run. The remedy menu even offers "narrow the date range," which is a fetch-count remedy, useless as a context remedy.

Keep the warning; drop the mandatory batching, which was context-driven and is now unnecessary. The skill's own performance note says the meta-synthesis pass roughly doubles synthesis time — that is the argument for dropping it.

**Tasks:**

1. [x] Retain the >100-entry warning, re-stated as an operation-cost warning (round-trips and wall-clock), not a context warning.
2. [x] Remove the mandatory batch-by-25 processing and the meta-synthesis pass it forces.
3. [x] Update the interaction payload so it no longer offers a mode the skill no longer describes.
4. [x] Leave `:95` unmodified.
5. [x] Update the performance table rows that reference the removed pass.

**Acceptance Criteria:**

- [x] WHEN entry count exceeds 100 THEN the skill SHALL still warn about run duration and API round-trips
- [x] WHEN the skill runs THEN it SHALL NOT mandate a fixed batch size for context reasons
- [x] The interaction payload offers no option the body does not describe
- [x] `:95` is byte-identical to `main`

**Notes:**

The E063 precedent is directly relevant: a naive conversion of an interaction payload silently deleted a capability. Check the payload against the body before and after.

### Phase 4 Testing Requirements

For each file, assert the *property* — no absolute token threshold governs a degradation path — rather than grepping for specific numbers, which would pass on a file that merely renamed its constant. Then assert every must-not-touch region byte-identical.

### Phase 4 Completion Checklist

- [x] All four items COMPLETE
- [x] `prime/SKILL.md` untouched (misfiled in #200 — it is a wall-clock table)
- [x] `finish-document.md:311-312` untouched (human interaction checkpoints, not context)
- [x] `consolidate-documents.md` and `define-questions.md` untouched (they are the exemplars)
- [ ] Version bumped and CHANGELOG entry added

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| Must-not-touch set intact | `git diff --quiet main -- plugins/personal-plugin/skills/prime/SKILL.md plugins/personal-plugin/commands/finish-document.md plugins/personal-plugin/commands/consolidate-documents.md plugins/personal-plugin/commands/define-questions.md` | exit 0 |
| `plan-improvements` relative trigger preserved | `grep -q '60% of available context' plugins/personal-plugin/commands/plan-improvements.md` | exit 0 |
| `plan-improvements` absolute table gone | `! grep -q 'Output Reserve' plugins/personal-plugin/commands/plan-improvements.md` | exit 0. **Row corrected during execution.** As authored it was `! grep -qE '^\| (Small\|Medium\|Large\|Very Large) \('`, which matches TWO tables — the absolute context-budget table this item deletes *and* a wall-clock duration table that legitimately survives — so it returned exit 1 against a correctly-completed item. `Output Reserve` is the column that made the table absolute, so it is the derived property. |
| Phase-size contract intact | `grep -q 'subagent with finite context' plugins/personal-plugin/commands/plan-improvements.md` | exit 0 |
| `summarize-feedback` relative trigger preserved | `grep -q '60% of estimated context window' plugins/personal-plugin/skills/summarize-feedback/SKILL.md` | exit 0 |
| No unbound-N instruction | `! grep -qE 'first N sections' plugins/personal-plugin/commands/assess-document.md` | exit 0 |
| Official validation | `claude plugin validate plugins/personal-plugin --strict` | exit 0 |
| Evals | `python3 scripts/check_eval_mapping.py` | exit 0 |
| Release gate | `python3 scripts/check_version_bump.py --base main` | exit 0 |
| Lint (mirrors CI exactly) | `npx markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'` | exit 0 |

<!-- END DOD -->

---

## Phase 5: Tier-Routing Prose + the visual-explainer Knob

### Goals

Ship the one tier-routing change the in-repo evidence supports, close the three claims it refutes, and split `visual-explainer`'s single model knob on the correct axis.

### Work Items

#### 5.1 Qualify Rule 17's opus bullet, in task properties ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #198 items 1–2 (item 1 mostly refuted)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/references/plan-template.md` (modify — Rule 17)
- `.claude/agents/opus-implementer.md` (modify)

**Description:**

The in-repo evidence supports exactly one change, and it points opposite to the issue's framing. Across plans v12 and v13, **15 `sonnet` items touched ≥3 files each (max 10) with zero escalations** — precisely the work Rule 17 assigns categorically to `opus`. Meanwhile two v13 `opus` items were a one-line CI edit and a zero-file verification task. There is concrete evidence of **opus over-spend** and none of sonnet under-performance.

`sonnet-implementer.md:31` is **not** touched: its escalation trigger is already qualified as multi-file refactoring *with system-wide coupling not anticipated in the plan*. The issue's claim that it fires on multi-file-ness per se is wrong.

**ADR-0005 rule 2 binds this edit.** The qualification must be written in task properties — coupling, spec clarity, ambiguity — and must **not** name a model generation. Writing "Sonnet 5 is now capable of multi-file refactors" re-creates the staleness class ADR-0005 exists to eliminate, and would be caught by the same reasoning that produced the ADR.

**Tasks:**

1. [x] Qualify Rule 17's unqualified "multi-file refactors" so it routes on coupling and spec clarity, not on file count.
2. [x] Apply the same qualification to `opus-implementer.md`'s corresponding bullet.
3. [x] Verify no model generation name appears in either edit.
4. [x] Do NOT modify `sonnet-implementer.md`.

**Acceptance Criteria:**

- [x] WHEN Rule 17 is read THEN "multi-file" SHALL NOT appear as an unqualified opus criterion
- [x] WHEN either edited file is read THEN no model generation name SHALL appear in the changed lines
- [x] `sonnet-implementer.md` is byte-identical to `main`
- [x] `python3 scripts/check_agent_models.py` exits 0

**Notes:**

This plan's own tier assignments already follow the corrected rule, which is the first live test of it.

#### 5.2 Split `visual-explainer`'s model knob on the loop boundary ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: opus**
**Recommendation Ref:** #198 item 5 (correct in substance, wrong in shape)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/config.py` (modify)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/pipeline.py` (modify)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/prompt_generator.py` (modify)
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/image_evaluator.py` (modify)
- `plugins/personal-plugin/tools/visual-explainer/tests/` (modify — ~6 files)
- `plugins/personal-plugin/tools/visual-explainer/README.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify — env-var docs only)

**Description:**

One setting feeds **four** runtime consumers, not the three the issue names. The missed one is prompt *refinement*, which receives its model from the generation knob but runs once per failed attempt **inside the loop**. So the issue's proposed eval-vs-everything-else split is wrong-shaped: it would move vision calls to a cheaper tier while stranding an equally high-volume text call on the expensive one. **The boundary is loop vs one-shot.**

Volume asymmetry is real and justifies the split: worst case 200 evaluation plus 180 refinement calls against 1 analysis call, with every evaluation call carrying a re-encoded 4K image.

The `DEFAULT_MODEL` constants are **not** dead as filed — they are the effective value on five factory paths, and `create_prompt_generator()` receives a config carrying the model and silently ignores it. That plumbing gap is a real bug and is fixed here; the constants stay.

Design is **fall-back override, not rename**: keep the existing setting unchanged in name, default, and environment variable; add an optional loop-tier override defaulting to `None` with a resolver that falls back to the base value, so an unset override is indistinguishable from today.

**Do not flip any default in this item.** The economic case rests on the tier premium, and the premium is currently **2.5×**, not the ~1.7× the issue assumes — the lower figure only becomes true after the current introductory pricing ends on 2026-08-31.

**Tasks:**

1. [x] Add an optional loop-tier setting with a `None` default plus a resolver that falls back to the existing setting.
2. [x] Route both loop consumers — image evaluation and prompt refinement — through the resolver.
3. [x] Fix `create_prompt_generator()` to forward the config value it already receives.
4. [x] Give `ImageEvaluator` optional config visibility for symmetry with its two siblings.
5. [x] Update the exact-kwarg assertion in the pipeline test, the shared config fixture, and the config default/env tests; add the missing mirror assertion for the evaluator construction site.
6. [x] Update both user-facing documentation surfaces.
7. [x] Leave the auth-ping model literal alone — it is a `max_tokens=1` reachability check whose output is discarded.
8. [x] Do NOT change any default model value.

**Acceptance Criteria:**

- [x] WHEN the loop override is unset THEN every call site SHALL resolve to exactly the value it resolves to today
- [x] WHEN the loop override is set THEN both evaluation and refinement SHALL use it, and analysis and generation SHALL NOT
- [x] WHEN `create_prompt_generator()` is called with a config THEN the config's model SHALL reach the constructed generator
- [x] Coverage remains at or above the configured floor
- [x] No default model value differs from `main`

**Notes:**

The backward-compatibility property — unset override is behaviourally identical to today — is the acceptance criterion that matters most and must be tested directly, not inferred.

**Completion notes (2026-07-31):**

Setting is `InternalConfig.claude_loop_model` (`str | None`, default `None`), env `VISUAL_EXPLAINER_CLAUDE_LOOP_MODEL`, resolver `InternalConfig.resolve_loop_model(base: str | None = None) -> str`.

**The resolver takes a `base` argument, and that is the load-bearing design decision.** A no-argument resolver falling back to `claude_model` would *not* have been backward compatible: `PromptRefiner` inherits its model from `PromptGenerator.model`, which can be passed explicitly and need not equal `claude_model` (`test_init_with_custom_model` constructs exactly that case). Falling back to `claude_model` there would have silently overridden a caller's explicit choice — a behaviour change smuggled in under a setting whose whole premise is that unset means unchanged. Falling back to `base` preserves the inheritance exactly. The resolver is idempotent, so resolving at both a construction site and inside the consumer is safe.

Resolution happens inside each in-loop consumer (`ImageEvaluator.__init__`, and `PromptGenerator.__init__` for the refiner it composes) rather than at the pipeline call sites, so the env var reaches direct-construction paths too, not only the pipeline.

`create_prompt_generator()` now resolves the config once and forwards `model=` explicitly; this also fixes the `internal_config=None` path, which previously paired a `DEFAULT_MODEL` literal with a `from_env()` config that could carry a different `claude_model`.

Negative test performed as required: reverting *only* the `create_prompt_generator()` fix failed 3 tests (`test_create_prompt_generator_forwards_config_model`, `..._forwards_env_model`, `test_factory_keeps_generation_on_base_model_under_override`, each asserting `claude-sonnet-5 != <configured>`); restoring it passed all 3. Suite 894 → 913 passed, coverage 93.37% → 93.38% (floor 85%), ruff and mypy clean. `api_setup.py` has a zero-line diff. Version bump and CHANGELOG are owned by item 8.1, so deliberately not done here.

#### 5.3 Close #198's refuted claims with evidence ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #198 items 1c, 3, 4
**Depends On:** 5.1
**Files Affected:**
- `LAB_NOTEBOOK.md` (modify — Decision Log)

**Description:**

Three of #198's four prose claims are refuted and must be recorded as such rather than silently dropped.

**Claim 1c** (`sonnet-implementer.md:31` escalates on multi-file-ness per se) is wrong — the trigger is already doubly qualified. **Claim 3** ("no escalation above Opus reads as staleness") is wrong twice over: it is D15, ACTIVE since 2026-05-10 with a recorded rejected alternative, and it is *literally true* for this repo, which has no fable-tier implementer agent and no mechanism to dispatch one. **Claim 4**'s premise ("the advisory is satisfied by default now") is unverifiable in-repo — nothing sets a session model — and the advisory it proposes to reword is D16, whose deletion was already considered and rejected.

Record a Decision Log row. Do not edit D15 or D16 beyond adding cross-references; both remain ACTIVE.

**Tasks:**

1. [x] Add a Decision Log row recording the three refutations with their evidence.
2. [x] Cross-reference D15 and D16 without changing their status.
3. [x] Record the escalation base rate — one escalation in 162 tiered items, attributable to a self-contradictory spec rather than capability — as the standing evidence for future tier debates.

**Acceptance Criteria:**

- [x] WHEN the Decision Log is read THEN a row SHALL record all three refutations with evidence
- [x] D15 and D16 remain ACTIVE with their original text intact
- [x] The escalation base rate is recorded with its denominator

**Notes:**

The base rate is the durable artifact. It is the only quantitative evidence this repo has about tier calibration, and it took reading two archived plans and two notebook entries to produce.

### Phase 5 Testing Requirements

The Python change carries the real test surface: the backward-compatibility property must be asserted directly, and the plumbing fix needs a test that fails before it. The prose changes need an assertion that no model generation name entered the diff.

### Phase 5 Completion Checklist

- [ ] All three items COMPLETE
- [ ] `sonnet-implementer.md` untouched
- [ ] No default model value changed
- [ ] Version bumped and CHANGELOG entry added

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| No model generation named in tier prose | `! git diff main -- plugins/personal-plugin/references/plan-template.md .claude/agents/opus-implementer.md \| grep -E '^\+' \| grep -qiE 'sonnet [0-9]\|opus [0-9]\|claude-(sonnet\|opus)-[0-9]'` | exit 0 |
| sonnet-implementer untouched | `git diff --quiet main -- .claude/agents/sonnet-implementer.md` | exit 0 |
| Agent alias gate | `python3 scripts/check_agent_models.py` | exit 0 |
| visual-explainer tests | `cd plugins/personal-plugin/tools/visual-explainer && python -m pytest -q` | exit 0, coverage floor met |
| Lint + types | `cd plugins/personal-plugin/tools/visual-explainer && uvx ruff@0.14.10 check src tests && mypy src --ignore-missing-imports` | exit 0 |
| No default flipped | `! git diff main -- plugins/personal-plugin/tools/visual-explainer/ \| grep -E '^[+-].*default=.*claude-' \| grep -qv 'claude-sonnet-5'` | exit 0 |
| Release gate | `python3 scripts/check_version_bump.py --base main` | exit 0 |

**Negative test required:** revert the `create_prompt_generator()` plumbing fix and confirm its new test fails. A test that passes both before and after proves nothing.

<!-- END DOD -->

---

## Phase 6: `/research-topic` Streaming Transport

### Goals

Move the Claude leg from a single non-streaming request to streaming with accumulation, **keeping the existing depth ladder unchanged**, and create the first testable surface this leg has ever had.

**Scope decision, taken by the owner:** transport only. The filed ladder change is not implemented — current guidance for the default model says start at the middle of the range and sweep *down*, treats the top tiers as requiring a measured win, and states that the effort dial is not a reliable lever on visible output length, which is exactly what this leg produces.

**The justification is stronger than the issue claims.** The shipped comprehensive tier already runs at double the documented non-streaming output ceiling. This is a latent correctness fix, not only an enhancement.

### Work Items

#### 6.1 Build the accumulator as a real, testable file ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: opus**
**Recommendation Ref:** #216 (testability, not in the issue)
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/tools/research-sse/` (create — package, entry point, accumulator)
- `plugins/personal-plugin/tools/research-sse/tests/fixtures/` (create — offline fixture corpus)
- `plugins/personal-plugin/tools/research-sse/pyproject.toml` (create)

**Description:**

This leg currently has **zero testable surface**: the request lives in a markdown reference file that a subagent reads and hand-substitutes at runtime. Nothing renders, lints, or executes it. That is the substrate that let a prior crash sit undetected on every dispatch.

The decision is binary. An inline heredoc inside a markdown fence reproduces that substrate exactly. A real file that reads an event stream on stdin and writes accumulated text plus terminal metadata to stdout is fully unit-testable with fixtures, needs no key and no network, and slots into the existing test job — for which the bundled diagram tool is the in-repo precedent.

**Tasks:**

1. [x] Create the package with a stdin→stdout accumulator, stdlib-only where practical. (Stdlib-only with no caveat — zero dependencies, `dependencies = []`.)
2. [x] Build the offline fixture corpus: happy path; interleaved reasoning block skipped; truncation-at-ceiling terminal reason; refusal terminal reason with a category; refusal with a null category; **mid-stream error event after a successful start**; truncated stream with no terminal event; malformed data line; unknown event type and unknown block type ignored gracefully; empty stream; non-stream error body. (15 fixtures — the 11 required plus refusal-with-absent-`stop_details`, refusal-with-`stop_details`-in-an-unexpected-position, completed-but-empty, and unrecognised-terminal-reason.)
3. [x] Implement a **completeness sentinel**: absence of a terminal event is a failure regardless of transport status. (Exit 5. Deliberately keyed to *an unresolved `stop_reason`*, not to `message_stop` — a `message_stop` with no stop_reason still fails, because "the turn ended" is not "we know why it ended".)
4. [~] Wire the test suite into the existing per-tool CI pattern. **Partially done, deliberately.** The tool conforms to the pattern exactly (sibling `pyproject.toml` shape, `tests/`, `requirements-lock.txt`, `[tool.coverage.report] fail_under = 95`, mypy-clean `src/`), and CI's **ruff check and ruff format steps already cover it automatically** — `validate.yml` globs `plugins/*/tools/*/src/ plugins/*/tools/*/tests/`, so no edit was needed there and lint is live now. The remaining wiring needs edits to files outside this item's declared `Files Affected` (a `research-sse` job in `test.yml`, a `python-compat` step, a `pip-audit` line, and the root `pyproject.toml` testpaths/pythonpath), so it is left to the follow-up that owns those files. Follow the `task-sync` precedent: add the job **non-required** first, so a not-yet-existing required check cannot deadlock the PR that creates it.

**Acceptance Criteria:**

- [x] WHEN a complete stream is supplied on stdin THEN the accumulator SHALL emit the concatenated text and exit 0
- [x] WHEN a stream ends without a terminal event THEN the accumulator SHALL exit non-zero
- [x] WHEN an error event arrives after a successful start THEN the accumulator SHALL exit non-zero
- [x] WHEN the terminal reason indicates a refusal THEN the accumulator SHALL exit non-zero and surface the category, including when the category is null
- [x] WHEN the terminal reason indicates truncation THEN the accumulator SHALL exit 0 and signal truncation distinctly from success
- [x] Every fixture has a corresponding mutation test: deleting the branch flips the row from caught to passing

**Notes:**

The refusal guard is the highest risk in the whole plan. In the current non-streaming shape the terminal reason is a top-level field; under streaming it moves inside a delta event. A port that reassembles the stream and keeps the old field lookup **compiles, reads correctly, passes review, and never fires** — silently writing an empty report on every refusal. That is a previously-fixed defect returning in a form that looks like a faithful port. Write its fixture first.

**Delivered (2026-07-31).** `plugins/personal-plugin/tools/research-sse/` — 87 tests, 99% branch coverage, ruff + `ruff format` + mypy clean.

The refusal fixture was written first and **run red before the accumulator existed** (`ModuleNotFoundError`), then green. `tests/conftest.py::naive_top_level_stop_reason` performs the *old* top-level lookup against every refusal fixture and asserts it returns `None` — so the defect is pinned by a test, not just by prose. The corresponding mutation (`G11`, rewriting `_terminal_stop_reason` to read only the top level — the faithful-looking port) flips all four refusal tests to failing.

**All 12 guards were mutation-tested fail-first** (baseline pass → mutant FAIL → restored pass), with `--no-cov` on the per-test runs so the 95% floor could not manufacture a false "caught". Deleting the refusal branch is instructive: the *with-category* fixture (which carries partial text) drops to `status='ok', exit_code=0` — it would have written a report whose entire body is a half-finished refusal sentence — while the null-category fixtures drop only to exit 8. The empty-output guard is a real second line of defence but is **not** a substitute for the refusal guard.

Two decisions taken where the spec was open:

- **Truncation exits 0** (as the acceptance criterion requires) and is signalled by a machine-readable marker — `"truncated": true` / `"status": "truncated"` in the metadata — not by a distinct exit code. Exit code **3 is reserved and never emitted** so this stays unambiguous for 6.2.
- **The refusal category's placement is treated as genuinely unknown.** `find_refusal_category` does a depth-bounded search for a `stop_details` (then `refusal`) object *anywhere* in the terminal event rather than hard-coding `delta.stop_details`, and a null/absent category surfaces as `category=unknown` **without** downgrading the refusal. A fixture pins each case, including one that puts `stop_details` at the event top level.

One guard was added beyond the brief: **exit 8, a completed stream that produced no text.** A reasoning-only response reaches a clean `end_turn` and would otherwise have been a silent empty report — the same failure mode as the refusal defect arriving by a different route. It also backstops an unrecognised future terminal reason, which is kept (exit 0, `stop_reason_known: false`) only when there is real text to keep.

#### 6.2 Rewrite the leg to stream, ladder unchanged ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: opus**
**Recommendation Ref:** #216
**Depends On:** 6.1
**Files Affected:**
- `plugins/personal-plugin/references/research-provider-protocols.md` (modify)

**Description:**

Replace the single buffered request with a streaming request piped to the accumulator. Preserve every existing guard.

**Two structural hazards.** The current code captures the transport exit status immediately after a command substitution; introducing a pipe destroys that capture and makes a timeout or reset invisible. And the status-code check reports the header status, which arrives before any content — a stream that opens successfully and then fails mid-flight reports success. The completeness sentinel from 6.1 is what covers that.

Keep the ladder exactly as it is. Keep the truncation note. Keep the refusal check, relocated to read the accumulator's exit status rather than a top-level field.

**Tasks:**

1. [x] Rewrite the request to stream, with buffering disabled. (`"stream": true` inserted as the first key of the body so the two ladder lines stay byte-identical and diff as context; `curl -sS --no-buffer --dump-header` — `-w '%{http_code}'` had to go, because under streaming it would write the status code into the pipe.)
2. [x] Preserve transport-failure detection across the pipe. (`PIPE=("${PIPESTATUS[@]}")` as the statement immediately after the pipeline, split into `CURL_EXIT`/`ACC_EXIT`. Negative-tested — see Notes.)
3. [x] Re-express the refusal and truncation guards in terms of the accumulator's contract. (The whole `CHECK=$(python3 …)` payload-inspection block is gone; the section now contains zero occurrences of the old top-level field name.)
4. [x] Update the section's "synchronous, single call" framing and the conventions note about bounded calls.
5. [x] Leave the depth ladder values unchanged.
6. [x] Add a forward-compatibility note so an unrecognized block type is ignored rather than fatal.

**Acceptance Criteria:**

- [x] WHEN the leg runs THEN the depth ladder values SHALL be unchanged from `main`
- [x] WHEN the transport fails THEN the failure SHALL be detected despite the pipe
- [x] WHEN a refusal occurs THEN the leg SHALL fail loudly rather than write an empty report
- [x] WHEN output is truncated at the ceiling THEN the report SHALL carry the truncation note

**Notes:**

A half-fix across the three files is a recorded failure mode for this skill: the skill body restates the mode and the silent-failure mechanism independently of the protocol file, so they must move together (6.3).

**Delivered (2026-07-31).** The block was not reviewed by reading — it was **extracted verbatim from the markdown fence and executed**, with only the `curl` invocation swapped for a fixture emitter, then driven through eight of 6.1's fixtures. Observed: happy `0`, truncation `0` + `truncated=true`, refusal `4`, no-terminal-event `5`, mid-stream error `6`, non-stream error body `7`, empty-text `8`, unknown-event-and-block `0`. Every non-zero path deleted `$BODY` before exiting. `bash -n` passes on the unmodified fence, and the `-d` payload extracted from it parses as JSON with `stream: true` and no `budget_tokens`.

**Both new guards were negative-tested** (per the repo rule that a guard which cannot fail is worse than none):

- **Transport across the pipe.** A fake transport that emits a *fully well-formed* stream and then exits 28 is the case the pipe would hide, because the accumulator sees a complete stream and exits 0. The `PIPESTATUS` form fails the leg (`transport curl_exit=28`, body discarded); rewriting only that one line to the naive post-pipe `$?` capture prints `Anthropic request ok` and keeps the body. The guard is what does the work, not the shape of the code around it.
- **Contract preflight.** A copy of the tool with `EXIT_REFUSAL` moved from `4` to `9` aborts the leg before the request is spent (`research-sse exit contract drifted (want, got): {'EXIT_REFUSAL': (4, 9)}`); the real tool passes silently. This exists because this file's copy of the exit-status table is a *label* for the contract, and the recorded failure mode is a label that stops matching its content (#226/#232/#235).

Two decisions taken where the item was open:

- **`-w '%{http_code}'` was dropped in favour of `--dump-header`.** The old capture wrote the status code onto stdout, which under streaming is the pipe — it would have been concatenated into the report body. The header status is now parsed out of a file, and is used **only** in diagnostics: it is never a success test, because it arrives before any content. Exit 5 is the success test.
- **An unreadable metadata line appends the truncation note anyway.** If the `research-sse-meta:` line cannot be parsed, `$TRUNCATED` is `unknown`; the leg still keeps the report but adds the note. Over-warning synthesis is much cheaper than letting it read a cut-off section as complete.

**Two verification commands in the brief were vacuous and are recorded here so they are not reused.** `sed -n '/^## Claude/,/^## OpenAI/p'` matches nothing — the heading is `## Anthropic Claude Protocol`. The "no `stop_reason` remains" check therefore passed on an empty range (a false pass), and the "streaming present" check produced no output despite the content being there (a false miss). Re-run against `/^## Anthropic Claude Protocol/,/^## OpenAI/`: 132 lines in range, zero `stop_reason` hits, and `--no-buffer`, `"stream": true` and `PIPESTATUS` all present. Same class as E063: a check expressed from what the author expected to match rather than derived from the artifact.

#### 6.3 Reconcile the skill body and the model reference ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #216 (blast radius)
**Depends On:** 6.2
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify)
- `plugins/personal-plugin/references/research-models.md` (modify)

**Description:**

The skill body independently restates the leg's mode, its parse target, and its silent-failure mechanism — the last of which becomes **wrong** under streaming, because the terminal reason is no longer a top-level field. The model reference restates the mode and carries the rationale paragraph that argues from the transport constraint.

Also correct the rationale's sourcing. The output-ceiling requirement it cites is real and current, but the wall-clock derivation built on it is an unsourced estimate, and the repo states the requirement in bare prose with no citation — the same unbacked-assertion shape a prior phase deleted elsewhere.

**Tasks:**

1. [x] Update the mode, parse-target, and silent-failure rows in the skill body.
2. [x] Update the "no real-time streaming progress" note, which becomes misleading.
3. [x] Update the mode row and rationale paragraph in the model reference.
4. [x] Mark the wall-clock derivation as an estimate, or remove it, rather than restating it as fact.
5. [x] Leave the cost table alone — the ladder is unchanged, so costs are unchanged.

**Acceptance Criteria:**

- [x] WHEN the skill body's silent-failure row is read THEN it SHALL describe the streaming mechanism, not the top-level-field one
- [x] WHEN the rationale is read THEN any unsourced numeric derivation SHALL be marked as an estimate or absent
- [x] The cost table is byte-identical to `main`
- [x] The depth ladder values are byte-identical to `main` in both files

**Notes:**

Leaving the skill body's silent-failure row stale would tell a future reader the guard works one way while it works another — the stale-contract shape a prior issue was filed about.

#### 6.4 Grant the missing execution permission ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: haiku**
**Recommendation Ref:** Latent defect found during #216 investigation, not filed
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/research-topic/SKILL.md` (modify — frontmatter only)

**Description:**

The skill's tool grants cover the transport binary but **not** the interpreter that the shipped fast-fail check and both other providers' extraction steps already invoke. Six other skills in the same plugin grant it, so this is an oversight rather than policy. The prior live verification ran through a standalone probe rather than a real dispatch, which is why this has never surfaced.

The streaming rewrite deepens the dependency, so the grant must land with it.

**Tasks:**

1. [x] Add the interpreter grant to `allowed-tools`.
2. [x] Verify no other binary invoked anywhere in the three files lacks a grant.
3. [x] Verify the frontmatter parses with a full key set after the edit — this frontmatter is a plain scalar list and is exactly the shape that has silently dropped before.

**Acceptance Criteria:**

- [x] WHEN the frontmatter is parsed THEN the interpreter grant SHALL be present and every pre-existing key SHALL remain
- [x] Every binary invoked in the three files has a corresponding grant
- [x] `claude plugin validate plugins/personal-plugin --strict` exits 0

**Notes:**

A dispatch-time-only failure is the hardest class to catch, because every offline gate passes.

#### 6.5 Commit the live probe and add an eval scenario ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #216 (verification gap)
**Depends On:** 6.2
**Files Affected:**
- `scripts/` or `tests/live/` (create — owner-run probe)
- `evals/skills/research-topic.eval.md` (modify)

**Description:**

The prior fix was verified by a probe that extracted the request body and ladder from the shipped files — so it could not pass while those files were broken — and **that probe was never committed**. The single artifact proving the fix existed is gone. Commit this one.

CI holds zero secrets and cannot run it, so it is explicitly owner-run. It needs a negative control: a deliberately-invalid request shape must fail, or the probe proves only that the network works.

Separately, the eval suite has **no scenario for depth, parameters, or the response parse at all** — so a broken parser or a wrong ladder value passes it untouched. Add one.

**Tasks:**

1. [x] Commit a probe that extracts the request shape and ladder from the shipped files rather than restating them.
2. [x] Give it a negative control that must fail.
3. [x] Mark it clearly as manual-run, with the zero-secrets constraint stated.
4. [x] Add an eval scenario covering the parse path and the terminal-reason handling.

**Acceptance Criteria:**

- [x] WHEN the shipped request shape is broken THEN the probe SHALL fail
- [x] WHEN the probe's negative control runs THEN it SHALL fail as designed
- [x] `python3 scripts/check_eval_mapping.py` exits 0 with the new scenario
- [x] No CI workflow references the probe

**Notes:**

"Derive it, don't restate it," applied to a probe: extracting from the shipped files is what makes it impossible to pass against a broken tree.

### Phase 6 Testing Requirements

Every guard gets a fixture **and** a mutation test. This is the phase where the standing rule matters most: a guard that cannot fail is worse than none, and the specific guard at risk here has already been mutation-tested once and would silently regress under a faithful-looking port.

### Phase 6 Completion Checklist

- [ ] All five items COMPLETE
- [ ] Depth ladder byte-identical to `main` in both files that state it
- [ ] Cost table byte-identical to `main`
- [ ] Every accumulator guard has a passing mutation test
- [ ] Version bumped and CHANGELOG entry added

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| Accumulator suite | `cd plugins/personal-plugin/tools/research-sse && python -m pytest -q` | exit 0 |
| Ladder unchanged | `git diff main -- plugins/personal-plugin/references/research-models.md \| grep -E '^[+-]' \| grep -cE '8,?000\|16,?000\|32,?000'` | output `0` |
| Cost table unchanged | `! git diff main -- plugins/personal-plugin/references/research-models.md \| grep -E '^[+-][^+-]' \| grep -qE '\$[0-9]'` | exit 0 |
| Interpreter grant present | `python3 -c "import yaml,pathlib,sys; d=yaml.safe_load(pathlib.Path('plugins/personal-plugin/skills/research-topic/SKILL.md').read_text().split('---')[1]); sys.exit(0 if 'python3' in d['allowed-tools'] else 1)"` | exit 0 |
| Frontmatter integrity | `python3 -c "import yaml,pathlib,sys; d=yaml.safe_load(pathlib.Path('plugins/personal-plugin/skills/research-topic/SKILL.md').read_text().split('---')[1]); sys.exit(0 if {'name','description','allowed-tools'} <= set(d) else 1)"` | exit 0 |
| Evals | `python3 scripts/check_eval_mapping.py` | exit 0 |
| Probe is not CI-wired | `! grep -rq 'research-sse-probe\|tests/live' .github/workflows/` | exit 0 |
| Official validation | `claude plugin validate plugins/personal-plugin --strict` | exit 0 |
| Release gate | `python3 scripts/check_version_bump.py --base main` | exit 0 |
| Lint (mirrors CI exactly) | `npx markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'` | exit 0 |

<!-- END DOD -->

---

## Phase 7: SKILL.md Body Budget — Fix, Then Gate

### Goals

Bring the two over-budget bodies back under the line, then land a gate that is **green on arrival**. A red-on-arrival gate reddens the push build on the default branch and deadlocks subsequent merges — the recorded hazard from a prior gate.

A ratchet is **rejected on this repo's own precedent**: a count-ratchet was adopted once against 152 pre-existing errors, then retired with the finding that it was scaffolding whose only remaining feature was an escape hatch contradicting the standard it enforced. The entire debt here is two files and 64 excess lines.

### Work Items

#### 7.1 Extract `lab-notebook`'s two verbatim templates ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #238
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/lab-notebook/SKILL.md` (modify)
- `plugins/personal-plugin/skills/lab-notebook/references/` (create — two files)

**Description:**

Two large fenced blocks are pure emit-this-verbatim templates: a ~116-line injection template and a ~98-line notebook-structure skeleton. Both are exactly what the wiki-creation skill already externalizes, and that skill — not the ship skill — is the correct exemplar to copy. It reads its templates at runtime and emits them verbatim, and the audit itself names it as proving the pattern.

Extracting both lands the body around 330 lines with substantial headroom, so this skill never returns to this issue.

Pointers must carry an inline summary of the load-bearing content, so the skill stays executable without pre-reading every reference — the constraint a prior audit established. The skill's existing rotation-reference pointer is the in-file model for that shape.

**Tasks:**

1. [x] Extract both templates into the skill's own references directory.
2. [x] Replace each with a pointer that **disambiguates the location explicitly** — the two skills that got this right say so in the pointer text, and the ship skill's bare relative path is ambiguous.
3. [x] Keep the verification checklist inline as the summary, since it references the extracted content.
4. [x] Confirm the emitted output is byte-identical to what the inline template produced.

**Acceptance Criteria:**

- [x] WHEN the skill runs THEN the content it emits SHALL be byte-identical to the pre-extraction template
- [x] WHEN a pointer is read THEN it SHALL state unambiguously which directory the reference lives in
- [x] The body is under 500 lines
- [x] `python3 scripts/check_injections.py` exits 0

**Notes:**

Byte-identical emission is the acceptance criterion. An extraction that subtly reformats the template changes what the skill writes into other repositories' `CLAUDE.md` files.

#### 7.2 Extract `visual-explainer`'s output samples ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Recommendation Ref:** #238
**Depends On:** Phase 5.2
**Files Affected:**
- `plugins/personal-plugin/skills/visual-explainer/SKILL.md` (modify)
- `plugins/personal-plugin/skills/visual-explainer/references/` (create)

**Description:**

Three illustrative output samples total roughly 112 lines. Extracting them lands the body near 417 with real headroom.

**Extract illustration only, never logic.** The interaction payloads in this skill are behavioural — the model must emit them — and stay inline. This is the illustration-versus-logic distinction the repo pre-authorized after a prior escalation caused by exactly this ambiguity.

This item depends on Phase 5.2, which edits the same file's environment-variable documentation.

**Tasks:**

1. [x] Extract the three output samples to a references file.
2. [x] Replace each with a one-line pointer carrying an explicit location.
3. [x] Leave every interaction payload inline.
4. [x] Confirm Phase 5.2's documentation edit is intact.

**Acceptance Criteria:**

- [x] WHEN the body is measured THEN it SHALL be under 500 lines
- [x] Every interaction payload remains inline
- [x] Phase 5.2's environment-variable documentation is present and correct

**Notes:**

This file grew past the budget as a side effect of a prior remediation whose replacement blocks were longer than what they replaced. That is the case for the gate, and it belongs in the commit message.

#### 7.3 Build and wire the budget gate ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: opus**
**Recommendation Ref:** #238 (the gate)
**Depends On:** 7.1, 7.2
**Files Affected:**
- `scripts/check_skill_budget.py` (create)
- `.github/workflows/validate.yml` (modify — one step)
- `scripts/pre-commit` (modify — one check)

**Description:**

Build a stdlib-only checker matching the house exemplar's shape: a module docstring carrying the motivating defect and numbered rules, a findings dataclass with a render method, a pure check function separated from an I/O runner with an injectable stream, and a self-test that asserts non-zero exit on every violation class.

**Four design decisions that determine whether it is green on arrival.** Measure the **body** (post-frontmatter), because that is what the rule says — and emit both numbers in any failure. Pin the boundary explicitly and negative-test at 499, 500, and 501, since a boundary bug lives entirely in the unexercised branch. Scope to a **non-recursive** glob over skill directories, mirroring the existing validator's documented reasoning, which also excludes test fixtures. And do **not** extend to commands: they are frozen legacy, and the largest is already over the line — extending scope there is the exact creep that causes the deadlock hazard.

The failure text must state the authoring-quality rationale corrected in Phase 1.2, not the context-economy one.

**Tasks:**

1. [x] Write the checker with a self-test that proves it exits non-zero on an over-budget fixture and zero on a compliant one.
2. [x] Negative-test the boundary at 499/500/501 before wiring.
3. [x] Wire as a **step** in the existing validation job, never a new job.
4. [x] Add a pre-commit check that delegates file selection to the script rather than restating it in shell.
5. [x] Confirm the required-check names are unchanged.

**Acceptance Criteria:**

- [x] WHEN a skill body exceeds the budget THEN the gate SHALL exit non-zero and name the file with both body and total line counts
- [x] WHEN the current tree is checked THEN the gate SHALL exit 0
- [x] WHEN the self-test runs THEN it SHALL assert non-zero exit on at least one over-budget case
- [x] The set of required status check names is unchanged from `main`
- [x] No file under `commands/` is evaluated by the gate
- [x] Test fixtures are not evaluated

**Notes:**

Green on arrival is the criterion, and it depends on 7.1 and 7.2 landing first. Verify it against the current tree before wiring, not after.

**Delivered 2026-07-31.** Predicate pinned in the module docstring and in `BODY_LINE_LIMIT = 500`: a body is a violation **iff `body_lines >= 500`**, so 499 passes, 500 fails, 501 fails. All three values are constructed as real fixtures and run through the pure `check_file` — observed `499 -> PASS`, `500 -> FAIL (over by 1)`, `501 -> FAIL (over by 2)`. The self-test carries the same three plus a 900-line file planted under `commands/`, an over-long file under `skills/*/references/`, one under `tests/fixtures/`, one nested a level deeper than `skills/<name>/`, and a no-frontmatter file (measured whole, fail-closed). 4 of 11 cases assert exit 1. `--filter` (the pre-commit delegation point) is asserted to agree with `in_scope()` on every one of those paths, so the hook cannot drift from the gate. Largest real body is 490 lines — 9 lines of headroom.

**Two DoD rows in this item's own table are unreliable, and both were hit.**

1. `! grep -q 'commands' scripts/check_skill_budget.py` **fails for a correct implementation** (5 hits). The docstring must name `commands/` to explain *why* the exclusion exists, and the self-test case that proves it is named `commands-file-not-evaluated`. The row tests the absence of a word, not the property. Derived replacement, which passes and would catch a real scope leak: `python3 scripts/check_skill_budget.py --self-test` (the planted-`commands/` case is in it), or directly — `printf 'plugins/p/commands/x.md\n' | python3 scripts/check_skill_budget.py --filter` must print nothing.
2. `... .split('---',2)[2].splitlines()) >= 500` **over-counts every body by exactly one**. `parts[2]` begins with the newline that terminates the closing `---`, so `splitlines()` yields a leading empty element that is not a body line. Measured: the idiom reports 491/489/440 where the gate reports 490/488/439. Both are green today, but at the boundary the row would fail a file the gate passes. Replace it with the gate itself — it is a restatement of an external truth, which is the failure class CLAUDE.md warns about.

**Not ticked:** the Phase 7 Completion Checklist's "Version bumped and CHANGELOG entry added". This item touches only `scripts/` and `.github/`, so it obliges no bump of its own; the bump owed for 7.1/7.2's `plugins/personal-plugin/` edits belongs to item 8.1, which has not run. Ticking it here would be a false claim in the exact place this phase exists to stop them.

### Phase 7 Testing Requirements

Negative-test before wiring, against deliberately-bad input, and confirm non-zero exit. This repo has shipped three guards that could not fail; the boundary case is where the fourth would hide.

### Phase 7 Completion Checklist

- [x] All three items COMPLETE
- [x] Gate green against the current tree — 40 skill bodies checked, 0 over budget, largest 490 (9 lines of headroom)
- [x] Required check names unchanged — the gate is a STEP in the existing `plugin-validate` job; `git diff main` removes or alters no `name:` line and adds exactly one
- [ ] Version bumped and CHANGELOG entry added — **deferred to item 8.1 by design**; 7.3 touches no `plugins/` path, and the bump owed for 7.1/7.2 is 8.1's deliverable

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| Gate green on arrival | `python3 scripts/check_skill_budget.py` | exit 0 |
| Gate can fail | `python3 scripts/check_skill_budget.py --self-test` | exit 0, output asserts ≥1 case expecting exit 1 |
| No skill body over budget | `python3 scripts/check_skill_budget.py` | exit 0. **Row corrected during execution.** As authored it re-implemented the measurement inline via `.split('---',2)[2].splitlines()`, which **over-counts every body by exactly one** — `parts[2]` begins with the newline terminating the closing `---`, so `splitlines()` yields a leading empty element (measured: idiom 491/489/440 vs gate 490/488/439). Green either way today, but at the boundary it would fail a file the gate passes. A row that restates an external truth drifts into disagreeing with it; use the gate itself. |
| Commands not in scope | `printf 'plugins/p/commands/x.md\n' \| python3 scripts/check_skill_budget.py --filter` | prints nothing. **Row corrected during execution.** As authored it was `! grep -q 'commands' scripts/check_skill_budget.py`, which **fails for a correct implementation** — the module docstring must name `commands/` to explain why they are excluded, and the self-test case is literally named `commands-file-not-evaluated` (5 legitimate hits). The derived property is that the glob does not match a `commands/` path, which `--self-test` also proves by planting a 900-line command file. |
| Required check names unchanged | `git diff main -- .github/workflows/validate.yml \| grep -E '^[+-]\s+(name\|jobs):' \| grep -vc 'Check SKILL.md body budget'` | output `0` |
| Injections | `python3 scripts/check_injections.py` | exit 0 |
| Official validation | `claude plugin validate plugins/personal-plugin --strict` | exit 0 |
| Release gate | `python3 scripts/check_version_bump.py --base main` | exit 0 |
| Lint (mirrors CI exactly) | `npx markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'` | exit 0 |

<!-- END DOD -->

---

## Phase 8: Release and Issue Reconciliation

### Goals

Ship the versions and close the issues with their corrections recorded, so the next reader does not re-derive the refuted claims.

### Work Items

#### 8.1 Version bump and CHANGELOG ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Depends On:** Phases 1–7
**Files Affected:**
- `plugins/personal-plugin/.claude-plugin/plugin.json`, `plugins/slide-gen/.claude-plugin/plugin.json`, `plugins/bpmn-plugin/.claude-plugin/plugin.json` (modify as applicable)
- `.claude-plugin/marketplace.json` (modify)
- Per-plugin `CHANGELOG.md` files and root `CHANGELOG.md` (modify)

**Description:**

Bump only the plugins with genuine changes; never issue an empty coordinated bump. `slide-gen` and `bpmn-plugin` change only if Phase 3 touched their skills.

**Tasks:**

1. [ ] Determine which plugins actually changed, from the diff.
2. [ ] Bump each changed plugin in both its manifest and the marketplace file.
3. [ ] Add a CHANGELOG entry per bumped plugin plus a root entry.
4. [ ] State the three doctrine corrections explicitly in the entries — they are the most valuable output and would otherwise be invisible.

**Acceptance Criteria:**

- [ ] WHEN the release gate runs THEN every changed plugin SHALL be bumped with a matching CHANGELOG entry
- [ ] No unchanged plugin is bumped
- [ ] Manifest and marketplace versions agree for every plugin

#### 8.2 Close the five issues with corrections ✅ Completed 2026-07-31

**Status: COMPLETE 2026-07-31**
**Model Tier: sonnet**
**Depends On:** 8.1
**Files Affected:**
- `LAB_NOTEBOOK.md` (modify — living sections)

**Description:**

Each issue closes with its corrections recorded, not silently. Several carry findings that invert what was filed, and a bare "fixed" comment would leave the wrong premise as the last word.

**Do not rely on a comma-separated closing list in the pull request body** — it closes only its leading entries, which left ten issues open on a prior merge. Write the keyword before each number, or close by hand and verify the count.

**Tasks:**

1. [ ] Comment on each issue with its verdict and the evidence, including the refutations.
2. [ ] File a follow-up for the effort A/B measurement, noting the confound is now removed.
3. [ ] File a follow-up for the tier-boundary replay experiment, deliberately not run.
4. [ ] Update the notebook's living sections: Decision Log, Action Items, Current Baseline, open backlog count.
5. [ ] Verify the closed count by listing, not by trusting the merge.

**Acceptance Criteria:**

- [ ] WHEN the issue list is queried after merge THEN the open count SHALL match the predicted set exactly
- [ ] Every closed issue carries a comment stating what was refuted
- [ ] Follow-up issues exist for both deliberately-deferred measurements
- [ ] The Current Baseline reflects the shipped versions

### Phase 8 Completion Checklist

- [ ] Both items COMPLETE
- [ ] Open issue count verified by listing
- [ ] Living sections current

### Definition of Done (Runnable)

<!-- BEGIN DOD -->

| Check | Command | Pass criteria |
|---|---|---|
| Release gate | `python3 scripts/check_version_bump.py --base main` | exit 0 |
| Version sync | `python3 -c "import json,pathlib,sys; m={p['name']:p['version'] for p in json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text())['plugins']}; bad=[n for n,v in m.items() if json.loads(pathlib.Path(f'plugins/{n}/.claude-plugin/plugin.json').read_text())['version']!=v]; print(bad); sys.exit(1 if bad else 0)"` | exit 0 |
| Inventory | `python3 scripts/update-readme.py --check` | exit 0 |
| Lint (mirrors CI exactly) | `npx markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'` | exit 0 |

<!-- END DOD -->

---

## Risk Register

| Risk | Phase | Severity | Mitigation |
|---|---|---|---|
| The refusal guard silently dies when the terminal reason relocates under streaming | 6 | **Critical** | **Mitigated both sides (2026-07-31).** 6.1: the fixture was written first and run red before the accumulator existed; the guard reads `message_delta`, is mutation-tested fail-first (`G1`, `G11`), and `naive_top_level_stop_reason` asserts the old top-level lookup finds nothing. 6.2: the leg branches on `$ACC_EXIT` alone — the payload-inspection block is deleted outright and the section contains **zero** occurrences of the old field name, so there is no surviving lookup to go quiet. Verified live: the refusal fixture returns 4 and the leg discards its 18 characters of partial refusal text rather than writing them. **Fully mitigated (2026-07-31).** 6.3 reconciled both of the skill body's silent-failure restatements (the Provider Deltas row and the Error Handling table row) plus the model reference's mode row and rationale to the exit-status mechanism; no surviving reference to the old top-level `stop_reason` field remains in either file |
| Transport-failure detection lost across the new pipe | 6 | High | **Mitigated (2026-07-31).** `PIPE=("${PIPESTATUS[@]}")` immediately after the pipeline. Negative-tested against the case that would otherwise hide: a transport emitting a *complete-looking* stream and then exiting 28 — the shipped form fails the leg and discards the body, the naive `$?` form reports success |
| Budget gate red on arrival deadlocks the default branch | 7 | High | **Mitigated (2026-07-31).** Both over-budget files were fixed in 7.1/7.2 first, and the gate was run against the real tree **before** the workflow step existed: 40 bodies, 0 findings, largest 490 lines. Scope exclusion of `commands/` is a tested property, not a comment — `--self-test` plants a 900-line file under a `commands/` directory (the largest real command, `implement-plan.md`, is 520 lines and would redden `main`'s own push build) and asserts it is neither globbed nor evaluated even when passed explicitly. Wired as a STEP in the existing `plugin-validate` job, so no new required check appears (D28/PLAT-012) |
| Tier prose names a model generation, recreating the staleness class | 5 | High | Explicit acceptance criterion and a DoD check on the diff |
| `plan-improvements.md` edits from three issues collide | 2, 4 | Medium | Phases serialized; each item lists the regions it must not touch; DoD asserts untouched regions byte-identical |
| Extraction changes what a skill emits into other repositories | 7 | Medium | Byte-identical emission is the acceptance criterion, not a side note |
| Backward-compatibility break in the model knob | 5 | Medium | Unset override must be behaviourally identical to today, tested directly |
| Documenting the keyword mechanism re-triggers it | 1, 2 | Low | Explanations live in commit messages and the notebook, never in a component body |

## Unknowns

| Unknown | Severity | Affects | Resolution strategy |
|---|---|---|---|
| Whether frontmatter outranks the session effort value, or the reverse | Low | Phase 3 framing | Does not change any action — "do not add `effort: high`" holds either way. The plan asserts only the no-op claim, never the removes-user-control claim |
| Whether the real API completes at the top effort tiers within the transport budget | Medium | #216 follow-up only | Out of scope — the ladder is unchanged. The committed probe makes it answerable later |
| Placement of the refusal category under streaming | Medium | Phase 6.1 | **RESOLVED 2026-07-31 by design, not by discovery — still unknown, and no longer needs to be known.** `find_refusal_category` does a depth-bounded search for a `stop_details` (then `refusal`) object anywhere in the terminal event instead of hard-coding a path, and a null/absent category surfaces as `category=unknown` without downgrading the refusal. Four fixtures pin it: category present, category null, `stop_details` absent entirely, and `stop_details` in an unexpected position. Mutation `G10` (collapsing the search to depth 0) flips the row to failing |
| Whether the keyword mechanism's feature gate stays on | Low | Phase 1.1 | Recorded as current behaviour, not a stable contract |

## Scope Boundaries

**In scope:** the corrections and fixes above for #200, #199, #238, #216, #198.

**Explicitly NOT in scope:**

- **The depth ladder change in #216** — owner decision; current guidance for the default model argues against the filed direction.
- **The tier-boundary replay experiment** — owner decision; the one change the evidence supports ships without it.
- **The effort A/B on the two top-tier planners** — remains open as a measurement task. Phase 2.2 removes its confound, which is a precondition for it ever being valid.
- **All three `effort: high` additions from #199** — no-ops.
- **`sonnet-implementer.md`** — its escalation clause is already correctly qualified.
- **`prime`, `finish-document`, `consolidate-documents`, `define-questions`** — misfiled or exemplars.
- **`commands/` line budgets** — frozen legacy; extending the gate there is the deadlock hazard.
- **The historical audit report** — editing it to remove findings it genuinely made would falsify the record.
- **Any default model value in `visual-explainer`** — the economic case rests on a premium that does not reach the assumed figure until after 2026-08-31.

**Recommended follow-up work:** the two deferred measurements; `explain-project` and `accessibility-annotator` banner reduction (both under budget, ~27% and ~34% of their files are decorative comments); `release-plugin`'s fifteen still-inline output templates; and the ambiguous relative pointer in the ship skill.
