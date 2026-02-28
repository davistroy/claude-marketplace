---
description: Document quality evaluation with scored assessment report
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Document Assessment Command

Perform a comprehensive evaluation of the specified document, identifying gaps, issues, missing content, and areas for improvement. Produce a detailed assessment report.

## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document to assess

**Optional Arguments:**
- `--format [md|json]` - Output format (default: md)
  - `md`: Markdown report with tables and sections (default)
  - `json`: Structured data with scores, issues array, and recommendations
- `--no-prompt` - Disable interactive prompting for missing arguments (for scripts and CI/CD)

**Validation:**
If the document path is missing:

1. **If `--no-prompt` is specified**, display the error and exit:
```text
Error: Missing required argument

Usage: /assess-document <document-path> [--format md|json] [--no-prompt]
Example: /assess-document PRD.md
Example: /assess-document PRD.md --format json
```

2. **Otherwise (default), prompt interactively**:
```text
/assess-document requires a document path.

Please provide the path to the document to assess:
> _

(or use --no-prompt to disable interactive prompting)
```

Wait for the user to provide the document path, then proceed with assessment.

## Error Handling

Before starting the assessment, validate the input file:

| Error Condition | Detection | Response |
|----------------|-----------|----------|
| File not found | File does not exist at specified path | Display: "Error: File not found: [path]. Check the path and try again." |
| Empty file | File exists but has zero content | Display: "Error: File is empty: [path]. Nothing to assess." |
| Binary file | File contains non-text content (images, executables, archives) | Display: "Error: [path] appears to be a binary file. This command only assesses text documents (markdown, text, HTML, etc.)." |
| File too large | File exceeds context window capacity (~100K tokens) | Display: "Warning: [path] is very large (X lines). Assessment will focus on the first N sections. Consider splitting the document for a thorough review." |
| Unsupported format | File extension is not a text format (.pdf, .docx, .xlsx) | Display: "Error: Unsupported format ([ext]). Supported formats: .md, .txt, .html, .rst, .adoc. For Word documents, use /convert-markdown first." |

## Input

The user will provide a document path or name after the `/assess-document` command (e.g., `/assess-document PRD.md`).

## Instructions

### 1. Read and Analyze the Document

Thoroughly read the specified document from start to finish. Build a mental model of:
- The document's purpose and intended audience
- Its structure and organization
- The key concepts, requirements, or information it conveys
- How sections relate to each other

### 2. Evaluate Against Quality Dimensions

Assess the document across these dimensions:

#### Completeness
- Are all necessary sections present?
- Are there gaps in coverage?
- Are dependencies and prerequisites identified?
- Are edge cases and exceptions addressed?
- Is there missing context that readers would need?

#### Clarity
- Is the language clear and unambiguous?
- Are technical terms defined?
- Are complex concepts explained adequately?
- Is the intended audience clear?
- Are examples provided where helpful?

#### Consistency
- Is terminology used consistently throughout?
- Do sections contradict each other?
- Is the level of detail consistent across sections?
- Is the formatting and structure consistent?

#### Specificity
- Are requirements specific enough to be actionable?
- Are vague terms like "should", "may", "appropriate" clarified?
- Are quantities, thresholds, and constraints defined?
- Are success criteria measurable?

#### Structure & Organization
- Is the document logically organized?
- Is information easy to find?
- Are related topics grouped together?
- Is there unnecessary duplication?
- Is the hierarchy of information clear?

#### Feasibility & Realism
- Are the stated goals achievable?
- Are there unstated assumptions?
- Are resource requirements realistic?
- Are timelines (if any) reasonable?
- Are there technical or practical constraints not addressed?

### 3. Score Rubric (1-5 Scale)

Apply the following anchors when scoring each dimension. Use these definitions consistently to ensure scores are meaningful and comparable across assessments.

| Score | Label | Definition | Example Indicators |
|-------|-------|------------|-------------------|
| **1** | Fundamentally Flawed | Requires complete rewrite. The dimension is essentially unaddressed or so poorly executed that it actively misleads. | Missing critical sections, contradictory statements throughout, no clear audience, completely disorganized |
| **2** | Significant Gaps | Major revision needed. Some elements are present but large, important gaps remain that block use of the document. | Key sections exist but are incomplete, several ambiguous requirements, inconsistent terminology, major structural issues |
| **3** | Adequate | Functional but needs several improvements. The document serves its basic purpose but has notable weaknesses. | Most sections present with moderate gaps, some vague requirements, occasional inconsistencies, reasonable but imperfect structure |
| **4** | Good | Minor improvements needed. The document is solid and usable with only small issues remaining. | Comprehensive coverage with minor gaps, mostly clear language, consistent formatting, well-organized with minor issues |
| **5** | Excellent | Ready for use as-is. The dimension is thoroughly and skillfully addressed with no meaningful issues. | Complete coverage, precise language, fully consistent, specific and measurable, logical structure, realistic goals |

**Scoring guidelines:**
- Score the document against its own goals and context (a draft has different expectations than a final document)
- Half-point scores (e.g., 3.5) are acceptable for the Overall score but not for individual dimensions
- The Overall score is the weighted average of all dimensions (equal weight unless the document type suggests otherwise)

### 4. Identify Specific Issues

For each issue found, capture:
- **Category**: Which quality dimension it falls under
- **Severity**: CRITICAL / WARNING / SUGGESTION (see definitions below)
- **Location**: Section or line reference
- **Description**: What the issue is
- **Impact**: Why it matters
- **Recommendation**: How to address it

#### Severity Definitions

| Severity | Definition |
|----------|------------|
| **CRITICAL** | Blocks understanding or implementation; must be resolved immediately |
| **WARNING** | Significant gap or ambiguity; should be resolved before proceeding |
| **SUGGESTION** | Minor improvement opportunity; nice to have |

### 5. Produce the Assessment Report

Create a markdown file with the following structure:

```markdown
# Document Assessment: [Document Name]

**Assessment Date:** [Date]
**Document Version/Date:** [If available]
**Assessor:** Claude (Automated Review)

---

## Executive Summary

[2-3 paragraph overview of the document's current state, major strengths, and critical gaps]

### Assessment Score

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Completeness | X | [Brief note] |
| Clarity | X | [Brief note] |
| Consistency | X | [Brief note] |
| Specificity | X | [Brief note] |
| Structure | X | [Brief note] |
| Feasibility | X | [Brief note] |
| **Overall** | **X.X** | [Brief summary] |

### Score Rubric Reference

1 = Fundamentally flawed (rewrite needed) | 2 = Significant gaps (major revision) | 3 = Adequate (several improvements) | 4 = Good (minor improvements) | 5 = Excellent (ready for use)

### Issue Summary

| Severity | Count |
|----------|-------|
| CRITICAL | X |
| WARNING | X |
| SUGGESTION | X |
| **Total** | **X** |

---

## Strengths

[Bulleted list of what the document does well]

---

## CRITICAL Issues (Must Fix)

[For each critical issue, provide detailed analysis]

### C1. [Issue Title]

**Location:** [Section/Line reference]
**Impact:** [Why this matters]

[Detailed description of the issue]

**Recommendation:** [How to fix it]

---

## WARNING Issues (Should Fix)

### W1. [Issue Title]
...

---

## SUGGESTION Issues (Nice to Have)

### S1. [Issue Title]
...

---

## Missing Content

[List of sections, topics, or information that should be added]

---

## Structural Recommendations

[Suggestions for reorganizing or restructuring the document]

---

## Appendix: Question Inventory

[Optional: List of explicit questions found in the document that need answers]

---

*Assessment generated by Claude on [timestamp]*
```

### 6. Save the Output

Based on the `--format` flag:

**Directory Creation:**
Before writing any output file, ensure the target directory exists. If the output is going to the `reports/` directory (for centralized assessment storage), create it if needed:

```bash
# Ensure output directory exists before writing
mkdir -p reports/
```

**Output file naming — use this pattern consistently:**
- Format: `assessment-[document-name]-[timestamp].[ext]`
- Timestamp format: `YYYYMMDD-HHMMSS`
- The document name is derived from the source filename without its extension
- Always place output in the `reports/` directory

**Markdown Format (default):**
- Save to: `reports/assessment-[document-name]-[timestamp].md`
- Example: `reports/assessment-PRD-20260110-143052.md`

**JSON Format:**
- Save to: `reports/assessment-[document-name]-[timestamp].json`
- Example: `reports/assessment-PRD-20260110-143052.json`
- Structure:
```json
{
  "metadata": {
    "document": "PRD.md",
    "assessment_date": "2026-01-10T14:30:52Z",
    "document_version": "1.0"
  },
  "scores": {
    "completeness": 4,
    "clarity": 3,
    "consistency": 4,
    "specificity": 2,
    "structure": 4,
    "feasibility": 3,
    "overall": 3.3
  },
  "score_rubric": {
    "1": "Fundamentally flawed - requires rewrite",
    "2": "Significant gaps - major revision needed",
    "3": "Adequate - several improvements needed",
    "4": "Good - minor improvements needed",
    "5": "Excellent - ready for use"
  },
  "summary": "Executive summary text here...",
  "strengths": ["Strength 1", "Strength 2"],
  "issues": [
    {
      "id": "C1",
      "severity": "CRITICAL",
      "category": "Completeness",
      "title": "Issue title",
      "location": "Section 3.1",
      "description": "Detailed description",
      "impact": "Why this matters",
      "recommendation": "How to fix"
    }
  ],
  "missing_content": ["Item 1", "Item 2"],
  "structural_recommendations": ["Recommendation 1", "Recommendation 2"]
}
```

### 7. Report Results to User

After creating the file, provide a summary including:
- Overall assessment score
- Count of issues by severity
- Top 3 most critical findings
- File path where the assessment was saved
- The format used (Markdown or JSON)

## Assessment Guidelines

### Be Thorough But Fair
- Look for genuine issues, not nitpicks
- Acknowledge what the document does well
- Consider the document's stated scope and purpose
- Don't penalize for intentional omissions that are noted

### Be Specific and Actionable
- Point to exact locations of issues
- Provide concrete recommendations, not vague suggestions
- Include examples of how to improve where helpful

### Maintain Objectivity
- Assess against the document's own goals
- Don't impose external standards unless relevant
- Note assumptions you're making in the assessment

### Consider Context
- A draft has different expectations than a final document
- An internal doc differs from a public-facing one
- Technical docs differ from business docs

## Example Usage

### Markdown Format (default)

```text
User: /assess-document PRD.md

Claude: [Reads PRD.md, performs assessment, creates reports/assessment-PRD-20260110-143052.md]

I've completed the assessment of PRD.md.

Overall Score: 3.8/5

Issue Summary:
- CRITICAL: 2
- WARNING: 5
- SUGGESTION: 4

Top 3 Critical Findings:
1. Board roles are referenced but never defined (blocks implementation)
2. No LLM provider strategy specified (blocks technical architecture)
3. Privacy policy wording not provided (blocks compliance review)

Full assessment saved to: reports/assessment-PRD-20260110-143052.md (Markdown format)
```

### JSON Format

```text
User: /assess-document PRD.md --format json

Claude: [Reads PRD.md, performs assessment, creates reports/assessment-PRD-20260110-143052.json]

I've completed the assessment of PRD.md.

Overall Score: 3.8/5

Issue Summary:
- CRITICAL: 2
- WARNING: 5
- SUGGESTION: 4

Full assessment saved to: reports/assessment-PRD-20260110-143052.json (JSON format)
```

## Related Commands

- `/define-questions` — Extract open questions from the assessed document into a structured JSON
- `/finish-document` — Complete a document by resolving all questions and TBDs
- `/consolidate-documents` — Merge multiple document versions after assessment
- `/review-intent` — Compare document intent vs current implementation
- `/create-plan` — Generate an implementation plan from assessed requirements documents
