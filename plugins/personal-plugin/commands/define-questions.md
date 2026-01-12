# Define Questions Command

Analyze the document specified by the user and extract all questions, open items, areas needing clarification, and incomplete sections into a comprehensive, downloadable JSON file.

## Instructions

1. **Read the specified document** - The user will provide a document path or name after the `/define-questions` command (e.g., `/define-questions PRD.md`). Read and analyze that document thoroughly.

2. **Identify all questions and open items** - Look for:
   - Explicit questions (sentences ending with `?`)
   - Open items marked with "TBD", "TODO", "TBC", or similar markers
   - Incomplete sections or placeholders
   - Areas marked as needing review or decision
   - Gaps in specifications or requirements
   - Ambiguous or vague statements that need clarification
   - Missing details that would be needed for implementation
   - Dependencies or prerequisites that are undefined
   - Edge cases or scenarios not addressed

3. **Create a JSON file** with the following structure for each question/open item:

```json
{
  "questions": [
    {
      "id": 1,
      "topic": "Best guess at the topic area (e.g., 'User Authentication', 'Data Model', 'Integration')",
      "sections": ["Section name or header where this question is relevant"],
      "question": "The actual question or open item that needs clarification",
      "context": "Any relevant information, background, or details needed to understand and properly answer this question"
    }
  ],
  "metadata": {
    "source_document": "Name of the analyzed document",
    "total_questions": 0,
    "generated_date": "ISO date string",
    "topics_summary": ["List of unique topics identified"]
  }
}
```

4. **Assign sequential IDs** starting from 1 for each question.

5. **Categorize by topic** - Group related questions under logical topic areas based on the content (e.g., "Technical Architecture", "User Experience", "Business Logic", "Data Management", "Integration", "Security", "Performance", etc.).

6. **Reference relevant sections** - For each question, note which section(s) of the document it relates to. Use the exact section headers/titles from the document.

7. **Provide rich context** - For each question, include enough context so that someone unfamiliar with the document could understand:
   - Why this question matters
   - What information is currently available
   - What specific details are missing or unclear
   - Any constraints or requirements that affect the answer

8. **Save the output** - Write the JSON file to a new file named `questions-[document-name]-[timestamp].json` in the repository root. Use a timestamp format like `YYYYMMDD-HHMMSS`.

9. **Report the results** - After creating the file, provide a summary to the user including:
   - Total number of questions identified
   - Breakdown by topic area
   - The file path where the JSON was saved

## Example Output

```json
{
  "questions": [
    {
      "id": 1,
      "topic": "Board Role Definitions",
      "sections": ["3.1 AI Board Members", "4.2 Governance Sessions"],
      "question": "What specific expertise and personality traits should each of the 5 AI board member roles embody?",
      "context": "The PRD mentions a 5-role AI board for career governance but does not define the specific roles, their areas of expertise, how they should interact with each other, or their individual decision-making styles. This is critical for implementing the governance session logic and ensuring diverse perspectives."
    },
    {
      "id": 2,
      "topic": "LLM Integration",
      "sections": ["5.1 Technical Architecture"],
      "question": "Which LLM provider(s) will be used for the AI board members and transcription services?",
      "context": "The document references LLM services for voice transcription and AI board member responses but does not specify whether to use OpenAI, Anthropic, or other providers. This affects API integration, cost modeling, and capability constraints."
    }
  ],
  "metadata": {
    "source_document": "PRD.md",
    "total_questions": 2,
    "generated_date": "2026-01-10T14:30:00Z",
    "topics_summary": ["Board Role Definitions", "LLM Integration"]
  }
}
```

## Important Notes

- Be thorough - it's better to capture more questions than to miss important ones
- Questions should be actionable - they should be answerable with specific decisions or information
- Avoid duplicate questions - consolidate similar questions into one with comprehensive context
- Preserve the original intent - don't rephrase questions in ways that change their meaning
- The JSON must be valid and properly formatted for downstream use with AI tools
