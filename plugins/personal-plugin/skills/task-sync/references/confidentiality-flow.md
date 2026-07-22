# Confidentiality Flow

Every task that is about to be pushed to a tracker for the first time (a
`creates` entry) or updated on one (a `pushes` entry) is scanned before it
leaves the machine — but this now happens **inside the tool**, as part of
building the plan. `sync --plan --json` (and `--dry-run`) already run the
scanner over every `creates`/`pushes` task's current content and populate
`confidentiality_findings` on the returned plan; nothing has to be invoked
separately for scanning, and the step is still strictly read-only (it never
writes `tasks.json` and never mutates a task). The four dispositions
(`keep`/`redact`/`remove`/`anonymize`) are implemented in the tool's Python
API (`task_sync.confidential`) and applied via a dedicated `task-sync
scan-apply --decisions <file>` subcommand — see Step 3 below.

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

Write the per-task decisions to a file (`{task_id: disposition}`, or wrapped
under a `"decisions"` key), then apply and persist them with the
`scan-apply` subcommand — it directly saves `tasks.json` and regenerates
`TASKS.md`, independent of `sync --apply`:

```bash
cat > /tmp/task-sync-confidentiality-decisions.json <<'JSON'
{"t-ab12cd": "anonymize"}
JSON

PYTHONPATH="$TOOL_SRC" python3 -m task_sync scan-apply \
  --decisions /tmp/task-sync-confidentiality-decisions.json
```

`scan-apply` validates every task id and disposition in the file **before**
mutating anything — an unknown task id or an invalid disposition rejects the
whole batch with a single error and writes nothing, rather than applying some
dispositions and failing partway through the rest. If the `--decisions` file
itself can't be read (missing, unreadable, malformed JSON), the error names
the path directly, e.g. `task-sync scan-apply: cannot read decisions file
/tmp/x.json: No such file or directory`. For each accepted pair, the task is
re-scanned to recover the finding spans (the sync plan JSON does not carry
them) and the disposition is applied, then `tasks.json` is saved and
`TASKS.md` regenerated together.

**Idempotent.** Re-running the same decisions file against content that
hasn't changed since it was last reviewed is a genuine no-op: a pair is
skipped when the task's recorded `confidentiality.decision` already equals
the requested disposition *and* its content is unchanged. When every pair is
skipped this way, nothing is written and the tool says so:
`task-sync scan-apply: N task(s) already carry the requested disposition —
nothing to apply`. A partial run — some applied, some already up to date —
reports both, e.g. `reviewed 2 task(s) — redact: 2 (1 already up to date)`.
Re-deciding a task with a *different* disposition than its recorded one
still applies, even though its content hasn't changed.

Do this **before** `sync --apply` so the create/push step reads the already-
cleaned content. Every task gets a `confidentiality` record
(`{decision, reviewed_hash, at}`) regardless of disposition, so `keep` also
counts as reviewed and will not re-prompt until the content changes again.
