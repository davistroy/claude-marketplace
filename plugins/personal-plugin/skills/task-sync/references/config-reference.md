# `tasks.json` Config Reference

`tasks.json` is the canonical store: a header plus the task list. It is
written canonically (stable key order, tasks sorted by `id`, 2-space indent,
trailing newline, atomic write) so two saves of unchanged content are
byte-identical and sync diffs stay minimal and readable.

## Header

```json
{
  "provider": "github",
  "repo": "owner/repo",
  "last_sync_at": "2026-07-18T00:00:00+00:00",
  "config": {
    "prune_closed_after_days": 30,
    "adopt_closed_within_days": 0,
    "sensitive_terms": []
  },
  "tasks": [ ... ]
}
```

| Field | Type | Meaning |
|---|---|---|
| `provider` | `"github"` \| `"gitea"` \| `"none"` | Auto-detected by `init` from the `origin` remote (`github.com` → `github`, any other host → `gitea`, no/unparseable remote → `none`, local-only mode). |
| `repo` | `string \| null` | `owner/repo`-shaped path from the remote URL. `null` in `none` mode. |
| `last_sync_at` | `string (ISO-8601) \| null` | Set by `sync --apply`; `null` until the first successful apply. |
| `config` | object | Per-repo settings, see below. |
| `tasks` | array | The task list — see `command-reference.md` for the fields on each task (`id`, `title`, `body`, `status`, `priority`, `labels`, `milestone`, `issue_number`, timestamps, `last_synced`, `confidentiality`). |

## `config` block

| Key | Type | Default | Meaning |
|---|---|---|---|
| `prune_closed_after_days` | int | `30` | How long a `done` task with a closed issue stays in `tasks.json` before `sync --apply` drops the row. The issue itself is never deleted or reopened — this only affects the local record. |
| `adopt_closed_within_days` | int | `0` | Its own, independent gate on `NEW_REMOTE` adoption: "is this issue recent enough to be worth adopting at all," a different question from prune's "how long do we keep completed work." `0` (the default) means **adopt open issues only** — any closed issue is skipped, no matter how recently it closed. A larger value is a grace window, e.g. `3` also adopts issues closed within the last 3 days (the comparison is strict-greater-than, so exactly 3 days ago is still adopted). An **absent** key — any `tasks.json` from before this setting existed, since `init` is a no-op on an existing file — resolves to `0` (open-only); it does **not** inherit `prune_closed_after_days`. An invalid value falls back to `0`; a negative value clamps to `0`. This gates first-time adoption only — an already-adopted task's `CHANGED_REMOTE` updates apply in full regardless of how long ago its issue closed. `sync --adopt-all` bypasses this key entirely and mirrors every issue in history. |
| `sensitive_terms` | list[string] | `[]` | Per-repo confidentiality terms (client/brand names, etc.) matched case-insensitively, whole-word, against `title`/`body` during the confidentiality scan. **The only place such terms may ever appear** — never hardcode them in the tool or the skill. |
| `gitea_url` | string | (unset) | Base URL for the Gitea REST API, used when `provider: "gitea"`. Written automatically by `init` for an http(s) `origin` (left unset for an ssh `origin` — see `init` in SKILL.md). Not needed for `provider: "github"` (uses the `gh` CLI's own auth). |

Editing `sensitive_terms` (e.g., to add a repo-specific brand name before the
first sync) is the one config change expected to happen by hand — edit
`tasks.json` directly, or `edit`/re-`init` do not currently expose it as a
flag.

### Gitea base URL / token resolution

`sync`'s `_build_provider` resolves the Gitea base URL and token independently,
env always overriding whatever `init`/`tea login` already configured:

- **base URL:** `$GITEA_URL` → `config.gitea_url` (written by `init`, see
  above) → the `url` from `~/.config/tea/config.yml`'s default (or first)
  login.
- **token:** `$GITEA_TOKEN` → the `token` from the same `tea` config login.

A missing/unreadable `tea` config is treated as "no credentials from that
source," not an error — the error only surfaces if every source above is
exhausted, and it names the remedy (`tea login add`, or export
`$GITEA_TOKEN`/`$GITEA_URL`).

## Committing `tasks.json` (optional, per-repo), `TASKS.md` never

Whether `tasks.json` is committed is a per-repo choice, not something the
tool enforces. Committing it is a reasonable default: it is the source of
truth, and committing makes `last_synced` durable across machines and gives
sync history via git blame. But a repo may deliberately keep it local
instead — this repo (`claude-marketplace`) gitignores both `tasks.json` and
`TASKS.md` (see `.gitignore`) so local task state never leaks into commits
here. `TASKS.md`, by contrast, should never be committed anywhere: it is a
pure, regenerated view (see `render.py`'s `render_open`) with no state of its
own, and committing it would just create merge-conflict noise on every task
change. `init` adds `TASKS.md` to the target repo's `.gitignore` for this
reason — see SKILL.md's "First Run: Auto-Init" section.
