# Commit protocol

Every commit the skill makes in the target goes through `document_repo commit`: each Phase 2 module commit, each restore commit, the Phase 3 docs commit and the Phase 4 explorer commit. Three things can put an unverified change into a commit after the verifier said yes:

- a command in `commands.json` rewrites files between the verify and the commit (`eslint --fix`, `ruff --fix`, `prettier --write`, a snapshot update);
- another file is already in the index, and a bare `git commit` takes the whole index;
- a pre-commit hook (husky with lint-staged, pre-commit with black or end-of-file-fixer) rewrites and re-stages files at commit time. A hook can add files to the commit even under `git commit --only`.

`document_repo commit` closes all three. It empties the index, stages the listed paths, verifies them, commits only those paths, and then checks the commit it made: exactly one new commit on the old HEAD, no other path in it, the work tree equal to it, and every committed source file comment-only against the ref. A failed check undoes the commit before the command returns. It replaced a hand-filled shell block (decision D76), which skipped verification when a variable expanded to empty, committed in the wrong repo after `cd ""`, and ran backticks in the message.

## The command

```bash
PYTHONPATH="$TOOL_SRC" python3 -m document_repo commit --repo "$TARGET" --verify-against HEAD \
  -m "docs(<module id>): add explanatory comments" \
  -m "Comment-only change, verified by document-repo verify." \
  -- <path> <path> ...
```

- `--repo` is the literal target path Setup printed. It must be the top level of the work tree. An empty value is refused.
- Exactly one of `--verify-against REF` and `--no-content-check` is required. There is no default and no empty form.
  - `--verify-against HEAD` for a Phase 2 comment commit: the files are verified against the commit they are about to sit on.
  - `--verify-against <base sha>` for a restore commit, whose files must equal the base. Paste the sha from `$RUN_DIR/base.txt` as a literal.
  - `--no-content-check` for Markdown and `explorer/`, which the verifier does not judge. Those commits still get every other check.
- `-m` is the subject. A second `-m` adds the body. Each message is one argv element, so quotes, backticks and `$` in it are text. Write it in single quotes when it holds a backtick or `$`.
- After `--`, list the paths relative to the target, each quoted when it holds a space. A directory (`explorer`) commits everything under it. List only paths that exist, or that HEAD has and the work tree deleted. A path that is neither is a fill error, and the command exits 2 without touching anything.
- `--skip-hooks` passes `--no-verify` to git. Add it only after the user chose it (see "Hooks").

The command prints JSON: `{"status", "detail", "sha", "paths", "verify", "restored", "strays", "git_output"}`. `paths` are the paths the commit holds (or would have held). `verify` lists the failing verifier results. `restored` lists the listed paths it reset in the work tree. `strays` lists paths outside the list that changed in the work tree while the commit ran, which only a hook can do.

## What each result means

| `status` (exit) | Meaning | Action |
|-----------------|---------|--------|
| `ok` (0) | Committed and proven | Go on. Apply the stray rules (SKILL.md) to every path in `strays`, recording "commit hook" as the cause. |
| `skip` (0) | Nothing under the listed paths differs from HEAD | Record the module as "nothing to commit". No commit was made. |
| `precheck` (1) | A listed file is not comment-only against the ref, for example because a command changed it after the batch verify. Nothing was committed and the index is empty. The work tree is untouched. | Restore each file in `verify` with `git -C "$TARGET" checkout HEAD -- <path>`, record it with its `detail`, take it out of the list and run the command again |
| `commit-failed` (1) | `git commit` itself failed. Nothing was committed and the index is empty. Any listed file that changed during the attempt (a hook that fixes, then exits 1) was reset to the bytes that were staged and is in `restored`. `detail` names the cause: the commit hooks that ran, or a signing failure. | A hook: see "Hooks". A signing failure (`commit.gpgsign` with a missing key or a pinentry that cannot prompt): stop and tell the user, because skipping hooks does not help. Anything else: show `git_output` to the user. Apply the stray rules to `strays`. |
| `undone` (1) | The commit failed a post-commit check and was taken back with `git reset --soft`. With `--verify-against`, the listed paths were reset to the old HEAD, so the module's change is gone. With `--no-content-check`, they were reset to the bytes that were staged, so the docs survive and only a hook's change is gone. | Record the module as reverted with `detail`. Apply the stray rules to `strays` and to any extra path `detail` names. See "Hooks". |
| `stop` (1) | History moved in a way the command did not cause (a hook made its own commit), or an undo could not restore a listed path | Stop the run and show the user `detail` and `git -C "$TARGET" log --oneline -5` |
| (2) | Bad input: the repo is not a top level, a path is missing or outside it, the ref does not resolve, the message is empty. Nothing was touched. stderr says which. | Fix the command line and run it again. Never fix it by switching to `--no-content-check`. |

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

Never pass `--skip-hooks` without that answer. Record the choice in the report. A module that ended in `commit-failed` keeps its verified edits in the work tree, so after the user chooses to skip hooks, run its command again with `--skip-hooks`. A module that ended in `undone` with `--verify-against` was reset to HEAD; record it as reverted.

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

It verifies every path that differs from the base (Markdown and `explorer/` excepted) and lists `git status --porcelain -uall`. It prints `{"ok", "base", "verify", "status"}`.

- Exit 0: `ok` is true. Every entry in `verify` passed and `status` is empty.
- Exit 1: a file in `verify` has `"ok": false`, or `status` lists paths. For a failing file that the base has, check it out of the base and commit it with `--verify-against <base sha>` and `-m "revert(<module id>): <reason>"`. A failing file that the base does not have was added on the branch: stop and show the user. Handle anything `status` lists with the stray rules in SKILL.md. Then run the backstop again until it exits 0.
- Exit 2: the base is empty, does not resolve, or is not an ancestor of HEAD, or the repo is not a top level. stderr says which. Fix the command line. Never skip the backstop.
