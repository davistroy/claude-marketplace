---
description: Generate detailed image generator prompts from content, with configurable dimensions and style options
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Image Prompt Generator

Transform content into a comprehensive prompt for AI image generators. The resulting image should visually explain the given content in rich detail, suitable for printing or digital display at the specified dimensions.

## Input Validation

**Required Arguments:**
- `<content-source>` - The content to visualize (see Input Types below)

**Optional Arguments:**
- `--style <style>` - Visual style preset or path to a style guide document (see Style Options below)
- `--dimensions <WxH>` - Output dimensions or aspect ratio (default: 11x17). See Dimensions section.
- `--no-prompt` - Skip interactive prompts. Use defaults for style selection and proceed directly to prompt generation.

**Input Types:**

The `<content-source>` argument accepts two input types:

| Type | Format | Example |
|------|--------|---------|
| **File path** | Path to a document file | `architecture.md`, `docs/design.md` |
| **Concept description** | Brief description in quotes | `"microservices communication patterns"` |

If no argument is provided and `--no-prompt` is not set, prompt interactively:

```text
What would you like to visualize?

1. File path — Provide a document to visualize (e.g., architecture.md)
2. Concept — Describe what you want visualized (e.g., "user auth flow")

Enter file path or concept in quotes:
```

If no argument is provided and `--no-prompt` is set, display the error and exit:
```text
Error: Missing required argument

Usage: /develop-image-prompt <content-source> [--style <style>] [--dimensions <WxH>] [--no-prompt]
Example: /develop-image-prompt architecture.md
Example: /develop-image-prompt "microservices communication patterns" --style infographic
```

**Full usage:**
```text
Usage: /develop-image-prompt <content-source> [--style <style>] [--dimensions <WxH>] [--no-prompt]

Arguments:
  <content-source>     File path or concept in quotes (required)
  --style <style>      Style preset or style guide file (optional)
  --dimensions <WxH>   Output dimensions or aspect ratio (optional, default: 11x17)

Examples:
  /develop-image-prompt architecture.md
  /develop-image-prompt "microservices communication patterns"
  /develop-image-prompt process-flow.md --style infographic --dimensions 16x9
  /develop-image-prompt "user auth flow" --dimensions square --style photorealistic
  /develop-image-prompt design-doc.md --style brand-guidelines.md
```

## Error Handling

| Error Condition | Detection | Response |
|----------------|-----------|----------|
| No input provided | No argument and no interactive response | Display usage message and exit |
| File not found | File path does not exist | "Error: File not found: [path]. Check the path and try again." |
| Empty file | File exists but has no content | "Error: File is empty: [path]. Provide a document with content to visualize." |
| Unsupported format | Binary file, .xlsx, .exe, etc. | "Error: Unsupported format ([ext]). Supported: .md, .txt, .html, .rst, .adoc" |
| Content too abstract | Input is a single word or extremely vague | "Warning: The input '[content]' is very abstract. Could you provide more context about what aspects to visualize? For example: key components, relationships, process flow, or data structure." |
| Invalid dimensions | Unrecognized dimension value | "Error: Invalid dimensions '[value]'. Use WxH (e.g., 11x17), a ratio (e.g., 16:9), or a preset (square, landscape, portrait)." |

## Dimensions

The `--dimensions` flag controls the output image size and aspect ratio. This affects composition, layout direction, and generator-specific parameters in the output.

**Default:** `11x17` (landscape, 17" wide x 11" tall, suitable for large-format printing)

| Value | Aspect Ratio | Resolution Guidance | Use Case |
|-------|-------------|-------------------|----------|
| `11x17` | ~1.55:1 | 5100x3300 px at 300 DPI | Large-format prints, posters, wall displays |
| `16x9` | 16:9 | 1920x1080 px | Presentations, widescreen displays |
| `4x3` | 4:3 | 1600x1200 px | Classic presentations, documents |
| `1x1` or `square` | 1:1 | 1024x1024 px | Social media, icons, thumbnails |
| `landscape` | 3:2 | 1536x1024 px | General landscape images |
| `portrait` | 2:3 | 1024x1536 px | Vertical displays, mobile, portraits |
| `8.5x11` or `letter` | ~1.29:1 | 3300x2550 px at 300 DPI | Standard print, letter-size handouts |
| Custom `WxH` | As specified | Calculated from dimensions | Any custom requirement |

When dimensions change from the default, adjust the prompt accordingly:
- **Square/portrait:** Use vertical composition, central focal point, stacked layout
- **Ultra-wide (16x9):** Use horizontal flow, left-to-right narrative, panoramic composition
- **Letter/standard:** Balance between detail and readability at typical viewing distance

## Style Options

The `--style` flag accepts either a preset name or a path to a style guide document.

**Style Presets:**

| Preset | Description | Best For |
|--------|-------------|----------|
| `infographic` | Clean data visualization with icons, charts, labeled sections, flat design | Data-heavy content, processes, comparisons |
| `photorealistic` | Realistic rendering with natural lighting, textures, depth of field | Physical systems, environments, product concepts |
| `illustration` | Hand-drawn or digital illustration style, expressive, editorial feel | Conceptual content, storytelling, editorial use |
| `diagram` | Technical diagram with precise lines, symbols, annotations, minimal color | Architecture, system design, engineering flows |
| `isometric` | 3D isometric projection, detailed components, technical but approachable | Infrastructure, system architecture, spatial relationships |
| `flat` | Minimal flat design with bold colors, simple shapes, modern aesthetic | UI concepts, marketing, clean presentations |
| `watercolor` | Soft, artistic watercolor rendering with blended colors | Creative presentations, non-technical audiences |
| `blueprint` | Technical blueprint style, white-on-blue, precise measurements | Engineering, construction, detailed specifications |

If `--style` points to a file path (e.g., `--style brand-guidelines.md`), read the file and extract:
- Color palette preferences
- Visual aesthetic guidance
- Brand elements or constraints
- Typography preferences
- Reference styles or inspirations

If no style is specified, infer the most appropriate style from the content type (technical content defaults to `diagram`, process content to `infographic`, conceptual content to `illustration`).

## Instructions

### Step 1: Gather Inputs

Read the content source (file or concept). If a style document is provided, read and extract visual preferences.

### Step 2: Analyze Content

Extract the key elements that must be visually represented:

1. **Core Concepts**: The main ideas that must be immediately clear
2. **Relationships**: How elements connect, flow, or interact
3. **Hierarchy**: What's most important vs. supporting details
4. **Components**: Individual pieces that make up the whole
5. **Process/Flow**: Any sequential or causal relationships
6. **Data/Metrics**: Numbers, comparisons, or quantitative elements

### Step 3: Construct the Prompt

Build a comprehensive image generation prompt with these sections:

#### A. Image Specifications
Include the resolved dimensions (from `--dimensions` flag or default):
```text
Format: [Orientation] orientation, [W]x[H] inches ([W]" wide x [H]" tall)
Aspect Ratio: [calculated ratio]
Resolution: High resolution suitable for [print/screen] ([DPI] DPI equivalent detail)
```

#### B. Scene Composition
Describe the overall layout:
- What occupies the foreground, middle ground, background
- Visual flow direction (left-to-right for landscape, top-to-bottom for portrait)
- Focal point placement (rule of thirds)
- Negative space usage

#### C. Content Elements
For each key concept identified, specify:
- Visual representation (icon, diagram, illustration, metaphor)
- Position in the composition
- Size relative to other elements
- How it connects to related elements

#### D. Visual Style
Include specific style directives (from `--style` flag, style document, or inferred):
- Art style (infographic, isometric, flat design, 3D render, etc.)
- Color scheme with specific colors when known
- Lighting and atmosphere
- Level of detail and complexity
- Text integration approach (labels, callouts, titles)

#### E. Technical Requirements
- Clean edges suitable for intended output (print or screen)
- Appropriate margins for the format
- Readable at intended viewing distance
- Professional presentation quality

### Step 4: Generate Style Variations

Generate 2-3 style variations when:
- The input content has multiple valid visual interpretations (e.g., a concept that could be shown as a flowchart OR a spatial metaphor)
- No specific `--style` was provided
- The content is conceptual rather than technical

Skip variations when:
- A specific `--style` preset or guide was provided
- The content has a single clear visual direction (e.g., a process flow is clearly a flowchart)
- The content is highly technical with an obvious diagram type

### Step 5: Generate Output

Create a markdown file containing:

1. **Prompt Summary**: One-paragraph overview
2. **Full Prompt**: The complete, copy-ready prompt for the image generator
3. **Style Variations**: 2-3 variations if applicable (see Step 4 rules)
4. **Generator-Specific Parameters**: Settings for each major generator
5. **Usage Notes**: Tips for getting the best results

## Output Format

**Output Location:** Save the output to the `reports/` directory. Create the directory if it doesn't exist.

**Filename Format:** `image-prompt-[topic]-YYYYMMDD-HHMMSS.md`

Example: `reports/image-prompt-architecture-20260114-143052.md`

Output structure:

```markdown
# Image Prompt: [Topic]

Generated: [timestamp]
Source: [input file or "direct input"]
Style: [style preset, style document, or "inferred: [type]"]
Dimensions: [WxH] ([orientation])

## Specifications
- Dimensions: [W]" x [H]" [orientation]
- Aspect Ratio: [ratio]
- Purpose: [Print-ready / Screen-optimized] [explanatory visual / infographic / diagram]

## Full Prompt

[Complete prompt text here - optimized for copy/paste into image generators]

## Style Variations

### Variation 1: [Style Name]
[Alternative prompt with different visual approach]

### Variation 2: [Style Name]
[Alternative prompt with different visual approach]

## Generator-Specific Parameters

**Midjourney:**
- Aspect ratio: --ar [W]:[H]
- Style: [suggested --style or --stylize values]
- [Other relevant parameters]

**DALL-E 3:**
- Size: [closest supported size]
- Style: [natural or vivid]
- [Description adjustments for DALL-E]

**Stable Diffusion:**
- Width: [px], Height: [px]
- Sampler: [suggested]
- CFG Scale: [suggested]
- [Other relevant parameters]

## Usage Notes

**Tips:**
- [Generator-specific tips for this content type]
- [Common pitfalls to avoid]
- [How to iterate on the prompt]
```

## Complete Example

Below is an end-to-end example showing how input content is transformed into a generated prompt.

**Input command:**
```text
/develop-image-prompt "microservices communication patterns" --dimensions 16x9 --style infographic
```

**Generated output (abbreviated):**

```markdown
# Image Prompt: Microservices Communication Patterns

Generated: 2026-02-28T14:30:00Z
Source: direct input
Style: infographic
Dimensions: 16x9 (landscape)

## Specifications
- Dimensions: 16:9 widescreen landscape
- Aspect Ratio: 16:9
- Purpose: Screen-optimized explanatory infographic

## Full Prompt

A clean, modern infographic explaining microservices communication patterns,
widescreen 16:9 landscape format. The composition flows left to right across
three major sections.

LEFT SECTION: "Synchronous Patterns" — Show a REST API call as two service
boxes connected by a solid arrow labeled "HTTP/REST", and a gRPC call as two
service boxes connected by a double-line arrow labeled "gRPC/Protocol Buffers".
Use a blue color palette for this section. Include a small latency indicator
icon (clock) showing request-response timing.

CENTER SECTION: "Asynchronous Patterns" — Show a message broker (drawn as a
central rounded rectangle labeled "Message Broker") with multiple service
boxes sending and receiving via dashed arrows. Include sub-patterns: pub/sub
(fan-out arrows), event sourcing (sequential numbered events), and CQRS
(split read/write paths). Use a green color palette. Include a queue depth
indicator.

RIGHT SECTION: "Service Mesh" — Show a grid of service boxes, each with a
small sidecar proxy (smaller attached box). Overlay a mesh network of thin
lines connecting all sidecars. Label key concepts: "Sidecar Proxy",
"Control Plane", "Data Plane". Use a purple color palette.

BOTTOM BAR: A comparison table strip showing: Pattern | Latency | Coupling |
Reliability | Use Case — for each of the three pattern categories.

HEADER: Bold title "Microservices Communication Patterns" with a subtitle
"Synchronous vs Asynchronous vs Service Mesh". Clean sans-serif typography.

Style: Flat design infographic with consistent iconography, minimal
gradients, white background, colored section backgrounds at 10% opacity,
professional data visualization aesthetic. No photorealistic elements.

## Generator-Specific Parameters

**Midjourney:**
- --ar 16:9
- --stylize 50
- --no photorealistic, 3d render

**DALL-E 3:**
- Size: 1792x1024 (landscape)
- Style: natural
- Describe as "clean infographic diagram"

**Stable Diffusion:**
- Width: 1920, Height: 1080
- Sampler: DPM++ 2M Karras
- CFG Scale: 7
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
- [ ] Specific style directives matching the selected style
- [ ] Composition guidance appropriate for the selected dimensions
- [ ] Resolution/size specifications for the target format
- [ ] Readable at intended viewing distance
- [ ] Professional presentation quality
- [ ] Generator-specific parameters for at least 2 generators

## Related Commands

- `/analyze-transcript` — Generate structured content that can be visualized
- `/assess-document` — Evaluate source document quality before prompt generation
- `/convert-markdown` — Convert documents to other formats for different outputs
