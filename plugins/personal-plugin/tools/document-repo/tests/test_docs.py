from pathlib import Path

import pytest

from document_repo.cli import main
from document_repo.docs import marker_pair, upsert_file, upsert_section


def test_append_keeps_human_text() -> None:
    start, end = marker_pair("overview")
    out = upsert_section("# Title\n\nHuman words.\n", "overview", "Generated.\n")
    assert out == f"# Title\n\nHuman words.\n\n{start}\nGenerated.\n{end}\n"


def test_replace_only_between_markers() -> None:
    first = upsert_section("Top\n", "a", "one")
    second = upsert_section(first + "Bottom\n", "a", "two")
    assert "one" not in second and "two" in second
    assert second.startswith("Top\n") and second.endswith("Bottom\n")


def test_idempotent() -> None:
    once = upsert_section("x\n", "a", "body")
    assert upsert_section(once, "a", "body") == once


def test_empty_file() -> None:
    start, end = marker_pair("a")
    assert upsert_section("", "a", "b") == f"{start}\nb\n{end}\n"


@pytest.mark.parametrize(
    "text,name,needle",
    [
        ("x", "Bad Name", "section name"),
        ("<!-- document-repo:start:a -->\nno end\n", "a", "no end marker"),
        ("<!-- document-repo:end:a -->\n", "a", "without a start"),
        (
            "<!-- document-repo:start:a -->\n<!-- document-repo:end:a -->\n"
            "<!-- document-repo:start:a -->\n<!-- document-repo:end:a -->\n",
            "a",
            "more than once",
        ),
    ],
)
def test_errors(text: str, name: str, needle: str) -> None:
    with pytest.raises(ValueError, match=needle):
        upsert_section(text, name, "b")


def test_upsert_file_creates_parents(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "GLOSSARY.md"
    upsert_file(target, "glossary", "Terms")
    assert "Terms" in target.read_text()


def test_crlf_human_lines_survive_upsert(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_bytes(b"# Mine\r\n\r\nHuman words.\r\n")
    upsert_file(target, "overview", "Generated.")
    raw = target.read_bytes()
    start, end = marker_pair("overview")
    assert raw.startswith(b"# Mine\r\n\r\nHuman words.\r\n")
    assert raw.count(b"\r\n") == raw.count(b"\n")
    assert f"{start}\r\nGenerated.\r\n{end}\r\n".encode() in raw


def test_crlf_upsert_replaces_inside_markers_only(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    upsert_file(target, "overview", "one")
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n") + b"Tail\r\n")
    upsert_file(target, "overview", "two")
    raw = target.read_bytes()
    assert b"one" not in raw and b"two" in raw
    assert raw.endswith(b"Tail\r\n")
    assert raw.count(b"\r\n") == raw.count(b"\n")


def test_non_utf8_file_raises_value_error(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_bytes(b"# Latin-1 \xe9 text\n")
    with pytest.raises(ValueError, match="not valid UTF-8"):
        upsert_file(target, "overview", "body")
    assert target.read_bytes() == b"# Latin-1 \xe9 text\n"


def test_cli(tmp_path: Path) -> None:
    content = tmp_path / "c.md"
    content.write_text("Hello")
    target = tmp_path / "README.md"
    target.write_text("# Mine\n")
    assert (
        main(
            [
                "upsert-section",
                "--file",
                str(target),
                "--section",
                "overview",
                "--content-file",
                str(content),
            ]
        )
        == 0
    )
    assert target.read_text().startswith("# Mine\n") and "Hello" in target.read_text()
    assert (
        main(
            [
                "upsert-section",
                "--file",
                str(target),
                "--section",
                "BAD",
                "--content-file",
                str(content),
            ]
        )
        == 2
    )


def test_cli_missing_content_file_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "README.md"
    target.write_text("# Mine\n")
    rc = main(
        [
            "upsert-section",
            "--file",
            str(target),
            "--section",
            "overview",
            "--content-file",
            str(tmp_path / "nope.md"),
        ]
    )
    assert rc == 2
    assert capsys.readouterr().err.startswith("upsert-section: ")
    assert target.read_text() == "# Mine\n"


def test_cli_non_utf8_target_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    content = tmp_path / "c.md"
    content.write_text("Hello")
    target = tmp_path / "README.md"
    target.write_bytes(b"\xff\xfe bad\n")
    rc = main(
        [
            "upsert-section",
            "--file",
            str(target),
            "--section",
            "overview",
            "--content-file",
            str(content),
        ]
    )
    assert rc == 2
    assert "upsert-section: " in capsys.readouterr().err
