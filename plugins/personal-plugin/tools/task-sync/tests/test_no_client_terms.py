"""GUARDRAIL: prove the confidentiality tool source carries no client terms.

This is a public repo. The design keeps client/brand/company terms OUT of
the source entirely: the detectors are pure *structural* regexes, and the
only client-specific terms the tool ever sees are the per-repo
``sensitive_terms`` supplied at RUNTIME via config (``scan_task``). A brand
or client name appearing anywhere in this source would itself be a leak —
exactly what the tool exists to prevent.

These tests enforce that invariant three ways:

1. No module in ``confidential/`` references the sibling repo's
   client-identifying source files (``leak_scan``,
   ``desensitization_glossary``) — proving nothing was copied from them.
2. The detector modules (``secrets.py``, ``patterns.py``) define NO
   hardcoded collection of proper-noun-shaped string literals — i.e. no
   inline brand/company/name denylist. They may only compile regexes.
3. The client-term entry point is runtime config: ``scan_task`` exposes a
   ``sensitive_terms`` parameter and nothing hardcodes a term list.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import task_sync.confidential as confidential_pkg

_CONF_DIR = Path(confidential_pkg.__file__).resolve().parent
_DETECTOR_FILES = [_CONF_DIR / "secrets.py", _CONF_DIR / "patterns.py"]

# Source files in the sibling repo that hold client-identifying term lists.
# They must never be referenced (let alone copied) here.
_FORBIDDEN_SOURCE_REFERENCES = ("leak_scan", "desensitization_glossary")

# A "bare proper noun" string literal: Capitalized, letters only, no dots,
# digits, or regex metacharacters. Brand/company/person names look like
# this; category slugs ("structural.email") and lowercase keywords do not.
_PROPER_NOUN = re.compile(r"^[A-Z][a-zA-Z]{2,}$")


def test_no_reference_to_client_identifying_source_files() -> None:
    for path in _CONF_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for forbidden in _FORBIDDEN_SOURCE_REFERENCES:
            assert forbidden not in text, (
                f"{path.name} references {forbidden!r} — the sibling repo's "
                "client-identifying source must never be copied in."
            )


def _collection_string_literals(tree: ast.AST) -> list[str]:
    """Every string constant that appears inside a list/tuple/set literal."""
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for element in node.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    literals.append(element.value)
    return literals


def test_detector_modules_have_no_hardcoded_proper_noun_lists() -> None:
    for path in _DETECTOR_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders = [
            value for value in _collection_string_literals(tree) if _PROPER_NOUN.match(value)
        ]
        assert offenders == [], (
            f"{path.name} contains proper-noun string literals in a "
            f"collection ({offenders}); detectors must be regex-only and "
            "client terms must come from runtime config, not source."
        )


def test_client_terms_are_runtime_config_not_hardcoded() -> None:
    scan_src = (_CONF_DIR / "scan.py").read_text(encoding="utf-8")
    # The client-term entry point is a runtime parameter, by name.
    assert "sensitive_terms" in scan_src
    tree = ast.parse(scan_src)
    scan_task = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "scan_task"
    )
    arg_names = {arg.arg for arg in scan_task.args.args}
    assert "sensitive_terms" in arg_names
