"""Constants for BPMN to Draw.io converter."""

from typing import Dict, Tuple

# Default element dimensions (width, height) in pixels
ELEMENT_DIMENSIONS: Dict[str, Tuple[int, int]] = {
    # Events (36x36)
    "startEvent": (36, 36),
    "endEvent": (36, 36),
    "intermediateCatchEvent": (36, 36),
    "intermediateThrowEvent": (36, 36),
    "boundaryEvent": (36, 36),
    # Tasks (120x80)
    "task": (120, 80),
    "userTask": (120, 80),
    "serviceTask": (120, 80),
    "scriptTask": (120, 80),
    "sendTask": (120, 80),
    "receiveTask": (120, 80),
    "businessRuleTask": (120, 80),
    "manualTask": (120, 80),
    "callActivity": (120, 80),
    "subProcess": (200, 150),
    # Gateways (50x50)
    "exclusiveGateway": (50, 50),
    "parallelGateway": (50, 50),
    "inclusiveGateway": (50, 50),
    "eventBasedGateway": (50, 50),
    "complexGateway": (50, 50),
    # Data objects
    "dataObject": (40, 50),
    "dataObjectReference": (40, 50),
    "dataStore": (50, 50),
    "dataStoreReference": (50, 50),
    # Artifacts
    "textAnnotation": (100, 40),
    "group": (200, 150),
}

# BPMN 2.0 XML namespaces
BPMN_NAMESPACES = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "semantic": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

# Element type categories
EVENT_TYPES = {
    "startEvent",
    "endEvent",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "boundaryEvent",
}

TASK_TYPES = {
    "task",
    "userTask",
    "serviceTask",
    "scriptTask",
    "sendTask",
    "receiveTask",
    "businessRuleTask",
    "manualTask",
    "callActivity",
    "subProcess",
}

GATEWAY_TYPES = {
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "eventBasedGateway",
    "complexGateway",
}

DATA_TYPES = {
    "dataObject",
    "dataObjectReference",
    "dataStore",
    "dataStoreReference",
}

ARTIFACT_TYPES = {
    "textAnnotation",
    "group",
}

FLOW_TYPES = {
    "sequenceFlow",
    "messageFlow",
    "association",
    "dataInputAssociation",
    "dataOutputAssociation",
}

# All supported element types
ALL_ELEMENT_TYPES = (
    EVENT_TYPES | TASK_TYPES | GATEWAY_TYPES | DATA_TYPES | ARTIFACT_TYPES
)


# Layout constants
class LayoutConstants:
    """Constants for diagram layout."""

    # Graphviz parameters
    GRAPHVIZ_NODESEP = 0.8  # Horizontal spacing (inches)
    GRAPHVIZ_RANKSEP = 1.2  # Vertical spacing (inches)

    # Scaling factors
    SCALE_X = 100  # Pixels per Graphviz inch
    SCALE_Y = 100

    # Margins
    DIAGRAM_MARGIN = 50  # Pixels around diagram

    # Inter-element spacing (pixels)
    NODE_HORIZONTAL_GAP = 60
    NODE_VERTICAL_GAP = 80
    RANK_SEPARATION = 120

    # Swimlane dimensions
    POOL_HEADER_WIDTH = 40
    LANE_HEADER_HEIGHT = 30
    LANE_PADDING = 20
