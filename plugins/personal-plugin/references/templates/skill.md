---
name: {{SKILL_NAME}}
description: {{DESCRIPTION}}
# argument-hint: "<required-arg> [--optional-flag]"
# effort: medium                    # low | medium | high | max
# allowed-tools: {{ALLOWED_TOOLS}}  # e.g., Read, Glob, Grep, Bash, Task
# disable-model-invocation: false   # true = no LLM call; pure-tool skill
#
# --- Modern Dispatch & Isolation ---
# context: fork          # spawn isolated subagent context (no shared conversation history)
# agent: Explore         # subagent type: Explore | Think | Code | (role-specific strings)
# model: claude-opus-4   # override model for this skill; omit = inherits caller model
# isolation: worktree    # create git worktree for run; auto-cleanup when no changes
#
# --- Auto-Activation ---
# paths:                 # activate skill when user opens matching files
#   - "**/*.spec.ts"
#   - "package.json"
#
# --- Lifecycle Hooks ---
# hooks:
#   pre:  "echo 'before skill runs'"
#   post: "echo 'after skill completes'"
#
# --- Shell Override ---
# shell: bash            # bash | zsh | sh
---

# {{TITLE}}

{{INTRO_PARAGRAPH}}

## Input

**Arguments:** `$ARGUMENTS`

The user may provide optional arguments when invoking this skill. Dynamic context is available via:
- `$ARGUMENTS` — raw argument string passed by the user
- `$CLAUDE_CONTEXT` — active file/selection context (if any)
- `` !`cmd` `` — command output injected before Claude reads the prompt (e.g., `` !`git status -s` ``)

## Instructions

### Phase 1: {{PHASE_1_TITLE}}

1. {{STEP_1}}
2. {{STEP_2}}
3. {{STEP_3}}

### Phase 2: {{PHASE_2_TITLE}}

1. {{STEP_1}}
2. {{STEP_2}}

## Output

Describe what output the skill produces (in-conversation, file, etc.)

## Example

```
User: /{{SKILL_NAME}}

Claude: [Example response]
```

## Error Handling

- If {{ERROR_CONDITION_1}}: {{ERROR_ACTION_1}}
- If {{ERROR_CONDITION_2}}: {{ERROR_ACTION_2}}
