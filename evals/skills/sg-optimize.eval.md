---
command: sg-optimize
type: skill
fixtures: []
---

# Eval: /sg-optimize (skill)

## Purpose

Runs quality analysis and automated improvement on a drafted `presentation.md` using Claude with extended thinking (budget_tokens=4096, temperature=1.0), scoring and improving content across 5 dimensions: readability, tone consistency, structure, redundancy, and citation quality. Good behavior: preflight-checks the external `sg` engine before doing anything, runs `sg optimize`, and reports concrete before/after quality signal rather than a vague "looks better."

## Fixtures

None — requires a `presentation.md` file (drafted output from `/sg-draft`) in the working directory, and the private `sg` CLI (`davistroy/slide-generator`, ADR-0008) on `PATH`.

## Setup

Run in a scratch directory containing a `presentation.md` with slide markers (e.g. `## Slide 1`). For the preflight-failure scenario, ensure `sg` is NOT on `PATH` (e.g. `PATH=/usr/bin:/bin`). For the missing-input scenario, use an empty directory.

## Test Scenarios

### S1: Happy path — optimize a drafted deck

**Setup:** `presentation.md` exists with 8-10 slides of drafted content; `sg` is installed and `ANTHROPIC_API_KEY` is set.

**Invocation:** `/sg-optimize presentation.md`

**Must:**
- [ ] Verifies `sg --version` succeeds before running optimization
- [ ] Confirms `presentation.md` exists and contains slide content before invoking the engine
- [ ] Runs `sg optimize presentation.md`
- [ ] Verifies the optimized output file was actually created (not just assumes success)
- [ ] Reports quality scores across the 5 dimensions (readability, tone, structure, redundancy, citations)

**Should:**
- [ ] Reports before/after comparison if the tool surfaces both
- [ ] Names the specific improvements made (e.g. shortened sentences, reduced redundancy between slides X and Y)

**Must NOT:**
- [ ] Fabricate quality scores if `sg optimize` did not actually run or produce output
- [ ] Claim the deck was optimized without verifying the output file exists

---

### S2: Preflight failure — `sg` engine missing

**Setup:** `sg` is not on `PATH`.

**Invocation:** `/sg-optimize presentation.md`

**Must:**
- [ ] Detects that `sg --version` fails before attempting optimization
- [ ] Stops immediately — does not attempt `sg optimize` anyway
- [ ] Tells the user this requires the private `davistroy/slide-generator` engine (owner-only, ADR-0008)

**Must NOT:**
- [ ] Attempt to fake or simulate optimization output when the engine is unavailable
- [ ] Fail with a raw/opaque "command not found" without the ADR-0008 context

---

### S3: Missing input file

**Setup:** Working directory has no `presentation.md` (and no other `*pres*.md` file).

**Invocation:** `/sg-optimize`

**Must:**
- [ ] Detects the missing presentation markdown before invoking `sg`
- [ ] Reports that no presentation file was found and that `/sg-draft` (or equivalent) must run first
- [ ] Does not proceed to run `sg optimize` against a nonexistent file

**Must NOT:**
- [ ] Invent slide content to "optimize" in place of a real file

---

### S4: Custom output path

**Invocation:** `/sg-optimize presentation.md --output presentation_v2.md`

**Must:**
- [ ] Passes `--output presentation_v2.md` through to the underlying `sg optimize` invocation
- [ ] Reports the custom output path back to the user
- [ ] Does not silently overwrite `presentation.md` in place when a distinct `--output` path was given

---

### S5: Large deck — representative sampling

**Setup:** `presentation.md` has 20+ slides (exceeds the 15-slide threshold documented in the skill).

**Invocation:** `/sg-optimize presentation.md`

**Must:**
- [ ] Notes that representative sampling / batched optimization is used rather than claiming every single slide was individually scored
- [ ] Still reports an overall quality result for the deck

**Should:**
- [ ] Mentions the `SG_OPTIMIZE_MAX_TOKENS` env var if a token-limit error surfaces for the large deck

---

### S6: Proactive trigger

**Setup:** User just ran `/sg-draft` in the current session and now says "can you improve the quality of these slides before I generate images?"

**Must:**
- [ ] Skill proactively engages the optimize workflow (preflight + `sg optimize`) without requiring the literal `/sg-optimize` command
- [ ] Confirms a `presentation.md` exists before proceeding

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Preflight (`sg --version`) checked before any optimize call | Required |
| Missing `sg` engine reported with ADR-0008 context, not a raw error | Required |
| Output file existence verified before reporting success | Required |
| Quality scores reported across the 5 documented dimensions | Required |
| Large-deck sampling behavior disclosed, not silently hidden | Should |
| Custom `--output` path honored and not silently ignored | Required |
