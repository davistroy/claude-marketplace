"""Secret/token detection — the PRIMARY tracker-push risk.

When a task body is pushed to an issue, a pasted API key or private-key
block is the single worst thing that can leak. This module is the primary
gate for that (GitGuardian remains an advisory CI backstop). It favors
**precision**: the regexes match the *documented shapes* of well-known
credentials so a normal sentence — or a plausible-but-innocent string like
a git SHA or a UUID — does not trip them, while the well-known formats are
never missed.

Design notes:

* Well-known formats (GitHub, OpenAI, AWS, PEM private-key blocks) are
  matched by their exact prefixes/lengths and flagged ``CRITICAL``.
* The generic catch-alls (``Bearer`` tokens, and keyword-anchored
  ``api_key = <value>`` assignments) are deliberately *context-gated*: a
  long high-entropy blob is only flagged when a secret-ish keyword or the
  ``Bearer`` scheme sits right next to it. A bare 40-char hex string (a git
  SHA) or a UUID carries no such context and is intentionally left alone —
  that is the precision/recall trade the plan asks for.

Contains NO client/brand terms and no hardcoded credential values — only
structural shapes. See ``patterns.py`` for the same guarantee on the
structural detectors.
"""

from __future__ import annotations

import math
import re

from task_sync.confidential.finding import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    Finding,
    preview,
)

# --- Well-known credential formats (CRITICAL) ----------------------------

# GitHub tokens: ghp_ (PAT classic), gho_ (OAuth), ghs_ (server-to-server),
# ghu_/ghr_ (user/refresh), plus the fine-grained github_pat_ prefix.
# Classic tokens carry a 36-char base62 body; fine-grained ones are longer.
_GITHUB_RE = re.compile(
    r"\bgh[posur]_[A-Za-z0-9]{36,255}\b"
    r"|\bgithub_pat_[A-Za-z0-9_]{22,255}\b"
)

# OpenAI keys: sk- (optionally sk-proj-) + a long body. Length ≥ 20 keeps
# short "sk-" fragments in ordinary prose from matching.
_OPENAI_RE = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")

# AWS access key id: literal AKIA + 16 uppercase-alnum chars.
_AWS_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")

# PEM private-key block header (RSA/EC/DSA/OPENSSH/PGP or bare).
_PEM_RE = re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----")

# --- Context-gated generic secrets (HIGH) --------------------------------

# HTTP bearer scheme followed by a long opaque token.
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/\-]{20,}={0,2}")

# keyword = "value" — a secret-ish key name immediately preceding a long,
# high-entropy value. The value is captured in group 1 so we flag only the
# secret, not the key name. Length ≥ 16 keeps English words like "required"
# out; the entropy gate below rejects low-randomness values.
_KEYED_RE = re.compile(
    r"(?i)\b(?:api[_-]?key|secret|secret[_-]?key|access[_-]?key|"
    r"auth[_-]?token|token|password|passwd|passphrase|client[_-]?secret)\b"
    r"\s*[:=]\s*"
    r"['\"]?(?P<value>[A-Za-z0-9+/=_\-]{16,})['\"]?"
)

_MIN_KEYED_ENTROPY = 3.0


def _shannon_entropy(value: str) -> float:
    """Shannon entropy (bits/char) of ``value`` — a randomness proxy.

    Real keys spread across many symbols (high entropy); a repeated or
    dictionary-ish placeholder (``password = xxxxxxxxxxxxxxxx``) scores low
    and is rejected, which is what keeps the keyed detector precise.
    """
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _critical(pattern: re.Pattern[str], category: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in pattern.finditer(text):
        findings.append(
            Finding(
                span=(match.start(), match.end()),
                category=category,
                severity=SEVERITY_CRITICAL,
                match_preview=preview(match.group(0), mask=True),
                suggestion="remove",
            )
        )
    return findings


def find_secrets(text: str) -> list[Finding]:
    """Return every secret/token finding in ``text``, ordered by position.

    Well-known formats are ``CRITICAL``; the context-gated generic
    detectors are ``HIGH``. Overlapping matches from different detectors are
    de-duplicated by span so a single credential is reported once (the
    highest-severity hit wins).
    """
    findings: list[Finding] = []

    findings += _critical(_GITHUB_RE, "secret.github", text)
    findings += _critical(_OPENAI_RE, "secret.openai", text)
    findings += _critical(_AWS_RE, "secret.aws", text)
    findings += _critical(_PEM_RE, "secret.private_key", text)

    for match in _BEARER_RE.finditer(text):
        findings.append(
            Finding(
                span=(match.start(), match.end()),
                category="secret.bearer",
                severity=SEVERITY_HIGH,
                match_preview=preview(match.group(0), mask=True),
                suggestion="remove",
            )
        )

    for match in _KEYED_RE.finditer(text):
        value = match.group("value")
        if _shannon_entropy(value) < _MIN_KEYED_ENTROPY:
            continue
        findings.append(
            Finding(
                span=(match.start("value"), match.end("value")),
                category="secret.generic",
                severity=SEVERITY_HIGH,
                match_preview=preview(value, mask=True),
                suggestion="remove",
            )
        )

    return _dedupe_by_span(findings)


def _dedupe_by_span(findings: list[Finding]) -> list[Finding]:
    """Drop findings whose span is contained in a higher-severity finding.

    A GitHub token also looks like a keyed-generic value; reporting it once,
    as ``CRITICAL``, is what the human wants to see.
    """
    from task_sync.confidential.finding import SEVERITY_RANK

    ordered = sorted(
        findings,
        key=lambda f: (-SEVERITY_RANK.get(f.severity, 0), f.span[0]),
    )
    kept: list[Finding] = []
    for finding in ordered:
        if any(_contains(k.span, finding.span) for k in kept):
            continue
        kept.append(finding)
    return sorted(kept, key=lambda f: f.span[0])


def _contains(outer: tuple[int, int], inner: tuple[int, int]) -> bool:
    """True if span ``inner`` overlaps span ``outer`` at all."""
    return inner[0] < outer[1] and outer[0] < inner[1]
