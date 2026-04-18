---
description: Run a single domain agent from the architecture review team against a target codebase
argument-hint: <agent-name> <path-to-target>
effort: medium
allowed-tools: Read, Glob, Grep, Bash, Task
---

# Architecture Review — Single Domain Agent

Run one domain reviewer against a target. Use for re-running after remediation, targeted spot-checks, or adding a domain to an existing review.

**Usage:** `/arch-review-single <agent-name> <path-to-target>`

**Valid agent names:**
- `solutions-architect` — Architecture fit, patterns, NFRs
- `data-architect` — Data models, storage, governance
- `integration-architect` — APIs, contracts, events, resilience
- `software-engineer` — Code quality, design, technical debt
- `performance-engineer` — Scalability, structural performance risks
- `qa-architect` — Test strategy, coverage, CI gates
- `security-architect` — Threat model, SAST, AppSec, dependencies
- `platform-engineer` — CI/CD, IaC, observability, ops readiness
- `risk-compliance` — Regulatory, audit trail, business continuity

---

Parse from: **$ARGUMENTS**

Format: `<agent-name> <target-path>`

1. Extract agent name (first token) and target path (remainder)
2. Validate agent name against the list above — if invalid, print valid names and stop
3. Read `${CLAUDE_PLUGIN_ROOT}/agents/<agent-name>.md`
4. Check if `<target-path>/arch-review/intake.md` exists:
   - If yes: use it as the intake context
   - If no: perform a brief intake pass (5-minute reconnaissance: stack detection, README read, directory structure)
5. Ensure output directory exists: `mkdir -p <target-path>/arch-review/findings`
6. Spawn a single Task with the agent's full definition, intake context, and target path
7. Agent writes findings to `<target-path>/arch-review/findings/<agent-name>.md`
8. Agent writes/merges its entry to `<target-path>/arch-review/findings/.meta.json`
9. Print findings summary to terminal on completion

If this is a re-run (findings file already exists), the new output overwrites the previous. Run `/arch-synthesize <target-path>` afterward to regenerate the executive summary.
