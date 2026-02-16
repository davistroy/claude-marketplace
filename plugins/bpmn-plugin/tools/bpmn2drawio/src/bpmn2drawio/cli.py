"""Command-line interface for bpmn2drawio."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .converter import Converter
from .config import get_env_config


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="bpmn2drawio",
        description="Convert BPMN 2.0 XML to Draw.io diagrams",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bpmn2drawio input.bpmn output.drawio
  bpmn2drawio input.bpmn output.drawio --theme blueprint
  bpmn2drawio input.bpmn output.drawio --layout graphviz --direction TB
  bpmn2drawio input.bpmn output.drawio --config brand-config.yaml
        """,
    )

    parser.add_argument(
        "input",
        help="Input BPMN file",
    )

    parser.add_argument(
        "output",
        help="Output Draw.io file",
    )

    parser.add_argument(
        "--theme",
        choices=["default", "blueprint", "monochrome", "high_contrast"],
        default="default",
        help="Color theme (default: default)",
    )

    parser.add_argument(
        "--config",
        help="Brand configuration YAML file",
    )

    parser.add_argument(
        "--layout",
        choices=["graphviz", "preserve"],
        default="graphviz",
        help="Layout algorithm (default: graphviz)",
    )

    parser.add_argument(
        "--direction",
        choices=["LR", "TB", "RL", "BT"],
        default="LR",
        help="Flow direction (default: LR)",
    )

    parser.add_argument(
        "--no-grid",
        action="store_true",
        help="Disable grid in output",
    )

    parser.add_argument(
        "--page-size",
        choices=["A4", "letter", "auto"],
        default="auto",
        help="Page size (default: auto)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main(args=None):
    """Main entry point for CLI.

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Get environment configuration
    env_config = get_env_config()

    # Apply environment defaults
    theme = env_config.get("theme", parsed_args.theme)
    layout = env_config.get("layout", parsed_args.layout)
    direction = env_config.get("direction", parsed_args.direction)

    # Validate input file
    input_path = Path(parsed_args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {parsed_args.input}", file=sys.stderr)
        return 1

    # Create converter
    converter = Converter(
        layout=layout,
        theme=theme,
        config=parsed_args.config,
        direction=direction,
    )

    # Convert
    result = converter.convert(parsed_args.input, parsed_args.output)

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    # Print warnings
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    if parsed_args.verbose:
        print(f"Converted {result.element_count} elements")
        print(f"Converted {result.flow_count} flows")
        print(f"Output: {result.output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
