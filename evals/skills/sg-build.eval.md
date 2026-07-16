---
command: sg-build
type: skill
fixtures: []
---

# Eval: /sg-build (skill)

## Purpose

Assembles the final PowerPoint (`.pptx`) from `presentation.md` and any generated images, using python-pptx and the selected template. Good behavior: preflight-checks the external `sg` engine, verifies the source markdown (and, where relevant, images) exist before building, and never silently ships a deck missing content it should have flagged.

## Fixtures

None — requires a `presentation.md` file (from `/sg-draft` / `/sg-optimize`) and, optionally, a populated `images/` directory (from `/sg-generate-images`) in the working directory. Requires the private `sg` CLI (`davistroy/slide-generator`, ADR-0008) on `PATH`.

## Setup

Run in a scratch directory. For the happy path, place a `presentation.md` with slide markers and an `images/` directory containing matching `slide-*.png` files. For edge cases, remove the relevant artifact per scenario.

## Test Scenarios

### S1: Happy path — build with markdown and images present

**Setup:** `presentation.md` and populated `images/` both exist; `sg` is installed.

**Invocation:** `/sg-build presentation.md --template generic`

**Must:**
- [ ] Verifies `sg --version` succeeds before building
- [ ] Confirms `presentation.md` exists and images are present before invoking the build
- [ ] Runs `sg build presentation.md --template generic`
- [ ] Verifies the `.pptx` file was actually created on disk
- [ ] Reports the output file path, file size, and slide count

**Should:**
- [ ] Confirms images were embedded (not just markdown parsed)

**Must NOT:**
- [ ] Report the build as successful without confirming the `.pptx` exists

---

### S2: Missing prior artifact — no presentation.md

**Setup:** Empty working directory (no `/sg-draft` or `/sg-optimize` has been run).

**Invocation:** `/sg-build`

**Must:**
- [ ] Detects that no `presentation.md` exists before attempting a build
- [ ] Reports that the draft/optimize steps must run first
- [ ] Does not call `sg build` against a nonexistent file

**Must NOT:**
- [ ] Fabricate or scaffold a placeholder `presentation.md` to build from
- [ ] Produce any `.pptx` file when there is no source markdown

---

### S3: Missing images directory

**Setup:** `presentation.md` exists but there is no `images/` directory (image generation step was skipped or not yet run).

**Invocation:** `/sg-build presentation.md`

**Must:**
- [ ] Explicitly tells the user images are missing and the deck will build without them (per the skill's documented "optional — builds without images if missing" behavior)
- [ ] Still completes the build if the user proceeds

**Must NOT:**
- [ ] Silently produce a deck with broken/placeholder image references without disclosing that images are absent
- [ ] Claim images were embedded when the `images/` directory does not exist

---

### S4: Preflight failure — `sg` engine missing

**Setup:** `sg` is not on `PATH`.

**Invocation:** `/sg-build presentation.md`

**Must:**
- [ ] Detects `sg --version` failure before attempting the build
- [ ] Stops immediately without attempting `sg build`
- [ ] Tells the user this requires the private `davistroy/slide-generator` engine (owner-only, ADR-0008)

**Must NOT:**
- [ ] Attempt to hand-assemble a `.pptx` via some other means when the engine is unavailable

---

### S5: Invalid template name

**Setup:** User requests a template that does not exist.

**Invocation:** `/sg-build presentation.md --template nonexistent-template`

**Must:**
- [ ] Surfaces the `Template not found` error rather than silently falling back to a different template
- [ ] Runs (or suggests running) `sg list-templates` to show valid options

**Must NOT:**
- [ ] Silently substitute `generic` (or any other template) without telling the user their requested template was invalid

---

### S6: Custom style and output path

**Invocation:** `/sg-build presentation.md --template generic --style style.json --output final-deck.pptx`

**Must:**
- [ ] Passes `--style style.json` and `--output final-deck.pptx` through to the `sg build` invocation
- [ ] Reports the actual output path used (`final-deck.pptx`, not an auto-generated topic-based name)

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Preflight (`sg --version`) checked before any build call | Required |
| Missing `presentation.md` reported clearly, no build attempted | Required |
| Missing images disclosed rather than silently building a broken deck | Required |
| Output `.pptx` existence verified before reporting success | Required |
| Invalid template surfaced with `sg list-templates` guidance, not silently substituted | Required |
| Custom `--style`/`--output` flags honored | Should |
