---
description: Generate a new skill file with proper nested directory structure and required frontmatter
argument-hint: "[<skill-name>] [--plugin <plugin-name>]"
allowed-tools: Read, Write, Edit, Glob, Grep
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

The generated frontmatter includes all modern fields as commented options so the author can uncomment what they need. Required fields are always active; optional fields are commented:

If tool restrictions provided:
```yaml
---
name: [skill-name]
description: [user-provided description]
# argument-hint: "<required-arg> [--optional-flag]"
# effort: medium
allowed-tools: [tool-restrictions]
# disable-model-invocation: false
#
# --- Modern Dispatch & Isolation ---
# context: fork
# agent: Explore
# model: claude-opus-4
# isolation: worktree
#
# --- Auto-Activation ---
# paths:
#   - "**/*.ext"
#
# --- Lifecycle Hooks ---
# hooks:
#   pre:  "echo 'before'"
#   post: "echo 'after'"
#
# shell: bash
---
```

If no tool restrictions:
```yaml
---
name: [skill-name]
description: [user-provided description]
# argument-hint: "<required-arg> [--optional-flag]"
# effort: medium
# allowed-tools: Read, Glob, Grep, Bash
# disable-model-invocation: false
#
# --- Modern Dispatch & Isolation ---
# context: fork
# agent: Explore
# model: claude-opus-4
# isolation: worktree
#
# --- Auto-Activation ---
# paths:
#   - "**/*.ext"
#
# --- Lifecycle Hooks ---
# hooks:
#   pre:  "echo 'before'"
#   post: "echo 'after'"
#
# shell: bash
---
```

**CRITICAL:** The `name` field is REQUIRED. Without it, the skill will NOT be discovered by Claude Code.

**Tip:** After generating, see the "Frontmatter Field Reference" section above and the worked examples for guidance on which modern features apply to your use case.

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
   - [ ] Uncomment modern frontmatter fields that apply (context, isolation, paths, etc.)
   - [ ] Add loop guard if using `paths:` auto-activation

2. Validate:
   - [ ] Run: /validate-plugin [plugin-name]

**Important Reminders:**
- Skills use NESTED directories: skills/[name]/SKILL.md
- Skills REQUIRE the 'name' field (unlike commands)
- The 'name' must match the directory name exactly
- See the Frontmatter Field Reference table and worked examples in this command for modern patterns
```

## Frontmatter Field Reference

All fields supported by Claude Code as of late 2025. Fields marked **Required** must be present for skill discovery. Fields marked *Optional* are commented-out in the generated template — uncomment to use.

| Field | Required? | Values / Syntax | Purpose |
|-------|-----------|-----------------|---------|
| `name` | **Required** | `kebab-case` string | Identifies the skill; must match directory name |
| `description` | **Required** | Free text ≤ 150 chars | Shown in `/skills` list; used for proactive triggering |
| `argument-hint` | Optional | `"<req> [opt]"` | Displayed in completions UI |
| `effort` | Optional | `low` / `medium` / `high` / `max` | Controls token budget allocation |
| `allowed-tools` | Optional | `Read, Glob, Bash(git:*)` | Restricts tool access for this skill |
| `disable-model-invocation` | Optional | `true` / `false` | `true` = run tools only, no LLM call |
| `context` | Optional | `fork` | Spawns an isolated subagent context; no shared conversation history. Use when analysis shouldn't pollute parent context |
| `agent` | Optional | `Explore`, `Think`, `Code`, role string | Selects subagent persona/capability profile. `Explore` = broad read-only analysis; `Think` = deep reasoning; `Code` = implementation |
| `model` | Optional | `claude-opus-4`, `claude-sonnet-4-5`, etc. | Overrides the model for this skill's execution |
| `isolation` | Optional | `worktree` | Creates a git worktree for the run; auto-cleans up when no file changes occur. Use for skills that write to disk to prevent conflicts |
| `paths` | Optional | List of glob patterns | Auto-activates skill when user opens a matching file. **Requires loop guard in skill body** — see gotcha below |
| `hooks` | Optional | `pre:` / `post:` shell commands | Lifecycle hooks run before/after the skill |
| `shell` | Optional | `bash` / `zsh` / `sh` | Overrides the shell used for Bash tool calls |

### Dynamic Context Injection

Three mechanisms inject data before Claude reads the skill prompt:

| Syntax | What it does | Example |
|--------|-------------|---------|
| `$ARGUMENTS` | Raw args the user passed | `$ARGUMENTS` resolves to `"my-branch --draft"` |
| `$CLAUDE_CONTEXT` | Active file/selection in the editor | Populated when user has a file open |
| `` !`cmd` `` | Runs `cmd` and splices stdout into prompt | `` !`git status -s` `` → current working tree status |

**Gotcha — `paths:` loop guard:** If your skill writes to a file that matches its own `paths:` pattern, it will re-trigger itself. Always add an entry-point guard:
```
Before running: check LAB_NOTEBOOK.md for an entry from this skill within the last 5 minutes.
If found → exit immediately (self-triggered re-entry detected).
```

**Gotcha — `context: fork`:** The forked subagent has no access to parent conversation history. Pass all needed context explicitly in the prompt body or via `` !`cmd` `` injection.

See `references/patterns/advanced-features.md` for full syntax and gotchas for each feature.

---

## Worked Examples

### Example A — Basic Skill (no modern features)

Suitable for: simple in-context analysis, no disk writes, no parallelism needed.

```yaml
---
name: check-deps
description: Audit package.json dependencies for outdated or insecure packages
argument-hint: "[--fix]"
effort: medium
allowed-tools: Read, Bash(npm:*)
---

# Dependency Checker

Audits the project's npm dependencies and reports outdated or vulnerable packages.

## Input

**Arguments:** `$ARGUMENTS` — pass `--fix` to auto-upgrade safe patches.

## Instructions

### Phase 1: Collect dependency info

Run `npm outdated` and `npm audit --json`. Parse JSON output.

### Phase 2: Report

Summarize: outdated count, critical vulns, high vulns. List top-5 most outdated.
If `--fix` in $ARGUMENTS: run `npm audit fix` (safe patches only).

## Output

In-conversation summary table. If --fix: updated package-lock.json.
```

---

### Example B — Fork-to-Explore Skill with Dynamic Injection

Suitable for: read-heavy analysis that shouldn't pollute parent context; pre-loading expensive git/file data before Claude reads the prompt.

```yaml
---
name: code-health
description: Analyze codebase health — complexity, test coverage gaps, stale TODOs
effort: high
allowed-tools: Read, Glob, Grep, Bash
context: fork
agent: Explore
---

# Code Health Analyzer

!`git log --oneline -20`
!`git shortlog -sn --no-merges | head -10`
!`find . -name "*.ts" -o -name "*.py" | wc -l`
!`grep -r "TODO\|FIXME\|HACK" --include="*.ts" --include="*.py" -l | head -20`

The above commands ran before you read this prompt. Use their output in your analysis.

## Instructions

This skill runs in an isolated context (`context: fork`, `agent: Explore`).
You have no access to prior conversation — analyze the project from scratch.

### Phase 1: Complexity hotspots

Read the 5 largest source files (by line count from Glob). Flag functions > 50 lines.

### Phase 2: Test coverage gaps

Find source files with no matching test file. List by directory.

### Phase 3: TODO/FIXME inventory

Use the grep output injected above. Categorize by severity (HACK > FIXME > TODO).

## Output

Structured report written to `reports/code-health-YYYYMMDD.md`. Summary in conversation.
```

**Key patterns demonstrated:**
- `` !`cmd` `` blocks at top of body — run before Claude reads the prompt
- `context: fork` isolates the analysis from conversation history
- `agent: Explore` selects the broad read-only analysis persona

---

### Example C — Paths-Activated Skill with Loop Guard

Suitable for: skills that should auto-run when specific files change (e.g., dependency manifests, config files, baseline docs).

```yaml
---
name: validate-config
description: Validate app config schema whenever config files change
allowed-tools: Read, Bash
paths:
  - "config/**/*.json"
  - "config/**/*.yaml"
  - ".env.example"
---

# Config Validator

Auto-activates when a config file changes. Validates schema, required keys, and type correctness.

## Instructions

### Entry guard (REQUIRED for paths-activated skills)

Check: has this skill run in the last 5 minutes (look for a recent entry in LAB_NOTEBOOK.md
or a sentinel file `.tmp/validate-config.last-run`)? If yes → exit immediately.
This prevents infinite re-entry if the skill itself writes to a config path.

Write sentinel: `echo $(date +%s) > .tmp/validate-config.last-run`

### Phase 1: Detect changed files

Identify which config file triggered activation from `$CLAUDE_CONTEXT`.
If no context: scan `config/` for recently modified files (`find config/ -newer .tmp/validate-config.last-run`).

### Phase 2: Validate schema

Read the changed file. Compare against the schema definition in `config/schema.json`.
Report: PASS / FAIL with specific field-level errors.

### Phase 3: Check required keys

Cross-reference against required key list in `config/required-keys.txt`.
Flag any missing required keys as CRITICAL.

## Output

In-conversation validation report. Does NOT modify the config file (read-only).
```

**Key patterns demonstrated:**
- `paths:` frontmatter for auto-activation
- Loop guard at skill entry (mandatory for any paths-activated skill)
- `$CLAUDE_CONTEXT` to identify which file triggered the activation

---

## Output

**Directory Created:** `plugins/[plugin-name]/skills/[skill-name]/`
**File Created:** `plugins/[plugin-name]/skills/[skill-name]/SKILL.md`

The generated file will contain:
- Proper frontmatter with required `name` field and all modern fields as commented options
- Frontmatter field reference table
- Template structure for skill content with dynamic injection examples
- Placeholder sections to customize

## Example Usage

```
User: /new-skill

Claude: What is the skill name? (kebab-case, e.g., "auto-format")
User:   quick-test

Claude: Provide a brief description:
User:   Run quick validation tests on the current file or directory

Claude: Restrict which tools? (Enter to skip)
User:   Bash(npm:*), Bash(pytest:*)

→ Creates plugins/personal-plugin/skills/quick-test/SKILL.md with full modern frontmatter template
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
