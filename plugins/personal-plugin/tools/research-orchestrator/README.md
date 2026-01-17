# Research Orchestrator

A Python tool for orchestrating parallel deep research across multiple LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini) and synthesizing results.

## Installation

```bash
pip install research-orchestrator
```

Or install with optional docx support:

```bash
pip install research-orchestrator[docx]
```

## Configuration

Set the following environment variables (or use a `.env` file):

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
```

## Usage

### Command Line

```bash
# Execute research across all providers
research-orchestrator execute \
  --prompt "What are the best practices for implementing RAG systems?" \
  --depth standard \
  --output-dir ./reports

# Use specific providers only
research-orchestrator execute \
  --prompt "Compare transformer architectures" \
  --sources claude,openai \
  --depth comprehensive

# Check provider availability
research-orchestrator check-providers

# List supported depth levels
research-orchestrator list-depths
```

### Python API

```python
from research_orchestrator import ResearchOrchestrator, ResearchConfig, Depth

# Create orchestrator
orchestrator = ResearchOrchestrator()

# Configure research
config = ResearchConfig(
    prompt="What are the best practices for RAG systems?",
    sources=["claude", "openai", "gemini"],
    depth=Depth.STANDARD,
)

# Execute research (async)
import asyncio

async def main():
    results = await orchestrator.execute(config)

    for result in results:
        print(f"Provider: {result.provider}")
        print(f"Status: {result.status}")
        print(f"Content: {result.content[:500]}...")
        print("---")

asyncio.run(main())
```

## Depth Levels

| Level | Claude budget_tokens | OpenAI effort | Gemini thinking_level | Est. Cost |
|-------|---------------------|---------------|----------------------|-----------|
| brief | 4,000 | medium | low | ~$0.75 |
| standard | 10,000 | high | high | ~$1.85 |
| comprehensive | 32,000 | xhigh | high | ~$5.00 |

## Provider Details

### Anthropic Claude (Opus 4.5)
- Model: `claude-opus-4-5-20251101`
- Endpoint: `https://api.anthropic.com/v1/messages`
- Mode: Synchronous with extended thinking

### OpenAI GPT-5.2 Pro
- Model: `gpt-5.2-pro`
- Endpoint: `https://api.openai.com/v1/responses`
- Mode: Async (background) with web search tool

### Google Gemini 3 Pro
- Agent: `deep-research-pro-preview-12-2025`
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/interactions`
- Mode: Async (background) deep research agent

## Error Handling

The orchestrator handles failures gracefully:
- If one provider fails, results from other providers are still returned
- Automatic retry with exponential backoff for rate limits
- Configurable timeouts (default: 180s for deep research)

## License

MIT
