---
command: analyze-transcript
type: command
fixtures: [docs/meeting-transcript.md]
---

# Eval: /analyze-transcript

## Purpose

Reads a meeting transcript and produces a structured report with key discussion points, action items, decisions, and risks. Good output captures all explicit action items and decisions from the transcript without fabricating details.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/meeting-transcript.md` | 20-min kickoff meeting with 4 action items, 3 decisions, 2 risks |

## Test Scenarios

### S1: Happy path — markdown output

**Invocation:** `/analyze-transcript fixtures/docs/meeting-transcript.md`

**Must:**
- [ ] Creates a report file (timestamped) in the current directory or `reports/`
- [ ] Report contains an action items section with at least 3 of the 4 actual action items
- [ ] Report contains a decisions section listing all 3 technology decisions (Node.js, PostgreSQL, Block Kit)
- [ ] Report contains a risks section identifying both risks (rate limiting, Jamie's availability)
- [ ] Each action item includes the owner and due date when stated in the transcript

**Should:**
- [ ] Action items include: Dev/scheduler spike (Jan 16), Sam/ECS provisioning (Jan 17), Alex/MVP doc (Jan 14), Alex/Payments PM follow-up (Jan 12)
- [ ] Decisions include: Node.js 20 LTS confirmed, PostgreSQL 15 confirmed, Slack Block Kit confirmed
- [ ] Report includes a participants section
- [ ] Meeting date and duration captured

**Must NOT:**
- [ ] Invent action items not in the transcript
- [ ] Invent attendees not listed

---

### S2: JSON output format

**Invocation:** `/analyze-transcript fixtures/docs/meeting-transcript.md --format json`

**Must:**
- [ ] Output file is valid JSON
- [ ] JSON contains `action_items`, `decisions`, `risks` arrays
- [ ] Each action item has `owner` and `due_date` fields where available

**Must NOT:**
- [ ] Create a markdown file when `--format json` is specified

---

### S3: Error — file not found

**Invocation:** `/analyze-transcript fixtures/docs/nonexistent.txt`

**Must:**
- [ ] Displays error message referencing the missing file
- [ ] Does not create output file

---

### S4: Missing argument (interactive)

**Invocation:** `/analyze-transcript` (no arguments)

**Must:**
- [ ] Prompts for transcript path interactively

---

### S5: Missing argument with --no-prompt

**Invocation:** `/analyze-transcript --no-prompt`

**Must:**
- [ ] Displays usage error with example
- [ ] Exits without prompting

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| All action items from transcript captured | Required (≥ 3 of 4) |
| All decisions captured | Required (all 3) |
| Both risks identified | Should |
| No invented facts | Required |
| Output file created with timestamp naming | Required |
