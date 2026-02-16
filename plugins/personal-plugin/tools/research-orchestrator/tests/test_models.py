"""Tests for data models."""

from research_orchestrator.models import ProviderResult, ProviderStatus, ResearchOutput


class TestProviderResult:
    """Tests for ProviderResult."""

    def test_is_success_when_success(self):
        """Test is_success property for successful result."""
        result = ProviderResult(
            provider="claude",
            status=ProviderStatus.SUCCESS,
            content="Test content",
        )
        assert result.is_success is True

    def test_is_success_when_failed(self):
        """Test is_success property for failed result."""
        result = ProviderResult(
            provider="claude",
            status=ProviderStatus.FAILED,
            error="Test error",
        )
        assert result.is_success is False

    def test_is_success_when_timeout(self):
        """Test is_success property for timeout result."""
        result = ProviderResult(
            provider="openai",
            status=ProviderStatus.TIMEOUT,
            error="Timed out",
        )
        assert result.is_success is False


class TestResearchOutput:
    """Tests for ResearchOutput."""

    def test_successful_results(self):
        """Test filtering successful results."""
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(provider="claude", status=ProviderStatus.SUCCESS),
                ProviderResult(provider="openai", status=ProviderStatus.FAILED),
                ProviderResult(provider="gemini", status=ProviderStatus.SUCCESS),
            ],
        )
        assert len(output.successful_results) == 2
        assert output.success_count == 2

    def test_failed_results(self):
        """Test filtering failed results."""
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(provider="claude", status=ProviderStatus.SUCCESS),
                ProviderResult(provider="openai", status=ProviderStatus.FAILED),
                ProviderResult(provider="gemini", status=ProviderStatus.TIMEOUT),
            ],
        )
        assert len(output.failed_results) == 2

    def test_has_partial_results(self):
        """Test partial results detection."""
        partial_output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(provider="claude", status=ProviderStatus.SUCCESS),
                ProviderResult(provider="openai", status=ProviderStatus.FAILED),
            ],
        )
        assert partial_output.has_partial_results is True

        all_success = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(provider="claude", status=ProviderStatus.SUCCESS),
                ProviderResult(provider="openai", status=ProviderStatus.SUCCESS),
            ],
        )
        assert all_success.has_partial_results is False

        all_failed = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(provider="claude", status=ProviderStatus.FAILED),
                ProviderResult(provider="openai", status=ProviderStatus.FAILED),
            ],
        )
        assert all_failed.has_partial_results is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        output = ResearchOutput(
            prompt="test prompt",
            results=[
                ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="test content",
                    duration_seconds=1.5,
                ),
            ],
            depth="standard",
        )
        data = output.to_dict()

        assert data["prompt"] == "test prompt"
        assert data["depth"] == "standard"
        assert len(data["results"]) == 1
        assert data["results"][0]["provider"] == "claude"
        assert data["results"][0]["status"] == "success"
