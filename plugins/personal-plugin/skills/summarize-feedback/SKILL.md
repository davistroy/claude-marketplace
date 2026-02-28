---
name: summarize-feedback
description: Synthesize employee feedback from Notion Voice Captures into a professional .docx assessment document
allowed-tools: Read, Glob, Grep, Write
---

You are generating a professional employee feedback assessment document. You will query Notion for feedback entries, synthesize them with Claude, and produce a formatted `.docx` file. The user may provide arguments: $ARGUMENTS

## Input Validation

**Required Arguments:**
- `employee_name="..."` - Employee name to match against the "Related To" property in Notion (partial matches supported)

**Optional Arguments:**
- `days=N` - Lookback period in days (default: 365, max: 1095)
- `start_date=YYYY-MM-DD` - Override start date (ISO 8601)
- `end_date=YYYY-MM-DD` - Override end date (ISO 8601)
- `output_path="..."` - Custom output file path (default: `./output/Feedback_Summary_{Name}_{datetime}.docx`)

If no `employee_name` is provided, ask the user for it before proceeding.

## Prerequisites Check

Before starting, verify all prerequisites:

### 1. Notion MCP Server
Verify the Notion MCP tools are available (`mcp__plugin_Notion_notion__notion-search`, `mcp__plugin_Notion_notion__notion-fetch`). If not connected:
```text
Notion MCP is not connected. Please verify:
1. Notion MCP is configured in your Claude settings
2. The MCP server is running and connected
3. Your Notion API key has access to the Voice Captures database
```

### 2. python-docx Package
```bash
python -c "import docx; print('python-docx: OK')" 2>/dev/null || echo "python-docx: MISSING"
```
If missing, ask the user to install: `pip install python-docx>=1.0`

## Step 1: Compute Date Range

Calculate the assessment period:
- If `start_date` and `end_date` are provided, use those
- Otherwise: `end_date` = today, `start_date` = today minus `days` parameter (default 365)

Display: `Assessment period: {start_date} to {end_date}`

## Step 2: Query Notion for Feedback Entries

Use the Notion MCP tools to search for feedback entries:

1. Use `mcp__plugin_Notion_notion__notion-search` to find pages in the Voice Captures database
2. Filter results where:
   - **Type** property equals "Feedback"
   - **Related To** property contains the `employee_name` (case-insensitive partial match)
   - **Date** property falls within the computed date range

If no entries are found:
```text
No Feedback entries found for "{employee_name}" in the period {start_date} to {end_date}.

Possible causes:
1. No feedback has been captured for this employee
2. The employee name doesn't match the "Related To" property in Notion
   (check for exact spelling, try first name only)
3. The date range is too narrow - try increasing the days parameter

Would you like to:
1. Try a different name or spelling?
2. Expand the date range?
3. List all employees with Feedback entries?
```

## Step 3: Fetch Full Page Content

For each matching entry, use `mcp__plugin_Notion_notion__notion-fetch` to retrieve the full page content.

Parse the Markdown body to extract:
- **Summary** (from `## Summary` section) - includes Feedback Type (Positive/Constructive/Observation)
- **Context** (from `## Context` section, if present)
- **Actionable Items** (from `## Actionable Items` section, if present)
- **Raw Transcript** (from `## Raw Transcript` section)

Also capture page properties: Title, Date, Tags, Related To.

Display progress: `Fetched {N} of {total} entries...`

## Step 4: Synthesize Assessment

Feed all structured feedback entries to Claude using the following synthesis prompt. Produce the output as structured JSON.

### Synthesis Prompt

```text
You are analyzing employee feedback entries to produce a structured performance assessment.

## Employee
{employee_name}

## Assessment Period
{start_date} to {end_date}

## Feedback Entries
{formatted_entries}

## Instructions

Analyze ALL feedback entries above and produce a structured JSON assessment.
Be specific - cite dates and actual observations from the entries. Do not
fabricate evidence. If there are only a few entries, note the limited sample
size in the executive summary.

The assessment should be balanced and evidence-based. Every strength and area
for development MUST be supported by specific entries with dates.

## Output Format

Return ONLY valid JSON matching this structure:

{
  "executive_summary": "3-5 sentence overall assessment. Note total feedback entries and trajectory (improving, consistent, declining, mixed).",
  "strengths": [
    {
      "name": "Short strength name (2-4 words)",
      "description": "1-2 sentence description of the strength and its impact.",
      "evidence": [
        {
          "date": "YYYY-MM-DD",
          "summary": "Brief reference to the specific feedback entry supporting this strength."
        }
      ],
      "frequency": "Consistent|Frequent|Occasional|Emerging"
    }
  ],
  "areas_for_development": [
    {
      "name": "Short area name (2-4 words)",
      "description": "1-2 sentence description of the development area and why it matters.",
      "evidence": [
        {
          "date": "YYYY-MM-DD",
          "summary": "Brief reference to the specific feedback entry supporting this area."
        }
      ],
      "pattern": "Recurring|Occasional|Situational|Improving"
    }
  ],
  "patterns_and_themes": {
    "trends": "Description of how performance has trended over the assessment period.",
    "relationships": "Connections between different feedback observations.",
    "situational": "Contexts or situations where performance notably varies."
  },
  "recommendations": [
    {
      "type": "Continue|Develop|Stretch",
      "recommendation": "Specific, actionable recommendation.",
      "rationale": "Why this recommendation is important based on the evidence."
    }
  ]
}

## Recommendation Types
- **Continue**: Behaviors and skills to maintain and reinforce
- **Develop**: Areas needing improvement with specific development actions
- **Stretch**: Growth opportunities that build on existing strengths
```

Format each entry for the prompt as:
```text
### Entry: {title}
- Date: {date}
- Feedback Type: {type}
- Summary: {summary}
- Context: {context}
- Actionable Items: {actionable_items}
- Transcript: {raw_transcript}
```

## Step 5: Generate .docx Document

Build a combined JSON payload with this structure:
```json
{
  "employee_name": "...",
  "assessment_period": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "generation_date": "YYYY-MM-DD",
  "total_entries": N,
  "synthesis": { ... },
  "entries": [ ... ]
}
```

Write the JSON to a temp file in the scratchpad directory.

Determine the output path:
- Use `output_path` parameter if provided
- Otherwise: `./output/Feedback_Summary_{Employee_Name}_{YYYY-MM-DD_HHMMSS}.docx`
  - Replace spaces in employee name with underscores

Run the document generator:
```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(find ~ -path '*/plugins/personal-plugin' -type d 2>/dev/null | head -1)}"
TOOL_SRC="$PLUGIN_DIR/tools/feedback-docx-generator/src"
PYTHONPATH="$TOOL_SRC" python -m feedback_docx_generator --input {temp_json_path} --output {output_path}
```

If the script fails, show the error and suggest running it directly for debugging.

## Step 6: Report Results

Display a summary:
```yaml
Feedback Assessment Generated
==============================
Employee:    {employee_name}
Period:      {start_date} to {end_date}
Entries:     {total_entries} feedback entries analyzed
Output:      {output_path}

Document sections:
  1. Executive Summary
  2. Strengths ({N} identified)
  3. Areas for Development ({N} identified)
  4. Patterns and Themes
  5. Recommendations ({N} total)
  6. Appendix: Individual Entries
```

## Error Handling

| Error | Action |
|-------|--------|
| No employee_name provided | Ask user for the name |
| Notion MCP not connected | Abort with configuration instructions |
| No entries found | Offer to retry with different name/date range |
| python-docx missing | Abort with install instruction |
| Synthesis fails | Show error, offer to retry |
| .docx generation fails | Show error, suggest running script directly |
