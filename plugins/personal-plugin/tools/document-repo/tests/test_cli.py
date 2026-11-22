import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import document_repo.cli as cli
from document_repo import __version__
from document_repo.cli import emit, load_json, main

TOOL_SRC = Path(__file__).resolve().parents[1] / "src"


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_subcommand_prints_help_and_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_module_entry_runs() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "document_repo", "--version"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(TOOL_SRC)},
    )
    assert proc.returncode == 0
    assert __version__ in proc.stdout


def test_emit_stdout_writes_pretty_json(capsys: pytest.CaptureFixture[str]) -> None:
    emit({"k": 1})
    out = capsys.readouterr().out
    assert out == '{\n  "k": 1\n}\n'
    assert json.loads(out) == {"k": 1}


def test_emit_file_creates_parents(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b.json"
    emit({"k": 1}, target)
    assert target.is_file()
    assert json.loads(target.read_text(encoding="utf-8")) == {"k": 1}


def test_emit_file_keeps_non_ascii_unescaped(tmp_path: Path) -> None:
    target = tmp_path / "u.json"
    emit({"s": "é—✓"}, target)
    raw = target.read_text(encoding="utf-8")
    assert "é—✓" in raw
    assert "\\u" not in raw
    assert load_json(target) == {"s": "é—✓"}


def test_load_json_reads_emitted_file(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    emit([1, "two", None], target)
    assert load_json(target) == [1, "two", None]


def test_emit_stdout_non_ascii_without_buffer(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class NoBuffer:
        def __init__(self) -> None:
            self.chunks: list[str] = []

        def write(self, text: str) -> None:
            self.chunks.append(text)

    fake = NoBuffer()
    monkeypatch.setattr(cli.sys, "stdout", fake)
    emit({"s": "é"})
    assert "".join(fake.chunks) == '{\n  "s": "é"\n}\n'


def test_main_dispatches_to_func(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="document_repo")
        sub = parser.add_subparsers(dest="cmd")
        p = sub.add_parser("fake")
        p.set_defaults(func=lambda args: 7)
        return parser

    monkeypatch.setattr(cli, "build_parser", fake_build_parser)
    assert main(["fake"]) == 7
