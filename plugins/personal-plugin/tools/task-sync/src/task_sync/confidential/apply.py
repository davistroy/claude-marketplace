"""Apply a review disposition to a task and remember it by content hash.

The four dispositions:

* ``keep``      — no-op on content; the reviewer accepted the text as-is.
* ``redact``    — replace each finding's span with ``[REDACTED]``.
* ``remove``    — delete each finding's span; if that empties the whole
  field, the field is left empty (the field was entirely sensitive).
* ``anonymize`` — replace each finding's span with a STABLE token
  ``<<TERM_ab12cd>>`` derived from a hash of the matched text, so the same
  term always maps to the same token (referential integrity across tasks).

After transforming, the task records
``confidentiality = {decision, reviewed_hash, at}`` where ``reviewed_hash``
is the content hash of the *resulting* task. That gives the review a
memory: :func:`needs_review` returns ``False`` while the content is
unchanged (hash matches) and flips back to ``True`` the moment the content
changes, so a re-scan re-surfaces genuinely new risk without nagging about
text a human already cleared.

The content hash is reused from the reconcile engine so "changed" means
exactly the same thing here as it does for sync.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from task_sync.confidential.finding import Finding
from task_sync.models import Task
from task_sync.reconcile.classify import content_hash

REDACTION_MARK = "[REDACTED]"
VALID_DISPOSITIONS = ("keep", "redact", "remove", "anonymize")

_TRANSFORM_FIELDS = ("title", "body")


def stable_token(term: str) -> str:
    """Return the deterministic anonymization token for ``term``.

    Keyed by a case-folded, stripped hash of the term so ``ACME``, ``acme``
    and `` acme `` all collapse to the same token — the property that lets
    an anonymized corpus stay internally consistent. Pure function of the
    input: same term in, same token out, forever.
    """
    normalized = term.strip().casefold()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:6]
    return f"<<TERM_{digest}>>"


def _replacement(disposition: str, matched: str) -> str:
    if disposition == "redact":
        return REDACTION_MARK
    if disposition == "remove":
        return ""
    if disposition == "anonymize":
        return stable_token(matched)
    raise ValueError(f"no replacement for disposition {disposition!r}")


def _transform_field(value: str, findings: list[Finding], disposition: str) -> str:
    """Apply ``disposition`` to every finding span in one field's text.

    Spans are rewritten right-to-left so each splice leaves the offsets of
    the not-yet-processed (leftward) spans valid. Overlapping spans are
    coalesced — the first (rightmost) wins — so a secret that two detectors
    both flagged is transformed once, cleanly.
    """
    ordered = sorted(findings, key=lambda f: f.span[0], reverse=True)
    result = value
    consumed_start = len(value) + 1
    for finding in ordered:
        start, end = finding.span
        if end > consumed_start:
            # Overlaps a span already handled to the right; skip it.
            continue
        matched = value[start:end]
        result = result[:start] + _replacement(disposition, matched) + result[end:]
        consumed_start = start
    return result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_review(
    task: Task,
    findings: list[Finding],
    disposition: str,
    *,
    at: str | None = None,
) -> Task:
    """Apply ``disposition`` to ``findings`` on ``task`` and record the review.

    Mutates and returns ``task``. ``keep`` changes no content; the other
    three transform each field the findings point at. Regardless of
    disposition, ``task.confidentiality`` is stamped with the decision and
    the post-transformation content hash so the review is remembered.

    ``at`` is injectable for deterministic tests; it defaults to now (UTC).
    """
    if disposition not in VALID_DISPOSITIONS:
        raise ValueError(
            f"invalid disposition {disposition!r}; must be one of {VALID_DISPOSITIONS}"
        )

    if disposition != "keep":
        for field_name in _TRANSFORM_FIELDS:
            field_findings = [f for f in findings if f.field == field_name]
            if not field_findings:
                continue
            new_value = _transform_field(getattr(task, field_name), field_findings, disposition)
            setattr(task, field_name, new_value)

    task.confidentiality = {
        "decision": disposition,
        "reviewed_hash": content_hash(task),
        "at": at or _now_iso(),
    }
    return task


def needs_review(task: Task) -> bool:
    """True if the task has never been reviewed, or changed since it was.

    The gate is purely the content hash: a task with no confidentiality
    record (or no stored hash) needs review; a reviewed task whose current
    content hash still matches ``reviewed_hash`` is honored silently; any
    content edit changes the hash and re-surfaces the task.
    """
    record = task.confidentiality
    if not isinstance(record, dict):
        return True
    reviewed_hash = record.get("reviewed_hash")
    if not reviewed_hash:
        return True
    return content_hash(task) != str(reviewed_hash)
