---
description: Meeting transcript to structured markdown report
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Meeting Transcript Analysis

Analyze a meeting transcript and produce a comprehensive markdown report with key discussion points, action items, decisions, and risks.

## Input Validation

**Required Arguments:**
- `<transcript-path>` - Path to the transcript file

**Optional Arguments:**
- `--format [md|json]` - Output format (default: md)
  - `md`: Markdown report with sections and tables (default)
  - `json`: Structured data with sections, action_items, decisions arrays
- `--preview` - Show summary and ask for confirmation before saving (see common-patterns.md)
- `--no-prompt` - Skip confirmation prompts. Use defaults for all options.

**Validation:**
If no transcript is provided:

1. **If `--no-prompt` is specified**, display the error and exit:
```text
Error: Missing required argument

Usage: /analyze-transcript <transcript-path> [--format md|json] [--preview] [--no-prompt]
Example: /analyze-transcript meeting-notes.txt
Example: /analyze-transcript transcript.md --format json
```

2. **Otherwise (default), prompt interactively** using the input flow below.

## Input Flow

Follow this concrete sequence to obtain the transcript:

**Step 1: Determine input source**

If a file path was provided as an argument, proceed to Step 2. Otherwise, ask:

```text
How would you like to provide the transcript?

1. File path — Provide the path to a transcript file (e.g., meeting-notes.txt)
2. Paste — Paste the transcript content directly into the chat

Enter choice (1 or 2):
```

**Step 2: Acquire the transcript**

- **If file path:** Read the file using the Read tool. Validate the file (see Error Handling section).
- **If paste:** Accept the pasted content. The user may need multiple messages for long transcripts. Ask "Is that the complete transcript, or is there more?" after the first paste.

**Step 3: Detect transcript type**

Analyze the content to determine the transcript type, which affects how sections are weighted:

| Type | Indicators | Analysis Focus |
|------|-----------|---------------|
| **Meeting notes** | Multiple speakers, agenda items, action items, "next steps" | Action items, decisions, owners |
| **Interview** | Q&A format, interviewer/interviewee pattern, structured questions | Key responses, themes, candidate assessment |
| **Presentation** | Single speaker dominant, slides referenced, Q&A at end | Key messages, audience questions, takeaways |
| **Workshop** | Exercises, breakout sessions, group activities, facilitation | Outcomes per activity, group decisions, parking lot |
| **General** | None of the above patterns match clearly | Balanced analysis across all sections |

Report the detected type to the user:
```text
Detected transcript type: Meeting notes
Transcript length: ~5,200 words (~7K tokens)
Proceeding with analysis...
```

**Step 4: Confirm scope (unless `--no-prompt`)**

For transcripts under 30K tokens, proceed directly to analysis. For larger transcripts, see Context Management below.

## Error Handling

Validate the transcript before beginning analysis:

| Error Condition | Detection | Response |
|----------------|-----------|----------|
| No transcript provided | No argument and `--no-prompt` set | Display usage message and exit |
| File not found | File does not exist at specified path | "Error: File not found: [path]. Check the path and try again." |
| Empty file | File exists but has no content | "Error: File is empty: [path]. Provide a transcript with content to analyze." |
| Binary file | File contains non-text data | "Error: [path] appears to be a binary file. Provide a text transcript (.txt, .md, .vtt, .srt)." |
| Unsupported format | File is .pdf, .docx, .xlsx, etc. | "Error: Unsupported format ([ext]). Supported: .txt, .md, .vtt, .srt, .html. For Word documents, use /convert-markdown first." |
| No actionable content | Text is present but contains no identifiable meeting content | "Warning: No actionable meeting content detected (no speakers, decisions, or action items found). The file may not be a transcript. Proceed anyway? (yes/no)" |
| Transcript too large | Content exceeds 50K tokens | See Context Management section below. Do not fail — process in sections. |

## Context Management (Large Transcripts)

For transcripts exceeding 30K tokens, process in sections to avoid context window limitations:

**First pass — Extraction:** Read the transcript in chunks (~20K tokens each). From each chunk, extract:
- Speakers identified
- Decisions made
- Action items assigned
- Risks or issues raised
- Key discussion topics

**Second pass — Synthesis:** Combine extracted elements across all chunks:
- Deduplicate speakers and topics that span chunks
- Merge action items, resolving any duplicates
- Synthesize discussion points into coherent topic summaries
- Ensure no decisions or action items are lost at chunk boundaries

Report to the user:
```text
Large transcript detected (~85K tokens). Processing in 5 sections.
  Section 1/5: Extracted 3 topics, 4 action items...
  Section 2/5: Extracted 2 topics, 2 action items...
  ...
Synthesis complete. Proceeding to report generation.
```

## Instructions

Read the provided transcript thoroughly and create a detailed analysis document with the following sections:

### 1. Meeting Overview
- Meeting title/topic (inferred from content)
- Date (if mentioned)
- Attendees (list all participants identified)
- Duration (if determinable)
- Transcript type (meeting, interview, presentation, workshop, or general)

### 2. Key Discussion Points
Synthesize the meeting content into a well-structured list of detailed points. **Important:** Organize these logically by topic/theme rather than chronologically as they occurred in the meeting. Group related discussions together even if they were spread throughout the meeting.

For each major topic:
- Provide context and background discussed
- Capture decisions made or conclusions reached
- Note any debate, alternatives considered, or dissenting views
- Include specific details, numbers, dates, or examples mentioned

### 3. Risks and Issues Identified
List all risks, concerns, blockers, and issues raised during the meeting:
- **Risk/Issue**: Clear description
- **Impact**: What could be affected
- **Mitigation** (if discussed): Any proposed solutions or workarounds
- **Status**: Open, being addressed, resolved, etc.

### 4. Action Items
Create a table of all action items with:

| Action Item | Owner | Due Date | Priority | Notes |
|-------------|-------|----------|----------|-------|
| Description | Name | Date or TBD | High/Med/Low | Context |

- Capture explicit assignments ("John will do X")
- Capture implicit commitments ("I'll follow up on...")
- Note if owner or date was not specified

### 5. Immediate Next Steps
List the concrete next steps that should happen before the next meeting or in the immediate future:
- What needs to happen first
- Who is responsible
- Any dependencies or prerequisites
- Timeline if mentioned

### 6. Decisions Made
Summarize any decisions that were finalized during the meeting:
- What was decided
- Key rationale
- Any conditions or caveats

### 7. Open Questions / Parking Lot
List any questions that were raised but not answered, or topics deferred for later discussion.

---

## Output Format

Based on the `--format` flag:

### Directory Creation

Before writing any output file, ensure the target directory exists:

```bash
# Ensure output directory exists before writing
mkdir -p reports/
```

### Markdown Format (default)

Generate the analysis as a clean markdown document that:
- Uses clear headers and subheaders
- Employs bullet points for readability
- Includes tables where appropriate
- Provides enough detail that someone who did not attend can fully understand what happened
- Maintains a professional, objective tone
- Highlights critical or time-sensitive items

Save as: `reports/meeting-analysis-YYYYMMDD-HHMMSS.md`

### JSON Format

Generate a structured JSON document with this schema:

```json
{
  "metadata": {
    "title": "Meeting title or topic",
    "date": "2026-01-10",
    "attendees": ["Person 1", "Person 2"],
    "duration": "1 hour",
    "transcript_type": "meeting",
    "analyzed_at": "2026-01-10T14:30:00Z"
  },
  "discussion_points": [
    {
      "topic": "Topic name",
      "summary": "Brief summary",
      "details": ["Detail 1", "Detail 2"],
      "decisions": ["Decision made"],
      "dissenting_views": ["Any disagreements noted"]
    }
  ],
  "risks_and_issues": [
    {
      "title": "Risk or issue name",
      "impact": "What could be affected",
      "mitigation": "Proposed solution",
      "status": "Open"
    }
  ],
  "action_items": [
    {
      "description": "Action item description",
      "owner": "Person name",
      "due_date": "2026-01-15",
      "priority": "High",
      "notes": "Additional context"
    }
  ],
  "next_steps": [
    {
      "step": "Description",
      "owner": "Person",
      "dependencies": ["Dependency 1"],
      "timeline": "Next week"
    }
  ],
  "decisions_made": [
    {
      "decision": "What was decided",
      "rationale": "Key reasoning",
      "conditions": ["Any caveats"]
    }
  ],
  "open_questions": ["Question 1", "Question 2"]
}
```

Save as: `reports/meeting-analysis-YYYYMMDD-HHMMSS.json`

## Preview Mode

When `--preview` is specified:

1. Generate the complete analysis in memory
2. Display summary:
   ```text
   Preview: /analyze-transcript
   Source: meeting-notes.txt
   Type: Meeting notes (detected)
   Attendees: 5 identified

   Content Summary:
     Discussion points: 8
     Action items: 12
     Risks/issues: 3
     Decisions made: 4
     Open questions: 2

   Output format: Markdown
   Output file: reports/meeting-analysis-20260114-143052.md

   Save this file? (y/n):
   ```
3. Wait for user confirmation before saving
4. On 'n' or 'no': Exit without saving

## File Naming

Use the timestamp format `YYYYMMDD-HHMMSS`. Use the meeting date if known (with current time), or the current date and time if not specified.

## Related Commands

- `/consolidate-documents` — Merge multiple meeting transcripts or document versions into one
- `/assess-document` — Evaluate the quality of a generated meeting report
- `/define-questions` — Extract open questions from the transcript for follow-up
- `/convert-markdown` — Convert the markdown report to a Word document for sharing
