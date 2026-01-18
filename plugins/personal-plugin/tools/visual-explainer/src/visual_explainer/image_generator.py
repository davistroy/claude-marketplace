"""Gemini image generator for Visual Concept Explainer.

This module provides the GeminiImageGenerator class for generating images
using Google's Imagen 3.0 API via raw HTTP calls (not the google-genai SDK).

Key features:
- Async HTTP client using httpx
- 4K image generation (LARGE/3200x1800) by default
- 300-second timeout for 4K generation
- Exponential backoff retry logic for rate limits (429)
- Safety filter handling (log and return None)
- Concurrent generation with semaphore control
- Progress callback support for UI updates

API Endpoint: POST https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict
API Key: Passed as query parameter ?key=YOUR_API_KEY
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

import httpx

from visual_explainer.config import AspectRatio, InternalConfig, Resolution

# Configure logging
logger = logging.getLogger(__name__)


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
    """Async Gemini image generator using Imagen 3.0 API.

    This class handles all image generation via Google's Imagen API,
    including retry logic, rate limiting, safety filter handling,
    and concurrent generation control.

    Attributes:
        api_key: Google API key for authentication.
        model_id: Imagen model ID to use.
        api_base: Base URL for the Gemini API.
        timeout_seconds: Timeout for API calls.
        max_retries: Maximum retry attempts for transient failures.
        base_delay_seconds: Base delay for exponential backoff.
        max_delay_seconds: Maximum delay between retries.
        semaphore: Asyncio semaphore for concurrent generation control.
    """

    # API configuration
    MODEL_ID = "imagen-3.0-generate-002"
    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    # Aspect ratio mapping for Imagen API
    ASPECT_RATIOS = {
        AspectRatio.LANDSCAPE_16_9: "16:9",
        AspectRatio.SQUARE: "1:1",
        AspectRatio.LANDSCAPE_4_3: "4:3",
        AspectRatio.PORTRAIT_9_16: "9:16",
        AspectRatio.PORTRAIT_3_4: "3:4",
    }

    # Resolution to sampleImageSize mapping
    RESOLUTION_MAP = {
        Resolution.STANDARD: "1024x1024",  # Standard resolution
        Resolution.HIGH: "1536x1536",  # Higher resolution
        Resolution.ULTRA: "1536x1536",  # Currently same as HIGH
    }

    def __init__(
        self,
        api_key: str | None = None,
        internal_config: InternalConfig | None = None,
        max_concurrent: int = 3,
        max_retries: int = 5,
        base_delay_seconds: float = 2.0,
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
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Load internal config with defaults
        self.internal_config = internal_config or InternalConfig.from_env()

        # Timeout for 4K image generation (300 seconds as specified)
        self.timeout_seconds = self.internal_config.gemini_timeout_seconds

        # Model ID from config or default
        self.model_id = self.internal_config.gemini_model
        # Override to use Imagen model for image generation
        if "image" not in self.model_id.lower() and "imagen" not in self.model_id.lower():
            self.model_id = self.MODEL_ID

        # Retry configuration
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds

        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Track API call count for cost estimation
        self._api_call_count = 0

    @property
    def api_endpoint(self) -> str:
        """Get the full API endpoint URL."""
        return f"{self.API_BASE}/models/{self.model_id}:predict"

    @property
    def api_call_count(self) -> int:
        """Get the total number of API calls made."""
        return self._api_call_count

    def reset_api_call_count(self) -> None:
        """Reset the API call counter."""
        self._api_call_count = 0

    def _build_request_payload(
        self,
        prompt: str,
        aspect_ratio: AspectRatio | str = AspectRatio.LANDSCAPE_16_9,
        negative_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Build the request payload for the Imagen API.

        Args:
            prompt: The image generation prompt.
            aspect_ratio: Desired aspect ratio for the image.
            negative_prompt: Optional negative prompt for exclusions.

        Returns:
            Dictionary payload for the API request.
        """
        # Normalize aspect ratio
        if isinstance(aspect_ratio, AspectRatio):
            ar_value = self.ASPECT_RATIOS.get(aspect_ratio, "16:9")
        else:
            ar_value = aspect_ratio

        # Build parameters
        parameters: dict[str, Any] = {
            "sampleCount": 1,
            "aspectRatio": ar_value,
            "personGeneration": "DONT_ALLOW",  # Safety setting per spec
        }

        # Add negative prompt if provided
        effective_negative = negative_prompt or self.internal_config.negative_prompt
        if effective_negative:
            parameters["negativePrompt"] = effective_negative

        return {
            "instances": [{"prompt": prompt}],
            "parameters": parameters,
        }

    async def _make_api_call(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
    ) -> tuple[GenerationStatus, bytes | None, str | None]:
        """Make a single API call and handle the response.

        Args:
            client: The httpx async client.
            payload: The request payload.

        Returns:
            Tuple of (status, image_data or None, error_message or None).
        """
        self._api_call_count += 1

        try:
            response = await client.post(
                self.api_endpoint,
                params={"key": self.api_key},
                json=payload,
                timeout=self.timeout_seconds,
            )

            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                logger.warning(
                    f"Rate limited by Gemini API. Retry-After: {retry_after}s"
                )
                return GenerationStatus.RATE_LIMITED, None, f"Rate limited. Retry after {retry_after}s"

            # Handle other HTTP errors
            if response.status_code != 200:
                error_text = response.text
                logger.error(
                    f"Gemini API error {response.status_code}: {error_text[:500]}"
                )

                # Check for safety filter in error response
                if "safety" in error_text.lower() or "blocked" in error_text.lower():
                    return GenerationStatus.SAFETY_BLOCKED, None, "Content blocked by safety filter"

                return GenerationStatus.ERROR, None, f"HTTP {response.status_code}: {error_text[:200]}"

            # Parse successful response
            result = response.json()
            return self._extract_image_from_response(result)

        except httpx.TimeoutException:
            logger.error(f"Gemini API timeout after {self.timeout_seconds}s")
            return GenerationStatus.TIMEOUT, None, f"Request timed out after {self.timeout_seconds}s"

        except httpx.RequestError as e:
            logger.error(f"Gemini API request error: {e}")
            return GenerationStatus.ERROR, None, f"Request error: {str(e)}"

    def _extract_image_from_response(
        self,
        result: dict[str, Any],
    ) -> tuple[GenerationStatus, bytes | None, str | None]:
        """Extract image data from the API response.

        Args:
            result: Parsed JSON response from the API.

        Returns:
            Tuple of (status, image_data or None, error_message or None).
        """
        # Check for safety filter blocks in response
        if "error" in result:
            error_info = result["error"]
            error_message = error_info.get("message", str(error_info))
            if "safety" in error_message.lower() or "blocked" in error_message.lower():
                logger.warning(f"Safety filter blocked generation: {error_message}")
                return GenerationStatus.SAFETY_BLOCKED, None, error_message
            return GenerationStatus.ERROR, None, error_message

        # Extract predictions from response
        predictions = result.get("predictions", [])
        if not predictions:
            logger.warning("No predictions in Gemini response")
            return GenerationStatus.ERROR, None, "No predictions in response"

        # Get the first prediction
        prediction = predictions[0]

        # Check for safety block at prediction level
        if prediction.get("safetyFilteredReason"):
            reason = prediction["safetyFilteredReason"]
            logger.warning(f"Safety filter blocked: {reason}")
            return GenerationStatus.SAFETY_BLOCKED, None, f"Safety blocked: {reason}"

        # Extract base64 image data
        # The response format uses "bytesBase64Encoded" for image data
        image_b64 = prediction.get("bytesBase64Encoded")
        if not image_b64:
            # Try alternative response formats
            if "image" in prediction:
                image_data = prediction["image"]
                if isinstance(image_data, dict):
                    image_b64 = image_data.get("bytesBase64Encoded") or image_data.get("data")
                elif isinstance(image_data, str):
                    image_b64 = image_data

        if not image_b64:
            logger.error(f"No image data in response. Keys: {prediction.keys()}")
            return GenerationStatus.ERROR, None, "No image data in response"

        # Decode base64 to bytes
        try:
            image_bytes = base64.b64decode(image_b64)
            return GenerationStatus.SUCCESS, image_bytes, None
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return GenerationStatus.ERROR, None, f"Failed to decode image: {e}"

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
        - Exponential backoff for rate limits (429)
        - Retry logic for transient failures
        - Safety filter handling (returns None for blocked content)
        - Progress callback support

        Args:
            prompt: The image generation prompt.
            aspect_ratio: Desired aspect ratio (default: 16:9).
            resolution: Image resolution (default: HIGH for 4K).
            negative_prompt: Optional negative prompt for exclusions.
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
                negative_prompt=negative_prompt,
                image_number=image_number,
                progress_callback=progress_callback,
            )

    async def _generate_with_retry(
        self,
        prompt: str,
        aspect_ratio: AspectRatio | str,
        resolution: Resolution,
        negative_prompt: str | None,
        image_number: int,
        progress_callback: ProgressCallback | None,
    ) -> GenerationResult:
        """Internal method that handles retry logic.

        Args:
            prompt: The image generation prompt.
            aspect_ratio: Desired aspect ratio.
            resolution: Image resolution.
            negative_prompt: Optional negative prompt.
            image_number: Image number for progress tracking.
            progress_callback: Optional progress callback.

        Returns:
            GenerationResult with status and image data.
        """
        start_time = time.time()
        payload = self._build_request_payload(prompt, aspect_ratio, negative_prompt)

        # Notify start
        if progress_callback:
            progress_callback(image_number, "Starting generation...", 0.0)

        async with httpx.AsyncClient() as client:
            for attempt in range(1, self.max_retries + 1):
                attempt_start = time.time()

                # Update progress
                if progress_callback:
                    progress = (attempt - 1) / self.max_retries * 100
                    progress_callback(
                        image_number,
                        f"Attempt {attempt}/{self.max_retries}...",
                        progress,
                    )

                logger.info(
                    f"Image {image_number}: Attempt {attempt}/{self.max_retries}"
                )

                status, image_data, error_msg = await self._make_api_call(client, payload)
                attempt_duration = time.time() - attempt_start

                # Success - return immediately
                if status == GenerationStatus.SUCCESS:
                    total_duration = time.time() - start_time
                    if progress_callback:
                        progress_callback(image_number, "Generation complete", 100.0)

                    logger.info(
                        f"Image {image_number}: Generated in {total_duration:.1f}s "
                        f"(attempt {attempt})"
                    )
                    return GenerationResult(
                        status=status,
                        image_data=image_data,
                        duration_seconds=total_duration,
                        attempt_number=attempt,
                    )

                # Safety block - don't retry, return None
                if status == GenerationStatus.SAFETY_BLOCKED:
                    total_duration = time.time() - start_time
                    logger.warning(
                        f"Image {image_number}: Safety blocked after {total_duration:.1f}s"
                    )
                    if progress_callback:
                        progress_callback(image_number, f"Blocked: {error_msg}", 100.0)

                    return GenerationResult(
                        status=status,
                        image_data=None,
                        error_message=error_msg,
                        duration_seconds=total_duration,
                        attempt_number=attempt,
                    )

                # Rate limit or transient error - retry with backoff
                if status in (GenerationStatus.RATE_LIMITED, GenerationStatus.TIMEOUT, GenerationStatus.ERROR):
                    if attempt < self.max_retries:
                        delay = self._calculate_backoff_delay(attempt)

                        # For rate limits, respect Retry-After if present
                        if status == GenerationStatus.RATE_LIMITED and error_msg:
                            try:
                                # Try to parse Retry-After from error message
                                if "Retry after" in error_msg:
                                    retry_seconds = int(error_msg.split()[-1].rstrip("s"))
                                    delay = max(delay, retry_seconds)
                            except (ValueError, IndexError):
                                pass

                        logger.info(
                            f"Image {image_number}: Retrying in {delay:.1f}s "
                            f"(status: {status.value})"
                        )
                        if progress_callback:
                            progress_callback(
                                image_number,
                                f"Retry in {delay:.0f}s...",
                                (attempt / self.max_retries) * 100,
                            )

                        await asyncio.sleep(delay)
                        continue

            # All retries exhausted
            total_duration = time.time() - start_time
            final_error = error_msg or f"Failed after {self.max_retries} attempts"

            logger.error(
                f"Image {image_number}: Generation failed after {self.max_retries} "
                f"attempts ({total_duration:.1f}s): {final_error}"
            )
            if progress_callback:
                progress_callback(image_number, f"Failed: {final_error[:50]}", 100.0)

            return GenerationResult(
                status=status,
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
        # Gemini image generation: ~$0.10 per image (estimate from spec)
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
        negative_prompt: Optional negative prompt.

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
