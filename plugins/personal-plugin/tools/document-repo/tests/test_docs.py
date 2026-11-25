import os
import re
import sys
from pathlib import Path

import pytest

from document_repo.cli import main
from document_repo.docs import marker_pair, upsert_file, upsert_section

START, END = marker_pair("a")
START_B, END_B = marker_pair("b")


def assert_human_bytes_intact(
    out: str | bytes,
    name: str,
    before: str,
    after: str = "",
    *,
    separator: str = "",
    terminator: str = "",
) -> None:
    """The bytes before the start marker and after the end marker are the original human bytes.

    ``before`` and ``after`` are the original human text, spelled out. An append adds only line
    breaks: ``separator`` between the original text and the new section, and ``terminator`` after
    the end marker.
    """
    raw = out if isinstance(out, bytes) else out.encode("utf-8")
    start, end = (m.encode("utf-8") for m in marker_pair(name))
    head = (before + separator).encode("utf-8")
    tail = (after + terminator).encode("utf-8")
    assert raw[: len(head)] == head, "bytes before the start marker changed"
    assert raw[len(head) :].startswith(start), "start marker is not where the human text ends"
    assert raw[len(raw) - len(tail) :] == tail, "bytes after the end marker changed"
    assert raw[: len(raw) - len(tail)].endswith(end), (
        "end marker is not where the human text resumes"
    )


def test_append_keeps_human_text() -> None:
    start, end = marker_pair("overview")
    original = "# Title\n\nHuman words.\n"
    out = upsert_section(original, "overview", "Generated.\n")
    assert out == f"# Title\n\nHuman words.\n\n{start}\nGenerated.\n{end}\n"
    assert_human_bytes_intact(out, "overview", original, separator="\n", terminator="\n")


def test_replace_only_between_markers() -> None:
    first = upsert_section("Top\n", "a", "one")
    second = upsert_section(first + "Bottom\n", "a", "two")
    assert "one" not in second and "two" in second
    assert second.startswith("Top\n") and second.endswith("Bottom\n")
    assert_human_bytes_intact(second, "a", "Top\n", "\nBottom\n", separator="\n")


def test_idempotent() -> None:
    once = upsert_section("x\n", "a", "body")
    assert upsert_section(once, "a", "body") == once
    assert_human_bytes_intact(once, "a", "x\n", separator="\n", terminator="\n")


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


# --- 1. Append never rewrites existing bytes --------------------------------------------------


@pytest.mark.parametrize(
    "original,separator,eol",
    [
        pytest.param("a\nb\r\nc\nd\n", "\n", "\n", id="mixed-endings-last-lf"),
        pytest.param("a\r\nb\nc\r\n", "\r\n", "\r\n", id="mixed-endings-last-crlf"),
        pytest.param("a\rb\r", "\r", "\r", id="lone-cr"),
        pytest.param("x\n\n\n", "", "\n", id="trailing-blank-lines"),
        pytest.param("x\r\n\r\n\r\n", "", "\r\n", id="trailing-blank-lines-crlf"),
        pytest.param("x\n \t\n", "", "\n", id="trailing-blank-line-with-spaces"),
        pytest.param("x", "\n\n", "\n", id="no-trailing-newline"),
        pytest.param("x\r\ny", "\r\n\r\n", "\r\n", id="no-trailing-newline-crlf"),
        pytest.param("x\n\n  ", "\n", "\n", id="blank-last-line-without-newline"),
        pytest.param("﻿# T\n", "\n", "\n", id="bom"),
        pytest.param("﻿\n", "", "\n", id="bom-then-newline"),
        pytest.param("\n\n  \n", "", "\n", id="whitespace-only-with-newlines"),
        pytest.param("\n", "", "\n", id="single-newline"),
        pytest.param("\r\n\r\n", "", "\r\n", id="newlines-only-crlf"),
        pytest.param("\n  ", "\n", "\n", id="whitespace-only-ending-without-newline"),
    ],
)
def test_append_never_rewrites_existing_bytes(original: str, separator: str, eol: str) -> None:
    out = upsert_section(original, "a", "g\nh")
    assert out == f"{original}{separator}{START}{eol}g{eol}h{eol}{END}{eol}"
    assert_human_bytes_intact(out, "a", original, separator=separator, terminator=eol)


@pytest.mark.parametrize(
    "original,kept",
    [
        pytest.param("", "", id="empty"),
        pytest.param("   ", "", id="spaces"),
        pytest.param("\t ", "", id="tab-and-space"),
        pytest.param("﻿", "﻿", id="bom-only"),
        pytest.param("﻿  ", "﻿", id="bom-and-spaces"),
    ],
)
def test_append_to_empty_or_blank_without_newline_writes_the_block_alone(
    original: str, kept: str
) -> None:
    out = upsert_section(original, "a", "b")
    assert out == f"{kept}{START}\nb\n{END}\n"
    assert_human_bytes_intact(out, "a", kept, terminator="\n")


def test_bom_file_keeps_its_bom_through_append_and_replace(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    original = "﻿# T\r\nhuman\r\n"
    target.write_bytes(original.encode("utf-8"))
    upsert_file(target, "a", "g")
    assert_human_bytes_intact(
        target.read_bytes(), "a", original, separator="\r\n", terminator="\r\n"
    )
    upsert_file(target, "a", "g2")
    assert target.read_bytes() == f"{original}\r\n{START}\r\ng2\r\n{END}\r\n".encode()
    assert_human_bytes_intact(
        target.read_bytes(), "a", original, separator="\r\n", terminator="\r\n"
    )


def test_marker_on_the_first_line_of_a_bom_file_is_recognised() -> None:
    text = f"﻿{START}\nold\n{END}\ntail"
    out = upsert_section(text, "a", "new")
    assert out == f"﻿{START}\nnew\n{END}\ntail"
    assert_human_bytes_intact(out, "a", "﻿", "\ntail")


def test_crlf_human_lines_survive_upsert(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    original = "# Mine\r\n\r\nHuman words.\r\n"
    target.write_bytes(original.encode())
    upsert_file(target, "overview", "Generated.")
    raw = target.read_bytes()
    start, end = marker_pair("overview")
    assert raw.startswith(original.encode())
    assert raw.count(b"\r\n") == raw.count(b"\n")
    assert f"{start}\r\nGenerated.\r\n{end}\r\n".encode() in raw
    assert_human_bytes_intact(raw, "overview", original, separator="\r\n", terminator="\r\n")


def test_crlf_upsert_replaces_inside_markers_only(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    upsert_file(target, "overview", "one")
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n") + b"Tail\r\n")
    upsert_file(target, "overview", "two")
    raw = target.read_bytes()
    assert b"one" not in raw and b"two" in raw
    assert raw.endswith(b"Tail\r\n")
    assert raw.count(b"\r\n") == raw.count(b"\n")
    assert_human_bytes_intact(raw, "overview", "", "\r\nTail\r\n")


def test_replace_without_trailing_newline_keeps_the_tail_exactly() -> None:
    text = f"head\r\n{START}\r\nold\r\n{END}\r\ntail-no-nl"
    out = upsert_section(text, "a", "new")
    assert out == f"head\r\n{START}\r\nnew\r\n{END}\r\ntail-no-nl"
    assert_human_bytes_intact(out, "a", "head\r\n", "\r\ntail-no-nl")
    text = f"{START}\nold\n{END}"
    assert upsert_section(text, "a", "new") == f"{START}\nnew\n{END}"


# --- 2. Markers count only alone on a line, outside fenced code -------------------------------

FENCED_EXAMPLE = (
    f"# Docs\n\nExample:\n\n```md\n{START}\nexample body\n{END}\n```\n\nMore human text.\n"
)


def test_markers_shown_in_a_fenced_example_are_not_a_section() -> None:
    out = upsert_section(FENCED_EXAMPLE, "a", "GENERATED")
    assert out == f"{FENCED_EXAMPLE}\n{START}\nGENERATED\n{END}\n"
    assert_human_bytes_intact(out, "a", FENCED_EXAMPLE, separator="\n", terminator="\n")
    assert upsert_section(out, "a", "GENERATED") == out


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(f"Use `{START}` to start.\n", id="start-in-prose"),
        pytest.param(f"Close with `{END}`.\n", id="end-in-prose"),
        pytest.param(f"{START} and {END}\n", id="both-on-one-line"),
        pytest.param(f"note {START}\n{END} note\n", id="text-around-each-marker"),
    ],
)
def test_inline_mention_of_a_marker_is_ignored(text: str) -> None:
    out = upsert_section(text, "a", "G")
    assert out == f"{text}\n{START}\nG\n{END}\n"
    assert_human_bytes_intact(out, "a", text, separator="\n", terminator="\n")


def test_fence_plus_real_section_replaces_only_the_real_section() -> None:
    before = f"```md\n{START}\nexample\n{END}\n```\n\n"
    tail = "\nTail.\n"
    out = upsert_section(before + f"{START}\nold\n{END}" + tail, "a", "new")
    assert out == before + f"{START}\nnew\n{END}" + tail
    assert_human_bytes_intact(out, "a", before, tail)


def test_fence_tracks_character_and_length() -> None:
    text = (
        "````md\n"  # four backticks open the fence
        "```\n"  # too short to close it
        f"{START}\n"
        "~~~\n"  # a different character does not close it
        "```` js\n"  # text after the fence characters does not close it
        f"{END}\n"
        "````\n"  # closes it
        "after\n"
    )
    out = upsert_section(text, "a", "G")
    assert out == f"{text}\n{START}\nG\n{END}\n"
    assert_human_bytes_intact(out, "a", text, separator="\n", terminator="\n")


def test_tilde_fence_with_indent_and_trailing_blanks_on_the_closer() -> None:
    before = f"  ~~~md\n{START}\n~~~~ \t\n"
    out = upsert_section(before + f"{START}\nold\n{END}\n", "a", "new")
    assert out == before + f"{START}\nnew\n{END}\n"
    assert_human_bytes_intact(out, "a", before, "\n")


def test_backticks_in_the_info_string_do_not_open_a_fence() -> None:
    before = "```not a fence```\n"
    out = upsert_section(before + f"{START}\nold\n{END}\n", "a", "new")
    assert out == before + f"{START}\nnew\n{END}\n"


def test_unclosed_fence_is_refused() -> None:
    with pytest.raises(ValueError, match="never closed"):
        upsert_section("intro\n```md\nno closer\n", "a", "G")


def test_marker_lines_may_carry_surrounding_whitespace() -> None:
    text = f"head\n  {START}  \nold\n\t{END} \t\ntail"
    out = upsert_section(text, "a", "new")
    assert out == f"head\n  {START}\nnew\n{END} \t\ntail"
    assert_human_bytes_intact(out, "a", "head\n  ", " \t\ntail")


# --- 3. A body must not contain markers -------------------------------------------------------


@pytest.mark.parametrize(
    "marker",
    [
        pytest.param(START, id="own-start"),
        pytest.param(END, id="own-end"),
        pytest.param(START_B, id="other-start"),
        pytest.param(END_B, id="other-end"),
        pytest.param("see document-repo:start:zz in prose", id="start-fragment"),
        pytest.param("see document-repo:end:zz in prose", id="end-fragment"),
    ],
)
def test_body_containing_a_marker_is_rejected(marker: str) -> None:
    with pytest.raises(ValueError, match="body contains"):
        upsert_section("human\n", "a", f"x\n{marker}\ny")


# --- 4. Symlinks are written through ----------------------------------------------------------

needs_symlinks = pytest.mark.skipif(
    sys.platform == "win32", reason="symlinks need elevated rights on Windows"
)


@needs_symlinks
def test_symlink_is_written_through_and_kept(tmp_path: Path) -> None:
    real = tmp_path / "AGENTS.md"
    original = "# Agents\r\n\r\nHuman.\r\n"
    real.write_bytes(original.encode())
    link = tmp_path / "CLAUDE.md"
    link.symlink_to("AGENTS.md")
    upsert_file(link, "a", "gen")
    assert link.is_symlink() and os.readlink(link) == "AGENTS.md"
    assert_human_bytes_intact(real.read_bytes(), "a", original, separator="\r\n", terminator="\r\n")
    assert link.read_bytes() == real.read_bytes()


@needs_symlinks
def test_dangling_symlink_creates_its_target(tmp_path: Path) -> None:
    link = tmp_path / "CLAUDE.md"
    link.symlink_to("AGENTS.md")
    upsert_file(link, "a", "gen")
    assert link.is_symlink()
    assert (tmp_path / "AGENTS.md").read_bytes() == f"{START}\ngen\n{END}\n".encode()


# --- 5. No overlapping or nested sections -----------------------------------------------------


def test_overlapping_sections_are_rejected() -> None:
    text = f"{START}\nA\n{START_B}\nB\n{END}\nC\n{END_B}\n"
    with pytest.raises(ValueError, match=re.escape(START_B)):
        upsert_section(text, "a", "x")
    with pytest.raises(ValueError, match=re.escape(END)):
        upsert_section(text, "b", "x")


def test_nested_sections_are_rejected() -> None:
    text = f"{START}\nA\n{START_B}\nB\n{END_B}\nC\n{END}\n"
    with pytest.raises(ValueError, match=re.escape(START_B)):
        upsert_section(text, "a", "x")


def test_fenced_or_inline_markers_inside_a_section_are_not_overlaps() -> None:
    text = f"{START}\nold\n```\n{START_B}\n```\nsee `{END_B}`\n{END}\n"
    assert upsert_section(text, "a", "new") == f"{START}\nnew\n{END}\n"


def test_adjacent_sections_do_not_overlap() -> None:
    other = f"{START_B}\nkeep\n{END_B}\n"
    out = upsert_section(f"top\n{START}\nold\n{END}\n{other}", "a", "new")
    assert out == f"top\n{START}\nnew\n{END}\n{other}"
    assert_human_bytes_intact(out, "a", "top\n", f"\n{other}")


# --- 6. Body handling -------------------------------------------------------------------------


def test_body_loses_surrounding_blank_lines_but_keeps_first_line_indent() -> None:
    out = upsert_section("h\n", "a", "\n \n    code line\n  more  \n\t\n\n")
    assert out == f"h\n\n{START}\n    code line\n  more  \n{END}\n"
    assert_human_bytes_intact(out, "a", "h\n", separator="\n", terminator="\n")


def test_body_bom_is_dropped() -> None:
    out = upsert_section("h\n", "a", "﻿Body\nline2\n")
    assert out == f"h\n\n{START}\nBody\nline2\n{END}\n"
    assert "﻿" not in out


@pytest.mark.parametrize(
    "original,eol",
    [
        pytest.param("h\n", "\n", id="lf"),
        pytest.param("h\r\n", "\r\n", id="crlf"),
        pytest.param("h\r", "\r", id="cr"),
        pytest.param("a\r\nb\nh\n", "\n", id="mixed-last-lf"),
        pytest.param("a\nb\r\nh\r\n", "\r\n", id="mixed-last-crlf"),
    ],
)
def test_body_lines_use_the_file_eol(original: str, eol: str) -> None:
    out = upsert_section(original, "a", "a\r\nb\rc\nd")
    assert out == f"{original}{eol}{START}{eol}a{eol}b{eol}c{eol}d{eol}{END}{eol}"
    assert_human_bytes_intact(out, "a", original, separator=eol, terminator=eol)


# --- files and CLI ----------------------------------------------------------------------------


def test_upsert_file_creates_parents(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "GLOSSARY.md"
    upsert_file(target, "glossary", "Terms")
    assert "Terms" in target.read_text()


def test_non_utf8_file_raises_value_error(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_bytes(b"# Latin-1 \xe9 text\n")
    with pytest.raises(ValueError, match="not valid UTF-8"):
        upsert_file(target, "overview", "body")
    assert target.read_bytes() == b"# Latin-1 \xe9 text\n"


def _cli(target: Path, section: str, content: Path) -> int:
    return main(
        [
            "upsert-section",
            "--file",
            str(target),
            "--section",
            section,
            "--content-file",
            str(content),
        ]
    )


def test_cli(tmp_path: Path) -> None:
    content = tmp_path / "c.md"
    content.write_text("Hello")
    target = tmp_path / "README.md"
    target.write_text("# Mine\n")
    assert _cli(target, "overview", content) == 0
    assert target.read_text().startswith("# Mine\n") and "Hello" in target.read_text()
    assert_human_bytes_intact(
        target.read_bytes(), "overview", "# Mine\n", separator="\n", terminator="\n"
    )
    assert _cli(target, "BAD", content) == 2


def test_cli_bad_section_name_reports_and_leaves_the_file_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    content = tmp_path / "c.md"
    content.write_text("Hello")
    target = tmp_path / "README.md"
    original = b"# Mine\r\n\r\nHuman words.\r\n"
    target.write_bytes(original)
    assert _cli(target, "BAD", content) == 2
    err = capsys.readouterr().err
    assert err.startswith("upsert-section: section name 'BAD' must match ")
    assert err.count("\n") == 1
    assert target.read_bytes() == original


def test_cli_rejects_a_content_file_that_contains_a_marker(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    content = tmp_path / "c.md"
    content.write_text(f"Hello\n{END}\n")
    target = tmp_path / "README.md"
    original = b"# Mine\n\nHuman.\n"
    target.write_bytes(original)
    assert _cli(target, "overview", content) == 2
    assert capsys.readouterr().err.startswith("upsert-section: body contains ")
    assert target.read_bytes() == original


def test_cli_missing_content_file_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "README.md"
    target.write_bytes(b"# Mine\n")
    assert _cli(target, "overview", tmp_path / "nope.md") == 2
    assert capsys.readouterr().err.startswith("upsert-section: ")
    assert target.read_bytes() == b"# Mine\n"


def test_cli_non_utf8_target_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    content = tmp_path / "c.md"
    content.write_text("Hello")
    target = tmp_path / "README.md"
    target.write_bytes(b"\xff\xfe bad\n")
    assert _cli(target, "overview", content) == 2
    assert "upsert-section: " in capsys.readouterr().err
    assert target.read_bytes() == b"\xff\xfe bad\n"
