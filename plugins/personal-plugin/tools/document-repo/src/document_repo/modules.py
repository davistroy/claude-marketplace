"""Propose module boundaries from the inventory.

A "module" is the unit of work for the rest of the run: one analysis agent,
one commenting agent, one README, one commit. This first cut is mechanical;
the skill then merges tiny modules and splits huge ones with judgement.

Rule: group by the first path segment, except under common grouping
directories (src, packages, apps, ...) where the second segment decides.
Top-level files form the "root" module. Internally they use the key ".", which
no git path can contain as a component, so a real directory named "root" never
merges with them.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

GROUPING_ROOTS = frozenset(
    {"src", "packages", "apps", "services", "libs", "lib", "modules", "cmd", "internal"}
)

# Grouping key of top-level files. "." cannot be a component of a git path, so it
# cannot collide with a real directory name.
ROOT_KEY = "."
ROOT_ID = "root"


def module_key(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) == 1:
        return ROOT_KEY
    if parts[0] in GROUPING_ROOTS and len(parts) > 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def slug(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-") or "root"


def _assign_ids(keys: list[str]) -> dict[str, str]:
    """Give each grouping key a distinct id, deterministically.

    Keys are taken in sorted order. "root" is reserved for the root key (top-level files),
    even when that key is absent, so id "root" always means path ".". Every other key
    takes ``slug(key)``, with ``-2``, ``-3`` and so on appended until the id is free.
    Distinct keys can slug alike (``.config`` and ``config``, ``lib/foo`` and
    ``lib-foo``, ``_`` and the ``root`` fallback), so the suffix keeps ids unique.
    """
    ids: dict[str, str] = {}
    taken: set[str] = {ROOT_ID}
    for key in sorted(keys, key=lambda k: (k != ROOT_KEY, k)):
        base = ROOT_ID if key == ROOT_KEY else slug(key)
        candidate = base
        n = 2
        while candidate in taken and key != ROOT_KEY:
            candidate = f"{base}-{n}"
            n += 1
        taken.add(candidate)
        ids[key] = candidate
    return ids


def propose_modules(inventory: dict[str, Any]) -> dict[str, Any]:
    """Group the non-skipped inventory files into modules, sorted by id.

    A module's ``files`` list is authoritative, and its ``path`` may be a prefix of
    another module's path (``src`` vs ``src/api``).
    """
    groups: dict[str, dict[str, Any]] = {}
    for entry in inventory["files"]:
        if entry["skip"] is not None:
            continue
        key = module_key(entry["path"])
        group = groups.setdefault(key, {"path": key, "files": [], "lines": 0})
        group["files"].append(entry["path"])
        group["lines"] += int(entry["lines"])
    ids = _assign_ids(list(groups))
    modules = []
    for key, group in groups.items():
        group["files"].sort()
        modules.append({"id": ids[key], **group})
    return {"modules": sorted(modules, key=lambda m: m["id"])}
