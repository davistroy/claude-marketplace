"""Output organization and file management for Visual Concept Explainer.

This module provides the OutputManager class which handles all file operations
including:
- Creating the output directory structure per §3 Phase 8
- Saving attempt images, prompts, and evaluations
- Creating final image copies and the all-images directory
- Writing metadata.json, concepts.json, and summary.md
- Checkpoint save/load for resume support

Directory structure:
    visual-explainer-[topic-slug]-[timestamp]/
        metadata.json           # Full generation metadata
        concepts.json           # Extracted concepts
        summary.md              # Human-readable report
        checkpoint.json         # Resume state (if generation incomplete)
        all-images/             # Final images only, numbered
            01-[title-slug].jpg
            02-[title-slug].jpg
        image-01/
            final.jpg           # Copy of best attempt
            prompt-v1.txt       # Original prompt
            attempt-01.jpg      # First attempt
            evaluation-01.json  # First evaluation
            prompt-v2.txt       # Refined prompt (if needed)
            attempt-02.jpg      # Second attempt (if needed)
            ...
        image-02/
            ...
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import aiofiles
import aiofiles.os

if TYPE_CHECKING:
    from .models import (
        ConceptAnalysis,
        EvaluationResult,
        GenerationMetadata,
        ImagePrompt,
        ImageResult,
    )


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a URL-safe slug.

    Args:
        text: The text to convert.
        max_length: Maximum length of the slug.

    Returns:
        Lowercase string with only alphanumeric characters and hyphens.
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    # Truncate to max length, avoiding cutting mid-word if possible
    if len(slug) > max_length:
        truncated = slug[:max_length]
        last_hyphen = truncated.rfind("-")
        if last_hyphen > max_length // 2:
            slug = truncated[:last_hyphen]
        else:
            slug = truncated.rstrip("-")
    return slug or "untitled"


def format_timestamp(dt: datetime | None = None) -> str:
    """Format timestamp as YYYYMMDD-HHMMSS.

    Args:
        dt: Datetime to format, defaults to now.

    Returns:
        Formatted timestamp string.
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y%m%d-%H%M%S")


class OutputManager:
    """Manages all file operations for visual explanation generation.

    This class handles the creation and organization of all output files
    including images, prompts, evaluations, metadata, and checkpoints.

    Attributes:
        base_dir: Base output directory (e.g., ./output).
        topic: Topic name for the output folder.
        session_dir: Full path to the session output directory.
        timestamp: Timestamp string for this session.
    """

    def __init__(
        self,
        base_dir: Path | str,
        topic: str,
        timestamp: datetime | None = None,
    ) -> None:
        """Initialize the output manager.

        Args:
            base_dir: Base output directory (e.g., ./output).
            topic: Topic name for directory naming.
            timestamp: Session timestamp, defaults to now.
        """
        self.base_dir = Path(base_dir)
        self.topic = topic
        self.topic_slug = slugify(topic)
        self._timestamp_dt = timestamp or datetime.now()
        self.timestamp = format_timestamp(self._timestamp_dt)

        # Build session directory name
        self.session_name = f"visual-explainer-{self.topic_slug}-{self.timestamp}"
        self.session_dir = self.base_dir / self.session_name

        # Track whether directories have been created
        self._initialized = False

    @classmethod
    def from_checkpoint(cls, checkpoint_path: Path | str) -> OutputManager:
        """Restore OutputManager from a checkpoint file.

        Args:
            checkpoint_path: Path to the checkpoint.json file.

        Returns:
            OutputManager configured to resume the session.

        Raises:
            FileNotFoundError: If checkpoint file doesn't exist.
            ValueError: If checkpoint is invalid.
        """
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        with open(checkpoint_path, encoding="utf-8") as f:
            checkpoint = json.load(f)

        # Extract session info from checkpoint
        session_dir = checkpoint_path.parent
        topic = checkpoint.get("topic", "unknown")

        # Parse timestamp from session directory name
        session_name = session_dir.name
        # Format: visual-explainer-[slug]-[timestamp]
        match = re.search(r"-(\d{8}-\d{6})$", session_name)
        if match:
            timestamp_str = match.group(1)
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
        else:
            timestamp = datetime.now()

        manager = cls(
            base_dir=session_dir.parent,
            topic=topic,
            timestamp=timestamp,
        )
        manager._initialized = True
        return manager

    async def initialize(self) -> None:
        """Create the output directory structure.

        Creates:
            - Session root directory
            - all-images/ subdirectory
        """
        if self._initialized:
            return

        # Create main directories
        await aiofiles.os.makedirs(self.session_dir, exist_ok=True)
        await aiofiles.os.makedirs(self.session_dir / "all-images", exist_ok=True)

        self._initialized = True

    async def create_image_directory(self, image_number: int) -> Path:
        """Create directory for a specific image.

        Args:
            image_number: Image number (1-indexed).

        Returns:
            Path to the image directory (e.g., image-01/).
        """
        await self.initialize()
        image_dir = self.session_dir / f"image-{image_number:02d}"
        await aiofiles.os.makedirs(image_dir, exist_ok=True)
        return image_dir

    async def save_attempt_image(
        self,
        image_number: int,
        attempt_number: int,
        image_bytes: bytes,
    ) -> Path:
        """Save an image generation attempt.

        Args:
            image_number: Image number (1-indexed).
            attempt_number: Attempt number (1-indexed).
            image_bytes: Raw image bytes (JPEG).

        Returns:
            Path to the saved image file.
        """
        image_dir = await self.create_image_directory(image_number)
        filename = f"attempt-{attempt_number:02d}.jpg"
        filepath = image_dir / filename

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(image_bytes)

        return filepath

    async def save_prompt(
        self,
        image_number: int,
        version: int,
        prompt: ImagePrompt,
    ) -> Path:
        """Save a prompt version as text file.

        Args:
            image_number: Image number (1-indexed).
            version: Prompt version (1-indexed).
            prompt: The ImagePrompt to save.

        Returns:
            Path to the saved prompt file.
        """
        image_dir = await self.create_image_directory(image_number)
        filename = f"prompt-v{version}.txt"
        filepath = image_dir / filename

        # Format prompt as readable text
        content = self._format_prompt_text(prompt)

        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)

        return filepath

    def _format_prompt_text(self, prompt: ImagePrompt) -> str:
        """Format an ImagePrompt as readable text.

        Args:
            prompt: The prompt to format.

        Returns:
            Formatted text representation.
        """
        lines = [
            f"Image {prompt.image_number}: {prompt.title}",
            "=" * 60,
            "",
            "## Visual Intent",
            prompt.visual_intent,
            "",
            "## Main Prompt",
            prompt.prompt.main_prompt,
            "",
        ]

        if prompt.prompt.style_guidance:
            lines.extend(["## Style Guidance", prompt.prompt.style_guidance, ""])

        if prompt.prompt.composition:
            lines.extend(["## Composition", prompt.prompt.composition, ""])

        if prompt.prompt.color_palette:
            lines.extend(["## Color Palette", prompt.prompt.color_palette, ""])

        if prompt.prompt.avoid:
            lines.extend(["## Avoid", prompt.prompt.avoid, ""])

        if prompt.success_criteria:
            lines.append("## Success Criteria")
            for criterion in prompt.success_criteria:
                lines.append(f"- {criterion}")
            lines.append("")

        if prompt.concepts_covered:
            lines.append(f"## Concepts Covered: {prompt.concepts_covered}")
            lines.append("")

        if prompt.flow_connection.transition_intent:
            lines.extend(
                [
                    "## Flow Connection",
                    f"Previous: {prompt.flow_connection.previous or 'None (first image)'}",
                    f"Next: {prompt.flow_connection.next_image or 'None (last image)'}",
                    f"Transition: {prompt.flow_connection.transition_intent}",
                ]
            )

        return "\n".join(lines)

    async def save_evaluation(
        self,
        image_number: int,
        attempt_number: int,
        evaluation: EvaluationResult,
    ) -> Path:
        """Save an evaluation result as JSON.

        Args:
            image_number: Image number (1-indexed).
            attempt_number: Attempt number (1-indexed).
            evaluation: The evaluation result.

        Returns:
            Path to the saved evaluation file.
        """
        image_dir = await self.create_image_directory(image_number)
        filename = f"evaluation-{attempt_number:02d}.json"
        filepath = image_dir / filename

        # Serialize evaluation to JSON
        eval_dict = evaluation.model_dump(mode="json")

        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(json.dumps(eval_dict, indent=2))

        return filepath

    async def create_final_image(
        self,
        image_number: int,
        best_attempt: int,
    ) -> Path:
        """Create final.jpg as a copy of the best attempt.

        Args:
            image_number: Image number (1-indexed).
            best_attempt: Attempt number to use as final.

        Returns:
            Path to the final.jpg file.
        """
        image_dir = self.session_dir / f"image-{image_number:02d}"
        attempt_path = image_dir / f"attempt-{best_attempt:02d}.jpg"
        final_path = image_dir / "final.jpg"

        # Copy the best attempt to final.jpg
        # Note: shutil.copy2 preserves metadata
        if attempt_path.exists():
            shutil.copy2(attempt_path, final_path)

        return final_path

    async def copy_to_all_images(
        self,
        image_number: int,
        title: str,
    ) -> Path:
        """Copy final image to all-images directory with numbered name.

        Args:
            image_number: Image number (1-indexed).
            title: Image title for filename.

        Returns:
            Path to the copied file in all-images/.
        """
        final_path = self.session_dir / f"image-{image_number:02d}" / "final.jpg"
        title_slug = slugify(title, max_length=40)
        dest_name = f"{image_number:02d}-{title_slug}.jpg"
        dest_path = self.session_dir / "all-images" / dest_name

        if final_path.exists():
            shutil.copy2(final_path, dest_path)

        return dest_path

    async def save_metadata(self, metadata: GenerationMetadata) -> Path:
        """Write metadata.json with full generation metadata.

        Args:
            metadata: The GenerationMetadata to save.

        Returns:
            Path to the metadata.json file.
        """
        await self.initialize()
        filepath = self.session_dir / "metadata.json"

        # Use model's JSON serialization
        metadata_dict = metadata.to_json_dict()

        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(json.dumps(metadata_dict, indent=2))

        return filepath

    async def save_concepts(self, analysis: ConceptAnalysis) -> Path:
        """Write concepts.json with the extracted concept analysis.

        Args:
            analysis: The ConceptAnalysis to save.

        Returns:
            Path to the concepts.json file.
        """
        await self.initialize()
        filepath = self.session_dir / "concepts.json"

        # Serialize to JSON
        analysis_dict = analysis.model_dump(mode="json")

        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(json.dumps(analysis_dict, indent=2))

        return filepath

    async def generate_summary(
        self,
        analysis: ConceptAnalysis,
        metadata: GenerationMetadata,
        image_results: list[ImageResult],
    ) -> Path:
        """Generate summary.md human-readable report.

        Args:
            analysis: The concept analysis.
            metadata: Generation metadata.
            image_results: Results for each image.

        Returns:
            Path to the summary.md file.
        """
        await self.initialize()
        filepath = self.session_dir / "summary.md"

        content = self._generate_summary_content(analysis, metadata, image_results)

        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)

        return filepath

    def _generate_summary_content(
        self,
        analysis: ConceptAnalysis,
        metadata: GenerationMetadata,
        image_results: list[ImageResult],
    ) -> str:
        """Generate the content for summary.md.

        Args:
            analysis: The concept analysis.
            metadata: Generation metadata.
            image_results: Results for each image.

        Returns:
            Markdown content for the summary.
        """
        # Calculate statistics
        completed = len([r for r in image_results if r.status == "complete"])
        failed = len([r for r in image_results if r.status == "failed"])
        total_attempts = sum(r.total_attempts for r in image_results)
        avg_score = 0.0
        scores = [r.final_score for r in image_results if r.final_score is not None]
        if scores:
            avg_score = sum(scores) / len(scores)

        lines = [
            f"# Visual Explanation: {analysis.title}",
            "",
            f"**Generated:** {metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(metadata.timestamp, 'strftime') else metadata.timestamp}",
            f"**Session ID:** {metadata.generation_id}",
            "",
            "---",
            "",
            "## Summary",
            "",
            analysis.summary,
            "",
            "---",
            "",
            "## Generation Results",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Images Planned | {metadata.results.images_planned} |",
            f"| Images Generated | {completed} |",
            f"| Failed | {failed} |",
            f"| Total Attempts | {total_attempts} |",
            f"| Average Quality Score | {avg_score:.1%} |",
            f"| Estimated Cost | {metadata.results.estimated_cost} |",
            "",
            "---",
            "",
            "## Concepts Analyzed",
            "",
            f"**Target Audience:** {analysis.target_audience}",
            f"**Concepts Identified:** {len(analysis.concepts)}",
            "",
        ]

        # List concepts
        for concept in analysis.concepts:
            lines.append(f"### {concept.id}. {concept.name}")
            lines.append("")
            lines.append(concept.description)
            lines.append("")
            lines.append(f"- **Complexity:** {concept.complexity.value}")
            lines.append(f"- **Visual Potential:** {concept.visual_potential.value}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## Generated Images",
                "",
            ]
        )

        # List image results
        for result in image_results:
            status_emoji = "OK" if result.status == "complete" else "FAILED"
            score_str = f"{result.final_score:.1%}" if result.final_score else "N/A"
            lines.append(f"### Image {result.image_number}: {result.title}")
            lines.append("")
            lines.append(f"- **Status:** {status_emoji}")
            lines.append(f"- **Attempts:** {result.total_attempts}")
            lines.append(f"- **Final Score:** {score_str}")
            if result.final_path:
                # Make path relative to summary.md location
                rel_path = Path(result.final_path).name
                if f"image-{result.image_number:02d}" in result.final_path:
                    rel_path = f"image-{result.image_number:02d}/final.jpg"
                lines.append(f"- **Final Image:** [{rel_path}]({rel_path})")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## Configuration",
                "",
                "| Setting | Value |",
                "|---------|-------|",
                f"| Max Iterations | {metadata.config.max_iterations} |",
                f"| Pass Threshold | {metadata.config.pass_threshold:.0%} |",
                f"| Aspect Ratio | {metadata.config.aspect_ratio} |",
                f"| Resolution | {metadata.config.resolution} |",
                f"| Style | {metadata.config.style} |",
                f"| Concurrency | {metadata.config.concurrency} |",
                "",
                "---",
                "",
                "*Generated by Visual Concept Explainer*",
            ]
        )

        return "\n".join(lines)

    async def save_checkpoint(
        self,
        state: CheckpointState,
    ) -> Path:
        """Save checkpoint for resume support.

        Args:
            state: Current generation state.

        Returns:
            Path to the checkpoint.json file.
        """
        await self.initialize()
        filepath = self.session_dir / "checkpoint.json"

        checkpoint_dict = state.to_dict()
        checkpoint_dict["topic"] = self.topic
        checkpoint_dict["session_name"] = self.session_name
        checkpoint_dict["saved_at"] = format_timestamp()

        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(json.dumps(checkpoint_dict, indent=2))

        return filepath

    async def load_checkpoint(self) -> CheckpointState | None:
        """Load checkpoint if it exists.

        Returns:
            CheckpointState if found, None otherwise.
        """
        filepath = self.session_dir / "checkpoint.json"
        if not filepath.exists():
            return None

        async with aiofiles.open(filepath, encoding="utf-8") as f:
            content = await f.read()

        checkpoint_dict = json.loads(content)
        return CheckpointState.from_dict(checkpoint_dict)

    async def delete_checkpoint(self) -> None:
        """Delete the checkpoint file after successful completion."""
        filepath = self.session_dir / "checkpoint.json"
        if filepath.exists():
            await aiofiles.os.remove(filepath)

    def get_image_dir(self, image_number: int) -> Path:
        """Get the path to an image directory.

        Args:
            image_number: Image number (1-indexed).

        Returns:
            Path to the image directory.
        """
        return self.session_dir / f"image-{image_number:02d}"

    def get_attempt_path(self, image_number: int, attempt_number: int) -> Path:
        """Get the path to a specific attempt image.

        Args:
            image_number: Image number (1-indexed).
            attempt_number: Attempt number (1-indexed).

        Returns:
            Path to the attempt image file.
        """
        return self.get_image_dir(image_number) / f"attempt-{attempt_number:02d}.jpg"

    def get_final_path(self, image_number: int) -> Path:
        """Get the path to the final image for an image number.

        Args:
            image_number: Image number (1-indexed).

        Returns:
            Path to the final.jpg file.
        """
        return self.get_image_dir(image_number) / "final.jpg"

    @property
    def all_images_dir(self) -> Path:
        """Get the path to the all-images directory."""
        return self.session_dir / "all-images"

    @property
    def metadata_path(self) -> Path:
        """Get the path to metadata.json."""
        return self.session_dir / "metadata.json"

    @property
    def concepts_path(self) -> Path:
        """Get the path to concepts.json."""
        return self.session_dir / "concepts.json"

    @property
    def summary_path(self) -> Path:
        """Get the path to summary.md."""
        return self.session_dir / "summary.md"

    @property
    def checkpoint_path(self) -> Path:
        """Get the path to checkpoint.json."""
        return self.session_dir / "checkpoint.json"


class CheckpointState:
    """State container for checkpoint save/restore.

    This class captures the current state of generation for resume support.
    It tracks which images have been completed, their results, and the
    current position in the generation process.

    Attributes:
        generation_id: Unique ID for this generation session.
        started_at: When generation started.
        current_image: Image currently being processed (1-indexed).
        current_attempt: Current attempt number for the image.
        completed_images: List of completed image numbers.
        image_results: Results for each completed image.
        total_images: Total number of images planned.
        config: Generation configuration snapshot.
        analysis_hash: Hash of the concept analysis for validation.
    """

    def __init__(
        self,
        generation_id: str,
        started_at: str,
        total_images: int,
        config: dict[str, Any],
        analysis_hash: str,
    ) -> None:
        """Initialize checkpoint state.

        Args:
            generation_id: Unique session ID.
            started_at: ISO timestamp when generation started.
            total_images: Total number of images to generate.
            config: Generation configuration dict.
            analysis_hash: SHA-256 hash of concept analysis.
        """
        self.generation_id = generation_id
        self.started_at = started_at
        self.total_images = total_images
        self.config = config
        self.analysis_hash = analysis_hash

        # Mutable state
        self.current_image: int = 1
        self.current_attempt: int = 0
        self.completed_images: list[int] = []
        self.image_results: dict[int, dict[str, Any]] = {}
        self.status: Literal["in_progress", "completed", "failed"] = "in_progress"

    def update_progress(
        self,
        image_number: int,
        attempt_number: int,
    ) -> None:
        """Update current progress position.

        Args:
            image_number: Current image being processed.
            attempt_number: Current attempt number.
        """
        self.current_image = image_number
        self.current_attempt = attempt_number

    def mark_image_complete(
        self,
        image_number: int,
        result: dict[str, Any],
    ) -> None:
        """Mark an image as completed.

        Args:
            image_number: The completed image number.
            result: Result data for the image.
        """
        if image_number not in self.completed_images:
            self.completed_images.append(image_number)
        self.image_results[image_number] = result

    def is_image_complete(self, image_number: int) -> bool:
        """Check if an image has been completed.

        Args:
            image_number: Image number to check.

        Returns:
            True if the image is complete.
        """
        return image_number in self.completed_images

    def get_next_image(self) -> int | None:
        """Get the next image number to process.

        Returns:
            Next image number, or None if all complete.
        """
        for i in range(1, self.total_images + 1):
            if i not in self.completed_images:
                return i
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize checkpoint state to dictionary.

        Returns:
            Dictionary representation of the state.
        """
        return {
            "generation_id": self.generation_id,
            "started_at": self.started_at,
            "total_images": self.total_images,
            "config": self.config,
            "analysis_hash": self.analysis_hash,
            "current_image": self.current_image,
            "current_attempt": self.current_attempt,
            "completed_images": self.completed_images,
            "image_results": self.image_results,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointState:
        """Restore checkpoint state from dictionary.

        Args:
            data: Dictionary with checkpoint data.

        Returns:
            Restored CheckpointState instance.
        """
        state = cls(
            generation_id=data["generation_id"],
            started_at=data["started_at"],
            total_images=data["total_images"],
            config=data.get("config", {}),
            analysis_hash=data.get("analysis_hash", ""),
        )
        state.current_image = data.get("current_image", 1)
        state.current_attempt = data.get("current_attempt", 0)
        state.completed_images = data.get("completed_images", [])
        state.image_results = data.get("image_results", {})
        state.status = data.get("status", "in_progress")
        return state

    def finalize(self, success: bool = True) -> None:
        """Mark generation as finalized.

        Args:
            success: Whether generation completed successfully.
        """
        self.status = "completed" if success else "failed"


async def finalize_output(
    output_manager: OutputManager,
    image_results: list[ImageResult],
) -> list[Path]:
    """Finalize all output files after generation completes.

    This function:
    1. Creates final.jpg for each image from best attempt
    2. Copies finals to all-images/ with numbered names

    Args:
        output_manager: The output manager instance.
        image_results: Results for all generated images.

    Returns:
        List of paths to all final images.
    """
    final_paths: list[Path] = []

    for result in image_results:
        if result.status != "complete" or result.final_attempt is None:
            continue

        # Create final.jpg copy
        await output_manager.create_final_image(
            image_number=result.image_number,
            best_attempt=result.final_attempt,
        )

        # Copy to all-images/
        all_images_path = await output_manager.copy_to_all_images(
            image_number=result.image_number,
            title=result.title,
        )
        final_paths.append(all_images_path)

    return final_paths


def load_checkpoint_from_path(checkpoint_path: Path | str) -> CheckpointState:
    """Load a CheckpointState directly from a checkpoint file path.

    This is a convenience function for resume functionality that reads
    and parses a checkpoint JSON file into a CheckpointState object.

    Args:
        checkpoint_path: Path to the checkpoint.json file.

    Returns:
        Parsed CheckpointState instance.

    Raises:
        FileNotFoundError: If the checkpoint file does not exist.
        ValueError: If the checkpoint JSON is invalid or missing required fields.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

    with open(checkpoint_path, encoding="utf-8") as f:
        data = json.load(f)

    # Validate required fields
    required_fields = ["generation_id", "started_at", "total_images"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Checkpoint missing required fields: {', '.join(missing)}")

    return CheckpointState.from_dict(data)
