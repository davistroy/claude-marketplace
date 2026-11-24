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
import os
import re
import shutil
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .fsutil import write_bytes_atomic
from .inventory import OUTPUT_DIR
from .schema import ID_HINT, ID_PATTERN, SCHEMA_VERSION, validate

SYSTEM_KEYS = ("project", "architecture", "flows", "glossary", "paths", "agent_notes")
MODEL_KEY_ORDER = (
    "meta",
    "project",
    "architecture",
    "modules",
    "flows",
    "glossary",
    "paths",
    "agent_notes",
)
JS_PREFIX = "window.PROJECT_MODEL = "


# user@host:path, the scp-like form git accepts for SSH. The user part is required so a Windows
# path such as C:\repo is not mistaken for a host.
_SCP_REMOTE = re.compile(r"[^@/:\s]+@(?P<host>[^@/:\s]+):(?P<path>\S+)")
_HOST = re.compile(r"[A-Za-z0-9._-]+")
# No lone surrogates: ``_git`` decodes with surrogateescape, so a remote whose bytes are not UTF-8
# arrives as one, and a URL that cannot be encoded is not a link the explorer can use.
_REPO_PATH = re.compile(r"[^\s@?#\\\ud800-\udfff]+")
_SURROGATE = re.compile(r"[\ud800-\udfff]")
_WEB_SCHEMES = ("http", "https")
_SSH_SCHEMES = ("ssh", "git", "git+ssh", "ssh+git")


def normalize_remote(url: str | None) -> str | None:
    """Browsable URL for a git remote, with any credentials removed.

    Returns None for anything that is not a remote on a named host (a local path, a ``file://``
    URL), and also when the URL cannot be split into host and path without guessing. Guessing is
    the privacy risk: a password containing ``/`` or ``@`` moves the boundary between credentials
    and host, so a loose pattern can leave part of a secret in the result. Userinfo, query and
    fragment are never copied. An ``http://`` remote stays http, with its port (a forge on
    ``localhost:3000`` has no TLS). SSH, ``git://`` and scp-style remotes become https and lose the
    port, which is not the web port.
    """
    if not url:
        return None
    url = url.strip()
    port = ""
    web_scheme = "https"
    if "://" in url:
        try:
            parts = urlsplit(url)
            host = parts.hostname
            web_port = parts.port
        except ValueError:
            return None
        scheme = parts.scheme.lower()
        if scheme in _WEB_SCHEMES:
            web_scheme = scheme
            if web_port is not None:
                port = f":{web_port}"
        elif scheme not in _SSH_SCHEMES:
            return None
        # A "/", "?" or "#" in a password ends the authority early and pushes the "@" into the
        # path, query or fragment. Any "@" outside the authority means the split is a guess.
        if "@" in parts.path + parts.query + parts.fragment:
            return None
        path = parts.path
    else:
        scp = _SCP_REMOTE.fullmatch(url)
        if scp is None:
            return None
        host, path = scp.group("host"), scp.group("path")
    path = path.strip("/").removesuffix(".git").strip("/")
    if not host or not _HOST.fullmatch(host) or not _REPO_PATH.fullmatch(path):
        return None
    return f"{web_scheme}://{host.lower()}{port}/{path}"


def _git(repo: Path, *args: str) -> str | None:
    # Bytes decoded with surrogateescape, as in verify.py: a path or remote that is not UTF-8
    # must not raise. text=True would raise UnicodeDecodeError.
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "surrogateescape").strip()


def _printable(text: str) -> str:
    """Replace lone surrogates (non-UTF-8 bytes from ``_git`` or the file system) with U+FFFD."""
    return _SURROGATE.sub("\ufffd", text)


def _stub(spec: dict[str, Any]) -> dict[str, Any]:
    note = "Not analyzed. The analysis agent failed twice for this module."
    return {
        "id": spec["id"],
        "name": spec["path"],
        "path": spec["path"],
        "status": "not_analyzed",
        "purpose": {"functional": note, "technical": note},
        "interface": [],
        "invariants": [],
        "dependencies": {"internal": [], "external": []},
        "key_files": [],
    }


def read_json(path: Path) -> Any:
    """Parse a JSON file. A syntax or encoding error becomes a ValueError that names the file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError
        raise ValueError(f"{path}: {exc}") from exc


def read_object(path: Path, *required: str) -> dict[str, Any]:
    """Parse a JSON file that must hold an object with every key in ``required``."""
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{path}: missing {', '.join(missing)}")
    return data


def _module_entries(modules: Any, where: str, *, with_path: bool = False) -> list[dict[str, Any]]:
    """Check a list of module entries, ids included, and return it.

    A module id becomes a file name (``modules/<id>.json``), so a value such as ``../x`` or
    ``/etc/passwd`` has to be refused before any path is built from it.
    """
    shape = "string id and path" if with_path else "a string id"
    if not isinstance(modules, list) or not all(
        isinstance(entry, dict)
        and isinstance(entry.get("id"), str)
        and (not with_path or isinstance(entry.get("path"), str))
        for entry in modules
    ):
        raise ValueError(f"{where}: modules must be a list of objects with {shape}")
    for entry in modules:
        if not ID_PATTERN.fullmatch(entry["id"]):
            raise ValueError(f"{where}: invalid module id {entry['id']!r} ({ID_HINT})")
    return modules


def assemble_model(
    run_dir: Path, repo: Path, base_model: dict[str, Any] | None = None, now: str | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Join module records and system sections into one model.

    Module precedence: a fresh record in run_dir/modules, then the module from
    ``base_model`` (update mode), then a ``not_analyzed`` stub.

    Raises ValueError, naming the file, when a run file is unreadable or has the wrong shape.
    That is a different failure from an invalid model: the caller can still write and validate
    a model, but not build one.
    """
    final_path = run_dir / "modules.final.json"
    final = _module_entries(
        read_object(final_path, "modules")["modules"], str(final_path), with_path=True
    )
    base_modules: dict[str, dict[str, Any]] = {}
    if base_model is not None:
        if "modules" not in base_model:
            raise ValueError("base model: missing modules")
        base_modules = {m["id"]: m for m in _module_entries(base_model["modules"], "base model")}
    system_path = run_dir / "system.json"
    if system_path.exists():
        system = read_object(system_path, *SYSTEM_KEYS)
    elif base_model is not None:
        absent = [key for key in SYSTEM_KEYS if key not in base_model]
        if absent:
            raise ValueError(f"base model: missing {', '.join(absent)}")
        system = base_model
    else:
        raise ValueError(f"{system_path} is missing and no base model was given")
    modules: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    for spec in final:
        record_path = run_dir / "modules" / f"{spec['id']}.json"
        if record_path.exists():
            record = read_object(record_path, "module")
            module = record["module"]
            if not isinstance(module, dict) or module.get("id") != spec["id"]:
                raise ValueError(f"{record_path}: module.id must be {spec['id']!r}")
            files = record.get("files", [])
            if not isinstance(files, list):
                raise ValueError(f"{record_path}: files must be a list")
            modules.append(module)
            notes.extend(files)
        elif spec["id"] in base_modules:
            modules.append(base_modules[spec["id"]])
        else:
            modules.append(_stub(spec))
    top = _git(repo, "rev-parse", "--show-toplevel")
    meta = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_commit": _git(repo, "rev-parse", "HEAD") or "",
        "repo_name": _printable(Path(top).name if top else repo.resolve().name),
        "repo_url": normalize_remote(_git(repo, "remote", "get-url", "origin")),
    }
    parts: dict[str, Any] = {
        "meta": meta,
        "modules": sorted(modules, key=lambda m: m["id"]),
        **{k: system[k] for k in SYSTEM_KEYS},
    }
    return {k: parts[k] for k in MODEL_KEY_ORDER}, notes


#: The files ``write_explorer_data`` writes into ``explorer/data/``, and the keys of its state.
MODEL_FILE = "model.json"
MODEL_JS_FILE = "model.js"
STATE_FILE = "state.json"
DATA_FILES = (MODEL_FILE, MODEL_JS_FILE, STATE_FILE)
STATE_KEYS = frozenset({"source_commit", "schema_version", "model_hash", "generated_at"})


def write_explorer_data(model: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Validate, then write model.json, model.js and state.json into ``out_dir``.

    Every payload is encoded to bytes before the first file is touched, so text that cannot be
    encoded (a lone surrogate) raises ValueError and writes nothing. The files are written as
    bytes, never in text mode, which would turn each newline into CRLF on Windows and make
    ``model_hash`` differ from the hash of the file on disk. Each file is replaced atomically, but
    the three replacements are not one transaction: a failure after the first leaves that file new
    and the rest old.

    ``model.js`` is ASCII (``ensure_ascii``): a ``<script src>`` over ``file://`` is decoded with
    whatever charset the page declares, and a raw U+2028 or U+2029 inside a string literal is a
    syntax error before ES2019. ``model.json`` keeps the text as written.
    """
    errors = validate(model)
    if errors:
        raise ValueError("model is invalid:\n" + "\n".join(errors))
    try:
        model_json = _model_json_bytes(model)
        model_js = (JS_PREFIX + json.dumps(model, ensure_ascii=True) + ";\n").encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"model cannot be encoded as UTF-8: {exc}") from exc
    state: dict[str, Any] = {
        "source_commit": model["meta"]["source_commit"],
        "schema_version": SCHEMA_VERSION,
        "model_hash": hashlib.sha256(model_json).hexdigest(),
        "generated_at": model["meta"]["generated_at"],
    }
    state_json = (json.dumps(state, indent=2) + "\n").encode("utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_bytes_atomic(out_dir / MODEL_FILE, model_json)
    write_bytes_atomic(out_dir / MODEL_JS_FILE, model_js)
    write_bytes_atomic(out_dir / STATE_FILE, state_json)
    return state


#: The explorer app the skill installs. The tool always runs from the plugin's source tree
#: (``PYTHONPATH=<plugin>/tools/document-repo/src``), so the template sits at a fixed place
#: beside it. ``verify.is_exempt`` reads its file list from here.
TEMPLATE_DIR = Path(__file__).resolve().parents[4] / "skills/document-repo/templates/explorer"

#: The directory inside the explorer that holds the model, its state and the run report. It is
#: never copied from the template.
DATA_DIR = "data"


def template_files(template_dir: Path) -> frozenset[str]:
    """Every file ``install_template`` copies, relative to the explorer directory, "/"-separated.

    This is the one list of the app's own files: the install copies exactly these, and
    ``verify.is_exempt`` exempts exactly these (plus the ``DATA_FILES``) in an explorer a build
    made. A missing template lists nothing, so no app file is exempt and every one is judged.
    """
    found: set[str] = set()
    for directory, dirs, files in os.walk(template_dir, followlinks=True):
        if Path(directory) == template_dir and DATA_DIR in dirs:
            dirs.remove(DATA_DIR)
        rel_dir = Path(directory).relative_to(template_dir)
        found.update((rel_dir / name).as_posix() for name in files)
    return frozenset(found)


#: The report Phase 4 of the skill writes into ``explorer/data/``. ``build`` does not write it.
RUN_REPORT_FILE = "run-report.md"


def explorer_output(template_dir: Path) -> list[str]:
    """Every path a run puts under ``explorer/``, relative to the repo root, sorted.

    The app's own files (``template_files``), the three ``DATA_FILES`` and the run report. The
    list does not depend on what exists: ``explorer-status`` asks git about these paths before
    any of them is written, to warn when an ignore rule would keep them out of the commit.
    """
    names = template_files(template_dir) | {
        f"{DATA_DIR}/{name}" for name in (*DATA_FILES, RUN_REPORT_FILE)
    }
    return sorted(f"{OUTPUT_DIR}/{name}" for name in names)


#: The file ``keep-local`` writes in the explorer directory, and the header it starts with. It
#: is a gitignore file: the header and the rule lines are comments, the last line is ``*``, so
#: every file in the explorer is ignored (an untracked app file would otherwise fail the final
#: backstop, and the stray rules would delete it). The rule lines record which rules of the
#: owner's made it necessary, because once this file exists ``git check-ignore`` only sees ``*``.
LOCAL_MARKER = ".gitignore"
MARKER_HEADER = (
    "# document-repo: this explorer is kept local and is never committed. Rules that ignore it:"
)
#: A marker is a few hundred bytes; a bigger file is not one and is never read whole.
MARKER_SIZE_CAP = 64 << 10


def marker_text(rules: list[str]) -> str:
    """The marker file for these rules, each ``source:line:pattern`` as ``check-ignore -v`` says."""
    return "\n".join([MARKER_HEADER, *(f"# {rule}" for rule in rules), "*", ""])


def parse_marker(text: str) -> list[str] | None:
    """The rules ``text`` records, or None unless ``text`` is exactly what ``marker_text`` makes.

    Fail closed: a file that is nearly the marker, or that adds a line to it (a negation, say),
    is somebody else's ignore file.
    """
    lines = text.split("\n")
    if len(lines) < 3 or lines[0] != MARKER_HEADER or lines[-2:] != ["*", ""]:
        return None
    rules = lines[1:-2]
    if not all(line.startswith("# ") for line in rules):
        return None
    return [line[2:] for line in rules]


def read_marker(explorer_dir: Path) -> list[str] | None:
    """The rules recorded in ``explorer_dir``'s marker, or None when there is no marker.

    A symlink, a directory, a file over ``MARKER_SIZE_CAP`` or any other content is not one.
    """
    path = explorer_dir / LOCAL_MARKER
    if not _regular_file(path):
        return None
    try:
        if path.lstat().st_size > MARKER_SIZE_CAP:
            return None
        return parse_marker(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError):
        return None


def write_marker(explorer_dir: Path, rules: list[str]) -> None:
    """Write the marker atomically. ``OSError`` when the directory cannot be written."""
    write_bytes_atomic(explorer_dir / LOCAL_MARKER, marker_text(rules).encode("utf-8"))


def _regular_file(path: Path) -> bool:
    """True when ``path`` is a regular file, not a symlink."""
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False


def _real_directory(path: Path) -> bool:
    try:
        return stat.S_ISDIR(path.lstat().st_mode)
    except OSError:
        return False


def _model_json_bytes(model: Any) -> bytes:
    """``model.json`` exactly as ``write_explorer_data`` writes it, and ``model_hash`` hashes."""
    return (json.dumps(model, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


#: A ``model.json`` larger than this is never parsed to check ownership; only its raw hash can
#: match. ``build`` writes models of a few MB; a parse costs 15 to 20 times the file size in
#: memory, and the tool's ceiling is 1.5 GB per process.
CANONICAL_PARSE_CAP = 64 << 20
#: A build's ``state.json`` is about 250 bytes; a bigger file is not one.
STATE_SIZE_CAP = 64 << 10
_HASH_CHUNK = 1 << 20


def _build_state(data: Path) -> dict[str, Any] | None:
    """``data/state.json`` when it has a build's shape (exactly ``STATE_KEYS``), else None."""
    path = data / STATE_FILE
    try:
        if path.lstat().st_size > STATE_SIZE_CAP:
            return None
        state = json.loads(path.read_bytes())
    except (OSError, ValueError, RecursionError):
        return None
    if not (isinstance(state, dict) and set(state) == STATE_KEYS):
        return None
    return state if isinstance(state["model_hash"], str) else None


def _raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_HASH_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_our_explorer(explorer_dir: Path) -> bool:
    """True when ``explorer_dir`` was made by ``build``, judged by content, not by a file name.

    A build leaves ``data/state.json`` as a JSON object with exactly ``STATE_KEYS``, whose
    ``model_hash`` is the sha256 of ``data/model.json`` as the build serialised it. A target's
    own ``state.json`` (UI state for an app that happens to be called "explorer") does not have
    that shape. The checks run cheapest first, so a foreign directory costs almost nothing
    however big its files are:

    1. ``state.json`` must have a build's shape (and be under ``STATE_SIZE_CAP``).
    2. The raw bytes of ``model.json``, hashed in 1 MiB chunks, match: a clean checkout.
    3. Otherwise, and only for a ``model.json`` under ``CANONICAL_PARSE_CAP``, the model parsed
       and serialised again as ``build`` writes it matches. This keeps a CRLF checkout (Git for
       Windows' ``core.autocrlf``) or a commit hook that re-indents JSON ours. A change to the
       model's values or key order, or a file that does not parse, does not match.

    The directory, ``data/``, ``state.json`` and ``model.json`` must be real (no symlinks), so
    the check reads the files the commit holds and not something they point at. Anything else is
    not ours: every file in the directory is then judged, and ``build`` refuses it.
    """
    data = explorer_dir / DATA_DIR
    if not (_real_directory(explorer_dir) and _real_directory(data)):
        return False
    if not (_regular_file(data / STATE_FILE) and _regular_file(data / MODEL_FILE)):
        return False
    state = _build_state(data)
    if state is None:
        return False
    model = data / MODEL_FILE
    try:
        if _raw_sha256(model) == state["model_hash"]:
            return True
        if model.lstat().st_size > CANONICAL_PARSE_CAP:
            return False
        canonical = _model_json_bytes(json.loads(model.read_bytes()))
    except (OSError, ValueError, RecursionError):
        return False
    return bool(hashlib.sha256(canonical).hexdigest() == state["model_hash"])


def foreign_files(template_dir: Path, explorer_dir: Path) -> list[str]:
    """Paths in ``explorer_dir`` a build would not have put there, relative to it, "/"-separated.

    Any symlink is foreign (``"."`` for the directory itself): the install would write through
    it, and the checks would read past it. In ``data/`` only the ``DATA_FILES`` and Markdown (the
    run report) belong, and only in an explorer a build made. Outside ``data/``, an explorer a
    build made may hold any app file (an older template's, say); any other explorer may hold
    only files byte-identical to the template's, as a half-finished install leaves them. A
    target's own ``explorer/app.js`` is foreign by its bytes, whatever its name.
    """
    if not os.path.lexists(explorer_dir):
        return []
    if not _real_directory(explorer_dir):
        return ["."]
    ours = is_our_explorer(explorer_dir)
    installed = template_files(template_dir)
    foreign = []
    for directory, dirs, files in os.walk(explorer_dir):
        here = Path(directory)
        rel_dir = here.relative_to(explorer_dir)
        for name in [*dirs, *files]:
            if (here / name).is_symlink():
                foreign.append((rel_dir / name).as_posix())
        dirs[:] = [d for d in dirs if not (here / d).is_symlink()]
        for name in files:
            path = here / name
            rel = (rel_dir / name).as_posix()
            if path.is_symlink():
                continue
            if rel == LOCAL_MARKER and read_marker(explorer_dir) is not None:
                continue  # what ``keep-local`` wrote: the skill's own, even in a partial build
            if rel_dir.parts[:1] == (DATA_DIR,):
                ok = ours and (
                    len(rel_dir.parts) == 1 and (name in DATA_FILES or name.lower().endswith(".md"))
                )
            elif ours:
                ok = True
            else:
                ok = rel in installed and path.read_bytes() == (template_dir / rel).read_bytes()
            if not ok:
                foreign.append(rel)
    return sorted(foreign)


def _looks_like_a_partial_build(explorer_dir: Path, foreign: list[str]) -> bool:
    """True when every foreign path is a file a build writes and ``state.json`` is a build's.

    That is what ``write_explorer_data`` leaves when it stops after replacing ``model.json``:
    the old ``state.json`` no longer matches, so the directory is not ours, but nothing in it is
    the repository's own.
    """
    names = template_files(TEMPLATE_DIR) | {f"{DATA_DIR}/{n}" for n in DATA_FILES}
    return _build_state(explorer_dir / DATA_DIR) is not None and set(foreign) <= names


def ensure_installable(template_dir: Path, explorer_dir: Path) -> None:
    """Raise ``ValueError`` unless ``build`` may write into ``explorer_dir``.

    ``foreign_files`` must be empty. Otherwise the directory holds the target's own code, a file
    that would ride into the commit unjudged, or a symlink a write would go through. ``build``
    runs this before it writes anything, with or without ``--template``: writing the data alone
    into a foreign directory would make its marker valid and every template-named file in it
    exempt. Each case has its own message, so the agent can tell a partial build (retry after
    restoring) from the repository's own files (stop and ask).
    """
    foreign = foreign_files(template_dir, explorer_dir)
    if not foreign:
        return
    if foreign == ["."]:
        what = "a symlink" if os.path.islink(explorer_dir) else "not a directory"
        raise ValueError(
            f"{explorer_dir} is {what}; build writes only into a real directory. "
            "Move it aside, then run again"
        )
    links = [f for f in foreign if os.path.islink(explorer_dir / f)]
    if links:
        raise ValueError(
            f"{explorer_dir} holds symlinks, which build never follows or writes through: "
            f"{', '.join(links)}. Move them aside, then run again"
        )
    if _looks_like_a_partial_build(explorer_dir, foreign):
        # Every file of a kept-local explorer is ignored, and ``git clean`` skips ignored files
        # unless given ``-x``.
        local = read_marker(explorer_dir) is not None
        clean = "git clean -fdqx -- explorer" if local else "git clean -fdq -- explorer"
        note = " (explorer/ is kept local, so its files are ignored)" if local else ""
        raise ValueError(
            f"{explorer_dir} looks like a build that stopped partway: data/state.json is a "
            f"build's, but these no longer match it: {', '.join(foreign)}. Restore what is "
            f"committed with `{clean}`{note}, then `git checkout HEAD -- explorer` "
            "if HEAD has an explorer/ (a first run's does not), and build again"
        )
    raise ValueError(
        f"{explorer_dir} was not made by document-repo, or holds what a build does not write: "
        f"{', '.join(foreign)}. These may be the repository's own files: move them aside, "
        "then run again"
    )


def install_template(template_dir: Path, explorer_dir: Path) -> None:
    """Copy the fixed explorer app into the target, never touching data/.

    Only the top-level ``data/`` is skipped: it holds the target's own model, and a ``data``
    directory deeper in the app (inside a vendored library, say) is part of the app. Refuses with
    ``ValueError``, touching nothing, unless ``ensure_installable`` passes.
    """
    ensure_installable(template_dir, explorer_dir)

    def skip_top_level_data(directory: str, names: list[str]) -> set[str]:
        return {DATA_DIR}.intersection(names) if Path(directory) == template_dir else set()

    shutil.copytree(template_dir, explorer_dir, dirs_exist_ok=True, ignore=skip_top_level_data)
