"""Gateway markers for Draw.io elements."""

from typing import Dict, Optional, Tuple
from xml.etree import ElementTree as ET

from .models import BPMNElement


# Gateway marker definitions
GATEWAY_MARKERS: Dict[str, Dict] = {
    "exclusiveGateway": {
        "style": "shape=cross;whiteSpace=wrap;html=1;strokeColor=#d6b656;fillColor=none;size=0.35;strokeWidth=2;",
        "size": (20, 20),
    },
    "parallelGateway": {
        "style": "shape=cross;whiteSpace=wrap;html=1;strokeColor=#d6b656;fillColor=#d6b656;strokeWidth=3;",
        "size": (22, 22),
    },
    "inclusiveGateway": {
        "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#d6b656;fillColor=none;strokeWidth=2;",
        "size": (20, 20),
    },
    "eventBasedGateway": {
        "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#d6b656;fillColor=none;strokeWidth=2;dashed=1;",
        "size": (26, 26),
    },
    "complexGateway": {
        "style": "shape=cross;whiteSpace=wrap;html=1;strokeColor=#d6b656;fillColor=#d6b656;rotation=45;strokeWidth=2;",
        "size": (16, 16),
    },
}


def create_gateway_marker(
    element: BPMNElement,
    parent_cell_id: str,
    cell_counter: int,
) -> Optional[Tuple[ET.Element, int]]:
    """Create marker cell positioned inside gateway.

    Args:
        element: BPMN gateway element
        parent_cell_id: ID of the parent gateway cell
        cell_counter: Current cell counter for ID generation

    Returns:
        Tuple of (mxCell element, new counter) or None if not a gateway
    """
    if element.type not in GATEWAY_MARKERS:
        return None

    marker_def = GATEWAY_MARKERS[element.type]
    marker_width, marker_height = marker_def["size"]

    # Calculate center position within gateway
    gateway_width = element.width or 50
    gateway_height = element.height or 50
    offset_x = (gateway_width - marker_width) / 2
    offset_y = (gateway_height - marker_height) / 2

    cell_id = str(cell_counter)

    cell = ET.Element("mxCell")
    cell.set("id", cell_id)
    cell.set("value", "")
    cell.set("style", marker_def["style"])
    cell.set("vertex", "1")
    cell.set("parent", parent_cell_id)

    geometry = ET.SubElement(cell, "mxGeometry")
    geometry.set("x", str(offset_x))
    geometry.set("y", str(offset_y))
    geometry.set("width", str(marker_width))
    geometry.set("height", str(marker_height))
    geometry.set("as", "geometry")

    return cell, cell_counter + 1


def get_gateway_marker_style(gateway_type: str) -> Optional[str]:
    """Get marker style for a gateway type.

    Args:
        gateway_type: BPMN gateway type

    Returns:
        Style string or None
    """
    marker = GATEWAY_MARKERS.get(gateway_type)
    return marker["style"] if marker else None
