---
name: sg-validate-graphics
description: Validate that image descriptions are concrete enough for AI image generation
argument-hint: "<presentation.md>"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Validate Graphics Step

Validate that image descriptions in the presentation are concrete and specific enough for AI image generation. Identifies vague descriptions and rewrites them to be generation-ready.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Available presentation files:**
!`ls -la *.md 2>/dev/null | grep -i pres || echo "No presentation files found"`

## Proactive Triggers

Suggest this skill when:
1. User wants to check if image descriptions are good enough for generation
2. User says "validate graphics" or "check image descriptions"
3. User completed the optimize step and wants to continue
4. Before running image generation to avoid wasted API calls

## Prerequisites

- `slide-generator` package installed
- `ANTHROPIC_API_KEY` set in environment
- A `presentation.md` file with graphics description fields

## Input Validation

**Required:**
- `<presentation.md>` - Path to presentation markdown file

## Instructions

1. **Verify input**: Confirm the presentation markdown exists and has graphics description fields
2. **Run validation**:
   ```bash
   sg validate-graphics presentation.md
   ```
3. **Review results**: Check which descriptions passed/failed validation
4. **Report**: Show pass/fail count and any descriptions that were rewritten

## How It Works

The validator checks each graphics description for:
- **Specificity**: Does it describe a concrete visual (not just "a diagram")?
- **Actionability**: Can an image generator produce this without guessing?
- **Completeness**: Does it specify composition, style, colors, and subject matter?
- **Chunk-scoped replacement**: Fixes are scoped per-slide to prevent cross-contamination

Descriptions that fail are automatically rewritten to be more concrete while preserving intent.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `No graphics descriptions found` | Presentation lacks image fields | Re-run draft step |
| `All descriptions failed` | Content too abstract | Consider manual description writing |

## Output

The validation step updates `presentation.md` in-place with:
- Validated (or rewritten) graphics descriptions
- A `.graphics_validated` marker file indicating completion

## Next Step

After validation completes, run image generation:
```bash
sg generate-images presentation.md --resolution high
```
Or use `/sg-generate-images` to continue the pipeline.
