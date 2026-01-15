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
Example: /{{COMMAND_NAME}} example-input.json
```

## Instructions

### 1. Load and Validate

- Read the specified input file
- Validate the format and required fields
- Report the total number of items to process

### 2. Process Each Item ONE AT A TIME

**CRITICAL: Never batch items. Never skip ahead. Wait for user response before proceeding.**

For each item in sequential order:

#### A. Display Progress Header
```
----------------------------------------------
Item X of Y | Category: [Category Name]
----------------------------------------------
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

### 3. Handle Special Commands

During the session, support these commands:
- `back` or `previous` - Return to the previous item
- `go to [N]` - Jump to item N
- `skip` - Skip current item
- `progress` - Show summary of completed/skipped/remaining
- `save` - Save current progress
- `quit` - Save progress and exit

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

#### C. Display Completion Summary

```
----------------------------------------------
Session Complete!
----------------------------------------------

Total Items: X
- Completed: X (X%)
- Skipped: X (X%)

Saved to: [filename]
```

## Key Requirements

1. **ONE AT A TIME** - This is critical. Never show multiple items at once.
2. **Always wait for input** - Do not auto-advance or assume responses.
3. **Specific options** - Generic answers are not acceptable.
4. **Maintain state** - Track progress so users can pause and resume.
5. **Conversational tone** - Be helpful and encouraging.
6. **Respect user choice** - Don't push back on their selections.

## Example Interaction

```
User: /{{COMMAND_NAME}} input.json

Claude:
----------------------------------------------
Item 1 of 10 | Category: Example
----------------------------------------------

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
