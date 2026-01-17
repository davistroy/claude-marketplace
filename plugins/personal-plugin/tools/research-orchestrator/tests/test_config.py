"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from research_orchestrator.config import Depth, ProviderConfig, ResearchConfig


class TestDepth:
    """Tests for Depth enum."""

    def test_anthropic_budget_values(self):
        """Test Anthropic budget token mappings."""
        assert Depth.BRIEF.get_anthropic_budget() == 4_000
        assert Depth.STANDARD.get_anthropic_budget() == 10_000
        assert Depth.COMPREHENSIVE.get_anthropic_budget() == 32_000

    def test_openai_effort_values(self):
        """Test OpenAI effort level mappings."""
        assert Depth.BRIEF.get_openai_effort() == "medium"
        assert Depth.STANDARD.get_openai_effort() == "high"
        assert Depth.COMPREHENSIVE.get_openai_effort() == "xhigh"

    def test_gemini_thinking_values(self):
        """Test Gemini thinking level mappings."""
        assert Depth.BRIEF.get_gemini_thinking_level() == "low"
        assert Depth.STANDARD.get_gemini_thinking_level() == "high"
        assert Depth.COMPREHENSIVE.get_gemini_thinking_level() == "high"


class TestProviderConfig:
    """Tests for ProviderConfig."""

    def test_is_available_with_key(self):
        """Test availability when API key is set."""
        config = ProviderConfig(name="claude", api_key="test-key")
        assert config.is_available is True

    def test_is_available_without_key(self):
        """Test availability when API key is missing."""
        config = ProviderConfig(name="claude", api_key=None)
        assert config.is_available is False

    def test_is_available_with_empty_key(self):
        """Test availability when API key is empty string."""
        config = ProviderConfig(name="claude", api_key="")
        assert config.is_available is False


class TestResearchConfig:
    """Tests for ResearchConfig."""

    def test_valid_config(self):
        """Test creating valid config."""
        config = ResearchConfig(
            prompt="Test prompt",
            sources=["claude", "openai"],
            depth=Depth.STANDARD,
        )
        assert config.prompt == "Test prompt"
        assert config.sources == ["claude", "openai"]
        assert config.depth == Depth.STANDARD

    def test_empty_prompt_raises(self):
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            ResearchConfig(prompt="")

    def test_invalid_source_raises(self):
        """Test that invalid source raises ValueError."""
        with pytest.raises(ValueError, match="Invalid sources"):
            ResearchConfig(prompt="test", sources=["invalid"])

    def test_depth_string_conversion(self):
        """Test that depth string is converted to enum."""
        config = ResearchConfig(prompt="test", depth="brief")  # type: ignore
        assert config.depth == Depth.BRIEF

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_get_missing_api_keys(self):
        """Test detection of missing API keys."""
        config = ResearchConfig(
            prompt="test",
            sources=["claude", "openai", "gemini"],
        )
        missing = config.get_missing_api_keys()
        assert "OPENAI_API_KEY" in missing
        assert "GOOGLE_API_KEY" in missing
        assert "ANTHROPIC_API_KEY" not in missing

    @patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "key1",
            "OPENAI_API_KEY": "key2",
            "GOOGLE_API_KEY": "key3",
        },
        clear=True,
    )
    def test_get_provider_configs(self):
        """Test getting provider configurations."""
        config = ResearchConfig(
            prompt="test",
            sources=["claude", "openai"],
        )
        provider_configs = config.get_provider_configs()
        assert len(provider_configs) == 2
        assert all(pc.is_available for pc in provider_configs)
