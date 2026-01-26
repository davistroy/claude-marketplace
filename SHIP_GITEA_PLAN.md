# Plan: Make `/ship` work with both GitHub and Gitea

## Goal
Modify the `ship` skill (and `validate-and-ship`) to auto-detect whether the current repo targets GitHub or Gitea, then use the appropriate CLI (`gh` or `tea`) throughout the workflow.

## Prerequisites
- Install `tea` CLI on the machine
- Configure a `tea` login for `homeserver.tale-mamba.ts.net:3333`

## Files to Modify

1. **`plugins/personal-plugin/skills/ship/SKILL.md`** — primary changes
2. **`plugins/personal-plugin/skills/validate-and-ship/SKILL.md`** — update allowed-tools and tool references

## Changes

### 1. Ship Skill (`ship/SKILL.md`)

**Frontmatter** — add `tea` to allowed-tools:
```yaml
allowed-tools: Bash(git:*), Bash(gh:*), Bash(tea:*)
```

**New section: Platform Detection** (insert after Pre-flight Checks, before Step 1):

Add a "Phase 0: Platform Detection" that runs during pre-flight:
- Parse `git remote -v` for the push remote
- If URL contains `github.com` → set `PLATFORM=github`, verify `gh auth status`
- Otherwise → set `PLATFORM=gitea`, verify `tea login list` shows a matching login
- Store the platform choice for all subsequent steps
- If neither CLI is available for the detected platform, abort with install instructions

**Command substitutions** — throughout the skill, replace hardcoded `gh` commands with platform-conditional equivalents:

| Phase | GitHub (`gh`) | Gitea (`tea`) |
|-------|---------------|---------------|
| Pre-flight auth check | `gh auth status` | `tea login list` (verify matching login exists) |
| Step 5: Create PR | `gh pr create --title "..." --body "..."` | `tea pr create --title "..." --description "..."` |
| Step 5: Draft PR | `gh pr create --draft` | `tea pr create` (no native draft flag — note limitation) |
| Phase 7: Get PR number | `gh pr view --json number -q '.number'` | Parse from `tea pr create` output, or `tea pr list --output json --fields index --state open` |
| Phase 7: Get diff | `gh pr diff $PR_NUMBER` | `tea pr view $PR_NUMBER --fields diff --output simple` |
| Phase 9: Merge | `gh pr merge $PR_NUMBER --squash --delete-branch` | `tea pr merge $PR_NUMBER --style squash` then `git push origin --delete $BRANCH_NAME` (tea merge doesn't auto-delete branch) |
| Phase 9: Return to main | Same for both | Same for both |
| Phase 9: Prune branches | Same for both | Same for both |

**PR URL output** — adjust URL format:
- GitHub: `https://github.com/owner/repo/pull/N`
- Gitea: parsed from `tea pr create` output or constructed from remote URL + `/pulls/N`

**Draft PR limitation** — document that `tea pr create` does not support `--draft`. When `draft` argument is passed on a Gitea repo, warn the user and create a normal PR.

### 2. Validate-and-Ship Skill (`validate-and-ship/SKILL.md`)

**Frontmatter** — add `tea`:
```yaml
allowed-tools: Bash(git:*), Bash(gh:*), Bash(tea:*), Glob, Grep, Read, Edit, Write
```

**Phase 3 references** — update:
- Line 230: "No git/gh CLI available" → "No git/gh/tea CLI available"
- Anywhere that mentions `gh` explicitly, add `or tea (for Gitea)`

## Tea CLI Reference

Key `tea` commands needed (v0.11.1):

```bash
# Authentication
tea login add --url "http://homeserver.tale-mamba.ts.net:3333" --name "homeserver" --token "TOKEN"
tea login list

# Pull requests
tea pr create --title "..." --description "..."
tea pr list --output json --fields index,title,state
tea pr view <N> --fields diff --output simple
tea pr merge <N> --style squash

# Branch cleanup (tea merge doesn't auto-delete)
git push origin --delete <branch-name>
```

Tea auto-detects the Gitea instance by matching `git remote -v` URLs against configured logins.

## Verification

After making changes:
1. From the `contact-center-lab` repo (Gitea remote), run `/ship --dry-run` — should detect Gitea and show `tea` commands
2. From a GitHub-hosted repo, run `/ship --dry-run` — should detect GitHub and show `gh` commands
3. Verify `validate-and-ship` still works by checking its Phase 3 references
