"""Tests for config module.

Tests configuration validation, serialization, and defaults.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from visual_explainer.config import (
    DEFAULT_STYLE,
    AspectRatio,
    ColorDefinition,
    ColorSystem,
    GenerationConfig,
    InternalConfig,
    PromptRecipe,
    Resolution,
    StyleConfig,
)


class TestResolution:
    """Tests for Resolution enum."""

    def test_resolution_values(self):
        """Test resolution enum values."""
        assert Resolution.STANDARD.value == "standard"
        assert Resolution.HIGH.value == "high"
        assert Resolution.ULTRA.value == "ultra"

    def test_get_gemini_size_standard(self):
        """Test Gemini size for standard resolution."""
        assert Resolution.STANDARD.get_gemini_size() == "STANDARD"

    def test_get_gemini_size_high(self):
        """Test Gemini size for high resolution."""
        assert Resolution.HIGH.get_gemini_size() == "LARGE"

    def test_get_gemini_size_ultra(self):
        """Test Gemini size for ultra resolution."""
        assert Resolution.ULTRA.get_gemini_size() == "LARGE"


class TestAspectRatio:
    """Tests for AspectRatio enum."""

    def test_aspect_ratio_values(self):
        """Test aspect ratio enum values."""
        assert AspectRatio.LANDSCAPE_16_9.value == "16:9"
        assert AspectRatio.SQUARE.value == "1:1"
        assert AspectRatio.LANDSCAPE_4_3.value == "4:3"
        assert AspectRatio.PORTRAIT_9_16.value == "9:16"
        assert AspectRatio.PORTRAIT_3_4.value == "3:4"


class TestGenerationConfig:
    """Tests for GenerationConfig."""

    def test_valid_config_minimal(self):
        """Test creating config with minimal required fields."""
        config = GenerationConfig(input_source="test input")
        assert config.input_source == "test input"
        assert config.style == "professional-clean"
        assert config.max_iterations == 5
        assert config.pass_threshold == 0.85
        assert config.resolution == Resolution.HIGH
        assert config.concurrency == 3

    def test_valid_config_all_fields(self, tmp_path: Path):
        """Test creating config with all fields."""
        config = GenerationConfig(
            input_source="test input",
            style="custom-style",
            output_dir=tmp_path,
            max_iterations=3,
            pass_threshold=0.80,
            resolution=Resolution.STANDARD,
            aspect_ratio=AspectRatio.SQUARE,
            image_count=5,
            no_cache=True,
            resume=tmp_path / "checkpoint.json",
            dry_run=True,
            setup_keys=True,
            concurrency=5,
        )
        assert config.style == "custom-style"
        assert config.output_dir == tmp_path
        assert config.max_iterations == 3
        assert config.pass_threshold == 0.80
        assert config.resolution == Resolution.STANDARD
        assert config.aspect_ratio == AspectRatio.SQUARE
        assert config.image_count == 5
        assert config.no_cache is True
        assert config.dry_run is True
        assert config.concurrency == 5

    def test_invalid_empty_input_source(self):
        """Test that empty input source is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="")

    def test_invalid_max_iterations_too_low(self):
        """Test that max_iterations below 1 is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", max_iterations=0)

    def test_invalid_max_iterations_too_high(self):
        """Test that max_iterations above 10 is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", max_iterations=11)

    def test_invalid_pass_threshold_too_low(self):
        """Test that pass_threshold below 0 is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", pass_threshold=-0.1)

    def test_invalid_pass_threshold_too_high(self):
        """Test that pass_threshold above 1 is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", pass_threshold=1.1)

    def test_invalid_concurrency_too_low(self):
        """Test that concurrency below 1 is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", concurrency=0)

    def test_invalid_concurrency_too_high(self):
        """Test that concurrency above 10 is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", concurrency=11)

    def test_invalid_image_count_negative(self):
        """Test that negative image_count is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", image_count=-1)

    def test_invalid_image_count_too_high(self):
        """Test that image_count above 20 is rejected."""
        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", image_count=21)

    def test_resolution_string_conversion(self):
        """Test resolution string is converted to enum."""
        config = GenerationConfig(input_source="test", resolution="standard")
        assert config.resolution == Resolution.STANDARD

    def test_aspect_ratio_string_conversion(self):
        """Test aspect ratio string is converted to enum."""
        config = GenerationConfig(input_source="test", aspect_ratio="1:1")
        assert config.aspect_ratio == AspectRatio.SQUARE

    def test_output_dir_string_conversion(self):
        """Test output_dir string is converted to Path."""
        config = GenerationConfig(input_source="test", output_dir="/tmp/test")
        assert isinstance(config.output_dir, Path)
        # Path normalization is platform-dependent
        assert config.output_dir == Path("/tmp/test")

    def test_resume_string_conversion(self):
        """Test resume string is converted to Path."""
        config = GenerationConfig(input_source="test", resume="/tmp/checkpoint.json")
        assert isinstance(config.resume, Path)

    def test_resume_empty_string_is_none(self):
        """Test empty resume string becomes None."""
        config = GenerationConfig(input_source="test", resume="")
        assert config.resume is None

    def test_to_metadata_dict(self):
        """Test serialization for metadata.json."""
        config = GenerationConfig(
            input_source="test",
            max_iterations=3,
            pass_threshold=0.80,
            resolution=Resolution.STANDARD,
            aspect_ratio=AspectRatio.SQUARE,
            image_count=5,
            style="custom",
            concurrency=2,
            no_cache=True,
        )
        metadata = config.to_metadata_dict()
        assert metadata["max_iterations"] == 3
        assert metadata["pass_threshold"] == 0.80
        assert metadata["resolution"] == "standard"
        assert metadata["aspect_ratio"] == "1:1"
        assert metadata["image_count"] == 5
        assert metadata["style"] == "custom"
        assert metadata["concurrency"] == 2
        assert metadata["no_cache"] is True

    def test_from_cli_and_env_defaults(self):
        """Test from_cli_and_env with default values."""
        config = GenerationConfig.from_cli_and_env(input_source="test")
        assert config.input_source == "test"
        assert config.style == "professional-clean"
        assert config.max_iterations == 5
        assert config.pass_threshold == 0.85

    def test_from_cli_and_env_with_values(self, tmp_path: Path):
        """Test from_cli_and_env with provided values."""
        config = GenerationConfig.from_cli_and_env(
            input_source="test",
            style="custom",
            output_dir=str(tmp_path),
            max_iterations=3,
            pass_threshold=0.80,
            resolution="standard",
            aspect_ratio="1:1",
            image_count=5,
            no_cache=True,
            dry_run=True,
            concurrency=2,
        )
        assert config.style == "custom"
        assert config.max_iterations == 3
        assert config.image_count == 5


class TestInternalConfig:
    """Tests for InternalConfig."""

    def test_default_values(self):
        """Test default internal config values."""
        config = InternalConfig()
        assert "no text" in config.negative_prompt
        assert config.cache_dir == Path(".cache/visual-explainer")
        assert config.cache_ttl_days == 0
        assert config.checkpoint_interval == 1
        assert config.gemini_timeout_seconds == 300.0
        assert config.claude_timeout_seconds == 60.0
        assert "gemini" in config.gemini_model.lower()
        assert "claude" in config.claude_model.lower()
        assert config.rate_limit_delay_seconds == 1.0

    def test_custom_values(self):
        """Test internal config with custom values."""
        config = InternalConfig(
            negative_prompt="custom negative",
            cache_dir=Path("/custom/cache"),
            gemini_timeout_seconds=120.0,
            claude_timeout_seconds=30.0,
        )
        assert config.negative_prompt == "custom negative"
        assert config.cache_dir == Path("/custom/cache")
        assert config.gemini_timeout_seconds == 120.0
        assert config.claude_timeout_seconds == 30.0

    def test_invalid_gemini_timeout_too_low(self):
        """Test gemini_timeout minimum is 30 seconds."""
        with pytest.raises(ValidationError):
            InternalConfig(gemini_timeout_seconds=25.0)

    def test_invalid_gemini_timeout_too_high(self):
        """Test gemini_timeout maximum is 600 seconds."""
        with pytest.raises(ValidationError):
            InternalConfig(gemini_timeout_seconds=700.0)

    def test_invalid_claude_timeout_too_low(self):
        """Test claude_timeout minimum is 10 seconds."""
        with pytest.raises(ValidationError):
            InternalConfig(claude_timeout_seconds=5.0)

    def test_from_env(self, monkeypatch):
        """Test creating from environment variables."""
        monkeypatch.setenv("VISUAL_EXPLAINER_GEMINI_TIMEOUT", "180.0")
        config = InternalConfig.from_env()
        assert config.gemini_timeout_seconds == 180.0


class TestPromptRecipe:
    """Tests for PromptRecipe."""

    def test_defaults(self):
        """Test PromptRecipe defaults."""
        recipe = PromptRecipe()
        assert recipe.style_prefix == ""
        assert recipe.core_style_prompt == ""
        assert recipe.quality_checklist == []

    def test_with_values(self):
        """Test PromptRecipe with values."""
        recipe = PromptRecipe(
            StylePrefix="Clean professional",
            CoreStylePrompt="modern illustration",
            ColorConstraintPrompt="blue palette",
            TextEnforcementPrompt="no text",
            NegativePrompt="cluttered",
            QualityChecklist=["Clear", "Professional"],
        )
        assert recipe.style_prefix == "Clean professional"
        assert recipe.core_style_prompt == "modern illustration"
        assert len(recipe.quality_checklist) == 2

    def test_get_combined_prompt(self):
        """Test combining prompts."""
        recipe = PromptRecipe(
            StylePrefix="Clean",
            CoreStylePrompt="modern",
            ColorConstraintPrompt="blue",
            TextEnforcementPrompt="no text",
        )
        combined = recipe.get_combined_prompt()
        assert "Clean" in combined
        assert "modern" in combined
        assert "blue" in combined
        assert "no text" in combined

    def test_get_combined_prompt_empty(self):
        """Test combining empty prompts."""
        recipe = PromptRecipe()
        combined = recipe.get_combined_prompt()
        assert combined == ""


class TestColorDefinition:
    """Tests for ColorDefinition."""

    def test_with_aliases(self):
        """Test ColorDefinition with alias names."""
        color = ColorDefinition(
            Name="Deep Blue",
            Hex="#1E3A5F",
            Role="Primary",
        )
        assert color.name == "Deep Blue"
        assert color.hex == "#1E3A5F"
        assert color.role == "Primary"
        assert color.usage_guidance is None

    def test_with_usage_guidance(self):
        """Test ColorDefinition with usage guidance."""
        color = ColorDefinition(
            Name="Accent",
            Hex="#3B82F6",
            Role="Highlights",
            UsageGuidance="Use sparingly",
        )
        assert color.usage_guidance == "Use sparingly"


class TestStyleConfig:
    """Tests for StyleConfig."""

    def test_minimal_style(self):
        """Test minimal StyleConfig."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(CoreStylePrompt="test"),
        )
        assert style.style_name == "Test"
        assert style.prompt_recipe.core_style_prompt == "test"

    def test_full_style(self):
        """Test full StyleConfig."""
        style = StyleConfig(
            SchemaVersion="1.2",
            StyleName="Full_Test",
            StyleIntent="Test style",
            ModelAndOutputProfiles={
                "ResolutionProfiles": {
                    "Landscape4K": {"Width": 3200, "Height": 1800, "AspectRatio": "16:9"}
                }
            },
            ColorSystem=ColorSystem(
                PaletteMode="Flexible",
                Background={"Base": "#FFFFFF"},
                PrimaryColors=[ColorDefinition(Name="Blue", Hex="#3B82F6", Role="Primary")],
            ),
            DesignPrinciples={"Clarity": "First"},
            PromptRecipe=PromptRecipe(
                StylePrefix="Professional",
                CoreStylePrompt="clean design",
            ),
        )
        assert style.schema_version == "1.2"
        assert style.style_name == "Full_Test"
        assert style.color_system is not None
        assert len(style.color_system.primary_colors) == 1

    def test_ensure_prompt_recipe_validator(self):
        """Test that missing PromptRecipe gets default."""
        # Model validator should add empty PromptRecipe if missing
        data = {"StyleName": "Test"}
        style = StyleConfig.model_validate(data)
        assert style.prompt_recipe is not None

    def test_get_resolution_profile(self):
        """Test getting resolution profile."""
        style = StyleConfig(
            StyleName="Test",
            ModelAndOutputProfiles={
                "ResolutionProfiles": {
                    "Landscape4K": {"Width": 3200, "Height": 1800, "AspectRatio": "16:9"}
                }
            },
            PromptRecipe=PromptRecipe(),
        )
        profile = style.get_resolution_profile("Landscape4K")
        assert profile is not None
        assert profile.width == 3200
        assert profile.height == 1800

    def test_get_resolution_profile_not_found(self):
        """Test getting non-existent resolution profile."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(),
        )
        profile = style.get_resolution_profile("NonExistent")
        assert profile is None

    def test_to_prompt_injection(self):
        """Test extracting prompt injection components."""
        style = StyleConfig(
            StyleName="Test",
            PromptRecipe=PromptRecipe(
                StylePrefix="Clean",
                CoreStylePrompt="modern",
                ColorConstraintPrompt="blue",
                TextEnforcementPrompt="no text",
                NegativePrompt="cluttered",
            ),
        )
        injection = style.to_prompt_injection()
        assert injection["style_prefix"] == "Clean"
        assert injection["core_style"] == "modern"
        assert injection["color_constraints"] == "blue"
        assert injection["text_rules"] == "no text"
        assert injection["negative"] == "cluttered"
        assert "Clean" in injection["combined"]


class TestDefaultStyle:
    """Tests for DEFAULT_STYLE constant."""

    def test_default_style_exists(self):
        """Test that DEFAULT_STYLE is defined."""
        assert DEFAULT_STYLE is not None
        assert isinstance(DEFAULT_STYLE, StyleConfig)

    def test_default_style_has_prompt_recipe(self):
        """Test DEFAULT_STYLE has prompt recipe."""
        assert DEFAULT_STYLE.prompt_recipe is not None
        assert DEFAULT_STYLE.prompt_recipe.core_style_prompt != ""

    def test_default_style_has_quality_checklist(self):
        """Test DEFAULT_STYLE has quality checklist."""
        assert len(DEFAULT_STYLE.prompt_recipe.quality_checklist) > 0
