# API Key Setup Reference

This reference documents how to configure API keys for skills that require external LLM provider access (e.g., `/research-topic`, `/visual-explainer`).

## Primary Method: Bitwarden Secrets Manager

All API keys must be stored in Bitwarden and loaded via the `/unlock` skill. This follows the Secrets Management Policy defined in CLAUDE.md.

### Setup Steps

1. **Store keys in Bitwarden** - Add API keys as secrets in your Bitwarden Secrets Manager vault
2. **Run `/unlock`** - This skill loads secrets from Bitwarden into the current environment using the `bws` CLI
3. **Verify** - The `/research-topic` skill will check for required keys during its pre-execution gate

### Required API Keys

| Key | Provider | Purpose | Where to Get |
|-----|----------|---------|--------------|
| `ANTHROPIC_API_KEY` | Anthropic | Claude Extended Thinking | https://console.anthropic.com/ |
| `OPENAI_API_KEY` | OpenAI | o3 Deep Research | https://platform.openai.com/ |
| `GOOGLE_API_KEY` | Google | Gemini Deep Research | https://aistudio.google.com/ |

### What NOT To Do

- Do NOT store API keys in `.env` files
- Do NOT hardcode API keys in scripts or configuration
- Do NOT commit API keys to version control
- Do NOT create `.env` files with actual key values

### Non-Sensitive Configuration

The following settings ARE safe to put in `.env` files (they are not secrets):

```bash
# Model overrides (non-sensitive)
ANTHROPIC_MODEL=claude-opus-4-5-20251101
OPENAI_MODEL=o3-deep-research-2025-06-26
GEMINI_AGENT=deep-research-pro-preview-12-2025

# Feature flags (non-sensitive)
CHECK_MODEL_UPDATES=true
AUTO_UPGRADE_MODELS=false
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Keys not in environment after `/unlock` | Verify secrets exist in Bitwarden vault: `bws secret list` |
| `bws` command not found | Install from: https://github.com/bitwarden/sdk-sm/releases |
| Auth token expired | Check the `TROY` environment variable is set with a valid machine access token |
| Partial keys (some providers only) | Use `--sources` flag to limit to available providers |
