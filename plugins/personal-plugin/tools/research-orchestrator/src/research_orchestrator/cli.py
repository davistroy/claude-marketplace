"""Command-line interface for research orchestrator."""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from research_orchestrator.bug_reporter import BugReporter
from research_orchestrator.config import Depth, ResearchConfig
from research_orchestrator.model_discovery import ModelDiscovery
from research_orchestrator.models import ProviderPhase
from research_orchestrator.orchestrator import ResearchOrchestrator

# Try to import Rich UI
try:
    from research_orchestrator.ui import RichUI, create_status_callback, RICH_AVAILABLE
except ImportError:
    RICH_AVAILABLE = False
    RichUI = None
    create_status_callback = None


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="research-orchestrator",
        description="Orchestrate parallel deep research across multiple LLM providers",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    execute_parser = subparsers.add_parser(
        "execute", help="Execute research across providers"
    )
    execute_parser.add_argument(
        "--prompt",
        "-p",
        required=True,
        help="The research prompt to execute",
    )
    execute_parser.add_argument(
        "--sources",
        "-s",
        default="claude,openai,gemini",
        help="Comma-separated list of providers (default: claude,openai,gemini)",
    )
    execute_parser.add_argument(
        "--depth",
        "-d",
        choices=["brief", "standard", "comprehensive"],
        default="standard",
        help="Research depth level (default: standard)",
    )
    execute_parser.add_argument(
        "--output-dir",
        "-o",
        default="./reports",
        help="Output directory for results (default: ./reports)",
    )
    execute_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    execute_parser.add_argument(
        "--timeout",
        type=float,
        default=720.0,
        help="Timeout in seconds per provider (default: 720 for deep research)",
    )

    subparsers.add_parser(
        "check-providers", help="Check which providers are available"
    )

    subparsers.add_parser("list-depths", help="List available depth levels")

    check_models_parser = subparsers.add_parser(
        "check-models", help="Check for newer model versions"
    )
    check_models_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    # check-ready command
    check_ready_parser = subparsers.add_parser(
        "check-ready", help="Check if all dependencies and API keys are configured"
    )
    check_ready_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (default for this command)",
    )

    return parser


def status_callback_legacy(provider: str, message: str) -> None:
    """Print status updates to stderr (legacy format)."""
    print(f"[{provider}] {message}", file=sys.stderr)


def status_callback_phase(provider: str, phase: ProviderPhase, message: str) -> None:
    """Print status updates to stderr with phase info."""
    print(f"[{provider}] [{phase.value}] {message}", file=sys.stderr)


def run_execute(args: argparse.Namespace) -> int:
    """Execute the research command."""
    sources = [s.strip() for s in args.sources.split(",")]

    try:
        config = ResearchConfig(
            prompt=args.prompt,
            sources=sources,  # type: ignore
            depth=Depth(args.depth),
            output_dir=args.output_dir,
            timeout_seconds=args.timeout,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    missing_keys = config.get_missing_api_keys()
    if missing_keys:
        print("Warning: Missing API keys:", file=sys.stderr)
        for key in missing_keys:
            print(f"  - {key}", file=sys.stderr)
        print("Research will only use providers with available keys.", file=sys.stderr)

    # Set up bug reporter
    bug_reporter = BugReporter(bugs_dir=Path(args.output_dir) / "bugs")

    if args.json:
        # JSON mode: no status updates
        orchestrator = ResearchOrchestrator(bug_reporter=bug_reporter)
        output = asyncio.run(orchestrator.execute(config))
        print(json.dumps(output.to_dict(), indent=2))
    elif RICH_AVAILABLE and RichUI is not None:
        # Rich UI mode
        ui = RichUI(providers=sources)
        callback = create_status_callback(ui)
        orchestrator = ResearchOrchestrator(
            on_status_update=callback,
            bug_reporter=bug_reporter
        )

        with ui:
            output = asyncio.run(orchestrator.execute(config))

        ui.print_summary()
        print_results(output, args.output_dir)
    else:
        # Fallback: simple text output
        orchestrator = ResearchOrchestrator(
            on_status_update=status_callback_phase,
            bug_reporter=bug_reporter
        )
        output = asyncio.run(orchestrator.execute(config))
        print_results(output, args.output_dir)

    # Save bug reports if any were detected
    if bug_reporter.bugs:
        saved_paths = bug_reporter.save_bugs()
        if saved_paths:
            print(f"\nBug reports saved: {len(saved_paths)} files", file=sys.stderr)
            for path in saved_paths[:3]:  # Show first 3
                print(f"  - {path}", file=sys.stderr)
            if len(saved_paths) > 3:
                print(f"  ... and {len(saved_paths) - 3} more", file=sys.stderr)

    return 0 if output.success_count > 0 else 1


def print_results(output, output_dir: str) -> None:
    """Print formatted results and save to files."""
    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)

    print(f"\nPrompt: {output.prompt[:100]}...")
    print(f"Depth: {output.depth}")
    print(f"Duration: {output.total_duration_seconds:.1f}s")
    print(f"Successful: {output.success_count}/{len(output.results)}")

    for result in output.results:
        print(f"\n--- {result.provider.upper()} ---")
        print(f"Status: {result.status.value}")
        if result.error:
            print(f"Error: {result.error}")
        print(f"Duration: {result.duration_seconds:.1f}s")

        if result.is_success:
            preview = result.content[:500]
            if len(result.content) > 500:
                preview += "..."
            print(f"Content preview:\n{preview}")

    if output.success_count > 0:
        save_results(output, output_dir)


def save_results(output, output_dir: str) -> None:
    """Save results to files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for result in output.successful_results:
        filename = f"research-{result.provider}-{timestamp}.md"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Research Results - {result.provider.upper()}\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Depth:** {output.depth}\n")
            f.write(f"**Duration:** {result.duration_seconds:.1f}s\n\n")
            f.write("---\n\n")
            f.write(result.content)

        print(f"\nSaved: {filepath}")


def run_check_providers(_args: argparse.Namespace) -> int:
    """Check provider availability."""
    orchestrator = ResearchOrchestrator()
    availability = asyncio.run(orchestrator.check_providers())

    print("Provider Availability:")
    print("-" * 30)
    for provider, available in availability.items():
        status = "Available" if available else "Not configured"
        print(f"  {provider}: {status}")

    return 0


def run_list_depths(_args: argparse.Namespace) -> int:
    """List available depth levels."""
    print("Available Depth Levels:")
    print("-" * 60)
    print(f"{'Level':<15} {'Claude tokens':<15} {'OpenAI effort':<15} {'Est. Cost':<10}")
    print("-" * 60)

    depths = [
        (Depth.BRIEF, "~$0.75"),
        (Depth.STANDARD, "~$1.85"),
        (Depth.COMPREHENSIVE, "~$5.00"),
    ]

    for depth, cost in depths:
        print(
            f"{depth.value:<15} "
            f"{depth.get_anthropic_budget():<15,} "
            f"{depth.get_openai_effort():<15} "
            f"{cost:<10}"
        )

    return 0


def run_check_models(args: argparse.Namespace) -> int:
    """Check for newer model versions."""
    discovery = ModelDiscovery()

    # Get current models
    current = discovery.get_current_models()

    # Check for upgrades
    recommendations = discovery.check_for_upgrades()

    if args.json:
        output = {
            "current_models": current,
            "upgrades_available": len(recommendations) > 0,
            "recommendations": [
                {
                    "provider": rec.provider,
                    "current_model": rec.current_model,
                    "recommended_model": rec.recommended_model,
                    "current_date": rec.current_date.isoformat() if rec.current_date else None,
                    "recommended_date": rec.recommended_date.isoformat()
                    if rec.recommended_date
                    else None,
                    "reason": rec.reason,
                }
                for rec in recommendations
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print("Model Version Check")
        print("=" * 50)
        print("\nCurrent Models:")
        print(f"  Anthropic: {current['anthropic']}")
        print(f"  OpenAI:    {current['openai']}")
        print(f"  Gemini:    {current['google']}")

        if recommendations:
            print("\n" + discovery.format_upgrade_report(recommendations))
        else:
            print("\n✓ All models are up to date.")

    return 0


def run_check_ready(args: argparse.Namespace) -> int:
    """Check if all dependencies and API keys are configured."""
    import importlib
    import shutil

    result = {
        "python_packages": {},
        "api_keys": {},
        "optional_tools": {},
    }

    # Check Python packages
    packages = [
        ("anthropic", "anthropic"),
        ("openai", "openai"),
        ("google-genai", "google.genai"),
        ("rich", "rich"),
        ("python-dotenv", "dotenv"),
        ("pydantic", "pydantic"),
        ("tenacity", "tenacity"),
    ]

    for package_name, import_name in packages:
        try:
            # Use importlib for proper nested module handling
            mod = importlib.import_module(import_name)

            # Try to get version
            version = getattr(mod, "__version__", "unknown")
            result["python_packages"][package_name] = {"ok": True, "version": version}
        except (ImportError, ModuleNotFoundError):
            result["python_packages"][package_name] = {"ok": False, "version": None}

    # Check API keys
    api_keys = [
        ("ANTHROPIC_API_KEY", "claude"),
        ("OPENAI_API_KEY", "openai"),
        ("GOOGLE_API_KEY", "gemini"),
    ]

    for key_name, provider in api_keys:
        value = os.getenv(key_name)
        is_present = bool(value and len(value) > 0)
        result["api_keys"][key_name] = {
            "ok": is_present,
            "present": is_present,
            "provider": provider,
        }

    # Check optional tools
    optional_tools = [
        ("pandoc", "Document conversion"),
    ]

    for tool_name, description in optional_tools:
        tool_path = shutil.which(tool_name)
        result["optional_tools"][tool_name] = {
            "ok": tool_path is not None,
            "path": tool_path,
            "description": description,
        }

    # Always output as JSON (this command is meant for programmatic use)
    print(json.dumps(result, indent=2))

    # Return success if all required packages and at least one API key are available
    all_packages_ok = all(p["ok"] for p in result["python_packages"].values())
    any_api_key_ok = any(k["ok"] for k in result["api_keys"].values())

    return 0 if (all_packages_ok and any_api_key_ok) else 1


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "execute": run_execute,
        "check-providers": run_check_providers,
        "list-depths": run_list_depths,
        "check-models": run_check_models,
        "check-ready": run_check_ready,
    }

    handler = commands.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
