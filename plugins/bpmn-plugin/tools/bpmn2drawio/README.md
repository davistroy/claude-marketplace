# bpmn2drawio

[![Test Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)](htmlcov/index.html)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library and CLI tool for converting BPMN 2.0 XML files to Draw.io diagram format.

## Features

- **Full BPMN 2.0 Support**: All element types including events, tasks, gateways, pools, lanes
- **Automatic Layout**: Graphviz-based layout engine for BPMN files without DI coordinates
- **Visual Markers**: Gateway symbols (X, +, O), task icons, event icons
- **Theming System**: 4 built-in themes with YAML brand configuration support
- **Swimlanes**: Full pool and lane support with proper hierarchy
- **Flow Types**: Sequence, message, association, conditional, and default flows
- **Validation**: Model validation with graceful error recovery

## Installation

### Prerequisites

Install Graphviz (required for automatic layout):

```bash
# Ubuntu/Debian
sudo apt-get install graphviz libgraphviz-dev

# macOS
brew install graphviz

# Windows
choco install graphviz
```

### Install Package

```bash
cd bpmn2drawio
pip install -e .
```

## Usage

### Command Line

```bash
# Basic conversion
bpmn2drawio input.bpmn output.drawio

# With theme
bpmn2drawio input.bpmn output.drawio --theme=blueprint

# Top-to-bottom layout direction
bpmn2drawio input.bpmn output.drawio --direction=TB

# Verbose output
bpmn2drawio input.bpmn output.drawio --verbose

# All options
bpmn2drawio input.bpmn output.drawio \
    --theme=high_contrast \
    --direction=LR \
    --layout=graphviz \
    --verbose
```

### Python Library

```python
from bpmn2drawio import Converter, parse_bpmn

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

# Convert string
drawio_xml = converter.convert_string(bpmn_xml_string)

# Parse and inspect BPMN
model = parse_bpmn("process.bpmn")
print(f"Process: {model.process_name}")
print(f"Elements: {len(model.elements)}")
print(f"Has DI coordinates: {model.has_di_coordinates}")
```

### Validation

```python
from bpmn2drawio import parse_bpmn, validate_model

model = parse_bpmn("process.bpmn")
warnings = validate_model(model)

for warning in warnings:
    print(f"[{warning.level}] {warning.element_id}: {warning.message}")
```

## Themes

Four built-in themes are available:

| Theme | Description |
|-------|-------------|
| `default` | Standard BPMN colors (green start, red end, blue tasks, yellow gateways) |
| `blueprint` | Professional blue monochrome scheme |
| `monochrome` | Black, white, and gray for printing |
| `high_contrast` | Accessibility-focused high contrast colors |

### Custom Theme via YAML

Create a brand configuration file:

```yaml
# brand-config.yaml
colors:
  start_event_fill: "#c8e6c9"
  start_event_stroke: "#2e7d32"
  task_fill: "#e3f2fd"
  task_stroke: "#1565c0"
  gateway_fill: "#fff9c4"
  gateway_stroke: "#f9a825"
```

Use with CLI:

```bash
bpmn2drawio input.bpmn output.drawio --config=brand-config.yaml
```

## Supported BPMN Elements

### Events

| Type | Variants |
|------|----------|
| Start Event | None, Message, Timer, Signal, Conditional |
| End Event | None, Message, Error, Terminate, Signal |
| Intermediate | Message (catch/throw), Timer, Signal, Link |
| Boundary | Timer, Error, Message (interrupting/non-interrupting) |

### Activities

| Type | Description |
|------|-------------|
| Task | Generic task |
| User Task | Human task with person icon |
| Service Task | Automated task with gear icon |
| Script Task | Script execution with scroll icon |
| Send Task | Message sending |
| Receive Task | Message receiving |
| Business Rule Task | DMN/rules execution |
| Manual Task | Manual work outside system |
| Call Activity | External process call |
| Sub-Process | Embedded process |

### Gateways

| Type | Symbol | Use Case |
|------|--------|----------|
| Exclusive (XOR) | X | One path based on condition |
| Parallel (AND) | + | All paths simultaneously |
| Inclusive (OR) | O | One or more paths |
| Event-Based | Pentagon | Path based on which event occurs |
| Complex | Asterisk | Complex merge conditions |

### Flows

| Type | Style |
|------|-------|
| Sequence Flow | Solid line with arrow |
| Default Flow | Solid line with slash marker |
| Conditional Flow | Solid line with diamond start |
| Message Flow | Dashed line with circle start |
| Association | Dotted line |

### Containers

- Pools (horizontal and vertical)
- Lanes (nested within pools)

## Output Format

Generated files use the Draw.io mxfile XML format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="bpmn2drawio" version="1.0.0">
  <diagram id="diagram_1" name="Process Name">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- Elements and flows -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Development

### Running Tests

```bash
cd bpmn2drawio
python -m pytest tests/ -v
```

### Test Coverage

```bash
python -m pytest tests/ --cov=bpmn2drawio --cov-report=html
```

## Architecture

```
src/bpmn2drawio/
├── cli.py           # Command-line interface
├── converter.py     # Main orchestrator
├── parser.py        # BPMN XML parsing
├── generator.py     # Draw.io XML generation
├── layout.py        # Graphviz auto-layout
├── themes.py        # Theme system
├── styles.py        # Element style mappings
├── markers.py       # Gateway markers
├── icons.py         # Task/event icons
├── swimlanes.py     # Pool/lane handling
├── routing.py       # Edge routing
├── validation.py    # Model validation
└── recovery.py      # Error recovery
```

## License

MIT
