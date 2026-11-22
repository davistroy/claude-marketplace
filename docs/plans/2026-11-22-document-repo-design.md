# document-repo — Skill Design

**Date:** 2026-11-22
**Status:** Design approved in brainstorming. The written spec is waiting for owner review. Not yet implemented.
**Author:** Troy Davis (brainstormed with Claude)
**Skill home:** `plugins/personal-plugin/skills/document-repo/`
**Bundled tool:** `plugins/personal-plugin/tools/document-repo/`
**Test targets:** `davistroy/open-brain` (public, TS/Python/SQL/Docker, ~12 MB) and `davistroy/retire` (private, Python + TS front end, ~5 MB)

## Purpose

You run one skill on a target repo. It makes the whole repo well documented, for two kinds of reader:

1. **A proficient junior developer.** They should understand any file quickly.
2. **An AI agent reading the repo for the first time.** It should find entry points, contracts, invariants, and traps without reading every file.

The skill produces four things:

- **Code comments:** a header on every file, a doc comment on every public item, and "why" notes where the code is not obvious.
- **Documentation:** a root README, READMEs at module boundaries, `AGENTS.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md`.
- **An interactive explorer:** a static web app in `explorer/`. It explains purpose, capabilities, architecture, modules, and flows, through a functional lens and a technical lens.
- **A project model:** `explorer/data/model.json`. All of the outputs above are generated from it.

## Decisions

| # | Decision | Rationale / rejected alternatives |
|---|----------|-----------------------------------|
| Structure | One skill with phases, plus flags to re-run one phase (`--phase`) or only the changes (`--update`) | All phases share one model and one entry point. Rejected: three skills plus an orchestrator. That means four components to maintain and a model contract that crosses skill boundaries, and it adds no ability the flags do not already give. |
| Single source of truth | Analysis writes one project model. Comments, docs, and the explorer all read from it. | The outputs cannot drift apart. Rejected: let each phase analyze the repo on its own. That costs three times as much, and the outputs contradict each other. |
| Explorer tech | Static HTML + vanilla JS + a vendored Mermaid file. The data comes from `model.js`. | Works in any repo, whatever its language. No npm. Works offline. Sends nothing to the internet, which matters for private repos such as `retire`. Rejected: React/Vite. It adds a Node toolchain to every target repo. |
| Explorer template | A fixed, tested template ships inside the skill. Only the data is generated per repo. | Every repo gets the same tested app, and a template fix helps every repo. Rejected: generate the app per repo. The output would not be testable and would vary from run to run. |
| Explorer location | `explorer/` at the repo root. The root README links to it. | Clean, and easy to delete. Rejected: `index.html` directly in the root, which clutters it. |
| Model loading | `model.json` is the canonical copy. `model.js` (`window.PROJECT_MODEL = …`) is generated from it. | A browser blocks a `file://` page from fetching JSON, but loads a `<script src>` without trouble. Agents read the plain JSON. |
| Run modes | A full run plus `--update` | Docs go stale. `--update` uses the commit stored in `state.json` and redoes only the modules that changed. Rejected: one-shot only. |
| Gate | One approval gate, after analysis and before any write to the target repo | The owner reviews the model and the write plan before the skill touches any source file. Rejected: a gate per phase, which is too slow for a run that is safe by construction. |
| Comment policy | Explain *why* and *intent*, not *what*. Never delete or rewrite existing comments. | Comments that repeat the code are noise and rot quickly. An existing comment that looks wrong goes in the report. The skill does not change it. |
| Comments only | A mechanical check proves that each file changed only in its comments. A file that fails goes back to its old version. | The skill must never change behavior. Prose promises are not proof (see the repo's DoD-row doctrine). |
| Isolation | Work on a new branch in the target repo. Commit once per module per phase. | The owner can review or revert each module alone. |

## Architecture

```text
plugins/personal-plugin/
  skills/document-repo/
    SKILL.md                      # orchestration, <500 lines
    references/
      model-schema.md             # project model contract (fields, required/optional)
      comment-standards.md        # per-language formats + density rules + examples
      doc-templates.md            # README / AGENTS.md / ARCHITECTURE / GLOSSARY skeletons
      explorer-contract.md        # which model fields each explorer view reads
      update-mode.md              # incremental procedure
    templates/explorer/           # fixed app, copied into target as explorer/
      index.html
      app.js
      styles.css
      vendor/mermaid.min.js       # pinned version, vendored
  tools/document-repo/
    pyproject.toml
    src/document_repo/
      __main__.py
      cli.py
      inventory.py                # file walk, languages, sizes, deps, entry-point candidates
      modules.py                  # module boundary proposal
      verify.py                   # comments-only proof per file
      build.py                    # model.json -> model.js, validate against schema, copy template
      changes.py                  # git diff since state.json commit -> affected modules
    tests/
```

The bundled tool runs from source through `PYTHONPATH`, as the house pattern says. It uses only the standard library. JS/TS checks use the target repo's `node` and `typescript` when they are present (see Verification).

## Flow

### Phase 0 — Preflight

1. Stop if the target's git tree has uncommitted changes.
2. Make the branch `docs/document-repo` (or `docs/document-repo-update-<date>` for `--update`).
3. Find the test, lint, and type-check commands. Run them once to record a **baseline**. Tests that already fail are recorded. They do not block the run.
4. Read `state.json` if it exists. With no `--update` flag and an existing `state.json`, ask the owner: update, or rebuild in full.

### Phase 1 — Analyze

1. `document_repo inventory` writes the inventory: files, languages, line counts, dependency manifests, entry-point candidates, and generated/vendor paths to skip.
2. `document_repo modules` proposes module boundaries (top-level packages, workspaces, service directories, and so on). The skill adjusts them with judgement.
3. **One subagent per module.** Each one gets the inventory slice and writes the module record: purpose, public interface, invariants, dependencies, key files, flows it takes part in, and notes per file. Files over 2000 lines are split by function or class and analyzed in parts.
4. **One synthesis agent** reads all module records. It writes the system-level sections: project, architecture (with Mermaid), flows, glossary, and agent notes.
5. `document_repo build --validate` checks the model against the schema. A missing required field fails the run.

If a module subagent fails, it gets one retry. After a second failure, the module is marked `status: not_analyzed` and shown at the gate.

### Gate — owner review

The skill uses `AskUserQuestion`, following house decision D64. It presents:

- A summary of the model: the purpose in two sentences, the modules, and the main flows.
- The write plan: how many files get comments, which folders get a README, the doc files to create or update, and the explorer views.
- Any `not_analyzed` modules and any baseline test failures.

Nothing is written into the target repo before the owner approves. The model itself is held in the run's scratch directory until then: `<target>/.document-repo/`, which ignores itself through a `.gitignore` holding `*`. It is not under `.git/`, because Claude Code blocks agent writes there.

### Phase 2 — Comments

Per file, using the language's native format: docstrings (Python), TSDoc/JSDoc (TS/JS), `--` (SQL), `#` (shell, Dockerfile, YAML).

| Kind | Where | Content |
|------|-------|---------|
| File header | Every source file | Role, where it fits, callers, inputs/outputs, side effects |
| Doc comment | Every public function, class, method, exported constant | Purpose, parameters, return value, errors, an example where it helps |
| "Why" note | Non-obvious code only | Reason for tricky logic, workarounds, magic numbers, ordering constraints |

**Skip:** generated files, vendor code, lock files, minified files, and build output. **SQL migrations** get a header comment only.

The comments follow `~/.claude/styles/WRITING_RULES.md` when that file exists.

Work runs as one subagent per module. Each subagent gets its module record plus the system sections of the model. After each file, the subagent runs `document_repo verify <file>`. When a module is done, the skill runs the baseline commands, then commits.

### Phase 3 — Docs

| File | Content |
|------|---------|
| `README.md` (root) | Purpose, capabilities, quick start, repo map, link to `explorer/index.html` |
| `<module>/README.md` | Purpose, public interface, invariants, dependencies, key files. Only at module boundaries. |
| `AGENTS.md` | Repo map for agents, entry points, commands, rules, traps, "do not touch" zones, pointer to `explorer/data/model.json` |
| `CLAUDE.md` | If it exists: add one line that points to `AGENTS.md`. Nothing else changes. If it does not exist: do not create it. |
| `docs/ARCHITECTURE.md` | Components, Mermaid diagrams, main flows, design decisions |
| `docs/GLOSSARY.md` | Domain terms and tech terms |

**Existing files:** the skill keeps the human text. Generated text goes between `<!-- document-repo:start:<section> -->` and `<!-- document-repo:end:<section> -->`. `--update` replaces only the text between the markers.

### Phase 4 — Explorer

The skill copies `templates/explorer/` to `explorer/`. Then `document_repo build` writes `explorer/data/model.js` and `explorer/data/state.json`.

| View | Content | Model fields |
|------|---------|--------------|
| Overview | What it is, who it is for, the problem it solves, capability cards | `project` |
| Architecture | Clickable Mermaid diagram. A click on a node opens its module panel. | `architecture`, `modules` |
| Modules | Purpose, interface, invariants, dependencies, files | `modules` |
| Tours | Step-by-step walks through the main flows, with short snippets and file:line links | `flows` |
| Glossary + search | Client-side search across all text | `glossary`, all |
| Start-here paths | "New dev, day 1", "AI agent", "I need to change X" | `paths` |

A global **lens switch** (functional or technical) selects which text variant each view shows. File links go to GitHub when the repo has a remote. Without a remote, they show a relative path. The app has light and dark modes and works at phone width.

## Project model (summary)

The full contract goes in `references/model-schema.md`. The top-level keys:

| Key | Holds |
|-----|-------|
| `meta` | Schema version, generated-at, source commit, repo remote URL |
| `project` | Name, purpose (functional + technical), users, capabilities, tech stack, how to run |
| `architecture` | Components, connections, deployment, Mermaid sources |
| `modules[]` | id, path, purpose (two lenses), interface, invariants, dependencies, key files, status |
| `flows[]` | id, title, steps[] (text + file + line range + snippet) |
| `glossary[]` | term, definition, kind (domain or tech), related modules |
| `paths[]` | audience, ordered list of model references |
| `agent_notes` | Rules, traps, do-not-touch zones, commands |

Snippets are capped at 30 lines each, so the model stays small. `state.json` holds `{source_commit, schema_version, model_hash, generated_at}`.

## Verification — comments only

`document_repo verify <file> --before <ref>` exits non-zero when anything besides comments changed.

| Language | Method |
|----------|--------|
| Python | `ast.parse` before and after. Strip docstring `Expr` nodes. Compare `ast.dump`. |
| JS / TS | When `node` and `typescript` resolve in the target: compare the `ts.createScanner` token streams with comment trivia skipped. Otherwise use the generic rule. |
| Other (SQL, shell, Dockerfile, YAML, …) | Generic diff rule: no line removed or changed, and every added line is a comment under that language's syntax (with state tracking for block comments) |

On failure, the skill restores the file with `git checkout -- <file>` and logs it in the run report.

Per the repo's doctrine on guards, every verifier gets a **negative test** before it ships: a planted code change in each language must make it exit non-zero.

## Update mode

1. Read `state.json`. Stop if `source_commit` is not in the history.
2. `document_repo changes` maps `git diff <source_commit>..HEAD` to the affected modules. New files that fit no module go to synthesis for a boundary decision.
3. Analyze the affected modules again. Run synthesis again only when an affected module's `interface` or `dependencies` changed, or when a module was added or removed.
4. Comment only new items and items with changed code (existing comments are never changed — the same rule as a full run).
5. Refresh the marker sections. Rebuild `model.js` and `state.json`.
6. The gate still runs, with the plan scoped to the delta.

## Run report

The skill writes `explorer/data/run-report.md` in the target repo and also shows it in chat. It holds counts (files commented, READMEs written), verifier failures and reverts, existing comments that look wrong, `not_analyzed` modules, baseline and after-run test results, and the comprehension score.

## Acceptance tests (on open-brain and retire)

1. `verify` reports 0 non-comment changes across all committed files.
2. The test results after the run equal the baseline.
3. `explorer/index.html` loads from `file://` in Chrome with 0 console errors. Every view renders. The lens switch changes the text.
4. **Comprehension test:** a fresh agent reads only the generated docs and the explorer data. It answers 10 questions written beforehand. The answers are checked against the source. Target: at least 9 correct.
5. `--update` after a small planted change touches only the affected module's files and marker sections.
6. For `retire`: grep the explorer files for `http://` and `https://`. The only matches allowed are the repo remote and inert strings inside vendored code. No network requests at runtime (checked with the Chrome network log).

## Out of scope (v1)

- Changing code behavior, refactors, or renaming.
- Publishing the explorer (to GitHub Pages or anywhere else). The owner can do that by hand.
- Languages with no comment syntax the verifier knows. Those files are skipped and listed in the report.
- Generated images (`visual-explainer` covers paid image generation).

## Relationship to existing skills

- `explain-project`: makes a Word document for non-CS readers. Its analysis step is the model for Phase 1, but the two skills do not share code.
- `create-wiki`: an LLM-maintained wiki that grows over time. Different lifecycle, so no overlap in output.
- `clean-repo`: cleanup plus a docs refresh. `document-repo` replaces neither part of it. It may later call `document-repo --phase docs`.
