---
name: research-topic
description: Orchestrate parallel deep research across multiple LLM providers using native context:fork subagents and synthesize results. Suggest when — in-depth topic research, multi-provider perspective comparison, well-sourced analysis needed, "deep research"/"research report" keywords, or thorough technical/strategic/emerging topic investigation.
effort: high
allowed-tools: Read, Write, Bash(echo:*), Bash(date:*), Bash(command:*), Bash(pandoc:*), Bash(curl:*), WebSearch, WebFetch, Task
---

# Multi-Source Deep Research

You are orchestrating parallel deep research across three LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini) using native `context: fork` subagents and synthesizing the results into a unified deliverable.

**Architecture:** Three subagents dispatch in parallel — one per provider. Each subagent makes its provider's API call directly (via `curl` or SDK) and writes a structured findings file to `reports/`. Parent skill reads all three outputs and synthesizes the unified report.

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
- `ANTHROPIC_API_KEY` - For Claude with adaptive thinking
- `OPENAI_API_KEY` - For OpenAI Deep Research
- `GOOGLE_API_KEY` - For Gemini Deep Research

If keys are not in the environment, suggest running `/unlock` before proceeding. Do NOT write API keys to `.env` files.

**Optional Model Configuration (non-sensitive, safe for .env):**
- `ANTHROPIC_MODEL` - Override Claude model. Default: `claude-opus-5`
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
```text
Pre-Execution Check: PARTIAL/FAILED

Missing API keys:
  - ANTHROPIC_API_KEY (required for claude source)
  - OPENAI_API_KEY (required for openai source)
  - GOOGLE_API_KEY (required for gemini source)

To load API keys from Bitwarden, run: /unlock
```

**If all keys present for selected sources:**
```text
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
CLAUDE_MODEL="${ANTHROPIC_MODEL:-claude-opus-5}"
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

| Depth | Claude effort | Claude max_tokens | OpenAI effort | Gemini thinking_level |
|-------|---------------|-------------------|---------------|-----------------------|
| brief | low | 8,000 | medium | low |
| standard | medium | 16,000 | high | high |
| comprehensive | high | 32,000 | high | high |

Claude's ladder tops out at `high` — not `xhigh`/`max` — because this leg is a single
non-streaming request. Anthropic requires `max_tokens` >= 64,000 at those levels, which
cannot finish inside the curl timeout. `high` is Anthropic's recommended minimum for
intelligence-sensitive work, so the comprehensive tier still sits on a solid floor.

**Dispatch subagents in parallel** (one Task per available provider, `context: fork`, skip providers with missing keys). Instantiate the template below once per provider, substituting its row from the Provider Deltas table. The dispatched subagent Reads `references/research-provider-protocols.md` (relative to this plugin's directory) for its provider's exact request/response shape, polling mechanics, and parse/output steps.

#### Subagent Prompt Template

```text
context: fork

You are a research agent responsible for the [DISPLAY NAME] research leg of a multi-provider research task.

Your job:
1. Execute the [DISPLAY NAME] protocol documented in `references/research-provider-protocols.md` under "[DISPLAY NAME] Protocol" (Mode row below: synchronous single call, or submit-then-poll)
2. Write your findings to reports/research-[SLUG]-[TIMESTAMP].md
3. Return a JSON status object on your final line

Provider: [DISPLAY NAME]
Model/Agent: [RESOLVED MODEL/AGENT VAR]
API Key env var: [API KEY ENV VAR]

Research prompt to submit:
[FULL RESEARCH PROMPT FROM PHASE 4]

Depth parameters (`[DEPTH PARAM]`): [value(s) — see the Depth-to-parameter mapping above, this provider's column(s), at the selected depth. Claude takes two: `output_config.effort` and `max_tokens`.]

Read `references/research-provider-protocols.md` → "[DISPLAY NAME] Protocol" for the exact endpoint, auth, request body, polling loop (if any), and parse/output steps. Use the Write tool to save findings in the structure shown there.

On final line output exactly: `{"provider":"[SLUG]","status":"success","file":"reports/research-[SLUG]-[TIMESTAMP].md"}` or `{"provider":"[SLUG]","status":"failed","error":"[message]"}`
```

#### Provider Deltas

| | Claude | OpenAI | Gemini |
|---|---|---|---|
| Display name | Anthropic Claude | OpenAI | Google Gemini |
| Slug | `claude` | `openai` | `gemini` |
| Endpoint | `api.anthropic.com/v1/messages` | `api.openai.com/v1/responses` | `generativelanguage.googleapis.com/v1beta/interactions` |
| Auth | `x-api-key` + `anthropic-version` headers | `Authorization: Bearer` header | `?key=` query param |
| API key env var | `ANTHROPIC_API_KEY` | `OPENAI_API_KEY` | `GOOGLE_API_KEY` |
| Model/Agent field (body) | `model` | `model` | `agent` |
| Resolved var | `[RESOLVED_CLAUDE_MODEL]` | `[RESOLVED_OAI_MODEL]` | `[RESOLVED_GEMINI_AGENT_ID]` |
| Mode | Synchronous, single call | Async: submit, poll ≤180× @10s, success = `status=="completed"` | Async: submit, poll ≤180× @10s, success = `state=="SUCCEEDED"` |
| Depth param | `output_config.effort` + `max_tokens` | `reasoning.effort` | `parameters.thinking_level` |
| Parse target | `text` blocks (skip `thinking`) | `text` output | reply text |
| Silent-failure check | `stop_reason` — `refusal` returns HTTP 200 with empty/partial content | HTTP status + `error` body | HTTP status + `error` body |

Full curl requests, poll loops, and Write-tool output structures for each provider: `references/research-provider-protocols.md`.

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
| Claude safety refusal | HTTP 200 with `stop_reason: "refusal"` and empty/partial content — the subagent treats it as a failure rather than writing an empty report |

## Performance

| Depth | Expected Duration | Notes |
|-------|-------------------|-------|
| Brief | 2-5 minutes | Faster Claude call; shorter OpenAI/Gemini jobs |
| Standard | 5-15 minutes | Deep research polling; subagents run concurrently |
| Comprehensive | 15-30 minutes | `high`-effort adaptive thinking; async deep research; concurrent |

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
