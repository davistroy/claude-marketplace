## Operational Rules — Learning Capture

**These rules apply in every session. Do not skip them.**

### When a plugin structure issue, discovery failure, or marketplace problem is diagnosed and fixed

After any non-trivial finding during plugin development, validation, or marketplace integration:

1. **Update `CLAUDE.md`** (this file) — add or update a bullet in the relevant section with the operational rule. This is the always-loaded, always-enforced file.
2. **Update the memory file** — write a detailed entry in `C:\Users\Troy Davis\.claude\projects\C--Users-Troy-Davis-dev-personal-claude-marketplace\memory\` in the appropriate topic file. Include the root cause, the fix, and what to watch for.
3. **Update `MEMORY.md`** — add a concise bullet + link to the topic file so it survives context compaction.

### What counts as a "non-trivial finding"

- Any plugin discovery failure (skill not found, command not loading, marketplace install error)
- Any frontmatter requirement discovered (missing `name` field, wrong key format)
- Any directory structure requirement (flat commands vs nested skills)
- Any Python tool invocation issue (PYTHONPATH, dependency gaps, entry point naming)
- Any fix that took more than one attempt to get right

### Learning file locations

| File | Purpose | When to write |
|------|---------|---------------|
| `CLAUDE.md` (this file) | Operational rules, always enforced | Every session with new learnings |
| `memory/MEMORY.md` | Concise index, survives compaction | After each new topic file entry |
| `memory/plugin-structure-learnings.md` | Discovery failures, frontmatter, directory layout | Plugin structure findings |
| `memory/marketplace-learnings.md` | Install behavior, versioning, namespace collisions | Marketplace findings |
| `memory/tool-integration-learnings.md` | Python tool invocation, PYTHONPATH, deps | Tool integration findings |

### Verified operational rules (do not repeat these mistakes)

- **Skills MUST use nested directory structure** — `skills/name/SKILL.md` not `skills/name.md`. Flat files are not discovered.
- **Skills MUST have `name` in frontmatter** — without it the skill is not registered.
- **Commands MUST NOT have `name` in frontmatter** — adding `name` prevents command discovery.
- **Do NOT add `tools` field to plugin.json** — causes "Unrecognized key: tools" error.

---

# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

This is a Claude Code plugin marketplace repository. It contains multiple plugins that extend Claude Code's functionality with specialized workflows for documentation review, architecture analysis, git workflows, document processing, and BPMN workflow generation.

## Marketplace Installation (For Users)

Users install plugins from this marketplace using the official Claude Code plugin system:

```
# Step 1: Add the marketplace
/plugin marketplace add davistroy/claude-marketplace

# Step 2: Install desired plugins
/plugin install personal-plugin@troys-plugins
/plugin install bpmn-plugin@troys-plugins
```

**Installation scopes:**
- `--scope user` - Global installation (all projects)
- `--scope project` - Team-shared (.claude/settings.json)
- `--scope local` - Personal only (gitignored)

## Marketplace Compatibility (For Developers)

**CRITICAL:** All changes must maintain compatibility with the official Claude Code marketplace installation system. The repository structure is NOT arbitrary - it follows the required format for `/plugin marketplace add` to work.

### Required Structure

```
.claude-plugin/
  marketplace.json          # REQUIRED: Central registry - Claude Code reads this first

plugins/
  [plugin-name]/
    .claude-plugin/
      plugin.json           # REQUIRED: Plugin metadata (name, version, description)
    commands/               # Slash commands (*.md files, flat structure)
    skills/                 # Proactive skills (nested directories with SKILL.md)
      [skill-name]/
        SKILL.md            # REQUIRED: Must be named exactly SKILL.md (uppercase)
```

**CRITICAL: Commands vs Skills Directory Structure**

| Component | Structure | Example |
|-----------|-----------|---------|
| Commands | Flat: `commands/name.md` | `commands/validate-plugin.md` |
| Skills | Nested: `skills/name/SKILL.md` | `skills/ship/SKILL.md` |

Skills require a **nested folder structure** where the file must be named exactly `SKILL.md` (uppercase). This is required by Claude Code for skill discovery.

### What Must NOT Change

| Item | Why |
|------|-----|
| `.claude-plugin/marketplace.json` location | Claude Code expects this at repo root |
| `plugins/[name]/.claude-plugin/plugin.json` location | Standard plugin metadata location |
| Marketplace name `troys-plugins` | Users reference this in install commands |
| Plugin names in marketplace.json | Must match directory names exactly |

### Testing Marketplace Compatibility

Before pushing changes, verify the marketplace still works:

```
# In a fresh Claude Code session:
/plugin marketplace add davistroy/claude-marketplace
/plugin install personal-plugin@troys-plugins
/help
```

If `/help` shows your plugin's commands, the marketplace integration works.

## Repository Structure

```
.claude-plugin/
  marketplace.json          # Marketplace config with plugin registry

plugins/
  personal-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    commands/
      analyze-transcript.md   # Meeting transcript to structured markdown report
      ask-questions.md        # Interactive Q&A session from questions JSON file
      assess-document.md      # Document quality evaluation with scored assessment report
      bump-version.md         # Automate version bumping across plugin files with CHANGELOG placeholder
      clean-repo.md           # Comprehensive repository cleanup, organization, and documentation refresh
      consolidate-documents.md # Analyze multiple document variations and synthesize a superior consolidated version
      convert-markdown.md     # Convert a markdown file to a nicely formatted Microsoft Word document
      create-plan.md          # Generate detailed IMPLEMENTATION_PLAN.md from requirements documents (BRD, PRD, TDD, design specs)
      define-questions.md     # Extract questions/TBDs from docs to JSON
      develop-image-prompt.md # Generate detailed image generator prompts from content, with configurable dimensions and style options
      finish-document.md      # Extract questions from a document, answer them interactively, and update the document
      implement-plan.md       # Execute IMPLEMENTATION_PLAN.md using orchestrated subagents with automatic testing, documentation, and git workflow
      new-command.md          # Generate a new command file from a template with proper structure and conventions
      new-skill.md            # Generate a new skill file with proper nested directory structure and required frontmatter
      plan-improvements.md    # Analyze codebase and generate prioritized improvement recommendations with phased implementation plan
      plan-next.md            # Analyze repo and recommend the next logical action
      remove-ip.md            # Sanitize documents by removing company identifiers and non-public intellectual property
      review-arch.md          # Quick architectural audit with technical debt assessment (read-only, no files generated)
      review-intent.md        # Determine original project intent and compare against current implementation, reporting discrepancies
      review-pr.md            # Structured PR review with security, performance, and code quality analysis
      scaffold-plugin.md      # Create a new plugin with proper directory structure, metadata, and starter files
      test-project.md         # Ensure 90%+ test coverage, run all tests with sub-agents, fix failures, then create PR
      validate-plugin.md      # Validate plugin structure, frontmatter, and content for consistency and correctness
    deprecated/               # Archived commands (convert-hooks, setup-statusline, check-updates)
    skills/
      help/
        SKILL.md            # Show available commands and skills with usage information (static table, manually maintained)
      plan-gate/
        SKILL.md            # Assess scope and route to the right planning approach (native plan mode, /plan-improvements, or /create-plan)
      prime/
        SKILL.md            # Evaluate an existing codebase to produce a detailed report on project purpose, health, status, and next steps
      research-topic/
        SKILL.md            # Orchestrate parallel deep research across multiple LLM providers and synthesize results
      security-analysis/
        SKILL.md            # Comprehensive security analysis with tech stack detection, vulnerability scanning, and remediation planning
      ship/
        SKILL.md            # Create branch, commit, push, open PR, auto-review, fix issues, and merge
      summarize-feedback/
        SKILL.md            # Synthesize employee feedback from Notion Voice Captures into a professional .docx assessment document
      unlock/
        SKILL.md            # Load secrets from Bitwarden Secrets Manager into environment using bws CLI
      release-plugin/
        SKILL.md            # Validate plugins, clean repository, and ship plugin releases in one automated workflow
      evaluate-pipeline-output/
        SKILL.md            # Evaluate contact-center-lab pipeline output quality
      visual-explainer/
        SKILL.md            # Transform text or documents into AI-generated infographic pages using Gemini Pro 3 and Claude Vision
      leak-risk-audit/
        SKILL.md            # Audit datasets for proprietary information leaks before sharing with public/cloud services
      spec-to-prototype/
        SKILL.md            # Build visual HTML/CSS prototypes from spec documents or wireframe descriptions
      accessibility-annotator/
        SKILL.md            # Analyze technical documents for CS/ML concepts and add explanation annotations for non-CS readers
      brain-entry/
        SKILL.md            # Send captures to Open Brain — summarize sessions, log decisions, capture ideas
      explain-project/
        SKILL.md            # Generate comprehensive annotated technical overview document for non-technical stakeholders
      lab-notebook/
        SKILL.md            # Initialize mandatory experiment logging with scientific notebook, ADR, and postmortem patterns
      spark-recon/
        SKILL.md            # Periodic intelligence scan of DGX Spark inference performance landscape
      ultra-plan/
        SKILL.md            # Structured implementation planning for bug lists, feature requests, or change sets
    references/
      common-patterns.md    # Shared patterns for timestamps, naming, etc.
      api-key-setup.md      # Bitwarden-based API key setup workflow
      flag-consistency.md   # Comprehensive flag reference across all commands
      plan-template.md      # Shared IMPLEMENTATION_PLAN.md template for create-plan and plan-improvements
      research-models.md    # LLM provider model configuration for research-topic
      validation-maturity-scorecard.md  # Plugin maturity scoring rubric for validate-plugin
      patterns/             # Extracted pattern references (logging, naming, output, etc.)
      templates/            # Command/skill pattern templates (conversion, generator, etc.)
    hooks/
      hooks.json              # Workflow automation hooks (Stop, SessionStart)
    tools/
      feedback-docx-generator/ # Python tool for feedback assessment .docx generation (run via PYTHONPATH)
      research-orchestrator/  # Python tool for multi-LLM research (run via PYTHONPATH)
      visual-explainer/       # Python tool for AI image generation from documents (run via PYTHONPATH)

  bpmn-plugin/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/
      bpmn-generator/
        SKILL.md            # BPMN 2.0 XML generation from NL or markdown
      bpmn-to-drawio/
        SKILL.md            # Convert BPMN XML to Draw.io format
      help/
        SKILL.md            # Show skills with usage information
    references/             # BPMN element documentation and guides
      archive/              # Historical reference documents
    templates/              # XML/Draw.io skeletons and style mappings
    examples/               # Sample BPMN and Draw.io files
    tools/
      bpmn2drawio/          # Python tool for BPMN→Draw.io conversion (run via PYTHONPATH)
```

## Commands vs Skills

- **Commands** (`/command-name`): User-initiated workflows. Comprehensive, standalone, take control of the session.
- **Skills** (`/skill-name`): Discrete actions Claude may proactively suggest after completing related work.

### Directory Structure Differences

**CRITICAL:** Commands and skills use different directory structures:

| Component | Directory Structure | File Naming |
|-----------|---------------------|-------------|
| Commands | Flat: `commands/name.md` | Any `.md` filename becomes the command name |
| Skills | Nested: `skills/name/SKILL.md` | **Must be `SKILL.md` (uppercase, exact)** |

**Why skills need nested directories:**
- Claude Code scans for `skills/*/SKILL.md` pattern specifically
- The directory name becomes the skill name
- Flat `.md` files in `skills/` are NOT discovered

**Correct skill structure:**
```
skills/
  ship/                    # Directory name = skill name (/ship)
    SKILL.md               # Must be exactly this filename
  help/
    SKILL.md
```

**Incorrect (will NOT be discovered):**
```
skills/
  ship.md                  # ❌ Flat file - NOT discovered
  help.md                  # ❌ Flat file - NOT discovered
```

### Skill Frontmatter Requirements

**CRITICAL:** Skills MUST include a `name` field in their YAML frontmatter. Without this field, the skill will not be registered and will not appear in the available skills list.

```yaml
---
name: ship                    # REQUIRED: Must match directory name
description: Brief description of what the skill does
argument-hint: "<branch-name> [draft]"  # Optional: UI hint for arguments
effort: high                  # Optional: Thinking depth (low/medium/high/max)
disable-model-invocation: true # Optional: Prevent auto-triggering
allowed-tools: Bash(git:*)    # Optional: Tool restrictions
---
```

**Required fields:**
- `name` - Must exactly match the skill's directory name (e.g., `ship` for `skills/ship/SKILL.md`)
- `description` - Brief description shown in skill list and used for proactive suggestions

**Optional fields:**
- `argument-hint` - UI hint showing expected arguments (e.g., `"<file-path> [--verbose]"`)
- `effort` - Thinking depth: `low` (routing), `medium` (moderate analysis), `high` (deep analysis), `max` (exhaustive analysis)
- `disable-model-invocation` - Set `true` to prevent Claude from auto-triggering (use for destructive skills like `ship`)
- `allowed-tools` - Restrict which tools the skill can use
- `context` - Set to `fork` to run in isolated subagent context
- `agent` - Route to specific agent type (`Explore`, `Plan`, `general-purpose`)
- `version` - Skill version for tracking changes
- `license` - License information

**Example comparison:**

| Working Skill | Non-Working Skill |
|---------------|-------------------|
| `name: ship` ✅ | (missing name) ❌ |
| `description: Create branch...` | `description: Create branch...` |

## Command Conventions

### Frontmatter Structure
```yaml
---
description: Brief description shown in command list
argument-hint: "<required-arg> [--optional-flag]"  # UI hint for arguments
effort: high                 # Thinking depth (optional)
allowed-tools: Bash(git:*)   # Tool restrictions (optional)
---
```

**Important:** Do NOT include a `name` field in frontmatter - the filename determines the command name. Adding `name` can prevent command discovery.

### Naming
- Use kebab-case for command filenames
- Commands are invoked as `/filename` (without .md extension)

### Patterns Used
- **Read-only commands** (`review-arch`, `assess-document`, `review-intent`, `review-pr`): Analyze and report, never modify
- **Interactive commands** (`ask-questions`, `finish-document`): Single-question flow, wait for user input
- **Workflow commands** (`ship` skill): Multi-step automation with confirmation points
- **Generator commands** (`define-questions`, `analyze-transcript`): Create structured output files
- **Synthesis commands** (`consolidate-documents`): Merge multiple sources into optimized output
- **Conversion commands** (`convert-markdown`): Transform files between formats (e.g., markdown to Word document)
- **Generation commands** (`develop-image-prompt`): Create prompts or content for external tools
- **Planning commands** (`create-plan`, `plan-improvements`, `plan-next`): Generate implementation plans from requirements or codebase analysis. Both `create-plan` and `plan-improvements` produce a unified IMPLEMENTATION_PLAN.md schema with standardized work item fields (Status, Tasks, Acceptance Criteria, Notes), concrete sizing (S/M/L using file count and LOC), machine-readable markers for append logic, and plan size limits (max 8 phases, max 6 items per phase). `create-plan` adds codebase reconnaissance and scope confirmation. `plan-improvements` adds sampling strategy, expanded analysis dimensions, priority rubric, and a two-stage `--recommendations-only` workflow.
- **Testing commands** (`test-project`): Comprehensive test, fix, and ship workflows
- **Orchestration commands** (`implement-plan`): Execute IMPLEMENTATION_PLAN.md via Agent tool subagents with selective git staging, state file resume, rollback/checkpoint capability, phase boundary quality gates, testing circuit breaker, and partial completion reporting. Creates PR by default (merge only with `--auto-merge`). Supports `--input`, `--pause-between-phases`, and `--progress` flags.
- **Cleanup commands** (`clean-repo`): Repository cleanup, organization, and documentation refresh
- **Sanitization commands** (`remove-ip`): De-identify documents by removing company info and intellectual property
- **Scaffolding commands** (`scaffold-plugin`, `new-command`, `new-skill`): Create new plugin/command/skill structures from templates
- **Utility commands** (`bump-version`, `validate-plugin`): Plugin/repository maintenance and configuration tasks. `validate-plugin` supports `--check-updates` to check for plugin updates from the marketplace

### Output File Naming
Commands that generate files use: `[type]-[source]-[timestamp].json` or `.md`

### Timestamp Format
All generated files use `YYYYMMDD-HHMMSS` format for timestamps.
Example: `assessment-PRD-20260114-143052.md`

### Output Locations
- Analysis reports → `reports/` directory
- Reference data (JSON) → `reference/` directory
- Generated documents → same directory as source
- Temporary files → `.tmp/` (auto-cleaned)

## BPMN Plugin

The bpmn-plugin provides two skills for BPMN workflow management:

### BPMN Generator (`/bpmn-generator`)

Generates BPMN 2.0 XML with two operating modes:

**Interactive Mode** - Natural language descriptions trigger structured Q&A:
1. Process Scope (name, triggers, outcomes)
2. Participants (pools, lanes, roles)
3. Activities (tasks, types, documentation)
4. Flow Control (gateways, conditions, loops)
5. Events & Exceptions (timers, errors, compensation)
6. Data & Integration (data objects, message flows)

**Document Parsing Mode** - Markdown file path triggers extraction of:
- Process metadata from headings/frontmatter
- Phases/stages from section structure
- Tasks from numbered lists with type inference
- Roles mapped to colored lanes
- Decision points from conditional language

### BPMN to Draw.io Converter (`/bpmn-to-drawio`)

Converts BPMN 2.0 XML files to Draw.io native format (.drawio):
- Proper swim lane structure (pools and lanes)
- BPMN-styled shapes for all element types
- Correct connector routing including cross-lane flows
- Color coding by lane function (Sales=blue, Finance=orange, etc.)
- Cross-lane edges use absolute coordinates for proper rendering

**Critical Rule:** Edges crossing lane boundaries must have `parent="1"` (root level) with absolute `mxPoint` coordinates.

### Key Output Features
- BPMN 2.0 compliant XML with all required namespaces
- Diagram Interchange (DI) data for visual rendering
- Phase comments (`<!-- Phase N: ... -->`) for PowerPoint compatibility
- Draw.io files compatible with Desktop and web applications

## Adding New Plugins

1. Create a new directory under `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add `commands/` directory with flat `.md` files (e.g., `commands/my-command.md`)
4. Add `skills/` directory with **nested subdirectories** containing `SKILL.md` files:
   ```
   skills/
     my-skill/
       SKILL.md    # Required: Must be exactly SKILL.md (uppercase)
   ```
5. **Create a `skills/help/SKILL.md`** with usage information for all commands/skills
6. Register the plugin in `.claude-plugin/marketplace.json`
7. Run `/validate-plugin [plugin-name]` to verify structure

## Bundled Python Tools

Plugins can include Python tools that commands/skills invoke at runtime. These tools must be **run from source** using `PYTHONPATH` - Claude Code's plugin schema does NOT support a `tools` field in plugin.json.

**Python Version:** All bundled Python tools require **Python 3.10+**.

### Directory Structure

```
plugins/
  [plugin-name]/
    tools/
      [tool-name]/
        pyproject.toml        # Tool metadata and dependencies
        src/
          [tool_module]/
            __init__.py
            __main__.py       # Entry point for `python -m [tool_module]`
            cli.py            # CLI implementation
```

### What NOT to Do

**DO NOT** add a `tools` field to plugin.json - it will cause installation to fail:

```json
// ❌ WRONG - causes "Unrecognized key: tools" error
{
  "name": "my-plugin",
  "tools": {
    "my-tool": { "path": "tools/my-tool" }
  }
}
```

### Running Tools from Source

In your command/skill markdown, use `PYTHONPATH` to run the tool directly from source:

```bash
# Set up tool path using CLAUDE_PLUGIN_ROOT
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/my-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/my-tool/src"

# Run the tool
PYTHONPATH="$TOOL_SRC" python -m my_tool_module <arguments>
```

### Dependency Checking Pattern

Check for and install missing Python dependencies at runtime:

```bash
# Check which packages are missing
python -c "import package_name" 2>/dev/null || echo "package_name: MISSING"

# Prompt user before installing
# "The following packages are missing: [list]. Install with pip install [packages]?"

# If approved:
pip install package1 package2 package3
```

### System Dependency Pattern

For tools requiring system dependencies (like Graphviz), check and provide installation instructions:

```bash
# Check for system dependency
command -v dot >/dev/null 2>&1 && echo "Graphviz: OK" || echo "Graphviz: MISSING"
```

If missing, display platform-specific installation instructions:
- Windows: `choco install graphviz`
- macOS: `brew install graphviz`
- Linux: `sudo apt install graphviz`

### Examples

See these plugins for reference implementations:
- `personal-plugin/tools/feedback-docx-generator/` - Feedback assessment .docx generator
- `personal-plugin/tools/research-orchestrator/` - Multi-provider LLM research tool
- `bpmn-plugin/tools/bpmn2drawio/` - BPMN to Draw.io converter

## Command Namespacing

Commands can be invoked with an explicit namespace for disambiguation:

| Format | Example | When to Use |
|--------|---------|-------------|
| Explicit namespace | `/personal-plugin:review-arch` | Required if another plugin has `/review-arch` |
| Short form | `/review-arch` | Works if only one plugin has this command |

**Collision Resolution:**
- If two plugins define commands with the same name, the short form becomes ambiguous
- Claude Code will prompt for clarification or suggest the namespaced form
- `/validate-plugin --all` detects naming collisions across plugins

## Plugin Dependencies

Plugins can declare dependencies on other plugins in their `plugin.json`:

```json
{
  "name": "advanced-plugin",
  "version": "1.0.0",
  "dependencies": {
    "personal-plugin": ">=2.0.0",
    "bpmn-plugin": "^1.5.0"
  }
}
```

**Version Syntax:**
- `>=2.0.0` - Version 2.0.0 or higher
- `^1.5.0` - Compatible with 1.5.0 (1.5.x or 1.x.y where x >= 5)
- `~1.5.0` - Approximately 1.5.0 (1.5.x only)
- `1.5.0` - Exactly version 1.5.0

Dependencies are validated by `/validate-plugin` but not automatically installed.

## Versioning Strategy

This repository uses a **two-tier versioning strategy**:

### 1. Marketplace Version (`marketplace_version` in marketplace.json)

The marketplace version tracks changes to the marketplace infrastructure itself:
- Schema changes to marketplace.json
- Changes to shared tooling (scripts, pre-commit hooks)
- Repository-wide documentation updates

**Not bumped for:** Individual plugin updates, new commands/skills.

**Format:** Semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking schema changes
- MINOR: New marketplace features
- PATCH: Bug fixes, documentation

### 2. Plugin Versions (in each plugin's plugin.json and marketplace.json)

Each plugin maintains its own independent version:
- Tracks changes to that plugin's commands, skills, and references
- Updated using `/bump-version [plugin-name] [major|minor|patch]`
- Reflected in both `plugins/[name]/.claude-plugin/plugin.json` and `marketplace.json`

### Version Update Workflow

1. **Plugin changes only**: Bump plugin version
2. **Marketplace infrastructure changes**: Bump `marketplace_version`
3. **Both**: Update both independently

## Help Skill Maintenance

**IMPORTANT:** Each plugin must have a `/help` skill at `skills/help/SKILL.md` (not `skills/help.md`).

Help skills use a static table that must be manually updated when commands or skills are added or removed. When creating a new plugin, create a `skills/help/SKILL.md` following the pattern used in existing plugins.
