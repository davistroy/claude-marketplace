"""Canonical, atomic load/save for the tasks.json store.

"Canonical" means: stable key order (delegated to `TaskList.to_dict` /
`Task.to_dict`), tasks sorted by `id`, 2-space indent, and a trailing
newline. Two saves of an unchanged `TaskList` must produce byte-identical
files so that sync runs show clean, minimal git diffs.

Writes are atomic (temp file in the same directory + `os.replace`) so a
crash or interrupt mid-write can never leave a truncated or corrupt
tasks.json behind — mirrors `visual_explainer.io_utils._atomic_write_text`.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from task_sync.models import TaskList

_INDENT = 2


def _canonical_json(tasklist: TaskList) -> str:
    data: dict[str, Any] = tasklist.to_dict()
    data["tasks"] = sorted(data["tasks"], key=lambda task: task["id"])
    return json.dumps(data, indent=_INDENT, sort_keys=False, ensure_ascii=False) + "\n"


def save(tasklist: TaskList, path: str | Path) -> None:
    """Write `tasklist` to `path` atomically, in canonical form."""
    destination = Path(path)
    content = _canonical_json(tasklist)

    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, destination)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def load(path: str | Path) -> TaskList:
    """Read and validate a tasks.json file into a `TaskList`.

    Raises:
        ValueError: if the file contains an invalid status/priority or is
            otherwise malformed (missing required fields, wrong types).
    """
    source = Path(path)
    with source.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"tasks.json must contain a JSON object, got {type(data).__name__}")

    return TaskList.from_dict(data)
