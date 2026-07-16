"""Tests for the currently-uncovered second half of ``visual_explainer.cli.main()``.

``tests/test_cli_extended.py`` already covers: ``--setup-keys``, missing/no-input
error paths, ``--resume``, and the non-JSON configuration-error path. This file
focuses on what remains uncovered in ``main()``:

- The normal (non-resume) run that builds a ``GenerationConfig`` and dispatches
  to ``run_generation_pipeline`` (JSON and non-JSON output modes).
- The ``--dry-run`` flag flowing through to the pipeline call.
- The API-key-check branches taken when input is provided (interactive check
  failure, non-interactive missing-key detection).
- The JSON-mode configuration-error branch (as opposed to the non-JSON one
  already covered in test_cli_extended.py).
- Style auto-selection (interactive prompt vs. default fallback).
- KeyboardInterrupt and generic-exception handling around the pipeline call,
  in both JSON and Rich/non-Rich console output modes.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

from visual_explainer.cli import main

# ---------------------------------------------------------------------------
# Normal run: dispatch to run_generation_pipeline
# ---------------------------------------------------------------------------


class TestMainNormalRunDispatch:
    """Tests for the normal (non-resume, non-setup-keys) run() dispatch."""

    def test_json_mode_dispatches_pipeline_with_config(self):
        """--json bypasses interactive key checks and dispatches to the pipeline."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text about neural networks", "--json"],
        ):
            mock_result = {"status": "complete", "images_generated": 2}
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                return_value=mock_result,
            ) as mock_pipeline:
                result = main()

        assert result == 0
        mock_pipeline.assert_called_once()
        call_kwargs = mock_pipeline.call_args.kwargs
        assert call_kwargs["config"].input_source == "Some text about neural networks"
        # No --style flag given and JSON mode never triggers the interactive
        # style prompt, so it must fall back to the documented default.
        assert call_kwargs["style_name"] == "professional-clean"
        assert call_kwargs["json_output"] is True
        assert call_kwargs["quiet"] is False
        assert call_kwargs["infographic_mode"] is False

    def test_json_mode_prints_result_json(self, capsys):
        """--json prints the pipeline result dict as JSON to stdout."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--json"],
        ):
            mock_result = {"status": "complete", "images_generated": 1}
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        printed = json.loads(captured.out)
        assert printed == mock_result

    def test_pipeline_incomplete_status_returns_1(self):
        """A non-complete/dry_run status from the pipeline is treated as failure."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--json"],
        ):
            mock_result = {"status": "error", "error": "something went wrong"}
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                result = main()

        assert result == 1

    def test_infographic_flag_passed_through(self):
        """--infographic is forwarded to run_generation_pipeline."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--json", "--infographic"],
        ):
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                return_value={"status": "complete"},
            ) as mock_pipeline:
                main()

        assert mock_pipeline.call_args.kwargs["infographic_mode"] is True

    def test_explicit_style_bypasses_prompt(self):
        """An explicit --style is forwarded and no interactive prompt is needed."""
        with patch(
            "sys.argv",
            [
                "visual-explainer",
                "--input",
                "Some text",
                "--json",
                "--style",
                "professional-sketch",
            ],
        ):
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                return_value={"status": "complete"},
            ) as mock_pipeline:
                main()

        assert mock_pipeline.call_args.kwargs["style_name"] == "professional-sketch"

    def test_non_json_quiet_success_no_console_print(self, capsys):
        """Non-JSON + --quiet: keys pre-verified, pipeline dispatched, no JSON print."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--quiet"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": True, "valid": None, "error": None},
                        "anthropic": {"present": True, "valid": None, "error": None},
                    }
                    with patch(
                        "visual_explainer.cli.run_generation_pipeline",
                        new_callable=AsyncMock,
                        return_value={"status": "complete"},
                    ) as mock_pipeline:
                        result = main()

        assert result == 0
        mock_pipeline.assert_called_once()
        assert mock_pipeline.call_args.kwargs["quiet"] is True
        # Non-JSON mode never prints the JSON result blob.
        captured = capsys.readouterr()
        assert captured.out.strip() == ""


# ---------------------------------------------------------------------------
# --dry-run
# ---------------------------------------------------------------------------


class TestMainDryRun:
    """Tests for --dry-run flowing through main()'s dispatch."""

    def test_dry_run_config_flag_set_and_pipeline_called(self):
        """--dry-run produces a config with dry_run=True and still calls the pipeline."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--dry-run", "--json"],
        ):
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                return_value={"status": "dry_run"},
            ) as mock_pipeline:
                result = main()

        assert result == 0
        mock_pipeline.assert_called_once()
        assert mock_pipeline.call_args.kwargs["config"].dry_run is True

    def test_dry_run_status_counts_as_success(self):
        """The 'dry_run' status returned by the pipeline is a success exit code."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--dry-run", "--quiet"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": True, "valid": None, "error": None},
                        "anthropic": {"present": True, "valid": None, "error": None},
                    }
                    with patch(
                        "visual_explainer.cli.run_generation_pipeline",
                        new_callable=AsyncMock,
                        return_value={"status": "dry_run"},
                    ):
                        result = main()

        assert result == 0


# ---------------------------------------------------------------------------
# API key check branches when input is provided
# ---------------------------------------------------------------------------


class TestMainApiKeyChecksWithInput:
    """Covers the interactive-check and non-interactive-check branches."""

    def test_interactive_key_check_fails_returns_1(self):
        """Interactive mode + failed key check aborts before building config."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch(
                    "visual_explainer.api_setup.check_keys_and_prompt_if_missing",
                    return_value=False,
                ):
                    result = main()

        assert result == 1

    def test_interactive_key_check_passes_proceeds_to_pipeline(self):
        """Interactive mode + successful key check proceeds to the pipeline."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--style", "professional-clean"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch(
                    "visual_explainer.api_setup.check_keys_and_prompt_if_missing",
                    return_value=True,
                ):
                    with patch(
                        "visual_explainer.cli.run_generation_pipeline",
                        new_callable=AsyncMock,
                        return_value={"status": "complete"},
                    ) as mock_pipeline:
                        result = main()

        assert result == 0
        mock_pipeline.assert_called_once()

    def test_non_interactive_missing_both_keys_returns_1(self, capsys):
        """Non-interactive, non-JSON mode with both keys missing reports and exits 1."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": False, "valid": None, "error": None},
                        "anthropic": {"present": False, "valid": None, "error": None},
                    }
                    result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "GOOGLE_API_KEY" in captured.out
        assert "ANTHROPIC_API_KEY" in captured.out

    def test_non_interactive_missing_one_key_returns_1(self, capsys):
        """Only the Anthropic key missing is still reported and treated as failure."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": True, "valid": None, "error": None},
                        "anthropic": {"present": False, "valid": None, "error": None},
                    }
                    result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "ANTHROPIC_API_KEY" in captured.out
        assert "GOOGLE_API_KEY" not in captured.out

    def test_non_interactive_missing_only_google_key_returns_1(self, capsys):
        """Only the Google key missing exercises the opposite missing-list arc."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": False, "valid": None, "error": None},
                        "anthropic": {"present": True, "valid": None, "error": None},
                    }
                    result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "GOOGLE_API_KEY" in captured.out
        assert "ANTHROPIC_API_KEY" not in captured.out


# ---------------------------------------------------------------------------
# Interactive mode with no input provided (distinct from the non-interactive
# no-input error path already covered in test_cli_extended.py)
# ---------------------------------------------------------------------------


class TestMainInteractiveNoInput:
    """Covers args.input_source is None combined with an interactive terminal.

    test_cli_extended.py only exercises the non-interactive no-input branch
    (is_interactive() == False). These tests drive the sibling branch where
    is_interactive() == True, which has its own Rich-availability check,
    welcome banner, key-setup prompt, and free-text input prompt.
    """

    def test_interactive_no_input_without_rich_returns_1(self, capsys):
        """Interactive + no input + Rich unavailable: clear error, no prompt attempted."""
        with patch("sys.argv", ["visual-explainer"]):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch("visual_explainer.terminal.RICH_AVAILABLE", False):
                    result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Rich" in captured.out

    def test_interactive_no_input_key_setup_declined_returns_1(self):
        """Interactive + no input + Rich available + key setup declined: abort."""
        with patch("sys.argv", ["visual-explainer"]):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch("visual_explainer.terminal.RICH_AVAILABLE", True):
                    with patch("visual_explainer.cli.display_welcome"):
                        with patch(
                            "visual_explainer.api_setup.check_keys_and_prompt_if_missing",
                            return_value=False,
                        ):
                            result = main()

        assert result == 1

    def test_interactive_no_input_blank_prompt_returns_1(self, capsys):
        """Interactive + no input + keys OK + user enters blank text: exit cleanly."""
        with patch("sys.argv", ["visual-explainer"]):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch("visual_explainer.terminal.RICH_AVAILABLE", True):
                    with patch("visual_explainer.cli.display_welcome"):
                        with patch(
                            "visual_explainer.api_setup.check_keys_and_prompt_if_missing",
                            return_value=True,
                        ):
                            with patch(
                                "visual_explainer.cli.prompt_for_input",
                                return_value="   ",
                            ):
                                result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "No input provided" in captured.out

    def test_interactive_no_input_prompted_text_dispatches_pipeline(self):
        """Interactive + no input + keys OK + user enters text: proceeds to pipeline."""
        with patch("sys.argv", ["visual-explainer"]):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch("visual_explainer.terminal.RICH_AVAILABLE", True):
                    with patch("visual_explainer.cli.display_welcome"):
                        with patch(
                            "visual_explainer.api_setup.check_keys_and_prompt_if_missing",
                            return_value=True,
                        ):
                            with patch(
                                "visual_explainer.cli.prompt_for_input",
                                return_value="Prompted input text",
                            ):
                                with patch(
                                    "visual_explainer.cli.prompt_for_style",
                                    return_value="professional-clean",
                                ):
                                    with patch(
                                        "visual_explainer.cli.run_generation_pipeline",
                                        new_callable=AsyncMock,
                                        return_value={"status": "complete"},
                                    ) as mock_pipeline:
                                        result = main()

        assert result == 0
        mock_pipeline.assert_called_once()
        assert mock_pipeline.call_args.kwargs["config"].input_source == "Prompted input text"


# ---------------------------------------------------------------------------
# Configuration-error branch in JSON mode (non-JSON already covered elsewhere)
# ---------------------------------------------------------------------------


class TestMainConfigErrorJsonMode:
    """Covers the --json variant of the config-build error branch."""

    def test_config_error_json_mode_prints_json_error(self, capsys):
        """--json config-build failure prints a JSON error blob and returns 1."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--json"],
        ):
            with patch(
                "visual_explainer.cli.GenerationConfig.from_cli_and_env",
                side_effect=ValueError("Bad config"),
            ):
                result = main()

        assert result == 1
        captured = capsys.readouterr()
        printed = json.loads(captured.out)
        assert printed == {"error": "Bad config"}

    def test_config_error_non_json_interactive_mode_prints_plain_error(self, capsys):
        """Non-JSON config-build failure reached via the interactive key-check arc.

        test_cli_extended.py's non-JSON config-error test goes through the
        non-interactive elif branch; this drives the same print via the
        interactive `if` branch instead, covering a distinct arc into the
        shared error-formatting line.
        """
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch(
                    "visual_explainer.api_setup.check_keys_and_prompt_if_missing",
                    return_value=True,
                ):
                    with patch(
                        "visual_explainer.cli.GenerationConfig.from_cli_and_env",
                        side_effect=ValueError("Bad config"),
                    ):
                        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Configuration error: Bad config" in captured.out


# ---------------------------------------------------------------------------
# Style auto-selection
# ---------------------------------------------------------------------------


class TestMainStyleSelection:
    """Covers the interactive style-prompt branch and its fallback."""

    def test_interactive_rich_prompts_for_style(self):
        """No --style, non-quiet, non-JSON, Rich available, interactive: prompts."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=True):
                with patch("visual_explainer.terminal.RICH_AVAILABLE", True):
                    with patch(
                        "visual_explainer.api_setup.check_keys_and_prompt_if_missing",
                        return_value=True,
                    ):
                        with patch(
                            "visual_explainer.cli.prompt_for_style",
                            return_value="professional-sketch",
                        ) as mock_prompt:
                            with patch(
                                "visual_explainer.cli.run_generation_pipeline",
                                new_callable=AsyncMock,
                                return_value={"status": "complete"},
                            ) as mock_pipeline:
                                result = main()

        assert result == 0
        mock_prompt.assert_called_once()
        assert mock_pipeline.call_args.kwargs["style_name"] == "professional-sketch"

    def test_non_interactive_falls_back_to_default_style(self):
        """No --style, non-interactive: no prompt, defaults to professional-clean."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--quiet"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": True, "valid": None, "error": None},
                        "anthropic": {"present": True, "valid": None, "error": None},
                    }
                    with patch("visual_explainer.cli.prompt_for_style") as mock_prompt:
                        with patch(
                            "visual_explainer.cli.run_generation_pipeline",
                            new_callable=AsyncMock,
                            return_value={"status": "complete"},
                        ) as mock_pipeline:
                            result = main()

        assert result == 0
        mock_prompt.assert_not_called()
        assert mock_pipeline.call_args.kwargs["style_name"] == "professional-clean"


# ---------------------------------------------------------------------------
# Exception handling around the pipeline call
# ---------------------------------------------------------------------------


class TestMainPipelineExceptionHandling:
    """Covers KeyboardInterrupt and generic-exception branches around the pipeline."""

    def test_keyboard_interrupt_json_mode_returns_130(self, capsys):
        """KeyboardInterrupt during the pipeline returns 130 and prints nothing extra in JSON mode."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--json"],
        ):
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                side_effect=KeyboardInterrupt(),
            ):
                result = main()

        assert result == 130
        captured = capsys.readouterr()
        assert "interrupted" not in captured.out.lower()

    def test_keyboard_interrupt_non_json_mode_prints_message(self, capsys):
        """KeyboardInterrupt during the pipeline prints an interruption message in non-JSON mode."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--quiet"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": True, "valid": None, "error": None},
                        "anthropic": {"present": True, "valid": None, "error": None},
                    }
                    with patch(
                        "visual_explainer.cli.run_generation_pipeline",
                        new_callable=AsyncMock,
                        side_effect=KeyboardInterrupt(),
                    ):
                        result = main()

        assert result == 130
        captured = capsys.readouterr()
        assert "interrupted" in captured.out.lower()

    def test_generic_exception_json_mode_prints_json_error(self, capsys):
        """A generic exception during the pipeline is reported as a JSON error blob."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--json"],
        ):
            with patch(
                "visual_explainer.cli.run_generation_pipeline",
                new_callable=AsyncMock,
                side_effect=RuntimeError("pipeline exploded"),
            ):
                result = main()

        assert result == 1
        captured = capsys.readouterr()
        printed = json.loads(captured.out)
        assert printed == {"error": "pipeline exploded"}

    def test_generic_exception_non_json_rich_console_prints_error(self):
        """Non-JSON + Rich available: the exception is printed via the Rich console."""
        mock_console = MagicMock()
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--quiet"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": True, "valid": None, "error": None},
                        "anthropic": {"present": True, "valid": None, "error": None},
                    }
                    with patch("visual_explainer.terminal.RICH_AVAILABLE", True):
                        with patch(
                            "visual_explainer.terminal.get_console",
                            return_value=mock_console,
                        ):
                            with patch(
                                "visual_explainer.cli.run_generation_pipeline",
                                new_callable=AsyncMock,
                                side_effect=RuntimeError("pipeline exploded"),
                            ):
                                result = main()

        assert result == 1
        mock_console.print.assert_called_once()
        printed_arg = mock_console.print.call_args.args[0]
        assert "pipeline exploded" in printed_arg

    def test_generic_exception_non_json_no_rich_plain_print(self, capsys):
        """Non-JSON + Rich unavailable: the exception falls back to a plain print."""
        with patch(
            "sys.argv",
            ["visual-explainer", "--input", "Some text", "--quiet"],
        ):
            with patch("visual_explainer.terminal.is_interactive", return_value=False):
                with patch("visual_explainer.api_setup.check_api_keys") as mock_check:
                    mock_check.return_value = {
                        "google": {"present": True, "valid": None, "error": None},
                        "anthropic": {"present": True, "valid": None, "error": None},
                    }
                    with patch("visual_explainer.terminal.RICH_AVAILABLE", False):
                        with patch(
                            "visual_explainer.cli.run_generation_pipeline",
                            new_callable=AsyncMock,
                            side_effect=RuntimeError("pipeline exploded"),
                        ):
                            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: pipeline exploded" in captured.out
