---
name: explain-project
description: Generate a comprehensive, annotated technical overview document for any project/repo, written for a smart non-CS reader. Analyzes the codebase, writes a deep-dive document following a proven structure template, and produces a styled Word document with sidebars, glossary, inline annotations, and optional generated images. Use when a project needs an explanatory document that makes the system understandable to non-technical stakeholders.
effort: high
---

<!-- ═══════════════════════════════════════════════════════════════════
  EXPLAIN PROJECT SKILL
  ═══════════════════════════════════════════════════════════════════

  PURPOSE:
  Generates a comprehensive technical overview document (.docx) for any
  software project, written for a brilliant non-CS reader. The document
  includes all accessibility annotations baked in from the start:
  sidebars, glossary, inline definitions, and optional images.

  TARGET READER:
  A top-quintile intelligence mechanical engineer who has never taken
  a CS class. Sharp, process-oriented, comfortable with measurements
  and thresholds. Understands quality gates and structured problem-solving.

  INPUT MODES:
  1. Local project directory path (e.g., "C:\Users\...\my-project")
  2. Public GitHub URL (e.g., "https://github.com/owner/repo")
     - Clones to temp, generates doc to ~/Downloads, cleans up

  OUTPUT:
  A styled Word document (.docx) following the CFA brand guidelines,
  with the document structure adapted to the project's complexity.

  COMPANION TOOLS:
  Paths below are defaults on the author's machine. Override via flags or environment variables.
  - CLI tool: C:\Users\Troy Davis\dev\tools\doc-builder
    (python -m doc_builder create --content content.json --output doc.docx)
  - Structure template: C:\Users\Troy Davis\dev\info\technical-document-structure-template.md
  - Style guide: C:\Users\Troy Davis\dev\info\CFA_Word_Style_Guide.md
  - Image style: C:\Users\Troy Davis\dev\info\clean-style-sanitized.json
  - Image learnings: C:\Users\Troy Davis\dev\info\gemini-image-generation-learnings.md

  HISTORY:
  Built and tested 2026-03-27. Tested on 4 projects:
  - cfa/pipeline (complex ML pipeline, 25 pages)
  - cfa/kb-analysis (complex analysis pipeline, 21 pages)
  - stratfield/community-mgt (Next.js enterprise app)
  - personal/open-brain (multi-container AI knowledge system)
  ═══════════════════════════════════════════════════════════════════ -->

# Explain Project

Generate a comprehensive technical overview document for a project, written for a brilliant reader who lacks computer science training.

**Target reader:** A top-quintile intelligence mechanical engineer. Sharp, process-oriented, comfortable with measurements and thresholds, experienced with quality systems and structured problem-solving. Has never taken a CS class.

**Output:** A styled Word document (.docx) with all accessibility annotations baked in — sidebars, glossary, inline definitions, footnotes, developer section labels, and optionally generated images.

## Inputs

<!-- ─── INPUT PARSING ───
  Accept either a local filesystem path or a GitHub URL.
  GitHub URLs are shallow-cloned to /tmp, analyzed, then cleaned up.
  Output for GitHub repos goes to ~/Downloads by default.
─── -->

One required argument (either a local path OR a GitHub URL):
1. **Project directory path** -- a local directory containing the codebase to document
2. **OR GitHub URL** -- a public repo URL (e.g., `https://github.com/owner/repo`). The skill will clone it to a temp directory, analyze it, and output the document to the user's Downloads folder.

Optional flags:
- `--style PATH` -- Path to a markdown style guide for Word formatting (default: `$DOC_STYLE_GUIDE` env var if set; author's default: `C:\Users\Troy Davis\dev\info\CFA_Word_Style_Guide.md`)
- `--style-json PATH` -- Path to image style JSON for Nano Banana Pro (default: `$IMAGE_STYLE_JSON` env var if set; author's default: `C:\Users\Troy Davis\dev\info\clean-style-sanitized.json`)
- `--generate-images` -- Generate diagrams via Google Gemini and insert them (default: OFF — costs money)
- `--update` -- Incremental update mode: reads the existing document, diffs the codebase against the last generation (via git log since the commit hash in the document's freshness metadata), generates only changed sections, and preserves the user's manual refinements to unchanged sections
- `--output PATH` -- Output file path (default: `{project-dir}/docs/{project-name}-overview.docx`, or `~/Downloads/{repo-name}-overview.docx` for GitHub URLs)

Parse from the user's message. If neither a path nor URL is provided, ask.

### Detecting Previous Documents

Before starting a fresh generation, check for existing documents matching `docs/*-overview*.docx` in the project directory. If found:
1. Read the existing document to understand what it covers
2. Check git log for changes since the document was last generated (use the freshness metadata commit hash if available, otherwise file modification date)
3. Offer the user a choice: **update** (incremental, preserves manual edits) vs **regenerate** (full fresh generation)

In `--update` mode:
- Parse the existing document's section structure
- Diff the codebase to identify what changed (new files, modified stages, config changes)
- Generate only the sections affected by codebase changes
- Preserve the user's manual refinements to unchanged sections
- Update the Document Freshness metadata block with current values

### Handling GitHub URLs

<!-- ─── GITHUB FLOW ───
  Shallow clone keeps it fast. Only public repos — no auth complexity.
  Clean up after generation so we don't accumulate cloned repos.
─── -->

When the input is a GitHub URL (contains `github.com`):

1. **Clone the repo** to a temporary directory:
   ```bash
   git clone --depth 1 "{url}" "/tmp/explain-project-{repo-name}"
   ```
   Use `--depth 1` for shallow clone (faster, less disk).

2. **Set output path** to Downloads:
   ```
   C:\Users\Troy Davis\Downloads\{repo-name}-overview.docx
   ```

3. **Analyze and generate** using the same Phase 1-5 process as for local projects.

4. **Clean up** the cloned repo after document generation.

Note: Only public repos are supported (no authentication). For private repos, clone manually first and provide the local path.

## Process

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 1: DEEP PROJECT ANALYSIS

  This is where we build the understanding that drives the document.
  Read broadly first, then deeply into the components that matter most.
  Use the Explore agent for broad sweeps, direct reads for specifics.
  ═══════════════════════════════════════════════════════════════════ -->

### Phase 1: Deep Project Analysis

Use the Explore agent or direct file reading to build comprehensive understanding:

1. **Project identity:** Read README, CLAUDE.md, package.json/pyproject.toml, and top-level docs
2. **Architecture:** Map the directory structure, identify major components, entry points, and data flow
3. **Pipeline/stages:** Identify processing stages, their order, inputs/outputs, and dependencies
4. **Data models:** Read model definitions, schemas, configuration files
5. **Products/outputs:** What does the system produce? What consumes the output?
6. **Testing:** Test suite structure, coverage, evaluation approach
7. **Infrastructure:** What hardware/services does it depend on? How does it deploy?
8. **Technical vocabulary:** Catalog every CS/ML/domain term the project uses
9. **Runtime artifacts:** If the project produces output artifacts (reports, logs, dashboards, metrics files), read them. Look for:
   - Latest pipeline output in `output/` or similar directories (statistics, counts, timing)
   - Log files with timing data, cache hit rates, throughput numbers
   - Metrics or evaluation result files from recent runs
   - Configuration files with active thresholds, weights, and feature flags

   Ground the document in production reality, not code-reading estimates. Every production number cited in the document should trace back to an actual output artifact, not a guess derived from reading the code.

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 2: DOCUMENT PLANNING

  IMPORTANT: Read the structure template BEFORE planning.
  Not every project needs every section. A 200-line CLI tool gets 5 pages.
  A 16-stage ML pipeline gets 25. Let the project dictate depth.

  Present the plan to the user before writing — this is a checkpoint.
  ═══════════════════════════════════════════════════════════════════ -->

### Phase 2: Document Planning

**IMPORTANT:** Read the structure template at `$DOC_STRUCTURE_TEMPLATE` (author's default: `C:\Users\Troy Davis\dev\info\technical-document-structure-template.md`) before planning. It contains a complexity table that maps project size to expected document depth. Not every section applies to every project.

1. **Select Key Concept Sidebars (2-3):** Choose the foundational concepts THIS project relies on most. These will be the first things the reader sees.

2. **Plan the "Why This Approach" section (if warranted):** Identify 2-4 reasonable objections a skeptic would raise. What simpler approaches would people suggest? Why do they fail? Skip for simple projects where the approach is obvious. Where available, include:
   - Actual benchmark data from evaluation runs (precision, recall, F1 from test sets)
   - Specific evaluation results that justify design decisions
   - A cost/benefit table for the overall system vs. simpler alternatives (time to build, accuracy gained, maintenance burden)

3. **Design the worked example:** Choose a concrete, realistic input that will be traced through every stage. It should exercise the system's most important capabilities.

4. **Map the stage/component walkthrough:** List every processing stage or major component with:
   - What it transforms (input → output)
   - Why it matters (consequence of skipping)
   - How the worked example changes at this stage

5. **Plan images (3-5):** Identify where diagrams would most help.

   **Always generate:**
   - Data flow diagram — stages with their inputs and outputs, showing the transformation pipeline end to end
   - System architecture — infrastructure topology showing hardware, services, and their connections

   **Generate if applicable:**
   - Worked example transformation — showing how the running example changes at key stages
   - Dashboard/UI mockup — conceptual layout of any interactive output the system produces
   - Conceptual visualization of the novel/hardest technique

   **Never generate:**
   - Screenshots of code (not useful for the target reader)
   - Class diagrams or UML (too developer-focused for the ME audience)

6. **Build the glossary list:** Every CS/ML term that will appear in the document, with draft definitions at the right depth. Plan bookmark names for each entry (convention: `_glossary_` + lowercase_underscored_name). The glossary will be the hyperlink target for first-occurrence terms in the body text.

Present this plan to the user before writing. Format as a brief outline showing:
- Proposed sidebar topics
- "Why not just..." questions (if any)
- Worked example selection
- Stage/component list with one-line descriptions
- Image locations
- Glossary term count

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 3: DOCUMENT GENERATION

  Write section by section, following the proven patterns below.
  The key structural patterns that work for the ME audience:

  - "What happens / Why it matters / Our example becomes" for stages
  - 3-column comparison tables for "Why This Approach"
  - Concrete numbers and examples over abstract descriptions
  - Consequence-based reasoning ("if you skip this, X breaks")

  All technical terms must be explained INLINE at first use, not just
  in the glossary. The glossary is the safety net, not the primary tool.
  ═══════════════════════════════════════════════════════════════════ -->

### Phase 3: Document Generation

Write each section following the proven patterns:

**Executive Summary:**
- Key Concept Sidebars (2-3) at the top — these are pedagogical gateways for the most foundational concepts only; all other terms use the glossary hyperlink mechanism
- What goes in → what comes out (one sentence)
- Problem context (why the status quo fails)
- What the system does (high-level, naming major phases)
- Production numbers table (if available)
- Validation summary

**Why This Approach (if warranted):**
- 2-4 subsections, each a skeptic's question
- 3-column comparison tables where applicable
- Concrete data and failure modes, not abstract arguments
- Include actual benchmark data when available (e.g., evaluation precision/recall)
- Include a cost/benefit summary table for the overall system vs. alternatives

**Worked Example:**
- Show the actual input (raw data, article text, etc.)
- Explain why this example demonstrates the system's capabilities
- **Prefer real examples from production output** when available — they are automatically accurate and carry more weight with the reader
- If a fabricated example is necessary, state explicitly: "This is a representative example constructed to illustrate the process" — never present fabricated data as production output

**Stage-by-Stage / Component Walkthrough:**
For each stage or component, follow this template:
```
**What happens:** [concrete transformation]
**Why it matters:** [consequence of skipping]
**Our example becomes:** [running example after this stage]
**Technical details:** [developer-oriented, preceded by "Technical Reference" label]
```

**Products/Applications** (if applicable):
- What uses the pipeline output
- How end users interact with it

**Second Worked Example** (if the system has a distinct "use" phase):
- Trace a realistic query/request through the system
- Show intermediate results at each step

**Quality and Validation:**
- Testing summary table
- Evaluation approach
- Quality metrics and regression gates

**Technical Architecture:**
- Preceded by "Technical Reference" label
- Infrastructure, models, caching, concurrency

**How to Evaluate This System** (if appropriate):
- Decision-maker-oriented questions with pointers to answers

**Known Limitations and Coverage Gaps:**
This is a standard section for every document — the ME reader treats this as the specification sheet. Every product has specs AND limitations. Include:
- What the system does not cover (explicit scope boundaries)
- What data it excludes and why
- Edge cases it handles poorly or not at all
- Known accuracy limitations (false positive rates, failure modes)
- Scale or performance boundaries

**Current Operational State / Config Snapshot** (if the project has a production deployment):
Auto-populate from actual config files and latest run output:
- Current deployment topology (what runs where)
- Latest run metrics (pair counts, timing, cache hit rates — sourced from output artifacts)
- Active configuration snapshot (key thresholds, weights, enabled features — pulled from config files)
- Known issues or operational constraints

**What's Next / Roadmap** (if applicable):
- Planned improvements and known gaps

**Technical Glossary:**
- Dependency-ordered, not alphabetical
- Every term annotated inline at first use in the body
- Every entry bookmarked as a hyperlink target
- First body-text occurrence of each term hyperlinked to its glossary entry
- Key Concept sidebar boxes (2-3) for the most foundational concepts remain as pedagogical gateways; the hyperlinked glossary handles all other terms

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 3.5: VERIFICATION AGAINST RUNTIME DATA

  Every claim in the document must be verifiable. This phase catches
  stale thresholds, outdated counts, and features described as active
  that are actually disabled. Run this BEFORE assembling the final
  document — it's cheaper to fix claims in draft than in formatted output.
  ═══════════════════════════════════════════════════════════════════ -->

### Phase 3.5: Verification Against Runtime Data

Before assembling the final document, verify every factual claim against the actual project state:

1. **Config verification:** Read config files (YAML, JSON, .env) and confirm that every threshold, weight, or setting mentioned in the document matches the current config values. Flag any discrepancies.

2. **Production numbers verification:** Cross-reference every number cited in the document (article counts, pair counts, timing, accuracy metrics) against actual pipeline output, logs, or metrics files. Every production number must be sourced from actual output, not estimated from code.

3. **Feature state verification:** For every feature described in the document, check the production config to determine whether it is enabled or disabled. Features that are disabled in config must not be described as part of the standard processing flow (see Writing Guidelines: "Available vs Active Features").

4. **Staleness check:** Run `git log --since` against the date the document was last generated (or the date of the output artifacts used for production numbers). Flag any changes that would invalidate document claims.

5. **Flag for review:** Present any stale, incorrect, or unverifiable claims to the user before proceeding to assembly. Do not silently correct — the user needs to see what changed.

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 4: DOCUMENT ASSEMBLY

  The doc-builder CLI tool at dev/tools/doc-builder handles the
  mechanical Word document creation. Write content as structured JSON,
  then invoke the CLI.

  JSON SCHEMA — the content JSON must follow this structure:
  {
    "title": "System Name — Overview",
    "sidebars": [{"title": "...", "body": "..."}],
    "sections": [{"heading": "...", "level": 2, "content": [...]}],
    "glossary": [{"term": "...", "definition": "..."}],
    "footnotes": [{"id": 1, "text": "..."}],
    "images": [{"name": "...", "prompt": "..."}]
  }

  Content element types: paragraph, heading, table, list, blockquote,
  sidebar, tech_ref_label, image_placeholder, glossary_entry, rich_paragraph
  ═══════════════════════════════════════════════════════════════════ -->

### Phase 4: Document Assembly

Write the complete content as a JSON file following the doc-builder schema, then invoke the CLI tool:

```bash
python -m doc_builder create \
  --content "{content_json}" \
  --output "{output_path}" \
  [--generate-images] \
  [--style-json "{style_json}"]
```

The CLI tool is at `$DOC_BUILDER_PATH` (or `python -m doc_builder` if on PYTHONPATH; author's default: `C:\Users\Troy Davis\dev\tools\doc-builder`) and handles:
- Word document creation with proper CFA styling
- Sidebar callout box formatting (red left border, light grey background)
- Glossary appendix formatting (dependency-ordered, bold red terms)
- Tables with navy headers and alternating row stripes
- Image placeholders (teal left border) or generated images (square text wrap)
- Developer section labeling (italic "Technical Reference" labels)
- Footnote creation

**Document Freshness Metadata:** Include a metadata block at the end of the document (or as a document property) with:
- **Generated:** date of document generation (ISO 8601)
- **Git commit:** the HEAD commit hash at generation time
- **Pipeline run:** version or run ID used for production numbers (if applicable)
- **Last verified:** date when claims were last checked against runtime data

This metadata supports the `--update` mode (enables diff detection) and tells readers how current the document is.

### Phase 5: Review

After generating the document:
1. Report the document structure (section count, page estimate, glossary entries, images)
2. **Glossary hyperlink coverage check:** Verify that every glossary term has at least one body-text hyperlink pointing to it. Report any gaps (terms defined in the glossary but never hyperlinked from the body text). These gaps mean the reader has no navigation path to that definition.
3. Ask if the user wants to review before finalizing
4. If `--generate-images` was used, note which images were generated

<!-- ═══════════════════════════════════════════════════════════════════
  WRITING GUIDELINES

  These are the rules that make the document work for the target reader.
  Every decision here was validated by having a review agent read the
  output from the ME persona's perspective.
  ═══════════════════════════════════════════════════════════════════ -->

## Writing Guidelines

### Voice and Tone
- Match the project's existing documentation tone if it has any
- Default to direct, conversational, confident — not academic or hedging
- Use "the system" not "our system" or "we"

### Depth Calibration
<!-- The "paint sample" test: could the ME follow the argument after reading your explanation? -->
- **Right depth:** The ME can follow WHY each technical choice was made and WHAT it accomplishes
- **Too shallow:** Useless ("vector search is a type of search")
- **Too deep:** CS-explaining-CS ("high-dimensional dense representations via transformer neural networks")
- The test: could the ME explain this system to a colleague after reading?

### Accessibility Rules (baked in from the start)
<!-- These are non-negotiable. Every one was learned from review feedback. -->
1. **Every technical term gets an inline definition at first use AND a hyperlink to the glossary** — the inline definition is the primary explanation, the glossary hyperlink is the navigation path for readers who need to revisit the definition later
2. **Replace developer jargon** — code class names become plain language
3. **Remove mathematical formulas** — replace with plain descriptions of what they accomplish
4. **Physical-world analogies** — paint samples for embeddings, ingredient lists for TF-IDF, book indexes for inverted indexes, quality inspection for cross-encoders
5. **Consequence-based reasoning** — "if you skip this, here's what breaks" earns trust with engineers
6. **Each document is self-contained** — never assume the reader has read another document

### Available vs Active Features
<!-- Features described as active must match production config. Misleading feature descriptions erode trust. -->
- **Check the actual production config** (YAML, JSON, .env) to determine which features are enabled vs disabled
- **Describe the active production configuration as the primary path** — this is what the system actually does today
- **Document disabled-but-available features in a clearly labeled "Available Extensions" section**, separate from the standard processing flow. Do not weave disabled features into stage descriptions as though they are part of normal operation.
- The test: if someone reads the stage walkthrough and cross-checks against the running config, do they match?

### What NOT to include
- Code snippets (unless they're configuration examples essential for operators)
- API documentation (that belongs in separate docs)
- Installation/setup instructions (that's README territory)
- Changelog/version history

<!-- ═══════════════════════════════════════════════════════════════════
  LESSONS LEARNED

  These patterns emerged from testing on 4 real projects and a thorough
  review by an agent reading from the ME persona. Each lesson represents
  a mistake we made and corrected. They prevent repeat errors.
  ═══════════════════════════════════════════════════════════════════ -->

## Lessons Learned

1. **The "Why Not Just..." section is the single strongest trust-builder.** Invest time here. Use data, not assertions.

2. **Worked examples make or break the document.** Choose examples that exercise the system's most interesting capabilities. Trace them ALL the way through — don't stop halfway.

3. **Tables are the visual language of the target reader.** Use 3-column comparison tables, scoring tables with concrete numbers, and threshold tables with rationale columns.

4. **Sidebars determine first impressions.** If the reader can't follow the executive summary because they don't know what an LLM or embedding is, they'll disengage. Gate with sidebars.

5. **Developer sections need explicit labels.** Port numbers, concurrency tuning, caching internals — label these "Technical Reference" so the target reader knows to skip.

6. **Dashboard/UI descriptions need mockup images.** Text descriptions of interactive tools are insufficient. Even a conceptual mockup helps more than no visual.

7. **The glossary is the safety net, not the primary mechanism.** Inline annotations at first use are the primary mechanism. The glossary catches terms the reader needs to revisit.

8. **Production numbers earn credibility.** "137,000 atoms" and "sub-second retrieval" are more convincing than "a lot of knowledge" and "fast responses."

9. **Scope the document to the project's complexity.** A 200-line bookmark validator doesn't need 25 pages. A 16-stage ML pipeline does. Let the project dictate depth.

10. **Glossary terms must be navigable via hyperlinks.** The glossary is only useful if readers can get to it from the body text. Every glossary term's first body-text occurrence should be an internal hyperlink to the glossary entry. This replaces the "see glossary" parenthetical pattern — hyperlinks are cleaner and less verbose. The doc-builder tool should generate bookmarks on glossary entries and hyperlinks on first occurrences automatically.

11. **TOC is mandatory for documents over 5 pages.** Every document with more than ~5 pages of content needs a Table of Contents. Include H2 and H3 scope (add H4 if the document uses it for meaningful content). The doc-builder should generate a TOC field automatically.

12. **Never embed images inside heading paragraphs.** When docx-js or the doc-builder places an anchored image, it must be in its own paragraph — not sharing a `<w:p>` with a heading. Images in heading paragraphs break outline view, corrupt TOC entries, and cause the heading text to render as part of the image float. Always create a separate body paragraph for the image, placed before or after the heading.

13. **Each numbered list needs an independent numbering ID.** In OOXML, paragraphs sharing the same numId are treated as a single continuous list. If the document has 3 separate numbered lists (e.g., classification steps, workflow steps, scoring criteria), each needs its own numId with a startOverride. Without this, the second list continues from the first (numbering as 5, 6, 7 instead of 1, 2, 3). The doc-builder should assign unique numbering references per list group.

14. **Features described as active must be verified against config.** Documents that describe disabled features as part of the standard processing flow mislead readers and erode trust when cross-checked against the running system. Always read the production config to determine what is actually enabled before writing stage descriptions.

15. **Production numbers fabricated from code analysis are the #1 source of document inaccuracy.** Code tells you what the system *can* do; output artifacts tell you what it *did* do. Always source counts, timing, accuracy metrics, and threshold values from actual pipeline output, logs, or config files — never estimate them by reading the code.
