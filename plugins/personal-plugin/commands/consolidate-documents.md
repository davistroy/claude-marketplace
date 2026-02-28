---
description: Analyze multiple document variations and synthesize a superior consolidated version
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Document Consolidation

Consolidate multiple variations of a document into a single, optimized version. Analyzes structural differences, resolves conflicts, and synthesizes the best elements from each source.

## Input Validation

**Required Arguments:**
- `<doc1-path> <doc2-path> [doc3-path...]` — Two or more file paths to documents to consolidate

**Optional Flags:**

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--format` | `markdown`, `text` | `markdown` | Output format for the consolidated document |
| `--preview` | (none — boolean flag) | off | Show consolidated outline and key decisions before writing full output |
| `--no-prompt` | (none — boolean flag) | off | Skip confirmation prompts (for automation/scripting) |
| `--baseline` | `<doc-path>` | (none) | Designate one document as the primary reference. Structure and terminology from this document take precedence when sources are equivalent. |

**Argument Parsing Rules:**
- File paths are positional arguments (no flag prefix)
- Flags can appear in any position (before, between, or after file paths)
- Paths containing spaces must be quoted
- Glob patterns are NOT expanded — provide explicit file paths

**Examples:**
```text
/consolidate-documents draft-v1.md draft-v2.md
/consolidate-documents spec-a.md spec-b.md spec-c.md --preview
/consolidate-documents old.md new.md --baseline old.md --format text
/consolidate-documents "path with spaces/doc1.md" doc2.md --no-prompt
```

### Validation Checks

Run these checks before proceeding. On failure, display the error and stop.

| Check | Error Message |
|-------|---------------|
| Fewer than 2 file paths provided | `Error: At least 2 documents required. Usage: /consolidate-documents <doc1> <doc2> [doc3...]` |
| File path does not exist | `Error: File not found: [path]. Verify the path and try again.` |
| File is binary (not text) | `Error: Binary file detected: [path]. This command only processes text documents.` |
| All files are identical | `Notice: All [N] documents are identical. No consolidation needed. The document is already at: [path]` |
| Single unique file (duplicates removed) | `Notice: After removing duplicates, only 1 unique document remains. No consolidation needed.` |
| `--baseline` path not in file list | `Error: Baseline document [path] must also be listed as an input document.` |
| `--format` value not recognized | `Error: Unsupported format "[value]". Supported: markdown, text` |

If no arguments are provided at all, display the usage help:

```text
Usage: /consolidate-documents <doc1> <doc2> [doc3...] [flags]

Consolidate multiple document versions into a single optimized version.

Required:
  <doc1> <doc2>    At least two document paths

Optional flags:
  --format <fmt>   Output format: markdown (default), text
  --preview        Show outline before writing full output
  --no-prompt      Skip confirmation prompts
  --baseline <doc> Designate primary reference document

Examples:
  /consolidate-documents draft-v1.md draft-v2.md
  /consolidate-documents spec-a.md spec-b.md --preview --baseline spec-a.md
```

---

## Instructions

### Step 1: Read and Catalog Sources

Read each input document and build a source catalog:

| Document | Path | Size (lines) | Sections | Format | Key Topics |
|----------|------|--------------|----------|--------|------------|
| Doc 1 | ... | ... | ... | ... | ... |
| Doc 2 | ... | ... | ... | ... | ... |

**Context management:** If total content across all documents exceeds approximately 60% of available context, use this strategy:
1. Read each document's structure first (headings and first paragraph of each section)
2. Identify which sections differ across documents (these need full reads)
3. For sections that are identical or near-identical across all documents, read one copy in full and note the others as duplicates
4. Summarize sections that are unchanged and low-priority to conserve context

If the user provided context about intended audience or use case, record it here for use in synthesis decisions.

### Step 2: Structural Analysis

For each source document, identify:
- **Overall structure** — Sections, hierarchy, heading levels, flow
- **Organizational approach** — Chronological, categorical, procedural, comparative, etc.
- **Formatting conventions** — Heading styles, list types, code blocks, tables, emphasis patterns
- **Terminology** — Key terms and whether they are consistent across documents

Determine which structure best supports the stated (or inferred) use case. If `--baseline` is set, the baseline document's structure takes precedence unless another document's structure is clearly superior.

**Output a brief structural comparison:**

| Aspect | Doc 1 | Doc 2 | Doc 3 | Winner |
|--------|-------|-------|-------|--------|
| Section count | 8 | 12 | 10 | Doc 2 (most complete) |
| Hierarchy depth | 2 levels | 3 levels | 3 levels | Doc 2/3 (tied) |
| Format quality | Basic | Tables + code | Tables | Doc 2 |
| Terminology | Consistent | Consistent | Mixed | Doc 1/2 (tied) |

### Step 3: Element-by-Element Comparison

For each concept, step, or component covered across the documents:

1. **Clarity winner** — Which version articulates it most clearly? (Fewest words to full understanding)
2. **Completeness check** — Which includes critical details the others omit?
3. **Conflict resolution** — Where versions contradict each other:
   - If `--baseline` is set, prefer the baseline version unless the other is clearly more accurate
   - If no baseline, prefer the most specific and actionable version
   - Note all conflicts for the consolidation notes
4. **Unique value** — What does each source contribute that others lack entirely?

Track findings in a comparison matrix for use in Step 4 and the consolidation notes.

### Step 4: Synthesis

Create the consolidated document using these criteria in priority order:

1. **Completeness** — No critical elements lost from any source
2. **Coherence** — Content fits the overall flow and chosen structure
3. **Clarity** — Language and structure minimize ambiguity
4. **Practicality** — Actionable and implementable as written
5. **Conciseness** — Eliminate redundancy without sacrificing meaning

**Synthesis Rules:**
- Preserve the best articulation of each concept (not necessarily the longest)
- Merge complementary details from different sources into unified sections
- Resolve conflicts by choosing the most accurate/practical version (document the choice)
- Maintain consistent voice and terminology throughout
- Match the formatting style of the highest-quality source (or the baseline if set)
- Do NOT invent content that does not appear in any source document
- Do NOT silently drop content — if something is intentionally excluded, note it in consolidation notes

**If `--preview` flag is set**, pause here and present:
1. The proposed outline (section headings with 1-line descriptions)
2. Key conflict resolutions (which version won and why)
3. Content that will be excluded (and why)

Ask the user to confirm before proceeding to Step 5. If the user requests changes, adjust the plan accordingly.

### Step 5: Generate Output

**Topic Derivation:**
Derive the `[topic]` for the output filename as follows:
1. If all documents share a common topic/subject in their filenames (e.g., `requirements-v1.md`, `requirements-v2.md`), use that topic (`requirements`)
2. If documents have the same base name with version suffixes, use the base name
3. If documents have completely different names, ask the user for a topic name (unless `--no-prompt` is set, in which case use `documents`)

**Output Location:** Save to the `reports/` directory. Create the directory if it does not exist.

**Filename Format:** `consolidated-[topic]-YYYYMMDD-HHMMSS.md` (or `.txt` if `--format text`)

**Output File Structure:**

```markdown
# Consolidated: [Topic]

**Generated:** YYYY-MM-DD HH:MM:SS
**Source Documents:**
- [doc1 path] ([line count] lines)
- [doc2 path] ([line count] lines)
- [doc3 path] ([line count] lines)
**Baseline:** [baseline path or "None — equal weight"]
**Format:** [markdown/text]

---

## [Consolidated content begins here]

[The complete merged document, ready for use]

---

## Consolidation Notes

### Structure Decision
[Why the chosen organizational approach was selected. Which source's structure
was adopted and why.]

### Key Divergences
[Where sources conflicted and how each conflict was resolved. Format as a
numbered list with the conflicting versions and the resolution rationale.]

### Preserved Additions
[Unique elements preserved from specific sources — content that appeared in
only one document but was valuable enough to include.]

### Intentional Omissions
[What was deliberately excluded and why. If nothing was omitted, state
"No content was omitted." Do NOT leave this section empty without explanation.]

### Source Contribution Summary
| Source | Sections Adopted | Unique Contributions | Conflicts Won |
|--------|-----------------|---------------------|---------------|
| Doc 1  | [count]         | [brief list]        | [count]       |
| Doc 2  | [count]         | [brief list]        | [count]       |
```

### Step 6: Post-Output Summary

After writing the file, display:

```
Consolidation Complete
======================
Output:    [full path to output file]
Sources:   [N] documents consolidated
Conflicts: [N] resolved ([M] in favor of baseline, [K] by quality)
Omissions: [N] items intentionally excluded

Review the Consolidation Notes section at the end of the output file for
full details on merge decisions.
```

---

## Error Handling

Handle these scenarios explicitly:

| Scenario | Behavior |
|----------|----------|
| **No files specified** | Display usage help (see Input Validation section) |
| **Single file provided** | `Error: At least 2 documents required for consolidation.` |
| **File not found** | Report which file(s) are missing with full paths. Do not proceed. |
| **Binary file detected** | Skip the binary file. If fewer than 2 text files remain, stop with error. |
| **Identical documents** | Report that documents are identical. No output file generated. |
| **Mixed formats** (e.g., .md and .txt) | Proceed — note format differences in consolidation notes. Output uses `--format` flag or markdown default. |
| **Empty file** | Warn about the empty file. Exclude it from consolidation. If fewer than 2 non-empty files remain, stop. |
| **Document too large for context** | Use the context management strategy from Step 1. If even the structure-first approach exceeds context, report: "Documents are too large for single-pass consolidation. Consider splitting into sections and consolidating each section separately." |
| **Write permission denied** | Report the target path and suggest an alternative location. |
| **reports/ directory creation fails** | Fall back to writing in the current directory. Report the fallback. |

---

## Related Commands

- `/assess-document` — Evaluate document quality before or after consolidation
- `/analyze-transcript` — Convert meeting transcripts to structured reports for consolidation
- `/define-questions` — Extract open questions from consolidated documents
- `/finish-document` — Resolve remaining TBDs in the consolidated output
- `/remove-ip` — Sanitize the consolidated document for external sharing
