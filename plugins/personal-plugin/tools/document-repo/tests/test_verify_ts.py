"""The ts-printer method: re-print JS/TS with comments removed and compare.

These tests run the real ``node`` and TypeScript compiler. Without them they skip locally and
fail under ``CI``, so a green run in CI always means the printer was exercised.
"""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path

import pytest

from document_repo import verify
from document_repo.verify import typescript_available, verify_file

BASE = "export function add(a: number, b: number): number {\n  return a + b;\n}\n"
TSX_BASE = "export const C = () => <div>hi</div>;\n"
TS_MISSING = (
    "TypeScript compiler not available; JS/TS files cannot be verified "
    "(install with: npm install -g typescript)"
)


def _unavailable(message: str) -> None:
    if os.environ.get("CI"):
        pytest.fail(message)
    pytest.skip(message)


@pytest.fixture
def ts_repo(make_repo):
    repo = make_repo(
        {"m.ts": BASE, "c.tsx": TSX_BASE, "j.js": "const x = 1;\n", "a.ts": "export const x = 1;\n"}
    )
    if not typescript_available(repo):
        _unavailable("node + typescript not available (install with: npm install -g typescript)")
    return repo


@pytest.fixture
def commit_then_edit(commit_files):
    """Make ``before`` the committed version of ``rel``, write ``after`` there, and verify it."""

    def _do(repo: Path, rel: str, before: str, after: str):
        commit_files(repo, {rel: before.encode("utf-8")}, "base")
        return _edit(repo, rel, after)

    return _do


def _edit(repo: Path, rel: str, text: str):
    """Write ``text`` as bytes (so ``\\r`` survives on every platform) and verify ``rel``."""
    (repo / rel).write_bytes(text.encode("utf-8"))
    return verify_file(repo, rel)


def _printer_json(repo: Path, rel: str, before: str, after: str) -> dict:
    proc = verify._run_printer(repo, rel, before, after)
    assert proc is not None and proc.returncode == 0, proc
    return json.loads(proc.stdout)


# --- the brief's cases ------------------------------------------------------------------------


def test_ts_comments_pass(ts_repo) -> None:
    after = "/** Add two numbers. */\n// why: demo\n" + BASE.replace("return", "// sum\n  return")
    r = _edit(ts_repo, "m.ts", after)
    assert r.ok and r.method == "ts-printer", r.detail


def test_ts_trailing_comment_passes(ts_repo) -> None:
    # Allowed by the printer method; the comment standards still forbid it.
    assert _edit(ts_repo, "m.ts", BASE.replace("a + b;", "a + b; // sum")).ok


def test_ts_code_change_fails(ts_repo) -> None:
    r = _edit(ts_repo, "m.ts", "// note\n" + BASE.replace("a + b", "a - b"))
    assert not r.ok and r.method == "ts-printer"
    assert "code changed" in r.detail


def test_ts_new_parse_error_fails(ts_repo) -> None:
    r = _edit(ts_repo, "m.ts", BASE + "/* unterminated\n")
    assert not r.ok and r.method == "ts-printer" and "parse errors" in r.detail, r.detail


def test_tsx_and_js(ts_repo) -> None:
    assert _edit(ts_repo, "c.tsx", "/** Greeting. */\n" + TSX_BASE).ok
    assert _edit(ts_repo, "j.js", "// one\nconst x = 1;\n").ok


def test_fails_closed_without_node(make_repo, monkeypatch) -> None:
    # Addendum A / D74: JS/TS are verified only by the printer; no heuristic fallback.
    repo = make_repo({"m.ts": BASE})
    monkeypatch.setattr(verify, "node_binary", lambda: None)
    r = _edit(repo, "m.ts", "// c\n" + BASE)
    assert not r.ok and "TypeScript compiler not available" in r.detail
    assert r.method == "none" and r.detail == TS_MISSING
    assert not typescript_available(repo)


def test_fails_closed_without_typescript(make_repo, monkeypatch, tmp_path) -> None:
    # node is present but no search path holds the typescript package: ts_print.js exits 3.
    repo = make_repo({"m.ts": BASE})
    if verify.node_binary() is None:
        _unavailable("node not available")
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(verify, "ts_search_paths", lambda repo: [str(empty)])
    r = _edit(repo, "m.ts", "// c\n" + BASE)
    assert not r.ok and r.method == "none" and r.detail == TS_MISSING, (r.method, r.detail)
    assert not typescript_available(repo)


def test_search_paths_include_env(make_repo, monkeypatch, tmp_path) -> None:
    repo = make_repo({"m.ts": BASE})
    monkeypatch.setenv("DOCUMENT_REPO_TS_PATHS", str(tmp_path))
    assert str(tmp_path) in verify.ts_search_paths(repo)


def test_search_paths_order_and_env_split(make_repo, monkeypatch, tmp_path) -> None:
    repo = make_repo({"m.ts": BASE})
    first, second = tmp_path / "one", tmp_path / "two"
    monkeypatch.setenv("DOCUMENT_REPO_TS_PATHS", os.pathsep.join([str(first), "", str(second)]))
    monkeypatch.setattr(verify, "_npm_global_root", lambda: "/global/root")
    assert verify.ts_search_paths(repo) == [str(repo), str(first), str(second), "/global/root"]


def test_search_paths_without_env_or_global(make_repo, monkeypatch) -> None:
    repo = make_repo({"m.ts": BASE})
    monkeypatch.delenv("DOCUMENT_REPO_TS_PATHS", raising=False)
    monkeypatch.setattr(verify, "_npm_global_root", lambda: None)
    assert verify.ts_search_paths(repo) == [str(repo)]


# --- the printer decides on the code exactly as TypeScript parses it ---------------------------


def test_tsx_comment_after_jsx_passes(ts_repo, commit_then_edit) -> None:
    # The old line-scanner fallback read the "//" in JSX text and attributes as a comment.
    jsx = '<a href="http://x.test">see http://x.test</a>'
    before = f"export const C = () => {jsx};\nexport const D = 1;\n"
    after = f"export const C = () => {jsx};\n// the second export\nexport const D = 1;\n"
    r = commit_then_edit(ts_repo, "c.tsx", before, after)
    assert r.ok and r.method == "ts-printer", r.detail


def test_tsx_comment_on_the_line_after_jsx_passes(ts_repo, commit_then_edit) -> None:
    after = TSX_BASE + "// Greets the reader.\nexport const D = 1;\n"
    r = commit_then_edit(ts_repo, "c.tsx", TSX_BASE + "export const D = 1;\n", after)
    assert r.ok, r.detail


def test_regex_with_backtick_and_quote_passes(ts_repo, commit_then_edit) -> None:
    before = "const re = /[`']/g;\nexport const ok = re.test('x');\n"
    after = (
        "const re = /[`']/g;\n// Matches a backtick or a quote.\nexport const ok = re.test('x');\n"
    )
    r = commit_then_edit(ts_repo, "m.ts", before, after)
    assert r.ok and r.method == "ts-printer", r.detail


def test_comment_inside_template_literal_fails(ts_repo, commit_then_edit) -> None:
    before = "export const s = `line one\nline two`;\n"
    after = "export const s = `line one\n// note\nline two`;\n"
    r = commit_then_edit(ts_repo, "m.ts", before, after)
    assert not r.ok and r.method == "ts-printer" and "code changed" in r.detail, r.detail


def test_comment_inside_template_substitution_passes(ts_repo, commit_then_edit) -> None:
    # Inside ${ ... } the text is code, so a comment there is a real comment.
    before = "export const s = `a ${1 + 2} b`;\n"
    after = "export const s = `a ${1 /* one */ + 2} b`;\n"
    r = commit_then_edit(ts_repo, "m.ts", before, after)
    assert r.ok, r.detail


def test_triple_slash_reference_fails_through_common_guards(ts_repo) -> None:
    before = "export const x = 1;\n"
    after = '/// <reference path="x" />\nexport const x = 1;\n'
    (ts_repo / "a.ts").write_bytes(after.encode())
    # The printer alone says the two versions are equal ...
    proof = verify._ts_verify(ts_repo, "a.ts", before, after)
    assert proof is not None and proof.ok and proof.method == "ts-printer"
    # ... and the guards that run after it still fail the file.
    r = verify_file(ts_repo, "a.ts")
    assert not r.ok and r.method == "ts-printer" and "directive" in r.detail, r.detail


def test_return_followed_by_multiline_comment_fails(ts_repo, commit_then_edit) -> None:
    # A block comment holding a newline is a line terminator, so ASI makes this "return;".
    before = "export function f() {\n  return 1;\n}\n"
    after = "export function f() {\n  return /* a\n  b */ 1;\n}\n"
    r = commit_then_edit(ts_repo, "m.ts", before, after)
    assert not r.ok and r.method == "ts-printer" and "code changed" in r.detail, r.detail


def test_crlf_files_keep_their_carriage_returns(ts_repo, commit_then_edit) -> None:
    before = "export const s = `a\r\nb`;\r\nexport const t = 1;\r\n"
    after = "export const s = `a\r\nb`;\r\n// Second.\r\nexport const t = 1;\r\n"
    r = commit_then_edit(ts_repo, "m.ts", before, after)
    assert r.ok, r.detail
    # A "\r" in a template literal is part of its raw text, so removing it is a code change.
    assert not _printer_json(ts_repo, "m.ts", "const s = `a\r\nb`;\n", "const s = `a\nb`;\n")[
        "equal"
    ]


# One file per extension, each using syntax that only that script kind parses without errors.
KIND_CASES = [
    ("a.ts", "export const a = <number>(1 as unknown);\n"),
    ("a.mts", "export const a = <number>(1 as unknown);\n"),
    ("a.cts", "export const a = <number>(1 as unknown);\n"),
    ("a.d.ts", "export declare const a: number;\n"),
    ("a.d.mts", "export declare const a: number;\n"),
    ("a.tsx", "export const a = <div>{1}</div>;\n"),
    ("a.jsx", "export const a = <div>{1}</div>;\n"),
    ("a.js", "export const a = <div>{1}</div>;\n"),
    ("a.mjs", "export const a = <div>{1}</div>;\n"),
    ("a.cjs", "exports.a = <div>{1}</div>;\n"),
    ("A.TSX", "export const a = <div>{1}</div>;\n"),
    ("dir.js/b.ts", "export const a = <number>(1 as unknown);\n"),
]


@pytest.mark.parametrize("rel,text", KIND_CASES, ids=[c[0] for c in KIND_CASES])
def test_script_kind_follows_the_extension(ts_repo, rel: str, text: str) -> None:
    data = _printer_json(ts_repo, rel, text, "// c\n" + text)
    assert data == {"equal": True, "before_errors": 0, "after_errors": 0}, data


@pytest.mark.parametrize("rel,text", KIND_CASES, ids=[c[0] for c in KIND_CASES])
def test_comment_only_edit_passes_for_every_extension(
    make_repo, ts_repo, rel: str, text: str
) -> None:
    repo = make_repo({rel: text})
    r = _edit(repo, rel, "// Note.\n" + text)
    assert r.ok and r.method == "ts-printer", r.detail


def test_declaration_files_are_recognised_by_name(ts_repo) -> None:
    # TypeScript prints /// <reference> lines only for a .d.ts, so the real name must reach it.
    before, after = "export {};\n", '/// <reference path="x" />\nexport {};\n'
    declaration = verify._ts_verify(ts_repo, "a.d.ts", before, after)
    assert declaration is not None and not declaration.ok and "code changed" in declaration.detail
    module = verify._ts_verify(ts_repo, "a.ts", before, after)
    assert module is not None and module.ok


def test_wrong_kind_would_show_parse_errors(ts_repo) -> None:
    # Guards the table above: a type assertion is not valid in a .tsx file.
    data = _printer_json(ts_repo, "a.tsx", "const a = <number>1;\n", "const a = <number>1;\n")
    assert data["before_errors"] > 0


def test_unknown_extension_is_an_error_not_a_guess(ts_repo) -> None:
    proc = verify._run_printer(ts_repo, "x.vue", "", "")
    assert proc is not None and proc.returncode not in (0, 3)
    assert "x.vue" in proc.stderr


# --- helpers around the printer ----------------------------------------------------------------


def test_typescript_available_with_the_real_compiler(ts_repo) -> None:
    assert typescript_available(ts_repo)


def test_global_root_is_cached_and_survives_npm_failure(monkeypatch) -> None:
    calls: list[list[str]] = []

    class Done:
        returncode = 1
        stdout = ""

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return Done()

    verify._npm_global_root.cache_clear()
    monkeypatch.setattr(verify.shutil, "which", lambda name: "/bin/npm")
    monkeypatch.setattr(verify.subprocess, "run", fake_run)
    try:
        assert verify._npm_global_root() is None
        assert verify._npm_global_root() is None
        assert len(calls) == 1
    finally:
        verify._npm_global_root.cache_clear()


@pytest.mark.parametrize(
    "error",
    [OSError("cannot execute"), subprocess.TimeoutExpired("npm", 30)],
    ids=["os-error", "timeout"],
)
def test_global_root_survives_npm_that_cannot_run(monkeypatch, error) -> None:
    def fake_run(cmd, **kwargs):
        raise error

    verify._npm_global_root.cache_clear()
    monkeypatch.setattr(verify.shutil, "which", lambda name: "/bin/npm")
    monkeypatch.setattr(verify.subprocess, "run", fake_run)
    try:
        assert verify._npm_global_root() is None
    finally:
        verify._npm_global_root.cache_clear()


def test_global_root_without_npm(monkeypatch) -> None:
    verify._npm_global_root.cache_clear()
    monkeypatch.setattr(verify.shutil, "which", lambda name: None)
    try:
        assert verify._npm_global_root() is None
    finally:
        verify._npm_global_root.cache_clear()


def test_global_root_reads_npm_output(monkeypatch) -> None:
    class Done:
        returncode = 0
        stdout = "/some/where/node_modules\n"

    verify._npm_global_root.cache_clear()
    monkeypatch.setattr(verify.shutil, "which", lambda name: "/bin/npm")
    monkeypatch.setattr(verify.subprocess, "run", lambda cmd, **kw: Done())
    try:
        assert verify._npm_global_root() == "/some/where/node_modules"
    finally:
        verify._npm_global_root.cache_clear()


def _script(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "fake_printer.js"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_printer_crash_fails_closed(ts_repo, monkeypatch, tmp_path) -> None:
    script = _script(tmp_path, "throw new Error('boom');\n")
    monkeypatch.setattr(verify, "TS_SCRIPT", script)
    r = _edit(ts_repo, "m.ts", "// c\n" + BASE)
    assert not r.ok and r.method == "ts-printer" and "printer failed" in r.detail, r.detail
    assert "boom" in r.detail


@pytest.mark.parametrize(
    "stdout",
    [
        "not json",
        "[]",
        "{}",
        '{"equal": true}',
        '{"equal": 1, "before_errors": 0, "after_errors": 0}',
    ],
    ids=["garbage", "list", "empty-object", "missing-counts", "wrong-type"],
)
def test_unreadable_printer_output_fails_closed(ts_repo, monkeypatch, tmp_path, stdout) -> None:
    script = _script(tmp_path, f"process.stdout.write({json.dumps(stdout)});\n")
    monkeypatch.setattr(verify, "TS_SCRIPT", script)
    r = _edit(ts_repo, "m.ts", "// c\n" + BASE)
    assert not r.ok and r.method == "ts-printer" and "unreadable output" in r.detail, r.detail


def test_printer_timeout_fails_closed(ts_repo, monkeypatch, tmp_path) -> None:
    script = _script(tmp_path, "setTimeout(() => {}, 30000);\n")
    monkeypatch.setattr(verify, "TS_SCRIPT", script)
    monkeypatch.setattr(verify, "TS_TIMEOUT", 1)
    r = _edit(ts_repo, "m.ts", "// c\n" + BASE)
    assert not r.ok and r.method == "ts-printer" and "timed out" in r.detail, r.detail
    assert not typescript_available(ts_repo)


def test_printer_runs_with_a_memory_ceiling(ts_repo, monkeypatch, tmp_path) -> None:
    script = _script(
        tmp_path,
        """
        const v8 = require('v8');
        const mb = Math.round(v8.getHeapStatistics().heap_size_limit / (1024 * 1024));
        process.stdout.write(JSON.stringify({ equal: true, before_errors: mb, after_errors: 0 }));
        """,
    )
    monkeypatch.setattr(verify, "TS_SCRIPT", script)
    proc = verify._run_printer(ts_repo, "m.ts", "", "")
    assert proc is not None and proc.returncode == 0
    assert json.loads(proc.stdout)["before_errors"] < 1536
