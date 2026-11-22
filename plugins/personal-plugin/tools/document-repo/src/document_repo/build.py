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
from urllib.parse import urlsplit

from .schema import SCHEMA_VERSION, validate

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
_REPO_PATH = re.compile(r"[^\s@?#\\]+")
_WEB_SCHEMES = ("http", "https")
_SSH_SCHEMES = ("ssh", "git", "git+ssh", "ssh+git")


def normalize_remote(url: str | None) -> str | None:
    """Browsable https URL for a git remote, with any credentials removed.

    Returns None for anything that is not a remote on a named host (a local path, a ``file://``
    URL), and also when the URL cannot be split into host and path without guessing. Guessing is
    the privacy risk: a password containing ``/`` or ``@`` moves the boundary between credentials
    and host, so a loose pattern can leave part of a secret in the result. Userinfo, query and
    fragment are never copied. The scheme becomes https, and an SSH port is dropped because it is
    not the web port.
    """
    if not url:
        return None
    url = url.strip()
    port = ""
    if "://" in url:
        try:
            parts = urlsplit(url)
            host = parts.hostname
            web_port = parts.port
        except ValueError:
            return None
        scheme = parts.scheme.lower()
        if scheme in _WEB_SCHEMES and web_port is not None:
            port = f":{web_port}"
        elif scheme not in _WEB_SCHEMES + _SSH_SCHEMES:
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
    return f"https://{host.lower()}{port}/{path}"


def _git(repo: Path, *args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


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
    final = read_object(final_path, "modules")["modules"]
    if not isinstance(final, list) or not all(
        isinstance(spec, dict)
        and isinstance(spec.get("id"), str)
        and isinstance(spec.get("path"), str)
        for spec in final
    ):
        raise ValueError(f"{final_path}: modules must be a list of objects with string id and path")
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
    base_modules = {m["id"]: m for m in (base_model or {}).get("modules", [])}
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
        "repo_name": Path(top).name if top else repo.resolve().name,
        "repo_url": normalize_remote(_git(repo, "remote", "get-url", "origin")),
    }
    parts: dict[str, Any] = {
        "meta": meta,
        "modules": sorted(modules, key=lambda m: m["id"]),
        **{k: system[k] for k in SYSTEM_KEYS},
    }
    return {k: parts[k] for k in MODEL_KEY_ORDER}, notes


def write_explorer_data(model: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Validate, then write model.json, model.js and state.json into ``out_dir``."""
    errors = validate(model)
    if errors:
        raise ValueError("model is invalid:\n" + "\n".join(errors))
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(model, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "model.json").write_text(canonical, encoding="utf-8")
    (out_dir / "model.js").write_text(
        JS_PREFIX + json.dumps(model, ensure_ascii=False) + ";\n", encoding="utf-8"
    )
    state = {
        "source_commit": model["meta"]["source_commit"],
        "schema_version": SCHEMA_VERSION,
        "model_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "generated_at": model["meta"]["generated_at"],
    }
    (out_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state


def install_template(template_dir: Path, explorer_dir: Path) -> None:
    """Copy the fixed explorer app into the target, never touching data/.

    Only the top-level ``data/`` is skipped: it holds the target's own model, and a ``data``
    directory deeper in the app (inside a vendored library, say) is part of the app.
    """

    def skip_top_level_data(directory: str, names: list[str]) -> set[str]:
        return {"data"}.intersection(names) if Path(directory) == template_dir else set()

    shutil.copytree(template_dir, explorer_dir, dirs_exist_ok=True, ignore=skip_top_level_data)
