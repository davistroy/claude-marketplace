# Research Provider Protocols

**Purpose:** Full per-provider API protocols (endpoint, auth, request body, polling loop, and parse/output instructions) for the three research legs dispatched by `/research-topic`. Kept out of SKILL.md to hold it to the progressive-disclosure line budget — the skill's Subagent Prompt Template and Provider Deltas table carry the parameterized dispatch logic; this file carries the exact, copy-pasteable mechanics for each provider.

**Consumers:** The Claude, OpenAI, and Gemini research-leg subagents dispatched from `research-topic/SKILL.md` Phase 4. Each dispatched subagent is instructed (via the Subagent Prompt Template) to Read this file for its provider's protocol before making its API call.

---

## Anthropic Claude Protocol

Synchronous — a single call, no polling.

**Request** (use Bash):

```bash
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "[RESOLVED_CLAUDE_MODEL]",
    "max_tokens": 16000,
    "thinking": {
      "type": "enabled",
      "budget_tokens": [BUDGET_TOKENS]
    },
    "messages": [{
      "role": "user",
      "content": "[ESCAPED RESEARCH PROMPT]"
    }]
  }' > /tmp/claude-research-response.json
```

**Parse:** Extract the `text` content blocks (skip `thinking` blocks). Write findings to `reports/research-claude-[TIMESTAMP].md` using the Write tool with this structure:

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

**Submit + Poll** (use Bash):

```bash
# Submit the request
RESPONSE=$(curl -s https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "[RESOLVED_OAI_MODEL]",
    "input": "[ESCAPED RESEARCH PROMPT]",
    "reasoning": {"effort": "[EFFORT_LEVEL]"},
    "tools": [{"type": "web_search_preview"}],
    "background": true
  }')
RESPONSE_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Submitted OpenAI request: $RESPONSE_ID"

# Poll until complete (max 30 minutes)
for i in $(seq 1 180); do
  sleep 10
  STATUS=$(curl -s "https://api.openai.com/v1/responses/$RESPONSE_ID" \
    -H "Authorization: Bearer $OPENAI_API_KEY")
  STATE=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
  echo "OpenAI poll $i: $STATE"
  if [ "$STATE" = "completed" ]; then
    echo "$STATUS" > /tmp/openai-research-response.json
    break
  fi
  if [ "$STATE" = "failed" ] || [ "$STATE" = "cancelled" ]; then
    echo "OpenAI request failed: $STATE"
    exit 1
  fi
done
```

**Parse:** Extract the `text` output from the completed response. Write findings to `reports/research-openai-[TIMESTAMP].md` using the Write tool with this structure:

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

Async — submit an interaction, then poll.

**Submit + Poll** (use Bash):

```bash
# Submit the deep research interaction
RESPONSE=$(curl -s "https://generativelanguage.googleapis.com/v1beta/interactions?key=$GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "[RESOLVED_GEMINI_AGENT_ID]",
    "message": {"text": "[ESCAPED RESEARCH PROMPT]"},
    "parameters": {"thinking_level": "[THINKING_LEVEL]"}
  }')
INTERACTION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','').split('/')[-1])")
echo "Submitted Gemini interaction: $INTERACTION_ID"

# Poll until complete (max 30 minutes)
for i in $(seq 1 180); do
  sleep 10
  STATUS=$(curl -s "https://generativelanguage.googleapis.com/v1beta/interactions/$INTERACTION_ID?key=$GOOGLE_API_KEY")
  STATE=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))")
  echo "Gemini poll $i: $STATE"
  if [ "$STATE" = "SUCCEEDED" ]; then
    echo "$STATUS" > /tmp/gemini-research-response.json
    break
  fi
  if [ "$STATE" = "FAILED" ] || [ "$STATE" = "CANCELLED" ]; then
    echo "Gemini request failed: $STATE"
    exit 1
  fi
done
```

**Parse:** Extract the reply text from the completed interaction. Write findings to `reports/research-gemini-[TIMESTAMP].md` using the Write tool with this structure:

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
