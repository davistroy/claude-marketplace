---
description: Create a new plugin with proper directory structure, metadata, and starter files
argument-hint: "[<plugin-name>] [--dry-run] [--with-commands]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir:*)
---

# Scaffold Plugin

Create a new Claude Code plugin with the proper directory structure, configuration files, and starter templates. This command ensures new plugins follow the established conventions.

## Input Validation

**Optional Arguments:**
- `<plugin-name>` - Name for the new plugin (kebab-case ending in `-plugin`)
- `--dry-run` - Show the directory structure and file list that would be created without creating any files
- `--with-commands` - Also scaffold a `commands/` directory (legacy format — see ADR-0006). Default scaffold is skills-only.

**Validation:**
If arguments are missing, the command will prompt interactively.

Plugin name must be:
- kebab-case format ending in `-plugin` (e.g., `my-new-plugin`)
- Unique (not already exist in `plugins/` directory)
- Descriptive but concise
- Contain only lowercase letters, numbers, and hyphens (no special characters, no spaces)

## Instructions

### Phase 1: Gather Information

Interactively collect the following from the user:

#### 1.1 Plugin Name

Ask:
```text
What is the plugin name? (kebab-case ending in '-plugin', e.g., "data-tools-plugin")
```

**Validate:**
- Must be kebab-case: lowercase letters, numbers, hyphens only
- Must end with `-plugin`
- Must not contain special characters (underscores, dots, spaces)
- Must not already exist in `plugins/` directory (scan with Glob)

If invalid:
```text
Error: Plugin name must be kebab-case ending in '-plugin'
Invalid: [what was provided]
Reason: [specific reason]

Please provide a valid plugin name:
```

#### 1.2 Description

Ask:
```text
Provide a brief description for the plugin:
```

**Validate:**
- Must be non-empty
- Should describe the plugin's purpose

#### 1.3 Category

Ask:
```text
Select a category for the plugin:

[1] productivity  - Personal productivity and workflow tools
[2] workflow      - Process automation and management
[3] analysis      - Code and data analysis tools
[4] integration   - External service integrations
[5] utility       - General utility commands
[6] custom        - Enter a custom category

Enter number (1-6) or category name:
```

#### 1.4 Tags

Ask:
```text
Enter tags for the plugin (comma-separated, e.g., "automation,cli,tools"):
```

Parse into array format for JSON.

### Phase 2: Dry-Run Check

If `--dry-run` was specified, display the planned directory structure and file list, then stop without creating anything:

```text
----------------------------------------------
Dry Run: Plugin Structure Preview
----------------------------------------------

Would create:
  plugins/[plugin-name]/
    .claude-plugin/
      plugin.json
    skills/                  (empty directory — add skills with /new-skill)
    references/              (empty directory — optional)

Would update:
  .claude-plugin/marketplace.json

No files were created or modified.
```

If `--with-commands` was also specified, add a `commands/ (empty directory — legacy format, see ADR-0006)` line to the preview above.

If not dry-run, proceed to Phase 3.

### Phase 3: Create Directory Structure

Create the following directory structure. Skills-first is the default (ADR-0006); `commands/` is legacy and created only when `--with-commands` is explicitly passed:

```text
plugins/[plugin-name]/
  .claude-plugin/
    plugin.json           # Plugin metadata
  skills/                 # Proactive skills (nested dirs — add with /new-skill)
  references/             # Reference documentation (optional)
```

If `--with-commands` was specified, also create `commands/` (legacy format, see ADR-0006):

```text
  commands/               # Legacy format (see ADR-0006) — user-initiated commands (flat .md files)
```

**CRITICAL:** Skills require a nested directory structure with `SKILL.md` files (not flat `.md` files). Use `/new-skill` to scaffold individual skills with modern frontmatter.

| Component | Correct Path | Wrong Path |
|-----------|-------------|------------|
| Any skill | `skills/[name]/SKILL.md` | `skills/[name].md` |
| Commands (legacy, `--with-commands` only) | `commands/[name].md` | `commands/[name]/command.md` |

**Note:** No help skill is generated. Native `/help` and `/skills` commands fully cover plugin-local help. Use `/new-skill` to add content to your plugin.

**Steps:**

1. Create main plugin directory: `plugins/[plugin-name]/`
2. Create `.claude-plugin/` subdirectory
3. Create `skills/` subdirectory (empty — skills added per-skill via `/new-skill`)
4. Optionally create `references/` subdirectory
5. If `--with-commands` was specified, also create `commands/` subdirectory (empty — legacy format, see ADR-0006)

### Phase 4: Generate Configuration Files

#### 4.1 Create plugin.json

Generate `plugins/[plugin-name]/.claude-plugin/plugin.json`:

```json
{
  "name": "[plugin-name]",
  "description": "[user-provided description]",
  "version": "1.0.0",
  "author": {
    "name": "[from marketplace.json owner or prompt]",
    "email": "[from marketplace.json owner or prompt]"
  },
  "homepage": "https://github.com/davistroy/claude-marketplace",
  "repository": "https://github.com/davistroy/claude-marketplace",
  "license": "MIT",
  "keywords": ["tag1", "tag2", "tag3"]
}
```

**Note:** The `keywords` field must be a valid JSON array of strings. Each tag from the user's comma-separated input becomes a separate string element.

#### 4.2 Skills Are the Primary Authoring Path

No starter help skill is generated. Native `/help` and `/skills` commands fully cover plugin-local help — a custom help skill is an unnecessary maintenance burden.

Skills are the default, primary way to add functionality to a scaffolded plugin (ADR-0006: skills-first authoring policy). The legacy `commands/` format is generated only when `--with-commands` is explicitly requested (see Phase 3) and should be treated as a frozen, maintained-not-extended surface.

To add your first skill after scaffolding, run `/new-skill`. It will generate a skill with modern frontmatter fields including `context`, `agent`, `model`, `paths`, `isolation`, `when_to_use`, and `allowed-tools`. See `plugins/personal-plugin/references/common-patterns.md` (Advanced Features section) for field documentation and worked examples.

**Skill frontmatter quick reference (primary authoring format):**
```yaml
---
name: my-skill             # REQUIRED — must match directory name
description: What it does  # REQUIRED
effort: medium             # low/medium/high/max
allowed-tools: Read, Glob, Grep, Bash
# context: fork            # Dispatch to isolated subagent context
# isolation: worktree      # Give subagent its own git worktree
# paths: ["**/*.ts"]       # Auto-trigger on file changes (add loop guard in body!)
# agent: explorer          # Agent type for context:fork dispatch
# when_to_use: "..."       # Routing hint shown in /skills list
---
```

**CRITICAL:** Skills REQUIRE a `name` field in frontmatter. Without it, the skill will NOT be discovered.

### Phase 5: Update Marketplace Registry

#### 5.1 Read Current marketplace.json

Read `.claude-plugin/marketplace.json`

#### 5.2 Add New Plugin Entry

Add to the `plugins` array:

```json
{
  "name": "[plugin-name]",
  "source": "./plugins/[plugin-name]",
  "description": "[user-provided description]",
  "version": "1.0.0",
  "category": "[selected category]",
  "tags": ["tag1", "tag2", "tag3"]
}
```

#### 5.3 Write Updated marketplace.json

Save the updated JSON with proper formatting.

### Phase 6: Report Results

Display:
```text
----------------------------------------------
Plugin Scaffolded Successfully!
----------------------------------------------

Created structure:
  plugins/[plugin-name]/
    .claude-plugin/
      plugin.json           [CREATED]
    skills/                 [CREATED] (empty — add skills with /new-skill)
    references/             [CREATED] (optional, empty)

Updated:
  .claude-plugin/marketplace.json  [UPDATED]

**Next Steps:**

1. Add your first skill (proactive triggers — nested dirs required):
   /new-skill
   (use `/new-skill <name> --pattern <type>` to scaffold from a pattern template — see `references/templates/`)

2. Or manually create in:
   - Skills: plugins/[plugin-name]/skills/my-skill/SKILL.md
     (skills MUST use nested directories with SKILL.md; name field required in frontmatter)

3. Review modern frontmatter options in common-patterns.md (Advanced Features section):
   plugins/personal-plugin/references/common-patterns.md

4. Validate the plugin:
   /validate-plugin [plugin-name]

**Useful Commands:**
- /validate-plugin [plugin-name]  - Validate plugin structure
- /new-skill                      - Create new skills with modern frontmatter
- /help                           - View available commands (native, no custom help skill needed)
```

If `--with-commands` was specified, add a `commands/ [CREATED] (empty — legacy format, see ADR-0006)` line to "Created structure" after `skills/`, and add a Next Steps item: "Manually create legacy command files: plugins/[plugin-name]/commands/my-command.md (legacy format, see ADR-0006)."

## Output

**Files Created:**
- `plugins/[plugin-name]/.claude-plugin/plugin.json`

**Files Updated:**
- `.claude-plugin/marketplace.json`

**Directories Created:**
- `plugins/[plugin-name]/`
- `plugins/[plugin-name]/.claude-plugin/`
- `plugins/[plugin-name]/skills/`
- `plugins/[plugin-name]/references/`
- `plugins/[plugin-name]/commands/` (only when `--with-commands` is specified — legacy format, see ADR-0006)

## Examples

```yaml
User: /scaffold-plugin

Claude:
What is the plugin name? (kebab-case ending in '-plugin', e.g., "data-tools-plugin")

User: api-client-plugin

Claude:
Provide a brief description for the plugin:

User: Tools for interacting with REST APIs and generating client code

Claude:
Select a category for the plugin:

[1] productivity  - Personal productivity and workflow tools
[2] workflow      - Process automation and management
[3] analysis      - Code and data analysis tools
[4] integration   - External service integrations
[5] utility       - General utility commands
[6] custom        - Enter a custom category

Enter number (1-6) or category name:

User: 4

Claude:
Enter tags for the plugin (comma-separated, e.g., "automation,cli,tools"):

User: api,rest,http,client,integration

Claude:
----------------------------------------------
Plugin Scaffolded Successfully!
----------------------------------------------

Created structure:
  plugins/api-client-plugin/
    .claude-plugin/
      plugin.json           [CREATED]
    skills/                 [CREATED] (empty — add skills with /new-skill)
    references/             [CREATED] (optional, empty)

Updated:
  .claude-plugin/marketplace.json  [UPDATED]

...
```

```yaml
User: /scaffold-plugin testing-tools-plugin --dry-run

Claude:
----------------------------------------------
Dry Run: Plugin Structure Preview
----------------------------------------------

Would create:
  plugins/testing-tools-plugin/
    .claude-plugin/
      plugin.json
    skills/                  (empty directory — add skills with /new-skill)
    references/              (empty directory — optional)

Would update:
  .claude-plugin/marketplace.json

No files were created or modified.
```

```yaml
User: /scaffold-plugin legacy-tools-plugin --with-commands --dry-run

Claude:
----------------------------------------------
Dry Run: Plugin Structure Preview
----------------------------------------------

Would create:
  plugins/legacy-tools-plugin/
    .claude-plugin/
      plugin.json
    skills/                  (empty directory — add skills with /new-skill)
    references/              (empty directory — optional)
    commands/                (empty directory — legacy format, see ADR-0006)

Would update:
  .claude-plugin/marketplace.json

No files were created or modified.
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Plugin already exists | Directory `plugins/[name]/` already present | Report conflict, suggest checking existing plugin or choosing different name |
| Invalid name format | Name contains special characters, spaces, or doesn't end in `-plugin` | Explain naming requirements with valid examples |
| marketplace.json parse error | Malformed JSON in marketplace config | Report error, show JSON parse error details, suggest manual fix |
| Write permission denied | File system permissions prevent creation | Report error and suggest checking directory permissions |
| Missing marketplace.json | `.claude-plugin/marketplace.json` does not exist | Report error, provide instructions to create it manually |
| Disk full | Cannot write files | Report the OS error and suggest freeing disk space |

## Performance

Typically completes in under 15 seconds once all inputs are provided.

## Related Commands

- `/new-skill` -- Add a new skill with proper nested directory structure
- `/validate-plugin` -- Verify plugin structure after scaffolding
- `/bump-version` -- Update plugin version numbers
