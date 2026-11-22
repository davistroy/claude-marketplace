import subprocess
import sys

import pytest

from document_repo import __version__
from document_repo.cli import main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_subcommand_prints_help_and_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_module_entry_runs() -> None:
    proc = subprocess.run([sys.executable, "-m", "document_repo", "--version"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert __version__ in proc.stdout
