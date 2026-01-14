---
description: Meeting transcript to structured markdown report
---

# Meeting Transcript Analysis

Analyze the attached meeting transcript and produce a comprehensive markdown report.

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

Generate the analysis as a clean markdown document that:
- Uses clear headers and subheaders
- Employs bullet points for readability
- Includes tables where appropriate
- Provides enough detail that someone who did not attend can fully understand what happened
- Maintains a professional, objective tone
- Highlights critical or time-sensitive items

## File Naming

Save the analysis as `meeting-analysis-YYYYMMDD-HHMMSS.md` using the timestamp format `YYYYMMDD-HHMMSS`. Use the meeting date if known (with current time), or the current date and time if not specified.
