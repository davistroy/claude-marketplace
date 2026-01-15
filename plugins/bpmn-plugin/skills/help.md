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
| /bpmn-generator | Generate BPMN 2.0 compliant XML files from natural language process... |
| /bpmn-to-drawio | Convert BPMN 2.0 XML files into Draw.io native format (.drawio) using the... |
| /help | Show available skills in this plugin with usage information |

---
Use '/help <name>' for detailed help on a specific skill.
```

## Mode 2: Detailed Help (with argument)

When invoked with a skill name, display detailed information.

### Skill Reference

---

#### /bpmn-generator
**Description:** Generate BPMN 2.0 compliant XML files from natural language process...
**Arguments:** None required
**Output:** Generated output file

**Example:**
```
/bpmn-generator
```

---

#### /bpmn-to-drawio
**Description:** Convert BPMN 2.0 XML files into Draw.io native format (.drawio) using the...
**Arguments:** None required
**Output:** Generated output file

**Example:**
```
/bpmn-to-drawio
```

---

#### /help
**Description:** Show available skills in this plugin with usage information
**Arguments:** None required
**Output:** In-conversation output

**Example:**
```
/help                          # Show all skills
/help <skill-name>             # Show detailed help for a specific skill
```

---

## Error Handling

If the requested skill is not found:
```
Skill '[name]' not found in bpmn-plugin.

Available skills:
  /bpmn-generator, /bpmn-to-drawio, /help
```
