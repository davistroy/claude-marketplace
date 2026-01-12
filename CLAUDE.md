# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

This is a Claude Code plugin marketplace repository. It contains multiple plugins that extend Claude Code's functionality with specialized workflows for documentation review, architecture analysis, git workflows, document processing, and BPMN workflow generation.

## Repository Structure

```
.claude-plugin/
  marketplace.json          # Marketplace config with plugin registry

plugins/
  personal-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    commands/
      arch-review.md        # Architectural audit (read-only analysis)
      cleanup.md            # Repository cleanup and organization
      doc-review.md         # Documentation audit and cleanup
      finish-document.md    # Extract questions, answer, update document
      transcript-analysis.md  # Meeting transcript to structured report
      define-questions.md   # Extract questions/TBDs from docs to JSON
      ask-questions.md      # Interactive Q&A session from JSON file
      doc-assessment.md     # Document quality evaluation with scoring
      next-step.md          # Analyze repo and recommend next action
      troy-statusline.md    # Custom status line setup (Windows/PowerShell)
    skills/
      ship.md               # Git workflow: branch, commit, push, PR

  bpmn-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/
      bpmn-generator.md     # BPMN 2.0 XML generation from NL or markdown
    references/             # BPMN element documentation and guides
    templates/              # XML skeletons and lane color mappings
    examples/               # Sample BPMN files for reference
```

## Commands vs Skills

- **Commands** (`/command-name`): User-initiated workflows. Comprehensive, standalone, take control of the session.
- **Skills** (`/skill-name`): Discrete actions Claude may proactively suggest after completing related work.

## Command Conventions

### Frontmatter Structure
```yaml
---
description: Brief description shown in command list
allowed-tools: Bash(git:*)   # Tool restrictions (optional)
---
```

### Naming
- Use kebab-case for command filenames
- Commands are invoked as `/filename` (without .md extension)

### Patterns Used
- **Read-only commands** (`arch-review`, `doc-assessment`): Analyze and report, never modify
- **Interactive commands** (`ask-questions`): Single-question flow, wait for user input
- **Workflow commands** (`ship`): Multi-step automation with confirmation points
- **Generator commands** (`define-questions`, `transcript-analysis`): Create structured output files

### Output File Naming
Commands that generate files use: `[type]-[source]-[timestamp].json` or `.md`
Example: `questions-PRD-20260110.json`, `meeting-analysis-2026-01-10.md`

## BPMN Plugin

The bpmn-plugin provides BPMN 2.0 XML generation capabilities with two operating modes:

### Interactive Mode
Triggered by natural language descriptions without a file. Uses structured Q&A phases:
1. Process Scope (name, triggers, outcomes)
2. Participants (pools, lanes, roles)
3. Activities (tasks, types, documentation)
4. Flow Control (gateways, conditions, loops)
5. Events & Exceptions (timers, errors, compensation)
6. Data & Integration (data objects, message flows)

### Document Parsing Mode
Triggered by providing a markdown file path. Extracts:
- Process metadata from headings/frontmatter
- Phases/stages from section structure
- Tasks from numbered lists with type inference
- Roles mapped to colored lanes
- Decision points from conditional language

### Key Output Features
- BPMN 2.0 compliant XML with all required namespaces
- Diagram Interchange (DI) data for visual rendering
- Phase comments (`<!-- Phase N: ... -->`) for PowerPoint compatibility
- Task documentation elements for each activity

## Adding New Plugins

1. Create a new directory under `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add `commands/` and/or `skills/` directories with markdown files
4. Register the plugin in `.claude-plugin/marketplace.json`
