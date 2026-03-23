---
command: clean-repo
type: command
fixtures: []
---

# Eval: /clean-repo

## Purpose

Performs repository cleanup: removes stale files, organizes structure, refreshes documentation. This is a potentially destructive command. Evals should be run in a throwaway clone.

## Fixtures

None — operates on the real repository. **Always run in a git-cloned scratch copy, never on the working repo.**

## Setup

```bash
git clone <marketplace-repo> /tmp/eval-clean-repo-test
cd /tmp/eval-clean-repo-test
# Add some deliberate stale artifacts for testing:
mkdir -p tmp/ && touch tmp/scratch.txt
touch orphaned-note.txt
```

## Test Scenarios

### S1: Standard cleanup run

**Invocation:** `/clean-repo`

**Must:**
- [ ] Presents a summary of what will be cleaned before making changes
- [ ] Identifies obviously stale files (files in `tmp/`, zero-byte files, etc.)
- [ ] Asks for confirmation before deleting anything
- [ ] Does not delete files that are referenced in CLAUDE.md, plugin.json, or marketplace.json

**Should:**
- [ ] Identifies the orphaned-note.txt as a candidate for review
- [ ] Reports what was cleaned and what was skipped
- [ ] Checks for outdated documentation references

**Must NOT:**
- [ ] Delete plugin command or skill files without explicit confirmation
- [ ] Delete git history or .git directory contents
- [ ] Modify plugin.json or marketplace.json during cleanup

---

### S2: Dry-run mode (if supported)

**Invocation:** `/clean-repo --dry-run` (or equivalent preview)

**Must:**
- [ ] Reports what would be cleaned without making changes
- [ ] Output clearly indicates "no changes made"

---

### S3: Cleanup on already-clean repo

**Invocation:** `/clean-repo` (on repo with no stale artifacts)

**Must:**
- [ ] Reports "nothing to clean" or equivalent
- [ ] Does not error or make unnecessary changes

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Preview before changes | Required |
| Confirmation required before destructive actions | Required |
| No deletion of active plugin files | Required |
| Clear post-cleanup summary | Should |
