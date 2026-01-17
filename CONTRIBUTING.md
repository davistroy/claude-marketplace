# Contributing to Claude Marketplace

Thank you for your interest in contributing to the Claude Code plugin marketplace. This guide will help you create commands, skills, and manage versions effectively.

**IMPORTANT:** All contributions must maintain compatibility with the official Claude Code marketplace installation system. Users install plugins via:

```
/plugin marketplace add davistroy/claude-marketplace
/plugin install personal-plugin@troys-plugins
```

See [CLAUDE.md](CLAUDE.md) for required repository structure and compatibility requirements.

## Table of Contents

- [Quick Start: Adding a Command](#quick-start-adding-a-command)
- [Quick Start: Adding a Plugin](#quick-start-adding-a-plugin)
- [Plugin Development Guide](#plugin-development-guide)
- [Adding a New Command](#adding-a-new-command)
- [Adding a New Skill](#adding-a-new-skill)
- [Maintaining the Help Skill](#maintaining-the-help-skill)
- [Command Template](#command-template)
- [Version Management](#version-management)
- [Pull Request Process](#pull-request-process)
- [Test Infrastructure](#test-infrastructure)
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

## Plugin Development Guide

**New to plugin development?** We have a comprehensive step-by-step tutorial that walks you through creating your first command.

**[Read the Plugin Development Guide](docs/PLUGIN-DEVELOPMENT.md)**

The guide includes:
1. **Prerequisites and Setup** (5 min read) - What you need to get started
2. **Creating Your First Command** (15 min tutorial) - Hands-on walkthrough
3. **Testing Your Command Locally** - Verification checklist
4. **Understanding Patterns** - Links to pattern documentation
5. **Submitting for Review** - PR checklist and template
6. **Common Mistakes and Solutions** - Avoid the most frequent pitfalls

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
plugins/[plugin-name]/skills/[skill-name]/SKILL.md
```

Example: `plugins/personal-plugin/skills/ship/SKILL.md`

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

### Pre-commit Hook Enforcement

**IMPORTANT:** The pre-commit hook enforces help.md completeness to ensure all commands and skills are documented.

**Blocking Behavior:**
- When you **add a new command/skill**, the hook **blocks** if it's not documented in help.md
- When you **modify existing files**, the hook shows an informational message but allows the commit

**Why this approach?**
- Some plugins maintain custom help content with enhanced descriptions
- Strict exact-match checking would reject legitimate custom content
- The hook still verifies all commands/skills are mentioned (Check 3)

**If your commit is blocked due to missing documentation:**

```bash
# Option 1: Regenerate help.md files automatically
python scripts/generate-help.py --all

# Option 2: Use Claude Code (recommended)
/validate-plugin --fix
```

Then stage the updated help.md files and commit again:
```bash
git add plugins/*/skills/help/SKILL.md
git commit -m "your message"
```

**Custom Help Content:**
If you maintain enhanced help.md content (not auto-generated), the hook will show an informational message about the difference but won't block your commit as long as all commands/skills are documented.

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
plugins/[plugin-name]/skills/help/SKILL.md
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
2. **Test your commands** - Manually verify they work as expected (see Testing Your Command below)
3. **Test marketplace compatibility** - Verify plugins install correctly (see below)
4. **Update documentation** - Keep README and CLAUDE.md current
5. **Update CHANGELOG** - Add entry for your changes
6. **Follow conventions** - Match existing code style and patterns

### Marketplace Compatibility Testing

**CRITICAL:** Before merging, verify your changes don't break marketplace installation.

After pushing your branch to GitHub:

```
# In a fresh Claude Code session, test installation from your branch:
/plugin marketplace add davistroy/claude-marketplace

# Install and verify
/plugin install personal-plugin@troys-plugins
/help

# Verify your new/modified commands appear and work
```

**What breaks marketplace compatibility:**
- Moving or renaming `.claude-plugin/marketplace.json`
- Moving or renaming `plugins/[name]/.claude-plugin/plugin.json`
- Changing plugin names without updating marketplace.json
- Invalid JSON in marketplace.json or plugin.json
- Mismatched versions between plugin.json and marketplace.json

---

## Testing Your Command

Before submitting a PR, test your command thoroughly to ensure it handles arguments correctly and provides helpful error messages.

### Required Test Cases

Test your command with these scenarios:

#### 1. Missing Required Arguments
```
/your-command
```
(no arguments provided)

**Expected:** Clear error message with usage example and argument descriptions.

#### 2. Invalid Argument Values
```
/your-command invalid-file.xyz
```

**Expected:** Helpful error explaining what's wrong and how to fix it.

#### 3. Default Optional Argument Behavior
```
/your-command file.md
```
(without optional flags like --format)

**Expected:** Command uses documented default values.

#### 4. All Documented Flags
Test each flag your command supports:
```
/your-command file.md --dry-run
/your-command file.md --force
/your-command file.md --format json
```

**Expected:** Each flag behaves as documented in Input Validation section.

### Test Checklist for PR Description

Include this checklist in your PR description:

```markdown
## Argument Testing Results

- [ ] Missing required argument shows usage with example
- [ ] Invalid argument value shows clear error and guidance
- [ ] Optional arguments use documented defaults
- [ ] All documented flags work as described
- [ ] --dry-run (if supported) produces no side effects
- [ ] --force (if supported) overrides with warning
- [ ] Unknown arguments show clear error
- [ ] Error messages include example of correct usage
```

### Schema Validation Testing (if applicable)

If your command generates or consumes JSON, test schema validation:

```markdown
## Schema Validation Testing

- [ ] Valid output passes schema validation
- [ ] Invalid output shows specific validation errors
- [ ] --force flag saves despite validation errors (with warning)
- [ ] Input validation catches malformed files
```

### Reference Documentation

See `plugins/personal-plugin/references/common-patterns.md` for:
- **Error Message Format** - Standard formats for error messages
- **Schema Validation** - How to implement schema validation
- **Argument Testing** - Detailed test case specifications

### PR Description Template

```markdown
## Summary
- [Brief bullet points of what changed]

## Test Plan
- [ ] Tested `/new-command` with valid input
- [ ] Tested `/new-command` with missing arguments
- [ ] Verified error messages are helpful
- [ ] Checked output file naming follows conventions

## Marketplace Compatibility
- [ ] Verified `/plugin marketplace add davistroy/claude-marketplace` works
- [ ] Verified `/plugin install [plugin-name]@troys-plugins` works
- [ ] Verified `/help` shows all commands after installation

## Related Issues
Closes #123
```

---

## Test Infrastructure

This project includes a pytest-based test infrastructure for validating command behavior and schema compliance.

### Directory Structure

```
tests/
  conftest.py              # Shared pytest fixtures
  __init__.py
  fixtures/                # Test data files
    sample-prd.md          # Sample document with TBD markers
    expected-questions.json # Expected /define-questions output
    sample-answers.json    # Sample /ask-questions output
    expected-updated-prd.md # Expected /finish-document output
  helpers/                 # Reusable test utilities
    __init__.py
    schema_validator.py    # JSON schema validation helpers
    file_comparator.py     # File comparison utilities
  integration/             # Integration tests
    __init__.py
    test_qa_workflow.py    # Q&A workflow chain tests
```

### Running Tests

```bash
# Install test dependencies
pip install pytest jsonschema

# Run all tests
pytest tests/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run with verbose output and stop on first failure
pytest tests/ -v -x

# Run specific test file
pytest tests/integration/test_qa_workflow.py -v

# Run tests matching a pattern
pytest tests/ -v -k "schema"
```

### Available Fixtures

The `tests/conftest.py` file provides these pytest fixtures:

| Fixture | Description |
|---------|-------------|
| `project_root` | Path to project root directory |
| `schema_dir` | Path to `schemas/` directory |
| `fixtures_dir` | Path to `tests/fixtures/` directory |
| `questions_schema` | Loaded questions.json schema |
| `answers_schema` | Loaded answers.json schema |
| `sample_prd` | Contents of sample-prd.md |
| `expected_questions` | Loaded expected-questions.json |
| `sample_answers` | Loaded sample-answers.json |
| `expected_updated_prd` | Contents of expected-updated-prd.md |

### Test Helpers

#### Schema Validation (`tests/helpers/schema_validator.py`)

```python
from tests.helpers.schema_validator import (
    validate_against_schema,
    get_validation_errors,
    validate_questions_structure,
    validate_answers_structure,
)

# Validate data against schema
is_valid = validate_against_schema(data, schema)

# Get list of specific errors
errors = get_validation_errors(data, schema)

# Validate structural requirements beyond schema
issues = validate_questions_structure(questions_data)
```

#### File Comparison (`tests/helpers/file_comparator.py`)

```python
from tests.helpers.file_comparator import (
    compare_files,
    compare_markdown_content,
    normalize_timestamps,
    extract_tbd_markers,
)

# Compare two files, ignoring timestamps
match, diff = compare_files(expected_path, actual_path, ignore_timestamps=True)

# Extract TBD markers from markdown
markers = extract_tbd_markers(markdown_content)
```

### Writing New Tests

When adding new tests:

1. **Add fixtures** to `tests/fixtures/` for test data
2. **Create fixture loaders** in `tests/conftest.py` if needed
3. **Use helper functions** from `tests/helpers/` for common operations
4. **Follow pytest conventions** for test naming and organization

Example test structure:

```python
import pytest
from tests.helpers.schema_validator import validate_against_schema

class TestMyFeature:
    """Tests for my feature."""

    def test_valid_input_produces_valid_output(self, my_fixture):
        """Verify valid input produces schema-compliant output."""
        result = process_input(my_fixture)
        assert validate_against_schema(result, schema)

    def test_invalid_input_raises_error(self):
        """Verify invalid input produces clear error."""
        with pytest.raises(ValueError, match="expected message"):
            process_input(invalid_data)
```

### CI Integration

Tests run automatically on GitHub Actions for:
- All pushes to `main`
- All pull requests targeting `main`

The workflow runs tests on:
- Python 3.10, 3.11, and 3.12
- Ubuntu, Windows, and macOS

See `.github/workflows/test.yml` for the full configuration.

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
