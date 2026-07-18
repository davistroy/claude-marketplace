# Confidentiality Flow

Every task that is about to be pushed to a tracker for the first time (a
`creates` entry) or updated on one (a `pushes` entry) is scanned before it
leaves the machine — but this now happens **inside the tool**, as part of
building the plan. `sync --plan --json` (and `--dry-run`) already run the
scanner over every `creates`/`pushes` task's current content and populate
`confidentiality_findings` on the returned plan; nothing has to be invoked
separately for scanning, and the step is still strictly read-only (it never
writes `tasks.json` and never mutates a task). The four dispositions
(`keep`/`redact`/`remove`/`anonymize`) are implemented and unit-tested in the
tool's Python API (`task_sync.confidential`) but — unlike the seven CLI
subcommands — applying one is not yet exposed as a dedicated `task-sync`
subcommand; that half still runs via the short inline script in Step 3 below.

## What gets scanned

Only `title` and `body` (the two fields that get pushed). Three detector
families, combined into one position-ordered list per field:

- **Secrets** — well-known token shapes (`ghp_`/`gho_`/`github_pat_`, `sk-`,
  AWS `AKIA…`, PEM key blocks, generic high-entropy bearer tokens). Always
  `CRITICAL`.
- **Structural identifiers** — emails, internal hostnames (`*.corp`,
  `*.internal`, etc.), IPv4 addresses, ticket/asset id patterns. `MEDIUM` or
  `HIGH` depending on category.
- **Per-repo sensitive terms** — the `config.sensitive_terms` list from
  `tasks.json` (empty by default; this is the only place client/brand terms
  ever enter the system — never hardcode them anywhere else). `HIGH`.

A task that was already reviewed and is unchanged since (its content hash
still matches the stored `confidentiality.reviewed_hash`) is skipped by the
tool's scan — it will not re-surface in `confidentiality_findings` unless its
`title`/`body` changes.

## Step 1: read the findings off the plan

Nothing to run — `confidentiality_findings` is already in the JSON from
`sync --plan --json` (see step 1 of the main plan→decide→apply flow in
`SKILL.md`). Its shape:

```json
[
  {
    "task_id": "t-ab12cd",
    "title": "...",
    "findings": [
      {
        "field": "body",
        "category": "secret.github",
        "severity": "CRITICAL",
        "preview": "ghp_1a…f9c2",
        "suggestion": "redact"
      }
    ]
  }
]
```

Render it as a table: task, field, category, severity, a masked preview
(never the raw secret — `preview` is already display-safe). If the list is
empty, say so and skip straight to the visibility guardrail — there is
nothing to disposition.

## Step 2: ask, per task

For each task with findings, ask the user to pick one disposition for that
task's findings as a whole:

- `keep` — no content change; the reviewer accepts the text as-is.
- `redact` — replace each flagged span with `[REDACTED]`.
- `remove` — delete each flagged span (if that empties a field, it is left
  empty).
- `anonymize` — replace each flagged span with a stable
  `<<TERM_xxxxxx>>` token, derived from a hash of the matched text, so the
  same term always maps to the same token across the whole file.

Treat any `CRITICAL` finding (a real secret/token shape) as blocking: do not
let that task proceed to `redact`-or-lower risk of "keep" without an explicit,
separate confirmation — a bare "keep" on a `CRITICAL` finding should be
double-checked with the user before writing it.

## Step 3: apply dispositions

Write the per-task decisions to a file (`{task_id: disposition}`), then apply
and persist them — this step directly saves `tasks.json` and regenerates
`TASKS.md`, independent of `sync --apply`:

```bash
PYTHONPATH="$TOOL_SRC" python3 - <<'PY'
import json
from task_sync import store, commands
from task_sync.confidential.scan import scan_task
from task_sync.confidential.apply import apply_review

tasklist = store.load("tasks.json")
dispositions = json.load(open("/tmp/task-sync-confidentiality-decisions.json"))

by_id = {t.id: t for t in tasklist.tasks}
sensitive_terms = tasklist.config.get("sensitive_terms", [])

for task_id, disposition in dispositions.items():
    task = by_id[task_id]
    findings = scan_task(task, sensitive_terms)
    apply_review(task, findings, disposition)

commands.save_and_regenerate(tasklist, "tasks.json")
PY
```

Do this **before** `sync --apply` so the create/push step reads the already-
cleaned content. Every task gets a `confidentiality` record
(`{decision, reviewed_hash, at}`) regardless of disposition, so `keep` also
counts as reviewed and will not re-prompt until the content changes again.
