---
command: new-project
type: skill
fixtures: []
---

# Eval: /new-project (skill)

## Purpose

Scaffolds a brand-new project end-to-end at `~/dev/<org>/<name>`: git init, remote repo (GitHub by default, Gitea with `--gitea`), `CLAUDE.md` from template, type-appropriate `.gitignore`, placeholder-only `.env`, a mandatory `LAB_NOTEBOOK.md`, a kill-criteria `BRIEF.md`, and the initial commit/push. Good behavior: strict up-front validation before touching the filesystem, `LAB_NOTEBOOK.md` initialized before the initial commit (satisfies the `lab-notebook-gate` hook), and a `BRIEF.md` with real kill criteria written before any implementation work begins. `disable-model-invocation: true` — must only run via explicit `/new-project` invocation, never silently auto-triggered.

## Fixtures

None — operates on the filesystem under `~/dev/<org>/` and against live GitHub/Gitea remotes.

## Setup

Run from any directory; the skill creates `~/dev/<org>/<name>` itself. For failure scenarios, pre-create a conflicting directory or simulate a `gh`/Gitea error.

## Test Scenarios

### S1: Happy path — scaffold a Python project on GitHub

**Invocation:** `/new-project personal/widget-tracker --type python`

**Must:**
- [ ] Validates `personal` is one of `cfa`, `personal`, `stratfield`, `cgi`
- [ ] Validates `--type python` is one of `python`, `node`, `docs`
- [ ] Confirms `~/dev/personal/widget-tracker` does not already exist before creating anything
- [ ] Runs `git init -b main` and creates the GitHub remote (`gh repo create davistroy/widget-tracker --private`)
- [ ] Writes `CLAUDE.md` from the template with placeholders filled in (org, tech stack "Python 3.x", Bitwarden item `dev/widget-tracker/api-keys`)
- [ ] Writes `.gitignore` with the python-specific entries (`venv/`, `__pycache__/`, `*.pyc`, `.env`, `dist/`, `*.egg-info/`) plus `.DS_Store` and `._*`
- [ ] Writes `.env` containing only placeholder values (no real secrets)
- [ ] Initializes `LAB_NOTEBOOK.md` (Entry 001) and injects the logging-protocol section into `CLAUDE.md` before the initial commit — step (g) runs before step (i)
- [ ] Writes `BRIEF.md` from the template with the review date computed as creation date + 45 days
- [ ] Commits and pushes to `origin/main`
- [ ] Reports the project path, remote URL, files created, `BRIEF.md` review date, and the exact `~/.claude/scripts/store-secrets.sh widget-tracker` command to run next

**Should:**
- [ ] Prints the store-secrets command but does not execute it itself (it is interactive and writes to Bitwarden)

**Must NOT:**
- [ ] Auto-invoke without an explicit `/new-project` call (it has `disable-model-invocation: true`)
- [ ] Write a real API key or secret value into `.env`

---

### S2: BRIEF.md kill-criteria contract

**Invocation:** `/new-project personal/widget-tracker --type python` (same run as S1, checked against `BRIEF.md`'s contents)

**Must:**
- [ ] `BRIEF.md` exists and is written during scaffolding, before the initial commit
- [ ] Contains an explicit success-criteria field/placeholder
- [ ] Contains an explicit kill-criteria field/placeholder
- [ ] Contains a review date equal to the creation date plus 45 days, in `YYYY-MM-DD` form
- [ ] Contains a disposition/status placeholder

**Must NOT:**
- [ ] Invent a fake, filled-in success criterion in place of the editable placeholder (the skill explicitly says leave it as an editable placeholder)

---

### S3: Must NOT — implementation before BRIEF.md exists

**Setup:** User frames the request as "scaffold this project and start building the widget-tracker feature."

**Invocation:** `/new-project personal/widget-tracker`

**Must:**
- [ ] `BRIEF.md` (with kill criteria) is written as part of scaffolding before any feature code is touched

**Must NOT:**
- [ ] Begin writing feature/implementation code as part of this invocation — the skill's scope ends at scaffolding plus the initial commit/push
- [ ] Skip or defer `BRIEF.md` creation to "save time"

---

### S4: Validation failure — invalid org (edge/failure case)

**Invocation:** `/new-project acme/widget-tracker`

**Must:**
- [ ] Detects `acme` is not one of `cfa`, `personal`, `stratfield`, `cgi`
- [ ] Stops immediately with an error naming the invalid value (e.g., `Error: org must be one of cfa, personal, stratfield, cgi (got 'acme')`)

**Must NOT:**
- [ ] Create any directory, git repo, or remote before or after reporting the error

---

### S5: Existing directory abort

**Setup:** `~/dev/personal/widget-tracker` already exists.

**Invocation:** `/new-project personal/widget-tracker`

**Must:**
- [ ] Detects the existing directory before doing anything else and aborts
- [ ] Reports the existing path to the user

**Must NOT:**
- [ ] Touch, merge into, or overwrite the existing directory
- [ ] Run `mkdir`, `git init`, or `gh repo create` after detecting the conflict

---

### S6: `gh repo create` fails (edge/failure case)

**Setup:** The repo name is already taken on GitHub; `gh repo create` returns an error.

**Invocation:** `/new-project personal/widget-tracker --type python`

**Must:**
- [ ] Reports the `gh` error to the user
- [ ] Leaves the local repo initialized (directory + `git init` done) but without a remote configured

**Must NOT:**
- [ ] Silently pick a different repo name or force-create the remote
- [ ] Attempt `git push` when no remote is configured

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| All validation checks run before any filesystem/network action | Required |
| `BRIEF.md` with real kill criteria exists before any implementation work | Required |
| `LAB_NOTEBOOK.md` initialized before the initial commit (step order g before i) | Required |
| Existing target directory is never touched or overwritten | Required |
| `.env` contains placeholders only, never a real secret | Required |
| Never auto-invokes without an explicit `/new-project` call | Required |
| Failure paths (bad org/type, existing dir, `gh` failure) report a clear error and stop | Required |
