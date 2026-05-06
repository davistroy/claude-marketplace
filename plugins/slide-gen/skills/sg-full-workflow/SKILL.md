---
name: sg-full-workflow
description: Run the complete 7-step slide generation pipeline from topic to PowerPoint
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

## Proactive Triggers

Suggest this skill when:
1. User wants to create a full presentation from scratch
2. User says "make a presentation about [topic]", "create slides on [topic]", or "generate a deck"
3. User provides a topic and expects end-to-end execution
4. User wants to see the complete pipeline in action

## Prerequisites

- `slide-generator` package installed (`pip install -e ".[all]"` from the slide-generator repo)
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
| `sg: command not found` | Not installed | `pip install -e ".[all]"` from slide-generator repo |
| `ANTHROPIC_API_KEY not found` | Missing env var | Set Claude API key |
| `GOOGLE_API_KEY not found` | Missing env var (images) | Set Gemini key, or use `--skip-images` |
| `Rate limit exceeded` | Too many API calls | Built-in retry with backoff handles this |
| `Circuit breaker open` | Repeated API failures | Wait 60s for circuit breaker reset |
| `Research timeout` | Topic too broad | Narrow the topic |

## Cost Estimate

Typical 20-slide presentation:
- Research: ~$0.20 (Claude)
- Outline + Draft + Optimize: ~$0.50 (Claude)
- Image generation: ~$2.00 (Gemini, 20 images at high resolution)
- **Total: ~$2.70**

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
