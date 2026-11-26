"""Differential check of the YAML comment rules against a real parser (SE-H2).

For every snippet and every place a comment line could be inserted: when the verifier accepts
the edit as comment-only, PyYAML must load the edited text to exactly what it loads the original
to. PyYAML is a test-only oracle (the ``dev`` extra); the tool itself stays stdlib only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from document_repo import verify
from document_repo.languages import detect

yaml = pytest.importorskip("yaml")

CORPUS = [
    "- foo\n  bar\n",
    "- foo\n bar\n",
    "a:\n  - foo\n    bar\n  - baz\n",
    "- - foo\n    bar\n  - x\n",
    "- k: foo\n  j: bar\n- k: 2\n",
    "- k: a long\n    plain value\n  j: 1\n",
    "k: a long\n  plain scalar\nj: 1\n",
    "a:\n  b: one\n    two\n  c: 3\n",
    "run: |\n  make\n  test\nnext: 1\n",
    "a:\n  run: >-\n    one\n    two\n  b: 1\n",
    "- |\n  text\n- >\n  more\n",
    'k: "a\n  b"\nj: 1\n',
    "k: 'it''s\n  x'\nj: 1\n",
    "k: [a,\n  b]\nj: 1\n",
    "jobs:\n  build:\n    steps:\n      - run: echo hi\n        name: say\n      - uses: x\n",
    "steps:\n  - name: a\n    run: echo a\n      && echo b\n  - name: c\n",
    "---\nk: 1\n---\nj: 2\n",
    "foo\nbar\n",
    "k: &a\n  x\nj: *a\n",
]

#: Comment lines a commenter might insert, at their own indentation.
INSERTS = ["# c", "  # c", "    # c", " # c", ""]


def _accepted(before: str, after: str) -> bool:
    lang = detect("c.yml")
    assert lang is not None
    return verify._judge(Path("."), "c.yml", before, after, lang).ok


def _load(text: str) -> list[object]:
    return list(yaml.safe_load_all(text))


@pytest.mark.parametrize("before", CORPUS)
def test_every_accepted_insert_loads_to_the_same_data(before: str) -> None:
    expected = _load(before)
    lines = before.splitlines(keepends=True)
    checked = 0
    for at in range(len(lines) + 1):
        for inserted in INSERTS:
            after = "".join(lines[:at] + [inserted + "\n"] + lines[at:])
            if not _accepted(before, after):
                continue
            checked += 1
            try:
                got = _load(after)
            except yaml.YAMLError as exc:  # pragma: no cover - the failure being guarded
                pytest.fail(f"accepted insert {inserted!r} at line {at} breaks the file: {exc}")
            assert got == expected, (at, inserted, after)
    assert checked, "the corpus entry accepted no insert at all, so it tests nothing"
