---
command: validate-plugin
type: command
fixtures: []
---

# Eval: /validate-plugin

## Purpose

Validates a plugin's directory structure, frontmatter fields, and content for consistency and correctness. Good output: a clear pass/fail result with specific findings for any structural or metadata issues.

## Fixtures

None — operates on plugins in the marketplace repo.

## Test Scenarios

### S1: Validate personal-plugin (should pass)

**Invocation:** `/validate-plugin personal-plugin`

**Must:**
- [ ] Checks `plugins/personal-plugin/.claude-plugin/plugin.json` exists and is valid JSON
- [ ] Checks all `commands/*.md` files have valid frontmatter (`description` field, no `name` field)
- [ ] Checks all `skills/*/SKILL.md` files have `name` and `description` in frontmatter
- [ ] Reports overall PASS or FAIL
- [ ] No false positives on a known-good plugin

**Should:**
- [ ] Reports count of commands and skills validated
- [ ] Lists any warnings (non-fatal issues)

**Must NOT:**
- [ ] Report FAIL for a plugin that is structurally correct

---

### S2: Validate bpmn-plugin

**Invocation:** `/validate-plugin bpmn-plugin`

**Must:**
- [ ] Passes without false positives on the bpmn-plugin structure

---

### S3: Validate --all plugins

**Invocation:** `/validate-plugin --all`

**Must:**
- [ ] Validates every plugin registered in marketplace.json
- [ ] Reports pass/fail for each
- [ ] Reports any naming collisions (two plugins with the same command name)

---

### S4: Detect missing name in skill frontmatter

**Setup:** Temporarily create a test skill file with no `name` field:
```bash
mkdir -p plugins/personal-plugin/skills/testbad
echo "---
description: test skill without name
---
# Test" > plugins/personal-plugin/skills/testbad/SKILL.md
```

**Invocation:** `/validate-plugin personal-plugin`

**Must:**
- [ ] Reports FAIL with specific error: skill `testbad` is missing `name` field
- [ ] References the exact file path

**Cleanup:** Remove the test skill after eval.

---

### S5: Detect flat skill file (wrong structure)

**Setup:** Create `plugins/personal-plugin/skills/flatskill.md` (flat, not nested).

**Invocation:** `/validate-plugin personal-plugin`

**Must:**
- [ ] Reports warning or error that `flatskill.md` is a flat skill file (won't be discovered by Claude Code)

**Cleanup:** Remove after eval.

---

### S6: --check-updates flag

**Invocation:** `/validate-plugin personal-plugin --check-updates`

**Must:**
- [ ] Checks the marketplace for available updates to the plugin
- [ ] Reports current version vs latest available

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Correctly validates known-good plugins without false positives | Required |
| Detects missing `name` in skill frontmatter | Required |
| Detects flat skill files | Required |
| Detects naming collisions with --all | Should |
| Specific file paths in error messages | Required |
