---
name: accessibility-annotator
description: Analyze technical documents for CS/ML concepts a smart non-CS reader wouldn't understand, recommend explanation mechanisms (glossary, inline, footnote, sidebar, appendix), present analysis for approval, then implement annotations in the Word document using the project directory for contextual accuracy. Use when making technical documents accessible to non-CS audiences.
effort: high
---

<!-- ═══════════════════════════════════════════════════════════════════
  ACCESSIBILITY ANNOTATOR SKILL
  ═══════════════════════════════════════════════════════════════════

  PURPOSE:
  Takes an EXISTING Word document about a technical project and adds
  explanatory annotations so a brilliant non-CS reader can understand it.
  Unlike explain-project (which generates from scratch), this skill
  works with documents that already exist.

  WORKFLOW:
  Phase 1: Analysis — read the doc, identify opaque concepts, recommend
           mechanisms (sidebar, glossary, inline, footnote), present
           analysis table to user for approval
  Phase 2: Implementation — after approval, modify the Word document
           to add all annotations

  TARGET READER:
  A top-quintile intelligence mechanical engineer who has never taken
  a CS class. Sharp, process-oriented, comfortable with measurements
  and thresholds. Understands quality gates and structured problem-solving.

  COMPANION TOOLS:
  Paths below are defaults on the author's machine. Override via --style-json flag or environment variables.
  - CFA Style Guide: C:\Users\Troy Davis\dev\info\CFA_Word_Style_Guide.md
  - Image style: C:\Users\Troy Davis\dev\info\clean-style-sanitized.json
  - Image learnings: C:\Users\Troy Davis\dev\info\gemini-image-generation-learnings.md
  - docx skill: document-skills:docx (for Word document manipulation)

  HISTORY:
  Built 2026-03-27. Tested on:
  - cfa/pipeline/docs/knowledge-extraction-pipeline-overview.docx (42 annotations, 4 images)
  - cfa/kb-analysis/docs/knowledge-analysis-tool-overview.docx (35 annotations, 5 images)
  Reviewed by ME-persona agent. All 12 identified issues fixed.
  10 lessons learned baked into the skill.
  ═══════════════════════════════════════════════════════════════════ -->

# Accessibility Annotator

Make technical documents fully understandable by a brilliant reader who lacks computer science training.

**Target reader:** A top-quintile intelligence mechanical engineer. Sharp, process-oriented, comfortable with measurements and thresholds, experienced with quality systems and structured problem-solving. Has never taken a CS class.

## Inputs

Two required arguments (positional or prompted):
1. **Word document path** -- the .docx file to annotate
2. **Project directory path** -- the codebase the document describes (used for accurate, contextual explanations)

Optional flags:
- `--generate-images` -- Generate diagrams via Google Gemini and insert them directly into the document (default: OFF — costs money). When off, insert teal-bordered placeholder boxes with full generation prompts instead.
- `--style-json PATH` -- Path to the image style JSON for Nano Banana Pro prompt construction (default: `$IMAGE_STYLE_JSON` env var if set, otherwise provide via `--style-json` flag. Author's default: `C:\Users\Troy Davis\dev\info\clean-style-sanitized.json`)

Parse from the user's message. If missing, ask for the two required arguments.

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 1: ANALYSIS

  This phase reads the document, identifies every concept the target
  reader wouldn't understand, and recommends how to explain each one.
  The output is a structured analysis table presented to the user for
  review and approval before any changes are made.

  KEY PRINCIPLES:
  - Check for self-explanation: many good docs already explain things
  - Flag concepts, not just terms: "cosine similarity" is a term;
    "measuring how similar two texts are" is the concept
  - Map dependencies: can't explain cross-encoders without embeddings
  - Assess density: high-density sections need glossary, not inline
  ═══════════════════════════════════════════════════════════════════ -->

## Phase 1: Analysis

### Step 1 -- Read the document

Extract text via pandoc:
```bash
pandoc "document.docx" -t markdown
```
Read the full output carefully. Note the document's voice, tone, and how it already explains concepts.

### Step 2 -- Survey the project

Read the project directory structure, README, CLAUDE.md, and 2-3 key source files. Build enough understanding to write accurate explanations later. Don't go deep yet -- that happens in Phase 2.

### Step 3 -- Identify opaque concepts

<!-- ─── CONCEPT FILTER ───
  This filter is calibrated for the specific target reader.
  An ME understands: processes, quality systems, measurements, hardware basics.
  An ME does NOT understand: ML/NLP, CS algorithms, software architecture patterns,
  database internals, DevOps, or named tools with non-obvious purpose.

  The most common mistake is flagging things the document already explains well.
  Always check surrounding context before flagging.
─── -->

Walk the document paragraph by paragraph. For each technical term or concept, apply the filter below.

**The ME WOULD understand (do not flag):**
- Process flows, staged pipelines, architecture as "how parts connect"
- Quality gates, thresholds, measurements, calibration, scoring
- Business logic, operational rationale, cost/benefit arguments
- Tables, metrics, percentages, scoring frameworks
- Procedures and step-by-step instructions
- "Database" as "a place that stores and retrieves information"
- Files, records, fields, filtering, sorting
- Statistical concepts: mean, standard deviation, precision, recall, accuracy, confidence, distributions, correlation
- Hardware: GPU, servers, CPU, memory, network, storage
- Acronyms that are expanded and self-explanatory in context

**The ME would NOT understand (flag these):**
- ML/NLP concepts: embeddings, vector similarity, transformers, tokenization, NER, NLI, cross-encoders, bi-encoders, attention, fine-tuning, inference temperature, context window, token budget, model parameters
- CS data structures and algorithms: inverted indexes, graph traversal, hash maps, B-trees, approximate nearest-neighbor, clustering algorithms (HDBSCAN, DBSCAN)
- Software architecture: REST API, microservices, SSE streaming, CORS, middleware, async processing, event-driven
- Database internals: vector databases, graph databases, Cypher queries, collections, upsert, indexing strategies (IVF, HNSW)
- Data formats beyond basic: JSON/JSONL structure, regex, serialization
- DevOps: Docker, CI/CD, containerization
- Named tools/frameworks with non-obvious purpose: ChromaDB, Neo4j, FAISS, FastAPI, GLiNER, vLLM, pandas, NumPy
- Techniques: TF-IDF, BM25, cosine similarity, Reciprocal Rank Fusion, PCA, anisotropy correction, Platt scaling, embedding dimensions

**Critical -- check for self-explanation:** If the document already explains a concept well enough for the target reader, do NOT flag it. Many good technical documents include "In plain English" sections or parenthetical clarifications. Only flag concepts that remain opaque after reading surrounding context.

**Critical -- flag the concept, not just the term:** "Cosine similarity" is a term. The concept is "measuring how similar two things are by comparing their numeric representations." Flag the concept only if the document doesn't convey this.

### Step 4 -- Map dependencies

<!-- ─── DEPENDENCY CHAINS ───
  Some concepts require understanding other concepts first.
  The glossary must be ordered by dependency (foundational first).
  Sidebars should be placed before the sections that use dependent concepts.
─── -->

Some concepts require others. Build a dependency list:
- "Cross-encoder reranking" needs "embeddings" explained first
- "Cosine similarity" needs "vector representation" explained first
- "Knowledge graph traversal" needs "graph database" explained first
- "BM25" needs "inverted index" or at minimum "keyword matching" explained first

Record dependencies by item number so the analysis table shows the chain.

### Step 5 -- Assess section density

<!-- ─── DENSITY DETERMINES MECHANISM ───
  This is the key insight: dense sections CANNOT use inline annotations
  without destroying readability. Density overrides all other heuristics.
  4+ flagged concepts per paragraph = escalate everything to glossary.
─── -->

For each document section, count flagged concepts per paragraph:
- **Low** (0-1 per paragraph): inline treatment works
- **Medium** (2-3 per paragraph): mix of inline and footnotes
- **High** (4+ per paragraph): glossary/appendix required -- inline would destroy readability

### Step 6 -- Select explanation mechanism

For each flagged concept, select ONE mechanism using these heuristics:

| Mechanism | When to use | Max per document |
|-----------|-------------|-----------------|
| **Inline parenthetical** | Low-density section. 5-12 words suffice. Term appears 1-2 times. | No hard limit, but density rules override |
| **Footnote** | Needs 2-3 sentences. Would break flow if inline. Medium-density section. | ~15-20 |
| **Sidebar / callout box** | Foundational concept that many other explanations depend on. A primer the reader needs before continuing. | 2-4 max |
| **Glossary appendix** | Default for high-density sections. Standard vocabulary needing a 1-2 sentence definition. Terms appearing throughout. | No limit -- this is the workhorse |
| **Appendix explainer section** | A cluster of related concepts that need a unified narrative explanation. Individual glossary entries wouldn't capture how they work together. | 1-3 max |
| **Web link** | An authoritative external resource explains it better than a brief annotation. Concept is well-established and stable. **Minimize.** | 3-5 max, and only when genuinely better than writing it ourselves |

**Density override:** If a section has 4+ flagged concepts per paragraph, do NOT use inline parentheticals in that section. Escalate all items to glossary entries, with footnotes or sidebars for foundational concepts.

**Dependency rule:** If Concept B depends on Concept A, and Concept A is assigned to the glossary, Concept A must appear before Concept B in the glossary. If Concept A gets a sidebar, place it before the first section that uses Concept B.

### Step 7 -- Present the analysis

<!-- ─── ANALYSIS TABLE FORMAT ───
  This table is the user's review checkpoint. They can approve, adjust,
  or reject items before any changes are made to the document.
  Order by appearance in the document, not by mechanism type.
─── -->

Output a **markdown table** with these columns:

| # | Concept/Term | Location | Why opaque | Depends on | Mechanism | Draft explanation |
|---|-------------|----------|------------|------------|-----------|-------------------|

- **#**: Sequential number
- **Concept/Term**: The flagged term or concept
- **Location**: Section name and approximate position (e.g., "Executive Summary, para 3")
- **Why opaque**: One sentence on why the ME wouldn't understand this
- **Depends on**: References to other items by # (e.g., "#3, #7") or "None"
- **Mechanism**: One of: inline, footnote, sidebar, glossary, appendix-section, web-link
- **Draft explanation**: The proposed explanation text at target depth

Order rows by appearance in the document.

After the table, include:

**Density summary:** List each document section with its density rating (low/medium/high).

**Dependency map:** Show chains (e.g., "#3 vector representation -> #7 cosine similarity -> #12 cross-encoder reranking").

**Mechanism distribution:** Counts per mechanism type plus a sentence on whether the distribution feels right.

**Appendix sections recommended:** If any, describe the unified explainer topics.

Then ask:
> Review the analysis above. You can approve as-is, adjust items (change mechanisms, edit explanations, add/remove items), or ask questions. When ready, say **implement** and I'll modify the document.

<!-- ═══════════════════════════════════════════════════════════════════
  PHASE 2: IMPLEMENTATION

  After user approval, modify the actual Word document.
  Use the docx skill (document-skills:docx) for the XML manipulation.

  CRITICAL RULES:
  1. Annotate at FIRST USE — the glossary is 15+ pages away
  2. Replace jargon, don't just annotate it
  3. Remove math formulas, replace with plain language
  4. Label developer sections explicitly
  5. Each document must be self-contained (own sidebars)
  6. Tables need fixed layout (w:tblLayout type="fixed") for 4+ columns
  7. Images use wp:anchor with wrapSquare, NOT wp:inline
  ═══════════════════════════════════════════════════════════════════ -->

## Phase 2: Implementation

After user approves or says "implement":

### Step 1 -- Deep-read the project

For each concept that needs explanation, read the relevant source code, configs, or docs in the project directory. Every explanation must be accurate to what the system actually does -- not a generic textbook definition.

### Step 2 -- Write final explanations

For each item:
- **Match the document's existing voice and tone.** If the document is direct and conversational, annotations should be too. If it's formal, match that.
- **Target depth:** "A standard way software systems talk to each other over the internet" -- enough to follow the argument, not enough to implement the concept.
- **Use analogies from the ME's world when they fit naturally:** manufacturing processes, measurement instruments, inspection systems, assembly lines, material testing, quality control. Don't force analogies -- only use them when they genuinely clarify.
- **Glossary ordering:** By dependency (foundational first), NOT alphabetical. Group related concepts when it aids comprehension.

### Step 3 -- Modify the Word document

Use the docx skill workflow. Invoke the `document-skills:docx` skill for the actual document modification.

**What to add:**
1. **Inline parentheticals** -- insert directly after the term in the text. **CRITICAL: annotate at FIRST USE, not just in the glossary.** A reader encountering "cosine similarity" on page 4 cannot be expected to know it's defined in a glossary on page 22. Add a brief parenthetical like "(a 0-to-1 measure of meaning similarity -- see glossary)" at the first occurrence in the body text. Every glossary term that appears in the body must have at minimum a brief inline definition or "(see glossary)" pointer at its first use.
2. **Footnotes** -- use Word's native footnote fields (FootnoteReferenceRun)
3. **Sidebars** -- styled bordered paragraphs or callout boxes with a distinct background. Use CFA Red (#DD0031) left border, #F5F5F5 background.
4. **Glossary appendix** -- new section at end titled "Technical Glossary" with dependency-ordered entries
5. **Appendix explainer sections** -- new sections at end, before the glossary, with narrative explanations
6. **Web links** -- hyperlinks with descriptive link text
7. **Developer section labels** -- insert italic "Technical Reference" labels before sections that contain implementation details aimed at developers rather than the target reader.

**Clean up developer jargon:** Replace code-level terms (class names like `AsyncLLMProcessor`, `GradientBoostingClassifier`, `FormalRule`) with plain-language equivalents. Replace technical shorthand ("SQLite-based LLM cache stores responses keyed on the prompt hash") with accessible language ("a local database caches previous results so identical requests skip the LLM entirely").

**Remove mathematical formulas:** Replace formulas like `P(correct) = sigmoid(a * raw_confidence + b)` with plain-language descriptions of what the formula accomplishes.

**Preserve everything:** All existing formatting, styles, headers, footers, images, tables. Additions must feel native to the document.

**Output file:** Save as `{original-name}-annotated.docx` alongside the original. Never overwrite the original.

### Step 4 -- Images (3-5 per document)

<!-- ─── IMAGE GENERATION ───
  Images default to OFF because they cost money (Gemini API).
  When off, insert teal-bordered placeholder boxes with full prompts.
  When on, use the patterns from gemini-image-generation-learnings.md.

  ALWAYS use wp:anchor with wrapSquare, NOT wp:inline.
  This was a bug we caught and fixed during development.
─── -->

Identify 3-5 locations where a generated diagram or illustration would most help the non-CS reader. Prioritize:
- System architecture / data flow diagrams (especially replacing existing ASCII-art or text-based diagrams)
- Conceptual visualizations of foundational techniques (how vector search works, how a knowledge graph looks)
- Process flow diagrams showing how data moves through stages
- Dashboard/UI mockups when the document describes interactive tools

For each image location, write a detailed content-specific description and a full generation prompt incorporating the style JSON from the `--style-json` flag value (or `$IMAGE_STYLE_JSON` env var).

**If `--generate-images` is ON:**
1. Load the Google API key from Bitwarden: `bws secret get 74f9abaf-d730-4c4e-b689-b3df01843d65`
2. Use `google-genai` SDK with model `gemini-3-pro-image-preview` (default as of 2026-03-31)
3. Generate each image with `response_modalities=["IMAGE"]`, aspect ratio 16:9, 300s timeout
4. Save to `word/media/` in the unpacked document
5. Add relationship entry to `word/_rels/document.xml.rels`
6. Add content type for PNG to `[Content_Types].xml` if not present
7. Insert image XML using `wp:anchor` with `<wp:wrapSquare wrapText="bothSides"/>` (NOT `wp:inline`)
8. Rate limit: 2-second delay between API calls; 3 retries with 8-second backoff
9. For image generation patterns, see the learnings file at `$GEMINI_IMAGE_LEARNINGS` env var or the path provided during setup

**If `--generate-images` is OFF (default):**
1. Insert teal-bordered (`#3EB1C8`) placeholder callout boxes at each image location
2. Each placeholder contains the full generation prompt (copy-paste ready for Nano Banana Pro)
3. Label: "Image Placeholder: [Title]" in teal bold, 9pt
4. Dimensions: "Landscape 16:9 -- 3200 x 1800px" in grey, 8pt
5. Content description in grey, 8pt; full prompt in grey, 7pt

If replacing an existing text-based diagram (ASCII art, blockquote flowcharts), remove the original.

### Step 5 -- Report

After modification, report:
- Count of each mechanism type added
- Count of images generated or placeholders inserted, with titles
- Count of inline first-use annotations added
- Count of developer section labels added
- Count of jargon replacements made
- List of appendix sections added
- Any concepts where the project directory didn't have enough context (and what you did instead)

<!-- ═══════════════════════════════════════════════════════════════════
  DEPTH CALIBRATION

  This section provides the "feel test" for whether an explanation
  is at the right depth. Read all three examples and internalize the
  difference before writing any explanations.
  ═══════════════════════════════════════════════════════════════════ -->

## Depth Calibration

**Too shallow:** "Vector search (a type of search)" -- useless, tells the reader nothing.

**Right depth:** "Vector search finds information by meaning rather than keywords. The system converts each piece of text into a numeric fingerprint that captures what it means, then finds other texts with the most similar fingerprints -- like identifying matching paint formulas by comparing their chemical compositions rather than their brand names."

**Too deep:** "Vector search works by encoding text into high-dimensional dense representations using transformer-based neural networks, then computing cosine similarity in the embedding space..." -- this IS the CS training the reader doesn't have.

The test: after reading your explanation, could the ME follow the document's argument about WHY this technique is used and WHAT it accomplishes? They don't need to know HOW to build it.

## What NOT to annotate

- Concepts the document already explains adequately for the target reader
- Business and operational concepts (even if they sound technical)
- Proper nouns that are just names -- only annotate their function, and only if unclear from context
- Statistical concepts an ME would know
- Acronyms that are expanded and self-explanatory
- Concepts where the document's own "why it matters" section makes the concept clear enough

<!-- ═══════════════════════════════════════════════════════════════════
  LESSONS LEARNED

  Every lesson below was discovered through real testing and review.
  They represent mistakes we made and corrected. Violating them will
  produce the same problems we already solved.
  ═══════════════════════════════════════════════════════════════════ -->

## Lessons Learned

1. **Always annotate at first use, not just in the glossary.** The glossary may be 20+ pages away. Every glossary term needs at minimum a brief parenthetical or "(see glossary)" at its first appearance in body text.

2. **Replace developer jargon, don't just annotate it.** Code-level class names (`AsyncLLMProcessor`, `GradientBoostingClassifier`) should be rewritten as plain language, not parenthetically defined. The reader gains nothing from knowing the class name.

3. **Remove mathematical formulas.** Replace with plain-language descriptions of what the formula accomplishes. "P(correct) = sigmoid(a * raw_confidence + b)" becomes "the system recalibrates raw confidence scores against actual outcomes."

4. **Label developer sections explicitly.** Sections containing port numbers, concurrency tuning, caching internals, and configuration parameters should be labeled "Technical Reference" in italic text so the target reader knows they can skip without losing the conceptual thread.

5. **Each document must be self-contained.** If documents share concepts (embeddings, LLM, etc.), each document needs its own sidebar explanations. Don't assume the reader has seen another document.

6. **Sidebar selection matters per document.** Choose sidebars for the 2-3 foundational concepts that THIS document relies on most heavily. A document focused on duplicate detection needs TF-IDF and embedding sidebars. A document focused on knowledge extraction needs LLM and embedding sidebars.

7. **Tables with many columns need fixed layout in Word XML** to prevent column truncation. Add `<w:tblLayout w:type="fixed"/>` to `<w:tblPr>` for any table with 4+ columns.

8. **Physical-world analogies work best.** Paint samples for embeddings, ingredient lists for TF-IDF, book indexes for inverted indexes, quality inspection stages for cross-encoder reranking, filing systems for FAISS. The ME thinks in physical processes.

9. **Dashboard/UI descriptions need mockup images.** When a document spends multiple pages describing an interactive dashboard, include at least 1-2 mockup images so the reader can visualize what's being described.

10. **The "Why it matters" / "Why Not Just..." pattern is the strongest rhetorical device for this audience.** These sections earn trust by explaining trade-offs through consequences. Support and extend them, don't compete with them.
