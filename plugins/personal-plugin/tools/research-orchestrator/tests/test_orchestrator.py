"""Tests for research orchestrator."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from research_orchestrator.config import Depth, ResearchConfig
from research_orchestrator.models import ProviderResult, ProviderStatus
from research_orchestrator.orchestrator import ResearchOrchestrator


@pytest.fixture
def orchestrator():
    """Create an orchestrator instance."""
    return ResearchOrchestrator()


class TestResearchOrchestrator:
    """Tests for ResearchOrchestrator."""

    @pytest.mark.asyncio
    async def test_execute_with_missing_keys(self, orchestrator):
        """Test execution when all API keys are missing."""
        with patch.dict(os.environ, {}, clear=True):
            config = ResearchConfig(
                prompt="test",
                sources=["claude", "openai"],
            )
            output = await orchestrator.execute(config)

            assert output.success_count == 0
            assert len(output.failed_results) == 2
            assert all("Missing API key" in r.error for r in output.results)

    @pytest.mark.asyncio
    async def test_check_providers_all_missing(self, orchestrator):
        """Test provider check when all keys are missing."""
        with patch.dict(os.environ, {}, clear=True):
            availability = await orchestrator.check_providers()

            assert availability["claude"] is False
            assert availability["openai"] is False
            assert availability["gemini"] is False

    @pytest.mark.asyncio
    async def test_check_providers_partial(self, orchestrator):
        """Test provider check with some keys configured."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}, clear=True):
            availability = await orchestrator.check_providers()

            assert availability["claude"] is True
            assert availability["openai"] is False
            assert availability["gemini"] is False

    @pytest.mark.asyncio
    async def test_status_callback(self):
        """Test that status callback is called."""
        status_updates = []

        def callback(provider: str, message: str):
            status_updates.append((provider, message))

        orchestrator = ResearchOrchestrator(on_status_update=callback)

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}, clear=True):
            with patch(
                "research_orchestrator.providers.anthropic.AnthropicProvider.execute",
                new_callable=AsyncMock,
                return_value=ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="test",
                ),
            ):
                config = ResearchConfig(prompt="test", sources=["claude"])
                await orchestrator.execute(config)

                assert len(status_updates) >= 2
                providers_updated = [p for p, _ in status_updates]
                assert "claude" in providers_updated


class TestProviderSelection:
    """Tests for provider selection and initialization."""

    def test_get_unknown_provider_raises(self, orchestrator):
        """Test that unknown provider raises ValueError."""
        from research_orchestrator.config import ProviderConfig

        config = ProviderConfig(name="unknown")  # type: ignore
        with pytest.raises(ValueError, match="Unknown provider"):
            orchestrator._get_provider(config, Depth.STANDARD)
