# Maintainer Runbook: Incident & Rollback

This is the maintainer-side counterpart to [TROUBLESHOOTING.md](../TROUBLESHOOTING.md). That guide helps
*users* recover a broken local install (stale cache, disabled plugins, etc.). This runbook is for the
**maintainer** when a bad change has already reached `main` on `davistroy/claude-marketplace` and needs to
be found, reverted, and re-verified under pressure.

Scope: one incident type — **P1: a bad change reached `main`**. If you're debugging a user's local
install problem, use TROUBLESHOOTING.md instead.

---

## P1: A Bad Change Reached `main`

### 1. Detect

Signs that a bad merge shipped:

- **CI red on `main`.** Check the Actions tab or:
  ```bash
  gh run list --branch main --limit 5
  gh run view --log-failed <run-id>
  ```
- **User report of vanished commands / broken discovery** — e.g. `/help` no longer lists a command,
  a skill stops being suggested, or `/plugin install` errors on marketplace.json parse. Treat any
  report of "a command/skill that worked yesterday doesn't today" as a P1 signal, not a one-off support
  ticket.
- **`/validate-plugin --all` fails against `origin/main`** when run locally after a fetch — confirms the
  break is in the shipped tree, not just your working copy.

First action on any of the above: identify the offending merge commit.

```bash
git fetch origin
git log origin/main --oneline -20
gh pr list --state merged --limit 10
```

Find the merge commit SHA (`<merge-sha>`) that introduced the regression — bisect with
`git log -p <good-sha>..origin/main -- <path>` if it isn't obvious which merge is at fault.

### 2. Revert

`main` is branch-protected — **no direct push**, even for the fix. The revert goes through a PR with
green CI, same as any other change.

```bash
git fetch origin
git checkout -b revert/<short-description> origin/main
git revert -m 1 <merge-sha>   # -m 1 only needed if <merge-sha> is itself a merge commit
git push -u origin revert/<short-description>
gh pr create --title "Revert: <short-description>" --body "Reverts <merge-sha> — <one-line reason>. See incident notes in LAB_NOTEBOOK.md."
```

**True-emergency admin fast-path:** the branch protection rule has `enforce_admins=false`, so a repo
admin *can* merge (or push) past a failing/pending check if the situation is severe enough to justify
bypassing review. This is an escape hatch, not the default path — use it only when the normal PR+CI
loop would leave the marketplace broken for an unacceptable period, and log the justification in
LAB_NOTEBOOK.md immediately after.

### 3. Re-verify

Before merging the revert PR:

```bash
gh pr checks <pr-number>          # confirm CI is green on the revert branch
claude plugin validate --strict   # confirm plugin structure is sound locally
```

Do not merge on red CI. If the revert itself fails validation (e.g. it collides with a later, unrelated
commit), resolve conflicts on the revert branch and re-push — don't force through a failing check.

Merge once green:

```bash
gh pr merge <pr-number> --squash   # or --merge, matching repo convention
```

### 4. Propagation — how the fix reaches installs

There is no push mechanism to installed clients. Propagation is pull-based, gated by two things:

- **Install-side `origin/main` tracking** — a user's local marketplace cache tracks the marketplace repo
  at whatever ref it last synced. It does not auto-update on its own.
- **Restart-gating** — even after an update is pulled, new skill/command definitions only take effect
  in the *next* Claude Code session, not the currently running one.

The fix reaches a given install only when the user (or you, for your own machines) runs:

```
/plugin marketplace update
# or, scoped to one plugin:
/plugin update <plugin-name>@troys-plugins
```

...followed by a restart of Claude Code.

**Target RTO:**
- Detect → fixed-on-`main`: **~30 minutes** (from first CI-red or user report to revert PR merged).
- Field propagation: **next user session where they run `/plugin marketplace update` or
  `/plugin update <plugin>@troys-plugins`**, then restart. This is not instantaneous — there is no
  forced-push notification, so treat "fixed on main" and "fixed in the field" as two different
  milestones, and communicate the second one explicitly to affected users if the outage was visible.

### 5. User escape hatch

A consumer who hit the break can freeze on a known-good commit while the fix lands on `main`, without
waiting on you:

- **Defer the update** — simplest option: just don't run `/plugin marketplace update` /
  `/plugin update <plugin>@troys-plugins` until the fix is confirmed merged. Nothing to undo.
- **Pin to a known-good SHA** — if they already updated into the bad state, point their local
  marketplace checkout at the last-good commit instead of `origin/main` HEAD:
  ```bash
  cd ~/.claude/plugins/cache/troys-plugins   # or wherever their marketplace clone lives
  git fetch origin
  git checkout <last-good-sha>
  ```
  Then restart Claude Code. Re-run `/plugin marketplace update` once the revert has merged to move
  back onto `origin/main` HEAD.

---

## After the Incident

Log the incident in `LAB_NOTEBOOK.md` per this repo's mandatory logging protocol (objective, root
cause, the revert commit, and any Decision Log / Action Items updates) before considering the incident
closed. This runbook does not replace that log — it's the procedure; the notebook is the record.
