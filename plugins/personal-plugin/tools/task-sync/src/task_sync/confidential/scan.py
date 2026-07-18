"""Combine every detector into a single per-task scan.

``scan_task`` runs the secret detector, the structural detectors, and a
**per-repo** ``sensitive_terms`` list over each syncable text field
(``title`` and ``body``) and returns one flat, position-ordered list of
:class:`Finding`s tagged with the field they were found in.

The ``sensitive_terms`` list is the ONLY place client/brand terms enter the
system, and it arrives at runtime from the tasks.json config header (see
``TaskList.config``) — it is never hardcoded in this repo. An empty list
(the default) contributes no term findings.
"""

from __future__ import annotations

import re

from task_sync.confidential.finding import SEVERITY_HIGH, Finding
from task_sync.confidential.finding import preview as _preview
from task_sync.confidential.patterns import find_structural
from task_sync.confidential.secrets import find_secrets
from task_sync.models import Task

# Fields that get pushed to a tracker and therefore must be scanned.
_SCANNED_FIELDS = ("title", "body")


def _compile_terms(sensitive_terms: list[str]) -> re.Pattern[str] | None:
    """Build one case-insensitive, whole-word alternation from the terms.

    Returns ``None`` when there are no usable terms so the caller can skip
    term scanning entirely. Terms are ``re.escape``-d, so a config value is
    matched literally — it is data, never an injected pattern.
    """
    cleaned = [term.strip() for term in sensitive_terms if term and term.strip()]
    if not cleaned:
        return None
    # Longest-first so "acme corp" wins over "acme" when both are configured.
    cleaned.sort(key=len, reverse=True)
    alternation = "|".join(re.escape(term) for term in cleaned)
    return re.compile(rf"(?<!\w)(?:{alternation})(?!\w)", re.IGNORECASE)


def _find_terms(text: str, term_re: re.Pattern[str] | None) -> list[Finding]:
    if term_re is None:
        return []
    findings: list[Finding] = []
    for match in term_re.finditer(text):
        findings.append(
            Finding(
                span=(match.start(), match.end()),
                category="sensitive-term",
                severity=SEVERITY_HIGH,
                match_preview=_preview(match.group(0)),
                suggestion="anonymize",
            )
        )
    return findings


def scan_task(task: Task, sensitive_terms: list[str] | None = None) -> list[Finding]:
    """Scan a task's syncable fields for secrets, structural ids, and terms.

    ``sensitive_terms`` is the per-repo config list (from
    ``TaskList.config['sensitive_terms']``); ``None`` or ``[]`` means no
    term matching. Returns findings across ``title`` then ``body``, each
    carrying its originating ``field`` so ``apply`` can transform the right
    string.
    """
    term_re = _compile_terms(sensitive_terms or [])
    findings: list[Finding] = []

    for field_name in _SCANNED_FIELDS:
        text = getattr(task, field_name)
        raw: list[Finding] = []
        raw += find_secrets(text)
        raw += find_structural(text)
        raw += _find_terms(text, term_re)
        # Re-stamp each finding with the field it belongs to and keep the
        # per-field list position-ordered for stable, readable output.
        for finding in sorted(raw, key=lambda f: f.span[0]):
            findings.append(
                Finding(
                    span=finding.span,
                    category=finding.category,
                    severity=finding.severity,
                    match_preview=finding.match_preview,
                    suggestion=finding.suggestion,
                    field=field_name,
                )
            )

    return findings
