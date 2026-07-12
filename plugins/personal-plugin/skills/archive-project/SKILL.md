---
name: archive-project
description: Archive, retire, or sunset a project repo — writes a status header into README.md, tags and commits the change, pushes and optionally archives the remote (GitHub only), moves the directory into ~/dev/archive/, and logs one line to ~/dev/PORTFOLIO.md. Suggest when the user says archive project, retire project, sunset repo, mothball this repo, shelve this project, or asks to wind down/decommission a repo that is no longer active.
argument-hint: "<repo-path>"
allowed-tools: Bash, Read, Write, Edit, Glob
disable-model-invocation: true
---

# Archive Project

You are retiring a project: recording why it ended and what was learned, tagging the final state, optionally archiving the remote, and relocating the directory out of active `~/dev/` space into a labeled archive — while keeping a single running index (`~/dev/PORTFOLIO.md`) of what's active, paused, and archived.

This skill is **destructive-adjacent**: it moves a directory on disk and can archive a remote repo (which, on GitHub, makes it read-only). It never deletes git history — everything is preserved via commit, tag, and `mv` — but the actions are not casually reversible mid-session. Confirm before acting.

## Input

**Arguments:** `$ARGUMENTS`

**Required:**
- `<repo-path>` — path to the project directory to archive (e.g. `~/dev/personal/old-experiment`). If omitted, ask the user.

**Optional (ask for these in Phase 0 if not supplied):**
- `--reason "<text>"` — why the project is being archived
- `--lesson "<text>"` — the "what I learned" / "what worked" line
- `--superseded-by "<name-or-path>"` — the project that replaces this one, if any
- `--archive-remote` — if the remote is GitHub and active, archive it after pushing (skipped for local-only or already-archived remotes; irrelevant for non-GitHub remotes)

## Destructive Action Warning

Before touching anything:
- Confirm the exact target directory with the user (typos here move or archive the wrong project)
- Never run this against a path that looks like an active dependency of other projects without asking
- Archiving a GitHub remote makes it **read-only** — pushes will fail afterward. Only do this if the user confirmed archive-remote intent
- If `git status` in the target shows uncommitted changes unrelated to the archival header, ask before proceeding — don't silently fold unrelated work into the archival commit

## Procedure

### Phase 0: Confirm Target

1. Resolve `<repo-path>` to an absolute path. If it doesn't exist or isn't a git repo (no `.git`), stop and report the error.
2. Gather facts and show them to the user before doing anything else:
   ```bash
   REPO="<resolved-absolute-path>"
   cd "$REPO"
   git remote -v
   git log -1 --format='%h %ad %s' --date=short
   git status -s
   ```
3. Display a confirmation summary:
   ```text
   Archive target: <REPO>
   Remote:         <url, or "none (local-only)">
   Last commit:    <date> <hash> <subject>
   Uncommitted:    <"clean" | list of changes>

   This will: write an archival header into README.md, tag and commit,
   [push + offer to archive the remote | skip remote steps — no remote],
   then move the directory to ~/dev/archive/<org>/<name>/.
   Proceed? (y/n)
   ```
4. If the user hasn't already supplied `--reason` / `--lesson` / `--superseded-by`, ask for them now:
   - Reason for archiving (required)
   - What worked / what you learned (required — one or two sentences)
   - Superseded by, if anything (optional)
5. Do not proceed past this point without explicit confirmation.

### Phase 1: Classify the Remote (do this before writing the README header — the header text depends on the outcome)

```bash
cd "$REPO"
REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
```

- **`REMOTE_URL` is empty** → classification = `LOCAL-ONLY`.
- **`REMOTE_URL` contains `github.com`** → parse `owner/repo` from the URL, not from the local directory name (a repo can be cloned into a differently-named folder):
  ```bash
  # SSH form:   git@github.com:owner/repo.git
  # HTTPS form: https://github.com/owner/repo.git  (or .git suffix absent)
  OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's#^git@github\.com:##; s#^https://github\.com/##; s#\.git$##')
  gh repo view "$OWNER_REPO" --json isArchived --jq .isArchived
  ```
  - `true` → classification = `GITHUB-ARCHIVED`
  - `false` → classification = `GITHUB-ACTIVE`
- **`REMOTE_URL` is non-empty but not `github.com`** (e.g. Gitea) → classification = `NON-GITHUB`.

Hold this classification — it drives both the header text (Phase 2) and the push/archive step (Phase 4).

### Phase 2: Build the README Status Header

1. If `README.md` doesn't exist in `$REPO`, create it with a single `# <repo-name>` title line before prepending the header.
2. Prepend (do not replace existing content) a header block:
   ```markdown
   > **ARCHIVED** — <YYYY-MM-DD>
   > **Reason:** <reason from Phase 0>
   > **What I learned:** <lesson from Phase 0>
   > **Superseded by:** <value, or omit this line if none given>
   > <classification note — see below>

   ---

   ```
3. Classification note, appended as the last line of the block, chosen by Phase 1's result:
   - `LOCAL-ONLY` → `> **Note:** no remote — local-only repo, archived in place.`
   - `GITHUB-ARCHIVED` → `> **Note:** tag not pushed (remote already archived).`
   - `GITHUB-ACTIVE` → omit (nothing extra to note yet; Phase 4 will archive the remote if requested)
   - `NON-GITHUB` → `> **Note:** remote is non-GitHub; remote archiving is manual.`

### Phase 3: Tag and Commit

```bash
cd "$REPO"
git add README.md
git commit -m "docs: mark project archived ($(date +%Y-%m))"
git tag "archived-$(date +%Y-%m)"
```

If there were other pre-existing uncommitted changes the user asked to include (Phase 0 step 5), stage and commit those separately first — keep the archival commit focused on the README header.

### Phase 4: Push and Remote Archive (branch on Phase 1's classification)

This is the critical decision point — do not skip or reorder these branches:

| Classification | Action |
|---|---|
| `LOCAL-ONLY` | Skip all push/archive steps entirely. Nothing to do here. |
| `GITHUB-ARCHIVED` | Skip the push (archived GitHub remotes reject pushes). The header already notes "tag not pushed." |
| `GITHUB-ACTIVE` | Push, then offer to archive: |
| `NON-GITHUB` | Push, then note remote archiving is manual. |

**`GITHUB-ACTIVE` and `NON-GITHUB` push:**
```bash
cd "$REPO"
BRANCH=$(git branch --show-current)
git push origin "$BRANCH" --tags
```

**`GITHUB-ACTIVE` only — offer/perform remote archive:**
- If the user passed `--archive-remote` or confirmed archive-remote intent in Phase 0, run:
  ```bash
  gh repo archive "$OWNER_REPO" --yes
  ```
- Otherwise, ask now: "Push succeeded. Archive the GitHub remote too (`$OWNER_REPO`)? This makes it read-only." Only run the command on explicit yes.

**`NON-GITHUB`:** after the push, tell the user remote archiving is manual for this host (no `gh`-equivalent assumed) and give the classification note already written into the header as the record of that.

### Phase 5: Move the Directory

1. Infer `<org>` from the path's parent segment directly under `~/dev/` (e.g. `~/dev/personal/foo` → `personal`, `~/dev/cfa/foo` → `cfa`). If `$REPO` isn't under `~/dev/` in a way that yields a clear org segment, default `<org>` to `personal`.
2. Determine `<name>` as the final path component of `$REPO`.
3. ```bash
   mkdir -p ~/dev/archive/<org>/
   mv "$REPO" ~/dev/archive/<org>/<name>/
   ```
4. Confirm the move succeeded (`test -d ~/dev/archive/<org>/<name>/` and `test ! -e "$REPO"`).

### Phase 6: Update the Portfolio Index

1. If `~/dev/PORTFOLIO.md` doesn't exist, create it with:
   ```markdown
   # Portfolio

   ## Active

   ## Paused

   ## Archived

   ```
2. Append one line under the `## Archived` section (add it directly after the `## Archived` heading, or after the last existing bullet under that section if others exist):
   ```markdown
   - <name> — archived <YYYY-MM>: <reason/lesson> (was ~/dev/<org>/<name>)
   ```
   Use the Phase 0 reason and lesson, condensed to a short clause. Do not touch the `## Active` or `## Paused` sections.

### Phase 7: Report

Display a summary of every artifact touched:
```text
Archive complete: <name>

  Classification:   <LOCAL-ONLY | GITHUB-ACTIVE | GITHUB-ARCHIVED | NON-GITHUB>
  README header:    written (<REPO>/README.md, created new | prepended)
  Tag:              archived-<YYYY-MM>
  Commit:           <sha> "docs: mark project archived (<YYYY-MM>)"
  Push:             <pushed to origin/<branch> | skipped — <reason>>
  Remote archive:   <archived <owner/repo> | not requested | already archived | manual (non-GitHub)>
  Moved to:         ~/dev/archive/<org>/<name>/
  Portfolio:        ~/dev/PORTFOLIO.md updated (Archived section)
```

## Output

In-conversation report only (Phase 7). No generated files beyond the modified `README.md`, the git tag/commit inside the (now moved) repo, and the appended line in `~/dev/PORTFOLIO.md`.

## Example

```
User: /archive-project ~/dev/personal/scratch-arch

Claude: Archive target: /home/user/dev/personal/scratch-arch
        Remote:         none (local-only)
        Last commit:    2026-07-10 a1b2c3d Initial commit
        Uncommitted:    clean

        This will: write an archival header into README.md, tag and commit,
        skip remote steps — no remote, then move the directory to
        ~/dev/archive/personal/scratch-arch/.
        Proceed? (y/n)

User: y — reason: superseded by the new-project skill work; lesson: quick
      scratch repos should live outside ~/dev/personal from the start.

Claude: [writes header, commits, tags, moves directory, updates PORTFOLIO.md]
        Archive complete: scratch-arch
          Classification:   LOCAL-ONLY
          ...
```

## Error Handling

- If `<repo-path>` doesn't exist or has no `.git`: stop, report the error, do not create anything.
- If the user declines to confirm in Phase 0: stop immediately, make no changes.
- If `gh repo view` fails (auth, network, or the parsed `owner/repo` doesn't resolve): treat as `NON-GITHUB`-style caution — report the failure, ask the user how to proceed rather than guessing archived status.
- If `git push` fails for a `GITHUB-ACTIVE`/`NON-GITHUB` repo: stop before offering remote archive, show the git error, and leave the directory in place (do not run Phase 5) until push is resolved or the user says to proceed anyway.
- If `mv` fails (permissions, destination exists): stop, report the exact error, leave the repo at its original path — do not attempt the portfolio update for a move that didn't happen.
- If `~/dev/PORTFOLIO.md` exists but lacks an `## Archived` heading: add the heading (and `## Active`/`## Paused` if also missing) rather than guessing where to insert.
