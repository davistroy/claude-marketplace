---
name: document-repo
description: >
  Document an entire repository for junior developers and AI agents — adds
  explanatory comments to the source (each file proven comment-only by a
  verifier, failures reverted), writes READMEs at module boundaries plus
  AGENTS.md, docs/ARCHITECTURE.md and docs/GLOSSARY.md, and builds an offline
  interactive explorer web app in explorer/, all generated from one project
  model. One approval gate after analysis; work happens on a new branch with
  one commit per module. Supports --update for incremental refresh and
  --phase to re-run comments, docs or explorer alone.
argument-hint: "[path] [--update] [--phase comments|docs|explorer]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion, Bash
---

# document-repo

Comment, document, and build an explorer for a target repo. The design is in
`docs/plans/2026-11-22-document-repo-design.md` in the marketplace repo.

**Prime rule: never change behaviour.** Every source edit is an insertion of
comment lines. The verifier proves it before each commit.

## Setup

Parse the arguments first. The path argument defaults to the current
directory. Flags are `--update` and `--phase comments|docs|explorer`. Do not
combine `--phase` with `--update`. If both are given, ask which one to run.

Run this once. Put the real path argument in place of `<path>`:

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(find ~ -path '*/plugins/personal-plugin' -type d 2>/dev/null | head -1)}"
TOOL_SRC="$PLUGIN_DIR/tools/document-repo/src"
SKILL_DIR="$PLUGIN_DIR/skills/document-repo"
TARGET="$(git -C "<path>" rev-parse --show-toplevel)"
test -d "$TOOL_SRC/document_repo" || { echo "document_repo tool not found under $PLUGIN_DIR"; exit 1; }
mkdir -p "$TARGET/.document-repo"
printf '*\n' > "$TARGET/.document-repo/.gitignore"
RUN_DIR="$TARGET/.document-repo/run-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN_DIR/modules" "$RUN_DIR/comments" "$RUN_DIR/docs"
PYTHONPATH="$TOOL_SRC" python3 -m document_repo --version
printf 'TARGET=%s\nTOOL_SRC=%s\nSKILL_DIR=%s\nRUN_DIR=%s\n' "$TARGET" "$TOOL_SRC" "$SKILL_DIR" "$RUN_DIR"
```

Shell state does not persist between Bash calls, and the timestamp in
`RUN_DIR` cannot be rebuilt. So copy the four printed paths, and write them
as literal paths in every later command and every agent prompt. This file
writes `$TARGET` and the like for brevity only.

If the version command fails, stop and report: Python 3.10+ is required.
`.document-repo/.gitignore` holds `*`, so no run directory is ever tracked or
dirties the tree. Each run gets a new directory. Never reuse an old one. It
is not under `.git/` because agents may not write there.

With `--update`, `$SKILL_DIR/references/update-mode.md` drives the run. Setup
above is its step 1. Follow its steps where they differ from the phases below.

## Agent dispatch

The prompts are in `$SKILL_DIR/references/agent-prompts.md`. Prepend the
preamble, fill every placeholder, and pass the prompt to the Agent tool
(`general-purpose`). Fill the placeholders as follows:

| Placeholder | Fill with |
|-------------|-----------|
| `{TARGET}`, `{RUN_DIR}`, `{TOOL_SRC}`, `{SKILL_DIR}` | The literal paths Setup printed |
| `{id}`, `{path}`, `{files}` | One entry of `$RUN_DIR/modules.final.json`. For a Commenter, `{files}` drops skipped JS/TS files (Phase 0 step 5) and, in an update run, files that update-mode.md step 10 leaves out. |
| `{all_module_ids}` | Every `id` in `modules.final.json` |
| `{entry_candidates_in_module}` | The `entry_candidates` in `$RUN_DIR/inventory.json` whose `path` is in `{files}`, as `path (why)` |
| `{header_only_files}` | The files in `{files}` whose inventory entry has `header_only` true, or "none" |
| `{ids}` | One batch of module ids (Phase 3) |
| `{UPDATE_LINE}` | Empty in a full run. In an update run, the line printed under that prompt in agent-prompts.md, with its own placeholders filled. |
| `{SINCE}` | `since` from `$RUN_DIR/changes.json` (update runs only) |
| `{BASE_MODEL}` | `$RUN_DIR/base-model.json` (update runs only) |
| `{affected_modules}` | `affected_modules` from `changes.json`, plus any new module id (update runs only) |

Before dispatch, check that no `{` placeholder is left in the prompt text,
except the JSON shapes the prompt itself shows.

## Phase 0 — Preflight

1. `git -C "$TARGET" status --porcelain` must print nothing. Otherwise stop and tell the user to commit or stash.
2. If `explorer/data/state.json` exists and neither `--update` nor `--phase` was given, ask with AskUserQuestion: **Update** (recommended, only changed modules) or **Full rebuild**. Update switches to update mode.
3. Record the base: `git -C "$TARGET" rev-parse HEAD > "$RUN_DIR/base.txt"`.
4. Branch: `git -C "$TARGET" switch -c docs/document-repo`. In update mode use `docs/document-repo-update-$(date +%Y%m%d)`. If the branch exists, stop and ask.
5. Inventory, used by every later phase (Phase 3 reads its `entry_candidates`):

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo inventory "$TARGET" --out "$RUN_DIR/inventory.json"
   ```

   If `summary.by_lang` has `javascript` or `typescript` and Phase 2 will run, check the TypeScript printer: `PYTHONPATH="$TOOL_SRC" python3 -c "from pathlib import Path; from document_repo.verify import typescript_available as t; print(t(Path('$TARGET')))"`. Only that printer can verify JS/TS edits. On `False`, ask with AskUserQuestion: **Install TypeScript** (recommended: `npm install -g typescript`, then check again) or **Skip JS/TS files** (they get no comments and are listed in the report).
6. Find the verification commands. Look in package.json `scripts` (test, lint, typecheck or type-check), pyproject.toml, pytest.ini and tox.ini (pytest), Makefile targets (test, lint), and CI workflow files. Write `$RUN_DIR/commands.json` as `{"test": [...], "lint": [...], "typecheck": [...]}`.
7. Baseline: run each command with a 10-minute timeout. Record its exit code, duration and last 40 lines in `$RUN_DIR/baseline.json`. Never install dependencies without asking. A command that cannot run is recorded as `not_runnable`. Failing or not-runnable commands do not block the run. They go in the gate summary and the report.

## Phase 1 — Analyze

With `--phase docs` or `--phase explorer`, skip this phase. Copy the committed
model instead: `cp "$TARGET/explorer/data/model.json" "$RUN_DIR/model.json"`.
If that file does not exist, stop and offer a full run. `--phase comments`
runs this phase in full, because commenters need fresh module records.

1. Proposal: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo modules "$RUN_DIR/inventory.json" --out "$RUN_DIR/modules.json"`
2. Review the proposal. Merge a module with fewer than 3 files into a sibling or parent with a related job. Split a module with more than 150 files or 20,000 lines by the next path segment. Write the result to `$RUN_DIR/modules.final.json`, in the same shape. Every non-skipped file must belong to exactly one module. Ids match `^[a-z0-9]+(-[a-z0-9]+)*$`.
3. Dispatch one **Module analyst** per module (prompt 1), up to 6 at a time. If an analyst fails or writes invalid JSON, retry it once. After a second failure, leave its record absent. `assemble` then makes a `not_analyzed` stub.
4. Dispatch one **Synthesizer** (prompt 2).
5. Assemble and validate: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo assemble --run-dir "$RUN_DIR" --repo "$TARGET"`. On exit 1, fix the listed errors in the module records or `system.json`, then run it again. Repeat until it exits 0. Never build from a model that failed.

## Gate — owner approval

Show a short summary:

- The purpose (2 sentences), the module list (id, path, file count, status), and the flow titles.
- **Write plan:** the files that will get comments (count, plus the header-only count), the READMEs to create or update, the root doc files, whether `CLAUDE.md` gets a pointer, and the explorer views.
- Baseline failures, `not_analyzed` modules, skipped JS/TS files, and skipped files by reason (counts).

Then ask with AskUserQuestion. The options are **Approve and write**
(recommended), **Change the plan** (take notes, adjust, and ask again), and
**Stop**. On Stop, run `git -C "$TARGET" switch -` and
`git -C "$TARGET" branch -D <branch>`. Nothing was written. Do not write to
the target before approval.

## Phase 2 — Comments

Skip this phase when `--phase` is `docs` or `explorer`.

Work in batches of up to 4 modules with status `analyzed`. Modules own
disjoint files, so parallel Commenters (prompt 3) never touch the same file.
Skip a module whose `{files}` list is empty. Dispatch the whole batch, wait
for every agent, then:

1. **Verify each module** with an explicit file list. Do not use `--changed` here: the other modules' edits are in the tree too.

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo "$TARGET" --before HEAD <file> <file> ...
   ```

   For every result with `"ok": false`, restore the file with `git -C "$TARGET" checkout HEAD -- <path>` and record it with its `detail`.
2. **Test the batch.** Run each command in `commands.json` that passed at baseline in under 5 minutes. A regression is a command that passed at baseline and fails now. On a regression, take the batch's modules out one at a time, and re-test after each. To take a module out, copy its changed files to `$RUN_DIR/hold/<id>/` and restore them from HEAD. When the regression is gone, the last module taken out caused it. Put the others back one at a time, re-testing after each, and keep out any whose return brings the failure back. Record every module kept out.
3. **Commit each surviving module separately,** naming its files:

   ```bash
   git -C "$TARGET" add -- <file> <file> ...
   git -C "$TARGET" commit -m "docs(<module id>): add explanatory comments" -m "Comment-only change, verified by document-repo verify."
   ```

4. **Check for stray edits.** `PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo "$TARGET" --before HEAD --changed` must print `[]`. Restore any tracked file it lists from HEAD. Delete any untracked file it lists: the tree was clean at preflight, so an agent made it. Record both.

Never `git add -A` in the target.

A command that passed at baseline in 5 minutes or more runs once, after the
last batch. On a regression there, revert module commits one at a time with
`git -C "$TARGET" revert --no-edit <sha>`, newest first, until it passes.

After the last commit, move the model's line numbers to the commented code:

```bash
PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/model.json" --repo "$TARGET" --to HEAD
```

It prints `{"warnings": [...]}`. Put every warning in the report.

## Phase 3 — Docs

Skip this phase when `--phase` is `comments` or `explorer`. Follow
`$SKILL_DIR/references/doc-templates.md` for every body.

1. **Root files.** Write each section body for the root `README.md` (`overview`, `quick-start`, `repo-map`, `explorer`), `AGENTS.md` (`agents`), `docs/ARCHITECTURE.md` (`architecture`) and `docs/GLOSSARY.md` (`glossary`). Use `$RUN_DIR/model.json` and the `entry_candidates` in `$RUN_DIR/inventory.json`. Save each body as `$RUN_DIR/docs/_<file>-<section>.md`; the underscore keeps it apart from module ids. Then write it:

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo upsert-section --file "$TARGET/README.md" --section overview --content-file "$RUN_DIR/docs/_readme-overview.md"
   ```

   Exit 2 prints the reason on stderr. Fix the body and run it again. If the reason is an unclosed fence in the existing file, leave that file alone and report it.
2. **Module READMEs.** Dispatch **Module docs writers** (prompt 4) in batches of up to 6 module ids.
3. **CLAUDE.md.** Only if it already exists and does not resolve to the same file as `AGENTS.md`, upsert section `agents-pointer`. Never create `CLAUDE.md`.
4. Confirm that no source file changed: `verify --repo "$TARGET" --before HEAD --changed` must print `[]`.
5. Commit the doc files by name, never with `-A`: `git -C "$TARGET" add -- README.md AGENTS.md docs/ARCHITECTURE.md docs/GLOSSARY.md <each module README> [CLAUDE.md]`, then `git -C "$TARGET" commit -m "docs: add READMEs, AGENTS.md, architecture and glossary"`.

## Phase 4 — Explorer

Skip this phase when `--phase` is `comments` or `docs`.

1. Remap to HEAD again: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/model.json" --repo "$TARGET" --to HEAD`. After Phase 2 only Markdown changed, so no line moves. It matters with `--phase explorer`: the copied model points at an older commit, and comment-only edits since then move lines exactly. A warning there means code changed in other ways. Report it and suggest `--update`. Exit 2 means the model is invalid or its `source_commit` is not in history: stop and offer a full run.
2. Build: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo build --model "$RUN_DIR/model.json" --explorer-dir "$TARGET/explorer" --template "$SKILL_DIR/templates/explorer"`
3. No-network check: `grep -rIlE "https?://" "$TARGET/explorer" --exclude-dir=vendor --exclude=model.json --exclude=model.js` must print nothing. The model files are left out because they hold text from the repo. The page's Content-Security-Policy blocks every request they could name.
4. If the claude-in-chrome tools are available, open `file://$TARGET/explorer/index.html` and run the acceptance list in `$SKILL_DIR/references/explorer-contract.md`: 0 console errors, every view renders, every diagram draws, only `file://` requests. Otherwise tell the user to open it.
5. **Comprehension check.** Dispatch the **Examiner** (prompt 5). Write `$RUN_DIR/quiz-questions.json` from `quiz.json` as `[{"q": str}]`, the same questions in the same order. Dispatch a fresh **Student** (prompt 6). Then send the **Grader** prompt (7) to the Examiner with SendMessage, or to a fresh agent if that fails. The score is the count of correct answers, 0 to 10. The target is 9. If it is lower, list the missed topics in the report as doc gaps. Do not loop.
6. Write `$TARGET/explorer/data/run-report.md`: counts (files commented, reverted, READMEs), reverted files with reasons, modules kept out for test regressions, suspect existing comments (from `$RUN_DIR/comments/*.json`), skipped JS/TS files, `not_analyzed` modules, baseline versus after-run results, remap warnings, and the quiz score with missed topics.
7. Commit the explorer: `git -C "$TARGET" add -- explorer && git -C "$TARGET" commit -m "docs: add interactive project explorer"`.

When Phase 4 is skipped, write the same report to `$RUN_DIR/run-report.md`
and leave it uncommitted.

## Finish

Tell the user:

- The branch name and the commit list: `git -C "$TARGET" log --oneline "$(cat "$RUN_DIR/base.txt")"..HEAD`.
- The report path and its headline numbers.
- How to view the result: open `explorer/index.html`.
- After `--phase comments`, the committed explorer still has the old line numbers. Suggest `--phase explorer`.
- That nothing was pushed. Suggest `git push -u origin <branch>` and a PR.

Never push, open a PR, or merge on your own initiative.
