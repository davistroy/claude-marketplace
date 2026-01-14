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
| `/analyze-transcript` | Convert meeting transcripts to structured markdown |
| `/ask-questions` | Interactive Q&A session from JSON file |
| `/assess-document` | Document quality evaluation with scoring |
| `/bump-version` | Automate version bumping across plugin files with CHANGELOG |
| `/clean-repo` | Repository cleanup, organization, and documentation refresh |
| `/consolidate-documents` | Analyze multiple document variations and synthesize |
| `/convert-markdown` | Convert markdown to formatted Word document |
| `/define-questions` | Extract questions/TBDs from docs to JSON |
| `/develop-image-prompt` | Generate AI image prompts from content |
| `/finish-document` | Extract questions, answer interactively, update document |
| `/plan-improvements` | Generate improvement recommendations with implementation plan |
| `/plan-next` | Analyze repo and recommend next action |
| `/review-arch` | Quick architectural audit (read-only, no files generated) |
| `/review-pr` | Structured PR review with security and code quality analysis |
| `/setup-statusline` | Custom status line setup (Windows/PowerShell) |
| `/test-project` | Ensure 90%+ coverage, run tests, fix, merge PR |
| `/validate-plugin` | Validate plugin structure, frontmatter, and content |

**Skills:**
| Skill | Description |
|-------|-------------|
| `/help` | Show available commands and skills with usage information |
| `/ship` | Git workflow: branch, commit, push, and open PR |

### bpmn-plugin

BPMN 2.0 workflow tools for generating and converting process diagrams.

**Skills:**
| Skill | Description |
|-------|-------------|
| `/bpmn-generator` | Generate BPMN 2.0 XML from natural language or markdown documents |
| `/bpmn-to-drawio` | Convert BPMN 2.0 XML files to Draw.io native format (.drawio) |
| `/help` | Show available skills with usage information |

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

## License

MIT
