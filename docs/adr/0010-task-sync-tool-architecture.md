# ADR-0010: task-sync Tool Architecture — Bundled Python Tool + Plan/Decide/Apply + REST Providers

**Date:** 2026-07-18
**Status:** Accepted
**Deciders:** Troy Davis (via `/ultra-plan` on the approved task-sync design, `docs/plans/2026-07-18-task-sync-design.md`, D34)

## Context

`/task-sync` keeps a per-repo `tasks.json` (with a generated `TASKS.md` view) reconciled with the repo's issue tracker — GitHub via the `gh` CLI, Gitea via its REST API. Three implementation choices had to be settled before Phase 1 could start, because they shape every subsequent phase (D34, `docs/plans/2026-07-18-task-sync-design.md`):

1. **Where does the deterministic logic live?** This repo's convention (ADR-0002) is that skills orchestrate and bundled Python tools do correctness-critical work. task-sync's reconcile engine has real correctness risk: a 3-way classify against a `last_synced` base, last-write-wins conflict handling, and prune-by-age — the kind of logic that is easy to get subtly wrong and expensive to get wrong silently (a sync bug can corrupt a task list or clobber a real edit).
2. **How does the skill decide what to push/pull without ever surprising the user?** The tool cannot itself prompt (it is a scriptable CLI, exercised by CI and by hand); the skill cannot itself be trusted to compute 3-way reconcile correctly inline. Something has to separate "compute what would change" from "the user has approved it" from "make it so."
3. **How does the Gitea provider actually read issue state?** The obvious low-effort option is shelling out to the `tea` CLI, which is already installed and authenticated for interactive use.

## Decision

1. **Bundled Python tool, not bash+jq.** All deterministic logic — the data model, the store (atomic canonical JSON read/write), provider adapters, the reconcile engine, and the confidentiality scanner — lives in `plugins/personal-plugin/tools/task-sync/` as a stdlib-only Python package (`task_sync`), invoked by the skill via `PYTHONPATH="$TOOL_SRC" python3 -m task_sync <command>`. This follows the existing bundled-tool pattern (ADR-0002) rather than introducing a new bash+jq pattern for this skill.

2. **A `plan → decide → apply` protocol for `sync`**, not a single opaque `sync` call:
   - `sync --plan --json` is strictly read-only: it never writes `tasks.json`/`TASKS.md` and never calls the tracker's write API. It computes and emits `creates`, `pushes`, `pulls`, `conflicts`, and `confidentiality_findings` as structured JSON.
   - The skill renders that plan for the user and collects explicit decisions (`local`/`remote` per conflict, `keep`/`redact`/`remove`/`anonymize` per confidentiality finding). An undecided conflict is left untouched by `apply` and simply resurfaces on the next `sync --plan` — deferring is always safe.
   - `sync --apply --decisions <file>` executes exactly the decided plan: creates/pushes/pulls, applies only the decided conflicts, prunes `done` tasks past the configured age threshold, and saves atomically.
   - `--dry-run` is simply "plan, don't apply" — the tool's default mode when no mode flag is given, so an accidental bare `sync` invocation can never mutate anything.

3. **REST-based provider adapters for both trackers**, not `tea` CLI reads for Gitea. GitHub reads/writes go through the `gh` CLI (already the repo's established authenticated GitHub interface) parsed as JSON. Gitea reads/writes go through its REST API directly via stdlib `urllib`, using the token already present in `~/.config/tea/config.yml`, rather than shelling out to `tea` and parsing its CLI output.

## Alternatives Considered

### bash + jq for the sync logic

- **Description:** Implement the store, reconcile, and provider calls as shell scripts piping through `jq`, consistent with some of this repo's lighter-weight tooling.
- **Pros:** No new Python package; fewer moving parts for the simplest commands (`list`, `status`).
- **Cons:** Untestable to this repo's coverage bar (ADR-0002's rationale for bundled Python tools over bash applies directly here) — a 3-way classify with last-write-wins and prune-by-age has enough branching that shell+jq tests would be fragile and hard to write exhaustively. Windows-fragile: this repo's CI matrix runs `windows-latest`, and `jq`-heavy bash pipelines are a known source of platform-specific breakage here. Most importantly, **a reconcile bug silently corrupts the task list** — there is no natural place to unit-test "did this conflict correctly surface instead of auto-clobbering" in bash the way `pytest` can assert it directly against fixtures.
- **Why rejected:** The correctness stakes (data loss / silent clobber) are exactly the case ADR-0002 already argues bundled Python tools exist for. Rejected before Phase 1 started.

### `tea` CLI reads for the Gitea provider

- **Description:** Shell out to the already-installed, already-authenticated `tea` CLI and parse its JSON output for issue state, mirroring the `gh` CLI approach used for GitHub.
- **Pros:** Reuses an existing authenticated tool; symmetrical with the GitHub adapter's use of `gh`; no new HTTP/token-handling code.
- **Cons:** `tea`'s JSON output omits `updated_at` and `body` — both are load-bearing for this design. `updated_at` is required for last-write-wins conflict detection (the reconcile engine cannot classify `changed-remote` vs `unchanged` without it), and `body` is required to scan pulled issue content and to render pull diffs. Without them the Gitea provider would be structurally incapable of the same reconcile fidelity as the GitHub provider.
- **Why rejected:** A thin adapter that silently loses the two fields the reconcile engine depends on is worse than the extra code of a REST client. The Gitea REST API (same token, network already reachable) returns the full GitHub-compatible shape, so both providers read via REST behind one normalized `Provider` protocol — no asymmetry between trackers.

## Consequences

### Positive
- The correctness-critical path (reconcile, confidentiality scanning, atomic store I/O) is unit-tested to the repo's coverage floor and is mypy/ruff-clean, independent of any LLM session.
- `--plan`/`--dry-run` being provably write-nothing (asserted by tests plus a git-clean check) means a user can always preview a sync with zero risk, and an accidental bare `sync` cannot mutate state.
- Both providers return the same normalized `Issue` shape, so the reconcile engine, tests, and skill rendering logic are provider-agnostic — no Gitea-specific branches leaking into the sync logic.
- Consistent with ADR-0002 (bundled Python tools from source) and this repo's existing three-tool pattern (bpmn2drawio, visual-explainer, feedback-docx-generator).

### Negative
- More code and more files than a bash+jq version for the simple commands (`list`, `status`, `add`) — a stdlib-only Python package with a store, model, and CLI plumbing, even for behavior that is individually simple.
- The Gitea REST adapter is bespoke stdlib `urllib` code (no `httpx`/`requests` dependency, to keep the tool's zero-runtime-dependency posture per its `requirements-lock.txt`), which means more manual HTTP/pagination handling than a well-maintained SDK would provide.

### Neutral
- `sync` remains the only subcommand that goes through plan→decide→apply; every other subcommand (`list`/`add`/`edit`/`done`/`remove`/`status`/`init`) mutates directly and immediately, since none of them carry cross-machine reconcile risk.

## References

- D34 / `docs/plans/2026-07-18-task-sync-design.md` — the approved design this ADR formalizes.
- `IMPLEMENTATION_PLAN.md` (task-sync build, Phases 1–6) — Phase 1 (tool skeleton + model), Phase 2 (provider abstraction), Phase 3 (reconcile engine), Phase 4 (confidentiality scanner).
- ADR-0002 (Python tools from source) — the bundled-tool pattern this ADR extends to task-sync.
- LAB_NOTEBOOK.md Entry 049 (archived, see `docs/archive/LAB_NOTEBOOK-E017-E050.md`) — build log across all six phases.
