"""The project model contract, and a validator for it.

The model (explorer/data/model.json) is the single source of truth for a run:
comments, READMEs, AGENTS.md and the explorer are all written from it. This
file defines its exact shape. ``references/model-schema.md`` explains what
each field should contain; this file decides what is valid.

Spec notation: a dict is an object (a key ending in "?" is optional, and any key
the spec does not name is an error), a one-item list is "array of", a type is
"instance of", ``OneOf`` is an enum, ``IdStr`` is an id slug, ``LineNo`` is a
1-based line number, and ``NULLABLE_STR`` allows a string or null.
"""

from __future__ import annotations

import re
from typing import Any

SCHEMA_VERSION = 1
MAX_SNIPPET_LINES = 30

# What ``modules.slug()`` produces, including its de-duplication suffix (``-2``). ``fullmatch``,
# not ``^...$``: ``$`` would also accept a trailing newline.
_ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
ID_HINT = "lowercase letters, digits and single hyphens"
DOC_HINT = "expected a relative POSIX path: no leading '/', no '..' segment, no backslash, no NUL"


class OneOf:
    """Spec node: the value must be one of a fixed set of strings (an enum)."""

    def __init__(self, *values: str) -> None:
        self.values = list(values)

    def __repr__(self) -> str:
        return f"OneOf({', '.join(map(repr, self.values))})"


class IdStr:
    """Spec node: a string id, lowercase letters and digits joined by single hyphens.

    Ids become file names, URL fragments and diagram node names downstream, so anything
    else (``../x``, ``a/b``, an empty string, uppercase) is rejected here, once.
    """


class LineNo:
    """Spec node: a 1-based line number, so an int of at least 1 (and not a bool)."""


ID = IdStr()
LINE = LineNo()
NULLABLE_STR = (str, type(None))
LENS = {"functional": str, "technical": str}
LABELLED_COMMAND = {"label": str, "command": str}

SPEC: dict[str, Any] = {
    "meta": {
        "schema_version": int,
        "generated_at": str,
        "source_commit": str,
        "repo_name": str,
        "repo_url": NULLABLE_STR,
    },
    "project": {
        "name": str,
        "tagline": str,
        "purpose": LENS,
        "users": [str],
        "capabilities": [{"title": str, "functional": str, "technical": str}],
        "tech_stack": [{"name": str, "role": str}],
        "run": {"setup": [str], "commands": [LABELLED_COMMAND]},
    },
    "architecture": {
        "summary": LENS,
        "components": [
            {"id": ID, "name": str, "kind": str, "module_ids": [str], "description": LENS}
        ],
        "connections": [{"from": str, "to": str, "label": str}],
        "diagrams": [{"id": ID, "title": str, "mermaid": str}],
    },
    "modules": [
        {
            "id": ID,
            "name": str,
            "path": str,
            "status": OneOf("analyzed", "not_analyzed"),
            "purpose": LENS,
            "interface": [
                {
                    "name": str,
                    "kind": str,
                    "signature": str,
                    "description": str,
                    "file": str,
                    "line": LINE,
                }
            ],
            "invariants": [str],
            "dependencies": {"internal": [str], "external": [str]},
            "key_files": [{"path": str, "role": str}],
        }
    ],
    "flows": [
        {
            "id": ID,
            "title": str,
            "summary": LENS,
            "steps": [
                {
                    "title": str,
                    "text": LENS,
                    "file": str,
                    "line_start": LINE,
                    "line_end": LINE,
                    "snippet?": str,
                }
            ],
        }
    ],
    "glossary": [
        {
            "term": str,
            "definition": str,
            "kind": OneOf("domain", "tech"),
            "module_ids": [str],
        }
    ],
    "paths": [
        {
            "id": ID,
            "audience": str,
            "title": str,
            "steps": [
                {
                    "ref_type": OneOf("module", "flow", "glossary", "doc"),
                    "ref_id": str,
                    "note": str,
                }
            ],
        }
    ],
    "agent_notes": {
        "rules": [str],
        "traps": [str],
        "do_not_touch": [{"path": str, "reason": str}],
        "commands": [LABELLED_COMMAND],
    },
}


def _type_name(spec: Any) -> str:
    if spec is NULLABLE_STR:
        return "str or null"
    return spec.__name__ if isinstance(spec, type) else str(spec)


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check(value: Any, spec: Any, path: str, errors: list[str]) -> None:
    if isinstance(spec, dict):
        if not isinstance(value, dict):
            errors.append(f"{path or '(root)'}: expected object")
            return
        known = {raw_key.rstrip("?") for raw_key in spec}
        for key in value:
            if key not in known:
                errors.append(f"{_join(path, key)}: unknown field")
        for raw_key, sub in spec.items():
            key = raw_key.rstrip("?")
            child = _join(path, key)
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
    elif isinstance(spec, IdStr):
        if not isinstance(value, str):
            errors.append(f"{path}: expected str")
        elif not _ID.fullmatch(value):
            errors.append(f"{path}: invalid id '{value}' ({ID_HINT})")
    elif isinstance(spec, LineNo):
        if not _is_int(value):
            errors.append(f"{path}: expected int")
        elif value < 1:
            errors.append(f"{path}: expected line number >= 1")
    elif (spec is int and isinstance(value, bool)) or not isinstance(value, spec):
        errors.append(f"{path}: expected {_type_name(spec)}")


def _unique(items: list[dict[str, Any]], key: str, label: str, errors: list[str]) -> set[str]:
    """Report repeated values of ``key``, compared case-folded; return the values as written.

    Terms are free text and ids are lowercase slugs, so "Note" and "note" are the same entry.
    The returned set keeps the original spelling because references match it exactly.
    """
    seen: set[str] = set()
    folded: set[str] = set()
    for item in items:
        value = item[key]
        if value.casefold() in folded:
            errors.append(f"duplicate {label} '{value}'")
        folded.add(value.casefold())
        seen.add(value)
    return seen


def _is_doc_path(ref: str) -> bool:
    """A repo-relative POSIX path that cannot escape the repo root."""
    return (
        bool(ref)
        and not ref.startswith("/")
        and "\\" not in ref
        and "\0" not in ref
        and ".." not in ref.split("/")
    )


def _cross_check(model: dict[str, Any], errors: list[str]) -> None:
    module_ids = _unique(model["modules"], "id", "module id", errors)
    component_ids = _unique(model["architecture"]["components"], "id", "component id", errors)
    _unique(model["architecture"]["diagrams"], "id", "diagram id", errors)
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
        where = f"modules[{i}].dependencies.internal"
        for mid in mod["dependencies"]["internal"]:
            need("module", mid, module_ids, where)
        if mod["id"] in mod["dependencies"]["internal"]:
            errors.append(f"{where}: module depends on itself")
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
            where = f"paths[{i}].steps[{j}]"
            ref_type, ref = step["ref_type"], step["ref_id"]
            if ref_type == "doc":
                if not _is_doc_path(ref):
                    errors.append(f"{where}.ref_id: invalid doc path {ref!r} ({DOC_HINT})")
            else:
                need(labels[ref_type], ref, known[ref_type], where)


def validate(model: dict[str, Any]) -> list[str]:
    """Return every problem found; an empty list means the model is valid.

    The schema version is checked first, whatever else is wrong, because a model of another
    version is expected to differ in shape and that is the first thing the author must learn.
    Cross-references are checked only once the shape is valid.
    """
    errors: list[str] = []
    meta = model.get("meta") if isinstance(model, dict) else None
    if isinstance(meta, dict) and "schema_version" in meta:
        if meta["schema_version"] != SCHEMA_VERSION:
            errors.append(f"meta.schema_version: expected {SCHEMA_VERSION}")
    _check(model, SPEC, "", errors)
    if not errors:
        _cross_check(model, errors)
    return errors
