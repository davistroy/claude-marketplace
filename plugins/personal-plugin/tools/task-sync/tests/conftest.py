"""Shared fixtures for task-sync tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tasks_json_path(tmp_path: Path) -> Path:
    """Provide a scratch path for a tasks.json store, not yet created."""
    return tmp_path / "tasks.json"
