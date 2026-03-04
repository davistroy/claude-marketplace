---
name: bpmn-generator
allowed-tools: Read, Write, Glob, Grep
description: >
  Generate BPMN 2.0 compliant XML files from natural language process descriptions
  OR from structured markdown business process documents. Use this skill when a user
  wants to create a BPMN workflow, convert a business process to BPMN XML, model a
  workflow diagram, or generate process definitions. Triggers on requests like
  "create a BPMN", "generate workflow XML", "model this process", "convert to BPMN 2.0",
  "create process diagram", "build workflow", or "convert this markdown to BPMN".
---

# BPMN 2.0 XML Generator

## Overview

This skill transforms process descriptions into fully compliant BPMN 2.0 XML files. It operates in two modes:

| Mode | Trigger | Workflow |
|------|---------|----------|
| **Interactive** | Natural language description, no file provided | Structured Q&A to gather requirements |
| **Document Parsing** | Markdown file path provided | Parse document structure, extract elements |

The generated XML includes:
- Complete process definitions with all BPMN elements
- Proper namespace declarations for BPMN 2.0 compliance
- Diagram Interchange (DI) data for visual rendering
- Phase comments for PowerPoint generation compatibility
- Layouts compatible with Draw.io, Camunda, Flowable, and bpmn.io

---

# MODE DETECTION

## Automatic Mode Selection

Determine the operating mode based on user input:

```text
IF user provides a markdown file path (.md):
    → Document Parsing Mode
ELSE IF user provides a natural language description:
    → Interactive Mode
```

### Document Parsing Mode Indicators
- File path ending in `.md`
- "convert this document", "parse this file"
- "generate BPMN from [filename]"
- Markdown content pasted directly

### Interactive Mode Indicators
- Brief process description without file
- "create a BPMN for...", "model a process that..."
- Questions about process design
- No structured document provided

### Preview Mode

Both modes support an optional `--preview` flag:

When `--preview` is specified:
1. Generate the complete BPMN XML in memory
2. Validate structure (namespace, elements, flows)
3. Display summary:
   ```
   Preview: /bpmn-generator
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Process: Order Fulfillment
   Source: Interactive mode

   Structure Summary:
     Pools: 1
     Lanes: 3 (Sales, Operations, Shipping)
     Tasks: 8 (5 user, 3 service)
     Gateways: 2 (1 exclusive, 1 parallel)
     Events: 2 (1 start, 1 end)

   Validation: PASSED
   Output file: order-fulfillment.bpmn
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Save this file? (y/n):
   ```
4. Wait for user confirmation before saving
5. On 'n' or 'no': Exit without saving

---

# PART 1: INTERACTIVE MODE

Use this mode when the user provides a natural language description without a structured document.

## Interactive Question Framework

### Purpose

Initial process descriptions are rarely sufficient for optimal BPMN generation. This mode uses a structured clarification process to gather complete requirements before generating XML.

### Question Format

For EVERY clarifying question, use this EXACT format:

```markdown
## Question [N]: [Topic Category]

[Clear, specific question about the process]

### Options:

**A) [Recommended]**: [Specific answer]
   *Why*: [2-3 sentence reasoning explaining why this is the best choice]

**B)** [Alternative answer 1]
**C)** [Alternative answer 2]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions (auto-accept mode)

---
Your choice (A/B/C/D/E):
```

### Auto-Accept Mode

When the user selects option **E**:
1. Set internal flag: `AUTO_ACCEPT_MODE = true`
2. For all subsequent questions, automatically use the recommended answer
3. Log each auto-accepted decision
4. Before generating XML, present a summary:

```markdown
## Auto-Accepted Decisions Summary

| Question | Topic | Decision |
|----------|-------|----------|
| Q3 | Gateway Type | Exclusive Gateway (XOR) |
| Q4 | Error Handling | Boundary Error Event |
| ... | ... | ... |

Proceeding with XML generation using these decisions.
```

### Question Phases

Process questions in this specific order:

#### Phase 1: Process Scope (Questions 1-3)
- Process name and identifier
- Process trigger (start event type)
- Process completion states (end event types)

#### Phase 2: Participants (Questions 4-5)
- Single process vs. collaboration (multiple pools)
- Lanes/roles within pools

#### Phase 3: Activities (Questions 6-11)
- Main activities/tasks identification
- Task types for each activity
- **Task descriptions/documentation** (CRITICAL for PowerPoint generation)
- Task sequencing and dependencies
- Subprocess candidates

#### Phase 4: Flow Control (Questions 11-15)
- Decision points requiring gateways
- Gateway types (exclusive, parallel, inclusive, event-based)
- Default flows
- Loop/cycle detection

#### Phase 5: Events & Exceptions (Questions 16-19)
- Intermediate events (timer, message, signal)
- Boundary events on tasks
- Error handling approach
- Compensation requirements

#### Phase 6: Data & Integration (Questions 20-22)
- Data objects needed
- External system integrations
- Message flows (for collaborations)

#### Phase 7: Optimization Review (Question 23)
- Final review of proposed structure
- Opportunity for adjustments

### Session Commands

Support these standard session commands during Interactive mode:

| Command | Aliases | Action |
|---------|---------|--------|
| `help` | `?`, `commands` | Show available session commands |
| `status` | `progress` | Show current phase and questions completed |
| `back` | `previous`, `prev` | Return to previous question |
| `skip` | `next`, `pass` | Skip current question (use recommended) |
| `quit` | `exit`, `stop` | Exit without generating BPMN |

**When user types `help`:**
```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session Commands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  help      Show this help message
  status    Show current phase and progress
  back      Return to previous question
  skip      Skip question (uses recommended answer)
  quit      Exit without generating BPMN

Press E at any question to accept recommended
answers for all remaining questions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Implementation notes:**
- Commands are case-insensitive
- Check for session commands before processing input as an answer choice
- Unknown input that is not A/B/C/D/E should trigger the help message

### Adaptive Questioning

Skip questions that don't apply:
- Skip participant questions for simple single-pool processes
- Skip data questions if no data dependencies mentioned
- Skip error handling if process is straightforward
- Always ask critical questions: start event, main tasks, end events

---

# PART 2: DOCUMENT PARSING MODE

Use this mode when the user provides a markdown file containing a structured business process document.

## Document Analysis Steps

### Step 1: Identify Document Structure

Analyze the markdown document for structural elements that map to BPMN constructs. Key patterns: H1 = process name, H2/H3 "Phase/Step" = phase comments, numbered lists = tasks, role tables = lanes, conditional language = gateways, "begins when" = start events, "completes when" = end events. See `../references/markdown-parsing-guide.md` for the complete document structure mapping table.

### Step 2: Extract Process Metadata

From the document, extract:

```yaml
process_name: [from H1 or title]
process_id: [sanitized process_name, e.g., "SocialMediaCommunityManagement"]
description: [from executive summary or overview section]
version: [from document metadata if present]
roles: [list of all mentioned roles/actors]
phases: [ordered list of phase names from section headings]
```

### Step 3: Map Roles to Lanes

Use the lane mapping configuration in `../templates/lane-mapping.yaml` to assign colors. Read `references/bpmn-elements.md` for the complete role-to-lane color mapping table (Sales, Legal, Finance, IT, Implementation, Training, Customer Success, Support, Customer).

### Step 4: Parse Phases and Tasks

#### Phase Detection Patterns

Match headings like "## Step 1:", "### Phase 2:", or "## 1.1 Section" using H2-H4 with step/phase/stage keywords or numbered sections. See `../references/markdown-parsing-guide.md` for regex patterns.

#### Task Type Inference

Use the task type selection table in `references/bpmn-elements.md` to map markdown language to BPMN task types. Common shortcuts: "reviews/approves" = userTask, "system/API" = serviceTask, "sends/notifies" = sendTask, "waits for/receives" = receiveTask, "subprocess" = subProcess.

### Step 5: Extract Documentation

**Critical:** Every task MUST have a `<bpmn:documentation>` element. Extract from:

1. Paragraph following task heading
2. Bullet points under task name
3. Table cell descriptions
4. "Process Description:" sections

Combine multiple sources into comprehensive documentation:

```xml
<bpmn:userTask id="Activity_ReviewTriage" name="Review and Triage">
    <bpmn:documentation>
        Community Manager and Social Team Lead manually review inbound interactions
        to assess and categorize them. Triage criteria includes: Topic/Intent,
        Location Relevance, Urgency, Risk Level, and Sentiment. Categories include
        location-specific issues, digital inquiries, brand questions, escalations,
        spam, and general engagement.
    </bpmn:documentation>
</bpmn:userTask>
```

---

# PART 3: SHARED BPMN GENERATION

Both modes use the same BPMN generation rules.

## BPMN Element Mapping

Read `references/bpmn-elements.md` (relative to this plugin's directory) for element type mappings and DI constants, including:
- **Task Type Selection** - keyword-to-BPMN-task-type mapping (userTask, serviceTask, sendTask, etc.)
- **Gateway Selection** - decision-pattern-to-gateway-type mapping (exclusive, parallel, inclusive, event-based)
- **Event Selection** - start and end event type mappings with XML elements

## Phase Comments (CRITICAL for PowerPoint)

**Always include phase comments** to enable automatic phase detection for PowerPoint presentations:

```xml
<bpmn:process id="Process_Example" name="Example Process" isExecutable="true">

    <!-- Phase 1: Intake and Validation -->
    <bpmn:startEvent id="StartEvent_1" name="Request Received">
        ...
    </bpmn:startEvent>

    <!-- Phase 2: Processing -->
    <bpmn:serviceTask id="Activity_Process" name="Process Request">
        ...
    </bpmn:serviceTask>

    <!-- Phase 3: Fulfillment -->
    <bpmn:userTask id="Activity_Fulfill" name="Fulfill Request">
        ...
    </bpmn:userTask>

</bpmn:process>
```

## XML Generation Rules

### Required Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    id="Definitions_[unique-id]"
    targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="Claude BPMN Generator"
    exporterVersion="2.0">

    <!-- Process definition goes here -->

    <!-- Diagram interchange goes here -->

</bpmn:definitions>
```

### ID Generation Rules

Read `references/bpmn-elements.md` for the complete ID pattern table (Process, StartEvent, EndEvent, Activity, Gateway, Lane, Flow patterns with examples).

### Sequence Flow Rules

1. Every element (except start events) MUST have at least one incoming flow
2. Every element (except end events) MUST have at least one outgoing flow
3. Gateways splitting must eventually merge (except for end paths)
4. Conditional flows MUST have condition expressions:

```xml
<bpmn:sequenceFlow id="Flow_1" sourceRef="Gateway_1" targetRef="Task_2">
    <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
        ${condition == true}
    </bpmn:conditionExpression>
</bpmn:sequenceFlow>
```

5. Default flows from gateways:

```xml
<bpmn:exclusiveGateway id="Gateway_1" default="Flow_default">
    ...
</bpmn:exclusiveGateway>
<bpmn:sequenceFlow id="Flow_default" sourceRef="Gateway_1" targetRef="Task_3"/>
```

## Diagram Interchange Generation

### Element Dimensions and Layout Constants

Read `references/bpmn-elements.md` for element dimension tables (width/height for events, tasks, gateways, subprocesses) and Draw.io-compatible layout constants (pool label width, lane offsets, element spacing).

### Cross-Lane Edge Rule (CRITICAL)

Edges crossing lane boundaries MUST have `parent="1"` (root) with absolute `mxPoint` coordinates when targeting Draw.io conversion.

## Validation Checklist

Before outputting XML, verify:

### Structural Integrity
- [ ] Exactly one start event (or multiple for event subprocess)
- [ ] At least one end event
- [ ] All elements connected via sequence flows
- [ ] No orphaned elements
- [ ] All IDs unique within document

### Flow Validity
- [ ] Start events have no incoming flows
- [ ] End events have no outgoing flows
- [ ] All other elements have both incoming and outgoing flows
- [ ] Parallel splits have matching parallel joins
- [ ] No infinite loops without exit condition

### BPMN 2.0 Compliance
- [ ] All required namespaces declared
- [ ] All elements have required attributes (id, name where applicable)
- [ ] Conditional flows have condition expressions
- [ ] Default flows properly marked on gateways
- [ ] Event definitions properly nested

### Documentation & Phases
- [ ] All tasks have `<bpmn:documentation>` elements
- [ ] Phase comments included for PowerPoint compatibility
- [ ] Documentation is comprehensive (not just task name repeated)

### Diagram Interchange
- [ ] Every process element has corresponding BPMNShape
- [ ] Every sequence flow has corresponding BPMNEdge
- [ ] All shapes have valid Bounds (x, y, width, height)
- [ ] All edges have at least 2 waypoints
- [ ] No negative coordinates
- [ ] Elements don't overlap

---

# OUTPUT FORMAT

## For Interactive Mode

### 1. Decision Summary
Display a "Process Configuration Summary" with process name, ID, and a decisions table (# / Topic / Decision).

### 2. Process Description
Show a brief narrative of the process flow with a flow summary line (Start -> Task -> Gateway -> End).

### 3. BPMN XML File
Write the complete XML to a file named `[process-name].bpmn` in the current directory.

## For Document Parsing Mode

### 1. Conversion Summary
Display source document, process name/ID, extracted structure counts (phases, roles/lanes, tasks by type, gateways, events), and any assumptions made during parsing.

### 2. BPMN XML File
Write complete XML to `[process-name].bpmn`

## Common Output

### Validation Confirmation
After generating XML, display validation results confirming: structural checks passed, flow validity passed, BPMN 2.0 compliance verified, diagram interchange complete, phase comments included, and the output filename.

---

## Performance

| Process Complexity | Elements | Expected Duration | Notes |
|--------------------|----------|-------------------|-------|
| Simple (linear flow) | 5-10 | 1-3 minutes | Few gateways, single pool |
| Medium (branching) | 10-30 | 3-8 minutes | Multiple gateways, 2-4 lanes |
| Complex (collaboration) | 30-60 | 8-15 minutes | Multiple pools, message flows, subprocesses |
| Document parsing mode | varies | 2-5 minutes | Faster than interactive; no Q&A overhead |

Interactive mode duration is dominated by the Q&A clarification phases (user response time not included). XML generation and DI coordinate calculation add 10-30 seconds regardless of complexity. Document parsing mode is faster because it skips the interactive question framework and extracts structure directly from markdown.

# REFERENCES

For detailed specifications, see:
- `../references/bpmn-elements.md` - Element type mappings, DI constants, ID patterns, and lane colors
- `../references/bpmn-elements-reference.md` - Complete element catalog
- `../references/xml-namespaces.md` - Namespace documentation
- `../references/clarification-patterns.md` - Question templates (Interactive mode)
- `../references/markdown-parsing-guide.md` - Document parsing patterns (Document mode)

For templates, see:
- `../templates/bpmn-skeleton.xml` - Base structure
- `../templates/element-templates.xml` - Element snippets
- `../templates/lane-mapping.yaml` - Role to lane color mapping

For examples, see:
- `../examples/` - Complete working examples for both modes
