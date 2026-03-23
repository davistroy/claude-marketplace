---
command: scaffold-plugin
type: command
fixtures: []
---

# Eval: /scaffold-plugin

## Purpose

Creates a new plugin with the proper directory structure, metadata files, and starter files. Good output: a complete, valid plugin skeleton that passes `/validate-plugin` immediately after creation.

## Fixtures

None — generates directory structure in the marketplace repo.

## Setup

Run on a feature branch to avoid polluting main with test plugins.

## Test Scenarios

### S1: Happy path — scaffold a new plugin

**Invocation:** `/scaffold-plugin` (then answer prompts)

**Interaction:**
- Plugin name: `test-plugin`
- Description: `Test plugin for eval purposes`

**Must:**
- [ ] Creates `plugins/test-plugin/` directory
- [ ] Creates `plugins/test-plugin/.claude-plugin/plugin.json` with correct metadata
- [ ] Creates `plugins/test-plugin/commands/` directory
- [ ] Creates `plugins/test-plugin/skills/` directory
- [ ] Creates `plugins/test-plugin/skills/help/SKILL.md` with `name: help` frontmatter
- [ ] plugin.json has `name`, `version`, `description` fields
- [ ] Registers the new plugin in `.claude-plugin/marketplace.json`

**Should:**
- [ ] Creates a starter command file with placeholder content
- [ ] Creates a `references/` directory
- [ ] Reports which files were created

**Must NOT:**
- [ ] Create files with invalid JSON (plugin.json must be valid)
- [ ] Skip registering in marketplace.json
- [ ] Use a flat skill file (`skills/help.md`) instead of nested structure

---

### S2: Validate scaffold immediately

**After S1**, run:

**Invocation:** `/validate-plugin test-plugin`

**Must:**
- [ ] Plugin passes all structural validation checks
- [ ] No "missing required file" errors

---

### S3: Plugin name as argument

**Invocation:** `/scaffold-plugin analytics-plugin`

**Must:**
- [ ] Uses `analytics-plugin` without prompting for name
- [ ] Creates `plugins/analytics-plugin/` with all required files

---

### S4: Error — plugin already exists

**Invocation:** `/scaffold-plugin personal-plugin`

**Must:**
- [ ] Detects that `plugins/personal-plugin/` already exists
- [ ] Prompts to confirm overwrite or aborts
- [ ] Does not overwrite existing plugin silently

---

### S5: Cleanup after eval

**After evals**, clean up test plugins:

```bash
rm -rf plugins/test-plugin plugins/analytics-plugin
# also revert marketplace.json
```

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| All required directories and files created | Required |
| plugin.json is valid JSON with required fields | Required |
| help skill uses nested structure (not flat file) | Required |
| Plugin registered in marketplace.json | Required |
| Passes /validate-plugin immediately | Required |
