# document-repo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a `document-repo` skill in `personal-plugin` that comments a target repo, writes its docs, and builds an offline explorer, all from one project model.

**Architecture:** A stdlib-only bundled Python tool (`tools/document-repo`) does every mechanical, testable step: inventory, module proposal, comment-only verification, model assembly and validation, line remapping, marker-section upserts, and change detection. The skill (`skills/document-repo/SKILL.md`) orchestrates subagents for the judgement work (analysis, synthesis, commenting, docs) and calls the tool between steps. The explorer is a fixed vanilla-JS template that reads `explorer/data/model.js`.

**Tech Stack:** Python ≥3.10 (stdlib only at runtime; pytest/pytest-cov/pytest-xdist/mypy for dev), Node + the target repo's `typescript` package (optional, for the JS/TS verifier), vanilla HTML/CSS/JS, Mermaid 11.4.1 (vendored).

**Spec:** `docs/plans/2026-11-22-document-repo-design.md` (approved 2026-11-22, D73).

## Global Constraints

- Python `requires-python = ">=3.10"`; runtime `dependencies = []`; coverage `fail_under = 90`.
- CI runs `ruff==0.14.10` (`ruff check` + `ruff format --check`, line length 100, rules E/F/W/I per root `ruff.toml`) on `plugins/*/tools/*/src` and `tests`. Run both from the repo root before every commit that touches Python.
- Tool runs from source: `PYTHONPATH="$PLUGIN_DIR/tools/document-repo/src" python3 -m document_repo …`. Never declare tools in `plugin.json`.
- Skill `name: document-repo` must equal the directory name.
- `description` ≤1024 chars and contains **no colon-space** (it silently drops all frontmatter). Use em dashes.
- SKILL.md body (after frontmatter) strictly under 500 lines (`scripts/check_skill_budget.py`).
- Never write a live dynamic-injection form in SKILL.md or references. Never write the bare deep-reasoning trigger word (see repo `CLAUDE.md`).
- Do **not** add `effort: high` (an absent field already means `high`, D67).
- `disable-model-invocation: true` (the skill writes to many files and must be user-invoked).
- The explorer makes **zero network requests** and no model value may become script. Only local `<script src>`; a CSP meta (`default-src 'none'; script-src 'self'; …`) enforces both. Mermaid **11.17.2** (was 11.4.1: nine advisories, two exploits confirmed in review), vendored at `explorer/vendor/mermaid.min.js`.
- Model `schema_version` is `1`. Each snippet is at most 30 lines.
- Generated doc text always sits between `<!-- document-repo:start:<name> -->` and `<!-- document-repo:end:<name> -->`.
- Bump `personal-plugin` 11.10.0 → **11.11.0** and add a CHANGELOG entry in the same PR.
- Repo rules: write a `LAB_NOTEBOOK.md` entry before the first commit (Entry 070 covers this whole build); lint markdown with `npx -y markdownlint-cli@0.45.0 <file>` before each commit that adds markdown.
- Every commit message ends with:

  ```text
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i
  ```

## File Map

```text
plugins/personal-plugin/tools/document-repo/
  pyproject.toml
  src/document_repo/
    __init__.py          version
    __main__.py          python -m entry
    cli.py               argparse; one small handler per subcommand
    languages.py         extension -> Lang (comment syntax, verify method)
    inventory.py         file walk, skip reasons, entry candidates
    modules.py           module boundary proposal
    verify.py            comment-only proof (python-ast, ts-printer, comment-lines)
    ts_print.js          node helper for the ts-printer method
    schema.py            model contract + validator
    build.py             assemble model, write explorer data, install template
    remap.py             shift model line numbers after comments are inserted
    docs.py              marker-section upsert
    changes.py           update-mode change detection
  tests/
    conftest.py
    fixtures/sample_model.json
    test_languages.py test_inventory.py test_modules.py test_verify.py
    test_verify_ts.py test_schema.py test_build.py test_remap.py
    test_docs.py test_changes.py test_cli.py test_explorer_template.py
plugins/personal-plugin/skills/document-repo/
  SKILL.md
  references/model-schema.md comment-standards.md doc-templates.md
  references/explorer-contract.md update-mode.md agent-prompts.md
  templates/explorer/index.html styles.css app.js
  templates/explorer/vendor/mermaid.min.js vendor/README.md
evals/skills/document-repo.eval.md
.github/workflows/test.yml            (modify: new non-required job + compat step)
plugins/personal-plugin/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, CHANGELOG.md, README.md, CLAUDE.md (bump + regenerate)
```

## Shared Definitions (used across tasks)

- `Lang(name: str, line: tuple[str, ...], block: tuple[tuple[str, str], ...], verify_method: str)`; `detect(path: str) -> Lang | None`; `EXT: dict[str, Lang]`.
- `build_inventory(root: Path) -> dict` → `{"root", "files": [{"path","lang","lines","bytes","skip","header_only"}], "manifests", "entry_candidates", "summary"}`.
- `propose_modules(inventory: dict) -> dict` → `{"modules": [{"id","path","files","lines"}]}`.
- `Result(path, method, ok, detail)`; `verify_file(repo: Path, rel: str, before_ref: str = "HEAD") -> Result`; `changed_files(repo: Path, ref: str) -> list[str]`.
- `validate(model: dict) -> list[str]`; `SCHEMA_VERSION = 1`.
- `assemble_model(run_dir: Path, repo: Path, base_model: dict | None = None, now: str | None = None) -> tuple[dict, list[dict]]`; `write_explorer_data(model: dict, out_dir: Path) -> dict`; `install_template(template_dir: Path, explorer_dir: Path) -> None`; `normalize_remote(url: str | None) -> str | None`.
- `line_map(before: list[str], after: list[str]) -> list[int]`; `remap_model(model: dict, repo: Path, new_ref: str) -> tuple[dict, list[str]]`.
- `upsert_section(text: str, name: str, body: str) -> str`; `upsert_file(path: Path, name: str, body: str) -> None`.
- `module_for(path: str, modules: list[dict]) -> str | None`; `compute_changes(repo: Path, state: dict, model: dict) -> dict`.
- Run directory (scratch, never committed): `$TARGET/.document-repo/`, made self-ignoring by a `.gitignore` containing `*`. Not under `.git/`: Claude Code blocks agent writes inside `.git/`, which would stop subagents from saving their output.

---

### Task 0: Open the lab notebook entry

**Files:**
- Modify: `LAB_NOTEBOOK.md` (append Entry 070; add Action Item)

- [ ] **Step 1: Make the build branch**

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace
git fetch -q origin && git status -sb | head -1
git switch -c feat/document-repo docs/document-repo-design
```

Expected: a new branch based on the spec branch. If `origin/main` moved, rebase the spec branch first: `git rebase origin/main`.

- [ ] **Step 2: Append the entry**

Append to the end of `LAB_NOTEBOOK.md`:

```markdown

### Entry 070 — Build `document-repo` (tool + skill + explorer + eval) [skill] [build] [ci]

**Date:** 2026-11-22
**Environment:** macOS, branch `feat/document-repo` off `docs/document-repo-design`. personal-plugin 11.10.0 → 11.11.0.

**Objective:** Implement `docs/plans/2026-11-22-document-repo-plan.md` (D73).

**Hypothesis:** All tool tests pass at ≥90% coverage; every repo gate (`check_injections`, `check_skill_budget`, `check_eval_mapping`, `update-readme --check`, `check_version_bump`, `claude plugin validate --strict`) passes; acceptance on open-brain and retire meets spec criteria 1–6.

**Rollback Plan:** `git switch main && git branch -D feat/document-repo`. Acceptance trials run in throwaway clones under `~/dev/doc-repo-trials/`; delete that directory to undo. Nothing is pushed to open-brain or retire.

**Results:** (log per task as it completes)
```

- [ ] **Step 3: Lint and commit**

```bash
npx -y markdownlint-cli@0.45.0 LAB_NOTEBOOK.md
git add LAB_NOTEBOOK.md
git commit -m "docs: open E070 for the document-repo build

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 1: Tool scaffold, language table, CLI skeleton

**Files:**
- Create: `plugins/personal-plugin/tools/document-repo/pyproject.toml`, `.gitignore`
- Create: `plugins/personal-plugin/tools/document-repo/src/document_repo/__init__.py`
- Create: `plugins/personal-plugin/tools/document-repo/src/document_repo/__main__.py`
- Create: `plugins/personal-plugin/tools/document-repo/src/document_repo/cli.py`
- Create: `plugins/personal-plugin/tools/document-repo/src/document_repo/languages.py`
- Create: `plugins/personal-plugin/tools/document-repo/tests/conftest.py`
- Test: `plugins/personal-plugin/tools/document-repo/tests/test_languages.py`, `tests/test_cli.py`

**Interfaces:**
- Produces: `Lang`, `detect`, `EXT`, `NAMES`, `VERIFY_METHODS`; `cli.emit(obj, out)`, `cli.build_parser()`, `cli.main(argv) -> int`; pytest fixtures `make_repo(files) -> Path` and `git(repo, *args) -> str`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "document-repo"
version = "0.1.0"
description = "Mechanical helpers for the document-repo skill (inventory, comment-only verifier, model build)"
license = {text = "MIT"}
requires-python = ">=3.10"
# Dependency choice: stdlib only, permanently. The tool reads files and shells
# out to git (and optionally node); it never needs a third-party package.
dependencies = []

[project.scripts]
document-repo = "document_repo.__main__:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-xdist>=3.5",
    "mypy>=1.8.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
document_repo = ["*.js"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--cov=document_repo --cov-report=term-missing"

[tool.coverage.run]
source = ["src/document_repo"]
branch = true

[tool.coverage.report]
fail_under = 90

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

Also create `plugins/personal-plugin/tools/document-repo/.gitignore`:

```gitignore
.venv/
__pycache__/
*.egg-info/
.coverage
.pytest_cache/
.mypy_cache/
```

- [ ] **Step 2: Write the package entry files**

`src/document_repo/__init__.py`:

```python
"""Mechanical helpers for the document-repo skill.

The skill does the judgement work (reading code, writing prose). This package
does every step that must be exact and testable: listing files, proving that
an edit only added comments, validating the project model, and building the
explorer's data files.
"""

__version__ = "0.1.0"
```

`src/document_repo/__main__.py`:

```python
"""Entry point for ``python -m document_repo``."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":  # pragma: no cover - exercised via subprocess
    sys.exit(main())
```

- [ ] **Step 3: Write the failing tests**

`tests/conftest.py`:

```python
"""Shared fixtures: throwaway git repos built from a dict of files."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

GIT = ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "-c", "commit.gpgsign=false"]


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run([*GIT, "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def _write(repo: Path, files: dict[str, str | bytes]) -> None:
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")


@pytest.fixture
def make_repo(tmp_path: Path) -> Callable[[dict[str, str | bytes]], Path]:
    def _make(files: dict[str, str | bytes]) -> Path:
        repo = tmp_path / "repo"
        repo.mkdir()
        run_git(repo, "init", "-q", "-b", "main")
        _write(repo, files)
        run_git(repo, "add", "-A")
        run_git(repo, "commit", "-q", "-m", "init")
        return repo

    return _make


@pytest.fixture
def git() -> Callable[..., str]:
    return run_git


@pytest.fixture
def commit_files(git: Callable[..., str]) -> Callable[[Path, dict[str, str | bytes], str], str]:
    def _commit(repo: Path, files: dict[str, str | bytes], message: str = "change") -> str:
        _write(repo, files)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message)
        return git(repo, "rev-parse", "HEAD").strip()

    return _commit
```

`tests/test_languages.py`:

```python
import pytest

from document_repo.languages import EXT, NAMES, VERIFY_METHODS, detect


@pytest.mark.parametrize(
    "path,name",
    [
        ("a/b.py", "python"),
        ("x.ts", "typescript"),
        ("x.tsx", "typescript"),
        ("x.mts", "typescript"),
        ("x.js", "javascript"),
        ("x.mjs", "javascript"),
        ("x.jsx", "javascript"),
        ("db/001.sql", "sql"),
        ("run.sh", "shell"),
        ("ci.yml", "yaml"),
        ("ci.YAML", "yaml"),
        ("Dockerfile", "dockerfile"),
        ("Dockerfile.dev", "dockerfile"),
        ("Makefile", "make"),
        ("s.css", "css"),
        ("p.html", "html"),
    ],
)
def test_detect_known(path: str, name: str) -> None:
    lang = detect(path)
    assert lang is not None and lang.name == name


@pytest.mark.parametrize("path", ["data.json", "README.md", "img.png", "noext", "x.lock"])
def test_detect_unknown(path: str) -> None:
    assert detect(path) is None


@pytest.mark.parametrize("lang", [*EXT.values(), *NAMES.values()])
def test_every_lang_is_well_formed(lang) -> None:
    # Derived from the tables themselves, never a copied list (repo rule).
    assert lang.verify_method in VERIFY_METHODS
    assert lang.line or lang.block
    for start, end in lang.block:
        assert start and end


def test_python_and_ts_methods() -> None:
    assert detect("a.py").verify_method == "python-ast"
    assert detect("a.ts").verify_method == "ts-printer"
    assert detect("a.sql").verify_method == "comment-lines"
```

`tests/test_cli.py`:

```python
import subprocess
import sys

import pytest

from document_repo import __version__
from document_repo.cli import main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_subcommand_prints_help_and_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_module_entry_runs() -> None:
    proc = subprocess.run([sys.executable, "-m", "document_repo", "--version"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert __version__ in proc.stdout
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
cd plugins/personal-plugin/tools/document-repo
python3 -m venv .venv && . .venv/bin/activate && pip install -q -e ".[dev]"
pytest -q --no-cov
```

Expected: FAIL / errors with `ModuleNotFoundError: No module named 'document_repo.languages'` and `document_repo.cli`.

- [ ] **Step 5: Write `languages.py`**

```python
"""Map a file path to its language and comment syntax.

Every other module asks this table one question: "if I add a comment to this
file, what does a comment look like, and how do I prove nothing else
changed?" A file whose type is not in the table has no known comment syntax,
so the skill never comments it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

#: How verify.py proves an edit is comment-only, per language.
VERIFY_METHODS = frozenset({"python-ast", "ts-printer", "comment-lines"})


@dataclass(frozen=True)
class Lang:
    """Comment syntax for one language.

    ``line`` holds line-comment prefixes (``#``, ``//``, ``--``).
    ``block`` holds (start, end) pairs (``/*``, ``*/``).
    ``verify_method`` names the proof verify.py uses.
    """

    name: str
    line: tuple[str, ...]
    block: tuple[tuple[str, str], ...]
    verify_method: str


C_BLOCK = (("/*", "*/"),)
PYTHON = Lang("python", ("#",), (), "python-ast")
TYPESCRIPT = Lang("typescript", ("//",), C_BLOCK, "ts-printer")
JAVASCRIPT = Lang("javascript", ("//",), C_BLOCK, "ts-printer")
SQL = Lang("sql", ("--",), C_BLOCK, "comment-lines")
SHELL = Lang("shell", ("#",), (), "comment-lines")
YAML = Lang("yaml", ("#",), (), "comment-lines")
TOML = Lang("toml", ("#",), (), "comment-lines")
DOCKERFILE = Lang("dockerfile", ("#",), (), "comment-lines")
MAKE = Lang("make", ("#",), (), "comment-lines")
CSS = Lang("css", (), C_BLOCK, "comment-lines")
HTML = Lang("html", (), (("<!--", "-->"),), "comment-lines")
C_LIKE = {name: Lang(name, ("//",), C_BLOCK, "comment-lines") for name in ("go", "rust", "java", "c", "cpp", "csharp")}

EXT: dict[str, Lang] = {
    ".py": PYTHON,
    ".ts": TYPESCRIPT, ".tsx": TYPESCRIPT, ".mts": TYPESCRIPT, ".cts": TYPESCRIPT,
    ".js": JAVASCRIPT, ".jsx": JAVASCRIPT, ".mjs": JAVASCRIPT, ".cjs": JAVASCRIPT,
    ".sql": SQL,
    ".sh": SHELL, ".bash": SHELL, ".zsh": SHELL,
    ".yml": YAML, ".yaml": YAML,
    ".toml": TOML,
    ".css": CSS, ".scss": CSS,
    ".html": HTML, ".htm": HTML,
    ".go": C_LIKE["go"], ".rs": C_LIKE["rust"], ".java": C_LIKE["java"],
    ".c": C_LIKE["c"], ".h": C_LIKE["c"], ".cpp": C_LIKE["cpp"], ".hpp": C_LIKE["cpp"],
    ".cs": C_LIKE["csharp"],
}

#: Files recognised by exact name rather than extension.
NAMES: dict[str, Lang] = {"Dockerfile": DOCKERFILE, "Makefile": MAKE, "Containerfile": DOCKERFILE}


def detect(path: str) -> Lang | None:
    """Return the Lang for ``path``, or None when it has no known comment syntax."""
    p = PurePosixPath(path)
    if p.name in NAMES:
        return NAMES[p.name]
    if p.name.startswith(("Dockerfile.", "Containerfile.")):
        return DOCKERFILE
    return EXT.get(p.suffix.lower())
```

- [ ] **Step 6: Write `cli.py`**

```python
"""Command-line front end for the document-repo tool.

Each subcommand is a thin wrapper: parse arguments, call one library
function, print JSON. Exit codes: 0 success, 1 a check failed (for example a
file changed in more than its comments), 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __version__


def emit(obj: Any, out: Path | None = None) -> None:
    """Write ``obj`` as pretty JSON to ``out``, or to stdout when ``out`` is None."""
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if out is None:
        sys.stdout.write(text)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="document_repo", description="Helpers for the document-repo skill.")
    parser.add_argument("--version", action="version", version=f"document_repo {__version__}")
    sub = parser.add_subparsers(dest="cmd", metavar="<command>")
    # SUBCOMMANDS — each later task adds one `_register_<name>(sub)` call here, in task order.
    _ = sub
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 2
    return int(args.func(args))
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest -q --no-cov`
Expected: all tests in `test_languages.py` and `test_cli.py` PASS.

- [ ] **Step 8: Commit**

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace
git add plugins/personal-plugin/tools/document-repo
git commit -m "feat(document-repo): tool scaffold, language table, CLI skeleton

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 2: Inventory

**Files:**
- Create: `src/document_repo/inventory.py`
- Modify: `src/document_repo/cli.py` (register `inventory`)
- Test: `tests/test_inventory.py`

(All paths and commands in Tasks 2–10 are relative to `plugins/personal-plugin/tools/document-repo/`. Start each task with `cd /Users/troydavis/dev/personal/plugins/claude-marketplace/plugins/personal-plugin/tools/document-repo && . .venv/bin/activate`.)

**Interfaces:**
- Consumes: `languages.detect`.
- Produces: `build_inventory(root: Path) -> dict`; `list_files(root: Path) -> list[str]`; `skip_reason(root: Path, rel: str) -> str | None`. Skip reasons are exactly: `skipped-dir`, `lock-file`, `minified`, `binary`, `no-comment-syntax`, `generated`. CLI: `inventory <repo> [--out PATH]`.

- [ ] **Step 1: Write the failing test**

`tests/test_inventory.py`:

```python
import json
from pathlib import Path

from document_repo.cli import main
from document_repo.inventory import SKIP_REASONS, build_inventory


def _files() -> dict[str, str | bytes]:
    return {
        "src/app.py": "print('hi')\nprint('bye')\n",
        "src/util.ts": "export const x = 1;\n",
        "node_modules/pkg/index.js": "x\n",
        "package-lock.json": "{}\n",
        "web/app.min.js": "a\n",
        "img.png": b"\x89PNG\x00\x00",
        "data.json": "{}\n",
        "gen/api.ts": "// Code generated by protoc. DO NOT EDIT.\nexport {}\n",
        "db/migrations/001_init.sql": "create table t (id int);\n",
        "explorer/app.js": "x\n",
        "package.json": json.dumps({"main": "src/util.ts", "bin": {"tool": "bin/tool.js"}, "scripts": {"start": "node x"}}),
        "pyproject.toml": '[project]\nname = "x"\n[project.scripts]\nx = "x.cli:main"\n',
        "Dockerfile": "FROM python:3.12\n",
        "src/main.py": "pass\n",
    }


def test_inventory_classifies_files(make_repo) -> None:
    inv = build_inventory(make_repo(_files()))
    by = {f["path"]: f for f in inv["files"]}
    assert by["src/app.py"] == {"path": "src/app.py", "lang": "python", "lines": 2, "bytes": 25, "skip": None, "header_only": False}
    assert by["node_modules/pkg/index.js"]["skip"] == "skipped-dir"
    assert by["explorer/app.js"]["skip"] == "skipped-dir"
    assert by["package-lock.json"]["skip"] == "lock-file"
    assert by["web/app.min.js"]["skip"] == "minified"
    assert by["img.png"]["skip"] == "binary"
    assert by["data.json"]["skip"] == "no-comment-syntax"
    assert by["gen/api.ts"]["skip"] == "generated"
    assert by["db/migrations/001_init.sql"]["header_only"] is True
    assert {f["skip"] for f in inv["files"]} <= SKIP_REASONS | {None}
    assert inv["summary"]["by_lang"] == {"dockerfile": 1, "python": 2, "sql": 1, "toml": 1, "typescript": 1}
    assert inv["summary"]["source_files"] == 6
    assert "package.json" in inv["manifests"] and "pyproject.toml" in inv["manifests"]


def test_entry_candidates(make_repo) -> None:
    inv = build_inventory(make_repo(_files()))
    whys = {(e["path"], e["why"]) for e in inv["entry_candidates"]}
    assert ("src/main.py", "conventional entry-point name") in whys
    assert ("package.json", "package main -> src/util.ts") in whys
    assert ("package.json", "package bin tool -> bin/tool.js") in whys
    assert ("package.json", "npm script start -> node x") in whys
    assert ("pyproject.toml", "console script x -> x.cli:main") in whys
    assert ("Dockerfile", "container definition") in whys


def test_untracked_included_and_gitignored_excluded(make_repo) -> None:
    repo = make_repo({".gitignore": "secret.py\n", "a.py": "x = 1\n"})
    (repo / "new.py").write_text("y = 2\n")
    (repo / "secret.py").write_text("z = 3\n")
    paths = {f["path"] for f in build_inventory(repo)["files"]}
    assert "new.py" in paths and "secret.py" not in paths


def test_non_git_directory_falls_back_to_walk(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("x\n")
    (tmp_path / "a.py").write_text("x = 1\n")
    paths = {f["path"] for f in build_inventory(tmp_path)["files"]}
    assert paths == {"a.py"}


def test_bad_package_json_is_ignored(make_repo) -> None:
    inv = build_inventory(make_repo({"package.json": "{not json"}))
    assert inv["entry_candidates"] == []


def test_cli_inventory_writes_file(make_repo, tmp_path: Path) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    out = tmp_path / "out" / "inv.json"
    assert main(["inventory", str(repo), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["summary"]["source_files"] == 1
```

Note the `bytes` value: `"print('hi')\nprint('bye')\n"` is 12 + 13 = 25 bytes.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_inventory.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.inventory'`.

- [ ] **Step 3: Write `inventory.py`**

```python
"""List every file in a target repo and decide which ones the skill documents.

The output ("the inventory") is the first input to the whole run. It says, per
file: its language, its size, and either ``skip: None`` (document it) or the
reason to leave it alone. It also lists dependency manifests and likely entry
points, so the analysis agents know where execution starts.

Files are listed with ``git ls-files`` so .gitignore is honoured. A directory
that is not a git repo falls back to a plain directory walk.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any

from .languages import detect

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 has no tomllib
    tomllib = None  # type: ignore[assignment]

SKIP_REASONS = frozenset({"skipped-dir", "lock-file", "minified", "binary", "no-comment-syntax", "generated"})
SKIP_DIRS = frozenset({
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "coverage",
    ".next", ".nuxt", ".turbo", ".cache", "vendor", "third_party", ".mypy_cache",
    ".pytest_cache", ".tox", "target", ".document-repo",
})
#: The skill's own output directory, skipped only at the repo root.
OUTPUT_DIR = "explorer"
LOCK_FILES = frozenset({
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "Pipfile.lock",
    "uv.lock", "Cargo.lock", "go.sum", "composer.lock", "Gemfile.lock",
})
MINIFIED_SUFFIXES = (".min.js", ".min.css", ".map")
GENERATED_MARKERS = ("@generated", "do not edit", "auto-generated", "autogenerated", "code generated")
MANIFESTS = frozenset({
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "go.mod",
    "Cargo.toml", "pom.xml", "build.gradle", "Gemfile", "composer.json",
})
COMPOSE_FILES = frozenset({"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"})
ENTRY_NAMES = frozenset({
    "main.py", "__main__.py", "app.py", "manage.py", "server.py", "cli.py", "wsgi.py", "asgi.py",
    "index.ts", "index.js", "main.ts", "main.js", "server.ts", "server.js", "app.ts", "app.js", "main.go",
})
MIGRATION_DIRS = frozenset({"migrations", "migration", "migrate"})
HEAD_BYTES = 8192


def _walk(root: Path) -> Iterator[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield Path(dirpath, name).relative_to(root).as_posix()


def list_files(root: Path) -> list[str]:
    """Tracked plus untracked-but-not-ignored files, as sorted POSIX paths."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted(_walk(root))
    names = proc.stdout.decode("utf-8", "surrogateescape").split("\0")
    return sorted({n for n in names if n and (root / n).is_file()})


def skip_reason(root: Path, rel: str) -> str | None:
    """Return why ``rel`` must not be commented, or None when it should be."""
    parts = PurePosixPath(rel).parts
    if parts[0] == OUTPUT_DIR or any(p in SKIP_DIRS for p in parts[:-1]):
        return "skipped-dir"
    name = parts[-1]
    if name in LOCK_FILES or name.endswith(".lock"):
        return "lock-file"
    if name.endswith(MINIFIED_SUFFIXES):
        return "minified"
    with (root / rel).open("rb") as fh:
        head = fh.read(HEAD_BYTES)
    if b"\0" in head:
        return "binary"
    if detect(rel) is None:
        return "no-comment-syntax"
    first_lines = head.decode("utf-8", "replace").splitlines()[:5]
    if any(marker in line.lower() for line in first_lines for marker in GENERATED_MARKERS):
        return "generated"
    return None


def count_lines(path: Path) -> int:
    """Count lines without loading the whole file (memory ceiling rule)."""
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def _is_migration(rel: str) -> bool:
    return any(p.lower() in MIGRATION_DIRS for p in PurePosixPath(rel).parts[:-1])


def _package_json_entries(root: Path, rel: str) -> list[dict[str, str]]:
    try:
        data = json.loads((root / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    out: list[dict[str, str]] = []
    if isinstance(data.get("main"), str):
        out.append({"path": rel, "why": f"package main -> {data['main']}"})
    bin_field = data.get("bin")
    if isinstance(bin_field, str):
        out.append({"path": rel, "why": f"package bin -> {bin_field}"})
    elif isinstance(bin_field, dict):
        for name, target in sorted(bin_field.items()):
            out.append({"path": rel, "why": f"package bin {name} -> {target}"})
    scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
    for key in ("start", "dev", "serve"):
        if key in scripts:
            out.append({"path": rel, "why": f"npm script {key} -> {scripts[key]}"})
    return out


def _pyproject_entries(root: Path, rel: str) -> list[dict[str, str]]:
    if tomllib is None:  # pragma: no cover - Python 3.10
        return []
    try:
        data = tomllib.loads((root / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    scripts = data.get("project", {}).get("scripts", {})
    return [{"path": rel, "why": f"console script {name} -> {target}"} for name, target in sorted(scripts.items())]


def entry_candidates(root: Path, files: list[str]) -> list[dict[str, str]]:
    """Places where execution likely starts. Hints for analysts, not facts."""
    out: list[dict[str, str]] = []
    for rel in files:
        p = PurePosixPath(rel)
        if p.parts[0] == OUTPUT_DIR or any(part in SKIP_DIRS for part in p.parts[:-1]):
            continue
        if p.name in ENTRY_NAMES and len(p.parts) <= 4:
            out.append({"path": rel, "why": "conventional entry-point name"})
        if p.name == "package.json":
            out.extend(_package_json_entries(root, rel))
        if p.name == "pyproject.toml":
            out.extend(_pyproject_entries(root, rel))
        if p.name.startswith(("Dockerfile", "Containerfile")) or p.name in COMPOSE_FILES:
            out.append({"path": rel, "why": "container definition"})
    return out


def build_inventory(root: Path) -> dict[str, Any]:
    """Describe every file under ``root``. See the module docstring."""
    root = root.resolve()
    rels = list_files(root)
    files: list[dict[str, Any]] = []
    by_lang: dict[str, int] = {}
    for rel in rels:
        reason = skip_reason(root, rel)
        lang = detect(rel)
        files.append({
            "path": rel,
            "lang": lang.name if lang else None,
            "lines": count_lines(root / rel),
            "bytes": (root / rel).stat().st_size,
            "skip": reason,
            "header_only": bool(reason is None and lang is not None and lang.name == "sql" and _is_migration(rel)),
        })
        if reason is None and lang is not None:
            by_lang[lang.name] = by_lang.get(lang.name, 0) + 1
    return {
        "root": str(root),
        "files": files,
        "manifests": [r for r in rels if PurePosixPath(r).name in MANIFESTS],
        "entry_candidates": entry_candidates(root, rels),
        "summary": {"total_files": len(files), "source_files": sum(by_lang.values()), "by_lang": dict(sorted(by_lang.items()))},
    }
```

- [ ] **Step 4: Register the subcommand in `cli.py`**

Add above `build_parser`:

```python
def _cmd_inventory(args: argparse.Namespace) -> int:
    from .inventory import build_inventory

    emit(build_inventory(args.repo), args.out)
    return 0


def _register_inventory(sub: Any) -> None:
    p = sub.add_parser("inventory", help="list files, languages, skip reasons, entry points")
    p.add_argument("repo", type=Path)
    p.add_argument("--out", type=Path)
    p.set_defaults(func=_cmd_inventory)
```

In `build_parser`, replace the line `_ = sub` with:

```python
    _register_inventory(sub)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_inventory.py tests/test_cli.py -q --no-cov`
Expected: PASS. (`by_lang` counts `pyproject.toml` as toml and `Dockerfile` as dockerfile — both have `#` comments, so they are documentable.)

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/inventory.py src/document_repo/cli.py tests/test_inventory.py
git commit -m "feat(document-repo): inventory with skip reasons and entry candidates

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 3: Module proposal

**Files:**
- Create: `src/document_repo/modules.py`
- Modify: `src/document_repo/cli.py` (register `modules`)
- Test: `tests/test_modules.py`

**Interfaces:**
- Consumes: inventory dict from Task 2.
- Produces: `module_key(path: str) -> str`; `slug(key: str) -> str`; `propose_modules(inventory: dict) -> dict` → `{"modules": [{"id": str, "path": str, "files": [str], "lines": int}]}` sorted by `id`; the root module has `id "root"`, `path "."`. CLI: `modules <inventory.json> [--out PATH]`.

- [ ] **Step 1: Write the failing test**

`tests/test_modules.py`:

```python
import json
from pathlib import Path

import pytest

from document_repo.cli import main
from document_repo.modules import module_key, propose_modules, slug


@pytest.mark.parametrize(
    "path,key",
    [
        ("setup.py", "root"),
        ("src/main.py", "src"),
        ("src/api/a.py", "src/api"),
        ("packages/web/src/x.ts", "packages/web"),
        ("web/index.ts", "web"),
        (".github/workflows/ci.yml", ".github"),
    ],
)
def test_module_key(path: str, key: str) -> None:
    assert module_key(path) == key


@pytest.mark.parametrize("key,expected", [("root", "root"), ("src/api", "src-api"), (".github", "github"), ("A B", "a-b")])
def test_slug(key: str, expected: str) -> None:
    assert slug(key) == expected


def _inv() -> dict:
    files = [
        ("src/api/a.py", None, 10), ("src/api/b.py", None, 5), ("src/main.py", None, 3),
        ("web/index.ts", None, 7), ("README.md", "no-comment-syntax", 1), ("setup.py", None, 2),
    ]
    return {"files": [{"path": p, "skip": s, "lines": n} for p, s, n in files]}


def test_propose_groups_and_sorts() -> None:
    mods = propose_modules(_inv())["modules"]
    assert [m["id"] for m in mods] == ["root", "src", "src-api", "web"]
    api = next(m for m in mods if m["id"] == "src-api")
    assert api == {"id": "src-api", "path": "src/api", "files": ["src/api/a.py", "src/api/b.py"], "lines": 15}
    assert next(m for m in mods if m["id"] == "root")["path"] == "."
    assert all("README.md" not in m["files"] for m in mods)


def test_cli_modules(tmp_path: Path) -> None:
    inv = tmp_path / "inv.json"
    inv.write_text(json.dumps(_inv()))
    out = tmp_path / "mods.json"
    assert main(["modules", str(inv), "--out", str(out)]) == 0
    assert len(json.loads(out.read_text())["modules"]) == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_modules.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.modules'`.

- [ ] **Step 3: Write `modules.py`**

```python
"""Propose module boundaries from the inventory.

A "module" is the unit of work for the rest of the run: one analysis agent,
one commenting agent, one README, one commit. This first cut is mechanical;
the skill then merges tiny modules and splits huge ones with judgement.

Rule: group by the first path segment, except under common grouping
directories (src, packages, apps, ...) where the second segment decides.
Top-level files form the "root" module.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

GROUPING_ROOTS = frozenset({"src", "packages", "apps", "services", "libs", "lib", "modules", "cmd", "internal"})


def module_key(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) == 1:
        return "root"
    if parts[0] in GROUPING_ROOTS and len(parts) > 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def slug(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-") or "root"


def propose_modules(inventory: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    for entry in inventory["files"]:
        if entry["skip"] is not None:
            continue
        key = module_key(entry["path"])
        group = groups.setdefault(key, {"id": slug(key), "path": "." if key == "root" else key, "files": [], "lines": 0})
        group["files"].append(entry["path"])
        group["lines"] += int(entry["lines"])
    for group in groups.values():
        group["files"].sort()
    return {"modules": sorted(groups.values(), key=lambda g: g["id"])}
```

- [ ] **Step 4: Register in `cli.py`**

Add above `build_parser`:

```python
def _cmd_modules(args: argparse.Namespace) -> int:
    from .modules import propose_modules

    emit(propose_modules(load_json(args.inventory)), args.out)
    return 0


def _register_modules(sub: Any) -> None:
    p = sub.add_parser("modules", help="propose module boundaries from an inventory")
    p.add_argument("inventory", type=Path)
    p.add_argument("--out", type=Path)
    p.set_defaults(func=_cmd_modules)
```

In `build_parser`, after `_register_inventory(sub)` add `_register_modules(sub)`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_modules.py -q --no-cov`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/modules.py src/document_repo/cli.py tests/test_modules.py
git commit -m "feat(document-repo): mechanical module boundary proposal

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 4: Comment-only verifier — Python AST and comment-lines

**Files:**
- Create: `src/document_repo/verify.py`
- Modify: `src/document_repo/cli.py` (register `verify`)
- Test: `tests/test_verify.py`

**Interfaces:**
- Consumes: `languages.detect`, `Lang`.
- Produces: `Result` dataclass with `to_dict()`; `git_show(repo, ref, rel) -> str | None`; `verify_file(repo: Path, rel: str, before_ref: str = "HEAD") -> Result` (compares the **working tree** file against `before_ref`); `changed_files(repo: Path, ref: str) -> list[str]`; `comment_chunk_ok(lines, lang) -> tuple[bool, str]`. `_ts_verify` is a stub returning `None` in this task (Task 5 fills it in). Methods reported: `python-ast`, `ts-printer`, `comment-lines`, `none`. CLI: `verify --repo R [--before REF] (--changed | FILE...)` → JSON list; exit 1 if any result is not ok.

- [ ] **Step 1: Write the failing tests**

`tests/test_verify.py`:

```python
import json

import pytest

from document_repo.cli import main
from document_repo.languages import detect
from document_repo.verify import changed_files, comment_chunk_ok, verify_file

BASE_PY = "def add(a, b):\n    return a + b\n"


def test_python_comments_and_docstrings_pass(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text(
        '"""Math helpers."""\n\n# Why: keep it simple.\ndef add(a, b):\n    """Add two numbers."""\n    return a + b  # sum\n'
    )
    r = verify_file(repo, "m.py")
    assert r.ok and r.method == "python-ast", r.detail


def test_python_docstring_added_to_pass_body(make_repo) -> None:
    repo = make_repo({"m.py": "def f():\n    pass\n"})
    (repo / "m.py").write_text('def f():\n    """Doc."""\n    pass\n')
    assert verify_file(repo, "m.py").ok


def test_python_code_change_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text("# note\ndef add(a, b):\n    return a - b\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and r.method == "python-ast"


def test_python_syntax_error_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text("def add(a, b:\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and "parse" in r.detail


def test_file_not_in_base_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "new.py").write_text("x = 1\n")
    r = verify_file(repo, "new.py")
    assert not r.ok and r.method == "none"


def test_unknown_language_fails(make_repo) -> None:
    repo = make_repo({"d.json": "{}\n"})
    assert not verify_file(repo, "d.json").ok


SQL = "select 1;\nselect 2;\n"


@pytest.mark.parametrize(
    "after",
    [
        "-- Header\nselect 1;\nselect 2;\n",
        "/* block\n   more */\nselect 1;\nselect 2;\n",
        "select 1;\n\n-- why the second query\nselect 2;\n",
        "/* one-line block */\nselect 1;\nselect 2;\n",
    ],
)
def test_sql_comment_only_passes(make_repo, after: str) -> None:
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").write_text(after)
    r = verify_file(repo, "q.sql")
    assert r.ok and r.method == "comment-lines", r.detail


@pytest.mark.parametrize(
    "after,needle",
    [
        ("select 1;\nselect 3;\n", "replace"),
        ("select 1;\n", "delete"),
        ("select 1; -- trailing\nselect 2;\n", "replace"),
        ("/* open\nselect 1;\nselect 2;\n", "unterminated"),
        ("/* x */ select 0;\nselect 1;\nselect 2;\n", "code after"),
        ("select 0;\nselect 1;\nselect 2;\n", "non-comment"),
    ],
)
def test_sql_negative_cases_fail(make_repo, after: str, needle: str) -> None:
    # Negative tests: a guard that cannot fail is worse than none (repo rule).
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").write_text(after)
    r = verify_file(repo, "q.sql")
    assert not r.ok and needle in r.detail, r.detail


def test_shell_code_added_fails(make_repo) -> None:
    repo = make_repo({"run.sh": "#!/bin/sh\necho a\n"})
    (repo / "run.sh").write_text("#!/bin/sh\n# say a\necho a\necho b\n")
    assert not verify_file(repo, "run.sh").ok


def test_comment_chunk_block_end_must_close_line() -> None:
    lang = detect("x.css")
    assert comment_chunk_ok(["/* a", " b */"], lang) == (True, "")
    ok, why = comment_chunk_ok(["/* a", " b */ x {}"], lang)
    assert not ok and "code after" in why


def test_changed_files(make_repo) -> None:
    repo = make_repo({"a.py": "x = 1\n", "README.md": "# r\n", "explorer/x.js": "x\n", "b.py": "y = 1\n"})
    (repo / "a.py").write_text("# c\nx = 1\n")
    (repo / "README.md").write_text("# r2\n")
    (repo / "explorer/x.js").write_text("y\n")
    assert changed_files(repo, "HEAD") == ["a.py"]


def test_cli_verify_exit_codes(make_repo, capsys) -> None:
    repo = make_repo({"a.py": "x = 1\n", "b.py": "y = 1\n"})
    (repo / "a.py").write_text("# ok\nx = 1\n")
    assert main(["verify", "--repo", str(repo), "a.py"]) == 0
    (repo / "b.py").write_text("y = 2\n")
    capsys.readouterr()
    assert main(["verify", "--repo", str(repo), "--changed"]) == 1
    results = json.loads(capsys.readouterr().out)
    assert {r["path"]: r["ok"] for r in results} == {"a.py": True, "b.py": False}


def test_cli_verify_needs_files_or_changed(make_repo) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    assert main(["verify", "--repo", str(repo)]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verify.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.verify'`.

- [ ] **Step 3: Write `verify.py`**

```python
"""Prove that an edited file changed only in its comments.

The skill promises never to change behaviour. This module is the proof. For
each file it compares the version at a base git ref with the working tree:

- python-ast: parse both, drop docstrings, compare the syntax trees.
- ts-printer: (JS/TS) re-print both with comments removed via the
  TypeScript compiler and compare the text. Falls back to comment-lines
  when node or typescript is not available.
- comment-lines: (everything else) a line diff may only INSERT lines, and
  every inserted line must be blank or a comment in that language.

A file that fails is reverted by the skill. This check is deliberately strict:
a false failure costs one reverted file; a false pass could ship a bug.
"""

from __future__ import annotations

import ast
import difflib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .inventory import OUTPUT_DIR
from .languages import Lang, detect


@dataclass
class Result:
    path: str
    method: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def git_show(repo: Path, ref: str, rel: str) -> str | None:
    """Return ``rel`` as it was at ``ref``, or None if it did not exist there."""
    proc = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True)
    if proc.returncode != 0:
        return None
    try:
        return proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _strip_docstrings(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]


def _python(rel: str, before: str, after: str) -> Result:
    try:
        tree_before = ast.parse(before)
    except SyntaxError as exc:
        return Result(rel, "python-ast", False, f"base version does not parse: {exc}")
    try:
        tree_after = ast.parse(after)
    except SyntaxError as exc:
        return Result(rel, "python-ast", False, f"edited version does not parse: {exc}")
    _strip_docstrings(tree_before)
    _strip_docstrings(tree_after)
    if ast.dump(tree_before) == ast.dump(tree_after):
        return Result(rel, "python-ast", True)
    return Result(rel, "python-ast", False, "syntax tree changed (code, not just comments or docstrings)")


def comment_chunk_ok(lines: list[str], lang: Lang) -> tuple[bool, str]:
    """True when every line in an inserted chunk is blank or a comment."""
    in_block: str | None = None
    for raw in lines:
        s = raw.strip()
        if in_block is not None:
            if in_block in s:
                if s.split(in_block, 1)[1].strip():
                    return False, f"code after block-comment end: {raw!r}"
                in_block = None
            continue
        if not s or any(s.startswith(m) for m in lang.line):
            continue
        for start, end in lang.block:
            if s.startswith(start):
                rest = s[len(start):]
                if end in rest:
                    if rest.split(end, 1)[1].strip():
                        return False, f"code after block-comment end: {raw!r}"
                else:
                    in_block = end
                break
        else:
            return False, f"non-comment line added: {raw!r}"
    if in_block is not None:
        return False, "unterminated block comment in inserted lines"
    return True, ""


def _comment_lines(rel: str, before: str, after: str, lang: Lang) -> Result:
    a, b = before.splitlines(), after.splitlines()
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag != "insert":
            return Result(rel, "comment-lines", False, f"{tag} of base lines {i1 + 1}-{i2}")
        ok, why = comment_chunk_ok(b[j1:j2], lang)
        if not ok:
            return Result(rel, "comment-lines", False, f"{why} (edited lines {j1 + 1}-{j2})")
    return Result(rel, "comment-lines", True)


def _ts_verify(repo: Path, rel: str, before: str, after: str) -> Result | None:
    """Placeholder until Task 5: None means "use comment-lines instead"."""
    return None


def verify_file(repo: Path, rel: str, before_ref: str = "HEAD") -> Result:
    """Compare the working-tree ``rel`` with ``before_ref``. See module docstring."""
    lang = detect(rel)
    if lang is None:
        return Result(rel, "none", False, "no known comment syntax for this file type")
    before = git_show(repo, before_ref, rel)
    if before is None:
        return Result(rel, "none", False, f"file is not in {before_ref} (or is not UTF-8)")
    try:
        after = (repo / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return Result(rel, "none", False, f"cannot read edited file: {exc}")
    if lang.verify_method == "python-ast":
        return _python(rel, before, after)
    if lang.verify_method == "ts-printer":
        ts_result = _ts_verify(repo, rel, before, after)
        if ts_result is not None:
            return ts_result
    return _comment_lines(rel, before, after, lang)


def changed_files(repo: Path, ref: str) -> list[str]:
    """Files changed in the working tree vs ``ref`` that have comment syntax.

    Markdown (no comment syntax) and the explorer output are excluded: they
    are documentation, not code, so they are never verified.
    """
    out = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", ref, "--"], capture_output=True, text=True, check=True
    ).stdout
    return sorted(p for p in out.splitlines() if p and not p.startswith(OUTPUT_DIR + "/") and detect(p) is not None)
```

- [ ] **Step 4: Register in `cli.py`**

Add above `build_parser`:

```python
def _cmd_verify(args: argparse.Namespace) -> int:
    from .verify import changed_files, verify_file

    if args.changed:
        files = changed_files(args.repo, args.before)
    elif args.files:
        files = list(args.files)
    else:
        sys.stderr.write("verify: give FILE paths or --changed\n")
        return 2
    results = [verify_file(args.repo, f, args.before).to_dict() for f in files]
    emit(results)
    return 0 if all(r["ok"] for r in results) else 1


def _register_verify(sub: Any) -> None:
    p = sub.add_parser("verify", help="prove files changed only in comments")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--before", default="HEAD", help="base git ref (default HEAD)")
    p.add_argument("--changed", action="store_true", help="verify every changed source file")
    p.add_argument("files", nargs="*")
    p.set_defaults(func=_cmd_verify)
```

In `build_parser`, add `_register_verify(sub)` after `_register_modules(sub)`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_verify.py -q --no-cov`
Expected: PASS. (`.ts` files currently use comment-lines because `_ts_verify` returns None.)

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/verify.py src/document_repo/cli.py tests/test_verify.py
git commit -m "feat(document-repo): comment-only verifier (python-ast, comment-lines)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 5: Comment-only verifier — JS/TS via the TypeScript printer

**Files:**
- Create: `src/document_repo/ts_print.js`
- Modify: `src/document_repo/verify.py` (replace `_ts_verify` stub; add helpers)
- Test: `tests/test_verify_ts.py`

**Interfaces:**
- Consumes: `Result`, `_comment_lines` from Task 4.
- Produces: `node_binary() -> str | None`; `ts_search_paths(repo: Path) -> list[str]`; `typescript_available(repo: Path) -> bool`; real `_ts_verify`. Env var `DOCUMENT_REPO_TS_PATHS` (os.pathsep-separated) adds search paths. `ts_print.js` exit 3 = typescript not found.

- [ ] **Step 1: Write the failing tests**

`tests/test_verify_ts.py`:

```python
import pytest

from document_repo import verify
from document_repo.verify import typescript_available, verify_file

BASE = "export function add(a: number, b: number): number {\n  return a + b;\n}\n"


@pytest.fixture
def ts_repo(make_repo):
    repo = make_repo({"m.ts": BASE, "c.tsx": "export const C = () => <div>hi</div>;\n", "j.js": "const x = 1;\n"})
    if not typescript_available(repo):
        pytest.skip("node + typescript not available (CI installs typescript globally)")
    return repo


def test_ts_comments_pass(ts_repo) -> None:
    (ts_repo / "m.ts").write_text("/** Add two numbers. */\n// why: demo\n" + BASE.replace("return", "// sum\n  return"))
    r = verify_file(ts_repo, "m.ts")
    assert r.ok and r.method == "ts-printer", r.detail


def test_ts_trailing_comment_passes(ts_repo) -> None:
    # Allowed by the printer method; the comment standards still forbid it.
    (ts_repo / "m.ts").write_text(BASE.replace("a + b;", "a + b; // sum"))
    assert verify_file(ts_repo, "m.ts").ok


def test_ts_code_change_fails(ts_repo) -> None:
    (ts_repo / "m.ts").write_text("// note\n" + BASE.replace("a + b", "a - b"))
    r = verify_file(ts_repo, "m.ts")
    assert not r.ok and r.method == "ts-printer"


def test_ts_new_parse_error_fails(ts_repo) -> None:
    (ts_repo / "m.ts").write_text(BASE + "/* unterminated\n")
    assert not verify_file(ts_repo, "m.ts").ok


def test_tsx_and_js(ts_repo) -> None:
    (ts_repo / "c.tsx").write_text("/** Greeting. */\nexport const C = () => <div>hi</div>;\n")
    (ts_repo / "j.js").write_text("// one\nconst x = 1;\n")
    assert verify_file(ts_repo, "c.tsx").ok
    assert verify_file(ts_repo, "j.js").ok


def test_fails_closed_without_node(make_repo, monkeypatch) -> None:
    # Addendum A / D74: JS/TS are verified only by the printer; no heuristic fallback.
    repo = make_repo({"m.ts": BASE})
    monkeypatch.setattr(verify, "node_binary", lambda: None)
    (repo / "m.ts").write_text("// c\n" + BASE)
    r = verify_file(repo, "m.ts")
    assert not r.ok and "TypeScript compiler not available" in r.detail


def test_search_paths_include_env(make_repo, monkeypatch, tmp_path) -> None:
    repo = make_repo({"m.ts": BASE})
    monkeypatch.setenv("DOCUMENT_REPO_TS_PATHS", str(tmp_path))
    assert str(tmp_path) in verify.ts_search_paths(repo)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verify_ts.py -q --no-cov`
Expected: FAIL with `ImportError: cannot import name 'typescript_available'`.

- [ ] **Step 3: Write `ts_print.js`**

```javascript
// Re-print a JS/TS file with every comment removed, using the TypeScript
// compiler found in the target repo (or a global install). Two versions of a
// file that print the same differ only in comments and formatting.
//
// Usage: node ts_print.js <search-paths-json> <before-file> <after-file> <virtual-name>
// Prints JSON {equal, before_errors, after_errors}. Exit 3 = typescript not found.
'use strict';
const fs = require('fs');

const [, , pathsJson, beforePath, afterPath, name] = process.argv;
let ts;
try {
  ts = require(require.resolve('typescript', { paths: JSON.parse(pathsJson) }));
} catch (err) {
  process.stdout.write(JSON.stringify({ error: 'typescript-not-found' }));
  process.exit(3);
}

function kindFor(fileName) {
  if (/\.tsx$/i.test(fileName)) return ts.ScriptKind.TSX;
  if (/\.jsx$/i.test(fileName)) return ts.ScriptKind.JSX;
  if (/\.(js|mjs|cjs)$/i.test(fileName)) return ts.ScriptKind.JS;
  return ts.ScriptKind.TS;
}

function print(path) {
  const text = fs.readFileSync(path, 'utf8');
  const sf = ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true, kindFor(name));
  const printer = ts.createPrinter({ removeComments: true });
  return { text: printer.printFile(sf), errors: (sf.parseDiagnostics || []).length };
}

const a = print(beforePath);
const b = print(afterPath);
process.stdout.write(JSON.stringify({ equal: a.text === b.text, before_errors: a.errors, after_errors: b.errors }));
```

- [ ] **Step 4: Replace the `_ts_verify` stub in `verify.py`**

Add imports at the top of `verify.py`:

```python
import functools
import json
import os
import shutil
import tempfile
```

Replace the whole `_ts_verify` placeholder with:

```python
TS_SCRIPT = Path(__file__).with_name("ts_print.js")


def node_binary() -> str | None:
    return shutil.which("node")


@functools.lru_cache(maxsize=1)
def _npm_global_root() -> str | None:
    npm = shutil.which("npm")
    if npm is None:
        return None
    proc = subprocess.run([npm, "root", "-g"], capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def ts_search_paths(repo: Path) -> list[str]:
    """Where to look for the typescript package: repo first, then env, then global."""
    paths = [str(repo)]
    extra = os.environ.get("DOCUMENT_REPO_TS_PATHS")
    if extra:
        paths.extend(p for p in extra.split(os.pathsep) if p)
    global_root = _npm_global_root()
    if global_root:
        paths.append(global_root)
    return paths


def _run_printer(repo: Path, rel: str, before: str, after: str) -> subprocess.CompletedProcess[str] | None:
    node = node_binary()
    if node is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp, "before"), Path(tmp, "after")
        a.write_text(before, encoding="utf-8")
        b.write_text(after, encoding="utf-8")
        return subprocess.run(
            [node, str(TS_SCRIPT), json.dumps(ts_search_paths(repo)), str(a), str(b), rel],
            capture_output=True,
            text=True,
        )


def typescript_available(repo: Path) -> bool:
    proc = _run_printer(repo, "probe.ts", "", "")
    return proc is not None and proc.returncode == 0


def _ts_verify(repo: Path, rel: str, before: str, after: str) -> Result | None:
    """Printer-based proof for JS/TS. None means "printer unavailable" (verify_file then fails)."""
    proc = _run_printer(repo, rel, before, after)
    if proc is None or proc.returncode == 3:
        return None
    if proc.returncode != 0:
        return Result(rel, "ts-printer", False, f"printer failed: {proc.stderr.strip()[:500]}")
    data = json.loads(proc.stdout)
    if data["after_errors"] > data["before_errors"]:
        return Result(rel, "ts-printer", False, "edited version has new parse errors")
    if data["equal"]:
        return Result(rel, "ts-printer", True)
    return Result(rel, "ts-printer", False, "code changed (printed output differs with comments removed)")
```

- [ ] **Step 5: Install typescript locally so the TS tests run, then run all verify tests**

```bash
npm install -g typescript@5.6.3
pytest tests/test_verify.py tests/test_verify_ts.py -q --no-cov
```

Expected: PASS, with no skips in `test_verify_ts.py`. If any TS test is skipped, `typescript_available` is wrong. Fix it before you commit.

- [ ] **Step 6: Negative-test the printer guard by hand**

```bash
python3 - <<'EOF'
from pathlib import Path
import subprocess, tempfile
from document_repo.verify import verify_file
d = Path(tempfile.mkdtemp())
subprocess.run(["git", "init", "-q", str(d)], check=True)
(d / "a.ts").write_text("export const x = 1;\n")
subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
subprocess.run(["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i"], check=True)
(d / "a.ts").write_text("// c\nexport const x = 2;\n")
print(verify_file(d, "a.ts"))
EOF
```

Expected: `Result(path='a.ts', method='ts-printer', ok=False, ...)`.

- [ ] **Step 7: Commit**

```bash
git add src/document_repo/ts_print.js src/document_repo/verify.py tests/test_verify_ts.py
git commit -m "feat(document-repo): TypeScript-printer proof for JS/TS comment edits

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 6: Model schema and validator

**Files:**
- Create: `src/document_repo/schema.py`
- Create: `tests/fixtures/sample_model.json`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces: `SCHEMA_VERSION = 1`; `MAX_SNIPPET_LINES = 30`; `SPEC` (dict); `OneOf`; `validate(model: dict) -> list[str]` (empty list = valid). Messages use dotted paths, for example `project.name: missing`, `modules[0].status: expected one of ['analyzed', 'not_analyzed']`.

- [ ] **Step 1: Write the fixture model**

`tests/fixtures/sample_model.json`:

```json
{
  "meta": {"schema_version": 1, "generated_at": "2026-11-22T12:00:00+00:00", "source_commit": "0123456789abcdef0123456789abcdef01234567", "repo_name": "demo", "repo_url": "https://github.com/example/demo"},
  "project": {
    "name": "Demo",
    "tagline": "A tiny service that stores notes.",
    "purpose": {"functional": "Lets you save a note and find it later.", "technical": "A FastAPI app over Postgres with a `notes` table."},
    "users": ["Note takers", "Developers extending the API"],
    "capabilities": [{"title": "Save notes", "functional": "Type a note and keep it.", "technical": "`POST /notes` inserts a row."}],
    "tech_stack": [{"name": "Python 3.12", "role": "API runtime"}, {"name": "PostgreSQL", "role": "Storage"}],
    "run": {"setup": ["pip install -e ."], "commands": [{"label": "Start the API", "command": "uvicorn demo.app:app"}]}
  },
  "architecture": {
    "summary": {"functional": "One app saves notes in one database.", "technical": "Stateless HTTP API; Postgres is the only state."},
    "components": [
      {"id": "api", "name": "API", "kind": "service", "module_ids": ["src-api"], "description": {"functional": "Takes requests.", "technical": "FastAPI routers."}},
      {"id": "db", "name": "Database", "kind": "datastore", "module_ids": ["db"], "description": {"functional": "Keeps notes.", "technical": "Postgres 16."}}
    ],
    "connections": [{"from": "api", "to": "db", "label": "SQL over asyncpg"}],
    "diagrams": [{"id": "overview", "title": "System overview", "mermaid": "flowchart LR\n  api[API] --> db[(Database)]"}]
  },
  "modules": [
    {
      "id": "db", "name": "Database schema", "path": "db", "status": "analyzed",
      "purpose": {"functional": "Defines where notes live.", "technical": "SQL migrations for the notes table."},
      "interface": [], "invariants": ["Migrations are append-only."],
      "dependencies": {"internal": [], "external": ["PostgreSQL"]},
      "key_files": [{"path": "db/migrations/001_init.sql", "role": "Creates the notes table"}]
    },
    {
      "id": "src-api", "name": "HTTP API", "path": "src/api", "status": "analyzed",
      "purpose": {"functional": "Receives notes from users.", "technical": "FastAPI routes and request models."},
      "interface": [{"name": "create_note", "kind": "function", "signature": "async def create_note(body: NoteIn) -> NoteOut", "description": "Stores one note.", "file": "src/api/routes.py", "line": 12}],
      "invariants": ["Every note has a non-empty body."],
      "dependencies": {"internal": ["db"], "external": ["fastapi", "asyncpg"]},
      "key_files": [{"path": "src/api/routes.py", "role": "Route handlers"}]
    }
  ],
  "flows": [
    {
      "id": "save-note", "title": "Save a note",
      "summary": {"functional": "What happens when you save a note.", "technical": "Request path from router to INSERT."},
      "steps": [
        {"title": "Request arrives", "text": {"functional": "The app gets your note.", "technical": "FastAPI validates `NoteIn`."}, "file": "src/api/routes.py", "line_start": 12, "line_end": 14, "snippet": "async def create_note(body: NoteIn) -> NoteOut:\n    row = await db.insert(body)\n    return NoteOut.from_row(row)"}
      ]
    }
  ],
  "glossary": [{"term": "Note", "definition": "One saved piece of text.", "kind": "domain", "module_ids": ["src-api"]}],
  "paths": [{"id": "new-dev", "audience": "New developer", "title": "Day 1", "steps": [
    {"ref_type": "doc", "ref_id": "README.md", "note": "Start with the overview."},
    {"ref_type": "module", "ref_id": "src-api", "note": "Then the API."},
    {"ref_type": "flow", "ref_id": "save-note", "note": "Follow one request."},
    {"ref_type": "glossary", "ref_id": "Note", "note": "Learn the one domain term."}
  ]}],
  "agent_notes": {"rules": ["Never edit applied migrations."], "traps": ["Tests need a running Postgres."], "do_not_touch": [{"path": "db/migrations", "reason": "Applied in production"}], "commands": [{"label": "Test", "command": "pytest"}]}
}
```

- [ ] **Step 2: Write the failing test**

`tests/test_schema.py`:

```python
import copy
import json
from pathlib import Path

import pytest

from document_repo.schema import MAX_SNIPPET_LINES, SCHEMA_VERSION, SPEC, validate

FIXTURE = Path(__file__).parent / "fixtures" / "sample_model.json"


@pytest.fixture
def model() -> dict:
    return json.loads(FIXTURE.read_text())


def test_fixture_is_valid(model) -> None:
    assert validate(model) == []


@pytest.mark.parametrize("key", sorted(SPEC))
def test_every_top_level_key_is_required(model, key: str) -> None:
    del model[key]
    assert f"{key}: missing" in validate(model)


def test_nested_missing_and_types(model) -> None:
    del model["project"]["name"]
    model["modules"][0]["status"] = "done"
    model["modules"][1]["interface"][0]["line"] = True
    model["meta"]["repo_url"] = 5
    errors = validate(model)
    assert "project.name: missing" in errors
    assert "modules[0].status: expected one of ['analyzed', 'not_analyzed']" in errors
    assert "modules[1].interface[0].line: expected int" in errors
    assert "meta.repo_url: expected str or null" in errors


def test_repo_url_may_be_null(model) -> None:
    model["meta"]["repo_url"] = None
    assert validate(model) == []


def test_snippet_optional_but_capped(model) -> None:
    step = model["flows"][0]["steps"][0]
    del step["snippet"]
    assert validate(model) == []
    step["snippet"] = "\n".join(["x"] * (MAX_SNIPPET_LINES + 1))
    assert any("snippet" in e and "30" in e for e in validate(model))


def test_schema_version(model) -> None:
    model["meta"]["schema_version"] = SCHEMA_VERSION + 1
    assert any("schema_version" in e for e in validate(model))


@pytest.mark.parametrize(
    "mutate,needle",
    [
        (lambda m: m["architecture"]["components"][0]["module_ids"].append("nope"), "unknown module 'nope'"),
        (lambda m: m["architecture"]["connections"].append({"from": "api", "to": "ghost", "label": "x"}), "unknown component 'ghost'"),
        (lambda m: m["modules"][1]["dependencies"]["internal"].append("ghost"), "unknown module 'ghost'"),
        (lambda m: m["glossary"][0]["module_ids"].append("ghost"), "unknown module 'ghost'"),
        (lambda m: m["paths"][0]["steps"].append({"ref_type": "flow", "ref_id": "ghost", "note": ""}), "unknown flow 'ghost'"),
        (lambda m: m["paths"][0]["steps"].append({"ref_type": "glossary", "ref_id": "Ghost", "note": ""}), "unknown glossary term 'Ghost'"),
        (lambda m: m["modules"].append(copy.deepcopy(m["modules"][0])), "duplicate module id 'db'"),
        (lambda m: m["flows"][0]["steps"][0].update(line_end=1), "line_end before line_start"),
    ],
)
def test_cross_references(model, mutate, needle: str) -> None:
    mutate(model)
    errors = validate(model)
    assert any(needle in e for e in errors), errors


def test_not_an_object() -> None:
    assert validate([]) == ["(root): expected object"]  # type: ignore[arg-type]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_schema.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.schema'`.

- [ ] **Step 4: Write `schema.py`**

```python
"""The project model contract, and a validator for it.

The model (explorer/data/model.json) is the single source of truth for a run:
comments, READMEs, AGENTS.md and the explorer are all written from it. This
file defines its exact shape. ``references/model-schema.md`` explains what
each field should contain; this file decides what is valid.

Spec notation: a dict is an object (a key ending in "?" is optional), a
one-item list is "array of", a type is "instance of", ``OneOf`` is an enum,
and ``NULLABLE_STR`` allows a string or null.
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = 1
MAX_SNIPPET_LINES = 30


class OneOf:
    def __init__(self, *values: str) -> None:
        self.values = list(values)


NULLABLE_STR = (str, type(None))
LENS = {"functional": str, "technical": str}
LABELLED_COMMAND = {"label": str, "command": str}

SPEC: dict[str, Any] = {
    "meta": {"schema_version": int, "generated_at": str, "source_commit": str, "repo_name": str, "repo_url": NULLABLE_STR},
    "project": {
        "name": str, "tagline": str, "purpose": LENS, "users": [str],
        "capabilities": [{"title": str, "functional": str, "technical": str}],
        "tech_stack": [{"name": str, "role": str}],
        "run": {"setup": [str], "commands": [LABELLED_COMMAND]},
    },
    "architecture": {
        "summary": LENS,
        "components": [{"id": str, "name": str, "kind": str, "module_ids": [str], "description": LENS}],
        "connections": [{"from": str, "to": str, "label": str}],
        "diagrams": [{"id": str, "title": str, "mermaid": str}],
    },
    "modules": [{
        "id": str, "name": str, "path": str, "status": OneOf("analyzed", "not_analyzed"), "purpose": LENS,
        "interface": [{"name": str, "kind": str, "signature": str, "description": str, "file": str, "line": int}],
        "invariants": [str],
        "dependencies": {"internal": [str], "external": [str]},
        "key_files": [{"path": str, "role": str}],
    }],
    "flows": [{
        "id": str, "title": str, "summary": LENS,
        "steps": [{"title": str, "text": LENS, "file": str, "line_start": int, "line_end": int, "snippet?": str}],
    }],
    "glossary": [{"term": str, "definition": str, "kind": OneOf("domain", "tech"), "module_ids": [str]}],
    "paths": [{
        "id": str, "audience": str, "title": str,
        "steps": [{"ref_type": OneOf("module", "flow", "glossary", "doc"), "ref_id": str, "note": str}],
    }],
    "agent_notes": {"rules": [str], "traps": [str], "do_not_touch": [{"path": str, "reason": str}], "commands": [LABELLED_COMMAND]},
}


def _type_name(spec: Any) -> str:
    if spec is NULLABLE_STR:
        return "str or null"
    return spec.__name__ if isinstance(spec, type) else str(spec)


def _check(value: Any, spec: Any, path: str, errors: list[str]) -> None:
    if isinstance(spec, dict):
        if not isinstance(value, dict):
            errors.append(f"{path or '(root)'}: expected object")
            return
        for raw_key, sub in spec.items():
            key = raw_key.rstrip("?")
            child = f"{path}.{key}" if path else key
            if key not in value:
                if not raw_key.endswith("?"):
                    errors.append(f"{child}: missing")
                continue
            _check(value[key], sub, child, errors)
    elif isinstance(spec, list):
        if not isinstance(value, list):
            errors.append(f"{path}: expected array")
            return
        for i, item in enumerate(value):
            _check(item, spec[0], f"{path}[{i}]", errors)
    elif isinstance(spec, OneOf):
        if value not in spec.values:
            errors.append(f"{path}: expected one of {spec.values}")
    elif (spec is int and isinstance(value, bool)) or not isinstance(value, spec):
        errors.append(f"{path}: expected {_type_name(spec)}")


def _unique(items: list[dict[str, Any]], key: str, label: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for item in items:
        if item[key] in seen:
            errors.append(f"duplicate {label} '{item[key]}'")
        seen.add(item[key])
    return seen


def _cross_check(model: dict[str, Any], errors: list[str]) -> None:
    if model["meta"]["schema_version"] != SCHEMA_VERSION:
        errors.append(f"meta.schema_version: expected {SCHEMA_VERSION}")
    module_ids = _unique(model["modules"], "id", "module id", errors)
    component_ids = _unique(model["architecture"]["components"], "id", "component id", errors)
    flow_ids = _unique(model["flows"], "id", "flow id", errors)
    terms = _unique(model["glossary"], "term", "glossary term", errors)
    _unique(model["paths"], "id", "path id", errors)

    def need(kind: str, ident: str, known: set[str], where: str) -> None:
        if ident not in known:
            errors.append(f"{where}: unknown {kind} '{ident}'")

    for i, comp in enumerate(model["architecture"]["components"]):
        for mid in comp["module_ids"]:
            need("module", mid, module_ids, f"architecture.components[{i}].module_ids")
    for i, conn in enumerate(model["architecture"]["connections"]):
        need("component", conn["from"], component_ids, f"architecture.connections[{i}].from")
        need("component", conn["to"], component_ids, f"architecture.connections[{i}].to")
    for i, mod in enumerate(model["modules"]):
        for mid in mod["dependencies"]["internal"]:
            need("module", mid, module_ids, f"modules[{i}].dependencies.internal")
    for i, term in enumerate(model["glossary"]):
        for mid in term["module_ids"]:
            need("module", mid, module_ids, f"glossary[{i}].module_ids")
    for i, flow in enumerate(model["flows"]):
        for j, step in enumerate(flow["steps"]):
            where = f"flows[{i}].steps[{j}]"
            if step["line_end"] < step["line_start"]:
                errors.append(f"{where}: line_end before line_start")
            if "snippet" in step and len(step["snippet"].splitlines()) > MAX_SNIPPET_LINES:
                errors.append(f"{where}.snippet: more than {MAX_SNIPPET_LINES} lines")
    known = {"module": module_ids, "flow": flow_ids, "glossary": terms}
    labels = {"module": "module", "flow": "flow", "glossary": "glossary term"}
    for i, path in enumerate(model["paths"]):
        for j, step in enumerate(path["steps"]):
            if step["ref_type"] in known:
                need(labels[step["ref_type"]], step["ref_id"], known[step["ref_type"]], f"paths[{i}].steps[{j}]")


def validate(model: dict[str, Any]) -> list[str]:
    """Return every problem found; an empty list means the model is valid."""
    errors: list[str] = []
    _check(model, SPEC, "", errors)
    if not errors:
        _cross_check(model, errors)
    return errors
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_schema.py -q --no-cov`
Expected: PASS. Cross-reference checks run only when the shape is valid. This is why each mutation in `test_cross_references` keeps the shape valid.

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/schema.py tests/test_schema.py tests/fixtures/sample_model.json
git commit -m "feat(document-repo): project model schema and validator

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 7: Assemble the model, write explorer data, install the template

**Files:**
- Create: `src/document_repo/build.py`
- Modify: `src/document_repo/cli.py` (register `assemble`, `build`)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `schema.validate`, `SCHEMA_VERSION`.
- Produces:
  - Run-dir contract: `modules.final.json` = `{"modules": [{"id","path","files","lines"}]}`; `modules/<id>.json` = `{"module": <module entry>, "files": [{"path","summary","callers","side_effects"}]}`; `system.json` = `{project, architecture, flows, glossary, paths, agent_notes}`.
  - `normalize_remote(url) -> str | None` (strips credentials, converts SSH to https, drops `.git`).
  - `assemble_model(run_dir, repo, base_model=None, now=None) -> (model, file_notes)`; meta `source_commit` = `git rev-parse HEAD` of `repo`.
  - `write_explorer_data(model, out_dir) -> state` writes `model.json`, `model.js`, `state.json`; raises `ValueError` listing errors and writes nothing if invalid. `state = {"source_commit", "schema_version", "model_hash", "generated_at"}`; `model_hash` = sha256 hex of `model.json` bytes.
  - `install_template(template_dir, explorer_dir)` copies everything except `data/`.
  - CLI `assemble --run-dir D --repo R [--base-model M]` → writes `D/model.json` and `D/file-notes.json`; prints validation errors and exits 1 if invalid (files are still written so the skill can fix them). CLI `build --model M --explorer-dir E [--template T] [--validate-only]`.

- [ ] **Step 1: Write the failing test**

`tests/test_build.py`:

```python
import hashlib
import json
from pathlib import Path

import pytest

from document_repo.build import assemble_model, install_template, normalize_remote, write_explorer_data
from document_repo.cli import main
from document_repo.schema import validate

FIXTURE = Path(__file__).parent / "fixtures" / "sample_model.json"
SYSTEM_KEYS = ("project", "architecture", "flows", "glossary", "paths", "agent_notes")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("git@github.com:owner/repo.git", "https://github.com/owner/repo"),
        ("ssh://git@github.com/owner/repo.git", "https://github.com/owner/repo"),
        ("https://github.com/owner/repo.git", "https://github.com/owner/repo"),
        ("https://x-token:secret@github.com/owner/repo", "https://github.com/owner/repo"),
        ("https://gitea.example.com/a/b/", "https://gitea.example.com/a/b"),
        ("/local/path/repo", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_remote(url, expected) -> None:
    assert normalize_remote(url) == expected


def _run_dir(tmp_path: Path, with_db_record: bool = True) -> Path:
    fixture = json.loads(FIXTURE.read_text())
    run = tmp_path / "run"
    (run / "modules").mkdir(parents=True)
    (run / "modules.final.json").write_text(json.dumps({"modules": [
        {"id": "db", "path": "db", "files": ["db/migrations/001_init.sql"], "lines": 1},
        {"id": "src-api", "path": "src/api", "files": ["src/api/routes.py"], "lines": 20},
    ]}))
    (run / "system.json").write_text(json.dumps({k: fixture[k] for k in SYSTEM_KEYS}))
    mods = {m["id"]: m for m in fixture["modules"]}
    (run / "modules" / "src-api.json").write_text(json.dumps({"module": mods["src-api"], "files": [
        {"path": "src/api/routes.py", "summary": "Routes.", "callers": ["uvicorn"], "side_effects": ["DB insert"]}]}))
    if with_db_record:
        (run / "modules" / "db.json").write_text(json.dumps({"module": mods["db"], "files": []}))
    return run


def test_assemble_full(make_repo, tmp_path: Path, git) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    git(repo, "remote", "add", "origin", "git@github.com:example/demo.git")
    model, notes = assemble_model(_run_dir(tmp_path), repo, now="2026-11-22T00:00:00+00:00")
    assert validate(model) == []
    assert list(model) == ["meta", "project", "architecture", "modules", "flows", "glossary", "paths", "agent_notes"]
    assert model["meta"]["repo_url"] == "https://github.com/example/demo"
    assert model["meta"]["repo_name"] == "repo"
    assert model["meta"]["source_commit"] == git(repo, "rev-parse", "HEAD").strip()
    assert [n["path"] for n in notes] == ["src/api/routes.py"]


def test_assemble_stub_for_missing_record(make_repo, tmp_path: Path) -> None:
    model, _ = assemble_model(_run_dir(tmp_path, with_db_record=False), make_repo({"a.py": "x\n"}))
    db = next(m for m in model["modules"] if m["id"] == "db")
    assert db["status"] == "not_analyzed" and db["path"] == "db"
    assert validate(model) == []


def test_assemble_uses_base_model_for_untouched_modules(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path, with_db_record=False)
    (run / "system.json").unlink()
    base = json.loads(FIXTURE.read_text())
    base["modules"][0]["name"] = "From base"
    model, _ = assemble_model(run, make_repo({"a.py": "x\n"}), base_model=base)
    assert next(m for m in model["modules"] if m["id"] == "db")["name"] == "From base"
    assert model["project"] == base["project"]


def test_assemble_without_system_or_base_fails(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path)
    (run / "system.json").unlink()
    with pytest.raises(ValueError, match="system.json"):
        assemble_model(run, make_repo({"a.py": "x\n"}))


def test_write_explorer_data(tmp_path: Path) -> None:
    model = json.loads(FIXTURE.read_text())
    state = write_explorer_data(model, tmp_path / "data")
    js = (tmp_path / "data" / "model.js").read_text()
    assert js.startswith("window.PROJECT_MODEL = ") and js.endswith(";\n")
    assert json.loads(js[len("window.PROJECT_MODEL = "):-2]) == model
    raw = (tmp_path / "data" / "model.json").read_bytes()
    assert state["model_hash"] == hashlib.sha256(raw).hexdigest()
    assert json.loads((tmp_path / "data" / "state.json").read_text()) == state
    assert state["source_commit"] == model["meta"]["source_commit"]


def test_write_explorer_data_rejects_invalid(tmp_path: Path) -> None:
    model = json.loads(FIXTURE.read_text())
    del model["project"]
    with pytest.raises(ValueError, match="project: missing"):
        write_explorer_data(model, tmp_path / "data")
    assert not (tmp_path / "data").exists()


def test_install_template_keeps_existing_data(tmp_path: Path) -> None:
    template = tmp_path / "tpl"
    (template / "vendor").mkdir(parents=True)
    (template / "index.html").write_text("<html></html>")
    (template / "vendor" / "m.js").write_text("//m")
    (template / "data").mkdir()
    (template / "data" / "model.js").write_text("TEMPLATE")
    explorer = tmp_path / "repo" / "explorer"
    (explorer / "data").mkdir(parents=True)
    (explorer / "data" / "model.js").write_text("REAL")
    install_template(template, explorer)
    assert (explorer / "index.html").exists() and (explorer / "vendor" / "m.js").exists()
    assert (explorer / "data" / "model.js").read_text() == "REAL"


def test_cli_assemble_and_build(make_repo, tmp_path: Path) -> None:
    run = _run_dir(tmp_path)
    repo = make_repo({"a.py": "x\n"})
    assert main(["assemble", "--run-dir", str(run), "--repo", str(repo)]) == 0
    assert (run / "model.json").exists() and (run / "file-notes.json").exists()
    assert main(["build", "--model", str(run / "model.json"), "--explorer-dir", str(tmp_path / "ex"), "--validate-only"]) == 0
    assert not (tmp_path / "ex").exists()
    tpl = tmp_path / "tpl"
    tpl.mkdir()
    (tpl / "index.html").write_text("x")
    assert main(["build", "--model", str(run / "model.json"), "--explorer-dir", str(tmp_path / "ex"), "--template", str(tpl)]) == 0
    assert (tmp_path / "ex" / "index.html").exists() and (tmp_path / "ex" / "data" / "state.json").exists()


def test_cli_build_invalid_exits_1(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "m.json"
    bad.write_text("{}")
    assert main(["build", "--model", str(bad), "--explorer-dir", str(tmp_path / "ex"), "--validate-only"]) == 1
    assert "meta: missing" in capsys.readouterr().err
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_build.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.build'`.

- [ ] **Step 3: Write `build.py`**

```python
"""Turn analysis output into the project model, and the model into explorer data.

Flow inside a run directory (<target>/.document-repo/, self-ignored, never committed):

    modules.final.json + modules/<id>.json + system.json
        --assemble_model-->  model.json (+ file-notes.json for commenters)
        --write_explorer_data-->  explorer/data/{model.json, model.js, state.json}

model.js exists because browsers refuse to fetch() a JSON file from a page
opened with file://, but they do load a <script src>.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema import SCHEMA_VERSION, validate

SYSTEM_KEYS = ("project", "architecture", "flows", "glossary", "paths", "agent_notes")
MODEL_KEY_ORDER = ("meta", "project", "architecture", "modules", "flows", "glossary", "paths", "agent_notes")
JS_PREFIX = "window.PROJECT_MODEL = "


def normalize_remote(url: str | None) -> str | None:
    """Browsable https URL for a git remote, with any credentials removed."""
    if not url:
        return None
    url = url.strip()
    match = re.match(r"^(?:ssh://)?git@([^:/]+)[:/](.+?)(?:\.git)?/?$", url)
    if match is None:
        match = re.match(r"^https?://(?:[^@/]+@)?([^/]+)/(.+?)(?:\.git)?/?$", url)
    return f"https://{match.group(1)}/{match.group(2)}" if match else None


def _git(repo: Path, *args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _stub(spec: dict[str, Any]) -> dict[str, Any]:
    note = "Not analyzed. The analysis agent failed twice for this module."
    return {
        "id": spec["id"], "name": spec["path"], "path": spec["path"], "status": "not_analyzed",
        "purpose": {"functional": note, "technical": note},
        "interface": [], "invariants": [], "dependencies": {"internal": [], "external": []}, "key_files": [],
    }


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def assemble_model(
    run_dir: Path, repo: Path, base_model: dict[str, Any] | None = None, now: str | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Join module records and system sections into one model.

    Module precedence: a fresh record in run_dir/modules, then the module from
    ``base_model`` (update mode), then a ``not_analyzed`` stub.
    """
    final = _read(run_dir / "modules.final.json")["modules"]
    system_path = run_dir / "system.json"
    if system_path.exists():
        system = _read(system_path)
    elif base_model is not None:
        system = {k: base_model[k] for k in SYSTEM_KEYS}
    else:
        raise ValueError(f"{system_path} is missing and no base model was given")
    base_modules = {m["id"]: m for m in (base_model or {}).get("modules", [])}
    modules: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    for spec in final:
        record_path = run_dir / "modules" / f"{spec['id']}.json"
        if record_path.exists():
            record = _read(record_path)
            modules.append(record["module"])
            notes.extend(record.get("files", []))
        elif spec["id"] in base_modules:
            modules.append(base_modules[spec["id"]])
        else:
            modules.append(_stub(spec))
    top = _git(repo, "rev-parse", "--show-toplevel")
    meta = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_commit": _git(repo, "rev-parse", "HEAD") or "",
        "repo_name": Path(top).name if top else repo.resolve().name,
        "repo_url": normalize_remote(_git(repo, "remote", "get-url", "origin")),
    }
    parts: dict[str, Any] = {"meta": meta, "modules": sorted(modules, key=lambda m: m["id"]), **{k: system[k] for k in SYSTEM_KEYS}}
    return {k: parts[k] for k in MODEL_KEY_ORDER}, notes


def write_explorer_data(model: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Validate, then write model.json, model.js and state.json into ``out_dir``."""
    errors = validate(model)
    if errors:
        raise ValueError("model is invalid:\n" + "\n".join(errors))
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(model, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "model.json").write_text(canonical, encoding="utf-8")
    (out_dir / "model.js").write_text(JS_PREFIX + json.dumps(model, ensure_ascii=False) + ";\n", encoding="utf-8")
    state = {
        "source_commit": model["meta"]["source_commit"],
        "schema_version": SCHEMA_VERSION,
        "model_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "generated_at": model["meta"]["generated_at"],
    }
    (out_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state


def install_template(template_dir: Path, explorer_dir: Path) -> None:
    """Copy the fixed explorer app into the target, never touching data/."""
    shutil.copytree(template_dir, explorer_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns("data"))
```

- [ ] **Step 4: Register in `cli.py`**

Add above `build_parser`:

```python
def _cmd_assemble(args: argparse.Namespace) -> int:
    from .build import assemble_model
    from .schema import validate

    base = load_json(args.base_model) if args.base_model else None
    model, notes = assemble_model(args.run_dir, args.repo, base_model=base)
    emit(model, args.run_dir / "model.json")
    emit(notes, args.run_dir / "file-notes.json")
    errors = validate(model)
    for err in errors:
        sys.stderr.write(err + "\n")
    return 1 if errors else 0


def _register_assemble(sub: Any) -> None:
    p = sub.add_parser("assemble", help="join module records + system sections into model.json")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--base-model", type=Path)
    p.set_defaults(func=_cmd_assemble)


def _cmd_build(args: argparse.Namespace) -> int:
    from .build import install_template, write_explorer_data
    from .schema import validate

    model = load_json(args.model)
    errors = validate(model)
    if errors:
        for err in errors:
            sys.stderr.write(err + "\n")
        return 1
    if args.validate_only:
        return 0
    if args.template:
        install_template(args.template, args.explorer_dir)
    emit(write_explorer_data(model, args.explorer_dir / "data"))
    return 0


def _register_build(sub: Any) -> None:
    p = sub.add_parser("build", help="validate a model and write explorer data")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--explorer-dir", type=Path, required=True)
    p.add_argument("--template", type=Path)
    p.add_argument("--validate-only", action="store_true")
    p.set_defaults(func=_cmd_build)
```

In `build_parser`, add `_register_assemble(sub)` and `_register_build(sub)` after `_register_verify(sub)`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_build.py -q --no-cov`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/build.py src/document_repo/cli.py tests/test_build.py
git commit -m "feat(document-repo): assemble model, write explorer data, install template

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 8: Remap model line numbers after commenting

**Files:**
- Create: `src/document_repo/remap.py`
- Modify: `src/document_repo/cli.py` (register `remap`)
- Test: `tests/test_remap.py`

**Why:** Analysis records line numbers at the base commit. Phase 2 inserts comments, so every later line moves down. Before the explorer is built, the skill remaps `modules[].interface[].line` and `flows[].steps[].line_start/line_end` to the new commit and refreshes snippets, which then show the new comments too.

**Interfaces:**
- Consumes: `verify.git_show`, `schema.MAX_SNIPPET_LINES`.
- Produces: `line_map(before: list[str], after: list[str]) -> list[int]` (index i = 1-based new line for old line i+1); `remap_model(model, repo, new_ref) -> (model, warnings)`. It reads both versions from git (`meta.source_commit` → `new_ref`), sets `meta.source_commit` to the resolved sha of `new_ref`, and returns a deep copy. CLI `remap --model M --repo R [--to REF]` rewrites `M` in place and prints the warnings as JSON.

- [ ] **Step 1: Write the failing test**

`tests/test_remap.py`:

```python
import json
from pathlib import Path

from document_repo.cli import main
from document_repo.remap import line_map, remap_model

FIXTURE = Path(__file__).parent / "fixtures" / "sample_model.json"
# Line 1 import, lines 2-11 blank, line 12 is the function (matches the fixture's line 12).
ROUTES = "import x\n" + "\n" * 10 + "async def create_note(body):\n    row = await db.insert(body)\n    return row\n"


def test_line_map_pure_insertions() -> None:
    assert line_map(["a", "b", "c"], ["# h", "a", "# why", "b", "c"]) == [2, 4, 5]


def test_line_map_replacement_is_clamped() -> None:
    assert line_map(["a", "b"], ["a", "z"]) == [1, 2]
    assert line_map(["a", "b", "c"], ["a"]) == [1, 1, 1]


def _model(sha: str) -> dict:
    model = json.loads(FIXTURE.read_text())
    model["meta"]["source_commit"] = sha
    return model


def test_remap_model_moves_lines_and_refreshes_snippet(make_repo, commit_files, git) -> None:
    repo = make_repo({"src/api/routes.py": ROUTES})
    base = git(repo, "rev-parse", "HEAD").strip()
    commented = '"""Routes."""\n' + ROUTES.replace("async def", "# Why: one insert per request.\nasync def")
    new = commit_files(repo, {"src/api/routes.py": commented})
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert warnings == []
    assert model["meta"]["source_commit"] == new
    assert model["modules"][1]["interface"][0]["line"] == 14
    step = model["flows"][0]["steps"][0]
    assert (step["line_start"], step["line_end"]) == (14, 16)
    assert step["snippet"].startswith("async def create_note")


def test_remap_warns_on_missing_file(make_repo, git) -> None:
    repo = make_repo({"other.py": "x\n"})
    base = git(repo, "rev-parse", "HEAD").strip()
    model, warnings = remap_model(_model(base), repo, "HEAD")
    assert any("src/api/routes.py" in w for w in warnings)
    assert model["modules"][1]["interface"][0]["line"] == 12


def test_cli_remap(make_repo, commit_files, git, tmp_path: Path) -> None:
    repo = make_repo({"src/api/routes.py": ROUTES})
    path = tmp_path / "model.json"
    path.write_text(json.dumps(_model(git(repo, "rev-parse", "HEAD").strip())))
    commit_files(repo, {"src/api/routes.py": "# h\n" + ROUTES})
    assert main(["remap", "--model", str(path), "--repo", str(repo)]) == 0
    assert json.loads(path.read_text())["modules"][1]["interface"][0]["line"] == 13
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_remap.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.remap'`.

- [ ] **Step 3: Write `remap.py`**

```python
"""Move model line numbers to a newer commit.

Comments inserted in Phase 2 push code down. A line_map built from the diff
between the analysed commit and the commented commit says where each old line
now lives. Comment-only edits are pure insertions, so the mapping is exact;
for anything else it is a best effort, and the caller gets a warning.
"""

from __future__ import annotations

import copy
import difflib
import subprocess
from pathlib import Path
from typing import Any

from .schema import MAX_SNIPPET_LINES
from .verify import git_show


def line_map(before: list[str], after: list[str]) -> list[int]:
    """Index i holds the 1-based line in ``after`` for line i+1 of ``before``."""
    mapping = [1] * len(before)
    last = max(len(after), 1)
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        for k in range(i1, i2):
            if tag == "equal":
                mapping[k] = j1 + (k - i1) + 1
            else:
                mapping[k] = min(j1 + (k - i1), max(j1, j2 - 1)) + 1
            mapping[k] = min(max(mapping[k], 1), last)
    return mapping


def remap_model(model: dict[str, Any], repo: Path, new_ref: str) -> tuple[dict[str, Any], list[str]]:
    """Return a copy of ``model`` whose line numbers refer to ``new_ref``."""
    out = copy.deepcopy(model)
    old_ref = model["meta"]["source_commit"]
    new_sha = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", new_ref], capture_output=True, text=True, check=True
    ).stdout.strip()
    warnings: list[str] = []
    cache: dict[str, tuple[list[int], list[str]] | None] = {}

    def lookup(path: str) -> tuple[list[int], list[str]] | None:
        if path not in cache:
            before, after = git_show(repo, old_ref, path), git_show(repo, new_sha, path)
            if before is None or after is None:
                warnings.append(f"{path}: missing at {old_ref[:12]} or {new_sha[:12]}; line numbers left unchanged")
                cache[path] = None
            else:
                after_lines = after.splitlines()
                cache[path] = (line_map(before.splitlines(), after_lines), after_lines)
        return cache[path]

    def move(path: str, line: int) -> int:
        found = lookup(path)
        if found is None or not found[0]:
            return line
        mapping = found[0]
        return mapping[min(max(line, 1), len(mapping)) - 1]

    for module in out["modules"]:
        for item in module["interface"]:
            item["line"] = move(item["file"], item["line"])
    for flow in out["flows"]:
        for step in flow["steps"]:
            step["line_start"] = move(step["file"], step["line_start"])
            step["line_end"] = max(move(step["file"], step["line_end"]), step["line_start"])
            found = lookup(step["file"])
            if "snippet" in step and found is not None:
                lines = found[1]
                end = min(step["line_end"], step["line_start"] + MAX_SNIPPET_LINES - 1)
                step["snippet"] = "\n".join(lines[step["line_start"] - 1:end])
    out["meta"]["source_commit"] = new_sha
    return out, warnings
```

- [ ] **Step 4: Register in `cli.py`**

```python
def _cmd_remap(args: argparse.Namespace) -> int:
    from .remap import remap_model

    model, warnings = remap_model(load_json(args.model), args.repo, args.to)
    emit(model, args.model)
    emit({"warnings": warnings})
    return 0


def _register_remap(sub: Any) -> None:
    p = sub.add_parser("remap", help="move model line numbers to a newer commit")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--to", default="HEAD")
    p.set_defaults(func=_cmd_remap)
```

In `build_parser`, add `_register_remap(sub)` after `_register_build(sub)`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_remap.py -q --no-cov`
Expected: PASS. Check the numbers: the docstring line plus the "Why" line move `async def` from line 12 to line 14.

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/remap.py src/document_repo/cli.py tests/test_remap.py
git commit -m "feat(document-repo): remap model line numbers after comment insertion

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 9: Marker-section upsert for docs

**Files:**
- Create: `src/document_repo/docs.py`
- Modify: `src/document_repo/cli.py` (register `upsert-section`)
- Test: `tests/test_docs.py`

**Interfaces:**
- Produces: `marker_pair(name) -> tuple[str, str]`; `upsert_section(text, name, body) -> str`; `upsert_file(path, name, body) -> None`. Names match `^[a-z0-9][a-z0-9-]*$`. Raises `ValueError` on a bad name, a duplicate start marker, a start without an end, or an end without a start. CLI `upsert-section --file F --section S --content-file C`.

- [ ] **Step 1: Write the failing test**

`tests/test_docs.py`:

```python
from pathlib import Path

import pytest

from document_repo.cli import main
from document_repo.docs import marker_pair, upsert_file, upsert_section


def test_append_keeps_human_text() -> None:
    start, end = marker_pair("overview")
    out = upsert_section("# Title\n\nHuman words.\n", "overview", "Generated.\n")
    assert out == f"# Title\n\nHuman words.\n\n{start}\nGenerated.\n{end}\n"


def test_replace_only_between_markers() -> None:
    first = upsert_section("Top\n", "a", "one")
    second = upsert_section(first + "Bottom\n", "a", "two")
    assert "one" not in second and "two" in second
    assert second.startswith("Top\n") and second.endswith("Bottom\n")


def test_idempotent() -> None:
    once = upsert_section("x\n", "a", "body")
    assert upsert_section(once, "a", "body") == once


def test_empty_file() -> None:
    start, end = marker_pair("a")
    assert upsert_section("", "a", "b") == f"{start}\nb\n{end}\n"


@pytest.mark.parametrize(
    "text,name,needle",
    [
        ("x", "Bad Name", "section name"),
        ("<!-- document-repo:start:a -->\nno end\n", "a", "no end marker"),
        ("<!-- document-repo:end:a -->\n", "a", "without a start"),
        ("<!-- document-repo:start:a -->\n<!-- document-repo:end:a -->\n<!-- document-repo:start:a -->\n<!-- document-repo:end:a -->\n", "a", "more than once"),
    ],
)
def test_errors(text: str, name: str, needle: str) -> None:
    with pytest.raises(ValueError, match=needle):
        upsert_section(text, name, "b")


def test_upsert_file_creates_parents(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "GLOSSARY.md"
    upsert_file(target, "glossary", "Terms")
    assert "Terms" in target.read_text()


def test_cli(tmp_path: Path) -> None:
    content = tmp_path / "c.md"
    content.write_text("Hello")
    target = tmp_path / "README.md"
    target.write_text("# Mine\n")
    assert main(["upsert-section", "--file", str(target), "--section", "overview", "--content-file", str(content)]) == 0
    assert target.read_text().startswith("# Mine\n") and "Hello" in target.read_text()
    assert main(["upsert-section", "--file", str(target), "--section", "BAD", "--content-file", str(content)]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.docs'`.

- [ ] **Step 3: Write `docs.py`**

```python
"""Write generated text into docs without touching the human-written parts.

Generated text always lives between a start and an end marker, which are
invisible HTML comments in rendered Markdown. A later run replaces only what
is between the markers, so a person's edits elsewhere in the file survive.
"""

from __future__ import annotations

import re
from pathlib import Path

_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def marker_pair(name: str) -> tuple[str, str]:
    if not _NAME.match(name):
        raise ValueError(f"section name {name!r} must match {_NAME.pattern}")
    return f"<!-- document-repo:start:{name} -->", f"<!-- document-repo:end:{name} -->"


def upsert_section(text: str, name: str, body: str) -> str:
    """Replace section ``name`` in ``text``, or append it when absent."""
    start, end = marker_pair(name)
    block = f"{start}\n{body.strip()}\n{end}"
    count = text.count(start)
    if count > 1:
        raise ValueError(f"start marker for {name!r} appears more than once")
    if count == 0:
        if end in text:
            raise ValueError(f"end marker for {name!r} without a start marker")
        return block + "\n" if not text.strip() else text.rstrip("\n") + "\n\n" + block + "\n"
    s = text.index(start)
    e = text.find(end, s)
    if e == -1:
        raise ValueError(f"start marker for {name!r} has no end marker")
    return text[:s] + block + text[e + len(end):]


def upsert_file(path: Path, name: str, body: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(upsert_section(text, name, body), encoding="utf-8")
```

- [ ] **Step 4: Register in `cli.py`**

```python
def _cmd_upsert_section(args: argparse.Namespace) -> int:
    from .docs import upsert_file

    try:
        upsert_file(args.file, args.section, args.content_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        sys.stderr.write(f"upsert-section: {exc}\n")
        return 2
    return 0


def _register_upsert_section(sub: Any) -> None:
    p = sub.add_parser("upsert-section", help="write a generated section between markers")
    p.add_argument("--file", type=Path, required=True)
    p.add_argument("--section", required=True)
    p.add_argument("--content-file", type=Path, required=True)
    p.set_defaults(func=_cmd_upsert_section)
```

In `build_parser`, add `_register_upsert_section(sub)` after `_register_remap(sub)`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_docs.py -q --no-cov`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/docs.py src/document_repo/cli.py tests/test_docs.py
git commit -m "feat(document-repo): marker-section upsert for generated docs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 10: Update-mode change detection

**Files:**
- Create: `src/document_repo/changes.py`
- Modify: `src/document_repo/cli.py` (register `changes`)
- Test: `tests/test_changes.py`

**Interfaces:**
- Consumes: `verify.verify_file`, `languages.detect`.
- Produces: `module_for(path, modules) -> str | None` (longest path prefix wins; the root module `"."` claims only top-level files); `compute_changes(repo, state, model) -> dict` with keys `since`, `head`, `changed_files` (`[{"status","path"}]`), `comment_only_files`, `removed_files`, `affected_modules`, `unmapped_files`. It ignores `explorer/**` and `*.md`. A modified file whose change vs `since` is comment-only does not count. It raises `ValueError` when `since` is not in the history. CLI `changes --repo R [--explorer-dir E]` (default `R/explorer`) reads `data/state.json` and `data/model.json`. Exit 2 on `ValueError`.

- [ ] **Step 1: Write the failing test**

`tests/test_changes.py`:

```python
import json
from pathlib import Path

import pytest

from document_repo.changes import compute_changes, module_for
from document_repo.cli import main

MODULES = [{"id": "root", "path": "."}, {"id": "src", "path": "src"}, {"id": "src-api", "path": "src/api"}, {"id": "web", "path": "web"}]


@pytest.mark.parametrize(
    "path,expected",
    [("setup.py", "root"), ("src/x.py", "src"), ("src/api/a.py", "src-api"), ("web/i.ts", "web"), ("other/z.py", None), ("srcx/a.py", None)],
)
def test_module_for(path: str, expected) -> None:
    assert module_for(path, MODULES) == expected


def _setup(make_repo, git):
    repo = make_repo({"setup.py": "x = 1\n", "src/api/a.py": "def f():\n    return 1\n", "web/i.ts": "export const a = 1;\n", "src/old.py": "y = 1\n"})
    state = {"source_commit": git(repo, "rev-parse", "HEAD").strip()}
    model = {"modules": MODULES}
    return repo, state, model


def test_compute_changes(make_repo, commit_files, git) -> None:
    repo, state, model = _setup(make_repo, git)
    commit_files(repo, {
        "src/api/a.py": "def f():\n    return 2\n",
        "web/i.ts": "// comment only\nexport const a = 1;\n",
        "README.md": "# docs\n",
        "explorer/data/model.js": "x\n",
        "tools/new.py": "z = 1\n",
    })
    git(repo, "rm", "-q", "src/old.py")
    git(repo, "commit", "-q", "-m", "rm")
    result = compute_changes(repo, state, model)
    assert result["affected_modules"] == ["src", "src-api"]
    assert result["comment_only_files"] == ["web/i.ts"]
    assert result["unmapped_files"] == ["tools/new.py"]
    assert result["removed_files"] == ["src/old.py"]
    assert {c["path"] for c in result["changed_files"]} == {"src/api/a.py", "tools/new.py", "src/old.py"}
    assert result["head"] == git(repo, "rev-parse", "HEAD").strip()


def test_rename_marks_both_modules(make_repo, git) -> None:
    repo, state, model = _setup(make_repo, git)
    git(repo, "mv", "src/old.py", "web/old.py")
    git(repo, "commit", "-q", "-m", "mv")
    result = compute_changes(repo, state, model)
    assert result["affected_modules"] == ["src", "web"]


def test_unknown_commit_raises(make_repo, git) -> None:
    repo, _, model = _setup(make_repo, git)
    with pytest.raises(ValueError, match="not in this repository"):
        compute_changes(repo, {"source_commit": "f" * 40}, model)


def test_cli_changes(make_repo, commit_files, git, capsys) -> None:
    repo, state, model = _setup(make_repo, git)
    data = repo / "explorer" / "data"
    data.mkdir(parents=True)
    (data / "state.json").write_text(json.dumps(state))
    (data / "model.json").write_text(json.dumps(model))
    commit_files(repo, {"setup.py": "x = 2\n"})
    assert main(["changes", "--repo", str(repo)]) == 0
    assert json.loads(capsys.readouterr().out)["affected_modules"] == ["root"]
    (data / "state.json").write_text(json.dumps({"source_commit": "0" * 40}))
    assert main(["changes", "--repo", str(repo)]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_changes.py -q --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'document_repo.changes'`.

- [ ] **Step 3: Write `changes.py`**

```python
"""Find what changed since the docs were built, for --update runs.

Input: state.json (the commit the docs describe) and model.json (module
paths). Output: which modules need fresh analysis. A file edited only in its
comments does not count (the verifier proves this), and documentation files
and the explorer itself are ignored.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .inventory import OUTPUT_DIR
from .languages import detect
from .verify import verify_file


def module_for(path: str, modules: list[dict[str, Any]]) -> str | None:
    best: str | None = None
    best_len = -1
    for module in modules:
        prefix = module["path"].strip("/")
        if prefix in ("", "."):
            if "/" not in path and best_len < 0:
                best, best_len = module["id"], 0
        elif (path == prefix or path.startswith(prefix + "/")) and len(prefix) > best_len:
            best, best_len = module["id"], len(prefix)
    return best


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def _ignored(path: str) -> bool:
    return path.startswith(OUTPUT_DIR + "/") or path.lower().endswith(".md")


def compute_changes(repo: Path, state: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    since = state["source_commit"]
    if _git(repo, "cat-file", "-e", f"{since}^{{commit}}").returncode != 0:
        raise ValueError(f"source_commit {since} is not in this repository's history")
    diff = _git(repo, "diff", "--name-status", "-M", since, "HEAD")
    changed: list[dict[str, str]] = []
    comment_only: list[str] = []
    removed: list[str] = []
    unmapped: set[str] = set()
    affected: set[str] = set()
    for line in diff.stdout.splitlines():
        fields = line.split("\t")
        status = fields[0][0]
        old, new = (fields[1], fields[2]) if status in ("R", "C") else (fields[1], fields[1])
        if _ignored(new) and _ignored(old):
            continue
        if status == "M" and detect(new) is not None and verify_file(repo, new, since).ok:
            comment_only.append(new)
            continue
        changed.append({"status": status, "path": new})
        if status == "D":
            removed.append(old)
        for path in {old, new}:
            module_id = module_for(path, model["modules"])
            if module_id is not None:
                affected.add(module_id)
            elif path == new and status != "D":
                unmapped.add(path)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return {
        "since": since, "head": head, "changed_files": changed, "comment_only_files": sorted(comment_only),
        "removed_files": sorted(removed), "affected_modules": sorted(affected), "unmapped_files": sorted(unmapped),
    }
```

- [ ] **Step 4: Register in `cli.py`**

```python
def _cmd_changes(args: argparse.Namespace) -> int:
    from .changes import compute_changes

    explorer = args.explorer_dir or (args.repo / "explorer")
    try:
        result = compute_changes(args.repo, load_json(explorer / "data" / "state.json"), load_json(explorer / "data" / "model.json"))
    except (ValueError, OSError) as exc:
        sys.stderr.write(f"changes: {exc}\n")
        return 2
    emit(result)
    return 0


def _register_changes(sub: Any) -> None:
    p = sub.add_parser("changes", help="modules affected since the docs were built")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--explorer-dir", type=Path)
    p.set_defaults(func=_cmd_changes)
```

In `build_parser`, add `_register_changes(sub)` after `_register_upsert_section(sub)`.

- [ ] **Step 5: Run the full suite with coverage and mypy**

```bash
pytest -q -n auto --cov=document_repo --cov-branch
mypy src/ --ignore-missing-imports
```

Expected: all PASS; coverage ≥90% (the run fails below that); mypy `Success: no issues found`.

- [ ] **Step 6: Commit**

```bash
git add src/document_repo/changes.py src/document_repo/cli.py tests/test_changes.py
git commit -m "feat(document-repo): update-mode change detection

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 11: Explorer template

**Files:**
- Create: `plugins/personal-plugin/skills/document-repo/templates/explorer/index.html`
- Create: `plugins/personal-plugin/skills/document-repo/templates/explorer/styles.css`
- Create: `plugins/personal-plugin/skills/document-repo/templates/explorer/app.js`
- Create: `plugins/personal-plugin/skills/document-repo/templates/explorer/vendor/mermaid.min.js` (downloaded)
- Create: `plugins/personal-plugin/skills/document-repo/templates/explorer/vendor/README.md`
- Test: `plugins/personal-plugin/tools/document-repo/tests/test_explorer_template.py`

**Interfaces:**
- Consumes: `window.PROJECT_MODEL` (shape = `schema.SPEC`). Diagram node ids equal component ids (or module ids) so clicks resolve.
- Produces: hash routes `#/overview`, `#/architecture`, `#/modules[/<id>]`, `#/tours[/<id>]`, `#/glossary[/<term>]`, `#/paths[/<id>]`, `#/search/<query>`. The lens is stored in `localStorage["document-repo-lens"]` (wrapped in try/catch).

- [ ] **Step 1: Write the failing structure test**

`tests/test_explorer_template.py`:

```python
import hashlib
import re
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[3] / "skills" / "document-repo" / "templates" / "explorer"
OWN_FILES = ["index.html", "app.js", "styles.css"]


def test_template_files_exist() -> None:
    for name in [*OWN_FILES, "vendor/mermaid.min.js", "vendor/README.md"]:
        assert (TEMPLATE / name).is_file(), name
    assert not (TEMPLATE / "data").exists(), "the template must not ship data/"


def test_index_loads_only_local_scripts_in_order() -> None:
    html = (TEMPLATE / "index.html").read_text()
    assert re.findall(r'<script src="([^"]+)"', html) == ["data/model.js", "vendor/mermaid.min.js", "app.js"]
    assert re.findall(r'<link rel="stylesheet" href="([^"]+)"', html) == ["styles.css"]


def test_no_network_in_own_files() -> None:
    for name in OWN_FILES:
        text = (TEMPLATE / name).read_text()
        assert "http://" not in text and "https://" not in text, name
        for banned in ("fetch(", "XMLHttpRequest", "import(", "@import", "sendBeacon", "WebSocket"):
            assert banned not in text, f"{name} uses {banned}"


def test_mermaid_checksum_matches_readme() -> None:
    readme = (TEMPLATE / "vendor" / "README.md").read_text()
    match = re.search(r"sha256: ([0-9a-f]{64})", readme)
    assert match, "vendor/README.md must record the sha256"
    digest = hashlib.sha256((TEMPLATE / "vendor" / "mermaid.min.js").read_bytes()).hexdigest()
    assert digest == match.group(1)
    assert "mermaid@11.4.1" in readme
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `plugins/personal-plugin/tools/document-repo`): `pytest tests/test_explorer_template.py -q --no-cov`
Expected: FAIL on `test_template_files_exist` (`index.html`).

- [ ] **Step 3: Vendor Mermaid and record the checksum**

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace/plugins/personal-plugin/skills/document-repo/templates/explorer
mkdir -p vendor
curl -fsSL https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js -o vendor/mermaid.min.js
shasum -a 256 vendor/mermaid.min.js
head -c 300 vendor/mermaid.min.js; echo
```

Expected: a file of about 2–3 MB that starts with minified JS (not an HTML error page). If it is HTML, stop. The URL is wrong.

Write `vendor/README.md`, with `<HEX>` replaced by the hash printed above:

```markdown
# Vendored files

| File | Source | Licence |
|------|--------|---------|
| `mermaid.min.js` | `mermaid@11.4.1`, `dist/mermaid.min.js` from the npm registry via jsDelivr | MIT |

sha256: <HEX>

Vendored so the explorer works offline and sends nothing to the network. To
upgrade: download the new `dist/mermaid.min.js`, update the version and sha256
above, then run `tests/test_explorer_template.py`.
```

- [ ] **Step 4: Write `index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project Explorer</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <!-- Fixed template from the document-repo skill. Regenerated on every run:
       edit the project model (explorer/data/model.json), not this file. -->
  <header class="topbar">
    <a class="brand" id="brand" href="#/overview">Project Explorer</a>
    <nav id="nav" aria-label="Sections"></nav>
    <div class="controls">
      <div class="lens" role="group" aria-label="Explanation style">
        <button type="button" data-lens="functional" aria-pressed="true">What it does</button>
        <button type="button" data-lens="technical" aria-pressed="false">How it works</button>
      </div>
      <input id="search" type="search" placeholder="Search" aria-label="Search the project">
    </div>
  </header>
  <main id="view" tabindex="-1"></main>
  <script src="data/model.js"></script>
  <script src="vendor/mermaid.min.js"></script>
  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 5: Write `styles.css`**

```css
/* Project Explorer styles. Colour tokens first; dark mode redefines them. */
:root {
  --bg: #f7f7f5; --surface: #ffffff; --text: #1d1d1f; --muted: #5f6368;
  --line: #e3e3e0; --accent: #2f5fd0; --accent-soft: #e8eefc; --warn: #a15c00; --warn-soft: #fff3df;
  --code-bg: #f1f1ee; --radius: 10px; --gap: 16px;
  --font: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #131416; --surface: #1c1d20; --text: #ececec; --muted: #a0a4ab;
    --line: #2e3035; --accent: #8fb0ff; --accent-soft: #1f2a44; --warn: #ffbf66; --warn-soft: #3a2a12;
    --code-bg: #24262a; color-scheme: dark;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 16px/1.6 var(--font); }
a { color: var(--accent); }
code, pre { font-family: var(--mono); font-size: 0.9em; }
code { background: var(--code-bg); padding: 0.1em 0.35em; border-radius: 4px; }
pre { background: var(--code-bg); padding: 12px; border-radius: var(--radius); overflow-x: auto; }
pre code { background: none; padding: 0; }

.topbar {
  position: sticky; top: 0; z-index: 10; display: flex; flex-wrap: wrap; align-items: center; gap: 8px 20px;
  padding: 10px 16px; background: var(--surface); border-bottom: 1px solid var(--line);
}
.brand { font-weight: 700; text-decoration: none; color: var(--text); }
#nav { display: flex; flex-wrap: wrap; gap: 4px; }
#nav a { padding: 4px 10px; border-radius: 999px; text-decoration: none; color: var(--muted); }
#nav a.active, #nav a:hover { background: var(--accent-soft); color: var(--accent); }
.controls { display: flex; flex-wrap: wrap; gap: 8px; margin-left: auto; }
.lens { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; overflow: hidden; }
.lens button { border: 0; background: none; color: var(--muted); padding: 4px 12px; font: inherit; cursor: pointer; }
.lens button[aria-pressed="true"] { background: var(--accent); color: var(--surface); }
#search { min-width: 0; width: 180px; padding: 4px 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--bg); color: var(--text); font: inherit; }

main { max-width: 1040px; margin: 0 auto; padding: 24px 16px 64px; outline: none; }
h1 { font-size: 1.9rem; line-height: 1.2; margin: 0.2em 0 0.4em; }
h2 { font-size: 1.25rem; margin: 2em 0 0.6em; }
h3 { font-size: 1.05rem; margin: 0 0 0.4em; }
.lead { font-size: 1.1rem; color: var(--text); max-width: 70ch; }
.muted, .crumbs, .path { color: var(--muted); }
.eyebrow { text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.8rem; color: var(--muted); margin: 0; }
.tagline { font-size: 1.2rem; margin: 0 0 0.6em; }
.hero { padding: 8px 0 8px; }

.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--gap); }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px; }
.link-card { text-decoration: none; color: inherit; transition: border-color 0.15s; }
.link-card:hover, .link-card:focus { border-color: var(--accent); }
.chips { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; }
.chips li { background: var(--accent-soft); color: var(--accent); padding: 2px 10px; border-radius: 999px; }
.tag { display: inline-block; font-size: 0.75rem; padding: 0 8px; border-radius: 999px; background: var(--code-bg); color: var(--muted); vertical-align: middle; }
.tag.warn, .warn { background: var(--warn-soft); color: var(--warn); }
p.warn { padding: 8px 12px; border-radius: var(--radius); }

table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: var(--radius); overflow: hidden; display: block; overflow-x: auto; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-weight: 600; color: var(--muted); }

.diagram { margin: 16px 0; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px; overflow-x: auto; }
.diagram figcaption { font-weight: 600; margin-bottom: 8px; }
.mermaid-out svg { max-width: 100%; height: auto; }
.mermaid-out g.clickable { cursor: pointer; }
.mermaid-out g.clickable:hover rect, .mermaid-out g.clickable:focus rect { stroke: var(--accent) !important; stroke-width: 2px !important; }

.steps { list-style: none; padding: 0; counter-reset: none; }
.step { display: flex; gap: 16px; padding: 16px 0; border-bottom: 1px solid var(--line); }
.step-num { flex: none; width: 32px; height: 32px; border-radius: 50%; background: var(--accent); color: var(--surface); display: grid; place-items: center; font-weight: 700; }
.step-body { min-width: 0; flex: 1; }
details summary { cursor: pointer; color: var(--accent); }

dl.glossary dt { font-weight: 700; margin-top: 12px; }
dl.glossary dt.hit { background: var(--accent-soft); border-radius: 4px; padding: 0 6px; }
dl.glossary dd { margin: 0 0 0 0; color: var(--text); }
.snippet { color: var(--muted); font-size: 0.9rem; }
.empty { padding: 48px 16px; text-align: center; color: var(--muted); }

@media (max-width: 640px) {
  .controls { margin-left: 0; width: 100%; }
  #search { flex: 1; width: auto; }
  h1 { font-size: 1.5rem; }
}
```

- [ ] **Step 6: Write `app.js`**

```javascript
/* Project Explorer. Renders window.PROJECT_MODEL (explorer/data/model.js).
 * Fixed template shipped by the document-repo skill; only data/ is generated.
 * No network access: every asset is local and nothing is fetched. */
(() => {
  'use strict';

  const M = window.PROJECT_MODEL;
  const view = document.getElementById('view');
  if (!M) {
    view.innerHTML = '<p class="empty">No project model found. Run the document-repo skill to generate <code>explorer/data/model.js</code>.</p>';
    return;
  }

  // ---- small helpers -------------------------------------------------------
  const store = {
    get(key) { try { return window.localStorage.getItem(key); } catch (e) { return null; } },
    set(key, value) { try { window.localStorage.setItem(key, value); } catch (e) { /* storage blocked */ } },
  };
  const LENS_KEY = 'document-repo-lens';
  let lens = store.get(LENS_KEY) === 'technical' ? 'technical' : 'functional';

  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ESC[c]);
  const rich = (s) => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>');
  const lensText = (o) => (o && typeof o === 'object' ? o[lens] || o.functional || '' : o || '');
  const byId = (items, id) => items.find((x) => x.id === id);
  const href = (...parts) => '#/' + parts.map((p) => encodeURIComponent(p)).join('/');
  const list = (items, fn) => (items.length ? '<ul>' + items.map((x) => '<li>' + fn(x) + '</li>').join('') + '</ul>' : '<p class="muted">None.</p>');
  const termAnchor = (term) => 'term-' + String(term).toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const tags = (items) => (items.length ? '<ul class="chips">' + items.map((x) => '<li>' + esc(x) + '</li>').join('') + '</ul>' : '');

  function fileLink(path, line) {
    const label = esc(path) + (line ? ':' + line : '');
    if (!M.meta.repo_url) return '<code class="file">' + label + '</code>';
    const url = M.meta.repo_url + '/blob/' + encodeURIComponent(M.meta.source_commit) + '/' +
      path.split('/').map((p) => encodeURIComponent(p)).join('/') + (line ? '#L' + line : '');
    return '<a class="file" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + label + '</a>';
  }
  const moduleLink = (id) => {
    const m = byId(M.modules, id);
    return '<a href="' + href('modules', id) + '">' + esc(m ? m.name : id) + '</a>';
  };
  const componentName = (id) => { const c = byId(M.architecture.components, id); return c ? c.name : id; };
  const notFound = (kind, id) => '<h1>Not found</h1><p>No ' + kind + ' called <code>' + esc(id) + '</code>. <a href="#/overview">Back to the overview</a>.</p>';
  const inModule = (m, file) => (m.path === '.' ? !file.includes('/') : file === m.path || file.startsWith(m.path + '/'));
  const codeBlock = (code) => {
    const pre = '<pre><code>' + esc(code) + '</code></pre>';
    return lens === 'technical' ? pre : '<details><summary>Show the code</summary>' + pre + '</details>';
  };

  // ---- views ---------------------------------------------------------------
  function overview() {
    const p = M.project;
    return `
      <section class="hero">
        <p class="eyebrow">${esc(M.meta.repo_name)}</p>
        <h1>${esc(p.name)}</h1>
        <p class="tagline">${rich(p.tagline)}</p>
        <p class="lead">${rich(lensText(p.purpose))}</p>
      </section>
      <h2>Who it is for</h2>${tags(p.users)}
      <h2>What it can do</h2>
      <div class="cards">${p.capabilities.map((c) => `<article class="card"><h3>${esc(c.title)}</h3><p>${rich(c[lens])}</p></article>`).join('')}</div>
      <h2>Built with</h2>
      <table><thead><tr><th>Technology</th><th>Role</th></tr></thead>
      <tbody>${p.tech_stack.map((t) => `<tr><td>${esc(t.name)}</td><td>${rich(t.role)}</td></tr>`).join('')}</tbody></table>
      <h2>Run it</h2>
      ${p.run.setup.length ? '<h3>Setup</h3><ol>' + p.run.setup.map((s) => `<li>${rich(s)}</li>`).join('') + '</ol>' : ''}
      ${p.run.commands.map((c) => `<p class="muted">${esc(c.label)}</p><pre><code>${esc(c.command)}</code></pre>`).join('')}
      <h2>Where to go next</h2>
      <div class="cards">${M.paths.map((pa) => `<a class="card link-card" href="${href('paths', pa.id)}"><h3>${esc(pa.title)}</h3><p>${esc(pa.audience)}</p></a>`).join('')}</div>`;
  }

  function architecture() {
    const a = M.architecture;
    return `<h1>Architecture</h1><p class="lead">${rich(lensText(a.summary))}</p>
      ${a.diagrams.map((d) => `<figure class="diagram"><figcaption>${esc(d.title)}</figcaption><pre class="mermaid-src">${esc(d.mermaid)}</pre></figure>`).join('')}
      ${a.diagrams.length ? '<p class="muted">Click a box in a diagram to open its module.</p>' : ''}
      <h2>Components</h2>
      <div class="cards">${a.components.map((c) => `<article class="card" id="comp-${esc(c.id)}">
        <h3>${esc(c.name)} <span class="tag">${esc(c.kind)}</span></h3>
        <p>${rich(lensText(c.description))}</p><p>${c.module_ids.map(moduleLink).join(' · ')}</p></article>`).join('')}</div>
      <h2>Connections</h2>
      ${list(a.connections, (k) => `<strong>${esc(componentName(k.from))}</strong> → <strong>${esc(componentName(k.to))}</strong>: ${rich(k.label)}`)}`;
  }

  function modules(id) {
    if (!id) {
      return `<h1>Modules</h1><p class="lead">Each module is one area of the code with one job.</p>
        <div class="cards">${M.modules.map((m) => `<a class="card link-card" href="${href('modules', m.id)}">
          <h3>${esc(m.name)}</h3><p class="path"><code>${esc(m.path)}</code></p><p>${rich(lensText(m.purpose))}</p>
          ${m.status === 'not_analyzed' ? '<span class="tag warn">not analyzed</span>' : ''}</a>`).join('')}</div>`;
    }
    const m = byId(M.modules, id);
    if (!m) return notFound('module', id);
    const flowsHere = M.flows.filter((f) => f.steps.some((s) => inModule(m, s.file)));
    const terms = M.glossary.filter((g) => g.module_ids.includes(m.id));
    const usedBy = M.modules.filter((o) => o.dependencies.internal.includes(m.id));
    const iface = m.interface.length
      ? `<table><thead><tr><th>Name</th><th>What it does</th><th>Where</th></tr></thead><tbody>${m.interface.map((i) => `<tr>
          <td><code>${esc(i.name)}</code> <span class="tag">${esc(i.kind)}</span>${lens === 'technical' ? `<pre><code>${esc(i.signature)}</code></pre>` : ''}</td>
          <td>${rich(i.description)}</td><td>${fileLink(i.file, i.line)}</td></tr>`).join('')}</tbody></table>`
      : '<p class="muted">No public interface.</p>';
    return `<p class="crumbs"><a href="${href('modules')}">Modules</a> / ${esc(m.name)}</p>
      <h1>${esc(m.name)} ${m.status === 'not_analyzed' ? '<span class="tag warn">not analyzed</span>' : ''}</h1>
      <p class="path"><code>${esc(m.path)}</code></p>
      <p class="lead">${rich(lensText(m.purpose))}</p>
      <h2>Public interface</h2>${iface}
      <h2>Rules that must stay true</h2>${list(m.invariants, rich)}
      <h2>Depends on</h2>${list(m.dependencies.internal, moduleLink)}${tags(m.dependencies.external)}
      <h2>Used by</h2>${list(usedBy, (o) => moduleLink(o.id))}
      <h2>Key files</h2>${list(m.key_files, (f) => `${fileLink(f.path)} — ${rich(f.role)}`)}
      <h2>Tours through this module</h2>${list(flowsHere, (f) => `<a href="${href('tours', f.id)}">${esc(f.title)}</a>`)}
      <h2>Terms</h2>${list(terms, (g) => `<a href="${href('glossary', g.term)}">${esc(g.term)}</a>`)}`;
  }

  function tours(id) {
    if (!id) {
      return `<h1>Tours</h1><p class="lead">Each tour follows one thing the system does, step by step, through the real code.</p>
        <div class="cards">${M.flows.map((f) => `<a class="card link-card" href="${href('tours', f.id)}">
          <h3>${esc(f.title)}</h3><p>${rich(lensText(f.summary))}</p><p class="muted">${f.steps.length} steps</p></a>`).join('')}</div>`;
    }
    const f = byId(M.flows, id);
    if (!f) return notFound('tour', id);
    return `<p class="crumbs"><a href="${href('tours')}">Tours</a> / ${esc(f.title)}</p>
      <h1>${esc(f.title)}</h1><p class="lead">${rich(lensText(f.summary))}</p>
      <ol class="steps">${f.steps.map((s, i) => `<li class="step" id="step-${i + 1}">
        <div class="step-num">${i + 1}</div>
        <div class="step-body"><h3>${esc(s.title)}</h3><p>${rich(lensText(s.text))}</p>
          <p>${fileLink(s.file, s.line_start)}${s.line_end > s.line_start ? '–' + s.line_end : ''}</p>
          ${s.snippet ? codeBlock(s.snippet) : ''}</div></li>`).join('')}</ol>`;
  }

  function glossary(term) {
    const groups = [['domain', 'Domain terms'], ['tech', 'Technical terms']];
    return '<h1>Glossary</h1>' + groups.map(([kind, title]) => {
      const items = M.glossary.filter((g) => g.kind === kind).sort((a, b) => a.term.localeCompare(b.term));
      if (!items.length) return '';
      return `<h2>${title}</h2><dl class="glossary">${items.map((g) => `
        <dt id="${termAnchor(g.term)}"${term === g.term ? ' class="hit"' : ''}>${esc(g.term)}</dt>
        <dd>${rich(g.definition)}${g.module_ids.length ? ' <span class="muted">— ' + g.module_ids.map(moduleLink).join(', ') + '</span>' : ''}</dd>`).join('')}</dl>`;
    }).join('');
  }

  function stepTarget(s) {
    if (s.ref_type === 'module') { const m = byId(M.modules, s.ref_id); return [href('modules', s.ref_id), m ? m.name : s.ref_id]; }
    if (s.ref_type === 'flow') { const f = byId(M.flows, s.ref_id); return [href('tours', s.ref_id), f ? f.title : s.ref_id]; }
    if (s.ref_type === 'glossary') return [href('glossary', s.ref_id), s.ref_id];
    return ['../' + s.ref_id.split('/').map((p) => encodeURIComponent(p)).join('/'), s.ref_id];
  }

  function startHere(id) {
    if (id) {
      const p = byId(M.paths, id);
      if (!p) return notFound('path', id);
      return `<p class="crumbs"><a href="${href('paths')}">Start here</a> / ${esc(p.title)}</p>
        <h1>${esc(p.title)}</h1><p class="lead">For: ${esc(p.audience)}</p>
        <ol class="steps">${p.steps.map((s, i) => { const [link, label] = stepTarget(s); return `<li class="step">
          <div class="step-num">${i + 1}</div><div class="step-body"><h3><a href="${esc(link)}">${esc(label)}</a></h3><p>${rich(s.note)}</p></div></li>`; }).join('')}</ol>`;
    }
    const n = M.agent_notes;
    return `<h1>Start here</h1><p class="lead">Pick the path that fits you.</p>
      <div class="cards">${M.paths.map((p) => `<a class="card link-card" href="${href('paths', p.id)}"><h3>${esc(p.title)}</h3><p>${esc(p.audience)}</p></a>`).join('')}</div>
      <h2>For AI agents</h2>
      <p class="muted">The full machine-readable model is <code>explorer/data/model.json</code>. The repo root has <code>AGENTS.md</code>.</p>
      <h3>Rules</h3>${list(n.rules, rich)}
      <h3>Traps</h3>${list(n.traps, rich)}
      <h3>Do not touch</h3>${list(n.do_not_touch, (d) => `<code>${esc(d.path)}</code> — ${rich(d.reason)}`)}
      <h3>Commands</h3>${n.commands.map((c) => `<p class="muted">${esc(c.label)}</p><pre><code>${esc(c.command)}</code></pre>`).join('')}`;
  }

  let index = null;
  function buildIndex() {
    const out = [];
    const both = (o) => (o ? o.functional + ' ' + o.technical : '');
    const add = (kind, title, text, link) => out.push({ kind, title, text, link, hay: (title + ' ' + text).toLowerCase() });
    add('Project', M.project.name, M.project.tagline + ' ' + both(M.project.purpose), href('overview'));
    M.project.capabilities.forEach((c) => add('Capability', c.title, c.functional + ' ' + c.technical, href('overview')));
    M.architecture.components.forEach((c) => add('Component', c.name, both(c.description), href('architecture')));
    M.modules.forEach((m) => add('Module', m.name, [m.path, both(m.purpose), ...m.interface.map((i) => i.name + ' ' + i.description), ...m.invariants].join(' '), href('modules', m.id)));
    M.flows.forEach((f) => add('Tour', f.title, [both(f.summary), ...f.steps.map((s) => s.title + ' ' + both(s.text) + ' ' + s.file)].join(' '), href('tours', f.id)));
    M.glossary.forEach((g) => add('Term', g.term, g.definition, href('glossary', g.term)));
    return out;
  }
  function excerpt(text, term) {
    const at = Math.max(0, text.toLowerCase().indexOf(term));
    const start = Math.max(0, at - 60);
    return (start > 0 ? '…' : '') + text.slice(start, start + 160) + (start + 160 < text.length ? '…' : '');
  }
  function search(query) {
    const q = (query || '').trim();
    index = index || buildIndex();
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    const hits = terms.length ? index.filter((e) => terms.every((t) => e.hay.includes(t))) : [];
    return `<h1>Search</h1><p class="muted">${hits.length} result${hits.length === 1 ? '' : 's'} for “${esc(q)}”</p>` +
      list(hits.slice(0, 100), (h) => `<span class="tag">${esc(h.kind)}</span> <a href="${h.link}">${esc(h.title)}</a><div class="snippet">${esc(excerpt(h.text, terms[0]))}</div>`);
  }

  // ---- diagrams ------------------------------------------------------------
  let mermaidReady = false;
  function wireDiagram(holder) {
    holder.querySelectorAll('g.node').forEach((g) => {
      const match = /flowchart-(.+)-\d+$/.exec(g.id || '');
      if (!match) return;
      const comp = byId(M.architecture.components, match[1]);
      const moduleId = comp ? comp.module_ids[0] : (byId(M.modules, match[1]) ? match[1] : null);
      if (!moduleId && !comp) return;
      const go = () => {
        if (moduleId) { location.hash = href('modules', moduleId); return; }
        const card = document.getElementById('comp-' + comp.id);
        if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      };
      g.classList.add('clickable');
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'link');
      g.addEventListener('click', go);
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    });
  }
  async function drawDiagrams() {
    const blocks = Array.from(view.querySelectorAll('.mermaid-src'));
    if (!blocks.length || !window.mermaid) return;
    if (!mermaidReady) {
      const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: dark ? 'dark' : 'default' });
      mermaidReady = true;
    }
    for (let i = 0; i < blocks.length; i += 1) {
      const el = blocks[i];
      try {
        const { svg } = await window.mermaid.render('dr-diagram-' + i + '-' + Date.now(), el.textContent);
        const holder = document.createElement('div');
        holder.className = 'mermaid-out';
        holder.innerHTML = svg;
        el.replaceWith(holder);
        wireDiagram(holder);
      } catch (err) {
        el.insertAdjacentHTML('beforebegin', '<p class="warn">This diagram could not be drawn, so its source is shown.</p>');
        console.warn('[explorer] mermaid render failed', err);
      }
    }
  }

  // ---- router --------------------------------------------------------------
  const ROUTES = { overview, architecture, modules, tours, glossary, paths: startHere, search };
  const NAV = [['overview', 'Overview'], ['architecture', 'Architecture'], ['modules', 'Modules'], ['tours', 'Tours'], ['glossary', 'Glossary'], ['paths', 'Start here']];
  const navEl = document.getElementById('nav');
  const searchEl = document.getElementById('search');
  const lensButtons = Array.from(document.querySelectorAll('[data-lens]'));

  function parseHash() {
    const raw = location.hash.replace(/^#\/?/, '');
    const [name, ...rest] = raw.split('/');
    let arg = null;
    try { arg = rest.length ? decodeURIComponent(rest.join('/')) : null; } catch (e) { arg = null; }
    return { name: ROUTES[name] ? name : 'overview', arg };
  }

  function render() {
    const { name, arg } = parseHash();
    navEl.querySelectorAll('a').forEach((a) => a.classList.toggle('active', a.dataset.route === name));
    lensButtons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lens === lens)));
    view.innerHTML = ROUTES[name](arg);
    if (name === 'architecture') drawDiagrams();
    const target = name === 'glossary' && arg ? document.getElementById(termAnchor(arg)) : null;
    if (target) target.scrollIntoView({ block: 'center' }); else window.scrollTo(0, 0);
    if (name !== 'search' && document.activeElement !== searchEl) searchEl.value = '';
  }

  document.title = M.project.name + ' · Project Explorer';
  document.getElementById('brand').textContent = M.project.name;
  navEl.innerHTML = NAV.map(([route, label]) => `<a href="${href(route)}" data-route="${route}">${label}</a>`).join('');
  lensButtons.forEach((b) => b.addEventListener('click', () => {
    lens = b.dataset.lens === 'technical' ? 'technical' : 'functional';
    store.set(LENS_KEY, lens);
    render();
  }));
  let timer = 0;
  searchEl.addEventListener('input', () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      const value = searchEl.value.trim();
      location.hash = value ? '#/search/' + encodeURIComponent(value) : '#/overview';
    }, 150);
  });
  window.addEventListener('hashchange', render);
  render();
})();
```

- [ ] **Step 7: Run the structure test**

Run: `pytest tests/test_explorer_template.py -q --no-cov`
Expected: PASS.

- [ ] **Step 8: Render the fixture in Chrome and check it by eye**

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace/plugins/personal-plugin/tools/document-repo
OUT=/private/tmp/claude-502/-Users-troydavis-dev-personal-plugins/b4a57bc9-257d-4ac5-81b3-551f29edc7c1/scratchpad/explorer-fixture
python3 -m document_repo build --model tests/fixtures/sample_model.json --explorer-dir "$OUT" --template ../../skills/document-repo/templates/explorer
echo "file://$OUT/index.html"
```

Load the `claude-in-chrome` skill. Open the URL in a new tab. Check each item:

1. Every nav item renders (Overview, Architecture, Modules, Tours, Glossary, Start here).
2. The Architecture diagram draws. A click on the API box opens `#/modules/src-api`.
3. "How it works" switches the text: the technical purpose shows, and the tour snippet shows open, not inside a details box.
4. A search for `note` lists results.
5. `read_console_messages` with pattern `error|Error` returns nothing.
6. `read_network_requests` lists only `file://` URLs.
7. At a window width of 390px there is no sideways scroll.

If the diagram does not draw, check the `g.node` ids in the SVG (`javascript_tool`: `[...document.querySelectorAll('g.node')].map(g => g.id)`), then fix the regex in `wireDiagram` to match them.

- [ ] **Step 9: Commit**

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace
git add plugins/personal-plugin/skills/document-repo/templates plugins/personal-plugin/tools/document-repo/tests/test_explorer_template.py
git commit -m "feat(document-repo): offline explorer template (vanilla JS + vendored Mermaid 11.4.1)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 12: Skill reference files

**Files:**
- Create: `plugins/personal-plugin/skills/document-repo/references/model-schema.md`
- Create: `plugins/personal-plugin/skills/document-repo/references/comment-standards.md`
- Create: `plugins/personal-plugin/skills/document-repo/references/doc-templates.md`
- Create: `plugins/personal-plugin/skills/document-repo/references/explorer-contract.md`
- Create: `plugins/personal-plugin/skills/document-repo/references/update-mode.md`
- Create: `plugins/personal-plugin/skills/document-repo/references/agent-prompts.md`

**Interfaces:**
- Consumes: the schema (Task 6), CLI subcommands (Tasks 2–10), the explorer routes (Task 11).
- Produces: the files SKILL.md (Task 13) tells agents to read, referenced by these exact paths.

- [ ] **Step 1: Write `references/model-schema.md`**

````markdown
# Project model — field guide

The exact shape is enforced by `tools/document-repo/src/document_repo/schema.py`
(`SCHEMA_VERSION = 1`). If this guide and the code disagree, the code is right.
This guide says what *good* content is.

## Lenses

Many fields are `{ "functional": "...", "technical": "..." }`.

- **functional** — what it does and why it matters, in plain words. No jargon
  unless it is in the glossary. At most 3 sentences. Reader: a smart person
  who has never seen the code.
- **technical** — how it works: names the mechanism, the library, the data
  structure, the file. Reader: a proficient junior developer.

## Sections

| Section | Content rules |
|---------|---------------|
| `meta` | Filled by `assemble`. Never written by hand. |
| `project` | `tagline` is 1 sentence. `users` are roles, not people. 3–8 `capabilities`, each user-visible. `tech_stack` lists runtimes, frameworks and stores, with each one's role. `run` holds the real commands from the repo (README, package.json, Makefile), copied exactly. |
| `architecture.components` | 3–12 runtime or deployable parts (service, worker, datastore, UI, CLI, external API). `module_ids` links each part to the code that implements it. |
| `architecture.connections` | One per real interaction. The label names the mechanism ("HTTP JSON", "SQL", "queue"). |
| `architecture.diagrams` | Mermaid `flowchart`. **Node ids must equal component ids** (or module ids). That is how clicks in the explorer open a module. Keep to ≤15 nodes per diagram. Add a second diagram (for example, deployment) only when it adds information. |
| `modules[]` | One per entry in `modules.final.json`. `interface` lists public items only (exported, routed, or called from another module). `invariants` are testable statements ("every note has a non-empty body"), never vague ones ("code is clean"). `dependencies.internal` holds module ids. `external` holds package names. |
| `flows[]` | 3–6 flows that matter most to a user. 3–10 steps each, in execution order. Each step points at real `file` + `line_start`/`line_end` at the analysed commit. `snippet` (optional, ≤30 lines) is copied exactly from those lines. |
| `glossary[]` | Every domain term used anywhere in the model or docs, plus tech terms a junior might not know. `kind` is `domain` or `tech`. |
| `paths[]` | At least three, with ids `new-dev` ("New developer, day 1"), `ai-agent` ("AI agent, first read"), and `change-x` ("I need to change something"). Each step references a module, flow, glossary term, or a doc path relative to the repo root. |
| `agent_notes` | `rules`: conventions an agent must follow. `traps`: things that look safe but are not. `do_not_touch`: generated, vendored, or production-critical paths with reasons. `commands`: build/test/lint, copied exactly. |

## Quality bar

- Every claim is checked against the code. When unsure, leave it out.
- No marketing words ("powerful", "seamless", "robust").
- Line numbers refer to the commit in `meta.source_commit`. `remap` moves them after comments are added. Never edit them by hand.
````

- [ ] **Step 2: Write `references/comment-standards.md`**

````markdown
# Comment standards

Goal: a proficient junior developer understands a file in minutes, and an AI
agent can find a file's role, contract and traps by reading its header.

## The three kinds

| Kind | Where | Must contain |
|------|-------|--------------|
| File header | Top of every source file the inventory did not skip (after a shebang or encoding line, if present) | Role in one sentence; where it fits (module, callers); main inputs/outputs; side effects; invariants (optional); traps (optional) |
| Doc comment | Every public function, class, method, exported constant; private ones only when non-obvious | Purpose; parameters; return value; errors raised; an example when the call is not obvious |
| "Why" note | Above non-obvious code only | The reason: a constraint, workaround, bug reference, magic number, ordering requirement |

Use these exact labels in headers, so agents can grep them: `Role:`,
`Used by:`, `Inputs:`, `Outputs:`, `Side effects:`, `Invariants:`, `Traps:`.
Leave a label out when it is empty.

## Hard rules

1. **Comments go on their own lines.** Never append a comment to a code line. The comment-lines verifier rejects it, and the file will be reverted.
2. **Never delete, move or reword an existing comment.** If one looks wrong, report it in your result (`suspect_comments`). Do not change it.
3. **Never change code**, not even whitespace inside a code line. Add new lines only.
4. Explain why and intent. Do not restate what the code says (`# increment i` is forbidden).
5. No TODOs, no opinions about code quality, no names of people, no secrets, no example values copied from real data.
6. SQL migration files (`header_only` in the inventory) get a file header only.
7. Keep each doc comment ≤12 lines. If it needs more, the module README is the place.
8. Write in plain English. Follow `~/.claude/styles/WRITING_RULES.md` when it exists.

## Formats

### Python

```python
"""Store and look up notes in Postgres.

Role: data-access layer for notes; the only module that writes the notes table.
Used by: api.routes (create/list endpoints), jobs.reindex.
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

### TypeScript / JavaScript

```typescript
/**
 * @file Capture pipeline entry: turns an incoming message into a stored thought.
 *
 * Role: orchestrates parse → embed → store for one message.
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

### CSS / HTML

Use `/* ... */` and `<!-- ... -->` with the same labels, on their own lines.
````

- [ ] **Step 3: Write `references/doc-templates.md`**

`````markdown
# Documentation templates

Every generated block sits between markers and is written with:

```bash
PYTHONPATH="$TOOL_SRC" python3 -m document_repo upsert-section --file <file> --section <name> --content-file <tmp.md>
```

Write the body to a temp file under the run directory first. Section names are fixed:

| File | Section names (in order) |
|------|--------------------------|
| `README.md` (root) | `overview`, `quick-start`, `repo-map`, `explorer` |
| `<module path>/README.md` | `module` |
| `AGENTS.md` | `agents` |
| `docs/ARCHITECTURE.md` | `architecture` |
| `docs/GLOSSARY.md` | `glossary` |
| `CLAUDE.md` (only if it exists) | `agents-pointer` |

If the root `README.md` already has a title line, keep it. Do not add a
second H1. If the file is new, start the first section with `# <project name>`.

## Root README

```markdown
## What this is
<project.purpose.functional>

<project.purpose.technical>

## What it can do
- **<capability.title>** — <capability.functional>

## Quick start
<project.run.setup as numbered steps>
<project.run.commands as fenced blocks with their labels>

## Repo map
| Path | What lives there |
|------|------------------|
| `<module.path>/` | <module.purpose.functional> ([README](<module.path>/README.md)) |

## Explore it
Open [`explorer/index.html`](explorer/index.html) in a browser for an
interactive tour: architecture, modules, step-by-step flows, and a glossary.
It works offline.
```

## Module README

```markdown
# <module.name>

<module.purpose.functional>

## How it works
<module.purpose.technical>

## Public interface
| Name | Kind | What it does | Where |
|------|------|--------------|-------|

## Rules that must stay true
- <invariants>

## Depends on
- Internal: <links to other module READMEs>
- External: <packages>

## Key files
| File | Role |
|------|------|

## Flows that pass through here
- <flow.title> — see the explorer: `explorer/index.html#/tours/<flow.id>`
```

## AGENTS.md

```markdown
# AGENTS.md

Guide for AI coding agents working in this repo. Humans: start at README.md.

## Repo map
<module path → one-line purpose, as a table>

## Entry points
<from inventory entry_candidates that analysis confirmed, with what each starts>

## Commands
<agent_notes.commands as fenced blocks>

## Rules
- <agent_notes.rules>

## Traps
- <agent_notes.traps>

## Do not touch
| Path | Why |
|------|-----|

## Conventions in the code
File headers use the labels `Role:`, `Used by:`, `Inputs:`, `Outputs:`,
`Side effects:`, `Invariants:`, `Traps:`. Grep for them.

## Full model
The machine-readable project model is `explorer/data/model.json`
(schema version <meta.schema_version>, built from commit <meta.source_commit>).
```

## docs/ARCHITECTURE.md

````markdown
# Architecture

<architecture.summary.functional>

<architecture.summary.technical>

## Diagram
```mermaid
<each architecture.diagrams[].mermaid>
```

## Components
### <component.name> (<kind>)
<description.technical> Implemented in: <module links>.

## How the parts talk
| From | To | How |
|------|----|-----|

## Main flows
### <flow.title>
<flow.summary.technical>
1. <step.title> — <step.text.technical> (`<file>:<line_start>`)

## Design decisions
<decisions found in code comments, ADRs, commit messages or docs, each with
its reason. Only include decisions with evidence. Omit the section if none.>
````

## docs/GLOSSARY.md

```markdown
# Glossary

## Domain terms
**<term>** — <definition>

## Technical terms
**<term>** — <definition>
```

## CLAUDE.md pointer (body of section `agents-pointer`)

```markdown
See `AGENTS.md` for the repo map, entry points, commands, rules and traps. The full project model is `explorer/data/model.json`.
```
`````

Note for the implementer: the outer five-backtick fence above exists only in this plan. In the real file, the ARCHITECTURE template block keeps its four-backtick fence, so its inner three-backtick `mermaid` fence nests correctly.

- [ ] **Step 4: Write `references/explorer-contract.md`**

````markdown
# Explorer contract

The explorer is a fixed app (`templates/explorer/`) copied into
`<target>/explorer/` on every run. Never edit it inside a target repo. Change
the template in the plugin and re-run.

| View (route) | Reads |
|--------------|-------|
| Overview `#/overview` | `meta.repo_name`, `project.*`, `paths[]` |
| Architecture `#/architecture` | `architecture.*`, `modules[].name` |
| Modules `#/modules/<id>` | `modules[]`, `flows[].steps[].file`, `glossary[].module_ids` |
| Tours `#/tours/<id>` | `flows[]` |
| Glossary `#/glossary/<term>` | `glossary[]` |
| Start here `#/paths/<id>` | `paths[]`, `agent_notes` |
| Search `#/search/<q>` | all text fields |

Rules that the data must satisfy for the app to work well:

1. Mermaid node ids equal component ids (or module ids). Otherwise boxes are not clickable.
2. Both lens texts are filled for every lens field. An empty technical text falls back to the functional one.
3. Backticks in text render as inline code. No other markup is interpreted (everything is HTML-escaped).
4. `meta.repo_url` set → file links open the code on the host at `meta.source_commit`. Null → paths show as plain text.
5. `paths[].steps[]` of type `doc` link to `../<ref_id>`, relative to `explorer/`.

Acceptance for every run: open `explorer/index.html` from disk; 0 console
errors; every view renders; the only network requests are `file://`.
````

- [ ] **Step 5: Write `references/update-mode.md`**

````markdown
# Update mode (`--update`)

Use when `explorer/data/state.json` exists and the code changed since.

1. Preflight as usual (clean tree, new branch `docs/document-repo-update-<YYYYMMDD>`, baseline).
2. Find changes:

   ```bash
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo changes --repo "$TARGET" > "$RUN_DIR/changes.json"
   ```

   Exit 2 means `state.json` names a commit that is not in history (for example, after a rebase or squash). Tell the user and offer a full run.
3. Inventory and module proposal run as normal. Then build `modules.final.json` from the **existing** model's module list. Add a module only for `unmapped_files` that do not fit an existing one. Drop a module only when all its files are in `removed_files`.
4. Re-analyse only `affected_modules` (plus new modules). Write their records to `$RUN_DIR/modules/<id>.json`.
5. Run synthesis again only when an affected module's `interface` or `dependencies` changed, or a module was added or removed. Otherwise skip `system.json`. `assemble` then reuses the base model's system sections.
6. Move the base model's line numbers to the current HEAD (human comment-only edits may have shifted them), then assemble with it:

   ```bash
   cp "$TARGET/explorer/data/model.json" "$RUN_DIR/base-model.json"
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/base-model.json" --repo "$TARGET" --to HEAD
   PYTHONPATH="$TOOL_SRC" python3 -m document_repo assemble --run-dir "$RUN_DIR" --repo "$TARGET" --base-model "$RUN_DIR/base-model.json"
   ```

7. Gate: the plan lists only the affected modules, files and doc sections.
8. Phase 2 comments: only the changed files in affected modules. Only new or changed items get comments. Existing comments are never touched.
9. Phase 3: rewrite only the marker sections whose content changed (affected module READMEs, plus root/AGENTS/ARCHITECTURE/GLOSSARY when synthesis ran).
10. Phase 4: remap, then build, as in a full run.
````

- [ ] **Step 6: Write `references/agent-prompts.md`**

````markdown
# Agent prompts

Fill the `{placeholders}` and pass each prompt to the Agent tool. Each agent
writes exactly one output file and replies with a 3-line summary. Agents never
commit, never push, and never edit files outside their stated scope.

## 1. Module analyst (Phase 1, one per module, up to 6 in parallel)

```text
You are documenting one module of the repo at {TARGET} for a junior developer
and for AI agents. Read every file listed below. Do not edit any file.

Module: id={id} path={path}
Files: {files}
Inventory entry points (hints only): {entry_candidates_in_module}
Model field guide: {SKILL_DIR}/references/model-schema.md

Write JSON to {RUN_DIR}/modules/{id}.json with exactly this shape:
{"module": <one modules[] entry per the field guide, status "analyzed">,
 "files": [{"path": str, "summary": str, "callers": [str], "side_effects": [str]}]}

Rules: one "files" entry per listed file. Line numbers are 1-based at the
current HEAD. Every interface item has file + line. Only claim what the code
shows. For files over 2000 lines, read them in parts by class or function.
For dependencies.internal, use module ids from this list: {all_module_ids}.
When done, run: python3 -c "import json;json.load(open('{RUN_DIR}/modules/{id}.json'))"
```

## 2. Synthesizer (Phase 1, one agent, after all analysts)

```text
Read every {RUN_DIR}/modules/*.json, {RUN_DIR}/inventory.json, and the root
README/docs of {TARGET} if present. Read source files only to confirm a flow.
Field guide: {SKILL_DIR}/references/model-schema.md.
Explorer rules: {SKILL_DIR}/references/explorer-contract.md.

Write {RUN_DIR}/system.json with keys project, architecture, flows, glossary,
paths, agent_notes, per the field guide. Mermaid node ids must equal component
ids. Flow steps cite real file:line ranges and copy snippets exactly (≤30
lines). Copy run commands exactly from the repo. paths must include ids
new-dev, ai-agent, change-x.
```

## 3. Commenter (Phase 2, one per module, up to 4 in parallel — modules never share files)

```text
Add comments to these files in {TARGET}, and nothing else: {files}
(header_only files: {header_only_files} — file header only).
Context — module record: {RUN_DIR}/modules/{id}.json. File notes:
{RUN_DIR}/file-notes.json. System view: {RUN_DIR}/model.json (project,
architecture, glossary). Standards: {SKILL_DIR}/references/comment-standards.md
— follow every hard rule.

Use the Edit tool only. Insert new lines; never change or remove an existing
line. After each file, run:
PYTHONPATH={TOOL_SRC} python3 -m document_repo verify --repo {TARGET} --before HEAD <file>
If it fails, run `git -C {TARGET} checkout HEAD -- <file>`, then try once more
with smaller, simpler insertions. If it fails again, restore it and move on.

Write {RUN_DIR}/comments/{id}.json:
{"commented": [paths], "reverted": [{"path", "detail"}], "suspect_comments": [{"path", "line", "why"}]}
```

## 4. Module docs writer (Phase 3, batches of up to 6 modules)

```text
For each module id in {ids}, write the body of the `module` section for
{TARGET}/<module.path>/README.md, following the "Module README" template in
{SKILL_DIR}/references/doc-templates.md, using only {RUN_DIR}/model.json.
Write each body to {RUN_DIR}/docs/{id}.md, then run:
PYTHONPATH={TOOL_SRC} python3 -m document_repo upsert-section --file {TARGET}/<module.path>/README.md --section module --content-file {RUN_DIR}/docs/{id}.md
Skip the root module ("."): the root README is written separately.
```

## 5. Examiner (end of run)

```text
Read the SOURCE CODE of {TARGET} (not README, AGENTS.md, docs/ or explorer/).
Write 10 questions a new developer must be able to answer to work safely in
this repo: purpose, where X happens, what calls Y, what must stay true, how
to run tests, one trap. Mix easy and hard. For each, write the correct answer
with file:line evidence. Write {RUN_DIR}/quiz.json:
[{"q": str, "answer": str, "evidence": str}]. Then stop.
```

## 6. Student (end of run, fresh agent)

```text
Answer the questions in {RUN_DIR}/quiz-questions.json about the repo at
{TARGET}. You may read ONLY: README.md, AGENTS.md, CLAUDE.md, docs/**,
any */README.md, and explorer/data/model.json. Do not open any other file.
Write {RUN_DIR}/quiz-answers.json: [{"q": str, "answer": str, "source": str}].
```

The orchestrator writes `quiz-questions.json` (questions only, no answers)
from `quiz.json`. It then gives the examiner both files to grade:
{"score": n, "per_question": [{"q", "correct": bool, "why"}]} → `{RUN_DIR}/quiz-grade.json`.
````

- [ ] **Step 7: Lint and commit**

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace
npx -y markdownlint-cli@0.45.0 plugins/personal-plugin/skills/document-repo/references/*.md plugins/personal-plugin/skills/document-repo/templates/explorer/vendor/README.md
python3 scripts/check_injections.py
git add plugins/personal-plugin/skills/document-repo/references
git commit -m "docs(document-repo): reference guides and agent prompts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

Expected: markdownlint prints nothing; `check_injections.py` passes. If markdownlint flags line length (MD013) or the fenced-code style, follow the repo's `.markdownlint*` config (`ls -a | grep markdownlint`) rather than disabling rules inline.

---

### Task 13: SKILL.md

**Files:**
- Create: `plugins/personal-plugin/skills/document-repo/SKILL.md`

**Interfaces:**
- Consumes: every CLI subcommand (`inventory`, `modules`, `verify`, `assemble`, `build`, `remap`, `upsert-section`, `changes`); `references/*.md`; `templates/explorer/`.

- [ ] **Step 1: Write `SKILL.md`**

````markdown
---
name: document-repo
description: >
  Document an entire repository for junior developers and AI agents — adds
  explanatory comments to the source (each file proven comment-only by a
  verifier, failures reverted), writes READMEs at module boundaries plus
  AGENTS.md, docs/ARCHITECTURE.md and docs/GLOSSARY.md, and builds an offline
  interactive explorer web app in explorer/, all generated from one project
  model. One approval gate after analysis; work happens on a new branch with
  one commit per module. Supports --update for incremental refresh and
  --phase to re-run comments, docs or explorer alone.
argument-hint: "[path] [--update] [--phase comments|docs|explorer]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion, Bash
---

# document-repo

Comment, document, and build an explorer for a target repo. The design is in
`docs/plans/2026-11-22-document-repo-design.md` in the marketplace repo.

**Prime rule: never change behaviour.** Every source edit is an insertion of
comment lines, and the verifier proves it before each commit.

## Setup

Run these first. Shell state does not persist between Bash calls, so repeat
the variable lines in each call that needs them.

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(find ~ -path '*/plugins/personal-plugin' -type d 2>/dev/null | head -1)}"
TOOL_SRC="$PLUGIN_DIR/tools/document-repo/src"
SKILL_DIR="$PLUGIN_DIR/skills/document-repo"
TARGET="$(git -C "${ARG_PATH:-.}" rev-parse --show-toplevel)"
RUN_DIR="$TARGET/.document-repo"
mkdir -p "$RUN_DIR" && printf '*\n' > "$RUN_DIR/.gitignore"
PYTHONPATH="$TOOL_SRC" python3 -m document_repo --version
```

`ARG_PATH` is the path argument (default: current directory). `RUN_DIR`
ignores itself (its `.gitignore` holds `*`), so nothing in it is ever
committed. It is not under `.git/` because agents may not write there. If the version command
fails, stop and report: Python 3.10+ is required.

Parse flags: `--update`, and `--phase comments|docs|explorer`. Do not combine
`--phase` with `--update`. If both are given, ask which one to run.

## Phase 0 — Preflight

1. `git -C "$TARGET" status --porcelain` must print nothing. Otherwise stop and tell the user to commit or stash.
2. Record the base: `git -C "$TARGET" rev-parse HEAD > "$RUN_DIR/base.txt"` (create `$RUN_DIR` first).
3. Branch: `git -C "$TARGET" switch -c docs/document-repo` (with `--update`: `docs/document-repo-update-$(date +%Y%m%d)`). If the branch exists, stop and ask.
4. If `explorer/data/state.json` exists and neither `--update` nor `--phase` was given, ask with AskUserQuestion: **Update** (recommended — only changed modules) or **Full rebuild**.
5. Find the verification commands. Look in package.json `scripts` (test, lint, typecheck/type-check), pyproject/pytest.ini/tox.ini (pytest), Makefile targets (test, lint), and CI workflow files. Write `$RUN_DIR/commands.json` as `{"test": [...], "lint": [...], "typecheck": [...]}`.
6. If the inventory has JS/TS files, check the printer: `PYTHONPATH="$TOOL_SRC" python3 -c "from pathlib import Path; from document_repo.verify import typescript_available as t; print(t(Path('$TARGET')))"`. On `False`, ask with AskUserQuestion: **Install TypeScript** (recommended: `npm install -g typescript`, then re-check) or **Skip JS/TS files** (they get no comments and are listed in the report). JS/TS edits can only be verified by the TypeScript printer.
7. Baseline: run each command with a 10-minute timeout. Record the exit code, the duration, and the last 40 lines in `$RUN_DIR/baseline.json`. Never install dependencies without asking. A command that cannot run is recorded as `not_runnable`. Failing or not-runnable commands do not block the run. They go in the gate summary and the report.

## Phase 1 — Analyze

With `--phase docs` or `--phase explorer`, skip this phase: copy the committed model (`cp "$TARGET/explorer/data/model.json" "$RUN_DIR/model.json"`) and go to the gate. `--phase comments` runs this phase in full, because commenters need fresh module records. With `--update`, follow `$SKILL_DIR/references/update-mode.md`.

1. Inventory: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo inventory "$TARGET" --out "$RUN_DIR/inventory.json"`
2. Proposal: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo modules "$RUN_DIR/inventory.json" --out "$RUN_DIR/modules.json"`
3. Review the proposal. Merge modules with fewer than 3 files into a sibling or parent with a related job. Split modules with more than 150 files or 20,000 lines by the next path segment. Write the result to `$RUN_DIR/modules.final.json` (same shape). Every non-skipped file must belong to exactly one module.
4. Dispatch one **Module analyst** per module (prompt 1 in `$SKILL_DIR/references/agent-prompts.md`), up to 6 at a time. If an analyst fails or writes invalid JSON, retry it once. After a second failure, leave its record absent (`assemble` makes a `not_analyzed` stub).
5. Dispatch one **Synthesizer** (prompt 2).
6. Assemble and validate: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo assemble --run-dir "$RUN_DIR" --repo "$TARGET"`. On exit 1, fix the listed errors in the module records or `system.json`, then re-run. Repeat until it exits 0.

## Gate — owner approval

Show a short summary:

- The purpose (2 sentences), the module list (id, path, file count, status), and the flow titles.
- **Write plan:** files that will get comments (count, plus the header-only count), READMEs to create or update, the root docs files, `CLAUDE.md` pointer yes/no, and the explorer views.
- Baseline failures, `not_analyzed` modules, and skipped files by reason (counts).

Then ask with AskUserQuestion. Options: **Approve and write** (recommended), **Change the plan** (take notes, adjust, and ask again), **Stop** (delete the branch with `git switch -` and `git branch -D`. Nothing was written). Do not write to the target before approval.

## Phase 2 — Comments

Skip this phase when `--phase` is `docs` or `explorer`.

For each module (status `analyzed`), dispatch a **Commenter** (prompt 3), up to 4 at a time. Each module's files are disjoint, so parallel commenters never touch the same file. After each commenter finishes:

1. `PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo "$TARGET" --before HEAD --changed`. For every result with `"ok": false`, restore the file: `git -C "$TARGET" checkout HEAD -- <path>`. Add it to the report.
2. Run the `test` commands from `commands.json`. If a command that passed at baseline now fails, revert the module's files (`git -C "$TARGET" checkout HEAD -- <files>`) and record it. If the suite takes over 5 minutes, run it once at the end of Phase 2 instead. On a regression, revert module commits one at a time (`git revert --no-edit <sha>`) until it passes.
3. Commit only that module's files:

   ```bash
   git -C "$TARGET" add -- <files>
   git -C "$TARGET" commit -m "docs(<module id>): add explanatory comments" -m "Comment-only change, verified by document-repo verify."
   ```

Never `git add -A` in the target.

## Phase 3 — Docs

Skip this phase when `--phase` is `comments` or `explorer`.

1. Root `README.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`: write each section body from `$RUN_DIR/model.json` per `$SKILL_DIR/references/doc-templates.md`, then `upsert-section` it.
2. Module READMEs: dispatch **Module docs writers** (prompt 4) in batches of up to 6 modules.
3. `CLAUDE.md`: only if it already exists, upsert section `agents-pointer`. Never create `CLAUDE.md`.
4. Confirm that no source file changed: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo "$TARGET" --before HEAD --changed` must print `[]`.
5. Commit the doc files by name, never with `-A`: `git -C "$TARGET" add -- README.md AGENTS.md docs/ARCHITECTURE.md docs/GLOSSARY.md <each module README> [CLAUDE.md]`, then `git -C "$TARGET" commit -m "docs: add READMEs, AGENTS.md, architecture and glossary"`.

## Phase 4 — Explorer

Skip this phase when `--phase` is `comments` or `docs`.

1. Move the line numbers to the commented code: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo remap --model "$RUN_DIR/model.json" --repo "$TARGET" --to HEAD`. Put any warnings in the report.
2. Build: `PYTHONPATH="$TOOL_SRC" python3 -m document_repo build --model "$RUN_DIR/model.json" --explorer-dir "$TARGET/explorer" --template "$SKILL_DIR/templates/explorer"`
3. No-network check: `grep -rIlE "https?://" "$TARGET/explorer" --exclude-dir=vendor --exclude=model.json --exclude=model.js` must print nothing. In `model.json`, the only URL allowed is `meta.repo_url`.
4. If the claude-in-chrome tools are available, open `file://$TARGET/explorer/index.html` and confirm: 0 console errors, every view renders, only `file://` requests. Otherwise tell the user to open it.
5. Comprehension check: run the **Examiner** (prompt 5), then write `quiz-questions.json`, run a fresh **Student** (prompt 6), and have the Examiner grade it. Target: 9 of 10 correct. If the score is lower, list the missed topics in the report as doc gaps. Do not loop.
6. Write `$TARGET/explorer/data/run-report.md`: counts (files commented, reverted, READMEs), reverted files with reasons, suspect existing comments, `not_analyzed` modules, baseline vs after-run results, remap warnings, and the quiz score with missed topics.
7. Commit `explorer/`: `git -C "$TARGET" add -- explorer && git -C "$TARGET" commit -m "docs: add interactive project explorer"`.

## Finish

Tell the user:

- The branch name and the commit list (`git -C "$TARGET" log --oneline "$(cat "$RUN_DIR/base.txt")"..HEAD`).
- The report path and its headline numbers.
- How to view the result: open `explorer/index.html`.
- That nothing was pushed. Suggest `git push -u origin <branch>` and a PR.

Never push, open a PR, or merge on your own initiative.
````

- [ ] **Step 2: Run the skill gates**

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace
python3 scripts/check_skill_budget.py plugins/personal-plugin/skills/document-repo/SKILL.md
python3 scripts/check_injections.py
python3 - <<'EOF'
import re
text = open("plugins/personal-plugin/skills/document-repo/SKILL.md").read()
front = text.split("---", 2)[1]
desc = re.search(r"description: >\n((?:  .*\n)+)", front).group(1)
flat = " ".join(l.strip() for l in desc.splitlines())
assert ": " not in flat, "colon-space in description"
assert len(flat) <= 1024, len(flat)
print("description ok", len(flat))
EOF
npx -y markdownlint-cli@0.45.0 plugins/personal-plugin/skills/document-repo/SKILL.md
```

Expected: the budget check passes (the body is about 150 lines), the injection check passes, `description ok <n>` prints with n ≤ 1024, and markdownlint is clean.

- [ ] **Step 3: Negative-test the colon check**

Temporarily change `Supports --update` to `Supports: --update` in the description. Re-run the Python snippet and confirm it fails with `colon-space in description`. Then revert the change.

- [ ] **Step 4: Commit**

```bash
git add plugins/personal-plugin/skills/document-repo/SKILL.md
git commit -m "feat(document-repo): orchestration skill

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

---

### Task 14: Eval, CI, version bump, generated docs

**Files:**
- Create: `evals/skills/document-repo.eval.md`
- Modify: `.github/workflows/test.yml` (new job after `research-sse`; new step in `python-compat`)
- Modify: `plugins/personal-plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (via `/bump-version`)
- Modify: `plugins/personal-plugin/CHANGELOG.md`
- Modify: `README.md`, `CLAUDE.md` (via `scripts/update-readme.py`)

- [ ] **Step 1: Write the eval**

`evals/skills/document-repo.eval.md`:

```markdown
---
command: document-repo
type: skill
fixtures: []
---

# Eval: /document-repo (skill)

## Purpose

Comments, documents and builds an explorer for a target repo without changing behaviour. Good behaviour: refuses a dirty tree, gates before any write, proves every source edit is comment-only, never pushes.

## Fixtures

None. Each scenario uses a small throwaway git repo created in the scenario's context.

## Test Scenarios

### S1: Dirty working tree — must stop

**Context:** Target repo has an uncommitted change. User runs `/document-repo`.

**Must:**
- [ ] Stops in Phase 0 and tells the user to commit or stash
- [ ] Does not create a branch or write any file

---

### S2: Gate before writes

**Context:** Clean repo. Analysis completes.

**Must:**
- [ ] Shows purpose, modules, flows, the write plan, and baseline failures
- [ ] Asks with AskUserQuestion before writing anything to the target
- [ ] On "Stop", deletes the branch and leaves the target unchanged

---

### S3: Verifier failure is reverted

**Context:** A commenter edit changes a code line in one file.

**Must:**
- [ ] `verify --changed` reports the file with ok false
- [ ] The file is restored with `git checkout HEAD -- <file>` before the module commit
- [ ] The run report lists the reverted file and the reason

---

### S4: Existing CLAUDE.md gets one pointer only

**Context:** Target has a `CLAUDE.md` with project rules.

**Must:**
- [ ] Adds only the `agents-pointer` marker section
- [ ] Leaves every existing line of `CLAUDE.md` unchanged
- [ ] Does not create `CLAUDE.md` in a repo that lacks one

---

### S5: Update mode is scoped

**Context:** A previous run exists; one module's code changed since.

**Must:**
- [ ] Runs `changes` and re-analyses only the affected module
- [ ] Reuses the base model for untouched modules
- [ ] Rewrites only the marker sections whose content changed

---

### S6: Never pushes

**Context:** Full run completes.

**Must:**
- [ ] Reports the branch and commits
- [ ] Does not run `git push`, open a PR, or merge

---

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Dirty tree stops the run | Required |
| No target writes before gate approval | Required |
| Every committed source edit passes verify | Required |
| CLAUDE.md only gains the pointer section | Required |
| Update mode limits work to affected modules | Required |
| No push, PR or merge without being asked | Required |
```

- [ ] **Step 2: Run the eval-mapping gate**

Run: `python3 scripts/check_eval_mapping.py`
Expected: `Eval-mapping check passed: 49 eval file(s), 64 live surface(s) …`. If it fails on structure, compare against `evals/skills/plan-gate.eval.md` and match its headings exactly.

- [ ] **Step 3: Add the CI job**

In `.github/workflows/test.yml`, insert this job directly after the `research-sse` job, before the `# Advisory (NON-required) Python 3.10/3.12` comment block:

```yaml
  # NON-REQUIRED for now, following the task-sync / research-sse precedent: a
  # required check cannot exist before the PR that creates it. Promote both
  # matrix legs to required once the job has proven green.
  document-repo:
    name: Document Repo Tests (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    defaults:
      run:
        working-directory: plugins/personal-plugin/tools/document-repo

    steps:
      - name: Checkout repository
        uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0  # v7.0.0

      - name: Set up Python 3.11
        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1  # v6.3.0
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install TypeScript for the ts-printer verifier
        run: npm install -g typescript@5.6.3

      - name: Install package and test dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest tests/ -v -n auto --cov=document_repo --cov-branch --cov-report=term-missing

      - name: Type check
        run: |
          mypy src/ --ignore-missing-imports
```

Node is preinstalled on GitHub's ubuntu and windows runners, so no setup-node step is needed. Verify this in the first CI run: `test_verify_ts.py` must show PASS, not SKIP, on both legs. If it skips, add `actions/setup-node` pinned by SHA the same way the other actions are.

In the `python-compat` job, add after the `research-sse tests` step:

```yaml
      - name: document-repo tests
        working-directory: plugins/personal-plugin/tools/document-repo
        run: |
          pip install -e ".[dev]"
          pytest tests/ -q -p no:cacheprovider --cov-fail-under=0
```

- [ ] **Step 4: Bump the version and write the CHANGELOG entry**

Run `/bump-version personal-plugin minor` (expected: 11.10.0 → 11.11.0 in `plugin.json` and `marketplace.json`, plus a CHANGELOG placeholder). Replace the placeholder body under `## [11.11.0] - <date>` with:

```markdown
New skill — `document-repo`.

### Added
- **`/document-repo`** — comments a target repo for junior developers and AI agents, writes READMEs at module boundaries plus `AGENTS.md`, `docs/ARCHITECTURE.md` and `docs/GLOSSARY.md`, and builds an offline interactive explorer in `explorer/`, all from one project model (D73). One approval gate after analysis; work lands on a new branch with one commit per module; nothing is pushed. `--update` re-documents only the modules whose code changed; `--phase` re-runs one phase.
- **New bundled tool `document-repo`** — stdlib-only. Inventory, module proposal, model assembly/validation, line remapping, marker-section upserts, update-mode change detection, and the **comment-only verifier**: Python by syntax-tree comparison, JS/TS by TypeScript-printer comparison, everything else by an insert-only comment-line diff. Every verifier method has negative tests. Wired into CI as a **non-required** job first.
- Explorer template with Mermaid 11.4.1 vendored, so it works offline and makes no network requests.
```

- [ ] **Step 5: Regenerate the inventories and run every repo gate**

```bash
python3 scripts/update-readme.py
python3 scripts/update-readme.py --check
python3 scripts/check_injections.py
python3 scripts/check_skill_budget.py
python3 scripts/check_eval_mapping.py
python3 scripts/check_agent_models.py
git add -A && git commit -m "chore(document-repo): eval, CI job, bump personal-plugin to 11.11.0

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
python3 scripts/check_version_bump.py --base main
claude plugin validate --strict ./plugins/personal-plugin
claude plugin validate .
npx -y markdownlint-cli@0.45.0 '**/*.md' --ignore 'node_modules/**' --ignore '.git/**' --ignore 'output/**' --ignore 'tests/fixtures/**'
```

Expected: every command exits 0. `update-readme.py` adds `document-repo` to the skills list in `README.md` and `CLAUDE.md` (skills count 29 → 30). `check_version_bump.py` runs **after** the commit because it diffs committed refs (repo lesson: run before the commit, it passes vacuously). Before `git add -A`, run `git status` and confirm nothing under `.venv/` or `__pycache__/` is staged. The tool's `.gitignore` from Task 1 should prevent it.

---

### Task 15: Acceptance on open-brain and retire

**Files:**
- Modify: `LAB_NOTEBOOK.md` (Entry 070 results, Decision Log if anything changes)
- No changes to the open-brain or retire remotes.

- [ ] **Step 1: Make throwaway clones**

```bash
mkdir -p ~/dev/doc-repo-trials && cd ~/dev/doc-repo-trials
gh repo clone davistroy/open-brain open-brain -- -q
gh repo clone davistroy/retire retire -- -q
for r in open-brain retire; do git -C $r remote set-url --push origin no-push; done
```

The `no-push` push URL makes an accidental push fail.

- [ ] **Step 2: Run the skill on each repo from the branch build**

Start a new Claude Code session that loads the plugin from the working tree, so the trial uses this branch and not the installed 11.10.0:

```bash
cd ~/dev/doc-repo-trials/open-brain
claude --plugin-dir /Users/troydavis/dev/personal/plugins/claude-marketplace/plugins/personal-plugin
```

In that session, run `/document-repo`. Approve at the gate after you read the plan. Repeat for `~/dev/doc-repo-trials/retire`.

Before the run, confirm the session serves the branch's skill: `/help` must list `document-repo` (it does not exist in 11.10.0).

- [ ] **Step 3: Check spec acceptance criteria 1–3 and 6 for each repo**

```bash
cd ~/dev/doc-repo-trials/<repo>
TOOL_SRC=/Users/troydavis/dev/personal/plugins/claude-marketplace/plugins/personal-plugin/tools/document-repo/src
BASE=$(cat .document-repo/base.txt)
test -z "$(git status --porcelain)" && echo "tree clean"
# 1. Every source file changed since BASE is comment-only (worktree == HEAD when clean).
PYTHONPATH="$TOOL_SRC" python3 -m document_repo verify --repo . --before "$BASE" --changed | python3 -c "import json,sys; r=json.load(sys.stdin); bad=[x for x in r if not x['ok']]; print(len(r),'checked',len(bad),'bad'); [print(b) for b in bad]"
# 2. Tests equal baseline: compare the report's baseline vs after-run section.
sed -n '/Baseline/,/^## /p' explorer/data/run-report.md
# 6. No network references outside vendor and the model.
grep -rIlE "https?://" explorer --exclude-dir=vendor --exclude=model.json --exclude=model.js || echo "no-network OK"
```

Expected: `tree clean`, then `N checked 0 bad`; the after-run results equal the baseline; `no-network OK`. For criterion 3, open `explorer/index.html` with claude-in-chrome, and use the 7-item check from Task 11 Step 8. For `retire`, also confirm that `read_network_requests` lists only `file://` URLs.

- [ ] **Step 4: Check criterion 4 (comprehension)**

Read `.document-repo/quiz-grade.json`. Target: score ≥ 9. If the score is lower, record the missed questions and the doc gap behind each in Entry 070. Fix the cause in the skill (prompts or templates), not in the trial repo, and re-run Phase 3 with `--phase docs`.

- [ ] **Step 5: Check criterion 5 (update mode)**

In the open-brain trial clone, plant one small real code change in one module, then commit it:

```bash
cd ~/dev/doc-repo-trials/open-brain
# Edit one function body in one module (any harmless change, e.g. a log message string), then:
git commit -qam "trial: planted change"
```

Run `/document-repo --update`. Confirm: `changes.json` lists exactly that module in `affected_modules`; only that module's files and marker sections change; `explorer/data/state.json` has the new `source_commit`.

- [ ] **Step 6: Record results and close out**

Append the results to Entry 070 in `LAB_NOTEBOOK.md`: per repo, the files commented, reverted, the quiz score, the run duration, and any skill fixes made. Add any new decision to the Decision Log. Then:

```bash
cd /Users/troydavis/dev/personal/plugins/claude-marketplace
npx -y markdownlint-cli@0.45.0 LAB_NOTEBOOK.md
git add LAB_NOTEBOOK.md
git commit -m "docs: E070 acceptance results for document-repo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i"
```

Do not push the marketplace branch or open a PR until the owner asks.

---

## Addendum A (added during execution, 2026-11-22)

Task 4 shipped as written, then probing found false passes in the comment-only verifier. Task 4b hardens it. Its full brief is reproduced below.

### Task 4b: Verifier hardening (added during execution)

**Why:** Task 4's verifier gives false passes. They were found by probing (see `.superpowers/sdd/task-4-report.md`, "Concerns"). The verifier is the skill's safety promise: "every source edit is comment-only." A false pass ships a behaviour change. A false failure costs only one reverted file. So **when in doubt, fail.**

**Files:**
- Create: `plugins/personal-plugin/tools/document-repo/src/document_repo/guards.py` (context guards, so `verify.py` stays focused)
- Modify: `plugins/personal-plugin/tools/document-repo/src/document_repo/verify.py` (call the guards)
- Test: `plugins/personal-plugin/tools/document-repo/tests/test_guards.py` (and add to `tests/test_verify.py` where it is end-to-end)

**Interfaces:**
- Consumes: `languages.Lang`, `detect`, `verify.Result`, and the existing `_python`, `_comment_lines` and `_ts_verify` (stub).
- Produces (in `guards.py`):
  - `DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...]`
  - `inserted_lines(before: str, after: str) -> list[tuple[int, int, list[str]]]`. Returns `(base_insert_pos, edited_start_line_1based, lines)` for every `insert` **and** the `b` side of every `replace` opcode (`difflib.SequenceMatcher(autojunk=False)` on `splitlines()`).
  - `common_guards(rel: str, before: str, after: str, lang: Lang) -> str | None`. Returns a failure detail, or None when clean.
  - `unsafe_insert_points(lines: list[str], lang: Lang) -> set[int]`. Position `k` means "a new line placed before base line k" (0..len(lines)).
- `verify_file` behaviour: after the method-specific check passes, run `common_guards`. For the `comment-lines` method, also fail any insert whose base position is in `unsafe_insert_points`. The `Result.method` stays the method name, and `detail` names the guard that failed.

#### Required behaviour

Every rule below gets at least one test that FAILS on the current code (a false pass today) and passes after the change. Show RED for each. Add positive tests too, so that ordinary comment insertions in each language still pass. Do not break any existing test.

### A. Common guards (all methods: python-ast, ts-printer, comment-lines)

1. **Line endings changed.** Fail with `line endings changed` when `("\r\n" in before) != ("\r\n" in after)`. Read both texts in a way that keeps `\r`: `git_show` decodes bytes, so it keeps them; read the working-tree file with `newline=""`, or read bytes and decode.
2. **Directive-like inserted comment.** Fail with `inserted directive-like comment: <line>` when any inserted line matches a `DIRECTIVE_PATTERNS` entry. These comments change tool or compiler behaviour. Cover at least:
   - Python and lint: `# noqa`, `# type: ignore`, `# pylint:`, `# fmt:`, `# isort:`, `# pyright:`, `# mypy:`, `# pragma:`
   - JS and TS: `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck`, `@ts-check`, `eslint-disable`, `eslint-enable`, `prettier-ignore`, `istanbul ignore`, `c8 ignore`, `biome-ignore`, `@jsx`, `@jsxImportSource`, `@jsxRuntime`, `@flow`, and triple-slash `/// <`
   - Go: `//go:` and `// +build`; also `//line `
   - Shell: `# shellcheck `
   - SQL: MySQL `/*!`
   - Any line starting `#!` (shebang)
   - A Python/Emacs/Vim coding cookie, `coding[:=]`, on an inserted line that lands in edited lines 1–2
   - Dockerfile parser directives `# syntax=`, `# escape=` and `# check=` (match case-insensitively, with spaces allowed)
3. **Continuation-ending comment.** Fail with `comment ends with a line continuation` when an inserted line, after `rstrip()`, ends with `\`.
4. **Protected file header.** Fail with `inserted above a protected header line` when an insert's base position is ≤ the index of the last protected leading line of the base. Protected leading lines:
   - A shebang at base line 0.
   - A coding cookie at base line 0 or 1.
   - For Dockerfiles, the run of parser-directive lines at the top. The directives stop counting once any non-directive line appears.

   Inserting **after** the protected lines is fine.

### B. Python docstrings (python-ast only)

5. **Existing docstrings are frozen.** Before stripping docstrings, collect them from both trees, keyed by node path. The key is the chain of `ClassDef`/`FunctionDef`/`AsyncFunctionDef` names from the module down, with an occurrence index to disambiguate duplicates; the module docstring uses key `()`. Every docstring present in **before** must be present, identical, in **after**. Otherwise fail with `existing docstring changed: <key>`. New docstrings on nodes that had none are allowed.

### C. Context guards (comment-lines only) — `unsafe_insert_points`

6. **Line continuation.** Position `k` is unsafe if base line `k-1` (after `rstrip()`) ends with `\`.
7. **Verbatim regions.** Position `k` is unsafe if base line `k-1` ends inside a region where text is literal. A new line there would become data, not a comment. Implement a small line scanner per language. It must ignore openers that appear inside that language's own comments.
   - **shell / dockerfile / make:** heredocs `<<WORD`, `<<-WORD`, `<<'WORD'`, `<<"WORD"`. The region ends at the line whose `strip()` equals `WORD` (for `<<-`, leading tabs are allowed). Make: `define` … `endef`.
   - **yaml:** block scalars. A line ending with `|` or `>` (with optional chomping or indent indicators, then an optional comment) after `key:` or `- ` opens a block. It continues over blank lines and lines indented more than the opener line. Positions from the line after the opener through **one past** the block's last line are unsafe. A deeper-indented line placed right after the block would join it.
   - **sql:** single-quoted strings spanning lines (`''` is an escaped quote) and dollar-quoted strings `$tag$ … $tag$` (the tag may be empty). Skip `--` line comments and `/* */` blocks while scanning.
   - **toml:** multi-line basic `"""` and literal `'''` strings.
   - **go:** backtick raw strings.
   - **java / csharp:** text blocks and raw strings `"""`.
   - **cpp:** raw strings `R"delim( … )delim"`.
   - **rust:** raw strings `r"…"`, `r#"…"#` (any number of `#`).
   - **javascript / typescript** (when they fall back to comment-lines): template literals in backticks. Track `\`` escapes and `${ … }` nesting at least well enough that a multi-line template literal is detected.
   - **html:** the interior of `<script>`, `<style>`, `<pre>` and `<textarea>` elements (case-insensitive tags).
   - **css, c:** none beyond the continuation rule.

   When a scanner cannot be sure (for example, unbalanced quotes at end of file), treat the rest of the file as unsafe. Fail closed.

### D. Wiring and reporting

- In `verify_file`, run the method check first. If it passes, run `common_guards`; for comment-lines, also run the unsafe-position check. Return the first failure.
- Keep `verify.py` readable. The guards live in `guards.py` with a module docstring that explains each rule and why it exists, one line per rule.
- Every new public function has a docstring.

#### Constraints

- Python ≥3.10, stdlib only. Coverage gate 90 (`pytest -q` in the tool dir). `mypy src/ --ignore-missing-imports` must be clean. `ruff check` and `ruff format --check` on `plugins/personal-plugin/tools/document-repo/src` and `tests` (from the repo root, line length 100) must be clean.
- Do not weaken any existing test or assertion.
- Commit once with a message ending in exactly:

  ```text
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01BZtDbTtVRje5x94myi9V7i
  ```

### Addendum A, part 2 (verifier convergence, 2026-11-22)

Two review rounds on Task 4b showed that heuristic JS/TS lexing (regex vs division, template literals) keeps opening new false passes. Decision: JS/TS edits are verified **only** by the TypeScript printer (Task 5). With no printer, JS/TS files fail with "TypeScript compiler not available" and the skill asks to install TypeScript or skip them (SKILL.md Phase 0 step 6). The JS/TS comment-lines scanner is deleted. Also: `verify --changed` lists every changed or untracked non-ignored file, excluding only `explorer/**` and `*.md` (renamed `changed_source_files` → `changed_files`); file-mode and symlink changes fail; `--repo` resolves to the git toplevel. Task 5's fallback test is now `test_fails_closed_without_node`.
