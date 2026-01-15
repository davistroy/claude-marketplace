"""File comparison utilities for testing."""

import re
from pathlib import Path
from difflib import unified_diff


# Regex patterns for normalizing content
TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?"
)
TIMESTAMP_FILENAME_PATTERN = re.compile(r"\d{8}-\d{6}")


def normalize_timestamps(content: str, placeholder: str = "TIMESTAMP") -> str:
    """
    Replace all timestamps in content with a placeholder.

    Handles:
    - ISO 8601 format: 2026-01-14T10:00:00Z
    - Date only: 2026-01-14
    - Filename format: 20260114-100000

    Args:
        content: The content to normalize
        placeholder: The placeholder string to use

    Returns:
        Content with timestamps replaced
    """
    # Replace ISO format timestamps first
    content = TIMESTAMP_PATTERN.sub(placeholder, content)
    # Replace filename format timestamps
    content = TIMESTAMP_FILENAME_PATTERN.sub(placeholder, content)
    return content


def normalize_whitespace(content: str) -> str:
    """
    Normalize whitespace in content for comparison.

    - Removes trailing whitespace from each line
    - Normalizes line endings to \n
    - Removes trailing newlines

    Args:
        content: The content to normalize

    Returns:
        Content with normalized whitespace
    """
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    return "\n".join(lines).rstrip()


def compare_files(
    expected_path: Path,
    actual_path: Path,
    ignore_timestamps: bool = True,
    ignore_whitespace: bool = True,
) -> tuple[bool, list[str]]:
    """
    Compare two files and return whether they match and any differences.

    Args:
        expected_path: Path to the expected file
        actual_path: Path to the actual file
        ignore_timestamps: Whether to ignore timestamp differences
        ignore_whitespace: Whether to ignore whitespace differences

    Returns:
        Tuple of (match: bool, diff_lines: list[str])
    """
    if not expected_path.exists():
        return False, [f"Expected file not found: {expected_path}"]

    if not actual_path.exists():
        return False, [f"Actual file not found: {actual_path}"]

    expected_content = expected_path.read_text(encoding="utf-8")
    actual_content = actual_path.read_text(encoding="utf-8")

    return compare_content(
        expected_content,
        actual_content,
        ignore_timestamps=ignore_timestamps,
        ignore_whitespace=ignore_whitespace,
        expected_name=expected_path.name,
        actual_name=actual_path.name,
    )


def compare_content(
    expected: str,
    actual: str,
    ignore_timestamps: bool = True,
    ignore_whitespace: bool = True,
    expected_name: str = "expected",
    actual_name: str = "actual",
) -> tuple[bool, list[str]]:
    """
    Compare two strings and return whether they match and any differences.

    Args:
        expected: The expected content
        actual: The actual content
        ignore_timestamps: Whether to ignore timestamp differences
        ignore_whitespace: Whether to ignore whitespace differences
        expected_name: Name for expected in diff output
        actual_name: Name for actual in diff output

    Returns:
        Tuple of (match: bool, diff_lines: list[str])
    """
    if ignore_timestamps:
        expected = normalize_timestamps(expected)
        actual = normalize_timestamps(actual)

    if ignore_whitespace:
        expected = normalize_whitespace(expected)
        actual = normalize_whitespace(actual)

    if expected == actual:
        return True, []

    # Generate unified diff
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)

    diff = list(
        unified_diff(
            expected_lines,
            actual_lines,
            fromfile=expected_name,
            tofile=actual_name,
            lineterm="",
        )
    )

    return False, diff


def compare_markdown_content(
    expected: str,
    actual: str,
    ignore_timestamps: bool = True,
) -> tuple[bool, list[str]]:
    """
    Compare two markdown documents, focusing on content rather than formatting.

    Args:
        expected: The expected markdown content
        actual: The actual markdown content
        ignore_timestamps: Whether to ignore timestamp differences

    Returns:
        Tuple of (match: bool, diff_lines: list[str])
    """
    return compare_content(
        expected,
        actual,
        ignore_timestamps=ignore_timestamps,
        ignore_whitespace=True,
        expected_name="expected.md",
        actual_name="actual.md",
    )


def extract_tbd_markers(content: str) -> list[dict]:
    """
    Extract TBD markers from markdown content.

    Args:
        content: The markdown content to analyze

    Returns:
        List of dictionaries with 'line', 'text', and 'marker' keys
    """
    tbd_pattern = re.compile(r"\[TBD:?\s*([^\]]*)\]", re.IGNORECASE)
    markers = []

    for i, line in enumerate(content.splitlines(), start=1):
        for match in tbd_pattern.finditer(line):
            markers.append({
                "line": i,
                "text": line.strip(),
                "marker": match.group(0),
                "content": match.group(1).strip() if match.group(1) else "",
            })

    return markers


def count_resolved_tbds(original: str, updated: str) -> dict:
    """
    Count how many TBD markers were resolved between two document versions.

    Args:
        original: The original document content
        updated: The updated document content

    Returns:
        Dictionary with 'original_count', 'updated_count', and 'resolved' keys
    """
    original_markers = extract_tbd_markers(original)
    updated_markers = extract_tbd_markers(updated)

    return {
        "original_count": len(original_markers),
        "updated_count": len(updated_markers),
        "resolved": len(original_markers) - len(updated_markers),
    }
