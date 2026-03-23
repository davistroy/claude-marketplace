---
command: new-command
type: command
fixtures: []
---

# Eval: /new-command

## Purpose

Generates a new command file from a template with proper structure and conventions. Good output: a `.md` file in `commands/` with correct frontmatter, input validation section, instructions, error handling, examples, and related commands — following the conventions in the plugin CLAUDE.md.

## Fixtures

None — this command generates new files in the plugin directory.

## Setup

Run these evals in a test branch. The command should be invoked from the marketplace repo root.

## Test Scenarios

### S1: Happy path — generate a new command

**Invocation:** `/new-command` (then provide name and description when prompted)

**Interaction:**
- Name: `summarize-code`
- Description: `Summarize a code file or directory into a plain-English description`

**Must:**
- [ ] Creates `plugins/personal-plugin/commands/summarize-code.md`
- [ ] File has valid YAML frontmatter with `description` field
- [ ] File does NOT have a `name` field in frontmatter (filename determines command name)
- [ ] File has an "Input Validation" section
- [ ] File has an "Instructions" or main workflow section
- [ ] File has an "Error Handling" section or table
- [ ] File has example usage

**Should:**
- [ ] Includes a "Related Commands" section
- [ ] Includes "Performance" estimates
- [ ] Frontmatter includes `allowed-tools` appropriate to the command type

**Must NOT:**
- [ ] Add `name:` to the frontmatter
- [ ] Create the file outside `plugins/personal-plugin/commands/`
- [ ] Generate a file that fails `/validate-plugin` structure checks

---

### S2: Command name provided as argument

**Invocation:** `/new-command export-report`

**Must:**
- [ ] Uses `export-report` as the command name without prompting for it
- [ ] Creates `plugins/personal-plugin/commands/export-report.md`

---

### S3: Error — command already exists

**Invocation:** `/new-command assess-document`

**Must:**
- [ ] Detects that `commands/assess-document.md` already exists
- [ ] Prompts user to confirm overwrite or aborts
- [ ] Does not silently overwrite

---

### S4: Invalid name (spaces or special chars)

**Invocation:** `/new-command "my command"` or `/new-command my_command`

**Must:**
- [ ] Either converts to kebab-case (`my-command`) and proceeds
- [ ] Or displays an error explaining valid naming conventions

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| File created at correct path | Required |
| No `name` field in frontmatter | Required |
| Required sections present (validation, instructions, errors, examples) | Required |
| Validates successfully with /validate-plugin | Required |
| Does not overwrite existing command silently | Required |
