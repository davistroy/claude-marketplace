---
description: Create a new plugin with proper directory structure, metadata, and starter files
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Scaffold Plugin

Create a new Claude Code plugin with the proper directory structure, configuration files, and starter templates. This command ensures new plugins follow the established conventions.

## Input Validation

**Optional Arguments:**
- `<plugin-name>` - Name for the new plugin (kebab-case ending in `-plugin`)
- `--dry-run` - Show the directory structure and file list that would be created without creating any files

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
    commands/                (empty directory)
    skills/
      help/
        SKILL.md

Would update:
  .claude-plugin/marketplace.json

No files were created or modified.
```

If not dry-run, proceed to Phase 3.

### Phase 3: Create Directory Structure

Create the following directory structure:

```text
plugins/[plugin-name]/
  .claude-plugin/
    plugin.json           # Plugin metadata
  commands/               # User-initiated commands (empty initially)
  skills/
    help/                 # CRITICAL: Skills use NESTED directories
      SKILL.md            # MUST be exactly SKILL.md (uppercase)
  references/             # Reference documentation (optional)
```

**CRITICAL:** Skills require a nested directory structure with `SKILL.md` files (not flat `.md` files). This is different from commands which use flat files.

| Component | Correct Path | Wrong Path |
|-----------|-------------|------------|
| Help skill | `skills/help/SKILL.md` | `skills/help.md` |
| Any skill | `skills/[name]/SKILL.md` | `skills/[name].md` |
| Commands | `commands/[name].md` | `commands/[name]/command.md` |

**Steps:**

1. Create main plugin directory: `plugins/[plugin-name]/`
2. Create `.claude-plugin/` subdirectory
3. Create `commands/` subdirectory
4. Create `skills/help/` subdirectory (nested — required for skill discovery)
5. Optionally create `references/` subdirectory

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

#### 4.2 Create Starter help Skill

Generate `plugins/[plugin-name]/skills/help/SKILL.md`:

**CRITICAL:** Skills REQUIRE a `name` field in frontmatter. Without it, the skill will NOT be discovered.

<!-- BEGIN EMBEDDED TEMPLATE: help skill -->
```markdown
---
name: help
description: Show available commands and skills in this plugin with usage information
---

# Help Skill

Display help information for the [plugin-name] commands and skills.

**IMPORTANT:** This skill must be updated whenever commands or skills are added, changed, or removed from this plugin.

## Usage

\`\`\`
/help                          # Show all commands and skills
/help <command-name>           # Show detailed help for a specific command
\`\`\`

## Mode 1: List All (no arguments)

When invoked without arguments, display this table:

\`\`\`
[plugin-name] Commands and Skills
=================================

COMMANDS
--------
| Command | Description |
|---------|-------------|
| (no commands yet) | Add commands using /new-command |

SKILLS
------
| Skill | Description |
|-------|-------------|
| /help | Show available commands and skills in this plugin with usage information |

---
Use '/help <name>' for detailed help on a specific command or skill.
\`\`\`

## Mode 2: Detailed Help (with argument)

When invoked with a command or skill name, read the corresponding file and display:

1. **Description** - From frontmatter
2. **Arguments** - From "Input Validation" section if present
3. **Output** - What the command produces
4. **Example** - Usage example

### Skill Reference

---

#### /help
**Description:** Show available commands and skills in this plugin with usage information
**Arguments:** None required
**Output:** In-conversation output
**Example:**
\`\`\`
/help                          # Show all commands and skills
/help <command-name>           # Show detailed help for a specific command
\`\`\`

---

## Error Handling

If the requested command is not found:
\`\`\`
Command '[name]' not found in [plugin-name].

Available commands:
  (none yet)

Available skills:
  /help
\`\`\`
```
<!-- END EMBEDDED TEMPLATE: help skill -->

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
    commands/               [CREATED] (empty)
    skills/
      help/
        SKILL.md            [CREATED]

Updated:
  .claude-plugin/marketplace.json  [UPDATED]

**Next Steps:**

1. Add your first command:
   /new-command

2. Add skills (proactive suggestions):
   /new-skill

3. Or manually create in:
   - Commands: plugins/[plugin-name]/commands/my-command.md
   - Skills: plugins/[plugin-name]/skills/my-skill/SKILL.md
     (skills MUST use nested directories with SKILL.md)

4. After adding commands/skills, update the plugin's `skills/help/SKILL.md` with new entries

5. Validate the plugin:
   /validate-plugin [plugin-name]

**Useful Commands:**
- /validate-plugin [plugin-name]  - Validate plugin structure
- /new-command                    - Create new commands
- /new-skill                      - Create new skills
- /help                           - View available commands
```

## Output

**Files Created:**
- `plugins/[plugin-name]/.claude-plugin/plugin.json`
- `plugins/[plugin-name]/skills/help/SKILL.md`

**Files Updated:**
- `.claude-plugin/marketplace.json`

**Directories Created:**
- `plugins/[plugin-name]/`
- `plugins/[plugin-name]/.claude-plugin/`
- `plugins/[plugin-name]/commands/`
- `plugins/[plugin-name]/skills/`
- `plugins/[plugin-name]/skills/help/`

## Example Usage

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
    commands/               [CREATED] (empty)
    skills/
      help/
        SKILL.md            [CREATED]

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
    commands/                (empty directory)
    skills/
      help/
        SKILL.md

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

## Related Commands

- `/new-command` -- Add a new command to the scaffolded plugin
- `/new-skill` -- Add a new skill with proper nested directory structure
- `/validate-plugin` -- Verify plugin structure after scaffolding
- `/bump-version` -- Update plugin version numbers
