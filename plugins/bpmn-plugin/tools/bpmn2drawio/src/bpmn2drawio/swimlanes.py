"""Swimlane handling for pools and lanes."""

from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from .models import Pool, Lane, BPMNElement, BPMNModel
from .styles import SWIMLANE_STYLES
from .constants import LayoutConstants


class SwimlaneSizer:
    """Calculate pool and lane dimensions based on contents."""

    def __init__(self, padding: float = 20):
        """Initialize sizer.

        Args:
            padding: Padding around elements in lanes
        """
        self.padding = padding
        self.pool_header_width = LayoutConstants.POOL_HEADER_WIDTH
        self.lane_header_height = LayoutConstants.LANE_HEADER_HEIGHT

    def calculate_pool_size(
        self,
        pool: Pool,
        elements: List[BPMNElement],
        lanes: List[Lane],
    ) -> Tuple[float, float]:
        """Calculate width/height to contain all elements.

        Args:
            pool: Pool to size
            elements: Elements in the pool
            lanes: Lanes in the pool

        Returns:
            (width, height) tuple
        """
        if pool.width and pool.height:
            return (pool.width, pool.height)

        # Find bounding box of all elements
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for element in elements:
            if element.x is not None and element.y is not None:
                min_x = min(min_x, element.x)
                min_y = min(min_y, element.y)
                max_x = max(max_x, element.x + (element.width or 120))
                max_y = max(max_y, element.y + (element.height or 80))

        if min_x == float('inf'):
            # No elements with positions
            width = 600
            height = 200
        else:
            width = max_x - min_x + self.padding * 2 + self.pool_header_width
            height = max_y - min_y + self.padding * 2

        # Ensure minimum size
        width = max(width, 400)
        height = max(height, 150)

        return (width, height)

    def calculate_lane_sizes(
        self,
        pool: Pool,
        lanes: List[Lane],
        elements: List[BPMNElement],
    ) -> Dict[str, Tuple[float, float, float, float]]:
        """Calculate lane dimensions to fill pool.

        Args:
            pool: Parent pool
            lanes: Lanes in the pool
            elements: Elements for sizing

        Returns:
            Dictionary mapping lane ID to (x, y, width, height)
        """
        if not lanes:
            return {}

        pool_width = pool.width or 600
        pool_height = pool.height or 200

        # Lane width is pool width minus header
        lane_width = pool_width - self.pool_header_width

        # Distribute height equally among lanes
        lane_height = pool_height / len(lanes)

        result = {}
        y_offset = 0

        for lane in lanes:
            if lane.width and lane.height:
                result[lane.id] = (
                    self.pool_header_width,
                    y_offset,
                    lane.width,
                    lane.height,
                )
            else:
                result[lane.id] = (
                    self.pool_header_width,
                    y_offset,
                    lane_width,
                    lane_height,
                )
            y_offset += lane_height

        return result


def create_pool_cell(
    pool: Pool,
    cell_id: str,
    parent_id: str = "1",
) -> ET.Element:
    """Create swimlane mxCell for pool.

    Args:
        pool: Pool data
        cell_id: Cell ID to assign
        parent_id: Parent cell ID

    Returns:
        mxCell element
    """
    cell = ET.Element("mxCell")
    cell.set("id", cell_id)
    cell.set("value", pool.name or "")

    # Choose style based on orientation
    if pool.is_horizontal:
        style = SWIMLANE_STYLES["pool"]
    else:
        style = SWIMLANE_STYLES["pool_vertical"]

    cell.set("style", style)
    cell.set("vertex", "1")
    cell.set("parent", parent_id)

    # Add geometry
    geometry = ET.SubElement(cell, "mxGeometry")
    geometry.set("x", str(pool.x or 0))
    geometry.set("y", str(pool.y or 0))
    geometry.set("width", str(pool.width or 600))
    geometry.set("height", str(pool.height or 200))
    geometry.set("as", "geometry")

    return cell


def create_lane_cell(
    lane: Lane,
    cell_id: str,
    pool_cell_id: str,
) -> ET.Element:
    """Create swimlane mxCell for lane with pool as parent.

    Args:
        lane: Lane data
        cell_id: Cell ID to assign
        pool_cell_id: Parent pool cell ID

    Returns:
        mxCell element
    """
    cell = ET.Element("mxCell")
    cell.set("id", cell_id)
    cell.set("value", lane.name or "")
    cell.set("style", SWIMLANE_STYLES["lane"])
    cell.set("vertex", "1")
    cell.set("parent", pool_cell_id)

    # Add geometry
    geometry = ET.SubElement(cell, "mxGeometry")
    geometry.set("x", str(lane.x or 0))
    geometry.set("y", str(lane.y or 0))
    geometry.set("width", str(lane.width or 560))
    geometry.set("height", str(lane.height or 200))
    geometry.set("as", "geometry")

    return cell


def resolve_parent_hierarchy(model: BPMNModel) -> Dict[str, str]:
    """Resolve parent hierarchy for all elements including subprocess internals.

    Parent-child structure for Draw.io:
    Root (id=1)
      └── Pool (parent=1)
            └── Lane (parent=pool_id)
                  └── Task (parent=lane_id)
                  └── Subprocess (parent=lane_id)
                        └── Internal Task (parent=subprocess_id)

    Args:
        model: BPMN model

    Returns:
        Dictionary mapping element ID to parent cell ID
    """
    hierarchy = {}

    # PHASE 1: Resolve lane/pool parents
    # Build lane membership lookup
    lane_elements = {}
    for lane in model.lanes:
        for elem_ref in lane.element_refs:
            lane_elements[elem_ref] = lane.id

    # Build pool membership lookup
    pool_lanes = {}
    for pool in model.pools:
        for lane_id in pool.lanes:
            pool_lanes[lane_id] = pool.id

    # Assign parent IDs for lane/pool membership
    for element in model.elements:
        if element.id in lane_elements:
            # Element is in a lane
            hierarchy[element.id] = lane_elements[element.id]
        elif element.parent_id:
            # Element already has parent
            hierarchy[element.id] = element.parent_id
        else:
            # Check if in any pool by process reference
            for pool in model.pools:
                if pool.process_ref == model.process_id:
                    hierarchy[element.id] = pool.id
                    break
            else:
                hierarchy[element.id] = "1"

    # PHASE 2: Resolve subprocess internal elements
    # Elements with subprocess_id should have that subprocess as their parent
    for element in model.elements:
        subprocess_id = element.properties.get("subprocess_id")
        if subprocess_id:
            hierarchy[element.id] = subprocess_id

    return hierarchy


def assign_elements_to_pools_and_lanes(model: BPMNModel) -> None:
    """Update element parent_id based on pool/lane containment.

    Modifies model in place.

    Args:
        model: BPMN model to update
    """
    hierarchy = resolve_parent_hierarchy(model)

    for element in model.elements:
        if element.id in hierarchy:
            element.parent_id = hierarchy[element.id]
