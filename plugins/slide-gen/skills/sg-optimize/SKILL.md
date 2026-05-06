---
name: sg-optimize
description: Run quality analysis and automated improvement on drafted slide content
argument-hint: "<presentation.md> [--output path]"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Optimize Step

Run quality analysis and automated improvement on drafted slide content. Uses Claude with extended thinking (budget_tokens=4096, temperature=1.0) to score and improve content across 5 dimensions: readability, tone consistency, structure, redundancy, and citation quality.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Available presentation files:**
!`ls -la *.md 2>/dev/null | grep -i pres || echo "No presentation files found"`

## Proactive Triggers

Suggest this skill when:
1. User has drafted slides and wants to improve quality
2. User says "optimize", "improve the slides", or "make it better"
3. User completed the draft step and wants to continue
4. User wants quality scoring before finalizing

## Prerequisites

- `slide-generator` package installed
- `ANTHROPIC_API_KEY` set in environment
- A `presentation.md` file from the draft step

## Input Validation

**Required:**
- `<presentation.md>` - Path to presentation markdown file

**Optional:**
- `--output <path>` - Output file path (default: overwrites input with `_optimized` suffix)

## Instructions

1. **Verify input**: Confirm the presentation markdown exists and contains slide content
2. **Run optimization**:
   ```bash
   sg optimize presentation.md
   ```
3. **Verify output**: Confirm optimized file was created
4. **Report results**: Show quality scores (before/after if available), improvements made

## How It Works

The optimize step uses:
- **Extended thinking**: budget_tokens=4096 for deep analysis (temperature=1.0 required)
- **5-dimension scoring**: Readability, tone, structure, redundancy, citations
- **Representative sampling**: For decks >15 slides, samples representative slides rather than processing all
- **Batched optimization**: Large decks optimized in batches with quality verification
- **Assistant prefill**: Forces structured JSON output for consistent scoring

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `File not found` | Wrong path | Check file path |
| `No slides detected` | Malformed markdown | Verify presentation.md has proper slide markers |
| `Token limit exceeded` | Very large deck | Set `SG_OPTIMIZE_MAX_TOKENS=32768` or reduce slide count |

## Output

The optimize step produces an improved `presentation.md` (or `presentation_optimized.md`) with:
- Improved readability (shorter sentences, clearer language)
- Consistent tone across all slides
- Reduced redundancy between slides
- Better structural flow and transitions
- Quality score summary

## Next Step

After optimization completes, run graphics validation:
```bash
sg validate-graphics presentation.md
```
Or use `/sg-validate-graphics` to continue the pipeline.
