---
name: sg-generate-images
effort: low
description: Generate slide visuals using Gemini Pro from validated graphics descriptions. Use when you want to generate slide images, create visuals after validation, or see what the slides will look like.
argument-hint: "<presentation.md> [--resolution high|medium|small]"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Generate Images Step

Generate slide visuals using Gemini Pro from the validated graphics descriptions in the presentation. Uses a unified prompt builder and async batch generation for efficiency.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Available presentation files:**
!`ls -la *.md 2>/dev/null | grep -i pres || echo "No presentation files found"`

**Existing images:**
!`ls -la images/ 2>/dev/null || echo "No images directory yet"`

## Prerequisites

- **Preflight:** `sg --version` must succeed before proceeding — if `sg` is missing, stop and tell the user this requires the private `davistroy/slide-generator` engine (owner-only; see ADR-0008)
- `slide-generator` package installed
- `GOOGLE_API_KEY` set in environment (Gemini Pro access)
- A `presentation.md` file with validated graphics descriptions
- Graphics validation should be run first (`.graphics_validated` marker)

## Input Validation

**Required:**
- `<presentation.md>` - Path to presentation markdown file

**Optional:**
- `--resolution <level>` - Image resolution: `small`, `medium`, `high` (default: high)
- `--image-format <fmt>` - Output format: `png`, `jpg` (default: png)
- `--skip-existing` - Don't regenerate images that already exist

## Instructions

1. **Verify prerequisites**: Confirm `GOOGLE_API_KEY` is set and presentation has validated graphics
2. **Run image generation**:
   ```bash
   sg generate-images presentation.md --resolution high
   ```
3. **Monitor progress**: Image generation takes time (~5-10s per image)
4. **Verify output**: Check that images were created in the `images/` directory
5. **Report results**: Show count of images generated, any failures

## How It Works

The image generation step uses:
- **Gemini Pro** (`gemini-3-pro-image-preview`): Google's image generation model
- **Unified prompt builder**: `prompt_builder.py` constructs optimized prompts from descriptions
- **Async batch generation**: Multiple images generated concurrently via `asyncio`
- **API key in header**: Authentication via header (not query param)
- **Block reason diagnostics**: Clear error messages when generation is blocked

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `GOOGLE_API_KEY not found` | Missing env var | Set the key |
| `Image blocked` | Content policy violation | Review and soften the description |
| `Rate limit` | Too many concurrent requests | Built-in rate limiter handles this |
| `Generation timeout` | Gemini service slow | Retry; increase `SG_API_TIMEOUT` |

## Cost Estimate

- ~$0.10 per image at high resolution
- Typical 20-slide deck: ~$2.00

## Output

The step produces:
- PNG/JPG images in an `images/` directory (one per slide)
- File names correspond to slide numbers (`slide-01.png`, `slide-02.png`, etc.)

## Next Step

After images are generated, build the final PowerPoint:
```bash
sg build presentation.md --template generic
```
Or use `/sg-build` to continue the pipeline.

## Related Gemini Image Path

This step delegates image generation to the external `sg` CLI (the `slide-generator` package), which is unbundled and maintained outside this repo. personal-plugin's `visual-explainer` skill/tool is a **separate**, in-tree, tested Gemini image path with its own prompt builder and model config — the two are intentionally independent implementations, not a shared library. Future Gemini model or API changes (e.g. a new model ID, auth scheme, or block-reason handling) must be applied in **both** places: here (via the external `sg` package) and in `plugins/personal-plugin/tools/visual-explainer/`.
