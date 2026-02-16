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
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Set PYTHONIOENCODING for Windows console compatibility
if "PYTHONIOENCODING" not in os.environ:
    os.environ["PYTHONIOENCODING"] = "utf-8"


def is_interactive() -> bool:
    """Check if we're running in an interactive terminal.

    Returns:
        True if stdin is a TTY and we can prompt for input.
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def supports_unicode() -> bool:
    """Check if the console supports Unicode characters.

    Returns:
        True if Unicode spinners/characters should render correctly.
    """
    # On Windows, check for modern terminal (Windows Terminal, ConEmu, etc.)
    if sys.platform == "win32":
        # Windows Terminal sets WT_SESSION
        if os.environ.get("WT_SESSION"):
            return True
        # ConEmu sets ConEmuANSI
        if os.environ.get("ConEmuANSI"):
            return True
        # VS Code terminal
        if os.environ.get("TERM_PROGRAM") == "vscode":
            return True
        # Check for UTF-8 code page (65001) or modern consoles
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # Get console output code page
            code_page = kernel32.GetConsoleOutputCP()
            if code_page == 65001:  # UTF-8
                return True
        except (AttributeError, OSError):
            pass
        # Default to ASCII for legacy Windows cmd.exe
        return False

    # On Unix-like systems, check encoding
    encoding = sys.stdout.encoding or ""
    return encoding.lower() in ("utf-8", "utf8")


# Try to import Rich for formatted output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.prompt import Prompt
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from visual_explainer.config import (  # noqa: E402
    GenerationConfig,
    InternalConfig,
)

if TYPE_CHECKING:
    from visual_explainer.models import (
        ConceptAnalysis,
        EvaluationResult,
        ImagePrompt,
        ImageResult,
    )

# Version
__version__ = "0.1.0"

# Console instance for Rich output
_console: Console | None = None


def get_console() -> Console:
    """Get or create the Rich console instance.

    Configures the console appropriately for:
    - Interactive vs non-interactive mode
    - Windows vs Unix platforms
    - Unicode vs ASCII-only terminals
    """
    global _console
    if _console is None:
        if RICH_AVAILABLE:
            # Determine terminal capabilities
            interactive = is_interactive()
            unicode_support = supports_unicode()

            if sys.platform == "win32":
                # Windows: use legacy_windows=False for modern terminals,
                # but don't force_terminal when not interactive
                _console = Console(
                    force_terminal=interactive,
                    legacy_windows=not unicode_support,
                )
            else:
                # Unix: configure based on interactivity
                _console = Console(
                    force_terminal=interactive,
                )
        else:
            raise RuntimeError("Rich library not available. Install with: pip install rich")
    return _console


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
    parser.add_argument(
        "--concurrency",
        type=_bounded_int(1, 10, "concurrency"),
        default=3,
        help="Max concurrent image generations (default: 3, range: 1-10)",
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


def display_welcome() -> None:
    """Display the welcome header."""
    console = get_console()
    console.print()
    console.print(
        Panel(
            "[bold cyan]Visual Concept Explainer[/bold cyan]\n"
            "[dim]Transform text into AI-generated visual explanations[/dim]",
            border_style="cyan",
        )
    )
    console.print()


def display_analysis_summary(analysis: ConceptAnalysis, infographic_mode: bool = False) -> None:
    """Display a summary of the concept analysis.

    Args:
        analysis: The ConceptAnalysis result.
        infographic_mode: Whether infographic mode is active.
    """
    console = get_console()

    # Create summary panel
    summary_text = f"""[bold white]Document:[/bold white] {analysis.title}
[bold white]Word Count:[/bold white] {analysis.word_count:,} words
[bold white]Key Concepts:[/bold white] {len(analysis.concepts)} concepts identified
[bold white]Target Audience:[/bold white] {analysis.target_audience}
[bold white]Recommended Images:[/bold white] {analysis.recommended_image_count}"""

    # Add page recommendation info if in infographic mode
    if infographic_mode and analysis.page_recommendation:
        page_rec = analysis.page_recommendation
        summary_text += (
            f"\n[bold white]Infographic Pages:[/bold white] {page_rec.page_count} pages recommended"
        )
        if analysis.content_types_detected:
            types_str = ", ".join(ct.value for ct in analysis.content_types_detected[:5])
            summary_text += f"\n[bold white]Content Types:[/bold white] {types_str}"

    console.print(Panel(summary_text, title="[bold]Concept Analysis[/bold]", border_style="green"))

    # Display page plan if infographic mode
    if infographic_mode and analysis.page_recommendation:
        page_rec = analysis.page_recommendation
        console.print("\n[bold white]Infographic Page Plan:[/bold white]")
        for page in page_rec.pages:
            concepts_str = ", ".join(str(c) for c in page.concepts_covered)
            console.print(f"  [cyan]Page {page.page_number}:[/cyan] {page.title}")
            console.print(f"    [dim]Type: {page.page_type.value}[/dim]")
            console.print(
                f"    [dim]Focus: {page.content_focus[:60]}...[/dim]"
                if len(page.content_focus) > 60
                else f"    [dim]Focus: {page.content_focus}[/dim]"
            )
            console.print(f"    [dim]Concepts: [{concepts_str}][/dim]")

        if page_rec.compression_warnings:
            console.print("\n[yellow]Compression Warnings:[/yellow]")
            for warning in page_rec.compression_warnings:
                console.print(f"  [yellow]![/yellow] {warning}")
    else:
        # Display concept flow (original behavior)
        if analysis.concepts:
            console.print("\n[bold white]Concept Flow:[/bold white]")
            for i, concept in enumerate(analysis.concepts, 1):
                console.print(f"  [cyan]{i}.[/cyan] {concept.name}")
                if i < len(analysis.concepts) and analysis.logical_flow:
                    # Find flow connection
                    for flow in analysis.logical_flow:
                        if flow.from_concept == concept.id:
                            console.print(f"     [dim]   +-[{flow.relationship.value}]-->[/dim]")
                            break

    console.print()


def prompt_for_style() -> str | None:
    """Prompt user to select a style.

    Returns:
        Style name/path or None for default.
        Returns "professional-clean" when running non-interactively.
    """
    # Non-interactive mode: return default without prompting
    if not is_interactive():
        return "professional-clean"

    console = get_console()

    console.print("[bold white]Visual Style:[/bold white] What style would you prefer?")
    console.print(
        "  [cyan]1.[/cyan] Professional Clean (Recommended) - Clean, corporate-ready with warm accents"
    )
    console.print(
        "  [cyan]2.[/cyan] Professional Sketch - Hand-drawn sketch aesthetic, creative feel"
    )
    console.print("  [cyan]3.[/cyan] Custom - Provide path to your own style JSON")
    console.print("  [cyan]4.[/cyan] Skip (use Professional Clean default)")
    console.print()

    choice = Prompt.ask("Select style", choices=["1", "2", "3", "4"], default="4")

    if choice == "1":
        return "professional-clean"
    elif choice == "2":
        return "professional-sketch"
    elif choice == "3":
        path = Prompt.ask("Enter path to custom style JSON")
        return path.strip()
    else:
        return None  # Will use default


def prompt_for_image_count(recommended: int) -> int:
    """Prompt user to confirm or adjust image count.

    Args:
        recommended: Recommended image count from analysis.

    Returns:
        Confirmed image count.
        Returns recommended count when running non-interactively.
    """
    # Non-interactive mode: return recommended without prompting
    if not is_interactive():
        return recommended

    console = get_console()

    console.print("[bold white]Image Count:[/bold white] Would you like to:")
    console.print(f"  [cyan]1.[/cyan] Proceed with {recommended} images (Recommended)")
    console.print("  [cyan]2.[/cyan] Use fewer images (condense concepts)")
    console.print("  [cyan]3.[/cyan] Use more images (expand detail)")
    console.print()

    choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")

    if choice == "1":
        return recommended
    elif choice == "2":
        count = Prompt.ask("How many images?", default=str(max(1, recommended - 1)))
        return max(1, int(count))
    else:
        count = Prompt.ask("How many images?", default=str(recommended + 1))
        return min(20, int(count))


def prompt_for_input() -> str:
    """Prompt user for input in interactive mode.

    Returns:
        Input text, file path, or URL.

    Raises:
        RuntimeError: If called in non-interactive mode (use --input flag instead).
    """
    # Non-interactive mode: cannot prompt for input
    if not is_interactive():
        raise RuntimeError(
            "Cannot prompt for input in non-interactive mode. "
            "Use --input or -i flag to provide input."
        )

    console = get_console()

    console.print("[bold white]Please provide your input in one of these formats:[/bold white]")
    console.print("  [cyan]1.[/cyan] Paste text directly (end with empty line)")
    console.print("  [cyan]2.[/cyan] Provide a file path (e.g., ./docs/concept.md)")
    console.print("  [cyan]3.[/cyan] Provide a URL to fetch content from")
    console.print()

    input_type = Prompt.ask("Input type", choices=["1", "2", "3"], default="2")

    if input_type == "1":
        console.print("[dim]Paste your text below (press Enter twice when done):[/dim]")
        lines = []
        while True:
            line = input()
            if line == "":
                if lines and lines[-1] == "":
                    break
            lines.append(line)
        return "\n".join(lines[:-1]) if lines else ""
    elif input_type == "2":
        return Prompt.ask("File path")
    else:
        return Prompt.ask("URL")


def display_dry_run_plan(
    analysis: ConceptAnalysis,
    prompts: list[ImagePrompt],
    config: GenerationConfig,
    style_name: str,
) -> None:
    """Display the generation plan for dry run mode.

    Args:
        analysis: The concept analysis.
        prompts: Generated image prompts.
        config: Generation configuration.
        style_name: Name of the selected style.
    """
    console = get_console()

    console.print(
        Panel(
            "[bold yellow]DRY RUN MODE[/bold yellow]\n"
            "[dim]No images will be generated. Review the plan below.[/dim]",
            border_style="yellow",
        )
    )

    # Configuration table
    config_table = Table(title="Configuration", show_header=False)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value")

    config_table.add_row(
        "Input",
        str(config.input_source)[:60] + "..."
        if len(config.input_source) > 60
        else config.input_source,
    )
    config_table.add_row("Style", style_name)
    config_table.add_row("Aspect Ratio", config.aspect_ratio.value)
    config_table.add_row("Resolution", config.resolution.value)
    config_table.add_row("Max Iterations", str(config.max_iterations))
    config_table.add_row("Pass Threshold", f"{config.pass_threshold:.0%}")
    config_table.add_row("Output Directory", str(config.output_dir))

    console.print(config_table)
    console.print()

    # Images table
    images_table = Table(title=f"Planned Images ({len(prompts)} total)")
    images_table.add_column("#", style="cyan", width=3)
    images_table.add_column("Title", width=30)
    images_table.add_column("Concepts", width=15)
    images_table.add_column("Visual Intent", width=40)

    for prompt in prompts:
        concepts_str = ", ".join(str(c) for c in prompt.concepts_covered)
        intent_preview = (
            prompt.visual_intent[:40] + "..."
            if len(prompt.visual_intent) > 40
            else prompt.visual_intent
        )
        images_table.add_row(
            str(prompt.image_number),
            prompt.title,
            concepts_str,
            intent_preview,
        )

    console.print(images_table)
    console.print()

    # Cost estimate
    estimated_cost = estimate_cost(len(prompts), config.max_iterations)
    console.print(f"[bold white]Estimated Cost:[/bold white] {estimated_cost}")
    console.print("[dim]Actual cost depends on refinement attempts needed.[/dim]")
    console.print()


def estimate_cost(image_count: int, max_iterations: int) -> str:
    """Estimate generation cost.

    Args:
        image_count: Number of images to generate.
        max_iterations: Maximum iterations per image.

    Returns:
        Formatted cost estimate string.
    """
    # Average attempts per image (typically 2-3)
    avg_attempts = min(2.5, max_iterations)

    # Gemini: ~$0.10 per image
    gemini_cost = image_count * avg_attempts * 0.10

    # Claude: ~$0.02 for concept analysis + ~$0.03 per evaluation
    claude_analysis = 0.02
    claude_eval = image_count * avg_attempts * 0.03

    total = gemini_cost + claude_analysis + claude_eval

    return f"${total:.2f} (range: ${total * 0.5:.2f} - ${total * 2:.2f})"


class GenerationProgress:
    """Track and display generation progress using Rich."""

    # ASCII spinner characters for terminals without Unicode support
    ASCII_SPINNER = "-\\|/"

    def __init__(self, total_images: int, max_iterations: int, quiet: bool = False):
        """Initialize progress tracker.

        Args:
            total_images: Total number of images to generate.
            max_iterations: Maximum iterations per image.
            quiet: If True, suppress detailed progress output.
        """
        self.total_images = total_images
        self.max_iterations = max_iterations
        self.quiet = quiet
        self.console = get_console() if RICH_AVAILABLE else None
        self.progress: Progress | None = None
        self.current_image = 0
        self.current_attempt = 0
        self.task_id: TaskID | None = None
        self._use_unicode = supports_unicode()

    def __enter__(self) -> GenerationProgress:
        """Enter context manager."""
        if not self.quiet and RICH_AVAILABLE:
            # Use ASCII spinner on terminals without Unicode support
            if self._use_unicode:
                spinner_column = SpinnerColumn()
            else:
                spinner_column = SpinnerColumn(spinner_name="line")

            self.progress = Progress(
                spinner_column,
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
            )
            self.progress.__enter__()
            self.task_id = self.progress.add_task(
                "Generating images...",
                total=self.total_images,
            )
        return self

    def __exit__(self, *args) -> None:
        """Exit context manager."""
        if self.progress:
            self.progress.__exit__(*args)

    def start_image(self, image_number: int, title: str) -> None:
        """Mark start of a new image.

        Args:
            image_number: Image number (1-indexed).
            title: Image title.
        """
        self.current_image = image_number
        self.current_attempt = 0

        if self.quiet:
            return

        if self.console:
            self.console.print()
            self.console.rule(f"[bold]Image {image_number} of {self.total_images}: {title}[/bold]")

    def start_attempt(self, attempt: int) -> None:
        """Mark start of a generation attempt.

        Args:
            attempt: Attempt number (1-indexed).
        """
        self.current_attempt = attempt

        if self.quiet:
            return

        if self.console:
            self.console.print(f"\n[cyan]Attempt {attempt}/{self.max_iterations}:[/cyan]")

    def update_status(self, status: str) -> None:
        """Update the current status message.

        Args:
            status: Status message to display.
        """
        if self.quiet:
            return

        if self.progress and self.task_id is not None:
            self.progress.update(
                self.task_id,
                description=f"Image {self.current_image}/{self.total_images}: {status}",
            )
        elif self.console:
            self.console.print(f"  [dim]{status}[/dim]")

    def show_evaluation(self, result: EvaluationResult) -> None:
        """Display evaluation results.

        Args:
            result: The evaluation result.
        """
        if self.quiet:
            return

        if self.console:
            # Color based on verdict
            verdict_colors = {
                "PASS": "green",
                "NEEDS_REFINEMENT": "yellow",
                "FAIL": "red",
            }
            color = verdict_colors.get(result.verdict.value, "white")

            self.console.print("  [dim]Evaluation:[/dim]")
            self.console.print(
                f"    - Concept clarity: {result.criteria_scores.concept_clarity:.0%}"
            )
            self.console.print(f"    - Visual appeal: {result.criteria_scores.visual_appeal:.0%}")
            self.console.print(
                f"    - Audience fit: {result.criteria_scores.audience_appropriateness:.0%}"
            )
            self.console.print(f"    - Flow: {result.criteria_scores.flow_continuity:.0%}")
            self.console.print(
                f"  [bold]Overall: {result.overall_score:.0%} — [{color}]{result.verdict.value}[/{color}][/bold]"
            )

    def complete_image(self, image_number: int, best_attempt: int, score: float) -> None:
        """Mark image as complete.

        Args:
            image_number: Image number (1-indexed).
            best_attempt: Which attempt was selected as best.
            score: Final score.
        """
        if self.progress and self.task_id is not None:
            self.progress.advance(self.task_id)

        if not self.quiet and self.console:
            self.console.print(
                f"\n[green]Image {image_number} complete.[/green] Best version: Attempt {best_attempt} ({score:.0%})"
            )


def display_completion_summary(
    image_results: list[ImageResult],
    output_dir: Path,
    total_duration: float,
    total_api_calls: int,
) -> None:
    """Display the completion summary.

    Args:
        image_results: List of image generation results.
        output_dir: Output directory path.
        total_duration: Total generation duration in seconds.
        total_api_calls: Total API calls made.
    """
    console = get_console()

    console.print()
    console.rule("[bold]Generation Complete[/bold]")
    console.print()

    # Calculate statistics
    successful = [r for r in image_results if r.status == "complete"]
    failed = [r for r in image_results if r.status == "failed"]
    total_attempts = sum(r.total_attempts for r in image_results)
    avg_score = sum(r.final_score or 0 for r in successful) / len(successful) if successful else 0

    # Results table
    results_table = Table(show_header=False)
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Value")

    results_table.add_row("Images generated", f"{len(successful)} of {len(image_results)}")
    results_table.add_row("Total attempts", str(total_attempts))
    results_table.add_row("Average quality score", f"{avg_score:.0%}")
    results_table.add_row("Total duration", f"{total_duration:.1f}s")
    results_table.add_row("API calls", str(total_api_calls))
    results_table.add_row(
        "Estimated cost",
        estimate_cost(len(image_results), total_attempts // max(len(image_results), 1)),
    )

    console.print(results_table)
    console.print()

    # Output location
    console.print("[bold white]Output saved to:[/bold white]")
    console.print(f"  {output_dir}")
    console.print()

    # Final images list
    if successful:
        console.print("[bold white]Final images:[/bold white]")
        for result in successful:
            score_pct = f"{(result.final_score or 0):.0%}"
            console.print(
                f"  [cyan]{result.image_number}.[/cyan] {result.title} (Score: {score_pct})"
            )

    if failed:
        console.print()
        console.print("[bold red]Failed images:[/bold red]")
        for result in failed:
            console.print(f"  [red]{result.image_number}.[/red] {result.title}")


async def _analyze_concepts(
    config: GenerationConfig,
    internal_config: InternalConfig,
    style_name: str,
    console: Console | None,
    infographic_mode: bool,
) -> tuple[ConceptAnalysis, object, str, int]:
    """Load style and analyze document concepts.

    Handles style loading and concept analysis (Steps 1-2 of the pipeline).

    Args:
        config: Generation configuration.
        internal_config: Internal configuration.
        style_name: Style name to use.
        console: Rich console for output, or None if suppressed.
        infographic_mode: If True, analyze for infographic pages.

    Returns:
        Tuple of (analysis, style, style_display_name, api_calls).
    """
    from visual_explainer.concept_analyzer import analyze_document
    from visual_explainer.style_loader import load_style

    api_calls = 0

    # Load style
    if console:
        console.print("[dim]Loading style configuration...[/dim]")

    style = load_style(style_name)
    style_display_name = style.style_name if style else style_name

    # Analyze concepts
    if console:
        mode_text = "infographic pages" if infographic_mode else "concepts"
        console.print(f"[dim]Analyzing document {mode_text}...[/dim]")

    analysis = await analyze_document(
        config.input_source,
        config,
        internal_config,
        infographic_mode=infographic_mode,
    )
    api_calls += 1  # Claude analysis call

    # Display analysis summary
    if console:
        display_analysis_summary(analysis, infographic_mode=infographic_mode)

    return analysis, style, style_display_name, api_calls


def _generate_prompts(
    config: GenerationConfig,
    internal_config: InternalConfig,
    analysis: ConceptAnalysis,
    style: object,
    console: Console | None,
    infographic_mode: bool,
) -> tuple[list[ImagePrompt], object, int]:
    """Generate image prompts from the concept analysis.

    Handles prompt generation and count adjustment (Steps 3-4 of the pipeline).

    Args:
        config: Generation configuration.
        internal_config: Internal configuration.
        analysis: Concept analysis result.
        style: Loaded style configuration.
        console: Rich console for output, or None if suppressed.
        infographic_mode: If True, generate infographic-style prompts.

    Returns:
        Tuple of (prompts, prompt_generator, api_calls).
    """
    from visual_explainer.prompt_generator import PromptGenerator

    api_calls = 0

    # Confirm image count
    image_count = config.image_count if config.image_count > 0 else analysis.recommended_image_count

    # Generate prompts
    if console:
        prompt_type = "infographic page" if infographic_mode else "image"
        console.print(f"[dim]Generating {prompt_type} prompts...[/dim]")

    prompt_generator = PromptGenerator(internal_config=internal_config)

    if infographic_mode and analysis.page_recommendation:
        # Use infographic-style prompt generation
        prompts = prompt_generator.generate_infographic_prompts(analysis, style, config)
        # Each page plan generates one prompt, so we count API calls per page
        api_calls += len(analysis.page_recommendation.pages)
    else:
        # Use standard prompt generation
        prompts = prompt_generator.generate_prompts(analysis, style, config)
        api_calls += 1  # Claude prompt generation call

        # Adjust prompt count if needed
        if len(prompts) > image_count:
            prompts = prompts[:image_count]

    return prompts, prompt_generator, api_calls


async def _evaluate_and_refine(
    gen_result: object,
    current_prompt: ImagePrompt,
    prompt: ImagePrompt,
    attempt: int,
    image_dir: Path,
    image_evaluator: object,
    analysis: ConceptAnalysis,
    total_prompts: int,
    style_display_name: str,
    result: ImageResult,
    progress: GenerationProgress,
    prompt_generator: object,
    style: object,
    config: GenerationConfig,
) -> tuple[object | None, ImagePrompt, int]:
    """Evaluate a generated image and optionally refine the prompt.

    Handles image saving, evaluation, attempt tracking, and prompt refinement
    for a single generation attempt.

    Args:
        gen_result: The generation result from the image generator.
        current_prompt: The current image prompt being used.
        prompt: The original prompt (for metadata like image_number).
        attempt: Current attempt number (1-indexed).
        image_dir: Directory for this image's files.
        image_evaluator: The image evaluator instance.
        analysis: Concept analysis (for audience context).
        total_prompts: Total number of prompts being generated.
        style_display_name: Display name of the style.
        result: The ImageResult tracker for this image.
        progress: The progress display manager.
        prompt_generator: The prompt generator for refinements.
        style: The style configuration.
        config: Generation configuration.

    Returns:
        Tuple of (eval_result_or_None, possibly_refined_prompt, api_calls).
    """
    from visual_explainer.models import EvaluationVerdict

    api_calls = 0

    # Save image
    image_file = image_dir / f"attempt-{attempt:02d}.jpg"
    image_file.write_bytes(gen_result.image_data)

    # Evaluate image
    progress.update_status("Evaluating...")
    eval_result = image_evaluator.evaluate_image(
        image_bytes=gen_result.image_data,
        intent=current_prompt.visual_intent,
        criteria=current_prompt.success_criteria,
        context={
            "audience": analysis.target_audience,
            "image_number": prompt.image_number,
            "total_images": total_prompts,
            "style": style_display_name,
        },
        image_id=prompt.image_number,
        iteration=attempt,
    )
    api_calls += 1

    # Save evaluation
    eval_file = image_dir / f"evaluation-{attempt:02d}.json"
    eval_file.write_text(
        json.dumps(eval_result.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    # Track attempt
    result.add_attempt(
        image_path=str(image_file),
        prompt_version=attempt,
        evaluation=eval_result,
        duration_seconds=gen_result.duration_seconds,
    )

    # Display evaluation
    progress.show_evaluation(eval_result)

    # Refine prompt for next attempt if needed
    if eval_result.verdict != EvaluationVerdict.PASS and attempt < config.max_iterations:
        progress.update_status("Refining prompt...")
        current_prompt = prompt_generator.refine_prompt(
            original=current_prompt,
            feedback=eval_result,
            attempt=attempt + 1,
            style=style,
            config=config,
        )
        api_calls += 1

    return eval_result, current_prompt, api_calls


async def _execute_generation_loop(
    prompts: list[ImagePrompt],
    config: GenerationConfig,
    internal_config: InternalConfig,
    analysis: ConceptAnalysis,
    style: object,
    style_display_name: str,
    prompt_generator: object,
    output_dir: Path,
    quiet: bool = False,
    json_output: bool = False,
) -> tuple[list[ImageResult], int]:
    """Execute the image generation loop with evaluation and refinement.

    Initializes the image generator and evaluator, then iterates over each
    prompt, generating images with up to max_iterations refinement attempts
    per image (Steps 6-8 of the pipeline).

    Args:
        prompts: List of image prompts to generate.
        config: Generation configuration.
        internal_config: Internal configuration.
        analysis: Concept analysis result.
        style: Loaded style configuration.
        style_display_name: Display name of the style.
        prompt_generator: Prompt generator for refinements.
        output_dir: Output directory for generated files.
        quiet: If True, suppress progress output.
        json_output: If True, suppress progress output.

    Returns:
        Tuple of (image_results, api_calls).
    """
    import shutil

    from visual_explainer.image_evaluator import ImageEvaluator
    from visual_explainer.image_generator import GeminiImageGenerator, GenerationStatus
    from visual_explainer.models import EvaluationVerdict, ImageResult

    api_calls = 0

    image_generator = GeminiImageGenerator(
        internal_config=internal_config,
        max_concurrent=config.concurrency,
    )
    image_evaluator = ImageEvaluator(pass_threshold=config.pass_threshold)

    image_results: list[ImageResult] = []

    with GenerationProgress(len(prompts), config.max_iterations, quiet or json_output) as progress:
        for prompt in prompts:
            progress.start_image(prompt.image_number, prompt.title)

            # Create image result tracker
            result = ImageResult(
                image_number=prompt.image_number,
                title=prompt.title,
            )
            result.status = "generating"

            # Image directory
            image_dir = output_dir / f"image-{prompt.image_number:02d}"
            image_dir.mkdir(exist_ok=True)

            current_prompt = prompt
            best_score = 0.0
            best_attempt = 0
            best_image_path: str | None = None

            for attempt in range(1, config.max_iterations + 1):
                progress.start_attempt(attempt)

                # Save prompt
                prompt_file = image_dir / f"prompt-v{attempt}.txt"
                prompt_file.write_text(current_prompt.prompt.main_prompt, encoding="utf-8")

                # Generate image
                progress.update_status("Generating...")
                gen_result = await image_generator.generate_image(
                    prompt=current_prompt.get_full_prompt(),
                    aspect_ratio=config.aspect_ratio,
                    resolution=config.resolution,
                    negative_prompt=current_prompt.prompt.avoid,
                    image_number=prompt.image_number,
                )
                api_calls += 1

                if gen_result.status != GenerationStatus.SUCCESS or gen_result.image_data is None:
                    progress.update_status(f"Generation failed: {gen_result.error_message}")
                    continue

                # Evaluate and optionally refine
                eval_result, current_prompt, eval_api_calls = await _evaluate_and_refine(
                    gen_result=gen_result,
                    current_prompt=current_prompt,
                    prompt=prompt,
                    attempt=attempt,
                    image_dir=image_dir,
                    image_evaluator=image_evaluator,
                    analysis=analysis,
                    total_prompts=len(prompts),
                    style_display_name=style_display_name,
                    result=result,
                    progress=progress,
                    prompt_generator=prompt_generator,
                    style=style,
                    config=config,
                )
                api_calls += eval_api_calls

                # Track best
                image_file = image_dir / f"attempt-{attempt:02d}.jpg"
                if eval_result.overall_score > best_score:
                    best_score = eval_result.overall_score
                    best_attempt = attempt
                    best_image_path = str(image_file)

                # Check verdict
                if eval_result.verdict == EvaluationVerdict.PASS:
                    break

            # Finalize image result
            if best_image_path:
                result.final_attempt = best_attempt
                result.final_score = best_score
                result.final_path = best_image_path
                result.status = "complete"

                # Create final.jpg copy/link
                final_path = image_dir / "final.jpg"
                shutil.copy2(best_image_path, final_path)

                progress.complete_image(prompt.image_number, best_attempt, best_score)
            else:
                result.status = "failed"

            image_results.append(result)

    return image_results, api_calls


def _save_outputs(
    image_results: list[ImageResult],
    prompts: list[ImagePrompt],
    output_dir: Path,
    config: GenerationConfig,
    analysis: ConceptAnalysis,
    style_display_name: str,
    timestamp: str,
    topic_slug: str,
    total_api_calls: int,
) -> None:
    """Save all output files: all-images directory, metadata, concepts, and summary.

    Creates the consolidated output structure (Steps 9-10 of the pipeline).

    Args:
        image_results: List of generation results per image.
        prompts: List of image prompts that were generated.
        output_dir: Output directory path.
        config: Generation configuration.
        analysis: Concept analysis result.
        style_display_name: Display name of the style.
        timestamp: Generation timestamp string.
        topic_slug: Sanitized topic slug for IDs.
        total_api_calls: Total API calls made during generation.
    """
    import shutil

    # Create all-images directory with final images
    all_images_dir = output_dir / "all-images"
    all_images_dir.mkdir(exist_ok=True)

    for result in image_results:
        if result.status == "complete" and result.final_path:
            src = Path(result.final_path)
            dst = (
                all_images_dir
                / f"{result.image_number:02d}-{result.title.lower().replace(' ', '-')[:30]}.jpg"
            )
            shutil.copy2(src, dst)

    # Save metadata
    metadata = {
        "generation_id": f"{timestamp}-{topic_slug}",
        "timestamp": datetime.now().isoformat(),
        "input": {
            "type": "file" if Path(config.input_source).exists() else "text",
            "word_count": analysis.word_count,
            "content_hash": analysis.content_hash,
        },
        "config": config.to_metadata_dict(),
        "results": {
            "images_planned": len(prompts),
            "images_generated": len([r for r in image_results if r.status == "complete"]),
            "total_attempts": sum(r.total_attempts for r in image_results),
            "total_api_calls": total_api_calls,
        },
        "images": [
            {
                "image_number": r.image_number,
                "title": r.title,
                "final_attempt": r.final_attempt,
                "total_attempts": r.total_attempts,
                "final_score": r.final_score,
                "final_path": r.final_path,
                "status": r.status,
            }
            for r in image_results
        ],
    }

    metadata_file = output_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Save concepts
    concepts_file = output_dir / "concepts.json"
    concepts_file.write_text(
        json.dumps(analysis.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    # Generate summary.md
    successful = [r for r in image_results if r.status == "complete"]
    avg_score = sum(r.final_score or 0 for r in successful) / max(1, len(successful))

    summary_lines = [
        "# Visual Explainer Results",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Document:** {analysis.title}",
        f"**Style:** {style_display_name}",
        "",
        "## Summary",
        "",
        f"- Images generated: {len(successful)} of {len(prompts)}",
        f"- Total attempts: {sum(r.total_attempts for r in image_results)}",
        f"- Average score: {avg_score:.0%}",
        "",
        "## Images",
        "",
    ]

    for result in image_results:
        status_icon = "check" if result.status == "complete" else "x"
        score_str = f"{(result.final_score or 0):.0%}" if result.final_score else "N/A"
        summary_lines.append(
            f"- [{status_icon}] **{result.image_number}. {result.title}** - Score: {score_str}"
        )

    summary_file = output_dir / "summary.md"
    summary_file.write_text("\n".join(summary_lines), encoding="utf-8")


async def run_generation_pipeline(
    config: GenerationConfig,
    internal_config: InternalConfig,
    style_name: str,
    quiet: bool = False,
    json_output: bool = False,
    infographic_mode: bool = False,
) -> dict:
    """Run the full generation pipeline.

    Orchestrates the end-to-end image generation workflow by delegating to
    focused helper functions for each phase: concept analysis, prompt
    generation, image generation with refinement, and output saving.

    Args:
        config: Generation configuration.
        internal_config: Internal configuration.
        style_name: Style name to use.
        quiet: Suppress progress output.
        json_output: Return JSON-compatible dict.
        infographic_mode: If True, generate information-dense infographics.

    Returns:
        Dictionary with generation results.
    """
    import time

    start_time = time.time()
    console = get_console() if not quiet and not json_output else None
    suppress_output = quiet or json_output

    # Phase 1: Analyze concepts and load style
    analysis, style, style_display_name, total_api_calls = await _analyze_concepts(
        config, internal_config, style_name, console, infographic_mode
    )

    # Phase 2: Generate prompts
    prompts, prompt_generator, api_calls = _generate_prompts(
        config, internal_config, analysis, style, console, infographic_mode
    )
    total_api_calls += api_calls

    # Early exit for dry run
    if config.dry_run:
        display_dry_run_plan(analysis, prompts, config, style_display_name)
        return {
            "status": "dry_run",
            "image_count": len(prompts),
            "prompts": [p.model_dump(mode="json") for p in prompts],
        }

    # Phase 3: Create output directory and execute generation loop
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    sanitized_title = re.sub(r'[<>:"/\\|?*]', "", analysis.title)
    topic_slug = sanitized_title.lower().replace(" ", "-")[:30]
    output_dir = config.output_dir / f"visual-explainer-{topic_slug}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    image_results, api_calls = await _execute_generation_loop(
        prompts,
        config,
        internal_config,
        analysis,
        style,
        style_display_name,
        prompt_generator,
        output_dir,
        quiet,
        json_output,
    )
    total_api_calls += api_calls

    # Phase 4: Save outputs and display summary
    _save_outputs(
        image_results,
        prompts,
        output_dir,
        config,
        analysis,
        style_display_name,
        timestamp,
        topic_slug,
        total_api_calls,
    )
    total_duration = time.time() - start_time
    if not suppress_output:
        display_completion_summary(image_results, output_dir, total_duration, total_api_calls)

    return {
        "status": "complete",
        "output_dir": str(output_dir),
        "images_generated": len([r for r in image_results if r.status == "complete"]),
        "total_images": len(prompts),
        "total_attempts": sum(r.total_attempts for r in image_results),
        "total_duration_seconds": total_duration,
        "total_api_calls": total_api_calls,
        "image_results": [r.model_dump(mode="json") for r in image_results],
    }


async def load_checkpoint_and_resume(
    checkpoint_path: Path,
    config: GenerationConfig,
    quiet: bool = False,
    json_output: bool = False,
) -> dict:
    """Load checkpoint and resume generation from where it left off.

    Reads the checkpoint JSON, determines which images have already been
    completed, and resumes the generation pipeline for any remaining images.
    If all images are already complete, displays a summary and returns.

    Args:
        checkpoint_path: Path to checkpoint.json file.
        config: Generation configuration (may override checkpoint settings).
        quiet: Suppress progress output.
        json_output: Return JSON-compatible dict.

    Returns:
        Dictionary with generation results including both previously
        completed and newly generated images.
    """
    import time

    from visual_explainer.output import CheckpointState

    console = get_console() if not quiet and not json_output else None

    # --- Validate checkpoint file exists ---
    if not checkpoint_path.exists():
        error_msg = f"Checkpoint file not found: {checkpoint_path}"
        if console:
            console.print(f"[red]{error_msg}[/red]")
        return {"status": "error", "error": error_msg}

    if console:
        console.print(f"[dim]Loading checkpoint: {checkpoint_path}[/dim]")

    # --- Load and parse checkpoint ---
    try:
        checkpoint_data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        checkpoint_state = CheckpointState.from_dict(checkpoint_data)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        error_msg = f"Invalid checkpoint file: {e}"
        if console:
            console.print(f"[red]{error_msg}[/red]")
        return {"status": "error", "error": error_msg}

    # --- Determine session directory from checkpoint path ---
    session_dir = checkpoint_path.parent

    # --- Display checkpoint summary ---
    completed_count = len(checkpoint_state.completed_images)
    remaining_count = checkpoint_state.total_images - completed_count

    if console:
        console.print()
        console.print(
            Panel(
                f"[bold cyan]Resuming Generation[/bold cyan]\n"
                f"[dim]Session: {checkpoint_data.get('session_name', 'unknown')}[/dim]",
                border_style="cyan",
            )
        )
        console.print(f"  Generation ID: {checkpoint_state.generation_id}")
        console.print(f"  Total images: {checkpoint_state.total_images}")
        console.print(f"  Completed: {completed_count}")
        console.print(f"  Remaining: {remaining_count}")
        console.print()

    # --- If all images are already complete, just return summary ---
    if remaining_count == 0 or checkpoint_state.status == "completed":
        if console:
            console.print(
                "[green]All images already completed.[/green] No further generation needed."
            )

        # Build results from checkpoint data
        image_results_data = []
        for _img_num_str, result_data in checkpoint_state.image_results.items():
            image_results_data.append(result_data)

        return {
            "status": "complete",
            "output_dir": str(session_dir),
            "images_generated": completed_count,
            "total_images": checkpoint_state.total_images,
            "total_attempts": sum(
                r.get("total_attempts", r.get("final_attempt", 1))
                for r in checkpoint_state.image_results.values()
            ),
            "resumed": True,
            "images_already_complete": completed_count,
            "images_newly_generated": 0,
            "image_results": image_results_data,
        }

    # --- Resume generation for remaining images ---
    start_time = time.time()

    # Load internal config and reconstruct pipeline inputs
    internal_config = InternalConfig.from_env()

    # Determine style from checkpoint config or CLI override
    style_name = config.style or checkpoint_state.config.get("style", "professional-clean")

    # Re-run concept analysis and prompt generation to get prompt objects
    if console:
        console.print("[dim]Restoring pipeline state...[/dim]")

    analysis, style, style_display_name, total_api_calls = await _analyze_concepts(
        config, internal_config, style_name, console, infographic_mode=False
    )

    prompts, prompt_generator, api_calls = _generate_prompts(
        config, internal_config, analysis, style, console, infographic_mode=False
    )
    total_api_calls += api_calls

    # Filter to only remaining (incomplete) prompts
    remaining_prompts = [
        p for p in prompts if p.image_number not in checkpoint_state.completed_images
    ]

    if console:
        console.print(
            f"[dim]Resuming generation for {len(remaining_prompts)} remaining image(s)...[/dim]"
        )

    # Execute generation loop for remaining images only
    new_results, gen_api_calls = await _execute_generation_loop(
        remaining_prompts,
        config,
        internal_config,
        analysis,
        style,
        style_display_name,
        prompt_generator,
        session_dir,
        quiet,
        json_output,
    )
    total_api_calls += gen_api_calls

    # --- Merge previously completed results with new results ---
    from visual_explainer.models import ImageResult as ImageResultModel

    all_results: list[ImageResultModel] = []

    # Reconstruct ImageResult objects for previously completed images
    for img_num in sorted(checkpoint_state.completed_images):
        img_num_key = str(img_num)
        if img_num_key in checkpoint_state.image_results:
            prev_data = checkpoint_state.image_results[img_num_key]
            prev_result = ImageResultModel(
                image_number=prev_data.get("image_number", img_num),
                title=prev_data.get("title", f"Image {img_num}"),
            )
            prev_result.status = prev_data.get("status", "complete")
            prev_result.final_attempt = prev_data.get("final_attempt")
            prev_result.final_score = prev_data.get("final_score")
            prev_result.final_path = prev_data.get("final_path")
            all_results.append(prev_result)

    # Add newly generated results
    all_results.extend(new_results)

    # Sort by image number for consistent ordering
    all_results.sort(key=lambda r: r.image_number)

    # --- Save updated outputs ---
    timestamp = checkpoint_data.get("started_at", datetime.now().isoformat())
    topic_slug = checkpoint_data.get("topic", "unknown").lower().replace(" ", "-")[:30]

    _save_outputs(
        all_results,
        prompts,
        session_dir,
        config,
        analysis,
        style_display_name,
        timestamp,
        topic_slug,
        total_api_calls,
    )

    total_duration = time.time() - start_time
    suppress_output = quiet or json_output

    if not suppress_output:
        display_completion_summary(all_results, session_dir, total_duration, total_api_calls)

    newly_generated = len([r for r in new_results if r.status == "complete"])

    return {
        "status": "complete",
        "output_dir": str(session_dir),
        "images_generated": len([r for r in all_results if r.status == "complete"]),
        "total_images": checkpoint_state.total_images,
        "total_attempts": sum(r.total_attempts for r in all_results),
        "total_duration_seconds": total_duration,
        "total_api_calls": total_api_calls,
        "resumed": True,
        "images_already_complete": completed_count,
        "images_newly_generated": newly_generated,
        "image_results": [r.model_dump(mode="json") for r in all_results],
    }


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
            concurrency=args.concurrency,
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
        if not is_interactive():
            print("Error: No input provided and not running interactively.")
            print("Use --input or -i flag to provide input.")
            return 1

        if not RICH_AVAILABLE:
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
        if not args.json and is_interactive() and not check_keys_and_prompt_if_missing():
            print("\nCannot proceed without API keys configured.")
            print("Run: visual-explainer --setup-keys")
            return 1
        elif not args.json and not is_interactive():
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
            concurrency=args.concurrency,
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
        and RICH_AVAILABLE
        and is_interactive()
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
            console = get_console() if RICH_AVAILABLE else None
            if console:
                console.print(f"[red]Error: {e}[/red]")
            else:
                print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
