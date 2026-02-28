---
description: Automate version bumping across plugin files with CHANGELOG placeholder
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Bump Version Command

Automate version updates across all plugin configuration files. This command ensures version numbers stay synchronized between plugin.json, marketplace.json, and CHANGELOG.md.

## Input Validation

**Required Arguments:**
- `<plugin-name>` - Name of the plugin to version (e.g., `personal-plugin`, `bpmn-plugin`)
- `<bump-type>` - Type of version bump: `major`, `minor`, or `patch`

**Optional Arguments:**
- `--dry-run` - Preview version changes without modifying any files

**Dry-Run Mode:**
When `--dry-run` is specified:
- Show current version and calculated new version
- Show which files would be modified with their proposed changes
- Show the diff that would be applied to each file
- Prefix all output with `[DRY-RUN]` to clearly indicate preview mode
- Do NOT write any changes to disk
- Skip the commit prompt (nothing to commit in dry-run)

**Validation:**
If arguments are missing or invalid, display:
```text
Usage: /bump-version <plugin-name> <major|minor|patch>

Examples:
  /bump-version personal-plugin minor    # 1.6.0 -> 1.7.0
  /bump-version bpmn-plugin patch        # 1.5.0 -> 1.5.1
  /bump-version personal-plugin major    # 1.6.0 -> 2.0.0

Available plugins:
  - personal-plugin
  - bpmn-plugin
```

If plugin-name is not found, display:
```text
Error: Plugin '[name]' not found.

Available plugins:
  - personal-plugin
  - bpmn-plugin

Check the plugins/ directory for valid plugin names.
```

If bump-type is invalid, display:
```text
Error: Invalid bump type '[type]'.

Valid bump types:
  - major  (breaking changes)      1.0.0 -> 2.0.0
  - minor  (new features)          1.0.0 -> 1.1.0
  - patch  (bug fixes)             1.0.0 -> 1.0.1
```

## Instructions

### Phase 1: Read Current Version

1. **Locate plugin.json:**
   ```
   plugins/[plugin-name]/.claude-plugin/plugin.json
   ```

2. **Read and parse the file:**
   - Extract current `version` field
   - Validate it follows semver format (X.Y.Z)

3. **Report current state:**
   ```
   Current version: [plugin-name] v[X.Y.Z]
   ```

### Phase 2: Calculate New Version

Apply the bump type to the current version:

| Bump Type | Current | New |
|-----------|---------|-----|
| major | 1.6.0 | 2.0.0 |
| minor | 1.6.0 | 1.7.0 |
| patch | 1.6.0 | 1.6.1 |

**Rules:**
- `major`: Increment first number, reset others to 0
- `minor`: Increment second number, reset third to 0
- `patch`: Increment third number only

### Phase 3: Update Files

Update the following files with the new version:

#### 3.1 Plugin Configuration

**File:** `plugins/[plugin-name]/.claude-plugin/plugin.json`

Update the `"version"` field:
```json
{
  "name": "[plugin-name]",
  "version": "[NEW_VERSION]",
  ...
}
```

#### 3.2 Marketplace Registry

**File:** `.claude-plugin/marketplace.json`

Find the plugin entry in the `plugins` array and update its `"version"`:
```json
{
  "plugins": [
    {
      "name": "[plugin-name]",
      "version": "[NEW_VERSION]",
      ...
    }
  ]
}
```

#### 3.3 CHANGELOG Placeholder

**File:** `CHANGELOG.md`

Add a new version section if it doesn't exist. Insert after `## [Unreleased]`:

```markdown
## [Unreleased]

## [NEW_VERSION] - YYYY-MM-DD

### Added
- [Describe new features]

### Changed
- [Describe changes to existing features]

### Fixed
- [Describe bug fixes]
```

**Note:** Use today's date in YYYY-MM-DD format. The placeholder categories should be filled in before committing.

### Phase 4: Show Diff and Summary

Display the changes made:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version Bump Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugin: [plugin-name]
Version: [OLD_VERSION] -> [NEW_VERSION]
Bump Type: [major|minor|patch]

Files Updated:
  1. plugins/[plugin-name]/.claude-plugin/plugin.json
  2. .claude-plugin/marketplace.json
  3. CHANGELOG.md (placeholder added)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Phase 5: Prompt for Commit

Ask user if they want to commit the changes:

```text
Would you like to commit these version changes?

Suggested commit message:
  chore([plugin-name]): bump version to [NEW_VERSION]

Type 'commit' to create the commit, or 'skip' to leave changes staged.
```

If user types 'commit':
1. Stage all modified files
2. Create commit with the suggested message
3. Report success

If user types 'skip':
1. Report that changes are saved but not committed
2. Remind user to commit manually after updating CHANGELOG

## Error Handling

- **Plugin not found:** Report error with list of valid plugins
- **Invalid version format:** Report error and current version format
- **File write failure:** Report which file failed and why
- **JSON parse error:** Report file and suggest manual inspection

## Safety Rules

1. **Always show diff** - Never commit without showing what changed
2. **Preserve formatting** - Maintain existing JSON indentation (2 spaces)
3. **Backup consideration** - Changes can be reverted with `git checkout`
4. **Validate before write** - Ensure new version is valid semver

## Example Usage

```yaml
User: /bump-version personal-plugin minor

Claude: Current version: personal-plugin v1.6.0

Calculating new version...
  minor bump: 1.6.0 -> 1.7.0

Updating files...
  ✓ plugins/personal-plugin/.claude-plugin/plugin.json
  ✓ .claude-plugin/marketplace.json
  ✓ CHANGELOG.md (placeholder added)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version Bump Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugin: personal-plugin
Version: 1.6.0 -> 1.7.0
Bump Type: minor

Files Updated:
  1. plugins/personal-plugin/.claude-plugin/plugin.json
  2. .claude-plugin/marketplace.json
  3. CHANGELOG.md (placeholder added)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Would you like to commit these version changes?

Suggested commit message:
  chore(personal-plugin): bump version to 1.7.0

Type 'commit' to create the commit, or 'skip' to leave changes staged.

User: commit

Claude: ✓ Changes committed: chore(personal-plugin): bump version to 1.7.0

Don't forget to:
  1. Update CHANGELOG.md with actual changes before pushing
  2. Create a git tag: git tag v1.7.0
  3. Push with tags: git push && git push --tags
```

## Related Commands

- `/validate-plugin` — Verify plugin structure and version synchronization after bumping
- `/check-updates` — Compare installed vs marketplace versions
- `/clean-repo` — Repository cleanup including version consistency checks
- `/scaffold-plugin` — Create a new plugin (sets initial version to 1.0.0)
