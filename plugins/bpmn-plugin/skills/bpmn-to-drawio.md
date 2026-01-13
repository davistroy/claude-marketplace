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

## Quick Start

```bash
# Basic conversion
bpmn2drawio input.bpmn output.drawio

# With theme
bpmn2drawio input.bpmn output.drawio --theme=blueprint

# Top-to-bottom layout
bpmn2drawio input.bpmn output.drawio --direction=TB
```

---

## Conversion Workflow

### Step 1: Check Tool Availability

First, check if `bpmn2drawio` is installed:

```bash
bpmn2drawio --version
```

If not installed, proceed to [Installation](#installation).

### Step 2: Analyze Source BPMN

Before conversion, briefly analyze the BPMN file to determine appropriate options:

```bash
# Check file structure
head -50 input.bpmn
```

Look for:
- `<bpmndi:BPMNDiagram>` - Has DI coordinates (use `--layout=preserve`)
- `<bpmn:participant>` - Multiple pools (complex diagram)
- `<bpmn:lane>` - Swimlanes present

### Step 3: Run Conversion

**Basic conversion (auto-layout):**
```bash
bpmn2drawio input.bpmn output.drawio
```

**Preserve existing layout (if BPMN has DI coordinates):**
```bash
bpmn2drawio input.bpmn output.drawio --layout=preserve
```

**With specific theme:**
```bash
bpmn2drawio input.bpmn output.drawio --theme=blueprint
```

**Verbose output for debugging:**
```bash
bpmn2drawio input.bpmn output.drawio --verbose
```

### Step 4: Validate Output

After conversion, verify the output:

```bash
# Check file was created
ls -la output.drawio

# Verify XML structure
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

## Installation

### Prerequisites

Install Graphviz (required for automatic layout):

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install graphviz libgraphviz-dev
```

**macOS:**
```bash
brew install graphviz
```

**Windows:**
```bash
choco install graphviz
```

### Install bpmn2drawio

The `bpmn2drawio` tool is bundled with this plugin. Install from the plugin's tools directory:

```bash
# Navigate to the plugin's tools directory and install
pip install /path/to/claude-marketplace/plugins/bpmn-plugin/tools/bpmn2drawio

# Or install in editable mode for development
pip install -e /path/to/claude-marketplace/plugins/bpmn-plugin/tools/bpmn2drawio
```

**Alternative: Install from PyPI (if published)**
```bash
pip install bpmn2drawio
```

### Verify Installation

```bash
bpmn2drawio --version
```

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
| `command not found: bpmn2drawio` | Tool not installed | See [Installation](#installation) |
| `pygraphviz` import error | Graphviz not installed | Install Graphviz system package |
| Empty output file | Invalid BPMN input | Check BPMN file validity |
| Overlapping elements | No DI coordinates | Use `--layout=graphviz` (default) |
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
