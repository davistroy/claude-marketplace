# BPMN to Draw.io Conversion Standard

## Overview

This document defines the standard process for converting BPMN 2.0 workflow diagrams into draw.io native format (.drawio) files that render properly in draw.io Desktop or web applications.

---

## 1. Source File Analysis

### 1.1 Extract Key Metrics from BPMN

Before conversion, analyze the source BPMN file to determine:

| Metric | How to Identify | Impact on Layout |
|--------|-----------------|------------------|
| **Number of Pools** | Count `<participant>` elements | Determines vertical stack height |
| **Number of Lanes** | Count `<lane>` elements per pool | Sets pool subdivision |
| **Task Count per Lane** | Count tasks/events in each lane | Determines lane width needs |
| **Gateway Complexity** | Count gateways and their branches | Affects horizontal spacing |
| **Cross-Lane Flows** | Sequence flows crossing lane boundaries | Requires root-level edge routing |
| **Message Flows** | Flows between pools | Requires dashed connectors |

### 1.2 Identify Process Sections

Map the horizontal flow into logical sections:

```
Section 1: Initiation (Start event → first gateway)
Section 2: Parallel Tracks (split activities)
Section 3: Synchronization (parallel join)
Section 4: Core Process (main workflow)
Section 5: Decision Points (exclusive gateways)
Section 6: Completion (end events)
```

---

## 2. Draw.io XML Structure

### 2.1 File Skeleton

```xml
<mxfile host="app.diagrams.net" modified="[DATE]" agent="[AGENT]" version="22.1.0" type="device">
  <diagram name="[DIAGRAM_NAME]" id="[UNIQUE_ID]">
    <mxGraphModel dx="2000" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" 
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

### 2.2 Page Dimensions Formula

Calculate page dimensions based on content:

```
PAGE_WIDTH  = POOL_LEFT_MARGIN + POOL_WIDTH + RIGHT_MARGIN
PAGE_HEIGHT = POOL_TOP_MARGIN + TOTAL_POOL_HEIGHT + BOTTOM_MARGIN + CUSTOMER_POOL_HEIGHT

Where:
- POOL_LEFT_MARGIN = 40px
- RIGHT_MARGIN = 100px  
- POOL_TOP_MARGIN = 40px
- BOTTOM_MARGIN = 40px
```

---

## 3. Element Hierarchy

### 3.1 Parent-Child Relationships

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
└── Cross-Lane Edges (parent="1")  ← CRITICAL: Must be at root level
```

### 3.2 Critical Rule: Cross-Lane Connections

**Edges that cross lane boundaries MUST have `parent="1"` (root level)**, not the lane they originate from. This ensures proper rendering when lanes are moved or resized.

---

## 4. BPMN to Draw.io Shape Mapping

### 4.1 Events

| BPMN Event | Draw.io Style |
|------------|---------------|
| Start Event (Message) | `shape=mxgraph.bpmn.shape;outline=throwing;symbol=message;` |
| Intermediate Event (Message Catch) | `shape=mxgraph.bpmn.shape;outline=catching;symbol=message;` |
| Intermediate Event (Timer) | `shape=mxgraph.bpmn.shape;outline=catching;symbol=timer;` |
| End Event (Terminate) | `shape=mxgraph.bpmn.shape;outline=end;symbol=terminate;` |

**Standard Event Dimensions:** 40x40 pixels

### 4.2 Tasks

| BPMN Task Type | Draw.io Style | Fill Color |
|----------------|---------------|------------|
| User Task | `rounded=1;whiteSpace=wrap;html=1;` | `#fff2cc` (yellow) |
| Service Task | `rounded=1;whiteSpace=wrap;html=1;` | `#e1d5e7` (purple) |
| Manual Task | `rounded=1;whiteSpace=wrap;html=1;` | `#fff2cc` (yellow) |
| Subprocess | `rounded=1;strokeWidth=2;` | `#dae8fc` (blue) |

**Standard Task Dimensions:** 100x50 pixels (or 90x40 for compact)

### 4.3 Gateways

| BPMN Gateway | Draw.io Style |
|--------------|---------------|
| Exclusive (XOR) | `shape=mxgraph.bpmn.gateway2;symbol=exclusiveGw;` |
| Parallel (AND) | `shape=mxgraph.bpmn.gateway2;symbol=parallelGw;` |
| Inclusive (OR) | `shape=mxgraph.bpmn.gateway2;symbol=inclusiveGw;` |

**Standard Gateway Dimensions:** 50x50 pixels

### 4.4 Swim Lanes

```xml
<!-- Pool Container -->
<mxCell id="pool_id" value="Pool Name" 
        style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;startSize=30;" 
        vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="[POOL_WIDTH]" height="[POOL_HEIGHT]" as="geometry"/>
</mxCell>

<!-- Lane within Pool -->
<mxCell id="lane_id" value="Lane Name" 
        style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;startSize=30;" 
        vertex="1" parent="pool_id">
  <mxGeometry x="30" y="[LANE_Y]" width="[LANE_WIDTH]" height="[LANE_HEIGHT]" as="geometry"/>
</mxCell>
```

---

## 5. Layout Standards

### 5.1 Spacing Constants

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

### 5.2 Lane Height Calculation

```
LANE_HEIGHT = max(LANE_MIN_HEIGHT, BRANCH_COUNT * 45 + 60)

Where:
- Single path lane: 100px
- Two branches (e.g., Yes/No): 130px  
- Three branches (e.g., High/Med/Low): 150px
- Four+ branches: 180px+
```

### 5.3 Horizontal Element Placement

**Key Principle:** Start lane-specific content AFTER any incoming cross-lane connections have space to route.

```
If lane receives parallel split input:
  FIRST_ELEMENT_X = 500-600px (leave routing space)
Else:
  FIRST_ELEMENT_X = 60-150px (standard start)
```

### 5.4 Vertical Element Placement Within Lanes

For lanes with branching paths:

```
TWO_BRANCH_LAYOUT:
  Upper path:  y = 5-10px from lane top
  Lower path:  y = LANE_HEIGHT - 45px

THREE_BRANCH_LAYOUT:
  Upper path:  y = 10px
  Middle path: y = (LANE_HEIGHT / 2) - 20px
  Lower path:  y = LANE_HEIGHT - 50px
```

---

## 6. Edge (Connector) Standards

### 6.1 Intra-Lane Edges

```xml
<mxCell id="flow_id" 
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;endArrow=block;endFill=1;" 
        edge="1" parent="lane_id" source="source_id" target="target_id">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### 6.2 Cross-Lane Edges (CRITICAL)

```xml
<!-- Must use parent="1" and absolute coordinates -->
<mxCell id="cross_flow_id" 
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

### 6.3 Message Flows (Between Pools)

```xml
<mxCell id="msg_flow_id" 
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;endArrow=open;endFill=0;dashed=1;dashPattern=8 4;" 
        edge="1" parent="1">
  <!-- Use absolute coordinates -->
</mxCell>
```

### 6.4 Edge Labels

```xml
<mxCell id="labeled_edge" value="Yes" 
        style="edgeStyle=orthogonalEdgeStyle;...">
```

---

## 7. Color Standards

### 7.1 Lane Colors by Function

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

### 7.2 Special Highlighting

| Purpose | Color | Usage |
|---------|-------|-------|
| Loop/Return Flow | `#b85450` (red) | Rework or escalation paths |
| Critical Path | `#000000` (black, strokeWidth=2) | Primary happy path |
| Subprocess | `#dae8fc` (blue, strokeWidth=2) | Collapsed subprocesses |
| Error/Escalation Task | `#f8cecc` | Tasks handling failures |

---

## 8. Conversion Process Checklist

### Phase 1: Analysis
- [ ] Count pools, lanes, tasks, gateways, events
- [ ] Map cross-lane sequence flows
- [ ] Identify parallel splits and joins
- [ ] Note decision points with 3+ branches
- [ ] Calculate required canvas dimensions

### Phase 2: Structure Creation
- [ ] Create XML skeleton with calculated dimensions
- [ ] Define pools with proper heights
- [ ] Define lanes with appropriate heights for branching
- [ ] Set lane colors by function

### Phase 3: Element Placement
- [ ] Place elements lane-by-lane
- [ ] Start lane content after routing space (if parallel input)
- [ ] Vertically separate branching paths
- [ ] Maintain consistent horizontal spacing

### Phase 4: Intra-Lane Connections
- [ ] Connect sequential elements within each lane
- [ ] Add gateway branch labels
- [ ] Create bypass/skip edges with waypoints

### Phase 5: Cross-Lane Connections
- [ ] Create parallel split flows from gateway to each target lane
- [ ] Create parallel join flows from each lane to sync gateway
- [ ] Add message flows between pools
- [ ] Add loop-back/rework flows

### Phase 6: Validation
- [ ] Open in draw.io Desktop
- [ ] Check for overlapping elements
- [ ] Verify all arrows render
- [ ] Confirm labels are readable
- [ ] Test lane resize behavior

---

## 9. Common Issues and Solutions

### Issue 1: Overlapping Elements at Parallel Split

**Symptom:** First tasks in parallel lanes overlap with incoming arrows from the split gateway.

**Solution:** Shift all lane content rightward (x += 400-500px) to leave routing space for the vertical distribution of parallel flows.

### Issue 2: Stacked Elements in Branching Lanes

**Symptom:** Multiple branch targets (e.g., three training tiers) render on top of each other.

**Solution:** 
1. Increase lane height to accommodate branches
2. Explicitly set different y-coordinates for each branch target
3. Use formula: `y = lane_top + (branch_index * vertical_spacing)`

### Issue 3: Cross-Lane Arrows Not Rendering

**Symptom:** Sequence flows that cross lane boundaries don't appear.

**Solution:** Ensure cross-lane edges use `parent="1"` (root) with absolute `mxPoint` coordinates, not relative parent references.

### Issue 4: Edge Labels Overlapping

**Symptom:** Gateway condition labels overlap with other labels or elements.

**Solution:** 
1. Use waypoints to route edges away from congested areas
2. For crowded areas, shorten labels (e.g., "Y" instead of "Yes")
3. Adjust element spacing to create label space

### Issue 5: Lane Labels Cut Off

**Symptom:** Horizontal lane labels don't fully display.

**Solution:** Ensure `startSize=30` in lane style for adequate label width.

---

## 10. Absolute Coordinate Calculation

When creating cross-lane edges, calculate absolute coordinates:

```
ABSOLUTE_X = POOL_X + LANE_X_OFFSET + ELEMENT_X_IN_LANE
ABSOLUTE_Y = POOL_Y + LANE_Y_IN_POOL + ELEMENT_Y_IN_LANE + (ELEMENT_HEIGHT / 2)

Example:
- Pool starts at (40, 40)
- Lane 3 is at y=340 within pool
- Element is at (550, 40) within lane
- Element center Y = 40 + 340 + 40 + 25 = 445 (absolute)
- Element right edge X = 40 + 30 + 550 + 100 = 720 (absolute)
```

---

## 11. Template Snippets

### 11.1 Standard Task

```xml
<mxCell id="task_[NAME]" value="Task&#xa;Description" 
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" 
        vertex="1" parent="[LANE_ID]">
  <mxGeometry x="[X]" y="[Y]" width="100" height="50" as="geometry"/>
</mxCell>
```

### 11.2 Exclusive Gateway with Label

```xml
<mxCell id="gw_[NAME]" value="Decision&#xa;Point?" 
        style="points=[[0.25,0.25,0],[0.5,0,0],[0.75,0.25,0],[1,0.5,0],[0.75,0.75,0],[0.5,1,0],[0.25,0.75,0],[0,0.5,0]];shape=mxgraph.bpmn.gateway2;html=1;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;verticalAlign=top;outline=none;symbol=exclusiveGw;fillColor=#ffffff;strokeColor=#000000;" 
        vertex="1" parent="[LANE_ID]">
  <mxGeometry x="[X]" y="[Y]" width="50" height="50" as="geometry"/>
</mxCell>
```

### 11.3 Cross-Lane Edge Template

```xml
<mxCell id="flow_[SOURCE]_to_[TARGET]" 
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

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-06 | Initial standard based on Enterprise Onboarding Process conversion |

---

## Appendix A: Quick Reference Card

```
DIMENSIONS
├── Task: 100x50 (standard), 90x40 (compact)
├── Gateway: 50x50
├── Event: 40x40
├── Lane Height: 100 (simple), 130 (2-branch), 150 (3-branch)
└── Element Spacing: 140px horizontal, 45px vertical

COLORS (Fill/Stroke)
├── Sales: #dae8fc / #6c8ebf
├── Legal: #d5e8d4 / #82b366
├── Finance: #ffe6cc / #d79b00
├── Security: #f8cecc / #b85450
├── Implementation: #e1d5e7 / #9673a6
└── Task (default): #fff2cc / #d6b656

CRITICAL RULES
├── Cross-lane edges: parent="1" + absolute coordinates
├── Parallel input lanes: Start content at x=500+
├── Branching lanes: Increase height + separate y-coords
└── Label space: Route edges to avoid congestion
```
