"""Infographic prompt building for Visual Concept Explainer.

This module builds detailed infographic-style prompts using a zone-based
layout system. Each page is divided into content zones with specific
typography, content types, and layout guidance.

Key features:
1. Zone-based composition with explicit text placement guidance
2. Typography specifications for headline/subhead/body/caption
3. Cross-page narrative flow and visual consistency
4. Adaptive page layouts based on content type

Design philosophy:
- 11x17 inch 4K infographics can hold 800-2000 words of readable text
- Each page should convey substantial information, not just simple visuals
- Zone-based layouts ensure consistent, professional composition
- Text specifications are explicit (font sizes, placement, content)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .config import GenerationConfig, InternalConfig
from .models import (
    ConceptAnalysis,
    FlowConnection,
    ImagePrompt,
    PagePlan,
    PromptDetails,
)
from .page_templates import get_zone_prompt_guidance

logger = logging.getLogger(__name__)


class InfographicPromptBuilder:
    """Builds detailed infographic-style prompts from page plans.

    This class handles the conversion of page plans and concept analysis
    into detailed zone-based infographic prompts that can be used for
    image generation.

    Attributes:
        internal_config: Internal configuration with defaults.

    Example:
        >>> builder = InfographicPromptBuilder()
        >>> prompt_text = builder.build_infographic_page_prompt(
        ...     analysis=analysis,
        ...     page_plan=page_plan,
        ...     layout=layout,
        ...     style_injection=style_injection,
        ...     total_pages=3,
        ... )
    """

    def __init__(
        self,
        internal_config: InternalConfig | None = None,
    ) -> None:
        """Initialize the infographic prompt builder.

        Args:
            internal_config: Internal configuration. If None, uses defaults.
        """
        self.internal_config = internal_config or InternalConfig.from_env()

    def build_infographic_page_prompt(
        self,
        analysis: ConceptAnalysis,
        page_plan: PagePlan,
        layout: Any,  # PageLayout
        style_injection: dict[str, str],
        total_pages: int,
        config: GenerationConfig | None = None,
    ) -> str:
        """Build prompt for a single infographic page.

        Creates a detailed prompt that specifies:
        - Zone-by-zone content requirements
        - Typography and text specifications
        - Visual elements and their placement
        - Specific text content to include
        - Cross-page consistency requirements

        Args:
            analysis: Full concept analysis for context.
            page_plan: Plan for this specific page.
            layout: PageLayout template for this page type.
            style_injection: Formatted style components.
            total_pages: Total number of pages in sequence.
            config: Optional generation configuration.

        Returns:
            Formatted prompt string for Claude.
        """
        # Get concepts covered by this page
        covered_concepts = [c for c in analysis.concepts if c.id in page_plan.concepts_covered]
        concepts_text = self._format_concepts_detail(covered_concepts)

        # Build zone specifications
        zone_specs = self._build_zone_specifications(
            layout=layout,
            page_plan=page_plan,
            analysis=analysis,
        )

        # Get aspect ratio
        aspect_ratio = config.aspect_ratio.value if config else "16:9"

        prompt = f"""You are an expert infographic designer creating a detailed image generation prompt.

## Document Context

**Title:** {analysis.title}
**Summary:** {analysis.summary}
**Target Audience:** {analysis.target_audience}

## Page Specification

**Page:** {page_plan.page_number} of {total_pages}
**Page Type:** {page_plan.page_type.value}
**Page Title:** {page_plan.title}
**Content Focus:** {page_plan.content_focus}

## Concepts to Visualize on This Page

{concepts_text}

## Page Layout Template

**Layout Type:** {layout.page_type.value}
**Description:** {layout.description}

### Zone-by-Zone Specifications

{zone_specs}

### Design Notes
{layout.design_notes}

## Style Requirements

**Core Style:** {style_injection.get("core_style", "professional, clean, modern infographic")}
**Color Palette:** {style_injection.get("color_constraints", "professional business colors")}
**Style Prefix:** {style_injection.get("style_prefix", "")}

## Critical Design Requirements

1. **INFORMATION DENSITY**: This is an 11x17 inch infographic at 4K resolution (5100x3300 pixels).
   - Can display 800-2000 words of readable text
   - Include specific, detailed text content in each zone
   - Every zone should carry meaningful information

2. **TYPOGRAPHY SPECIFICATIONS**:
   - Headline text: 48-72pt equivalent (zone: page_header, hero elements)
   - Subhead text: 24-36pt equivalent (zone headers, section titles)
   - Body text: 14-18pt equivalent (descriptions, explanations)
   - Caption text: 10-12pt equivalent (annotations, source notes)

3. **TEXT CONTENT**: For each zone, specify the ACTUAL text to be displayed:
   - Headers and titles with specific wording
   - Bullet points with complete text
   - Data labels and annotations
   - Callout text and explanations

4. **VISUAL HIERARCHY**: Ensure clear reading flow:
   - Primary: Hero stats/key insights (largest, most prominent)
   - Secondary: Framework elements and supporting data
   - Tertiary: Detail text and annotations

5. **CROSS-PAGE CONSISTENCY** (Page {page_plan.page_number} of {total_pages}):
   - Maintain consistent header style across pages
   - Use consistent iconography and visual language
   - Page number and navigation indicators
{self._get_cross_references_text(page_plan)}

## Output Format

Create a detailed image generation prompt with these components:

```json
{{
  "page_title": "Exact title text for page header",
  "main_prompt": "Comprehensive prompt describing the entire infographic layout, visual elements, and text specifications...",
  "zone_content": {{
    "zone_name": {{
      "text_content": ["Exact text line 1", "Exact text line 2", "..."],
      "visual_elements": "Description of icons, charts, or graphics",
      "layout_notes": "Specific placement guidance"
    }}
  }},
  "typography_spec": {{
    "headline_text": ["List of headline-sized text items"],
    "subhead_text": ["List of subhead-sized text items"],
    "body_text": ["List of body-sized text blocks"],
    "caption_text": ["List of caption-sized annotations"]
  }},
  "style_guidance": "Specific style instructions for this page",
  "color_palette": "Color specifications with hex codes if possible",
  "composition": "Overall layout and visual hierarchy description",
  "avoid": "Elements that should NOT appear",
  "success_criteria": [
    "Specific, measurable criteria for this infographic page"
  ]
}}
```

## Aspect Ratio
Design for {aspect_ratio} aspect ratio (landscape orientation for 11x17 printing).

Generate a prompt that will create an information-rich infographic page that could be printed at 11x17 inches and read like a detailed visual document.

Respond with ONLY the JSON object, no additional text."""

        return prompt

    def parse_infographic_response(self, response_text: str) -> dict[str, Any]:
        """Parse Claude's infographic prompt response.

        Args:
            response_text: Raw response text from Claude.

        Returns:
            Parsed prompt data dictionary.

        Raises:
            json.JSONDecodeError: If parsing fails.
        """
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find JSON object directly
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text.strip()

        return json.loads(json_str)

    def build_infographic_image_prompt(
        self,
        prompt_data: dict[str, Any],
        page_plan: PagePlan,
        layout: Any,  # PageLayout
        total_pages: int,
        style_injection: dict[str, str],
        config: GenerationConfig | None = None,
    ) -> ImagePrompt:
        """Build an ImagePrompt from infographic response data.

        Args:
            prompt_data: Parsed response data.
            page_plan: Plan for this page.
            layout: PageLayout template.
            total_pages: Total number of pages.
            style_injection: Style components.
            config: Optional generation configuration.

        Returns:
            Validated ImagePrompt instance.
        """
        # Build main prompt with zone content embedded
        main_prompt = prompt_data.get("main_prompt", "")

        # Add typography specifications to prompt if available
        typography_spec = prompt_data.get("typography_spec", {})
        if typography_spec:
            typography_text = self._format_typography_for_prompt(typography_spec)
            main_prompt = f"{main_prompt}\n\n{typography_text}"

        # Add style prefix if not already present
        if (
            style_injection.get("style_prefix")
            and style_injection["style_prefix"] not in main_prompt
        ):
            main_prompt = f"{style_injection['style_prefix']}. {main_prompt}"

        # Combine avoid/negative prompts
        avoid = prompt_data.get("avoid", "")
        style_negative = style_injection.get("negative", "")
        default_negative = self.internal_config.negative_prompt
        combined_avoid = self._combine_negative_prompts(avoid, style_negative, default_negative)

        # Build PromptDetails
        prompt_details = PromptDetails(
            main_prompt=main_prompt,
            style_guidance=prompt_data.get("style_guidance", style_injection.get("core_style", "")),
            color_palette=prompt_data.get(
                "color_palette", style_injection.get("color_constraints", "")
            ),
            composition=prompt_data.get("composition", layout.description),
            avoid=combined_avoid,
        )

        # Build flow connection
        flow_connection = FlowConnection(
            previous=page_plan.page_number - 1 if page_plan.page_number > 1 else None,
            next_image=page_plan.page_number + 1 if page_plan.page_number < total_pages else None,
            transition_intent=f"Continues to page {page_plan.page_number + 1}"
            if page_plan.page_number < total_pages
            else "Final page",
        )

        # Get success criteria
        success_criteria = prompt_data.get("success_criteria", [])
        if not success_criteria:
            success_criteria = self._generate_infographic_criteria(page_plan, layout)

        return ImagePrompt(
            image_number=page_plan.page_number,
            image_title=prompt_data.get("page_title", page_plan.title),
            concepts_covered=page_plan.concepts_covered,
            visual_intent=page_plan.content_focus,
            prompt=prompt_details,
            success_criteria=success_criteria,
            flow_connection=flow_connection,
        )

    def _format_concepts_detail(self, concepts: list) -> str:
        """Format concepts with full detail for infographic generation.

        Args:
            concepts: List of Concept objects to format.

        Returns:
            Detailed formatted concept descriptions.
        """
        if not concepts:
            return "No specific concepts for this page."

        lines = []
        for concept in concepts:
            lines.append(
                f"### Concept {concept.id}: {concept.name}\n"
                f"**Description:** {concept.description}\n"
                f"**Key Points:**\n"
            )
            # Extract key points from description if available
            if hasattr(concept, "key_points") and concept.key_points:
                for point in concept.key_points:
                    lines.append(f"  - {point}")
            lines.append(
                f"\n**Visual Potential:** {concept.visual_potential.value}\n"
                f"**Complexity:** {concept.complexity.value}"
            )
        return "\n\n".join(lines)

    def _build_zone_specifications(
        self,
        layout: Any,  # PageLayout
        page_plan: PagePlan,
        analysis: ConceptAnalysis,
    ) -> str:
        """Build detailed zone specifications for the prompt.

        Args:
            layout: PageLayout template.
            page_plan: Plan for this page.
            analysis: Full analysis for context.

        Returns:
            Formatted zone specifications.
        """
        lines = []
        for zone in layout.zones:
            get_zone_prompt_guidance(zone)

            # Get zone assignment if available
            assigned_content = page_plan.zone_assignments.get(zone.name, "")

            lines.append(f"""
#### Zone: {zone.name}
- **Position:** {zone.position}
- **Size:** {zone.width_percent}% width x {zone.height_percent}% height
- **Content Type:** {zone.content_type.value}
- **Typography Scale:** {zone.typography_scale}
- **Guidance:** {zone.content_guidance}
{f"- **Assigned Content:** {assigned_content}" if assigned_content else ""}
""")
        return "\n".join(lines)

    def _get_cross_references_text(self, page_plan: PagePlan) -> str:
        """Generate cross-reference text for page plan.

        Args:
            page_plan: Plan for this page.

        Returns:
            Formatted cross-reference instructions.
        """
        if not page_plan.cross_references:
            return ""

        refs = "\n".join(f"   - {ref}" for ref in page_plan.cross_references)
        return f"\n   **Cross-references to other pages:**\n{refs}"

    def _format_typography_for_prompt(self, typography_spec: dict[str, list[str]]) -> str:
        """Format typography specifications for inclusion in prompt.

        Args:
            typography_spec: Dictionary of typography levels to text items.

        Returns:
            Formatted typography instructions.
        """
        lines = ["TEXT CONTENT SPECIFICATIONS:"]

        if typography_spec.get("headline_text"):
            lines.append("\nHEADLINE TEXT (48-72pt):")
            for text in typography_spec["headline_text"]:
                lines.append(f'  "{text}"')

        if typography_spec.get("subhead_text"):
            lines.append("\nSUBHEAD TEXT (24-36pt):")
            for text in typography_spec["subhead_text"]:
                lines.append(f'  "{text}"')

        if typography_spec.get("body_text"):
            lines.append("\nBODY TEXT (14-18pt):")
            for text in typography_spec["body_text"]:
                lines.append(f'  "{text}"')

        if typography_spec.get("caption_text"):
            lines.append("\nCAPTION TEXT (10-12pt):")
            for text in typography_spec["caption_text"]:
                lines.append(f'  "{text}"')

        return "\n".join(lines)

    def _generate_infographic_criteria(
        self,
        page_plan: PagePlan,
        layout: Any,  # PageLayout
    ) -> list[str]:
        """Generate default success criteria for infographic pages.

        Args:
            page_plan: Plan for this page.
            layout: PageLayout template.

        Returns:
            List of success criteria.
        """
        criteria = [
            f"Page clearly presents: {page_plan.content_focus}",
            f"All {len(layout.zones)} content zones are populated with readable text",
            "Typography hierarchy is clear (headlines > subheads > body > captions)",
            "Information density appropriate for 11x17 inch print at 300 DPI",
            f"Visual style consistent with {page_plan.page_type.value} page type",
        ]

        if page_plan.page_number > 1:
            criteria.append("Visual consistency with previous pages maintained")

        return criteria

    def _combine_negative_prompts(self, *prompts: str) -> str:
        """Combine multiple negative prompts, deduplicating entries.

        Args:
            *prompts: Variable number of negative prompt strings.

        Returns:
            Combined negative prompt string.
        """
        # Split each prompt by comma and collect unique entries
        seen = set()
        entries = []

        for prompt in prompts:
            if not prompt:
                continue
            for entry in prompt.split(","):
                entry = entry.strip().lower()
                if entry and entry not in seen:
                    seen.add(entry)
                    entries.append(entry.strip())

        return ", ".join(entries)
