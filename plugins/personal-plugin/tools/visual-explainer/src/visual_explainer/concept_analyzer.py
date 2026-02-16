"""Concept Analyzer for Visual Explainer.

This module analyzes input documents using Claude to extract structured
concepts and their relationships. It supports:

- Multiple input types: raw text, file paths (.md, .txt, .docx, .pdf), URLs
- SHA-256 content hashing for cache invalidation
- JSON cache storage at .cache/visual-explainer/concepts-[hash].json
- Optional dependencies for DOCX and PDF support

Usage:
    from visual_explainer.concept_analyzer import analyze_document
    from visual_explainer.config import GenerationConfig

    config = GenerationConfig.from_cli_and_env("Your text here...")
    analysis = await analyze_document("Your text here...", config)
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from .config import GenerationConfig, InternalConfig
from .models import (
    Complexity,
    Concept,
    ConceptAnalysis,
    ContentType,
    LogicalFlowStep,
    PagePlan,
    PageRecommendation,
    PageType,
    RelationshipType,
    VisualPotential,
)

# Optional dependencies for document reading
try:
    from docx import Document as DocxDocument

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from PyPDF2 import PdfReader

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# URL fetching dependencies
try:
    import httpx
    from bs4 import BeautifulSoup

    URL_AVAILABLE = True
except ImportError:
    URL_AVAILABLE = False


# Analysis prompt template for infographic page planning
ANALYSIS_PROMPT_TEMPLATE = """You are an expert at analyzing documents for conversion into information-dense infographic pages.

Your goal is to extract concepts AND plan how to present them across 1-6 infographic pages (11x17 inches, 4K resolution) that can hold substantial information including text, diagrams, tables, and data visualizations.

## Document

{document_text}

## Your Task

Analyze this document and provide a comprehensive plan for infographic pages.

### Content Types to Identify

Detect which content types are present:
- **statistics**: Quantitative data, percentages, metrics, specific numbers
- **process**: Sequential steps, workflows, procedures, methodologies
- **comparison**: Side-by-side analysis, alternatives, trade-offs, vendor comparisons
- **hierarchy**: Org structures, taxonomies, nested relationships, failure trees
- **timeline**: Chronological sequences, milestones, phases, evolution
- **framework**: Conceptual models, matrices, named methodologies
- **narrative**: Explanatory text, context, stories
- **list**: Parallel items, bullet points, enumerated content
- **matrix**: Multi-dimensional comparisons, grids, decision tables

### Page Types Available

- **hero_summary**: Executive overview - the "one page" view with core thesis, key stats, framework preview
- **problem_landscape**: Why this matters, failure modes, risks, current state analysis
- **framework_overview**: High-level process or methodology visualization
- **framework_deep_dive**: Detailed breakdown of specific stages with activities
- **comparison_matrix**: Side-by-side vendor/option analysis
- **dimensions_variations**: How framework adapts to different contexts/scales
- **reference_action**: Checklists, decision trees, quick reference
- **data_evidence**: Charts, statistics, research findings

### Page Count Guidelines

Determine page count based on:
- Word count: <1000 = 1 page, 1000-2500 = 2-3 pages, 2500-5000 = 3-4 pages, 5000+ = 4-6 pages
- Content type diversity: +1 page if 3+ distinct content types
- Nested frameworks: +1 page if framework has 4+ stages needing deep-dive
- Operational content: +1 page if requires checklists/decision trees
- Comparison data: +1 page if 3+ options need comparison matrix

### Response Format

```json
{{
  "title": "Document Title",
  "summary": "One-paragraph summary",
  "target_audience": "Who this is for",
  "concepts": [
    {{
      "id": 1,
      "name": "Concept Name",
      "description": "What this concept means",
      "relationships": ["concept_id:2"],
      "complexity": "simple|moderate|complex",
      "visual_potential": "high|medium|low"
    }}
  ],
  "logical_flow": [
    {{"from": 1, "to": 2, "relationship": "leads_to|supports|contrasts|builds_on|depends_on|contains"}}
  ],
  "content_types_detected": ["statistics", "process", "comparison"],
  "page_recommendation": {{
    "page_count": 3,
    "rationale": "Why this page count is appropriate for the content",
    "pages": [
      {{
        "page_number": 1,
        "page_type": "hero_summary",
        "title": "Page Title",
        "content_focus": "What this page communicates",
        "concepts_covered": [1, 2, 3],
        "content_types_present": ["statistics", "framework"],
        "zone_assignments": {{
          "hero_stat": "The key statistic to feature prominently",
          "main_framework": "Description of the main diagram/framework to show",
          "detail_cards": "What goes in the detail cards section"
        }},
        "cross_references": ["See page 2 for details"]
      }}
    ],
    "compression_warnings": ["Complex topic X may need more depth than one page allows"]
  }},
  "recommended_image_count": 3,
  "reasoning": "Explanation of page/image count"
}}
```

### Important Guidelines

1. Each page should be meaningful standalone but also connect to the sequence
2. Hero summary page (page 1) should give the "executive overview" - if someone only sees one page
3. Assign content to zones based on the zone's content_guidance requirements
4. Include specific content descriptions for zone_assignments, not just "the main content"
5. Flag compression_warnings if important content might be over-compressed
6. Process frameworks with 4+ stages need separate deep-dive pages
7. Comparison matrices with 3+ vendors need dedicated comparison page
8. Operational documents (meant to be used) need reference_action page

Respond with ONLY valid JSON, no markdown code fences or additional text."""


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for cache key.

    Args:
        content: The text content to hash.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_cache_path(content_hash: str, cache_dir: Path) -> Path:
    """Get the cache file path for a content hash.

    Args:
        content_hash: SHA-256 hash of the content.
        cache_dir: Directory for cache files.

    Returns:
        Path to the cache file.
    """
    return cache_dir / f"concepts-{content_hash[:16]}.json"


def load_from_cache(
    content_hash: str,
    cache_dir: Path,
) -> ConceptAnalysis | None:
    """Load cached concept analysis if it exists and matches.

    Args:
        content_hash: SHA-256 hash of the content.
        cache_dir: Directory for cache files.

    Returns:
        ConceptAnalysis if cache hit, None otherwise.
    """
    cache_path = get_cache_path(content_hash, cache_dir)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)

        # Verify hash matches
        if data.get("content_hash") != content_hash:
            return None

        # Handle both cache formats: original API response and model_dump output
        # model_dump uses 'from_concept' and 'to_concept', API uses 'from' and 'to'
        if "logical_flow" in data:
            for flow in data["logical_flow"]:
                if "from_concept" in flow and "from" not in flow:
                    flow["from"] = flow["from_concept"]
                if "to_concept" in flow and "to" not in flow:
                    flow["to"] = flow["to_concept"]

        return _parse_analysis_json(data)
    except (json.JSONDecodeError, KeyError, ValueError):
        # Invalid cache file
        return None


def save_to_cache(
    analysis: ConceptAnalysis,
    content_hash: str,
    cache_dir: Path,
) -> Path:
    """Save concept analysis to cache.

    Args:
        analysis: The analysis to cache.
        content_hash: SHA-256 hash of the content.
        cache_dir: Directory for cache files.

    Returns:
        Path to the cache file.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = get_cache_path(content_hash, cache_dir)

    # Use Pydantic v2's model_dump with mode='json' for serialization
    data = analysis.model_dump(mode="json")
    data["content_hash"] = content_hash
    data["cached_at"] = datetime.now().isoformat()

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return cache_path


def detect_input_type(input_source: str) -> tuple[str, str | None]:
    """Detect the type of input and return normalized type and path.

    Args:
        input_source: Raw text, file path, or URL.

    Returns:
        Tuple of (input_type, path_or_url).
        input_type is one of: "text", "file", "url"
        path_or_url is the file path or URL if applicable, None for raw text.
    """
    # Check if it looks like a URL
    if input_source.startswith(("http://", "https://", "www.")):
        url = input_source
        if url.startswith("www."):
            url = "https://" + url
        return "url", url

    # Check if it's a file path that exists
    potential_path = Path(input_source)
    if potential_path.exists() and potential_path.is_file():
        return "file", str(potential_path.resolve())

    # Check if it looks like a file path even if it doesn't exist
    # (has file extension and reasonable path structure)
    if len(input_source) < 500 and (
        "/" in input_source
        or "\\" in input_source
        or input_source.endswith((".md", ".txt", ".docx", ".pdf"))
    ):
        # Likely intended as a file path but doesn't exist
        return "file", input_source

    # Default to raw text
    return "text", None


def read_text_file(path: Path) -> str:
    """Read plain text file (.txt, .md).

    Args:
        path: Path to the text file.

    Returns:
        File contents as string.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file can't be read.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            return path.read_text(encoding="latin-1")
        except Exception as e:
            raise ValueError(f"Could not read file {path}: {e}") from e


def read_docx_file(path: Path) -> str:
    """Read DOCX file content.

    Args:
        path: Path to the DOCX file.

    Returns:
        Extracted text content.

    Raises:
        ImportError: If python-docx is not installed.
        FileNotFoundError: If file doesn't exist.
        ValueError: If file can't be read.
    """
    if not DOCX_AVAILABLE:
        raise ImportError(
            "DOCX support requires python-docx. Install with: pip install python-docx"
        )

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        doc = DocxDocument(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"Could not read DOCX file {path}: {e}") from e


def read_pdf_file(path: Path) -> str:
    """Read PDF file content.

    Args:
        path: Path to the PDF file.

    Returns:
        Extracted text content.

    Raises:
        ImportError: If PyPDF2 is not installed.
        FileNotFoundError: If file doesn't exist.
        ValueError: If file can't be read.
    """
    if not PDF_AVAILABLE:
        raise ImportError("PDF support requires PyPDF2. Install with: pip install PyPDF2")

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        reader = PdfReader(str(path))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Could not read PDF file {path}: {e}") from e


async def fetch_url_content(url: str, timeout: float = 30.0) -> str:
    """Fetch and extract text content from a URL.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Extracted text content.

    Raises:
        ImportError: If httpx or beautifulsoup4 is not installed.
        ValueError: If URL can't be fetched or parsed.
    """
    if not URL_AVAILABLE:
        raise ImportError(
            "URL fetching requires httpx and beautifulsoup4. "
            "Install with: pip install httpx beautifulsoup4"
        )

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; VisualExplainer/1.0)",
                },
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                raise ValueError(f"Unsupported content type: {content_type}")

            html = response.text
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP error fetching URL: {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise ValueError(f"Error fetching URL: {e}") from e

    # Parse HTML and extract text
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, and nav elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
        element.decompose()

    # Try to find main content
    main_content = soup.find("main") or soup.find("article") or soup.find("body")
    if main_content is None:
        main_content = soup

    # Extract text
    text = main_content.get_text(separator="\n", strip=True)

    # Clean up whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n\n".join(lines)


async def read_input(input_source: str) -> tuple[str, str, str | None]:
    """Read content from input source (text, file, or URL).

    Args:
        input_source: Raw text, file path, or URL.

    Returns:
        Tuple of (content, input_type, path_or_url).

    Raises:
        ValueError: If input can't be read.
        FileNotFoundError: If file path doesn't exist.
        ImportError: If required dependency is missing.
    """
    input_type, path_or_url = detect_input_type(input_source)

    if input_type == "text":
        return input_source, "text", None

    if input_type == "url":
        content = await fetch_url_content(path_or_url)
        return content, "url", path_or_url

    # File type
    path = Path(path_or_url)
    suffix = path.suffix.lower()

    if suffix in (".txt", ".md"):
        content = read_text_file(path)
    elif suffix == ".docx":
        content = read_docx_file(path)
    elif suffix == ".pdf":
        content = read_pdf_file(path)
    else:
        # Try reading as text
        try:
            content = read_text_file(path)
        except Exception as e:
            raise ValueError(
                f"Unsupported file type: {suffix}. Supported types: .md, .txt, .docx, .pdf"
            ) from e

    return content, "file", path_or_url


def _parse_complexity(value: str) -> Complexity:
    """Parse complexity string to enum."""
    value = value.lower().strip()
    try:
        return Complexity(value)
    except ValueError:
        return Complexity.MODERATE


def _parse_visual_potential(value: str) -> VisualPotential:
    """Parse visual potential string to enum."""
    value = value.lower().strip()
    try:
        return VisualPotential(value)
    except ValueError:
        return VisualPotential.MEDIUM


def _parse_relationship_type(value: str) -> RelationshipType:
    """Parse relationship type string to enum."""
    value = value.lower().strip()
    try:
        return RelationshipType(value)
    except ValueError:
        return RelationshipType.LEADS_TO


def _parse_content_type(value: str) -> ContentType | None:
    """Parse content type string to enum."""
    value = value.lower().strip()
    try:
        return ContentType(value)
    except ValueError:
        return None


def _parse_page_type(value: str) -> PageType:
    """Parse page type string to enum."""
    value = value.lower().strip()
    try:
        return PageType(value)
    except ValueError:
        return PageType.HERO_SUMMARY


def _parse_content_types_list(values: list[str]) -> list[ContentType]:
    """Parse a list of content type strings to enums."""
    result = []
    for v in values:
        ct = _parse_content_type(v)
        if ct is not None:
            result.append(ct)
    return result


def _parse_page_plan(data: dict[str, Any]) -> PagePlan:
    """Parse page plan data into PagePlan model."""
    return PagePlan(
        page_number=max(1, data.get("page_number", 1)),
        page_type=_parse_page_type(data.get("page_type", "hero_summary")),
        title=data.get("title", "Untitled Page") or "Untitled Page",
        content_focus=data.get("content_focus", "") or "",
        concepts_covered=data.get("concepts_covered", []),
        content_types_present=_parse_content_types_list(data.get("content_types_present", [])),
        zone_assignments=data.get("zone_assignments", {}),
        cross_references=data.get("cross_references", []),
    )


def _parse_page_recommendation(data: dict[str, Any] | None) -> PageRecommendation | None:
    """Parse page recommendation data into PageRecommendation model."""
    if data is None:
        return None

    pages = []
    for page_data in data.get("pages", []):
        pages.append(_parse_page_plan(page_data))

    # Ensure at least one page if page_count > 0
    page_count = max(1, min(6, data.get("page_count", 1)))
    if not pages:
        # Create a default hero page
        pages = [
            PagePlan(
                page_number=1,
                page_type=PageType.HERO_SUMMARY,
                title="Document Overview",
                content_focus="Executive summary of the document",
                concepts_covered=[],
                content_types_present=[],
                zone_assignments={},
                cross_references=[],
            )
        ]

    return PageRecommendation(
        page_count=page_count,
        rationale=data.get("rationale", "") or "",
        pages=pages,
        compression_warnings=data.get("compression_warnings", []),
    )


def _parse_analysis_json(data: dict[str, Any]) -> ConceptAnalysis:
    """Parse raw JSON data into ConceptAnalysis model.

    Args:
        data: Raw JSON data from Claude response or cache.

    Returns:
        Validated ConceptAnalysis model.

    Raises:
        ValueError: If data is invalid.
    """
    # Parse concepts
    concepts = []
    for c in data.get("concepts", []):
        concept_id = c.get("id", len(concepts) + 1)
        # Ensure concept ID is at least 1 (model constraint)
        if concept_id < 1:
            concept_id = len(concepts) + 1

        concepts.append(
            Concept(
                id=concept_id,
                name=c.get("name", "Unnamed Concept") or "Unnamed Concept",
                description=c.get("description", "No description provided")
                or "No description provided",
                relationships=c.get("relationships", []),
                complexity=_parse_complexity(c.get("complexity", "moderate")),
                visual_potential=_parse_visual_potential(c.get("visual_potential", "medium")),
            )
        )

    # Ensure at least one concept exists (model constraint)
    if not concepts:
        concepts = [
            Concept(
                id=1,
                name="Main Concept",
                description="The primary concept from the analyzed content",
                complexity=Complexity.MODERATE,
                visual_potential=VisualPotential.MEDIUM,
            )
        ]

    # Parse logical flow
    logical_flow = []
    for f in data.get("logical_flow", []):
        from_id = f.get("from", 1)
        to_id = f.get("to", 1)
        # Ensure IDs are at least 1 (model constraint)
        if from_id < 1:
            from_id = 1
        if to_id < 1:
            to_id = 1
        logical_flow.append(
            LogicalFlowStep(
                from_concept=from_id,
                to_concept=to_id,
                relationship=_parse_relationship_type(f.get("relationship", "leads_to")),
            )
        )

    # Ensure title and summary have content (model constraint)
    title = data.get("title", "").strip() or "Untitled Document"
    summary = data.get("summary", "").strip() or "Content analysis summary not available."

    # Parse content types detected
    content_types_detected = _parse_content_types_list(data.get("content_types_detected", []))

    # Parse page recommendation
    page_recommendation = _parse_page_recommendation(data.get("page_recommendation"))

    # If no page recommendation, use recommended_image_count for backward compatibility
    recommended_count = data.get("recommended_image_count", 1)
    if page_recommendation is None and recommended_count > 0:
        # Keep legacy behavior
        pass
    elif page_recommendation is not None:
        # Use page count from recommendation
        recommended_count = page_recommendation.page_count

    return ConceptAnalysis(
        title=title,
        summary=summary,
        target_audience=data.get("target_audience", "General audience") or "General audience",
        concepts=concepts,
        logical_flow=logical_flow,
        content_types_detected=content_types_detected,
        recommended_image_count=max(1, min(20, recommended_count)),
        reasoning=data.get("reasoning", ""),
        page_recommendation=page_recommendation,
        content_hash=data.get("content_hash", ""),
        word_count=max(0, data.get("word_count", 0)),
    )


def _extract_json_from_response(text: str) -> dict[str, Any]:
    """Extract JSON object from Claude response text.

    Handles responses that may include markdown code fences or
    additional text around the JSON.

    Args:
        text: Raw response text from Claude.

    Returns:
        Parsed JSON object.

    Raises:
        ValueError: If no valid JSON found.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code fence
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in text
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from response")


async def call_claude_for_analysis(
    content: str,
    internal_config: InternalConfig,
    infographic_mode: bool = True,
) -> dict[str, Any]:
    """Call Claude API to analyze content and extract concepts.

    Args:
        content: The document text to analyze.
        internal_config: Internal configuration with model settings.
        infographic_mode: If True, use infographic-focused analysis (default).

    Returns:
        Parsed JSON response from Claude.

    Raises:
        ValueError: If Claude returns invalid response.
        anthropic.APIError: If API call fails.
    """
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Run with --setup-keys to configure.")

    client = anthropic.Anthropic(api_key=api_key)

    # Truncate very long documents to avoid context limits
    max_content_length = 100000  # ~25k tokens
    if len(content) > max_content_length:
        content = content[:max_content_length] + "\n\n[Content truncated...]"

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(document_text=content)

    response = client.messages.create(
        model=internal_config.claude_model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text
    return _extract_json_from_response(response_text)


async def analyze_document(
    input_source: str,
    config: GenerationConfig,
    internal_config: InternalConfig | None = None,
    infographic_mode: bool = True,
) -> ConceptAnalysis:
    """Analyze a document and extract concepts for visual explanation.

    This is the main entry point for concept analysis. It:
    1. Detects input type (text, file, URL)
    2. Reads content from the source
    3. Computes content hash for caching
    4. Checks cache (unless --no-cache)
    5. Calls Claude for analysis if cache miss
    6. Saves result to cache
    7. Returns validated ConceptAnalysis

    Args:
        input_source: Raw text, file path, or URL to analyze.
        config: User configuration (includes no_cache flag).
        internal_config: Internal config (defaults loaded if None).
        infographic_mode: If True, analyze for infographic page layout (default).

    Returns:
        ConceptAnalysis with extracted concepts and flow.
        When infographic_mode=True, includes page_recommendation.

    Raises:
        ValueError: If input is invalid or analysis fails.
        FileNotFoundError: If file path doesn't exist.
        ImportError: If required dependency is missing.
    """
    if internal_config is None:
        internal_config = InternalConfig.from_env()

    # Read input content
    content, input_type, path_or_url = await read_input(input_source)

    if not content.strip():
        raise ValueError("Input content is empty")

    # Compute hash and word count
    content_hash = compute_content_hash(content)
    word_count = len(content.split())

    # Check cache unless disabled
    if not config.no_cache:
        cached = load_from_cache(content_hash, internal_config.cache_dir)
        if cached is not None:
            # Update hash and word count in case they weren't stored
            cached.content_hash = content_hash
            cached.word_count = word_count
            return cached

    # Call Claude for analysis
    raw_analysis = await call_claude_for_analysis(content, internal_config, infographic_mode)

    # Add metadata
    raw_analysis["content_hash"] = content_hash
    raw_analysis["word_count"] = word_count

    # Parse into model
    analysis = _parse_analysis_json(raw_analysis)

    # Save to cache
    save_to_cache(analysis, content_hash, internal_config.cache_dir)

    return analysis


# Synchronous wrapper for non-async contexts
def analyze_document_sync(
    input_source: str,
    config: GenerationConfig,
    internal_config: InternalConfig | None = None,
    infographic_mode: bool = True,
) -> ConceptAnalysis:
    """Synchronous wrapper for analyze_document.

    Args:
        input_source: Raw text, file path, or URL to analyze.
        config: User configuration.
        internal_config: Internal config (defaults loaded if None).
        infographic_mode: If True, analyze for infographic page layout (default).

    Returns:
        ConceptAnalysis with extracted concepts and flow.
    """
    import asyncio

    return asyncio.run(analyze_document(input_source, config, internal_config, infographic_mode))
