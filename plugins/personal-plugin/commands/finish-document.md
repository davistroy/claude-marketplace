---
description: Extract questions from a document, answer them interactively, and update the document
---

# Finish Document

Complete an incomplete document by extracting all questions/TBDs, walking through them interactively, and updating the document with the resolved answers.

## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document to complete

**Optional Arguments:**
- `--auto` - Auto-select recommended answers instead of interactive Q&A (user can still override)
- `--force` - Proceed even if schema validation fails for intermediate files (not recommended)

**Validation:**
If the document path is missing, display:
```
Usage: /finish-document <document-path> [--auto] [--force]
Example: /finish-document PRD.md
Example: /finish-document docs/requirements.md --auto
```

## Input

The user will provide a document path after the command (e.g., `/finish-document PRD.md`).

Optional flags:
- `--auto` — Auto-select recommended answers instead of interactive Q&A (user can still override)

## Workflow Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Extract     │────▶│  2. Answer      │────▶│  3. Update      │
│     Questions   │     │     Questions   │     │     Document    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   questions.json          answers.json          backup + updated
   (in reference/)         (in reference/)       original document
```

## Phase 1: Setup and Question Extraction

### 1.1 Validate Input
- Confirm the specified document exists
- Read and parse the document
- Create `reference/` folder if it doesn't exist

### 1.2 Extract Questions
Execute the logic from `/define-questions`:

- Identify all questions and open items:
  - Explicit questions (sentences ending with `?`)
  - Open items marked with "TBD", "TODO", "TBC", or similar markers
  - Incomplete sections or placeholders
  - Areas marked as needing review or decision
  - Gaps in specifications or requirements
  - Ambiguous or vague statements that need clarification
  - Missing details needed for implementation
  - Dependencies or prerequisites that are undefined
  - Edge cases or scenarios not addressed

- Create JSON conforming to `schemas/questions.json`:
```json
{
  "questions": [
    {
      "id": 1,
      "topic": "Topic area",
      "sections": ["Section name"],
      "question": "The question or open item",
      "context": "Relevant background",
      "location": {
        "line_start": 45,
        "line_end": 45,
        "original_text": "The original text containing the TBD/question"
      }
    }
  ],
  "metadata": {
    "source_document": "document.md",
    "total_questions": 0,
    "generated_date": "ISO date",
    "topics_summary": ["List of topics"]
  }
}
```

**Schema:** Output must conform to `schemas/questions.json`

**Important:** Capture `location` data for each question — this enables precise document updates later.

### 1.3 Save Questions File
Save to: `reference/questions-[document-name]-[timestamp].json`

#### Questions Validation Behavior

Before saving the questions file:

1. **Generate output in memory** - Create the complete JSON structure
2. **Validate against `schemas/questions.json`**
3. **If valid:** Save file and proceed to Q&A session
4. **If invalid:** Report specific validation errors
5. **If `--force` provided:** Save anyway with a warning

**Validation Error Message:**
```
Schema validation failed for questions file:

Errors:
  - questions[3].id: Required field missing
  - metadata.generated_at: Invalid date-time format

Fix these issues or use --force to save anyway (not recommended).
```

### 1.4 Report to User
```
Found [X] questions/open items in [document]:

By topic:
- Technical Architecture: 5 questions
- User Experience: 3 questions
- Data Model: 7 questions

Questions saved to: reference/questions-PRD-20260111-143052.json

Ready to begin Q&A session. Type 'start' to proceed or 'preview' to see all questions first.
```

Wait for user confirmation before proceeding.

## Phase 2: Interactive Q&A Session

Execute the logic from `/ask-questions`:

### 2.0 Resume Support

Before starting the Q&A session, check for an incomplete previous session:

1. Look for existing `reference/answers-[document-name]-*.json` files
2. If found with `metadata.status: "in_progress"`:
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Incomplete session detected
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Previous session: reference/answers-PRD-20260114-100000.json
   Progress: 15 of 47 questions answered (32%)
   Last activity: 2026-01-14T10:45:00Z

   Options:
   [R] Resume from question 16
   [S] Start fresh (overwrites previous progress)
   [A] Abort

   Your choice (R/S/A):
   ```
3. On resume: Load existing answers and continue from `last_question_answered + 1`
4. On start fresh: Backup existing file and start from question 1

See `references/patterns/workflow.md` for full state management specification.

### 2.1 Question Flow

For each question, present:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Question 3 of 15 | Topic: [Topic Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Question:** [The question text]

**Location:** Line [X] in section "[Section Name]"
**Original text:** "[The TBD or question as it appears in the document]"

**Context:** [Background from the JSON]

**What You're Solving:** [Inferred goal]

---

**[A] Recommended:** [Best answer]
    Why: [Rationale]

**[B] Alternative:** [Other option]
    Trade-off: [What changes]

**[C] Alternative:** [Another option if applicable]
    Trade-off: [What changes]

**[D] Custom:** Provide your own answer

**[S] Skip:** Skip for now

Your choice (A/B/C/D/S):
```

### 2.2 Auto Mode Behavior
If `--auto` flag was provided:
- Auto-select option A (Recommended) for each question
- Show what was selected but don't wait for input
- User can interrupt with `pause` to switch to interactive mode

### 2.3 Session Commands

Support these standard session commands during Q&A (see `references/patterns/workflow.md` for full specification):

| Command | Aliases | Action |
|---------|---------|--------|
| `help` | `?`, `commands` | Show available session commands |
| `status` | `progress` | Show answered/skipped/remaining summary |
| `back` | `previous`, `prev` | Return to previous question |
| `skip` | `next`, `pass` | Skip current question |
| `quit` | `exit`, `stop` | Save progress and exit |
| `go to [N]` | | Jump to question N |
| `save` | | Save current progress without exiting |
| `pause` | | (Auto mode) Switch to interactive |
| `auto` | | (Interactive mode) Switch to auto for remaining |

**When user types `help`:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session Commands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  help      Show this help message
  status    Show current progress (X of Y completed)
  back      Return to previous question
  skip      Skip current question (can return later)
  quit      Exit session (progress will be saved)

Additional commands:
  go to N   Jump to question number N
  save      Save progress without exiting
  pause     Switch from auto to interactive mode
  auto      Switch to auto mode for remaining questions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Implementation notes:**
- Commands are case-insensitive
- Check for session commands before processing input as an answer choice
- Unknown input that is not A/B/C/D/S should trigger the help message

### 2.4 Save Answers
After all questions are answered (or skipped), save to:
`reference/answers-[document-name]-[timestamp].json`

**Schema:** Output must conform to `schemas/answers.json`

#### Output Validation Behavior

Before saving the answers file:

1. **Generate output in memory** - Create the complete JSON structure
2. **Validate against `schemas/answers.json`**
3. **If valid:** Save file and proceed to Phase 3
4. **If invalid:** Report specific validation errors
5. **If `--force` provided:** Save anyway with a warning

**Validation Error Message:**
```
Schema validation failed for answers file:

Errors:
  - answers[5].selected_answer: Required field missing
  - metadata.total_questions: Must be an integer

Fix these issues or use --force to save anyway (not recommended).
```

**Validation Warning (with --force):**
```
WARNING: Output validation failed but --force was specified.
Answers saved to reference/answers-PRD-20260114-150030.json

Proceeding with document update. Some answers may not apply correctly.
```

Structure:
```json
{
  "answers": [
    {
      "id": 1,
      "question": "Original question",
      "location": {
        "line_start": 45,
        "line_end": 45,
        "original_text": "TBD: Define the authentication method"
      },
      "selected_answer": "Use OAuth 2.0 with JWT tokens",
      "answer_type": "recommended | alternative | custom | skipped"
    }
  ],
  "metadata": {
    "source_document": "PRD.md",
    "questions_file": "reference/questions-PRD-20260111-143052.json",
    "total_questions": 15,
    "answered": 14,
    "skipped": 1,
    "completed_at": "ISO date"
  }
}
```

## Phase 3: Document Update

### 3.1 Create Backup
Before any modifications:
1. Copy original document to backup: `[name].backup-[timestamp].md`
2. Confirm backup was created successfully

Example: `PRD.md` → `PRD.backup-20260111-150000.md`

### 3.2 Apply Updates
For each answered question (not skipped):

**For TBD/TODO markers:**
- Find the original text using `location` data
- Replace the TBD/placeholder with the answer
- Preserve surrounding formatting

Example:
```markdown
# Before
Authentication method: TBD

# After
Authentication method: OAuth 2.0 with JWT tokens for stateless session management
```

**For questions in the text:**
- Replace the question with a statement incorporating the answer
- Or add the answer immediately after the question

**For gaps/missing sections:**
- Add new content at the appropriate location
- Use document's existing style and formatting

### 3.3 Add Resolution Summary
At the end of the document (or in a dedicated section), optionally add:

```markdown
---

## Document Resolution Log

*This document was completed on [date] using `/finish-document`.*

**Questions Resolved:** 14 of 15
**Reference Files:**
- Questions: `reference/questions-PRD-20260111-143052.json`
- Answers: `reference/answers-PRD-20260111-150030.json`
- Original backup: `PRD.backup-20260111-150000.md`
```

Ask user if they want this summary included.

### 3.4 Save Updated Document
Save to the original filename (e.g., `PRD.md`).

### 3.5 Handle Skipped Questions
If any questions were skipped:
- Leave original TBD/question text in place
- Optionally mark with a comment: `<!-- UNRESOLVED: [question] -->`
- Report skipped items in final summary

## Final Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Document Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Document:** PRD.md (updated)
**Backup:** PRD.backup-20260111-150000.md

**Questions Resolved:** 14 of 15
- Recommended answers: 10
- Alternative answers: 2
- Custom answers: 2
- Skipped: 1

**Reference Files:**
- reference/questions-PRD-20260111-143052.json
- reference/answers-PRD-20260111-150030.json

**Skipped Questions:**
- Q7: "What is the data retention policy?" (Section: Compliance)

You can re-run `/finish-document PRD.md` to address skipped questions.
```

## Error Handling

- **Document not found:** Report error and exit
- **No questions found:** Report that document appears complete, offer to do a deeper analysis
- **Backup failed:** Abort before making changes
- **Parse error:** Report location and skip that update, continue with others
- **User quits mid-session:** Save progress, allow resume with `--resume` flag

## Safety Rules

1. **Always backup first** — Never modify original without successful backup
2. **Preserve formatting** — Match the document's existing style
3. **Don't lose content** — If unsure where to place an answer, append rather than replace
4. **Keep references** — Never delete the questions/answers JSON files automatically
5. **Atomic updates** — If document update fails partway, restore from backup

## Schema Validation Summary

This command validates intermediate files at each phase. See `references/patterns/validation.md` for full validation behavior.

| Phase | Output | Schema |
|-------|--------|--------|
| 1 (Extract) | `questions-*.json` | `schemas/questions.json` |
| 2 (Answer) | `answers-*.json` | `schemas/answers.json` |

| Flag | Behavior |
|------|----------|
| (default) | Validate at each phase, fail if invalid, show specific errors |
| `--force` | Proceed/save despite validation errors (with warning) |
| `--auto` | Auto-select recommended answers (validation still applies) |

**Validation Status in Output:**
All phase completions include validation status:
- `Validation: PASSED` - All required fields present, types correct
- `Validation: FAILED` - Errors listed, file not saved (unless `--force`)
- `Validation: SKIPPED` - Used with `--force`, file saved with warning

**Multi-Phase Validation:**
- Phase 1 output is validated before Phase 2 begins
- Phase 2 output is validated before Phase 3 (document update) begins
- Using `--force` allows progression despite validation failures, but may result in incomplete document updates
