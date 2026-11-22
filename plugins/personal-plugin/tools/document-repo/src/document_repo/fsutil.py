"""File helpers shared by the modules that write model and explorer files."""

from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from pathlib import Path


def write_bytes_atomic(path: Path, data: bytes) -> None:
    """Replace ``path`` with ``data`` so a reader sees the old bytes or the new, never a mix.

    The bytes go to a temporary file in the same directory (a rename is atomic only within one
    file system), are flushed and fsynced, then renamed over ``path``. On any error the temporary
    file is removed and the error is re-raised, so ``path`` is left as it was.
    """
    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
            tmp_name = tmp.name
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        if path.exists():
            # mkstemp-style files are 0600; keep the mode the file already had.
            os.chmod(tmp_name, stat.S_IMODE(path.stat().st_mode))
        os.replace(tmp_name, path)
    except BaseException:
        if tmp_name is not None:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
        raise
