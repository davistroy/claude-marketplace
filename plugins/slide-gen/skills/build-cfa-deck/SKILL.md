---
name: build-cfa-deck
description: Generate a complete, on-brand Chick-fil-A PowerPoint presentation from a topic using CFA brand guidelines, template layouts, and extracted brand assets. Use when you need a Chick-fil-A branded presentation, want to build a CFA deck with brand compliance, or need an on-brand presentation for a CFA audience.
argument-hint: "\"Topic\" [--slides 20] [--audience \"CFA Leadership\"] [--presenter \"Name\"]"
allowed-tools: Bash, Read, Write, Agent, Edit
effort: high
---

# Build CFA Deck

Generate a complete, on-brand Chick-fil-A PowerPoint presentation from a topic prompt. Uses the CFA "Support Now" PPTX template (64 layouts, 194 SVG icons, embedded Apercu fonts), extracted brand assets, and comprehensive brand guidelines.

No API key needed — content generation happens in this Claude Code session using your subscription.

## Pre-loaded Context

**Brand assets location:**
!`ls -d ~/dev/stratfield/slide-generator/examples/cfa-brand-assets/ 2>/dev/null && echo "Assets: OK" || echo "Assets: MISSING — run asset extraction first"`

**CFA template:**
!`ls -lh ~/dev/stratfield/slide-generator/examples/CFA\ PPT\ Template2.pptx 2>/dev/null && echo "Template: OK" || echo "Template: MISSING"`

**Brand guidelines:**
!`wc -l ~/dev/stratfield/slide-generator/examples/cfa-brand-guidelines-for-ppt.md 2>/dev/null || echo "Guidelines: MISSING"`

**python-pptx:**
!`python3 -c "import pptx; print('python-pptx: OK')" 2>/dev/null || echo "python-pptx: NOT INSTALLED — run: pip install python-pptx --break-system-packages"`

## Prerequisites

- `python-pptx` installed (`pip install python-pptx --break-system-packages`)
- CFA PPTX template at `~/dev/stratfield/slide-generator/examples/CFA PPT Template2.pptx`
- Brand guidelines at `~/dev/stratfield/slide-generator/examples/cfa-brand-guidelines-for-ppt.md`
- Brand assets extracted to `~/dev/stratfield/slide-generator/examples/cfa-brand-assets/`

## Input Validation

**Required:**
- `$ARGUMENTS` must contain a topic string (quoted). Example: `"The Future of Quick-Service Restaurants"`

**Optional flags (parse from $ARGUMENTS):**
- `--slides <N>` — number of slides (default: 20)
- `--audience <text>` — target audience (default: "CFA Leadership Team")
- `--presenter <text>` — presenter name for title/closing slides (default: empty)
- `--output <path>` — output .pptx file path (default: topic-slug in current directory)

If no topic is provided, ask the user for one. Do not proceed without a topic.

## Instructions

Follow these steps exactly. Do not skip or reorder.

### Step 1: Load Brand Context

Read the brand guidelines file. You need sections 1 (Color System), 5 (Layout System), 7 (Content Density Standards), and 8 (Deck Composition) to generate compliant content.

```
Read: ~/dev/stratfield/slide-generator/examples/cfa-brand-guidelines-for-ppt.md
```

Internalize these critical rules before generating content:
- **Color sequencing**: Never more than 3 consecutive white-background slides. Rotate navy, green, teal, red as visual breaks.
- **Content density**: Every content slide needs 3 layers (primary, supporting, contextual). Minimum word counts per slide type.
- **Headlines**: Insight-driven, not generic labels. Must contain a specific claim, number, or insight.
- **Data enrichment**: Every factual claim needs a specific number. No vague qualitative language.

### Step 2: Enumerate Template Layouts

Run this to get the exact layout names from the template:

```bash
python3 -c "
from pptx import Presentation
prs = Presentation(os.path.expanduser('~/dev/stratfield/slide-generator/examples/CFA PPT Template2.pptx'))
for i, layout in enumerate(prs.slide_layouts):
    phs = ', '.join([f'idx={p.placeholder_format.idx}:{p.placeholder_format.type}' for p in layout.placeholders])
    print(f'{i:2d}. {layout.name} [{phs}]')
import os
" 2>/dev/null || python3 -c "
import os
from pptx import Presentation
prs = Presentation(os.path.expanduser(os.path.join('~', 'dev', 'stratfield', 'slide-generator', 'examples', 'CFA PPT Template2.pptx')))
for i, layout in enumerate(prs.slide_layouts):
    phs = ', '.join([f'idx={p.placeholder_format.idx}' for p in layout.placeholders])
    print(f'{i:2d}. {layout.name} [{phs}]')
"
```

### Step 3: Generate the Slide Plan

Using the brand guidelines context and the template layout names, generate a complete slide plan as a JSON array. This is the creative core — you ARE the content engine.

For each slide, produce this structure:

```json
{
  "slide_number": 1,
  "slide_type": "cover|content|section_divider|stat_callout|data_chart|quote|split|card_grid|timeline|closing|...",
  "layout_name": "exact template layout name from Step 2",
  "background_color": "#hex or default",
  "headline": "Insight-driven headline with a specific claim or number",
  "subheadline": "Supporting context or null",
  "body_content": ["Substantive bullet 1 with specific data...", "Bullet 2...", "..."] or "Paragraph text...",
  "stats": [{"number": "$410B", "label": "QSR Market Size"}, ...] or null,
  "speaker_notes": "2-4 sentences adding context not visible on slide",
  "accent_color": "#hex for accent shapes",
  "footer_text": "Presenter | Title | Date"
}
```

**Content quality rules (enforce strictly):**
- Every headline contains a specific insight, number, or claim
- Every bullet point contains a specific fact, percentage, dollar amount, or date
- Content slides have 4-8 bullets OR 2-3 substantive paragraphs (2-3 sentences each)
- Stat callout slides have 2-4 large statistics with labels
- Quote slides have 40+ word quotes with full attribution
- Data slides describe specific chart data (type, axes, series, values)
- Speaker notes add background context not visible on the slide
- Word count minimums: content=80-150, stat=40-60, data=50-80, quote=60-100

**Color sequencing rules (enforce strictly):**
- Slide 1: Navy or Red background (title)
- Slides 2-3: White background (content)
- Slide 4: Navy or Green (section break)
- Slides 5-7: White with rotating accent colors (teal, then navy, then green)
- Slide 8: Teal or Navy (stat/impact)
- Continue pattern: never 3+ consecutive white slides
- Last slide: Navy or Red (closing)
- Distribution targets: ~25% Navy, ~15% Red, ~10% Green/Teal, ~45% White, ~5% Warm Gray

**Layout selection guidance:**
- Title: "Title Slide Dark Blue Pattern", "Title Slide Blue Values", "Title Slide Green Pattern"
- Section dividers: "Large Transition Dark Blue", "Large Transition Green", "Transition Pattern"
- Content: "Text Chat", "Text Dots", "Split Slide Medium Titles", "Triple Block Content"
- Stats/callouts: "Circle Callout", "Circle Callout 2", "Circle Callout 3"
- Quotes: "Large Quote Dark Blue", "Quote Green", "Quote White"
- Charts: "Small Title Chart", "Split with Chart"
- Team: "Team Slide Four Column", "Team Slide"
- Closing: "End Slide Dark Blue", "End Slide Green", "Final Words"

### Step 4: Write the Build Script

Write a Python script to `/tmp/build_cfa_deck.py` that:

1. Opens the CFA template
2. Removes all 28 sample slides (preserve layouts and masters)
3. For each slide in your JSON plan:
   a. Finds the matching layout by name
   b. Adds a new slide with that layout
   c. Populates placeholders (idx 0=title, 1=body, 10=footer, 12=slide number)
   d. If the layout lacks needed placeholders, adds text boxes at appropriate positions
   e. Applies background color if not "default"
   f. Adds speaker notes
   g. Adds the CFA Script Logo where appropriate (red on light backgrounds from `cfa-brand-assets/logos/`)
4. Saves the .pptx

**Critical python-pptx patterns:**

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os, json

EXAMPLES = os.path.expanduser("~/dev/stratfield/slide-generator/examples")
TEMPLATE = os.path.join(EXAMPLES, "CFA PPT Template2.pptx")
ASSETS = os.path.join(EXAMPLES, "cfa-brand-assets")

COLORS = {
    "cfa_red": RGBColor(0xDD, 0x00, 0x31),
    "white": RGBColor(0xFF, 0xFF, 0xFF),
    "navy": RGBColor(0x00, 0x4F, 0x71),
    "teal": RGBColor(0x3E, 0xB1, 0xC8),
    "slate": RGBColor(0x5B, 0x67, 0x70),
    "green": RGBColor(0x24, 0x9D, 0x6A),
    "dark_red": RGBColor(0xAF, 0x27, 0x2F),
    "gold": RGBColor(0xFF, 0xB5, 0x49),
    "warm_gray": RGBColor(0xEE, 0xED, 0xEB),
    "coral": RGBColor(0xF2, 0x6B, 0x43),
    "deep_navy": RGBColor(0x0A, 0x3C, 0x60),
    "light_blue": RGBColor(0xA7, 0xCE, 0xD8),
    "light_green": RGBColor(0xB2, 0xCF, 0xAE),
}

# Remove sample slides (reverse order to preserve indices)
def remove_samples(prs):
    slide_ids = [slide.slide_id for slide in prs.slides]
    for slide_id in reversed(slide_ids):
        rId = None
        for rel in prs.part.rels.values():
            if hasattr(rel, 'target_part') and hasattr(rel.target_part, 'slide_id'):
                if rel.target_part.slide_id == slide_id:
                    rId = rel.rId
                    break
        if rId:
            # Remove from slide list and relationships
            sldIdLst = prs.presentation.sldIdLst
            for sldId in sldIdLst:
                if sldId.get('id') == str(slide_id):
                    sldIdLst.remove(sldId)
                    break
            del prs.part.rels[rId]

# Find layout by name (fuzzy match)
def find_layout(prs, name):
    for layout in prs.slide_layouts:
        if layout.name.lower().strip() == name.lower().strip():
            return layout
    # Fuzzy: check if name is substring
    for layout in prs.slide_layouts:
        if name.lower() in layout.name.lower():
            return layout
    # Fallback to blank
    for layout in prs.slide_layouts:
        if "blank" in layout.name.lower() and "white" in layout.name.lower():
            return layout
    return prs.slide_layouts[-1]

# Populate placeholders
def set_placeholder(slide, idx, text, font_size=None, font_color=None, bold=None):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            ph.text = text
            if font_size or font_color or bold is not None:
                for para in ph.text_frame.paragraphs:
                    for run in para.runs:
                        if font_size: run.font.size = Pt(font_size)
                        if font_color: run.font.color.rgb = font_color
                        if bold is not None: run.font.bold = bold
            return True
    return False

# Add text box when no placeholder available
def add_textbox(slide, left, top, width, height, text, font_name="Apercu",
                font_size=14, font_color=None, bold=False, alignment=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = alignment
    run = p.runs[0]
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    if font_color:
        run.font.color.rgb = font_color
    return txBox
```

**Removing sample slides — use this reliable approach:**
```python
import copy
from lxml import etree

def remove_all_slides(prs):
    """Remove all existing slides while preserving layouts and masters."""
    sldIdLst = prs.presentation.sldIdLst
    rIds_to_remove = []
    for sldId in list(sldIdLst):
        rId = sldId.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        if rId:
            rIds_to_remove.append(rId)
        sldIdLst.remove(sldId)
    for rId in rIds_to_remove:
        if rId in prs.part.rels:
            del prs.part.rels[rId]
```

### Step 5: Run the Build Script

```bash
python3 /tmp/build_cfa_deck.py
```

Verify the output:
```bash
python3 -c "
from pptx import Presentation
import sys
prs = Presentation(sys.argv[1])
print(f'Slides: {len(prs.slides)}')
print(f'Dimensions: {prs.slide_width.inches:.3f}\" x {prs.slide_height.inches:.3f}\"')
for i, s in enumerate(prs.slides, 1):
    print(f'  Slide {i}: {len(s.shapes)} shapes')
" OUTPUT_PATH
```

### Step 6: Report Results

Tell the user:
- Output file path and size
- Slide count and layout distribution
- Color sequence used
- What to polish in PowerPoint (font rendering, real photos, layout tweaks)

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `python-pptx not installed` | Missing dependency | `pip install python-pptx --break-system-packages` |
| `Template not found` | Wrong path | Verify `CFA PPT Template2.pptx` exists in examples/ |
| `Guidelines not found` | Wrong path | Verify `cfa-brand-guidelines-for-ppt.md` exists in examples/ |
| `Layout not found` | Layout name mismatch | Script falls back to blank layout — check template layout names |
| `Slide removal fails` | python-pptx internal | Use the lxml-based removal approach |
| `Font not rendering` | Apercu not installed locally | Template embeds fonts — they render on open in PowerPoint |
| `Output too small (< 30KB)` | Slides not built properly | Check for python-pptx errors in script output |

## Output

The skill produces:
- A `.pptx` file with the specified number of slides
- Uses CFA template layouts (64 available), embedded fonts, and theme colors
- Content is substantive and data-rich (enforced by content density standards)
- Color sequence follows brand guidelines (navy/red/green/teal rotation)
- Ready for final polish in PowerPoint (swap in real photos, verify fonts, adjust layouts)

## Notes

- This skill generates content directly in the Claude Code session — no separate API key or API credits needed
- The CFA template embeds Apercu and Rooney fonts — they render correctly when opened in PowerPoint
- 194 SVG icons in the template are theme-aware and auto-recolor with theme changes
- For best results, specify a focused topic and target audience — generic topics produce generic content
- The skill handles all brand compliance automatically: color sequencing, content density, headline style, layout selection
