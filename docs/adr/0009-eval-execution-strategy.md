# ADR-0009: Eval Execution Strategy — Structural Linter Now, Behavioral Runner Deferred

**Date:** 2026-07-17
**Status:** Accepted
**Deciders:** Troy Davis (proposed via /ultra-plan session on the 2026-07-17 /prime backlog, issue #150, Lab Notebook E040/E043 -- archived, see `docs/archive/LAB_NOTEBOOK-E017-E050.md`)

## Context

The `evals/` directory holds 45 `.eval.md` behavioral specs (24 under `evals/skills/`, 21 under `evals/commands/`), each with scenarios, `Must:`/`Must NOT:` criteria, and a quality rubric. Issue #150 framed CI's failure to execute them as a regression ("zero regression signal — a skill prompt body can drift arbitrarily and CI stays green").

Investigation overturned that framing. `evals/README.md:87` states the design intent explicitly: _"Evals are designed to be executed in a live Claude Code session. They are not automated unit tests — they test LLM behavior against a behavioral contract."_ CI never executing them is the **original, documented design**, not an oversight. `scripts/check_eval_mapping.py` was added later (for a different problem — evals outliving renamed surfaces, arch-review SA-006) and only validates that each eval's `command:` maps to a live skill/command. Making the evals CI-executable is therefore not a bug fix but an **architecture change** to what CI is and what it costs.

Two hard constraints shape the choice:

1. **The `Must:` criteria are a mix of mechanical and semantic.** Some are deterministic filesystem/JSON assertions (`assess-document.eval.md`: "Creates `reports/assessment-draft-prd-*.json`", "Output is valid JSON"). Others are irreducibly judgment calls (`prime.eval.md`: "Does not fabricate features that don't exist"; `description-triggers.eval.md`: "Activates the bpmn-generator skill"). Verifying the semantic ones requires actually running the skill and grading its output with an LLM.

2. **CI holds zero secrets today.** No `.github/workflows/*` references `secrets.*`. The `plugin-validate` job installs the Claude Code CLI purely for `claude plugin validate` and is commented "auth-free — no secrets needed." An LLM-judge runner needs `ANTHROPIC_API_KEY`, which would be the repo's **first CI secret** — and secrets are never exposed to pull requests from forks, so an LLM-graded gate could not run on external contributions (e.g. PR #98).

## Decision

Split #150 into a part that ships now and a part deferred to an explicit future decision.

1. **Ship a deterministic structural linter now.** Extend `scripts/check_eval_mapping.py` (stdlib-only, auth-free, <2s, already a required check) to also gate eval _structure_: every scenario has an invocation line and a `Must:` block, every eval has a Rubric, and the `command:` field is validated even for cross-cutting evals (fixing the dead `description-triggers` field). Add a coverage gate: every live surface has an eval or an explicit, reasoned allowlist entry — closing the 10-surface gap and making future gaps fail CI.

2. **Be honest about what it does and does not do.** The structural linter gates the _specs_, not the _behavior_. A skill's prompt body can still drift without tripping it. That is stated plainly rather than papered over — the linter raises the floor (no malformed or orphaned evals, no silent coverage gaps) without claiming to test LLM behavior.

3. **Defer the LLM-judge behavioral runner to its own go/no-go.** Building a runner that actually executes each surface and grades `Must:` criteria with a judge model is a decision about CI's posture — whether it should hold its first secret, run non-deterministically, cost money and minutes per run, and skip fork PRs. That decision is not made here. If taken up later, it lands as a **non-required** (nightly or label-triggered) job so a flaky judge never blocks merges (consistent with D28's advisory-vs-required stance).

## Consequences

### Positive
- Closes the actionable, deterministic part of #150 immediately: no malformed evals, no orphaned `command:` fields, no silent coverage gaps — all in a fast, auth-free, required check.
- Keeps CI deterministic and secret-free; nothing about the merge gate becomes flaky or fork-hostile.
- Records the real design fact (evals are human-run by intent) so a future reader does not re-file #150 as a regression.
- Frames the behavioral runner as an explicit, cost-aware decision rather than something smuggled in under "make evals executable."

### Negative
- The core complaint in #150 — that prompt-body drift passes CI — is **not** solved by this ADR. That remains true until (and unless) the behavioral runner is built.
- A structural linter can give a false sense of coverage: "every surface has an eval" says nothing about whether the eval's assertions still match the skill's behavior.

### Neutral
- The 45 evals remain useful exactly as before for manual/live-session grading; nothing about their authoring or the documented scoring changes.
- `evaluate-pipeline-output.eval.md` is allowlisted (it pins a machine-specific path and is unrunnable in CI under any architecture), documenting a real limitation rather than hiding it.

## Alternatives Considered

### Build the LLM-judge runner now (structural linter + behavioral execution)
- **Description:** Add a Claude Agent SDK runner that spins a scratch workspace per eval, invokes the surface, and grades each `Must:` with a judge model.
- **Pros:** The only option that actually tests behavior and matches the authors' "test LLM behavior" intent; genuinely closes #150's stated gap.
- **Cons:** Introduces `ANTHROPIC_API_KEY` as the repo's first CI secret; cannot run on fork PRs (secrets withheld), breaking the external-contribution path; real per-run cost and minutes across 45 evals × ~237 `Must:` blocks; nondeterministic (`assess-document` asserts an LLM's aesthetic score is 3.5–4.5, which will flake); would be a required-check deadlock risk (PLAT-012/D28).
- **Why rejected (for now):** It is a CI-posture decision, not an implementation task, and deserves its own explicit go/no-go rather than riding in under a backlog item. Deferred, not refused.

### Hybrid: re-author all 45 evals with machine-readable criterion markers
- **Description:** Tag each criterion as mechanical vs semantic (e.g. `- [ ] {file_exists: reports/*.json}`); hard-gate the mechanical subset deterministically, run the semantic subset under the LLM judge on a non-required job.
- **Pros:** Best fidelity-to-cost ratio in theory — a fast deterministic required gate plus real behavioral checks where they matter.
- **Cons:** By far the largest diff (all 45 evals rewritten); the mechanically-assertable share looks like a minority of the ~237 criteria (`description-triggers` alone contributes ~30, none mechanical), so the required gate would still cover little more than file-existence and JSON shape — i.e. the structural linter with much more work.
- **Why rejected:** High cost for a required gate that ends up barely stronger than option 1's structural linter. Not worth the full re-authoring pass.

### Close #150 as working-as-intended
- **Description:** Accept `evals/README.md:87` at face value (evals are human-run) and close the issue with no code.
- **Pros:** Keeps the repo honest; adds no half-gate.
- **Cons:** Leaves the 10-surface coverage gap and the dead `description-triggers` `command:` field unfixed, and lets orphaned/malformed evals pass CI silently.
- **Why rejected:** There is a real, deterministic, auth-free improvement available (structure + coverage gating) that is worth shipping; closing outright forgoes it.
