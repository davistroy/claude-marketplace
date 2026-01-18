"""Base provider interface for research execution."""

from abc import ABC, abstractmethod
from typing import Callable

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderResult


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        config: ProviderConfig,
        depth: Depth,
        on_status_update: Callable[[str, str], None] | None = None,
    ) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration including API key and timeout.
            depth: Research depth level.
            on_status_update: Optional callback for status updates.
                Called with (provider_name, status_message).
        """
        self.config = config
        self.depth = depth
        self._on_status_update = on_status_update

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

    def _status_update(self, message: str) -> None:
        """Emit a status update during long-running operations.

        This method is called by providers during polling loops to report
        progress. If a callback is configured, it will be invoked with the
        provider name and message.

        Args:
            message: Status message to emit.
        """
        if self._on_status_update:
            self._on_status_update(self.name, message)
