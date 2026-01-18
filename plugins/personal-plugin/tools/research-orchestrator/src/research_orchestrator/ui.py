"""Rich terminal UI for research progress display."""

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

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Phase display configurations
PHASE_CONFIG = {
    ProviderPhase.INITIALIZING: {"label": "initializing", "style": "dim white"},
    ProviderPhase.CONNECTING: {"label": "connecting", "style": "cyan"},
    ProviderPhase.THINKING: {"label": "thinking", "style": "yellow"},
    ProviderPhase.RESEARCHING: {"label": "researching", "style": "blue"},
    ProviderPhase.POLLING: {"label": "polling", "style": "magenta"},
    ProviderPhase.PROCESSING: {"label": "processing", "style": "cyan"},
    ProviderPhase.COMPLETED: {"label": "completed", "style": "green"},
    ProviderPhase.FAILED: {"label": "failed", "style": "red"},
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
        return f"{minutes}m {seconds}s"

    @property
    def is_complete(self) -> bool:
        """Check if the provider has finished (completed or failed)."""
        return self.phase in (ProviderPhase.COMPLETED, ProviderPhase.FAILED)


class RichUI:
    """Rich terminal UI for displaying research progress."""

    def __init__(self, providers: list[str] | None = None) -> None:
        """Initialize the Rich UI.

        Args:
            providers: List of provider names to track.
        """
        if not RICH_AVAILABLE:
            raise ImportError("rich package required. Install with: pip install rich")

        self.console = Console()
        self._providers: dict[str, ProviderState] = {}
        self._live: Live | None = None
        self._start_time = time.time()

        # Initialize provider states
        if providers:
            for provider in providers:
                self._providers[provider] = ProviderState(name=provider)

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
            self._live.update(self._create_table())

    def _create_table(self) -> Panel:
        """Create the progress table."""
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))

        table.add_column("Provider", style="bold", width=10)
        table.add_column("Phase", width=14)
        table.add_column("Status", width=35)
        table.add_column("Elapsed", justify="right", width=8)

        for name, state in self._providers.items():
            # Provider name with color
            provider_color = PROVIDER_COLORS.get(name, "white")
            provider_text = Text(name.upper(), style=f"bold {provider_color}")

            # Phase with styling
            phase_config = PHASE_CONFIG.get(state.phase, {"label": "unknown", "style": "white"})
            phase_text = Text(f"[{phase_config['label']}]", style=phase_config["style"])

            # Status message (truncate if needed)
            status = state.status_message[:35] if state.status_message else ""
            status_text = Text(status)

            # Elapsed time
            elapsed = state.elapsed_formatted
            if state.is_complete:
                elapsed_style = "green" if state.phase == ProviderPhase.COMPLETED else "red"
                elapsed_text = Text(f"({elapsed})", style=elapsed_style)
            else:
                elapsed_text = Text(elapsed)

            table.add_row(provider_text, phase_text, status_text, elapsed_text)

        # Total elapsed time
        total_elapsed = time.time() - self._start_time
        if total_elapsed < 60:
            total_str = f"{total_elapsed:.0f}s"
        else:
            minutes = int(total_elapsed // 60)
            seconds = int(total_elapsed % 60)
            total_str = f"{minutes}m {seconds}s"

        return Panel(
            table,
            title="Research Progress",
            subtitle=f"Total: {total_str}",
            border_style="cyan",
        )

    def start(self) -> None:
        """Start the live display."""
        self._start_time = time.time()
        self._live = Live(
            self._create_table(),
            console=self.console,
            refresh_per_second=2,
            transient=False,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the live display."""
        if self._live:
            self._live.update(self._create_table())  # Final update
            self._live.stop()
            self._live = None

    def print_summary(self) -> None:
        """Print a summary after completion."""
        self.console.print()

        completed = sum(1 for s in self._providers.values() if s.phase == ProviderPhase.COMPLETED)
        failed = sum(1 for s in self._providers.values() if s.phase == ProviderPhase.FAILED)
        total = len(self._providers)

        if completed == total:
            self.console.print(f"[green]All {total} providers completed successfully[/green]")
        elif failed == total:
            self.console.print(f"[red]All {total} providers failed[/red]")
        else:
            self.console.print(
                f"[yellow]Research completed: {completed}/{total} succeeded, "
                f"{failed} failed[/yellow]"
            )

        # Per-provider summary
        for name, state in self._providers.items():
            color = "green" if state.phase == ProviderPhase.COMPLETED else "red"
            self.console.print(
                f"  [{color}]{name.upper()}[/{color}]: {state.elapsed_formatted}"
            )

    def __enter__(self) -> "RichUI":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def create_status_callback(ui: RichUI) -> Callable[[str, ProviderPhase, str], None]:
    """Create a status callback function for the orchestrator.

    Args:
        ui: The RichUI instance to update.

    Returns:
        Callback function compatible with orchestrator.
    """

    def callback(provider: str, phase: ProviderPhase, message: str) -> None:
        ui.update_provider(provider, phase, message)

    return callback


class SimpleUI:
    """Simple fallback UI when Rich is not available."""

    def __init__(self, providers: list[str] | None = None) -> None:
        """Initialize the simple UI."""
        self._providers: set[str] = set(providers) if providers else set()
        self._start_time = time.time()

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
        phase_label = PHASE_CONFIG.get(phase, {"label": "unknown"})["label"]
        print(f"[{name.upper()}] [{phase_label}] {message} ({elapsed:.0f}s)")

    def start(self) -> None:
        """Start tracking (no-op for simple UI)."""
        self._start_time = time.time()
        print("Research Progress")
        print("-" * 40)

    def stop(self) -> None:
        """Stop tracking (no-op for simple UI)."""
        pass

    def print_summary(self) -> None:
        """Print completion summary."""
        elapsed = time.time() - self._start_time
        print("-" * 40)
        print(f"Completed in {elapsed:.1f}s")

    def __enter__(self) -> "SimpleUI":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def get_ui(providers: list[str] | None = None, use_rich: bool = True) -> RichUI | SimpleUI:
    """Get the appropriate UI based on availability.

    Args:
        providers: List of provider names to track.
        use_rich: Whether to prefer Rich UI if available.

    Returns:
        RichUI or SimpleUI instance.
    """
    if use_rich and RICH_AVAILABLE:
        return RichUI(providers)
    return SimpleUI(providers)
