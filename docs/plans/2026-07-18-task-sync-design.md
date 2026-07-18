# task-sync — Skill Design

**Date:** 2026-07-18
**Status:** Design approved (not yet implemented)
**Author:** Troy Davis (brainstormed with Claude)
**Skill home:** `plugins/personal-plugin/skills/task-sync/`

## Purpose

A per-repo task list, stored as JSON in the repo, that stays reconciled with the repo's issue tracker — GitHub (via `gh`) or Gitea (via `tea`). Run the skill in any repo: it creates the list if absent, and thereafter you can manage tasks locally from a Claude session (the skill renders sortable/filterable tables and edits the file for you) or see the same tasks online as tracker issues. One list, two windows onto it.

## Decisions

| # | Decision | Rationale / rejected alternatives |
|---|----------|-----------------------------------|
| Storage | Single JSON file, canonicalized (stable key order, tasks sorted by id) | Clean git diffs, deterministic sync. Rejected YAML/Markdown-as-storage — you never hand-edit, so machine-reliability beats hand-editability. |
| Interface | The skill is the interface; it renders tables in-session and regenerates a read-only `TASKS.md` for glancing | Lightweight. Rejected a standalone interactive TUI app — large maintenance surface that duplicates what the terminal Claude session already gives. |
| Edit model | You primarily edit locally; the tracker is a peer that also changes on its own | A pure one-way push would fight dependabot, PR-close automation, and web-filed issues. |
| Sync | Reconciling 3-way merge against a committed `last_synced` base | Handles both directions; the committed base makes multi-machine safe. |
| Conflict tiebreaker | Last-write-wins by `updated_at`, but **report genuine two-sided conflicts** for the user to resolve | You are in a Claude session when syncing, so ask rather than silently clobber. |
| Archiving | Prune `done` tasks from the JSON after N days; the tracker's closed issues are the permanent archive | Keeps the JSON a live working list. Safe in every repo because closed issues persist in the tracker forever. |
| Confidentiality | One list, always the sanitized version; a scan offers keep/anonymize/redact/remove per finding, remembered by content hash | Rejected a second gitignored private file — the user wants exactly one list. |
| Grouping | An optional `milestone` field (tracker-native), not a bespoke `project` field | Round-trips to GitHub/Gitea milestones; a freeform field would not. |
| Relationship to plans | `IMPLEMENTATION_PLAN.md` stays separate; task list holds backlog items, plans are execution blueprints derived from them | Different altitude and lifecycle; flattening plans into tasks loses the structure `/implement-plan` needs. |

## Data model

**Status values** (map onto native issue state + `status/*` labels):

| Status | In the tracker | Meaning |
|--------|----------------|---------|
| `backlog` | open + `status/backlog` | captured, not committed to |
| `todo` | open (default, no status label) | ready to work |
| `in-progress` | open + `status/in-progress` | actively working |
| `blocked` | open + `status/blocked` | waiting on something |
| `done` | closed | completed (pruned after N days) |

No `archived` status — prune-on-close covers it; the closed issue is the archive.

**Task record:**

```json
{
  "id": "t-a1b2c3",
  "title": "Short summary",
  "body": "Longer markdown description",
  "status": "todo",
  "priority": "P2",
  "labels": ["area/ci"],
  "milestone": "prime-backlog",
  "issue_number": 42,
  "created_at": "...", "updated_at": "...", "closed_at": null,
  "last_synced": { "hash": "...", "at": "..." },
  "confidentiality": { "decision": "anonymize", "reviewed_hash": "...", "at": "..." }
}
```

`priority`, `labels`, `milestone`, and `confidentiality` are optional. Status maps to issue state + `status/*` label; `priority` maps to a `priority/*` label; `labels` map to freeform tracker labels.

**File header** (top of `tasks.json`): `provider` (github/gitea/none), `repo`, `last_sync_at`, and config such as the prune window and the sensitive-terms list.

## Files & interface

- **`tasks.json`** — repo root, **committed**. The list plus the `last_synced` merge base. Committed so the base travels between the user's two machines via git.
- **`TASKS.md`** — repo root, **gitignored**, regenerated each sync/list. A read-only terminal glance view. Not committed: it is derived (would churn every sync and conflict across machines), and "see it on the web" is already the tracker's job.

**Commands** (natural language or explicit; aliases in the last column):

| Intent | Command | Aliases / NL |
|--------|---------|--------------|
| Reconcile with tracker | `/task-sync` (default) | "sync my tasks" |
| See tasks | `/task-sync list [--status] [--priority] [--sort] [--milestone]` | `ls`; "show open P1s" |
| Add | `/task-sync add "title" [--priority --labels --milestone]` | "add a task to…" |
| Change | `/task-sync edit <id\|#> …` | "start task 3" |
| Complete | `/task-sync done <id\|#>` | `close`; "close 42" |
| Delete | `/task-sync remove <id\|#>` | `rm` |
| Overview | `/task-sync status` | "task summary" |

Safety: `sync --dry-run` previews the whole reconciliation with zero writes; first run in a repo auto-`init`s (`tasks.json` + provider detection).

**Example `list` / `ls` output:**

```
Open tasks — claude-marketplace  ·  github  ·  synced 2m ago

  #    Pri   Status         Title                                    Labels
  47   P1    in-progress    Wire the eval runner into CI             ci
  52   P2    todo           Add retry/backoff to the Gitea client    area/sync
  48   P2    blocked  #20   Migrate homeserver to 7.2.4              infra
  —    P3    backlog        Explore caching for list rendering       —
  51   P3    todo           Document the confidentiality flow        docs

  5 open  ·  2 todo · 1 in-progress · 1 blocked · 1 backlog     (12 done, hidden)
```

`#` is the issue number (`—` = not yet synced); a blocked row shows what it waits on; `done` is hidden by default. Filters just narrow the same view.

## Confidentiality

One list, always the safe version — so `tasks.json` is fine to commit (even in a public repo) and fine to sync.

On `sync` (and on `add`/`edit`), the skill scans each task's title/body/labels for confidential info: secret/token patterns plus a configurable sensitive-terms list (client names, internal hostnames), reusing the `leak-risk-audit` and `remove-ip` machinery. For each new finding it offers four dispositions:

- **keep** — judged fine (false positive / acceptable).
- **anonymize** — rewrite to a meaning-preserving generic ("Acme's prod-db-01" → "the client's production DB").
- **redact** — mask the span (`[REDACTED]`).
- **remove** — drop that content, or the whole task if it is entirely sensitive.

The choice is applied to the stored task (so the one list stays clean) and remembered as `confidentiality: {decision, reviewed_hash, at}`. Unchanged content is honored silently on later syncs; editing the task changes the hash and triggers a re-scan. The skill tunes its recommendation by repo visibility (`gh repo view --json visibility`) — a public repo steers away from "keep."

Trade-off: once anonymized/redacted, the raw detail is gone from the task (that is the point). If the raw detail matters, it lives in the lab notebook, not here.

## Sync algorithm

1. Detect provider from the remote → `gh` / `tea` / **none** (local-only mode).
2. Check visibility; warn if public. Fetch open + recently-closed issues.
3. Match tasks ↔ issues on `issue_number`; classify each against the `last_synced` base: new-local, new-remote, changed-one-side, changed-both.
4. Confidentiality scan on outbound content → apply remembered dispositions, prompt on anything new.
5. Apply: create issues for new-local (save numbers back), adopt new-remote as tasks, push/pull one-sided changes, resolve two-sided by last-write-wins and report genuine conflicts. Map `status` ↔ `status/*` labels both ways; `priority` ↔ `priority/*`.
6. Prune `done` tasks closed > N days; refresh `last_synced`; regenerate `TASKS.md`.
7. Print a summary: created / adopted / pushed / pulled / conflicts / pruned.

### Edge cases

- **No remote** → pure local task list; everything except sync works.
- **Offline / auth fails** → sync aborts cleanly, local edits preserved; `add`/`edit`/`ls` still work.
- **First sync in an existing repo** → adopts all current issues as tasks (including dependabot's).
- **Issue deleted on the tracker** → flag and ask keep-local-or-drop; never silent.
- **Two machines** → `git pull` before syncing so you reconcile against the latest base; the committed `last_synced` makes it safe.
- **Rate limits / pagination** → batch tracker reads.

## Relationship to `IMPLEMENTATION_PLAN.md`

The task list and the plan operate at different altitudes and do not merge:

- **Task list** = the durable, synced backlog — issue-level items with status/priority (what / whether).
- **`IMPLEMENTATION_PLAN.md`** = a transient execution blueprint for a chosen chunk — phases, Files Affected, Acceptance Criteria, Depends-On, runnable Definition-of-Done, model-tier routing (how). This structure exists to drive `/implement-plan`; a flat task list cannot hold or run it.

They form a pipeline (as this repo's 2026-07-17 session demonstrated): backlog issues → `/ultra-plan` → plan → `/implement-plan` → close issues → backlog reflects done. Plans reference the tasks they implement (generalize the existing "Recommendation Ref" to issue numbers); a body of work is grouped by a **milestone**, which is the "project" identifier and round-trips to the tracker.

**Do not move away from markdown plans** — `/implement-plan` depends on their structure and archived plans are a real execution record.

## Packaging

A new skill at `plugins/personal-plugin/skills/task-sync/SKILL.md` under house conventions (`name:` matching the directory, body < 500 lines, detail in `references/`). It shells out to `gh`/`tea` and reuses the `leak-risk-audit`/`remove-ip` scan patterns.

### Open implementation decision (settle at plan time)

The deterministic reconcile — 3-way match, conflict detection, status/label mapping, prune — is a natural **small bundled Python tool** (`tools/task-sync/`, like `bpmn2drawio` / `visual-explainer`, testable to the repo's coverage bar), with `SKILL.md` orchestrating it and owning the interactive parts (confidentiality prompts, conflict calls). The lighter alternative is the skill driving `gh`/`tea`/`jq` in bash. Lean: the Python tool, for testability.

## Out of scope (for now)

- **Cross-machine private tasks** — with one committed list there is no private lane that travels between machines; private detail is sanitized out, not hidden. Revisit only if a real need appears.
- **A standalone interactive TUI** — the in-session table is the interactive view.
- **Tighter plan integration** (phase 2) — `/ultra-plan` registering its plan as a milestone and ensuring its items exist as tasks, and `/implement-plan` closing those tasks as phases complete. Ship task-sync standalone first.

## Next step

Turn this into an implementation plan via `/ultra-plan` (or `/create-plan`), resolving the Python-tool-vs-bash fork first, then `/implement-plan`.
