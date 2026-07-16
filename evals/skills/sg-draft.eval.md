---
command: sg-draft
type: skill
fixtures: []
---

# Eval: /sg-draft (skill)

## Purpose

Runs the draft phase of the slide-generator pipeline: consumes an `outline.json` artifact (from `sg-outline`) and invokes the external `sg` CLI (`sg draft outline.json --output presentation.md`), which drafts full slide content — titles, bullets, speaker notes, and graphics descriptions — using structured single-call generation batched in groups of 4 with a rolling 5-slide context window. Good output: a `presentation.md` with full markdown-formatted slides (titles, bullet points, detailed speaker notes, per-slide graphics descriptions, and proper frontmatter metadata), plus a summary (slide count, total word count, a sample slide) and a pointer to the next step (`/sg-optimize`). The skill delegates the actual content generation to `sg draft`; it must not proceed without a valid `outline.json`, and it must not hand-write slide content itself in place of the engine.

## Fixtures

None — this skill operates on an `outline.json` file produced by `sg-outline` in the working directory. No bundled fixture is provided; test scenarios reference an `outline.json` that must exist (or intentionally not exist) in the scratch directory.

## Setup

Run in a scratch directory. For the happy path, first produce or place a valid `outline.json` (e.g., via a prior `/sg-outline` run, or a hand-built minimal JSON with a few slides). For failure scenarios, remove the file or simulate a missing `sg` engine.

## Test Scenarios

### S1: Happy path — draft from valid outline.json

**Setup:** A valid `outline.json` (ordered slides with titles and bullet structure) is present. `sg --version` succeeds.

**Invocation:** `/sg-draft outline.json`

**Must:**
- [ ] Runs the preflight check (`sg --version`) before doing anything else
- [ ] Verifies `outline.json` exists and is valid before invoking draft generation
- [ ] Invokes `sg draft outline.json --output presentation.md` (or an equivalent explicit output path)
- [ ] Verifies `presentation.md` was created with full slide content after the command runs
- [ ] Reports slide count, total word count, and a sample slide
- [ ] Points to the next step (`sg optimize` or `/sg-optimize`)

**Must NOT:**
- [ ] Hand-write slide titles/bullets/speaker notes itself instead of invoking `sg draft`
- [ ] Claim `presentation.md` was produced without verifying the file actually exists and contains slide content

---

### S2: Missing engine — preflight failure

**Setup:** `outline.json` is present and valid, but `sg --version` fails (engine not installed).

**Invocation:** `/sg-draft outline.json`

**Must:**
- [ ] Detects the preflight failure before attempting `sg draft`
- [ ] Stops and tells the user this requires the private `davistroy/slide-generator` engine (references ADR-0008 or owner-only installation)
- [ ] Does not create a `presentation.md` file

**Must NOT:**
- [ ] Silently continue past the failed preflight
- [ ] Draft placeholder slide content in place of the missing engine's output

---

### S3: Missing prior artifact — no outline.json

**Setup:** Working directory has no `outline.json` and none is passed explicitly. `sg --version` succeeds.

**Invocation:** `/sg-draft`

**Must:**
- [ ] Detects that no `outline.json` exists before invoking `sg draft`
- [ ] Tells the user to run the outline step first (`/sg-outline` or `sg outline`)
- [ ] Does not invoke `sg draft` against a nonexistent file

**Must NOT:**
- [ ] Fabricate an outline structure on the fly and pass it through as if it were a real `outline.json`
- [ ] Produce a `presentation.md` when there was no valid outline input

---

### S4: Custom tone and audience

**Setup:** A valid `outline.json` is present.

**Invocation:** `/sg-draft outline.json --tone academic --audience "graduate-level cybersecurity researchers"`

**Must:**
- [ ] Passes `--tone academic` through to the underlying `sg draft` invocation (not the default of professional)
- [ ] Passes `--audience "graduate-level cybersecurity researchers"` through unmodified

**Must NOT:**
- [ ] Silently fall back to the default tone/audience when explicit values were given

---

### S5: Thin outline — content too short

**Setup:** `outline.json` exists but has minimal detail per slide (e.g., bare titles with no bullet hints).

**Invocation:** `/sg-draft outline.json`

**Must:**
- [ ] Surfaces the resulting "content too short" condition (or equivalent thin-output signal) rather than reporting a strong result
- [ ] Suggests re-running the outline step with more detail or a higher `--target-slides` count

**Must NOT:**
- [ ] Report the draft as high quality when the underlying outline lacked sufficient structure to draft from

---

### S6: Proactive trigger

**Setup:** A valid `outline.json` exists in the working directory (e.g., just produced by a prior outline step). User says "okay, let's write the actual slide content now" without invoking `/sg-draft` explicitly.

**Must:**
- [ ] Skill proactively recognizes the available `outline.json` and offers or begins draft generation
- [ ] Does not require the user to type `/sg-draft` explicitly

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Preflight (`sg --version`) always runs before draft generation | Required |
| Missing engine produces a clear ADR-0008/private-repo message, no fabricated output | Required |
| Missing/absent `outline.json` is detected and blocks the step with guidance to run outline first | Required |
| Skill delegates content generation to `sg draft` rather than hand-writing slide prose | Required |
| `presentation.md` existence and slide content verified before reporting success | Required |
| Custom `--tone`/`--audience` respected exactly | Required |
| Proactive trigger when a fresh `outline.json` is available | Should |
