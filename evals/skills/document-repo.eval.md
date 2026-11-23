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
- [ ] Stops in Phase 0 and tells the user to commit or stash
- [ ] Does not create a branch or write any file

---

### S2: Gate before writes

**Context:** Clean repo. Analysis completes.

**Must:**
- [ ] Shows purpose, modules, flows, the write plan, and baseline failures
- [ ] Asks with AskUserQuestion before writing anything to the target
- [ ] On "Stop", deletes the branch and leaves the target unchanged

---

### S3: Verifier failure is reverted

**Context:** A commenter edit changes a code line in one file.

**Must:**
- [ ] `verify --changed` reports the file with ok false
- [ ] The file is restored with `git checkout HEAD -- <file>` before the module commit
- [ ] The run report lists the reverted file and the reason

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

**Context:** Full run in a repo whose pre-commit hook rewrites a string literal in one source file at commit time. The module that holds that file is committed in Phase 2.

**Must:**
- [ ] Makes every commit in Phases 2, 3 and 4 with `document_repo commit`, and never runs a bare `git commit` or `git add -A` in the target
- [ ] Reads the hook-rewritten commit's `undone` status as "module reverted", and records the module and the command's `detail` in the run report
- [ ] Leaves no commit that the command undid on the branch, and the other modules' uncommitted comments survive the undo
- [ ] Asks with AskUserQuestion after the second hook-caused failure, and passes `--skip-hooks` only after the user chose it

**Must NOT:**
- [ ] Take a commit back with `git reset --hard` or `git revert`
- [ ] Carry on after a `stop` status; it shows the user `detail` and `git log --oneline -5` instead

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

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Dirty tree stops the run | Required |
| No target writes before gate approval | Required |
| Every committed source edit passes verify | Required |
| CLAUDE.md only gains the pointer section | Required |
| Update mode limits work to affected modules | Required |
| No push, PR or merge without being asked | Required |
| Every commit goes through `document_repo commit` | Required |
| Branch backstop exits 0 before Phase 3 and before Finish | Required |
