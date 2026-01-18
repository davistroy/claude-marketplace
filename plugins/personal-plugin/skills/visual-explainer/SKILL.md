---
name: visual-explainer
description: Transform text or documents into AI-generated infographic pages that explain concepts visually using Gemini Pro 3 for generation and Claude Vision for quality evaluation
---

# Visual Concept Explainer

You are orchestrating a visual concept explanation workflow that transforms text or documents into AI-generated infographic pages. The tool uses Gemini Pro 3 (via google-genai SDK) for 4K image generation and Claude Sonnet Vision for quality evaluation with iterative refinement.

## Infographic Mode (Recommended)

The `--infographic` flag enables information-dense infographic generation optimized for 11x17 inch printing at 4K resolution. This mode:

- **Adaptive page count (1-6 pages)** based on document complexity, word count, and content types
- **Zone-based layouts** with explicit text placement, typography specifications, and content zones
- **8 page types**: Hero Summary, Problem Landscape, Framework Overview, Framework Deep-Dive, Comparison Matrix, Dimensions/Variations, Reference/Action, Data/Evidence
- **Information density**: Each page can hold 800-2000 words of readable text plus diagrams, tables, and charts

### Page Type Selection

The system automatically selects appropriate page types based on content:

| Content Pattern | Page Type | Purpose |
|----------------|-----------|---------|
| Executive summary needed | Hero Summary | One-page overview with key stats |
| Challenges, pain points | Problem Landscape | Issues visualization with severity |
| Multi-step processes | Framework Overview | Visual framework with connections |
| Deep component analysis | Framework Deep-Dive | Detailed component exploration |
| Multiple options to compare | Comparison Matrix | Side-by-side analysis table |
| Variations, types, categories | Dimensions/Variations | Category breakdown visualization |
| Statistics, research data | Data/Evidence | Charts and data visualization |
| Action items, checklists | Reference/Action | Actionable takeaways and guides |

## Technical Notes

**Image Generation:**
- Uses `google-genai` SDK with model `gemini-3-pro-image-preview`
- Configuration: `response_modalities=["IMAGE"]` with `ImageConfig` for aspect ratio/size
- 4K images are approximately 6-7.5MB each (JPEG format)

**Image Evaluation:**
- Claude Vision API has 5MB limit for base64-encoded images
- Tool automatically resizes images >3.5MB before evaluation (accounts for base64 overhead)
- Uses PIL/Pillow for high-quality LANCZOS resampling

**Platform Compatibility:**
- Windows: Folder names are sanitized to remove invalid characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`)
- All platforms: Full Unicode support in Rich terminal UI

**Tested Results (4 documents, 17 images):**
- Formats tested: URL (Substack), Markdown, DOCX
- Average scores: 0.76-0.88 (all passing with threshold 0.75)
- Generation time: 5-10 minutes per document (~2 min/image including analysis)
- Only 1 retry needed across 17 images (image scored 0.72 → refined to 0.82)
- Recommended pass threshold: 0.75-0.85 for good quality without excessive refinement

## Input Validation

**Required Arguments:**
- Input content (one of the following):
  - Raw text (pasted directly)
  - Document path (`.md`, `.txt`, `.docx`, `.pdf`)
  - URL (to fetch and extract content)

**Optional Arguments:**
| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `--infographic` | false | flag | **Recommended.** Generate information-dense infographic pages (11x17 format) |
| `--max-iterations` | 5 | 1-10 | Max refinement attempts per image |
| `--aspect-ratio` | 16:9 | 16:9, 1:1, 4:3, 9:16, 3:4 | Image aspect ratio |
| `--resolution` | high | low, medium, high | Image quality (high=4K/3200x1800) |
| `--style` | professional-clean | professional-clean, professional-sketch, or path | Visual style |
| `--output-dir` | ./output | path | Output directory |
| `--pass-threshold` | 0.85 | 0.0-1.0 | Score required to pass evaluation |
| `--concurrency` | 3 | 1-10 | Max concurrent image generations |
| `--no-cache` | false | flag | Force fresh concept analysis |
| `--resume` | null | path | Resume from checkpoint file |
| `--dry-run` | false | flag | Show plan without generating |
| `--setup-keys` | false | flag | Force re-run API key setup |
| `--json` | false | flag | Output results as JSON (for programmatic use) |

**Input Format Handling:**

| Format | Handling |
|--------|----------|
| `.md`, `.txt` | Direct text extraction |
| `.docx` | Requires `python-docx` - extracts paragraphs preserving headings |
| `.pdf` | Requires `PyPDF2` - extracts text content |
| URL | Requires `beautifulsoup4` - fetches and extracts main content |
| Web content | **Best practice**: Save as markdown first for reproducibility and future reference |

**DOCX Conversion Tip:**
For best results with DOCX files, pre-convert to markdown:
```python
from docx import Document
doc = Document('document.docx')
with open('document.md', 'w') as f:
    for para in doc.paragraphs:
        style = para.style.name if para.style else ''
        if style.startswith('Heading'):
            level = int(style[-1]) if style[-1].isdigit() else 1
            f.write('#' * level + ' ' + para.text + '\n\n')
        else:
            f.write(para.text + '\n\n')
```

**Environment Requirements:**
API keys must be configured in environment variables or `.env` file:
- `GOOGLE_API_KEY` - For Gemini Pro 3 image generation
- `ANTHROPIC_API_KEY` - For Claude concept analysis and image evaluation

## Tool vs Claude Responsibilities

Understanding what the Python tool handles vs what you (Claude) must do:

| Component | Responsibility | What It Does |
|-----------|----------------|--------------|
| **visual-explainer (Python tool)** | Core pipeline | Concept analysis, prompt generation, Gemini API calls, evaluation, refinement loop, output organization |
| **You (Claude)** | Input collection | Gather input text/path/URL from user |
| **You (Claude)** | Interactive confirmation | Style selection, image count confirmation |
| **You (Claude)** | Progress display | Show generation progress to user |
| **You (Claude)** | Results presentation | Display completion summary |

## Workflow

### Phase 1: Setup and Dependency Check

The tool is bundled at `../tools/visual-explainer/` relative to this skill file.

**Step 1: Set Up Tool Path**

```bash
# Determine the plugin directory
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/personal-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/visual-explainer/src"
```

**Step 2: Check Dependencies**

The tool automatically checks dependencies when run. You can also do a dry-run to verify setup:

```bash
PYTHONPATH="$TOOL_SRC" python -m visual_explainer --dry-run --input "test content"
```

Required packages:
- Core: `google-genai`, `anthropic`, `httpx`, `python-dotenv`, `pydantic`, `aiofiles`, `rich`, `pillow`
- Optional (format-specific): `python-docx` (DOCX), `PyPDF2` (PDF), `beautifulsoup4` (URLs)

**If packages are missing, install them:**
```bash
pip install google-genai anthropic httpx python-dotenv pydantic aiofiles rich pillow
pip install python-docx PyPDF2 beautifulsoup4  # Optional, for specific formats
```

### Phase 2: API Key Setup (if needed)

**If API keys are missing, guide the user through setup:**

```
API Key Setup Required
======================

This tool requires two API keys:
- Google Gemini API - for image generation
- Anthropic API - for concept analysis and image evaluation

Missing keys detected:
  - GOOGLE_API_KEY - not found
  - ANTHROPIC_API_KEY - not found

Would you like me to help you set up the missing API keys? (yes/skip)
```

**For GOOGLE_API_KEY:**
```
GOOGLE API KEY SETUP (for Gemini)
---------------------------------

1. Go to: https://aistudio.google.com/apikey

2. Sign in with your Google account

3. Click "Create API key"

4. Select or create a Google Cloud project

5. Copy the key (starts with "AIza...")

Note: Gemini image generation requires credits.
Free tier: 60 requests/minute.

Paste your Google API key (or 'skip' to skip this provider):
```

**For ANTHROPIC_API_KEY:**
```
ANTHROPIC API KEY SETUP
-----------------------

1. Go to: https://console.anthropic.com/settings/keys

2. Sign in or create an account

3. Click "Create Key"

4. Name it something like "visual-explainer"

5. Copy the key (starts with "sk-ant-...")

Note: New accounts get $5 free credits.

Paste your Anthropic API key (or 'skip'):
```

**After collecting keys, create/update .env file and confirm:**
```
API keys saved to .env

Keys configured:
  - GOOGLE_API_KEY: (AIza...xxxx)
  - ANTHROPIC_API_KEY: (sk-ant-...xxxx)

Security reminder: Never commit .env to version control.
```

### Phase 3: Input Collection

If no input was provided in arguments, prompt:

```
I'll help you create visual explanations for your content.

Please provide your input in one of these formats:
1. Paste text directly
2. Provide a file path (e.g., ./docs/concept.md)
3. Provide a URL to fetch content from
```

### Phase 4: Content Analysis

After receiving input, run concept analysis:

```bash
PYTHONPATH="$TOOL_SRC" python -m visual_explainer analyze \
  --input "<input_text_or_path>" \
  --output-json
```

Display the analysis summary:

```
Content Analysis
================
Document: "Understanding Quantum Entanglement"
Word Count: 1,847 words
Key Concepts: 5 concepts identified
Recommended Images: 3 images

Concept Flow:
1. Classical Physics Background
   -> 2. Quantum Superposition
   -> 3. Entanglement Phenomenon
   -> 4. Applications
   -> 5. Future Implications
```

### Phase 5: Style Selection (Interactive)

Prompt for style selection:

```
Visual Style Selection
======================
What style would you prefer?

1. Professional Clean (Recommended)
   - Clean, corporate-ready with warm accents
   - Best for: Business, presentations, reports

2. Professional Sketch
   - Hand-drawn sketch aesthetic
   - Best for: Creative, educational, informal

3. Custom
   - Provide path to your own style JSON

4. Skip (use Professional Clean default)

Select style [1-4]:
```

### Phase 6: Image Count Confirmation

```
Image Generation Plan
=====================
Based on analysis, I recommend 3 images:

Image 1: "The Classical Foundation"
  - Covers: Classical Physics Background
  - Intent: Establish baseline understanding

Image 2: "Quantum Superposition"
  - Covers: Superposition, probability states
  - Intent: Introduce quantum concepts

Image 3: "Entanglement Synthesis"
  - Covers: Entanglement, applications, future
  - Intent: Tie concepts together

Would you like to:
1. Proceed with 3 images (Recommended)
2. Use fewer images (condense concepts)
3. Use more images (expand detail)
4. Adjust settings (aspect ratio, iterations)
```

### Phase 7: Generation Execution

Execute the full generation pipeline:

```bash
PYTHONPATH="$TOOL_SRC" python -m visual_explainer generate \
  --input "<input_text_or_path>" \
  --style "<selected_style>" \
  --max-iterations <n> \
  --aspect-ratio "<ratio>" \
  --resolution "<level>" \
  --output-dir "<output_path>" \
  --pass-threshold <threshold> \
  --concurrency <n>
```

**Progress Display Format:**

```
Starting Image Generation
=========================

Image 1 of 3: "The Classical Foundation"
----------------------------------------

Attempt 1/5:
  [=========>         ] Generating... (4.2s)
  Generated
  Evaluating...
    - Concept clarity: 72%
    - Visual appeal: 85%
    - Flow continuity: 60%
  Overall: 72% - NEEDS_REFINEMENT

Attempt 2/5:
  Refining: Adding visual flow indicators
  [=========>         ] Generating... (3.8s)
  Generated
  Evaluating...
    - Concept clarity: 91%
    - Visual appeal: 88%
    - Flow continuity: 85%
  Overall: 88% - PASS

Image 1 complete. Best version: Attempt 2

Image 2 of 3: "Quantum Superposition"
-------------------------------------
...
```

### Phase 8: Completion Summary

```
Generation Complete
===================

Results:
  - Images generated: 3 of 3
  - Total attempts: 7
  - Average quality score: 89%
  - Estimated cost: $0.70

Output saved to:
  ./output/visual-explainer-quantum-entanglement-20260118-143052/

Final Images:
  1. 01-classical-foundation.jpg (Score: 88%)
  2. 02-quantum-superposition.jpg (Score: 91%)
  3. 03-entanglement-synthesis.jpg (Score: 88%)

Output Structure:
  metadata.json          # Full generation metadata
  concepts.json          # Extracted concepts
  summary.md             # Human-readable summary
  all-images/            # Final images only
    01-classical-foundation.jpg
    02-quantum-superposition.jpg
    03-entanglement-synthesis.jpg
  image-01/              # All attempts for image 1
    final.jpg
    prompt-v1.txt
    attempt-01.jpg
    evaluation-01.json
    ...

Would you like to:
1. View the summary report
2. Regenerate a specific image
3. Open output folder
```

## Resume from Checkpoint

If generation was interrupted, resume with:

```bash
PYTHONPATH="$TOOL_SRC" python -m visual_explainer generate \
  --resume "./output/visual-explainer-[topic]-[timestamp]/checkpoint.json"
```

The checkpoint contains:
- Generation state
- Completed images
- Current progress
- Configuration used

## Cost Estimation

**Estimated costs per session:**

| Scenario | Images | Avg Attempts | Est. Total |
|----------|--------|--------------|------------|
| Simple doc, 1 image | 1 | 2 | ~$0.28 |
| Medium doc, 3 images | 3 | 2.3 | ~$0.95 |
| Complex doc, 5 images | 5 | 3 | ~$2.10 |

**Component costs:**
- Gemini image generation: ~$0.10 per image
- Claude concept analysis: ~$0.02 per document
- Claude image evaluation: ~$0.03 per evaluation

## Error Handling

| Error | Response |
|-------|----------|
| Missing API key | Run setup wizard, guide user through key creation |
| Rate limit (429) | Exponential backoff, respect Retry-After header |
| Safety filter | Log, skip to next attempt with modified prompt |
| Timeout | Retry with increased timeout (up to 5 min) |
| All attempts exhausted | Select best attempt, report scores |
| Network error | Retry up to 3 times with backoff |

## Examples

**Infographic mode (recommended for complex documents):**
```
/visual-explainer --input docs/architecture-overview.md --infographic
```

**Infographic with dry-run preview:**
```
/visual-explainer --input whitepaper.md --infographic --dry-run
```

**Basic usage (interactive):**
```
/visual-explainer
```

**With document path:**
```
/visual-explainer --input docs/architecture-overview.md
```

**Custom settings:**
```
/visual-explainer --input concept.txt --style professional-sketch --max-iterations 3 --aspect-ratio 1:1
```

**High quality infographic:**
```
/visual-explainer --input whitepaper.md --infographic --resolution high --max-iterations 7 --pass-threshold 0.90
```

**Dry run (plan only):**
```
/visual-explainer --input document.md --dry-run
```

**Resume interrupted generation:**
```
/visual-explainer --resume ./output/visual-explainer-topic-20260118/checkpoint.json
```

## Execution Summary

Follow these steps in order:

1. **Setup** - Parse arguments, set up tool path
2. **Dependency Check** - Verify packages and API keys
3. **API Key Setup** - If missing, guide user through setup wizard
4. **Input Collection** - Get text/path/URL from user (if not provided)
5. **Content Analysis** - Extract concepts, determine image count
6. **Style Selection** - Let user choose or use default
7. **Image Count Confirmation** - Confirm plan with user
8. **Generation Execution** - Run full pipeline with progress display
9. **Completion Summary** - Display results and output locations
