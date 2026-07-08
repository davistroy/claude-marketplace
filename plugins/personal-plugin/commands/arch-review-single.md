---
description: Run a single domain agent from the architecture review team against a target codebase
argument-hint: <agent-name> <path-to-target>
effort: medium
allowed-tools: Read, Glob, Grep, Bash, Agent
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
3. Check if `<target-path>/arch-review/intake.md` exists:
   - If yes: use it as the intake context
   - If no: perform a brief intake pass (5-minute reconnaissance: stack detection, README read, directory structure)
4. Ensure output directory exists: `mkdir -p <target-path>/arch-review/findings`
5. Dispatch via the **Agent tool** with `subagent_type: "personal-plugin:<agent-name>"` (fall back to the bare `<agent-name>` if the namespaced subagent type does not resolve). Pass only the intake context, target path, and output paths — do NOT read or inline the agent's definition file; the registered agent supplies its own system prompt.
6. Agent writes findings to `<target-path>/arch-review/findings/<agent-name>.md`
7. Agent writes its own `<target-path>/arch-review/findings/<agent-name>.meta.json` (per-agent file, not a shared/merged meta file)
8. Print findings summary to terminal on completion

If this is a re-run (findings file already exists), the new output overwrites the previous. Run `/arch-synthesize <target-path>` afterward to regenerate the executive summary.
