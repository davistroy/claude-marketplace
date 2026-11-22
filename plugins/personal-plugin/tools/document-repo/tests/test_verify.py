import json

import pytest

from document_repo.cli import main
from document_repo.languages import detect
from document_repo.verify import changed_source_files, comment_chunk_ok, verify_file

BASE_PY = "def add(a, b):\n    return a + b\n"


def test_python_comments_and_docstrings_pass(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text(
        '"""Math helpers."""\n\n# Why: keep it simple.\ndef add(a, b):\n'
        '    """Add two numbers."""\n    return a + b  # sum\n'
    )
    r = verify_file(repo, "m.py")
    assert r.ok and r.method == "python-ast", r.detail


def test_python_docstring_added_to_pass_body(make_repo) -> None:
    repo = make_repo({"m.py": "def f():\n    pass\n"})
    (repo / "m.py").write_text('def f():\n    """Doc."""\n    pass\n')
    assert verify_file(repo, "m.py").ok


def test_python_code_change_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text("# note\ndef add(a, b):\n    return a - b\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and r.method == "python-ast"


def test_python_syntax_error_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "m.py").write_text("def add(a, b:\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and "parse" in r.detail


def test_file_not_in_base_fails(make_repo) -> None:
    repo = make_repo({"m.py": BASE_PY})
    (repo / "new.py").write_text("x = 1\n")
    r = verify_file(repo, "new.py")
    assert not r.ok and r.method == "none"


def test_unknown_language_fails(make_repo) -> None:
    repo = make_repo({"d.json": "{}\n"})
    assert not verify_file(repo, "d.json").ok


SQL = "select 1;\nselect 2;\n"


@pytest.mark.parametrize(
    "after",
    [
        "-- Header\nselect 1;\nselect 2;\n",
        "/* block\n   more */\nselect 1;\nselect 2;\n",
        "select 1;\n\n-- why the second query\nselect 2;\n",
        "/* one-line block */\nselect 1;\nselect 2;\n",
    ],
)
def test_sql_comment_only_passes(make_repo, after: str) -> None:
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").write_text(after)
    r = verify_file(repo, "q.sql")
    assert r.ok and r.method == "comment-lines", r.detail


@pytest.mark.parametrize(
    "after,needle",
    [
        ("select 1;\nselect 3;\n", "replace"),
        ("select 1;\n", "delete"),
        ("select 1; -- trailing\nselect 2;\n", "replace"),
        ("/* open\nselect 1;\nselect 2;\n", "unterminated"),
        ("/* x */ select 0;\nselect 1;\nselect 2;\n", "code after"),
        ("select 0;\nselect 1;\nselect 2;\n", "non-comment"),
    ],
)
def test_sql_negative_cases_fail(make_repo, after: str, needle: str) -> None:
    # Negative tests: a guard that cannot fail is worse than none (repo rule).
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").write_text(after)
    r = verify_file(repo, "q.sql")
    assert not r.ok and needle in r.detail, r.detail


def test_shell_code_added_fails(make_repo) -> None:
    repo = make_repo({"run.sh": "#!/bin/sh\necho a\n"})
    (repo / "run.sh").write_text("#!/bin/sh\n# say a\necho a\necho b\n")
    assert not verify_file(repo, "run.sh").ok


def test_comment_chunk_block_end_must_close_line() -> None:
    lang = detect("x.css")
    assert comment_chunk_ok(["/* a", " b */"], lang) == (True, "")
    ok, why = comment_chunk_ok(["/* a", " b */ x {}"], lang)
    assert not ok and "code after" in why


def test_changed_source_files(make_repo) -> None:
    repo = make_repo(
        {"a.py": "x = 1\n", "README.md": "# r\n", "explorer/x.js": "x\n", "b.py": "y = 1\n"}
    )
    (repo / "a.py").write_text("# c\nx = 1\n")
    (repo / "README.md").write_text("# r2\n")
    (repo / "explorer/x.js").write_text("y\n")
    assert changed_source_files(repo, "HEAD") == ["a.py"]


def test_cli_verify_exit_codes(make_repo, capsys) -> None:
    repo = make_repo({"a.py": "x = 1\n", "b.py": "y = 1\n"})
    (repo / "a.py").write_text("# ok\nx = 1\n")
    assert main(["verify", "--repo", str(repo), "a.py"]) == 0
    (repo / "b.py").write_text("y = 2\n")
    capsys.readouterr()
    assert main(["verify", "--repo", str(repo), "--changed"]) == 1
    results = json.loads(capsys.readouterr().out)
    assert {r["path"]: r["ok"] for r in results} == {"a.py": True, "b.py": False}


def test_cli_verify_needs_files_or_changed(make_repo) -> None:
    repo = make_repo({"a.py": "x = 1\n"})
    assert main(["verify", "--repo", str(repo)]) == 2


# Fail-closed branches the brief's tests do not reach.
def test_python_base_that_does_not_parse_fails(make_repo) -> None:
    repo = make_repo({"m.py": "def add(a, b:\n"})
    (repo / "m.py").write_text("# note\ndef add(a, b:\n")
    r = verify_file(repo, "m.py")
    assert not r.ok and r.method == "python-ast" and "base version does not parse" in r.detail


def test_non_utf8_base_fails(make_repo) -> None:
    repo = make_repo({"q.sql": b"select '\xe9';\n"})
    (repo / "q.sql").write_text("-- note\nselect 1;\n", encoding="utf-8")
    r = verify_file(repo, "q.sql")
    assert not r.ok and r.method == "none" and "UTF-8" in r.detail


def test_deleted_working_file_fails(make_repo) -> None:
    repo = make_repo({"q.sql": SQL})
    (repo / "q.sql").unlink()
    r = verify_file(repo, "q.sql")
    assert not r.ok and r.method == "none" and "cannot read edited file" in r.detail
