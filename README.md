# Claude Marketplace

A collection of Claude Code plugins containing custom slash commands and skills for documentation review, architecture analysis, git workflows, document processing, and BPMN workflow generation.

## Installation

Add this marketplace to your Claude Code configuration:

```bash
claude mcp add-plugin https://github.com/davistroy/claude-marketplace
```

## Available Plugins

### personal-plugin

Custom commands and skills for productivity workflows.

**Commands:**
| Command | Description |
|---------|-------------|
| `/analyze-transcript` | Meeting transcript to structured markdown report |
| `/ask-questions` | Interactive Q&A session from questions JSON file |
| `/assess-document` | Document quality evaluation with scored assessment report |
| `/bump-version` | Automate version bumping across plugin files with CHANGEL... |
| `/check-updates` | Check for available plugin updates by comparing installed... |
| `/clean-repo` | Comprehensive repository cleanup, organization, and docum... |
| `/consolidate-documents` | Analyze multiple document variations and synthesize a sup... |
| `/convert-markdown` | Convert a markdown file to a nicely formatted Microsoft W... |
| `/define-questions` | Extract questions and open items from documents to JSON |
| `/develop-image-prompt` | Generate detailed image generator prompts from content, o... |
| `/finish-document` | Extract questions from a document, answer them interactiv... |
| `/new-command` | Generate a new command file from a template with proper s... |
| `/plan-improvements` | Analyze codebase and generate prioritized improvement rec... |
| `/plan-next` | Analyze repo and recommend the next logical action |
| `/remove-ip` | Sanitize documents by removing company identifiers and IP... |
| `/review-arch` | Quick architectural audit with technical debt assessment ... |
| `/review-pr` | Structured PR review with security, performance, and code... |
| `/scaffold-plugin` | Create a new plugin with proper directory structure, meta... |
| `/setup-statusline` | "[Personal] Troy's custom status line setup (Windows/Powe... |
| `/test-project` | Ensure 90%+ test coverage, run all tests with sub-agents,... |
| `/validate-plugin` | Validate plugin structure, frontmatter, and content for c... |

**Skills:**
| Skill | Description |
|-------|-------------|
| `/help` | Show available commands and skills in this plugin with us... |
| `/ship` | Create branch, commit, push, open PR, auto-review, fix is... |

### bpmn-plugin

BPMN 2.0 workflow tools for generating and converting process diagrams.

**Skills:**
| Skill | Description |
|-------|-------------|
| `/bpmn-generator` | Generate BPMN 2.0 compliant XML files from natural langua... |
| `/bpmn-to-drawio` | Convert BPMN 2.0 XML files into Draw.io native format (.d... |
| `/help` | Show available skills in this plugin with usage information |

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

- [WORKFLOWS.md](WORKFLOWS.md) - How to chain commands for common use cases
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solutions to common issues
- [SECURITY.md](SECURITY.md) - Security model and vulnerability reporting

## License

MIT
