---
description: Generate a new command file from a template with proper structure and conventions
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# New Command Generator

Generate a new command file for a plugin from one of the predefined templates. This command ensures consistency across all commands by using standardized patterns.

## Input Validation

**Optional Arguments:**
- `<command-name>` - Name for the new command (kebab-case)
- `<pattern-type>` - Template pattern: read-only, interactive, workflow, generator, utility, synthesis, conversion, planning, orchestration
- `--plugin <name>` - Target plugin to add the command to (auto-detected if only one plugin exists)

**Validation:**
If arguments are missing, the command will prompt interactively.

Command name must be:
- kebab-case format (e.g., `my-new-command`)
- Unique (not already exist in the target plugin's `commands/` or `skills/` directories)
- Descriptive but concise

## Instructions

### Phase 1: Determine Target Plugin

Before collecting command details, determine which plugin the command should be added to:

1. **Scan for available plugins** by reading `.claude-plugin/marketplace.json` and listing all registered plugins.

2. **If `--plugin <name>` was provided**, verify the plugin exists in `plugins/[name]/`. If not found, display:
   ```text
   Error: Plugin '[name]' not found.

   Available plugins:
     - personal-plugin
     - bpmn-plugin
     - [others...]

   Use --plugin <name> to specify a target plugin.
   ```

3. **If only one plugin exists**, use it automatically and inform the user:
   ```text
   Target plugin: personal-plugin (auto-detected, only plugin available)
   ```

4. **If multiple plugins exist and no --plugin flag**, prompt:
   ```text
   Multiple plugins detected. Which plugin should this command be added to?

   [1] personal-plugin  - Personal productivity and workflow tools
   [2] bpmn-plugin      - BPMN workflow generation and conversion
   [3] [other plugins...]

   Enter number or plugin name:
   ```

Store the selected plugin as `TARGET_PLUGIN` for use in subsequent phases.

### Phase 2: Gather Information

Interactively collect the following from the user:

#### 2.1 Command Name

Ask:
```text
What is the command name? (kebab-case, e.g., "analyze-logs")
```

**Validate:**
- Must be kebab-case: lowercase letters, numbers, hyphens only
- Must not start or end with a hyphen
- Must not contain consecutive hyphens
- Must not already exist in `plugins/[TARGET_PLUGIN]/commands/` or `plugins/[TARGET_PLUGIN]/skills/`

If invalid:
```text
Error: Command name must be kebab-case (e.g., 'my-command', 'analyze-data')
Invalid: [what was provided]
Reason: [specific reason]

Please provide a valid command name:
```

#### 2.2 Description

Ask:
```text
Provide a brief description (shown in /help):
```

**Validate:**
- Must be non-empty
- Should be concise (under 80 characters ideal)
- Should describe what the command does

#### 2.3 Pattern Type

Ask:
```text
Select the command pattern type:

[1] read-only      - Analysis commands that report without modifying
                     Examples: /review-arch, /assess-document

[2] interactive    - Q&A commands with single-question flow
                     Examples: /ask-questions, /finish-document

[3] workflow       - Multi-step automation with confirmations
                     Examples: /clean-repo, /ship

[4] generator      - Commands that create structured output files
                     Examples: /define-questions, /analyze-transcript

[5] utility        - Maintenance and validation commands
                     Examples: /validate-plugin, /bump-version

[6] synthesis      - Commands that merge multiple sources into one output
                     Examples: /consolidate-documents

[7] conversion     - Commands that transform files between formats
                     Examples: /convert-markdown, /convert-hooks

[8] planning       - Commands that analyze and generate improvement plans
                     Examples: /plan-improvements, /plan-next

[9] orchestration  - Commands that execute multi-phase plans via subagents
                     Examples: /implement-plan
                     Features: phase-based execution, state file tracking,
                     resume/rollback, quality gates, checkpoint management

Enter number (1-9) or pattern name:
```

### Phase 3: Generate Command File

#### 3.1 Load Template

Read the appropriate template from the target plugin's references (or fall back to personal-plugin templates):

**Template locations** (checked in order):
1. `plugins/[TARGET_PLUGIN]/references/templates/[pattern].md`
2. `plugins/personal-plugin/references/templates/[pattern].md`

Available templates:

| Pattern | Template File |
|---------|--------------|
| read-only | `references/templates/read-only.md` |
| interactive | `references/templates/interactive.md` |
| workflow | `references/templates/workflow.md` |
| generator | `references/templates/generator.md` |
| utility | `references/templates/utility.md` |
| synthesis | `references/templates/synthesis.md` |
| conversion | `references/templates/conversion.md` |
| planning | `references/templates/planning.md` |
| orchestration | Based on `implement-plan.md` structure: Agent-based subagent execution, state file tracking (`[plan]-state.json`), `--resume` flag, `--rollback` flag, phase boundary quality gates, testing circuit breaker, partial completion reporting |

If the template file is not found, report the error and list available templates:
```text
Error: Template not found for pattern '[pattern]'

Searched:
  1. plugins/[TARGET_PLUGIN]/references/templates/[pattern].md  (not found)
  2. plugins/personal-plugin/references/templates/[pattern].md  (not found)

Available templates:
  - read-only, interactive, workflow, generator, utility, synthesis, conversion, planning

For the 'orchestration' pattern, the command structure is generated inline
based on the implement-plan.md reference pattern.
```

#### 3.2 Customize Template

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
- orchestration: "Execute a phased plan via Agent tool subagents with state tracking, resume, rollback, and quality gates."

**Determine output location** (for generators, synthesis, planning):
- Analysis reports -> `reports/`
- Reference data (JSON) -> `reference/`
- Planning documents -> repository root
- Consolidated documents -> `reports/`
- Other -> prompt user

#### 3.3 Write Command File

Save to: `plugins/[TARGET_PLUGIN]/commands/[command-name].md`

### Phase 4: Post-Generation Validation

After creating the command file, perform a quick validation:

1. **Verify frontmatter** -- check the generated file has `description` in the YAML frontmatter
2. **Verify file location** -- confirm the file is in the correct `plugins/[TARGET_PLUGIN]/commands/` directory
3. **Check for duplicates** -- verify no other command in the same plugin has the same filename
4. **Validate structure** -- ensure the file has required sections (Input Validation, Instructions, Error Handling, Related Commands)

Report validation results:
```text
Post-generation validation:
  Frontmatter:   PASS (description present)
  File location:  PASS (plugins/[TARGET_PLUGIN]/commands/)
  Unique name:    PASS (no duplicates found)
  Structure:      PASS (all required sections present)
```

### Phase 5: Remind About Documentation Updates

Display:
```text
----------------------------------------------
Command Generated Successfully!
----------------------------------------------

File created: plugins/[TARGET_PLUGIN]/commands/[command-name].md

**Required Next Steps:**

1. Edit the generated file to complete:
   - [ ] Customize phases/instructions for your specific use case
   - [ ] Add specific validation logic
   - [ ] Write example usage scenarios
   - [ ] Review and adjust error handling

2. Update documentation:
   - [ ] Update the plugin's `skills/help/SKILL.md` with the new command entry
   - [ ] Add entry to CHANGELOG.md under [Unreleased]

3. Validate:
   - [ ] Run: /validate-plugin [TARGET_PLUGIN]

**Pattern Documentation:**
See plugins/personal-plugin/references/common-patterns.md for conventions.
See plugins/personal-plugin/references/templates/ for all available templates.
```

## Output

**File Location:** `plugins/[TARGET_PLUGIN]/commands/[command-name].md`

The generated file will contain:
- Proper frontmatter with description and allowed-tools
- Appropriate structure for the selected pattern
- Placeholder sections to customize
- Standard conventions (timestamps, output locations, etc.)
- Error handling section
- Related commands section

## Example Usage

```yaml
User: /new-command

Claude:
Multiple plugins detected. Which plugin should this command be added to?

[1] personal-plugin  - Personal productivity and workflow tools
[2] bpmn-plugin      - BPMN workflow generation and conversion

Enter number or plugin name:

User: 1

Claude:
Target plugin: personal-plugin

What is the command name? (kebab-case, e.g., "analyze-logs")

User: check-dependencies

Claude:
Provide a brief description (shown in /help):

User: Scan project dependencies and report outdated or vulnerable packages

Claude:
Select the command pattern type:

[1] read-only      - Analysis commands
[2] interactive    - Q&A commands
[3] workflow       - Multi-step automation
[4] generator      - Output generation
[5] utility        - Maintenance commands
[6] synthesis      - Merge multiple sources
[7] conversion     - Format transformation
[8] planning       - Improvement planning
[9] orchestration  - Plan execution via subagents

Enter number (1-9) or pattern name:

User: 1

Claude:
Post-generation validation:
  Frontmatter:   PASS
  File location:  PASS
  Unique name:    PASS
  Structure:      PASS

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
   - [ ] Update the plugin's `skills/help/SKILL.md` with the new command entry

3. Validate:
   - [ ] Run: /validate-plugin personal-plugin
```

```yaml
User: /new-command export-data generator --plugin bpmn-plugin

Claude:
Target plugin: bpmn-plugin

Provide a brief description (shown in /help):

User: Export BPMN data to various formats for external tools

Claude:
----------------------------------------------
Command Generated Successfully!
----------------------------------------------

File created: plugins/bpmn-plugin/commands/export-data.md

...
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Template not found | No template file for the selected pattern | Report missing template, list available templates, suggest using a similar pattern |
| Command already exists | File with same name in target plugin's `commands/` | Report conflict, suggest alternative name |
| Invalid name format | Name contains uppercase, spaces, or special characters | Explain kebab-case requirement with valid examples |
| Write permission denied | Cannot write to plugin directory | Report error and suggest checking file permissions |
| Target plugin not found | `--plugin` value doesn't match any registered plugin | List available plugins from marketplace.json |
| No plugins available | `plugins/` directory is empty or has no valid plugins | Suggest running `/scaffold-plugin` first |

## Related Commands

- `/new-skill` -- Generate a new skill with nested directory structure and required frontmatter
- `/scaffold-plugin` -- Create an entire new plugin with proper structure
- `/validate-plugin` -- Validate the plugin after adding a new command
- `/bump-version` -- Update plugin version after adding new commands
