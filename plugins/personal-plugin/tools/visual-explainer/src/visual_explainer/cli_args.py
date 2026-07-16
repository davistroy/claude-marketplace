"""Argument parsing for the visual-explainer CLI.

Owns the argparse parser construction and the bounded-value validator
factories used by numeric CLI options, plus the package ``__version__``
surfaced by ``--version``.
"""

from __future__ import annotations

import argparse

# Version
__version__ = "0.1.0"


def _bounded_float(min_val: float, max_val: float, label: str):
    """Create an argparse type validator for bounded floats.

    Args:
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        label: Label for error messages.

    Returns:
        Validator function for argparse type parameter.
    """

    def validator(value: str) -> float:
        fval = float(value)
        if fval < min_val or fval > max_val:
            raise argparse.ArgumentTypeError(
                f"{label} must be between {min_val} and {max_val}, got {fval}"
            )
        return fval

    validator.__name__ = f"float[{min_val}-{max_val}]"
    return validator


def _bounded_int(min_val: int, max_val: int, label: str):
    """Create an argparse type validator for bounded integers.

    Args:
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        label: Label for error messages.

    Returns:
        Validator function for argparse type parameter.
    """

    def validator(value: str) -> int:
        ival = int(value)
        if ival < min_val or ival > max_val:
            raise argparse.ArgumentTypeError(
                f"{label} must be between {min_val} and {max_val}, got {ival}"
            )
        return ival

    validator.__name__ = f"int[{min_val}-{max_val}]"
    return validator


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="visual-explainer",
        description="Transform text or documents into AI-generated images that explain concepts visually",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for input)
  visual-explainer

  # Generate from a markdown file
  visual-explainer -i ./docs/concept.md

  # Generate with specific settings
  visual-explainer -i document.txt --style professional-sketch --max-iterations 3

  # Dry run to preview the generation plan
  visual-explainer -i document.txt --dry-run

  # Resume an interrupted generation
  visual-explainer --resume ./output/visual-explainer-topic-20260118/checkpoint.json
""",
    )

    # Main input argument
    parser.add_argument(
        "--input",
        "-i",
        dest="input_source",
        help="Input text, file path, or URL",
    )

    # Style selection
    parser.add_argument(
        "--style",
        "-s",
        default=None,
        help="Style name (bundled) or path to custom JSON (default: interactive selection)",
    )

    # Output configuration
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./output",
        help="Output directory (default: ./output)",
    )

    # Generation parameters
    parser.add_argument(
        "--max-iterations",
        type=_bounded_int(1, 20, "max-iterations"),
        default=5,
        help="Max refinement attempts per image (default: 5, range: 1-20)",
    )
    parser.add_argument(
        "--pass-threshold",
        type=_bounded_float(0.0, 1.0, "pass-threshold"),
        default=0.85,
        help="Min evaluation score to pass (default: 0.85, range: 0.0-1.0)",
    )
    parser.add_argument(
        "--image-count",
        type=int,
        default=0,
        help="Number of images to generate (default: 0 = auto based on content)",
    )

    # Image settings
    parser.add_argument(
        "--aspect-ratio",
        choices=["16:9", "1:1", "4:3", "9:16", "3:4"],
        default="16:9",
        help="Image aspect ratio (default: 16:9)",
    )
    parser.add_argument(
        "--resolution",
        choices=["standard", "high"],
        default="high",
        help="Image resolution - high=4K (default: high)",
    )
    # Cache and resume
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force fresh concept analysis (skip cache)",
    )
    parser.add_argument(
        "--resume",
        metavar="CHECKPOINT",
        help="Resume from a checkpoint file",
    )

    # Mode flags
    parser.add_argument(
        "--infographic",
        action="store_true",
        help="Generate information-dense infographic pages (11x17 inch format)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show generation plan without actually generating images",
    )
    parser.add_argument(
        "--setup-keys",
        action="store_true",
        help="Run API key setup wizard",
    )

    # Output format
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for programmatic use)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output (only show final summary)",
    )

    # Version
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser
