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
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, SendMessage, AskUserQuestion, Bash, mcp__claude-in-chrome
---

# document-repo

Comment, document, and build an explorer for a target repo. The design is in
`docs/plans/2026-11-22-document-repo-design.md` in the marketplace repo.

**Prime rule: never change behaviour.** Every source edit is an insertion of
comment lines. The verifier proves it immediately before each commit and again
on the commit itself, and the branch as a whole is checked against its base
before Phase 3 and before Finish. No unverified source change may stay on the
branch.

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
[ -n "$TARGET" ] || { echo "<path> is not inside a git repository"; exit 1; }
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
| `{id}`, `{path}`, `{files}` | One entry of `$RUN_DIR/modules.final.json`. For a Commenter, `{files}` drops skipped JS/TS files (Phase 0 step 6) and, in an update run, files that update-mode.md step 10 leaves out. |
| `{all_module_ids}` | Every `id` in `modules.final.json` |
| `{entry_candidates_in_module}` | The `entry_candidates` in `$RUN_DIR/inventory.json` whose `path` is in `{files}`, as `path (why)`. A manifest hint (`package.json`, `pyproject.toml`) belongs to no module, so also give a module each hint whose target, the path after `->` in `why` resolved from the manifest's directory, is in `{files}`. Give a hint whose target is no file (an npm script command) to the module with path `.`, if there is one. "none" when nothing matches. |
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
2. The skill writes its explorer to `explorer/` and never judges its own files there, so check who owns that directory: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo explorer-status --repo "$TARGET"`. It prints `{"explorer", "foreign_files", "ignored", "ignored_by", "tracked", "incomplete", "kept_local"}`. `absent` (no `explorer/`, or one `build` may write into: empty, or only unchanged template files) and `ours` (a build made it, judged by the content of `data/state.json`, not its name) go on. On `foreign`, or any exit other than 0, stop. Ask with AskUserQuestion: **Stop** (recommended: move the listed files, or the whole `explorer/`, aside, then run again) or **Check again** (rerun this step after the user moved them). Never go on while it says `foreign`. `build` refuses that directory too. `ignored` lists the explorer files a `.gitignore` rule would keep out of a commit (the app, and `explorer/data/model.json`, `model.js`, `state.json` and `run-report.md`), whether or not they exist yet, and `ignored_by` names each rule as `file:line:pattern`. Both are empty when no rule matches. Git skips an ignored file without a word, so `document_repo commit` refuses (exit 2) to commit `explorer/` while one would be left out. `tracked` lists the build's files HEAD already holds. `incomplete` lists the ones it lacks when it holds some, except the run report: an explorer committed without its data opens empty on a fresh clone, and `--update` cannot run. Read `tracked` and `incomplete` only for `ours` and `absent`: for `foreign` they go by file name. `kept_local` is null, or `{"rules", "gone"}` when an earlier run kept the explorer local (Phase 4 step 7): `rules` are the owner's rules that run recorded, `gone` the ones no longer found in their files. If `ignored` is not empty and `kept_local` is null, carry `ignored` and `ignored_by` to the Gate. If `kept_local` is not null, carry its `rules` as the owner's choice and do not ask again. If every rule is in `gone`, say that `explorer/.gitignore` is now the only thing keeping the explorer local. Carry `tracked` and `incomplete` to the Gate and to Phase 4.
3. If step 2 printed `ours` and neither `--update` nor `--phase` was given, ask with AskUserQuestion: **Update** (recommended, only changed modules) or **Full rebuild**. Update switches to update mode.
4. Record the base: `git -C "$TARGET" rev-parse HEAD > "$RUN_DIR/base.txt"`.
5. Branch: `git -C "$TARGET" switch -c docs/document-repo`. In update mode use `docs/document-repo-update-$(date +%Y%m%d)`. If the branch exists, stop and ask. In update mode, run update-mode.md step 3 (`changes`) now, before the baseline: it refuses a dirty tree, and a test run can leave artifacts.
6. Inventory, used by every later phase (Phase 3 reads its `entry_candidates`):

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo inventory "$TARGET" --out "$RUN_DIR/inventory.json"
   ```

   If `summary.by_lang` has `javascript` or `typescript` and Phase 2 will run, check the TypeScript printer: `PYTHONPATH="$TOOL_SRC" python3 -c "import sys; from pathlib import Path; from document_repo.verify import typescript_available as t; print(t(Path(sys.argv[1])))" "$TARGET"`. Only that printer can verify JS/TS edits. On `False`, ask with AskUserQuestion: **Install TypeScript** (recommended: `npm install -g typescript`, then check again) or **Skip JS/TS files** (they get no comments and are listed in the report).
7. Find the verification commands. Skip steps 7 and 8 with `--phase docs` or `--phase explorer`: no source file changes. Look in package.json `scripts` (test, lint, typecheck or type-check), pyproject.toml, pytest.ini and tox.ini (pytest), Makefile targets (test, lint), and CI workflow files. Leave out any command that writes files: `--fix`, `--write`, `format` or `fmt`, `-u`, `--update-snapshot`, `--snapshot-update`. Use the check-only form when there is one (`ruff check` without `--fix`, `prettier --check`). Write `$RUN_DIR/commands.json` as `{"test": [...], "lint": [...], "typecheck": [...]}`.
8. Baseline: run each command with a 10-minute timeout, with the command fingerprint in `$SKILL_DIR/references/commit-protocol.md` taken before and after. Record its exit code, duration and last 40 lines in `$RUN_DIR/baseline.json`. Never install dependencies without asking. A command that cannot run is recorded as `not_runnable`. Failing or not-runnable commands do not block the run. They go in the gate summary and the report. After each command, `git -C "$TARGET" status --porcelain -uall` must print nothing. If it lists files, follow the fingerprint rules: delete new artifacts, and drop a command that changed a tracked file.

## Phase 1 — Analyze

With `--phase docs` or `--phase explorer`, skip this phase. Copy the committed
model instead: `cp "$TARGET/explorer/data/model.json" "$RUN_DIR/model.json"`.
If that file does not exist, stop and offer a full run. `--phase comments`
runs this phase in full, because commenters need fresh module records.

1. Proposal: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo modules "$RUN_DIR/inventory.json" --out "$RUN_DIR/modules.json"`
2. Review the proposal. Merge a module with fewer than 3 files into a sibling or parent with a related job. Split a module with more than 150 files or 20,000 lines by the next path segment. Write the result to `$RUN_DIR/modules.final.json`, in the same shape. Every non-skipped file must belong to exactly one module. Ids match `^[a-z0-9]+(-[a-z0-9]+)*$`.
3. Dispatch one **Module analyst** per module (prompt 1), up to 6 at a time. If an analyst fails or writes invalid JSON, retry it once. After a second failure, leave its record absent. `assemble` then makes a `not_analyzed` stub.
4. Dispatch one **Synthesizer** (prompt 2).
5. Assemble and validate: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo assemble --run-dir "$RUN_DIR" --repo "$TARGET"`. On exit 1, fix the listed errors in the module records or `system.json`, then run it again. Exit 2 means a record has the wrong shape or names an unknown module id, and stderr says which: fix that record, or delete it so it becomes a `not_analyzed` stub, then run it again. Repeat until it exits 0. Never build from a model that failed.

## Gate — owner approval

Show a short summary:

- The purpose (2 sentences), the module list (id, path, file count, status), and the flow titles.
- **Write plan:** the files that will get comments (count, plus the header-only count), the READMEs to create or update, the root doc files, whether `CLAUDE.md` gets a pointer, and the explorer views.
- Baseline failures, `not_analyzed` modules, skipped JS/TS files, and skipped files by reason (counts).
- When `ignored` is not empty, one line: the rule (`file:line:pattern` from `ignored_by`) and what it keeps out of git, for example "`.gitignore:30:data/` keeps `explorer/data/` out of git, so the explorer cannot be committed whole".
- When `incomplete` is not empty, one line: "the committed explorer is incomplete", naming what HEAD lacks (its data files, or only files the template gained since) and the rule behind it, if any. If `ignored` is empty, say that this run's commit adds the missing files.

Then ask with AskUserQuestion. The options are **Approve and write**
(recommended), **Change the plan** (take notes, adjust, and ask again), and
**Stop**. On Stop, run `git -C "$TARGET" switch -` and
`git -C "$TARGET" branch -D <branch>`. Nothing was written. Do not write to
the target before approval.

When `ignored` is not empty and Phase 4 will run (not with `--phase comments` or
`--phase docs`), put a second question in the same call, with two options.
Overriding an ignore rule is the owner's decision (it may be a privacy guard),
so never force-add the files and never edit the owner's `.gitignore`:

- **Keep the explorer local** (recommended): build and check it, but do not commit `explorer/`. Phase 4 steps 6 and 7 say how. `--update` then works only on this machine. When `tracked` is not empty, HEAD keeps the explorer files it already holds, updated, and stays without the data: say so.
- **Stop so I can change .gitignore**: print the exact negation lines to add, then stop as for **Stop**. For a rule that ignores a directory (its pattern ends in `/`), the line is `!` plus the directory that holds the ignored files, placed after that rule in that file: `!explorer/data/` after `data/`. For a rule that names files (`*.js`), one `!<path>` line per ignored file. A negation has no effect while a parent directory is itself ignored.

**Stop** on the first question overrides this one.

## Phase 2 — Comments

Skip this phase when `--phase` is `docs` or `explorer`.

Read `$SKILL_DIR/references/commit-protocol.md` first. Every commit in this
phase, and in Phases 3 and 4, goes through `document_repo commit` as it
describes, and its result table says what to do with each outcome.

**Stray rules.** A stray is a path in `git -C "$TARGET" status --porcelain -uall`
that the current step does not own. For a tracked stray, run
`git -C "$TARGET" checkout HEAD -- <path>`. Delete an untracked stray. Record
each one with its cause: an agent, a command (the fingerprint names it), or a
commit hook. The tree was clean at preflight, so the run made every stray.

Work in batches of up to 4 modules with status `analyzed`. Modules own
disjoint files, so parallel Commenters (prompt 3) never touch the same file.
Skip a module whose `{files}` list is empty. Dispatch the whole batch, wait
for every agent, then:

1. **Clean up.** Empty the index with `git -C "$TARGET" restore --staged -- .`, because agents must not stage. Apply the stray rules to every listed path that is not in the `{files}` of a batch module.
2. **Verify each module.** A module's list is the files in its `{files}` that differ from HEAD: `git -C "$TARGET" diff --name-only HEAD -- <its files>`. Do not use `--changed` here, because the other modules' edits are in the tree too.

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo "$TARGET" --before HEAD <file> <file> ...
   ```

   For every result with `"ok": false`, restore the file with `git -C "$TARGET" checkout HEAD -- <path>`, take it out of the list, and record it with its `detail`. A module with an empty list has nothing to commit.
3. **Snapshot the batch** as "Batch snapshot" in commit-protocol.md describes: one patch for the batch and one per module in `$RUN_DIR/hold/`.
4. **Test the batch.** Run each command in `commands.json` that passed at baseline in under 5 minutes, with the fingerprint before and after. If the command wrote to the tree, follow the fingerprint rules. A regression is a command that passed at baseline and fails now. On a regression:
   1. Run the command once more. If it passes, it is flaky: record it and go on.
   2. Take the batch's modules out one at a time, and re-run after each. commit-protocol.md says how to take a module out and put it back. When the failure is gone, the last module taken out caused it. Put the others back one at a time, re-running after each, and keep out any whose return brings the failure back. A module kept out stays restored from HEAD and is recorded.
   3. If the failure remains with every module out, the tree equals HEAD and the batch did not cause it. Record the command as unstable, put every module back, and do not run that command for later batches.
5. **Commit each surviving module separately.** The paths are its list from step 2, each quoted:

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo commit --repo "$TARGET" --verify-against HEAD -m "docs(<module id>): add explanatory comments" -m "Comment-only change, verified by document-repo verify." -- <path> <path> ...
   ```

   Act on the `status` it prints as the commit-protocol table says. Exit 2 is a fill error: fix the command line, never drop the check.
6. **Check that the batch is done.** `git -C "$TARGET" status --porcelain -uall` must print nothing. Apply the stray rules to anything it lists.

Never `git add -A` in the target, and never make a commit outside `document_repo commit`.

A command that passed at baseline in 5 minutes or more runs once, after the
last batch, with the fingerprint. On a regression, run it once more, as in
step 4. Then find the cause in the work tree, as in step 4: take a module out
with `git -C "$TARGET" checkout <base sha> -- <its files>`, and put it back
with `git -C "$TARGET" checkout HEAD -- <its files>`. For each module that
caused it, check its files out of the base and commit them with
`--verify-against <base sha>` (the literal sha from `$RUN_DIR/base.txt`) and
`-m 'revert(<module id>): remove comments that broke <command>'`. If the
failure remains with every module out, record the command as unstable and put
every module back. If this command writes to the tree, the fingerprint rules
for a run after the last batch apply: check out HEAD and clean, because no
batch snapshot is left to restore.

**Branch backstop.** Run "Branch backstop" in commit-protocol.md
(`PYTHONPATH="$TOOL_SRC" python3 -m document_repo backstop --repo "$TARGET" --base <base sha>`).
It must exit 0 before anything else happens.

After the backstop, move the model's line numbers to the commented code:

```bash
PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/model.json" --repo "$TARGET" --to HEAD
```

It prints `{"warnings": [...]}`. Put every warning in the report. Exit 2
means the model is invalid or its `source_commit` is not in history. The model
was assembled in this run, so either one is a bug: stop and report stderr.

## Phase 3 — Docs

Skip this phase when `--phase` is `comments` or `explorer`. Follow
`$SKILL_DIR/references/doc-templates.md` for every body.

1. **Fold in the traps the commenters found.** Phase 1 wrote `agent_notes.traps` before any commenter read a file, and a `Traps:` line a commenter wrote in a file header reaches no doc on its own. Harvest them before writing any body. In a full run, Phase 2 ran in this run, so ask for what the branch added:

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo traps --repo "$TARGET" --before "$(cat "$RUN_DIR/base.txt")" --out "$RUN_DIR/traps.json"
   ```

   In a `--phase docs` or `--update` run, leave `--before` out (`... traps --repo "$TARGET" --out "$RUN_DIR/traps.json"`): it then lists every `Traps:` comment in the tracked files, the owner's included. A `--phase docs` run has no Phase 2 of its own, because its commenters ran in an earlier run whose base is not known, so `--before` would list nothing. An update run's base model can lack traps an earlier run never folded in. In both, the merge rule below drops what the model already holds. The file holds `[{"path", "line", "text"}]` sorted by path and line; a text longer than 2000 characters is cut and ends in ` ...`, so read the file at `path:line` before you copy a trap that ends so. Exit 2 is a bad repo or ref and stderr says which: stop and report. A file over the size limit is not read: stderr names each one (path and size), so put them in the report. The list holds candidates, not proven traps: Python and JavaScript/TypeScript are read with a tokenizer, but in other languages, without `--before`, a `Traps:` line inside a shell heredoc or a multi-line string can pass for a comment, so drop an entry that is not a real trap as you pick. Pick the traps that matter beyond their own file: how to build, run, test or deploy, a config default that changes a bare command, behaviour across modules, and data loss or a wrong result that looks safe. A trap that matters only to someone editing that file stays in its header. Add at most 12 to `agent_notes.traps` in `$RUN_DIR/model.json`, each written as "Notes on `agent_notes.traps`" in model-schema.md says and naming its file as `path:line`. When one describes what an existing trap already does, merge them and keep the fuller consequence. Edit `model.json` itself and never run `assemble` again, because it would rebuild the file from the records and drop the edit. Then check it: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo build --model "$RUN_DIR/model.json" --explorer-dir "$TARGET/explorer" --validate-only` (it writes nothing). On exit 1, fix the listed errors and run it again until it exits 0. A `--phase docs` run does not run Phase 4, so the traps it folds in reach `AGENTS.md` but not the committed `explorer/data/model.json`. `--phase explorer` copies that committed model and would lose them: run `--update` (when it finds changes to make) or a full run to carry them into the explorer.
2. **Root files.** Write each section body for the root `README.md` (`overview`, `quick-start`, `repo-map`, `explorer`), `AGENTS.md` (`agents`), `docs/ARCHITECTURE.md` (`architecture`) and `docs/GLOSSARY.md` (`glossary`). Use `$RUN_DIR/model.json` and the `entry_candidates` in `$RUN_DIR/inventory.json`. Save each body as `$RUN_DIR/docs/_<file>-<section>.md`; the underscore keeps it apart from module ids. Then write it:

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo upsert-section --file "$TARGET/README.md" --section overview --content-file "$RUN_DIR/docs/_readme-overview.md"
   ```

   Exit 2 prints the reason on stderr. Fix the body and run it again. If the reason is an unclosed fence in the existing file, leave that file alone and report it.
3. **Module READMEs.** Dispatch **Module docs writers** (prompt 4) in batches of up to 6 module ids.
4. **CLAUDE.md.** Only if it already exists and does not resolve to the same file as `AGENTS.md`, upsert section `agents-pointer`. Never create `CLAUDE.md`.
5. Confirm that no source file changed: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo "$TARGET" --before HEAD --changed` must print `[]`. Apply the stray rules to every path it lists, then run it again until it prints `[]`.
6. Commit the doc files: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo commit --repo "$TARGET" --no-content-check -m "docs: add READMEs, AGENTS.md, architecture and glossary" -- README.md AGENTS.md docs/ARCHITECTURE.md docs/GLOSSARY.md <module READMEs>`. List each module README that was written and `CLAUDE.md` only if it was written: a path that does not exist exits 2. Then `git -C "$TARGET" status --porcelain -uall` must print nothing. A path it lists is a stray, for example a Markdown file an agent made.

## Phase 4 — Explorer

Skip this phase when `--phase` is `comments` or `docs`.

1. Remap to HEAD again: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/model.json" --repo "$TARGET" --to HEAD`. After Phase 2 only Markdown changed, so no line moves. It matters with `--phase explorer`: the copied model points at an older commit, and comment-only edits since then move lines exactly. A warning there means code changed in other ways. Report it and suggest `--update`. Exit 2 means the model is invalid or its `source_commit` is not in history: stop and offer a full run.
2. Build: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo build --model "$RUN_DIR/model.json" --explorer-dir "$TARGET/explorer" --template "$SKILL_DIR/templates/explorer"`. Exit 1 lists validation errors. With `--phase explorer`, the committed model fails today's schema, so offer a full run. Otherwise it is a bug: stop and report. Exit 2 means the model or template could not be read or written, or `explorer/` holds what a build does not write: report stderr and stop. If stderr says the explorer "looks like a build that stopped partway" (an earlier `build` in this run exited 2 or was interrupted), run the `git clean` the message gives with `git -C "$TARGET"` (`-fdqx` when `explorer/` is kept local: its files are ignored, and a plain clean skips them), then `git -C "$TARGET" checkout HEAD -- explorer` if HEAD has an `explorer/` (a first run's does not), and build once more. Any other refusal names files that are not the build's: stop and report.
3. No-network check: `grep -rIlE "https?://" "$TARGET/explorer" --exclude-dir=vendor --exclude=model.json --exclude=model.js` must print nothing. The model files are left out because they hold text from the repo. The page's Content-Security-Policy blocks every request they could name.
4. **Browser check.** The Chrome extension refuses `file://` pages, so serve the explorer on the loopback address only. Start this with Bash `run_in_background: true`. It prints the port and stops by itself after 10 minutes:

   ```bash
   python3 -c 'import functools,http.server,sys,threading; s=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=sys.argv[1])); print(s.server_address[1],flush=True); threading.Timer(600,s.shutdown).start(); s.serve_forever()' "$TARGET/explorer"
   ```

   Read the port from the task's output file. Load the claude-in-chrome tools with one ToolSearch call. Open `http://127.0.0.1:<port>/index.html` in a new tab and run the acceptance list in `$SKILL_DIR/references/explorer-contract.md`. Close the tab. If the tools are missing or fail twice, tell the user to open `explorer/index.html` and record "browser check not run" with the reason.
5. **Comprehension check.** Dispatch the **Examiner** (prompt 5). Write `$RUN_DIR/quiz-questions.json` from `quiz.json` as `[{"q": str}]`, the same questions in the same order. Dispatch a fresh **Student** (prompt 6). Then send the **Grader** prompt (7) to the Examiner with SendMessage, or to a fresh agent if that fails. The score is the count of correct answers, 0 to 10. The target is 9. If it is lower, list the missed topics in the report as doc gaps. Do not loop.
6. Write `$TARGET/explorer/data/run-report.md`: counts (files commented, reverted, READMEs), reverted files with reasons, modules kept out for test regressions, suspect existing comments (from `$RUN_DIR/comments/*.json`), skipped JS/TS files, files `traps` named as over the size limit, `not_analyzed` modules, baseline versus after-run results, commands dropped because they write files or marked unstable, strays and their causes, commits the commit protocol undid and the hook choice, the Phase 2 backstop result, remap warnings, the browser check result (passed, failed with what, or not run and why), and the quiz score with missed topics. When the explorer is kept local, add the line `explorer kept local: <file:line:pattern>` with each rule from `ignored_by` (from `kept_local.rules` in a later run), and, when `incomplete` is not empty, the line `committed explorer incomplete: HEAD holds <tracked> but not <incomplete>, so a fresh clone opens it empty`.
7. Commit the explorer: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo commit --repo "$TARGET" --no-content-check -m "docs: add interactive project explorer" -- explorer`. Skip that command when the explorer is kept local (the owner chose it at the gate, or `kept_local` is not null) and do this instead:
   1. When `tracked` is not empty, HEAD already holds some explorer files, and the build rewrote them. Commit them so the tree stays clean: the same command with `-m "docs: update the committed explorer app"` and `--` followed by every path in `tracked`, not `explorer`. A directory holding ignored files exits 2, and the command skips the paths that did not change (`skip` is fine). Act on the status as the commit protocol says.
   2. `PYTHONPATH="$TOOL_SRC" python3 -m document_repo keep-local --repo "$TARGET"`. It writes `$TARGET/explorer/.gitignore`, a self-ignoring file like the one Setup writes in `.document-repo/`, and records the owner's rules in it. It prints `{"written", "rules"}`; `written` false means an earlier run did it. Without that file the app's files sit untracked, the final backstop exits 1 on them, and the stray rules would delete the explorer. It is not the owner's `.gitignore` and overrides no rule of theirs: it keeps what is not tracked out of git on this machine only. Exit 2 names the reason (a different `explorer/.gitignore` is in the way, or no rule ignores the explorer): stop and show the user.
   3. `git -C "$TARGET" status --porcelain -uall` must print nothing.

When Phase 4 is skipped, write the same report to `$RUN_DIR/run-report.md`
and leave it uncommitted.

## Finish

Run "Branch backstop" in commit-protocol.md one last time. It must exit 0
before you tell the user anything else.

Tell the user:

- The branch name and the commit list: `git -C "$TARGET" log --oneline "$(cat "$RUN_DIR/base.txt")"..HEAD`.
- The report path and its headline numbers, and that the final backstop passed.
- How to view the result: open `explorer/index.html`.
- After `--phase comments`, the committed explorer still holds the previous analysis and its old line numbers. The fresh analysis from this run is in `$RUN_DIR/model.json` and nothing uses it. Suggest `--phase explorer`, which moves the committed model's line numbers to the new code exactly because the new commits are comment-only, or a full run to publish the fresh analysis.
- After `--phase docs`, `AGENTS.md` holds the traps folded in this run and the committed explorer does not (Phase 3 step 1 says how to carry them).
- When the explorer was kept local: that its data is in no commit, so a fresh clone has no data and `--update` works only on this machine, and the rule that caused it. When `tracked` was not empty, say that HEAD holds the app files without the data, so a fresh clone opens an empty page. To publish it, the owner adds the negation lines from the gate to `.gitignore` and deletes `explorer/.gitignore`. Then `document_repo commit --no-content-check ... -- explorer` makes the commit, as in Phase 4 step 7.
- That nothing was pushed. Suggest `git push -u origin <branch>` and a PR.

Never push, open a PR, or merge on your own initiative.
