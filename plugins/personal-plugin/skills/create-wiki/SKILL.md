---
name: create-wiki
description: Set up a persistent, LLM-maintained wiki inside any project. Creates a wiki/ directory with sources, pages, schema, and navigation files, seeds initial pages from project discovery, and injects CLAUDE.md rules that make Claude automatically maintain the wiki during normal work sessions.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*)
paths:
  - wiki/sources/**/*
  - CLAUDE.md
  - LAB_NOTEBOOK.md
---

# Create Wiki

Set up a persistent, LLM-maintained knowledge base inside a project following Andrej Karpathy's LLM Wiki pattern. The wiki uses a three-layer architecture:

- **Sources** (`wiki/sources/`) — Human-curated raw documents. Immutable. Claude reads but never modifies.
- **Pages** (`wiki/pages/`) — LLM-generated markdown pages. Claude owns these entirely — creates, updates, deletes as needed.
- **Schema** (`wiki/schema.yaml`) — Configuration defining categories, conventions, and maintenance thresholds. Co-evolves with use.

The key insight: the tedious part of maintaining a knowledge base is not the reading or thinking — it's the bookkeeping. LLMs excel at updating cross-references and maintaining consistency across dozens of pages without fatigue. Humans curate sources and ask questions. Claude handles everything else.

## Proactive Triggers

Suggest this skill when:
1. A project is accumulating complexity — multiple integrations, services, or domain-specific concepts
2. Context is being lost between sessions — the same questions keep coming up
3. Multiple sessions or people are working on the same project
4. The user mentions "I keep forgetting..." or "what was that decision about..."
5. A project has significant domain knowledge that isn't captured in code comments or README
6. LAB_NOTEBOOK.md entries contain durable knowledge that deserves a more structured home

**Do NOT fire when:**
- A `wiki/` directory already exists with an `index.md` — redirect to `/wiki status` instead
- The project is trivial (single file, no domain complexity)
- The user explicitly declines structured knowledge management

## Input

**Arguments:** `$ARGUMENTS`

Supported arguments:
- `init` — Full initialization: discover project context, create wiki structure, seed pages, inject CLAUDE.md rules
- `status` — Show wiki health (redirects to `/wiki status`)
- No arguments — Same as `init` if no wiki exists, same as `status` if one does

## Entry-Point: Init vs Maintenance Mode

**Before doing anything else**, determine which mode to run:

```text
IF wiki/ directory exists AND wiki/index.md exists:
    → Run MAINTENANCE MODE (see below)
ELSE:
    → Run INITIALIZATION MODE (On `init` section below)
```

Check for wiki existence:
```bash
test -f wiki/index.md && echo "EXISTS" || echo "NOT_FOUND"
```

### Maintenance Mode (wiki already exists)

Used when `paths:` auto-activation fires (a source file or CLAUDE.md changed) OR when the user invokes with `status`.

**Maintenance mode is idempotent** — running it twice produces the same result. It updates, never re-initializes.

#### Maintenance Step 1: Identify Changed Sources

Determine what triggered the skill (if auto-activated via `paths:`):
- If triggered by `wiki/sources/**/*` — a source file was added or modified
- If triggered by `CLAUDE.md` — project rules changed; wiki pages covering architecture or conventions may be stale
- If triggered by `LAB_NOTEBOOK.md` — new findings may be wiki-worthy; check for extractable durable knowledge
- If invoked directly — check recent git changes: `git diff --name-only HEAD~1 HEAD`

#### Maintenance Step 2: Update Relevant Wiki Pages

For each changed source:
1. Read the changed file
2. Identify which existing `wiki/pages/*.md` pages reference or relate to it (check frontmatter `sources:` fields and content body links)
3. For source files in `wiki/sources/`: re-ingest the source, update pages whose content depends on it
4. For `CLAUDE.md` changes: update pages in the `architecture`, `decisions`, or `operations` categories if rules changed meaningfully
5. For `LAB_NOTEBOOK.md` changes: read the new entries (look for headings dated after the last `## [YYYY-MM-DD] ingest` entry in `wiki/log.md`); extract wiki-worthy findings; create or update pages

**Idempotency rule:** Before creating a new page, check whether a page for that topic already exists in `wiki/index.md`. If it does, update the existing page rather than creating a duplicate.

#### Maintenance Step 3: Update index.md and log.md

- Update `wiki/index.md` for any created or modified pages
- Append to `wiki/log.md`:
  ```
  ## [YYYY-MM-DD] update | Maintenance triggered by <trigger-description>
  Changed: <list of pages updated>
  Source: <what triggered the run>
  ```

#### Maintenance Step 4: Report

Print a brief summary:
```text
Wiki maintenance complete.

  Trigger:  <what file changed>
  Updated:  <N pages updated or created>
            - Page Title (category)
  Skipped:  <N pages checked, no changes needed>
```

---

## Instructions

### On `init` (or no wiki exists):

Execute ALL steps below. Do not skip any.

#### Step 1: Project Discovery

Before creating the wiki, perform a thorough survey of existing project state. The goal: seed the wiki with real content from day one. An empty wiki has no gravity — nobody will maintain it. A wiki with useful content gets maintained.

**1a. Read project documentation:**
- `CLAUDE.md` — project rules, architecture notes, operational conventions
- `README.md`, `docs/` — project purpose, architecture, setup instructions
- `LAB_NOTEBOOK.md` — decisions, findings, experiment history (if exists)
- `LEARNINGS.md`, `PROGRESS.md` — distilled knowledge (if exists)
- Any `*PLAN*.md`, `*SPEC*.md`, `*DESIGN*.md` files

**1b. Read project metadata:**
- `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `*.csproj` — dependencies, project name, scripts
- Configuration files — `.env.example`, `tsconfig.json`, `docker-compose.yml`, etc.
- `git log --oneline -20` — recent activity, active areas

**1c. Survey project structure:**
- Directory layout — identify major components, modules, services
- Entry points — `src/index.*`, `src/main.*`, `app.*`, `__main__.py`
- Test infrastructure — `tests/`, `__tests__/`, test config files

**1d. Extract durable knowledge:**
While reading, actively extract:
- **Architecture patterns** — how components relate, data flow, key interfaces
- **Technology decisions** — what was chosen and why (from CLAUDE.md rules, commit messages, config)
- **Domain concepts** — business rules, terminology, domain-specific logic
- **Integration details** — external APIs, services, dependencies, their configuration
- **Operational knowledge** — deployment, monitoring, troubleshooting patterns

**If an existing `wiki/` directory with `index.md` is found:** Do NOT recreate. Report to the user and redirect to `/wiki status`.

#### Step 2: Create Directory Structure

Create the following structure in the project root:

```text
wiki/
├── index.md              # Content catalog organized by category
├── log.md                # Append-only chronological record
├── schema.yaml           # Wiki configuration and conventions
├── README.md             # Human-readable usage guide
├── sources/              # Human-curated raw documents (immutable)
│   └── .gitkeep
└── pages/                # LLM-generated wiki pages
    └── .gitkeep
```

#### Step 3: Generate schema.yaml

Create `wiki/schema.yaml` with smart defaults:

```yaml
version: 1

categories:
  - architecture     # System design, component relationships, data flow
  - decisions        # Key choices with rationale and alternatives
  - concepts         # Domain concepts, glossary, terminology
  - entities         # Services, tools, teams, external systems
  - integrations     # APIs, dependencies, external system interfaces
  - operations       # Deployment, monitoring, runbooks, troubleshooting
  - reference        # Config values, standards, lookup tables

naming:
  convention: kebab-case
  extension: .md

page_frontmatter:
  required: [title, category, created, updated]
  optional: [sources, related, tags]

maintenance:
  auto_update_triggers:
    - architecture_decisions
    - new_integrations
    - significant_code_changes
    - debugging_insights
    - dependency_changes
    - domain_knowledge
  lint_interval_days: 7
  staleness_threshold_days: 30
```

Users can edit this file later to add project-specific categories, adjust thresholds, or change conventions.

#### Step 4: Seed Initial Pages

Based on Step 1 discovery, create 3-8 initial wiki pages in `wiki/pages/`. Priority order:

1. **Project architecture overview** — from README + directory structure survey
2. **Key decisions** — from CLAUDE.md rules, LAB_NOTEBOOK decisions, git history
3. **Technology stack** — from package files, configs, detected frameworks
4. **Domain concepts** — from any domain-specific docs, business rules, terminology
5. **Active integrations** — from config files, API references, docker-compose
6. **Operational patterns** — from deployment scripts, CI/CD, monitoring setup

Each page must have complete YAML frontmatter:

```yaml
---
title: Page Title
category: architecture
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
related:
  - pages/related-page.md
tags: [relevant, tags]
---
```

**Quality bar for seeded pages:** Each page should contain enough information that a new Claude session reading it would learn something useful. Don't create placeholder pages with just a title — write substantive content based on what you discovered. If you can't write at least 3-4 meaningful paragraphs about a topic, it doesn't need its own page yet.

**Cross-references:** As you create pages, add bidirectional links in the `related` frontmatter and in the content body. Every page should link to at least one other page.

#### Step 5: Generate index.md

Create `wiki/index.md` populated with the seeded pages:

```markdown
# Wiki Index

> Auto-maintained by Claude. Updated on every page create/update/delete.
> Last updated: YYYY-MM-DD | Last lint: never

## Architecture
- [Project Architecture](pages/project-architecture.md) — High-level system design and component relationships

## Decisions
- [Technology Choices](pages/technology-choices.md) — Key technology decisions with rationale
_...etc for each seeded page..._

## Concepts
_No pages yet._

## Entities
_No pages yet._

## Integrations
_No pages yet._

## Operations
_No pages yet._

## Reference
_No pages yet._

---
**Stats:** N pages across 7 categories
```

Include a section for every category from schema.yaml, even if empty. Populate with actual seeded pages where they exist.

#### Step 6: Generate log.md

Create `wiki/log.md` with the initialization entry:

```markdown
# Wiki Log

> Append-only chronological record. Parseable by prefix.
> Verbs: `create` | `update` | `delete` | `ingest` | `lint` | `query`

## [YYYY-MM-DD] create | Wiki initialized
Seeded N pages from project discovery.
Pages created: page-1.md, page-2.md, page-3.md, ...
Categories populated: architecture, decisions, ...
```

#### Step 7: Generate wiki/README.md

Create `wiki/README.md` — a human-readable guide:

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

#### Step 8: Inject CLAUDE.md Section

Append the following section to the project's CLAUDE.md. If no CLAUDE.md exists, create one with this section. If one exists, append at the end.

**Before injecting:** Check that no existing `## Project Wiki` section is already present. If found, skip injection and report to the user.

**The section to inject:**

```markdown
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
```

#### Step 9: LAB_NOTEBOOK.md Integration

If the project has a `LAB_NOTEBOOK.md`, append the following to the CLAUDE.md wiki section (after Rule 7):

```markdown
### Lab Notebook to Wiki Pipeline
When LAB_NOTEBOOK.md entries contain findings that represent durable, reusable
knowledge (not ephemeral session state), distill those findings into wiki pages.
The notebook captures raw experiments; the wiki captures distilled understanding.
Periodically review recent notebook entries and extract wiki-worthy content.
```

#### Step 10: Verify Setup

After creating all files, confirm:
1. `wiki/` directory exists with: `index.md`, `log.md`, `schema.yaml`, `README.md`, `sources/`, `pages/`
2. `wiki/index.md` is populated with seeded pages (not just empty category placeholders)
3. `wiki/pages/` contains the seeded page files with valid YAML frontmatter
4. `wiki/schema.yaml` has all 7 categories and maintenance config
5. `CLAUDE.md` has the `## Project Wiki — Persistent Knowledge Base` section with all 7 rules
6. If `LAB_NOTEBOOK.md` exists, the pipeline section was added

#### Step 11: Report to User

Print a summary:

```text
Wiki initialized.

  Directory:  wiki/ created with sources/, pages/, index, log, schema, README
  Pages:      N pages seeded from project discovery
              - Page Title 1 (category)
              - Page Title 2 (category)
              - ...
  CLAUDE.md:  7 wiki maintenance rules injected
  Notebook:   [Lab notebook pipeline added | No LAB_NOTEBOOK.md found]

Next steps:
  - Drop source documents into wiki/sources/ and run /wiki ingest <path>
  - Ask questions with /wiki query <topic>
  - Check health with /wiki lint
  - View stats with /wiki status
  - Customize categories and thresholds in wiki/schema.yaml
```

### On `status` (wiki already exists):

Redirect to `/wiki status`. If the `/wiki` skill is available, invoke it. Otherwise, provide a basic status report:
1. Count pages by category
2. Show last 5 log entries
3. Check if CLAUDE.md wiki section exists

## Relationship to Existing Documentation

The wiki doesn't replace other documentation patterns — it complements them:

| Existing pattern | Relationship to wiki |
|-----------------|----------------------|
| `LAB_NOTEBOOK.md` | Notebook captures raw experiments and ephemeral state. Wiki captures distilled, durable knowledge. Periodically extract insights from notebook into wiki pages. |
| `LEARNINGS.md` | Learnings captures distilled wisdom from sessions. Wiki organizes knowledge by topic with cross-references. They can coexist — learnings is linear, wiki is structured. |
| `PROGRESS.md` / session handoffs | Progress tracks session-level work. Wiki tracks project-level knowledge. Wiki-worthy findings from progress notes should become wiki pages. |
| `README.md` | README is the public-facing entry point. Wiki is the deep internal reference. README stays concise; wiki goes deep. |
| Git commit messages | Commits record what changed. Wiki records what we know and why. |
| `CLAUDE.md` | CLAUDE.md has operational rules. Wiki has knowledge. The CLAUDE.md wiki section tells Claude how to maintain the wiki; the wiki itself holds the knowledge. |
| Memory system (MEMORY.md) | Memory is cross-project, cross-session. Wiki is per-project, durable knowledge. Memory remembers user preferences and project context; wiki remembers how the system works. |

## Design Principles

- **Seeded, not empty.** The wiki starts with useful content from project discovery. Empty scaffolds don't get maintained.
- **Judgment, not mandates.** Wiki update rules are judgment calls ("wiki-worthy"), not blocking preconditions. Over-triggering floods the wiki with noise.
- **Per-project scope.** Each project gets its own wiki. Cross-project knowledge belongs in the memory system.
- **Git-tracked.** The entire wiki is version-controlled. Review wiki changes in PRs, revert bad updates, track knowledge evolution.
- **LLM-owned pages.** Humans should not hand-edit `wiki/pages/`. Let Claude maintain consistency. Report errors to Claude and it will fix pages plus cross-references.
- **Human-owned sources.** Files in `wiki/sources/` are immutable input. Claude reads but never modifies.
