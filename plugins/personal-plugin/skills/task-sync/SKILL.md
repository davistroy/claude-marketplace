---
name: task-sync
description: >
  Manage a local task/backlog list (tasks.json + a generated TASKS.md) for the
  current repo and reconcile it with GitHub or Gitea issues, via the bundled
  task-sync Python tool. Supports direct commands (list/add/edit/done/remove/
  status/init) and a plan-decide-apply sync that surfaces creates, pushes,
  pulls, conflicts, and confidentiality findings for review before anything
  leaves the machine, with a public-repo push warning and a --dry-run mode.
  Suggest when — the user wants to see or manage this repo's tasks or backlog,
  sync tasks with GitHub/Gitea issues, mentions a local task tracker or
  TASKS.md, or asks to push/pull/reconcile tasks against issues; keywords —
  task list, backlog, sync issues, task-sync, todo list, reconcile issues.
argument-hint: "[sync|list|add|edit|done|remove|status|init] [args...] [--dry-run]"
effort: medium
allowed-tools: Read, Write, Edit, Glob, Bash
---

# Task Sync

Local-first task tracking backed by a canonical `tasks.json` (with a generated,
read-only `TASKS.md` view) that optionally reconciles with GitHub or Gitea
issues. All logic lives in the bundled `task_sync` Python tool — this skill's
job is invocation, table rendering, and human-in-the-loop decisions (conflict
resolution, confidentiality review, the public-repo push warning). The tool
never auto-resolves a conflict and never pushes anything without an explicit
plan the user has seen.

## Setup

The tool is bundled at `tools/task-sync/src`. Resolve the plugin root the same
way other bundled-tool skills do, then invoke every subcommand through
`python3 -m task_sync`:

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(find ~ -path '*/plugins/personal-plugin' -type d 2>/dev/null | head -1)}"
TOOL_SRC="$PLUGIN_DIR/tools/task-sync/src"

PYTHONPATH="$TOOL_SRC" python3 -m task_sync status
```

`tasks.json` lives at the target repo's root by default (`--tasks tasks.json`,
resolved relative to the working directory). Pass `--tasks <path>` for any
other location.

## First Run: Auto-Init

Before any subcommand, check whether `tasks.json` exists at the target repo
root. If not, run `init` first (this is a no-op if it already exists, so it is
always safe to run):

```bash
PYTHONPATH="$TOOL_SRC" python3 -m task_sync init
```

`init` detects the provider (`github`, `gitea`, or `none` for local-only) from
the `origin` git remote, writes the `tasks.json` header (`provider`, `repo`,
`last_sync_at: null`, and a `config` block with
`prune_closed_after_days: 30` and an empty `sensitive_terms` list), and
generates `TASKS.md`. After init, also make sure `TASKS.md` is gitignored in
the **target** repo (it is a generated view, regenerated after every mutating
command — never hand-edit it, never commit it):

```bash
grep -qxF 'TASKS.md' .gitignore 2>/dev/null || echo 'TASKS.md' >> .gitignore
```

## Commands

Direct subcommand invocation and natural-language requests both route to the
same tool calls. Full flag reference: `references/command-reference.md`.

| Command | Aliases | Natural language | Mutates? |
|---|---|---|---|
| `sync` | — | "sync my tasks", "push/pull tasks", "reconcile with issues" | plan→decide→apply, see below |
| `list` | `ls` | "show my tasks", "what's open", "list backlog" | no |
| `add "title"` | — | "add a task to …", "track this as a task" | yes |
| `edit <id\|#>` | — | "update task …", "change the priority of …" | yes |
| `done <id\|#>` | `close` | "mark … done", "close task …" | yes |
| `remove <id\|#>` | `rm` | "delete task …", "drop …" | yes |
| `status` | — | "task status", "how many open tasks" | no |
| `init` | — | "set up task tracking here" | yes (first run only) |

For a bare command (`list`, `add "…"`, `edit`, `done`, `remove`, `status`,
`init`), run `init` if needed (see above), then invoke the subcommand and
report its output directly — no plan/decide/apply cycle applies to these;
`store.save` + `TASKS.md` regeneration happen inside the tool itself.

`<id|#>` accepts either a task id (`t-ab12cd`) or an issue number, optionally
`#`-prefixed (`42` or `#42`) — whichever the user gave.

When the user just says "sync" (or gives no subcommand and a tracker is
configured), run the full plan→decide→apply flow below.

## Plan → Decide → Apply (sync)

Never call `sync --apply` blind. Always build and show a plan first, get
explicit decisions for anything ambiguous, then apply.

### 1. Build the plan

```bash
PYTHONPATH="$TOOL_SRC" python3 -m task_sync sync --plan --json
```

This is **strictly read-only** — it never writes `tasks.json` or `TASKS.md`
and never calls the tracker's write API. If the repo has no tracker remote,
the tool prints "local-only mode" and exits 0; there is nothing to plan.

Parse the JSON: `creates`, `pushes`, `pulls`, `conflicts`,
`confidentiality_findings`. Field shapes: `references/sync-semantics.md`.

### 2. Render the plan as tables

Show the user what would happen, grouped by section, before asking for any
decision:

- **Creates** — local tasks with no issue yet → new issues (title, priority,
  labels, milestone).
- **Pushes** — local edits → update an existing issue (`#<issue_number>`,
  what changed).
- **Pulls** — remote-only or remote-changed issues → adopted or updated
  locally (`#<issue_number>`, resulting status/title).
- **Conflicts** — both sides changed since the last sync; render as a
  side-by-side table (`local` vs `remote`, each field) with the tool's
  `recommendation` (last-write-wins) called out, but never pre-select it.

If every section is empty, report "already in sync" and stop — there is
nothing to decide or apply.

### 3. Confidentiality scan

The plan JSON from step 1 already carries the scan results — no separate
scan step is needed. Before building the plan, the tool itself scans every
`creates`/`pushes` task's current `title`/`body` for secrets, structural
identifiers (emails, internal hostnames, ticket/asset ids), and any per-repo
`sensitive_terms` from `tasks.json`'s `config`, skipping a task whose prior
review still covers its content unchanged. Just read `confidentiality_findings`
off the plan you already fetched. Field shapes and detector details:
`references/confidentiality-flow.md`.

Render every finding as a table (task, field, category, severity, preview —
never the full secret) and ask the user to disposition each one. `CRITICAL`
findings (real secret/token shapes) need an explicit decision; do not let a
push proceed past them silently.

### 4. Prompt for every decision

For each conflict, ask the user to pick `local` or `remote` (showing the
recommendation as a hint, not a default). For each confidentiality finding,
ask for `keep`, `redact`, `remove`, or `anonymize`. Do not guess — an
unanswered conflict is left untouched by `apply` and simply resurfaces next
sync, so it is always safe to defer one the user is unsure about.

Write the conflict decisions to a JSON file (flat `{task_id: "local"|"remote"}`,
or `{"decisions": {...}}`):

```bash
cat > /tmp/task-sync-decisions.json <<'JSON'
{"t-ab12cd": "local", "t-ef34gh": "remote"}
JSON
```

Apply confidentiality dispositions immediately (before `sync --apply`) using
the disposition-apply script from `references/confidentiality-flow.md` — this
directly saves `tasks.json` and regenerates `TASKS.md`. (Disposition apply is
not yet a dedicated CLI subcommand; scanning is — the plan already did that
part in step 3.)

### 5. Public-repo visibility guardrail

Before the **first** push or create in this session, check the repo's
visibility and warn loudly if it is public:

```bash
gh repo view --json visibility --jq .visibility 2>/dev/null
```

(For a Gitea remote, check the repo's `private` field via its REST API using
the token from `~/.config/tea/config.yml`, the same source the tool's own
Gitea adapter uses.)

If the result is `PUBLIC` (GitHub) or `private: false` (Gitea), show:

```text
Warning: <owner>/<repo> is a PUBLIC repository.
Creating/updating N issue(s) will publish this content publicly.
Continue? (yes / no / show plan again)
```

Do not proceed to apply without an explicit "yes". A private repo needs no
extra confirmation beyond the normal plan review.

### 6. Apply

```bash
PYTHONPATH="$TOOL_SRC" python3 -m task_sync sync --apply --decisions /tmp/task-sync-decisions.json
```

This executes creates/pushes/pulls, applies only the decided conflicts
(undecided ones are left exactly as-is), prunes `done` tasks whose issue
closed more than `prune_closed_after_days` ago, refreshes `last_sync_at`, and
saves `tasks.json` + regenerates `TASKS.md` — all inside the tool, atomically.
Report the printed summary (counts of creates/pushes/pulls, conflicts
surfaced) to the user.

### `--dry-run`

`sync --dry-run` (or `sync` with no mode flag — this is the default) prints a
short human summary of the same plan and writes nothing. Use it whenever the
user wants a preview without going through the decide/apply steps: run it,
show the summary, and stop. Do not build a decisions file or call `--apply`.

## Confidentiality Flow (summary)

Four dispositions, applied deterministically by the tool and remembered by
content hash (`keep` is a no-op; `redact` masks a span; `remove` deletes it;
`anonymize` swaps in a stable `<<TERM_xxxxxx>>` token so the same term always
maps to the same token). A previously-reviewed task is skipped on re-scan
unless its content changed — the scan itself runs inside `sync --plan`/
`--dry-run` now, so there is nothing to invoke separately for it. Full flow,
output shapes, and the disposition-apply script:
`references/confidentiality-flow.md`.

## Sync Semantics (summary)

Three-way classification against the last synced base: exactly one side
changed → applied automatically in that direction; both sides changed →
surfaced as a conflict, recommendation is last-write-wins but nothing is
auto-applied. Full classify/resolve/prune rules: `references/sync-semantics.md`.

## Config (`tasks.json`)

Header fields (`provider`, `repo`, `last_sync_at`, `config`) and the
`config` block (`prune_closed_after_days`, `sensitive_terms`, optional
`gitea_url`): `references/config-reference.md`.

## Error Handling

- **No `tasks.json`** for a non-`init` command: run `init` first (see "First
  Run: Auto-Init"), then retry the original command.
- **`gh`/Gitea auth failure** during `sync`: report the tool's error verbatim
  (it names the missing credential — `gh auth login` or `tea login`) and stop;
  do not retry blind.
- **Unresolved conflicts after apply**: expected, not an error — they were
  left untouched on purpose and will resurface on the next `sync --plan`.
- **`add`/`edit` validation error** (bad status/priority): the tool rejects it
  with a clear message; relay it and ask the user to correct the value.

## References

- `references/command-reference.md` — full flag reference for every subcommand.
- `references/sync-semantics.md` — 3-way classify, last-write-wins, conflicts, prune.
- `references/confidentiality-flow.md` — scan/disposition flow and exact inline scripts.
- `references/config-reference.md` — `tasks.json` header and `config` shape.
