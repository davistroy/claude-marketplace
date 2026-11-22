"""Entry point for ``python -m document_repo``."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":  # pragma: no cover - exercised via subprocess
    sys.exit(main())
