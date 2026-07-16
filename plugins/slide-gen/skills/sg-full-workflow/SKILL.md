---
name: sg-full-workflow
description: Run the complete 7-step slide generation pipeline from topic to PowerPoint. Use when you want to create a full presentation from scratch, generate a complete deck end-to-end, or see the entire pipeline in action.
argument-hint: "<topic> [--template generic] [--skip-images] [--output dir]"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Full Workflow

Run the complete 7-step presentation generation pipeline end-to-end. Takes a topic string and produces a finished PowerPoint file through: Research, Outline, Draft, Optimize, Validate Graphics, Generate Images, and Build.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Slide-generator installation check:**
!`sg --version 2>&1 || echo "NOT INSTALLED"`

**API key status:**
!`sg health-check 2>&1 | head -15`

**Available templates:**
!`sg list-templates 2>&1 || echo "Cannot list templates"`

## Preflight Check (Required First Step — Fail Fast)

Before running any pipeline step, confirm `sg` is actually installed and on `PATH`:

```bash
command -v sg >/dev/null 2>&1 && sg --version || echo "SG_MISSING"
```

**If this reports `SG_MISSING` (or the "Slide-generator installation check" above shows `NOT INSTALLED`), STOP immediately.** Do not proceed to Research or any other step. Report to the user, verbatim:

> slide-gen requires the external `sg` engine from davistroy/slide-generator (currently a PRIVATE repo — owner-only). Install it and ensure `sg` is on PATH before running. This plugin ships only the pipeline skills, not the engine.

This check exists so the pipeline never dies several steps in with an opaque `sg: command not found` — see ADR-0008 (`docs/adr/0008-slide-gen-dependency-model.md`) for why the engine is external rather than bundled, and the slide-gen README's "External Dependency" section for the current owner-only status.

## Prerequisites

- `slide-generator` package installed (`pip install -e ".[all]"` from the private `davistroy/slide-generator` repo — owner-only access as of this writing)
- `ANTHROPIC_API_KEY` set in environment (required for steps 1-5)
- `GOOGLE_API_KEY` set in environment (required for step 6, unless `--skip-images`)

## Input Validation

**Required:**
- `<topic>` - The presentation topic (quoted string)

**Optional:**
- `--template <name>` - Presentation template (default: `generic`)
- `--output <dir>` - Output directory (default: `./output`)
- `--skip-images` - Skip image generation (steps 1-5 + 7 only)
- `--resolution <level>` - Image resolution: `small`, `medium`, `high` (default: high)
- `--tone <tone>` - Content tone: professional, casual, academic, technical
- `--audience <audience>` - Target audience description
- `--target-slides <N>` - Target slide count (default: 20)
- `--no-interactive` - Non-interactive mode (no prompts)

## Instructions

### Step 0: Preflight Check

Run the preflight check above before anything else. If `sg` is missing, stop and report the message verbatim — do not attempt the Quick Path or Step-by-Step Path below.

### Quick Path (Single Command)

For most use cases, the `sg full-workflow` command handles everything:

```bash
sg full-workflow "<topic>" --template generic --no-interactive
```

This runs all 7 steps sequentially with automatic error handling, retries, and progress reporting.

### Step-by-Step Path (More Control)

If you need to inspect or modify artifacts between steps, run each step individually:

**Step 1: Research**
```bash
sg research "<topic>" --output research.json
```
Produces `research.json` — autonomous web research via Claude Agent SDK.

**Step 2: Outline**
```bash
sg outline research.json --output outline.json
```
Produces `outline.json` — structured slide outline with extended thinking.

**Step 3: Draft**
```bash
sg draft outline.json --output presentation.md
```
Produces `presentation.md` — full slide content with batched generation.

**Step 4: Optimize**
```bash
sg optimize presentation.md
```
Updates `presentation.md` — quality analysis and improvement across 5 dimensions.

**Step 5: Validate Graphics**
```bash
sg validate-graphics presentation.md
```
Updates `presentation.md` — ensures image descriptions are concrete and generation-ready.

**Step 6: Generate Images**
```bash
sg generate-images presentation.md --resolution high
```
Produces `images/slide-*.png` — AI-generated visuals via Gemini Pro.

**Step 7: Build**
```bash
sg build presentation.md --template generic
```
Produces final `.pptx` file — assembled PowerPoint with all content and images.

### Resume After Interruption

If the pipeline is interrupted at any step:
```bash
sg resume
```
Or check status and resume manually:
```bash
sg status
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `sg: command not found` | Not installed, or private `slide-generator` repo inaccessible | Caught by the Preflight Check above before this step runs. If seen mid-pipeline anyway, install `sg` from the private `davistroy/slide-generator` repo (owner-only) and ensure it's on `PATH` |
| `ANTHROPIC_API_KEY not found` | Missing env var | Set Claude API key |
| `GOOGLE_API_KEY not found` | Missing env var (images) | Set Gemini key, or use `--skip-images` |
| `Rate limit exceeded` | Too many API calls | Built-in retry with backoff handles this |
| `Circuit breaker open` | Repeated API failures | Wait 60s for circuit breaker reset |
| `Research timeout` | Topic too broad | Narrow the topic |

## Cost Considerations

Image generation dominates the cost of a full workflow run. Research, outline, draft, and optimize stages are comparatively cheap compared to generating 20 high-resolution images. To minimize costs, use the `--skip-images` flag to run steps 1-5 and 7 without image generation, eliminating most of the expense. You can always generate images later if needed.

## Output

The full workflow produces in the output directory:
- `research.json` — Raw research findings
- `outline.json` — Slide structure
- `presentation.md` — Full slide content
- `images/` — Generated slide visuals
- `<topic>.pptx` — Final PowerPoint file

## Configuration

Override defaults via environment variables:
```bash
SG_TEMPLATE=generic          # Default template
SG_OUTPUT_DIR=./output       # Output directory
SG_IMAGE_RESOLUTION=high     # Image quality
SG_TARGET_SLIDES=20          # Target slide count
SG_TONE=professional         # Content tone
SG_API_TIMEOUT=120           # API timeout (seconds)
SG_MAX_RETRIES=3             # Retry attempts
```
