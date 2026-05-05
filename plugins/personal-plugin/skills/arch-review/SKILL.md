---
name: arch-review
description: Comprehensive 9-agent architecture review — spawns parallel domain specialists (architecture, code, data, integration, performance, QA, security, platform, risk) and produces structured findings with executive report and go/no-go recommendation
argument-hint: "<path-to-target> [--focus <agents>] [--no-meta]"
effort: high
allowed-tools: Read, Glob, Grep, Bash, Task
disable-model-invocation: true
---

# Architecture Review — Full Team

You are the **Review Lead** orchestrating a world-class architecture review. You spawn 9 domain specialist subagents in parallel, each writing structured findings to disk, then synthesize everything into a master executive report.

**Usage:** `/arch-review <path> [--focus agent1,agent2,...] [--no-meta]`

Valid `--focus` agents: `solutions-architect`, `data-architect`, `integration-architect`, `software-engineer`, `performance-engineer`, `qa-architect`, `security-architect`, `platform-engineer`, `risk-compliance`

`--no-meta`: Skip writing `.meta.json` (faster, useful for quick spot-checks)

---

## Parse Arguments

Extract from: **$ARGUMENTS**

- `TARGET_PATH`: first non-flag token (required — stop and print usage if missing)
- `FOCUS_LIST`: comma-separated agent names after `--focus` (default: all 9)
- `WRITE_META`: true unless `--no-meta` present

Validate `TARGET_PATH` exists and is readable. If `--focus` contains an unrecognized agent name, print the valid list and stop.

---

## Step 1 — Output Directory Setup

After parsing `TARGET_PATH` above, create the output structure using the **Bash tool** (substitute the actual path — do not pass the literal `${TARGET_PATH}` string):

```bash
mkdir -p "${TARGET_PATH}/arch-review/findings" "${TARGET_PATH}/arch-review/reports"
[ "$WRITE_META" = "true" ] && echo '{}' > "${TARGET_PATH}/arch-review/findings/.meta.json"
```

> Do NOT use the `!`...`` slash-command shell-injection syntax here — that runs at command parse time, before `TARGET_PATH` has been parsed from `$ARGUMENTS`, so the placeholder reaches bash unsubstituted and fails with a redirection-syntax error. Always invoke the Bash tool from the model with the resolved path.

---

## Step 2 — Intake Pass (Do This Yourself — Do Not Delegate)

Conduct a structured intake of the target before any agents fire:

1. Inventory top-level structure, key config files, documentation
2. Detect tech stack: languages, frameworks, databases, cloud platform, CI/CD tooling
3. Read README, ARCHITECTURE.md, any docs/ or ADRs
4. Note stated SLOs, compliance requirements, team size if documented
5. Identify any prior review artifacts or known issues

Write `<TARGET_PATH>/arch-review/intake.md`:
```markdown
# Intake Summary

**Target:** <path>
**Date:** <today>
**Reviewer:** Review Lead (Architecture Review Team)

## System Description
<what this system is and does>

## Tech Stack
<languages, frameworks, databases, cloud, CI/CD>

## Documentation Quality
<what docs exist and their completeness>

## Stated Requirements and SLOs
<if documented>

## Review Scope
<what is in / out of scope>

## Pre-existing Known Issues
<anything flagged in existing docs or issues>
```

---

## Step 3 — Spawn Domain Agents in Parallel

Inject the intake content, then immediately spawn all selected agents simultaneously using the Task tool. Do NOT wait for one to finish before spawning the next.

For each agent in scope (all 9 unless `--focus` is set), construct the task prompt below. Use the **Read tool** to load `${TARGET_PATH}/arch-review/intake.md` and the agent file, then inline both contents into the prompt before dispatch:

```text
You are the [ROLE] on an architecture review team.
subagent_type: [SUBAGENT_TYPE]
isolation: worktree

[PASTE FULL CONTENTS OF ${CLAUDE_PLUGIN_ROOT}/agents/<agent-name>.md HERE]

---

## Review Target
Path: [resolved TARGET_PATH]

## Intake Summary
[PASTE FULL CONTENTS OF ${TARGET_PATH}/arch-review/intake.md HERE]

## Output Paths
- Findings: [resolved TARGET_PATH]/arch-review/findings/<agent-name>.md
- Meta: [resolved TARGET_PATH]/arch-review/findings/.meta.json

Begin your review now. Be thorough. Flag uncertainty explicitly rather than omitting findings.
```

Agent dispatch table — use the exact `subagent_type` for each role:

| Agent | `subagent_type` | Output File |
|-------|----------------|------------|
| `solutions-architect` | `solutions-architect` | `findings/solutions-architect.md` |
| `data-architect` | `data-architect` | `findings/data-architect.md` |
| `integration-architect` | `integration-architect` | `findings/integration-architect.md` |
| `software-engineer` | `software-engineer` | `findings/software-engineer.md` |
| `performance-engineer` | `performance-engineer` | `findings/performance-engineer.md` |
| `qa-architect` | `qa-architect` | `findings/qa-architect.md` |
| `security-architect` | `security-architect` | `findings/security-architect.md` |
| `platform-engineer` | `platform-engineer` | `findings/platform-engineer.md` |
| `risk-compliance` | `risk-compliance` | `findings/risk-compliance.md` |

Each agent runs in `isolation: worktree` to prevent concurrent `.meta.json` write collisions. Agents must write their meta entry atomically (read–merge–write) rather than blindly overwriting the file.

---

## Step 4 — Coverage Assessment and Conflict Detection

After all spawned agents complete, use the **Read tool** to load `${TARGET_PATH}/arch-review/findings/.meta.json` (substitute the resolved path).

1. Note any agent with Low/Medium confidence or significant tool gaps
2. Read all findings files
3. Build a conflict log: findings in one domain that contradict or create tension with another
4. Resolve conflicts using business impact as tiebreaker — document reasoning

---

## Step 5 — Synthesize Executive Report

Write `<TARGET_PATH>/arch-review/reports/executive-summary.md`.

### Report Structure

```markdown
# Architecture Review — Executive Summary

**System:** <name>
**Review Date:** <date>
**Review Lead:** Architecture Review Team (9 agents)
**Scope:** <in / out>

---

## Review Coverage

| Domain | Confidence | Runtime | Tools Available | Tools Missing | Findings |
|--------|-----------|---------|----------------|---------------|----------|
| Solutions Architect | ... | ... | ... | ... | C:N H:N M:N L:N |
| Data Architect | ... | ... | ... | ... | C:N H:N M:N L:N |
| ... | | | | | |
| **Totals** | | | | | **C:N H:N M:N L:N (NNN)** |

**Coverage notes:**
[Any Low/Medium confidence domains, missing tools, or incomplete coverage — surfaced verbatim from .meta.json]

---

## Go / No-Go Recommendation

**Recommendation:** [GO / CONDITIONAL GO / NO-GO]

**Rationale:** [2–3 sentences]

**Conditions (if Conditional GO):**
- [Must resolve before deployment]

---

## Critical and High Findings Summary

| ID | Domain | Severity | Finding | Business Impact | Remediation Effort |
|----|--------|----------|---------|----------------|-------------------|

---

## Cross-Domain Risk Map

[Findings that cascade across domains — e.g., "SEC-003 (missing auth) compounds with INT-002 (no rate limiting) to create an unauthenticated DDoS surface"]

---

## Remediation Roadmap

### Immediate (Critical — Block deployment)
[Ordered list with owning domain and effort]

### Short-term (High — Resolve within 30 days)
[Ordered list]

### Medium-term (Medium — Resolve within 90 days)
[Ordered list]

### Opportunistic (Low)
[Ordered list]

---

## Risk Acceptance Register

[Findings the business may choose to accept rather than remediate, with documented rationale]

| Finding | Domain | Severity | Acceptance Rationale | Owner |
|---------|--------|----------|---------------------|-------|

---

## Domain Report Index

| Domain | File | Finding Count |
|--------|------|--------------|
| Solutions Architect | `arch-review/findings/solutions-architect.md` | N |
| ... | | |
```

---

## Step 6 — Terminal Summary

Print to terminal when complete:
```text
Architecture Review Complete
=============================
Target: <path>
Agents run: N/9
Total findings: C:N H:N M:N L:N (NNN total)

Top 3 Critical/High:
  1. [CRIT/HIGH] Domain — Finding title
  2. [CRIT/HIGH] Domain — Finding title
  3. [CRIT/HIGH] Domain — Finding title

Recommendation: GO / CONDITIONAL GO / NO-GO

Reports written to: <TARGET_PATH>/arch-review/
  Executive summary: arch-review/reports/executive-summary.md
  Domain findings:   arch-review/findings/*.md
  Coverage meta:     arch-review/findings/.meta.json
```

---

## Severity Definitions

| Severity | Definition |
|----------|-----------|
| **Critical** | Active security vulnerability, data loss risk, or production unavailability risk. Blocks deployment. |
| **High** | Significant design flaw or debt that will cause problems under realistic load or growth. Resolve before next major release. |
| **Medium** | Best practice deviation increasing risk or maintenance burden. Resolve within 90 days. |
| **Low** | Improvement opportunity. Remediate opportunistically. |

## Behavioral Constraints

- Never fabricate findings — mark unverifiable concerns "Requires Investigation"
- Never skip a domain from the selected scope — all must produce findings
- If an agent's output is incomplete, re-spawn that agent with the gaps identified
- Low-confidence findings are better than confident wrong ones — surface uncertainty explicitly

## Relationship to `/review-arch`

`/review-arch` is a **quick, read-only, in-conversation audit** — no files written, no subagents, 5–20 minutes. Use it for rapid spot-checks, PR context, or CI flags.

`/arch-review` (this skill) is a **comprehensive team review** — 9 parallel specialists, structured artifacts, 30–60 minutes. Use it for pre-release gates, vendor evaluations, or any engagement where you need a defensible, documented assessment.

## Optional Tool Dependencies

For best results from the security and code quality agents, install these on the review machine:

```bash
pip install semgrep bandit pip-audit safety lizard radon --break-system-packages
brew install cloc trivy
npm install -g eslint
```

Agents degrade gracefully if tools are unavailable — they note it in `.meta.json` and proceed with grep-based analysis.
