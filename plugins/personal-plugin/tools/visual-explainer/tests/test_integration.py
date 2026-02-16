"""Integration tests for visual-explainer pipeline.

These tests verify the full generation pipeline with mocked APIs:
- Full pipeline: input -> concepts -> prompts -> images -> evaluation
- Retry logic with simulated rate limits
- Checkpoint/resume with interrupted generation
- Error recovery (API failures, timeouts)
- Output directory structure verification

Run with: pytest -m integration
Run slow tests with: pytest -m slow
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from visual_explainer.config import (
    AspectRatio,
    GenerationConfig,
    InternalConfig,
    StyleConfig,
)
from visual_explainer.image_evaluator import ImageEvaluator
from visual_explainer.image_generator import (
    GeminiImageGenerator,
    GenerationStatus,
)
from visual_explainer.models import (
    ConceptAnalysis,
    EvaluationResult,
    EvaluationVerdict,
    ImagePrompt,
    ImageResult,
)
from visual_explainer.output import CheckpointState, OutputManager, finalize_output
from visual_explainer.prompt_generator import PromptGenerator

# =============================================================================
# Test Markers
# =============================================================================

pytestmark = [pytest.mark.integration]


# =============================================================================
# Mock Response Builders
# =============================================================================


def create_mock_gemini_response(image_b64: str) -> dict[str, Any]:
    """Create a mock Gemini API success response."""
    return {
        "predictions": [
            {
                "bytesBase64Encoded": image_b64,
            }
        ]
    }


def create_mock_gemini_rate_limit_response() -> httpx.Response:
    """Create a mock Gemini 429 rate limit response."""
    return httpx.Response(
        status_code=429,
        headers={"Retry-After": "5"},
        content=json.dumps(
            {
                "error": {
                    "code": 429,
                    "message": "Rate limit exceeded",
                }
            }
        ).encode(),
    )


def create_mock_gemini_timeout() -> httpx.TimeoutException:
    """Create a mock Gemini timeout exception."""
    return httpx.TimeoutException("Request timed out")


def create_mock_gemini_safety_block() -> dict[str, Any]:
    """Create a mock Gemini safety filter block response."""
    return {
        "predictions": [
            {
                "safetyFilteredReason": "Content blocked by safety filter",
            }
        ]
    }


# =============================================================================
# Integration Test: Full Pipeline
# =============================================================================


class TestFullPipeline:
    """Integration tests for the complete generation pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_success(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        sample_style_config: StyleConfig,
        sample_concept_analysis: ConceptAnalysis,
        sample_image_b64: str,
        mock_claude_prompt_generation_response: list[dict[str, Any]],
        mock_claude_passing_evaluation_response: dict[str, Any],
        temp_output_dir: Path,
    ):
        """Test full pipeline from input to final images with mocked APIs."""
        # Setup mocks
        mock_anthropic_client = MagicMock()

        # Mock concept analysis call
        mock_analysis_response = MagicMock()
        mock_analysis_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "title": sample_concept_analysis.title,
                        "summary": sample_concept_analysis.summary,
                        "target_audience": sample_concept_analysis.target_audience,
                        "concepts": [c.model_dump() for c in sample_concept_analysis.concepts],
                        "logical_flow": [
                            {
                                "from": f.from_concept,
                                "to": f.to_concept,
                                "relationship": f.relationship.value,
                            }
                            for f in sample_concept_analysis.logical_flow
                        ],
                        "recommended_image_count": sample_concept_analysis.recommended_image_count,
                        "reasoning": sample_concept_analysis.reasoning,
                    }
                )
            )
        ]

        # Mock prompt generation call
        mock_prompt_response = MagicMock()
        mock_prompt_response.content = [
            MagicMock(text=json.dumps(mock_claude_prompt_generation_response))
        ]

        # Mock evaluation call
        mock_eval_response = MagicMock()
        mock_eval_response.content = [
            MagicMock(text=json.dumps(mock_claude_passing_evaluation_response))
        ]

        # Set up messages.create to return different responses based on call count
        call_count = [0]

        def mock_create(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_analysis_response
            elif call_count[0] == 2:
                return mock_prompt_response
            else:
                return mock_eval_response

        mock_anthropic_client.messages.create = mock_create

        # Mock Gemini API response
        mock_gemini_response = httpx.Response(
            status_code=200,
            content=json.dumps(create_mock_gemini_response(sample_image_b64)).encode(),
        )

        with patch("anthropic.Anthropic", return_value=mock_anthropic_client):
            with patch(
                "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_gemini_response
            ):
                # Import and run pipeline components
                from visual_explainer.concept_analyzer import analyze_document

                # Step 1: Analyze document
                analysis = await analyze_document(
                    sample_generation_config.input_source,
                    sample_generation_config,
                    sample_internal_config,
                )

                assert analysis.title == sample_concept_analysis.title
                assert len(analysis.concepts) > 0

                # Step 2: Generate prompts
                generator = PromptGenerator(internal_config=sample_internal_config)
                prompts = generator.generate_prompts(
                    analysis,
                    sample_style_config,
                    sample_generation_config,
                )

                assert len(prompts) >= 1
                assert all(isinstance(p, ImagePrompt) for p in prompts)

                # Step 3: Generate image
                image_gen = GeminiImageGenerator(
                    api_key="test-key",
                    internal_config=sample_internal_config,
                )

                with patch.object(image_gen, "_generate_sync") as mock_api:
                    mock_api.return_value = (
                        GenerationStatus.SUCCESS,
                        base64.b64decode(sample_image_b64),
                        None,
                    )

                    result = await image_gen.generate_image(
                        prompt=prompts[0].get_full_prompt(),
                        aspect_ratio=sample_generation_config.aspect_ratio,
                        resolution=sample_generation_config.resolution,
                    )

                    assert result.status == GenerationStatus.SUCCESS
                    assert result.image_data is not None

                # Step 4: Evaluate image
                evaluator = ImageEvaluator()
                eval_result = evaluator.evaluate_image(
                    image_bytes=base64.b64decode(sample_image_b64),
                    intent=prompts[0].visual_intent,
                    criteria=prompts[0].success_criteria,
                    context={"audience": "technical", "image_number": 1, "total_images": 1},
                )

                assert isinstance(eval_result, EvaluationResult)
                assert eval_result.overall_score >= 0.0
                assert eval_result.verdict in [
                    EvaluationVerdict.PASS,
                    EvaluationVerdict.NEEDS_REFINEMENT,
                    EvaluationVerdict.FAIL,
                ]

    @pytest.mark.asyncio
    async def test_pipeline_creates_correct_output_structure(
        self,
        sample_concept_analysis: ConceptAnalysis,
        sample_image_prompt: ImagePrompt,
        sample_image_bytes: bytes,
        temp_output_dir: Path,
    ):
        """Verify the pipeline creates the correct output directory structure."""
        # Create output manager
        output_manager = OutputManager(
            base_dir=temp_output_dir,
            topic=sample_concept_analysis.title,
        )

        await output_manager.initialize()

        # Verify session directory created
        assert output_manager.session_dir.exists()
        assert output_manager.all_images_dir.exists()

        # Save an attempt image
        image_path = await output_manager.save_attempt_image(
            image_number=1,
            attempt_number=1,
            image_bytes=sample_image_bytes,
        )

        assert image_path.exists()
        assert image_path.name == "attempt-01.jpg"

        # Save a prompt
        prompt_path = await output_manager.save_prompt(
            image_number=1,
            version=1,
            prompt=sample_image_prompt,
        )

        assert prompt_path.exists()
        assert prompt_path.name == "prompt-v1.txt"

        # Create final image
        final_path = await output_manager.create_final_image(
            image_number=1,
            best_attempt=1,
        )

        assert final_path.exists()
        assert final_path.name == "final.jpg"

        # Verify directory structure
        image_dir = output_manager.get_image_dir(1)
        assert image_dir.exists()
        assert (image_dir / "attempt-01.jpg").exists()
        assert (image_dir / "prompt-v1.txt").exists()
        assert (image_dir / "final.jpg").exists()


# =============================================================================
# Integration Test: Retry Logic
# =============================================================================


class TestRetryLogic:
    """Integration tests for retry logic with rate limits and failures."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(
        self,
        sample_internal_config: InternalConfig,
        sample_image_b64: str,
    ):
        """Test that rate limits trigger exponential backoff retry."""
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
            max_retries=3,
            base_delay_seconds=0.1,  # Fast for testing
        )

        call_count = [0]

        def mock_api_call(prompt, aspect_ratio, image_size):
            call_count[0] += 1
            if call_count[0] < 3:
                # Return rate limited for first 2 calls
                return (
                    GenerationStatus.RATE_LIMITED,
                    None,
                    "Rate limited. Retry after 1s",
                )
            # Succeed on 3rd call
            return (
                GenerationStatus.SUCCESS,
                base64.b64decode(sample_image_b64),
                None,
            )

        with patch.object(image_gen, "_generate_sync", side_effect=mock_api_call):
            result = await image_gen.generate_image(
                prompt="Test prompt",
                aspect_ratio=AspectRatio.LANDSCAPE_16_9,
            )

            assert result.status == GenerationStatus.SUCCESS
            assert result.image_data is not None
            assert call_count[0] == 3  # Two retries + success

    @pytest.mark.asyncio
    async def test_retry_exhaustion(
        self,
        sample_internal_config: InternalConfig,
    ):
        """Test behavior when all retries are exhausted."""
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
            max_retries=2,
            base_delay_seconds=0.01,  # Fast for testing
        )

        def always_fail(prompt, aspect_ratio, image_size):
            return (
                GenerationStatus.ERROR,
                None,
                "API error",
            )

        with patch.object(image_gen, "_generate_sync", side_effect=always_fail):
            result = await image_gen.generate_image(
                prompt="Test prompt",
                aspect_ratio=AspectRatio.LANDSCAPE_16_9,
            )

            assert result.status == GenerationStatus.ERROR
            assert result.image_data is None
            assert "Failed after" in result.error_message or "API error" in result.error_message

    @pytest.mark.asyncio
    async def test_no_retry_on_safety_block(
        self,
        sample_internal_config: InternalConfig,
    ):
        """Test that safety blocks are not retried."""
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
            max_retries=3,
        )

        call_count = [0]

        def mock_safety_block(prompt, aspect_ratio, image_size):
            call_count[0] += 1
            return (
                GenerationStatus.SAFETY_BLOCKED,
                None,
                "Content blocked by safety filter",
            )

        with patch.object(image_gen, "_generate_sync", side_effect=mock_safety_block):
            result = await image_gen.generate_image(
                prompt="Test prompt",
                aspect_ratio=AspectRatio.LANDSCAPE_16_9,
            )

            assert result.status == GenerationStatus.SAFETY_BLOCKED
            assert call_count[0] == 1  # No retries

    @pytest.mark.asyncio
    async def test_timeout_handling(
        self,
        sample_internal_config: InternalConfig,
        sample_image_b64: str,
    ):
        """Test timeout handling with retry."""
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
            max_retries=2,
            base_delay_seconds=0.01,
        )

        call_count = [0]

        def mock_timeout_then_success(prompt, aspect_ratio, image_size):
            call_count[0] += 1
            if call_count[0] == 1:
                return (
                    GenerationStatus.TIMEOUT,
                    None,
                    "Request timed out",
                )
            return (
                GenerationStatus.SUCCESS,
                base64.b64decode(sample_image_b64),
                None,
            )

        with patch.object(image_gen, "_generate_sync", side_effect=mock_timeout_then_success):
            result = await image_gen.generate_image(
                prompt="Test prompt",
                aspect_ratio=AspectRatio.LANDSCAPE_16_9,
            )

            assert result.status == GenerationStatus.SUCCESS
            assert call_count[0] == 2


# =============================================================================
# Integration Test: Checkpoint and Resume
# =============================================================================


class TestCheckpointResume:
    """Integration tests for checkpoint save/load and resume functionality."""

    @pytest.mark.asyncio
    async def test_checkpoint_save_and_load(
        self,
        sample_generation_config: GenerationConfig,
        temp_output_dir: Path,
    ):
        """Test checkpoint state can be saved and loaded."""
        output_manager = OutputManager(
            base_dir=temp_output_dir,
            topic="Test Checkpoint",
        )
        await output_manager.initialize()

        # Create checkpoint state
        checkpoint = CheckpointState(
            generation_id="test-gen-123",
            started_at=datetime.now().isoformat(),
            total_images=3,
            config=sample_generation_config.to_metadata_dict(),
            analysis_hash="sha256:abc123",
        )

        # Update progress
        checkpoint.update_progress(image_number=1, attempt_number=2)
        checkpoint.mark_image_complete(
            image_number=1,
            result={
                "status": "complete",
                "final_score": 0.88,
                "final_attempt": 2,
            },
        )

        # Save checkpoint
        checkpoint_path = await output_manager.save_checkpoint(checkpoint)
        assert checkpoint_path.exists()

        # Load checkpoint
        loaded = await output_manager.load_checkpoint()
        assert loaded is not None
        assert loaded.generation_id == "test-gen-123"
        assert loaded.total_images == 3
        assert 1 in loaded.completed_images
        # Note: JSON serialization converts int keys to strings
        assert (
            loaded.image_results.get(1, loaded.image_results.get("1", {})).get("final_score")
            == 0.88
        )

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(
        self,
        checkpoint_file: Path,
        sample_checkpoint_data: dict[str, Any],
    ):
        """Test resuming generation from a checkpoint file."""
        # Load checkpoint
        with open(checkpoint_file, encoding="utf-8") as f:
            checkpoint_data = json.load(f)

        # Verify checkpoint data
        assert checkpoint_data["generation_id"] == sample_checkpoint_data["generation_id"]
        assert checkpoint_data["current_image"] == 2
        assert 1 in checkpoint_data["completed_images"]

        # Create checkpoint state from loaded data
        state = CheckpointState.from_dict(checkpoint_data)

        # Verify state
        assert state.is_image_complete(1)
        assert not state.is_image_complete(2)
        assert state.get_next_image() == 2

    @pytest.mark.asyncio
    async def test_checkpoint_on_interruption(
        self,
        sample_concept_analysis: ConceptAnalysis,
        sample_image_prompt: ImagePrompt,
        sample_image_bytes: bytes,
        temp_output_dir: Path,
    ):
        """Test checkpoint is saved when generation is interrupted."""
        output_manager = OutputManager(
            base_dir=temp_output_dir,
            topic="Interruption Test",
        )
        await output_manager.initialize()

        # Simulate partial generation with checkpoint
        checkpoint = CheckpointState(
            generation_id="interrupt-test-123",
            started_at=datetime.now().isoformat(),
            total_images=3,
            config={"max_iterations": 5},
            analysis_hash=sample_concept_analysis.content_hash,
        )

        # Complete first image
        await output_manager.create_image_directory(1)
        await output_manager.save_attempt_image(1, 1, sample_image_bytes)
        checkpoint.mark_image_complete(1, {"status": "complete", "final_score": 0.85})

        # Start second image but "interrupt"
        checkpoint.update_progress(2, 1)
        await output_manager.create_image_directory(2)
        await output_manager.save_attempt_image(2, 1, sample_image_bytes)

        # Save checkpoint
        await output_manager.save_checkpoint(checkpoint)

        # Verify checkpoint preserves state
        loaded = await output_manager.load_checkpoint()
        assert loaded is not None
        assert loaded.current_image == 2
        assert loaded.current_attempt == 1
        assert 1 in loaded.completed_images
        assert 2 not in loaded.completed_images

    @pytest.mark.asyncio
    async def test_checkpoint_deleted_on_completion(
        self,
        temp_output_dir: Path,
    ):
        """Test checkpoint is deleted after successful completion."""
        output_manager = OutputManager(
            base_dir=temp_output_dir,
            topic="Completion Test",
        )
        await output_manager.initialize()

        checkpoint = CheckpointState(
            generation_id="complete-test-123",
            started_at=datetime.now().isoformat(),
            total_images=1,
            config={},
            analysis_hash="test-hash",
        )

        await output_manager.save_checkpoint(checkpoint)
        assert output_manager.checkpoint_path.exists()

        # Delete checkpoint
        await output_manager.delete_checkpoint()
        assert not output_manager.checkpoint_path.exists()


# =============================================================================
# Integration Test: Error Recovery
# =============================================================================


class TestErrorRecovery:
    """Integration tests for error recovery scenarios."""

    @pytest.mark.asyncio
    async def test_api_failure_handling(
        self,
        sample_internal_config: InternalConfig,
    ):
        """Test handling of API failures."""
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
            max_retries=1,
            base_delay_seconds=0.01,
        )

        def mock_error(prompt, aspect_ratio, image_size):
            return (
                GenerationStatus.ERROR,
                None,
                "HTTP 500: Internal Server Error",
            )

        with patch.object(image_gen, "_generate_sync", side_effect=mock_error):
            result = await image_gen.generate_image(
                prompt="Test prompt",
                aspect_ratio=AspectRatio.LANDSCAPE_16_9,
            )

            assert result.status == GenerationStatus.ERROR
            assert "500" in result.error_message or "Internal Server Error" in result.error_message

    @pytest.mark.asyncio
    async def test_partial_batch_failure(
        self,
        sample_internal_config: InternalConfig,
        sample_image_b64: str,
    ):
        """Test batch generation with partial failures."""
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
            max_concurrent=2,
            max_retries=1,
            base_delay_seconds=0.01,
        )

        call_count = [0]

        def mock_partial_failure(prompt, aspect_ratio, image_size):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return (
                    GenerationStatus.ERROR,
                    None,
                    "Simulated failure",
                )
            return (
                GenerationStatus.SUCCESS,
                base64.b64decode(sample_image_b64),
                None,
            )

        with patch.object(image_gen, "_generate_sync", side_effect=mock_partial_failure):
            prompts = [
                (1, "Prompt 1", AspectRatio.LANDSCAPE_16_9, None),
                (2, "Prompt 2", AspectRatio.LANDSCAPE_16_9, None),
                (3, "Prompt 3", AspectRatio.LANDSCAPE_16_9, None),
            ]

            results = await image_gen.generate_batch(prompts)

            # Some should succeed, some fail
            successes = [r for r in results if r.status == GenerationStatus.SUCCESS]
            assert len(successes) >= 1
            # Due to retry logic, we might have different counts
            assert len(results) == 3

    @pytest.mark.asyncio
    async def test_evaluation_error_recovery(
        self,
        sample_image_bytes: bytes,
    ):
        """Test recovery from evaluation errors."""
        mock_anthropic = MagicMock()

        # First call fails, second succeeds
        call_count = [0]

        def mock_create(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("API temporarily unavailable")
            return MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(
                            {
                                "overall_score": 0.85,
                                "criteria_scores": {
                                    "concept_clarity": 0.85,
                                    "visual_appeal": 0.85,
                                    "audience_appropriateness": 0.85,
                                    "flow_continuity": 0.85,
                                },
                                "strengths": ["Good"],
                                "weaknesses": [],
                                "missing_elements": [],
                                "refinement_suggestions": [],
                            }
                        )
                    )
                ]
            )

        mock_anthropic.messages.create = mock_create

        with patch("anthropic.Anthropic", return_value=mock_anthropic):
            evaluator = ImageEvaluator()

            # First evaluation fails
            from visual_explainer.image_evaluator import ImageEvaluationError

            with pytest.raises(ImageEvaluationError):
                evaluator.evaluate_image(
                    image_bytes=sample_image_bytes,
                    intent="Test intent",
                    criteria=["Test criterion"],
                    context={},
                )

            # Second evaluation succeeds
            result = evaluator.evaluate_image(
                image_bytes=sample_image_bytes,
                intent="Test intent",
                criteria=["Test criterion"],
                context={},
            )

            assert result.overall_score == 0.85

    @pytest.mark.asyncio
    async def test_invalid_config_recovery(
        self,
        temp_output_dir: Path,
    ):
        """Test recovery from invalid configuration."""
        # Test that invalid max_iterations is caught
        with pytest.raises(ValueError):
            GenerationConfig(
                input_source="test",
                max_iterations=100,  # Invalid: > 10
            )

        # Test that invalid pass_threshold is caught
        with pytest.raises(ValueError):
            GenerationConfig(
                input_source="test",
                pass_threshold=2.0,  # Invalid: > 1.0
            )

        # Valid config should work
        config = GenerationConfig(
            input_source="test",
            max_iterations=5,
            pass_threshold=0.85,
            output_dir=temp_output_dir,
        )
        assert config.max_iterations == 5


# =============================================================================
# Integration Test: Output Verification
# =============================================================================


class TestOutputVerification:
    """Integration tests for output directory structure verification."""

    @pytest.mark.asyncio
    async def test_complete_output_structure(
        self,
        sample_concept_analysis: ConceptAnalysis,
        sample_image_prompt: ImagePrompt,
        sample_image_bytes: bytes,
        sample_evaluation_result: EvaluationResult,
        temp_output_dir: Path,
    ):
        """Verify complete output directory structure is created correctly."""
        output_manager = OutputManager(
            base_dir=temp_output_dir,
            topic=sample_concept_analysis.title,
        )
        await output_manager.initialize()

        # Simulate full generation for 2 images
        for img_num in range(1, 3):
            # Create image directory
            await output_manager.create_image_directory(img_num)

            # Save attempts
            for attempt in range(1, 3):
                await output_manager.save_attempt_image(img_num, attempt, sample_image_bytes)
                await output_manager.save_prompt(img_num, attempt, sample_image_prompt)
                await output_manager.save_evaluation(img_num, attempt, sample_evaluation_result)

            # Create final
            await output_manager.create_final_image(img_num, best_attempt=2)
            await output_manager.copy_to_all_images(img_num, f"Test Image {img_num}")

        # Verify structure
        session_dir = output_manager.session_dir

        # Root level files would be created
        assert (session_dir / "all-images").exists()

        # Image directories
        for img_num in range(1, 3):
            img_dir = session_dir / f"image-{img_num:02d}"
            assert img_dir.exists()
            assert (img_dir / "attempt-01.jpg").exists()
            assert (img_dir / "attempt-02.jpg").exists()
            assert (img_dir / "prompt-v1.txt").exists()
            assert (img_dir / "prompt-v2.txt").exists()
            assert (img_dir / "evaluation-01.json").exists()
            assert (img_dir / "evaluation-02.json").exists()
            assert (img_dir / "final.jpg").exists()

        # All images directory
        all_images = session_dir / "all-images"
        assert len(list(all_images.glob("*.jpg"))) == 2

    @pytest.mark.asyncio
    async def test_finalize_output(
        self,
        sample_image_bytes: bytes,
        temp_output_dir: Path,
    ):
        """Test finalize_output creates final images correctly."""
        output_manager = OutputManager(
            base_dir=temp_output_dir,
            topic="Finalize Test",
        )
        await output_manager.initialize()

        # Create some attempts
        await output_manager.create_image_directory(1)
        await output_manager.save_attempt_image(1, 1, sample_image_bytes)
        await output_manager.save_attempt_image(1, 2, sample_image_bytes)

        await output_manager.create_image_directory(2)
        await output_manager.save_attempt_image(2, 1, sample_image_bytes)

        # Create image results
        results = [
            ImageResult(image_number=1, title="First Image"),
            ImageResult(image_number=2, title="Second Image"),
        ]
        results[0].status = "complete"
        results[0].final_attempt = 2
        results[0].final_score = 0.90

        results[1].status = "complete"
        results[1].final_attempt = 1
        results[1].final_score = 0.85

        # Finalize
        final_paths = await finalize_output(output_manager, results)

        assert len(final_paths) == 2
        for path in final_paths:
            assert path.exists()

    @pytest.mark.asyncio
    async def test_output_manager_from_checkpoint(
        self,
        checkpoint_file: Path,
    ):
        """Test OutputManager can be restored from checkpoint."""
        output_manager = OutputManager.from_checkpoint(checkpoint_file)

        assert output_manager.topic == "Machine Learning"
        assert output_manager._initialized is True
        assert output_manager.session_dir.exists()


# =============================================================================
# Integration Test: Concurrent Generation
# =============================================================================


class TestConcurrentGeneration:
    """Integration tests for concurrent image generation."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_generation_respects_semaphore(
        self,
        sample_internal_config: InternalConfig,
        sample_image_b64: str,
    ):
        """Test that concurrent generation respects the semaphore limit."""
        max_concurrent = 2
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
            max_concurrent=max_concurrent,
            max_retries=1,
        )

        concurrent_count = [0]
        max_observed_concurrent = [0]

        def mock_slow_api(prompt, aspect_ratio, image_size):
            concurrent_count[0] += 1
            max_observed_concurrent[0] = max(max_observed_concurrent[0], concurrent_count[0])
            import time as _time

            _time.sleep(0.1)  # Simulate API delay (sync — runs in executor)
            concurrent_count[0] -= 1
            return (
                GenerationStatus.SUCCESS,
                base64.b64decode(sample_image_b64),
                None,
            )

        with patch.object(image_gen, "_generate_sync", side_effect=mock_slow_api):
            prompts = [
                (i, f"Prompt {i}", AspectRatio.LANDSCAPE_16_9, None)
                for i in range(1, 6)  # 5 prompts
            ]

            results = await image_gen.generate_batch(prompts)

            assert len(results) == 5
            assert all(r.status == GenerationStatus.SUCCESS for r in results)
            assert max_observed_concurrent[0] <= max_concurrent


# =============================================================================
# Integration Test: Prompt Refinement Loop
# =============================================================================


class TestPromptRefinement:
    """Integration tests for the prompt refinement loop."""

    def test_refinement_strategy_escalation(
        self,
        sample_image_prompt: ImagePrompt,
        sample_evaluation_result: EvaluationResult,
        sample_style_config: StyleConfig,
    ):
        """Test that refinement strategy escalates with attempt number."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "main_prompt": "Refined prompt",
                        "style_guidance": "Refined style",
                        "composition": "Refined composition",
                        "color_palette": "Refined colors",
                        "avoid": "Refined avoid",
                        "success_criteria": ["Refined criteria"],
                        "refinement_reasoning": "Made changes based on feedback",
                    }
                )
            )
        ]
        mock_anthropic.messages.create = MagicMock(return_value=mock_response)

        with patch("anthropic.Anthropic", return_value=mock_anthropic):
            generator = PromptGenerator()

            # Get strategies for different attempts
            strategy_2 = generator._get_refinement_strategy(2, sample_evaluation_result)
            strategy_3 = generator._get_refinement_strategy(3, sample_evaluation_result)
            strategy_4 = generator._get_refinement_strategy(4, sample_evaluation_result)
            strategy_5 = generator._get_refinement_strategy(5, sample_evaluation_result)

            # Verify escalation
            assert strategy_2["name"] == "specific_fixes"
            assert strategy_3["name"] == "strengthen_and_simplify"
            assert strategy_4["name"] == "alternative_metaphor"
            assert strategy_5["name"] == "fundamental_restructure"

    def test_refinement_preserves_metadata(
        self,
        sample_image_prompt: ImagePrompt,
        sample_evaluation_result: EvaluationResult,
        sample_style_config: StyleConfig,
    ):
        """Test that refinement preserves image metadata."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "main_prompt": "Completely new prompt",
                        "style_guidance": "New style",
                        "composition": "New composition",
                        "color_palette": "New colors",
                        "avoid": "New avoid",
                        "success_criteria": ["New criteria"],
                        "refinement_reasoning": "Major changes",
                    }
                )
            )
        ]
        mock_anthropic.messages.create = MagicMock(return_value=mock_response)

        with patch("anthropic.Anthropic", return_value=mock_anthropic):
            generator = PromptGenerator()

            refined = generator.refine_prompt(
                original=sample_image_prompt,
                feedback=sample_evaluation_result,
                attempt=2,
                style=sample_style_config,
            )

            # Metadata should be preserved
            assert refined.image_number == sample_image_prompt.image_number
            assert refined.title == sample_image_prompt.title
            assert refined.concepts_covered == sample_image_prompt.concepts_covered
            assert refined.visual_intent == sample_image_prompt.visual_intent

            # Prompt should be updated
            assert refined.prompt.main_prompt == "Completely new prompt"


# =============================================================================
# Integration Test: End-to-End with Mocked APIs
# =============================================================================


class TestEndToEnd:
    """End-to-end integration tests with fully mocked APIs."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_generation_workflow(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        sample_style_config: StyleConfig,
        sample_concept_analysis: ConceptAnalysis,
        sample_image_prompt: ImagePrompt,
        sample_image_b64: str,
        mock_claude_prompt_generation_response: list[dict[str, Any]],
        mock_claude_passing_evaluation_response: dict[str, Any],
        temp_output_dir: Path,
    ):
        """Test complete workflow from input to final output.

        This test verifies the end-to-end flow by:
        1. Using a pre-built concept analysis (simulating Step 1)
        2. Building prompts directly from the mock response (simulating Step 2)
        3. Mocking image generation (Step 3)
        4. Mocking evaluation (Step 4)
        5. Verifying output structure
        """
        # Create output manager
        output_manager = OutputManager(
            base_dir=temp_output_dir,
            topic=sample_concept_analysis.title,
        )
        await output_manager.initialize()

        # Step 1: Use provided analysis (mocked) — sample_concept_analysis fixture

        # Step 2: Build prompts from mock response directly
        # (avoiding the need to mock the PromptGenerator API call)
        prompts = [sample_image_prompt]  # Use the fixture directly

        # Verify we have prompts to work with
        assert len(prompts) >= 1
        assert all(isinstance(p, ImagePrompt) for p in prompts)

        # Step 3: Generate images with mocked API
        image_gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=sample_internal_config,
        )

        # Mock evaluation responses
        mock_anthropic = MagicMock()
        mock_eval_response = MagicMock()
        mock_eval_response.content = [
            MagicMock(text=json.dumps(mock_claude_passing_evaluation_response))
        ]
        mock_anthropic.messages.create = MagicMock(return_value=mock_eval_response)

        image_results: list[ImageResult] = []

        for prompt in prompts:
            result = ImageResult(
                image_number=prompt.image_number,
                title=prompt.title,
            )
            result.status = "generating"

            # Simulate generation
            with patch.object(image_gen, "_generate_sync") as mock_api:
                mock_api.return_value = (
                    GenerationStatus.SUCCESS,
                    base64.b64decode(sample_image_b64),
                    None,
                )

                gen_result = await image_gen.generate_image(
                    prompt=prompt.get_full_prompt(),
                    aspect_ratio=sample_generation_config.aspect_ratio,
                )

                if gen_result.status == GenerationStatus.SUCCESS:
                    # Save attempt
                    image_path = await output_manager.save_attempt_image(
                        prompt.image_number,
                        1,
                        gen_result.image_data,
                    )

                    # Evaluate with mocked evaluator
                    with patch("anthropic.Anthropic", return_value=mock_anthropic):
                        evaluator = ImageEvaluator()
                        eval_result = evaluator.evaluate_image(
                            image_bytes=gen_result.image_data,
                            intent=prompt.visual_intent,
                            criteria=prompt.success_criteria,
                            context={"audience": "technical"},
                        )

                    result.add_attempt(
                        image_path=str(image_path),
                        prompt_version=1,
                        evaluation=eval_result,
                    )

                    if eval_result.verdict == EvaluationVerdict.PASS:
                        result.status = "complete"
                        result.final_attempt = 1
                        result.final_score = eval_result.overall_score
                        result.final_path = str(image_path)

            image_results.append(result)

        # Verify results
        assert len(image_results) >= 1
        completed = [r for r in image_results if r.status == "complete"]
        assert len(completed) >= 1

        # Create finals
        for result in completed:
            await output_manager.create_final_image(result.image_number, result.final_attempt)
            await output_manager.copy_to_all_images(result.image_number, result.title)

        # Verify output structure
        assert output_manager.session_dir.exists()
        assert output_manager.all_images_dir.exists()

        # Verify images were saved
        image_dir = output_manager.get_image_dir(1)
        assert image_dir.exists()
        assert (image_dir / "attempt-01.jpg").exists()
        assert (image_dir / "final.jpg").exists()

    @pytest.mark.asyncio
    async def test_prompt_generation_mocked(
        self,
        sample_concept_analysis: ConceptAnalysis,
        sample_style_config: StyleConfig,
        sample_generation_config: GenerationConfig,
        mock_claude_prompt_generation_response: list[dict[str, Any]],
    ):
        """Test prompt generation with properly mocked API response."""
        # Create a mock anthropic client that returns the expected response
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_prompt_generation_response))]
        mock_anthropic.messages.create = MagicMock(return_value=mock_response)

        # Patch at the point where the client is created
        with patch("anthropic.Anthropic", return_value=mock_anthropic):
            generator = PromptGenerator()
            prompts = generator.generate_prompts(
                sample_concept_analysis,
                sample_style_config,
                sample_generation_config,
            )

            # Verify prompts were generated
            assert len(prompts) == 2
            assert prompts[0].title == "Neural Network Overview"
            assert prompts[1].title == "Training Data Flow"
            assert prompts[0].image_number == 1
            assert prompts[1].image_number == 2
