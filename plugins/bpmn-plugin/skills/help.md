---
description: Show available skills in this plugin with usage information
---

# Help Skill

Display help information for the bpmn-plugin skills.

**IMPORTANT:** This skill must be updated whenever skills are added, changed, or removed from this plugin.

## Usage

```
/help                          # Show all skills
/help <skill-name>             # Show detailed help for a specific skill
```

## Mode 1: List All (no arguments)

When invoked without arguments, display this table:

```
bpmn-plugin Skills
==================

| Skill | Description |
|-------|-------------|
| /bpmn-generator | Generate BPMN 2.0 XML from natural language or markdown documents |
| /bpmn-to-drawio | Convert BPMN 2.0 XML files to Draw.io native format (.drawio) |
| /help | Show available skills with usage information |

---
Use '/help <name>' for detailed help on a specific skill.
```

## Mode 2: Detailed Help (with argument)

When invoked with a skill name, display detailed information.

### Skill Reference

---

#### /bpmn-generator
**Description:** Generate BPMN 2.0 compliant XML files from natural language process descriptions or structured markdown documents.

**Arguments:**
- Natural language description of a business process, OR
- `<markdown-file-path>` - Path to a structured markdown document

**Modes:**
- **Interactive Mode**: Triggered by natural language descriptions. Structured Q&A gathers requirements through 6 phases: Process Scope, Participants, Activities, Flow Control, Events & Exceptions, Data & Integration.
- **Document Parsing Mode**: Triggered by providing a markdown file path. Extracts process elements from document structure.

**Output:** BPMN 2.0 compliant XML file with:
- Complete process definitions
- Proper namespace declarations
- Diagram Interchange (DI) data for visual rendering
- Phase comments for PowerPoint compatibility

**Example:**
```
/bpmn-generator
# Then describe: "Create a BPMN for an order fulfillment process"

/bpmn-generator docs/order-process.md
# Parses markdown and generates BPMN XML
```

---

#### /bpmn-to-drawio
**Description:** Convert BPMN 2.0 XML files into Draw.io native format (.drawio) for visual editing.

**Arguments:** `<bpmn-file-path>` - Path to the BPMN 2.0 XML file

**Features:**
- Automatic Graphviz-based layout for files without DI coordinates
- Four built-in themes with custom YAML branding support
- Visual markers for gateways (X, +, O) and task/event icons
- Complete swimlane support with proper hierarchy
- Model validation with error recovery

**Requirements:**
- Python 3.x with lxml, networkx, pyyaml
- Graphviz and pygraphviz (for automatic layout)

**Output:** `.drawio` file compatible with Draw.io Desktop and web applications

**Example:**
```
/bpmn-to-drawio process.bpmn
# Converts BPMN XML to Draw.io format

/bpmn-to-drawio order-fulfillment.xml --theme corporate
# Uses corporate theme for styling
```

---

#### /help
**Description:** Show available skills with usage information
**Arguments:** `[skill-name]` - Optional specific skill to get help for
**Output:** Skill list or detailed help

**Example:**
```
/help
/help bpmn-generator
```

---

## Error Handling

If the requested skill is not found:
```
Skill '[name]' not found in bpmn-plugin.

Available skills:
  /bpmn-generator, /bpmn-to-drawio, /help
```
