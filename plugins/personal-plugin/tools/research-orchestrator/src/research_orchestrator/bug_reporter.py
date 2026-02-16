"""Bug detection and reporting for research orchestration."""

import json
from datetime import datetime
from pathlib import Path

from research_orchestrator.models import (
    BugCategory,
    BugReport,
    ProviderResult,
    ProviderStatus,
    ResearchOutput,
)


class BugReporter:
    """Detects and reports bugs/anomalies during research execution."""

    # Thresholds for anomaly detection
    EMPTY_RESPONSE_THRESHOLD = 100  # Characters
    TRUNCATION_INDICATORS = [
        "I apologize, but I'm unable to complete",
        "Due to length constraints",
        "This response has been truncated",
        "[Content truncated]",
        "... (continued)",
        "I'll have to stop here",
    ]
    MIN_EXPECTED_LENGTH = {
        "brief": 500,
        "standard": 1500,
        "comprehensive": 3000,
    }

    def __init__(self, bugs_dir: str | Path = "./bugs") -> None:
        """Initialize the bug reporter.

        Args:
            bugs_dir: Directory to save bug reports.
        """
        self.bugs_dir = Path(bugs_dir)
        self._bugs: list[BugReport] = []

    @property
    def bugs(self) -> list[BugReport]:
        """Get all detected bugs."""
        return self._bugs

    def detect_and_report(
        self,
        result: ProviderResult,
        prompt: str,
        depth: str,
    ) -> list[BugReport]:
        """Detect bugs in a provider result and create reports.

        Args:
            result: The provider result to analyze.
            prompt: The original research prompt.
            depth: The research depth level.

        Returns:
            List of detected bug reports.
        """
        detected: list[BugReport] = []

        # Check for API errors (non-success status)
        if result.status == ProviderStatus.FAILED:
            bug = self._create_bug_report(
                category=BugCategory.API_ERROR,
                provider=result.provider,
                severity="error",
                prompt=prompt,
                depth=depth,
                error_message=result.error,
                duration=result.duration_seconds,
                model=result.metadata.get("model"),
            )
            detected.append(bug)
            self._bugs.append(bug)

        # Check for timeout
        elif result.status == ProviderStatus.TIMEOUT:
            bug = self._create_bug_report(
                category=BugCategory.TIMEOUT,
                provider=result.provider,
                severity="error",
                prompt=prompt,
                depth=depth,
                error_message=result.error or f"Timed out after {result.duration_seconds:.0f}s",
                duration=result.duration_seconds,
                model=result.metadata.get("model"),
            )
            detected.append(bug)
            self._bugs.append(bug)

        # Check successful results for content issues
        elif result.status == ProviderStatus.SUCCESS:
            # Empty or near-empty response
            if len(result.content) < self.EMPTY_RESPONSE_THRESHOLD:
                bug = self._create_bug_report(
                    category=BugCategory.EMPTY_RESPONSE,
                    provider=result.provider,
                    severity="warning",
                    prompt=prompt,
                    depth=depth,
                    error_message=f"Response only {len(result.content)} characters",
                    duration=result.duration_seconds,
                    model=result.metadata.get("model"),
                    metadata={"content_length": len(result.content)},
                )
                detected.append(bug)
                self._bugs.append(bug)

            # Check for truncation indicators
            for indicator in self.TRUNCATION_INDICATORS:
                if indicator.lower() in result.content.lower():
                    bug = self._create_bug_report(
                        category=BugCategory.TRUNCATED,
                        provider=result.provider,
                        severity="warning",
                        prompt=prompt,
                        depth=depth,
                        error_message=f"Truncation detected: '{indicator}'",
                        duration=result.duration_seconds,
                        model=result.metadata.get("model"),
                        metadata={"truncation_indicator": indicator},
                    )
                    detected.append(bug)
                    self._bugs.append(bug)
                    break  # Only report one truncation indicator

            # Check for suspiciously short response given depth
            min_expected = self.MIN_EXPECTED_LENGTH.get(depth, 1000)
            if len(result.content) < min_expected:
                bug = self._create_bug_report(
                    category=BugCategory.TRUNCATED,
                    provider=result.provider,
                    severity="warning",
                    prompt=prompt,
                    depth=depth,
                    error_message=(
                        f"Response shorter than expected for {depth} depth "
                        f"({len(result.content)} < {min_expected} chars)"
                    ),
                    duration=result.duration_seconds,
                    model=result.metadata.get("model"),
                    metadata={
                        "content_length": len(result.content),
                        "expected_minimum": min_expected,
                    },
                )
                detected.append(bug)
                self._bugs.append(bug)

        return detected

    def analyze_output(self, output: ResearchOutput) -> list[BugReport]:
        """Analyze complete research output for systemic issues.

        Args:
            output: The complete research output.

        Returns:
            List of detected systemic bug reports.
        """
        detected: list[BugReport] = []

        # Check for partial failure (some but not all providers failed)
        if output.has_partial_results:
            failed_providers = [r.provider for r in output.failed_results]
            bug = self._create_bug_report(
                category=BugCategory.PARTIAL_FAILURE,
                provider="orchestrator",
                severity="warning",
                prompt=output.prompt,
                depth=output.depth,
                error_message=f"Partial failure: {', '.join(failed_providers)} failed",
                duration=output.total_duration_seconds,
                metadata={
                    "failed_providers": failed_providers,
                    "success_count": output.success_count,
                    "total_count": len(output.results),
                },
            )
            detected.append(bug)
            self._bugs.append(bug)

        return detected

    def _create_bug_report(
        self,
        category: BugCategory,
        provider: str,
        severity: str,
        prompt: str,
        depth: str,
        error_message: str | None = None,
        duration: float | None = None,
        model: str | None = None,
        metadata: dict | None = None,
    ) -> BugReport:
        """Create a bug report with consistent formatting."""
        timestamp = datetime.now()
        bug_id = f"bug-{timestamp.strftime('%Y%m%d-%H%M%S')}-{provider}"

        # Create preview of prompt (first 100 chars)
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt

        return BugReport(
            id=bug_id,
            timestamp=timestamp,
            category=category,
            provider=provider,
            severity=severity,
            prompt_preview=prompt_preview,
            depth=depth,
            error_message=error_message,
            duration_seconds=duration,
            model_version=model,
            metadata=metadata or {},
        )

    def save_bugs(self) -> list[Path]:
        """Save all detected bugs to JSON files.

        Returns:
            List of paths to saved bug report files.
        """
        if not self._bugs:
            return []

        # Create bugs directory if needed
        self.bugs_dir.mkdir(parents=True, exist_ok=True)

        saved_paths: list[Path] = []

        for bug in self._bugs:
            filepath = self.bugs_dir / f"{bug.id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(bug.to_dict(), f, indent=2)
            saved_paths.append(filepath)

        return saved_paths

    def clear(self) -> None:
        """Clear all detected bugs."""
        self._bugs = []

    def get_summary(self) -> dict:
        """Get a summary of detected bugs.

        Returns:
            Dictionary with bug counts by category and severity.
        """
        if not self._bugs:
            return {"total": 0, "by_category": {}, "by_severity": {}, "by_provider": {}}

        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_provider: dict[str, int] = {}

        for bug in self._bugs:
            cat = bug.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            by_severity[bug.severity] = by_severity.get(bug.severity, 0) + 1

            by_provider[bug.provider] = by_provider.get(bug.provider, 0) + 1

        return {
            "total": len(self._bugs),
            "by_category": by_category,
            "by_severity": by_severity,
            "by_provider": by_provider,
        }
