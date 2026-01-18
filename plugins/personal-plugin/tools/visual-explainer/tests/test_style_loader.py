"""Tests for style_loader module.

Tests loading bundled styles, custom styles, and style validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from visual_explainer.config import PromptRecipe, StyleConfig
from visual_explainer.style_loader import (
    DEFAULT_STYLE_NAME,
    StyleLoadError,
    clear_style_cache,
    discover_bundled_styles,
    format_prompt_injection,
    get_bundled_styles_path,
    get_default_style,
    get_prompt_recipe,
    get_style_summary,
    list_available_styles,
    load_style,
)


class TestGetBundledStylesPath:
    """Tests for get_bundled_styles_path function."""

    def test_returns_path_or_none(self):
        """Test that function returns Path or None."""
        result = get_bundled_styles_path()
        assert result is None or isinstance(result, Path)

    def test_path_is_directory_when_exists(self):
        """Test that returned path is a directory when it exists."""
        result = get_bundled_styles_path()
        if result is not None:
            assert result.is_dir()


class TestDiscoverBundledStyles:
    """Tests for discover_bundled_styles function."""

    def test_returns_dict(self):
        """Test that discover_bundled_styles returns a dict."""
        # Clear cache to ensure fresh discovery
        clear_style_cache()
        styles = discover_bundled_styles()
        assert isinstance(styles, dict)

    def test_style_values_are_paths(self):
        """Test that style values are Path objects."""
        clear_style_cache()
        styles = discover_bundled_styles()
        for name, path in styles.items():
            assert isinstance(path, Path)
            assert path.suffix == ".json"


class TestLoadStyle:
    """Tests for load_style function."""

    def test_load_default_when_none(self):
        """Test loading default style when None is passed."""
        clear_style_cache()
        style = load_style(None)
        assert style is not None
        assert isinstance(style, StyleConfig)

    def test_load_bundled_style_by_name(self):
        """Test loading bundled style by simple name."""
        clear_style_cache()
        bundled = discover_bundled_styles()
        if bundled:
            first_style_name = next(iter(bundled.keys()))
            style = load_style(first_style_name)
            assert style is not None
            assert isinstance(style, StyleConfig)
            assert style.prompt_recipe is not None

    def test_load_custom_style_by_path(self, tmp_path: Path):
        """Test loading custom style from file path."""
        clear_style_cache()
        custom_style = {
            "SchemaVersion": "1.2",
            "StyleName": "My_Custom_Style",
            "PromptRecipe": {
                "CoreStylePrompt": "custom style prompt",
                "NegativePrompt": "things to avoid",
            },
        }
        style_path = tmp_path / "custom.json"
        with open(style_path, "w", encoding="utf-8") as f:
            json.dump(custom_style, f)

        loaded = load_style(str(style_path))
        assert loaded.style_name == "My_Custom_Style"
        assert loaded.prompt_recipe.core_style_prompt == "custom style prompt"

    def test_load_nonexistent_style_raises_error(self):
        """Test that loading non-existent style raises StyleLoadError."""
        clear_style_cache()
        with pytest.raises(StyleLoadError) as exc_info:
            load_style("definitely-not-a-real-style-12345")
        assert "not found" in str(exc_info.value).lower()

    def test_load_nonexistent_file_raises_error(self, tmp_path: Path):
        """Test that loading non-existent file path raises StyleLoadError."""
        clear_style_cache()
        nonexistent = tmp_path / "nonexistent.json"
        with pytest.raises(StyleLoadError) as exc_info:
            load_style(str(nonexistent))
        assert "not found" in str(exc_info.value).lower()

    def test_load_invalid_json_raises_error(self, tmp_path: Path):
        """Test that loading invalid JSON raises StyleLoadError."""
        clear_style_cache()
        invalid_path = tmp_path / "invalid.json"
        with open(invalid_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        with pytest.raises(StyleLoadError) as exc_info:
            load_style(str(invalid_path))
        assert "json" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    def test_load_invalid_schema_raises_error(self, tmp_path: Path):
        """Test that loading invalid schema raises StyleLoadError."""
        clear_style_cache()
        invalid_style = {
            "SchemaVersion": "1.2",
            # Missing required StyleName
        }
        style_path = tmp_path / "invalid-schema.json"
        with open(style_path, "w", encoding="utf-8") as f:
            json.dump(invalid_style, f)

        with pytest.raises(StyleLoadError) as exc_info:
            load_style(str(style_path))
        assert "validation" in str(exc_info.value).lower() or "stylename" in str(exc_info.value).lower()

    def test_caches_loaded_style(self):
        """Test that loaded styles are cached."""
        clear_style_cache()
        style1 = load_style(None)  # Load default
        style2 = load_style(None)  # Should return cached
        assert style1 is style2


class TestListAvailableStyles:
    """Tests for list_available_styles function."""

    def test_returns_list(self):
        """Test that list_available_styles returns a list."""
        clear_style_cache()
        styles = list_available_styles()
        assert isinstance(styles, list)

    def test_style_info_structure(self):
        """Test structure of style info entries."""
        clear_style_cache()
        styles = list_available_styles()
        for info in styles:
            assert isinstance(info, dict)
            assert "name" in info
            assert "path" in info


class TestGetDefaultStyle:
    """Tests for get_default_style function."""

    def test_returns_style_config(self):
        """Test that get_default_style returns StyleConfig."""
        clear_style_cache()
        style = get_default_style()
        assert isinstance(style, StyleConfig)

    def test_default_style_has_prompt_recipe(self):
        """Test that default style has valid prompt recipe."""
        clear_style_cache()
        style = get_default_style()
        assert style.prompt_recipe is not None
        # Check that at least some prompt content exists
        assert (
            style.prompt_recipe.core_style_prompt != ""
            or style.prompt_recipe.style_prefix != ""
        )


class TestGetPromptRecipe:
    """Tests for get_prompt_recipe function."""

    def test_extracts_prompt_recipe(self, sample_style_config: StyleConfig):
        """Test that prompt recipe is correctly extracted."""
        recipe = get_prompt_recipe(sample_style_config)
        assert isinstance(recipe, PromptRecipe)
        assert recipe.core_style_prompt == sample_style_config.prompt_recipe.core_style_prompt

    def test_returns_same_object(self, sample_style_config: StyleConfig):
        """Test that the same PromptRecipe object is returned."""
        recipe = get_prompt_recipe(sample_style_config)
        assert recipe is sample_style_config.prompt_recipe


class TestGetStyleSummary:
    """Tests for get_style_summary function."""

    def test_returns_dict_with_required_keys(self, sample_style_config: StyleConfig):
        """Test that summary contains required keys."""
        summary = get_style_summary(sample_style_config)
        assert isinstance(summary, dict)
        assert "name" in summary
        assert "intent" in summary
        assert "version" in summary

    def test_name_matches_style_name(self, sample_style_config: StyleConfig):
        """Test that name in summary matches style name."""
        summary = get_style_summary(sample_style_config)
        assert summary["name"] == sample_style_config.style_name


class TestFormatPromptInjection:
    """Tests for format_prompt_injection function."""

    def test_extracts_all_components(self, sample_style_config: StyleConfig):
        """Test that all prompt components are extracted."""
        injection = format_prompt_injection(sample_style_config)
        assert "style_prefix" in injection
        assert "core_style" in injection
        assert "color_constraints" in injection
        assert "text_rules" in injection
        assert "negative" in injection
        assert "quality_checklist" in injection
        assert "combined" in injection

    def test_style_prefix_extracted(self):
        """Test style prefix extraction."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(
                StylePrefix="Clean professional",
                CoreStylePrompt="modern",
            ),
        )
        injection = format_prompt_injection(style)
        assert injection["style_prefix"] == "Clean professional"

    def test_core_style_extracted(self):
        """Test core style extraction."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(
                CoreStylePrompt="modern illustration style",
            ),
        )
        injection = format_prompt_injection(style)
        assert injection["core_style"] == "modern illustration style"

    def test_quality_checklist_formatted(self):
        """Test quality checklist is properly formatted."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(
                CoreStylePrompt="test",
                QualityChecklist=["Clear layout", "Professional look"],
            ),
        )
        injection = format_prompt_injection(style)
        checklist = injection["quality_checklist"]
        assert "Clear layout" in checklist
        assert "Professional look" in checklist

    def test_combined_prompt_includes_all(self):
        """Test combined prompt includes all non-empty components."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(
                StylePrefix="Prefix",
                CoreStylePrompt="Core",
                ColorConstraintPrompt="Colors",
                TextEnforcementPrompt="Text rules",
            ),
        )
        injection = format_prompt_injection(style)
        combined = injection["combined"]
        assert "Prefix" in combined
        assert "Core" in combined
        assert "Colors" in combined
        assert "Text rules" in combined

    def test_empty_components_handled(self):
        """Test that empty components don't cause issues."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(),
        )
        injection = format_prompt_injection(style)
        # Should not raise, empty strings are fine
        assert injection["core_style"] == ""
        assert injection["combined"] == ""


class TestClearStyleCache:
    """Tests for clear_style_cache function."""

    def test_clears_cache(self):
        """Test that cache is properly cleared."""
        # Load a style to populate cache
        load_style(None)
        # Clear the cache
        clear_style_cache()
        # Should reload (not return cached)
        style1 = load_style(None)
        clear_style_cache()
        style2 = load_style(None)
        # After clearing, we get new objects
        assert style1 is not style2


class TestDefaultStyleName:
    """Tests for DEFAULT_STYLE_NAME constant."""

    def test_default_style_name_is_string(self):
        """Test that DEFAULT_STYLE_NAME is a string."""
        assert isinstance(DEFAULT_STYLE_NAME, str)
        assert len(DEFAULT_STYLE_NAME) > 0

    def test_default_style_name_value(self):
        """Test expected value of DEFAULT_STYLE_NAME."""
        assert DEFAULT_STYLE_NAME == "professional-clean"


class TestBundledStylesDirectory:
    """Tests for bundled styles directory."""

    def test_bundled_styles_dir_exists_when_path_returned(self):
        """Test that bundled styles directory exists when path is returned."""
        styles_dir = get_bundled_styles_path()
        if styles_dir is not None:
            assert styles_dir.exists()
            assert styles_dir.is_dir()

    def test_bundled_styles_are_valid_json(self):
        """Test that all bundled style files are valid JSON."""
        styles_dir = get_bundled_styles_path()
        if styles_dir is not None:
            for json_file in styles_dir.glob("*.json"):
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                assert isinstance(data, dict)

    def test_bundled_styles_have_required_fields(self):
        """Test that bundled styles have minimum required fields."""
        styles_dir = get_bundled_styles_path()
        if styles_dir is not None:
            for json_file in styles_dir.glob("*.json"):
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                assert "StyleName" in data
                assert "PromptRecipe" in data


class TestStyleLoadWithPath:
    """Tests for loading styles using Path objects."""

    def test_load_with_path_object(self, tmp_path: Path):
        """Test loading style with Path object."""
        clear_style_cache()
        custom_style = {
            "SchemaVersion": "1.2",
            "StyleName": "Path_Test",
            "PromptRecipe": {"CoreStylePrompt": "path test"},
        }
        style_path = tmp_path / "path-style.json"
        with open(style_path, "w", encoding="utf-8") as f:
            json.dump(custom_style, f)

        # load_style accepts str, so convert Path to str
        loaded = load_style(str(style_path))
        assert loaded.style_name == "Path_Test"


class TestStyleLoadErrorDetails:
    """Tests for StyleLoadError exception details."""

    def test_error_contains_style_ref(self):
        """Test that error contains the style reference."""
        clear_style_cache()
        try:
            load_style("nonexistent-style-xyz")
        except StyleLoadError as e:
            assert e.style_ref == "nonexistent-style-xyz"
            assert "nonexistent-style-xyz" in str(e)

    def test_error_contains_reason(self):
        """Test that error contains the reason."""
        clear_style_cache()
        try:
            load_style("nonexistent-style-xyz")
        except StyleLoadError as e:
            assert e.reason != ""
            assert len(e.reason) > 0
