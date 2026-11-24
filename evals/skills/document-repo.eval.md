---
command: document-repo
type: skill
fixtures: []
---

# Eval: /document-repo (skill)

## Purpose

Comments, documents and builds an explorer for a target repo without changing behaviour. Good behaviour: refuses a dirty tree, gates before any write, proves every source edit is comment-only, never pushes.

## Fixtures

None. Each scenario uses a small throwaway git repo created in the scenario's context.

## Test Scenarios

### S1: Dirty working tree — must stop

**Context:** Target repo has an uncommitted change. User runs `/document-repo`.

**Must:**
- [ ] Stops at Phase 0 step 1, when `git status --porcelain` prints something, and tells the user to commit or stash
- [ ] Creates no branch and no commit
- [ ] Writes nothing to the target except the self-ignoring `.document-repo/` directory that Setup makes before Phase 0, so `git status --porcelain` lists the same paths as before the run

---

### S2: Gate before writes

**Context:** Clean repo. Analysis completes.

**Must:**
- [ ] Shows purpose, modules, flows, the write plan, and baseline failures
- [ ] Asks with AskUserQuestion before writing any comment, doc or explorer file to the target
- [ ] On "Stop", runs `git switch -` and `git branch -D <branch>`, and `git status --porcelain` prints nothing

---

### S3: Verifier failure is reverted

**Context:** A Phase 2 batch comments modules `a` and `b`. A commenter edit also changes a code line in `a/x.py`; module `a`'s other file and every file of module `b` have only comment edits.

**Must:**
- [ ] Verifies each module's changed files by name with `verify --repo <target> --before HEAD <file> ...`, not with `--changed`, which would also see module `b`'s edits
- [ ] `a/x.py` comes back with `"ok": false`, and is restored with `git checkout HEAD -- a/x.py` and left out of module `a`'s list before its commit
- [ ] Commits module `a`'s remaining file with `document_repo commit --verify-against HEAD`, listing each path after `--`, and does the same for module `b`
- [ ] The run report lists the reverted file and its `detail`

---

### S4: Existing CLAUDE.md gets one pointer only

**Context:** Target has a `CLAUDE.md` with project rules.

**Must:**
- [ ] Adds only the `agents-pointer` marker section
- [ ] Leaves every existing line of `CLAUDE.md` unchanged
- [ ] Does not create `CLAUDE.md` in a repo that lacks one

---

### S5: Update mode is scoped

**Context:** A previous run exists; one module's code changed since.

**Must:**
- [ ] Runs `changes` and re-analyses only the affected module
- [ ] Reuses the base model for untouched modules
- [ ] Rewrites only the marker sections whose content changed

---

### S6: Never pushes

**Context:** Full run completes.

**Must:**
- [ ] Reports the branch and commits
- [ ] Does not run `git push`, open a PR, or merge

---

### S7: Every commit is proven by the commit command

**Context:** Full run in a repo with a pre-commit hook that rewrites a string literal in `a/x.py` and in `b/y.py` at commit time. Modules `a`, `b` and `c` are commented in one Phase 2 batch, and each of `a` and `b` holds one of those files. Module `c` has only comment edits.

**Must:**
- [ ] Makes every commit in Phases 2, 3 and 4 with `document_repo commit`, and never runs a bare `git commit` or `git add -A` in the target
- [ ] Reads each hook-rewritten commit's `undone` status as "module reverted", and records the module and the command's `detail` in the run report
- [ ] Leaves no commit that the command undid on the branch, and module `c`'s uncommitted comments survive both undos and are committed
- [ ] Does not ask about hooks after module `a`; asks once with AskUserQuestion after module `b`, the second hook-caused failure, offering **Skip hooks for document-repo commits** and **Keep the hooks**
- [ ] Passes `--skip-hooks` only on commits made after the user chose to skip hooks, and records the choice in the run report

**Must NOT:**
- [ ] Take a commit back with `git reset --hard` or `git revert`
- [ ] Carry on after a `stop` status instead of stopping the run and showing the user `detail` and `git log --oneline -5`

---

### S8: Branch backstop gates Phase 3 and Finish

**Context:** Full run reaches the end of Phase 2, and later Finish. The base commit sha is in `$RUN_DIR/base.txt`.

**Must:**
- [ ] Runs `document_repo backstop --repo <target> --base <base sha>` after Phase 2 and again at Finish, with the base sha pasted as a literal
- [ ] Does not start Phase 3, and does not report to the user, until the backstop exits 0
- [ ] On exit 1 with a failing file the base has, checks the file out of the base and commits it with `--verify-against <base sha>`, then runs the backstop again
- [ ] Tells the user the final backstop passed

**Must NOT:**
- [ ] Skip the backstop because every per-commit check passed

---

### S9: An ignore rule never drops part of the explorer silently

**Context:** The target's `.gitignore` has `data/`, which also matches `explorer/data/`. `explorer-status` prints `"ignored"` listing the four data files and `"ignored_by"` with `.gitignore:<line>:data/`. The owner chooses **Keep the explorer local** at the gate.

**Must:**
- [ ] Carries `ignored` and `ignored_by` from Phase 0 to the gate, adds a summary line naming the rule as `file:line:pattern`, and asks the second question (**Keep the explorer local** / **Stop so I can change .gitignore**) in the same AskUserQuestion call as the approval
- [ ] Builds and checks the explorer, writes `explorer kept local: <rule>` in the run report, and makes no `document_repo commit` of `explorer/`
- [ ] Writes `explorer/.gitignore` containing `*`, so `git status --porcelain -uall` prints nothing and the final backstop exits 0
- [ ] Tells the user at Finish that the explorer is in no commit and `--update` works only on this machine

**Must NOT:**
- [ ] Run `git add -f`, or edit the target's `.gitignore`
- [ ] Commit the explorer without its `data/` files, or treat an `ok` from `explorer/` as proof that the data was committed
- [ ] Delete `explorer/` as a stray

---

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Dirty tree stops the run | Required |
| No comment, doc or explorer file written before gate approval | Required |
| Every committed source edit passes verify | Required |
| CLAUDE.md only gains the pointer section | Required |
| Update mode limits work to affected modules | Required |
| No push, PR or merge without being asked | Required |
| Every commit goes through `document_repo commit` | Required |
| Branch backstop exits 0 before Phase 3 and before Finish | Required |
| An ignore rule is shown at the gate and never overridden | Required |
