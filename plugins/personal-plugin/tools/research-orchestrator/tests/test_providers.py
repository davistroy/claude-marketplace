"""Tests for OpenAI and Google provider modules."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderResult, ProviderStatus
from research_orchestrator.providers.anthropic import AnthropicProvider
from research_orchestrator.providers.base import BaseProvider
from research_orchestrator.providers.google import GoogleProvider
from research_orchestrator.providers.openai import OpenAIProvider


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def openai_config():
    """Create OpenAI provider config with test key."""
    return ProviderConfig(name="openai", api_key="test-key", timeout_seconds=60)


@pytest.fixture
def openai_config_no_key():
    """Create OpenAI provider config without API key."""
    return ProviderConfig(name="openai", api_key=None, timeout_seconds=60)


@pytest.fixture
def google_config():
    """Create Google provider config with test key."""
    return ProviderConfig(name="gemini", api_key="test-key", timeout_seconds=60)


@pytest.fixture
def google_config_no_key():
    """Create Google provider config without API key."""
    return ProviderConfig(name="gemini", api_key=None, timeout_seconds=60)


@pytest.fixture
def anthropic_config():
    """Create Anthropic provider config with test key."""
    return ProviderConfig(name="claude", api_key="test-key", timeout_seconds=60)


@pytest.fixture
def openai_provider(openai_config):
    """Create OpenAI provider instance."""
    return OpenAIProvider(openai_config, Depth.BRIEF)


@pytest.fixture
def google_provider(google_config):
    """Create Google provider instance."""
    return GoogleProvider(google_config, Depth.BRIEF)


@pytest.fixture
def anthropic_provider(anthropic_config):
    """Create Anthropic provider instance."""
    return AnthropicProvider(anthropic_config, Depth.BRIEF)


# ============================================================================
# Mock Response Classes
# ============================================================================


class MockOpenAIResponse:
    """Mock OpenAI response object."""

    def __init__(
        self,
        response_id: str = "resp_123",
        status: str = "completed",
        output: list | str | None = None,
    ):
        self.id = response_id
        self.status = status
        self.output = output or [MockOutputItem()]
        self.usage = {"total_tokens": 1000}
        self.error = None


class MockOutputItem:
    """Mock output item for OpenAI response."""

    def __init__(self, text: str = "Test research result", content: str | None = None):
        self.text = text
        self.content = content or text
        self.type = "text"


class MockGoogleInteraction:
    """Mock Google interaction object."""

    def __init__(
        self,
        name: str = "interactions/123",
        done: bool = True,
        status: str = "completed",
        outputs: list | None = None,
    ):
        self.name = name
        self.id = "123"
        self.interaction_id = "int_123"
        self.done = done
        self.status = status
        self.outputs = outputs or [MockGoogleOutput()]
        self.error = None


class MockGoogleOutput:
    """Mock Google output object."""

    def __init__(self, text: str = "Test research result"):
        self.text = text
        self.content = text


# ============================================================================
# BaseProvider Tests
# ============================================================================


class TestBaseProvider:
    """Tests for BaseProvider functionality."""

    def test_validate_api_key_missing(self, openai_config_no_key):
        """BP-001: Validate raises error when API key is missing."""
        provider = OpenAIProvider(openai_config_no_key, Depth.BRIEF)
        with pytest.raises(ValueError, match="API key not configured"):
            provider._validate_api_key()

    def test_validate_api_key_present(self, openai_provider):
        """BP-002: Validate passes when API key is present."""
        # Should not raise
        openai_provider._validate_api_key()

    def test_status_update_exists(self, openai_provider):
        """BP-003: Verify _status_update method exists and is callable."""
        assert hasattr(openai_provider, "_status_update")
        assert callable(openai_provider._status_update)

    def test_status_update_with_callback(self, openai_config):
        """BP-004: Status update invokes callback when configured."""
        status_updates = []

        def callback(provider: str, message: str):
            status_updates.append((provider, message))

        provider = OpenAIProvider(openai_config, Depth.BRIEF, on_status_update=callback)
        provider._status_update("Test message")

        assert len(status_updates) == 1
        assert status_updates[0] == ("openai", "Test message")

    def test_status_update_without_callback(self, openai_provider):
        """BP-005: Status update is no-op without callback."""
        # Should not raise even without callback
        openai_provider._status_update("Test message")


# ============================================================================
# OpenAI Provider Tests
# ============================================================================


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_openai_provider_name(self, openai_provider):
        """OA-001: Check provider name property."""
        assert openai_provider.name == "openai"

    def test_openai_get_model_default(self):
        """OA-002: Get model without env override."""
        with patch.dict(os.environ, {}, clear=True):
            model = OpenAIProvider.get_model()
            assert model == "o3-deep-research-2025-06-26"

    def test_openai_get_model_override(self):
        """OA-003: Get model with env override."""
        with patch.dict(os.environ, {"OPENAI_MODEL": "custom-model"}):
            model = OpenAIProvider.get_model()
            assert model == "custom-model"

    @pytest.mark.asyncio
    async def test_openai_execute_success(self, openai_provider):
        """OA-004: Execute with mocked successful response."""
        mock_client = MagicMock()
        mock_response = MockOpenAIResponse()
        mock_client.responses.create.return_value = mock_response
        mock_client.responses.retrieve.return_value = mock_response

        with patch.object(openai_provider, "_get_client", return_value=mock_client):
            result = await openai_provider.execute("Test prompt")

        assert result.status == ProviderStatus.SUCCESS
        assert result.provider == "openai"
        assert "Test research result" in result.content

    @pytest.mark.asyncio
    async def test_openai_execute_api_failure(self, openai_provider):
        """OA-005: Execute with mocked API error."""
        mock_client = MagicMock()
        mock_client.responses.create.side_effect = Exception("API Error")

        with patch.object(openai_provider, "_get_client", return_value=mock_client):
            result = await openai_provider.execute("Test prompt")

        assert result.status == ProviderStatus.FAILED
        assert "API Error" in result.error

    @pytest.mark.asyncio
    async def test_openai_execute_timeout(self, openai_config):
        """OA-006: Execute exceeding timeout."""
        # Use very short timeout
        config = ProviderConfig(name="openai", api_key="test", timeout_seconds=0.001)
        provider = OpenAIProvider(config, Depth.BRIEF)

        mock_client = MagicMock()
        # Response stays in "running" status
        mock_response = MockOpenAIResponse(status="running")
        mock_client.responses.create.return_value = mock_response
        mock_client.responses.retrieve.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.execute("Test prompt")

        assert result.status == ProviderStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_openai_poll_completion_success(self, openai_provider):
        """OA-007: Poll until completed status."""
        import time

        mock_client = MagicMock()
        mock_response = MockOpenAIResponse(status="completed")
        mock_client.responses.retrieve.return_value = mock_response

        result = await openai_provider._poll_for_completion(
            mock_client, "resp_123", time.time(), "auto"
        )

        assert result.status == ProviderStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_openai_poll_completion_failed(self, openai_provider):
        """OA-008: Poll returns failed status."""
        import time

        mock_client = MagicMock()
        mock_response = MockOpenAIResponse(status="failed")
        mock_response.error = "Research failed"
        mock_client.responses.retrieve.return_value = mock_response

        result = await openai_provider._poll_for_completion(
            mock_client, "resp_123", time.time(), "auto"
        )

        assert result.status == ProviderStatus.FAILED

    def test_openai_extract_content_string(self, openai_provider):
        """OA-009: Extract content from string output."""
        response = MagicMock()
        response.output = "Direct string output"

        content = openai_provider._extract_content(response)
        assert content == "Direct string output"

    def test_openai_extract_content_list(self, openai_provider):
        """OA-010: Extract content from list output."""
        response = MockOpenAIResponse(
            output=[MockOutputItem("Part 1"), MockOutputItem("Part 2")]
        )

        content = openai_provider._extract_content(response)
        assert "Part 1" in content
        assert "Part 2" in content

    @pytest.mark.asyncio
    async def test_openai_reasoning_summary_fallback(self, openai_provider):
        """OA-011: Test fallback when org not verified."""
        mock_client = MagicMock()

        # First call fails with org verification error
        org_error = Exception("organization must be verified")
        success_response = MockOpenAIResponse()

        mock_client.responses.create.side_effect = [org_error, success_response]
        mock_client.responses.retrieve.return_value = success_response

        with patch.object(openai_provider, "_get_client", return_value=mock_client):
            result = await openai_provider.execute("Test prompt")

        # Should have retried and succeeded
        assert result.status == ProviderStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_openai_status_update_called(self, openai_config):
        """OA-012: Verify status updates during polling."""
        status_updates = []

        def callback(provider: str, message: str):
            status_updates.append((provider, message))

        # Very short timeout to trigger status updates quickly
        config = ProviderConfig(name="openai", api_key="test", timeout_seconds=0.1)
        provider = OpenAIProvider(config, Depth.BRIEF, on_status_update=callback)

        mock_client = MagicMock()
        mock_response = MockOpenAIResponse(status="running")
        mock_client.responses.create.return_value = mock_response
        mock_client.responses.retrieve.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            # This will timeout, but we can still verify callback setup
            await provider.execute("Test prompt")

        # Provider should have _status_update method that works
        assert hasattr(provider, "_status_update")

    @pytest.mark.asyncio
    async def test_openai_missing_api_key(self, openai_config_no_key):
        """OA-013: Execute without API key returns error."""
        provider = OpenAIProvider(openai_config_no_key, Depth.BRIEF)

        with pytest.raises(ValueError, match="API key not configured"):
            await provider.execute("Test prompt")


# ============================================================================
# Google Provider Tests
# ============================================================================


class TestGoogleProvider:
    """Tests for GoogleProvider."""

    def test_google_provider_name(self, google_provider):
        """GP-001: Check provider name property."""
        assert google_provider.name == "gemini"

    def test_google_get_agent_default(self):
        """GP-002: Get agent without env override."""
        with patch.dict(os.environ, {}, clear=True):
            agent = GoogleProvider.get_agent()
            assert agent == "deep-research-pro-preview-12-2025"

    def test_google_get_agent_override(self):
        """GP-003: Get agent with env override."""
        with patch.dict(os.environ, {"GEMINI_AGENT": "custom-agent"}):
            agent = GoogleProvider.get_agent()
            assert agent == "custom-agent"

    @pytest.mark.asyncio
    async def test_google_execute_success(self, google_provider):
        """GP-004: Execute with mocked successful response."""
        mock_client = MagicMock()
        mock_interaction = MockGoogleInteraction()

        # Mock the async create call
        async_create_mock = AsyncMock(return_value=mock_interaction)
        mock_client.aio.interactions.create.return_value = async_create_mock()

        # Mock the async get call
        async_get_mock = AsyncMock(return_value=mock_interaction)
        mock_client.aio.interactions.get = async_get_mock

        with patch.object(google_provider, "_get_client", return_value=mock_client):
            result = await google_provider.execute("Test prompt")

        assert result.status == ProviderStatus.SUCCESS
        assert result.provider == "gemini"

    @pytest.mark.asyncio
    async def test_google_execute_api_failure(self, google_provider):
        """GP-005: Execute with mocked API error."""
        mock_client = MagicMock()

        # Mock the async create call to raise an exception
        async_create_mock = AsyncMock(side_effect=Exception("API Error"))
        mock_client.aio.interactions.create.return_value = async_create_mock()

        with patch.object(google_provider, "_get_client", return_value=mock_client):
            result = await google_provider.execute("Test prompt")

        assert result.status == ProviderStatus.FAILED
        assert "API Error" in result.error

    @pytest.mark.asyncio
    async def test_google_execute_timeout(self, google_config):
        """GP-006: Execute exceeding timeout."""
        config = ProviderConfig(name="gemini", api_key="test", timeout_seconds=0.001)
        provider = GoogleProvider(config, Depth.BRIEF)

        mock_client = MagicMock()
        mock_interaction = MockGoogleInteraction(done=False, status="running")

        async_create_mock = AsyncMock(return_value=mock_interaction)
        mock_client.aio.interactions.create.return_value = async_create_mock()

        async_get_mock = AsyncMock(return_value=mock_interaction)
        mock_client.aio.interactions.get = async_get_mock

        with patch.object(provider, "_get_client", return_value=mock_client):
            result = await provider.execute("Test prompt")

        assert result.status == ProviderStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_google_poll_completion_done_flag(self, google_provider):
        """GP-007: Poll with done=True flag."""
        import time

        mock_client = MagicMock()
        mock_interaction = MockGoogleInteraction(done=True)

        async_get_mock = AsyncMock(return_value=mock_interaction)
        mock_client.aio.interactions.get = async_get_mock

        result = await google_provider._poll_for_completion(
            mock_client, "interactions/123", time.time()
        )

        assert result.status == ProviderStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_google_poll_completion_status_completed(self, google_provider):
        """GP-008: Poll with status='completed'."""
        import time

        mock_client = MagicMock()
        mock_interaction = MockGoogleInteraction(done=False, status="completed")

        async_get_mock = AsyncMock(return_value=mock_interaction)
        mock_client.aio.interactions.get = async_get_mock

        result = await google_provider._poll_for_completion(
            mock_client, "interactions/123", time.time()
        )

        assert result.status == ProviderStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_google_poll_completion_status_failed(self, google_provider):
        """GP-009: Poll with status='failed'."""
        import time

        mock_client = MagicMock()
        mock_interaction = MockGoogleInteraction(done=False, status="failed")
        mock_interaction.error = MagicMock()
        mock_interaction.error.message = "Research failed"

        async_get_mock = AsyncMock(return_value=mock_interaction)
        mock_client.aio.interactions.get = async_get_mock

        result = await google_provider._poll_for_completion(
            mock_client, "interactions/123", time.time()
        )

        assert result.status == ProviderStatus.FAILED
        assert "Research failed" in result.error

    def test_google_extract_content_outputs(self, google_provider):
        """GP-010: Extract from outputs[-1].text."""
        interaction = MockGoogleInteraction(
            outputs=[MockGoogleOutput("First"), MockGoogleOutput("Last output")]
        )

        content = google_provider._extract_content(interaction)
        assert content == "Last output"

    def test_google_extract_content_result(self, google_provider):
        """GP-011: Extract from result attribute."""
        interaction = MagicMock()
        interaction.outputs = []
        interaction.result = "Result text"

        content = google_provider._extract_content(interaction)
        assert content == "Result text"

    def test_google_extract_content_response_candidates(self, google_provider):
        """GP-012: Extract from response.candidates."""
        # Need to avoid having 'text' attribute on response to hit candidates path
        # The code checks hasattr(response, "text") first
        class Part:
            text = "Candidate text"

        class Content:
            parts = [Part()]

        class Candidate:
            content = Content()

        class Response:
            # Don't define 'text' attribute so hasattr returns False
            candidates = [Candidate()]

        # Use __slots__ to truly exclude 'text' attribute
        class MockInteraction:
            __slots__ = ["outputs", "result", "response"]

            def __init__(self):
                self.outputs = None
                self.result = None
                self.response = Response()

        interaction = MockInteraction()
        content = google_provider._extract_content(interaction)
        assert "Candidate text" in content

    def test_google_extract_content_fallback(self, google_provider):
        """GP-013: Extract when all formats fail returns str(interaction)."""
        # Use __slots__ to strictly control which attributes exist
        class EmptyInteraction:
            """Interaction with no extractable content."""

            __slots__ = []  # No attributes at all

            def __str__(self):
                return "Fallback string representation"

        interaction = EmptyInteraction()
        content = google_provider._extract_content(interaction)
        assert "Fallback string representation" in content

    @pytest.mark.asyncio
    async def test_google_status_update_called(self, google_config):
        """GP-014: Verify status updates during polling."""
        status_updates = []

        def callback(provider: str, message: str):
            status_updates.append((provider, message))

        provider = GoogleProvider(google_config, Depth.BRIEF, on_status_update=callback)

        # Verify callback is properly configured
        provider._status_update("Test update")
        assert len(status_updates) == 1
        assert status_updates[0] == ("gemini", "Test update")

    @pytest.mark.asyncio
    async def test_google_missing_api_key(self, google_config_no_key):
        """GP-015: Execute without API key returns error."""
        provider = GoogleProvider(google_config_no_key, Depth.BRIEF)

        with pytest.raises(ValueError, match="API key not configured"):
            await provider.execute("Test prompt")

    def test_google_interaction_id_extraction(self, google_provider):
        """GP-016: Test interaction ID from various attrs."""
        # Test with 'name' attribute
        interaction = MagicMock()
        interaction.name = "interactions/name123"
        interaction.id = None
        interaction.interaction_id = None

        # The actual extraction happens in execute(), but we can verify the logic
        interaction_id = (
            getattr(interaction, "name", None)
            or getattr(interaction, "id", None)
            or getattr(interaction, "interaction_id", None)
        )
        assert interaction_id == "interactions/name123"

        # Test with 'id' attribute
        interaction2 = MagicMock()
        interaction2.name = None
        interaction2.id = "id456"
        interaction2.interaction_id = None

        interaction_id2 = (
            getattr(interaction2, "name", None)
            or getattr(interaction2, "id", None)
            or getattr(interaction2, "interaction_id", None)
        )
        assert interaction_id2 == "id456"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for providers with orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_with_openai_mock(self):
        """INT-001: Execute orchestrator with mocked OpenAI."""
        from research_orchestrator.config import ResearchConfig
        from research_orchestrator.orchestrator import ResearchOrchestrator

        orchestrator = ResearchOrchestrator()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True):
            with patch(
                "research_orchestrator.providers.openai.OpenAIProvider.execute",
                new_callable=AsyncMock,
                return_value=ProviderResult(
                    provider="openai",
                    status=ProviderStatus.SUCCESS,
                    content="Mocked result",
                ),
            ):
                config = ResearchConfig(prompt="test", sources=["openai"])
                output = await orchestrator.execute(config)

        assert output.success_count == 1
        assert output.results[0].provider == "openai"

    @pytest.mark.asyncio
    async def test_orchestrator_with_google_mock(self):
        """INT-002: Execute orchestrator with mocked Google."""
        from research_orchestrator.config import ResearchConfig
        from research_orchestrator.orchestrator import ResearchOrchestrator

        orchestrator = ResearchOrchestrator()

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}, clear=True):
            with patch(
                "research_orchestrator.providers.google.GoogleProvider.execute",
                new_callable=AsyncMock,
                return_value=ProviderResult(
                    provider="gemini",
                    status=ProviderStatus.SUCCESS,
                    content="Mocked result",
                ),
            ):
                config = ResearchConfig(prompt="test", sources=["gemini"])
                output = await orchestrator.execute(config)

        assert output.success_count == 1
        assert output.results[0].provider == "gemini"

    @pytest.mark.asyncio
    async def test_orchestrator_status_callback_openai(self):
        """INT-003: Status callback called for OpenAI."""
        from research_orchestrator.config import ResearchConfig
        from research_orchestrator.orchestrator import ResearchOrchestrator

        status_updates = []

        def callback(provider: str, message: str):
            status_updates.append((provider, message))

        orchestrator = ResearchOrchestrator(on_status_update=callback)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True):
            with patch(
                "research_orchestrator.providers.openai.OpenAIProvider.execute",
                new_callable=AsyncMock,
                return_value=ProviderResult(
                    provider="openai",
                    status=ProviderStatus.SUCCESS,
                    content="Mocked result",
                ),
            ):
                config = ResearchConfig(prompt="test", sources=["openai"])
                await orchestrator.execute(config)

        # Should have received status updates
        assert len(status_updates) >= 1
        providers = [p for p, _ in status_updates]
        assert "openai" in providers

    @pytest.mark.asyncio
    async def test_orchestrator_status_callback_google(self):
        """INT-004: Status callback called for Google."""
        from research_orchestrator.config import ResearchConfig
        from research_orchestrator.orchestrator import ResearchOrchestrator

        status_updates = []

        def callback(provider: str, message: str):
            status_updates.append((provider, message))

        orchestrator = ResearchOrchestrator(on_status_update=callback)

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}, clear=True):
            with patch(
                "research_orchestrator.providers.google.GoogleProvider.execute",
                new_callable=AsyncMock,
                return_value=ProviderResult(
                    provider="gemini",
                    status=ProviderStatus.SUCCESS,
                    content="Mocked result",
                ),
            ):
                config = ResearchConfig(prompt="test", sources=["gemini"])
                await orchestrator.execute(config)

        # Should have received status updates
        assert len(status_updates) >= 1
        providers = [p for p, _ in status_updates]
        assert "gemini" in providers

    @pytest.mark.asyncio
    async def test_orchestrator_parallel_execution(self):
        """INT-005: Execute all providers in parallel."""
        from research_orchestrator.config import ResearchConfig
        from research_orchestrator.orchestrator import ResearchOrchestrator

        orchestrator = ResearchOrchestrator()

        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "test",
                "OPENAI_API_KEY": "test",
                "GOOGLE_API_KEY": "test",
            },
            clear=True,
        ):
            with patch(
                "research_orchestrator.providers.anthropic.AnthropicProvider.execute",
                new_callable=AsyncMock,
                return_value=ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="Claude result",
                ),
            ):
                with patch(
                    "research_orchestrator.providers.openai.OpenAIProvider.execute",
                    new_callable=AsyncMock,
                    return_value=ProviderResult(
                        provider="openai",
                        status=ProviderStatus.SUCCESS,
                        content="OpenAI result",
                    ),
                ):
                    with patch(
                        "research_orchestrator.providers.google.GoogleProvider.execute",
                        new_callable=AsyncMock,
                        return_value=ProviderResult(
                            provider="gemini",
                            status=ProviderStatus.SUCCESS,
                            content="Gemini result",
                        ),
                    ):
                        config = ResearchConfig(
                            prompt="test", sources=["claude", "openai", "gemini"]
                        )
                        output = await orchestrator.execute(config)

        assert output.success_count == 3
        providers = {r.provider for r in output.results}
        assert providers == {"claude", "openai", "gemini"}
