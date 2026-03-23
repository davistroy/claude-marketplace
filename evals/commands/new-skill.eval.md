---
command: new-skill
type: command
fixtures: []
---

# Eval: /new-skill

## Purpose

Generates a new skill file with proper nested directory structure and required frontmatter. Good output: a `skills/<name>/SKILL.md` file with `name` and `description` in frontmatter, proactive trigger conditions, and the correct nested structure.

## Fixtures

None — generates files in the plugin directory.

## Test Scenarios

### S1: Happy path — generate a new skill

**Invocation:** `/new-skill` (then provide name and description when prompted)

**Interaction:**
- Name: `diff-summary`
- Description: `Summarize staged git changes before committing`

**Must:**
- [ ] Creates `plugins/personal-plugin/skills/diff-summary/SKILL.md`
- [ ] SKILL.md has `name: diff-summary` in frontmatter
- [ ] SKILL.md has `description:` in frontmatter
- [ ] File is named exactly `SKILL.md` (uppercase)
- [ ] Directory name matches the `name` field exactly

**Should:**
- [ ] Includes "Proactive Triggers" section describing when Claude should suggest the skill
- [ ] Includes `allowed-tools` frontmatter field
- [ ] Includes at least one usage example

**Must NOT:**
- [ ] Create `skills/diff-summary.md` (flat structure — skill would not be discovered)
- [ ] Create `skills/diff-summary/skill.md` (wrong case — skill would not be discovered)
- [ ] Omit `name` from frontmatter (skill would not be registered)

---

### S2: Skill name provided as argument

**Invocation:** `/new-skill audit-log`

**Must:**
- [ ] Creates `plugins/personal-plugin/skills/audit-log/SKILL.md`
- [ ] `name: audit-log` in frontmatter

---

### S3: Error — skill already exists

**Invocation:** `/new-skill ship`

**Must:**
- [ ] Detects `skills/ship/SKILL.md` already exists
- [ ] Prompts to confirm overwrite or aborts
- [ ] Does not silently overwrite the existing `ship` skill

---

### S4: Validate created skill

**After running S1**, run:

**Invocation:** `/validate-plugin personal-plugin`

**Must:**
- [ ] The new `diff-summary` skill passes validation
- [ ] No missing `name` or `description` errors reported

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Nested directory structure created (not flat file) | Required |
| File named exactly SKILL.md (uppercase) | Required |
| `name` field in frontmatter matches directory name | Required |
| `description` field present | Required |
| Proactive triggers section included | Should |
