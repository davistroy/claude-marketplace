"""Pytest configuration and fixtures for visual-explainer tests."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from visual_explainer.config import (
    AspectRatio,
    GenerationConfig,
    InternalConfig,
    PromptRecipe,
    Resolution,
    StyleConfig,
)
from visual_explainer.models import (
    Complexity,
    Concept,
    ConceptAnalysis,
    CriteriaScores,
    EvaluationResult,
    EvaluationVerdict,
    FlowConnection,
    ImagePrompt,
    ImageResult,
    LogicalFlowStep,
    PromptDetails,
    RelationshipType,
    VisualPotential,
)

# =============================================================================
# Pytest Markers
# =============================================================================


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


# =============================================================================
# Test Data: Sample Image Bytes
# =============================================================================

# Minimal valid JPEG header (1x1 pixel red image) - 125 bytes
MINIMAL_JPEG_BYTES = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYI"
    "DAoMCwsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/wAALCAABAAEBAREA"
    "/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AVN//2Q=="
)


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Return a minimal valid JPEG image for testing."""
    return MINIMAL_JPEG_BYTES


@pytest.fixture
def sample_image_b64() -> str:
    """Return base64-encoded minimal JPEG image."""
    return base64.b64encode(MINIMAL_JPEG_BYTES).decode("utf-8")


# =============================================================================
# Test Data: Configuration Fixtures
# =============================================================================


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory for tests."""
    cache_dir = tmp_path / ".cache" / "visual-explainer"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def sample_generation_config(temp_output_dir: Path) -> GenerationConfig:
    """Create a sample GenerationConfig for testing."""
    return GenerationConfig(
        input_source="Test content about machine learning concepts.",
        style="professional-clean",
        output_dir=temp_output_dir,
        max_iterations=3,
        pass_threshold=0.85,
        resolution=Resolution.HIGH,
        aspect_ratio=AspectRatio.LANDSCAPE_16_9,
        image_count=2,
        no_cache=True,
        dry_run=False,
        concurrency=2,
    )


@pytest.fixture
def sample_internal_config(temp_cache_dir: Path) -> InternalConfig:
    """Create a sample InternalConfig for testing."""
    return InternalConfig(
        cache_dir=temp_cache_dir,
        gemini_timeout_seconds=60.0,  # Shorter for tests
        claude_timeout_seconds=30.0,
        gemini_model="imagen-3.0-generate-002",
        claude_model="claude-sonnet-4-20250514",
        negative_prompt="no text, no words, no labels",
    )


@pytest.fixture
def sample_style_config() -> StyleConfig:
    """Create a sample StyleConfig for testing."""
    return StyleConfig(
        SchemaVersion="1.2",
        StyleName="Test_Style",
        StyleIntent="Clean test style",
        PromptRecipe=PromptRecipe(
            StylePrefix="Professional illustration",
            CoreStylePrompt="clean lines, modern design",
            ColorConstraintPrompt="blue and gray tones",
            TextEnforcementPrompt="no text or labels",
            NegativePrompt="cluttered, messy",
            QualityChecklist=["Clear", "Professional", "Clean"],
        ),
    )


# =============================================================================
# Test Data: Model Fixtures
# =============================================================================


@pytest.fixture
def sample_concepts() -> list[Concept]:
    """Create sample concepts for testing."""
    return [
        Concept(
            id=1,
            name="Neural Networks",
            description="Computational systems inspired by biological neural networks",
            relationships=["concept_id:2", "concept_id:3"],
            complexity=Complexity.MODERATE,
            visual_potential=VisualPotential.HIGH,
        ),
        Concept(
            id=2,
            name="Training Data",
            description="Data used to train machine learning models",
            relationships=["concept_id:1"],
            complexity=Complexity.SIMPLE,
            visual_potential=VisualPotential.MEDIUM,
        ),
        Concept(
            id=3,
            name="Model Output",
            description="Predictions or classifications from trained models",
            relationships=["concept_id:1"],
            complexity=Complexity.SIMPLE,
            visual_potential=VisualPotential.HIGH,
        ),
    ]


@pytest.fixture
def sample_logical_flow() -> list[LogicalFlowStep]:
    """Create sample logical flow for testing."""
    return [
        LogicalFlowStep(
            from_concept=1,
            to_concept=2,
            relationship=RelationshipType.DEPENDS_ON,
        ),
        LogicalFlowStep(
            from_concept=1,
            to_concept=3,
            relationship=RelationshipType.LEADS_TO,
        ),
    ]


@pytest.fixture
def sample_concept_analysis(
    sample_concepts: list[Concept],
    sample_logical_flow: list[LogicalFlowStep],
) -> ConceptAnalysis:
    """Create a sample ConceptAnalysis for testing."""
    return ConceptAnalysis(
        title="Introduction to Machine Learning",
        summary="An overview of machine learning concepts including neural networks, training, and predictions.",
        target_audience="Technical professionals",
        concepts=sample_concepts,
        logical_flow=sample_logical_flow,
        recommended_image_count=2,
        reasoning="Two images can effectively cover the main concepts.",
        content_hash="sha256:abc123def456",
        word_count=500,
    )


@pytest.fixture
def sample_image_prompt() -> ImagePrompt:
    """Create a sample ImagePrompt for testing."""
    return ImagePrompt(
        image_number=1,
        image_title="Neural Network Architecture",
        concepts_covered=[1, 2],
        visual_intent="Show the structure of a neural network with data flowing through layers",
        prompt=PromptDetails(
            main_prompt="A professional illustration showing interconnected nodes in a neural network, with data flowing from input to output layers",
            style_guidance="Clean, modern technical illustration",
            color_palette="Blue and gray tones",
            composition="Left to right flow, centered network",
            avoid="No text, no labels, no cluttered elements",
        ),
        success_criteria=[
            "Clear visualization of neural network structure",
            "Data flow is evident",
            "Professional appearance",
        ],
        flow_connection=FlowConnection(
            previous=None,
            next_image=2,
            transition_intent="Sets foundation for understanding model training",
        ),
    )


@pytest.fixture
def sample_evaluation_result() -> EvaluationResult:
    """Create a sample EvaluationResult for testing."""
    return EvaluationResult(
        image_id=1,
        iteration=1,
        overall_score=0.75,
        criteria_scores=CriteriaScores(
            concept_clarity=0.80,
            visual_appeal=0.70,
            audience_appropriateness=0.75,
            flow_continuity=0.75,
        ),
        strengths=["Clear structure", "Good color usage"],
        weaknesses=["Could be more detailed", "Flow not immediately obvious"],
        missing_elements=["Connection indicators"],
        verdict=EvaluationVerdict.NEEDS_REFINEMENT,
        refinement_suggestions=[
            "Add more visual connections between nodes",
            "Increase contrast for data flow visualization",
        ],
    )


@pytest.fixture
def sample_passing_evaluation() -> EvaluationResult:
    """Create a passing EvaluationResult for testing."""
    return EvaluationResult(
        image_id=1,
        iteration=2,
        overall_score=0.90,
        criteria_scores=CriteriaScores(
            concept_clarity=0.92,
            visual_appeal=0.88,
            audience_appropriateness=0.90,
            flow_continuity=0.90,
        ),
        strengths=["Excellent clarity", "Professional appearance", "Clear flow"],
        weaknesses=[],
        missing_elements=[],
        verdict=EvaluationVerdict.PASS,
        refinement_suggestions=[],
    )


@pytest.fixture
def sample_image_result() -> ImageResult:
    """Create a sample ImageResult for testing."""
    result = ImageResult(
        image_number=1,
        title="Neural Network Architecture",
    )
    result.status = "complete"
    result.final_attempt = 2
    result.final_score = 0.90
    result.final_path = "/output/image-01/final.jpg"
    return result


# =============================================================================
# Mock API Response Fixtures
# =============================================================================


@pytest.fixture
def mock_gemini_success_response(sample_image_b64: str) -> dict[str, Any]:
    """Create a mock successful Gemini API response."""
    return {
        "predictions": [
            {
                "bytesBase64Encoded": sample_image_b64,
            }
        ]
    }


@pytest.fixture
def mock_gemini_rate_limited_response() -> tuple[int, dict[str, Any]]:
    """Create a mock rate-limited Gemini API response."""
    return (
        429,
        {
            "error": {
                "code": 429,
                "message": "Resource exhausted. Please try again later.",
            }
        },
    )


@pytest.fixture
def mock_gemini_safety_blocked_response() -> dict[str, Any]:
    """Create a mock safety-blocked Gemini API response."""
    return {
        "predictions": [
            {
                "safetyFilteredReason": "Content blocked by safety filter",
            }
        ]
    }


@pytest.fixture
def mock_claude_concept_analysis_response() -> dict[str, Any]:
    """Create a mock Claude concept analysis response."""
    return {
        "title": "Machine Learning Fundamentals",
        "summary": "An introduction to core machine learning concepts.",
        "target_audience": "Technical professionals",
        "concepts": [
            {
                "id": 1,
                "name": "Neural Networks",
                "description": "Computational models inspired by biological brains",
                "relationships": ["concept_id:2"],
                "complexity": "moderate",
                "visual_potential": "high",
            },
            {
                "id": 2,
                "name": "Training Process",
                "description": "How models learn from data",
                "relationships": ["concept_id:1"],
                "complexity": "moderate",
                "visual_potential": "high",
            },
        ],
        "logical_flow": [
            {"from": 1, "to": 2, "relationship": "leads_to"},
        ],
        "recommended_image_count": 2,
        "reasoning": "Two images to cover main concepts effectively",
    }


@pytest.fixture
def mock_claude_evaluation_response() -> dict[str, Any]:
    """Create a mock Claude evaluation response."""
    return {
        "overall_score": 0.82,
        "criteria_scores": {
            "concept_clarity": 0.85,
            "visual_appeal": 0.80,
            "audience_appropriateness": 0.82,
            "flow_continuity": 0.80,
        },
        "strengths": ["Clear visualization", "Good composition"],
        "weaknesses": ["Could improve contrast"],
        "missing_elements": ["Flow indicators"],
        "refinement_suggestions": ["Add directional arrows"],
    }


@pytest.fixture
def mock_claude_passing_evaluation_response() -> dict[str, Any]:
    """Create a mock Claude passing evaluation response."""
    return {
        "overall_score": 0.90,
        "criteria_scores": {
            "concept_clarity": 0.92,
            "visual_appeal": 0.88,
            "audience_appropriateness": 0.90,
            "flow_continuity": 0.90,
        },
        "strengths": ["Excellent clarity", "Professional", "Clear flow"],
        "weaknesses": [],
        "missing_elements": [],
        "refinement_suggestions": [],
    }


@pytest.fixture
def mock_claude_prompt_generation_response() -> list[dict[str, Any]]:
    """Create a mock Claude prompt generation response."""
    return [
        {
            "image_title": "Neural Network Overview",
            "concepts_covered": [1],
            "visual_intent": "Show the basic structure of a neural network",
            "main_prompt": "Professional illustration of interconnected nodes forming a neural network",
            "style_guidance": "Clean, modern, technical illustration",
            "color_palette": "Blues and grays",
            "composition": "Centered, left-to-right flow",
            "avoid": "Text, labels, clutter",
            "success_criteria": ["Clear nodes", "Visible connections", "Professional look"],
            "transition_intent": "Foundation for next image",
        },
        {
            "image_title": "Training Data Flow",
            "concepts_covered": [2],
            "visual_intent": "Visualize how data flows through training",
            "main_prompt": "Professional illustration showing data transformation through processing stages",
            "style_guidance": "Clean, modern, technical illustration",
            "color_palette": "Blues and grays with accent highlights",
            "composition": "Sequential flow visualization",
            "avoid": "Text, labels, clutter",
            "success_criteria": ["Clear data flow", "Processing stages visible", "Professional"],
            "transition_intent": "Final image in sequence",
        },
    ]


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def mock_env_with_api_keys(monkeypatch):
    """Set up environment with mock API keys."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-api-key")


@pytest.fixture
def mock_env_without_api_keys(monkeypatch):
    """Clear API keys from environment."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


# =============================================================================
# Checkpoint Fixtures
# =============================================================================


@pytest.fixture
def sample_checkpoint_data(
    sample_concept_analysis: ConceptAnalysis,
    temp_output_dir: Path,
) -> dict[str, Any]:
    """Create sample checkpoint data for testing resume functionality."""
    return {
        "generation_id": "test-gen-id-12345",
        "started_at": datetime.now().isoformat(),
        "total_images": 3,
        "config": {
            "max_iterations": 5,
            "pass_threshold": 0.85,
            "aspect_ratio": "16:9",
            "resolution": "high",
            "style": "professional-clean",
            "concurrency": 3,
        },
        "analysis_hash": sample_concept_analysis.content_hash,
        "current_image": 2,
        "current_attempt": 1,
        "completed_images": [1],
        "image_results": {
            "1": {
                "image_number": 1,
                "title": "First Image",
                "final_attempt": 2,
                "final_score": 0.88,
                "final_path": str(temp_output_dir / "image-01" / "final.jpg"),
                "status": "complete",
            }
        },
        "status": "in_progress",
        "topic": "Machine Learning",
        "session_name": "visual-explainer-machine-learning-20260118-120000",
        "saved_at": datetime.now().isoformat(),
    }


@pytest.fixture
def checkpoint_file(
    sample_checkpoint_data: dict[str, Any],
    temp_output_dir: Path,
) -> Path:
    """Create a checkpoint file for testing resume functionality."""
    session_dir = temp_output_dir / sample_checkpoint_data["session_name"]
    session_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = session_dir / "checkpoint.json"
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(sample_checkpoint_data, f, indent=2)

    # Also create the completed image directory
    image_dir = session_dir / "image-01"
    image_dir.mkdir(exist_ok=True)
    (image_dir / "final.jpg").write_bytes(MINIMAL_JPEG_BYTES)

    return checkpoint_path
