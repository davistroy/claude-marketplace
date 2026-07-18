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
| n/a | issue with no matching task | `NEW_REMOTE` | pull (adopt: create a new task) |

A `CHANGED_LOCAL` task whose issue has vanished (deleted on the tracker) is
re-created instead of pushed — there is nothing left to push to.

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

Priority maps to a `priority/P1`.."`priority/P4"` label the same way.
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

## What `--plan --json` returns

```json
{
  "creates": [{"task_id": "t-ab12cd", "fields": {"title": "...", "body": "...", "state": "open", "labels": [...], "milestone": null}}],
  "pushes": [{"task_id": "t-ef34gh", "issue_number": 12, "fields": {...}}],
  "pulls": [{"issue_number": 15, "task_id": null, "fields": {"title": "...", "body": "...", "status": "todo", "priority": null, "labels": [...], "milestone": null}, "issue_updated_at": "...", "issue_closed_at": null}],
  "conflicts": [{"task_id": "t-ij56kl", "issue_number": 9, "local": {...}, "remote": {...}, "recommendation": "remote", "local_updated_at": "...", "remote_updated_at": "...", "remote_closed_at": null}],
  "confidentiality_findings": []
}
```

A `pulls` entry with `task_id: null` is an **adopt** (a brand-new task will be
created from the issue); a non-null `task_id` is an update to an existing
task. `confidentiality_findings` is populated by `sync --plan`/`--dry-run`
itself: the tool scans every `creates` + `pushes` task's current content
before printing the plan (skipping tasks whose prior review still covers
their content) and is empty only when nothing outbound is flagged. See
`confidentiality-flow.md` for the field shapes and detector details.
