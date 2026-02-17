# BPMN2DrawIO Visual Testing Report

**Date:** 2026-01-16
**Converter Version:** 0.4.2
**Test Suite:** 6 comprehensive visual stress tests

---

## Executive Summary

Visual testing of the bpmn2drawio converter revealed **2 critical bugs** that significantly impact usability, along with several medium-severity layout issues. The converter successfully handles basic lane structures and cross-lane flows, but fails on subprocess internal rendering and has inconsistent pool boundary rendering.

### Overall Results

| Test ID | File | Status | Critical Issues |
|---------|------|--------|-----------------|
| ML-03 | test_ml_03_many_lanes | Pass with issues | 0 |
| CF-03 | test_cf_03_criss_cross_messages | **FAIL** | 1 (Pool boundaries) |
| GW-04 | test_gw_04_nested_gateways | **FAIL** | 1 (Disconnected element) |
| SP-04 | test_sp_04_subprocess_gateway | **FAIL** | 1 (Empty subprocess) |
| CR-05 | test_cr_05_cross_lane_flows | **PASS** | 0 |
| Combined | test_combined_complex | **FAIL** | 1 (Empty subprocess) |

**Summary:** 2 of 6 tests passed. 4 tests have critical issues requiring code fixes.

---

## Critical Bugs Identified

### BUG-001: Subprocess Internal Elements Not Rendered

**Severity:** CRITICAL
**Affected Tests:** SP-04, Combined Complex
**Impact:** Subprocesses appear as empty boxes, losing all internal workflow detail

**Description:**
When a BPMN file contains a subprocess with internal elements (start events, tasks, gateways, end events, and internal flows), the converter creates the subprocess container box but **does not render any of the internal elements**. The subprocess appears completely empty.

**Expected Behavior:**
- Subprocess box should contain all child elements
- Internal flows should connect elements within the subprocess
- Subprocess should expand to fit internal content

**Actual Behavior:**
- Subprocess box renders as an empty rectangle
- All internal elements (8 in SP-04, 5 in Combined) are missing
- Internal sequence flows are not rendered

**Files Affected:**
- `generator.py` - subprocess cell creation
- `layout.py` - subprocess internal layout
- `position_resolver.py` - child element positioning

**Reproduction:**
```bash
bpmn2drawio tests/visual/test_sp_04_subprocess_gateway.bpmn output.drawio
# Open output.drawio - subprocess "Validation Subprocess" will be empty
```

---

### BUG-002: Pool Rectangular Boundaries Not Rendering (Inconsistent)

**Severity:** CRITICAL
**Affected Tests:** CF-03
**Impact:** Pools appear as floating elements without container structure

**Description:**
In the criss-cross message flow test (2 pools), the pools did not render with visible rectangular boundaries. Elements appeared to float in space without clear pool containment. This bug appears intermittent - the Combined Complex test rendered pools correctly.

**Expected Behavior:**
- Pools should have visible rectangular borders
- Pool header with name should be visible
- All pool contents should be visually contained

**Actual Behavior:**
- Pool boundaries invisible (CF-03)
- Elements float without containment
- Message flows connect correctly but pool structure lost

**Possible Cause:**
May be related to pool-only diagrams (no lanes) vs pool-with-lanes diagrams.

---

### BUG-003: Elements Can Become Disconnected During Layout

**Severity:** HIGH
**Affected Tests:** GW-04
**Impact:** Elements lose their sequence flow connections

**Description:**
In the nested gateways test, the element "B2 Parallel Task" appeared completely disconnected from the flow. No incoming or outgoing connections were visible, despite the BPMN defining proper sequence flows.

**Expected Behavior:**
- All elements connected as defined in BPMN
- Graphviz layout should preserve connections

**Actual Behavior:**
- Element rendered but isolated
- Flows that should connect to it are missing

---

## Test-by-Test Results

### Test ML-03: Many Lanes (5 Lanes)

**File:** test_ml_03_many_lanes.bpmn
**Purpose:** Test layout with 5 horizontal lanes in single pool

**Results:**
- Pool boundary: Visible ✓
- Lane headers: Visible ✓
- Lane separation: Correct ✓
- Element placement: Mostly correct ✓
- Flow routing: Some awkward crossings

**Issues:**
| # | Type | Severity | Description |
|---|------|----------|-------------|
| 1 | Routing | Medium | Flow lines cross lanes at awkward angles |
| 2 | Alignment | Low | Elements not perfectly horizontally aligned |

**Screenshot Observations:**
Elements were correctly assigned to their lanes. The 5-lane structure rendered properly with visible lane boundaries. Flow routing between lanes worked but used diagonal paths rather than clean orthogonal routing in some cases.

---

### Test CF-03: Criss-Cross Message Flows

**File:** test_cf_03_criss_cross_messages.bpmn
**Purpose:** Test 2 pools with 4 criss-crossing message flows

**Results:**
- Pool boundary: **NOT VISIBLE** ✗
- Pool header: Not rendered properly ✗
- Message flows: Rendered ✓
- Element placement: Floating without containment ✗

**Issues:**
| # | Type | Severity | Description |
|---|------|----------|-------------|
| 1 | Pool Rendering | **CRITICAL** | Pool rectangular boundaries not rendered |
| 2 | Structure | High | Elements appear to float without pool containment |
| 3 | Layout | Medium | Without pool boundaries, diagram structure unclear |

**Screenshot Observations:**
This was the worst-performing test. The two pools ("System A" and "System B") did not render as visible rectangular containers. All elements were present but appeared scattered in space. Message flows connected elements across where pools should be, but the lack of pool boundaries made the diagram confusing and unprofessional.

---

### Test GW-04: Nested Gateways (3 Levels)

**File:** test_gw_04_nested_gateways.bpmn
**Purpose:** Test deeply nested gateway structure (XOR→Parallel→XOR)

**Results:**
- Gateway symbols: Visible ✓
- Nesting hierarchy: Partially visible
- All elements connected: **NO** ✗
- Layout clarity: Poor

**Issues:**
| # | Type | Severity | Description |
|---|------|----------|-------------|
| 1 | Connectivity | **CRITICAL** | "B2 Parallel Task" completely disconnected |
| 2 | Layout | High | Gateway hierarchy creates confusing zigzag pattern |
| 3 | Routing | Medium | Nested branches overlap visually |

**Screenshot Observations:**
The nested gateway structure caused layout difficulties. While most gateways and tasks rendered, one element ("B2 Parallel Task") was completely isolated with no visible connections. The graphviz layout struggled to create a clear visual hierarchy, resulting in a confusing zigzag pattern rather than clean parallel branches.

---

### Test SP-04: Subprocess with Internal Gateway

**File:** test_sp_04_subprocess_gateway.bpmn
**Purpose:** Test subprocess containing gateway with boundary events

**Results:**
- Subprocess box: Visible ✓
- Subprocess interior: **EMPTY** ✗
- Boundary events: Attached correctly ✓
- Main process flow: Correct ✓

**Issues:**
| # | Type | Severity | Description |
|---|------|----------|-------------|
| 1 | Subprocess | **CRITICAL** | All 8 internal elements missing from subprocess |
| 2 | Content Loss | **CRITICAL** | Internal gateway and validation tasks not rendered |

**Screenshot Observations:**
The subprocess "Validation Subprocess" rendered as a visible blue rectangle with boundary events (timer, error) correctly attached to its border. However, the interior was completely empty. The BPMN defines 8 internal elements (SubStart, SubTask_Load, SubGW_Split, SubTask_ValidA/B/C, SubGW_Join, SubTask_Save, SubEnd) and 10 internal flows - none of which appeared in the output.

---

### Test CR-05: Cross-Lane Flows (Best Result)

**File:** test_cr_05_cross_lane_flows.bpmn
**Purpose:** Test flows that traverse multiple lanes

**Results:**
- Pool boundary: Visible ✓
- 4 lanes: All visible ✓
- Cross-lane flows: Working correctly ✓
- Element placement: Correct ✓
- Lane 4→Lane 1 flow: Renders correctly ✓

**Issues:**
| # | Type | Severity | Description |
|---|------|----------|-------------|
| 1 | Routing | Low | Some flow lines could be more direct |

**Screenshot Observations:**
This was the **best performing test**. The single pool with 4 lanes rendered perfectly. All lane headers were visible. Elements were correctly positioned within their assigned lanes. Most importantly, the cross-lane flows (including the long Lane 4→Lane 1 return flow that crosses all lanes) rendered correctly with proper orthogonal routing.

---

### Test Combined Complex: Ultimate Stress Test

**File:** test_combined_complex.bpmn
**Purpose:** Test all features combined (2 pools, 3 lanes, subprocess, gateways, message flows, loops)

**Results:**
- 2 pools: Visible ✓
- 3 lanes in main pool: Visible ✓
- Subprocess interior: **EMPTY** ✗
- Boundary events: Visible ✓
- Cross-pool message flows: Present ✓
- Parallel gateway flow: Present ✓

**Issues:**
| # | Type | Severity | Description |
|---|------|----------|-------------|
| 1 | Subprocess | **CRITICAL** | "Order Fulfillment" subprocess interior empty |
| 2 | Layout | Medium | External Partner pool elements scattered |
| 3 | Routing | Medium | Some flow routing paths are awkward |

**Screenshot Observations:**
Mixed results. Pool and lane structure rendered correctly (unlike CF-03). Boundary events attached to subprocess visible. Cross-pool message flows connecting the two pools were present. However, the subprocess bug persisted - "Order Fulfillment" was an empty box. The External Partner System pool had elements but layout was less clean than expected.

---

## Issues by Category

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Subprocess Rendering | 2 | 0 | 0 | 0 | 2 |
| Pool Rendering | 1 | 1 | 0 | 0 | 2 |
| Element Connectivity | 1 | 0 | 0 | 0 | 1 |
| Flow Routing | 0 | 0 | 4 | 2 | 6 |
| Layout Clarity | 0 | 1 | 2 | 1 | 4 |
| **TOTAL** | **4** | **2** | **6** | **3** | **15** |

---

## Recommended Fixes (Priority Order)

### Priority 1: Fix Subprocess Internal Rendering

**Files to investigate:**
- `generator.py` - `_create_subprocess_cell()` or similar
- `layout.py` - subprocess child positioning
- `converter.py` - subprocess element traversal

**Fix approach:**
1. Ensure subprocess child elements are extracted from BPMN
2. Position children relative to subprocess container
3. Scale subprocess container to fit children
4. Route internal flows within subprocess bounds

### Priority 2: Ensure Pool Boundaries Always Render

**Files to investigate:**
- `swimlanes.py` - pool cell creation
- `generator.py` - pool styling

**Fix approach:**
1. Investigate why CF-03 pools didn't render boundaries
2. Check if pool-only (no lanes) vs pool-with-lanes behaves differently
3. Ensure pool container cells always have visible stroke/border

### Priority 3: Fix Disconnected Elements

**Files to investigate:**
- `layout.py` - graphviz node positioning
- `routing.py` - edge routing

**Fix approach:**
1. Add validation that all edges in BPMN create visible flows
2. Check for edge cases in graphviz layout causing node isolation
3. Add fallback positioning for orphaned nodes

### Priority 4: Improve Flow Routing

**Files to investigate:**
- `routing.py` - orthogonal routing algorithm
- `waypoints.py` - waypoint calculation

**Fix approach:**
1. Prefer orthogonal (right-angle) routing over diagonal
2. Improve cross-lane flow routing to be cleaner
3. Reduce unnecessary waypoints that create zigzag patterns

---

## Test File Locations

All test files are located in:
```text
plugins/bpmn-plugin/tools/bpmn2drawio/tests/visual/
```

**Input files (.bpmn):**
- test_ml_03_many_lanes.bpmn
- test_cf_03_criss_cross_messages.bpmn
- test_gw_04_nested_gateways.bpmn
- test_sp_04_subprocess_gateway.bpmn
- test_cr_05_cross_lane_flows.bpmn
- test_combined_complex.bpmn

**Output files (.drawio):**
```text
plugins/bpmn-plugin/tools/bpmn2drawio/tests/visual/output/
```

---

## Conclusion

The bpmn2drawio converter shows promise for basic BPMN diagrams with lanes and cross-lane flows (CR-05 was excellent). However, **critical bugs prevent production use**:

1. **Subprocess rendering is completely broken** - internal elements are lost
2. **Pool rendering is inconsistent** - sometimes boundaries don't appear
3. **Complex layouts can disconnect elements** - breaking diagram correctness

The highest priority fix is subprocess rendering, as this is a core BPMN feature. Pool boundaries should be addressed next. Once these critical issues are resolved, the converter would be suitable for most business process diagrams.

---

## Appendix: Test Case Matrix Reference

| Test ID | Category | Description | Key Stress Points |
|---------|----------|-------------|-------------------|
| ML-03 | Multiple Lanes | Single pool, 5 lanes | Many parallel lanes, cross-lane assignment |
| CF-03 | Message Flows | 2 pools, criss-cross messages | Cross-pool routing, overlapping flows |
| GW-04 | Gateways | 3 levels nested | Deep nesting, rank assignment |
| SP-04 | Subprocesses | Gateway + boundaries | Nested complexity, boundary events |
| CR-05 | Routing | 4 lanes, cross-lane flows | Orthogonal routing, lane traversal |
| Combined | All Features | Everything combined | Ultimate stress test |
