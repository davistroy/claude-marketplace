---
name: bpmn-to-drawio
description: >
  Convert BPMN 2.0 XML files into Draw.io native format (.drawio) using the
  bpmn2drawio Python tool. Renders properly in Draw.io Desktop or web applications.
  Use this skill when a user wants to visualize a BPMN process in Draw.io, convert
  BPMN to editable diagrams, or create Draw.io files from process definitions.
  Triggers on: "convert BPMN to Draw.io", "create drawio from BPMN", "visualize
  BPMN in Draw.io".
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

The tool is bundled at `../tools/bpmn2drawio/` relative to this skill file:

```bash
# Determine the plugin directory (adjust path as needed)
PLUGIN_DIR="/path/to/plugins/bpmn-plugin"
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

```
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

### Command Syntax

```
bpmn2drawio <input.bpmn> <output.drawio> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input` | Yes | Input BPMN 2.0 XML file |
| `output` | Yes | Output Draw.io file path |

### Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--theme` | `default`, `blueprint`, `monochrome`, `high_contrast` | `default` | Color theme |
| `--config` | file path | — | Custom brand configuration YAML |
| `--layout` | `graphviz`, `preserve` | `graphviz` | Layout algorithm |
| `--direction` | `LR`, `TB`, `RL`, `BT` | `LR` | Flow direction |
| `--no-grid` | flag | — | Disable grid in output |
| `--page-size` | `A4`, `letter`, `auto` | `auto` | Page size |
| `-v`, `--verbose` | flag | — | Verbose output |
| `--version` | flag | — | Show version |

### Direction Options

| Value | Description | Best For |
|-------|-------------|----------|
| `LR` | Left to Right | Standard process flows |
| `TB` | Top to Bottom | Hierarchical processes |
| `RL` | Right to Left | RTL language support |
| `BT` | Bottom to Top | Reverse hierarchy |

---

## Themes

### Built-in Themes

| Theme | Description | Use Case |
|-------|-------------|----------|
| `default` | Standard BPMN colors (green start, red end, blue tasks, yellow gateways) | General use |
| `blueprint` | Professional blue monochrome | Technical documentation |
| `monochrome` | Black, white, gray | Printing, high contrast |
| `high_contrast` | Accessibility-focused | Vision accessibility |

### Custom Theme Configuration

Create a YAML configuration file for brand colors:

```yaml
# brand-config.yaml
colors:
  # Events
  start_event_fill: "#c8e6c9"
  start_event_stroke: "#2e7d32"
  end_event_fill: "#ffcdd2"
  end_event_stroke: "#c62828"

  # Tasks
  task_fill: "#e3f2fd"
  task_stroke: "#1565c0"
  user_task_fill: "#fff8e1"
  user_task_stroke: "#ff8f00"
  service_task_fill: "#f3e5f5"
  service_task_stroke: "#7b1fa2"

  # Gateways
  gateway_fill: "#fff9c4"
  gateway_stroke: "#f9a825"

  # Swimlanes
  pool_fill: "#fafafa"
  pool_stroke: "#616161"
  lane_fill: "#ffffff"
  lane_stroke: "#9e9e9e"

# Lane colors by function (pattern matching)
lane_colors:
  sales:
    patterns: ["sales", "commercial"]
    fill: "#dae8fc"
    stroke: "#6c8ebf"
  finance:
    patterns: ["finance", "billing"]
    fill: "#ffe6cc"
    stroke: "#d79b00"
  legal:
    patterns: ["legal", "compliance"]
    fill: "#d5e8d4"
    stroke: "#82b366"
```

Use with:
```bash
bpmn2drawio input.bpmn output.drawio --config=brand-config.yaml
```

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

For programmatic use within scripts:

```python
from bpmn2drawio import Converter, parse_bpmn, validate_model

# Simple conversion
converter = Converter()
result = converter.convert("process.bpmn", "process.drawio")
print(f"Converted {result.element_count} elements, {result.flow_count} flows")

# With options
converter = Converter(
    theme="blueprint",
    direction="TB",
    layout="graphviz"
)
result = converter.convert("input.bpmn", "output.drawio")

# Check for warnings
if result.warnings:
    for warning in result.warnings:
        print(f"Warning: {warning}")

# Convert BPMN string to Draw.io string
drawio_xml = converter.convert_string(bpmn_xml_string)

# Parse and inspect BPMN before conversion
model = parse_bpmn("process.bpmn")
print(f"Process: {model.process_name}")
print(f"Elements: {len(model.elements)}")
print(f"Has DI coordinates: {model.has_di_coordinates}")

# Validate model
warnings = validate_model(model)
for warning in warnings:
    print(f"[{warning.level}] {warning.element_id}: {warning.message}")
```

---

## Supported BPMN Elements

### Events

| Type | Variants |
|------|----------|
| Start Event | None, Message, Timer, Signal, Conditional |
| End Event | None, Message, Error, Terminate, Signal |
| Intermediate Catch | Message, Timer, Signal, Link, Conditional |
| Intermediate Throw | Message, Signal, Escalation, Compensation, Link |
| Boundary | Timer, Error, Message, Escalation (interrupting/non-interrupting) |

### Activities

| Type | Icon | Description |
|------|------|-------------|
| Task | — | Generic task |
| User Task | Person | Human interaction required |
| Service Task | Gear | Automated service call |
| Script Task | Scroll | Script execution |
| Send Task | Envelope | Send message |
| Receive Task | Envelope | Receive message |
| Business Rule Task | Table | Business rule evaluation |
| Manual Task | Hand | Manual work |
| Call Activity | Bold border | Reusable process call |
| Sub-Process | + marker | Embedded sub-process |

### Gateways

| Type | Symbol | Description |
|------|--------|-------------|
| Exclusive (XOR) | X | One path based on condition |
| Parallel (AND) | + | All paths simultaneously |
| Inclusive (OR) | O | One or more paths |
| Event-Based | Pentagon | Path based on event |
| Complex | * | Complex merge conditions |

### Flows

| Type | Style | Description |
|------|-------|-------------|
| Sequence Flow | Solid arrow | Normal flow |
| Default Flow | Solid + slash | Default path from gateway |
| Conditional Flow | Diamond start | Condition-based flow |
| Message Flow | Dashed + circle | Between pools |
| Association | Dotted | Data/annotation links |

### Containers

- **Pools** - Horizontal or vertical participant containers
- **Lanes** - Subdivisions within pools for roles/departments

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

```
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

## References

- **Bundled Tool**: `../tools/bpmn2drawio/` (source code included in this plugin)
- **Original Repository**: https://github.com/davistroy/bpmn/tree/main/bpmn2drawio
- **Conversion Standard**: `../references/BPMN-to-DrawIO-Conversion-Standard.md`
- **Element Styles**: `../templates/element-styles.yaml`
- **Draw.io Skeleton**: `../templates/drawio-skeleton.xml`
- **Example Files**: `../examples/`
