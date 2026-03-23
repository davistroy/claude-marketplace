---
name: help
description: Show available commands and skills in this plugin with usage information
---

# Help Skill

Display help information for the personal-plugin commands and skills.

**IMPORTANT:** This skill must be updated whenever commands or skills are added, changed, or removed from this plugin.

## Usage

```
/help                          # Show all commands and skills
/help <command-name>           # Show detailed help for a specific command
```

## Mode 1: List All (no arguments)

When invoked without arguments, display this table:

```
personal-plugin Commands and Skills
===================================

COMMANDS
--------
| Command | Description |
|---------|-------------|
| /analyze-transcript | Meeting transcript to structured markdown report |
| /ask-questions | Interactive Q&A session from questions JSON file |
| /assess-document | Document quality evaluation with scored assessment report |
| /bump-version | Automate version bumping across plugin files with CHANGELOG placeholder |
| /clean-repo | Comprehensive repository cleanup, organization, and documentation refresh |
| /consolidate-documents | Analyze multiple document variations and synthesize a superior consolidated... |
| /convert-markdown | Convert a markdown file to a nicely formatted Microsoft Word document |
| /create-plan | Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD,... |
| /define-questions | Extract questions and open items from documents to JSON |
| /develop-image-prompt | Generate detailed image generator prompts from content, with configurable... |
| /finish-document | Extract questions from a document, answer them interactively, and update the... |
| /implement-plan | Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic... |
| /new-command | Generate a new command file from a template with proper structure and... |
| /new-skill | Generate a new skill file with proper nested directory structure and... |
| /plan-improvements | Analyze codebase and generate prioritized improvement recommendations with... |
| /plan-next | Analyze repo and recommend the next logical action |
| /remove-ip | Sanitize documents by removing company identifiers and non-public... |
| /review-arch | Quick architectural audit with technical debt assessment (read-only, no... |
| /review-intent | Determine original project intent and compare against current... |
| /review-pr | Structured PR review with security, performance, and code quality analysis |
| /scaffold-plugin | Create a new plugin with proper directory structure, metadata, and starter files |
| /test-project | Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then... |
| /validate-plugin | Validate plugin structure, frontmatter, and content for consistency and... |

SKILLS
------
| Skill | Description |
|-------|-------------|
| /evaluate-pipeline-output | Thoroughly evaluate contact-center-lab pipeline output quality against... |
| /leak-risk-audit | Audit a dataset for proprietary information leaks before sharing with... |
| /plan-gate | Before starting complex multi-step implementation tasks, assess scope and... |
| /prime | Evaluate an existing codebase to produce a detailed report on project... |
| /research-topic | Orchestrate parallel deep research across multiple LLM providers and... |
| /security-analysis | Comprehensive security analysis with tech stack detection, vulnerability... |
| /ship | Create branch, commit, push, open PR, auto-review, fix issues, and merge |
| /spec-to-prototype | Use when the user has a spec document, design system reference, component... |
| /summarize-feedback | Synthesize employee feedback from Notion Voice Captures into a professional... |
| /unlock | Load secrets from Bitwarden Secrets Manager into environment using bws CLI |
| /validate-and-ship | Validate plugins, clean repository, and ship changes in one automated workflow |
| /visual-explainer | Transform text or documents into AI-generated infographic pages that explain... |

---
Use '/help <name>' for detailed help on a specific command or skill.
```

## Mode 2: Detailed Help (with argument)

When invoked with a command or skill name, read the corresponding file and display:

1. **Description** - From frontmatter
2. **Arguments** - From "Input Validation" section if present
3. **Output** - What the command produces
4. **Example** - Usage example

### Command Reference

Use this reference to provide detailed help. Read the actual command file to get the most accurate information.

---

#### /analyze-transcript
**Description:** Meeting transcript to structured markdown report
**Arguments:** <transcript-path> [--format [md|json]]
**Output:** Generated output file
**Example:**
```
/analyze-transcript meeting-notes.txt
/analyze-transcript transcript.md --format json
```

---

#### /ask-questions
**Description:** Interactive Q&A session from questions JSON file
**Arguments:** <questions-file> [--force]
**Output:** Generated output file
**Example:**
```
/ask-questions questions-PRD-20260110.json
```

---

#### /assess-document
**Description:** Document quality evaluation with scored assessment report
**Arguments:** <document-path> [--format [md|json]]
**Output:** Files in reports/
**Example:**
```
/assess-document
/assess-document PRD.md
```

---

#### /bump-version
**Description:** Automate version bumping across plugin files with CHANGELOG placeholder
**Arguments:** <plugin-name> <bump-type> [--dry-run]
**Output:** In-conversation output
**Example:**
```
/bump-version
```

---

#### /clean-repo
**Description:** Comprehensive repository cleanup, organization, and documentation refresh
**Arguments:** [--dry-run] [--audit] [--docs-only] [--json]
**Output:** In-conversation output
**Example:**
```
/clean-repo
```

---

#### /consolidate-documents
**Description:** Analyze multiple document variations and synthesize a superior consolidated...
**Arguments:** <doc1-path> <doc2-path> [doc3-path...]
**Output:** consolidated-[topic]-YYYYMMDD-HHMMSS.md
**Example:**
```
/consolidate-documents
```

---

#### /convert-markdown
**Description:** Convert a markdown file to a nicely formatted Microsoft Word document
**Arguments:** <markdown-file> [<output-file>] [--no-toc] [--style <path>] [--dry-run] [--highlight <style>]
**Output:** Generated output file
**Example:**
```
/convert-markdown
```

---

#### /create-plan
**Description:** Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD,...
**Arguments:** [<document-paths>] [--output <path>] [--phases <n>] [--max-phases <n>] [--verbose]
**Output:** In-conversation output
**Example:**
```
/create-plan
```

---

#### /define-questions
**Description:** Extract questions and open items from documents to JSON
**Arguments:** <document-path> [--format [json|csv]]
**Output:** Generated output file
**Example:**
```
/define-questions
/define-questions PRD.md
```

---

#### /develop-image-prompt
**Description:** Generate detailed image generator prompts from content, with configurable...
**Arguments:** <content-source> [--style <style>] [--dimensions <WxH>] [--no-prompt]
**Output:** Generated output file
**Example:**
```
/develop-image-prompt architecture.md
/develop-image-prompt "microservices communication patterns" --style infographic
```

---

#### /finish-document
**Description:** Extract questions from a document, answer them interactively, and update the...
**Arguments:** <document-path> [--auto] [--force]
**Output:** Generated output file
**Example:**
```
/finish-document PRD.md
/finish-document
/finish-document PRD.md
```

---

#### /implement-plan
**Description:** Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/implement-plan
/implement-plan
/implement-plan
```

---

#### /new-command
**Description:** Generate a new command file from a template with proper structure and...
**Arguments:** [<command-name>] [<pattern-type>] [--plugin <name>]
**Output:** plugins/[TARGET_PLUGIN]/commands/[command-name].md
**Example:**
```
/new-command
```

---

#### /new-skill
**Description:** Generate a new skill file with proper nested directory structure and...
**Arguments:** [<skill-name>] [--plugin <plugin-name>]
**Output:** plugins/[plugin-name]/skills/[skill-name]/SKILL.md
**Example:**
```
/new-skill
```

---

#### /plan-improvements
**Description:** Analyze codebase and generate prioritized improvement recommendations with...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/plan-improvements
```

---

#### /plan-next
**Description:** Analyze repo and recommend the next logical action
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/plan-next
```

---

#### /remove-ip
**Description:** Sanitize documents by removing company identifiers and non-public...
**Arguments:** <document-path> [--company <name>] [--mode [standard|strict]]
**Output:** Generated output file
**Example:**
```
/remove-ip internal-process.md
/remove-ip strategy-doc.md --mode strict
```

---

#### /review-arch
**Description:** Quick architectural audit with technical debt assessment (read-only, no...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/review-arch --focus security,testing
```

---

#### /review-intent
**Description:** Determine original project intent and compare against current...
**Arguments:** [<path>] [--deep] [--save]
**Output:**  flag is provided:**
Save the report to a file using the Write tool:
- **Location:** 
**Example:**
```
/review-intent
```

---

#### /review-pr
**Description:** Structured PR review with security, performance, and code quality analysis
**Arguments:** <pr-number-or-url>
**Output:** In-conversation output
**Example:**
```
/review-pr
```

---

#### /scaffold-plugin
**Description:** Create a new plugin with proper directory structure, metadata, and starter files
**Arguments:** [<plugin-name>] [--dry-run]
**Output:** plugins/[plugin-name]/.claude-plugin/plugin.json
**Example:**
```
/scaffold-plugin
```

---

#### /test-project
**Description:** Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then...
**Arguments:** None (operates on the current project) [--coverage <n>] [--auto-merge]
**Output:** In-conversation output
**Example:**
```
/test-project
```

---

#### /validate-plugin
**Description:** Validate plugin structure, frontmatter, and content for consistency and...
**Arguments:** <plugin-name> [--all] [--fix] [--verbose] [--strict] [--report] [--scorecard] [--check-updates]
**Output:** Generated output file
**Example:**
```
/validate-plugin
```

---

#### /evaluate-pipeline-output
**Description:** Thoroughly evaluate contact-center-lab pipeline output quality against...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/SKILL
```

---

#### /leak-risk-audit
**Description:** Audit a dataset for proprietary information leaks before sharing with...
**Arguments:** <path> [--output <filename>] [--glossary <path>]
**Output:** Generated output file
**Example:**
```
/SKILL
```

---

#### /plan-gate
**Description:** Before starting complex multi-step implementation tasks, assess scope and...
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/SKILL
```

---

#### /prime
**Description:** Evaluate an existing codebase to produce a detailed report on project...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/SKILL
```

---

#### /research-topic
**Description:** Orchestrate parallel deep research across multiple LLM providers and...
**Arguments:** Research request (provided by user as $ARGUMENTS or in conversation) [--sources <list>] [--depth <level>] [--format <type>] [--no-clarify] [--no-audience] [--skip-model-check]
**Output:** In-conversation output
**Example:**
```
/SKILL
```

---

#### /security-analysis
**Description:** Comprehensive security analysis with tech stack detection, vulnerability...
**Arguments:** [<path>] [--quick] [--dependencies-only]
**Output:** reports/security-analysis-[YYYYMMDD-HHMMSS].md
**Example:**
```
/SKILL
```

---

#### /ship
**Description:** Create branch, commit, push, open PR, auto-review, fix issues, and merge
**Arguments:** [<branch-name>] [draft] [--dry-run] [--audit]
**Output:** Generated output file
**Example:**
```
/SKILL
```

---

#### /spec-to-prototype
**Description:** Use when the user has a spec document, design system reference, component...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/SKILL
```

---

#### /summarize-feedback
**Description:** Synthesize employee feedback from Notion Voice Captures into a professional...
**Arguments:** employee_name="..." [days=N] [start_date=YYYY-MM-DD] [end_date=YYYY-MM-DD] [output_path="..."]
**Output:** Generated output file
**Example:**
```
/SKILL
```

---

#### /unlock
**Description:** Load secrets from Bitwarden Secrets Manager into environment using bws CLI
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/SKILL
```

---

#### /validate-and-ship
**Description:** Validate plugins, clean repository, and ship changes in one automated workflow
**Arguments:** [--skip-validate] [--skip-cleanup] [--skip-ship] [--dry-run] [<branch-name>]
**Output:** Generated output file
**Example:**
```
/SKILL
```

---

#### /visual-explainer
**Description:** Transform text or documents into AI-generated infographic pages that explain...
**Arguments:** Input content (one of the following):
**Output:** In-conversation output
**Example:**
```
/SKILL
```

---

## Error Handling

If the requested command is not found:
```
Command '[name]' not found in personal-plugin.

Available commands:
  /analyze-transcript, /ask-questions, /assess-document, /bump-version, /clean-repo, /consolidate-documents, /convert-markdown, /create-plan, /define-questions, /develop-image-prompt, /finish-document, /implement-plan, /new-command, /new-skill, /plan-improvements, /plan-next, /remove-ip, /review-arch, /review-intent, /review-pr, /scaffold-plugin, /test-project, /validate-plugin

Available skills:
  /evaluate-pipeline-output, /leak-risk-audit, /plan-gate, /prime, /research-topic, /security-analysis, /ship, /spec-to-prototype, /summarize-feedback, /unlock, /validate-and-ship, /visual-explainer
```
