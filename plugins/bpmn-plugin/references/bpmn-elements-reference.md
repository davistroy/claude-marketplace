# BPMN 2.0 Elements Reference

Quick reference guide for all BPMN 2.0 elements supported by this skill.

---

## Table of Contents

1. [Events](#events)
2. [Tasks](#tasks)
3. [Gateways](#gateways)
4. [Subprocesses](#subprocesses)
5. [Data Elements](#data-elements)
6. [Connecting Objects](#connecting-objects)
7. [Swimlanes](#swimlanes)
8. [Artifacts](#artifacts)

---

## Events

Events represent something that happens during the process lifecycle.

### Event Types by Position

| Position | Description | Can Catch | Can Throw |
|----------|-------------|-----------|-----------|
| Start | Initiates process | Yes | No |
| Intermediate | Occurs during flow | Yes | Yes |
| End | Concludes process | No | Yes |
| Boundary | Attached to activity | Yes | No |

### Event Definitions

| Event Type | Symbol | Start | Intermediate Catch | Intermediate Throw | End | Boundary |
|------------|--------|-------|-------------------|-------------------|-----|----------|
| None | Circle | Yes | Yes | Yes | Yes | - |
| Message | Envelope | Yes | Yes | Yes | Yes | Yes |
| Timer | Clock | Yes | Yes | - | - | Yes |
| Error | Lightning | - | - | - | Yes | Yes |
| Escalation | Arrow up | - | Yes | Yes | Yes | Yes |
| Cancel | X | - | - | - | Yes | Yes |
| Compensation | Rewind | - | Yes | Yes | Yes | Yes |
| Conditional | Document | Yes | Yes | - | - | Yes |
| Link | Arrow | - | Yes | Yes | - | - |
| Signal | Triangle | Yes | Yes | Yes | Yes | Yes |
| Terminate | Filled circle | - | - | - | Yes | - |
| Multiple | Pentagon | Yes | Yes | Yes | Yes | Yes |
| Parallel Multiple | Plus pentagon | Yes | Yes | - | - | Yes |

### Event Usage Guidelines

**Start Events:**
- Use **None** when process is triggered manually or by unspecified means
- Use **Message** when external message/request initiates process
- Use **Timer** for scheduled processes (daily reports, monthly billing)
- Use **Signal** when broadcast event triggers multiple process instances
- Use **Conditional** when data condition triggers process start

**End Events:**
- Use **None** for normal completion
- Use **Message** to send notification on completion
- Use **Error** when process fails and error needs propagation
- Use **Terminate** to immediately stop all process activities
- Use **Escalation** to escalate to parent process

**Boundary Events:**
- **Interrupting**: Cancels the activity and diverts flow (solid border)
- **Non-interrupting**: Spawns parallel path without canceling (dashed border)
- Timer boundaries: Deadlines, reminders
- Error boundaries: Exception handling
- Message boundaries: Handle external communications

---

## Tasks

Tasks are atomic activities within a process.

### Task Types

| Task Type | Icon | Use When | XML Element |
|-----------|------|----------|-------------|
| **User Task** | Person | Human performer required | `<bpmn:userTask>` |
| **Service Task** | Gears | Automated system operation | `<bpmn:serviceTask>` |
| **Script Task** | Script | Execute embedded code | `<bpmn:scriptTask>` |
| **Send Task** | Message (filled) | Send message to external | `<bpmn:sendTask>` |
| **Receive Task** | Message (empty) | Wait for external message | `<bpmn:receiveTask>` |
| **Business Rule Task** | Table | Apply decision table/DMN | `<bpmn:businessRuleTask>` |
| **Manual Task** | Hand | Physical work, untracked | `<bpmn:manualTask>` |
| **Call Activity** | Thick border | Invoke reusable process | `<bpmn:callActivity>` |
| **Task** | None | Unspecified task type | `<bpmn:task>` |

### Task Selection Guide

```
Is the work performed by...

A person using the system?
  └─> User Task

An automated system/API?
  └─> Service Task

Embedded code execution?
  └─> Script Task

Sending a message/notification?
  └─> Send Task

Waiting for external response?
  └─> Receive Task

Business rules/decision table?
  └─> Business Rule Task

Physical/manual work (no system)?
  └─> Manual Task

Another defined process?
  └─> Call Activity

Unsure/generic?
  └─> Task
```

### Multi-Instance Tasks

For tasks that repeat for a collection:

| Type | Marker | Description |
|------|--------|-------------|
| Sequential | Three horizontal lines | Execute one at a time |
| Parallel | Three vertical lines | Execute all simultaneously |

```xml
<!-- Sequential -->
<bpmn:multiInstanceLoopCharacteristics isSequential="true">
    <bpmn:loopCardinality>${itemCount}</bpmn:loopCardinality>
</bpmn:multiInstanceLoopCharacteristics>

<!-- Parallel -->
<bpmn:multiInstanceLoopCharacteristics isSequential="false">
    <bpmn:loopCardinality>${itemCount}</bpmn:loopCardinality>
</bpmn:multiInstanceLoopCharacteristics>
```

---

## Gateways

Gateways control process flow divergence and convergence.

### Gateway Types

| Gateway | Symbol | Diverging (Split) | Converging (Merge) |
|---------|--------|-------------------|-------------------|
| **Exclusive (XOR)** | X | One path based on condition | First to arrive continues |
| **Parallel (AND)** | + | All paths execute | Wait for all paths |
| **Inclusive (OR)** | O | One or more paths | Wait for active paths |
| **Event-Based** | Pentagon | Wait for event to determine path | N/A |
| **Complex** | * | Custom activation rules | Custom synchronization |

### Gateway Selection Guide

```
How many outgoing paths should be taken?

Exactly one (based on conditions)?
  └─> Exclusive Gateway (XOR)

All paths simultaneously?
  └─> Parallel Gateway (AND)

One or more (based on conditions)?
  └─> Inclusive Gateway (OR)

Determined by which event occurs first?
  └─> Event-Based Gateway

Complex rules?
  └─> Complex Gateway
```

### Gateway Best Practices

1. **Always pair splits with merges** of the same type
2. **Exclusive gateways** should have a default flow for unmatched conditions
3. **Parallel gateways** must have matching joins before continuing
4. **Event-based gateways** must be followed by catching events
5. **Name decision gateways** with a question (e.g., "Order Valid?")

### Condition Expression Examples

```xml
<!-- Equals -->
${status == 'approved'}

<!-- Not equals -->
${status != 'rejected'}

<!-- Greater than -->
${amount > 1000}

<!-- Boolean -->
${isVIP == true}

<!-- String contains -->
${category.contains('premium')}

<!-- Multiple conditions -->
${status == 'approved' && amount > 100}
```

---

## Subprocesses

Subprocesses group activities and can have their own scope.

### Subprocess Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Embedded** | Inline subprocess | Group related activities |
| **Event** | Triggered by event | Handle exceptions, cancellation |
| **Transaction** | ACID properties | Payment processing, bookings |
| **Call Activity** | External reference | Reusable processes |
| **Ad-Hoc** | Unordered activities | Flexible task completion |

### Embedded Subprocess Structure

```xml
<bpmn:subProcess id="SubProcess_1" name="Process Items">
    <bpmn:incoming>Flow_1</bpmn:incoming>
    <bpmn:outgoing>Flow_2</bpmn:outgoing>

    <bpmn:startEvent id="SubStart"/>
    <!-- Activities -->
    <bpmn:endEvent id="SubEnd"/>
    <!-- Sequence flows -->
</bpmn:subProcess>
```

### Event Subprocess

- Contained within parent process/subprocess
- Has event start (message, timer, error, etc.)
- Can be interrupting or non-interrupting

```xml
<bpmn:subProcess id="EventSubProcess" triggeredByEvent="true">
    <bpmn:startEvent isInterrupting="false">
        <bpmn:messageEventDefinition messageRef="Message_Cancel"/>
    </bpmn:startEvent>
    <!-- Handle cancellation -->
</bpmn:subProcess>
```

---

## Data Elements

Data elements represent information used or produced by activities.

### Data Object Types

| Element | Description | Use |
|---------|-------------|-----|
| **Data Object** | Single data item | Order, Invoice |
| **Data Object (Collection)** | Multiple items | Line Items, Recipients |
| **Data Store** | Persistent storage | Database, File System |
| **Data Input** | Process input | Request parameters |
| **Data Output** | Process output | Response data |

### Data Association Directions

| Association | Direction | Description |
|-------------|-----------|-------------|
| **Input** | Data → Activity | Activity reads data |
| **Output** | Activity → Data | Activity writes data |

```xml
<!-- Input Association -->
<bpmn:dataInputAssociation id="Input_1">
    <bpmn:sourceRef>DataObjectRef_Order</bpmn:sourceRef>
</bpmn:dataInputAssociation>

<!-- Output Association -->
<bpmn:dataOutputAssociation id="Output_1">
    <bpmn:targetRef>DataObjectRef_Invoice</bpmn:targetRef>
</bpmn:dataOutputAssociation>
```

---

## Connecting Objects

### Sequence Flow

Connects flow elements within a process.

```xml
<!-- Basic flow -->
<bpmn:sequenceFlow id="Flow_1" sourceRef="Task_1" targetRef="Task_2"/>

<!-- Conditional flow -->
<bpmn:sequenceFlow id="Flow_Conditional" sourceRef="Gateway_1" targetRef="Task_2">
    <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
        ${approved == true}
    </bpmn:conditionExpression>
</bpmn:sequenceFlow>

<!-- Default flow (set on gateway) -->
<bpmn:exclusiveGateway id="Gateway_1" default="Flow_Default">
```

### Message Flow

Connects elements across pools (in collaborations).

```xml
<bpmn:messageFlow id="MessageFlow_1"
    sourceRef="Task_SendOrder"
    targetRef="StartEvent_ReceiveOrder"/>
```

### Association

Connects artifacts to flow elements.

```xml
<bpmn:association id="Association_1"
    sourceRef="TextAnnotation_1"
    targetRef="Task_1"/>
```

---

## Swimlanes

### Pools

Represent participants in a collaboration.

```xml
<bpmn:collaboration id="Collaboration_1">
    <bpmn:participant id="Pool_Customer" name="Customer" processRef="Process_Customer"/>
    <bpmn:participant id="Pool_Vendor" name="Vendor" processRef="Process_Vendor"/>
</bpmn:collaboration>
```

### Lanes

Subdivide pools by role or department.

```xml
<bpmn:laneSet id="LaneSet_1">
    <bpmn:lane id="Lane_Sales" name="Sales">
        <bpmn:flowNodeRef>Task_CreateQuote</bpmn:flowNodeRef>
    </bpmn:lane>
    <bpmn:lane id="Lane_Finance" name="Finance">
        <bpmn:flowNodeRef>Task_ApproveDiscount</bpmn:flowNodeRef>
    </bpmn:lane>
</bpmn:laneSet>
```

### Lane Assignment

Reference activities in lanes:

```xml
<bpmn:lane id="Lane_Manager" name="Manager">
    <bpmn:flowNodeRef>Task_Review</bpmn:flowNodeRef>
    <bpmn:flowNodeRef>Gateway_Decision</bpmn:flowNodeRef>
    <bpmn:flowNodeRef>Task_Approve</bpmn:flowNodeRef>
</bpmn:lane>
```

---

## Artifacts

### Text Annotation

Add notes to diagram elements.

```xml
<bpmn:textAnnotation id="TextAnnotation_1">
    <bpmn:text>SLA: Complete within 24 hours</bpmn:text>
</bpmn:textAnnotation>

<bpmn:association id="Association_1"
    sourceRef="TextAnnotation_1"
    targetRef="Task_Review"/>
```

### Group

Visually group elements (no semantic meaning).

```xml
<bpmn:group id="Group_1" categoryValueRef="CategoryValue_1"/>

<bpmn:category id="Category_1">
    <bpmn:categoryValue id="CategoryValue_1" value="Approval Phase"/>
</bpmn:category>
```

---

## Quick Reference: Common Patterns

### Sequential Flow
```
Start → Task A → Task B → Task C → End
```

### Exclusive Decision
```
Start → Task → [Decision?] →(Yes)→ Path A → End
                          →(No)→ Path B → End
```

### Parallel Execution
```
Start → Task → [+] → Task A → [+] → End
              → Task B →
```

### Error Handling
```
                    ↓ (error boundary)
Start → Task → [Error Handler] → End (Error)
       ↓
      End (Success)
```

### Loop Pattern
```
Start → Task → [Complete?] →(No)→ (back to Task)
                          →(Yes)→ End
```

---

## Element Dimensions (Diagram Interchange)

| Element | Width | Height |
|---------|-------|--------|
| Start Event | 36 | 36 |
| Intermediate Event | 36 | 36 |
| End Event | 36 | 36 |
| Task | 100 | 80 |
| Gateway | 50 | 50 |
| Collapsed Subprocess | 100 | 80 |
| Expanded Subprocess | 350+ | 200+ |
| Data Object | 36 | 50 |
| Data Store | 50 | 50 |
| Text Annotation | variable | variable |
| Pool | 600+ | 250+ |
| Lane | pool width | 125 |
