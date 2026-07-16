# ADR-0003: Bitwarden Secrets Management

**Date:** 2026-02-16
**Status:** Accepted

## Context

Multiple plugins and tools in this marketplace require API keys and tokens at runtime -- Anthropic API keys for Claude interactions, OpenAI keys for research orchestration, Google API keys for Gemini access, and potentially others as the plugin ecosystem grows. These credentials must be available in the shell environment when commands and skills execute.

The conventional approach in development projects is to store secrets in `.env` files at the project root and load them into the environment at startup. This is convenient but carries well-known risks: `.env` files are frequently committed to version control by accident (even with `.gitignore` entries), they persist credentials in plaintext on disk, they are copied between machines via insecure channels, and they accumulate stale credentials over time. For a marketplace repository that is public on GitHub, any accidental commit of a `.env` file exposes credentials to the entire internet with no practical way to revoke before automated scrapers harvest them.

A more robust approach is needed that separates credential storage from the codebase entirely, provides encrypted at-rest storage, supports programmatic retrieval, and works within the constraints of Claude Code's plugin execution model (where tools run as shell commands, not as managed services with injected secrets).

## Decision

All API keys, tokens, and sensitive credentials are stored in Bitwarden vault and retrieved at runtime via the `bws` CLI (Bitwarden Secrets Manager). The convention is:

- **Storage:** Secrets are stored as structured fields in Bitwarden with the naming pattern `dev/<project-name>/<secret-type>` (e.g., `dev/slide-generator/api-keys`)
- **Retrieval:** The `/unlock` skill handles Bitwarden authentication and loads secrets into the current shell session's environment variables
- **`.env` files:** May exist but contain only non-sensitive configuration (model names, feature flags, URLs) and placeholder comments pointing to Bitwarden for actual credentials

The marketplace provides helper scripts at `~/.claude/scripts/` for common operations: `get-secrets.sh`, `store-secrets.sh`, and `list-secrets.sh`.

## Consequences

### Positive
- Credentials never exist in plaintext files within the repository, eliminating the primary vector for accidental exposure
- Bitwarden provides encrypted at-rest storage and access control, meeting enterprise security expectations
- The `/unlock` skill integrates secret loading into the Claude Code workflow, making it a natural first step rather than an afterthought
- Credentials are centrally managed: rotating a key in Bitwarden immediately takes effect across all projects that reference it
- Works across machines without copying credential files -- any authenticated Bitwarden client can retrieve the secrets

### Negative
- Adds a mandatory setup step: users must have Bitwarden CLI installed, a Bitwarden account configured, and secrets pre-populated before plugins that need API keys will work
- Introduces a runtime dependency on Bitwarden's service availability -- if Bitwarden is unreachable, secrets cannot be retrieved (though they persist in the environment once loaded within a session)
- The `bws` CLI must be installed separately (it is not a standard system tool), adding friction to the initial setup experience
- Debugging credential issues is harder: "API key not found" could mean the Bitwarden item is missing, the field name is wrong, the vault is locked, or the `bws` CLI is not installed
- Shell environment variables are visible to any process in the session, so secrets are only protected at rest, not in use

### Neutral
- `.env` files still serve a purpose as documentation: they show which environment variables are expected and where to find the actual values
- This pattern is specific to the repository owner's workflow; other marketplace users who fork or install plugins would need to adapt the secret retrieval mechanism to their own vault or secret manager
- The Bitwarden access token itself (`TROY` environment variable) must be stored as a machine-level environment variable, creating a bootstrap dependency

## Amendment: Sanctioned exception -- standalone-tool local runtime

**Date:** 2026-07-16

The `visual-explainer` tool (`plugins/personal-plugin/tools/visual-explainer/`) is a bundled, distributable Python CLI that end users run standalone -- it is not exclusively part of the repository owner's own Bitwarden-provisioned workflow. Requiring the `bws` CLI and a pre-populated Bitwarden vault before a first-run user can generate a single image is impractical: the tool's own setup wizard exists precisely to lower that first-run barrier, and forcing an external secrets manager onto every downstream installer contradicts that goal.

To reconcile this with the Decision above, this ADR is amended to sanction a narrow exception:

- The `visual-explainer` API key setup wizard (`api_setup.py::create_env_file`) MAY write `GOOGLE_API_KEY` and `ANTHROPIC_API_KEY` to a local `.env` file at runtime, as a first-run convenience.
- The written file MUST be mode `0600` (owner read/write only) on platforms that support POSIX permissions; `chmod` failures on platforms where it is unsupported or a no-op (e.g. some Windows filesystems) are tolerated and do not block key storage.
- The file MUST remain gitignored (`_update_gitignore` continues to run on every write) and MUST never be committed.
- The wizard MUST print an explicit warning at write time that keys are stored locally **unencrypted** and that Bitwarden is the preferred store per this ADR.

This exception is intentionally narrow: it applies only to this tool's local runtime `.env`, not to the Anthropic/OpenAI/Google credentials used by the marketplace's own plugins and skills, which continue to follow the Decision above (Bitwarden + `bws` + `/unlock`). The exception does not change this ADR's Status -- Bitwarden remains the accepted, preferred mechanism everywhere it is practical to require it.
