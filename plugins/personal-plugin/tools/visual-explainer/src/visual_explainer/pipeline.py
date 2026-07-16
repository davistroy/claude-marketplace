"""End-to-end generation pipeline for visual-explainer.

Contains the phase helpers (concept analysis, prompt generation, image
generation with evaluation/refinement, output saving) and the two
top-level orchestrators: ``run_generation_pipeline`` and
``load_checkpoint_and_resume``.

Sibling pipeline helpers are called by BARE name so a patch on
``visual_explainer.pipeline.<helper>`` intercepts them; terminal singletons
are referenced module-qualified via ``terminal``.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from . import terminal
from .config import GenerationConfig, InternalConfig
from .io_utils import _atomic_write_text
from .reporting import (
    ConcurrentGenerationProgress,
    GenerationProgress,
    display_analysis_summary,
    display_completion_summary,
    display_dry_run_plan,
)

# Rich UI classes (available whenever RICH_AVAILABLE is True)
try:
    from rich.panel import Panel
except ImportError:
    pass

if TYPE_CHECKING:
    from rich.console import Console

    from visual_explainer.config import StyleConfig
    from visual_explainer.image_evaluator import ImageEvaluator
    from visual_explainer.image_generator import GeminiImageGenerator, GenerationResult
    from visual_explainer.models import (
        ConceptAnalysis,
        EvaluationResult,
        ImagePrompt,
        ImageResult,
    )
    from visual_explainer.prompt_generator import PromptGenerator
    from visual_explainer.reporting import ProgressReporter


async def _analyze_concepts(
    config: GenerationConfig,
    internal_config: InternalConfig,
    style_name: str,
    console: Console | None,
    infographic_mode: bool,
) -> tuple[ConceptAnalysis, StyleConfig, str, int]:
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
    style: StyleConfig,
    console: Console | None,
    infographic_mode: bool,
) -> tuple[list[ImagePrompt], PromptGenerator, int]:
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

    prompt_generator = PromptGenerator(
        internal_config=internal_config, model=internal_config.claude_model
    )

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
    gen_result: GenerationResult,
    current_prompt: ImagePrompt,
    prompt: ImagePrompt,
    attempt: int,
    image_dir: Path,
    image_evaluator: ImageEvaluator,
    analysis: ConceptAnalysis,
    total_prompts: int,
    style_display_name: str,
    result: ImageResult,
    progress: ProgressReporter,
    prompt_generator: PromptGenerator,
    style: StyleConfig,
    config: GenerationConfig,
) -> tuple[EvaluationResult, ImagePrompt, int]:
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
        Tuple of (eval_result, possibly_refined_prompt, api_calls).
    """
    from visual_explainer.models import EvaluationVerdict

    api_calls = 0

    # gen_result.image_data is bytes | None on GenerationResult, but the only
    # caller (_generate_single_image) already `continue`s past any gen_result
    # with image_data is None before invoking this helper, so it is always
    # bytes here.
    assert gen_result.image_data is not None

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
    _atomic_write_text(
        eval_file,
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


async def _generate_single_image(
    prompt: ImagePrompt,
    config: GenerationConfig,
    internal_config: InternalConfig,
    analysis: ConceptAnalysis,
    style: StyleConfig,
    style_display_name: str,
    prompt_generator: PromptGenerator,
    output_dir: Path,
    image_generator: GeminiImageGenerator,
    image_evaluator: ImageEvaluator,
    progress: ProgressReporter,
    *,
    concurrent: bool,
) -> tuple[ImageResult, int]:
    """Generate one image end-to-end: attempt loop, best-tracking, finalize.

    This is the per-image body extracted from ``_execute_generation_loop`` so a
    single image can be produced independently (own ``image-NN/`` directory, own
    ``ImageResult``, own prompt-refinement chain). It is called once per prompt,
    either serially or as one task among several under a concurrency semaphore.

    Per-image framing (``start_image`` / ``complete_image`` / ``fail_image``) is
    called polymorphically on ``progress``: the rich reporter renders a live
    spinner/rule; the concurrency-safe reporter emits discrete, lock-guarded
    lines. The per-attempt spinner calls (``start_attempt`` and the
    ``update_status`` status lines) are gated behind ``concurrent`` and fire only
    on the serial path — driving a shared per-attempt live render from
    interleaved coroutines is exactly what is unsafe. (``_evaluate_and_refine``
    still calls ``update_status`` / ``show_evaluation`` on ``progress``; those
    are no-ops on the concurrency-safe reporter.)

    Args:
        prompt: The image prompt to generate.
        config: Generation configuration.
        internal_config: Internal configuration.
        analysis: Concept analysis result.
        style: Loaded style configuration.
        style_display_name: Display name of the style.
        prompt_generator: Prompt generator for refinements.
        output_dir: Output directory for generated files.
        image_generator: Shared image generator instance.
        image_evaluator: Shared image evaluator instance.
        progress: Progress reporter (rich spinner when serial, concurrency-safe
            reporter when concurrent). ``progress.total_images`` supplies the
            evaluation context's total-image count.
        concurrent: Whether this image is being generated concurrently. Gates the
            per-attempt spinner calls (serial only).

    Returns:
        Tuple of (image_result, api_calls_for_this_image).
    """
    import shutil

    from visual_explainer.image_generator import GenerationStatus
    from visual_explainer.models import EvaluationVerdict, ImageResult

    api_calls = 0

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
        # Per-attempt live spinner is serial-only (unsafe across coroutines).
        if not concurrent:
            progress.start_attempt(attempt)

        # Save prompt
        prompt_file = image_dir / f"prompt-v{attempt}.txt"
        prompt_file.write_text(current_prompt.prompt.main_prompt, encoding="utf-8")

        # Generate image
        if not concurrent:
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
            if not concurrent:
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
            total_prompts=progress.total_images,
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
        progress.fail_image(prompt.image_number, prompt.title)

    return result, api_calls


async def _execute_generation_loop(
    prompts: list[ImagePrompt],
    config: GenerationConfig,
    internal_config: InternalConfig,
    analysis: ConceptAnalysis,
    style: StyleConfig,
    style_display_name: str,
    prompt_generator: PromptGenerator,
    output_dir: Path,
    quiet: bool = False,
    json_output: bool = False,
) -> tuple[list[ImageResult], int]:
    """Execute the image generation for all prompts (Steps 6-8 of the pipeline).

    Initializes ONE image generator and ONE evaluator (both safe for concurrent
    use — the generator runs its blocking work in a thread-pool executor), then
    produces each image via :func:`_generate_single_image`.

    The images are independent (own directory, own ``ImageResult``, own
    refinement chain), so they run in parallel up to ``config.concurrency``:

    - ``effective = min(config.concurrency, len(prompts))``; a single prompt (or
      ``effective <= 1``) runs on the **serial** path, which is byte-for-byte
      identical to the original loop — same ordering, same rich live spinner.
    - Otherwise an :class:`asyncio.Semaphore` bounds in-flight images to
      ``effective`` (memory-bounded: each 4K image holds decoded bytes in RAM),
      and ``asyncio.gather`` collects results **in prompt order** — the returned
      list is ordered by image number, never by completion order.

    API-call counts are summed from each image's own returned count rather than
    read off the shared generator, so concurrent counting stays correct.

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
    from visual_explainer.image_evaluator import ImageEvaluator
    from visual_explainer.image_generator import GeminiImageGenerator

    image_generator = GeminiImageGenerator(
        internal_config=internal_config,
    )
    image_evaluator = ImageEvaluator(
        model=internal_config.claude_model, pass_threshold=config.pass_threshold
    )

    suppress_output = quiet or json_output
    effective = min(config.concurrency, len(prompts))

    # --- Serial path: unchanged behavior, full rich live spinner ---
    if len(prompts) <= 1 or effective <= 1:
        image_results: list[ImageResult] = []
        total_api_calls = 0
        with GenerationProgress(len(prompts), config.max_iterations, suppress_output) as progress:
            for prompt in prompts:
                result, api_calls = await _generate_single_image(
                    prompt,
                    config,
                    internal_config,
                    analysis,
                    style,
                    style_display_name,
                    prompt_generator,
                    output_dir,
                    image_generator,
                    image_evaluator,
                    progress,
                    concurrent=False,
                )
                image_results.append(result)
                total_api_calls += api_calls
        return image_results, total_api_calls

    # --- Concurrent path: bounded parallelism, prompt-ordered results ---
    semaphore = asyncio.Semaphore(effective)
    reporter = ConcurrentGenerationProgress(len(prompts), config.max_iterations, suppress_output)

    async def _bounded_generate(prompt: ImagePrompt) -> tuple[ImageResult, int]:
        async with semaphore:
            return await _generate_single_image(
                prompt,
                config,
                internal_config,
                analysis,
                style,
                style_display_name,
                prompt_generator,
                output_dir,
                image_generator,
                image_evaluator,
                reporter,
                concurrent=True,
            )

    # gather preserves input order, so results are ordered by prompt/image_number.
    results_with_counts = await asyncio.gather(*(_bounded_generate(p) for p in prompts))

    image_results = [result for result, _ in results_with_counts]
    total_api_calls = sum(api_calls for _, api_calls in results_with_counts)
    return image_results, total_api_calls


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
    _atomic_write_text(metadata_file, json.dumps(metadata, indent=2), encoding="utf-8")

    # Save concepts
    concepts_file = output_dir / "concepts.json"
    _atomic_write_text(
        concepts_file,
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
    console = terminal.get_console() if not quiet and not json_output else None
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

    console = terminal.get_console() if not quiet and not json_output else None

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
