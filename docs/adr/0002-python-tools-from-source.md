# ADR-0002: Python Tools Run From Source

**Date:** 2026-02-16
**Status:** Accepted

## Context

Several plugins in this marketplace bundle Python tools that provide functionality beyond what Claude Code can do natively -- generating Word documents, orchestrating multi-LLM research queries, converting BPMN XML to Draw.io format, and producing AI-generated visual explanations. These tools need to be distributed alongside the plugin and executable at runtime.

The natural approach would be to declare tools in `plugin.json` so Claude Code could manage their lifecycle (discovery, dependency installation, execution). However, Claude Code's plugin schema does not support a `tools` field in `plugin.json`. Adding one causes an "Unrecognized key: tools" error that prevents the entire plugin from loading. This is not a bug to be worked around -- it reflects a deliberate constraint in the plugin system's current design.

An alternative would be to publish each Python tool as a standalone pip package and require users to `pip install` them before using the plugin. This would add friction to the installation process, require maintaining package releases on PyPI (or a private index), and create version synchronization problems between the plugin and its tools. It would also mean the tool source code lives outside the plugin directory, breaking the self-contained nature of plugins.

## Decision

All Python tools are bundled within the plugin directory structure at `plugins/<plugin-name>/tools/<tool-name>/` and run directly from source using `PYTHONPATH` manipulation. The invocation pattern is:

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/plugin-name}"
TOOL_SRC="$PLUGIN_DIR/tools/tool-name/src"
PYTHONPATH="$TOOL_SRC" python -m tool_module <arguments>
```

Each tool follows standard Python project layout with `pyproject.toml` for metadata and a `src/<module>/` structure with `__main__.py` for entry points. Dependencies are checked at runtime and installed via pip on first use (with user confirmation).

## Consequences

### Positive
- Plugins remain fully self-contained: all code (commands, skills, tools) lives under one directory tree
- No PyPI publishing or package release workflow needed
- Tool source is always in sync with the plugin version that ships it -- no version mismatch possible
- Users can inspect and modify tool source directly without needing to locate installed packages
- Works immediately after plugin installation with no additional setup beyond Python itself

### Negative
- `PYTHONPATH` manipulation is fragile: if the path is wrong, errors can be confusing (module not found, wrong version loaded)
- Each command or skill that invokes a tool must include the boilerplate for setting `PYTHONPATH` and resolving the plugin root directory
- Runtime dependency checking adds latency on first invocation and requires user interaction to approve pip installs
- No dependency isolation: tools share the user's global Python environment (or active virtualenv), which can cause conflicts with other packages
- Tools are not importable from outside the plugin without manually setting up `PYTHONPATH`, making reuse across plugins awkward

### Neutral
- The `pyproject.toml` in each tool directory serves as documentation of dependencies even though it is not used for installation
- This pattern requires Python 3.10+ to be available on the user's system, which is a reasonable baseline for Claude Code users
- If Claude Code's plugin schema later adds native tool support, migration would involve moving the invocation logic from command/skill markdown into plugin.json configuration
