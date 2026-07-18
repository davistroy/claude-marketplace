# TASKS.md

`TASKS.md` is a generated, read-only view produced by `render.render_open` /
`render.render_summary` from the canonical `tasks.json` store — it is not
itself a source of truth and is never hand-edited.

**Phase 1 status:** the renderer (`src/task_sync/render.py`) exists and is
unit-tested, but nothing in this tool writes `TASKS.md` to disk yet, and no
`.gitignore` entry for it exists yet either.

**Deferred to Phase 5/6:** the `sync`/`status` subcommands will write
`TASKS.md` at the repo root (or wherever `tasks.json`'s config designates),
and the repo's `.gitignore` will gain a `TASKS.md` entry at that point —
tracking a generated, frequently-changing file in git would create noise on
every sync run for no benefit, the same reasoning already applied to
`output/` (visual-explainer) and `reports/` in the root `.gitignore`.
