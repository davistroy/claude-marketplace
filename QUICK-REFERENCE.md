# Quick Reference Card

Essential patterns for plugin development. See full docs in `plugins/personal-plugin/references/`.

## Command Naming

| Rule | Example | Avoid |
|------|---------|-------|
| Use kebab-case | `define-questions.md` | `defineQuestions.md` |
| Verb-noun pattern | `review-pr`, `assess-document` | `pr-review`, `document` |
| No `name` in frontmatter | Filename = command name | `name: my-command` |

## Frontmatter Template

```yaml
---
description: Brief description shown in command list (10-200 chars)
allowed-tools: Bash(git:*)  # Optional: restrict tool access
---
```

## Output File Naming

```
[type]-[source]-[timestamp].[ext]

Examples:
  questions-PRD-20260115-143052.json
  assessment-requirements-20260115-143052.md
  report-validation-20260115-143052.md
```

## Output Directories

| Output Type | Directory | Example |
|-------------|-----------|---------|
| Assessment reports | `reports/` | `reports/assessment-PRD-*.md` |
| Question files | `reference/` | `reference/questions-*.json` |
| Validation reports | `reports/` | `reports/validation-*.md` |
| Generated docs | Same as source | `docs/output.md` |

## Input Validation Template

```markdown
## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document

**Optional Arguments:**
- `--format [json|md]` - Output format (default: md)
- `--preview` - Preview before saving
- `--force` - Proceed despite validation errors
- `--no-prompt` - Disable interactive prompting

**Validation:**
If arguments missing, prompt or show usage.
```

## Common Flags

| Flag | Purpose | Behavior |
|------|---------|----------|
| `--all` | Apply to all targets | Iterate all plugins/files |
| `--fix` | Auto-fix issues | Modify files to fix problems |
| `--force` | Override validation | Proceed despite errors |
| `--verbose` | Detailed output | Show all checks, not just failures |
| `--preview` | Preview changes | Show output before saving |
| `--dry-run` | Simulate only | No file modifications |
| `--strict` | Fail on warnings | Treat warnings as errors |
| `--report` | Generate report file | Save to `reports/` |
| `--no-prompt` | Non-interactive mode | For scripts and CI/CD |
| `--scorecard` | Maturity assessment | Show plugin maturity levels |
| `--docs-only` | Documentation focus | Focus only on documentation updates |
| `--no-audience` | Skip audience detection | Skip audience profile detection |
| `--no-clarify` | Skip clarification | Skip clarification questions |
| `--audit` | Audit logging | Log actions to audit file |
| `--deep` | Deep analysis | Include git history analysis |

## Personal-Plugin Skills

Skills are proactive actions Claude may suggest after completing related work. Invoke with `/skill-name`.

| Skill | Purpose |
|-------|---------|
| `help` | Show available commands and skills with usage information |
| `prime` | Prime Claude with project context for faster onboarding |
| `research-topic` | Multi-source deep research across LLM providers |
| `security-analysis` | Comprehensive security analysis with tech stack detection |
| `ship` | Git workflow: branch, commit, push, PR |
| `summarize-feedback` | Synthesize Notion feedback into .docx assessment |
| `unlock` | Load Bitwarden secrets into environment via bws CLI |
| `validate-and-ship` | Validate plugins, clean repo, and ship in one workflow |
| `visual-explainer` | Transform text/docs into AI-generated visual explanations |

## Severity Levels

| Level | Use For |
|-------|---------|
| **CRITICAL** | Blocks progress, security issues |
| **WARNING** | Quality issues, missing tests |
| **SUGGESTION** | Improvements, best practices |

## Directory Creation

Always ensure output directories exist before writing:

```bash
mkdir -p reports/
mkdir -p reference/
```

## Links

- Full patterns: `plugins/personal-plugin/references/patterns/`
- Templates: `plugins/personal-plugin/references/templates/`
- Schema docs: `schemas/README.md`
- Contributing: `CONTRIBUTING.md`
