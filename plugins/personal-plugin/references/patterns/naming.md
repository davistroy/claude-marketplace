# Naming Patterns

This document defines naming conventions for files, commands, and output artifacts.

## Timestamp Format

`YYYYMMDD-HHMMSS` (e.g., `20260114-143052`)

## Output File Naming

`[type]-[source]-[timestamp].[ext]`

Examples:
- `assessment-PRD-20260114-143052.md`
- `questions-requirements-20260114-150000.json`
- `answers-design-doc-20260114-160030.json`
- `meeting-analysis-20260114-093000.md`

## Output Locations

| Output Type | Directory | Example |
|-------------|-----------|---------|
| Analysis reports | `reports/` | `reports/assessment-PRD-20260114.md` |
| Reference data (JSON) | `reference/` | `reference/questions-PRD-20260114.json` |
| Generated documents | Same as source | `docs/PRD.docx` |
| Temporary files | `.tmp/` | `.tmp/cache-20260114.json` |

## Command Naming Conventions

- Use **kebab-case** for command filenames (e.g., `define-questions.md`)
- Commands are invoked as `/filename` (without `.md` extension)
- Use action-oriented verbs: `define-`, `validate-`, `review-`, `analyze-`, etc.
- Be descriptive but concise: prefer `review-pr` over `code-review-pull-request`

## Variable and Field Naming

- JSON fields: use **snake_case** (e.g., `source_document`, `generated_date`)
- Boolean fields: use `is_` or `has_` prefix for clarity (e.g., `is_completed`, `has_errors`)
- Timestamps: use ISO 8601 format in JSON (`2026-01-14T14:30:00Z`)

## Type Prefixes for Generated Files

| Type Prefix | Use Case | Example |
|-------------|----------|---------|
| `questions-` | Extracted questions | `questions-PRD-20260114.json` |
| `answers-` | Answered questions | `answers-PRD-20260114.json` |
| `assessment-` | Document evaluations | `assessment-PRD-20260114.md` |
| `analysis-` | General analysis output | `analysis-codebase-20260114.md` |
| `report-` | Summary reports | `report-validation-20260114.md` |

## Backup File Naming

For backup files created before modifications:
`[original-name].backup-[timestamp].[ext]`

Example: `PRD.backup-20260111-150000.md`
