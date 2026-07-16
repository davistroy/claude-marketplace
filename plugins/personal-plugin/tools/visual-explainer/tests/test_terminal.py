"""Tests for the terminal and io_utils modules.

Covers:
- ``visual_explainer.terminal``: ``is_interactive``, ``supports_unicode``,
  ``get_console`` (lazy singleton), and the ``RICH_AVAILABLE`` flag.
- ``visual_explainer.io_utils``: ``_atomic_write_text`` (write-then-replace
  with cleanup on error).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

import visual_explainer.terminal as terminal
from visual_explainer.io_utils import _atomic_write_text
from visual_explainer.terminal import get_console, is_interactive, supports_unicode

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_console_singleton():
    """Ensure the module-level Console singleton doesn't leak across tests.

    ``get_console`` caches its result in ``terminal._console``. Other test
    modules in this suite also exercise ``get_console``, so the singleton
    must be reset both before and after each test here to keep this module
    self-contained and order-independent.
    """
    terminal._console = None
    yield
    terminal._console = None


# ---------------------------------------------------------------------------
# is_interactive Tests
# ---------------------------------------------------------------------------


class TestIsInteractive:
    """Tests for is_interactive()."""

    def test_both_tty_returns_true(self):
        with patch("sys.stdin.isatty", return_value=True):
            with patch("sys.stdout.isatty", return_value=True):
                assert is_interactive() is True

    def test_stdin_not_tty_returns_false(self):
        with patch("sys.stdin.isatty", return_value=False):
            with patch("sys.stdout.isatty", return_value=True):
                assert is_interactive() is False

    def test_stdout_not_tty_returns_false(self):
        with patch("sys.stdin.isatty", return_value=True):
            with patch("sys.stdout.isatty", return_value=False):
                assert is_interactive() is False

    def test_neither_tty_returns_false(self):
        with patch("sys.stdin.isatty", return_value=False):
            with patch("sys.stdout.isatty", return_value=False):
                assert is_interactive() is False


# ---------------------------------------------------------------------------
# supports_unicode Tests — Unix path
# ---------------------------------------------------------------------------


class TestSupportsUnicodeUnix:
    """Tests for supports_unicode() on the Unix (non-win32) code path."""

    def test_utf8_encoding_returns_true(self):
        with patch("sys.platform", "linux"):
            with patch("sys.stdout", new=SimpleNamespace(encoding="utf-8")):
                assert supports_unicode() is True

    def test_utf8_no_dash_variant_returns_true(self):
        with patch("sys.platform", "linux"):
            with patch("sys.stdout", new=SimpleNamespace(encoding="UTF8")):
                assert supports_unicode() is True

    def test_ascii_encoding_returns_false(self):
        with patch("sys.platform", "linux"):
            with patch("sys.stdout", new=SimpleNamespace(encoding="ascii")):
                assert supports_unicode() is False

    def test_none_encoding_returns_false(self):
        with patch("sys.platform", "linux"):
            with patch("sys.stdout", new=SimpleNamespace(encoding=None)):
                assert supports_unicode() is False


# ---------------------------------------------------------------------------
# supports_unicode Tests — Windows path
# ---------------------------------------------------------------------------


class TestSupportsUnicodeWindows:
    """Tests for supports_unicode() on the win32 code path.

    The final branch inside the win32 ``try`` block (a successful
    ``ctypes.windll.kernel32.GetConsoleOutputCP() == 65001`` check) is
    genuinely unreachable on Linux: ``ctypes.windll`` does not exist outside
    real Windows, so the attribute access always raises ``AttributeError``
    before that comparison can run. That sub-branch is intentionally left
    uncovered here (verified: it raises inside the try, is caught by
    ``except (AttributeError, OSError)``, and falls through to ``return
    False`` at the bottom of the function — the fallthrough itself IS
    covered by ``test_fallthrough_to_legacy_returns_false`` below).
    """

    def test_wt_session_returns_true(self, monkeypatch):
        monkeypatch.setenv("WT_SESSION", "1")
        monkeypatch.delenv("ConEmuANSI", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        with patch("sys.platform", "win32"):
            assert supports_unicode() is True

    def test_conemu_returns_true(self, monkeypatch):
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.setenv("ConEmuANSI", "ON")
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        with patch("sys.platform", "win32"):
            assert supports_unicode() is True

    def test_vscode_terminal_returns_true(self, monkeypatch):
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.delenv("ConEmuANSI", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        with patch("sys.platform", "win32"):
            assert supports_unicode() is True

    def test_fallthrough_to_legacy_returns_false(self, monkeypatch):
        """No modern-terminal env vars set and a non-UTF8 console code page:
        the ctypes probe reports a legacy code page (not 65001), so the
        function falls through to the ASCII-legacy default (False). ``ctypes.windll``
        is mocked (create=True) so the result is deterministic on any host OS —
        without this a real Windows runner reports code page 65001 and returns True."""
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.delenv("ConEmuANSI", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        fake_windll = MagicMock()
        fake_windll.kernel32.GetConsoleOutputCP.return_value = 437  # legacy US OEM, not UTF-8
        with (
            patch("sys.platform", "win32"),
            patch("ctypes.windll", fake_windll, create=True),
        ):
            assert supports_unicode() is False


# ---------------------------------------------------------------------------
# RICH_AVAILABLE import-fallback Test
# ---------------------------------------------------------------------------


class TestRichImportFallback:
    """Covers the module-level ``except ImportError: RICH_AVAILABLE = False``
    fallback (lines 25-26), which normally never executes in this test
    environment because ``rich`` is installed.

    Simulates the import failure by blanking ``sys.modules["rich.console"]``
    (which forces the next `from rich.console import Console` to raise
    ImportError) and reloading the module so its top-level try/except
    re-runs. The module is reloaded again in ``finally`` to restore
    ``RICH_AVAILABLE=True`` and a real ``Console`` binding for every other
    test in this file and the wider suite.
    """

    def test_import_error_sets_rich_available_false(self):
        assert terminal.RICH_AVAILABLE is True  # sanity: rich is installed here
        try:
            with patch.dict(sys.modules, {"rich.console": None}):
                importlib.reload(terminal)
                assert terminal.RICH_AVAILABLE is False
        finally:
            importlib.reload(terminal)
        assert terminal.RICH_AVAILABLE is True


# ---------------------------------------------------------------------------
# get_console Tests
# ---------------------------------------------------------------------------


class TestGetConsole:
    """Tests for get_console()."""

    def test_returns_console_instance(self):
        with patch("visual_explainer.terminal.is_interactive", return_value=False):
            with patch("visual_explainer.terminal.supports_unicode", return_value=False):
                console = get_console()
        assert isinstance(console, Console)

    def test_caches_same_instance_across_calls(self):
        with patch("visual_explainer.terminal.is_interactive", return_value=False):
            with patch("visual_explainer.terminal.supports_unicode", return_value=False):
                first = get_console()
                second = get_console()
        assert first is second
        assert terminal._console is first

    def test_no_rich_raises_runtime_error(self):
        with patch("visual_explainer.terminal.RICH_AVAILABLE", False):
            with pytest.raises(RuntimeError, match="Rich"):
                get_console()
        # Confirm the singleton was never populated on the failure path.
        assert terminal._console is None

    def test_unix_branch_passes_force_terminal_only(self):
        """On non-win32 platforms, Console is built with force_terminal but
        no legacy_windows kwarg."""
        mock_console_cls = MagicMock(return_value=MagicMock(name="console-instance"))
        with patch("visual_explainer.terminal.Console", mock_console_cls):
            with patch("sys.platform", "linux"):
                with patch("visual_explainer.terminal.is_interactive", return_value=True):
                    with patch("visual_explainer.terminal.supports_unicode", return_value=True):
                        result = get_console()

        mock_console_cls.assert_called_once_with(force_terminal=True)
        assert result is mock_console_cls.return_value

    def test_windows_branch_sets_legacy_windows_when_no_unicode(self):
        mock_console_cls = MagicMock(return_value=MagicMock(name="console-instance"))
        with patch("visual_explainer.terminal.Console", mock_console_cls):
            with patch("sys.platform", "win32"):
                with patch("visual_explainer.terminal.is_interactive", return_value=False):
                    with patch("visual_explainer.terminal.supports_unicode", return_value=False):
                        get_console()

        mock_console_cls.assert_called_once_with(force_terminal=False, legacy_windows=True)

    def test_windows_branch_clears_legacy_windows_when_unicode_supported(self):
        mock_console_cls = MagicMock(return_value=MagicMock(name="console-instance"))
        with patch("visual_explainer.terminal.Console", mock_console_cls):
            with patch("sys.platform", "win32"):
                with patch("visual_explainer.terminal.is_interactive", return_value=True):
                    with patch("visual_explainer.terminal.supports_unicode", return_value=True):
                        get_console()

        mock_console_cls.assert_called_once_with(force_terminal=True, legacy_windows=False)


# ---------------------------------------------------------------------------
# _atomic_write_text Tests
# ---------------------------------------------------------------------------


class TestAtomicWriteText:
    """Tests for io_utils._atomic_write_text()."""

    def test_writes_expected_content(self, tmp_path: Path):
        target = tmp_path / "metadata.json"
        _atomic_write_text(target, '{"key": "value"}')
        assert target.read_text(encoding="utf-8") == '{"key": "value"}'

    def test_no_temp_file_left_behind_on_success(self, tmp_path: Path):
        target = tmp_path / "metadata.json"
        _atomic_write_text(target, "content")
        # os.replace renames the temp file onto the destination, so the
        # directory should contain exactly the target file — no ".*.tmp"
        # artifact left over.
        assert list(tmp_path.glob("*.tmp")) == []
        assert list(tmp_path.iterdir()) == [target]

    def test_overwrites_existing_file(self, tmp_path: Path):
        target = tmp_path / "concepts.json"
        target.write_text("old content", encoding="utf-8")
        _atomic_write_text(target, "new content")
        assert target.read_text(encoding="utf-8") == "new content"

    def test_custom_encoding_round_trips(self, tmp_path: Path):
        target = tmp_path / "evaluation-01.json"
        content = "café — unicode payload"
        _atomic_write_text(target, content, encoding="utf-16")
        assert target.read_text(encoding="utf-16") == content

    def test_error_during_replace_cleans_up_temp_file_and_propagates(self, tmp_path: Path):
        target = tmp_path / "metadata.json"
        with patch(
            "visual_explainer.io_utils.os.replace",
            side_effect=OSError("replace failed"),
        ):
            with pytest.raises(OSError, match="replace failed"):
                _atomic_write_text(target, "content")

        # The destination was never created, and the temp file used to
        # stage the write was cleaned up by the except-clause unlink.
        assert not target.exists()
        assert list(tmp_path.glob("*.tmp")) == []
        assert list(tmp_path.iterdir()) == []

    def test_error_propagates_original_exception_type_unwrapped(self, tmp_path: Path):
        """The bare `except BaseException: ...; raise` must re-raise the
        original exception unchanged, not wrap or swallow it."""
        target = tmp_path / "metadata.json"
        with patch(
            "visual_explainer.io_utils.os.replace",
            side_effect=ValueError("custom failure"),
        ):
            with pytest.raises(ValueError, match="custom failure"):
                _atomic_write_text(target, "content")
        assert list(tmp_path.iterdir()) == []
