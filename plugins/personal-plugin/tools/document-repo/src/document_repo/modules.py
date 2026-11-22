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

GROUPING_ROOTS = frozenset(
    {"src", "packages", "apps", "services", "libs", "lib", "modules", "cmd", "internal"}
)


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
        group = groups.setdefault(
            key, {"id": slug(key), "path": "." if key == "root" else key, "files": [], "lines": 0}
        )
        group["files"].append(entry["path"])
        group["lines"] += int(entry["lines"])
    for group in groups.values():
        group["files"].sort()
    return {"modules": sorted(groups.values(), key=lambda g: g["id"])}
