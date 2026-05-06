---
name: sg-research
description: Conduct autonomous web research on a topic using Claude Agent SDK, producing structured research.json
argument-hint: "<topic> [--output path] [--max-sources N]"
allowed-tools: Bash, Read, Glob, Grep
---

# Slide Generator: Research Step

Run the research phase of the slide-generator pipeline. This step uses the Claude Agent SDK to conduct autonomous web research, producing a structured `research.json` artifact that feeds the outline step.

## Pre-loaded Context

**Working directory:**
!`pwd`

**Slide-generator installation check:**
!`sg --version 2>&1 || echo "NOT INSTALLED"`

**API key status:**
!`sg health-check 2>&1 | head -10`

## Proactive Triggers

Suggest this skill when:
1. User wants to research a topic for a presentation
2. User says "research [topic]" or "find information about [topic] for slides"
3. User wants to start the slide generation pipeline from scratch
4. User has a topic but no research.json yet

## Prerequisites

- `slide-generator` package installed (`pip install -e ".[all]"` from the slide-generator repo)
- `ANTHROPIC_API_KEY` set in environment
- Working directory where output should be saved

## Input Validation

**Required:**
- `<topic>` - The research topic (quoted string)

**Optional:**
- `--output <path>` - Output file path (default: `research.json` in current directory)
- `--max-sources <N>` - Maximum number of sources to research (default: 20)

## Instructions

1. **Validate environment**: Confirm `sg` CLI is available and API keys are set via `sg health-check`
2. **Run research**:
   ```bash
   sg research "<topic>" --output research.json
   ```
3. **Verify output**: Confirm `research.json` was created and contains valid JSON with research findings
4. **Report results**: Show a brief summary of what was found (number of sources, key themes)

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `ANTHROPIC_API_KEY not found` | Missing env var | Set the key: `export ANTHROPIC_API_KEY=...` |
| `Rate limit exceeded` | Too many API calls | Wait 60s and retry, or reduce `--max-sources` |
| `Research timeout` | Topic too broad | Narrow the topic or increase `SG_API_TIMEOUT` |
| `sg: command not found` | Not installed | Run `pip install -e ".[all]"` from slide-generator repo |

## Output

The research step produces `research.json` containing:
- Structured findings organized by subtopic
- Source URLs and citations
- Key facts and statistics
- Recommended presentation angles

## Next Step

After research completes, run the outline step:
```bash
sg outline research.json --output outline.json
```
Or use `/sg-outline` to continue the pipeline.
