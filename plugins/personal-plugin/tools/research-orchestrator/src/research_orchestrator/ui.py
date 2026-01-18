"""Rich terminal UI for research progress display."""

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Callable

from research_orchestrator.models import ProviderPhase

# Try to import rich, provide fallback if not available
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.spinner import Spinner
    from rich.style import Style

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Phase display configurations with icons
PHASE_CONFIG = {
    ProviderPhase.INITIALIZING: {"label": "Initializing", "style": "dim white", "icon": "⏳", "spinner": "dots"},
    ProviderPhase.CONNECTING: {"label": "Connecting", "style": "cyan", "icon": "🔌", "spinner": "dots"},
    ProviderPhase.THINKING: {"label": "Thinking", "style": "yellow", "icon": "🧠", "spinner": "dots"},
    ProviderPhase.RESEARCHING: {"label": "Researching", "style": "blue", "icon": "🔍", "spinner": "dots"},
    ProviderPhase.POLLING: {"label": "Polling", "style": "magenta", "icon": "⏱️", "spinner": "dots"},
    ProviderPhase.PROCESSING: {"label": "Processing", "style": "cyan", "icon": "⚙️", "spinner": "dots"},
    ProviderPhase.COMPLETED: {"label": "Completed", "style": "green", "icon": "✓", "spinner": None},
    ProviderPhase.FAILED: {"label": "Failed", "style": "red", "icon": "✗", "spinner": None},
}

# Provider color coding
PROVIDER_COLORS = {
    "claude": "yellow",
    "openai": "green",
    "gemini": "blue",
}


@dataclass
class ProviderState:
    """Tracks the current state of a provider during execution."""

    name: str
    phase: ProviderPhase = ProviderPhase.INITIALIZING
    status_message: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    word_count: int = 0

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    @property
    def elapsed_formatted(self) -> str:
        """Get elapsed time as formatted string."""
        elapsed = self.elapsed_seconds
        if elapsed < 60:
            return f"{elapsed:.0f}s"
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes}m {seconds:02d}s"

    @property
    def is_complete(self) -> bool:
        """Check if the provider has finished (completed or failed)."""
        return self.phase in (ProviderPhase.COMPLETED, ProviderPhase.FAILED)


class RichUI:
    """Rich terminal UI for displaying research progress."""

    def __init__(self, providers: list[str] | None = None, force_terminal: bool = False) -> None:
        """Initialize the Rich UI.

        Args:
            providers: List of provider names to track.
            force_terminal: Force terminal output even if not detected as TTY.
        """
        if not RICH_AVAILABLE:
            raise ImportError("rich package required. Install with: pip install rich")

        # Force terminal if requested or via environment variable
        force = force_terminal or os.environ.get('FORCE_RICH_UI', '').lower() in ('1', 'true')
        self.console = Console(force_terminal=force)
        self._providers: dict[str, ProviderState] = {}
        self._live: Live | None = None
        self._start_time = time.time()
        self._saved_files: list[str] = []

        # Check Unicode support for emojis
        self._use_emoji = self._check_emoji_support()

        # Initialize provider states
        if providers:
            for provider in providers:
                self._providers[provider] = ProviderState(name=provider)

    def _check_emoji_support(self) -> bool:
        """Check if the terminal supports emoji output."""
        try:
            # Try to encode a test emoji
            '🔬'.encode(sys.stdout.encoding or 'utf-8')
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def add_provider(self, name: str) -> None:
        """Add a provider to track."""
        if name not in self._providers:
            self._providers[name] = ProviderState(name=name)

    def update_provider(
        self,
        name: str,
        phase: ProviderPhase,
        message: str = "",
    ) -> None:
        """Update a provider's state.

        Args:
            name: Provider name.
            phase: New phase.
            message: Status message.
        """
        if name not in self._providers:
            self.add_provider(name)

        state = self._providers[name]
        state.phase = phase
        state.status_message = message

        # Mark end time if completed
        if phase in (ProviderPhase.COMPLETED, ProviderPhase.FAILED):
            state.end_time = time.time()

        # Refresh display if live
        if self._live:
            self._live.update(self._create_display())

    def add_saved_file(self, filepath: str) -> None:
        """Track a saved file for summary display."""
        self._saved_files.append(filepath)

    def _create_display(self) -> Panel:
        """Create the progress display panel."""
        table = Table(
            show_header=True,
            header_style="bold white",
            box=None,
            padding=(0, 1),
            expand=True,
        )

        table.add_column("Provider", style="bold", width=12)
        table.add_column("Phase", width=16)
        table.add_column("Status", width=38)
        table.add_column("Elapsed", justify="right", width=10)

        for name, state in self._providers.items():
            # Provider name with color
            provider_color = PROVIDER_COLORS.get(name, "white")
            provider_text = Text(name.upper(), style=f"bold {provider_color}")

            # Phase with icon and styling
            phase_config = PHASE_CONFIG.get(state.phase, {"label": "Unknown", "style": "white", "icon": "•"})

            if state.is_complete:
                # Show static icon for completed states
                if self._use_emoji:
                    icon = phase_config['icon']
                else:
                    icon = "[OK]" if state.phase == ProviderPhase.COMPLETED else "[X]"
                phase_text = Text(f"{icon} {phase_config['label']}", style=phase_config["style"])
            else:
                # Show spinner-like indicator for active states
                if self._use_emoji:
                    spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
                else:
                    spinner_chars = "|/-\\"
                idx = int(time.time() * 8) % len(spinner_chars)
                spinner = spinner_chars[idx]
                phase_text = Text(f"{spinner} {phase_config['label']}", style=phase_config["style"])

            # Status message (truncate if needed)
            status = state.status_message[:38] if state.status_message else ""
            status_text = Text(status, style="dim" if state.is_complete else "white")

            # Elapsed time with color coding
            elapsed = state.elapsed_formatted
            if state.phase == ProviderPhase.COMPLETED:
                elapsed_text = Text(elapsed, style="green")
            elif state.phase == ProviderPhase.FAILED:
                elapsed_text = Text(elapsed, style="red")
            else:
                elapsed_text = Text(elapsed, style="cyan")

            table.add_row(provider_text, phase_text, status_text, elapsed_text)

        # Calculate totals
        total_elapsed = time.time() - self._start_time
        completed = sum(1 for s in self._providers.values() if s.phase == ProviderPhase.COMPLETED)
        total = len(self._providers)

        if total_elapsed < 60:
            total_str = f"{total_elapsed:.0f}s"
        else:
            minutes = int(total_elapsed // 60)
            seconds = int(total_elapsed % 60)
            total_str = f"{minutes}m {seconds:02d}s"

        subtitle = f"{completed}/{total} complete | Elapsed: {total_str}"
        title = "[bold cyan]Research in Progress[/bold cyan]"

        return Panel(
            table,
            title=title,
            subtitle=f"[dim]{subtitle}[/dim]",
            border_style="cyan",
            padding=(0, 1),
        )

    def start(self) -> None:
        """Start the live display."""
        self._start_time = time.time()
        self._live = Live(
            self._create_display(),
            console=self.console,
            refresh_per_second=4,  # Faster refresh for smoother spinners
            transient=False,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the live display."""
        if self._live:
            self._live.update(self._create_display())  # Final update
            self._live.stop()
            self._live = None

    def print_summary(self, output=None) -> None:
        """Print an enhanced summary panel after completion."""
        self.console.print()

        completed = sum(1 for s in self._providers.values() if s.phase == ProviderPhase.COMPLETED)
        failed = sum(1 for s in self._providers.values() if s.phase == ProviderPhase.FAILED)
        total = len(self._providers)

        # Calculate total elapsed
        total_elapsed = time.time() - self._start_time
        if total_elapsed < 60:
            total_str = f"{total_elapsed:.0f}s"
        else:
            minutes = int(total_elapsed // 60)
            seconds = int(total_elapsed % 60)
            total_str = f"{minutes}m {seconds:02d}s"

        # Build summary content
        lines = []

        # Status header - use ASCII-safe alternatives
        if completed == total:
            status_icon = "[OK]" if not self._use_emoji else "+"
            status_text = "Research Complete"
            status_style = "green"
        elif failed == total:
            status_icon = "[FAIL]" if not self._use_emoji else "X"
            status_text = "Research Failed"
            status_style = "red"
        else:
            status_icon = "[!]" if not self._use_emoji else "!"
            status_text = f"Partial Results ({completed}/{total})"
            status_style = "yellow"

        # Results section
        lines.append("")
        lines.append("[bold white]Results Summary[/bold white]")
        lines.append("[dim]" + "-" * 50 + "[/dim]")

        for name, state in self._providers.items():
            color = PROVIDER_COLORS.get(name, "white")
            if state.phase == ProviderPhase.COMPLETED:
                icon = "+" if not self._use_emoji else "+"
                status = "Success"
                words = f"~{state.word_count:,} words" if state.word_count > 0 else ""
            elif state.phase == ProviderPhase.FAILED:
                icon = "X" if not self._use_emoji else "X"
                status = state.status_message[:25] if state.status_message else "Failed"
                words = ""
            else:
                icon = "-" if not self._use_emoji else "-"
                status = state.phase.value
                words = ""

            status_color = "green" if state.phase == ProviderPhase.COMPLETED else "red"
            line = f"  [{color}]{icon} {name.upper():8}[/{color}]  {state.elapsed_formatted:>8}  [{status_color}]{status:20}[/{status_color}]  {words}"
            lines.append(line)

        # Output files section (if we have saved files)
        if self._saved_files:
            lines.append("")
            lines.append("[bold white]Output Files[/bold white]")
            lines.append("[dim]" + "-" * 50 + "[/dim]")
            for filepath in self._saved_files:
                lines.append(f"  [dim]*[/dim] {filepath}")

        # Footer
        lines.append("")
        lines.append(f"[dim]Total Duration: {total_str}[/dim]")

        content = "\n".join(lines)

        panel = Panel(
            content,
            title=f"[bold {status_style}]{status_icon} {status_text}[/bold {status_style}]",
            border_style=status_style,
            padding=(0, 1),
        )

        self.console.print(panel)

    def __enter__(self) -> "RichUI":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


class StreamingUI:
    """Line-by-line streaming UI for piped/captured contexts.

    This UI outputs each status update as a separate line, immediately flushed,
    ensuring visibility even when stdout is captured or piped.
    """

    # Box drawing characters with ASCII fallbacks for Windows
    BOX_CHARS = {
        'tl': '+',   # top-left
        'tr': '+',   # top-right
        'bl': '+',   # bottom-left
        'br': '+',   # bottom-right
        'h': '-',    # horizontal
        'v': '|',    # vertical
        'lj': '+',   # left junction
        'rj': '+',   # right junction
    }

    def __init__(self, providers: list[str] | None = None) -> None:
        """Initialize the streaming UI."""
        self._providers: dict[str, ProviderState] = {}
        self._start_time = time.time()
        self._saved_files: list[str] = []
        self._last_update: dict[str, str] = {}

        # Check if we can use Unicode box characters
        self._use_unicode = self._check_unicode_support()

        if self._use_unicode:
            self.BOX_CHARS = {
                'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
                'h': '─', 'v': '│', 'lj': '├', 'rj': '┤',
                'tl2': '╭', 'tr2': '╮', 'bl2': '╰', 'br2': '╯',
            }

        if providers:
            for provider in providers:
                self._providers[provider] = ProviderState(name=provider)

    def _check_unicode_support(self) -> bool:
        """Check if the terminal supports Unicode output."""
        try:
            # Try to encode a test Unicode character
            '─'.encode(sys.stdout.encoding or 'utf-8')
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def _flush_print(self, message: str) -> None:
        """Print and immediately flush output, handling encoding errors."""
        try:
            print(message, flush=True)
        except UnicodeEncodeError:
            # Fall back to ASCII-safe version
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            print(safe_message, flush=True)

    def add_provider(self, name: str) -> None:
        """Add a provider to track."""
        if name not in self._providers:
            self._providers[name] = ProviderState(name=name)

    def update_provider(
        self,
        name: str,
        phase: ProviderPhase,
        message: str = "",
    ) -> None:
        """Print a status update line."""
        if name not in self._providers:
            self.add_provider(name)

        state = self._providers[name]
        state.phase = phase
        state.status_message = message

        if phase in (ProviderPhase.COMPLETED, ProviderPhase.FAILED):
            state.end_time = time.time()

        # Get phase config
        phase_config = PHASE_CONFIG.get(phase, {"label": "Unknown", "icon": "•"})
        phase_label = phase_config["label"]
        elapsed = state.elapsed_formatted

        # Use ASCII-safe icons if Unicode not supported
        if self._use_unicode:
            icon = phase_config["icon"]
            sep = "│"
        else:
            # ASCII fallback icons
            ascii_icons = {
                ProviderPhase.INITIALIZING: "[.]",
                ProviderPhase.CONNECTING: "[~]",
                ProviderPhase.THINKING: "[*]",
                ProviderPhase.RESEARCHING: "[?]",
                ProviderPhase.POLLING: "[>]",
                ProviderPhase.PROCESSING: "[#]",
                ProviderPhase.COMPLETED: "[+]",
                ProviderPhase.FAILED: "[X]",
            }
            icon = ascii_icons.get(phase, "[.]")
            sep = "|"

        # Truncate message
        msg = message[:40] if message else ""

        # Create update key to avoid duplicate prints
        update_key = f"{name}:{phase.value}:{message}"
        if update_key == self._last_update.get(name):
            return
        self._last_update[name] = update_key

        # Print the update
        line = f"  {icon} [{name.upper():8}] {phase_label:12} {sep} {msg:40} {sep} {elapsed:>8}"
        self._flush_print(line)

    def add_saved_file(self, filepath: str) -> None:
        """Track a saved file."""
        self._saved_files.append(filepath)

    def start(self) -> None:
        """Start tracking."""
        self._start_time = time.time()
        h = self.BOX_CHARS['h']
        v = self.BOX_CHARS['v']
        tl = self.BOX_CHARS['tl']
        tr = self.BOX_CHARS['tr']
        lj = self.BOX_CHARS['lj']
        rj = self.BOX_CHARS['rj']

        self._flush_print("")
        self._flush_print(tl + h * 78 + tr)
        title = "  Research in Progress" if not self._use_unicode else "  🔬 Research in Progress"
        self._flush_print(v + title.ljust(78) + v)
        self._flush_print(lj + h * 78 + rj)

    def stop(self) -> None:
        """Stop tracking."""
        bl = self.BOX_CHARS['bl']
        br = self.BOX_CHARS['br']
        h = self.BOX_CHARS['h']
        self._flush_print(bl + h * 78 + br)

    def print_summary(self, output=None) -> None:
        """Print completion summary."""
        completed = sum(1 for s in self._providers.values() if s.phase == ProviderPhase.COMPLETED)
        failed = sum(1 for s in self._providers.values() if s.phase == ProviderPhase.FAILED)
        total = len(self._providers)

        total_elapsed = time.time() - self._start_time
        if total_elapsed < 60:
            total_str = f"{total_elapsed:.0f}s"
        else:
            minutes = int(total_elapsed // 60)
            seconds = int(total_elapsed % 60)
            total_str = f"{minutes}m {seconds:02d}s"

        # Use box characters
        h = self.BOX_CHARS['h']
        v = self.BOX_CHARS['v']
        tl = self.BOX_CHARS.get('tl2', self.BOX_CHARS['tl'])
        tr = self.BOX_CHARS.get('tr2', self.BOX_CHARS['tr'])
        bl = self.BOX_CHARS.get('bl2', self.BOX_CHARS['bl'])
        br = self.BOX_CHARS.get('br2', self.BOX_CHARS['br'])
        lj = self.BOX_CHARS['lj']
        rj = self.BOX_CHARS['rj']

        self._flush_print("")
        if completed == total:
            title = "[OK] Research Complete" if not self._use_unicode else "  ✅ Research Complete"
        elif failed == total:
            title = "[FAIL] Research Failed" if not self._use_unicode else "  ❌ Research Failed"
        else:
            title = f"[PARTIAL] Results ({completed}/{total})" if not self._use_unicode else f"  ⚠️  Partial Results ({completed}/{total})"

        self._flush_print(tl + h * 58 + tr)
        self._flush_print(v + title.ljust(58) + v)
        self._flush_print(lj + h * 58 + rj)

        results_title = "  Results Summary" if not self._use_unicode else "  📊 Results Summary"
        self._flush_print(v + results_title.ljust(58) + v)
        self._flush_print(v + "  " + h * 40 + "".ljust(16) + v)

        for name, state in self._providers.items():
            if state.phase == ProviderPhase.COMPLETED:
                icon = "[OK]" if not self._use_unicode else "✓"
                status = "Success"
            elif state.phase == ProviderPhase.FAILED:
                icon = "[X]" if not self._use_unicode else "✗"
                status = "Failed"
            else:
                icon = "[-]" if not self._use_unicode else "•"
                status = state.phase.value

            line = f"  {icon} {name.upper():8}  {state.elapsed_formatted:>8}  {status:20}"
            self._flush_print(v + line.ljust(58) + v)

        if self._saved_files:
            self._flush_print(v + "".ljust(58) + v)
            files_title = "  Output Files" if not self._use_unicode else "  📁 Output Files"
            self._flush_print(v + files_title.ljust(58) + v)
            self._flush_print(v + "  " + h * 40 + "".ljust(16) + v)
            for filepath in self._saved_files:
                line = f"  * {filepath}"
                # Truncate if too long
                if len(line) > 56:
                    line = line[:53] + "..."
                self._flush_print(v + line.ljust(58) + v)

        self._flush_print(v + "".ljust(58) + v)
        duration_line = f"  Total Duration: {total_str}" if not self._use_unicode else f"  ⏱️  Total Duration: {total_str}"
        self._flush_print(v + duration_line.ljust(58) + v)
        self._flush_print(bl + h * 58 + br)

    def __enter__(self) -> "StreamingUI":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


class SimpleUI:
    """Simple fallback UI when Rich is not available."""

    def __init__(self, providers: list[str] | None = None) -> None:
        """Initialize the simple UI."""
        self._providers: set[str] = set(providers) if providers else set()
        self._start_time = time.time()
        self._saved_files: list[str] = []

    def add_provider(self, name: str) -> None:
        """Add a provider to track."""
        self._providers.add(name)

    def update_provider(
        self,
        name: str,
        phase: ProviderPhase,
        message: str = "",
    ) -> None:
        """Print a status update."""
        elapsed = time.time() - self._start_time
        phase_config = PHASE_CONFIG.get(phase, {"label": "Unknown", "icon": "•"})
        icon = phase_config["icon"]
        print(f"{icon} [{name.upper()}] [{phase_config['label']}] {message} ({elapsed:.0f}s)", flush=True)

    def add_saved_file(self, filepath: str) -> None:
        """Track a saved file."""
        self._saved_files.append(filepath)

    def start(self) -> None:
        """Start tracking."""
        self._start_time = time.time()
        print("Research Progress", flush=True)
        print("-" * 60, flush=True)

    def stop(self) -> None:
        """Stop tracking."""
        pass

    def print_summary(self, output=None) -> None:
        """Print completion summary."""
        elapsed = time.time() - self._start_time
        print("-" * 60, flush=True)
        print(f"Completed in {elapsed:.1f}s", flush=True)
        if self._saved_files:
            print("\nOutput files:", flush=True)
            for f in self._saved_files:
                print(f"  • {f}", flush=True)

    def __enter__(self) -> "SimpleUI":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def create_status_callback(ui: "RichUI | StreamingUI | SimpleUI") -> Callable[[str, ProviderPhase, str], None]:
    """Create a status callback function for the orchestrator.

    Args:
        ui: The UI instance to update.

    Returns:
        Callback function compatible with orchestrator.
    """

    def callback(provider: str, phase: ProviderPhase, message: str) -> None:
        ui.update_provider(provider, phase, message)

    return callback


def get_ui(
    providers: list[str] | None = None,
    use_rich: bool = True,
    force_terminal: bool = False,
    streaming: bool = False,
) -> "RichUI | StreamingUI | SimpleUI":
    """Get the appropriate UI based on availability and context.

    Args:
        providers: List of provider names to track.
        use_rich: Whether to prefer Rich UI if available.
        force_terminal: Force terminal output for Rich.
        streaming: Use streaming UI for piped contexts.

    Returns:
        Appropriate UI instance.
    """
    # Check for streaming mode (piped output)
    if streaming or os.environ.get('STREAMING_UI', '').lower() in ('1', 'true'):
        return StreamingUI(providers)

    # Check for Rich availability
    if use_rich and RICH_AVAILABLE:
        force = force_terminal or os.environ.get('FORCE_RICH_UI', '').lower() in ('1', 'true')
        return RichUI(providers, force_terminal=force)

    return SimpleUI(providers)


def detect_ui_mode() -> str:
    """Detect the best UI mode for the current environment.

    Returns:
        One of: 'rich', 'streaming', 'simple'
    """
    # Check for explicit override
    if os.environ.get('STREAMING_UI', '').lower() in ('1', 'true'):
        return 'streaming'

    if os.environ.get('FORCE_RICH_UI', '').lower() in ('1', 'true'):
        return 'rich'

    # Check if Rich is available
    if not RICH_AVAILABLE:
        return 'simple'

    # Check if stdout is a TTY (interactive terminal)
    if sys.stdout.isatty():
        return 'rich'

    # For piped/captured output, use streaming
    return 'streaming'
