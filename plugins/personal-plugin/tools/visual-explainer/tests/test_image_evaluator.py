"""Tests for image_evaluator module.

Tests the ImageEvaluator class including:
- Score parsing and clamping
- Verdict determination (PASS, NEEDS_REFINEMENT, FAIL)
- Evaluation prompt building
- Media type detection
- JSON response parsing (markdown blocks, raw JSON)
- Image resize logic
- Error handling (API errors, parse errors)
- Factory function
"""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from visual_explainer.image_evaluator import (
    CLAUDE_IMAGE_SIZE_LIMIT,
    ImageEvaluationError,
    ImageEvaluator,
    create_evaluator,
    resize_image_for_claude,
)
from visual_explainer.models import EvaluationVerdict

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def evaluator():
    """Create an ImageEvaluator with mocked Anthropic client."""
    with patch("visual_explainer.image_evaluator.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        ev = ImageEvaluator(
            api_key="test-anthropic-key",
            pass_threshold=0.85,
            fail_threshold=0.5,
        )
        # Replace the client with our mock
        ev.client = mock_client
        yield ev


@pytest.fixture
def sample_eval_response_json():
    """A valid evaluation JSON response."""
    return json.dumps(
        {
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
    )


@pytest.fixture
def passing_eval_response_json():
    """A passing evaluation JSON response."""
    return json.dumps(
        {
            "overall_score": 0.92,
            "criteria_scores": {
                "concept_clarity": 0.95,
                "visual_appeal": 0.90,
                "audience_appropriateness": 0.92,
                "flow_continuity": 0.88,
            },
            "strengths": ["Excellent clarity", "Professional"],
            "weaknesses": [],
            "missing_elements": [],
            "refinement_suggestions": [],
        }
    )


# ---------------------------------------------------------------------------
# Verdict Determination Tests
# ---------------------------------------------------------------------------


class TestVerdictDetermination:
    """Tests for _determine_verdict method."""

    def test_pass_at_threshold(self, evaluator):
        """Test exactly at pass threshold yields PASS."""
        assert evaluator._determine_verdict(0.85) == EvaluationVerdict.PASS

    def test_pass_above_threshold(self, evaluator):
        """Test above pass threshold yields PASS."""
        assert evaluator._determine_verdict(0.95) == EvaluationVerdict.PASS

    def test_needs_refinement_at_fail_threshold(self, evaluator):
        """Test exactly at fail threshold yields NEEDS_REFINEMENT."""
        assert evaluator._determine_verdict(0.50) == EvaluationVerdict.NEEDS_REFINEMENT

    def test_needs_refinement_between_thresholds(self, evaluator):
        """Test between thresholds yields NEEDS_REFINEMENT."""
        assert evaluator._determine_verdict(0.70) == EvaluationVerdict.NEEDS_REFINEMENT

    def test_fail_below_threshold(self, evaluator):
        """Test below fail threshold yields FAIL."""
        assert evaluator._determine_verdict(0.30) == EvaluationVerdict.FAIL

    def test_fail_at_zero(self, evaluator):
        """Test zero score yields FAIL."""
        assert evaluator._determine_verdict(0.0) == EvaluationVerdict.FAIL

    def test_pass_at_one(self, evaluator):
        """Test perfect score yields PASS."""
        assert evaluator._determine_verdict(1.0) == EvaluationVerdict.PASS

    def test_custom_thresholds(self):
        """Test custom pass/fail thresholds."""
        with patch("visual_explainer.image_evaluator.anthropic.Anthropic"):
            ev = ImageEvaluator(
                api_key="key",
                pass_threshold=0.70,
                fail_threshold=0.30,
            )
        assert ev._determine_verdict(0.70) == EvaluationVerdict.PASS
        assert ev._determine_verdict(0.50) == EvaluationVerdict.NEEDS_REFINEMENT
        assert ev._determine_verdict(0.20) == EvaluationVerdict.FAIL


# ---------------------------------------------------------------------------
# Score Clamping Tests
# ---------------------------------------------------------------------------


class TestScoreClamping:
    """Tests for _clamp_score method."""

    def test_normal_score(self, evaluator):
        """Test normal score passes through."""
        assert evaluator._clamp_score(0.75) == 0.75

    def test_score_below_zero(self, evaluator):
        """Test negative score clamped to 0."""
        assert evaluator._clamp_score(-0.5) == 0.0

    def test_score_above_one(self, evaluator):
        """Test score above 1 clamped to 1."""
        assert evaluator._clamp_score(1.5) == 1.0

    def test_none_score(self, evaluator):
        """Test None score becomes 0."""
        assert evaluator._clamp_score(None) == 0.0

    def test_string_score(self, evaluator):
        """Test string score that can be converted."""
        assert evaluator._clamp_score("0.8") == 0.8

    def test_invalid_string_score(self, evaluator):
        """Test non-numeric string returns 0."""
        assert evaluator._clamp_score("invalid") == 0.0

    def test_zero_score(self, evaluator):
        """Test zero score stays zero."""
        assert evaluator._clamp_score(0.0) == 0.0

    def test_one_score(self, evaluator):
        """Test 1.0 score stays 1.0."""
        assert evaluator._clamp_score(1.0) == 1.0


# ---------------------------------------------------------------------------
# Media Type Detection Tests
# ---------------------------------------------------------------------------


class TestMediaTypeDetection:
    """Tests for _detect_media_type method."""

    def test_jpeg_magic_bytes(self, evaluator, sample_image_bytes):
        """Test JPEG detection from magic bytes."""
        media_type = evaluator._detect_media_type(sample_image_bytes)
        assert media_type == "image/jpeg"

    def test_png_magic_bytes(self, evaluator):
        """Test PNG detection from magic bytes."""
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
        media_type = evaluator._detect_media_type(png_header)
        assert media_type == "image/png"

    def test_gif_magic_bytes(self, evaluator):
        """Test GIF detection from magic bytes."""
        gif_header = b"GIF89a" + b"\x00" * 20
        media_type = evaluator._detect_media_type(gif_header)
        assert media_type == "image/gif"

    def test_webp_magic_bytes(self, evaluator):
        """Test WebP detection from magic bytes."""
        webp_header = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20
        media_type = evaluator._detect_media_type(webp_header)
        assert media_type == "image/webp"

    def test_unknown_defaults_to_jpeg(self, evaluator):
        """Test unknown format defaults to JPEG."""
        media_type = evaluator._detect_media_type(b"\x00\x00\x00\x00" * 10)
        assert media_type == "image/jpeg"


# ---------------------------------------------------------------------------
# Response Parsing Tests
# ---------------------------------------------------------------------------


class TestResponseParsing:
    """Tests for _parse_evaluation_response method."""

    def test_parse_raw_json(self, evaluator, sample_eval_response_json):
        """Test parsing raw JSON response."""
        result = evaluator._parse_evaluation_response(sample_eval_response_json)
        assert result["overall_score"] == 0.82

    def test_parse_json_in_markdown_block(self, evaluator, sample_eval_response_json):
        """Test parsing JSON wrapped in markdown code block."""
        text = f"```json\n{sample_eval_response_json}\n```"
        result = evaluator._parse_evaluation_response(text)
        assert result["overall_score"] == 0.82

    def test_parse_json_in_generic_code_block(self, evaluator, sample_eval_response_json):
        """Test parsing JSON in generic code block (no json tag)."""
        text = f"```\n{sample_eval_response_json}\n```"
        result = evaluator._parse_evaluation_response(text)
        assert result["overall_score"] == 0.82

    def test_parse_json_with_surrounding_text(self, evaluator, sample_eval_response_json):
        """Test parsing JSON with surrounding text."""
        text = f"Here is my evaluation:\n{sample_eval_response_json}\n\nDone!"
        result = evaluator._parse_evaluation_response(text)
        assert result["overall_score"] == 0.82

    def test_parse_invalid_json_raises(self, evaluator):
        """Test that invalid JSON raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            evaluator._parse_evaluation_response("this is not json")


# ---------------------------------------------------------------------------
# Build Evaluation Result Tests
# ---------------------------------------------------------------------------


class TestBuildEvaluationResult:
    """Tests for _build_evaluation_result method."""

    def test_build_with_full_data(self, evaluator):
        """Test building result from complete evaluation data."""
        data = {
            "overall_score": 0.82,
            "criteria_scores": {
                "concept_clarity": 0.85,
                "visual_appeal": 0.80,
                "audience_appropriateness": 0.82,
                "flow_continuity": 0.80,
            },
            "strengths": ["Good"],
            "weaknesses": ["Needs work"],
            "missing_elements": ["Label"],
            "refinement_suggestions": ["Add label"],
        }
        result = evaluator._build_evaluation_result(1, 1, data)

        assert result.image_id == 1
        assert result.iteration == 1
        assert result.overall_score == 0.82
        assert result.verdict == EvaluationVerdict.NEEDS_REFINEMENT
        assert result.criteria_scores.concept_clarity == 0.85
        assert len(result.strengths) == 1
        assert len(result.refinement_suggestions) == 1

    def test_build_with_missing_criteria(self, evaluator):
        """Test building result when criteria_scores is missing."""
        data = {"overall_score": 0.90}
        result = evaluator._build_evaluation_result(1, 1, data)

        assert result.overall_score == 0.90
        # Should use overall_score as default for each criterion
        assert result.criteria_scores.concept_clarity == 0.90

    def test_build_with_out_of_range_score(self, evaluator):
        """Test score clamping in build result."""
        data = {"overall_score": 1.5}
        result = evaluator._build_evaluation_result(1, 1, data)
        assert result.overall_score == 1.0

    def test_build_converts_string_lists(self, evaluator):
        """Test that non-list strengths/weaknesses are converted to lists."""
        data = {
            "overall_score": 0.80,
            "strengths": "A single strength",
            "weaknesses": "A single weakness",
            "missing_elements": None,
            "refinement_suggestions": "A suggestion",
        }
        result = evaluator._build_evaluation_result(1, 1, data)

        assert isinstance(result.strengths, list)
        assert result.strengths == ["A single strength"]
        assert isinstance(result.weaknesses, list)
        assert result.weaknesses == ["A single weakness"]
        assert isinstance(result.missing_elements, list)
        assert result.missing_elements == []
        assert isinstance(result.refinement_suggestions, list)


# ---------------------------------------------------------------------------
# Evaluation Prompt Tests
# ---------------------------------------------------------------------------


class TestBuildEvaluationPrompt:
    """Tests for _build_evaluation_prompt method."""

    def test_prompt_contains_intent(self, evaluator):
        """Test prompt includes the visual intent."""
        prompt = evaluator._build_evaluation_prompt(
            intent="Show neural network",
            criteria=["Clear nodes"],
            context={},
        )
        assert "Show neural network" in prompt

    def test_prompt_contains_criteria(self, evaluator):
        """Test prompt includes success criteria."""
        prompt = evaluator._build_evaluation_prompt(
            intent="test",
            criteria=["Criterion 1", "Criterion 2"],
            context={},
        )
        assert "Criterion 1" in prompt
        assert "Criterion 2" in prompt

    def test_prompt_contains_context(self, evaluator):
        """Test prompt includes context values."""
        prompt = evaluator._build_evaluation_prompt(
            intent="test",
            criteria=["test"],
            context={
                "audience": "engineers",
                "image_number": 2,
                "total_images": 5,
                "style": "professional-clean",
            },
        )
        assert "engineers" in prompt
        assert "2 of 5" in prompt
        assert "professional-clean" in prompt

    def test_prompt_includes_previous_summary(self, evaluator):
        """Test prompt includes previous image summary when provided."""
        prompt = evaluator._build_evaluation_prompt(
            intent="test",
            criteria=["test"],
            context={"previous_image_summary": "Previous showed data flow"},
        )
        assert "Previous showed data flow" in prompt

    def test_prompt_requests_json(self, evaluator):
        """Test prompt asks for JSON response."""
        prompt = evaluator._build_evaluation_prompt("test", ["test"], {})
        assert "JSON" in prompt


# ---------------------------------------------------------------------------
# Full Evaluation Tests
# ---------------------------------------------------------------------------


class TestEvaluateImage:
    """Tests for the full evaluate_image method."""

    def test_successful_evaluation(self, evaluator, sample_image_bytes, sample_eval_response_json):
        """Test successful image evaluation flow."""
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = sample_eval_response_json
        mock_message.content = [mock_content]
        evaluator.client.messages.create.return_value = mock_message

        result = evaluator.evaluate_image(
            image_bytes=sample_image_bytes,
            intent="Show neural network",
            criteria=["Clear nodes", "Professional"],
            context={"audience": "technical"},
            image_id=1,
            iteration=1,
        )

        assert result.overall_score == 0.82
        assert result.verdict == EvaluationVerdict.NEEDS_REFINEMENT
        assert len(result.strengths) == 2

    def test_passing_evaluation(self, evaluator, sample_image_bytes, passing_eval_response_json):
        """Test evaluation that meets pass threshold."""
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = passing_eval_response_json
        mock_message.content = [mock_content]
        evaluator.client.messages.create.return_value = mock_message

        result = evaluator.evaluate_image(
            image_bytes=sample_image_bytes,
            intent="Show data flow",
            criteria=["Clear flow"],
            context={},
        )

        assert result.verdict == EvaluationVerdict.PASS
        assert result.overall_score >= 0.85

    def test_api_error_raises(self, evaluator, sample_image_bytes):
        """Test API error is wrapped in ImageEvaluationError."""
        import anthropic

        evaluator.client.messages.create.side_effect = anthropic.APIError(
            message="API Error",
            request=MagicMock(),
            body=None,
        )

        with pytest.raises(ImageEvaluationError, match="API error"):
            evaluator.evaluate_image(
                image_bytes=sample_image_bytes,
                intent="test",
                criteria=["test"],
                context={},
            )

    def test_json_parse_error_raises(self, evaluator, sample_image_bytes):
        """Test JSON parse error is wrapped in ImageEvaluationError."""
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "this is not valid json at all"
        mock_message.content = [mock_content]
        evaluator.client.messages.create.return_value = mock_message

        with pytest.raises(ImageEvaluationError, match="parse error"):
            evaluator.evaluate_image(
                image_bytes=sample_image_bytes,
                intent="test",
                criteria=["test"],
                context={},
            )


# ---------------------------------------------------------------------------
# Image Resize Tests
# ---------------------------------------------------------------------------


class TestResizeImageForClaude:
    """Tests for resize_image_for_claude function."""

    def test_small_image_unchanged(self, sample_image_bytes):
        """Test small image is returned unchanged."""
        result = resize_image_for_claude(sample_image_bytes)
        assert result == sample_image_bytes

    def test_large_image_resized(self):
        """Test large image is resized to fit limit."""
        try:
            from PIL import Image

            # Create a large image
            img = Image.new("RGB", (4000, 3000), color="red")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=100)
            large_bytes = buf.getvalue()

            if len(large_bytes) <= CLAUDE_IMAGE_SIZE_LIMIT:
                pytest.skip("Generated image not large enough to trigger resize")

            result = resize_image_for_claude(large_bytes)
            assert len(result) <= CLAUDE_IMAGE_SIZE_LIMIT
        except ImportError:
            pytest.skip("Pillow not available")

    def test_resize_without_pil_raises(self):
        """Test resize raises when PIL is not available and image is too large."""
        large_bytes = b"\xff\xd8" + b"\x00" * (CLAUDE_IMAGE_SIZE_LIMIT + 1000)

        with patch("visual_explainer.image_evaluator.PIL_AVAILABLE", False):
            with pytest.raises(ImageEvaluationError, match="Pillow"):
                resize_image_for_claude(large_bytes)


# ---------------------------------------------------------------------------
# Factory Function Tests
# ---------------------------------------------------------------------------


class TestCreateEvaluator:
    """Tests for create_evaluator factory function."""

    def test_create_with_defaults(self):
        """Test factory creates evaluator with defaults."""
        with patch("visual_explainer.image_evaluator.anthropic.Anthropic"):
            ev = create_evaluator(api_key="test-key")
        assert ev.pass_threshold == 0.85

    def test_create_with_custom_threshold(self):
        """Test factory creates evaluator with custom threshold."""
        with patch("visual_explainer.image_evaluator.anthropic.Anthropic"):
            ev = create_evaluator(api_key="test-key", pass_threshold=0.70)
        assert ev.pass_threshold == 0.70
