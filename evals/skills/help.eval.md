---
command: help
type: skill
fixtures: []
---

# Eval: /help (skill)

## Purpose

Dynamically discovers and lists all available commands and skills in personal-plugin using Glob-based scanning. Good output: an accurate, complete list that matches the actual files on disk — not a hardcoded list.

## Fixtures

None — discovers files in the plugin directory.

## Test Scenarios

### S1: Basic invocation

**Invocation:** `/help` or `/personal-plugin:help`

**Must:**
- [ ] Lists all commands currently in `plugins/personal-plugin/commands/*.md`
- [ ] Lists all skills currently in `plugins/personal-plugin/skills/*/SKILL.md`
- [ ] Each entry shows the command/skill name and its description (from frontmatter)
- [ ] Output is organized (commands section, skills section)

**Should:**
- [ ] Shows invocation syntax for each command (e.g., `/assess-document <path>`)
- [ ] Notes any flags or key options for complex commands

**Must NOT:**
- [ ] Show a hardcoded list that could be out of date
- [ ] List commands from other plugins as personal-plugin commands
- [ ] List deprecated commands from `deprecated/` directory as active commands

---

### S2: Accuracy after adding a new command

**Setup:** Create a new command file `plugins/personal-plugin/commands/test-eval-cmd.md` with a description in frontmatter.

**Invocation:** `/help`

**Must:**
- [ ] The new `test-eval-cmd` command appears in the output
- [ ] Its description matches the frontmatter description

**Cleanup:** Remove the test command after eval.

---

### S3: Accuracy after removing a command

**Setup:** Temporarily rename a command file (e.g., rename `new-command.md` to `new-command.md.bak`).

**Invocation:** `/help`

**Must:**
- [ ] `new-command` does NOT appear in the output

**Cleanup:** Restore the renamed file.

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| All active commands listed | Required |
| All active skills listed | Required |
| Descriptions accurate (from frontmatter) | Required |
| Deprecated commands excluded | Required |
| Dynamically discovers (not hardcoded) | Required |
