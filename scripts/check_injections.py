#!/usr/bin/env python3
"""
Dynamic-injection linter (stdlib only) -- ADR-0011 R4 enforcement.

A textual grep for the `!` + backtick marker finds ~74 occurrences under
`plugins/`, but only a fraction of those are actually live in an executable
surface: the harness's pre-pass (`Jds`) blanks an inline-code span *unless*
the character immediately before its opening backtick is `!` or a backtick.
That rule is inverted from what looks "correctly escaped", so a grep-based
gate is wrong in both directions at once -- see
`docs/adr/0011-dynamic-injection-doctrine.md` (R4) for the full case, the
harness functions recovered verbatim from Claude Code 2.1.220, and the
LIVE/INERT table this script's --self-test is checked against.

This script REPLAYS the harness's own matching behavior instead of
approximating it with a pattern:

  - `jds()` ports `Jds` -- the pre-pass that blanks inline-code spans not
    preceded by `!` or a backtick.
  - `cfo()` ports `Cfo` -- the extractor. It unions two matchers:
      * `soy` -- a fenced block whose info string is exactly `!`, matched
        against the RAW text. This form is never pre-passed at all (F1),
        so it is live regardless of what surrounds it (including inside
        material an author believes is a quoted example).
      * `aoy` -- the inline `!`cmd`` marker, matched against `jds(text)`,
        and only where the character before the `!` is start-of-line or
        whitespace. Python's `re` module cannot express the harness's
        variable-width lookbehind `(?<=^|\\s)` directly (JS supports it,
        Python does not), so this is replicated with an explicit
        preceding-character check instead -- see `_preceded_by_bol_or_ws`.

For every live injection found in an executable surface (a skill or
command body -- `references/**` and `deprecated/**` are excluded because
the loader never expands them, ADR-0011 "Neutral" consequences), this
script checks two load-time preconditions (ADR-0011 F3/F4):

  1. GUARDED -- the command cannot abort skill load with a non-zero exit.
     This is necessarily a heuristic (proving arbitrary shell scripts
     always exit 0 is undecidable) scoped to the guard idioms actually
     used in this repo: an explicit top-level `||` fallback branch, or a
     pipeline/statement whose *final* stage is a command that exits 0
     regardless of upstream failure or empty input (`awk`, `head`, `wc`,
     `cat`, `true`, `:`) or that has no plausible failure mode of its own
     (`pwd`, `echo`). See `_SAFE_TERMINAL_COMMANDS`.
  2. GRANTED -- every external binary the command invokes appears in the
     component's `allowed-tools` (either a scoped `Bash(name:*)` grant or
     an unscoped `Bash` wildcard). Shell builtins that spawn no subprocess
     (`echo`, `true`, `cd`, `pwd`, ...) are exempted -- see `_BUILTINS`,
     and ADR-0011 F4's own examples (git, grep, awk, tail) are all
     external binaries, never builtins.

Usage:
    python3 scripts/check_injections.py              # scan plugins/, exit 0/1
    python3 scripts/check_injections.py --self-test   # negative-test the checker itself

Exit codes:
    0 - No unguarded or ungranted live injections found (or self-test passed)
    1 - At least one violation found (or self-test failed)
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
ADR_PATH = REPO_ROOT / "docs" / "adr" / "0011-dynamic-injection-doctrine.md"

# ---------------------------------------------------------------------------
# The pre-pass and extractor, ported from Claude Code 2.1.220's `Jds`/`Cfo`
# (recovered verbatim in docs/adr/0011-dynamic-injection-doctrine.md).
# ---------------------------------------------------------------------------

# Jds: /`[^`\n]+`/g -- a single-backtick inline-code span (no fence awareness).
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")

# soy: fenced block whose info string is exactly "!", matched against RAW text.
# JS: new RegExp("```" + "!" + "\\s*\\n?([\\s\\S]*?)\\n?" + "```", "g")
_SOY_RE = re.compile(r"```!\s*\n?([\s\S]*?)\n?```")

# aoy core: JS `(?<=^|\s)!`([^`]+)`` with the variable-width lookbehind
# stripped out -- Python's `re` requires fixed-width lookbehind, so the
# `(?<=^|\s)` boundary check is done manually via `_preceded_by_bol_or_ws`
# against the match's own start position instead of being part of the regex.
_AOY_CORE_RE = re.compile(r"!`([^`]+)`")


def jds(text: str) -> str:
    """Port of the harness's `Jds` pre-pass.

    Blanks every single-line inline-code span to same-length whitespace,
    UNLESS the character immediately before its opening backtick is `!` or
    a backtick. Blanking preserves length so a blanked span can never
    contribute an `!` for the inline extractor to anchor on.
    """

    def repl(m: re.Match[str]) -> str:
        start = m.start()
        prev = text[start - 1] if start > 0 else ""
        if prev == "!" or prev == "`":
            return m.group(0)
        return "`" + (" " * (len(m.group(0)) - 2)) + "`"

    return _INLINE_CODE_RE.sub(repl, text)


def _preceded_by_bol_or_ws(text: str, idx: int) -> bool:
    """Replicates `(?<=^|\\s)` at position `idx` without lookbehind."""
    if idx == 0:
        return True
    return re.match(r"\s", text[idx - 1]) is not None


@dataclass
class Injection:
    raw: str
    command: str
    start: int  # character offset into the RAW file text
    kind: str  # "fence" (soy, raw-text) or "inline" (aoy, post-Jds)


def cfo(text: str) -> list[Injection]:
    """Port of the harness's `Cfo` extractor: union of `soy` and `aoy`.

    `soy` runs against the raw text unconditionally (F1 -- a `!`-fenced
    block is never pre-passed). `aoy` runs against `jds(text)`, and only
    if the raw text contains the literal substring "!`" at all -- this
    mirrors the harness's own fast-path (`e.includes("!" + "`")`), which is
    safe to replay because `Jds` blanking can only remove interior
    characters between existing backtick pairs, never introduce a new `!`
    adjacent to a backtick outside one.
    """
    injections: list[Injection] = []

    for m in _SOY_RE.finditer(text):
        cmd = (m.group(1) or "").strip()
        if cmd:
            injections.append(Injection(raw=m.group(0), command=cmd, start=m.start(), kind="fence"))

    if "!`" in text:
        transformed = jds(text)
        for m in _AOY_CORE_RE.finditer(transformed):
            if not _preceded_by_bol_or_ws(transformed, m.start()):
                continue
            cmd = (m.group(1) or "").strip()
            if cmd:
                injections.append(
                    Injection(raw=m.group(0), command=cmd, start=m.start(), kind="inline")
                )

    return injections


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


# ---------------------------------------------------------------------------
# Guard heuristic (F3: a live injection must exit 0 everywhere).
#
# This is deliberately scoped to the guard idioms this repo actually uses
# (ADR-0011 R2's `2>/dev/null || echo "(sentinel)"` idiom, and the
# pipe-terminated form ship's diff-size line uses instead). It is not a
# general shell-semantics prover -- see the module docstring.
# ---------------------------------------------------------------------------

# Commands whose exit status, as the FINAL stage of a top-level pipeline or
# statement, does not depend on upstream failure or on stdin content under
# normal (non-crash) operation. A single bare command is a pipeline of
# length 1, so this list also covers "no plausible failure mode of its own"
# commands like `pwd`/`echo` when used unguarded and alone.
_SAFE_TERMINAL_COMMANDS = {"awk", "head", "wc", "cat", "true", ":", "pwd", "echo"}

# Shell builtins that spawn no subprocess -- ADR-0011 F4's examples (git,
# grep, awk, tail) are all external binaries; none of these appear in any
# `allowed-tools` grant anywhere in this repo, including on skills whose
# injections use them unguarded (ship/clear-prep's `|| echo` fallback).
_BUILTINS = {
    "echo",
    "true",
    "false",
    ":",
    "cd",
    "pwd",
    "read",
    "export",
    "shift",
    "exit",
    "return",
    "test",
    "[",
}


def _split_top_level(command: str) -> tuple[list[str], bool]:
    """Split a shell command/script into top-level segments, quote-aware.

    Splits on `|`, `||`, `&&`, `;`, and newlines (bash statement/pipeline
    separators) whenever they occur outside single or double quotes.
    Returns (segments, saw_top_level_or) -- `saw_top_level_or` is True iff
    a literal `||` occurred outside quotes anywhere in the command.
    """
    segments: list[str] = []
    buf: list[str] = []
    saw_or = False
    quote: str | None = None
    i, n = 0, len(command)
    while i < n:
        c = command[i]
        if quote:
            buf.append(c)
            if c == "\\" and quote == '"' and i + 1 < n:
                buf.append(command[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in ("'", '"'):
            quote = c
            buf.append(c)
            i += 1
            continue
        if command[i : i + 2] == "||":
            segments.append("".join(buf))
            buf = []
            saw_or = True
            i += 2
            continue
        if command[i : i + 2] == "&&":
            segments.append("".join(buf))
            buf = []
            i += 2
            continue
        if c in ("|", ";", "\n"):
            segments.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    segments.append("".join(buf))
    return [s.strip() for s in segments if s.strip()], saw_or


def _first_word(segment: str) -> str:
    stripped = segment.strip()
    if not stripped:
        return ""
    return stripped.split(None, 1)[0]


def is_guarded(command: str) -> bool:
    """True if `command` cannot plausibly abort skill load (F3)."""
    segments, saw_or = _split_top_level(command)
    if saw_or:
        return True
    if not segments:
        return True
    return _first_word(segments[-1]) in _SAFE_TERMINAL_COMMANDS


def referenced_binaries(command: str) -> set[str]:
    """External binaries invoked anywhere in `command`, builtins excluded."""
    segments, _ = _split_top_level(command)
    binaries: set[str] = set()
    for seg in segments:
        word = _first_word(seg)
        if word and word not in _BUILTINS:
            binaries.add(word)
    return binaries


# ---------------------------------------------------------------------------
# allowed-tools grant parsing (F4).
# ---------------------------------------------------------------------------

_BASH_SCOPED_RE = re.compile(r"Bash\(([A-Za-z0-9_.\-]+):[^)]*\)")


def parse_allowed_tools(frontmatter_text: str) -> tuple[bool, set[str]]:
    """Returns (wildcard, granted_binaries) from an `allowed-tools:` line.

    `wildcard=True` means a bare `Bash` token (no parens) grants every
    binary. Otherwise `granted_binaries` holds every name inside a scoped
    `Bash(name:*)` entry.
    """
    m = re.search(r"^allowed-tools:\s*(.+)$", frontmatter_text, re.MULTILINE)
    if not m:
        return False, set()
    value = m.group(1)
    # Strip a trailing inline comment (`  # explanation`), matching the
    # `Bash unscoped: ...` comments used on a few skills in this repo.
    value = re.split(r"\s+#", value, maxsplit=1)[0]

    wildcard = False
    granted: set[str] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if token == "Bash":
            wildcard = True
            continue
        scoped = _BASH_SCOPED_RE.match(token)
        if scoped:
            granted.add(scoped.group(1))
    return wildcard, granted


def split_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return ""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[1]


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    file: Path
    line: int
    command: str
    reason: str  # "unguarded" or "ungranted"
    detail: str


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    live_injections: int = 0


def live_skill_and_command_files(root: Path) -> list[Path]:
    """plugins/*/skills/*/SKILL.md and plugins/*/commands/*.md.

    Deliberately excludes references/** and deprecated/** -- those
    surfaces are read as documentation and never expanded as a skill or
    command body, so a live-looking form there executes nothing today
    (ADR-0011 "Neutral" consequences). Restricting the glob is what keeps
    this a real linter instead of the rejected grep-based gate: a textual
    search finds 74 sites, only 14 of which are live in an executable
    surface.
    """
    files: list[Path] = []
    plugins_dir = root / "plugins"
    if not plugins_dir.is_dir():
        return files
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            files.extend(sorted(skills_dir.glob("*/SKILL.md")))
        commands_dir = plugin_dir / "commands"
        if commands_dir.is_dir():
            files.extend(sorted(commands_dir.glob("*.md")))
    return files


def check_file(path: Path, root: Path) -> tuple[list[Finding], int]:
    text = path.read_text(encoding="utf-8")
    frontmatter = split_frontmatter(text)
    wildcard, granted = parse_allowed_tools(frontmatter)

    findings: list[Finding] = []
    injections = cfo(text)
    for inj in injections:
        line = line_number(text, inj.start)
        rel = path.relative_to(root) if path.is_relative_to(root) else path

        if not is_guarded(inj.command):
            findings.append(
                Finding(
                    file=rel,
                    line=line,
                    command=inj.command,
                    reason="unguarded",
                    detail=(
                        "live injection has no exit-0 guard (no top-level `||` fallback and no "
                        "safe terminal command) -- a non-zero exit aborts skill load (ADR-0011 F3)"
                    ),
                )
            )

        if not wildcard:
            missing = sorted(referenced_binaries(inj.command) - granted)
            if missing:
                findings.append(
                    Finding(
                        file=rel,
                        line=line,
                        command=inj.command,
                        reason="ungranted",
                        detail=(
                            f"live injection calls {missing} not present in `allowed-tools` "
                            "(ADR-0011 F4 -- every binary in an injection pipeline must be granted)"
                        ),
                    )
                )

    return findings, len(injections)


def scan(root: Path) -> ScanResult:
    result = ScanResult()
    for path in live_skill_and_command_files(root):
        findings, count = check_file(path, root)
        result.findings.extend(findings)
        result.files_scanned += 1
        result.live_injections += count
    return result


def report(result: ScanResult) -> int:
    if result.findings:
        print(f"Injection linter FAILED -- {len(result.findings)} issue(s):\n")
        for f in result.findings:
            print(f"  - {f.file}:{f.line} [{f.reason}] `{f.command}`")
            print(f"      {f.detail}")
        print(
            '\nFix by guarding the injection with a `2>/dev/null || echo "(sentinel)"` fallback '
            "(or ending its pipeline in a command that always exits 0, e.g. `awk`), and by adding "
            "every binary it invokes to the component's `allowed-tools` (ADR-0011 R2/F4)."
        )
        return 1

    print(
        f"Injection linter passed: {result.files_scanned} file(s) scanned, "
        f"{result.live_injections} live injection(s), all guarded and granted."
    )
    return 0


# ---------------------------------------------------------------------------
# --self-test
#
# E043's rule applied to itself: a verification guard that can't fail is
# worse than none. This builds deliberately-bad fixtures and asserts the
# checker exits 1 on them, AND asserts it exits 0 on known-good fixtures --
# both directions of the inverted escaping rule, plus the raw-fence form
# that no regex over pre-passed text can see (F1).
# ---------------------------------------------------------------------------


def _adr_table_verdicts() -> list[str]:
    """Extract the 9 'Reality' verdicts (LIVE/INERT), in row order, directly
    from ADR-0011's F2 table -- so if a future edit changes a verdict without
    updating the fixtures below, self-test drift is caught rather than a
    hand-copied constant silently disagreeing with the doctrine it tests
    against (CLAUDE.md: "derive it, don't copy it").
    """
    text = ADR_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    verdicts: list[str] = []
    in_table = False
    for line in lines:
        if line.startswith("| Source form"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        verdict_cell = cells[-1]
        if "LIVE" in verdict_cell:
            verdicts.append("LIVE")
        elif "INERT" in verdict_cell:
            verdicts.append("INERT")
    return verdicts


# The 9 rows of ADR-0011's F2 table, reproduced as literal fixture TEXT (what
# an author would actually type in a SKILL.md source file -- not the ADR's
# own `\!`-neutralized, code-span-wrapped display form, which exists only so
# the ADR doesn't become a live injection site itself). Order matches the
# table exactly; row order here is the "where possible" boundary of
# programmatic derivation -- the LIVE/INERT *verdicts* are still pulled from
# the ADR file itself via `_adr_table_verdicts()`, not hand-copied.
_ADR_ROW_FIXTURES: list[tuple[str, str]] = [
    ("double-backtick wrapper with space padding", "`` !`echo hi` ``"),
    ("single backtick, nested, ragged", "`!`echo hi``"),
    ("bare at the start of a line", "!`echo hi`"),
    ("inside a plain triple-backtick fence", "```text\n!`echo hi`\n```"),
    ("fenced block opened with three backticks and !", "```!\necho hi\n```"),
    ("in a markdown table cell", "| !`echo hi` | description |"),
    ("non-whitespace immediately before the marker", "x!`echo hi`"),
    ("a space between the marker and the backtick", "! `echo hi`"),
    ("a literal backslash before the marker", "\\!`echo hi`"),
]


def _self_test_adr_table() -> list[str]:
    failures: list[str] = []
    verdicts = _adr_table_verdicts()
    if len(verdicts) != len(_ADR_ROW_FIXTURES):
        failures.append(
            f"ADR-0011 F2 table has {len(verdicts)} verdict row(s), but this self-test has "
            f"{len(_ADR_ROW_FIXTURES)} fixture(s) -- the table changed shape; update "
            "_ADR_ROW_FIXTURES in scripts/check_injections.py to match"
        )
        return failures

    for (label, fixture), expected in zip(_ADR_ROW_FIXTURES, verdicts):
        live = bool(cfo(fixture))
        expected_live = expected == "LIVE"
        status = "PASS" if live == expected_live else "FAIL"
        print(f"  [{status}] {expected:<5} {label!r} -> {fixture!r}")
        if live != expected_live:
            failures.append(
                f"row {label!r}: fixture {fixture!r} classified as "
                f"{'LIVE' if live else 'INERT'}, ADR-0011 says {expected}"
            )
    return failures


def _write_fixture_skill(
    root: Path, plugin: str, skill: str, allowed_tools: str, body: str
) -> Path:
    skill_dir = root / "plugins" / plugin / "skills" / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    path = skill_dir / "SKILL.md"
    frontmatter = (
        f"---\nname: {skill}\ndescription: self-test fixture\nallowed-tools: {allowed_tools}\n---\n"
    )
    path.write_text(f"{frontmatter}\n{body}\n", encoding="utf-8")
    return path


def _self_test_fixtures() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="check_injections_selftest_") as tmp:
        root = Path(tmp)

        cases: list[tuple[str, str, str, str, str, bool, str | None]] = [
            # (case name, plugin, skill, allowed-tools, body, expect_exit_0, expected_reason_if_bad)
            (
                "unguarded-but-granted",
                "p",
                "bad-unguarded",
                "Bash(git:*)",
                "!`git status -s`",
                False,
                "unguarded",
            ),
            (
                "guarded-but-ungranted",
                "p",
                "bad-ungranted",
                "Read",
                '!`git status -s 2>/dev/null || echo "(not a git repository)"`',
                False,
                "ungranted",
            ),
            (
                "good-scoped-guard",
                "p",
                "good-scoped",
                "Bash(git:*)",
                '!`git status -s 2>/dev/null || echo "(not a git repository)"`',
                True,
                None,
            ),
            (
                "good-pipe-terminal-awk",
                "p",
                "good-awk",
                "Bash(git:*), Bash(grep:*), Bash(awk:*)",
                "!`git diff HEAD --shortstat 2>/dev/null | grep -oE '[0-9]+' "
                "| awk '{s+=$1} END {print s+0}'`",
                True,
                None,
            ),
            (
                "good-wildcard-bash",
                "p",
                "good-wildcard",
                "Bash, Read, Glob",
                '!`curl -s https://example.invalid 2>/dev/null || echo "unreachable"`',
                True,
                None,
            ),
            (
                "inert-nested-form-not-flagged",
                "p",
                "inert-doc",
                "Read",
                "Dynamic context: `!`git status -s``",
                True,
                None,
            ),
            (
                "raw-fence-form-unguarded",
                "p",
                "bad-fence",
                "Bash(git:*)",
                "```!\ngit status -s\n```",
                False,
                "unguarded",
            ),
        ]

        for name, plugin, skill, allowed_tools, body, expect_pass, expected_reason in cases:
            _write_fixture_skill(root, plugin, skill, allowed_tools, body)
            findings, _ = check_file(
                root / "plugins" / plugin / "skills" / skill / "SKILL.md", root
            )
            passed = len(findings) == 0
            ok = passed == expect_pass
            if ok and not expect_pass and expected_reason is not None:
                ok = any(f.reason == expected_reason for f in findings)
            status = "PASS" if ok else "FAIL"
            reasons = [f.reason for f in findings]
            print(f"  [{status}] {name}: expect_pass={expect_pass} findings={reasons}")
            if not ok:
                failures.append(f"fixture case {name!r} did not classify as expected: {findings}")

        # Full-scan wiring check: a directory containing only the unguarded
        # bad fixture must make `scan()` (the function `main()` actually
        # calls) exit non-zero; a directory containing only good fixtures
        # must exit 0. This is the "wire it in" half of the negative test,
        # not just the per-file classification half above.
        bad_root = Path(tmp) / "bad-tree"
        _write_fixture_skill(bad_root, "p", "bad-unguarded", "Bash(git:*)", "!`git status -s`")
        bad_result = scan(bad_root)
        if not bad_result.findings:
            failures.append(
                "scan() over a tree containing only an unguarded live injection found 0 issues"
            )

        good_root = Path(tmp) / "good-tree"
        _write_fixture_skill(
            good_root,
            "p",
            "good-scoped",
            "Bash(git:*)",
            '!`git status -s 2>/dev/null || echo "(not a git repository)"`',
        )
        good_result = scan(good_root)
        if good_result.findings:
            failures.append(
                "scan() over a tree containing only guarded/granted injections found issues: "
                f"{good_result.findings}"
            )

    return failures


def self_test() -> int:
    print("=== check_injections.py --self-test ===\n")

    print("-- ADR-0011 F2 table (9 rows, verdicts derived from the ADR file) --")
    failures = _self_test_adr_table()

    print(
        "\n-- File-level fixtures (guard + grant classification, inert-not-flagged, raw-fence) --"
    )
    failures += _self_test_fixtures()

    print("\n-- Real repo tree (must be green: ship/clear-prep are already compliant) --")
    real_result = scan(REPO_ROOT)
    real_ok = not real_result.findings
    print(
        f"  [{'PASS' if real_ok else 'FAIL'}] {REPO_ROOT} -> {len(real_result.findings)} finding(s)"
    )
    if not real_ok:
        for f in real_result.findings:
            print(f"      {f.file}:{f.line} [{f.reason}] `{f.command}`")
        failures.append("the real repo tree is not clean -- see findings above")

    print()
    if failures:
        print(f"self-test FAILED -- {len(failures)} problem(s):\n")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("self-test PASSED -- all fixtures classified correctly in both directions.")
    return 0


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Injection linter that replays the harness pre-pass (ADR-0011 R4).",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Negative-test the checker itself against deliberately-bad and known-good fixtures.",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    result = scan(REPO_ROOT)
    return report(result)


if __name__ == "__main__":
    sys.exit(main())
