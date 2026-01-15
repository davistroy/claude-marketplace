---
description: {{DESCRIPTION}}
---

# {{TITLE}}

{{INTRO_PARAGRAPH}}

## Input Validation

**Required Arguments:**
- `<{{ARG_NAME}}>` - {{ARG_DESCRIPTION}}

**Validation:**
If required arguments are missing, display:
```
Usage: /{{COMMAND_NAME}} <{{ARG_NAME}}>
Example: /{{COMMAND_NAME}} input.md
Example: /{{COMMAND_NAME}} docs/example.md
```

## Instructions

1. **Read the specified input** - The user will provide a path after the slash command. Read and analyze that input thoroughly.

2. **Process the content** - Look for:
   - [Item type 1]
   - [Item type 2]
   - [Item type 3]
   - [Item type 4]

3. **Create output file** with the following structure:

```json
{
  "items": [
    {
      "id": 1,
      "field1": "value1",
      "field2": "value2",
      "field3": "value3"
    }
  ],
  "metadata": {
    "source_document": "Name of the analyzed document",
    "total_items": 0,
    "generated_date": "ISO date string"
  }
}
```

4. **Assign sequential IDs** starting from 1 for each item.

5. **Categorize appropriately** - Group related items under logical categories.

6. **Provide rich context** - For each item, include enough context for downstream use.

7. **Save the output** - Write the file to the appropriate location following naming conventions.

8. **Report the results** - After creating the file, provide a summary including:
   - Total number of items identified
   - Breakdown by category
   - The file path where output was saved

## Output

**File Naming:** `{{OUTPUT_PREFIX}}-[source]-YYYYMMDD-HHMMSS.{{OUTPUT_EXT}}`

**Location:** `{{OUTPUT_LOCATION}}`

Example: `{{OUTPUT_PREFIX}}-document-20260114-143052.{{OUTPUT_EXT}}`

## Example Output

```json
{
  "items": [
    {
      "id": 1,
      "field1": "Example value",
      "field2": "Example category",
      "field3": "Example context"
    }
  ],
  "metadata": {
    "source_document": "example.md",
    "total_items": 1,
    "generated_date": "2026-01-14T14:30:00Z"
  }
}
```

## Example Usage

```
User: /{{COMMAND_NAME}} document.md

Claude: Analyzing document.md...

Found X items across Y categories.

**Summary:**
- Category 1: X items
- Category 2: Y items
- Category 3: Z items

Output saved to: {{OUTPUT_LOCATION}}/{{OUTPUT_PREFIX}}-document-20260114-143052.{{OUTPUT_EXT}}
```

## Important Notes

- Be thorough - it's better to capture more items than to miss important ones
- Items should be actionable and specific
- Avoid duplicates - consolidate similar items
- Preserve original intent - don't rephrase in ways that change meaning
- Output must be valid and properly formatted for downstream use
