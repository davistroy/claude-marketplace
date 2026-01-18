# IMAGE_GEN_PLAN.md

## Skill: Visual Concept Explainer

**Purpose:** Transform text or documents into a series of AI-generated images that fully explain the concepts, thoughts, and ideas in a logical, flowing visual narrative.

---

## 1. Executive Summary

This skill will:
1. Accept text input or a document path
2. Analyze the content to identify key concepts and their logical flow
3. Determine whether concepts can be explained in 1 image or require multiple images
4. Generate detailed image prompts for each visual
5. Call Google Gemini Pro 3 (gemini-3-pro-image-preview) to generate each image
6. Evaluate each generated image against original intent using Claude's vision capabilities
7. Iterate up to N times (default: 5, user-configurable) to refine prompts and regenerate
8. Store all images in an organized output folder with metadata

---

## 2. Architecture Overview

### 2.1 Component Structure

```
plugins/
  personal-plugin/
    skills/
      visual-explainer/
        SKILL.md                  # Main skill definition
    tools/
      visual-explainer/
        pyproject.toml            # Tool dependencies
        styles/                   # Pre-built style configurations
          professional-clean.json   # Clean, corporate-ready (default)
          professional-sketch.json  # Hand-drawn sketch aesthetic
          README.md                 # Style documentation
        src/
          visual_explainer/
            __init__.py
            __main__.py           # Entry point
            cli.py                # CLI interface
            api_setup.py          # First-run API key setup wizard
            concept_analyzer.py   # Document → concept extraction
            prompt_generator.py   # Concept → image prompt
            image_generator.py    # Gemini API integration
            image_evaluator.py    # Vision-based quality check
            style_loader.py       # Load and merge style configs
            models.py             # Data structures
            config.py             # Configuration
```

### 2.2 Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   Input Text    │────▶│ Concept Analyzer │────▶│ Prompt Generator  │
│   or Document   │     │ (Claude/LLM)     │     │ (Claude/LLM)      │
└─────────────────┘     └──────────────────┘     └───────────────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌───────────────────┐
                        │ Image Evaluator  │◀────│ Image Generator   │
                        │ (Claude Vision)  │     │ (Gemini Pro 3)    │
                        └──────────────────┘     └───────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
            ┌───────────┐             ┌───────────────┐
            │   PASS    │             │     FAIL      │
            │  (Save)   │             │ (Refine & Retry)
            └───────────┘             └───────────────┘
```

---

## 3. Detailed Workflow

### Phase 1: Input Processing

**Inputs accepted:**
- Raw text (pasted directly)
- Document path (`.md`, `.txt`, `.docx`, `.pdf`)
- URL (fetch and extract content)

**Processing:**
1. Detect input type
2. Extract plain text content
3. Estimate complexity (word count, concept density)
4. Determine target audience (infer or ask user)

### Phase 2: Concept Analysis

**Claude analyzes the text to produce:**

```json
{
  "title": "Document/Concept Title",
  "summary": "One-paragraph summary",
  "target_audience": "Technical professionals | General public | Students | etc.",
  "concepts": [
    {
      "id": 1,
      "name": "Core Concept Name",
      "description": "What this concept means",
      "relationships": ["concept_id:2", "concept_id:3"],
      "complexity": "simple | moderate | complex",
      "visual_potential": "high | medium | low"
    }
  ],
  "logical_flow": [
    {"from": 1, "to": 2, "relationship": "leads_to | supports | contrasts"},
    {"from": 2, "to": 3, "relationship": "builds_on"}
  ],
  "recommended_image_count": 3,
  "reasoning": "Why this number of images works best"
}
```

### Phase 3: Image Count Decision

**Decision Matrix:**

| Document Complexity | Concept Count | Recommended Images |
|---------------------|---------------|-------------------|
| Simple (< 500 words) | 1-2 concepts | 1 image |
| Moderate (500-2000 words) | 3-5 concepts | 2-3 images |
| Complex (2000+ words) | 6+ concepts | 4-6 images |
| Highly technical | Many interrelated | Consider infographic series |

**User Override:** Allow user to specify desired image count if they disagree with recommendation.

### Phase 4: Prompt Generation

For each planned image, generate:

```json
{
  "image_number": 1,
  "image_title": "The Foundation: Understanding X",
  "concepts_covered": [1, 2],
  "visual_intent": "Show the relationship between A and B in a way that...",
  "prompt": {
    "main_prompt": "Detailed image generation prompt...",
    "style_guidance": "Clean, professional infographic style...",
    "color_palette": "Blues and greens for trust and growth...",
    "composition": "Left-to-right flow showing progression...",
    "avoid": "Do not include text, complex charts, or..."
  },
  "success_criteria": [
    "Shows clear visual metaphor for concept X",
    "Demonstrates relationship between A and B",
    "Appropriate for target audience",
    "Flows naturally to next image"
  ],
  "flow_connection": {
    "previous": null,
    "next": 2,
    "transition_intent": "This image sets up the foundation for..."
  }
}
```

### Phase 5: Image Generation

**Using Gemini Pro 3 API:**

```python
# API Configuration (from slide-generator patterns)
MODEL_ID = "gemini-3-pro-image-preview"
API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Request structure
payload = {
    "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
    "generationConfig": {
        "responseModalities": ["IMAGE"],
        "imageConfig": {
            "aspectRatio": "16:9",  # or user-specified
            "imageSize": "LARGE",   # 4K for quality
        },
    },
}
```

**Generation Parameters:**
- Aspect ratio: 16:9 (default) | 1:1 | 4:3 | 9:16
- Resolution: STANDARD (1280x720) | LARGE (3200x1800)
- Timeout: 300 seconds for 4K images

### Phase 6: Image Evaluation

**Claude Vision evaluates each generated image:**

```json
{
  "image_id": 1,
  "iteration": 1,
  "evaluation": {
    "overall_score": 0.75,  // 0-1 scale
    "criteria_scores": {
      "concept_clarity": 0.8,
      "visual_appeal": 0.7,
      "audience_appropriateness": 0.9,
      "flow_continuity": 0.6
    },
    "strengths": [
      "Clear visual metaphor for the core concept",
      "Good use of color to distinguish elements"
    ],
    "weaknesses": [
      "Relationship between A and B not immediately obvious",
      "Could better connect to next image in sequence"
    ],
    "missing_elements": [
      "Visual indicator of progression"
    ],
    "verdict": "NEEDS_REFINEMENT",  // PASS | NEEDS_REFINEMENT | FAIL
    "refinement_suggestions": [
      "Add visual arrow or flow indicator",
      "Increase contrast between concept zones"
    ]
  }
}
```

**Scoring Thresholds:**
- **PASS** (≥ 0.85): Accept image, move to next
- **NEEDS_REFINEMENT** (0.5-0.84): Refine prompt, regenerate
- **FAIL** (< 0.5): Significant prompt rewrite needed

### Phase 7: Iterative Refinement

**Loop Logic:**

```
FOR each image IN planned_images:
    attempt = 0
    max_attempts = user_specified OR 5

    WHILE attempt < max_attempts:
        attempt += 1

        IF attempt == 1:
            prompt = original_prompt
        ELSE:
            prompt = refine_prompt(original_prompt, evaluation_feedback, attempt)

        image_bytes = generate_image(prompt)
        save_image(image_bytes, image_number, attempt)

        evaluation = evaluate_image(image_bytes, success_criteria)

        IF evaluation.verdict == "PASS":
            mark_as_final(image_number, attempt)
            BREAK

        IF attempt == max_attempts:
            select_best_attempt(image_number)
            log_exhaustion_report(image_number, all_evaluations)
```

**Prompt Refinement Strategy:**

| Attempt | Strategy |
|---------|----------|
| 2 | Add specific fixes from evaluation feedback |
| 3 | Strengthen weak areas, simplify complex elements |
| 4 | Try alternative visual metaphor |
| 5 | Fundamental restructure of composition |

### Phase 8: Output Organization

**Directory Structure:**

```
output/
  visual-explainer-[topic-slug]-[timestamp]/
    metadata.json                 # Full generation metadata
    concepts.json                 # Extracted concepts

    image-01/
      final.jpg                   # Best version (symlink or copy)
      prompt-v1.txt               # Original prompt
      attempt-01.jpg              # First attempt
      evaluation-01.json          # First evaluation
      prompt-v2.txt               # Refined prompt (if needed)
      attempt-02.jpg              # Second attempt (if needed)
      evaluation-02.json          # Second evaluation (if needed)
      ...

    image-02/
      ...

    summary.md                    # Human-readable summary
    all-images/                   # Final images only, numbered
      01-foundation.jpg
      02-relationships.jpg
      03-synthesis.jpg
```

**Metadata Schema:**

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
    "resolution": "LARGE",
    "style": "professional",
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
    "total_api_calls": 7,
    "estimated_cost": "$0.70"
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

---

## 4. User Interface (Skill Flow)

### 4.1 Invocation

```
/visual-explainer
```

or

```
/visual-explainer --input document.md --max-iterations 3 --aspect-ratio 1:1
```

### 4.2 Interactive Flow

```
User: /visual-explainer

Claude: I'll help you create visual explanations for your content.

Please provide your input in one of these formats:
1. Paste text directly
2. Provide a file path (e.g., ./docs/concept.md)
3. Provide a URL to fetch content from

[User pastes text or provides path]

Claude: I've analyzed your content. Here's what I found:

**Document:** "Understanding Quantum Entanglement"
**Word Count:** 1,847 words
**Key Concepts:** 5 concepts identified
**Recommended Images:** 3 images

**Concept Flow:**
1. Classical Physics Background → 2. Quantum Superposition → 3. Entanglement Phenomenon → 4. Applications → 5. Future Implications

**Visual Style:** What style would you prefer?
1. Professional Clean (Recommended) - Clean, corporate-ready with warm accents
2. Professional Sketch - Hand-drawn sketch aesthetic, creative feel
3. Custom - Provide path to your own style JSON
4. Skip (use Professional Clean default)

[User selects or skips]

Would you like to:
1. Proceed with 3 images (Recommended)
2. Use fewer images (condense concepts)
3. Use more images (expand detail)
4. Adjust other settings (aspect ratio, iterations)
```

### 4.3 Generation Progress

```
Claude: Starting image generation...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Image 1 of 3: "The Classical Foundation"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Attempt 1/5:
[■■■■■■■■░░] Generating...

✓ Generated (4.2s)
✓ Evaluating...
  - Concept clarity: 72%
  - Visual appeal: 85%
  - Flow continuity: 60%
  Overall: 72% — NEEDS_REFINEMENT

Attempt 2/5:
Refining prompt: Adding visual flow indicators, strengthening concept zones
[■■■■■■■■░░] Generating...

✓ Generated (3.8s)
✓ Evaluating...
  - Concept clarity: 91%
  - Visual appeal: 88%
  - Flow continuity: 85%
  Overall: 88% — PASS ✓

Image 1 complete. Best version: Attempt 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Image 2 of 3: "Quantum Superposition"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

### 4.4 Completion Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generation Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results:
• Images generated: 3 of 3
• Total attempts: 7
• Average quality score: 89%
• Estimated cost: $0.70

Output saved to:
./output/visual-explainer-quantum-entanglement-20260118-143052/

Final images:
1. 01-classical-foundation.jpg (Score: 88%)
2. 02-quantum-superposition.jpg (Score: 91%)
3. 03-entanglement-synthesis.jpg (Score: 88%)

Would you like to:
1. View the summary report
2. Regenerate a specific image
3. Adjust the image sequence
4. Export to different format
```

---

## 5. Configuration Options

### 5.1 User-Configurable Parameters

| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `--max-iterations` | 5 | 1-10 | Max refinement attempts per image |
| `--aspect-ratio` | 16:9 | 16:9, 1:1, 4:3, 9:16, 3:4 | Image aspect ratio |
| `--resolution` | high | low, medium, high | Image quality - high=4K/3200x1800 (default) |
| `--style` | professional-clean | professional-clean, professional-sketch, or path | Visual style (bundled or custom JSON) |
| `--output-dir` | ./output | path | Output directory |
| `--pass-threshold` | 0.85 | 0.0-1.0 | Score required to pass evaluation |
| `--include-text` | false | true, false | Allow text in images |
| `--save-all-attempts` | true | true, false | Keep all attempts or only final |
| `--concurrency` | 3 | 1-10 | Max concurrent image generations |
| `--no-cache` | false | true, false | Force fresh concept analysis |
| `--resume` | null | path | Resume from checkpoint file |
| `--negative-prompt` | (internal) | string | Override default negative prompt (advanced) |

### 5.2 Internal Defaults (Not Exposed to Users)

**Default Negative Prompt** (always applied unless overridden):
```
no text, no words, no letters, no numbers, no watermarks, no logos,
no stock photo aesthetic, no borders, no frames, no signatures,
no artificial lighting artifacts, no lens flare
```

**Concept Cache:**
- Location: `.cache/visual-explainer/concepts-[content-hash].json`
- TTL: Indefinite (invalidated by content change)
- Hash: SHA-256 of document content

**Checkpoint File:**
- Location: `[output-dir]/checkpoint.json`
- Updated: After each image completes
- Contains: Generation state, completed images, current progress

### 5.3 Bundled Style Configurations

The tool ships with comprehensive style JSON files (adapted from slide-generator):

| Style File | Description | Best For |
|------------|-------------|----------|
| `professional-clean.json` | Clean, corporate-ready with warm accents | Business, presentations, reports |
| `professional-sketch.json` | Hand-drawn sketch aesthetic | Creative, educational, informal |

**Style Configuration Schema** (comprehensive JSON structure):

```json
{
  "SchemaVersion": "1.2",
  "StyleName": "Professional_Clean",
  "StyleIntent": "High-level description of the visual intent...",

  "ModelAndOutputProfiles": {
    "TargetModelHint": "nano_banana_pro",
    "ResolutionProfiles": {
      "Landscape4K": { "Width": 3200, "Height": 1800, "AspectRatio": "16:9" }
    }
  },

  "ColorSystem": {
    "PaletteMode": "Strict",
    "Background": { "Base": "#FFFFFF" },
    "PrimaryColors": [
      { "Name": "Brand Red", "Hex": "#DD0031", "Role": "Signature accent" },
      { "Name": "Navy Blue", "Hex": "#004F71", "Role": "Structural color" }
    ],
    "ColorUsageRules": { "ProhibitedHues": ["Neon", "Purple", "Hot pink"] }
  },

  "DesignPrinciples": {
    "CleanlinessIsVirtue": "Crisp, organized, uncluttered layouts",
    "SignatureAccent": "Use brand color intentionally and sparingly"
  },

  "PromptRecipe": {
    "StylePrefix": "Clean, professional presentation graphic...",
    "CoreStylePrompt": "modern professional illustration, clean lines...",
    "ColorConstraintPrompt": "strict color palette: Brand Red as accent...",
    "TextEnforcementPrompt": "Text must be perfectly legible...",
    "NegativePrompt": "cluttered, messy, neon, garish, 3D effects...",
    "QualityChecklist": [
      "Generous white space; layout feels clean",
      "Brand accent used sparingly (not dominant)"
    ]
  }
}
```

**Style Loading Priority:**
1. User-provided `--style path/to/custom.json` (full path)
2. Named style `--style professional-clean` (bundled)
3. Interactive selection during skill flow
4. Default: `professional-clean.json`

**Custom Styles:** Users can create their own style JSON following the schema above. The `PromptRecipe` section is directly injected into image generation prompts.

---

## 6. API Integration Details

### 6.1 Environment Variables

```bash
# .env file (gitignored)
GOOGLE_API_KEY=your-gemini-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key  # For evaluation
```

### 6.2 First-Run API Key Setup

On first run (or if `.env` is missing/invalid), the tool will guide the user through API key setup:

**Detection Logic:**
```python
def check_api_keys() -> dict[str, bool]:
    """Check which API keys are present and valid."""
    results = {}

    # Check Google API key
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key and len(google_key) > 20:
        # Quick validation: attempt a minimal API call
        results["google"] = validate_google_key(google_key)
    else:
        results["google"] = False

    # Check Anthropic API key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and anthropic_key.startswith("sk-ant-"):
        results["anthropic"] = validate_anthropic_key(anthropic_key)
    else:
        results["anthropic"] = False

    return results
```

**Interactive Setup Flow:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API Key Setup Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This tool requires two API keys:
• Google Gemini API - for image generation
• Anthropic API - for image evaluation

Missing keys detected:
❌ GOOGLE_API_KEY - not found
❌ ANTHROPIC_API_KEY - not found

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Google Gemini API Key
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To get your Google Gemini API key:

1. Go to Google AI Studio:
   https://aistudio.google.com/apikey

2. Sign in with your Google account

3. Click "Create API Key"

4. Select or create a Google Cloud project
   (A default project works fine)

5. Copy the generated API key
   (It looks like: AIzaSy...)

Paste your Google API key here (or 'skip' to set up later):
> [user pastes key]

✓ Google API key validated successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Anthropic API Key
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To get your Anthropic API key:

1. Go to the Anthropic Console:
   https://console.anthropic.com/settings/keys

2. Sign in or create an Anthropic account

3. Click "Create Key"

4. Give it a name (e.g., "visual-explainer")

5. Copy the key immediately (it won't be shown again!)
   (It looks like: sk-ant-api03-...)

Note: New accounts get $5 free credits. After that,
you'll need to add a payment method.

Paste your Anthropic API key here (or 'skip' to set up later):
> [user pastes key]

✓ Anthropic API key validated successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Creating .env File
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Creating .env file at: /path/to/project/.env

Contents:
┌─────────────────────────────────────────────┐
│ # Visual Explainer API Keys                 │
│ # Generated: 2026-01-18 14:30:00            │
│                                             │
│ GOOGLE_API_KEY=AIzaSy...                    │
│ ANTHROPIC_API_KEY=sk-ant-api03-...          │
└─────────────────────────────────────────────┘

✓ .env file created successfully!
✓ Added .env to .gitignore (if not already present)

You're all set! Run the tool again to start generating images.
```

**Key Validation:**
```python
async def validate_google_key(key: str) -> bool:
    """Validate Google API key with minimal API call."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": key}
            )
            return response.status_code == 200
    except Exception:
        return False

def validate_anthropic_key(key: str) -> bool:
    """Validate Anthropic API key format and connectivity."""
    try:
        client = anthropic.Anthropic(api_key=key)
        # Minimal API call to verify
        client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}]
        )
        return True
    except anthropic.AuthenticationError:
        return False
    except Exception:
        return True  # Other errors mean key format is valid
```

**Env File Creation:**
```python
def create_env_file(google_key: str | None, anthropic_key: str | None, path: Path) -> None:
    """Create .env file with provided keys."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Visual Explainer API Keys
# Generated: {timestamp}
# Documentation: https://github.com/davistroy/claude-marketplace

"""
    if google_key:
        content += f"GOOGLE_API_KEY={google_key}\n"
    else:
        content += "# GOOGLE_API_KEY=your-google-api-key-here\n"

    if anthropic_key:
        content += f"ANTHROPIC_API_KEY={anthropic_key}\n"
    else:
        content += "# ANTHROPIC_API_KEY=your-anthropic-api-key-here\n"

    path.write_text(content)

    # Ensure .gitignore includes .env
    gitignore = path.parent / ".gitignore"
    if gitignore.exists():
        existing = gitignore.read_text()
        if ".env" not in existing:
            gitignore.write_text(existing.rstrip() + "\n.env\n")
    else:
        gitignore.write_text(".env\n")
```

**Cost Warnings During Setup:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API Cost Information
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimated costs per image generation session:

Google Gemini (image generation):
• ~$0.10 per image generated
• 4K images may cost slightly more
• Free tier: 60 requests/minute

Anthropic Claude (image evaluation):
• ~$0.03 per evaluation
• Multiple evaluations per image if refinement needed
• New accounts: $5 free credits

Example: 3-image document with 2 attempts each
• Gemini: 6 images × $0.10 = $0.60
• Claude: 6 evals × $0.03 = $0.18
• Total: ~$0.78

Press Enter to continue...
```

### 6.3 Gemini API Usage

**From slide-generator patterns:**

```python
import httpx
import base64
from pathlib import Path

class GeminiImageGenerator:
    MODEL_ID = "gemini-3-pro-image-preview"
    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    ASPECT_RATIOS = {
        "16:9": "16:9",
        "1:1": "1:1",
        "4:3": "4:3",
        "9:16": "9:16",
    }

    IMAGE_SIZES = {
        "low": "STANDARD",
        "medium": "STANDARD",
        "high": "LARGE",
    }

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        image_size: str = "high",
        negative_prompt: str | None = None,
    ) -> bytes:
        """Generate image and return raw bytes."""

        endpoint = f"{self.API_BASE}/models/{self.MODEL_ID}:generateContent"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": self.ASPECT_RATIOS[aspect_ratio],
                    "imageSize": self.IMAGE_SIZES[image_size],
                },
            },
        }

        if negative_prompt:
            payload["generationConfig"]["imageConfig"]["negativePrompt"] = negative_prompt

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                endpoint,
                params={"key": self.api_key},
                json=payload,
            )
            response.raise_for_status()

            result = response.json()

            # Extract image bytes
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        image_b64 = part["inlineData"]["data"]
                        return base64.b64decode(image_b64)

            raise ValueError("No image in response")
```

### 6.4 Claude Vision Evaluation

```python
import anthropic
import base64

class ImageEvaluator:
    MODEL = "claude-sonnet-4-20250514"  # Sonnet: sufficient vision, 5x cheaper than Opus

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def evaluate_image(
        self,
        image_bytes: bytes,
        original_intent: str,
        success_criteria: list[str],
        context: dict,
    ) -> dict:
        """Evaluate generated image against intent."""

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        prompt = f"""You are evaluating an AI-generated image for quality and intent alignment.

## Original Intent
{original_intent}

## Success Criteria
{chr(10).join(f'- {c}' for c in success_criteria)}

## Context
- Target audience: {context.get('audience', 'general')}
- Part of sequence: Image {context.get('image_number', 1)} of {context.get('total_images', 1)}
- Visual style: {context.get('style', 'professional')}

## Your Task
Evaluate this image against the criteria above. Provide:

1. **Overall Score** (0.0 to 1.0): How well does this image fulfill the intent?

2. **Criteria Scores**: Score each success criterion (0.0 to 1.0)

3. **Strengths**: What works well?

4. **Weaknesses**: What needs improvement?

5. **Missing Elements**: What's absent that should be present?

6. **Verdict**:
   - PASS (score >= 0.85): Accept this image
   - NEEDS_REFINEMENT (0.5-0.84): Minor adjustments needed
   - FAIL (< 0.5): Major rework required

7. **Refinement Suggestions**: If not PASS, specific prompt changes to improve

Respond in JSON format."""

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }],
        )

        return self._parse_evaluation(response.content[0].text)
```

---

## 7. Error Handling

### 7.1 API Errors

| Error Type | Handling |
|------------|----------|
| Rate limit (429) | Exponential backoff, respect Retry-After header |
| Safety filter | Log, skip to next attempt with modified prompt |
| Timeout | Retry with increased timeout (up to 5 min) |
| Invalid API key | Fail fast with clear error message |
| Network error | Retry up to 3 times with backoff |

### 7.2 Content Errors

| Error Type | Handling |
|------------|----------|
| Empty input | Prompt user for content |
| Unsupported file type | List supported types, offer conversion |
| Content too short | Warn, suggest single image |
| Content too long | Chunk or summarize, warn user |

### 7.3 Generation Errors

| Error Type | Handling |
|------------|----------|
| All attempts exhausted | Select best attempt, report scores |
| No passing images | Present options: accept best, try different approach |
| Partial failure | Complete successful images, report failures |

---

## 8. Cost Estimation

### 8.1 API Costs

| Component | Estimated Cost |
|-----------|----------------|
| Gemini image generation | ~$0.10 per image |
| Claude concept analysis | ~$0.02 per document |
| Claude image evaluation | ~$0.03 per evaluation |

### 8.2 Example Scenarios

| Scenario | Images | Avg Attempts | Est. Total |
|----------|--------|--------------|------------|
| Simple doc, 1 image | 1 | 2 | ~$0.28 |
| Medium doc, 3 images | 3 | 2.3 | ~$0.95 |
| Complex doc, 5 images | 5 | 3 | ~$2.10 |
| Max iterations (5 each) | 3 | 5 | ~$2.00 |

---

## 9. Dependencies

### 9.1 Python Dependencies

```toml
# pyproject.toml
[project]
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.24.0",           # Async HTTP client
    "anthropic>=0.24.0",       # Claude API for evaluation
    "python-dotenv>=1.0.0",    # Environment variable loading
    "python-docx>=0.8.0",      # DOCX reading (optional)
    "PyPDF2>=3.0.0",           # PDF reading (optional)
    "beautifulsoup4>=4.12.0",  # URL content extraction
    "aiofiles>=23.0.0",        # Async file I/O
    "pydantic>=2.0.0",         # Data validation
]
```

### 9.2 External Requirements

- **Google API Key**: Gemini Pro 3 image generation
- **Anthropic API Key**: Claude for analysis and evaluation
- **Internet connection**: API calls

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Concept extraction accuracy
- Prompt generation quality
- Evaluation parsing
- File I/O operations

### 10.2 Integration Tests

- Full pipeline with mock APIs
- Rate limiting behavior
- Error recovery

### 10.3 Manual Testing

- Visual quality assessment
- Flow/narrative coherence
- Style consistency

---

## 11. Future Enhancements

### 11.1 Phase 2 Features

- [ ] Support for image editing/inpainting (refine specific regions)
- [ ] Batch processing of multiple documents
- [ ] Custom style configuration files
- [ ] Export to PowerPoint/presentation format
- [ ] Integration with vector databases for style consistency

### 11.2 Phase 3 Features

- [ ] Video generation from image sequences
- [ ] Interactive diagram generation (SVG)
- [ ] Multi-language support
- [ ] Collaborative editing of prompts

---

## 12. Implementation Checklist

### 12.1 Skill Layer

- [ ] Create `skills/visual-explainer/SKILL.md`
- [ ] Add help entry to `skills/help/SKILL.md`
- [ ] Define frontmatter with name, description, allowed-tools

### 12.2 Tool Layer

- [ ] Create `tools/visual-explainer/` directory structure
- [ ] Copy and adapt style files from `C:\dev\stratfield\slide-generator\styles\`:
  - [ ] `clean-style-sanitized.json` → `styles/professional-clean.json`
  - [ ] `sketch-style-sanitized.json` → `styles/professional-sketch.json`
  - [ ] Create `styles/README.md` documenting the schema
- [ ] Implement `style_loader.py` (load/merge style configs)
- [ ] Implement `api_setup.py` (first-run API key detection, validation, .env creation)
- [ ] Implement `concept_analyzer.py` (document → concepts)
- [ ] Implement `prompt_generator.py` (concepts → prompts, inject style)
- [ ] Implement `image_generator.py` (Gemini API wrapper)
- [ ] Implement `image_evaluator.py` (Claude Vision evaluation)
- [ ] Implement `cli.py` (entry point)
- [ ] Add `pyproject.toml` with dependencies
- [ ] Add `__main__.py` for module execution

### 12.3 Testing

- [ ] Unit tests for each component
- [ ] Integration tests for full pipeline
- [ ] Manual testing with sample documents

### 12.4 Documentation

- [ ] Update plugin `help` skill
- [ ] Add example outputs to README
- [ ] Document API key setup

---

## 13. Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Image generation API | Gemini Pro 3 | Already proven in slide-generator; good quality |
| Evaluation method | Claude Vision | Accurate semantic understanding |
| Evaluation model | Claude Sonnet 4 | Sufficient vision capability; 5x cheaper/faster than Opus |
| Default iterations | 5 | Balance between quality and cost |
| Pass threshold | 0.85 | High quality bar, but achievable |
| Output format | JPEG only | Gemini returns JPEG natively; universal compatibility |
| Async execution | Yes | Required for long-running image generation |
| Parallel generation | Yes, max 3 concurrent | Gemini allows 60 req/min; 3 concurrent balances speed/limits |
| Negative prompts | Internal only | Baked-in smart defaults; `--negative-prompt` flag for power users |
| Style library | Yes, with "professional" default | Ask user; use default if skipped |
| Concept caching | Yes, SHA-256 content hash | Avoid re-analyzing unchanged docs; `--no-cache` to override |
| Resume support | Yes, checkpoint after each image | Handle interruptions gracefully |

---

## Appendix A: Sample Prompt Templates

### A.1 Concept Analysis Prompt

```
You are an expert at analyzing documents and extracting the core concepts.

Analyze the following text and identify:
1. The main concepts/ideas presented
2. How these concepts relate to each other
3. The logical flow from one concept to the next
4. Which concepts are foundational vs. derived

Consider how these concepts could be visualized effectively.

Document:
{document_text}

Respond in JSON format with the structure defined above.
```

### A.2 Image Prompt Generation Template

```
You are an expert visual designer creating prompts for AI image generation.

Based on the following concept(s), create a detailed image generation prompt:

Concept(s):
{concept_descriptions}

Target Audience: {audience}
Visual Style: {style}
Aspect Ratio: {aspect_ratio}
Image Position: {image_number} of {total_images}
Connection to Previous: {previous_connection}
Connection to Next: {next_connection}

Create a prompt that:
1. Clearly visualizes the concept(s)
2. Uses appropriate visual metaphors
3. Maintains the specified style
4. Flows naturally in the sequence
5. Does NOT include any text elements

Respond with:
- main_prompt: The full image generation prompt
- style_guidance: Specific style instructions
- composition: Layout and arrangement guidance
- avoid: What to exclude from the image
- success_criteria: How to evaluate if the image succeeds
```

---

*Document Version: 1.0*
*Created: 2026-01-18*
*Status: DRAFT - Awaiting Review*
