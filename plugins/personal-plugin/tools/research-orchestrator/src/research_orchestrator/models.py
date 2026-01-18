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


class ProviderPhase(Enum):
    """Granular phase tracking for provider execution."""

    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    THINKING = "thinking"
    RESEARCHING = "researching"
    POLLING = "polling"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BugCategory(Enum):
    """Categories of bugs/anomalies detected during research."""

    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    EMPTY_RESPONSE = "empty_response"
    TRUNCATED = "truncated"
    MALFORMED = "malformed"
    PARTIAL_FAILURE = "partial_failure"


@dataclass
class BugReport:
    """Report of a detected bug/anomaly during research."""

    id: str
    timestamp: datetime
    category: BugCategory
    provider: str
    severity: str  # "warning", "error", "critical"
    prompt_preview: str
    depth: str
    error_message: str | None = None
    duration_seconds: float | None = None
    model_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "provider": self.provider,
            "severity": self.severity,
            "prompt_preview": self.prompt_preview,
            "depth": self.depth,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "model_version": self.model_version,
            "metadata": self.metadata,
        }


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
    bugs: list[BugReport] = field(default_factory=list)

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
            "bugs": [b.to_dict() for b in self.bugs],
        }
