"""Configuration system for Visual Concept Explainer.

This module provides Pydantic models for all configuration options:
- GenerationConfig: User-configurable parameters (CLI args, env vars)
- InternalConfig: Non-exposed defaults (negative prompt, cache settings)
- StyleConfig: Style JSON schema matching bundled style files

Configuration priority: CLI args > environment variables > defaults
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator

# Load .env file with override to ensure it takes precedence
load_dotenv(override=True)


class Resolution(str, Enum):
    """Image resolution options."""

    STANDARD = "standard"  # 1280x720
    HIGH = "high"  # 3200x1800 (4K)
    ULTRA = "ultra"  # Reserved for future higher resolutions

    def get_gemini_size(self) -> str:
        """Get the Gemini API imageSize parameter."""
        return {
            Resolution.STANDARD: "STANDARD",
            Resolution.HIGH: "LARGE",
            Resolution.ULTRA: "LARGE",  # Currently same as HIGH
        }[self]


class AspectRatio(str, Enum):
    """Supported aspect ratios."""

    LANDSCAPE_16_9 = "16:9"
    SQUARE = "1:1"
    LANDSCAPE_4_3 = "4:3"
    PORTRAIT_9_16 = "9:16"
    PORTRAIT_3_4 = "3:4"


# Type alias for input types
InputType = Literal["text", "file", "url"]


class GenerationConfig(BaseModel):
    """User-configurable parameters for image generation.

    All parameters can be set via CLI arguments, environment variables,
    or fall back to defaults. CLI args have highest priority.

    Attributes:
        input_source: The input text, file path, or URL to process.
        style: Style name (bundled) or path to custom style JSON.
        output_dir: Directory for generated images and metadata.
        max_iterations: Maximum refinement attempts per image (1-10).
        pass_threshold: Score required to pass evaluation (0.0-1.0).
        resolution: Image resolution (standard, high, ultra).
        aspect_ratio: Image aspect ratio.
        image_count: Number of images to generate (0=auto).
        no_cache: Skip concept analysis cache.
        resume: Path to checkpoint file for resuming.
        dry_run: Show plan without generating images.
        setup_keys: Force API key setup wizard.
        concurrency: Max concurrent image generations (1-10).
    """

    input_source: str = Field(
        ...,
        description="Input text, file path, or URL to process",
        min_length=1,
    )
    style: str = Field(
        default="professional-clean",
        description="Style name (bundled) or path to custom style JSON file",
    )
    output_dir: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Output directory for generated images and metadata",
    )
    max_iterations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum refinement attempts per image (1-10)",
    )
    pass_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Score required to pass evaluation (0.0-1.0)",
    )
    resolution: Resolution = Field(
        default=Resolution.HIGH,
        description="Image resolution: standard (1280x720), high (3200x1800/4K), ultra",
    )
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.LANDSCAPE_16_9,
        description="Image aspect ratio",
    )
    image_count: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Number of images to generate (0=auto based on content analysis)",
    )
    no_cache: bool = Field(
        default=False,
        description="Skip concept analysis cache, force fresh analysis",
    )
    resume: Path | None = Field(
        default=None,
        description="Path to checkpoint file for resuming interrupted generation",
    )
    dry_run: bool = Field(
        default=False,
        description="Show generation plan without actually generating images",
    )
    setup_keys: bool = Field(
        default=False,
        description="Force API key setup wizard even if keys exist",
    )
    concurrency: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent image generations (1-10)",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def validate_output_dir(cls, v: Any) -> Path:
        """Convert string to Path and validate."""
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("resolution", mode="before")
    @classmethod
    def validate_resolution(cls, v: Any) -> Resolution:
        """Convert string to Resolution enum."""
        if isinstance(v, str):
            return Resolution(v.lower())
        return v

    @field_validator("aspect_ratio", mode="before")
    @classmethod
    def validate_aspect_ratio(cls, v: Any) -> AspectRatio:
        """Convert string to AspectRatio enum."""
        if isinstance(v, str):
            return AspectRatio(v)
        return v

    @field_validator("resume", mode="before")
    @classmethod
    def validate_resume(cls, v: Any) -> Path | None:
        """Convert string to Path if provided."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return Path(v)
        return v

    @classmethod
    def from_cli_and_env(
        cls,
        input_source: str,
        style: str | None = None,
        output_dir: str | None = None,
        max_iterations: int | None = None,
        pass_threshold: float | None = None,
        resolution: str | None = None,
        aspect_ratio: str | None = None,
        image_count: int | None = None,
        no_cache: bool = False,
        resume: str | None = None,
        dry_run: bool = False,
        setup_keys: bool = False,
        concurrency: int | None = None,
    ) -> "GenerationConfig":
        """Create config from CLI args with environment variable fallbacks.

        Priority: CLI arg > environment variable > default

        Args:
            input_source: Required input text, file path, or URL.
            style: Style name or path (env: VISUAL_EXPLAINER_STYLE).
            output_dir: Output directory (env: VISUAL_EXPLAINER_OUTPUT_DIR).
            max_iterations: Max attempts (env: VISUAL_EXPLAINER_MAX_ITERATIONS).
            pass_threshold: Pass score (env: VISUAL_EXPLAINER_PASS_THRESHOLD).
            resolution: Image resolution (env: VISUAL_EXPLAINER_RESOLUTION).
            aspect_ratio: Aspect ratio (env: VISUAL_EXPLAINER_ASPECT_RATIO).
            image_count: Image count (env: VISUAL_EXPLAINER_IMAGE_COUNT).
            no_cache: Skip cache flag.
            resume: Checkpoint path.
            dry_run: Dry run flag.
            setup_keys: Force setup flag.
            concurrency: Concurrent generations (env: VISUAL_EXPLAINER_CONCURRENCY).

        Returns:
            Validated GenerationConfig instance.
        """
        # Helper to get env var with type conversion
        def env_int(key: str, default: int) -> int:
            val = os.getenv(key)
            return int(val) if val else default

        def env_float(key: str, default: float) -> float:
            val = os.getenv(key)
            return float(val) if val else default

        def env_str(key: str, default: str) -> str:
            return os.getenv(key, default)

        return cls(
            input_source=input_source,
            style=style or env_str("VISUAL_EXPLAINER_STYLE", "professional-clean"),
            output_dir=output_dir or env_str("VISUAL_EXPLAINER_OUTPUT_DIR", str(Path.cwd())),
            max_iterations=max_iterations or env_int("VISUAL_EXPLAINER_MAX_ITERATIONS", 5),
            pass_threshold=pass_threshold or env_float("VISUAL_EXPLAINER_PASS_THRESHOLD", 0.85),
            resolution=resolution or env_str("VISUAL_EXPLAINER_RESOLUTION", "high"),
            aspect_ratio=aspect_ratio or env_str("VISUAL_EXPLAINER_ASPECT_RATIO", "16:9"),
            image_count=image_count if image_count is not None else env_int("VISUAL_EXPLAINER_IMAGE_COUNT", 0),
            no_cache=no_cache,
            resume=resume,
            dry_run=dry_run,
            setup_keys=setup_keys,
            concurrency=concurrency or env_int("VISUAL_EXPLAINER_CONCURRENCY", 3),
        )

    def to_metadata_dict(self) -> dict[str, Any]:
        """Serialize config for metadata.json output."""
        return {
            "max_iterations": self.max_iterations,
            "pass_threshold": self.pass_threshold,
            "resolution": self.resolution.value,
            "aspect_ratio": self.aspect_ratio.value,
            "image_count": self.image_count,
            "style": self.style,
            "concurrency": self.concurrency,
            "no_cache": self.no_cache,
        }


class InternalConfig(BaseModel):
    """Non-exposed internal configuration defaults.

    These settings are not configurable via CLI but control
    internal behavior. Advanced users can override via environment
    variables or programmatically.

    Attributes:
        negative_prompt: Default negative prompt applied to all generations.
        cache_dir: Directory for concept analysis cache.
        cache_ttl_days: Cache time-to-live (0=indefinite).
        checkpoint_interval: Save checkpoint after every N images.
        gemini_timeout_seconds: Timeout for Gemini API calls.
        claude_timeout_seconds: Timeout for Claude API calls.
        gemini_model: Model ID for image generation.
        claude_model: Model ID for evaluation.
        rate_limit_delay_seconds: Delay between API calls to avoid rate limits.
    """

    negative_prompt: str = Field(
        default=(
            "no text, no words, no letters, no numbers, no watermarks, no logos, "
            "no stock photo aesthetic, no borders, no frames, no signatures, "
            "no artificial lighting artifacts, no lens flare"
        ),
        description="Default negative prompt applied to all image generations",
    )
    cache_dir: Path = Field(
        default_factory=lambda: Path(".cache/visual-explainer"),
        description="Directory for concept analysis cache",
    )
    cache_ttl_days: int = Field(
        default=0,
        ge=0,
        description="Cache TTL in days (0=indefinite, invalidated by content change)",
    )
    checkpoint_interval: int = Field(
        default=1,
        ge=1,
        description="Save checkpoint after every N images completed",
    )
    gemini_timeout_seconds: float = Field(
        default=300.0,
        ge=30.0,
        le=600.0,
        description="Timeout for Gemini API calls (4K images need ~300s)",
    )
    claude_timeout_seconds: float = Field(
        default=60.0,
        ge=10.0,
        le=300.0,
        description="Timeout for Claude API calls",
    )
    gemini_model: str = Field(
        default="gemini-3-pro-image-preview",
        description="Gemini model ID for image generation",
    )
    claude_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model ID for concept analysis and evaluation",
    )
    rate_limit_delay_seconds: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Minimum delay between API calls",
    )

    @classmethod
    def from_env(cls) -> "InternalConfig":
        """Create config from environment variables with defaults."""
        return cls(
            negative_prompt=os.getenv("VISUAL_EXPLAINER_NEGATIVE_PROMPT", cls.model_fields["negative_prompt"].default),
            cache_dir=Path(os.getenv("VISUAL_EXPLAINER_CACHE_DIR", ".cache/visual-explainer")),
            gemini_timeout_seconds=float(os.getenv("VISUAL_EXPLAINER_GEMINI_TIMEOUT", "300.0")),
            claude_timeout_seconds=float(os.getenv("VISUAL_EXPLAINER_CLAUDE_TIMEOUT", "60.0")),
            gemini_model=os.getenv("VISUAL_EXPLAINER_GEMINI_MODEL", "gemini-3-pro-image-preview"),
            claude_model=os.getenv("VISUAL_EXPLAINER_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        )


class ColorDefinition(BaseModel):
    """Color definition within a style."""

    name: str = Field(description="Human-readable color name")
    hex: str = Field(alias="Hex", description="Hex color code")
    role: str = Field(alias="Role", description="How this color should be used")

    model_config = {"populate_by_name": True}


class ResolutionProfile(BaseModel):
    """Resolution profile for output images."""

    width: int = Field(alias="Width")
    height: int = Field(alias="Height")
    aspect_ratio: str = Field(alias="AspectRatio")

    model_config = {"populate_by_name": True}


class ColorSystem(BaseModel):
    """Color system configuration."""

    palette_mode: str = Field(alias="PaletteMode", default="Strict")
    background: dict[str, str] = Field(alias="Background", default_factory=dict)
    primary_colors: list[ColorDefinition] = Field(alias="PrimaryColors", default_factory=list)
    color_usage_rules: dict[str, Any] = Field(alias="ColorUsageRules", default_factory=dict)

    model_config = {"populate_by_name": True}


class PromptRecipe(BaseModel):
    """Prompt recipe for style injection into image generation.

    These components are combined to create the final image prompt.
    """

    style_prefix: str = Field(alias="StylePrefix", default="")
    core_style_prompt: str = Field(alias="CoreStylePrompt", default="")
    color_constraint_prompt: str = Field(alias="ColorConstraintPrompt", default="")
    text_enforcement_prompt: str = Field(alias="TextEnforcementPrompt", default="")
    negative_prompt: str = Field(alias="NegativePrompt", default="")
    quality_checklist: list[str] = Field(alias="QualityChecklist", default_factory=list)

    model_config = {"populate_by_name": True}

    def get_combined_prompt(self) -> str:
        """Combine all style prompts into a single string."""
        parts = []
        if self.style_prefix:
            parts.append(self.style_prefix)
        if self.core_style_prompt:
            parts.append(self.core_style_prompt)
        if self.color_constraint_prompt:
            parts.append(self.color_constraint_prompt)
        if self.text_enforcement_prompt:
            parts.append(self.text_enforcement_prompt)
        return " ".join(parts)


class StyleConfig(BaseModel):
    """Complete style configuration matching bundled style JSON schema.

    This model validates style files and provides structured access
    to style components for prompt injection.
    """

    schema_version: str = Field(alias="SchemaVersion", default="1.2")
    style_name: str = Field(alias="StyleName")
    style_intent: str = Field(alias="StyleIntent", default="")
    model_and_output_profiles: dict[str, Any] = Field(
        alias="ModelAndOutputProfiles",
        default_factory=dict,
    )
    color_system: ColorSystem | None = Field(alias="ColorSystem", default=None)
    design_principles: dict[str, str] = Field(alias="DesignPrinciples", default_factory=dict)
    prompt_recipe: PromptRecipe = Field(alias="PromptRecipe")

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def ensure_prompt_recipe(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure PromptRecipe exists with at least empty defaults."""
        if "PromptRecipe" not in values and "prompt_recipe" not in values:
            values["PromptRecipe"] = {}
        return values

    def get_resolution_profile(self, name: str = "Landscape4K") -> ResolutionProfile | None:
        """Get a specific resolution profile by name."""
        profiles = self.model_and_output_profiles.get("ResolutionProfiles", {})
        if name in profiles:
            return ResolutionProfile(**profiles[name])
        return None

    def to_prompt_injection(self) -> dict[str, str]:
        """Extract prompt components for injection into generation prompts."""
        return {
            "style_prefix": self.prompt_recipe.style_prefix,
            "core_style": self.prompt_recipe.core_style_prompt,
            "color_constraints": self.prompt_recipe.color_constraint_prompt,
            "text_rules": self.prompt_recipe.text_enforcement_prompt,
            "negative": self.prompt_recipe.negative_prompt,
            "combined": self.prompt_recipe.get_combined_prompt(),
        }


# Default style configuration for fallback
DEFAULT_STYLE = StyleConfig(
    SchemaVersion="1.2",
    StyleName="Visual_Explainer_Default",
    StyleIntent="Clean, professional visualization style for concept explanation",
    PromptRecipe=PromptRecipe(
        StylePrefix="Clean, professional presentation graphic",
        CoreStylePrompt=(
            "modern professional illustration, clean lines, minimalist design, "
            "clear visual hierarchy, balanced composition, professional business aesthetic"
        ),
        ColorConstraintPrompt="use a professional color palette with blues and neutral tones",
        TextEnforcementPrompt="no text or labels in the image",
        NegativePrompt=(
            "cluttered, messy, neon colors, garish, 3D effects, "
            "photorealistic, stock photo, watermarks, text, words"
        ),
        QualityChecklist=[
            "Clean, uncluttered layout",
            "Professional appearance",
            "Clear visual hierarchy",
            "Appropriate for business context",
        ],
    ),
)
