# Flag Consistency Reference

**Purpose:** Internal reference documenting which flags each command supports. Used for consistency audits.

**Last Updated:** 2026-03-04

## File-Generating Commands

These commands write output files. All support `--no-prompt` for automation.

| Command | `--format` | `--preview` | `--no-prompt` | `--force` | `--dry-run` | Other Flags |
|---------|-----------|------------|--------------|----------|------------|-------------|
| `/analyze-transcript` | `md`, `json` | Yes | Yes | -- | -- | -- |
| `/assess-document` | `md`, `json` | -- | Yes | -- | -- | `--focus <dimensions>` |
| `/consolidate-documents` | `markdown`, `text` | Yes | Yes | -- | -- | `--baseline <doc>`, `--json` |
| `/define-questions` | `json`, `csv` | Yes | Yes | Yes | -- | -- |
| `/develop-image-prompt` | -- | -- | Yes | -- | -- | `--style <style>`, `--dimensions <WxH>` |
| `/finish-document` | -- | -- | -- | Yes | -- | `--auto` (serves as non-interactive mode) |
| `/remove-ip` | -- | -- | Yes | -- | -- | `--company`, `--mode`, `--industry`, `--audience`, `--web-research` |

**Notes:**
- `/finish-document` uses `--auto` instead of `--no-prompt` because its interactive mode is the core value proposition (Q&A session). `--auto` auto-selects recommended answers.
- `/assess-document` does not have `--preview` because it always generates a report to `reports/` without intermediate decisions.

## Utility and In-Conversation Commands

These commands produce in-conversation output or modify files directly.

| Command | `--dry-run` | `--verbose` | `--audit` | Other Flags |
|---------|------------|------------|----------|-------------|
| `/bump-version` | Yes | -- | -- | -- |
| `/clean-repo` | Yes | -- | Yes | `--docs-only`, `--json` |
| `/convert-markdown` | Yes | -- | -- | `--no-toc`, `--style <path>`, `--highlight <style>` |
| `/new-command` | -- | -- | -- | `--plugin <name>` |
| `/new-skill` | -- | -- | -- | `--plugin <name>` |
| `/scaffold-plugin` | Yes | -- | -- | -- |
| `/validate-plugin` | -- | Yes | -- | `--all`, `--fix`, `--strict`, `--report`, `--scorecard`, `--check-updates` |

## Read-Only Analysis Commands

These commands produce in-conversation reports and never modify files.

| Command | Flags |
|---------|-------|
| `/plan-next` | None |
| `/review-arch` | `--json`, `--focus <dimensions>` |
| `/review-intent` | `--deep`, `--save` |

## Planning and Orchestration Commands

| Command | Key Flags |
|---------|-----------|
| `/create-plan` | `--output <path>`, `--phases <n>`, `--max-phases <n>`, `--verbose` |
| `/implement-plan` | `--input <path>`, `--auto-merge`, `--pause-between-phases`, `--progress` |
| `/plan-improvements` | `--recommendations-only` / `--no-plan`, `--max-phases <n>` |
| `/test-project` | `--coverage <n>`, `--auto-merge` |

## Interactive Commands

| Command | Key Flags |
|---------|-----------|
| `/ask-questions` | `--force` |

## Consistency Patterns

**Flag naming conventions:**
- Boolean flags use `--kebab-case` (e.g., `--dry-run`, `--no-prompt`)
- Value flags use `--flag <value>` (e.g., `--format md`, `--style infographic`)
- Negation flags use `--no-` prefix (e.g., `--no-prompt`, `--no-toc`, `--no-clarify`)

**Standard flag meanings:**
- `--dry-run`: Preview all operations without executing. Output prefixed with `[DRY-RUN]`.
- `--no-prompt`: Skip interactive prompts. Use defaults. Exit with error if required args are missing.
- `--preview`: Show summary and ask for confirmation before saving output.
- `--force`: Proceed despite validation errors (with warning).
- `--verbose`: Show additional detail in output.
- `--audit`: Log operations to `.claude-plugin/audit.log` as JSON lines.
- `--json`: Emit machine-readable JSON output instead of human-readable markdown/text.
- `--focus <dimensions>`: Limit analysis to specific dimensions (comma-separated).
- `--check-updates`: Check remote marketplace for plugin version drift and available updates.

**`--focus` valid dimension values:**
- `/assess-document`: `completeness`, `clarity`, `consistency`, `specificity`, `structure`, `feasibility`
- `/review-arch`: `code-quality`, `architecture`, `security`, `performance`, `testing`, `dependencies`

**Mutually exclusive flags:**
- `--recommendations-only` and `--no-plan` are aliases (same behavior)
- `--preview` and `--no-prompt` are effectively incompatible (preview asks for confirmation; no-prompt skips it)
