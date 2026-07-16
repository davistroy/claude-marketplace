"""Rich-based console reporting and interactive prompts for the CLI.

Holds all user-facing rendering (welcome banner, analysis summary, dry-run
plan, completion summary), the cost estimator, the generation progress
tracker, and the interactive prompts used when running in a TTY.

Terminal singletons are always referenced module-qualified via ``terminal``
so patches on ``visual_explainer.terminal.<symbol>`` intercept every call.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from . import terminal

# Rich UI classes (available whenever RICH_AVAILABLE is True)
try:
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
except ImportError:
    pass

if TYPE_CHECKING:
    from visual_explainer.config import GenerationConfig
    from visual_explainer.models import (
        ConceptAnalysis,
        EvaluationResult,
        ImagePrompt,
        ImageResult,
    )


def display_welcome() -> None:
    """Display the welcome header."""
    console = terminal.get_console()
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
    console = terminal.get_console()

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
    if not terminal.is_interactive():
        return "professional-clean"

    console = terminal.get_console()

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
    if not terminal.is_interactive():
        return recommended

    console = terminal.get_console()

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
    if not terminal.is_interactive():
        raise RuntimeError(
            "Cannot prompt for input in non-interactive mode. "
            "Use --input or -i flag to provide input."
        )

    console = terminal.get_console()

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
    console = terminal.get_console()

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
        self.console = terminal.get_console() if terminal.RICH_AVAILABLE else None
        self.progress: Progress | None = None
        self.current_image = 0
        self.current_attempt = 0
        self.task_id: TaskID | None = None
        self._use_unicode = terminal.supports_unicode()

    def __enter__(self) -> GenerationProgress:
        """Enter context manager."""
        if not self.quiet and terminal.RICH_AVAILABLE:
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
    console = terminal.get_console()

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
