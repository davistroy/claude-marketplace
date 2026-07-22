# task-sync Command Reference

Every subcommand below is invoked the same way:

```bash
PYTHONPATH="$TOOL_SRC" python3 -m task_sync <command> [args...] [--tasks <path>]
```

`--tasks` defaults to `tasks.json` in the current working directory and is
accepted by every subcommand. Every mutating command (`init` when creating,
`add`, `edit`, `done`, `remove`, `scan-apply`) saves `tasks.json` canonically
(stable key order, tasks sorted by id, atomic write) and regenerates
`TASKS.md` in the same directory before returning.

## `init`

```bash
python3 -m task_sync init [--tasks tasks.json] [--repo-root .]
```

Creates `tasks.json` if it does not already exist: detects `provider`
(`github`/`gitea`/`none`) from the `origin` remote at `--repo-root`, writes the
header (`provider`, `repo`, `last_sync_at: null`, `config:
{prune_closed_after_days: 30, adopt_closed_within_days: 0, sensitive_terms: []}`,
plus `gitea_url` when `provider` is `gitea` and `origin` is http(s) — see
`config-reference.md`),
and generates `TASKS.md`. If `tasks.json` already exists this is a no-op on the file itself,
but `TASKS.md` is still regenerated from current content (so a stale/deleted
`TASKS.md` is repaired). Always safe to run — use it as the "make sure this
repo is set up" step before any other command.

## `list` (alias `ls`)

```bash
python3 -m task_sync list [--status S] [--priority P] [--milestone M] [--sort FIELD] [--all]
```

Prints the open-tasks table (`#`, priority, status, title, labels; `blocked`
tasks show what they are waiting on if `last_synced.blocked_on` is set).
`done` tasks are hidden unless `--status done` or `--all` is given.

- `--status` — exact-match filter on one status (`backlog`/`todo`/
  `in-progress`/`blocked`/`done`).
- `--priority` — exact-match filter on one priority (`P1`-`P4`).
- `--milestone` — exact-match filter on milestone name.
- `--sort` — any `Task` field name (e.g. `title`, `priority`, `id`); ties
  break on `id`. Omit for the default status → priority → id ordering.
- `--all` — include `done` tasks without narrowing to only `done`.

Filters combine with AND (all given filters must match).

## `add "title"`

```bash
python3 -m task_sync add "Write the release notes" \
  --body "..." --priority P2 --labels "backend,urgent" --milestone v1
```

Creates a new task with `status: todo` (the only default; there is no way to
add directly into another status — use `edit` afterward if needed), a fresh
`id` (`t-` + 6 hex chars), `created_at`/`updated_at` stamped now, and prints
the added task's one-line summary. `--labels` is a single comma-separated
value; whitespace around each label is stripped and empty entries dropped.
`--priority`, if given, must be one of `P1`-`P4` or the tool rejects it with a
`ValueError`-derived message.

## `edit <id|#>`

```bash
python3 -m task_sync edit t-ab12cd --status in-progress --priority P1
python3 -m task_sync edit 42 --title "New title"          # by issue number
python3 -m task_sync edit "#42" --labels "a,b"             # '#'-prefixed also matches
```

Updates only the fields explicitly passed (`--title`, `--body`, `--status`,
`--priority`, `--labels`, `--milestone`); anything omitted is left as-is.
`--labels` **replaces** the full label set (there is no add/remove-one
primitive — pass the complete desired list). `updated_at` is always
refreshed. The merged result is re-validated the same way a fresh task would
be (invalid `--status`/`--priority` values are rejected before anything is
written). Matches `<id|#>` against the task's `id` first, then — if the ref is
numeric (optionally `#`-prefixed) — against `issue_number`.

## `done <id|#>` (alias `close`)

```bash
python3 -m task_sync done t-ab12cd
python3 -m task_sync close 42
```

Sets `status: done` and stamps `closed_at`/`updated_at` to now. Does not touch
the tracker — that only happens on the next `sync --apply` (which will close
the corresponding issue as part of the push). A `done` task is hidden from
`list`'s default view (use `--all` or `--status done` to see it) and is a
candidate for pruning by `sync --apply` once its issue has been closed for
longer than `config.prune_closed_after_days`.

## `remove <id|#>` (alias `rm`)

```bash
python3 -m task_sync remove t-ab12cd
python3 -m task_sync rm 42
```

Deletes the task from `tasks.json` entirely. This does **not** close or
delete the corresponding tracker issue (there is nothing left locally to push
that state) — if the task was already linked to an issue, close it on the
tracker separately if that is also the intent. Irreversible other than via
git history on `tasks.json` (assuming it is committed).

## `status`

```bash
python3 -m task_sync status
```

Prints counts by status (`backlog`/`todo`/`in-progress`/`blocked`/`done`,
plus `total` and `open`), `last_sync_at` (or `never`), the detected
`provider`/`repo`, and a health hint: if any `done` task has been closed for
longer than `config.prune_closed_after_days`, it is called out as
prune-eligible on the next `sync --apply`; otherwise "health: ok" is printed.

## `sync`

```bash
python3 -m task_sync sync --dry-run                          # default: preview only
python3 -m task_sync sync --plan --json                       # machine-readable plan, writes nothing
python3 -m task_sync sync --apply --decisions decisions.json  # execute
python3 -m task_sync sync --apply --adopt-all                 # full-mirror adopt, ignore the adopt window
```

The only subcommand this skill does not call directly for its own output —
see the SKILL.md "Plan → Decide → Apply" section for the full orchestration.
`--plan`, `--dry-run`, and `--apply` are mutually exclusive; `--dry-run` (or
no mode flag at all) is the default and is always safe — it never writes
`tasks.json` or `TASKS.md` and never calls the tracker's write API. In
local-only mode (no tracker remote detected) `sync` prints a notice and exits
0 immediately; there is nothing to reconcile.

- `--adopt-all` — full-mirror mode: adopt every `NEW_REMOTE` issue regardless
  of how long ago it closed. Without it, adoption is gated by its own
  `config.adopt_closed_within_days` (default `0` = adopt open issues only —
  see `config-reference.md` and `sync-semantics.md`'s Prune section for the
  full rule). An open issue is always adopted, flag or not, and an
  already-adopted task's `CHANGED_REMOTE` updates are never gated by this
  window either way.

Issues the adopt window rejects are never silently dropped. `--plan --json`
lists their issue numbers under `skipped_adopts`. `--dry-run` (and `--plan`'s
human summary) adds a line directly under the pull count, only when
non-empty:

```text
  skipped (closed outside adopt window): 3 — use --adopt-all to mirror them
```

A plan holding only skipped adoptions (no creates/pushes/pulls/conflicts) no
longer reports "already in sync" — it reports the skipped count instead.
`--apply` appends the equivalent sentence to its own summary, again only when
non-zero: `N issue(s) closed outside the adopt window were not adopted — use
--adopt-all to mirror them.`

## `scan-apply`

```bash
python3 -m task_sync scan-apply --decisions decisions.json [--tasks tasks.json]
```

Applies a confidentiality disposition (`keep`/`redact`/`remove`/`anonymize`)
per task, from a decisions file shaped like the conflict-decisions file above
(flat `{task_id: disposition}`, or wrapped under a `"decisions"` key).
Replaces the inline `python3` heredoc previously documented in
`confidentiality-flow.md`.

Validates every task id and disposition **before** mutating anything — an
unknown task id or a disposition outside `keep`/`redact`/`remove`/`anonymize`
rejects the whole batch with a single error, and nothing is written. For
each accepted pair, the task is re-scanned to recover the finding spans (the
sync plan JSON does not carry them), the disposition is applied and stamped
onto `task.confidentiality`, and then `tasks.json` is saved canonically and
`TASKS.md` is regenerated. An empty decisions file is a no-op — nothing is
scanned, mutated, or written. Run this **before** `sync --apply` so any
subsequent create/push reads the already-cleaned content.

**Idempotent.** A `task_id`/disposition pair is skipped when the task's
recorded `confidentiality.decision` already equals the requested disposition
**and** its content hasn't changed since that review — re-deciding a task
with a *different* disposition still applies, even if unchanged. When every
pair in the file is skipped this way, nothing is written at all and the tool
prints:

```text
task-sync scan-apply: N task(s) already carry the requested disposition — nothing to apply
```

A partial run (some applied, some skipped) instead prints a breakdown with a
trailing count of how many were already up to date, e.g.:

```text
task-sync scan-apply: reviewed 2 task(s) — redact: 2 (1 already up to date)
```
