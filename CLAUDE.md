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
- **Skills MUST have `name` in frontmatter (house convention)** — the 2026 platform spec makes `name` optional (defaults to the dir name); this repo requires it explicitly for dispatch clarity and directory-name consistency (ADR-0006).
- **New functionality ships as skills; `commands/` is frozen legacy** — maintained, not extended. Scaffold new work with `/new-skill` (ADR-0006).
- **Commands MUST NOT have `name` in frontmatter** — adding `name` prevents command discovery.
- **Do NOT add `tools` field to plugin.json** — causes "Unrecognized key: tools" error.
- **Do NOT add `"hooks"` field to plugin.json** — Claude Code auto-loads `hooks/hooks.json`. Declaring it causes "Duplicate hooks file detected" error.
- **Agent `model:` frontmatter uses tier aliases, never pinned IDs** — `haiku`/`sonnet`/`opus`/`fable`/`inherit` resolve at dispatch time so pins can't silently go stale (ADR-0005).
- **Keep descriptions and skill bodies compact** — `description` ≤1024 chars (1536 combined with `when_to_use`), with all trigger/proactive-use info there, never a body "Proactive Triggers" section; SKILL.md body <500 lines, bulk moved to `references/`.
- **Always `git fetch` + check `origin/main` divergence before trusting any version state** — the local working tree can silently lag origin even when `git status` shows clean. Happened twice (LAB_NOTEBOOK.md Entry 006/D17, Entry 007/D19 -- archived, see `docs/archive/LAB_NOTEBOOK-E001-E016.md`; D17/D19 remain in the live Decision Log), both times causing wrong version-bump math or a stale baseline. Version source of truth is always `origin/main`, never local HEAD.
- **A verification guard that can't fail is worse than none — negative-test every new gate before wiring it in.** It converts "unchecked" into a false "checked". Three 2026-07-17 issues were exactly this: `update-readme.py --check` exited 0 for ANY drift (dead glob + stale anchor), the eval check validated mapping only (not structure), the pre-commit hook was uninstalled with a dead `help.md` check inside. Before trusting/wiring any guard: run it against deliberately-bad input and confirm it exits non-zero (E043 -- archived along with E040/E042, see `docs/archive/LAB_NOTEBOOK-E017-E050.md`).
- **A check that restates an external truth will drift into agreeing with the bug — derive it, don't copy it.** The sibling of the rule above: that one is about guards that *can't* fail, this one is about guards that *do* run, pass, and are wrong. Three instances (2026-07-28/29), all at high coverage: `test_priority_round_trip` was parametrized over a hardcoded `["P1".."P4"]` that had drifted from `VALID_PRIORITIES` alongside the defect, so the missing `P0` path was never exercised — `mapping.py` reported **100%** while the bug shipped (#208/E056); `test_update_issue_clears_milestone` asserted `--remove-milestone`, **a `gh` flag that does not exist**, and passed for the tool's whole life because `subprocess.run` is mocked, while `sync --apply` crashed on every real push — `github.py` at **92%** (#212/E057). **Parametrize from the constant, never a copy of it; always include an out-of-set value** (bugs of this class live entirely in the unrecognized-value branch); and when mocking a CLI/API, verify the argv or payload against the real tool at least once. Safe probe: target a nonexistent resource so the request 404s and mutates nothing (`gh api repos/<r>/issues/99999999 -X PATCH -F k=v --verbose` prints the outgoing body) — that is how `-F milestone=null` (JSON null) vs `-f` (the string `"null"`) was settled without guessing.
- **Skill `name` MUST equal the directory name**, enforced in BOTH `validate.yml` and `scripts/pre-commit` (E043 reconciled them — validate.yml's skills branch had been dead code because its glob was non-recursive). Never resolve a validator disagreement by stripping `name`; `claude plugin validate --strict` (which requires `name`) is the tiebreaker.
- **`docs/archive/` is matched by the global `~/.gitignore_global` `archive/` rule** — new files there are silently skipped by `git add`. Use `git add -f` (the v4–v9 + LAB_NOTEBOOK archives are all force-added). A plain `git add -A` will omit them without warning (E040/E043).
- **Add a STEP to an existing CI job, don't add a JOB, when you can** — a new step keeps the required-check name (safe under branch protection); a new job creates a new required check that must be coordinated with branch-protection settings or it deadlocks merges (PLAT-012/D28). The README-sync and eval checks were added as steps in the existing `Validate Plugins (official CLI)` job for this reason (E043).
- **Lint long markdown before you COMMIT it, not before you push — and know the two traps `--fix` cannot repair.** The 924-line E052 audit report was committed to a branch entirely unlinted and failed 14 rules; the red only surfaced when someone tried to land it (E053/PR #207). (a) **MD052** — adjacent brackets are reference-link syntax, so tag-style labels like `[stale-model][ADR-0005]` read as links to undefined labels; fix by inserting a space (separated brackets are *shortcut* refs, which MD052 skips by default), after confirming the file defines no real reference links via `grep -nE '^\[[^]]+\]:'`. (b) **MD018** — a line starting `#183 …` parses as an ATX heading, which will recur in LAB_NOTEBOOK entries that open a paragraph with an issue number; lead with bold or prose instead.
- **`gh issue view <n>` silently resolves PULL REQUEST numbers.** It renders a PR as though it were an issue, with no warning — so establishing an issue range by number turns open Dependabot PRs into phantom backlog items (#186/#187/#188 were misread as part of the E052 audit set, which is actually #189–#206). `gh issue list` is correct; it omits PRs. Derive ranges from `list`, never from `view` in a loop.
- **A LAB_NOTEBOOK entry on an unmerged branch does not exist.** Rule 6's "next session can resume from the notebook alone" guarantee is against `main`, not the union of all branches. E052/E053 were fully written but sat unmerged, so `main` showed 18 issues appearing after E051 with no explanation, and the next session was briefed to write entries that already existed. Land docs branches as promptly as code branches; before writing an entry for seemingly-undocumented work, check `git log --oneline main..origin/<branch>` first.
- **Promote body-only Decision Log entries to the table before archiving/rotating the notebook** — D14–D18 lived only in entry bodies (a Rule 7 lapse) and a naive rotation would have silently deleted five decisions and orphaned an Accepted ADR's cited precedent. Rotate only after the Decision Log is complete and gapless; rotation is a MOVE (banner + bidirectional pointers), never a delete (Rule 4, D-none/E042/E043).

---

# CLAUDE.md

## Project Overview

Claude Code plugin marketplace. Multiple plugins extending Claude Code with specialized workflows.

## Marketplace Installation

```
/plugin marketplace add davistroy/claude-marketplace
/plugin install personal-plugin@troys-plugins
/plugin install bpmn-plugin@troys-plugins
/plugin install slide-gen@troys-plugins
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

Optional: `argument-hint`, `effort`, `disable-model-invocation`, `allowed-tools`, `context`, `agent`, `version`, `license`, `when_to_use`, `arguments`, `user-invocable`, `disallowed-tools`, `shell`

`disable-model-invocation: true` also removes the description from session context — use for side-effect-only skills that should never be proactively suggested.

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
    commands/ (23)     # analyze-transcript, arch-review-single, arch-synthesize, ask-questions,
                       # assess-document, bump-version, clean-repo, consolidate-documents,
                       # convert-markdown, create-plan, define-questions, develop-image-prompt,
                       # finish-document, implement-plan, new-skill, plan-improvements,
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
                       # plan-template.md, research-models.md, validation-maturity-scorecard.md,
                       # adr-template.md, agents-md-template.md, anti-patterns.md,
                       # …plus extraction references (validation-output-examples, ship-output-templates, etc.) and hooks/patterns/templates/ subdirs
    hooks/hooks.json
    tools/             # feedback-docx-generator, visual-explainer

  bpmn-plugin/
    .claude-plugin/plugin.json
    skills/            # bpmn-generator, bpmn-to-drawio
    references/        # BPMN element docs and guides
    templates/         # XML/Draw.io skeletons
    examples/
    tools/bpmn2drawio/

  slide-gen/
    .claude-plugin/plugin.json
    skills/            # sg-research, sg-outline, sg-draft, sg-optimize,
                       # sg-validate-graphics, sg-generate-images, sg-build, sg-full-workflow

.claude/
  agents/              # Named implementer agents for implement-plan model routing
                       # haiku-implementer, sonnet-implementer, opus-implementer —
                       # model: tier alias in frontmatter, never pinned IDs (ADR-0005)
```

## Command Patterns

| Pattern | Commands |
|---------|---------|
| Read-only | `review-arch`, `assess-document`, `review-intent` |
| Interactive | `ask-questions`, `finish-document` |
| Generator | `define-questions`, `analyze-transcript` |
| Planning | `create-plan`, `plan-improvements`, `plan-next` |
| Orchestration | `implement-plan` — Agent tool subagents, state file resume, rollback/checkpoint, phase gates |
| Scaffolding | `scaffold-plugin`, `new-skill` |

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
3. Add `skills/` (nested dirs with SKILL.md) — default; `commands/` (flat .md files) only for the frozen-legacy format (ADR-0006)
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
- `IMPLEMENTATION_PLAN.md` — Current/completed implementation plan (planning-pipeline gap-analysis upgrade, completed 2026-04-30)
- `CHANGELOG.md` — Version history across all plugins

## Deprecated

- `review-pr` (deprecated 2026-04-21) — use native `/review` for standard PR review or `/code-review ultra` for multi-agent deep review

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

### Rule 12: Rotate When Large

The notebook is read in full by CLAUDE.md and `/prime`, so it must stay bounded. When the Experiment Log exceeds **~40 entries or LAB_NOTEBOOK.md exceeds ~1200 lines**, run `/lab-notebook rotate` to archive the oldest entries to `docs/archive/` (keeping the living sections + the last ~20 entries). Rotation is a MOVE, never a delete (Rule 4): **promote any body-only decisions to the Decision Log table BEFORE archiving their entries** (a naive cut nearly lost D14–D18), cut only at a session-marker boundary, and `git add -f` the archive (`docs/archive/` is gitignored). Full procedure: `plugins/personal-plugin/skills/lab-notebook/references/rotation.md`.

### Enforcement

These rules are BLOCKING PRECONDITIONS, not suggestions. The mechanical process is:
1. Create/update entry with Hypothesis + Rollback Plan
2. Execute the action
3. Log the result immediately
4. **Before `git commit`: verify the notebook entry exists and covers this change**
5. Update Decision Log and Action Items if applicable
6. Repeat

There are NO exceptions for "quick" changes, "obvious" fixes, or "simple" tests. The cost of logging is seconds. The cost of NOT logging is hours of forensic reconstruction when a session crashes.
