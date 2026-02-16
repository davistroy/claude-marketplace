"""Tests for the bug reporter module."""

import json

import pytest

from research_orchestrator.bug_reporter import BugReporter
from research_orchestrator.models import (
    BugCategory,
    ProviderResult,
    ProviderStatus,
    ResearchOutput,
)


@pytest.fixture
def reporter(tmp_path):
    """Create a BugReporter with a temporary bugs directory."""
    return BugReporter(bugs_dir=tmp_path / "bugs")


@pytest.fixture
def successful_result():
    """Create a successful provider result with substantial content."""
    return ProviderResult(
        provider="claude",
        status=ProviderStatus.SUCCESS,
        content="A" * 5000,  # Long enough for any depth
        duration_seconds=10.0,
        metadata={"model": "claude-opus-4-5-20251101"},
    )


@pytest.fixture
def failed_result():
    """Create a failed provider result."""
    return ProviderResult(
        provider="openai",
        status=ProviderStatus.FAILED,
        error="API key invalid",
        duration_seconds=1.0,
        metadata={"model": "o3-deep-research"},
    )


@pytest.fixture
def timeout_result():
    """Create a timed-out provider result."""
    return ProviderResult(
        provider="gemini",
        status=ProviderStatus.TIMEOUT,
        error="Timed out after 720s",
        duration_seconds=720.0,
        metadata={"model": "deep-research-pro"},
    )


# ---------------------------------------------------------------------------
# detect_and_report tests
# ---------------------------------------------------------------------------


class TestDetectAndReport:
    """Tests for the detect_and_report method."""

    def test_detects_api_error(self, reporter, failed_result):
        """Test detection of API errors."""
        bugs = reporter.detect_and_report(failed_result, "test prompt", "standard")

        assert len(bugs) == 1
        assert bugs[0].category == BugCategory.API_ERROR
        assert bugs[0].severity == "error"
        assert bugs[0].provider == "openai"

    def test_detects_timeout(self, reporter, timeout_result):
        """Test detection of timeouts."""
        bugs = reporter.detect_and_report(timeout_result, "test prompt", "standard")

        assert len(bugs) == 1
        assert bugs[0].category == BugCategory.TIMEOUT
        assert bugs[0].severity == "error"

    def test_detects_empty_response(self, reporter):
        """Test detection of empty/near-empty responses."""
        result = ProviderResult(
            provider="claude",
            status=ProviderStatus.SUCCESS,
            content="Short",  # Less than 100 chars
            duration_seconds=5.0,
            metadata={},
        )
        bugs = reporter.detect_and_report(result, "test prompt", "standard")

        categories = [b.category for b in bugs]
        assert BugCategory.EMPTY_RESPONSE in categories

    def test_detects_truncation_indicator(self, reporter):
        """Test detection of truncation indicators in content."""
        result = ProviderResult(
            provider="claude",
            status=ProviderStatus.SUCCESS,
            content="A" * 5000 + " I apologize, but I'm unable to complete this analysis.",
            duration_seconds=10.0,
            metadata={},
        )
        bugs = reporter.detect_and_report(result, "test prompt", "standard")

        categories = [b.category for b in bugs]
        assert BugCategory.TRUNCATED in categories

    def test_detects_short_response_for_depth(self, reporter):
        """Test detection of suspiciously short responses given depth."""
        result = ProviderResult(
            provider="claude",
            status=ProviderStatus.SUCCESS,
            content="A" * 200,  # Too short for comprehensive (3000)
            duration_seconds=5.0,
            metadata={},
        )
        bugs = reporter.detect_and_report(result, "test prompt", "comprehensive")

        categories = [b.category for b in bugs]
        assert BugCategory.TRUNCATED in categories

    def test_no_bugs_for_good_result(self, reporter, successful_result):
        """Test that a good result produces no bugs."""
        bugs = reporter.detect_and_report(successful_result, "test prompt", "standard")
        assert len(bugs) == 0

    def test_bugs_accumulated(self, reporter, failed_result, timeout_result):
        """Test that bugs are accumulated across calls."""
        reporter.detect_and_report(failed_result, "prompt1", "standard")
        reporter.detect_and_report(timeout_result, "prompt2", "standard")

        assert len(reporter.bugs) == 2

    def test_prompt_preview_truncated(self, reporter, failed_result):
        """Test that long prompts are truncated in preview."""
        long_prompt = "A" * 200
        bugs = reporter.detect_and_report(failed_result, long_prompt, "standard")

        assert len(bugs[0].prompt_preview) <= 103  # 100 chars + "..."
        assert bugs[0].prompt_preview.endswith("...")


# ---------------------------------------------------------------------------
# analyze_output tests
# ---------------------------------------------------------------------------


class TestAnalyzeOutput:
    """Tests for the analyze_output method."""

    def test_detects_partial_failure(self, reporter):
        """Test detection of partial failure."""
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(
                    provider="claude",
                    status=ProviderStatus.SUCCESS,
                    content="Good result",
                ),
                ProviderResult(
                    provider="openai",
                    status=ProviderStatus.FAILED,
                    error="API error",
                ),
            ],
            depth="standard",
        )
        bugs = reporter.analyze_output(output)

        assert len(bugs) == 1
        assert bugs[0].category == BugCategory.PARTIAL_FAILURE
        assert "openai" in bugs[0].error_message

    def test_no_bugs_when_all_succeed(self, reporter):
        """Test no bugs when all providers succeed."""
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(provider="claude", status=ProviderStatus.SUCCESS, content="OK"),
                ProviderResult(provider="openai", status=ProviderStatus.SUCCESS, content="OK"),
            ],
            depth="standard",
        )
        bugs = reporter.analyze_output(output)
        assert len(bugs) == 0

    def test_no_partial_failure_when_all_fail(self, reporter):
        """Test no partial failure bug when all providers fail."""
        output = ResearchOutput(
            prompt="test",
            results=[
                ProviderResult(provider="claude", status=ProviderStatus.FAILED, error="Error"),
                ProviderResult(provider="openai", status=ProviderStatus.FAILED, error="Error"),
            ],
            depth="standard",
        )
        bugs = reporter.analyze_output(output)
        # has_partial_results is False when 0 succeed, so no PARTIAL_FAILURE bug
        assert len(bugs) == 0


# ---------------------------------------------------------------------------
# save_bugs tests
# ---------------------------------------------------------------------------


class TestSaveBugs:
    """Tests for the save_bugs method."""

    def test_save_creates_files(self, reporter, failed_result):
        """Test that save_bugs creates JSON files."""
        reporter.detect_and_report(failed_result, "test", "standard")
        paths = reporter.save_bugs()

        assert len(paths) == 1
        assert paths[0].suffix == ".json"
        assert paths[0].exists()

    def test_saved_json_is_valid(self, reporter, failed_result):
        """Test that saved JSON files are valid and complete."""
        reporter.detect_and_report(failed_result, "test", "standard")
        paths = reporter.save_bugs()

        data = json.loads(paths[0].read_text(encoding="utf-8"))
        assert "id" in data
        assert "category" in data
        assert "provider" in data
        assert data["category"] == "api_error"

    def test_save_no_bugs_returns_empty(self, reporter):
        """Test that saving with no bugs returns empty list."""
        paths = reporter.save_bugs()
        assert paths == []

    def test_save_creates_directory(self, tmp_path, failed_result):
        """Test that bugs directory is created if needed."""
        bugs_dir = tmp_path / "nested" / "bugs"
        reporter = BugReporter(bugs_dir=bugs_dir)
        reporter.detect_and_report(failed_result, "test", "standard")
        paths = reporter.save_bugs()

        assert bugs_dir.exists()
        assert len(paths) == 1


# ---------------------------------------------------------------------------
# clear and get_summary tests
# ---------------------------------------------------------------------------


class TestClearAndSummary:
    """Tests for clear and get_summary methods."""

    def test_clear(self, reporter, failed_result):
        """Test that clear removes all bugs."""
        reporter.detect_and_report(failed_result, "test", "standard")
        assert len(reporter.bugs) > 0

        reporter.clear()
        assert len(reporter.bugs) == 0

    def test_get_summary_empty(self, reporter):
        """Test summary with no bugs."""
        summary = reporter.get_summary()
        assert summary["total"] == 0
        assert summary["by_category"] == {}
        assert summary["by_severity"] == {}
        assert summary["by_provider"] == {}

    def test_get_summary_with_bugs(self, reporter, failed_result, timeout_result):
        """Test summary with multiple bugs."""
        reporter.detect_and_report(failed_result, "test", "standard")
        reporter.detect_and_report(timeout_result, "test", "standard")

        summary = reporter.get_summary()
        assert summary["total"] == 2
        assert "api_error" in summary["by_category"]
        assert "timeout" in summary["by_category"]
        assert "error" in summary["by_severity"]
        assert summary["by_severity"]["error"] == 2


# ---------------------------------------------------------------------------
# Bug ID and timestamp tests
# ---------------------------------------------------------------------------


class TestBugReportCreation:
    """Tests for bug report creation details."""

    def test_bug_id_format(self, reporter, failed_result):
        """Test that bug IDs follow expected format."""
        bugs = reporter.detect_and_report(failed_result, "test", "standard")

        assert bugs[0].id.startswith("bug-")
        assert "openai" in bugs[0].id

    def test_bug_has_timestamp(self, reporter, failed_result):
        """Test that bugs have timestamps."""
        bugs = reporter.detect_and_report(failed_result, "test", "standard")
        assert bugs[0].timestamp is not None

    def test_bug_to_dict(self, reporter, failed_result):
        """Test BugReport.to_dict serialization."""
        bugs = reporter.detect_and_report(failed_result, "test", "standard")
        d = bugs[0].to_dict()

        assert isinstance(d, dict)
        assert d["category"] == "api_error"
        assert d["provider"] == "openai"
        assert "timestamp" in d
