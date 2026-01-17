"""OpenAI provider for deep research with web search."""

import asyncio
import os
import time
from typing import Any

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderResult, ProviderStatus
from research_orchestrator.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI provider using o3 deep research model with web search."""

    DEFAULT_MODEL = "o3-deep-research-2025-06-26"
    POLL_INTERVAL = 5.0  # seconds between status checks

    @classmethod
    def get_model(cls) -> str:
        """Get model from environment or use default."""
        return os.getenv("OPENAI_MODEL", cls.DEFAULT_MODEL)

    def __init__(self, config: ProviderConfig, depth: Depth) -> None:
        """Initialize the OpenAI provider."""
        super().__init__(config, depth)
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

        try:
            client = self._get_client()
            reasoning_summary = self.depth.get_openai_reasoning_summary()

            # Deep research requires structured input with roles
            # and uses web_search_preview tool type
            model = self.get_model()
            response = client.responses.create(
                model=model,
                background=True,
                tools=[{"type": "web_search_preview"}],
                reasoning={"summary": reasoning_summary},
                input=[
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}],
                    }
                ],
            )

            response_id = response.id
            result = await self._poll_for_completion(client, response_id, start_time)
            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

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
        self, client: Any, response_id: str, start_time: float
    ) -> ProviderResult:
        """Poll for background response completion."""
        while True:
            elapsed = time.time() - start_time
            if elapsed > self.config.timeout_seconds:
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.TIMEOUT,
                    error=f"Request timed out after {self.config.timeout_seconds}s",
                    duration_seconds=elapsed,
                )

            try:
                response = client.responses.retrieve(response_id)

                if response.status == "completed":
                    content = self._extract_content(response)
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.SUCCESS,
                        content=content,
                        duration_seconds=time.time() - start_time,
                        tokens_used=getattr(response, "usage", {}).get("total_tokens"),
                        metadata={
                            "model": self.get_model(),
                            "reasoning_summary": self.depth.get_openai_reasoning_summary(),
                            "response_id": response_id,
                        },
                    )
                elif response.status == "failed":
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.FAILED,
                        error=getattr(response, "error", "Unknown error"),
                        duration_seconds=time.time() - start_time,
                    )

                await asyncio.sleep(self.POLL_INTERVAL)

            except Exception as e:
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.FAILED,
                    error=f"Polling error: {e}",
                    duration_seconds=time.time() - start_time,
                )

    def _extract_content(self, response: Any) -> str:
        """Extract content from completed response."""
        if hasattr(response, "output"):
            if isinstance(response.output, str):
                return response.output
            if isinstance(response.output, list):
                parts = []
                for item in response.output:
                    if hasattr(item, "content"):
                        parts.append(item.content)
                    elif isinstance(item, str):
                        parts.append(item)
                return "\n\n".join(parts)
        return str(response)
