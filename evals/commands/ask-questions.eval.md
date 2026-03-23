---
command: ask-questions
type: command
fixtures: [json/questions-sample.json]
---

# Eval: /ask-questions

## Purpose

Reads a questions JSON file (produced by `/define-questions`) and conducts a single-question-at-a-time interactive Q&A session. Each question is presented individually; the user's answer is recorded and the session proceeds to the next question. Good behavior: one question at a time, patient waiting, no skipping ahead.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `json/questions-sample.json` | 5 pre-extracted questions from draft-prd.md |

## Test Scenarios

### S1: Happy path — full Q&A session

**Setup:** Have `fixtures/json/questions-sample.json` available. Be prepared to answer all 5 questions.

**Invocation:** `/ask-questions fixtures/json/questions-sample.json`

**Must:**
- [ ] Reads and parses the JSON file successfully
- [ ] Displays question 1 with its context before asking for an answer
- [ ] Waits for user input before proceeding to question 2
- [ ] Advances to question 2 only after user responds
- [ ] Displays a progress indicator (e.g., "Question 1 of 5")
- [ ] After all 5 answers are collected, provides a summary of answers
- [ ] Does not present all 5 questions at once

**Should:**
- [ ] Shows the question topic/category before the question text
- [ ] After each answer, briefly acknowledges before moving on

**Must NOT:**
- [ ] Ask two questions in the same message
- [ ] Skip any question
- [ ] Invent or pre-fill answers

---

### S2: Session with "skip" response

**Setup:** Answer first question normally, respond "skip" to question 2, then answer remaining questions.

**Must:**
- [ ] Accepts "skip" and moves to next question without requiring an actual answer
- [ ] Skipped questions are noted in the final summary as skipped (not answered)
- [ ] Total question count is still displayed correctly

---

### S3: Error — invalid JSON file

**Invocation:** `/ask-questions fixtures/docs/sample-prd.md` (wrong file type)

**Must:**
- [ ] Displays an error indicating the file is not a valid questions JSON
- [ ] Does not crash or ask nonsensical questions

---

### S4: Error — file not found

**Invocation:** `/ask-questions fixtures/json/nonexistent.json`

**Must:**
- [ ] Displays a file not found error
- [ ] Does not start the Q&A session

---

### S5: Missing argument (interactive)

**Invocation:** `/ask-questions` (no arguments)

**Must:**
- [ ] Prompts for the questions file path

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| One question presented at a time | Required |
| Progress tracking displayed | Required |
| Skip handling works correctly | Should |
| Final summary of answers provided | Should |
| Does not advance without user input | Required |
