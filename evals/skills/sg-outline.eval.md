---
command: sg-outline
type: skill
fixtures: []
---

# Eval: /sg-outline (skill)

## Purpose

Runs the outline phase of the slide-generator pipeline: consumes a `research.json` artifact (from `sg-research`) and invokes the external `sg` CLI (`sg outline research.json --output outline.json`), which uses Claude with extended thinking to produce a structured presentation outline. Good output: an `outline.json` containing an ordered list of slides with titles, bullet-point structure, speaker-notes hints, graphics-description placeholders, and a coherent logical flow — plus a summary (slide titles, approximate count) and a pointer to the next step (`/sg-draft`). This is a structure-planning step only: it must not write full slide prose (that is `sg-draft`'s job), and it must not proceed without a real, valid `research.json` to build from.

## Fixtures

None — this skill operates on a `research.json` file produced by `sg-research` (or an equivalent structured JSON) in the working directory. No bundled fixture is provided; test scenarios reference a `research.json` that must exist (or intentionally not exist) in the scratch directory.

## Setup

Run in a scratch directory. For the happy path, first produce or place a valid `research.json` (e.g., via a prior `/sg-research` run, or a hand-built minimal JSON with a few subtopics and sources). For failure scenarios, remove or corrupt that file, or simulate a missing `sg` engine.

## Test Scenarios

### S1: Happy path — outline from valid research.json

**Setup:** A valid `research.json` (structured findings, sources, facts) is present in the working directory. `sg --version` succeeds.

**Invocation:** `/sg-outline research.json`

**Must:**
- [ ] Runs the preflight check (`sg --version`) before doing anything else
- [ ] Verifies `research.json` exists and contains valid structured data before invoking outline generation
- [ ] Invokes `sg outline research.json --output outline.json` (or an equivalent explicit output path)
- [ ] Verifies `outline.json` was created with a slide structure after the command runs
- [ ] Reports the outline structure (slide titles, approximate slide count)
- [ ] Points to the next step (`sg draft` or `/sg-draft`)

**Must NOT:**
- [ ] Write full slide content (paragraphs of bullet prose, speaker notes text) itself — that belongs to `sg-draft`
- [ ] Claim `outline.json` was produced without verifying the file exists and parses as JSON

---

### S2: Missing engine — preflight failure

**Setup:** `research.json` is present and valid, but `sg --version` fails (engine not installed).

**Invocation:** `/sg-outline research.json`

**Must:**
- [ ] Detects the preflight failure before attempting `sg outline`
- [ ] Stops and tells the user this requires the private `davistroy/slide-generator` engine (references ADR-0008 or owner-only installation)
- [ ] Does not create an `outline.json` file

**Must NOT:**
- [ ] Silently continue past the failed preflight
- [ ] Hand-write a placeholder outline in place of the missing engine's output

---

### S3: Missing prior artifact — no research.json

**Setup:** Working directory has no `research.json` and none is passed explicitly. `sg --version` succeeds.

**Invocation:** `/sg-outline`

**Must:**
- [ ] Detects that no `research.json` (or equivalent) exists before invoking `sg outline`
- [ ] Tells the user to run the research step first (`/sg-research` or `sg research`)
- [ ] Does not invoke `sg outline` against a nonexistent or empty file

**Must NOT:**
- [ ] Fabricate research findings on the fly and pass them through as if they were a real `research.json`
- [ ] Produce an `outline.json` when there was no valid research input

---

### S4: Custom target slide count and multi-presentation flag

**Setup:** A valid `research.json` covering a broad topic (many subtopics) is present.

**Invocation:** `/sg-outline research.json --target-slides 35 --multi-presentation`

**Must:**
- [ ] Passes `--target-slides 35` through to the underlying `sg outline` invocation (not the default of 20)
- [ ] Passes `--multi-presentation` through, allowing the outline step to split into multiple presentations if content warrants it

**Must NOT:**
- [ ] Silently fall back to the default target-slide count when an explicit value was given

---

### S5: Corrupted research.json

**Setup:** `research.json` exists but contains malformed/invalid JSON (e.g., truncated file).

**Invocation:** `/sg-outline research.json`

**Must:**
- [ ] Detects the invalid JSON (either via its own check or by surfacing the `sg outline` error)
- [ ] Reports the failure clearly and suggests re-running the research step
- [ ] Does not report success or produce an `outline.json` from corrupted input

---

### S6: Proactive trigger

**Setup:** A valid `research.json` exists in the working directory (e.g., just produced by a prior research step). User says "great, now turn this research into a slide structure" without invoking `/sg-outline` explicitly.

**Must:**
- [ ] Skill proactively recognizes the available `research.json` and offers or begins outline generation
- [ ] Does not require the user to type `/sg-outline` explicitly

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Preflight (`sg --version`) always runs before outline generation | Required |
| Missing engine produces a clear ADR-0008/private-repo message, no fabricated output | Required |
| Missing/absent `research.json` is detected and blocks the step with guidance to run research first | Required |
| Corrupted `research.json` is detected rather than silently accepted | Required |
| Skill does not write full slide prose — stays at structure/outline level | Required |
| Custom `--target-slides`/`--multi-presentation` respected exactly | Required |
| Proactive trigger when a fresh `research.json` is available | Should |
