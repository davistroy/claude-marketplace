# ADR-0011: Dynamic-Injection Doctrine — Parse-Time, Fail-Closed, Permission-Checked, and Inversely Escaped

**Date:** 2026-07-28
**Status:** Accepted
**Deciders:** Troy Davis (via `/ultra-plan` over the 24-item correctness backlog, LAB_NOTEBOOK E059/E060; `IMPLEMENTATION_PLAN.md` Phase 1.1)

## Context

Skill and command bodies in this repo may contain *dynamic injections*: a shell command whose stdout is spliced into the prompt before the model ever sees it. Five surfaces teach the syntax (`commands/new-skill.md`, `references/templates/skill.md`, `references/common-patterns.md`, `references/patterns/advanced-features.md`, `references/new-skill-examples.md`) and every skill scaffolded by `/new-skill` inherits what they say.

What they said was wrong in the two ways that matter most:

- `references/patterns/advanced-features.md:132` stated **"failure is silent — if the command fails (non-zero exit), the output is empty, no error is surfaced to Claude."** The opposite is true: a non-zero exit throws, and the skill never reaches the model at all.
- No surface stated the escaping rule, and the rule is counterintuitive enough that nobody derived it. The *tidier-looking* documentation form is the one that executes.

The cost was not theoretical. E059 found two shipped components — `/new-skill` and `/leak-risk-audit` — failing on **every** invocation in **every** directory, neither filed as a crash, because their authors wrote documentation *about* the syntax that accidentally became the syntax. In the other direction, the two largest blocks cited in issue **#183** (`prime`, 7 sites; `explain-project`, 2 sites) turned out to execute nothing at all, so half of that issue's remediation list was work on dead text — and "tidying" those backticks would have switched on seven shell executions that have never run.

Underlying all of it: **nobody could tell a live injection from an inert one by reading it**, and the repo had no written statement of the semantics to check against. This ADR is that statement.

### How the facts below were established

Every claim here is read out of the shipped harness — Claude Code **2.1.220**, `~/.local/share/claude/versions/2.1.220` — not inferred from behavior and not taken from a subagent's summary (E039). The relevant functions were recovered from the binary and are quoted verbatim:

```js
// the pre-pass
function Jds(e){
  return e.replace(/`[^`\n]+`/g, (t, r) => {
    let n = e[r-1];
    return n === "!" || n === "`" ? t : "`" + Mm(" ", t.length - 2) + "`"
  })
}

// the extractor
function Cfo(e){
  let t = e.matchAll(soy),
      r = e.includes("!" + "`") ? Jds(e).matchAll(aoy) : [],
      n = [];
  for (let o of [...t, ...r]) { let i = o[1]?.trim(); if (i) n.push({ raw: o[0], command: i }) }
  return n
}
// soy is written here as a concatenation rather than a literal, because a literal
// !-fence in this file would itself be a live injection — see F1.
soy = new RegExp("``" + "`!" + "\\s*\\n?([\\s\\S]*?)\\n?" + "``" + "`", "g")
aoy = /(?<=^|\s)!`([^`]+)`/gm

// the executor
async function WFe(e, t, r, n){
  let o = e;
  return await Promise.all(Cfo(e).map(async ({ raw: s, command: a }) => {
    try {
      let l = await cM(i, { command: a }, t, qT({ content: [] }), "");
      if (l.behavior !== "allow") throw new gye(`Shell command permission check failed for pattern "${s}": ...`);
      let { data: c } = await i.call({ command: a }, t);
      o = o.replace(s, () => ...)
    } catch (l) { if (l instanceof gye) throw l; en_(l, s) }
  })), o
}

// the error path
function en_(e, t){
  if (e instanceof p8) {                                  // shell error
    if (e.interrupted) throw new gye(`Shell command interrupted for pattern "${t}": ...`);
    throw new gye(`Shell command failed for pattern "${t}": ...`)   // <- non-zero exit lands here
  }
  throw new gye(...)
}
```

The behavior of `Jds` + `Cfo` was then independently re-implemented in Python and replayed over every markdown file under `plugins/`, and the replay was **negative-tested before its zeros were trusted** (E043): a one-line fixture in the tidy form must report LIVE, and a one-line fixture in the nested form must report INERT. Without that, "0 live" is indistinguishable from a broken checker — which matters more than usual here, because the entire finding rests on one subtlety of the pre-pass.

## Decision

### The five facts

**F1 — There are exactly two live forms, and one of them is never pre-passed.**
`Cfo` unions two matchers. `soy` matches a fenced block whose info string is `!` (three backticks, then `!`) and runs **against the raw text** — `Jds` is not applied to it, so a `!`-fenced block is live no matter what surrounds it, including inside material an author believes is a quoted example. `aoy` matches the inline marker, but only **after** `Jds` has rewritten the text.

**F2 — The escaping rule is inverted.**
`Jds` blanks every single-line inline-code span **unless the character immediately before its opening backtick is `!` or a backtick**. Blanking preserves length (backtick, *n* spaces, backtick), so a blanked span cannot contribute an `!` for `aoy` to anchor on. The consequence runs exactly opposite to intuition:

> **Notation for this section.** Dangerous forms below are written with `\!` — a backslash-escaped exclamation mark — because writing them literally would make this ADR itself a live injection site. The backslash is the harness's own neutralizer (`Aee()` does `.replace(/(^|\s)!/gm, "$1\\!")`); it is not part of the syntax. Safe forms are written exactly as they should appear in a real file.

| Source form | What the author thinks it is | Reality |
|---|---|---|
| `` `` \!`cmd` `` `` — double-backtick wrapper with space padding | correctly-escaped documentation | **LIVE** |
| `` `!`cmd`` `` — single backtick, nested, ragged | sloppy, obviously broken | **INERT** |
| `` \!`cmd` `` bare at the start of a line | live, and it is | **LIVE** |
| `` \!`cmd` `` inside a plain triple-backtick fence | a quoted example | **LIVE** |
| a fenced block opened with three backticks and `!` | a quoted example | **LIVE** (F1 — never pre-passed) |
| `` \!`cmd` `` in a markdown table cell | a doc table | **LIVE** |
| `` x\!`cmd` `` — any non-whitespace immediately before the marker | live | **INERT** (`aoy` lookbehind fails) |
| `` `` \! `cmd` `` `` — a space between the marker and the backtick | live | **INERT** |
| `` \!`cmd` `` with a literal backslash before the marker | escaped | **INERT** |

The pattern: **every author who "properly escaped" a documentation example by the ordinary markdown convention thereby created a live shell execution, and every author who nested backticks sloppily created dead text.**

**F3 — A non-zero exit aborts skill load. It does not degrade to empty output.**
The Bash tool rejects with a shell error (`p8`), `en_` converts it to a `gye`, the `catch` re-throws it, the enclosing `Promise.all` rejects, prompt expansion fails, and **the skill never reaches the model**. There is no partial prompt, no empty string, and no `[Error]` placeholder in the body. Every live injection is therefore a **load-time precondition** on the skill: it must exit 0 in every directory the skill can be invoked from.

**F4 — Injections are permission-checked against `allowed-tools` before they run.**
`cM(...)` is the ordinary Bash permission check. A `behavior !== "allow"` result throws the same `gye` as a shell failure — so a skill whose `allowed-tools` omits a binary its injection calls fails to load for that reason alone, with no prompt to the user. Every binary in an injection pipeline (`git`, `grep`, `awk`, `tail`, …) must appear in the grant set, pipes included.

**F5 — Expansion happens at parse time, before `$ARGUMENTS` exists.**
`WFe` operates on the body before argument substitution, so a placeholder that the author intends to be filled from `$ARGUMENTS` reaches bash literally. E059 measured this: `leak-risk-audit`'s injected `ls -la <dataset-path>` exited **2** — a bash syntax error, because the unsubstituted angle brackets parse as redirects — in every directory. `skills/arch-review/SKILL.md:44` had already documented the identical failure for its own `TARGET_PATH`; the knowledge existed in the repo and had simply not propagated.

### The five rules this repo adopts

**R1 — Documentation writes the nested form.** Any surface that *shows* the syntax rather than *using* it writes `` `!`cmd`` `` (single backtick, nested). It is inert by F2 and it is the established house form as of 11.5.1. The tidy double-backtick form is banned in every file under `plugins/`, including `references/` and `deprecated/`, which are inert today only by accident of where they are loaded from.

**R2 — Every live injection must exit 0 everywhere and be fully granted.** Guard with `2>/dev/null || echo "(sentinel)"` and branch on the sentinel in the skill body, per F3; list every binary the pipeline invokes in `allowed-tools`, per F4. A guard is not optional politeness — an unguarded injection is a skill that cannot load.

**R3 — Never inject a command containing an argument-derived placeholder.** By F5 there is nothing to guard: the design is impossible, not fragile. The fix is to delete the injection framing and invoke the Bash tool from the model with the resolved path — not to wrap the impossible command in `|| true`.

**R4 — A linter for this class MUST replay the pre-pass. Grepping is not an acceptable implementation.** This is the operative rule and the reason the ADR exists. A textual search for the marker finds **74** occurrences under `plugins/`; **14** of them are live in an executable surface. A grep-based gate is wrong in *both* directions at once — it reports inert documentation as a defect (60 false positives, which trains reviewers to ignore it) and it cannot see that a `!`-fenced block inside a quoted example is live (F1). Only a checker that ports `Jds` and both extractor regexes can distinguish them. Such a checker must be negative-tested against a tidy-form and a nested-form fixture before its output is trusted (E043), and it must be re-validated against the harness whenever the pinned Claude Code version moves, since `Jds`/`Cfo` are internal and unversioned.

**R5 — Injected content is optional, never load-bearing.** `disableSkillShellExecution` (policy setting or `CLAUDE_CODE_IS_COWORK`) replaces every injection with the literal string `[shell command execution disabled by policy]`, and a shared-memory skill ignores capability frontmatter and does not run inline shell at all. A skill must still function, with degraded context, when its injections return that string.

## Alternatives Considered

### A grep-based injection gate

- **Description:** Add a CI step and a pre-commit check that greps for the marker and fails on any occurrence outside an allowlist.
- **Pros:** Ten lines of shell; no dependency on harness internals; trivially portable; nothing to keep in sync when Claude Code updates.
- **Cons:** Wrong in both directions simultaneously. 74 textual hits vs 14 live sites means an ~81% false-positive rate on day one, which guarantees the allowlist grows until it is the only thing the gate consults — the E043 failure mode, a guard that has been argued into never firing. And it under-reports: a `!`-fenced block is live regardless of surrounding context (F1), so a grep tuned to the inline marker misses the form with the *largest* blast radius. Worst of all, it inverts the sign of the escaping rule for anyone reading its output, since the form it flags most loudly (the nested one) is the safe one.
- **Why rejected:** It would have "passed" this repo on the day two components were crashing on every invocation. R4 exists specifically to foreclose this option.

### Ban dynamic injection entirely

- **Description:** Forbid live injections in all authored surfaces; require every skill to fetch context via a model-issued Bash tool call instead.
- **Pros:** Eliminates the defect class outright. No pre-pass to replay, no guards to audit, no permission coupling between `allowed-tools` and injected pipelines. Sidesteps F3 and F4 completely.
- **Cons:** Throws away the feature's actual value — `ship` and `clear-prep` legitimately need git state *in the prompt* rather than as a mid-skill tool round-trip, and forked subagents (which have no conversation history) can only receive pre-loaded context this way without a disk roundtrip. It also would not have prevented E059: those two crashes came from documentation *about* the syntax, which a usage ban does not touch.
- **Why rejected:** The defect is unwritten semantics, not the feature. Banning it would remove the capability and leave the actual failure mode (F2, in prose) in place.

### Neutralize documentation with an invisible character or HTML entity

- **Description:** Break the marker in documentation with a zero-width space or `&#33;` so it renders identically to the live form while remaining inert.
- **Pros:** Documentation would display the syntax *exactly* as it should be typed, which the nested form does not quite manage.
- **Cons:** Invisible damage. A reviewer cannot see the difference between a neutralized and a live example in a diff, `grep` cannot find either reliably, and copy-pasting from the rendered doc silently carries the neutralizer into a real skill where it produces a marker that never fires and never explains why. It optimizes the one thing that does not matter (pixel fidelity of a code sample) at the cost of the thing that does (a human being able to audit the file).
- **Why rejected:** The whole point of R1 is that live and inert must be *visually distinguishable in source*. A neutralizer designed to be invisible defeats it. The `\!` notation used in this ADR is the deliberate opposite — visible, greppable, and self-explaining.

### Document the rule and rely on review

- **Description:** Fix the prose in `advanced-features.md`, add the gotcha to `/new-skill`, and trust code review to catch regressions.
- **Pros:** Zero tooling; immediately available; addresses the root cause (the doc taught the opposite of the truth).
- **Cons:** The rule is counterintuitive by construction — the safe-looking form is the dangerous one — so review is exactly the control most likely to fail. Two shipped components already passed review in the broken state, and one of them was the repo's own skill generator.
- **Why rejected:** Necessary but not sufficient. It is adopted *and* paired with R4's replaying linter; the doc fix alone is not treated as closing the class.

## Consequences

### Positive

- The live/inert question becomes decidable by tooling rather than by inspection, which is what it needs to be given that inspection is systematically wrong here.
- `#183`'s remediation scope collapses from 74 textual sites to 14 real ones, and — more importantly — the 9 inert sites in `prime` and `explain-project` are now protected from a well-meaning "tidy the backticks" edit that would switch on shell executions that have never run.
- F3 and F4 reframe an injection as a **load-time precondition** rather than a convenience, which makes the guard-and-grant requirement (R2) obviously mandatory instead of a style preference.
- R3 gives a principled reason to *delete* rather than guard an argument-substituted injection, closing a class where a guard would look like a fix and would not be one.

### Negative

- R4 couples a repo gate to two undocumented internal functions of a third-party binary. `Jds` and `Cfo` can change in any Claude Code release with no notice, and when they do the linter is silently wrong in whichever direction the change went. The mitigation is re-validating the replay against the pinned version, which is manual work with no automatic trigger.
- The nested house form of R1 renders imperfectly (a trailing double-backtick is visible in the output), so documentation is slightly uglier than it would be if the escaping rule ran the intuitive way. This is accepted deliberately: legibility in *source* outranks fidelity in *render* for a construct whose defect mode is invisibility.

### Neutral

- Files under `references/` and `deprecated/` are read as documentation and never expanded as a skill or command body, so live forms there execute nothing **today**. R1 still applies to them, because that safety is a property of the loader's current behavior rather than of the files, and because those files are the templates from which live surfaces are copied.
- ADR-0011 constrains authored surfaces only. It says nothing about the Bash tool's own behavior when a skill's *body instructions* tell the model to run a command; that path is an ordinary tool call with ordinary permission prompts and error handling.

## References

- LAB_NOTEBOOK E059 — the two crashing components, the decompilation, the independent Python replay, and the negative test.
- LAB_NOTEBOOK E060 — `/ultra-plan` over the backlog; finding 1 (the inverted rule) is the reason this ADR is Phase 1 item 1.1.
- `IMPLEMENTATION_PLAN.md` Phase 1 — items 1.2/1.4 apply R2, item 1.5 corrects `#183`'s scope, item 1.6 builds the R4 linter.
- `plugins/personal-plugin/references/patterns/advanced-features.md` — the surface corrected alongside this ADR; `:132` previously taught the opposite of F3.
- `plugins/personal-plugin/skills/arch-review/SKILL.md:44` — the pre-existing in-repo statement of F5 that had not propagated.
- ADR-0006 (skills-first authoring) — the generator layer this doctrine governs.
- Claude Code 2.1.220, `Jds` / `Cfo` / `WFe` / `en_` / `Aee` — the primary source for F1–F5.
