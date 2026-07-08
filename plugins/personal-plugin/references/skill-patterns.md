# Skill Pattern Reference

Purpose: one-line descriptions of the 8 command-pattern templates in `references/templates/`, for use by `/new-skill --pattern <name>` (see `commands/new-skill.md` Phase 2.2 "Pattern Adaptation" for how each template is adapted to SKILL.md form). Do not edit them here — edit `references/templates/<name>.md` directly.

| Pattern | Template | Purpose |
|---------|----------|---------|
| `conversion` | `references/templates/conversion.md` | Transforms files between formats, validating prerequisites before converting |
| `generator` | `references/templates/generator.md` | Analyzes input and generates structured output (JSON/data) with schema validation |
| `interactive` | `references/templates/interactive.md` | Runs a one-item-at-a-time Q&A session with resume support |
| `planning` | `references/templates/planning.md` | Analyzes a scope and generates recommendations plus a phased implementation plan |
| `read-only` | `references/templates/read-only.md` | Analyzes and reports findings by severity; makes no changes |
| `synthesis` | `references/templates/synthesis.md` | Merges multiple source documents into one superior consolidated output |
| `utility` | `references/templates/utility.md` | Runs validation/maintenance checks with pass/fail/warn reporting and auto-fix |
| `workflow` | `references/templates/workflow.md` | Executes a multi-step process with confirmations, dry-run, and audit logging |
