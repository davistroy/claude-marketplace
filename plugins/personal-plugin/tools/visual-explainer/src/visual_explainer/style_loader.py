"""Style loader for Visual Concept Explainer.

This module handles loading style configurations with the following priority:
1. User-provided path (full path to custom JSON file)
2. Named bundled style ("professional-clean" -> styles/professional-clean.json)
3. Default "professional-clean" when no style specified

Uses importlib.resources for accessing bundled styles in the package.
Includes caching to avoid re-loading the same style multiple times.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from .config import DEFAULT_STYLE, PromptRecipe, StyleConfig

if TYPE_CHECKING:
    from importlib.abc import Traversable

logger = logging.getLogger(__name__)

# Default style name when none specified
DEFAULT_STYLE_NAME = "professional-clean"

# Cache for loaded styles (path/name -> StyleConfig)
_style_cache: dict[str, StyleConfig] = {}


class StyleLoadError(Exception):
    """Raised when a style file cannot be loaded or validated."""

    def __init__(self, style_ref: str, reason: str) -> None:
        self.style_ref = style_ref
        self.reason = reason
        super().__init__(f"Failed to load style '{style_ref}': {reason}")


def get_bundled_styles_path() -> Path | None:
    """Get the path to bundled styles directory.

    Returns:
        Path to the styles directory, or None if not found.
    """
    # Try to locate styles relative to the package
    # The styles are at: tools/visual-explainer/styles/
    # The package is at: tools/visual-explainer/src/visual_explainer/
    package_dir = Path(__file__).parent
    tool_root = package_dir.parent.parent  # Up to tools/visual-explainer/
    styles_dir = tool_root / "styles"

    if styles_dir.is_dir():
        return styles_dir

    return None


@lru_cache(maxsize=16)
def discover_bundled_styles() -> dict[str, Path]:
    """Discover all available bundled style files.

    Returns:
        Dictionary mapping style names to their file paths.
        E.g., {"professional-clean": Path(".../professional-clean.json")}
    """
    styles: dict[str, Path] = {}

    styles_dir = get_bundled_styles_path()
    if styles_dir is None:
        logger.warning("Bundled styles directory not found")
        return styles

    for style_file in styles_dir.glob("*.json"):
        # Style name is the filename without extension
        style_name = style_file.stem
        styles[style_name] = style_file
        logger.debug("Discovered bundled style: %s at %s", style_name, style_file)

    return styles


def load_style(style_arg: str | None) -> StyleConfig:
    """Load a style configuration.

    Resolution priority:
    1. If style_arg is a path to an existing file, load it as custom style
    2. If style_arg is a name, look up in bundled styles
    3. If style_arg is None, return default "professional-clean"

    Args:
        style_arg: Style name (e.g., "professional-clean") or path to JSON file,
                   or None for default.

    Returns:
        Validated StyleConfig instance.

    Raises:
        StyleLoadError: If the style cannot be loaded or validated.
    """
    # Check cache first
    cache_key = style_arg or DEFAULT_STYLE_NAME
    if cache_key in _style_cache:
        logger.debug("Returning cached style: %s", cache_key)
        return _style_cache[cache_key]

    # Determine which style to load
    if style_arg is None:
        style_arg = DEFAULT_STYLE_NAME

    # Try loading
    style_config = _resolve_and_load_style(style_arg)

    # Cache and return
    _style_cache[cache_key] = style_config
    return style_config


def _resolve_and_load_style(style_arg: str) -> StyleConfig:
    """Resolve and load a style from path or name.

    Args:
        style_arg: Style name or file path.

    Returns:
        Loaded and validated StyleConfig.

    Raises:
        StyleLoadError: If the style cannot be found or is invalid.
    """
    # Check if it's a file path
    style_path = Path(style_arg)
    if style_path.is_file():
        logger.info("Loading custom style from path: %s", style_path)
        return _load_style_from_file(style_path)

    # Check if it looks like a path but doesn't exist
    if style_path.suffix == ".json" or "/" in style_arg or "\\" in style_arg:
        raise StyleLoadError(
            style_arg,
            f"File not found. Ensure the path exists: {style_path.absolute()}",
        )

    # Try to find as bundled style
    bundled_styles = discover_bundled_styles()
    if style_arg in bundled_styles:
        logger.info("Loading bundled style: %s", style_arg)
        return _load_style_from_file(bundled_styles[style_arg])

    # Style not found
    available = ", ".join(sorted(bundled_styles.keys())) or "none found"
    raise StyleLoadError(
        style_arg,
        f"Style '{style_arg}' not found. Available bundled styles: {available}. "
        f"Or provide a path to a custom JSON file.",
    )


def _load_style_from_file(file_path: Path) -> StyleConfig:
    """Load and validate a style from a JSON file.

    Args:
        file_path: Path to the style JSON file.

    Returns:
        Validated StyleConfig instance.

    Raises:
        StyleLoadError: If the file cannot be read or parsed.
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise StyleLoadError(str(file_path), f"Invalid JSON: {e}") from e
    except OSError as e:
        raise StyleLoadError(str(file_path), f"Cannot read file: {e}") from e

    return _validate_style_data(data, str(file_path))


def _validate_style_data(data: dict, source: str) -> StyleConfig:
    """Validate style data against the StyleConfig model.

    Args:
        data: Raw JSON data to validate.
        source: Source identifier for error messages.

    Returns:
        Validated StyleConfig instance.

    Raises:
        StyleLoadError: If validation fails.
    """
    try:
        return StyleConfig.model_validate(data)
    except ValidationError as e:
        # Format validation errors nicely
        errors = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"  - {loc}: {msg}")
        error_details = "\n".join(errors)
        raise StyleLoadError(
            source,
            f"Style validation failed:\n{error_details}",
        ) from e


def get_prompt_recipe(style: StyleConfig) -> PromptRecipe:
    """Extract the PromptRecipe from a style configuration.

    Args:
        style: Loaded StyleConfig instance.

    Returns:
        The PromptRecipe for prompt injection.
    """
    return style.prompt_recipe


def format_prompt_injection(style: StyleConfig) -> dict[str, str]:
    """Format style components for injection into image generation prompts.

    This extracts the relevant PromptRecipe sections and formats them
    for easy integration into the prompt generation pipeline.

    Args:
        style: Loaded StyleConfig instance.

    Returns:
        Dictionary with formatted prompt components:
        - style_prefix: Opening style description
        - core_style: Main style characteristics
        - color_constraints: Color palette guidance
        - text_rules: Text/typography rules
        - negative: Negative prompt (things to avoid)
        - combined: All positive prompts combined
        - quality_checklist: List of quality criteria as formatted string
    """
    recipe = style.prompt_recipe

    # Build the combined positive prompt
    combined_parts = []
    if recipe.style_prefix:
        combined_parts.append(recipe.style_prefix)
    if recipe.core_style_prompt:
        combined_parts.append(recipe.core_style_prompt)
    if recipe.color_constraint_prompt:
        combined_parts.append(recipe.color_constraint_prompt)
    if recipe.text_enforcement_prompt:
        combined_parts.append(recipe.text_enforcement_prompt)

    # Format quality checklist
    checklist_formatted = ""
    if recipe.quality_checklist:
        checklist_formatted = "\n".join(f"- {item}" for item in recipe.quality_checklist)

    return {
        "style_prefix": recipe.style_prefix,
        "core_style": recipe.core_style_prompt,
        "color_constraints": recipe.color_constraint_prompt,
        "text_rules": recipe.text_enforcement_prompt,
        "negative": recipe.negative_prompt,
        "combined": " ".join(combined_parts),
        "quality_checklist": checklist_formatted,
    }


def get_style_summary(style: StyleConfig) -> dict[str, str]:
    """Get a human-readable summary of a style.

    Useful for displaying style information to users.

    Args:
        style: Loaded StyleConfig instance.

    Returns:
        Dictionary with style summary information.
    """
    color_info = "Default palette"
    if style.color_system and style.color_system.primary_colors:
        color_names = [c.name for c in style.color_system.primary_colors[:3]]
        color_info = ", ".join(color_names)

    return {
        "name": style.style_name,
        "intent": style.style_intent,
        "version": style.schema_version,
        "colors": color_info,
    }


def list_available_styles() -> list[dict[str, str]]:
    """List all available styles with their summaries.

    Returns:
        List of style information dictionaries.
    """
    styles_info = []
    bundled = discover_bundled_styles()

    for name, path in sorted(bundled.items()):
        try:
            style = _load_style_from_file(path)
            info = get_style_summary(style)
            info["path"] = str(path)
            info["bundled"] = "yes"
            styles_info.append(info)
        except StyleLoadError as e:
            logger.warning("Could not load style %s: %s", name, e)
            styles_info.append({
                "name": name,
                "intent": f"(Error loading: {e.reason})",
                "path": str(path),
                "bundled": "yes",
            })

    return styles_info


def clear_style_cache() -> None:
    """Clear the style cache.

    Useful for testing or when styles may have changed on disk.
    """
    _style_cache.clear()
    discover_bundled_styles.cache_clear()
    logger.debug("Style cache cleared")


def get_default_style() -> StyleConfig:
    """Get the default style configuration.

    This returns a built-in default if the bundled "professional-clean"
    style cannot be loaded.

    Returns:
        StyleConfig instance for the default style.
    """
    try:
        return load_style(DEFAULT_STYLE_NAME)
    except StyleLoadError:
        logger.warning(
            "Could not load bundled default style '%s', using built-in fallback",
            DEFAULT_STYLE_NAME,
        )
        return DEFAULT_STYLE
