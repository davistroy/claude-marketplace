# Wiki README Template

**Purpose:** Verbatim `wiki/README.md` content emitted by `skills/create-wiki/SKILL.md` Step 7 — the human-readable usage guide written into every project's `wiki/README.md` on initialization. Content must be copied byte-for-byte; do not paraphrase or reformat.

**Consumer:** `skills/create-wiki/SKILL.md` — Step 7.

---

## Template

```markdown
# Project Wiki

This is a persistent, LLM-maintained knowledge base for this project. It follows a three-layer architecture where humans own the source material and Claude maintains the knowledge pages.

## How It Works

**You (human) do:**
- Drop source documents into `wiki/sources/` (specs, transcripts, research, design docs)
- Ask Claude to ingest them: `/wiki ingest sources/new-doc.md`
- Ask questions: `/wiki query "how does authentication work?"`
- Edit `wiki/schema.yaml` to customize categories or conventions

**Claude does:**
- Reads sources, extracts knowledge, creates/updates wiki pages
- Maintains cross-references between pages
- Keeps the index current
- Flags stale or contradictory content via lint checks
- Auto-updates pages when discovering wiki-worthy knowledge during normal work

## Directory Structure

| Path | Owner | Purpose |
|------|-------|---------|
| `sources/` | Human | Raw documents. Immutable — Claude reads, never modifies. |
| `pages/` | Claude | Generated wiki pages. Claude creates, updates, deletes. |
| `schema.yaml` | Shared | Categories, conventions, thresholds. Edit to customize. |
| `index.md` | Claude | Content catalog by category. Auto-updated. |
| `log.md` | Claude | Chronological activity record. Append-only. |

## Commands

| Command | Description |
|---------|-------------|
| `/wiki ingest <path>` | Process a source document into wiki pages |
| `/wiki lint` | Run health checks on wiki structure and content |
| `/wiki query <topic>` | Search wiki and synthesize an answer |
| `/wiki status` | Show wiki stats, health, and recent activity |

## Customization

Edit `wiki/schema.yaml` to:
- Add or remove categories
- Change the staleness threshold (default: 30 days)
- Change the lint interval (default: 7 days)
- Adjust naming conventions

## Important

- **Do not hand-edit files in `pages/`** — let Claude maintain consistency. If you spot an error, tell Claude and it will fix the page plus any cross-references.
- **Sources are immutable** — once a file is in `sources/`, don't modify or delete it. Claude's pages may reference specific content.
- **The wiki is git-tracked** — review wiki changes in PRs, revert bad updates, track knowledge evolution over time.
```
