---
command: arch-review
type: skill
fixtures: []
---

# Eval: /arch-review (skill)

## Purpose

Comprehensive 9-agent architecture review — spawns parallel domain specialists (solutions-architect, data-architect, integration-architect, software-engineer, performance-engineer, qa-architect, security-architect, platform-engineer, risk-compliance), each writing structured findings to disk, then synthesizes an executive report with a Go/No-Go recommendation. `disable-model-invocation: true` — must only run via explicit `/arch-review` invocation. Good behavior: all 9 agents (or the `--focus` subset) are dispatched in parallel (not sequentially), no domain is silently dropped, and the executive summary is written to disk with a defensible recommendation.

## Fixtures

None — targets an arbitrary codebase path; can be run against this repository itself.

## Setup

Run against a target directory (e.g., a plugin directory or the whole repo). Requires the Agent tool and the 9 registered `personal-plugin:*` review agents.

## Test Scenarios

### S1: Happy path — full review, default scope

**Invocation:** `/arch-review <path>`

**Must:**
- [ ] Creates `<path>/arch-review/findings/` and `<path>/arch-review/reports/`
- [ ] Writes `<path>/arch-review/intake.md` itself (Step 2) before spawning any agents — does not delegate intake
- [ ] Spawns all 9 domain agents via the Agent tool using `subagent_type: "personal-plugin:<agent-name>"`, dispatched in parallel (not one-at-a-time)
- [ ] Each agent writes `findings/<agent-name>.md` and `findings/<agent-name>.meta.json`
- [ ] After all agents complete, reads all 9 findings files and builds a conflict log
- [ ] Writes `<path>/arch-review/reports/executive-summary.md` containing a Review Coverage table, a Go/No-Go recommendation, Critical/High findings summary, Cross-Domain Risk Map, Remediation Roadmap, and Domain Report Index
- [ ] Prints a terminal summary with agents-run count (N/9), total findings by severity, top 3 Critical/High findings, and the recommendation

**Must NOT:**
- [ ] Auto-invoke without an explicit `/arch-review` call (it has `disable-model-invocation: true`)
- [ ] Fabricate findings for a domain it didn't actually analyze
- [ ] Silently skip a domain that was in scope

---

### S2: `--focus` subset

**Invocation:** `/arch-review <path> --focus security-architect,performance-engineer`

**Must:**
- [ ] Spawns only the 2 named agents, not all 9
- [ ] Executive summary's Review Coverage table and Domain Report Index reflect only the 2 domains run

---

### S3: Unrecognized `--focus` name

**Invocation:** `/arch-review <path> --focus nonexistent-agent`

**Must:**
- [ ] Prints the valid `--focus` agent list
- [ ] Stops rather than silently dropping the unrecognized name or substituting a guess

---

### S4: `--no-meta`

**Invocation:** `/arch-review <path> --no-meta`

**Must:**
- [ ] Instructs each spawned agent not to write a `.meta.json` file
- [ ] Still produces `findings/*.md` and the executive summary
- [ ] Coverage table in the executive summary still reflects confidence/runtime notes surfaced by agents even without persisted meta files, or clearly notes meta was skipped

---

### S5: Missing target path

**Invocation:** `/arch-review` (no path argument)

**Must:**
- [ ] Stops and prints usage
- [ ] Does not guess a target directory

---

### S6: A domain agent returns incomplete output

**Setup:** Simulate (or reason about) a spawned agent returning no findings file or an incomplete one.

**Must:**
- [ ] Re-spawns that agent with the identified gaps rather than silently omitting the domain from the report
- [ ] Notes the low-confidence/incomplete coverage in the executive summary's Coverage notes if it still can't be resolved

---

### S7: Conflicting findings across domains

**Setup:** Two domain findings contradict each other (e.g., one recommends a change the other flags as a regression).

**Must:**
- [ ] Builds a conflict log during Step 4 (Coverage Assessment and Conflict Detection)
- [ ] Resolves the conflict using business impact as the tiebreaker, with the reasoning documented in the Cross-Domain Risk Map — does not silently drop either finding

## Rubric

| Criterion | Pass Threshold |
|-----------|-----------------|
| Never auto-invokes without explicit `/arch-review` | Required |
| All in-scope domains produce findings (none silently skipped) | Required |
| Agents dispatched in parallel, not sequentially | Required |
| Executive summary written with Go/No-Go recommendation | Required |
| `--focus` restricts scope correctly; invalid names stop rather than get dropped | Required |
| Conflicting cross-domain findings are resolved and documented, not discarded | Required |
| No fabricated findings | Required |
