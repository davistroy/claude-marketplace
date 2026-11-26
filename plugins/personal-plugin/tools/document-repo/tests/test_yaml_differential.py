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
    # Review round: a bare scalar on its own line continues to its parent's column, not its own.
    "key:\n  foo\n  bar\n",
    "key:\n  foo\n bar\n",
    "a:\n  key:\n    foo\n    bar\n",
    "- \n  foo\n  bar\n",
    "-\n  foo\n  bar\n",
    "-   foo\n  bar\n",
    "-   foo\n bar\n",
    "- &a foo\n  bar\n- *a\n",
    "--- foo\nbar\n",
    "--- foo\n bar\n",
    "? foo\n  bar\n: 1\n",
    "? k\n: foo\n  bar\n",
    "k: foo\n  bar\n  baz\n",
    "- k: v\n  j: foo\n    bar\n",
    "- k: v\n  j:\n    foo\n    bar\n",
    "k: >\n  a\n\n  b\nj: 1\n",
    "k: |2\n    a\n  b\nj: 1\n",
    "k: |\n a\nj: 1\n",
    "k: !!str\n  foo\n  bar\n",
    "k: &x\n  foo\n  bar\n",
    "k: {a: 1,\n  b: 2}\n",
    "k: [a, b\n  , c]\n",
    'k: "a\n\n  b"\n',
    "k: 'a\n\n  b'\n",
    "k: a\n\n  b\n",
    "- a\n\n  b\n",
    "a\n\n b\n",
    "%YAML 1.1\n---\nfoo\nbar\n",
    "k:\n- a\n  b\n",
    "k:\n- a\n b\n",
    "- k:\n  - a\n    b\n",
    'k: "x" \nj: |\n  y\n',
    "k: http://x\n  y\n",
    "key:\n  foo\n  - bar\n",
    "k: v\n  [a]\n",
    # Ordinary commenting that must keep passing.
    "a: 1\nb:\n  - x\n  - y\nc:\n  d: 2\n",
]

#: Comment lines a commenter might insert, at their own indentation.
INSERTS = ["# c", "  # c", "    # c", " # c", "", "      # c", "\t# c"]


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


#: Generated bases (yfuzz-style): a holder, a plain scalar that may run over two lines at any
#: indent, and a following node. Invalid YAML is skipped; every valid base is checked.
_HOLDERS = ["key:", "-", "- k: v\n  j:", "k: !!str", "k: &x", "---", "a:\n  b:", "- - x\n  -"]
_TAILS = ["", "z: 1\n", "- q\n"]


def _generated() -> list[str]:
    bases = []
    for holder in _HOLDERS:
        firsts = [f"{holder} foo\n"] + [f"{holder}\n{' ' * i}foo\n" for i in range(5)]
        for first in firsts:
            for j in range(5):
                for cont in ("bar", "- bar", "[x]"):
                    for tail in _TAILS:
                        bases.append(f"{first}{' ' * j}{cont}\n{tail}")
    return bases


def _valid(text: str) -> bool:
    try:
        _load(text)
    except yaml.YAMLError:
        return False
    return True


def test_generated_bases_accept_no_insert_that_changes_the_data() -> None:
    bad = []
    bases = [b for b in _generated() if _valid(b)]
    assert len(bases) > 100, "the generator should produce many valid bases"
    for before in bases:
        expected = _load(before)
        lines = before.splitlines(keepends=True)
        for at in range(len(lines) + 1):
            for inserted in INSERTS:
                after = "".join(lines[:at] + [inserted + "\n"] + lines[at:])
                if not _accepted(before, after):
                    continue
                try:
                    got = _load(after)
                except yaml.YAMLError:
                    got = "ERR"
                if got != expected:
                    bad.append((before, at, inserted))
    assert not bad, f"{len(bad)} accepted inserts change the data, first: {bad[:5]}"
