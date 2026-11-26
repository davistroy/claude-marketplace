# Agent prompts

Fill the `{placeholders}`, prepend the preamble, and pass each prompt to the Agent tool. Each agent writes only the files its prompt names, and replies with 3 lines. Agents never commit and never push.

| Placeholder | Value |
|-------------|-------|
| `{TARGET}` | Git top level of the repo being documented |
| `{RUN_DIR}` | `$TARGET/.document-repo/run-<UTC timestamp>`, a new directory for every run. Create it with `modules/`, `comments/` and `docs/` inside before dispatching, so agents can write there. `$TARGET/.document-repo/.gitignore` holds `*`, so nothing in a run directory is tracked. |
| `{SKILL_DIR}`, `{TOOL_SRC}` | The skill directory, and `tools/document-repo/src` in the plugin |
| `{id}`, `{path}`, `{files}` | One entry of `modules.final.json`: the module id, its path, and the files it owns |
| `{all_module_ids}` | Every module id in `modules.final.json` |
| `{entry_candidates_in_module}` | The inventory's `entry_candidates` whose path is in `{files}`, plus each manifest hint (`package.json`, `pyproject.toml`) whose target after `->` is in `{files}`. SKILL.md gives the full rule. |
| `{ids}` | A batch of module ids |
| `{UPDATE_LINE}` | Empty in a full run. In an update run, the line given in the prompt. |
| `{SINCE}`, `{BASE_MODEL}` | Update runs only: `since` from `changes.json`, and the path of the base model copy |
| `{affected_modules}` | Update runs only: the ids of the modules to re-analyse, from `affected_modules` in `changes.json` plus any new module |

## Preamble for every prompt

```text
Rules for every agent in this run:
- Write only the files your task names. Never commit, push, stash, reset, or
  switch branches. Never edit a file outside your scope.
- Paths are relative to the git top level of {TARGET}, with / separators.
- Never copy a secret, token or credential from any file into any output.
- Follow ~/.claude/styles/WRITING_RULES.md for every sentence you write, when
  that file exists.
- Finish with a 3-line reply: what you wrote, the counts, and anything the
  orchestrator must know.
```

## 1. Module analyst (Phase 1, one per module, up to 6 in parallel)

```text
You are documenting one module of the repo at {TARGET} for a junior developer
and for AI agents. Read every file listed below. Do not edit any file.

Module: id={id} path={path}
Files: {files}
Inventory entry points (hints only): {entry_candidates_in_module}
Module ids in this repo: {all_module_ids}
Field guide: {SKILL_DIR}/references/model-schema.md (read all of it, including
the module record example)

Write JSON to {RUN_DIR}/modules/{id}.json with this shape:
{"module": <one modules[] entry per the field guide>,
 "files": [{"path": str, "summary": str, "callers": [str], "side_effects": [str]}]}

Rules:
- module.id is exactly "{id}", module.path is exactly "{path}", and
  module.status is "analyzed".
- Use only the field names in the guide. An unknown field makes the whole
  model invalid. Fill both the functional and the technical text.
- One "files" entry per listed file.
- Line numbers are 1-based, counted at the current HEAD. Every interface item
  has file and line, and line is the line that names the item.
- Only claim what the code shows. Name the mechanism: write "validates the
  body, inserts a row, returns the id", not "handles notes".
- For files over 2000 lines, read them in parts, by class or function.
- dependencies.internal holds ids from the module id list above and never this
  module's own id. dependencies.external holds package names.

When done, run:
python3 -c "import json;d=json.load(open('{RUN_DIR}/modules/{id}.json'));assert d['module']['id']=='{id}'"
```

## 2. Synthesizer (Phase 1, one agent, after all analysts)

```text
Read every {RUN_DIR}/modules/*.json, {RUN_DIR}/inventory.json, and the root
README and docs of {TARGET} if present. Read source files only to confirm a
flow, and the configuration files the commands rule below names.
Field guide: {SKILL_DIR}/references/model-schema.md.
Explorer rules: {SKILL_DIR}/references/explorer-contract.md. Read its
"Diagrams" section before you draw anything.
{UPDATE_LINE}

Write {RUN_DIR}/system.json: an object with exactly six keys: project,
architecture, flows, glossary, paths, agent_notes. Do not write meta or
modules.

Rules:
- Use only the field names in the guide. An unknown field makes the whole
  model invalid. Fill both the functional and the technical text.
- Ids of components, diagrams, flows and paths are lowercase letters and
  digits joined by single hyphens. components[].module_ids and
  glossary[].module_ids hold module ids from the module records.
  connections[].from and .to hold component ids.
- Each diagram is a Mermaid flowchart. Node ids equal component ids. Do not use
  %%{init}%% directives, front-matter config, click lines or colours: the
  explorer ignores or blocks them. At most 15 nodes per diagram.
- Flow steps cite real file and line ranges at the current HEAD, with
  line_end not below line_start. Copy a snippet exactly from its lines. A
  snippet has at most 30 lines.
- Copy run commands exactly from the repo (README, package.json, Makefile,
  compose file). Never invent one.
- For each command in agent_notes.commands, read the configuration the tool
  reads and record every default that changes what the bare command does as a
  trap: pyproject.toml addopts and its other tool sections, pytest.ini,
  setup.cfg, package.json scripts and tool sections, Makefile default targets
  and variables, tsconfig.json, .npmrc. Example: addopts adds -m "not slow",
  so a bare pytest skips slow tests.
- Write each trap as one or two sentences: what looks safe, what actually
  happens, what to do instead, then the file as path:line. A trap with no
  consequence and no fix is not finished. The guide's "Notes on
  agent_notes.traps" has an example.
- The glossary has one entry per term, ignoring case. A path step that names a
  term uses its exact spelling.
- paths must include ids new-dev, ai-agent and change-x. A step with
  ref_type "doc" names a file that exists, as a path relative to the repo
  root, such as README.md or docs/ARCHITECTURE.md.

When done, run:
python3 -c "import json;d=json.load(open('{RUN_DIR}/system.json'));assert set(d)=={'project','architecture','flows','glossary','paths','agent_notes'}"
```

`{UPDATE_LINE}` in an update run: `Update run: the base model is {BASE_MODEL}. Start from it and keep every statement that is still true. These modules changed since {SINCE}: {affected_modules}.`

## 3. Commenter (Phase 2, one per module, up to 4 in parallel; modules never share files)

```text
Add comments to these files in {TARGET}, and change nothing else: {files}
Context: module record {RUN_DIR}/modules/{id}.json; file notes
{RUN_DIR}/file-notes.json (find your files by path); system view
{RUN_DIR}/model.json (project, architecture, glossary).
Standards: {SKILL_DIR}/references/comment-standards.md. Read all of it first.
Every rule in it matches a check that reverts your file.
{UPDATE_LINE}

Change source files with the Edit tool only. To insert, put the unchanged
neighbouring line in both old_string and new_string, byte for byte, and add
your lines around it. old_string must occur exactly once in the file: if the
neighbouring line repeats (a blank line, a closing brace), add the line above
or below it to old_string until it is unique. Never change or remove an
existing line. Keep the file's line endings.

After each file, run:
PYTHONPATH="{TOOL_SRC}" python3 -m document_repo verify --repo "{TARGET}" --before HEAD <path>
Read "detail" in the JSON result. If "ok" is false, restore the file with
git -C "{TARGET}" checkout HEAD -- <path> and try once more with fewer, simpler
insertions that avoid the rule "detail" names. If it fails again, restore it
and move on. If "detail" says the TypeScript compiler is not available,
restore the file, do not retry, and report every JS/TS file the same way. If it
says the file does not parse cleanly, or its base version does not parse, restore
it and move on.

Other agents are editing other files in the same working tree. Touch only your
files. Run git checkout only on your own files, and never git add, commit,
stash or reset.

Write {RUN_DIR}/comments/{id}.json:
{"commented": [paths], "reverted": [{"path": str, "detail": str}],
 "suspect_comments": [{"path": str, "line": int, "why": str}]}
```

`{UPDATE_LINE}` in an update run: `Update run: comment only items that are new or whose code changed since {SINCE}. git -C {TARGET} diff {SINCE} HEAD -- <path> shows them. A new file gets a header.`

## 4. Module docs writer (Phase 3, batches of up to 6 modules)

```text
For each module id in {ids}, write the body of the `module` section for
{TARGET}/<module.path>/README.md. Use only {RUN_DIR}/model.json, the "Module
README" template, and the "Rules for every body" in
{SKILL_DIR}/references/doc-templates.md.
For each id, write the body to {RUN_DIR}/docs/<id>.md, then run:
PYTHONPATH="{TOOL_SRC}" python3 -m document_repo upsert-section --repo "{TARGET}" --file "{TARGET}/<module.path>/README.md" --section module --content-file "{RUN_DIR}/docs/<id>.md"
Skip the root module (path ".") and any module whose status is not_analyzed:
the root README is written separately. If upsert-section exits 2, do not retry.
Copy its message into your reply. Never edit README text outside the markers.
```

## 5. Examiner (end of run)

```text
Read the SOURCE CODE of {TARGET}. Do not read README files, AGENTS.md,
CLAUDE.md, docs/, explorer/ or .document-repo/.
Write 10 questions a new developer must be able to answer to work safely in
this repo: its purpose, where X happens, what calls Y, what must stay true,
how to run the tests, and one trap. Mix easy and hard questions. For each,
write the correct answer with file:line evidence.
Write {RUN_DIR}/quiz.json: [{"q": str, "answer": str, "evidence": str}].
Then stop.
```

The orchestrator writes `{RUN_DIR}/quiz-questions.json` from `quiz.json`: `[{"q": str}]`, the same questions in the same order, with no `answer` or `evidence` key. Then it runs the student.

## 6. Student (end of run, fresh agent)

```text
Answer the questions in {RUN_DIR}/quiz-questions.json about the repo at
{TARGET}. You may read ONLY these files: README.md, AGENTS.md, CLAUDE.md,
anything under docs/, any README.md in a subdirectory, and
explorer/data/model.json. Do not open any other file, run any code, or read
git history. In {RUN_DIR} you may read quiz-questions.json and write
quiz-answers.json, nothing else.
Write {RUN_DIR}/quiz-answers.json: [{"q": str, "answer": str, "source": str}],
where source names the file you used. If the files do not answer a question,
say so in "answer".
```

## 7. Grader (end of run, the examiner again)

```text
Grade a student's answers. Read {RUN_DIR}/quiz.json (questions, correct
answers, evidence) and {RUN_DIR}/quiz-answers.json. For each question, decide
whether the student's answer means the same as the correct answer. Mark it
incorrect when it is incomplete in a way that would mislead, names the wrong
file, function or command, or says the answer cannot be found.
Write {RUN_DIR}/quiz-grade.json:
{"score": n, "per_question": [{"q": str, "correct": bool, "why": str}]}
per_question has one entry per question, in the order of quiz.json. score is
the number of entries with "correct" true (0 to 10).
```
