# ADR-0004: Plugin Encapsulation

**Date:** 2026-02-16
**Status:** Accepted

## Context

This marketplace hosts multiple plugins within a single GitHub repository (`davistroy/claude-marketplace`). Currently there are two -- `personal-plugin` (productivity commands and skills) and `bpmn-plugin` (BPMN workflow tools) -- but the architecture must support additional plugins as the collection grows. A key design question is how to handle the boundaries between plugins: should they share resources (common commands, shared tool libraries, unified skill namespaces), or should each plugin be fully self-contained?

Shared resources reduce duplication. For example, both plugins could reference a single `common-patterns.md` file, share a Python utility library, or inherit commands from a base plugin. However, sharing creates coupling: changing a shared resource requires testing every plugin that depends on it, versioning becomes entangled (a change to shared code forces version bumps across multiple plugins), and the installation experience becomes fragile (installing plugin B might silently require resources from plugin A).

Claude Code's marketplace system reinforces this boundary: each plugin is installed independently via `/plugin install <name>@<marketplace>`, and there is no mechanism for one plugin to declare or resolve runtime dependencies on files from another plugin. The `CLAUDE_PLUGIN_ROOT` variable points to the individual plugin's directory, not the marketplace root, so cross-plugin file references would require hardcoded paths that break under different installation configurations.

## Decision

Each plugin is fully self-contained within its directory under `plugins/<plugin-name>/`. This means:

- **Commands and skills** are scoped to the plugin that defines them, with namespace prefixing (`/personal-plugin:review-arch`) available for disambiguation
- **References and templates** are duplicated per plugin if both need them, rather than shared from a common location
- **Python tools** live within the plugin that uses them at `tools/<tool-name>/`
- **Versioning** is independent: each plugin has its own version in `plugin.json` and `marketplace.json`, bumped with `/bump-version <plugin-name> <level>`
- **A `help` skill** is required in every plugin, documenting only that plugin's own commands and skills

The marketplace-level `marketplace.json` serves as a registry that points to each plugin's location but does not define shared behavior.

## Consequences

### Positive
- Plugins can be installed, updated, and removed independently without affecting other plugins
- A breaking change in one plugin (restructured commands, renamed skills, updated tool dependencies) has zero impact on other plugins
- Each plugin's directory is a complete unit that can be understood, tested, and validated in isolation
- Version numbers are meaningful per plugin: a version bump in `bpmn-plugin` reflects actual changes to BPMN functionality, not unrelated changes elsewhere
- Namespace collision detection (`/validate-plugin --all`) catches naming conflicts early, before they confuse users at runtime
- Contributors can work on a single plugin without needing to understand the entire marketplace

### Negative
- Duplication is inevitable: if two plugins need the same reference document, utility function, or pattern documentation, each must carry its own copy
- Keeping duplicated content in sync across plugins is a manual process with no built-in enforcement -- divergence is likely over time
- The repository grows larger than it would with shared resources, though the marginal cost is small for documentation and reference files
- Cross-plugin workflows (e.g., a command in `personal-plugin` that generates BPMN output for `bpmn-plugin` to process) must operate through file system conventions rather than direct integration

### Neutral
- Plugin dependencies can be declared in `plugin.json` (e.g., `"personal-plugin": ">=2.0.0"`), but these are informational only -- Claude Code does not enforce or auto-install them
- The two-tier versioning strategy (marketplace version vs. plugin versions) is a direct consequence of this encapsulation: the marketplace version tracks infrastructure changes, while plugin versions track their own content independently
- If a future need arises for genuinely shared libraries, this decision could be revisited by introducing a `shared/` directory at the marketplace root, though this would require changes to how `CLAUDE_PLUGIN_ROOT` is resolved
