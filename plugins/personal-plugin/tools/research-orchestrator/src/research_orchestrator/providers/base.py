"""Base provider interface for research execution."""

from abc import ABC, abstractmethod

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderResult


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ProviderConfig, depth: Depth) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration including API key and timeout.
            depth: Research depth level.
        """
        self.config = config
        self.depth = depth

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        ...

    @abstractmethod
    async def execute(self, prompt: str) -> ProviderResult:
        """Execute research with the provider.

        Args:
            prompt: The research prompt to execute.

        Returns:
            ProviderResult with the research output or error.
        """
        ...

    def _validate_api_key(self) -> None:
        """Validate that API key is available."""
        if not self.config.api_key:
            raise ValueError(f"API key not configured for {self.name}")
