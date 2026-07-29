---
name: {{SKILL_NAME}}
description: {{DESCRIPTION}}
# argument-hint: "<required-arg> [--optional-flag]"
# effort: medium                    # low | medium | high | xhigh | max
# allowed-tools: {{ALLOWED_TOOLS}}  # e.g., Read, Glob, Grep, Bash, Task
# disable-model-invocation: false   # true = removes LLM call; pure-tool skill (also excludes from proactive triggering)
#
# --- Modern Dispatch ---
# context: fork          # spawn isolated subagent context (no shared conversation history)
# agent: Explore         # subagent type: Explore | Plan | general-purpose | (role-specific strings)
# model: opus            # override model for this skill (tier alias: haiku|sonnet|opus|fable); omit = inherits caller model (ADR-0005)
#
# --- Auto-Activation ---
# paths:                 # activate skill when user opens matching files
#   - "**/*.spec.ts"
#   - "package.json"
#
# --- Lifecycle Hooks ---
# hooks:
#   Stop:
#     - matcher: any
#       hooks:
#         - type: command
#           command: "echo 'after skill completes'"
#           timeout: 5
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
- `!`cmd`` — command output injected before Claude reads the prompt (e.g., `!`git status -s``)
  - Injections run at **parse time**, before `$ARGUMENTS` is available — never inject a command containing a placeholder you expect to be substituted.
  - A non-zero exit **aborts skill load**; it does not degrade to empty output. Guard anything that can fail: `!`git status -s 2>/dev/null || echo "(not a git repository)"``

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
