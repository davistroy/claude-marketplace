---
name: evaluate-pipeline-output
description: Thoroughly evaluate contact-center-lab pipeline output quality against input, checking sanitization correctness, atom/entity/triple quality, graph structure, and procedure integrity across all stages
allowed-tools: Read, Glob, Grep, Bash
---

# Pipeline Output Evaluator

Perform a comprehensive semantic quality evaluation of a contact-center-lab pipeline run. This skill reads pipeline source code to discover schemas and configuration, then reads every key output file, compares content against expectations derived from both the code and the input, and produces a structured report with severity-rated findings.

**This skill is read-only. It never modifies files, commits, or pushes.**

## Proactive Triggers

Suggest this skill when:
1. User completes a pipeline run and wants to evaluate quality
2. User asks "did that run produce good output?" or "evaluate the results"
3. Before deciding to run the full 10K corpus
4. After implementing any pipeline code change to verify quality is maintained

## Input

**Arguments:** `$ARGUMENTS`

Required:
- `<output-dir>` — path to the pipeline output directory (e.g., `./output/single-2026-03-05-1803`)

Optional:
- `--input <path>` — path to input fixture/data directory, used to read raw source articles for comparison
- `--baseline <previous-output-dir>` — path to a prior run's output directory for regression comparison
- `--mode test|validation|production` — adjusts severity thresholds (default: `validation`)

**Usage:**
```text
/evaluate-pipeline-output ./output/single-2026-03-05-1803
/evaluate-pipeline-output ./output/full-run-2026-03-06 --baseline ./output/full-run-2026-03-04
/evaluate-pipeline-output ./output/test-5 --input ./pipeline/tests/fixtures/five --mode test
```

If the output directory is not provided, ask the user which run to evaluate.

---

## Core Principle: Derive, Don't Hardcode

**This skill must never be a source of truth for anything the pipeline already defines.** Field names, thresholds, file names, expected ranges, and schemas all change as the pipeline evolves. The skill discovers these at runtime from two sources:

1. **Pipeline source code** (schemas, configuration, stage contracts)
2. **Output data** (actual file contents, record structures, `_meta` blocks)

Every evaluation phase starts with discovery. Python snippets in this skill express **intent** ("print all triples in subject → predicate → object form"), not **field names** ("access `t['subject_label']`"). When this skill says "the field for X," it means "find the field that represents X by inspecting the data."

---

## Finding Analysis Protocol

**Every finding MUST receive a full deep-dive analysis.** Do not shortcut to a label and severity. For each finding, work through this structure before moving to the next:

1. **Symptom** — What did you observe in the output? Quote specific data (text, counts, field values). Be precise enough that someone unfamiliar with the run could see it.

2. **Issue** — What is wrong? Distinguish between the observed symptom and the underlying problem. "Entity count is high" is a symptom. "Entity resolution is not merging variants because the similarity threshold is too high for the current embedding model" is the issue.

3. **Root Cause** — Where in the pipeline does this originate? Trace backward through the stage chain. A problem visible in Stage 9 output may originate in Stage B. Name the specific stage, and if possible the specific function or logic path. Read the relevant pipeline source code to confirm — do not guess.

4. **Cascade Analysis** — What downstream effects does this root cause produce? Trace forward through the stage chain. A Stage B entity type error cascades to Stage C (wrong Faker generator), Stage 5 (wrong entity type in resolution), Stage 6 (garbled triple subjects), and Stage 9 (nonsensical graph labels). Map the full chain.

5. **Architectural Fix** — What is the right fix? Not a patch — a fix that solves the problem permanently. Consider:
   - Does the fix address the root cause, not just the symptom?
   - Will the fix survive future pipeline changes (new stages, new models, new schemas)?
   - Does the fix minimize technical debt, or does it add a special case that someone will need to maintain?
   - Are there simpler alternatives that achieve the same outcome?
   - What are the risks of the fix itself (could it break something else)?

6. **Verification** — How would you confirm the fix worked? What specific output would change, and what would the correct values look like?

**Do not skip this protocol.** A finding without root cause analysis is just noise. A finding without cascade analysis misses the real impact. A finding without an architectural fix creates technical debt.

---

## Evaluation Process

Execute ALL phases in order. Use Bash for JSON parsing with python3 where needed. Keep individual Bash calls focused and fast.

---

### Phase 0: Discovery & Orientation

This phase builds the evaluation context that all subsequent phases depend on. Do not skip any step.

#### 0A: Locate Pipeline Source Code

1. **Find the pipeline root.** The output directory is typically under a project that contains a `pipeline/` directory. Look for `pipeline/config.yaml` relative to the output directory, or in common locations:
   - Same repo as the output directory
   - `C:\Users\Troy Davis\dev\contact-center-lab\pipeline`
   - Ask the user if not found.

2. **Read `pipeline/config.yaml`** in full. Extract and note:
   - LLM backend configuration (which model, concurrency, timeout)
   - Embedding backend configuration (model name, dimension, truncate_dimension)
   - All pipeline thresholds (`semantic_break_threshold`, `typing_min_confidence`, `decomposition_min_length`, `dedup_high_threshold`, `dedup_review_threshold`, `entity_similarity_threshold`, `predicate_similarity_threshold`, etc.)
   - Sanitization config: denylist terms, safelist references, internal URL domains
   - Predicate synonyms and blocklist

3. **Read `pipeline/shared/models.py`**. Identify all dataclass definitions and their field names. These are the canonical schemas for every stage output. Note especially:
   - Triple fields (the field names for subject, predicate, object, condition, negation)
   - NormalizedProcedure fields (the field names for title/name, goal/purpose/expected_outcome, steps)
   - FinalAtom fields (especially `procedure`, `triples`, `entity_refs`)
   - EntityRecord fields
   - PolicyRecord and FormalRule fields

4. **Read `pipeline/runner.py`** to discover:
   - `STAGE_ORDER` — what stages exist and their execution order
   - `STAGE_NAMES` — human-readable stage names
   - `CONCURRENT_GROUPS` — which stages run in parallel
   - Output file naming patterns per stage

#### 0B: Scan Output Directory

1. **List all files** in the output directory (including `final/` subdirectory). Record which stage output files are present. Note any unexpected or missing files.

2. **For each stage output file found**, read the `_meta` record (typically the last line in JSONL files, or a `_meta` key in JSON files). Record:
   - Stage number/letter
   - Timestamp
   - All counts and rates (these are the pipeline's own self-reported metrics)
   - LLM failure counts and rates (for LLM-calling stages)
   - Any error or failure flags (e.g., `hdbscan_failed`)

3. **Read `final/statistics.json`** in full. This is the pipeline's summary dashboard. Record its complete structure — do not assume key names; inspect the actual JSON.

4. **Discover schemas from actual data.** For each key output file, read the first non-`_meta` record and note its field names. This is the ground truth for how to access data in subsequent phases, regardless of what `models.py` says the fields should be called.

#### 0C: Compute Expectations

1. **Identify article count** from statistics.json (look for a key representing document/article count).

2. **Derive expected ranges** using these per-article heuristics for well-formed KB articles. These are evaluation heuristics, not pipeline config — they represent what good output looks like:

| Metric | Expected per Article | Scale Behavior |
|--------|---------------------|----------------|
| Atoms | 15-60 | Linear; short articles produce fewer |
| Entities | 15-50 | Sublinear at scale (resolution merges across articles) |
| Triples | 5-20 | Procedure-heavy articles yield fewer |
| Procedures | 5-20 | ~40-60% of atoms should be procedures for KB articles |
| Policies | 0-3 | Only for articles with explicit policy statements |
| Rules | 0-3 | Only for conditional/IF-THEN content |
| Graph edges | 10-40 | Superlinear at scale (cross-doc connections) |
| Isolated nodes | <50% at 1 article, <20% at 100+ | Improves with scale |

**Adjust for article complexity:** If Stage 1 chunk data is available, compute average article length. Short articles (<500 chars) should use the low end of ranges. Long articles (>3000 chars) should use the high end.

**For multi-article runs:** Multiply per-article expectations by article count, then apply a 20-40% discount for entities (resolution merges variants).

3. **If `--baseline` was provided**, read the baseline run's statistics.json for regression comparison.

---

### Phase 1: Infrastructure Health

**Goal:** Before evaluating content quality, verify the pipeline machinery ran correctly.

1. **Check LLM failure rates.** For every stage that used an LLM (look for `llm_failures` or `llm_failure_rate` in `_meta`):
   - >1% failure rate: WARNING — some content was silently dropped
   - >5% failure rate: CRITICAL — run is unreliable; downstream counts are depressed by an invisible factor
   - Note which backend was used and whether failures suggest timeout, connection, or model issues

2. **Check HDBSCAN success.** For stages that use clustering (entity resolution, deduplication), look for `hdbscan_failed` in `_meta`:
   - If `true`: CRITICAL — entity resolution or deduplication did not run. All downstream entity/dedup metrics are meaningless.
   - Note the `hdbscan_error` message if present.

3. **Check processing time.** If timing data is available in `_meta` (`elapsed_seconds`) or statistics.json:
   - Note total wall time and per-stage time
   - If `--baseline` provided, flag >50% time increases as potential performance regressions

4. **Check Stage 3 passthrough rate.** Look for `passthrough_count` in Stage 3's `_meta`:
   - High passthrough (>60%): Most segments were too short for LLM decomposition — could indicate over-segmentation in Stage 2
   - Cross-reference with Stage 2's segment counts

**Key findings (apply Finding Analysis Protocol to each):** LLM failures >1% (CRITICAL at >5%), HDBSCAN failures (CRITICAL), performance regressions (INFO).

---

### Phase 2: Ingestion Quality (Stage A)

**Goal:** Verify source articles were correctly ingested, filtered, and prepared.

1. **Read Stage A's `_meta`**. Check:
   - `articles_output` vs `total_records_scanned` — what fraction was kept? If <50%, version filtering may be too aggressive.
   - `articles_skipped_empty` — if high, source data may have quality issues.

2. **Sample 2-3 articles from Stage A output.** Verify:
   - `body_text` is non-empty and contains readable content (not raw HTML tags)
   - Title is present and meaningful
   - No duplicate articles with the same KB number (would indicate version filtering failure)

3. **Check for HTML artifacts.** Search Stage A output for residual HTML tags (`<div>`, `<span>`, `<table>`, `&nbsp;`) that should have been stripped.

**Key findings (apply Finding Analysis Protocol to each):** High skip rate (MEDIUM), HTML artifacts in body_text (HIGH), duplicate KB articles (HIGH).

---

### Phase 3: Sanitization Quality (Stages B, C)

**Goal:** Verify PII was removed, synthetic replacements are coherent, and no proprietary identifiers survived.

1. **Read Stage B's `_meta`.** Check:
   - `finding_types` distribution — is any single type dominating? (>50 INTERNAL_TOOL per article suggests over-detection)
   - `spacy_enabled` — if false, PERSON detection relied solely on patterns
   - `fuzzy_consolidated` — how many entities were merged by fuzzy matching

2. **Read the Stage C glossary CSV** (discover filename from directory listing). This maps original → placeholder → synthetic. Check:
   - Are ORG-typed entities getting company-style synthetic names (not person-style names like "Dominguez-Berry")?
   - Are PERSON-typed entities getting person-style names?
   - Type mismatches here indicate Stage B misclassified the entity type, causing Stage C to use the wrong Faker generator.

3. **Read Stage C sanitized output.** Sample 1-3 articles (skip `_meta`). Print the full body text.

4. **Check for PII leakage.** Read the denylist terms from the pipeline config (discovered in Phase 0). Search the Stage C output for those specific terms — do NOT hardcode company names. Also search for patterns suggesting real names survived:
   - Email patterns: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
   - Phone patterns from the pipeline's regex config
   - Internal URL domain patterns from the pipeline's config

5. **Evaluate synthetic replacement coherence.** For each synthetic replacement in the glossary, check:
   - Company names replacing real orgs: plausible? (Faker surname compounds replacing org names = Stage B entity type error)
   - Tool/product names: do they read as plausible tech product names?
   - Partial replacements: same real term appearing both replaced and unreplaced across articles

6. **Check the risk report CSV.** Are any articles flagged HIGH or CRITICAL? If so, read those articles and verify what triggered the flag.

**Key findings (apply Finding Analysis Protocol to each):** PII leakage (CRITICAL), entity type misclassification causing wrong Faker generator (HIGH), partial replacements (MEDIUM), over-redaction of public entities (LOW).

---

### Phase 4: Chunking and Boundary Detection (Stages 1, 2)

**Goal:** Verify articles were chunked and segmented sensibly.

1. **Read Stage 1 output.** Discover the structure from Phase 0. Verify:
   - Chunk count is reasonable relative to article count
   - Body text in chunks is non-empty and retains structure
   - Provenance fields link back to source articles

2. **Read Stage 2 output.** Check:
   - Segment count per article (discover from data; typical range is 10-40 for multi-step KB articles)
   - Single-sentence rate if available in `_meta`
   - Read 3-5 sample segments to verify they are coherent text, not fragments

3. **Cross-stage signal.** Compare segment count with Stage 3 passthrough count (from Phase 1). If most segments bypass LLM decomposition, Stage 2 may be over-segmenting.

**Key findings (apply Finding Analysis Protocol to each):** Unusually high/low segment counts (MEDIUM), empty segments (HIGH), markdown artifacts in segments (MEDIUM).

---

### Phase 5: Atom Quality (Stages 3, 4)

**Goal:** Verify claims are correctly decomposed and typed.

1. **Read Stage 4 atoms output.** Discover the field names for atom type, text, confidence, and parent segment from Phase 0. Print a representative sample (first 50 atoms) showing type, confidence, and text.

2. **Check atom type distribution.** Read the distribution from statistics.json or compute from data. Apply these semantic heuristics:
   - `procedure` atoms should describe *actions* (imperative verbs: tap, click, navigate, disconnect, verify, select)
   - `fact` atoms should describe *states* (is, has, contains, remains, may be)
   - `rule` atoms should describe *conditions* (if X then Y, must, required, only when)
   - `definition` atoms should describe *what something is*
   - `reference` atoms should be support contacts, URLs, ticket references

3. **Check confidence distribution.** Compute what percentage of atoms have:
   - High confidence (>0.8): these are reliable classifications
   - Moderate confidence (0.5-0.8): spot-check a few for accuracy
   - Low confidence (<0.5, near the `typing_min_confidence` from config): these are likely misclassified. Read several and assess.

4. **Flag misclassified atoms.** Read 20-30 atoms across all types. Common errors:
   - Statements with "is/has/contains" typed as `procedure` — should be `fact`
   - Pure navigation paths with no action verb typed as `procedure` — should be `reference` or `fact`
   - IF-THEN statements typed as anything other than `rule`

5. **Check for over-decomposition.** If a single segment produced 4+ atoms, the LLM may be splitting sub-paths into individual atoms. Note how many atoms came from each parent segment.

6. **Verify atom text is sanitized.** Using the denylist terms from pipeline config (Phase 0), search atom texts for any that leaked through.

**Key findings (apply Finding Analysis Protocol to each):** Type misclassification rate >20% (HIGH), over-decomposition pattern (MEDIUM), unsanitized content in atoms (CRITICAL), low confidence clustering (MEDIUM).

---

### Phase 6: Entity Quality (Stage 5)

**Goal:** Verify entities are correctly typed, non-fragmented, and meaningful.

1. **Read `final/entities.json`** (or the entities file discovered in Phase 0). Discover the field names for entity type, canonical label, aliases, and mention count. Print all entities grouped by type.

2. **Check entity type assignments.** Apply these semantic rules:
   - Labels that are clearly organization names should be ORG, not PERSON
   - Software products should be SOFTWARE or PRODUCT, not PERSON
   - UI navigation items should be UI_ELEMENT or CONCEPT, not PERSON
   - Labels containing phone numbers, URLs, or boilerplate text are junk entities
   - Labels that are single common words (the, a, it, this) are junk entities

3. **Check for fragmentation.** Look for entity groups that refer to the same concept:
   - Multiple grammatical forms (possessive, "your X", "the X") that were not merged
   - Same concept appearing under multiple types (CONCEPT and SOFTWARE, ORG and CONCEPT)
   - Calculate effective fragmentation ratio: distinct real-world concepts vs entity records. >2.0 is HIGH.

4. **Check mention count distribution.** Compute singleton rate (entities with mention_count=1):
   - Single article: >60% singletons is expected
   - 10+ articles: >40% singletons indicates fragmentation
   - Use the `entity_similarity_threshold` from config (Phase 0) to assess whether the threshold might need tuning

5. **Check entity type cross-contamination.** For entities with aliases, verify the aliases are semantically consistent with the canonical label and type. Flag any entity where aliases span clearly different concepts.

6. **Flag type errors that propagate downstream.** If an ORG was typed PERSON in Stage B (visible in the glossary), Stage C used a person name generator — meaning person-style company names now appear throughout the graph.

**Key findings (apply Finding Analysis Protocol to each):** PERSON/ORG misclassification (HIGH), fragmentation ratio >2.0 (MEDIUM), junk entities (MEDIUM), entity count anomalies (INFO).

---

### Phase 7: Triple and Predicate Quality (Stage 6)

**Goal:** Verify extracted relationships are semantically correct and predicates are normalized.

1. **Read the triples output file.** Discover field names from Phase 0. There may be both basic triple fields (entity/attribute/value) and enhanced fields (subject_label/predicate_label with URIs). Use whichever is most informative. Print all triples in readable subject → predicate → object form.

2. **Check Stage 6 `_meta`.** Look for:
   - `llm_failures` / `llm_failure_rate` — covered in Phase 1 but note here for context
   - `eligible_atoms` vs `atoms_with_triples` — what percentage of eligible atoms produced triples?
   - `unmapped_predicates` — if present, what percentage of predicates failed to normalize?
   - `self_referential_filtered` — how many self-referencing triples were removed?

3. **Verify semantic correctness of a sample.** For 10-15 triples, check:
   - Does the subject-predicate-object relationship match what the source text says?
   - Is the direction correct? (e.g., "A owned_by B" vs "B owns A")
   - Is the condition accurate?
   - Do subject/object refer to entities that make semantic sense (not garbled synthetic names)?

4. **Check predicate normalization.** Look for predicate URI fields and normalization confidence:
   - Predicates mapped to "unmapped" or with zero normalization confidence are not in the taxonomy
   - >20% unmapped predicates: MEDIUM — taxonomy may need expansion
   - Normalization confidence <0.5 indicates weak mapping that may be wrong
   - Read `final/predicates.json` and check which predicates are most used. Are there custom predicates that should be added to the taxonomy in config?

5. **Check triple coverage.** What percentage of atoms produced triples?
   - Typical range: 15-30% for KB procedure articles
   - Below 10%: LLM could not find relationships (may be acceptable for pure procedural content)
   - Above 50%: likely over-extraction

**Key findings (apply Finding Analysis Protocol to each):** Semantically inverted triples (HIGH), unmapped predicates >20% (MEDIUM), directional errors (HIGH), triple coverage anomalies (INFO).

---

### Phase 8: Procedure Quality (Stage 7)

**Goal:** Verify procedures are structured, sequenced, and contain actionable steps.

1. **Read the procedures output file.** Discover field names from Phase 0 — look for the fields that represent procedure name/title, goal/purpose/expected_outcome, steps, and preconditions. Print a summary of 5-10 procedures showing these fields.

2. **Check step quality.** For each sampled procedure:
   - Does the name/title accurately describe the action?
   - Does the goal/purpose state a meaningful outcome?
   - Are steps specific enough to execute? ("Disconnect VPN" is good; "Perform the action" is bad)
   - Are preconditions meaningful when the procedure clearly has prerequisites?

3. **Check single-step rate** from statistics.json (find the key for single-step rate in the procedures section):
   - Rate >80%: LLM is not aggregating sub-steps — over-decomposition
   - Rate <30%: LLM is over-aggregating unrelated steps
   - Target: 40-65% for KB troubleshooting articles

4. **Check stub procedures** from statistics.json (find the key for stub/empty procedure count):
   - Stubs are procedures where the LLM returned no steps — these are extraction failures
   - >5% stub rate: HIGH

5. **Verify procedure chain structure** from statistics.json:
   - Chain count: for a single article, expect 1-3 chains
   - If max chain length equals total procedure count with only 1 chain, the chaining treated every micro-action as sequential rather than grouping

6. **Check procedure data in final atoms.** For procedure-type atoms in `final/atoms.json`, verify the embedded procedure block has populated steps. Note: there may be legacy/unused fields at the atom root level — empty values there are NOT bugs if the nested procedure block has the data.

**Key findings (apply Finding Analysis Protocol to each):** High single-step rate (MEDIUM), missing or vague steps (MEDIUM), high stub rate (HIGH), chain anomalies (INFO), empty procedure blocks on procedure-type atoms (HIGH).

---

### Phase 9: Deduplication Quality (Stage 8)

**Goal:** Verify dedup correctly identified near-duplicates without false positives.

1. **Read Stage 8 `_meta`.** Check:
   - `input_atom_count` vs `output_atom_count` — how many atoms were removed?
   - `total_duplicates_removed` — does this match the atom count delta?
   - `review_item_count` — how many borderline pairs were flagged?
   - `hdbscan_failed` — if true, dedup didn't actually run (CRITICAL, covered in Phase 1)
   - `entity_aware` — was entity-aware dedup enabled?

2. **Read the review items file.** Discover the field names. For each review item:
   - Read both atom texts
   - Are they genuinely semantically equivalent?
   - Are they from the same article or different articles?
   - What is the similarity score? Compare against the thresholds from config (`dedup_high_threshold`, `dedup_review_threshold`)

3. **Check for false positives.** Review items that are actually *distinct* atoms with similar wording (e.g., same instruction for different channels) should NOT be merged. Flag these.

4. **Check dedup aggressiveness.** Compare `total_duplicates_removed` against total input atoms:
   - Single article: expect 0-5% removal
   - Multi-article: expect 5-15% removal
   - >20% removal at any scale suggests overly aggressive thresholds

**Key findings (apply Finding Analysis Protocol to each):** False positive dedup (HIGH), HDBSCAN failure (CRITICAL), dedup too aggressive or too passive (MEDIUM).

---

### Phase 10: Graph Structure (Stage 9)

**Goal:** Verify the knowledge graph has expected connectivity and correct edge types.

1. **Read `final/graph_edges.json`**. Discover the field names. Compute edge type distribution.

2. **Verify expected edge types are present.** The pipeline should produce structural edges (connecting procedures in flows) and semantic edges (from triples). Common structural edge types include next-step, part-of-flow, derived-from, and governs — discover the actual type labels from the data.

3. **Check DERIVED_FROM completeness.** Every policy and rule should have a DERIVED_FROM edge pointing to its source atom. Compare the count of DERIVED_FROM edges against the total policies + rules from statistics.json. A mismatch indicates a field name bug in the graph generation code.

4. **Check isolated node rate** from statistics.json (find the key in the graph section):
   - Scale-adjusted expectations: <50% at 1 article, <30% at 10 articles, <20% at 100+ articles
   - Above threshold indicates underperforming entity resolution or triple extraction

5. **Verify vector DB atoms have embeddings.** Read the first record of `final/vector_db_atoms.jsonl`. Check:
   - Embedding field exists and is non-empty
   - Embedding dimension matches what the pipeline config specifies (check `embedding.backends.[active_backend].dimension` or `truncate_dimension` from config)
   - Verify a few values are non-zero (all-zero embeddings indicate an embedding failure)

6. **Verify all expected output files exist and are non-empty.** List the files in `final/` and confirm each has >0 bytes.

7. **Read `final/graph_nodes.json`**. Check node type distribution matches entity + procedure + flow counts from statistics.json.

**Key findings (apply Finding Analysis Protocol to each):** Missing DERIVED_FROM edges (HIGH), zero/missing embeddings (CRITICAL), isolated node rate above threshold (MEDIUM), missing output files (CRITICAL).

---

### Phase 11: Cross-Cutting Anomaly Detection

Run these checks across the full output:

1. **Sanitization bleed-through.** Using the denylist terms from pipeline config (Phase 0), search ALL downstream output files for any leaked terms. Do NOT hardcode company names — use the actual denylist.

2. **Empty text fields.** Scan atoms for empty text, entities for empty canonical labels, and procedures for empty name/title. Any empty required field is a parsing or extraction failure.

3. **Statistics consistency.** Verify the counts in statistics.json match actual file contents. For each major count in statistics.json:
   - Read the corresponding output file
   - Count the actual records (excluding `_meta`)
   - Report any mismatches

4. **ID cross-reference validation.** Sample 5 atoms from `final/atoms.json`. For each:
   - Verify its atom_id appears in the vector DB atoms file
   - If it is a procedure-type atom, verify its atom_id appears in the procedures file's source references
   - Verify its entity references (if any) point to valid entities in the entities file
   - Walk the provenance chain: atom → segment → chunk. Verify each link resolves.

5. **Cross-stage causal analysis.** If issues were found in multiple phases, identify causal chains:
   - Stage B entity type errors → Stage C wrong Faker generator → downstream nonsensical labels
   - Stage 2 over-segmentation → Stage 3 high passthrough → shallow atoms → poor triples
   - LLM failures → depressed counts in affected stages → misleading quality metrics
   - HDBSCAN failure → no entity resolution/dedup → inflated entity counts and duplicate atoms
   Report these chains as a single root-cause finding rather than multiple independent findings.

---

### Phase 12: Regression Analysis (if --baseline provided)

**Goal:** Compare this run against a prior run to detect regressions and improvements.

1. **Read baseline statistics.json.** Compare every metric:
   - Atoms per article: delta
   - Entity count and fragmentation: delta
   - Triple count and unmapped rate: delta
   - Procedure single-step rate: delta
   - Graph connectivity (isolated node rate, avg degree): delta
   - Dedup removal rate: delta

2. **Flag significant changes.** Use these thresholds:
   - >20% degradation in any metric: WARNING
   - >50% degradation: CRITICAL regression
   - Improvements should also be noted (positive signal that a code change worked)

3. **Include a regression table in the report.**

---

### Phase 13: Evaluation Report

Produce a structured report in this format:

---

**Pipeline Output Evaluation Report**

**Run:** [output directory name]
**Date:** [from statistics.json timestamp or current date]
**Articles processed:** [N]
**Pipeline config:** [LLM backend + model, embedding backend + model, key thresholds]
**Stages run:** [list stages found in output]
**Mode:** [test/validation/production]

---

**Executive Summary**

[2-4 sentence summary: did the run succeed, what are the top 2-3 issues, is it ready for scale-up. Mention any CRITICAL infrastructure issues (LLM failures, HDBSCAN failures) first.]

---

**Infrastructure Health**

| Check | Status | Detail |
|-------|--------|--------|
| LLM failure rate (Stage 3) | pass/warn/fail | X% (N failures of M calls) |
| LLM failure rate (Stage 6) | pass/warn/fail | X% |
| LLM failure rate (Stage 7) | pass/warn/fail | X% |
| HDBSCAN (Stage 5) | pass/fail | succeeded/failed |
| HDBSCAN (Stage 8) | pass/fail | succeeded/failed |
| Processing time | info | Xs total (Xs stage 3, Xs stage 6, Xs stage 7) |

---

**Counts vs Expectations**

| Metric | Expected | Actual | Per Article | Status |
|--------|----------|--------|-------------|--------|
| Articles ingested | — | N | — | info |
| Atoms (total) | N x range | ... | .../article | pass/warn/fail |
| Entities (total) | N x range (discounted) | ... | .../article | pass/warn/fail |
| Entity fragmentation ratio | <2.0 | ... | — | pass/warn/fail |
| Triples | N x range | ... | .../article | pass/warn/fail |
| Unmapped predicates | <20% | ...% | — | pass/warn/fail |
| Procedure single-step rate | 40-65% | ...% | — | pass/warn/fail |
| Procedure stub rate | <5% | ...% | — | pass/warn/fail |
| DERIVED_FROM completeness | 100% | ...% | — | pass/warn/fail |
| Isolated nodes | scale-adjusted | ...% | — | pass/warn/fail |
| Embedding dimension | [from config] | ... | — | pass/warn/fail |
| Dedup removal rate | 0-15% | ...% | — | pass/warn/fail |

---

**Regression Analysis** (if --baseline provided)

| Metric | Baseline | Current | Delta | Status |
|--------|----------|---------|-------|--------|

---

**Findings**

For each finding, use the full deep-dive format. Group by severity.

CRITICAL (data loss, infrastructure failure, or semantic corruption):

> **[C1] Title**
> - **Symptom:** What was observed, with specific data/quotes
> - **Issue:** What is actually wrong (not just the symptom)
> - **Root Cause:** Which stage/function/logic path, confirmed by reading code
> - **Cascade:** What downstream stages and outputs are affected, and how
> - **Fix:** Architectural fix that addresses root cause permanently, not a patch
> - **Verification:** How to confirm the fix worked

HIGH (semantic errors that produce wrong answers at query time):
> [same format as above for each finding]

MEDIUM (quality issues that degrade usefulness):
> [same format]

LOW (observations worth tracking across runs):
> [same format — cascade and fix may be "none needed" for pure observations]

---

**Causal Chain Summary**

After all individual findings, consolidate any findings that share a root cause into chains:

> **Chain 1:** [Root cause stage + description]
> → [First downstream effect] (finding [X1])
> → [Second downstream effect] (finding [X2])
> → [Final output impact] (finding [X3])
> **Single fix resolves:** [X1], [X2], [X3]

This section ensures the user sees that fixing one root cause eliminates multiple findings, and knows which fix to prioritize.

---

**Scale Readiness Assessment**

[Direct answer: is this output good enough to run the full corpus? What must be fixed first vs what can wait? What will improve naturally at scale (entity resolution, dedup) vs what will get worse (any linear bug gets multiplied)?]

---

**Recommended Next Steps**

Ordered by impact (root causes that resolve the most causal chains first):

1. [Fix from finding [X]: what to change, in which file/function, why this is the architecturally sound approach, and which other findings this resolves]
2. [next fix, same format]
3. ...

**Do not list symptom-level patches here.** Every recommendation must trace back to a root cause identified in the Findings section. If a recommendation would add a special case, workaround, or hardcoded fix, explain why no better alternative exists.

---

## Severity Calibration by Mode

| Mode | CRITICAL threshold | HIGH threshold | What it means |
|------|--------------------|----------------|---------------|
| `test` | Data loss or corruption only | Semantic errors affecting >20% of output | Small run, expect rough edges |
| `validation` (default) | Infrastructure failures OR data corruption | Semantic errors >10% | Pre-scale-up gate |
| `production` | Any infrastructure issue OR data corruption | Any semantic error >5% | Full corpus, zero tolerance |

---

## Evaluator Guidance

These are durable heuristics that help the evaluator avoid false findings:

- **Legacy/unused fields:** Some atom or procedure records may have empty fields at the root level that are populated in a nested block instead. Before flagging empty fields, check whether the data lives in a nested structure (e.g., `atom.procedure.steps` vs `atom.normalized_steps`). Inspect the actual data, don't assume.

- **Public entity redaction:** Well-known public companies (carriers, tech giants) appearing in sanitized output may or may not be correct — it depends on whether the relationship with that company is confidential. Check the safelist from config before flagging.

- **Isolated nodes at small scale:** High isolation rates (>50%) are expected and normal for single-article runs. Only flag isolation as a finding if it exceeds the scale-adjusted threshold from the expectations table.

- **Entity type cascade:** Synthetic company names that look like person names (e.g., "Keith-Francis") are a downstream symptom, not a root cause. The root cause is always in Stage B entity type detection. Report the root cause, not the symptom.

- **Standalone tools:** Tools like `extract_terms.py` or `calibrate_thresholds.py` in the pipeline's `tools/` directory are NOT part of the A-through-9 pipeline. They don't affect output quality directly. Don't flag their output or absence.

- **Passthrough is not failure:** Stage 3 passing short segments through without LLM decomposition is by design (configurable via `decomposition_min_length` and `simple_segment_passthrough` in config). High passthrough is only a concern if it cascades to shallow atoms.

- **Embedding model changes:** The pipeline may change embedding models over time. Always read the configured model and its expected dimension from config rather than assuming a specific value. Similarly, all similarity thresholds are model-dependent — read them from config.
