"""The :class:`Finding` value object shared across the confidential package.

A finding is one located leak risk in a task field. Every detector
(secrets, structural patterns, per-repo terms) emits ``Finding``s in the
same shape so ``scan``/``apply`` can treat them uniformly and so the skill
layer can render one consistent list to the human.

Severities are ordered CRITICAL > HIGH > MEDIUM > LOW. ``CRITICAL`` is
reserved for *real secrets* (keys/tokens/private-key blocks) — the things
that must never reach a tracker — so the skill can gate hardest on them.
"""

from __future__ import annotations

from dataclasses import dataclass

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

# Rank for sorting/aggregation; higher is more severe.
SEVERITY_RANK: dict[str, int] = {
    SEVERITY_LOW: 1,
    SEVERITY_MEDIUM: 2,
    SEVERITY_HIGH: 3,
    SEVERITY_CRITICAL: 4,
}


@dataclass(frozen=True)
class Finding:
    """One located leak risk.

    * ``span`` — ``(start, end)`` half-open offsets into ``field``'s text.
    * ``category`` — machine slug of the detector (e.g. ``"secret.github"``,
      ``"structural.email"``, ``"sensitive-term"``).
    * ``severity`` — one of the ``SEVERITY_*`` constants.
    * ``match_preview`` — a short, masked-if-secret preview safe to show a
      human. Never the full secret.
    * ``suggestion`` — the recommended disposition (keep/redact/remove/
      anonymize) for this category.
    * ``field`` — which task field the span indexes: ``"title"`` or
      ``"body"``. Defaults to ``"body"`` for the bare-``text`` detectors.
    """

    span: tuple[int, int]
    category: str
    severity: str
    match_preview: str = ""
    suggestion: str = ""
    field: str = "body"


def preview(match: str, *, mask: bool = False) -> str:
    """Return a short, display-safe preview of a matched substring.

    When ``mask`` is set (secrets), the middle is elided so the full secret
    is never surfaced: ``ghp_1234…def0`` keeps only enough to recognize it.
    Non-secret matches (emails, hostnames) are shown verbatim but truncated.
    """
    match = match.replace("\n", "\\n")
    if mask:
        if len(match) <= 10:
            return match[:2] + "…"
        return f"{match[:6]}…{match[-4:]}"
    if len(match) <= 60:
        return match
    return match[:57] + "…"
