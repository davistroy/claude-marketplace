"""Anthropic Claude provider for extended thinking research."""

import os
import time
from collections.abc import Callable
from typing import Any

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderPhase, ProviderResult, ProviderStatus
from research_orchestrator.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider using extended thinking."""

    DEFAULT_MODEL = "claude-opus-4-5-20251101"

    @classmethod
    def get_model(cls) -> str:
        """Get model from environment or use default."""
        return os.getenv("ANTHROPIC_MODEL", cls.DEFAULT_MODEL)

    def __init__(
        self,
        config: ProviderConfig,
        depth: Depth,
        on_status_update: Callable[[str, str], None] | None = None,
    ) -> None:
        """Initialize the Anthropic provider."""
        super().__init__(config, depth, on_status_update)
        self._client: Any = None

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "claude"

    def _get_client(self) -> Any:
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError as err:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                ) from err
        return self._client

    async def execute(self, prompt: str) -> ProviderResult:
        """Execute research using Claude with extended thinking.

        Claude's extended thinking is synchronous, but we wrap it in async
        for consistency with other providers.
        """
        self._validate_api_key()
        start_time = time.time()

        try:
            # Phase: INITIALIZING
            self._phase_update(ProviderPhase.INITIALIZING, "Creating Anthropic client")
            client = self._get_client()
            budget_tokens = self.depth.get_anthropic_budget()

            # max_tokens MUST be greater than budget_tokens per API requirements
            # Add buffer for the actual response text after thinking
            max_tokens = budget_tokens + 16000

            model = self.get_model()

            # Phase: CONNECTING
            self._phase_update(ProviderPhase.CONNECTING, f"Opening stream to {model}")

            # Phase: THINKING
            self._phase_update(
                ProviderPhase.THINKING, f"Extended thinking ({budget_tokens:,} token budget)"
            )

            # Use streaming for extended thinking to avoid 10-minute timeout
            # on long-running requests (especially with large budget_tokens)
            # See: https://github.com/anthropics/anthropic-sdk-python#long-requests
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                thinking={
                    "type": "enabled",
                    "budget_tokens": budget_tokens,
                },
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                response = stream.get_final_message()

            # Phase: PROCESSING
            self._phase_update(ProviderPhase.PROCESSING, "Extracting content")
            content = self._extract_content(response)
            duration = time.time() - start_time

            # Phase: COMPLETED
            self._phase_update(ProviderPhase.COMPLETED, f"Done ({duration:.1f}s)")

            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.SUCCESS,
                content=content,
                duration_seconds=duration,
                tokens_used=response.usage.output_tokens if hasattr(response, "usage") else None,
                metadata={
                    "model": model,
                    "budget_tokens": budget_tokens,
                    "stop_reason": response.stop_reason
                    if hasattr(response, "stop_reason")
                    else None,
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            # Phase: FAILED
            self._phase_update(ProviderPhase.FAILED, str(e)[:50])
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.FAILED,
                error=str(e),
                duration_seconds=duration,
            )

    def _extract_content(self, response: Any) -> str:
        """Extract text content from response, filtering out thinking blocks."""
        content_parts = []
        for block in response.content:
            if hasattr(block, "type"):
                if block.type == "text":
                    content_parts.append(block.text)
        return "\n\n".join(content_parts)
