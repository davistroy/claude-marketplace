# BPMN 2.0 XML Namespaces Reference

This document details all XML namespaces required for valid BPMN 2.0 files.

---

## Required Namespaces

Every BPMN 2.0 XML file must declare these namespaces in the root `<definitions>` element:

### Core Namespaces

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    id="Definitions_1"
    targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="Claude BPMN Generator"
    exporterVersion="1.1">
```

---

## Namespace Details

### 1. BPMN Model Namespace

**Prefix:** `bpmn`
**URI:** `http://www.omg.org/spec/BPMN/20100524/MODEL`

**Purpose:** Contains all BPMN 2.0 process elements.

**Elements using this namespace:**
- `definitions` - Root element
- `process` - Process container
- `startEvent`, `endEvent`, `intermediateThrowEvent`, `intermediateCatchEvent`
- `task`, `userTask`, `serviceTask`, `scriptTask`, `sendTask`, `receiveTask`
- `exclusiveGateway`, `parallelGateway`, `inclusiveGateway`, `eventBasedGateway`
- `sequenceFlow`
- `subProcess`, `transaction`
- `dataObject`, `dataObjectReference`, `dataStoreReference`
- `message`, `error`, `signal`, `escalation`
- `collaboration`, `participant`
- `messageFlow`
- `laneSet`, `lane`
- `textAnnotation`, `group`, `association`

**Example:**
```xml
<bpmn:process id="Process_1" name="Order Process" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Order Received">
        <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
</bpmn:process>
```

---

### 2. BPMN Diagram Interchange Namespace

**Prefix:** `bpmndi`
**URI:** `http://www.omg.org/spec/BPMN/20100524/DI`

**Purpose:** Contains BPMN-specific diagram elements.

**Elements using this namespace:**
- `BPMNDiagram` - Diagram container
- `BPMNPlane` - Drawing plane for process
- `BPMNShape` - Visual representation of flow nodes
- `BPMNEdge` - Visual representation of connections
- `BPMNLabel` - Label positioning
- `BPMNLabelStyle` - Label styling

**Example:**
```xml
<bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
        <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
            <dc:Bounds x="180" y="102" width="36" height="36"/>
            <bpmndi:BPMNLabel>
                <dc:Bounds x="163" y="145" width="70" height="14"/>
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
</bpmndi:BPMNDiagram>
```

---

### 3. Diagram Common Namespace

**Prefix:** `dc`
**URI:** `http://www.omg.org/spec/DD/20100524/DC`

**Purpose:** Common diagram elements for bounds and dimensions.

**Elements using this namespace:**
- `Bounds` - Rectangle with x, y, width, height
- `Point` - Coordinate point (x, y)
- `Font` - Font specifications

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| x | double | X coordinate (pixels from left) |
| y | double | Y coordinate (pixels from top) |
| width | double | Element width in pixels |
| height | double | Element height in pixels |

**Example:**
```xml
<dc:Bounds x="180" y="102" width="36" height="36"/>
```

---

### 4. Diagram Interchange Namespace

**Prefix:** `di`
**URI:** `http://www.omg.org/spec/DD/20100524/DI`

**Purpose:** Generic diagram interchange elements.

**Elements using this namespace:**
- `waypoint` - Point on an edge/connection

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| x | double | X coordinate of waypoint |
| y | double | Y coordinate of waypoint |

**Example:**
```xml
<bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
    <di:waypoint x="216" y="120"/>
    <di:waypoint x="280" y="120"/>
</bpmndi:BPMNEdge>
```

---

### 5. XML Schema Instance Namespace

**Prefix:** `xsi`
**URI:** `http://www.w3.org/2001/XMLSchema-instance`

**Purpose:** XML Schema instance attributes for type definitions.

**Common uses:**
- Type specification for condition expressions
- Type specification for formal expressions

**Example:**
```xml
<bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
    ${approved == true}
</bpmn:conditionExpression>

<bpmn:timeDuration xsi:type="bpmn:tFormalExpression">PT1H</bpmn:timeDuration>
```

---

## Root Element Attributes

The `<definitions>` element requires these attributes:

| Attribute | Required | Description | Example |
|-----------|----------|-------------|---------|
| `id` | Yes | Unique identifier | `Definitions_OrderProcess` |
| `targetNamespace` | Yes | Process namespace | `http://bpmn.io/schema/bpmn` |
| `exporter` | No | Tool that created file | `Claude BPMN Generator` |
| `exporterVersion` | No | Tool version | `1.1` |
| `expressionLanguage` | No | Default expression language | `http://www.w3.org/1999/XPath` |
| `typeLanguage` | No | Default type language | `http://www.w3.org/2001/XMLSchema` |

---

## Optional/Extension Namespaces

### Camunda Extensions

For Camunda-specific features:

```xml
xmlns:camunda="http://camunda.org/schema/1.0/bpmn"
```

**Example usage:**
```xml
<bpmn:userTask id="Task_1" name="Review" camunda:assignee="${assignee}">
```

### Flowable Extensions

For Flowable-specific features:

```xml
xmlns:flowable="http://flowable.org/bpmn"
```

**Example usage:**
```xml
<bpmn:userTask id="Task_1" flowable:assignee="${assignee}">
```

### Activiti Extensions

For Activiti-specific features:

```xml
xmlns:activiti="http://activiti.org/bpmn"
```

---

## Complete Template

Here's a complete namespace declaration template:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    id="Definitions_[UNIQUE_ID]"
    targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="Claude BPMN Generator"
    exporterVersion="1.1">

    <!-- Process definitions -->
    <bpmn:process id="Process_[ID]" name="[Process Name]" isExecutable="true">
        <!-- Flow elements -->
    </bpmn:process>

    <!-- Optional: Message definitions -->
    <bpmn:message id="Message_[ID]" name="[Message Name]"/>

    <!-- Optional: Error definitions -->
    <bpmn:error id="Error_[ID]" name="[Error Name]" errorCode="[CODE]"/>

    <!-- Diagram interchange -->
    <bpmndi:BPMNDiagram id="BPMNDiagram_1">
        <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_[ID]">
            <!-- Shapes and edges -->
        </bpmndi:BPMNPlane>
    </bpmndi:BPMNDiagram>

</bpmn:definitions>
```

---

## Namespace Prefix Conventions

While prefixes are technically arbitrary, these are the standard conventions:

| Prefix | Namespace | Standard |
|--------|-----------|----------|
| `bpmn` or `bpmn2` | BPMN Model | Common |
| `bpmndi` | BPMN DI | Standard |
| `dc` | Diagram Common | Standard |
| `di` | Diagram Interchange | Standard |
| `xsi` | XML Schema Instance | Universal |
| `camunda` | Camunda extensions | Camunda-specific |
| `flowable` | Flowable extensions | Flowable-specific |
| `activiti` | Activiti extensions | Activiti-specific |

---

## Validation

To validate BPMN 2.0 XML against the official schema:

**Schema locations:**
- BPMN Model: `http://www.omg.org/spec/BPMN/20100524/MODEL`
- BPMN DI: `http://www.omg.org/spec/BPMN/20100524/DI`
- DC: `http://www.omg.org/spec/DD/20100524/DC`
- DI: `http://www.omg.org/spec/DD/20100524/DI`

**With schema location attribute:**
```xml
<bpmn:definitions
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.omg.org/spec/BPMN/20100524/MODEL BPMN20.xsd">
```

---

## Common Errors

### Missing Namespace

**Error:** Element not recognized
**Cause:** Namespace not declared
**Fix:** Add missing xmlns declaration

### Wrong Prefix

**Error:** Element prefix doesn't match namespace
**Cause:** Using undeclared prefix
**Fix:** Ensure prefix matches xmlns declaration

### Invalid Namespace URI

**Error:** Schema validation fails
**Cause:** Typo in namespace URI
**Fix:** Use exact URIs from this document

### Missing xsi:type

**Error:** Condition expression not parsed
**Cause:** Missing type attribute
**Fix:** Add `xsi:type="bpmn:tFormalExpression"`
