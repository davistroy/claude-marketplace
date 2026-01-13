"""Configuration loading for brand customization."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .themes import BPMNTheme, THEMES
from .exceptions import ConfigurationError


def load_brand_config(config_path: str) -> BPMNTheme:
    """Load brand configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configured BPMNTheme

    Raises:
        ConfigurationError: If configuration is invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in configuration: {e}") from e

    if not config:
        return BPMNTheme()

    # Get base theme if specified
    base_theme_name = config.get("base_theme", "default")
    base_theme = THEMES.get(base_theme_name, BPMNTheme())

    # Merge with config values
    return merge_theme_with_config(base_theme, config)


def merge_theme_with_config(
    base_theme: BPMNTheme,
    config: Dict[str, Any],
) -> BPMNTheme:
    """Override theme values with config values.

    Args:
        base_theme: Base theme to extend
        config: Configuration dictionary

    Returns:
        New BPMNTheme with merged values
    """
    # Create dict of base theme values
    theme_dict = {
        "start_event_fill": base_theme.start_event_fill,
        "start_event_stroke": base_theme.start_event_stroke,
        "end_event_fill": base_theme.end_event_fill,
        "end_event_stroke": base_theme.end_event_stroke,
        "intermediate_event_fill": base_theme.intermediate_event_fill,
        "intermediate_event_stroke": base_theme.intermediate_event_stroke,
        "task_fill": base_theme.task_fill,
        "task_stroke": base_theme.task_stroke,
        "script_task_fill": base_theme.script_task_fill,
        "script_task_stroke": base_theme.script_task_stroke,
        "business_rule_task_fill": base_theme.business_rule_task_fill,
        "business_rule_task_stroke": base_theme.business_rule_task_stroke,
        "manual_task_fill": base_theme.manual_task_fill,
        "manual_task_stroke": base_theme.manual_task_stroke,
        "gateway_fill": base_theme.gateway_fill,
        "gateway_stroke": base_theme.gateway_stroke,
        "pool_fill": base_theme.pool_fill,
        "pool_stroke": base_theme.pool_stroke,
        "lane_fill": base_theme.lane_fill,
        "lane_stroke": base_theme.lane_stroke,
        "sequence_flow_stroke": base_theme.sequence_flow_stroke,
        "message_flow_stroke": base_theme.message_flow_stroke,
        "font_family": base_theme.font_family,
        "font_size": base_theme.font_size,
        "font_color": base_theme.font_color,
    }

    # Apply config overrides
    colors = config.get("colors", {})
    for key, value in colors.items():
        if key in theme_dict:
            theme_dict[key] = value

    # Handle nested sections
    events = colors.get("events", {})
    if "start_fill" in events:
        theme_dict["start_event_fill"] = events["start_fill"]
    if "start_stroke" in events:
        theme_dict["start_event_stroke"] = events["start_stroke"]
    if "end_fill" in events:
        theme_dict["end_event_fill"] = events["end_fill"]
    if "end_stroke" in events:
        theme_dict["end_event_stroke"] = events["end_stroke"]

    tasks = colors.get("tasks", {})
    if "fill" in tasks:
        theme_dict["task_fill"] = tasks["fill"]
    if "stroke" in tasks:
        theme_dict["task_stroke"] = tasks["stroke"]

    gateways = colors.get("gateways", {})
    if "fill" in gateways:
        theme_dict["gateway_fill"] = gateways["fill"]
    if "stroke" in gateways:
        theme_dict["gateway_stroke"] = gateways["stroke"]

    # Handle fonts
    fonts = config.get("fonts", {})
    if "family" in fonts:
        theme_dict["font_family"] = fonts["family"]
    if "size" in fonts:
        theme_dict["font_size"] = fonts["size"]
    if "color" in fonts:
        theme_dict["font_color"] = fonts["color"]

    return BPMNTheme(**theme_dict)


def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables.

    Returns:
        Configuration dictionary
    """
    config = {}

    theme = os.environ.get("BPMN2DRAWIO_THEME")
    if theme:
        config["theme"] = theme

    layout = os.environ.get("BPMN2DRAWIO_LAYOUT")
    if layout:
        config["layout"] = layout

    direction = os.environ.get("BPMN2DRAWIO_DIRECTION")
    if direction:
        config["direction"] = direction

    graphviz_path = os.environ.get("BPMN2DRAWIO_GRAPHVIZ_PATH")
    if graphviz_path:
        config["graphviz_path"] = graphviz_path

    return config
