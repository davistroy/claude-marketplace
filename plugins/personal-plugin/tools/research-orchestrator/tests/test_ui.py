"""Tests for the Rich terminal UI module."""

import time
from unittest.mock import MagicMock, patch

from research_orchestrator.models import ProviderPhase
from research_orchestrator.ui import (
    PHASE_CONFIG,
    PROVIDER_COLORS,
    ProviderState,
    RichUI,
    SimpleUI,
    StreamingUI,
    create_status_callback,
    detect_ui_mode,
    get_ui,
)

# ---------------------------------------------------------------------------
# ProviderState tests
# ---------------------------------------------------------------------------


class TestProviderState:
    """Tests for the ProviderState dataclass."""

    def test_defaults(self):
        """Test default state values."""
        state = ProviderState(name="claude")
        assert state.name == "claude"
        assert state.phase == ProviderPhase.INITIALIZING
        assert state.status_message == ""
        assert state.end_time is None
        assert state.word_count == 0

    def test_elapsed_seconds_running(self):
        """Test elapsed time while running."""
        state = ProviderState(name="claude", start_time=time.time() - 5.0)
        elapsed = state.elapsed_seconds
        assert 4.5 < elapsed < 6.0

    def test_elapsed_seconds_completed(self):
        """Test elapsed time when completed."""
        now = time.time()
        state = ProviderState(name="claude", start_time=now - 10.0, end_time=now - 5.0)
        elapsed = state.elapsed_seconds
        assert 4.5 < elapsed < 5.5

    def test_elapsed_formatted_seconds(self):
        """Test formatted elapsed time under 60s."""
        state = ProviderState(name="claude", start_time=time.time() - 30.0)
        formatted = state.elapsed_formatted
        assert formatted.endswith("s")
        assert "m" not in formatted

    def test_elapsed_formatted_minutes(self):
        """Test formatted elapsed time over 60s."""
        state = ProviderState(
            name="claude",
            start_time=time.time() - 125.0,
            end_time=time.time(),
        )
        formatted = state.elapsed_formatted
        assert "m" in formatted
        assert formatted.startswith("2m")

    def test_is_complete_when_completed(self):
        """Test is_complete for COMPLETED phase."""
        state = ProviderState(name="claude", phase=ProviderPhase.COMPLETED)
        assert state.is_complete is True

    def test_is_complete_when_failed(self):
        """Test is_complete for FAILED phase."""
        state = ProviderState(name="claude", phase=ProviderPhase.FAILED)
        assert state.is_complete is True

    def test_is_complete_when_running(self):
        """Test is_complete for RESEARCHING phase."""
        state = ProviderState(name="claude", phase=ProviderPhase.RESEARCHING)
        assert state.is_complete is False


# ---------------------------------------------------------------------------
# RichUI tests
# ---------------------------------------------------------------------------


class TestRichUI:
    """Tests for the RichUI class."""

    def test_init_with_providers(self):
        """Test initialization with provider list."""
        ui = RichUI(providers=["claude", "openai"], force_terminal=True)
        assert "claude" in ui._providers
        assert "openai" in ui._providers

    def test_init_no_providers(self):
        """Test initialization without providers."""
        ui = RichUI(force_terminal=True)
        assert len(ui._providers) == 0

    def test_add_provider(self):
        """Test adding a provider dynamically."""
        ui = RichUI(force_terminal=True)
        ui.add_provider("gemini")
        assert "gemini" in ui._providers

    def test_add_provider_idempotent(self):
        """Test adding the same provider twice."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.add_provider("claude")
        assert len(ui._providers) == 1

    def test_update_provider_existing(self):
        """Test updating an existing provider."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.RESEARCHING, "Working...")

        state = ui._providers["claude"]
        assert state.phase == ProviderPhase.RESEARCHING
        assert state.status_message == "Working..."

    def test_update_provider_new(self):
        """Test updating a non-existent provider auto-adds it."""
        ui = RichUI(force_terminal=True)
        ui.update_provider("openai", ProviderPhase.CONNECTING, "Connecting...")

        assert "openai" in ui._providers
        assert ui._providers["openai"].phase == ProviderPhase.CONNECTING

    def test_update_provider_completed_sets_end_time(self):
        """Test that completing a provider sets end_time."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")

        state = ui._providers["claude"]
        assert state.end_time is not None

    def test_update_provider_failed_sets_end_time(self):
        """Test that failing a provider sets end_time."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.FAILED, "Error occurred")

        state = ui._providers["claude"]
        assert state.end_time is not None

    def test_add_saved_file(self):
        """Test tracking saved files."""
        ui = RichUI(force_terminal=True)
        ui.add_saved_file("/path/to/file.md")
        assert "/path/to/file.md" in ui._saved_files

    def test_create_display_returns_panel(self):
        """Test that _create_display returns a Panel."""
        from rich.panel import Panel

        ui = RichUI(providers=["claude"], force_terminal=True)
        panel = ui._create_display()
        assert isinstance(panel, Panel)

    def test_create_display_completed_provider(self):
        """Test display with a completed provider."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        panel = ui._create_display()
        # Should not raise
        assert panel is not None

    def test_context_manager(self):
        """Test context manager start/stop."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        with ui:
            assert ui._live is not None
        assert ui._live is None

    def test_print_summary_all_complete(self):
        """Test summary with all providers complete."""
        ui = RichUI(providers=["claude", "openai"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        ui.update_provider("openai", ProviderPhase.COMPLETED, "Done")
        # Should not raise
        ui.print_summary()

    def test_print_summary_all_failed(self):
        """Test summary with all providers failed."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.FAILED, "API Error")
        ui.print_summary()

    def test_print_summary_partial(self):
        """Test summary with partial results."""
        ui = RichUI(providers=["claude", "openai"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        ui.update_provider("openai", ProviderPhase.FAILED, "Error")
        ui.print_summary()

    def test_print_summary_with_saved_files(self):
        """Test summary displays saved files."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        ui.add_saved_file("report.md")
        ui.print_summary()

    def test_print_summary_with_word_count(self):
        """Test summary displays word count."""
        ui = RichUI(providers=["claude"], force_terminal=True)
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        ui._providers["claude"].word_count = 5000
        ui.print_summary()


# ---------------------------------------------------------------------------
# StreamingUI tests
# ---------------------------------------------------------------------------


class TestStreamingUI:
    """Tests for the StreamingUI class."""

    def test_init_with_providers(self):
        """Test initialization with providers."""
        ui = StreamingUI(providers=["claude", "openai"])
        assert "claude" in ui._providers
        assert "openai" in ui._providers

    def test_add_provider(self):
        """Test adding a provider."""
        ui = StreamingUI()
        ui.add_provider("gemini")
        assert "gemini" in ui._providers

    def test_update_provider_prints(self, capsys):
        """Test that update_provider prints a status line."""
        ui = StreamingUI(providers=["claude"])
        ui.update_provider("claude", ProviderPhase.RESEARCHING, "Working...")

        captured = capsys.readouterr()
        assert "CLAUDE" in captured.out
        assert "Researching" in captured.out

    def test_update_provider_completed(self, capsys):
        """Test completed provider output."""
        ui = StreamingUI(providers=["claude"])
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")

        captured = capsys.readouterr()
        assert "Completed" in captured.out

    def test_update_provider_deduplicates(self, capsys):
        """Test that duplicate updates are suppressed."""
        ui = StreamingUI(providers=["claude"])
        ui.update_provider("claude", ProviderPhase.RESEARCHING, "Working...")
        ui.update_provider("claude", ProviderPhase.RESEARCHING, "Working...")

        captured = capsys.readouterr()
        # Only one line should be printed
        lines = [ln for ln in captured.out.strip().split("\n") if ln.strip()]
        assert len(lines) == 1

    def test_start_prints_header(self, capsys):
        """Test that start prints a header box."""
        ui = StreamingUI()
        ui.start()

        captured = capsys.readouterr()
        assert "Research in Progress" in captured.out

    def test_stop_prints_footer(self, capsys):
        """Test that stop prints a footer line."""
        ui = StreamingUI()
        ui.start()
        _ = capsys.readouterr()  # Clear start output
        ui.stop()

        captured = capsys.readouterr()
        # Should contain the bottom border
        assert len(captured.out.strip()) > 0

    def test_context_manager(self, capsys):
        """Test streaming UI as context manager."""
        with StreamingUI(providers=["claude"]) as ui:
            ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")

        captured = capsys.readouterr()
        assert "Research in Progress" in captured.out

    def test_print_summary_all_complete(self, capsys):
        """Test streaming summary with all complete."""
        ui = StreamingUI(providers=["claude"])
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        _ = capsys.readouterr()
        ui.print_summary()

        captured = capsys.readouterr()
        assert "Research Complete" in captured.out

    def test_print_summary_all_failed(self, capsys):
        """Test streaming summary with all failed."""
        ui = StreamingUI(providers=["claude"])
        ui.update_provider("claude", ProviderPhase.FAILED, "Error")
        _ = capsys.readouterr()
        ui.print_summary()

        captured = capsys.readouterr()
        assert "Research Failed" in captured.out

    def test_print_summary_partial(self, capsys):
        """Test streaming summary with partial results."""
        ui = StreamingUI(providers=["claude", "openai"])
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        ui.update_provider("openai", ProviderPhase.FAILED, "Error")
        _ = capsys.readouterr()
        ui.print_summary()

        captured = capsys.readouterr()
        assert "Partial" in captured.out or "1/2" in captured.out

    def test_print_summary_with_saved_files(self, capsys):
        """Test that saved files appear in summary."""
        ui = StreamingUI(providers=["claude"])
        ui.update_provider("claude", ProviderPhase.COMPLETED, "Done")
        ui.add_saved_file("report.md")
        _ = capsys.readouterr()
        ui.print_summary()

        captured = capsys.readouterr()
        assert "report.md" in captured.out

    def test_add_saved_file(self):
        """Test tracking saved files."""
        ui = StreamingUI()
        ui.add_saved_file("test.md")
        assert "test.md" in ui._saved_files


# ---------------------------------------------------------------------------
# SimpleUI tests
# ---------------------------------------------------------------------------


class TestSimpleUI:
    """Tests for the SimpleUI class."""

    def test_init_with_providers(self):
        """Test initialization with providers."""
        ui = SimpleUI(providers=["claude", "openai"])
        assert "claude" in ui._providers
        assert "openai" in ui._providers

    def test_add_provider(self):
        """Test adding a provider."""
        ui = SimpleUI()
        ui.add_provider("gemini")
        assert "gemini" in ui._providers

    def test_update_provider_prints(self, capsys):
        """Test that update_provider prints output."""
        ui = SimpleUI(providers=["claude"])
        ui.update_provider("claude", ProviderPhase.RESEARCHING, "Working...")

        captured = capsys.readouterr()
        assert "CLAUDE" in captured.out

    def test_start_prints_header(self, capsys):
        """Test that start prints header."""
        ui = SimpleUI()
        ui.start()

        captured = capsys.readouterr()
        assert "Research Progress" in captured.out

    def test_print_summary(self, capsys):
        """Test that summary prints completion info."""
        ui = SimpleUI()
        ui.start()
        _ = capsys.readouterr()
        ui.print_summary()

        captured = capsys.readouterr()
        assert "Completed in" in captured.out

    def test_print_summary_with_files(self, capsys):
        """Test that summary shows output files."""
        ui = SimpleUI()
        ui.add_saved_file("output.md")
        ui.start()
        _ = capsys.readouterr()
        ui.print_summary()

        captured = capsys.readouterr()
        assert "output.md" in captured.out

    def test_context_manager(self, capsys):
        """Test simple UI as context manager."""
        with SimpleUI() as ui:
            ui.update_provider("test", ProviderPhase.COMPLETED, "Done")

        captured = capsys.readouterr()
        assert "Research Progress" in captured.out


# ---------------------------------------------------------------------------
# Factory function tests
# ---------------------------------------------------------------------------


class TestCreateStatusCallback:
    """Tests for create_status_callback."""

    def test_callback_calls_update_provider(self):
        """Test that callback calls ui.update_provider."""
        ui = MagicMock()
        callback = create_status_callback(ui)
        callback("claude", ProviderPhase.RESEARCHING, "Working...")

        ui.update_provider.assert_called_once_with(
            "claude", ProviderPhase.RESEARCHING, "Working..."
        )


class TestGetUI:
    """Tests for the get_ui factory function."""

    def test_returns_rich_ui_when_available(self):
        """Test that RichUI is returned when available."""
        ui = get_ui(providers=["claude"], use_rich=True, force_terminal=True)
        assert isinstance(ui, RichUI)

    def test_returns_simple_when_rich_disabled(self):
        """Test fallback to SimpleUI when rich is disabled."""
        ui = get_ui(providers=["claude"], use_rich=False)
        assert isinstance(ui, SimpleUI)

    def test_returns_streaming_when_flag_set(self):
        """Test that streaming mode is selected via flag."""
        ui = get_ui(providers=["claude"], streaming=True)
        assert isinstance(ui, StreamingUI)

    @patch.dict("os.environ", {"STREAMING_UI": "1"})
    def test_returns_streaming_from_env(self):
        """Test that streaming mode is selected via env var."""
        ui = get_ui(providers=["claude"])
        assert isinstance(ui, StreamingUI)


class TestDetectUIMode:
    """Tests for detect_ui_mode."""

    @patch.dict("os.environ", {"STREAMING_UI": "1"})
    def test_streaming_env_override(self):
        """Test streaming env var override."""
        assert detect_ui_mode() == "streaming"

    @patch.dict("os.environ", {"FORCE_RICH_UI": "true"}, clear=False)
    def test_force_rich_env_override(self):
        """Test force rich env var override."""
        # Remove STREAMING_UI if set
        import os

        os.environ.pop("STREAMING_UI", None)
        assert detect_ui_mode() == "rich"

    @patch.dict("os.environ", {}, clear=True)
    def test_tty_returns_rich(self):
        """Test that TTY detection returns rich."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            result = detect_ui_mode()
            assert result == "rich"

    @patch.dict("os.environ", {}, clear=True)
    def test_non_tty_returns_streaming(self):
        """Test that non-TTY returns streaming."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            result = detect_ui_mode()
            assert result == "streaming"


# ---------------------------------------------------------------------------
# Module-level constants tests
# ---------------------------------------------------------------------------


class TestPhaseConfig:
    """Tests for PHASE_CONFIG constants."""

    def test_all_phases_configured(self):
        """Test that all ProviderPhase values have configuration."""
        for phase in ProviderPhase:
            assert phase in PHASE_CONFIG, f"Missing config for {phase}"

    def test_phase_config_keys(self):
        """Test that phase configs have required keys."""
        required_keys = {"label", "style", "icon"}
        for phase, config in PHASE_CONFIG.items():
            assert required_keys.issubset(config.keys()), (
                f"Missing keys for {phase}: {required_keys - config.keys()}"
            )


class TestProviderColors:
    """Tests for PROVIDER_COLORS constants."""

    def test_known_providers_have_colors(self):
        """Test that known providers have color mappings."""
        assert "claude" in PROVIDER_COLORS
        assert "openai" in PROVIDER_COLORS
        assert "gemini" in PROVIDER_COLORS
