"""Tests for the visual_explainer.reporting module.

Covers all rendering/reporting surfaces: the welcome banner, analysis
summary (including infographic-mode page plans), the dry-run plan, the
completion summary, the pure cost estimator, the ``GenerationProgress``
context manager, and the three interactive ``prompt_for_*`` helpers.

Rich console output is always mocked via ``visual_explainer.terminal.get_console``
so no real terminal I/O occurs. Interactive prompts are exercised by patching
``visual_explainer.terminal.is_interactive`` and ``reporting.Prompt.ask`` (or
``builtins.input`` for the free-text paste path).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from visual_explainer import reporting
from visual_explainer.models import (
    ContentType,
    ImageResult,
    PagePlan,
    PageRecommendation,
    PageType,
)

# ---------------------------------------------------------------------------
# display_welcome
# ---------------------------------------------------------------------------


class TestDisplayWelcome:
    """Tests for display_welcome."""

    def test_prints_banner_panel_with_expected_text(self):
        """Welcome banner prints a cyan-bordered Panel containing the title."""
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_welcome()

        # Two blank console.print() calls plus the panel itself.
        assert mock_console.print.call_count == 3
        panel_call = mock_console.print.call_args_list[1]
        panel = panel_call.args[0]
        assert isinstance(panel, reporting.Panel)
        assert "Visual Concept Explainer" in panel.renderable
        assert panel.border_style == "cyan"


# ---------------------------------------------------------------------------
# display_analysis_summary
# ---------------------------------------------------------------------------


class TestDisplayAnalysisSummary:
    """Tests for display_analysis_summary."""

    def test_default_mode_shows_summary_fields(self, sample_concept_analysis):
        """Non-infographic mode prints a panel with title, word count, concepts."""
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_analysis_summary(sample_concept_analysis)

        panel_calls = [
            c
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], reporting.Panel)
        ]
        assert len(panel_calls) == 1
        panel = panel_calls[0].args[0]
        assert "Introduction to Machine Learning" in panel.renderable
        assert "500 words" in panel.renderable
        assert "3 concepts identified" in panel.renderable
        assert "Technical professionals" in panel.renderable
        assert panel.title == "[bold]Concept Analysis[/bold]"

    def test_default_mode_shows_concept_flow_with_relationship_arrow(self, sample_concept_analysis):
        """Concept flow lists each concept name and a relationship arrow line."""
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_analysis_summary(sample_concept_analysis)

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Neural Networks" in printed_text
        assert "Training Data" in printed_text
        assert "Model Output" in printed_text
        # First concept (id=1) has an outgoing flow -> depends_on arrow printed.
        assert "[depends_on]" in printed_text

    def test_infographic_mode_without_page_recommendation_falls_back(self, sample_concept_analysis):
        """infographic_mode=True with no page_recommendation still shows concept flow."""
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_analysis_summary(sample_concept_analysis, infographic_mode=True)

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Concept Flow:" in printed_text
        assert "Infographic Page Plan:" not in printed_text

    def test_infographic_mode_with_page_recommendation_shows_pages(self, sample_concept_analysis):
        """infographic_mode=True with a page_recommendation prints the page plan."""
        page = PagePlan(
            page_number=1,
            page_type=PageType.HERO_SUMMARY,
            title="Overview Page",
            content_focus="A short focus statement.",
            concepts_covered=[1, 2],
        )
        analysis = sample_concept_analysis.model_copy(
            update={
                "page_recommendation": PageRecommendation(
                    page_count=1,
                    rationale="One page suffices.",
                    pages=[page],
                ),
                "content_types_detected": [ContentType.PROCESS, ContentType.STATISTICS],
            }
        )

        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_analysis_summary(analysis, infographic_mode=True)

        # The page-count/content-types summary is embedded in the Panel's
        # renderable text, not a standalone console.print(str) call.
        panel = next(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], reporting.Panel)
        )
        assert "Infographic Pages:" in panel.renderable
        assert "1 pages recommended" in panel.renderable
        assert "process, statistics" in panel.renderable

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Infographic Page Plan:" in printed_text
        assert "Page 1:" in printed_text
        assert "Overview Page" in printed_text
        assert "hero_summary" in printed_text
        assert "A short focus statement." in printed_text
        assert "[1, 2]" in printed_text

    def test_infographic_mode_truncates_long_content_focus(self, sample_concept_analysis):
        """content_focus longer than 60 chars is truncated with an ellipsis."""
        long_focus = "x" * 80
        page = PagePlan(
            page_number=1,
            page_type=PageType.DATA_EVIDENCE,
            title="Data Page",
            content_focus=long_focus,
        )
        analysis = sample_concept_analysis.model_copy(
            update={
                "page_recommendation": PageRecommendation(
                    page_count=1,
                    rationale="rationale",
                    pages=[page],
                ),
            }
        )

        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_analysis_summary(analysis, infographic_mode=True)

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert f"Focus: {long_focus[:60]}...[/dim]" in printed_text
        assert long_focus not in printed_text  # full untruncated string absent

    def test_infographic_mode_shows_compression_warnings(self, sample_concept_analysis):
        """compression_warnings are printed under a yellow warning heading."""
        page = PagePlan(
            page_number=1,
            page_type=PageType.HERO_SUMMARY,
            title="Overview",
            content_focus="Focus text",
        )
        analysis = sample_concept_analysis.model_copy(
            update={
                "page_recommendation": PageRecommendation(
                    page_count=1,
                    rationale="rationale",
                    pages=[page],
                    compression_warnings=["Section 3 heavily condensed"],
                ),
            }
        )

        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_analysis_summary(analysis, infographic_mode=True)

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Compression Warnings:" in printed_text
        assert "Section 3 heavily condensed" in printed_text


# ---------------------------------------------------------------------------
# prompt_for_style
# ---------------------------------------------------------------------------


class TestPromptForStyle:
    """Tests for prompt_for_style."""

    def test_non_interactive_returns_default_without_prompting(self):
        with patch("visual_explainer.terminal.is_interactive", return_value=False):
            result = reporting.prompt_for_style()
        assert result == "professional-clean"

    def test_interactive_choice_1_returns_professional_clean(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", return_value="1") as mock_ask,
        ):
            result = reporting.prompt_for_style()
        assert result == "professional-clean"
        mock_ask.assert_called_once_with("Select style", choices=["1", "2", "3", "4"], default="4")

    def test_interactive_choice_2_returns_professional_sketch(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", return_value="2"),
        ):
            result = reporting.prompt_for_style()
        assert result == "professional-sketch"

    def test_interactive_choice_3_returns_stripped_custom_path(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", side_effect=["3", "  ./my-style.json  "]),
        ):
            result = reporting.prompt_for_style()
        assert result == "./my-style.json"

    def test_interactive_choice_4_returns_none(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", return_value="4"),
        ):
            result = reporting.prompt_for_style()
        assert result is None


# ---------------------------------------------------------------------------
# prompt_for_image_count
# ---------------------------------------------------------------------------


class TestPromptForImageCount:
    """Tests for prompt_for_image_count."""

    def test_non_interactive_returns_recommended(self):
        with patch("visual_explainer.terminal.is_interactive", return_value=False):
            result = reporting.prompt_for_image_count(4)
        assert result == 4

    def test_interactive_choice_1_returns_recommended(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", return_value="1"),
        ):
            result = reporting.prompt_for_image_count(5)
        assert result == 5

    def test_interactive_choice_2_returns_fewer_images(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", side_effect=["2", "3"]),
        ):
            result = reporting.prompt_for_image_count(5)
        assert result == 3

    def test_interactive_choice_2_enforces_minimum_of_one(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", side_effect=["2", "0"]),
        ):
            result = reporting.prompt_for_image_count(1)
        assert result == 1

    def test_interactive_choice_3_returns_more_images(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", side_effect=["3", "7"]),
        ):
            result = reporting.prompt_for_image_count(5)
        assert result == 7

    def test_interactive_choice_3_enforces_maximum_of_20(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", side_effect=["3", "99"]),
        ):
            result = reporting.prompt_for_image_count(5)
        assert result == 20


# ---------------------------------------------------------------------------
# prompt_for_input
# ---------------------------------------------------------------------------


class TestPromptForInput:
    """Tests for prompt_for_input."""

    def test_non_interactive_raises_runtime_error(self):
        with patch("visual_explainer.terminal.is_interactive", return_value=False):
            with pytest.raises(RuntimeError, match="non-interactive"):
                reporting.prompt_for_input()

    def test_interactive_file_path(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", side_effect=["2", "./docs/concept.md"]),
        ):
            result = reporting.prompt_for_input()
        assert result == "./docs/concept.md"

    def test_interactive_url(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", side_effect=["3", "https://example.com/doc"]),
        ):
            result = reporting.prompt_for_input()
        assert result == "https://example.com/doc"

    def test_interactive_pasted_text_returns_joined_lines(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", return_value="1"),
            patch("builtins.input", side_effect=["Hello", "World", "", ""]),
        ):
            result = reporting.prompt_for_input()
        assert result == "Hello\nWorld"

    def test_interactive_pasted_text_immediate_double_blank_returns_empty(self):
        with (
            patch("visual_explainer.terminal.is_interactive", return_value=True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch.object(reporting.Prompt, "ask", return_value="1"),
            patch("builtins.input", side_effect=["", ""]),
        ):
            result = reporting.prompt_for_input()
        assert result == ""


# ---------------------------------------------------------------------------
# display_dry_run_plan
# ---------------------------------------------------------------------------


class TestDisplayDryRunPlan:
    """Tests for display_dry_run_plan."""

    def test_prints_config_table_and_images_table_and_cost(
        self, sample_concept_analysis, sample_image_prompt, sample_generation_config
    ):
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_dry_run_plan(
                sample_concept_analysis,
                [sample_image_prompt],
                sample_generation_config,
                "professional-clean",
            )

        table_calls = [
            c
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], reporting.Table)
        ]
        assert len(table_calls) == 2
        config_table, images_table = table_calls[0].args[0], table_calls[1].args[0]
        assert config_table.title == "Configuration"
        assert config_table.row_count == 7
        assert images_table.title == "Planned Images (1 total)"
        assert images_table.row_count == 1

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Estimated Cost:" in printed_text
        assert reporting.estimate_cost(1, sample_generation_config.max_iterations) in printed_text

    def test_short_input_source_not_truncated(
        self, sample_concept_analysis, sample_image_prompt, sample_generation_config
    ):
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_dry_run_plan(
                sample_concept_analysis,
                [sample_image_prompt],
                sample_generation_config,
                "professional-clean",
            )

        config_table = next(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args
            and isinstance(c.args[0], reporting.Table)
            and c.args[0].title == "Configuration"
        )
        input_row_value = config_table.columns[1]._cells[0]
        assert input_row_value == sample_generation_config.input_source
        assert "..." not in input_row_value

    def test_long_input_source_truncated(
        self, sample_concept_analysis, sample_image_prompt, sample_generation_config
    ):
        long_config = sample_generation_config.model_copy(update={"input_source": "y" * 80})
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_dry_run_plan(
                sample_concept_analysis,
                [sample_image_prompt],
                long_config,
                "professional-clean",
            )

        config_table = next(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args
            and isinstance(c.args[0], reporting.Table)
            and c.args[0].title == "Configuration"
        )
        input_row_value = config_table.columns[1]._cells[0]
        assert input_row_value == "y" * 60 + "..."


# ---------------------------------------------------------------------------
# estimate_cost (pure function)
# ---------------------------------------------------------------------------


class TestEstimateCost:
    """Tests for estimate_cost — a pure function, asserted on exact values."""

    def test_known_values_single_image(self):
        # avg_attempts = min(2.5, 3) = 2.5
        # gemini = 1 * 2.5 * 0.10 = 0.25
        # claude_analysis = 0.02; claude_eval = 1 * 2.5 * 0.03 = 0.075
        # total = 0.25 + 0.02 + 0.075 = 0.345 -> "$0.34" (banker's/round-half-even via f-string)
        result = reporting.estimate_cost(1, 3)
        total = 1 * min(2.5, 3) * 0.10 + 0.02 + 1 * min(2.5, 3) * 0.03
        expected = f"${total:.2f} (range: ${total * 0.5:.2f} - ${total * 2:.2f})"
        assert result == expected

    def test_known_values_multiple_images(self):
        result = reporting.estimate_cost(5, 5)
        avg_attempts = min(2.5, 5)
        total = 5 * avg_attempts * 0.10 + 0.02 + 5 * avg_attempts * 0.03
        expected = f"${total:.2f} (range: ${total * 0.5:.2f} - ${total * 2:.2f})"
        assert result == expected

    def test_zero_images_only_analysis_cost(self):
        result = reporting.estimate_cost(0, 5)
        assert result == "$0.02 (range: $0.01 - $0.04)"

    def test_avg_attempts_capped_at_two_point_five(self):
        # max_iterations=10 should behave identically to max_iterations >= 2.5-cap
        result_10 = reporting.estimate_cost(2, 10)
        result_3 = reporting.estimate_cost(2, 3)
        # Both cap avg_attempts at 2.5 when max_iterations >= 2.5.
        assert result_10 == result_3

    def test_result_format_contains_dollar_sign_and_range(self):
        result = reporting.estimate_cost(3, 4)
        assert result.startswith("$")
        assert "range:" in result
        assert result.count("$") == 3


# ---------------------------------------------------------------------------
# GenerationProgress
# ---------------------------------------------------------------------------


class TestGenerationProgressInit:
    """Tests for GenerationProgress.__init__."""

    def test_rich_available_stores_console_and_state(self):
        mock_console = MagicMock()
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=mock_console),
            patch("visual_explainer.terminal.supports_unicode", return_value=True),
        ):
            progress = reporting.GenerationProgress(5, 3, quiet=False)

        assert progress.console is mock_console
        assert progress.total_images == 5
        assert progress.max_iterations == 3
        assert progress.quiet is False
        assert progress.current_image == 0
        assert progress.current_attempt == 0
        assert progress.task_id is None
        assert progress._use_unicode is True

    def test_rich_unavailable_console_is_none(self):
        with patch("visual_explainer.terminal.RICH_AVAILABLE", False):
            progress = reporting.GenerationProgress(2, 4, quiet=False)

        assert progress.console is None

    def test_ascii_unicode_flag_stored_when_unicode_unsupported(self):
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch("visual_explainer.terminal.supports_unicode", return_value=False),
        ):
            progress = reporting.GenerationProgress(2, 4, quiet=False)

        assert progress._use_unicode is False


class TestGenerationProgressContextManager:
    """Tests for GenerationProgress.__enter__ / __exit__."""

    def test_enter_creates_progress_and_task_when_rich_available(self):
        mock_progress_instance = MagicMock()
        mock_progress_instance.__enter__.return_value = mock_progress_instance
        mock_progress_instance.add_task.return_value = "task-id-1"

        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch("visual_explainer.terminal.supports_unicode", return_value=True),
            patch.object(reporting, "Progress", return_value=mock_progress_instance),
        ):
            progress = reporting.GenerationProgress(3, 2, quiet=False)
            entered = progress.__enter__()

            assert entered is progress
            assert progress.progress is mock_progress_instance
            assert progress.task_id == "task-id-1"
            mock_progress_instance.add_task.assert_called_once_with("Generating images...", total=3)

    def test_enter_uses_ascii_spinner_when_unicode_unsupported(self):
        mock_progress_instance = MagicMock()
        mock_progress_instance.__enter__.return_value = mock_progress_instance
        mock_progress_instance.add_task.return_value = "task-id-1"

        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch("visual_explainer.terminal.supports_unicode", return_value=False),
            patch.object(reporting, "Progress", return_value=mock_progress_instance),
            patch.object(reporting, "SpinnerColumn") as mock_spinner_cls,
        ):
            progress = reporting.GenerationProgress(3, 2, quiet=False)
            assert progress._use_unicode is False
            progress.__enter__()

        mock_spinner_cls.assert_called_once_with(spinner_name="line")
        assert progress.progress is mock_progress_instance

    def test_enter_skips_progress_when_quiet(self):
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
            patch("visual_explainer.terminal.supports_unicode", return_value=True),
            patch.object(reporting, "Progress") as mock_progress_cls,
        ):
            progress = reporting.GenerationProgress(3, 2, quiet=True)
            progress.__enter__()

        assert progress.progress is None
        mock_progress_cls.assert_not_called()

    def test_enter_skips_progress_when_rich_unavailable(self):
        with patch("visual_explainer.terminal.RICH_AVAILABLE", False):
            progress = reporting.GenerationProgress(3, 2, quiet=False)
            progress.__enter__()

        assert progress.progress is None
        assert progress.task_id is None

    def test_exit_calls_progress_exit_when_present(self):
        mock_progress_instance = MagicMock()
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=MagicMock()),
        ):
            progress = reporting.GenerationProgress(2, 2, quiet=False)
            progress.progress = mock_progress_instance
            progress.__exit__(None, None, None)

        mock_progress_instance.__exit__.assert_called_once_with(None, None, None)

    def test_exit_is_noop_when_progress_none(self):
        with patch("visual_explainer.terminal.RICH_AVAILABLE", False):
            progress = reporting.GenerationProgress(2, 2, quiet=False)
            # Should not raise even though self.progress is None.
            progress.__exit__(None, None, None)
        assert progress.progress is None


class TestGenerationProgressMethods:
    """Tests for GenerationProgress instance methods."""

    def _make_progress(self, quiet=False, console=None):
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=console or MagicMock()),
            patch("visual_explainer.terminal.supports_unicode", return_value=True),
        ):
            return reporting.GenerationProgress(3, 2, quiet=quiet)

    def test_start_image_updates_state_and_prints_rule(self):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        progress.start_image(2, "My Title")

        assert progress.current_image == 2
        assert progress.current_attempt == 0
        mock_console.rule.assert_called_once()
        rule_arg = mock_console.rule.call_args.args[0]
        assert "Image 2 of 3" in rule_arg
        assert "My Title" in rule_arg

    def test_start_image_quiet_mode_skips_printing(self):
        mock_console = MagicMock()
        progress = self._make_progress(quiet=True, console=mock_console)
        progress.start_image(1, "Title")

        assert progress.current_image == 1
        mock_console.rule.assert_not_called()

    def test_start_attempt_updates_state_and_prints(self):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        progress.start_attempt(2)

        assert progress.current_attempt == 2
        printed = mock_console.print.call_args.args[0]
        assert "Attempt 2/2:" in printed

    def test_start_attempt_quiet_mode_skips_printing(self):
        mock_console = MagicMock()
        progress = self._make_progress(quiet=True, console=mock_console)
        progress.start_attempt(1)

        assert progress.current_attempt == 1
        mock_console.print.assert_not_called()

    def test_update_status_updates_progress_bar_description_when_present(self):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        progress.current_image = 2
        mock_bar = MagicMock()
        progress.progress = mock_bar
        progress.task_id = "task-1"

        progress.update_status("Refining...")

        mock_bar.update.assert_called_once_with("task-1", description="Image 2/3: Refining...")
        mock_console.print.assert_not_called()

    def test_update_status_prints_dim_text_when_no_progress_bar(self):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        # No progress bar set (progress is None, as after a non-entered context).
        progress.update_status("Generating...")

        printed = mock_console.print.call_args.args[0]
        assert "Generating..." in printed

    def test_update_status_quiet_mode_is_noop(self):
        mock_console = MagicMock()
        progress = self._make_progress(quiet=True, console=mock_console)
        progress.update_status("Should not print")

        mock_console.print.assert_not_called()

    def test_show_evaluation_prints_scores_and_pass_verdict(self, sample_passing_evaluation):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        progress.show_evaluation(sample_passing_evaluation)

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Concept clarity: 92%" in printed_text
        assert "Visual appeal: 88%" in printed_text
        assert "Audience fit: 90%" in printed_text
        assert "Flow: 90%" in printed_text
        assert "Overall: 90%" in printed_text
        assert "[green]PASS[/green]" in printed_text

    def test_show_evaluation_prints_needs_refinement_verdict_in_yellow(
        self, sample_evaluation_result
    ):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        progress.show_evaluation(sample_evaluation_result)

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "[yellow]NEEDS_REFINEMENT[/yellow]" in printed_text

    def test_show_evaluation_quiet_mode_is_noop(self, sample_evaluation_result):
        mock_console = MagicMock()
        progress = self._make_progress(quiet=True, console=mock_console)
        progress.show_evaluation(sample_evaluation_result)

        mock_console.print.assert_not_called()

    def _make_no_console_progress(self):
        """A GenerationProgress built with RICH_AVAILABLE=False, so self.console is None."""
        with patch("visual_explainer.terminal.RICH_AVAILABLE", False):
            return reporting.GenerationProgress(3, 2, quiet=False)

    def test_start_image_with_no_console_updates_state_without_raising(self):
        progress = self._make_no_console_progress()
        progress.start_image(2, "Title")

        assert progress.current_image == 2
        assert progress.current_attempt == 0

    def test_start_attempt_with_no_console_updates_state_without_raising(self):
        progress = self._make_no_console_progress()
        progress.start_attempt(1)

        assert progress.current_attempt == 1

    def test_update_status_with_no_console_and_no_progress_is_noop(self):
        progress = self._make_no_console_progress()
        # Neither self.progress nor self.console is set: should not raise.
        progress.update_status("Working...")

        assert progress.progress is None
        assert progress.console is None

    def test_show_evaluation_with_no_console_is_noop(self, sample_evaluation_result):
        progress = self._make_no_console_progress()
        # Should not raise even with no console to print to.
        progress.show_evaluation(sample_evaluation_result)

        assert progress.console is None

    def test_complete_image_advances_progress_bar_and_prints_summary(self):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        mock_bar = MagicMock()
        progress.progress = mock_bar
        progress.task_id = "task-1"

        progress.complete_image(1, 2, 0.9)

        mock_bar.advance.assert_called_once_with("task-1")
        printed = mock_console.print.call_args.args[0]
        assert "Image 1 complete." in printed
        assert "Attempt 2" in printed
        assert "90%" in printed

    def test_complete_image_without_progress_bar_still_prints_summary(self):
        mock_console = MagicMock()
        progress = self._make_progress(console=mock_console)
        # progress.progress is None (never entered context manager).
        progress.complete_image(3, 1, 0.75)

        printed = mock_console.print.call_args.args[0]
        assert "Image 3 complete." in printed
        assert "75%" in printed

    def test_complete_image_quiet_mode_skips_print_but_still_advances(self):
        mock_console = MagicMock()
        progress = self._make_progress(quiet=True, console=mock_console)
        mock_bar = MagicMock()
        progress.progress = mock_bar
        progress.task_id = "task-1"

        progress.complete_image(1, 1, 0.8)

        mock_bar.advance.assert_called_once_with("task-1")
        mock_console.print.assert_not_called()


# ---------------------------------------------------------------------------
# display_completion_summary
# ---------------------------------------------------------------------------


class TestDisplayCompletionSummary:
    """Tests for display_completion_summary."""

    def _successful_result(self, number, title, score) -> ImageResult:
        result = ImageResult(image_number=number, title=title)
        result.status = "complete"
        result.final_score = score
        return result

    def _failed_result(self, number, title) -> ImageResult:
        result = ImageResult(image_number=number, title=title)
        result.status = "failed"
        return result

    def test_prints_results_table_and_final_images_list(self, temp_output_dir):
        results = [
            self._successful_result(1, "First Image", 0.90),
            self._successful_result(2, "Second Image", 0.80),
        ]

        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_completion_summary(results, temp_output_dir, 12.5, 8)

        table_calls = [
            c
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], reporting.Table)
        ]
        assert len(table_calls) == 1
        results_table = table_calls[0].args[0]
        assert results_table.row_count == 6

        mock_console.rule.assert_called_once_with("[bold]Generation Complete[/bold]")

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert str(temp_output_dir) in printed_text
        assert "Final images:" in printed_text
        assert "First Image (Score: 90%)" in printed_text
        assert "Second Image (Score: 80%)" in printed_text
        assert "Failed images:" not in printed_text

    def test_prints_failed_images_section_when_present(self, temp_output_dir):
        results = [
            self._successful_result(1, "Good Image", 0.95),
            self._failed_result(2, "Bad Image"),
        ]

        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_completion_summary(results, temp_output_dir, 5.0, 4)

        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Failed images:" in printed_text
        assert "Bad Image" in printed_text

    def test_no_successful_images_average_score_is_zero(self, temp_output_dir):
        results = [self._failed_result(1, "Only Failure")]

        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_completion_summary(results, temp_output_dir, 3.0, 2)

        results_table = next(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], reporting.Table)
        )
        # Row 2 (index 1) is "Average quality score".
        assert results_table.columns[1]._cells[2] == "0%"
        printed_text = "\n".join(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], str)
        )
        assert "Final images:" not in printed_text

    def test_metrics_row_values_reflect_inputs(self, temp_output_dir):
        results = [self._successful_result(1, "Image One", 0.85)]

        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            reporting.display_completion_summary(results, temp_output_dir, 7.25, 10)

        results_table = next(
            c.args[0]
            for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], reporting.Table)
        )
        # Row order: Images generated(0), Total attempts(1), Average quality
        # score(2), Total duration(3), API calls(4), Estimated cost(5).
        assert results_table.columns[1]._cells[0] == "1 of 1"
        assert results_table.columns[1]._cells[3] == f"{7.25:.1f}s"
        assert results_table.columns[1]._cells[4] == "10"
        assert results_table.columns[1]._cells[2] == "85%"
