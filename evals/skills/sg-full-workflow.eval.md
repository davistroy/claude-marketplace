---
command: sg-full-workflow
type: skill
fixtures: []
---

# Eval: /sg-full-workflow (skill)

## Purpose

Runs the complete 7-step slide generation pipeline (Research, Outline, Draft, Optimize, Validate Graphics, Generate Images, Build) end-to-end from a topic string to a finished `.pptx`. Good behavior: a mandatory fail-fast preflight check before touching any step, sequential execution that stops immediately on a failed step rather than limping forward, and honest reporting of exactly which artifacts exist in the output directory.

## Fixtures

None — this skill starts from a topic string and generates all its own artifacts. Requires the private `sg` CLI (`davistroy/slide-generator`, ADR-0008), `ANTHROPIC_API_KEY` (steps 1-5), and `GOOGLE_API_KEY` (step 6, unless `--skip-images`).

## Setup

Run in an empty scratch directory. For the preflight-failure scenario, ensure `sg` is not on `PATH`. For the mid-pipeline-failure scenario, simulate a failure at one step (e.g. an API error during Draft) and observe whether the pipeline halts.

## Test Scenarios

### S1: Happy path — quick path from topic to PowerPoint

**Setup:** `sg` installed, `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set.

**Invocation:** `/sg-full-workflow "Intro to Quantum Computing" --template generic`

**Must:**
- [ ] Runs the Preflight Check (`command -v sg && sg --version`) before any pipeline step
- [ ] Executes the pipeline via `sg full-workflow "..." --template generic --no-interactive` (quick path) or all 7 steps in order (step-by-step path)
- [ ] Produces a final `.pptx` file in the output directory
- [ ] Reports the full artifact set: `research.json`, `outline.json`, `presentation.md`, `images/`, and the final `.pptx`

**Must NOT:**
- [ ] Skip the preflight check "because it worked last time"
- [ ] Report the workflow complete without confirming the final `.pptx` exists

---

### S2: Preflight failure — `sg` engine missing (fail-fast)

**Setup:** `sg` is not on `PATH`.

**Invocation:** `/sg-full-workflow "Intro to Quantum Computing"`

**Must:**
- [ ] Detects `SG_MISSING` from the preflight check before attempting Research or any other step
- [ ] Stops immediately — does not proceed to the Quick Path or Step-by-Step Path
- [ ] Reports, verbatim in substance, that slide-gen requires the external `sg` engine from `davistroy/slide-generator` (currently private, owner-only) and references ADR-0008

**Must NOT:**
- [ ] Run one or more pipeline steps before failing later with an opaque `sg: command not found`
- [ ] Attempt Research, Outline, or any step against a missing engine

---

### S3: `--skip-images` flag

**Invocation:** `/sg-full-workflow "Intro to Quantum Computing" --skip-images`

**Must:**
- [ ] Runs steps 1-5 and 7 (Research, Outline, Draft, Optimize, Validate Graphics, Build)
- [ ] Skips step 6 (Generate Images) entirely
- [ ] Does not require `GOOGLE_API_KEY` to be set
- [ ] Final `.pptx` is still produced, built without an `images/` directory

**Must NOT:**
- [ ] Fail or block on a missing `GOOGLE_API_KEY` when `--skip-images` was passed

---

### S4: Mid-pipeline step failure — stop, don't produce a broken deck

**Setup:** Simulate a failure partway through (e.g. Draft step errors out, or `ANTHROPIC_API_KEY` is revoked mid-run after Research/Outline succeed).

**Invocation:** `/sg-full-workflow "Intro to Quantum Computing"`

**Must:**
- [ ] Halts the pipeline at the failed step rather than continuing to subsequent steps
- [ ] Reports which specific step failed and why
- [ ] Does not run the Build step against incomplete or missing upstream artifacts
- [ ] Suggests `sg resume` or `sg status` to recover

**Must NOT:**
- [ ] Skip the failed step and press on to Build anyway
- [ ] Produce any `.pptx` file from a run that didn't complete all required steps
- [ ] Silently treat a partial/broken deck as the finished output

---

### S5: Missing API key

**Setup:** `ANTHROPIC_API_KEY` unset, `sg` installed.

**Invocation:** `/sg-full-workflow "Intro to Quantum Computing"`

**Must:**
- [ ] Surfaces the `ANTHROPIC_API_KEY not found` condition (per the skill's Error Handling table) rather than a raw stack trace
- [ ] Stops before or at the first step that needs the key (Research)
- [ ] Tells the user to set the Claude API key

---

### S6: Resume after interruption

**Setup:** A prior run was interrupted after Draft — `research.json`, `outline.json`, and a partial `presentation.md` already exist in the output directory.

**Invocation:** User says "resume the presentation build" (or re-invokes `/sg-full-workflow "Intro to Quantum Computing"`)

**Must:**
- [ ] Recognizes existing partial artifacts rather than blindly restarting from Research
- [ ] Runs (or suggests) `sg resume` or `sg status` to pick up from the interruption point

**Must NOT:**
- [ ] Silently overwrite `research.json`/`outline.json` by restarting step 1 without telling the user prior artifacts exist

---

### S7: Proactive trigger

**Setup:** User says "generate a full deck on quantum computing from scratch" without naming the skill.

**Must:**
- [ ] Proactively engages the full-workflow pipeline (including its Preflight Check) rather than requiring the literal `/sg-full-workflow` invocation

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Preflight check always runs before any pipeline step | Required |
| Missing `sg` engine reported with ADR-0008 context, no step attempted first | Required |
| Pipeline halts on a failed step rather than continuing to Build | Required |
| No `.pptx` produced from an incomplete pipeline run | Required |
| `--skip-images` correctly bypasses step 6 and its API key requirement | Required |
| Resume path recognizes and preserves existing partial artifacts | Should |
