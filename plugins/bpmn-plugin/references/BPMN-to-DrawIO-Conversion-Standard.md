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

### 1.3 Pre-Generation Checklist (MANDATORY)

Before writing ANY draw.io XML, complete ALL of these steps:

#### Analysis Complete
- [ ] Counted all pools (participant elements)
- [ ] Counted all lanes per pool
- [ ] Listed all elements per lane with IDs
- [ ] Identified ALL cross-lane sequence flows
- [ ] Identified ALL message flows between pools

#### Coordinate Registry Built
- [ ] All pool absolute positions calculated
- [ ] All lane absolute positions calculated
- [ ] All element absolute positions calculated
- [ ] Registry exported/documented

#### Layout Planned
- [ ] Page dimensions calculated
- [ ] Pool heights accommodate all lanes
- [ ] Lane heights accommodate branching
- [ ] Element spacing verified (no overlaps)

#### Edge Inventory Complete
- [ ] All intra-lane edges listed with source/target IDs
- [ ] All cross-lane edges listed with source/target IDs
- [ ] All message flows listed with source/target IDs
- [ ] Each edge has calculated coordinates from registry

**DO NOT PROCEED** to XML generation until ALL boxes are checked.

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

### 2.3 Coordinate Registry (MANDATORY)

Before generating ANY XML, build a coordinate registry that tracks absolute positions of all elements. This registry is the SINGLE SOURCE OF TRUTH for edge calculations.

#### 2.3.1 Registry Structure

```javascript
const coordinateRegistry = {
  pools: {
    "pool_customer": { x: 40, y: 40, width: 3000, height: 120 },
    "pool_ai_system": { x: 40, y: 180, width: 3000, height: 900 },
    "pool_crm": { x: 40, y: 1100, width: 3000, height: 120 }
  },
  lanes: {
    "lane_ai_automation": {
      poolId: "pool_ai_system",
      relativeY: 0,        // Y within pool (after pool label)
      height: 300,
      absoluteY: 180       // CALCULATED: pool.y + relativeY
    },
    "lane_human_review": {
      poolId: "pool_ai_system",
      relativeY: 300,
      height: 300,
      absoluteY: 480       // CALCULATED: pool.y + relativeY
    }
  },
  elements: {
    "task_normalize": {
      laneId: "lane_ai_automation",
      relativeX: 130,      // X within lane (after lane label)
      relativeY: 125,      // Y within lane
      width: 90,
      height: 50,
      // CALCULATED absolute positions:
      absoluteX: 200,      // pool.x + LANE_LABEL_WIDTH + relativeX
      absoluteY: 305,      // lane.absoluteY + relativeY
      centerX: 245,        // absoluteX + width/2
      centerY: 330,        // absoluteY + height/2
      rightEdgeX: 290,     // absoluteX + width
      bottomEdgeY: 355     // absoluteY + height
    }
  }
};
```

#### 2.3.2 Registry Population Order

1. **First:** Calculate all pool absolute positions
2. **Second:** Calculate all lane absolute positions (depends on pools)
3. **Third:** Calculate all element absolute positions (depends on lanes)
4. **Fourth:** Generate XML using registry values
5. **Fifth:** Calculate edge coordinates from registry

**CRITICAL:** Never hardcode coordinates in XML. Always reference the registry.

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

### 3.3 Lane Position Calculation Table

For a pool with multiple lanes, calculate lane positions systematically:

| Lane | Relative Y (in pool) | Height | Absolute Y |
|------|---------------------|--------|------------|
| Lane 1 | 0 | 300 | POOL_Y + 0 |
| Lane 2 | 300 | 300 | POOL_Y + 300 |
| Lane 3 | 600 | 300 | POOL_Y + 600 |

**Important:** Lane Y coordinates are relative to the pool, NOT the page.

#### Example: 3-Lane Pool

```
Pool "AI System" at y=180, height=900

Lane "AI Automation":
  - y=0 (within pool)
  - height=300
  - absoluteY = 180 + 0 = 180

Lane "Human Review":
  - y=300 (within pool)
  - height=300
  - absoluteY = 180 + 300 = 480

Lane "Specialists":
  - y=600 (within pool)
  - height=300
  - absoluteY = 180 + 600 = 780
```

#### Lane XML with Correct Coordinates

```xml
<!-- Pool -->
<mxCell id="pool_ai" value="AI System" ... parent="1">
  <mxGeometry x="40" y="180" width="3000" height="900"/>
</mxCell>

<!-- Lane 1 - y=0 within pool -->
<mxCell id="lane_ai_auto" value="AI Automation" ... parent="pool_ai">
  <mxGeometry x="30" y="0" width="2970" height="300"/>
</mxCell>

<!-- Lane 2 - y=300 within pool (after Lane 1) -->
<mxCell id="lane_human" value="Human Review" ... parent="pool_ai">
  <mxGeometry x="30" y="300" width="2970" height="300"/>
</mxCell>

<!-- Lane 3 - y=600 within pool (after Lane 2) -->
<mxCell id="lane_specialist" value="Specialists" ... parent="pool_ai">
  <mxGeometry x="30" y="600" width="2970" height="300"/>
</mxCell>
```

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

### 5.5 Subprocess Element Positioning

Subprocesses are containers with their own internal coordinate system.

#### 5.5.1 Subprocess Structure

```
Subprocess (parent = lane_id)
├── mxGeometry defines subprocess position WITHIN LANE
└── Internal elements (parent = subprocess_id)
    └── mxGeometry defines position WITHIN SUBPROCESS
```

#### 5.5.2 Internal Element Coordinates

Elements inside a subprocess use coordinates RELATIVE TO THE SUBPROCESS, not the lane:

```xml
<!-- Subprocess container -->
<mxCell id="subprocess_response" value="AI Response Generation"
        style="swimlane;horizontal=1;rounded=1;..."
        vertex="1" parent="lane_ai_automation">
  <mxGeometry x="1260" y="30" width="420" height="120" as="geometry"/>
</mxCell>

<!-- Internal start event - coordinates relative to subprocess -->
<mxCell id="sub_start" value=""
        style="ellipse;..."
        vertex="1" parent="subprocess_response">
  <mxGeometry x="15" y="50" width="25" height="25" as="geometry"/>
  <!-- This places the event at (15,50) INSIDE the subprocess -->
</mxCell>
```

#### 5.5.3 Absolute Position of Subprocess Internal Elements

To calculate absolute position of an element inside a subprocess:

```
ABSOLUTE_X = POOL_X + POOL_LABEL + LANE_LABEL + SUBPROCESS_X + ELEMENT_X_IN_SUBPROCESS
ABSOLUTE_Y = POOL_Y + LANE_Y + SUBPROCESS_Y + SUBPROCESS_HEADER + ELEMENT_Y_IN_SUBPROCESS

Where:
- SUBPROCESS_HEADER = 25px (the title bar of the subprocess)
```

#### 5.5.4 Subprocess Sizing

Ensure subprocess is large enough for internal content:

```
SUBPROCESS_WIDTH = INTERNAL_FLOW_LENGTH + LEFT_PADDING + RIGHT_PADDING
SUBPROCESS_HEIGHT = SUBPROCESS_HEADER + MAX_ELEMENT_HEIGHT + TOP_PADDING + BOTTOM_PADDING

Minimums:
- WIDTH: 300px for 3-4 internal elements
- HEIGHT: 100px for single-row flow
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

### 6.4 Edge Labels (IMPORTANT)

#### 6.4.1 Correct: Label as Edge Value

Labels should be part of the edge's `value` attribute:

```xml
<mxCell id="flow_yes" value="Yes"
        style="edgeStyle=orthogonalEdgeStyle;..."
        edge="1" parent="lane_id" source="gw_id" target="task_id">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

#### 6.4.2 INCORRECT: Label as Separate Element

**DO NOT** create labels as separate text elements:

```xml
<!-- WRONG - Creates floating label that won't move with edge -->
<mxCell id="label_yes" value="Yes"
        style="text;html=1;..."
        vertex="1" parent="lane_id">
  <mxGeometry x="500" y="200" width="30" height="20"/>
</mxCell>
```

#### 6.4.3 Label Positioning

Control label position with style attributes:

```xml
<!-- Label at middle of edge (default) -->
style="...;labelPosition=center;verticalLabelPosition=middle;"

<!-- Label near source -->
style="...;labelPosition=left;align=right;"

<!-- Label near target -->
style="...;labelPosition=right;align=left;"

<!-- Label offset from edge -->
style="...;labelBackgroundColor=#ffffff;spacingTop=5;"
```

#### 6.4.4 Multiple Labels (Gateway Branches)

For gateways with multiple outgoing edges, each edge gets its own label:

```xml
<!-- Yes branch -->
<mxCell id="flow_gw_yes" value="Yes" .../>

<!-- No branch -->
<mxCell id="flow_gw_no" value="No" .../>

<!-- Default branch (no label needed) -->
<mxCell id="flow_gw_default" value="" .../>
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

### Phase 5.5: Edge Validation (MANDATORY before Phase 6)

For EVERY edge in the diagram, verify:

- [ ] **Source Exists:** Source element ID exists in coordinate registry
- [ ] **Target Exists:** Target element ID exists in coordinate registry
- [ ] **Coordinates Calculated:** Both source and target absolute coordinates are computed
- [ ] **Parent Correct:**
  - Intra-lane edges: `parent="[lane_id]"`
  - Cross-lane edges: `parent="1"`
- [ ] **Connection Points Valid:** Edge connects to element edge, not center
- [ ] **Waypoints Logical:** Waypoints create orthogonal (right-angle) paths
- [ ] **No Orphan Labels:** Edge labels are in `value` attribute, not separate text elements

#### Validation Script (Pseudocode)

```javascript
function validateEdge(edge, registry) {
  const errors = [];

  // Check source
  if (!registry.elements[edge.sourceId]) {
    errors.push(`Source element '${edge.sourceId}' not found in registry`);
  }

  // Check target
  if (!registry.elements[edge.targetId]) {
    errors.push(`Target element '${edge.targetId}' not found in registry`);
  }

  // Check parent for cross-lane
  const sourceLane = registry.elements[edge.sourceId]?.laneId;
  const targetLane = registry.elements[edge.targetId]?.laneId;
  if (sourceLane !== targetLane && edge.parent !== "1") {
    errors.push(`Cross-lane edge must have parent="1", found parent="${edge.parent}"`);
  }

  // Check coordinates are numbers
  if (isNaN(edge.sourceX) || isNaN(edge.sourceY)) {
    errors.push(`Invalid source coordinates: (${edge.sourceX}, ${edge.sourceY})`);
  }

  return errors;
}
```

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

### 9.6 Common Mistakes to Avoid

#### Mistake 1: Using Relative Coordinates for Cross-Lane Edges

**WRONG:**
```xml
<mxCell id="cross_edge" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <!-- These are lane-relative, not page-absolute! -->
    <mxPoint x="940" y="150" as="sourcePoint"/>
    <mxPoint x="925" y="125" as="targetPoint"/>
  </mxGeometry>
</mxCell>
```

**RIGHT:**
```xml
<mxCell id="cross_edge" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <!-- Calculated absolute coordinates -->
    <mxPoint x="1065" y="355" as="sourcePoint"/>
    <mxPoint x="1075" y="605" as="targetPoint"/>
  </mxGeometry>
</mxCell>
```

#### Mistake 2: Forgetting Pool/Lane Label Offsets

**WRONG:** Element at x=100 in lane
```
Absolute X = 40 + 100 = 140  // Missing label offsets!
```

**RIGHT:**
```
Absolute X = 40 + 30 + 30 + 100 = 200  // Pool label + Lane label + element X
```

#### Mistake 3: Creating Orphan Labels

**WRONG:** Separate text element for edge label
```xml
<mxCell id="label_g1" value="G1" style="text;..." vertex="1"/>
```

**RIGHT:** Label as edge value attribute
```xml
<mxCell id="flow_g1" value="G1" style="edge;..." edge="1"/>
```

#### Mistake 4: Inconsistent Parent References

**WRONG:** Cross-lane edge with lane parent
```xml
<mxCell id="cross_edge" edge="1" parent="lane_ai_automation">
```

**RIGHT:** Cross-lane edge with root parent
```xml
<mxCell id="cross_edge" edge="1" parent="1">
```

#### Mistake 5: Missing Waypoints for Orthogonal Routing

**WRONG:** Direct diagonal line (won't render as BPMN flow)
```xml
<mxCell id="edge">
  <mxGeometry>
    <mxPoint x="100" y="100" as="sourcePoint"/>
    <mxPoint x="500" y="400" as="targetPoint"/>
    <!-- No waypoints = diagonal line -->
  </mxGeometry>
</mxCell>
```

**RIGHT:** Orthogonal routing with waypoints
```xml
<mxCell id="edge">
  <mxGeometry>
    <mxPoint x="100" y="100" as="sourcePoint"/>
    <mxPoint x="500" y="400" as="targetPoint"/>
    <Array as="points">
      <mxPoint x="300" y="100"/>  <!-- Horizontal first -->
      <mxPoint x="300" y="400"/>  <!-- Then vertical -->
    </Array>
  </mxGeometry>
</mxCell>
```

#### Mistake 6: Not Connecting All Flow Elements

**WRONG:** Tasks created but not wired into sequence flow
```xml
<mxCell id="task_quality_audit" ... />
<!-- No edge connecting to or from this task -->
```

**RIGHT:** Every task has incoming and outgoing edges (except start/end events)
```xml
<mxCell id="task_quality_audit" ... />
<mxCell id="flow_to_audit" ... target="task_quality_audit" />
<mxCell id="flow_from_audit" ... source="task_quality_audit" />
```

---

## 10. Absolute Coordinate Calculation (CRITICAL)

### 10.1 The Five Offset Components

Every element position involves FIVE cumulative offsets:

```
┌─────────────────────────────────────────────────────────────┐
│ PAGE                                                         │
│  ┌─ POOL_X (40px) ─────────────────────────────────────────┐│
│  │ POOL                                                     ││
│  │  ┌─ POOL_LABEL_WIDTH (30px) ────────────────────────────┐││
│  │  │ LANE                                                  │││
│  │  │  ┌─ LANE_LABEL_WIDTH (30px) ─────────────────────────┐│││
│  │  │  │ CONTENT AREA                                       ││││
│  │  │  │  ┌─ ELEMENT_X ──┐                                  ││││
│  │  │  │  │   ELEMENT    │                                  ││││
│  │  │  │  └──────────────┘                                  ││││
```

### 10.2 Absolute X Calculation

```
ABSOLUTE_X = POOL_X + POOL_LABEL_WIDTH + LANE_LABEL_WIDTH + ELEMENT_X_IN_LANE

Where:
- POOL_X = 40 (constant for leftmost pool)
- POOL_LABEL_WIDTH = 30 (the vertical "Pool Name" label area)
- LANE_LABEL_WIDTH = 30 (the vertical "Lane Name" label area)
- ELEMENT_X_IN_LANE = element's x coordinate within the lane content area

SIMPLIFIED: ABSOLUTE_X = 40 + 30 + 30 + ELEMENT_X_IN_LANE = 100 + ELEMENT_X_IN_LANE
```

### 10.3 Absolute Y Calculation

```
ABSOLUTE_Y = POOL_Y + LANE_Y_IN_POOL + ELEMENT_Y_IN_LANE

Where:
- POOL_Y = vertical position of pool on page
- LANE_Y_IN_POOL = lane's y position within pool (0 for first lane)
- ELEMENT_Y_IN_LANE = element's y coordinate within the lane
```

### 10.4 Edge Connection Points

For edges, calculate the CONNECTION POINT, not the element corner:

```
SOURCE_RIGHT_CENTER:
  x = ABSOLUTE_X + ELEMENT_WIDTH
  y = ABSOLUTE_Y + (ELEMENT_HEIGHT / 2)

TARGET_LEFT_CENTER:
  x = ABSOLUTE_X
  y = ABSOLUTE_Y + (ELEMENT_HEIGHT / 2)

SOURCE_BOTTOM_CENTER (for downward cross-lane):
  x = ABSOLUTE_X + (ELEMENT_WIDTH / 2)
  y = ABSOLUTE_Y + ELEMENT_HEIGHT

TARGET_TOP_CENTER (for downward cross-lane):
  x = ABSOLUTE_X + (ELEMENT_WIDTH / 2)
  y = ABSOLUTE_Y
```

### 10.5 Worked Example: Cross-Lane Edge

**Scenario:** Edge from "Confidence Gateway" in AI Automation Lane to "Human Verification Queue" in Human Review Lane.

**Given:**
- Pool "AI System" at (40, 180)
- Lane "AI Automation" at y=0 within pool, height=300
- Lane "Human Review" at y=300 within pool, height=300
- Gateway in AI Automation at (940, 125) within lane, size 50x50
- Task in Human Review at (925, 125) within lane, size 100x50

**Calculate Gateway (source) absolute position:**
```
Gateway.absoluteX = 40 + 30 + 30 + 940 = 1040
Gateway.absoluteY = 180 + 0 + 125 = 305
Gateway.centerX = 1040 + 25 = 1065
Gateway.centerY = 305 + 25 = 330
Gateway.bottomCenter = (1065, 355)  // Exit point for downward edge
```

**Calculate Task (target) absolute position:**
```
Task.absoluteX = 40 + 30 + 30 + 925 = 1025
Task.absoluteY = 180 + 300 + 125 = 605
Task.centerX = 1025 + 50 = 1075
Task.centerY = 605 + 25 = 630
Task.topCenter = (1075, 605)  // Entry point for downward edge
```

**Edge XML:**
```xml
<mxCell id="flow_confidence_to_verify" value="<70%"
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#d6b656;endArrow=block;endFill=1;"
        edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="1065" y="355" as="sourcePoint"/>
    <mxPoint x="1075" y="605" as="targetPoint"/>
    <Array as="points">
      <mxPoint x="1065" y="480"/>
      <mxPoint x="1075" y="480"/>
    </Array>
  </mxGeometry>
</mxCell>
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
| 1.1 | 2026-01-12 | Added 9 sections based on AI Community Management Process conversion failure: Pre-Generation Checklist (1.3), Coordinate Registry (2.3), Lane Position Calculation (3.3), Subprocess Positioning (5.5), Edge Labels expanded (6.4), Edge Validation (8.5), Common Mistakes (9.6), Absolute Coordinate Calculation expanded (10), Quick Reference Card expanded (Appendix A) |

---

## Appendix A: Quick Reference Card

```
COORDINATE OFFSETS (MEMORIZE THESE)
├── POOL_X = 40px (from page left)
├── POOL_LABEL_WIDTH = 30px (vertical pool name)
├── LANE_LABEL_WIDTH = 30px (vertical lane name)
├── LANE_X_START = 30px (lane content starts here within pool)
└── TOTAL_X_OFFSET = 100px (40 + 30 + 30 = element absolute X base)

ABSOLUTE COORDINATE FORMULAS
├── Element Absolute X = 40 + 30 + 30 + element.x = 100 + element.x
├── Element Absolute Y = pool.y + lane.relativeY + element.y
├── Element Center X = absoluteX + (width / 2)
├── Element Center Y = absoluteY + (height / 2)
├── Right Edge X = absoluteX + width
└── Bottom Edge Y = absoluteY + height

EDGE PARENT RULES
├── Same lane: parent="[lane_id]", can use source/target attributes
├── Cross-lane: parent="1", MUST use mxPoint absolute coordinates
└── Cross-pool: parent="1", MUST use mxPoint absolute coordinates

EDGE CONNECTION POINTS
├── Horizontal flow: right-center of source → left-center of target
├── Downward cross-lane: bottom-center of source → top-center of target
├── Upward cross-lane: top-center of source → bottom-center of target
└── Always add waypoints for orthogonal (90°) routing

DIMENSIONS
├── Task: 100x50 (standard), 90x40 (compact)
├── Gateway: 50x50
├── Event: 40x40
├── Subprocess: min 300x100, header 25px
├── Lane Height: 100 (simple), 130 (2-branch), 150+ (3+ branch)
└── Element Spacing: 140px horizontal, 45px vertical

VALIDATION CHECKLIST (BEFORE SAVING)
├── [ ] Coordinate registry built for all elements
├── [ ] All cross-lane edges use parent="1"
├── [ ] All cross-lane edges use mxPoint (not source/target)
├── [ ] All edge labels are in value attribute (not separate text)
├── [ ] All waypoints create orthogonal (90°) paths
├── [ ] Every task has incoming AND outgoing edges
├── [ ] Registry coordinates match generated XML
└── [ ] Opened in draw.io and visually verified
```
