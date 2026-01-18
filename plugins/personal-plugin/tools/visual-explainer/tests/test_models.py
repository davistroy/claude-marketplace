"""Tests for models module.

Tests model creation, validation, serialization/deserialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from visual_explainer.models import (
    CacheMetadata,
    Complexity,
    Concept,
    ConceptAnalysis,
    ConfigMetadata,
    CriteriaScores,
    EvaluationResult,
    EvaluationVerdict,
    FlowConnection,
    GenerationMetadata,
    ImageAttempt,
    ImageMetadataEntry,
    ImagePrompt,
    ImageResult,
    InputMetadata,
    LogicalFlowStep,
    PromptDetails,
    RelationshipType,
    ResultsMetadata,
    VisualPotential,
)


class TestEnums:
    """Tests for enum types."""

    def test_complexity_values(self):
        """Test Complexity enum values."""
        assert Complexity.SIMPLE.value == "simple"
        assert Complexity.MODERATE.value == "moderate"
        assert Complexity.COMPLEX.value == "complex"

    def test_visual_potential_values(self):
        """Test VisualPotential enum values."""
        assert VisualPotential.HIGH.value == "high"
        assert VisualPotential.MEDIUM.value == "medium"
        assert VisualPotential.LOW.value == "low"

    def test_relationship_type_values(self):
        """Test RelationshipType enum values."""
        assert RelationshipType.LEADS_TO.value == "leads_to"
        assert RelationshipType.SUPPORTS.value == "supports"
        assert RelationshipType.BUILDS_ON.value == "builds_on"

    def test_evaluation_verdict_values(self):
        """Test EvaluationVerdict enum values."""
        assert EvaluationVerdict.PASS.value == "PASS"
        assert EvaluationVerdict.NEEDS_REFINEMENT.value == "NEEDS_REFINEMENT"
        assert EvaluationVerdict.FAIL.value == "FAIL"

    def test_verdict_from_score_pass(self):
        """Test verdict determination for passing score."""
        assert EvaluationVerdict.from_score(0.90) == EvaluationVerdict.PASS
        assert EvaluationVerdict.from_score(0.85) == EvaluationVerdict.PASS

    def test_verdict_from_score_needs_refinement(self):
        """Test verdict determination for refinement score."""
        assert EvaluationVerdict.from_score(0.70) == EvaluationVerdict.NEEDS_REFINEMENT
        assert EvaluationVerdict.from_score(0.50) == EvaluationVerdict.NEEDS_REFINEMENT
        assert EvaluationVerdict.from_score(0.84) == EvaluationVerdict.NEEDS_REFINEMENT

    def test_verdict_from_score_fail(self):
        """Test verdict determination for failing score."""
        assert EvaluationVerdict.from_score(0.30) == EvaluationVerdict.FAIL
        assert EvaluationVerdict.from_score(0.49) == EvaluationVerdict.FAIL
        assert EvaluationVerdict.from_score(0.0) == EvaluationVerdict.FAIL

    def test_verdict_from_score_custom_threshold(self):
        """Test verdict with custom pass threshold."""
        assert EvaluationVerdict.from_score(0.75, pass_threshold=0.70) == EvaluationVerdict.PASS
        assert EvaluationVerdict.from_score(0.75, pass_threshold=0.80) == EvaluationVerdict.NEEDS_REFINEMENT


class TestConcept:
    """Tests for Concept model."""

    def test_minimal_concept(self):
        """Test creating minimal concept."""
        concept = Concept(
            id=1,
            name="Test Concept",
            description="A test concept",
        )
        assert concept.id == 1
        assert concept.name == "Test Concept"
        assert concept.complexity == Complexity.MODERATE
        assert concept.visual_potential == VisualPotential.MEDIUM
        assert concept.relationships == []

    def test_full_concept(self):
        """Test creating concept with all fields."""
        concept = Concept(
            id=1,
            name="Neural Networks",
            description="Computational systems inspired by biology",
            relationships=["concept_id:2", "concept_id:3"],
            complexity=Complexity.COMPLEX,
            visual_potential=VisualPotential.HIGH,
        )
        assert concept.complexity == Complexity.COMPLEX
        assert len(concept.relationships) == 2

    def test_invalid_id_zero(self):
        """Test that concept ID must be >= 1."""
        with pytest.raises(ValidationError):
            Concept(id=0, name="Test", description="Test")

    def test_invalid_name_empty(self):
        """Test that concept name cannot be empty."""
        with pytest.raises(ValidationError):
            Concept(id=1, name="", description="Test")

    def test_get_related_ids(self):
        """Test extracting related concept IDs."""
        concept = Concept(
            id=1,
            name="Test",
            description="Test",
            relationships=["concept_id:2", "concept_id:3", "invalid"],
        )
        ids = concept.get_related_ids()
        assert ids == [2, 3]


class TestCriteriaScores:
    """Tests for CriteriaScores model."""

    def test_create_scores(self):
        """Test creating criteria scores."""
        scores = CriteriaScores(
            concept_clarity=0.85,
            visual_appeal=0.90,
            audience_appropriateness=0.80,
            flow_continuity=0.75,
        )
        assert scores.concept_clarity == 0.85
        assert scores.visual_appeal == 0.90

    def test_invalid_score_too_high(self):
        """Test that scores cannot exceed 1.0."""
        with pytest.raises(ValidationError):
            CriteriaScores(
                concept_clarity=1.1,
                visual_appeal=0.9,
                audience_appropriateness=0.9,
                flow_continuity=0.9,
            )

    def test_to_dict(self):
        """Test converting scores to dict."""
        scores = CriteriaScores(
            concept_clarity=0.85,
            visual_appeal=0.90,
            audience_appropriateness=0.80,
            flow_continuity=0.75,
        )
        d = scores.to_dict()
        assert d["concept_clarity"] == 0.85
        assert len(d) == 4

    def test_from_dict(self):
        """Test creating from dict."""
        scores = CriteriaScores.from_dict({
            "concept_clarity": 0.85,
            "visual_appeal": 0.90,
            "audience_appropriateness": 0.80,
            "flow_continuity": 0.75,
        })
        assert scores.concept_clarity == 0.85

    def test_from_dict_missing_keys(self):
        """Test creating from dict with missing keys."""
        scores = CriteriaScores.from_dict({
            "concept_clarity": 0.85,
        })
        assert scores.concept_clarity == 0.85
        assert scores.visual_appeal == 0.0


class TestEvaluationResult:
    """Tests for EvaluationResult model."""

    def test_create_result(self):
        """Test creating evaluation result."""
        result = EvaluationResult(
            image_id=1,
            iteration=1,
            overall_score=0.85,
            criteria_scores=CriteriaScores(
                concept_clarity=0.85,
                visual_appeal=0.85,
                audience_appropriateness=0.85,
                flow_continuity=0.85,
            ),
            verdict=EvaluationVerdict.PASS,
        )
        assert result.overall_score == 0.85
        assert result.verdict == EvaluationVerdict.PASS

    def test_from_evaluation_response(self):
        """Test creating from API response."""
        response: dict[str, Any] = {
            "overall_score": 0.75,
            "criteria_scores": {
                "concept_clarity": 0.80,
                "visual_appeal": 0.70,
                "audience_appropriateness": 0.75,
                "flow_continuity": 0.75,
            },
            "strengths": ["Good colors"],
            "weaknesses": ["Needs work"],
            "missing_elements": [],
            "refinement_suggestions": ["Add more detail"],
        }
        result = EvaluationResult.from_evaluation_response(
            image_id=1,
            iteration=1,
            response=response,
        )
        assert result.overall_score == 0.75
        assert result.verdict == EvaluationVerdict.NEEDS_REFINEMENT
        assert len(result.strengths) == 1

    def test_from_score(self):
        """Test creating from score only."""
        result = EvaluationResult.from_score(
            image_id=1,
            iteration=1,
            overall_score=0.90,
        )
        assert result.overall_score == 0.90
        assert result.verdict == EvaluationVerdict.PASS


class TestImageResult:
    """Tests for ImageResult model."""

    def test_create_result(self):
        """Test creating image result."""
        result = ImageResult(
            image_number=1,
            title="Test Image",
        )
        assert result.image_number == 1
        assert result.status == "pending"
        assert result.total_attempts == 0

    def test_add_attempt(self, sample_evaluation_result):
        """Test adding attempt to result."""
        result = ImageResult(image_number=1, title="Test")
        attempt = result.add_attempt(
            image_path="/path/to/image.jpg",
            prompt_version=1,
            evaluation=sample_evaluation_result,
            duration_seconds=30.0,
        )
        assert attempt.attempt_number == 1
        assert result.total_attempts == 1

    def test_best_attempt(self, sample_passing_evaluation, sample_evaluation_result):
        """Test getting best attempt."""
        result = ImageResult(image_number=1, title="Test")
        result.add_attempt("/path/1.jpg", 1, sample_evaluation_result)
        result.add_attempt("/path/2.jpg", 2, sample_passing_evaluation)

        best = result.best_attempt
        assert best is not None
        assert best.attempt_number == 2  # Higher score

    def test_passed_property(self, sample_passing_evaluation):
        """Test passed property."""
        result = ImageResult(image_number=1, title="Test")
        result.add_attempt("/path/1.jpg", 1, sample_passing_evaluation)
        assert result.passed is True

    def test_finalize(self, sample_passing_evaluation):
        """Test finalizing result."""
        result = ImageResult(image_number=1, title="Test")
        result.add_attempt("/path/1.jpg", 1, sample_passing_evaluation)
        result.finalize()

        assert result.status == "complete"
        assert result.final_attempt == 1


class TestGenerationMetadata:
    """Tests for GenerationMetadata model."""

    def test_create_metadata(self):
        """Test creating generation metadata."""
        metadata = GenerationMetadata(
            generation_id="test-123",
            timestamp=datetime.now(),
            input=InputMetadata(
                type="text",
                content_hash="sha256:abc",
                word_count=500,
            ),
            config=ConfigMetadata(
                max_iterations=5,
                aspect_ratio="16:9",
                resolution="high",
                style="professional-clean",
                concurrency=3,
                pass_threshold=0.85,
            ),
        )
        assert metadata.generation_id == "test-123"

    def test_to_json_dict(self):
        """Test JSON serialization."""
        metadata = GenerationMetadata(
            generation_id="test-123",
            input=InputMetadata(
                type="text",
                content_hash="sha256:abc",
            ),
            config=ConfigMetadata(
                max_iterations=5,
                aspect_ratio="16:9",
                resolution="high",
                style="professional-clean",
                concurrency=3,
                pass_threshold=0.85,
            ),
        )
        d = metadata.to_json_dict()
        assert "generation_id" in d
        assert d["input"]["type"] == "text"
