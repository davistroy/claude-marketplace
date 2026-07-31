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
- **Dynamic injections are parse-time, fail-closed, permission-checked, and inversely escaped — read [ADR-0011](docs/adr/0011-dynamic-injection-doctrine.md) before writing or editing one.** A non-zero exit **aborts skill load** (it does not degrade to empty output); the command is permission-checked against `allowed-tools`, so every binary in the pipe must be granted; it expands before `$ARGUMENTS` exists, so an argument-derived placeholder reaches bash literally and must be deleted, not guarded. **The escaping rule is inverted:** the harness blanks an inline-code span *unless* the char before its opening backtick is `` ` `` or `!`, so the tidy double-backtick form is **live** and the ragged nested form is **inert** — always document the syntax as `!`cmd`` (nested). Two shipped components crashed on every invocation because of this (E059). **Any linter for this class must replay the pre-pass, never grep** — 74 textual hits under `plugins/` vs 14 live sites.
- **A `: ` inside an unquoted YAML `description:` silently drops the ENTIRE frontmatter** — colon-space is a mapping indicator in a plain scalar, so the skill loads with empty metadata: `name`, `allowed-tools`, and `disable-model-invocation` all gone, with no crash and no visible symptom. On a D40-protected skill that means it quietly loads **unprotected**. Only `claude plugin validate --strict` catches it ("At runtime this skill loads with empty metadata"); markdownlint, the injection linter, and human reading all pass. Use an em dash, never a colon, in descriptions — the house style already did, which is why the corpus was clean when swept (E061).
- **Documentation of a dynamic injection must NAME the form, never RENDER it.** Writing out the *tidy* double-backtick form in prose to explain it **is** writing a live injection — inside a skill body, aborting skill load on non-zero exit. This is not a novice error: it caught the author of ADR-0011 editing the file ADR-0011 is about, because prose explaining syntax naturally wants to display that syntax. `scripts/check_injections.py` caught it (E061, item 7.3) — the gate's first catch on real unplanted work.
- **Bump the plugin version in the same PR that changes anything under `plugins/<name>/` — otherwise nobody ever gets the change.** `claude plugin update` compares version strings, so an unbumped change leaves two materially different trees under one version and the installed cache reports "already up to date" forever. PR #222 shipped 42 items of behavior change at an unchanged 11.5.1 and every gate was green: version bumping is a `/bump-version` step, not a check; `claude plugin validate --strict` checks manifest *shape*, not *currency*; `update-readme.py --check` is version-blind. The second-order damage is worse than the first — it silently invalidated the next task's eval run, which would have tested pre-change skills against a post-change spec and read as a real finding (#226/E061). Update with `claude plugin update <name>@<marketplace>` (the bare name fails), and before any behavior test verify the installed cache *content*, not its version string.
- **An artifact identified by a LABEL rather than its CONTENT will eventually disagree with itself, silently.** Three instances in two sessions: #226 (two trees under one version string — `claude plugin update` compares strings, so it says "already up to date" forever), #232 (the skill loader served personal-plugin **11.3.0** while `installed_plugins.json` named 11.6.0 as its only entry, so a skill body three versions stale defined the contract a *current* tool's output was parsed against), and #235 (`/implement-plan`'s state file names its plan by **path**, so a completed run's state was inherited by a different plan at the same path — resume would have skipped all 19 PENDING items and reported success). Each is individually silent and produces no error. **Before trusting any cached, installed, or resumed artifact, compare content, not the identifier**: diff the installed cache copy against the repo copy before a behavior test; print the keys a tool actually emits before parsing against a documented contract; fingerprint the plan in any state file.
- **A running session serves the plugin version it resolved at START-UP; `claude plugin update` is for the NEXT process, and says so.** Characterized in E066 (#232) with on-disk evidence: Claude Code writes `.in_use/<pid>` refcount markers into each cache version directory it serves, and the number a live process holds scales with its age — a session started 2026-07-15 pinned **four** personal-plugin versions, one started 2026-07-29 pinned two, one started 2026-07-30 pinned one. The session that filed #232 was itself serving **11.3.0 / bpmn 4.3.1 / slide-gen 1.2.0** — the versions current on the day it started — while `installed_plugins.json` named 11.7.0 / 4.4.0 / 1.4.0 after three updates run *from inside that same session*. `claude plugin update` provisions the *next* process and prints "Restart to apply changes", so this is documented behaviour, **not an upstream loader bug** — #232's premise that the root cause was in Claude Code's loader is wrong. **The remedy is `/reload-plugins`, not necessarily a restart** — measured, not assumed: a `/reload-plugins` re-resolved all three troys-plugins in place and took this session from the 11.3.0 it had served since the previous day to the installed 11.7.0. Markers are **additive and never cleaned up**, which is why the count tracks process age: each re-resolution adds one and removes none. Consequences: (a) a long-lived session can run the **current** bundled tool from repo source while reading a **stale** skill body, which is a current tool against an old contract with no error anywhere; (b) **never prune old cache version directories** — the `.in_use` markers exist to stop the GC deleting a tree a live process is still serving, and #232 listed pruning as a candidate fix that would in fact break running sessions; (c) any skill that parses a bundled tool's structured output must **enumerate the keys the tool actually emitted and halt on an unrecognized one**, never parse for a key list restated in prose — a body predating `orphans` read six keys and silently dropped the seventh. Verify by content, per the rule above; the version string is the label.
- **A Definition-of-Done row is a GATE, not documentation — derive it from what CI actually runs, and negative-test it.** Four DoD rows authored in the E063 plan were wrong the same way: written from what the author expected the command to match. One filtered on `grep -v 'TOKEN'` and only worked because the target line incidentally carried that token — it broke the moment the item legitimately restructured that line. Two used `markdownlint-cli2 "**/*.md"` while **CI runs a different tool** (`markdownlint` from `markdownlint-cli`) with four `--ignore` globs, so they swept gitignored `.venv` files and deliberately-invalid fixtures. One flagged a historical audit report that *quotes* the banned phrase as its own finding. Express the **property** (a leak is output reaching stdout uncaptured and unredirected), never a proxy that correlates today, and run it against a deliberately-bad input before the plan ships.
- **Keep descriptions and skill bodies compact — this is an authoring-quality rule, not a context-economy one.** The harness loads a SKILL.md body only on invocation; the always-loaded surface every turn is the one-line `description` (the harness's own skill-doctor legend says so verbatim). That's why the `description` ≤1024 chars (1536 combined with `when_to_use`) half of this rule has real teeth — put all trigger/proactive-use info there, never a body "Proactive Triggers" section. The SKILL.md body <500 lines half is about keeping instructions scannable and pushing bulk to `references/` so the model reads it on demand when the skill runs — it does not save context on turns that never invoke the skill. `disable-model-invocation: true` (below) is the setting that actually removes the description from session context every turn.
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
- **The bare deep-reasoning trigger word documented at `skills/ultra-plan/SKILL.md:9` is LIVE, not a no-op.** Verified by reading the Claude Code 2.1.220 binary: a case-insensitive, word-bounded matcher runs against the *expanded body* of every command and skill at load and emits a system-reminder requesting deeper reasoning; the exemption guard returns true only for MCP and memory-store sources, so plugin skills and commands are NOT exempt. It is a prompt-level attachment, entirely separate from the `effort` frontmatter field, and the two stack additively — a component can carry both at once. The feature sits behind a server-controllable gate that currently defaults on, so this is current behavior, not a stable contract. Per the name-don't-render lesson (E061): prose that merely *contains* the word inside a skill or command body fires it, so — deliberately, in this very bullet — the mechanism is named, never rendered; never write the literal token in a component body to explain or discuss it. Three in-repo surfaces asserted the old "no-op" claim and are superseded by this entry: `docs/model-optimization-audit-opus5-sonnet5-20260728.md` (a dated historical report, left byte-identical — do not edit it), `LAB_NOTEBOOK.md`'s Entry 067 discussion (corrected in place per Rule 4), and IMPLEMENTATION_PLAN.md Phase 2, which removes the live instances.

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
effort: high                  # low | medium | high | xhigh | max
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

The `commands/`, `skills/` and `agents/` name lists below are generated — run `python3 scripts/update-readme.py` after adding or removing one; CI fails the build if they drift. Every other line in the tree is hand-written and is left alone by the generator.

<!-- BEGIN:inventory -->
```
plugins/
  personal-plugin/
    .claude-plugin/plugin.json
    commands/ (23)     # analyze-transcript, arch-review-single, arch-synthesize, ask-questions,
                       # assess-document, bump-version, clean-repo, consolidate-documents,
                       # convert-markdown, create-plan, define-questions, develop-image-prompt,
                       # finish-document, implement-plan, new-skill, plan-improvements, plan-next,
                       # remove-ip, review-arch, review-intent, scaffold-plugin, test-project,
                       # validate-plugin
    deprecated/        # Archived commands
    skills/ (29)       # accessibility-annotator, arch-review, archive-project, brain-entry,
                       # clear-prep, create-wiki, evaluate-pipeline-output, explain-project,
                       # fleet-health, jetson-audit, jetson-recon, lab-notebook, leak-risk-audit,
                       # new-project, plan-gate, prime, release-plugin, research-topic,
                       # security-analysis, ship, spark-audit, spark-recon, spec-to-prototype,
                       # summarize-feedback, task-sync, ultra-plan, unlock, visual-explainer, wiki
    agents/ (10)       # data-architect, integration-architect, performance-engineer,
                       # platform-engineer, qa-architect, risk-compliance, security-architect,
                       # software-engineer, solutions-architect, sre-operator
    references/        # common-patterns.md, api-key-setup.md, flag-consistency.md,
                       # plan-template.md, research-models.md, validation-maturity-scorecard.md,
                       # adr-template.md, agents-md-template.md, anti-patterns.md,
                       # …plus extraction references (validation-output-examples, ship-output-templates, etc.) and hooks/patterns/templates/ subdirs
    hooks/hooks.json
    tools/             # feedback-docx-generator, visual-explainer

  bpmn-plugin/
    .claude-plugin/plugin.json
    skills/ (2)        # bpmn-generator, bpmn-to-drawio
    references/        # BPMN element docs and guides
    templates/         # XML/Draw.io skeletons
    examples/
    tools/bpmn2drawio/

  slide-gen/
    .claude-plugin/plugin.json
    skills/ (9)        # build-cfa-deck, sg-build, sg-draft, sg-full-workflow, sg-generate-images,
                       # sg-optimize, sg-outline, sg-research, sg-validate-graphics
    references/        # CFA deck helper reference

.claude/
  agents/              # Named implementer agents for implement-plan model routing
                       # haiku-implementer, sonnet-implementer, opus-implementer —
                       # model: tier alias in frontmatter, never pinned IDs (ADR-0005)
```
<!-- END:inventory -->

Two distinct agent surfaces, do not conflate: `plugins/personal-plugin/agents/` ships 9 arch-review domain agents plus `sre-operator` (fleet ops, not part of the arch-review team), while `.claude/agents/` holds only the three `implement-plan` model-routing tiers.

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

- `LAB_NOTEBOOK.md` — Experiment log with decision tracking and action items. Older entries archived to `docs/archive/LAB_NOTEBOOK-E001-E016.md` and `-E017-E050.md`
- `IMPLEMENTATION_PLAN.md` — The **one active** plan; superseded plans are archived to `docs/archive/IMPLEMENTATION_PLAN-v<N>.md` (v4–v12), never deleted. The plan is rewritten in place each cycle, so treat any date or scope in it as current, not historical
- `CHANGELOG.md` — Version history across all plugins
- `docs/adr/` — Accepted architecture decisions; `LAB_NOTEBOOK.md`'s Decision Log is the index

## Deprecated

Retired commands live in `plugins/personal-plugin/deprecated/` with per-command rationale in that directory's `README.md`. None are discoverable by Claude Code — the directory is outside `commands/`.

| Retired | Date | Use instead |
|---------|------|-------------|
| `review-pr` | 2026-04-21 | native `/review`, or `/code-review ultra` for multi-agent deep review |
| `new-command` | 2026-07-08 | `/new-skill --pattern <name>` — skills-first authoring (ADR-0006) |
| `convert-hooks` | 2026-03-04 | Claude Code's native cross-platform hook support |
| `check-updates` | pending | `/validate-plugin --check-updates` |
| `setup-statusline` | pending | Claude Code's built-in status line configuration |

Also retired, though never a command: the **per-plugin `skills/help/` requirement** of ADR-0004, dropped by D42 (2026-07-16) in favor of native `/help`. No plugin ever implemented it; `scripts/generate-help.py` and its pre-commit check are gone. Any doc or test still asserting a plugin ships `skills/help/SKILL.md` is stale.

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
