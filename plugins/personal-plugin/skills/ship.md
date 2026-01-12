---
allowed-tools: Bash(git:*), Bash(gh:*)
description: Create branch from main, commit all changes, push, and open a PR
---

You are automating the complete git workflow to ship code changes. The user may provide a branch name and description as arguments: $ARGUMENTS

## Pre-flight Checks
1. Verify this is a git repository
2. Check that the GitHub CLI (gh) is installed and authenticated
3. Confirm there are uncommitted changes (staged or unstaged) - if not, abort with a clear message
4. Confirm the current branch is `main` - if not, ask the user if they want to proceed from the current branch or abort

## Execution Steps

### Step 1: Determine Branch Name
- If the user provided a branch name in arguments, use it
- If not, analyze the staged/unstaged changes and generate a descriptive kebab-case branch name (e.g., `fix-login-validation`, `add-user-export-feature`)
- Confirm the branch name with the user before proceeding

### Step 2: Create and Switch to New Branch
```bash
git checkout -b <branch-name>
```

### Step 3: Stage and Commit
- Stage all changes: `git add -A`
- Analyze the diff to generate a clear, conventional commit message
- Format: `<type>: <concise description>` (e.g., `feat: add CSV export for user data`)
- Include a body if changes are complex enough to warrant explanation
- Show the user the proposed commit message and proceed unless they object

### Step 4: Push to Remote
```bash
git push -u origin <branch-name>
```

### Step 5: Create Pull Request
- Use the GitHub CLI to create the PR: `gh pr create`
- Set the PR title to match or expand on the commit message
- Generate a PR body that includes:
  - Summary of what changed and why
  - Key files modified
  - Any testing notes if apparent from the changes
- Target branch: `main`
- Open the PR as a draft if the user included "draft" in their arguments

## Output
After completion, display:
- Branch name created
- Commit SHA
- Direct link to the PR

## Error Handling
- If any git command fails, stop immediately and show the error
- If push fails due to remote rejection, suggest possible causes
- If PR creation fails, provide the manual `gh pr create` command the user can run
