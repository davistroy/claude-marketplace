"""Terminal capability detection and the shared Rich console singleton.

This module owns terminal/console concerns for the CLI:

- ``is_interactive`` / ``supports_unicode`` capability probes
- the Rich import that determines ``RICH_AVAILABLE``
- the process-wide ``_console`` singleton and its accessor ``get_console``

Consumers (``reporting``, ``pipeline``, ``cli``) must reference these
symbols module-qualified (``terminal.get_console()``, ``terminal.RICH_AVAILABLE``)
so a single ``unittest.mock.patch`` on ``visual_explainer.terminal.<symbol>``
intercepts every call site.
"""

from __future__ import annotations

import os
import sys

# Try to import Rich for formatted output
try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Console instance for Rich output
_console: Console | None = None


def is_interactive() -> bool:
    """Check if we're running in an interactive terminal.

    Returns:
        True if stdin is a TTY and we can prompt for input.
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def supports_unicode() -> bool:
    """Check if the console supports Unicode characters.

    Returns:
        True if Unicode spinners/characters should render correctly.
    """
    # On Windows, check for modern terminal (Windows Terminal, ConEmu, etc.)
    if sys.platform == "win32":
        # Windows Terminal sets WT_SESSION
        if os.environ.get("WT_SESSION"):
            return True
        # ConEmu sets ConEmuANSI
        if os.environ.get("ConEmuANSI"):
            return True
        # VS Code terminal
        if os.environ.get("TERM_PROGRAM") == "vscode":
            return True
        # Check for UTF-8 code page (65001) or modern consoles
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # Get console output code page
            code_page = kernel32.GetConsoleOutputCP()
            if code_page == 65001:  # UTF-8
                return True
        except (AttributeError, OSError):
            pass
        # Default to ASCII for legacy Windows cmd.exe
        return False

    # On Unix-like systems, check encoding
    encoding = sys.stdout.encoding or ""
    return encoding.lower() in ("utf-8", "utf8")


def get_console() -> Console:
    """Get or create the Rich console instance.

    Configures the console appropriately for:
    - Interactive vs non-interactive mode
    - Windows vs Unix platforms
    - Unicode vs ASCII-only terminals
    """
    global _console
    if _console is None:
        if RICH_AVAILABLE:
            # Determine terminal capabilities
            interactive = is_interactive()
            unicode_support = supports_unicode()

            if sys.platform == "win32":
                # Windows: use legacy_windows=False for modern terminals,
                # but don't force_terminal when not interactive
                _console = Console(
                    force_terminal=interactive,
                    legacy_windows=not unicode_support,
                )
            else:
                # Unix: configure based on interactivity
                _console = Console(
                    force_terminal=interactive,
                )
        else:
            raise RuntimeError("Rich library not available. Install with: pip install rich")
    return _console
