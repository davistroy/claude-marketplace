---
name: bpmn-to-drawio
description: >
  Convert BPMN 2.0 XML files into Draw.io native format (.drawio) using the
  bpmn2drawio Python tool. Renders properly in Draw.io Desktop or web applications.
  Use this skill when a user wants to visualize a BPMN process in Draw.io, convert
  BPMN to editable diagrams, or create Draw.io files from process definitions.
  Triggers on: "convert BPMN to Draw.io", "create drawio from BPMN", "visualize
  BPMN in Draw.io". Do NOT use for creating new BPMN from a process description or
  markdown doc — use bpmn-generator for that.
argument-hint: "<bpmn-file-path>"
allowed-tools: Read, Write, Bash, Glob, Grep
---

# BPMN to Draw.io Converter

## Overview

This skill converts BPMN 2.0 XML files into Draw.io native format (.drawio) using the `bpmn2drawio` Python tool. The tool provides:

- Automatic Graphviz-based layout for files without DI coordinates
- Four built-in themes with custom YAML branding support
- Visual markers for gateways (X, +, O) and task/event icons
- Complete swimlane support with proper hierarchy
- Model validation with error recovery

## Conversion Workflow

Follow these steps in order. The workflow automatically handles dependency installation.

### Step 1: Set Up Tool Path

The tool is bundled in the plugin's `tools/bpmn2drawio/` directory. Use `${CLAUDE_PLUGIN_ROOT}` for the plugin path (auto-set for marketplace-installed plugins):

```bash
# Use CLAUDE_PLUGIN_ROOT (auto-set for marketplace-installed plugins)
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-/path/to/plugins/bpmn-plugin}"
TOOL_SRC="$PLUGIN_DIR/tools/bpmn2drawio/src"
```

### Step 2: Check and Install Python Dependencies

Check for required Python packages and install any that are missing:

```bash
# Check which packages are missing
python -c "import lxml" 2>/dev/null || echo "lxml: MISSING"
python -c "import networkx" 2>/dev/null || echo "networkx: MISSING"
python -c "import yaml" 2>/dev/null || echo "pyyaml: MISSING"
python -c "import pygraphviz" 2>/dev/null || echo "pygraphviz: MISSING (requires Graphviz)"
```

**If any packages are missing (except pygraphviz), ask the user:**
> "The following Python packages are missing: [list]. Install them now with `pip install [packages]`?"

If user approves:
```bash
pip install lxml networkx pyyaml
```

**Note:** `pygraphviz` is handled separately in Step 3 because it requires Graphviz.

### Step 3: Check Graphviz and pygraphviz

**CRITICAL:** Graphviz is required for automatic layout. Check BEFORE any processing:

```bash
# Check for Graphviz
dot -V 2>/dev/null && echo "Graphviz: OK" || echo "Graphviz: MISSING"
```

**If Graphviz is missing**, display this standardized error:

```text
Error: Required dependency 'graphviz' not found

/bpmn-to-drawio requires Graphviz for automatic diagram layout.

Installation instructions:
  Windows: choco install graphviz
  macOS:   brew install graphviz
  Linux:   sudo apt install graphviz libgraphviz-dev

After installing Graphviz, also install the Python bindings:
  pip install pygraphviz

After installing, run the command again.

Note: If your BPMN file already has layout coordinates, you can skip
Graphviz and use: /bpmn-to-drawio input.bpmn output.drawio --layout=preserve
```

**Important Decision Point:**

Before showing the error, check if the BPMN file has DI coordinates (Step 4):
- If `HAS_DI=true`: Offer the `--layout=preserve` alternative
- If `HAS_DI=false`: Graphviz is required, display the full error

**If user wants to install Graphviz**, guide them through:

```bash
# Detect OS and install
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update && sudo apt-get install -y graphviz libgraphviz-dev
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew install graphviz
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
    choco install graphviz -y
fi
```

**After Graphviz is installed, install pygraphviz:**
```bash
pip install pygraphviz
```

### Step 4: Analyze Source BPMN

Check if the BPMN file has existing layout coordinates:

```bash
# Check for DI coordinates
grep -q "bpmndi:BPMNDiagram" input.bpmn && echo "HAS_DI=true" || echo "HAS_DI=false"
```

Also check for complexity:
- `<bpmn:participant>` - Multiple pools
- `<bpmn:lane>` - Swimlanes present

**Layout decision:**
- If `HAS_DI=true`: Can use `--layout=preserve` (Graphviz optional)
- If `HAS_DI=false`: Must use `--layout=graphviz` (Graphviz required)

### Step 5: Run Conversion

**With Graphviz available (auto-layout):**
```bash
PYTHONPATH="$TOOL_SRC" python -m bpmn2drawio input.bpmn output.drawio
```

**Without Graphviz (preserve existing layout):**
```bash
PYTHONPATH="$TOOL_SRC" python -m bpmn2drawio input.bpmn output.drawio --layout=preserve
```

**With theme:**
```bash
PYTHONPATH="$TOOL_SRC" python -m bpmn2drawio input.bpmn output.drawio --theme=blueprint
```

**Verbose output for debugging:**
```bash
PYTHONPATH="$TOOL_SRC" python -m bpmn2drawio input.bpmn output.drawio --verbose
```

### Step 6: Validate Output

Verify the conversion succeeded:

```bash
# Check file was created and has content
ls -la output.drawio
head -30 output.drawio
```

---

## CLI Reference

Full command syntax, arguments, `--theme`/`--layout`/`--direction`/etc. options, and direction values — see `../references/bpmn2drawio-reference.md#cli-reference`.

---

## Themes

Built-in theme options (`default`, `blueprint`, `monochrome`, `high_contrast`) and custom YAML brand configuration (event/task/gateway/swimlane colors, lane-color pattern matching) — see `../references/bpmn2drawio-reference.md#themes`.

---

## Dependencies

Dependencies are checked and installed automatically during the conversion workflow (Steps 2-3).

### Python Packages
- `lxml` - XML parsing
- `networkx` - Graph algorithms
- `pyyaml` - YAML configuration parsing
- `pygraphviz` - Graphviz Python bindings (requires Graphviz)

### System Dependencies
- **Graphviz** - Required for automatic layout generation
  - Not needed if BPMN file already has DI coordinates (use `--layout=preserve`)

### Manual Installation (if needed)

**Python packages:**
```bash
pip install lxml networkx pyyaml pygraphviz
```

**Graphviz:**
- Ubuntu/Debian: `sudo apt-get install graphviz libgraphviz-dev`
- macOS: `brew install graphviz`
- Windows: `choco install graphviz`

---

## Python API

For programmatic use within scripts (`Converter`, `parse_bpmn`, `validate_model`) — see `../references/bpmn2drawio-reference.md#python-api`.

---

## Supported BPMN Elements

Full tables of supported Events, Activities, Gateways, Flows, and Containers (pools/lanes) — see `../references/bpmn2drawio-reference.md#supported-bpmn-elements`.

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: bpmn2drawio` | PYTHONPATH not set | Set `PYTHONPATH="$TOOL_SRC"` before running |
| `ModuleNotFoundError: lxml` | Missing dependency | Run `pip install lxml` |
| `ModuleNotFoundError: pygraphviz` | Graphviz not installed | Install Graphviz first, then `pip install pygraphviz` |
| Empty output file | Invalid BPMN input | Check BPMN file validity |
| Overlapping elements | No DI coordinates | Use `--layout=graphviz` (requires Graphviz) |
| Wrong flow direction | Default is LR | Use `--direction=TB` for vertical |

### Validation Errors

If the tool reports validation warnings:

```bash
# Run with verbose to see details
bpmn2drawio input.bpmn output.drawio --verbose
```

Common validation issues:
- **Orphan elements**: Tasks not connected to flows
- **Missing end events**: Process has no termination
- **Dangling sequence flows**: Flow references non-existent element

The tool attempts recovery for most issues but warnings indicate potential problems.

### Manual Inspection

If output doesn't render correctly in Draw.io:

1. Open the .drawio file in a text editor
2. Check for `<mxCell>` elements with valid geometry
3. Verify cross-lane edges have `parent="1"`
4. Check that all referenced IDs exist

---

## Output Format

### Conversion Summary

After successful conversion, report:

```markdown
## Draw.io Conversion Summary

**Source File:** input.bpmn
**Output File:** output.drawio
**Theme:** default
**Layout:** graphviz
**Direction:** LR

### Elements Converted:
- Pools: X
- Lanes: X
- Tasks: X
- Gateways: X
- Events: X
- Sequence Flows: X
- Message Flows: X

### Validation:
✓ All elements converted successfully
✓ No orphan elements detected
✓ All flows connected

### Next Steps:
- Open output.drawio in Draw.io Desktop or diagrams.net
- Verify visual layout matches expectations
- Adjust element positions if needed
```

---

## Fallback: Manual Conversion

If the `bpmn2drawio` tool is unavailable and cannot be installed, fall back to manual conversion using the reference documents:

1. **Conversion Standard**: `../references/BPMN-to-DrawIO-Conversion-Standard.md`
2. **Element Styles**: `../templates/element-styles.yaml`
3. **Draw.io Skeleton**: `../templates/drawio-skeleton.xml`

### Manual Conversion Steps

1. Parse BPMN XML to extract elements, flows, and DI coordinates
2. Build coordinate registry for all elements
3. Generate Draw.io XML structure
4. Create pool and lane hierarchy
5. Place elements within lanes
6. Generate edges (intra-lane with relative coords, cross-lane with absolute)
7. Write output file

**Critical Rules for Manual Conversion:**
- Cross-lane edges MUST have `parent="1"` with absolute `mxPoint` coordinates
- Lane positions are relative to their parent pool
- Element positions are relative to their parent lane
- Always calculate absolute coordinates for cross-lane edge routing

---

## Performance

| BPMN Size | Elements | Expected Duration | Notes |
|-----------|----------|-------------------|-------|
| Small | 5-15 | Under 10 seconds | Simple processes, single pool |
| Medium | 15-50 | 10-30 seconds | Multiple lanes, moderate gateways |
| Large | 50-100 | 30-90 seconds | Multiple pools, complex routing |
| Very large | 100+ | 1-3 minutes | Graphviz layout dominates at scale |

Duration is dominated by Graphviz layout computation for files without DI coordinates. Using `--layout=preserve` (when DI coordinates exist) reduces conversion to under 5 seconds regardless of size. Dependency installation (first run only) may add 30-60 seconds.

## References

- **Bundled Tool**: `../tools/bpmn2drawio/` (source code included in this plugin)
- **Original Repository**: https://github.com/davistroy/bpmn/tree/main/bpmn2drawio
- **Conversion Standard**: `../references/BPMN-to-DrawIO-Conversion-Standard.md`
- **Element Styles**: `../templates/element-styles.yaml`
- **Draw.io Skeleton**: `../templates/drawio-skeleton.xml`
- **Example Files**: `../examples/`
