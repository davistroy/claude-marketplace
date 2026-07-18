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
| `prune_closed_after_days` | int | `30` | How long a `done` task with a closed issue stays in `tasks.json` before `sync --apply` drops the row. The issue itself is never deleted or reopened — this only prunes the local record. |
| `sensitive_terms` | list[string] | `[]` | Per-repo confidentiality terms (client/brand names, etc.) matched case-insensitively, whole-word, against `title`/`body` during the confidentiality scan. **The only place such terms may ever appear** — never hardcode them in the tool or the skill. |
| `gitea_url` | string | (unset) | Base URL for the Gitea REST API, used when `provider: "gitea"`. Falls back to `$GITEA_URL` if unset; the token comes from `$GITEA_TOKEN` (or `~/.config/tea/config.yml` for the visibility check — see SKILL.md's public-repo guardrail). Not needed for `provider: "github"` (uses the `gh` CLI's own auth). |

Editing `sensitive_terms` (e.g., to add a repo-specific brand name before the
first sync) is the one config change expected to happen by hand — edit
`tasks.json` directly, or `edit`/re-`init` do not currently expose it as a
flag.

## Why this file is committed, `TASKS.md` is not

`tasks.json` is the source of truth and is meant to be committed — it is what
makes `last_synced` durable across machines and gives sync history via git
blame. `TASKS.md` is a pure, regenerated view (see `render.py`'s
`render_open`) with no state of its own; committing it would just create
merge-conflict noise on every task change. `init` adds `TASKS.md` to the
target repo's `.gitignore` for this reason — see SKILL.md's "First Run:
Auto-Init" section.
