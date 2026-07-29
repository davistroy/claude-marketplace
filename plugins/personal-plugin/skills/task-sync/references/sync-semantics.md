# Sync Semantics

How `sync` decides what to do, in full. The engine is pure and read-only up
through plan construction — nothing here ever writes a file or calls a
tracker's write API on its own; only `sync --apply` executes a plan.

## Three-way classification

Every task/issue pair (matched by `issue_number`) is classified against its
**last synced base** — the `last_synced` snapshot recorded on the task the
previous time it was pushed, pulled, created, or adopted (`hash` of the
task's syncable fields plus the issue's `updated_at` at that moment):

| Local changed since base | Remote changed since base | Classification | Resulting action |
|---|---|---|---|
| no | no | `UNCHANGED` | nothing |
| yes | no | `CHANGED_LOCAL` | push (update the issue) |
| no | yes | `CHANGED_REMOTE` | pull (update the task) |
| yes | yes | `CHANGED_BOTH` | **conflict** — surfaced, never auto-applied |
| n/a (no `issue_number`) | n/a | `NEW_LOCAL` | create (new issue) |
| n/a | issue with no matching task | `NEW_REMOTE` | pull (adopt: create a new task, subject to the adoption window — see Prune below) |

An orphaned task (a local task whose issue no longer appears in the tracker's
returned issue list, though its `issue_number` is still recorded) is classified
as `ORPHAN_LOCAL`. `resolve()` does not convert it to a push or a create; instead,
it is surfaced as an `Orphan` record in the plan for human inspection. The user
must then decide whether to re-create the issue, re-adopt a different one, or
delete the local task (#181).

## Field mapping (task ↔ issue)

The five local statuses collapse onto an issue's `open`/`closed` state plus
at most one `status/*` label:

| Status | Issue state | `status/*` label |
|---|---|---|
| `backlog` | open | `status/backlog` |
| `todo` | open | (none — "open, nothing else said") |
| `in-progress` | open | `status/in-progress` |
| `blocked` | open | `status/blocked` |
| `done` | closed | (none — closed already encodes it) |

Priority maps to a `priority/P0`..`priority/P4` label the same way. A `priority/*` or `status/*` label whose suffix the tool does not recognize is left alone: it stays in the user label set and is never removed from the issue (#208).
Everything else on `labels` passes through untouched. This mapping is exactly
invertible on the managed fields, so a value that has not otherwise changed
survives a full round trip (push then pull, or vice versa) unchanged.

## Conflict resolution (never automatic)

A `CHANGED_BOTH` conflict carries both projections (`local` — what the task
would push as; `remote` — what the issue would pull as), each side's
`updated_at`, and a `recommendation` (`"local"` or `"remote"`, last-write-wins
by `updated_at`; ties favor `"remote"` since the tracker is the shared source
of record). The recommendation is advisory only — render it as a hint next to
each conflict, never pre-select it, and never apply a conflict that the user
did not explicitly decide. An undecided conflict is left exactly as-is by
`apply` and will resurface, unchanged, on the next `sync --plan`.

## Prune

On `--apply`, after every create/push/pull/conflict-decision is executed,
`done` tasks whose issue has been closed for longer than
`config.prune_closed_after_days` (default 30) are dropped from `tasks.json`.
The issue itself is left closed on the tracker as the permanent record —
pruning only removes the row from the local file/table, it never deletes or
reopens anything remotely.

Adoption (the `NEW_REMOTE` row above) is gated separately, by its own
`config.adopt_closed_within_days` key (default `0`) — not by
`prune_closed_after_days`. `0` means adopt open issues only: a closed issue
is skipped no matter how recently it closed (the check is
`now - closed_at > timedelta(days=window)`, which is true for every closed
issue when `window` is `0`). A larger value is a grace window — e.g. `3` also
adopts issues closed within the last 3 days, with the same strict-greater-than
comparison so exactly-N-days-ago is still adopted. An absent key (a
`tasks.json` predating this setting) resolves to `0`, not to the prune
window. An already-adopted task is unaffected by the window — only
first-time adoption is gated; a `CHANGED_REMOTE` update to an adopted task
always applies in full, no matter how long ago the issue closed. Pass `sync
--adopt-all` to disable the adoption window and mirror every issue in
history regardless of when it closed.

Adoption and prune answer different questions on purpose — "is this issue
actionable enough to be worth tracking at all?" versus "how long do we keep
completed work?" — and are therefore separate keys rather than one shared
threshold.

Every issue the window rejects is still visible, never silently dropped:
`sync --plan --json` lists their issue numbers under `skipped_adopts` (see
below), and `--dry-run` surfaces a count with the same `--adopt-all` pointer.

## What `--plan --json` returns

```json
{
  "creates": [{"task_id": "t-ab12cd", "fields": {"title": "...", "body": "...", "state": "open", "labels": [...], "milestone": null}}],
  "pushes": [{"task_id": "t-ef34gh", "issue_number": 12, "fields": {...}}],
  "pulls": [{"issue_number": 15, "task_id": null, "fields": {"title": "...", "body": "...", "status": "todo", "priority": null, "labels": [...], "milestone": null}, "issue_updated_at": "...", "issue_closed_at": null}],
  "conflicts": [{"task_id": "t-ij56kl", "issue_number": 9, "local": {...}, "remote": {...}, "recommendation": "remote", "local_updated_at": "...", "remote_updated_at": "...", "remote_closed_at": null}],
  "skipped_adopts": [174, 173, 172, 156],
  "confidentiality_findings": []
}
```

The key order is fixed: `creates`, `pushes`, `pulls`, `conflicts`,
`skipped_adopts`, `confidentiality_findings`.

A `pulls` entry with `task_id: null` is an **adopt** (a brand-new task will be
created from the issue); a non-null `task_id` is an update to an existing
task.

`skipped_adopts` is a JSON array of tracker issue *numbers* (not task ids —
these issues have no local task yet), in classification order, e.g. `[174,
173, 172, 156]`. Each is a `NEW_REMOTE` issue the adopt window (see Prune
above) left unadopted because it closed outside
`config.adopt_closed_within_days`. It is not an action list — nothing in it
is ever applied by `--apply` — it exists purely so a plan whose only
outstanding work is N unadoptable issues does not read as "already in sync."
Act on it by re-running with `sync --adopt-all` to mirror every one of them
regardless of the window, or leave them unadopted if that is the intent.

`confidentiality_findings` is populated by `sync --plan`/`--dry-run`
itself: the tool scans every `creates` + `pushes` task's current content
before printing the plan (skipping tasks whose prior review still covers
their content) and is empty only when nothing outbound is flagged. See
`confidentiality-flow.md` for the field shapes and detector details.
