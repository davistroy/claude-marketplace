---
name: help
description: Show available skills in this plugin with usage information
---

# Help Skill

Display help information for the bpmn-plugin skills.

**IMPORTANT:** This skill must be updated whenever skills are added, changed, or removed from this plugin.

## Usage

```text
/help                          # Show all skills
/help <skill-name>             # Show detailed help for a specific skill
```

## Mode 1: List All (no arguments)

When invoked without arguments, display this table:

```text
bpmn-plugin Skills
==================

| Skill | Description |
|-------|-------------|
| /bpmn-generator | Generate BPMN 2.0 XML from natural language or markdown documents |
| /bpmn-to-drawio | Convert BPMN XML to Draw.io format for visual editing |
| /help | Show available skills in this plugin with usage information |

---
Use '/help <name>' for detailed help on a specific skill.
```

## Mode 2: Detailed Help (with argument)

When invoked with a skill name, display detailed information.

### Skill Reference

---

#### /bpmn-generator
**Description:** Generate BPMN 2.0 compliant XML files from natural language process descriptions or structured markdown documents. Creates complete process definitions with proper namespaces, Diagram Interchange (DI) data for rendering, and phase comments for PowerPoint compatibility.

**Operating Modes:**
- **Interactive Mode**: When given a natural language description (no file), conducts structured Q&A to gather requirements across 7 phases (scope, participants, activities, flow control, events, data, optimization).
- **Document Parsing Mode**: When given a markdown file path, extracts process elements from headings, numbered lists, and document structure.

**Arguments:** `[description or file.md]` `[--preview]`
**Output:** `[process-name].bpmn` - BPMN 2.0 compliant XML file

**Examples:**
```text
/bpmn-generator                           # Interactive mode - guided Q&A
/bpmn-generator "order fulfillment flow"  # Interactive mode with initial description
/bpmn-generator process-doc.md            # Document parsing mode
/bpmn-generator process-doc.md --preview  # Preview before saving
```

---

#### /bpmn-to-drawio
**Description:** Convert BPMN 2.0 XML files into Draw.io native format (.drawio) using the bundled bpmn2drawio Python tool. Produces editable diagrams with proper swim lanes, BPMN-styled shapes, and correct connector routing. Supports automatic layout via Graphviz or preserves existing DI coordinates.

**Features:**
- Four built-in themes: default, blueprint, monochrome, high_contrast
- Custom YAML branding configuration support
- Visual markers for gateways (X, +, O) and task/event icons
- Complete swimlane support with role-based color coding

**Arguments:** `<input.bpmn>` `<output.drawio>` `[--theme=NAME]` `[--layout=MODE]` `[--direction=DIR]`
**Output:** `.drawio` file compatible with Draw.io Desktop and web applications

**Examples:**
```text
/bpmn-to-drawio process.bpmn diagram.drawio                    # Basic conversion
/bpmn-to-drawio process.bpmn diagram.drawio --theme=blueprint  # With theme
/bpmn-to-drawio process.bpmn diagram.drawio --layout=preserve  # Keep existing layout
/bpmn-to-drawio process.bpmn diagram.drawio --direction=TB     # Top-to-bottom flow
```

---

#### /help
**Description:** Show available skills in this plugin with usage information
**Arguments:** `[skill-name]` - Optional skill name for detailed help
**Output:** In-conversation output

**Examples:**
```text
/help                          # Show all skills
/help bpmn-generator           # Detailed help for bpmn-generator
/help bpmn-to-drawio           # Detailed help for bpmn-to-drawio
```

---

## Error Handling

If the requested skill is not found:
```text
Skill '[name]' not found in bpmn-plugin.

Available skills:
  /bpmn-generator, /bpmn-to-drawio, /help
```
