# Visual Explainer

A Python tool that transforms text or documents into AI-generated images that explain concepts visually. Uses Gemini Pro 3 for 4K image generation and Claude Sonnet Vision for quality evaluation with iterative refinement.

## Features

- **Concept Analysis**: Uses Claude to extract key concepts from text/documents
- **4K Image Generation**: Leverages Gemini Pro 3 for high-resolution explanatory images
- **Quality Evaluation**: Claude Vision evaluates generated images against success criteria
- **Iterative Refinement**: Automatically refines prompts based on evaluation feedback (up to 5 attempts by default)
- **Checkpoint/Resume**: Recover from interruptions with checkpoint support
- **Multiple Input Formats**: Supports .md, .txt, .docx, .pdf, and URLs
- **Bundled Styles**: Professional-clean and professional-sketch styles included
- **Concept Caching**: Avoids re-analyzing unchanged documents (SHA-256 content hash)

## Table of Contents

1. [Installation](#installation)
2. [API Key Setup](#api-key-setup)
3. [Configuration Options](#configuration-options)
4. [Usage](#usage)
5. [Bundled Styles](#bundled-styles)
6. [Style Customization](#style-customization)
7. [Output Structure](#output-structure)
8. [Cost Estimates](#cost-estimates)
9. [Troubleshooting](#troubleshooting)
10. [License](#license)

---

## Installation

### From Source (Development)

```bash
cd plugins/personal-plugin/tools/visual-explainer
pip install -e .
```

### With Optional Format Support

```bash
# For DOCX support
pip install -e ".[docx]"

# For PDF support
pip install -e ".[pdf]"

# For web/URL support
pip install -e ".[web]"

# For all optional formats
pip install -e ".[all]"
```

### Dependencies

**Required:**
- Python 3.10+
- httpx (async HTTP client)
- anthropic (Claude API)
- python-dotenv (environment variables)
- pydantic (data validation)
- aiofiles (async file I/O)
- rich (terminal UI)
- google-genai (Gemini image generation SDK)
- Pillow (image resizing for Claude evaluation)

**Optional:**
- python-docx (DOCX reading)
- PyPDF2 (PDF reading)
- beautifulsoup4 (URL content extraction)

---

## API Key Setup

The Visual Explainer requires two API keys:

| Service | Purpose | Environment Variable |
|---------|---------|---------------------|
| Google Gemini | Image generation | `GOOGLE_API_KEY` |
| Anthropic Claude | Concept analysis & image evaluation | `ANTHROPIC_API_KEY` |

### Interactive Setup Wizard

On first run, if API keys are missing, the tool launches an interactive setup wizard:

```bash
visual-explainer --setup-keys
```

Or simply run the tool without a `.env` file - it will guide you through setup.

### Manual Setup

Create a `.env` file in your project directory:

```bash
# Visual Explainer API Keys
# Generated: 2026-01-18 14:30:00

GOOGLE_API_KEY=AIzaSy...your-google-api-key
ANTHROPIC_API_KEY=sk-ant-api03-...your-anthropic-key
```

### Getting API Keys

#### Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Select or create a Google Cloud project
5. Copy the generated API key (starts with `AIzaSy...`)

**Free tier**: 60 requests/minute, no charge for basic usage.

#### Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Sign in or create an Anthropic account
3. Click "Create Key"
4. Name it (e.g., "visual-explainer")
5. Copy the key immediately (starts with `sk-ant-api03-...`)

**Free credits**: New accounts receive $5 in free credits.

### Key Validation

The setup wizard validates keys before saving:

- **Google**: Tests connectivity to Gemini model list endpoint
- **Anthropic**: Performs minimal API call to verify authentication

If validation fails, you'll see a clear error message with troubleshooting suggestions.

---

## Configuration Options

### CLI Parameters

| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `--input` | (interactive) | text, file path, URL | Input content source |
| `--style` | professional-clean | professional-clean, professional-sketch, or path | Visual style |
| `--output-dir` | ./visual-explainer-output | path | Output directory |
| `--max-iterations` | 5 | 1-10 | Maximum refinement attempts per image |
| `--pass-threshold` | 0.85 | 0.0-1.0 | Minimum evaluation score to pass |
| `--resolution` | high | low, medium, high | Image quality (high=4K) |
| `--aspect-ratio` | 16:9 | 16:9, 1:1, 4:3, 9:16, 3:4 | Image aspect ratio |
| `--concurrency` | 3 | 1-10 | Maximum parallel generations |
| `--no-cache` | false | flag | Disable concept analysis caching |
| `--resume` | - | checkpoint path | Resume from checkpoint file |
| `--dry-run` | false | flag | Show plan without generating |
| `--setup-keys` | - | flag | Run API key setup wizard |
| `--image-count` | (auto) | 1-10 | Override recommended image count |
| `--negative-prompt` | (internal) | string | Custom negative prompt (advanced) |

### Resolution Profiles

| Level | Size | Aspect Ratio | Best For |
|-------|------|--------------|----------|
| low | 1280x720 | 16:9 | Quick tests, drafts |
| medium | 1920x1080 | 16:9 | Standard presentations |
| high | 3200x1800 | 16:9 | Print, high-quality displays |

**Note**: High resolution (4K) images take ~60-120 seconds to generate.

### Internal Defaults

These are not exposed via CLI but can be customized in code:

**Default Negative Prompt** (always applied unless overridden):
```
no text, no words, no letters, no numbers, no watermarks, no logos,
no stock photo aesthetic, no borders, no frames, no signatures,
no artificial lighting artifacts, no lens flare
```

**Concept Cache Location**: `.cache/visual-explainer/concepts-[content-hash].json`

**Checkpoint Location**: `[output-dir]/checkpoint.json`

---

## Usage

### Command Line

```bash
# Generate images from a document
visual-explainer --input document.md --style professional-clean

# Use custom settings
visual-explainer --input document.md \
  --max-iterations 3 \
  --pass-threshold 0.9 \
  --output-dir ./output \
  --aspect-ratio 1:1

# Generate from raw text
visual-explainer --input "Explain how neural networks learn through backpropagation"

# Generate from URL
visual-explainer --input https://example.com/article.html

# Interactive mode (no input specified)
visual-explainer

# Dry run (see plan without generating)
visual-explainer --input document.md --dry-run

# Resume interrupted generation
visual-explainer --resume ./output/visual-explainer-topic-20260118/checkpoint.json

# Setup API keys
visual-explainer --setup-keys

# Show help
visual-explainer --help
```

### As a Claude Code Skill

The Visual Explainer is integrated as a Claude Code skill:

```
/visual-explainer "Explain the concept of neural networks"
/visual-explainer document.md
/visual-explainer architecture.md --style professional-sketch --image-count 5
/visual-explainer --dry-run "Microservices communication patterns"
```

### Interactive Flow

When running without `--input`, the tool guides you through:

1. **Input Selection**: Paste text, provide file path, or enter URL
2. **Concept Summary**: Shows extracted concepts and recommended image count
3. **Style Selection**: Choose bundled style or provide custom path
4. **Image Count Confirmation**: Accept recommendation or override
5. **Generation Progress**: Real-time status for each image and attempt
6. **Completion Summary**: Final scores, costs, and output location

---

## Bundled Styles

| Style | File | Description | Best For |
|-------|------|-------------|----------|
| **Professional Clean** | `professional-clean.json` | Modern, clean digital illustration with generous white space | Business, presentations, reports |
| **Professional Sketch** | `professional-sketch.json` | Hand-rendered watercolor and graphite sketch aesthetic | Creative, educational, informal |

### Style Selection Priority

1. **Explicit path**: `--style /path/to/custom.json` loads your custom file
2. **Named bundled style**: `--style professional-clean` loads from bundled styles
3. **Interactive selection**: If no style specified in interactive mode
4. **Default**: `professional-clean` when running non-interactively

---

## Style Customization

Custom styles can be created following the style JSON schema. See `styles/README.md` for full documentation.

### Quick Start: Create Custom Style

1. **Copy an existing style**:
   ```bash
   cp styles/professional-clean.json styles/my-brand-style.json
   ```

2. **Update metadata**:
   ```json
   {
     "StyleName": "Visual_Explainer_MyBrand",
     "StyleIntent": "Corporate brand-aligned concept visualizations"
   }
   ```

3. **Customize color palette** in `ColorSystem.PrimaryColors`:
   ```json
   {
     "PrimaryColors": [
       {
         "Name": "Brand Blue",
         "Hex": "#0066CC",
         "Role": "Primary accent for key elements"
       }
     ]
   }
   ```

4. **Update PromptRecipe** (most impactful section):
   ```json
   {
     "PromptRecipe": {
       "CoreStylePrompt": "Your detailed style description...",
       "ColorConstraintPrompt": "strict color palette: Brand Blue #0066CC...",
       "NegativePrompt": "cluttered, neon, garish, off-brand colors..."
     }
   }
   ```

5. **Test with your style**:
   ```bash
   visual-explainer --input test.md --style ./styles/my-brand-style.json
   ```

### Key Style Sections

| Section | Purpose | Impact |
|---------|---------|--------|
| `PromptRecipe.CoreStylePrompt` | Main style description | High - defines visual characteristics |
| `PromptRecipe.ColorConstraintPrompt` | Color enforcement | High - controls palette |
| `PromptRecipe.NegativePrompt` | What to avoid | Medium - prevents unwanted elements |
| `ColorSystem.PrimaryColors` | Brand colors | Medium - referenced in prompts |
| `PromptRecipe.QualityChecklist` | Evaluation criteria | Medium - affects pass/fail decisions |

---

## Output Structure

Generated output is organized in a timestamped directory:

```
visual-explainer-[topic-slug]-[YYYYMMDD-HHMMSS]/
  metadata.json           # Full generation metadata
  concepts.json           # Extracted concept analysis
  summary.md              # Human-readable summary report
  checkpoint.json         # Resume checkpoint (if interrupted)

  all-images/             # Final images only (numbered)
    01-foundation.jpg
    02-relationships.jpg
    03-synthesis.jpg

  image-01/               # Per-image working directory
    final.jpg             # Best version (copy of best attempt)
    prompt-v1.txt         # Original prompt
    attempt-01.jpg        # First generation attempt
    evaluation-01.json    # First evaluation result
    prompt-v2.txt         # Refined prompt (if needed)
    attempt-02.jpg        # Second attempt (if needed)
    evaluation-02.json    # Second evaluation (if needed)
    ...

  image-02/
    ...
```

### Metadata Schema

The `metadata.json` file contains:

```json
{
  "generation_id": "uuid",
  "timestamp": "2026-01-18T14:30:00Z",
  "input": {
    "type": "document",
    "path": "/path/to/input.md",
    "word_count": 1500,
    "content_hash": "sha256:abc123..."
  },
  "config": {
    "max_iterations": 5,
    "aspect_ratio": "16:9",
    "resolution": "high",
    "style": "professional-clean",
    "concurrency": 3,
    "pass_threshold": 0.85
  },
  "cache": {
    "concepts_cached": true,
    "cache_path": ".cache/visual-explainer/concepts-abc123.json"
  },
  "results": {
    "images_planned": 3,
    "images_generated": 3,
    "total_attempts": 7,
    "total_api_calls": 14,
    "estimated_cost": "$0.95"
  },
  "images": [
    {
      "image_number": 1,
      "final_attempt": 2,
      "total_attempts": 2,
      "final_score": 0.88,
      "final_path": "image-01/attempt-02.jpg"
    }
  ]
}
```

### Summary Report

The `summary.md` file provides a human-readable overview:

- Generation configuration
- Concept analysis summary
- Per-image results with scores
- Total cost estimate
- Any warnings or issues encountered

---

## Cost Estimates

### Per-Operation Costs

| Operation | Model | Est. Cost |
|-----------|-------|-----------|
| Concept Analysis | Claude Sonnet | ~$0.02-0.05 |
| Prompt Generation | Claude Sonnet | ~$0.02-0.03 |
| Image Generation | Gemini Pro 3 (4K) | ~$0.04-0.10 |
| Image Evaluation | Claude Sonnet Vision | ~$0.02-0.04 |

### Example Scenarios

| Scenario | Images | Avg Attempts | Est. Total |
|----------|--------|--------------|------------|
| Simple document, 1 image | 1 | 1.5 | ~$0.20-0.30 |
| Medium document, 3 images | 3 | 2 | ~$0.60-0.95 |
| Complex document, 5 images | 5 | 2.5 | ~$1.50-2.10 |
| All max iterations (edge case) | 3 | 5 | ~$1.80-2.50 |

### Cost Factors

**Lower costs:**
- Simpler documents (fewer concepts)
- Higher `--pass-threshold` (more likely to pass early)
- Lower resolution (`--resolution low`)
- Concept caching (re-running with same document)

**Higher costs:**
- Complex, multi-concept documents
- Lower `--pass-threshold` (more refinement attempts)
- 4K resolution (default)
- Disabled caching (`--no-cache`)

### Monitoring Costs

- Each run logs estimated cost in the completion summary
- `metadata.json` includes cost breakdown
- Use `--dry-run` to preview without incurring costs

---

## Troubleshooting

### API Key Issues

#### "Invalid API key" Error

**Symptoms**: Error on startup or first API call mentioning authentication failure.

**Solutions**:
1. Verify key is correctly copied (no extra spaces or newlines)
2. Re-run setup wizard: `visual-explainer --setup-keys`
3. Check `.env` file location (should be in project root or working directory)
4. For Google: Ensure Gemini API is enabled in your Google Cloud project
5. For Anthropic: Verify account has API access enabled

#### "API key not found" Error

**Symptoms**: Tool prompts for setup even though you have a `.env` file.

**Solutions**:
1. Ensure `.env` is in current working directory
2. Check variable names: `GOOGLE_API_KEY` and `ANTHROPIC_API_KEY` (exact spelling)
3. Verify no BOM (byte order mark) at start of `.env` file
4. Try loading manually: `source .env && echo $GOOGLE_API_KEY`

### Rate Limiting

#### "429 Too Many Requests" Error

**Symptoms**: Repeated errors during generation, especially with high concurrency.

**Solutions**:
1. Reduce concurrency: `--concurrency 1`
2. Wait a few minutes and retry
3. Check your API usage limits in respective consoles
4. For Gemini: Free tier allows 60 requests/minute
5. The tool implements automatic exponential backoff - wait and it will retry

#### Generation Taking Too Long

**Symptoms**: Images take several minutes to generate.

**Solutions**:
1. 4K images (high resolution) take 60-120 seconds each - this is normal
2. Use `--resolution medium` or `--resolution low` for faster generation
3. Reduce `--concurrency` if hitting rate limits
4. Check your internet connection

### Safety Filter Blocks

#### "Image blocked by safety filter" Warning

**Symptoms**: Some images fail with safety filter messages.

**Solutions**:
1. This is normal for certain content types
2. The tool automatically retries with a modified prompt
3. Check if your content contains potentially sensitive topics
4. Review the original prompt in `image-XX/prompt-v1.txt`
5. Try simplifying the concept or using different visual metaphors

#### All Images Blocked

**Symptoms**: Every generation attempt fails safety filter.

**Solutions**:
1. Review your input content for sensitive topics
2. Try a different style (sketch style may have different results)
3. Simplify the concept description
4. Break complex topics into smaller, simpler parts

### Memory/Timeout Issues

#### "Out of Memory" Error

**Symptoms**: Process crashes during generation, especially with multiple images.

**Solutions**:
1. Reduce `--concurrency 1` (process one image at a time)
2. Use `--resolution medium` (smaller images use less memory)
3. Close other memory-intensive applications
4. Restart and use `--resume` to continue from checkpoint

#### "Timeout" Error

**Symptoms**: API calls fail with timeout messages.

**Solutions**:
1. 4K generation has 300-second timeout - some images may take longer
2. Check your internet connection stability
3. Retry the same command (tool will resume from checkpoint)
4. Use `--resume [checkpoint-path]` to continue interrupted generation
5. Consider lower resolution for faster generation

### Checkpoint/Resume Issues

#### "Checkpoint not found" Error

**Symptoms**: Resume fails because checkpoint file doesn't exist.

**Solutions**:
1. Verify the checkpoint path is correct
2. Check the output directory for `checkpoint.json`
3. If checkpoint was corrupted, start fresh (delete output directory)
4. Checkpoints are saved after each image completes

#### "Invalid checkpoint" Error

**Symptoms**: Resume fails with JSON parsing error.

**Solutions**:
1. Checkpoint may be corrupted from interrupted write
2. Try opening `checkpoint.json` to see if it's valid JSON
3. If corrupted, delete checkpoint and restart generation
4. Previously completed images are preserved in the output directory

### Format Support Issues

#### "Unsupported file format" Error

**Symptoms**: Tool doesn't recognize input file type.

**Solutions**:
1. Supported formats: `.md`, `.txt`, `.docx`, `.pdf`, URLs
2. For DOCX: Install with `pip install -e ".[docx]"`
3. For PDF: Install with `pip install -e ".[pdf]"`
4. For URLs: Install with `pip install -e ".[web]"`
5. Use `pip install -e ".[all]"` for all format support

#### DOCX/PDF Reading Failures

**Symptoms**: Errors when processing Word or PDF files.

**Solutions**:
1. Verify optional dependencies are installed
2. For encrypted PDFs: Remove password protection first
3. For complex DOCX: Try exporting as plain text
4. Check file isn't corrupted (try opening in native app)

### Image Size Limit Issues

#### "Image exceeds 5 MB maximum" Error

**Symptoms**: Evaluation fails with Claude API error about image size.

**Solution**: This should be automatically handled by the tool's image resizing. If you see this error:
1. Verify Pillow is installed: `pip install Pillow`
2. The tool resizes images >3.5MB before sending to Claude (accounts for base64 encoding overhead)
3. High-resolution 4K images are typically 6-7.5MB - resizing preserves quality while meeting API limits

### Windows Path Issues

#### "The directory name is invalid" Error

**Symptoms**: Generation fails immediately when creating output directory.

**Solution**: This is caused by invalid characters in document titles (e.g., colons). The tool automatically sanitizes folder names, but if you see this:
1. Check your document title for characters: `:`, `*`, `?`, `"`, `<`, `>`, `|`
2. These are now automatically removed from folder names

### Common Warnings

| Warning | Meaning | Action |
|---------|---------|--------|
| "Concept cache hit" | Using cached analysis | Normal - saves API cost |
| "Low visual potential" | Concept hard to visualize | Consider simpler metaphors |
| "Max iterations reached" | Couldn't achieve pass threshold | Best attempt selected automatically |
| "Large document" | Input exceeds optimal size | May summarize before analysis |
| "Resizing image" | Image exceeds Claude's 5MB limit | Normal - automatic quality preservation |

---

## License

MIT

---

## Support

For issues, feature requests, or contributions:
- Repository: [davistroy/claude-marketplace](https://github.com/davistroy/claude-marketplace)
- Plugin: `plugins/personal-plugin/tools/visual-explainer`

For API-specific issues:
- Google Gemini: [Google AI Documentation](https://ai.google.dev/docs)
- Anthropic Claude: [Anthropic Documentation](https://docs.anthropic.com)
