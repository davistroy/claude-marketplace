# visual-explainer: Output Samples

Illustrative examples of what the tool's terminal output looks like at three points
in the workflow, all drawn from a single worked example (a hypothetical document on
quantum entanglement). These are samples for the model to pattern-match against when
rendering real results — not text the model must reproduce verbatim, and not
interactive payloads. Interaction payloads (`AskUserQuestion` calls) stay inline in
`SKILL.md`, not here.

## Phase 4: Content Analysis Summary

Referenced from SKILL.md's "Display the analysis summary:" instruction in Phase 4.

```text
Content Analysis
================
Document: "Understanding Quantum Entanglement"
Word Count: 1,847 words
Key Concepts: 5 concepts identified
Recommended Images: 3 images

Concept Flow:
1. Classical Physics Background
   -> 2. Quantum Superposition
   -> 3. Entanglement Phenomenon
   -> 4. Applications
   -> 5. Future Implications
```

## Phase 7: Progress Display Format

Referenced from SKILL.md's "Progress Display Format:" instruction in Phase 7.

```text
Starting Image Generation
=========================

Image 1 of 3: "The Classical Foundation"
----------------------------------------

Attempt 1/5:
  [=========>         ] Generating... (4.2s)
  Generated
  Evaluating...
    - Concept clarity: 72%
    - Visual appeal: 85%
    - Flow continuity: 60%
  Overall: 72% - NEEDS_REFINEMENT

Attempt 2/5:
  Refining: Adding visual flow indicators
  [=========>         ] Generating... (3.8s)
  Generated
  Evaluating...
    - Concept clarity: 91%
    - Visual appeal: 88%
    - Flow continuity: 85%
  Overall: 88% - PASS

Image 1 complete. Best version: Attempt 2

Image 2 of 3: "Quantum Superposition"
-------------------------------------
...
```

## Phase 8: Completion Summary

Referenced from SKILL.md's Phase 8 ("Completion Summary") section.

```text
Generation Complete
===================

Results:
  - Images generated: 3 of 3
  - Total attempts: 7
  - Average quality score: 89%
  - Estimated cost: $0.70

Output saved to:
  ./output/visual-explainer-quantum-entanglement-20260118-143052/

Final Images:
  1. 01-classical-foundation.jpg (Score: 88%)
  2. 02-quantum-superposition.jpg (Score: 91%)
  3. 03-entanglement-synthesis.jpg (Score: 88%)

Output Structure:
  metadata.json          # Full generation metadata
  concepts.json          # Extracted concepts
  summary.md             # Human-readable summary
  all-images/            # Final images only
    01-classical-foundation.jpg
    02-quantum-superposition.jpg
    03-entanglement-synthesis.jpg
  image-01/              # All attempts for image 1
    final.jpg
    prompt-v1.txt
    attempt-01.jpg
    evaluation-01.json
    ...

Would you like to:
1. View the summary report
2. Regenerate a specific image
3. Open output folder
```
