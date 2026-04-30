## Learning Capture — Every Session

After any non-trivial finding (plugin discovery failure, frontmatter requirement, directory structure requirement, Python tool invocation issue, multi-attempt fix):
1. Update `CLAUDE.md` — add/update bullet in relevant section
2. Update memory file — `C:\Users\Troy Davis\.claude\projects\C--Users-Troy-Davis-dev-personal-claude-marketplace\memory\`
3. Update `MEMORY.md` — concise bullet + link to topic file

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Operational rules, always enforced |
| `memory/MEMORY.md` | Concise index, survives compaction |
| `memory/plugin-structure-learnings.md` | Discovery failures, frontmatter, directory layout |
| `memory/marketplace-learnings.md` | Install behavior, versioning, namespace collisions |
| `memory/tool-integration-learnings.md` | Python tool invocation, PYTHONPATH, deps |

### Verified Operational Rules

- **Skills MUST use nested directory structure** — `skills/name/SKILL.md` not `skills/name.md`. Flat files not discovered.
- **Skills MUST have `name` in frontmatter** — without it the skill is not registered.
- **Commands MUST NOT have `name` in frontmatter** — adding `name` prevents command discovery.
- **Do NOT add `tools` field to plugin.json** — causes "Unrecognized key: tools" error.
- **Do NOT add `"hooks"` field to plugin.json** — Claude Code auto-loads `hooks/hooks.json`. Declaring it causes "Duplicate hooks file detected" error.

---

# CLAUDE.md

## Project Overview

Claude Code plugin marketplace. Multiple plugins extending Claude Code with specialized workflows.

## Marketplace Installation

```
/plugin marketplace add davistroy/claude-marketplace
/plugin install personal-plugin@troys-plugins
/plugin install bpmn-plugin@troys-plugins
```

Scopes: `--scope user` (global), `--scope project` (team), `--scope local` (personal/gitignored)

## CRITICAL: Structure Requirements

All changes must maintain compatibility with `/plugin marketplace add`. Structure is NOT arbitrary.

### Required Layout

```
.claude-plugin/
  marketplace.json          # REQUIRED: Claude Code reads this first

plugins/
  [plugin-name]/
    .claude-plugin/
      plugin.json           # REQUIRED: name, version, description
    commands/               # Slash commands (*.md files, flat)
    skills/                 # Proactive skills (nested dirs with SKILL.md)
      [skill-name]/
        SKILL.md            # REQUIRED: Must be exactly SKILL.md (uppercase)
```

| Component | Structure | Example |
|-----------|-----------|---------|
| Commands | Flat: `commands/name.md` | `commands/validate-plugin.md` |
| Skills | Nested: `skills/name/SKILL.md` | `skills/ship/SKILL.md` |

### What Must NOT Change

| Item | Why |
|------|-----|
| `.claude-plugin/marketplace.json` location | Claude Code expects at repo root |
| `plugins/[name]/.claude-plugin/plugin.json` location | Standard plugin metadata |
| Marketplace name `troys-plugins` | Users reference in install commands |
| Plugin names in marketplace.json | Must match directory names exactly |

### Testing

```
/plugin marketplace add davistroy/claude-marketplace
/plugin install personal-plugin@troys-plugins
/help    # If commands show, marketplace integration works
```

## Skill Frontmatter

```yaml
---
name: ship                    # REQUIRED: Must match directory name
description: Brief description
argument-hint: "<branch-name> [draft]"
effort: high                  # low/medium/high/max
disable-model-invocation: true
allowed-tools: Bash(git:*)
---
```

- `name` — REQUIRED, must match directory name
- `description` — REQUIRED

Optional: `argument-hint`, `effort`, `disable-model-invocation`, `allowed-tools`, `context`, `agent`, `version`, `license`

## Command Frontmatter

```yaml
---
description: Brief description
argument-hint: "<required-arg> [--optional-flag]"
effort: high
allowed-tools: Bash(git:*)
---
```

**Do NOT include `name` field** — filename determines command name.

## Repository Structure

```
plugins/
  personal-plugin/
    .claude-plugin/plugin.json
    commands/          # analyze-transcript, arch-review-single, arch-synthesize, ask-questions,
                       # assess-document, bump-version, clean-repo, consolidate-documents,
                       # convert-markdown, create-plan, define-questions, develop-image-prompt,
                       # finish-document, implement-plan, new-command, new-skill, plan-improvements,
                       # plan-next, remove-ip, review-arch, review-intent, scaffold-plugin,
                       # test-project, validate-plugin
    deprecated/        # Archived commands
    skills/            # accessibility-annotator, arch-review, brain-entry, create-wiki,
                       # evaluate-pipeline-output, explain-project, jetson-audit, jetson-recon,
                       # lab-notebook, leak-risk-audit, plan-gate, prime, release-plugin,
                       # research-topic, security-analysis, ship, spark-audit, spark-recon,
                       # spec-to-prototype, summarize-feedback, ultra-plan, unlock,
                       # visual-explainer, wiki
    references/        # common-patterns.md, api-key-setup.md, flag-consistency.md,
                       # plan-template.md, research-models.md, validation-maturity-scorecard.md
    hooks/hooks.json
    tools/             # feedback-docx-generator, visual-explainer

  bpmn-plugin/
    .claude-plugin/plugin.json
    skills/            # bpmn-generator, bpmn-to-drawio
    references/        # BPMN element docs and guides
    templates/         # XML/Draw.io skeletons
    examples/
    tools/bpmn2drawio/
```

## Command Patterns

| Pattern | Commands |
|---------|---------|
| Read-only | `review-arch`, `assess-document`, `review-intent` |
| Interactive | `ask-questions`, `finish-document` |
| Generator | `define-questions`, `analyze-transcript` |
| Planning | `create-plan`, `plan-improvements`, `plan-next` |
| Orchestration | `implement-plan` — Agent tool subagents, state file resume, rollback/checkpoint, phase gates |
| Scaffolding | `scaffold-plugin`, `new-command`, `new-skill` |

**Planning commands:** Both `create-plan` and `plan-improvements` produce unified IMPLEMENTATION_PLAN.md schema (max 8 phases, max 6 items/phase). `create-plan` adds codebase recon + scope confirmation. `plan-improvements` adds sampling strategy, priority rubric, `--recommendations-only` workflow.

**`implement-plan`:** Creates PR by default (merge only with `--auto-merge`). Supports `--input`, `--pause-between-phases`, `--progress`.

### Output Conventions

- Files: `[type]-[source]-YYYYMMDD-HHMMSS.json` or `.md`
- Analysis reports → `reports/`
- Reference data → `reference/`
- Generated docs → same dir as source
- Temp files → `.tmp/` (auto-cleaned)

## BPMN Plugin

**`/bpmn-generator`:** Interactive mode (NL → structured Q&A) or document parsing mode (markdown path → extract process elements).

**`/bpmn-to-drawio`:** BPMN 2.0 XML → Draw.io native format. **CRITICAL:** Edges crossing lane boundaries must have `parent="1"` (root level) with absolute `mxPoint` coordinates.

## Bundled Python Tools

Run from source via `PYTHONPATH` — do NOT declare in plugin.json `tools` field.

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/my-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/my-tool/src"
PYTHONPATH="$TOOL_SRC" python -m my_tool_module <arguments>
```

**Python Version:** 3.10+

**Tool structure:**
```
tools/[tool-name]/
  pyproject.toml
  src/[tool_module]/
    __init__.py
    __main__.py    # Entry point for `python -m [tool_module]`
    cli.py
```

**Dependency check pattern:**
```bash
python -c "import package_name" 2>/dev/null || echo "package_name: MISSING"
# Prompt user before installing
```

## Adding New Plugins

1. Create `plugins/[name]/`
2. Add `.claude-plugin/plugin.json`
3. Add `commands/` (flat .md files) and `skills/` (nested dirs with SKILL.md)
4. Register in `.claude-plugin/marketplace.json`
5. Run `/validate-plugin [plugin-name]`

## Versioning

**Marketplace version** (`marketplace_version` in marketplace.json): schema changes, shared tooling, repo-wide docs. NOT bumped for individual plugin updates.

**Plugin versions** (each plugin's plugin.json + marketplace.json): `/bump-version [plugin-name] [major|minor|patch]`

## Namespacing

| Format | When to Use |
|--------|-------------|
| `/review-arch` | Works if only one plugin has this command |
| `/personal-plugin:review-arch` | Required if name collision exists |

`/validate-plugin --all` detects naming collisions.

## Key References

- `LAB_NOTEBOOK.md` — Experiment log with decision tracking and action items
- `IMPLEMENTATION_PLAN.md` — Current/completed implementation plan (v8.0.0 modernization)
- `CHANGELOG.md` — Version history across all plugins

## Deprecated

- `review-pr` (deprecated 2026-04-21) — use native `/review` for standard PR review or `/ultrareview` for multi-agent deep review

---

## Lab Notebook — MANDATORY Logging Protocol

**LAB_NOTEBOOK.md is the permanent experiment record for this project. The following rules are NON-NEGOTIABLE and have the HIGHEST PRIORITY after user safety.**

### Rule 1: Hypothesize, Plan Rollback, THEN Act

Before executing ANY system-modifying action, you MUST add an entry to LAB_NOTEBOOK.md with:
- **Objective:** What you're trying to achieve
- **Hypothesis:** What you expect to happen and why. Include measurable success criteria. Even simple expectations count: "Expect plugin reinstall to sync spark-recon to repo version."
- **Rollback Plan:** How to undo this change. For read-only operations, state "N/A — read-only." For destructive operations, this is CRITICAL — document the undo BEFORE you do the thing.

This applies to: plugin structure changes, template modifications, skill/command rewrites, hook changes, marketplace.json edits, and any action that could break plugin discovery or execution.

**If you catch yourself about to run a command without an entry: STOP. Create the entry first. No exceptions.**

### Rule 2: Log Results As They Happen

Update the entry immediately after each action with:
- The exact command or operation performed
- The result: success, failure, or unexpected behavior
- Raw error output for failures — not just "it failed" but the actual message
- Performance numbers with units, conditions, and comparison to baseline
- Environment context: which plugin version, marketplace version, Claude Code version was active

Do NOT batch-log multiple actions after the fact. Log each one as it completes.

### Rule 3: Analyze Failures — Root Cause, Not Symptoms

Failed attempts are MORE valuable than successes. For every failure:
- **Exact error:** The literal message or behavior observed
- **Root cause:** WHY it failed — trace to the underlying reason
- **System insight:** What this failure reveals about how the system works
- **Next approach:** What to try differently based on this understanding
- **Pattern recognition:** If this is the same class of failure as a previous entry, create or update a pattern table

### Rule 4: Document Decisions with Alternatives

Every decision must include:
- **The decision itself** and WHY it was made
- **Alternatives considered** — what other options were evaluated, with their trade-offs
- **Update the Decision Log table** at the top of LAB_NOTEBOOK.md (Decision, Status=ACTIVE, Entry reference, Alternatives)

When revisiting a previous decision: update the old decision's status to SUPERSEDED and reference the new entry. Never delete old decisions.

Bad: "Changed the template field"
Good: "Consolidated `Parallelizable` and `Execution Mode` into a single field. `Execution Mode` is strictly more expressive (Sequential/Parallel/Worktree-Isolated vs Yes/No). Alt: keep both — rejected because two fields carrying the same signal adds confusion without value."

### Rule 5: Track What Worked, Not Just What Failed

Include a "What Worked" section in entries with mixed outcomes. Successes establish positive patterns:
- Which approaches are reliable
- Which template structures are stable
- What the plugin loader handles well

This prevents drift toward excessive caution — not everything is a problem to solve.

### Rule 6: Write Before Risky Operations

Before any operation that could crash the session, corrupt state, or take a long time:
- Flush ALL current findings to LAB_NOTEBOOK.md
- Include intermediate results, even if incomplete
- Update the Decision Log and Action Items tables
- If the session crashes, the next session must be able to continue from LAB_NOTEBOOK.md alone

### Rule 7: Maintain Living Sections

After EVERY completed entry, update the living sections at the top of LAB_NOTEBOOK.md:
- **Decision Log:** Add new decisions, update superseded ones
- **Action Items:** Add follow-ups from the entry, mark completed items

These tables are the "dashboard" — they must always reflect the current state.

### Rule 8: Tag and Contextualize Every Entry

Every entry must have:
- **Tags** in the title line — for searchability. Use project tags: `[plugin]` `[template]` `[skill]` `[command]` `[hooks]` `[ci]` alongside standard tags: `[config]` `[decision]` `[debug]` `[build]` `[cleanup]` `[init]`
- **Environment** field: which plugin version, marketplace version, git state. Critical for reproducibility.
- **Duration** (when completed): how long the work took. Helps estimate future work.

### Rule 9: Pattern Tables for Repeated Issues

When failures share a root cause or pattern, consolidate them into a table:

| Attempt | Error | Root Cause | Fix |
|---------|-------|-----------|-----|
| ... | ... | ... | ... |

This transforms individual failures into systematic understanding.

### Rule 10: Session Boundaries

When starting a new session on a project with an existing notebook, add a session boundary marker before your first entry:

`--- New session: {date} — {brief context of what this session will focus on} ---`

This traces context switches between sessions and helps explain gaps, changes in approach, or fresh perspectives. Read the Decision Log and Open Action Items before starting work — they are your orientation to current state.

### Rule 11: Log Before You Commit

**BLOCKING PRECONDITION on `git commit`:** Before every commit that touches application code (not just docs), the LAB_NOTEBOOK.md must have a current entry covering what you're about to commit. If the entry doesn't exist yet, create it before staging files. One entry can cover multiple related commits, but the entry must be written BEFORE the first commit in that sequence, not after.

This is the rule that prevents batching. It's easy to skip a "log results" step. It's harder to skip when the log IS the commit workflow.

### Enforcement

These rules are BLOCKING PRECONDITIONS, not suggestions. The mechanical process is:
1. Create/update entry with Hypothesis + Rollback Plan
2. Execute the action
3. Log the result immediately
4. **Before `git commit`: verify the notebook entry exists and covers this change**
5. Update Decision Log and Action Items if applicable
6. Repeat

There are NO exceptions for "quick" changes, "obvious" fixes, or "simple" tests. The cost of logging is seconds. The cost of NOT logging is hours of forensic reconstruction when a session crashes.
