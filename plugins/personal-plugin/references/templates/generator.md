<!-- ============================================================
     GENERATOR COMMAND TEMPLATE

     Canonical Section Order (per schemas/command.json):
     1. Frontmatter (description, allowed-tools)
     2. Title (# Command Name)
     3. Brief description paragraph
     4. Input Validation
     5. Instructions
     6. Output Format (required for generators)
     7. Examples
     8. Performance (if applicable)

     Pattern References:
     - Naming: references/patterns/naming.md
     - Validation: references/patterns/validation.md
     - Output: references/patterns/output.md
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
- `<{{ARG_NAME}}>` - {{ARG_DESCRIPTION}}

**Optional Arguments:**
- `--preview` - Show summary and ask for confirmation before saving
- `--force` - Save output even if schema validation fails (not recommended)

**Validation:**
If required arguments are missing, display:
```
Error: Missing required argument

Usage: /{{COMMAND_NAME}} <{{ARG_NAME}}> [--preview] [--force]
Example: /{{COMMAND_NAME}} input.md
Example: /{{COMMAND_NAME}} docs/example.md

Arguments:
  <{{ARG_NAME}}>  {{ARG_DESCRIPTION}}
  --preview       Preview output before saving
  --force         Save despite validation errors (not recommended)
```

See `references/patterns/validation.md` for error message format.

<!-- SECTION 5: INSTRUCTIONS -->
## Instructions

1. **Read the specified input** - The user will provide a path after the slash command. Read and analyze that input thoroughly.

2. **Ensure output directory exists** - Before writing any output:
   ```bash
   mkdir -p {{OUTPUT_LOCATION}}
   ```
   See `references/patterns/output.md` for directory auto-creation pattern.

3. **Process the content** - Look for:
   - [Item type 1]
   - [Item type 2]
   - [Item type 3]
   - [Item type 4]

4. **Create output file** with the following structure:

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

5. **Assign sequential IDs** starting from 1 for each item.

6. **Categorize appropriately** - Group related items under logical categories.

7. **Provide rich context** - For each item, include enough context for downstream use.

8. **Handle preview mode** - If `--preview` specified:
   - Generate output in memory
   - Validate against schema
   - Display summary with confirmation prompt
   - Only save on explicit 'y' or 'yes'

   See `references/patterns/output.md` for preview pattern.

9. **Validate and save the output** - Validate against schema, then write to file.
   See `references/patterns/validation.md` for schema validation behavior.

10. **Report the results** - After creating the file, provide a summary including:
    - Total number of items identified
    - Breakdown by category
    - The file path where output was saved
    - Validation status

<!-- SECTION 6: OUTPUT FORMAT -->
## Output Format

**File Naming:** `{{OUTPUT_PREFIX}}-[source]-YYYYMMDD-HHMMSS.{{OUTPUT_EXT}}`

See `references/patterns/naming.md` for naming conventions.

**Location:** `{{OUTPUT_LOCATION}}`

Example: `{{OUTPUT_PREFIX}}-document-20260114-143052.{{OUTPUT_EXT}}`

**Schema:** Output must conform to `schemas/{{SCHEMA_NAME}}.json`

### Validation Success Message

```
Output validated against schemas/{{SCHEMA_NAME}}.json. Saved to {{OUTPUT_LOCATION}}/{{OUTPUT_PREFIX}}-document-20260114-143052.{{OUTPUT_EXT}}

Validation: PASSED
- Required fields: All present
- Field types: All correct
- Total items: X
```

### Validation Error Message

```
Schema validation failed:

Errors:
  - items[3].id: Required field missing
  - metadata.generated_at: Invalid date-time format

Fix these issues or use --force to save anyway (not recommended).
```

<!-- SECTION 7: EXAMPLES -->
## Examples

### Basic Usage

```
User: /{{COMMAND_NAME}} document.md

Claude: Analyzing document.md...

Found X items across Y categories.

**Summary:**
- Category 1: X items
- Category 2: Y items
- Category 3: Z items

Output validated against schemas/{{SCHEMA_NAME}}.json. Saved to {{OUTPUT_LOCATION}}/{{OUTPUT_PREFIX}}-document-20260114-143052.{{OUTPUT_EXT}}
```

### Preview Mode

```
User: /{{COMMAND_NAME}} document.md --preview

Claude:
Preview: /{{COMMAND_NAME}}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: document.md
Items found: 15

By category:
  Category 1: 5
  Category 2: 3
  Category 3: 7

Schema validation: PASSED
Output file: {{OUTPUT_PREFIX}}-document-20260114-143052.{{OUTPUT_EXT}}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Save this file? (y/n):
```

## Important Notes

- Be thorough - it's better to capture more items than to miss important ones
- Items should be actionable and specific
- Avoid duplicates - consolidate similar items
- Preserve original intent - don't rephrase in ways that change meaning
- Output must be valid and properly formatted for downstream use
