---
name: evaluate-pipeline-output
description: Thoroughly evaluate contact-center-lab pipeline output quality against input, checking sanitization correctness, atom/entity/triple quality, graph structure, and procedure integrity across all stages
allowed-tools: Read, Glob, Grep, Bash
---

# Pipeline Output Evaluator

Perform a comprehensive semantic quality evaluation of a contact-center-lab pipeline run. This skill reads every key output file, compares content against expectations derived from the input, and produces a structured report with severity-rated findings.

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
- `--articles N` — number of input articles (for scaling expectations). Defaults to reading from statistics.json.
- `--input <path>` — path to input fixture/data directory, used to read raw source articles for comparison

**Usage:**
```text
/evaluate-pipeline-output ./output/single-2026-03-05-1803
/evaluate-pipeline-output ./output/full-run-2026-03-06 --articles 10357
/evaluate-pipeline-output ./output/test-5 --input ./pipeline/tests/fixtures/five
```

If the output directory is not provided, ask the user which run to evaluate.

---

## Evaluation Process

Execute ALL phases. Use Bash for JSON parsing with python3 where needed. Keep individual Bash calls focused and fast.

---

### Phase 0: Orientation

1. **Verify the output directory exists** and contains expected subdirectories (`final/`, intermediate JSONL files).
2. **Read `final/statistics.json`** — this is the primary dashboard. Extract all counts and store them for use throughout the evaluation.
3. **Identify article count** from `statistics.json` (field: `documents`).
4. **Compute per-article expectations** using the scaling table below. These are the benchmarks for all subsequent phases.

**Per-article scaling benchmarks (single well-formed KB article):**

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Atoms | 35-60 | >80 indicates over-decomposition |
| Entities | 25-50 | >80 indicates fragmentation; at scale entities converge |
| Triples | 8-20 | How-to articles yield fewer triples than policy articles |
| Procedures | 8-20 | ~50-60% of atoms should be procedures for KB articles |
| Policies | 0-3 | Only for articles with explicit policy statements |
| Rules | 0-3 | Only for conditional/IF-THEN content |
| Graph edges | 15-40 | Grows nonlinearly with scale (cross-doc connections) |
| Isolated nodes | <50% at 1 article, <20% at 100+ articles | High isolation is expected at tiny scale |

**For multi-article runs:** multiply single-article expectations by article count, then apply a cross-doc discount of 20-40% for entities (resolution merges variants across articles).

---

### Phase 1: Sanitization Quality (Stages A, B, C)

**Goal:** Verify PII was removed, synthetic replacements are coherent, and no proprietary identifiers survived.

1. **Read the Stage C sanitized JSONL** (`stage_C_sanitized.jsonl`). Sample the first 1-3 articles (skip `_meta` records). Print the full `body_text` of each.

2. **Check for PII leakage.** Search for patterns that suggest real names survived:
   ```bash
   grep -i "chick-fil-a\|cfahome\|@cfa\|cfaperform" stage_C_sanitized.jsonl
   grep -E "\b[A-Z][a-z]+\.[A-Z][a-z]+\b" stage_C_sanitized.jsonl
   ```

3. **Evaluate synthetic replacement coherence.** For each synthetic name used, ask: does it still make semantic sense in context?
   - Company names replacing real orgs: plausible? (A Faker surname like "Dominguez-Berry" replacing "Apple" makes the text absurd)
   - Tool/product names: do they read as plausible tech product names?
   - Person names: are they distinguishable from org names?

   **Red flag:** Org replaced with a human surname compound (e.g., "Dominguez-Berry Menu", "Foster-Boyd Support"). This means the entity was mistyped ORG to PERSON in Stage B, causing Faker to use a person name generator instead of a company name generator.

4. **Check for partial replacements.** Are there cases where a term is replaced in some occurrences but not others? (e.g., "Safari" appearing unchanged in one phrase but "Catalyst Hub" elsewhere for the same product).

5. **Check Stage B finding counts** from the pipeline log or redacted JSONL metadata:
   - Is INTERNAL_TOOL count reasonable? (>50 per article suggests over-detection)
   - Are major carrier/vendor names (Verizon, AT&T, Samsung, Apple, T-Mobile) being redacted when they are public entities and should not be?

6. **Check the risk report** (`stage_C_risk_report.csv`). Are any articles flagged HIGH or CRITICAL risk? If so, read those articles and verify what triggered the flag.

**Key findings to report:** PII leakage (CRITICAL), entity type misclassification causing wrong Faker generator (HIGH), partial replacements (MEDIUM), over-redaction of public entities (LOW).

---

### Phase 2: Chunking and Boundary Detection (Stages 1, 2)

**Goal:** Verify the article was chunked and segmented sensibly.

1. **Read `stage_1_chunks.json`**. Verify chunk count matches article count. Check that `body_text` in chunks is non-empty and retains structure.

2. **Read `stage_2_segments.json`**. Check:
   - Segment count per article: 15-40 is typical for a multi-step KB article
   - `single_sentence_rate`: expect 65-85%. Below 50% means boundaries are too aggressive. Above 90% means every sentence became its own segment.
   - Read 3-5 sample segments to verify they are coherent text, not fragments.

**Key findings:** Unusually high/low segment counts, empty segments, segments containing markdown artifacts (headers, bullet markers that should have been stripped in Stage C preprocessing).

---

### Phase 3: Atom Quality (Stages 3, 4)

**Goal:** Verify claims are correctly decomposed and typed.

1. **Read `stage_4_atoms.json`**. Print ALL atoms with their type and text:
   ```bash
   python3 -c "
   import json
   atoms = json.load(open('stage_4_atoms.json'))
   print(f'Total: {len(atoms)}')
   for a in atoms:
       print(f'[{a[\"atom_type\"]:12s}] {a[\"text\"][:120]}')
   "
   ```

2. **Check atom type distribution.** Apply these heuristics:
   - `procedure` atoms should describe *actions* (imperative verbs: tap, click, navigate, disconnect, verify, select)
   - `fact` atoms should describe *states* (is, has, contains, remains, may be)
   - `rule` atoms should describe *conditions* (if X then Y, must, required, only when)
   - `definition` atoms should describe *what something is*
   - `reference` atoms should be support contacts, URLs, ticket references, agent instructions

3. **Flag misclassified atoms.** Common errors:
   - "X is found after clicking Y" typed as `procedure` — should be `fact`
   - "X may be set to ON" typed as `procedure` — should be `fact`
   - "X has login policies" typed as `procedure` — should be `fact`
   - Pure navigation path strings ("Settings > General > Transfer") with no action verb — `reference` or `fact`

4. **Check for over-decomposition.** If a single numbered troubleshooting step in the source article produced 4+ atoms, the LLM is splitting navigation sub-paths into individual atoms. This loses step context. Note how many atoms came from each segment.

5. **Verify atom text is sanitized.** No atom should contain the real company name, real employee names, or real internal URLs.

**Key findings:** Type misclassification rate >20% (HIGH), over-decomposition pattern (MEDIUM), unsanitized content in atoms (CRITICAL).

---

### Phase 4: Entity Quality (Stage 5)

**Goal:** Verify entities are correctly typed, non-fragmented, and meaningful.

1. **Read `final/entities.json`**. Print all entities:
   ```bash
   python3 -c "
   import json
   from collections import Counter
   entities = json.load(open('final/entities.json'))
   types = Counter(e['entity_type'] for e in entities)
   print('Total:', len(entities), '| By type:', dict(types))
   print()
   for e in entities:
       print(f'[{e[\"entity_type\"]:15s}] {e[\"canonical_label\"]}  (mentions={e[\"mention_count\"]}, aliases={e[\"aliases\"]})')
   "
   ```

2. **Check entity type assignments.** Apply these rules:
   - Any entity whose canonical label is clearly an organization name should be ORG, not PERSON
   - VPN or software products should be SOFTWARE, not PERSON
   - Navigation menu items (Settings, iCloud, General) should be UI_ELEMENT, not CONCEPT
   - Support phone numbers or URLs embedded in entity labels are junk entities
   - Link preview boilerplate leaking into labels (e.g., "Find support for your service") is a junk entity

3. **Check for fragmentation.** Look for entity groups that refer to the same concept:
   - Multiple grammatical forms of the same term (possessive, "your X", "the X", "an X") that were not merged
   - Same product described as both CONCEPT and SOFTWARE
   - A company appearing as ORG while its support service appears as separate CONCEPT

4. **Calculate effective fragmentation ratio.** Count how many distinct real-world concepts the entities represent vs how many entity records exist. A ratio above 2.0 is HIGH severity.

5. **Check `mention_count` distribution.** In a single article, >60% singletons is expected. In a 10+ article run, >40% singletons indicates fragmentation.

6. **Flag type errors that propagate downstream.** If an ORG was typed PERSON in Stage B, Stage C Faker used a person name generator — meaning company-as-person names now appear throughout the graph. These cause all downstream stages to inherit nonsensical entity labels.

**Key findings:** PERSON/ORG or PERSON/SOFTWARE misclassification (HIGH), fragmentation ratio >2.0 (MEDIUM), junk entity labels containing URLs or phone numbers (MEDIUM), entity count vs article count anomalies (INFO).

---

### Phase 5: Triple and Predicate Quality (Stage 6)

**Goal:** Verify extracted relationships are semantically correct and predicates are normalized.

1. **Read `stage_6_triples.jsonl`**. Print all triples in readable form:
   ```bash
   python3 -c "
   import json
   for line in open('stage_6_triples.jsonl'):
       t = json.loads(line.strip())
       if t.get('_meta'): continue
       subj = t.get('subject_label') or t.get('entity','?')
       pred = t.get('predicate_label') or t.get('attribute','?')
       obj = t.get('value','?')
       cond = f' [IF: {t[\"condition\"]}]' if t.get('condition') else ''
       norm = t.get('normalization_confidence', 0)
       print(f'  {subj} --[{pred}]--> {obj}{cond}  (norm_conf={norm:.2f})')
   "
   ```

2. **Verify semantic correctness of each triple.** For each triple, check:
   - Does the subject-predicate-object relationship match what the source article actually says?
   - Is the direction correct? (e.g., "A owned_by B" vs "B owns A")
   - Is the condition (IF clause) accurate?
   - Does the subject/object refer to the entity that makes semantic sense (not a garbled synthetic name)?

3. **Check predicate normalization.** Look at `predicate_uri` and `normalization_confidence`:
   - `predicate_uri: "kb://predicates/unmapped"` with `normalization_confidence: 0.0` means the predicate is not in the 116-predicate taxonomy
   - `normalization_confidence < 0.5` means the predicate is weakly mapped and may be wrong

4. **Check triple coverage.** What percentage of atoms produced triples?
   - For KB procedure articles: expect 15-30% of atoms to yield triples
   - Below 10%: LLM could not find relationships (article may be pure procedural with no relational content — acceptable)
   - Above 50%: likely over-extraction

5. **Read `final/predicates.json`** and note which predicates are in use. Are there custom predicates that should be added to the taxonomy in `pipeline/config.yaml`?

**Key findings:** Semantically inverted triples (HIGH), unmapped predicates at >20% of total (MEDIUM), directional errors in ownership/containment (HIGH), triple coverage anomalies (INFO).

---

### Phase 6: Procedure Quality (Stage 7)

**Goal:** Verify procedures are structured, sequenced, and contain actionable steps.

1. **Read `stage_7_procedures.jsonl`** — this has the rich structure Stage 7 produces, separate from the merged atom output. Print a summary of the first 5 procedures:
   ```bash
   python3 -c "
   import json
   procs = [json.loads(l) for l in open('stage_7_procedures.jsonl') if l.strip() and not json.loads(l.strip()).get('_meta')]
   print(f'Total: {len(procs)}')
   for p in procs[:5]:
       steps = p.get('steps', [])
       print(f'  Title: {p.get(\"title\",\"?\")}')
       print(f'  Goal: {p.get(\"goal\",\"?\")}')
       print(f'  Steps: {len(steps)} | Preconditions: {len(p.get(\"preconditions\",[]))}')
       for s in steps:
           print(f'    [{s[\"step_number\"]}] {s[\"action\"]} — {s.get(\"detail\",\"\")}')
       print()
   "
   ```

2. **Check step quality.** For each procedure:
   - Does the `title` accurately describe the action?
   - Does the `goal` state a meaningful outcome?
   - Are `steps[]` specific enough to execute? ("Disconnect VPN" is good; "Perform the action" is bad)
   - Are `preconditions` meaningful when the procedure clearly has prerequisites?

3. **Check single-step rate** from `statistics.json` (`procedures.single_step_rate`):
   - Rate >80%: LLM is not aggregating sub-steps. Each micro-action became a 1-step procedure instead of grouping related steps.
   - Rate <30%: LLM is over-aggregating, stuffing unrelated steps together.
   - Target: 40-65% single-step rate for KB troubleshooting articles.

4. **Verify procedure chain structure.** From `statistics.json`:
   - `chain_count`: for a single troubleshooting article, expect 1-3 chains
   - If `max_chain_length` equals `total_procedure_count` with only 1 chain, the chaining is treating every micro-action as a sequential step rather than grouping into main steps

5. **Check `atom.procedure.steps[]` in `final/atoms.json`** for procedure-type atoms. This should be populated. Note: `atom.normalized_steps` at the root level is a legacy/unused field — empty is expected and is NOT a bug. The live step data is in `atom.procedure.steps`.

**Key findings:** High single-step rate indicating over-decomposition (MEDIUM), missing or vague step descriptions (MEDIUM), chain structure anomalies (INFO), empty `procedure.steps` arrays on procedure-type atoms (HIGH).

---

### Phase 7: Deduplication (Stage 8)

**Goal:** Verify the dedup correctly identified near-duplicates without false positives.

1. **Read `final/review_items.json`**. For each review item:
   - Read both `canonical_text` and `duplicate_text`
   - Are they genuinely semantically equivalent?
   - Are they from the same article or different articles?
   - What is the similarity score? (>0.95 is near-certain duplicate; 0.85-0.95 needs review)

2. **Check dedup statistics** from `statistics.json`:
   - Single article: expect 0-2 review items
   - 10+ articles: expect 5-15% of atoms to have near-duplicates across articles

3. **Check for false positives.** Are any review items actually *distinct* atoms that happen to be phrased similarly? (e.g., "Inbound Call: reach out to carrier" vs "Help ticket: reach out to carrier" — similar wording but distinct channel instructions that should both be kept)

**Key findings:** False positive dedup (legitimate distinct atoms incorrectly merged) is HIGH. Obvious missed duplicates are MEDIUM.

---

### Phase 8: Graph Structure (Stage 9)

**Goal:** Verify the knowledge graph has expected connectivity and correct edge types.

1. **Read `final/graph_edges.json`**. Print edge type distribution:
   ```bash
   python3 -c "
   import json
   from collections import Counter
   edges = json.load(open('final/graph_edges.json'))
   types = Counter(e.get('type') for e in edges)
   print('Edge types:', dict(types))
   print('Total:', len(edges))
   "
   ```

2. **Verify expected edge types are present:**
   - `NEXT_STEP`: connects procedures in troubleshooting sequence
   - `PART_OF_FLOW`: connects procedures to their parent flow
   - `DERIVED_FROM`: policies and rules point back to source atoms
   - `GOVERNS`: policies and rules reference the entities they govern
   - Semantic triple edges (owned_by, contains, supports, etc.) from Stage 6

3. **Check DERIVED_FROM completeness.** Every policy and rule must have exactly one DERIVED_FROM edge:
   ```bash
   python3 -c "
   import json
   edges = json.load(open('final/graph_edges.json'))
   policies = json.load(open('final/policies.json'))
   rules = json.load(open('final/rules.json'))
   derived = [e for e in edges if e.get('type') == 'DERIVED_FROM']
   print(f'Policies: {len(policies)}, Rules: {len(rules)}, DERIVED_FROM edges: {len(derived)}')
   if len(derived) != len(policies) + len(rules):
       print('WARNING: count mismatch — check source_atom_id vs atom_id field name in stage_9_output/run.py')
   "
   ```

4. **Check isolated node rate** from `statistics.json`:
   - Single article: 50-70% isolation is normal
   - 10 articles: 30-50% expected
   - 100+ articles: target <20%
   - Above these thresholds at scale indicates underperforming entity resolution or triple extraction

5. **Verify `vector_db_atoms.jsonl` has embeddings:**
   ```bash
   python3 -c "
   import json
   with open('final/vector_db_atoms.jsonl') as f:
       line = f.readline()
       a = json.loads(line)
       emb = a.get('embedding', [])
       print(f'Embedding dim: {len(emb)}, first 3 values: {emb[:3]}')
   "
   ```
   Expected embedding dimension: 1024 (RunPod Qwen3-Embedding-8B Matryoshka-truncated).

6. **Verify all expected output files exist and are non-empty:**
   - `atoms.json`, `entities.json`, `predicates.json`, `graph_nodes.json`, `graph_edges.json`
   - `vector_db_atoms.jsonl`, `review_items.json`, `policies.json`, `rules.json`, `statistics.json`

**Key findings:** Missing DERIVED_FROM edges (HIGH), zero embeddings in vector_db_atoms.jsonl (CRITICAL), isolated node rate above threshold for the scale of this run (MEDIUM).

---

### Phase 9: Cross-Cutting Anomaly Detection

Run these quick checks across the full output:

1. **Sanitization bleed-through in downstream outputs:**
   ```bash
   grep -il "chick-fil-a\|@cfa\|cfahome\|central avenue" final/atoms.json final/entities.json stage_6_triples.jsonl 2>/dev/null
   ```

2. **Empty text fields.** Any atom with empty `text`, entity with empty `canonical_label`, or procedure with empty `goal` is a parsing or extraction failure.

3. **Statistics consistency.** Verify the counts in `statistics.json` match actual file contents:
   ```bash
   python3 -c "
   import json
   stats = json.load(open('final/statistics.json'))
   atoms = json.load(open('final/atoms.json'))
   entities = json.load(open('final/entities.json'))
   edges = json.load(open('final/graph_edges.json'))
   print(f'Atoms: stats={stats[\"atoms\"][\"total\"]} actual={len(atoms)} match={stats[\"atoms\"][\"total\"]==len(atoms)}')
   print(f'Entities: stats={stats[\"entities\"][\"total\"]} actual={len(entities)} match={stats[\"entities\"][\"total\"]==len(entities)}')
   print(f'Edges: stats={stats[\"graph\"][\"total_edges\"]} actual={len(edges)} match={stats[\"graph\"][\"total_edges\"]==len(edges)}')
   "
   ```

4. **ID cross-reference spot check.** Sample 3 atoms from `final/atoms.json`. For each, verify:
   - Its `atom_id` appears in `vector_db_atoms.jsonl`
   - If it is a procedure-type atom, its `atom_id` appears in `stage_7_procedures.jsonl` source_atom_ids
   - Its `entity_refs` point to valid entries in `entities.json`

---

### Phase 10: Evaluation Report

Produce a structured report in this format:

---

**Pipeline Output Evaluation Report**

**Run:** [output directory name]
**Date:** [from statistics.json or current date]
**Articles processed:** [N]
**Stages run:** [list from statistics.json]

---

**Executive Summary**

[2-4 sentence summary: did the run succeed, what are the top 2-3 issues, is it ready for scale-up to the full corpus]

---

**Counts vs Expectations**

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Atoms (total) | N x 35-60 | ... | pass/warn/fail |
| Atoms per article | 35-60 | ... | pass/warn/fail |
| Entities (total) | N x 25-50 | ... | pass/warn/fail |
| Entity fragmentation ratio | <2.0 | ... | pass/warn/fail |
| Triples | N x 8-20 | ... | pass/warn/fail |
| Procedure single-step rate | 40-65% | ...% | pass/warn/fail |
| DERIVED_FROM completeness | 100% | ...% | pass/warn/fail |
| Isolated nodes | <50% (1 article) | ...% | pass/warn/fail |
| Embedding dimension | 1024 | ... | pass/warn/fail |

---

**Findings**

CRITICAL (data loss or semantic corruption):
- [C1] description — Stage: X — Evidence: quote or count

HIGH (semantic errors that produce wrong answers at query time):
- [H1] description — Stage: X — Evidence: quote or count

MEDIUM (quality issues that degrade usefulness):
- [M1] description — Stage: X — Evidence: quote or count

LOW (observations worth tracking across runs):
- [L1] description — Stage: X — Evidence: quote or count

---

**Scale Readiness Assessment**

[Direct answer: is this output good enough to run the full 10K article corpus? What must be fixed first vs what can wait? What will improve naturally at scale vs what will get worse?]

---

**Recommended Next Steps**

1. [highest priority fix, with specific file/function pointer if identifiable from the evidence]
2. [next fix]
3. ...

---

## Notes for the Evaluator

- `atom.normalized_steps` at the root level being empty is NOT a bug. Step data lives in `atom.procedure.steps[]`. Only report this as an issue if `atom.procedure.steps` is also empty for procedure-type atoms.
- Verizon appearing unsanitized while Apple and Samsung are replaced is not necessarily wrong. Verizon is simply absent from the denylist. Whether that is correct depends on whether CFA's Verizon relationship is considered confidential.
- 63%+ isolated nodes at single-article scale is expected and is not a finding unless it persists above 20% at 100+ article scale.
- Entity type misclassification of synthetic company names (e.g., "Keith-Francis" typed PERSON) is a downstream consequence of Stage C generating surname-style company names using Faker's person name provider. The root cause is Stage B incorrectly classifying the original org as PERSON before Stage C substitution. Fix is in Stage B entity type detection or in Stage C's Faker generator selection logic.
- The `term_classifications.csv` produced by `pipeline/tools/extract_terms.py` is NOT consumed by the A-through-9 pipeline. It is a standalone corpus analysis tool for informing the safelist and denylist. It does not affect pipeline output quality directly.
