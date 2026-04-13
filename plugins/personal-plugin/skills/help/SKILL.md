---
name: help
description: Show available commands and skills in this plugin with usage information
---

# Help Skill

Display help information for the personal-plugin commands and skills.

**Note:** This skill uses a static table that must be manually updated when commands or skills are added, changed, or removed.

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
| /release-plugin | Validate plugins, clean repository, and ship plugin releases in one automated workflow |
| /visual-explainer | Transform text or documents into AI-generated infographic pages that explain... |
| /accessibility-annotator | Analyze technical documents and add explanation annotations for non-CS... |
| /brain-entry | Send a capture to Open Brain — summarize sessions, log decisions, capture ideas |
| /create-wiki | Set up a persistent LLM-maintained wiki inside any project with auto-maintenance rules |
| /explain-project | Generate comprehensive annotated technical overview for non-technical... |
| /lab-notebook | Initialize mandatory experiment logging with scientific notebook, ADR, and... |
| /spark-recon | Use when checking on DGX Spark inference performance landscape |
| /ultra-plan | Deep investigation, interaction mapping, and integrated solution design for... |
| /wiki | Wiki operations: ingest sources, lint health, query topics, show status |
| /jetson-audit | Audit Jetson Orin Nano running inference config against best practices |
| /jetson-recon | Periodic Jetson Orin Nano inference performance landscape scan |
| /spark-audit | Audit DGX Spark running containers against best practices |

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
/evaluate-pipeline-output ./output/run-2026-03-31
```

---

#### /leak-risk-audit
**Description:** Audit a dataset for proprietary information leaks before sharing with...
**Arguments:** <path> [--output <filename>] [--glossary <path>]
**Output:** Generated output file
**Example:**
```
/leak-risk-audit ./data/export-2026-03-31/
/leak-risk-audit ./dataset.jsonl --glossary terms.json
```

---

#### /plan-gate
**Description:** Before starting complex multi-step implementation tasks, assess scope and...
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/plan-gate
```

---

#### /prime
**Description:** Evaluate an existing codebase to produce a detailed report on project...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/prime
/prime /path/to/repo
```

---

#### /research-topic
**Description:** Orchestrate parallel deep research across multiple LLM providers and...
**Arguments:** Research request (provided by user as $ARGUMENTS or in conversation) [--sources <list>] [--depth <level>] [--format <type>] [--no-clarify] [--no-audience] [--skip-model-check]
**Output:** In-conversation output
**Example:**
```
/research-topic "comparison of vLLM vs TensorRT-LLM for GB10"
/research-topic --depth deep --sources anthropic,openai "RAG vs fine-tuning tradeoffs"
```

---

#### /security-analysis
**Description:** Comprehensive security analysis with tech stack detection, vulnerability...
**Arguments:** [<path>] [--quick] [--dependencies-only]
**Output:** reports/security-analysis-[YYYYMMDD-HHMMSS].md
**Example:**
```
/security-analysis
/security-analysis --quick --dependencies-only
```

---

#### /ship
**Description:** Create branch, commit, push, open PR, auto-review, fix issues, and merge
**Arguments:** [<branch-name>] [draft] [--dry-run] [--audit]
**Output:** Generated output file
**Example:**
```
/ship feat/my-branch
/ship feat/quick-fix draft
```

---

#### /spec-to-prototype
**Description:** Use when the user has a spec document, design system reference, component...
**Arguments:** None required
**Output:** Generated output file
**Example:**
```
/spec-to-prototype ./docs/wireframe-spec.md
/spec-to-prototype ./design-system.md
```

---

#### /summarize-feedback
**Description:** Synthesize employee feedback from Notion Voice Captures into a professional...
**Arguments:** employee_name="..." [days=N] [start_date=YYYY-MM-DD] [end_date=YYYY-MM-DD] [output_path="..."]
**Output:** Generated output file
**Example:**
```
/summarize-feedback employee_name="Jane Doe" days=30
/summarize-feedback employee_name="John Smith" start_date=2026-03-01 end_date=2026-03-31
```

---

#### /unlock
**Description:** Load secrets from Bitwarden Secrets Manager into environment using bws CLI
**Arguments:** None required
**Output:** In-conversation output
**Example:**
```
/unlock
```

---

#### /release-plugin
**Description:** Validate plugins, clean repository, and ship plugin releases in one automated workflow
**Arguments:** [--skip-validate] [--skip-cleanup] [--skip-ship] [--dry-run] [<branch-name>]
**Output:** Generated output file
**Example:**
```
/release-plugin --dry-run
/release-plugin feat/v7-release
```

---

#### /visual-explainer
**Description:** Transform text or documents into AI-generated infographic pages that explain...
**Arguments:** Input content (one of the following):
**Output:** In-conversation output
**Example:**
```
/visual-explainer ./docs/architecture-overview.md
/visual-explainer "How container orchestration works"
```

---

#### /accessibility-annotator
**Description:** Analyze technical documents for CS/ML concepts and add explanation annotations for non-CS readers
**Arguments:** <document-path>
**Output:** Updated document with annotations
**Example:**
```
/accessibility-annotator technical-report.docx
```

---

#### /brain-entry
**Description:** Send a capture to Open Brain — summarize sessions, log decisions, capture ideas
**Arguments:** <instruction> (what to generate and send)
**Output:** POST to Open Brain captures API
**Example:**
```
/brain-entry summarize everything we did in this session
/brain-entry log a decision: we chose Cloudflare for email ingestion
```

---

#### /create-wiki
**Description:** Set up a persistent LLM-maintained wiki inside any project with auto-maintenance rules
**Arguments:** [init | status] (default: auto-detect)
**Output:** wiki/ directory with sources/, pages/, schema, index, log, README + CLAUDE.md injection
**Example:**
```
/create-wiki
/create-wiki init
```

---

#### /explain-project
**Description:** Generate comprehensive annotated technical overview document for non-technical stakeholders
**Arguments:** [<project-path>]
**Output:** Generated Word document with annotations, glossary, and sidebars
**Example:**
```
/explain-project
/explain-project /path/to/repo
```

---

#### /lab-notebook
**Description:** Initialize mandatory experiment logging for projects involving system changes, benchmarks, debugging, or exploratory work
**Arguments:** None required
**Output:** LAB_NOTEBOOK.md and CLAUDE.md injection with logging rules
**Example:**
```
/lab-notebook
```

---

#### /spark-recon
**Description:** Periodic DGX Spark performance landscape scan — Arena leaderboard, vLLM releases, spark-vllm-docker builds, Qwen models, and NVIDIA forum
**Arguments:** None required
**Output:** Console report + LAB_NOTEBOOK.md entry + SPARK_BASELINE.md update (with confirmation)
**Example:**
```
/spark-recon
```

---

#### /ultra-plan
**Description:** Deep investigation, interaction mapping, and integrated solution design for bug lists, feature requests, or change sets. Produces a formal IMPLEMENTATION_PLAN.md via /create-plan.
**Arguments:** Provide a bug list, feature request list, change set, or review document
**Output:** IMPLEMENTATION_PLAN.md (via /create-plan after approval)
**Example:**
```
/ultra-plan
/ultra-plan Here are 5 bugs found during testing: [list]
```

---

#### /wiki
**Description:** Wiki operations: ingest source documents, lint health, query topics, show status
**Arguments:** <subcommand> [args]
**Output:** Varies by subcommand
**Subcommands:**
  - `ingest <path>` — Process a source document into wiki pages
  - `lint` — Run health checks on wiki structure and content
  - `query <topic>` — Search wiki and synthesize an answer
  - `status` — Show wiki stats, health, and recent activity
**Example:**
```
/wiki ingest docs/architecture-spec.md
/wiki lint
/wiki query "authentication flow"
/wiki status
```

---

#### /jetson-audit
**Description:** Audit Jetson Orin Nano running inference config against best practices and community optimizations
**Arguments:** None required
**Output:** Console report with gaps, misconfigurations, and optimization opportunities
**Example:**
```
/jetson-audit
```

---

#### /jetson-recon
**Description:** Periodic Jetson Orin Nano inference performance landscape scan — JetPack updates, llama.cpp releases, small models, NVIDIA forum
**Arguments:** None required
**Output:** Console report + LAB_NOTEBOOK.md entry
**Example:**
```
/jetson-recon
```

---

#### /spark-audit
**Description:** Audit DGX Spark running containers against best practices and community optimizations
**Arguments:** None required
**Output:** Console report with gaps, misconfigurations, and optimization opportunities
**Example:**
```
/spark-audit
```

---

## Error Handling

If the requested command is not found:
```
Command '[name]' not found in personal-plugin.

Available commands:
  /analyze-transcript, /ask-questions, /assess-document, /bump-version, /clean-repo, /consolidate-documents, /convert-markdown, /create-plan, /define-questions, /develop-image-prompt, /finish-document, /implement-plan, /new-command, /new-skill, /plan-improvements, /plan-next, /remove-ip, /review-arch, /review-intent, /review-pr, /scaffold-plugin, /test-project, /validate-plugin

Available skills:
  /accessibility-annotator, /brain-entry, /create-wiki, /evaluate-pipeline-output, /explain-project, /jetson-audit, /jetson-recon, /lab-notebook, /leak-risk-audit, /plan-gate, /prime, /release-plugin, /research-topic, /security-analysis, /ship, /spark-audit, /spark-recon, /spec-to-prototype, /summarize-feedback, /ultra-plan, /unlock, /visual-explainer, /wiki
```
