"""Tests for CLI."""

import pytest
from pathlib import Path
import subprocess
import sys

from bpmn2drawio.cli import main, create_parser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCLIParser:
    """Tests for CLI argument parser."""

    def test_help_option(self, capsys):
        """Test --help displays usage."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "bpmn2drawio" in captured.out
        assert "Convert BPMN" in captured.out

    def test_version_option(self, capsys):
        """Test --version displays version."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "1.0.0" in captured.out

    def test_parse_basic_args(self):
        """Test parsing basic arguments."""
        parser = create_parser()
        args = parser.parse_args(["input.bpmn", "output.drawio"])

        assert args.input == "input.bpmn"
        assert args.output == "output.drawio"
        assert args.theme == "default"
        assert args.layout == "graphviz"

    def test_parse_all_options(self):
        """Test parsing all options."""
        parser = create_parser()
        args = parser.parse_args([
            "input.bpmn", "output.drawio",
            "--theme", "blueprint",
            "--layout", "preserve",
            "--direction", "TB",
            "--verbose",
        ])

        assert args.theme == "blueprint"
        assert args.layout == "preserve"
        assert args.direction == "TB"
        assert args.verbose


class TestCLIMain:
    """Tests for CLI main function."""

    def test_basic_conversion(self, tmp_path):
        """Test basic file conversion."""
        output_file = tmp_path / "output.drawio"

        exit_code = main([
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output_file),
        ])

        assert exit_code == 0
        assert output_file.exists()

    def test_conversion_with_theme(self, tmp_path):
        """Test conversion with theme."""
        output_file = tmp_path / "output.drawio"

        exit_code = main([
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output_file),
            "--theme", "blueprint",
        ])

        assert exit_code == 0
        assert output_file.exists()

    def test_verbose_output(self, tmp_path, capsys):
        """Test verbose output."""
        output_file = tmp_path / "output.drawio"

        exit_code = main([
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output_file),
            "--verbose",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Converted" in captured.out or "elements" in captured.out

    def test_missing_input_file(self, tmp_path, capsys):
        """Test error handling for missing input file."""
        output_file = tmp_path / "output.drawio"

        exit_code = main([
            "/nonexistent/file.bpmn",
            str(output_file),
        ])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "not found" in captured.err

    def test_direction_option(self, tmp_path):
        """Test direction option."""
        output_file = tmp_path / "output.drawio"

        exit_code = main([
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output_file),
            "--direction", "TB",
        ])

        assert exit_code == 0


class TestCLIModule:
    """Tests for running as module."""

    def test_run_as_module(self, tmp_path):
        """Test running as python -m bpmn2drawio."""
        output_file = tmp_path / "output.drawio"

        result = subprocess.run(
            [
                sys.executable, "-m", "bpmn2drawio",
                str(FIXTURES_DIR / "minimal.bpmn"),
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_file.exists()

    def test_module_help(self):
        """Test module --help."""
        result = subprocess.run(
            [sys.executable, "-m", "bpmn2drawio", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "bpmn2drawio" in result.stdout
