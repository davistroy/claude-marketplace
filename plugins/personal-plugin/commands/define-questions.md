---
description: Extract questions and open items from documents to JSON
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Define Questions Command

Analyze the document specified by the user and extract all questions, open items, areas needing clarification, and incomplete sections into a comprehensive, downloadable JSON file.

## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document to analyze

**Optional Arguments:**
- `--format [json|csv]` - Output format (default: json)
  - `json`: Structured format with metadata (default, compatible with `/ask-questions`)
  - `csv`: Flat tabular format with columns: id, text, context, topic, sections, priority
- `--preview` - Show summary and ask for confirmation before saving (see `references/patterns/output.md`)
- `--force` - Save output even if schema validation fails (not recommended)
- `--no-prompt` - Disable interactive prompting for missing arguments (for scripts and CI/CD)

**Validation:**
If the document path is missing:

1. **If `--no-prompt` is specified**, display the error and exit:
```text
Error: Missing required argument

Usage: /define-questions <document-path> [--format json|csv] [--no-prompt]
Example: /define-questions PRD.md
Example: /define-questions docs/requirements.md
Example: /define-questions PRD.md --format csv
```

2. **Otherwise (default), prompt interactively**:
```text
/define-questions requires a document path.

Please provide the path to the document to analyze:
> _

(or use --no-prompt to disable interactive prompting)
```

Wait for the user to provide the document path, then proceed with analysis.

## Instructions

1. **Read the specified document** - The user will provide a document path or name after the `/define-questions` command (e.g., `/define-questions PRD.md`). Read and analyze that document thoroughly.

2. **Identify all questions and open items** - Look for:
   - Explicit questions (sentences ending with `?`)
   - Open items marked with "TBD", "TODO", "TBC", or similar markers
   - Incomplete sections or placeholders
   - Areas marked as needing review or decision
   - Gaps in specifications or requirements
   - Ambiguous or vague statements that need clarification
   - Missing details that would be needed for implementation
   - Dependencies or prerequisites that are undefined
   - Edge cases or scenarios not addressed

3. **Create a JSON file** with the following structure for each question/open item:

```json
{
  "questions": [
    {
      "id": 1,
      "topic": "Best guess at the topic area (e.g., 'User Authentication', 'Data Model', 'Integration')",
      "sections": ["Section name or header where this question is relevant"],
      "question": "The actual question or open item that needs clarification",
      "context": "Any relevant information, background, or details needed to understand and properly answer this question"
    }
  ],
  "metadata": {
    "source_document": "Name of the analyzed document",
    "total_questions": 0,
    "generated_date": "ISO date string",
    "topics_summary": ["List of unique topics identified"]
  }
}
```

4. **Assign sequential IDs** starting from 1 for each question.

5. **Categorize by topic** - Group related questions under logical topic areas based on the content (e.g., "Technical Architecture", "User Experience", "Business Logic", "Data Management", "Integration", "Security", "Performance", etc.).

6. **Reference relevant sections** - For each question, note which section(s) of the document it relates to. Use the exact section headers/titles from the document.

7. **Provide rich context** - For each question, include enough context so that someone unfamiliar with the document could understand:
   - Why this question matters
   - What information is currently available
   - What specific details are missing or unclear
   - Any constraints or requirements that affect the answer

8. **Save the output** - Based on the `--format` flag:

   **Directory Creation:**
   Before writing any output file, ensure the target directory exists:

   ```bash
   # Ensure output directory exists before writing
   mkdir -p reference/
   ```

   **JSON Format (default):**
   - Write the JSON file to `reference/questions-[document-name]-[timestamp].json`
   - Use a timestamp format like `YYYYMMDD-HHMMSS`

   **CSV Format:**
   - Write the CSV file to `reference/questions-[document-name]-[timestamp].csv`
   - Include header row: `id,text,context,topic,sections,priority`
   - Escape commas and quotes properly in field values
   - Use semicolons to separate multiple sections within the sections field

9. **Report the results** - After creating the file, provide a summary to the user including:
   - Total number of questions identified
   - Breakdown by topic area
   - The file path where the output was saved
   - The format used (JSON or CSV)

10. **Preview mode** - When `--preview` is specified:
    - Generate the output in memory
    - Validate against schema
    - Display summary:
      ```
      Preview: /define-questions
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Source: PRD.md
      Questions found: 15

      By topic:
        Technical Architecture: 5
        User Experience: 3
        Data Model: 7

      Schema validation: PASSED
      Output file: questions-PRD-20260114-143052.json
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      Save this file? (y/n):
      ```
    - Wait for user confirmation before saving
    - On 'n' or 'no': Exit without saving

## Example Output

### JSON Format (default)

```json
{
  "questions": [
    {
      "id": 1,
      "topic": "Board Role Definitions",
      "sections": ["3.1 AI Board Members", "4.2 Governance Sessions"],
      "question": "What specific expertise and personality traits should each of the 5 AI board member roles embody?",
      "context": "The PRD mentions a 5-role AI board for career governance but does not define the specific roles, their areas of expertise, how they should interact with each other, or their individual decision-making styles. This is critical for implementing the governance session logic and ensuring diverse perspectives."
    },
    {
      "id": 2,
      "topic": "LLM Integration",
      "sections": ["5.1 Technical Architecture"],
      "question": "Which LLM provider(s) will be used for the AI board members and transcription services?",
      "context": "The document references LLM services for voice transcription and AI board member responses but does not specify whether to use OpenAI, Anthropic, or other providers. This affects API integration, cost modeling, and capability constraints."
    }
  ],
  "metadata": {
    "source_document": "PRD.md",
    "total_questions": 2,
    "generated_date": "2026-01-10T14:30:00Z",
    "topics_summary": ["Board Role Definitions", "LLM Integration"]
  }
}
```

### CSV Format

```csv
id,text,context,topic,sections,priority
1,"What specific expertise and personality traits should each of the 5 AI board member roles embody?","The PRD mentions a 5-role AI board for career governance but does not define the specific roles, their areas of expertise, how they should interact with each other, or their individual decision-making styles.",Board Role Definitions,"3.1 AI Board Members;4.2 Governance Sessions",high
2,"Which LLM provider(s) will be used for the AI board members and transcription services?","The document references LLM services for voice transcription and AI board member responses but does not specify whether to use OpenAI, Anthropic, or other providers.",LLM Integration,5.1 Technical Architecture,high
```

## Output Schema

The output JSON must conform to the schema defined in `schemas/questions.json`.

**Schema Location:** `schemas/questions.json`

### Schema Validation Behavior

Before saving the output file, validate against `schemas/questions.json`:

1. **Generate output in memory** - Create the complete JSON structure
2. **Validate against schema** - Check all required fields and types
3. **If valid:** Save file and report success with validation status
4. **If invalid:** Report specific validation errors
5. **If `--force` provided:** Save anyway with a warning

**Required fields (metadata):**
- `metadata.source_document` - Source document path
- `metadata.generated_at` - ISO 8601 timestamp
- `metadata.total_questions` - Integer count

**Required fields (per question):**
- `id` - Unique identifier (string or integer)
- `text` or `question` - The question text
- `context` - Background information

**Optional fields:**
- `topic`, `category`, `sections`, `priority`, `location`

### Validation Success Message

After successful validation, display:
```text
Output validated against schemas/questions.json. Saved to questions-PRD-20260114-143052.json

Validation: PASSED
- Required fields: All present
- Field types: All correct
- Total questions: 15
```

### Validation Error Message

If validation fails and `--force` is not provided:
```text
Schema validation failed:

Errors:
  - questions[3].id: Required field missing
  - questions[7].priority: Must be one of: high, medium, low
  - metadata.generated_at: Invalid date-time format

Fix these issues or use --force to save anyway (not recommended).
```

If `--force` is provided, save the file with a warning:
```text
WARNING: Schema validation failed but --force was specified.
Output saved to questions-PRD-20260114-143052.json

This file may not work correctly with /ask-questions or /finish-document.
```

See `schemas/README.md` for validation instructions and tools.

## Important Notes

- Be thorough - it's better to capture more questions than to miss important ones
- Questions should be actionable - they should be answerable with specific decisions or information
- Avoid duplicate questions - consolidate similar questions into one with comprehensive context
- Preserve the original intent - don't rephrase questions in ways that change their meaning
- The JSON must be valid and properly formatted for downstream use with AI tools
- Output must conform to `schemas/questions.json` for compatibility with `/ask-questions` and `/finish-document`

## Schema Validation Summary

This command validates output against `schemas/questions.json`. See `references/patterns/validation.md` for full validation behavior.

| Flag | Behavior |
|------|----------|
| (default) | Validate output, fail if invalid, show specific errors |
| `--force` | Save output despite validation errors (with warning) |
| `--preview` | Show validation status before save confirmation |

**Validation Status in Output:**
All command completions include validation status:
- `Validation: PASSED` - All required fields present, types correct
- `Validation: FAILED` - Errors listed, file not saved (unless `--force`)
- `Validation: SKIPPED` - Used with `--force`, file saved with warning
