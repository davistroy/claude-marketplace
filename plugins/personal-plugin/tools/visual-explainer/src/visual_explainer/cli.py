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
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

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
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from visual_explainer.config import (
    AspectRatio,
    GenerationConfig,
    InternalConfig,
    Resolution,
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
    """Get or create the Rich console instance."""
    global _console
    if _console is None:
        if RICH_AVAILABLE:
            _console = Console()
        else:
            raise RuntimeError("Rich library not available. Install with: pip install rich")
    return _console


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
        type=int,
        default=5,
        help="Max refinement attempts per image (default: 5, range: 1-10)",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
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
        type=int,
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


def display_analysis_summary(analysis: "ConceptAnalysis") -> None:
    """Display a summary of the concept analysis.

    Args:
        analysis: The ConceptAnalysis result.
    """
    console = get_console()

    # Create summary panel
    summary_text = f"""[bold white]Document:[/bold white] {analysis.title}
[bold white]Word Count:[/bold white] {analysis.word_count:,} words
[bold white]Key Concepts:[/bold white] {len(analysis.concepts)} concepts identified
[bold white]Target Audience:[/bold white] {analysis.target_audience}
[bold white]Recommended Images:[/bold white] {analysis.recommended_image_count}"""

    console.print(Panel(summary_text, title="[bold]Concept Analysis[/bold]", border_style="green"))

    # Display concept flow
    if analysis.concepts:
        console.print("\n[bold white]Concept Flow:[/bold white]")
        for i, concept in enumerate(analysis.concepts, 1):
            console.print(f"  [cyan]{i}.[/cyan] {concept.name}")
            if i < len(analysis.concepts) and analysis.logical_flow:
                # Find flow connection
                for flow in analysis.logical_flow:
                    if flow.from_concept == concept.id:
                        console.print(f"     [dim]   └─[{flow.relationship.value}]──>[/dim]")
                        break

    console.print()


def prompt_for_style() -> str | None:
    """Prompt user to select a style.

    Returns:
        Style name/path or None for default.
    """
    console = get_console()

    console.print("[bold white]Visual Style:[/bold white] What style would you prefer?")
    console.print("  [cyan]1.[/cyan] Professional Clean (Recommended) - Clean, corporate-ready with warm accents")
    console.print("  [cyan]2.[/cyan] Professional Sketch - Hand-drawn sketch aesthetic, creative feel")
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
    """
    console = get_console()

    console.print(f"[bold white]Image Count:[/bold white] Would you like to:")
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
    """
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
    analysis: "ConceptAnalysis",
    prompts: list["ImagePrompt"],
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

    config_table.add_row("Input", str(config.input_source)[:60] + "..." if len(config.input_source) > 60 else config.input_source)
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
        intent_preview = prompt.visual_intent[:40] + "..." if len(prompt.visual_intent) > 40 else prompt.visual_intent
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

    def __enter__(self) -> "GenerationProgress":
        """Enter context manager."""
        if not self.quiet and RICH_AVAILABLE:
            self.progress = Progress(
                SpinnerColumn(),
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

    def show_evaluation(self, result: "EvaluationResult") -> None:
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

            self.console.print(f"  [dim]Evaluation:[/dim]")
            self.console.print(f"    - Concept clarity: {result.criteria_scores.concept_clarity:.0%}")
            self.console.print(f"    - Visual appeal: {result.criteria_scores.visual_appeal:.0%}")
            self.console.print(f"    - Audience fit: {result.criteria_scores.audience_appropriateness:.0%}")
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
    image_results: list["ImageResult"],
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
    results_table.add_row("Estimated cost", estimate_cost(len(image_results), total_attempts // max(len(image_results), 1)))

    console.print(results_table)
    console.print()

    # Output location
    console.print(f"[bold white]Output saved to:[/bold white]")
    console.print(f"  {output_dir}")
    console.print()

    # Final images list
    if successful:
        console.print("[bold white]Final images:[/bold white]")
        for result in successful:
            score_pct = f"{(result.final_score or 0):.0%}"
            console.print(f"  [cyan]{result.image_number}.[/cyan] {result.title} (Score: {score_pct})")

    if failed:
        console.print()
        console.print("[bold red]Failed images:[/bold red]")
        for result in failed:
            console.print(f"  [red]{result.image_number}.[/red] {result.title}")


async def run_generation_pipeline(
    config: GenerationConfig,
    internal_config: InternalConfig,
    style_name: str,
    quiet: bool = False,
    json_output: bool = False,
) -> dict:
    """Run the full generation pipeline.

    Args:
        config: Generation configuration.
        internal_config: Internal configuration.
        style_name: Style name to use.
        quiet: Suppress progress output.
        json_output: Return JSON-compatible dict.

    Returns:
        Dictionary with generation results.
    """
    import time

    from visual_explainer.concept_analyzer import analyze_document
    from visual_explainer.image_evaluator import ImageEvaluator
    from visual_explainer.image_generator import GeminiImageGenerator, GenerationStatus
    from visual_explainer.models import EvaluationVerdict, ImageResult
    from visual_explainer.prompt_generator import PromptGenerator
    from visual_explainer.style_loader import load_style

    console = get_console() if not quiet and not json_output else None
    start_time = time.time()
    total_api_calls = 0

    # Step 1: Load style
    if console:
        console.print("[dim]Loading style configuration...[/dim]")

    style = load_style(style_name)
    style_display_name = style.style_name if style else style_name

    # Step 2: Analyze concepts
    if console:
        console.print("[dim]Analyzing document concepts...[/dim]")

    analysis = await analyze_document(
        config.input_source,
        config,
        internal_config,
    )
    total_api_calls += 1  # Claude analysis call

    # Display analysis summary
    if console:
        display_analysis_summary(analysis)

    # Step 3: Confirm image count (interactive mode)
    image_count = config.image_count if config.image_count > 0 else analysis.recommended_image_count

    # Step 4: Generate prompts
    if console:
        console.print("[dim]Generating image prompts...[/dim]")

    prompt_generator = PromptGenerator(internal_config=internal_config)
    prompts = prompt_generator.generate_prompts(analysis, style, config)
    total_api_calls += 1  # Claude prompt generation call

    # Adjust prompt count if needed
    if len(prompts) > image_count:
        prompts = prompts[:image_count]

    # Step 5: Handle dry run
    if config.dry_run:
        display_dry_run_plan(analysis, prompts, config, style_display_name)
        return {
            "status": "dry_run",
            "image_count": len(prompts),
            "prompts": [p.model_dump(mode="json") for p in prompts],
        }

    # Step 6: Initialize generators
    image_generator = GeminiImageGenerator(
        internal_config=internal_config,
        max_concurrent=config.concurrency,
    )
    image_evaluator = ImageEvaluator(pass_threshold=config.pass_threshold)

    # Step 7: Create output directory
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    topic_slug = analysis.title.lower().replace(" ", "-")[:30]
    output_dir = config.output_dir / f"visual-explainer-{topic_slug}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 8: Generate images with refinement loop
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
                total_api_calls += 1

                if gen_result.status != GenerationStatus.SUCCESS or gen_result.image_data is None:
                    progress.update_status(f"Generation failed: {gen_result.error_message}")
                    continue

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
                        "total_images": len(prompts),
                        "style": style_display_name,
                    },
                    image_id=prompt.image_number,
                    iteration=attempt,
                )
                total_api_calls += 1

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

                # Track best
                if eval_result.overall_score > best_score:
                    best_score = eval_result.overall_score
                    best_attempt = attempt
                    best_image_path = str(image_file)

                # Check verdict
                if eval_result.verdict == EvaluationVerdict.PASS:
                    break

                # Refine prompt for next attempt
                if attempt < config.max_iterations:
                    progress.update_status("Refining prompt...")
                    current_prompt = prompt_generator.refine_prompt(
                        original=current_prompt,
                        feedback=eval_result,
                        attempt=attempt + 1,
                        style=style,
                        config=config,
                    )
                    total_api_calls += 1

            # Finalize image result
            if best_image_path:
                result.final_attempt = best_attempt
                result.final_score = best_score
                result.final_path = best_image_path
                result.status = "complete"

                # Create final.jpg copy/link
                final_path = image_dir / "final.jpg"
                import shutil
                shutil.copy2(best_image_path, final_path)

                progress.complete_image(prompt.image_number, best_attempt, best_score)
            else:
                result.status = "failed"

            image_results.append(result)

    # Step 9: Create all-images directory with final images
    all_images_dir = output_dir / "all-images"
    all_images_dir.mkdir(exist_ok=True)

    for result in image_results:
        if result.status == "complete" and result.final_path:
            src = Path(result.final_path)
            dst = all_images_dir / f"{result.image_number:02d}-{result.title.lower().replace(' ', '-')[:30]}.jpg"
            import shutil
            shutil.copy2(src, dst)

    # Step 10: Save metadata
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
    summary_lines = [
        f"# Visual Explainer Results",
        f"",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Document:** {analysis.title}",
        f"**Style:** {style_display_name}",
        f"",
        f"## Summary",
        f"",
        f"- Images generated: {len([r for r in image_results if r.status == 'complete'])} of {len(prompts)}",
        f"- Total attempts: {sum(r.total_attempts for r in image_results)}",
        f"- Average score: {sum(r.final_score or 0 for r in image_results if r.status == 'complete') / max(1, len([r for r in image_results if r.status == 'complete'])):.0%}",
        f"",
        f"## Images",
        f"",
    ]

    for result in image_results:
        status_icon = "check" if result.status == "complete" else "x"
        score_str = f"{(result.final_score or 0):.0%}" if result.final_score else "N/A"
        summary_lines.append(f"- [{status_icon}] **{result.image_number}. {result.title}** - Score: {score_str}")

    summary_file = output_dir / "summary.md"
    summary_file.write_text("\n".join(summary_lines), encoding="utf-8")

    # Calculate total duration
    total_duration = time.time() - start_time

    # Display completion summary
    if not quiet and not json_output:
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


async def load_checkpoint_and_resume(checkpoint_path: Path, config: GenerationConfig) -> dict:
    """Load checkpoint and resume generation.

    Args:
        checkpoint_path: Path to checkpoint file.
        config: Generation configuration.

    Returns:
        Generation results.
    """
    console = get_console()

    if not checkpoint_path.exists():
        console.print(f"[red]Checkpoint file not found: {checkpoint_path}[/red]")
        return {"status": "error", "error": "Checkpoint file not found"}

    console.print(f"[dim]Loading checkpoint: {checkpoint_path}[/dim]")

    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))

    # TODO: Implement full checkpoint resume logic
    # For now, display what would be resumed
    console.print(f"[yellow]Resume functionality coming soon.[/yellow]")
    console.print(f"Checkpoint contains:")
    console.print(f"  - Generation ID: {checkpoint.get('generation_id', 'unknown')}")
    console.print(f"  - Images completed: {checkpoint.get('images_completed', 0)}")
    console.print(f"  - Images remaining: {checkpoint.get('images_remaining', 0)}")

    return {"status": "resume_not_implemented", "checkpoint": checkpoint}


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
        result = asyncio.run(load_checkpoint_and_resume(checkpoint_path, config))
        if args.json:
            print(json.dumps(result, indent=2))
        return 0 if result.get("status") != "error" else 1

    # Interactive mode if no input provided
    if args.input_source is None:
        if args.json:
            print(json.dumps({"error": "No input provided. Use --input or -i flag."}))
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

        if not args.json and not check_keys_and_prompt_if_missing():
            print("\nCannot proceed without API keys configured.")
            print("Run: visual-explainer --setup-keys")
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

    # Determine style (interactive selection if not specified and not quiet/json)
    style_name = args.style
    if style_name is None and not args.quiet and not args.json and RICH_AVAILABLE:
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
