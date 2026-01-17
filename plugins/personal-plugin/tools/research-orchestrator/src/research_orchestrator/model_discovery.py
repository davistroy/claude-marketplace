"""Model discovery and upgrade checking for research providers."""

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from research_orchestrator.providers.anthropic import AnthropicProvider
from research_orchestrator.providers.google import GoogleProvider
from research_orchestrator.providers.openai import OpenAIProvider


@dataclass
class ModelInfo:
    """Information about a model."""

    id: str
    provider: str
    date: datetime | None = None
    is_current: bool = False
    is_newer: bool = False


@dataclass
class UpgradeRecommendation:
    """Recommendation for a model upgrade."""

    provider: str
    current_model: str
    recommended_model: str
    current_date: datetime | None
    recommended_date: datetime | None
    reason: str


def parse_model_date(model_id: str) -> datetime | None:
    """Extract date from model ID if present.

    Handles formats like:
    - claude-opus-4-5-20251101
    - o3-deep-research-2025-06-26
    - deep-research-pro-preview-12-2025
    """
    # Try YYYYMMDD format (Anthropic)
    match = re.search(r"(\d{4})(\d{2})(\d{2})$", model_id)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass

    # Try YYYY-MM-DD format (OpenAI)
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})$", model_id)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass

    # Try MM-YYYY format (Google)
    match = re.search(r"(\d{2})-(\d{4})$", model_id)
    if match:
        try:
            return datetime(int(match.group(2)), int(match.group(1)), 1)
        except ValueError:
            pass

    return None


class ModelDiscovery:
    """Discover available models and check for upgrades."""

    # Patterns to identify relevant models for each provider
    ANTHROPIC_PATTERNS = [
        r"claude-opus-4",
        r"claude-sonnet-4",
    ]

    OPENAI_PATTERNS = [
        r"o3-deep-research",
        r"o4-deep-research",
        r"o4-mini-deep-research",
        r"o5-deep-research",  # Future-proofing
    ]

    GEMINI_PATTERNS = [
        r"deep-research",
    ]

    def __init__(
        self,
        anthropic_key: str | None = None,
        openai_key: str | None = None,
        google_key: str | None = None,
    ):
        """Initialize with API keys."""
        self.anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.google_key = google_key or os.getenv("GOOGLE_API_KEY")

    def _get_anthropic_client(self) -> Any | None:
        """Get Anthropic client if available."""
        if not self.anthropic_key:
            return None
        try:
            import anthropic

            return anthropic.Anthropic(api_key=self.anthropic_key)
        except ImportError:
            return None

    def _get_openai_client(self) -> Any | None:
        """Get OpenAI client if available."""
        if not self.openai_key:
            return None
        try:
            import openai

            return openai.OpenAI(api_key=self.openai_key)
        except ImportError:
            return None

    def _get_google_client(self) -> Any | None:
        """Get Google client if available."""
        if not self.google_key:
            return None
        try:
            from google import genai

            return genai.Client(api_key=self.google_key)
        except ImportError:
            return None

    def discover_anthropic_models(self) -> list[ModelInfo]:
        """Discover available Anthropic models."""
        client = self._get_anthropic_client()
        if not client:
            return []

        models = []
        current_model = AnthropicProvider.get_model()
        current_date = parse_model_date(current_model)

        try:
            # List models from Anthropic API
            response = client.models.list()
            for model in response.data:
                model_id = model.id
                # Check if it matches our patterns
                if any(re.search(pattern, model_id) for pattern in self.ANTHROPIC_PATTERNS):
                    model_date = parse_model_date(model_id)
                    is_current = model_id == current_model
                    is_newer = (
                        model_date is not None
                        and current_date is not None
                        and model_date > current_date
                    )
                    models.append(
                        ModelInfo(
                            id=model_id,
                            provider="anthropic",
                            date=model_date,
                            is_current=is_current,
                            is_newer=is_newer,
                        )
                    )
        except Exception:
            # API might not support listing, return empty
            pass

        return sorted(models, key=lambda m: m.date or datetime.min, reverse=True)

    def discover_openai_models(self) -> list[ModelInfo]:
        """Discover available OpenAI deep research models."""
        client = self._get_openai_client()
        if not client:
            return []

        models = []
        current_model = OpenAIProvider.get_model()
        current_date = parse_model_date(current_model)

        try:
            # List models from OpenAI API
            response = client.models.list()
            for model in response.data:
                model_id = model.id
                # Check if it matches our patterns (deep research models)
                if any(re.search(pattern, model_id) for pattern in self.OPENAI_PATTERNS):
                    model_date = parse_model_date(model_id)
                    is_current = model_id == current_model
                    is_newer = (
                        model_date is not None
                        and current_date is not None
                        and model_date > current_date
                    )
                    models.append(
                        ModelInfo(
                            id=model_id,
                            provider="openai",
                            date=model_date,
                            is_current=is_current,
                            is_newer=is_newer,
                        )
                    )
        except Exception:
            pass

        return sorted(models, key=lambda m: m.date or datetime.min, reverse=True)

    def discover_google_agents(self) -> list[ModelInfo]:
        """Discover available Google deep research agents.

        Note: Google's API may not have a list endpoint for agents,
        so we may need to check known agent names.
        """
        client = self._get_google_client()
        if not client:
            return []

        models = []
        current_agent = GoogleProvider.get_agent()
        current_date = parse_model_date(current_agent)

        # Google may not have a public list API for agents
        # We'll check known agent patterns
        known_agents = [
            "deep-research-pro-preview-12-2025",
            "deep-research-pro-preview-01-2026",  # Possible future
            "deep-research-pro-preview-02-2026",
        ]

        for agent_id in known_agents:
            agent_date = parse_model_date(agent_id)
            is_current = agent_id == current_agent
            is_newer = (
                agent_date is not None
                and current_date is not None
                and agent_date > current_date
            )
            models.append(
                ModelInfo(
                    id=agent_id,
                    provider="google",
                    date=agent_date,
                    is_current=is_current,
                    is_newer=is_newer,
                )
            )

        return sorted(models, key=lambda m: m.date or datetime.min, reverse=True)

    def check_for_upgrades(self) -> list[UpgradeRecommendation]:
        """Check all providers for available upgrades."""
        recommendations = []

        # Check Anthropic
        anthropic_models = self.discover_anthropic_models()
        newer_anthropic = [m for m in anthropic_models if m.is_newer]
        if newer_anthropic:
            current = AnthropicProvider.get_model()
            best = newer_anthropic[0]
            recommendations.append(
                UpgradeRecommendation(
                    provider="Anthropic (Claude)",
                    current_model=current,
                    recommended_model=best.id,
                    current_date=parse_model_date(current),
                    recommended_date=best.date,
                    reason=f"Newer model available ({best.date.strftime('%Y-%m-%d') if best.date else 'unknown date'})",
                )
            )

        # Check OpenAI
        openai_models = self.discover_openai_models()
        newer_openai = [m for m in openai_models if m.is_newer]
        if newer_openai:
            current = OpenAIProvider.get_model()
            best = newer_openai[0]
            recommendations.append(
                UpgradeRecommendation(
                    provider="OpenAI (o3 Deep Research)",
                    current_model=current,
                    recommended_model=best.id,
                    current_date=parse_model_date(current),
                    recommended_date=best.date,
                    reason=f"Newer model available ({best.date.strftime('%Y-%m-%d') if best.date else 'unknown date'})",
                )
            )

        # Check Google
        google_models = self.discover_google_agents()
        newer_google = [m for m in google_models if m.is_newer]
        if newer_google:
            current = GoogleProvider.get_agent()
            best = newer_google[0]
            recommendations.append(
                UpgradeRecommendation(
                    provider="Google (Gemini Deep Research)",
                    current_model=current,
                    recommended_model=best.id,
                    current_date=parse_model_date(current),
                    recommended_date=best.date,
                    reason=f"Newer agent available ({best.date.strftime('%Y-%m') if best.date else 'unknown date'})",
                )
            )

        return recommendations

    def get_current_models(self) -> dict[str, str]:
        """Get currently configured models for all providers."""
        return {
            "anthropic": AnthropicProvider.get_model(),
            "openai": OpenAIProvider.get_model(),
            "google": GoogleProvider.get_agent(),
        }

    def format_upgrade_report(self, recommendations: list[UpgradeRecommendation]) -> str:
        """Format upgrade recommendations as a readable report."""
        if not recommendations:
            return "✓ All models are up to date."

        lines = ["## Model Upgrade Recommendations\n"]
        for rec in recommendations:
            lines.append(f"### {rec.provider}")
            lines.append(f"- **Current:** `{rec.current_model}`")
            lines.append(f"- **Recommended:** `{rec.recommended_model}`")
            lines.append(f"- **Reason:** {rec.reason}")
            lines.append("")

        lines.append("### How to Upgrade")
        lines.append("Update the following in your `.env` file:\n")
        lines.append("```bash")
        for rec in recommendations:
            if "Anthropic" in rec.provider:
                lines.append(f"ANTHROPIC_MODEL={rec.recommended_model}")
            elif "OpenAI" in rec.provider:
                lines.append(f"OPENAI_MODEL={rec.recommended_model}")
            elif "Google" in rec.provider:
                lines.append(f"GEMINI_AGENT={rec.recommended_model}")
        lines.append("```")

        return "\n".join(lines)
