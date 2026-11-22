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
            {"id": str, "name": str, "kind": str, "module_ids": [str], "description": LENS}
        ],
        "connections": [{"from": str, "to": str, "label": str}],
        "diagrams": [{"id": str, "title": str, "mermaid": str}],
    },
    "modules": [
        {
            "id": str,
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
                    "line": int,
                }
            ],
            "invariants": [str],
            "dependencies": {"internal": [str], "external": [str]},
            "key_files": [{"path": str, "role": str}],
        }
    ],
    "flows": [
        {
            "id": str,
            "title": str,
            "summary": LENS,
            "steps": [
                {
                    "title": str,
                    "text": LENS,
                    "file": str,
                    "line_start": int,
                    "line_end": int,
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
            "id": str,
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
                need(
                    labels[step["ref_type"]],
                    step["ref_id"],
                    known[step["ref_type"]],
                    f"paths[{i}].steps[{j}]",
                )


def validate(model: dict[str, Any]) -> list[str]:
    """Return every problem found; an empty list means the model is valid."""
    errors: list[str] = []
    _check(model, SPEC, "", errors)
    if not errors:
        _cross_check(model, errors)
    return errors
