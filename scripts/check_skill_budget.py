#!/usr/bin/env python3
"""
SKILL.md body-length budget gate (stdlib only) -- issue #238 / IMPLEMENTATION_PLAN.md 7.3.

MOTIVATING DEFECT
-----------------
The house rule "a SKILL.md body stays under 500 lines" has existed since E032 and
was never enforced by anything. Two skill bodies crossed the line in a single
commit -- `evaluate-pipeline-output` and `explain-project` -- in a change whose
own plan budget-checked a *different* file, and one of them grew past the limit
as a side effect of a prior remediation whose replacement blocks were longer
than what they replaced. Nothing anywhere reported it. A rule that only a human
reader enforces is a rule that drifts silently; this script makes it a gate.

WHY THE RULE EXISTS (state this correctly -- a gate that ships explaining itself
with a false premise is worse than one that ships silently)
-----------------------------------------------------------------------------
This budget is an **authoring-quality** rule about progressive disclosure. It is
NOT a context-economy rule and NOT a platform limit:

  * The harness loads a SKILL.md **body** only when the skill is *invoked*. The
    always-loaded surface, present every turn, is the one-line `description`.
  * Trimming a body therefore saves **zero** tokens on every turn that does not
    invoke that skill, and saves them once on a turn that was about to do that
    skill's work anyway.
  * What the budget actually buys is a body the model can follow: instructions
    stay scannable, and bulk (samples, tables, long reference material) moves
    into `references/`, where it is read on demand.

CLAUDE.md carries this corrected wording; keep the two consistent.

RULES
-----
  Rule 1 (body-budget)
      For every in-scope SKILL.md, the **body** -- every line after the closing
      frontmatter delimiter -- MUST be strictly fewer than 500 lines.

BOUNDARY PREDICATE (pinned here so it cannot drift)
---------------------------------------------------
      violation  <=>  body_lines >= BODY_LINE_LIMIT   (BODY_LINE_LIMIT = 500)

  so 499 PASSES, 500 FAILS, 501 FAILS. "Under 500" is read literally. All three
  boundary values are negative-tested in `--self-test`; a boundary bug lives
  entirely in the branch nobody exercises.

WHAT IS MEASURED
----------------
The **body**, because that is what the rule says -- but every message emits BOTH
the body count and the total file line count, so a reader can tell at a glance
which number tripped the gate and how much of the file is frontmatter. The body
is defined mechanically: if line 1 is `---`, the frontmatter ends at the next
line that is exactly `---`, and the body is every line strictly after it. A file
with no parseable frontmatter is measured whole (fail-closed: the conservative
reading), and the finding says so.

Note for anyone comparing against an ad-hoc measurement: `text.split('---', 2)[2]
.splitlines()` returns exactly ONE MORE element than this script's body count.
That extra element is the empty string preceding the newline that terminates the
closing `---` line -- it is not a body line. This script's count is the honest
one; the split-based idiom is conservative by one.

SCOPE
-----
A NON-RECURSIVE glob, `plugins/*/skills/*/SKILL.md`, mirroring the reasoning
already documented in `.github/workflows/validate.yml` ("glob('*/SKILL.md') is
intentional, NOT rglob"). Consequences, all deliberate:

  * `plugins/<p>/skills/<s>/references/*.md` is NOT evaluated -- that is where
    the budget tells you to put the bulk. Gating it would punish the fix.
  * `tests/fixtures/**` is NOT evaluated: it lives outside `plugins/`, and it
    holds deliberately-malformed inputs.
  * A `SKILL.md` nested deeper than `skills/<name>/` is not a discoverable
    skill, so it is not evaluated either.
  * The `commands/` directory of every plugin is OUT OF SCOPE. Commands are
    frozen legacy (ADR-0006): maintained, never extended, and the largest one
    already exceeds 500 lines. Widening this gate to cover them would make it
    red the day it lands, which reddens `main`'s own push build and deadlocks
    every subsequent merge -- the D55 hazard. `--self-test` plants a
    deliberately over-long file under a `commands/` directory and asserts the
    gate does not evaluate it, so this exclusion is a tested property rather
    than a claim in a comment.

Usage:
    python3 scripts/check_skill_budget.py                  # CI: scan the whole repo
    python3 scripts/check_skill_budget.py PATH [PATH ...]  # scan only these paths
    python3 scripts/check_skill_budget.py --filter          # stdin -> in-scope paths
    python3 scripts/check_skill_budget.py --self-test       # negative-test this gate

`--filter` exists so `scripts/pre-commit` can ask THIS script which staged files
are in scope instead of restating the glob in shell. A restated glob is how the
two copies drift apart (CLAUDE.md: "derive it, don't copy it"); both modes here
are backed by the single `in_scope()` predicate, which is itself derived from
`SKILL_GLOB`.

Exit codes:
    0 - every in-scope skill body is under budget (or self-test passed)
    1 - at least one body is at or over the limit (or self-test failed)
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REPO_ROOT = Path(__file__).resolve().parent.parent

# The budget, as an EXCLUSIVE limit: a body of exactly this many lines is a
# violation. See BOUNDARY PREDICATE in the module docstring.
BODY_LINE_LIMIT = 500

# The single source of truth for scope. `in_scope()` is derived from this
# string, and `iter_skill_files()` feeds it straight to `Path.glob`, whose `*`
# never crosses a path separator -- that non-recursiveness is the point.
SKILL_GLOB = "plugins/*/skills/*/SKILL.md"

FRONTMATTER_DELIM = "---"


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


def _glob_matches(glob: str, rel_path: str) -> bool:
    """Segment-wise match where `*` means exactly one path segment.

    Deliberately NOT fnmatch: fnmatch translates `*` to `.*`, which spans `/`,
    so `plugins/*/skills/*/SKILL.md` would also match
    `plugins/p/skills/s/nested/deeper/SKILL.md` -- exactly the recursion this
    gate must not have.
    """
    pattern = glob.split("/")
    parts = rel_path.split("/")
    if len(pattern) != len(parts):
        return False
    return all(pat == "*" or pat == part for pat, part in zip(pattern, parts))


def in_scope(rel_path: str) -> bool:
    """True if a repo-root-relative POSIX path is an evaluated skill body."""
    return _glob_matches(SKILL_GLOB, rel_path.replace("\\", "/").lstrip("./"))


def to_rel(path: Path, root: Path) -> str:
    """Repo-root-relative POSIX form of `path`, for display and scope matching."""
    candidate = path if path.is_absolute() else (root / path)
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        # Outside the root entirely -- cannot be in scope; keep something
        # printable so the skip message names the path the caller passed.
        return candidate.as_posix()


def iter_skill_files(root: Path) -> list[Path]:
    """Every in-scope SKILL.md under `root`, sorted. Non-recursive by construction."""
    return sorted(root.glob(SKILL_GLOB))


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Measurement:
    body_lines: int
    total_lines: int
    frontmatter_lines: int
    has_frontmatter: bool


def measure(text: str) -> Measurement:
    """Split a SKILL.md into frontmatter and body and count both.

    The body is every line strictly AFTER the closing `---`. The newline that
    terminates that delimiter line belongs to the delimiter, not to the body.
    """
    lines = text.splitlines()
    total = len(lines)

    if lines and lines[0].rstrip() == FRONTMATTER_DELIM:
        for index in range(1, total):
            if lines[index].rstrip() == FRONTMATTER_DELIM:
                fm = index + 1
                return Measurement(
                    body_lines=total - fm,
                    total_lines=total,
                    frontmatter_lines=fm,
                    has_frontmatter=True,
                )

    # No parseable frontmatter: measure the whole file. Fail-closed -- the
    # conservative reading -- and the finding says which reading was used.
    return Measurement(
        body_lines=total,
        total_lines=total,
        frontmatter_lines=0,
        has_frontmatter=False,
    )


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    file: str
    body_lines: int
    total_lines: int
    frontmatter_lines: int
    has_frontmatter: bool
    limit: int = BODY_LINE_LIMIT

    @property
    def over_by(self) -> int:
        return self.body_lines - (self.limit - 1)

    def render(self) -> str:
        if self.has_frontmatter:
            shape = (
                f"{self.frontmatter_lines} frontmatter line(s) + "
                f"{self.body_lines} body line(s) = {self.total_lines} total"
            )
        else:
            shape = (
                f"no parseable frontmatter, so the whole file counts as body: "
                f"{self.body_lines} body line(s) = {self.total_lines} total"
            )
        skill_dir = self.file.rsplit("/", 1)[0]
        return "\n".join(
            [
                f"  {self.file}",
                f"      body {self.body_lines} lines, total {self.total_lines} lines "
                f"-- the budget is under {self.limit} body lines, so this is "
                f"over by {self.over_by}.",
                f"      ({shape})",
                "      Fix: move reference material -- long samples, tables, enumerations -- into",
                f"           {skill_dir}/references/",
                "           and leave a one-line pointer in the body. Extract illustration only;",
                "           never move behaviour the model itself has to emit.",
            ]
        )


def check_file(path: Path, root: Path) -> Finding | None:
    """Pure per-file rule evaluation. Returns None when the body is under budget."""
    measurement = measure(path.read_text(encoding="utf-8"))
    if measurement.body_lines < BODY_LINE_LIMIT:
        return None
    return Finding(
        file=to_rel(path, root),
        body_lines=measurement.body_lines,
        total_lines=measurement.total_lines,
        frontmatter_lines=measurement.frontmatter_lines,
        has_frontmatter=measurement.has_frontmatter,
    )


@dataclass(frozen=True)
class Result:
    findings: tuple[Finding, ...]
    checked: tuple[str, ...]
    skipped: tuple[str, ...]
    unreadable: tuple[tuple[str, str], ...] = ()


def check(root: Path, paths: list[Path] | None = None) -> Result:
    """Evaluate Rule 1 over `paths` (default: every in-scope SKILL.md under `root`).

    Pure: reads files, returns findings, prints nothing, exits nothing. The I/O
    runner is `run()`.
    """
    targets: list[Path] = []
    skipped: list[str] = []
    if paths is None:
        targets = iter_skill_files(root)
    else:
        for raw in paths:
            rel = to_rel(raw, root)
            if in_scope(rel):
                targets.append(root / rel)
            else:
                skipped.append(rel)

    findings: list[Finding] = []
    checked: list[str] = []
    unreadable: list[tuple[str, str]] = []
    for path in targets:
        rel = to_rel(path, root)
        try:
            finding = check_file(path, root)
        except OSError as exc:
            unreadable.append((rel, str(exc)))
            continue
        checked.append(rel)
        if finding is not None:
            findings.append(finding)

    return Result(
        findings=tuple(findings),
        checked=tuple(checked),
        skipped=tuple(skipped),
        unreadable=tuple(unreadable),
    )


# ---------------------------------------------------------------------------
# I/O runner
# ---------------------------------------------------------------------------

RATIONALE = (
    "  Why this budget exists: it is an AUTHORING-QUALITY rule about progressive\n"
    "  disclosure, not a context saving and not a platform limit. A SKILL.md body is\n"
    "  loaded only when the skill is INVOKED; the surface that is in context every\n"
    "  turn is the one-line `description`. Trimming a body saves nothing on turns\n"
    "  that never invoke the skill -- what it buys is instructions the model can\n"
    "  actually follow, with bulk in references/ to be read on demand."
)


def run(root: Path, paths: list[Path] | None = None, stream: TextIO | None = None) -> int:
    out = stream if stream is not None else sys.stdout

    def emit(line: str = "") -> None:
        print(line, file=out)

    result = check(root, paths)

    for rel in result.skipped:
        emit(f"check_skill_budget: skipping {rel} -- not an in-scope skill body ({SKILL_GLOB})")

    if result.unreadable:
        emit()
        emit(f"check_skill_budget: FAILED -- {len(result.unreadable)} unreadable file(s):")
        for rel, err in result.unreadable:
            emit(f"  {rel}: {err}")
        return 1

    if not result.findings:
        emit(
            f"check_skill_budget: OK -- {len(result.checked)} skill body/bodies checked, "
            f"all under {BODY_LINE_LIMIT} lines ({SKILL_GLOB})."
        )
        return 0

    emit()
    emit(
        f"check_skill_budget: FAILED -- {len(result.findings)} of {len(result.checked)} "
        f"skill body/bodies at or over the {BODY_LINE_LIMIT}-line budget:"
    )
    emit()
    for finding in result.findings:
        emit(finding.render())
        emit()
    emit(RATIONALE)
    return 1


def filter_mode(lines: list[str], stream: TextIO | None = None) -> int:
    """Print the in-scope subset of `lines` (repo-relative paths). Always exit 0.

    This is the delegation point for `scripts/pre-commit`: the hook pipes
    `git diff --cached --name-only` in and gets back exactly the paths this gate
    would evaluate, without restating `SKILL_GLOB` in shell.
    """
    out = stream if stream is not None else sys.stdout
    for line in lines:
        candidate = line.strip()
        if candidate and in_scope(candidate):
            print(candidate, file=out)
    return 0


# ---------------------------------------------------------------------------
# --self-test
#
# CLAUDE.md, standing rule: "a verification guard that can't fail is worse than
# none -- negative-test every new gate before wiring it in. It converts
# 'unchecked' into a false 'checked'." This repo has shipped three such guards.
#
# So this asserts exit 1 on every violation class -- including all three
# boundary values, where a boundary bug would otherwise hide in an unexercised
# branch -- and asserts exit 0 for every out-of-scope location, including a
# deliberately over-long file planted under `commands/`.
# ---------------------------------------------------------------------------


def _body(n: int) -> str:
    """A SKILL.md whose body is EXACTLY `n` lines."""
    frontmatter = ["---", "name: fixture", "description: a fixture skill", "---"]
    body = [f"body line {i}" for i in range(1, n + 1)]
    return "\n".join(frontmatter + body) + ("\n" if n else "")


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@dataclass(frozen=True)
class Case:
    name: str
    rel: str
    text: str
    expect_exit: int
    expect_flagged: bool
    expect_in_output: tuple[str, ...] = ()


OVER = BODY_LINE_LIMIT + 120

SELF_TEST_CASES: tuple[Case, ...] = (
    # --- the boundary, all three values ------------------------------------
    Case(
        f"boundary-{BODY_LINE_LIMIT - 1}-passes",
        "plugins/p/skills/at-499/SKILL.md",
        _body(BODY_LINE_LIMIT - 1),
        0,
        False,
    ),
    Case(
        f"boundary-{BODY_LINE_LIMIT}-fails",
        "plugins/p/skills/at-500/SKILL.md",
        _body(BODY_LINE_LIMIT),
        1,
        True,
        ("body 500 lines, total 504 lines", "over by 1"),
    ),
    Case(
        f"boundary-{BODY_LINE_LIMIT + 1}-fails",
        "plugins/p/skills/at-501/SKILL.md",
        _body(BODY_LINE_LIMIT + 1),
        1,
        True,
        ("body 501 lines, total 505 lines", "over by 2"),
    ),
    # --- ordinary cases -----------------------------------------------------
    Case("small-body-passes", "plugins/p/skills/small/SKILL.md", _body(42), 0, False),
    Case(
        "far-over-names-both-counts",
        "plugins/p/skills/huge/SKILL.md",
        _body(OVER),
        1,
        True,
        (
            f"body {OVER} lines, total {OVER + 4} lines",
            "skills/huge/references/",
            "AUTHORING-QUALITY",
            "loaded only when the skill is INVOKED",
        ),
    ),
    Case(
        "no-frontmatter-measured-whole",
        "plugins/p/skills/bare/SKILL.md",
        "\n".join(f"line {i}" for i in range(OVER)) + "\n",
        1,
        True,
        ("no parseable frontmatter",),
    ),
    # --- out of scope: every one of these is deliberately OVER the limit -----
    Case(
        "commands-file-not-evaluated (frozen legacy, ADR-0006 / D55 hazard)",
        "plugins/p/commands/huge-command.md",
        _body(OVER),
        0,
        False,
    ),
    Case(
        "skill-references-not-evaluated (references/ is where bulk BELONGS)",
        "plugins/p/skills/small/references/huge.md",
        _body(OVER),
        0,
        False,
    ),
    Case(
        "test-fixture-not-evaluated (outside plugins/)",
        "tests/fixtures/valid-plugin/skills/help/SKILL.md",
        _body(OVER),
        0,
        False,
    ),
    Case(
        "deeper-nesting-not-evaluated (glob is NON-recursive)",
        "plugins/p/skills/small/nested/SKILL.md",
        _body(OVER),
        0,
        False,
    ),
    Case(
        "root-level-skill-not-evaluated (outside plugins/*/skills/)",
        "plugins/p/SKILL.md",
        _body(OVER),
        0,
        False,
    ),
)


def _run_case(case: Case) -> list[str]:
    import io

    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="check_skill_budget_selftest_") as tmp:
        root = Path(tmp)
        _write(root, case.rel, case.text)
        # A second, always-compliant skill so the "whole tree" scan is never
        # trivially empty -- an empty scan exits 0 for the wrong reason.
        _write(root, "plugins/p/skills/companion/SKILL.md", _body(10))

        buf = io.StringIO()
        code = run(root, None, stream=buf)
        output = buf.getvalue()

        if code != case.expect_exit:
            problems.append(f"exit {code}, expected {case.expect_exit}")

        result = check(root, None)
        flagged = any(f.file == case.rel for f in result.findings)
        if flagged != case.expect_flagged:
            problems.append(f"{case.rel} flagged={flagged}, expected {case.expect_flagged}")
        evaluated = case.rel in result.checked
        if evaluated != in_scope(case.rel):
            problems.append(f"{case.rel} evaluated={evaluated} but in_scope()={in_scope(case.rel)}")

        for needle in case.expect_in_output:
            if needle not in output:
                problems.append(f"output missing {needle!r}")

        if problems:
            problems.append("--- captured output ---\n" + output)
    return problems


def _self_test_filter() -> list[str]:
    """`--filter` and the glob must agree about scope -- they back the same
    pre-commit decision, and two scope predicates that disagree is precisely
    the drift this delegation exists to prevent."""
    import io

    problems: list[str] = []
    paths = [case.rel for case in SELF_TEST_CASES]
    buf = io.StringIO()
    filter_mode(paths, stream=buf)
    emitted = {line for line in buf.getvalue().splitlines() if line}

    for rel in paths:
        want = in_scope(rel)
        got = rel in emitted
        status = "PASS" if want == got else "FAIL"
        print(f"  [{status}] --filter {'keeps' if got else 'drops'} {rel}")
        if want != got:
            problems.append(f"--filter disagreed with in_scope() on {rel}")
    return problems


def self_test() -> int:
    print("=== check_skill_budget.py --self-test ===\n")
    print(
        f"-- Boundary predicate under test: a body is a VIOLATION when "
        f"body_lines >= {BODY_LINE_LIMIT}\n"
        f"   (so {BODY_LINE_LIMIT - 1} passes, {BODY_LINE_LIMIT} fails, "
        f"{BODY_LINE_LIMIT + 1} fails) --\n"
    )

    failures: list[str] = []
    for case in SELF_TEST_CASES:
        problems = _run_case(case)
        status = "PASS" if not problems else "FAIL"
        print(f"  [{status}] expect exit={case.expect_exit}  {case.name}")
        for problem in problems:
            print(f"           -> {problem}")
        failures.extend(f"{case.name}: {p}" for p in problems)

    print("\n-- `--filter` scope agreement (the pre-commit delegation point) --")
    failures += _self_test_filter()

    print("\n-- Real repo tree (must be green on arrival: items 7.1/7.2 landed first) --")
    real = check(REPO_ROOT, None)
    widest = max(
        (measure((REPO_ROOT / rel).read_text(encoding="utf-8")).body_lines for rel in real.checked),
        default=0,
    )
    real_ok = not real.findings
    print(
        f"  [{'PASS' if real_ok else 'FAIL'}] {len(real.checked)} skill body/bodies, "
        f"{len(real.findings)} over budget; largest body = {widest} lines "
        f"({BODY_LINE_LIMIT - 1 - widest} line(s) of headroom)"
    )
    if not real_ok:
        for finding in real.findings:
            print(f"      {finding.file}: body {finding.body_lines}, total {finding.total_lines}")
        failures.append("the real repo tree is not clean -- see findings above")

    print()
    violation_cases = [c for c in SELF_TEST_CASES if c.expect_exit == 1]
    print(
        f"-- {len(violation_cases)} of {len(SELF_TEST_CASES)} cases assert exit 1 "
        f"(this gate CAN fail) --"
    )

    if failures:
        print(f"\nself-test FAILED -- {len(failures)} problem(s):\n")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "\nself-test PASSED -- all three boundary values classified correctly, every "
        "out-of-scope\nlocation ignored even when deliberately over the limit, and the "
        "real tree is green."
    )
    return 0


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Enforce Rule 1: a SKILL.md body (every line after the closing frontmatter "
            f"delimiter) must be strictly under {BODY_LINE_LIMIT} lines. Scope is "
            f"{SKILL_GLOB} -- non-recursive, and deliberately excluding frozen-legacy "
            "command files."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific paths to check (default: every in-scope SKILL.md in the repo).",
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        help=(
            "Read newline-separated paths on stdin and print the in-scope subset. "
            "Always exits 0. Lets callers delegate file selection here instead of "
            "restating the glob."
        ),
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Negative-test this gate against synthetic fixtures and exit.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.filter:
        return filter_mode(sys.stdin.read().splitlines() + list(args.paths))

    paths = [Path(p) for p in args.paths] or None
    return run(REPO_ROOT, paths)


if __name__ == "__main__":
    sys.exit(main())
