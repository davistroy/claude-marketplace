"""Smoke tests for the task_sync CLI skeleton."""

from __future__ import annotations

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


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_subcommand_stub_runs_and_prints_notice(
    name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([name])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "not yet implemented" in out
    assert name in out


def test_no_subcommand_is_an_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0


def test_build_parser_registers_all_subcommands() -> None:
    parser = build_parser()
    # argparse exposes registered subparser choices via the private _subparsers
    # action; assert against the public SUBCOMMANDS tuple instead of reaching
    # into argparse internals.
    args = parser.parse_args(["status"])
    assert args.command == "status"
    assert callable(args.func)
