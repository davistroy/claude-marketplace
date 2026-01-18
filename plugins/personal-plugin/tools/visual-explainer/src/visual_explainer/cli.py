"""Command-line interface for visual-explainer.

This is a placeholder that will be implemented in Phase 4 (Work Item 4.2).
The --setup-keys flag is implemented in Phase 1 (Work Item 1.3).
"""

import argparse
import sys

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="visual-explainer",
        description="Transform text or documents into AI-generated images that explain concepts visually",
    )

    parser.add_argument(
        "--input", "-i",
        dest="input_source",
        help="Input text, file path, or URL",
    )
    parser.add_argument(
        "--style", "-s",
        default="professional-clean",
        help="Style name or path (default: professional-clean)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Max refinement attempts per image (default: 5)",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.85,
        help="Min evaluation score to pass (default: 0.85)",
    )
    parser.add_argument(
        "--aspect-ratio",
        choices=["16:9", "1:1", "4:3", "9:16", "3:4"],
        default="16:9",
        help="Image aspect ratio (default: 16:9)",
    )
    parser.add_argument(
        "--resolution",
        choices=["low", "medium", "high"],
        default="high",
        help="Image resolution - high=4K (default: high)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force fresh concept analysis (skip cache)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show generation plan without actually generating images",
    )
    parser.add_argument(
        "--resume",
        metavar="CHECKPOINT",
        help="Resume from a checkpoint file",
    )
    parser.add_argument(
        "--setup-keys",
        action="store_true",
        help="Run API key setup wizard",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def main() -> int:
    """Main entry point for the visual-explainer CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle --setup-keys flag
    if args.setup_keys:
        from visual_explainer.api_setup import handle_setup_keys_flag
        return handle_setup_keys_flag()

    # If no input provided and not in setup mode, show help
    if args.input_source is None:
        print("Visual Explainer v0.1.0")
        print()
        print("Full CLI implementation coming in Phase 4.")
        print("Currently implemented: --setup-keys (API key setup wizard)")
        print()
        print("To set up API keys, run:")
        print("  visual-explainer --setup-keys")
        print()
        print("For full help:")
        print("  visual-explainer --help")
        return 0

    # Check for API keys before proceeding
    from visual_explainer.api_setup import check_keys_and_prompt_if_missing
    if not check_keys_and_prompt_if_missing():
        print("\nCannot proceed without API keys configured.")
        print("Run: visual-explainer --setup-keys")
        return 1

    # Placeholder for actual generation logic (Phase 4)
    print("Visual Explainer v0.1.0")
    print()
    print(f"Input: {args.input_source}")
    print(f"Style: {args.style}")
    print(f"Output: {args.output_dir}")
    print(f"Max iterations: {args.max_iterations}")
    print(f"Pass threshold: {args.pass_threshold}")
    print(f"Aspect ratio: {args.aspect_ratio}")
    print(f"Resolution: {args.resolution}")
    print()
    print("Generation pipeline not yet implemented - coming in Phase 4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
