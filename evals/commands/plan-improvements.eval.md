---
command: plan-improvements
type: command
fixtures: []
---

# Eval: /plan-improvements

## Purpose

Analyzes a codebase and generates a prioritized `IMPLEMENTATION_PLAN.md` with improvement recommendations. Unlike `/create-plan` (requirements-driven), this is codebase-driven. Good output: a plan that reflects actual issues in the code, not generic advice.

## Fixtures

None — operates on the current repository. Run against the marketplace repo itself for a meaningful eval.

## Test Scenarios

### S1: Happy path — analyze current repo

**Invocation:** `/plan-improvements`

**Must:**
- [ ] Performs codebase reconnaissance (scans files, identifies structure)
- [ ] Produces `IMPLEMENTATION_PLAN.md` or a `RECOMMENDATIONS.md` (per command docs, it generates both)
- [ ] Plan has STATUS markers (`<!-- STATUS:todo -->`) on all work items
- [ ] Findings reference specific files from the actual codebase (not generic "add unit tests")
- [ ] At least 2 phases with at least 2 items each

**Should:**
- [ ] Priority rubric is applied (higher priority items appear in earlier phases)
- [ ] Items include file count and LOC estimates for sizing
- [ ] Plan covers multiple improvement dimensions (not just one category)

**Must NOT:**
- [ ] Generate a plan that could apply to any project (must be specific to this codebase)
- [ ] Exceed 8 phases or 6 items per phase

---

### S2: Recommendations-only mode

**Invocation:** `/plan-improvements --recommendations-only`

**Must:**
- [ ] Generates `RECOMMENDATIONS.md` without creating `IMPLEMENTATION_PLAN.md`
- [ ] Recommendations include priority and rationale
- [ ] Does not write a plan file

---

### S3: Focus on specific dimension

**Invocation:** `/plan-improvements --focus security`

**Must:**
- [ ] Analysis emphasizes security-related issues
- [ ] Generated plan items are predominantly security-focused

---

### S4: Does not modify source files

**Must:**
- [ ] Only creates/modifies `IMPLEMENTATION_PLAN.md` and/or `RECOMMENDATIONS.md`
- [ ] Does not modify any existing plugin commands, skills, or references

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Findings are codebase-specific (not generic) | Required |
| STATUS markers present | Required |
| Both RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md created (default mode) | Required |
| Plan size limits respected | Required |
| Source files not modified | Required |
