---
name: new-project
effort: low
description: Scaffold a brand-new project directory end-to-end — git init, remote repository (GitHub by default, Gitea with --gitea), CLAUDE.md, .gitignore, placeholder .env, lab notebook, kill-criteria BRIEF.md, and the initial commit/push. Creates a remote repo, so it runs only when invoked explicitly.
argument-hint: "<org>/<name> [--type python|node|docs] [--gitea]"
disable-model-invocation: true
allowed-tools: Bash(mkdir:*), Bash(cd:*), Bash(git:*), Bash(gh:*), Bash(bws:*), Bash(python3:*), Bash(curl:*), Bash(unset:*), Bash(date:*), Bash(echo:*), Read, Write, Edit, Glob
---

# New Project

Scaffold a new project at `~/dev/<org>/<name>` with everything a project needs on day one: an initialized git repo with a remote, a project `CLAUDE.md` seeded from the house template, a type-appropriate `.gitignore`, a placeholder-only `.env`, a mandatory `LAB_NOTEBOOK.md`, a kill-criteria `BRIEF.md`, and an initial commit pushed to the new remote.

This is a side-effect-only skill (`disable-model-invocation: true`) — it never runs proactively. Invoke it explicitly: `/new-project <org>/<name> [--type python|node|docs] [--gitea]`.

## Input

**Arguments:** `$ARGUMENTS`

Expected form: `<org>/<name> [--type python|node|docs] [--gitea]`

- `<org>` — one of `cfa`, `personal`, `stratfield`, `cgi`. Selects the target directory `~/dev/<org>/`.
- `<name>` — kebab-case project name. Becomes the directory name and the GitHub/Gitea repo name.
- `--type python|node|docs` — optional. Selects the `.gitignore` template (Step (d)). Omit for a minimal generic `.gitignore`.
- `--gitea` — optional. Create the remote on the shared Gitea instance instead of GitHub (Step (b)).

### Validation (before doing anything else)

1. Parse `<org>/<name>` from the first argument token. If it doesn't match `org/name` shape, stop and ask for it in that form.
2. `<org>` must be exactly one of `cfa`, `personal`, `stratfield`, `cgi`. If not, stop: `Error: org must be one of cfa, personal, stratfield, cgi (got '<org>')`.
3. If `--type` is given, its value must be exactly one of `python`, `node`, `docs`. If not, stop: `Error: --type must be one of python, node, docs (got '<value>')`.
4. **Abort if `~/dev/<org>/<name>` already exists** — do not touch, merge into, or overwrite an existing directory. Report the existing path and stop.

## Instructions

Execute the steps below in order. Steps (g) and (i) have a real dependency: the lab-notebook init in (g) creates a fresh `LAB_NOTEBOOK.md` entry, which is what satisfies the `lab-notebook-gate` pre-commit hook's "entry within 24h" check for the commit in (i). Do not reorder (i) ahead of (g).

### (a) Local init

```bash
mkdir -p ~/dev/<org>/<name>
cd ~/dev/<org>/<name>
git init -b main
```

Already validated above that the directory doesn't exist — `mkdir -p` here is just for the nested `<org>/` parent, not a license to reuse an existing project directory.

### (b) Remote repository

**Default (GitHub):**

```bash
gh repo create davistroy/<name> --private
git remote add origin https://github.com/davistroy/<name>.git
```

**With `--gitea`:**

1. Retrieve the Gitea API token from Bitwarden Secrets Manager (never echo the token value):

```bash
PROJECT_ID="${BWS_PROJECT_ID:-5022ea9c-e711-4f4e-bf5f-b3df0181a41d}"
GITEA_TOKEN=$(BWS_ACCESS_TOKEN="${BWS_ACCESS_TOKEN:-$TROY}" bws secret list "$PROJECT_ID" | python3 -c "import json,sys; d=json.load(sys.stdin); print(next((s['value'] for s in d if s['key']=='dev/gitea/api-token'), ''))")  # TROY: deprecated fallback name, honored only if BWS_ACCESS_TOKEN is unset

if [ -z "$GITEA_TOKEN" ]; then
  echo "Error: Bitwarden secret 'dev/gitea/api-token' not found. Store it first (see /unlock for the bws pattern)."
  exit 1
fi
```

2. Create the repo via the Gitea API:

```bash
curl -s -X POST "http://gitea.tale-mamba.ts.net:3000/api/v1/user/repos" \
  -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"<name>\", \"private\": true}"
unset GITEA_TOKEN
```

3. Wire up the remote with a **credential-free URL** — auth is supplied transparently by the shared credential store, not embedded in the URL or written anywhere in this repo:

```bash
git config --global credential."http://gitea.tale-mamba.ts.net:3000".helper \
  "store --file=$HOME/.config/git/gitea-credentials"
git remote add origin "http://gitea.tale-mamba.ts.net:3000/davistroy/<name>.git"
```

The `git config --global` call is idempotent (safe to run every time) and only wires the existing shared credential file into git's lookup chain for this one host — it never creates, reads, or prints the stored credential itself.

### (c) CLAUDE.md from template

Read the template from `${CLAUDE_PLUGIN_ROOT}/references/templates/project-claude-md.md` (fall back to `plugins/personal-plugin/references/templates/project-claude-md.md` if `CLAUDE_PLUGIN_ROOT` is unset). The template is read-only source — never modify it in place. Fill placeholders and write the result to `~/dev/<org>/<name>/CLAUDE.md`:

| Placeholder | Value |
|---|---|
| `{{PROJECT_NAME}}` | `<name>` |
| `{{ORG}}` | `<org>` |
| `{{TECH_STACK}}` | `python` → "Python 3.x"; `node` → "Node.js / npm"; `docs` → "Documentation only — no build tooling"; no `--type` → "[Fill in: primary language/framework]" |
| `{{BITWARDEN_ITEM}}` | `dev/<name>/api-keys` |

### (d) .gitignore by --type

Write `~/dev/<org>/<name>/.gitignore`. Every variant always includes `.DS_Store` and `._*` regardless of type.

**`--type python`:**
```
venv/
__pycache__/
*.pyc
.env
dist/
*.egg-info/

.DS_Store
._*
```

**`--type node`:**
```
node_modules/
.env
dist/

.DS_Store
._*
```

**`--type docs`:**
```
.env

.DS_Store
._*
```

**No `--type` given (generic default):**
```
.env

.DS_Store
._*
```

### (e) .env with placeholder values

Write `~/dev/<org>/<name>/.env` with placeholder-only values — never a real key. Use styles like `your-<x>-key` or `get-from-bitwarden`:

```
# Placeholders only. Real secrets: Bitwarden item dev/<name>/api-keys — see CLAUDE.md > Secrets.
API_KEY=your-api-key
ANOTHER_SECRET=get-from-bitwarden
```

**Why this matters mechanically, not just by convention:** a global `PreToolUse` hook (`~/.claude/hooks/env-secrets-guard.sh`) inspects every `Write`/`Edit` targeting a `.env*` file and **denies** the write if the content matches a real-key pattern (`sk-ant-...`, `sk-...`, `AKIA...`, `ghp_...`, `github_pat_...`, `xox[baprs]-...`, `AIza...`, or a PEM private-key header). Placeholders like `your-api-key` and `get-from-bitwarden` don't match any of those patterns and will pass through cleanly. If you ever see this write get denied, it means a real-looking key slipped into the content — stop and remove it, do not retry with `--no-verify`-style bypasses.

### (f) Print the store-secrets command

After scaffolding, print the exact command for the user to run to populate real secrets:

```
~/.claude/scripts/store-secrets.sh <name>
```

Do not run this yourself — it's interactive (prompts for secret name/value pairs) and writes to the user's Bitwarden vault as `dev/<name>/api-keys`, matching `{{BITWARDEN_ITEM}}` from Step (c).

### (g) Initialize the lab notebook

Run `/lab-notebook init` (invoke the `lab-notebook` skill's init behavior) from inside `~/dev/<org>/<name>`. This creates `LAB_NOTEBOOK.md` with Entry 001 and injects the "Lab Notebook — MANDATORY Logging Protocol" section into the `CLAUDE.md` created in Step (c). Because this is a brand-new project, the "Prior Work Summary" will be short — that's expected, not a defect.

This step must run before Step (i)'s commit: the fresh `LAB_NOTEBOOK.md` entry it creates is what the `lab-notebook-gate` pre-commit hook checks for.

### (h) BRIEF.md from template

Read the template from `${CLAUDE_PLUGIN_ROOT}/references/templates/brief.md` (same fallback rule as Step (c)). Fill placeholders and write to `~/dev/<org>/<name>/BRIEF.md`:

| Placeholder | Value |
|---|---|
| `{{PROJECT_NAME}}` | `<name>` |
| `{{CREATED_DATE}}` | Today's date, `YYYY-MM-DD` |
| `{{REVIEW_DATE}}` | Today + 45 days, `YYYY-MM-DD` — compute with `date -d "+45 days" +%Y-%m-%d` (GNU date; use `date -v+45d +%Y-%m-%d` on macOS) |
| `{{SUCCESS_CRITERION_EXAMPLE}}` | Leave as an editable placeholder bullet — do not invent a fake criterion |
| `{{ADDITIONAL_KILL_CRITERION}}` | Leave as an editable placeholder bullet |

### (i) Initial commit and push

```bash
git add -A
git commit -m "chore: scaffold <name>"
git push -u origin main
```

If the `lab-notebook-gate` hook blocks this commit, it means Step (g) did not actually run or did not write a dated entry — go back and complete Step (g), do not bypass with `git commit --no-verify`.

## Output

Report to the user:
- The project path created: `~/dev/<org>/<name>`
- Remote URL and platform (GitHub or Gitea)
- Files created: `CLAUDE.md`, `.gitignore`, `.env`, `LAB_NOTEBOOK.md`, `BRIEF.md`
- The `BRIEF.md` review date
- The exact `~/.claude/scripts/store-secrets.sh <name>` command from Step (f) for the user to run next

## Example

```
User: /new-project personal/widget-tracker --type python

Claude:
(a) Created ~/dev/personal/widget-tracker, git init -b main
(b) Created davistroy/widget-tracker on GitHub (private), remote 'origin' added
(c) CLAUDE.md written from template (org=personal, tech stack=Python 3.x)
(d) .gitignore written (python)
(e) .env written with placeholders only
(g) Lab notebook initialized — LAB_NOTEBOOK.md + CLAUDE.md logging rules
(h) BRIEF.md written — review date 2026-08-26
(i) Committed and pushed to origin/main

Next: run `~/.claude/scripts/store-secrets.sh widget-tracker` to populate real secrets in Bitwarden.
```

## Error Handling

- If `~/dev/<org>/<name>` already exists: abort immediately, report the path, do not modify it.
- If `org` or `--type` fails validation: stop and report the specific invalid value before touching the filesystem.
- If `gh repo create` fails (e.g., name already taken on GitHub): stop, report the `gh` error, leave the local repo initialized but without a remote so the user can resolve the naming conflict and add the remote manually.
- If the Gitea token lookup fails (`dev/gitea/api-token` not found): stop before calling the Gitea API — do not fall back to prompting for a raw token inline.
- If `git push` fails: report the error; do not force-push.
