"""Build and serialize a :class:`SyncPlan` — the reviewable unit of a sync.

A plan is the complete, inspectable description of what a sync *would* do:
issues to create, issues to push, tasks to pull/adopt, unresolved conflicts,
and confidentiality findings. It is what ``sync --plan --json`` emits and
what ``sync --dry-run`` summarizes. Building a plan is **pure** — it reads a
classification/resolution and writes nothing; only ``apply`` mutates state.

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
from typing import Any

from task_sync.reconcile.classify import Classification
from task_sync.reconcile.resolve import (
    Conflict,
    CreateAction,
    PullAction,
    PushAction,
    ResolveResult,
    resolve,
)


@dataclass
class SyncPlan:
    """The full set of pending sync actions, ready to serialize or apply."""

    creates: list[CreateAction] = field(default_factory=list)
    pushes: list[PushAction] = field(default_factory=list)
    pulls: list[PullAction] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    confidentiality_findings: list[dict[str, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        """True when the plan would perform no actions at all."""
        return not (self.creates or self.pushes or self.pulls or self.conflicts)

    def to_dict(self) -> dict[str, Any]:
        """A JSON-ready dict with a stable, section-ordered shape."""
        return {
            "creates": [asdict(a) for a in self.creates],
            "pushes": [asdict(a) for a in self.pushes],
            "pulls": [asdict(a) for a in self.pulls],
            "conflicts": [asdict(c) for c in self.conflicts],
            "confidentiality_findings": list(self.confidentiality_findings),
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to canonical JSON (this is the ``--plan --json`` output)."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def build_plan(
    classifications: list[Classification],
    confidentiality_findings: list[dict[str, Any]] | None = None,
) -> SyncPlan:
    """Resolve classifications into a :class:`SyncPlan`. Pure — writes nothing."""
    resolved: ResolveResult = resolve(classifications)
    return SyncPlan(
        creates=resolved.creates,
        pushes=resolved.pushes,
        pulls=resolved.pulls,
        conflicts=resolved.conflicts,
        confidentiality_findings=list(confidentiality_findings or []),
    )


def summarize_plan(plan: SyncPlan) -> str:
    """A short human-readable summary for ``--dry-run`` (no I/O, no mutation)."""
    lines = ["Sync plan (dry run — nothing written):"]
    lines.append(f"  create (new issues):   {len(plan.creates)}")
    lines.append(f"  push   (local -> remote): {len(plan.pushes)}")
    lines.append(f"  pull   (remote -> local): {len(plan.pulls)}")
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
