"""Configuration for research orchestration."""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


class Depth(Enum):
    """Research depth levels with provider-specific configurations."""

    BRIEF = "brief"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"

    def get_anthropic_budget(self) -> int:
        """Get thinking budget tokens for Anthropic."""
        return {
            Depth.BRIEF: 4_000,
            Depth.STANDARD: 10_000,
            Depth.COMPREHENSIVE: 32_000,
        }[self]

    def get_openai_effort(self) -> str:
        """Get reasoning effort for OpenAI (legacy, kept for compatibility)."""
        return {
            Depth.BRIEF: "medium",
            Depth.STANDARD: "high",
            Depth.COMPREHENSIVE: "xhigh",
        }[self]

    def get_openai_reasoning_summary(self) -> str:
        """Get reasoning summary level for OpenAI deep research.

        'detailed' provides more thorough reasoning output.
        'auto' lets the model decide the appropriate level.
        """
        return {
            Depth.BRIEF: "auto",
            Depth.STANDARD: "detailed",
            Depth.COMPREHENSIVE: "detailed",
        }[self]

    def get_gemini_thinking_level(self) -> str:
        """Get thinking level for Gemini."""
        return {
            Depth.BRIEF: "low",
            Depth.STANDARD: "high",
            Depth.COMPREHENSIVE: "high",
        }[self]


ProviderName = Literal["claude", "openai", "gemini"]

VALID_PROVIDERS: set[ProviderName] = {"claude", "openai", "gemini"}


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    name: ProviderName
    api_key: str | None = None
    timeout_seconds: float = 180.0
    max_retries: int = 3

    @property
    def is_available(self) -> bool:
        """Check if the provider has a valid API key."""
        return bool(self.api_key)


@dataclass
class ResearchConfig:
    """Configuration for a research execution."""

    prompt: str
    sources: list[ProviderName] = field(default_factory=lambda: ["claude", "openai", "gemini"])
    depth: Depth = Depth.STANDARD
    output_dir: str = "./reports"
    timeout_seconds: float = 180.0
    max_retries: int = 3

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.prompt:
            raise ValueError("Research prompt cannot be empty")

        invalid_sources = set(self.sources) - VALID_PROVIDERS
        if invalid_sources:
            raise ValueError(f"Invalid sources: {invalid_sources}. Valid: {VALID_PROVIDERS}")

        if isinstance(self.depth, str):
            self.depth = Depth(self.depth)

    def get_provider_configs(self) -> list[ProviderConfig]:
        """Get configurations for all selected providers."""
        configs = []
        for source in self.sources:
            api_key = self._get_api_key(source)
            configs.append(
                ProviderConfig(
                    name=source,
                    api_key=api_key,
                    timeout_seconds=self.timeout_seconds,
                    max_retries=self.max_retries,
                )
            )
        return configs

    def _get_api_key(self, source: ProviderName) -> str | None:
        """Get API key for a provider from environment."""
        key_map = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }
        return os.getenv(key_map[source])

    def get_missing_api_keys(self) -> list[str]:
        """Get list of missing API keys for selected sources."""
        missing = []
        for config in self.get_provider_configs():
            if not config.is_available:
                key_name = {
                    "claude": "ANTHROPIC_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "gemini": "GOOGLE_API_KEY",
                }[config.name]
                missing.append(key_name)
        return missing
