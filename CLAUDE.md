# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal Claude Code plugin repository containing custom slash commands. These commands extend Claude Code's functionality with specialized workflows for documentation review, architecture analysis, git workflows, and document processing.

## Repository Structure

Commands live in `.claude/commands/`, skills in `.claude/skills/`:

```
.claude/commands/
├── arch-review.md       # Architectural audit (read-only analysis)
├── doc-review.md        # Documentation audit and cleanup
├── transcript-analysis.md  # Meeting transcript → structured markdown report
├── define-questions.md  # Extract questions/TBDs from docs → JSON
├── ask-questions.md     # Interactive Q&A session from JSON file
├── doc-assessment.md    # Document quality evaluation → scored report
├── next-step.md         # Analyze repo and recommend next action
├── troy-statusline.md   # Custom status line setup (Windows/PowerShell)

.claude/skills/
├── ship.md              # Git workflow: branch → commit → push → PR
```

## Commands vs Skills

- **Commands** (`/command-name`): User-initiated workflows. Comprehensive, standalone, take control of the session.
- **Skills** (`/skill-name`): Discrete actions Claude may proactively suggest after completing related work.

## Command Conventions

### Frontmatter Structure
```yaml
---
name: command-name           # Optional display name
description: Brief desc      # Shown in command list
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
