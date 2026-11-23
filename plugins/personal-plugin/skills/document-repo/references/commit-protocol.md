# Commit protocol

Every commit the skill makes in the target goes through the block below: each Phase 2 module commit, each restore commit, the Phase 3 docs commit and the Phase 4 explorer commit. The block exists because three things can put an unverified change into a commit after the verifier said yes:

- a command in `commands.json` rewrites files between the verify and the commit (`eslint --fix`, `ruff --fix`, `prettier --write`, a snapshot update);
- another file is already in the index, and a bare `git commit` takes the whole index;
- a pre-commit hook (husky with lint-staged, pre-commit with black or end-of-file-fixer) rewrites and re-stages files at commit time. A hook can add files to the commit even under `git commit --only`.

The block closes all three. It empties the index, verifies the files immediately before staging, commits only the named paths, and then checks the commit it made: exactly one new commit, no other path in it, the work tree equal to it, and every source file comment-only against its parent. A failed check undoes the commit before the block returns.

## The block

Run it as one Bash call. Fill in the literal paths and the file list. Shell state does not persist between calls, which is why the whole check sits in one call.

```bash
bash -s <<'COMMIT'
cd "<TARGET>" || exit 2
TOOL_SRC="<TOOL_SRC>"
FILES=(<path> <path>)          # paths relative to TARGET; a directory is allowed
MSG="<subject>"
BODY="<body>"
VERIFY_REF="HEAD"              # HEAD for a comment commit, the base sha for a restore commit, "" for docs and explorer/
HOOKS=""                       # "--no-verify" only after the user chose it
verify() { PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo . --before "$1" -- "${FILES[@]}"; }
git restore --staged -- . 2>/dev/null || git reset -q
KEEP=(); for f in "${FILES[@]}"; do if [ -e "$f" ]; then KEEP+=("$f"); else echo "NOTE: $f does not exist, left out"; fi; done
[ ${#KEEP[@]} -gt 0 ] || { echo "SKIP: no files"; exit 0; }
FILES=("${KEEP[@]}")
if git diff --quiet HEAD -- "${FILES[@]}" && [ -z "$(git ls-files --others --exclude-standard -- "${FILES[@]}")" ]; then echo "SKIP: nothing to commit"; exit 0; fi
if [ -n "$VERIFY_REF" ]; then
  REF="$(git rev-parse --verify "$VERIFY_REF^{commit}")" || exit 2
  verify "$REF" >/dev/null || { verify "$REF"; echo "PRECHECK: restore each ok:false file above, take it out of FILES, run again"; exit 1; }
fi
PRE="$(git rev-parse HEAD)"
git add -- "${FILES[@]}" || exit 2
if ! git commit -q --only $HOOKS -m "$MSG" -m "$BODY" -- "${FILES[@]}"; then
  git restore --staged -- .
  [ "$(git rev-parse HEAD)" = "$PRE" ] || { echo "STOP: HEAD moved although the commit failed"; exit 5; }
  echo "HOOK: the commit was refused and nothing was committed"; exit 3
fi
undo() {
  git reset -q --soft "$PRE" && git restore --staged -- .
  [ -z "$VERIFY_REF" ] || git restore --source=HEAD --worktree -- "${FILES[@]}"
  echo "UNDONE: $1"; exit 4
}
[ "$(git rev-parse HEAD~1)" = "$PRE" ] || { echo "STOP: more than one new commit"; exit 5; }
EXCL=(); for f in "${FILES[@]}"; do EXCL+=(":(exclude,literal)$f"); done
EXTRA="$(git diff-tree -r --no-commit-id --name-only --no-renames HEAD -- . "${EXCL[@]}")"
[ -z "$EXTRA" ] || undo "the commit also held $(echo $EXTRA)"
git diff --quiet HEAD -- "${FILES[@]}" || undo "the work tree differs from the commit (a hook changed files)"
if [ -n "$VERIFY_REF" ]; then verify "$REF" >/dev/null || { verify "$REF"; undo "the committed files are not comment-only against $REF"; }; fi
echo "OK $(git rev-parse --short HEAD)"
COMMIT
```

`VERIFY_REF` is `HEAD` for a Phase 2 comment commit, so the files are verified against the commit they are about to sit on. It is the base sha (`$RUN_DIR/base.txt`) for a restore commit, whose files must equal the base. It is empty for Markdown and `explorer/`, which the verifier does not judge. Those commits still get every other check.

## What each result means

| Output (exit) | Meaning | Action |
|---------------|---------|--------|
| `OK <sha>` (0) | Committed and proven | Go on |
| `SKIP` (0) | No file exists, or none differs from HEAD | Record the module as "nothing to commit". No commit is made. |
| `PRECHECK` (1) | A file changed after the batch verify, for example by a command | Restore each listed file with `git -C "$TARGET" checkout HEAD -- <path>`, record it with its `detail`, take it out of `FILES` and run the block again |
| `HOOK` (3) | A hook refused the commit. Nothing was committed, the index is empty | See "Hooks" below |
| `UNDONE` (4) | The commit failed a check and was taken back. With `VERIFY_REF` set, the files were also restored from HEAD | Record the module as reverted with the printed reason. Treat any extra path it names as a stray (SKILL.md). See "Hooks" below. |
| `STOP` (5) | History moved in a way the block did not cause | Stop the run and show the user `git -C "$TARGET" log --oneline -5` |
| any other non-zero | A git or tool error | Read it, fix the cause, run again |

## Why the undo is `reset --soft`

The bad commit is HEAD and its parent is `PRE`, which the block checked. `git reset --soft "$PRE"` moves only the branch pointer. The index and the work tree keep every byte. `git restore --staged -- .` then empties the index, and with `VERIFY_REF` set, `git restore --source=HEAD --worktree` resets only the committed files to the parent. Nothing outside `FILES` is touched.

- `git reset --hard HEAD~1` would also wipe the uncommitted edits of every other module in the batch, and every file a stray rule has not yet looked at.
- `git revert` keeps the unverified commit in history, makes a second commit that hooks can rewrite too, and needs its own verification.

The same reasoning replaces `git revert` everywhere in this skill. To take back a commit that is no longer HEAD, check its files out of the base (`git -C "$TARGET" checkout <base sha> -- <files>`) and run the block with `VERIFY_REF` set to the base sha. That makes a new commit whose files equal the base, and the block proves it.

## Hooks

The block runs the target's hooks by default, because they are the owner's rules. The post-commit checks catch any hook that rewrites a file. A hook that only formats Python code can pass, because the Python check compares syntax trees. A hook that changes a string, strips trailing whitespace inside one, or reformats a language checked line by line fails.

After the second module that ends in `HOOK` or in `UNDONE` caused by a hook, ask the user once with AskUserQuestion:

- **Skip hooks for document-repo commits** (recommended when the hook only formats). The block then runs with `HOOKS="--no-verify"`, and the commit holds exactly the verified bytes. Every post-commit check still runs.
- **Keep the hooks.** Every module the hook rewrites is reverted and reported.

Never pass `--no-verify` without that answer. Record the choice in the report.

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
- **A tracked file changed:** the command rewrites files. Take it out of `commands.json` and record it. In Phase 0, run `git -C "$TARGET" checkout HEAD -- .` and `git -C "$TARGET" clean -fdq`. In Phase 2, restore the batch snapshot.

## Branch backstop

The per-commit checks cover each commit. The backstop covers the branch as a whole, the restore commits included:

```bash
PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo "$TARGET" --before "$(cat "$RUN_DIR/base.txt")" --changed
git -C "$TARGET" status --porcelain -uall
```

`verify` must exit 0, with `"ok": true` for every entry. `status` must print nothing. For a file that fails `verify`, check it out of the base and run the block with `VERIFY_REF` set to the base sha. A failing path that is not in the base was added on the branch: stop and show the user. Handle anything `status` lists with the stray rules in SKILL.md. Then run the backstop again until it passes.
