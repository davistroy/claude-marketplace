"""Tests for image_generator module.

Tests the GeminiImageGenerator class including:
- Initialization and configuration
- Successful image generation
- Retry logic with exponential backoff
- Safety filter handling
- Timeout handling
- Rate limit handling
- Concurrent generation (semaphore)
- Progress callbacks
- Cost estimation
- Batch generation
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from visual_explainer.config import AspectRatio, InternalConfig, Resolution
from visual_explainer.image_generator import (
    GeminiImageGenerator,
    GenerationResult,
    GenerationStatus,
    generate_image,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def internal_config(temp_cache_dir):
    """Create InternalConfig for tests with short timeouts."""
    return InternalConfig(
        cache_dir=temp_cache_dir,
        gemini_timeout_seconds=60.0,
        claude_timeout_seconds=30.0,
        gemini_model="imagen-3.0-generate-002",
        claude_model="claude-sonnet-4-20250514",
        negative_prompt="no text, no words",
    )


@pytest.fixture
def generator(mock_env_with_api_keys, internal_config):
    """Create a GeminiImageGenerator with mocked environment."""
    gen = GeminiImageGenerator(
        api_key="test-google-api-key",
        internal_config=internal_config,
        max_concurrent=2,
        max_retries=3,
        base_delay_seconds=0.01,
        max_delay_seconds=0.05,
    )
    return gen


# ---------------------------------------------------------------------------
# Initialization Tests
# ---------------------------------------------------------------------------


class TestGeminiImageGeneratorInit:
    """Tests for GeminiImageGenerator initialization."""

    def test_init_with_explicit_key(self, mock_env_with_api_keys, internal_config):
        """Test init with explicit API key parameter."""
        gen = GeminiImageGenerator(api_key="explicit-key", internal_config=internal_config)
        assert gen.api_key == "explicit-key"

    def test_init_from_env(self, monkeypatch, internal_config):
        """Test init reads GOOGLE_API_KEY from environment."""
        monkeypatch.setenv("GOOGLE_API_KEY", "env-key-value")
        gen = GeminiImageGenerator(internal_config=internal_config)
        assert gen.api_key == "env-key-value"

    def test_init_no_key_raises(self, mock_env_without_api_keys):
        """Test init raises ValueError when no key is available."""
        with pytest.raises(ValueError, match="Google API key required"):
            GeminiImageGenerator()

    def test_init_default_config(self, mock_env_with_api_keys):
        """Test init creates default InternalConfig when none provided."""
        gen = GeminiImageGenerator(api_key="test-key")
        assert gen.internal_config is not None
        assert gen.max_retries == 3

    def test_init_custom_retries(self, mock_env_with_api_keys, internal_config):
        """Test custom retry configuration."""
        gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=internal_config,
            max_retries=5,
            base_delay_seconds=2.0,
            max_delay_seconds=30.0,
        )
        assert gen.max_retries == 5
        assert gen.base_delay_seconds == 2.0
        assert gen.max_delay_seconds == 30.0

    def test_init_timeout_calculation(self, mock_env_with_api_keys, internal_config):
        """Test timeout is converted from seconds to milliseconds."""
        gen = GeminiImageGenerator(api_key="test-key", internal_config=internal_config)
        assert gen.timeout_ms == int(internal_config.gemini_timeout_seconds * 1000)

    def test_init_semaphore(self, mock_env_with_api_keys, internal_config):
        """Test semaphore is created with correct concurrency."""
        gen = GeminiImageGenerator(
            api_key="test-key",
            internal_config=internal_config,
            max_concurrent=5,
        )
        assert gen.semaphore._value == 5


# ---------------------------------------------------------------------------
# API Call Count Tests
# ---------------------------------------------------------------------------


class TestApiCallTracking:
    """Tests for API call count tracking."""

    def test_initial_count_zero(self, generator):
        """Test API call count starts at zero."""
        assert generator.api_call_count == 0

    def test_reset_api_call_count(self, generator):
        """Test resetting API call counter."""
        generator._api_call_count = 5
        generator.reset_api_call_count()
        assert generator.api_call_count == 0


# ---------------------------------------------------------------------------
# Backoff Calculation Tests
# ---------------------------------------------------------------------------


class TestBackoffCalculation:
    """Tests for exponential backoff delay calculation."""

    def test_first_attempt_base_delay(self, generator):
        """Test first attempt delay is close to base_delay."""
        delay = generator._calculate_backoff_delay(1)
        # base = 0.01, with jitter (10-30%) should be 0.011 to 0.013
        assert delay >= generator.base_delay_seconds
        assert delay <= generator.base_delay_seconds * 1.5

    def test_delay_increases_exponentially(self, generator):
        """Test delay increases with each attempt."""
        delay1 = generator._calculate_backoff_delay(1)
        delay2 = generator._calculate_backoff_delay(2)
        assert delay2 > delay1

    def test_delay_capped_at_max(self, generator):
        """Test delay does not exceed max_delay_seconds."""
        delay = generator._calculate_backoff_delay(100)
        assert delay <= generator.max_delay_seconds


# ---------------------------------------------------------------------------
# Synchronous Generation Tests
# ---------------------------------------------------------------------------


class TestGenerateSync:
    """Tests for the synchronous _generate_sync method."""

    def test_successful_generation(self, generator, sample_image_bytes):
        """Test successful image generation returns image data."""
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        mock_response = MagicMock()
        mock_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        status, data, error = generator._generate_sync("test prompt", "16:9", "4K")

        assert status == GenerationStatus.SUCCESS
        assert data == sample_image_bytes
        assert error is None
        assert generator.api_call_count == 1

    def test_safety_blocked(self, generator):
        """Test safety filter block is detected from candidates."""
        mock_response = MagicMock()
        mock_response.parts = []
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "SAFETY"
        mock_response.candidates = [mock_candidate]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        status, data, error = generator._generate_sync("test prompt", "16:9", None)

        assert status == GenerationStatus.SAFETY_BLOCKED
        assert data is None
        assert "safety" in error.lower()

    def test_no_image_returned(self, generator):
        """Test handling of empty response (no image, no safety block)."""
        mock_response = MagicMock()
        mock_response.parts = []
        mock_response.candidates = []

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        status, data, error = generator._generate_sync("test prompt", "16:9", None)

        assert status == GenerationStatus.ERROR
        assert data is None
        assert "No image returned" in error

    def test_rate_limit_error(self, generator):
        """Test rate limiting detection from exception."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("429 Resource exhausted")
        generator._client = mock_client

        status, data, error = generator._generate_sync("test prompt", "16:9", None)

        assert status == GenerationStatus.RATE_LIMITED
        assert data is None

    def test_timeout_error(self, generator):
        """Test timeout detection from exception."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Request timeout exceeded")
        generator._client = mock_client

        status, data, error = generator._generate_sync("test prompt", "16:9", None)

        assert status == GenerationStatus.TIMEOUT
        assert data is None

    def test_safety_error_from_exception(self, generator):
        """Test safety block detection from exception message."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(
            "Content blocked by safety filter"
        )
        generator._client = mock_client

        status, data, error = generator._generate_sync("test prompt", "16:9", None)

        assert status == GenerationStatus.SAFETY_BLOCKED
        assert data is None

    def test_generic_error(self, generator):
        """Test generic error handling."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Unknown error occurred")
        generator._client = mock_client

        status, data, error = generator._generate_sync("test prompt", "16:9", None)

        assert status == GenerationStatus.ERROR
        assert "Unknown error" in error


# ---------------------------------------------------------------------------
# Async Generate Image Tests
# ---------------------------------------------------------------------------


class TestGenerateImage:
    """Tests for the async generate_image method."""

    async def test_success_first_attempt(self, generator, sample_image_bytes):
        """Test successful generation on first attempt."""
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        mock_response = MagicMock()
        mock_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        result = await generator.generate_image(
            prompt="test prompt",
            aspect_ratio=AspectRatio.LANDSCAPE_16_9,
            resolution=Resolution.HIGH,
        )

        assert result.status == GenerationStatus.SUCCESS
        assert result.image_data == sample_image_bytes
        assert result.attempt_number == 1

    async def test_success_with_string_aspect_ratio(self, generator, sample_image_bytes):
        """Test generation with string aspect ratio value."""
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        mock_response = MagicMock()
        mock_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        result = await generator.generate_image(
            prompt="test prompt",
            aspect_ratio="16:9",
            resolution=Resolution.STANDARD,
        )

        assert result.status == GenerationStatus.SUCCESS

    async def test_safety_blocked_no_retry(self, generator):
        """Test that safety-blocked results are not retried."""
        mock_response = MagicMock()
        mock_response.parts = []
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "SAFETY"
        mock_response.candidates = [mock_candidate]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        result = await generator.generate_image(prompt="blocked prompt")

        assert result.status == GenerationStatus.SAFETY_BLOCKED
        assert result.image_data is None
        # Should only be called once (no retry for safety blocks)
        assert mock_client.models.generate_content.call_count == 1

    async def test_retry_on_error(self, generator, sample_image_bytes):
        """Test retry on transient error then success."""
        # First call fails, second succeeds
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        success_response = MagicMock()
        success_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            Exception("Temporary error"),
            success_response,
        ]
        generator._client = mock_client

        result = await generator.generate_image(prompt="test prompt")

        assert result.status == GenerationStatus.SUCCESS
        assert result.attempt_number == 2

    async def test_all_retries_exhausted(self, generator):
        """Test behavior when all retries are exhausted."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Persistent error")
        generator._client = mock_client

        result = await generator.generate_image(prompt="test prompt")

        assert result.status == GenerationStatus.ERROR
        assert result.image_data is None
        assert result.attempt_number == generator.max_retries
        assert "Persistent error" in result.error_message

    async def test_progress_callback_called(self, generator, sample_image_bytes):
        """Test that progress callback is invoked."""
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        mock_response = MagicMock()
        mock_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        callback = MagicMock()

        result = await generator.generate_image(
            prompt="test prompt",
            image_number=1,
            progress_callback=callback,
        )

        assert result.status == GenerationStatus.SUCCESS
        assert callback.call_count >= 2  # At least start and completion

    async def test_duration_tracked(self, generator, sample_image_bytes):
        """Test that generation duration is tracked."""
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        mock_response = MagicMock()
        mock_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        result = await generator.generate_image(prompt="test prompt")

        assert result.duration_seconds >= 0.0


# ---------------------------------------------------------------------------
# Batch Generation Tests
# ---------------------------------------------------------------------------


class TestGenerateBatch:
    """Tests for batch image generation."""

    async def test_batch_generation(self, generator, sample_image_bytes):
        """Test generating multiple images in a batch."""
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        mock_response = MagicMock()
        mock_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        generator._client = mock_client

        prompts = [
            (1, "prompt 1", AspectRatio.LANDSCAPE_16_9, None),
            (2, "prompt 2", AspectRatio.SQUARE, None),
        ]

        results = await generator.generate_batch(prompts)

        assert len(results) == 2
        assert all(r.status == GenerationStatus.SUCCESS for r in results)

    async def test_batch_handles_exceptions(self, generator):
        """Test batch generation handles individual exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Batch error")
        generator._client = mock_client

        prompts = [(1, "prompt 1", AspectRatio.LANDSCAPE_16_9, None)]

        results = await generator.generate_batch(prompts)

        assert len(results) == 1
        # The result should be an ERROR (retries exhausted)
        assert results[0].status == GenerationStatus.ERROR


# ---------------------------------------------------------------------------
# Cost Estimation Tests
# ---------------------------------------------------------------------------


class TestCostEstimation:
    """Tests for cost estimation."""

    def test_single_image_cost(self, generator):
        """Test cost estimation for single image."""
        cost = generator.estimate_cost(1)
        assert cost.startswith("$")
        assert float(cost.replace("$", "")) > 0

    def test_multiple_images_cost(self, generator):
        """Test cost scales with image count."""
        cost1 = generator.estimate_cost(1)
        cost5 = generator.estimate_cost(5)
        assert float(cost5.replace("$", "")) > float(cost1.replace("$", ""))

    def test_custom_avg_attempts(self, generator):
        """Test cost with custom average attempts."""
        cost = generator.estimate_cost(2, avg_attempts=3.0)
        expected = 2 * 3 * 0.10  # 2 images * 3 attempts * $0.10
        assert cost == f"${expected:.2f}"


# ---------------------------------------------------------------------------
# Convenience Function Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Tests for the module-level generate_image convenience function."""

    async def test_generate_image_success(self, mock_env_with_api_keys, sample_image_bytes):
        """Test convenience function returns bytes on success."""
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes

        mock_response = MagicMock()
        mock_response.parts = [mock_part]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("visual_explainer.image_generator.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await generate_image(
                prompt="test prompt",
                api_key="test-key",
            )

        assert result == sample_image_bytes

    async def test_generate_image_failure_returns_none(self, mock_env_with_api_keys):
        """Test convenience function returns None on failure."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("fail")

        with patch("visual_explainer.image_generator.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await generate_image(
                prompt="test prompt",
                api_key="test-key",
            )

        assert result is None


# ---------------------------------------------------------------------------
# GenerationResult Dataclass Tests
# ---------------------------------------------------------------------------


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_default_values(self):
        """Test GenerationResult defaults."""
        result = GenerationResult(status=GenerationStatus.PENDING)
        assert result.image_data is None
        assert result.error_message is None
        assert result.duration_seconds == 0.0
        assert result.attempt_number == 1

    def test_success_result(self, sample_image_bytes):
        """Test creating a success result."""
        result = GenerationResult(
            status=GenerationStatus.SUCCESS,
            image_data=sample_image_bytes,
            duration_seconds=5.2,
            attempt_number=2,
        )
        assert result.status == GenerationStatus.SUCCESS
        assert result.image_data == sample_image_bytes
        assert result.duration_seconds == 5.2

    def test_error_result(self):
        """Test creating an error result."""
        result = GenerationResult(
            status=GenerationStatus.ERROR,
            error_message="Something went wrong",
        )
        assert result.error_message == "Something went wrong"
        assert result.image_data is None


# ---------------------------------------------------------------------------
# GenerationStatus Enum Tests
# ---------------------------------------------------------------------------


class TestGenerationStatus:
    """Tests for GenerationStatus enum."""

    def test_all_status_values(self):
        """Test all status enum values exist."""
        assert GenerationStatus.PENDING.value == "pending"
        assert GenerationStatus.GENERATING.value == "generating"
        assert GenerationStatus.SUCCESS.value == "success"
        assert GenerationStatus.RATE_LIMITED.value == "rate_limited"
        assert GenerationStatus.SAFETY_BLOCKED.value == "safety_blocked"
        assert GenerationStatus.TIMEOUT.value == "timeout"
        assert GenerationStatus.ERROR.value == "error"


# ---------------------------------------------------------------------------
# Aspect Ratio Mapping Tests
# ---------------------------------------------------------------------------


class TestAspectRatioMapping:
    """Tests for aspect ratio constant mapping."""

    def test_all_ratios_mapped(self):
        """Test all AspectRatio values have mappings."""
        for ar in AspectRatio:
            assert ar in GeminiImageGenerator.ASPECT_RATIOS

    def test_landscape_16_9(self):
        """Test 16:9 mapping."""
        assert GeminiImageGenerator.ASPECT_RATIOS[AspectRatio.LANDSCAPE_16_9] == "16:9"

    def test_square(self):
        """Test 1:1 mapping."""
        assert GeminiImageGenerator.ASPECT_RATIOS[AspectRatio.SQUARE] == "1:1"


# ---------------------------------------------------------------------------
# Resolution Mapping Tests
# ---------------------------------------------------------------------------


class TestResolutionMapping:
    """Tests for resolution constant mapping."""

    def test_standard_resolution(self):
        """Test standard resolution maps to None."""
        assert GeminiImageGenerator.RESOLUTION_MAP[Resolution.STANDARD] is None

    def test_high_resolution(self):
        """Test high resolution maps to 4K."""
        assert GeminiImageGenerator.RESOLUTION_MAP[Resolution.HIGH] == "4K"

    def test_ultra_resolution(self):
        """Test ultra resolution maps to 4K."""
        assert GeminiImageGenerator.RESOLUTION_MAP[Resolution.ULTRA] == "4K"
