# Research Provider Protocols

**Purpose:** Full per-provider API protocols (endpoint, auth, request body, polling loop, and parse/output instructions) for the three research legs dispatched by `/research-topic`. Kept out of SKILL.md to hold it to the progressive-disclosure line budget — the skill's Subagent Prompt Template and Provider Deltas table carry the parameterized dispatch logic; this file carries the exact, copy-pasteable mechanics for each provider.

**Consumers:** The Claude, OpenAI, and Gemini research-leg subagents dispatched from `research-topic/SKILL.md` Phase 4. Each dispatched subagent is instructed (via the Subagent Prompt Template) to Read this file for its provider's protocol before making its API call.

**Conventions used below:** `[BRACKETED]` tokens are placeholders the dispatching subagent substitutes with real values it was given (model name, prompt text, and `[TIMESTAMP]` — the same run timestamp already used in its `reports/research-[SLUG]-[TIMESTAMP].md` output path). Reusing `[TIMESTAMP]` in temp filenames keeps them unique per run without inventing a second value. All `curl` calls are bounded with `--max-time`/`--connect-timeout` so a hung connection cannot block indefinitely — the 180-iteration poll loops bound poll *count*, not any single call's duration. **The Claude leg is the exception to the "bounded call" reading:** its `--max-time` now bounds a long-lived streaming transfer, so it caps total generation time rather than a round trip, and because that call is piped its transport status must be read from `PIPESTATUS`, never from `$?`. Every submit (POST) response is checked for a valid ID and no `error` body before the poll loop is entered; a failed submit exits immediately instead of polling a nonexistent job.

---

## Anthropic Claude Protocol

Streaming — one long-lived call, no polling. There is still exactly one request, but the reply arrives as a `text/event-stream` and is consumed incrementally: `curl` is piped into the bundled `research-sse` accumulator, which folds the events back into report text and returns its verdict as an **exit status**. Adaptive-thinking requests at higher depths can legitimately run several minutes, so this leg gets a longer `--max-time` than the two polling legs' individual calls — and here that budget covers the whole generation, not a round trip.

**Thinking configuration — do not reintroduce `budget_tokens`.** `thinking: {"type": "enabled", "budget_tokens": N}` was **removed** from the API (not deprecated) and returns HTTP 400 on every current model, including `claude-opus-5` and `claude-opus-4-8`. Depth is controlled by `output_config.effort` instead. `effort` and `max_tokens` are both substituted from the depth ladder in `research-models.md`; `max_tokens` is a hard ceiling on thinking **plus** response text, so the two move together.

**Request** (use Bash — this block reads the `PIPESTATUS` array, so run it as one bash invocation, top to bottom; splitting it across calls loses the transport status):

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(find ~ -path '*/plugins/personal-plugin' -type d 2>/dev/null | head -1)}"
TOOL_SRC="$PLUGIN_DIR/tools/research-sse/src"
BODY=/tmp/claude-research-body-[TIMESTAMP].md
META=/tmp/claude-research-meta-[TIMESTAMP].txt
HDR=/tmp/claude-research-headers-[TIMESTAMP].txt
CURLERR=/tmp/claude-research-curl-[TIMESTAMP].txt

# Preflight. The exit codes this block branches on are a CONTRACT, and this
# file's copy of that contract is a label, not the thing itself. Confirm the
# tool still implements it before spending a multi-minute request on it.
PYTHONPATH="$TOOL_SRC" python3 -c 'import research_sse.accumulator as a
want = {"EXIT_OK": 0, "EXIT_REFUSAL": 4, "EXIT_INCOMPLETE": 5,
        "EXIT_STREAM_ERROR": 6, "EXIT_NO_STREAM": 7, "EXIT_EMPTY_OUTPUT": 8}
drift = {k: (v, getattr(a, k, None)) for k, v in want.items() if getattr(a, k, None) != v}
raise SystemExit("research-sse exit contract drifted (want, got): %r" % drift if drift else 0)' \
  || { echo "Anthropic request aborted: research-sse preflight failed"; exit 1; }

curl -sS --no-buffer --dump-header "$HDR" \
  --max-time 900 --connect-timeout 10 \
  https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "stream": true,
    "model": "[RESOLVED_CLAUDE_MODEL]",
    "max_tokens": [MAX_TOKENS],
    "thinking": {
      "type": "adaptive"
    },
    "output_config": {
      "effort": "[EFFORT]"
    },
    "messages": [{
      "role": "user",
      "content": "[ESCAPED RESEARCH PROMPT]"
    }]
  }' 2>"$CURLERR" \
  | PYTHONPATH="$TOOL_SRC" python3 -m research_sse >"$BODY" 2>"$META"
PIPE=("${PIPESTATUS[@]}")   # MUST be the very next statement. Any command in
CURL_EXIT=${PIPE[0]}        # between overwrites it, and a bare `$?` here would
ACC_EXIT=${PIPE[1]}         # report only the accumulator — a timeout, DNS
                            # failure or connection reset would go invisible.

# Diagnostics only. The header status arrives BEFORE any content, so 200 is not
# evidence of a complete response; ACC_EXIT is the verdict.
HTTP_CODE=$(awk 'toupper($1) ~ /^HTTP\// {c=$2} END {print c+0}' "$HDR" 2>/dev/null)
DIAG=$(grep -v '^research-sse-meta:' "$META" 2>/dev/null | tr '\n' ' ')

# 1. Transport. Detected across the pipe, which is the whole point of PIPESTATUS.
if [ "$CURL_EXIT" -ne 0 ]; then
  rm -f "$BODY"
  echo "Anthropic request failed: transport curl_exit=$CURL_EXIT header_http=$HTTP_CODE $(tr -d '\r\n' < "$CURLERR")"
  exit 1
fi

# 2. Stream verdict. Every non-zero code discards the body — a partial refusal
#    sentence or a half-written section is worse than no report at all.
if [ "$ACC_EXIT" -ne 0 ]; then
  case "$ACC_EXIT" in
    4) WHY="SAFETY REFUSAL — partial output discarded, never written" ;;
    5) WHY="stream died mid-flight, no terminal event (header_http=$HTTP_CODE proves nothing here)" ;;
    6) WHY="error event on the stream" ;;
    7) WHY="not a stream: empty body, or a plain JSON error object carrying the API message" ;;
    8) WHY="stream completed but produced zero text" ;;
    1|2) WHY="research-sse internal or usage error" ;;
    *) WHY="unrecognized research-sse exit status — treat as failure" ;;
  esac
  rm -f "$BODY"
  echo "Anthropic request failed: acc_exit=$ACC_EXIT ($WHY) header_http=$HTTP_CODE $DIAG"
  exit 1
fi

# 3. Success (exit 0 covers BOTH a normal completion and truncation at the
#    ceiling). The truncation marker is metadata, never an exit status.
TRUNCATED=$(sed -n 's/^research-sse-meta: //p' "$META" | python3 -c 'import json, sys
try:
    print("true" if json.load(sys.stdin).get("truncated") else "false")
except Exception:
    print("unknown")')
echo "Anthropic request ok: header_http=$HTTP_CODE truncated=$TRUNCATED body=$BODY"
```

**Exit-status contract.** Branch on `$ACC_EXIT` and nothing else. Do not re-derive the outcome from a field in the payload, and do not invent extra checks:

| `$ACC_EXIT` | Meaning | Action |
|---|---|---|
| 0 | Complete, non-refusal, non-empty — **covers both a normal completion and truncation at the ceiling** | Keep `$BODY`; read `$TRUNCATED` to decide on the note |
| 1 / 2 | `research-sse` internal or usage error | Fail the leg |
| 3 | Reserved, never emitted | — |
| 4 | Safety refusal; category (possibly `unknown`) on stderr | **Fail loudly and DISCARD `$BODY`** — it may hold a partial refusal sentence |
| 5 | Completeness sentinel — no terminal event ever resolved | Fail. The mid-flight-death case the header status cannot see |
| 6 | `error` event on the stream | Fail |
| 7 | Not a stream at all — empty body, or a plain JSON error object | Fail; `$DIAG` carries the API error text |
| 8 | Completed normally but produced zero text | Fail — an empty report is never a success |

**The refusal guard now lives in the exit status, not in a field lookup.** Under streaming the terminal reason arrives inside a `message_delta` event, so the old top-level field lookup would still compile, still read correctly, and never fire — silently writing an empty research report on every refusal. Exit 4 is the only refusal signal this leg reads.

**A 200 header is not success.** The status line arrives before any content, so a stream that opens cleanly and then dies mid-flight still reports 200. Exit 5 is the only thing that catches that, which is why `$HTTP_CODE` appears in diagnostics and never in a success test.

**Parse:** nothing to parse — `$BODY` already *is* the report text. `research-sse` concatenates the `text` content blocks in block-index order and skips reasoning blocks on two independent gates (delta type and block type), so thinking never reaches the report regardless of `thinking.display`. Read `$BODY` and write findings to `reports/research-claude-[TIMESTAMP].md` using the Write tool with this structure. Never attempt to salvage text from a failed run.

**Truncation** at the depth ceiling is **not** a failure and exits 0 — the content is real, just cut short. It is signalled by the `truncated` marker in the metadata line (surfaced above as `$TRUNCATED`), never by the exit status. When it is `true`, keep the findings and append a `> **Note:** response truncated at the depth ceiling; consider a deeper `--depth`.` line to the report so synthesis does not read a truncated section as a complete one. If `$TRUNCATED` came back `unknown` the metadata line was unreadable — append the note anyway; over-warning synthesis is far cheaper than presenting a cut-off section as complete.

**Forward compatibility:** an unrecognized event type, content-block type, or delta type is **ignored, never fatal**. It is recorded in the metadata line (`unknown_event_types`, `unknown_block_types`) and the run still succeeds, so a block type added after this file was written degrades to "absent from the report", not "leg crashed". When a report looks unexpectedly thin, read the `research-sse-meta:` line in `$META` and enumerate the keys the tool actually emitted — do not parse for the subset restated here.

```markdown
# Claude Research: [topic]
**Provider:** Anthropic Claude
**Model:** [model]
**Depth:** [depth]
**Generated:** [timestamp]

## Research Findings

[Full text content from API response — all text blocks concatenated]
```

**Status line:** `{"provider":"claude","status":"success","file":"reports/research-claude-[TIMESTAMP].md"}` or `{"provider":"claude","status":"failed","error":"[message]"}`

---

## OpenAI Protocol

Async — submit a background job, then poll.

**Submit** (use Bash):

```bash
RAW=$(curl -s -w '\n%{http_code}' --max-time 60 --connect-timeout 10 \
  https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "[RESOLVED_OAI_MODEL]",
    "input": "[ESCAPED RESEARCH PROMPT]",
    "reasoning": {"effort": "[EFFORT_LEVEL]"},
    "tools": [{"type": "web_search_preview"}],
    "background": true
  }')
CURL_EXIT=$?
HTTP_CODE=$(echo "$RAW" | tail -n1)
RESPONSE=$(echo "$RAW" | sed '$d')
RESPONSE_ID=$(echo "$RESPONSE" | python3 -c "import sys,json
try:
    print(json.load(sys.stdin).get('id',''))
except Exception:
    print('')")

# Fast-fail: do not enter the 30-minute poll loop for a submit that never
# produced a job (curl failure, HTTP error, or empty id).
if [ "$CURL_EXIT" -ne 0 ] || [ "$HTTP_CODE" -ge 400 ] || [ -z "$RESPONSE_ID" ]; then
  ERROR_MSG=$(echo "$RESPONSE" | python3 -c "import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get('error', {}).get('message', 'unknown error') if isinstance(d, dict) else 'unknown error')
except Exception:
    print('unparseable response body')")
  echo "OpenAI submit failed: curl_exit=$CURL_EXIT http=$HTTP_CODE error=\"$ERROR_MSG\""
  exit 1
fi
echo "Submitted OpenAI request: $RESPONSE_ID"
```

**Poll until complete** (max 30 minutes; use Bash):

```bash
HEADERS_FILE=/tmp/openai-poll-headers-[TIMESTAMP].txt
BACKOFF=10
for i in $(seq 1 180); do
  sleep "$BACKOFF"
  BACKOFF=10

  RAW=$(curl -s -D "$HEADERS_FILE" -w '\n%{http_code}' \
    --max-time 30 --connect-timeout 10 --retry 2 \
    "https://api.openai.com/v1/responses/$RESPONSE_ID" \
    -H "Authorization: Bearer $OPENAI_API_KEY")
  CURL_EXIT=$?
  HTTP_CODE=$(echo "$RAW" | tail -n1)
  STATUS=$(echo "$RAW" | sed '$d')

  if [ "$CURL_EXIT" -ne 0 ]; then
    echo "OpenAI poll $i: curl error (exit $CURL_EXIT), will retry"
    continue
  fi

  if [ "$HTTP_CODE" = "429" ]; then
    RETRY_AFTER=$(grep -i '^retry-after:' "$HEADERS_FILE" | tr -d '\r' | cut -d' ' -f2)
    BACKOFF=${RETRY_AFTER:-30}
    echo "OpenAI poll $i: rate limited (429), honoring Retry-After, backing off ${BACKOFF}s"
    continue
  fi

  if [ "$HTTP_CODE" -ge 400 ]; then
    echo "OpenAI poll $i failed: HTTP $HTTP_CODE"
    exit 1
  fi

  STATE=$(echo "$STATUS" | python3 -c "import sys,json
try:
    print(json.load(sys.stdin).get('status',''))
except Exception:
    print('')")
  if [ -z "$STATE" ]; then
    echo "OpenAI poll $i: missing status field in response — treating as error, not a reason to keep polling"
    exit 1
  fi
  echo "OpenAI poll $i: $STATE"

  if [ "$STATE" = "completed" ]; then
    echo "$STATUS" > /tmp/openai-research-response-[TIMESTAMP].json
    break
  fi
  if [ "$STATE" = "failed" ] || [ "$STATE" = "cancelled" ]; then
    echo "OpenAI request failed: $STATE"
    exit 1
  fi
done
```

**Parse:** Extract the `text` output from `/tmp/openai-research-response-[TIMESTAMP].json`. Write findings to `reports/research-openai-[TIMESTAMP].md` using the Write tool with this structure:

```markdown
# OpenAI Research: [topic]
**Provider:** OpenAI
**Model:** [model]
**Depth:** [depth]
**Generated:** [timestamp]

## Research Findings

[Full text output from completed response]
```

**Status line:** `{"provider":"openai","status":"success","file":"reports/research-openai-[TIMESTAMP].md"}` or `{"provider":"openai","status":"failed","error":"[message]"}`

---

## Google Gemini Protocol

Async — submit an interaction, then poll. The API key goes in the `x-goog-api-key` header, not the URL query string — a query-string key leaks into `ps`, shell history, and proxy access logs.

**Submit** (use Bash):

```bash
RAW=$(curl -s -w '\n%{http_code}' --max-time 60 --connect-timeout 10 \
  "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "x-goog-api-key: $GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "[RESOLVED_GEMINI_AGENT_ID]",
    "message": {"text": "[ESCAPED RESEARCH PROMPT]"},
    "parameters": {"thinking_level": "[THINKING_LEVEL]"}
  }')
CURL_EXIT=$?
HTTP_CODE=$(echo "$RAW" | tail -n1)
RESPONSE=$(echo "$RAW" | sed '$d')
INTERACTION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json
try:
    print(json.load(sys.stdin).get('name','').split('/')[-1])
except Exception:
    print('')")

# Fast-fail: do not enter the 30-minute poll loop for a submit that never
# produced an interaction (curl failure, HTTP error, or empty id).
if [ "$CURL_EXIT" -ne 0 ] || [ "$HTTP_CODE" -ge 400 ] || [ -z "$INTERACTION_ID" ]; then
  ERROR_MSG=$(echo "$RESPONSE" | python3 -c "import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get('error', {}).get('message', 'unknown error') if isinstance(d, dict) else 'unknown error')
except Exception:
    print('unparseable response body')")
  echo "Gemini submit failed: curl_exit=$CURL_EXIT http=$HTTP_CODE error=\"$ERROR_MSG\""
  exit 1
fi
echo "Submitted Gemini interaction: $INTERACTION_ID"
```

**Poll until complete** (max 30 minutes; use Bash):

```bash
HEADERS_FILE=/tmp/gemini-poll-headers-[TIMESTAMP].txt
BACKOFF=10
for i in $(seq 1 180); do
  sleep "$BACKOFF"
  BACKOFF=10

  RAW=$(curl -s -D "$HEADERS_FILE" -w '\n%{http_code}' \
    --max-time 30 --connect-timeout 10 --retry 2 \
    "https://generativelanguage.googleapis.com/v1beta/interactions/$INTERACTION_ID" \
    -H "x-goog-api-key: $GOOGLE_API_KEY")
  CURL_EXIT=$?
  HTTP_CODE=$(echo "$RAW" | tail -n1)
  STATUS=$(echo "$RAW" | sed '$d')

  if [ "$CURL_EXIT" -ne 0 ]; then
    echo "Gemini poll $i: curl error (exit $CURL_EXIT), will retry"
    continue
  fi

  if [ "$HTTP_CODE" = "429" ]; then
    RETRY_AFTER=$(grep -i '^retry-after:' "$HEADERS_FILE" | tr -d '\r' | cut -d' ' -f2)
    BACKOFF=${RETRY_AFTER:-30}
    echo "Gemini poll $i: rate limited (429), honoring Retry-After, backing off ${BACKOFF}s"
    continue
  fi

  if [ "$HTTP_CODE" -ge 400 ]; then
    echo "Gemini poll $i failed: HTTP $HTTP_CODE"
    exit 1
  fi

  STATE=$(echo "$STATUS" | python3 -c "import sys,json
try:
    print(json.load(sys.stdin).get('state',''))
except Exception:
    print('')")
  if [ -z "$STATE" ]; then
    echo "Gemini poll $i: missing state field in response — treating as error, not a reason to keep polling"
    exit 1
  fi
  echo "Gemini poll $i: $STATE"

  if [ "$STATE" = "SUCCEEDED" ]; then
    echo "$STATUS" > /tmp/gemini-research-response-[TIMESTAMP].json
    break
  fi
  if [ "$STATE" = "FAILED" ] || [ "$STATE" = "CANCELLED" ]; then
    echo "Gemini request failed: $STATE"
    exit 1
  fi
done
```

**Parse:** Extract the reply text from `/tmp/gemini-research-response-[TIMESTAMP].json`. Write findings to `reports/research-gemini-[TIMESTAMP].md` using the Write tool with this structure:

```markdown
# Gemini Research: [topic]
**Provider:** Google Gemini
**Agent:** [agent]
**Depth:** [depth]
**Generated:** [timestamp]

## Research Findings

[Full reply text from completed interaction]
```

**Status line:** `{"provider":"gemini","status":"success","file":"reports/research-gemini-[TIMESTAMP].md"}` or `{"provider":"gemini","status":"failed","error":"[message]"}`
