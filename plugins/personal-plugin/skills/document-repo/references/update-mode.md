# Update mode (`--update`)

Use when Phase 0's `explorer-status` prints `ours` and the code changed after the commit it names. An update re-analyses only the modules whose files changed, rewrites only the doc sections that depend on them, and leaves every existing comment alone.

The inputs are in `$TARGET/explorer/data/`: `state.json` (`source_commit`, the commit the docs describe) and `model.json` (the base model). If either is missing, there is nothing to update from: offer a full run. If Phase 0 says `foreign` after a merge that took `model.json` and `state.json` from different sides, explorer-contract.md says how to recover.

Every command below uses `$TARGET`, `$TOOL_SRC`, `$SKILL_DIR` and `$RUN_DIR` for brevity. Shell variables do not persist between Bash calls, so set each one again at the top of every command, or write the literal paths. Step 1 prints `RUN_DIR`: use that literal path from then on, because the timestamp in it cannot be rebuilt.

## Steps

1. **Start a new run directory.** The skill's Setup does this step. Never reuse an old one. `assemble` prefers a file in the run directory over the base model: a leftover `system.json` would replace the base model's system sections, and a leftover `modules/<id>.json` would replace a module with its old line numbers. The previous model comes from the committed `explorer/data/model.json` (step 8), not from an old run directory. `$TARGET/.document-repo/.gitignore` holds `*`, so a run directory never dirties the tree. Old run directories can stay.

   ```bash
   mkdir -p "$TARGET/.document-repo"
   printf '*\n' > "$TARGET/.document-repo/.gitignore"
   RUN_DIR="$TARGET/.document-repo/run-$(date -u +%Y%m%dT%H%M%SZ)"
   mkdir -p "$RUN_DIR/modules" "$RUN_DIR/comments" "$RUN_DIR/docs"
   echo "$RUN_DIR"
   ```

2. **Preflight as usual.** The tree must be clean. Create the branch `docs/document-repo-update-<YYYYMMDD>`, run step 3 at once, and only then find the commands and record the baseline. `changes` reads only committed state, but it refuses a dirty tree, and a test run can leave artifacts behind.

3. **Find the changes.**

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo changes --repo "$TARGET" > "$RUN_DIR/changes.json"
   ```

   `--repo` must be the top level of the git work tree. `--explorer-dir` defaults to `<repo>/explorer`. Exit 0 prints the report below. Exit 2 means the tool refused to answer; stderr says why.

   | Message contains | Meaning and action |
   |------------------|--------------------|
   | `is not in this repository's history` | `source_commit` was rebased or squashed away. Tell the user and offer a full run. |
   | `no source_commit`, `not a full commit hash`, a missing `state.json` or `model.json` | The state cannot drive an update. Offer a full run. |
   | `working tree is not clean` | Commit or stash, then run again. |
   | `repo must be the top level` | Pass the directory from `git rev-parse --show-toplevel`. |
   | `assume-unchanged`, `skip-worktree`, or `differs from HEAD although git status reports a clean tree` | Git is hiding edits to a file. The message gives the git command that clears it. Run it, then run `changes` again. |

   | Report key | Meaning |
   |------------|---------|
   | `since`, `head` | The two full commit hashes compared |
   | `changed_files` | `{status, path}` per changed file, using git's status letter and, for a rename, the new path. It leaves out comment-only edits, Markdown files and the explorer output (the files a build writes, in an explorer a build made: see commit-protocol.md). |
   | `comment_only_files` | Files edited in comments only, proven by the verifier. They are not changes. |
   | `removed_files` | Deleted paths |
   | `affected_modules` | Every module that owns a changed path. Modules that share a path are all listed. A rename lists the module it left and the one it entered. |
   | `unmapped_files` | Added or modified files that no module path claims, a rename by its new path. This includes a modified file in a directory the model never covered. The root module (path `.`) claims top-level files only. |

4. **If `affected_modules` and `unmapped_files` are both empty and `removed_files` is empty**, no module needs analysis. If `comment_only_files` is non-empty, people edited comments by hand, so line numbers moved: do steps 5 and 8 with no module records and no `system.json` (`files` is not needed in step 5), then the gate in step 9, then step 12. Nothing is written before the gate approves. Otherwise tell the user the docs are current and stop.

5. **Write `$RUN_DIR/modules.final.json`** from the base model's `modules[]`: one `{"id", "path", "files"}` entry each, with the same `id` and `path`. Set `files` to the non-skipped files in a fresh inventory that the module owns by longest path prefix. Use the inventory from preflight (Phase 0), and run `modules` on it as in a full run.

   - **New modules.** Group `unmapped_files` by directory. Take a new module for each group from the fresh `modules` proposal, or widen an existing module's `path` when the files belong to it. Check each new `id` against the existing ids and add `-2`, `-3` until it is free.
   - **Dropped modules.** Drop a module only when all its files are in `removed_files`.

6. **Re-analyse** every module in `affected_modules` and every new module, with the module analyst prompt, writing `$RUN_DIR/modules/<id>.json`. A module without a record is not re-analysed: `assemble` takes it from the base model. If an analyst for an affected module fails twice, `assemble` keeps the old base-model record for it, not a `not_analyzed` stub (a new module with no record does become a stub). Report that module as "documented from the previous run" at the gate and in the run report.

7. **Decide on synthesis.** Run the synthesizer again only when an affected module's `interface` or `dependencies` differ from the base model's, or a module was added or removed. Give it the base model and tell it to keep what is still true. Its `system.json` replaces all six system sections as a whole; `assemble` does not merge. Skip synthesis otherwise. With no `system.json` in the run directory, `assemble` reuses the base model's sections.

   A dropped module that components, glossary terms or `dependencies.internal` still name fails validation in step 8. That is a signal to run synthesis.

8. **Move the base model's line numbers to HEAD, then assemble with it.** Human comment-only edits may have shifted them.

   ```bash
   cp "$TARGET/explorer/data/model.json" "$RUN_DIR/base-model.json"
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/base-model.json" --repo "$TARGET" --to HEAD
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo assemble --run-dir "$RUN_DIR" --repo "$TARGET" --base-model "$RUN_DIR/base-model.json"
   ```

   `remap` rewrites its model in place and prints `{"warnings": [...]}`. Put the warnings in the report. A warning that names a file in an affected module means a flow step points at code that changed beyond added lines, so its numbers are approximate. Treat that as a reason to run synthesis. `remap` exits 2 on an invalid base model, for example one with another `schema_version`; offer a full run. `assemble` exits 1 and lists validation errors, as in a full run. Fix the module records or `system.json`, then run it again.

9. **Gate.** The plan lists only the affected and new modules, the files to comment, the doc sections to rewrite, and any module documented from the previous run. Ask for approval before any write.

10. **Comments** (Phase 2). Comment the files in `changed_files` whose status is not `D` and that belong to an affected or new module, plus every file of a new module. Skip `comment_only_files`. Give each commenter `since` from `changes.json`, so it comments only items that are new or whose code changed. Existing comments are never touched. Verify, test and commit per module through the commit protocol (`references/commit-protocol.md`), and run the branch backstop, as in a full run. After the backstop, remap `$RUN_DIR/model.json` to HEAD, as in a full run.

11. **Docs** (Phase 3). Write these sections and no others:

    | Section | Rewrite when |
    |---------|--------------|
    | `module` in an affected or new module's README | always |
    | `repo-map` in the root README | a module was added or removed, or a re-analysed module's purpose changed |
    | `agents` in `AGENTS.md` | synthesis ran, a module was added or removed, or a re-analysed module's purpose or entry points changed |
    | `overview`, `quick-start` and `explorer` in the root README; `architecture`; `glossary` | synthesis ran |

    Writing a section whose text did not change produces no git diff, so an uncertain case costs nothing. A removed module leaves its README behind, because the tool cannot delete a section. List it in the report as stale.

12. **Explorer** (Phase 4). Remap the assembled model to HEAD, then build. After step 10 only Markdown has changed, so no line moves; when step 10 was skipped, this remap is the one that counts:

    ```bash
    PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/model.json" --repo "$TARGET" --to HEAD
    PYTHONPATH="$TOOL_SRC" python3 -m document_repo build --model "$RUN_DIR/model.json" --explorer-dir "$TARGET/explorer" --template "$SKILL_DIR/templates/explorer"
    ```

    `build` writes a new `state.json` whose `source_commit` is that commit, so the next update starts from here. Then run the no-network check, commit `explorer/` through the commit protocol, and finish as in a full run, final backstop included.
