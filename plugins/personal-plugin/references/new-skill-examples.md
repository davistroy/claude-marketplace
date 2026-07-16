# New Skill Generator — Worked Examples

Three fully worked example `SKILL.md` files produced by `/new-skill`, referenced from the command's "Frontmatter Field Reference" section. Each demonstrates a different combination of modern frontmatter fields.

## Example A — Basic Skill (no modern features)

Suitable for: simple in-context analysis, no disk writes, no parallelism needed.

```yaml
---
name: check-deps
description: Audit package.json dependencies for outdated or insecure packages
argument-hint: "[--fix]"
effort: medium
allowed-tools: Read, Bash(npm:*)
---

# Dependency Checker

Audits the project's npm dependencies and reports outdated or vulnerable packages.

## Input

**Arguments:** `$ARGUMENTS` — pass `--fix` to auto-upgrade safe patches.

## Instructions

### Phase 1: Collect dependency info

Run `npm outdated` and `npm audit --json`. Parse JSON output.

### Phase 2: Report

Summarize: outdated count, critical vulns, high vulns. List top-5 most outdated.
If `--fix` in $ARGUMENTS: run `npm audit fix` (safe patches only).

## Output

In-conversation summary table. If --fix: updated package-lock.json.
```

---

## Example B — Fork-to-Explore Skill with Dynamic Injection

Suitable for: read-heavy analysis that shouldn't pollute parent context; pre-loading expensive git/file data before Claude reads the prompt.

```yaml
---
name: code-health
description: Analyze codebase health — complexity, test coverage gaps, stale TODOs
effort: high
allowed-tools: Read, Glob, Grep, Bash
context: fork
agent: Explore
---

# Code Health Analyzer

!`git log --oneline -20`
!`git shortlog -sn --no-merges | head -10`
!`find . -name "*.ts" -o -name "*.py" | wc -l`
!`grep -r "TODO\|FIXME\|HACK" --include="*.ts" --include="*.py" -l | head -20`

The above commands ran before you read this prompt. Use their output in your analysis.

## Instructions

This skill runs in an isolated context (`context: fork`, `agent: Explore`).
You have no access to prior conversation — analyze the project from scratch.

### Phase 1: Complexity hotspots

Read the 5 largest source files (by line count from Glob). Flag functions > 50 lines.

### Phase 2: Test coverage gaps

Find source files with no matching test file. List by directory.

### Phase 3: TODO/FIXME inventory

Use the grep output injected above. Categorize by severity (HACK > FIXME > TODO).

## Output

Structured report written to `reports/code-health-YYYYMMDD.md`. Summary in conversation.
```

**Key patterns demonstrated:**

- `` !`cmd` `` blocks at top of body — run before Claude reads the prompt
- `context: fork` isolates the analysis from conversation history
- `agent: Explore` selects the broad read-only analysis persona

---

## Example C — Paths-Activated Skill with Loop Guard

Suitable for: skills that should auto-run when specific files change (e.g., dependency manifests, config files, baseline docs).

```yaml
---
name: validate-config
description: Validate app config schema whenever config files change
allowed-tools: Read, Bash
paths:
  - "config/**/*.json"
  - "config/**/*.yaml"
  - ".env.example"
---

# Config Validator

Auto-activates when a config file changes. Validates schema, required keys, and type correctness.

## Instructions

### Entry guard (REQUIRED for paths-activated skills)

Check: has this skill run in the last 5 minutes (look for a recent entry in LAB_NOTEBOOK.md
or a sentinel file `.tmp/validate-config.last-run`)? If yes → exit immediately.
This prevents infinite re-entry if the skill itself writes to a config path.

Write sentinel: `echo $(date +%s) > .tmp/validate-config.last-run`

### Phase 1: Detect changed files

Identify which config file triggered activation from `$CLAUDE_CONTEXT`.
If no context: scan `config/` for recently modified files (`find config/ -newer .tmp/validate-config.last-run`).

### Phase 2: Validate schema

Read the changed file. Compare against the schema definition in `config/schema.json`.
Report: PASS / FAIL with specific field-level errors.

### Phase 3: Check required keys

Cross-reference against required key list in `config/required-keys.txt`.
Flag any missing required keys as CRITICAL.

## Output

In-conversation validation report. Does NOT modify the config file (read-only).
```

**Key patterns demonstrated:**

- `paths:` frontmatter for auto-activation
- Loop guard at skill entry (mandatory for any paths-activated skill)
- `$CLAUDE_CONTEXT` to identify which file triggered the activation
