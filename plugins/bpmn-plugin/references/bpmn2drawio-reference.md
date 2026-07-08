# bpmn2drawio Reference

**Purpose:** CLI option reference, theme/branding configuration, the Python API, and the supported-BPMN-element catalog for the `bpmn2drawio` conversion tool. Kept out of the skill file to hold it to the progressive-disclosure line budget — the six-step conversion workflow (dependency checks, layout decision, running the conversion, validating output) lives inline in the skill and is fully specified without opening this file. Use this file for CLI flag lookup, theme/YAML branding, programmatic (Python) usage, and BPMN element/coverage lookups.

**Consumer:** `skills/bpmn-to-drawio/SKILL.md` — Steps 1-6 point here for CLI Reference, Themes, Python API, and Supported BPMN Elements sections.

---

## CLI Reference

### Command Syntax

```text
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
