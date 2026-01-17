# Claude Marketplace

[![Plugin Validation](https://github.com/davistroy/claude-marketplace/actions/workflows/validate.yml/badge.svg)](https://github.com/davistroy/claude-marketplace/actions/workflows/validate.yml)
[![Tests](https://github.com/davistroy/claude-marketplace/actions/workflows/test.yml/badge.svg)](https://github.com/davistroy/claude-marketplace/actions/workflows/test.yml)

A collection of Claude Code plugins containing custom slash commands and skills for documentation review, architecture analysis, git workflows, document processing, and BPMN workflow generation.

## Installation

### Add the Marketplace

First, add this marketplace to Claude Code:

```
/plugin marketplace add davistroy/claude-marketplace
```

### Install Plugins

Then install the plugins you want:

```
/plugin install personal-plugin@troys-plugins
/plugin install bpmn-plugin@troys-plugins
```

### Installation Scopes

You can install to different scopes:

```
/plugin install personal-plugin@troys-plugins --scope user      # Global (all projects)
/plugin install personal-plugin@troys-plugins --scope project   # Team-shared (.claude/settings.json)
/plugin install personal-plugin@troys-plugins --scope local     # Personal only (gitignored)
```

## Available Plugins

### personal-plugin

Custom commands and skills for productivity workflows.

**Commands:**
| Command | Description |
|---------|-------------|
| [`/analyze-transcript`](plugins/personal-plugin/commands/analyze-transcript.md) | Meeting transcript to structured markdown report |
| [`/ask-questions`](plugins/personal-plugin/commands/ask-questions.md) | Interactive Q&A session from questions JSON file |
| [`/assess-document`](plugins/personal-plugin/commands/assess-document.md) | Document quality evaluation with scored assessment report |
| [`/bump-version`](plugins/personal-plugin/commands/bump-version.md) | Automate version bumping across plugin files with CHANGELOG placeholder |
| [`/check-updates`](plugins/personal-plugin/commands/check-updates.md) | Check for available plugin updates by comparing installed versions to marketplace |
| [`/clean-repo`](plugins/personal-plugin/commands/clean-repo.md) | Comprehensive repository cleanup, organization, and documentation refresh |
| [`/consolidate-documents`](plugins/personal-plugin/commands/consolidate-documents.md) | Analyze multiple document variations and synthesize a superior consolidated version |
| [`/convert-hooks`](plugins/personal-plugin/commands/convert-hooks.md) | Convert plugin hook bash scripts to PowerShell for Windows compatibility |
| [`/convert-markdown`](plugins/personal-plugin/commands/convert-markdown.md) | Convert a markdown file to a nicely formatted Microsoft Word document |
| [`/create-plan`](plugins/personal-plugin/commands/create-plan.md) | Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs) |
| [`/define-questions`](plugins/personal-plugin/commands/define-questions.md) | Extract questions and open items from documents to JSON |
| [`/develop-image-prompt`](plugins/personal-plugin/commands/develop-image-prompt.md) | Generate detailed image generator prompts from content, optimized for 11x17 landscape prints |
| [`/finish-document`](plugins/personal-plugin/commands/finish-document.md) | Extract questions from a document, answer them interactively, and update the document |
| [`/implement-plan`](plugins/personal-plugin/commands/implement-plan.md) | Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic testing and git workflow |
| [`/new-command`](plugins/personal-plugin/commands/new-command.md) | Generate a new command file from a template with proper structure and conventions |
| [`/plan-improvements`](plugins/personal-plugin/commands/plan-improvements.md) | Analyze codebase and generate prioritized improvement recommendations with phased implementation... |
| [`/plan-next`](plugins/personal-plugin/commands/plan-next.md) | Analyze repo and recommend the next logical action |
| [`/remove-ip`](plugins/personal-plugin/commands/remove-ip.md) | Sanitize documents by removing company identifiers and non-public intellectual property while pre... |
| [`/review-arch`](plugins/personal-plugin/commands/review-arch.md) | Quick architectural audit with technical debt assessment (read-only, no files generated) |
| [`/review-pr`](plugins/personal-plugin/commands/review-pr.md) | Structured PR review with security, performance, and code quality analysis |
| [`/scaffold-plugin`](plugins/personal-plugin/commands/scaffold-plugin.md) | Create a new plugin with proper directory structure, metadata, and starter files |
| [`/setup-statusline`](plugins/personal-plugin/commands/setup-statusline.md) | "[Personal] Troy's custom status line setup (Windows/PowerShell)" |
| [`/test-project`](plugins/personal-plugin/commands/test-project.md) | Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then create and merge PR |
| [`/validate-plugin`](plugins/personal-plugin/commands/validate-plugin.md) | Validate plugin structure, frontmatter, and content for consistency and correctness |

**Skills:**
| Skill | Description |
|-------|-------------|
| [`/help`](plugins/personal-plugin/skills/help/SKILL.md) | Show available commands and skills in this plugin with usage information |
| [`/research-topic`](plugins/personal-plugin/skills/research-topic/SKILL.md) | Orchestrate parallel deep research across multiple LLM providers and synthesize results |
| [`/ship`](plugins/personal-plugin/skills/ship/SKILL.md) | Create branch, commit, push, open PR, auto-review, fix issues, and merge |

### bpmn-plugin

BPMN 2.0 workflow tools for generating and converting process diagrams.

**Skills:**
| Skill | Description |
|-------|-------------|
| [`/bpmn-generator`](plugins/bpmn-plugin/skills/bpmn-generator/SKILL.md) | Generate BPMN 2.0 compliant XML files from natural language process descriptions OR from structur... |
| [`/bpmn-to-drawio`](plugins/bpmn-plugin/skills/bpmn-to-drawio/SKILL.md) | Convert BPMN 2.0 XML files into Draw.io native format (.drawio) using the bpmn2drawio Python tool. |
| [`/help`](plugins/bpmn-plugin/skills/help/SKILL.md) | Show available skills in this plugin with usage information |

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

```
.claude-plugin/
  marketplace.json          # Marketplace configuration

plugins/
  personal-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    commands/               # Slash commands
    skills/                 # Proactive skills

  bpmn-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/                 # BPMN generator skill
    references/             # BPMN element documentation
    templates/              # XML templates and lane mappings
    examples/               # Sample BPMN files
```

## Documentation

- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - Essential patterns for plugin development
- [WORKFLOWS.md](WORKFLOWS.md) - How to chain commands for common use cases
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solutions to common issues
- [SECURITY.md](SECURITY.md) - Security model and vulnerability reporting

## License

MIT
