<!-- ============================================================
     SYNTHESIS COMMAND TEMPLATE

     Canonical Section Order (per schemas/command.json):
     1. Frontmatter (description, allowed-tools)
     2. Title (# Command Name)
     3. Brief description paragraph
     4. Input Validation
     5. Instructions (organized as phases)
     6. Output Format (required for synthesis)
     7. Examples
     8. Performance (recommended)

     Pattern References:
     - Naming: references/patterns/naming.md
     - Validation: references/patterns/validation.md
     - Output: references/patterns/output.md (consolidation notes)
     - Workflow: references/patterns/workflow.md (multi-source handling)

     Note: Synthesis commands MERGE MULTIPLE SOURCES into a superior combined output
     ============================================================ -->

<!-- SECTION 1: FRONTMATTER -->
---
description: {{DESCRIPTION}}
---

<!-- SECTION 2: TITLE -->
# {{TITLE}}

<!-- SECTION 3: BRIEF DESCRIPTION -->
{{INTRO_PARAGRAPH}}

<!-- SECTION 4: INPUT VALIDATION -->
## Input Validation

**Required Arguments:**
- `<source1>` - First source to consolidate
- `<source2>` - Second source to consolidate
- `[source3...]` - Additional sources (optional)

**Minimum Requirement:** At least 2 sources must be provided.

**Optional Arguments:**
- `--baseline <source>` - Specify which source is the primary reference
- `--preview` - Show synthesis plan before generating output

**Input Types:**

Sources can be provided as:
| Type | Format | Example |
|------|--------|---------|
| **File paths** | Space-separated paths | `doc-v1.md doc-v2.md` |
| **Pasted content** | Paste when prompted | (provide content in chat) |
| **URLs** | Web addresses (if fetch available) | `https://example.com/doc.md` |

**Validation:**
If fewer than two sources are provided, display:
```
Error: Insufficient sources provided

Usage: /{{COMMAND_NAME}} <source1> <source2> [source3...]

This command requires at least 2 sources to compare and synthesize.
It analyzes multiple versions/variations and creates a superior combined output.

Arguments:
  <source1>     First source (required)
  <source2>     Second source (required)
  [source3...]  Additional sources (optional)
  --baseline    Specify primary reference source
  --preview     Show synthesis plan before output

Examples:
  /{{COMMAND_NAME}} draft-v1.md draft-v2.md
  /{{COMMAND_NAME}} spec-a.md spec-b.md spec-c.md
  /{{COMMAND_NAME}} old.md new.md --baseline old.md
```

See `references/patterns/validation.md` for error message format.

<!-- SECTION 5: INSTRUCTIONS -->
## Instructions

### Phase 1: Gather Sources

1. **Collect all source materials** - Accept file paths, pasted content, or URLs
2. **Validate source availability** - Ensure all sources can be read
3. **Identify baseline** (if specified) - Note which source is the primary reference

If the user provides context about:
- **Baseline source**: Which source should be the primary reference
- **Intended audience**: Who will use the consolidated output
- **Use case**: How the output will be used

Incorporate this context into synthesis decisions.

### Phase 2: Structural Analysis

For each source, identify:
- Overall structure (sections, hierarchy, flow)
- Core concepts and components covered
- Organizational approach (chronological, categorical, procedural, etc.)
- Formatting conventions (headings, lists, code blocks, etc.)

Determine which structure best supports clarity and usability for the stated use case.

### Phase 3: Element-by-Element Comparison

For each concept, step, or component covered across sources:

1. **Clarity winner**: Which version articulates it most clearly?
2. **Completeness check**: Which includes critical details others omit?
3. **Conflict resolution**: Where versions conflict, which is most accurate/practical?
4. **Unique value**: What does each source contribute that others lack?

Track findings for the synthesis notes.

### Phase 4: Synthesis

Create the consolidated output applying these criteria in priority order:

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

### Phase 5: Output

1. **Ensure output directory exists**:
   ```bash
   mkdir -p {{OUTPUT_LOCATION}}
   ```
   See `references/patterns/output.md` for directory auto-creation pattern.

2. **Write consolidated output** following naming conventions

3. **Include synthesis notes** explaining decisions made

<!-- SECTION 6: OUTPUT FORMAT -->
## Output Format

**File Naming:** `consolidated-[topic]-YYYYMMDD-HHMMSS.md`

See `references/patterns/naming.md` for naming conventions.

**Location:** `{{OUTPUT_LOCATION}}`

Example: `consolidated-requirements-20260114-143052.md`

### Output Structure

The output file must contain two sections:

#### 1. Consolidated Content
The complete, merged content ready for use.

#### 2. Synthesis Notes
A brief section explaining:
- **Structure decision**: Why you chose the organizational approach
- **Key divergences**: Where sources conflicted and how you resolved it
- **Additions**: Unique elements preserved from specific sources
- **Omissions**: What was intentionally excluded and why (if anything)

### Completion Message

```
Synthesis complete.

Sources analyzed: X
Conflicts resolved: Y
Unique elements merged: Z

Output saved to: {{OUTPUT_LOCATION}}/consolidated-[topic]-YYYYMMDD-HHMMSS.md

Key decisions:
- Structure based on: [source name]
- [X] conflicts resolved (see Synthesis Notes)
- [Y] unique elements preserved from individual sources
```

<!-- SECTION 7: EXAMPLES -->
## Examples

### Basic Usage

```
User: /{{COMMAND_NAME}} draft-v1.md draft-v2.md

Claude: Analyzing sources for consolidation...

**Source 1: draft-v1.md**
- 5 sections, chronological structure
- Strong on technical details
- Missing user guidance

**Source 2: draft-v2.md**
- 4 sections, task-based structure
- Better user explanations
- Less technical depth

**Synthesis Plan:**
- Using task-based structure from draft-v2.md (better usability)
- Incorporating technical details from draft-v1.md
- 2 content conflicts to resolve

Proceeding with synthesis...

Synthesis complete.

Sources analyzed: 2
Conflicts resolved: 2
Unique elements merged: 8

Output saved to: reports/consolidated-draft-20260114-143052.md
```

### With Baseline Specified

```
User: /{{COMMAND_NAME}} spec-old.md spec-new.md updates.md --baseline spec-old.md

Claude: Using spec-old.md as baseline reference...

Analyzing divergences from baseline...

**Baseline: spec-old.md**
- 12 sections, established structure
- Will preserve unless explicitly improved

**Additions from spec-new.md:**
- 2 new sections
- 5 updated requirements

**Additions from updates.md:**
- 3 clarifications
- 1 new constraint

Synthesis complete.

Output saved to: reports/consolidated-spec-20260114-143052.md
```

### Preview Mode

```
User: /{{COMMAND_NAME}} doc1.md doc2.md doc3.md --preview

Claude:
Preview: /{{COMMAND_NAME}}
------------------------------------------
Sources: 3 documents
Baseline: None specified (will auto-detect)

Structural Analysis:
  doc1.md: 8 sections, procedural
  doc2.md: 6 sections, conceptual
  doc3.md: 10 sections, mixed

Proposed Structure: Hybrid (procedural + conceptual intro)

Conflicts Detected: 4
  - Section 3: Different ordering approaches
  - Section 5: Contradictory requirements
  - Section 7: Terminology inconsistency
  - Section 9: Missing in doc2.md

Proceed with synthesis? (y/n):
```

<!-- SECTION 8: PERFORMANCE -->
## Performance

**Typical Duration:**

| Source Count | Combined Size | Expected Time |
|--------------|---------------|---------------|
| 2 sources | < 10KB | 1-2 minutes |
| 3-4 sources | 10-50KB | 2-5 minutes |
| 5+ sources | 50KB+ | 5-10 minutes |

**Factors Affecting Performance:**
- **Source count**: More sources = more comparisons
- **Content overlap**: High overlap requires more conflict resolution
- **Structural differences**: Different structures take longer to reconcile
- **Document complexity**: Technical content requires careful merging

**If the command seems stuck:**
1. Check for output activity
2. Wait at least 5 minutes for large/complex sources
3. If no activity, interrupt and try with fewer sources
4. Consider specifying a baseline to simplify decisions

See `references/patterns/logging.md` for performance documentation pattern.

## Execution Instructions

- **Preserve value from all sources** - Don't favor one source blindly
- **Document all decisions** - Synthesis notes are required
- **Resolve conflicts explicitly** - Don't leave ambiguities
- **Maintain consistency** - Voice, terminology, formatting should be uniform

Begin by gathering sources and presenting a structural analysis before synthesizing.
