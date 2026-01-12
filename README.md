# Claude Marketplace

A collection of Claude Code plugins containing custom slash commands and skills for documentation review, architecture analysis, git workflows, and document processing.

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
| `/doc-review` | Documentation audit and cleanup |
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
```

## License

MIT
