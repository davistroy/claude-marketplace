---
command: arch-review-single
type: command
fixtures: []
---

# Eval: /arch-review-single

## Purpose

Runs one domain agent from the architecture review team against a target codebase, without running the full 9-agent `/arch-review` suite. Good output: a single `findings/<agent-name>.md` (plus its `.meta.json`) written for the requested domain, using an existing `intake.md` when present, without touching any other domain's findings.

## Fixtures

None — operates on an arbitrary target codebase path; can be run against this repository itself.

## Test Scenarios

### S1: Happy path — single domain against this repo

**Invocation:** `/arch-review-single security-architect .`

**Must:**
- [ ] Validates `security-architect` against the documented list of 9 valid agent names
- [ ] Reuses `<target-path>/arch-review/intake.md` if it exists, rather than re-running intake
- [ ] Ensures `<target-path>/arch-review/findings/` exists before dispatch
- [ ] Dispatches via the Agent tool with `subagent_type: "personal-plugin:security-architect"`
- [ ] Writes `<target-path>/arch-review/findings/security-architect.md` and `security-architect.meta.json`
- [ ] Prints a findings summary to the terminal on completion
- [ ] Does not modify or delete any other agent's existing findings file

**Must NOT:**
- [ ] Dispatch any agent other than the one requested
- [ ] Fabricate findings if the target has no obvious issues in that domain

---

### S2: Invalid agent name

**Invocation:** `/arch-review-single not-a-real-agent .`

**Must:**
- [ ] Detects the name is not one of the 9 valid domain agents
- [ ] Prints the valid agent-name list
- [ ] Stops before dispatching any agent

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Only the requested domain agent is dispatched | Required |
| Existing intake.md is reused, not regenerated | Required |
| Findings + meta files are written per the documented naming convention | Required |
| Invalid agent name is rejected before dispatch | Required |
