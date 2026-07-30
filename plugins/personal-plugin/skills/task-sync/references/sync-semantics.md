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
  "orphans": [{"task_id": "t-mn78op", "issue_number": 42, "local_changed": true}],
  "confidentiality_findings": []
}
```

The key order is fixed: `creates`, `pushes`, `pulls`, `conflicts`,
`skipped_adopts`, `orphans`, `confidentiality_findings`.

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

`orphans` is a JSON array of local tasks whose linked issue disappeared from
the fetched tracker list (pagination/saturation, deletion, or archive). Each
carries the task id, the missing issue number (still recorded on the task),
and a `local_changed` boolean indicating whether the task has drifted locally
since the last sync. It is not an action list — nothing in it is ever applied
automatically — it exists purely to surface the fact that something needs human
attention. Act on it by either (1) running `sync --plan` again (if the issue
reappears in the fetched list, the task will be reclassified and treated normally),
(2) deciding to "keep" the link and re-run next sync (the issue may yet appear
in pagination), or (3) deciding to "drop" the link and delete the local task.
The keep/drop disposition is applied by passing `--decisions` with an
`orphan_decisions` section (see below).

`confidentiality_findings` is populated by `sync --plan`/`--dry-run`
itself: the tool scans every `creates` + `pushes` task's current content
before printing the plan (skipping tasks whose prior review still covers
their content) and is empty only when nothing outbound is flagged. See
`confidentiality-flow.md` for the field shapes and detector details.

## Orphan decisions and apply

When a plan contains orphans, apply requires explicit `orphan_decisions` to
handle them (all ids and dispositions are validated upfront before any mutations).
The `--decisions` file can carry both conflict and orphan decisions in one of
three formats:

**1. Wrapped, both sections:**

```json
{
  "decisions": {"t-ab12cd": "local", "t-ef34gh": "remote"},
  "orphan_decisions": {"t-orphan-1": "keep", "t-orphan-2": "drop"}
}
```

**2. Wrapped, one section only** — a file is *wrapped* if it carries **any**
top-level key named `decisions` or `orphan_decisions`. Once wrapped, a
missing section means "no decisions of that kind" (an empty map), not "fall
through to the outer object" — this is what backward-compat conflicts-only
files rely on:

```json
{"decisions": {"t-ab12cd": "local", "t-ef34gh": "remote"}}
```

```json
{"orphan_decisions": {"t-orphan-1": "keep", "t-orphan-2": "drop"}}
```

**3. Flat** (decisions and orphan_decisions coexist in the same object, with
no `decisions`/`orphan_decisions` wrapper key; each id is routed to whichever
of the current plan's conflicts/orphans it matches — an id in neither is
routed to the orphan map on purpose, since that is the only fail-loud
consumer, so a mistyped id still raises rather than being silently dropped):

```json
{"t-ab12cd": "local", "t-orphan-1": "keep"}
```

Valid orphan dispositions:

| Disposition | Effect |
|---|---|
| `keep` | Clears the task's `issue_number` and `last_synced` base so the next `sync --plan` treats it as a NEW_LOCAL task and re-creates a fresh issue |
| `drop` | Removes the local task from `tasks.json` entirely |

An undecided orphan (no entry in `orphan_decisions`) is left untouched and
will resurface unchanged on the next `sync --plan`, so it is always safe to
defer a decision the user is unsure about.
