"""Prompt generation and refinement for Visual Concept Explainer.

This module generates image prompts from concept analysis and refines them
based on evaluation feedback. It implements:

1. generate_prompts(): Uses Claude to plan an image sequence from concepts
2. refine_prompt(): Iteratively improves prompts based on evaluation feedback

The refinement strategy escalates across attempts:
- Attempt 2: Add specific fixes from feedback
- Attempt 3: Strengthen weak areas, simplify
- Attempt 4: Try alternative visual metaphor
- Attempt 5: Fundamental restructure

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
    EvaluationResult,
    FlowConnection,
    ImagePrompt,
    PromptDetails,
)
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
