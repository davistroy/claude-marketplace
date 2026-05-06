---
name: sg-draft
description: Draft full slide content (titles, bullets, speaker notes, graphics descriptions) from an outline
argument-hint: "<outline.json> [--output path]"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Draft Step

Draft full slide content from an outline. Uses structured single-call generation (one API call per slide) with batching (groups of 4) for efficiency. Produces a complete presentation markdown with titles, bullets, speaker notes, and graphics descriptions.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Available outline files:**
!`ls -la outline*.json 2>/dev/null || echo "No outline files found"`

## Proactive Triggers

Suggest this skill when:
1. User has an outline and wants to generate full slide content
2. User says "draft the slides" or "write the content"
3. User completed the outline step and wants to continue
4. User wants to go from structure to full presentation content

## Prerequisites

- `slide-generator` package installed
- `ANTHROPIC_API_KEY` set in environment
- An `outline.json` file from the outline step

## Input Validation

**Required:**
- `<outline.json>` - Path to outline file

**Optional:**
- `--output <path>` - Output file path (default: `presentation.md`)
- `--tone <tone>` - Content tone: professional, casual, academic, technical (default: professional)
- `--audience <audience>` - Target audience description

## Instructions

1. **Verify input**: Confirm the outline JSON file exists and is valid
2. **Run draft generation**:
   ```bash
   sg draft outline.json --output presentation.md
   ```
3. **Verify output**: Confirm `presentation.md` was created with full slide content
4. **Report results**: Show slide count, total word count, and a sample slide

## How It Works

The draft step uses:
- **Structured single-call**: Each slide generated in one API call (not 4 separate calls)
- **Batch generation**: Slides grouped in batches of 4 for efficiency
- **Inter-slide context**: Rolling 5-slide context window for coherence
- **Temperature 0.5**: Balanced creativity for content generation
- **Research cache**: Reuses research findings for factual accuracy

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `File not found` | Wrong path to outline.json | Check file path |
| `Rate limit` | Too many API calls in batch | Wait and retry (built-in backoff handles this) |
| `Content too short` | Outline lacks detail | Re-run outline with more target slides |

## Output

The draft step produces `presentation.md` containing:
- Full markdown-formatted slides
- Titles, bullet points, and detailed speaker notes
- Graphics descriptions for each slide (feeds image generation)
- Proper frontmatter with metadata

## Next Step

After draft completes, run the optimize step:
```bash
sg optimize presentation.md
```
Or use `/sg-optimize` to continue the pipeline.
