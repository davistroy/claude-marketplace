"""Main orchestrator for parallel research execution."""

import asyncio
import time
from typing import Callable

from research_orchestrator.config import Depth, ProviderConfig, ResearchConfig
from research_orchestrator.models import ProviderResult, ProviderStatus, ResearchOutput
from research_orchestrator.providers.anthropic import AnthropicProvider
from research_orchestrator.providers.base import BaseProvider
from research_orchestrator.providers.google import GoogleProvider
from research_orchestrator.providers.openai import OpenAIProvider


class ResearchOrchestrator:
    """Orchestrator for parallel deep research across multiple LLM providers."""

    def __init__(
        self,
        on_status_update: Callable[[str, str], None] | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            on_status_update: Optional callback for status updates.
                Called with (provider_name, status_message).
        """
        self._on_status_update = on_status_update

    def _get_provider(self, config: ProviderConfig, depth: Depth) -> BaseProvider:
        """Get the appropriate provider instance."""
        providers: dict[str, type[BaseProvider]] = {
            "claude": AnthropicProvider,
            "openai": OpenAIProvider,
            "gemini": GoogleProvider,
        }

        provider_class = providers.get(config.name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {config.name}")

        return provider_class(config, depth, self._on_status_update)

    def _update_status(self, provider: str, message: str) -> None:
        """Send status update if callback is configured."""
        if self._on_status_update:
            self._on_status_update(provider, message)

    async def execute(self, config: ResearchConfig) -> ResearchOutput:
        """Execute parallel research across configured providers.

        Args:
            config: Research configuration including prompt, sources, and depth.

        Returns:
            ResearchOutput containing results from all providers.
        """
        start_time = time.time()

        missing_keys = config.get_missing_api_keys()
        if missing_keys:
            results = []
            for key in missing_keys:
                provider_name = {
                    "ANTHROPIC_API_KEY": "claude",
                    "OPENAI_API_KEY": "openai",
                    "GOOGLE_API_KEY": "gemini",
                }[key]
                results.append(
                    ProviderResult(
                        provider=provider_name,
                        status=ProviderStatus.FAILED,
                        error=f"Missing API key: {key}",
                    )
                )
            return ResearchOutput(
                prompt=config.prompt,
                results=results,
                depth=config.depth.value,
                total_duration_seconds=time.time() - start_time,
            )

        provider_configs = config.get_provider_configs()
        available_configs = [c for c in provider_configs if c.is_available]

        if not available_configs:
            return ResearchOutput(
                prompt=config.prompt,
                results=[
                    ProviderResult(
                        provider="none",
                        status=ProviderStatus.FAILED,
                        error="No providers available (all API keys missing)",
                    )
                ],
                depth=config.depth.value,
                total_duration_seconds=time.time() - start_time,
            )

        tasks = []
        for provider_config in available_configs:
            provider = self._get_provider(provider_config, config.depth)
            self._update_status(provider.name, "Starting...")
            tasks.append(self._execute_with_status(provider, config.prompt))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                provider_name = available_configs[i].name
                processed_results.append(
                    ProviderResult(
                        provider=provider_name,
                        status=ProviderStatus.FAILED,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return ResearchOutput(
            prompt=config.prompt,
            results=processed_results,
            depth=config.depth.value,
            total_duration_seconds=time.time() - start_time,
        )

    async def _execute_with_status(
        self, provider: BaseProvider, prompt: str
    ) -> ProviderResult:
        """Execute provider with status updates."""
        self._update_status(provider.name, "Executing...")
        try:
            result = await provider.execute(prompt)
            status_msg = "Completed" if result.is_success else f"Failed: {result.error}"
            self._update_status(provider.name, status_msg)
            return result
        except Exception as e:
            self._update_status(provider.name, f"Error: {e}")
            raise

    async def check_providers(self, sources: list[str] | None = None) -> dict[str, bool]:
        """Check which providers are available (have API keys configured).

        Args:
            sources: List of providers to check. If None, checks all.

        Returns:
            Dict mapping provider name to availability status.
        """
        if sources is None:
            sources = ["claude", "openai", "gemini"]

        config = ResearchConfig(prompt="test", sources=sources)  # type: ignore
        provider_configs = config.get_provider_configs()

        return {pc.name: pc.is_available for pc in provider_configs}
