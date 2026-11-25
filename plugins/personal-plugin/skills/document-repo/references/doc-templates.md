# Documentation templates

Every generated block of documentation sits between two marker lines and is written with `upsert-section`:

```bash
PYTHONPATH="{TOOL_SRC}" python3 -m document_repo upsert-section --file <file> --section <name> --content-file <tmp.md>
```

Run the command as written in your prompt, with `{TOOL_SRC}` already filled in. Do not rely on a `$TOOL_SRC` variable: a subagent's shell does not have it, and no shell keeps variables between Bash calls.

Write the body to a temporary file under the run directory first. The command prints nothing and exits 0 on success. On failure it prints `upsert-section: <reason>` to stderr and exits 2.

The tool replaces only the text between `<!-- document-repo:start:<name> -->` and `<!-- document-repo:end:<name> -->`. When the markers are absent it appends the section at the end of the file after one blank line. It creates a missing file and its parent directories. Every byte outside the markers, including CRLF line endings and trailing blank lines, comes back unchanged. Never merge or rewrite human text yourself.

## Sections

Section names are fixed. A name matches `[a-z0-9][a-z0-9-]*`.

| File | Section names, in the order to write them |
|------|-------------------------------------------|
| `README.md` (root) | `overview`, `quick-start`, `repo-map`, `explorer` |
| `<module path>/README.md` | `module` |
| `AGENTS.md` | `agents` |
| `docs/ARCHITECTURE.md` | `architecture` |
| `docs/GLOSSARY.md` | `glossary` |
| `CLAUDE.md` (only if it exists) | `agents-pointer` |

Write a module README for every module with status `analyzed`, except the root module (path `.`), which has no directory of its own. A `not_analyzed` module gets none.

## Rules for every body

1. **Copy text from the model.** Placeholders in angle brackets below are model fields. Do not add a claim the model does not hold.
2. **Never write a marker string.** A body must not contain `document-repo:start:` or `document-repo:end:` anywhere, not even inside a code fence. The tool refuses it.
3. **Close every code fence.** An unclosed fence hides the end marker, and the next `upsert-section` on that file fails with "the code fence opened on line N is never closed". If the text inside a fence contains a run of three or more backticks, open the fence with a longer run. Fences must also balance in the file you are writing into. If the tool reports an unclosed fence in an existing file, stop, report the file and line, and leave it alone.
4. **A marker counts only when it is alone on its line and outside a code fence.** A README that shows a marker in a fenced example, or mentions one in a sentence, is not mistaken for a section.
5. **Keep the H1 when the file is new or already holds this section's start marker.** Each template below starts with its H1 where it has one. A file with the marker was made by an earlier run, so keep the H1 and each run writes the same text. Drop the H1 only when the file exists with its own title and has no start marker for this section.
6. **Do not cite line numbers.** Lines shift with every code change, and nothing rewrites the docs when they do. Cite file paths. The explorer carries the line links. The one exception is an `agent_notes.traps` item, which keeps the `path:line` the model gives it.
7. **Links are relative to the file you are writing.** From the root, `src/api/README.md`. From `docs/`, `../src/api/README.md`. From `src/api/README.md` to the `db` module, `../../db/README.md`. Link to a module README only when that module has one; otherwise write its name without a link.
8. **Write through symlinks knowingly.** `upsert-section` resolves a symlink and writes the target, so `CLAUDE.md -> AGENTS.md` would receive the pointer inside `AGENTS.md` itself. Check `CLAUDE.md` first. If it resolves to the same file as `AGENTS.md`, skip `agents-pointer`.
9. Inline code in the model uses single backticks. Keep them.

## Root README

Four sections, written in this order. The H1 follows rule 5.

| Section | Contents |
|---------|----------|
| `overview` | `# <project.name>` (when rule 5 keeps it), then "What this is" and "What it can do" |
| `quick-start` | "Quick start" |
| `repo-map` | "Repo map" |
| `explorer` | "Explore it" |

```markdown
# <project.name>

## What this is
<project.purpose.functional>

<project.purpose.technical>

## What it can do
- **<capability.title>** — <capability.functional>
```

```markdown
## Quick start
<project.run.setup as a numbered list, one item per step>

<for each project.run.commands entry: its label on one line, then the command in a fenced bash block>
```

```markdown
## Repo map
| Path | What lives there |
|------|------------------|
| `<module.path>/` | <module.purpose.functional> ([README](<module.path>/README.md)) |
```

```markdown
## Explore it
Open [`explorer/index.html`](explorer/index.html) in a browser for an
interactive tour: architecture, modules, step-by-step flows, and a glossary.
It works offline and needs no server.
```

In `repo-map`, give the root module's row no path link and no README link. Give a `not_analyzed` module's row no README link.

## Module README

Body of the `module` section in `<module.path>/README.md`.

```markdown
# <module.name>

<module.purpose.functional>

## How it works
<module.purpose.technical>

## Public interface
| Name | Kind | What it does | Where |
|------|------|--------------|-------|
| `<interface.name>` | <interface.kind> | <interface.description> | `<interface.file>` |

## Rules that must stay true
- <each invariant>

## Depends on
- Internal: <relative links to the README of each module in dependencies.internal>
- External: <dependencies.external>

## Key files
| File | Role |
|------|------|
| `<key_file.path>` | <key_file.role> |

## Flows that pass through here
- <flow.title> — in the explorer: `explorer/index.html#/tours/<flow.id>`
```

A flow passes through a module when at least one of its steps has a `file` under the module's path. The explorer uses the same rule. Leave out a heading whose list would be empty, except "Public interface", which says "No public interface." in that case.

## AGENTS.md

Body of the `agents` section.

```markdown
# AGENTS.md

Guide for AI coding agents working in this repo. Humans: start at README.md.

## Repo map
<one table row per module: path, one-line purpose>

## Entry points
<one line per entry point: its name, its file, and what it starts>

## Commands
<agent_notes.commands: each label, then its command in a fenced block>

## Rules
- <each agent_notes.rules item>

## Traps
- <each agent_notes.traps item, whole, with its path:line reference>

## Do not touch
| Path | Why |
|------|-----|
| `<do_not_touch.path>` | <do_not_touch.reason> |

## Conventions in the code
File headers use the labels `Role:`, `Used by:`, `Inputs:`, `Outputs:`,
`Side effects:`, `Invariants:`, `Traps:`. Grep for them.

## Full model
The machine-readable project model is `explorer/data/model.json`
(schema version <meta.schema_version>). Its `meta.source_commit` names the
commit that its line numbers refer to.
```

Copy each trap whole: what looks safe, what actually happens, what to do instead, and the `path:line` at its end. Do not shorten a trap to a phrase.

Take entry points from two sources only. The first is the `interface` items in `model.json` whose `kind` is `command` or `route`. The second is the `entry_candidates` in `inventory.json` whose `why` is not "conventional entry-point name" (a package main, bin or script, a console script, a container definition). No model field records that an analyst confirmed an entry point.

## docs/ARCHITECTURE.md

Body of the `architecture` section. The block below is fenced with four backticks because it contains a fenced `mermaid` block.

````markdown
# Architecture

<architecture.summary.functional>

<architecture.summary.technical>

## Diagram
<diagram.title>

```mermaid
<diagram.mermaid, unchanged>
```

<repeat the title and the fence for each further diagram, in order>

## Components
### <component.name> (<component.kind>)
<component.description.technical> Implemented in: <links to the module READMEs, from docs/>.

## How the parts talk
| From | To | How |
|------|----|-----|
| <component name> | <component name> | <connection.label> |

## Main flows
### <flow.title>
<flow.summary.technical>
1. <step.title> — <step.text.technical> (`<step.file>`)

## Design decisions
<decisions with evidence, each with its reason and the file that records it>
````

Include "Design decisions" only when the repo records decisions: ADRs, a decisions document, or `Why:` comments that state a choice. Cite the file for each one. Omit the heading when there are none. A component with no modules has no "Implemented in" sentence.

## docs/GLOSSARY.md

Body of the `glossary` section. Sort terms alphabetically within each group, ignoring case. Omit an empty group.

```markdown
# Glossary

## Domain terms
**<term>** — <definition>

## Technical terms
**<term>** — <definition>
```

## CLAUDE.md pointer

Body of the `agents-pointer` section, written only when `CLAUDE.md` exists and is not the same file as `AGENTS.md`. Never create `CLAUDE.md`.

```markdown
See `AGENTS.md` for the repo map, entry points, commands, rules and traps. The full project model is `explorer/data/model.json`.
```
