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
- `--style PATH` -- Path to a markdown style guide for Word formatting (default: `C:\Users\Troy Davis\dev\info\CFA_Word_Style_Guide.md`)
- `--style-json PATH` -- Path to image style JSON for Nano Banana Pro (default: `C:\Users\Troy Davis\dev\info\clean-style-sanitized.json`)
- `--generate-images` -- Generate diagrams via Google Gemini and insert them (default: OFF — costs money)
- `--output PATH` -- Output file path (default: `{project-dir}/docs/{project-name}-overview.docx`, or `~/Downloads/{repo-name}-overview.docx` for GitHub URLs)

Parse from the user's message. If neither a path nor URL is provided, ask.

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

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 2: DOCUMENT PLANNING

  IMPORTANT: Read the structure template BEFORE planning.
  Not every project needs every section. A 200-line CLI tool gets 5 pages.
  A 16-stage ML pipeline gets 25. Let the project dictate depth.

  Present the plan to the user before writing — this is a checkpoint.
  ═══════════════════════════════════════════════════════════════════ -->

### Phase 2: Document Planning

**IMPORTANT:** Read the structure template at `C:\Users\Troy Davis\dev\info\technical-document-structure-template.md` before planning. It contains a complexity table that maps project size to expected document depth. Not every section applies to every project.

1. **Select Key Concept Sidebars (2-3):** Choose the foundational concepts THIS project relies on most. These will be the first things the reader sees.

2. **Plan the "Why This Approach" section (if warranted):** Identify 2-4 reasonable objections a skeptic would raise. What simpler approaches would people suggest? Why do they fail? Skip for simple projects where the approach is obvious.

3. **Design the worked example:** Choose a concrete, realistic input that will be traced through every stage. It should exercise the system's most important capabilities.

4. **Map the stage/component walkthrough:** List every processing stage or major component with:
   - What it transforms (input → output)
   - Why it matters (consequence of skipping)
   - How the worked example changes at this stage

5. **Plan images (3-5):** Identify where diagrams would most help:
   - System architecture / data flow (almost always needed)
   - Conceptual visualization of the novel/hardest technique
   - Product/output visualization (dashboards, reports, etc.)
   - Worked example transformation diagram

6. **Build the glossary list:** Every CS/ML term that will appear in the document, with draft definitions at the right depth.

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
- Key Concept Sidebars (2-3) at the top
- What goes in → what comes out (one sentence)
- Problem context (why the status quo fails)
- What the system does (high-level, naming major phases)
- Production numbers table (if available)
- Validation summary

**Why This Approach (if warranted):**
- 2-4 subsections, each a skeptic's question
- 3-column comparison tables where applicable
- Concrete data and failure modes, not abstract arguments

**Worked Example:**
- Show the actual input (raw data, article text, etc.)
- Explain why this example demonstrates the system's capabilities

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

**What's Next / Roadmap** (if applicable):
- Planned improvements and known gaps

**Technical Glossary:**
- Dependency-ordered, not alphabetical
- Every term annotated inline at first use in the body

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

The CLI tool is at `C:\Users\Troy Davis\dev\tools\doc-builder` and handles:
- Word document creation with proper CFA styling
- Sidebar callout box formatting (red left border, light grey background)
- Glossary appendix formatting (dependency-ordered, bold red terms)
- Tables with navy headers and alternating row stripes
- Image placeholders (teal left border) or generated images (square text wrap)
- Developer section labeling (italic "Technical Reference" labels)
- Footnote creation

### Phase 5: Review

After generating the document:
1. Report the document structure (section count, page estimate, glossary entries, images)
2. Ask if the user wants to review before finalizing
3. If `--generate-images` was used, note which images were generated

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
1. **Every technical term gets an inline definition at first use** — not just in the glossary
2. **Replace developer jargon** — code class names become plain language
3. **Remove mathematical formulas** — replace with plain descriptions of what they accomplish
4. **Physical-world analogies** — paint samples for embeddings, ingredient lists for TF-IDF, book indexes for inverted indexes, quality inspection for cross-encoders
5. **Consequence-based reasoning** — "if you skip this, here's what breaks" earns trust with engineers
6. **Each document is self-contained** — never assume the reader has read another document

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
