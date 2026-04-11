---
name: wiki
description: "Wiki operations: ingest source documents into wiki pages, lint for health issues, query the wiki for answers, and report status. Companion to /create-wiki which handles initial setup."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
---

# Wiki Operations

Explicit operations for maintaining and querying a project's LLM-maintained wiki. For automatic maintenance, the CLAUDE.md rules injected by `/create-wiki` handle it. This skill is for when you want to explicitly process a source document, run a health check, search the wiki, or check its status.

## Input

**Arguments:** `$ARGUMENTS`

Supported subcommands:
- `ingest <path>` — Process a source document into wiki pages
- `lint` — Run health checks on wiki structure and content
- `query <topic>` — Search wiki and synthesize an answer
- `status` — Show wiki stats, health, and recent activity
- No arguments — Show help

## Pre-flight Check

Before executing any subcommand:

1. **Verify wiki exists:** Check that `wiki/` directory exists with `wiki/index.md`. If missing:
   ```text
   No wiki found in this project.
   Run /create-wiki to set up the wiki first.
   ```
2. **Read schema:** Read `wiki/schema.yaml` to get current configuration — categories, `lint_interval_days`, `staleness_threshold_days`, naming conventions.
3. **Read index:** Read `wiki/index.md` to get current page inventory.

## Instructions

### No Arguments — Show Help

If invoked without arguments, display:

```text
Wiki Operations
===============
Usage: /wiki <subcommand> [args]

Subcommands:
  ingest <path>    Process a source document into wiki pages
  lint             Run health checks on wiki structure and content
  query <topic>    Search wiki and synthesize an answer
  status           Show wiki stats, health, and recent activity

Examples:
  /wiki ingest docs/architecture-spec.md
  /wiki lint
  /wiki query "authentication flow"
  /wiki status

Setup: If no wiki exists, run /create-wiki first.
```

### Subcommand: `ingest <path>`

Process a source document into wiki pages. This is the primary way to grow the wiki — drop a document in and let Claude extract, organize, and cross-reference the knowledge.

#### Protocol

1. **Validate source.** Verify the path exists and is readable. If the file is not already in `wiki/sources/`, copy it there (preserve original filename). If a file with the same name exists in `wiki/sources/`, warn the user and ask whether to overwrite or rename.

2. **Read thoroughly.** Read the entire source document. Understand its structure, key topics, and how it relates to existing wiki content.

3. **Extract knowledge.** Identify discrete topics to become wiki pages or page updates:
   - Entities — services, tools, teams, external systems
   - Concepts — domain terms, business rules, patterns
   - Decisions — choices made with rationale and alternatives
   - Architecture — component relationships, data flow, interfaces
   - Integrations — APIs, protocols, configuration, failure modes
   - Operations — deployment steps, monitoring, troubleshooting

4. **Create or update pages.** For each extractable topic:
   - Check `wiki/index.md` — does a page on this topic already exist?
   - **If page exists:** Read it, merge new information, update the `updated` date in frontmatter, add source to `sources` frontmatter field.
   - **If no page exists:** Create a new page in `wiki/pages/` with complete frontmatter:
     ```yaml
     ---
     title: Page Title
     category: {from schema.yaml categories}
     created: YYYY-MM-DD
     updated: YYYY-MM-DD
     sources:
       - sources/filename.ext
     related:
       - pages/related-page.md
     tags: [tag1, tag2]
     ---
     ```
   - Page content should be substantive — clear headings, concrete examples, enough detail that a future session learns something useful.
   - One concept per page. Split large topics into separate pages rather than creating monoliths.

5. **Maintain cross-references.**
   - Add `related` entries to the new/updated page's frontmatter
   - Update `related` entries on LINKED pages (bidirectional)
   - Add inline links in content body where relevant
   - Check existing pages — should any of them now reference this new content?

6. **Update index.md.** Add new pages or update summaries for changed pages. Format: `- [Title](pages/filename.md) — one-line summary`. Update the stats line at the bottom. Maintain category organization.

7. **Update log.md.** Append:
   ```markdown
   ## [YYYY-MM-DD] ingest | filename.ext
   Source: sources/filename.ext
   Created: page-1.md, page-2.md
   Updated: existing-page.md
   Cross-references updated: 5 pages
   ```

8. **Report results.**
   ```text
   Ingested: filename.ext
   Created: N new pages
   Updated: M existing pages
   Pages touched:
     - [new] Page Title 1 (category)
     - [new] Page Title 2 (category)
     - [updated] Existing Page (category)
   Cross-references: K bidirectional links maintained
   ```

#### Guidance on Page Granularity

- **One concept per page.** A page about "Authentication" should not also cover "Database Schema."
- **Focused but complete.** Each page should fully cover its topic — don't split artificially.
- **Target 5-15 page touches** per substantive source. A one-page config doc might touch 2-3 pages. A 30-page architecture spec might touch 20+. This is guidance, not a hard rule.
- **Prefer updating over creating.** If a page on a related topic exists, merge the new information rather than creating a near-duplicate.

### Subcommand: `lint`

Run health checks on wiki structure and content. Identifies issues across three severity levels and offers auto-fix for structural problems.

#### Check Catalog

Execute checks in this order — structural first, then content, then best-effort:

**Structural Checks:**

| Check | Severity | Detection |
|-------|----------|-----------|
| Broken index entries | Error | Index.md links that point to missing files in `wiki/pages/` |
| Missing required frontmatter | Error | Pages missing fields listed in `schema.yaml` `page_frontmatter.required` |
| Orphan pages | Warning | Files in `wiki/pages/` not listed in `wiki/index.md` |

**Content Checks:**

| Check | Severity | Detection |
|-------|----------|-----------|
| Stale pages | Warning | Pages with `updated` field older than `staleness_threshold_days` from schema.yaml |
| Missing source files | Warning | Pages with `sources` entries pointing to files not in `wiki/sources/` |
| Island pages | Info | Pages with empty `related` field (no cross-references) |

**Best-Effort Checks:**

| Check | Severity | Detection |
|-------|----------|-----------|
| Duplicate topics | Warning | Multiple pages with substantially similar titles or overlapping content |
| Contradictions | Error | Pages making conflicting claims about the same entity or concept |

Note: contradiction and duplicate detection is inherently fuzzy. Focus on obvious cases — e.g., page A says "we use PostgreSQL" while page B says "the MySQL database." Flag these for human review rather than claiming certainty.

#### Report Format

Group by severity, errors first:

```text
Wiki Lint Report
================

ERRORS (must fix):
  [E1] Broken index: index.md links to pages/old-auth.md which does not exist
  [E2] Missing frontmatter: pages/api-design.md is missing required field 'category'

WARNINGS (should fix):
  [W1] Orphan page: pages/scratch-notes.md is not listed in index.md
  [W2] Stale page: pages/deploy-guide.md last updated 45 days ago (threshold: 30)
  [W3] Missing source: pages/design-spec.md references sources/spec-v1.md which does not exist

INFO:
  [I1] Island page: pages/glossary.md has no cross-references

Summary: 2 errors, 3 warnings, 1 info across N pages
```

#### Auto-Fix

After reporting, offer auto-fix for fixable issues:

```text
Auto-fixable issues found:
  - Add orphan pages/scratch-notes.md to index.md
  - Add missing 'category' field to pages/api-design.md frontmatter
  - Remove broken index entry for pages/old-auth.md

Apply auto-fixes? (yes/no)
```

Only fix structural issues automatically. Content issues (stale pages, contradictions, duplicates) require human judgment — report them but don't auto-fix.

#### Post-Lint Updates

1. Update `Last lint` timestamp in `wiki/index.md`
2. Append to `wiki/log.md`:
   ```markdown
   ## [YYYY-MM-DD] lint | 2 errors, 3 warnings, 1 info
   Auto-fixed: added orphan to index, filled missing frontmatter, removed broken entry
   Remaining: 2 stale pages, 1 missing source, 1 island page
   ```

### Subcommand: `query <topic>`

Search the wiki for a topic and synthesize an answer from wiki content, with citations.

#### Protocol

1. **Search index.** Read `wiki/index.md` and identify candidate pages by title and summary that relate to the topic.

2. **Search content.** Use Grep to search `wiki/pages/` for the topic keywords. Include fuzzy matches — related terms, abbreviations, synonyms.

3. **Read relevant pages.** Read all pages identified in steps 1-2. Note connections between pages.

4. **Synthesize answer.** Produce a concise, well-structured answer drawing from wiki content. Do not just list page contents — synthesize across pages, connect dots, highlight relationships.

5. **Cite sources.** For every claim or fact, cite the wiki page: "Based on [Page Title](pages/filename.md)."

6. **Offer page creation.** If the answer required significant cross-page synthesis or revealed new connections not captured in any single page, offer:
   ```text
   This synthesis draws from N pages and connects information not captured
   in any single page. Create a wiki page for this topic? (yes/no)
   ```
   If yes, create the page following standard page creation protocol (frontmatter, cross-references, index update, log entry).

7. **Handle no results.** If no relevant pages are found:
   ```text
   No wiki pages found for "{topic}".
   Consider:
     - Ingesting relevant source documents: /wiki ingest <path>
     - Updating pages after researching this topic
     - Checking if the topic is known by a different name
   ```

8. **Update log.** Append to `wiki/log.md`:
   ```markdown
   ## [YYYY-MM-DD] query | {topic}
   Pages consulted: N
   Answer synthesized from: page-1.md, page-2.md, ...
   New page created: [yes — new-page.md | no]
   ```

### Subcommand: `status`

Show a dashboard view of wiki health, stats, and recent activity. Designed to be scannable in 10 seconds.

#### Report Format

```text
Wiki Status
===========

Pages by Category:
  | Category       | Count |
  |----------------|-------|
  | architecture   | 3     |
  | decisions      | 2     |
  | concepts       | 1     |
  | entities       | 0     |
  | integrations   | 2     |
  | operations     | 1     |
  | reference      | 0     |
  | TOTAL          | 9     |

Sources: N files in wiki/sources/

Recent Activity (last 5):
  [YYYY-MM-DD] ingest | architecture-spec.md
  [YYYY-MM-DD] create | Wiki initialized
  ...

Health:
  Last lint: YYYY-MM-DD (N days ago) [OK | OVERDUE — run /wiki lint]
  Stale pages: N pages not updated in >30 days
  Orphan pages: N pages not in index
  Island pages: N pages with no cross-references
  CLAUDE.md: Wiki rules present [OK | MISSING — run /create-wiki to reinject]
```

#### Edge Cases

- **Empty wiki (just initialized):** Show zero counts, note "Wiki just initialized. Add source documents with /wiki ingest or let auto-maintenance build pages during normal work."
- **No log entries:** Show "No activity recorded yet."
- **Missing schema.yaml:** Warn: "schema.yaml not found. Using defaults. Run /create-wiki to regenerate."
- **CLAUDE.md missing wiki section:** Warn loudly: "CLAUDE.md is missing the wiki maintenance rules. Auto-maintenance is not active. Run /create-wiki to reinject the rules."
