---
description: Generate detailed image generator prompts from content, optimized for 11x17 landscape prints
---

# Image Prompt Generator

Transform content into a comprehensive prompt for AI image generators. The resulting image should visually explain the given content in rich detail, suitable for printing landscape on 11x17 paper.

## Input Validation

**Required Arguments:**
- `<content-source>` - The content to visualize (see Input Types below)

**Optional Arguments:**
- `--style <style-file>` - Path to a style guide document with visual preferences

**Input Types:**

The `<content-source>` argument accepts three different input types:

| Type | Format | Example |
|------|--------|---------|
| **File path** | Path to a document file | `architecture.md`, `docs/design.md` |
| **Pasted content** | Raw content provided in chat | (paste content directly when prompted) |
| **Concept description** | Brief description in quotes | `"microservices communication patterns"` |

**Validation:**
If no content source is provided, display:
```
Error: Missing required argument

Usage: /develop-image-prompt <content-source> [--style <style-file>]

Input can be one of:
  1. File path      - Path to a document (e.g., architecture.md)
  2. Pasted content - Paste content directly when prompted
  3. Concept        - Description in quotes (e.g., "user auth flow")

Arguments:
  <content-source>   Content to visualize (required)
  --style <file>     Style guide for visual preferences (optional)

Examples:
  /develop-image-prompt architecture.md
  /develop-image-prompt process-flow.md --style brand-guidelines.md
  /develop-image-prompt "microservices communication patterns"
```

## Process

### Step 1: Gather Inputs

Identify the source content. Accept any of:
- File path to a document (markdown, text, etc.)
- Pasted content directly
- A concept or topic description

Optionally, identify a style document containing visual style preferences (colors, aesthetic, mood, etc.).

If neither is provided, ask the user for:
1. The content/concept to visualize
2. (Optional) A style guide or visual preferences

### Step 2: Analyze Content

Extract the key elements that must be visually represented:

1. **Core Concepts**: The main ideas that must be immediately clear
2. **Relationships**: How elements connect, flow, or interact
3. **Hierarchy**: What's most important vs. supporting details
4. **Components**: Individual pieces that make up the whole
5. **Process/Flow**: Any sequential or causal relationships
6. **Data/Metrics**: Numbers, comparisons, or quantitative elements

### Step 3: Analyze Style (if provided)

If a style document is provided, extract:
- Color palette preferences
- Visual aesthetic (modern, vintage, corporate, playful, etc.)
- Mood/tone (serious, optimistic, technical, approachable)
- Brand elements or constraints
- Typography preferences (if relevant to the image)
- Reference styles or inspirations

### Step 4: Construct the Prompt

Build a comprehensive image generation prompt with these sections:

#### A. Image Specifications
```
Format: Landscape orientation, 11x17 inches (17" wide × 11" tall)
Aspect Ratio: 1.545:1 (approximately 3:2)
Resolution: High resolution suitable for print (300 DPI equivalent detail)
```

#### B. Scene Composition
Describe the overall layout:
- What occupies the foreground, middle ground, background
- Visual flow direction (left-to-right for Western audiences)
- Focal point placement (rule of thirds)
- Negative space usage

#### C. Content Elements
For each key concept identified, specify:
- Visual representation (icon, diagram, illustration, metaphor)
- Position in the composition
- Size relative to other elements
- How it connects to related elements

#### D. Visual Style
Include specific style directives:
- Art style (infographic, isometric, flat design, 3D render, etc.)
- Color scheme with specific colors when known
- Lighting and atmosphere
- Level of detail and complexity
- Text integration approach (labels, callouts, titles)

#### E. Technical Requirements
- Clean edges suitable for printing
- No bleeding elements at margins
- Readable at arm's length when printed
- Professional presentation quality

### Step 5: Generate Output

Create a markdown file containing:

1. **Prompt Summary**: One-paragraph overview
2. **Full Prompt**: The complete, copy-ready prompt for the image generator
3. **Alternative Variations**: 2-3 style variations if applicable
4. **Usage Notes**: Recommended image generators and settings

## Output Format

**Output Location:** Save the output to the `reports/` directory. Create the directory if it doesn't exist.

**Filename Format:** `image-prompt-[topic]-YYYYMMDD-HHMMSS.md`

Example: `reports/image-prompt-architecture-20260114-143052.md`

Example structure:

```markdown
# Image Prompt: [Topic]

Generated: [timestamp]
Source: [input file or "direct input"]
Style: [style document or "default"]

## Specifications
- Dimensions: 11" × 17" landscape
- Aspect Ratio: 1.545:1
- Purpose: Print-ready explanatory visual

## Full Prompt

[Complete prompt text here - optimized for copy/paste into image generators]

## Style Variations

### Variation 1: [Style Name]
[Alternative prompt with different visual approach]

### Variation 2: [Style Name]
[Alternative prompt with different visual approach]

## Usage Notes

**Recommended Generators:**
- Midjourney: Use --ar 17:11 parameter
- DALL-E 3: Request landscape 1792x1024, describe as "wide format"
- Stable Diffusion: Set width=1700, height=1100

**Tips:**
- [Generator-specific tips]
```

## Prompt Construction Guidelines

### For Explanatory/Educational Content:
- Use clear visual hierarchies
- Include labeled sections or regions
- Employ consistent iconography
- Use arrows or flow lines for processes
- Balance detail with readability

### For Technical/Process Content:
- Flowchart or diagram style
- Step numbers or sequence indicators
- Clear start and end points
- Decision points highlighted
- Annotations for complex steps

### For Conceptual/Abstract Content:
- Metaphorical representations
- Symbolic imagery
- Spatial relationships showing connections
- Central concept with radiating elements
- Visual anchors for abstract ideas

### For Data-Heavy Content:
- Infographic style
- Charts integrated into illustration
- Comparative visual elements
- Scale indicators
- Key statistics prominently displayed

## Quality Checklist

Before finalizing, verify the prompt includes:
- [ ] All key concepts from the source content
- [ ] Clear visual hierarchy
- [ ] Specific style directives
- [ ] Composition guidance
- [ ] Print-ready specifications
- [ ] Readable at intended size
- [ ] Professional presentation quality
