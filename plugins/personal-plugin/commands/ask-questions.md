---
description: Interactive Q&A session from questions JSON file
---

# Ask Questions Command

Interactively walk the user through answering questions from a JSON file produced by the `/define-questions` command.

## Input Validation

**Required Arguments:**
- `<questions-file>` - Path to the JSON file created by `/define-questions`

**Optional Arguments:**
- `--force` - Proceed even if input or output schema validation fails (not recommended)

**Validation:**
If the questions file path is missing, display:
```
Usage: /ask-questions <questions-file> [--force]
Example: /ask-questions questions-PRD-20260110-143052.json
Example: /ask-questions reference/questions-requirements-20260114.json
```

## Input

The user will provide a JSON file path after the slash command (e.g., `/ask-questions questions-PRD-20260110.json`). This file must follow the structure created by `/define-questions`.

## Instructions

### 1. Load and Validate

- Read the specified JSON file
- Validate it conforms to `schemas/questions.json` schema structure
- Verify it contains the required `questions` array and `metadata`
- Load the original source document referenced in `metadata.source_document`
- **Check for existing answer file** (resume support - see below)
- Report the total number of questions to the user

### 1.1 Resume Support

Before starting the Q&A session, check for an incomplete previous session:

1. Look for existing `answers-[source-document]-*.json` files
2. If found with `metadata.status: "in_progress"`:
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Incomplete session detected
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Previous session: answers-PRD-20260114-100000.json
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

**Input Schema:** The input file must conform to `schemas/questions.json`

#### Input Validation Behavior

Before proceeding with the Q&A session:

1. **Load the JSON file**
2. **Validate against `schemas/questions.json`**
3. **If valid:** Proceed with the session
4. **If invalid:** Report validation errors
5. **If `--force` provided:** Proceed with a warning

**Input Validation Error Message:**
```
Input validation failed for questions-PRD-20260114.json:

Errors:
  - metadata.source_document: Required field missing
  - questions[2]: Missing required field 'context'

The input file may have been created with an older version or manually edited.
Use --force to proceed anyway (some features may not work correctly).
```

**Input Validation Warning (with --force):**
```
WARNING: Input validation failed but --force was specified.
Proceeding with Q&A session. Some questions may not display correctly.
```

### 2. Process Each Question ONE AT A TIME

**CRITICAL: Never batch questions. Never skip ahead. Wait for user response before proceeding.**

For each question in sequential order by ID:

#### A. Display Progress Header
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Question 12 of 47 | Topic: [Topic Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### B. Present the Question with Enriched Context

Display:
- **Question:** The original question text
- **Relevant Sections:** Section(s) from the source document
- **Context:** The stored context from the JSON
- **Additional Detail:** Review the original source document and provide supplementary context that helps clarify the question
- **What You're Solving:** Infer and explain what the user is trying to achieve by answering this question - connect it to the bigger picture

#### C. Provide Answer Options in Multiple-Choice Format

Always present options in this structure:

```
**[A] Recommended:** [Your best answer]
    Why this is best: [Clear rationale - 1-2 sentences]

**[B] Alternative:** [Viable alternative answer]
    Trade-off: [What you gain/lose with this choice]

**[C] Alternative:** [Another option if applicable]
    Trade-off: [What you gain/lose with this choice]

**[D] Custom:** Provide your own answer

**[S] Skip:** Skip this question for now (can return later)

Your choice (A/B/C/D/S):
```

Guidelines for generating answers:
- Make answers **specific and actionable**, not generic
- Base recommendations on best practices, the source document's goals, and practical implementation considerations
- Explain trade-offs honestly - no option is perfect
- If the question has an objectively correct answer, still offer alternatives that might fit different constraints (budget, timeline, scope)
- For subjective questions, acknowledge that preferences may vary

#### D. Wait for User Response

- Do not proceed until the user provides input
- Accept: A, B, C, D, S, or the full answer text
- If user selects D (Custom), prompt them to type their answer
- If user selects S (Skip), mark as skipped and continue
- If user wants to revisit a previous question, allow it (e.g., "go back to question 5")

#### E. Confirm and Record

- Briefly confirm the recorded answer
- Proceed to the next question

### 3. Handle Session Commands

During the session, support these standard session commands (see `references/patterns/workflow.md` for full specification):

| Command | Aliases | Action |
|---------|---------|--------|
| `help` | `?`, `commands` | Show available session commands |
| `status` | `progress` | Show answered/skipped/remaining summary |
| `back` | `previous`, `prev` | Return to previous question |
| `skip` | `next`, `pass` | Skip current question |
| `quit` | `exit`, `stop` | Save progress and exit |
| `go to [N]` | | Jump to question N |
| `save` | | Save current progress without exiting |

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Implementation notes:**
- Commands are case-insensitive
- Check for session commands before processing input as an answer choice
- Unknown input that is not A/B/C/D/S should trigger the help message

### 4. After All Questions Are Answered

#### A. Handle Skipped Questions

If any questions were skipped:
```
You skipped 3 questions. Would you like to:
[A] Answer them now
[B] Leave them unanswered
[C] Review the list first
```

#### B. Generate Output JSON

Create a file with this structure:

```json
{
  "answers": [
    {
      "id": 1,
      "topic": "Original topic from questions file",
      "sections": ["Original sections from questions file"],
      "question": "Original question text",
      "context": "Original context from questions file",
      "selected_answer": "The answer the user selected or provided",
      "answer_type": "recommended | alternative | custom | skipped",
      "answered_at": "2026-01-10T14:30:00Z"
    }
  ],
  "metadata": {
    "source_questions_file": "questions-PRD-20260110.json",
    "source_document": "PRD.md",
    "total_questions": 47,
    "started_at": "2026-01-10T14:00:00Z",
    "completed_at": "2026-01-10T15:30:00Z",
    "answer_summary": {
      "recommended": 35,
      "alternative": 8,
      "custom": 4,
      "skipped": 0
    }
  }
}
```

#### C. Save the File

Save as `answers-[source-document]-YYYYMMDD-HHMMSS.json` in the repository root.

Example: `answers-PRD-20260110-143052.json`

**Output Schema:** The output file must conform to `schemas/answers.json`

#### Output Validation Behavior

Before saving the answers file:

1. **Generate output in memory** - Create the complete JSON structure
2. **Validate against `schemas/answers.json`**
3. **If valid:** Save file and report success with validation status
4. **If invalid:** Report specific validation errors
5. **If `--force` provided:** Save anyway with a warning

**Output Validation Success Message:**
```
Output validated against schemas/answers.json. Saved to answers-PRD-20260114-143052.json

Validation: PASSED
- Required fields: All present
- Field types: All correct
```

**Output Validation Error Message:**
```
Schema validation failed:

Errors:
  - answers[5].selected_answer: Required field missing
  - metadata.total_questions: Must be an integer

Fix these issues or use --force to save anyway (not recommended).
```

**Output Validation Warning (with --force):**
```
WARNING: Output validation failed but --force was specified.
Output saved to answers-PRD-20260114-143052.json

This file may not work correctly with /finish-document.
```

#### D. Display Completion Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Questions: 47
- Recommended answers selected: 35 (74%)
- Alternative answers selected: 8 (17%)
- Custom answers provided: 4 (9%)
- Skipped: 0 (0%)

Saved to: answers-PRD-20260110-143052.json

This file can be used to:
- Update your source document with decisions made
- Share decisions with stakeholders
- Track rationale for future reference
```

## Key Requirements

1. **ONE AT A TIME** - This is critical. Never show multiple questions at once.
2. **Always wait for input** - Do not auto-advance or assume answers.
3. **Reference the source** - Always consult the original document for context.
4. **Specific answers** - Generic answers like "it depends" are not acceptable. Commit to recommendations.
5. **Maintain state** - Track progress so users can pause and resume.
6. **Conversational tone** - Be helpful and encouraging, especially for long sessions.
7. **Respect user choice** - If they prefer an alternative or custom answer, don't push back.

## Example Interaction

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Question 3 of 32 | Topic: LLM Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Question:** Which LLM provider(s) should be used for the AI board members and transcription services?

**Relevant Sections:** 5.1 Technical Architecture, 3.2 AI Services

**Context:** The PRD references LLM services for voice transcription and AI board member responses but does not specify providers. This affects API integration, cost modeling, and capability constraints.

**Additional Detail:** Your PRD emphasizes privacy and data security (Section 7.1), mentions the need for consistent personality in AI board members (Section 3.1), and targets a $9.99/month price point. The transcription service needs to handle voice memos up to 5 minutes.

**What You're Solving:** You need to select infrastructure that balances cost, capability, and privacy while ensuring the AI board members can maintain consistent, high-quality personas across sessions.

---

**[A] Recommended:** Use Claude (Anthropic) for AI board members + Deepgram for transcription
    Why this is best: Claude excels at maintaining consistent personas and nuanced conversation. Deepgram offers accurate, cost-effective transcription with good privacy practices. Combined cost fits your margin at scale.

**[B] Alternative:** Use GPT-4 (OpenAI) for both AI and transcription (Whisper)
    Trade-off: Single vendor simplifies integration but higher cost per request. Whisper is excellent but OpenAI's data practices may conflict with privacy emphasis.

**[C] Alternative:** Use Claude for AI + AssemblyAI for transcription
    Trade-off: AssemblyAI has strong accuracy and real-time features, but adds another vendor relationship. Good middle-ground on privacy.

**[D] Custom:** Provide your own answer

**[S] Skip:** Skip this question for now

Your choice (A/B/C/D/S):
```

User types: `A`

```
Recorded: Claude (Anthropic) for AI board members + Deepgram for transcription

Proceeding to question 4...
```

## Schema Validation Summary

This command validates both input and output against their respective schemas. See `references/patterns/validation.md` for full validation behavior.

| Direction | Schema | Flag Behavior |
|-----------|--------|---------------|
| Input | `schemas/questions.json` | Validate before session starts |
| Output | `schemas/answers.json` | Validate before saving |

| Flag | Behavior |
|------|----------|
| (default) | Validate input/output, fail if invalid, show specific errors |
| `--force` | Proceed/save despite validation errors (with warning) |

**Validation Status in Output:**
All command completions include validation status:
- `Validation: PASSED` - All required fields present, types correct
- `Validation: FAILED` - Errors listed, file not saved (unless `--force`)
- `Validation: SKIPPED` - Used with `--force`, file saved with warning

**Downstream Compatibility:**
- Input from `/define-questions` is validated to ensure compatibility
- Output is validated for `/finish-document` compatibility
- Using `--force` may result in files that don't work with downstream commands
