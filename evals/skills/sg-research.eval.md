---
command: sg-research
type: skill
fixtures: []
---

# Eval: /sg-research (skill)

## Purpose

Runs the research phase of the slide-generator pipeline: invokes the external `sg` CLI (`sg research "<topic>" --output research.json`) to conduct autonomous web research via the Claude Agent SDK, producing a structured `research.json` artifact that feeds `sg-outline`. Good output: a `research.json` file containing findings organized by subtopic, source URLs/citations, key facts/statistics, and recommended presentation angles, plus a short summary (source count, key themes) and a pointer to the next step (`/sg-outline`). The skill itself does not do the research — it delegates to the `sg` engine and must fail fast (not fabricate) if that engine or its API key is unavailable.

## Fixtures

None — this skill calls the external `sg` CLI, which itself calls the Anthropic API. Requires the private `davistroy/slide-generator` engine installed (ADR-0008) and `ANTHROPIC_API_KEY` set for a live run. No fixture files are needed since the topic is supplied as a free-text argument.

## Setup

Run in a scratch directory (not the marketplace repo). For scenarios exercising failure paths, simulate engine absence by testing in a `PATH` without `sg`, or simulate missing credentials by unsetting `ANTHROPIC_API_KEY`.

## Test Scenarios

### S1: Happy path — research a topic from scratch

**Setup:** Empty working directory, no `research.json` present. `sg --version` succeeds, `sg health-check` reports keys OK.

**Invocation:** `/sg-research "impact of edge AI on real-time video analytics"`

**Must:**
- [ ] Runs the preflight check (`sg --version`) before doing anything else
- [ ] Invokes `sg research "<topic>" --output research.json` (or an equivalent explicit output path)
- [ ] Verifies `research.json` was created and contains valid JSON after the command runs
- [ ] Reports a summary including source count and key themes found
- [ ] Points to the next step (`sg outline` or `/sg-outline`)

**Should:**
- [ ] Confirms `ANTHROPIC_API_KEY` is set via `sg health-check` before running research
- [ ] Quotes the topic string exactly as given (no paraphrasing into a different topic)

**Must NOT:**
- [ ] Fabricate or hand-write research findings itself instead of invoking `sg research`
- [ ] Claim `research.json` was produced without having verified the file actually exists and parses as JSON

---

### S2: Missing engine — preflight failure

**Setup:** `sg --version` fails (command not found) — the private `davistroy/slide-generator` engine is not installed.

**Invocation:** `/sg-research "quantum error correction for NISQ devices"`

**Must:**
- [ ] Detects the preflight failure before attempting to run `sg research`
- [ ] Stops and tells the user this requires the private `davistroy/slide-generator` engine (references ADR-0008 or owner-only installation)
- [ ] Does not create a `research.json` file
- [ ] Does not attempt to substitute its own research in place of the missing engine

**Must NOT:**
- [ ] Silently continue past the failed preflight
- [ ] Produce a fake or placeholder `research.json`

---

### S3: Missing API key

**Setup:** `sg --version` succeeds, but `sg health-check` reports `ANTHROPIC_API_KEY not found`.

**Invocation:** `/sg-research "supply chain resilience post-2020"`

**Must:**
- [ ] Surfaces the `ANTHROPIC_API_KEY not found` condition before (or instead of) running `sg research`
- [ ] Tells the user how to fix it (`export ANTHROPIC_API_KEY=...`)
- [ ] Does not proceed to burn a research run that will fail partway through

**Must NOT:**
- [ ] Report success or produce a `research.json` when the key is missing

---

### S4: Custom output path and source cap

**Invocation:** `/sg-research "hydrogen fuel cell adoption in freight" --output research/haul-topic.json --max-sources 5`

**Must:**
- [ ] Uses `research/haul-topic.json` as the output path, not the default `research.json`
- [ ] Passes `--max-sources 5` through to the underlying `sg research` invocation (not the default of 20)

**Must NOT:**
- [ ] Ignore the custom flags and write to the default `research.json` path anyway

---

### S5: Proactive trigger

**Setup:** Working directory has no `research.json`. User says "I need to build a deck on renewable energy storage but I don't have any research yet" without invoking `/sg-research` explicitly.

**Must:**
- [ ] Skill proactively identifies this as the start of the slide-generator pipeline and offers or begins the research step
- [ ] Does not require the user to type `/sg-research` explicitly

**Should:**
- [ ] Confirms the topic phrasing with the user before running a potentially costly multi-source research call

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Preflight (`sg --version`) always runs before research | Required |
| Missing engine produces a clear ADR-0008/private-repo message, no fabricated output | Required |
| Missing API key is surfaced before/instead of a failed run | Required |
| `research.json` existence and JSON validity verified before reporting success | Required |
| Custom `--output`/`--max-sources` respected exactly | Required |
| Proactive trigger on "need research for a deck" phrasing | Should |
