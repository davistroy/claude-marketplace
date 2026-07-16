"""Filesystem helpers for visual-explainer.

Provides small, dependency-free I/O utilities shared across the CLI pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path


def _atomic_write_text(filepath: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text to a file atomically.

    Writes to a temporary file in the same directory first, then atomically
    replaces the destination with `os.replace` (atomic on both POSIX and
    Windows). This prevents a truncated or partially-written durable file
    (metadata.json, evaluation-NN.json, concepts.json) if the process is
    interrupted mid-write, which would otherwise lose track of already
    completed (and already-paid-for) generation work.

    Args:
        filepath: Destination path for the file.
        content: Text content to write.
        encoding: Text encoding to use.
    """
    import uuid

    tmp_path = filepath.with_name(f".{filepath.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp_path.write_text(content, encoding=encoding)
        os.replace(tmp_path, filepath)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
