# Project model field guide

The model is `explorer/data/model.json`. Every comment, README, AGENTS.md section and explorer view is written from it. The exact shape is enforced by `tools/document-repo/src/document_repo/schema.py` in the plugin (`SCHEMA_VERSION = 1`). When this guide and that file disagree, the file is right. This guide adds what the file cannot check: what good content looks like.

## Who writes what

| File in the run directory | Written by | Holds |
|---------------------------|------------|-------|
| `modules.final.json` | the orchestrator | `{"modules": [{"id", "path", "files", ...}]}`, the module list for this run |
| `modules/<id>.json` | one module analyst per module | `{"module": <one modules[] entry>, "files": [<file note>]}` |
| `system.json` | the synthesizer | an object with exactly six keys: `project`, `architecture`, `flows`, `glossary`, `paths`, `agent_notes` |
| `model.json`, `file-notes.json` | `assemble` | the joined model, and every module's `files` notes in one list |

`assemble` writes `meta` itself and sorts `modules` by id. Nobody writes `meta` by hand.

| `meta` field | Value |
|--------------|-------|
| `schema_version` | `1` |
| `generated_at` | UTC timestamp of the `assemble` run |
| `source_commit` | `HEAD` when `assemble` ran. Line numbers in the model refer to this commit until `remap` moves them. |
| `repo_name` | Directory name of the git top level |
| `repo_url` | `origin` as a browsable URL, or `null` (rule below) |

`repo_url` comes from `normalize_remote` in `build.py`, so a credential cannot reach the explorer. User, password, query and fragment are never copied. `ssh://`, `git://` and `user@host:path` remotes become `https://host/path` (the SSH port is dropped). An `http://` remote stays `http://` and keeps its port. A local path, a `file://` URL, a remote with no host, or a URL where a password makes the host/path split ambiguous gives `null`.

## What the validator rejects

`assemble` prints one error per line to stderr and exits 1. Its `model.json` is already written at that point and must not be built from. `build --model <file> --explorer-dir <dir> --validate-only` checks a model without writing anything.

| Rule | Example that fails |
|------|--------------------|
| Unknown fields are errors at every level. Only `flows[].steps[].snippet` is optional. | `modules[0].owner: unknown field` |
| Every other field in the tables below is required. Arrays and strings may be empty. | `project.run: missing` |
| `meta.schema_version` is `1`. | a model from another version |
| Every `id` (component, diagram, module, flow, path) matches `^[a-z0-9]+(-[a-z0-9]+)*$`: lowercase letters and digits joined by single hyphens. | `Src_Api`, `api/v1`, `-db`, or an empty string |
| Ids are unique within their list, and so are glossary terms, ignoring case. | terms `Note` and `note` |
| Line numbers are integers of at least 1, and `line_end` is not below `line_start`. | `line: 0`, `line_end: 3` with `line_start: 5` |
| A snippet has at most 30 lines. | a 31-line snippet |
| `components[].module_ids`, `glossary[].module_ids` and `dependencies.internal` name existing module ids. | `module_ids: ["api"]` when the module id is `src-api` |
| `connections[].from` and `.to` name existing component ids. | a connection to a module id |
| A module does not list itself in `dependencies.internal`. | `src-api` depending on `src-api` |
| A path step with `ref_type` `module`, `flow` or `glossary` names an existing id or term. A glossary reference must match the term's spelling exactly. | `ref_id: "note"` for the term `Note` |
| A path step with `ref_type` `doc` has a safe relative POSIX path: not empty, no leading `/`, no `..` segment, no backslash, no NUL byte. | `../secrets.md`, `docs\x.md` |
| `status` is `analyzed` or `not_analyzed`. Glossary `kind` is `domain` or `tech`. `ref_type` is `module`, `flow`, `glossary` or `doc`. | `kind: "technical"` |

The validator does not check that a `doc` path exists, that `file` paths exist, or that line numbers point at the right code. Check those against the repo.

## Lens fields

A lens field is `{"functional": "...", "technical": "..."}` and both keys are required. The explorer shows one lens at a time, chosen by the reader ("What it does" or "How it works").

- **functional**: what it does and why it matters, in plain words, in at most 3 sentences. No jargon unless the term is in the glossary. The reader is a smart person who has never seen the code.
- **technical**: how it works. Name the mechanism, the library, the data structure, the file. The reader is a proficient junior developer.

Lens fields: `project.purpose`, `architecture.summary`, `architecture.components[].description`, `modules[].purpose`, `flows[].summary`, `flows[].steps[].text`. `project.capabilities[]` is flat: it has `functional` and `technical` keys directly, with no wrapping object. The explorer falls back to `functional` when a lens object has an empty `technical`, but it does not do that for capabilities, so fill both.

## Sections

All `file` and `path` values are relative to the git top level, with `/` separators, no leading `./` and no trailing `/`. `verify`, `remap` and the explorer all resolve them that way.

| Section | Fields | Content rules |
|---------|--------|---------------|
| `project` | `name`, `tagline`, `purpose` (lens), `users`, `capabilities`, `tech_stack`, `run` | See "Notes on `project`" below the table. |
| `architecture.components` | `id`, `name`, `kind`, `module_ids`, `description` (lens) | 3 to 12 runtime or deployable parts: service, worker, datastore, UI, CLI, external API. `kind` is free text; use one lowercase word such as `service`, `datastore`, `ui`, `external`. `module_ids` lists the code that implements the part; an external API has `[]`. |
| `architecture.connections` | `from`, `to`, `label` | One per real interaction, between component ids. The label names the mechanism: "HTTP JSON", "SQL", "queue". |
| `architecture.diagrams` | `id`, `title`, `mermaid` | A Mermaid `flowchart` whose node ids equal component ids. At most 15 nodes. Add a second diagram (deployment, for example) only when it shows something the first does not. Mermaid rules are in `explorer-contract.md`. |
| `modules[]` | `id`, `name`, `path`, `status`, `purpose` (lens), `interface`, `invariants`, `dependencies`, `key_files` | See "Notes on `modules[]`" below the table. |
| `modules[].interface[]` | `name`, `kind`, `signature`, `description`, `file`, `line` | Public items only: exported, routed, or called from another module. A helper that only its own file calls is not interface. `kind` is free text (`function`, `class`, `route`, `command`, `table`). `signature` is the declaration as written in the code. `description` is one sentence. `line` is the line that names the item (`def create_note`, `export function x`, `CREATE TABLE notes`). |
| `flows[]` | `id`, `title`, `summary` (lens), `steps` | 3 to 6 flows that matter most to a user. 3 to 10 steps each, in execution order. Each step has `title`, `text` (lens), `file`, `line_start`, `line_end` and optional `snippet`. A step with a snippet spans at most 30 lines. The snippet is copied exactly from those lines. |
| `glossary[]` | `term`, `definition`, `kind`, `module_ids` | Every domain term used anywhere in the model or the docs, plus tech terms a junior might not know. `module_ids` may be `[]`. |
| `paths[]` | `id`, `audience`, `title`, `steps` | Reading orders. Each step has `ref_type`, `ref_id` and `note`; a `doc` step names a file such as `README.md` or `docs/ARCHITECTURE.md`. Convention (not validated): include `new-dev` ("New developer, day 1"), `ai-agent` ("AI agent, first read") and `change-x` ("I need to change something"). |
| `agent_notes` | `rules`, `traps`, `do_not_touch`, `commands` | `rules`: conventions an agent must follow. `traps`: things that look safe and are not (rules in "Notes on `agent_notes.traps`" below). `do_not_touch[]` holds `path` and `reason`: generated, vendored or production-critical paths. `commands[]` holds `label` and `command`: build, test, lint, copied exactly. |

### Notes on `project`

- `tagline` is 1 sentence.
- `users` are roles, not people.
- Write 3 to 8 `capabilities`, each a thing a user can see. Each holds `title`, `functional` and `technical`.
- `tech_stack[]` holds `name` and `role`. List runtimes, frameworks and stores, and say what each does here.
- `run.setup` is a list of steps, one per string, without numbers (the README and the explorer add them).
- `run.commands[]` holds `label` ("Start the API") and `command`, copied exactly from the README, package.json, Makefile or compose file. Never invent a command.

### Notes on `modules[]`

- Copy `id` and `path` from the `modules.final.json` entry. `assemble` stops if `module.id` differs. `path` is `.` for the root module.
- `name` is human-readable ("HTTP API"), not the path.
- An analyst always writes `status: "analyzed"`. Only `assemble` writes `not_analyzed`, for a stub.
- `invariants` are testable statements ("every note has a non-empty body"), never vague ones ("the code is clean").
- `dependencies.internal` holds module ids. `dependencies.external` holds package names.
- `key_files` lists the 3 to 8 files a newcomer opens first.

### Notes on `agent_notes.traps`

- Write each trap in one or two sentences with three parts: what looks safe, what actually happens, and what to do instead. A trap that only says what the code does ("omits `ko_return` when there is one path") leaves the reader to guess the consequence and the fix. State both.
- Example: "A bare `pytest` skips slow tests: `pyproject.toml` addopts adds `-m "not slow"`. Run `pytest -m slow` or `pytest -m ""` for the full suite. (`pyproject.toml:42`)"
- Name the file as `path:line` at the end. The line is where the trap is written or where the code it describes starts, at the commit the run ends on. The path stays right when the line drifts.
- A trap belongs here when it matters beyond its own file: how to build, run, test or deploy; a config default that changes what a bare command does; behaviour across modules; data loss or a wrong result that looks safe. A trap that matters only to someone editing one file stays in that file's `Traps:` header.
- Sources, in this order: a trap the owner already documents, a config default found by reading the tool's configuration (agent-prompts.md prompt 2), and the `Traps:` lines the commenters added, which SKILL.md Phase 3 step 1 folds in with `traps`. Merge two entries that describe the same thing and keep the fuller consequence.
- Never put a secret, token or real credential in a trap. Inline code in single backticks, as everywhere in the model.

## Module record

The file an analyst writes to `modules/<id>.json`. `files` is optional for `assemble` but required by the commenters, which read it through `file-notes.json`. Its entries are not validated.

```json
{
  "module": {
    "id": "src-api",
    "name": "HTTP API",
    "path": "src/api",
    "status": "analyzed",
    "purpose": {
      "functional": "Receives notes from users and stores them.",
      "technical": "FastAPI routes and request models; every write goes through `db.insert`."
    },
    "interface": [
      {
        "name": "create_note",
        "kind": "function",
        "signature": "async def create_note(body: NoteIn) -> NoteOut",
        "description": "Validates the body, inserts one row, returns it with its id.",
        "file": "src/api/routes.py",
        "line": 12
      }
    ],
    "invariants": ["Every stored note has a non-empty body."],
    "dependencies": {"internal": ["db"], "external": ["fastapi", "asyncpg"]},
    "key_files": [{"path": "src/api/routes.py", "role": "Route handlers"}]
  },
  "files": [
    {
      "path": "src/api/routes.py",
      "summary": "Route handlers for creating and listing notes.",
      "callers": ["src/api/app.py"],
      "side_effects": ["writes to the notes table"]
    }
  ]
}
```

## Line numbers and snippets

Analysts and the synthesizer work on the commit before any comment exists, so their line numbers refer to it. Phase 2 inserts comment lines, and `remap --to HEAD` then moves every `interface[].line` and every step's `line_start` and `line_end` to the commented commit. A range grows when a comment is inserted inside it: a step covering lines 11 to 13 becomes 11 to 14 if one comment line lands between them. `remap` also re-cuts each snippet from the commented file, so a snippet may contain the new comment lines. Never edit line numbers or snippets by hand after `remap`.

## Quality bar

- Check every claim against the code. When unsure, leave it out.
- Name what happens. Write "validates the body, inserts a row, returns the id", not "handles notes".
- Do not use marketing words ("powerful", "seamless", "robust").
- Put inline code in single backticks. The explorer renders backticks as code and shows every other character as text, so Markdown links, bold and HTML appear literally.
- Never put a secret, token or real credential in any field. `run.commands` may name an environment variable, not its value.
