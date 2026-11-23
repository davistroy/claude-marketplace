"""The ts-printer method: re-print JS/TS with comments removed and compare.

These tests run the real ``node`` and TypeScript compiler. Without them they skip locally and
fail under ``CI``, so a green run in CI always means the printer was exercised.
"""

from __future__ import annotations

import json
import os
import re
import shutil
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


PARSE_FAIL = re.compile(
    r"^file does not parse cleanly as TypeScript/JavaScript "
    r"\(before: (\d+) errors, after: (\d+) errors\)$"
)


def _parse_fail(result, before_clean: bool, after_clean: bool) -> None:
    """``result`` failed on parse errors, and the error counts say which side was broken."""
    assert not result.ok and result.method == "ts-printer", result
    found = PARSE_FAIL.match(result.detail)
    assert found, result.detail
    assert (int(found[1]) == 0) is before_clean and (int(found[2]) == 0) is after_clean, (
        result.detail
    )


def test_ts_new_parse_error_fails(ts_repo) -> None:
    r = _edit(ts_repo, "m.ts", BASE + "/* unterminated\n")
    _parse_fail(r, before_clean=True, after_clean=False)


def test_same_count_parse_errors_cannot_hide_a_code_change(commit_then_edit, ts_repo) -> None:
    # The old rule was "after_errors > before_errors". Here both sides have one error, and
    # the parser skips the changed token, so the printer output is equal: a false pass.
    broken = "class A { ) }\n"
    r = commit_then_edit(ts_repo, "b.ts", broken, "class A { ] }\n")
    _parse_fail(r, before_clean=False, after_clean=False)


def test_broken_base_fails_even_for_a_pure_comment_insertion(commit_then_edit, ts_repo) -> None:
    broken = "class A { ) }\n"
    r = commit_then_edit(ts_repo, "b.ts", broken, "// a note\n" + broken)
    _parse_fail(r, before_clean=False, after_clean=False)


def test_broken_base_fails_when_the_edit_parses(commit_then_edit, ts_repo) -> None:
    # Either side is enough: a file that parsed badly before cannot be proved unchanged.
    r = commit_then_edit(ts_repo, "b.ts", "class A { ) }\n", "class A { }\n")
    _parse_fail(r, before_clean=False, after_clean=True)


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
    monkeypatch.setattr(verify, "ts_search_paths", lambda repo, rel=None: [str(empty)])
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


def test_search_paths_walk_from_the_files_directory_up_to_the_repo_root(
    make_repo, monkeypatch, tmp_path
) -> None:
    # packages/web/src/a.ts finds packages/web/node_modules before the repo root's own, and
    # every directory in between is a candidate: nearest first, ending at the root.
    repo = make_repo({"packages/web/src/a.ts": BASE})
    env = tmp_path / "env"
    monkeypatch.setenv("DOCUMENT_REPO_TS_PATHS", str(env))
    monkeypatch.setattr(verify, "_npm_global_root", lambda: "/global/root")
    paths = verify.ts_search_paths(repo, "packages/web/src/a.ts")
    assert paths == [
        str(repo / "packages/web/src"),
        str(repo / "packages/web"),
        str(repo / "packages"),
        str(repo),
        str(env),
        "/global/root",
    ]
    # The old one-argument call is unchanged.
    assert verify.ts_search_paths(repo) == [str(repo), str(env), "/global/root"]
    assert verify.ts_search_paths(repo, None) == verify.ts_search_paths(repo)


def test_search_paths_do_not_repeat_the_repo_root(make_repo, monkeypatch) -> None:
    # A file at the top of the work tree has the repo root as its own directory.
    repo = make_repo({"a.ts": BASE})
    monkeypatch.delenv("DOCUMENT_REPO_TS_PATHS", raising=False)
    monkeypatch.setattr(verify, "_npm_global_root", lambda: "/global/root")
    assert verify.ts_search_paths(repo, "a.ts") == [str(repo), "/global/root"]


def test_nested_compiler_is_found_from_the_files_directory(make_repo, monkeypatch) -> None:
    # End to end: the only compiler reachable is packages/web/node_modules/typescript (a stub
    # that delegates to the real one). The env var and the global root are switched off, so
    # only the file's own directory can find it.
    global_root = verify._npm_global_root()
    real = Path(global_root, "typescript") if global_root else None
    if real is None or not real.is_dir() or verify.node_binary() is None:
        _unavailable("node + typescript not available (install with: npm install -g typescript)")
    stub = {
        "packages/web/node_modules/typescript/package.json": json.dumps(
            {"name": "typescript", "version": "0.0.0", "main": "index.js"}
        ),
        "packages/web/node_modules/typescript/index.js": (
            f"module.exports = require({json.dumps(str(real))});\n"
        ),
        "packages/web/src/a.ts": BASE,
    }
    repo = make_repo(stub)
    monkeypatch.delenv("DOCUMENT_REPO_TS_PATHS", raising=False)
    monkeypatch.setattr(verify, "_npm_global_root", lambda: None)
    r = _edit(repo, "packages/web/src/a.ts", "// note\n" + BASE)
    assert r.ok and r.method == "ts-printer", (r.method, r.detail)
    changed = _edit(repo, "packages/web/src/a.ts", BASE.replace("a + b", "a - b"))
    assert not changed.ok and "code changed" in changed.detail, changed.detail


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
    assert isinstance(data.pop("version"), str), data
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
        '{"equal": true, "version": "5.6.3"}',
        '{"equal": 1, "before_errors": 0, "after_errors": 0, "version": "5.6.3"}',
        '{"equal": true, "before_errors": 0, "after_errors": 0}',
        '{"equal": true, "before_errors": 0, "after_errors": 0, "version": ""}',
        '{"equal": true, "before_errors": 0, "after_errors": 0, "version": 5}',
    ],
    ids=[
        "garbage",
        "list",
        "empty-object",
        "missing-counts",
        "wrong-type",
        "missing-version",
        "empty-version",
        "wrong-version-type",
    ],
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


# --- empty bodies: the parser's multiLine flag is layout, not code ------------------------------

# A comment makes an empty body span lines, and the parser records that in a multiLine flag the
# printer honours ("{ }" against "{\n}"). Each pair differs only in a comment.
EMPTY_BODIES = [
    (
        "function",
        "export function noop() {}\n",
        "export function noop() {\n  // Does nothing.\n}\n",
    ),
    (
        "catch",
        "try { f(); } catch (e) {}\n",
        "try { f(); } catch (e) {\n  // The caller retries.\n}\n",
    ),
    (
        "finally",
        "try { f(); } finally {}\n",
        "try { f(); } finally {\n  // Nothing to release.\n}\n",
    ),
    ("arrow", "export const a = () => {};\n", "export const a = () => {\n  // Does nothing.\n};\n"),
    (
        "method",
        "export class A { m() {} }\n",
        "export class A {\n  m() {\n    // Does nothing.\n  }\n}\n",
    ),
    (
        "constructor",
        "export class A { constructor() {} }\n",
        "export class A {\n  constructor() {\n    // Nothing to set up.\n  }\n}\n",
    ),
    ("static-block", "class A { static {} }\n", "class A { static {\n  // Nothing yet.\n} }\n"),
    ("if", "if (a) {}\n", "if (a) {\n  // Nothing to do.\n}\n"),
    (
        "else",
        "if (a) { b(); } else {}\n",
        "if (a) { b(); } else {\n  // Nothing to do.\n}\n",
    ),
    ("while", "while (a) {}\n", "while (a) {\n  // Spin until a clears.\n}\n"),
    ("bare-block", "{}\n", "{\n  // A scope with nothing in it.\n}\n"),
    ("namespace", "namespace N {}\n", "namespace N {\n  // Filled in by merging.\n}\n"),
    (
        "ambient-module",
        'declare module "m" {}\n',
        'declare module "m" {\n  // Augmented elsewhere.\n}\n',
    ),
    (
        "nested",
        "export const a = () => {\n  if (x) {}\n};\n",
        "export const a = () => {\n  if (x) {\n    // Nothing to do.\n  }\n};\n",
    ),
]


@pytest.mark.parametrize(
    "before,after", [c[1:] for c in EMPTY_BODIES], ids=[c[0] for c in EMPTY_BODIES]
)
def test_a_comment_in_an_empty_body_passes(
    ts_repo, commit_then_edit, before: str, after: str
) -> None:
    r = commit_then_edit(ts_repo, "e.ts", before, after)
    assert r.ok and r.method == "ts-printer", r.detail


def test_a_comment_in_an_empty_body_passes_in_every_script_kind(ts_repo, commit_then_edit) -> None:
    before, after = "export const a = () => {};\n", "export const a = () => {\n  // c\n};\n"
    for rel in ("e.tsx", "e.js", "e.jsx", "e.mjs", "e.cts"):
        r = commit_then_edit(ts_repo, rel, before, after)
        assert r.ok, (rel, r.detail)


EMPTY_BODY_CODE_CHANGES = [
    ("statement", "export function noop() {}\n", "export function noop() {\n  go();\n}\n"),
    (
        "statement-and-comment",
        "export function noop() {}\n",
        "export function noop() {\n  // Now it goes.\n  go();\n}\n",
    ),
    ("catch-statement", "try { f(); } catch (e) {}\n", "try { f(); } catch (e) {\n  g();\n}\n"),
    ("arrow-to-object", "export const a = () => {};\n", "export const a = () => ({});\n"),
    (
        "arrow-to-object-and-comment",
        "export const a = () => {};\n",
        "export const a = () => ({\n  // c\n});\n",
    ),
    ("block-to-empty-statement", "for (;;) {}\n", "for (;;);\n"),
    (
        "namespace-member",
        "namespace N {}\n",
        "namespace N {\n  export const x = 1;\n}\n",
    ),
]


@pytest.mark.parametrize(
    "before,after",
    [c[1:] for c in EMPTY_BODY_CODE_CHANGES],
    ids=[c[0] for c in EMPTY_BODY_CODE_CHANGES],
)
def test_a_code_change_in_an_empty_body_still_fails(
    ts_repo, commit_then_edit, before: str, after: str
) -> None:
    r = commit_then_edit(ts_repo, "e.ts", before, after)
    assert not r.ok and r.method == "ts-printer" and "code changed" in r.detail, (
        r.method,
        r.detail,
    )


# --- JSX: {/* c */} is an empty child expression the compiler discards ---------------------------

JSX_COMMENTS = [
    (
        "inline",
        "export const C = () => <div><A /></div>;\n",
        "export const C = () => <div>{/* the A */}<A /></div>;\n",
    ),
    (
        "own-line",
        "export const C = () => (\n  <div>\n    <A />\n  </div>\n);\n",
        "export const C = () => (\n  <div>\n    {/* the A */}\n    <A />\n  </div>\n);\n",
    ),
    (
        "between-siblings",
        "export const C = () => (\n  <div>\n    <A />\n    <B />\n  </div>\n);\n",
        "export const C = () => (\n  <div>\n    <A />\n    {/* B */}\n    <B />\n  </div>\n);\n",
    ),
    (
        "last-child",
        "export const C = () => (\n  <ul>\n    <li />\n  </ul>\n);\n",
        "export const C = () => (\n  <ul>\n    <li />\n    {/* end of list */}\n  </ul>\n);\n",
    ),
    (
        "fragment",
        "export const C = () => <><A /></>;\n",
        "export const C = () => <>{/* the A */}<A /></>;\n",
    ),
    (
        "nested",
        "export const C = () => <div><p><A /></p></div>;\n",
        "export const C = () => <div><p>{/* the A */}<A /></p>{/* end */}</div>;\n",
    ),
    (
        "empty-element",
        "export const C = () => <div></div>;\n",
        "export const C = () => <div>{/* nothing here */}</div>;\n",
    ),
]


@pytest.mark.parametrize(
    "before,after", [c[1:] for c in JSX_COMMENTS], ids=[c[0] for c in JSX_COMMENTS]
)
def test_a_jsx_child_comment_passes(ts_repo, commit_then_edit, before: str, after: str) -> None:
    r = commit_then_edit(ts_repo, "c.tsx", before, after)
    assert r.ok and r.method == "ts-printer", r.detail


def test_a_jsx_child_comment_passes_in_a_jsx_file(ts_repo, commit_then_edit) -> None:
    r = commit_then_edit(
        ts_repo,
        "c.jsx",
        "export const C = () => <div><A /></div>;\n",
        "export const C = () => <div>{/* the A */}<A /></div>;\n",
    )
    assert r.ok, r.detail


JSX_CODE_CHANGES = [
    (
        "element-swapped",
        "export const C = () => <div><A /></div>;\n",
        "export const C = () => <div>{/* the A */}<B /></div>;\n",
    ),
    (
        "text-changed",
        "export const C = () => <p>hi</p>;\n",
        "export const C = () => <p>{/* greeting */}hello</p>;\n",
    ),
    (
        "text-added",
        "export const C = () => <p><A /></p>;\n",
        "export const C = () => <p>{/* c */}<A />!</p>;\n",
    ),
    (
        "expression-swapped",
        "export const C = () => <p>{x}</p>;\n",
        "export const C = () => <p>{/* c */}{y}</p>;\n",
    ),
    (
        "expression-emptied",
        "export const C = () => <p>{x}</p>;\n",
        "export const C = () => <p>{}</p>;\n",
    ),
    (
        "attribute-changed",
        'export const C = () => <div id="a"><A /></div>;\n',
        'export const C = () => <div id="b">{/* c */}<A /></div>;\n',
    ),
    (
        # The newline between the words is the space between them; a comment there splits the
        # text into two children and the words run together.
        "comment-splits-text",
        "export const C = () => (\n  <p>\n    hello\n    world\n  </p>\n);\n",
        "export const C = () => (\n  <p>\n    hello\n    {/* c */}\n    world\n  </p>\n);\n",
    ),
    (
        "spaces-around-comment",
        "export const C = () => <p>a <A /></p>;\n",
        "export const C = () => <p>a {/* c */} <A /></p>;\n",
    ),
    (
        "child-removed",
        "export const C = () => <div><A /><B /></div>;\n",
        "export const C = () => <div>{/* c */}<A /></div>;\n",
    ),
]


@pytest.mark.parametrize(
    "before,after", [c[1:] for c in JSX_CODE_CHANGES], ids=[c[0] for c in JSX_CODE_CHANGES]
)
def test_a_code_change_next_to_a_jsx_comment_still_fails(
    ts_repo, commit_then_edit, before: str, after: str
) -> None:
    r = commit_then_edit(ts_repo, "c.tsx", before, after)
    assert not r.ok and r.method == "ts-printer" and "code changed" in r.detail, (
        r.method,
        r.detail,
    )


# --- JSX text is compared as it renders, one child per text node -------------------------------
#
# JSX cooks whitespace per text node: lines are trimmed at their inner edges, whitespace-only
# lines are dropped, and the rest are joined with one space. A comment that splits one text node
# into two changes what renders even though the raw characters around it are the same, so the
# printer must compare cooked text node by node, never the concatenated source.

JSX_TEXT_CHANGES = [
    (
        # "Hello world" becomes "Hello", "world": the line break was the space.
        "split-after-word",
        "export const A = () => <p>Hello\n  world</p>;\n",
        "export const A = () => <p>Hello{/* greeting */}\n  world</p>;\n",
    ),
    (
        "split-before-word",
        "export const A = () => <p>Hello\n  world</p>;\n",
        "export const A = () => <p>Hello\n  {/* greeting */}world</p>;\n",
    ),
    (
        # The DOM text is the same, but the children array goes from ["a ", x] to ["a", " ", x].
        "split-before-space",
        "export const A = () => <p>a {x}</p>;\n",
        "export const A = () => <p>a{/* c */} {x}</p>;\n",
    ),
    (
        # One child "a b" becomes two, "a " and "b".
        "split-inside-one-line-run",
        "export const A = () => <p>a b</p>;\n",
        "export const A = () => <p>a {/* c */}b</p>;\n",
    ),
    (
        # "Hello" becomes "Hello ": the space before the comment is now the end of the last line.
        "space-left-before-trailing-comment",
        "export const A = () => (\n  <p>\n    Hello\n  </p>\n);\n",
        "export const A = () => (\n  <p>\n    Hello {/* c */}\n  </p>\n);\n",
    ),
    (
        # A tab inside a line renders as a tab under TypeScript and as a space under Babel.
        "tab-for-space",
        "export const A = () => <p>a b</p>;\n",
        "export const A = () => <p>a\tb</p>;\n",
    ),
    (
        # TypeScript trims U+00A0 at a line edge; the reflowed line no longer has that edge.
        "nbsp-at-line-edge",
        "export const A = () => <p>a\u00a0 b</p>;\n",
        "export const A = () => <p>a\u00a0\nb</p>;\n",
    ),
    (
        # Babel decodes &#32; before it trims lines, so the reflow changes "a b" to "a  b" there.
        "entity-space-at-line-edge",
        "export const A = () => <p>a&#32;\nb</p>;\n",
        "export const A = () => <p>a&#32; b</p>;\n",
    ),
    (
        "text-changed",
        "export const A = () => <p>\n  Hello world\n</p>;\n",
        "export const A = () => <p>\n  {/* c */}\n  Hello, world\n</p>;\n",
    ),
]


@pytest.mark.parametrize("rel", ["c.tsx", "c.jsx", "c.js"])
@pytest.mark.parametrize(
    "before,after", [c[1:] for c in JSX_TEXT_CHANGES], ids=[c[0] for c in JSX_TEXT_CHANGES]
)
def test_a_comment_that_changes_rendered_jsx_text_fails(
    ts_repo, commit_then_edit, rel: str, before: str, after: str
) -> None:
    r = commit_then_edit(ts_repo, rel, before, after)
    assert not r.ok and r.method == "ts-printer" and "code changed" in r.detail, (
        r.method,
        r.detail,
    )


# Text is compared through an encoding of its cooked value. No source may print the same as that
# encoding: a child expression, an element, or text that spells the encoding out.
JSX_ENCODING_COLLISIONS = [
    (
        "text-to-array",
        "export const A = () => <p>Hello</p>;\n",
        'export const A = () => <p>{["Hello", "Hello"]}</p>;\n',
    ),
    (
        "entity-text-to-array",
        "export const A = () => <p>a&amp;b</p>;\n",
        'export const A = () => <p>{["a&amp;b", "a&amp;b", "a&amp;b"]}</p>;\n',
    ),
    (
        "trailing-space-text-to-array",
        "export const A = () => <p>Hello </p>;\n",
        'export const A = () => <p>{["Hello ", "Hello "]}</p>;\n',
    ),
    (
        "array-to-text",
        'export const A = () => <p>{["x", "x"]}</p>;\n',
        "export const A = () => <p>x</p>;\n",
    ),
    (
        "text-to-string-child",
        "export const A = () => <p>Hello</p>;\n",
        'export const A = () => <p>{"Hello"}</p>;\n',
    ),
    (
        "text-to-private-name-tag",
        "export const A = () => <p>Hello</p>;\n",
        'export const A = () => <p><#text ["Hello","Hello"]></p>;\n',
    ),
    (
        "text-to-empty-expression",
        "export const A = () => <p>Hello</p>;\n",
        "export const A = () => <p>{}</p>;\n",
    ),
]


@pytest.mark.parametrize("rel", ["c.tsx", "c.jsx", "c.js"])
@pytest.mark.parametrize(
    "before,after",
    [c[1:] for c in JSX_ENCODING_COLLISIONS],
    ids=[c[0] for c in JSX_ENCODING_COLLISIONS],
)
def test_code_cannot_print_as_encoded_jsx_text(
    ts_repo, commit_then_edit, rel: str, before: str, after: str
) -> None:
    r = commit_then_edit(ts_repo, rel, before, after)
    assert not r.ok and r.method == "ts-printer", (r.method, r.detail)


JSX_TEXT_SAME = [
    (
        "comment-alone-between-elements",
        "export const A = () => (\n  <div>\n    <B />\n    <C />\n  </div>\n);\n",
        "export const A = () => (\n  <div>\n    <B />\n    {/* C */}\n    <C />\n  </div>\n);\n",
    ),
    (
        "comment-alone-after-text",
        "export const A = () => (\n  <p>\n    Hello\n  </p>\n);\n",
        "export const A = () => (\n  <p>\n    Hello\n    {/* c */}\n  </p>\n);\n",
    ),
    (
        "comment-alone-before-text",
        "export const A = () => (\n  <p>\n    Hello world\n  </p>\n);\n",
        "export const A = () => (\n  <p>\n    {/* c */}\n    Hello world\n  </p>\n);\n",
    ),
    (
        "comment-at-end-of-one-line-run",
        "export const A = () => <p>Hello</p>;\n",
        "export const A = () => <p>Hello{/* c */}</p>;\n",
    ),
    (
        "comment-between-text-and-element",
        "export const A = () => <p>Hello <b>x</b></p>;\n",
        "export const A = () => <p>Hello {/* c */}<b>x</b></p>;\n",
    ),
    (
        "comment-alone-next-to-entity-text",
        "export const A = () => (\n  <p>\n    Fish &amp; chips\n  </p>\n);\n",
        "export const A = () => (\n  <p>\n    {/* c */}\n    Fish &amp; chips\n  </p>\n);\n",
    ),
    (
        # Re-indenting a multi-line text renders the same text.
        "reindented-text",
        "export const A = () => (\n  <p>\n    Hello\n    world\n  </p>\n);\n",
        "export const A = () => (\n  <p>\n      Hello\n      world\n  </p>\n);\n",
    ),
]


@pytest.mark.parametrize("rel", ["c.tsx", "c.jsx", "c.js"])
@pytest.mark.parametrize(
    "before,after", [c[1:] for c in JSX_TEXT_SAME], ids=[c[0] for c in JSX_TEXT_SAME]
)
def test_a_comment_that_keeps_rendered_jsx_text_passes(
    ts_repo, commit_then_edit, rel: str, before: str, after: str
) -> None:
    r = commit_then_edit(ts_repo, rel, before, after)
    assert r.ok and r.method == "ts-printer", r.detail


# --- the compiler is looked up from explicit candidates, never by walking up --------------------


@pytest.fixture
def real_ts() -> Path:
    """The installed typescript package, which the fake compilers below wrap."""
    root = verify._npm_global_root()
    real = Path(root, "typescript") if root else None
    if real is None or not real.is_dir() or verify.node_binary() is None:
        _unavailable("node + typescript not available (install with: npm install -g typescript)")
    assert real is not None
    return real


def _version_of(package: Path) -> str:
    return json.loads((package / "package.json").read_text(encoding="utf-8"))["version"]


#: Makes every pair of files print equal: a compiler that would pass any code change.
ALWAYS_EQUAL = "ts.createPrinter = () => ({ printFile: () => '' });"


def _fake_typescript(real: Path, where: Path, version: str, patch: str = "") -> Path:
    """Write ``where/node_modules/typescript``: the real compiler, relabelled and patched.

    Returns ``where``, the candidate directory that holds it.
    """
    package = where / "node_modules" / "typescript"
    package.mkdir(parents=True)
    manifest = {"name": "typescript", "version": version, "main": "index.js"}
    (package / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "index.js").write_text(
        f"const ts = Object.assign({{}}, require({json.dumps(str(real))}));\n"
        f"ts.version = {json.dumps(version)};\n"
        f"{patch}\n"
        "module.exports = ts;\n",
        encoding="utf-8",
    )
    return where


def _only_explicit_candidates(monkeypatch) -> None:
    monkeypatch.delenv("DOCUMENT_REPO_TS_PATHS", raising=False)
    monkeypatch.setattr(verify, "_npm_global_root", lambda: None)


def test_a_compiler_above_the_repo_root_is_never_executed(
    make_repo, real_ts, monkeypatch, tmp_path
) -> None:
    # tmp_path is the repo's parent. Node's require.resolve would walk up into it and run a
    # compiler that says every edit is comment-only.
    repo = make_repo({"m.ts": BASE})
    _fake_typescript(real_ts, tmp_path, "0.0.0-above-the-root", ALWAYS_EQUAL)
    _only_explicit_candidates(monkeypatch)
    r = _edit(repo, "m.ts", BASE.replace("a + b", "a - b"))
    assert not r.ok and r.method == "none" and r.detail == TS_MISSING, (r.method, r.detail)
    assert not typescript_available(repo)


def test_an_explicit_path_outranks_a_compiler_above_the_repo_root(
    make_repo, real_ts, monkeypatch, tmp_path
) -> None:
    repo = make_repo({"m.ts": BASE})
    _fake_typescript(real_ts, tmp_path, "0.0.0-above-the-root", ALWAYS_EQUAL)
    monkeypatch.setenv("DOCUMENT_REPO_TS_PATHS", str(real_ts))  # the package directory itself
    monkeypatch.setattr(verify, "_npm_global_root", lambda: None)
    changed = _edit(repo, "m.ts", BASE.replace("a + b", "a - b"))
    assert not changed.ok and "code changed" in changed.detail, (changed.method, changed.detail)
    assert _edit(repo, "m.ts", "// note\n" + BASE).ok


def test_the_nearest_compiler_wins(make_repo, real_ts, monkeypatch) -> None:
    repo = make_repo({"packages/web/src/a.ts": BASE, "packages/api/b.ts": BASE})
    _fake_typescript(real_ts, repo, "0.0.1-root")
    _fake_typescript(real_ts, repo / "packages/web", "0.0.2-web")
    _only_explicit_candidates(monkeypatch)
    web = _edit(repo, "packages/web/src/a.ts", "// note\n" + BASE)
    assert web.ok and web.detail == "ts-printer (typescript 0.0.2-web)", (web.method, web.detail)
    api = _edit(repo, "packages/api/b.ts", "// note\n" + BASE)
    assert api.ok and api.detail == "ts-printer (typescript 0.0.1-root)", (api.method, api.detail)


def test_candidates_are_tried_repo_then_env_then_global(
    make_repo, real_ts, monkeypatch, tmp_path
) -> None:
    repo = make_repo({"m.ts": BASE})
    env = _fake_typescript(real_ts, tmp_path / "env", "0.0.3-env")
    in_repo = _fake_typescript(real_ts, repo, "0.0.1-root")
    monkeypatch.setenv("DOCUMENT_REPO_TS_PATHS", str(env))
    # The global root is the real compiler's own directory, so its version is the real one.
    monkeypatch.setattr(verify, "_npm_global_root", lambda: str(real_ts.parent))
    assert _edit(repo, "m.ts", "// a\n" + BASE).detail == "ts-printer (typescript 0.0.1-root)"
    shutil.rmtree(in_repo / "node_modules")
    assert _edit(repo, "m.ts", "// b\n" + BASE).detail == "ts-printer (typescript 0.0.3-env)"
    shutil.rmtree(env / "node_modules")
    last = _edit(repo, "m.ts", "// c\n" + BASE)
    assert last.detail == f"ts-printer (typescript {_version_of(real_ts)})", last.detail


def test_a_compiler_that_cannot_load_is_an_error_not_a_fall_through(
    make_repo, real_ts, monkeypatch
) -> None:
    # The nearest compiler is broken and a good one is still reachable (the global root): the
    # run must fail, not quietly use the other one.
    repo = make_repo({"m.ts": BASE})
    _fake_typescript(real_ts, repo, "0.0.0-broken", "throw new Error('broken install');")
    monkeypatch.delenv("DOCUMENT_REPO_TS_PATHS", raising=False)
    monkeypatch.setattr(verify, "_npm_global_root", lambda: str(real_ts.parent))
    r = _edit(repo, "m.ts", "// c\n" + BASE)
    assert not r.ok and r.method == "ts-printer", (r.method, r.detail)
    assert "broken install" in r.detail and "printer failed" in r.detail, r.detail


def test_a_directory_that_is_not_the_typescript_package_is_never_loaded(
    make_repo, monkeypatch, tmp_path
) -> None:
    # A candidate that is not a project directory or a node_modules directory is taken to be the
    # package itself only if its package.json says so. An env entry that names some other
    # project (with a "main" that would say every edit is comment-only) must not be executed.
    repo = make_repo({"m.ts": BASE})
    other = tmp_path / "other-project"
    other.mkdir()
    (other / "package.json").write_text(
        json.dumps({"name": "other-project", "version": "1.0.0", "main": "index.js"}),
        encoding="utf-8",
    )
    (other / "index.js").write_text(
        "module.exports = { version: '1.0.0-impostor', ScriptKind: {}, ScriptTarget: {},\n"
        "  NewLineKind: {}, createPrinter: () => ({ printFile: () => '' }),\n"
        "  createSourceFile: () => ({ parseDiagnostics: [] }) };\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DOCUMENT_REPO_TS_PATHS", str(other))
    monkeypatch.setattr(verify, "_npm_global_root", lambda: None)
    r = _edit(repo, "m.ts", BASE.replace("a + b", "a - b"))
    assert not r.ok and r.method == "none" and r.detail == TS_MISSING, (r.method, r.detail)


def test_search_paths_never_go_above_the_repo_root(make_repo, monkeypatch) -> None:
    repo = make_repo({"a/b/c.ts": BASE})
    monkeypatch.delenv("DOCUMENT_REPO_TS_PATHS", raising=False)
    monkeypatch.setattr(verify, "_npm_global_root", lambda: None)
    assert verify.ts_search_paths(repo, "a/b/c.ts") == [
        str(repo / "a/b"),
        str(repo / "a"),
        str(repo),
    ]
    # A path that climbs out of the work tree is not a directory the walk may visit.
    assert verify.ts_search_paths(repo, "../outside/x.ts") == [str(repo)]
    assert verify.ts_search_paths(repo, "a/../../x.ts") == [str(repo)]
    assert verify.ts_search_paths(repo, "a/../x.ts") == [str(repo)]


def test_search_paths_drop_repeats_and_keep_the_first_place(
    make_repo, monkeypatch, tmp_path
) -> None:
    repo = make_repo({"pkg/a.ts": BASE})
    env = tmp_path / "env"
    monkeypatch.setenv(
        "DOCUMENT_REPO_TS_PATHS",
        os.pathsep.join([str(repo), str(env), str(repo / "pkg"), str(env)]),
    )
    monkeypatch.setattr(verify, "_npm_global_root", lambda: str(env))
    assert verify.ts_search_paths(repo, "pkg/a.ts") == [str(repo / "pkg"), str(repo), str(env)]


# --- the global npm root is asked from a neutral directory --------------------------------------


def _record_npm_cwd(monkeypatch) -> list[object]:
    cwds: list[object] = []

    class Done:
        returncode = 0
        stdout = "/global/root\n"

    def fake_run(cmd, **kwargs):
        cwds.append(kwargs.get("cwd", "<inherited>"))
        return Done()

    verify._npm_global_root.cache_clear()
    monkeypatch.setattr(verify.shutil, "which", lambda name: "/bin/npm")
    monkeypatch.setattr(verify.subprocess, "run", fake_run)
    return cwds


def test_global_root_is_asked_from_the_home_directory_not_the_repo(
    make_repo, monkeypatch, tmp_path
) -> None:
    # `npm root -g` reads the project's .npmrc, so it must not run in the target repo, which is
    # where the CLI is usually started.
    repo = make_repo({"m.ts": BASE})
    home = tmp_path / "home"
    home.mkdir()
    for var in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(var, str(home))
    monkeypatch.chdir(repo)
    cwds = _record_npm_cwd(monkeypatch)
    try:
        assert verify._npm_global_root() == "/global/root"
    finally:
        verify._npm_global_root.cache_clear()
    assert cwds == [str(home)]


def test_global_root_falls_back_to_the_tool_directory_without_a_home(monkeypatch, tmp_path) -> None:
    for var in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(var, str(tmp_path / "missing"))
    cwds = _record_npm_cwd(monkeypatch)
    try:
        verify._npm_global_root()
    finally:
        verify._npm_global_root.cache_clear()
    assert cwds == [str(Path(verify.__file__).parent)]
    assert Path(cwds[0]).is_dir()


# --- the compiler's version is part of the evidence ---------------------------------------------


def test_the_compiler_version_is_recorded_on_success(ts_repo, real_ts) -> None:
    r = _edit(ts_repo, "m.ts", "// note\n" + BASE)
    assert r.ok and r.method == "ts-printer"
    assert r.detail == f"ts-printer (typescript {_version_of(real_ts)})", r.detail
    assert _printer_json(ts_repo, "m.ts", BASE, BASE)["version"] == _version_of(real_ts)


def test_a_failed_proof_does_not_claim_a_compiler_version(ts_repo) -> None:
    r = _edit(ts_repo, "m.ts", BASE.replace("a + b", "a - b"))
    assert not r.ok and "typescript" not in r.detail.lower(), r.detail


# --- the printer refuses a compiler that hides its parse errors ---------------------------------


@pytest.mark.parametrize(
    "patch",
    [
        "delete sf.parseDiagnostics;",
        "sf.parseDiagnostics = undefined;",
        "sf.parseDiagnostics = { length: 0 };",
        "sf.parseDiagnostics = '';",
        "sf.parseDiagnostics = 0;",
    ],
    ids=["deleted", "undefined", "array-like-object", "empty-string", "number"],
)
def test_a_compiler_without_a_diagnostics_array_fails_closed(
    make_repo, real_ts, monkeypatch, tmp_path, patch: str
) -> None:
    # A future compiler may rename or reshape parseDiagnostics. Anything that is not an array
    # must fail the run: `.length` of an array-like or a string reads as "no errors".
    repo = make_repo({"m.ts": BASE})
    fake = _fake_typescript(
        real_ts,
        tmp_path / "fake",
        "0.0.0-no-diagnostics",
        "const create = ts.createSourceFile;\n"
        f"ts.createSourceFile = (...args) => {{ const sf = create(...args); {patch} return sf; }};",
    )
    monkeypatch.setattr(verify, "ts_search_paths", lambda repo, rel=None: [str(fake)])
    r = _edit(repo, "m.ts", "// c\n" + BASE)
    assert not r.ok and r.method == "ts-printer", (r.method, r.detail)
    assert "does not expose parseDiagnostics" in r.detail, r.detail
