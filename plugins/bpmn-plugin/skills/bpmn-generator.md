---
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

```
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

---

# PART 1: INTERACTIVE MODE

Use this mode when the user provides a natural language description without a structured document.

## Interactive Question Framework

### Purpose

Initial process descriptions are rarely sufficient for optimal BPMN generation. This mode uses a structured clarification process to gather complete requirements before generating XML.

### Question Format

For EVERY clarifying question, use this EXACT format:

```
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

```
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

Analyze the markdown document for these structural elements:

| Element | Markdown Indicators | BPMN Mapping |
|---------|---------------------|--------------|
| **Process Name** | H1 heading, title in frontmatter | `<bpmn:process name="...">` |
| **Phases/Stages** | H2/H3 headings like "Step 1:", "Phase:", numbered sections | Phase comments `<!-- Phase N: ... -->` |
| **Workflow Steps** | Numbered lists, H3/H4 subheadings under phases | Tasks and events |
| **Roles/Actors** | "Roles Involved:", tables with role columns, bold text at step start | Lanes in LaneSet |
| **Decision Points** | "if/then", conditional language, branching described | Gateways |
| **Parallel Activities** | "simultaneously", "at the same time", "in parallel" | Parallel gateways |
| **Process Triggers** | "begins when", "triggered by", "starts with" | Start events |
| **Process Outcomes** | "completes when", "ends with", outcome sections | End events |

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

Use the lane mapping configuration in `../templates/lane-mapping.yaml` to assign colors:

| Document Role Pattern | Lane Name | Fill / Stroke Color |
|----------------------|-----------|---------------------|
| Sales, Commercial | Sales | `#dae8fc` / `#6c8ebf` |
| Legal, Compliance | Legal Operations | `#d5e8d4` / `#82b366` |
| Finance, Billing | Finance | `#ffe6cc` / `#d79b00` |
| IT, Security | Security/IT | `#f8cecc` / `#b85450` |
| Implementation, Project | Implementation | `#e1d5e7` / `#9673a6` |
| Training, Enablement | Training | `#fff2cc` / `#d6b656` |
| Customer Success | Customer Success | `#d5e8d4` / `#82b366` |
| Support, Help Desk | Support | `#f5f5f5` / `#666666` |
| Customer (External) | Customer Pool | `#f5f5f5` / `#666666` |

### Step 4: Parse Phases and Tasks

#### Phase Detection Patterns

```regex
# Explicit step numbering
^#{2,4}\s*[\d.]*\s*Step\s+\d+[:.]?\s*(.+)$

# Phase/Stage keywords
^#{2,3}\s*(Phase|Stage|Step)\s+\d+[:.]?\s*(.+)$

# Numbered workflow sections
^#{2,4}\s*([\d.]+)\s+(.+)$
```

#### Task Type Inference

| Markdown Language | Task Type | BPMN Element |
|-------------------|-----------|--------------|
| "reviews", "approves", "manually", "person" | User Task | `<bpmn:userTask>` |
| "system", "automated", "API", "queries" | Service Task | `<bpmn:serviceTask>` |
| "sends", "notifies", "emails", "alerts" | Send Task | `<bpmn:sendTask>` |
| "waits for", "receives", "awaits" | Receive Task | `<bpmn:receiveTask>` |
| "subprocess", "sub-process" reference | Subprocess | `<bpmn:subProcess>` |

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

### Task Type Selection

| Keywords in Description | BPMN Task Type | XML Element |
|------------------------|----------------|-------------|
| "user reviews", "person approves", "manually enters", "human performs" | User Task | `<bpmn:userTask>` |
| "system calls API", "automated process", "service executes", "integration" | Service Task | `<bpmn:serviceTask>` |
| "send email", "send notification", "notify user", "alert" | Send Task | `<bpmn:sendTask>` |
| "wait for response", "receive message", "await confirmation" | Receive Task | `<bpmn:receiveTask>` |
| "run script", "execute code", "calculate", "transform data" | Script Task | `<bpmn:scriptTask>` |
| "apply business rule", "decision table", "evaluate rules" | Business Rule Task | `<bpmn:businessRuleTask>` |
| "call external process", "invoke subprocess" | Call Activity | `<bpmn:callActivity>` |
| Generic activity with no specific type | Task | `<bpmn:task>` |

### Gateway Selection

| Decision Pattern | Gateway Type | XML Element | Symbol |
|-----------------|--------------|-------------|--------|
| "if/then/else", "either A or B", "based on condition" | Exclusive (XOR) | `<bpmn:exclusiveGateway>` | X |
| "do all of", "simultaneously", "in parallel" | Parallel (AND) | `<bpmn:parallelGateway>` | + |
| "one or more of", "any combination", "at least one" | Inclusive (OR) | `<bpmn:inclusiveGateway>` | O |
| "wait for first event", "whichever happens first" | Event-Based | `<bpmn:eventBasedGateway>` | Pentagon |

### Event Selection

#### Start Events
| Trigger | Event Type | XML Element |
|---------|-----------|-------------|
| Process begins manually or undefined | None | `<bpmn:startEvent>` |
| External message received | Message | `<bpmn:startEvent><bpmn:messageEventDefinition/></bpmn:startEvent>` |
| Scheduled time/date | Timer | `<bpmn:startEvent><bpmn:timerEventDefinition/></bpmn:startEvent>` |
| Condition becomes true | Conditional | `<bpmn:startEvent><bpmn:conditionalEventDefinition/></bpmn:startEvent>` |

#### End Events
| Outcome | Event Type | XML Element |
|---------|-----------|-------------|
| Normal completion | None | `<bpmn:endEvent>` |
| Send final message | Message | `<bpmn:endEvent><bpmn:messageEventDefinition/></bpmn:endEvent>` |
| Error occurred | Error | `<bpmn:endEvent><bpmn:errorEventDefinition/></bpmn:endEvent>` |
| Stop all process instances | Terminate | `<bpmn:endEvent><bpmn:terminateEventDefinition/></bpmn:endEvent>` |

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

| Element Type | ID Pattern | Example |
|--------------|------------|---------|
| Process | `Process_[ProcessName]` | `Process_OrderFulfillment` |
| Start Event | `StartEvent_[Trigger]` | `StartEvent_OrderReceived` |
| End Event | `EndEvent_[Outcome]` | `EndEvent_Complete` |
| User Task | `Activity_[ActionVerb][Noun]` | `Activity_ReviewApplication` |
| Service Task | `Activity_[SystemAction]` | `Activity_ValidateOrder` |
| Gateway (XOR) | `ExclusiveGateway_[Decision]` | `ExclusiveGateway_Approved` |
| Gateway (AND) | `ParallelGateway_[Split/Join]` | `ParallelGateway_SplitTracks` |
| Lane | `Lane_[RoleName]` | `Lane_CommunityManager` |
| Flow | `Flow_[Source]_[Target]` | `Flow_Review_Route` |

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

### Element Dimensions

| Element | Width | Height |
|---------|-------|--------|
| Start Event | 36 | 36 |
| End Event | 36 | 36 |
| Intermediate Event | 36 | 36 |
| Task | 100 | 80 |
| Gateway | 50 | 50 |
| Collapsed Subprocess | 100 | 80 |
| Expanded Subprocess | 350+ | 200+ |

### Layout Constants (Draw.io Compatible)

```
POOL_LABEL_WIDTH     = 30px
LANE_LEFT_OFFSET     = 30px
ELEMENT_LEFT_MARGIN  = 60px
ELEMENT_SPACING_H    = 140px  (horizontal gap between elements)
ELEMENT_SPACING_V    = 45px   (vertical gap for branching paths)
LANE_MIN_HEIGHT      = 100px
LANE_BRANCH_HEIGHT   = 130px  (lane with 2 branches)
LANE_TRIPLE_HEIGHT   = 150px  (lane with 3+ branches)
```

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
```
## Process Configuration Summary

**Process Name:** [name]
**Process ID:** [id]

### Decisions Made:
| # | Topic | Decision |
|---|-------|----------|
| 1 | Start Event | [type] |
| 2 | Main Tasks | [list] |
...
```

### 2. Process Description
```
## Generated Process Structure

[Brief narrative description of the process flow]

**Flow Summary:**
Start → [Task 1] → [Gateway] → [Branch A] / [Branch B] → [Merge] → End
```

### 3. BPMN XML File
Write the complete XML to a file named `[process-name].bpmn` in the current directory.

## For Document Parsing Mode

### 1. Conversion Summary
```
## Conversion Summary

**Source Document:** [filename.md]
**Process Name:** [name]
**Process ID:** [id]

### Extracted Structure:
- Phases: [count]
- Roles/Lanes: [list]
- Tasks: [count by type]
- Gateways: [count by type]
- Events: [count by type]

### Assumptions Made:
[List any inferences or assumptions about unclear elements]
```

### 2. BPMN XML File
Write complete XML to `[process-name].bpmn`

## Common Output

### Validation Confirmation
```
## Validation Results

✓ All structural checks passed
✓ All flow validity checks passed
✓ BPMN 2.0 compliance verified
✓ Diagram interchange complete
✓ Phase comments included

File written: [filename].bpmn
```

---

# REFERENCES

For detailed specifications, see:
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
