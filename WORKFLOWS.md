# Workflow Documentation

This document describes how to chain commands together for common use cases. Each workflow shows the complete command sequence and expected outputs.

---

## Table of Contents

1. [Document Completion Workflow](#1-document-completion-workflow)
2. [Code Review Workflow](#2-code-review-workflow)
3. [Architecture Analysis Workflow](#3-architecture-analysis-workflow)
4. [Repository Maintenance Workflow](#4-repository-maintenance-workflow)
5. [New Command Development Workflow](#5-new-command-development-workflow)
6. [BPMN Diagram Workflow](#6-bpmn-diagram-workflow)

---

## 1. Document Completion Workflow

**Purpose:** Extract open questions from a document, answer them interactively, and update the document with answers.

**Best for:** PRDs, specifications, design documents, or any document with TBDs/open items.

### Command Sequence

```
/define-questions docs/my-prd.md
    |
    v
/ask-questions reference/questions-my-prd-20260114-143052.json
    |
    v
/finish-document docs/my-prd.md reference/answers-my-prd-20260114-150000.json
```

### Step-by-Step

#### Step 1: Extract Questions
```
/define-questions docs/requirements.md
```

**Output:** `reference/questions-requirements-20260114-143052.json`

This command scans the document for:
- Explicit questions (marked with `?`)
- TBD/TODO markers
- Placeholders like `[PLACEHOLDER]` or `<FILL IN>`
- Ambiguous sections needing clarification

#### Step 2: Answer Questions Interactively
```
/ask-questions reference/questions-requirements-20260114-143052.json
```

**Output:** `reference/answers-requirements-20260114-150000.json`

This starts an interactive session:
- Questions are presented one at a time
- Type your answer and press Enter
- Use session commands: `help`, `status`, `back`, `skip`, `quit`
- Progress is saved automatically

#### Step 3: Update the Document
```
/finish-document docs/requirements.md reference/answers-requirements-20260114-150000.json
```

**Output:** Updated `docs/requirements.md` with answers integrated.

The command:
- Replaces TBD markers with answers
- Updates placeholder sections
- Adds clarifications inline
- Preserves document structure

### File Naming Convention

| Step | Output Pattern |
|------|----------------|
| Define Questions | `reference/questions-[source]-[timestamp].json` |
| Answer Questions | `reference/answers-[source]-[timestamp].json` |
| Finish Document | Original file updated in place |

---

## 2. Code Review Workflow

**Purpose:** Review a pull request, fix identified issues, and ship the changes.

**Best for:** Ensuring code quality before merging PRs.

### Command Sequence

```
/review-pr 123
    |
    v
Fix identified issues (manually or with Claude)
    |
    v
/ship
```

### Step-by-Step

#### Step 1: Review the PR
```
/review-pr 123
```
or
```
/review-pr https://github.com/owner/repo/pull/123
```

**Output:** In-conversation review report with:
- Security analysis
- Performance assessment
- Code quality evaluation
- Categorized issues (CRITICAL, WARNING, SUGGESTION)

#### Step 2: Fix Issues

Address issues by priority:
1. **CRITICAL** - Must fix before merge
2. **WARNING** - Should fix, may block merge
3. **SUGGESTION** - Nice to have, at discretion

Work through each issue:
```
User: Fix the SQL injection issue in user_service.py
Claude: [Makes the fix]
```

#### Step 3: Ship the Fixes
```
/ship
```

This command:
- Creates a branch (if not on one)
- Commits changes with descriptive message
- Pushes to remote
- Creates/updates PR
- Runs auto-review to catch new issues
- Reports when ready for merge

### Iteration Pattern

If `/ship` auto-review finds issues:
```
/ship
    |
    v
[Auto-review finds issues]
    |
    v
Fix issues
    |
    v
/ship  (repeat until clean)
```

---

## 3. Architecture Analysis Workflow

**Purpose:** Analyze codebase architecture and create an improvement plan.

**Best for:** Planning refactoring, understanding technical debt, onboarding to a codebase.

### Quick Analysis Path

For a fast, conversational analysis:
```
/review-arch
```

**Output:** In-conversation report covering:
- Architecture pattern identification
- Technical debt inventory (CRITICAL/HIGH/MEDIUM/LOW)
- Remediation roadmap (quick wins to strategic initiatives)

**Note:** This is read-only and generates no files.

### Deep Analysis Path

For comprehensive analysis with actionable plan:
```
/plan-improvements
```

**Output:**
- `RECOMMENDATIONS.md` - Categorized improvement recommendations
- `IMPLEMENTATION_PLAN.md` - Phased action plan with work items

### Working Through the Plan

After running `/plan-improvements`:

1. **Review RECOMMENDATIONS.md** for context on each recommendation
2. **Open IMPLEMENTATION_PLAN.md** to see phased work items
3. **Work through phases sequentially**:
   ```
   Phase 1: Documentation & Quick Wins
       Work Item 1.1 -> 1.2 -> 1.3 -> ...
       |
       v
   Phase 2: Quality Foundation
       Work Item 2.1 -> 2.2 -> ...
       |
       v
   [Continue through all phases]
   ```
4. **Mark checkboxes** in IMPLEMENTATION_PLAN.md as you complete items
5. **Run `/ship`** after completing each phase

---

## 4. Repository Maintenance Workflow

**Purpose:** Validate, version, and ship plugin changes.

**Best for:** Before releases, after adding new commands, routine maintenance.

### Command Sequence

```
/validate-plugin
    |
    v
/bump-version
    |
    v
/ship
```

### Step-by-Step

#### Step 1: Validate Plugin Structure
```
/validate-plugin
```

This checks:
- `plugin.json` has required fields
- All commands have valid frontmatter
- No `name` field in frontmatter (uses filename)
- `/help` skill is up to date
- No orphaned files

Fix any reported issues before proceeding.

#### Step 2: Bump Version
```
/bump-version major|minor|patch
```

Example: `/bump-version minor`

This updates:
- Version in `plugin.json`
- Version in `CHANGELOG.md` (adds placeholder if needed)
- Any other version references

#### Step 3: Ship Changes
```
/ship
```

Creates PR with version bump and all changes.

### Periodic Cleanup

For comprehensive repository maintenance:
```
/clean-repo
```

This command:
- Removes orphaned files
- Updates documentation
- Organizes directory structure
- Cleans up temporary files

Run before major releases or when repository becomes cluttered.

---

## 5. New Command Development Workflow

**Purpose:** Create a new command with proper structure and ship it.

**Best for:** Adding new functionality to a plugin.

### Command Sequence

```
/new-command
    |
    v
Test the command
    |
    v
/validate-plugin
    |
    v
/ship
```

### Step-by-Step

#### Step 1: Generate Command Template
```
/new-command my-new-command
```

This creates:
- `commands/my-new-command.md` with proper structure
- Valid frontmatter (description, optional allowed-tools)
- Standard sections (Input Validation, Process, etc.)

#### Step 2: Implement and Test

1. Edit the generated command file
2. Add your implementation logic
3. Test with various inputs:
   - Valid arguments
   - Missing arguments (should show usage)
   - Invalid arguments (should show clear error)
   - Edge cases

#### Step 3: Validate Plugin
```
/validate-plugin
```

Verify:
- Command appears in plugin listing
- Frontmatter is valid
- `/help` includes the new command

#### Step 4: Ship the Command
```
/ship
```

PR description should include:
- What the new command does
- Example usage
- Any dependencies required

---

## 6. BPMN Diagram Workflow

**Purpose:** Generate BPMN diagrams from descriptions and convert to editable Draw.io format.

**Best for:** Process documentation, workflow visualization, business process design.

### Command Sequence

```
/bpmn-generator
    |
    v
/bpmn-to-drawio process.bpmn output.drawio
```

### Step-by-Step

#### Step 1: Generate BPMN

**Interactive Mode** (for new processes):
```
/bpmn-generator
```
Answer structured questions about:
- Process scope (name, triggers, outcomes)
- Participants (pools, lanes, roles)
- Activities (tasks, types)
- Flow control (gateways, conditions)
- Events and exceptions

**Document Mode** (from existing documentation):
```
/bpmn-generator docs/process-description.md
```

**Output:** `process-name.bpmn` - BPMN 2.0 compliant XML

#### Step 2: Convert to Draw.io
```
/bpmn-to-drawio process-name.bpmn output.drawio
```

This converts:
- Pools and lanes with proper hierarchy
- All BPMN element types with correct styling
- Connector routing (including cross-lane flows)
- Color coding by lane function

**Output:** `output.drawio` - Editable in Draw.io Desktop or diagrams.net

#### Step 3: Refine (Optional)

Open in Draw.io to:
- Adjust layout manually
- Add annotations
- Customize colors
- Export to PNG/PDF for documentation

---

## Workflow Tips

### Session Commands

During interactive commands (`/ask-questions`, `/bpmn-generator`):

| Command | Action |
|---------|--------|
| `help` | Show available commands |
| `status` | Show progress (X of Y) |
| `back` | Return to previous item |
| `skip` | Skip current, return later |
| `quit` | Exit and save progress |

### File Organization

| Output Type | Location | Example |
|-------------|----------|---------|
| Analysis reports | `reports/` | `reports/assessment-PRD-20260114.md` |
| Reference data | `reference/` | `reference/questions-spec-20260114.json` |
| Generated docs | Same as source | `docs/spec.docx` |
| Temporary files | `.tmp/` | `.tmp/cache-20260114.json` |

### Handling Interruptions

If a workflow is interrupted:
1. Commands auto-save progress where possible
2. Re-run the same command to resume
3. Check `reference/` for partial output files
4. Use `status` command to see progress

---

*For troubleshooting common issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).*
*For security considerations, see [SECURITY.md](SECURITY.md).*
