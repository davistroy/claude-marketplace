---
command: bump-version
type: command
fixtures: []
---

# Eval: /bump-version

## Purpose

Increments the version number in a plugin's `plugin.json` and `marketplace.json` files and adds a CHANGELOG placeholder entry. Good behavior: updates both files atomically with the correct semantic version bump and does not touch other files.

## Fixtures

None — this command operates on the actual marketplace repository files. Run these evals in a git branch.

## Setup

All scenarios assume the current directory is the marketplace repo root and the working directory is on a feature branch (not main).

## Test Scenarios

### S1: Patch bump — personal-plugin

**Invocation:** `/bump-version personal-plugin patch`

**Setup:** Note the current version in `plugins/personal-plugin/.claude-plugin/plugin.json`.

**Must:**
- [ ] Updates `version` in `plugins/personal-plugin/.claude-plugin/plugin.json` with patch increment (e.g., 2.3.1 → 2.3.2)
- [ ] Updates matching version entry in `.claude-plugin/marketplace.json`
- [ ] Both files show the same new version
- [ ] Adds a CHANGELOG placeholder entry (e.g., `## [2.3.2] - YYYY-MM-DD` or `## Unreleased`)

**Should:**
- [ ] Reports the old and new version to the user
- [ ] Identifies both files that were updated

**Must NOT:**
- [ ] Change any other files (commands, skills, README, etc.)
- [ ] Skip updating marketplace.json

---

### S2: Minor bump — bpmn-plugin

**Invocation:** `/bump-version bpmn-plugin minor`

**Must:**
- [ ] Minor version increments, patch resets to 0 (e.g., 1.4.2 → 1.5.0)
- [ ] Both plugin.json and marketplace.json updated

---

### S3: Major bump

**Invocation:** `/bump-version personal-plugin major`

**Must:**
- [ ] Major version increments, minor and patch reset to 0 (e.g., 2.3.1 → 3.0.0)

---

### S4: Error — unknown plugin name

**Invocation:** `/bump-version nonexistent-plugin patch`

**Must:**
- [ ] Error message listing valid plugin names
- [ ] No files modified

---

### S5: Error — invalid bump type

**Invocation:** `/bump-version personal-plugin hotfix`

**Must:**
- [ ] Error message showing valid bump types: major, minor, patch

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Correct semantic version math for all three bump types | Required |
| Both files (plugin.json and marketplace.json) updated | Required |
| CHANGELOG placeholder added | Required |
| No unrelated files changed | Required |
| Error cases produce informative messages | Required |
