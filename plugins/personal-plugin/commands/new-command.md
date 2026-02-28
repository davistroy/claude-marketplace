---
description: Generate a new command file from a template with proper structure and conventions
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# New Command Generator

Generate a new command file for this plugin from one of the predefined templates. This command ensures consistency across all commands by using standardized patterns.

## Input Validation

**Optional Arguments:**
- `<command-name>` - Name for the new command (kebab-case)
- `<pattern-type>` - Template pattern: read-only, interactive, workflow, generator, utility, synthesis, conversion, planning

**Validation:**
If arguments are missing, the command will prompt interactively.

Command name must be:
- kebab-case format (e.g., `my-new-command`)
- Unique (not already exist in commands/ or skills/)
- Descriptive but concise

## Instructions

### Phase 1: Gather Information

Interactively collect the following from the user:

#### 1.1 Command Name

Ask:
```text
What is the command name? (kebab-case, e.g., "analyze-logs")
```

**Validate:**
- Must be kebab-case: lowercase letters, numbers, hyphens only
- Must not start or end with a hyphen
- Must not contain consecutive hyphens
- Must not already exist in `plugins/personal-plugin/commands/` or `plugins/personal-plugin/skills/`

If invalid:
```text
Error: Command name must be kebab-case (e.g., 'my-command', 'analyze-data')
Invalid: [what was provided]
Reason: [specific reason]

Please provide a valid command name:
```

#### 1.2 Description

Ask:
```text
Provide a brief description (shown in /help):
```

**Validate:**
- Must be non-empty
- Should be concise (under 80 characters ideal)
- Should describe what the command does

#### 1.3 Pattern Type

Ask:
```text
Select the command pattern type:

[1] read-only    - Analysis commands that report without modifying
                   Examples: /review-arch, /assess-document

[2] interactive  - Q&A commands with single-question flow
                   Examples: /ask-questions, /finish-document

[3] workflow     - Multi-step automation with confirmations
                   Examples: /clean-repo, /ship

[4] generator    - Commands that create structured output files
                   Examples: /define-questions, /analyze-transcript

[5] utility      - Maintenance and validation commands
                   Examples: /validate-plugin, /bump-version

[6] synthesis    - Commands that merge multiple sources into one output
                   Examples: /consolidate-documents

[7] conversion   - Commands that transform files between formats
                   Examples: /convert-markdown

[8] planning     - Commands that analyze and generate improvement plans
                   Examples: /plan-improvements, /plan-next

Enter number (1-8) or pattern name:
```

### Phase 2: Generate Command File

#### 2.1 Load Template

Read the appropriate template from:
- `plugins/personal-plugin/references/templates/read-only.md`
- `plugins/personal-plugin/references/templates/interactive.md`
- `plugins/personal-plugin/references/templates/workflow.md`
- `plugins/personal-plugin/references/templates/generator.md`
- `plugins/personal-plugin/references/templates/utility.md`
- `plugins/personal-plugin/references/templates/synthesis.md`
- `plugins/personal-plugin/references/templates/conversion.md`
- `plugins/personal-plugin/references/templates/planning.md`

#### 2.2 Customize Template

Replace placeholders in the template:

| Placeholder | Replace With |
|-------------|--------------|
| `{{COMMAND_NAME}}` | The command name (e.g., `analyze-logs`) |
| `{{TITLE}}` | Title case version (e.g., `Analyze Logs`) |
| `{{DESCRIPTION}}` | User-provided description |
| `{{INTRO_PARAGRAPH}}` | Generated introduction paragraph |
| `{{ARG_NAME}}` | Primary argument name based on pattern |
| `{{ARG_DESCRIPTION}}` | Primary argument description |
| `{{OUTPUT_PREFIX}}` | Output file prefix (for generators) |
| `{{OUTPUT_EXT}}` | Output file extension (for generators) |
| `{{OUTPUT_LOCATION}}` | Output directory (per common-patterns.md) |

**Generate intro paragraph** based on pattern:
- read-only: "Perform a [description] analysis. This command provides in-conversation analysis without generating files."
- interactive: "Interactively walk the user through [description]."
- workflow: "Perform [description]. Execute each phase systematically."
- generator: "Analyze the specified input and generate [description]."
- utility: "Perform [description] to maintain repository quality."
- synthesis: "Consolidate multiple sources into a single optimized [description]."
- conversion: "Convert [input format] to [output format] for [description]."
- planning: "Analyze the codebase and generate [description] with phased implementation plan."

**Determine output location** (for generators, synthesis, planning):
- Analysis reports -> `reports/`
- Reference data (JSON) -> `reference/`
- Planning documents -> repository root
- Consolidated documents -> `reports/`
- Other -> prompt user

#### 2.3 Write Command File

Save to: `plugins/personal-plugin/commands/[command-name].md`

### Phase 3: Post-Generation Tasks

#### 3.1 Remind About Documentation Updates

Display:
```text
----------------------------------------------
Command Generated Successfully!
----------------------------------------------

File created: plugins/personal-plugin/commands/[command-name].md

**Required Next Steps:**

1. Edit the generated file to complete:
   - [ ] Customize phases/instructions
   - [ ] Add specific validation logic
   - [ ] Write example usage

2. Update documentation:
   - [ ] Run: python scripts/generate-help.py plugins/personal-plugin
   - [ ] Run: python scripts/update-readme.py (if available)
   - [ ] Add entry to CHANGELOG.md under [Unreleased]

3. Validate:
   - [ ] Run: /validate-plugin personal-plugin

**Pattern Documentation:**
See plugins/personal-plugin/references/common-patterns.md for conventions.
```

## Output

**File Location:** `plugins/personal-plugin/commands/[command-name].md`

The generated file will contain:
- Proper frontmatter with description
- Appropriate structure for the selected pattern
- Placeholder sections to customize
- Standard conventions (timestamps, output locations, etc.)

## Example Usage

```yaml
User: /new-command

Claude:
What is the command name? (kebab-case, e.g., "analyze-logs")

User: check-dependencies

Claude:
Provide a brief description (shown in /help):

User: Scan project dependencies and report outdated or vulnerable packages

Claude:
Select the command pattern type:

[1] read-only    - Analysis commands
[2] interactive  - Q&A commands
[3] workflow     - Multi-step automation
[4] generator    - Output generation
[5] utility      - Maintenance commands
[6] synthesis    - Merge multiple sources
[7] conversion   - Format transformation
[8] planning     - Improvement planning

Enter number (1-8) or pattern name:

User: 1

Claude:
----------------------------------------------
Command Generated Successfully!
----------------------------------------------

File created: plugins/personal-plugin/commands/check-dependencies.md

**Required Next Steps:**

1. Edit the generated file to complete:
   - [ ] Customize phases/instructions
   - [ ] Add specific validation logic
   - [ ] Write example usage

2. Update documentation:
   - [ ] Run: python scripts/generate-help.py plugins/personal-plugin
   - [ ] Run: python scripts/update-readme.py (if available)
   - [ ] Add entry to CHANGELOG.md under [Unreleased]

3. Validate:
   - [ ] Run: /validate-plugin personal-plugin
```

```yaml
User: /new-command export-data generator

Claude:
Provide a brief description (shown in /help):

User: Export project data to various formats for external tools

Claude:
----------------------------------------------
Command Generated Successfully!
----------------------------------------------

File created: plugins/personal-plugin/commands/export-data.md

...
```

## Error Handling

- **Template not found:** Report missing template and available templates
- **Command already exists:** Report conflict and suggest alternative name
- **Invalid name format:** Explain kebab-case requirement with examples
- **Write permission denied:** Report error and suggest checking permissions
