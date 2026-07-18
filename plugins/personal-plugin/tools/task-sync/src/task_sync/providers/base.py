"""Provider abstraction: normalized Issue model + the Provider protocol.

All reconcile logic (Phase 3) speaks only this interface — it never touches
the `gh` CLI or Gitea's REST API directly. Two adapters implement it:
`github.py` (shells out to the `gh` CLI via `subprocess`) and `gitea.py`
(talks to the Gitea REST API via stdlib `urllib`). Both normalize their
tracker's JSON into this same `Issue` shape so reconcile code never
branches on which concrete adapter it holds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

# Normalized issue state. Trackers use their own vocabularies (gh: "OPEN"/
# "CLOSED"; Gitea: "open"/"closed") — both adapters lowercase to this pair.
VALID_ISSUE_STATES: tuple[str, ...] = ("open", "closed")


def parse_aware_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp (as returned by gh/Gitea) into an aware datetime.

    Both providers return UTC timestamps with a trailing `Z`, which
    `datetime.fromisoformat` only accepts natively from Python 3.11 —
    normalize `Z` to `+00:00` first so this works on 3.10 too. A naive
    result (no offset in the source string) is assumed UTC. Returns `None`
    for `None`/empty input, since some fields (e.g. `closed_at`) are
    legitimately absent.
    """
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@dataclass
class Issue:
    """A tracker issue, normalized to a single shape regardless of provider."""

    number: int
    title: str
    body: str
    state: str
    labels: list[str]
    milestone: str | None
    updated_at: datetime
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.number, int):
            raise ValueError(f"'number' must be an int, got {type(self.number).__name__}")

        if self.state not in VALID_ISSUE_STATES:
            raise ValueError(
                f"invalid state {self.state!r} for issue #{self.number}; "
                f"must be one of {VALID_ISSUE_STATES}"
            )

        if not isinstance(self.labels, list) or not all(
            isinstance(label, str) for label in self.labels
        ):
            raise ValueError(f"'labels' must be a list of strings for issue #{self.number}")

        if self.updated_at.tzinfo is None:
            raise ValueError(f"'updated_at' must be timezone-aware for issue #{self.number}")

        if self.closed_at is not None and self.closed_at.tzinfo is None:
            raise ValueError(f"'closed_at' must be timezone-aware for issue #{self.number}")


@runtime_checkable
class Provider(Protocol):
    """The interface every tracker adapter implements.

    Phase 3's reconcile engine speaks only this interface — it never
    branches on which concrete adapter (`GithubProvider`, `GiteaProvider`)
    it holds.
    """

    def list_issues(self, state: str = "all") -> list[Issue]:
        """Return all issues matching `state` ('open', 'closed', or 'all')."""
        ...

    def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        milestone: str | None = None,
    ) -> Issue:
        """Create a new issue on the tracker and return its normalized form."""
        ...

    def update_issue(self, number: int, **fields: Any) -> Issue:
        """Update one or more fields (title, body, labels, milestone, state, ...)."""
        ...

    def set_state(self, number: int, state: str) -> None:
        """Open or close an issue ('open' or 'closed')."""
        ...

    def ensure_labels(self, names: list[str]) -> None:
        """Create any of `names` that don't already exist on the tracker."""
        ...

    def ensure_milestone(self, name: str) -> None:
        """Create `name` as a milestone on the tracker if it doesn't already exist."""
        ...

    def visibility(self) -> str:
        """Return 'public' or 'private' for the repo this provider is bound to."""
        ...
