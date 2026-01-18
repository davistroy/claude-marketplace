---
name: research-topic
description: Orchestrate parallel deep research across multiple LLM providers and synthesize results
---

# Multi-Source Deep Research

You are orchestrating parallel deep research across three LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini) and synthesizing the results into a unified deliverable.

## Input Validation

**Required Arguments:**
- Research request (provided by user as $ARGUMENTS or in conversation)

**Optional Arguments:**
- `--sources <list>` - Comma-separated list of sources to use: `claude`, `openai`, `gemini` (default: all three)
- `--depth <level>` - Research depth: `brief`, `standard`, `comprehensive` (default: standard)
- `--format <type>` - Output format: `md`, `docx`, `both` (default: both)
- `--no-clarify` - Skip clarification loop, use request as-is

**Environment Requirements:**
API keys must be configured in environment variables:
- `ANTHROPIC_API_KEY` - For Claude with Extended Thinking
- `OPENAI_API_KEY` - For OpenAI Deep Research (o3)
- `GOOGLE_API_KEY` - For Gemini Deep Research

**Optional Model Configuration (in .env):**
- `ANTHROPIC_MODEL` - Override Claude model (default: claude-opus-4-5-20251101)
- `OPENAI_MODEL` - Override OpenAI model (default: o3-deep-research-2025-06-26)
- `GEMINI_AGENT` - Override Gemini agent (default: deep-research-pro-preview-12-2025)
- `CHECK_MODEL_UPDATES` - Check for newer models on startup (default: true)
- `AUTO_UPGRADE_MODELS` - Auto-upgrade without prompting (default: false)

**Validation:**
Before proceeding, check and install dependencies as needed.

### Step 1: Set Up Tool Path

The tool is bundled at `../tools/research-orchestrator/` relative to this skill file:

```bash
# Determine the plugin directory (use ${CLAUDE_PLUGIN_ROOT} or adjust path as needed)
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/personal-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/research-orchestrator/src"
```

### Step 2: Check and Install Python Dependencies

Check for required Python packages and install any that are missing:

```bash
# Check which packages are missing
python -c "import anthropic" 2>/dev/null || echo "anthropic: MISSING"
python -c "import openai" 2>/dev/null || echo "openai: MISSING"
python -c "from google import genai" 2>/dev/null || echo "google-genai: MISSING"
python -c "import dotenv" 2>/dev/null || echo "python-dotenv: MISSING"
python -c "import pydantic" 2>/dev/null || echo "pydantic: MISSING"
python -c "import tenacity" 2>/dev/null || echo "tenacity: MISSING"
```

**If any packages are missing, ask the user:**
> "The following Python packages are missing: [list]. Install them now with `pip install [packages]`?"

If user approves:
```bash
pip install anthropic openai google-genai python-dotenv pydantic tenacity
```

### Step 3: Verify API Keys

Check that API keys are available for selected sources. If missing:
```
Error: Missing API key(s) for selected source(s)

The following API keys are required but not found:
  - ANTHROPIC_API_KEY (for Claude)
  - OPENAI_API_KEY (for OpenAI)
  - GOOGLE_API_KEY (for Gemini)

Configure these in your environment or .env file.
See .env.example in the plugin directory for the required format.
```

### Step 4: Check Model Versions (RECOMMENDED)

**Execute this step** to check for newer model versions and offer upgrades. Skip only if the user explicitly requests to bypass with `--skip-model-check`:

```bash
# Set up tool path
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/personal-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/research-orchestrator/src"

# Check for model upgrades
PYTHONPATH="$TOOL_SRC" python -m research_orchestrator check-models
```

**If newer models are found:**
```
Model Version Check
===================
Current models:
  Anthropic: claude-opus-4-5-20251101
  OpenAI:    o3-deep-research-2025-06-26
  Gemini:    deep-research-pro-preview-12-2025

Upgrades Available:
  ⬆ Anthropic: claude-opus-4-5-20260115 (2026-01-15)
    Newer model available. Update ANTHROPIC_MODEL in .env to use.

Would you like to:
1. Continue with current models
2. Update .env to use newer models (recommended)
```

**If AUTO_UPGRADE_MODELS=true:** Skip prompt and automatically use the newest available models for this session (does not modify .env).

**If no upgrades available:**
```
✓ All models are up to date.
```

## Workflow

### Phase 1: Intake

Accept the research request from the user. If no request is provided in arguments, prompt:
```
What would you like to research?

Please describe your research question or topic. Include any relevant context
about scope, audience, or specific aspects you want explored.
```

### Phase 2: Clarification Loop (max 4 rounds)

**REQUIRED:** Unless `--no-clarify` is specified, you MUST run the clarification loop before proceeding to research execution. Even if the request seems clear, ask at least one round of clarifying questions to ensure the research is properly scoped.

Analyze the request for ambiguities and ask clarifying questions using the AskUserQuestion tool.

**Dimensions to Clarify:**
| Dimension | Question Type |
|-----------|---------------|
| **Scope** | Breadth vs depth, specific subtopics to include/exclude |
| **Audience** | Technical level, domain expertise assumed |
| **Depth** | Summary vs comprehensive analysis |
| **Deliverable** | Report structure, key sections needed |
| **Recency** | How current must information be? |
| **Sources** | Academic, industry, news, primary/secondary |

**Clarification Rules:**
- Ask 1-4 questions per round using the AskUserQuestion tool
- Stop clarifying when the request is sufficiently defined OR 4 rounds complete
- Group related questions logically
- Provide sensible defaults for questions user skips

**Example Clarification:**
```
To ensure comprehensive research, I have a few clarifying questions:

1. Scope: Should this focus on [specific aspect A] or cover [broader topic B]?
2. Audience: Is this for technical practitioners or executive decision-makers?
3. Depth: Do you want a summary overview or detailed analysis with citations?
```

### Phase 3: Confirmation

Present the refined research brief to the user:

```
Research Brief
==============
Topic: [refined topic statement]
Scope: [defined boundaries]
Audience: [target readers]
Depth: [brief/standard/comprehensive]
Sources: [claude, openai, gemini - as selected]
Deliverable: [expected output structure]

Proceed with this research brief? (yes/revise)
```

Wait for user confirmation. If they request revisions, incorporate changes and re-confirm.

### Phase 4: Parallel Research Execution

Execute research calls to selected LLM providers concurrently.

**Default Audience Context:**
Unless the user specifies otherwise, the default audience is a senior technology leader with the following profile:
- **Role:** Senior Director/VP-level technology executive
- **Background:** Enterprise software architecture, AI/ML systems, cloud infrastructure
- **Interests:** Emerging technology trends, practical implementation strategies, ROI-focused analysis
- **Communication style:** Prefers actionable insights, executive summaries, and data-driven recommendations
- **Technical depth:** Comfortable with technical details but values strategic framing

**Craft the Research Prompt:**
Transform the refined brief into an effective research prompt that includes audience context:
```
Research Request: [topic]

Context:
- Scope: [boundaries]
- Depth: [level]

Target Audience Profile:
The reader is a senior technology executive (Director/VP level) with deep experience
in enterprise software architecture, AI/ML systems, and cloud infrastructure. They are
evaluating emerging technologies for strategic decisions and prefer:
- Actionable, implementation-focused insights
- Data-driven analysis with concrete examples
- Strategic framing with ROI considerations
- Technical depth balanced with executive-level clarity
[Include any additional audience context from user if provided]

Please provide a comprehensive analysis covering:
1. [Key aspect 1]
2. [Key aspect 2]
3. [Key aspect 3]
...

Structure your response with:
- Executive summary (2-3 key takeaways)
- Detailed analysis with supporting evidence
- Practical implementation considerations
- Strategic recommendations

Include relevant examples, data points, and citations where available.
```

**Depth Parameter Mapping:**

| User Selection | Anthropic budget_tokens | OpenAI effort | Google thinking_level |
|----------------|-------------------------|---------------|-----------------------|
| Brief          | 4,000                   | medium        | low                   |
| Standard       | 10,000                  | high          | high                  |
| Comprehensive  | 32,000                  | xhigh         | high                  |

**API Calls:**

Use the research-orchestrator tool to execute parallel API calls. Run from source using PYTHONPATH:

```bash
# Set up tool path
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/personal-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/research-orchestrator/src"

# Execute research
PYTHONPATH="$TOOL_SRC" python -m research_orchestrator execute \
  --prompt "<research_prompt>" \
  --sources "<claude,openai,gemini>" \
  --depth "<brief|standard|comprehensive>" \
  --output-dir "<reports_directory>"
```

The tool handles:
- Parallel execution across providers
- Polling for async APIs (OpenAI and Google deep research)
- Timeout handling (default 720s for deep research - these APIs can take 5-10 minutes)
- Progress updates every 30 seconds during polling
- Error recovery (continue with available sources if one fails)

**Provider Configurations:**

| Provider | Default Model | Endpoint | Mode |
|----------|---------------|----------|------|
| Anthropic | claude-opus-4-5-20251101 | /v1/messages | Synchronous (extended thinking) |
| OpenAI | o3-deep-research-2025-06-26 | /v1/responses | Async (background + web_search_preview) |
| Google | deep-research-pro-preview-12-2025 | /v1beta/interactions | Async (deep-research agent) |

**Note:** Models can be overridden via environment variables (`ANTHROPIC_MODEL`, `OPENAI_MODEL`, `GEMINI_AGENT`).

**Progress Display:**
```
Executing Research
==================
[Claude] Extended thinking... (synchronous)
[OpenAI] Deep research initiated... polling for completion
[Gemini] Deep research initiated... polling for completion

Status:
  Claude:  [=====>    ] Processing (45s)
  OpenAI:  [=======>  ] Researching (72s)
  Gemini:  [========> ] Finalizing (89s)
```

### Phase 5: Synthesis

Once all (or available) responses are received, synthesize using the /consolidate-documents approach.

**Synthesis Steps:**

1. **Save Raw Responses:**
   Save each provider's response to temporary files:
   - `.tmp/research-claude-[timestamp].md`
   - `.tmp/research-openai-[timestamp].md`
   - `.tmp/research-gemini-[timestamp].md`

2. **Invoke Consolidation:**
   Use the consolidate-documents skill internally to merge responses:
   - Identify consensus findings across sources
   - Highlight contradictions or unique insights (attributed by source)
   - Structure output to directly answer the research question
   - Include source attribution section

3. **Synthesis Criteria (priority order):**
   - **Accuracy**: Cross-validate facts across sources
   - **Completeness**: Preserve unique insights from each source
   - **Coherence**: Unified narrative, not a patchwork
   - **Attribution**: Clear source labels for claims
   - **Actionability**: Practical takeaways highlighted

**Handling Partial Results:**
If one or more APIs fail:
```
Note: Research completed with partial results.
  - Claude: Success
  - OpenAI: Failed (timeout after 720s)
  - Gemini: Success

The synthesis below is based on available sources. Consider re-running
with --sources claude,gemini to retry the failed provider.
```

### Phase 6: Output

**Output Location:** `reports/` directory (create if doesn't exist)

**Filename Format:** `research-[topic-slug]-YYYYMMDD-HHMMSS.[ext]`

Generate both formats (unless `--format` specifies otherwise):
- `research-[topic]-YYYYMMDD-HHMMSS.md` - Markdown report
- `research-[topic]-YYYYMMDD-HHMMSS.docx` - Word document (via pandoc)

**Report Structure:**

```markdown
# [Research Topic]

**Generated:** [date]
**Sources:** [list of providers used]
**Depth:** [brief/standard/comprehensive]

## Executive Summary
[2-3 paragraph synthesis of key findings]

## Key Findings

### [Finding 1]
[Content with source attribution]

### [Finding 2]
[Content with source attribution]

...

## Detailed Analysis

### [Section 1]
[Comprehensive coverage]

### [Section 2]
[Comprehensive coverage]

...

## Contradictions & Nuances
[Where sources disagreed, with analysis of which perspective seems more accurate]

## Unique Insights by Source

### From Claude
[Insights unique to Claude's response]

### From OpenAI
[Insights unique to OpenAI's response]

### From Gemini
[Insights unique to Gemini's response]

## Recommendations
[Actionable next steps based on research]

## Sources & Attribution
- **Claude:** Extended thinking analysis (model: [configured model])
- **OpenAI:** o3 Deep research with web search (model: [configured model])
- **Gemini:** Deep research agent (agent: [configured agent])

## Methodology Note
This report synthesizes research from multiple AI providers to provide
balanced, cross-validated insights. Areas of consensus are highlighted,
while disagreements are explicitly noted for reader consideration.
```

**Final Output:**
```
Research Complete
=================
Topic: [topic]
Duration: [total time]
Sources: [N] of 3 successful

Output Files:
  - reports/research-[topic]-YYYYMMDD-HHMMSS.md
  - reports/research-[topic]-YYYYMMDD-HHMMSS.docx

Word Count: [N] words
Sections: [N]
```

## Error Handling

| Error | Response |
|-------|----------|
| Missing API key | List missing keys, abort with setup instructions |
| Single API failure | Continue with available sources, note in output |
| All APIs fail | Abort with error details, suggest troubleshooting |
| Timeout (>720s) | Cancel that source, continue with others |
| Rate limit | Retry with exponential backoff (2s, 4s, 8s, 16s) |
| Invalid response | Log error, exclude from synthesis |

## Cost Considerations

Running all three providers at "comprehensive" depth may cost $2-5+ per query.

**Cost Estimates by Depth:**
| Depth | Claude | OpenAI | Gemini | Total (est.) |
|-------|--------|--------|--------|--------------|
| Brief | ~$0.20 | ~$0.30 | ~$0.25 | ~$0.75 |
| Standard | ~$0.50 | ~$0.75 | ~$0.60 | ~$1.85 |
| Comprehensive | ~$1.50 | ~$2.00 | ~$1.50 | ~$5.00 |

Consider using `--sources` to select specific providers for cost management.

## Examples

**Basic research:**
```
/research-topic What are the best practices for implementing RAG systems in production?
```

**Targeted research with options:**
```
/research-topic --sources claude,openai --depth comprehensive \
  "Compare transformer architectures for long-context processing"
```

**Quick research, no clarification:**
```
/research-topic --depth brief --no-clarify \
  "Current state of quantum computing for optimization problems"
```

## Execution

1. Parse arguments and validate API key availability
2. Check for missing Python dependencies (install if needed)
3. Check for model version upgrades (recommended, skip with --skip-model-check)
4. **Run clarification loop** (REQUIRED unless --no-clarify) - ask at least one round of questions
5. Confirm research brief with user
6. Execute parallel research via research-orchestrator tool (default timeout: 720s)
7. Synthesize results using consolidate-documents approach
8. Generate output files in both formats
9. Display completion summary with file locations
