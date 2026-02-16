"""First-run API key setup wizard for visual-explainer.

Detects missing API keys, provides step-by-step instructions,
validates keys against the APIs, and creates the .env file.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import httpx

# Set PYTHONIOENCODING for Windows console compatibility
if "PYTHONIOENCODING" not in os.environ:
    os.environ["PYTHONIOENCODING"] = "utf-8"


def is_interactive() -> bool:
    """Check if we're running in an interactive terminal.

    Returns:
        True if stdin is a TTY and we can prompt for input.
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def supports_unicode() -> bool:
    """Check if the console supports Unicode characters.

    Returns:
        True if Unicode characters should render correctly.
    """
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
        # Check for UTF-8 code page (65001)
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            code_page = kernel32.GetConsoleOutputCP()
            if code_page == 65001:
                return True
        except (AttributeError, OSError):
            pass
        return False

    encoding = sys.stdout.encoding or ""
    return encoding.lower() in ("utf-8", "utf8")

# Try to import Rich for formatted output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Try to import anthropic for key validation
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class KeyStatus(TypedDict):
    """Status of an API key check."""

    present: bool
    valid: bool | None  # None = not checked
    error: str | None


class APIKeySetupResult(TypedDict):
    """Result of the API key setup process."""

    google: KeyStatus
    anthropic: KeyStatus
    env_file_created: bool
    env_file_path: str | None
    skipped: bool


# Console instance for Rich output
_console: Console | None = None


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
            interactive = is_interactive()
            unicode_support = supports_unicode()

            if sys.platform == "win32":
                _console = Console(
                    force_terminal=interactive,
                    legacy_windows=not unicode_support,
                )
            else:
                _console = Console(
                    force_terminal=interactive,
                )
        else:
            raise RuntimeError("Rich library not available. Install with: pip install rich")
    return _console


def check_api_keys() -> dict[str, KeyStatus]:
    """Check which API keys are present and their format validity.

    Returns:
        Dictionary with 'google' and 'anthropic' key statuses.
    """
    results: dict[str, KeyStatus] = {}

    # Check Google API key
    google_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if google_key and len(google_key) > 20:
        results["google"] = {"present": True, "valid": None, "error": None}
    else:
        results["google"] = {
            "present": bool(google_key),
            "valid": False if google_key else None,
            "error": "Key too short" if google_key else None,
        }

    # Check Anthropic API key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key and anthropic_key.startswith("sk-ant-"):
        results["anthropic"] = {"present": True, "valid": None, "error": None}
    elif anthropic_key:
        results["anthropic"] = {
            "present": True,
            "valid": False,
            "error": "Invalid format (should start with 'sk-ant-')",
        }
    else:
        results["anthropic"] = {"present": False, "valid": None, "error": None}

    return results


async def validate_google_key(key: str, timeout: float = 10.0) -> tuple[bool, str | None]:
    """Validate Google API key with a minimal API call.

    Args:
        key: The Google API key to validate.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not key or len(key) < 20:
        return False, "Key is too short or empty"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": key},
            )

            if response.status_code == 200:
                return True, None
            elif response.status_code == 400:
                return False, "Invalid API key format"
            elif response.status_code == 403:
                return False, "API key is invalid or the API is not enabled for this project"
            else:
                return False, f"Unexpected response: {response.status_code}"

    except httpx.TimeoutException:
        return False, "Connection timed out - check your internet connection"
    except httpx.ConnectError:
        return False, "Could not connect to Google API - check your internet connection"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_anthropic_key(key: str) -> tuple[bool, str | None]:
    """Validate Anthropic API key with a minimal API call.

    Args:
        key: The Anthropic API key to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not ANTHROPIC_AVAILABLE:
        # If anthropic package not installed, just check format
        if key and key.startswith("sk-ant-"):
            return True, None
        return False, "Invalid key format (should start with 'sk-ant-')"

    if not key or not key.startswith("sk-ant-"):
        return False, "Invalid key format (should start with 'sk-ant-')"

    try:
        client = anthropic.Anthropic(api_key=key)
        # Minimal API call to verify the key works
        client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
        return True, None
    except anthropic.AuthenticationError:
        return False, "Authentication failed - invalid API key"
    except anthropic.PermissionDeniedError:
        return False, "Permission denied - check your API key permissions"
    except anthropic.RateLimitError:
        # Rate limit means the key is valid but we're being rate limited
        return True, None
    except anthropic.APIConnectionError:
        return False, "Could not connect to Anthropic API - check your internet connection"
    except Exception as e:
        # Other errors might mean the key is valid but something else is wrong
        error_str = str(e).lower()
        if "authentication" in error_str or "invalid" in error_str:
            return False, f"Authentication error: {str(e)}"
        # If we can't determine, assume valid (conservative approach)
        return True, None


def create_env_file(
    google_key: str | None,
    anthropic_key: str | None,
    path: Path | None = None,
) -> Path:
    """Create .env file with provided keys.

    Args:
        google_key: Google API key (or None to comment out).
        anthropic_key: Anthropic API key (or None to comment out).
        path: Path for .env file. Defaults to current working directory.

    Returns:
        Path to the created .env file.
    """
    if path is None:
        path = Path.cwd() / ".env"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Visual Explainer API Keys
# Generated: {timestamp}
# Documentation: https://github.com/davistroy/claude-marketplace

"""

    if google_key:
        content += f"GOOGLE_API_KEY={google_key}\n"
    else:
        content += "# GOOGLE_API_KEY=your-google-api-key-here\n"

    if anthropic_key:
        content += f"ANTHROPIC_API_KEY={anthropic_key}\n"
    else:
        content += "# ANTHROPIC_API_KEY=your-anthropic-api-key-here\n"

    # Write the file
    path.write_text(content, encoding="utf-8")

    # Ensure .gitignore includes .env
    _update_gitignore(path.parent)

    return path


def _update_gitignore(directory: Path) -> None:
    """Update .gitignore to include .env if not already present.

    Args:
        directory: Directory containing or to contain .gitignore.
    """
    gitignore = directory / ".gitignore"

    if gitignore.exists():
        existing = gitignore.read_text(encoding="utf-8")
        # Check if .env is already in gitignore (as a line or part of a pattern)
        lines = existing.strip().split("\n")
        env_patterns = [".env", "*.env", ".env*"]
        for pattern in env_patterns:
            if any(line.strip() == pattern for line in lines):
                return  # Already covered
        # Add .env
        gitignore.write_text(existing.rstrip() + "\n.env\n", encoding="utf-8")
    else:
        gitignore.write_text(".env\n", encoding="utf-8")


def display_header() -> None:
    """Display the setup wizard header."""
    console = get_console()

    header = Panel(
        "[bold white]This tool requires two API keys:[/bold white]\n"
        "  [cyan]* Google Gemini API[/cyan] - for image generation\n"
        "  [cyan]* Anthropic API[/cyan] - for image evaluation",
        title="[bold cyan]API Key Setup Required[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(header)


def display_key_status(status: dict[str, KeyStatus]) -> None:
    """Display the current status of API keys."""
    console = get_console()

    console.print("\n[bold white]Current Status:[/bold white]")

    for name, key_status in status.items():
        display_name = "GOOGLE_API_KEY" if name == "google" else "ANTHROPIC_API_KEY"

        if key_status["present"] and key_status["valid"] is not False:
            icon = "[green]OK[/green]"
            msg = "configured"
        elif key_status["present"] and key_status["valid"] is False:
            icon = "[yellow]!![/yellow]"
            msg = f"invalid - {key_status['error']}" if key_status["error"] else "invalid format"
        else:
            icon = "[red]X[/red]"
            msg = "not found"

        console.print(f"  {icon} {display_name} - {msg}")


def display_google_instructions() -> None:
    """Display instructions for obtaining a Google API key."""
    console = get_console()

    instructions = """[bold white]Step 1: Google Gemini API Key[/bold white]

To get your Google Gemini API key:

[cyan]1.[/cyan] Go to Google AI Studio:
   [link=https://aistudio.google.com/apikey]https://aistudio.google.com/apikey[/link]

[cyan]2.[/cyan] Sign in with your Google account

[cyan]3.[/cyan] Click [bold]"Create API Key"[/bold]

[cyan]4.[/cyan] Select or create a Google Cloud project
   (A default project works fine)

[cyan]5.[/cyan] Copy the generated API key
   (It looks like: [dim]AIzaSy...[/dim])"""

    panel = Panel(
        instructions,
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def display_anthropic_instructions() -> None:
    """Display instructions for obtaining an Anthropic API key."""
    console = get_console()

    instructions = """[bold white]Step 2: Anthropic API Key[/bold white]

To get your Anthropic API key:

[cyan]1.[/cyan] Go to the Anthropic Console:
   [link=https://console.anthropic.com/settings/keys]https://console.anthropic.com/settings/keys[/link]

[cyan]2.[/cyan] Sign in or create an Anthropic account

[cyan]3.[/cyan] Click [bold]"Create Key"[/bold]

[cyan]4.[/cyan] Give it a name (e.g., "visual-explainer")

[cyan]5.[/cyan] Copy the key immediately (it won't be shown again!)
   (It looks like: [dim]sk-ant-api03-...[/dim])

[yellow]Note:[/yellow] New accounts get $5 free credits. After that,
you'll need to add a payment method."""

    panel = Panel(
        instructions,
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(panel)


def display_cost_information() -> None:
    """Display API cost information summary."""
    console = get_console()

    # Create cost table
    table = Table(title="Estimated Costs Per Generation Session", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Cost Per Unit", justify="right")
    table.add_column("Notes")

    table.add_row("Gemini image generation", "~$0.10/image", "4K images may cost slightly more")
    table.add_row("Claude concept analysis", "~$0.02/document", "One-time per document")
    table.add_row("Claude image evaluation", "~$0.03/evaluation", "Multiple if refinement needed")

    console.print()
    console.print(table)

    # Example scenarios
    console.print("\n[bold white]Example Scenarios:[/bold white]")
    console.print("  [dim]*[/dim] Simple doc, 1 image, 2 attempts: [green]~$0.28[/green]")
    console.print("  [dim]*[/dim] Medium doc, 3 images, avg 2.3 attempts: [green]~$0.95[/green]")
    console.print("  [dim]*[/dim] Complex doc, 5 images, avg 3 attempts: [yellow]~$2.10[/yellow]")

    # Only wait for input in interactive mode
    if is_interactive():
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()


def display_env_file_created(path: Path, google_key: str | None, anthropic_key: str | None) -> None:
    """Display confirmation that .env file was created."""
    console = get_console()

    # Show preview of file contents (with masked keys)
    google_display = f"GOOGLE_API_KEY={google_key[:10]}..." if google_key else "# GOOGLE_API_KEY=..."
    anthropic_display = (
        f"ANTHROPIC_API_KEY={anthropic_key[:12]}..." if anthropic_key else "# ANTHROPIC_API_KEY=..."
    )

    preview = f"""[dim]# Visual Explainer API Keys[/dim]
[dim]# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}[/dim]

{google_display}
{anthropic_display}"""

    panel = Panel(
        preview,
        title=f"[bold green]Created: {path}[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)

    console.print("[green]OK[/green] .env file created successfully!")
    console.print("[green]OK[/green] Added .env to .gitignore (if not already present)")


def prompt_for_key(
    key_name: str,
    validator: callable,
    is_async: bool = False,
) -> tuple[str | None, bool]:
    """Prompt user for an API key with validation.

    Args:
        key_name: Display name for the key (e.g., "Google API").
        validator: Function to validate the key.
        is_async: Whether the validator is async.

    Returns:
        Tuple of (key or None, was_skipped).
    """
    console = get_console()

    while True:
        key = Prompt.ask(
            f"\nPaste your {key_name} key here (or [cyan]'skip'[/cyan] to set up later)",
            password=True,
        )

        if key.lower().strip() == "skip":
            console.print(f"[yellow]Skipped {key_name} key setup[/yellow]")
            return None, True

        # Clean up the key
        key = key.strip()

        if not key:
            console.print("[red]No key entered. Please try again.[/red]")
            continue

        # Validate the key
        console.print(f"[dim]Validating {key_name} key...[/dim]")

        if is_async:
            valid, error = asyncio.run(validator(key))
        else:
            valid, error = validator(key)

        if valid:
            console.print(f"[green]OK[/green] {key_name} key validated successfully!")
            return key, False
        else:
            console.print(f"[red]X[/red] Validation failed: {error}")
            retry = Prompt.ask("Try again?", choices=["y", "n"], default="y")
            if retry.lower() != "y":
                return None, True


async def run_setup_wizard(
    force: bool = False,
    env_path: Path | None = None,
) -> APIKeySetupResult:
    """Run the interactive API key setup wizard.

    Args:
        force: Force re-running setup even if keys are present.
        env_path: Custom path for .env file.

    Returns:
        Setup result with key statuses and file creation info.

    Raises:
        RuntimeError: If called in non-interactive mode.
    """
    # Non-interactive mode: cannot run wizard
    if not is_interactive():
        raise RuntimeError(
            "Cannot run API key setup wizard in non-interactive mode. "
            "Set GOOGLE_API_KEY and ANTHROPIC_API_KEY environment variables, "
            "or run interactively with: visual-explainer --setup-keys"
        )

    console = get_console()

    # Check current key status
    status = check_api_keys()

    # Determine if setup is needed
    google_needed = not status["google"]["present"] or status["google"]["valid"] is False or force
    anthropic_needed = (
        not status["anthropic"]["present"] or status["anthropic"]["valid"] is False or force
    )

    if not google_needed and not anthropic_needed:
        console.print("[green]OK[/green] All API keys are already configured!")
        return APIKeySetupResult(
            google=status["google"],
            anthropic=status["anthropic"],
            env_file_created=False,
            env_file_path=None,
            skipped=False,
        )

    # Display header and current status
    display_header()
    display_key_status(status)

    # Collect keys
    google_key: str | None = os.getenv("GOOGLE_API_KEY") if not google_needed else None
    anthropic_key: str | None = os.getenv("ANTHROPIC_API_KEY") if not anthropic_needed else None
    any_skipped = False

    # Google API key
    if google_needed:
        display_google_instructions()
        key, skipped = prompt_for_key("Google API", validate_google_key, is_async=True)
        if key:
            google_key = key
            status["google"] = {"present": True, "valid": True, "error": None}
        if skipped:
            any_skipped = True

    # Anthropic API key
    if anthropic_needed:
        display_anthropic_instructions()
        key, skipped = prompt_for_key("Anthropic API", validate_anthropic_key, is_async=False)
        if key:
            anthropic_key = key
            status["anthropic"] = {"present": True, "valid": True, "error": None}
        if skipped:
            any_skipped = True

    # Create .env file if we have at least one key
    env_file_created = False
    env_file_path: str | None = None

    if google_key or anthropic_key:
        console.print("\n[bold white]Creating .env File[/bold white]")
        path = create_env_file(google_key, anthropic_key, env_path)
        display_env_file_created(path, google_key, anthropic_key)
        env_file_created = True
        env_file_path = str(path)

        # Display cost information
        display_cost_information()
    else:
        console.print(
            "\n[yellow]No keys were configured. "
            "Run with --setup-keys to try again.[/yellow]"
        )

    return APIKeySetupResult(
        google=status["google"],
        anthropic=status["anthropic"],
        env_file_created=env_file_created,
        env_file_path=env_file_path,
        skipped=any_skipped,
    )


def run_setup_wizard_sync(
    force: bool = False,
    env_path: Path | None = None,
) -> APIKeySetupResult:
    """Synchronous wrapper for run_setup_wizard.

    Args:
        force: Force re-running setup even if keys are present.
        env_path: Custom path for .env file.

    Returns:
        Setup result with key statuses and file creation info.
    """
    return asyncio.run(run_setup_wizard(force=force, env_path=env_path))


def check_keys_and_prompt_if_missing() -> bool:
    """Check for API keys and prompt for setup if missing.

    This is the main entry point for CLI integration. It checks if
    keys are present and valid, and runs the setup wizard if needed.

    In non-interactive mode, this only checks for key presence without
    prompting, and returns False if keys are missing.

    Returns:
        True if all required keys are available, False otherwise.
    """
    # Load .env file if present
    from dotenv import load_dotenv

    load_dotenv(override=True)

    # Check current status
    status = check_api_keys()

    # Both keys needed for full functionality
    google_ok = status["google"]["present"]
    anthropic_ok = status["anthropic"]["present"]

    if google_ok and anthropic_ok:
        return True

    # Non-interactive mode: cannot prompt, just report status
    if not is_interactive():
        missing = []
        if not google_ok:
            missing.append("GOOGLE_API_KEY")
        if not anthropic_ok:
            missing.append("ANTHROPIC_API_KEY")
        print(f"Missing required API keys: {', '.join(missing)}")
        print("Set environment variables or run: visual-explainer --setup-keys")
        return False

    # Interactive mode: offer setup wizard
    console = get_console()

    console.print()
    console.print("[yellow]Missing required API keys detected.[/yellow]")

    missing = []
    if not google_ok:
        missing.append("GOOGLE_API_KEY")
    if not anthropic_ok:
        missing.append("ANTHROPIC_API_KEY")

    console.print(f"  Missing: {', '.join(missing)}")
    console.print()

    run_setup = Prompt.ask(
        "Would you like to set up API keys now?",
        choices=["y", "n"],
        default="y",
    )

    if run_setup.lower() == "y":
        result = run_setup_wizard_sync(force=True)
        return result["google"]["present"] and result["anthropic"]["present"]
    else:
        console.print(
            "\n[dim]You can run setup later with: "
            "visual-explainer --setup-keys[/dim]"
        )
        return False


# CLI flag support
def handle_setup_keys_flag() -> int:
    """Handle the --setup-keys CLI flag.

    Returns:
        Exit code (0 for success, 1 for failure/skip).
    """
    # Check for non-interactive mode first
    if not is_interactive():
        print("Error: --setup-keys requires an interactive terminal.")
        print("Set environment variables instead:")
        print("  export GOOGLE_API_KEY=your-google-api-key")
        print("  export ANTHROPIC_API_KEY=your-anthropic-api-key")
        return 1

    console = get_console()

    try:
        result = run_setup_wizard_sync(force=True)

        if result["google"]["present"] and result["anthropic"]["present"]:
            console.print(
                "\n[bold green]Setup complete![/bold green] "
                "You're ready to generate images."
            )
            return 0
        elif result["skipped"]:
            console.print("\n[yellow]Setup incomplete - some keys were skipped.[/yellow]")
            return 1
        else:
            console.print("\n[red]Setup failed - could not configure API keys.[/red]")
            return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Setup error: {e}[/red]")
        return 1


if __name__ == "__main__":
    # Allow running this module directly for testing
    sys.exit(handle_setup_keys_flag())
