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
| `/arch-review` | Deep architectural review with technical debt assessment |
| `/cleanup` | Repository cleanup, organization, and documentation refresh |
| `/doc-review` | Documentation audit and cleanup |
| `/finish-document` | Extract questions, answer interactively, update document |
| `/transcript-analysis` | Convert meeting transcripts to structured markdown |
| `/define-questions` | Extract questions/TBDs from docs to JSON |
| `/ask-questions` | Interactive Q&A session from JSON file |
| `/doc-assessment` | Document quality evaluation with scoring |
| `/next-step` | Analyze repo and recommend next action |
| `/troy-statusline` | Custom status line setup (Windows/PowerShell) |

**Skills:**
| Skill | Description |
|-------|-------------|
| `/ship` | Git workflow: branch, commit, push, and open PR |

### bpmn-plugin

BPMN 2.0 XML generator for creating compliant workflow diagrams.

**Skills:**
| Skill | Description |
|-------|-------------|
| `/bpmn-generator` | Generate BPMN 2.0 XML from natural language or markdown documents |

The BPMN generator operates in two modes:
- **Interactive Mode**: Structured Q&A to gather requirements from natural language descriptions
- **Document Parsing Mode**: Parse markdown documents to extract process elements

Generated XML includes:
- Complete BPMN 2.0 compliant process definitions
- Diagram Interchange (DI) data for visual rendering
- Phase comments for PowerPoint generation compatibility
- Layouts compatible with Draw.io, Camunda, Flowable, and bpmn.io

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
