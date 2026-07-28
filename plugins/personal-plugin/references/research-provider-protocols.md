# Research Provider Protocols

**Purpose:** Full per-provider API protocols (endpoint, auth, request body, polling loop, and parse/output instructions) for the three research legs dispatched by `/research-topic`. Kept out of SKILL.md to hold it to the progressive-disclosure line budget — the skill's Subagent Prompt Template and Provider Deltas table carry the parameterized dispatch logic; this file carries the exact, copy-pasteable mechanics for each provider.

**Consumers:** The Claude, OpenAI, and Gemini research-leg subagents dispatched from `research-topic/SKILL.md` Phase 4. Each dispatched subagent is instructed (via the Subagent Prompt Template) to Read this file for its provider's protocol before making its API call.

**Conventions used below:** `[BRACKETED]` tokens are placeholders the dispatching subagent substitutes with real values it was given (model name, prompt text, and `[TIMESTAMP]` — the same run timestamp already used in its `reports/research-[SLUG]-[TIMESTAMP].md` output path). Reusing `[TIMESTAMP]` in temp filenames keeps them unique per run without inventing a second value. All `curl` calls are bounded with `--max-time`/`--connect-timeout` so a hung connection cannot block indefinitely — the 180-iteration poll loops bound poll *count*, not any single call's duration. Every submit (POST) response is checked for a valid ID and no `error` body before the poll loop is entered; a failed submit exits immediately instead of polling a nonexistent job.

---

## Anthropic Claude Protocol

Synchronous — a single call, no polling. Adaptive-thinking requests at higher depths can legitimately run several minutes, so this leg gets a longer `--max-time` than the other providers' individual calls.

**Thinking configuration — do not reintroduce `budget_tokens`.** `thinking: {"type": "enabled", "budget_tokens": N}` was **removed** from the API (not deprecated) and returns HTTP 400 on every current model, including `claude-opus-5` and `claude-opus-4-8`. Depth is controlled by `output_config.effort` instead. `effort` and `max_tokens` are both substituted from the depth ladder in `research-models.md`; `max_tokens` is a hard ceiling on thinking **plus** response text, so the two move together.

**Request** (use Bash):

```bash
HTTP_CODE=$(curl -s -o /tmp/claude-research-response-[TIMESTAMP].json -w '%{http_code}' \
  --max-time 900 --connect-timeout 10 \
  https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
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
  }')
CURL_EXIT=$?

# Fast-fail before parsing. Four distinct failure modes, only three of which are
# visible in the HTTP status:
#   1. curl-level failure (timeout, DNS, connection reset)
#   2. an HTTP error status
#   3. an `error` body
#   4. a SAFETY REFUSAL — HTTP 200, no `error` key, `stop_reason: "refusal"`, and
#      content that is empty (declined before output) or partial (declined mid-stream).
#      Without this check the leg writes a silently empty research report.
CHECK=$(python3 -c "import json
try:
    d = json.load(open('/tmp/claude-research-response-[TIMESTAMP].json'))
    if not isinstance(d, dict):
        print('unparseable response body')
    elif d.get('error'):
        print(d['error'].get('message', 'unknown API error'))
    elif d.get('stop_reason') == 'refusal':
        det = d.get('stop_details') or {}
        print('request declined by safety classifiers (category=%s)' % det.get('category'))
    else:
        print('')
except Exception:
    print('unparseable response body')")

if [ "$CURL_EXIT" -ne 0 ] || [ "$HTTP_CODE" -ge 400 ] || [ -n "$CHECK" ]; then
  echo "Anthropic request failed: curl_exit=$CURL_EXIT http=$HTTP_CODE${CHECK:+ error=\"$CHECK\"}"
  exit 1
fi
```

**Parse:** Extract the `text` content blocks (skip `thinking` blocks) from `/tmp/claude-research-response-[TIMESTAMP].json`. Thinking blocks arrive with empty text by default on current models (`thinking.display` defaults to `"omitted"`), which is fine — this leg discards them either way. Write findings to `reports/research-claude-[TIMESTAMP].md` using the Write tool with this structure.

A `stop_reason` of `"max_tokens"` is **not** a failure — the content is real, just cut short at the depth ceiling. Keep the findings, but append a `> **Note:** response truncated at the depth ceiling (`stop_reason: max_tokens`); consider a deeper `--depth`.` line to the report so synthesis does not read a truncated section as a complete one.

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
