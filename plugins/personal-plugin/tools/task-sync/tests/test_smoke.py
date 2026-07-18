"""Smoke tests for the task_sync CLI wiring (help text, dispatch)."""

from __future__ import annotations

from pathlib import Path

import pytest

from task_sync.__main__ import SUBCOMMANDS, build_parser, main


def test_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in out


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_subcommand_help_exits_zero(name: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([name, "--help"])
    assert exc_info.value.code == 0


@pytest.mark.parametrize("alias", ["ls", "close", "rm"])
def test_subcommand_alias_help_exits_zero(alias: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([alias, "--help"])
    assert exc_info.value.code == 0


def test_no_subcommand_is_an_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0


def test_build_parser_registers_all_subcommands() -> None:
    parser = build_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"
    assert callable(args.func)


def test_missing_tasks_file_is_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = str(tmp_path / "nope.json")
    exit_code = main(["status", "--tasks", missing])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "task-sync init" in err
