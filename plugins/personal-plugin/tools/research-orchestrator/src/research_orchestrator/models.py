"""Data models for research orchestration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProviderStatus(Enum):
    """Status of a provider's research execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ProviderResult:
    """Result from a single provider's research execution."""

    provider: str
    status: ProviderStatus
    content: str = ""
    error: str | None = None
    duration_seconds: float = 0.0
    tokens_used: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if the result was successful."""
        return self.status == ProviderStatus.SUCCESS


@dataclass
class ResearchOutput:
    """Complete output from research orchestration."""

    prompt: str
    results: list[ProviderResult]
    timestamp: datetime = field(default_factory=datetime.now)
    total_duration_seconds: float = 0.0
    depth: str = "standard"

    @property
    def successful_results(self) -> list[ProviderResult]:
        """Get only successful results."""
        return [r for r in self.results if r.is_success]

    @property
    def failed_results(self) -> list[ProviderResult]:
        """Get failed results."""
        return [r for r in self.results if not r.is_success]

    @property
    def success_count(self) -> int:
        """Count of successful provider results."""
        return len(self.successful_results)

    @property
    def has_partial_results(self) -> bool:
        """Check if some but not all providers succeeded."""
        return 0 < self.success_count < len(self.results)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt": self.prompt,
            "timestamp": self.timestamp.isoformat(),
            "depth": self.depth,
            "total_duration_seconds": self.total_duration_seconds,
            "results": [
                {
                    "provider": r.provider,
                    "status": r.status.value,
                    "content": r.content,
                    "error": r.error,
                    "duration_seconds": r.duration_seconds,
                    "tokens_used": r.tokens_used,
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
        }
