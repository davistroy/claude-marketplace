# JSON Schemas

This directory contains JSON Schema definitions for structured outputs produced by plugin commands.

## Purpose

These schemas define contracts between commands that work in chains:

```
/define-questions  -->  questions.json  -->  /ask-questions  -->  answers.json  -->  /finish-document
```

## Available Schemas

| Schema | Description | Used By |
|--------|-------------|---------|
| `questions.json` | Questions extracted from documents | `/define-questions`, `/finish-document` |
| `answers.json` | Answered questions with selections | `/ask-questions`, `/finish-document` |

## Schema Details

### questions.json

Defines the structure for extracted questions and open items.

**Required Fields:**
- `metadata.source_document` - The analyzed document path
- `metadata.generated_at` - ISO 8601 timestamp
- `metadata.total_questions` - Count of questions
- `questions[].id` - Unique identifier (string or integer)
- `questions[].text` or `questions[].question` - The question text
- `questions[].context` - Background information

**Optional Fields:**
- `metadata.topics_summary` - List of unique topics
- `questions[].topic` / `questions[].category` - Topic area
- `questions[].sections` - Relevant document sections
- `questions[].priority` - "high", "medium", or "low"
- `questions[].location` - Line numbers for document updates

### answers.json

Defines the structure for answered questions from Q&A sessions.

**Required Fields:**
- `metadata.source_document` - Original document path
- `metadata.total_questions` - Count of questions
- `answers[].id` - Matching question identifier
- `answers[].selected_answer` - The answer text

**Optional Fields:**
- `metadata.source_questions_file` - Input questions file path
- `metadata.answer_summary` - Breakdown by answer type
- `answers[].answer_type` - "recommended", "alternative", "custom", or "skipped"
- `answers[].location` - Line numbers for document updates

## Validation

You can validate JSON files against these schemas using any JSON Schema validator:

```bash
# Using ajv-cli (Node.js)
npm install -g ajv-cli
ajv validate -s schemas/questions.json -d your-questions-file.json

# Using jsonschema (Python)
pip install jsonschema
python -c "from jsonschema import validate; import json; validate(json.load(open('file.json')), json.load(open('schemas/questions.json')))"
```

## Versioning

These schemas follow JSON Schema draft 2020-12. Breaking changes will be noted in the repository CHANGELOG.

## Examples

Each schema file contains an `examples` array with valid sample data demonstrating proper usage.
