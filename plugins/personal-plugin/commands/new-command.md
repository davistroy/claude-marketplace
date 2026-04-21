---
description: Generate a new command file from a template with proper structure and conventions
argument-hint: "[<command-name>] [<pattern-type>] [--plugin <name>]"
effort: low
allowed-tools: Read, Write, Edit, Glob, Grep
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
                     Modern: dispatch analysis phases to context: fork + agent: Explore
                             for isolation; use dynamic injection for file inventory

[2] interactive    - Q&A commands with single-question flow
                     Examples: /ask-questions, /finish-document

[3] workflow       - Multi-step automation with confirmations
                     Examples: /clean-repo, /ship
                     Modern: use dynamic injection (!`git status -s`) to pre-load
                             context before Claude sees the prompt

[4] generator      - Commands that create structured output files
                     Examples: /define-questions, /analyze-transcript

[5] utility        - Maintenance and validation commands
                     Examples: /validate-plugin, /bump-version

[6] synthesis      - Commands that merge multiple sources into one output
                     Examples: /consolidate-documents
                     Modern: dispatch per-source analysis to parallel context: fork
                             subagents; parent aggregates and writes final output

[7] conversion     - Commands that transform files between formats
                     Examples: /convert-markdown

[8] planning       - Commands that analyze and generate improvement plans
                     Examples: /plan-improvements, /plan-next

[9] orchestration  - Commands that execute multi-phase plans via subagents
                     Examples: /implement-plan
                     Features: phase-based execution, state file tracking,
                     resume/rollback, quality gates, checkpoint management
                     Modern: use context: fork + isolation: worktree per phase
                             so each phase gets an isolated working tree; merge
                             to main branch at phase boundary

Enter number (1-9) or pattern name:
```

#### 2.4 Modern Features (Optional)

After the user selects a pattern type, prompt for optional modern feature configuration:

```text
Would you like to enable any modern Claude Code features? (leave empty to skip)

Available features (can combine):
  [A] Dynamic context injection  - Pre-load file content or command output
                                   before Claude reads the prompt
                                   Example: !`git status -s`, !`cat package.json`

  [B] context: fork dispatch     - Run analysis phases in isolated subagent
                                   contexts (no conversation history bleed)
                                   Best for: read-only, synthesis, orchestration

  [C] isolation: worktree        - Give each phase/subagent its own git worktree
                                   Best for: orchestration commands writing files

  [D] paths: auto-activation     - Trigger command automatically when specified
                                   files change (requires loop guard in body)

  [E] effort: level              - Declare compute budget: low/medium/high/max

  [F] None - generate a standard command

Enter letters (e.g., "A B" or "ACE") or press Enter to skip:
```

If the user selects features, note them for inclusion in the generated frontmatter and body.

**Modern frontmatter fields reference** (see `references/common-patterns.md` Advanced Features section for full details):

| Field | Command Use | Example Value |
|-------|------------|---------------|
| `description` | REQUIRED — shown in /help | `"Analyze and report X"` |
| `argument-hint` | Shown in /help usage line | `"<file> [--flag]"` |
| `effort` | Declare compute budget | `low` / `medium` / `high` / `max` |
| `allowed-tools` | Restrict tool access | `Read, Glob, Grep, Bash(git:*)` |
| `context` | Subagent context mode | `fork` (isolated, no history) |
| `agent` | Subagent role specialization | `Explore` / `Edit` / `Research` |
| `model` | Override model per subagent | `claude-opus-4-5` |
| `isolation` | Filesystem isolation | `worktree` |
| `when_to_use` | Proactive trigger phrases | `"when X needs to happen"` |

**Critical:** Do NOT include `name` in command frontmatter — it breaks command discovery. The `name` field is only for skills.

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

**Generate frontmatter** based on pattern and user-selected modern features:

Minimal (no modern features selected):
```yaml
---
description: {{DESCRIPTION}}
argument-hint: "<required-arg> [--flag]"
effort: medium
allowed-tools: Read, Glob, Grep
---
```

With modern features (example: read-only + context fork + effort):
```yaml
---
description: {{DESCRIPTION}}
argument-hint: "<target> [--focus <area>]"
effort: high
allowed-tools: Read, Glob, Grep, Bash
# context: fork          # Uncomment to dispatch analysis to isolated subagent
# agent: Explore         # Uncomment to specialize subagent role
# isolation: worktree    # Uncomment for filesystem isolation (orchestration only)
# when_to_use: "when X"  # Uncomment to enable proactive suggestion
---
```

With orchestration pattern (inject worktree isolation guidance):
```yaml
---
description: {{DESCRIPTION}}
argument-hint: "[--input <plan.md>] [--pause-between-phases] [--auto-merge]"
effort: max
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---
```

**CRITICAL:** Never generate a `name` field in command frontmatter — it breaks command discovery in Claude Code. The `name` field is only valid in skill frontmatter (SKILL.md files).

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
2. **Verify no `name` field** -- commands must NOT have `name` in frontmatter (breaks discovery)
3. **Verify file location** -- confirm the file is in the correct `plugins/[TARGET_PLUGIN]/commands/` directory
4. **Check for duplicates** -- verify no other command in the same plugin has the same filename
5. **Validate structure** -- ensure the file has required sections (Input Validation, Instructions, Error Handling, Related Commands)

Report validation results:
```text
Post-generation validation:
  Frontmatter:   PASS (description present, no name field)
  File location:  PASS (plugins/[TARGET_PLUGIN]/commands/)
  Unique name:    PASS (no duplicates found)
  Structure:      PASS (all required sections present)
  Modern fields: [PRESENT / COMMENTED / NONE] (effort, allowed-tools, context)
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
   - [ ] Uncomment modern frontmatter fields that apply (effort, context, isolation)

2. Update documentation:
   - [ ] Add entry to CHANGELOG.md under [Unreleased]

3. Validate:
   - [ ] Run: /validate-plugin [TARGET_PLUGIN]

**Pattern Documentation:**
See plugins/personal-plugin/references/common-patterns.md for conventions.
See plugins/personal-plugin/references/common-patterns.md#advanced-features for
    modern fields: context:fork, isolation:worktree, dynamic injection, paths:
See plugins/personal-plugin/references/templates/ for all available templates.

**Modern Feature Reference:**
See new-command.md Worked Examples section for read-only, orchestration, and
synthesis patterns with modern dispatch.
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

2. Validate:
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

## Worked Examples: Modern Pattern Commands

These examples show what high-quality generated commands look like with modern features applied. Use these as reference when customizing generated output.

### Example A: Read-Only + Dynamic Injection

A read-only analysis command that pre-loads git context before Claude reads the prompt:

```markdown
---
description: Analyze commit history and flag unusual change patterns
argument-hint: "[--since <date>] [--author <name>]"
effort: medium
allowed-tools: Read, Glob, Grep, Bash(git:*)
---

# Commit Pattern Analyzer

Analyze the git commit history for unusual patterns, large diffs, or
off-hours commits. Reports findings without modifying anything.

<!-- Dynamic injection: these run before Claude reads the prompt -->
Current branch: !`git branch --show-current`
Recent commits: !`git log --oneline -20`
Change stats: !`git diff --stat HEAD~10..HEAD`

## Instructions

### Phase 1: Review Injected Context

Use the pre-loaded git data above. Do not re-run git commands for data
already provided.
...
```

### Example B: Orchestration + context:fork + isolation:worktree

A multi-phase orchestration command that isolates each phase in its own worktree:

```markdown
---
description: Execute a phased refactoring plan across multiple modules
argument-hint: "<plan.md> [--pause-between-phases] [--dry-run]"
effort: max
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# Refactor Executor

Execute a phased refactoring plan. Each phase runs in an isolated worktree
and merges to the working branch on phase completion.

## Instructions

### Phase 1: Load Plan

Read the plan file specified by the user. Validate it has the expected
structure (phases → work items).

### Phase 2: Execute Phases

For each phase in the plan, dispatch a Task subagent with:
- context: fork       (isolated context, no bleed from prior phases)
- isolation: worktree (dedicated filesystem for this phase's changes)
- Instruction: "Complete ALL work items in Phase N. Merge to branch on
  completion. Write a brief summary of changes made."

If `--pause-between-phases` is set, present phase summary and ask for
confirmation before dispatching the next phase.

### Phase 3: Final Report

After all phases complete, read the per-phase summaries and generate a
consolidated report: what changed, what was skipped, and next steps.
```

### Example C: Synthesis + Parallel context:fork Dispatch

A synthesis command that dispatches one subagent per source for parallel analysis:

```markdown
---
description: Synthesize findings from multiple audit reports into a unified executive brief
argument-hint: "<reports-dir> [--format <md|docx>]"
effort: high
allowed-tools: Read, Write, Glob, Grep, Task
---

# Audit Synthesizer

Read all audit report files in the specified directory, dispatch parallel
analysis subagents (one per report), then synthesize into a single
executive brief.

## Instructions

### Phase 1: Discover Reports

Use Glob to find all `*.md` files in `<reports-dir>`. Validate at least
2 reports exist.

### Phase 2: Parallel Analysis

For each report file, dispatch a Task with context: fork:
- Instruction: "Read [report-path]. Extract: (1) critical findings,
  (2) top 3 recommendations, (3) severity counts. Return structured
  JSON summary."

Collect all subagent responses before proceeding. Do NOT write any
files during this phase — leave writing to Phase 3.

### Phase 3: Synthesize and Write

Merge subagent responses into a unified executive brief. Write to
`reports/audit-synthesis-YYYYMMDD-HHMMSS.md`.
```

---

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Template not found | No template file for the selected pattern | Report missing template, list available templates, suggest using a similar pattern |
| Command already exists | File with same name in target plugin's `commands/` | Report conflict, suggest alternative name |
| Invalid name format | Name contains uppercase, spaces, or special characters | Explain kebab-case requirement with valid examples |
| Write permission denied | Cannot write to plugin directory | Report error and suggest checking file permissions |
| Target plugin not found | `--plugin` value doesn't match any registered plugin | List available plugins from marketplace.json |
| No plugins available | `plugins/` directory is empty or has no valid plugins | Suggest running `/scaffold-plugin` first |

## Performance

Typically completes in under 15 seconds once all inputs are provided.

## Related Commands

- `/new-skill` -- Generate a new skill with nested directory structure and required frontmatter
- `/scaffold-plugin` -- Create an entire new plugin with proper structure
- `/validate-plugin` -- Validate the plugin after adding a new command
- `/bump-version` -- Update plugin version after adding new commands
