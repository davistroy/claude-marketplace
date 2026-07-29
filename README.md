# Claude Marketplace

[![Plugin Validation](https://github.com/davistroy/claude-marketplace/actions/workflows/validate.yml/badge.svg)](https://github.com/davistroy/claude-marketplace/actions/workflows/validate.yml)
[![Tests](https://github.com/davistroy/claude-marketplace/actions/workflows/test.yml/badge.svg)](https://github.com/davistroy/claude-marketplace/actions/workflows/test.yml)

A collection of Claude Code plugins containing custom slash commands and skills for documentation review, architecture analysis, git workflows, document processing, security analysis, multi-LLM research, visual explanation generation, and BPMN workflow generation.

## Installation

### Add the Marketplace

First, add this marketplace to Claude Code:

```text
/plugin marketplace add davistroy/claude-marketplace
```

### Install Plugins

Then install the plugins you want:

```text
/plugin install personal-plugin@troys-plugins
/plugin install bpmn-plugin@troys-plugins
```

### Installation Scopes

You can install to different scopes:

```text
/plugin install personal-plugin@troys-plugins --scope user      # Global (all projects)
/plugin install personal-plugin@troys-plugins --scope project   # Team-shared (.claude/settings.json)
/plugin install personal-plugin@troys-plugins --scope local     # Personal only (gitignored)
```

## Available Plugins

### personal-plugin

23 commands and 29 skills for productivity workflows, code review, document processing, and security analysis.

**23 Commands:**
| Command | Description |
|---------|-------------|
| [`/analyze-transcript`](plugins/personal-plugin/commands/analyze-transcript.md) | Meeting transcript to structured markdown report |
| [`/arch-review-single`](plugins/personal-plugin/commands/arch-review-single.md) | Run a single domain agent from the architecture review team against a target codebase |
| [`/arch-synthesize`](plugins/personal-plugin/commands/arch-synthesize.md) | Re-synthesize the executive summary from existing domain findings — use after editing findings, r... |
| [`/ask-questions`](plugins/personal-plugin/commands/ask-questions.md) | Interactive Q&A session from questions JSON file |
| [`/assess-document`](plugins/personal-plugin/commands/assess-document.md) | Document quality evaluation with scored assessment report |
| [`/bump-version`](plugins/personal-plugin/commands/bump-version.md) | Automate version bumping across plugin files with CHANGELOG placeholder |
| [`/clean-repo`](plugins/personal-plugin/commands/clean-repo.md) | Comprehensive repository cleanup, organization, and documentation refresh |
| [`/consolidate-documents`](plugins/personal-plugin/commands/consolidate-documents.md) | Analyze multiple document variations and synthesize a superior consolidated version (supports `--... |
| [`/convert-markdown`](plugins/personal-plugin/commands/convert-markdown.md) | Convert a markdown file to a nicely formatted Microsoft Word document |
| [`/create-plan`](plugins/personal-plugin/commands/create-plan.md) | Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs) |
| [`/define-questions`](plugins/personal-plugin/commands/define-questions.md) | Extract questions and open items from documents to JSON |
| [`/develop-image-prompt`](plugins/personal-plugin/commands/develop-image-prompt.md) | Generate detailed image generator prompts from content, with configurable dimensions and style op... |
| [`/finish-document`](plugins/personal-plugin/commands/finish-document.md) | Extract questions from a document, answer them interactively, and update the document |
| [`/implement-plan`](plugins/personal-plugin/commands/implement-plan.md) | Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic testing, documentation... |
| [`/new-skill`](plugins/personal-plugin/commands/new-skill.md) | Generate a new skill file with proper nested directory structure and required frontmatter |
| [`/plan-improvements`](plugins/personal-plugin/commands/plan-improvements.md) | Analyze codebase and generate prioritized improvement recommendations with phased implementation... |
| [`/plan-next`](plugins/personal-plugin/commands/plan-next.md) | Analyze repo and recommend the next logical action |
| [`/remove-ip`](plugins/personal-plugin/commands/remove-ip.md) | Sanitize documents by removing company identifiers and non-public intellectual property while pre... |
| [`/review-arch`](plugins/personal-plugin/commands/review-arch.md) | Quick architectural audit with technical debt assessment (read-only, no files generated) |
| [`/review-intent`](plugins/personal-plugin/commands/review-intent.md) | Determine original project intent and compare against current implementation, reporting discrepan... |
| [`/scaffold-plugin`](plugins/personal-plugin/commands/scaffold-plugin.md) | Create a new plugin with proper directory structure, metadata, and starter files |
| [`/test-project`](plugins/personal-plugin/commands/test-project.md) | Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then create PR (merge onl... |
| [`/validate-plugin`](plugins/personal-plugin/commands/validate-plugin.md) | Validate plugin structure, frontmatter, and content for consistency and correctness (supports `--... |

**29 Skills:**
| Skill | Description |
|-------|-------------|
| [`/accessibility-annotator`](plugins/personal-plugin/skills/accessibility-annotator/SKILL.md) | Analyze technical documents for CS/ML concepts a smart non-CS reader wouldn't understand, recomme... |
| [`/arch-review`](plugins/personal-plugin/skills/arch-review/SKILL.md) | Comprehensive 9-agent architecture review — spawns parallel domain specialists (architecture, cod... |
| [`/archive-project`](plugins/personal-plugin/skills/archive-project/SKILL.md) | Archive, retire, or sunset a project repo — writes a status header into README.md, tags and commi... |
| [`/brain-entry`](plugins/personal-plugin/skills/brain-entry/SKILL.md) | Send a capture to Open Brain. |
| [`/clear-prep`](plugins/personal-plugin/skills/clear-prep/SKILL.md) | Prepare a project for a context clear (/clear) or compaction with zero loss of state. |
| [`/create-wiki`](plugins/personal-plugin/skills/create-wiki/SKILL.md) | Set up a persistent, LLM-maintained wiki inside any project. |
| [`/evaluate-pipeline-output`](plugins/personal-plugin/skills/evaluate-pipeline-output/SKILL.md) | Thoroughly evaluate contact-center-lab pipeline output quality against input, checking sanitizati... |
| [`/explain-project`](plugins/personal-plugin/skills/explain-project/SKILL.md) | Generate a comprehensive, annotated technical overview document for any project/repo, written for... |
| [`/fleet-health`](plugins/personal-plugin/skills/fleet-health/SKILL.md) | One-shot, read-only health snapshot across the personal fleet (DGX Spark, Jetson Orin Nano, homes... |
| [`/jetson-audit`](plugins/personal-plugin/skills/jetson-audit/SKILL.md) | SSH into the Jetson Orin Nano and audit the running inference config against known best practices... |
| [`/jetson-recon`](plugins/personal-plugin/skills/jetson-recon/SKILL.md) | Recon of the Jetson Orin Nano inference-performance landscape — scans JetPack updates, llama.cpp... |
| [`/lab-notebook`](plugins/personal-plugin/skills/lab-notebook/SKILL.md) | Initialize mandatory experiment logging using scientific notebook, ADR, and postmortem patterns. |
| [`/leak-risk-audit`](plugins/personal-plugin/skills/leak-risk-audit/SKILL.md) | Audit a dataset for proprietary information leaks before sharing with public/cloud services. |
| [`/new-project`](plugins/personal-plugin/skills/new-project/SKILL.md) | Scaffold a brand-new project directory end-to-end — git init, remote repository (GitHub by defaul... |
| [`/plan-gate`](plugins/personal-plugin/skills/plan-gate/SKILL.md) | Before starting complex multi-step implementation tasks, assess scope and route to the right plan... |
| [`/prime`](plugins/personal-plugin/skills/prime/SKILL.md) | Evaluate an existing codebase to produce a detailed report on project purpose, health, status, an... |
| [`/release-plugin`](plugins/personal-plugin/skills/release-plugin/SKILL.md) | Validate plugins, clean the repository, and ship plugin releases in one automated workflow. |
| [`/research-topic`](plugins/personal-plugin/skills/research-topic/SKILL.md) | Orchestrate parallel deep research across multiple LLM providers using native context:fork subage... |
| [`/security-analysis`](plugins/personal-plugin/skills/security-analysis/SKILL.md) | Comprehensive security analysis with tech stack detection, vulnerability scanning, and remediatio... |
| [`/ship`](plugins/personal-plugin/skills/ship/SKILL.md) | Create branch, commit, push, open PR, auto-review, fix issues, and merge — the full ship workflow. |
| [`/spark-audit`](plugins/personal-plugin/skills/spark-audit/SKILL.md) | SSH into the DGX Spark and audit all running containers against known best practices and communit... |
| [`/spark-recon`](plugins/personal-plugin/skills/spark-recon/SKILL.md) | Recon of the DGX Spark inference-performance landscape — scans the Arena leaderboard, vLLM releas... |
| [`/spec-to-prototype`](plugins/personal-plugin/skills/spec-to-prototype/SKILL.md) | Use when the user has a spec document, design system reference, component library doc, wireframe... |
| [`/summarize-feedback`](plugins/personal-plugin/skills/summarize-feedback/SKILL.md) | Synthesize employee feedback from Notion Voice Captures into a professional .docx assessment docu... |
| [`/task-sync`](plugins/personal-plugin/skills/task-sync/SKILL.md) | Manage a local task/backlog list (tasks.json + a generated TASKS.md) for the current repo and rec... |
| [`/ultra-plan`](plugins/personal-plugin/skills/ultra-plan/SKILL.md) | "Structured implementation planning for bug lists, feature requests, or change sets. |
| [`/unlock`](plugins/personal-plugin/skills/unlock/SKILL.md) | Load secrets from Bitwarden Secrets Manager into the environment using the bws CLI. |
| [`/visual-explainer`](plugins/personal-plugin/skills/visual-explainer/SKILL.md) | Transform text or documents into AI-generated infographic pages that explain concepts visually, u... |
| [`/wiki`](plugins/personal-plugin/skills/wiki/SKILL.md) | "Wiki operations: ingest source documents into wiki pages, lint for health issues, query the wiki... |

### slide-gen

AI-assisted presentation generation pipeline: 7-step workflow from topic research to finished PowerPoint using Claude and Gemini.

**External dependency (required):** the pipeline skills wrap an `sg` CLI from the separate, currently **private** `davistroy/slide-generator` repo — `/plugin install slide-gen@troys-plugins` installs the skills only, not the engine, so the plugin is owner-only until that repo is made public. See [ADR-0008](docs/adr/0008-slide-gen-dependency-model.md) and the [slide-gen README](plugins/slide-gen/README.md) for details.

```text
/plugin install slide-gen@troys-plugins
```

**9 Skills:**
| Skill | Description |
|-------|-------------|
| [`/build-cfa-deck`](plugins/slide-gen/skills/build-cfa-deck/SKILL.md) | Generate a complete, on-brand Chick-fil-A PowerPoint presentation from a topic using CFA brand gu... |
| [`/sg-build`](plugins/slide-gen/skills/sg-build/SKILL.md) | Assemble final PowerPoint (.pptx) from presentation markdown and generated images. |
| [`/sg-draft`](plugins/slide-gen/skills/sg-draft/SKILL.md) | Draft full slide content (titles, bullets, speaker notes, graphics descriptions) from an outline. |
| [`/sg-full-workflow`](plugins/slide-gen/skills/sg-full-workflow/SKILL.md) | Run the complete 7-step slide generation pipeline from topic to PowerPoint. |
| [`/sg-generate-images`](plugins/slide-gen/skills/sg-generate-images/SKILL.md) | Generate slide visuals using Gemini Pro from validated graphics descriptions. |
| [`/sg-optimize`](plugins/slide-gen/skills/sg-optimize/SKILL.md) | Run quality analysis and automated improvement on drafted slide content. |
| [`/sg-outline`](plugins/slide-gen/skills/sg-outline/SKILL.md) | Generate a structured presentation outline from research findings. |
| [`/sg-research`](plugins/slide-gen/skills/sg-research/SKILL.md) | Conduct autonomous web research on a topic using Claude Agent SDK, producing structured research.... |
| [`/sg-validate-graphics`](plugins/slide-gen/skills/sg-validate-graphics/SKILL.md) | Validate that image descriptions are concrete enough for AI image generation. |

### bpmn-plugin

BPMN 2.0 workflow tools for generating and converting process diagrams.

**2 Skills:**
| Skill | Description |
|-------|-------------|
| [`/bpmn-generator`](plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md) | Generate BPMN 2.0 compliant XML files from natural language process descriptions OR from structur... |
| [`/bpmn-to-drawio`](plugins/bpmn-plugin/skills/bpmn-to-drawio/SKILL.md) | Convert BPMN 2.0 XML files into Draw.io native format (.drawio) using the bpmn2drawio Python tool. |

**BPMN Generator** operates in two modes:
- **Interactive Mode**: Structured Q&A to gather requirements from natural language descriptions
- **Document Parsing Mode**: Parse markdown documents to extract process elements

**BPMN to Draw.io Converter** produces:
- Proper swim lane structure (pools and lanes)
- BPMN-styled shapes for all element types
- Correct connector routing including cross-lane flows
- Color coding by lane function
- Editable diagrams for Draw.io Desktop and web

## Repository Structure

```text
.claude-plugin/
  marketplace.json          # Marketplace configuration

plugins/
  personal-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    commands/               # Slash commands
    skills/                 # Proactive skills
    hooks/                  # Workflow automation hooks
    references/             # Shared patterns and templates
    tools/                  # Bundled Python tools

  bpmn-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/                 # BPMN generator skills
    references/             # BPMN element documentation
    templates/              # XML templates and lane mappings
    examples/               # Sample BPMN files
    tools/                  # Bundled bpmn2drawio converter

  slide-gen/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/                 # sg-research, sg-outline, sg-draft, sg-optimize,
                            # sg-validate-graphics, sg-generate-images, sg-build, sg-full-workflow

.claude/
  agents/              # Named implementer agents for implement-plan model routing
                       # haiku-implementer, sonnet-implementer, opus-implementer —
                       # model: tier alias in frontmatter, never pinned IDs (ADR-0005)
```

## CI/CD Pipeline

The repository includes a comprehensive CI pipeline:

- **Plugin validation** - Structure, frontmatter, and content checks
- **Python linting** - Ruff lint + format enforcement (`ruff.toml` at repo root)
- **Dependency security** - `pip-audit` scans for known CVEs in all Python tools
- **Markdown linting** - Blocking markdownlint checks on all `.md` files
- **Cross-platform testing** - Python tool tests run on both Ubuntu and Windows
- **Test coverage** - pytest suites for all 4 bundled Python tools

## Documentation

- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - Essential patterns for plugin development
- [WORKFLOWS.md](WORKFLOWS.md) - How to chain commands for common use cases
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solutions to common issues
- [SECURITY.md](SECURITY.md) - Security model and vulnerability reporting

All commands include Performance and Examples sections for consistent documentation coverage.

## License

MIT
