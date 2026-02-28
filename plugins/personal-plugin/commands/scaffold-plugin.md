---
description: Create a new plugin with proper directory structure, metadata, and starter files
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Scaffold Plugin

Create a new Claude Code plugin with the proper directory structure, configuration files, and starter templates. This command ensures new plugins follow the established conventions.

## Input Validation

**Optional Arguments:**
- `<plugin-name>` - Name for the new plugin (kebab-case ending in `-plugin`)

**Validation:**
If arguments are missing, the command will prompt interactively.

Plugin name must be:
- kebab-case format ending in `-plugin` (e.g., `my-new-plugin`)
- Unique (not already exist in `plugins/` directory)
- Descriptive but concise

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
- Must not already exist in `plugins/` directory

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

### Phase 2: Create Directory Structure

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

**Steps:**

1. Create main plugin directory: `plugins/[plugin-name]/`
2. Create `.claude-plugin/` subdirectory
3. Create `commands/` subdirectory
4. Create `skills/` subdirectory
5. Optionally create `references/` subdirectory

### Phase 3: Generate Configuration Files

#### 3.1 Create plugin.json

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
  "keywords": ["[parsed tags array]"]
}
```

#### 3.2 Create Starter help Skill

Generate `plugins/[plugin-name]/skills/help/SKILL.md`:

**CRITICAL:** Skills REQUIRE a `name` field in frontmatter. Without it, the skill will NOT be discovered.

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

### Phase 4: Update Marketplace Registry

#### 4.1 Read Current marketplace.json

Read `.claude-plugin/marketplace.json`

#### 4.2 Add New Plugin Entry

Add to the `plugins` array:

```json
{
  "name": "[plugin-name]",
  "source": "./plugins/[plugin-name]",
  "description": "[user-provided description]",
  "version": "1.0.0",
  "category": "[selected category]",
  "tags": ["[parsed tags array]"]
}
```

#### 4.3 Write Updated marketplace.json

Save the updated JSON with proper formatting.

### Phase 5: Report Results

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
      help.md               [CREATED]

Updated:
  .claude-plugin/marketplace.json  [UPDATED]

**Next Steps:**

1. Add your first command:
   /new-command

2. Add skills (proactive suggestions):
   /new-skill

3. Or manually create in:
   - Commands: plugins/[plugin-name]/commands/
   - Skills: plugins/[plugin-name]/skills/[name]/SKILL.md

4. After adding commands/skills, update documentation:
   python scripts/generate-help.py plugins/[plugin-name]

5. Update README.md with plugin information

6. Add entry to CHANGELOG.md:
   ### Added
   - New [plugin-name] plugin for [description]

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
      help.md               [CREATED]

Updated:
  .claude-plugin/marketplace.json  [UPDATED]

**Next Steps:**

1. Add your first command:
   /new-command

2. Or manually create commands in:
   plugins/api-client-plugin/commands/

3. After adding commands, update documentation:
   python scripts/generate-help.py plugins/api-client-plugin

...
```

```yaml
User: /scaffold-plugin testing-tools-plugin

Claude:
Provide a brief description for the plugin:

User: Automated testing utilities and test generation tools

...
```

## Error Handling

- **Plugin already exists:** Report conflict and suggest checking existing plugin
- **Invalid name format:** Explain naming requirements with examples
- **marketplace.json parse error:** Report error and suggest manual fix
- **Write permission denied:** Report error and suggest checking permissions
- **Missing marketplace.json:** Report error and suggest creating manually

## Related Commands

- `/new-command` — Add a new command to the scaffolded plugin
- `/new-skill` — Add a new skill with proper nested directory structure
- `/validate-plugin` — Verify plugin structure after scaffolding
- `/bump-version` — Update plugin version numbers
