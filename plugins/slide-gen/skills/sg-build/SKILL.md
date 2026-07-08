---
name: sg-build
description: Assemble final PowerPoint (.pptx) from presentation markdown and generated images. Use when you want to create the final PowerPoint, build the deck after image generation, or skip to building from presentation.md.
argument-hint: "<presentation.md> [--template generic] [--style style.json]"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Build Step

Assemble the final PowerPoint file (.pptx) from the presentation markdown and generated images. Uses python-pptx to create a professional slide deck with the selected template.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Available presentation files:**
!`ls -la *.md 2>/dev/null | grep -i pres || echo "No presentation files found"`

**Available images:**
!`ls images/ 2>/dev/null | wc -l || echo "0"`

**Available templates:**
!`sg list-templates 2>&1 || echo "Cannot list templates"`

## Prerequisites

- `slide-generator` package installed
- A `presentation.md` file with slide content
- Generated images in `images/` directory (optional — builds without images if missing)

## Input Validation

**Required:**
- `<presentation.md>` - Path to presentation markdown file

**Optional:**
- `--template <name>` - Template to use (default: `generic`). Use `sg list-templates` to see options
- `--style <path>` - Custom style JSON file for colors, fonts, sizing
- `--output <path>` - Output .pptx file path

## Instructions

1. **Verify input**: Confirm presentation markdown and images exist
2. **List templates** (if user hasn't specified):
   ```bash
   sg list-templates
   ```
3. **Run build**:
   ```bash
   sg build presentation.md --template generic
   ```
4. **Verify output**: Confirm .pptx file was created
5. **Report results**: Show file path, file size, slide count

## How It Works

The build step:
- Parses markdown into structured slide data (titles, bullets, notes, image refs)
- Classifies each slide type (title, content, two-column, image-heavy, etc.)
- Applies template layout rules for each slide type
- Embeds generated images at appropriate positions
- Adds speaker notes, slide numbers, and footers
- Uses dynamic year detection for copyright footers

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Template not found` | Invalid template name | Run `sg list-templates` |
| `No slides parsed` | Malformed markdown | Check presentation.md format |
| `Image not found` | Missing image file | Re-run `sg generate-images` or use `--skip-images` |
| `python-pptx error` | Template corruption | Try a different template |

## Output

The build step produces:
- A `.pptx` PowerPoint file ready for presentation
- File is named based on the topic or output flag

## Custom Templates

Install custom templates to `~/.slide-generator/templates/<name>/`:
- Must contain a `.pptx` template file
- Optional `template.py` extending `PresentationTemplate`
- Optional `style.json` for color/font configuration
