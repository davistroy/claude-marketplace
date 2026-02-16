"""Style mappings for Draw.io elements."""

from typing import Dict

# Style mappings for BPMN elements to Draw.io styles
STYLE_MAP: Dict[str, str] = {
    # Start Events
    "startEvent": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#d5e8d4;strokeColor=#82b366;perimeter=ellipsePerimeter;",
    # End Events
    "endEvent": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=3;perimeter=ellipsePerimeter;",
    # Intermediate Events
    "intermediateCatchEvent": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=2;perimeter=ellipsePerimeter;",
    "intermediateThrowEvent": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=2;perimeter=ellipsePerimeter;",
    "boundaryEvent": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=2;perimeter=ellipsePerimeter;",
    # Tasks
    "task": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;arcSize=10;",
    "userTask": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;arcSize=10;",
    "serviceTask": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;arcSize=10;",
    "scriptTask": "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;arcSize=10;",
    "sendTask": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;arcSize=10;",
    "receiveTask": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;arcSize=10;",
    "businessRuleTask": "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;arcSize=10;",
    "manualTask": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;arcSize=10;",
    "callActivity": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;arcSize=10;strokeWidth=3;",
    "subProcess": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;arcSize=10;",
    # Gateways
    "exclusiveGateway": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;perimeter=rhombusPerimeter;",
    "parallelGateway": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;perimeter=rhombusPerimeter;",
    "inclusiveGateway": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;perimeter=rhombusPerimeter;",
    "eventBasedGateway": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;perimeter=rhombusPerimeter;",
    "complexGateway": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;perimeter=rhombusPerimeter;",
    # Data Objects
    "dataObject": "shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;",
    "dataObjectReference": "shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;",
    "dataStore": "shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;",
    "dataStoreReference": "shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;",
    # Artifacts
    "textAnnotation": "shape=note;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;",
    "group": "rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#666666;strokeWidth=2;dashed=1;",
}

# Edge styles for flow types
EDGE_STYLES: Dict[str, str] = {
    "sequenceFlow": "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;strokeWidth=1;endArrow=block;endFill=1;",
    "messageFlow": "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;strokeWidth=1;dashed=1;dashPattern=8 8;endArrow=open;endFill=0;startArrow=oval;startFill=0;startSize=8;",
    "association": "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;strokeWidth=1;dashed=1;dashPattern=1 2;endArrow=none;",
    "dataInputAssociation": "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;strokeWidth=1;dashed=1;dashPattern=1 2;endArrow=open;endFill=0;",
    "dataOutputAssociation": "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;strokeWidth=1;dashed=1;dashPattern=1 2;endArrow=open;endFill=0;",
}

# Swimlane styles
SWIMLANE_STYLES: Dict[str, str] = {
    "pool": "swimlane;whiteSpace=wrap;html=1;horizontal=0;startSize=40;fillColor=#f5f5f5;strokeColor=#666666;collapsible=0;",
    "lane": "swimlane;whiteSpace=wrap;html=1;horizontal=0;fillColor=#ffffff;strokeColor=#666666;collapsible=0;",
    "pool_vertical": "swimlane;whiteSpace=wrap;html=1;startSize=30;fillColor=#f5f5f5;strokeColor=#666666;collapsible=0;",
}


def get_element_style(element_type: str) -> str:
    """Get Draw.io style string for an element type.

    Args:
        element_type: BPMN element type

    Returns:
        Draw.io style string
    """
    return STYLE_MAP.get(element_type, STYLE_MAP["task"])


def get_edge_style(
    flow_type: str, is_default: bool = False, has_condition: bool = False
) -> str:
    """Get Draw.io style string for a flow type.

    Args:
        flow_type: BPMN flow type
        is_default: Whether this is a default flow
        has_condition: Whether this flow has a condition

    Returns:
        Draw.io style string
    """
    base_style = EDGE_STYLES.get(flow_type, EDGE_STYLES["sequenceFlow"])

    if flow_type == "sequenceFlow":
        if is_default:
            # Add slash marker for default flow
            base_style = base_style.replace(
                "endArrow=block",
                "startArrow=dash;startFill=0;startSize=14;endArrow=block",
            )
        elif has_condition:
            # Add diamond marker for conditional flow
            base_style = base_style.replace(
                "endArrow=block",
                "startArrow=diamond;startFill=0;startSize=14;endArrow=block",
            )

    return base_style
