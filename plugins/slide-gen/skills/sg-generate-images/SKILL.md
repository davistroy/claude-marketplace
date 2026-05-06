---
name: sg-generate-images
description: Generate slide visuals using Gemini Pro from validated graphics descriptions
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

## Proactive Triggers

Suggest this skill when:
1. User wants to generate slide images/visuals
2. User says "generate images", "create visuals", or "make the graphics"
3. User completed graphics validation and wants to continue
4. User wants to see what the slides will look like

## Prerequisites

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
