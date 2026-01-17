---
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
| /check-updates | Check for available plugin updates by comparing installed versions to... |
| /clean-repo | Comprehensive repository cleanup, organization, and documentation refresh |
| /consolidate-documents | Analyze multiple document variations and synthesize a superior consolidated... |
| /convert-markdown | Convert a markdown file to a nicely formatted Microsoft Word document |
| /create-plan | Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD,... |
| /define-questions | Extract questions and open items from documents to JSON |
| /develop-image-prompt | Generate detailed image generator prompts from content, optimized for 11x17... |
| /finish-document | Extract questions from a document, answer them interactively, and update the... |
| /implement-plan | Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic... |
| /new-command | Generate a new command file from a template with proper structure and... |
| /plan-improvements | Analyze codebase and generate prioritized improvement recommendations with... |
| /plan-next | Analyze repo and recommend the next logical action |
| /remove-ip | Sanitize documents by removing company identifiers and non-public... |
| /review-arch | Quick architectural audit with technical debt assessment (read-only, no... |
| /review-pr | Structured PR review with security, performance, and code quality analysis |
| /scaffold-plugin | Create a new plugin with proper directory structure, metadata, and starter files |
| /setup-statusline | "[Personal] Troy's custom status line setup (Windows/PowerShell)" |
| /test-project | Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then... |
| /validate-plugin | Validate plugin structure, frontmatter, and content for consistency and... |

SKILLS
------
| Skill | Description |
|-------|-------------|
| /help | Show available commands and skills in this plugin with usage information |
| /research-topic | Orchestrate parallel deep research across multiple LLM providers and synthesize results |
| /ship | Create branch, commit, push, open PR, auto-review, fix issues, and merge |

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
/bump-version personal-plugin minor    # 1.6.0 -> 1.7.0
/bump-version bpmn-plugin patch        # 1.5.0 -> 1.5.1
/bump-version personal-plugin major    # 1.6.0 -> 2.0.0
```

---

#### /check-updates
**Description:** Check for available plugin updates by comparing installed versions to...
**Arguments:** [--verbose]
**Output:** Generated output file
**Example:**
```
/check-updates --verbose
```

---

#### /clean-repo
**Description:** Comprehensive repository cleanup, organization, and documentation refresh
**Arguments:** [--dry-run] [--audit]
**Output:** Generated output file
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
/consolidate-documents draft-v1.md draft-v2.md
/consolidate-documents spec-a.md spec-b.md spec-c.md
/consolidate-documents requirements-old.md requirements-new.md updates.md
```

---

#### /convert-markdown
**Description:** Convert a markdown file to a nicely formatted Microsoft Word document
**Arguments:** <markdown-file> [<output-file>]
**Output:** In-conversation output
**Example:**
```
/convert-markdown requires pandoc for document conversion.
```

---

#### /create-plan
**Description:** Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs)
**Arguments:** [<document-paths>] [--output <path>] [--phases <n>] [--verbose]
**Output:** IMPLEMENTATION_PLAN.md in repository root
**Example:**
```
/create-plan                              # Auto-discover documents
/create-plan PRD.md TDD.md               # Use specific documents
/create-plan --phases 5                   # Target 5 phases
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
**Description:** Generate detailed image generator prompts from content, optimized for 11x17...
**Arguments:** <content-source> [--style <style-file>]
**Output:** Generated output file
**Example:**
```
/develop-image-prompt architecture.md
/develop-image-prompt process-flow.md --style brand-guidelines.md
/develop-image-prompt "microservices communication patterns"
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
**Description:** Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic testing, documentation, and git workflow
**Arguments:** None required
**Output:** Updates IMPLEMENTATION_PLAN.md, PROGRESS.md, LEARNINGS.md; creates and merges PR
**Example:**
```
/implement-plan
```

---

#### /new-command
**Description:** Generate a new command file from a template with proper structure and...
**Arguments:** [<command-name>] [<pattern-type>]
**Output:** plugins/personal-plugin/commands/[command-name].md
**Example:**
```
/new-command
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
/remove-ip playbook.md --company "Acme Corp" --industry "Finance"
```

---

#### /review-arch
**Description:** Quick architectural audit with technical debt assessment (read-only, no...
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/review-arch
```

---

#### /review-pr
**Description:** Structured PR review with security, performance, and code quality analysis
**Arguments:** <pr-number-or-url>
**Output:** In-conversation output
**Example:**
```
/review-pr 123                                    # Review PR #123
/review-pr https://github.com/owner/repo/pull/42 # Review from URL
```

---

#### /scaffold-plugin
**Description:** Create a new plugin with proper directory structure, metadata, and starter files
**Arguments:** [<plugin-name>]
**Output:** plugins/[plugin-name]/.claude-plugin/plugin.json
**Example:**
```
/scaffold-plugin
```

---

#### /setup-statusline
**Description:** "[Personal] Troy's custom status line setup (Windows/PowerShell)"
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/setup-statusline
```

---

#### /test-project
**Description:** Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then...
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/test-project
```

---

#### /validate-plugin
**Description:** Validate plugin structure, frontmatter, and content for consistency and...
**Arguments:** <plugin-name> [--all] [--fix] [--verbose]
**Output:** In-conversation output
**Example:**
```
/validate-plugin personal-plugin          # Validate single plugin
/validate-plugin --all                    # Validate all plugins
/validate-plugin bpmn-plugin --verbose    # Detailed output
```

---

#### /help
**Description:** Show available commands and skills in this plugin with usage information
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/help                          # Show all commands and skills
/help <command-name>           # Show detailed help for a specific command
```

---

#### /research-topic
**Description:** Orchestrate parallel deep research across multiple LLM providers and synthesize results
**Arguments:** <research-request> [--sources <claude,openai,gemini>] [--depth <brief|standard|comprehensive>] [--format <md|docx|both>] [--no-clarify]
**Output:** reports/research-[topic]-YYYYMMDD-HHMMSS.md and .docx
**Example:**
```
/research-topic What are the best practices for implementing RAG systems?
/research-topic --sources claude,openai --depth comprehensive "Compare transformer architectures"
/research-topic --depth brief --no-clarify "Current state of quantum computing"
```

---

#### /ship
**Description:** Create branch, commit, push, open PR, auto-review, fix issues, and merge
**Arguments:** [<branch-name>] [draft] [--dry-run] [--audit]
**Output:** Generated output file
**Example:**
```
/ship
```

---

## Error Handling

If the requested command is not found:
```
Command '[name]' not found in personal-plugin.

Available commands:
  /analyze-transcript, /ask-questions, /assess-document, /bump-version, /check-updates, /clean-repo, /consolidate-documents, /convert-markdown, /create-plan, /define-questions, /develop-image-prompt, /finish-document, /implement-plan, /new-command, /plan-improvements, /plan-next, /remove-ip, /review-arch, /review-pr, /scaffold-plugin, /setup-statusline, /test-project, /validate-plugin

Available skills:
  /help, /research-topic, /ship
```
