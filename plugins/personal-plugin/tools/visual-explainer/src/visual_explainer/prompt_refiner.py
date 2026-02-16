"""Prompt refinement for Visual Concept Explainer.

This module handles iterative refinement of image prompts based on
evaluation feedback. It implements an escalating strategy that progresses
from targeted fixes to fundamental restructuring.

Refinement strategies by attempt:
- Attempt 2: Add specific fixes from feedback
- Attempt 3: Strengthen weak areas, simplify complex elements
- Attempt 4: Try alternative visual metaphor
- Attempt 5+: Fundamental restructure of composition

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
    EvaluationResult,
    ImagePrompt,
    PromptDetails,
)
from .style_loader import format_prompt_injection

logger = logging.getLogger(__name__)

# Default model for prompt refinement
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class PromptRefiner:
    """Refines image prompts based on evaluation feedback.

    Implements an escalating refinement strategy where each successive
    attempt tries a more aggressive approach to improve the prompt.

    Attributes:
        client: Anthropic API client.
        model: Claude model ID to use for refinement.
        internal_config: Internal configuration with defaults.

    Example:
        >>> refiner = PromptRefiner(client=anthropic_client, model="claude-sonnet-4-20250514")
        >>> refined = refiner.refine_prompt(original, feedback, attempt=2, style=style)
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str = DEFAULT_MODEL,
        internal_config: InternalConfig | None = None,
    ) -> None:
        """Initialize the prompt refiner.

        Args:
            client: Pre-configured Anthropic API client.
            model: Claude model ID to use for refinement.
            internal_config: Internal configuration. If None, uses defaults.
        """
        self.client = client
        self.model = model
        self.internal_config = internal_config or InternalConfig.from_env()

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
        from .prompt_generator import PromptGenerationError

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
        strengths_text = (
            "\n".join(f"- {s}" for s in feedback.strengths)
            if feedback.strengths
            else "- None identified"
        )
        weaknesses_text = (
            "\n".join(f"- {w}" for w in feedback.weaknesses)
            if feedback.weaknesses
            else "- None identified"
        )
        missing_text = (
            "\n".join(f"- {m}" for m in feedback.missing_elements)
            if feedback.missing_elements
            else "- None identified"
        )
        suggestions_text = (
            "\n".join(f"- {s}" for s in feedback.refinement_suggestions)
            if feedback.refinement_suggestions
            else "- None provided"
        )

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

## Refinement Strategy: {strategy["name"]}

{strategy["description"]}

**Instructions:** {strategy["instructions"]}

## Style Guidance (Maintain)

**Core Style:** {style.get("core_style", "")}
**Color Constraints:** {style.get("color_constraints", "")}

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
