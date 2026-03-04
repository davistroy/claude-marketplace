# BPMN Element Reference

Reference tables for the `/bpmn-generator` skill. Loaded on demand to keep the main skill prompt focused on workflow and generation logic.

## Table of Contents

- [Task Type Selection](#task-type-selection)
- [Gateway Selection](#gateway-selection)
- [Event Selection](#event-selection)
- [ID Generation Rules](#id-generation-rules)
- [Diagram Interchange Dimensions](#diagram-interchange-dimensions)
- [Layout Constants](#layout-constants)
- [Role to Lane Mapping](#role-to-lane-mapping)

---

## Task Type Selection

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

---

## Gateway Selection

| Decision Pattern | Gateway Type | XML Element | Symbol |
|-----------------|--------------|-------------|--------|
| "if/then/else", "either A or B", "based on condition" | Exclusive (XOR) | `<bpmn:exclusiveGateway>` | X |
| "do all of", "simultaneously", "in parallel" | Parallel (AND) | `<bpmn:parallelGateway>` | + |
| "one or more of", "any combination", "at least one" | Inclusive (OR) | `<bpmn:inclusiveGateway>` | O |
| "wait for first event", "whichever happens first" | Event-Based | `<bpmn:eventBasedGateway>` | Pentagon |

---

## Event Selection

### Start Events

| Trigger | Event Type | XML Element |
|---------|-----------|-------------|
| Process begins manually or undefined | None | `<bpmn:startEvent>` |
| External message received | Message | `<bpmn:startEvent><bpmn:messageEventDefinition/></bpmn:startEvent>` |
| Scheduled time/date | Timer | `<bpmn:startEvent><bpmn:timerEventDefinition/></bpmn:startEvent>` |
| Condition becomes true | Conditional | `<bpmn:startEvent><bpmn:conditionalEventDefinition/></bpmn:startEvent>` |

### End Events

| Outcome | Event Type | XML Element |
|---------|-----------|-------------|
| Normal completion | None | `<bpmn:endEvent>` |
| Send final message | Message | `<bpmn:endEvent><bpmn:messageEventDefinition/></bpmn:endEvent>` |
| Error occurred | Error | `<bpmn:endEvent><bpmn:errorEventDefinition/></bpmn:endEvent>` |
| Stop all process instances | Terminate | `<bpmn:endEvent><bpmn:terminateEventDefinition/></bpmn:endEvent>` |

---

## ID Generation Rules

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

---

## Diagram Interchange Dimensions

| Element | Width | Height |
|---------|-------|--------|
| Start Event | 36 | 36 |
| End Event | 36 | 36 |
| Intermediate Event | 36 | 36 |
| Task | 100 | 80 |
| Gateway | 50 | 50 |
| Collapsed Subprocess | 100 | 80 |
| Expanded Subprocess | 350+ | 200+ |

---

## Layout Constants (Draw.io Compatible)

```text
POOL_LABEL_WIDTH     = 30px
LANE_LEFT_OFFSET     = 30px
ELEMENT_LEFT_MARGIN  = 60px
ELEMENT_SPACING_H    = 140px  (horizontal gap between elements)
ELEMENT_SPACING_V    = 45px   (vertical gap for branching paths)
LANE_MIN_HEIGHT      = 100px
LANE_BRANCH_HEIGHT   = 130px  (lane with 2 branches)
LANE_TRIPLE_HEIGHT   = 150px  (lane with 3+ branches)
```

---

## Role to Lane Mapping

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
