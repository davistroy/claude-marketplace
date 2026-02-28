---
name: help
description: Show available commands and skills in this plugin with usage information
---

# Help Skill

Display help information for the personal-plugin commands and skills.

**IMPORTANT:** This skill must be updated whenever commands or skills are added, changed, or removed from this plugin.

## Usage

```text
/help                          # Show all commands and skills
/help <command-name>           # Show detailed help for a specific command
```

## Mode 1: List All (no arguments)

When invoked without arguments, display this table:

```text
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
| /convert-hooks | Convert plugin hook bash scripts to PowerShell for Windows compatibility |
| /convert-markdown | Convert a markdown file to a nicely formatted Microsoft Word document |
| /create-plan | Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD,... |
| /define-questions | Extract questions and open items from documents to JSON |
| /develop-image-prompt | Generate detailed image generator prompts from content, optimized for 11x17... |
| /finish-document | Extract questions from a document, answer them interactively, and update the... |
| /implement-plan | Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic... |
| /new-command | Generate a new command file from a template with proper structure and... |
| /new-skill | Generate a new skill file with proper nested directory structure and required... |
| /plan-improvements | Analyze codebase and generate prioritized improvement recommendations with... |
| /plan-next | Analyze repo and recommend the next logical action |
| /remove-ip | Sanitize documents by removing company identifiers and non-public... |
| /review-arch | Quick architectural audit with technical debt assessment (read-only, no... |
| /review-intent | Determine original project intent and compare against current implementation,... |
| /review-pr | Structured PR review with security, performance, and code quality analysis |
| /scaffold-plugin | Create a new plugin with proper directory structure, metadata, and starter files |
| /setup-statusline | Custom status line setup (Windows/PowerShell) |
| /test-project | Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then... |
| /validate-plugin | Validate plugin structure, frontmatter, and content for consistency and... |

SKILLS
------
| Skill | Description |
|-------|-------------|
| /help | Show available commands and skills in this plugin with usage information |
| /plan-gate | Assess task complexity and route to the right planning approach (native plan mode, /plan-improvements, or /create-plan) |
| /prime | Evaluate a codebase to produce a detailed report on project purpose, health, status, and next steps |
| /research-topic | Orchestrate parallel deep research across multiple LLM providers and synthesize results |
| /security-analysis | Comprehensive security vulnerability scanning and analysis with technology-specific patterns |
| /ship | Create branch, commit, push, open PR, auto-review, fix issues, and merge (GitHub and Gitea) |
| /summarize-feedback | Synthesize employee feedback from Notion Voice Captures into a professional .docx assessment document |
| /unlock | Load secrets from Bitwarden Secrets Manager into environment using bws CLI |
| /validate-and-ship | Validate plugins, clean repository, and ship changes in one automated workflow |
| /visual-explainer | Transform text or documents into AI-generated images that explain concepts visually |

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
```text
/analyze-transcript meeting-notes.txt
/analyze-transcript transcript.md --format json
```

---

#### /ask-questions
**Description:** Interactive Q&A session from questions JSON file
**Arguments:** <questions-file> [--force]
**Output:** Generated output file
**Example:**
```text
/ask-questions questions-PRD-20260110.json
```

---

#### /assess-document
**Description:** Document quality evaluation with scored assessment report
**Arguments:** <document-path> [--format [md|json]]
**Output:** Files in reports/
**Example:**
```text
/assess-document
/assess-document PRD.md
```

---

#### /bump-version
**Description:** Automate version bumping across plugin files with CHANGELOG placeholder
**Arguments:** <plugin-name> <bump-type> [--dry-run]
**Output:** In-conversation output
**Example:**
```text
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
```text
/check-updates --verbose
```

---

#### /clean-repo
**Description:** Comprehensive repository cleanup, organization, and documentation refresh
**Arguments:** [--dry-run] [--audit] [--docs-only]
**Output:** In-conversation report with cleanup summary
**Example:**
```text
/clean-repo                    # Full cleanup with documentation sync
/clean-repo --docs-only        # Focus only on documentation updates
/clean-repo --dry-run          # Preview changes without executing
```

---

#### /consolidate-documents
**Description:** Analyze multiple document variations and synthesize a superior consolidated...
**Arguments:** <doc1-path> <doc2-path> [doc3-path...]
**Output:** consolidated-[topic]-YYYYMMDD-HHMMSS.md
**Example:**
```text
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
```text
/convert-markdown requires pandoc for document conversion.
```


---

#### /convert-hooks
**Description:** Convert plugin hook bash scripts to PowerShell for Windows compatibility
**Arguments:** <plugin-name> [--dry-run] [--verbose] [--list]
**Output:** PowerShell scripts and updated hooks.json
**Example:**
```text
/convert-hooks my-plugin              # Convert hooks for a plugin
/convert-hooks my-plugin --dry-run    # Preview changes
/convert-hooks --list                 # Show plugins with hooks
```

---

#### /create-plan
**Description:** Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs)
**Arguments:** [<document-paths>] [--output <path>] [--phases <n>] [--verbose]
**Output:** IMPLEMENTATION_PLAN.md in repository root
**Example:**
```text
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
```text
/define-questions
/define-questions PRD.md
```

---

#### /develop-image-prompt
**Description:** Generate detailed image generator prompts from content, optimized for 11x17...
**Arguments:** <content-source> [--style <style-file>]
**Output:** Generated output file
**Example:**
```text
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
```text
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
```text
/implement-plan
```

---

#### /new-command
**Description:** Generate a new command file from a template with proper structure and...
**Arguments:** [<command-name>] [<pattern-type>]
**Output:** plugins/personal-plugin/commands/[command-name].md
**Example:**
```text
/new-command
```

---

#### /new-skill
**Description:** Generate a new skill file with proper nested directory structure and required frontmatter
**Arguments:** [<skill-name>]
**Output:** plugins/personal-plugin/skills/[skill-name]/SKILL.md
**Example:**
```text
/new-skill                    # Interactive mode
/new-skill quick-test         # With skill name
```
**Key Differences from /new-command:**
- Creates nested directory: `skills/[name]/SKILL.md`
- Includes required `name` field in frontmatter
- Skills are for proactive suggestions, commands are user-initiated

---

#### /plan-improvements
**Description:** Analyze codebase and generate prioritized improvement recommendations with...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```text
/plan-improvements
```

---

#### /plan-next
**Description:** Analyze repo and recommend the next logical action
**Arguments:** None required
**Output:** Generated output file
**Example:**
```text
/plan-next
```

---

#### /remove-ip
**Description:** Sanitize documents by removing company identifiers and non-public...
**Arguments:** <document-path> [--company <name>] [--mode [standard|strict]]
**Output:** Generated output file
**Example:**
```text
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
```text
/review-arch
```

---

#### /review-intent
**Description:** Determine original project intent and compare against current implementation, reporting discrepancies
**Arguments:** [<path>] [--deep]
**Output:** In-conversation output (intent profile, scorecard, discrepancy report)
**Example:**
```text
/review-intent                # Full repo intent analysis
/review-intent --deep         # Include git history analysis
/review-intent src/api        # Scoped to specific directory
```

---

#### /review-pr
**Description:** Structured PR review with security, performance, and code quality analysis
**Arguments:** <pr-number-or-url>
**Output:** In-conversation output
**Example:**
```text
/review-pr 123                                    # Review PR #123
/review-pr https://github.com/owner/repo/pull/42 # Review from URL
```

---

#### /scaffold-plugin
**Description:** Create a new plugin with proper directory structure, metadata, and starter files
**Arguments:** [<plugin-name>]
**Output:** plugins/[plugin-name]/.claude-plugin/plugin.json
**Example:**
```text
/scaffold-plugin
```

---

#### /setup-statusline
**Description:** "[Personal] Troy's custom status line setup (Windows/PowerShell)"
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```text
/setup-statusline
```

---

#### /test-project
**Description:** Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then...
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```text
/test-project
```

---

#### /validate-plugin
**Description:** Validate plugin structure, frontmatter, and content for consistency and...
**Arguments:** <plugin-name> [--all] [--fix] [--verbose]
**Output:** In-conversation output
**Example:**
```text
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
```text
/help                          # Show all commands and skills
/help <command-name>           # Show detailed help for a specific command
```

---

#### /plan-gate
**Description:** Assess task complexity and route to the right planning approach
**Arguments:** None (fires proactively based on task signals)
**Output:** In-conversation scope assessment with recommended planning path
**Features:**
- Proactive — fires automatically before complex implementation tasks
- Routes to: native plan mode, /plan-improvements, /create-plan, or /implement-plan
- Detects existing planning artifacts (IMPLEMENTATION_PLAN.md, requirements docs)
- Completes in under 10 seconds — routing decision, not deep analysis
**Paths:**
- Path A: Just do it (trivial tasks, 1-3 files)
- Path B: Native plan mode (moderate tasks, 4-8 files)
- Path C: /plan-improvements (multi-phase codebase refactoring)
- Path D: /create-plan (requirements docs exist)
- Path E: /implement-plan (existing plan with incomplete items)
- Path F: Ask clarifying questions (ambiguous scope)
**Example:**
```text
# Fires automatically when you say something like:
"Refactor the authentication system"
"Build the features described in the PRD"
"Let's keep working on the implementation"
```

---

#### /prime
**Description:** Evaluate a codebase to produce a detailed report on project purpose, health, status, and next steps
**Arguments:** [<focus-area>] [<path>]
**Output:** In-conversation structured report (Project Prime Report)
**Features:**
- Project identity: type, language, purpose, dependencies
- Repository health: git history, activity level, open work
- Code quality: architecture, test coverage, CI/CD, linting
- Documentation grade (A-F) across 5 dimensions
- Risk assessment: critical/high/medium/low categorization
- Prioritized next steps with suggested first task
**Example:**
```text
/prime                          # Full project evaluation
/prime testing                  # Focus on testing infrastructure
/prime plugins/bpmn-plugin      # Scope to a subdirectory
```

---

#### /research-topic
**Description:** Orchestrate parallel deep research across multiple LLM providers and synthesize results
**Arguments:** <research-request> [--sources <claude,openai,gemini>] [--depth <brief|standard|comprehensive>] [--format <md|docx|both>] [--no-clarify] [--no-audience]
**Output:** reports/research-[topic]-YYYYMMDD-HHMMSS.md and .docx
**Features:**
- Detects audience profile from CLAUDE.md files (project/local/global)
- Interactive API key setup wizard if .env missing
- Creates .env file with collected keys
**Example:**
```text
/research-topic What are the best practices for implementing RAG systems?
/research-topic --sources claude,openai --depth comprehensive "Compare transformer architectures"
/research-topic --depth brief --no-clarify --no-audience "Current state of quantum computing"
```

---

#### /security-analysis
**Description:** Comprehensive security vulnerability scanning and analysis with technology-specific patterns
**Arguments:** None required (auto-detects technology stack)
**Output:** Security Analysis Report (in-conversation or markdown)
**Features:**
- Auto-detects technology stack (Node.js, Python, Java, PHP, Go, .NET, Rust, React, Vue, NestJS, Next.js, React Native)
- OWASP Top 10 vulnerability scanning
- Dependency vulnerability analysis with native audit tools
- Context-aware risk assessment with CVSS scoring
- Remediation roadmap with prioritized fixes
**Example:**
```text
/security-analysis
```

---

#### /ship
**Description:** Create branch, commit, push, open PR, auto-review, fix issues, and merge (GitHub and Gitea)
**Arguments:** [<branch-name>] [draft] [--dry-run] [--audit]
**Platform:** Auto-detects GitHub (gh) or Gitea (tea) from git remote
**Output:** Generated output file
**Example:**
```text
/ship
```

---

#### /summarize-feedback
**Description:** Synthesize employee feedback from Notion Voice Captures into a professional .docx assessment document
**Arguments:** employee_name="..." [days=N] [start_date=YYYY-MM-DD] [end_date=YYYY-MM-DD] [output_path="..."]
**Output:** ./output/Feedback_Summary_{Name}_{datetime}.docx
**Prerequisites:** Notion MCP server, python-docx>=1.0
**Example:**
```text
/summarize-feedback employee_name="Sarah Chen"
/summarize-feedback employee_name="Sarah Chen" days=180
/summarize-feedback employee_name="Sarah Chen" start_date=2025-07-01 end_date=2026-01-27
/summarize-feedback employee_name="Sarah Chen" output_path="./reviews/sarah_q4.docx"
```

---

#### /unlock
**Description:** Load secrets from Bitwarden Secrets Manager into environment using bws CLI
**Arguments:** None required
**Output:** In-conversation output (environment variables set)
**Example:**
```text
/unlock
# Loaded 8 secret(s) from Bitwarden Secrets Manager:
#   ANTHROPIC_API_KEY
#   OPENAI_API_KEY
#   GOOGLE_API_KEY
#   ...
```

---

#### /validate-and-ship
**Description:** Validate plugins, clean repository, and ship changes in one automated workflow
**Arguments:** [--skip-validate] [--skip-cleanup] [--dry-run] [<branch-name>]
**Output:** In-conversation output with PR URL on success
**Example:**
```text
/validate-and-ship                      # Full workflow: validate → cleanup → ship
/validate-and-ship feat/my-feature      # With custom branch name
/validate-and-ship --dry-run            # Preview all phases without executing
/validate-and-ship --skip-validate      # Skip validation, run cleanup and ship
```
**Workflow:**
1. **Phase 1**: Run `/validate-plugin --all` (stops on errors, continues on warnings)
2. **Phase 2**: Run `/clean-repo` (auto-executes artifact cleanup)
3. **Phase 3**: Run `/ship` (full git workflow with auto-review and merge)

---

#### /visual-explainer
**Description:** Transform text or documents into AI-generated images that explain concepts visually
**Arguments:** <input> [--style <name>] [--output-dir <path>] [--max-iterations <n>] [--pass-threshold <0-1>] [--image-count <n>] [--aspect-ratio <ratio>] [--resolution <level>] [--no-cache] [--dry-run] [--resume <checkpoint>] [--setup-keys]
**Output:** visual-explainer-[topic]-[timestamp]/ directory with images, metadata, and summary
**Features:**
- Uses Gemini Pro 3 for 4K image generation
- Claude Sonnet Vision for quality evaluation
- Iterative refinement with escalating strategies
- Checkpoint/resume for long-running generations
- Interactive mode for style and image count selection
**Example:**
```text
/visual-explainer "How does photosynthesis work?"
/visual-explainer architecture.md --style professional-sketch --image-count 5
/visual-explainer --resume checkpoint.json
/visual-explainer --dry-run "Explain microservices patterns"
```

---

## Error Handling

If the requested command is not found:
```text
Command '[name]' not found in personal-plugin.

Available commands:
  /analyze-transcript, /ask-questions, /assess-document, /bump-version, /check-updates, /clean-repo, /consolidate-documents, /convert-hooks, /convert-markdown, /create-plan, /define-questions, /develop-image-prompt, /finish-document, /implement-plan, /new-command, /new-skill, /plan-improvements, /plan-next, /remove-ip, /review-arch, /review-intent, /review-pr, /scaffold-plugin, /setup-statusline, /test-project, /validate-plugin

Available skills:
  /help, /plan-gate, /prime, /research-topic, /security-analysis, /ship, /summarize-feedback, /unlock, /validate-and-ship, /visual-explainer
```
