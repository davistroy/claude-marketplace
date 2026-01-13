"""Waypoint calculation and conversion for BPMN flows."""

from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from .models import BPMNElement, BPMNFlow


def convert_bpmn_waypoints(
    di_waypoints: List[Dict],
) -> List[Tuple[float, float]]:
    """Convert BPMN DI waypoints to Draw.io format.

    Args:
        di_waypoints: List of waypoint dicts with x, y keys

    Returns:
        List of (x, y) tuples
    """
    waypoints = []
    for wp in di_waypoints:
        x = float(wp.get("x", 0))
        y = float(wp.get("y", 0))
        waypoints.append((x, y))
    return waypoints


def generate_waypoints(
    source: BPMNElement,
    target: BPMNElement,
    routing_style: str = "orthogonal",
) -> List[Tuple[float, float]]:
    """Generate waypoints when DI doesn't provide them.

    Args:
        source: Source element
        target: Target element
        routing_style: Routing style (orthogonal, direct)

    Returns:
        List of waypoints
    """
    src_x = (source.x or 0) + (source.width or 120) / 2
    src_y = (source.y or 0) + (source.height or 80) / 2
    tgt_x = (target.x or 0) + (target.width or 120) / 2
    tgt_y = (target.y or 0) + (target.height or 80) / 2

    if routing_style == "direct":
        return [(src_x, src_y), (tgt_x, tgt_y)]

    # Orthogonal routing
    waypoints = []

    # Source exit point
    if tgt_x > src_x + (source.width or 120) / 2:
        src_exit = ((source.x or 0) + (source.width or 120), src_y)
    elif tgt_x < src_x - (source.width or 120) / 2:
        src_exit = (source.x or 0, src_y)
    elif tgt_y > src_y:
        src_exit = (src_x, (source.y or 0) + (source.height or 80))
    else:
        src_exit = (src_x, source.y or 0)

    waypoints.append(src_exit)

    # Target entry point
    if src_x > tgt_x + (target.width or 120) / 2:
        tgt_entry = ((target.x or 0) + (target.width or 120), tgt_y)
    elif src_x < tgt_x - (target.width or 120) / 2:
        tgt_entry = (target.x or 0, tgt_y)
    elif src_y > tgt_y:
        tgt_entry = (tgt_x, (target.y or 0) + (target.height or 80))
    else:
        tgt_entry = (tgt_x, target.y or 0)

    # Add intermediate point if needed
    if abs(src_exit[0] - tgt_entry[0]) > 10 and abs(src_exit[1] - tgt_entry[1]) > 10:
        mid_x = (src_exit[0] + tgt_entry[0]) / 2
        waypoints.append((mid_x, src_exit[1]))
        waypoints.append((mid_x, tgt_entry[1]))

    waypoints.append(tgt_entry)

    return waypoints


def create_waypoint_array(
    waypoints: List[Tuple[float, float]],
) -> Optional[ET.Element]:
    """Create mxPoint Array element for edge geometry.

    Args:
        waypoints: List of waypoints

    Returns:
        Array element or None if no intermediate waypoints
    """
    # Skip first and last (source/target connection points)
    intermediate = waypoints[1:-1] if len(waypoints) > 2 else []

    if not intermediate:
        return None

    array = ET.Element("Array")
    array.set("as", "points")

    for x, y in intermediate:
        point = ET.SubElement(array, "mxPoint")
        point.set("x", str(x))
        point.set("y", str(y))

    return array


def position_edge_label(
    flow: BPMNFlow,
    waypoints: List[Tuple[float, float]],
) -> Dict[str, Any]:
    """Calculate label position along edge midpoint.

    Args:
        flow: BPMN flow
        waypoints: Edge waypoints

    Returns:
        Label position info dict
    """
    if not flow.name:
        return {}

    if len(waypoints) < 2:
        return {"x": 0.5, "y": 0}

    # Find midpoint
    if len(waypoints) == 2:
        mid_x = (waypoints[0][0] + waypoints[1][0]) / 2
        mid_y = (waypoints[0][1] + waypoints[1][1]) / 2
    else:
        # Use middle waypoint
        mid_idx = len(waypoints) // 2
        mid_x = waypoints[mid_idx][0]
        mid_y = waypoints[mid_idx][1]

    return {
        "x": mid_x,
        "y": mid_y,
        "offset_x": 0,
        "offset_y": -10,  # Above the edge
    }
