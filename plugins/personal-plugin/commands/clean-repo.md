---
description: Comprehensive repository cleanup, organization, and documentation refresh
---

# Repository Cleanup and Organization

Perform a thorough cleanup and organization pass on this repository. **This command requires deep analysis of the codebase before any cleanup actions.**

## Input Validation

**Optional Arguments:**
- `--dry-run` - Preview all changes without executing them
- `--audit` - Log all actions to `.claude-plugin/audit.log`
- `--docs-only` - Skip artifact cleanup, focus only on documentation sync

**Dry-Run Mode:**
When `--dry-run` is specified:
- Perform all analysis phases normally
- Show what files would be deleted, moved, or modified
- Show what documentation updates would be made
- Prefix all proposed actions with `[DRY-RUN]`
- Do NOT execute any file deletions, moves, or modifications

**Audit Mode:**
When `--audit` is specified:
- Log every action to `.claude-plugin/audit.log`
- Each log entry is a JSON line with: timestamp, command, action, path, success

---

## Phase 0: Deep Repository Analysis (REQUIRED)

**CRITICAL: This phase must be completed thoroughly before any cleanup.**

Before cleaning or updating anything, you MUST understand what this repository actually contains and does. Use the available tools to build a complete mental model.

### 0.1 Project Discovery

Execute these analysis steps:

```
1. Read the root README.md completely
2. Read CLAUDE.md if present
3. Examine the directory structure (use Glob to map all directories)
4. Identify the project type(s): library, CLI tool, plugin, monorepo, etc.
5. Find all package manifests (package.json, pyproject.toml, plugin.json, etc.)
```

### 0.2 Feature Inventory

Build a complete list of what this project provides:

**For plugins/tools:**
- List all commands/skills with their actual functionality
- Read command/skill files to understand what each does
- Note any bundled tools or utilities

**For libraries:**
- List all exported functions/classes
- Identify the public API surface
- Note major features and capabilities

**For applications:**
- Identify main entry points
- List key features and user flows
- Note external integrations

### 0.3 Documentation Inventory

Map ALL documentation in the repository:

```bash
# Find all markdown files
find . -name "*.md" -type f | grep -v node_modules | grep -v .git

# Find all README files
find . -name "README*" -type f
```

Create a documentation map:
```
Documentation Map
-----------------
Root Level:
  - README.md: [purpose]
  - CLAUDE.md: [purpose]
  - CHANGELOG.md: [last updated version]
  - CONTRIBUTING.md: [exists/missing]

Subdirectory READMEs:
  - [path]: [purpose]
  - [path]: [purpose]

Other Docs:
  - docs/: [contents summary]
  - [other locations]
```

### 0.4 Current State Assessment

Before proceeding, summarize:
1. What does this project do? (1-2 sentences)
2. What are its main components/features?
3. Who is the target audience?
4. What documentation exists and where?

**Do not proceed to Phase 1 until this analysis is complete.**

---

## Phase 1: Artifact Cleanup

Identify and remove files that should not be in the repository:

### Temporary Files
- `**/tmp*`, `**/*.tmp`, `**/*.temp`
- `**/tmpclaude-*`, `**/*.bak`, `**/*.swp`, `**/*.swo`
- `**/*~`, `**/*.orig`, `**/*.pyc`, `**/*.pyo`
- `**/__pycache__/`, `**/.cache/`, `**/node_modules/.cache/`
- `**/nul`, `**/NUL` (Windows artifacts)

### Build Artifacts (if not gitignored)
- `**/dist/`, `**/build/`, `**/out/`
- `**/*.log`, `**/logs/`
- `**/.next/`, `**/.nuxt/`, `**/.output/`
- `**/*.egg-info/`, `**/.pytest_cache/`

### IDE/Editor Artifacts (if not gitignored)
- `**/.idea/`, `**/.vscode/` (unless intentionally committed)
- `**/*.iml`, `**/.project`, `**/.classpath`

### OS Artifacts
- `**/.DS_Store`, `**/Thumbs.db`, `**/desktop.ini`

**Actions:**
1. List all suspected artifacts found
2. Check `.gitignore` - add missing patterns if appropriate
3. Remove untracked artifacts from working directory
4. For tracked artifacts that shouldn't be: stage removal and note for commit

---

## Phase 2: Structure Validation

Verify the repository structure follows conventions:

### Standard Files in Root
- `README.md` - Must exist
- `LICENSE` or `LICENSE.md` - Should exist for open source
- `.gitignore` - Should exist and be comprehensive
- `CHANGELOG.md` - Recommended for versioned projects

### Framework-Specific Structure
Detect the project type and validate:
- **Node.js**: `package.json` in root, source in `src/` or root
- **Python**: `pyproject.toml` in root, source in `src/` or package dir
- **Claude Code Plugin**: `.claude-plugin/` with proper structure
- **Monorepo**: `packages/` or `plugins/` with proper workspace config

### Misplaced Files
Look for:
- Source files in root that belong in `src/`
- Config files in wrong locations
- Test files outside of `tests/` or `__tests__/`

---

## Phase 3: Documentation Deep Sync

**This is the most important phase.** Documentation must accurately reflect the current state of the codebase.

### 3.1 Root README.md Verification

**Read the actual code/features, then verify README accuracy:**

| Check | How to Verify |
|-------|---------------|
| Project description | Does it match what the code actually does? |
| Feature list | Are all listed features implemented? Are there unlisted features? |
| Installation steps | Do they actually work? Are dependencies current? |
| Usage examples | Do code snippets reflect current API/CLI? |
| Version references | Are version numbers current? |
| Links | Do all links resolve? Are paths correct? |

**Required Actions:**
1. Read the README completely
2. Cross-reference EVERY claim against actual code
3. Test or verify installation/usage instructions mentally
4. Update any stale information immediately

### 3.2 CLAUDE.md Sync

CLAUDE.md must provide accurate guidance for AI assistants working on this codebase.

**Verification checklist:**
- [ ] Project overview matches reality
- [ ] Listed commands/tools actually exist
- [ ] File paths and directory structure are accurate
- [ ] Build/test commands work
- [ ] Conventions described are actually followed in code
- [ ] No references to removed features or old structure

**If CLAUDE.md is stale, update it to reflect:**
1. Current project structure
2. Actual commands and their purposes
3. Real conventions used in the codebase
4. Current development workflow

### 3.3 Subdirectory README Audit

For EACH subdirectory README found:

1. **Read the README**
2. **Examine the actual directory contents**
3. **Verify every statement:**
   - Do referenced files exist?
   - Do example commands work?
   - Are feature descriptions accurate?
   - Are installation/setup steps current?

**Common issues to fix:**
- Old CLI flags or arguments
- Deprecated API references
- Outdated version requirements
- Missing new features
- Dead internal links

### 3.4 CHANGELOG Currency

**Analysis:**
1. Parse CHANGELOG.md for the most recent version and date
2. Run `git log --oneline` to find commits since then
3. Identify any significant changes not documented

**If CHANGELOG is behind:**
- List missing entries by category (Added, Changed, Fixed, Removed)
- Propose additions in Keep a Changelog format

### 3.5 Code-Documentation Cross-Reference

For projects with inline documentation (docstrings, JSDoc, etc.):

1. Sample 3-5 key files/modules
2. Verify docstrings match actual function behavior
3. Check that parameter types and return values are accurate
4. Flag any obvious mismatches

### 3.6 Documentation Remediation

**Apply these updates immediately (don't just report):**

| Issue Type | Action |
|------------|--------|
| Wrong version number | Update to current |
| Dead link | Fix or remove |
| Missing feature in docs | Add documentation |
| Documented feature removed | Remove from docs |
| Outdated example | Update example |
| Incorrect path/filename | Correct it |

**For complex issues requiring user input:**
- Flag for review
- Propose specific changes
- Ask for confirmation before applying

---

## Phase 4: Configuration Consistency

### Package Metadata Sync
For each package manifest found, verify:
- `name` matches project identity
- `description` is accurate
- `version` is consistent across all manifests
- `repository`, `homepage` URLs are correct

### Cross-File Version Consistency
If multiple files reference versions, ensure they match:
- README badges
- Package manifests
- CHANGELOG latest entry
- Any version constants in code

---

## Phase 5: Git Hygiene

### Branch Cleanup
```bash
# Find merged branches
git branch --merged main | grep -v main

# Find stale remote branches
git remote prune origin --dry-run
```

### Gitignore Completeness
Verify `.gitignore` includes patterns for all artifacts found in Phase 1.

---

## Execution Instructions

### Order of Operations

1. **Phase 0: Analyze** - Build complete understanding of the repository
2. **Phase 1: Clean** - Remove artifacts (quick, low risk)
3. **Phase 2: Validate** - Check structure (identify issues)
4. **Phase 3: Sync Docs** - Update all documentation to match reality
5. **Phase 4: Consistency** - Ensure config files agree
6. **Phase 5: Git** - Clean up branches and gitignore

### Documentation Update Rules

**DO immediately update:**
- Version numbers
- Dead links
- Incorrect file paths
- Obviously wrong statements
- Missing critical information

**ASK before updating:**
- Major rewrites of descriptions
- Removing large sections
- Adding substantial new content
- Changing the document structure

### Output Format

#### Analysis Summary (after Phase 0)
```
## Repository Analysis

**Project:** [name] - [one-line description]

**Type:** [plugin/library/CLI/application/monorepo]

**Main Components:**
- [component]: [purpose]
- [component]: [purpose]

**Documentation Map:**
- Root: README.md, CLAUDE.md, CHANGELOG.md
- [path]: [purpose]

**Proceeding to cleanup...**
```

#### Cleanup Report (after all phases)
```
## Repository Cleanup Complete

### Artifacts Removed
- [X] files/directories cleaned

### Documentation Updated
- [file]: [what was changed]
- [file]: [what was changed]

### Configuration Synced
- [what was synchronized]

### Git Hygiene
- [branches pruned, etc.]

### Remaining Items (if any)
- [items requiring manual review]
```

---

## Safety Rules

- **Never delete source code** - Only remove artifacts and temp files
- **Preserve git history** - Don't rewrite history without explicit request
- **Verify before documenting** - Don't document features you haven't verified exist
- **Update, don't fabricate** - Fix stale docs, don't invent new content
- **Ask when uncertain** - Flag ambiguous issues for user decision
