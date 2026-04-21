---
name: research-topic
description: Orchestrate parallel deep research across multiple LLM providers using native context:fork subagents and synthesize results
effort: high
allowed-tools: Read, Write, Bash, WebSearch, WebFetch, Task
---

# Multi-Source Deep Research

You are orchestrating parallel deep research across three LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini) using native `context: fork` subagents and synthesizing the results into a unified deliverable.

**Architecture:** Three subagents dispatch in parallel — one per provider. Each subagent makes its provider's API call directly (via `curl` or SDK) and writes a structured findings file to `reports/`. Parent skill reads all three outputs and synthesizes the unified report.

**Trade-offs vs Previous Implementation:** This architecture eliminates the Python research-orchestrator tool and all its dependencies (no pip installs, no virtual env, no PYTHONPATH setup). Trade-off: no real-time streaming progress bars during API polling. For long runs (30+ min), watch the in-progress agent indicators in the Claude Code UI. Architecture gains: simpler debugging, cross-platform portability, single-runtime execution.

## Proactive Triggers

Suggest this skill when:
1. User asks to research a topic in depth or wants a comprehensive analysis
2. User wants to compare perspectives across multiple AI providers
3. User needs a well-sourced analysis that benefits from multi-source synthesis
4. User mentions "deep research", "research report", or "multi-provider analysis"
5. User asks for a thorough investigation of a technical, strategic, or emerging topic

## Input Validation

**Required Arguments:**
- Research request (provided by user as $ARGUMENTS or in conversation)

**Optional Arguments:**
- `--sources <list>` - Comma-separated list of sources to use: `claude`, `openai`, `gemini` (default: all three)
- `--depth <level>` - Research depth: `brief`, `standard`, `comprehensive` (default: standard)
- `--format <type>` - Output format: `md`, `docx`, `both` (default: both)
- `--no-clarify` - Skip clarification loop, use request as-is
- `--no-audience` - Skip audience profile detection, use default profile

**Environment Requirements:**
API keys must be loaded into the environment before use. Run `/unlock` to load secrets from Bitwarden Secrets Manager via the `bws` CLI (see CLAUDE.md Secrets Management Policy):
- `ANTHROPIC_API_KEY` - For Claude with Extended Thinking
- `OPENAI_API_KEY` - For OpenAI Deep Research
- `GOOGLE_API_KEY` - For Gemini Deep Research

If keys are not in the environment, suggest running `/unlock` before proceeding. Do NOT write API keys to `.env` files.

**Optional Model Configuration (non-sensitive, safe for .env):**
- `ANTHROPIC_MODEL` - Override Claude model. Default: `claude-opus-4-6-20250725`
- `OPENAI_MODEL` - Override OpenAI model. Default: `o3-deep-research-2025-06-26`
- `GEMINI_AGENT` - Override Gemini agent. Default: `deep-research-pro-preview-12-2025`

For provider configurations, depth parameter mappings, and cost estimates, read `references/research-models.md` (relative to this plugin's directory).

## Workflow

### Phase 1: Intake

Accept the research request from the user. If no request is provided in arguments, prompt:
```text
What would you like to research?

Please describe your research question or topic. Include any relevant context
about scope, audience, or specific aspects you want explored.
```

### Phase 1.5: Audience Profile Detection

**Purpose:** Tailor research output to the user's profile.

**Step 1: Search for Existing Profile**

Search for an audience/user profile in CLAUDE.md files in this priority order:
1. **Project:** `./CLAUDE.md` or `./.claude/CLAUDE.md`
2. **Local:** `./.claude.local/CLAUDE.md`
3. **Global:** `~/.claude/CLAUDE.md` (Windows: `%USERPROFILE%\.claude\CLAUDE.md`)

Look for sections matching: `# Audience Profile`, `# User Profile`, `# Target Audience`, `# Reader Profile`, or name-prefixed variants.

**Step 2A: If Profile Found** — Display a summary (Role, Background, Preferences) with source path. Ask user to confirm or modify.

**Step 2B: If No Profile Found** — Prompt user to describe their target audience. Offer to save the profile to `~/.claude/CLAUDE.md` for future sessions.

**Step 3: Store for Session** — Store the confirmed profile for use in Phase 4 prompt construction.

**Skip Conditions:** Skip with `--no-audience` flag or if user says "skip"/"none" (use default profile).

### Phase 2: Clarification Loop (max 4 rounds)

**REQUIRED:** Unless `--no-clarify` is specified, run the clarification loop before proceeding.

Ask clarifying questions across these dimensions:

| Dimension | Question Type |
|-----------|---------------|
| **Scope** | Breadth vs depth, specific subtopics to include/exclude |
| **Audience** | Technical level, domain expertise assumed |
| **Depth** | Summary vs comprehensive analysis |
| **Deliverable** | Report structure, key sections needed |
| **Recency** | How current must information be? |

- Ask 1-4 questions per round
- Stop when request is sufficiently defined OR 4 rounds complete
- Provide sensible defaults for skipped questions

### Phase 3: Pre-Execution Gate

**Step 1: Check API Key Availability**

Check which provider API keys are present in the environment:

```bash
# Check which keys are available
echo "ANTHROPIC_API_KEY: $([ -n "$ANTHROPIC_API_KEY" ] && echo 'PRESENT' || echo 'MISSING')"
echo "OPENAI_API_KEY: $([ -n "$OPENAI_API_KEY" ] && echo 'PRESENT' || echo 'MISSING')"
echo "GOOGLE_API_KEY: $([ -n "$GOOGLE_API_KEY" ] && echo 'PRESENT' || echo 'MISSING')"
```

**If any requested provider keys are missing:**
```
Pre-Execution Check: PARTIAL/FAILED

Missing API keys:
  - ANTHROPIC_API_KEY (required for claude source)
  - OPENAI_API_KEY (required for openai source)
  - GOOGLE_API_KEY (required for gemini source)

To load API keys from Bitwarden, run: /unlock
```

**If all keys present for selected sources:**
```
Pre-Execution Check: PASSED
API keys configured for: [list of available providers]
```

**Handling missing keys gracefully:** If a provider key is missing, skip that provider's subagent dispatch. Proceed with the available providers and note the skip in the output. Do not abort unless ALL selected providers are missing keys.

**Step 2: Present the research brief:**

```yaml
Research Brief
==============
Topic: [refined topic statement]
Scope: [defined boundaries]
Depth: [brief/standard/comprehensive]
Sources: [providers that will be used — skip any with missing keys]
Skipped: [providers skipped due to missing API keys, if any]
Deliverable: [expected output structure]

Target Audience:
  Role: [from Phase 1.5 profile]
  Background: [key expertise areas]
  Preferences: [communication style]

Proceed with this research brief? (yes/revise)
```

Wait for user confirmation.

### Phase 4: Parallel Provider Research via context:fork Subagents

**Resolve model names before dispatch:**

```bash
# Resolve model identifiers (env var override or defaults)
CLAUDE_MODEL="${ANTHROPIC_MODEL:-claude-opus-4-6-20250725}"
OAI_MODEL="${OPENAI_MODEL:-o3-deep-research-2025-06-26}"
GEMINI_AGENT_ID="${GEMINI_AGENT:-deep-research-pro-preview-12-2025}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
echo "CLAUDE_MODEL=$CLAUDE_MODEL"
echo "OAI_MODEL=$OAI_MODEL"
echo "GEMINI_AGENT_ID=$GEMINI_AGENT_ID"
echo "TIMESTAMP=$TIMESTAMP"
```

**Craft the Research Prompt:**

Transform the refined brief into a provider-agnostic prompt including the audience profile from Phase 1.5. If Phase 1.5 was skipped, use the default profile: Senior Director/VP-level technology executive; enterprise software architecture, AI/ML systems, cloud infrastructure; prefers actionable insights and data-driven recommendations; comfortable with technical details but values strategic framing.

```text
Research Request: [topic]

Context:
- Scope: [boundaries]
- Depth: [level]

Target Audience Profile:
[INSERT AUDIENCE PROFILE FROM PHASE 1.5 HERE]

Please provide a comprehensive analysis covering:
1. [Key aspect 1 — derived from clarification]
2. [Key aspect 2]
3. [Key aspect 3]

Structure your response with:
- Executive summary (2-3 key takeaways)
- Detailed analysis with supporting evidence
- Practical implementation considerations
- Strategic recommendations
- Sources and citations where available
```

**Depth-to-parameter mapping** (from `references/research-models.md`):

| Depth | Claude budget_tokens | OpenAI effort | Gemini thinking_level |
|-------|---------------------|---------------|-----------------------|
| brief | 4,000 | medium | low |
| standard | 10,000 | high | high |
| comprehensive | 32,000 | high | high |

**Dispatch subagents in parallel** (one Task per available provider — skip providers with missing keys):

#### Claude Subagent

```
context: fork
agent: claude-opus-4-6-20250725  (or value of $ANTHROPIC_MODEL)

You are a research agent responsible for the Anthropic Claude research leg of a multi-provider research task.

Your job:
1. Call the Anthropic Messages API with extended thinking enabled
2. Write your findings to reports/research-claude-[TIMESTAMP].md
3. Return a JSON status object on your final line

Provider: Anthropic Claude
Model: [RESOLVED_CLAUDE_MODEL]
API Key env var: ANTHROPIC_API_KEY

Research prompt to submit:
[FULL RESEARCH PROMPT FROM PHASE 4]

Extended thinking budget_tokens: [4000|10000|32000 based on depth]

API call (use Bash):
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

Parse the response: extract the `text` content blocks (skip `thinking` blocks). Write findings to `reports/research-claude-[TIMESTAMP].md` using the Write tool with this structure:

```markdown
# Claude Research: [topic]
**Provider:** Anthropic Claude
**Model:** [model]
**Depth:** [depth]
**Generated:** [timestamp]

## Research Findings

[Full text content from API response — all text blocks concatenated]
```

On final line output exactly: `{"provider":"claude","status":"success","file":"reports/research-claude-[TIMESTAMP].md"}` or `{"provider":"claude","status":"failed","error":"[message]"}`
```

#### OpenAI Subagent

```
context: fork

You are a research agent responsible for the OpenAI research leg of a multi-provider research task.

Your job:
1. Submit a deep research request to the OpenAI Responses API
2. Poll until completion (background job)
3. Write your findings to reports/research-openai-[TIMESTAMP].md
4. Return a JSON status object on your final line

Provider: OpenAI
Model: [RESOLVED_OAI_MODEL]
API Key env var: OPENAI_API_KEY

Research prompt to submit:
[FULL RESEARCH PROMPT FROM PHASE 4]

OpenAI reasoning_effort: [medium|high based on depth]

API call — submit and poll (use Bash):
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

Parse the response: extract text output from the completed response. Write findings to `reports/research-openai-[TIMESTAMP].md` using the Write tool with this structure:

```markdown
# OpenAI Research: [topic]
**Provider:** OpenAI
**Model:** [model]
**Depth:** [depth]
**Generated:** [timestamp]

## Research Findings

[Full text output from completed response]
```

On final line output exactly: `{"provider":"openai","status":"success","file":"reports/research-openai-[TIMESTAMP].md"}` or `{"provider":"openai","status":"failed","error":"[message]"}`
```

#### Gemini Subagent

```
context: fork

You are a research agent responsible for the Google Gemini research leg of a multi-provider research task.

Your job:
1. Submit a deep research interaction to the Google Gemini Interactions API
2. Poll until completion
3. Write your findings to reports/research-gemini-[TIMESTAMP].md
4. Return a JSON status object on your final line

Provider: Google Gemini
Agent: [RESOLVED_GEMINI_AGENT_ID]
API Key env var: GOOGLE_API_KEY

Research prompt to submit:
[FULL RESEARCH PROMPT FROM PHASE 4]

Gemini thinking_level: [low|high based on depth]

API call — submit and poll (use Bash):
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

Parse the response: extract the reply text from the completed interaction. Write findings to `reports/research-gemini-[TIMESTAMP].md` using the Write tool with this structure:

```markdown
# Gemini Research: [topic]
**Provider:** Google Gemini
**Agent:** [agent]
**Depth:** [depth]
**Generated:** [timestamp]

## Research Findings

[Full reply text from completed interaction]
```

On final line output exactly: `{"provider":"gemini","status":"success","file":"reports/research-gemini-[TIMESTAMP].md"}` or `{"provider":"gemini","status":"failed","error":"[message]"}`
```

**Progress display during dispatch:**
```text
Executing Research (parallel subagents)
========================================
[Claude]  context:fork subagent dispatched...
[OpenAI]  context:fork subagent dispatched...
[Gemini]  context:fork subagent dispatched...

All three subagents running in parallel. Watch agent-in-progress indicators.
Note: No real-time streaming progress — results arrive when each subagent completes.
Expected duration: brief ~2-5 min | standard ~5-15 min | comprehensive ~15-30 min
```

### Phase 5: Collect Results and Synthesize

After all subagents complete, collect their output status:

**Step 5.1: Read Provider Output Files**

For each subagent that returned `"status":"success"`, use the Read tool to read the corresponding `reports/research-[provider]-[TIMESTAMP].md` file.

**Handle partial results:**
If one or more subagents failed or were skipped:
```text
Research completed with partial results.
  - Claude:  [Success | Failed (reason) | Skipped (no API key)]
  - OpenAI:  [Success | Failed (reason) | Skipped (no API key)]
  - Gemini:  [Success | Failed (reason) | Skipped (no API key)]

Synthesis will proceed with available sources.
```

**Step 5.2: Synthesize into Unified Report**

Apply cross-provider synthesis:

1. **Identify Consensus:** Facts and recommendations that appear across multiple sources
2. **Note Contradictions:** Where sources disagree, present both perspectives with source attribution
3. **Preserve Unique Insights:** Include valuable information unique to one source (attributed)
4. **Structure for the Research Question:** Organize around directly answering the original question

**Synthesis Criteria (priority order):**
- **Accuracy:** Cross-validate facts across sources
- **Completeness:** Preserve unique insights from each source
- **Coherence:** Unified narrative, not a patchwork
- **Attribution:** Clear source labels for claims (e.g., `[Claude]`, `[OpenAI]`, `[Gemini]`)
- **Actionability:** Practical takeaways highlighted

### Phase 6: Output

**Step 6.1: Write Synthesized Markdown**

Use the Write tool to create the synthesized report. Read the Report Structure Template in `references/research-models.md` for the full template (sections: Executive Summary, Key Findings with attribution, Detailed Analysis, Contradictions & Nuances, Unique Insights by Source, Recommendations, Sources & Attribution, Methodology Note).

- **Location:** `reports/` directory (create if doesn't exist)
- **Filename:** `research-[topic-slug]-[TIMESTAMP].md`
- **topic-slug:** URL-friendly lowercase version of the topic (hyphens, no special chars)

**Step 6.2: Generate DOCX (if requested)**

If `--format docx` or `--format both` (default), generate a Word document:

```bash
# Check if pandoc is available
command -v pandoc >/dev/null 2>&1 || echo "pandoc not installed"

# If available, convert
pandoc "reports/research-[topic-slug]-[TIMESTAMP].md" \
  -o "reports/research-[topic-slug]-[TIMESTAMP].docx" \
  --from markdown --to docx
```

If pandoc is not installed:
```text
Note: DOCX output requires pandoc. Install with:
  - Windows: choco install pandoc
  - macOS: brew install pandoc
  - Linux: sudo apt install pandoc

Markdown report generated. Run the pandoc command above to create DOCX.
```

**Final Output:**
```yaml
Research Complete
=================
Topic: [topic]
Duration: [total time]
Sources: [N] of [M requested] successful

Subagent Results:
  - Claude:  [Success | Failed | Skipped]
  - OpenAI:  [Success | Failed | Skipped]
  - Gemini:  [Success | Failed | Skipped]

Output Files:
  - reports/research-[topic]-[TIMESTAMP].md   (synthesized)
  - reports/research-claude-[TIMESTAMP].md    (provider file, if success)
  - reports/research-openai-[TIMESTAMP].md    (provider file, if success)
  - reports/research-gemini-[TIMESTAMP].md    (provider file, if success)
  - reports/research-[topic]-[TIMESTAMP].docx (if pandoc available)

Word Count: [N] words
```

## Error Handling

| Error | Response |
|-------|----------|
| Missing API key for a provider | Skip that provider's subagent; continue with others |
| Missing API keys for ALL providers | Abort with error; suggest running `/unlock` |
| Single subagent API failure | Continue with available sources; note in output |
| All subagents fail | Abort with error details |
| Timeout in subagent (>30 min) | Subagent exits; parent proceeds with partial results |
| Rate limit | Subagent retries with exponential backoff internally |
| Invalid/empty response | Subagent exits with `"status":"failed"`; parent notes in partial results |

## Performance

| Depth | Expected Duration | Notes |
|-------|-------------------|-------|
| Brief | 2-5 minutes | Faster Claude call; shorter OpenAI/Gemini jobs |
| Standard | 5-15 minutes | Deep research polling; subagents run concurrently |
| Comprehensive | 15-30 minutes | Extended thinking; async deep research; concurrent |

Duration reflects wall-clock time for the slowest subagent (all three run in parallel).

## Cost Considerations

Running all three providers at "comprehensive" depth may cost $2-5+ per query. For detailed cost estimates, read `references/research-models.md`. Use `--sources` to select specific providers.

## Examples

**Basic research:**
```text
/research-topic What are the best practices for implementing RAG systems in production?
```

**Targeted research with options:**
```text
/research-topic --sources claude,openai --depth comprehensive \
  "Compare transformer architectures for long-context processing"
```

**Quick research, no clarification:**
```text
/research-topic --depth brief --no-clarify \
  "Current state of quantum computing for optimization problems"
```

**Skip a missing provider gracefully:**
If `OPENAI_API_KEY` is not set, the OpenAI subagent is skipped automatically. Research proceeds with Claude + Gemini.

## Execution Summary

Follow these steps in order:

1. **Intake** — Accept research request from user
2. **Audience Profile** — Detect profile in CLAUDE.md files, confirm or collect (skip with `--no-audience`)
3. **Clarification** — Run clarification loop (REQUIRED unless `--no-clarify`)
4. **Pre-Execution Gate** — Check API key availability for selected providers; show PASSED/PARTIAL/FAILED; skip providers with missing keys
5. **Confirmation** — Present research brief (with audience summary and skip list) and wait for user approval
6. **Resolve Models** — Read env vars; fall back to defaults from `references/research-models.md`
7. **Parallel Dispatch** — Dispatch one `context: fork` Task subagent per available provider simultaneously; each subagent calls its provider API, polls if async, writes `reports/research-[provider]-[TIMESTAMP].md`
8. **Collect Results** — After all subagents complete, note each provider's success/failure status
9. **Read Provider Files** — Use Read tool to read each successful provider output file
10. **Synthesize** — Merge provider outputs into unified report following the Report Structure template in `references/research-models.md`
11. **Write Report** — Use Write tool to save synthesized report as `reports/research-[topic-slug]-[TIMESTAMP].md`
12. **DOCX Generation** — If format includes docx, run pandoc to convert
13. **Summary** — Display completion summary with subagent results, file locations, and word count
