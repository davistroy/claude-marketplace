---
name: brain-entry
description: Send a capture to Open Brain. Takes any instruction as an argument — summarize a session, log a decision, capture an idea — processes it, and POSTs to the captures API. Use when the user says "/brain-entry <instruction>".
---

# Brain Entry

Create a capture in Open Brain from any instruction. The argument tells you what content to generate and send.

## Proactive Triggers

Suggest this skill when:
1. User says "log this", "capture this", "remember this", "brain entry", or "send to open brain"
2. At the end of a significant work session when a summary would be valuable
3. User makes a decision and says "record this decision"
4. User explicitly invokes `/brain-entry <instruction>`

## Examples

```
/brain-entry summarize everything we have done so far in this session and send it to my open-brain
/brain-entry log a decision: we chose Cloudflare Email Routing for email ingestion because it adds zero infrastructure
/brain-entry capture this idea: add a weekly email digest that summarizes all captures from the past 7 days
/brain-entry record that I had a productive call with Butch about the CFA merger timeline
```

## Implementation

### Step 1: Generate the content

Based on the user's instruction in the arguments:

- If the instruction says "summarize this session" or similar — review the full conversation context and produce a clear, structured summary of what was accomplished, decisions made, and outcomes.
- If the instruction describes a decision, idea, observation, task, or other capture — write it up clearly and concisely.
- If the instruction references specific context from the conversation — include the relevant details.

Write the content in first person (Troy's voice) since this is his personal knowledge base. Be substantive and specific — include names, dates, technical details, and outcomes. No filler.

### Step 2: Classify the capture

Determine the best `capture_type` from: `decision`, `idea`, `observation`, `task`, `win`, `blocker`, `question`, `reflection`.

Determine the best `brain_view` from: `career`, `personal`, `technical`, `work-internal`, `client`.

Use your judgment based on the content. When in doubt, use `observation` and `personal`.

### Step 3: POST to the captures API

Use the Bash tool to POST to the captures API:

```bash
curl -s -X POST "https://brain.troy-davis.com/api/v1/captures" \
  -H "Content-Type: application/json" \
  -H "X-Open-Brain-Caller: claude-code" \
  -d '{
    "content": "<generated content>",
    "capture_type": "<classified type>",
    "brain_view": "<classified view>",
    "source": "api",
    "metadata": {
      "source_metadata": {
        "origin": "claude-code-skill",
        "session_context": "<brief description of what prompted this>"
      }
    }
  }'
```

**Important:**
- Escape all special characters in the content for JSON (newlines as `\n`, quotes as `\"`)
- Content max length: 50,000 characters
- The API returns `{ id, pipeline_status, created_at }` on success (201)
- Use a heredoc or Python for complex content to avoid shell escaping issues

**Preferred approach for complex content (avoids shell escaping):**
```bash
python3 -c "
import json, urllib.request
payload = json.dumps({
    'content': '''<content here>''',
    'capture_type': '<type>',
    'brain_view': '<view>',
    'source': 'api',
    'metadata': {
        'source_metadata': {
            'origin': 'claude-code-skill',
            'session_context': '<context>'
        }
    }
})
req = urllib.request.Request(
    'https://brain.troy-davis.com/api/v1/captures',
    data=payload.encode(),
    headers={'Content-Type': 'application/json', 'X-Open-Brain-Caller': 'claude-code'},
    method='POST'
)
resp = urllib.request.urlopen(req)
print(resp.read().decode())
"
```

### Step 4: Confirm to the user

On success, display:
```
Captured in Open Brain:
  ID: <capture_id>
  Type: <capture_type>
  View: <brain_view>
  Pipeline: <status>
```

On failure, show the error and suggest the user check that the homeserver is running.

## Error Handling

- If the API returns 4xx/5xx, show the error body
- If the API is unreachable, suggest checking Cloudflare Tunnel / homeserver status
- If the content exceeds 50K chars, truncate with a `[truncated]` marker
- Never silently fail — always report the outcome

## Notes

- The pipeline will automatically classify, embed, and extract entities from the capture
- The capture will be searchable immediately via FTS and after embedding via semantic search
- This skill is the Claude Code equivalent of voice memos (phone) or Slack messages — another input channel into the brain
