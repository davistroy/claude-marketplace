---
name: wiki
description: "Wiki operations: ingest source documents into wiki pages, lint for health issues, query the wiki for answers, propagate resolved facts, and report status. Supports both /create-wiki layouts (wiki/ + schema.yaml) and OKF-bundle layouts (kb/ + AGENTS.md contract)."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(python3:*)
---

# Wiki Operations

Explicit operations for maintaining and querying a project's LLM-maintained wiki. For automatic maintenance, the CLAUDE.md rules injected by `/create-wiki` handle it. This skill is for when you want to explicitly process a source document, run a health check, search the wiki, propagate a resolved fact, or check its status.

## Input

**Arguments:** `$ARGUMENTS`

Supported subcommands:
- `ingest <path>` — Process a source document into wiki pages
- `lint` — Run health checks on wiki structure and content
- `query <topic>` — Search wiki and synthesize an answer
- `propagate <fact>` — Sweep all pages for stale variants of a newly resolved fact (OKF mode; see OKF Bundle Mode)
- `status` — Show wiki stats, health, and recent activity
- No arguments — Show help

## Pre-flight Check: Layout Detection

Before executing any subcommand, detect which wiki layout this project uses. Check in this order:

1. **Legacy layout** — `wiki/schema.yaml` exists:
   - Contract source: `wiki/schema.yaml` (categories, `lint_interval_days`, `staleness_threshold_days`, `page_frontmatter.required`)
   - Pages: `wiki/pages/` · Sources: `wiki/sources/` · Index: single `wiki/index.md` · Log: `wiki/log.md`
   - Execute the subcommand sections below exactly as written.
2. **OKF bundle layout** — an `AGENTS.md` exists at the repo root AND a `kb/index.md` declares `okf_version` in its frontmatter:
   - Contract source: **`AGENTS.md`** — read it in full before any operation; it defines the type vocabulary, required frontmatter, sensitivity tiers, ingest procedure, and lint rules. The contract file governs; this skill adapts to it.
   - Pages: `kb/**` (one concept per file; path = identity) · Sources: `sources/` (immutable, dated; outside the bundle) · Indexes: **per-directory `index.md`** · Log: `kb/log.md`
   - Execute the subcommand sections below **with the deltas defined in "OKF Bundle Mode"**.
3. **Neither found:**
   ```text
   No wiki found in this project.
   Run /create-wiki to set up one, or add an AGENTS.md contract + kb/ OKF bundle.
   ```

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

## OKF Bundle Mode

When layout detection found an OKF bundle (`kb/` + AGENTS.md contract), apply these deltas to the subcommands above. The AGENTS.md contract always wins over this section where they disagree.

### Mode-wide substitutions

| Legacy concept | OKF equivalent |
|---|---|
| `wiki/pages/*.md` | `kb/**/*.md` (one concept per file, stable kebab-case slugs) |
| `wiki/sources/` | `sources/` subdirectories per the contract (dated, immutable — never edited, only added) |
| Single `wiki/index.md` | Per-directory `index.md`; `kb/index.md` is the bundle root |
| `wiki/log.md` `## [date] verb` entries | `kb/log.md` — follow the target repo's own entry convention (read the top entries and match them; do NOT impose the legacy format) |
| `schema.yaml` frontmatter rules | Contract-defined frontmatter (`type` from the contract's vocabulary, plus its required extensions such as `owner`, `last_verified`, `sensitivity`) |
| Skill-native lint checks | **Delegate:** if `tools/lint.py` exists, run `python3 tools/lint.py` (and its documented flags) instead of reimplementing checks; report its output verbatim |

### `ingest <path>` in OKF mode

Follow the contract's ingest pipeline exactly. Baseline (confirm against the contract):

1. Raw material lands in the appropriate `sources/` subdirectory, dated, immutable.
2. **Synthesize, never mirror:** reconcile the new source against existing pages; a page reflects ALL sources, not the latest one.
3. Mark uncertainty with the contract's marker vocabulary (e.g., `[INFERRED]`, `[CONFLICT]`, `[UNDOCUMENTED]`, `[OPEN]`, `[DATED: …]`). Never present unverified claims as fact.
4. Update every touched section's `index.md`; update `owner`/`last_verified` on touched pages; append to `kb/log.md` in the repo's own format.
5. Run the lint gate; commit per the repo's commit conventions.

**Ingest lessons checklist** (apply every time; each is a documented failure mode):
- [ ] Distinguish **current-state from designed-vision** content — vision documents try hard to read as current state.
- [ ] Flag artifacts older than ~12 months `[DATED: …]` and treat their claims as historical.
- [ ] **Negative results are retrieval-bounded:** a source not finding something is evidence of absence-of-retrieval, not absence.
- [ ] **Scope-inference trap:** converging sources can still be wrong when they share a scope blind spot — mark such conclusions `[LIKELY]`, not fact.
- [ ] Normalize name variants against the most authoritative source; note the variant.
- [ ] After resolving any conflict or marker, run the `propagate` sweep (below) — partial propagation is the dominant contradiction source.
- [ ] Respect sensitivity tiers: content on restricted pages never migrates to ordinary pages.

### `propagate <fact>` (OKF mode)

Input: one newly confirmed fact (e.g., "X = Y", "A leads both B and C", a corrected spelling).

1. Grep ALL pages (including indexes and the glossary) for every stale variant, alias, and contradicting statement.
2. Present the full edit list (file, line, current text → proposed text) before changing anything.
3. Apply edits; close or annotate the related markers/conflict-ledger entries; update `last_verified` on touched pages.
4. Append one consolidated `kb/log.md` entry naming the fact, its source, and every page touched; run lint.

### `query <topic>` in OKF mode

Navigate index-first (`kb/index.md` → section index → page), then grep. Cite pages by relative path. Respect sensitivity: do not surface restricted-page content unless the user explicitly authorizes. Where the wiki records an open marker on the answer, say so — the marker IS part of the answer.

### `status` in OKF mode

If `tools/lint.py --status` exists, run it and present its output (pages, marker census, asks, conflicts) plus the top of `kb/log.md` for recent activity. Otherwise, derive equivalents from the bundle: page count, marker counts, index table states.

## Error Handling

- **Neither a legacy `wiki/schema.yaml` nor an OKF `AGENTS.md` + `kb/index.md` bundle is found:** report "No wiki found" and direct the user to `/create-wiki` or to add an OKF bundle (see Pre-flight Check step 3) rather than guessing a layout.
- **`ingest <path>` given a path that doesn't exist or isn't readable:** report the error and stop before touching `wiki/sources/` or `wiki/pages/`.
- **`ingest` target file already exists in `wiki/sources/` with the same name:** warn the user and ask whether to overwrite or rename (see Protocol step 1) rather than silently overwriting.
- **`query <topic>` finds no relevant pages:** report "No wiki pages found" and suggest ingesting a source or checking for a different name (see "Handle no results") rather than fabricating an answer.
- **`lint` finds auto-fixable structural issues:** only apply them if the user confirms "yes" (see Auto-Fix) — content issues (stale/contradictions/duplicates) are never auto-fixed, only reported.
- **OKF mode: `tools/lint.py` referenced by the contract doesn't exist:** derive equivalents manually from the bundle (page/marker/index counts) instead of failing the subcommand (see Mode-wide substitutions and `status` in OKF mode).
