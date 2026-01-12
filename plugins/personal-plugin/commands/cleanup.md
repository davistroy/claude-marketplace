---
description: Comprehensive repository cleanup, organization, and documentation refresh
---

# Repository Cleanup and Organization

Perform a thorough cleanup and organization pass on this repository. Execute each phase systematically.

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

## Phase 3: Documentation Audit

### README.md Validation
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

### CLAUDE.md Validation (if exists)
Verify CLAUDE.md follows best practices:
- [ ] Concise project overview
- [ ] Accurate repository structure documentation
- [ ] Key commands and workflows
- [ ] Conventions and patterns used
- [ ] No redundant or obvious instructions

Check for issues:
- Structure documentation doesn't match actual structure
- References to non-existent files or directories
- Outdated conventions or patterns
- Excessive verbosity or filler content

### Other Documentation
- Check `docs/` folder contents are current
- Verify inline code comments match implementation
- Check for TODO/FIXME comments that are stale

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
