# Research Models Reference

Reference tables for the `/research-topic` skill. Loaded on demand to keep the main skill prompt focused on workflow logic.

## Table of Contents

- [Provider Configurations](#provider-configurations)
- [Default Model Names](#default-model-names)
- [Depth Parameter Mapping](#depth-parameter-mapping)
- [Model Check Output Examples](#model-check-output-examples)
- [Cost Estimates by Depth](#cost-estimates-by-depth)

---

## Provider Configurations

| Provider | Default Model | Endpoint | Mode |
|----------|---------------|----------|------|
| Anthropic | claude-opus-4-5-20251101 | /v1/messages | Synchronous (extended thinking) |
| OpenAI | o3-deep-research-2025-06-26 | /v1/responses | Async (background + web_search_preview) |
| Google | deep-research-pro-preview-12-2025 | /v1beta/interactions | Async (deep-research agent) |

**Note:** Models can be overridden via environment variables (`ANTHROPIC_MODEL`, `OPENAI_MODEL`, `GEMINI_AGENT`).

---

## Default Model Names

These are the default model identifiers used when environment variable overrides are not set. All defaults are annotated with their last-verified date.

| Provider | Env Var Override | Default Value | Last Verified |
|----------|-----------------|---------------|---------------|
| Anthropic | `ANTHROPIC_MODEL` | `claude-opus-4-5-20251101` | 2026-03-04 |
| OpenAI | `OPENAI_MODEL` | `o3-deep-research-2025-06-26` | 2026-03-04 |
| Google | `GEMINI_AGENT` | `deep-research-pro-preview-12-2025` | 2026-03-04 |

# Default as of 2026-03-04 -- verify with provider if errors occur

**Resolution Order:**
1. Check environment variable (e.g., `ANTHROPIC_MODEL`)
2. Use the skill's model check feature (`check-models` command)
3. Fall back to hardcoded defaults listed above

---

## Depth Parameter Mapping

| User Selection | Anthropic budget_tokens | OpenAI effort | Google thinking_level |
|----------------|-------------------------|---------------|-----------------------|
| Brief          | 4,000                   | medium        | low                   |
| Standard       | 10,000                  | high          | high                  |
| Comprehensive  | 32,000                  | xhigh         | high                  |

---

## Model Check Output Examples

**If newer models are found:**
```yaml
Model Version Check
===================
Current models:
  Anthropic: claude-opus-4-5-20251101
  OpenAI:    o3-deep-research-2025-06-26
  Gemini:    deep-research-pro-preview-12-2025

Upgrades Available:
  Anthropic: claude-opus-4-5-20260115 (2026-01-15)
    Newer model available. Update ANTHROPIC_MODEL in .env to use.

Would you like to:
1. Continue with current models
2. Update .env to use newer models (recommended)
```

**If AUTO_UPGRADE_MODELS=true:** Skip prompt and automatically use the newest available models for this session (does not modify .env).

**If no upgrades available:**
```text
All models are up to date.
```

---

## Cost Estimates by Depth

Running all three providers at "comprehensive" depth may cost $2-5+ per query.

| Depth | Claude | OpenAI | Gemini | Total (est.) |
|-------|--------|--------|--------|--------------|
| Brief | ~$0.20 | ~$0.30 | ~$0.25 | ~$0.75 |
| Standard | ~$0.50 | ~$0.75 | ~$0.60 | ~$1.85 |
| Comprehensive | ~$1.50 | ~$2.00 | ~$1.50 | ~$5.00 |

Consider using `--sources` to select specific providers for cost management.

---

## Report Structure Template

Use this structure for the synthesized output report:

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

---

## Bug Report JSON Format

Bug reports are saved to `reports/bugs/` with this schema:

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

**Detectable anomalies:**
- API errors (failed provider calls)
- Timeouts (requests exceeding 720s)
- Empty responses (less than 100 characters)
- Truncated content (detected via truncation indicators)
- Suspiciously short responses for the depth level
- Partial failures (some providers failed)
