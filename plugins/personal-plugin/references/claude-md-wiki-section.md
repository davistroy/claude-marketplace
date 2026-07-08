# CLAUDE.md Wiki Section Template

**Purpose:** Verbatim CLAUDE.md injection block emitted by `skills/create-wiki/SKILL.md` Step 8 — the 7 wiki-maintenance rules appended to a project's CLAUDE.md so Claude auto-maintains the wiki during normal work. Content must be copied byte-for-byte; do not paraphrase or reformat. Rule 3 contains its own nested fenced YAML example, so the wrapper below uses four backticks to contain it correctly.

**Consumer:** `skills/create-wiki/SKILL.md` — Step 8.

---

## Template

````markdown
## Project Wiki — Persistent Knowledge Base

This project maintains an LLM-generated wiki at `wiki/`. The wiki compounds
understanding across sessions — you own the wiki layer and maintain it as
part of normal work. Use `/wiki` commands for explicit operations.

### Wiki Structure
- `wiki/sources/` — Human-curated raw documents. **Read only. Never modify.**
- `wiki/pages/` — LLM-generated pages. You create, update, and delete these.
- `wiki/index.md` — Content catalog by category. Update on every page change.
- `wiki/log.md` — Append-only activity log. Append on every wiki operation.
- `wiki/schema.yaml` — Categories, conventions, maintenance config.

### Rule 1: Check the Wiki First
Before researching any topic related to this project, check `wiki/index.md`.
If a relevant page exists, read it before doing fresh research. The wiki may
already contain what you need — and if it's incomplete, you'll know what to
add rather than duplicating effort.

### Rule 2: Update When Wiki-Worthy
During normal work, update the wiki when you encounter or produce **durable
knowledge** — information useful in future sessions, not just this one:

- Architecture decisions with rationale and alternatives considered
- New integrations — API surface, configuration, gotchas, failure modes
- Non-obvious system behavior discovered during debugging
- Dependency changes — new libraries, version upgrades, deprecations
- Domain concepts, business rules, or terminology learned from context
- Significant code changes — new modules, refactored interfaces, changed contracts

**Judgment standard:** Would a future Claude session benefit from this being
written down? If yes, it's wiki-worthy. Session-specific task progress,
ephemeral debugging state, or information already in git history is NOT
wiki-worthy.

### Rule 3: Page Format
Every page in `wiki/pages/` requires YAML frontmatter:

```yaml
---
title: Page Title
category: {from schema.yaml categories}
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []       # source file paths if applicable
related: []       # paths to related wiki pages
tags: []          # searchable tags
---
```

Content: clear headings, concrete examples, cross-links to related pages.
Aim for completeness over brevity — this is a reference, not a summary.

### Rule 4: Cross-Reference Maintenance
When creating or updating a page:
1. Link to related pages in the content body
2. Update `related` frontmatter on THIS page
3. Update `related` frontmatter on LINKED pages (bidirectional)
4. Check if existing pages should now reference this one

### Rule 5: Index and Log Maintenance
- **index.md**: Update on every page create/update/delete. Format:
  `- [Title](pages/filename.md) — one-line summary`
- **log.md**: Append on every wiki operation. Format:
  `## [YYYY-MM-DD] verb | description` — verbs: create, update, delete,
  ingest, lint, query

### Rule 6: Lint on Session Start
If the last lint entry in `wiki/log.md` is older than the configured
`lint_interval_days` in `schema.yaml` (default: 7 days), run a quick
lint check at session start. Report issues but don't block work.

### Rule 7: Sources Are Immutable
Files in `wiki/sources/` are human-curated input. Never modify, rename,
or delete them. Only read. If a source contains errors, note the
correction in the relevant wiki page with attribution.
````
