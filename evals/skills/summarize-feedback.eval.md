---
command: summarize-feedback
type: skill
fixtures: []
---

# Eval: /summarize-feedback (skill)

## Purpose

Synthesizes employee feedback from Notion Voice Captures into a professional .docx assessment document. Good output: a structured Word document with themes, quotes, sentiment analysis, and actionable recommendations.

## Fixtures

None provided — this skill requires actual Notion voice capture data. Create a minimal test fixture if needed.

## Setup

Create a minimal test fixture representing Notion voice captures:

```markdown
# Voice Capture: Q4 Feedback Session
Participant: Anonymous
Date: 2026-01-10

"I really enjoy the collaborative culture here. My manager is supportive and I feel like my work matters."

"The tooling is outdated — we're still using a 5-year-old CI system that constantly breaks. It slows down every team."

"Communication from leadership about strategy could be better. I often hear about decisions through the grapevine."
```

Save this to `test-feedback.md` and use it as input.

## Test Scenarios

### S1: Synthesize feedback into .docx

**Invocation:** `/summarize-feedback test-feedback.md` (or provide path interactively)

**Must:**
- [ ] Creates a `.docx` output file
- [ ] Document contains a summary section
- [ ] Document identifies themes from the feedback
- [ ] Sentiment is assessed (positive/neutral/negative)
- [ ] Actionable recommendations are included

**Should:**
- [ ] Direct quotes are included to support themes
- [ ] Document looks professional (proper formatting)
- [ ] Themes are accurate to the test input (culture positive, tooling negative, communication gap)

**Must NOT:**
- [ ] Produce an empty or zero-byte .docx
- [ ] Attribute specific quotes to named individuals when anonymized

---

### S2: Missing python-docx dependency

**Setup:** Temporarily uninstall python-docx if testing dependency handling.

**Must:**
- [ ] Detects missing dependency
- [ ] Provides pip install instruction
- [ ] Asks user before installing

---

### S3: Error — file not found

**Invocation:** `/summarize-feedback nonexistent-feedback.md`

**Must:**
- [ ] Error message for missing file

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| .docx file created | Required |
| Themes identified from feedback | Required |
| Sentiment assessed | Required |
| Recommendations included | Required |
| Quotes not attributed to named individuals when anonymized | Required |
