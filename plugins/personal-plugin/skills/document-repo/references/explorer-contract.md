# Explorer contract

The explorer is a fixed app in the skill's `templates/explorer/`. `build --template` copies it into `<target>/explorer/` (everything except the top-level `data/`) and then writes `explorer/data/`. Copy it on every run. Never edit it inside a target repo: change the template in the plugin and run again.

| File in `explorer/data/` | Written by | Holds |
|--------------------------|------------|-------|
| `model.json` | `build` | The canonical model. Agents read this one. |
| `model.js` | `build` | `window.PROJECT_MODEL = {...};`, the same model with every non-ASCII character escaped. The page loads it with `<script src>`, because a browser will not `fetch` a JSON file from a page opened over `file://`. |
| `state.json` | `build` | `source_commit`, `schema_version`, `model_hash` (SHA-256 of the `model.json` bytes), `generated_at`. `changes` reads it in update mode. |

## What each view reads

Routes are hash routes. `#/modules/<id>`, `#/tours/<id>`, `#/glossary/<term>` and `#/paths/<id>` open one item; the same route without the last part lists them.

| Route | Shows | Reads |
|-------|-------|-------|
| `#/overview` | Name, tagline, purpose, users, capabilities, tech stack, setup steps, commands, cards for the reading paths | `meta.repo_name`, all of `project`, `paths[].id`, `.title`, `.audience` |
| `#/architecture` | Summary, every diagram, a card per component, the connection list | `architecture.*`, `modules[].name` |
| `#/modules` | A card per module, with a "not analyzed" tag where it applies | `modules[]` |
| `#/modules/<id>` | Purpose, interface table, invariants, dependencies, "Used by", key files, tours, terms | `modules[]`. "Used by" lists the modules whose `dependencies.internal` names this one. Tours are the flows with a step whose `file` lies under the module's `path` (the root module `.` owns top-level files only). Terms are the glossary entries whose `module_ids` hold this id. |
| `#/tours`, `#/tours/<id>` | Each flow, step by step, with file and line links and snippets | `flows[]` |
| `#/glossary`, `#/glossary/<term>` | Terms in two groups, sorted alphabetically. With `<term>`, the page scrolls to that term and highlights it. | `glossary[]` |
| `#/paths`, `#/paths/<id>` | The reading paths, then rules, traps, do-not-touch paths and commands for agents | `paths[]`, `agent_notes` |
| `#/search/<q>` | Matches, 100 at most | Project name, tagline and purpose; capabilities; component names and descriptions; module name, path, purpose, interface names and descriptions, invariants; flow titles, summaries, step titles, step text and files; glossary terms and definitions |

Search does not index `agent_notes`, `paths`, `key_files`, `signature`, `tech_stack` or `run`. A term that appears only there cannot be found.

## What the data must satisfy

1. **Both lenses are filled.** The reader switches between "What it does" (`functional`) and "How it works" (`technical`) at any time. A lens object with an empty `technical` falls back to `functional`. A capability does not, so an empty capability text renders empty.
2. **Backticks make inline code. Nothing else is markup.** Every value is HTML-escaped, so `<b>`, `**bold**` and `[a link](x)` appear literally. Backticks are interpreted in: tagline, purpose, capability text, tech-stack role, run setup step, architecture summary, component description, connection label, module purpose, interface description, invariants, key-file role, flow summary, step text, glossary definition, path-step note, and agent rules, traps and reasons. They are not interpreted in names, titles, audiences, `signature`, `snippet`, command labels and commands.
3. **Snippets and signatures show in the technical lens.** The functional lens folds a snippet under "Show the code" and hides `signature`.
4. **`meta.repo_url` decides whether files are links.** When it is an `http(s)` URL, a file reference links to `<repo_url>/blob/<meta.source_commit>/<file>#L<line>`, which is GitHub's URL shape and may not resolve on another forge. The commit must be pushed for the link to work. When `repo_url` is `null` or anything else, the path shows as plain text. The rule that derives `repo_url` is in `model-schema.md`.
5. **A `doc` step in `paths[]` links to `../<ref_id>`**, relative to `explorer/index.html`, so it opens the file in the repo. The tool does not check that the file exists.
6. **`modules[].path` and every `file` are normalised** (no leading `./`, no trailing `/`), because the explorer matches them as plain prefixes.
7. **Glossary references match exactly.** A path step that names a glossary term must use the term's spelling. The validator rejects a model where it does not. Without that check, the link would open the glossary with every term listed and none highlighted.

## Diagrams

Mermaid 11.17.2 draws each `architecture.diagrams[].mermaid` source in the browser, with `securityLevel: 'strict'`.

1. **Write a `flowchart`.** Only flowchart nodes become clickable.
2. **Node ids equal component ids** (or module ids). Mermaid names each node element `<render id>-flowchart-<node id>-<n>`. The app removes the render id it chose, reads `<node id>`, and looks it up in `architecture.components[].id`, then in `modules[].id`. A click opens the component's first module. A component with no modules scrolls to its card. A node id that matches neither is drawn but not clickable. A hyphenated id such as `src-api` works.
3. **Do not use `%%{init: ...}%%`, a front-matter `config:` block, or `click` lines.** The app locks `theme`, `themeCSS`, `themeVariables`, `fontFamily`, `altFontFamily`, `darkMode`, `htmlLabels`, `securityLevel` and the size limits in a `secure` list, so an `init` directive that sets them is ignored. Strict mode disables `click`.
4. **Do not set fixed colours.** The app picks Mermaid's default or dark theme from the browser's colour scheme when the page loads, and a hard-coded light fill is unreadable in dark mode.
5. **Keep the syntax plain.** Put spaces around arrows. Use labels that are plain text. Avoid a component id that Mermaid reads as a keyword, such as `end`; give that component another id.
6. A diagram that fails to render does not stop the page. The Architecture view shows "This diagram could not be drawn, so its source is shown" and writes a console warning.

## What the page enforces

`index.html` carries a Content-Security-Policy: `default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; base-uri 'none'; form-action 'none'`. The page loads exactly four local files (`styles.css`, `data/model.js`, `vendor/mermaid.min.js`, `app.js`). No inline script, no `eval` and no network request can run, so no value in the model can become script or fetch a URL.

## Acceptance for every run

Open `explorer/index.html` from disk and check:

- The console shows 0 errors.
- Every route in the table renders.
- The Architecture view draws every diagram, with no "could not be drawn" message. A bad diagram logs a warning, not an error, so look at the page.
- Clicking a diagram box opens its module.
- Every request is to a `file://` address.
