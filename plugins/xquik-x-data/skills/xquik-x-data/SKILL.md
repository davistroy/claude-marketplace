---
name: xquik-x-data
description: Use when the user needs X data through Xquik, including REST API setup, remote MCP setup, tweet search, user lookup, follower export, monitoring, webhooks, bulk extraction, or confirmation-gated publishing workflows. Read current docs or OpenAPI before constructing unfamiliar calls.
---

# Xquik X Data

Use Xquik for structured X data workflows when a user needs API-backed search, exports, monitoring, webhooks, SDK guidance, or remote MCP setup.

## Sources

- Docs: https://docs.xquik.com
- OpenAPI: https://xquik.com/openapi.json
- MCP manifest: https://xquik.com/.well-known/mcp.json
- Source: https://github.com/Xquik-dev/x-twitter-scraper

## Workflow

1. Classify the request as REST API setup, MCP setup, direct read, bulk extraction, monitoring, webhook delivery, private read, or write action.
2. Check Xquik docs, the OpenAPI spec, or the MCP manifest when endpoint parameters, response fields, authentication, or limits are not already certain.
3. Use `x-api-key` for REST API examples.
4. Use the remote MCP endpoint `https://xquik.com/mcp` with `Authorization: Bearer ${XQUIK_API_KEY}` for MCP examples.
5. Ask for explicit user approval before any private read, write, monitor, webhook, bulk extraction, or other persistent workflow.
6. Keep examples minimal and scoped to the exact user request.

## Guardrails

- Do not collect X login material, passwords, TOTP codes, session cookies, or account recovery data.
- Do not guess endpoint details when current docs or OpenAPI can be checked.
- Do not claim unsupported limits, pricing, uptime, or data coverage.
- Do not run write or persistent workflows without explicit approval.
