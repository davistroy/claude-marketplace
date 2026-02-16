"""Tests for the model discovery module."""

import logging
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

from research_orchestrator.model_discovery import (
    ModelDiscovery,
    ModelInfo,
    UpgradeRecommendation,
    parse_model_date,
)

# ---------------------------------------------------------------------------
# parse_model_date tests
# ---------------------------------------------------------------------------


class TestParseModelDate:
    """Tests for the parse_model_date function."""

    def test_yyyymmdd_format(self):
        """Test Anthropic-style YYYYMMDD date format."""
        result = parse_model_date("claude-opus-4-5-20251101")
        assert result == datetime(2025, 11, 1)

    def test_yyyy_mm_dd_format(self):
        """Test OpenAI-style YYYY-MM-DD date format."""
        result = parse_model_date("o3-deep-research-2025-06-26")
        assert result == datetime(2025, 6, 26)

    def test_mm_yyyy_format(self):
        """Test Google-style MM-YYYY date format."""
        result = parse_model_date("deep-research-pro-preview-12-2025")
        assert result == datetime(2025, 12, 1)

    def test_no_date_returns_none(self):
        """Test model ID without date returns None."""
        result = parse_model_date("gpt-4")
        assert result is None

    def test_invalid_yyyymmdd_date(self):
        """Test invalid YYYYMMDD date (e.g., month 13)."""
        result = parse_model_date("model-20251301")
        assert result is None

    def test_invalid_yyyy_mm_dd_date(self):
        """Test invalid YYYY-MM-DD date."""
        result = parse_model_date("model-2025-13-01")
        assert result is None

    def test_invalid_mm_yyyy_date(self):
        """Test invalid MM-YYYY date (e.g., month 13)."""
        result = parse_model_date("model-13-2025")
        assert result is None

    def test_empty_string(self):
        """Test empty string returns None."""
        result = parse_model_date("")
        assert result is None

    def test_yyyymmdd_at_end_only(self):
        """Test that YYYYMMDD pattern only matches at end of string."""
        result = parse_model_date("20250101-model")
        assert result is None

    def test_multiple_date_patterns_prefers_yyyymmdd(self):
        """Test that YYYYMMDD is checked first."""
        # This has 8 digits at the end that form YYYYMMDD
        result = parse_model_date("model-20250615")
        assert result == datetime(2025, 6, 15)


# ---------------------------------------------------------------------------
# ModelInfo tests
# ---------------------------------------------------------------------------


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_defaults(self):
        """Test default values."""
        info = ModelInfo(id="test-model", provider="anthropic")
        assert info.date is None
        assert info.is_current is False
        assert info.is_newer is False

    def test_with_date(self):
        """Test creation with date."""
        dt = datetime(2025, 6, 15)
        info = ModelInfo(id="model-20250615", provider="anthropic", date=dt)
        assert info.date == dt


# ---------------------------------------------------------------------------
# UpgradeRecommendation tests
# ---------------------------------------------------------------------------


class TestUpgradeRecommendation:
    """Tests for UpgradeRecommendation dataclass."""

    def test_creation(self):
        """Test creation of upgrade recommendation."""
        rec = UpgradeRecommendation(
            provider="Anthropic",
            current_model="claude-opus-4-5-20251101",
            recommended_model="claude-opus-4-5-20260101",
            current_date=datetime(2025, 11, 1),
            recommended_date=datetime(2026, 1, 1),
            reason="Newer model available",
        )
        assert rec.provider == "Anthropic"
        assert rec.reason == "Newer model available"


# ---------------------------------------------------------------------------
# ModelDiscovery tests
# ---------------------------------------------------------------------------


class TestModelDiscovery:
    """Tests for the ModelDiscovery class."""

    def test_init_from_env(self):
        """Test initialization from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "key1",
                "OPENAI_API_KEY": "key2",
                "GOOGLE_API_KEY": "key3",
            },
            clear=True,
        ):
            discovery = ModelDiscovery()
            assert discovery.anthropic_key == "key1"
            assert discovery.openai_key == "key2"
            assert discovery.google_key == "key3"

    def test_init_with_explicit_keys(self):
        """Test initialization with explicit keys."""
        discovery = ModelDiscovery(anthropic_key="a", openai_key="b", google_key="c")
        assert discovery.anthropic_key == "a"
        assert discovery.openai_key == "b"
        assert discovery.google_key == "c"

    def test_get_current_models(self):
        """Test getting current model IDs."""
        discovery = ModelDiscovery()
        models = discovery.get_current_models()

        assert "anthropic" in models
        assert "openai" in models
        assert "google" in models
        assert "claude" in models["anthropic"]

    # --- Anthropic discovery tests ---

    def test_discover_anthropic_no_key(self):
        """Test Anthropic discovery without API key."""
        discovery = ModelDiscovery(anthropic_key=None)
        models = discovery.discover_anthropic_models()
        assert models == []

    def test_discover_anthropic_import_error(self):
        """Test Anthropic discovery when package not installed."""
        discovery = ModelDiscovery(anthropic_key="test-key")
        with patch.dict("sys.modules", {"anthropic": None}):
            with patch.object(discovery, "_get_anthropic_client", return_value=None):
                models = discovery.discover_anthropic_models()
                assert models == []

    def test_discover_anthropic_with_models(self):
        """Test Anthropic discovery with mock API response."""
        discovery = ModelDiscovery(anthropic_key="test-key")

        mock_model_1 = MagicMock()
        mock_model_1.id = "claude-opus-4-5-20251101"
        mock_model_2 = MagicMock()
        mock_model_2.id = "claude-sonnet-4-20260115"

        mock_response = MagicMock()
        mock_response.data = [mock_model_1, mock_model_2]

        mock_client = MagicMock()
        mock_client.models.list.return_value = mock_response

        with patch.object(discovery, "_get_anthropic_client", return_value=mock_client):
            models = discovery.discover_anthropic_models()

        assert len(models) == 2
        # Sorted by date descending
        assert models[0].id == "claude-sonnet-4-20260115"

    def test_discover_anthropic_api_error_logs_warning(self, caplog):
        """Test that API error logs a warning (not raises)."""
        discovery = ModelDiscovery(anthropic_key="test-key")

        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("API Error")

        with patch.object(discovery, "_get_anthropic_client", return_value=mock_client):
            with caplog.at_level(logging.WARNING, logger="research_orchestrator.model_discovery"):
                models = discovery.discover_anthropic_models()

        assert models == []
        assert "Failed to list" in caplog.text

    def test_discover_anthropic_filters_irrelevant_models(self):
        """Test that non-matching models are filtered out."""
        discovery = ModelDiscovery(anthropic_key="test-key")

        mock_model = MagicMock()
        mock_model.id = "claude-3-haiku-20240307"

        mock_response = MagicMock()
        mock_response.data = [mock_model]

        mock_client = MagicMock()
        mock_client.models.list.return_value = mock_response

        with patch.object(discovery, "_get_anthropic_client", return_value=mock_client):
            models = discovery.discover_anthropic_models()

        assert len(models) == 0

    # --- OpenAI discovery tests ---

    def test_discover_openai_no_key(self):
        """Test OpenAI discovery without API key."""
        discovery = ModelDiscovery(openai_key=None)
        models = discovery.discover_openai_models()
        assert models == []

    def test_discover_openai_with_models(self):
        """Test OpenAI discovery with mock API response."""
        discovery = ModelDiscovery(openai_key="test-key")

        mock_model = MagicMock()
        mock_model.id = "o3-deep-research-2025-06-26"

        mock_response = MagicMock()
        mock_response.data = [mock_model]

        mock_client = MagicMock()
        mock_client.models.list.return_value = mock_response

        with patch.object(discovery, "_get_openai_client", return_value=mock_client):
            models = discovery.discover_openai_models()

        assert len(models) == 1
        assert models[0].id == "o3-deep-research-2025-06-26"

    def test_discover_openai_api_error_logs_warning(self, caplog):
        """Test that OpenAI API error logs a warning."""
        discovery = ModelDiscovery(openai_key="test-key")

        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Rate limited")

        with patch.object(discovery, "_get_openai_client", return_value=mock_client):
            with caplog.at_level(logging.WARNING, logger="research_orchestrator.model_discovery"):
                models = discovery.discover_openai_models()

        assert models == []
        assert "Failed to list" in caplog.text

    # --- Google discovery tests ---

    @patch.dict(os.environ, {}, clear=True)
    def test_discover_google_no_key_returns_empty(self):
        """Test Google discovery without API key returns empty list."""
        discovery = ModelDiscovery(google_key=None)
        # _get_google_client returns None when no key, which triggers early return
        models = discovery.discover_google_agents()
        assert models == []

    @patch.dict(os.environ, {}, clear=True)
    def test_get_google_client_no_key(self):
        """Test that _get_google_client returns None without API key."""
        discovery = ModelDiscovery(google_key=None)
        assert discovery._get_google_client() is None

    def test_discover_google_known_agents(self):
        """Test Google discovery returns known agents."""
        discovery = ModelDiscovery(google_key="test-key")

        mock_client = MagicMock()
        with patch.object(discovery, "_get_google_client", return_value=mock_client):
            models = discovery.discover_google_agents()

        # Should contain the known agent
        agent_ids = [m.id for m in models]
        assert "deep-research-pro-preview-12-2025" in agent_ids

    # --- Upgrade checking tests ---

    def test_check_for_upgrades_no_newer(self):
        """Test upgrade check when no newer models exist."""
        discovery = ModelDiscovery()

        with patch.object(discovery, "discover_anthropic_models", return_value=[]):
            with patch.object(discovery, "discover_openai_models", return_value=[]):
                with patch.object(discovery, "discover_google_agents", return_value=[]):
                    recommendations = discovery.check_for_upgrades()

        assert recommendations == []

    def test_check_for_upgrades_with_newer_anthropic(self):
        """Test upgrade check when newer Anthropic model exists."""
        discovery = ModelDiscovery()

        newer_model = ModelInfo(
            id="claude-opus-4-5-20260201",
            provider="anthropic",
            date=datetime(2026, 2, 1),
            is_newer=True,
        )

        with patch.object(discovery, "discover_anthropic_models", return_value=[newer_model]):
            with patch.object(discovery, "discover_openai_models", return_value=[]):
                with patch.object(discovery, "discover_google_agents", return_value=[]):
                    recommendations = discovery.check_for_upgrades()

        assert len(recommendations) == 1
        assert "Anthropic" in recommendations[0].provider

    # --- Format report tests ---

    def test_format_upgrade_report_empty(self):
        """Test format report with no recommendations."""
        discovery = ModelDiscovery()
        report = discovery.format_upgrade_report([])
        assert "up to date" in report

    def test_format_upgrade_report_with_recommendations(self):
        """Test format report with recommendations."""
        discovery = ModelDiscovery()
        recs = [
            UpgradeRecommendation(
                provider="Anthropic (Claude)",
                current_model="claude-opus-4-5-20251101",
                recommended_model="claude-opus-4-5-20260201",
                current_date=datetime(2025, 11, 1),
                recommended_date=datetime(2026, 2, 1),
                reason="Newer model available",
            ),
        ]
        report = discovery.format_upgrade_report(recs)

        assert "Anthropic" in report
        assert "claude-opus-4-5-20251101" in report
        assert "claude-opus-4-5-20260201" in report
        assert "How to Upgrade" in report
        assert "ANTHROPIC_MODEL=" in report

    def test_format_upgrade_report_all_providers(self):
        """Test format report with recommendations for all providers."""
        discovery = ModelDiscovery()
        recs = [
            UpgradeRecommendation(
                provider="Anthropic (Claude)",
                current_model="old",
                recommended_model="new",
                current_date=None,
                recommended_date=None,
                reason="Newer",
            ),
            UpgradeRecommendation(
                provider="OpenAI (o3 Deep Research)",
                current_model="old",
                recommended_model="new",
                current_date=None,
                recommended_date=None,
                reason="Newer",
            ),
            UpgradeRecommendation(
                provider="Google (Gemini Deep Research)",
                current_model="old",
                recommended_model="new",
                current_date=None,
                recommended_date=None,
                reason="Newer",
            ),
        ]
        report = discovery.format_upgrade_report(recs)

        assert "ANTHROPIC_MODEL=" in report
        assert "OPENAI_MODEL=" in report
        assert "GEMINI_AGENT=" in report
