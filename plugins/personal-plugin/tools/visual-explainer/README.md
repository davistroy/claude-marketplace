---
description: Visual Explainer tool documentation - transforms text into AI-generated explanatory images
---

# Visual Explainer

A Python tool that transforms text or documents into AI-generated images that explain concepts visually. Uses Gemini Pro 3 for 4K image generation and Claude Sonnet Vision for quality evaluation with iterative refinement.

## Features

- **Concept Analysis**: Uses Claude to extract key concepts from text/documents
- **4K Image Generation**: Leverages Gemini Pro 3 for high-resolution explanatory images
- **Quality Evaluation**: Claude Vision evaluates generated images against success criteria
- **Iterative Refinement**: Automatically refines prompts based on evaluation feedback
- **Checkpoint/Resume**: Recover from interruptions with checkpoint support
- **Multiple Input Formats**: Supports .md, .txt, .docx, .pdf, and URLs
- **Bundled Styles**: Professional-clean and professional-sketch styles included

## Installation

```bash
pip install visual-explainer
```

Or install with optional format support:

```bash
# For DOCX support
pip install visual-explainer[docx]

# For PDF support
pip install visual-explainer[pdf]

# For web/URL support
pip install visual-explainer[web]

# For all optional formats
pip install visual-explainer[all]
```

## Configuration

Set the following environment variables (or use a `.env` file):

```bash
GOOGLE_API_KEY=AI...      # For Gemini image generation
ANTHROPIC_API_KEY=sk-ant-...  # For Claude analysis and evaluation
```

On first run, the tool will guide you through API key setup if keys are missing.

## Usage

### Command Line

```bash
# Generate images from a document
visual-explainer --input document.md --style professional-clean

# Use custom settings
visual-explainer --input document.md \
  --max-iterations 3 \
  --pass-threshold 0.9 \
  --output-dir ./output

# Interactive mode (no input specified)
visual-explainer

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
```

## CLI Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--input` | (interactive) | Input text, file path, or URL |
| `--style` | professional-clean | Style name or path to custom JSON |
| `--output-dir` | ./visual-explainer-output | Output directory |
| `--max-iterations` | 5 | Maximum refinement attempts per image |
| `--pass-threshold` | 0.85 | Minimum evaluation score to pass |
| `--resolution` | high | Image resolution (low, medium, high) |
| `--concurrency` | 3 | Maximum parallel generations |
| `--no-cache` | false | Disable concept analysis caching |
| `--resume` | - | Resume from checkpoint file |
| `--dry-run` | false | Show plan without generating |
| `--setup-keys` | - | Run API key setup wizard |

## Output Structure

```
visual-explainer-[topic]-[timestamp]/
  metadata.json           # Generation metadata
  concepts.json           # Extracted concept analysis
  summary.md              # Human-readable summary
  all-images/             # Final images (numbered)
    01-concept-name.jpg
    02-concept-name.jpg
  image-01/               # Per-image working directory
    attempt-01.jpg
    attempt-02.jpg
    prompt-v1.txt
    prompt-v2.txt
    evaluation-01.json
    final.jpg
  image-02/
    ...
```

## Cost Estimates

| Operation | Model | Est. Cost |
|-----------|-------|-----------|
| Concept Analysis | Claude Sonnet | ~$0.03 |
| Prompt Generation | Claude Sonnet | ~$0.02 |
| Image Generation | Gemini Pro 3 4K | ~$0.04/image |
| Image Evaluation | Claude Sonnet Vision | ~$0.02/eval |
| **Typical Run** | (3 images, 2 attempts avg) | **~$0.35** |

## Bundled Styles

- **professional-clean**: Clean, corporate-friendly visuals
- **professional-sketch**: Hand-drawn sketch aesthetic

Custom styles can be created following the style JSON schema (see styles/README.md).

## License

MIT
