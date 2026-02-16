"""Tests for configuration loading module."""

from pathlib import Path
from textwrap import dedent

import pytest

from bpmn2drawio.config import (
    load_brand_config,
    merge_theme_with_config,
    get_env_config,
)
from bpmn2drawio.exceptions import ConfigurationError
from bpmn2drawio.themes import BPMNTheme, THEMES


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# load_brand_config: valid YAML
# ---------------------------------------------------------------------------


class TestLoadBrandConfigValid:
    """Tests for loading valid configuration files."""

    def test_load_valid_config_returns_theme(self):
        """Valid YAML config file returns a BPMNTheme instance."""
        theme = load_brand_config(str(FIXTURES_DIR / "brand-config.yaml"))
        assert isinstance(theme, BPMNTheme)

    def test_load_valid_config_applies_event_colors(self):
        """Event colors from config override defaults."""
        theme = load_brand_config(str(FIXTURES_DIR / "brand-config.yaml"))
        assert theme.start_event_fill == "#e8f5e9"
        assert theme.start_event_stroke == "#4caf50"
        assert theme.end_event_fill == "#ffebee"
        assert theme.end_event_stroke == "#f44336"

    def test_load_valid_config_applies_task_colors(self):
        """Task colors from config override defaults."""
        theme = load_brand_config(str(FIXTURES_DIR / "brand-config.yaml"))
        assert theme.task_fill == "#e3f2fd"
        assert theme.task_stroke == "#2196f3"

    def test_load_valid_config_applies_gateway_colors(self):
        """Gateway colors from config override defaults."""
        theme = load_brand_config(str(FIXTURES_DIR / "brand-config.yaml"))
        assert theme.gateway_fill == "#fff8e1"
        assert theme.gateway_stroke == "#ffc107"

    def test_load_valid_config_applies_fonts(self):
        """Font settings from config override defaults."""
        theme = load_brand_config(str(FIXTURES_DIR / "brand-config.yaml"))
        assert theme.font_family == "Arial"
        assert theme.font_size == 11
        assert theme.font_color == "#212121"

    def test_load_empty_yaml_returns_default_theme(self, tmp_path):
        """Empty YAML file (null content) returns default BPMNTheme."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        theme = load_brand_config(str(config_file))
        default = BPMNTheme()
        assert theme.start_event_fill == default.start_event_fill
        assert theme.font_family == default.font_family

    def test_load_config_with_base_theme(self, tmp_path):
        """Config specifying a base_theme inherits that theme's values."""
        config_file = tmp_path / "blueprint-based.yaml"
        config_file.write_text(
            dedent("""\
            base_theme: blueprint
            colors:
              tasks:
                fill: "#custom_fill"
        """)
        )
        theme = load_brand_config(str(config_file))
        blueprint = THEMES["blueprint"]
        # Overridden value
        assert theme.task_fill == "#custom_fill"
        # Inherited from blueprint (not default)
        assert theme.start_event_stroke == blueprint.start_event_stroke

    def test_load_config_unknown_base_theme_uses_default(self, tmp_path):
        """Unknown base_theme falls back to default BPMNTheme."""
        config_file = tmp_path / "unknown-base.yaml"
        config_file.write_text(
            dedent("""\
            base_theme: nonexistent_theme
        """)
        )
        theme = load_brand_config(str(config_file))
        default = BPMNTheme()
        assert theme.start_event_fill == default.start_event_fill


# ---------------------------------------------------------------------------
# load_brand_config: missing file
# ---------------------------------------------------------------------------


class TestLoadBrandConfigMissingFile:
    """Tests for missing configuration files."""

    def test_missing_file_raises_configuration_error(self):
        """Non-existent config path raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_brand_config("/nonexistent/path/config.yaml")
        assert "not found" in str(exc_info.value)

    def test_missing_file_error_includes_path(self):
        """Error message includes the missing file path."""
        bogus_path = "/some/missing/config.yaml"
        with pytest.raises(ConfigurationError, match=bogus_path):
            load_brand_config(bogus_path)


# ---------------------------------------------------------------------------
# load_brand_config: malformed YAML
# ---------------------------------------------------------------------------


class TestLoadBrandConfigMalformedYAML:
    """Tests for malformed YAML content."""

    def test_malformed_yaml_raises_configuration_error(self, tmp_path):
        """Invalid YAML syntax raises ConfigurationError."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("colors:\n  - fill: [unclosed bracket")
        with pytest.raises(ConfigurationError) as exc_info:
            load_brand_config(str(config_file))
        assert "Invalid YAML" in str(exc_info.value)

    def test_yaml_with_tabs_raises_configuration_error(self, tmp_path):
        """YAML with tab indentation raises ConfigurationError."""
        config_file = tmp_path / "tabs.yaml"
        config_file.write_text("colors:\n\t- fill: bad")
        with pytest.raises(ConfigurationError) as exc_info:
            load_brand_config(str(config_file))
        assert "Invalid YAML" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Default values when keys are missing
# ---------------------------------------------------------------------------


class TestDefaultValues:
    """Tests that default values are applied when config keys are absent."""

    def test_missing_colors_preserves_all_defaults(self, tmp_path):
        """Config with no 'colors' key preserves all default theme values."""
        config_file = tmp_path / "no-colors.yaml"
        config_file.write_text("base_theme: default\n")
        theme = load_brand_config(str(config_file))
        default = BPMNTheme()
        assert theme.task_fill == default.task_fill
        assert theme.gateway_fill == default.gateway_fill
        assert theme.sequence_flow_stroke == default.sequence_flow_stroke

    def test_missing_fonts_preserves_font_defaults(self, tmp_path):
        """Config with no 'fonts' key preserves default font settings."""
        config_file = tmp_path / "no-fonts.yaml"
        config_file.write_text(
            dedent("""\
            colors:
              tasks:
                fill: "#111111"
        """)
        )
        theme = load_brand_config(str(config_file))
        default = BPMNTheme()
        assert theme.font_family == default.font_family
        assert theme.font_size == default.font_size
        assert theme.font_color == default.font_color

    def test_partial_events_preserves_unset_event_defaults(self, tmp_path):
        """Setting only start event colors preserves end/intermediate defaults."""
        config_file = tmp_path / "partial-events.yaml"
        config_file.write_text(
            dedent("""\
            colors:
              events:
                start_fill: "#aaaaaa"
        """)
        )
        theme = load_brand_config(str(config_file))
        default = BPMNTheme()
        assert theme.start_event_fill == "#aaaaaa"
        assert theme.end_event_fill == default.end_event_fill
        assert theme.intermediate_event_fill == default.intermediate_event_fill


# ---------------------------------------------------------------------------
# Type validation for config values
# ---------------------------------------------------------------------------


class TestTypeValidation:
    """Tests for type handling of configuration values."""

    def test_font_size_as_integer(self, tmp_path):
        """Font size provided as integer is accepted."""
        config_file = tmp_path / "int-size.yaml"
        config_file.write_text(
            dedent("""\
            fonts:
              size: 14
        """)
        )
        theme = load_brand_config(str(config_file))
        assert theme.font_size == 14
        assert isinstance(theme.font_size, int)

    def test_font_size_as_float_passthrough(self, tmp_path):
        """Font size provided as float is passed through (YAML parses 14.5 as float)."""
        config_file = tmp_path / "float-size.yaml"
        config_file.write_text(
            dedent("""\
            fonts:
              size: 14.5
        """)
        )
        theme = load_brand_config(str(config_file))
        # The config module does not enforce strict int typing; it passes through
        assert theme.font_size == 14.5

    def test_color_values_are_strings(self, tmp_path):
        """Color values loaded from config remain strings."""
        config_file = tmp_path / "colors.yaml"
        config_file.write_text(
            dedent("""\
            colors:
              tasks:
                fill: "#ff0000"
                stroke: "#00ff00"
        """)
        )
        theme = load_brand_config(str(config_file))
        assert isinstance(theme.task_fill, str)
        assert isinstance(theme.task_stroke, str)

    def test_unrecognized_color_keys_are_ignored(self, tmp_path):
        """Unknown keys in the colors section do not cause errors."""
        config_file = tmp_path / "extra-keys.yaml"
        config_file.write_text(
            dedent("""\
            colors:
              invented_key: "#abcdef"
              tasks:
                fill: "#111111"
        """)
        )
        theme = load_brand_config(str(config_file))
        assert theme.task_fill == "#111111"
        # No attribute for the unknown key, but no error either
        assert not hasattr(theme, "invented_key")


# ---------------------------------------------------------------------------
# Path resolution for relative config paths
# ---------------------------------------------------------------------------


class TestPathResolution:
    """Tests for path resolution behavior in load_brand_config."""

    def test_absolute_path_resolves(self, tmp_path):
        """Absolute path to config file loads successfully."""
        config_file = tmp_path / "abs.yaml"
        config_file.write_text("base_theme: default\n")
        theme = load_brand_config(str(config_file.resolve()))
        assert isinstance(theme, BPMNTheme)

    def test_relative_path_from_cwd(self, tmp_path, monkeypatch):
        """Relative path resolves from current working directory."""
        config_file = tmp_path / "rel.yaml"
        config_file.write_text("base_theme: monochrome\n")
        monkeypatch.chdir(tmp_path)
        theme = load_brand_config("rel.yaml")
        monochrome = THEMES["monochrome"]
        assert theme.start_event_fill == monochrome.start_event_fill

    def test_path_with_subdirectory(self, tmp_path):
        """Config file in a subdirectory loads correctly."""
        subdir = tmp_path / "config" / "brand"
        subdir.mkdir(parents=True)
        config_file = subdir / "theme.yaml"
        config_file.write_text(
            dedent("""\
            colors:
              tasks:
                fill: "#nested"
        """)
        )
        theme = load_brand_config(str(config_file))
        assert theme.task_fill == "#nested"


# ---------------------------------------------------------------------------
# merge_theme_with_config
# ---------------------------------------------------------------------------


class TestMergeThemeWithConfig:
    """Tests for the merge_theme_with_config function."""

    def test_merge_empty_config_returns_base_unchanged(self):
        """Empty config dict returns theme identical to base."""
        base = BPMNTheme()
        result = merge_theme_with_config(base, {})
        assert result.start_event_fill == base.start_event_fill
        assert result.font_family == base.font_family

    def test_merge_top_level_color_key(self):
        """Top-level keys in colors dict override matching theme fields."""
        base = BPMNTheme()
        config = {"colors": {"task_fill": "#override"}}
        result = merge_theme_with_config(base, config)
        assert result.task_fill == "#override"

    def test_merge_nested_events_section(self):
        """Nested events section maps to correct theme fields."""
        base = BPMNTheme()
        config = {
            "colors": {
                "events": {
                    "start_fill": "#sf",
                    "start_stroke": "#ss",
                    "end_fill": "#ef",
                    "end_stroke": "#es",
                }
            }
        }
        result = merge_theme_with_config(base, config)
        assert result.start_event_fill == "#sf"
        assert result.start_event_stroke == "#ss"
        assert result.end_event_fill == "#ef"
        assert result.end_event_stroke == "#es"

    def test_merge_fonts_section(self):
        """Fonts config overrides font-related theme fields."""
        base = BPMNTheme()
        config = {
            "fonts": {
                "family": "Courier",
                "size": 16,
                "color": "#000000",
            }
        }
        result = merge_theme_with_config(base, config)
        assert result.font_family == "Courier"
        assert result.font_size == 16
        assert result.font_color == "#000000"

    def test_merge_does_not_mutate_base_theme(self):
        """Merging creates a new theme; the base is not modified."""
        base = BPMNTheme()
        original_fill = base.task_fill
        config = {"colors": {"tasks": {"fill": "#changed"}}}
        merge_theme_with_config(base, config)
        assert base.task_fill == original_fill


# ---------------------------------------------------------------------------
# get_env_config
# ---------------------------------------------------------------------------


class TestGetEnvConfig:
    """Tests for environment variable configuration."""

    def test_empty_env_returns_empty_dict(self, monkeypatch):
        """No BPMN2DRAWIO_* env vars returns empty dict."""
        for var in (
            "BPMN2DRAWIO_THEME",
            "BPMN2DRAWIO_LAYOUT",
            "BPMN2DRAWIO_DIRECTION",
            "BPMN2DRAWIO_GRAPHVIZ_PATH",
        ):
            monkeypatch.delenv(var, raising=False)
        config = get_env_config()
        assert config == {}

    def test_theme_env_var(self, monkeypatch):
        """BPMN2DRAWIO_THEME env var populates config['theme']."""
        monkeypatch.setenv("BPMN2DRAWIO_THEME", "blueprint")
        config = get_env_config()
        assert config["theme"] == "blueprint"

    def test_layout_env_var(self, monkeypatch):
        """BPMN2DRAWIO_LAYOUT env var populates config['layout']."""
        monkeypatch.setenv("BPMN2DRAWIO_LAYOUT", "preserve")
        config = get_env_config()
        assert config["layout"] == "preserve"

    def test_direction_env_var(self, monkeypatch):
        """BPMN2DRAWIO_DIRECTION env var populates config['direction']."""
        monkeypatch.setenv("BPMN2DRAWIO_DIRECTION", "vertical")
        config = get_env_config()
        assert config["direction"] == "vertical"

    def test_graphviz_path_env_var(self, monkeypatch):
        """BPMN2DRAWIO_GRAPHVIZ_PATH env var populates config['graphviz_path']."""
        monkeypatch.setenv("BPMN2DRAWIO_GRAPHVIZ_PATH", "/usr/local/bin/dot")
        config = get_env_config()
        assert config["graphviz_path"] == "/usr/local/bin/dot"

    def test_all_env_vars_together(self, monkeypatch):
        """All four env vars populate their respective keys."""
        monkeypatch.setenv("BPMN2DRAWIO_THEME", "monochrome")
        monkeypatch.setenv("BPMN2DRAWIO_LAYOUT", "auto")
        monkeypatch.setenv("BPMN2DRAWIO_DIRECTION", "horizontal")
        monkeypatch.setenv("BPMN2DRAWIO_GRAPHVIZ_PATH", "/opt/graphviz/bin/dot")
        config = get_env_config()
        assert len(config) == 4
        assert config["theme"] == "monochrome"
        assert config["layout"] == "auto"
        assert config["direction"] == "horizontal"
        assert config["graphviz_path"] == "/opt/graphviz/bin/dot"
