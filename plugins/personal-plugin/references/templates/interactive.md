<!-- ============================================================
     INTERACTIVE COMMAND TEMPLATE

     Canonical Section Order:
     1. Frontmatter (description, allowed-tools)
     2. Title (# Command Name)
     3. Brief description paragraph
     4. Input Validation
     5. Instructions
     6. Output Format (if applicable)
     7. Examples
     8. Performance (if applicable)

     Pattern References:
     - Workflow: references/patterns/workflow.md (session commands, resume)
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
- `--force` - Proceed even if validation fails (not recommended)

**Validation:**
If required arguments are missing, display:
```
Error: Missing required argument

Usage: /{{COMMAND_NAME}} <{{ARG_NAME}}> [--force]
Example: /{{COMMAND_NAME}} example-input.json

Arguments:
  <{{ARG_NAME}}>  {{ARG_DESCRIPTION}}
  --force         Proceed despite validation errors (not recommended)
```

See `references/patterns/validation.md` for error message format.

<!-- SECTION 5: INSTRUCTIONS -->
## Instructions

### 1. Load and Validate

- Read the specified input file
- Validate the format and required fields against schema
- Report the total number of items to process
- **Check for existing state file** (resume support)

See `references/patterns/validation.md` for schema validation behavior.

### 1.1 Resume Support

Before starting the session, check for an incomplete previous session:

1. Look for existing state files matching the input
2. If found with `status: "in_progress"`, offer resume options
3. On resume: Load existing state and continue
4. On start fresh: Backup existing file and start from item 1

See `references/patterns/workflow.md` for full state management specification.

### 2. Process Each Item ONE AT A TIME

**CRITICAL: Never batch items. Never skip ahead. Wait for user response before proceeding.**

For each item in sequential order:

#### A. Display Progress Header
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Item X of Y | Category: [Category Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### B. Present the Item with Context

Display:
- **Item:** The item text or content
- **Context:** Background information
- **What You're Solving:** Explain the purpose

#### C. Provide Options in Multiple-Choice Format

Always present options in this structure:

```
**[A] Recommended:** [Best answer]
    Why this is best: [Rationale]

**[B] Alternative:** [Viable alternative]
    Trade-off: [What you gain/lose]

**[C] Alternative:** [Another option if applicable]
    Trade-off: [What you gain/lose]

**[D] Custom:** Provide your own answer

**[S] Skip:** Skip this item for now

Your choice (A/B/C/D/S):
```

#### D. Wait for User Response

- Do not proceed until the user provides input
- Accept: A, B, C, D, S, or the full answer text
- If user selects D (Custom), prompt for their input
- If user selects S (Skip), mark as skipped and continue

#### E. Confirm and Record

- Briefly confirm the recorded response
- Proceed to the next item

### 3. Handle Session Commands

During the session, support these standard session commands:

| Command | Aliases | Action |
|---------|---------|--------|
| `help` | `?`, `commands` | Show available session commands |
| `status` | `progress` | Show answered/skipped/remaining summary |
| `back` | `previous`, `prev` | Return to previous item |
| `skip` | `next`, `pass` | Skip current item |
| `quit` | `exit`, `stop` | Save progress and exit |
| `go to [N]` | | Jump to item N |
| `save` | | Save current progress without exiting |

See `references/patterns/workflow.md` for session commands specification.

**Implementation notes:**
- Commands are case-insensitive
- Check for session commands before processing input as an answer choice
- Unknown input that is not A/B/C/D/S should trigger the help message

### 4. After All Items Are Processed

#### A. Handle Skipped Items

If any items were skipped:
```
You skipped X items. Would you like to:
[A] Process them now
[B] Leave them unprocessed
[C] Review the list first
```

#### B. Generate Output

Save results to a file with this naming: `{{OUTPUT_PREFIX}}-[source]-YYYYMMDD-HHMMSS.{{OUTPUT_EXT}}`

See `references/patterns/naming.md` for naming conventions.

#### C. Display Completion Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Items: X
- Completed: X (X%)
- Skipped: X (X%)

Saved to: [filename]
```

See `references/patterns/output.md` for completion summary format.

<!-- SECTION 6: OUTPUT FORMAT (if applicable) -->
## Output Format

**File Naming:** `{{OUTPUT_PREFIX}}-[source]-YYYYMMDD-HHMMSS.{{OUTPUT_EXT}}`

**Schema:** Output must conform to the {{SCHEMA_NAME}} schema (see inline validation rules)

<!-- SECTION 7: EXAMPLES -->
## Examples

```
User: /{{COMMAND_NAME}} input.json

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Item 1 of 10 | Category: Example
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Item:** [Example item text]

**Context:** [Example context]

**What You're Solving:** [Example purpose]

---

**[A] Recommended:** [Example recommendation]
    Why this is best: [Rationale]

**[B] Alternative:** [Example alternative]
    Trade-off: [Trade-off description]

**[D] Custom:** Provide your own answer

**[S] Skip:** Skip this item for now

Your choice (A/B/C/D/S):
```

User types: `A`

```
Recorded: [Selected option]

Proceeding to item 2...
```

## Key Requirements

1. **ONE AT A TIME** - This is critical. Never show multiple items at once.
2. **Always wait for input** - Do not auto-advance or assume responses.
3. **Specific options** - Generic answers are not acceptable.
4. **Maintain state** - Track progress so users can pause and resume.
5. **Conversational tone** - Be helpful and encouraging.
6. **Respect user choice** - Don't push back on their selections.
