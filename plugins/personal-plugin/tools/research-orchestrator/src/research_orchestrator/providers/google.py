"""Google Gemini provider for deep research agent using google-genai SDK."""

import asyncio
import os
import time
import warnings
from typing import Any, Callable

# Suppress experimental API warnings from google-genai SDK
warnings.filterwarnings("ignore", module="google.genai")
warnings.filterwarnings("ignore", message=".*Interactions usage is experimental.*")
warnings.filterwarnings("ignore", message=".*Async interactions client cannot use aiohttp.*")

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderPhase, ProviderResult, ProviderStatus
from research_orchestrator.providers.base import BaseProvider


class GoogleProvider(BaseProvider):
    """Google Gemini provider using deep research agent via google-genai SDK."""

    DEFAULT_AGENT = "deep-research-pro-preview-12-2025"
    POLL_INTERVAL = 5.0  # seconds between status checks

    @classmethod
    def get_agent(cls) -> str:
        """Get agent from environment or use default."""
        return os.getenv("GEMINI_AGENT", cls.DEFAULT_AGENT)

    def __init__(
        self,
        config: ProviderConfig,
        depth: Depth,
        on_status_update: Callable[[str, str], None] | None = None,
    ) -> None:
        """Initialize the Google provider."""
        super().__init__(config, depth, on_status_update)
        self._client: Any = None

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "gemini"

    def _get_client(self) -> Any:
        """Get or create the Google GenAI client."""
        if self._client is None:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.config.api_key)
            except ImportError:
                raise ImportError(
                    "google-genai package required. Install with: pip install google-genai"
                )
        return self._client

    async def execute(self, prompt: str) -> ProviderResult:
        """Execute research using Gemini deep research agent.

        Gemini deep research runs in background mode and requires polling.
        Uses the google-genai SDK for reliable API interaction.
        """
        self._validate_api_key()
        start_time = time.time()

        try:
            # Phase: INITIALIZING
            self._phase_update(ProviderPhase.INITIALIZING, "Creating Gemini client")
            client = self._get_client()

            agent = self.get_agent()

            # Phase: CONNECTING
            self._phase_update(ProviderPhase.CONNECTING, f"Connecting to {agent}")

            # Create interaction with deep research agent in background mode
            # The SDK handles the API endpoint and request formatting
            # Note: store=True is required when using background=True per Google docs
            interaction = client.aio.interactions.create(
                input=prompt,
                agent=agent,
                background=True,
                store=True,
            )

            # Phase: RESEARCHING
            self._phase_update(ProviderPhase.RESEARCHING, "Initiating deep research")

            # Run the async create call
            interaction_result = await interaction

            # Get interaction ID - try multiple possible attribute names
            interaction_id = (
                getattr(interaction_result, 'name', None) or
                getattr(interaction_result, 'id', None) or
                getattr(interaction_result, 'interaction_id', None)
            )
            if not interaction_id:
                # Debug: show what attributes are available
                attrs = [a for a in dir(interaction_result) if not a.startswith('_')]
                raise ValueError(f"No interaction ID in response. Available attrs: {attrs[:10]}")

            result = await self._poll_for_completion(client, interaction_id, start_time)
            return result

        except asyncio.TimeoutError:
            self._phase_update(
                ProviderPhase.FAILED,
                f"Timeout after {self.config.timeout_seconds}s"
            )
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.TIMEOUT,
                error=f"Request timed out after {self.config.timeout_seconds}s",
                duration_seconds=time.time() - start_time,
            )
        except Exception as e:
            self._phase_update(ProviderPhase.FAILED, str(e)[:50])
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.FAILED,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def _poll_for_completion(
        self, client: Any, interaction_id: str, start_time: float
    ) -> ProviderResult:
        """Poll for background interaction completion."""
        last_status_update = 0.0
        poll_count = 0
        while True:
            elapsed = time.time() - start_time
            if elapsed > self.config.timeout_seconds:
                self._phase_update(ProviderPhase.FAILED, f"Timeout after {elapsed:.0f}s")
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.TIMEOUT,
                    error=f"Request timed out after {self.config.timeout_seconds}s",
                    duration_seconds=elapsed,
                )

            # Emit progress update every 30 seconds
            if elapsed - last_status_update >= 30.0:
                poll_count += 1
                self._phase_update(
                    ProviderPhase.POLLING,
                    f"Checking status ({elapsed:.0f}s elapsed)"
                )
                last_status_update = elapsed

            try:
                # Use SDK to get interaction status (pass ID as positional arg)
                interaction = await client.aio.interactions.get(interaction_id)

                # Check for completion
                if getattr(interaction, "done", False):
                    # Phase: PROCESSING
                    self._phase_update(ProviderPhase.PROCESSING, "Extracting content")
                    content = self._extract_content(interaction)
                    duration = time.time() - start_time

                    # Phase: COMPLETED
                    self._phase_update(ProviderPhase.COMPLETED, f"Done ({duration:.1f}s)")

                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.SUCCESS,
                        content=content,
                        duration_seconds=duration,
                        metadata={
                            "agent": self.get_agent(),
                            "interaction_id": interaction_id,
                        },
                    )

                status = getattr(interaction, "status", "").lower()
                if status in ("completed", "done"):
                    # Phase: PROCESSING
                    self._phase_update(ProviderPhase.PROCESSING, "Extracting content")
                    content = self._extract_content(interaction)
                    duration = time.time() - start_time

                    # Phase: COMPLETED
                    self._phase_update(ProviderPhase.COMPLETED, f"Done ({duration:.1f}s)")

                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.SUCCESS,
                        content=content,
                        duration_seconds=duration,
                        metadata={
                            "agent": self.get_agent(),
                            "interaction_id": interaction_id,
                        },
                    )
                elif status in ("failed", "error", "cancelled"):
                    error_msg = getattr(interaction, "error", None)
                    if error_msg and hasattr(error_msg, "message"):
                        error_msg = error_msg.message
                    else:
                        error_msg = str(error_msg) if error_msg else "Unknown error"
                    self._phase_update(ProviderPhase.FAILED, str(error_msg)[:50])
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.FAILED,
                        error=error_msg,
                        duration_seconds=time.time() - start_time,
                    )

                await asyncio.sleep(self.POLL_INTERVAL)

            except Exception as e:
                self._phase_update(ProviderPhase.FAILED, f"Polling error: {str(e)[:30]}")
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.FAILED,
                    error=f"Polling error: {e}",
                    duration_seconds=time.time() - start_time,
                )

    def _extract_content(self, interaction: Any) -> str:
        """Extract content from completed interaction response."""
        # Per Google docs: interaction.outputs[-1].text is the primary format
        if hasattr(interaction, "outputs") and interaction.outputs:
            last_output = interaction.outputs[-1]
            if hasattr(last_output, "text"):
                return last_output.text
            if hasattr(last_output, "content"):
                return last_output.content
            if isinstance(last_output, str):
                return last_output

        # Try various response formats the SDK might return
        if hasattr(interaction, "result"):
            result = interaction.result
            if isinstance(result, str):
                return result
            if hasattr(result, "text"):
                return result.text
            if hasattr(result, "content"):
                return result.content
            if isinstance(result, dict):
                if "text" in result:
                    return result["text"]
                if "content" in result:
                    return result["content"]

        if hasattr(interaction, "response"):
            response = interaction.response
            if isinstance(response, str):
                return response
            if hasattr(response, "text"):
                return response.text
            if hasattr(response, "candidates"):
                candidates = response.candidates
                if candidates:
                    candidate = candidates[0]
                    if hasattr(candidate, "content"):
                        content = candidate.content
                        if hasattr(content, "parts"):
                            parts = content.parts
                            texts = []
                            for part in parts:
                                if hasattr(part, "text"):
                                    texts.append(part.text)
                            if texts:
                                return "\n\n".join(texts)

        # Fallback: try to get any text-like attribute
        if hasattr(interaction, "text"):
            return interaction.text
        if hasattr(interaction, "output"):
            output = interaction.output
            if isinstance(output, str):
                return output
            if hasattr(output, "text"):
                return output.text

        return str(interaction)
