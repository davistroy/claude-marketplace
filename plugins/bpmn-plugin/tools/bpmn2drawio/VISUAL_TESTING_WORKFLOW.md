# BPMN2DrawIO Visual Testing Workflow

## Overview

This workflow provides a systematic approach to visually test the bpmn2drawio converter's graphviz layout functionality using app.diagrams.net. The goal is to identify and fix visual issues such as overlapping elements, misaligned connectors, incorrect lane positioning, and other layout problems.

## Prerequisites

1. **Python environment** with bpmn2drawio installed:
   ```bash
   cd plugins/bpmn-plugin/tools/bpmn2drawio
   pip install -e ".[graphviz]"
   ```

2. **Graphviz** installed (for automatic layout):
   ```bash
   # Windows
   choco install graphviz
   ```

3. **Browser** with access to https://app.diagrams.net/

## Workflow Automation Notes

This workflow is **semi-automated**:
- **Automated**: Test file creation, BPMN conversion, screenshot capture, issue analysis
- **Manual**: File upload to diagrams.net (OS file dialogs cannot be automated)

**File Upload Process:**
1. Claude navigates to app.diagrams.net
2. Claude opens Diagram → Import from → Device...
3. **YOU** select the .drawio file from the file picker dialog
4. Claude takes screenshots and analyzes the result

---

## Test Case Matrix

### Category 1: Multiple Lanes/Pools

| Test ID | Description | Key Stress Points |
|---------|-------------|-------------------|
| ML-01 | 2 pools, 2 lanes each | Basic pool/lane hierarchy |
| ML-02 | 3 pools, varying lane counts (1, 3, 2) | Uneven lane distribution |
| ML-03 | Single pool, 5 lanes | Many parallel lanes |
| ML-04 | Nested elements across all lanes | Lane assignment and positioning |

### Category 2: Cross-Lane Message Flows

| Test ID | Description | Key Stress Points |
|---------|-------------|-------------------|
| CF-01 | Message flow between adjacent pools | Basic cross-pool routing |
| CF-02 | Message flow from lane to different pool | Cross-lane cross-pool |
| CF-03 | Multiple message flows (criss-cross pattern) | Overlapping flow lines |
| CF-04 | Message flow to subprocess in another pool | Complex target resolution |

### Category 3: Gateways

| Test ID | Description | Key Stress Points |
|---------|-------------|-------------------|
| GW-01 | Parallel gateway 4-way split/join | Symmetric branching |
| GW-02 | Exclusive gateway with 3 paths + default | Asymmetric branching |
| GW-03 | Inclusive gateway with conditional paths | Multiple path activation |
| GW-04 | Nested gateways (3 levels deep) | Deep nesting layout |
| GW-05 | Event-based gateway with timer + message | Special gateway type |
| GW-06 | Diamond pattern (XOR split -> XOR join) | Classic BPMN pattern |

### Category 4: Subprocesses

| Test ID | Description | Key Stress Points |
|---------|-------------|-------------------|
| SP-01 | Simple subprocess with 3 internal tasks | Basic subprocess layout |
| SP-02 | Subprocess spanning multiple ranks | Wide subprocess |
| SP-03 | Multiple subprocesses in sequence | Sequential containers |
| SP-04 | Subprocess with internal gateway | Nested complexity |

### Category 5: Boundary Events

| Test ID | Description | Key Stress Points |
|---------|-------------|-------------------|
| BE-01 | Timer boundary on task | Basic boundary placement |
| BE-02 | Error boundary on subprocess | Boundary on container |
| BE-03 | Multiple boundaries on one element | Boundary stacking |
| BE-04 | Non-interrupting boundary events | Different boundary types |

### Category 6: Complex Routing Patterns

| Test ID | Description | Key Stress Points |
|---------|-------------|-------------------|
| CR-01 | Loop back to previous task | Backward flow |
| CR-02 | Long sequence (10+ tasks) | Horizontal span |
| CR-03 | Merge from 5 different sources | Fan-in pattern |
| CR-04 | Split to 5 different targets | Fan-out pattern |
| CR-05 | Cross-lane sequence flows | Flows between lanes |

---

## Test BPMN Files to Create

### File: test_ml_03_many_lanes.bpmn
```
Purpose: Test layout with 5 lanes in single pool
Features:
- 1 pool "Order Processing"
- 5 lanes: Customer, Sales, Warehouse, Shipping, Finance
- Tasks distributed across all lanes
- Sequence flows crossing multiple lanes
- NO DI coordinates (forces graphviz layout)
```

### File: test_cf_03_criss_cross_messages.bpmn
```
Purpose: Test overlapping message flow routing
Features:
- 2 pools: "System A" and "System B"
- 4 message flows creating X pattern
- Sequence flows within each pool
- Tests edge routing collision avoidance
```

### File: test_gw_04_nested_gateways.bpmn
```
Purpose: Test deep gateway nesting
Features:
- Start -> XOR -> (Parallel -> (XOR -> tasks) ) -> Merge -> End
- 3 levels of nested gateways
- Tests rank assignment and spacing
```

### File: test_sp_04_subprocess_gateway.bpmn
```
Purpose: Test subprocess with internal complexity
Features:
- Main flow with subprocess
- Subprocess contains: Start -> XOR -> 3 tasks -> XOR -> End
- Boundary timer on subprocess
- Tests nested layout boundaries
```

### File: test_cr_05_cross_lane_flows.bpmn
```
Purpose: Test flows that traverse multiple lanes
Features:
- 4 lanes in single pool
- Tasks in lanes 1, 2, 3, 4
- Flows: Lane1->Lane3, Lane2->Lane4, Lane3->Lane1
- Tests orthogonal routing across swimlanes
```

### File: test_combined_complex.bpmn
```
Purpose: Ultimate stress test combining all features
Features:
- 2 pools, 3 lanes in first pool
- Subprocesses with boundary events
- Parallel and exclusive gateways
- Cross-pool message flows
- Loop back flows
- 40+ elements total
```

---

## Execution Workflow

### Phase 1: Generate Test Files

**Prompt for Claude:**
```
Create the BPMN test file test_ml_03_many_lanes.bpmn in
plugins/bpmn-plugin/tools/bpmn2drawio/tests/visual/

Requirements:
- Single pool named "Order Processing"
- 5 horizontal lanes: Customer, Sales, Warehouse, Shipping, Finance
- At least 2 tasks per lane (10 tasks minimum)
- Sequence flows that cross at least 2 lanes
- Start event in Customer lane, End event in Finance lane
- DO NOT include any bpmndi:BPMNDiagram section (no DI coordinates)
- Use proper BPMN 2.0 XML structure with lane flowNodeRef elements
```

### Phase 2: Convert to DrawIO

**Command:**
```bash
cd plugins/bpmn-plugin/tools/bpmn2drawio
bpmn2drawio tests/visual/test_ml_03_many_lanes.bpmn tests/visual/output/test_ml_03_many_lanes.drawio --verbose
```

**Prompt for Claude:**
```
Run the bpmn2drawio converter on all test files in tests/visual/:

For each .bpmn file:
1. Run: bpmn2drawio tests/visual/{file}.bpmn tests/visual/output/{file}.drawio --verbose
2. Record the output (element count, flow count, any warnings)
3. If conversion fails, record the error
```

### Phase 3: Visual Inspection

**Prompt for Claude:**
```
Open the converted DrawIO file in app.diagrams.net and take a screenshot.

Steps:
1. Navigate to https://app.diagrams.net/
2. Click "Open Existing Diagram" or use File > Open
3. Upload the file: tests/visual/output/test_ml_03_many_lanes.drawio
4. Wait for diagram to render
5. Zoom to fit entire diagram in view
6. Take a screenshot

Then analyze the screenshot for these issues:
- Elements overlapping other elements
- Flow lines crossing through elements (not around)
- Flow lines overlapping each other without clear routing
- Elements positioned outside their assigned lane
- Lanes with incorrect heights (not fitting content)
- Pool header not visible or incorrectly sized
- Gateway symbols missing or incorrectly placed
- Connector arrows missing or pointing wrong direction
- Labels overlapping elements or each other
- Inconsistent spacing between elements
```

### Phase 4: Document Findings

**Issue Report Template:**
```markdown
## Visual Test Report: {Test ID}

**File:** {filename}.bpmn → {filename}.drawio
**Conversion Status:** Success/Failed
**Element Count:** X
**Flow Count:** Y

### Screenshot
[Attached or described]

### Issues Found

| Issue # | Type | Description | Severity | Location |
|---------|------|-------------|----------|----------|
| 1 | Overlap | Task A overlaps Task B | High | Lane 2 |
| 2 | Routing | Flow crosses through gateway | Medium | Gateway_1 |

### Detailed Observations
- ...

### Recommended Fixes
- ...
```

---

## Automated Testing Script

Create `run_visual_tests.py`:

```python
#!/usr/bin/env python3
"""Run visual tests for bpmn2drawio converter."""

import subprocess
from pathlib import Path

VISUAL_TEST_DIR = Path(__file__).parent / "tests" / "visual"
OUTPUT_DIR = VISUAL_TEST_DIR / "output"

def run_tests():
    OUTPUT_DIR.mkdir(exist_ok=True)

    results = []
    for bpmn_file in VISUAL_TEST_DIR.glob("*.bpmn"):
        output_file = OUTPUT_DIR / f"{bpmn_file.stem}.drawio"

        print(f"\nConverting: {bpmn_file.name}")
        result = subprocess.run(
            ["bpmn2drawio", str(bpmn_file), str(output_file), "--verbose"],
            capture_output=True,
            text=True
        )

        results.append({
            "file": bpmn_file.name,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })

        if result.returncode == 0:
            print(f"  ✓ Success: {output_file.name}")
        else:
            print(f"  ✗ Failed: {result.stderr}")

    return results

if __name__ == "__main__":
    run_tests()
```

---

## Visual Inspection Checklist

For each test file, verify:

### Layout Quality
- [ ] Elements are evenly spaced
- [ ] No elements overlap
- [ ] Diagram fits within reasonable bounds
- [ ] Left-to-right flow direction is maintained

### Swimlane Structure
- [ ] Pools have visible headers with names
- [ ] Lanes are correctly stacked vertically
- [ ] Lane heights accommodate their contents
- [ ] Elements are positioned within their assigned lane

### Flow Routing
- [ ] Sequence flows connect correct elements
- [ ] Flows use orthogonal (right-angle) routing
- [ ] Flows don't cross through elements
- [ ] Flow arrows point in correct direction
- [ ] Flow labels are readable (not overlapping)

### Gateway Rendering
- [ ] Gateway diamonds are visible
- [ ] Gateway markers (X, +, O) are present
- [ ] Split gateways have multiple outgoing flows
- [ ] Join gateways have multiple incoming flows

### Subprocess Handling
- [ ] Subprocess box is visible with border
- [ ] Internal elements are contained within box
- [ ] Boundary events attach to subprocess edge

### Cross-Pool Communication
- [ ] Message flows are dashed lines
- [ ] Message flows connect correct pools
- [ ] Message flow routing doesn't overlap badly

---

## Issue Severity Classification

| Severity | Description | Examples |
|----------|-------------|----------|
| Critical | Diagram is unusable | Elements completely overlapping, flows connecting wrong elements |
| High | Significant visual defect | Elements partially overlapping, flows through elements |
| Medium | Noticeable but usable | Inconsistent spacing, minor routing inefficiency |
| Low | Cosmetic issue | Slightly off-center labels, minor alignment issues |

---

## Iteration Process

1. **Create test file** → Generate BPMN with specific features
2. **Convert** → Run bpmn2drawio converter
3. **Inspect** → Open in diagrams.net, screenshot, analyze
4. **Document** → Record all issues found
5. **Fix** → Update converter code (layout.py, routing.py, etc.)
6. **Verify** → Re-run conversion, confirm fix
7. **Regression** → Re-test all previous files to ensure no regression

---

## Final Report Structure

After completing all tests:

```markdown
# BPMN2DrawIO Visual Testing Report

## Summary
- Total test files: X
- Passed: Y
- Issues found: Z

## Issues by Category
| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Layout   | 0        | 2    | 3      | 1   |
| Routing  | 1        | 1    | 2      | 0   |
| ...      | ...      | ...  | ...    | ... |

## Detailed Results
[Per-test reports]

## Recommended Fixes
[Prioritized list of code changes]
```
