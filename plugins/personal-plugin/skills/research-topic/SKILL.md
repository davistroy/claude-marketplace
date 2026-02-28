---
name: research-topic
description: Orchestrate parallel deep research across multiple LLM providers and synthesize results
allowed-tools: Read, Write, Bash, WebSearch, WebFetch
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
- `--no-audience` - Skip audience profile detection, use default profile

**Environment Requirements:**
API keys must be loaded into the environment before use. The primary method is the `/unlock` skill, which loads secrets from Bitwarden Secrets Manager via the `bws` CLI (see CLAUDE.md Secrets Management Policy):
- `ANTHROPIC_API_KEY` - For Claude with Extended Thinking
- `OPENAI_API_KEY` - For OpenAI Deep Research (o3)
- `GOOGLE_API_KEY` - For Gemini Deep Research

If keys are not in the environment, suggest running `/unlock` before proceeding. Do NOT write API keys to `.env` files.

**Optional Model Configuration (in .env):**
- `ANTHROPIC_MODEL` - Override Claude model (default: claude-opus-4-5-20251101)
- `OPENAI_MODEL` - Override OpenAI model (default: o3-deep-research-2025-06-26)
- `GEMINI_AGENT` - Override Gemini agent (default: deep-research-pro-preview-12-2025)
- `CHECK_MODEL_UPDATES` - Check for newer models on startup (default: true)
- `AUTO_UPGRADE_MODELS` - Auto-upgrade without prompting (default: false)

**Validation:**
Before proceeding, run the background dependency check and handle any issues.

### Step 1: Set Up Tool Path and Start Background Check

The tool is bundled at `../tools/research-orchestrator/` relative to this skill file.

**IMPORTANT:** Start the dependency check in the background IMMEDIATELY so it runs in parallel with clarification:

```bash
# Determine the plugin directory (use ${CLAUDE_PLUGIN_ROOT} or adjust path as needed)
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/personal-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/research-orchestrator/src"

# Start background check (run_in_background=true)
PYTHONPATH="$TOOL_SRC" python -m research_orchestrator check-ready
```

This outputs JSON with the status of:
- Python packages (anthropic, openai, google-genai, rich, python-dotenv, pydantic, tenacity)
- API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY)
- Optional tools (pandoc)

**Do NOT wait for this to complete** - proceed immediately to Phase 1 (Intake) and Phase 2 (Clarification). You will check the results before execution.

### Step 2: Check Model Versions (OPTIONAL)

**Execute this step** if user has not specified `--skip-model-check`:

```bash
PYTHONPATH="$TOOL_SRC" python -m research_orchestrator check-models
```

**If newer models are found:**
```yaml
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
```text
✓ All models are up to date.
```

## Tool vs Claude Responsibilities

Understanding what the Python tool handles vs what you (Claude) must do:

| Component | Responsibility | What It Does |
|-----------|----------------|--------------|
| **research-orchestrator (Python tool)** | Parallel API execution | Calls Claude, OpenAI, Gemini APIs concurrently; polls async APIs; saves individual provider outputs to `reports/research-[provider]-[timestamp].md` |
| **You (Claude)** | Clarification & Confirmation | Phases 1-3: Ask clarifying questions, confirm research brief with user |
| **You (Claude)** | Synthesis | Phase 5: Read provider outputs, merge into unified report following template |
| **You (Claude)** | Output Generation | Phase 6: Write synthesized report, generate DOCX via pandoc |

The tool is a helper for the parallel API calls. All user interaction, synthesis, and final output generation is your responsibility.

## Workflow

### Phase 1: Intake

Accept the research request from the user. If no request is provided in arguments, prompt:
```text
What would you like to research?

Please describe your research question or topic. Include any relevant context
about scope, audience, or specific aspects you want explored.
```

### Phase 1.5: Audience Profile Detection

**Purpose:** Tailor research output to the user's profile by detecting or collecting audience information.

**Step 1: Search for Existing Profile**

Search for an audience/user profile in CLAUDE.md files in this priority order:
1. **Project:** `./CLAUDE.md` or `./.claude/CLAUDE.md`
2. **Local:** `./.claude.local/CLAUDE.md`
3. **Global:** `~/.claude/CLAUDE.md` (Windows: `%USERPROFILE%\.claude\CLAUDE.md`)

Look for sections matching these patterns (case-insensitive):
- `# Audience Profile` or `## Audience Profile`
- `# User Profile` or `## User Profile`
- `# Target Audience` or `## Target Audience`
- `# Troy Davis — Audience Profile` (or similar name-prefixed headers)
- `# Reader Profile` or `## Reader Profile`

Extract the profile content (everything under the header until the next same-level or higher header).

**Step 2A: If Profile Found**

Display a concise summary and confirm:
```yaml
Audience Profile Detected
=========================
Source: [path to CLAUDE.md where found]

Summary:
  - Role: [extracted role/title]
  - Background: [key expertise areas]
  - Preferences: [communication style preferences]

Use this profile for research? (yes/modify)
```

If user says "modify":
- Show the full profile text
- Let user edit inline or provide replacement text
- Use modified version for this session only (don't save changes)

**Step 2B: If No Profile Found**

Prompt user to provide audience context:
```text
No audience profile found in CLAUDE.md files.

For better-tailored research, describe your target audience:

Example profile (modify as needed):
─────────────────────────────────────
Role: Senior technology executive (Director/VP level)
Background: Enterprise software architecture, cloud infrastructure
Expertise: AI/ML systems, digital transformation
Preferences:
  - Actionable insights over theoretical discussion
  - Data-driven analysis with concrete examples
  - Strategic framing with ROI considerations
Technical depth: Comfortable with technical details but values strategic clarity
─────────────────────────────────────

Enter your audience profile (or press Enter to use the example above):
```

After user provides profile (or accepts default):
```text
Would you like to save this profile to your global CLAUDE.md for future sessions?
This will add an "Audience Profile" section to ~/.claude/CLAUDE.md

(yes/no)
```

If "yes":
- Read existing `~/.claude/CLAUDE.md` (create if doesn't exist)
- Append the audience profile section:
```markdown

# Audience Profile

[user's profile content]
```

**Step 3: Store for Session**

Store the confirmed/provided audience profile for use in Phase 4 prompt construction.

**Skip Conditions:**
- If `--no-audience` flag is provided, skip this phase entirely and use the default profile
- If user explicitly says "skip" or "none", use the default profile

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
```text
To ensure comprehensive research, I have a few clarifying questions:

1. Scope: Should this focus on [specific aspect A] or cover [broader topic B]?
2. Audience: Is this for technical practitioners or executive decision-makers?
3. Depth: Do you want a summary overview or detailed analysis with citations?
```

### Phase 3: Pre-Execution Gate

**BEFORE presenting the research brief**, check the results of the background dependency check:

1. **If `check-ready` returned failures:**
   - Show which packages are missing
   - Show which API keys are not configured
   - Ask user to fix issues before proceeding

   **Example output if packages missing:**
   ```
   Pre-Execution Check: FAILED

   Missing Python packages:
     - rich: Install with `pip install rich`
     - google-genai: Install with `pip install google-genai`

   Would you like me to install these packages now?
   ```

   **If API keys are missing:**

   ```
   Pre-Execution Check: FAILED

   Missing API keys for selected sources:
     - ANTHROPIC_API_KEY (required for claude source)
     - OPENAI_API_KEY (required for openai source)
     - GOOGLE_API_KEY (required for gemini source)

   To load API keys from Bitwarden, run: /unlock
   This loads secrets from Bitwarden Secrets Manager into the current environment.

   See CLAUDE.md Secrets Management Policy for details on storing and retrieving secrets.
   ```

   If keys are still missing after `/unlock`, ask the user to verify the secrets are stored in their Bitwarden vault. Do NOT offer to write keys to `.env` files or guide users through creating `.env` files with API keys.

2. **If `check-ready` passed:**
   ```
   Pre-Execution Check: PASSED

   All dependencies installed
   API keys configured for: claude, openai, gemini
   ```

3. **Present the research brief:**

```yaml
Research Brief
==============
Topic: [refined topic statement]
Scope: [defined boundaries]
Depth: [brief/standard/comprehensive]
Sources: [claude, openai, gemini - as selected]
Deliverable: [expected output structure]

Target Audience:
  Role: [from Phase 1.5 profile]
  Background: [key expertise areas]
  Preferences: [communication style]
  Source: [CLAUDE.md path or "User-provided" or "Default"]

Proceed with this research brief? (yes/revise)
```

Wait for user confirmation. If they request revisions, incorporate changes and re-confirm.

### Phase 4: Parallel Research Execution

Execute research calls to selected LLM providers concurrently.

**Audience Context:**
Use the audience profile collected in Phase 1.5. If Phase 1.5 was skipped (via `--no-audience` or user chose "skip"), use this default:
- **Role:** Senior Director/VP-level technology executive
- **Background:** Enterprise software architecture, AI/ML systems, cloud infrastructure
- **Interests:** Emerging technology trends, practical implementation strategies, ROI-focused analysis
- **Communication style:** Prefers actionable insights, executive summaries, and data-driven recommendations
- **Technical depth:** Comfortable with technical details but values strategic framing

**Craft the Research Prompt:**
Transform the refined brief into an effective research prompt that includes the audience profile from Phase 1.5:
```text
Research Request: [topic]

Context:
- Scope: [boundaries]
- Depth: [level]

Target Audience Profile:
[INSERT AUDIENCE PROFILE FROM PHASE 1.5 HERE]

The research should be tailored to this audience's:
- Role and decision-making context
- Technical background and expertise level
- Preferred communication style and format
- Key interests and evaluation criteria

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

# Execute research with streaming UI for real-time progress visibility
PYTHONUNBUFFERED=1 STREAMING_UI=1 PYTHONPATH="$TOOL_SRC" python -u -m research_orchestrator execute \
  --prompt "<research_prompt>" \
  --sources "<claude,openai,gemini>" \
  --depth "<brief|standard|comprehensive>" \
  --output-dir "<reports_directory>"
```

**Environment Variables for UI:**
- `PYTHONUNBUFFERED=1` - Ensures output is not buffered
- `STREAMING_UI=1` - Uses line-by-line streaming output for visibility in Claude Code
- `python -u` - Additional unbuffered flag for Python

The tool handles:
- Parallel execution across providers
- Polling for async APIs (OpenAI and Google deep research)
- Timeout handling (default 1800s = 30 minutes for deep research)
- Real-time progress updates with status indicators
- Error recovery (continue with available sources if one fails)

**Provider Configurations:**

| Provider | Default Model | Endpoint | Mode |
|----------|---------------|----------|------|
| Anthropic | claude-opus-4-5-20251101 | /v1/messages | Synchronous (extended thinking) |
| OpenAI | o3-deep-research-2025-06-26 | /v1/responses | Async (background + web_search_preview) |
| Google | deep-research-pro-preview-12-2025 | /v1beta/interactions | Async (deep-research agent) |

**Note:** Models can be overridden via environment variables (`ANTHROPIC_MODEL`, `OPENAI_MODEL`, `GEMINI_AGENT`).

**Progress Display:**
```text
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

Once the research-orchestrator tool completes, **you (Claude) must synthesize the results**.

The tool saves individual provider responses to `reports/research-[provider]-[timestamp].md`. You must now read these files and create a unified synthesized report.

**Step 5.1: Read Provider Outputs**

After the tool completes, read each generated file:

```bash
# The tool output shows the saved file paths, e.g.:
# Saved: reports/research-claude-20260118-005325.md
# Saved: reports/research-openai-20260118-005325.md
# Saved: reports/research-gemini-20260118-005325.md
```

Use the Read tool to read each provider's output file.

**Step 5.2: Synthesize into Unified Report**

Apply the consolidate-documents approach to merge the provider responses:

1. **Identify Consensus:** Find facts and recommendations that appear across multiple sources
2. **Note Contradictions:** Where sources disagree, present both perspectives with source attribution
3. **Preserve Unique Insights:** Include valuable information that only appears in one source (attributed)
4. **Structure for the Research Question:** Organize around directly answering the user's original question

**Synthesis Criteria (priority order):**
- **Accuracy**: Cross-validate facts across sources
- **Completeness**: Preserve unique insights from each source
- **Coherence**: Unified narrative, not a patchwork
- **Attribution**: Clear source labels for claims (e.g., "[Claude]", "[OpenAI]", "[Gemini]")
- **Actionability**: Practical takeaways highlighted

**Handling Partial Results:**
If one or more APIs failed:
```text
Note: Research completed with partial results.
  - Claude: Success
  - OpenAI: Failed (timeout after 720s)
  - Gemini: Success

The synthesis below is based on available sources. Consider re-running
with --sources claude,gemini to retry the failed provider.
```

### Phase 6: Output

**You (Claude) must write the synthesized report and optionally generate DOCX.**

**Step 6.1: Write Synthesized Markdown**

Create the synthesized report file using the Write tool:
- **Location:** `reports/` directory (create if doesn't exist)
- **Filename:** `research-[topic-slug]-YYYYMMDD-HHMMSS.md`

The topic-slug should be a URL-friendly version of the topic (lowercase, hyphens, no special chars).

**Step 6.2: Generate DOCX (if requested)**

If `--format docx` or `--format both` (default), generate a Word document using pandoc:

```bash
# Check if pandoc is available
command -v pandoc >/dev/null 2>&1 || echo "pandoc not installed"

# If pandoc is available, convert to DOCX
pandoc "reports/research-[topic-slug]-YYYYMMDD-HHMMSS.md" \
  -o "reports/research-[topic-slug]-YYYYMMDD-HHMMSS.docx" \
  --from markdown --to docx
```

If pandoc is not installed, inform the user:
```text
Note: DOCX output requires pandoc. Install with:
  - Windows: choco install pandoc
  - macOS: brew install pandoc
  - Linux: sudo apt install pandoc

Markdown report has been generated. Run the pandoc command above to create DOCX.
```

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
```yaml
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

### Phase 7: Bug Report Summary

After research completes, check if any bugs/anomalies were detected during execution.

**The tool automatically detects:**
- API errors (failed provider calls)
- Timeouts (requests exceeding 720s)
- Empty responses (less than 100 characters)
- Truncated content (detected via truncation indicators)
- Suspiciously short responses for the depth level
- Partial failures (some providers failed)

**If bugs were detected:**
```text
Bug Report Summary
==================
Detected [N] issues during research execution:

[warning] OPENAI: Response shorter than expected for comprehensive depth (2847 < 3000 chars)
[error] GEMINI: Request timed out after 720s

Bug reports saved to: reports/bugs/
  - bug-20260118-143052-openai.json
  - bug-20260118-143055-gemini.json

These issues may affect research quality. Review the individual provider reports for details.
```

**If no bugs detected:**
```text
Bug Report Summary
==================
No issues detected. All providers responded normally.
```

**Bug report JSON format:**
```json
{
  "id": "bug-20260118-143052-openai",
  "timestamp": "2026-01-18T14:30:52Z",
  "category": "timeout",
  "provider": "openai",
  "severity": "error",
  "prompt_preview": "Research the impact of...",
  "depth": "comprehensive",
  "error_message": "Request timed out after 720s",
  "duration_seconds": 720.3,
  "model_version": "o3-deep-research-2025-06-26"
}
```

## Error Handling

| Error | Response |
|-------|----------|
| Missing API key | List missing keys, suggest running `/unlock` to load from Bitwarden |
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

## Execution Summary

Follow these steps in order:

1. **Setup** - Parse arguments, set up tool path
2. **Background Check** - Start `check-ready` command in background (runs parallel to clarification)
3. **Model Check** - Check for model version upgrades (optional, skip with --skip-model-check)
4. **Intake** - Accept research request from user
5. **Audience Profile** - Detect profile in CLAUDE.md files, confirm or collect (skip with --no-audience)
6. **Clarification** - Run clarification loop (REQUIRED unless --no-clarify) using AskUserQuestion tool
7. **Pre-Execution Gate** - Check background check results, show PASSED/FAILED, resolve any issues
8. **Confirmation** - Present research brief (including audience summary) and wait for user approval
9. **Tool Execution** - Run research-orchestrator tool with audience-tailored prompt (saves individual provider files to reports/)
10. **Read Results** - Use Read tool to read each provider output file from reports/
11. **Synthesize** - Merge provider outputs into unified report following the Report Structure template
12. **Write Report** - Use Write tool to save synthesized report as `research-[topic-slug]-[timestamp].md`
13. **DOCX Generation** - If format includes docx, run pandoc to convert markdown to Word
14. **Bug Report** - Summarize any detected bugs/anomalies, show saved bug report locations
15. **Summary** - Display completion summary with file locations and word count
