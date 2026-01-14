---
description: Show available commands and skills in this plugin with usage information
---

# Help Skill

Display help information for the personal-plugin commands and skills.

**IMPORTANT:** This skill must be updated whenever commands or skills are added, changed, or removed from this plugin.

## Usage

```
/help                          # Show all commands and skills
/help <command-name>           # Show detailed help for a specific command
```

## Mode 1: List All (no arguments)

When invoked without arguments, display this table:

```
personal-plugin Commands and Skills
===================================

COMMANDS
--------
| Command | Description |
|---------|-------------|
| /analyze-transcript | Convert meeting transcripts to structured markdown report |
| /ask-questions | Interactive Q&A session from questions JSON file |
| /assess-document | Document quality evaluation with scored assessment report |
| /bump-version | Automate version bumping across plugin files with CHANGELOG |
| /clean-repo | Repository cleanup, organization, and documentation refresh |
| /consolidate-documents | Analyze multiple document variations and synthesize |
| /convert-markdown | Convert markdown to formatted Word document |
| /define-questions | Extract questions/TBDs from docs to JSON |
| /develop-image-prompt | Generate AI image prompts from content |
| /finish-document | Extract questions, answer interactively, update document |
| /plan-improvements | Generate improvement recommendations with implementation plan |
| /plan-next | Analyze repo and recommend next action |
| /review-arch | Quick architectural audit (read-only, no files generated) |
| /review-pr | Structured PR review with security and code quality analysis |
| /setup-statusline | Custom status line setup (Windows/PowerShell) |
| /test-project | Ensure 90%+ coverage, run tests, fix, merge PR |
| /validate-plugin | Validate plugin structure, frontmatter, and content |

SKILLS
------
| Skill | Description |
|-------|-------------|
| /help | Show available commands and skills with usage information |
| /ship | Git workflow: branch, commit, push, and open PR |

---
Use '/help <name>' for detailed help on a specific command or skill.
```

## Mode 2: Detailed Help (with argument)

When invoked with a command or skill name, read the corresponding file and display:

1. **Description** - From frontmatter
2. **Arguments** - From "Input Validation" section if present
3. **Output** - What the command produces
4. **Example** - Usage example

### Command Reference

Use this reference to provide detailed help. Read the actual command file to get the most accurate information.

---

#### /analyze-transcript
**Description:** Convert meeting transcripts to structured markdown report
**Arguments:** Transcript content (pasted or file path)
**Output:** `meeting-analysis-YYYYMMDD-HHMMSS.md` in current directory
**Example:**
```
/analyze-transcript meeting-notes.txt
```

---

#### /ask-questions
**Description:** Interactive Q&A session from questions JSON file
**Arguments:** `<questions-file>` - Path to JSON from /define-questions
**Output:** `answers-[source]-YYYYMMDD-HHMMSS.json`
**Example:**
```
/ask-questions questions-PRD-20260114.json
```

---

#### /assess-document
**Description:** Document quality evaluation with scored assessment report
**Arguments:** `<document-path>` - Path to document to assess
**Output:** `[name]-assessment-YYYYMMDD-HHMMSS.md` in same directory as source
**Example:**
```
/assess-document PRD.md
```

---

#### /bump-version
**Description:** Automate version bumping across plugin files with CHANGELOG
**Arguments:** `<plugin-name>` `<major|minor|patch>`
**Output:** Updates plugin.json, marketplace.json, and CHANGELOG.md
**Example:**
```
/bump-version personal-plugin minor
```

---

#### /clean-repo
**Description:** Repository cleanup, organization, and documentation refresh
**Arguments:** None required
**Output:** Cleaned repository with updated documentation
**Example:**
```
/clean-repo
```

---

#### /consolidate-documents
**Description:** Analyze multiple document variations and synthesize a superior version
**Arguments:** `<doc1-path>` `<doc2-path>` `[doc3-path...]` - Two or more documents
**Output:** Consolidated document with consolidation notes
**Example:**
```
/consolidate-documents draft-v1.md draft-v2.md draft-final.md
```

---

#### /convert-markdown
**Description:** Convert markdown to formatted Word document
**Arguments:** `<markdown-file>` `[output-file]`
**Output:** `.docx` file with formatting, TOC, and syntax highlighting
**Example:**
```
/convert-markdown docs/api-guide.md
```

---

#### /define-questions
**Description:** Extract questions and open items from documents to JSON
**Arguments:** `<document-path>` - Path to document to analyze
**Output:** `questions-[name]-YYYYMMDD-HHMMSS.json`
**Example:**
```
/define-questions PRD.md
```

---

#### /develop-image-prompt
**Description:** Generate detailed AI image prompts from content
**Arguments:** `<content-source>` `[--style <style-file>]`
**Output:** `image-prompt-[topic]-YYYYMMDD-HHMMSS.md`
**Example:**
```
/develop-image-prompt architecture.md --style brand-guidelines.md
```

---

#### /finish-document
**Description:** Extract questions, answer interactively, update document
**Arguments:** `<document-path>` `[--auto]`
**Output:** Updated document with resolved questions, backup created
**Example:**
```
/finish-document PRD.md
/finish-document PRD.md --auto
```

---

#### /plan-improvements
**Description:** Generate improvement recommendations with phased implementation plan
**Arguments:** None required
**Output:** `RECOMMENDATIONS.md` and `IMPLEMENTATION_PLAN.md`
**Example:**
```
/plan-improvements
```

---

#### /plan-next
**Description:** Analyze repo and recommend the next logical action
**Arguments:** None required
**Output:** In-conversation recommendation with scope and success criteria
**Example:**
```
/plan-next
```

---

#### /review-arch
**Description:** Quick architectural audit (read-only, no files generated)
**Arguments:** None required
**Output:** In-conversation analysis with technical debt assessment
**Example:**
```
/review-arch
```

---

#### /review-pr
**Description:** Structured PR review with security and code quality analysis
**Arguments:** `<pr-number-or-url>`
**Output:** Review report, optionally posted to GitHub
**Example:**
```
/review-pr 123
/review-pr https://github.com/owner/repo/pull/42
```

---

#### /setup-statusline
**Description:** Custom status line setup for Windows/PowerShell
**Arguments:** None required
**Output:** PowerShell script and settings.json configuration
**Example:**
```
/setup-statusline
```

---

#### /test-project
**Description:** Ensure 90%+ test coverage, run tests, fix failures, merge PR
**Arguments:** None required
**Output:** All tests passing, PR created and merged
**Example:**
```
/test-project
```

---

#### /validate-plugin
**Description:** Validate plugin structure, frontmatter, and content
**Arguments:** `<plugin-name>` `[--all]` `[--fix]` `[--verbose]`
**Output:** Validation report with errors and warnings
**Example:**
```
/validate-plugin personal-plugin
/validate-plugin --all
```

---

#### /help
**Description:** Show available commands and skills with usage information
**Arguments:** `[command-name]` - Optional specific command to get help for
**Output:** Command list or detailed help
**Example:**
```
/help
/help ship
```

---

#### /ship
**Description:** Complete git workflow: branch, commit, push, create PR, auto-review, fix issues, and merge
**Arguments:** `[branch-name]` `[description]`
**Output:**
- Creates branch, commits changes, pushes, and opens PR
- Automatically reviews PR for security, performance, code quality, test coverage, and documentation issues
- Fixes CRITICAL and WARNING issues automatically (up to 5 attempts)
- Squash merges PR when all blocking issues resolved
- If issues cannot be fixed, reports details with manual remediation steps

**Example:**
```
/ship
/ship fix-login-bug
/ship feature/user-export "Add CSV export for user data"
```

**Workflow:**
1. Pre-flight checks (git repo, gh auth, uncommitted changes)
2. Create branch and commit
3. Push and create PR
4. Auto-review PR (5 analysis dimensions)
5. Fix loop (up to 5 attempts for CRITICAL/WARNING issues)
6. Merge on success, or report unfixable issues

---

## Error Handling

If the requested command is not found:
```
Command '[name]' not found in personal-plugin.

Available commands:
  /analyze-transcript, /ask-questions, /assess-document, /bump-version,
  /clean-repo, /consolidate-documents, /convert-markdown, /define-questions,
  /develop-image-prompt, /finish-document, /plan-improvements, /plan-next,
  /review-arch, /review-pr, /setup-statusline, /test-project, /validate-plugin

Available skills:
  /help, /ship
```
