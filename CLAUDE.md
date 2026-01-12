# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

This is a Claude Code plugin marketplace repository. It contains multiple plugins that extend Claude Code's functionality with specialized workflows for documentation review, architecture analysis, git workflows, and document processing.

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

## Adding New Plugins

1. Create a new directory under `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add `commands/` and/or `skills/` directories with markdown files
4. Register the plugin in `.claude-plugin/marketplace.json`
