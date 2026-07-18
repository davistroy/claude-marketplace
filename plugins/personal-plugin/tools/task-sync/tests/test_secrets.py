"""Tests for the secret/token detector.

Positive corpus: every well-known credential format the plan names must be
flagged CRITICAL (or HIGH for the context-gated generics). Negative corpus:
ordinary prose and plausible-but-innocent strings (git SHAs, UUIDs,
placeholders, short prefixes) must NOT be flagged — precision is the point.
"""

from __future__ import annotations

import pytest

from task_sync.confidential.finding import SEVERITY_CRITICAL, SEVERITY_HIGH
from task_sync.confidential.secrets import find_secrets

# A 36-char base62 body for the GitHub token formats.
_GH_BODY = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


@pytest.mark.parametrize(
    "text, category",
    [
        (f"token is ghp_{_GH_BODY} ok", "secret.github"),
        (f"token is gho_{_GH_BODY} ok", "secret.github"),
        (f"token is ghs_{_GH_BODY} ok", "secret.github"),
        ("pat github_pat_11ABCDE0123456789abcdef_x end", "secret.github"),
        ("key sk-A1b2C3d4E5f6G7h8I9j0K1l2 end", "secret.openai"),
        ("aws AKIAIOSFODNN7EXAMPLE end", "secret.aws"),
        ("-----BEGIN RSA PRIVATE KEY-----", "secret.private_key"),
        ("-----BEGIN PRIVATE KEY-----", "secret.private_key"),
        ("-----BEGIN OPENSSH PRIVATE KEY-----", "secret.private_key"),
    ],
)
def test_well_known_formats_flagged_critical(text: str, category: str) -> None:
    findings = find_secrets(text)
    assert findings, f"expected a finding in {text!r}"
    match = next(f for f in findings if f.category == category)
    assert match.severity == SEVERITY_CRITICAL


def test_ghp_token_flagged_critical() -> None:
    """Acceptance: a body containing a ghp_… token is flagged CRITICAL."""
    findings = find_secrets(f"Please deploy with ghp_{_GH_BODY} thanks")
    assert len(findings) == 1
    assert findings[0].category == "secret.github"
    assert findings[0].severity == SEVERITY_CRITICAL
    # The preview never contains the full secret.
    assert _GH_BODY not in findings[0].match_preview


def test_bearer_token_flagged_high() -> None:
    findings = find_secrets("Authorization: Bearer A1b2C3d4E5f6G7h8I9j0K1l2M3")
    assert any(f.category == "secret.bearer" and f.severity == SEVERITY_HIGH for f in findings)


def test_keyed_high_entropy_value_flagged_high() -> None:
    findings = find_secrets('api_key = "aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY"')
    assert any(f.category == "secret.generic" and f.severity == SEVERITY_HIGH for f in findings)


# --- Negative corpus: NONE of these may be flagged -----------------------

_NEGATIVES = [
    "The quick brown fox jumps over the lazy dog.",
    "Fixed the bug in the reconcile engine; see PR #42.",
    # A 40-char git SHA carries no secret-keyword context.
    "Commit a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0 broke the build.",
    # A UUID is not a credential.
    "Request id 550e8400-e29b-41d4-a716-446655440000 timed out.",
    # A short placeholder value under the length/entropy floor.
    "Set api_key = your-key-here in the config.",
    # A low-entropy value in a secret field is a placeholder, not a secret.
    'password = "xxxxxxxxxxxxxxxxxxxx"',
    # "sk-" prefix that is far too short to be an OpenAI key.
    "The sk-123 label is not a token.",
    # "ghp_" mentioned as a prefix, with no 36-char body following.
    "Use the ghp_ prefix for GitHub tokens.",
    # keyword with a short/plain value.
    "password: required",
    # Hyphenated words that embed 'sk-' mid-word.
    "risk-based testing keeps task-sync healthy.",
]


@pytest.mark.parametrize("text", _NEGATIVES)
def test_negative_corpus_not_flagged(text: str) -> None:
    assert find_secrets(text) == []


def test_multiple_secrets_all_reported() -> None:
    text = f"a ghp_{_GH_BODY} b AKIAIOSFODNN7EXAMPLE c"
    cats = {f.category for f in find_secrets(text)}
    assert cats == {"secret.github", "secret.aws"}


def test_overlapping_detectors_deduped_to_critical() -> None:
    """A github token in a `token = ...` assignment reports once, CRITICAL."""
    findings = find_secrets(f'token = "ghp_{_GH_BODY}"')
    assert len(findings) == 1
    assert findings[0].severity == SEVERITY_CRITICAL


def test_shannon_entropy_empty_is_zero() -> None:
    from task_sync.confidential.secrets import _shannon_entropy

    assert _shannon_entropy("") == 0.0


def test_preview_masks_secrets_and_truncates_long_matches() -> None:
    from task_sync.confidential.finding import preview

    assert preview("ab", mask=True) == "ab…"  # short masked form
    long_text = "x" * 80
    assert preview(long_text).endswith("…") and len(preview(long_text)) == 58
