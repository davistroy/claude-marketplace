# Validation Maturity Scorecard

Reference for the `/validate-plugin --scorecard` flag. Loaded on demand when the `--scorecard` flag is passed.

## Table of Contents

- [Maturity Levels Overview](#maturity-levels-overview)
- [Level 1 (Basic) Criteria](#level-1-basic-criteria)
- [Level 2 (Standard) Criteria](#level-2-standard-criteria)
- [Level 3 (Complete) Criteria](#level-3-complete-criteria)
- [Level 4 (Exemplary) Criteria](#level-4-exemplary-criteria)
- [Scorecard Output Format](#scorecard-output-format)
- [Scorecard Calculation Logic](#scorecard-calculation-logic)
- [Example Usage](#example-usage)

---

## Maturity Levels Overview

| Level | Name | Criteria | Score Range |
|-------|------|----------|-------------|
| **1** | Basic | Valid plugin.json, commands parse without errors | 0-25% |
| **2** | Standard | Help.md complete, all patterns followed, frontmatter valid | 26-50% |
| **3** | Complete | Tests exist, all standard flags implemented, no warnings | 51-75% |
| **4** | Exemplary | Full documentation, CI validation passing, 90%+ test coverage | 76-100% |

---

## Level 1 (Basic) Criteria

A plugin achieves Level 1 when:
- `plugin.json` exists and contains valid JSON
- Required fields present: `name`, `description`, `version`
- Version follows semver format (X.Y.Z)
- All command `.md` files have valid frontmatter
- All skills use correct directory structure (`skills/[name]/SKILL.md`)
- YAML in frontmatter parses without errors

---

## Level 2 (Standard) Criteria

A plugin achieves Level 2 when all Level 1 criteria are met, plus:
- `help.md` exists and documents all commands/skills
- All commands have `## Input Validation` section
- All commands have `## Instructions` section
- No forbidden `name` field in frontmatter
- Output naming follows convention: `[type]-[source]-[timestamp].[ext]`
- Error messages follow standard format

---

## Level 3 (Complete) Criteria

A plugin achieves Level 3 when all Level 2 criteria are met, plus:
- Tests exist in `tests/` directory for the plugin
- Standard flags implemented where applicable:
  - `--verbose` for detailed output
  - `--preview` for commands generating output
  - `--force` for validation override
- Zero warnings in validation output
- All code blocks have language specifiers
- All internal references resolve correctly

---

## Level 4 (Exemplary) Criteria

A plugin achieves Level 4 when all Level 3 criteria are met, plus:
- Documentation complete (README, CONTRIBUTING if applicable)
- CI/CD workflow validates the plugin
- Test coverage at 90% or higher
- Examples provided for all commands
- Performance notes for long-running commands

---

## Scorecard Output Format

```text
Plugin Maturity Scorecard

Plugin: personal-plugin
-----------------------
Level 1 (Basic)        [################] 100%
  [x] Valid plugin.json
  [x] Required fields present
  [x] Semver version format
  [x] Skill structure correct (skills/[name]/SKILL.md)
  [x] Frontmatter parses

Level 2 (Standard)     [################] 100%
  [x] help.md complete
  [x] Input Validation sections
  [x] Instructions sections
  [x] No forbidden fields
  [x] Output naming compliant

Level 3 (Complete)     [############----]  75%
  [x] Tests exist
  [x] Standard flags implemented
  [ ] Zero warnings (2 warnings found)
  [x] Code block languages

Level 4 (Exemplary)    [########--------]  50%
  [x] CI/CD workflow exists
  [ ] Test coverage 90%+ (currently 85%)
  [x] Examples in all commands
  [ ] Performance notes missing

Current Level: 3 (Complete)
Overall Score: 81%

-----------------------
Plugin: bpmn-plugin
-----------------------
Level 1 (Basic)        [################] 100%
Level 2 (Standard)     [################] 100%
Level 3 (Complete)     [################] 100%
Level 4 (Exemplary)    [################] 100%

Current Level: 4 (Exemplary)
Overall Score: 100%

Aggregate Scorecard

| Plugin | Level | Score | Status |
|--------|-------|-------|--------|
| personal-plugin | 3 | 81% | Complete |
| bpmn-plugin | 4 | 100% | Exemplary |

Average Score: 90.5%
Plugins at Level 4: 1/2 (50%)

Improvement Suggestions

personal-plugin:
  To reach Level 4 (Exemplary):
  1. Fix 2 code block warnings (add language specifiers)
  2. Increase test coverage to 90%+ (currently 85%)
  3. Add Performance section to long-running commands

Priority: Address warnings first (quick win for Level 3 completion)
```

---

## Scorecard Calculation Logic

**Level Score Calculation:**
- Each level has a set of criteria (checkboxes)
- Level percentage = (criteria met / total criteria) * 100
- A level is "achieved" when 100% of its criteria are met

**Overall Score Calculation:**
```text
Overall Score = (L1_score * 0.1) + (L2_score * 0.2) + (L3_score * 0.3) + (L4_score * 0.4)
```

**Current Level Assignment:**
- Level 1: All L1 criteria met
- Level 2: Level 1 + all L2 criteria met
- Level 3: Level 2 + all L3 criteria met
- Level 4: Level 3 + all L4 criteria met

---

## Example Usage

```yaml
User: /validate-plugin --all --scorecard

Claude: [Evaluates all plugins and generates scorecard]

Plugin Maturity Scorecard generated.

Summary:
- personal-plugin: Level 3 (81%)
- bpmn-plugin: Level 4 (100%)

Average marketplace maturity: 90.5%

Top improvement opportunities:
1. personal-plugin: Add language specifiers to reach 100% Level 3
2. personal-plugin: Increase test coverage for Level 4
```
