"""Confidentiality scanner: detect leak risks in task content before push.

The package is the leak-critical gate that runs before any task text is
pushed to an issue tracker. It has three concerns, one module each:

* ``secrets`` — the primary tracker-push risk: API keys, tokens, private
  keys. Precise, well-known-format regexes flagged ``CRITICAL``.
* ``patterns`` — generic *structural* identifiers (email, phone, IPv4,
  internal hostnames, ticket/asset IDs) adapted from a sibling repo's
  redaction stage. No client/brand term lists — those would themselves be
  a leak in this public repo.
* ``scan`` / ``apply`` — combine the detectors with a *per-repo*
  sensitive-terms list (supplied at runtime, never hardcoded here), then
  disposition each finding (keep/redact/remove/anonymize) and remember the
  review by content hash.

Stdlib-only, mirroring the rest of ``task_sync``.
"""

from __future__ import annotations

from task_sync.confidential.finding import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    Finding,
)

__all__ = [
    "Finding",
    "SEVERITY_CRITICAL",
    "SEVERITY_HIGH",
    "SEVERITY_MEDIUM",
    "SEVERITY_LOW",
]
