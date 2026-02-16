"""Tests for theming system."""

import pytest
from pathlib import Path

from bpmn2drawio.themes import BPMNTheme, THEMES, get_theme
from bpmn2drawio.config import (
    load_brand_config,
    merge_theme_with_config,
    get_env_config,
)
from bpmn2drawio.exceptions import ConfigurationError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestBPMNTheme:
    """Tests for BPMNTheme class."""

    def test_default_theme_values(self):
        """Test default theme has expected values."""
        theme = BPMNTheme()

        assert theme.start_event_fill == "#d5e8d4"
        assert theme.task_fill == "#dae8fc"
        assert theme.gateway_fill == "#fff2cc"

    def test_custom_theme_values(self):
        """Test custom theme values."""
        theme = BPMNTheme(
            start_event_fill="#custom",
            task_fill="#blue",
        )

        assert theme.start_event_fill == "#custom"
        assert theme.task_fill == "#blue"
        # Default values still present
        assert theme.end_event_fill == "#f8cecc"

    def test_style_for_start_event(self):
        """Test style_for generates correct start event style."""
        theme = BPMNTheme()
        style = theme.style_for("startEvent")

        assert "ellipse" in style
        assert "#d5e8d4" in style
        assert "#82b366" in style

    def test_style_for_task(self):
        """Test style_for generates correct task style."""
        theme = BPMNTheme()
        style = theme.style_for("task")

        assert "rounded=1" in style
        assert "#dae8fc" in style

    def test_style_for_unknown_defaults_to_task(self):
        """Test unknown element type defaults to task style."""
        theme = BPMNTheme()
        style = theme.style_for("unknownType")

        assert "rounded=1" in style


class TestPredefinedThemes:
    """Tests for predefined themes."""

    def test_default_theme_exists(self):
        """Test default theme exists."""
        assert "default" in THEMES

    def test_blueprint_theme(self):
        """Test blueprint theme has blue colors."""
        theme = THEMES["blueprint"]

        assert "#1976d2" in theme.start_event_stroke
        assert "#1976d2" in theme.task_stroke

    def test_monochrome_theme(self):
        """Test monochrome theme has grayscale colors."""
        theme = THEMES["monochrome"]

        assert theme.start_event_fill == "#ffffff"
        assert "#333333" in theme.start_event_stroke

    def test_high_contrast_theme(self):
        """Test high contrast theme has distinct colors."""
        theme = THEMES["high_contrast"]

        # Different colors for different elements
        assert theme.start_event_stroke != theme.end_event_stroke


class TestGetTheme:
    """Tests for get_theme function."""

    def test_get_existing_theme(self):
        """Test getting existing theme."""
        theme = get_theme("blueprint")
        assert theme == THEMES["blueprint"]

    def test_get_unknown_returns_default(self):
        """Test unknown theme returns default."""
        theme = get_theme("nonexistent")
        assert theme == THEMES["default"]


class TestLoadBrandConfig:
    """Tests for brand configuration loading."""

    def test_load_valid_config(self):
        """Test loading valid configuration file."""
        theme = load_brand_config(FIXTURES_DIR / "brand-config.yaml")

        assert theme.start_event_fill == "#e8f5e9"
        assert theme.start_event_stroke == "#4caf50"
        assert theme.task_fill == "#e3f2fd"

    def test_load_missing_file(self):
        """Test loading missing file raises error."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_brand_config("/nonexistent/config.yaml")

        assert "not found" in str(exc_info.value)


class TestMergeThemeWithConfig:
    """Tests for theme merging."""

    def test_merge_empty_config(self):
        """Test merging empty config preserves base theme."""
        base = BPMNTheme()
        config = {}

        result = merge_theme_with_config(base, config)

        assert result.start_event_fill == base.start_event_fill

    def test_merge_partial_config(self):
        """Test merging partial config."""
        base = BPMNTheme()
        config = {"colors": {"tasks": {"fill": "#newcolor"}}}

        result = merge_theme_with_config(base, config)

        assert result.task_fill == "#newcolor"
        assert result.start_event_fill == base.start_event_fill


class TestEnvConfig:
    """Tests for environment configuration."""

    def test_get_env_config_empty(self, monkeypatch):
        """Test empty environment returns empty config."""
        # Clear relevant env vars
        monkeypatch.delenv("BPMN2DRAWIO_THEME", raising=False)
        monkeypatch.delenv("BPMN2DRAWIO_LAYOUT", raising=False)

        config = get_env_config()

        # Should return empty dict or dict without those keys
        assert config.get("theme") is None
        assert config.get("layout") is None

    def test_get_env_config_with_vars(self, monkeypatch):
        """Test environment variables are read."""
        monkeypatch.setenv("BPMN2DRAWIO_THEME", "blueprint")
        monkeypatch.setenv("BPMN2DRAWIO_LAYOUT", "preserve")

        config = get_env_config()

        assert config["theme"] == "blueprint"
        assert config["layout"] == "preserve"
