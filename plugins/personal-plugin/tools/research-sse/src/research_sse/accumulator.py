"""Parse an Anthropic Messages SSE stream into report text + a terminal verdict.

The single entry point is :func:`accumulate`, which takes an iterable of raw
lines (so a caller can stream stdin rather than slurping it) and returns a
:class:`Result`. It is a pure function of its input: no I/O, no network, no
clock, no environment. That is what makes this leg testable offline for the
first time.

Design notes that are load-bearing, not decoration:

**The terminal reason lives in `message_delta`, not at the top level.** In the
non-streaming response body the terminal reason is a top-level ``stop_reason``
field. Under streaming it arrives inside a ``message_delta`` event. A port
that keeps the old top-level lookup compiles, reads correctly, and never
fires — silently writing an empty report on every refusal. Everything in
:func:`_terminal_stop_reason` exists to prevent that regression.

**The refusal category's placement is treated as UNKNOWN.** ``stop_details``
is documented as populated only on refusal, with a nullable ``category``. Its
exact nesting under streaming is not something this tool assumes: it searches
for the object wherever it sits in the terminal event, tolerates its absence,
and never lets a missing category downgrade a refusal to success.

**Absence of a terminal event is itself a failure** (the completeness
sentinel). A stream can open with HTTP 200 and then die mid-flight; the header
status says nothing about that. If no terminal reason was ever resolved, the
accumulated text is by definition incomplete and this tool fails.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

# --------------------------------------------------------------------------
# Exit-status contract. This is the interface the shell leg branches on, so
# these values are API: changing one is a breaking change to the caller.
# --------------------------------------------------------------------------

#: Complete stream, non-refusal terminal reason, non-empty text. Keep the report.
EXIT_OK = 0
#: Unexpected internal failure (a bug in this tool, not in the stream).
EXIT_INTERNAL = 1
#: Command-line usage error. Reserved for argparse, which exits 2 by default.
EXIT_USAGE = 2
#: 3 is deliberately RESERVED AND UNUSED. Truncation at the depth ceiling exits
#: 0 by design — the content is real, just cut short — and is signalled by the
#: ``truncated`` marker in the metadata instead. See module README/`Result`.
_EXIT_RESERVED = 3
#: Terminal reason indicates a safety refusal. The category (possibly unknown)
#: is on stderr and in the metadata. NEVER write a report on this.
EXIT_REFUSAL = 4
#: Completeness sentinel: the stream ended without ever resolving a terminal
#: reason. The text is incomplete regardless of the transport's exit status.
EXIT_INCOMPLETE = 5
#: An `error` event arrived on the stream (typically after a successful start).
EXIT_STREAM_ERROR = 6
#: The input contained no SSE events at all — empty body, or a plain JSON
#: error object with no SSE framing.
EXIT_NO_STREAM = 7
#: The stream completed and reached a normal terminal reason, but accumulated
#: zero characters of text. An empty research report is never a success.
EXIT_EMPTY_OUTPUT = 8

#: Terminal reasons that mean "the safety classifiers declined this request".
REFUSAL_REASONS = frozenset({"refusal"})

#: Terminal reasons that mean "real content, cut short at a ceiling". These
#: exit 0: the findings are kept and the caller appends a truncation note.
TRUNCATION_REASONS = frozenset({"max_tokens", "model_context_window_exceeded"})

#: Terminal reasons that mean the turn ended normally.
COMPLETION_REASONS = frozenset({"end_turn", "stop_sequence", "tool_use", "pause_turn"})

#: Content-block types whose deltas are reasoning, not report text. Skipped.
SKIP_BLOCK_TYPES = frozenset({"thinking", "redacted_thinking"})

#: Delta types that carry report text. Anything else (thinking_delta,
#: signature_delta, input_json_delta, or something added after this was
#: written) is skipped rather than concatenated into the findings.
TEXT_DELTA_TYPES = frozenset({"text_delta"})

#: Event types this parser understands. Anything else is ignored gracefully
#: (forward compatibility) and recorded in the metadata.
KNOWN_EVENT_TYPES = frozenset(
    {
        "message_start",
        "content_block_start",
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop",
        "ping",
        "error",
    }
)

#: Content-block types this parser understands. Unknown ones are ignored
#: gracefully and recorded — a new block type must never be fatal.
KNOWN_BLOCK_TYPES = frozenset(
    {"text", "thinking", "redacted_thinking", "tool_use", "server_tool_use"}
)

#: How much raw input to retain for the "this wasn't a stream at all"
#: diagnostic. Bounded so a huge body cannot be pulled into memory.
RAW_CAPTURE_LIMIT = 64 * 1024

#: Depth bound for the placement-agnostic `stop_details` search.
_MAX_SEARCH_DEPTH = 8


@dataclass
class Result:
    """The outcome of accumulating one stream.

    ``text`` is the report body. ``exit_code`` is the contract the shell leg
    branches on. Everything else is metadata for humans and for ``--json``.
    """

    text: str = ""
    status: str = "ok"
    exit_code: int = EXIT_OK
    message: str = ""
    stop_reason: str | None = None
    stop_reason_known: bool = False
    truncated: bool = False
    refusal_category: str | None = None
    refusal_category_present: bool = False
    saw_message_start: bool = False
    saw_message_stop: bool = False
    events_seen: int = 0
    malformed_data_lines: int = 0
    unknown_event_types: list[str] = field(default_factory=list)
    unknown_block_types: list[str] = field(default_factory=list)
    skipped_delta_types: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when the caller should keep the report (includes truncation)."""
        return self.exit_code == EXIT_OK

    def to_meta(self) -> dict[str, Any]:
        """Machine-readable terminal metadata, minus the (possibly huge) text."""
        return {
            "status": self.status,
            "exit_code": self.exit_code,
            "message": self.message,
            "stop_reason": self.stop_reason,
            "stop_reason_known": self.stop_reason_known,
            "truncated": self.truncated,
            "refusal_category": self.refusal_category,
            "refusal_category_present": self.refusal_category_present,
            "saw_message_start": self.saw_message_start,
            "saw_message_stop": self.saw_message_stop,
            "events_seen": self.events_seen,
            "malformed_data_lines": self.malformed_data_lines,
            "unknown_event_types": sorted(set(self.unknown_event_types)),
            "unknown_block_types": sorted(set(self.unknown_block_types)),
            "text_chars": len(self.text),
        }


@dataclass
class ParsedEvent:
    """One dispatched SSE event."""

    type: str
    data: dict[str, Any] | None
    malformed: bool = False


def parse_sse(lines: Iterable[str]) -> Iterator[ParsedEvent]:
    """Yield events from an SSE byte stream, one per blank-line-delimited block.

    Tolerant by construction — this is a *parser for someone else's output*,
    so every deviation is a recoverable condition rather than a traceback:

    * ``:`` comment lines and unrecognised lines are ignored.
    * Multiple ``data:`` lines in one event are joined with newlines (SSE spec).
    * A ``data:`` payload that is not valid JSON marks the event malformed and
      is skipped by the caller; it never raises.
    * The event name comes from the ``event:`` field, falling back to the
      ``type`` key inside the JSON payload (the API sets both).
    """
    event_name: str | None = None
    data_parts: list[str] = []
    saw_any_field = False

    def dispatch() -> ParsedEvent | None:
        if not saw_any_field:
            return None
        raw = "\n".join(data_parts)
        payload: dict[str, Any] | None = None
        malformed = False
        if raw:
            try:
                decoded = json.loads(raw)
            except json.JSONDecodeError:
                malformed = True
            else:
                if isinstance(decoded, dict):
                    payload = decoded
                else:
                    # Valid JSON but not an event object (e.g. a bare list).
                    malformed = True
        else:
            malformed = event_name is None
        name = event_name or (payload or {}).get("type") or ""
        return ParsedEvent(type=str(name), data=payload, malformed=malformed)

    for raw_line in lines:
        line = raw_line.rstrip("\n").rstrip("\r")
        if line == "":
            event = dispatch()
            if event is not None:
                yield event
            event_name = None
            data_parts = []
            saw_any_field = False
            continue
        if line.startswith(":"):
            continue
        field_name, sep, value = line.partition(":")
        if not sep:
            continue
        value = value[1:] if value.startswith(" ") else value
        if field_name == "event":
            event_name = value
            saw_any_field = True
        elif field_name == "data":
            data_parts.append(value)
            saw_any_field = True
        # Other SSE fields (id, retry) are valid but carry nothing we need.

    trailing = dispatch()
    if trailing is not None:
        yield trailing


def _find_mapping(obj: Any, key: str, depth: int = 0) -> Mapping[str, Any] | None:
    """Depth-bounded search for a mapping stored under ``key`` anywhere in ``obj``.

    This is how the tool stays honest about not knowing where the refusal
    category lives under streaming: rather than hard-coding ``delta.stop_details``
    and silently returning nothing if the API nests it elsewhere, it looks for
    the object wherever it is.
    """
    if depth > _MAX_SEARCH_DEPTH:
        return None
    if isinstance(obj, Mapping):
        found = obj.get(key)
        if isinstance(found, Mapping):
            return found
        for value in obj.values():
            nested = _find_mapping(value, key, depth + 1)
            if nested is not None:
                return nested
    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        for item in obj:
            nested = _find_mapping(item, key, depth + 1)
            if nested is not None:
                return nested
    return None


def find_refusal_category(*roots: Any) -> tuple[bool, str | None]:
    """Locate the refusal category, returning ``(details_found, category)``.

    ``category`` is documented as nullable, so ``(True, None)`` is a normal,
    permanent outcome and must never be read as "not a refusal". Callers that
    key a failure off a truthy category reintroduce exactly the defect this
    tool exists to catch.
    """
    for root in roots:
        details = _find_mapping(root, "stop_details")
        if details is None:
            details = _find_mapping(root, "refusal")
        if details is None:
            continue
        category = details.get("category")
        return True, category if isinstance(category, str) and category else None
    return False, None


def _terminal_stop_reason(event: Mapping[str, Any]) -> str | None:
    """Extract a resolved terminal reason from a ``message_delta`` payload.

    Checks ``delta.stop_reason`` (where the API puts it) and then the event
    top level and the embedded message, so a shape change relocating the field
    degrades to "still found" rather than "silently never fires". A ``null``
    value is not a terminal reason — intermediate deltas legitimately carry one.
    """
    for candidate in (event.get("delta"), event, event.get("message")):
        if isinstance(candidate, Mapping):
            reason = candidate.get("stop_reason")
            if isinstance(reason, str) and reason:
                return reason
    return None


def _error_message(payload: Mapping[str, Any] | None) -> str:
    """Best-effort human message out of an API error object."""
    if not isinstance(payload, Mapping):
        return "unknown stream error"
    error = payload.get("error")
    if isinstance(error, Mapping):
        message = error.get("message")
        if isinstance(message, str) and message:
            return message
        error_type = error.get("type")
        if isinstance(error_type, str) and error_type:
            return error_type
    message = payload.get("message")
    if isinstance(message, str) and message:
        return message
    return "unknown stream error"


def _tee(lines: Iterable[str], sink: list[str], limit: int) -> Iterator[str]:
    """Pass lines through while retaining a bounded prefix for diagnostics."""
    captured = 0
    for line in lines:
        if captured < limit:
            sink.append(line)
            captured += len(line)
        yield line


def _describe_non_stream(raw_prefix: str) -> str:
    """Explain an input that carried no SSE events at all."""
    stripped = raw_prefix.strip()
    if not stripped:
        return "empty stream: no data received on stdin"
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        preview = " ".join(stripped.split())[:200]
        return f"input is not an SSE stream and is not JSON; first bytes: {preview!r}"
    if isinstance(decoded, Mapping) and decoded.get("error"):
        return f"non-stream API error body: {_error_message(decoded)}"
    return "input parsed as JSON but contained no SSE events (not a stream)"


def accumulate(lines: Iterable[str], *, raw_capture_limit: int = RAW_CAPTURE_LIMIT) -> Result:
    """Fold an SSE line stream into report text plus a terminal verdict.

    Streams its input — safe on a multi-megabyte response — and never raises
    on malformed content. See the module docstring for the invariants.
    """
    result = Result()
    raw_prefix: list[str] = []

    # Text is keyed by block index so out-of-order deltas still land correctly;
    # blocks are concatenated in index order at the end.
    text_by_index: dict[int, list[str]] = {}
    block_types: dict[int, str] = {}
    error_payload: Mapping[str, Any] | None = None
    terminal_event: Mapping[str, Any] | None = None
    start_message: Any = None

    for event in parse_sse(_tee(lines, raw_prefix, raw_capture_limit)):
        if event.malformed:
            result.malformed_data_lines += 1
            continue
        result.events_seen += 1
        data = event.data or {}

        if event.type not in KNOWN_EVENT_TYPES:
            # Forward compatibility: a new event type is information, not a fault.
            result.unknown_event_types.append(event.type)
            continue

        if event.type == "message_start":
            result.saw_message_start = True
            start_message = data.get("message")

        elif event.type == "content_block_start":
            index = data.get("index")
            block = data.get("content_block")
            block = block if isinstance(block, Mapping) else {}
            block_type = block.get("type")
            block_type = block_type if isinstance(block_type, str) else "unknown"
            if block_type not in KNOWN_BLOCK_TYPES:
                result.unknown_block_types.append(block_type)
            if isinstance(index, int):
                block_types[index] = block_type
                seed = block.get("text")
                if block_type not in SKIP_BLOCK_TYPES and isinstance(seed, str) and seed:
                    text_by_index.setdefault(index, []).append(seed)

        elif event.type == "content_block_delta":
            index = data.get("index")
            delta = data.get("delta")
            delta = delta if isinstance(delta, Mapping) else {}
            delta_type = delta.get("type")
            delta_type = delta_type if isinstance(delta_type, str) else "unknown"
            block_type = block_types.get(index, "unknown") if isinstance(index, int) else "unknown"
            # Two independent gates. The delta type is the authority (a
            # thinking block emits `thinking_delta`), and the block type is a
            # belt-and-braces guard so reasoning can never reach the report.
            if delta_type not in TEXT_DELTA_TYPES or block_type in SKIP_BLOCK_TYPES:
                result.skipped_delta_types.append(delta_type)
                continue
            chunk = delta.get("text")
            if isinstance(chunk, str) and isinstance(index, int):
                text_by_index.setdefault(index, []).append(chunk)

        elif event.type == "message_delta":
            reason = _terminal_stop_reason(data)
            if reason is not None:
                result.stop_reason = reason
                terminal_event = data

        elif event.type == "message_stop":
            result.saw_message_stop = True

        elif event.type == "error":
            error_payload = data

        # `content_block_stop` and `ping` carry nothing this tool needs.

    result.text = "".join("".join(text_by_index[index]) for index in sorted(text_by_index))
    return _classify(result, error_payload, terminal_event, start_message, raw_prefix)


def _classify(
    result: Result,
    error_payload: Mapping[str, Any] | None,
    terminal_event: Mapping[str, Any] | None,
    start_message: Any,
    raw_prefix: list[str],
) -> Result:
    """Assign the status/exit code. Order of these branches is the contract."""
    # 1. Nothing that looked like a stream at all.
    if result.events_seen == 0:
        result.status = "no_stream"
        result.exit_code = EXIT_NO_STREAM
        result.message = _describe_non_stream("".join(raw_prefix))
        return result

    # 2. An explicit error event outranks everything else on the stream.
    if error_payload is not None:
        result.status = "stream_error"
        result.exit_code = EXIT_STREAM_ERROR
        where = "after a successful start" if result.saw_message_start else "before any start"
        result.message = f"stream error {where}: {_error_message(error_payload)}"
        return result

    # 3. Completeness sentinel — no terminal reason was ever resolved.
    if result.stop_reason is None:
        result.status = "incomplete"
        result.exit_code = EXIT_INCOMPLETE
        result.message = (
            "stream ended without a terminal event "
            f"(message_stop seen: {result.saw_message_stop}); output is incomplete"
        )
        return result

    result.stop_reason_known = result.stop_reason in (
        REFUSAL_REASONS | TRUNCATION_REASONS | COMPLETION_REASONS
    )

    # 4. Refusal. A missing or null category must NOT downgrade this.
    if result.stop_reason in REFUSAL_REASONS:
        present, category = find_refusal_category(terminal_event, start_message)
        result.refusal_category_present = present
        result.refusal_category = category
        shown = category if category else "unknown"
        result.status = "refusal"
        result.exit_code = EXIT_REFUSAL
        result.message = f"request declined by safety classifiers (category={shown})"
        return result

    # 5. A terminal reason we reached, but with nothing to show for it. An
    #    empty research report is never a success, whatever the reason says.
    if not result.text:
        result.status = "empty_output"
        result.exit_code = EXIT_EMPTY_OUTPUT
        result.message = f"stream completed (stop_reason={result.stop_reason}) but produced no text"
        return result

    # 6. Truncation at the ceiling: real content, deliberately exit 0, flagged
    #    distinctly so the caller can append its truncation note.
    if result.stop_reason in TRUNCATION_REASONS:
        result.truncated = True
        result.status = "truncated"
        result.exit_code = EXIT_OK
        result.message = (
            f"response truncated at the depth ceiling (stop_reason={result.stop_reason}); "
            "content is complete up to that point"
        )
        return result

    result.status = "ok"
    result.exit_code = EXIT_OK
    if result.stop_reason_known:
        result.message = f"complete (stop_reason={result.stop_reason})"
    else:
        # Unrecognised terminal reason with real text: keep it, but say so
        # loudly rather than pretending we understood the stream.
        result.message = (
            f"complete, but stop_reason={result.stop_reason!r} is not recognised "
            "by this tool; treating as success because text was produced"
        )
    return result
