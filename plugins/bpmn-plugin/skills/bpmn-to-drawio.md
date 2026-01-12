---
name: bpmn-to-drawio
description: >
  Convert BPMN 2.0 XML files into Draw.io native format (.drawio) that renders
  properly in Draw.io Desktop or web applications. Use this skill when a user
  wants to visualize a BPMN process in Draw.io, convert BPMN to editable diagrams,
  or create Draw.io files from process definitions. Triggers on: "convert BPMN to
  Draw.io", "create drawio from BPMN", "visualize BPMN in Draw.io".
---

# BPMN to Draw.io Converter

## Overview

This skill transforms BPMN 2.0 XML files into Draw.io native format (.drawio) files. The output renders correctly in Draw.io Desktop and web applications with:

- Proper swim lane structure (pools and lanes)
- BPMN-styled shapes for all element types
- Correct connector routing including cross-lane flows
- Color coding by lane function
- Editable elements for further customization

## Conversion Process

### Phase 1: BPMN Analysis

Before conversion, analyze the source BPMN file to extract:

| Metric | How to Identify | Impact on Layout |
|--------|-----------------|------------------|
| **Number of Pools** | Count `<bpmn:participant>` elements | Determines vertical stack height |
| **Number of Lanes** | Count `<bpmn:lane>` elements per pool | Sets pool subdivision |
| **Task Count per Lane** | Count tasks/events assigned to each lane | Determines lane width needs |
| **Gateway Complexity** | Count gateways and their branches | Affects horizontal spacing |
| **Cross-Lane Flows** | Sequence flows crossing lane boundaries | Requires root-level edge routing |
| **Message Flows** | Flows between pools | Requires dashed connectors |

### Phase 2: Extract BPMN Elements

Parse the BPMN XML to extract:

```yaml
collaboration:
  id: [collaboration id]
  participants: [list of pools]

process:
  id: [process id]
  name: [process name]

lanes:
  - id: [lane id]
    name: [lane name]
    elements: [list of element refs]

elements:
  start_events: [...]
  end_events: [...]
  tasks: [...]
  gateways: [...]
  intermediate_events: [...]

flows:
  sequence_flows: [...]
  message_flows: [...]

diagram_interchange:
  shapes: [BPMNShape elements with bounds]
  edges: [BPMNEdge elements with waypoints]
```

### Phase 3: Calculate Dimensions

Use BPMN DI coordinates if available, otherwise calculate:

```
PAGE_WIDTH  = POOL_LEFT_MARGIN + POOL_WIDTH + RIGHT_MARGIN
PAGE_HEIGHT = POOL_TOP_MARGIN + TOTAL_POOL_HEIGHT + BOTTOM_MARGIN

Where:
- POOL_LEFT_MARGIN = 40px
- RIGHT_MARGIN = 100px
- POOL_TOP_MARGIN = 40px
- BOTTOM_MARGIN = 40px
```

### Phase 4: Generate Draw.io XML

Create the Draw.io file structure with all elements.

---

## Draw.io XML Structure

### File Skeleton

```xml
<mxfile host="app.diagrams.net" modified="[ISO_DATE]" agent="Claude BPMN Converter" version="22.1.0" type="device">
  <diagram name="[PROCESS_NAME]" id="[UNIQUE_ID]">
    <mxGraphModel dx="[DX]" dy="[DY]" grid="1" gridSize="10" guides="1" tooltips="1"
                  connect="1" arrows="1" fold="1" page="1" pageScale="1"
                  pageWidth="[WIDTH]" pageHeight="[HEIGHT]" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- Pools, Lanes, Elements, and Edges go here -->

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Element Hierarchy (CRITICAL)

```
Root (id="1")
├── Pool (parent="1")
│   ├── Lane 1 (parent="pool_id")
│   │   ├── Task (parent="lane_id")
│   │   ├── Gateway (parent="lane_id")
│   │   ├── Event (parent="lane_id")
│   │   └── Intra-lane Edge (parent="lane_id")
│   ├── Lane 2 (parent="pool_id")
│   └── ...
├── External Pool (parent="1")
└── Cross-Lane Edges (parent="1")  ← MUST be at root level
```

**CRITICAL RULE:** Edges that cross lane boundaries MUST have `parent="1"` (root level), not the lane they originate from. This ensures proper rendering when lanes are moved or resized.

---

## BPMN to Draw.io Shape Mapping

### Events

| BPMN Element | Draw.io Style |
|--------------|---------------|
| Start Event (None) | `shape=mxgraph.bpmn.shape;outline=throwing;symbol=general;` |
| Start Event (Message) | `shape=mxgraph.bpmn.shape;outline=throwing;symbol=message;` |
| Start Event (Timer) | `shape=mxgraph.bpmn.shape;outline=throwing;symbol=timer;` |
| Intermediate Catch (Message) | `shape=mxgraph.bpmn.shape;outline=catching;symbol=message;` |
| Intermediate Catch (Timer) | `shape=mxgraph.bpmn.shape;outline=catching;symbol=timer;` |
| Intermediate Throw (Message) | `shape=mxgraph.bpmn.shape;outline=throwing;symbol=message;` |
| End Event (None) | `shape=mxgraph.bpmn.shape;outline=end;symbol=general;` |
| End Event (Message) | `shape=mxgraph.bpmn.shape;outline=end;symbol=message;` |
| End Event (Terminate) | `shape=mxgraph.bpmn.shape;outline=end;symbol=terminate;` |
| End Event (Error) | `shape=mxgraph.bpmn.shape;outline=end;symbol=error;` |

**Event Dimensions:** 40x40 pixels

### Tasks

| BPMN Task Type | Draw.io Style | Default Fill Color |
|----------------|---------------|-------------------|
| Task (generic) | `rounded=1;whiteSpace=wrap;html=1;` | `#fff2cc` |
| User Task | `rounded=1;whiteSpace=wrap;html=1;` | `#fff2cc` |
| Service Task | `rounded=1;whiteSpace=wrap;html=1;` | `#e1d5e7` |
| Send Task | `rounded=1;whiteSpace=wrap;html=1;` | `#dae8fc` |
| Receive Task | `rounded=1;whiteSpace=wrap;html=1;` | `#dae8fc` |
| Script Task | `rounded=1;whiteSpace=wrap;html=1;` | `#e1d5e7` |
| Manual Task | `rounded=1;whiteSpace=wrap;html=1;` | `#fff2cc` |
| Business Rule Task | `rounded=1;whiteSpace=wrap;html=1;` | `#e1d5e7` |
| Subprocess (collapsed) | `rounded=1;whiteSpace=wrap;html=1;strokeWidth=2;` | `#dae8fc` |

**Task Dimensions:** 100x50 pixels (compact) or 100x80 pixels (standard)

### Gateways

| BPMN Gateway | Draw.io Style |
|--------------|---------------|
| Exclusive (XOR) | `shape=mxgraph.bpmn.gateway2;html=1;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;verticalAlign=top;outline=none;symbol=exclusiveGw;` |
| Parallel (AND) | `shape=mxgraph.bpmn.gateway2;html=1;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;verticalAlign=top;outline=none;symbol=parallelGw;` |
| Inclusive (OR) | `shape=mxgraph.bpmn.gateway2;html=1;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;verticalAlign=top;outline=none;symbol=inclusiveGw;` |
| Event-Based | `shape=mxgraph.bpmn.gateway2;html=1;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;verticalAlign=top;outline=none;symbol=eventGw;` |

**Gateway Dimensions:** 50x50 pixels

### Swim Lanes

#### Pool Container
```xml
<mxCell id="[POOL_ID]" value="[POOL_NAME]"
        style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;startSize=30;"
        vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="[POOL_WIDTH]" height="[POOL_HEIGHT]" as="geometry"/>
</mxCell>
```

#### Lane within Pool
```xml
<mxCell id="[LANE_ID]" value="[LANE_NAME]"
        style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=[FILL];strokeColor=[STROKE];startSize=30;"
        vertex="1" parent="[POOL_ID]">
  <mxGeometry x="30" y="[LANE_Y]" width="[LANE_WIDTH]" height="[LANE_HEIGHT]" as="geometry"/>
</mxCell>
```

---

## Lane Color Standards

Apply colors based on lane function/name:

| Lane Type | Fill Color | Stroke Color |
|-----------|------------|--------------|
| Sales/Commercial | `#dae8fc` | `#6c8ebf` |
| Legal/Compliance | `#d5e8d4` | `#82b366` |
| Finance | `#ffe6cc` | `#d79b00` |
| Security/IT | `#f8cecc` | `#b85450` |
| Implementation | `#e1d5e7` | `#9673a6` |
| Training | `#fff2cc` | `#d6b656` |
| Customer Success | `#d5e8d4` | `#82b366` |
| Support | `#f5f5f5` | `#666666` |
| External/Customer | `#f5f5f5` | `#666666` |

### Special Highlighting

| Purpose | Color | Usage |
|---------|-------|-------|
| Loop/Return Flow | `strokeColor=#b85450` | Rework or escalation paths |
| Critical Path | `strokeColor=#000000;strokeWidth=2` | Primary happy path |
| Error/Escalation Task | `fillColor=#f8cecc` | Tasks handling failures |

---

## Layout Standards

### Spacing Constants

```
POOL_LABEL_WIDTH     = 30px   (left side label area)
LANE_LEFT_OFFSET     = 30px   (lane starts 30px into pool)
ELEMENT_LEFT_MARGIN  = 60px   (first element from lane left edge)
ELEMENT_SPACING_H    = 140px  (horizontal gap between elements)
ELEMENT_SPACING_V    = 45px   (vertical gap for branching paths)
LANE_MIN_HEIGHT      = 100px  (minimum lane height)
LANE_BRANCH_HEIGHT   = 130px  (lane with vertical branching)
LANE_TRIPLE_HEIGHT   = 150px  (lane with 3+ vertical options)
```

### Lane Height Calculation

```
LANE_HEIGHT = max(LANE_MIN_HEIGHT, BRANCH_COUNT * 45 + 60)

Where:
- Single path lane: 100px
- Two branches (e.g., Yes/No): 130px
- Three branches (e.g., High/Med/Low): 150px
- Four+ branches: 180px+
```

### Element Positioning Within Lanes

Elements within a lane use coordinates relative to the lane:

```xml
<!-- Element inside lane -->
<mxCell id="task_1" value="Task Name"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
        vertex="1" parent="[LANE_ID]">
  <mxGeometry x="60" y="25" width="100" height="50" as="geometry"/>
</mxCell>
```

Note: `x` and `y` are relative to the lane's geometry, not the page.

---

## Edge (Connector) Generation

### Intra-Lane Edges

Edges that stay within a single lane:

```xml
<mxCell id="[FLOW_ID]" value="[LABEL]"
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;endArrow=block;endFill=1;"
        edge="1" parent="[LANE_ID]" source="[SOURCE_ID]" target="[TARGET_ID]">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Cross-Lane Edges (CRITICAL)

Edges crossing lane boundaries MUST use absolute coordinates:

```xml
<mxCell id="[FLOW_ID]" value="[LABEL]"
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;endArrow=block;endFill=1;"
        edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="[ABS_SOURCE_X]" y="[ABS_SOURCE_Y]" as="sourcePoint"/>
    <mxPoint x="[ABS_TARGET_X]" y="[ABS_TARGET_Y]" as="targetPoint"/>
    <Array as="points">
      <mxPoint x="[WAYPOINT_X]" y="[WAYPOINT_Y]"/>
      <!-- Additional waypoints as needed -->
    </Array>
  </mxGeometry>
</mxCell>
```

### Message Flows (Between Pools)

```xml
<mxCell id="[MSG_FLOW_ID]" value="[LABEL]"
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;endArrow=open;endFill=0;dashed=1;dashPattern=8 4;"
        edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="[SOURCE_X]" y="[SOURCE_Y]" as="sourcePoint"/>
    <mxPoint x="[TARGET_X]" y="[TARGET_Y]" as="targetPoint"/>
  </mxGeometry>
</mxCell>
```

---

## Absolute Coordinate Calculation

When creating cross-lane edges, calculate absolute coordinates:

```
ABSOLUTE_X = POOL_X + LANE_X_OFFSET + ELEMENT_X_IN_LANE + (ELEMENT_WIDTH / 2)
ABSOLUTE_Y = POOL_Y + LANE_Y_IN_POOL + ELEMENT_Y_IN_LANE + (ELEMENT_HEIGHT / 2)

Example:
- Pool starts at (40, 40)
- Lane 3 is at y=340 within pool (lane x offset = 30)
- Element is at (550, 40) within lane, size 100x50
- Element center X = 40 + 30 + 550 + 50 = 670 (absolute)
- Element center Y = 40 + 340 + 40 + 25 = 445 (absolute)
- Element right edge X = 40 + 30 + 550 + 100 = 720 (absolute)
```

### Connection Points

| Element Type | Center | Right Edge | Bottom |
|--------------|--------|------------|--------|
| Event (40x40) | x+20, y+20 | x+40, y+20 | x+20, y+40 |
| Task (100x50) | x+50, y+25 | x+100, y+25 | x+50, y+50 |
| Gateway (50x50) | x+25, y+25 | x+50, y+25 | x+25, y+50 |

---

## Conversion Workflow

### Step 1: Parse BPMN XML

```python
# Pseudocode
bpmn = parse_xml(input_file)
collaboration = bpmn.find('collaboration')
process = bpmn.find('process')
lanes = process.findall('.//lane')
elements = extract_all_elements(process)
diagram = bpmn.find('BPMNDiagram/BPMNPlane')
```

### Step 2: Build Lane Structure

1. Create pool mxCell with calculated dimensions
2. For each lane:
   - Determine lane height based on branching
   - Calculate y-position (cumulative)
   - Assign color based on lane name
   - Create lane mxCell

### Step 3: Place Elements

For each BPMN element:
1. Find corresponding BPMNShape in DI
2. Get bounds (x, y, width, height)
3. Determine parent lane
4. Convert to lane-relative coordinates
5. Apply appropriate style based on element type
6. Create mxCell

### Step 4: Create Edges

For each sequence flow:
1. Check if source and target are in same lane
2. If same lane: Create edge with `parent="[LANE_ID]"` and `source`/`target` attributes
3. If cross-lane: Create edge with `parent="1"` and absolute `mxPoint` coordinates
4. Add waypoints from BPMNEdge if available
5. Add labels for conditional flows

### Step 5: Generate Output

1. Build mxfile structure
2. Insert all mxCell elements in correct order
3. Write to .drawio file

---

## Element Templates

### Standard Task
```xml
<mxCell id="task_[ID]" value="[NAME]"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
        vertex="1" parent="[LANE_ID]">
  <mxGeometry x="[X]" y="[Y]" width="100" height="50" as="geometry"/>
</mxCell>
```

### Exclusive Gateway with Label
```xml
<mxCell id="gw_[ID]" value="[DECISION_QUESTION]"
        style="shape=mxgraph.bpmn.gateway2;html=1;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;verticalAlign=top;outline=none;symbol=exclusiveGw;fillColor=#ffffff;strokeColor=#000000;"
        vertex="1" parent="[LANE_ID]">
  <mxGeometry x="[X]" y="[Y]" width="50" height="50" as="geometry"/>
</mxCell>
```

### Start Event
```xml
<mxCell id="start_[ID]" value="[NAME]"
        style="shape=mxgraph.bpmn.shape;outline=throwing;symbol=general;fillColor=#ffffff;strokeColor=#000000;"
        vertex="1" parent="[LANE_ID]">
  <mxGeometry x="[X]" y="[Y]" width="40" height="40" as="geometry"/>
</mxCell>
```

### End Event
```xml
<mxCell id="end_[ID]" value="[NAME]"
        style="shape=mxgraph.bpmn.shape;outline=end;symbol=general;fillColor=#ffffff;strokeColor=#000000;strokeWidth=3;"
        vertex="1" parent="[LANE_ID]">
  <mxGeometry x="[X]" y="[Y]" width="40" height="40" as="geometry"/>
</mxCell>
```

### Cross-Lane Edge
```xml
<mxCell id="flow_[SOURCE]_to_[TARGET]" value="[LABEL]"
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;endArrow=block;endFill=1;"
        edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="[SOURCE_X]" y="[SOURCE_Y]" as="sourcePoint"/>
    <mxPoint x="[TARGET_X]" y="[TARGET_Y]" as="targetPoint"/>
    <Array as="points">
      <mxPoint x="[MID_X]" y="[SOURCE_Y]"/>
      <mxPoint x="[MID_X]" y="[TARGET_Y]"/>
    </Array>
  </mxGeometry>
</mxCell>
```

---

## Common Issues and Solutions

### Issue 1: Cross-Lane Arrows Not Rendering

**Symptom:** Sequence flows crossing lane boundaries don't appear.

**Solution:** Ensure cross-lane edges use `parent="1"` (root) with absolute `mxPoint` coordinates, not relative parent references.

### Issue 2: Elements Overlapping

**Symptom:** Multiple elements render on top of each other.

**Solution:**
1. Increase lane height to accommodate branches
2. Explicitly set different y-coordinates for each branch
3. Use formula: `y = lane_top + (branch_index * vertical_spacing)`

### Issue 3: Lane Labels Cut Off

**Symptom:** Horizontal lane labels don't fully display.

**Solution:** Ensure `startSize=30` in lane style for adequate label width.

### Issue 4: Connectors Not Routing Properly

**Symptom:** Edges take unexpected paths or overlap elements.

**Solution:** Add explicit waypoints in the `<Array as="points">` element.

### Issue 5: Gateway Labels Overlapping

**Symptom:** Condition labels overlap with other labels or elements.

**Solution:**
1. Use waypoints to route edges away from congested areas
2. Shorten labels (e.g., "Y" instead of "Yes")
3. Adjust element spacing

---

## Output Format

After conversion, output:

### 1. Conversion Summary
```
## Draw.io Conversion Summary

**Source File:** [input.bpmn]
**Output File:** [output.drawio]

### Elements Converted:
- Pools: [count]
- Lanes: [count]
- Tasks: [count]
- Gateways: [count]
- Events: [count]
- Sequence Flows: [count]
- Message Flows: [count]

### Cross-Lane Flows: [count]
(These use absolute positioning for proper rendering)
```

### 2. Draw.io File
Write the complete XML to a file named `[process-name].drawio`

### 3. Validation Notes
```
## Conversion Notes

✓ All elements converted successfully
✓ Lane colors applied based on function
✓ Cross-lane edges use absolute coordinates
✓ Gateway labels positioned

Recommendations:
- [Any manual adjustments suggested]
```

---

## References

- `../references/BPMN-to-DrawIO-Conversion-Standard.md` - Complete conversion specification
- `../templates/drawio-skeleton.xml` - Base Draw.io structure
- `../templates/element-styles.yaml` - Style definitions for all element types
- `../examples/` - Sample conversions
