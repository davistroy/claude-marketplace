# Comment standards

Goal: a proficient junior developer understands a file in minutes, and an AI agent finds a file's role, contract and traps by reading its header.

Every edit you make is checked mechanically by `verify`. A file that fails is restored from git and your comments in it are lost, so the rules below are not style advice. Each one matches a check in `tools/document-repo/src/document_repo/verify.py` or `guards.py`.

## The three kinds

| Kind | Where | Must contain |
|------|-------|--------------|
| File header | Top of every source file the inventory did not skip, below a shebang or encoding line if there is one | Role in one sentence; where it fits (module, callers); main inputs and outputs; side effects; invariants (optional); traps (optional) |
| Doc comment | Every public function, class, method and exported constant; private ones only when non-obvious | Purpose; parameters; return value; errors raised; an example when the call is not obvious |
| "Why" note | Above non-obvious code only | The reason: a constraint, workaround, bug reference, magic number, ordering requirement |

Use these exact labels in headers so agents can grep them: `Role:`, `Used by:`, `Inputs:`, `Outputs:`, `Side effects:`, `Invariants:`, `Traps:`. Leave a label out when it would be empty. Start a "why" note with `Why:`.

If the file already has a header comment or docstring, leave it alone and do not add a second header. Add a separate comment block directly below it with only the labelled facts it lacks, or add nothing.

## How each file is checked

| Language | Method | A comment edit fails when |
|----------|--------|---------------------------|
| Python | Parse before and after, drop docstrings, compare syntax trees | the tree differs, an existing docstring changed, or a new docstring contains `>>>` |
| JavaScript, TypeScript (`.js .jsx .mjs .cjs .ts .tsx .mts .cts`) | Print both versions with comments removed, using the TypeScript compiler, and compare | the printed code differs, or either version has a parse error |
| Everything else (SQL, shell, YAML, TOML, Dockerfile, Makefile, CSS, HTML, Go, Rust, Java, C, C++, C#) | Line diff | any base line changed or was removed, or any inserted line is not blank or a comment |

After the method passes, shared guards run on every language.

Check a file with the command in your prompt, which has `{TOOL_SRC}` and `{TARGET}` already filled in. Your shell has no `$TOOL_SRC` or `$TARGET`. The file path is relative to the git top level.

```bash
PYTHONPATH="{TOOL_SRC}" python3 -m document_repo verify --repo "{TARGET}" --before HEAD src/api/routes.py
```

The output is a JSON list with `path`, `method`, `ok` and `detail`. Exit code 0 means every file is `ok`; 1 means at least one failed. `detail` names the broken rule. Read it before you retry.

## Before you insert a line

1. **Insert new lines only.** Never append a comment to a code line and never touch a code line, even its whitespace. Line-diff languages reject an appended comment. Python and JS/TS compare syntax trees, which ignore comments, so they would let it through. The rule still holds there.
2. **Never edit, move, reword or delete an existing comment or docstring**, and never insert a line inside an existing block comment (`/** ... */`, a `/* ... */` banner). In line-diff languages the verifier rejects both, because the position is inside the block. In Python an edited docstring fails. In JS/TS the verifier cannot see it, but the rule holds. If an existing comment looks wrong, list it in `suspect_comments` and leave it.
3. **Do not change line endings, the byte order mark or the file mode.** Keep the file's own line endings. Do not put a form feed, vertical tab, NEL or U+2028 in a comment. Do not `chmod`. A symlink fails.
4. **Never insert above these lines:** a shebang, an encoding line in lines 1 and 2, or Dockerfile parser directives at the top (`# syntax=`, `# escape=`, `# check=`). Insert on the first line below them.
5. **Never insert directly below a directive-like comment** (a `# noqa` line, `// eslint-disable-next-line`, `//go:build`, `// @flow`). The directive applies to the next line or sits with it, so a new line under it moves its effect. Put your comment above an `eslint-disable-next-line` or `# noqa` line. For a file-level `// @flow`, insert below the blank line that follows it, so the directive stays the first comment. For `//go:build`, see the Go row under Formats.
6. **Never insert after a line that ends in `\`.** The statement continues on the next line. Comment above the whole statement.
7. **Never insert where a new line would be data, not a comment.**

| Language | Unsafe positions |
|----------|------------------|
| Shell, Dockerfile | Heredoc bodies; multi-line quoted strings; between the items of a multi-line `( ... )` array or `$( ... )`; between the lines of a `RUN` that uses `\` continuation (comment above the instruction) |
| Makefile | `define` ... `endef` blocks; recipe heredocs. A comment inside a recipe starts in column 0. |
| YAML | Inside a block scalar (`key: \|` or `key: >`); directly under one, when the new line is indented deeper than the `key:` line; between the lines of a multi-line plain or quoted scalar |
| SQL | Dollar-quoted bodies (`$$ ... $$`, `$tag$ ... $tag$`); multi-line string literals; `COPY ... FROM STDIN` data; inside a block comment |
| TOML | Multi-line strings |
| Go | Raw strings (backticks); the comment above `import "C"`; anywhere from `// Output:` to the closing brace of an Example function |
| Rust, Java, C, C++, C# | Multi-line, raw and text-block strings; inside a block comment |
| HTML | Inside `<script>`, `<style>`, `<pre>`, `<textarea>`, `<title>`, `<noscript>`, `<iframe>` and the other raw-text elements; inside a multi-line tag |
| Python | Inside a triple-quoted string (any line you add changes the string) |
| JS, TS | Not scanned. The compiler decides, so see "When the file is JavaScript or TypeScript". |

## When you write the comment text

8. **No directive-like text on any inserted line.** The check runs on every inserted line, so prose and docstring lines count too. Writing "this is not a noqa thing" fails. The patterns live in `_DIRECTIVES` in `guards.py`, which is the source of truth. Each pattern applies only to the languages whose tools read it. The table groups some of them by family and is partial.

| Family | Examples |
|--------|----------|
| Lint and format suppression | `noqa`, `nosec`, `nolint`, `NOLINT`, `prettier-ignore`, `biome-ignore`; `eslint-disable`, `eslint-enable`, `eslint-env`; `istanbul ignore`, `c8 ignore`, `v8 ignore`; `deno-lint-ignore`, `deno-fmt-ignore`; `pragma` after a `#` (Python, shell, YAML, TOML, Dockerfile, Makefile) |
| Type and tool prefixes | `# type:` and `# pylint:`, `# mypy:`, `# ruff:`, `# isort:`, `# fmt:`, `# pyright:`, `# pyre-`, `# yapf:` in Python; `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck`, `@ts-check`; `@flow`; `@jsx`; `@jest-environment`, `@vitest-environment` |
| Linter and scanner names | `hadolint`, `yamllint`, `tflint`, `tfsec`, `trivy`, `kics`, `checkov`, `nosemgrep`, `# shellcheck`, `# renovate:`; `stylelint`, `purgecss`, `autoprefixer` in CSS |
| Compiler and build directives | `//go:`, `// +build`-style `//` followed by `+word`, `//line `, `//export`, `//extern`, `// Output:` in Go; `/// <` and `@cc_on` in JS and TS; `rtl:` in CSS; `# syntax=`, `# escape=`, `# check=` in Dockerfiles; `#__PURE__`; `@vite-ignore`; `webpackChunkName:`-style magic comments; `sourceMappingURL=` |
| Generator and format markers | `@generated`, `Code generated ... DO NOT EDIT`, `<auto-generated`, `@format`, `@prettier`, `@noformat` |
| SQL and migration markers | `/*!`, `/*+`, a line starting `-- +`, `-- migrate:`, `-- name: x :`, liquibase and changeset lines |
| HTML markers | `<!-- [if`, `<![endif]`, `<!--#`, `<!-- ko` |
| Shebang | any line that starts with `#!` |
| JS and TS block lines | a block-comment line whose first word is lowercase `eslint`, `global`, `globals`, `exported`, `jshint` or `jslint` |

When one of these words is the subject of your comment, describe it instead: "the lint-suppression marker on the next line".

9. **Do not end a comment line with `\`** (or the `??/` trigraph). It continues onto the next line in C, shell and make. Rewrite the sentence.
10. **Do not put `{{`, `{%` or `{#` in a comment in a template file.** Template engines evaluate them inside comments. A template file is an HTML file, a file under a `templates/` directory, a file whose path contains `{{`, or a file that already contains `{{` or `{%`.
11. **Do not write `coding:` or `coding=` in lines 1 and 2** (`encoding:` contains it). Python reads such a comment as an encoding declaration. The Emacs form `-*- coding: x -*-` counts in any language.
12. **Java: do not write a backslash and `u` followed by four hex digits.** Java decodes it before it finds the comment end.
13. **SQL: put a space after `--`.** MySQL reads `--x` as two minus signs. **YAML: indent with spaces.** A tab in an inserted line is a parse error. **Makefile: never start an inserted line with a tab.** It becomes a recipe line.
14. **In a block comment never write `*/`, and avoid `/*`.** The first `*/` ends the comment, and a glob such as `src/**/*.ts` contains one. SQL and Rust nest block comments, so an unmatched `/*` inside leaves the comment open. Write globs in prose ("every `.ts` file under `src`") or inside a `//` comment.

## When the file is Python

- A new docstring must not contain `>>>`. Show an example in prose, or as an indented line without the `>>>` prompt.
- A backslash in a new docstring can be a parse error, because a normal string reads `\u`, `\x` and `\N` as escapes. `C:\users` in a plain docstring is a "truncated \uXXXX escape" error. Write the docstring as a raw string (`r"""..."""`) or leave the backslash out.
- Never add a second module docstring, and never add a docstring to a function or class that already has one. Both change the syntax tree. If the module already has a docstring, put the header in `#` lines directly below it.
- A docstring is runtime data wherever something reads `__doc__`: Click and Typer help text, FastAPI and Django REST route descriptions in the OpenAPI schema, `argparse` calls with `description=__doc__`, PLY grammar rules. The verifier accepts a new docstring, but the new text changes what those tools print. Search the file for `__doc__` first. For a command, route, handler or parser function, and for a module whose docstring is passed on, write `#` comments instead.
- A base file that does not parse (Python 2 code, for example) fails with "base version does not parse". Skip the file and report it, as for JS and TS below.

## When the file is JavaScript or TypeScript

- Only the TypeScript compiler verifies these files. It needs `node` and exactly `typescript@5.6.3` (the verifier checks the package name, the version and a SHA-256 of `lib/typescript.js`, and skips any other copy without running it). It looks in each `DOCUMENT_REPO_TS_PATHS` entry, then the npm global root (`npm install -g typescript@5.6.3`). The target repo's own `node_modules` is searched only when `DOCUMENT_REPO_TS_ALLOW_REPO=1` is set, and then last, because it is part of the code being judged. Without it, every JS/TS file fails with "TypeScript compiler not available". Stop, report the files as unverifiable, and do not retry.
- A file the compiler cannot parse cleanly fails, even if your edit is fine. A typical cause is JSX in a `.ts`, `.mts` or `.cts` file, which TypeScript parses without JSX. If `detail` says "does not parse cleanly" for the base file too, skip the file and report it.
- In JSX, a `//` line between elements is rendered as text and fails. Put the comment above the component or element, outside the JSX, or write `{/* ... */}` alone on its own line between elements. Use `{/* ... */}` only that way and never inside a text run: next to text it can split the text, and the verifier then fails the file. The verifier compares JSX text as TypeScript and Babel (and so esbuild and swc) cook its whitespace. Compilers with their own JSX whitespace rules, such as Solid's dom-expressions or Vue's JSX, are not modelled. Every such rule probed so far is coarser, so it renders the same whenever both modelled rules do, but that is an assumption, not a proof.
- A shebang stays on line 1. A `'use strict'` line may have a comment above it.

## Judgement rules

These are not mechanical, and they decide whether the comments are worth keeping.

15. Explain why and intent. Do not restate what the code says (`# increment i` is forbidden).
16. No TODOs, no opinions about code quality, no names of people, no secrets, and no example values copied from real data.
17. SQL migration files get no comments at all: the inventory skips them (`skip: "migration"`), so they are never in a commenter's file list. A migration is applied history, and migration tools checksum it: one header comment makes Flyway refuse to migrate, Prisma offer a database reset and sqlx refuse to run. That covers any `.sql` under a `migrations/`, `migration/` or `migrate/` directory (Prisma's `migrations/<name>/migration.sql` included) and Flyway's `V<n>__*.sql`, `U<n>__*.sql` and `R__*.sql` anywhere.
18. Keep each doc comment to 12 lines. If it needs more, the module README is the place.
19. Write plain English. Follow `~/.claude/styles/WRITING_RULES.md` when it exists.
20. In Rust doc comments (`///`, `//!`), fence an example as `text`. An unmarked fence is compiled and run as a test by `cargo test`, and the verifier does not look inside it.
21. Write a `Traps:` line as what looks safe, what actually happens, and what to do instead, in one or two sentences. "Omits `ko_return` for one path" leaves out the consequence and the fix. Before you write one about a bare command, read the configuration the tool reads (a pyproject `addopts`, `package.json` scripts, a Makefile default): a default that changes what the command does is a trap. The orchestrator copies the ones that matter beyond the file into AGENTS.md.

## Formats

### Python

```python
"""Store and look up notes in Postgres.

Role: data-access layer for notes; the only module that writes the notes table.
Used by: api.routes (create and list endpoints), jobs.reindex.
Side effects: database writes; opens a pooled connection on first use.
Invariants: every stored note has a non-empty body.
"""


def create_note(body: str) -> Note:
    """Insert one note and return it with its new id.

    Args:
        body: The note text. Must not be empty or only whitespace.

    Returns:
        The stored Note, including the database-assigned ``id``.

    Raises:
        ValueError: If ``body`` is empty.
    """
    # Why: strip here rather than in the API so jobs.reindex gets the same rule.
    ...
```

When the module already has a docstring, the header is `#` lines below it:

```python
"""Existing module docstring, left as it is."""
# Used by: api.routes, jobs.reindex.
# Side effects: database writes.
```

### TypeScript and JavaScript

```typescript
/**
 * @file Capture pipeline entry: turns an incoming message into a stored thought.
 *
 * Role: orchestrates parse, embed and store for one message.
 * Used by: server/routes/capture.ts.
 * Side effects: calls the embedding service; writes to Postgres.
 */

/**
 * Parse, embed and store one captured message.
 *
 * @param msg - Raw message from the capture endpoint.
 * @returns The stored thought's id.
 * @throws {EmbeddingError} When the embedding service is unreachable after retries.
 * @example
 * const id = await captureThought({ text: "Buy milk", source: "sms" });
 */
```

In JSX:

```tsx
export const NoteList = () => (
  <ul>
    {/* Why: keyed by id so a reorder does not remount rows. */}
    <Rows />
  </ul>
);
```

### SQL

```sql
-- Role: creates the notes table and its full-text index.
-- Invariants: body is NOT NULL and non-empty (CHECK constraint below).
-- Traps: applied in production; never edit, add a new migration instead.
```

### Shell, YAML, Dockerfile, TOML, Makefile

```bash
# Role: builds the API image and runs migrations before start.
# Used by: docker-compose.yml (api service).
# Side effects: runs `alembic upgrade head` against $DATABASE_URL.
```

### CSS and HTML

Use `/* ... */` (CSS) and `<!-- ... -->` (HTML) with the same labels, each comment on its own lines. A multi-line comment must open and close inside what you insert.

### Go, Rust, Java and the C family

| Language | Header | Doc comment |
|----------|--------|-------------|
| Go | `//` lines, then a blank line, then whatever the file started with (`package`, or a `//go:build` line, which Go allows line comments to precede). The blank line keeps the header from becoming the package documentation. A comment directly under a `//go:build` line is rejected. | `// Name does x.` directly above the declaration, starting with the name |
| Rust | `//!` lines at the top of the file, after any `#![...]` lines | `///` above the item |
| Java | `/** ... */` above the class | Javadoc `/** ... */` above the member |
| C, C++ | `/** ... */` or `//` lines at the top | Doxygen-style `/** ... */` above the declaration |
| C# | `///` with `<summary>`, written as well-formed XML (`&lt;`, `&amp;`) | `///` with `<summary>`, `<param>`, `<returns>` |
