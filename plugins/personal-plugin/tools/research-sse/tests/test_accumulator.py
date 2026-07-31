"""Behavioural tests for the accumulator — one per required behaviour.

Guard-to-test map (each row is a mutation target: delete or invert the guard
and the named test must FAIL):

=========================== ==================================================
Guard                       Test
=========================== ==================================================
refusal branch              test_refusal.py::test_refusal_exits_non_zero
completeness sentinel       test_no_terminal_event_is_incomplete
mid-stream error branch     test_error_event_after_start_exits_non_zero
thinking/delta-type skip    test_reasoning_is_not_concatenated_into_text
truncation marker           test_truncation_exits_zero_and_is_flagged
empty-output branch         test_completed_but_empty_is_not_success
no-stream branch            test_empty_stream_exits_non_zero
malformed-data tolerance    test_malformed_data_line_is_survivable
unknown-event tolerance     test_unknown_event_and_block_types_are_ignored
category placement search   test_refusal.py::...category_from_unexpected_placement
=========================== ==================================================
"""

from __future__ import annotations

import pytest

from conftest import fixture_lines
from research_sse.accumulator import (
    COMPLETION_REASONS,
    EXIT_EMPTY_OUTPUT,
    EXIT_INCOMPLETE,
    EXIT_NO_STREAM,
    EXIT_OK,
    EXIT_REFUSAL,
    EXIT_STREAM_ERROR,
    REFUSAL_REASONS,
    TRUNCATION_REASONS,
    accumulate,
    find_refusal_category,
    parse_sse,
)

# --------------------------------------------------------------------------
# 1. Complete stream -> concatenated text, exit 0
# --------------------------------------------------------------------------


def test_happy_path_emits_text_and_exits_zero() -> None:
    result = accumulate(fixture_lines("happy_path.sse"))
    assert result.exit_code == EXIT_OK
    assert result.status == "ok"
    assert result.stop_reason == "end_turn"
    assert result.text == "## Key Findings\n\nStreaming avoids the output ceiling."
    assert result.truncated is False
    assert result.saw_message_start is True
    assert result.saw_message_stop is True


# --------------------------------------------------------------------------
# 2. Reasoning blocks are skipped, not concatenated
# --------------------------------------------------------------------------


def test_reasoning_is_not_concatenated_into_text() -> None:
    """thinking_delta / signature_delta must never reach the report body."""
    result = accumulate(fixture_lines("interleaved_reasoning.sse"))
    assert result.exit_code == EXIT_OK
    assert result.text == "VISIBLE_ONE VISIBLE_TWO"
    assert "REASONING_MUST_NOT_APPEAR" not in result.text
    assert "REASONING_MUST_NOT_APPEAR_EITHER" not in result.text
    assert "SIGNATURE_MUST_NOT_APPEAR" not in result.text
    assert "thinking_delta" in result.skipped_delta_types


def test_text_delta_inside_a_thinking_block_is_still_skipped() -> None:
    """The block-type gate is independent of the delta-type gate.

    Belt-and-braces: even if a reasoning block somehow emitted a `text_delta`,
    it must not land in the findings.
    """
    stream = [
        "event: content_block_start\n",
        'data: {"type":"content_block_start","index":0,'
        '"content_block":{"type":"thinking","thinking":""}}\n',
        "\n",
        "event: content_block_delta\n",
        'data: {"type":"content_block_delta","index":0,'
        '"delta":{"type":"text_delta","text":"LEAKED"}}\n',
        "\n",
        "event: message_delta\n",
        'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}\n',
        "\n",
    ]
    result = accumulate(stream)
    assert "LEAKED" not in result.text
    assert result.exit_code == EXIT_EMPTY_OUTPUT


# --------------------------------------------------------------------------
# 3. Completeness sentinel
# --------------------------------------------------------------------------


def test_no_terminal_event_is_incomplete() -> None:
    """Absence of a terminal event is a failure regardless of transport status."""
    result = accumulate(fixture_lines("no_terminal_event.sse"))
    assert result.exit_code == EXIT_INCOMPLETE
    assert result.status == "incomplete"
    assert result.stop_reason is None
    # Text was accumulated and is non-empty — this must still fail. The whole
    # point is that partial content plus a clean header is not success.
    assert result.text
    assert "without a terminal event" in result.message


def test_message_stop_without_stop_reason_is_still_incomplete() -> None:
    """`message_stop` alone does not tell us WHY the turn ended."""
    stream = [
        "event: message_start\n",
        'data: {"type":"message_start","message":{"id":"m","stop_reason":null}}\n',
        "\n",
        "event: content_block_start\n",
        'data: {"type":"content_block_start","index":0,'
        '"content_block":{"type":"text","text":"hi"}}\n',
        "\n",
        "event: message_stop\n",
        'data: {"type":"message_stop"}\n',
        "\n",
    ]
    result = accumulate(stream)
    assert result.saw_message_stop is True
    assert result.exit_code == EXIT_INCOMPLETE


# --------------------------------------------------------------------------
# 4. Mid-stream error event
# --------------------------------------------------------------------------


def test_error_event_after_start_exits_non_zero() -> None:
    result = accumulate(fixture_lines("mid_stream_error.sse"))
    assert result.exit_code == EXIT_STREAM_ERROR
    assert result.status == "stream_error"
    assert result.saw_message_start is True
    assert "after a successful start" in result.message
    assert "Overloaded" in result.message
    # Partial text existed; it must not be mistaken for a usable report.
    assert result.text


def test_error_event_outranks_a_terminal_reason() -> None:
    """An error plus a stop_reason must still fail — the error wins."""
    stream = [
        "event: message_start\n",
        'data: {"type":"message_start","message":{"id":"m","stop_reason":null}}\n',
        "\n",
        "event: content_block_start\n",
        'data: {"type":"content_block_start","index":0,'
        '"content_block":{"type":"text","text":"partial"}}\n',
        "\n",
        "event: message_delta\n",
        'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}\n',
        "\n",
        "event: error\n",
        'data: {"type":"error","error":{"type":"api_error"}}\n',
        "\n",
    ]
    result = accumulate(stream)
    assert result.exit_code == EXIT_STREAM_ERROR
    assert "api_error" in result.message


# --------------------------------------------------------------------------
# 6. Truncation at the ceiling
# --------------------------------------------------------------------------


def test_truncation_exits_zero_and_is_flagged() -> None:
    """Truncation keeps the content (exit 0) but is distinct from plain success."""
    result = accumulate(fixture_lines("truncation_max_tokens.sse"))
    assert result.exit_code == EXIT_OK
    assert result.truncated is True
    assert result.status == "truncated"
    assert result.status != "ok"
    assert result.to_meta()["truncated"] is True
    assert result.text.startswith("## Key Findings")


def test_success_is_not_flagged_as_truncated() -> None:
    """The other half of 'distinct from plain success'."""
    result = accumulate(fixture_lines("happy_path.sse"))
    assert result.exit_code == EXIT_OK
    assert result.truncated is False
    assert result.status == "ok"


@pytest.mark.parametrize("reason", sorted(TRUNCATION_REASONS))
def test_every_truncation_reason_is_flagged(reason: str) -> None:
    """Parametrised from the constant, not a copy of it."""
    result = accumulate(_minimal_stream(reason, "content"))
    assert result.truncated is True
    assert result.exit_code == EXIT_OK


@pytest.mark.parametrize("reason", sorted(COMPLETION_REASONS))
def test_every_completion_reason_is_plain_success(reason: str) -> None:
    result = accumulate(_minimal_stream(reason, "content"))
    assert result.exit_code == EXIT_OK
    assert result.truncated is False
    assert result.stop_reason_known is True


@pytest.mark.parametrize("reason", sorted(REFUSAL_REASONS))
def test_every_refusal_reason_fails(reason: str) -> None:
    result = accumulate(_minimal_stream(reason, "content"))
    assert result.exit_code == EXIT_REFUSAL


def test_out_of_set_stop_reason_is_kept_but_flagged_unknown() -> None:
    """The out-of-set value the parametrised tests above cannot cover.

    Bugs of this class live entirely in the unrecognised-value branch, so it
    gets its own fixture: content is kept (exit 0) but `stop_reason_known` is
    False so a caller can tell it was never understood.
    """
    result = accumulate(fixture_lines("unknown_stop_reason.sse"))
    assert result.exit_code == EXIT_OK
    assert result.stop_reason == "some_future_stop_reason"
    assert result.stop_reason_known is False
    assert result.truncated is False
    assert "not recognised" in result.message


def test_unknown_stop_reason_with_no_text_still_fails() -> None:
    """An unrecognised terminal reason must not become a silent empty report."""
    result = accumulate(_minimal_stream("some_future_stop_reason", ""))
    assert result.exit_code == EXIT_EMPTY_OUTPUT


# --------------------------------------------------------------------------
# 7. Malformed data line
# --------------------------------------------------------------------------


def test_malformed_data_line_is_survivable() -> None:
    """A bad `data:` payload is skipped and counted, never a traceback."""
    result = accumulate(fixture_lines("malformed_data_line.sse"))
    assert result.exit_code == EXIT_OK
    assert result.malformed_data_lines == 2
    assert result.text == "BEFORE AFTER"


def test_data_line_holding_valid_but_non_object_json_is_malformed() -> None:
    result = accumulate(["event: message_delta\n", "data: [1, 2, 3]\n", "\n"])
    assert result.malformed_data_lines == 1
    assert result.exit_code == EXIT_NO_STREAM


# --------------------------------------------------------------------------
# 8. Forward compatibility
# --------------------------------------------------------------------------


def test_unknown_event_and_block_types_are_ignored() -> None:
    """An unrecognised event type or block type must never be fatal."""
    result = accumulate(fixture_lines("unknown_event_and_block.sse"))
    assert result.exit_code == EXIT_OK
    assert result.text == "SURVIVES"
    assert "some_future_event" in result.unknown_event_types
    assert "some_future_block" in result.unknown_block_types


# --------------------------------------------------------------------------
# 9 & 10. Not a stream at all
# --------------------------------------------------------------------------


def test_empty_stream_exits_non_zero() -> None:
    result = accumulate(fixture_lines("empty_stream.sse"))
    assert result.exit_code == EXIT_NO_STREAM
    assert result.events_seen == 0
    assert "empty stream" in result.message


def test_non_stream_error_body_exits_non_zero_with_a_useful_message() -> None:
    """A plain JSON error object with no SSE framing must be explained, not shrugged at."""
    result = accumulate(fixture_lines("non_stream_error_body.sse"))
    assert result.exit_code == EXIT_NO_STREAM
    assert "non-stream API error body" in result.message
    assert "budget_tokens" in result.message


def test_non_stream_non_json_body_is_reported() -> None:
    result = accumulate(["<html><body>502 Bad Gateway</body></html>\n"])
    assert result.exit_code == EXIT_NO_STREAM
    assert "not an SSE stream" in result.message
    assert "502" in result.message


def test_non_stream_json_without_error_key_is_reported() -> None:
    result = accumulate(['{"id": "msg_01", "content": []}\n'])
    assert result.exit_code == EXIT_NO_STREAM
    assert "no SSE events" in result.message


# --------------------------------------------------------------------------
# 5. Completed but empty
# --------------------------------------------------------------------------


def test_completed_but_empty_is_not_success() -> None:
    """Reasoning-only output reaches a clean end_turn but is not a report."""
    result = accumulate(fixture_lines("empty_text_end_turn.sse"))
    assert result.exit_code == EXIT_EMPTY_OUTPUT
    assert result.status == "empty_output"
    assert result.text == ""
    assert "produced no text" in result.message


# --------------------------------------------------------------------------
# Parser and helper units
# --------------------------------------------------------------------------


def test_multi_line_data_is_joined_per_sse_spec() -> None:
    events = list(parse_sse(["event: x\n", 'data: {"a":\n', "data: 1}\n", "\n"]))
    assert len(events) == 1
    assert events[0].data == {"a": 1}


def test_comments_and_unknown_fields_are_ignored() -> None:
    events = list(parse_sse([": keep-alive\n", "id: 7\n", "retry: 100\n", "event: ping\n", "\n"]))
    assert [event.type for event in events] == ["ping"]


def test_event_name_falls_back_to_the_payload_type() -> None:
    events = list(parse_sse(['data: {"type":"message_stop"}\n', "\n"]))
    assert events[0].type == "message_stop"


def test_trailing_event_without_a_blank_line_is_dispatched() -> None:
    """A stream cut off before its final blank line must not lose the last event."""
    events = list(parse_sse(["event: message_stop\n", 'data: {"type":"message_stop"}\n']))
    assert [event.type for event in events] == ["message_stop"]


def test_crlf_line_endings_are_handled() -> None:
    result = accumulate(
        [
            "event: content_block_start\r\n",
            'data: {"type":"content_block_start","index":0,'
            '"content_block":{"type":"text","text":"crlf"}}\r\n',
            "\r\n",
            "event: message_delta\r\n",
            'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}\r\n',
            "\r\n",
        ]
    )
    assert result.text == "crlf"
    assert result.exit_code == EXIT_OK


def test_find_refusal_category_tolerates_junk() -> None:
    assert find_refusal_category(None, "a string", 42, []) == (False, None)


def test_find_refusal_category_reads_a_nested_details_object() -> None:
    assert find_refusal_category({"a": {"b": {"stop_details": {"category": "cyber"}}}}) == (
        True,
        "cyber",
    )


def test_find_refusal_category_treats_empty_string_as_unknown() -> None:
    assert find_refusal_category({"stop_details": {"category": ""}}) == (True, None)


def test_find_refusal_category_searches_inside_lists() -> None:
    assert find_refusal_category({"items": [{"stop_details": {"category": "bio"}}]}) == (
        True,
        "bio",
    )


def test_find_refusal_category_is_depth_bounded() -> None:
    """A pathological nesting must terminate rather than recurse forever."""
    deep: dict[str, object] = {"stop_details": {"category": "cyber"}}
    for _ in range(50):
        deep = {"n": deep}
    assert find_refusal_category(deep) == (False, None)


def test_raw_capture_is_bounded() -> None:
    """The non-stream diagnostic must not buffer an unbounded body."""
    result = accumulate(["x" * 10_000 + "\n" for _ in range(50)], raw_capture_limit=100)
    assert result.exit_code == EXIT_NO_STREAM
    assert len(result.message) < 500


def test_out_of_order_block_indices_are_joined_in_index_order() -> None:
    stream = [
        "event: content_block_start\n",
        'data: {"type":"content_block_start","index":1,'
        '"content_block":{"type":"text","text":"SECOND"}}\n',
        "\n",
        "event: content_block_start\n",
        'data: {"type":"content_block_start","index":0,'
        '"content_block":{"type":"text","text":"FIRST"}}\n',
        "\n",
        "event: message_delta\n",
        'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}\n',
        "\n",
    ]
    assert accumulate(stream).text == "FIRSTSECOND"


def test_meta_is_json_serialisable_and_excludes_the_body() -> None:
    import json

    meta = accumulate(fixture_lines("happy_path.sse")).to_meta()
    json.dumps(meta)
    assert "text" not in meta
    assert meta["text_chars"] > 0


def test_ok_property_tracks_the_exit_code() -> None:
    assert accumulate(fixture_lines("happy_path.sse")).ok is True
    assert accumulate(fixture_lines("refusal_with_category.sse")).ok is False


def _minimal_stream(stop_reason: str, text: str) -> list[str]:
    """Build the smallest stream that reaches ``stop_reason`` with ``text``."""
    import json as _json

    lines: list[str] = [
        "event: message_start\n",
        'data: {"type":"message_start","message":{"id":"m","stop_reason":null}}\n',
        "\n",
    ]
    if text:
        block = _json.dumps(
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": text},
            }
        )
        lines += ["event: content_block_start\n", f"data: {block}\n", "\n"]
    delta = _json.dumps({"type": "message_delta", "delta": {"stop_reason": stop_reason}})
    lines += ["event: message_delta\n", f"data: {delta}\n", "\n"]
    lines += ["event: message_stop\n", 'data: {"type":"message_stop"}\n', "\n"]
    return lines


# --------------------------------------------------------------------------
# Error-message extraction — 6.2 surfaces these strings to the operator, so
# every shape the API might send needs a message that is actually useful.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            '{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}',
            "Overloaded",
        ),
        ('{"type":"error","error":{"type":"api_error"}}', "api_error"),
        ('{"type":"error","error":{}}', "unknown stream error"),
        ('{"type":"error","message":"top level message"}', "top level message"),
        ('{"type":"error"}', "unknown stream error"),
        ('{"type":"error","error":"not-a-mapping"}', "unknown stream error"),
    ],
)
def test_error_event_message_extraction(payload: str, expected: str) -> None:
    result = accumulate(["event: error\n", f"data: {payload}\n", "\n"])
    assert result.exit_code == EXIT_STREAM_ERROR
    assert expected in result.message


def test_error_event_before_any_start_is_labelled_as_such() -> None:
    result = accumulate(
        ["event: error\n", 'data: {"type":"error","error":{"type":"api_error"}}\n', "\n"]
    )
    assert result.exit_code == EXIT_STREAM_ERROR
    assert "before any start" in result.message


def test_message_delta_with_null_stop_reason_is_not_terminal() -> None:
    """An intermediate `message_delta` carries only usage — it must not end the stream.

    Treating any `message_delta` as terminal would defeat the completeness
    sentinel: a usage-only delta would resolve to `stop_reason=None` and then
    be reported as a successful, complete run.
    """
    result = accumulate(
        [
            "event: content_block_start\n",
            'data: {"type":"content_block_start","index":0,'
            '"content_block":{"type":"text","text":"partial"}}\n',
            "\n",
            "event: message_delta\n",
            'data: {"type":"message_delta","delta":{"stop_reason":null},'
            '"usage":{"output_tokens":10}}\n',
            "\n",
        ]
    )
    assert result.stop_reason is None
    assert result.exit_code == EXIT_INCOMPLETE


def test_error_message_helper_tolerates_a_missing_payload() -> None:
    """Defensive path: the helper must never raise on a null payload."""
    from research_sse.accumulator import _error_message

    assert _error_message(None) == "unknown stream error"
