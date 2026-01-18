"""Prompt generation and refinement for Visual Concept Explainer.

This module generates infographic-style image prompts from concept analysis.
It implements a zone-based layout system where each page is divided into
content zones with specific typography, content types, and layout guidance.

Key features:
1. generate_infographic_prompts(): Creates information-dense page prompts
2. Zone-based composition with explicit text placement guidance
3. Adaptive page count based on content complexity
4. Cross-page narrative flow and visual consistency

Design philosophy:
- 11×17 inch 4K infographics can hold 800-2000 words of readable text
- Each page should convey substantial information, not just simple visuals
- Zone-based layouts ensure consistent, professional composition
- Text specifications are explicit (font sizes, placement, content)

Uses anthropic SDK for Claude API calls.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from .config import GenerationConfig, InternalConfig, StyleConfig
from .models import (
    ConceptAnalysis,
    ContentType,
    ContentZone,
    EvaluationResult,
    FlowConnection,
    ImagePrompt,
    PagePlan,
    PageRecommendation,
    PageType,
    PromptDetails,
)
from .page_templates import PAGE_LAYOUTS, get_layout_for_page_type, get_zone_prompt_guidance
from .style_loader import format_prompt_injection

logger = logging.getLogger(__name__)

# Default model for prompt generation
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class PromptGenerationError(Exception):
    """Raised when prompt generation fails."""

    pass


class PromptGenerator:
    """Generates and refines image prompts using Claude.

    This class handles the conversion of concept analysis into detailed image
    prompts, and the iterative refinement of prompts based on evaluation feedback.

    Attributes:
        client: Anthropic API client.
        model: Claude model ID to use for generation.
        internal_config: Internal configuration with defaults.

    Example:
        >>> generator = PromptGenerator(api_key="sk-ant-...")
        >>> prompts = generator.generate_prompts(analysis, style)
        >>> for prompt in prompts:
        ...     print(prompt.title)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        internal_config: InternalConfig | None = None,
    ) -> None:
        """Initialize the prompt generator.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            model: Claude model ID to use for generation.
            internal_config: Internal configuration. If None, uses defaults.

        Raises:
            anthropic.AuthenticationError: If API key is invalid.
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.internal_config = internal_config or InternalConfig.from_env()

    def generate_prompts(
        self,
        analysis: ConceptAnalysis,
        style: StyleConfig,
        config: GenerationConfig | None = None,
    ) -> list[ImagePrompt]:
        """Generate image prompts from concept analysis.

        Uses Claude to plan an image sequence that covers all concepts with
        proper flow and narrative structure. Injects style PromptRecipe
        components and applies default negative prompt.

        Args:
            analysis: ConceptAnalysis with extracted concepts and flow.
            style: StyleConfig with PromptRecipe for style injection.
            config: Optional GenerationConfig for aspect ratio and other settings.

        Returns:
            List of ImagePrompt objects, one per planned image.

        Raises:
            PromptGenerationError: If prompt generation fails.
        """
        try:
            # Get style injection components
            style_injection = format_prompt_injection(style)

            # Build the prompt generation request
            generation_prompt = self._build_generation_prompt(
                analysis=analysis,
                style_injection=style_injection,
                config=config,
            )

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": generation_prompt,
                    }
                ],
            )

            # Extract and parse response
            response_text = response.content[0].text
            prompts_data = self._parse_prompts_response(response_text)

            # Build ImagePrompt objects
            prompts = []
            total_images = len(prompts_data)

            for i, prompt_data in enumerate(prompts_data):
                image_number = i + 1
                image_prompt = self._build_image_prompt(
                    prompt_data=prompt_data,
                    image_number=image_number,
                    total_images=total_images,
                    style_injection=style_injection,
                    config=config,
                )
                prompts.append(image_prompt)

            logger.info(f"Generated {len(prompts)} image prompts")
            return prompts

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during prompt generation: {e}")
            raise PromptGenerationError(f"API error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prompt generation response: {e}")
            raise PromptGenerationError(f"Response parse error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during prompt generation: {e}")
            raise PromptGenerationError(f"Prompt generation failed: {e}") from e

    def generate_infographic_prompts(
        self,
        analysis: ConceptAnalysis,
        style: StyleConfig,
        config: GenerationConfig | None = None,
    ) -> list[ImagePrompt]:
        """Generate infographic-style prompts using page recommendation.

        Creates information-dense page prompts based on the adaptive page
        recommendation from concept analysis. Each page uses zone-based
        composition with explicit text specifications.

        Key differences from simple prompt generation:
        - Uses PageRecommendation from analysis for page planning
        - Generates zone-specific content with typography guidance
        - Includes explicit text content specifications
        - Maintains cross-page visual and narrative consistency

        Args:
            analysis: ConceptAnalysis with page_recommendation populated.
            style: StyleConfig with PromptRecipe for style injection.
            config: Optional GenerationConfig for aspect ratio settings.

        Returns:
            List of ImagePrompt objects, one per recommended page.

        Raises:
            PromptGenerationError: If prompt generation fails.
            ValueError: If analysis lacks page_recommendation.
        """
        if not analysis.page_recommendation:
            raise ValueError(
                "ConceptAnalysis must have page_recommendation populated. "
                "Ensure concept_analyzer is using infographic analysis mode."
            )

        try:
            page_rec = analysis.page_recommendation
            style_injection = format_prompt_injection(style)
            prompts = []

            for page_plan in page_rec.pages:
                # Get layout template for this page type
                layout = get_layout_for_page_type(page_plan.page_type)

                # Build the infographic prompt for this page
                infographic_prompt = self._build_infographic_page_prompt(
                    analysis=analysis,
                    page_plan=page_plan,
                    layout=layout,
                    style_injection=style_injection,
                    total_pages=page_rec.page_count,
                    config=config,
                )

                # Call Claude API to generate the detailed prompt
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    messages=[
                        {
                            "role": "user",
                            "content": infographic_prompt,
                        }
                    ],
                )

                # Parse response and build ImagePrompt
                response_text = response.content[0].text
                prompt_data = self._parse_infographic_response(response_text)

                image_prompt = self._build_infographic_image_prompt(
                    prompt_data=prompt_data,
                    page_plan=page_plan,
                    layout=layout,
                    total_pages=page_rec.page_count,
                    style_injection=style_injection,
                    config=config,
                )
                prompts.append(image_prompt)

                logger.info(
                    f"Generated infographic prompt for page {page_plan.page_number}: "
                    f"{page_plan.page_type.value}"
                )

            logger.info(
                f"Generated {len(prompts)} infographic prompts "
                f"({page_rec.page_count} pages recommended)"
            )
            return prompts

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during infographic generation: {e}")
            raise PromptGenerationError(f"API error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse infographic response: {e}")
            raise PromptGenerationError(f"Response parse error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during infographic generation: {e}")
            raise PromptGenerationError(f"Infographic generation failed: {e}") from e

    def _build_infographic_page_prompt(
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
        covered_concepts = [
            c for c in analysis.concepts if c.id in page_plan.concepts_covered
        ]
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

**Core Style:** {style_injection.get('core_style', 'professional, clean, modern infographic')}
**Color Palette:** {style_injection.get('color_constraints', 'professional business colors')}
**Style Prefix:** {style_injection.get('style_prefix', '')}

## Critical Design Requirements

1. **INFORMATION DENSITY**: This is an 11×17 inch infographic at 4K resolution (5100×3300 pixels).
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
Design for {aspect_ratio} aspect ratio (landscape orientation for 11×17 printing).

Generate a prompt that will create an information-rich infographic page that could be printed at 11×17 inches and read like a detailed visual document.

Respond with ONLY the JSON object, no additional text."""

        return prompt

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
            if hasattr(concept, 'key_points') and concept.key_points:
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
            zone_guidance = get_zone_prompt_guidance(zone)

            # Get zone assignment if available
            assigned_content = page_plan.zone_assignments.get(zone.name, "")

            lines.append(f"""
#### Zone: {zone.name}
- **Position:** {zone.position}
- **Size:** {zone.width_percent}% width × {zone.height_percent}% height
- **Content Type:** {zone.content_type.value}
- **Typography Scale:** {zone.typography_scale}
- **Guidance:** {zone.content_guidance}
{f'- **Assigned Content:** {assigned_content}' if assigned_content else ''}
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

    def _parse_infographic_response(self, response_text: str) -> dict[str, Any]:
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

    def _build_infographic_image_prompt(
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
        if style_injection.get("style_prefix") and style_injection["style_prefix"] not in main_prompt:
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
            color_palette=prompt_data.get("color_palette", style_injection.get("color_constraints", "")),
            composition=prompt_data.get("composition", layout.description),
            avoid=combined_avoid,
        )

        # Build flow connection
        flow_connection = FlowConnection(
            previous=page_plan.page_number - 1 if page_plan.page_number > 1 else None,
            next_image=page_plan.page_number + 1 if page_plan.page_number < total_pages else None,
            transition_intent=f"Continues to page {page_plan.page_number + 1}" if page_plan.page_number < total_pages else "Final page",
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
            "Information density appropriate for 11×17 inch print at 300 DPI",
            f"Visual style consistent with {page_plan.page_type.value} page type",
        ]

        if page_plan.page_number > 1:
            criteria.append("Visual consistency with previous pages maintained")

        return criteria

    def refine_prompt(
        self,
        original: ImagePrompt,
        feedback: EvaluationResult,
        attempt: int,
        style: StyleConfig,
        config: GenerationConfig | None = None,
    ) -> ImagePrompt:
        """Refine a prompt based on evaluation feedback.

        Implements an escalating refinement strategy:
        - Attempt 2: Add specific fixes from feedback
        - Attempt 3: Strengthen weak areas, simplify complex elements
        - Attempt 4: Try alternative visual metaphor
        - Attempt 5: Fundamental restructure of composition

        Args:
            original: The original ImagePrompt that was evaluated.
            feedback: EvaluationResult with scores and refinement suggestions.
            attempt: Current attempt number (2-5 typically).
            style: StyleConfig for maintaining style consistency.
            config: Optional GenerationConfig.

        Returns:
            Refined ImagePrompt with updated prompt components.

        Raises:
            PromptGenerationError: If refinement fails.
        """
        try:
            # Determine refinement strategy based on attempt
            strategy = self._get_refinement_strategy(attempt, feedback)

            # Build refinement prompt
            refinement_prompt = self._build_refinement_prompt(
                original=original,
                feedback=feedback,
                strategy=strategy,
                style=format_prompt_injection(style),
            )

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": refinement_prompt,
                    }
                ],
            )

            # Parse response
            response_text = response.content[0].text
            refined_data = self._parse_refinement_response(response_text)

            # Build refined ImagePrompt
            refined_prompt = self._build_refined_prompt(
                original=original,
                refined_data=refined_data,
                attempt=attempt,
            )

            logger.info(
                f"Refined prompt for image {original.image_number}, attempt {attempt}: "
                f"strategy={strategy['name']}"
            )
            return refined_prompt

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during prompt refinement: {e}")
            raise PromptGenerationError(f"API error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during prompt refinement: {e}")
            raise PromptGenerationError(f"Refinement failed: {e}") from e

    def _build_generation_prompt(
        self,
        analysis: ConceptAnalysis,
        style_injection: dict[str, str],
        config: GenerationConfig | None = None,
    ) -> str:
        """Build the prompt for image sequence generation.

        Based on Appendix A.2 from IMAGE_GEN_PLAN.md.

        Args:
            analysis: Concept analysis with extracted concepts.
            style_injection: Formatted style components.
            config: Optional generation configuration.

        Returns:
            Formatted prompt string.
        """
        # Format concepts for the prompt
        concepts_text = self._format_concepts_for_prompt(analysis)

        # Get configuration values
        aspect_ratio = config.aspect_ratio.value if config else "16:9"
        image_count = config.image_count if config and config.image_count > 0 else analysis.recommended_image_count

        # Build the prompt
        prompt = f"""You are an expert visual designer creating prompts for AI image generation.

## Document Analysis

**Title:** {analysis.title}
**Summary:** {analysis.summary}
**Target Audience:** {analysis.target_audience}
**Recommended Images:** {image_count}

## Concepts to Visualize

{concepts_text}

## Logical Flow
{self._format_logical_flow(analysis)}

## Style Guidance

**Core Style:** {style_injection.get('core_style', 'professional, clean, modern')}
**Color Guidance:** {style_injection.get('color_constraints', 'professional color palette')}
**Style Prefix:** {style_injection.get('style_prefix', '')}

## Quality Checklist
{style_injection.get('quality_checklist', '- Professional appearance')}

## Your Task

Create {image_count} image generation prompts that form a cohesive visual narrative explaining these concepts.

For EACH image, provide:
1. **image_title**: A descriptive title for the image
2. **concepts_covered**: Which concept IDs this image covers (list of integers)
3. **visual_intent**: What this image should convey (2-3 sentences)
4. **main_prompt**: The detailed image generation prompt (be specific about visual elements, composition, metaphors)
5. **style_guidance**: Specific style instructions for this image
6. **color_palette**: Color guidance for this image
7. **composition**: Layout and arrangement guidance
8. **avoid**: What to exclude from this image
9. **success_criteria**: List of 3-5 specific, evaluatable criteria
10. **transition_intent**: How this image connects to the next (or "Final image" if last)

### Important Guidelines

1. Each image should clearly visualize its concepts using appropriate visual metaphors
2. Maintain the specified style throughout all images
3. Create a logical visual flow that mirrors the concept flow
4. Do NOT include any text, words, numbers, or labels in the images
5. Success criteria should be specific and measurable (not vague)
6. Ensure each image can stand alone but also connects to the sequence

### Aspect Ratio
Generate prompts for {aspect_ratio} aspect ratio images.

Respond with a JSON array of image prompt objects:
```json
[
  {{
    "image_title": "...",
    "concepts_covered": [1, 2],
    "visual_intent": "...",
    "main_prompt": "...",
    "style_guidance": "...",
    "color_palette": "...",
    "composition": "...",
    "avoid": "...",
    "success_criteria": ["...", "...", "..."],
    "transition_intent": "..."
  }}
]
```

Respond with ONLY the JSON array, no additional text."""

        return prompt

    def _format_concepts_for_prompt(self, analysis: ConceptAnalysis) -> str:
        """Format concepts as text for the generation prompt.

        Args:
            analysis: ConceptAnalysis with concepts.

        Returns:
            Formatted concept descriptions.
        """
        lines = []
        for concept in analysis.concepts:
            lines.append(
                f"**Concept {concept.id}: {concept.name}**\n"
                f"  - Description: {concept.description}\n"
                f"  - Complexity: {concept.complexity.value}\n"
                f"  - Visual Potential: {concept.visual_potential.value}\n"
                f"  - Relationships: {', '.join(concept.relationships) if concept.relationships else 'None'}"
            )
        return "\n\n".join(lines)

    def _format_logical_flow(self, analysis: ConceptAnalysis) -> str:
        """Format the logical flow for the prompt.

        Args:
            analysis: ConceptAnalysis with logical flow.

        Returns:
            Formatted flow description.
        """
        if not analysis.logical_flow:
            return "Linear progression through concepts."

        lines = []
        for step in analysis.logical_flow:
            from_concept = analysis.get_concept_by_id(step.from_concept)
            to_concept = analysis.get_concept_by_id(step.to_concept)
            from_name = from_concept.name if from_concept else f"Concept {step.from_concept}"
            to_name = to_concept.name if to_concept else f"Concept {step.to_concept}"
            lines.append(f"- {from_name} --[{step.relationship.value}]--> {to_name}")

        return "\n".join(lines)

    def _parse_prompts_response(self, response_text: str) -> list[dict[str, Any]]:
        """Parse Claude's response into a list of prompt data dictionaries.

        Args:
            response_text: Raw response text from Claude.

        Returns:
            List of prompt data dictionaries.

        Raises:
            json.JSONDecodeError: If response cannot be parsed.
        """
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find JSON array directly
            json_match = re.search(r"\[[\s\S]*\]", response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text.strip()

        data = json.loads(json_str)

        # Ensure it's a list
        if not isinstance(data, list):
            data = [data]

        return data

    def _build_image_prompt(
        self,
        prompt_data: dict[str, Any],
        image_number: int,
        total_images: int,
        style_injection: dict[str, str],
        config: GenerationConfig | None = None,
    ) -> ImagePrompt:
        """Build an ImagePrompt from parsed data.

        Args:
            prompt_data: Parsed prompt data dictionary.
            image_number: Position in sequence (1-indexed).
            total_images: Total number of images in sequence.
            style_injection: Style components for prompt enhancement.
            config: Optional generation configuration.

        Returns:
            Validated ImagePrompt instance.
        """
        # Build PromptDetails with style injection
        main_prompt = prompt_data.get("main_prompt", "")
        style_guidance = prompt_data.get("style_guidance", style_injection.get("core_style", ""))
        color_palette = prompt_data.get("color_palette", style_injection.get("color_constraints", ""))

        # Combine style prefix with main prompt
        if style_injection.get("style_prefix") and style_injection["style_prefix"] not in main_prompt:
            main_prompt = f"{style_injection['style_prefix']}. {main_prompt}"

        # Build avoid/negative prompt
        avoid = prompt_data.get("avoid", "")
        style_negative = style_injection.get("negative", "")
        default_negative = self.internal_config.negative_prompt
        combined_avoid = self._combine_negative_prompts(avoid, style_negative, default_negative)

        prompt_details = PromptDetails(
            main_prompt=main_prompt,
            style_guidance=style_guidance,
            color_palette=color_palette,
            composition=prompt_data.get("composition", ""),
            avoid=combined_avoid,
        )

        # Build flow connection
        flow_connection = FlowConnection(
            previous=image_number - 1 if image_number > 1 else None,
            next_image=image_number + 1 if image_number < total_images else None,
            transition_intent=prompt_data.get("transition_intent", ""),
        )

        # Extract success criteria
        success_criteria = prompt_data.get("success_criteria", [])
        if not success_criteria:
            # Generate default criteria
            success_criteria = self._generate_default_criteria(prompt_data)

        return ImagePrompt(
            image_number=image_number,
            image_title=prompt_data.get("image_title", f"Image {image_number}"),
            concepts_covered=prompt_data.get("concepts_covered", []),
            visual_intent=prompt_data.get("visual_intent", "Visualize the key concepts"),
            prompt=prompt_details,
            success_criteria=success_criteria,
            flow_connection=flow_connection,
        )

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

    def _generate_default_criteria(self, prompt_data: dict[str, Any]) -> list[str]:
        """Generate default success criteria when none provided.

        Args:
            prompt_data: Prompt data dictionary.

        Returns:
            List of default success criteria.
        """
        criteria = [
            "Clearly visualizes the intended concepts",
            "Professional and visually appealing",
            "Appropriate for the target audience",
        ]

        # Add concept-specific criterion if concepts are covered
        concepts = prompt_data.get("concepts_covered", [])
        if concepts:
            criteria.append(f"Effectively represents concept(s): {', '.join(map(str, concepts))}")

        return criteria

    def _get_refinement_strategy(
        self,
        attempt: int,
        feedback: EvaluationResult,
    ) -> dict[str, Any]:
        """Determine the refinement strategy based on attempt number.

        Escalating strategy:
        - Attempt 2: Add specific fixes from feedback
        - Attempt 3: Strengthen weak areas, simplify
        - Attempt 4: Try alternative visual metaphor
        - Attempt 5+: Fundamental restructure

        Args:
            attempt: Current attempt number.
            feedback: Evaluation result with scores and suggestions.

        Returns:
            Strategy dictionary with name and instructions.
        """
        # Find weakest criterion
        scores = feedback.criteria_scores.to_dict()
        weakest_criterion = min(scores, key=scores.get)
        weakest_score = scores[weakest_criterion]

        if attempt == 2:
            return {
                "name": "specific_fixes",
                "description": "Add specific fixes from evaluation feedback",
                "instructions": (
                    "Apply the specific refinement suggestions from the evaluation. "
                    "Focus on addressing the listed weaknesses while preserving strengths. "
                    "Make targeted changes rather than wholesale rewrites."
                ),
                "focus_areas": feedback.refinement_suggestions,
                "preserve": feedback.strengths,
            }

        elif attempt == 3:
            return {
                "name": "strengthen_and_simplify",
                "description": "Strengthen weak areas while simplifying complex elements",
                "instructions": (
                    f"The weakest area is {weakest_criterion} (score: {weakest_score:.2f}). "
                    "Significantly strengthen this area. Simplify any overly complex visual "
                    "elements that may be causing confusion. Reduce visual noise and "
                    "increase clarity of the core message."
                ),
                "focus_areas": [weakest_criterion] + feedback.missing_elements,
                "preserve": feedback.strengths,
            }

        elif attempt == 4:
            return {
                "name": "alternative_metaphor",
                "description": "Try an alternative visual metaphor",
                "instructions": (
                    "The current visual approach isn't working well. Try a completely "
                    "different visual metaphor or representation for the concepts. "
                    "Think of an alternative way to visualize the same ideas that might "
                    "resonate better with the target audience. Consider using different "
                    "shapes, symbols, or organizational structures."
                ),
                "focus_areas": feedback.weaknesses,
                "preserve": [],  # Fresh approach, don't constrain
            }

        else:  # Attempt 5+
            return {
                "name": "fundamental_restructure",
                "description": "Fundamental restructure of composition and approach",
                "instructions": (
                    "Multiple refinement attempts have not achieved the desired quality. "
                    "Fundamentally rethink the image composition and visual approach. "
                    "Consider: different perspective, different scale, different focus, "
                    "or representing only the most essential concept if covering too much. "
                    "Prioritize clarity over comprehensiveness."
                ),
                "focus_areas": ["simplify", "clarity", "core_message"],
                "preserve": [],
            }

    def _build_refinement_prompt(
        self,
        original: ImagePrompt,
        feedback: EvaluationResult,
        strategy: dict[str, Any],
        style: dict[str, str],
    ) -> str:
        """Build the prompt for refining an image prompt.

        Args:
            original: Original ImagePrompt that was evaluated.
            feedback: Evaluation result with feedback.
            strategy: Refinement strategy dictionary.
            style: Style injection components.

        Returns:
            Formatted refinement prompt.
        """
        # Format feedback
        strengths_text = "\n".join(f"- {s}" for s in feedback.strengths) if feedback.strengths else "- None identified"
        weaknesses_text = "\n".join(f"- {w}" for w in feedback.weaknesses) if feedback.weaknesses else "- None identified"
        missing_text = "\n".join(f"- {m}" for m in feedback.missing_elements) if feedback.missing_elements else "- None identified"
        suggestions_text = "\n".join(f"- {s}" for s in feedback.refinement_suggestions) if feedback.refinement_suggestions else "- None provided"

        # Format scores
        scores = feedback.criteria_scores.to_dict()
        scores_text = "\n".join(f"- {k}: {v:.2f}" for k, v in scores.items())

        prompt = f"""You are refining an image generation prompt based on evaluation feedback.

## Original Prompt

**Title:** {original.title}
**Visual Intent:** {original.visual_intent}
**Main Prompt:** {original.prompt.main_prompt}
**Style Guidance:** {original.prompt.style_guidance}
**Composition:** {original.prompt.composition}
**Color Palette:** {original.prompt.color_palette}

## Evaluation Feedback

**Overall Score:** {feedback.overall_score:.2f}

**Criteria Scores:**
{scores_text}

**Strengths:**
{strengths_text}

**Weaknesses:**
{weaknesses_text}

**Missing Elements:**
{missing_text}

**Refinement Suggestions:**
{suggestions_text}

## Refinement Strategy: {strategy['name']}

{strategy['description']}

**Instructions:** {strategy['instructions']}

## Style Guidance (Maintain)

**Core Style:** {style.get('core_style', '')}
**Color Constraints:** {style.get('color_constraints', '')}

## Your Task

Create a refined prompt that addresses the evaluation feedback while following the refinement strategy.

Focus on:
1. Addressing the weaknesses identified
2. Incorporating missing elements
3. Following the specific refinement instructions
4. Maintaining style consistency
5. Preserving what worked well (strengths)

Respond with a JSON object:
```json
{{
  "main_prompt": "Your refined main prompt...",
  "style_guidance": "Refined style guidance...",
  "composition": "Refined composition guidance...",
  "color_palette": "Color guidance...",
  "avoid": "Elements to avoid...",
  "success_criteria": ["Updated success criteria..."],
  "refinement_reasoning": "Brief explanation of key changes made..."
}}
```

Respond with ONLY the JSON object, no additional text."""

        return prompt

    def _parse_refinement_response(self, response_text: str) -> dict[str, Any]:
        """Parse Claude's refinement response.

        Args:
            response_text: Raw response text.

        Returns:
            Parsed refinement data dictionary.

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

    def _build_refined_prompt(
        self,
        original: ImagePrompt,
        refined_data: dict[str, Any],
        attempt: int,
    ) -> ImagePrompt:
        """Build a refined ImagePrompt from refinement response.

        Args:
            original: Original ImagePrompt.
            refined_data: Parsed refinement data.
            attempt: Current attempt number.

        Returns:
            Refined ImagePrompt with updated components.
        """
        # Build updated PromptDetails
        prompt_details = PromptDetails(
            main_prompt=refined_data.get("main_prompt", original.prompt.main_prompt),
            style_guidance=refined_data.get("style_guidance", original.prompt.style_guidance),
            color_palette=refined_data.get("color_palette", original.prompt.color_palette),
            composition=refined_data.get("composition", original.prompt.composition),
            avoid=refined_data.get("avoid", original.prompt.avoid),
        )

        # Update success criteria if provided
        success_criteria = refined_data.get("success_criteria", original.success_criteria)
        if not success_criteria:
            success_criteria = original.success_criteria

        # Log refinement reasoning if available
        reasoning = refined_data.get("refinement_reasoning", "")
        if reasoning:
            logger.debug(f"Refinement reasoning for attempt {attempt}: {reasoning}")

        return ImagePrompt(
            image_number=original.image_number,
            image_title=original.title,
            concepts_covered=original.concepts_covered,
            visual_intent=original.visual_intent,
            prompt=prompt_details,
            success_criteria=success_criteria,
            flow_connection=original.flow_connection,
        )


def generate_prompts(
    analysis: ConceptAnalysis,
    style: StyleConfig,
    config: GenerationConfig | None = None,
    api_key: str | None = None,
) -> list[ImagePrompt]:
    """Generate image prompts from concept analysis.

    Convenience function that creates a PromptGenerator and generates prompts.

    Args:
        analysis: ConceptAnalysis with extracted concepts.
        style: StyleConfig with PromptRecipe.
        config: Optional GenerationConfig.
        api_key: Optional Anthropic API key.

    Returns:
        List of ImagePrompt objects.

    Raises:
        PromptGenerationError: If generation fails.
    """
    generator = PromptGenerator(api_key=api_key)
    return generator.generate_prompts(analysis, style, config)


def refine_prompt(
    original: ImagePrompt,
    feedback: EvaluationResult,
    attempt: int,
    style: StyleConfig,
    config: GenerationConfig | None = None,
    api_key: str | None = None,
) -> ImagePrompt:
    """Refine a prompt based on evaluation feedback.

    Convenience function that creates a PromptGenerator and refines a prompt.

    Args:
        original: Original ImagePrompt.
        feedback: EvaluationResult with suggestions.
        attempt: Current attempt number (2-5).
        style: StyleConfig for style consistency.
        config: Optional GenerationConfig.
        api_key: Optional Anthropic API key.

    Returns:
        Refined ImagePrompt.

    Raises:
        PromptGenerationError: If refinement fails.
    """
    generator = PromptGenerator(api_key=api_key)
    return generator.refine_prompt(original, feedback, attempt, style, config)


def create_prompt_generator(
    api_key: str | None = None,
    internal_config: InternalConfig | None = None,
) -> PromptGenerator:
    """Factory function to create a PromptGenerator.

    Args:
        api_key: Optional Anthropic API key.
        internal_config: Optional internal configuration.

    Returns:
        Configured PromptGenerator instance.
    """
    return PromptGenerator(api_key=api_key, internal_config=internal_config)


def generate_infographic_prompts(
    analysis: ConceptAnalysis,
    style: StyleConfig,
    config: GenerationConfig | None = None,
    api_key: str | None = None,
) -> list[ImagePrompt]:
    """Generate infographic-style prompts from concept analysis.

    Creates information-dense page prompts based on the adaptive page
    recommendation from concept analysis. This is the preferred method
    for generating visual explanations of complex documents.

    Key features:
    - Adaptive page count (1-6) based on document complexity
    - Zone-based composition with explicit text specifications
    - Typography guidance for headline/subhead/body/caption
    - Cross-page visual and narrative consistency

    Args:
        analysis: ConceptAnalysis with page_recommendation populated.
        style: StyleConfig with PromptRecipe.
        config: Optional GenerationConfig.
        api_key: Optional Anthropic API key.

    Returns:
        List of ImagePrompt objects, one per recommended page.

    Raises:
        PromptGenerationError: If generation fails.
        ValueError: If analysis lacks page_recommendation.

    Example:
        >>> # Analyze document with infographic mode
        >>> analysis = analyze_document(doc_path, infographic_mode=True)
        >>>
        >>> # Generate infographic prompts
        >>> prompts = generate_infographic_prompts(analysis, style)
        >>>
        >>> # Each prompt is designed for 11×17 inch infographic
        >>> for prompt in prompts:
        ...     print(f"Page {prompt.image_number}: {prompt.title}")
    """
    generator = PromptGenerator(api_key=api_key)
    return generator.generate_infographic_prompts(analysis, style, config)
