"""Command-line interface for visual-explainer.

This module provides the full CLI orchestrator that ties together all components
of the visual-explainer pipeline:

1. Load config from CLI args/env
2. Check/setup API keys
3. Load input (text/file/URL)
4. Analyze concepts (or load from cache)
5. Load style
6. Generate prompts
7. For each image: generate -> evaluate -> refine loop
8. Save outputs
9. Display summary

Uses Rich for formatted output (progress bars, tables, panels).

The implementation is split across cohesive modules:

- ``terminal``  — console singleton, Rich availability, TTY/Unicode probes
- ``cli_args``  — argparse parser and bounded-value validators
- ``io_utils``  — atomic file writes
- ``reporting`` — Rich rendering and interactive prompts
- ``pipeline``  — the end-to-end generation and resume orchestrators

``cli`` keeps the import-time environment setup, ``main`` dispatch, and
re-exports the public entry contract so existing imports and
``unittest.mock.patch("visual_explainer.cli.<symbol>")`` targets keep working.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Set PYTHONIOENCODING for Windows console compatibility
if "PYTHONIOENCODING" not in os.environ:
    os.environ["PYTHONIOENCODING"] = "utf-8"

from . import terminal  # noqa: E402
from .cli_args import (  # noqa: E402
    __version__,
    _bounded_float,
    _bounded_int,
    create_parser,
)
from .config import (  # noqa: E402
    GenerationConfig,
    InternalConfig,
)
from .io_utils import _atomic_write_text  # noqa: E402
from .pipeline import (  # noqa: E402
    _analyze_concepts,
    _evaluate_and_refine,
    _execute_generation_loop,
    _generate_prompts,
    _save_outputs,
    load_checkpoint_and_resume,
    run_generation_pipeline,
)
from .reporting import (  # noqa: E402
    GenerationProgress,
    display_analysis_summary,
    display_completion_summary,
    display_dry_run_plan,
    display_welcome,
    estimate_cost,
    prompt_for_image_count,
    prompt_for_input,
    prompt_for_style,
)
from .terminal import (  # noqa: E402
    RICH_AVAILABLE,
    get_console,
    is_interactive,
    supports_unicode,
)

# Public entry contract. Terminal singletons are additionally referenced
# module-qualified (``terminal.<symbol>``) inside ``main`` so patches on
# ``visual_explainer.terminal.<symbol>`` intercept dispatch; the re-exports
# below keep ``from visual_explainer.cli import <symbol>`` working.
__all__ = [
    "main",
    "__version__",
    # cli_args
    "create_parser",
    "_bounded_float",
    "_bounded_int",
    # terminal
    "is_interactive",
    "supports_unicode",
    "get_console",
    "RICH_AVAILABLE",
    # config
    "GenerationConfig",
    "InternalConfig",
    # io_utils
    "_atomic_write_text",
    # reporting
    "GenerationProgress",
    "display_welcome",
    "display_analysis_summary",
    "display_dry_run_plan",
    "display_completion_summary",
    "estimate_cost",
    "prompt_for_style",
    "prompt_for_image_count",
    "prompt_for_input",
    # pipeline
    "run_generation_pipeline",
    "load_checkpoint_and_resume",
    "_analyze_concepts",
    "_generate_prompts",
    "_evaluate_and_refine",
    "_execute_generation_loop",
    "_save_outputs",
]


def main() -> int:
    """Main entry point for the visual-explainer CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle --setup-keys flag
    if args.setup_keys:
        from visual_explainer.api_setup import handle_setup_keys_flag

        return handle_setup_keys_flag()

    # Handle --resume flag
    if args.resume:
        checkpoint_path = Path(args.resume)
        config = GenerationConfig.from_cli_and_env(
            input_source=args.input_source or "",
            style=args.style,
            output_dir=args.output_dir,
            max_iterations=args.max_iterations,
            pass_threshold=args.pass_threshold,
            resolution=args.resolution,
            aspect_ratio=args.aspect_ratio,
            image_count=args.image_count,
            no_cache=args.no_cache,
            dry_run=args.dry_run,
        )
        result = asyncio.run(
            load_checkpoint_and_resume(
                checkpoint_path,
                config,
                quiet=args.quiet,
                json_output=args.json,
            )
        )
        if args.json:
            print(json.dumps(result, indent=2))
        return 0 if result.get("status") != "error" else 1

    # Interactive mode if no input provided
    if args.input_source is None:
        if args.json:
            print(json.dumps({"error": "No input provided. Use --input or -i flag."}))
            return 1

        # Non-interactive mode without input is an error
        if not terminal.is_interactive():
            print("Error: No input provided and not running interactively.")
            print("Use --input or -i flag to provide input.")
            return 1

        if not terminal.RICH_AVAILABLE:
            print("Interactive mode requires Rich library. Install with: pip install rich")
            print("Or provide input with: visual-explainer --input <text|file|url>")
            return 1

        display_welcome()

        # Check for API keys first
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        if not check_keys_and_prompt_if_missing():
            print("\nCannot proceed without API keys configured.")
            print("Run: visual-explainer --setup-keys")
            return 1

        # Prompt for input
        input_source = prompt_for_input()
        if not input_source.strip():
            print("No input provided. Exiting.")
            return 1
    else:
        input_source = args.input_source

        # Check for API keys before proceeding
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        # Skip interactive key prompts in non-interactive mode
        if not args.json and terminal.is_interactive() and not check_keys_and_prompt_if_missing():
            print("\nCannot proceed without API keys configured.")
            print("Run: visual-explainer --setup-keys")
            return 1
        elif not args.json and not terminal.is_interactive():
            # In non-interactive mode, just check if keys exist
            from visual_explainer.api_setup import check_api_keys

            status = check_api_keys()
            if not status["google"]["present"] or not status["anthropic"]["present"]:
                print("Error: Missing required API keys.")
                missing = []
                if not status["google"]["present"]:
                    missing.append("GOOGLE_API_KEY")
                if not status["anthropic"]["present"]:
                    missing.append("ANTHROPIC_API_KEY")
                print(f"Missing: {', '.join(missing)}")
                print("Set environment variables or run: visual-explainer --setup-keys")
                return 1

    # Build configuration
    try:
        config = GenerationConfig.from_cli_and_env(
            input_source=input_source,
            style=args.style,
            output_dir=args.output_dir,
            max_iterations=args.max_iterations,
            pass_threshold=args.pass_threshold,
            resolution=args.resolution,
            aspect_ratio=args.aspect_ratio,
            image_count=args.image_count,
            no_cache=args.no_cache,
            dry_run=args.dry_run,
        )
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Configuration error: {e}")
        return 1

    # Load internal config
    internal_config = InternalConfig.from_env()

    # Determine style (interactive selection if not specified and in interactive mode)
    style_name = args.style
    if (
        style_name is None
        and not args.quiet
        and not args.json
        and terminal.RICH_AVAILABLE
        and terminal.is_interactive()
    ):
        style_name = prompt_for_style()

    if style_name is None:
        style_name = "professional-clean"

    # Run the generation pipeline
    try:
        result = asyncio.run(
            run_generation_pipeline(
                config=config,
                internal_config=internal_config,
                style_name=style_name,
                quiet=args.quiet,
                json_output=args.json,
                infographic_mode=args.infographic,
            )
        )

        if args.json:
            print(json.dumps(result, indent=2))

        return 0 if result.get("status") in ("complete", "dry_run") else 1

    except KeyboardInterrupt:
        if not args.json:
            print("\n\nGeneration interrupted by user.")
        return 130
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            console = terminal.get_console() if terminal.RICH_AVAILABLE else None
            if console:
                console.print(f"[red]Error: {e}[/red]")
            else:
                print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
