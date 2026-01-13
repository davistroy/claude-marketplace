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
      consolidate.md        # Merge multiple document versions into one
      wordify.md            # Convert markdown to formatted Word document
      image-prompt.md       # Generate AI image prompts from content
      next-step.md          # Analyze repo and recommend next action
      troy-statusline.md    # Custom status line setup (Windows/PowerShell)
    skills/
      ship.md               # Git workflow: branch, commit, push, PR

  bpmn-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/
      bpmn-generator.md     # BPMN 2.0 XML generation from NL or markdown
      bpmn-to-drawio.md     # Convert BPMN XML to Draw.io format
    references/             # BPMN element documentation and guides
    templates/              # XML/Draw.io skeletons and style mappings
    examples/               # Sample BPMN and Draw.io files
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
- **Synthesis commands** (`consolidate`): Merge multiple sources into optimized output
- **Conversion commands** (`wordify`): Transform files between formats
- **Generation commands** (`image-prompt`): Create prompts or content for external tools

### Output File Naming
Commands that generate files use: `[type]-[source]-[timestamp].json` or `.md`
Example: `questions-PRD-20260110.json`, `meeting-analysis-2026-01-10.md`

## BPMN Plugin

The bpmn-plugin provides two skills for BPMN workflow management:

### BPMN Generator (`/bpmn-generator`)

Generates BPMN 2.0 XML with two operating modes:

**Interactive Mode** - Natural language descriptions trigger structured Q&A:
1. Process Scope (name, triggers, outcomes)
2. Participants (pools, lanes, roles)
3. Activities (tasks, types, documentation)
4. Flow Control (gateways, conditions, loops)
5. Events & Exceptions (timers, errors, compensation)
6. Data & Integration (data objects, message flows)

**Document Parsing Mode** - Markdown file path triggers extraction of:
- Process metadata from headings/frontmatter
- Phases/stages from section structure
- Tasks from numbered lists with type inference
- Roles mapped to colored lanes
- Decision points from conditional language

### BPMN to Draw.io Converter (`/bpmn-to-drawio`)

Converts BPMN 2.0 XML files to Draw.io native format (.drawio):
- Proper swim lane structure (pools and lanes)
- BPMN-styled shapes for all element types
- Correct connector routing including cross-lane flows
- Color coding by lane function (Sales=blue, Finance=orange, etc.)
- Cross-lane edges use absolute coordinates for proper rendering

**Critical Rule:** Edges crossing lane boundaries must have `parent="1"` (root level) with absolute `mxPoint` coordinates.

### Key Output Features
- BPMN 2.0 compliant XML with all required namespaces
- Diagram Interchange (DI) data for visual rendering
- Phase comments (`<!-- Phase N: ... -->`) for PowerPoint compatibility
- Draw.io files compatible with Desktop and web applications

## Adding New Plugins

1. Create a new directory under `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add `commands/` and/or `skills/` directories with markdown files
4. Register the plugin in `.claude-plugin/marketplace.json`
