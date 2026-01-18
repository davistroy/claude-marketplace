"""Data models for Visual Concept Explainer.

This module provides Pydantic v2 models for all data structures used in the
visual explanation generation pipeline:

- Concept: A single extracted concept from the document
- ConceptAnalysis: Complete analysis result including all concepts and flow
- ImagePrompt: Generated prompt for a single image
- EvaluationResult: Evaluation of a generated image
- ImageResult: Tracking for a single image through generation attempts
- GenerationMetadata: Full metadata for the generation session (matches §8 schema)

These models provide the contract between modules and enable JSON
serialization via model_dump(mode='json').
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field


class Complexity(str, Enum):
    """Complexity level of a concept."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class VisualPotential(str, Enum):
    """How well a concept can be visualized."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RelationshipType(str, Enum):
    """Type of relationship between concepts."""

    LEADS_TO = "leads_to"
    SUPPORTS = "supports"
    CONTRASTS = "contrasts"
    BUILDS_ON = "builds_on"
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    REQUIRES = "requires"
    ENABLES = "enables"


class EvaluationVerdict(str, Enum):
    """Verdict from image evaluation.

    Based on score thresholds:
    - PASS: >= 0.85 (or configured pass_threshold)
    - NEEDS_REFINEMENT: 0.5 to 0.84
    - FAIL: < 0.5
    """

    PASS = "PASS"
    NEEDS_REFINEMENT = "NEEDS_REFINEMENT"
    FAIL = "FAIL"

    @classmethod
    def from_score(cls, score: float, pass_threshold: float = 0.85) -> "EvaluationVerdict":
        """Determine verdict from overall score.

        Args:
            score: Overall evaluation score (0.0 to 1.0).
            pass_threshold: Minimum score for PASS verdict (default: 0.85).

        Returns:
            EvaluationVerdict based on score thresholds.
        """
        if score >= pass_threshold:
            return cls.PASS
        elif score >= 0.5:
            return cls.NEEDS_REFINEMENT
        else:
            return cls.FAIL


# =============================================================================
# Content Type and Page Planning Models (Infographic Generation)
# =============================================================================


class ContentType(str, Enum):
    """Types of content that require different visual treatments."""

    STATISTICS = "statistics"  # Quantitative data, percentages, metrics
    PROCESS = "process"  # Sequential steps, workflows, procedures
    COMPARISON = "comparison"  # Side-by-side analysis, alternatives, trade-offs
    HIERARCHY = "hierarchy"  # Org structures, taxonomies, nested relationships
    TIMELINE = "timeline"  # Chronological sequences, milestones, phases
    FRAMEWORK = "framework"  # Conceptual models, matrices, named methodologies
    NARRATIVE = "narrative"  # Explanatory text, stories, context
    LIST = "list"  # Parallel items, bullet points, enumerated content
    MATRIX = "matrix"  # Multi-dimensional comparisons, grids


class PageType(str, Enum):
    """Types of infographic pages, each with specific layout and purpose."""

    HERO_SUMMARY = "hero_summary"  # Executive overview - the "one page" view
    PROBLEM_LANDSCAPE = "problem_landscape"  # Why this matters, failure modes, risks
    FRAMEWORK_OVERVIEW = "framework_overview"  # High-level process/methodology view
    FRAMEWORK_DEEP_DIVE = "framework_deep_dive"  # Detailed breakdown of stages
    COMPARISON_MATRIX = "comparison_matrix"  # Side-by-side vendor/option analysis
    DIMENSIONS_VARIATIONS = "dimensions_variations"  # How framework adapts to contexts
    REFERENCE_ACTION = "reference_action"  # Checklists, decision trees, quick reference
    DATA_EVIDENCE = "data_evidence"  # Charts, statistics, research findings


class ContentZone(BaseModel):
    """A content zone within a page layout.

    Each page is divided into zones that hold different types of content.
    Zones are specified as percentages of the page area.

    Attributes:
        name: Identifier for this zone (e.g., "hero_stat", "main_diagram").
        position: Position descriptor (e.g., "top_left", "center", "right_rail").
        width_percent: Width as percentage of page (5-100).
        height_percent: Height as percentage of page (5-100).
        content_type: Primary content type for this zone.
        content_guidance: Specific guidance for what goes in this zone.
        typography_scale: Relative text size ("headline", "subhead", "body", "caption").
    """

    name: str = Field(description="Zone identifier")
    position: str = Field(description="Position descriptor")
    width_percent: int = Field(ge=5, le=100, description="Width as percentage")
    height_percent: int = Field(ge=5, le=100, description="Height as percentage")
    content_type: ContentType = Field(description="Primary content type")
    content_guidance: str = Field(description="What goes in this zone")
    typography_scale: Literal["headline", "subhead", "body", "caption"] = Field(
        default="body",
        description="Relative text size for this zone",
    )


class PageLayout(BaseModel):
    """Layout template for a specific page type.

    Defines the structure of zones and their arrangement for
    generating information-dense infographic pages.

    Attributes:
        page_type: Type of page this layout is for.
        description: What this layout is designed for.
        zones: List of content zones that make up the page.
        design_notes: Additional design guidance for this layout.
    """

    page_type: PageType = Field(description="Page type this layout serves")
    description: str = Field(description="Purpose of this layout")
    zones: list[ContentZone] = Field(description="Content zones in this layout")
    design_notes: str = Field(default="", description="Additional design guidance")


class PagePlan(BaseModel):
    """Plan for a single infographic page.

    Maps content from the document to a specific page layout.

    Attributes:
        page_number: Position in the page sequence (1-indexed).
        page_type: Type of page layout to use.
        title: Title for this page.
        content_focus: What this page should communicate.
        concepts_covered: Which concept IDs this page addresses.
        content_types_present: What types of content appear on this page.
        zone_assignments: Mapping of zone names to content descriptions.
        cross_references: References to other pages for navigation.
    """

    page_number: int = Field(ge=1, description="Position in sequence")
    page_type: PageType = Field(description="Layout type to use")
    title: str = Field(description="Page title")
    content_focus: str = Field(description="Primary message of this page")
    concepts_covered: list[int] = Field(
        default_factory=list,
        description="Concept IDs addressed",
    )
    content_types_present: list[ContentType] = Field(
        default_factory=list,
        description="Content types on this page",
    )
    zone_assignments: dict[str, str] = Field(
        default_factory=dict,
        description="Zone name -> content description",
    )
    cross_references: list[str] = Field(
        default_factory=list,
        description="References to other pages",
    )


class PageRecommendation(BaseModel):
    """Recommendation for page count and structure.

    Output from the analysis phase that determines how many pages
    are needed and what type each should be.

    Attributes:
        page_count: Recommended number of pages (1-6).
        rationale: Explanation for the recommendation.
        pages: Planned page structures.
        compression_warnings: Alerts about content that may be compressed.
    """

    page_count: int = Field(ge=1, le=6, description="Recommended page count")
    rationale: str = Field(description="Why this page count is appropriate")
    pages: list[PagePlan] = Field(description="Plan for each page")
    compression_warnings: list[str] = Field(
        default_factory=list,
        description="Content that may be over-compressed",
    )


# =============================================================================
# Concept Analysis Models (Phase 2 - Document Analysis)
# =============================================================================


class Concept(BaseModel):
    """A single concept extracted from the document.

    Attributes:
        id: Unique identifier for this concept within the analysis (1-indexed).
        name: Short, descriptive name for the concept.
        description: Full explanation of what this concept means.
        relationships: List of related concept IDs with relationship type.
        complexity: How complex this concept is to understand.
        visual_potential: How well this concept lends itself to visualization.
    """

    id: int = Field(ge=1, description="Unique identifier for this concept")
    name: str = Field(description="Short, descriptive name", min_length=1, max_length=200)
    description: str = Field(description="Full explanation of the concept")
    relationships: list[str] = Field(
        default_factory=list,
        description="Related concept IDs (format: 'concept_id:N')",
    )
    complexity: Complexity = Field(
        default=Complexity.MODERATE,
        description="Complexity level: simple, moderate, complex",
    )
    visual_potential: VisualPotential = Field(
        default=VisualPotential.MEDIUM,
        description="Visualization potential: high, medium, low",
    )

    def get_related_ids(self) -> list[int]:
        """Extract numeric IDs from relationship strings.

        Returns:
            List of concept IDs referenced in relationships.
        """
        ids = []
        for rel in self.relationships:
            if ":" in rel:
                try:
                    ids.append(int(rel.split(":")[-1]))
                except ValueError:
                    pass
        return ids


class LogicalFlowStep(BaseModel):
    """A single step in the logical flow between concepts.

    Attributes:
        from_concept: Source concept ID.
        to_concept: Target concept ID.
        relationship: Type of relationship between concepts.
    """

    from_concept: int = Field(alias="from", ge=1, description="Source concept ID")
    to_concept: int = Field(alias="to", ge=1, description="Target concept ID")
    relationship: RelationshipType = Field(description="Relationship type")

    model_config = {"populate_by_name": True}


class ConceptAnalysis(BaseModel):
    """Complete analysis of a document's concepts.

    This is the output from the concept analyzer and serves as input
    to the prompt generator.

    Attributes:
        title: Title of the document or main topic.
        summary: One-paragraph summary of the content.
        target_audience: Who this content is intended for.
        concepts: List of extracted concepts.
        logical_flow: Relationships between concepts in order.
        content_types_detected: Types of content found in the document.
        recommended_image_count: Suggested number of images (1-20) - legacy field.
        reasoning: Explanation for the recommendation.
        page_recommendation: Structured page planning recommendation.
        content_hash: SHA-256 hash of source content for caching.
        word_count: Word count of the analyzed document.
    """

    title: str = Field(description="Document or topic title", min_length=1, max_length=500)
    summary: str = Field(description="One-paragraph summary", min_length=1)
    target_audience: str = Field(
        default="General audience",
        description="Target audience description",
    )
    concepts: list[Concept] = Field(
        default_factory=list,
        min_length=1,
        description="Extracted concepts",
    )
    logical_flow: list[LogicalFlowStep] = Field(
        default_factory=list,
        description="Flow between concepts",
    )
    content_types_detected: list[ContentType] = Field(
        default_factory=list,
        description="Types of content found in document",
    )
    recommended_image_count: int = Field(
        default=1,
        ge=1,
        le=20,
        description="Recommended number of images (legacy, use page_recommendation)",
    )
    reasoning: str = Field(
        default="",
        description="Explanation for image count recommendation",
    )
    page_recommendation: PageRecommendation | None = Field(
        default=None,
        description="Structured page planning recommendation",
    )
    content_hash: str = Field(
        default="",
        description="SHA-256 hash of source content (sha256:...)",
    )
    word_count: int = Field(default=0, ge=0, description="Source word count")

    def get_concept_by_id(self, concept_id: int) -> Concept | None:
        """Get a concept by its ID.

        Args:
            concept_id: The concept ID to find.

        Returns:
            The Concept if found, None otherwise.
        """
        for concept in self.concepts:
            if concept.id == concept_id:
                return concept
        return None

    def get_concepts_for_image(self, concept_ids: list[int]) -> list[Concept]:
        """Get concepts by their IDs for image generation.

        Args:
            concept_ids: List of concept IDs to retrieve.

        Returns:
            List of matching Concept objects.
        """
        return [c for c in self.concepts if c.id in concept_ids]


# =============================================================================
# Image Prompt Models (Phase 4 - Prompt Generation)
# =============================================================================


class FlowConnection(BaseModel):
    """Connection to adjacent images in a sequence.

    Attributes:
        previous: Previous image number (None if first).
        next_image: Next image number (None if last).
        transition_intent: How this image connects to the next.
    """

    previous: int | None = Field(default=None, description="Previous image number")
    next_image: int | None = Field(
        default=None,
        alias="next",
        description="Next image number",
    )
    transition_intent: str = Field(
        default="",
        description="How this connects to adjacent images",
    )

    model_config = {"populate_by_name": True}


class PromptDetails(BaseModel):
    """Detailed prompt components for image generation.

    Attributes:
        main_prompt: The full image generation prompt.
        style_guidance: Specific style instructions.
        color_palette: Color guidance for the image.
        composition: Layout and arrangement guidance.
        avoid: What to exclude from the image.
    """

    main_prompt: str = Field(description="Full image generation prompt", min_length=1)
    style_guidance: str = Field(default="", description="Style instructions")
    color_palette: str = Field(default="", description="Color guidance")
    composition: str = Field(default="", description="Layout guidance")
    avoid: str = Field(default="", description="Elements to exclude")

    def get_full_prompt(self, include_avoid: bool = False) -> str:
        """Combine all prompt components into a single string.

        Args:
            include_avoid: Whether to include negative prompt elements.

        Returns:
            Combined prompt string.
        """
        parts = [self.main_prompt]
        if self.style_guidance:
            parts.append(self.style_guidance)
        if self.composition:
            parts.append(self.composition)
        if self.color_palette:
            parts.append(self.color_palette)
        if include_avoid and self.avoid:
            parts.append(f"Avoid: {self.avoid}")
        return " ".join(parts)


class ImagePrompt(BaseModel):
    """Generated prompt for a single image.

    This represents the complete prompt package for generating one image
    in the visual explanation sequence.

    Attributes:
        image_number: Position in the image sequence (1-indexed).
        title: Title for this image (aliased as image_title per spec).
        concepts_covered: List of concept IDs this image explains.
        visual_intent: What this image should convey.
        prompt: Detailed prompt components.
        success_criteria: Criteria for evaluating the image.
        flow_connection: How this connects to adjacent images.
    """

    image_number: int = Field(ge=1, description="Position in sequence (1-indexed)")
    title: str = Field(
        alias="image_title",
        description="Title for this image",
        min_length=1,
        max_length=200,
    )
    concepts_covered: list[int] = Field(
        default_factory=list,
        description="Concept IDs covered by this image",
    )
    visual_intent: str = Field(description="What the image should convey", min_length=1)
    prompt: PromptDetails = Field(description="Detailed prompt components")
    success_criteria: list[str] = Field(
        default_factory=list,
        min_length=1,
        description="Criteria for evaluation",
    )
    flow_connection: FlowConnection = Field(
        default_factory=FlowConnection,
        description="Connection to adjacent images",
    )

    model_config = {"populate_by_name": True}

    @computed_field
    @property
    def is_first(self) -> bool:
        """Check if this is the first image in the sequence."""
        return self.flow_connection.previous is None

    @computed_field
    @property
    def is_last(self) -> bool:
        """Check if this is the last image in the sequence."""
        return self.flow_connection.next_image is None

    def get_full_prompt(self, negative_prompt: str = "") -> str:
        """Combine all prompt components into a single generation prompt.

        Args:
            negative_prompt: Optional negative prompt to append.

        Returns:
            Complete prompt string for image generation.
        """
        return self.prompt.get_full_prompt(include_avoid=False)


# =============================================================================
# Evaluation Models (Phase 6 - Image Evaluation)
# =============================================================================


class CriteriaScores(BaseModel):
    """Scores for individual evaluation criteria.

    Matches the criteria_scores structure from spec §3 Phase 6.

    Attributes:
        concept_clarity: How clearly concepts are visualized (0.0-1.0).
        visual_appeal: Aesthetic quality of the image (0.0-1.0).
        audience_appropriateness: Suitability for target audience (0.0-1.0).
        flow_continuity: How well it connects to other images (0.0-1.0).
    """

    concept_clarity: float = Field(ge=0.0, le=1.0, description="How clearly concepts are visualized")
    visual_appeal: float = Field(ge=0.0, le=1.0, description="Aesthetic quality")
    audience_appropriateness: float = Field(ge=0.0, le=1.0, description="Suitability for audience")
    flow_continuity: float = Field(ge=0.0, le=1.0, description="Connection to sequence")

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            "concept_clarity": self.concept_clarity,
            "visual_appeal": self.visual_appeal,
            "audience_appropriateness": self.audience_appropriateness,
            "flow_continuity": self.flow_continuity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "CriteriaScores":
        """Create from dictionary (handles missing keys with defaults).

        Args:
            data: Dictionary with score values.

        Returns:
            CriteriaScores instance.
        """
        return cls(
            concept_clarity=data.get("concept_clarity", 0.0),
            visual_appeal=data.get("visual_appeal", 0.0),
            audience_appropriateness=data.get("audience_appropriateness", 0.0),
            flow_continuity=data.get("flow_continuity", 0.0),
        )


class EvaluationResult(BaseModel):
    """Result from evaluating a generated image.

    Matches the evaluation structure from spec §3 Phase 6.

    Attributes:
        image_id: Which image this evaluates (1-indexed).
        iteration: Which generation attempt this evaluates (1-indexed).
        overall_score: Overall quality score (0.0-1.0).
        criteria_scores: Structured scores for each criterion.
        strengths: What works well in the image.
        weaknesses: What needs improvement.
        missing_elements: Elements that should be present but aren't.
        verdict: PASS, NEEDS_REFINEMENT, or FAIL.
        refinement_suggestions: Specific changes to improve the prompt.
    """

    image_id: int = Field(ge=1, description="Image number being evaluated (1-indexed)")
    iteration: int = Field(ge=1, description="Generation attempt number (1-indexed)")
    overall_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall quality score",
    )
    criteria_scores: CriteriaScores = Field(description="Per-criterion scores")
    strengths: list[str] = Field(
        default_factory=list,
        description="Image strengths",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Areas for improvement",
    )
    missing_elements: list[str] = Field(
        default_factory=list,
        description="Missing required elements",
    )
    verdict: EvaluationVerdict = Field(description="Evaluation verdict")
    refinement_suggestions: list[str] = Field(
        default_factory=list,
        description="Specific prompt improvements",
    )

    @classmethod
    def from_evaluation_response(
        cls,
        image_id: int,
        iteration: int,
        response: dict[str, Any],
        pass_threshold: float = 0.85,
    ) -> "EvaluationResult":
        """Create EvaluationResult from Claude's JSON response.

        Args:
            image_id: Which image this evaluates.
            iteration: Which attempt this evaluates.
            response: Parsed JSON response from Claude.
            pass_threshold: Threshold for PASS verdict.

        Returns:
            Validated EvaluationResult instance.
        """
        overall_score = float(response.get("overall_score", 0.0))
        criteria = response.get("criteria_scores", {})

        return cls(
            image_id=image_id,
            iteration=iteration,
            overall_score=overall_score,
            criteria_scores=CriteriaScores.from_dict(criteria),
            strengths=response.get("strengths", []),
            weaknesses=response.get("weaknesses", []),
            missing_elements=response.get("missing_elements", []),
            verdict=EvaluationVerdict.from_score(overall_score, pass_threshold),
            refinement_suggestions=response.get("refinement_suggestions", []),
        )

    @classmethod
    def from_score(
        cls,
        image_id: int,
        iteration: int,
        overall_score: float,
        pass_threshold: float = 0.85,
        **kwargs: Any,
    ) -> "EvaluationResult":
        """Create an EvaluationResult with automatic verdict determination.

        Args:
            image_id: Which image this evaluates.
            iteration: Which attempt this evaluates.
            overall_score: The overall quality score.
            pass_threshold: Score >= this is PASS (default 0.85).
            **kwargs: Additional fields for the result.

        Returns:
            EvaluationResult with appropriate verdict.
        """
        verdict = EvaluationVerdict.from_score(overall_score, pass_threshold)

        # Default criteria scores if not provided
        if "criteria_scores" not in kwargs:
            kwargs["criteria_scores"] = CriteriaScores(
                concept_clarity=overall_score,
                visual_appeal=overall_score,
                audience_appropriateness=overall_score,
                flow_continuity=overall_score,
            )

        return cls(
            image_id=image_id,
            iteration=iteration,
            overall_score=overall_score,
            verdict=verdict,
            **kwargs,
        )


# =============================================================================
# Image Result Models (Tracking Generation Progress)
# =============================================================================


class ImageAttempt(BaseModel):
    """Record of a single image generation attempt.

    Attributes:
        attempt_number: Which attempt this is (1-indexed).
        prompt_version: Which version of the prompt was used.
        image_path: Path to the generated image file.
        evaluation: Evaluation result for this attempt.
        duration_seconds: Time taken to generate.
        timestamp: When this attempt was made.
    """

    attempt_number: int = Field(ge=1, description="Attempt number (1-indexed)")
    prompt_version: int = Field(ge=1, description="Prompt version used")
    image_path: str = Field(description="Path to generated image")
    evaluation: EvaluationResult | None = Field(
        default=None,
        description="Evaluation result",
    )
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Generation time")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When attempt was made",
    )


class ImageResult(BaseModel):
    """Complete tracking for a single image through all attempts.

    Attributes:
        image_number: Position in the image sequence (1-indexed).
        title: Image title.
        attempts: All generation attempts.
        final_attempt: Which attempt was selected as final.
        final_score: Score of the final selected image.
        final_path: Path to the final image.
        status: Current status (pending, generating, complete, failed).
    """

    image_number: int = Field(ge=1, description="Position in sequence")
    title: str = Field(description="Image title")
    attempts: list[ImageAttempt] = Field(
        default_factory=list,
        description="All attempts",
    )
    final_attempt: int | None = Field(
        default=None,
        description="Selected final attempt number",
    )
    final_score: float | None = Field(default=None, ge=0.0, le=1.0, description="Final image score")
    final_path: str | None = Field(default=None, description="Final image path")
    status: Literal["pending", "generating", "complete", "failed"] = Field(
        default="pending",
        description="Current generation status",
    )

    @property
    def total_attempts(self) -> int:
        """Get the total number of attempts."""
        return len(self.attempts)

    @property
    def passed(self) -> bool:
        """Check if any attempt passed evaluation."""
        return any(
            a.evaluation and a.evaluation.verdict == EvaluationVerdict.PASS
            for a in self.attempts
        )

    @property
    def best_attempt(self) -> ImageAttempt | None:
        """Get the attempt with the highest score."""
        if not self.attempts:
            return None
        scored = [a for a in self.attempts if a.evaluation is not None]
        if not scored:
            return self.attempts[-1] if self.attempts else None
        return max(scored, key=lambda a: a.evaluation.overall_score if a.evaluation else 0.0)

    def add_attempt(
        self,
        image_path: str,
        prompt_version: int,
        evaluation: EvaluationResult | None = None,
        duration_seconds: float = 0.0,
    ) -> ImageAttempt:
        """Add a new attempt record.

        Args:
            image_path: Path to the generated image.
            prompt_version: Which prompt version was used.
            evaluation: Optional evaluation result.
            duration_seconds: Time taken to generate.

        Returns:
            The created ImageAttempt.
        """
        attempt = ImageAttempt(
            attempt_number=len(self.attempts) + 1,
            prompt_version=prompt_version,
            image_path=image_path,
            evaluation=evaluation,
            duration_seconds=duration_seconds,
        )
        self.attempts.append(attempt)
        return attempt

    def select_best(self) -> None:
        """Select the best attempt as final based on scores."""
        if not self.attempts:
            return

        best_attempt = None
        best_score = -1.0

        for attempt in self.attempts:
            if attempt.evaluation and attempt.evaluation.overall_score > best_score:
                best_score = attempt.evaluation.overall_score
                best_attempt = attempt

        if best_attempt:
            self.final_attempt = best_attempt.attempt_number
            self.final_score = best_score
            self.final_path = best_attempt.image_path

    def finalize(self, attempt_number: int | None = None) -> None:
        """Mark generation complete with the selected final attempt.

        Args:
            attempt_number: Which attempt to use as final (None = best scoring).
        """
        if attempt_number is None:
            best = self.best_attempt
            if best:
                attempt_number = best.attempt_number

        if attempt_number is not None:
            for attempt in self.attempts:
                if attempt.attempt_number == attempt_number:
                    self.final_attempt = attempt_number
                    self.final_path = attempt.image_path
                    if attempt.evaluation:
                        self.final_score = attempt.evaluation.overall_score
                    self.status = "complete"
                    return

        # If no valid attempt found, mark as failed
        self.status = "failed"


# =============================================================================
# Generation Metadata Model (Phase 8 - Output)
# Matches the metadata.json schema from §8 exactly
# =============================================================================


class InputMetadata(BaseModel):
    """Metadata about the input content.

    Matches §8 input schema.

    Attributes:
        type: Input type (text, file, url).
        path: Original path or URL if applicable.
        word_count: Word count of the content.
        content_hash: SHA-256 hash for caching (format: sha256:...).
    """

    type: Literal["text", "file", "url"] = Field(description="Input type")
    path: str | None = Field(default=None, description="Source path or URL")
    word_count: int = Field(default=0, ge=0, description="Word count")
    content_hash: str = Field(description="SHA-256 content hash (sha256:...)")


class ConfigMetadata(BaseModel):
    """Configuration used for generation.

    Matches §8 config schema.

    Attributes:
        max_iterations: Maximum refinement attempts per image.
        aspect_ratio: Image aspect ratio used.
        resolution: Resolution setting used.
        style: Style name or path used.
        concurrency: Concurrent generation limit.
        pass_threshold: Score threshold for passing.
    """

    max_iterations: int = Field(description="Maximum refinement attempts")
    aspect_ratio: str = Field(description="Image aspect ratio")
    resolution: str = Field(description="Resolution setting")
    style: str = Field(description="Style name or path")
    concurrency: int = Field(description="Concurrent generation limit")
    pass_threshold: float = Field(description="Score threshold for passing")


class CacheMetadata(BaseModel):
    """Metadata about cached analysis.

    Matches §8 cache schema.

    Attributes:
        concepts_cached: Whether concept analysis was cached.
        cache_path: Path to the cache file.
    """

    concepts_cached: bool = Field(default=False, description="Was analysis cached")
    cache_path: str | None = Field(default=None, description="Cache file path")


class ResultsMetadata(BaseModel):
    """Summary of generation results.

    Matches §8 results schema.

    Attributes:
        images_planned: Number of images planned.
        images_generated: Number successfully generated.
        total_attempts: Total generation attempts across all images.
        total_api_calls: Total API calls made.
        estimated_cost: Estimated cost string (e.g., "$0.70").
    """

    images_planned: int = Field(default=0, ge=0, description="Images planned")
    images_generated: int = Field(default=0, ge=0, description="Images generated")
    total_attempts: int = Field(default=0, ge=0, description="Total attempts")
    total_api_calls: int = Field(default=0, ge=0, description="API calls made")
    estimated_cost: str = Field(default="$0.00", description="Estimated cost")


class ImageMetadataEntry(BaseModel):
    """Metadata for a single generated image.

    Matches §8 images array entries.

    Attributes:
        image_number: Position in sequence.
        final_attempt: Which attempt was selected.
        total_attempts: Total attempts for this image.
        final_score: Final image score.
        final_path: Path to final image.
    """

    image_number: int = Field(ge=1, description="Position in sequence")
    final_attempt: int = Field(ge=1, description="Selected attempt number")
    total_attempts: int = Field(ge=1, description="Total attempts for this image")
    final_score: float = Field(ge=0.0, le=1.0, description="Final image score")
    final_path: str = Field(description="Relative path to final image")


class GenerationMetadata(BaseModel):
    """Full metadata for a generation session.

    Matches the metadata.json schema from §8 exactly.

    Attributes:
        generation_id: Unique identifier for this generation (UUID).
        timestamp: When generation started (ISO 8601 format).
        input: Input content metadata.
        config: Configuration used for generation.
        cache: Cache metadata.
        results: Summary of results.
        images: Per-image results.
    """

    generation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique generation ID",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Generation start time (ISO 8601)",
    )
    input: InputMetadata = Field(description="Input metadata")
    config: ConfigMetadata = Field(description="Config used")
    cache: CacheMetadata = Field(
        default_factory=CacheMetadata,
        description="Cache metadata",
    )
    results: ResultsMetadata = Field(
        default_factory=ResultsMetadata,
        description="Results summary",
    )
    images: list[ImageMetadataEntry] = Field(
        default_factory=list,
        description="Per-image results",
    )

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dictionary.

        Uses model_dump with mode='json' for proper serialization
        of datetime and other complex types.

        Returns:
            JSON-serializable dictionary.
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_generation_session(
        cls,
        input_type: Literal["text", "file", "url"],
        input_path: str | None,
        word_count: int,
        content_hash: str,
        config: dict[str, Any],
        concepts_cached: bool,
        cache_path: str | None,
        image_results: list[ImageResult],
        total_api_calls: int,
        estimated_cost: str,
    ) -> "GenerationMetadata":
        """Create metadata from a completed generation session.

        Args:
            input_type: Type of input (text, file, url).
            input_path: Path or URL if applicable.
            word_count: Input word count.
            content_hash: SHA-256 hash of content.
            config: Generation configuration dict.
            concepts_cached: Whether concepts were cached.
            cache_path: Path to cache file.
            image_results: List of ImageResult from generation.
            total_api_calls: Total API calls made.
            estimated_cost: Estimated cost string.

        Returns:
            Populated GenerationMetadata instance.
        """
        # Build image entries from results
        image_entries = []
        for result in image_results:
            if result.status == "complete" and result.final_attempt is not None:
                image_entries.append(
                    ImageMetadataEntry(
                        image_number=result.image_number,
                        final_attempt=result.final_attempt,
                        total_attempts=result.total_attempts,
                        final_score=result.final_score or 0.0,
                        final_path=result.final_path or "",
                    )
                )

        return cls(
            input=InputMetadata(
                type=input_type,
                path=input_path,
                word_count=word_count,
                content_hash=content_hash,
            ),
            config=ConfigMetadata(
                max_iterations=config.get("max_iterations", 5),
                aspect_ratio=config.get("aspect_ratio", "16:9"),
                resolution=config.get("resolution", "high"),
                style=config.get("style", "professional-clean"),
                concurrency=config.get("concurrency", 3),
                pass_threshold=config.get("pass_threshold", 0.85),
            ),
            cache=CacheMetadata(
                concepts_cached=concepts_cached,
                cache_path=cache_path,
            ),
            results=ResultsMetadata(
                images_planned=len(image_results),
                images_generated=len([r for r in image_results if r.status == "complete"]),
                total_attempts=sum(r.total_attempts for r in image_results),
                total_api_calls=total_api_calls,
                estimated_cost=estimated_cost,
            ),
            images=image_entries,
        )
