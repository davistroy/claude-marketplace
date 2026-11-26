"""Map a file path to its language and comment syntax.

Every other module asks this table one question: "if I add a comment to this
file, what does a comment look like, and how do I prove nothing else
changed?" A file whose type is not in the table has no known comment syntax,
so the skill never comments it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

#: How verify.py proves an edit is comment-only, per language.
VERIFY_METHODS = frozenset({"python-ast", "ts-printer", "comment-lines"})


@dataclass(frozen=True)
class Lang:
    """Comment syntax for one language.

    ``line`` holds line-comment prefixes (``#``, ``//``, ``--``).
    ``block`` holds (start, end) pairs (``/*``, ``*/``).
    ``verify_method`` names the proof verify.py uses.
    ``nested_block`` is True when block comments nest (PostgreSQL, Rust): there ``/*`` inside a
    block comment opens another level, so ``/* staging/*.csv */`` is still open at its end.
    """

    name: str
    line: tuple[str, ...]
    block: tuple[tuple[str, str], ...]
    verify_method: str
    nested_block: bool = False


C_BLOCK = (("/*", "*/"),)
PYTHON = Lang("python", ("#",), (), "python-ast")
TYPESCRIPT = Lang("typescript", ("//",), C_BLOCK, "ts-printer")
JAVASCRIPT = Lang("javascript", ("//",), C_BLOCK, "ts-printer")
# PostgreSQL nests /* */; MySQL and SQLite do not. Counting depth is the strict reading of both.
SQL = Lang("sql", ("--",), C_BLOCK, "comment-lines", nested_block=True)
SHELL = Lang("shell", ("#",), (), "comment-lines")
YAML = Lang("yaml", ("#",), (), "comment-lines")
TOML = Lang("toml", ("#",), (), "comment-lines")
DOCKERFILE = Lang("dockerfile", ("#",), (), "comment-lines")
MAKE = Lang("make", ("#",), (), "comment-lines")
CSS = Lang("css", (), C_BLOCK, "comment-lines")
HTML = Lang("html", (), (("<!--", "-->"),), "comment-lines")
C_LIKE = {
    name: Lang(name, ("//",), C_BLOCK, "comment-lines", nested_block=name == "rust")
    for name in ("go", "rust", "java", "c", "cpp", "csharp")
}

EXT: dict[str, Lang] = {
    ".py": PYTHON,
    ".ts": TYPESCRIPT,
    ".tsx": TYPESCRIPT,
    ".mts": TYPESCRIPT,
    ".cts": TYPESCRIPT,
    ".js": JAVASCRIPT,
    ".jsx": JAVASCRIPT,
    ".mjs": JAVASCRIPT,
    ".cjs": JAVASCRIPT,
    ".sql": SQL,
    ".sh": SHELL,
    ".bash": SHELL,
    ".zsh": SHELL,
    ".yml": YAML,
    ".yaml": YAML,
    ".toml": TOML,
    ".css": CSS,
    ".scss": CSS,
    ".html": HTML,
    ".htm": HTML,
    ".go": C_LIKE["go"],
    ".rs": C_LIKE["rust"],
    ".java": C_LIKE["java"],
    # ``.c`` and ``.C`` (detect lowercases suffixes; GCC reads ``.C`` as C++) and ``.h`` are
    # scanned with the C and C++ readings unioned (guards._C_FAMILY), so a raw string R"( is
    # data in any of them (SE-C1, review fix 4).
    ".c": C_LIKE["c"],
    ".h": C_LIKE["cpp"],
    ".cpp": C_LIKE["cpp"],
    ".hpp": C_LIKE["cpp"],
    ".cs": C_LIKE["csharp"],
}

#: Files recognised by exact name rather than extension.
NAMES: dict[str, Lang] = {"Dockerfile": DOCKERFILE, "Makefile": MAKE, "Containerfile": DOCKERFILE}


def detect(path: str) -> Lang | None:
    """Return the Lang for ``path``, or None when it has no known comment syntax."""
    p = PurePosixPath(path)
    if p.name in NAMES:
        return NAMES[p.name]
    if p.name.startswith(("Dockerfile.", "Containerfile.")):
        return DOCKERFILE
    return EXT.get(p.suffix.lower())
