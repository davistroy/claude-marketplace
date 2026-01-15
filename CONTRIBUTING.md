# Contributing to Claude Marketplace

Thank you for your interest in contributing to the Claude Code plugin marketplace. This guide will help you create commands, skills, and manage versions effectively.

## Table of Contents

- [Quick Start: Adding a Command](#quick-start-adding-a-command)
- [Quick Start: Adding a Plugin](#quick-start-adding-a-plugin)
- [Adding a New Command](#adding-a-new-command)
- [Adding a New Skill](#adding-a-new-skill)
- [Maintaining the Help Skill](#maintaining-the-help-skill)
- [Command Template](#command-template)
- [Version Management](#version-management)
- [Pull Request Process](#pull-request-process)
- [Pre-commit Hook Setup](#pre-commit-hook-setup)

---

## Quick Start: Adding a Command

The simplified workflow for adding a new command is just 4 steps:

### Step 1: Create the Command File

Use the `/new-command` command to generate a properly structured command file:

```
/new-command
```

This will:
- Prompt for command name (validates kebab-case)
- Prompt for description
- Ask which pattern type to use
- Generate the command file from a template

Alternatively, create the file manually in `plugins/[plugin-name]/commands/[command-name].md`.

### Step 2: Update Documentation

Run the automation scripts to update help files and README:

```bash
# Update help.md files
python scripts/generate-help.py --all

# Update README.md tables
python scripts/update-readme.py
```

### Step 3: Update CHANGELOG

Manually add an entry to `CHANGELOG.md` under `[Unreleased]`:

```markdown
### Added
- New `/my-command` for doing something useful
```

### Step 4: Validate and Commit

```bash
# Validate the plugin
/validate-plugin personal-plugin

# Commit your changes
git add .
git commit -m "feat(personal-plugin): add my-command"
```

---

## Quick Start: Adding a Plugin

To create a new plugin with proper structure:

### Step 1: Scaffold the Plugin

Use the `/scaffold-plugin` command:

```
/scaffold-plugin
```

This will:
- Prompt for plugin name
- Prompt for description and category
- Create the directory structure
- Generate `plugin.json` and starter `help.md`
- Update `marketplace.json`

### Step 2: Add Commands

Use `/new-command` to add commands to your new plugin.

### Step 3: Update Documentation

```bash
python scripts/generate-help.py plugins/[plugin-name]
python scripts/update-readme.py
```

### Step 4: Update CHANGELOG and Commit

Add entry to CHANGELOG.md and commit your changes.

---

## Adding a New Command

Commands are user-initiated workflows that take control of the Claude Code session. They are comprehensive, standalone operations.

### File Location

```
plugins/[plugin-name]/commands/[command-name].md
```

Example: `plugins/personal-plugin/commands/assess-document.md`

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
| **Read-only** | Analyzing and reporting without modifications | `review-arch`, `assess-document` |
| **Interactive** | Single-question flow requiring user input | `ask-questions` |
| **Workflow** | Multi-step automation with confirmation points | `clean-repo`, `finish-document` |
| **Generator** | Creating structured output files | `define-questions`, `analyze-transcript` |
| **Synthesis** | Merging multiple sources into one | `consolidate-documents` |
| **Conversion** | Transforming files between formats | `convert-markdown` |
| **Generation** | Creating prompts or content for external tools | `develop-image-prompt` |
| **Planning** | Analyzing codebase and generating actionable plans | `plan-improvements`, `plan-next` |
| **Testing** | Comprehensive test, fix, and ship workflows | `test-project` |

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
| Example: `/review-arch` | Example: `/ship` |

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

## Maintaining the Help Skill

**IMPORTANT:** Each plugin must have a `/help` skill that documents all commands and skills. This skill must be kept in sync with the plugin's contents.

### Automated Help Generation (Recommended)

Use the `generate-help.py` script to automatically generate help.md files from command metadata:

```bash
# Generate help.md for a specific plugin
python scripts/generate-help.py plugins/personal-plugin

# Generate help.md for all plugins
python scripts/generate-help.py --all

# Check if help.md needs updating (no changes made)
python scripts/generate-help.py --all --check
```

The script extracts:
- **Description** from frontmatter
- **Arguments** from "Input Validation" section
- **Output** from "Output" or "File Naming" sections
- **Examples** from code blocks containing `/command-name`

**Note:** The pre-commit hook runs `--check` as an optional warning. It will not block commits.

### When to Regenerate Help

| Action | What to Do |
|--------|------------|
| Add a command/skill | Run `python scripts/generate-help.py plugins/<plugin>` |
| Rename a command/skill | Regenerate help.md |
| Change arguments/output | Regenerate help.md |
| Remove a command/skill | Regenerate help.md |
| Create a new plugin | Run generator on the new plugin |

### Help Skill Location

```
plugins/[plugin-name]/skills/help.md
```

### Manual Updates (If Needed)

If you need to add custom content not captured by the generator, you can still manually edit help.md. However, note that regenerating will overwrite your changes.

Add this for each new command or skill:

```markdown
#### /command-name
**Description:** Brief description of what it does
**Arguments:** `<required-arg>` `[optional-arg]` - Description of arguments
**Output:** What the command produces (files, reports, etc.)
**Example:**
```
/command-name example-usage
```
```

### Checklist

Before submitting a PR that modifies commands or skills:

- [ ] Ran `python scripts/generate-help.py --all` to update help files
- [ ] Verified description matches the command's frontmatter description
- [ ] Verified arguments section matches the command's Input Validation
- [ ] Verified examples are accurate and functional

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
