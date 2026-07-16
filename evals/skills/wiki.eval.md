---
command: wiki
type: skill
fixtures: []
---

# Eval: /wiki (skill)

## Purpose

Explicit wiki maintenance and query operations: `ingest <path>`, `lint`, `query <topic>`, `propagate <fact>`, and `status`. Supports two layouts — the legacy `/create-wiki` layout (`wiki/` + `schema.yaml`) and the OKF bundle layout (`kb/` + `AGENTS.md` contract) — and must detect which one a project uses before doing anything else. Good behavior: correct layout detection, pages that synthesize rather than duplicate, citations grounded in actual wiki content (never fabricated), and structural auto-fixes gated behind explicit confirmation. Has no `disable-model-invocation`, so it may also be proactively suggested when a conversation matches its domain.

## Fixtures

None — requires a scratch project directory set up per scenario with either a legacy `wiki/` tree, an OKF `kb/`+`AGENTS.md` bundle, or neither, plus a small source document to ingest where noted.

## Setup

Build each scenario's wiki state in a disposable scratch directory before invoking. For legacy scenarios: `wiki/schema.yaml`, `wiki/pages/`, `wiki/sources/`, `wiki/index.md`, `wiki/log.md`. For OKF scenarios: `AGENTS.md` at the repo root and `kb/index.md` with `okf_version` in its frontmatter, plus `kb/**` pages and a `sources/` tree.

## Test Scenarios

### S1: No arguments — help

**Invocation:** `/wiki`

**Must:**
- [ ] Displays the subcommand list (`ingest`, `lint`, `query`, `status`) with usage examples
- [ ] Notes that `/create-wiki` is the setup path if no wiki exists

**Must NOT:**
- [ ] Execute any subcommand or touch any file

---

### S2: Legacy layout — `status` dashboard

**Setup:** Legacy `wiki/` tree with a handful of pages across categories, a recent `wiki/log.md` entry, and `schema.yaml` present.

**Invocation:** `/wiki status`

**Must:**
- [ ] Detects the legacy layout via `wiki/schema.yaml` (Pre-flight Check step 1)
- [ ] Shows a pages-by-category table with a correct TOTAL row
- [ ] Shows sources count, recent activity (last 5 from `wiki/log.md`), and a Health block (last-lint recency, stale/orphan/island counts, CLAUDE.md wiki-rules presence)
- [ ] Flags `Last lint` as `OVERDUE` if it exceeds `schema.yaml`'s lint interval, and says so explicitly

**Must NOT:**
- [ ] Write or modify any file (status is read-only)

---

### S3: Legacy layout — `ingest <path>` happy path

**Setup:** Legacy `wiki/` tree with 1-2 existing pages; a new source document covering a mix of new and already-documented topics.

**Invocation:** `/wiki ingest <path-to-source>`

**Must:**
- [ ] Copies the source into `wiki/sources/` (unless already there)
- [ ] Reads the entire source before extracting topics
- [ ] Creates new pages with complete frontmatter (title, category, created, updated, sources, related, tags) for genuinely new topics
- [ ] Merges new information into the existing page (updates `updated` date, adds to `sources`) instead of creating a near-duplicate page for a topic already covered
- [ ] Updates `related` bidirectionally on both new/updated pages and any pages they now cross-reference
- [ ] Updates `wiki/index.md` (new entries + stats line) and appends a `## [YYYY-MM-DD] ingest | filename` entry to `wiki/log.md`
- [ ] Final report matches the documented format (Ingested/Created/Updated/Pages touched/Cross-references)

**Must NOT:**
- [ ] Create a second page duplicating an existing page's topic instead of merging into it
- [ ] Split one concept across multiple pages, or cram unrelated concepts into one page

---

### S4: Legacy layout — `ingest` source-name collision

**Setup:** A file with the same name as one already present in `wiki/sources/`.

**Invocation:** `/wiki ingest <path-to-same-named-source>`

**Must:**
- [ ] Detects the name collision in `wiki/sources/` before copying
- [ ] Asks the user whether to overwrite or rename rather than picking one silently

**Must NOT:**
- [ ] Overwrite the existing source file without asking
- [ ] Proceed with page extraction before the collision is resolved

---

### S5: OKF bundle layout — `ingest <path>` follows contract deltas

**Setup:** `AGENTS.md` at the repo root and `kb/index.md` with `okf_version` in its frontmatter (OKF bundle layout), plus at least one existing `kb/**` page touching the same topic as the new source.

**Invocation:** `/wiki ingest <path-to-source>`

**Must:**
- [ ] Detects the OKF bundle layout (Pre-flight Check step 2) rather than falling back to legacy or reporting "no wiki found"
- [ ] Reads `AGENTS.md` in full and treats it as governing (its type vocabulary, required frontmatter, and marker vocabulary win over this skill's own defaults where they differ)
- [ ] Lands the raw source in the correct dated `sources/` subdirectory, immutable
- [ ] Reconciles the new source against the existing `kb/**` page (synthesizes — reflects all sources, not just the latest) instead of overwriting it
- [ ] Marks any uncertain or conflicting claims with the contract's marker vocabulary (e.g. `[INFERRED]`, `[CONFLICT]`, `[DATED: ...]`) rather than stating them as settled fact
- [ ] Updates the touched section's `index.md` and `owner`/`last_verified` on touched pages
- [ ] Appends to `kb/log.md` matching that file's own existing entry format, not the legacy `## [date] verb` convention

**Must NOT:**
- [ ] Write to `wiki/pages/`, `wiki/sources/`, or `wiki/index.md` (legacy paths) when an OKF bundle is present
- [ ] Present an `[INFERRED]` or `[CONFLICT]`-worthy claim as plain fact

---

### S6: Neither layout found

**Setup:** A project with no `wiki/schema.yaml` and no `AGENTS.md` + `kb/index.md` bundle.

**Invocation:** `/wiki status` (or any subcommand)

**Must:**
- [ ] Reports that no wiki was found and directs the user to `/create-wiki` or to add an `AGENTS.md` + `kb/` OKF bundle

**Must NOT:**
- [ ] Create `wiki/` or `kb/` structure unprompted
- [ ] Guess a layout and proceed with the subcommand anyway

---

### S7: `lint` — severity grouping and auto-fix boundary

**Setup:** A legacy wiki containing at least one of each: a broken index entry (index.md links to a missing page), an orphan page (exists in `wiki/pages/` but not in index.md), a stale page (older than `staleness_threshold_days`), and an island page (empty `related`).

**Invocation:** `/wiki lint`

**Must:**
- [ ] Groups findings by severity — ERRORS, then WARNINGS, then INFO — with a correct summary count
- [ ] Correctly classifies the broken index entry and any missing-required-frontmatter case as ERROR, orphan/stale/missing-source as WARNING, island pages as INFO
- [ ] Offers auto-fix only for the structural issues (orphan-not-in-index, missing frontmatter field, broken index entry) and asks "Apply auto-fixes? (yes/no)" before touching anything
- [ ] Updates `Last lint` in `wiki/index.md` and appends a summarized entry to `wiki/log.md` after the run

**Must NOT:**
- [ ] Auto-fix content issues (stale pages, duplicate topics, contradictions) even if the user says yes to the structural auto-fix prompt
- [ ] Apply any auto-fix before the user answers the confirmation prompt
- [ ] Claim certainty on a fuzzy contradiction/duplicate finding instead of flagging it for human review

---

### S8: `query <topic>` — happy path with citations

**Setup:** A wiki with 2-3 pages relevant to a topic, where a good answer requires connecting information across more than one page.

**Invocation:** `/wiki query "<topic>"`

**Must:**
- [ ] Searches `wiki/index.md` for candidate pages, then greps `wiki/pages/` content (including fuzzy/synonym matches)
- [ ] Reads all identified relevant pages before answering
- [ ] Synthesizes a connected answer rather than concatenating page contents verbatim
- [ ] Cites the specific wiki page for every claim (e.g. "Based on [Page Title](pages/filename.md)")
- [ ] Offers to create a new page when the synthesis crosses pages in a way no single page captures
- [ ] Appends a `## [YYYY-MM-DD] query | {topic}` entry to `wiki/log.md`

**Must NOT:**
- [ ] Present a claim without a page citation

---

### S9: `query <topic>` — no relevant pages (no-fabrication boundary)

**Setup:** Same wiki as S8, but query a topic with no relevant coverage.

**Invocation:** `/wiki query "<unrelated topic>"`

**Must:**
- [ ] Reports "No wiki pages found for {topic}" and suggests ingesting a source, updating pages, or checking for a different name

**Must NOT:**
- [ ] Fabricate or infer an answer not grounded in any actual wiki page content
- [ ] Cite a page that doesn't actually address the topic just to appear grounded

---

### S10: `propagate <fact>` (OKF mode) — review before apply

**Setup:** OKF bundle with a fact that has stale variants scattered across 2+ pages, including an index and the glossary page (e.g. a corrected spelling or a changed ownership fact).

**Invocation:** `/wiki propagate "<newly confirmed fact>"`

**Must:**
- [ ] Greps ALL pages, including indexes and the glossary, for stale variants/aliases/contradicting statements — not just the pages already known to discuss the fact
- [ ] Presents the full edit list (file, line, current text -> proposed text) before making any change
- [ ] Only applies edits after the list has been presented
- [ ] Closes or annotates related markers/conflict-ledger entries and updates `last_verified` on touched pages
- [ ] Appends one consolidated `kb/log.md` entry naming the fact, its source, and every page touched, then runs lint

**Must NOT:**
- [ ] Edit any page before the edit list has been shown
- [ ] Skip the glossary or index files when sweeping for stale variants (partial propagation is the documented dominant contradiction source)

---

### S11: `propagate` invoked under a legacy (non-OKF) layout

**Setup:** A legacy `wiki/` project (no `AGENTS.md`/OKF bundle) — `propagate` is only specified under "OKF Bundle Mode" and doesn't appear in the legacy help/subcommand list.

**Invocation:** `/wiki propagate "<fact>"`

**Must:**
- [ ] Recognizes that `propagate`'s documented procedure is OKF-specific and does not silently execute an undefined legacy-mode substitute
- [ ] Tells the user this rather than guessing at an equivalent, or asks how they'd like stale facts corrected in the legacy layout

**Must NOT:**
- [ ] Invent an ad hoc legacy propagate procedure not grounded in the skill's contract and present it as the documented behavior
- [ ] Edit pages under an assumed procedure without flagging that it's improvised

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Layout detected correctly (legacy vs OKF vs neither) before any subcommand executes | Required |
| `ingest` merges into existing pages on topic overlap instead of duplicating | Required |
| Source-name collisions in `ingest` are never silently overwritten | Required |
| OKF contract (`AGENTS.md`) governs over the skill's own legacy-mode defaults when they differ | Required |
| `lint` auto-fixes only structural issues, and only after explicit confirmation | Required |
| `query` never presents an uncited or fabricated claim; reports plainly when nothing is found | Required |
| `propagate` always presents the full edit list before applying any change, and sweeps indexes/glossary | Required |
| Undefined behavior (e.g. `propagate` under legacy layout) is surfaced, not silently improvised | Should |
