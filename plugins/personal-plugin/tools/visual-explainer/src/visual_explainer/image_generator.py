"""Gemini image generator for Visual Concept Explainer.

This module provides the GeminiImageGenerator class for generating images
using Google's Gemini API with the google-genai SDK.

Key features:
- Uses google-genai SDK (not raw HTTP calls)
- 4K image generation support
- 300-second timeout for 4K generation
- Retry logic for transient failures
- Safety filter handling (log and return None)
- Concurrent generation with semaphore control
- Progress callback support for UI updates
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from visual_explainer.config import AspectRatio, InternalConfig, Resolution

# Configure logging
logger = logging.getLogger(__name__)

# Try to import google-genai
try:
    from google import genai
    from google.genai import types

    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    logger.warning("google-genai package not installed. Image generation will not be available.")


class GenerationStatus(str, Enum):
    """Status of an image generation attempt."""

    PENDING = "pending"
    GENERATING = "generating"
    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    SAFETY_BLOCKED = "safety_blocked"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class GenerationResult:
    """Result of an image generation attempt.

    Attributes:
        status: The status of the generation attempt.
        image_data: Raw image bytes if successful, None otherwise.
        error_message: Error description if failed, None otherwise.
        duration_seconds: Time taken for the generation.
        attempt_number: Which retry attempt this was (1-indexed).
    """

    status: GenerationStatus
    image_data: bytes | None = None
    error_message: str | None = None
    duration_seconds: float = 0.0
    attempt_number: int = 1


# Type alias for progress callback
# Callback signature: (image_number, status_message, progress_percent)
ProgressCallback = Callable[[int, str, float], None]


class GeminiImageGenerator:
    """Gemini image generator using google-genai SDK.

    This class handles all image generation via Google's Gemini API,
    including retry logic, rate limiting, safety filter handling,
    and concurrent generation control.

    Attributes:
        api_key: Google API key for authentication.
        model_id: Gemini model ID to use.
        timeout_ms: Timeout for API calls in milliseconds.
        max_retries: Maximum retry attempts for transient failures.
        base_delay_seconds: Base delay for exponential backoff.
        max_delay_seconds: Maximum delay between retries.
        semaphore: Asyncio semaphore for concurrent generation control.
    """

    # Default model - gemini-3-pro-image-preview supports image generation
    MODEL_ID = "gemini-3-pro-image-preview"

    # Aspect ratio mapping
    ASPECT_RATIOS = {
        AspectRatio.LANDSCAPE_16_9: "16:9",
        AspectRatio.SQUARE: "1:1",
        AspectRatio.LANDSCAPE_4_3: "4:3",
        AspectRatio.PORTRAIT_9_16: "9:16",
        AspectRatio.PORTRAIT_3_4: "3:4",
    }

    # Resolution mapping to image_size parameter
    RESOLUTION_MAP = {
        Resolution.STANDARD: None,  # Standard resolution
        Resolution.HIGH: "4K",  # 4K resolution
        Resolution.ULTRA: "4K",  # Same as HIGH for now
    }

    def __init__(
        self,
        api_key: str | None = None,
        internal_config: InternalConfig | None = None,
        max_concurrent: int = 3,
        max_retries: int = 3,
        base_delay_seconds: float = 5.0,
        max_delay_seconds: float = 60.0,
    ) -> None:
        """Initialize the Gemini image generator.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
            internal_config: Internal configuration. If None, uses defaults from env.
            max_concurrent: Maximum concurrent generations (default: 3).
            max_retries: Maximum retry attempts for transient failures.
            base_delay_seconds: Base delay for exponential backoff.
            max_delay_seconds: Maximum delay between retries.

        Raises:
            ValueError: If no API key is provided or found in environment.
            RuntimeError: If google-genai package is not installed.
        """
        if not GOOGLE_GENAI_AVAILABLE:
            raise RuntimeError(
                "google-genai package not installed. Install with: pip install google-genai"
            )

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Load internal config with defaults
        self.internal_config = internal_config or InternalConfig.from_env()

        # Timeout for 4K image generation (300 seconds as specified, in ms for SDK)
        self.timeout_ms = int(self.internal_config.gemini_timeout_seconds * 1000)

        # Model ID - use default image generation model
        self.model_id = self.MODEL_ID

        # Retry configuration
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds

        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Track API call count for cost estimation
        self._api_call_count = 0

        # Initialize client
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create the Gemini client."""
        if self._client is None:
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=self.timeout_ms),
            )
        return self._client

    @property
    def api_call_count(self) -> int:
        """Get the total number of API calls made."""
        return self._api_call_count

    def reset_api_call_count(self) -> None:
        """Reset the API call counter."""
        self._api_call_count = 0

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter.

        Args:
            attempt: The current attempt number (1-indexed).

        Returns:
            Delay in seconds before next retry.
        """
        # Exponential backoff: base * 2^(attempt-1)
        delay = self.base_delay_seconds * (2 ** (attempt - 1))

        # Add jitter (10-30% random variation)
        jitter = delay * random.uniform(0.1, 0.3)
        delay += jitter

        # Cap at maximum delay
        return min(delay, self.max_delay_seconds)

    def _generate_sync(
        self,
        prompt: str,
        aspect_ratio: str,
        image_size: str | None,
    ) -> tuple[GenerationStatus, bytes | None, str | None]:
        """Synchronous image generation using google-genai SDK.

        Args:
            prompt: The image generation prompt.
            aspect_ratio: Aspect ratio string (e.g., "16:9").
            image_size: Image size string (e.g., "4K") or None for standard.

        Returns:
            Tuple of (status, image_data or None, error_message or None).
        """
        self._api_call_count += 1

        try:
            client = self._get_client()

            # Build image config
            image_config = types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            )

            # Build generation config with IMAGE modality
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=image_config,
            )

            # Make the API call
            response = client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=config,
            )

            # Check for image in response
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        # Success - return the image data
                        return GenerationStatus.SUCCESS, part.inline_data.data, None

            # No image returned - check for safety blocks
            if response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)
                if "SAFETY" in finish_reason:
                    logger.warning(f"Safety filter blocked generation: {finish_reason}")
                    return (
                        GenerationStatus.SAFETY_BLOCKED,
                        None,
                        f"Blocked by safety filter: {finish_reason}",
                    )

            # No image and no safety block
            logger.warning("No image returned from Gemini API")
            return GenerationStatus.ERROR, None, "No image returned from API"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini API error: {error_msg}")

            # Check for rate limiting
            if "429" in error_msg or "rate" in error_msg.lower():
                return GenerationStatus.RATE_LIMITED, None, f"Rate limited: {error_msg}"

            # Check for timeout
            if "timeout" in error_msg.lower():
                return GenerationStatus.TIMEOUT, None, f"Timeout: {error_msg}"

            # Check for safety block in error
            if "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                return GenerationStatus.SAFETY_BLOCKED, None, f"Blocked: {error_msg}"

            return GenerationStatus.ERROR, None, error_msg

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: AspectRatio | str = AspectRatio.LANDSCAPE_16_9,
        resolution: Resolution = Resolution.HIGH,
        negative_prompt: str | None = None,
        image_number: int = 1,
        progress_callback: ProgressCallback | None = None,
    ) -> GenerationResult:
        """Generate an image with retry logic and rate limit handling.

        This method implements:
        - Exponential backoff for rate limits
        - Retry logic for transient failures
        - Safety filter handling (returns None for blocked content)
        - Progress callback support

        Args:
            prompt: The image generation prompt.
            aspect_ratio: Desired aspect ratio (default: 16:9).
            resolution: Image resolution (default: HIGH for 4K).
            negative_prompt: Optional negative prompt (not used in Gemini API).
            image_number: Image number for progress tracking (1-indexed).
            progress_callback: Optional callback for progress updates.
                Signature: (image_number, status_message, progress_percent)

        Returns:
            GenerationResult with status and image data (if successful).
        """
        # Acquire semaphore for concurrent generation control
        async with self.semaphore:
            return await self._generate_with_retry(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                image_number=image_number,
                progress_callback=progress_callback,
            )

    async def _attempt_generation(
        self,
        prompt: str,
        ar_value: str,
        image_size: str | None,
        attempt: int,
        image_number: int,
        start_time: float,
        progress_callback: ProgressCallback | None,
    ) -> GenerationResult:
        """Execute a single generation attempt.

        Args:
            prompt: The image generation prompt.
            ar_value: Normalized aspect ratio string (e.g., "16:9").
            image_size: Image size string (e.g., "4K") or None.
            attempt: Current attempt number (1-indexed).
            image_number: Image number for progress tracking.
            start_time: Overall start time for duration tracking.
            progress_callback: Optional progress callback.

        Returns:
            GenerationResult for this attempt.
        """
        # Update progress
        if progress_callback:
            progress = (attempt - 1) / self.max_retries * 100
            progress_callback(
                image_number,
                f"Attempt {attempt}/{self.max_retries}...",
                progress,
            )

        logger.info(f"Image {image_number}: Attempt {attempt}/{self.max_retries}")

        # Run synchronous API call in executor to not block async loop
        loop = asyncio.get_event_loop()
        status, image_data, error_msg = await loop.run_in_executor(
            None,
            self._generate_sync,
            prompt,
            ar_value,
            image_size,
        )

        total_duration = time.time() - start_time

        if status == GenerationStatus.SUCCESS:
            if progress_callback:
                progress_callback(image_number, "Generation complete", 100.0)
            logger.info(
                f"Image {image_number}: Generated in {total_duration:.1f}s (attempt {attempt})"
            )
            return GenerationResult(
                status=status,
                image_data=image_data,
                duration_seconds=total_duration,
                attempt_number=attempt,
            )

        if status == GenerationStatus.SAFETY_BLOCKED:
            logger.warning(f"Image {image_number}: Safety blocked after {total_duration:.1f}s")
            if progress_callback:
                progress_callback(image_number, f"Blocked: {error_msg}", 100.0)
            return GenerationResult(
                status=status,
                image_data=None,
                error_message=error_msg,
                duration_seconds=total_duration,
                attempt_number=attempt,
            )

        # Transient failure — caller decides whether to retry
        return GenerationResult(
            status=status,
            image_data=None,
            error_message=error_msg,
            duration_seconds=total_duration,
            attempt_number=attempt,
        )

    def _should_retry(self, result: GenerationResult, attempt: int) -> bool:
        """Determine whether a failed attempt should be retried.

        Args:
            result: The result of the latest attempt.
            attempt: Current attempt number (1-indexed).

        Returns:
            True if the attempt should be retried.
        """
        if result.status in (GenerationStatus.SUCCESS, GenerationStatus.SAFETY_BLOCKED):
            return False
        return attempt < self.max_retries

    async def _wait_for_retry(
        self,
        attempt: int,
        result: GenerationResult,
        image_number: int,
        progress_callback: ProgressCallback | None,
    ) -> None:
        """Handle backoff delay between retry attempts.

        Args:
            attempt: Current attempt number (1-indexed).
            result: The result of the latest attempt.
            image_number: Image number for progress tracking.
            progress_callback: Optional progress callback.
        """
        delay = self._calculate_backoff_delay(attempt)

        logger.info(
            f"Image {image_number}: Retrying in {delay:.1f}s (status: {result.status.value})"
        )
        if progress_callback:
            progress_callback(
                image_number,
                f"Retry in {delay:.0f}s...",
                (attempt / self.max_retries) * 100,
            )

        await asyncio.sleep(delay)

    async def _generate_with_retry(
        self,
        prompt: str,
        aspect_ratio: AspectRatio | str,
        resolution: Resolution,
        image_number: int,
        progress_callback: ProgressCallback | None,
    ) -> GenerationResult:
        """Internal method that handles retry logic.

        Args:
            prompt: The image generation prompt.
            aspect_ratio: Desired aspect ratio.
            resolution: Image resolution.
            image_number: Image number for progress tracking.
            progress_callback: Optional progress callback.

        Returns:
            GenerationResult with status and image data.
        """
        start_time = time.time()
        ar_value = (
            self.ASPECT_RATIOS.get(aspect_ratio, "16:9")
            if isinstance(aspect_ratio, AspectRatio)
            else aspect_ratio
        )
        image_size = self.RESOLUTION_MAP.get(resolution)

        if progress_callback:
            progress_callback(image_number, "Starting generation...", 0.0)

        result = GenerationResult(status=GenerationStatus.ERROR)
        for attempt in range(1, self.max_retries + 1):
            result = await self._attempt_generation(
                prompt,
                ar_value,
                image_size,
                attempt,
                image_number,
                start_time,
                progress_callback,
            )
            if result.status == GenerationStatus.SUCCESS:
                return result
            if not self._should_retry(result, attempt):
                return result
            await self._wait_for_retry(attempt, result, image_number, progress_callback)

        # All retries exhausted
        total_duration = time.time() - start_time
        final_error = result.error_message or f"Failed after {self.max_retries} attempts"
        logger.error(
            f"Image {image_number}: Generation failed after {self.max_retries} "
            f"attempts ({total_duration:.1f}s): {final_error}"
        )
        if progress_callback:
            progress_callback(image_number, f"Failed: {final_error[:50]}", 100.0)

        return GenerationResult(
            status=result.status,
            image_data=None,
            error_message=final_error,
            duration_seconds=total_duration,
            attempt_number=self.max_retries,
        )

    async def generate_batch(
        self,
        prompts: list[tuple[int, str, AspectRatio | str, str | None]],
        resolution: Resolution = Resolution.HIGH,
        progress_callback: ProgressCallback | None = None,
    ) -> list[GenerationResult]:
        """Generate multiple images concurrently.

        The semaphore controls concurrent generation to respect API limits.

        Args:
            prompts: List of (image_number, prompt, aspect_ratio, negative_prompt) tuples.
            resolution: Image resolution for all images.
            progress_callback: Optional callback for progress updates.

        Returns:
            List of GenerationResult in the same order as input prompts.
        """
        tasks = [
            self.generate_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                negative_prompt=negative_prompt,
                image_number=image_num,
                progress_callback=progress_callback,
            )
            for image_num, prompt, aspect_ratio, negative_prompt in prompts
        ]

        # Run all tasks concurrently (semaphore controls actual concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to GenerationResult
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch generation error for prompt {i}: {result}")
                final_results.append(
                    GenerationResult(
                        status=GenerationStatus.ERROR,
                        error_message=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def estimate_cost(self, image_count: int, avg_attempts: float = 1.5) -> str:
        """Estimate generation cost based on image count.

        Args:
            image_count: Number of images to generate.
            avg_attempts: Average attempts per image (default: 1.5).

        Returns:
            Formatted cost string (e.g., "$0.70").
        """
        # Gemini image generation: ~$0.10 per image (estimate)
        cost_per_image = 0.10
        total_calls = int(image_count * avg_attempts)
        estimated_cost = total_calls * cost_per_image
        return f"${estimated_cost:.2f}"


# Convenience function for simple usage
async def generate_image(
    prompt: str,
    api_key: str | None = None,
    aspect_ratio: AspectRatio | str = AspectRatio.LANDSCAPE_16_9,
    negative_prompt: str | None = None,
) -> bytes | None:
    """Convenience function to generate a single image.

    Args:
        prompt: The image generation prompt.
        api_key: Google API key (or uses GOOGLE_API_KEY env var).
        aspect_ratio: Desired aspect ratio.
        negative_prompt: Optional negative prompt (not used).

    Returns:
        Image bytes if successful, None otherwise.
    """
    generator = GeminiImageGenerator(api_key=api_key)
    result = await generator.generate_image(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        negative_prompt=negative_prompt,
    )
    return result.image_data if result.status == GenerationStatus.SUCCESS else None
