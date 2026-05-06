---
name: sg-outline
description: Generate a structured presentation outline from research findings
argument-hint: "<research.json> [--output path] [--target-slides N]"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Outline Step

Generate a structured presentation outline from research findings. Uses Claude with extended thinking (budget_tokens=4096) to produce a well-organized slide structure.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Available research files:**
!`ls -la *.json 2>/dev/null || echo "No JSON files found"`

## Proactive Triggers

Suggest this skill when:
1. User has a `research.json` and wants to create an outline
2. User says "outline this" or "structure these findings into slides"
3. User completed the research step and wants to continue
4. User wants to plan slide structure before drafting content

## Prerequisites

- `slide-generator` package installed
- `ANTHROPIC_API_KEY` set in environment
- A `research.json` file from the research step (or equivalent structured JSON)

## Input Validation

**Required:**
- `<research.json>` - Path to research findings file

**Optional:**
- `--output <path>` - Output file path (default: `outline.json`)
- `--target-slides <N>` - Target number of slides (default: 20, configurable via `SG_TARGET_SLIDES`)
- `--multi-presentation` - Allow splitting into multiple presentations if content warrants it

## Instructions

1. **Verify input**: Confirm the research JSON file exists and contains valid structured data
2. **Run outline generation**:
   ```bash
   sg outline research.json --output outline.json
   ```
3. **Verify output**: Confirm `outline.json` was created with slide structure
4. **Report results**: Show the outline structure (slide titles, approximate slide count)

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `File not found` | Wrong path to research.json | Check file path, list directory |
| `Invalid JSON` | Corrupted or incomplete research file | Re-run research step |
| `Token limit exceeded` | Research too large | Set `SG_OUTLINE_MAX_TOKENS=16384` or reduce research scope |

## Output

The outline step produces `outline.json` containing:
- Ordered list of slides with titles
- Bullet point structure per slide
- Speaker notes hints
- Graphics description placeholders
- Logical flow and transitions

## Next Step

After outline completes, run the draft step:
```bash
sg draft outline.json --output presentation.md
```
Or use `/sg-draft` to continue the pipeline.
