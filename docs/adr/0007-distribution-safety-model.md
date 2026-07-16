# ADR-0007: Distribution Safety Model — Branch Protection Only

**Date:** 2026-07-16
**Status:** Accepted
**Deciders:** Troy Davis (proposed via arch-review synthesis, finding PLAT-001)

## Context

Consumers install this marketplace with `/plugin marketplace add davistroy/claude-marketplace` and track `origin/main` — this is Claude Code's install-side default for GitHub-hosted marketplaces, not something configurable via `marketplace.json`. Whatever lands on `main` ships to every install on next refresh; there is no release-promotion step between "merged" and "distributed."

The architecture review (platform-engineer domain, finding PLAT-001, Critical) verified via the GitHub API that `main` had no branch protection (404 on the protection endpoint). The repo already runs a substantial CI suite — per-tool test jobs on ubuntu and windows, `Validate Plugins` (×2), `Schema Validation`, `Lint Markdown`, `Python Lint & Format`, `Dependency Security Audit` — but every check was advisory: a red run did not block a merge, and nothing stopped a direct push to `main`. A broken plugin, a bad skill, or a failed schema check could reach every installed instance unreviewed.

This is a solo-maintained, personal marketplace: bus factor 1, no co-maintainers, no external consumers registered.

## Decision

Protect `main` with branch protection only — no separate release channel, no required review:

- **Require a pull request** to merge into `main` (no direct pushes), with **0 required approvals** — the author is the only reviewer available, so requiring approval would deadlock every merge.
- **Require the existing CI status checks to pass** before merge: the per-tool test jobs (ubuntu + windows), `Validate Plugins` (×2), `Schema Validation`, `Lint Markdown`, `Python Lint & Format`, `Dependency Security Audit`. This converts the previously-advisory suite into an enforced merge gate.
- **`enforce_admins=false`** — the maintainer retains an explicit escape hatch for emergency fixes, since there is no second maintainer to unblock a stuck protection rule.
- **CodeQL and GitGuardian remain advisory, not required checks.** Both run as app/default-setup checks whose context names are less stable than authored workflow jobs; making them required risks deadlocking merges on a context that fails to report. They are monitored via the Security tab instead.

This closes PLAT-001: a red-CI merge or a direct push to `main` can no longer auto-ship to every install.

## Consequences

### Positive
- The single Critical finding from the arch review is closed with no new infrastructure
- CI that was already being written and maintained now actually gates what ships
- Zero added process for the common case — a solo maintainer still merges their own PRs, just through a required (and now-enforced) status-check gate instead of an honor system

### Negative
- 0-required-approvals branch protection is a formality against direct pushes, not a substantive second-reviewer safety net — self-approval risk is unchanged from today
- CodeQL/GitGuardian findings can land on `main` without blocking a merge; catching them still depends on the maintainer checking the Security tab
- `enforce_admins=false` means the gate can be bypassed under time pressure, which is also its intended purpose

### Neutral
- No change to how installs work or how `origin/main` is tracked — this decision only changes what is allowed to reach `main`, not the install mechanism
- Revisiting `enforce_admins` or required-approvals is cheap later if a co-maintainer joins

## Alternatives Considered

### Stable/tagged release channel
- **Description:** Consumers pin to a tagged release rather than tracking `origin/main` directly; a release-promotion workflow cuts tags from vetted commits, decoupling "merged" from "released."
- **Pros:** Strongest isolation — a bad merge to `main` never reaches installs until explicitly promoted; standard pattern for multi-consumer distribution.
- **Cons:** Requires a release-promotion workflow, tag/version discipline, and consumer-side pinning instructions that do not exist today; disproportionate process for a marketplace with one maintainer and no known external consumers.
- **Why rejected:** Cost exceeds benefit at current scale. Revisit if external consumers or a co-maintainer appear.

### Required approving review / CODEOWNERS
- **Description:** Require at least one approving review (optionally via CODEOWNERS) before merge.
- **Pros:** Standard second-set-of-eyes control; catches errors the author is blind to.
- **Cons:** Bus factor 1 means author and reviewer are the same person — a required review would deadlock every merge with no override short of disabling the rule.
- **Why rejected:** Structurally unenforceable at bus factor 1.

### Status quo (no protection)
- **Description:** Leave `main` unprotected, keep CI advisory-only.
- **Pros:** No change needed.
- **Cons:** This is the exact configuration the arch review flagged as Critical — any red-CI merge or direct push ships to every install unreviewed.
- **Why rejected:** It is the finding being remediated, not an alternative to it.
