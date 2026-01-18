"""OpenAI provider for deep research with web search."""

import asyncio
import os
import time
from typing import Any, Callable

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderPhase, ProviderResult, ProviderStatus
from research_orchestrator.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI provider using o3 deep research model with web search."""

    DEFAULT_MODEL = "o3-deep-research-2025-06-26"
    POLL_INTERVAL = 5.0  # seconds between status checks

    @classmethod
    def get_model(cls) -> str:
        """Get model from environment or use default."""
        return os.getenv("OPENAI_MODEL", cls.DEFAULT_MODEL)

    def __init__(
        self,
        config: ProviderConfig,
        depth: Depth,
        on_status_update: Callable[[str, str], None] | None = None,
    ) -> None:
        """Initialize the OpenAI provider."""
        super().__init__(config, depth, on_status_update)
        self._client: Any = None

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "openai"

    def _get_client(self) -> Any:
        """Get or create the OpenAI client."""
        if self._client is None:
            try:
                import openai

                self._client = openai.OpenAI(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        return self._client

    async def execute(self, prompt: str) -> ProviderResult:
        """Execute research using OpenAI o3 deep research with web search.

        OpenAI deep research runs in background mode and requires polling.
        Uses web_search_preview tool for comprehensive web research.
        """
        self._validate_api_key()
        start_time = time.time()

        # Phase: INITIALIZING
        self._phase_update(ProviderPhase.INITIALIZING, "Creating OpenAI client")

        # Try with reasoning summary first, fall back without if org not verified
        reasoning_summary = self.depth.get_openai_reasoning_summary()
        result = await self._execute_with_reasoning(prompt, reasoning_summary, start_time)

        # Check if we got the "organization must be verified" error
        if (
            result.status == ProviderStatus.FAILED
            and result.error
            and "organization must be verified" in result.error.lower()
        ):
            # Retry without reasoning summary
            self._phase_update(
                ProviderPhase.CONNECTING,
                "Retrying without reasoning summary"
            )
            result = await self._execute_with_reasoning(prompt, None, start_time)
            if result.status == ProviderStatus.SUCCESS and result.metadata:
                result.metadata["reasoning_summary_fallback"] = True

        return result

    async def _execute_with_reasoning(
        self, prompt: str, reasoning_summary: str | None, start_time: float
    ) -> ProviderResult:
        """Execute the actual API call with optional reasoning summary."""
        try:
            client = self._get_client()
            model = self.get_model()

            # Phase: CONNECTING
            self._phase_update(ProviderPhase.CONNECTING, f"Connecting to {model}")

            # Build request parameters
            request_params: dict[str, Any] = {
                "model": model,
                "background": True,
                "tools": [{"type": "web_search_preview"}],
                "input": [
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}],
                    }
                ],
            }

            # Only add reasoning if summary is specified
            if reasoning_summary:
                request_params["reasoning"] = {"summary": reasoning_summary}

            # Phase: RESEARCHING
            self._phase_update(ProviderPhase.RESEARCHING, "Initiating deep research")

            response = client.responses.create(**request_params)

            response_id = response.id
            result = await self._poll_for_completion(
                client, response_id, start_time, reasoning_summary
            )
            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            # Phase: FAILED
            self._phase_update(ProviderPhase.FAILED, error_msg[:50])

            if "timeout" in error_msg.lower():
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.TIMEOUT,
                    error=f"Request timed out after {self.config.timeout_seconds}s",
                    duration_seconds=duration,
                )

            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.FAILED,
                error=error_msg,
                duration_seconds=duration,
            )

    async def _poll_for_completion(
        self, client: Any, response_id: str, start_time: float, reasoning_summary: str | None
    ) -> ProviderResult:
        """Poll for background response completion."""
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
                response = client.responses.retrieve(response_id)

                if response.status == "completed":
                    # Phase: PROCESSING
                    self._phase_update(ProviderPhase.PROCESSING, "Extracting content")
                    content = self._extract_content(response)
                    duration = time.time() - start_time

                    # Phase: COMPLETED
                    self._phase_update(ProviderPhase.COMPLETED, f"Done ({duration:.1f}s)")

                    # Extract tokens_used safely - usage may be an object or dict
                    usage = getattr(response, "usage", None)
                    tokens_used = None
                    if usage is not None:
                        if hasattr(usage, "total_tokens"):
                            tokens_used = usage.total_tokens
                        elif isinstance(usage, dict):
                            tokens_used = usage.get("total_tokens")
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.SUCCESS,
                        content=content,
                        duration_seconds=duration,
                        tokens_used=tokens_used,
                        metadata={
                            "model": self.get_model(),
                            "reasoning_summary": reasoning_summary or "disabled",
                            "response_id": response_id,
                        },
                    )
                elif response.status == "failed":
                    error_msg = getattr(response, "error", "Unknown error")
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

    def _extract_content(self, response: Any) -> str:
        """Extract content from completed response.

        OpenAI deep research returns output as a list containing:
        - ResponseReasoningItem (reasoning, may have content=None)
        - ResponseOutputMessage (final output, content is list of ResponseOutputText)

        We extract text from ResponseOutputText objects nested in content lists.
        """
        if hasattr(response, "output"):
            if isinstance(response.output, str):
                return response.output
            if isinstance(response.output, list):
                parts = []
                for item in response.output:
                    # Check for content attribute that contains ResponseOutputText list
                    if hasattr(item, "content") and item.content is not None:
                        content = item.content
                        if isinstance(content, list):
                            # Iterate through content items (ResponseOutputText objects)
                            for content_item in content:
                                if hasattr(content_item, "text") and content_item.text is not None:
                                    parts.append(str(content_item.text))
                        elif isinstance(content, str):
                            parts.append(content)
                    # Direct text attribute (less common but handle it)
                    elif hasattr(item, "text") and item.text is not None:
                        parts.append(str(item.text))
                    elif isinstance(item, str):
                        parts.append(item)
                if parts:
                    return "\n\n".join(parts)
        return str(response)
