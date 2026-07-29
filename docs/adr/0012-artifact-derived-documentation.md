# ADR-0012: Artifact-Derived Documentation — the `paths:` Conditional-Load Gate

**Date:** 2026-07-29
**Status:** Accepted
**Deciders:** Troy Davis (via `/ultra-plan` over the 24-item correctness backlog, LAB_NOTEBOOK E060; `IMPLEMENTATION_PLAN.md` Phase 5.1)

## Context

Issue #202 catalogued eight skill-frontmatter keys as "unverified" and proposed deleting six of them. Investigation (Phase 5's recon pass) found the opposite shape of problem: six of the eight keys are real and shipping — the defect is **correct keys documented with wrong semantics**, not fictional keys. Blindly applying #202's remedy would have deleted working capability from every skill author's toolchain.

The flagship case is `paths:`. Three teaching sites — `references/common-patterns.md`, `references/patterns/advanced-features.md`, and `commands/new-skill.md` — describe it as an **event trigger**: "auto-activates the skill when the user opens or saves a file matching one of the glob patterns." All three then instruct authors to add a **loop guard**, because a skill that writes a file matching its own `paths:` pattern would supposedly "re-trigger indefinitely."

None of that is how the harness implements `paths:`. And the cost was not theoretical: four shipped skills (`spark-audit`, `jetson-audit`, `spark-recon`, `jetson-recon`) built a "Loop Guard — Auto-Activation Safety Check" section against an event that cannot occur, and all four additionally pair `paths:` with `disable-model-invocation: true` — a combination that, once the actual mechanism is understood, **can only make the skill harder to invoke, never easier**.

This ADR generalizes the root cause shared by #193 (bpmn-to-drawio's `HAS_DI` reimplementation diverging from `converter.py`'s actual layout resolution), #194 (hook recipes missing the wrapper/matcher levels that `hooks/hooks.json` actually requires), #196 (visual-explainer documenting an env var — `$GOOGLE_IMAGE_MODEL` — that appears zero times in `config.py`), #202 (this issue), and #218 (a freshness column with no backing mechanism): **documentation of a bundled artifact must be derived from, or verified against, the artifact itself — never from what the feature was proposed to do, what it resembles, or what would be convenient if true.**

### How the facts below were established

Every claim about `paths:` is read out of the shipped harness — Claude Code **2.1.220**, `~/.local/share/claude/versions/2.1.220` — the same pinned build ADR-0011 used, recovered the same way: `strings -n 6` over the binary (it is a Bun single-file executable; the bundled JS is plaintext inside it, not obfuscated at the identifier level) followed by targeted `grep` for the literal keys and function bodies, not inference from observed behavior and not taken from a subagent's summary. The functions below are quoted verbatim (minified names kept, since a renamed function is no longer a verbatim quote):

```js
// paths: normalizer — called once per skill file at load time
function sn_(e){
  if(!e.paths) return;
  let t = Zno(e.paths)
    .map((r) => r.endsWith("/**") ? r.slice(0,-3) : r)
    .filter((r) => r.length > 0);
  if(t.length === 0 || t.every((r) => r === "**")) return;
  return t
}

// top-level skill loader — after collecting every skill file `g`:
let _ = [], E = [];
for (let A of g)
  if (A.type === "prompt" && A.paths && A.paths.length > 0
      && !sae().activatedConditionalSkillNames.has(A.name))
    E.push(A);
  else
    _.push(A);
for (let A of E) sae().conditionalSkills.set(A.name, A);
if (E.length > 0)
  w(`[skills] ${E.length} conditional skills stored (activated when matching files are touched)`);
return _;   // <- only the UNCONDITIONAL list is returned from the loader

// the activator — `e` is the touched path(s), `t` is the project root
function gn_(e, t) {
  if ((ocn()?.conditionalSkills.size ?? 0) === 0) return [];
  let r = [];
  for (let [n, o] of sae().conditionalSkills) {
    if (o.type !== "prompt" || !o.paths || o.paths.length === 0) continue;
    let i = mMd.default().add(Ult(o.paths, "skill_paths"));   // `ignore`-package matcher
    for (let s of e) {
      let a = E_.isAbsolute(s) ? E_.relative(t, s) : s;
      if (!a || a.startsWith("..") || E_.isAbsolute(a)) continue;
      if (i.ignores(a)) {
        sae().dynamicSkills.set(_Md(o), o);
        sae().conditionalSkills.delete(n);
        sae().activatedConditionalSkillNames.add(n);   // <- one-shot: never processed again
        r.push(n);
        w(`[skills] Activated conditional skill '${n}' (matched path: ${a})`);
        break
      }
    }
  }
  return r;
}

// the sole caller of gn_ — takes one touched path
async function tur(e, t) {
  let r = Ht(), n = await hn_([e], r);
  if (n.length > 0) { /* dynamic skill-dir discovery, unrelated to paths: */ }
  gn_([e], r)
}
```

`tur()` is called from exactly three places, confirmed by grepping the surrounding tool-handler bodies:

- The **Read** tool's `call()`: `await tur(f, o.dynamicSkillDirTriggers)`
- The **Edit** tool's `call()`: `await tur(y, u)`
- The **Write** tool's `call()`: `await tur(p, d)`

And the skill-visibility assembly that every invocation path (model **and** user) resolves through:

```js
async function nw(e) {
  let t = await GBo(e), r = ATo(), n = ...;     // t = unconditional loader output
  let o = t.filter(...);
  if (r.length === 0 && n.length === 0) return o;
  let i = r.filter(...);                         // r = ATo() = activated conditionalSkills only
  ...
}
function ATo() {
  return Array.from(ocn()?.dynamicSkills.entries() ?? []) ...
}
async function tRs(e) {
  let t = ...mcp commands..., r = await nw(Rl()), n = efr();
  return M7(VNy([...r, ...n, ...t]));
}
function Cv(e, t) {                              // by-name/alias lookup
  let r;
  return t.find((o) => { if (o.name === e) return !0; ... }) ?? r;
}
```

The SkillTool's `validateInput` — the gate every invocation (a model-issued Skill tool call **or** a user typing `/skill-name`) passes through — calls `let s = await tRs(t), a = Cv(o, s)`, and returns `Unknown skill: <name>` if `a` is undefined. `tRs`'s only sources are `nw()` (unconditional + **activated** conditional) and `efr()`; `sae().conditionalSkills` (not-yet-activated) is never consulted.

## Decision

### The four facts

**F1 — `paths:` is a conditional-existence gate, not an event trigger.** A skill declaring a non-empty, non-`**`-only `paths:` list is **not returned by the skill loader at all**. It is held in a separate `conditionalSkills` map and is invisible to every lookup path — including a user typing the skill's own slash command on a fresh session — until it is moved into `dynamicSkills` by `gn_`. There is no "the skill runs when a file changes." There is "the skill does not exist yet."

**F2 — Activation fires on Claude's own Read, Edit, or Write tool calls touching a matching relative path, once per session, and never again.** `tur()`'s three call sites are the tool handlers themselves — not a filesystem watcher, not a git hook, not an external-process notification. A file changed by `git checkout`, another process, or a human editing outside the session activates nothing. Once `gn_` matches a skill, its name is added to `activatedConditionalSkillNames` and the entry is deleted from `conditionalSkills`, so the match loop skips it forever after — activation is a one-time, monotonic transition per session, not a recurring event.

**F3 — Because activation only ever adds visibility, it cannot re-trigger, and no loop guard has anything to guard against.** "Auto-activation" in the documentation implied the skill's body would re-execute on every matching write. The mechanism does not execute the skill body at all — it only changes whether `Cv()` can find the skill by name. A skill that writes its own trigger file after activation changes nothing: `activatedConditionalSkillNames` already contains its name, so `gn_`'s match loop `continue`s past it on every subsequent call. The four "Loop Guard — Auto-Activation Safety Check" sections removed by this ADR (§ Tasks) were defending against a state transition the harness structurally cannot produce.

**F4 — Pairing `paths:` with `disable-model-invocation: true` is not merely redundant — it is a strict availability regression.** `disable-model-invocation: true` restricts *who* may invoke an already-visible skill (Claude never; only a user via slash command). `paths:` restricts *whether the skill is visible at all this session* (only after Claude's own Read/Edit/Write touches a match — F1, F2). A skill carrying both is invisible to `Cv()`/`tRs()` for **everyone**, Claude and the human user alike, until Claude happens to touch a matching file for some unrelated reason — which a `disable-model-invocation: true` skill, by construction, never gives Claude a reason to go looking for. A user who wants to run `/spark-audit` on turn one of a fresh session gets `Unknown skill: spark-audit`. Omitting `paths:` entirely would have made the skill invocable from the first turn; adding it can only ever subtract availability for this class of skill.

### The rule this repo adopts

**R1 — A frontmatter behavior claim is only as good as its most recent probe against the shipped harness.** Every "auto-activates," "triggers," or "runs when" claim in a teaching document must cite the mechanism that produces it (a specific function, tool-handler call site, or config field) or be deleted. A claim inferred from the key's name, from what a similar tool in another ecosystem does, or from what the feature was originally proposed to do in a planning document is not a substitute and has produced four confirmed defects in this repo (#193, #194, #196, #202) plus one confirmed-fictional claim (#218).

**R2 — `paths:` is documented as a conditional load gate, in these exact terms: invisible until touched, activated by Claude's own Read/Edit/Write, one-shot per session, no loop guard.** All three teaching sites (`common-patterns.md`, `advanced-features.md`, `commands/new-skill.md`) are corrected to this wording. The `.gitignore`-style glob semantics the prior text described were independently confirmed (`gn_` builds its matcher with the `ignore` npm package via `.add()`/`.ignores()`) and are retained.

**R3 — `paths:` + `disable-model-invocation: true` is resolved per skill, not banned outright.** The combination is legitimate only if something *other than the gated skill's own invocation* benefits from the file-touch signal (there is no such case identified in this repo today). Where a skill's design intent is "invoked directly by a human at will" (the four fleet audit/recon skills — their own descriptions say "run periodically," implying on-demand, not conditional), `paths:` is removed and `disable-model-invocation: true` is kept. Where a skill's design intent is "Claude notices a relevant file changed and considers acting on it" (`security-analysis`, which carries no `disable-model-invocation`), `paths:` is kept and the body text is corrected from "triggered automatically" to "becomes available for you to consider invoking."

**R4 — The same probe technique ADR-0011 established (`strings` over the pinned binary, `grep` for literal schema keys and function bodies, verified call sites, not behavioral inference) is the required method for any future frontmatter-semantics claim**, per R1. It settled `paths:` here exactly as it settled the injection-escaping rule in ADR-0011: by reading the loader and the three tool handlers that call into it, not by re-reading the four sites that were already wrong.

## Alternatives Considered

### Delete `paths:` from the documentation entirely, per #202's literal text

- **Description:** Treat `paths:` as unverified and remove all teaching-site coverage of it, matching #202's proposed remedy.
- **Pros:** Zero risk of documenting the wrong mechanism again; simplest possible diff.
- **Cons:** `paths:` is real, shipping, load-bearing in `security-analysis` today, and independently useful for exactly the case F4 describes as legitimate (a model-invocable skill that should surface when a relevant file appears). Deleting it removes a real capability to fix a documentation defect — the mistake this entire plan phase exists to correct.
- **Why rejected:** #202 conflated "documented wrong" with "doesn't exist." This ADR's Context section is the record of why that conflation happened and why the corrected finding inverts the remedy.

### Keep the loop-guard instruction as defensive programming, even if unnecessary

- **Description:** Leave the "Loop Guard — Auto-Activation Safety Check" sections in place on the theory that an unnecessary guard is harmless insurance against a future harness change.
- **Pros:** Costs nothing if the mechanism never changes; the guard code, if ever needed, is already written.
- **Cons:** It teaches every future skill author, correctly reading the current SKILL.md files as reference examples, that `paths:` re-triggers and must be guarded — actively propagating the F3 misunderstanding into every skill scaffolded by copying this pattern. A guard against an impossible event is not neutral documentation; it is a load-bearing lie about the mechanism, structurally identical to the dead injection guards ADR-0011 found in `prime` and `explain-project`.
- **Why rejected:** ADR-0011's R5 standard — injected content must be optional, never load-bearing, and its guard-worthiness must match the real failure mode — applies here by the same logic. A guard for a defect class that cannot occur is not defense in depth; it is noise that will be trusted the next time someone reads these files as a template.

### Fix only the four fleet skills, leave the three teaching sites as-is

- **Description:** Since the immediate harm (dead loop guards, self-cancelling pairing) lives in the five SKILL.md files, correct only those and leave `common-patterns.md`/`advanced-features.md`/`new-skill.md` for a later pass.
- **Pros:** Smaller diff; the generator-layer fix could be sequenced independently.
- **Cons:** `commands/new-skill.md` is the generator every future skill is scaffolded from (ADR-0006). Leaving its `paths:` row and loop-guard gotcha wrong guarantees the next `paths:`-using skill reintroduces the identical dead guard within a week — the exact "generator layer is the highest-leverage surface in the repo" finding that makes Phase 5 its own phase in this plan.
- **Why rejected:** Fixing the five skills without fixing the generator they were originally written against treats the symptom in five places while leaving the propagation mechanism live for the sixth.

## Consequences

### Positive

- The four fleet skills no longer carry dead "Auto-Activation Safety Check" sections that would mislead a maintainer reading them as a reference for how `paths:` works.
- `security-analysis` keeps its legitimate `paths:` gate, now correctly described, instead of being caught by an over-broad #202-style deletion.
- `spark-audit`, `jetson-audit`, `spark-recon`, `jetson-recon` become invocable by a human on turn one of a fresh session again — F4's availability regression is closed by removing `paths:` where it served no purpose.
- Future `/new-skill`-scaffolded skills using `paths:` inherit correct semantics and no dead-code guard.

### Negative

- The four fleet skills lose whatever future value `paths:` might have offered them if Claude were ever given a reason to touch `SPARK_BASELINE.md`/`*_CONFIG.md` for an unrelated purpose while `disable-model-invocation` were also relaxed — a hypothetical redesign, not a capability these skills exercise today, so the loss is theoretical against a documented, present-tense correctness bug.
- Like ADR-0011's R4, this ADR's evidence is pinned to Claude Code 2.1.220's internal, unversioned function shapes (`sn_`, `gn_`, `tur`, `nw`, `Cv`, `tRs`). A harness update could change any of it silently; re-verification against a new pinned version is manual, with no automated trigger.

### Neutral

- The conditional-load mechanism can be disabled outright (`fd("skills")` reduced-mode checks, `Z.CLAUDE_CODE_SIMPLE` gating the `tur()` call sites) — under those conditions `paths:`-gated skills behave as if `paths:` were absent from the loader's perspective in ways this ADR does not fully enumerate; that surface is out of scope here and does not change F1–F4 under normal operation.

## References

- LAB_NOTEBOOK E060 — `/ultra-plan` over the 24-item backlog; the investigation that found #202's remedy inverted.
- `IMPLEMENTATION_PLAN.md` Phase 5, item 5.1 — the work item this ADR documents; items 5.2–5.6 correct the remaining Phase 5 findings (`hooks:` shape, fictional-key deletion, enum corrections, `/schedule` fleet-skill usage, tier aliases) against the same doctrine.
- ADR-0011 (dynamic-injection doctrine) — the precedent for both the probe method (decompile the pinned binary, don't infer from behavior) and the standard ("recovered by replay, not reasoning").
- ADR-0006 (skills-first authoring policy) — the generator layer (`commands/new-skill.md`) this doctrine governs.
- `plugins/personal-plugin/skills/{spark-audit,jetson-audit,spark-recon,jetson-recon,security-analysis}/SKILL.md` — the five surfaces corrected alongside this ADR.
- Claude Code 2.1.220, `sn_` / `gn_` / `tur` / `nw` / `Cv` / `tRs` / `ATo` — the primary source for F1–F4.
