---
command: prime
type: skill
fixtures: []
---

# Eval: /prime (skill)

## Purpose

Evaluates an existing codebase to produce a detailed report on project purpose, health, status, and recommended next steps. Good output: a report that accurately characterizes what the project actually does, rates its health across key dimensions, and gives concrete next steps grounded in the actual state.

## Fixtures

None — operates on the current repository.

## Test Scenarios

### S1: Prime the marketplace repo

**Invocation:** `/prime`

**Must:**
- [ ] Reads project structure, README, CLAUDE.md, plugin.json files
- [ ] Produces a report identifying the project as a Claude Code plugin marketplace
- [ ] Report includes a health rating or scorecard
- [ ] Report includes recommended next steps
- [ ] Report is saved to a file (e.g., `PRIME_REPORT.md`) or presented in-conversation with clear structure

**Should:**
- [ ] Identifies the two plugins (personal-plugin, bpmn-plugin) correctly
- [ ] Notes the versioning strategy (two-tier: marketplace + per-plugin)
- [ ] Recommended next steps are specific to the current state (not generic)

**Must NOT:**
- [ ] Fabricate features or components that don't exist
- [ ] Give the same report for different projects (must be context-specific)
- [ ] Modify any existing files (read-only)

---

### S2: Health metrics accuracy

**Must:**
- [ ] If the project has no unit tests, the health report reflects this as a gap
- [ ] If CLAUDE.md is well-maintained, this is noted as a strength

---

### S3: Proactive trigger

**Context:** User opens a new conversation in an unfamiliar project.

**Must:**
- [ ] Skill suggests itself (proactive) when conversation context is a new/unfamiliar codebase

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Project purpose accurately described | Required |
| Health assessment grounded in actual state | Required |
| Next steps are specific, not generic | Required |
| No files modified | Required |
| Report clearly structured | Should |
