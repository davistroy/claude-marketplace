---
description: Analyze multiple document variations and synthesize a superior consolidated version
---

# Document Consolidation

You are consolidating multiple variations of a document into a single, optimized version. The user will provide paths to the source documents or paste their contents.

## Process

### Step 1: Gather Sources

Ask the user to provide the documents to consolidate. Accept any of:
- File paths (relative or absolute)
- Pasted content
- URLs (if web fetch is available)

If the user provides context about:
- **Baseline document**: Which source should be the primary reference
- **Intended audience**: Who will use the consolidated document
- **Use case**: How the document will be used

Incorporate this context into your synthesis decisions.

### Step 2: Structural Analysis

For each source document, identify:
- Overall structure (sections, hierarchy, flow)
- Core concepts and components covered
- Organizational approach (chronological, categorical, procedural, etc.)
- Formatting conventions (headings, lists, code blocks, etc.)

Determine which structure best supports clarity and usability for the stated use case.

### Step 3: Element-by-Element Comparison

For each concept, step, or component covered across the documents:

1. **Clarity winner**: Which version articulates it most clearly?
2. **Completeness check**: Which includes critical details the others omit?
3. **Conflict resolution**: Where versions conflict, which is most accurate/practical?
4. **Unique value**: What does each source contribute that others lack?

Track your findings for the consolidation notes.

### Step 4: Synthesis

Create the consolidated document applying these criteria in priority order:

1. **Completeness**: No critical elements lost from any source
2. **Coherence**: Content fits the overall flow and structure
3. **Clarity**: Language and structure minimize ambiguity
4. **Practicality**: Actionable and implementable as written
5. **Conciseness**: Eliminate redundancy without sacrificing meaning

Rules:
- Preserve the best articulation of each concept
- Merge complementary details from different sources
- Resolve conflicts by choosing the most accurate/practical version
- Maintain consistent voice and terminology throughout
- Match the formatting style of the highest-quality source

### Step 5: Output

Produce two sections:

#### Consolidated Document
The complete, merged document ready for use.

#### Consolidation Notes
A brief section explaining:
- **Structure decision**: Why you chose the organizational approach
- **Key divergences**: Where sources conflicted and how you resolved it
- **Additions**: Unique elements preserved from specific sources
- **Omissions**: What was intentionally excluded and why (if anything)

## Execution

Begin by asking the user for the source documents if not already provided. Then work through each step, showing your analysis before producing the final consolidated output.
