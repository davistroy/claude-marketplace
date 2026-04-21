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
    commands/          # analyze-transcript, ask-questions, assess-document, bump-version,
                       # clean-repo, consolidate-documents, convert-markdown, create-plan,
                       # define-questions, develop-image-prompt, finish-document, implement-plan,
                       # new-command, new-skill, plan-improvements, plan-next, remove-ip,
                       # review-arch, review-intent, scaffold-plugin, test-project,
                       # validate-plugin
    deprecated/        # Archived commands
    skills/            # plan-gate, prime, research-topic, security-analysis, ship,
                       # summarize-feedback, unlock, release-plugin, evaluate-pipeline-output,
                       # visual-explainer, leak-risk-audit, spec-to-prototype,
                       # accessibility-annotator, brain-entry, explain-project, lab-notebook,
                       # spark-recon, ultra-plan
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

## Deprecated

- `review-pr` (deprecated 2026-04-21) — use native `/review` for standard PR review or `/ultrareview` for multi-agent deep review
