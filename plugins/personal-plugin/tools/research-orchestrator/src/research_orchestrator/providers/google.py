"""Google Gemini provider for deep research agent."""

import asyncio
import time
from typing import Any

import httpx

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderResult, ProviderStatus
from research_orchestrator.providers.base import BaseProvider


class GoogleProvider(BaseProvider):
    """Google Gemini provider using deep research agent."""

    AGENT = "deep-research-pro-preview-12-2025"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    POLL_INTERVAL = 5.0  # seconds between status checks

    def __init__(self, config: ProviderConfig, depth: Depth) -> None:
        """Initialize the Google provider."""
        super().__init__(config, depth)

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "gemini"

    async def execute(self, prompt: str) -> ProviderResult:
        """Execute research using Gemini deep research agent.

        Gemini deep research runs in background mode and requires polling.
        """
        self._validate_api_key()
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/interactions",
                    headers={"x-goog-api-key": self.config.api_key},
                    json={
                        "input": prompt,
                        "agent": self.AGENT,
                        "background": True,
                        "agent_config": {
                            "type": "deep-research",
                            "thinking_summaries": "auto",
                            "thinking_level": self.depth.get_gemini_thinking_level(),
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()

                interaction_id = data.get("name") or data.get("id")
                if not interaction_id:
                    raise ValueError("No interaction ID in response")

                result = await self._poll_for_completion(interaction_id, start_time)
                return result

        except httpx.TimeoutException:
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.TIMEOUT,
                error=f"Request timed out after {self.config.timeout_seconds}s",
                duration_seconds=time.time() - start_time,
            )
        except Exception as e:
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.FAILED,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def _poll_for_completion(
        self, interaction_id: str, start_time: float
    ) -> ProviderResult:
        """Poll for background interaction completion."""
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                    response = await client.get(
                        f"{self.BASE_URL}/{interaction_id}",
                        headers={"x-goog-api-key": self.config.api_key},
                    )
                    response.raise_for_status()
                    data = response.json()

                    status = data.get("status", "").lower()

                    if status == "completed" or data.get("done"):
                        content = self._extract_content(data)
                        return ProviderResult(
                            provider=self.name,
                            status=ProviderStatus.SUCCESS,
                            content=content,
                            duration_seconds=time.time() - start_time,
                            metadata={
                                "agent": self.AGENT,
                                "thinking_level": self.depth.get_gemini_thinking_level(),
                                "interaction_id": interaction_id,
                            },
                        )
                    elif status in ("failed", "error"):
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        return ProviderResult(
                            provider=self.name,
                            status=ProviderStatus.FAILED,
                            error=error_msg,
                            duration_seconds=time.time() - start_time,
                        )

                    await asyncio.sleep(self.POLL_INTERVAL)

                except httpx.HTTPStatusError as e:
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.FAILED,
                        error=f"HTTP error: {e.response.status_code}",
                        duration_seconds=time.time() - start_time,
                    )
                except Exception as e:
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.FAILED,
                        error=f"Polling error: {e}",
                        duration_seconds=time.time() - start_time,
                    )

    def _extract_content(self, data: dict[str, Any]) -> str:
        """Extract content from completed interaction response."""
        if "result" in data:
            result = data["result"]
            if isinstance(result, str):
                return result
            if isinstance(result, dict):
                if "text" in result:
                    return result["text"]
                if "content" in result:
                    return result["content"]

        if "response" in data:
            response = data["response"]
            if isinstance(response, str):
                return response
            if isinstance(response, dict):
                candidates = response.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return "\n\n".join(p.get("text", "") for p in parts if "text" in p)

        return str(data)
