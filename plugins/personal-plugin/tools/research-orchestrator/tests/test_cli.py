"""Tests for the CLI module."""

import json
import os
from unittest.mock import patch

import pytest

from research_orchestrator.cli import (
    create_parser,
    main,
    print_results,
    run_check_providers,
    run_check_ready,
    run_execute,
    run_list_depths,
    save_results,
    status_callback_legacy,
    status_callback_phase,
)
from research_orchestrator.models import (
    ProviderPhase,
    ProviderResult,
    ProviderStatus,
    ResearchOutput,
)

# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestCreateParser:
    """Tests for argument parser creation."""

    def test_parser_exists(self):
        """Test that parser is created."""
        parser = create_parser()
        assert parser is not None

    def test_execute_subcommand(self):
        """Test parsing execute subcommand."""
        parser = create_parser()
        args = parser.parse_args(["execute", "--prompt", "test query"])
        assert args.command == "execute"
        assert args.prompt == "test query"

    def test_execute_default_sources(self):
        """Test default sources for execute."""
        parser = create_parser()
        args = parser.parse_args(["execute", "--prompt", "test"])
        assert args.sources == "claude,openai,gemini"

    def test_execute_custom_sources(self):
        """Test custom sources for execute."""
        parser = create_parser()
        args = parser.parse_args(["execute", "--prompt", "test", "--sources", "claude"])
        assert args.sources == "claude"

    def test_execute_depth_options(self):
        """Test depth choices for execute."""
        parser = create_parser()
        for depth in ["brief", "standard", "comprehensive"]:
            args = parser.parse_args(["execute", "--prompt", "test", "--depth", depth])
            assert args.depth == depth

    def test_execute_invalid_depth(self):
        """Test that invalid depth is rejected."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["execute", "--prompt", "test", "--depth", "invalid"])

    def test_execute_json_flag(self):
        """Test --json flag for execute."""
        parser = create_parser()
        args = parser.parse_args(["execute", "--prompt", "test", "--json"])
        assert args.json is True

    def test_execute_timeout(self):
        """Test custom timeout."""
        parser = create_parser()
        args = parser.parse_args(["execute", "--prompt", "test", "--timeout", "3600"])
        assert args.timeout == 3600.0

    def test_check_providers_subcommand(self):
        """Test check-providers subcommand."""
        parser = create_parser()
        args = parser.parse_args(["check-providers"])
        assert args.command == "check-providers"

    def test_list_depths_subcommand(self):
        """Test list-depths subcommand."""
        parser = create_parser()
        args = parser.parse_args(["list-depths"])
        assert args.command == "list-depths"

    def test_check_models_subcommand(self):
        """Test check-models subcommand."""
        parser = create_parser()
        args = parser.parse_args(["check-models"])
        assert args.command == "check-models"

    def test_check_ready_subcommand(self):
        """Test check-ready subcommand."""
        parser = create_parser()
        args = parser.parse_args(["check-ready"])
        assert args.command == "check-ready"

    def test_no_command_prints_help(self):
        """Test that no command defaults to None."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.command is None


# ---------------------------------------------------------------------------
# Status callback tests
# ---------------------------------------------------------------------------


class TestStatusCallbacks:
    """Tests for status callback functions."""

    def test_legacy_callback(self, capsys):
        """Test legacy status callback output."""
        status_callback_legacy("claude", "Starting research")

        captured = capsys.readouterr()
        assert "[claude] Starting research" in captured.err

    def test_phase_callback(self, capsys):
        """Test phase-aware status callback output."""
        status_callback_phase("openai", ProviderPhase.RESEARCHING, "Deep research started")

        captured = capsys.readouterr()
        assert "[openai]" in captured.err
        assert "researching" in captured.err


# ---------------------------------------------------------------------------
# run_list_depths tests
# ---------------------------------------------------------------------------


class TestRunListDepths:
    """Tests for run_list_depths."""

    def test_lists_all_depths(self, capsys):
        """Test that all depth levels are listed."""
        parser = create_parser()
        args = parser.parse_args(["list-depths"])
        result = run_list_depths(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "brief" in captured.out
        assert "standard" in captured.out
        assert "comprehensive" in captured.out


# ---------------------------------------------------------------------------
# run_check_providers tests
# ---------------------------------------------------------------------------


class TestRunCheckProviders:
    """Tests for run_check_providers."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_shows_availability(self, capsys):
        """Test provider availability display."""
        parser = create_parser()
        args = parser.parse_args(["check-providers"])
        result = run_check_providers(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Provider Availability" in captured.out
        assert "claude" in captured.out


# ---------------------------------------------------------------------------
# run_check_ready tests
# ---------------------------------------------------------------------------


class TestRunCheckReady:
    """Tests for run_check_ready."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_outputs_json(self, capsys):
        """Test that check-ready outputs valid JSON."""
        parser = create_parser()
        args = parser.parse_args(["check-ready"])
        run_check_ready(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "python_packages" in data
        assert "api_keys" in data
        assert "optional_tools" in data

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_detects_api_keys(self, capsys):
        """Test API key detection."""
        parser = create_parser()
        args = parser.parse_args(["check-ready"])
        run_check_ready(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["api_keys"]["ANTHROPIC_API_KEY"]["ok"] is True
        assert data["api_keys"]["OPENAI_API_KEY"]["ok"] is False


# ---------------------------------------------------------------------------
# run_execute tests
# ---------------------------------------------------------------------------


class TestRunExecute:
    """Tests for run_execute."""

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_keys_warning(self, capsys, tmp_path):
        """Test that missing API keys produce a warning."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "execute",
                "--prompt",
                "test",
                "--sources",
                "claude",
                "--output-dir",
                str(tmp_path),
            ]
        )
        result = run_execute(args)

        captured = capsys.readouterr()
        assert "Missing API keys" in captured.err
        assert result == 1

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_json_output_mode(self, capsys, tmp_path):
        """Test JSON output mode."""
        mock_output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="Test content",
                    duration_seconds=5.0,
                )
            ],
            depth="standard",
            total_duration_seconds=5.0,
        )

        parser = create_parser()
        args = parser.parse_args(
            [
                "execute",
                "--prompt",
                "test",
                "--sources",
                "claude",
                "--json",
                "--output-dir",
                str(tmp_path),
            ]
        )

        with patch("research_orchestrator.cli.asyncio.run", return_value=mock_output):
            result = run_execute(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["prompt"] == "test"
        assert result == 0

    def test_invalid_source_error(self, capsys, tmp_path):
        """Test that invalid source raises error."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "execute",
                "--prompt",
                "test",
                "--sources",
                "invalid_provider",
                "--output-dir",
                str(tmp_path),
            ]
        )
        result = run_execute(args)

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert result == 1


# ---------------------------------------------------------------------------
# print_results / save_results tests
# ---------------------------------------------------------------------------


class TestPrintResults:
    """Tests for print_results."""

    def test_prints_header(self, capsys, tmp_path):
        """Test that results header is printed."""
        output = ResearchOutput(
            prompt="test query for analysis",
            results=[
                ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="Some research content here that is long enough.",
                    duration_seconds=10.0,
                )
            ],
            depth="standard",
            total_duration_seconds=10.0,
        )
        print_results(output, str(tmp_path))

        captured = capsys.readouterr()
        assert "RESEARCH RESULTS" in captured.out
        assert "test query" in captured.out

    def test_prints_failed_results(self, capsys, tmp_path):
        """Test that failed results show error."""
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(
                    provider="openai",
                    status=ProviderStatus.FAILED,
                    error="API key invalid",
                    duration_seconds=1.0,
                )
            ],
            depth="standard",
            total_duration_seconds=1.0,
        )
        print_results(output, str(tmp_path))

        captured = capsys.readouterr()
        assert "API key invalid" in captured.out


class TestSaveResults:
    """Tests for save_results."""

    def test_saves_successful_results(self, tmp_path):
        """Test that successful results are saved to files."""
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="Research findings here",
                    duration_seconds=5.0,
                )
            ],
            depth="standard",
        )
        save_results(output, str(tmp_path))

        files = list(tmp_path.glob("research-claude-*.md"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "Research findings here" in content

    def test_creates_output_directory(self, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "nested" / "results"
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="Content",
                    duration_seconds=1.0,
                )
            ],
            depth="standard",
        )
        save_results(output, str(output_dir))
        assert output_dir.exists()


# ---------------------------------------------------------------------------
# main() tests
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for the main entry point."""

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help and exits 0."""
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_unknown_command_exits(self):
        """Test that unknown command exits with error."""
        with patch("sys.argv", ["prog", "nonexistent"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0
