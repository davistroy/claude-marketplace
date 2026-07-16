# Validate Plugin — Additional Examples

Reference for `/validate-plugin`. Loaded on demand. Holds illustrative content that doesn't affect check behavior: the exact usage/error text blocks, the required directory-structure diagram, a sample namespace registry, and the remote-fetch fallback message.

Sample PASS/FAIL/WARN report output for each validation phase already lives in `references/validation-output-examples.md` — this file only covers the pieces not already there. The command file (`commands/validate-plugin.md`) holds the authoritative check logic; nothing here changes behavior.

## Usage & Error Messages

### Missing Arguments

Displayed when required arguments are missing:

```text
Usage: /validate-plugin <plugin-name> [--all] [--fix] [--verbose] [--strict] [--report] [--scorecard] [--check-updates]

Examples:
  /validate-plugin personal-plugin          # Validate single plugin
  /validate-plugin --all                    # Validate all plugins
  /validate-plugin bpmn-plugin --verbose    # Detailed output
  /validate-plugin personal-plugin --fix    # Auto-fix simple issues
  /validate-plugin --all --strict           # Fail on any violation
  /validate-plugin --all --report           # Generate compliance report
  /validate-plugin --all --scorecard        # Generate maturity scorecard
  /validate-plugin --all --check-updates    # Include remote version check

Available plugins:
  [Scan the plugins/ directory for subdirectories containing .claude-plugin/plugin.json.
   List each discovered plugin name.]
```

### Plugin Not Found

Displayed when `plugin-name` doesn't match a discovered plugin and `--all` was not specified:

```text
Error: Plugin '[name]' not found.

Available plugins:
  [Scan the plugins/ directory for subdirectories containing .claude-plugin/plugin.json.
   List each discovered plugin name.]

Use --all to validate all plugins.
```

## Required Directory Structure

The layout Phase 1.1 checks for:

```text
plugins/[plugin-name]/
  .claude-plugin/
    plugin.json              # REQUIRED
  commands/                  # At least one of commands/ or skills/
    *.md                     # Flat structure: filename becomes command name
  skills/
    [skill-name]/            # REQUIRED: Nested directory structure
      SKILL.md               # REQUIRED: Must be exactly SKILL.md (uppercase)
```

## Namespace Registry Example

What Phase 5.1's per-plugin command/skill registry looks like once built:

```text
Plugin: personal-plugin
  Commands: [dynamically discovered from commands/*.md]
  Skills: [dynamically discovered from skills/*/SKILL.md]

Plugin: bpmn-plugin
  Commands: (none)
  Skills: bpmn-generator, bpmn-to-drawio, help
```

## Remote Fetch Fallback

Displayed by Phase 9.5.2 when the `gh` command fails (not installed, not authenticated, no network):

```text
Note: Could not fetch remote versions (gh CLI unavailable or network error).
Falling back to local version consistency report.

To enable remote checks:
  1. Install gh CLI: https://cli.github.com
  2. Authenticate: gh auth login
```

After this message, Phase 9.5.3 proceeds with a local-only comparison (local plugin.json against local marketplace.json only — no remote data).
