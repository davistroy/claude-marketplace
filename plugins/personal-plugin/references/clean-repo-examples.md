# clean-repo JSON Schema and Examples

**Purpose:** The machine-readable `--json` output schema and full example transcripts for `/clean-repo`, kept out of the command file to hold it to the progressive-disclosure line budget. The command's phase-by-phase workflow (Phases 0-5) and the behavioral contract for `--json` mode (raw JSON only, no surrounding text) live inline in `commands/clean-repo.md`; this file carries the schema shape and worked transcripts.

**Consumer:** `commands/clean-repo.md` — "JSON Output Mode" (schema) and "Examples" (transcripts) sections point here.

---

## JSON Output Schema

Used when `/clean-repo` is invoked with `--json`. See `commands/clean-repo.md` → "JSON Output Mode" for the behavioral contract.

```json
{
  "phases": [
    {
      "name": "string — phase name (e.g., 'Artifact Cleanup', 'Structure Validation')",
      "actions": [
        {
          "type": "string — delete | move | update | create | skip",
          "path": "string — file or directory path affected",
          "status": "string — completed | skipped | failed | dry-run",
          "detail": "string — optional description of what was done"
        }
      ]
    }
  ],
  "summary": {
    "files_deleted": "number — count of files removed",
    "files_moved": "number — count of files relocated",
    "docs_updated": "number — count of documentation files modified"
  }
}
```

---

## Examples

### `--dry-run` mode

```text
User: /clean-repo --dry-run

Claude:
## Repository Analysis

**Project:** claude-marketplace - Claude Code plugin marketplace
**Type:** monorepo (plugin marketplace)
**Main Components:**
- personal-plugin: 21 commands, 10 skills, 3 Python tools
- bpmn-plugin: 2 skills, 1 Python tool

**Documentation Map:**
- Root: README.md, CLAUDE.md, CHANGELOG.md, CONTRIBUTING.md
- plugins/personal-plugin/: references/, tools/
- plugins/bpmn-plugin/: references/, templates/, examples/

**Proceeding to cleanup...**

### Phase 1: Artifact Cleanup
[DRY-RUN] Would delete: .coverage (294 KB)
[DRY-RUN] Would delete: plugins/bpmn-plugin/tools/bpmn2drawio/.coverage (147 KB)
[DRY-RUN] Would add to .gitignore: *.pyc

### Phase 2: Structure Validation
All standard files present (README.md, LICENSE, .gitignore, CHANGELOG.md)
Plugin structure valid for personal-plugin and bpmn-plugin

### Phase 3: Documentation Deep Sync
[DRY-RUN] Would update README.md: version reference 4.0.0 -> 5.0.0
[DRY-RUN] Would update CLAUDE.md: add new command "plan-next" to listing

No files were modified (dry-run mode).
```

### Default run

```text
User: /clean-repo

Claude:
## Repository Analysis
...

## Repository Cleanup Complete

### Artifacts Removed
- 3 .coverage files cleaned (588 KB recovered)
- 2 __pycache__ directories removed

### Documentation Updated
- README.md: updated version references, fixed 2 dead links
- CLAUDE.md: added missing command entries, corrected directory structure
- CHANGELOG.md: current (no updates needed)

### Configuration Synced
- marketplace.json version matches plugin.json (both 5.0.0)

### Git Hygiene
- .gitignore updated with 2 new patterns
- No stale branches found

### Remaining Items
- None
```

### `--docs-only --audit` mode

```text
User: /clean-repo --docs-only --audit

Claude:
[Skipping Phase 1: Artifact Cleanup (--docs-only)]

## Repository Analysis
...

### Phase 3: Documentation Deep Sync
Updated README.md: corrected installation command syntax
Updated CLAUDE.md: added 3 new skills to listing
Audit log written to .claude-plugin/audit.log (12 entries)

### Phase 4: Configuration Consistency
All versions consistent across manifests.
```
