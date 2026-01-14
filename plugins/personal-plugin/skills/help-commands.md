---
description: Discover available commands and skills with descriptions and usage info
---

# Help Commands Skill

Provide command discovery and help information for all available plugins, commands, and skills in the marketplace.

## Input Validation

**Optional Arguments:**
- `<command-name>` - Name of a specific command or skill to get detailed help for

**Usage:**
```
/help-commands                    # List all available commands
/help-commands arch-review        # Get details about arch-review command
/help-commands ship               # Get details about ship skill
```

## Instructions

### Mode 1: List All Commands (no arguments)

Scan the plugin directories and display a categorized list of all available commands and skills.

#### Step 1: Discover Commands and Skills

Scan these directories for `.md` files:
- `plugins/*/commands/*.md`
- `plugins/*/skills/*.md`

For each markdown file found:
1. Read the frontmatter to extract the `description` field
2. Extract the filename (without `.md`) as the command name
3. Note the plugin it belongs to
4. Categorize based on the patterns below

#### Step 2: Categorize Commands

Group commands into these categories based on their behavior pattern (from CLAUDE.md):

**Analysis (Read-Only)**
Commands that analyze and report without modifying files:
- arch-review
- doc-assessment
- next-step

**Interactive Workflows**
Commands that involve back-and-forth with the user:
- ask-questions
- finish-document

**Generation**
Commands that create new output files:
- define-questions
- transcript-analysis
- image-prompt

**Synthesis**
Commands that merge or consolidate multiple sources:
- consolidate

**Conversion**
Commands that transform files between formats:
- wordify
- bpmn-to-drawio

**Git & Automation**
Commands for version control and CI/CD workflows:
- ship
- review-pr

**Validation**
Commands that verify correctness:
- validate-plugin

**Planning**
Commands that analyze and recommend next steps:
- plan-improvements
- fully-test-project

**Cleanup & Organization**
Commands that clean up or reorganize:
- cleanup
- doc-review

**Specialized**
Domain-specific commands:
- bpmn-generator
- troy-statusline

#### Step 3: Display Formatted List

Output format:

```
Available Commands and Skills
=============================

Analysis (Read-Only)
--------------------
  /arch-review       Deep architectural review with technical debt assessment
  /doc-assessment    Document quality evaluation with scored assessment report
  /next-step         Analyze repo and recommend the next logical action

Interactive Workflows
---------------------
  /ask-questions     Interactive Q&A session from questions JSON file
  /finish-document   Extract questions, answer interactively, update document

Generation
----------
  /define-questions  Extract questions/TBDs from docs to JSON
  /transcript-analysis  Meeting transcript to structured markdown report
  /image-prompt      Generate AI image prompts from content

Synthesis
---------
  /consolidate       Merge multiple document versions into optimized single version

Conversion
----------
  /wordify           Convert markdown to formatted Word document
  /bpmn-to-drawio    Convert BPMN XML to Draw.io format

Git & Automation
----------------
  /ship              Create branch, commit changes, push, and open PR
  /review-pr         Structured PR review with security and quality analysis

Validation
----------
  /validate-plugin   Validate plugin structure, frontmatter, and consistency

Planning
--------
  /plan-improvements Generate improvement recommendations with phased plan
  /fully-test-project  Ensure 90%+ coverage, run tests, fix failures, merge PR

Cleanup & Organization
----------------------
  /cleanup           Repository cleanup and organization
  /doc-review        Documentation audit and cleanup

Specialized
-----------
  /bpmn-generator    Generate BPMN 2.0 XML from natural language or markdown

-----------------------------
Total: [X] commands, [Y] skills

Use '/help-commands <name>' for detailed help on a specific command.
```

### Mode 2: Detailed Help (with command name argument)

When a specific command name is provided, show detailed information.

#### Step 1: Find the Command

Search for the command in:
1. `plugins/*/commands/[name].md`
2. `plugins/*/skills/[name].md`

If not found, display:
```
Command '[name]' not found.

Did you mean one of these?
  - [similar command 1]
  - [similar command 2]

Use '/help-commands' to see all available commands.
```

#### Step 2: Parse Command File

Extract from the markdown file:
- **Description**: From frontmatter `description` field
- **Tool Restrictions**: From frontmatter `allowed-tools` field (if present)
- **Input Validation**: From "Input Validation" section (if present)
- **Usage Examples**: From "Example Usage" section (if present)
- **Key Sections**: List main heading sections

#### Step 3: Display Detailed Help

Output format:

```
Command: /[name]
================

Description:
  [description from frontmatter]

Plugin: [plugin-name]
Type: [command|skill]
Tool Restrictions: [allowed-tools or "None"]

Usage:
  /[name] <required-arg> [optional-arg]

Arguments:
  <required-arg>    Description of required argument
  [optional-arg]    Description of optional argument (default: value)

Examples:
  /[name] example1
  /[name] example2 --flag

Sections:
  - Phase 1: [section name]
  - Phase 2: [section name]
  ...

Full documentation: plugins/[plugin]/[type]/[name].md
```

## Category Detection Logic

Use these heuristics to auto-categorize commands:

1. **Analysis**: Contains "review", "assessment", "analyze", "audit" in description AND has read-only instructions
2. **Interactive**: Contains "interactive", "Q&A", "ask", "answer" in description
3. **Generation**: Contains "generate", "create", "extract" AND creates output files
4. **Synthesis**: Contains "consolidate", "merge", "combine" in description
5. **Conversion**: Contains "convert", "transform", description mentions format changes
6. **Git/Automation**: Has `allowed-tools: Bash(git:*)` or mentions git/PR/commit
7. **Validation**: Contains "validate", "verify", "check" in description
8. **Planning**: Contains "plan", "improve", "recommend", "next" in description
9. **Cleanup**: Contains "cleanup", "organize", "refactor" in description
10. **Specialized**: Doesn't fit other categories

## Error Handling

- **No plugins found**: Report that no plugin directories exist
- **Malformed frontmatter**: Skip file and log warning
- **Missing description**: Use filename as fallback description
- **Empty directories**: Report "No commands found in [plugin]"

## Example Usage

```
User: /help-commands

Claude:
Available Commands and Skills
=============================

Analysis (Read-Only)
--------------------
  /arch-review       Deep architectural review with technical debt assessment
  /doc-assessment    Document quality evaluation with scored assessment report
  ...

[Full categorized list]

-----------------------------
Total: 17 commands, 3 skills

Use '/help-commands <name>' for detailed help on a specific command.
```

```
User: /help-commands ship

Claude:
Command: /ship
==============

Description:
  Create branch from main, commit all changes, push, and open a PR

Plugin: personal-plugin
Type: skill
Tool Restrictions: Bash(git:*), Bash(gh:*)

Usage:
  /ship [branch-name] [description]

Arguments:
  [branch-name]     Optional branch name (auto-generated if not provided)
  [description]     Optional description for PR body

Examples:
  /ship
  /ship fix-login-bug
  /ship feature/user-export "Add CSV export for user data"

Sections:
  - Pre-flight Checks
  - Step 1: Determine Branch Name
  - Step 2: Create and Switch to New Branch
  - Step 3: Stage and Commit
  - Step 4: Push to Remote
  - Step 5: Create Pull Request

Full documentation: plugins/personal-plugin/skills/ship.md
```

```
User: /help-commands foobar

Claude:
Command 'foobar' not found.

Did you mean one of these?
  - /wordify
  - /validate-plugin

Use '/help-commands' to see all available commands.
```
