<!-- ============================================================
     READ-ONLY COMMAND TEMPLATE

     Canonical Section Order (per schemas/command.json):
     1. Frontmatter (description, allowed-tools)
     2. Title (# Command Name)
     3. Brief description paragraph
     4. Input Validation (optional for read-only)
     5. Instructions (organized as phases)
     6. Output Format (inline report, not file)
     7. Examples
     8. Performance (recommended for analysis commands)

     Pattern References:
     - Validation: references/patterns/validation.md (severity levels)
     - Output: references/patterns/output.md (completion summaries)
     - Logging: references/patterns/logging.md (performance expectations)

     Note: Read-only commands ANALYZE AND REPORT but DO NOT MAKE CHANGES
     ============================================================ -->

<!-- SECTION 1: FRONTMATTER -->
---
description: {{DESCRIPTION}}
---

<!-- SECTION 2: TITLE -->
# {{TITLE}}

<!-- SECTION 3: BRIEF DESCRIPTION -->
{{INTRO_PARAGRAPH}}

<!-- SECTION 4: INPUT VALIDATION (optional for read-only) -->
## Input Validation

**Optional Arguments:**
- `<target>` - Specific target to analyze (default: current context)

**Validation:**
If target is not found, display:
```
Error: Target '[name]' not found.

Available targets:
  - [list available targets]

Example: /{{COMMAND_NAME}} target-name
```

See `references/patterns/validation.md` for error message format.

<!-- SECTION 5: INSTRUCTIONS -->
## Instructions

Execute the following systematic analysis. **DO NOT MAKE ANY CHANGES - ONLY ANALYZE AND REPORT.**

### Phase 1: Information Gathering

1. [First step of data collection]
2. [Second step of data collection]
3. [Third step of data collection]

### Phase 2: Analysis

Evaluate each dimension against best practices:

**[Category 1]**
- [Check point 1]
- [Check point 2]
- [Check point 3]

**[Category 2]**
- [Check point 1]
- [Check point 2]
- [Check point 3]

### Phase 3: Findings Summary

Create a categorized inventory of all findings using standard severity levels:

See `references/patterns/validation.md` for severity level definitions.

| Severity | Label | Action Required |
|----------|-------|-----------------|
| **CRITICAL** | Must fix | Immediate resolution required |
| **WARNING** | Should fix | Should be addressed before merge |
| **SUGGESTION** | Nice to have | Non-blocking, at discretion |

**Report Structure:**
```markdown
### CRITICAL Issues (Must Fix)
#### C1. [Issue Title]
...

### WARNING Issues (Should Fix)
#### W1. [Issue Title]
...

### SUGGESTION Issues (Nice to Have)
#### S1. [Issue Title]
...
```

### Phase 4: Recommendations

Produce a prioritized action plan with:
1. **Quick wins**: Low-effort, high-impact fixes (< 1 day each)
2. **Short-term targets**: Important changes achievable in 1-2 weeks
3. **Long-term considerations**: Larger changes requiring planning

For each item include:
- Specific items affected
- Concrete approach
- Risk level
- Estimated effort

<!-- SECTION 6: OUTPUT FORMAT -->
## Output Format

Read-only commands produce inline reports (not saved files) with this structure:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{TITLE}} Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Target:** [What was analyzed]
**Scope:** [Analysis boundaries]

## Executive Summary

[Brief overview of findings]

## Issue Summary

| Severity | Count |
|----------|-------|
| CRITICAL | X |
| WARNING | X |
| SUGGESTION | X |
| **Total** | **X** |

## Detailed Findings

[Categorized findings]

## Recommendations

[Prioritized action plan]
```

See `references/patterns/output.md` for completion summary format.

<!-- SECTION 7: EXAMPLES -->
## Examples

```
User: /{{COMMAND_NAME}}

Claude:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{TITLE}} Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Target:** [Example target]
**Scope:** [Example scope]

## Executive Summary

Analysis identified 0 critical issues, 2 warnings, and 5 suggestions.
Overall architecture follows best practices with room for minor improvements.

## Issue Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| WARNING | 2 |
| SUGGESTION | 5 |
| **Total** | **7** |

## Detailed Findings

### WARNING Issues (Should Fix)
#### W1. [Example Warning]
[Description and impact]

### SUGGESTION Issues (Nice to Have)
#### S1. [Example Suggestion]
[Description and benefit]

## Recommendations

### Quick Wins
1. [Low-effort improvement]

### Short-term Targets
1. [Medium-effort improvement]
```

<!-- SECTION 8: PERFORMANCE (recommended for analysis) -->
## Performance

**Typical Duration:**
| Input Size | Expected Time |
|------------|---------------|
| Small | 30-60 seconds |
| Medium | 1-3 minutes |
| Large | 3-10 minutes |

**Factors Affecting Performance:**
- [Factor 1: description]
- [Factor 2: description]

**If the command seems stuck:**
1. Check for output activity
2. Wait at least [X] minutes for large inputs
3. If no activity, interrupt and retry with smaller scope

See `references/patterns/logging.md` for performance documentation pattern.

## Execution Instructions

- **DO NOT MAKE ANY CHANGES** - ONLY ANALYZE AND REPORT
- Be specific - cite concrete examples
- Distinguish between severity levels
- Flag areas needing clarification

Begin by analyzing and presenting an executive summary before detailed findings.
