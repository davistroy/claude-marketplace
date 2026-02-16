"""Tests for output module.

Tests OutputManager and CheckpointState including:
- Directory creation and structure
- File writing (images, prompts, evaluations)
- Checkpoint save/load/delete
- Summary generation
- Slugify and timestamp formatting
- Final image operations
- From checkpoint restoration
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from visual_explainer.models import (
    ImageResult,
)
from visual_explainer.output import (
    CheckpointState,
    OutputManager,
    finalize_output,
    format_timestamp,
    slugify,
)

# ---------------------------------------------------------------------------
# Slugify Tests
# ---------------------------------------------------------------------------


class TestSlugify:
    """Tests for the slugify function."""

    def test_basic_text(self):
        """Test basic text slugification."""
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self):
        """Test special characters are removed."""
        assert slugify("Hello! @World #2024") == "hello-world-2024"

    def test_underscores_converted(self):
        """Test underscores become hyphens."""
        assert slugify("hello_world_test") == "hello-world-test"

    def test_multiple_spaces(self):
        """Test multiple spaces collapse to single hyphen."""
        assert slugify("hello   world") == "hello-world"

    def test_leading_trailing_hyphens(self):
        """Test leading/trailing hyphens stripped."""
        assert slugify("--hello-world--") == "hello-world"

    def test_max_length(self):
        """Test truncation at max length."""
        result = slugify("a" * 100, max_length=20)
        assert len(result) <= 20

    def test_max_length_word_boundary(self):
        """Test truncation respects word boundaries."""
        result = slugify("hello-world-testing-long-text", max_length=15)
        assert len(result) <= 15
        assert not result.endswith("-")

    def test_empty_text(self):
        """Test empty string returns 'untitled'."""
        assert slugify("") == "untitled"

    def test_only_special_chars(self):
        """Test only special characters returns 'untitled'."""
        assert slugify("!@#$%") == "untitled"


# ---------------------------------------------------------------------------
# Format Timestamp Tests
# ---------------------------------------------------------------------------


class TestFormatTimestamp:
    """Tests for the format_timestamp function."""

    def test_specific_datetime(self):
        """Test formatting a specific datetime."""
        dt = datetime(2026, 1, 18, 14, 30, 52)
        assert format_timestamp(dt) == "20260118-143052"

    def test_none_uses_now(self):
        """Test None defaults to current time."""
        result = format_timestamp()
        assert len(result) == 15  # YYYYMMDD-HHMMSS
        assert "-" in result


# ---------------------------------------------------------------------------
# OutputManager Init Tests
# ---------------------------------------------------------------------------


class TestOutputManagerInit:
    """Tests for OutputManager initialization."""

    def test_basic_init(self, tmp_path):
        """Test basic initialization with topic."""
        mgr = OutputManager(tmp_path, "Machine Learning Basics")
        assert mgr.base_dir == tmp_path
        assert mgr.topic == "Machine Learning Basics"
        assert mgr.topic_slug == "machine-learning-basics"
        assert "visual-explainer-machine-learning-basics" in mgr.session_name
        assert not mgr._initialized

    def test_session_dir_construction(self, tmp_path):
        """Test session directory path construction."""
        dt = datetime(2026, 1, 18, 12, 0, 0)
        mgr = OutputManager(tmp_path, "Test Topic", timestamp=dt)
        assert mgr.session_dir == tmp_path / "visual-explainer-test-topic-20260118-120000"

    def test_string_base_dir(self, tmp_path):
        """Test string base_dir is converted to Path."""
        mgr = OutputManager(str(tmp_path), "Test")
        assert isinstance(mgr.base_dir, Path)


# ---------------------------------------------------------------------------
# OutputManager Async Operations Tests
# ---------------------------------------------------------------------------


class TestOutputManagerOperations:
    """Tests for OutputManager async file operations."""

    async def test_initialize_creates_dirs(self, tmp_path):
        """Test initialize creates session and all-images directories."""
        mgr = OutputManager(tmp_path, "Test Topic")
        await mgr.initialize()

        assert mgr.session_dir.exists()
        assert (mgr.session_dir / "all-images").exists()
        assert mgr._initialized

    async def test_initialize_idempotent(self, tmp_path):
        """Test calling initialize twice is safe."""
        mgr = OutputManager(tmp_path, "Test Topic")
        await mgr.initialize()
        await mgr.initialize()
        assert mgr.session_dir.exists()

    async def test_create_image_directory(self, tmp_path):
        """Test creating an image directory."""
        mgr = OutputManager(tmp_path, "Test")
        image_dir = await mgr.create_image_directory(1)
        assert image_dir.exists()
        assert image_dir.name == "image-01"

    async def test_create_image_directory_double_digit(self, tmp_path):
        """Test image directory with number > 9."""
        mgr = OutputManager(tmp_path, "Test")
        image_dir = await mgr.create_image_directory(12)
        assert image_dir.name == "image-12"

    async def test_save_attempt_image(self, tmp_path, sample_image_bytes):
        """Test saving an attempt image."""
        mgr = OutputManager(tmp_path, "Test")
        path = await mgr.save_attempt_image(1, 1, sample_image_bytes)

        assert path.exists()
        assert path.name == "attempt-01.jpg"
        assert path.read_bytes() == sample_image_bytes

    async def test_save_prompt(self, tmp_path, sample_image_prompt):
        """Test saving a prompt version."""
        mgr = OutputManager(tmp_path, "Test")
        path = await mgr.save_prompt(1, 1, sample_image_prompt)

        assert path.exists()
        assert path.name == "prompt-v1.txt"
        content = path.read_text(encoding="utf-8")
        assert "Neural Network Architecture" in content

    async def test_save_evaluation(self, tmp_path, sample_evaluation_result):
        """Test saving an evaluation result."""
        mgr = OutputManager(tmp_path, "Test")
        path = await mgr.save_evaluation(1, 1, sample_evaluation_result)

        assert path.exists()
        assert path.name == "evaluation-01.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["overall_score"] == 0.75

    async def test_create_final_image(self, tmp_path, sample_image_bytes):
        """Test creating final.jpg from best attempt."""
        mgr = OutputManager(tmp_path, "Test")
        # First save an attempt
        await mgr.save_attempt_image(1, 2, sample_image_bytes)
        # Create final from attempt 2
        final_path = await mgr.create_final_image(1, 2)

        assert final_path.parent.name == "image-01"
        assert final_path.name == "final.jpg"
        assert final_path.exists()
        assert final_path.read_bytes() == sample_image_bytes

    async def test_copy_to_all_images(self, tmp_path, sample_image_bytes):
        """Test copying final image to all-images directory."""
        mgr = OutputManager(tmp_path, "Test")
        await mgr.initialize()
        # Create image dir and save attempt
        await mgr.save_attempt_image(1, 1, sample_image_bytes)
        await mgr.create_final_image(1, 1)

        dest_path = await mgr.copy_to_all_images(1, "Neural Network")
        assert "all-images" in str(dest_path)
        assert dest_path.name.startswith("01-")
        assert dest_path.exists()


# ---------------------------------------------------------------------------
# Path Property Tests
# ---------------------------------------------------------------------------


class TestOutputManagerPaths:
    """Tests for OutputManager path properties."""

    def test_get_image_dir(self, tmp_path):
        """Test get_image_dir returns correct path."""
        mgr = OutputManager(tmp_path, "Test")
        path = mgr.get_image_dir(3)
        assert path == mgr.session_dir / "image-03"

    def test_get_attempt_path(self, tmp_path):
        """Test get_attempt_path returns correct path."""
        mgr = OutputManager(tmp_path, "Test")
        path = mgr.get_attempt_path(2, 3)
        assert path == mgr.session_dir / "image-02" / "attempt-03.jpg"

    def test_get_final_path(self, tmp_path):
        """Test get_final_path returns correct path."""
        mgr = OutputManager(tmp_path, "Test")
        path = mgr.get_final_path(1)
        assert path == mgr.session_dir / "image-01" / "final.jpg"

    def test_all_images_dir(self, tmp_path):
        """Test all_images_dir property."""
        mgr = OutputManager(tmp_path, "Test")
        assert mgr.all_images_dir == mgr.session_dir / "all-images"

    def test_metadata_path(self, tmp_path):
        """Test metadata_path property."""
        mgr = OutputManager(tmp_path, "Test")
        assert mgr.metadata_path == mgr.session_dir / "metadata.json"

    def test_concepts_path(self, tmp_path):
        """Test concepts_path property."""
        mgr = OutputManager(tmp_path, "Test")
        assert mgr.concepts_path == mgr.session_dir / "concepts.json"

    def test_summary_path(self, tmp_path):
        """Test summary_path property."""
        mgr = OutputManager(tmp_path, "Test")
        assert mgr.summary_path == mgr.session_dir / "summary.md"

    def test_checkpoint_path(self, tmp_path):
        """Test checkpoint_path property."""
        mgr = OutputManager(tmp_path, "Test")
        assert mgr.checkpoint_path == mgr.session_dir / "checkpoint.json"


# ---------------------------------------------------------------------------
# Checkpoint Tests
# ---------------------------------------------------------------------------


class TestCheckpointState:
    """Tests for CheckpointState."""

    def test_init(self):
        """Test CheckpointState initialization."""
        state = CheckpointState(
            generation_id="test-id",
            started_at="2026-01-18T12:00:00",
            total_images=3,
            config={"max_iterations": 5},
            analysis_hash="sha256:abc123",
        )
        assert state.generation_id == "test-id"
        assert state.total_images == 3
        assert state.current_image == 1
        assert state.current_attempt == 0
        assert state.completed_images == []
        assert state.status == "in_progress"

    def test_update_progress(self):
        """Test updating progress position."""
        state = CheckpointState("id", "2026-01-18", 3, {}, "hash")
        state.update_progress(2, 3)
        assert state.current_image == 2
        assert state.current_attempt == 3

    def test_mark_image_complete(self):
        """Test marking an image as complete."""
        state = CheckpointState("id", "2026-01-18", 3, {}, "hash")
        state.mark_image_complete(1, {"score": 0.90})
        assert 1 in state.completed_images
        assert state.image_results[1] == {"score": 0.90}

    def test_mark_image_complete_idempotent(self):
        """Test marking same image complete twice doesn't duplicate."""
        state = CheckpointState("id", "2026-01-18", 3, {}, "hash")
        state.mark_image_complete(1, {"score": 0.90})
        state.mark_image_complete(1, {"score": 0.95})
        assert state.completed_images.count(1) == 1
        assert state.image_results[1] == {"score": 0.95}

    def test_is_image_complete(self):
        """Test checking image completion status."""
        state = CheckpointState("id", "2026-01-18", 3, {}, "hash")
        assert not state.is_image_complete(1)
        state.mark_image_complete(1, {})
        assert state.is_image_complete(1)

    def test_get_next_image(self):
        """Test getting next image to process."""
        state = CheckpointState("id", "2026-01-18", 3, {}, "hash")
        assert state.get_next_image() == 1
        state.mark_image_complete(1, {})
        assert state.get_next_image() == 2
        state.mark_image_complete(2, {})
        assert state.get_next_image() == 3
        state.mark_image_complete(3, {})
        assert state.get_next_image() is None

    def test_to_dict(self):
        """Test serialization to dictionary."""
        state = CheckpointState("test-id", "2026-01-18", 3, {"k": "v"}, "hash")
        state.update_progress(2, 1)
        state.mark_image_complete(1, {"score": 0.9})

        d = state.to_dict()
        assert d["generation_id"] == "test-id"
        assert d["total_images"] == 3
        assert d["current_image"] == 2
        assert d["completed_images"] == [1]
        assert d["status"] == "in_progress"

    def test_from_dict(self):
        """Test restoration from dictionary."""
        data = {
            "generation_id": "restored-id",
            "started_at": "2026-01-18T12:00:00",
            "total_images": 5,
            "config": {"max_iterations": 3},
            "analysis_hash": "sha256:def",
            "current_image": 3,
            "current_attempt": 2,
            "completed_images": [1, 2],
            "image_results": {1: {"score": 0.8}, 2: {"score": 0.9}},
            "status": "in_progress",
        }
        state = CheckpointState.from_dict(data)
        assert state.generation_id == "restored-id"
        assert state.total_images == 5
        assert state.current_image == 3
        assert state.completed_images == [1, 2]

    def test_from_dict_defaults(self):
        """Test from_dict with minimal data."""
        data = {
            "generation_id": "id",
            "started_at": "now",
            "total_images": 1,
        }
        state = CheckpointState.from_dict(data)
        assert state.config == {}
        assert state.analysis_hash == ""
        assert state.completed_images == []

    def test_finalize_success(self):
        """Test finalizing as successful."""
        state = CheckpointState("id", "now", 1, {}, "hash")
        state.finalize(success=True)
        assert state.status == "completed"

    def test_finalize_failure(self):
        """Test finalizing as failed."""
        state = CheckpointState("id", "now", 1, {}, "hash")
        state.finalize(success=False)
        assert state.status == "failed"


# ---------------------------------------------------------------------------
# Checkpoint Save/Load Tests
# ---------------------------------------------------------------------------


class TestCheckpointSaveLoad:
    """Tests for saving and loading checkpoints."""

    async def test_save_checkpoint(self, tmp_path):
        """Test saving a checkpoint file."""
        mgr = OutputManager(tmp_path, "Test Topic")
        state = CheckpointState("test-id", "2026-01-18", 3, {"k": "v"}, "hash")

        path = await mgr.save_checkpoint(state)

        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["generation_id"] == "test-id"
        assert data["topic"] == "Test Topic"
        assert data["session_name"] == mgr.session_name

    async def test_load_checkpoint(self, tmp_path):
        """Test loading a saved checkpoint."""
        mgr = OutputManager(tmp_path, "Test Topic")
        state = CheckpointState("test-id", "2026-01-18", 3, {}, "hash")
        state.mark_image_complete(1, {"score": 0.9})
        await mgr.save_checkpoint(state)

        loaded = await mgr.load_checkpoint()
        assert loaded is not None
        assert loaded.generation_id == "test-id"
        assert 1 in loaded.completed_images

    async def test_load_checkpoint_missing(self, tmp_path):
        """Test loading when no checkpoint exists returns None."""
        mgr = OutputManager(tmp_path, "Test Topic")
        await mgr.initialize()

        loaded = await mgr.load_checkpoint()
        assert loaded is None

    async def test_delete_checkpoint(self, tmp_path):
        """Test deleting a checkpoint file."""
        mgr = OutputManager(tmp_path, "Test Topic")
        state = CheckpointState("test-id", "2026-01-18", 3, {}, "hash")
        await mgr.save_checkpoint(state)
        assert mgr.checkpoint_path.exists()

        await mgr.delete_checkpoint()
        assert not mgr.checkpoint_path.exists()

    async def test_delete_nonexistent_checkpoint(self, tmp_path):
        """Test deleting when no checkpoint is safe."""
        mgr = OutputManager(tmp_path, "Test Topic")
        await mgr.initialize()
        await mgr.delete_checkpoint()  # Should not raise


# ---------------------------------------------------------------------------
# From Checkpoint Tests
# ---------------------------------------------------------------------------


class TestFromCheckpoint:
    """Tests for OutputManager.from_checkpoint."""

    async def test_from_checkpoint(self, tmp_path):
        """Test restoring OutputManager from a checkpoint file."""
        # Create a manager and save a checkpoint
        original = OutputManager(tmp_path, "ML Basics", timestamp=datetime(2026, 1, 18, 12, 0, 0))
        state = CheckpointState("id-123", "2026-01-18T12:00:00", 3, {}, "hash")
        await original.save_checkpoint(state)

        # Restore from checkpoint
        restored = OutputManager.from_checkpoint(original.checkpoint_path)
        assert restored.topic == "ML Basics"
        assert restored._initialized

    def test_from_checkpoint_missing_file(self, tmp_path):
        """Test from_checkpoint with missing file raises."""
        with pytest.raises(FileNotFoundError):
            OutputManager.from_checkpoint(tmp_path / "nonexistent.json")


# ---------------------------------------------------------------------------
# Finalize Output Tests
# ---------------------------------------------------------------------------


class TestFinalizeOutput:
    """Tests for the finalize_output function."""

    async def test_finalize_copies_images(self, tmp_path, sample_image_bytes):
        """Test finalize creates final.jpg and copies to all-images."""
        mgr = OutputManager(tmp_path, "Test")
        await mgr.initialize()
        # Save an attempt image
        await mgr.save_attempt_image(1, 2, sample_image_bytes)

        # Create ImageResult
        result = ImageResult(image_number=1, title="Test Image")
        result.status = "complete"
        result.final_attempt = 2
        result.final_score = 0.90
        result.final_path = str(mgr.get_attempt_path(1, 2))

        paths = await finalize_output(mgr, [result])
        assert len(paths) == 1

    async def test_finalize_skips_failed(self, tmp_path):
        """Test finalize skips images with failed status."""
        mgr = OutputManager(tmp_path, "Test")
        await mgr.initialize()

        result = ImageResult(image_number=1, title="Failed Image")
        result.status = "failed"

        paths = await finalize_output(mgr, [result])
        assert len(paths) == 0

    async def test_finalize_skips_no_final_attempt(self, tmp_path):
        """Test finalize skips images without final_attempt set."""
        mgr = OutputManager(tmp_path, "Test")
        await mgr.initialize()

        result = ImageResult(image_number=1, title="Incomplete")
        result.status = "complete"
        result.final_attempt = None

        paths = await finalize_output(mgr, [result])
        assert len(paths) == 0


# ---------------------------------------------------------------------------
# Summary Generation Tests
# ---------------------------------------------------------------------------


class TestSummaryGeneration:
    """Tests for OutputManager._generate_summary_content."""

    def test_summary_contains_title(self, tmp_path, sample_concept_analysis):
        """Test summary includes the analysis title."""
        mgr = OutputManager(tmp_path, "Test")

        # Create a minimal metadata mock
        metadata = MagicMock()
        metadata.timestamp = datetime(2026, 1, 18, 12, 0, 0)
        metadata.generation_id = "test-gen-id"
        metadata.results.images_planned = 2
        metadata.results.estimated_cost = "$0.50"
        metadata.config.max_iterations = 5
        metadata.config.pass_threshold = 0.85
        metadata.config.aspect_ratio = "16:9"
        metadata.config.resolution = "high"
        metadata.config.style = "professional-clean"
        metadata.config.concurrency = 3

        result1 = ImageResult(image_number=1, title="Image 1")
        result1.status = "complete"
        result1.final_attempt = 1
        result1.final_score = 0.90
        result1.final_path = "/output/image-01/final.jpg"

        content = mgr._generate_summary_content(sample_concept_analysis, metadata, [result1])

        assert "Introduction to Machine Learning" in content
        assert "Image 1" in content
        assert "90" in content

    def test_summary_handles_failed_images(self, tmp_path, sample_concept_analysis):
        """Test summary correctly shows failed images."""
        mgr = OutputManager(tmp_path, "Test")

        metadata = MagicMock()
        metadata.timestamp = datetime(2026, 1, 18, 12, 0, 0)
        metadata.generation_id = "id"
        metadata.results.images_planned = 1
        metadata.results.estimated_cost = "$0.20"
        metadata.config.max_iterations = 3
        metadata.config.pass_threshold = 0.85
        metadata.config.aspect_ratio = "16:9"
        metadata.config.resolution = "high"
        metadata.config.style = "professional-clean"
        metadata.config.concurrency = 2

        result = ImageResult(image_number=1, title="Failed Image")
        result.status = "failed"

        content = mgr._generate_summary_content(sample_concept_analysis, metadata, [result])

        assert "FAILED" in content
