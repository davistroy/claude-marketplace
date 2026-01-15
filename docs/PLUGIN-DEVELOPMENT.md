# Plugin Development Guide

Welcome to the Claude Code Plugin Development Guide. This step-by-step tutorial will help you create your first plugin command from scratch.

**Total Time:** ~25 minutes (5 min reading + 15 min tutorial + 5 min testing)

---

## Table of Contents

1. [Prerequisites and Setup](#1-prerequisites-and-setup) (5 min read)
2. [Creating Your First Command](#2-creating-your-first-command) (15 min tutorial)
3. [Testing Your Command Locally](#3-testing-your-command-locally)
4. [Understanding Patterns](#4-understanding-patterns)
5. [Submitting for Review](#5-submitting-for-review)
6. [Common Mistakes and Solutions](#6-common-mistakes-and-solutions)

---

## 1. Prerequisites and Setup

### What You Need

Before creating a plugin command, ensure you have:

- **Git** installed and configured
- **Python 3.10+** (for running validation scripts)
- **Claude Code** CLI installed
- A cloned copy of the `claude-marketplace` repository

### Repository Structure Overview

```
claude-marketplace/
  plugins/
    personal-plugin/
      .claude-plugin/
        plugin.json         # Plugin metadata
      commands/             # User-initiated commands
        assess-document.md
        new-command.md
        ...
      skills/               # Proactive suggestions
        help.md
        ship.md
      references/           # Patterns and templates
        common-patterns.md
        patterns/           # Modular pattern files
        templates/          # Command templates
```

### Key Concepts

| Term | Definition |
|------|------------|
| **Command** | User-initiated workflow invoked with `/command-name` |
| **Skill** | Action Claude may proactively suggest |
| **Pattern** | Reusable structure or convention |
| **Template** | Starting point for new commands |

### Setting Up Your Environment

```bash
# Clone the repository
git clone https://github.com/your-org/claude-marketplace.git
cd claude-marketplace

# Install Python dependencies for testing
pip install pytest jsonschema pyyaml

# Copy the pre-commit hook
cp scripts/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit  # Unix/Mac/WSL
```

---

## 2. Creating Your First Command

In this tutorial, we will create a simple "read-only" command called `/check-links` that scans a document for broken links and reports findings.

### Step 1: Choose a Pattern Type

First, decide what type of command you are building:

| Pattern | Use Case | Examples |
|---------|----------|----------|
| **read-only** | Analyze and report without changes | `review-arch`, `assess-document` |
| **interactive** | Q&A flow requiring user input | `ask-questions` |
| **workflow** | Multi-step automation | `clean-repo`, `ship` |
| **generator** | Create structured output files | `define-questions` |
| **utility** | Maintenance and validation | `validate-plugin` |
| **synthesis** | Merge multiple sources | `consolidate-documents` |
| **conversion** | Transform file formats | `convert-markdown` |
| **planning** | Generate improvement plans | `plan-improvements` |

For our example, we will use the **read-only** pattern since we are analyzing without modifying.

### Step 2: Use the Command Generator

The easiest way to create a command is using `/new-command`:

```
/new-command
```

When prompted:
1. **Command name:** `check-links`
2. **Description:** `Scan a document for broken or invalid links`
3. **Pattern type:** `1` (read-only)

This generates `plugins/personal-plugin/commands/check-links.md` with the template structure.

### Step 3: Customize the Generated File

Open the generated file and customize it. Here is the key structure:

#### Frontmatter (Required)

```yaml
---
description: Scan a document for broken or invalid links
---
```

**Important:** Do NOT add a `name` field. The filename determines the command name.

#### Title and Introduction

```markdown
# Check Links

Scan a document for broken or invalid links. This command provides in-conversation analysis without generating files.
```

#### Input Validation Section

```markdown
## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document to scan

**Optional Arguments:**
- `--verbose` - Show all links, not just broken ones

**Validation:**
If the document path is missing, display:
```
Usage: /check-links <document-path> [--verbose]
Example: /check-links README.md
Example: /check-links docs/api-guide.md --verbose
```
```

#### Instructions Section

```markdown
## Instructions

Execute the following systematic analysis. **DO NOT MAKE ANY CHANGES - ONLY ANALYZE AND REPORT.**

### Phase 1: Link Discovery

1. Read the specified document
2. Extract all links (URLs, file references, anchor links)
3. Categorize links by type:
   - External URLs (https://, http://)
   - Internal file links (relative paths)
   - Anchor links (#section-name)

### Phase 2: Link Validation

For each link found:
- **External URLs**: Check if the domain is reachable
- **Internal files**: Verify the file exists
- **Anchors**: Verify the target heading exists

### Phase 3: Report Findings

Create a categorized report of all issues using standard severity levels:

| Severity | Label | Meaning |
|----------|-------|---------|
| **CRITICAL** | Broken link | Link returns 404 or file missing |
| **WARNING** | Suspicious | Redirect, slow response, or outdated |
| **SUGGESTION** | Improvement | Could use better anchor text |
```

#### Output Format Section

```markdown
## Output Format

Read-only commands produce inline reports (not saved files) with this structure:

```
-------------------------------------------
Link Check Summary
-------------------------------------------

**Document:** [path]
**Links Found:** X total

## Issue Summary

| Severity | Count |
|----------|-------|
| CRITICAL | X |
| WARNING | X |
| SUGGESTION | X |
| **Total** | **X** |

## Broken Links (CRITICAL)

1. [line N] `https://example.com/broken` - 404 Not Found
2. [line M] `docs/missing.md` - File not found

## Suspicious Links (WARNING)

1. [line P] `https://old-domain.com` - Redirects to new-domain.com
```
```

#### Examples Section

```markdown
## Examples

```
User: /check-links README.md

Claude:
-------------------------------------------
Link Check Summary
-------------------------------------------

**Document:** README.md
**Links Found:** 15 total

## Issue Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| WARNING | 1 |
| SUGGESTION | 3 |
| **Total** | **6** |

## Broken Links (CRITICAL)

1. [line 45] `https://api.old-service.com/docs` - 404 Not Found
2. [line 89] `docs/deprecated.md` - File not found

All other links validated successfully.
```
```

### Step 4: Save Your Command

Save the file to `plugins/personal-plugin/commands/check-links.md`.

---

## 3. Testing Your Command Locally

### Run the Command

Test your command with various inputs:

```bash
# Test with a real document
/check-links README.md

# Test with missing argument (should show usage)
/check-links

# Test with invalid path (should show error)
/check-links nonexistent.md

# Test with optional flag
/check-links README.md --verbose
```

### Validation Checklist

Use this checklist to verify your command works correctly:

- [ ] Missing required argument shows usage message with example
- [ ] Invalid file path shows clear error
- [ ] Optional flags work as documented
- [ ] Output format matches the documented structure
- [ ] Severity levels are used correctly

### Run Plugin Validation

```bash
# Validate the entire plugin
/validate-plugin personal-plugin

# Or use the Python script
python scripts/generate-help.py plugins/personal-plugin --check
```

---

## 4. Understanding Patterns

The plugin system uses modular pattern files to ensure consistency. Familiarize yourself with these references:

### Pattern File Index

| Pattern File | What It Covers |
|--------------|----------------|
| [`references/patterns/naming.md`](../plugins/personal-plugin/references/patterns/naming.md) | File naming, timestamps, kebab-case |
| [`references/patterns/validation.md`](../plugins/personal-plugin/references/patterns/validation.md) | Input validation, error messages, severity levels |
| [`references/patterns/output.md`](../plugins/personal-plugin/references/patterns/output.md) | Output directories, preview mode, completion messages |
| [`references/patterns/workflow.md`](../plugins/personal-plugin/references/patterns/workflow.md) | Multi-phase execution, state management, dry-run |
| [`references/patterns/testing.md`](../plugins/personal-plugin/references/patterns/testing.md) | Dry-run mode, prerequisite checks |
| [`references/patterns/logging.md`](../plugins/personal-plugin/references/patterns/logging.md) | Audit logging, performance expectations |

### Template Selection Guide

Choose your template based on what your command does:

```
Does your command modify files?
  No  --> Does it analyze and report? --> read-only template
  Yes --> Does it require user input at each step? --> interactive template
        --> Does it run multiple automated steps? --> workflow template
        --> Does it create structured output files? --> generator template
        --> Does it merge multiple sources? --> synthesis template
        --> Does it transform file formats? --> conversion template
        --> Does it generate improvement plans? --> planning template
        --> Does it maintain the repository? --> utility template
```

### Key Conventions

#### Output Directories

| Content Type | Directory |
|--------------|-----------|
| Analysis reports | `reports/` |
| Reference data (JSON) | `reference/` |
| Planning documents | Repository root |
| Converted files | Same as source |

#### Timestamp Format

Always use `YYYYMMDD-HHMMSS`:
```
assessment-PRD-20260115-143052.md
questions-requirements-20260115-093000.json
```

#### Error Message Format

```
Error: [What went wrong]

Usage: /command-name <required-arg> [--optional-flag]
Example: /command-name example.md

Arguments:
  <required-arg>  Description of the argument
  --optional-flag Description of the flag
```

---

## 5. Submitting for Review

### Pre-Submission Checklist

Before creating a pull request, complete these steps:

#### Documentation Updates

- [ ] Updated help.md with new command entry
  ```bash
  python scripts/generate-help.py plugins/personal-plugin
  ```

- [ ] Updated README.md tables (if applicable)
  ```bash
  python scripts/update-readme.py
  ```

- [ ] Added entry to CHANGELOG.md under `[Unreleased]`
  ```markdown
  ### Added
  - New `/check-links` command for scanning documents for broken links
  ```

#### Validation

- [ ] Ran `/validate-plugin personal-plugin` with no errors
- [ ] Pre-commit hook passes (test with `git commit --dry-run`)

#### Testing

- [ ] Tested with valid input - produces expected output
- [ ] Tested with missing arguments - shows usage message
- [ ] Tested with invalid input - shows helpful error
- [ ] Tested all documented flags

### Pull Request Template

When creating your PR, use this template:

```markdown
## Summary
- Added `/check-links` command for scanning documents for broken links
- Follows read-only pattern with standard severity levels

## Test Plan
- [ ] Tested with README.md - found 2 broken links correctly
- [ ] Tested without arguments - shows usage message
- [ ] Tested with nonexistent file - shows clear error
- [ ] Ran /validate-plugin - passed all checks

## Documentation
- [ ] help.md updated
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if command table changed)

## Related Issues
Closes #123
```

### Branch Naming

Use descriptive branch names:

```
feature/add-check-links-command
fix/validate-plugin-error-handling
docs/update-plugin-development-guide
```

---

## 6. Common Mistakes and Solutions

### Mistake 1: Adding `name` Field to Frontmatter

**Problem:** Command is not discovered or shows wrong name.

**Wrong:**
```yaml
---
name: check-links
description: Scan a document for broken links
---
```

**Correct:**
```yaml
---
description: Scan a document for broken links
---
```

**Why:** The filename determines the command name. Adding a `name` field can cause discovery issues.

**Validation:** Run `/validate-plugin` - it will flag forbidden frontmatter fields.

---

### Mistake 2: Forgetting to Update help.md

**Problem:** New command exists but is not shown in `/help`.

**Fix:**
```bash
python scripts/generate-help.py plugins/personal-plugin
```

**Validation:** Pre-commit hook will block commits with missing help entries.

---

### Mistake 3: Using Wrong Output Directory

**Problem:** Output files are saved to unexpected locations.

**Wrong:**
```markdown
Save to: output/assessment-PRD.md
```

**Correct:**
```markdown
Save to: reports/assessment-PRD-20260115-143052.md
```

**Reference:** See `references/patterns/output.md` for the directory table.

**Validation:** Run `/validate-plugin --strict` to check output conventions.

---

### Mistake 4: Missing Input Validation Section

**Problem:** Command fails confusingly when given invalid input.

**Wrong:** No Input Validation section at all.

**Correct:**
```markdown
## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document

**Validation:**
If the document path is missing, display:
```
Usage: /check-links <document-path>
Example: /check-links README.md
```
```

**Validation:** Run `/validate-plugin --strict` - it checks for required sections.

---

### Mistake 5: Inconsistent Flag Naming

**Problem:** Flags don't follow conventions, confusing users.

**Wrong:**
```
--dryRun, --DRY-RUN, --dry_run
```

**Correct:**
```
--dry-run
```

**Convention:** All flags use lowercase kebab-case with double dashes.

**Reference:** See `references/patterns/naming.md` for naming conventions.

---

### Additional Resources

- **Full Contributing Guide:** [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Project Overview:** [CLAUDE.md](../CLAUDE.md)
- **Common Patterns:** [references/common-patterns.md](../plugins/personal-plugin/references/common-patterns.md)
- **Existing Commands:** Browse [plugins/personal-plugin/commands/](../plugins/personal-plugin/commands/)

---

*Plugin Development Guide v1.0 - Last updated 2026-01-15*
