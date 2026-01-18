"""Image evaluation using Claude Vision.

This module provides the ImageEvaluator class that uses Claude Sonnet's vision
capabilities to evaluate generated images against success criteria and provide
refinement suggestions for prompt iteration.

The evaluator:
- Scores images on multiple criteria (concept clarity, visual appeal, etc.)
- Determines verdicts based on thresholds: PASS >= 0.85, NEEDS_REFINEMENT 0.5-0.84, FAIL < 0.5
- Extracts actionable refinement suggestions for prompt improvement
- Handles errors gracefully with meaningful feedback
"""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

import anthropic

from .models import CriteriaScores, EvaluationResult, EvaluationVerdict

logger = logging.getLogger(__name__)

# Default evaluation model - Sonnet is sufficient for vision, 5x cheaper than Opus
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Default thresholds for verdict determination
DEFAULT_PASS_THRESHOLD = 0.85
DEFAULT_FAIL_THRESHOLD = 0.5


class ImageEvaluationError(Exception):
    """Raised when image evaluation fails."""

    pass


class ImageEvaluator:
    """Evaluates generated images using Claude Vision.

    This class uses Claude Sonnet's vision capabilities to evaluate generated
    images against their intended purpose and success criteria.

    Attributes:
        client: Anthropic API client.
        model: Model ID to use for evaluation.
        pass_threshold: Score threshold for PASS verdict (default: 0.85).
        fail_threshold: Score threshold for FAIL verdict (default: 0.5).

    Example:
        >>> evaluator = ImageEvaluator(api_key="sk-ant-...")
        >>> with open("image.jpg", "rb") as f:
        ...     image_bytes = f.read()
        >>> result = evaluator.evaluate_image(
        ...     image_bytes=image_bytes,
        ...     intent="Show the relationship between inputs and outputs",
        ...     criteria=["Clear visual metaphor", "Professional appearance"],
        ...     context={"audience": "technical", "image_number": 1, "total_images": 3}
        ... )
        >>> print(result.verdict)
        PASS
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
        fail_threshold: float = DEFAULT_FAIL_THRESHOLD,
    ) -> None:
        """Initialize the image evaluator.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            model: Claude model to use for evaluation.
            pass_threshold: Score threshold for PASS verdict.
            fail_threshold: Score threshold for FAIL verdict.

        Raises:
            anthropic.AuthenticationError: If API key is invalid.
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.pass_threshold = pass_threshold
        self.fail_threshold = fail_threshold

    def evaluate_image(
        self,
        image_bytes: bytes,
        intent: str,
        criteria: list[str],
        context: dict[str, Any],
        image_id: int = 1,
        iteration: int = 1,
    ) -> EvaluationResult:
        """Evaluate a generated image against intent and criteria.

        This method sends the image to Claude Vision along with the evaluation
        prompt, parses the structured response, and returns an EvaluationResult
        with scores, strengths, weaknesses, verdict, and refinement suggestions.

        Args:
            image_bytes: Raw JPEG image bytes to evaluate.
            intent: The visual intent/goal for this image.
            criteria: List of success criteria to evaluate against.
            context: Additional context including:
                - audience: Target audience (e.g., "technical", "general")
                - image_number: Position in sequence (1-indexed)
                - total_images: Total images in sequence
                - style: Visual style name
                - previous_image_summary: Summary of previous image (if applicable)
            image_id: Image number being evaluated (for result tracking).
            iteration: Generation attempt number (for result tracking).

        Returns:
            EvaluationResult with scores, verdict, and refinement suggestions.

        Raises:
            ImageEvaluationError: If evaluation fails (API error, parse error, etc.).
        """
        try:
            # Build the evaluation prompt
            prompt = self._build_evaluation_prompt(intent, criteria, context)

            # Encode image as base64
            image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

            # Determine media type (assume JPEG since Gemini returns JPEG)
            media_type = self._detect_media_type(image_bytes)

            # Call Claude Vision API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse the JSON response
            evaluation_data = self._parse_evaluation_response(response_text)

            # Build and return EvaluationResult
            return self._build_evaluation_result(
                image_id=image_id,
                iteration=iteration,
                evaluation_data=evaluation_data,
            )

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during evaluation: {e}")
            raise ImageEvaluationError(f"API error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation response as JSON: {e}")
            raise ImageEvaluationError(f"Response parse error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during evaluation: {e}")
            raise ImageEvaluationError(f"Evaluation failed: {e}") from e

    def _build_evaluation_prompt(
        self,
        intent: str,
        criteria: list[str],
        context: dict[str, Any],
    ) -> str:
        """Build the evaluation prompt for Claude Vision.

        Args:
            intent: The visual intent/goal for this image.
            criteria: List of success criteria.
            context: Additional context dict.

        Returns:
            Formatted evaluation prompt string.
        """
        # Format criteria as bullet list
        criteria_text = "\n".join(f"- {c}" for c in criteria)

        # Extract context values with defaults
        audience = context.get("audience", "general")
        image_number = context.get("image_number", 1)
        total_images = context.get("total_images", 1)
        style = context.get("style", "professional")
        previous_summary = context.get("previous_image_summary", "")

        # Build sequence context
        sequence_context = f"Image {image_number} of {total_images}"
        if previous_summary:
            sequence_context += f"\nPrevious image showed: {previous_summary}"

        prompt = f"""You are evaluating an AI-generated image for quality and intent alignment.

## Original Intent
{intent}

## Success Criteria
{criteria_text}

## Context
- Target audience: {audience}
- Part of sequence: {sequence_context}
- Visual style: {style}

## Your Task
Evaluate this image against the criteria above. Provide your assessment in JSON format.

### Scoring Guidelines
- 0.0-0.49: Poor - Major issues, doesn't meet the criterion
- 0.50-0.69: Fair - Partially meets the criterion with notable issues
- 0.70-0.84: Good - Meets the criterion with minor issues
- 0.85-1.0: Excellent - Fully meets or exceeds the criterion

### Required JSON Response Structure
```json
{{
  "overall_score": 0.0,
  "criteria_scores": {{
    "concept_clarity": 0.0,
    "visual_appeal": 0.0,
    "audience_appropriateness": 0.0,
    "flow_continuity": 0.0
  }},
  "strengths": ["List of what works well"],
  "weaknesses": ["List of what needs improvement"],
  "missing_elements": ["Elements that should be present but aren't"],
  "refinement_suggestions": ["Specific prompt changes to improve the image"]
}}
```

### Criteria Definitions
- **concept_clarity**: How clearly the intended concepts are visualized
- **visual_appeal**: Aesthetic quality, professional appearance, visual coherence
- **audience_appropriateness**: Suitability for the target audience
- **flow_continuity**: How well it connects to other images in the sequence (use 0.8 if standalone)

### Important Notes
1. Be constructive in refinement_suggestions - focus on specific, actionable prompt changes
2. Overall score should reflect the weighted importance of each criterion
3. Strengths should highlight what to preserve in refinements
4. Missing_elements should list specific visual elements, not general concepts

Respond with ONLY the JSON object, no additional text."""

        return prompt

    def _detect_media_type(self, image_bytes: bytes) -> str:
        """Detect the media type from image bytes.

        Args:
            image_bytes: Raw image bytes.

        Returns:
            Media type string (e.g., "image/jpeg", "image/png").
        """
        # Check magic bytes
        if image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif image_bytes[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
        elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        else:
            # Default to JPEG (Gemini's default output)
            return "image/jpeg"

    def _parse_evaluation_response(self, response_text: str) -> dict[str, Any]:
        """Parse Claude's evaluation response into a dictionary.

        Handles responses that may have markdown code blocks or extra text.

        Args:
            response_text: Raw response text from Claude.

        Returns:
            Parsed evaluation dictionary.

        Raises:
            json.JSONDecodeError: If response cannot be parsed as JSON.
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

    def _build_evaluation_result(
        self,
        image_id: int,
        iteration: int,
        evaluation_data: dict[str, Any],
    ) -> EvaluationResult:
        """Build an EvaluationResult from parsed evaluation data.

        Applies verdict thresholds and validates data.

        Args:
            image_id: Image number being evaluated.
            iteration: Generation attempt number.
            evaluation_data: Parsed JSON evaluation data.

        Returns:
            Validated EvaluationResult instance.
        """
        # Extract overall score with validation
        overall_score = float(evaluation_data.get("overall_score", 0.0))
        overall_score = max(0.0, min(1.0, overall_score))  # Clamp to 0-1

        # Extract criteria scores
        criteria_data = evaluation_data.get("criteria_scores", {})
        criteria_scores = CriteriaScores(
            concept_clarity=self._clamp_score(criteria_data.get("concept_clarity", overall_score)),
            visual_appeal=self._clamp_score(criteria_data.get("visual_appeal", overall_score)),
            audience_appropriateness=self._clamp_score(
                criteria_data.get("audience_appropriateness", overall_score)
            ),
            flow_continuity=self._clamp_score(criteria_data.get("flow_continuity", 0.8)),
        )

        # Determine verdict based on thresholds
        verdict = self._determine_verdict(overall_score)

        # Extract lists with defaults
        strengths = evaluation_data.get("strengths", [])
        weaknesses = evaluation_data.get("weaknesses", [])
        missing_elements = evaluation_data.get("missing_elements", [])
        refinement_suggestions = evaluation_data.get("refinement_suggestions", [])

        # Ensure lists are actually lists
        if not isinstance(strengths, list):
            strengths = [str(strengths)] if strengths else []
        if not isinstance(weaknesses, list):
            weaknesses = [str(weaknesses)] if weaknesses else []
        if not isinstance(missing_elements, list):
            missing_elements = [str(missing_elements)] if missing_elements else []
        if not isinstance(refinement_suggestions, list):
            refinement_suggestions = [str(refinement_suggestions)] if refinement_suggestions else []

        return EvaluationResult(
            image_id=image_id,
            iteration=iteration,
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_elements=missing_elements,
            verdict=verdict,
            refinement_suggestions=refinement_suggestions,
        )

    def _clamp_score(self, value: Any) -> float:
        """Clamp a value to the valid score range 0.0-1.0.

        Args:
            value: Value to clamp (may be None or non-numeric).

        Returns:
            Float clamped to 0.0-1.0.
        """
        try:
            score = float(value) if value is not None else 0.0
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return 0.0

    def _determine_verdict(self, overall_score: float) -> EvaluationVerdict:
        """Determine the verdict based on score thresholds.

        Thresholds:
        - PASS: >= pass_threshold (default 0.85)
        - NEEDS_REFINEMENT: >= fail_threshold and < pass_threshold (0.5-0.84)
        - FAIL: < fail_threshold (default 0.5)

        Args:
            overall_score: The overall evaluation score.

        Returns:
            EvaluationVerdict enum value.
        """
        if overall_score >= self.pass_threshold:
            return EvaluationVerdict.PASS
        elif overall_score >= self.fail_threshold:
            return EvaluationVerdict.NEEDS_REFINEMENT
        else:
            return EvaluationVerdict.FAIL


def create_evaluator(
    api_key: str | None = None,
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> ImageEvaluator:
    """Factory function to create an ImageEvaluator.

    This is a convenience function that creates an evaluator with common defaults.

    Args:
        api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        pass_threshold: Score threshold for PASS verdict.

    Returns:
        Configured ImageEvaluator instance.
    """
    return ImageEvaluator(
        api_key=api_key,
        pass_threshold=pass_threshold,
    )
