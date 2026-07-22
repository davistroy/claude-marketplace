---
command: task-sync
type: skill
fixtures: []
---

# Eval: /task-sync (skill)

## Purpose

Local-first task tracking (`tasks.json` + generated `TASKS.md`) that
optionally reconciles with GitHub or Gitea issues via the bundled
`task_sync` Python tool. The tool owns all deterministic work (store I/O,
3-way reconcile, confidentiality scanning); the skill owns invocation,
table rendering, and every human-in-the-loop decision. Good behavior: never
call `sync --apply` without first showing a plan built from `sync --plan
--json`, never auto-resolve a conflict, never let a `CRITICAL`
confidentiality finding push silently, and never treat a public-repo push
as pre-approved.

## Fixtures

None — operates on the current repo's `tasks.json` via the bundled tool
(`PYTHONPATH="$TOOL_SRC" python3 -m task_sync <command>`).

## Test Scenarios

### S1: First run — auto-init creates tasks.json

**Invocation:** `/task-sync` (or any subcommand) in a repo with no
`tasks.json`

**Must:**
- [ ] Detects the missing `tasks.json` and runs `init` before the requested
      subcommand
- [ ] `init` detects the provider (`github`/`gitea`/`none`) from the `origin`
      git remote rather than asking the user or guessing
- [ ] `tasks.json` is created with `provider`, `repo`, `last_sync_at: null`,
      and a `config` block (`prune_closed_after_days: 30`,
      `sensitive_terms: []`)
- [ ] `TASKS.md` is generated and added to `.gitignore` in the target repo
      if not already present

**Must NOT:**
- [ ] Hand-edit `TASKS.md` directly — it is always tool-generated

---

### S2: Add a task

**Invocation:** `/task-sync add "Write the release notes" --priority P2`

**Must:**
- [ ] Runs `init` first if `tasks.json` does not yet exist (see S1)
- [ ] Invokes `python3 -m task_sync add "Write the release notes" --priority
      P2` through the bundled tool, not a hand-rolled JSON edit
- [ ] Reports the added task's id (`t-` + 6 hex chars) and one-line summary
      back to the user
- [ ] Does not run the plan→decide→apply sync cycle for this direct
      subcommand — `add` mutates `tasks.json` and regenerates `TASKS.md`
      inside the tool itself

**Must NOT:**
- [ ] Accept a `--priority` value outside `P1`-`P4` without surfacing the
      tool's validation error

---

### S3: List / ls filtering

**Invocation:** `/task-sync list --status in-progress` (also verify the
`ls` alias and the default view hides `done` tasks)

**Must:**
- [ ] Invokes `python3 -m task_sync list --status in-progress` and renders
      the returned table (`#`, priority, status, title, labels)
- [ ] With no `--status`/`--all` filter, `done` tasks are hidden from the
      default view
- [ ] `--status`, `--priority`, `--milestone` filters combine with AND when
      more than one is given
- [ ] `ls` is treated as an exact alias for `list`, not a separate behavior

---

### S4: Sync — push-create (new local task → new issue)

**Invocation:** `/task-sync sync` with a local task that has no
`issue_number` yet and a configured tracker remote

**Must:**
- [ ] Builds the plan first via `sync --plan --json` (read-only — writes
      neither `tasks.json` nor `TASKS.md`, calls no write API)
- [ ] Renders the task under a **Creates** section (title, priority, labels,
      milestone) before asking for any decision
- [ ] Checks repo visibility (`gh repo view --json visibility` or the Gitea
      REST equivalent) before the **first** push/create in the session and
      warns explicitly if the repo is `PUBLIC`
- [ ] Only calls `sync --apply --decisions <file>` after the user has seen
      the plan and (for a public repo) given an explicit "yes"

**Must NOT:**
- [ ] Call `sync --apply` before `sync --plan` has been shown to the user
- [ ] Skip the public-repo visibility warning on the first create/push of the
      session

---

### S5: Sync — adopt a new remote issue

**Setup:** An issue exists on the tracker with no corresponding local task.

**Invocation:** `/task-sync sync`

**Must:**
- [ ] The plan's **Pulls** section includes the remote-only issue (`#<issue_
      number>`, resulting status/title) before any decision is requested
- [ ] On apply, the issue is adopted into `tasks.json` as a new local task
      linked by `issue_number`, and `TASKS.md` is regenerated to reflect it
- [ ] Does not require a user decision for a pure remote-only pull (only
      genuine conflicts and confidentiality findings need one)

---

### S6: Sync — conflict surfaced, never auto-resolved

**Setup:** A task's local fields and its linked issue's remote fields have
both changed since `last_synced` (`CHANGED_BOTH`).

**Invocation:** `/task-sync sync`

**Must:**
- [ ] The plan's **Conflicts** section renders the task as a side-by-side
      table (`local` vs `remote`, each changed field) with the tool's
      last-write-wins `recommendation` shown as a hint only
- [ ] Explicitly asks the user to choose `local` or `remote` for this task —
      never applies the recommendation automatically
- [ ] If the user does not answer, the conflict is left undecided in the
      decisions file, `apply` leaves that task untouched, and it resurfaces
      on the next `sync --plan`

**Must NOT:**
- [ ] Pre-select or silently apply the `recommendation` without an explicit
      user choice
- [ ] Drop the conflict from the rendered plan because a recommendation
      exists

---

### S7: Confidentiality disposition — secret flagged

**Setup:** A local task's `body` scheduled to be pushed contains a
recognizable secret/token shape (e.g. a `ghp_`-prefixed string).

**Invocation:** `/task-sync sync`

**Must:**
- [ ] The plan's `confidentiality_findings` (already computed inside
      `sync --plan --json` — no separate scan step) surface the finding at
      `CRITICAL` severity with task, field, category, and a redacted
      preview — never the full secret
- [ ] Asks the user to disposition it explicitly as one of `keep`, `redact`,
      `remove`, or `anonymize`
- [ ] Does not let this task's create/push proceed to `apply` past a
      `CRITICAL` finding without an explicit disposition decision

**Must NOT:**
- [ ] Print the full secret value anywhere in the rendered plan or chat
      output
- [ ] Silently drop the finding or default it to `keep`

---

### S8: Confidentiality disposition — redact/anonymize applied

**Setup:** Continuing S7, the user disposition the finding as `anonymize`.

**Must:**
- [ ] Applies the disposition via `task-sync scan-apply --decisions <file>`
      before `sync --apply` (per the SKILL.md ordering), swapping in a
      stable `<<TERM_xxxxxx>>` token so the same term maps to the same
      token on reuse
- [ ] `scan-apply` saves `tasks.json` and regenerates `TASKS.md` after
      applying the disposition
- [ ] A subsequent scan of the same unchanged content is skipped (the
      content-hash review memory recognizes it was already reviewed)

---

### S9: Prune — done tasks older than the threshold

**Setup:** A task is `status: done` with `closed_at` more than
`config.prune_closed_after_days` (default 30) days in the past, and its
linked issue is closed on the tracker.

**Invocation:** `/task-sync sync --apply --decisions <file>` (following a
plan the user has already reviewed), or `/task-sync status`

**Must:**
- [ ] `status` calls out the task as prune-eligible in its health hint
      rather than silently reporting "health: ok"
- [ ] `sync --apply` prunes the task (removes it from `tasks.json`) as part
      of the apply step and regenerates `TASKS.md` to reflect the removal
- [ ] A `done` task closed for fewer than the threshold days is left in
      place, not pruned

**Must NOT:**
- [ ] Prune a task that is not `status: done`
- [ ] Prune during `sync --plan`/`--dry-run` (both are read-only and must
      write nothing)

## Rubric

| Criterion | Pass Threshold |
|-----------|-----------------|
| `init` runs automatically before any subcommand when `tasks.json` is missing | Required |
| Every mutating direct subcommand (`add`/`edit`/`done`/`remove`) goes through the bundled tool, not hand-rolled JSON edits | Required |
| `sync --plan --json` is always built and rendered before any `sync --apply` | Required |
| Conflicts are always surfaced for an explicit user decision, never auto-resolved by the recommendation | Required |
| `CRITICAL` confidentiality findings block that item's apply until dispositioned; full secret values are never printed | Required |
| Public-repo visibility warning fires before the first push/create of the session | Required |
| Prune only removes `done` tasks past the configured threshold, only during `--apply` | Required |
| `list`/`ls` filtering and default `done`-hiding behavior match the tool's documented semantics | Should |
