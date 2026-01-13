"""Task and event icons for Draw.io elements."""

from typing import Dict, Optional, Tuple
from xml.etree import ElementTree as ET

from .models import BPMNElement


# Task icon definitions
TASK_ICONS: Dict[str, Dict] = {
    "userTask": {
        "style": "shape=mxgraph.bpmn.user_task;fillColor=#6c8ebf;strokeColor=#6c8ebf;",
        "size": (16, 16),
        "offset": (5, 5),
    },
    "serviceTask": {
        "style": "shape=mxgraph.bpmn.service_task;fillColor=#6c8ebf;strokeColor=#6c8ebf;",
        "size": (16, 16),
        "offset": (5, 5),
    },
    "scriptTask": {
        "style": "shape=mxgraph.bpmn.script_task;fillColor=#9673a6;strokeColor=#9673a6;",
        "size": (16, 16),
        "offset": (5, 5),
    },
    "sendTask": {
        "style": "shape=mxgraph.bpmn.message;fillColor=#6c8ebf;strokeColor=#6c8ebf;",
        "size": (16, 12),
        "offset": (5, 5),
    },
    "receiveTask": {
        "style": "shape=mxgraph.bpmn.message;fillColor=none;strokeColor=#6c8ebf;strokeWidth=2;",
        "size": (16, 12),
        "offset": (5, 5),
    },
    "businessRuleTask": {
        "style": "shape=mxgraph.bpmn.business_rule_task;fillColor=#d79b00;strokeColor=#d79b00;",
        "size": (16, 16),
        "offset": (5, 5),
    },
    "manualTask": {
        "style": "shape=mxgraph.bpmn.manual_task;fillColor=#666666;strokeColor=#666666;",
        "size": (16, 16),
        "offset": (5, 5),
    },
}

# Event icon definitions based on event type and definition
EVENT_ICONS: Dict[str, Dict] = {
    # Start events
    "startEvent_message": {
        "style": "shape=mxgraph.bpmn.message;fillColor=none;strokeColor=#82b366;strokeWidth=1;",
        "size": (18, 14),
    },
    "startEvent_timer": {
        "style": "shape=mxgraph.bpmn.timer;fillColor=none;strokeColor=#82b366;strokeWidth=1;",
        "size": (20, 20),
    },
    "startEvent_signal": {
        "style": "shape=triangle;direction=north;fillColor=none;strokeColor=#82b366;strokeWidth=1;",
        "size": (16, 16),
    },
    "startEvent_conditional": {
        "style": "shape=mxgraph.bpmn.conditional;fillColor=none;strokeColor=#82b366;strokeWidth=1;",
        "size": (18, 18),
    },
    "startEvent_error": {
        "style": "shape=mxgraph.bpmn.error;fillColor=none;strokeColor=#82b366;strokeWidth=1;",
        "size": (16, 16),
    },

    # End events
    "endEvent_message": {
        "style": "shape=mxgraph.bpmn.message;fillColor=#b85450;strokeColor=#b85450;",
        "size": (18, 14),
    },
    "endEvent_error": {
        "style": "shape=mxgraph.bpmn.error;fillColor=#b85450;strokeColor=#b85450;",
        "size": (16, 16),
    },
    "endEvent_signal": {
        "style": "shape=triangle;direction=north;fillColor=#b85450;strokeColor=#b85450;",
        "size": (16, 16),
    },
    "endEvent_terminate": {
        "style": "ellipse;fillColor=#b85450;strokeColor=#b85450;",
        "size": (20, 20),
    },
    "endEvent_escalation": {
        "style": "shape=triangle;direction=north;fillColor=#b85450;strokeColor=#b85450;",
        "size": (16, 16),
    },
    "endEvent_cancel": {
        "style": "shape=cross;fillColor=#b85450;strokeColor=#b85450;size=0.4;",
        "size": (16, 16),
    },
    "endEvent_compensation": {
        "style": "shape=mxgraph.bpmn.compensation;fillColor=#b85450;strokeColor=#b85450;",
        "size": (16, 16),
    },

    # Intermediate catch events
    "intermediateCatchEvent_message": {
        "style": "shape=mxgraph.bpmn.message;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (18, 14),
    },
    "intermediateCatchEvent_timer": {
        "style": "shape=mxgraph.bpmn.timer;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (20, 20),
    },
    "intermediateCatchEvent_signal": {
        "style": "shape=triangle;direction=north;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (16, 16),
    },
    "intermediateCatchEvent_conditional": {
        "style": "shape=mxgraph.bpmn.conditional;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (18, 18),
    },
    "intermediateCatchEvent_link": {
        "style": "shape=mxgraph.bpmn.link;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (16, 16),
    },

    # Intermediate throw events
    "intermediateThrowEvent_message": {
        "style": "shape=mxgraph.bpmn.message;fillColor=#d6b656;strokeColor=#d6b656;",
        "size": (18, 14),
    },
    "intermediateThrowEvent_signal": {
        "style": "shape=triangle;direction=north;fillColor=#d6b656;strokeColor=#d6b656;",
        "size": (16, 16),
    },
    "intermediateThrowEvent_escalation": {
        "style": "shape=triangle;direction=north;fillColor=#d6b656;strokeColor=#d6b656;",
        "size": (16, 16),
    },
    "intermediateThrowEvent_compensation": {
        "style": "shape=mxgraph.bpmn.compensation;fillColor=#d6b656;strokeColor=#d6b656;",
        "size": (16, 16),
    },
    "intermediateThrowEvent_link": {
        "style": "shape=mxgraph.bpmn.link;fillColor=#d6b656;strokeColor=#d6b656;",
        "size": (16, 16),
    },

    # Boundary events
    "boundaryEvent_message": {
        "style": "shape=mxgraph.bpmn.message;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (16, 12),
    },
    "boundaryEvent_timer": {
        "style": "shape=mxgraph.bpmn.timer;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (18, 18),
    },
    "boundaryEvent_error": {
        "style": "shape=mxgraph.bpmn.error;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (14, 14),
    },
    "boundaryEvent_signal": {
        "style": "shape=triangle;direction=north;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (14, 14),
    },
    "boundaryEvent_escalation": {
        "style": "shape=triangle;direction=north;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (14, 14),
    },
    "boundaryEvent_cancel": {
        "style": "shape=cross;fillColor=none;strokeColor=#d6b656;size=0.4;strokeWidth=1;",
        "size": (14, 14),
    },
    "boundaryEvent_compensation": {
        "style": "shape=mxgraph.bpmn.compensation;fillColor=none;strokeColor=#d6b656;strokeWidth=1;",
        "size": (14, 14),
    },
}


def create_task_icon(
    element: BPMNElement,
    parent_cell_id: str,
    cell_counter: int,
) -> Optional[Tuple[ET.Element, int]]:
    """Create icon cell positioned in task top-left.

    Args:
        element: BPMN task element
        parent_cell_id: ID of the parent task cell
        cell_counter: Current cell counter for ID generation

    Returns:
        Tuple of (mxCell element, new counter) or None if no icon needed
    """
    if element.type not in TASK_ICONS:
        return None

    icon_def = TASK_ICONS[element.type]
    icon_width, icon_height = icon_def["size"]
    offset_x, offset_y = icon_def["offset"]

    cell_id = str(cell_counter)

    cell = ET.Element("mxCell")
    cell.set("id", cell_id)
    cell.set("value", "")
    cell.set("style", icon_def["style"])
    cell.set("vertex", "1")
    cell.set("parent", parent_cell_id)

    geometry = ET.SubElement(cell, "mxGeometry")
    geometry.set("x", str(offset_x))
    geometry.set("y", str(offset_y))
    geometry.set("width", str(icon_width))
    geometry.set("height", str(icon_height))
    geometry.set("as", "geometry")

    return cell, cell_counter + 1


def create_event_icon(
    element: BPMNElement,
    parent_cell_id: str,
    cell_counter: int,
) -> Optional[Tuple[ET.Element, int]]:
    """Create icon cell positioned inside event.

    Args:
        element: BPMN event element
        parent_cell_id: ID of the parent event cell
        cell_counter: Current cell counter for ID generation

    Returns:
        Tuple of (mxCell element, new counter) or None if no icon needed
    """
    # Get event definition type from properties
    event_def = element.properties.get("eventDefinition", "")
    if not event_def:
        return None

    # Build icon key
    icon_key = f"{element.type}_{event_def}"

    if icon_key not in EVENT_ICONS:
        return None

    icon_def = EVENT_ICONS[icon_key]
    icon_width, icon_height = icon_def["size"]

    # Center the icon in the event circle
    event_width = element.width or 36
    event_height = element.height or 36
    offset_x = (event_width - icon_width) / 2
    offset_y = (event_height - icon_height) / 2

    cell_id = str(cell_counter)

    cell = ET.Element("mxCell")
    cell.set("id", cell_id)
    cell.set("value", "")
    cell.set("style", icon_def["style"])
    cell.set("vertex", "1")
    cell.set("parent", parent_cell_id)

    geometry = ET.SubElement(cell, "mxGeometry")
    geometry.set("x", str(offset_x))
    geometry.set("y", str(offset_y))
    geometry.set("width", str(icon_width))
    geometry.set("height", str(icon_height))
    geometry.set("as", "geometry")

    return cell, cell_counter + 1


def get_task_icon_style(task_type: str) -> Optional[str]:
    """Get icon style for a task type.

    Args:
        task_type: BPMN task type

    Returns:
        Style string or None
    """
    icon = TASK_ICONS.get(task_type)
    return icon["style"] if icon else None


def get_event_icon_style(event_type: str, event_def: str) -> Optional[str]:
    """Get icon style for an event.

    Args:
        event_type: BPMN event type
        event_def: Event definition type

    Returns:
        Style string or None
    """
    icon_key = f"{event_type}_{event_def}"
    icon = EVENT_ICONS.get(icon_key)
    return icon["style"] if icon else None
