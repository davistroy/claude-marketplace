# CFA Deck Build Helpers

Reusable python-pptx helper functions for `build-cfa-deck` Step 4 (Write the Build
Script). Read this file, then compose `/tmp/build_cfa_deck.py` (or `.tmp/build_cfa_deck.py`,
per house convention) from these functions plus your slide-plan-driven build loop.

**Verified against python-pptx 1.0.2** (see Prerequisites in `SKILL.md` — `remove_all_slides`
depends on a private attribute; re-verify this file if the installed version differs).

## Imports and Color Palette

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
```

## Removing Sample Slides

`Presentation()` returns a `pptx.presentation.Presentation` object — it has no nested
`.presentation` attribute (that name refers to itself, not a sub-object), so
`prs.presentation.sldIdLst` raises `AttributeError` before the slide list is ever reached.
The slide ID list lives on `prs.slides._sldIdLst` instead — a private (leading-underscore)
attribute with no public equivalent in 1.0.2.

Similarly, `prs.part.rels` is a `pptx.opc.package._Relationships`, which implements
`collections.abc.Mapping` but **not** `MutableMapping` — `del prs.part.rels[rId]` raises
`TypeError: '_Relationships' object doesn't support item deletion`. The supported removal
path is `prs.part.drop_rel(rId)`.

This is the only slide-removal implementation in this skill — do not reintroduce a second
one; a prior second implementation (`remove_samples`, keyed off `slide.slide_id` and a
`prs.part.rels.values()` scan) was removed because it shared the same broken attribute
access and never worked either.

```python
def remove_all_slides(prs):
    """Remove all existing slides while preserving layouts and masters."""
    sldIdLst = prs.slides._sldIdLst
    rIds_to_remove = []
    for sldId in list(sldIdLst):
        rId = sldId.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        if rId:
            rIds_to_remove.append(rId)
        sldIdLst.remove(sldId)
    for rId in rIds_to_remove:
        if rId in prs.part.rels:
            prs.part.drop_rel(rId)
```

Executed against a scratch copy of the real CFA template on 2026-07-29 (python-pptx 1.0.2):
5 sample slides in → 0 slides after `remove_all_slides` + save + reopen from disk; all 5
slide layouts and the slide master survived; a new slide could be added via
`prs.slides.add_slide(layout)` afterward and the deck still opened cleanly. A partial-removal
variant (remove 2 of 5) was also verified to drop the count by exactly 2, confirming the
function removes precisely the targeted slides rather than all-or-nothing.

## Finding a Layout by Name

```python
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
```

## Populating Placeholders

```python
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
```

## Adding a Text Box (no placeholder available)

```python
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
