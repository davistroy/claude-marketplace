---
description: Meeting transcript to structured markdown report
---

# Meeting Transcript Analysis

Analyze the attached meeting transcript and produce a comprehensive markdown report.

## Input Validation

**Required Arguments:**
- `<transcript-path>` - Path to the transcript file or pasted content

**Optional Arguments:**
- `--format [md|json]` - Output format (default: md)
  - `md`: Markdown report with sections and tables (default)
  - `json`: Structured data with sections, action_items, decisions arrays
- `--preview` - Show summary and ask for confirmation before saving (see common-patterns.md)

**Validation:**
If no transcript is provided, display:
```
Usage: /analyze-transcript <transcript-path> [--format md|json]
Example: /analyze-transcript meeting-notes.txt
Example: /analyze-transcript transcript.md --format json
```

You can also paste transcript content directly when prompted.

## Instructions

Read the provided transcript thoroughly and create a detailed analysis document with the following sections:

### 1. Meeting Overview
- Meeting title/topic (inferred from content)
- Date (if mentioned)
- Attendees (list all participants identified)
- Duration (if determinable)

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
   ```
   Preview: /analyze-transcript
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Source: meeting-notes.txt
   Meeting: Project Kickoff (inferred)
   Attendees: 5 identified

   Content Summary:
     Discussion points: 8
     Action items: 12
     Risks/issues: 3
     Decisions made: 4
     Open questions: 2

   Output format: Markdown
   Output file: meeting-analysis-20260114-143052.md
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Save this file? (y/n):
   ```
3. Wait for user confirmation before saving
4. On 'n' or 'no': Exit without saving

## File Naming

Use the timestamp format `YYYYMMDD-HHMMSS`. Use the meeting date if known (with current time), or the current date and time if not specified.
