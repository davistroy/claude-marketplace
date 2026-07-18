"""Generic STRUCTURAL identifier detectors.

Attribution: the structural-regex approach here is adapted from a sibling
repository's redaction stage (``contact-center-lab/pipeline/
stage_B_redaction/patterns.py``). Only the *generic, non-client-specific*
shapes are reused — email, phone, IPv4, internal-hostname TLDs, and
ticket/asset identifiers. The sibling repo's hardcoded brand/company/term
lists are deliberately NOT copied: this is a public repo, and any such term
in this source would itself be a leak. Client-specific sensitive terms are
supplied at runtime as per-repo config (see ``scan.py``), never here.

Everything below is a pure structural pattern — no proper nouns, no brand
names, no client identifiers.
"""

from __future__ import annotations

import re

from task_sync.confidential.finding import (
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    Finding,
    preview,
)

# EMAIL: standard RFC-ish address.
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

# PHONE: US formats — (NNN) NNN-NNNN, NNN-NNN-NNNN, NNN.NNN.NNNN, +1NNNNNNNNNN.
# Hex-boundary guards keep it from matching inside long hex ids.
_PHONE_RE = re.compile(
    r"(?<![a-fA-F0-9])"
    r"(?:\+?1[\s.\-]?)?"
    r"(?:\(\d{3}\)|\d{3})"
    r"[\s.\-]"
    r"\d{3}"
    r"[\s.\-]"
    r"\d{4}"
    r"(?![a-fA-F0-9])"
)

# IP_ADDRESS: IPv4 dotted-quad, each octet 0-255.
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?!\d)"
)

# Internal TLD suffixes — the marker that a hostname is private infra.
_INTERNAL_TLDS = r"\.(?:internal|corp|local|lan|intra|private)"

# INTERNAL_HOSTNAME: a dotted hostname ending in an internal TLD. This
# intentionally does NOT include cc-lab's "2+ dots, any TLD" branch, so a
# public domain like ``example.com`` is never mis-flagged as internal.
_INTERNAL_HOST_RE = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?" + _INTERNAL_TLDS + r"\b",
    re.IGNORECASE,
)

# TICKET_ID: common ITSM record prefixes + 6-10 digits.
_TICKET_RE = re.compile(
    r"\b(?:INC|KB|CHG|REQ|RITM|PRB|SCTASK|TASK|CTASK)\d{6,10}(?!\d)",
    re.IGNORECASE,
)

# ASSET_ID: SN + 6+ digits, ASSET[-]NNNN, or a MAC address.
_ASSET_RE = re.compile(
    r"\bSN\d{6,}\b"
    r"|\bASSET-?\d{4,}\b"
    r"|\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b"
)


# (category, severity, suggestion, compiled) — order sets report priority.
_DETECTORS: list[tuple[str, str, str, re.Pattern[str]]] = [
    ("structural.email", SEVERITY_MEDIUM, "anonymize", _EMAIL_RE),
    ("structural.internal_hostname", SEVERITY_HIGH, "redact", _INTERNAL_HOST_RE),
    ("structural.phone", SEVERITY_MEDIUM, "redact", _PHONE_RE),
    ("structural.ipv4", SEVERITY_LOW, "redact", _IPV4_RE),
    ("structural.ticket_id", SEVERITY_MEDIUM, "redact", _TICKET_RE),
    ("structural.asset_id", SEVERITY_MEDIUM, "redact", _ASSET_RE),
]


def find_structural(text: str) -> list[Finding]:
    """Return every structural-identifier finding in ``text``, by position.

    An email address contains a hostname-like tail; to avoid double-flagging
    the same characters, a match contained within an already-reported span
    is dropped (email, reported first, wins over the hostname inside it).
    """
    findings: list[Finding] = []
    claimed: list[tuple[int, int]] = []
    for category, severity, suggestion, pattern in _DETECTORS:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if any(_overlaps(span, taken) for taken in claimed):
                continue
            claimed.append(span)
            findings.append(
                Finding(
                    span=span,
                    category=category,
                    severity=severity,
                    match_preview=preview(match.group(0)),
                    suggestion=suggestion,
                )
            )
    return sorted(findings, key=lambda f: f.span[0])


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]
