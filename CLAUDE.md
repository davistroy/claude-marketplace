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
      analyze-transcript.md   # Meeting transcript to structured report
      ask-questions.md        # Interactive Q&A session from JSON file
      assess-document.md           # Document quality evaluation with scoring
      bump-version.md         # Automate version bumping across plugin files
      clean-repo.md           # Repository cleanup, organization, and documentation refresh
      consolidate-documents.md     # Merge multiple document versions into one
      convert-markdown.md     # Convert markdown to formatted Word document
      define-questions.md     # Extract questions/TBDs from docs to JSON
      develop-image-prompt.md # Generate AI image prompts from content
      finish-document.md      # Extract questions, answer, update document
      plan-improvements.md    # Generate improvement recommendations and phased implementation plan
      plan-next.md            # Analyze repo and recommend next action
      review-arch.md          # Quick architectural audit (read-only, no files generated)
      review-pr.md            # Structured PR review with code analysis
      setup-statusline.md     # Custom status line setup (Windows/PowerShell)
      test-project.md         # Run all tests, fix failures, achieve 90%+ coverage, merge PR
      validate-plugin.md      # Validate plugin structure and content
    skills/
      help.md               # Show commands/skills with usage information
      ship.md               # Git workflow: branch, commit, push, PR
    references/
      common-patterns.md    # Shared patterns for timestamps, naming, etc.

  bpmn-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/
      bpmn-generator.md     # BPMN 2.0 XML generation from NL or markdown
      bpmn-to-drawio.md     # Convert BPMN XML to Draw.io format
      help.md               # Show skills with usage information
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

**Important:** Do NOT include a `name` field in frontmatter - the filename determines the command name. Adding `name` can prevent command discovery.

### Naming
- Use kebab-case for command filenames
- Commands are invoked as `/filename` (without .md extension)

### Patterns Used
- **Read-only commands** (`review-arch`, `assess-document`): Analyze and report, never modify
- **Interactive commands** (`ask-questions`): Single-question flow, wait for user input
- **Workflow commands** (`ship`): Multi-step automation with confirmation points
- **Generator commands** (`define-questions`, `analyze-transcript`): Create structured output files
- **Synthesis commands** (`consolidate-documents`): Merge multiple sources into optimized output
- **Conversion commands** (`convert-markdown`): Transform files between formats
- **Generation commands** (`develop-image-prompt`): Create prompts or content for external tools
- **Planning commands** (`plan-improvements`, `plan-next`): Analyze codebase and generate actionable plans
- **Testing commands** (`test-project`): Comprehensive test, fix, and ship workflows
- **Cleanup commands** (`clean-repo`): Repository cleanup, organization, and documentation refresh
- **Utility commands** (`bump-version`, `validate-plugin`, `setup-statusline`): Plugin/repository maintenance and configuration tasks

### Output File Naming
Commands that generate files use: `[type]-[source]-[timestamp].json` or `.md`

### Timestamp Format
All generated files use `YYYYMMDD-HHMMSS` format for timestamps.
Example: `assessment-PRD-20260114-143052.md`

### Output Locations
- Analysis reports → `reports/` directory
- Reference data (JSON) → `reference/` directory
- Generated documents → same directory as source
- Temporary files → `.tmp/` (auto-cleaned)

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
4. **Create a `help.md` skill** with usage information for all commands/skills
5. Register the plugin in `.claude-plugin/marketplace.json`

## Help Skill Maintenance

**IMPORTANT:** Each plugin must have a `/help` skill that documents all commands and skills.

When modifying a plugin:
- **Adding a command/skill**: Update the plugin's `help.md` with the new entry
- **Changing a command/skill**: Update the corresponding entry in `help.md`
- **Removing a command/skill**: Remove the entry from `help.md`
- **Creating a new plugin**: Create a `help.md` skill following the pattern in existing plugins
