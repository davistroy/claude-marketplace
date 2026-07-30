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
argument-hint: "[sync|list|add|edit|done|remove|status|init|scan-apply] [args...] [--dry-run]"
effort: medium
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion
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

### Version-skew preflight

Run this once, before the first subcommand, and report the result if it warns:

```bash
python3 - "$PLUGIN_DIR" <<'PY'
import json, os, re, sys
served = re.search(r"/personal-plugin/(\d+\.\d+\.\d+)(?:/|$)", sys.argv[1])
served = served.group(1) if served else None
reg = os.path.expanduser("~/.claude/plugins/installed_plugins.json")
try:
    entries = json.load(open(reg))["plugins"]["personal-plugin@troys-plugins"]
    installed = entries[0]["version"]
except Exception:
    installed = None
if served and installed and served != installed:
    print(f"WARNING: this session is serving personal-plugin {served}; "
          f"{installed} is installed. Run /reload-plugins to pick it up "
          f"(a full restart also works). "
          f"Until then this skill body may be older than the bundled tool.")
else:
    print(f"version-skew: none ({served or 'unknown'})")
PY
```

**Why this exists.** A running Claude Code session serves the plugin version it
resolved at start-up. `claude plugin update` writes `installed_plugins.json` and
prints "Restart to apply changes", but it does **not** change what the current
session is already serving. So a long-lived session can run the **current**
bundled tool from repo source while reading a **stale** skill body — a current
tool against an old contract, with no error anywhere. That is #232: a session
served an 11.3.0 body whose plan-JSON key list predated `orphans`, so the orphan
findings the tool emitted were never read.

**The remedy is `/reload-plugins`, not necessarily a restart** — measured, not
assumed: a `/reload-plugins` re-resolved all three troys-plugins in place and
brought a session that had been serving 11.3.0 since the previous day up to the
installed 11.7.0. The preflight is a warning, not a gate: an older body is
usually still usable, and the caller should know rather than be blocked.

## First Run: Auto-Init

Before any subcommand, check whether `tasks.json` exists at the target repo
root. If not, run `init` first (this is a no-op if it already exists, so it is
always safe to run):

```bash
PYTHONPATH="$TOOL_SRC" python3 -m task_sync init
```

`init` detects the provider (`github`, `gitea`, or `none` for local-only) from
the `origin` git remote, writes the `tasks.json` header (`provider`, `repo`,
`last_sync_at: null`, and a `config` block with `prune_closed_after_days: 30`,
`adopt_closed_within_days: 0`, and an empty `sensitive_terms` list), and
generates `TASKS.md`. For a `gitea` provider with an http(s) `origin`, `config`
also gets a `gitea_url` (scheme+host+port) so the first `sync` has a base URL
without needing `$GITEA_URL` or a `tea login` first; an ssh `origin` leaves it
unset (scheme/port aren't derivable from ssh) and relies on the fallback in
"Config (`tasks.json`)" below. After init, also make sure `TASKS.md` is gitignored in
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
| `scan-apply` | — | "apply that redaction decision", "anonymize that task" | yes |

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

**Enumerate the top-level keys the tool actually emitted — do not parse for a
remembered list.** Read every key present in the JSON, then map each to its
handling below. Any key you do not recognize is a finding: **surface it to the
user by name and do not proceed to `apply`** until they say whether it matters.

The keys known at the time this body was written are `creates`, `pushes`,
`pulls`, `conflicts`, `skipped_adopts`, `orphans`, and
`confidentiality_findings`. `skipped_adopts` is a list of tracker issue numbers
left unadopted by the adopt window — not an action, but always worth surfacing
(see step 2). `orphans` is a list of local tasks whose linked issues are missing
from the fetched list (pagination, saturation, or deletion), surfaced for human
review (see step 4). Field shapes: `references/sync-semantics.md`.

**That list is a convenience, not the contract — the tool's output is the
contract.** This inversion is the whole point: a session can serve a skill body
older than the bundled tool (see the version-skew preflight in Setup), and when
that happened in #232 a body predating `orphans` parsed for six keys and
silently dropped the seventh. It reported the backlog fully reconciled while
discarding the exact finding `orphans` was added to surface. Enumerating what is
there cannot fail that way: an unrecognized key stops the run instead of
vanishing. A missing key is the benign direction — treat it as empty.

By default, a remote-only issue (`NEW_REMOTE` — no local task references it
yet) is only adopted into `pulls` if it is still open, or closed within
`config.adopt_closed_within_days` days — its own key, default `0`, meaning
**adopt open issues only**: any closed issue is left unadopted no matter how
recently it closed. Set it higher (e.g. `3`) for a grace window that also
adopts issues closed within the last N days. An absent key (a `tasks.json`
predating this setting) also resolves to `0`, not to the unrelated
`prune_closed_after_days` window. Already-adopted tasks are never affected by
this window — it gates first-time adoption only. Pass `sync --adopt-all` to
disable the window and mirror every issue in history regardless of how long
ago it closed.

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
- **Orphans** — local tasks whose linked issues are missing from the fetched
  list (the issue may still exist remotely and simply wasn't fetched, or it
  may have been deleted): render as a table (`task id`, `linked issue #`,
  `local edits since last sync?`) and prompt per orphan for `keep` (clears the
  link so the next run re-creates via the normal creates path) or `drop`
  (removes the local task). An undecided orphan is left untouched and resurfaces
  on the next sync.
- **Skipped adoptions** — if `skipped_adopts` is non-empty, always call it out
  even though it needs no decision: "N issue(s) closed outside the adopt
  window were not adopted: #174, #173, …" plus a pointer to `--adopt-all`.
  These issues are otherwise invisible in the rest of the plan, and a user
  who expects a closed issue to show up as a task would see nothing without
  this line.

If `creates`, `pushes`, `pulls`, `conflicts`, `orphans`, and `skipped_adopts`
are all empty, report "already in sync" and stop — there is nothing to decide
or apply. If only `skipped_adopts` and/or `orphans` are non-empty, do not
report "already in sync" — surface the counts and stop; there is nothing to
apply immediately, but it is not nothing to report.

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
recommendation as a hint, not a default). For each orphan, ask for `keep`
(clears the link, next run re-creates) or `drop` (removes the task). For each
confidentiality finding, ask for `keep`, `redact`, `remove`, or `anonymize`.
Do not guess — unanswered conflicts/orphans are left untouched by `apply` and
simply resurface next sync, so it is always safe to defer one the user is
unsure about.

Write the decisions to a JSON file (conflict and orphan decisions can coexist
in one file):

```bash
cat > /tmp/task-sync-decisions.json <<'JSON'
{
  "decisions": {"t-ab12cd": "local", "t-ef34gh": "remote"},
  "orphan_decisions": {"t-orphan-1": "keep", "t-orphan-2": "drop"}
}
JSON
```

Or flat form for either or both:

```bash
cat > /tmp/task-sync-decisions.json <<'JSON'
{"t-ab12cd": "local", "t-orphan-1": "keep"}
JSON
```

Apply confidentiality dispositions immediately (before `sync --apply`) by
running `scan-apply` (full walkthrough: `references/confidentiality-flow.md`):

```bash
PYTHONPATH="$TOOL_SRC" python3 -m task_sync scan-apply \
  --decisions /tmp/task-sync-confidentiality-decisions.json
```

This validates every task id and disposition in the file before mutating
anything — a bad entry rejects the whole batch and writes nothing — then, if
anything actually changed, saves `tasks.json` and regenerates `TASKS.md`. It
is idempotent: re-running the same decisions file against content that
hasn't changed since the last review is a true no-op (nothing written), and
the tool says so explicitly rather than pretending it applied something.

### 5. Public-repo visibility guardrail

Before the **first** push or create in this session, check the repo's
visibility and warn loudly if it is public:

```bash
gh repo view --json visibility --jq .visibility 2>/dev/null
```

(For a Gitea remote, check the repo's `private` field via its REST API using
`$GITEA_TOKEN` if set, else the token from `~/.config/tea/config.yml` — the
same order the tool's own Gitea adapter uses.)

If the result is `PUBLIC` (GitHub) or `private: false` (Gitea), show the
warning text below, then confirm with `AskUserQuestion`:

```text
Warning: <owner>/<repo> is a PUBLIC repository.
Creating/updating N issue(s) will publish this content publicly.
```

```json
{
  "questions": [
    {
      "question": "<owner>/<repo> is a PUBLIC repository. Creating/updating N issue(s) will publish this content publicly. Continue?",
      "header": "Public Repo",
      "multiSelect": false,
      "options": [
        {
          "label": "Yes",
          "description": "Proceed with applying the planned creates/pushes/pulls to the public repo"
        },
        {
          "label": "No",
          "description": "Abort — nothing is applied"
        },
        {
          "label": "Show plan again",
          "description": "Re-print the full sync plan (creates/pushes/pulls/conflicts) before deciding"
        }
      ]
    }
  ]
}
```

Do not proceed to apply without an explicit "Yes". A private repo needs no
extra confirmation beyond the normal plan review.

### 6. Apply

```bash
PYTHONPATH="$TOOL_SRC" python3 -m task_sync sync --apply --decisions /tmp/task-sync-decisions.json
```

This executes creates/pushes/pulls, applies only the decided conflicts
(undecided ones are left exactly as-is), applies only the decided orphans
(undecided orphans are left untouched and resurface next sync), prunes `done`
tasks whose issue closed more than `prune_closed_after_days` ago, refreshes
`last_sync_at`, and saves `tasks.json` + regenerates `TASKS.md` — all inside
the tool, atomically. Report the printed summary (counts of creates/pushes/pulls,
conflicts surfaced, and — only when `skipped_adopts` and/or `orphans` were
non-empty — the trailing sentences about skipped adoptions and orphans) to
the user.

### `--dry-run`

`sync --dry-run` (or `sync` with no mode flag — this is the default) prints a
short human summary of the same plan and writes nothing. Use it whenever the
user wants a preview without going through the decide/apply steps: run it,
show the summary, and stop. Do not build a decisions file or call `--apply`.

## Confidentiality Flow (summary)

Four dispositions, applied deterministically by the tool and remembered by
content hash (`keep` is a no-op to content; `redact` masks a span; `remove`
deletes it; `anonymize` swaps in a stable `<<TERM_xxxxxx>>` token so the same
term always maps to the same token). A previously-reviewed task is skipped on
re-scan unless its content changed — the scan itself runs inside `sync
--plan`/`--dry-run` now, so there is nothing to invoke separately for it;
applying a disposition runs via `scan-apply --decisions <file>`, which is
itself idempotent (re-applying the same disposition to unchanged content
writes nothing). Full flow, output shapes, and the exact invocation:
`references/confidentiality-flow.md`.

## Sync Semantics (summary)

Three-way classification against the last synced base: exactly one side
changed → applied automatically in that direction; both sides changed →
surfaced as a conflict, recommendation is last-write-wins but nothing is
auto-applied. Full classify/resolve/prune rules: `references/sync-semantics.md`.

## Config (`tasks.json`)

Header fields (`provider`, `repo`, `last_sync_at`, `config`) and the
`config` block (`prune_closed_after_days`, `adopt_closed_within_days`,
`sensitive_terms`, optional `gitea_url`), plus the full Gitea base-URL/token
resolution order: `references/config-reference.md`.

### `tasks.json` is machine-local, and not git-recoverable

Whether `tasks.json` is committed is a per-repo choice. **In this repo it is
gitignored** (D65), which has two consequences worth stating plainly rather
than discovering:

- **Cross-machine sync of local state is out of scope.** The `last_synced`
  merge base lives inside `tasks.json`, so each machine keeps its own. On a
  second machine `sync` exits until `init` runs there, after which every open
  issue is adopted fresh. Conflict detection works normally *within* a
  machine; what does not travel is state that has never been pushed —
  unpushed tasks, unpushed edits, and confidentiality dispositions. The
  tracker remains the archive of record (D34), so nothing pushed is at risk.
- **There is no `git checkout` undo.** A gitignored file has no version
  history, so any destructive command against `tasks.json` is final. Before a
  bulk `remove`, or any hand-edit, copy the file first.

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
- `references/confidentiality-flow.md` — scan/disposition flow and the `scan-apply` invocation.
- `references/config-reference.md` — `tasks.json` header and `config` shape.
