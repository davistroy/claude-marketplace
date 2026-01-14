# Contributing to Claude Marketplace

Thank you for your interest in contributing to the Claude Code plugin marketplace. This guide will help you create commands, skills, and manage versions effectively.

## Table of Contents

- [Adding a New Command](#adding-a-new-command)
- [Adding a New Skill](#adding-a-new-skill)
- [Command Template](#command-template)
- [Version Management](#version-management)
- [Pull Request Process](#pull-request-process)
- [Pre-commit Hook Setup](#pre-commit-hook-setup)

---

## Adding a New Command

Commands are user-initiated workflows that take control of the Claude Code session. They are comprehensive, standalone operations.

### File Location

```
plugins/[plugin-name]/commands/[command-name].md
```

Example: `plugins/personal-plugin/commands/doc-assessment.md`

### Frontmatter Requirements

Every command must have YAML frontmatter at the top:

```yaml
---
description: Brief description shown in command list
allowed-tools: Bash(git:*)   # Optional: restrict available tools
---
```

**Required Fields:**
- `description` - A brief description (shown in `/help` and command lists)

**Optional Fields:**
- `allowed-tools` - Restrict which tools Claude can use during this command

**Forbidden Fields:**
- `name` - Do NOT include a name field. The filename determines the command name. Adding `name` can prevent command discovery.

### Naming Conventions

- Use **kebab-case** for filenames: `my-new-command.md`
- Commands are invoked as `/filename` (without `.md` extension)
- Example: `my-new-command.md` becomes `/my-new-command`

### Pattern Selection

Choose the appropriate pattern for your command:

| Pattern | Use When | Examples |
|---------|----------|----------|
| **Read-only** | Analyzing and reporting without modifications | `arch-review`, `doc-assessment` |
| **Interactive** | Single-question flow requiring user input | `ask-questions` |
| **Workflow** | Multi-step automation with confirmation points | `cleanup`, `finish-document` |
| **Generator** | Creating structured output files | `define-questions`, `transcript-analysis` |
| **Synthesis** | Merging multiple sources into one | `consolidate` |
| **Conversion** | Transforming files between formats | `wordify` |
| **Generation** | Creating prompts or content for external tools | `image-prompt` |
| **Planning** | Analyzing codebase and generating actionable plans | `plan-improvements`, `next-step` |
| **Testing** | Comprehensive test, fix, and ship workflows | `fully-test-project` |

See `plugins/personal-plugin/references/common-patterns.md` for detailed pattern documentation.

### Input Validation

Commands that accept arguments should include an Input Validation section:

```markdown
## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document to process

**Optional Arguments:**
- `--format [json|md]` - Output format (default: md)
- `--verbose` - Enable detailed output

**Validation:**
If required arguments missing, display:
```
Usage: /my-command <document-path> [--format json|md]
Example: /my-command docs/PRD.md --format json
```
```

---

## Adding a New Skill

Skills are discrete actions that Claude may proactively suggest after completing related work. They are more focused than commands.

### When to Use Skill vs Command

| Use a **Command** when... | Use a **Skill** when... |
|---------------------------|------------------------|
| User explicitly requests it | Claude suggests it proactively |
| Comprehensive workflow | Focused, single action |
| Takes over the session | Quick operation |
| Example: `/arch-review` | Example: `/ship` |

### File Location

```
plugins/[plugin-name]/skills/[skill-name].md
```

Example: `plugins/personal-plugin/skills/ship.md`

### Frontmatter

Same requirements as commands:

```yaml
---
description: Brief description of the skill
---
```

---

## Command Template

Use this template when creating a new command:

```markdown
---
description: [Brief description for command list]
---

# [Command Title]

[One paragraph describing what this command does and when to use it.]

## Input Validation

**Required Arguments:**
- `<arg-name>` - Description

**Optional Arguments:**
- `--flag [value]` - Description (default: value)

**Validation:**
If required arguments missing, display:
```
Usage: /command-name <required-arg> [--optional-flag value]
Example: /command-name my-file.md
```

## Instructions

### Phase 1: [Phase Name]

[Detailed instructions for this phase]

### Phase 2: [Phase Name]

[Detailed instructions for this phase]

## Output

[Describe what output is produced]

**File Naming:** `[type]-[source]-[YYYYMMDD-HHMMSS].[ext]`
**Location:** [Where output is saved - see common-patterns.md]

## Example Usage

```
User: /command-name input.md

Claude: [Example of what Claude does and outputs]
```

## Error Handling

- **[Error condition]:** [How to handle it]
- **[Error condition]:** [How to handle it]
```

---

## Version Management

### When to Bump Versions

| Bump Type | When to Use | Version Change |
|-----------|-------------|----------------|
| **Major** | Breaking changes, major new features | 1.0.0 -> 2.0.0 |
| **Minor** | New commands/skills, non-breaking features | 1.0.0 -> 1.1.0 |
| **Patch** | Bug fixes, documentation updates | 1.0.0 -> 1.0.1 |

### Files to Update

When releasing a new version, update these files:

1. **Plugin metadata:** `plugins/[plugin]/.claude-plugin/plugin.json`
   - Update `"version"` field

2. **Marketplace registry:** `.claude-plugin/marketplace.json`
   - Update the plugin's `"version"` in the plugins array

3. **Changelog:** `CHANGELOG.md`
   - Add entry under `[Unreleased]` or create new version section
   - Follow [Keep a Changelog](https://keepachangelog.com) format

### Automation

Use `/bump-version` to automate version updates:

```
/bump-version personal-plugin minor
```

This will update all version references and create a CHANGELOG placeholder.

### CHANGELOG Format

```markdown
## [Unreleased]

## [1.6.0] - 2026-01-14

### Added
- New `my-command` for doing something useful

### Changed
- Updated `existing-command` to support new option

### Fixed
- Fixed issue with argument parsing in `other-command`
```

---

## Pull Request Process

### Branch Naming

Use descriptive branch names:

```
feature/add-review-pr-command
fix/validate-plugin-error-handling
docs/update-contributing-guide
```

Format: `[type]/[brief-description]`

Types: `feature`, `fix`, `docs`, `refactor`, `test`, `chore`

### Commit Message Format

```
type(scope): brief description

Longer description if needed.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
**Scope:** Plugin or component name (e.g., `personal-plugin`, `bpmn-plugin`)

Examples:
```
feat(personal-plugin): add PR review command
fix(bpmn-plugin): correct cross-lane edge routing
docs: update CONTRIBUTING with validation guide
```

### Review Expectations

Before submitting a PR:

1. **Validate your changes** - Run `/validate-plugin` on affected plugins
2. **Test your commands** - Manually verify they work as expected
3. **Update documentation** - Keep README and CLAUDE.md current
4. **Update CHANGELOG** - Add entry for your changes
5. **Follow conventions** - Match existing code style and patterns

### PR Description Template

```markdown
## Summary
- [Brief bullet points of what changed]

## Test Plan
- [ ] Tested `/new-command` with valid input
- [ ] Tested `/new-command` with missing arguments
- [ ] Verified error messages are helpful
- [ ] Checked output file naming follows conventions

## Related Issues
Closes #123
```

---

## Pre-commit Hook Setup

A pre-commit hook is available to validate plugin files before committing.

### Installation

```bash
# Copy the pre-commit hook
cp scripts/pre-commit .git/hooks/

# Make it executable (Unix/Mac/WSL)
chmod +x .git/hooks/pre-commit

# On Windows (Git Bash)
chmod +x .git/hooks/pre-commit
```

### What It Checks

The pre-commit hook validates staged `.md` files in the plugins directory:

- Valid YAML frontmatter syntax
- Required `description` field present
- No forbidden `name` field in frontmatter
- Markdown parses correctly

### Bypassing (Not Recommended)

If you need to bypass the hook temporarily:

```bash
git commit --no-verify -m "your message"
```

**Note:** Only bypass for legitimate reasons. The hook exists to catch common mistakes.

---

## Getting Help

- **Command patterns:** See `plugins/personal-plugin/references/common-patterns.md`
- **Project structure:** See `CLAUDE.md`
- **Existing examples:** Browse `plugins/personal-plugin/commands/`
- **Version history:** See `CHANGELOG.md`

If you're unsure about something, look at existing commands for patterns and open an issue for discussion.
