"""OpenAI GPT provider for deep research with web search."""

import asyncio
import time
from typing import Any

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderResult, ProviderStatus
from research_orchestrator.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider using deep research mode with web search."""

    MODEL = "gpt-5.2-pro"
    POLL_INTERVAL = 5.0  # seconds between status checks

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
        """Execute research using OpenAI deep research with web search.

        OpenAI deep research runs in background mode and requires polling.
        """
        self._validate_api_key()
        start_time = time.time()

        try:
            client = self._get_client()
            effort = self.depth.get_openai_effort()

            response = client.responses.create(
                model=self.MODEL,
                background=True,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                reasoning={"effort": effort},
                input=prompt,
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
                            "model": self.MODEL,
                            "effort": self.depth.get_openai_effort(),
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
