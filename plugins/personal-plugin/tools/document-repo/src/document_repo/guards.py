"""Context guards that run after a verify method says "only comments changed".

A comment can still change behaviour: through what it says, where it sits, or how its line ends.
Each rule below closes one way that happens. Every rule fails closed: a false failure reverts one
file, a false pass ships a behaviour change.

Common guards (every method: python-ast, ts-printer, comment-lines). The file-mode check
(git's own view of a mode change, and symlinks) runs in verify.py, before any method:

- byte order mark: adding or dropping a BOM breaks shebangs and some parsers.
- line endings: LF <-> CRLF breaks shebangs (``/bin/sh\\r``) and heredoc terminators.
- non-newline line break: ``str.splitlines`` also splits on form feed and friends, so a "new line"
  could sit inside a physical line (and comment out the rest of it).
- directive-like comment: ``# noqa``, ``// @ts-ignore``, ``//go:build`` and the like are read by
  tools and compilers, so they are code. Each pattern applies only to the languages whose tools
  read it (``DIRECTIVE_SCOPES``): ``/// <summary>`` is a C# doc comment, a TypeScript directive.
  Patterns see one line at a time, so multi-line forms are matched by their lines: a JS block
  line whose first word is ``eslint``, ``global(s)``, ``exported``, ``jshint`` or ``jslint``,
  and a Go block comment whose first content line is ``Output:``.
- coding cookie: a PEP 263 ``# coding: x`` comment (Python) or an Emacs ``-*- coding: x -*-``
  line (any language) in lines 1-2 changes how the file is decoded.
- template markers: ``{{``/``{%``/``{#`` in a comment run under Helm, Jinja and friends, but only
  in a file that is a template (``template_file``).
- YAML tab: a tab in the indentation of an inserted YAML line is a parse error.
- continuation-ending comment: ``# note \\`` swallows the next line in make, C and shell.
- protected header: nothing may go above a shebang, a coding cookie or Dockerfile parser
  directives, or they stop being recognised.
- below a directive: ``// eslint-disable-next-line`` and friends apply to the NEXT line, so a new
  line under them moves their effect.
- removed directive: deleting or rewriting a directive line passes python-ast, but changes
  behaviour (a dropped shebang or coding cookie).
- make recipe line: a tab-indented ``# x`` inside a recipe is a shell command make echoes.
- SQL ``--x``: MySQL needs whitespace after ``--``; otherwise it is two minus signs.

Context guards (comment-lines only, run by ``context_guard``). It tests the position of every
inserted chunk against the scanners that ``unsafe_insert_points`` also combines (it does not call
that function), and tests the one position that depends on the text, below a YAML block scalar,
against the inserted lines themselves:

- line continuation: a new line after a base line ending in ``\\`` splits that statement.
- verbatim regions: inside heredocs, block scalars, multi-line strings, raw strings, block
  comments and HTML raw-text elements a new line is data, not a comment.
- Go example output: from ``// Output:`` to the closing ``}`` the comments are compared with
  the program's output by ``go test``; a line directly above ``// Output:`` hides the prefix.
- no scanner: a language without a scanner is unsafe at every position. JS/TS have none: they are
  verified only by ts-printer, because a line scanner cannot lex template literals, regex
  literals and JSX reliably enough to stake a false pass on.
- after a YAML block scalar: the position directly below its last line is unsafe only for an
  inserted line indented deeper than the ``key: |`` line (it would join the block), or a blank
  line under keep chomping (``|+``). A comment level with the next key is fine.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Callable
from dataclasses import dataclass

from .languages import Lang

_I = re.IGNORECASE

_ALL: frozenset[str] | None = None
_JS = frozenset({"typescript", "javascript"})
_JS_CSS = _JS | {"css"}
_GO = frozenset({"go"})
_PY = frozenset({"python"})
_HASH = frozenset({"python", "shell", "yaml", "toml", "dockerfile", "make"})
_CSS = frozenset({"css"})
_JAVA = frozenset({"java"})
_DOCKER = frozenset({"dockerfile"})

#: A Go example's output comment. The directive check and ``go_example_output_points`` share it.
_GO_OUTPUT = re.compile(r"^\s*(?://|/\*)\s*(?:unordered\s+)?output:", _I)

#: Comment text that a tool, compiler or runtime reads, as ``(languages, patterns)``. ``None``
#: means every language. A pattern is scoped to the languages whose tools read it, so ordinary
#: comments elsewhere are not false failures: ``/// <summary>`` is a C# XML doc comment but a
#: TypeScript triple-slash directive, and a ``type: string`` comment is a YAML note but a Python
#: type comment. Anything read by tools in several ecosystems stays ``None`` (the ruff/flake8
#: suppression word is also read by ansible-lint in YAML; Prettier's ignore marker in JS, CSS,
#: HTML and YAML). Template markers are not here: ``TEMPLATE_PATTERN`` applies them by file instead.
_DIRECTIVES: tuple[tuple[frozenset[str] | None, tuple[tuple[str, int], ...]], ...] = (
    (
        _ALL,
        (
            (r"\bnoqa\b", _I),
            (r"\bnosec\b", _I),
            (r"prettier-ignore", 0),
            (r"biome-ignore", 0),
            (r"\bnolint\b", _I),
            (r"\bNOLINT", 0),
            (r"Code generated .*DO NOT EDIT", 0),
            (r"#\s*shellcheck\b", _I),
            (r"\b(hadolint|yamllint|tflint|tfsec|trivy|kics|checkov|nosemgrep)\b", _I),
            (r"#\s*renovate:", _I),
            # SQL: MySQL executable comments (also JS and CSS banners), hints, migration markers
            (r"/\*[!+]", 0),
            (r"^\s*--\s*\+", 0),
            (
                r"^\s*--\s*(liquibase|changeset|rollback|precondition|validchecksum|ignorelines)\b",
                _I,
            ),
            (r"^\s*--\s*migrate:", _I),
            (r"^\s*--\s*name:\s*\S+\s*:", _I),
            (r"<auto-generated", _I),
            (r"@generated\b", 0),
            (r"@(format|prettier|noformat)\b", 0),
            # HTML: IE conditional comments, server-side includes, Knockout virtual elements
            (r"<!--\s*\[if", _I),
            (r"<!\[endif\]", _I),
            (r"<!--\s*#", 0),
            (r"<!--\s*/?ko\b", 0),
            # Shebang anywhere
            (r"^\s*#!", 0),
        ),
    ),
    (
        _PY,
        (
            (r"#\s*type\s*:", 0),
            (r"#\s*(pylint|fmt|isort|pyright|mypy|ruff|pyre|yapf)\s*:", _I),
            (r"#\s*pyre-", 0),
        ),
    ),
    # coverage.py reads its no-cover pragma comment, and detect-secrets reads its allowlist pragma
    # in any file whose comments start with a hash. In C, a comment naming the pack pragma is prose.
    (_HASH, ((r"#\s*pragma\b", _I),)),
    (
        _JS,
        (
            (r"@ts-(ignore|expect-error|nocheck|check)\b", 0),
            # Directive forms only: "-disable"/"-enable" (and "-line"/"-next-line"), the
            # "/* eslint-env */" environment comment, and "/* eslint rule: x */" config comments.
            (r"\beslint-(disable|enable|env)\b", 0),
            (r"/\*\s*eslint\s", 0),
            (r"/\*\s*(global|globals|exported|jshint|jslint)\b", 0),
            # Multi-line block forms: "/* eslint" alone on its line, or a later line of the block
            # whose first word (after an optional "*") is the directive keyword.
            (r"/\*\s*(eslint|globals?|exported|jshint|jslint)\s*$", 0),
            (r"^\s*\*?\s*(eslint|globals?|exported|jshint|jslint)(\s|$)", 0),
            (r"\b(istanbul|c8|v8)\s+ignore\b", 0),
            (r"deno-(lint|fmt)-ignore", 0),
            (r"@jsx\w*", 0),
            (r"@flow\b", 0),
            # TypeScript triple-slash directive. C# and C++ use "/// <summary>" for doc comments.
            (r"^\s*///\s*<", 0),
            (r"[@#]__(PURE|NO_SIDE_EFFECTS)__", 0),
            (r"webpack[A-Z]\w*\s*:", 0),
            (r"@vite-ignore", 0),
            (r"@(jest|vitest)-environment", 0),
            (r"@cc_on", _I),
        ),
    ),
    (_JS_CSS, ((r"[#@]\s*source(Mapping)?URL\s*=", 0),)),
    (
        _GO,
        (
            (r"//\s*go:", 0),
            (r"//\s*\+\w", 0),  # build constraints and kubebuilder markers; "// +1" is prose
            (r"(//|/\*)line ", 0),
            (r"^\s*//(export|extern)\s", 0),
            (_GO_OUTPUT.pattern, _I),  # example tests, "//" or "/*"; elsewhere "Output:" is prose
        ),
    ),
    (_CSS, ((r"\b(stylelint|purgecss|autoprefixer)\b", _I), (r"\brtl\s*:", _I))),
    # Java decodes \u escapes before lexing, so "\u000a" in a // comment ends it.
    (_JAVA, ((r"\\u+[0-9a-fA-F]{4}", 0),)),
    (_DOCKER, ((r"^\s*#\s*(syntax|escape|check)\s*=", _I),)),
)

#: Every directive pattern with the languages it applies to (``None``: all languages).
DIRECTIVE_SCOPES: tuple[tuple[re.Pattern[str], frozenset[str] | None], ...] = tuple(
    (re.compile(pattern, flags), langs) for langs, group in _DIRECTIVES for pattern, flags in group
)

#: Every directive pattern, regardless of language scope.
DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(p for p, _ in DIRECTIVE_SCOPES)

#: PEP 263 coding cookie. Python reads it from lines 1-2; it also matches the Emacs and Vim forms.
CODING_COOKIE = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*[-\w.]+")
#: Emacs file-variables line (``-*- coding: x -*-``), read from lines 1-2 of a file in any language.
EMACS_COOKIE = re.compile(r"-\*-.*?\bcoding[ \t]*:[ \t]*[-\w.]+")

#: Template-engine markers: ``{{`` and ``{%`` (expressions, tags) and ``{#`` (a Jinja comment,
#: which swallows text up to ``#}``). Helm, Jinja, Django, Go templates and cookiecutter evaluate
#: them even inside comments, but only in files that are templates, so ``template_file`` decides
#: where they apply; in an ordinary Python docstring ``{{ name }}`` is prose.
TEMPLATE_PATTERN = re.compile(r"\{\{|\{%|\{#")
#: What makes a base a template. ``{#`` is left out: shell ``${#x}`` is not a template.
_TEMPLATE_BASE = re.compile(r"\{\{|\{%")
_DOCKER_DIRECTIVE = re.compile(r"^\s*#\s*[A-Za-z][\w-]*\s*=")
_NEWLINES = ("\n", "\r\n")


def _is_directive(line: str, lang: Lang, templated: bool = False) -> bool:
    """True when ``line`` matches a directive pattern that applies to ``lang``.

    ``templated`` (see ``template_file``) adds the template-engine markers.
    """
    return (templated and bool(TEMPLATE_PATTERN.search(line))) or any(
        p.search(line) for p, langs in DIRECTIVE_SCOPES if langs is None or lang.name in langs
    )


def _is_cookie(line: str, lang: Lang) -> bool:
    """True for an encoding declaration ``lang`` reads when it sits in lines 1-2."""
    return bool(EMACS_COOKIE.search(line)) or (
        lang.name == "python" and bool(CODING_COOKIE.match(line))
    )


def template_file(rel: str, before: str, lang: Lang) -> bool:
    """True when ``rel`` is evaluated by a template engine, so ``{{`` in a comment is code.

    That is: HTML (Jinja, Django and Go templates treat ``<!-- -->`` as text), a file under a
    ``templates`` directory (Helm charts, Django, Ansible roles), a path with ``{{`` in it
    (cookiecutter, copier), or a base that already uses ``{{`` or ``{%`` (it is a template).
    """
    parts = rel.replace("\\", "/").split("/")
    return (
        lang.name == "html"
        or "templates" in parts[:-1]
        or any("{{" in part for part in parts)
        or bool(_TEMPLATE_BASE.search(before))
    )


def inserted_lines(before: str, after: str) -> list[tuple[int, int, list[str]]]:
    """New lines in ``after``: ``(base_insert_pos, edited_start_line_1based, lines)``.

    Covers every ``insert`` opcode and the ``b`` side of every ``replace`` opcode of a
    ``difflib.SequenceMatcher(autojunk=False)`` over ``splitlines()``.
    """
    a, b = before.splitlines(), after.splitlines()
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [
        (i1, j1 + 1, b[j1:j2])
        for tag, i1, _i2, j1, j2 in matcher.get_opcodes()
        if tag in ("insert", "replace")
    ]


def _split_ends(text: str) -> tuple[list[str], list[str]]:
    """Lines without terminators, and each line's terminator ("" for a last unterminated line)."""
    raw = text.splitlines(keepends=True)
    content = [r.splitlines()[0] if r.splitlines() else "" for r in raw]
    return content, [r[len(c) :] for r, c in zip(raw, content)]


def _line_ending_guard(before: str, after: str) -> str | None:
    if ("\r\n" in before) != ("\r\n" in after):
        return "line endings changed"
    a, a_end = _split_ends(before)
    b, b_end = _split_ends(after)
    allowed = {e for e in a_end if e} or {"\n"}
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                last_gains_newline = i == len(a) - 1 and not a_end[i] and b_end[j] in allowed
                if a_end[i] != b_end[j] and not last_gains_newline:
                    return f"line endings changed (base line {i + 1})"
            continue
        if tag in ("insert", "replace") and i1 > 0 and a_end[i1 - 1] not in (*_NEWLINES, ""):
            return f"inserted inside a physical line (non-newline line break after base line {i1})"
        for j in range(j1, j2):
            if b_end[j] and b_end[j] not in _NEWLINES:
                return f"inserted line ends with a non-newline line break (edited line {j + 1})"
            if b_end[j] and b_end[j] not in allowed:
                return f"line endings changed (edited line {j + 1} uses a new terminator)"
    return None


def _last_protected(lines: list[str], lang: Lang) -> int:
    """Index of the last protected leading base line, or -1 when there is none."""
    last = -1
    if lines and lines[0].lstrip("\ufeff").startswith("#!"):
        last = 0
    for i in (0, 1):
        if i < len(lines) and _is_cookie(lines[i].lstrip("\ufeff"), lang):
            last = max(last, i)
    if lang.name == "dockerfile":
        for i, line in enumerate(lines):
            if not _DOCKER_DIRECTIVE.match(line.lstrip("\ufeff")):
                break
            last = max(last, i)
    return last


def _is_comment_line(line: str, lang: Lang) -> bool:
    s = line.strip()
    return bool(s) and (
        any(s.startswith(m) for m in lang.line) or any(s.startswith(b) for b, _ in lang.block)
    )


def _removed_lines(before: str, after: str) -> list[tuple[int, str]]:
    a, b = before.splitlines(), after.splitlines()
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [
        (i, a[i])
        for tag, i1, i2, _j1, _j2 in matcher.get_opcodes()
        if tag in ("delete", "replace")
        for i in range(i1, i2)
    ]


def _go_block_output(lines: list[str]) -> str | None:
    """Fail a ``/*`` line whose first non-blank content line starts with ``Output:``.

    go/doc strips the comment markers and leading blank lines, so ``/*`` then ``Output: hi`` is an
    example's expected output, just like ``/* Output: hi */`` (which the line patterns catch).
    """
    for k, line in enumerate(lines):
        if line.strip() != "/*":
            continue
        first = next((nxt.strip() for nxt in lines[k + 1 :] if nxt.strip()), "")
        if _GO_OUTPUT.match("/* " + first):
            return f"inserted directive-like comment: /* {first}"
    return None


def common_guards(rel: str, before: str, after: str, lang: Lang) -> str | None:
    """Run the guards every verify method shares. Return a failure detail, or None when clean."""
    if before.startswith("\ufeff") != after.startswith("\ufeff"):
        return "byte order mark changed"
    why = _line_ending_guard(before, after)
    if why:
        return why
    base = before.splitlines()
    protected = _last_protected(base, lang)
    templated = template_file(rel, before, lang)
    for i, line in _removed_lines(before, after):
        directive = _is_directive(line, lang, templated) and _is_comment_line(line, lang)
        if i <= protected or directive:
            return f"removed or changed directive-like line: {line.strip()!r} (base line {i + 1})"
    for pos, start, lines in inserted_lines(before, after):
        if pos <= protected:
            return f"inserted above a protected header line (base line {protected + 1})"
        prev = base[pos - 1] if pos > 0 else ""
        if (
            pos > 0
            and pos - 1 > protected
            and _is_comment_line(prev, lang)
            and _is_directive(prev, lang, templated)
        ):
            return f"inserted below a directive-like comment: {prev.strip()!r}"
        if lang.name == "go":
            why = _go_block_output(lines)
            if why:
                return why
        for offset, line in enumerate(lines):
            text = line.strip()
            if _is_directive(line, lang, templated) or (
                start + offset <= 2 and _is_cookie(line, lang)
            ):
                return f"inserted directive-like comment: {text}"
            if text.endswith(("\\", "??/")):
                return f"comment ends with a line continuation: {text}"
            if lang.name == "yaml" and "\t" in line[: len(line) - len(line.lstrip())]:
                return f"tab in the indentation of an inserted YAML line: {line!r}"
            if lang.name == "make" and line.startswith("\t") and text:
                return f"tab-indented line in a Makefile is a recipe line, not a comment: {text}"
            if lang.name == "sql" and re.match(r"--[^\s]", text):
                return f"'--' must be followed by whitespace to be a comment in MySQL: {text}"
    return None


# ---------------------------------------------------------------------------
# Context scanners. Each returns the indices of base lines that END inside a verbatim region, so
# a new line placed after them (insert position index + 1) would become data.
# ---------------------------------------------------------------------------


def _continuation_points(lines: list[str]) -> set[int]:
    return {k for k in range(1, len(lines) + 1) if lines[k - 1].rstrip().endswith(("\\", "??/"))}


# --- shell, dockerfile, make -----------------------------------------------

_HEREDOC = re.compile(r"<<(-?)[ \t]*(?:'([^']*)'|\"([^\"]*)\"|\\?([A-Za-z0-9_][\w.-]*))")


def _shell_scan_line(line: str, stack: list[str], heredocs: list[tuple[str, bool]]) -> None:
    """Advance a shell quoting ``stack`` over one line, queueing heredoc words it opens."""
    i, n = 0, len(line)
    while i < n:
        top, c = stack[-1], line[i]
        if top in ("code", "paren"):
            if c == "#" and (i == 0 or line[i - 1] in " \t;|&()<>"):
                return
            if c == "\\":
                i += 2
                continue
            if line.startswith("<<<", i):
                i += 3  # here-string, not a heredoc
                continue
            if line.startswith("<<", i):
                m = _HEREDOC.match(line, i)
                if m:
                    word = m.group(2) if m.group(2) is not None else m.group(3) or m.group(4)
                    heredocs.append((word or "", m.group(1) == "-"))
                    i = m.end()
                    continue
            if line.startswith("$'", i):
                stack.append("ansi")
                i += 2
                continue
            if c == "'":
                stack.append("sq")
            elif c == '"':
                stack.append("dq")
            elif c == "`":
                stack.append("bq")
            elif line.startswith("${", i):
                stack.append("brace")
                i += 1
            elif c == "(":
                stack.append("paren")
            elif c == ")" and top == "paren":
                stack.pop()
            i += 1
            continue
        if top == "sq":
            if c == "'":
                stack.pop()
            i += 1
            continue
        if c == "\\":
            i += 2
            continue
        if (top == "ansi" and c == "'") or (top == "dq" and c == '"') or (top == "bq" and c == "`"):
            stack.pop()
        elif top == "brace" and c == "}":
            stack.pop()
        elif top in ("dq", "brace") and line.startswith("$(", i):
            stack.append("paren")
            i += 1
        elif top in ("dq", "brace") and line.startswith("${", i):
            stack.append("brace")
            i += 1
        elif top == "dq" and c == "`":
            stack.append("bq")
        elif top == "brace" and c in "'\"":
            stack.append("sq" if c == "'" else "dq")
        i += 1


def _heredoc_body(line: str, heredocs: list[tuple[str, bool]]) -> None:
    word, dash = heredocs[0]
    if (line.lstrip("\t") if dash else line) == word:
        heredocs.pop(0)


def _scan_shell(lines: list[str]) -> set[int]:
    out: set[int] = set()
    stack: list[str] = ["code"]
    heredocs: list[tuple[str, bool]] = []
    for idx, line in enumerate(lines):
        if heredocs:
            _heredoc_body(line, heredocs)
        else:
            _shell_scan_line(line, stack, heredocs)
        if heredocs or len(stack) > 1:
            out.add(idx)
    return out


_MAKE_DEFINE = re.compile(r"^\s*(?:(?:override|export|private|unexport)\s+)*define\b")
_MAKE_ENDEF = re.compile(r"^\s*endef\b")


def _scan_make(lines: list[str]) -> set[int]:
    out: set[int] = set()
    depth = 0
    heredocs: list[tuple[str, bool]] = []
    for idx, line in enumerate(lines):
        if heredocs:
            _heredoc_body(line, heredocs)
        elif depth:
            if _MAKE_ENDEF.match(line):
                depth -= 1
            elif _MAKE_DEFINE.match(line):
                depth += 1
        elif not line.startswith("\t") and _MAKE_DEFINE.match(line):
            depth = 1
        elif line.startswith("\t"):
            _shell_scan_line(line, ["code"], heredocs)
        if depth or heredocs:
            out.add(idx)
    return out


# --- yaml ------------------------------------------------------------------

_YAML_BLOCK = re.compile(
    r"(?:^\s*(?:-\s+)*|:\s+|^---\s+)(?:[!&]\S*\s+)*[|>]([-+1-9]{0,2})\s*(?:#.*)?$"
)
_YAML_KEY = re.compile(r"""^(?:"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"{\[?][^#]*?)\s*:(?=\s|$)""")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _yaml_quote_end(text: str, start: int, quote: str) -> int:
    """Index just past the closing ``quote`` in ``text`` from ``start``, or -1 when still open."""
    i = start
    while i < len(text):
        c = text[i]
        if quote == '"' and c == "\\":
            i += 2
            continue
        if c == quote:
            if quote == "'" and text.startswith("''", i):
                i += 2
                continue
            return i + 1
        i += 1
    return -1


@dataclass(frozen=True)
class _BlockTail:
    """The position directly after a YAML block scalar's last line, and what decides if it is safe.

    A line inserted there joins the block when it is indented deeper than ``opener_indent`` (the
    indentation of the ``key: |`` line). A blank line there is scalar content under keep
    chomping (``|+``, ``>+``). ``opener_indent`` is -1 when the opener line does not show where
    the content starts, so every inserted line is unsafe.
    """

    opener_indent: int
    keep: bool


_YAML_PROPS_AT_END = re.compile(r"(?:\s+[!&]\S*)+\s*$")
_YAML_DASH_AT_END = re.compile(r"(?:^|\s)-$")


def _yaml_anchored(line: str, block: re.Match[str]) -> bool:
    """True for a ``key: |`` or ``- |`` opener, whose content is always indented deeper than it.

    A document-level scalar (``--- |``, a bare ``|``) may start at column 0, and a header alone on
    its line may be indented deeper than its content, so neither says where the content starts.
    """
    head = line[: block.start(1) - 1]  # everything before the "|" or ">" indicator
    head = _YAML_PROPS_AT_END.sub("", head).rstrip()
    return head.endswith(":") or bool(_YAML_DASH_AT_END.search(head))


def _scan_yaml(lines: list[str]) -> set[int]:
    return _yaml_scan(lines)[0]


def _yaml_scan(lines: list[str]) -> tuple[set[int], dict[int, _BlockTail]]:
    """Base lines that end inside verbatim YAML, and the position after each block scalar.

    The first result holds the same indices as the other scanners (a new line after base line
    ``idx`` is unsafe), which for a block scalar covers the opener and every block line but the
    last. The block's last line is the second result's key minus one: whether a new line right
    after it joins the block depends on the inserted text, so ``context_guard`` decides.
    """
    out: set[int] = set()
    tails: dict[int, _BlockTail] = {}
    n, i, quote = len(lines), 0, ""
    while i < n:
        line = lines[i]
        if quote:
            if _yaml_quote_end(line, 0, quote) < 0:
                out.add(i)
            else:
                quote = ""
            i += 1
            continue
        s = line.strip()
        if not s or s.startswith("#"):
            i += 1
            continue
        block = _YAML_BLOCK.search(line)
        if block:
            opener, last, j = _indent(line), i, i + 1
            while j < n and (not lines[j].strip() or _indent(lines[j]) > opener):
                last, j = j, j + 1
            out.update(range(i, last))  # the opener and every block line but the last
            anchored = _yaml_anchored(line, block)
            tails[last + 1] = _BlockTail(opener if anchored else -1, "+" in block.group(1))
            i = last + 1
            continue
        col = _indent(line)
        body = line[col:]
        dash = -1  # the column of the innermost "- " on the line, -1 for none
        while re.match(r"-(\s|$)", body):
            step = len(body) - len(body[1:].lstrip(" "))
            dash, col, body = col, col + step, body[step:]
        m = _YAML_KEY.match(body)
        value = body[m.end() :] if m else body
        value = re.sub(r"^(?:\s*[!&]\S*)*", "", value).strip()
        if not value or value.startswith("#"):
            i += 1
            continue
        if value[0] in "\"'":
            if _yaml_quote_end(value, 1, value[0]) < 0:
                quote = value[0]
                out.add(i)
        # A plain scalar continues on every following line indented deeper than the node that
        # holds it (SE-H2). For ``key: value`` that is the key's column (the mapping's indent).
        # For a bare sequence entry (``- foo``) it is the dash's column, not the content's:
        # ``- foo`` then ``  bar`` is one scalar, "foo bar". A bare scalar at column 0 is held by
        # nothing (a document scalar), so any line continues it; a marker (``---``, ``...``,
        # ``%YAML``) is not a scalar. Any other bare line keeps its own indent: it continues an
        # earlier scalar, whose run was already marked.
        if not m and dash >= 0:
            col = dash
        elif not m and col == 0 and not body.startswith(("---", "...", "%")):
            col = -1
        last_cont, j = -1, i + 1
        while j < n:
            nxt = lines[j].strip()
            if nxt.startswith("#"):
                break
            if nxt and _indent(lines[j]) <= col:
                break
            if nxt:
                last_cont = j
            j += 1
        out.update(range(i, last_cont))
        i += 1
    return out, tails


# --- sql -------------------------------------------------------------------

_DOLLAR = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)?\$")
_COPY_STDIN = re.compile(r"^\s*COPY\b.*\bFROM\s+STDIN\b", _I)


def _scan_sql_dialect(lines: list[str], backslash: bool, mysql: bool) -> set[int]:
    out: set[int] = set()
    state, close, depth, copy = "code", "", 0, False
    for idx, line in enumerate(lines):
        if copy:
            copy = line != "\\."
            if copy:
                out.add(idx)
            continue
        if state == "code" and _COPY_STDIN.match(line):
            copy = True
            out.add(idx)
            continue
        i, n = 0, len(line)
        while i < n:
            c = line[i]
            if state == "block":
                if not mysql and line.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif line.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                    state = "code" if depth == 0 else "block"
                else:
                    i += 1
                continue
            if state == "str":
                if backslash and c == "\\":
                    i += 2
                elif line.startswith(close * 2, i) and len(close) == 1:
                    i += 2
                elif line.startswith(close, i):
                    state, i = "code", i + len(close)
                else:
                    i += 1
                continue
            if line.startswith("--", i) and (not mysql or line[i + 2 : i + 3] in ("", " ", "\t")):
                break
            if mysql and c == "#":
                break
            if line.startswith("/*", i):
                state, depth, i = "block", 1, i + 2
                continue
            if c in "'\"" or (mysql and c == "`"):
                state, close, i = "str", c, i + 1
                continue
            m = None if mysql else _DOLLAR.match(line, i)
            if m and (i == 0 or not (line[i - 1].isalnum() or line[i - 1] in "_$")):
                state, close, i = "str", m.group(0), m.end()
                continue
            i += 1
        if state != "code":
            out.add(idx)
    return out


def _scan_sql(lines: list[str]) -> set[int]:
    # Dialects disagree on backslash escapes, "#" comments and $$ quoting: union every reading.
    out: set[int] = set()
    for backslash, mysql in ((False, False), (True, False), (True, True)):
        out |= _scan_sql_dialect(lines, backslash, mysql)
    return out


# --- toml ------------------------------------------------------------------


def _scan_toml(lines: list[str]) -> set[int]:
    out: set[int] = set()
    close, broken = "", False
    for idx, line in enumerate(lines):
        i, n = 0, len(line)
        while i < n and not broken:
            if close:
                if close == '"""' and line[i] == "\\":
                    i += 2
                elif line.startswith(close, i):
                    i += 3
                    while i < n and line[i] == close[0]:
                        i += 1
                    close = ""
                else:
                    i += 1
                continue
            c = line[i]
            if c == "#":
                break
            if line.startswith(('"""', "'''"), i):
                close, i = line[i : i + 3], i + 3
                continue
            if c in "\"'":
                j = i + 1
                while j < n and line[j] != c:
                    j += 2 if c == '"' and line[j] == "\\" else 1
                if j >= n:
                    broken = True  # unterminated single-line string: fail closed
                i = j + 1
                continue
            i += 1
        if close or broken:
            out.add(idx)
    return out


# --- C family, CSS ------------------------------------------------------------


@dataclass(frozen=True)
class _Syntax:
    line_comment: bool = True
    nested_block: bool = False
    sq_string: bool = False
    char_lit: bool = True
    multiline_dq: bool = False
    backtick_raw: bool = False
    text_block: bool = False
    cs_strings: bool = False
    cpp_raw: bool = False
    rust_raw: bool = False


#: JS/TS are absent on purpose: they are verified only by ts-printer (see the module docstring).
_SYNTAX = {
    "c": _Syntax(),
    "cpp": _Syntax(cpp_raw=True),
    "go": _Syntax(backtick_raw=True),
    "java": _Syntax(text_block=True),
    "csharp": _Syntax(cs_strings=True),
    "rust": _Syntax(nested_block=True, multiline_dq=True, rust_raw=True),
    "css": _Syntax(line_comment=False, sq_string=True, char_lit=False),
}
_CPP_RAW = re.compile(r'(?:u8|u|U|L)?R"([^()\\\s]{0,16})\(')
_RUST_RAW = re.compile(r'[bc]?r(#*)"')
_CS_RAW = re.compile(r'[$]*("{3,})')


def _ident(c: str) -> bool:
    return c.isalnum() or c == "_"


def _scan_clike(lines: list[str], syn: _Syntax) -> set[int]:
    """One lexer, one loop: base lines that end inside a string or a block comment."""
    out: set[int] = set()
    # Frames: ["code"] | ["block"] | ["str", close, esc, multi, dbl]
    stack: list[list[object]] = [["code"]]
    for idx, line in enumerate(lines):
        i, n = 0, len(line)
        while i < n:
            top = stack[-1]
            kind, c = top[0], line[i]
            if kind == "block":
                if syn.nested_block and line.startswith("/*", i):
                    stack.append(["block"])
                    i += 2
                elif line.startswith("*/", i):
                    stack.pop()
                    i += 2
                else:
                    i += 1
                continue
            if kind == "str":
                close, esc, _multi, dbl = str(top[1]), top[2], top[3], top[4]
                if esc and c == "\\":
                    i += 2
                elif dbl and line.startswith(close * 2, i):
                    i += 2
                elif line.startswith(close, i):
                    stack.pop()
                    i += len(close)
                else:
                    i += 1
                continue
            # code
            if syn.line_comment and line.startswith("//", i):
                break
            if line.startswith("/*", i):
                stack.append(["block"])
                i += 2
                continue
            boundary = i == 0 or not _ident(line[i - 1])
            m = _CPP_RAW.match(line, i) if syn.cpp_raw and boundary else None
            if m:
                stack.append(["str", ")" + m.group(1) + '"', False, True, False])
                i = m.end()
                continue
            m = _RUST_RAW.match(line, i) if syn.rust_raw and boundary else None
            if m:
                stack.append(["str", '"' + m.group(1), False, True, False])
                i = m.end()
                continue
            if syn.cs_strings and c in "@$":
                m = re.match(r'(?:\$+@|@\$*)"', line[i:])
                if m:
                    stack.append(["str", '"', False, True, True])
                    i += m.end()
                    continue
                m = _CS_RAW.match(line, i)
                if m and c == "$":
                    stack.append(["str", m.group(1), False, True, False])
                    i = m.end()
                    continue
            m = _CS_RAW.match(line, i) if syn.cs_strings and c == '"' else None
            if m:  # three or more quotes: a C# raw string
                stack.append(["str", m.group(1), False, True, False])
                i = m.end()
                continue
            if syn.text_block and line.startswith('"""', i):
                stack.append(["str", '"""', True, True, False])
                i += 3
                continue
            if c == '"' or (c == "'" and syn.sq_string):
                stack.append(["str", c, True, syn.multiline_dq and c == '"', False])
                i += 1
                continue
            if c == "'" and syn.char_lit:
                if line[i + 1 : i + 2] == "\\":
                    j = line.find("'", i + 2, i + 14)
                    i = j + 1 if j > 0 else i + 1
                elif line[i + 2 : i + 3] == "'":
                    i += 3
                else:
                    i += 1  # Rust lifetime or label, C++ digit separator
                continue
            if c == "`" and syn.backtick_raw:
                stack.append(["str", "`", False, True, False])
                i += 1
                continue
            i += 1
        top = stack[-1]
        if top[0] == "str" and not top[3] and not line.rstrip().endswith("\\"):
            stack.pop()  # single-line string closed by the line end (a syntax error anyway)
        if len(stack) > 1:
            out.add(idx)
    return out


_CGO_IMPORT = re.compile(r'^\s*(import\s+)?"C"\s*(//.*)?$')


def _cgo_preamble_points(lines: list[str]) -> set[int]:
    """Positions inside or just above a cgo preamble (the comment right before ``import "C"``)."""
    points: set[int] = set()
    for idx, line in enumerate(lines):
        if not _CGO_IMPORT.match(line):
            continue
        start = idx
        while start > 0:
            prev = lines[start - 1].strip()
            if prev.endswith("*/"):
                start -= 1
                while start > 0 and "/*" not in lines[start]:
                    start -= 1
            elif prev.startswith("//"):
                start -= 1
            else:
                break
        points.update(range(start, idx + 1))
    return points


_GO_EXAMPLE = re.compile(r"^func\s+Example\w*\s*\(")


def go_example_output_points(lines: list[str]) -> set[int]:
    """Positions from an example function's ``// Output:`` line through its closing ``}``.

    ``go test`` compares the function's last comment group with the program's output. A line
    inserted inside the run, or after it before ``}``, changes the expected output or becomes the
    last comment group. A line inserted directly above ``// Output:`` joins its group, which then
    no longer starts with ``Output:``, so the example silently stops running: position ``k`` of
    the ``// Output:`` line itself is unsafe too. A comment separated from it by a blank line is
    its own group and stays safe. The function ends at the first column-0 ``}`` (gofmt layout);
    without one, everything to end of file is unsafe.
    """
    points: set[int] = set()
    in_example, i, n = False, 0, len(lines)
    while i < n:
        line = lines[i]
        if _GO_EXAMPLE.match(line):
            in_example = True
        elif in_example and line.startswith("}"):
            in_example = False
        elif in_example and _GO_OUTPUT.match(line):
            end = next((j for j in range(i + 1, n) if lines[j].startswith("}")), n)
            points.update(range(i, end + 1))
            i = end
            continue
        i += 1
    return points


# --- html ------------------------------------------------------------------

_HTML_RAW = {
    "script",
    "style",
    "pre",
    "textarea",
    "title",
    "xmp",
    "noscript",
    "iframe",
    "noembed",
    "noframes",
    "listing",
    "plaintext",
}
_HTML_TAG = re.compile(r"<(/?)([A-Za-z][\w:-]*)")


def _scan_html(lines: list[str]) -> set[int]:
    out: set[int] = set()
    state, raw, tag, closing, quote = "text", "", "", False, ""
    for idx, line in enumerate(lines):
        i, n = 0, len(line)
        while i < n:
            if state == "comment":
                j = line.find("-->", i)
                state, i = ("comment", n) if j < 0 else ("text", j + 3)
            elif state == "raw":
                m = re.compile(r"</" + raw + r"(?=[\s/>]|$)", _I).search(line, i)
                state, i = ("raw", n) if m is None else ("text", m.start())
            elif state in ("tag", "decl"):
                c = line[i]
                if quote:
                    quote = "" if c == quote else quote
                elif c in "\"'" and state == "tag":
                    quote = c
                elif c == ">":
                    raw_tag = state == "tag" and not closing and tag in _HTML_RAW
                    state, raw = ("raw", tag) if raw_tag else ("text", "")
                i += 1
            elif line.startswith("<!--", i):
                state, i = "comment", i + 4
            else:
                m = _HTML_TAG.match(line, i)
                if m:
                    state, closing, tag, i = "tag", bool(m.group(1)), m.group(2).lower(), m.end()
                elif line.startswith(("<!", "<?"), i):
                    state, i = "decl", i + 2
                else:
                    i += 1
        if state != "text":
            out.add(idx)
    return out


_SCANNERS: dict[str, Callable[[list[str]], set[int]]] = {
    "shell": _scan_shell,
    "dockerfile": _scan_shell,
    "make": _scan_make,
    "yaml": _scan_yaml,
    "sql": _scan_sql,
    "toml": _scan_toml,
    "html": _scan_html,
}


def _verbatim_points(lines: list[str], lang: Lang) -> set[int]:
    scan = _SCANNERS.get(lang.name)
    if scan is not None:
        inside = scan(lines)
    elif lang.name in _SYNTAX:
        inside = _scan_clike(lines, _SYNTAX[lang.name])
    else:
        # No scanner for this language: nothing is known to be safe, so every position fails.
        return set(range(len(lines) + 1))
    points = {i + 1 for i in inside}
    if lang.name == "go":
        points |= _cgo_preamble_points(lines)
    return points


def unsafe_insert_points(lines: list[str], lang: Lang) -> set[int]:
    """Insert positions where a new line would not be a comment.

    Position ``k`` means "a new line placed before base line k" (0..len(lines)). It is unsafe
    after a base line that ends in a line continuation, inside a verbatim region of ``lang``
    (heredoc, block scalar, multi-line or raw string, block comment, HTML raw-text element), or
    in or next to a Go example's expected output. Scanners that lose track fail closed: the rest
    of the file is unsafe. A language with no scanner (JS/TS among them) is unsafe at every
    position.

    The one position this does not report is the one directly below a YAML block scalar's last
    line: whether it is safe depends on the inserted text, so ``context_guard`` decides it.
    """
    examples = go_example_output_points(lines) if lang.name == "go" else set()
    return _continuation_points(lines) | _verbatim_points(lines, lang) | examples


def _tail_conflict(tail: _BlockTail, lines: list[str]) -> tuple[int, str] | None:
    """The first inserted line that would join a block scalar, as ``(offset, reason)``."""
    for offset, line in enumerate(lines):
        indent = _indent(line)
        if tail.opener_indent < 0:
            return offset, "the opener is not a `key: |` or `- |` line, so any line may join it"
        if line[indent:].startswith("\t"):
            return offset, "tab-indented, so its indentation cannot be compared"
        if indent > tail.opener_indent:
            return offset, f"indented {indent}, deeper than the opener line ({tail.opener_indent})"
        if tail.keep and not line.strip():
            return offset, "a blank line is content of a keep-chomped block scalar"
    return None


def context_guard(before: str, after: str, lang: Lang) -> str | None:
    """Fail any comment-lines insert at an unsafe position. Return a detail, or None.

    The position right after a YAML block scalar is the one case decided by the inserted text
    rather than by the position alone, so it is checked here, where the inserts are known.
    """
    base = before.splitlines()
    continued = _continuation_points(base)
    examples = go_example_output_points(base) if lang.name == "go" else set()
    unsafe = continued | _verbatim_points(base, lang)
    tails = _yaml_scan(base)[1] if lang.name == "yaml" else {}
    for pos, start, lines in inserted_lines(before, after):
        if pos in continued:
            return f"inserted after a line continuation (base line {pos}, edited line {start})"
        if pos in examples:
            return (
                f"inserted in or next to a Go example output comment "
                f"(after base line {pos}, edited line {start})"
            )
        if pos in unsafe:
            return f"inserted inside a verbatim region (after base line {pos}, edited line {start})"
        conflict = _tail_conflict(tails[pos], lines) if pos in tails else None
        if conflict:
            offset, why = conflict
            return (
                f"inserted line would join the block scalar above it: {why} "
                f"(after base line {pos}, edited line {start + offset})"
            )
    return None
