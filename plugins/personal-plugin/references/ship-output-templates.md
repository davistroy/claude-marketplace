# Ship Output Templates

**Purpose:** Illustrative fix-loop pseudocode and Phase 8 completion output formats referenced by `skills/ship/SKILL.md`. These are display templates and an algorithmic walkthrough, not executable logic — the governing gate conditions, loop-exit criteria, and phase decision rules live inline in the skill (Phase 7.1 Loop Parameters, the decision bullets in Phase 7.2, Phase 7.3 Fix Strategies, Phase 7.4 Unfixable Issue Detection).

**Consumer:** `skills/ship/SKILL.md` — Phase 7 (Fix Loop) and Phase 8 (Completion).

---

## Fix Loop Pseudocode (Phase 7.2)

```yaml
FOR attempt = 1 TO 5:
    IF no blocking issues: EXIT LOOP → go to Phase 8 (merge)

    Display: "Fix Attempt [attempt] of 5"
    Display: "[N] critical, [N] warnings remaining"

    FOR each blocking issue:
        Display: "Fixing [ID]: [title]..."

        IF issue is fixable:
            Read the affected file
            Apply the appropriate fix
            Mark as fixed
        ELSE:
            Mark as unfixable with reason

    IF has unfixable issues:
        EXIT LOOP → go to Phase 8 (failure report)

    Commit fixes:
        git add -A
        git commit -m "fix: address PR review issues (attempt [N]/5)

        Resolved:
        - [C1] Issue description
        - [W1] Issue description

        Co-Authored-By: Claude <noreply@anthropic.com>"

    Push:
        git push

    Re-analyze PR

    IF all blocking issues resolved:
        Display: "✓ All issues resolved!"
        EXIT LOOP → go to Phase 8 (merge)

IF attempt > 5 AND blocking issues remain:
    EXIT LOOP → go to Phase 8 (exhaustion report)
```

---

## Phase 8.1 Success Template

```text
Phase 8: Completion
===================
✓ PR #[number] successfully merged!

Summary:
  Branch: [branch-name]
  Fix Attempts: [N]
  Issues Resolved: [N] critical, [N] warnings
  Merge Strategy: Squash

Branches Cleaned:
  ✓ origin/[branch-name] (deleted)
  ✓ local/[branch-name] (deleted)

Stale Branches Pruned:
  ✓ [stale-branch-1] (remote gone, merged)
  ✓ [stale-branch-2] (remote gone, merged)
  [If no stale branches: "None found"]
  [If unmerged branches with gone remotes exist:]
  ⚠ [unmerged-branch] (remote gone, NOT deleted - has unmerged changes)

PR URL: [url]
```

---

## Phase 8.2 Failure Template

```text
Phase 8: Completion (Manual Review Required)
============================================
✗ PR #[number] NOT merged - unfixable issues detected.

Fix Attempts Made: [N]
Issues Resolved: [N]
Issues Remaining: [N]

Unfixable Issues:
-----------------

[C1] [Issue title]
File: [path/to/file] (lines [X-Y])
Reason: [Why it cannot be auto-fixed]
Suggestion: [Manual steps to resolve]

[W2] [Issue title]
File: [path/to/file] (lines [X-Y])
Reason: [Why it cannot be auto-fixed]
Suggestion: [Manual steps to resolve]

Next Steps:
-----------
1. Review the unfixable issues above
2. Make manual fixes in your editor
3. Push additional commits to the PR
4. Run /ship again to retry analysis and merge

PR URL: [url] (still open)
Branch: [branch-name] (preserved for manual work)
```

---

## Phase 8.3 Exhaustion Template

```text
Phase 8: Completion (Fix Loop Exhausted)
========================================
✗ PR #[number] NOT merged - max fix attempts (5) reached.

Attempts Made: 5
Issues Found: [N]
Issues Resolved: [N]
Issues Still Blocking: [N]

Remaining Issues:
-----------------

[C1] [Issue title]
File: [path/to/file]
Status: [e.g., "Fixed 3 times but keeps returning"]

Diagnostic Information:
-----------------------
Attempt 1: Fixed [issues], then [what happened]
Attempt 2: Fixed [issues], then [what happened]
...

This typically indicates:
- Generated/compiled code being modified
- Conflicting linting rules
- Circular dependency between fixes

Recommendation:
---------------
1. Review the diagnostic information above
2. Manually inspect the recurring issues
3. Consider excluding generated files
4. Push manual fix and run /ship again

PR URL: [url] (still open)
Branch: [branch-name] (preserved for manual work)
```
