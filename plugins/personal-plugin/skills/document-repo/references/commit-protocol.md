# Commit protocol

Every commit the skill makes in the target goes through `document_repo commit`: each Phase 2 module commit, each restore commit, the Phase 3 docs commit and the Phase 4 explorer commit. Three things can put an unverified change into a commit after the verifier said yes:

- a command in `commands.json` rewrites files between the verify and the commit (`eslint --fix`, `ruff --fix`, `prettier --write`, a snapshot update);
- another file is already in the index, and a bare `git commit` takes the whole index;
- a pre-commit hook (husky with lint-staged, pre-commit with black or end-of-file-fixer) rewrites and re-stages files at commit time. A hook can add files to the commit even under `git commit --only`.

`document_repo commit` closes all three. It empties the index, stages the listed paths, verifies them, commits only those paths, and then checks the commit it made: exactly one new commit on the old HEAD, no other path in it, the work tree equal to it, and every committed source file comment-only against the ref (with `--no-content-check`, no source file in it at all). A failed check undoes the commit before the command returns. It replaced a hand-filled shell block (decision D76), which skipped verification when a variable expanded to empty, committed in the wrong repo after `cd ""`, and ran backticks in the message.

## The command

```bash
PYTHONPATH="$TOOL_SRC" python3 -m document_repo commit --repo "$TARGET" --verify-against HEAD \
  -m "docs(<module id>): add explanatory comments" \
  -m "Comment-only change, verified by document-repo verify." \
  -- <path> <path> ...
```

Run `commit` and `backstop` with a 10-minute Bash timeout, as Phase 0 does for commands. Both can run the TypeScript verifier (up to 2 minutes per file) and the target's hooks, so the default 2-minute timeout can kill a run after the commit landed.

- `--repo` is the literal target path Setup printed. It must be the top level of the work tree. An empty value is refused.
- Exactly one of `--verify-against REF` and `--no-content-check` is required. There is no default and no empty form.
  - `--verify-against HEAD` for a Phase 2 comment commit: the files are verified against the commit they are about to sit on.
  - `--verify-against <base sha>` for a restore commit, whose files must equal the base. Paste the sha from `$RUN_DIR/base.txt` as a literal. The ref must be HEAD or an ancestor of it; any other commit exits 2.
  - `--no-content-check` for Markdown and the skill's explorer output, which the verifier does not judge. The explorer output is the app's own files as the template installs them (`index.html`, `app.js` and the rest of `templates/explorer/`) plus `explorer/data/model.json`, `model.js` and `state.json`. These count only while the explorer is one a build made: `state.json` has exactly the keys a build writes, and its `model_hash` matches `model.json` (see explorer-contract.md). When a hook changes the model's content or key order, the commit ends `undone` and `detail` says the explorer "no longer reads as one a build made": that is a hook case, so follow "Hooks". A hook that only re-indents the JSON or changes line endings commits fine. Any other file under `explorer/` is the target's and is judged, `explorer/data/` included. The test is by name only, the same one the backstop uses: a symlink named `*.md` counts as Markdown whatever it points at. Its target's content is not changed by the commit, and the backstop exempts it the same way. Any other changed path under the list (a source file, a rename, a submodule) exits 2 before anything is touched, and a commit that ends up holding one is undone. Those commits still get every other check.
- `-m` is the subject. A second `-m` adds the body. Each message is one argv element, so quotes, backticks and `$` in it are text. Write it in single quotes when it holds a backtick or `$`.
- After `--`, list the paths relative to the target, each quoted when it holds a space. A directory (`explorer`) commits everything under it. List only paths that exist, or that HEAD has and the work tree deleted, spelled as git lists them. A path that is neither, one through a symlinked directory, one inside a submodule, one in the wrong case, a directory that holds only ignored files, or a directory that holds some ignored file the commit should carry (see "Ignored files") is a fill error, and the command exits 2 without touching anything.
- `--skip-hooks` passes `--no-verify` to git. Add it only after the user chose it (see "Hooks").

The command prints JSON: `{"status", "detail", "pre", "sha", "paths", "verify", "restored", "strays", "git_output"}`. `pre` is the commit HEAD named before the command ran. `sha` is the commit it made (or found on HEAD). `paths` are the paths the commit holds (or would have held). `verify` lists the failing verifier results. `restored` lists the listed paths it reset in the work tree. `strays` lists paths outside the list that changed in the work tree while the commit ran, which only a hook can do.

## What each result means

| `status` (exit) | Meaning | Action |
|-----------------|---------|--------|
| `ok` (0) | Committed and proven. The index is reset to HEAD afterwards, so a hook that re-staged a file leaves no stale staged bytes; the work tree was already checked to equal the commit. | Go on. Apply the stray rules (SKILL.md) to every path in `strays`, recording "commit hook" as the cause. |
| `skip` (0) | Nothing under the listed paths differs from HEAD | Record the module as "nothing to commit". No commit was made. |
| `precheck` (1) | A listed file is not comment-only against the ref, for example because a command changed it after the batch verify. Nothing was committed and the index is empty. The work tree is untouched. | With `--verify-against HEAD`: restore each file in `verify` with `git -C "$TARGET" checkout HEAD -- <path>`. In a restore commit (`--verify-against <base sha>`), HEAD holds the version being reverted, so check the file out of the base again instead: `git -C "$TARGET" checkout <base sha> -- <path>`, and keep it in the list; if the base lacks the file, stop and show the user. Record the file with its `detail` and run the command again. |
| `commit-failed` (1) | `git commit` itself failed. Nothing was committed and the index is empty. Any listed file that changed during the attempt (a hook that fixes, then exits 1) was reset to the bytes that were staged and is in `restored`. `detail` names the cause: the commit hooks that ran, or a signing failure. | The verified edits are still in the work tree: hold them as "Holding work for a retry" says, before any status check or stray rule runs. A hook: see "Hooks". A signing failure (`commit.gpgsign` with a missing key or a pinentry that cannot prompt): stop and tell the user, because skipping hooks does not help. Anything else: show `git_output` to the user. Apply the stray rules to `strays`. |
| `undone` (1) | The commit failed a post-commit check and was taken back with `git reset --soft`. With `--verify-against`, the listed paths were reset to the old HEAD, so the module's change is gone. With `--no-content-check`, they were reset to the bytes that were staged, so the docs survive and only a hook's change is gone. | With `--verify-against`: record the module as reverted with `detail`. With `--no-content-check`: the docs are still in the tree, uncommitted. Hold them as "Holding work for a retry" says, and see "Hooks". Either way, apply the stray rules to `strays` and to any extra path `detail` names. |
| `stop` (1) | History moved in a way the command did not cause (a hook made its own commit), an undo could not restore a listed path, or anything failed after `git commit` ran (the command tried the undo and `detail` says whether it worked) | Stop the run. Show the user `detail` and `git -C "$TARGET" log --oneline -5`. If HEAD is not `pre`, the commits above `pre` were not verified by this command: the branch must not be pushed, and the user decides whether to run `git -C "$TARGET" reset --soft <pre>`. Never reset on your own. |
| `error` (2) | A git command or the verifier failed before `git commit` ran. Nothing was committed. The index may have been emptied, or may hold the listed paths staged (a precheck crash comes after staging); the next `commit` empties it again. | Stop the run and show the user `detail`. |
| (2, no JSON) | Bad input: the repo is not a top level, a path is missing, outside it or not one git knows, the ref does not resolve or is not an ancestor of HEAD, a source path was listed with `--no-content-check`, a listed directory holds an ignored file the commit would leave out, the message is empty. Nothing was touched. stderr says which. | Fix the command line and run it again. Never fix it by switching to `--no-content-check`. |
| anything else | No JSON with a status from this table: a traceback, an unknown status, an exit code not listed, or the Bash call timed out | Treat it as `stop`: run the branch backstop, and show the user its output, stderr and `git -C "$TARGET" log --oneline -5`. |

## Ignored files

`git add -- <directory>` skips an untracked file an ignore rule matches, and says nothing. With `data/` in a target's `.gitignore`, `explorer/data/model.json`, `model.js` and `state.json` stay out of the commit, which still reported `ok`: the page of a fresh clone was empty and `--update` had no `state.json` to read. So the command looks first. Under each listed directory it finds the untracked files git ignores. If any is a file the commit is expected to carry, it exits 2 before touching anything (the index included) and names each file with the rule that ignores it, as `file:line:pattern`, up to 20 files and then a count.

- **Expected to carry:** Markdown, and the files a build writes in an explorer it made (the app, `vendor/` included, and `data/`). That is the exempt set of `--no-content-check`. A source file is not in it: the inventory never lists an ignored file, so the skill never comments one, and an ignored `local_settings.py` or virtualenv under a module is not lost work.
- **Not refused:** `.DS_Store`, `*.pyc`, swap files, and everything below the listed directory under `node_modules`, `.venv`, `venv`, `dist`, `build`, `__pycache__` and the other directories the inventory skips, Markdown included. The listed directory's own name does not count. A file git tracks is never "ignored" to it, even when a rule matches it.
- **Never override it.** No `git add -f`, no edit to the target's `.gitignore`: a rule may be a privacy guard, and the owner decides. At the Phase 0 gate the owner already chose for the explorer (Keep local, or stop and add the negation lines), so this exit for `explorer` means the gate was skipped or the rule is new: stop and show the user stderr. For a docs directory, ask the user: add the negation line the message names after the ignoring rule (it says which file the line goes in, and re-includes the directory when a directory is what is ignored), or list only the files to commit. The ignored files then stay local, and the run report names them.

## Why the undo is `reset --soft`

The bad commit is HEAD and its parent is the old HEAD, which the command checked. `git reset --soft <old HEAD>` moves only the branch pointer. The index and the work tree keep every byte. The command then empties the index and resets only the listed paths. Edits to other paths stay as they are, so the other modules of the batch keep their uncommitted comments.

- `git reset --hard HEAD~1` would also wipe the uncommitted edits of every other module in the batch, and every file a stray rule has not yet looked at.
- `git revert` keeps the unverified commit in history, makes a second commit that hooks can rewrite too, and needs its own verification.

The same reasoning replaces `git revert` everywhere in this skill. To take back a commit that is no longer HEAD, check its files out of the base (`git -C "$TARGET" checkout <base sha> -- <files>`) and run `document_repo commit` with `--verify-against <base sha>`. That makes a new commit whose files equal the base, and the command proves it. A file the branch deleted comes back the same way: `checkout <base sha>` puts it back in the work tree and the index, and the verifier compares it with the base.

## Hooks

The command runs the target's hooks by default, because they are the owner's rules. The post-commit checks catch any hook that rewrites a file. A hook that only formats Python code can pass, because the Python check compares syntax trees. A hook that changes a string, strips trailing whitespace inside one, or reformats a language checked line by line fails.

After the second module that ends in `commit-failed` caused by a hook, or in `undone` caused by a hook, ask the user once with AskUserQuestion:

- **Skip hooks for document-repo commits** (recommended when the hook only formats). Later commits then run with `--skip-hooks`, and each commit holds exactly the verified bytes. Every post-commit check still runs.
- **Keep the hooks.** Every module the hook rewrites is reverted and reported.

Never pass `--skip-hooks` without that answer. Record the choice in the report. A Phase 3 or Phase 4 commit is that phase's only one, so when it ends in `commit-failed` or `undone` because of a hook, ask at once rather than after a second. A module that ended in `undone` with `--verify-against` was reset to HEAD; record it as reverted.

### Holding work for a retry

`commit-failed`, and `undone` after `--no-content-check`, leave verified work uncommitted in the work tree. Step 6 of Phase 2 and the stray rules would otherwise revert it as a stray. Hold it first:

- **Phase 2 module:** `git -C "$TARGET" diff HEAD --binary -- <its paths> > "$RUN_DIR/hold/<id>.patch"`, then `git -C "$TARGET" checkout HEAD -- <its paths>`. To retry: `git -C "$TARGET" apply "$RUN_DIR/hold/<id>.patch"` and run its command again.
- **Phase 3 or 4 docs:** ask the hook question at once. To skip hooks, run the same command again with `--skip-hooks`; the files are still in place. To keep the hooks, copy the listed files into `$RUN_DIR/uncommitted/` with their paths, run `git -C "$TARGET" checkout HEAD -- <the tracked ones>`, delete the untracked ones, and tell the user where the copies are.

After the user chooses to skip hooks, retry every held module with `--skip-hooks`. After the user chooses to keep the hooks, leave every held module out and record it as reverted, with the hook as the cause.

## Batch snapshot

Before Phase 2 runs any command on a batch, save the batch's edits:

```bash
git -C "$TARGET" diff HEAD --binary > "$RUN_DIR/batch-<n>.patch"
mkdir -p "$RUN_DIR/hold"
git -C "$TARGET" diff HEAD --binary -- <module files> > "$RUN_DIR/hold/<id>.patch"   # once per module
```

To restore the snapshot: `git -C "$TARGET" checkout HEAD -- .`, then `git -C "$TARGET" clean -fdq`, then `git -C "$TARGET" apply "$RUN_DIR/batch-<n>.patch"`. `clean` deletes only untracked files that are not ignored. The tree was clean at preflight and stray files were removed before the snapshot, so those files were made by a command. `.document-repo/` ignores itself, so the run directory survives.

To take one module out: `git -C "$TARGET" checkout HEAD -- <module files>`. To put it back: `git -C "$TARGET" apply "$RUN_DIR/hold/<id>.patch"`.

## Command fingerprint

Take this before and after every command run, in Phase 0 and in Phase 2:

```bash
{ git -C "$TARGET" status --porcelain=v1 -uall; git -C "$TARGET" diff HEAD --binary; } | shasum
```

If the two values differ, the command wrote to the tree. Look at `git -C "$TARGET" status --porcelain -uall`.

- **Only new untracked files** (`.coverage`, `junit.xml`, `coverage/`): delete them with `git -C "$TARGET" clean -fdq`, record them as "created by `<command>`", and keep the command.
- **A tracked file changed:** the command rewrites files. Take it out of `commands.json` and record it. Then put the tree back:
  - In Phase 0, and for a slow command run after the last batch, the tree should equal HEAD: run `git -C "$TARGET" checkout HEAD -- .` and `git -C "$TARGET" clean -fdq`. After the last batch every module is committed, so a batch snapshot no longer applies (`git apply` fails on every file).
  - For a command run on a batch, restore that batch's snapshot as above.

## Branch backstop

The per-commit checks cover each commit. The backstop covers the branch as a whole, the restore commits included. Paste the base sha from `$RUN_DIR/base.txt` as a literal:

```bash
PYTHONPATH="$TOOL_SRC" python3 -m document_repo backstop --repo "$TARGET" --base <base sha>
```

It verifies every path that differs from the base (Markdown and the explorer output excepted, as for `--no-content-check`) and lists `git status --porcelain -uall`. A committed path is judged from the commits themselves (the base blob against the HEAD blob), never from the work tree, so a flag that hides the work tree from `git status` cannot pass a committed change. A path flagged `assume-unchanged` or `skip-worktree`, or whose work-tree bytes are not HEAD's although `git status` is clean, fails; so does a path that differs from the base only in the work tree. It prints `{"ok", "base", "verify", "status"}`.

- Exit 0: `ok` is true. Every entry in `verify` passed and `status` is empty.
- Exit 1: a file in `verify` has `"ok": false`, or `status` lists paths. For a failing file that the base has, check it out of the base and commit it with `--verify-against <base sha>` and `-m "revert(<module id>): <reason>"`. A failing file that the base does not have was added on the branch: stop and show the user. So is a file whose `detail` names `assume-unchanged` or `skip-worktree`, or says it differs from HEAD although git status reports a clean tree: those are the owner's index state, which a revert commit does not clear. Handle anything `status` lists with the stray rules in SKILL.md. Then run the backstop again until it exits 0.
- Exit 2: the base is empty, does not resolve, or is not an ancestor of HEAD, or the repo is not a top level: fix the command line. Or git itself failed (stderr starts `backstop: git`, as in `backstop: git failed while listing…` or `backstop: git status --porcelain=v1 … failed`): stop and show the user stderr. Never skip the backstop.
- Anything else (a traceback, no JSON, a timeout): stop and show the user what it printed.
