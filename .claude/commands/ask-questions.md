# Ask Questions Command

Interactively walk the user through answering questions from a JSON file produced by the `/define-questions` command.

## Input

The user will provide a JSON file path after the slash command (e.g., `/ask-questions questions-PRD-20260110.json`). This file must follow the structure created by `/define-questions`.

## Instructions

### 1. Load and Validate

- Read the specified JSON file
- Validate it contains the expected `questions` array and `metadata`
- Load the original source document referenced in `metadata.source_document`
- Report the total number of questions to the user

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

### 3. Handle Special Commands

During the session, support these commands:
- `back` or `previous` - Return to the previous question
- `go to [N]` - Jump to question N
- `skip` - Skip current question
- `progress` - Show summary of answered/skipped/remaining
- `save` - Save current progress to a partial file
- `quit` - Save progress and exit (can resume later)

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

Save as `answers-[source-document]-[timestamp].json` in the repository root.

Example: `answers-PRD-20260110-143052.json`

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
