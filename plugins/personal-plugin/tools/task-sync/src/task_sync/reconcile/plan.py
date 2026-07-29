"""Build and serialize a :class:`SyncPlan` — the reviewable unit of a sync.

A plan is the complete, inspectable description of what a sync *would* do:
issues to create, issues to push, tasks to pull/adopt, unresolved conflicts,
issues the adopt window left unadopted, and confidentiality findings. It is
what ``sync --plan --json`` emits and what ``sync --dry-run`` summarizes.
Building a plan is **pure** — it reads a classification/resolution and writes
nothing; only ``apply`` mutates state.

``confidentiality_findings`` starts empty out of :func:`build_plan` itself —
that function stays pure, taking no task content and doing no I/O. It is
populated by the CLI's ``sync --plan``/``--dry-run`` path
(``task_sync.__main__.run_sync``), which scans every ``creates``/``pushes``
task's current content via ``task_sync.confidential.scan.scan_task`` and
assigns the result onto ``plan.confidentiality_findings`` before printing —
still read-only, still writing nothing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from task_sync.reconcile.classify import Classification
from task_sync.reconcile.resolve import (
    Conflict,
    CreateAction,
    Orphan,
    PullAction,
    PushAction,
    ResolveResult,
    resolve,
)


@dataclass
class SyncPlan:
    """The full set of pending sync actions, ready to serialize or apply.

    ``skipped_adopts`` carries the issue numbers the adopt window rejected.
    ``orphans`` carries tasks whose linked issue is missing from the fetched
    list (#181). Both are *not* actions — nothing is applied for them — but
    are part of the plan because leaving them out makes an otherwise-empty
    plan claim the repo is already in sync while N issues need human review.
    """

    creates: list[CreateAction] = field(default_factory=list)
    pushes: list[PushAction] = field(default_factory=list)
    pulls: list[PullAction] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    skipped_adopts: list[int] = field(default_factory=list)
    orphans: list[Orphan] = field(default_factory=list)
    confidentiality_findings: list[dict[str, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        """True when the plan has nothing at all to report.

        Skipped adoptions and orphans count even though they are not actions:
        a plan holding them is *not* "already in sync", and reporting it as
        such is exactly the silent-data-loss story these fields exist to prevent.
        """
        return not (
            self.creates or self.pushes or self.pulls or self.conflicts
            or self.skipped_adopts or self.orphans
        )

    def to_dict(self) -> dict[str, Any]:
        """A JSON-ready dict with a stable, section-ordered shape."""
        return {
            "creates": [asdict(a) for a in self.creates],
            "pushes": [asdict(a) for a in self.pushes],
            "pulls": [asdict(a) for a in self.pulls],
            "conflicts": [asdict(c) for c in self.conflicts],
            "skipped_adopts": list(self.skipped_adopts),
            "orphans": [asdict(o) for o in self.orphans],
            "confidentiality_findings": list(self.confidentiality_findings),
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to canonical JSON (this is the ``--plan --json`` output)."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def build_plan(
    classifications: list[Classification],
    confidentiality_findings: list[dict[str, Any]] | None = None,
    *,
    adopt_closed_within_days: int | None = None,
    now: datetime | None = None,
) -> SyncPlan:
    """Resolve classifications into a :class:`SyncPlan`. Pure — writes nothing.

    ``adopt_closed_within_days`` and ``now`` are threaded straight through to
    :func:`resolve` — see its docstring for the adopt-window semantics.
    """
    resolved: ResolveResult = resolve(
        classifications, adopt_closed_within_days=adopt_closed_within_days, now=now
    )
    return SyncPlan(
        creates=resolved.creates,
        pushes=resolved.pushes,
        pulls=resolved.pulls,
        conflicts=resolved.conflicts,
        skipped_adopts=list(resolved.skipped_adopts),
        orphans=list(resolved.orphans),
        confidentiality_findings=list(confidentiality_findings or []),
    )


def summarize_plan(plan: SyncPlan) -> str:
    """A short human-readable summary for ``--dry-run`` (no I/O, no mutation)."""
    lines = ["Sync plan (dry run — nothing written):"]
    lines.append(f"  create (new issues):   {len(plan.creates)}")
    lines.append(f"  push   (local -> remote): {len(plan.pushes)}")
    lines.append(f"  pull   (remote -> local): {len(plan.pulls)}")
    if plan.skipped_adopts:
        # Placed directly under the pull count because it qualifies it: the
        # honest reading of "pull: 0" is impossible without this line.
        lines.append(
            f"  skipped (closed outside adopt window): {len(plan.skipped_adopts)} "
            "— use --adopt-all to mirror them"
        )
    if plan.orphans:
        # Placed directly after skipped adoptions because they share the same
        # nature: issues that exist but need human review before any action.
        orphan_ids = ", ".join(f"#{o.issue_number}" for o in plan.orphans)
        lines.append(
            f"  orphans (links missing from fetch): {len(plan.orphans)} "
            f"({orphan_ids}) — decide keep/drop"
        )
    lines.append(f"  conflicts (need decision): {len(plan.conflicts)}")
    lines.append(f"  confidentiality findings:  {len(plan.confidentiality_findings)}")

    for c in plan.conflicts:
        lines.append(
            f"  ! conflict: task {c.task_id} <-> issue #{c.issue_number} "
            f"(recommend: {c.recommendation})"
        )

    if plan.is_empty():
        lines.append("  (already in sync — nothing to do)")

    return "\n".join(lines)
