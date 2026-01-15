---
description: Comprehensive repository cleanup, organization, and documentation refresh
---

# Repository Cleanup and Organization

Perform a thorough cleanup and organization pass on this repository. Execute each phase systematically.

## Input Validation

**Optional Arguments:**
- `--dry-run` - Preview all changes without executing them
- `--audit` - Log all actions to `.claude-plugin/audit.log` (see common-patterns.md)

**Dry-Run Mode:**
When `--dry-run` is specified:
- Perform all analysis phases normally
- Show what files would be deleted, moved, or modified
- Show what `.gitignore` entries would be added
- Show what documentation updates would be made
- Prefix all proposed actions with `[DRY-RUN]` to clearly indicate preview mode
- Do NOT execute any file deletions, moves, or modifications
- Skip all confirmation prompts (nothing will be executed anyway)

**Audit Mode:**
When `--audit` is specified:
- Log every file deletion and move to `.claude-plugin/audit.log`
- Each log entry is a JSON line with: timestamp, command, action, path, success
- Create `.claude-plugin/` directory if it doesn't exist
- Append to log file (never overwrite existing entries)

Example log entries:
```json
{"timestamp": "2026-01-14T10:30:00Z", "command": "clean-repo", "action": "delete", "path": "temp/cache.json", "success": true}
{"timestamp": "2026-01-14T10:30:01Z", "command": "clean-repo", "action": "move", "path": "old.md", "details": {"to": "archive/old.md"}, "success": true}
```

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

## Phase 2: Structure Validation

Verify the repository structure follows conventions:

### Standard Files in Root
Check for presence and proper location of:
- `README.md` - Must exist in root
- `LICENSE` or `LICENSE.md` - Should exist for open source
- `.gitignore` - Should exist and be comprehensive
- `CHANGELOG.md` - Recommended for versioned projects
- `CONTRIBUTING.md` - Recommended for collaborative projects

### Framework-Specific Structure
Detect the project type and validate structure:
- **Node.js**: `package.json` in root, source in `src/` or root
- **Python**: `setup.py`/`pyproject.toml` in root, source in `src/` or package dir
- **Claude Code Plugin**: `.claude-plugin/` or `.claude/commands/` structure
- **Monorepo**: `packages/` or `apps/` with proper workspace config

### Misplaced Files
Look for:
- Source files in root that belong in `src/`
- Config files in wrong locations
- Documentation scattered instead of in `docs/`
- Test files outside of `tests/` or `__tests__/`

**Actions:**
1. Report structural issues found
2. Propose file moves if needed (confirm before executing)
3. Note any missing standard files

## Phase 3: Documentation Audit and Remediation

Perform a thorough documentation audit and update. This phase incorporates comprehensive documentation review.

### 3.1 Documentation Discovery

Map the entire project structure and identify ALL documentation touchpoints:
- README files (root and subdirectories)
- Inline code comments and docstrings/JSDoc/type annotations
- API documentation
- Configuration file comments
- CHANGELOG, CONTRIBUTING, LICENSE files
- Doc folders (`/docs`, `/documentation`, etc.)
- Package.json descriptions, setup.py metadata, etc.

### 3.2 Documentation Analysis

For each documentation touchpoint, evaluate:
- Does the code behavior match its documentation?
- Are there undocumented functions, classes, modules, or exports?
- Are examples/usage snippets still accurate and runnable?
- Are dependencies and version requirements current?
- Is terminology consistent across all docs?
- Are there dead links or references to removed code?

### 3.3 README.md Validation

Verify README contains:
- [ ] Project name and clear description
- [ ] Installation/setup instructions
- [ ] Basic usage examples
- [ ] Link to more detailed docs (if they exist)
- [ ] License mention
- [ ] Accurate information (no stale references)

Check for issues:
- References to old project names, URLs, or paths
- Outdated version numbers or dependencies
- Broken links (internal and external)
- Missing or outdated badges

### 3.4 CLAUDE.md Optimization

Evaluate CLAUDE.md against these criteria:
1. **Structure**: Does it follow best practices? (project overview → key commands → architecture → conventions)
2. **Conciseness**: Is every line earning its place? Remove filler words and redundant explanations
3. **Actionability**: Are instructions specific and useful for Claude Code, or generic boilerplate?
4. **Duplication**: Identify and eliminate repeated information across sections
5. **Coherence**: Does information flow logically? Are related topics grouped together?
6. **Relevance**: Remove outdated info, dead links, or references to non-existent files/features

Refactoring guidelines:
- **Merge overlapping sections** - Combine related guidance into single coherent blocks
- **Use terse, imperative language** - "Use X for Y" not "When you need to do Y, you should consider using X"
- **Prefer lists over prose** - Bullets and tables scan faster than paragraphs
- **Cut meta-commentary** - Remove "This section describes..." type filler
- **Consolidate commands** - Group related shell commands, don't scatter them
- **Eliminate obvious instructions** - Don't tell Claude to "read files" or "understand code"
- **Keep domain knowledge** - Preserve project-specific terminology, stakeholders, and context

### 3.5 Documentation Remediation

Apply these updates to all documentation:
1. **Accuracy**: Fix any documentation that contradicts actual code behavior
2. **Completeness**: Add missing docstrings, parameter descriptions, return types, and usage examples
3. **Clarity**: Rewrite confusing explanations; break up walls of text
4. **Consistency**: Standardize formatting, heading styles, and terminology
5. **Currency**: Update version numbers, deprecation notices, and outdated patterns
6. **Cleanup**: Remove commented-out code, stale TODOs, and redundant documentation

### 3.6 Other Documentation

- Check `docs/` folder contents are current
- Verify inline code comments match implementation
- Check for TODO/FIXME comments that are stale
- Create missing documentation files if the project lacks them (README, CONTRIBUTING, etc.)
- Note any significant architectural decisions that should be documented

## Phase 4: Configuration Consistency

### Package Metadata
For projects with package files, verify:
- `name` field matches project identity
- `description` is accurate and helpful
- `repository`, `homepage`, `bugs` URLs are correct
- `version` follows semver and is current
- `author`/`contributors` information is accurate

### Cross-File Consistency
Check that these match across files:
- Project name (README, package.json, CLAUDE.md, etc.)
- Version numbers
- Repository URLs
- Author/maintainer information

## Phase 5: Git Hygiene

### Branch Cleanup
- Identify merged branches that can be deleted
- Check for stale remote tracking branches

### Gitignore Completeness
Ensure `.gitignore` includes:
- Language-specific artifacts
- IDE/editor files
- OS-specific files
- Environment files (`.env`, `.env.local`)
- Build outputs
- Dependency directories

## Execution Instructions

1. **Scan first, act second** - Complete all phases of analysis before making changes
2. **Present findings** - Show a summary of all issues found, categorized by severity
3. **Propose changes** - List specific changes to be made
4. **Confirm before bulk operations** - Get user approval before:
   - Deleting multiple files
   - Moving files to new locations
   - Updating multiple documentation files
5. **Make changes incrementally** - Execute approved changes, showing progress
6. **Summarize results** - Report what was cleaned, moved, updated, and any remaining items

## Output Format

### Initial Report
```
## Repository Cleanup Report

### Artifacts Found
- [X files] Temporary files
- [X files] Build artifacts
- [X files] OS/IDE artifacts

### Structure Issues
- [List of misplaced or missing files]

### Documentation Issues
- [List of outdated or missing documentation]

### Configuration Issues
- [List of inconsistencies]

### Recommended Actions
1. [Priority-ordered list of changes]
```

### After Cleanup
```
## Cleanup Complete

### Removed
- [X] temp files deleted
- [X] artifacts cleaned

### Updated
- [List of files updated with brief description]

### Remaining Items
- [Any manual actions needed]
```

## Safety Rules

- **Never delete source code** - Only remove artifacts and temp files
- **Preserve git history** - Don't rewrite history without explicit request
- **Backup before bulk moves** - Suggest committing current state first
- **Skip if uncertain** - Flag ambiguous files for user decision rather than guessing
