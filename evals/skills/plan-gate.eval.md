---
command: plan-gate
type: skill
fixtures: []
---

# Eval: /plan-gate (skill)

## Purpose

Before starting complex multi-step implementation tasks, assesses scope and routes to the right planning approach: native plan mode for simple changes, `/plan-improvements` for codebase-driven improvements, or `/create-plan` for requirements-driven builds. Good behavior: routes correctly based on task complexity.

## Fixtures

None — triggered by user request description.

## Test Scenarios

### S1: Simple change — should route to native plan mode

**Context:** User asks "can you add a --verbose flag to the review-arch command?"

**Must:**
- [ ] Recognizes this as a simple, targeted change (1-2 files, clear scope)
- [ ] Routes to native plan mode or just proceeds without a full planning workflow
- [ ] Does not invoke `/create-plan` for a 2-line change

---

### S2: Codebase improvement — should route to /plan-improvements

**Context:** User asks "can you improve the overall quality of this plugin? I want to reduce technical debt."

**Must:**
- [ ] Recognizes this as a codebase-driven improvement task
- [ ] Routes to `/plan-improvements` or uses that workflow
- [ ] Does not try to create a plan from requirements documents that don't exist

---

### S3: Requirements-driven build — should route to /create-plan

**Context:** User says "I have a PRD here, can you plan the implementation?"

**Must:**
- [ ] Recognizes this as a requirements-driven task
- [ ] Routes to `/create-plan`
- [ ] Does not use `/plan-improvements` (which analyzes code, not requirements)

---

### S4: Ambiguous request — should ask clarifying questions

**Context:** User asks "can you plan some improvements?"

**Must:**
- [ ] Asks at least one clarifying question to determine scope and source
- [ ] Does not assume the routing without information

---

### S5: Proactive trigger

**Context:** User describes a complex multi-step task without explicitly invoking a plan command.

**Must:**
- [ ] Skill proactively suggests itself before starting implementation
- [ ] Does not start coding a complex task without scope assessment

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Simple changes bypass heavy planning | Required |
| Codebase improvements route to /plan-improvements | Required |
| Requirements tasks route to /create-plan | Required |
| Ambiguous requests prompt clarification | Required |
| Proactive suggestion before complex implementation | Required |
