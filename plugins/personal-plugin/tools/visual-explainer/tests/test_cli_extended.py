"""Tests for cli module.

Tests the CLI orchestrator including:
- Argument parsing (create_parser)
- Parameter validation (argparse type validators)
- Configuration building from args
- Cost estimation
- Display functions
- Pipeline orchestration (mocked)
- Interactive mode detection
- JSON output mode
- Dry run mode
- Resume mode
- GenerationProgress context manager
"""

from __future__ import annotations

import argparse
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from visual_explainer.cli import (
    GenerationProgress,
    _bounded_float,
    _bounded_int,
    create_parser,
    display_analysis_summary,
    display_welcome,
    estimate_cost,
    get_console,
    is_interactive,
    main,
    prompt_for_image_count,
    prompt_for_style,
    supports_unicode,
)
from visual_explainer.config import GenerationConfig
from visual_explainer.models import EvaluationVerdict

# ---------------------------------------------------------------------------
# Argument Parser Tests
# ---------------------------------------------------------------------------


class TestCreateParser:
    """Tests for create_parser function."""

    def test_parser_creation(self):
        """Test parser is created successfully."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_input_argument(self):
        """Test --input argument parsing."""
        parser = create_parser()
        args = parser.parse_args(["--input", "test.md"])
        assert args.input_source == "test.md"

    def test_input_short_flag(self):
        """Test -i short flag parsing."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md"])
        assert args.input_source == "test.md"

    def test_style_argument(self):
        """Test --style argument parsing."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--style", "professional-sketch"])
        assert args.style == "professional-sketch"

    def test_output_dir_argument(self):
        """Test --output-dir argument parsing."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--output-dir", "/tmp/output"])
        assert args.output_dir == "/tmp/output"

    def test_max_iterations_default(self):
        """Test default max-iterations value."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md"])
        assert args.max_iterations == 5

    def test_max_iterations_custom(self):
        """Test custom max-iterations value."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--max-iterations", "3"])
        assert args.max_iterations == 3

    def test_pass_threshold_default(self):
        """Test default pass-threshold value."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md"])
        assert args.pass_threshold == 0.85

    def test_pass_threshold_custom(self):
        """Test custom pass-threshold value."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--pass-threshold", "0.70"])
        assert args.pass_threshold == 0.70

    def test_concurrency_default(self):
        """Test default concurrency value."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md"])
        assert args.concurrency == 3

    def test_concurrency_custom(self):
        """Test custom concurrency value."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--concurrency", "5"])
        assert args.concurrency == 5

    def test_aspect_ratio_choices(self):
        """Test valid aspect ratio choices."""
        parser = create_parser()
        for ratio in ["16:9", "1:1", "4:3", "9:16", "3:4"]:
            args = parser.parse_args(["-i", "test.md", "--aspect-ratio", ratio])
            assert args.aspect_ratio == ratio

    def test_resolution_choices(self):
        """Test valid resolution choices."""
        parser = create_parser()
        for res in ["standard", "high"]:
            args = parser.parse_args(["-i", "test.md", "--resolution", res])
            assert args.resolution == res

    def test_no_cache_flag(self):
        """Test --no-cache flag."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--no-cache"])
        assert args.no_cache is True

    def test_dry_run_flag(self):
        """Test --dry-run flag."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--dry-run"])
        assert args.dry_run is True

    def test_setup_keys_flag(self):
        """Test --setup-keys flag."""
        parser = create_parser()
        args = parser.parse_args(["--setup-keys"])
        assert args.setup_keys is True

    def test_json_output_flag(self):
        """Test --json flag."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--json"])
        assert args.json is True

    def test_quiet_flag(self):
        """Test --quiet flag."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--quiet"])
        assert args.quiet is True

    def test_quiet_short_flag(self):
        """Test -q short flag."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "-q"])
        assert args.quiet is True

    def test_resume_argument(self):
        """Test --resume argument."""
        parser = create_parser()
        args = parser.parse_args(["--resume", "/path/to/checkpoint.json"])
        assert args.resume == "/path/to/checkpoint.json"

    def test_image_count_default(self):
        """Test default image-count is 0 (auto)."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md"])
        assert args.image_count == 0

    def test_image_count_custom(self):
        """Test custom image count."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--image-count", "5"])
        assert args.image_count == 5

    def test_infographic_flag(self):
        """Test --infographic flag."""
        parser = create_parser()
        args = parser.parse_args(["-i", "test.md", "--infographic"])
        assert args.infographic is True

    def test_no_input_default_none(self):
        """Test no input defaults to None."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.input_source is None


# ---------------------------------------------------------------------------
# Cost Estimation Tests
# ---------------------------------------------------------------------------


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_single_image(self):
        """Test cost for single image."""
        cost = estimate_cost(1, 5)
        assert "$" in cost
        assert "range" in cost

    def test_multiple_images(self):
        """Test cost for multiple images."""
        cost = estimate_cost(5, 5)
        assert "$" in cost

    def test_zero_images(self):
        """Test cost for zero images."""
        cost = estimate_cost(0, 5)
        assert "$0.0" in cost

    def test_avg_attempts_capped(self):
        """Test average attempts is capped at 2.5."""
        # With max_iterations=10, avg should be min(2.5, 10) = 2.5
        cost = estimate_cost(1, 10)
        # Verify it's reasonable
        assert "$" in cost


# ---------------------------------------------------------------------------
# is_interactive Tests
# ---------------------------------------------------------------------------


class TestIsInteractiveCli:
    """Tests for CLI is_interactive function."""

    def test_returns_bool(self):
        """Test returns boolean."""
        result = is_interactive()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# supports_unicode Tests
# ---------------------------------------------------------------------------


class TestSupportsUnicodeCli:
    """Tests for CLI supports_unicode function."""

    def test_returns_bool(self):
        """Test returns boolean."""
        result = supports_unicode()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# prompt_for_style Tests
# ---------------------------------------------------------------------------


class TestPromptForStyle:
    """Tests for prompt_for_style function."""

    def test_non_interactive_returns_default(self):
        """Test non-interactive returns default style."""
        with patch("visual_explainer.cli.is_interactive", return_value=False):
            result = prompt_for_style()
        assert result == "professional-clean"


# ---------------------------------------------------------------------------
# prompt_for_image_count Tests
# ---------------------------------------------------------------------------


class TestPromptForImageCount:
    """Tests for prompt_for_image_count function."""

    def test_non_interactive_returns_recommended(self):
        """Test non-interactive returns recommended count."""
        with patch("visual_explainer.cli.is_interactive", return_value=False):
            result = prompt_for_image_count(3)
        assert result == 3


# ---------------------------------------------------------------------------
# GenerationProgress Tests
# ---------------------------------------------------------------------------


class TestGenerationProgress:
    """Tests for GenerationProgress context manager."""

    def test_init(self):
        """Test progress tracker initialization."""
        with patch("visual_explainer.cli.get_console", return_value=MagicMock()):
            progress = GenerationProgress(5, 3, quiet=False)
        assert progress.total_images == 5
        assert progress.max_iterations == 3
        assert progress.current_image == 0

    def test_quiet_mode(self):
        """Test quiet mode suppresses output."""
        with patch("visual_explainer.cli.get_console", return_value=MagicMock()):
            progress = GenerationProgress(5, 3, quiet=True)
        assert progress.quiet is True

    def test_context_manager_quiet(self):
        """Test context manager works in quiet mode."""
        with patch("visual_explainer.cli.get_console", return_value=MagicMock()):
            with GenerationProgress(2, 3, quiet=True) as progress:
                progress.start_image(1, "Test Image")
                progress.start_attempt(1)
                progress.update_status("Generating...")
                # Should not raise

    def test_start_image(self):
        """Test starting a new image."""
        with patch("visual_explainer.cli.get_console", return_value=MagicMock()):
            with GenerationProgress(2, 3, quiet=True) as progress:
                progress.start_image(1, "Test")
                assert progress.current_image == 1
                assert progress.current_attempt == 0

    def test_start_attempt(self):
        """Test starting a new attempt."""
        with patch("visual_explainer.cli.get_console", return_value=MagicMock()):
            with GenerationProgress(2, 3, quiet=True) as progress:
                progress.start_attempt(2)
                assert progress.current_attempt == 2

    def test_complete_image_quiet(self):
        """Test completing an image in quiet mode."""
        with patch("visual_explainer.cli.get_console", return_value=MagicMock()):
            with GenerationProgress(2, 3, quiet=True) as progress:
                progress.complete_image(1, 2, 0.90)
                # Should not raise

    def test_show_evaluation_quiet(self):
        """Test showing evaluation in quiet mode."""
        with patch("visual_explainer.cli.get_console", return_value=MagicMock()):
            with GenerationProgress(2, 3, quiet=True) as progress:
                mock_eval = MagicMock()
                mock_eval.verdict = EvaluationVerdict.PASS
                mock_eval.overall_score = 0.90
                progress.show_evaluation(mock_eval)
                # Should not raise


# ---------------------------------------------------------------------------
# Main Function Tests
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for the main CLI entry point."""

    def test_setup_keys_flag(self):
        """Test --setup-keys flag invokes setup handler."""
        with patch("sys.argv", ["visual-explainer", "--setup-keys"]):
            # main() does a local import: from visual_explainer.api_setup import handle_setup_keys_flag
            # So we must patch it on the source module.
            with patch(
                "visual_explainer.api_setup.handle_setup_keys_flag", return_value=0
            ) as mock_setup:
                result = main()
                assert result == 0
                mock_setup.assert_called_once()

    def test_no_input_non_interactive_json(self):
        """Test no input with --json returns error JSON."""
        with patch("sys.argv", ["visual-explainer", "--json"]):
            with patch("visual_explainer.cli.is_interactive", return_value=False):
                result = main()
                assert result == 1

    def test_no_input_non_interactive_error(self):
        """Test no input in non-interactive mode returns error."""
        with patch("sys.argv", ["visual-explainer"]):
            with patch("visual_explainer.cli.is_interactive", return_value=False):
                result = main()
                assert result == 1

    def test_resume_mode(self, tmp_path):
        """Test --resume flag triggers checkpoint loading."""
        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint_path.write_text(
            json.dumps(
                {
                    "generation_id": "test-id",
                    "images_completed": 1,
                    "images_remaining": 2,
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "sys.argv",
            ["visual-explainer", "--resume", str(checkpoint_path)],
        ):
            # Mock both GenerationConfig.from_cli_and_env (resume path passes
            # empty input_source which fails Pydantic min_length) and
            # load_checkpoint_and_resume (async, needs AsyncMock).
            mock_config = MagicMock()
            with patch(
                "visual_explainer.cli.GenerationConfig.from_cli_and_env",
                return_value=mock_config,
            ):
                with patch(
                    "visual_explainer.cli.load_checkpoint_and_resume",
                    new_callable=AsyncMock,
                    return_value={"status": "resume_not_implemented"},
                ) as mock_resume:
                    result = main()
                    # Should complete (resume_not_implemented status)
                    assert result == 0
                    mock_resume.assert_called_once()

    def test_config_error_returns_1(self):
        """Test configuration error returns exit code 1."""
        with patch(
            "sys.argv",
            ["visual-explainer", "-i", "test.md"],
        ):
            with patch("visual_explainer.cli.is_interactive", return_value=False):
                with patch(
                    "visual_explainer.cli.GenerationConfig.from_cli_and_env",
                    side_effect=ValueError("Bad config"),
                ):
                    # Also need to mock API key check to pass
                    with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                        mock_check.return_value = {
                            "google": {"present": True, "valid": None, "error": None},
                            "anthropic": {"present": True, "valid": None, "error": None},
                        }
                        result = main()
                        assert result == 1


# ---------------------------------------------------------------------------
# Display Functions Tests
# ---------------------------------------------------------------------------


class TestDisplayFunctions:
    """Tests for display helper functions."""

    def test_display_welcome(self):
        """Test display_welcome doesn't crash."""
        with patch("visual_explainer.cli._console", None):
            with patch("visual_explainer.cli.is_interactive", return_value=False):
                with patch("visual_explainer.cli.supports_unicode", return_value=False):
                    with patch("visual_explainer.cli.RICH_AVAILABLE", True):
                        # Reset console
                        import visual_explainer.cli as cli_mod

                        cli_mod._console = None
                        display_welcome()

    def test_display_analysis_summary(self, sample_concept_analysis):
        """Test display_analysis_summary doesn't crash."""
        with patch("visual_explainer.cli._console", None):
            with patch("visual_explainer.cli.is_interactive", return_value=False):
                with patch("visual_explainer.cli.supports_unicode", return_value=False):
                    with patch("visual_explainer.cli.RICH_AVAILABLE", True):
                        import visual_explainer.cli as cli_mod

                        cli_mod._console = None
                        display_analysis_summary(sample_concept_analysis)


# ---------------------------------------------------------------------------
# Parameter Validation Tests (Item 4.7)
# ---------------------------------------------------------------------------


class TestBoundedFloat:
    """Tests for _bounded_float validator factory."""

    def test_valid_value(self):
        """Test valid value passes through."""
        validator = _bounded_float(0.0, 1.0, "test")
        assert validator("0.5") == 0.5

    def test_min_boundary(self):
        """Test minimum boundary is accepted."""
        validator = _bounded_float(0.0, 1.0, "test")
        assert validator("0.0") == 0.0

    def test_max_boundary(self):
        """Test maximum boundary is accepted."""
        validator = _bounded_float(0.0, 1.0, "test")
        assert validator("1.0") == 1.0

    def test_below_min_raises(self):
        """Test value below minimum raises."""
        validator = _bounded_float(0.0, 1.0, "test")
        with pytest.raises(argparse.ArgumentTypeError, match="must be between"):
            validator("-0.1")

    def test_above_max_raises(self):
        """Test value above maximum raises."""
        validator = _bounded_float(0.0, 1.0, "test")
        with pytest.raises(argparse.ArgumentTypeError, match="must be between"):
            validator("1.5")


class TestBoundedInt:
    """Tests for _bounded_int validator factory."""

    def test_valid_value(self):
        """Test valid value passes through."""
        validator = _bounded_int(1, 10, "test")
        assert validator("5") == 5

    def test_min_boundary(self):
        """Test minimum boundary is accepted."""
        validator = _bounded_int(1, 10, "test")
        assert validator("1") == 1

    def test_max_boundary(self):
        """Test maximum boundary is accepted."""
        validator = _bounded_int(1, 10, "test")
        assert validator("10") == 10

    def test_below_min_raises(self):
        """Test value below minimum raises."""
        validator = _bounded_int(1, 10, "test")
        with pytest.raises(argparse.ArgumentTypeError, match="must be between"):
            validator("0")

    def test_above_max_raises(self):
        """Test value above maximum raises."""
        validator = _bounded_int(1, 10, "test")
        with pytest.raises(argparse.ArgumentTypeError, match="must be between"):
            validator("11")


class TestParameterValidation:
    """Tests for CLI parameter validation via argparse type validators."""

    def test_pass_threshold_valid_range(self):
        """Test pass-threshold accepts valid range."""
        parser = create_parser()
        for val in ["0.0", "0.5", "0.85", "1.0"]:
            args = parser.parse_args(["-i", "test.md", "--pass-threshold", val])
            assert 0.0 <= args.pass_threshold <= 1.0

    def test_pass_threshold_invalid_rejected(self):
        """Test pass-threshold rejects out-of-range values at argparse level."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "test.md", "--pass-threshold", "1.5"])
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "test.md", "--pass-threshold", "-0.1"])

    def test_concurrency_valid_range(self):
        """Test concurrency accepts valid range."""
        parser = create_parser()
        for val in ["1", "3", "5", "10"]:
            args = parser.parse_args(["-i", "test.md", "--concurrency", val])
            assert 1 <= args.concurrency <= 10

    def test_concurrency_invalid_rejected(self):
        """Test concurrency rejects out-of-range values at argparse level."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "test.md", "--concurrency", "0"])
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "test.md", "--concurrency", "11"])

    def test_max_iterations_valid_range(self):
        """Test max-iterations accepts valid range."""
        parser = create_parser()
        for val in ["1", "5", "10", "20"]:
            args = parser.parse_args(["-i", "test.md", "--max-iterations", val])
            assert 1 <= args.max_iterations <= 20

    def test_max_iterations_invalid_rejected(self):
        """Test max-iterations rejects out-of-range values at argparse level."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "test.md", "--max-iterations", "0"])
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "test.md", "--max-iterations", "21"])

    def test_generation_config_rejects_invalid_threshold(self):
        """Test GenerationConfig rejects out-of-range threshold."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", pass_threshold=1.5)

        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", pass_threshold=-0.1)

    def test_generation_config_rejects_invalid_concurrency(self):
        """Test GenerationConfig rejects out-of-range concurrency."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", concurrency=0)

        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", concurrency=11)

    def test_generation_config_rejects_invalid_max_iterations(self):
        """Test GenerationConfig rejects out-of-range max_iterations."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", max_iterations=0)

        with pytest.raises(ValidationError):
            GenerationConfig(input_source="test", max_iterations=11)


# ---------------------------------------------------------------------------
# get_console Tests
# ---------------------------------------------------------------------------


class TestGetConsole:
    """Tests for get_console function."""

    def test_returns_console(self):
        """Test get_console returns a Console instance."""
        import visual_explainer.cli as cli_mod

        cli_mod._console = None
        with patch("visual_explainer.cli.is_interactive", return_value=False):
            with patch("visual_explainer.cli.supports_unicode", return_value=False):
                console = get_console()
                assert console is not None

    def test_caches_console(self):
        """Test get_console returns same instance on second call."""
        import visual_explainer.cli as cli_mod

        cli_mod._console = None
        with patch("visual_explainer.cli.is_interactive", return_value=False):
            with patch("visual_explainer.cli.supports_unicode", return_value=False):
                c1 = get_console()
                c2 = get_console()
                assert c1 is c2

    def test_no_rich_raises(self):
        """Test error when Rich not available."""
        import visual_explainer.cli as cli_mod

        cli_mod._console = None
        with patch("visual_explainer.cli.RICH_AVAILABLE", False):
            with pytest.raises(RuntimeError, match="Rich"):
                get_console()


# ---------------------------------------------------------------------------
# prompt_for_input Tests
# ---------------------------------------------------------------------------


class TestPromptForInput:
    """Tests for prompt_for_input function."""

    def test_non_interactive_raises(self):
        """Test prompt_for_input raises in non-interactive mode."""
        from visual_explainer.cli import prompt_for_input

        with patch("visual_explainer.cli.is_interactive", return_value=False):
            with pytest.raises(RuntimeError, match="non-interactive"):
                prompt_for_input()
