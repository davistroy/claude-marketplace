"""Base provider interface for research execution."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from research_orchestrator.config import Depth, ProviderConfig
from research_orchestrator.models import ProviderPhase, ProviderResult

# Type alias for status callbacks
# New signature: (provider_name, phase, message)
# Legacy signature: (provider_name, message) - still supported for backwards compatibility
StatusCallback = Callable[[str, ProviderPhase, str], None] | Callable[[str, str], None]


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        config: ProviderConfig,
        depth: Depth,
        on_status_update: StatusCallback | None = None,
    ) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration including API key and timeout.
            depth: Research depth level.
            on_status_update: Optional callback for status updates.
                New signature: (provider_name, phase, message)
                Legacy signature: (provider_name, message) also supported.
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

    def _phase_update(self, phase: ProviderPhase, message: str = "") -> None:
        """Emit a phase update with granular status tracking.

        This is the primary method for status updates. It provides structured
        phase information along with a status message.

        Args:
            phase: Current execution phase.
            message: Status message to emit.
        """
        if self._on_status_update:
            # Try new signature first (provider, phase, message)
            try:
                self._on_status_update(self.name, phase, message)
            except TypeError:
                # Fall back to legacy signature (provider, message)
                phase_label = phase.value
                legacy_msg = f"[{phase_label}] {message}" if message else f"[{phase_label}]"
                self._on_status_update(self.name, legacy_msg)

    def _status_update(self, message: str) -> None:
        """Emit a status update during long-running operations.

        DEPRECATED: Use _phase_update() instead for granular phase tracking.

        This method is kept for backwards compatibility. It wraps the message
        with a generic RESEARCHING phase.

        Args:
            message: Status message to emit.
        """
        self._phase_update(ProviderPhase.RESEARCHING, message)
