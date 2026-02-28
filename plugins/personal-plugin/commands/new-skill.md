---
description: Generate a new skill file with proper nested directory structure and required frontmatter
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# New Skill Generator

Generate a new skill for this plugin with the correct directory structure and frontmatter. This command ensures skills are discoverable by Claude Code by using the required nested directory pattern.

**CRITICAL:** Skills have DIFFERENT requirements than commands:
- Skills use **nested directories**: `skills/[name]/SKILL.md`
- Skills **REQUIRE** a `name` field in frontmatter
- Commands use flat files and FORBID the `name` field

## Input Validation

**Optional Arguments:**
- `<skill-name>` - Name for the new skill (kebab-case)
- `--plugin <plugin-name>` - Target plugin (defaults to auto-detected or prompted)

**Plugin Target Resolution:**
1. If `--plugin` is specified, use that plugin
2. If the current working directory is inside a plugin, use that plugin
3. If only one plugin exists in `plugins/`, use it automatically
4. If multiple plugins exist, scan `plugins/*/` using the Glob tool and prompt the user:
   ```text
   Multiple plugins detected:
     [1] personal-plugin
     [2] bpmn-plugin

   Which plugin should this skill be added to? (1/2):
   ```

**Validation:**
If arguments are missing, the command will prompt interactively.

Skill name must be:
- kebab-case format (e.g., `my-new-skill`)
- Unique (not already exist in the target plugin's `skills/` directory)
- Descriptive but concise

## Instructions

### Phase 1: Gather Information

Interactively collect the following from the user:

#### 1.1 Skill Name

Ask:
```text
What is the skill name? (kebab-case, e.g., "auto-format")
```

**Validate:**
- Must be kebab-case: lowercase letters, numbers, hyphens only
- Must not start or end with a hyphen
- Must not contain consecutive hyphens
- Must not already exist in the target plugin's `skills/` directory

If invalid:
```text
Error: Skill name must be kebab-case (e.g., 'my-skill', 'auto-deploy')
Invalid: [what was provided]
Reason: [specific reason]

Please provide a valid skill name:
```

If skill already exists:
```text
Error: Skill '[name]' already exists at plugins/[plugin-name]/skills/[name]/SKILL.md

Please provide a different skill name:
```

#### 1.2 Description

Ask:
```text
Provide a brief description (shown in Skill tool and used for proactive suggestions):
```

**Validate:**
- Must be non-empty
- Should be concise but descriptive (under 150 characters ideal)
- Should describe WHEN the skill should be used (for proactive triggering)

**Good description examples:**
- "Create branch, commit, push, open PR, auto-review, fix issues, and merge"
- "Orchestrate parallel deep research across multiple LLM providers and synthesize results"

#### 1.3 Tool Restrictions (Optional)

Ask:
```text
Restrict which tools this skill can use? (leave empty for no restrictions)

Examples:
  Bash(git:*)           - Only git commands
  Bash(git:*), Bash(gh:*) - Git and GitHub CLI only
  Read, Glob, Grep      - Read-only tools

Enter tool restrictions or press Enter to skip:
```

### Phase 2: Create Skill Structure

#### 2.1 Create Directory

Create the nested directory structure required by Claude Code:

```text
plugins/[plugin-name]/skills/[skill-name]/
  SKILL.md    # Must be exactly this name (uppercase)
```

**Steps:**
1. Create directory: `plugins/[plugin-name]/skills/[skill-name]/`
2. Create file: `plugins/[plugin-name]/skills/[skill-name]/SKILL.md`

#### 2.2 Load and Customize Template

Read the skill template from: `plugins/[plugin-name]/references/templates/skill.md`

If the template file does not exist in the target plugin, fall back to `plugins/personal-plugin/references/templates/skill.md`. If neither exists, generate a minimal valid skill file with the required frontmatter fields.

Replace placeholders:

| Placeholder | Replace With |
|-------------|--------------|
| `{{SKILL_NAME}}` | The skill name (e.g., `auto-format`) |
| `{{TITLE}}` | Title case version (e.g., `Auto Format`) |
| `{{DESCRIPTION}}` | User-provided description |
| `{{ALLOWED_TOOLS}}` | Tool restrictions or remove the line if empty |
| `{{INTRO_PARAGRAPH}}` | Generated introduction |

**Generate frontmatter:**

If tool restrictions provided:
```yaml
---
name: [skill-name]
description: [user-provided description]
allowed-tools: [tool-restrictions]
---
```

If no tool restrictions:
```yaml
---
name: [skill-name]
description: [user-provided description]
---
```

**CRITICAL:** The `name` field is REQUIRED. Without it, the skill will NOT be discovered by Claude Code.

#### 2.3 Write Skill File

Save to: `plugins/[plugin-name]/skills/[skill-name]/SKILL.md`

### Phase 3: Post-Generation Tasks

#### 3.1 Remind About Documentation Updates

Display:
```text
----------------------------------------------
Skill Generated Successfully!
----------------------------------------------

Plugin: [plugin-name]
Created:
  plugins/[plugin-name]/skills/[skill-name]/
    SKILL.md    [CREATED]

Structure verified:
  [PASS] Nested directory structure (skills/[name]/SKILL.md)
  [PASS] Required 'name' field in frontmatter
  [PASS] Description field present

**Required Next Steps:**

1. Edit the generated file to complete:
   - [ ] Customize phases/instructions
   - [ ] Add specific examples
   - [ ] Define error handling

2. Update help skill:
   - [ ] Add entry to plugins/[plugin-name]/skills/help/SKILL.md

3. Validate:
   - [ ] Run: /validate-plugin [plugin-name]

**Important Reminders:**
- Skills use NESTED directories: skills/[name]/SKILL.md
- Skills REQUIRE the 'name' field (unlike commands)
- The 'name' must match the directory name exactly
```

## Output

**Directory Created:** `plugins/[plugin-name]/skills/[skill-name]/`
**File Created:** `plugins/[plugin-name]/skills/[skill-name]/SKILL.md`

The generated file will contain:
- Proper frontmatter with required `name` field
- Template structure for skill content
- Placeholder sections to customize

## Example Usage

```yaml
User: /new-skill

Claude:
What is the skill name? (kebab-case, e.g., "auto-format")

User: quick-test

Claude:
Provide a brief description (shown in Skill tool and used for proactive suggestions):

User: Run quick validation tests on the current file or directory

Claude:
Restrict which tools this skill can use? (leave empty for no restrictions)

Examples:
  Bash(git:*)           - Only git commands
  Bash(git:*), Bash(gh:*) - Git and GitHub CLI only
  Read, Glob, Grep      - Read-only tools

Enter tool restrictions or press Enter to skip:

User: Bash(npm:*), Bash(pytest:*)

Claude:
----------------------------------------------
Skill Generated Successfully!
----------------------------------------------

Plugin: personal-plugin
Created:
  plugins/personal-plugin/skills/quick-test/
    SKILL.md    [CREATED]

Structure verified:
  [PASS] Nested directory structure (skills/quick-test/SKILL.md)
  [PASS] Required 'name' field in frontmatter
  [PASS] Description field present

**Required Next Steps:**

1. Edit the generated file to complete:
   - [ ] Customize phases/instructions
   - [ ] Add specific examples
   - [ ] Define error handling

2. Update help skill:
   - [ ] Add entry to plugins/personal-plugin/skills/help/SKILL.md

3. Validate:
   - [ ] Run: /validate-plugin personal-plugin
```

```yaml
User: /new-skill deploy-preview

Claude:
Provide a brief description (shown in Skill tool and used for proactive suggestions):

User: Deploy current changes to preview environment for testing

Claude:
Restrict which tools this skill can use? (leave empty for no restrictions)
...
```

## Error Handling

- **Skill already exists:** Report existing path and suggest alternative name
- **Invalid name format:** Explain kebab-case requirement with examples
- **Template not found:** Create minimal valid skill file with required fields
- **Write permission denied:** Report error and suggest checking permissions
- **Directory creation failed:** Report error with path details

## Common Mistakes This Command Prevents

| Mistake | How This Command Prevents It |
|---------|------------------------------|
| Flat file structure (`skills/name.md`) | Creates nested directory automatically |
| Missing `name` field | Always includes `name` in frontmatter |
| Wrong filename (`skill.md` lowercase) | Creates `SKILL.md` (uppercase) |
| `name` doesn't match directory | Uses same value for both |

## Key Differences: Skills vs Commands

| Aspect | Commands | Skills |
|--------|----------|--------|
| Structure | `commands/name.md` (flat) | `skills/name/SKILL.md` (nested) |
| `name` field | **FORBIDDEN** | **REQUIRED** |
| Filename | Any `.md` name | Must be `SKILL.md` |
| Discovery | By filename | By directory name + `name` field |

## Related Commands

- `/new-command` — Generate a new command file from a template (flat file structure)
- `/scaffold-plugin` — Create an entire new plugin with proper structure
- `/validate-plugin` — Validate the plugin after adding a new skill
- `/bump-version` — Update plugin version after adding new skills
